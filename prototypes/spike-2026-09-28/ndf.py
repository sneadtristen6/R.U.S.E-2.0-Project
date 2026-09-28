"""Read-only helpers for R.U.S.E. NDF binaries (.ndfbin/.gladndfbin/.truendfbin) inside EDAT packs."""
import os, struct, sys, zlib

WORK = r"C:\Users\snead\AppData\Roaming\Claude\scratch-workspaces\1b22630c-4e82-4690-ac49-607665140ad7\14f0b3f4-2f49-40b6-aa73-3e269bce083c\scratch-2026-09-28-f34142"
sys.path.insert(0, WORK)
from ruse_edat import EdatArchive  # noqa: E402

GAME = r"D:\Steam\steamapps\common\R.U.S.E"
PACKS = os.path.join(GAME, r"Data\PC\190852")


def pack(name):
    return EdatArchive(os.path.join(PACKS, name + ".dat") if not name.endswith(".dat") else name)


def read_entry(arc, suffix):
    for e in arc.entries:
        if e.path.lower().endswith(suffix.lower()):
            return arc.read(e)
    raise KeyError(suffix)


def decode(raw):
    assert raw[:4] == b"EUG0" and raw[8:12] == b"CNDF", raw[:12]
    flags = struct.unpack_from("<I", raw, 12)[0]
    if flags & 0x80:
        body_size = struct.unpack_from("<I", raw, 0x28)[0]
        body = zlib.decompressobj().decompress(raw[0x2C:])
        assert len(body) == body_size, (len(body), body_size)
        return raw[:0x28] + body
    return raw


class Ndf:
    def __init__(self, raw):
        self.data = d = decode(raw)
        self.flags, self.footer, self.hsize, self.fsize = struct.unpack_from("<IQQQ", d, 12)
        assert d[self.footer:self.footer + 4] == b"TOC0"
        n = struct.unpack_from("<I", d, self.footer + 4)[0]
        self.toc = {}
        for i in range(n):
            name, _, off, size = struct.unpack_from("<4sIQQ", d, self.footer + 8 + 24 * i)
            self.toc[name.decode()] = (off, size)
        self.classes = [s for s, _ in self._lenstr_table("CLAS")]
        self.props = self._props()
        self.strings = [s for s, _ in self._lenstr_table("STRG")]
        self.trans = [s for s, _ in self._lenstr_table("TRAN")]

    def section(self, name):
        off, size = self.toc[name]
        return self.data[off:off + size]

    def _lenstr_table(self, name, extra=0):
        b = self.section(name)
        out, p = [], 0
        while p < len(b):
            n = struct.unpack_from("<I", b, p)[0]
            s = b[p + 4:p + 4 + n].decode("latin-1")
            p += 4 + n
            ex = struct.unpack_from("<" + "I" * extra, b, p) if extra else ()
            p += 4 * extra
            out.append((s, ex))
        return out

    def _props(self):
        return [(s, ex[0]) for s, ex in self._lenstr_table("PROP", 1)]


def load(pack_name, suffix):
    arc = pack(pack_name)
    try:
        return Ndf(read_entry(arc, suffix))
    finally:
        arc.close()
