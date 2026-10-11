"""A mission script written by the build, with no compiler: the game's 45 mission scripts are straight-line code
(PLAN decision 23's "safe mission language", private/notes/mission-scripting-research-2026-10-03.md): a list of
`NAME = module.Block(Arg=value, ...)` statements after the imports, and one function, `def launch(): import
leveldesign.launcher; return leveldesign.launcher.launch(ER)`. This module holds that list (Call, Attr, Ref, plain
values) and writes it the way Python 2.5 compiles it (the game's interpreter: absolute imports, true division, the
with statement, code flags 0xe040), as marshal data for an .xyz file (rusemod.pyscript.write_xyz). `source()` writes
the same list as Python, to show it or to compile it with Python 2.5 for comparison.

Only the instructions the shipped missions use are ever written (LOAD_NAME, LOAD_CONST, LOAD_ATTR, STORE_NAME,
CALL_FUNCTION, BUILD_LIST, IMPORT_NAME, MAKE_FUNCTION, RETURN_VALUE, and in launch() LOAD_FAST, STORE_FAST,
LOAD_GLOBAL), and only the blocks `ALLOWED` lists can be called: rusemod.mission makes every statement from the
mission file's data, nothing from text a mod brings.
"""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass, field

from .pyscript import Code, ScriptError

# Python 2.5's instruction numbers
POP_TOP, RETURN_VALUE, STORE_NAME, BUILD_TUPLE, BUILD_LIST = 1, 83, 90, 102, 103
LOAD_CONST, LOAD_NAME, LOAD_ATTR, IMPORT_NAME, LOAD_GLOBAL = 100, 101, 105, 107, 116
LOAD_FAST, STORE_FAST, CALL_FUNCTION, MAKE_FUNCTION = 124, 125, 131, 132
HAVE_ARGUMENT = 90
MODULE_FLAGS = 0xE040    # CO_NOFREE | the three __future__ flags, as every shipped mission
FUNCTION_FLAGS = 0xE043  # and CO_OPTIMIZED | CO_NEWLOCALS for launch()
WRITTEN_OPS = {LOAD_NAME, LOAD_CONST, LOAD_ATTR, STORE_NAME, CALL_FUNCTION, BUILD_LIST, IMPORT_NAME, MAKE_FUNCTION,
               RETURN_VALUE, LOAD_FAST, STORE_FAST, LOAD_GLOBAL}

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# The blocks a mission may make: module -> class names, all from the game's own missions (the research note's
# usage.txt and catalog.txt), the ones rusemod.mission writes.
ALLOWED = {
    "leveldesign.camera": {"DescriptorStartCameraPath"},
    "leveldesign.camps": {"VariableCamp", "LocalizedCampName", "DescriptorHudElementsVisibility"},
    "leveldesign.condition": {"ConditionVariableInteger"},
    "leveldesign.descriptor": {"DescriptorSequential", "DescriptorSimultaneous", "DescriptorWaitDuree",
                               "DescriptorWaitCondition", "DescriptorLoadingDone", "DescriptorIncrementeVariableInteger",
                               "DescriptorSetVariableInteger", "DescriptorPlayEffetAfterWait"},
    "leveldesign.descriptorspecial": {"DescriptorInitSoundAndMusic"},
    "leveldesign.launcheffetmap": {"DescriptorLaunchEffetMap", "GameRulesChallenge", "GameRulesSkirmish"},
    "leveldesign.operator": {"OperatorIntegerEqual", "OperatorIntegerStrictlyMore", "OperatorIntegerMoreOrEqual"},
    "leveldesign.variable": {"VariableInteger"},
    "leveldesignsolo.camps": {"DescriptorSetRessourceCamp"},
    "leveldesignsolo.condition": {"ConditionUnitGroup", "ConditionDetectUnitDansZoneDetection"},
    "leveldesignsolo.contrainte_unit": {"ContrainteOnUnitTeam", "ContrainteOnUnitCategory",
                                        "ContrainteOnUnitAllContrainte"},
    "leveldesignsolo.descriptor": {"DescriptorAfficheHint"},
    "leveldesignsolo.fx": {"DescriptorDrawLabel"},
    "leveldesignsolo.helper": {"TagPosition", "TagZoneDetection", "TagUnit"},
    "leveldesignsolo.missions": {"DescriptorMove", "DescriptorDefendZone", "DescriptorAttack", "DescriptorParachutage",
                                 "DescriptorFrappeArtillerie", "DescriptorBombardement"},
    "leveldesignsolo.objectif": {"DescriptorGereObjectifAvecLabel", "DescriptorObjectifsPanel",
                                 "DescriptorDeclencheVictoireChallenge", "DescriptorDeclencheVictoire",
                                 "DescriptorDeclencheDefaite"},
    "leveldesignsolo.production": {"DescriptorCreateUnit"},
    "leveldesignsolo.strategic_ia": {"DescriptorIAAll"},   # (not .camps: T45 stopped on it, 2026-10-10)
    "leveldesignsolo.timer": {"VariableTimer", "DescriptorStartTimer"},
    "leveldesignsolo.units": {"VariableUnitGroup"},
}
# What a value may name besides the statements above: the game's enums, colours and unit classes
ATTR_ROOTS = ("_enum_for_game_play.", "defines.colors.", "parametres.Classes.")


@dataclass(frozen=True)
class Attr:
    """A dotted name read from a module: `_enum_for_game_play.NiveauIA.Player`, `parametres.Classes.Unit_M4_Sherman`."""
    path: str


@dataclass(frozen=True)
class Ref:
    """Another statement's name: `G_ENEMY`."""
    name: str


@dataclass(frozen=True)
class Long:
    """A whole number stored as Python 2.5's long ('l'), as the game's text keys are."""
    value: int


@dataclass
class Call:
    """`module.Block(positional..., Key=value, ...)`; keywords in the order given (the shipped missions sort them)."""
    func: str
    args: tuple = ()
    kwargs: list = field(default_factory=list)


def call(func: str, *args, **kwargs) -> Call:
    return Call(func, tuple(args), sorted(kwargs.items()))


# --- Python source (for showing, and for comparing with Python 2.5's own compiler) ---

def _src(v) -> str:
    if isinstance(v, Call):
        parts = [_src(a) for a in v.args] + [f"{k}={_src(x)}" for k, x in v.kwargs]
        return f"{v.func}({', '.join(parts)})"
    if isinstance(v, Ref):
        return v.name
    if isinstance(v, Attr):
        return v.path
    if isinstance(v, Long):
        return f"{v.value}L"
    if isinstance(v, list):
        return "[" + ", ".join(_src(x) for x in v) + "]"
    if isinstance(v, bool) or v is None:
        return repr(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return repr(v.encode("latin-1"))[1:]  # a plain string, as Python 2 writes it
    raise ScriptError(f"a mission can't hold a {type(v).__name__}")


def source(imports: list, defs: list, launch: str) -> str:
    """The mission as Python 2.5 source: one statement a line, as the build's code numbers its lines."""
    lines = [f"import {m}" for m in imports] + [f"{name} = {_src(v)}" for name, v in defs]
    lines += ["def launch():", "    import leveldesign.launcher", f"    return leveldesign.launcher.launch({launch})", ""]
    return "\n".join(lines)


# --- checks ---

def check(imports: list, defs: list, launch: str) -> None:
    """Raise ScriptError unless every statement is an allowed block whose values are plain values, enum/colour/class
    names from imported modules, or names stored above it."""
    for m in imports:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*", m):
            raise ScriptError(f"{m!r} isn't a module name")
    roots = {m.split(".")[0] for m in imports}
    seen: set = set()

    def value(v, where):
        if isinstance(v, Call):
            mod, _, cls = v.func.rpartition(".")
            if cls not in ALLOWED.get(mod, ()):
                raise ScriptError(f"{where}: {v.func} isn't a block a mission may use")
            if mod not in imports:
                raise ScriptError(f"{where}: {mod} isn't imported")
            for a in v.args:
                value(a, where)
            for k, x in v.kwargs:
                if not _NAME.match(k):
                    raise ScriptError(f"{where}: {k!r} isn't an argument name")
                value(x, where)
        elif isinstance(v, Ref):
            if v.name not in seen:
                raise ScriptError(f"{where}: {v.name} is used before it's made")
        elif isinstance(v, Attr):
            if not v.path.startswith(ATTR_ROOTS) or v.path.split(".")[0] not in roots \
                    or not all(_NAME.match(p) for p in v.path.split(".")):
                raise ScriptError(f"{where}: {v.path} isn't an enum, colour or unit class")
        elif isinstance(v, list):
            for x in v:
                value(x, where)
        elif isinstance(v, Long):
            if not 0 <= v.value < 2 ** 64:
                raise ScriptError(f"{where}: {v.value} isn't a text key")
        elif v is None or isinstance(v, (bool, int, float)):
            pass
        elif isinstance(v, str):
            if not all(32 <= ord(ch) < 127 for ch in v):
                raise ScriptError(f"{where}: {v!r}: a mission's own strings are plain ASCII (texts go in the text files)")
        else:
            raise ScriptError(f"{where}: a mission can't hold a {type(v).__name__}")
    for name, v in defs:
        if not _NAME.match(name) or name in seen or name in roots or name == "launch":
            raise ScriptError(f"{name!r} can't name a statement")
        if not isinstance(v, Call):
            raise ScriptError(f"{name}: each statement makes a block")
        value(v, name)
        seen.add(name)
    if launch not in seen:
        raise ScriptError(f"launch() hands over {launch}, which isn't made")


# --- the code writer ---

class _Unit:
    """One code object being written: its instructions, constants and names, its stack and line numbers."""

    def __init__(self, function: bool, first_line: int):
        self.code = bytearray()
        self.consts: list = [None] if function else []  # a function's first constant: its docstring, or None
        self.names: list = []
        self.varnames: list = []
        self.depth = self.most = 0
        self.lnotab = bytearray()
        self.line, self.line_at = first_line, 0  # the line numbers start at the code object's first line

    def const(self, v) -> int:
        key = (type(v), v)
        for i, c in enumerate(self.consts):
            if (type(c), c) == key and not (isinstance(v, float) and struct.pack("<d", v) != struct.pack("<d", c)):
                return i
        self.consts.append(v)
        return len(self.consts) - 1

    def name(self, n: bytes, table: list) -> int:
        if n not in table:
            table.append(n)
        return table.index(n)

    def op(self, o: int, arg: int | None = None, effect: int = 0) -> None:
        if arg is None:
            self.code.append(o)
        else:
            if not 0 <= arg < 65536:
                raise ScriptError(f"argument {arg} is too big for one instruction")
            self.code += bytes([o, arg & 255, arg >> 8])
        self.depth += effect
        self.most = max(self.most, self.depth)

    def statement(self, line: int) -> None:
        """A new source line starts here (Python 2.5's line-number table)."""
        d_code, d_line = len(self.code) - self.line_at, line - self.line
        if d_line <= 0:
            return
        while d_code > 255:
            self.lnotab += b"\xff\x00"
            d_code -= 255
        while d_line > 255:
            self.lnotab += bytes([d_code, 255])
            d_code, d_line = 0, d_line - 255
        self.lnotab += bytes([d_code, d_line])
        self.line, self.line_at = line, len(self.code)

    def value(self, v) -> None:
        if isinstance(v, Call):
            first, *rest = v.func.split(".")
            self.op(LOAD_NAME, self.name(first.encode(), self.names), 1)
            for part in rest:
                self.op(LOAD_ATTR, self.name(part.encode(), self.names))
            for a in v.args:
                self.value(a)
            for k, x in v.kwargs:
                self.op(LOAD_CONST, self.const(k.encode()), 1)
                self.value(x)
            n_pos, n_kw = len(v.args), len(v.kwargs)
            if n_pos > 255 or n_kw > 255:
                raise ScriptError(f"{v.func}: too many arguments for one call")
            self.op(CALL_FUNCTION, n_pos | n_kw << 8, -(n_pos + 2 * n_kw))
        elif isinstance(v, Ref):
            self.op(LOAD_NAME, self.name(v.name.encode(), self.names), 1)
        elif isinstance(v, Attr):
            first, *rest = v.path.split(".")
            self.op(LOAD_NAME, self.name(first.encode(), self.names), 1)
            for part in rest:
                self.op(LOAD_ATTR, self.name(part.encode(), self.names))
        elif isinstance(v, list):
            for x in v:
                self.value(x)
            self.op(BUILD_LIST, len(v), 1 - len(v))
        elif isinstance(v, Long):
            self.op(LOAD_CONST, self.const(_LongConst(v.value)), 1)
        elif isinstance(v, bool):  # Python 2's True and False are names, not constants
            self.op(LOAD_NAME, self.name(b"True" if v else b"False", self.names), 1)
        elif v is None:  # compiled as the name None; Python 2.5's optimiser may make it the constant (optimised())
            self.op(LOAD_NAME, self.name(b"None", self.names), 1)
        elif isinstance(v, str):
            self.op(LOAD_CONST, self.const(v.encode("latin-1")), 1)
        elif isinstance(v, int) and not isinstance(v, bool) and not -2 ** 31 <= v < 2 ** 31:
            self.op(LOAD_CONST, self.const(_LongConst(v)), 1)  # too big for a 32-bit int: Python 2.5 makes it a long
        else:
            self.op(LOAD_CONST, self.const(v), 1)

    def import_(self, module: str, store_fast: bool) -> None:
        self.op(LOAD_CONST, self.const(0), 1)      # level 0: an absolute import
        self.op(LOAD_CONST, self.const(None), 1)   # no from-list
        # (it takes both and leaves the module, but Python 2.5's compiler counts it as taking nothing, so its stack
        # size grows by one an import: counted the same way, the code object is the one Python 2.5 makes)
        self.op(IMPORT_NAME, self.name(module.encode(), self.names), 0)
        top = module.split(".")[0].encode()
        if store_fast:
            self.op(STORE_FAST, self.name(top, self.varnames), -1)
        else:
            self.op(STORE_NAME, self.name(top, self.names), -1)


    def optimised(self) -> bytes:
        """The code as Python 2.5's optimiser leaves it: the name None loaded as the constant None (the name stays
        listed), unless a statement's code is over 255 bytes (its line table then holds a 255), when the optimiser
        leaves the whole code object as it is."""
        code = bytes(self.code)
        if b"None" not in self.names or None not in self.consts or 255 in self.lnotab:
            return code
        name, const = self.names.index(b"None"), self.consts.index(None)
        out = bytearray(code)
        for at, op, arg in _instructions(code):
            if op == LOAD_NAME and arg == name:
                out[at:at + 3] = bytes([LOAD_CONST, const & 255, const >> 8])
        return bytes(out)


def _instructions(code: bytes):
    p = 0
    while p < len(code):
        op = code[p]
        if op >= HAVE_ARGUMENT:
            yield p, op, code[p + 1] | code[p + 2] << 8
            p += 3
        else:
            yield p, op, None
            p += 1


@dataclass(frozen=True)
class _LongConst:
    value: int


def _dump(v, out: bytearray) -> None:
    """Marshal (Python 2.5, version 2) the values a mission needs. Strings are written plain ('s')."""
    if v is None:
        out += b"N"
    elif v is True or v is False:
        out += b"T" if v else b"F"
    elif isinstance(v, _LongConst):
        n, digits = abs(v.value), []
        while n:
            digits.append(n & 0x7FFF)
            n >>= 15
        out += b"l" + struct.pack("<i", -len(digits) if v.value < 0 else len(digits))
        out += struct.pack(f"<{len(digits)}H", *digits)
    elif isinstance(v, int):
        out += b"i" + struct.pack("<i", v)
    elif isinstance(v, float):
        out += b"g" + struct.pack("<d", v)
    elif isinstance(v, bytes):
        out += b"s" + struct.pack("<i", len(v)) + v
    elif isinstance(v, tuple):
        out += b"(" + struct.pack("<i", len(v))
        for x in v:
            _dump(x, out)
    elif isinstance(v, Code):
        out += b"c" + struct.pack("<4i", v.argcount, v.nlocals, v.stacksize, v.flags)
        for x in (v.code, v.consts, v.names, v.varnames, v.freevars, v.cellvars, v.filename, v.name):
            _dump(x, out)
        out += struct.pack("<i", v.firstlineno)
        _dump(v.lnotab, out)
    else:
        raise ScriptError(f"can't write a {type(v).__name__} into a mission")


def assemble(imports: list, defs: list, launch: str, filename: str) -> bytes:
    """The mission (checked by `check`) as Python 2.5 marshal data: the module code object, numbered as `source()`
    numbers its lines."""
    check(imports, defs, launch)
    fn_line = len(imports) + len(defs) + 1
    # launch(): import leveldesign.launcher; return leveldesign.launcher.launch(<launch>)
    f = _Unit(function=True, first_line=fn_line)
    f.statement(fn_line + 1)
    f.import_("leveldesign.launcher", store_fast=True)
    f.statement(fn_line + 2)
    f.op(LOAD_FAST, f.name(b"leveldesign", f.varnames), 1)
    f.op(LOAD_ATTR, f.name(b"launcher", f.names))
    f.op(LOAD_ATTR, f.name(b"launch", f.names))
    f.op(LOAD_GLOBAL, f.name(launch.encode(), f.names), 1)
    f.op(CALL_FUNCTION, 1, -1)
    f.op(RETURN_VALUE, None, -1)
    fcode = Code(0, len(f.varnames), f.most, FUNCTION_FLAGS, f.optimised(), tuple(f.consts), tuple(f.names),
                 tuple(f.varnames), (), (), filename.encode("latin-1"), b"launch", fn_line, bytes(f.lnotab))
    m = _Unit(function=False, first_line=1)
    line = 1
    for mod in imports:
        m.statement(line)
        m.import_(mod, store_fast=False)
        line += 1
    for name, v in defs:
        m.statement(line)
        m.value(v)
        m.op(STORE_NAME, m.name(name.encode(), m.names), -1)
        line += 1
    m.statement(line)
    m.op(LOAD_CONST, m.const(_CodeConst(fcode)), 1)
    m.op(MAKE_FUNCTION, 0)
    m.op(STORE_NAME, m.name(b"launch", m.names), -1)
    m.op(LOAD_CONST, m.const(None), 1)
    m.op(RETURN_VALUE, None, -1)
    consts = tuple(c.code if isinstance(c, _CodeConst) else c for c in m.consts)
    module = Code(0, 0, m.most, MODULE_FLAGS, m.optimised(), consts, tuple(m.names), (), (), (),
                  filename.encode("latin-1"), b"<module>", 1, bytes(m.lnotab))
    out = bytearray()
    _dump(module, out)
    return bytes(out)


@dataclass(frozen=True)
class _CodeConst:
    code: Code

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


def instructions_used(data: bytes) -> set:
    """Every instruction in the marshalled module `data` and the code inside it (rusemod.pyscript's reader)."""
    from .pyscript import instructions, load
    seen: set = set()

    def walk(c: Code):
        seen.update(op for _at, op, _arg in instructions(c.code))
        for k in c.consts:
            if isinstance(k, Code):
                walk(k)
    walk(load(data))
    return seen
