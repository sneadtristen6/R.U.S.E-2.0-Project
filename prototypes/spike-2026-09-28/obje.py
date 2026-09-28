"""Experimental OBJE parser for R.U.S.E. NDF binaries (read-only). Type table is empirical; see TYPES."""
import collections, struct, sys
import ndf

END = 0xABABABAB
# R.U.S.E. (swapped vs. Wargame/moddingSuite): 0xAAAAAAAA = import ref (u32 IMPR leaf index),
# 0xBBBBBBBB = local object ref (u32 instance, u32 class; FFFFFFFF/FFFFFFFF = null)
IMPREF, OBJREF = 0xAAAAAAAA, 0xBBBBBBBB

# type code -> (name, fixed payload size) ; None size = special handler.
# Only codes observed in the 1,982 shipped NDF files (all parse to the end of OBJE); anything else raises.
TYPES = {
    0x00: ("bool", 1), 0x01: ("int8", 1), 0x02: ("int32", 4), 0x03: ("uint32", 4), 0x05: ("float32", 4),
    0x06: ("float64", 8), 0x07: ("string", 4), 0x08: ("wstring", None), 0x09: ("reference", None),
    0x0B: ("vec3f", 12), 0x0C: ("float4", 16), 0x0D: ("color32", 4),
    0x11: ("list", None), 0x12: ("map", None), 0x13: ("int64", 8),
    0x18: ("int16", 2), 0x19: ("uint16", 2), 0x1A: ("guid", 16), 0x1C: ("path", 4), 0x1D: ("lochash", 8),
    0x1F: ("int2", 8), 0x21: ("float2", 8), 0x22: ("pair", None),
}


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, n, types=None, strict=True):
        self.n = n
        self.b = n.section("OBJE")
        self.types = dict(TYPES if types is None else types)
        self.seen = collections.Counter()
        self.strict = strict
        self.nobj_hint = 1 << 30

    def u32(self, p):
        return struct.unpack_from("<I", self.b, p)[0]

    def value(self, p, depth=0):
        t = self.u32(p)
        p += 4
        if t not in self.types:
            raise ParseError(f"unknown type 0x{t:x} at 0x{p - 4:x}")
        name, size = self.types[t]
        self.seen[t] += 1
        if size is not None:
            v = self.b[p:p + size]
            if name == "string":
                v = self.n.strings[struct.unpack_from("<I", v)[0]]
            elif name == "float32":
                v = struct.unpack("<f", v)[0]
            elif name in ("int32", "uint32"):
                v = struct.unpack("<i" if name == "int32" else "<I", v)[0]
            elif name == "bool":
                v = v[0] != 0  # exporter writes uninitialised bytes (e.g. 0x4E) for some bools
            return (name, v), p + size
        if name == "wstring":
            ln = self.u32(p)
            return (name, self.b[p + 4:p + 4 + ln].decode("utf-16le", "replace")), p + 4 + ln
        if name == "reference":
            sub = self.u32(p)
            # R.U.S.E.: 0xBBBBBBBB = local object ref (instance, class); 0xAAAAAAAA = import ref (index)
            if sub == 0xBBBBBBBB:
                inst, cls = struct.unpack_from("<II", self.b, p + 4)
                if (inst, cls) == (0xFFFFFFFF, 0xFFFFFFFF):
                    return ("objref", None), p + 12
                if inst >= self.nobj_hint or cls >= len(self.n.classes):
                    raise ParseError(f"implausible objref ({inst},{cls}) at 0x{p:x}")
                return ("objref", (inst, cls)), p + 12
            if sub == 0xAAAAAAAA:
                return ("impref", self.u32(p + 4)), p + 8
            raise ParseError(f"unknown ref subtype 0x{sub:x} at 0x{p:x}")
        if name == "list":
            cnt = self.u32(p)
            p += 4
            out = []
            for _ in range(cnt):
                v, p = self.value(p, depth + 1)
                out.append(v)
            return (name, out), p
        if name == "pair":
            k, p = self.value(p, depth + 1)
            v, p = self.value(p, depth + 1)
            return (name, (k, v)), p
        if name == "map":
            cnt = self.u32(p)
            p += 4
            out = []
            for _ in range(cnt):
                k, p = self.value(p, depth + 1)
                v, p = self.value(p, depth + 1)
                out.append((k, v))
            return (name, out), p
        if name == "blob":
            ln = self.u32(p)
            return (name, self.b[p + 4:p + 4 + ln]), p + 4 + ln
        if name == "zipblob":
            ln = self.u32(p)
            return (name, self.b[p + 5:p + 5 + ln]), p + 5 + ln
        raise ParseError(f"no handler for {name}")

    def objects(self):
        p, out = 0, []
        while p < len(self.b):
            start = p
            cls = self.u32(p)
            if cls >= len(self.n.classes):
                raise ParseError(f"bad class index {cls} at 0x{p:x} (object #{len(out)})")
            p += 4
            props = []
            while True:
                pi = self.u32(p)
                p += 4
                if pi == END:
                    break
                if pi >= len(self.n.props):
                    raise ParseError(f"bad prop index 0x{pi:x} at 0x{p - 4:x} (object #{len(out)}, class {self.n.classes[cls]})")
                v, p = self.value(p)
                props.append((pi, v))
            out.append((start, cls, props))
        return out


def summarize(n, objs):
    cc = collections.Counter(n.classes[c] for _, c, _ in objs)
    return cc


def name_tree(section, trans):
    """IMPR/EXPR: node = u32 tranIndex, s32 leafIndex (-1 = none), u32 childCount,
    u32 childOffset[childCount] (relative to the start of the offset array). Returns {leafIndex: path}."""
    out = {}

    def node(off, prefix):
        tr, idx, cnt = struct.unpack_from("<IiI", section, off)
        path = trans[tr] if not prefix else prefix + "/" + trans[tr]
        if idx >= 0:
            out[idx] = path
        base = off + 12
        for k in range(cnt):
            node(base + struct.unpack_from("<I", section, base + 4 * k)[0], path)

    if section:
        node(0, "")
    return out
