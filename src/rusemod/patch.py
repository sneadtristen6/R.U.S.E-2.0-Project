"""The mod rules engine: applies mod operations to a game model, following docs/MOD_FORMAT.md §10 exactly.

It works on a plain model of the game (objects with properties), not on NDF bytes: an adapter turns NDF files into
this model and back (M2). That keeps every rule testable without game files.

Model: named top-level objects (`Game.objects`, keyed by export path or `#<n>` for shared unnamed ones), each an `Obj`
with a class and ordered properties. A property holds a `Num`, `Text`, `Ref` (to another object, or nil), `Inline`
(an unnamed object only its owner uses), `ListV`, `MapV` or `Raw` (anything the engine only copies).

Rules, in short: operations run in load order, then the `final` ones; every operation sees the game as the ones
before it left it; math is exact and rounds once at the end (half away from zero); each pair of operations by two
different mods on the same thing gives the error / warning / note of the §10.4 table.
"""
from __future__ import annotations

import copy
import re
import struct
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

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


@dataclass
class Game:
    objects: dict = field(default_factory=dict)   # name -> Obj
    files: dict = field(default_factory=dict)     # game path -> bytes
    notes: list = field(default_factory=list)     # things noticed while loading, for the build report


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
        self.game = copy.deepcopy(game)
        self.findings: list[Finding] = []
        self.touch = defaultdict(list)     # (object, path) -> [(op, category, items)]
        self.obj_log = defaultdict(list)   # object -> [op] (property operations, for patch-then-delete)
        self.deleted: dict[str, Op] = {}
        self.created: dict[str, Op] = {}
        self.file_log: dict[str, Op] = {}
        self.trail = defaultdict(list)

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
        return Result(self.game, self.findings, dict(self.trail))

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

    # --- dispatch ---
    def apply(self, op: Op) -> None:
        if op.kind in PROP_KINDS:
            if op.every:
                names = sorted(n for n, o in self.game.objects.items() if o.cls == op.every)
                for name in names:
                    try:
                        self._prop_op(op, name, every=True)
                    except PatchError as exc:
                        self._find("error", str(exc), op)
            else:
                self._prop_op(op, op.target, every=False)
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
        if op.kind == "clone":
            if op.source not in self.game.objects:
                raise self._missing(op.source, op, "clones")
            obj = _fresh(self.game.objects[op.source])  # owned sub-objects copied, references kept
        else:
            obj = Obj(op.cls or "?")
        self.game.objects[name] = obj
        self.created[name] = op
        for sub in op.body:
            body_op = copy.copy(sub)
            body_op.target, body_op.mod = name, body_op.mod or op.mod
            body_op.file, body_op.line = body_op.file or op.file, body_op.line or op.line
            try:
                self._prop_op(body_op, name, every=False, own_object=True)
            except PatchError as exc:
                self._find("error", str(exc), body_op)

    def _delete_object(self, op: Op) -> None:
        name = op.target
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

    def _file_op(self, op: Op) -> None:
        path = op.target.lower().replace("\\", "/")
        if op.kind == "addfile":
            if path in self.game.files:
                raise PatchError(f"{op.at()} adds {op.target}, which already exists")
        elif path not in self.game.files:
            raise PatchError(f"{op.at()} replaces {op.target}, which isn't a game file")
        prev = self.file_log.get(path)
        if prev and prev.mod != op.mod:
            self._find("warning", f"{op.at()} replaces {op.target}, which {prev.at()} already replaced", op)
        self.game.files[path] = op.value
        self.file_log[path] = op

    # --- properties ---
    def _prop_op(self, op: Op, name: str, every: bool, own_object: bool = False) -> None:
        if name not in self.game.objects:
            raise self._missing(name, op, "patches")
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
        self.touch[key].append((op, category, op.value))
        self.trail[key].append((op, copy.deepcopy(new)))

    def _locate(self, op: Op, name: str):
        """Walk the property path. Returns (owner name, Obj holding the property, property, list index or None, path
        from owner). Crossing into an object that others use too needs `own` or `shared` (MOD_FORMAT §10.5)."""
        segs = _parse_path(op.path)
        owner, obj, walked = name, self.game.objects[name], []
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
                if not isinstance(val, ListV):
                    raise PatchError(f"{op.at()}: {owner}:{'.'.join(walked + [prop])} isn't a list")
                k = self._select(op, val, sel, owner, prop)
                holder, key, val = val.items, k, val.items[k]
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
                else:
                    owner, obj, walked = val.target, self.game.objects[val.target], []
            else:
                raise PatchError(f"{op.at()}: {owner}:{'.'.join(walked + [step])} isn't an object")
        raise PatchError(f"{op.at()}: empty property path")

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
            if o is None:
                continue
            if field_ == "class" and o.cls == want:
                hits.append(k)
            elif field_ != "class" and show(o.props.get(field_)) in (want, repr(want.strip("'"))):
                hits.append(k)
        if len(hits) != 1:
            raise PatchError(f"{op.at()}: [{sel}] matches {len(hits)} items of {owner}:{prop}, it must match exactly one")
        return hits[0]

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
                if isinstance(v, Ref) and v in items:
                    self._find("note", f"{op.at()}: {show(v)} is already in {where}; not added twice", op)
                else:
                    items.append(v)
        elif op.kind == "remove":
            kept = [v for v in items if v not in op.value]
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
                if op.anchor not in items:
                    prev = self._last_other(op, key)
                    why = f" ({prev[0].at()} removed it)" if prev and prev[1] == "remove" and \
                        _overlap([op.anchor], prev[2]) else ""
                    raise PatchError(f"{op.at()}: can't insert next to {show(op.anchor)} in {where}, it isn't there{why}")
                pos = items.index(op.anchor) + (1 if op.where == "after" else 0)
            items.insert(pos, op.value)
        return ListV(items)

    def _no_deleted_refs(self, op: Op, value) -> None:
        for v in _walk_value(value):
            if isinstance(v, Ref) and v.target in self.deleted and v.target not in self.game.objects:
                raise PatchError(f"{op.at()} refers to {v.target}, which {self.deleted[v.target].at()} deleted")

    # --- the end: round numbers once, check references ---
    def _finish(self) -> None:
        for name, obj in self.game.objects.items():
            for v in _walk_obj(obj):
                if isinstance(v, Num):
                    try:
                        v.value = _round(v)
                    except PatchError as exc:
                        self._find("error", f"{name}: {exc}")
                elif isinstance(v, Ref) and v.target is not None and v.target not in self.game.objects:
                    why = f", which {self.deleted[v.target].at()} deleted" if v.target in self.deleted else ""
                    self._find("error", f"{name} still refers to {v.target}{why}")


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
    new.origin = None
    for v in _walk_obj(new):
        if isinstance(v, Inline):
            v.obj.origin = None
    return new


def _walk_obj(obj: Obj):
    for v in obj.props.values():
        yield from _walk_value(v)
