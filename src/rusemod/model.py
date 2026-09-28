"""The bridge between game data files (NDF) and the rules engine's model (rusemod.patch).

load():  NDF files -> one `Game`. Named objects keep their export path; an unnamed object that exactly one other object
         uses becomes an `Inline` part of it (as in `ruse dump`); other unnamed objects are named `<file>#<index>`.
         Every object remembers where it came from (`Obj.origin`), and references to objects in files that weren't
         loaded get stand-ins, so they don't count as broken.
save():  the base `Game` and the engine's result -> new bytes for each file that changed. Values that didn't change
         keep their exact original bytes; changed values are re-encoded. Adding or removing objects (new units,
         deletes) is the next step and is reported as not supported yet.
"""
from __future__ import annotations

import struct
from decimal import Decimal

from .dic import key_to_name, name_to_key
from .ndf import Ndf, Value, local_ref, sub_values
from .patch import Game, Inline, ListV, MapV, Num, Obj, PairV, Raw, Ref, Text, _walk_obj

NUMBERS = {0x00: ("bool", "<B"), 0x01: ("int8", "<b"), 0x02: ("int32", "<i"), 0x03: ("uint32", "<I"),
           0x13: ("int64", "<q"), 0x18: ("int16", "<h"), 0x19: ("uint16", "<H"),
           0x05: ("float32", "<f"), 0x06: ("float64", "<d")}
KIND_CODE = {kind: (tc, fmt) for tc, (kind, fmt) in NUMBERS.items()}
EXTERNAL = "<external>"  # class of stand-ins for objects in files that weren't loaded


class ModelError(Exception):
    pass


def game_path(path: str) -> str:
    return path.replace("\\", "/").lower()


class NdfFile:
    """One NDF file in the model: which objects are named, inline or shared, so it can be written back."""

    def __init__(self, path: str, raw: bytes):
        self.path = game_path(path)
        self.raw = raw
        self.ndf = Ndf(raw)
        users: dict[int, int] = {}
        for o in self.ndf.objects:
            for _pi, v in o.props:
                for x in _values(v):
                    r = local_ref(x)
                    if r is not None:
                        users[r] = users.get(r, 0) + 1
        self.names: dict[int, str] = {}      # top-level object index -> name in the model
        self.inline: set[int] = set()
        for i in range(len(self.ndf.objects)):
            if i in self.ndf.exports:
                self.names[i] = self.ndf.exports[i]
            elif users.get(i, 0) == 1:
                self.inline.add(i)
            else:
                self.names[i] = f"{self.path}#{i}"
        self.index_of = {name: i for i, name in self.names.items()}
        # which PROP entry objects of each class use for each property name (the same name exists once per class)
        self.prop_for: dict[tuple[int, str], int] = {}
        for o in self.ndf.objects:
            for pi, _v in o.props:
                self.prop_for.setdefault((o.cls, self.ndf.prop_name(pi)), pi)

    def prop_index(self, cls: int, name: str, where: str) -> int:
        """The PROP entry to use for property `name` on an object of class `cls`."""
        if (cls, name) in self.prop_for:
            return self.prop_for[(cls, name)]
        same_class = [pi for pi, (n, c) in enumerate(self.ndf.props) if n == name and c == cls]
        if len(same_class) == 1:
            return same_class[0]
        raise ModelError(f"{where}: can't tell which {name} property objects of class "
                         f"{self.ndf.classes[cls]} use in this file (no object of that class sets it)")

    # --- NDF -> model ---
    def obj(self, i: int, seen=()) -> Obj:
        o = self.ndf.objects[i]
        props = {}
        for pi, v in o.props:
            name = self.ndf.prop_name(pi)
            if name in props:
                raise ModelError(f"{self.path} #{i}: property {name} appears twice")
            props[name] = self.value(v, seen + (i,))
        return Obj(self.ndf.classes[o.cls], props, origin=(self.path, i))

    def value(self, v: Value, seen):
        tc, b = v.tc, v.payload
        if tc in NUMBERS:
            kind, fmt = NUMBERS[tc]
            return Num(kind, Decimal(struct.unpack(fmt, b)[0]))
        if tc in (0x07, 0x1C):
            return Text("string" if tc == 0x07 else "path", self.ndf.strings[struct.unpack("<I", b)[0]])
        if tc == 0x08:
            return Text("wstr", b[4:4 + struct.unpack_from("<I", b)[0]].decode("utf-16-le"))
        if tc == 0x1D:
            k = struct.unpack("<Q", b)[0]
            return Text("key", key_to_name(k) or f"0x{k:016X}")
        if tc == 0x09:
            sub, idx = struct.unpack_from("<II", b)
            if sub == 0xAAAAAAAA:
                return Ref(self.ndf.imports.get(idx, f"<import #{idx}>"))
            if idx == 0xFFFFFFFF:
                return Ref(None)
            if idx in self.inline and idx not in seen:
                return Inline(self.obj(idx, seen))
            return Ref(self.names.get(idx, f"{self.path}#{idx}"))
        if tc == 0x11:
            return ListV([self.value(x, seen) for x in sub_values(v)])
        if tc == 0x12:
            items = sub_values(v)
            return MapV([(self.value(items[k], seen), self.value(items[k + 1], seen)) for k in range(0, len(items), 2)])
        if tc == 0x22:
            a, c = sub_values(v)
            return PairV(self.value(a, seen), self.value(c, seen))
        return Raw(tc, b)

    # --- model -> NDF ---
    def encode(self, v, where: str) -> Value:
        if isinstance(v, Num):
            if v.kind not in KIND_CODE:
                raise ModelError(f"{where}: unknown number type {v.kind}")
            tc, fmt = KIND_CODE[v.kind]
            x = float(v.value) if fmt in ("<f", "<d") else int(v.value)
            return Value(tc, struct.pack(fmt, x))
        if isinstance(v, Text):
            if v.kind in ("string", "path"):
                idx = self.ndf.string_index(v.value)
                if idx is None:
                    idx = self.ndf.add_string(v.value)
                return Value(0x07 if v.kind == "string" else 0x1C, struct.pack("<I", idx))
            if v.kind == "wstr":
                data = v.value.encode("utf-16-le")
                return Value(0x08, struct.pack("<I", len(data)) + data)
            if v.kind == "key":
                k = int(v.value, 16) if v.value.startswith("0x") else name_to_key(v.value)
                return Value(0x1D, struct.pack("<Q", k))
            raise ModelError(f"{where}: {v.kind} text needs the builder's text step first")
        if isinstance(v, Ref):
            if v.target is None:
                return Value(0x09, struct.pack("<III", 0xBBBBBBBB, 0xFFFFFFFF, 0xFFFFFFFF))
            if v.target in self.index_of:
                i = self.index_of[v.target]
                return Value(0x09, struct.pack("<III", 0xBBBBBBBB, i, self.ndf.objects[i].cls))
            for idx, path in self.ndf.imports.items():
                if path == v.target:
                    return Value(0x09, struct.pack("<II", 0xAAAAAAAA, idx))
            raise ModelError(f"{where}: refers to {v.target}, which this file doesn't import yet (adding imports "
                             f"is the next step)")
        if isinstance(v, Inline):
            origin = v.obj.origin
            if origin is None or origin[0] != self.path:
                raise ModelError(f"{where}: holds a new {v.obj.cls} part (new objects are the next step)")
            i = origin[1]
            return Value(0x09, struct.pack("<III", 0xBBBBBBBB, i, self.ndf.objects[i].cls))
        if isinstance(v, ListV):
            return Value(0x11, struct.pack("<I", len(v.items)) + b"".join(self.encode(x, where).encode() for x in v.items))
        if isinstance(v, MapV):
            return Value(0x12, struct.pack("<I", len(v.pairs)) + b"".join(
                self.encode(k, where).encode() + self.encode(x, where).encode() for k, x in v.pairs))
        if isinstance(v, PairV):
            return Value(0x22, self.encode(v.a, where).encode() + self.encode(v.b, where).encode())
        if isinstance(v, Raw):
            return Value(v.tc, v.payload)
        raise ModelError(f"{where}: can't write {type(v).__name__}")


def _values(v: Value):
    yield v
    for x in sub_values(v):
        yield from _values(x)


def load(files: dict[str, bytes]) -> tuple[Game, dict[str, NdfFile]]:
    """Load NDF files (game path -> bytes) into one Game."""
    loaded = {game_path(p): NdfFile(p, raw) for p, raw in files.items()}
    owner: dict[str, str] = {}
    for nf in loaded.values():
        for name in nf.names.values():
            if name in owner:
                raise ModelError(f"{name} is named in both {owner[name]} and {nf.path}")
            owner[name] = nf.path
    game = Game()
    for nf in loaded.values():
        for i, name in nf.names.items():
            game.objects[name] = nf.obj(i)
    for obj in list(game.objects.values()):  # stand-ins for objects in files that weren't loaded
        for v in _walk_obj(obj):
            if isinstance(v, Ref) and v.target and v.target not in game.objects:
                game.objects[v.target] = Obj(EXTERNAL)
    return game, loaded


def _by_origin(game: Game) -> dict[tuple, Obj]:
    found = {}
    for obj in game.objects.values():
        for o in [obj] + [v.obj for v in _walk_obj(obj) if isinstance(v, Inline)]:
            if o.origin is not None:
                if o.origin in found and found[o.origin] is not o:
                    raise ModelError(f"{o.origin[0]} #{o.origin[1]} appears twice after the mods ran")
                found[o.origin] = o
    return found


def save(base: Game, result: Game, loaded: dict[str, NdfFile]) -> dict[str, bytes]:
    """New bytes for every file whose content changed (game path -> NDF member bytes)."""
    new_objects = [n for n, o in result.objects.items() if o.origin is None and o.cls != EXTERNAL]
    if new_objects:
        raise ModelError(f"new objects ({', '.join(new_objects[:5])}) can't be written yet; adding objects is the next step")
    gone = [n for n, o in base.objects.items() if n not in result.objects and o.cls != EXTERNAL]
    if gone:
        raise ModelError(f"deleted objects ({', '.join(gone[:5])}) can't be written yet; that's the next step")
    before, after = _by_origin(base), _by_origin(result)
    out = {}
    for path, nf in loaded.items():
        changed = False
        for i, nobj in enumerate(nf.ndf.objects):
            a, b = before.get((path, i)), after.get((path, i))
            if a is None:
                continue
            if b is None:
                raise ModelError(f"{path} #{i} ({a.cls}) is gone after the mods ran (deleted, or a part that was "
                                 f"replaced); removing objects is the next step")
            if a.props == b.props:
                continue
            original = {nf.ndf.prop_name(pi): (pi, v) for pi, v in nobj.props}
            props = []
            for name, value in b.props.items():
                where = f"{path} #{i}.{name}"
                if name in original:  # existing property: keep its own PROP entry
                    pi, old = original[name]
                    props.append((pi, old if a.props.get(name) == value else nf.encode(value, where)))
                else:  # newly set property: the entry objects of this class use
                    props.append((nf.prop_index(nobj.cls, name, where), nf.encode(value, where)))
            nobj.props = props
            changed = True
        if changed:
            compressed = bool(struct.unpack_from("<I", nf.raw, 12)[0] & 0x80)
            out[path] = nf.ndf.to_member(compress=compressed)
    return out
