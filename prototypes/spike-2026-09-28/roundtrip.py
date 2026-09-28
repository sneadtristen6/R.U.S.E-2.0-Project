"""C1: prove a lossless read->write of the unit-database NDF (OBJE), and probe TOPO.

Read-only against the game install. Re-encodes every OBJE value from a decoded form and checks it
reproduces the original bytes, so the writer is proven lossless per value type (not by copying raw spans).
"""
import collections, os, struct, sys, zlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from ruse_edat import EdatArchive  # noqa: E402

PACK = r"D:\Steam\steamapps\common\R.U.S.E\Data\PC\190852\ZZ_GladPatchableWin.dat"
ENTRY = "gfx\\everything.cpp.gladndfbin"
END = 0xABABABAB


def decode(raw):
    assert raw[:4] == b"EUG0" and raw[8:12] == b"CNDF"
    flags = struct.unpack_from("<I", raw, 12)[0]
    if not (flags & 0x80):
        return raw
    body_size = struct.unpack_from("<I", raw, 0x28)[0]
    body = zlib.decompressobj().decompress(raw[0x2C:])
    assert len(body) == body_size, (len(body), body_size)
    return raw[:0x28] + body


# (typecode) -> fixed payload byte length, for the raw-passthrough types.
RAW = {0x05: 4, 0x06: 8, 0x0B: 12, 0x0C: 16, 0x0D: 4, 0x1A: 16, 0x1D: 8, 0x1F: 8, 0x21: 8}
INT = {0x01: "<b", 0x18: "<h", 0x19: "<H", 0x02: "<i", 0x03: "<I", 0x13: "<q"}


def read_value(b, p):
    """Return (encoded_bytes, next_p): encoded_bytes is rebuilt from the decoded value."""
    t = struct.unpack_from("<I", b, p)[0]
    p += 4
    tc = struct.pack("<I", t)
    if t == 0x00:  # bool: keep the exact byte (some are neither 0 nor 1)
        return tc + b[p:p + 1], p + 1
    if t in INT:
        n = struct.calcsize(INT[t])
        v = struct.unpack_from(INT[t], b, p)[0]
        return tc + struct.pack(INT[t], v), p + n
    if t in (0x07, 0x1C):  # string / path: u32 index into STRG
        idx = struct.unpack_from("<I", b, p)[0]
        return tc + struct.pack("<I", idx), p + 4
    if t in RAW:  # float/double/vec/color/guid/lochash/int2/float2: opaque, kept raw
        n = RAW[t]
        return tc + b[p:p + n], p + n
    if t == 0x08:  # wide string: u32 byte length + UTF-16
        ln = struct.unpack_from("<I", b, p)[0]
        return tc + struct.pack("<I", ln) + b[p + 4:p + 4 + ln], p + 4 + ln
    if t == 0x09:  # reference
        sub = struct.unpack_from("<I", b, p)[0]
        if sub == 0xBBBBBBBB:
            inst, cls = struct.unpack_from("<II", b, p + 4)
            return tc + struct.pack("<III", sub, inst, cls), p + 12
        if sub == 0xAAAAAAAA:
            idx = struct.unpack_from("<I", b, p + 4)[0]
            return tc + struct.pack("<II", sub, idx), p + 8
        raise ValueError(f"ref subtype {sub:#x} at {p:#x}")
    if t == 0x11:  # list
        cnt = struct.unpack_from("<I", b, p)[0]
        p += 4
        out = tc + struct.pack("<I", cnt)
        for _ in range(cnt):
            enc, p = read_value(b, p)
            out += enc
        return out, p
    if t == 0x12:  # map: count + key/value pairs
        cnt = struct.unpack_from("<I", b, p)[0]
        p += 4
        out = tc + struct.pack("<I", cnt)
        for _ in range(cnt):
            enc, p = read_value(b, p)
            out += enc
            enc, p = read_value(b, p)
            out += enc
        return out, p
    if t == 0x22:  # pair
        out = tc
        for _ in range(2):
            enc, p = read_value(b, p)
            out += enc
        return out, p
    raise ValueError(f"type {t:#x} at {p - 4:#x}")


def main():
    arc = EdatArchive(PACK)
    raw = next(arc.read(e) for e in arc.entries if e.path.endswith(ENTRY))
    arc.close()
    data = decode(raw)
    footer = struct.unpack_from("<Q", data, 16)[0]
    toc = {}
    for i in range(struct.unpack_from("<I", data, footer + 4)[0]):
        name, _, off, size = struct.unpack_from("<4sIQQ", data, footer + 8 + 24 * i)
        toc[name.decode()] = (off, size)

    o_off, o_size = toc["OBJE"]
    obje = data[o_off:o_off + o_size]
    ncls = 0
    p, out, nobj, nval, tally = 0, bytearray(), 0, 0, collections.Counter()
    while p < len(obje):
        cls = struct.unpack_from("<I", obje, p)[0]
        out += struct.pack("<I", cls)
        p += 4
        while True:
            pi = struct.unpack_from("<I", obje, p)[0]
            p += 4
            if pi == END:
                out += struct.pack("<I", END)
                break
            out += struct.pack("<I", pi)
            t = struct.unpack_from("<I", obje, p)[0]
            tally[t] += 1
            nval += 1
            enc, p = read_value(obje, p)
            out += enc
        nobj += 1
    ok = bytes(out) == obje
    print(f"OBJE: {nobj} objects, {nval} values, {len(obje):,} bytes")
    print(f"round-trip byte-identical: {ok}")
    if not ok:
        for i in range(min(len(out), len(obje))):
            if out[i] != obje[i]:
                print(f"  first diff at OBJE offset {i:#x}")
                break
        print(f"  len out={len(out)} orig={len(obje)}")
    print("value type histogram (code: count):", {f"0x{k:02x}": v for k, v in sorted(tally.items())})

    # TOPO probe
    t_off, t_size = toc["TOPO"]
    topo = struct.unpack_from(f"<{t_size // 4}I", data, t_off)
    is_perm = sorted(topo) == list(range(nobj))
    identity = list(topo) == list(range(nobj))
    print(f"TOPO: {t_size} bytes = {len(topo)} u32 (objects={nobj}); "
          f"permutation_of_0..N-1={is_perm}; identity={identity}; first 12={list(topo[:12])}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
