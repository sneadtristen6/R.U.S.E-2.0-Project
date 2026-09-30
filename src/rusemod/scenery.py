"""A map's scenery (docs/FORMATS.md §6): every tree, house, field, road piece and ground decal the game draws, in
`output\\save.boobspc` of its map pack. The layout follows the notes of DomesticNukes and his Claude (checked here on
every shipped map).

    [0:16]    MD5 of everything after it (the game refuses a file whose sum is wrong)
    [16:124]  "0.6\\0", then (offset, size or count) pairs, offsets from the file's start: the block table (count),
              the block data, the per-name flags (count), the name table, an optional table, a second name table,
              the layer boundaries (u32s), then the three grids' sizes (Low, Mid, Hi) and (offset, size) of each
    blocks    block table: one u32 per block (from the data's start), then the data size (an end marker)

A block is a list of items with a small search tree over them; an item is an object (a scenery type from the name
table, placed with a transform), a road piece, or another block placed with a transform (a child, always stored
after its parent). Objects are stored at height 0: the game puts them on the ground when it loads the map.
"""
from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass, field

VERSION = b"0.6\0"
_HEAD = struct.Struct("<4s26I")  # the version, then 26 u32 fields (bytes 16..124)
SCALE16 = 3 / 32767              # the compact transform's int16 scale (so it tops out at 3.0)
IDENTITY = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
T_COMPACT, T_IDENTITY, T_MOVE, T_FULL = 0, 1, 2, 3
_T_SIZE = {T_COMPACT: 24, T_IDENTITY: 0, T_MOVE: 12, T_FULL: 48}
ROAD_WORDS = 15


class SceneryError(ValueError):
    pass


@dataclass
class Item:
    at: int                # offset from the block's items start
    word: int
    kind: str              # "object", "child" or "road"
    data: bytes            # what follows the word: the transform (or a road piece's 15 words)

    @property
    def symbol(self) -> int:           # an object's index in the name table
        return (self.word >> 4) & 0xFFFFF

    @property
    def child_offset(self) -> int:     # a child's block, from the data's start
        return self.word & 0xFFFFFC

    @property
    def tform(self) -> int:
        return self.word & 3

    @property
    def tier(self) -> int:             # the LOD tier (0..3)
        return (self.word >> 26) & 3

    def matrix(self) -> tuple:
        """The item's transform as 12 floats, 3 rows of (a, b, c, t): x' = a x + b y + c z + t."""
        return decode_transform(self.tform, self.data)


def decode_transform(kind: int, data: bytes) -> tuple:
    if kind == T_IDENTITY:
        return IDENTITY
    if kind == T_MOVE:
        tx, ty, tz = struct.unpack_from("<3f", data)
        return (1.0, 0.0, 0.0, tx, 0.0, 1.0, 0.0, ty, 0.0, 0.0, 1.0, tz)
    if kind == T_FULL:
        return struct.unpack_from("<12f", data)
    s0, s1, s2, s3 = (v * SCALE16 for v in struct.unpack_from("<4h", data))
    tx, ty, tz, sz = struct.unpack_from("<4f", data, 8)
    return (s0, s1, 0.0, tx, s2, s3, 0.0, ty, 0.0, 0.0, sz, tz)


def compose(p: tuple, c: tuple) -> tuple:
    """p then c: the transform of c placed with p (both 3x4)."""
    out = []
    for r in range(3):
        a, b, d, t = p[4 * r:4 * r + 4]
        out += [a * c[0] + b * c[4] + d * c[8], a * c[1] + b * c[5] + d * c[9], a * c[2] + b * c[6] + d * c[10],
                a * c[3] + b * c[7] + d * c[11] + t]
    return tuple(out)


@dataclass
class Block:
    index: int
    offset: int            # from the data's start
    raw: bytes             # the whole block, as stored
    long: bool
    bbox: tuple            # x0, y0, x1, y1 in the block's own coordinates
    entries: list          # item offsets (from the items start), one per item, in tree order
    nodes: bytes           # the search tree: C 8-byte nodes
    items_start: int       # offset of the items within `raw`
    items: list = field(default_factory=list)

    @property
    def mask(self) -> int:
        """The LOD mask of the tree's root node (bits 20-24: 1/2 close, 4 and 0x10 middle, 8 far)."""
        return (struct.unpack_from("<I", self.nodes, 0)[0] >> 20) & 0x1F if self.nodes else 0


class Scenery:
    def __init__(self, data: bytes):
        data = bytes(data)
        if len(data) < 124:
            raise SceneryError("not a scenery file: too short")
        if hashlib.md5(data[16:]).digest() != data[:16]:
            raise SceneryError("the scenery file's MD5 is wrong (the game would refuse it)")
        version, *f = _HEAD.unpack_from(data, 16)
        if version != VERSION:
            raise SceneryError(f"unknown scenery version {version!r}")
        self.raw = data
        self.fields = f
        (tab_off, tab_n, data_off, data_len, flags_off, flags_n, names_off, names_len,
         opt_off, opt_len, names2_off, names2_len, layers_off, layers_len) = f[:14]
        self.grid_dims = f[14:20]
        self.grids = [(f[20 + 2 * i], f[21 + 2 * i]) for i in range(3)]
        table = struct.unpack_from(f"<{tab_n}I", data, tab_off)
        if table[-1] != data_len:
            raise SceneryError("the block table's end marker isn't the data size")
        self.data_off = data_off
        self.names = []  # one per flag byte, then an empty name that ends the table
        p = names_off
        while p < names_off + names_len:
            (n,) = struct.unpack_from("<I", data, p)
            self.names.append(data[p + 4:p + 4 + n].decode("latin-1"))
            p += 4 + n
        if p != names_off + names_len or len(self.names) < flags_n:
            raise SceneryError("the name table doesn't end where its size says")
        self.flags = data[flags_off:flags_off + flags_n]
        self.layers = struct.unpack_from(f"<{layers_len // 4}I", data, layers_off)
        self.blocks: list[Block] = []
        self._by_offset: dict[int, int] = {}
        for i, (start, end) in enumerate(zip(table, table[1:])):
            self._by_offset[start] = i
            self.blocks.append(self._block(i, start, data[data_off + start:data_off + end]))

    def _block(self, index: int, offset: int, raw: bytes) -> Block:
        w0, c = struct.unpack_from("<II", raw)
        long, n = bool(w0 >> 31), w0 & 0x7FFFFFFF
        tree = 0x20 if long else 0x1C
        entries = list(struct.unpack_from(f"<{n}I", raw, tree))
        nodes = raw[tree + 4 * n:tree + 4 * n + 8 * c]
        start = tree + 4 * n + 8 * c
        b = Block(index, offset, raw, long, struct.unpack_from("<4f", raw, 8), entries, nodes, start)
        seen = set()
        for at in entries:  # a block seen from far lists its far-view items first, then every item again
            if at in seen:
                continue
            seen.add(at)
            p = start + at
            (w,) = struct.unpack_from("<I", raw, p)
            if w >> 31:
                kind, size = "object", _T_SIZE[w & 3]
            elif w & 0x01000000:
                kind, size = "road", 4 * ROAD_WORDS
            else:
                kind, size = "child", _T_SIZE[w & 3]
            if p + 4 + size > len(raw):
                raise SceneryError(f"block {index}: an item runs past the block's end")
            b.items.append(Item(at, w, kind, raw[p + 4:p + 4 + size]))
        return b

    # --- reading ---
    def block_at(self, offset: int) -> Block:
        try:
            return self.blocks[self._by_offset[offset]]
        except KeyError:
            raise SceneryError(f"a child points at {offset}, which isn't a block's start") from None

    def roots(self) -> list[int]:
        """Blocks that no other block places (the map's top level)."""
        placed = {self._by_offset.get(it.child_offset) for b in self.blocks for it in b.items if it.kind == "child"}
        return [b.index for b in self.blocks if b.index not in placed]

    def counts(self) -> list[int]:
        """Objects each block puts on the map (its own and its children's, however deep), without walking them:
        children are stored after their parents, so one pass from the last block back does it."""
        out = [0] * len(self.blocks)
        for b in reversed(self.blocks):
            n = 0
            for it in b.items:
                if it.kind == "object":
                    n += 1
                elif it.kind == "child":
                    n += out[self._by_offset[it.child_offset]]
            out[b.index] = n
        return out

    def walk(self, block: int | None = None, matrix: tuple = IDENTITY):
        """(name index, 3x4 transform in map coordinates) for every object under `block` (default: every root)."""
        todo = [(r, IDENTITY) for r in reversed(self.roots())] if block is None else [(block, matrix)]
        while todo:
            i, m = todo.pop()
            for it in self.blocks[i].items:
                if it.kind == "object":
                    yield it.symbol, compose(m, it.matrix())
                elif it.kind == "child":
                    todo.append((self._by_offset[it.child_offset], compose(m, it.matrix())))

    def types(self) -> dict[int, int]:
        """How many objects of each name the map places (no walk: each block's objects times how often it's placed)."""
        weight = [0] * len(self.blocks)
        for r in self.roots():
            weight[r] += 1
        for b in self.blocks:  # parents before children: a block's weight is complete when it's reached
            for it in b.items:
                if it.kind == "child":
                    weight[self._by_offset[it.child_offset]] += weight[b.index]
        out: dict[int, int] = {}
        for b in self.blocks:
            if weight[b.index]:
                for it in b.items:
                    if it.kind == "object":
                        out[it.symbol] = out.get(it.symbol, 0) + weight[b.index]
        return out


# --- what a name is: the scenery descriptors in the unit-data pack (genglad\patchable\scenery\...) ---
SCENERY_DIR = "genglad\\patchable\\scenery\\"
GROUPS = ("building", "vegetation", "prop", "decal", "other")
_BUILDING = ("batiment", "building", "eglise", "ferme", "maison", "ponts", "landmark", "montcassin", "ville")
_OTHER = ("lb", "ld", "level design", "script", "camera", "test", "old", "aggregation")


@dataclass
class Descriptor:
    name: str          # the registration name, e.g. TypeWarrior/MairieNormande
    cls: str           # TSceneryDescriptorMultiState, ...Sticker, ...
    category: str      # the game editor's Classement, e.g. COC/Normandie/Batiments_Villes_Villages
    group: str         # building, vegetation, prop, decal or other (GROUPS)
    model: str | None  # the close-up model, e.g. ww2\res3d\decors\france\france_1\mairienormandelod0.ase2ndfbin
    source: str        # the NDF file it comes from


def group_of(category: str, cls: str) -> str:
    c = category.lower()
    top = c.split("/")[0]
    if cls.endswith("Sticker") or "sticker" in c:
        return "decal"
    if top.startswith("vegetation"):
        return "vegetation"
    if top in _OTHER or cls.endswith(("TagGD", "Void", "Terminal")) or "/fx" in c or "staticfx" in c:
        return "other"
    if any(part.startswith("props") for part in c.split("/")):
        return "prop"
    if any(k in c.replace("_", "") for k in _BUILDING):
        return "building"
    return "prop"


def descriptors(arc) -> dict[str, Descriptor]:
    """Every scenery type the game knows, by registration name, from the unit-data pack `arc` (an Edat)."""
    from .ndf import Ndf, local_ref, sub_values
    out: dict[str, Descriptor] = {}
    for e in arc.entries:
        if not e.path.lower().startswith(SCENERY_DIR):
            continue
        n = Ndf(bytes(arc.read(e)))
        names = [p for p, _ in n.props]
        objs = [{names[pi]: v for pi, v in o.props} for o in n.objects]

        def text(v):
            return n.strings[struct.unpack("<I", v.payload)[0]] if v is not None and v.tc in (0x07, 0x1C) else ""

        def model(i, depth=0):
            """The close-up model under object i: through a multi-state's normal look and a multi-mode's nearest
            level to a Model3DFromFile."""
            if i is None or depth > 8:
                return None
            d = objs[i]
            if "ModelASE" in d:
                return text(d["ModelASE"]).replace("DataDir:\\", "").lower() or None
            if "SDFalse" in d:
                return model(local_ref(d["SDFalse"]), depth + 1)
            if "ModeEntry" in d:
                entries = [local_ref(v) for v in sub_values(d["ModeEntry"])]
                entries = [x for x in entries if x is not None]
                entries.sort(key=lambda x: objs[x]["ModeMask"].scalar() if "ModeMask" in objs[x] else 99)
                for x in entries:
                    found = model(local_ref(objs[x].get("SceneryDescriptor")) if objs[x].get("SceneryDescriptor")
                                  else None, depth + 1)
                    if found:
                        return found
            if "SceneryDescriptor" in d:
                return model(local_ref(d["SceneryDescriptor"]), depth + 1)
            return None

        for i, d in enumerate(objs):
            name = text(d.get("RegistrationName"))
            if not name:
                path = n.exports.get(i) or ""
                name = path[2:] if path.startswith("$/TypeWarrior/") else ""
            if not name or name in out:
                continue
            cls = n.classes[n.objects[i].cls]
            category = text(d.get("Classement"))
            out[name] = Descriptor(name, cls, category, group_of(category, cls), model(i), e.path)
    return out


def layout(sc: Scenery, group_of_name: dict[int, str], budget: dict[str, int | None]) -> dict[str, list]:
    """The objects to show, per group: {group: [(name index, x, y, turn, size), ...]}. `budget` says how many of a
    group to show at most (None: all; a group left out: none). A group over its budget is sampled by whole clumps
    (a child block full of trees is taken or skipped as one), so the walk only visits what it shows."""
    wanted = {g for g in budget}
    G = sorted(wanted)
    gi = {g: k for k, g in enumerate(G)}
    sym_g = {s: gi[g] for s, g in group_of_name.items() if g in gi}
    n_blocks = len(sc.blocks)
    cnt = [[0] * len(G) for _ in range(n_blocks)]
    for b in reversed(sc.blocks):  # objects of each group under each block
        c = cnt[b.index]
        for it in b.items:
            if it.kind == "object":
                k = sym_g.get(it.symbol)
                if k is not None:
                    c[k] += 1
            elif it.kind == "child":
                cc = cnt[sc._by_offset[it.child_offset]]
                for k in range(len(G)):
                    c[k] += cc[k]
    total = [0] * len(G)
    for g, n in _group_totals(sc, sym_g, len(G)).items():
        total[g] = n
    rate = [1.0 if budget[g] is None or total[gi[g]] <= budget[g] else budget[g] / total[gi[g]] for g in G]
    full = [k for k, g in enumerate(G) if rate[k] >= 1.0]
    acc = [0.0] * len(G)
    out: dict[str, list] = {g: [] for g in G}
    todo = [(r, IDENTITY, False) for r in reversed(sc.roots())]
    while todo:
        i, m, taken = todo.pop()
        for it in sc.blocks[i].items:
            if it.kind == "object":
                k = sym_g.get(it.symbol)
                if k is None:
                    continue
                if not taken and rate[k] < 1.0:
                    acc[k] += rate[k]
                    if acc[k] < 1.0:
                        continue
                    acc[k] -= 1.0
                x, y, turn, size = placement(compose(m, it.matrix()))
                out[G[k]].append((it.symbol, x, y, turn, size))
            elif it.kind == "child":
                j = sc._by_offset[it.child_offset]
                c = cnt[j]
                if not any(c):
                    continue
                if taken or any(c[k] for k in full):
                    todo.append((j, compose(m, it.matrix()), taken))
                    continue
                k = max(range(len(G)), key=lambda q: c[q])  # a clump of sampled groups: take it or skip it whole
                acc[k] += rate[k] * c[k]  # its share of the budget; taken once the share reaches half the clump
                if acc[k] >= c[k] / 2:
                    acc[k] -= c[k]
                    todo.append((j, compose(m, it.matrix()), True))
    return out


def _group_totals(sc: Scenery, sym_g: dict[int, int], n: int) -> dict[int, int]:
    per_type = sc.types()
    out: dict[int, int] = {}
    for s, c in per_type.items():
        k = sym_g.get(s)
        if k is not None:
            out[k] = out.get(k, 0) + c
    return out


MEMBER = "output\\save.boobspc"
SHOW = {"building": None, "prop": 20000, "vegetation": 40000}  # what the Studio's map view draws


def view(map_arc, unit_arc, descs: dict[str, Descriptor] | None = None, budget: dict | None = None) -> dict:
    """A map's scenery for the Studio's map view (JSON-ready): {"types": [[short name, group, category, model]],
    "groups": {group: {"shown": n, "total": n}}, "items": {group: [type, x, y, turn, size, ...] flat}} with every
    building and a sample of props and trees (`budget`, default SHOW). Positions are map units; the game sets
    objects on the ground itself."""
    descs = descriptors(unit_arc) if descs is None else descs
    sc = Scenery(map_arc.read(map_arc.find(MEMBER)))
    budget = SHOW if budget is None else budget
    group_of_name = {i: descs[n].group for i, n in enumerate(sc.names) if n in descs}
    shown = layout(sc, group_of_name, budget)
    totals: dict[str, int] = {}
    for s, c in sc.types().items():
        g = group_of_name.get(s)
        if g:
            totals[g] = totals.get(g, 0) + c
    index: dict[int, int] = {}
    types, items = [], {}
    for g, rows in shown.items():
        flat = []
        for s, x, y, turn, size in rows:
            if s not in index:
                index[s] = len(types)
                d = descs[sc.names[s]]
                types.append([d.name.split("/", 1)[-1], d.group, d.category, d.model or ""])
            flat += [index[s], round(x), round(y), round(turn, 3), round(size, 2)]
        items[g] = flat
    return {"types": types, "items": items,
            "groups": {g: {"shown": len(shown.get(g, [])), "total": totals.get(g, 0)} for g in budget}}


def placement(m: tuple) -> tuple[float, float, float, float]:
    """x, y, the turn (radians, counterclockwise from +x) and the size (the scale along the object's own x) of a
    placed object's transform."""
    return m[3], m[7], math.atan2(m[4], m[0]), math.hypot(m[0], m[4])
