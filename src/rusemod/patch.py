"""The mod rules engine: applies mod operations to a game model, following docs/MOD_FORMAT.md §10 exactly.

It works on a plain model of the game (objects with properties), not on NDF bytes: an adapter turns NDF files into
this model and back (M2). That keeps every rule testable without game files.

Model: named top-level objects (`Game.objects`, keyed by export path or `#<n>` for shared unnamed ones), each an `Obj`
with a class and ordered properties. A property holds a `Num`, `Text`, `Ref` (to another object, or nil), `Inline`
(an unnamed object only its owner uses), `ListV`, `MapV` or `Raw` (anything the engine only copies).

Rules, in short: operations run in load order, then the `final` ones; every operation sees the game as the ones
before it left it; math is exact and rounds once at the end (half away from zero); each pair of operations by two
different mods on the same thing gives the error / warning / note of the §10.4 table.

Objects are named by export path, or found by a property value (`@TAmmunition[AmmunitionId=1120]`, MOD_FORMAT §4):
exactly one object, of that class or of any class (`@[ClassNameForDebug='Unit_M4_Sherman']`), named or an unnamed
part of another object. `patch every <class> [Prop=value]` takes all of them. A reference to a part of a game
object (`$/X:Weapons[0].Ammunition`, or `@...:path`) makes that part a shared object with a name of its own.
"""
from __future__ import annotations

import copy
import re
import struct
from bisect import bisect_left
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from operator import itemgetter

INT_RANGES = {"bool": (0, 255), "int8": (-2**7, 2**7 - 1), "int16": (-2**15, 2**15 - 1), "uint16": (0, 2**16 - 1),
              "int32": (-2**31, 2**31 - 1), "uint32": (0, 2**32 - 1), "int64": (-2**63, 2**63 - 1)}


# --- the game model ---
@dataclass
class Num:
    kind: str          # bool int8 int16 uint16 int32 uint32 int64 float32 float64
    value: Decimal


@dataclass
class Text:
    kind: str          # string wstr path key loc
    value: str


@dataclass
class Ref:
    target: str | None  # an object name, or None for nil


@dataclass
class Inline:
    obj: "Obj"


@dataclass
class ListV:
    items: list


@dataclass
class MapV:
    pairs: list        # [(key value, value)]


@dataclass
class PairV:
    a: object
    b: object


@dataclass
class Raw:
    tc: int
    payload: bytes


@dataclass
class Obj:
    cls: str
    props: dict = field(default_factory=dict)
    origin: tuple | None = field(default=None, compare=False)  # (game file, object index) it was read from; None = new
    copied_from: tuple | None = field(default=None, compare=False)  # for copies: the origin of what was copied


@dataclass
class Game:
    objects: dict = field(default_factory=dict)   # name -> Obj
    files: dict = field(default_factory=dict)     # game path -> bytes
    notes: list = field(default_factory=list)     # things noticed while loading, for the build report
    # name -> the Obj this game still has in common with the game it was copied from (lazy_copy), until it's changed
    shared: dict = field(default_factory=dict, compare=False, repr=False)

    def own(self, name: str) -> Obj:
        """The top-level object `name`, to change in place. One this game still has in common with the game it was
        copied from (lazy_copy) is copied first, with its parts, so that game never changes."""
        obj = self.objects[name]
        if self.shared.pop(name, None) is obj:
            obj = copy.deepcopy(obj)
            self.objects[name] = obj
        return obj

    def own_part(self, name: str, path: str) -> Obj:
        """The part at `path` ("" for the object itself, "SubClusterList[1]" as _parts names it) of the top-level
        object `name`, to change in place (own)."""
        return part_at(self.own(name), path)

    def shares(self, name: str) -> bool:
        """Whether the top-level object `name` is still the same object as in the game this one was copied from."""
        return name in self.shared and self.shared[name] is self.objects.get(name)


def lazy_copy(game: Game) -> Game:
    """A copy of `game` to change: lists of objects and files of its own, the objects themselves in common with `game`
    until one is changed (Game.own copies it first), so `game` never changes. A build changes a few of the unit data's
    21,926 top-level objects; copying them all took 6.7 to 9.3 s of each build (measured 2026-10-04)."""
    return Game(dict(game.objects), dict(game.files), list(game.notes), shared=dict(game.objects))


def num(v, kind="int32") -> Num:
    return Num(kind, Decimal(str(v)))


def nums(values, kind="int32") -> ListV:
    return ListV([num(v, kind) for v in values])


# --- operations ---
PROP_KINDS = {"set", "mul", "add", "append", "remove", "insert", "delprop"}


@dataclass
class Op:
    kind: str                       # set mul add append remove insert delprop create clone delobj replacefile addfile
    target: str | None = None       # object name (the new name for create / clone; the path for file operations)
    path: str = ""                  # property path inside the object: "Weapons[0].Ammunition.Puissance"
    value: object = None            # set: a value; mul / add: a number; append / remove: a list; insert: one value
    anchor: object = None           # insert: the item to go next to, or an index for where="at"
    where: str = "after"            # insert: after | before | at
    cls: str | None = None          # create: class
    source: str | None = None       # clone: the object copied
    body: list = field(default_factory=list)   # create / clone: property operations on the new object
    every: str | None = None        # `patch every <class>`
    filter: str | None = None       # `patch every <class> [Prop=value]`: only objects whose Prop has that value
    final: bool = False
    override: bool = False
    share: str | None = None        # own | shared
    when: list = field(default_factory=list)   # [(mod id, version range, negate)]
    mod: str = ""
    file: str = ""
    line: int = 0

    def at(self) -> str:
        return f"{self.mod} ({self.file}:{self.line})" if self.file else self.mod


@dataclass
class Finding:
    level: str          # error | warning | note
    message: str
    op: Op | None = None


@dataclass
class Result:
    game: Game
    findings: list
    trail: dict         # (object, path) -> [(op, value after)]
    created: dict = field(default_factory=dict)  # new object name -> the create / clone operation, in order

    def _level(self, level):
        return [f for f in self.findings if f.level == level]

    @property
    def errors(self):
        return self._level("error")

    @property
    def warnings(self):
        return self._level("warning")

    @property
    def notes(self):
        return self._level("note")

    def history(self, obj: str, path: str) -> list[str]:
        """The chain of operations that produced a value: `mod (file:line): <kind> -> value`."""
        return [f"{op.at()}: {op.kind} -> {show(v)}" for op, v in self.trail.get((obj, path), [])]


class PatchError(Exception):
    pass


ENTRY = "(map entry)"  # one entry of a map, as a path sees it: `Map[i].k` is its key, `Map[i].v` its value


class _EntryProps(dict):
    """The key ("k") and value ("v") of one map entry as a part's properties; a change goes into the map."""

    def __init__(self, mapv: MapV, i: int):
        super().__init__(k=mapv.pairs[i][0], v=mapv.pairs[i][1])
        self.mapv, self.i = mapv, i

    def __setitem__(self, key, value):
        if key not in ("k", "v"):
            raise PatchError(f"a map entry has k (its key) and v (its value), not {key}")
        super().__setitem__(key, value)
        self.mapv.pairs[self.i] = (self["k"], self["v"])

    def pop(self, key, *default):
        raise PatchError("a map entry's key or value can't be deleted")


def show(v) -> str:
    if isinstance(v, Num):
        return format(v.value.normalize(), "f") if v.value == v.value.to_integral() else str(v.value)
    if isinstance(v, ListV):
        return "[" + ", ".join(show(x) for x in v.items) + "]"
    if isinstance(v, Ref):
        return v.target or "nil"
    if isinstance(v, Text):
        return repr(v.value)
    if isinstance(v, Inline):
        return f"{v.obj.cls}(…)"
    return type(v).__name__ if v is not None else "(absent)"


_SEG = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)((?:\[[^\]]*\])*)$")


def _parse_path(path: str) -> list[tuple[str, list[str]]]:
    segs = []
    for part in path.split("."):
        m = _SEG.match(part)
        if not m:
            raise PatchError(f"bad property path {path!r}")
        segs.append((m.group(1), re.findall(r"\[([^\]]*)\]", m.group(2))))
    return segs


# --- the engine ---
class Engine:
    def __init__(self, game: Game):
        # the caller's game stays as it was: the build compares the two to write only what changed (model.save), and
        # reads the game as shipped after (build.unit_classes, build.unit_models). Every change in place goes through
        # _own (Game.own), which copies an object the two still have in common first.
        self.game = lazy_copy(game)
        self.findings: list[Finding] = []
        self.touch = defaultdict(list)     # (object, path) -> [(op, category, items)]
        self.obj_log = defaultdict(list)   # object -> [op] (property operations, for patch-then-delete)
        self.deleted: dict[str, Op] = {}
        self.created: dict[str, Op] = {}
        self.file_log: dict[str, Op] = {}
        self.trail = defaultdict(list)
        self._gen = 0                      # bumped whenever objects appear, disappear or parts are shared
        self._index_gen, self._by_class, self._all = -1, {}, []
        from .unitflags import truck_flags  # the truck-only flags units carry before any mod (_truck_flags)
        self._had_truck_flags = {n: f for n, o in self.game.objects.items() if (f := truck_flags(o))}
        from . import unitcheck  # what's wrong with the units before any mod: not the mods' doing (_unit_rules)
        self._had_unit = {n: {why for _lvl, _prop, why in unitcheck.problems(o)}
                          for n, o in self.game.objects.items() if unitcheck.is_unit(o)}
        self._had_ids = unitcheck.ids(self.game)
        self._had_salvos = {(top, path, why) for top, path, _named, why in unitcheck.salvo_problems(self.game)}
        self._had_research = set(unitcheck.research_parent_problems(
            self.game, [n for n, o in self.game.objects.items() if unitcheck.is_unit(o)]).items())
        self._done: list = []  # (owner, path, op) of every property operation, in the order they ran
        self._kinds: dict | None = None  # (class, property) -> the number type the game gives it (_kind_in_class)

    def run(self, mods) -> Result:
        """`mods`: [(ModInfo, [Op])] already in load order (resolve.load_order)."""
        present = {m.id: m.version for m, _ in mods}
        ops = [op for _, mod_ops in mods for op in mod_ops if self._when_ok(op, present)]
        for op in [o for o in ops if not o.final] + [o for o in ops if o.final]:
            try:
                self.apply(op)
            except PatchError as exc:
                self._find("error", str(exc), op)
        self._finish()
        return Result(self.game, self.findings, dict(self.trail), dict(self.created))

    @staticmethod
    def _when_ok(op: Op, present: dict) -> bool:
        from .resolve import matches
        for mod_id, rng, negate in op.when:
            has = mod_id in present and matches(present[mod_id], rng or "*")
            if has == negate:
                return False
        return True

    def _find(self, level: str, message: str, op: Op | None = None) -> None:
        if level == "warning" and op is not None and op.override:
            level = "note"
        self.findings.append(Finding(level, message, op))

    def _own(self, name: str) -> Obj:
        """The top-level object `name`, to change in place (Game.own). When that copies it, the find index
        (_objects_of) is pointed at the copy's parts, so filters see the changes made to it."""
        old = self.game.objects[name]
        obj = self.game.own(name)
        if obj is not old and self._index_gen == self._gen:
            new = dict(zip((id(o) for _p, o in _parts(old)), (o for _p, o in _parts(obj))))  # same parts, same order
            classes = {o.cls for o in new.values()}
            for found in [self._all] + [self._by_class[c] for c in classes if c in self._by_class]:
                i = bisect_left(found, name, key=itemgetter(0))  # (in name order, one object's parts together)
                while i < len(found) and found[i][0] == name:
                    found[i] = (name, found[i][1], new.get(id(found[i][2]), found[i][2]))
                    i += 1
        return obj

    # --- dispatch ---
    def apply(self, op: Op) -> None:
        if op.kind in PROP_KINDS:
            if op.every:
                found = self._objects_of(op.every, op.filter)
                if not found:
                    # not a game rule: the game or one of its files isn't found
                    raise PatchError(f"{op.at()} patches every {_what(op.every, op.filter)}, but none exists in this "
                                     f"game build (after a game update, this needs a rebase)")
                for name, prefix, _obj in found:
                    try:
                        self._prop_op(op, name, every=True, prefix=prefix)
                    except PatchError as exc:
                        self._find("error", str(exc), op)
            else:
                name, prefix = self._target(op, op.target, "patches")
                self._prop_op(op, name, every=False, prefix=prefix)
        elif op.kind in ("create", "clone"):
            self._create(op)
        elif op.kind == "delobj":
            self._delete_object(op)
        elif op.kind in ("replacefile", "addfile"):
            self._file_op(op)
        else:
            raise PatchError(f"unknown operation {op.kind!r}")

    # --- objects ---
    def _missing(self, name: str, op: Op, verb: str) -> PatchError:
        if name in self.deleted:
            d = self.deleted[name]
            return PatchError(f"{op.at()} {verb} {name}, which {d.at()} deleted")
        return PatchError(f"{op.at()} {verb} {name}, which doesn't exist in this game build "
                          f"(after a game update, this needs a rebase)")

    def _create(self, op: Op) -> None:
        name = op.target
        if name in self.game.objects:
            by = self.created.get(name)
            who = by.at() if by else "the game"
            raise PatchError(f"{op.at()} creates {name}, but {who} already has an object with that name")
        placed = op
        if op.kind == "clone":
            src, prefix = self._target(op, op.source, "clones")
            if src not in self.game.objects:
                raise self._missing(src, op, "clones")
            source = self.game.objects[src]
            if prefix:  # a part of another object (or what a part refers to): copied like a named source would be
                val = self._part_at(op, src, prefix)[2]
                if isinstance(val, Ref) and val.target in self.game.objects:
                    src, source = val.target, self.game.objects[val.target]
                elif isinstance(val, Inline):
                    source = val.obj
                else:
                    raise PatchError(f"{op.at()} clones {op.source}, which isn't an object")
            obj = _fresh(source)  # owned sub-objects copied, references kept
            placed = copy.copy(op)
            placed.source = src  # the new object goes into its source's file (model.save)
        else:
            obj = Obj(op.cls or "?")
        self.game.objects[name] = obj
        self.created[name] = placed
        self._gen += 1
        for sub in op.body:
            body_op = copy.copy(sub)
            body_op.target, body_op.mod = name, body_op.mod or op.mod
            body_op.file, body_op.line = body_op.file or op.file, body_op.line or op.line
            try:
                self._prop_op(body_op, name, every=False, own_object=True)
            except PatchError as exc:
                self._find("error", str(exc), body_op)
        if op.kind == "clone":
            self._fresh_identity(placed, name)

    def _fresh_identity(self, op: Op, name: str) -> None:
        """A clone gets its own id, debug name and build-menu slot (MOD_FORMAT §10.5, rusemod.identity), except for
        any it sets itself. Reported as a note, and in the history of each value."""
        from .identity import refresh
        own = {m.group(0) for b in op.body if (m := re.match(r"[A-Za-z_][A-Za-z0-9_]*", b.path or ""))}
        changed = refresh(self.game, name, op.source, skip=own, new=self.created)
        if not changed:
            return
        fresh = copy.copy(op)
        fresh.kind = "fresh identity"
        for prop, _old, new in changed:
            self.trail[(name, prop)].append((fresh, copy.deepcopy(new)))
        parts = ", ".join(f"{prop} {show(old)} -> {show(new)}" for prop, old, new in changed)
        self._find("note", f"{op.at()}: {name} gets its own {parts} (set any of these in the clone to choose)", op)

    def _delete_object(self, op: Op) -> None:
        name, prefix = self._target(op, op.target, "deletes")
        if prefix:
            raise PatchError(f"{op.at()} deletes {op.target}, a part of {name}; parts can't be deleted, patch {name} "
                             f"instead")
        if name not in self.game.objects:
            if name in self.deleted:
                self._find("note", f"{op.at()} deletes {name}, already deleted by {self.deleted[name].at()}", op)
                return
            raise self._missing(name, op, "deletes")
        others = [o for o in self.obj_log[name] if o.mod != op.mod]
        if others:
            self._find("warning", f"{op.at()} deletes {name}; the changes {others[-1].at()} made to it are thrown away", op)
        del self.game.objects[name]
        self.deleted[name] = op
        self._gen += 1

    def _file_op(self, op: Op) -> None:
        path = op.target.lower().replace("\\", "/")
        if op.kind == "addfile":
            if path in self.game.files:
                raise PatchError(f"{op.at()} adds {op.target}, which already exists")
        elif path not in self.game.files:
            # not a game rule: how a mod names what it patches
            raise PatchError(f"{op.at()} replaces {op.target}, which isn't a game file")
        prev = self.file_log.get(path)
        if prev and prev.mod != op.mod:
            self._find("warning", f"{op.at()} replaces {op.target}, which {prev.at()} already replaced", op)
        self.game.files[path] = op.value
        self.file_log[path] = op

    # --- properties ---
    def _prop_op(self, op: Op, name: str, every: bool, own_object: bool = False, prefix: str = "") -> None:
        """`prefix`: the path from `name` to the part the operation is for (a found part, MOD_FORMAT §4)."""
        if name not in self.game.objects:
            raise self._missing(name, op, "patches")
        if prefix or _needs_finding(op.value) or _needs_finding(op.anchor):
            op = copy.copy(op)
            if prefix:
                op.path = f"{prefix}.{op.path}"
            op.value, op.anchor = self._found(op, op.value), self._found(op, op.anchor)
        owner, obj, prop, idx, path = self._locate(op, name)
        key = (owner, path)
        if not own_object:
            self.obj_log[owner].append(op)
        old = obj.props.get(prop)
        target_val = old
        if idx is not None:
            if not isinstance(old, ListV):
                raise PatchError(f"{op.at()}: {owner}:{path} isn't a list")
            target_val = old.items[idx]
        category = {"set": "set", "mul": "math", "add": "math", "delprop": "delprop"}.get(op.kind, op.kind)
        self._check_conflict(op, key, category, target_val)

        if op.kind == "delprop":
            obj.props.pop(prop, None)
            new = None
        elif op.kind == "set":
            self._no_deleted_refs(op, op.value)
            new = _convert(op.value, target_val)
            if target_val is None and idx is None:  # a property the object doesn't have yet: the type its class has
                new = self._typed(obj.cls, prop, new)
        elif op.kind in ("mul", "add"):
            if target_val is None:
                if every:
                    self._find("note", f"{op.at()}: {owner} has no {path}; skipped", op)
                    return
                prev = self._last_other(op, key)
                why = f" ({prev[0].at()} deleted it)" if prev and prev[1] == "delprop" else ""
                raise PatchError(f"{op.at()}: can't {op.kind} {owner}:{path}, it isn't set{why}; set it first "
                                 f"(the engine's default isn't stored in the data)")
            new = _math(op, target_val, owner, path)
        else:
            new = self._list_op(op, target_val, owner, path, key)

        if op.kind != "delprop":
            if idx is not None:
                old.items[idx] = new
            else:
                obj.props[prop] = new
        if any(isinstance(x, Inline) for v in (target_val, new) for x in _walk_value(v)):
            self._gen += 1  # a part came or went: the object index is rebuilt before the next find
        self.touch[key].append((op, category, op.value))
        self.trail[key].append((op, copy.deepcopy(new)))
        self._done.append((owner, path, op))

    def _kind_in_class(self, cls: str, prop: str) -> tuple[str, bool] | None:
        """(number type, a list of them or not) the game's objects of class `cls` give `prop`, the most common;
        None when none of them has it as numbers. Read once, from the game as loaded, the first time it's needed."""
        if self._kinds is None:
            seen: dict = defaultdict(Counter)
            for top in self.game.objects.values():
                for _path, part in _parts(top):
                    for name, v in part.props.items():
                        if isinstance(v, Num):
                            seen[(part.cls, name)][(v.kind, False)] += 1
                        elif isinstance(v, ListV) and v.items and all(isinstance(x, Num) for x in v.items):
                            seen[(part.cls, name)][(v.items[0].kind, True)] += 1
            self._kinds = {key: c.most_common(1)[0][0] for key, c in seen.items()}
        return self._kinds.get((cls, prop))

    def _typed(self, cls: str, prop: str, new):
        """A number (or list of numbers) given to a property its object doesn't have yet, in the type the class has it
        elsewhere ("type follows the schema"): `IsUpgrade = 1` on a unit that isn't an upgrade yet is a yes/no, as on
        the game's upgrades, not a whole number. Anything else, or a property no object of the class has, as written."""
        found = self._kind_in_class(cls, prop)
        if found is None:
            return new
        kind, is_list = found
        if isinstance(new, Num) and not is_list:
            return Num(kind, new.value)
        if isinstance(new, ListV) and is_list and all(isinstance(x, Num) for x in new.items):
            return ListV([Num(kind, x.value) for x in new.items])
        return new

    def _locate(self, op: Op, name: str):
        """Walk the property path. Returns (owner name, Obj holding the property, property, list index or None, path
        from owner). Crossing into an object that others use too needs `own` or `shared` (MOD_FORMAT §10.5)."""
        segs = _parse_path(op.path)
        owner, obj, walked = name, self._own(name), []  # (every object the walk enters is one the operation changes)
        for i, (prop, sels) in enumerate(segs):
            last = i == len(segs) - 1
            if last and len(sels) <= 1 and (not sels or re.fullmatch(r"-?\d+", sels[0])):
                idx = int(sels[0]) if sels else None
                if idx is not None:
                    val = obj.props.get(prop)
                    if not isinstance(val, ListV) or not -len(val.items) <= idx < len(val.items):
                        raise PatchError(f"{op.at()}: {owner}:{'.'.join(walked + [prop])} has no item {idx}")
                    idx %= len(val.items)
                path = ".".join(walked + [prop + (f"[{idx}]" if idx is not None else "")])
                return owner, obj, prop, idx, path
            holder, key = obj.props, prop
            val = obj.props.get(prop)
            if val is None:
                raise PatchError(f"{op.at()}: {owner} has no {'.'.join(walked + [prop])}")
            for sel in sels:
                holder, key, val = self._item(op, val, sel, owner, ".".join(walked + [prop]))
            step = prop + "".join(f"[{s}]" for s in sels)
            if isinstance(val, Inline):
                obj, walked = val.obj, walked + [step]
            elif isinstance(val, Ref) and val.target in self.game.objects:
                users = self._referrers(val.target)
                if users > 1 and op.share not in ("own", "shared"):
                    raise PatchError(
                        f"{op.at()}: {owner}:{'.'.join(walked + [step])} is {val.target}, which {users} places use; "
                        f"say `own` (this one only gets its own copy) or `shared` (change it for all of them)")
                if users > 1 and op.share == "own":
                    copy_ = Inline(_fresh(self.game.objects[val.target]))
                    holder[key] = copy_
                    obj, walked = copy_.obj, walked + [step]
                    self._gen += 1
                else:
                    owner, obj, walked = val.target, self._own(val.target), []
            else:
                raise PatchError(f"{op.at()}: {owner}:{'.'.join(walked + [step])} isn't an object")
        raise PatchError(f"{op.at()}: empty property path")

    def _item(self, op: Op, val, sel: str, owner: str, prop: str):
        """(holder, key, value) of one item of a list (by number or filter), or of one entry of a map (by number; the
        path goes on with `.k` or `.v`)."""
        if isinstance(val, MapV):
            if not re.fullmatch(r"-?\d+", sel) or not -len(val.pairs) <= int(sel) < len(val.pairs):
                raise PatchError(f"{op.at()}: {owner}:{prop} has no entry [{sel}]")
            return None, None, Inline(Obj(ENTRY, _EntryProps(val, int(sel) % len(val.pairs))))
        if not isinstance(val, ListV):
            raise PatchError(f"{op.at()}: {owner}:{prop} isn't a list")
        k = self._select(op, val, sel, owner, prop)
        return val.items, k, val.items[k]

    def _select(self, op: Op, lst: ListV, sel: str, owner: str, prop: str) -> int:
        if re.fullmatch(r"-?\d+", sel):
            k = int(sel)
            if not -len(lst.items) <= k < len(lst.items):
                raise PatchError(f"{op.at()}: {owner}:{prop} has no item {k}")
            return k % len(lst.items)
        field_, _, want = sel.partition("=")
        hits = []
        for k, item in enumerate(lst.items):
            o = item.obj if isinstance(item, Inline) else self.game.objects.get(item.target) \
                if isinstance(item, Ref) else None
            if o is not None and _matches(o, field_.strip(), want.strip()):
                hits.append(k)
        if len(hits) != 1:
            # not a game rule: how a mod names what it patches
            raise PatchError(f"{op.at()}: [{sel}] matches {len(hits)} items of {owner}:{prop}, it must match exactly one")
        return hits[0]

    # --- finding objects (MOD_FORMAT §4) ---
    def _objects_of(self, cls: str | None, filter_: str | None) -> list:
        """[(top-level name, path to the part or "", Obj)] of every object of class `cls` (any class when None)
        whose property matches `filter_` ("Prop=value"), unnamed parts included; in name, then path order."""
        if self._index_gen != self._gen:
            by_class, all_ = defaultdict(list), []
            for name in sorted(self.game.objects):
                for path, o in _parts(self.game.objects[name]):
                    by_class[o.cls].append((name, path, o))
                    all_.append((name, path, o))
            self._by_class, self._all, self._index_gen = by_class, all_, self._gen
        found = self._by_class.get(cls, []) if cls else self._all
        # several conditions, all to match: [RegistrationName="TypeWarrior/X", file="propsset.cpp"]; `file` is part
        # of the game file the object is in (two files may define a scenery type of one name: the summer and winter
        # prop sets)
        for cond in _conditions(filter_ or ""):
            field_, eq, want = cond.partition("=")
            if not eq or not field_.strip():
                raise PatchError(f"a filter is written [Property=value], not [{filter_}]")
            field_, want = field_.strip(), want.strip()
            if field_ == "file":
                found = [t for t in found if _unquote(want).lower() in self._file_of(t[0], t[2]).lower()]
            else:
                found = [t for t in found if _matches(t[2], field_, want)]
        return found

    def _file_of(self, name: str, obj: Obj) -> str:
        """The game file a top-level object is in: from its origin, else its `<file>#<index>` name."""
        top = self.game.objects.get(name)
        origin = (top.origin or top.copied_from) if top is not None else None
        return origin[0] if origin else name.partition("#")[0]

    def _target(self, op: Op, text: str, verb: str) -> tuple[str, str]:
        """An object as written (`$/Name`, or `@Class[Prop=value]` with an optional `:path`) -> (top-level object
        name, path to the part or ""). A designator must match exactly one object."""
        if not text or not text.startswith("@"):
            name, _, sub = text.partition(":") if text else ("", "", "")
            return name, sub
        cls, filter_, sub = _split_designator(text)
        found = self._objects_of(cls, filter_)
        what = _what(cls, filter_)
        if not found:
            # not a game rule: the game or one of its files isn't found
            raise PatchError(f"{op.at()} {verb} {what}, which doesn't exist in this game build (after a game update, "
                             f"this needs a rebase)")
        if len(found) > 1:
            names = ", ".join(f"{n}:{p}" if p else n for n, p, _ in found[:4])
            # not a game rule: how a mod names what it patches
            raise PatchError(f"{op.at()}: {what} matches {len(found)} objects ({names}{', …' if len(found) > 4 else ''}); "
                             f"it must match exactly one")
        name, prefix, _ = found[0]
        if sub:
            prefix = f"{prefix}.{sub}" if prefix else sub
        return name, prefix

    def _part_at(self, op: Op, name: str, path: str, own: bool = False):
        """A read-only walk from the top-level object `name` along `path`: (holder, key, the value at the end).
        Crosses references to named objects on the way; the end may be a part, a reference or a plain value.
        `own`: for a change at the end, through the engine's own copies of the objects on the way (_own)."""
        get = self._own if own else self.game.objects.__getitem__
        obj, holder, key, val = get(name), None, None, None
        segs = _parse_path(path)
        for i, (prop, sels) in enumerate(segs):
            val = obj.props.get(prop)
            if val is None:
                raise PatchError(f"{op.at()}: {name} has no {path}")
            holder, key = obj.props, prop
            for sel in sels:
                holder, key, val = self._item(op, val, sel, name, prop)
            if i == len(segs) - 1:
                break
            if isinstance(val, Inline):
                obj = val.obj
            elif isinstance(val, Ref) and val.target in self.game.objects:
                name, obj = val.target, get(val.target)
            else:
                raise PatchError(f"{op.at()}: {name}:{path}: {prop} isn't an object")
        return holder, key, val

    def _ref_to(self, op: Op, text: str) -> str | None:
        """The object a reference written as `$/Name:path`, `@Class[Prop=value]` or `@...:path` points at, as a
        top-level name. A part only its owner used so far becomes a shared object named `<file>#<index>`."""
        if text.startswith("@"):
            name, prefix = self._target(op, text, "refers to")
        else:
            name, _, prefix = text.partition(":")
        if name not in self.game.objects:
            raise self._missing(name, op, "refers to")
        if not prefix:
            return name
        holder, key, val = self._part_at(op, name, prefix)
        if isinstance(val, Ref):
            return val.target
        if isinstance(val, Inline):
            holder, key, val = self._part_at(op, name, prefix, own=True)  # the same part, in the object _share changes
            return self._share(op, val.obj, holder, key)
        raise PatchError(f"{op.at()}: {text} isn't an object")

    def _share(self, op: Op, part: Obj, holder, key) -> str:
        """Give a part its own name so something else can refer to it too (it stays where it is in its file)."""
        if part.origin is None:
            # not a game rule: how a mod names what it patches
            raise PatchError(f"{op.at()}: can't refer to a {part.cls} part that a mod made; refer to a part of a game "
                             f"object, or make it a named object of its own")
        name = f"{part.origin[0]}#{part.origin[1]}"
        holder[key] = Ref(name)
        self.game.objects[name] = part
        self._gen += 1
        return name

    def _found(self, op: Op, v):
        """`v` with every reference that still has to be found (`@...`, `$/X:path`) replaced by a plain one."""
        if isinstance(v, Ref) and v.target and (v.target.startswith("@") or ":" in v.target):
            return Ref(self._ref_to(op, v.target))
        if isinstance(v, list):
            return [self._found(op, x) for x in v]
        if isinstance(v, ListV):
            return ListV([self._found(op, x) for x in v.items])
        if isinstance(v, MapV):
            return MapV([(self._found(op, k), self._found(op, x)) for k, x in v.pairs])
        if isinstance(v, PairV):
            return PairV(self._found(op, v.a), self._found(op, v.b))
        return v

    def _referrers(self, target: str) -> int:
        n = 0
        for o in self.game.objects.values():
            for v in _walk_obj(o):
                if isinstance(v, Ref) and v.target == target:
                    n += 1
        return n

    def _last_other(self, op: Op, key):
        for entry in reversed(self.touch.get(key, [])):
            if entry[0].mod != op.mod:
                return entry
        return None

    def _check_conflict(self, op: Op, key, category: str, current) -> None:
        prev = self._last_other(op, key)
        if prev is None:
            return
        a_op, a, a_items = prev
        b, where = category, f"{key[0]}:{key[1]}"
        if a == "set" and b == "set":
            if _convert(op.value, current) != current:
                self._find("warning", f"{op.at()} sets {where}, replacing the value {a_op.at()} set", op)
        elif a == "set" and b == "math":
            self._find("note", f"{op.at()} does math on the value {a_op.at()} set for {where}", op)
        elif a == "math" and b == "set":
            self._find("warning", f"{op.at()} sets {where}; the change {a_op.at()} made is lost", op)
        elif a == "math" and b == "math":
            self._find("note", f"{where}: {a_op.at()} and {op.at()} both change it; applied in load order", op)
        elif a == "delprop" and b == "set":
            self._find("warning", f"{op.at()} sets {where} again after {a_op.at()} deleted it", op)
        elif b == "delprop" and a in ("set", "math", "append", "remove", "insert"):
            self._find("warning", f"{op.at()} deletes {where}; the change {a_op.at()} made is lost", op)
        elif a in ("append", "remove", "insert") and b == "set":
            self._find("warning", f"{op.at()} replaces the list {where}; the list edits {a_op.at()} made are lost", op)
        elif a == "set" and b in ("append", "remove", "insert"):
            self._find("note", f"{op.at()} edits the list {a_op.at()} set for {where}", op)
        elif a == "append" and b == "remove" and _overlap(op.value, a_items):
            self._find("warning", f"{op.at()} removes from {where} items {a_op.at()} added", op)
        elif a == "remove" and b == "append" and _overlap(op.value, a_items):
            self._find("warning", f"{op.at()} adds back to {where} items {a_op.at()} removed", op)

    def _list_op(self, op: Op, current, owner: str, path: str, key):
        where = f"{owner}:{path}"
        if not isinstance(current, ListV):
            raise PatchError(f"{op.at()}: {where} isn't a list" + (" (it isn't set)" if current is None else ""))
        items = list(current.items)
        if op.kind == "append":
            self._no_deleted_refs(op, ListV(op.value))
            for v in op.value:
                v = _fit(v, items)
                if v in items:
                    self._find("note", f"{op.at()}: {show(v)} is already in {where}; not added twice", op)
                else:
                    items.append(v)
        elif op.kind == "remove":
            gone = [_fit(v, items) for v in op.value]
            kept = [v for v in items if v not in gone]
            if len(kept) == len(items):
                prev = self._last_other(op, key)
                if prev and prev[1] == "remove" and _overlap(op.value, prev[2]):
                    self._find("note", f"{op.at()}: nothing to remove from {where}; {prev[0].at()} removed it already", op)
                else:
                    self._find("warning", f"{op.at()}: nothing matched in {where}; nothing removed", op)
            items = kept
        elif op.kind == "insert":
            self._no_deleted_refs(op, ListV([op.value]))
            if op.where == "at":
                pos = int(op.anchor)
                if not 0 <= pos <= len(items):
                    raise PatchError(f"{op.at()}: {where} has no position {pos}")
            else:
                anchor = _fit(op.anchor, items)
                if anchor not in items:
                    prev = self._last_other(op, key)
                    why = f" ({prev[0].at()} removed it)" if prev and prev[1] == "remove" and \
                        _overlap([op.anchor], prev[2]) else ""
                    raise PatchError(f"{op.at()}: can't insert next to {show(op.anchor)} in {where}, it isn't there{why}")
                pos = items.index(anchor) + (1 if op.where == "after" else 0)
            items.insert(pos, _fit(op.value, items))
        return ListV(items)

    def _no_deleted_refs(self, op: Op, value) -> None:
        for v in _walk_value(value):
            if isinstance(v, Ref) and v.target in self.deleted and v.target not in self.game.objects:
                raise PatchError(f"{op.at()} refers to {v.target}, which {self.deleted[v.target].at()} deleted")

    # --- the end: round numbers once, check references, the truck flags and what the game needs of units ---
    def _finish(self) -> None:
        for name, obj in list(self.game.objects.items()):
            found = self._finish_obj(name, obj, write=not self.game.shares(name))
            if found is None:  # a number of an object still in common with the caller's game changes: copied first
                found = self._finish_obj(name, self._own(name), write=True)
            for message in found:
                self._find("error", message)
        new = [n for n in self.created if n in self.game.objects]
        if new:
            from .identity import clashes
            for name, message in clashes(self.game, new):
                self._find("warning", message, self.created[name])
        self._truck_flags(new)
        self._unit_rules(new)
        self._ruses_per_sector()

    def _ruses_per_sector(self) -> None:
        """More than two ruses on one sector crashes the game (rusemod.economy): an error for every copy of the game's
        constants holding more, naming the last operation that set it; a .rmod mod's change (made before these
        operations ran) has none, so the message says where else it came from."""
        from .economy import CLASS, RUSES_PER_SECTOR as PROP, RUSES_PER_SECTOR_MOST as MOST
        for name, obj in self.game.objects.items():
            v = obj.props.get(PROP) if obj.cls == CLASS else None
            if not isinstance(v, Num) or v.value <= MOST:
                continue
            op = self._blame(lambda o, p, n=name: o == n and _root(p) == PROP)
            why = f"{PROP} = {v.value}: more than {MOST} ruse cards on one sector crashes the game (a sector has room " \
                  f"for {MOST}); leave it at {MOST} or lower"
            # rule: ruses-per-sector
            self._find("error", f"{op.at()}: {why}" if op else f"{name}: {why} (a .rmod mod in the set sets it)", op)

    def _finish_obj(self, name: str, obj: Obj, write: bool) -> list[str] | None:
        """Round the numbers of the top-level object `name` once (in place) and check its references: the errors, in
        order. Not `write`: None as soon as rounding would change a number, even only in how it's written (5.0 to 5),
        or would make a new NaN, which compares unequal and so counts as changed (model.save)."""
        found = []
        for v in _walk_obj(obj):
            if isinstance(v, Num):
                try:
                    r = _round(v)
                except PatchError as exc:
                    found.append(f"{name}: {exc}")
                    continue
                if write:
                    v.value = r
                elif not (r == v.value and r.compare_total(v.value) == 0):
                    return None
            elif isinstance(v, Ref) and v.target is not None and v.target not in self.game.objects:
                why = f", which {self.deleted[v.target].at()} deleted" if v.target in self.deleted else ""
                found.append(f"{name} still refers to {v.target}{why}")
        return found

    def _blame(self, hit) -> Op | None:
        """The last property operation for which `hit(owner, path)` holds."""
        for owner, path, op in reversed(self._done):
            if hit(owner, path):
                return op
        return None

    def _unit_rules(self, new: list) -> None:
        """What the game needs of a unit and its weapons (rusemod.unitcheck), on every unit a mod made or changed and
        every weapon: an error or warning for each thing the mods made wrong, naming the last operation on the property
        concerned, else the one that made the unit, else the last one on it. What the game's data already had isn't the
        mods' doing, nor what a copy has from the unit it copies."""
        from . import unitcheck as uc
        touched = set(new) | {owner for owner, _path, _op in self._done if owner in self.game.objects}
        units = sorted(n for n in touched if uc.is_unit(self.game.objects[n]))
        found = []  # (unit, property, level, why)
        for name in units:
            obj = self.game.objects[name]
            made = self.created.get(name)
            # a copy is compared with what it copies, as the game had it: what it inherits isn't the mod's doing
            had = self._had_unit.get(made.source if made else name, set()) if not made or made.kind == "clone" \
                else set()
            found += [(name, prop, level, why) for level, prop, why in uc.problems(obj) if why not in had]
            if uc.ID not in obj.props and (made.kind == "create" if made else self._had_ids.get(name) is not None):
                # rule: unit-id-zero
                found.append((name, uc.ID, "error", f"it has no {uc.ID}, so the game skips it in its unit lists, and "
                                                    f"ordering it causes an error in the match; give it a number no "
                                                    f"other unit has"))
        now = uc.ids(self.game)
        moved = [n for n in units if n in self.created or now.get(n) != self._had_ids.get(n)]
        # rule: unit-id-clash
        found += [(name, uc.ID, "error", why) for name, why in uc.id_clashes(self.game, moved).items()]
        # every unit, not only those the mods touched: moving a parent to another army breaks the units researched
        # from it; what the game's own data had (or a copy has from what it copies) isn't the mods' doing
        everyone = [n for n, o in self.game.objects.items() if uc.is_unit(o)]
        for name, why in uc.research_parent_problems(self.game, everyone).items():
            made = self.created.get(name)
            if (made.source if made and made.kind == "clone" else name, why) not in self._had_research:
                # rule: unit-research-parent
                found.append((name, uc.UPGRADE, "error", why))
        for name, prop, level, why in found:
            op = self._blame(lambda o, p, n=name, r=prop: o == n and _root(p) == r) or self.created.get(name) \
                or self._blame(lambda o, p, n=name: o == n)
            self._find(level, f"{op.at()}: {name}: {why}" if op else f"{name}: {why}", op)
        for top, path, named, why in uc.salvo_problems(self.game):
            made = self.created.get(top)
            if (made.source if made else top, path, why) in self._had_salvos:  # the game's own, or a copy of it
                continue
            root = _root(path) if path else None
            op = self._blame(lambda o, p, t=top, r=root, s=named: (o == t and r in (None, _root(p))) or o in s) \
                or self.created.get(top)
            where = f"{top}:{path}" if path else top
            # rule: weapon-salvo
            self._find("error", f"{op.at()}: {where}: {why}" if op else f"{where}: {why}", op)

    def _truck_flags(self, new: list) -> None:
        """Flags 62 and 63 on a unit that isn't a truck crash the game (rusemod.unitflags): an error for each, on every
        unit a mod made or whose flags a mod changed, unless the unit carried that flag before the mods. It names the
        last operation that put the flag there, whether it changed the whole list or one item of it, else the last one
        that changed the unit's flags, else the one that made the unit."""
        from .unitflags import PROP, TRUCK_ONLY, crashes, numbers
        blame = {name: self.created[name] for name in new}
        steps = defaultdict(list)  # unit -> [(puts a truck flag in, when it ran, step, op)], every path to its flags
        for (owner, path), done in self.trail.items():
            if path.split("[", 1)[0] != PROP or owner not in self.game.objects:
                continue
            # the order the unit's operations ran in; a new unit's own ones (its body) ran first, when it was made
            when = {id(op): i for i, op in enumerate(self.obj_log.get(owner, []))}
            for k, (op, value) in enumerate(done):
                given = op.value if op.kind in ("set", "append", "insert") else value if op.kind in ("mul", "add") \
                    else None  # `add` turns an item into another number: what it made
                steps[owner].append((bool(numbers(given) & set(TRUCK_ONLY)), when.get(id(op), -1), k, op))
        for owner, found in steps.items():
            blame[owner] = max(found, key=lambda s: s[:3])[3]
        for name in sorted(blame):
            had = set() if name in self.created else self._had_truck_flags.get(name, set())
            for why in crashes(self.game.objects[name], had):
                # rule: truck-flags
                self._find("error", f"{blame[name].at()}: {name}: {why}", blame[name])


def _root(path: str) -> str:
    """The property a path starts at: `Weapons[0].Ammunition` -> `Weapons`."""
    return path.split(".", 1)[0].split("[", 1)[0]


def _round(v: Num) -> Decimal:
    if v.kind in INT_RANGES:
        r = v.value.quantize(Decimal(1), rounding=ROUND_HALF_UP)  # half away from zero: 52.5 -> 53, -2.5 -> -3
        lo, hi = INT_RANGES[v.kind]
        if not lo <= r <= hi:
            raise PatchError(f"{r} doesn't fit in {v.kind}")
        return r
    if v.kind == "float32":
        return Decimal(struct.unpack("<f", struct.pack("<f", float(v.value)))[0])
    return Decimal(float(v.value))


def _convert(new, old):
    """A literal takes the type of the property it replaces ("type follows the schema")."""
    if isinstance(new, Num) and isinstance(old, Num):
        return Num(old.kind, new.value)
    if isinstance(new, ListV) and isinstance(old, ListV) and old.items and all(isinstance(x, Num) for x in old.items):
        kind = old.items[0].kind
        return ListV([Num(kind, x.value) if isinstance(x, Num) else x for x in new.items])
    return copy.deepcopy(new)


def _math(op: Op, current, owner: str, path: str):
    k = Decimal(str(op.value))

    def one(n):
        if not isinstance(n, Num):
            raise PatchError(f"{op.at()}: {owner}:{path} isn't a number")
        return Num(n.kind, n.value * k if op.kind == "mul" else n.value + k)

    if isinstance(current, ListV):
        return ListV([one(x) for x in current.items])
    return one(current)


def _overlap(a, b) -> bool:
    a = a if isinstance(a, list) else [a]
    b = b if isinstance(b, list) else [b]
    return any(x in b for x in a)


def _walk_value(v):
    yield v
    if isinstance(v, ListV):
        for x in v.items:
            yield from _walk_value(x)
    elif isinstance(v, MapV):
        for k, x in v.pairs:
            yield from _walk_value(k)
            yield from _walk_value(x)
    elif isinstance(v, PairV):
        yield from _walk_value(v.a)
        yield from _walk_value(v.b)
    elif isinstance(v, Inline):
        yield from _walk_obj(v.obj)


def _fresh(obj: Obj) -> Obj:
    """A deep copy that counts as new: it and its owned parts forget which game file they came from."""
    new = copy.deepcopy(obj)
    new.copied_from, new.origin = new.origin, None
    for v in _walk_obj(new):
        if isinstance(v, Inline):
            v.obj.copied_from, v.obj.origin = v.obj.origin, None
    return new


def _walk_obj(obj: Obj):
    for v in obj.props.values():
        yield from _walk_value(v)


def _parts(obj: Obj, prefix: str = ""):
    """(path, Obj) for `obj` itself ("" ) and every unnamed part inside it, through lists ("Weapons[0].Ammunition")."""
    yield prefix, obj
    for prop, v in obj.props.items():
        yield from _parts_in(v, f"{prefix}.{prop}" if prefix else prop)


def _parts_in(v, path: str):
    if isinstance(v, Inline):
        yield from _parts(v.obj, path)
    elif isinstance(v, ListV):
        for i, x in enumerate(v.items):
            yield from _parts_in(x, f"{path}[{i}]")


def part_at(obj: Obj, path: str) -> Obj:
    """The part of `obj` at a path as _parts gives it: `obj` itself for "", else through parts and list items
    ("SubClusterList[1].Loader")."""
    for prop, sels in _parse_path(path) if path else []:
        v = obj.props[prop]
        for sel in sels:
            v = v.items[int(sel)]
        obj = v.obj
    return obj


def _matches(obj: Obj, field_: str, want: str) -> bool:
    """Whether `obj` fits the filter `field_=want` ([class=TAmmunition], [AmmunitionId=1120], [Name='x'], [Ref=$/…])."""
    if field_ == "class":
        return obj.cls == want
    v = obj.props.get(field_)
    if isinstance(v, Text):
        return v.value == _unquote(want)
    if isinstance(v, Num):
        w = want.lower()
        if w in ("true", "false"):
            return (v.value != 0) == (w == "true")
        try:
            return v.value == (Decimal(int(w, 16)) if w.startswith(("0x", "-0x")) else Decimal(w))
        except (InvalidOperation, ValueError):
            return False
    if isinstance(v, Ref):
        return v.target == want or (v.target is None and want == "nil")
    return False


def _conditions(filter_: str) -> list[str]:
    """A filter's conditions, split at the commas outside quotes."""
    out, cur, quote = [], "", None
    for ch in filter_:
        if quote:
            quote = None if ch == quote else quote
        elif ch in "'\"":
            quote = ch
        elif ch == ",":
            out.append(cur)
            cur = ""
            continue
        cur += ch
    if cur.strip():
        out.append(cur)
    return [c for c in out if c.strip()]


def _unquote(s: str) -> str:
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"" else s


def _split_designator(text: str) -> tuple[str | None, str, str]:
    """`@TAmmunition[AmmunitionId=1120]:Icon` -> ("TAmmunition", "AmmunitionId=1120", "Icon"); no class -> None."""
    head, _, rest = text[1:].partition("[")
    filter_, _, sub = rest.partition("]")
    return head or None, filter_, sub[1:] if sub.startswith(":") else sub


def _what(cls: str | None, filter_: str | None) -> str:
    return f"{cls or 'object'}" + (f" with [{filter_}]" if filter_ else "")


def _needs_finding(v) -> bool:
    values = v if isinstance(v, list) else [v]
    return any(isinstance(x, Ref) and x.target and (x.target.startswith("@") or ":" in x.target)
               for value in values for x in _walk_value(value))


def _fit(v, items: list):
    """A number added to a list of numbers takes the list's own type (uint32 flags stay uint32)."""
    if isinstance(v, Num) and items and all(isinstance(x, Num) for x in items):
        return Num(items[0].kind, v.value)
    return v
