"""Minimal Python 2.5 marshal reader (enough to walk code objects from .xyz payloads). Read-only."""
import struct, zlib


def parse_xyz(raw):
    """XYZ0 | BE u32 pyc magic | BE u32 payload size | 16 B md5 | zlib(marshal code object)."""
    assert raw[:4] == b"XYZ0"
    magic, size = struct.unpack_from(">II", raw, 4)
    md5 = raw[12:28]
    d = zlib.decompressobj()
    payload = d.decompress(raw[28:])
    assert len(payload) == size and d.eof
    return magic, md5, payload


class M25:
    def __init__(self, b):
        self.b, self.p, self.refs = b, 0, []

    def u32(self):
        v = struct.unpack_from("<i", self.b, self.p)[0]
        self.p += 4
        return v

    def obj(self):
        t = chr(self.b[self.p]); self.p += 1
        if t in "0NFTS.":
            return {"0": None, "N": None, "F": False, "T": True, "S": StopIteration, ".": Ellipsis}[t]
        if t == "i":
            return self.u32()
        if t == "l":
            n = self.u32(); self.p += 2 * abs(n); return ("long", n)
        if t == "I":
            self.p += 8; return ("int64",)
        if t == "f":
            n = self.b[self.p]; self.p += 1 + n; return ("float",)
        if t == "g":
            self.p += 8; return ("float",)
        if t == "y":
            self.p += 16; return ("complex",)
        if t in "stu":
            n = self.u32(); s = self.b[self.p:self.p + n]; self.p += n
            s = s.decode("utf-8" if t == "u" else "latin-1")
            if t == "t":
                self.refs.append(s)
            return s
        if t == "R":
            return self.refs[self.u32()]
        if t in "([<>":
            n = self.u32(); return tuple(self.obj() for _ in range(n))
        if t == "{":
            out = {}
            while self.b[self.p] != ord("0"):
                k = self.obj(); out[k] = self.obj()
            self.p += 1
            return out
        if t == "c":
            argc, nloc, stack, flags = struct.unpack_from("<4i", self.b, self.p); self.p += 16
            code = self.obj(); consts = self.obj(); names = self.obj(); varnames = self.obj()
            free = self.obj(); cell = self.obj(); filename = self.obj(); name = self.obj()
            first = self.u32(); lnotab = self.obj()
            return {"code": True, "argc": argc, "flags": flags, "consts": consts, "names": names,
                    "filename": filename, "name": name, "firstlineno": first, "codelen": len(code)}
        raise ValueError(f"unknown marshal type {t!r} at {self.p - 1}")


def load_code(payload):
    m = M25(payload)
    co = m.obj()
    return co, m.p == len(payload)
