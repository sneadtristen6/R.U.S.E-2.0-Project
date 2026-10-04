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

With a cache folder, load() keeps what it made there (the unit-data pack is the same on every build); a model loaded
from there has its files read only when save() changes them.
"""
from __future__ import annotations

import gc
import hashlib
import io
import os
import pickle
import struct
import sys
import threading
import zlib
from contextlib import contextmanager
from decimal import Decimal
from functools import lru_cache
from itertools import chain
from pathlib import Path

from .dic import key_to_name, name_to_key
from .ndf import Ndf, Value, local_ref, sub_values
from .patch import Game, Inline, ListV, MapV, Num, Obj, PairV, Raw, Ref, Text

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
    """One NDF file in the model: which objects are named, inline or shared, so it can be written back.

    `kept`: what an earlier load worked out for these same bytes (state()); the file itself is then read only when
    something needs it (ndf), which saving does only for the files that changed."""

    def __init__(self, path: str, raw: bytes, kept: tuple | None = None):
        self.path = game_path(path)
        self.raw = raw
        self._ndf: Ndf | None = None
        if kept is not None:
            self.names, self.inline, self.index_of, self.n_objects = kept
            return
        ndf = self.ndf
        users: dict[int, int] = {}
        for o in ndf.objects:
            for _pi, v in o.props:
                _count_refs(v, users)
        self.names: dict[int, str] = {}      # top-level object index -> name in the model
        self.inline: set[int] = set()
        for i in range(len(ndf.objects)):
            if i in ndf.exports:
                self.names[i] = ndf.exports[i]
            elif users.get(i, 0) == 1:
                self.inline.add(i)
            else:
                self.names[i] = f"{self.path}#{i}"
        self.index_of = {name: i for i, name in self.names.items()}
        self.n_objects = ndf._n_objects      # the objects the file had as read

    @property
    def ndf(self) -> Ndf:
        """The file itself, read on first use."""
        return self._ndf if self._ndf is not None else self._read()

    @property
    def prop_for(self) -> dict[tuple[int, str], int]:
        """Which PROP entry objects of each class use for each property name (the same name exists once per class)."""
        if self._ndf is None:
            self._read()
        return self._prop_for

    def _read(self) -> Ndf:
        ndf = Ndf(self.raw)
        self._prop_for: dict[tuple[int, str], int] = {}  # as the file was read, before anything changes it
        for o in ndf.objects:
            for pi, _v in o.props:
                self._prop_for.setdefault((o.cls, ndf.prop_name(pi)), pi)
        self._ndf = ndf
        return ndf

    def state(self) -> tuple:
        """What load() worked out for this file, to be kept with the model (NdfFile's `kept`)."""
        return self.names, self.inline, self.index_of, self.n_objects

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
        ndf = self.ndf
        o = ndf.objects[i]
        props = {}
        for pi, v in o.props:
            name = ndf.prop_name(pi)
            if name in props:
                raise ModelError(f"{self.path} #{i}: property {name} appears twice")
            props[name] = self.value(v, seen + (i,))
        return Obj(ndf.classes[o.cls], props, origin=(self.path, i))

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


def _count_refs(v: Value, users: dict[int, int]) -> None:
    """Count the local references in `v` and in every value inside it, per object index."""
    if v.tc == 0x09:
        r = local_ref(v)
        if r is not None:
            users[r] = users.get(r, 0) + 1
    elif v.tc in (0x11, 0x12, 0x22):
        for x in sub_values(v):
            _count_refs(x, users)


_HOLDERS = (ListV, Inline, MapV, PairV)  # the values that hold other values


def _inside(v):
    """The values directly inside a holder, in patch._walk_value's order."""
    if isinstance(v, ListV):
        return iter(v.items)
    if isinstance(v, Inline):
        return iter(v.obj.props.values())
    if isinstance(v, MapV):
        return chain.from_iterable(v.pairs)
    return iter((v.a, v.b))


def walked(obj: Obj) -> list:
    """Every value in `obj`, in the order patch._walk_obj gives them (the same list), made without a generator for
    each value."""
    out = []
    stack = [iter(obj.props.values())]
    while stack:
        for v in stack[-1]:
            out.append(v)
            if isinstance(v, _HOLDERS):
                stack.append(_inside(v))
                break
        else:
            stack.pop()
    return out


def parts_inside(obj: Obj) -> list[Obj]:
    """The unnamed parts inside `obj` (its Inline objects, at any depth), outermost first: those in walked(obj)."""
    out = []
    stack = [iter(obj.props.values())]
    while stack:
        for v in stack[-1]:
            if isinstance(v, _HOLDERS):
                if isinstance(v, Inline):
                    out.append(v.obj)
                stack.append(_inside(v))
                break
        else:
            stack.pop()
    return out


@contextmanager
def collector_paused():
    """Python's garbage collector paused while a whole model is made, kept or worked on: it looks through every object
    made so far, again and again as they grow in number, and almost none of them is garbage (2 of the 5 seconds a load
    took, 2026-10-04; a build of the unit data leaves about 13,000 objects for it, of millions). It runs again after,
    as before (not if it was off already)."""
    was = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if was:
            gc.enable()


def load(files: dict[str, bytes], cache=None) -> tuple[Game, dict[str, NdfFile]]:
    """Load NDF files (game path -> bytes) into one Game.

    With `cache` (a folder) the model is kept there, named by a fingerprint of everything it's made from (kept_path),
    and the same files load from there next time: the unit-data pack in about a second, against three to four made
    afresh (2026-10-04). A kept model that can't be read, or isn't whole, is ignored and made again."""
    kept = kept_path(files, cache) if cache is not None else None
    if kept is not None:
        got = _read_kept(kept, files)
        if got is not None:
            return got
    with collector_paused():
        game, loaded = _load(files)
        if kept is not None:
            _keep(kept, game, loaded)  # now, before anything changes the model
    return game, loaded


def _load(files: dict[str, bytes]) -> tuple[Game, dict[str, NdfFile]]:
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
        for v in walked(obj):
            if isinstance(v, Ref) and v.target and v.target not in game.objects:
                game.objects[v.target] = Obj(EXTERNAL)
    return game, loaded


# --- the kept model (load's `cache`) ---
KEPT_FORMAT = 1  # the kept models' layout: a new one means every model is loaded afresh
KEPT_MOST = 8    # kept models a cache folder holds at most, the most recently used: one per game build and set of .rmod
KEPT_DIGEST = 20  # bytes of the fingerprint at the start of a kept file, over the rest of it


@lru_cache(maxsize=1)
def code_version() -> bytes:
    """A fingerprint of the code that makes models: the platform's own Python files, or in an app built from them
    (which has none beside it) the app's program file. Any change to the code gives kept models other names. OSError
    when neither can be read (then nothing is kept)."""
    h = hashlib.blake2b(digest_size=20)
    h.update(sys.version.encode())
    here = Path(__file__).resolve().parent
    if Path(__file__).is_file():
        for f in sorted(here.rglob("*.py")):
            data = f.read_bytes()
            name = f.relative_to(here).as_posix().encode()
            h.update(struct.pack("<QQ", len(name), len(data)) + name)
            h.update(data)
    elif getattr(sys, "frozen", False) or "__compiled__" in globals():  # a built app: the code is in its program
        h.update(Path(sys.executable).read_bytes())
    else:
        raise OSError(f"the code at {here} can't be read")
    return h.digest()


def kept_path(files: dict[str, bytes], cache) -> Path | None:
    """Where the model of `files` is kept in the folder `cache`: named by a fingerprint of the files' paths and bytes
    in their order (which file comes first counts, for names two files share) and of the code (code_version). None
    when the code can't be read to tell."""
    try:
        code = code_version()
    except OSError:
        return None
    h = hashlib.blake2b(digest_size=20)
    h.update(f"model v{KEPT_FORMAT}".encode() + code)
    for p, raw in files.items():
        name = p.encode("utf-8", "surrogatepass")
        h.update(struct.pack("<QQ", len(name), len(raw)) + name)
        h.update(raw)
    return Path(cache) / f"model-{h.hexdigest()}.bin"


class _Unpickler(pickle.Unpickler):
    """Reads back only what a kept model holds: the model's own value types, and decimal numbers."""
    ALLOWED = {("decimal", "Decimal"): Decimal,
               **{("rusemod.patch", c.__name__): c for c in (Game, Obj, Num, Text, Ref, Inline, ListV, MapV, PairV,
                                                              Raw)}}

    def find_class(self, module, name):
        if (module, name) not in self.ALLOWED:
            raise pickle.UnpicklingError(f"a kept model doesn't hold {module}.{name}")
        return self.ALLOWED[(module, name)]


def _keep(kept: Path, game: Game, loaded: dict[str, NdfFile]) -> None:
    """Keep a model just loaded at `kept`, whole or not at all; then forget the least recently used beyond KEPT_MOST."""
    part = kept.with_name(f"{kept.name}.{os.getpid()}-{threading.get_ident()}.part")
    try:
        body = zlib.compress(pickle.dumps((KEPT_FORMAT, game, {p: nf.state() for p, nf in loaded.items()}),
                                          protocol=5), 1)
        kept.parent.mkdir(parents=True, exist_ok=True)
        part.write_bytes(hashlib.blake2b(body, digest_size=KEPT_DIGEST).digest() + body)
        part.replace(kept)  # two builds at once never read half a file
    except (OSError, pickle.PicklingError, TypeError, AttributeError, RecursionError):
        try:
            part.unlink(missing_ok=True)
        except OSError:
            pass
        return  # not kept: loaded afresh next time
    try:
        others = sorted(((f.stat().st_mtime, f) for f in kept.parent.glob("model-*.bin")), reverse=True)
    except OSError:
        return
    for _when, old in others[KEPT_MOST:]:
        try:
            old.unlink(missing_ok=True)
        except OSError:
            pass  # in use by another build: forgotten next time


def _read_kept(kept: Path, files: dict[str, bytes]) -> tuple[Game, dict[str, NdfFile]] | None:
    """The model kept at `kept` for `files`, or None when there's none, or it's damaged or not whole."""
    try:
        data = kept.read_bytes()
    except OSError:
        return None  # not kept yet
    try:
        body = data[KEPT_DIGEST:]
        if len(data) <= KEPT_DIGEST or hashlib.blake2b(body, digest_size=KEPT_DIGEST).digest() != data[:KEPT_DIGEST]:
            return None
        with collector_paused():
            fmt, game, states = _Unpickler(io.BytesIO(zlib.decompress(body))).load()
        if fmt != KEPT_FORMAT or not isinstance(game, Game) or not isinstance(states, dict):
            return None
        loaded = {}
        for p, raw in files.items():
            state = states.get(game_path(p))
            if not (isinstance(state, tuple) and len(state) == 4 and isinstance(state[0], dict)
                    and isinstance(state[1], set) and isinstance(state[2], dict) and isinstance(state[3], int)):
                return None
            loaded[game_path(p)] = NdfFile(p, raw, kept=state)
        if len(loaded) != len(states):
            return None
    except Exception:  # noqa: BLE001 - whatever is wrong with a kept file, the model is loaded afresh instead
        return None
    try:
        os.utime(kept)  # recently used: kept longest
    except OSError:
        pass
    return game, loaded


def _per_scenario(a: str, b: str) -> bool:
    """Two maps' or scenarios' own copies of one file (clustermap, mapterrain...), naming the same objects by design."""
    return any(f"/{d}/" in a and f"/{d}/" in b for d in ("scenario", "map")) \
        and a.rsplit("/", 1)[-1] == b.rsplit("/", 1)[-1]


def _by_origin(game: Game, parts: dict | None = None) -> dict[tuple, Obj]:
    """Every object and part of `game` that came from a file, by its origin. `parts`: parts_inside() of each object
    by name, when already worked out."""
    found = {}
    for name, obj in game.objects.items():
        for o in [obj] + (parts[name] if parts is not None else parts_inside(obj)):
            if o.origin is not None:
                if o.origin in found and found[o.origin] is not o:
                    raise ModelError(f"{o.origin[0]} #{o.origin[1]} appears twice after the mods ran")
                found[o.origin] = o
    return found


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
    yet (properties the game's classes have but its data never writes, set by the build itself). Only the files that
    get new objects or changes are read (NdfFile.ndf), and the files new parts are copied from, for their TOPO."""
    created = created or {}
    notes = notes if notes is not None else []
    inner = {name: parts_inside(obj) for name, obj in result.objects.items()}
    before, after = _by_origin(base), _by_origin(result, inner)
    topo_of: dict[str, set] = {}  # each file's TOPO entries as they were, when asked for

    def orig_topo(path: str) -> set:
        if path not in topo_of:
            topo_of[path] = set(loaded[path].ndf.topo) if path in loaded else set()
        return topo_of[path]
    topo_add: dict[str, list] = {p: [] for p in loaded}
    topo_drop: dict[str, set] = {p: set() for p in loaded}
    touched: set[str] = set()

    # 1. where each new named object goes, in creation order (a clone of a clone follows its source)
    new_named = [n for n, o in result.objects.items() if o.origin is None and o.cls != EXTERNAL]
    order = [n for n in created if n in new_named] + sorted(n for n in new_named if n not in created)
    home: dict[str, str] = {}
    for name in order:
        home[name] = _home_file(name, created.get(name), base, loaded, home)

    # 2. reserve an index for every new object: named ones with their parts, then new (copied) parts of existing
    # objects; parts outermost first
    new_objs = []
    for name in order:
        new_objs.append((home[name], result.objects[name], name))
        new_objs += [(home[name], p, None) for p in inner[name] if p.origin is None]
    for name, obj in result.objects.items():
        if obj.origin is not None and obj.cls != EXTERNAL:
            new_objs += [(obj.origin[0], p, None) for p in inner[name] if p.origin is None]
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
        elif obj.copied_from and obj.copied_from[1] in orig_topo(obj.copied_from[0]):
            topo_add[path].append(idx)
    for path, obj, name in new_objs:
        nf, idx = loaded[path], obj.origin[1]
        cls = nf.ndf.objects[idx].cls
        nf.ndf.objects[idx].props = [
            (nf.prop_index(cls, p, f"{path} #{idx}.{p}", may_add=True), nf.encode(v, f"{path} #{idx}.{p}"))
            for p, v in obj.props.items()]

    # 4. existing objects, file by file in index order: changed values re-encoded; deleted ones lose their name and
    # TOPO entry
    in_file: dict[str, list[int]] = {}
    for path, i in before:
        in_file.setdefault(path, []).append(i)
    for path, nf in loaded.items():
        for i in sorted(in_file.get(path, ())):
            if not 0 <= i < nf.n_objects:
                continue
            a, b = before[(path, i)], after.get((path, i))
            if b is None:
                if i in nf.ndf.exports:
                    notes.append(f"{nf.ndf.exports[i]} is deleted: it loses its name and stays unused in {path}")
                    nf.ndf.remove_export(i)
                if i in orig_topo(path):
                    topo_drop[path].add(i)
                touched.add(path)
                continue
            if a.props == b.props:
                continue
            nobj = nf.ndf.objects[i]
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
