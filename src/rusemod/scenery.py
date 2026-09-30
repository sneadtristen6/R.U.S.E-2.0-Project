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

    def placings(self) -> tuple[list[int], list]:
        """(how many times the map places each block, its one transform in map coordinates or None when it's placed
        more than once or not at all): parents come before children, so one pass does it."""
        n = len(self.blocks)
        weight, where = [0] * n, [None] * n
        for r in self.roots():
            weight[r] += 1
            where[r] = IDENTITY
        for b in self.blocks:
            for it in b.items:
                if it.kind == "child":
                    j = self._by_offset[it.child_offset]
                    weight[j] += weight[b.index]
                    where[j] = compose(where[b.index], it.matrix()) if where[b.index] is not None else None
        return weight, [w if weight[i] == 1 else None for i, w in enumerate(where)]

    def objects_once(self):
        """(block index, item, transform in map coordinates) for every object on the map exactly once (in a block
        placed once), so it can be changed where it's stored."""
        _weight, where = self.placings()
        for b in self.blocks:
            if where[b.index] is not None:
                for it in b.items:
                    if it.kind == "object":
                        yield b.index, it, compose(where[b.index], it.matrix())

    def roads(self) -> list[tuple]:
        """Every road piece, in map coordinates: a cubic Bézier as (x0, y0, x1, y1, x2, y2, x3, y3). A piece's 15
        words are its start (x, y, z), the start's handle as an offset from it, its end, the end's handle as an offset
        from the end, then three words (3 and two codes on every piece seen); pieces join end to start, handles in
        line. Roads lie on the ground, so their z (0) isn't kept. A few long far-view pieces of the top block repeat
        roads the close pieces already draw."""
        out = []
        todo = [(r, IDENTITY) for r in reversed(self.roots())]
        while todo:
            i, m = todo.pop()
            for it in self.blocks[i].items:
                if it.kind == "child":
                    todo.append((self._by_offset[it.child_offset], compose(m, it.matrix())))
                elif it.kind == "road":
                    f = struct.unpack_from("<12f", it.data)
                    ends = ((f[0], f[1]), (f[0] + f[3], f[1] + f[4]), (f[6] + f[9], f[7] + f[10]), (f[6], f[7]))
                    out.append(tuple(v for x, y in ends for v in (m[0] * x + m[1] * y + m[3], m[4] * x + m[5] * y + m[7])))
        return out

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
    models: tuple = ()  # every model it's drawn with close up: a tree is two (its leaves and its trunk)

    @property
    def bridge(self) -> bool:
        return is_bridge(self.category)


def is_bridge(category: str | None) -> bool:
    """A bridge kind: the game editor files them under …/Ponts (Normandie, Italie, Allemagne, Ardennes, Tunisie).
    Placed by a mod, a bridge opens the ground along its deck to units instead of blocking it (rusemod.bridges)."""
    return (category or "").lower().rstrip("/").split("/")[-1] == "ponts"


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

        def models(i, depth=0) -> list:
            """The close-up models under object i: through a multi-state's normal look, a multi-mode's nearest
            level and a composite's every part (a tree: its leaves and its trunk) to each Model3DFromFile.
            Composites are from DomesticNukes and his Claude's scenery notes."""
            if i is None or depth > 8:
                return []
            d = objs[i]
            if "ModelASE" in d:
                name = text(d["ModelASE"]).replace("DataDir:\\", "").lower()
                return [name] if name else []
            if "SDFalse" in d:
                return models(local_ref(d["SDFalse"]), depth + 1)
            if "ModeEntry" in d:
                entries = [local_ref(v) for v in sub_values(d["ModeEntry"])]
                entries = [x for x in entries if x is not None]
                entries.sort(key=lambda x: objs[x]["ModeMask"].scalar() if "ModeMask" in objs[x] else 99)
                for x in entries:
                    found = models(local_ref(objs[x].get("SceneryDescriptor")) if objs[x].get("SceneryDescriptor")
                                   else None, depth + 1)
                    if found:
                        return found
            if "DescriptorComposition" in d:
                return [m for v in sub_values(d["DescriptorComposition"]) for m in models(local_ref(v), depth + 1)]
            if "SceneryDescriptor" in d:
                v = d["SceneryDescriptor"]
                refs = [local_ref(x) for x in sub_values(v)] if v.tc == 0x11 else [local_ref(v)]
                return [m for r in refs for m in models(r, depth + 1)]
            return []

        for i, d in enumerate(objs):
            name = text(d.get("RegistrationName"))
            if not name:
                path = n.exports.get(i) or ""
                name = path[2:] if path.startswith("$/TypeWarrior/") else ""
            if not name or name in out:
                continue
            cls = n.classes[n.objects[i].cls]
            category = text(d.get("Classement"))
            found = models(i)
            out[name] = Descriptor(name, cls, category, group_of(category, cls), found[0] if found else None, e.path,
                                   tuple(found))
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
    """A map's scenery for the Studio's map view (JSON-ready): {"types": [[short name, group, category, model,
    [every model]]],
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
                types.append([d.name.split("/", 1)[-1], d.group, d.category, d.model or "", list(d.models)])
            flat += [index[s], round(x), round(y), round(turn, 3), round(size, 2)]
        items[g] = flat
    per_type = sc.types()
    palette = sorted(([descs[n].name, n.split("/", 1)[-1], descs[n].group, descs[n].category, per_type.get(i, 0)]
                      for i, n in enumerate(sc.names[:len(sc.flags)])
                      if sc.flags[i] == 1 and n in descs and descs[n].group in PLACEABLE),
                     key=lambda r: (PLACEABLE.index(r[2]), -r[4], r[1].lower()))
    return {"types": types, "items": items, "palette": palette,
            "groups": {g: {"shown": len(shown.get(g, [])), "total": totals.get(g, 0)} for g in budget}}


PLACEABLE = ("building", "prop", "vegetation")  # what the Studio offers to place (decals come later)


# --- adding objects (a mod's maps/<map>/scenery.toml; docs/MOD_FORMAT.md §8) ---
FILLER = 0xCAFE5A1E   # every block's items start with this word, which the game never reads
BLOCK_TAIL = bytes.fromhex("000bb00bb00bb00b")  # bytes 0x18-0x1f of a long block header, as the shipped blocks have
ALL_TIERS = 0x1F      # a block's LOD mask: drawn close, middle and far (a superset only costs culling)
MARGIN = 5000.0       # added to a new block's box around its objects' positions (map units, times their size)
GROUP = 40000.0       # objects further apart than this (400 m) go in separate new blocks, each hung on an object near
                      # them: the game draws a block when the object it hangs on is in view (owner's test, 2026-09-30:
                      # towers hung on a decal 3 km away never showed)


class SceneryEditError(ValueError):
    pass


@dataclass(frozen=True)
class NewObject:
    type: str            # a scenery type the map already uses, e.g. TypeWarrior/MairieNormande
    x: float
    y: float
    turn: float = 0.0    # degrees, from east toward south (clockwise on the minimap)
    size: float = 1.0
    solid: bool = True   # a building units can't go through (rusemod.nav.solid_blocks); false: only drawn
    stretch: float = 1.0  # a further scale along the object's own y only: a bridge's length (the shipped maps
                          # stretch theirs 0.9 to 1.9 to fit the river)
    lift: float = 0.0    # its height against the ground the game puts it on (map units; shipped bridges sit
                         # 130 to 850 below)

    def matrix(self) -> tuple:
        """Where it goes, in map coordinates: turned, sized, stretched along its own y, lifted."""
        t = math.radians(self.turn)
        c, s = math.cos(t) * self.size, math.sin(t) * self.size
        k = self.stretch
        return (c, -s * k, 0.0, self.x, s, c * k, 0.0, self.y, 0.0, 0.0, self.size, self.lift)


def _inverse(m: tuple) -> tuple:
    a, b, c, tx, d, e, f, ty, g, h, i, tz = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-12:
        raise SceneryEditError("a block is placed with a flat transform")
    r = [(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det,
         (f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det,
         (d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det]
    t = [-(r[0] * tx + r[1] * ty + r[2] * tz), -(r[3] * tx + r[4] * ty + r[5] * tz), -(r[6] * tx + r[7] * ty + r[8] * tz)]
    return (r[0], r[1], r[2], t[0], r[3], r[4], r[5], t[1], r[6], r[7], r[8], t[2])


def encode_transform(m: tuple) -> tuple[int, bytes]:
    """The shortest exact-enough form of a 3x4 transform: compact when it's a turn and scale about the vertical
    (each of the four numbers within +-3), else the full 12 floats."""
    a, b, c, tx, d, e, f, ty, g, h, i, tz = m
    if c == f == g == h == 0 and max(abs(a), abs(b), abs(d), abs(e)) <= 3.0:
        q = [max(-32767, min(32767, round(v / SCALE16))) for v in (a, b, d, e)]
        return T_COMPACT, struct.pack("<4h4f", *q, tx, ty, tz, i)
    return T_FULL, struct.pack("<12f", *m)


def _identity_data(kind: int) -> bytes:
    """A transform of the given kind that changes nothing (a compact one is within 1/32767 of it)."""
    return {T_IDENTITY: b"", T_MOVE: struct.pack("<3f", 0, 0, 0), T_FULL: struct.pack("<12f", *IDENTITY),
            T_COMPACT: struct.pack("<4h4f", round(1 / SCALE16), 0, 0, round(1 / SCALE16), 0, 0, 0, 1.0)}[kind]


def _carrier(sc: Scenery, near: tuple | None = None) -> tuple[Block, Item, tuple]:
    """An object item to turn into the reference to the new block: in a block placed exactly once. `near` (x, y):
    the object nearest it, in the small block nearest it (a block's distance counts half its size, so the map-wide
    top block loses to a village's); else the top block first. An exact kind (none, a move, full) before a compact
    one. Returns (its block, it, the block's transform in map coordinates)."""
    _weight, where = sc.placings()
    best = None
    for b in sc.blocks:
        if where[b.index] is None:
            continue
        objects = [it for it in b.items if it.kind == "object"]
        if not objects:
            continue
        if near is None:
            return b, min(objects, key=lambda it: (it.tform == T_COMPACT, it.at)), where[b.index]
        w = where[b.index]
        x0, y0, x1, y1 = b.bbox
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        wx, wy = w[0] * cx + w[1] * cy + w[3], w[4] * cx + w[5] * cy + w[7]
        score = math.hypot(wx - near[0], wy - near[1]) + math.hypot(x1 - x0, y1 - y0) * math.hypot(w[0], w[4]) / 2
        if best is None or score < best[0]:
            best = (score, b, objects)
    if best is None:
        raise SceneryEditError("the map has no object to hang new ones on")
    _s, b, objects = best
    w = where[b.index]

    def distance(it):
        m = it.matrix()
        return math.hypot(w[0] * m[3] + w[1] * m[7] + w[3] - near[0], w[4] * m[3] + w[5] * m[7] + w[7] - near[1])
    return b, min(objects, key=lambda it: (distance(it), it.tform == T_COMPACT, it.at)), w


def _new_block(items: list[bytes], box: tuple) -> bytes:
    offsets, pos = [], 4
    for it in items:
        offsets.append(pos)
        pos += len(it)
    entries = offsets + offsets  # every item is drawn from far too: the far-view items first, then all of them
    p = len(items)
    nodes = (struct.pack("<IHBB", (ALL_TIERS << 20) | (2 << 2), p, 0xFF, 0)
             + struct.pack("<IHBB", 0xC0000000 | (0x08 << 20), p, 0xFF, 0)
             + struct.pack("<IHBB", 0xC0000000 | ((ALL_TIERS & ~0x08) << 20), 0, 0xFF, 0))
    head = struct.pack("<II4f", 0x80000000 | len(entries), 3, *box) + BLOCK_TAIL
    return head + struct.pack(f"<{len(entries)}I", *entries) + nodes + struct.pack("<I", FILLER) + b"".join(items)


def _groups(objects: list[NewObject]) -> list[list[NewObject]]:
    """Objects in groups of neighbours: each joins the first group with an object within GROUP of it."""
    out: list[list[NewObject]] = []
    for o in objects:
        home = next((g for g in out if any(math.hypot(o.x - p.x, o.y - p.y) <= GROUP for p in g)), None)
        if home is None:
            out.append([o])
        else:
            home.append(o)
    return out


def add_objects(data: bytes, objects: list[NewObject]) -> tuple[bytes, list[str]]:
    """The scenery file with `objects` added, per group of neighbours (GROUP). The game draws the top block through
    its tree: a spatial tree whose first node counts the entries seen from far (listed first). So each group goes in
    a new block that wraps the nearest block the top block lists for far view (a village, a farm): that reference now
    points to the new block, which places the old one where it was and the new objects; the tree is unchanged, and the
    objects are drawn wherever and from however far that block is. The new block goes right after the top block (a
    reference must point forward), so every later reference moves by its size. A map whose top block lists no block
    for far view gets the first way DomesticNukes proved in the game (_add_block: an object near them becomes the
    reference). The grids are left alone. Types must be ones the map already uses (in its name table). Returns (new
    file, notes)."""
    if not objects:
        return bytes(data), []
    notes = []
    for group in _groups(objects):
        sc = Scenery(data)
        far = _far_children(sc)
        data, more = _wrap(sc, data, group, far) if far else _add_block(data, group)
        notes += more
    return data, notes


BURY = 200000.0  # map units an object sunk out of sight goes under the ground (about 770 m)
SHRINK = 0.05    # and the size it shrinks to, in case the game sets it on the ground whatever its height


def bury_objects(data: bytes, places: list[tuple[int, int]]) -> tuple[bytes, list[str]]:
    """The scenery file with the objects at `places` ((block index, item offset from the block's items start), as
    Scenery.objects_once gives them) sunk BURY under the ground and shrunk to SHRINK: out of sight, while the file
    keeps every size and offset (each transform is rewritten where it's stored, in its own kind). An object stored
    with no transform (the bare "no change" kind) can't be sunk. Returns (new file, notes)."""
    if not places:
        return bytes(data), []
    sc = Scenery(data)
    out = bytearray(data)
    for bi, at in places:
        if not 0 <= bi < len(sc.blocks):
            raise SceneryEditError(f"there's no block {bi} to sink an object in")
        b = sc.blocks[bi]
        it = next((i for i in b.items if i.at == at and i.kind == "object"), None)
        if it is None:
            raise SceneryEditError(f"block {bi} has no object at {at} to sink")
        m = it.matrix()
        if it.tform == T_IDENTITY:
            raise SceneryEditError(f"block {bi}: the object at {at} is stored without a transform, so it can't be sunk")
        if it.tform == T_MOVE:
            new = struct.pack("<3f", m[3], m[7], m[11] - BURY)
        elif it.tform == T_FULL:
            new = struct.pack("<12f", *[v * SHRINK if k % 4 != 3 else v for k, v in enumerate(m[:11])], m[11] - BURY)
        else:
            q = struct.unpack_from("<4h", it.data)
            new = struct.pack("<4h4f", *[round(v * SHRINK) for v in q], m[3], m[7], m[11] - BURY, m[10] * SHRINK)
        if len(new) != len(it.data):
            raise SceneryError("a sunk object's transform changed size")
        at_file = sc.data_off + b.offset + b.items_start + it.at + 4
        out[at_file:at_file + len(new)] = new
    out[:16] = hashlib.md5(bytes(out[16:])).digest()
    return bytes(out), [f"{len(places)} object(s) sunk out of sight"]


def _far_children(sc: Scenery) -> list[Item]:
    """The top block's references to blocks that it lists for far view (its first node's count of entries)."""
    roots = sc.roots()
    if roots != [0] or len(sc.blocks[0].nodes) < 8:
        return []
    b = sc.blocks[0]
    far = struct.unpack_from("<H", b.nodes, 4)[0]
    by_at = {it.at: it for it in b.items}
    return [by_at[a] for a in b.entries[:far] if a in by_at and by_at[a].kind == "child"]


def _world_box(sc: Scenery, it: Item) -> tuple[float, float, float, float]:
    """A top-block reference's block's box on the map (its corners through the reference's transform)."""
    m = it.matrix()
    x0, y0, x1, y1 = sc.block_at(it.child_offset).bbox
    xs, ys = [], []
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        xs.append(m[0] * x + m[1] * y + m[3])
        ys.append(m[4] * x + m[5] * y + m[7])
    return min(xs), min(ys), max(xs), max(ys)


def _wrap(sc: Scenery, data: bytes, objects: list[NewObject], far: list[Item]) -> tuple[bytes, list[str]]:
    index = {name: i for i, name in enumerate(sc.names[:len(sc.flags)]) if sc.flags[i] == 1}
    words: dict[int, int] = {}
    for b in sc.blocks:
        for it in b.items:
            if it.kind == "object":
                words.setdefault(it.symbol, it.word & 0x7C000000)
    cx, cy = sum(o.x for o in objects) / len(objects), sum(o.y for o in objects) / len(objects)

    def score(it):  # how far the group's middle is from the block's box (0 inside), then the smaller box
        x0, y0, x1, y1 = _world_box(sc, it)
        return math.hypot(max(x0 - cx, 0.0, cx - x1), max(y0 - cy, 0.0, cy - y1)), (x1 - x0) * (y1 - y0)
    carrier = min(far, key=score)
    top = sc.blocks[0]
    ins = top.offset + len(top.raw)  # the new block goes right after the top block
    if len(sc.blocks) > 1 and sc.blocks[1].offset != ins:
        raise SceneryError("the scenery file's blocks aren't in the order this writer knows")
    to_local = _inverse(carrier.matrix())
    inner = sc.block_at(carrier.child_offset)
    items, xs, ys = [], [inner.bbox[0], inner.bbox[2]], [inner.bbox[1], inner.bbox[3]]
    for o in objects:
        sym = index.get(o.type)
        if sym is None:
            raise SceneryEditError(f"{o.type} isn't used on this map, so the map can't take it (only types its "
                                   f"scenery already lists)")
        if not 0.05 <= o.size <= 50:
            raise SceneryEditError(f"{o.type}: size {o.size} is outside 0.05 to 50")
        local = compose(to_local, o.matrix())
        kind, tdata = encode_transform(local)
        items.append(struct.pack("<I", 0x80000000 | words.get(sym, 0) | (sym << 4) | kind) + tdata)
        pad = MARGIN * o.size * max(1.0, o.stretch)
        xs += [local[3] - pad, local[3] + pad]
        ys += [local[7] - pad, local[7] + pad]
    probe = _new_block([b"\0" * 4] + items, (0.0, 0.0, 0.0, 0.0))  # its size, to know where the old block moves to
    shift = len(probe)
    moved_to = carrier.child_offset + shift
    if (sc.fields[3] + shift) & ~0xFFFFFC:
        raise SceneryEditError("the map's scenery is too big for a new block to be referenced")
    # the old block, placed where it was (no transform: the reference to the new block keeps the old one's)
    first = struct.pack("<I", (carrier.word & 0xFF000000) | moved_to | T_IDENTITY)
    new = _new_block([first] + items, (min(xs), min(ys), max(xs), max(ys)))
    # every block, its references to blocks after the top one moved by the new block's size
    f = list(sc.fields)
    tab_off, tab_n, data_off, data_len = f[0], f[1], f[2], f[3]
    if tab_off != 124 or data_off != tab_off + 4 * tab_n:
        raise SceneryError("the scenery file's tables aren't in the order this writer knows")
    parts = []
    for b in sc.blocks:
        raw = bytearray(b.raw)
        for it in b.items:
            if it.kind != "child":
                continue
            at = b.items_start + it.at
            if b.index == 0 and it.at == carrier.at:
                target = ins
            else:
                target = it.child_offset + shift if it.child_offset >= ins else it.child_offset
            struct.pack_into("<I", raw, at, (it.word & ~0x00FFFFFC) | target)
        parts.append(bytes(raw))
        if b.index == 0:
            parts.append(new)
    body_data = b"".join(parts)
    if len(body_data) != data_len + shift:
        raise SceneryError("the scenery file's blocks don't fill its data exactly")
    end = data_off + data_len
    for k in (4, 6, 8, 10, 12, 20, 22, 24):  # the tables after the data move by the table's new entry and the block
        if f[k] < end:
            raise SceneryError("the scenery file's tables aren't in the order this writer knows")
        f[k] += 4 + shift
    f[1], f[2], f[3] = tab_n + 1, data_off + 4, data_len + shift
    table = list(struct.unpack_from(f"<{tab_n}I", data, tab_off))  # the offsets, then the end marker
    table = [table[0], ins] + [v + shift for v in table[1:]]
    body = (VERSION + struct.pack("<26I", *f) + struct.pack(f"<{len(table)}I", *table) + body_data + data[end:])
    x0, y0, x1, y1 = _world_box(sc, carrier)
    far_m = math.hypot(max(x0 - cx, 0.0, cx - x1), max(y0 - cy, 0.0, cy - y1)) / 100
    return hashlib.md5(body).digest() + body, [
        f"{len(objects)} object(s) added in a new block with block {inner.index} (drawn from far, {far_m:.0f} m "
        f"from them), placed where the top block had it"]


def _add_block(data: bytes, objects: list[NewObject]) -> tuple[bytes, list[str]]:
    sc = Scenery(data)
    index = {name: i for i, name in enumerate(sc.names[:len(sc.flags)]) if sc.flags[i] == 1}  # not Route etc.
    words: dict[int, int] = {}  # a placed item's high bits (its LOD tier and variation) per type
    for b in sc.blocks:
        for it in b.items:
            if it.kind == "object":
                words.setdefault(it.symbol, it.word & 0x7C000000)
    block, carrier, frame = _carrier(sc, (sum(o.x for o in objects) / len(objects), sum(o.y for o in objects) / len(objects)))
    # the reference's own "no change" transform: exact, except a compact one (a scale of 32766.99/32767); new
    # objects are placed through it, and the carried object gets its inverse, so nothing moves
    q = decode_transform(carrier.tform, _identity_data(carrier.tform))
    to_local = _inverse(compose(frame, q))
    if q == IDENTITY:
        items = [struct.pack("<I", carrier.word) + carrier.data]
    else:
        kind, tdata = encode_transform(compose(_inverse(q), carrier.matrix()))
        items = [struct.pack("<I", (carrier.word & ~3) | kind) + tdata]
    xs, ys, notes = [], [], []
    for o in objects:
        sym = index.get(o.type)
        if sym is None:
            raise SceneryEditError(f"{o.type} isn't used on this map, so the map can't take it (only types its "
                                   f"scenery already lists)")
        if not 0.05 <= o.size <= 50:
            raise SceneryEditError(f"{o.type}: size {o.size} is outside 0.05 to 50")
        local = compose(to_local, o.matrix())
        kind, tdata = encode_transform(local)
        items.append(struct.pack("<I", 0x80000000 | words.get(sym, 0) | (sym << 4) | kind) + tdata)
        xs.append(local[3])
        ys.append(local[7])
    cm = carrier.matrix()
    xs.append(cm[3])
    ys.append(cm[7])
    pad = MARGIN * max([1.0] + [o.size for o in objects])
    new = _new_block(items, (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad))
    f = list(sc.fields)
    tab_off, tab_n, data_off, data_len = f[0], f[1], f[2], f[3]
    if tab_off != 124 or data_off != tab_off + 4 * tab_n:
        raise SceneryEditError("the scenery file's tables aren't in the order this writer knows")
    offset = data_len  # the new block goes after every other block: all references stay forward
    if offset & ~0xFFFFFC:
        raise SceneryEditError("the map's scenery is too big for a new block to be referenced")
    ref = (offset & 0xFFFFFC) | (carrier.word & 0x0C000000) | carrier.tform
    patched = bytearray(data[data_off:data_off + data_len])
    at = block.offset + block.items_start + carrier.at
    patched[at:at + 4 + len(carrier.data)] = struct.pack("<I", ref) + _identity_data(carrier.tform)
    end = data_off + data_len
    shift = 4 + len(new)
    for k in (4, 6, 8, 10, 12, 20, 22, 24):  # the tables after the data move by the table's new entry and the block
        if f[k] < end:
            raise SceneryEditError("the scenery file's tables aren't in the order this writer knows")
        f[k] += shift
    f[1], f[2], f[3] = tab_n + 1, data_off + 4, data_len + len(new)
    table = list(struct.unpack_from(f"<{tab_n}I", data, tab_off))
    table = table[:-1] + [offset, data_len + len(new)]
    body = (VERSION + struct.pack("<26I", *f) + struct.pack(f"<{len(table)}I", *table) + bytes(patched) + new
            + data[end:])
    out = hashlib.md5(body).digest() + body
    cw = compose(frame, cm)
    notes.append(f"{len(objects)} object(s) added in a new block, hung on {sc.names[carrier.symbol]} in block "
                 f"{block.index}, {math.hypot(cw[3] - objects[0].x, cw[7] - objects[0].y) / 100:.0f} m away")
    return out, notes


def parse_objects(rows: list, where: str = "scenery.toml") -> list[NewObject]:
    out = []
    for k, row in enumerate(rows):
        extra = sorted(set(row) - {"type", "x", "y", "turn", "size", "solid", "stretch", "lift"})
        if extra:
            raise SceneryEditError(f"{where}: object {k + 1}: unknown key {extra[0]!r}")
        try:
            if not isinstance(row.get("solid", True), bool):
                raise SceneryEditError(f"{where}: object {k + 1}: solid must be true or false")
            o = NewObject(str(row["type"]), float(row["x"]), float(row["y"]), float(row.get("turn", 0.0)),
                          float(row.get("size", 1.0)), row.get("solid", True), float(row.get("stretch", 1.0)),
                          float(row.get("lift", 0.0)))
        except KeyError as exc:
            raise SceneryEditError(f"{where}: object {k + 1} has no {exc.args[0]}") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: object {k + 1}: x, y, turn, size, stretch and lift must be numbers") from None
        if (not all(math.isfinite(v) for v in (o.x, o.y, o.turn, o.size, o.stretch, o.lift)) or not 0.05 <= o.size <= 50
                or not 0.2 <= o.stretch <= 5 or abs(o.lift) > 100000):
            raise SceneryEditError(f"{where}: object {k + 1}: a number is out of range (size: 0.05 to 50, stretch: "
                                   f"0.2 to 5, lift: within 100,000)")
        out.append(o)
    return out


def objects_toml(objects: list[NewObject], header: str = "") -> str:
    lines = [f"# {ln}" if ln else "#" for ln in header.splitlines()] + ([""] if header else [])
    for o in objects:
        lines += ["[[object]]", f'type = "{o.type}"', f"x = {o.x!r}", f"y = {o.y!r}", f"turn = {o.turn!r}",
                  f"size = {o.size!r}"] + ([] if o.solid else ["solid = false"])
        lines += ([f"stretch = {o.stretch!r}"] if o.stretch != 1.0 else []) + ([f"lift = {o.lift!r}"] if o.lift else []) + [""]
    return "\n".join(lines) + "\n" if lines else "\n"


def placement(m: tuple) -> tuple[float, float, float, float]:
    """x, y, the turn (radians, counterclockwise from +x) and the size (the scale along the object's own x) of a
    placed object's transform."""
    return m[3], m[7], math.atan2(m[4], m[0]), math.hypot(m[0], m[4])
