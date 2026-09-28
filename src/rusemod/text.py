"""Show an NDF file as readable text, spelled like Eugen's own text NDF (WARNO) where it has a spelling.

This is a first draft of the text form mods are written in (docs/MOD_FORMAT.md §5); it is for reading, not yet for
compiling back. Unnamed objects used by exactly one other object are printed inside it, as in WARNO; unnamed objects
used by several (shared) or by none are printed on their own as `#<index> is <Class>`.
"""
from __future__ import annotations

import collections
import struct
import uuid

from .dic import key_to_name
from .ndf import Ndf, Value, iter_values, local_ref, sub_values

PAD = "    "


def _f32(b: bytes) -> str:
    x = struct.unpack("<f", b)[0]
    if x != x or x in (float("inf"), float("-inf")):
        return repr(x)
    for digits in range(1, 10):
        s = f"{x:.{digits}g}"
        if struct.pack("<f", float(s)) == b:
            break
    return s if any(c in s for c in ".en") else s + ".0"


def _quote(s: str) -> str:
    return f"'{s}'" if "'" not in s else 'str("' + s.replace('"', '\\"') + '")'


class NdfText:
    def __init__(self, ndf: Ndf):
        self.ndf = ndf
        self.used_by: dict[int, list[int]] = collections.defaultdict(list)
        for oi, o in enumerate(ndf.objects):
            for _pi, v in o.props:
                for x in iter_values(v):
                    r = local_ref(x)
                    if r is not None:
                        self.used_by[r].append(oi)
        self.inline = {i for i in range(len(ndf.objects)) if i not in ndf.exports and len(self.used_by[i]) == 1}
        self.printed: set[int] = set()

    # --- one value -> lines (the first line continues the current line; later lines carry their own indent) ---
    def value(self, v: Value, depth: int) -> list[str]:
        tc, b = v.tc, v.payload
        simple = {
            0x01: lambda: f"int8({struct.unpack('<b', b)[0]})",
            0x02: lambda: str(struct.unpack("<i", b)[0]),
            0x03: lambda: f"uint32({struct.unpack('<I', b)[0]})",
            0x05: lambda: _f32(b),
            0x06: lambda: f"f64({struct.unpack('<d', b)[0]!r})",
            0x07: lambda: _quote(self._strg(b)),
            0x08: lambda: 'wstr("' + b[4:4 + struct.unpack_from("<I", b)[0]].decode("utf-16-le", "replace")
                          .replace('"', '\\"') + '")',
            0x0B: lambda: "Float3[" + ", ".join(_f32(b[i:i + 4]) for i in range(0, 12, 4)) + "]",
            0x0C: lambda: "Float4[" + ", ".join(_f32(b[i:i + 4]) for i in range(0, 16, 4)) + "]",
            0x0D: lambda: "RGBA[" + ", ".join(str(c) for c in b) + "]",
            0x13: lambda: f"int64({struct.unpack('<q', b)[0]})",
            0x14: lambda: f"blob({struct.unpack_from('<I', b)[0]} bytes)",
            0x18: lambda: f"int16({struct.unpack('<h', b)[0]})",
            0x19: lambda: f"uint16({struct.unpack('<H', b)[0]})",
            0x1A: lambda: "GUID:{" + str(uuid.UUID(bytes_le=b)) + "}",
            0x1C: lambda: f"path({_quote(self._strg(b))})",
            0x1D: lambda: self._key(b),
            0x1E: lambda: f"zipblob({struct.unpack_from('<I', b)[0]} bytes)",
            0x1F: lambda: "Int2[{}, {}]".format(*struct.unpack("<ii", b)),
            0x21: lambda: f"Float2[{_f32(b[:4])}, {_f32(b[4:])}]",
        }
        if tc == 0x00:
            return ["true" if b == b"\x01" else "false" if b == b"\x00" else f"bool(0x{b[0]:02X})"]
        if tc in simple:
            return [simple[tc]()]
        if tc == 0x09:
            return self._ref(b, depth)
        if tc == 0x11:
            return self._seq("[", "]", [self.value(x, depth + 1) for x in sub_values(v)], depth)
        if tc == 0x12:
            items = sub_values(v)
            pairs = [self._pair(items[i], items[i + 1], depth + 1) for i in range(0, len(items), 2)]
            return self._seq("MAP [", "]", pairs, depth)
        if tc == 0x22:
            a, c = sub_values(v)
            return self._pair(a, c, depth)
        return [f"raw(0x{tc:02X}, {b.hex()})"]

    def _strg(self, b: bytes) -> str:
        i = struct.unpack("<I", b)[0]
        return self.ndf.strings[i] if i < len(self.ndf.strings) else f"<bad string #{i}>"

    @staticmethod
    def _key(b: bytes) -> str:
        k = struct.unpack("<Q", b)[0]
        name = key_to_name(k)
        return f"key({name})" if name else f"key(0x{k:016X})"

    def _ref(self, b: bytes, depth: int) -> list[str]:
        sub = struct.unpack_from("<I", b)[0]
        if sub == 0xAAAAAAAA:
            idx = struct.unpack_from("<I", b, 4)[0]
            return [self.ndf.imports.get(idx, f"<import #{idx}>")]
        inst = struct.unpack_from("<I", b, 4)[0]
        if inst == 0xFFFFFFFF:
            return ["nil"]
        if inst in self.ndf.exports:
            return [self.ndf.exports[inst]]
        if inst in self.inline and inst not in self.printed and inst < len(self.ndf.objects):
            return self.object_body(inst, depth)
        return [f"#{inst}"]

    def _pair(self, a: Value, c: Value, depth: int) -> list[str]:
        return self._seq("(", ")", [self.value(a, depth + 1), self.value(c, depth + 1)], depth)

    @staticmethod
    def _seq(open_: str, close: str, parts: list[list[str]], depth: int) -> list[str]:
        if all(len(p) == 1 for p in parts):
            inner = ", ".join(p[0] for p in parts)
            return [f"{open_}{inner}{close}" if open_ != "MAP [" else f"MAP [{' ' + inner + ' ' if inner else ''}]"]
        lines = [open_]
        for k, p in enumerate(parts):
            part = [PAD * (depth + 1) + p[0]] + p[1:]
            if k < len(parts) - 1:
                part[-1] += ","
            lines += part
        return lines + [PAD * depth + close]

    # --- objects ---
    def object_body(self, i: int, depth: int) -> list[str]:
        """`Class` then `( … )`, with the parenthesised part at `depth`."""
        self.printed.add(i)
        o = self.ndf.objects[i]
        lines = [self.ndf.classes[o.cls], PAD * depth + "("]
        for pi, v in o.props:
            vl = self.value(v, depth + 1)
            lines.append(f"{PAD * (depth + 1)}{self.ndf.prop_name(pi)} = {vl[0]}")
            lines += vl[1:]
        return lines + [PAD * depth + ")"]

    def top_level(self, i: int) -> list[str]:
        body = self.object_body(i, 0)
        if i in self.ndf.exports:
            path = self.ndf.exports[i]
            head = f"export {path.rsplit('/', 1)[-1]} is {body[0]}   // {path}, #{i}"
        else:
            users = self.used_by[i]
            note = "not used by any object" if not users else "shared: used by " + ", ".join(f"#{u}" for u in users[:8])
            head = f"#{i} is {body[0]}   // unnamed, {note}" + (" …" if len(users) > 8 else "")
        return [head] + body[1:]

    def lines(self, match: str | None = None):
        """All top-level objects in file order; `match` keeps only those whose export path or class contains it."""
        want = match.lower() if match else None
        for i in range(len(self.ndf.objects)):
            if i in self.inline:
                continue
            if want and want not in self.ndf.exports.get(i, "").lower() and \
                    want not in self.ndf.classes[self.ndf.objects[i].cls].lower():
                continue
            yield from self.top_level(i)
            yield ""
        if not want:  # unnamed objects that only other inline objects use in a loop: never reached above
            for i in sorted(self.inline - self.printed):
                yield from self.top_level(i)
                yield ""
