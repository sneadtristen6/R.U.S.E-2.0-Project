"""The bridge between game data files (NDF) and the rules engine's model (rusemod.patch).

load():  NDF files -> one `Game`. Named objects keep their export path; an unnamed object that exactly one other object
         uses becomes an `Inline` part of it (as in `ruse dump`); other unnamed objects are named `<file>#<index>`.
         Every object remembers where it came from (`Obj.origin`), and references to objects in files that weren't
         loaded get stand-ins, so they don't count as broken.
save():  the base `Game` and the engine's result -> new bytes for each file that changed. Values that didn't change
         keep their exact original bytes; changed values are re-encoded.
         New objects are appended to the file their clone source is in (a new object from scratch goes to the file
         holding the most names under its namespace); a new named object gets its export name and a TOPO entry, a
         copied part gets a TOPO entry if what it was copied from had one (the rule checked on all 2,176 files).
         References to objects in other files become imports. A deleted object loses its name and TOPO entry but
         stays in the file unused, so no other object's index ever moves.
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

    def prop_index(self, cls: int, name: str, where: str, may_add: bool = False) -> int:
        """The PROP entry to use for property `name` on an object of class `cls` (added for new classes)."""
        if (cls, name) in self.prop_for:
            return self.prop_for[(cls, name)]
        same_class = [pi for pi, (n, c) in enumerate(self.ndf.props) if n == name and c == cls]
        if len(same_class) == 1:
            return same_class[0]
        if not same_class and may_add:
            self.prop_for[(cls, name)] = self.ndf.add_prop(name, cls)
            return self.prop_for[(cls, name)]
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
            i = self.index_of.get(v.target)
            if i is None and v.target.startswith(f"{self.path}#") and v.target[len(self.path) + 1:].isdigit():
                i = int(v.target[len(self.path) + 1:])  # a part of this file that a mod made shared (patch._share)
                if i >= len(self.ndf.objects):
                    i = None
            if i is not None:
                return Value(0x09, struct.pack("<III", 0xBBBBBBBB, i, self.ndf.objects[i].cls))
            if v.target.startswith("$/"):  # a named object in another file: import it (reused if already imported)
                return Value(0x09, struct.pack("<II", 0xAAAAAAAA, self.ndf.import_index(v.target)))
            raise ModelError(f"{where}: refers to {v.target}, an unnamed object in another file, which can't be "
                             f"imported; name it or keep the reference inside one file")
        if isinstance(v, Inline):
            origin = v.obj.origin
            if origin is None or origin[0] != self.path:
                raise ModelError(f"{where}: holds a {v.obj.cls} part that wasn't placed in this file")
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
    game = Game()
    for nf in loaded.values():
        for i, name in list(nf.names.items()):
            if name in owner:  # MOD_FORMAT §14 q3: which copy the game uses is unknown, so say so
                alt = f"{nf.path}#{i}"
                if not _per_scenario(owner[name], nf.path):  # each scenario's own copy of a file: expected
                    game.notes.append(f"{name} is named in both {owner[name]} and {nf.path}; mods reach the first, "
                                      f"the second is {alt}")
                nf.names[i] = alt
                nf.index_of[alt] = nf.index_of.pop(name)
            else:
                owner[name] = nf.path
    for nf in loaded.values():
        for i, name in nf.names.items():
            game.objects[name] = nf.obj(i)
    for obj in list(game.objects.values()):  # stand-ins for objects in files that weren't loaded
        for v in _walk_obj(obj):
            if isinstance(v, Ref) and v.target and v.target not in game.objects:
                game.objects[v.target] = Obj(EXTERNAL)
    return game, loaded


def _per_scenario(a: str, b: str) -> bool:
    """Two scenarios' own copies of one file (clustermap, mapia...), which name the same objects by design."""
    return "/scenario/" in a and "/scenario/" in b and a.rsplit("/", 1)[-1] == b.rsplit("/", 1)[-1]


def _by_origin(game: Game) -> dict[tuple, Obj]:
    found = {}
    for obj in game.objects.values():
        for o in [obj] + [v.obj for v in _walk_obj(obj) if isinstance(v, Inline)]:
            if o.origin is not None:
                if o.origin in found and found[o.origin] is not o:
                    raise ModelError(f"{o.origin[0]} #{o.origin[1]} appears twice after the mods ran")
                found[o.origin] = o
    return found


def _new_parts(obj: Obj) -> list[Obj]:
    """New (copied) parts inside `obj`, outermost first."""
    return [v.obj for v in _walk_obj(obj) if isinstance(v, Inline) and v.obj.origin is None]


def _home_file(name: str, op, base: Game, loaded: dict[str, NdfFile], home: dict[str, str]) -> str:
    """Which file a new named object goes to (MOD_FORMAT §4)."""
    if op is not None and op.kind == "clone":
        if op.source in home:
            return home[op.source]
        src = base.objects.get(op.source)
        if src is not None and src.origin is not None:
            return src.origin[0]
        raise ModelError(f"{name}: can't tell which file its source {op.source} is in")
    namespace = name.rsplit("/", 1)[0] + "/"
    counts = {p: sum(1 for e in nf.ndf.exports.values() if e.startswith(namespace)) for p, nf in loaded.items()}
    best = max(sorted(counts), key=lambda p: counts[p], default=None)
    if best is None or counts[best] == 0:
        raise ModelError(f"{name}: no loaded file holds names under {namespace}, so there's nowhere to put it")
    return best


def save(base: Game, result: Game, loaded: dict[str, NdfFile], created: dict | None = None,
         notes: list | None = None, new_props=frozenset()) -> dict[str, bytes]:
    """New bytes for every file whose content changed (game path -> NDF member bytes). `created` is the engine's
    Result.created (where clones came from); `notes` collects what the build report should mention. `new_props`:
    (class, property) pairs that a file may get a PROP entry for when no object of that class in it sets the property
    yet (properties the game's classes have but its data never writes, set by the build itself)."""
    created = created or {}
    notes = notes if notes is not None else []
    before, after = _by_origin(base), _by_origin(result)
    orig_topo = {p: set(nf.ndf.topo) for p, nf in loaded.items()}
    topo_add: dict[str, list] = {p: [] for p in loaded}
    topo_drop: dict[str, set] = {p: set() for p in loaded}
    touched: set[str] = set()

    # 1. where each new named object goes, in creation order (a clone of a clone follows its source)
    new_named = [n for n, o in result.objects.items() if o.origin is None and o.cls != EXTERNAL]
    order = [n for n in created if n in new_named] + sorted(n for n in new_named if n not in created)
    home: dict[str, str] = {}
    for name in order:
        home[name] = _home_file(name, created.get(name), base, loaded, home)

    # 2. reserve an index for every new object: named ones with their parts, then new parts of existing objects
    new_objs = []
    for name in order:
        new_objs.append((home[name], result.objects[name], name))
        new_objs += [(home[name], p, None) for p in _new_parts(result.objects[name])]
    for obj in result.objects.values():
        if obj.origin is not None and obj.cls != EXTERNAL:
            new_objs += [(obj.origin[0], p, None) for p in _new_parts(obj)]
    for path, obj, name in new_objs:
        nf = loaded[path]
        idx = nf.ndf.add_object(nf.ndf.class_index(obj.cls), [])
        obj.origin = (path, idx)
        if name:
            nf.names[idx] = name
            nf.index_of[name] = idx
        touched.add(path)

    # 3. names and TOPO entries for the new objects, then their properties
    for path, obj, name in new_objs:
        idx = obj.origin[1]
        if name:
            loaded[path].ndf.add_export(name, idx)
            topo_add[path].append(idx)
        elif obj.copied_from and obj.copied_from[1] in orig_topo.get(obj.copied_from[0], ()):
            topo_add[path].append(idx)
    for path, obj, name in new_objs:
        nf, idx = loaded[path], obj.origin[1]
        cls = nf.ndf.objects[idx].cls
        nf.ndf.objects[idx].props = [
            (nf.prop_index(cls, p, f"{path} #{idx}.{p}", may_add=True), nf.encode(v, f"{path} #{idx}.{p}"))
            for p, v in obj.props.items()]

    # 4. existing objects: changed values re-encoded; deleted ones lose their name and TOPO entry
    for path, nf in loaded.items():
        for i in range(nf.ndf._n_objects):
            nobj = nf.ndf.objects[i]
            a, b = before.get((path, i)), after.get((path, i))
            if a is None:
                continue
            if b is None:
                if i in nf.ndf.exports:
                    notes.append(f"{nf.ndf.exports[i]} is deleted: it loses its name and stays unused in {path}")
                    nf.ndf.remove_export(i)
                if i in orig_topo[path]:
                    topo_drop[path].add(i)
                touched.add(path)
                continue
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
                    props.append((nf.prop_index(nobj.cls, name, where,
                                                may_add=(b.cls, name) in new_props), nf.encode(value, where)))
            nobj.props = props
            touched.add(path)

    # 5. TOPO, then the bytes
    out = {}
    for path in sorted(touched):
        nf = loaded[path]
        if topo_add[path] or topo_drop[path]:
            kept = [i for i in nf.ndf.topo if i not in topo_drop[path]]
            nf.ndf.set_topo(kept + [i for i in topo_add[path] if i not in kept])
        compressed = bool(struct.unpack_from("<I", nf.raw, 12)[0] & 0x80)
        out[path] = nf.ndf.to_member(compress=compressed)
    return out
