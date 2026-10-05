"""The game's unit list: R.U.S.E. only uses the units it lists, so `add_classes` lists every copied unit the way its
source is listed.

This is code the game runs. The only thing ever written is one fixed template, filled in from checked values: a class
name of letters, digits and `_`, and a `$/...` object path. `check_added` proves the new list is the old one plus
exactly those lines before anything is used. Mods never bring scripts of their own (`build.load_mod` refuses them)."""
from __future__ import annotations

import re
import struct
import zlib
from dataclasses import dataclass

MAGIC = b"XYZ0"
PY25 = b"\x0a\x0d\xf2\xb3"   # Python 2.5's magic number 62131, stored big-endian
SCRIPT_PACK = "genpython\\eugenpatchable.ipk"   # the pack in ZZ_Win.dat that holds the unit list
UNIT_LIST = "parametres\\classes.xyz"           # the unit list in that pack (the end of its member path)

# Python 2.5 instructions used by the unit list
BUILD_CLASS, LOAD_LOCALS, RETURN_VALUE, HAVE_ARGUMENT = 89, 82, 83, 90
STORE_NAME, STORE_ATTR, LOAD_CONST, LOAD_NAME, BUILD_TUPLE, LOAD_ATTR = 90, 95, 100, 101, 102, 105
CALL_FUNCTION, MAKE_FUNCTION = 131, 132
_ADDED_OPS = {LOAD_CONST, LOAD_NAME, LOAD_ATTR, BUILD_TUPLE, MAKE_FUNCTION, CALL_FUNCTION, BUILD_CLASS, STORE_NAME,
              STORE_ATTR}  # everything the template uses; check_added allows nothing else

# The class body every standard unit class has: `__module__ = __name__; descriptor = _ndf.Database.GetObject(path)`
BODY_NAMES = (b"__name__", b"__module__", b"_ndf", b"Database", b"GetObject", b"descriptor")
BODY_CODE = bytes([LOAD_NAME, 0, 0, STORE_NAME, 1, 0, LOAD_NAME, 2, 0, LOAD_ATTR, 3, 0, LOAD_ATTR, 4, 0,
                   LOAD_CONST, 0, 0, CALL_FUNCTION, 1, 0, STORE_NAME, 5, 0, LOAD_LOCALS, RETURN_VALUE])

_CLASS_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,99}$")
_PATH = re.compile(r"^\$/[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*$")


class ScriptError(ValueError):
    pass


@dataclass
class Code:
    """A Python 2.5 code object, as marshal stores it. Strings are bytes."""
    argcount: int
    nlocals: int
    stacksize: int
    flags: int
    code: bytes
    consts: tuple
    names: tuple
    varnames: tuple
    freevars: tuple
    cellvars: tuple
    filename: bytes
    name: bytes
    firstlineno: int
    lnotab: bytes


# --- marshal (Python 2.5) ---

class _Reader:
    def __init__(self, data: bytes):
        self.b, self.pos, self.interned = data, 0, []

    def take(self, n: int) -> bytes:
        if n < 0 or self.pos + n > len(self.b):
            raise ScriptError(f"marshal data ends early at {self.pos}")
        v = self.b[self.pos:self.pos + n]
        self.pos += n
        return v

    def i32(self) -> int:
        return struct.unpack("<i", self.take(4))[0]

    def obj(self):
        t = chr(self.take(1)[0])
        if t == "N":
            return None
        if t in "FT":
            return t == "T"
        if t == "S":
            return StopIteration
        if t == ".":
            return Ellipsis
        if t == "i":
            return self.i32()
        if t == "I":
            return struct.unpack("<q", self.take(8))[0]
        if t == "g":
            return struct.unpack("<d", self.take(8))[0]
        if t == "y":
            return complex(*struct.unpack("<dd", self.take(16)))
        if t == "f":
            return float(self.take(self.take(1)[0]))
        if t == "x":
            re_, im = (float(self.take(self.take(1)[0])) for _ in range(2))
            return complex(re_, im)
        if t == "l":
            n = self.i32()
            digits = struct.unpack(f"<{abs(n)}H", self.take(2 * abs(n)))
            v = sum(d << (15 * i) for i, d in enumerate(digits))
            return -v if n < 0 else v
        if t in "st":
            v = self.take(self.i32())
            if t == "t":
                self.interned.append(v)
            return v
        if t == "R":
            i = self.i32()
            if not 0 <= i < len(self.interned):
                raise ScriptError(f"string reference {i} at {self.pos - 4} points nowhere")
            return self.interned[i]
        if t == "u":
            return self.take(self.i32()).decode("utf-8")
        if t in "([<>":
            items = tuple(self.obj() for _ in range(self.i32()))
            return items if t == "(" else list(items) if t == "[" else frozenset(items)
        if t == "{":
            d = {}
            while self.b[self.pos:self.pos + 1] != b"0":
                k = self.obj()
                d[k] = self.obj()
            self.pos += 1
            return d
        if t == "c":
            return self.code_body()
        raise ScriptError(f"marshal type {t!r} at {self.pos - 1} isn't Python 2.5's")

    def code_body(self) -> Code:
        ints = [self.i32() for _ in range(4)]
        fields = [self.obj() for _ in range(8)]
        first = self.i32()
        return Code(*ints, *fields, first, self.obj())


def load(data: bytes):
    """Read marshal data (Python 2.5) written by the game's build."""
    r = _Reader(data)
    v = r.obj()
    if r.pos != len(data):
        raise ScriptError(f"{len(data) - r.pos} bytes after the marshal data")
    return v


def _module_spans(data: bytes) -> list[tuple[int, int]]:
    """Where the top-level code object's code, consts and names fields sit in `data`."""
    if data[:1] != b"c":
        raise ScriptError("the module isn't a marshalled code object")
    r = _Reader(data)
    r.pos = 1 + 16
    spans = []
    for _ in range(3):
        start = r.pos
        r.obj()
        spans.append((start, r.pos))
    return spans


def dump(v) -> bytes:
    """Marshal (Python 2.5) the few kinds of values the template needs. Strings are always written plain (`s`), never
    interned (`t`): that way the numbering of the file's shared strings, which later `R` references use, never
    changes."""
    if v is None:
        return b"N"
    if v is True or v is False:
        return b"T" if v else b"F"
    if isinstance(v, int):
        if not -2 ** 31 <= v < 2 ** 31:
            raise ScriptError(f"{v} doesn't fit in marshal's int")
        return b"i" + struct.pack("<i", v)
    if isinstance(v, bytes):
        return b"s" + struct.pack("<i", len(v)) + v
    if isinstance(v, tuple):
        return b"(" + struct.pack("<i", len(v)) + b"".join(dump(x) for x in v)
    if isinstance(v, Code):
        return (b"c" + struct.pack("<4i", v.argcount, v.nlocals, v.stacksize, v.flags)
                + b"".join(dump(x) for x in (v.code, v.consts, v.names, v.varnames, v.freevars, v.cellvars,
                                             v.filename, v.name))
                + struct.pack("<i", v.firstlineno) + dump(v.lnotab))
    raise ScriptError(f"can't write a {type(v).__name__} (only what the unit-list template needs)")


def instructions(code: bytes) -> list[tuple[int, int, int | None]]:
    """(offset, instruction, argument or None) for Python 2.5 compiled code."""
    out, p = [], 0
    while p < len(code):
        op = code[p]
        if op >= HAVE_ARGUMENT:
            if p + 3 > len(code):
                raise ScriptError(f"the compiled code ends inside an instruction at {p}")
            out.append((p, op, code[p + 1] | code[p + 2] << 8))
            p += 3
        else:
            out.append((p, op, None))
            p += 1
    return out


# --- .xyz files ---

@dataclass
class Xyz:
    source_md5: bytes  # the MD5 of the .py source; kept as is (the game has no source to check it against)
    payload: bytes     # the marshalled module code object


def read_xyz(raw: bytes) -> Xyz:
    if raw[:4] != MAGIC or raw[4:8] != PY25:
        raise ScriptError(f"not a Python 2.5 .xyz file (starts {raw[:8].hex(' ')})")
    size = struct.unpack_from(">I", raw, 8)[0]
    payload = zlib.decompressobj().decompress(raw[28:])
    if len(payload) != size:
        raise ScriptError(f".xyz says {size} bytes but holds {len(payload)}")
    return Xyz(raw[12:28], payload)


def write_xyz(x: Xyz) -> bytes:
    return MAGIC + PY25 + struct.pack(">I", len(x.payload)) + x.source_md5 + zlib.compress(x.payload, 9)


# --- the unit list ---

@dataclass
class UnitClass:
    name: str          # the Python class, e.g. Unit_M3_Lee
    path: str | None   # the unit it stands for, e.g. $/GFX/Everything/Descriptor_Unit_M3_Lee (None if not standard)
    base: tuple        # (module, class) under `front`, e.g. ("unit", "TankUnit")
    body: Code
    standard: bool     # the body is exactly the two-line template
    registered: bool = False  # has its `X.descriptor.base_class = X` line


@dataclass
class UnitList:
    module: Code
    classes: dict  # class name -> UnitClass
    by_path: dict  # unit path -> UnitClass (standard classes only)


def unit_list(data: bytes) -> UnitList:
    """The classes in the unit list module (marshal data of parametres/classes.py)."""
    mod = load(data)
    if not isinstance(mod, Code):
        raise ScriptError("the unit list isn't a code object")
    ins, names = instructions(mod.code), mod.names
    pattern = [LOAD_CONST, LOAD_NAME, LOAD_ATTR, LOAD_ATTR, BUILD_TUPLE, LOAD_CONST, MAKE_FUNCTION, CALL_FUNCTION,
               BUILD_CLASS, STORE_NAME]
    classes = {}
    for j in range(len(ins) - len(pattern) + 1):
        seq = ins[j:j + len(pattern)]
        if [op for _, op, _ in seq] != pattern:
            continue
        a = [arg for _, _, arg in seq]
        cname, body = mod.consts[a[0]], mod.consts[a[5]]
        if (a[4], a[6], a[7]) != (1, 0, 0) or names[a[1]] != b"front" or not isinstance(body, Code) \
                or not isinstance(cname, bytes) or names[a[9]] != cname:
            continue
        standard = (body.code == BODY_CODE and body.names == BODY_NAMES and len(body.consts) == 1
                    and isinstance(body.consts[0], bytes) and body.argcount == 0
                    and not (body.varnames or body.freevars or body.cellvars))
        name = cname.decode("latin-1")
        classes[name] = UnitClass(name, body.consts[0].decode("latin-1") if standard else None,
                                  (names[a[2]].decode("latin-1"), names[a[3]].decode("latin-1")), body, standard)
    for j in range(len(ins) - 3):
        (_, o1, a1), (_, o2, a2), (_, o3, a3), (_, o4, a4) = ins[j:j + 4]
        if (o1, o2, o3, o4) == (LOAD_NAME, LOAD_NAME, LOAD_ATTR, STORE_ATTR) and a1 == a2 \
                and names[a3] == b"descriptor" and names[a4] == b"base_class":
            c = classes.get(names[a1].decode("latin-1"))
            if c is not None:
                c.registered = True
    return UnitList(mod, classes, {c.path: c for c in classes.values() if c.standard})


@dataclass
class NewClass:
    name: str  # the Python class name: the new unit's ClassNameForDebug
    path: str  # the new unit's $/... path
    like: str  # the class of the unit it was copied from (gives the base class)


def _checked(ul: UnitList, new: list[NewClass]) -> list[UnitClass]:
    taken = {n.decode("latin-1") for n in ul.module.names}
    likes, seen_names, seen_paths = [], set(), set()
    for n in new:
        if not _CLASS_NAME.match(n.name):
            raise ScriptError(f"{n.name!r} can't be a class name: use letters, digits and '_', not starting with a digit")
        if not _PATH.match(n.path):
            raise ScriptError(f"{n.path!r} isn't an object path like $/GFX/Everything/Descriptor_Unit_X")
        if n.name in taken or n.name in seen_names:
            raise ScriptError(f"the unit list already has a class or name {n.name!r}")
        if n.path in ul.by_path or n.path in seen_paths:
            raise ScriptError(f"{n.path} already has a class in the unit list")
        like = ul.classes.get(n.like)
        if like is None or not like.standard or not like.registered:
            raise ScriptError(f"{n.like!r} isn't a standard, registered class in the unit list, so it can't be copied")
        seen_names.add(n.name)
        seen_paths.add(n.path)
        likes.append(like)
    return likes


def _statements(ul: UnitList, new: list[NewClass], likes: list[UnitClass]):
    """The constants, names and compiled code that define and register `new`, appended to the module's own."""
    index = {n: i for i, n in enumerate(ul.module.names)}
    consts, names, code = [], [], b""
    kc, kn = len(ul.module.consts), len(ul.module.names)

    def op(o, arg=None):
        if arg is None:
            return bytes([o])
        if not 0 <= arg < 65536:
            raise ScriptError(f"index {arg} is too big for one instruction")
        return bytes([o, arg & 255, arg >> 8])
    for n, like in zip(new, likes):
        name, b = n.name.encode("latin-1"), like.body
        body = Code(b.argcount, b.nlocals, b.stacksize, b.flags, BODY_CODE, (n.path.encode("latin-1"),), BODY_NAMES,
                    (), (), (), b.filename, name, b.firstlineno, b.lnotab)
        c_name, c_body, n_name = kc + len(consts), kc + len(consts) + 1, kn + len(names)
        consts += [name, body]
        names.append(name)
        module, base = (x.encode("latin-1") for x in like.base)
        code += (op(LOAD_CONST, c_name) + op(LOAD_NAME, index[b"front"]) + op(LOAD_ATTR, index[module])
                 + op(LOAD_ATTR, index[base]) + op(BUILD_TUPLE, 1) + op(LOAD_CONST, c_body) + op(MAKE_FUNCTION, 0)
                 + op(CALL_FUNCTION, 0) + op(BUILD_CLASS) + op(STORE_NAME, n_name)           # class X(front.m.B): ...
                 + op(LOAD_NAME, n_name) + op(LOAD_NAME, n_name) + op(LOAD_ATTR, index[b"descriptor"])
                 + op(STORE_ATTR, index[b"base_class"]))                                  # X.descriptor.base_class = X
    return consts, names, code


def add_classes(data: bytes, new: list[NewClass]) -> bytes:
    """The unit list module `data` (marshal) with a standard class for each of `new`, checked by check_added."""
    ul = unit_list(data)
    likes = _checked(ul, new)
    consts, names, code = _statements(ul, new, likes)
    mod = ul.module
    tail = instructions(mod.code)[-2:]
    if len(tail) != 2 or tail[0][1] != LOAD_CONST or mod.consts[tail[0][2]] is not None or tail[1][1] != RETURN_VALUE:
        raise ScriptError("the unit list doesn't end with 'return None' as expected")
    (c0, c1), (k0, k1), (n0, n1) = _module_spans(data)
    if data[c0:c0 + 1] != b"s" or data[k0:k0 + 1] != b"(" or data[n0:n0 + 1] != b"(":
        raise ScriptError("the unit list's compiled code, constants or names aren't stored the usual way")
    new_data = (data[:c0] + dump(mod.code[:-4] + code + mod.code[-4:])
                + b"(" + struct.pack("<i", len(mod.consts) + len(consts)) + data[k0 + 5:k1]
                + b"".join(dump(c) for c in consts)
                + b"(" + struct.pack("<i", len(mod.names) + len(names)) + data[n0 + 5:n1]
                + b"".join(dump(n) for n in names)
                + data[n1:])
    check_added(data, new_data, new)
    return new_data


def check_added(old: bytes, new: bytes, added: list[NewClass]) -> None:
    """Raise ScriptError unless `new` is exactly `old` plus the template statements for `added` (decision 23)."""
    a, b = load(old), load(new)
    for f in ("argcount", "nlocals", "stacksize", "flags", "varnames", "freevars", "cellvars", "filename", "name",
              "firstlineno", "lnotab"):
        if getattr(a, f) != getattr(b, f):
            raise ScriptError(f"the module's {f} changed")
    if b.consts[:len(a.consts)] != a.consts or b.names[:len(a.names)] != a.names:
        raise ScriptError("the module's existing constants or names changed")
    ul = unit_list(old)
    consts, names, code = _statements(ul, added, _checked(ul, added))
    if b.consts[len(a.consts):] != tuple(consts) or b.names[len(a.names):] != tuple(names):
        raise ScriptError("the added constants or names aren't exactly the template's")
    if b.code != a.code[:-4] + code + a.code[-4:]:
        raise ScriptError("the module's compiled code isn't the old one plus the template")
    if {op for _, op, _ in instructions(code)} - _ADDED_OPS:
        raise ScriptError("the added code uses an instruction the template never needs")
    after = unit_list(new)
    if len(after.classes) != len(ul.classes) + len(added):
        raise ScriptError("the unit list doesn't have exactly the added classes more")
    for n in added:
        c = after.classes.get(n.name)
        if c is None or not (c.standard and c.registered) or c.path != n.path or c.base != ul.classes[n.like].base:
            raise ScriptError(f"{n.name} doesn't read back as a registered class for {n.path}")


def find_unit_list(arc):
    """In ZZ_Win.dat (an Edat): (script pack member, the pack as Edat, its unit-list member, the unit list's raw
    bytes), or None when the pack or the list isn't there (a made-up game in tests, say)."""
    from .edat import Edat
    entry = next((e for e in arc.entries if e.path.lower() == SCRIPT_PACK), None)
    if entry is None:
        return None
    pack = Edat(bytes(arc.read(entry)))
    member = next((e for e in pack.entries if e.path.lower().endswith(UNIT_LIST)), None)
    if member is None:
        return None
    return entry, pack, member, bytes(pack.read(member))
