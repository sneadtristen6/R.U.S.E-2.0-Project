"""Read-only reader for Eugen Systems EDAT v1 archives (R.U.S.E.).

Layout (reverse-engineered from the game files, little-endian):
  0x00  char[4]  "edat"
  0x04  u32      version (1)
  0x08  u8[16]   checksum (zero in Data\\*.dat, set in Maps\\*.dat)
  0x18  u8       unknown (0)
  0x19  u32      dictionary offset
  0x1D  u32      dictionary length
  0x21  u32      data offset
  0x25  u32      data length
Dictionary: a trie of path fragments, entries aligned to 2 bytes.
  dir : u32 header_len (!=0, children follow the header), u32 next_sibling, cstr fragment
  file: u32 0, u32 next_sibling, u32 offset (from data offset), u32 size, u8 flag, cstr fragment
  next_sibling is relative to the entry start; 0 = last sibling.
"""
import argparse, collections, math, os, struct, sys, zlib

MAGIC = b"edat"


class Entry:
    __slots__ = ("path", "offset", "size", "flag")

    def __init__(self, path, offset, size, flag):
        self.path, self.offset, self.size, self.flag = path, offset, size, flag


def _cstr(buf, pos):
    end = buf.index(b"\0", pos)
    return buf[pos:end].decode("latin-1")


class EdatArchive:
    def __init__(self, path):
        self.path = path
        self._f = open(path, "rb")  # read-only; the game install is never written
        head = self._f.read(0x29)
        if head[:4] != MAGIC:
            raise ValueError(f"{path}: not an EDAT archive ({head[:4]!r})")
        self.version = struct.unpack_from("<I", head, 4)[0]
        if self.version != 1:
            raise ValueError(f"{path}: unsupported EDAT version {self.version}")
        self.checksum = head[8:24]
        self.dict_offset, self.dict_len, self.data_offset, self.data_len = struct.unpack_from("<IIII", head, 0x19)
        self._f.seek(self.dict_offset)
        self._dict = self._f.read(self.dict_len)
        self.entries = []
        self._walk(0, "")

    def _walk(self, pos, prefix):
        d = self._dict
        while True:
            head_len, next_sib = struct.unpack_from("<II", d, pos)
            if head_len == 0:
                offset, size, flag = struct.unpack_from("<IIB", d, pos + 8)
                self.entries.append(Entry(prefix + _cstr(d, pos + 17), offset, size, flag))
            else:
                self._walk(pos + head_len, prefix + _cstr(d, pos + 8))
            if next_sib == 0:
                return
            pos += next_sib

    def read(self, entry, n=None):
        self._f.seek(self.data_offset + entry.offset)
        return self._f.read(entry.size if n is None else min(n, entry.size))

    def close(self):
        self._f.close()


def entropy(b):
    if not b:
        return 0.0
    c = collections.Counter(b)
    return -sum(v / len(b) * math.log2(v / len(b)) for v in c.values())


def magic_of(b):
    m = b[:4]
    return m.decode("latin-1") if all(32 <= x < 127 for x in m) else m.hex()


def cmd_list(a):
    arc = EdatArchive(a.archive)
    for e in arc.entries:
        print(f"{e.size:>11} {e.flag:>3} {magic_of(arc.read(e, 4)):>8}  {e.path}")


def cmd_stats(a):
    for path in a.archive:
        arc = EdatArchive(path)
        by_ext = collections.defaultdict(lambda: [0, 0, collections.Counter(), []])
        overlaps, end = 0, 0
        for e in sorted(arc.entries, key=lambda e: e.offset):
            overlaps += e.offset < end
            end = max(end, e.offset + e.size)
            ext = os.path.splitext(e.path)[1].lower() or "(none)"
            s = by_ext[ext]
            head = arc.read(e, 4096)
            s[0] += 1; s[1] += e.size; s[2][magic_of(head)] += 1
            s[3].append(entropy(head))
        flags = collections.Counter(e.flag for e in arc.entries)
        print(f"== {path}\n   entries={len(arc.entries)} data={arc.data_len:,} B  checksum={arc.checksum.hex()}"
              f"  flags={dict(flags)}  overlaps={overlaps}  covered_to={end:,}")
        for ext, (n, size, mags, ents) in sorted(by_ext.items(), key=lambda kv: -kv[1][1]):
            top = ", ".join(f"{m}x{c}" for m, c in mags.most_common(3))
            print(f"   {ext:<10} n={n:<6} {size / 2**20:>9.1f} MB  H(4K) avg={sum(ents) / n:.2f}  magic: {top}")
        arc.close()


def cmd_extract(a):
    arc = EdatArchive(a.archive)
    for e in arc.entries:
        if a.match.lower() in e.path.lower():
            dst = os.path.join(a.out, *e.path.split("\\"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(arc.read(e))
            print(dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("list"); p.add_argument("archive"); p.set_defaults(fn=cmd_list)
    p = sub.add_parser("stats"); p.add_argument("archive", nargs="+"); p.set_defaults(fn=cmd_stats)
    p = sub.add_parser("extract", help="copy matching files OUT of an archive")
    p.add_argument("archive"); p.add_argument("match"); p.add_argument("out"); p.set_defaults(fn=cmd_extract)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
