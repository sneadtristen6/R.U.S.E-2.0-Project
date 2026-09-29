"""Read `.rndf` mod files (docs/MOD_FORMAT.md §5) into operations for the rules engine (rusemod.patch).

    patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( ProductionPrice = [30, 30, 30, 30, 30]  SeuilMort += 100 )
    export Descriptor_Unit_R2_Marines is clone $/GFX/Everything/Descriptor_Unit_US_Rangers ( ShowInMenu = [1, 1, 1, 1, 1] )
    final patch every TUniteAuSolDescriptor ( SeuilMort *= 1.1 )
    when mod better-ai ( patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( ProductionPrice += 5 ) )
    patch @TAmmunition[AmmunitionId=1120] ( NbTirParSalves = 40 )          // found by a property (MOD_FORMAT §4)
    patch every TUniteAuSolDescriptor [Nationalite=1] ( SeuilMort += 10 )   // every object that fits the filter

Values are spelled like Eugen's own text NDF (WARNO) where it has a spelling. Errors give file, line and column.
"""
from __future__ import annotations

import re
import struct
import uuid
from decimal import Decimal

from .patch import Inline, ListV, MapV, Num, Obj, Op, PairV, Raw, Ref, Text  # noqa: F401  (Inline/Obj for callers)

DEFAULT_NAMESPACE = "$/GFX/Everything"  # where `X is TClass` objects go unless cloned (draft; M2 confirms)

_TOKENS = [
    ("skip", r"\s+|//[^\n]*|/\*.*?\*/|\(\*.*?\*\)"),
    ("guid", r"GUID:\{[0-9A-Fa-f-]+\}"),
    ("designator", r"@(?:[A-Za-z_]\w*)?\[[^\]]*\](?::(?:[\w.]|\[[^\]]*\])+)?"),
    ("ref", r"[$~]/[\w/]+(?::(?:[\w.]|\[[^\]]*\])+)?"),
    ("shared", r"#\d+"),
    ("number", r"-?(?:0x[0-9A-Fa-f]+|\d+\.\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?|\d+(?:[eE][-+]?\d+)?)"),
    ("string", r"'[^'\n]*'|\"[^\"\n]*\""),
    ("op", r"\*=|\+=|-=|>=|<=|==|[()\[\],=.^~<>*]"),
    ("name", r"[A-Za-z_]\w*(?:-\w+)*"),
]
_LEXER = re.compile("|".join(f"(?P<{k}>{v})" for k, v in _TOKENS), re.S)
_INT_TYPES = {"int8", "int16", "uint16", "uint32", "int64"}
_VECTORS = {"Float2": (0x21, "<ff", 2), "Float3": (0x0B, "<fff", 3), "Float4": (0x0C, "<ffff", 4),
            "Int2": (0x1F, "<ii", 2), "RGBA": (0x0D, "<BBBB", 4)}


class RndfError(Exception):
    pass


class _Tok:
    __slots__ = ("kind", "text", "line", "col")

    def __init__(self, kind, text, line, col):
        self.kind, self.text, self.line, self.col = kind, text, line, col

    def __repr__(self):
        return f"{self.text!r}"


def tokenize(text: str, file: str = "<text>") -> list[_Tok]:
    toks, pos, line, line_start = [], 0, 1, 0
    while pos < len(text):
        m = _LEXER.match(text, pos)
        if not m:
            raise RndfError(f"{file}:{line}:{pos - line_start + 1}: can't read {text[pos:pos + 12]!r}")
        kind, s = m.lastgroup, m.group()
        if kind != "skip":
            toks.append(_Tok(kind, s, line, pos - line_start + 1))
        nl = s.count("\n")
        if nl:
            line += nl
            line_start = pos + s.rfind("\n") + 1
        pos = m.end()
    toks.append(_Tok("end", "", line, pos - line_start + 1))
    return toks


class Parser:
    def __init__(self, text: str, file: str = "<text>", mod: str = ""):
        self.toks, self.i, self.file, self.mod = tokenize(text, file), 0, file, mod
        self.declared: dict[str, str] = {}   # local name -> full export path

    # --- token helpers ---
    def peek(self, k=0) -> _Tok:
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def next(self) -> _Tok:
        t = self.peek()
        self.i += 1
        return t

    def error(self, msg: str, t: _Tok | None = None):
        t = t or self.peek()
        got = "the end of the file" if t.kind == "end" else repr(t.text)
        return RndfError(f"{self.file}:{t.line}:{t.col}: {msg} (found {got})")

    def expect(self, text: str) -> _Tok:
        t = self.next()
        if t.text != text:
            raise self.error(f"expected {text!r}", t)
        return t

    def is_(self, *texts: str) -> bool:
        return self.peek().text in texts and self.peek().kind in ("name", "op")

    def op(self, kind: str, line: int, **kw) -> Op:
        return Op(kind, mod=self.mod, file=self.file, line=line, **kw)

    # --- statements ---
    def parse(self) -> list[Op]:
        ops = []
        while self.peek().kind != "end":
            ops += self.statement()
        return _resolve_locals(ops, self.declared, self.file)

    def statement(self) -> list[Op]:
        if self.is_("final"):
            self.next()
            ops = self.statement()
            for o in ops:
                o.final = True
            return ops
        if self.is_("when"):
            return self.when()
        if self.is_("patch"):
            return self.patch()
        if self.is_("delete"):
            t = self.next()
            return [self.op("delobj", t.line, target=self.target_ref())]
        if self.is_("export") or (self.peek().kind == "name" and self.peek(1).text == "is"):
            return self.declaration()
        raise self.error("expected patch, delete, when, final, or a new object (`Name is ...`)")

    def when(self) -> list[Op]:
        self.next()
        negate = False
        if self.is_("not"):
            self.next()
            negate = True
        self.expect("mod")
        mod_id = self.next()
        if mod_id.kind != "name":
            raise self.error("expected a mod id after `when mod`", mod_id)
        rng = ""
        while self.peek().text != "(" and self.peek().kind != "end":
            rng += self.next().text
        self.expect("(")
        ops = []
        while not self.is_(")"):
            if self.peek().kind == "end":
                raise self.error("this `when` block is never closed with ')'")
            ops += self.statement()
        self.expect(")")
        for o in ops:
            o.when = [(mod_id.text, rng or "*", negate)] + o.when
        return ops

    def patch(self) -> list[Op]:
        start = self.next()
        every = share = filter_ = None
        if self.is_("own", "shared"):
            share = self.next().text
        if self.is_("every"):
            self.next()
            cls = self.next()
            if cls.kind != "name":
                raise self.error("expected a class name after `patch every`", cls)
            every = cls.text
            if self.is_("["):
                filter_ = self.bracketed()
        if share is None and self.is_("own", "shared"):
            share = self.next().text
        target, sub = (None, "") if every else self.split_target(self.target_ref())
        ops = self.body()
        for o in ops:
            o.target, o.every, o.filter, o.share = target, every, filter_, share
            o.path = f"{sub}.{o.path}" if sub else o.path
        if not ops:
            raise self.error("empty patch", start)
        return ops

    def declaration(self) -> list[Op]:
        if self.is_("export"):
            self.next()
        name = self.next()
        if name.kind != "name":
            raise self.error("expected the new object's name", name)
        self.expect("is")
        if self.is_("clone"):
            self.next()
            src_tok = self.peek()
            source = self.target_ref()
            if source.startswith("~/"):  # a copy of something declared earlier in this file: same namespace
                local = source[2:].split(":")[0]
                if local not in self.declared:
                    raise self.error(f"~/{local} must be declared earlier in this file to be cloned", src_tok)
                namespace = self.declared[local].rsplit("/", 1)[0]
            elif source.startswith("@"):  # found by a property: the engine puts the copy in its source's file
                namespace = DEFAULT_NAMESPACE
            else:
                namespace = source.rsplit("/", 1)[0]
            full = f"{namespace}/{name.text}"
            self._declare(name, full)
            return [self.op("clone", name.line, target=full, source=source, body=self.body())]
        cls = self.next()
        if cls.kind != "name":
            raise self.error("expected a class name or `clone`", cls)
        full = f"{DEFAULT_NAMESPACE}/{name.text}"
        self._declare(name, full)
        return [self.op("create", name.line, target=full, cls=cls.text, body=self.body())]

    def _declare(self, name: _Tok, full: str) -> None:
        if name.text in self.declared:
            raise self.error(f"{name.text} is declared twice in this file", name)
        self.declared[name.text] = full

    def body(self) -> list[Op]:
        self.expect("(")
        ops = []
        while not self.is_(")"):
            if self.peek().kind == "end":
                raise self.error("this block is never closed with ')'")
            ops.append(self.member())
        self.expect(")")
        return ops

    def member(self) -> Op:
        override = False
        if self.is_("override"):
            self.next()
            override = True
        if self.is_("delete"):
            t = self.next()
            return self.op("delprop", t.line, path=self.prop_path(), override=override)
        start = self.peek()
        path = self.prop_path()
        if self.is_(".") and self.peek(1).text == "insert":
            self.next()
            self.next()
            return self.insert(path, start.line)
        sym = self.next()
        if sym.text == "=":
            return self.op("set", start.line, path=path, value=self.value(), override=override)
        if sym.text == "*=":
            return self.op("mul", start.line, path=path, value=self.number(), override=override)
        if sym.text in ("+=", "-="):
            if self.is_("["):
                kind = "append" if sym.text == "+=" else "remove"
                return self.op(kind, start.line, path=path, value=self.value().items, override=override)
            n = self.number()
            return self.op("add", start.line, path=path, value=n if sym.text == "+=" else -n, override=override)
        raise self.error("expected =, *=, += or -=", sym)

    def insert(self, path: str, line: int) -> Op:
        self.expect("(")
        where = self.next()
        if where.text not in ("after", "before", "at"):
            raise self.error("expected after=, before= or at=", where)
        self.expect("=")
        anchor = self.value()
        self.expect(",")
        self.expect("value")
        self.expect("=")
        value = self.value()
        self.expect(")")
        if where.text == "at":
            if not isinstance(anchor, Num):
                raise self.error("at= needs a position number")
            anchor = int(anchor.value)
        return self.op("insert", line, path=path, value=value, anchor=anchor, where=where.text)

    # --- paths and references ---
    def prop_path(self) -> str:
        t = self.next()
        if t.kind != "name":
            raise self.error("expected a property name", t)
        path = t.text
        while True:
            if self.is_("["):
                path += f"[{self.bracketed()}]"
            elif self.is_(".") and self.peek(1).kind == "name" and self.peek(1).text != "insert":
                self.next()
                path += "." + self.next().text
            else:
                return path

    def bracketed(self) -> str:
        """The text between `[` and `]`, tokens joined: a list index, a selector or a filter."""
        self.expect("[")
        inner = ""
        while not self.is_("]"):
            if self.peek().kind == "end":
                raise self.error("'[' is never closed")
            inner += self.next().text
        self.next()
        return inner

    def target_ref(self) -> str:
        t = self.next()
        if t.kind not in ("ref", "designator"):
            raise self.error("expected an object like $/GFX/Everything/Name, ~/Name or @TClass[Property=value]", t)
        return t.text

    @staticmethod
    def split_target(ref: str) -> tuple[str, str]:
        """`$/Name:Sub.Path` or `@TClass[Prop=v]:Sub.Path` -> (the object, the path inside it)."""
        if ref.startswith("@"):
            head, _, rest = ref.partition("]")
            return head + "]", rest[1:] if rest.startswith(":") else rest
        obj, _, sub = ref.partition(":")
        return obj, sub

    # --- values ---
    def number(self) -> Decimal:
        t = self.next()
        if t.kind != "number":
            raise self.error("expected a number", t)
        return _number(t.text)

    def value(self):
        t = self.peek()
        if t.kind == "number":
            self.next()
            return Num("float32" if re.search(r"[.eE]", t.text) and not t.text.lower().startswith(("0x", "-0x"))
                       else "int32", _number(t.text))
        if t.kind == "string":
            self.next()
            return Text("string", t.text[1:-1])
        if t.kind in ("ref", "designator"):
            self.next()
            return Ref(t.text)
        if t.kind == "shared":
            self.next()
            return Ref(t.text)
        if t.kind == "guid":
            self.next()
            return Raw(0x1A, uuid.UUID(t.text[6:-1]).bytes_le)
        if self.is_("["):
            return ListV(self.seq("[", "]"))
        if self.is_("("):
            items = self.seq("(", ")")
            if len(items) != 2:
                raise self.error(f"a pair holds exactly 2 values, this one has {len(items)}", t)
            return PairV(*items)
        if t.kind == "name":
            return self.named_value()
        raise self.error("expected a value")

    def seq(self, open_: str, close: str) -> list:
        self.expect(open_)
        items = []
        while not self.is_(close):
            items.append(self.value())
            if self.is_(","):
                self.next()
            elif not self.is_(close):
                raise self.error(f"expected ',' or {close!r}")
        self.expect(close)
        return items

    def named_value(self):
        t = self.next()
        word = t.text
        if word == "nil":
            return Ref(None)
        if word in ("true", "false"):
            return Num("bool", Decimal(1 if word == "true" else 0))
        if word == "MAP":
            self.expect("[")
            pairs = []
            while not self.is_("]"):
                p = self.value()
                if not isinstance(p, PairV):
                    raise self.error("a MAP holds pairs like (key, value)")
                pairs.append((p.a, p.b))
                if self.is_(","):
                    self.next()
            self.expect("]")
            return MapV(pairs)
        if word in _VECTORS:
            tc, fmt, n = _VECTORS[word]
            items = self.seq("[", "]")
            if len(items) != n or not all(isinstance(x, Num) for x in items):
                raise self.error(f"{word} needs {n} numbers", t)
            vals = [float(x.value) if "f" in fmt else int(x.value) for x in items]
            return Raw(tc, struct.pack(fmt, *vals))
        if word in _INT_TYPES or word in ("f64", "str", "wstr", "path", "key", "loc"):
            self.expect("(")
            arg = self.next()
            self.expect(")")
            if word in _INT_TYPES or word == "f64":
                if arg.kind != "number":
                    raise self.error(f"{word}() needs a number", arg)
                return Num("float64" if word == "f64" else word, _number(arg.text))
            if word == "key":
                return Text("key", arg.text)
            if arg.kind != "string":
                raise self.error(f"{word}() needs a quoted text", arg)
            return Text({"str": "string"}.get(word, word), arg.text[1:-1])
        raise self.error(f"unknown value {word!r}", t)


def _number(s: str) -> Decimal:
    neg = s.startswith("-")
    body = s[1:] if neg else s
    d = Decimal(int(body, 16)) if body.lower().startswith("0x") else Decimal(body)
    return -d if neg else d


def _resolve_locals(ops: list[Op], declared: dict[str, str], file: str) -> list[Op]:
    """Turn `~/Name` into the full name that Name was declared with in this file."""
    def fix(v):
        if isinstance(v, Ref) and v.target and v.target.startswith("~/"):
            local, _, sub = v.target[2:].partition(":")
            if local not in declared:
                raise RndfError(f"{file}: ~/{local} isn't declared in this file")
            return Ref(declared[local] + (":" + sub if sub else ""))
        if isinstance(v, ListV):
            return ListV([fix(x) for x in v.items])
        if isinstance(v, MapV):
            return MapV([(fix(k), fix(x)) for k, x in v.pairs])
        if isinstance(v, PairV):
            return PairV(fix(v.a), fix(v.b))
        return v

    def fix_name(name):
        return fix(Ref(name)).target if name and name.startswith("~/") else name

    for o in ops:
        o.target, o.source = fix_name(o.target), fix_name(o.source)
        o.value = [fix(x) for x in o.value] if isinstance(o.value, list) else fix(o.value)
        o.anchor = fix(o.anchor)
        for b in o.body:
            b.value = [fix(x) for x in b.value] if isinstance(b.value, list) else fix(b.value)
            b.anchor = fix(b.anchor)
    return ops


def parse(text: str, file: str = "<text>", mod: str = "") -> list[Op]:
    return Parser(text, file, mod).parse()
