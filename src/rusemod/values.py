"""Every value of the game's unit data, for the Studio's Values tab (LittleGroove's raw value editor in RUSE Mod Manager,
brought over): the data files a mod can change, the objects in them, one object's values as the game's file has them,
and what the modder types turned into a value of the mod file (rusemod.rndf.literal), checked against the game's.

A mod changes the unit data pack (rusemod.build.DEFAULT_PACK), so that's what the tab offers: its files, without the
debug-info copies the build leaves as shipped. An object is shown from the file itself, not the game index: the index
keeps only the first numbers and texts of each object (rusemod.index), the file has all of them (positions, colours,
long lists, maps). The index still names everything (addresses, links, who uses what).
"""
from __future__ import annotations

import re
import struct
import uuid
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .build import DEFAULT_PACK, SHADOW
from .model import NdfFile
from .patch import INT_RANGES, Inline, ListV, MapV, Num, PairV, Raw, Ref, Text
from .rndf import RndfError, float32_text, literal, parse_value

PACK = DEFAULT_PACK
WHOLE = set(INT_RANGES) - {"bool"}
VECTORS = {0x21: ("Float2", 2, "f"), 0x0B: ("Float3", 3, "f"), 0x0C: ("Float4", 4, "f"), 0x1F: ("Int2", 2, "i"),
           0x0D: ("RGBA", 4, "B")}
GUID = 0x1A
CONTAINERS = {ListV: "list", MapV: "map", PairV: "pair"}
_SPLIT = re.compile(r"[\s,;]+")


class TypedError(ValueError):
    """What the modder typed doesn't fit the value (the message says what would)."""


class Spelled(str):
    """A value for the mod file, already spelled as the mod file spells it (rusemod.rndf.literal)."""


class Linked(str):
    """A link to a named object, by its address."""


# --- the files and the objects in them ---
def files(ix) -> list[dict]:
    """The data files a mod can change: [{path (the file's place in the pack), objects}], by path."""
    rows_ = ix.db.execute("""SELECT f.display, n.objects FROM ndf n JOIN file f ON f.id = n.file JOIN pack p ON p.id = f.pack
                             WHERE p.name = ? AND p.layer = 'core' ORDER BY f.display""", (PACK,)).fetchall()
    return [{"path": path.replace("\\", "/"), "objects": n} for path, n in rows_ if not SHADOW.search(path.lower())]


def _location(path: str) -> str:
    return f"{PACK}!{path.replace('/', chr(92))}"


def find(ix, file: str = "", words: str = "", prop: str = "", value: str = "", limit: int = 300) -> tuple[list, int]:
    """Objects of the unit data: in one file (`file`, as files() names it; "" for every file), whose name or class has
    each of `words`, and (when `prop` or `value` is given) a value whose property has `prop` and whose number, text or
    link has `value`. ([{address, class, export, file, index, match}], how many there are in all); named objects first.
    `match`: the value found ("Prop = 12"), when looking by value."""
    where = ["p.name = ?", "p.layer = 'core'", "o.shadow = 0"]
    args: list = [PACK]
    if file:
        where.append("f.location = ?")
        args.append(_location(file))
    for word in _SPLIT.split(words.strip()) if words.strip() else []:
        where.append("(o.address LIKE ? OR o.class LIKE ?)")
        args += [f"%{word}%", f"%{word}%"]
    joins, match = "", "NULL"
    if prop.strip() or value.strip():
        # a value of the object (a number or a text) or a link it holds, whose property and shown value fit
        joins = """JOIN (SELECT v.object AS oid, v.path AS path, COALESCE(v.text, CAST(v.num AS TEXT)) AS shown
                         FROM value v
                         UNION ALL
                         SELECT r.src, r.path, COALESCE(d.address, r.target) FROM ref r
                         LEFT JOIN object d ON d.id = r.dst) m ON m.oid = o.id"""
        if prop.strip():
            where.append("m.path LIKE ?")
            args.append(f"%{prop.strip()}%")
        if value.strip():
            where.append("(m.shown LIKE ? OR m.shown = ?)")
            args += [f"%{value.strip()}%", _number_text(value.strip())]
        match = "m.path || ' = ' || m.shown"
    sql = f"""FROM object o JOIN file f ON f.id = o.file JOIN pack p ON p.id = f.pack {joins}
              WHERE {' AND '.join(where)}"""
    total = ix.db.execute(f"SELECT COUNT(DISTINCT o.id) {sql}", args).fetchone()[0]
    found = ix.db.execute(f"""SELECT o.address, o.class, o.export, f.display, o.idx, MIN({match}) {sql}
                              GROUP BY o.id ORDER BY o.export IS NULL, o.address LIMIT ?""", args + [limit]).fetchall()
    return [{"address": a, "class": c, "export": e, "file": d.replace("\\", "/"), "index": i, "match": m}
            for a, c, e, d, i, m in found], total


def _number_text(text: str) -> str:
    """A typed number as the index prints a number it keeps (12 -> 12.0), so looking for 12 finds 12."""
    try:
        return repr(float(text))
    except ValueError:
        return text


def read(arc, file: str) -> NdfFile:
    """One data file of the unit data pack `arc` (an Edat), as the build's model reads it."""
    entry = arc.entry(file)
    if entry is None:
        raise KeyError(f"the unit data has no file {file}")
    return NdfFile(file, bytes(arc.read(entry)))


# --- one object's values ---
def number(v: Num):
    """A number of the model as the modder should see it: 12, not 12.0; 0.1, not the float32's 0.100000001."""
    if v.kind in WHOLE or v.kind == "bool":
        return int(v.value)
    x = float(v.value)
    if v.kind == "float32":
        x = float(float32_text(x))
    return int(x) if x.is_integer() and abs(x) < 2**53 else x


def _text(v) -> str | None:
    try:
        return literal(v)
    except ValueError:
        return None


def row(prop: str, v, links: dict[str, str]) -> dict:
    """One property of an object as the Values tab shows it: `kind` (what sort of value, which picks how it's
    changed), `type` (the game's type), `value` (numbers, a text, a key's name, a link's address), `text` (the value as
    a mod file spells it: None when a mod file can't, so it can't be changed here), `to` (where a link or a part
    leads, as the game index names it) and, for lists, maps and pairs, `items` (the parts and links inside, each with
    `to`) and `count`."""
    out = {"prop": prop, "text": _text(v), "value": None}
    if isinstance(v, Num):
        out.update(kind="bool" if v.kind == "bool" else "number", type=v.kind, value=number(v))
    elif isinstance(v, Text):
        out.update(kind="key" if v.kind == "key" else "text", type=v.kind, value=v.value)
    elif isinstance(v, Ref):
        named = v.target if v.target and v.target.startswith("$/") else None
        to = links.get(prop, named)
        out.update(kind="link", type="reference", value=to or v.target, to=to)
    elif isinstance(v, Inline):
        out.update(kind="part", type=v.obj.cls, to=links.get(prop))
    elif isinstance(v, Raw) and v.tc in VECTORS:
        word, n, fmt = VECTORS[v.tc]
        out.update(kind="vector", type=word)
        if len(v.payload) == struct.calcsize(f"<{n}{fmt}"):
            items = struct.unpack(f"<{n}{fmt}", v.payload)
            out["value"] = [number(Num("float32", Decimal(x))) for x in items] if fmt == "f" else list(items)
    elif isinstance(v, Raw) and v.tc == GUID:
        out.update(kind="guid", type="guid")
        if len(v.payload) == 16:
            out["value"] = str(uuid.UUID(bytes_le=bytes(v.payload)))
    elif isinstance(v, ListV) and v.items and all(isinstance(x, Num) for x in v.items):
        out.update(kind="numbers", type=v.items[0].kind, value=[number(x) for x in v.items])
    elif isinstance(v, tuple(CONTAINERS)):
        out.update(kind=CONTAINERS[type(v)], type=CONTAINERS[type(v)])
        out["items"] = [{"path": p, "to": links.get(p, x.target if isinstance(x, Ref) else None),
                         "part": isinstance(x, Inline), "class": x.obj.cls if isinstance(x, Inline) else None}
                        for p, x in _inside(v, prop) if isinstance(x, Inline) or (isinstance(x, Ref) and x.target)]
        out["count"] = len(v.items) if isinstance(v, ListV) else len(v.pairs) if isinstance(v, MapV) else 2
    else:
        out.update(kind="fixed", type=f"0x{v.tc:02X}" if isinstance(v, Raw) else type(v).__name__,
                   value=f"{len(v.payload)} bytes" if isinstance(v, Raw) else None)
    return out


def _inside(v, path: str):
    """(path, value) of the values inside a list, map or pair (and inside those), the way the game index names their
    places: `List[0]`, `Map[0].k` / `Map[0].v`, `Pair.0` / `Pair.1`."""
    if isinstance(v, ListV):
        parts = [(f"{path}[{i}]", x) for i, x in enumerate(v.items)]
    elif isinstance(v, MapV):
        parts = [p for i, (k, x) in enumerate(v.pairs) for p in ((f"{path}[{i}].k", k), (f"{path}[{i}].v", x))]
    elif isinstance(v, PairV):
        parts = [(f"{path}.0", v.a), (f"{path}.1", v.b)]
    else:
        return
    for p, x in parts:
        yield p, x
        yield from _inside(x, p)


def rows(obj, links: dict[str, str]) -> list[dict]:
    """Every property of `obj` (a model Obj), in the file's order."""
    return [row(prop, v, links) for prop, v in obj.props.items()]


# --- what the modder types, as a value of the mod file ---
def _num(text, what: str) -> Decimal:
    t = str(text).strip()
    if t.count(",") == 1 and "." not in t:  # 0,5: a decimal comma
        t = t.replace(",", ".")
    try:
        d = Decimal(t)
    except InvalidOperation:
        raise TypedError(f"{what}: {text!r} isn't a number") from None
    if not d.is_finite():
        raise TypedError(f"{what}: {text!r} isn't a number")
    return d


def _fitted(d: Decimal, kind: str, what: str):
    """A typed number in the property's type, as the build will store it: whole numbers rounded half away from zero
    and checked against their range, float32s to the nearest float32."""
    if kind in WHOLE or kind == "bool":
        r = int(d.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        lo, hi = (0, 1) if kind == "bool" else INT_RANGES[kind]
        if not lo <= r <= hi:
            raise TypedError(f"{what}: {r} doesn't fit (it must be {lo} to {hi})")
        return r
    x = float(d)
    if kind == "float32":
        try:
            x = struct.unpack("<f", struct.pack("<f", x))[0]
        except OverflowError:
            raise TypedError(f"{what}: {d} is too big") from None
        return number(Num("float32", Decimal(x)))
    return int(x) if x.is_integer() and abs(x) < 2**53 else x


def _numbers(text, what: str) -> list[Decimal]:
    if isinstance(text, (list, tuple)):
        return [_num(x, what) for x in text]
    return [_num(p, what) for p in _SPLIT.split(str(text).strip().strip("[]")) if p]


def _byte(d: Decimal, what: str) -> int:
    r = int(d.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if not 0 <= r <= 255:
        raise TypedError(f"{what}: {r} doesn't fit (a colour's parts are 0 to 255)")
    return r


def typed(old, text, prop: str, named, game_to: str | None = None) -> tuple[object, bool]:
    """What the modder typed (`text`: a string, a number, a yes/no or a list of numbers) for property `prop`, whose
    game value is `old` (a model value), as the mod file's value: a number or a list of numbers (the build gives them
    the property's type), a Linked address, or Spelled text (rusemod.rndf). `named(address)`: whether a link may point
    there; `game_to`: the game index's address of what the game's link points at (the same link, when typed again).
    Returns (the value, whether it is the game's own value again). TypedError when it doesn't fit."""
    game_text = _text(old)
    if isinstance(old, Num):
        if isinstance(text, bool) or (old.kind == "bool" and str(text).strip().lower() in ("true", "false", "yes", "no")):
            text = 1 if str(text).strip().lower() in ("true", "yes") else 0
        value = _fitted(_num(text, prop), old.kind, prop)
        return value, value == number(old)
    if isinstance(old, Text):
        s = str(text)
        if old.kind == "key":
            s = s.strip()
            if not re.fullmatch(r"0x[0-9A-Fa-f]{1,16}", s):
                from .dic import name_to_key
                try:
                    name_to_key(s)
                except ValueError:
                    raise TypedError(f"{prop}: {s!r} isn't a text key (up to 10 letters, digits and _)") from None
        try:
            out = literal(Text(old.kind, s))
        except ValueError as exc:
            raise TypedError(f"{prop}: {exc}") from None
        return Spelled(out), out == game_text
    if isinstance(old, Ref):
        s = str(text or "").strip()
        if s in ("", "nil"):
            return Spelled("nil"), old.target is None
        if not named(s):
            # not a game rule: a link has to point at something the game's data (the index) has
            raise TypedError(f"{prop}: there's nothing at {s} in the game data to link to")
        return Linked(s), s in (old.target, game_to)
    if isinstance(old, Raw) and old.tc in VECTORS:
        word, n, fmt = VECTORS[old.tc]
        got = _numbers(text, prop)
        if len(got) != n:
            raise TypedError(f"{prop}: {n} numbers, one for each part of a {word}")
        if fmt == "f":
            items = [struct.unpack("<f", struct.pack("<f", float(x)))[0] for x in got]
        elif fmt == "i":
            items = [_fitted(x, "int32", prop) for x in got]
        else:
            items = [_byte(x, prop) for x in got]
        out = literal(Raw(old.tc, struct.pack(f"<{n}{fmt}", *items)))
        return Spelled(out), out == game_text
    if isinstance(old, Raw) and old.tc == GUID:
        try:
            g = uuid.UUID(str(text).strip().strip("{}"))
        except ValueError:
            raise TypedError(f"{prop}: {text!r} isn't a GUID (32 hexadecimal digits)") from None
        out = literal(Raw(GUID, g.bytes_le))
        return Spelled(out), out == game_text
    if isinstance(old, ListV) and old.items and all(isinstance(x, Num) for x in old.items):
        kind = old.items[0].kind
        got = [_fitted(x, kind, prop) for x in _numbers(text, prop)]
        if not got:
            return Spelled("[]"), False
        return got, got == [number(x) for x in old.items]
    if isinstance(old, tuple(CONTAINERS)) and game_text is not None:
        try:
            new = parse_value(str(text))
        except RndfError as exc:
            raise TypedError(f"{prop}: {exc}") from None
        if type(new) is not type(old):
            raise TypedError(f"{prop}: it's a {CONTAINERS[type(old)]}, so the new value must be one too")
        for v in _all(new):
            if isinstance(v, Ref) and v.target and not named(v.target):
                # not a game rule: a link has to point at something the game's data (the index) has
                raise TypedError(f"{prop}: there's nothing at {v.target} in the game data to link to")
        try:
            out = literal(_like(new, old))
        except ValueError as exc:
            raise TypedError(f"{prop}: {exc}") from None
        return Spelled(out), out == game_text
    raise TypedError(f"{prop} can't be changed here: a mod file can't write this kind of value")


def _all(v):
    yield v
    if isinstance(v, ListV):
        for x in v.items:
            yield from _all(x)
    elif isinstance(v, MapV):
        for k, x in v.pairs:
            yield from _all(k)
            yield from _all(x)
    elif isinstance(v, PairV):
        yield from _all(v.a)
        yield from _all(v.b)


def _like(new, old):
    """`new` with each number in the type of the game's number at the same place (the last one's, for a list that
    grew), and texts in the game's kind of text, as the build reads a value into a property: `[1, 2]` typed for a list
    of float32s stays float32s, `'a.png'` for a file path stays a file path."""
    if isinstance(new, Num) and isinstance(old, Num):
        return Num(old.kind, new.value)
    if isinstance(new, Text) and isinstance(old, Text) and new.kind == "string":
        return Text(old.kind, new.value)
    if isinstance(new, ListV) and isinstance(old, ListV) and old.items:
        return ListV([_like(x, old.items[min(i, len(old.items) - 1)]) for i, x in enumerate(new.items)])
    if isinstance(new, MapV) and isinstance(old, MapV) and old.pairs:
        out = []
        for i, (k, x) in enumerate(new.pairs):
            ok, ox = old.pairs[min(i, len(old.pairs) - 1)]
            out.append((_like(k, ok), _like(x, ox)))
        return MapV(out)
    if isinstance(new, PairV) and isinstance(old, PairV):
        return PairV(_like(new.a, old.a), _like(new.b, old.b))
    return new
