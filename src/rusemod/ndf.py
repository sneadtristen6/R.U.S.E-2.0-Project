"""NDF binary: read and write, with an editable object model.

Layout in docs/FORMATS.md. Values are stored as (type_code, raw_payload) spans so an unchanged file
re-serializes byte-for-byte; scalar values can be decoded and re-encoded for editing. Adding objects or
strings (which would touch TOPO/STRG/TRAN/IMPR/EXPR) is intentionally NOT supported yet.
"""
from __future__ import annotations

import struct
import zlib

END = 0xABABABAB
HDR = 0x28
SCALAR = {  # editable scalar type codes -> struct format
    0x00: "<B", 0x01: "<b", 0x18: "<h", 0x19: "<H", 0x02: "<i", 0x03: "<I", 0x13: "<q", 0x05: "<f", 0x06: "<d",
}
_FIXED = {0x00: 1, 0x01: 1, 0x18: 2, 0x19: 2, 0x02: 4, 0x03: 4, 0x13: 8,
          0x05: 4, 0x06: 8, 0x07: 4, 0x1C: 4, 0x0B: 12, 0x0C: 16, 0x0D: 4, 0x1A: 16, 0x1D: 8, 0x1F: 8, 0x21: 8}


def decode(raw: bytes) -> bytes:
    """Return the logical (uncompressed) NDF bytes for a possibly-zlib-compressed member."""
    if raw[:4] != b"EUG0" or raw[8:12] != b"CNDF":
        raise ValueError("not an NDF binary")
    flags = struct.unpack_from("<I", raw, 12)[0]
    if not (flags & 0x80):
        return raw
    body_size = struct.unpack_from("<I", raw, HDR)[0]
    body = zlib.decompressobj().decompress(raw[HDR + 4:])
    if len(body) != body_size:
        raise ValueError(f"bad decompressed size {len(body)} != {body_size}")
    return raw[:HDR] + body


class Value:
    __slots__ = ("tc", "payload")

    def __init__(self, tc: int, payload: bytes):
        self.tc, self.payload = tc, payload

    def scalar(self):
        if self.tc not in SCALAR:
            raise TypeError(f"type 0x{self.tc:02x} is not a scalar")
        return struct.unpack(SCALAR[self.tc], self.payload)[0]

    def set_scalar(self, v) -> None:
        if self.tc not in SCALAR:
            raise TypeError(f"type 0x{self.tc:02x} is not a scalar")
        self.payload = struct.pack(SCALAR[self.tc], v)

    def int_list(self) -> list[int]:
        """Decode a list (0x11) of int32 (0x02)."""
        if self.tc != 0x11:
            raise TypeError(f"type 0x{self.tc:02x} is not a list")
        cnt = struct.unpack_from("<I", self.payload, 0)[0]
        return [struct.unpack_from("<i", self.payload, 4 + 8 * i + 4)[0] for i in range(cnt)]

    def set_int_list(self, values: list[int]) -> None:
        """Overwrite a list (0x11) of int32 in place (same count, so the payload length is unchanged)."""
        buf = bytearray(self.payload)
        cnt = struct.unpack_from("<I", buf, 0)[0]
        if len(values) != cnt:
            raise ValueError(f"expected {cnt} values, got {len(values)}")
        for i, v in enumerate(values):
            if struct.unpack_from("<I", buf, 4 + 8 * i)[0] != 0x02:
                raise TypeError("list element is not int32")
            struct.pack_into("<i", buf, 4 + 8 * i + 4, v)
        self.payload = bytes(buf)

    def encode(self) -> bytes:
        return struct.pack("<I", self.tc) + self.payload


def _read_value(b: bytes, p: int) -> tuple[Value, int]:
    tc = struct.unpack_from("<I", b, p)[0]
    p += 4
    if tc in _FIXED:
        n = _FIXED[tc]
        return Value(tc, b[p:p + n]), p + n
    start = p
    if tc in (0x08, 0x14):  # wide string (UTF-16) / blob (raw bytes, e.g. zlib data in .kdt): u32 length + bytes
        ln = struct.unpack_from("<I", b, p)[0]
        end = p + 4 + ln
    elif tc == 0x1E:  # zip blob (seen only in the shader cache): u32 length + u8 flag + length bytes (u32 size + zlib)
        ln = struct.unpack_from("<I", b, p)[0]
        end = p + 5 + ln
    elif tc == 0x09:  # reference
        sub = struct.unpack_from("<I", b, p)[0]
        end = p + (12 if sub == 0xBBBBBBBB else 8)
    elif tc in (0x11, 0x12):  # list / map
        cnt = struct.unpack_from("<I", b, p)[0]
        p += 4
        for _ in range(cnt):
            _, p = _read_value(b, p)
            if tc == 0x12:
                _, p = _read_value(b, p)
        end = p
    elif tc == 0x22:  # pair
        _, p = _read_value(b, p)
        _, p = _read_value(b, p)
        end = p
    else:
        raise ValueError(f"unknown NDF type 0x{tc:x} at 0x{p - 4:x}")
    return Value(tc, b[start:end]), end


class Obj:
    __slots__ = ("cls", "props")

    def __init__(self, cls: int, props: list[tuple[int, Value]]):
        self.cls, self.props = cls, props

    def get(self, prop_index: int) -> Value | None:
        for pi, v in self.props:
            if pi == prop_index:
                return v
        return None


def _name_tree(section: bytes, trans: list[str]) -> dict[int, str]:
    """IMPR/EXPR node = u32 tranIndex, s32 leaf(-1 none), u32 childCount, u32 childOffset[] (rel to array)."""
    out: dict[int, str] = {}

    def node(off: int, prefix: str) -> None:
        tr, leaf, cnt = struct.unpack_from("<IiI", section, off)
        path = trans[tr] if not prefix else prefix + "/" + trans[tr]
        if leaf >= 0:
            out[leaf] = path
        base = off + 12
        for k in range(cnt):
            node(base + struct.unpack_from("<I", section, base + 4 * k)[0], path)

    if section:
        node(0, "")
    return out


class Ndf:
    def __init__(self, raw: bytes):
        self.data = decode(raw)
        self._parse()

    @classmethod
    def from_logical(cls, data: bytes) -> "Ndf":
        """Parse already-decoded (logical) NDF bytes, skipping the decompression step."""
        self = cls.__new__(cls)
        self.data = data
        self._parse()
        return self

    def _parse(self) -> None:
        d = self.data
        self.flags, self.footer_off, self.hsize, self.fsize = struct.unpack_from("<IQQQ", d, 12)
        if d[self.footer_off:self.footer_off + 4] != b"TOC0":
            raise ValueError("missing TOC0")
        count = struct.unpack_from("<I", d, self.footer_off + 4)[0]
        self._order: list[str] = []
        self._toc: dict[str, tuple[int, int, int]] = {}  # name -> (flagsField, offset, size)
        for i in range(count):
            name, ff, off, size = struct.unpack_from("<4sIQQ", d, self.footer_off + 8 + 24 * i)
            name = name.decode()
            self._order.append(name)
            self._toc[name] = (ff, off, size)
        self.classes = self._strs("CLAS")
        self.strings = self._strs("STRG")
        self._strg_dirty = False
        self.trans = self._strs("TRAN")
        self.props = self._props()
        self.objects = self._objects()
        self.exports = _name_tree(self._sec("EXPR"), self.trans)   # object index -> export path
        self.imports = _name_tree(self._sec("IMPR"), self.trans)   # import index -> path in another file
        self._by_export = {v: k for k, v in self.exports.items()}
        self._prop_index = {name: i for i, (name, _cls) in enumerate(self.props)}

    def _sec(self, name: str) -> bytes:
        _ff, off, size = self._toc[name]
        return self.data[off:off + size]

    def _strs(self, name: str) -> list[str]:
        b, p, out = self._sec(name), 0, []
        while p < len(b):
            n = struct.unpack_from("<I", b, p)[0]
            out.append(b[p + 4:p + 4 + n].decode("latin-1"))
            p += 4 + n
        return out

    def _props(self) -> list[tuple[str, int]]:
        b, p, out = self._sec("PROP"), 0, []
        while p < len(b):
            n = struct.unpack_from("<I", b, p)[0]
            name = b[p + 4:p + 4 + n].decode("latin-1")
            cls = struct.unpack_from("<I", b, p + 4 + n)[0]
            out.append((name, cls))
            p += 8 + n
        return out

    def _objects(self) -> list[Obj]:
        b, p, out = self._sec("OBJE"), 0, []
        while p < len(b):
            cls = struct.unpack_from("<I", b, p)[0]
            p += 4
            props = []
            while True:
                pi = struct.unpack_from("<I", b, p)[0]
                p += 4
                if pi == END:
                    break
                v, p = _read_value(b, p)
                props.append((pi, v))
            out.append(Obj(cls, props))
        return out

    # --- editing helpers ---
    def object_by_export(self, name: str) -> Obj:
        return self.objects[self._by_export[name]]

    def prop_index(self, name: str) -> int:
        return self._prop_index[name]

    def prop_name(self, index: int) -> str:
        return self.props[index][0]

    def set_string(self, index: int, text: str) -> None:
        """Change entry `index` of the STRG table (what string/path values, types 0x07/0x1C, point at).

        Every value in this file that points at the entry changes with it, so check who uses it first.
        """
        text.encode("latin-1")  # STRG is latin-1: fail now, not at write time
        self.strings[index] = text
        self._strg_dirty = True

    # --- serialization ---
    def _encode_obje(self) -> bytes:
        buf = bytearray()
        for o in self.objects:
            buf += struct.pack("<I", o.cls)
            for pi, v in o.props:
                buf += struct.pack("<I", pi) + v.encode()
            buf += struct.pack("<I", END)
        return bytes(buf)

    def to_logical(self) -> bytes:
        sections = {name: (self._encode_obje() if name == "OBJE" else self._sec(name)) for name in self._order}
        if self._strg_dirty:
            sections["STRG"] = b"".join(struct.pack("<I", len(s.encode("latin-1"))) + s.encode("latin-1")
                                        for s in self.strings)
        blob = bytearray()
        layout = []  # (name, offset, size)
        for name in self._order:
            layout.append((name, HDR + len(blob), len(sections[name])))
            blob += sections[name]
        footer_off = HDR + len(blob)
        footer = bytearray(b"TOC0" + struct.pack("<I", len(self._order)))
        for name, off, size in layout:
            footer += name.encode("latin-1") + struct.pack("<IQQ", self._toc[name][0], off, size)
        header = bytearray(self.data[:HDR])
        struct.pack_into("<Q", header, 0x10, footer_off)
        struct.pack_into("<Q", header, 0x20, footer_off + len(footer))
        return bytes(header) + bytes(blob) + bytes(footer)

    def to_member(self, compress: bool = True, level: int = 9) -> bytes:
        logical = self.to_logical()
        header, body = bytearray(logical[:HDR]), logical[HDR:]
        flags = struct.unpack_from("<I", header, 12)[0]
        if compress:
            struct.pack_into("<I", header, 12, flags | 0x80)
            return bytes(header) + struct.pack("<I", len(body)) + zlib.compress(body, level)
        struct.pack_into("<I", header, 12, flags & ~0x80)
        return bytes(header) + body


# --- walking values (for indexes and checks) ---
def sub_values(v: Value) -> list[Value]:
    """The values directly inside a list (0x11), map (0x12: key, value, key, value, ...) or pair (0x22)."""
    b, out = v.payload, []
    if v.tc in (0x11, 0x12):
        cnt, p = struct.unpack_from("<I", b, 0)[0], 4
        for _ in range(cnt * (2 if v.tc == 0x12 else 1)):
            x, p = _read_value(b, p)
            out.append(x)
    elif v.tc == 0x22:
        x, p = _read_value(b, 0)
        out = [x, _read_value(b, p)[0]]
    return out


def iter_values(v: Value):
    """`v` and every value nested inside it, depth first."""
    yield v
    for x in sub_values(v):
        yield from iter_values(x)


def local_ref(v: Value) -> int | None:
    """The object index a local reference (0x09, 0xBBBBBBBB) points at; None for anything else or null."""
    if v.tc == 0x09 and struct.unpack_from("<I", v.payload)[0] == 0xBBBBBBBB:
        inst = struct.unpack_from("<I", v.payload, 4)[0]
        return None if inst == 0xFFFFFFFF else inst
    return None

