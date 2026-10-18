"""A map's scenery: every tree, house, field, road piece and ground decal the game draws, read, added to (a mod's
objects) and erased from (a mod's erase areas), following the notes of DomesticNukes and his Claude (checked on
every shipped map). Objects stand on the ground wherever it is: the game puts them there when it loads the map."""
from __future__ import annotations

import bisect
import collections
import hashlib
import json
import math
import re
import struct
from dataclasses import dataclass, field

VERSION = b"0.6\0"
_HEAD = struct.Struct("<4s26I")
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
        return link_offset(self.word)

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
            # rule: scenery-md5
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

    def holding(self, symbols) -> list[bool]:
        """Whether each block puts an object of one of `symbols` (name indexes) on the map, itself or through its
        children: one pass from the last block back, as counts()."""
        out = [False] * len(self.blocks)
        for b in reversed(self.blocks):
            out[b.index] = any(it.symbol in symbols if it.kind == "object"
                               else it.kind == "child" and out[self._by_offset[it.child_offset]] for it in b.items)
        return out

    def walk(self, block: int | None = None, matrix: tuple = IDENTITY, only=None):
        """(name index, 3x4 transform in map coordinates) for every object under `block` (default: every root); with
        `only` (a set of name indexes), those objects alone, and blocks holding none of them aren't walked (a map
        places millions of objects: its bridges are found in a moment)."""
        keep = self.holding(only) if only is not None else None
        todo = [(r, IDENTITY) for r in reversed(self.roots())] if block is None else [(block, matrix)]
        while todo:
            i, m = todo.pop()
            if keep is not None and not keep[i]:
                continue
            for it in self.blocks[i].items:
                if it.kind == "object":
                    if only is None or it.symbol in only:
                        yield it.symbol, compose(m, it.matrix())
                elif it.kind == "child":
                    j = self._by_offset[it.child_offset]
                    if keep is None or keep[j]:
                        todo.append((j, compose(m, it.matrix())))

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
        """Every road piece, in map coordinates: a cubic Bézier as (x0, y0, x1, y1, x2, y2, x3, y3); pieces join end to
        start. Roads lie on the ground, so their height isn't kept. A few long far-view pieces of the top block repeat
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
        return is_bridge(self.category, self.name)


RUINS = ("_detruit", "_dest")  # a bridge's wreck (Bridge_Dest, Pont_Allemagne_03_Detruit): no deck, no floor


def is_bridge(category: str | None, name: str = "") -> bool:
    """A bridge kind units can cross. The game editor files most under …/Ponts (Normandie, Italie, Allemagne,
    Ardennes, Tunisie) but Holland's (Pont_Hollande_*, on 4 maps, with floors) under its town buildings, so a `Pont_`
    name counts too; a wreck doesn't, nor do the jetties (Ponton…). Placed by a mod, a bridge opens the ground along
    its deck to units instead of blocking it (rusemod.bridges)."""
    last = name.rsplit("/", 1)[-1].lower()
    if last.endswith(RUINS):
        return False
    return (category or "").lower().rstrip("/").split("/")[-1] == "ponts" or last.startswith("pont_")


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
    [every model], whether it's a bridge]],
    "groups": {group: {"shown": n, "total": n}}, "items": {group: [type, x, y, turn, size, ...] flat},
    "palette": [[type, short name, group, category, how many the map has, its names, what it is, its number in
    types]]} with every building and a sample of props and trees (`budget`, default SHOW), and every type there is
    to place (the palette). Positions are map units; the game sets objects on the ground itself."""
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
                types.append([d.name.split("/", 1)[-1], d.group, d.category, d.model or "", list(d.models), d.bridge])
            flat += [index[s], round(x), round(y), round(turn, 3), round(size, 2)]
        items[g] = flat
    per_type = sc.types()
    from .scenerynames import kinds, names  # the game names these only in its editor's code, mostly French
    # every type there is to place gets a number in `types` too, after the shown items' own: the Studio makes each
    # one's model (rusemod.models.map_models) for the place list's pictures and what's placed
    rows = []
    for i, n in enumerate(sc.names[:len(sc.flags)]):
        if sc.flags[i] != 1 or n not in descs or descs[n].group not in PLACEABLE:
            continue
        d = descs[n]
        if i not in index:
            index[i] = len(types)
            types.append([d.name.split("/", 1)[-1], d.group, d.category, d.model or "", list(d.models), d.bridge])
        rows.append([d.name, n.split("/", 1)[-1], d.group, d.category, per_type.get(i, 0), names(n.split("/", 1)[-1]),
                     kinds(d.category), index[i]])
    palette = sorted(rows, key=lambda r: (PLACEABLE.index(r[2]), -r[4], r[1].lower()))
    return {"types": types, "items": items, "palette": palette,
            "groups": {g: {"shown": len(shown.get(g, [])), "total": totals.get(g, 0)} for g in budget}}


PLACEABLE = ("building", "prop", "vegetation")  # what the Studio offers to place (decals come later)


# --- adding objects (a mod's maps/<map>/scenery.toml; docs/MOD_FORMAT.md §8) ---
FILLER = 0xCAFE5A1E   # every block's items start with this word, which the game never reads
BLOCK_TAIL = bytes.fromhex("000bb00bb00bb00b")  # bytes 0x18-0x1f of a long block header, as the shipped blocks have
ALL_TIERS = 0x1F      # a block's LOD mask: drawn close, middle and far (a superset only costs culling)
WORD_KEEP = 0x40000000  # what a new object copies of its type's first shipped item word: bit 30, not the detail
                        # tier (bits 26-27: a tier above 0 is missing at the lowest scenery detail) nor the variation
                        # (bits 28-29: the game turns the object by a pseudo-random angle the Studio doesn't show)
ROAD_TIER = 0x20      # a tree node's road mark, above the LOD mask (bit 25 of its word): the game's road pass walks
ROAD_BIT = ROAD_TIER << 20  # Route pieces only through nodes that carry it (every Route piece of the shipped maps does);
#                             what that pass draws on screen isn't known (TESTS.md T12)
MARGIN = 5000.0       # added to a new block's box around its objects' positions (map units, times their size)
LEAF_MOST = 4         # entries a leaf of a new block's tree lists at most, as the shipped trees' leaves do (1 to 4)
BLOCK_MOST = 12000    # objects one new block holds at most: each is listed twice (far and full), a tree node splits
                      # its entries at a 16-bit index, and the shipped maps' biggest block lists 39,699 (M03_Italie)
WIDEN_MOST = 2500     # objects one widened carrier takes at most (add_objects): D-Day's blocks hold up to 2,830 in
                      # 99 of 100 (measured 2026-10-15); the blank farm's field 7, drawn, hung 1,637 on one
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
    levels: int = 0      # which of the decor dresser's levels draw it, as a draw-tree LOD mask (1/2 close, 4 middle,
                         # 0x10 middle with GroundQuality, 8 far): the mask a shipped copy of it carries (copy_objects);
                         # 0 = drawn by every level, far included (what placed buildings and trees get)
    height: float = 0.0  # its scale upward when not its size (a shipped plant is often flatter or taller than it is
                         # wide: copy_objects keeps it); 0 = its size
    up: tuple = ()       # its own up direction when it is tilted (a unit vector x, y, z: a rock laid to its slope,
                         # rusemod.rocks); () = upright. The game draws a tilted full transform (the shipped maps'
                         # leaning ladders) and still sets it on the ground by its `lift` (measured 2026-10-16)

    def matrix(self) -> tuple:
        """Where it goes, in map coordinates: turned, sized, stretched along its own y, tilted to `up`, lifted."""
        t = math.radians(self.turn)
        k = self.stretch
        if not self.up:
            c, s = math.cos(t) * self.size, math.sin(t) * self.size
            return (c, -s * k, 0.0, self.x, s, c * k, 0.0, self.y, 0.0, 0.0, self.height or self.size, self.lift)
        # its own x: the turn's direction laid into the plane square to `up`; its own y: up across that
        ux, uy, uz = self.up
        ax, ay = math.cos(t), math.sin(t)
        d = ax * ux + ay * uy
        xx, xy, xz = ax - d * ux, ay - d * uy, -d * uz
        n = math.sqrt(xx * xx + xy * xy + xz * xz) or 1.0
        xx, xy, xz = xx / n, xy / n, xz / n
        yx, yy, yz = uy * xz - uz * xy, uz * xx - ux * xz, ux * xy - uy * xx
        s, h = self.size, self.height or self.size
        return (xx * s, yx * s * k, ux * h, self.x, xy * s, yy * s * k, uy * h, self.y, xz * s, yz * s * k, uz * h,
                self.lift)


ROAD_PIECE = 4000.0   # map units a new road's sticker pieces run (the shipped ones: 1,300 to 73,000, about 4,100 typical)


@dataclass(frozen=True)
class RoadPiece:
    """One piece of a road sticker (the game's `Route` items, a STICKERS type). The map's road model
    (rusemod.roadstrips) is built from them; a new road gets these pieces, to match the map's own, and the model's
    strips. What the game draws from them, and what draws the close-up road, isn't known (TESTS.md T12): only the
    painted ground is seen showing a new road, from afar. A cubic from (x0, y0) to (x1, y1), each end's handle an
    offset from it (the shipped pieces' are a tenth of the piece, along it)."""
    x0: float
    y0: float
    hx0: float
    hy0: float
    x1: float
    y1: float
    hx1: float
    hy1: float

    @property
    def x(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def y(self) -> float:
        return (self.y0 + self.y1) / 2


def road_pieces(line, step: float = ROAD_PIECE) -> list[RoadPiece]:
    """A road's line (map points, in order) as sticker pieces about `step` long, end to end, the way the shipped
    roads are cut: each piece straight, its handles a tenth of it."""
    pts = [tuple(map(float, line[0]))]
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        d = math.hypot(bx - ax, by - ay)
        n = max(1, round(d / step))
        pts += [(ax + (bx - ax) * k / n, ay + (by - ay) * k / n) for k in range(1, n + 1)]
    merged = [pts[0]]  # short steps (a line's own close points) joined up to about a piece
    for q in pts[1:-1]:
        if math.hypot(q[0] - merged[-1][0], q[1] - merged[-1][1]) >= step * 0.75:
            merged.append(q)
    if math.hypot(pts[-1][0] - merged[-1][0], pts[-1][1] - merged[-1][1]) > 1.0 or len(merged) == 1:
        merged.append(pts[-1])
    out = []
    for (ax, ay), (bx, by) in zip(merged, merged[1:]):
        dx, dy = (bx - ax) / 10, (by - ay) / 10
        out.append(RoadPiece(ax, ay, dx, dy, bx, by, -dx, -dy))
    return out


# What draws a road up close (proven in the game on D-Day, 2026-10-02, the owner: "night and day"): the map's asphalt
# stickers laid along it the way the map lays its own, each with an edge sticker either side, on a road whose ground is
# painted as the map's roads are (rusemod.groundpaint.road_profile), with the plants and props standing on its path
# taken off. Measured on D-Day's own roads: an asphalt sticker every 1,506 to 1,598 along (its x axis along the road),
# size 2.0; two edge stickers at the same place, 1,361 to 1,405 across, the right one turned as the asphalt, the left
# one turned round (22,841 pairs). Every shipped map with roads lays them this way, with one of three pairs (counted
# on all 32: about twice as many edge stickers beside its roads as asphalt ones on them): D-Day's on 27 maps, and on
# the desert maps RouteBitume with Bords_Route (Alpha, ChessMate, Edge, Mireille: one every 1,465, size 2.0) or the
# Tunisian pair. Only D-Day's has been seen in the game.
ROAD_DECALS = {  # asphalt -> (its edge sticker, map units between asphalt stickers)
    "TypeWarrior/Route_Bitume": ("TypeWarrior/Route_Bitume_Bords", 1590.0),
    "TypeWarrior/RouteBitume": ("TypeWarrior/Bords_Route", 1465.0),
    "TypeWarrior/RouteBitumeTunisie": ("TypeWarrior/Bords_Route_Tunisie", 1455.0),  # Tunisia's: one every 1,455
}
ROAD_DECAL_GAP = 1590.0    # map units between a road's asphalt stickers (D-Day's)
ROAD_DECAL_EDGE = 1380.0   # an edge sticker's offset across the road
ROAD_DECAL_SIZE = 2.0
ROAD_CLEAR = 1500.0        # map units either side of a new road's line its plants and props are taken off


def road_decals(line, asphalt: str, edge: str | None, gap: float = ROAD_DECAL_GAP) -> list[NewObject]:
    """A road's line (map points, in order) dressed as the map's own roads are up close: an `asphalt` sticker every
    `gap` along it (the first one `gap` from its start, as the tested roads had), turned along the line there, and an
    `edge` sticker either side of each. Never solid."""
    out, walked, nxt = [], 0.0, gap
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        d = math.hypot(bx - ax, by - ay)
        if d <= 0:
            continue
        ux, uy = (bx - ax) / d, (by - ay) / d
        turn = math.degrees(math.atan2(uy, ux))
        while nxt <= walked + d + 1e-6:
            t = nxt - walked
            x, y = ax + ux * t, ay + uy * t
            out.append(NewObject(asphalt, x, y, turn, ROAD_DECAL_SIZE, solid=False))
            if edge:
                nx, ny = -uy, ux
                out.append(NewObject(edge, x + nx * ROAD_DECAL_EDGE, y + ny * ROAD_DECAL_EDGE, turn, ROAD_DECAL_SIZE,
                                     solid=False))
                out.append(NewObject(edge, x - nx * ROAD_DECAL_EDGE, y - ny * ROAD_DECAL_EDGE, turn + 180.0,
                                     ROAD_DECAL_SIZE, solid=False))
            nxt += gap
        walked += d
    return out


def road_clearing(line, half: float = ROAD_CLEAR, keep_trees: bool = False) -> list["EraseArea"]:
    """Erase areas taking the plants and props off a new road's path: circles of `half` along its line, close enough
    that the band is at least 0.97 * `half` wide either side, from half a circle in. Its cover and movement stay as
    they are (keep_ground): only what stands on the road goes. With `keep_trees` (the road's own switch) only the props
    go: the trees and bushes stay over the road."""
    kinds = ("prop",) if keep_trees else ("vegetation", "prop")
    step = half / 2
    out, walked, nxt = [], 0.0, step
    for (ax, ay), (bx, by) in zip(line, line[1:]):
        d = math.hypot(bx - ax, by - ay)
        if d <= 0:
            continue
        while nxt <= walked + d + 1e-6:
            t = nxt - walked
            out.append(EraseArea(ax + (bx - ax) * t / d, ay + (by - ay) * t / d, half, kinds, keep_ground=True))
            nxt += step
        walked += d
    return out


def _road_style(sc: "Scenery") -> tuple[int, tuple[int, int]] | None:
    """(the Route name's number, the two trailing words every piece carries) as the map's own road pieces have
    them, or None when it has none."""
    from collections import Counter
    syms, tails = Counter(), Counter()
    for b in sc.blocks:
        for it in b.items:
            if it.kind == "road":
                syms[it.symbol] += 1
                tails[struct.unpack_from("<2I", it.data, 52)] += 1
    if not syms:
        return None
    return syms.most_common(1)[0][0], tails.most_common(1)[0][0]


def _road_item(piece: RoadPiece, m: tuple, style, count: int) -> tuple[bytes, list[float], list[float]]:
    """A road piece's item bytes in the block whose map-to-block transform is `m`, and its ends' x and y there.
    `count`: how many road pieces the block holds (the first trailing word: the shipped maps' every piece has its
    block's count, 10,505 of 10,505)."""
    sym, tail = style

    def pt(x, y):
        return m[0] * x + m[1] * y + m[3], m[4] * x + m[5] * y + m[7]

    def vec(x, y):
        return m[0] * x + m[1] * y, m[4] * x + m[5] * y
    a, b = pt(piece.x0, piece.y0), pt(piece.x1, piece.y1)
    h0, h1 = vec(piece.hx0, piece.hy0), vec(piece.hx1, piece.hy1)
    body = struct.pack("<I12f3I", 0x01000001 | (sym << 4), a[0], a[1], 0.0, h0[0], h0[1], 0.0, b[0], b[1], 0.0,
                       h1[0], h1[1], 0.0, count, *tail)
    return body, [a[0], b[0]], [a[1], b[1]]


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


def _is_road(item: bytes) -> bool:
    (w,) = struct.unpack_from("<I", item)
    return not w >> 31 and bool(w & 0x01000000)  # as Scenery._block tells them: not an object, not a reference


def _new_block(items: list[bytes], box: tuple, boxes: list[tuple] | None = None,
               levels: list[int] | None = None) -> bytes:
    """A block of `items` in `box`, its tree as the shipped blocks' (D-Day's block 13: 29,228 entries, 9,853 nodes):
    the root's left side the far-view list (every item but road pieces, which the shipped maps never list for far
    view: 0 of 10,505), its right side every item, each list a search tree (_subtree) over the items' `boxes` (in the
    block's coordinates; none: each the whole block), so the game finds the items of a cell it walks without going
    through all of them. The root and the full list's nodes over a road piece or a placed block carry the road mark,
    so the game's road pass reaches road pieces in it, or in a block it places (a superset only costs culling);
    whether that shows them on screen isn't known (T12). `levels` (one per item, NewObject.levels; 0 = every level):
    an item whose mask has no far bit stays off the far-view list, and the full list holds each mask's items under
    nodes of that mask, as the shipped blocks' own stickers, low plants and stones are (the deepest node's mask is
    the one the dresser goes by: their middle-only and close-only items never drawn from far)."""
    offsets, pos = [], 4
    for it in items:
        offsets.append(pos)
        pos += len(it)
    boxes = boxes or [tuple(box)] * len(items)
    levels = levels or [0] * len(items)
    far_e, far_n = _subtree([(b, o, False) for it, o, b, lv in zip(items, offsets, boxes, levels)
                             if not _is_road(it) and (not lv or lv & 0x08)], box, 0, 0x08)
    groups: dict[int, list] = {}  # the full list by mask: the default (every level but far) first
    for it, o, b, lv in zip(items, offsets, boxes, levels):
        mask = ALL_TIERS & ~0x08 if not lv else lv & ALL_TIERS & ~0x08
        groups.setdefault(mask, []).append((b, o, not struct.unpack_from("<I", it)[0] >> 31))  # a road piece or block
    full_e, full_n = _by_mask(sorted(groups.items(), key=lambda kv: -kv[0]), box, len(far_e))
    entries = far_e + full_e  # the far-view items first, then all of them
    if len(entries) > 0xFFFF:
        raise SceneryEditError("too many objects for one new block: a tree node splits its entries at a 16-bit index")
    nodes = [[((ALL_TIERS | ROAD_TIER) << 20) | ((1 + len(far_n)) << 2), len(far_e), 0xFF, 0]] + far_n + full_n
    head = struct.pack("<II4f", 0x80000000 | len(entries), len(nodes), *box) + BLOCK_TAIL
    out = (head + struct.pack(f"<{len(entries)}I", *entries) + b"".join(struct.pack("<IHBB", *n) for n in nodes)
           + struct.pack("<I", FILLER) + b"".join(items))
    return out + b"\0" * (-len(out) % BLOCK_ALIGN)


def _by_mask(groups: list[tuple[int, list]], box: tuple, lo: int) -> tuple[list[int], list[list[int]]]:
    """The full list's tree over `groups` [(mask, things as _subtree takes them)]: one group is its own search tree;
    more are joined by nodes whose two sides each span the whole box (shares 255 and 0), the first group on the left
    and the rest on the right, each node's mask all of its groups' together (the deepest node's is the one that
    counts). Returns (entries from index `lo`, nodes) as _subtree does."""
    mask, things = groups[0]
    if len(groups) == 1:
        return _subtree(things, box, lo, mask)
    left_e, left_n = _subtree(things, box, lo, mask)
    right_e, right_n = _by_mask(groups[1:], box, lo + len(left_e))
    every = 0
    road = False
    for m, ts in groups:
        every |= m
        road = road or any(t[2] for t in ts)
    if 1 + len(left_n) >= 1 << 18:
        raise SceneryEditError("too many objects for one new block: its tree's nodes are too far apart")
    word = ((every | (ROAD_TIER if road else 0)) << 20) | ((1 + len(left_n)) << 2)  # axis 0, both sides whole
    return left_e + right_e, [[word, lo + len(left_e), 255, 0]] + left_n + right_n


def _share(v: float, a0: float, ext: float, up: bool) -> int:
    """`v` as a share /255 of [a0, a0 + ext], as a tree node keeps its sides' edges: rounded outward (up for a side's
    top, down for its bottom), within 0 to 255."""
    if ext <= 0:
        return 255 if up else 0
    s = (v - a0) / ext * 255
    return min(255, max(0, math.ceil(s) if up else math.floor(s)))


def _sides(node, box: tuple) -> tuple[tuple, tuple]:
    """A tree node's left and right sides' boxes, from its own `box` (as _leaf_boxes reads them)."""
    w, _split, b1, b2 = node[:4]
    x0, y0, x1, y1 = box
    if w & 3 == 0:
        return (x0, y0, x0 + b1 / 255 * (x1 - x0), y1), (x0 + b2 / 255 * (x1 - x0), y0, x1, y1)
    return (x0, y0, x1, y0 + b1 / 255 * (y1 - y0)), (x0, y0 + b2 / 255 * (y1 - y0), x1, y1)


def _subtree(things: list, box: tuple, lo: int, mask: int) -> tuple[list[int], list[list[int]]]:
    """A search tree over `things` [(its box, its entry, whether the road pass needs it)] in `box`, as the shipped
    blocks' are: each node splits its things in two halves along the longer spread of their middles, its sides' boxes
    (shares /255 of its own, rounded outward) holding each half, down to leaves of LEAF_MOST or fewer. Returns (the
    entries in the order the leaves list them, from entry index `lo`; the nodes as [word, split, b1, b2], the first
    its root, each with the LOD mask `mask` and the road mark when a thing under it needs the road pass)."""
    entries: list[int] = []
    nodes: list = []

    def node(part, nbox, at):
        k = len(nodes)
        nodes.append(None)
        mids = [((t[0][0] + t[0][2]) / 2, (t[0][1] + t[0][3]) / 2) for t in part]
        spread = [max((m[a] for m in mids), default=0.0) - min((m[a] for m in mids), default=0.0) for a in (0, 1)]
        axis = 0 if spread[0] >= spread[1] else 1
        part = sorted(part, key=lambda t: t[0][axis] + t[0][axis + 2])
        left, right = part[:len(part) // 2], part[len(part) // 2:]
        a0, ext = (nbox[0], nbox[2] - nbox[0]) if axis == 0 else (nbox[1], nbox[3] - nbox[1])
        b1 = _share(max((t[0][axis + 2] for t in left), default=a0), a0, ext, up=True)
        b2 = _share(min((t[0][axis] for t in right), default=a0 + ext), a0, ext, up=False)
        word = ((mask | (ROAD_TIER if any(t[2] for t in part) else 0)) << 20) | axis
        lbox, rbox = _sides([word, 0, b1, b2], nbox)
        split = at + len(left)
        if len(left) <= LEAF_MOST:
            word |= 0x40000000
            entries.extend(t[1] for t in left)
        else:
            node(left, lbox, at)
        if len(right) <= LEAF_MOST:
            word |= 0x80000000
            entries.extend(t[1] for t in right)
        else:
            if len(nodes) - k >= 1 << 18:
                raise SceneryEditError("too many objects for one new block: its tree's nodes are too far apart")
            word |= (len(nodes) - k) << 2
            node(right, rbox, split)
        nodes[k] = [word, split, b1, b2]

    node(things, tuple(box), lo)
    return entries, nodes


def _chunks(things: list, most: int | None = None) -> list[list]:
    """`things` in parts of at most `most` (BLOCK_MOST), neighbours together: halved along the longer spread of their
    places."""
    most = BLOCK_MOST if most is None else most
    if len(things) <= most:
        return [things]
    spread_x = max(p.x for p in things) - min(p.x for p in things)
    spread_y = max(p.y for p in things) - min(p.y for p in things)
    part = sorted(things, key=(lambda p: p.x) if spread_x >= spread_y else (lambda p: p.y))
    return _chunks(part[:len(part) // 2], most) + _chunks(part[len(part) // 2:], most)


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
    reference). Each object goes on the reference whose boxes in the top block's tree hold it (_carriers), and the
    grids' cells under the new objects are marked as holding something (_grids_hold). Types must be ones the map
    already uses (in its name table). `objects` may hold RoadPiece too (a new road's stickers, in the map's own Route
    style; a map without one gets none): they're filed with the map's own pieces (file_roads); a piece no leaf holds
    goes in a block of its own, on the reference whose box holds it, and the tree's nodes down to it get the road
    mark. Returns (new file, notes)."""
    if not objects:
        return bytes(data), []
    notes = []
    pieces = [o for o in objects if isinstance(o, RoadPiece)]
    objects = [o for o in objects if not isinstance(o, RoadPiece)]
    if pieces and _road_style(Scenery(data)) is None:
        pieces = []
        notes.append("this map has no road stickers to copy: its new roads show from afar only")
    if pieces:
        data, pieces, more = file_roads(data, pieces)
        notes += more
    outside: list = []
    for things, roads in ((objects, False), (pieces, True)):
        if not things:
            continue
        if not _far_children(Scenery(data)):  # (no shipped map: all 32 list blocks for far view)
            for group in _groups(things):
                data, more = _add_block(data, group)
                notes += more
            continue
        groups, lost, short = _carriers(Scenery(data), things, roads)
        if (lost or short) and not roads:
            # in open ground, or where only blocks listed at fewer levels than they ask lie (a blank map's erased
            # ground: its big sticker blocks are listed middle-only, 0x10, so copied crops and stones there were
            # never drawn; the blank farm, 2026-10-15): one carrier listed at their levels, its box in the top
            # block's tree widened over them, as the map hangs its own crops on blocks listed at every level
            # (2026-10-15: one carrier 5.6 km off took all 30,183 in four blocks nested one in the next, and none was
            # drawn; field 7's 1,637 in one block on a carrier 218 m off were.) In parts of neighbours of at most
            # WIDEN_MOST, each on its own carrier, the nearest one listed at the part's levels (and for far view when
            # one of them asks for it), so no new block wraps another.
            move = list({id(p): p for p in lost + short}.values())
            lost_ids = {id(p) for p in lost}
            placed: dict[int, list] = {}
            # those asking to be drawn from far (trees: a far-listed carrier, often farther off) in parts of their
            # own, so the rest (crops, stones, low plants) take the nearest carriers listed at their levels
            asks_far = [p for p in move if getattr(p, "levels", 0) & 0x08]
            rest = [p for p in move if not getattr(p, "levels", 0) & 0x08]
            parts = (_chunks(rest, WIDEN_MOST) if rest else []) + (_chunks(asks_far, WIDEN_MOST) if asks_far else [])
            for part in parts:
                levels = 0
                for p in part:
                    levels |= _needs(p)
                far = any(getattr(p, "levels", 0) & 0x08 for p in part)
                data, at, more = _widen(Scenery(data), data, part, levels, far, avoid=set(placed))
                if at is None and far:   # no far-listed reference listed at their levels: drawn from middle in
                    data, at, more = _widen(Scenery(data), data, part, levels, avoid=set(placed))
                if at is None and any(id(p) in lost_ids for p in part):  # none listed at their levels: the open ground's
                    data, at, more = _widen(Scenery(data), data, part, avoid=set(placed))   # on any
                notes += more
                if at is not None:
                    placed.setdefault(at, []).extend(part)
            if placed:
                gone, kept = {id(p) for ps in placed.values() for p in ps}, {}
                for a, group in groups:
                    kept.setdefault(a, []).extend(p for p in group if id(p) not in gone)
                for a, ps in placed.items():
                    kept.setdefault(a, []).extend(ps)
                groups = [(a, g) for a, g in kept.items() if g]
                lost = [p for p in lost if id(p) not in gone]
                short = [p for p in short if id(p) not in gone]
        if short:
            notes.append(f"{len(short)} new object(s) hang on a block the map lists at fewer detail levels than they "
                         f"ask (no block listed at theirs holds their spot): drawn at those levels only")
        outside += lost
        for at, group in groups:
            for part in _chunks(group):  # a carrier given more than one block holds: one wrapping the next
                sc = Scenery(data)  # the top block's items and tree stay where they are: `at` still names the carrier
                data, more = _wrap(sc, data, part, _far_children(sc),
                                   next(it for it in sc.blocks[0].items if it.at == at))
                notes += more
    if objects:
        data, cells = _grids_hold(data, [(o.x, o.y) for o in objects])
        if cells:
            notes.append(f"{cells} cell(s) of the scenery's grids marked as holding something, so the game draws "
                         f"the new objects there")
    if outside:
        where = ", ".join(f"({p.x:.0f}, {p.y:.0f})" for p in outside[:5]) + (", ..." if len(outside) > 5 else "")
        notes.append(f"{len(outside)} new object(s) or road piece(s) lie in no box of the map's draw tree, too far "
                     f"from the map's own scenery: they went with the nearest block and may not show at every "
                     f"distance (move them nearer a village, a farm or a wood): {where}")
    return data, notes


def add_names(data: bytes, new: list[str]) -> bytes:
    """The scenery file with scenery type names added to its name table (each with flag 1, an object type, as
    every name but Route has), before the empty name that ends it; the tables after it move with it. Names the
    table has already are left alone. For a mod's types the map doesn't use yet, such as a visibility copy
    (rusemod.visibility)."""
    sc = Scenery(data)
    have = set(sc.names)
    new = [n for n in dict.fromkeys(new) if n not in have]
    if not new:
        return bytes(data)
    f = list(sc.fields)
    names_off, names_len, flags_off, flags_n = f[6], f[7], f[4], f[5]
    if not (names_off + names_len == flags_off and flags_off + flags_n <= f[8] <= f[10] <= f[12] <= f[20]):
        raise SceneryError("the scenery file's tables aren't in the order this writer knows")
    end = names_off + names_len - 4  # the empty name that ends the table: its 4-byte length
    if struct.unpack_from("<I", data, end)[0] != 0:
        raise SceneryError("the scenery file's name table doesn't end with an empty name")
    added = b"".join(struct.pack("<I", len(n.encode("latin-1"))) + n.encode("latin-1") for n in new)
    out = bytearray(data[:end]) + added + data[end:flags_off + flags_n] + bytes([1] * len(new)) + data[flags_off + flags_n:]
    grow = len(added)
    f[7] = names_len + grow
    f[4] = flags_off + grow
    f[5] = flags_n + len(new)
    for k in (8, 10, 12, 20, 22, 24):
        f[k] += grow + len(new)
    struct.pack_into("<26I", out, 20, *f)
    out[:16] = hashlib.md5(bytes(out[16:])).digest()
    return bytes(out)


SECTION_PART = 100   # places one new block lists at most (add_sections): neighbours, about 300 m across for 30 m
                     # sections, each block hung on a carrier of its own as add_objects hangs WIDEN_MOST objects


@dataclass(frozen=True)
class _Place:
    section: int   # which section (its index in add_sections' list)
    x: float
    y: float
    turn: float


def _placed(x: float, y: float, turn: float) -> tuple:
    """A section's place: turned `turn` degrees (as NewObject.turn) round its middle, that middle at (x, y)."""
    t = math.radians(turn)
    c, s = math.cos(t), math.sin(t)
    return (c, -s, 0.0, x, s, c, 0.0, y, 0.0, 0.0, 1.0, 0.0)


def _box_through(box: tuple, m: tuple) -> tuple:
    """A box (x0, y0, x1, y1) through transform `m`: the box round its four corners."""
    xs, ys = [], []
    for x, y in ((box[0], box[1]), (box[2], box[1]), (box[0], box[3]), (box[2], box[3])):
        xs.append(m[0] * x + m[1] * y + m[3])
        ys.append(m[4] * x + m[5] * y + m[7])
    return min(xs), min(ys), max(xs), max(ys)


def add_sections(data: bytes, sections: list[tuple[str, list, tuple]]) -> tuple[bytes, list[str]]:
    """The scenery file with each section ((name, its NewObjects about its middle (0, 0), its places ((x, y, turn),
    ...)): SectionArea, copy_objects) written ONCE, as a block of its own, and placed at each of its places by a
    reference to that block, as the shipped maps place their landscape tiles. The references go in new blocks of at
    most SECTION_PART neighbouring places each, each new block wrapping a reference of the top block (it places the
    old block where it was, then the sections' references), as add_objects wraps one for new objects in open ground:
    the reference listed at the sections' levels nearest them, a free one while there is one, its box in the draw
    tree widened over them (_widen). New blocks go right after the top block (a reference must point forward): the
    wrapping blocks, then the sections' own; every later reference moves by their size. The grids' cells under the
    placed sections are marked as holding something (_grids_hold). Types must be ones the map already uses. Returns
    (new file, notes)."""
    sections = [(n, list(objs), tuple(places)) for n, objs, places in sections if objs and places]
    if not sections:
        return bytes(data), []
    sc = Scenery(data)
    index = {name: i for i, name in enumerate(sc.names[:len(sc.flags)]) if sc.flags[i] == 1}
    words: dict[int, int] = {}
    for b in sc.blocks:
        for it in b.items:
            if it.kind == "object":
                words.setdefault(it.symbol, it.word & WORD_KEEP)
    own: list[bytes] = []   # each section's block
    made: list[tuple] = []  # each section's (box, levels it asks but far, whether it asks far, its points for the grids)
    step = GRID_CELL[2] / 4
    for name, objects, _places in sections:
        if len(objects) > BLOCK_MOST:
            raise SceneryEditError(f"section {name}: {len(objects):,} objects, more than one block holds "
                                   f"({BLOCK_MOST:,}): copy a smaller square")
        items, boxes, levels = [], [], []
        need, far = 0, False
        for o in objects:
            sym = index.get(o.type)
            if sym is None:
                raise SceneryEditError(f"section {name}: {o.type} isn't used on this map, so the map can't take it "
                                       f"(only types its scenery already lists)")
            if not 0.05 <= o.size <= 50:
                raise SceneryEditError(f"section {name}: {o.type}: size {o.size} is outside 0.05 to 50")
            m = o.matrix()
            kind, tdata = encode_transform(m)
            items.append(struct.pack("<I", 0x80000000 | words.get(sym, 0) | (sym << 4) | kind) + tdata)
            pad = MARGIN * o.size * max(1.0, o.stretch)
            boxes.append((m[3] - pad, m[7] - pad, m[3] + pad, m[7] + pad))
            levels.append(o.levels)
            need |= _needs(o)
            far = far or not o.levels or bool(o.levels & 0x08)
        box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
        own.append(_new_block(items, box, boxes, levels))
        points = sorted({(round(o.x / step) * step, round(o.y / step) * step) for o in objects})
        made.append((box, need, far, points))
    places = [_Place(k, x, y, t) for k, (_n, _o, ps) in enumerate(sections) for x, y, t in ps]
    notes: list[str] = []
    hung: dict[int, list[_Place]] = {}   # the top block's reference's `at` -> the places its new block lists
    widened = 0
    for part in _chunks(places, SECTION_PART):
        need, far = 0, False
        corners = []
        for p in part:
            box, n, f, _pts = made[p.section]
            need, far = need | n, far or f
            x0, y0, x1, y1 = _box_through(box, _placed(p.x, p.y, p.turn))
            corners += [NewObject("", x, y, levels=n) for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
        data, at, more = _widen(Scenery(data), data, corners, need, far, avoid=set(hung))
        if at is None and far:   # no far-listed reference listed at their levels: drawn from middle in
            data, at, more = _widen(Scenery(data), data, corners, need, avoid=set(hung))
        if at is None:
            data, at, more = _widen(Scenery(data), data, corners, avoid=set(hung))
        if at is None:
            raise SceneryEditError("the map's top block has no draw tree to hang the sections on")
        widened += bool(more)
        hung.setdefault(at, []).extend(part)
    sc = Scenery(data)
    top = sc.blocks[0]
    ins = top.offset + len(top.raw)  # the new blocks go right after the top block
    if len(sc.blocks) > 1 and sc.blocks[1].offset != ins:
        raise SceneryError("the scenery file's blocks aren't in the order this writer knows")
    by_at = {it.at: it for it in top.items}

    def wrapper(at: int, part: list[_Place], shift: int, own_at: list[int]) -> bytes:
        """The new block wrapping reference `at`: the old block where it was (the reference to the new block keeps
        the old one's transform), then a reference to each place's section (`own_at`: where each section's block
        starts; `shift`: how far the old blocks move)."""
        carrier = by_at[at]
        inner = sc.block_at(carrier.child_offset)
        to_local = _inverse(carrier.matrix())
        items = [struct.pack("<I", link_word(carrier.word & 0xFF000000, carrier.child_offset + shift) | T_IDENTITY)]
        boxes, levels = [tuple(inner.bbox)], [0]
        for p in part:
            box, n, f, _pts = made[p.section]
            m = compose(to_local, _placed(p.x, p.y, p.turn))
            kind, tdata = encode_transform(m)
            items.append(struct.pack("<I", link_word(0, own_at[p.section]) | kind) + tdata)
            boxes.append(_box_through(box, m))
            levels.append(n | (0x08 if f else 0))
        whole = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes),
                 max(b[3] for b in boxes))
        return _new_block(items, whole, boxes, levels)
    ats = list(hung)
    sizes = [len(wrapper(at, hung[at], 0, [0] * len(own))) for at in ats]   # (their sizes don't hang on offsets)
    wrap_at = [ins + sum(sizes[:j]) for j in range(len(ats))]
    own_at = [ins + sum(sizes) + sum(len(b) for b in own[:k]) for k in range(len(own))]
    shift = sum(sizes) + sum(len(b) for b in own)
    if sc.fields[3] + shift > DATA_LIMIT:
        raise SceneryEditError(f"the map's scenery is too big for the sections ({shift:,} bytes more) to be "
                               f"referenced")
    news = [wrapper(at, hung[at], shift, own_at) for at in ats]
    if [len(b) for b in news] != sizes:
        raise SceneryError("a new block came out a different size than measured")
    goes_to = dict(zip(ats, wrap_at))
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
            if b.index == 0 and it.at in goes_to:
                target = goes_to[it.at]
            else:
                target = it.child_offset + shift if it.child_offset >= ins else it.child_offset
            struct.pack_into("<I", raw, b.items_start + it.at, link_word(it.word, target))
        parts.append(bytes(raw))
        if b.index == 0:
            parts += news + own
    body_data = b"".join(parts)
    if len(body_data) != data_len + shift:
        raise SceneryError("the scenery file's blocks don't fill its data exactly")
    added = len(news) + len(own)
    end = data_off + data_len
    for k in (4, 6, 8, 10, 12, 20, 22, 24):  # the tables after the data move by the table's new entries and blocks
        if f[k] < end:
            raise SceneryError("the scenery file's tables aren't in the order this writer knows")
        f[k] += 4 * added + shift
    f[1], f[2], f[3] = tab_n + added, data_off + 4 * added, data_len + shift
    table = list(struct.unpack_from(f"<{tab_n}I", data, tab_off))  # the offsets, then the end marker
    table = [table[0]] + wrap_at + own_at + [v + shift for v in table[1:]]
    body = VERSION + struct.pack("<26I", *f) + struct.pack(f"<{len(table)}I", *table) + body_data + data[end:]
    out = hashlib.md5(body).digest() + body
    points = []
    for p in places:
        m = _placed(p.x, p.y, p.turn)
        points += [(m[0] * x + m[1] * y + m[3], m[4] * x + m[5] * y + m[7]) for x, y in made[p.section][3]]
    out, cells = _grids_hold(out, points)
    total = sum(len(objs) for _n, objs, _p in sections)
    notes.append(f"{len(sections)} section(s) ({total:,} objects) written once and placed {len(places):,} times "
                 f"({sum(len(objs) * len(ps) for _n, objs, ps in sections):,} objects on the map) by "
                 f"{len(news)} new block(s), each hung on a block of the map's draw tree"
                 + (f" ({widened} of their boxes widened to reach them)" if widened else ""))
    if cells:
        notes.append(f"{cells} cell(s) of the scenery's grids marked as holding something, so the game draws the "
                     f"sections there")
    return out, notes


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


# --- erasing the map's own scenery (a mod's [[erase]] areas in scenery.toml; docs/MOD_FORMAT.md §8) ---
ERASE_GROUPS = ("vegetation", "prop", "decal", "building")  # what an erase area may name in `what`
ERASE_DEFAULT = ("vegetation", "prop")                        # trees and props, unless the area says otherwise
ERASE_MAX = 4000000.0  # map units an erase area's radius may reach: any map, whole (M04_Cotentin is 3,932,160 wide); a
                       # whole-map erase takes seconds (erase_plan's bulk) and fits (erase_objects shares copies)
DATA_LIMIT = 0xFFFFFC  # a reference holds a block's offset in 24 bits (4-byte steps): the blocks' data stops there
BLOCK_ALIGN = 4        # a new block's size is padded to a multiple of this (4: none; the shipped blocks are padded to 16)


def link_offset(word: int) -> int:
    """Where the block a reference (a child item's word) points at starts, from the data's start."""
    return word & 0xFFFFFC


def link_word(word: int, offset: int) -> int:
    """Reference `word` pointed at the block starting at `offset` (its other bits kept)."""
    if offset & ~0xFFFFFC:
        raise SceneryEditError(f"the map's scenery is too big for a block {offset:,} bytes in to be referenced")
    return (word & ~0x00FFFFFC) | offset


@dataclass(frozen=True)
class EraseArea:
    """A circle whose scenery the build takes off the map: the groups in `what` (never a bridge) and the types named
    in `types` (any kind, bridges too). Road pieces and level-design markers stay. `keep_ground`: the ground's cover
    and movement stay even when it takes trees (a new road's own clearing, road_clearing), unlike a mod's erase area,
    which clears a wood (build.cleared_woods)."""
    x: float
    y: float
    radius: float
    what: tuple = ERASE_DEFAULT
    types: tuple = ()
    keep_ground: bool = False
    shape: str = "round"   # round, square (sides along dx, dy, `radius` from its middle to each side) or line (to x2,
    dx: float = 1.0        # y2, `radius` either side): rusemod.brush Footprint
    dy: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    by_size: bool = False  # an object goes when any of it reaches in (its type's reach times its size: erase_plan's
                           # `sizes`), not only its middle: Map Paint's clearing (a sticker 20 m across centred outside
                           # a painted patch still covers its edge up close; seen in the game, TESTS.md T26)
    mask: object = field(default=None, compare=False)  # with by_size: `mask(x, y, reach)` says whether an object
                           # reaching that far from (x, y) goes, inside the shape (the filled riverbeds of a reshaped
                           # map: rusemod.mend.Filled.touches); the shape only narrows the search
    opens: float = 0.0     # how far round its middle the ground opens to every unit and loses its blocked mark,
                           # though `what` names no group: one of the map's own buildings taken away or moved ([[own]],
                           # OwnEdit), its own reach (build.cleared_woods)

    def footprint(self):
        """Its shape (rusemod.brush.Footprint), made once: an erase over a big map asks it millions of times."""
        f = self.__dict__.get("_foot")
        if f is None:
            from .brush import Footprint
            if self.shape == "line":
                f = Footprint("line", self.x, self.y, self.radius, x2=self.x2, y2=self.y2)
            elif self.shape == "square":
                f = Footprint("square", self.x, self.y, self.radius, self.dx, self.dy)
            else:
                f = Footprint("round", self.x, self.y, self.radius)
            object.__setattr__(self, "_foot", f)
        return f

    def covers(self, points) -> bool:
        """Whether every one of `points` ((x, y) pairs) lies inside it: a block's four corners (each shape is convex, so
        its corners inside means all of it is)."""
        if self.shape == "round":
            r2 = self.radius * self.radius
            return all((x - self.x) ** 2 + (y - self.y) ** 2 <= r2 for x, y in points)
        f = self.footprint()
        return all(f.t2(x, y) <= 1.0 for x, y in points)

    def box(self) -> tuple[float, float, float, float]:
        """x min, y min, x max, y max."""
        bx0, bx1, by0, by1 = self.footprint().box()
        return bx0, by0, bx1, by1

    def contains(self, x: float, y: float) -> bool:
        if self.shape == "round":
            return (x - self.x) ** 2 + (y - self.y) ** 2 <= self.radius ** 2
        return self.footprint().t2(x, y) <= 1.0

    def meets(self, x0: float, y0: float, x1: float, y1: float) -> bool:
        if self.shape == "round":
            return max(x0 - self.x, 0.0, self.x - x1) ** 2 + max(y0 - self.y, 0.0, self.y - y1) ** 2 <= self.radius ** 2
        return self.footprint().meets(x0, y0, x1, y1)


@dataclass
class _Cut:
    """What an erase takes out of one placement of a block: its items (by offset) that go, and the placements under
    it that change."""
    block: int
    removed: set
    changes: dict                                # child item's offset -> _Cut
    gone: dict = field(default_factory=dict)     # name index -> objects erased under this placement
    empty: bool = False                          # nothing would be left in it: its reference goes instead


def _placed_items(sc: Scenery) -> tuple[list, list]:
    """Each block's transforms read once, for erase_plan: per block, its objects (at, name index, x, y, z, and its
    transform's first column: its size) and its children holding objects (at, -1, the child's block, its transform),
    in order; and per block the box (x0, y0, x1, y1) in its own coordinates of every object under it, children
    included, or None for a block with none (children are stored after their parents: one pass from the end)."""
    items: list = [None] * len(sc.blocks)
    boxes: list = [None] * len(sc.blocks)
    for b in reversed(sc.blocks):
        out, xs, ys = [], [], []
        for it in b.items:
            if it.kind == "object":
                m = it.matrix()
                out.append((it.at, it.symbol, m[3], m[7], m[11], m[0], m[4], m[8]))
                xs.append(m[3])
                ys.append(m[7])
            elif it.kind == "child":
                j = sc._by_offset[it.child_offset]
                cb = boxes[j]
                if cb is not None:
                    m = it.matrix()
                    out.append((it.at, -1, j, m))
                    for x, y in ((cb[0], cb[1]), (cb[2], cb[1]), (cb[0], cb[3]), (cb[2], cb[3])):
                        xs.append(m[0] * x + m[1] * y + m[3])
                        ys.append(m[4] * x + m[5] * y + m[7])
        items[b.index] = out
        if xs:
            boxes[b.index] = (min(xs), min(ys), max(xs), max(ys))
    return items, boxes


class _AreaGrid:
    """The (area, names) pairs bucketed on a grid of `cell` map units by their circles' boxes, so a placement far
    from most areas looks at only the few near it (a new road's clearing makes thousands of small circles: 2,141 for
    the owner's D-Day roads, which took 25 minutes when every placement was tested against every circle). An area
    over more than BIG cells is kept with the span of cells it covers instead (Map Paint's clearing by size reaches
    a kilometre past its strokes: 136 of those filled 2.3 million cells on M04_Cotentin); a query finds it the same."""
    BIG = 256

    def __init__(self, pairs: list, cell: float = 16000.0):
        self.cell, self.cells, self.big = cell, {}, []
        for k, pair in enumerate(pairs):
            ax0, ay0, ax1, ay1 = pair[0].box()
            gx0, gx1 = int(ax0 // cell), int(ax1 // cell)
            if gx1 < gx0:
                continue
            gy0, gy1 = int(ay0 // cell), int(ay1 // cell)
            if gy1 < gy0:
                continue
            if (gx1 - gx0 + 1) * (gy1 - gy0 + 1) > self.BIG:
                self.big.append((k, gx0, gx1, gy0, gy1))
                continue
            for gx in range(gx0, gx1 + 1):
                for gy in range(gy0, gy1 + 1):
                    self.cells.setdefault((gx, gy), []).append(k)
        self.pairs = pairs

    def query(self, x0: float, y0: float, x1: float, y1: float) -> list:
        c = self.cell
        if (x1 - x0) * (y1 - y0) > 400 * c * c:  # a huge box (the top block): the cells would cost more than the list
            return self.pairs
        gx0, gx1 = int(x0 // c), int(x1 // c)
        if gx1 < gx0:
            return []
        gy0, gy1 = int(y0 // c), int(y1 // c)
        if gy1 < gy0:
            return []
        found = set()
        for gx in range(gx0, gx1 + 1):
            for gy in range(gy0, gy1 + 1):
                found.update(self.cells.get((gx, gy), ()))
        found.update(k for k, ax0, ax1, ay0, ay1 in self.big if ax0 <= gx1 and gx0 <= ax1 and ay0 <= gy1 and gy0 <= ay1)
        return [self.pairs[k] for k in sorted(found)]


SIZE_MOST = 8.0  # the largest size an erase by size allows for when it narrows its search (Blitz places none past 5.3)


# An erase asks its areas about millions of objects and placements (most of M04_Cotentin: 15 million objects in
# 750,000 placements), so each area's questions are made once as small functions: the same sums in the same order as
# EraseArea.contains and .meets and rusemod.brush.Footprint.t2 and .meets, with what is the same for every question
# (a square's corners and sides, a line's run, a radius squared) worked out once. The answers are the same numbers.

def _t2_test(f):
    """Footprint `f`'s t2(px, py) (rusemod.brush.Footprint.t2)."""
    fx, fy, r = f.x, f.y, f.r
    if f.shape == "square":
        dx, dy = f.dx, f.dy
        n = math.sqrt(dx * dx + dy * dy) or 1.0

        def t2(px, py):
            ox, oy = px - fx, py - fy
            u = abs(ox * dx + oy * dy) / n
            v = abs(oy * dx - ox * dy) / n
            return ((u if u > v else v) / r) ** 2
        return t2
    rr = r * r
    if f.shape == "line":
        sx, sy = f.x2 - fx, f.y2 - fy
        len2 = sx * sx + sy * sy

        def t2(px, py):
            ox, oy = px - fx, py - fy
            t = 0.0
            if len2 > 0.0:
                t = (ox * sx + oy * sy) / len2
                t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
            qx, qy = ox - sx * t, oy - sy * t
            return (qx * qx + qy * qy) / rr
        return t2

    def t2(px, py):
        ox, oy = px - fx, py - fy
        return (ox * ox + oy * oy) / rr
    return t2


def _takes_test(a: EraseArea, by_size: bool) -> tuple:
    """(whether it needs the object's reach, test): whether area `a` takes an object at (x, y), test(x, y), as
    a.contains says; or, reaching `rs` from there, test(x, y, rs), for an area by size (`by_size`: its footprint's t2
    grown by the reach) or with a mask (the mask itself)."""
    if a.mask is not None:
        return True, a.mask
    if by_size:
        t2, ar = _t2_test(a.footprint()), a.radius

        def takes(x, y, rs):
            r = ar + rs  # (how far out / r)² grown by the object's reach
            return t2(x, y) * ar * ar <= r * r
        return True, takes
    if a.shape == "round":
        try:
            ax, ay, rr = a.x, a.y, a.radius ** 2
        except OverflowError:  # a radius no map holds: asked as before, so it fails where it did
            return False, a.contains
        return False, lambda x, y: (x - ax) ** 2 + (y - ay) ** 2 <= rr
    t2 = _t2_test(a.footprint())
    return False, lambda x, y: t2(x, y) <= 1.0


def _meets_test(a: EraseArea):
    """a.meets(x0, y0, x1, y1): whether area `a` reaches into the box."""
    if a.shape == "round":
        try:
            ax, ay, rr = a.x, a.y, a.radius ** 2
        except OverflowError:
            return a.meets
        return lambda x0, y0, x1, y1: max(x0 - ax, 0.0, ax - x1) ** 2 + max(y0 - ay, 0.0, ay - y1) ** 2 <= rr
    f = a.footprint()
    if f.shape not in ("square", "line"):
        return a.meets
    bx0, bx1, by0, by1 = f.box()
    if f.shape == "square":
        cs = f.corners()
        n = math.sqrt(f.dx * f.dx + f.dy * f.dy) or 1.0
        sides = []
        for ux, uy in ((f.dx / n, f.dy / n), (-f.dy / n, f.dx / n)):
            ps = [cx * ux + cy * uy for cx, cy in cs]
            sides.append((ux, uy, min(ps), max(ps)))

        def meets(x0, y0, x1, y1):
            if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
                return False
            for ux, uy, lo, hi in sides:
                qs = [px * ux + py * uy for px in (x0, x1) for py in (y0, y1)]
                if max(qs) < lo or min(qs) > hi:
                    return False
            return True
        return meets
    ax, ay, bx, by, rr = f.x, f.y, f.x2, f.y2, f.r * f.r
    sx, sy = bx - ax, by - ay
    len2 = sx * sx + sy * sy

    def sign(v):
        return (v > 0) - (v < 0)

    def crosses(r0, r1, s0, s1, d1, d2):  # brush._segments_cross(the line, the box's side from r to s)
        if d1 == d2 or d1 == 0 or d2 == 0:
            return False
        d3 = sign((s0 - r0) * (ay - r1) - (s1 - r1) * (ax - r0))
        d4 = sign((s0 - r0) * (by - r1) - (s1 - r1) * (bx - r0))
        return d3 != d4 and d3 != 0 and d4 != 0

    def apart2(px, py):  # brush._point_segment2
        t = 0.0 if len2 == 0.0 else max(0.0, min(1.0, ((px - ax) * sx + (py - ay) * sy) / len2))
        return (px - ax - sx * t) ** 2 + (py - ay - sy * t) ** 2

    def meets(x0, y0, x1, y1):  # brush._segment_box_distance2 of the line and the box, within its radius
        if bx1 < x0 or bx0 > x1 or by1 < y0 or by0 > y1:
            return False
        if x0 <= ax <= x1 and y0 <= ay <= y1 or x0 <= bx <= x1 and y0 <= by <= y1:
            return 0.0 <= rr
        d00, d10 = sign(sx * (y0 - ay) - sy * (x0 - ax)), sign(sx * (y0 - ay) - sy * (x1 - ax))
        d11, d01 = sign(sx * (y1 - ay) - sy * (x1 - ax)), sign(sx * (y1 - ay) - sy * (x0 - ax))
        if (crosses(x0, y0, x1, y0, d00, d10) or crosses(x1, y0, x1, y1, d10, d11)
                or crosses(x1, y1, x0, y1, d11, d01) or crosses(x0, y1, x0, y0, d01, d00)):
            return 0.0 <= rr
        best = min(apart2(x0, y0), apart2(x0, y1), apart2(x1, y0), apart2(x1, y1))
        for px, py in ((ax, ay), (bx, by)):
            nx, ny = min(max(px, x0), x1), min(max(py, y0), y1)
            best = min(best, (nx - px) ** 2 + (ny - py) ** 2)
        return best <= rr
    return meets


_FAR = 1e100  # map units no map comes near: a placement's corners inside it, a tame area's covers() can't fail
_MAP = 1e12   # map units past any map (M04_Cotentin is 3,932,160 wide): erase_plan's sure areas work within it


def _tame_cover(a: EraseArea) -> bool:
    """Whether a.covers can't fail (raise) for corners within _FAR, whatever order it's asked in: its numbers finite
    and within _FAR (squaring them stays a float), and a radius well above 0 where it divides by it."""
    vals = (a.x, a.y, a.radius) + ((a.dx, a.dy) if a.shape == "square" else ()) \
        + ((a.x2, a.y2) if a.shape == "line" else ())
    if not all(type(v) in (int, float) and math.isfinite(v) and abs(v) <= _FAR for v in vals):
        return False
    return a.shape == "round" or a.radius >= 1e-40


def _sure_test(a: EraseArea, by_size: bool, reach: dict):
    """inside(x0, y0, x1, y1): whether a box lies inside area `a` (its four corners do: each shape is convex), for
    erase_plan's sure areas; None for an area that can't be one: with a mask, numbers past _MAP, a radius under a map
    unit, a square without a direction, or by size with a reach that isn't a plain distance."""
    if a.mask is not None or a.shape not in ("round", "square", "line"):
        return None
    if not all(type(v) in (int, float) and math.isfinite(v) and abs(v) <= _MAP
               for v in (a.x, a.y, a.radius, a.dx, a.dy, a.x2, a.y2)) or a.radius < 1.0:
        return None
    if a.shape == "square" and not 1e-12 <= a.dx * a.dx + a.dy * a.dy <= 1e24:
        return None
    if by_size and not all(type(v) in (int, float) and math.isfinite(v) and v >= 0.0 for v in reach.values()):
        return None
    t2 = _t2_test(a.footprint())
    return lambda x0, y0, x1, y1: t2(x0, y0) <= 1.0 and t2(x1, y0) <= 1.0 and t2(x0, y1) <= 1.0 and t2(x1, y1) <= 1.0


def _room(blocks: list, boxes: list) -> float | None:
    """How far inside an area a placement's box must lie for erase_plan to call the area sure for it (map units): a
    millionth of the farthest anything placed can be from the map's corner, and a unit more. That is far past what
    the sums can stray by (a few billionths of it at most), so every object under the box tests inside the area as
    surely as the box does. None when that bound passes _MAP, a number isn't finite, the blocks aren't stored
    parents first, a placement stretches things a million times, or they nest past 64 deep. `blocks`: per block,
    _placed_items."""
    n = len(blocks)
    # per block, over its placements: the most they stretch (the largest row sum of a transform's turning part), the
    # farthest they move it, how deep it nests
    stretch, move, deep = [0.0] * n, [0.0] * n, [0] * n
    stretch[0] = 1.0
    far = 0.0
    for bi, items in enumerate(blocks):
        own = max(map(abs, boxes[bi])) if boxes[bi] is not None else 0.0
        for e in items:
            if e[1] >= 0:
                if not math.isfinite(sum(map(abs, e[2:]))):
                    return None
                own = max(own, abs(e[2]), abs(e[3]), abs(e[4]))
                continue
            j, c = e[2], e[3]
            if j <= bi or not math.isfinite(sum(map(abs, c))):
                return None
            turn = max(abs(c[0]) + abs(c[1]) + abs(c[2]), abs(c[4]) + abs(c[5]) + abs(c[6]),
                       abs(c[8]) + abs(c[9]) + abs(c[10]))
            stretch[j] = max(stretch[j], stretch[bi] * turn)
            move[j] = max(move[j], stretch[bi] * max(abs(c[3]), abs(c[7]), abs(c[11])) + move[bi])
            deep[j] = max(deep[j], deep[bi] + 1)
            if not (stretch[j] <= 1e6 and move[j] <= _MAP) or deep[j] > 64:  # (an object's size stays a number)
                return None
        far = max(far, stretch[bi] * own + move[bi])
    return 1.0 + far * 1e-6 if math.isfinite(far) and far <= _MAP else None


def erase_plan(sc: Scenery, areas: list[EraseArea], kinds: dict[int, str], bridges=frozenset(),
               sizes: dict[str, float] | None = None, cancel=None) -> _Cut | None:
    """What erasing `areas` takes out, placement by placement from the top block down, or None for nothing. An object
    goes when its place lies in an area that may remove its kind: its group (`kinds`: name index -> group) is in the
    area's `what` and it isn't a bridge (`bridges`: name indexes), or its name is in the area's `types`. In an area
    `by_size`, an object also goes when its reach does (`sizes`: type name -> how far it reaches from its middle at
    size 1, map units; times the size it is placed at).

    A placement lying wholly inside one area, with no area meeting it that takes other names, loses every object of
    that area's names at once (bulk), worked out once per block: erasing most of a big map (the owner's whole-map erase
    on M04_Cotentin, 2026-10-04) no longer tests every object of every placement. And an area a placement lies inside
    with room to spare (_room) is sure for it and for everything under it, while they are placed flat (their x and y
    don't hang on their z, as the boxes take it): the objects of its names there go without a test, since each test
    would say so, and a placement whose every name is sure goes whole. The owner's 175 areas over most of M04_Cotentin
    (2026-10-04) took 3 minutes when every object was tested. `cancel()`, asked now and then, stops the plan with
    EraseCancelled when it says so."""
    roots = sc.roots()
    if roots != [0]:
        raise SceneryError("the scenery file's blocks aren't in the order this writer knows")
    reach = {s: sizes[n] for s, n in enumerate(sc.names[:len(sc.flags)]) if n in sizes} if sizes else {}
    most = max(reach.values(), default=0.0) * SIZE_MOST
    # (area as searched, the name indexes it takes, the area, whether its test needs the object's reach, its test,
    # whether the searched area meets a box, whether a box lies inside the area: _takes_test, _meets_test,
    # _sure_test); areas asking the same share one set
    pairs, takes = [], {}
    for a in areas:
        key = (tuple(a.what), tuple(a.types))
        if key not in takes:
            named = set(a.types)
            takes[key] = {s for s, n in enumerate(sc.names[:len(sc.flags)])
                          if n in named or (kinds.get(s) in a.what and s not in bridges)}
        by_size = bool(a.by_size and most)
        if by_size:  # searched as far as the farthest reach, asked by each object's own
            from dataclasses import replace
            searched = replace(a, radius=a.radius + most)
        else:
            searched = a
        pairs.append((searched, takes[key], a) + _takes_test(a, by_size)
                     + (_meets_test(searched), _sure_test(a, by_size, reach)))
    flat, boxes = _placed_items(sc)
    grid = _AreaGrid(pairs) if len(pairs) > 64 else None
    whole: dict = {}  # (block, id(its names)) -> what taking every object of those names under it takes (bulk)
    seen = [0]
    n_blocks = len(sc.blocks)
    tame = all(_tame_cover(a) for a in areas)
    held: dict = {}  # the name sets (by id) of the areas meeting a placement -> those holding all the others

    def holding(inner: list):
        ids = {id(p[1]): p[1] for p in inner}
        if len(ids) == 1:
            return ids
        key = frozenset(ids)
        got = held.get(key)
        if got is None:
            got = held[key] = {i for i, ok in ids.items() if all(o <= ok for o in ids.values())}
        return got
    nothing = frozenset()
    room = _room(flat, boxes) if any(p[6] for p in pairs) else None
    if room is not None:
        under = [nothing] * n_blocks  # the names under each block, however deep
        level = [True] * n_blocks     # whether every block under it is placed flat (x and y not hanging on z)
        for bi in range(n_blocks - 1, -1, -1):
            names, even = set(), True
            for e in flat[bi]:
                if e[1] >= 0:
                    names.add(e[1])
                else:
                    names |= under[e[2]]
                    even = even and level[e[2]] and e[3][2] == 0.0 and e[3][6] == 0.0
            under[bi], level[bi] = frozenset(names), even
    every = set(range(len(sc.names)))  # bulk with every name: the whole placement goes
    unions: dict = {}  # (sure names, id(an area's names)) -> both together

    def bulk(j: int, ok: set) -> _Cut | None:
        """What a placement of block j loses when every object under it lies in an area taking the names `ok` and no
        area meeting it takes any other: every object of those names, its children's too. Worked out once per block
        and names (most blocks are placed many times: a wood's patch), each placement getting its own copy (the
        writer makes one block copy per cut)."""
        key = (j, id(ok))
        if key not in whole:
            b = sc.blocks[j]
            removed, changes, gone = set(), {}, {}
            for it in b.items:
                if it.kind == "object":
                    if it.symbol in ok:
                        removed.add(it.at)
                        gone[it.symbol] = gone.get(it.symbol, 0) + 1
                elif it.kind == "child":
                    k = sc._by_offset[it.child_offset]
                    if boxes[k] is None:
                        continue
                    c = bulk(k, ok)
                    if c is None:
                        continue
                    for s, n in c.gone.items():
                        gone[s] = gone.get(s, 0) + n
                    if c.empty:
                        removed.add(it.at)
                    else:
                        changes[it.at] = c
            whole[key] = None if not removed and not changes else \
                _Cut(j, removed, changes, gone, len(removed) == len(b.items) and j != 0)
        return _copy_cut(whole[key])

    def visit(bi: int, m: tuple, near: list, sure: frozenset) -> _Cut | None:
        """`near`: the areas that meet this placement (only they can take anything from it); `sure`: the names areas
        sure for it take (only while it's placed flat)."""
        seen[0] += 1
        if cancel is not None and seen[0] % 4096 == 0 and cancel():
            raise EraseCancelled("a newer erase was asked for")
        removed, changes, gone = set(), {}, {}
        g = grid if near is pairs else None  # the grid holds exactly every area: only for the top placement
        m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, _m11 = m
        even = room is not None and m2 == 0.0 and m6 == 0.0  # placed flat: an area can be sure for what's under it
        asks: dict = {}  # name index -> the tests of the areas in `near` that take it, in their order
        for e in flat[bi]:
            s = e[1]
            if s >= 0:  # an object: it goes when the first area (in order) taking its name says so
                if s in sure:
                    removed.add(e[0])
                    gone[s] = gone.get(s, 0) + 1
                    continue
                tx, ty, tz = e[2], e[3], e[4]
                x = m0 * tx + m1 * ty + m2 * tz + m3
                y = m4 * tx + m5 * ty + m6 * tz + m7
                if g is not None:
                    tests = [p[3:5] for p in g.query(x, y, x, y) if s in p[1]]
                else:
                    tests = asks.get(s)
                    if tests is None:
                        tests = asks[s] = [p[3:5] for p in near if s in p[1]]
                rs = None  # how far it reaches: its type's reach times its size (the length of its placed x axis)
                for by_reach, test in tests:
                    if by_reach:
                        if rs is None:
                            l0, l4, l8 = e[5], e[6], e[7]
                            ax = m0 * l0 + m1 * l4 + m2 * l8
                            ay = m4 * l0 + m5 * l4 + m6 * l8
                            az = m8 * l0 + m9 * l4 + m10 * l8
                            rs = reach.get(s, 0.0) * math.sqrt(ax * ax + ay * ay + az * az)
                        if test(x, y, rs):
                            break
                    elif test(x, y):
                        break
                else:
                    continue
                removed.add(e[0])
                gone[s] = gone.get(s, 0) + 1
                continue
            at, _s, j, local = e
            flat_here = even and local[2] == 0.0 and local[6] == 0.0  # what's sure here is sure for it too
            if flat_here and level[j] and under[j] <= sure:
                c = bulk(j, every)
            else:
                cm = compose(m, local)
                bx0, by0, bx1, by1 = boxes[j]  # its box's corners, placed
                c0, c1, c3, c4, c5, c7 = cm[0], cm[1], cm[3], cm[4], cm[5], cm[7]
                xa, ya = c0 * bx0 + c1 * by0 + c3, c4 * bx0 + c5 * by0 + c7
                xb, yb = c0 * bx1 + c1 * by0 + c3, c4 * bx1 + c5 * by0 + c7
                xc, yc = c0 * bx0 + c1 * by1 + c3, c4 * bx0 + c5 * by1 + c7
                xd, yd = c0 * bx1 + c1 * by1 + c3, c4 * bx1 + c5 * by1 + c7
                x0, y0, x1, y1 = min(xa, xb, xc, xd), min(ya, yb, yc, yd), max(xa, xb, xc, xd), max(ya, yb, yc, yd)
                inner = [p for p in (g.query(x0, y0, x1, y1) if g is not None else near) if p[5](x0, y0, x1, y1)]
                if not inner:
                    continue
                held_there, need = nothing, None
                if flat_here:  # the areas it lies inside with room to spare join those sure for this placement
                    held_there, need = sure, under[j] - sure
                    gx0, gy0, gx1, gy1 = x0 - room, y0 - room, x1 + room, y1 + room
                    for p in inner:
                        if p[6] is not None and not p[1].isdisjoint(need) and p[6](gx0, gy0, gx1, gy1):
                            k = (held_there, id(p[1]))
                            u = unions.get(k)
                            if u is None:
                                u = unions[k] = held_there | p[1]
                            held_there, need = u, need - p[1]
                            if not need:
                                break
                if flat_here and level[j] and not need:
                    c = bulk(j, every)
                else:
                    corners = ((xa, ya), (xb, yb), (xc, yc), (xd, yd))
                    if tame and -_FAR <= x0 and x1 <= _FAR and -_FAR <= y0 and y1 <= _FAR:
                        # covers() can't fail here (_tame_cover): asked only of an area whose names hold the others'
                        sup = holding(inner)
                        over = next((p[1] for p in inner if id(p[1]) in sup and p[2].mask is None
                                     and p[2].covers(corners)), None) if sup else None
                    else:
                        over = next((p[1] for p in inner if p[2].mask is None and p[2].covers(corners)
                                     and all(q[1] <= p[1] for q in inner)), None)
                    c = bulk(j, over) if over is not None else visit(j, cm, inner, held_there)
            if c is None:
                continue
            for s, n in c.gone.items():
                gone[s] = gone.get(s, 0) + n
            if c.empty:
                removed.add(at)
            else:
                changes[at] = c
        if not removed and not changes:
            return None
        return _Cut(bi, removed, changes, gone, len(removed) == len(sc.blocks[bi].items) and bi != 0)
    return visit(0, IDENTITY, pairs, nothing)


class EraseCancelled(Exception):
    """erase_plan stopped because its `cancel()` said so (the Studio: a newer count was asked for)."""


def _copy_cut(c: _Cut | None) -> _Cut | None:
    """A cut of its own for one placement (the writer copies a shared block once per cut), sharing the sets it only
    reads."""
    if c is None:
        return None
    return _Cut(c.block, c.removed, {k: _copy_cut(v) for k, v in c.changes.items()}, c.gone, c.empty)


def _rebuilt(b: Block, removed: set) -> tuple[bytes, dict[int, int]]:
    """Block `b` without the items at `removed`: their entries leave the lists, every tree node's split moves back by
    the entries taken out before it (a node's boxes and LOD masks stay: a box holding fewer items is still right; a
    leaf may end up empty, as hundreds of the shipped ones are), the items close up, and the block is padded to 16
    bytes as the shipped ones are. Returns (the block, {old item offset: new}) for the references in it."""
    if not removed:
        return b.raw, {it.at: it.at for it in b.items}
    head = 0x20 if b.long else 0x1C
    gone_idx = [e for e, at in enumerate(b.entries) if at in removed]
    first = min(it.at for it in b.items)  # what comes before the first item (the shipped blocks' filler word)
    new_at, items, pos = {}, [], first
    for it in sorted(b.items, key=lambda i: i.at):
        if it.at in removed:
            continue
        new_at[it.at] = pos
        items.append(struct.pack("<I", it.word) + it.data)
        pos += 4 + len(it.data)
    entries = [new_at[at] for at in b.entries if at not in removed]
    nodes = b"".join(struct.pack("<IHBB", w, split - bisect.bisect_left(gone_idx, split), b1, b2)
                     for w, split, b1, b2 in _tree(b))
    (w0,) = struct.unpack_from("<I", b.raw)
    out = (struct.pack("<I", (w0 & 0x80000000) | len(entries)) + b.raw[4:head]
           + struct.pack(f"<{len(entries)}I", *entries) + nodes
           + b.raw[b.items_start:b.items_start + first] + b"".join(items))
    return out + b"\0" * (-len(out) % 16), new_at


def erase_objects(data: bytes, areas: list[EraseArea], kinds: dict[int, str],
                  bridges=frozenset(), sizes: dict[str, float] | None = None,
                  cancel=None) -> tuple[bytes, list[str], dict[str, int]]:
    """The scenery file with the objects in `areas` taken out (erase_plan says which). Most of a map's trees are in
    blocks it places many times (a wood's patch, repeated across the map), so a placement that loses objects gets a
    copy of its block of its own, without them (copy on write): the reference that placed it points to the copy, the
    copy's references to the blocks under it that change point to their own copies, and the rest still point to the
    shared blocks. A block placed once is changed where it is; a placement left with nothing loses its reference; a
    block nothing places any more goes. Every copy goes right before the block it copies, so references still point
    forward. The trees' boxes, the road marks and the grids stay as they are (a cell or box that holds less is still
    right). Returns (new file, notes, objects erased per group: `kinds`' groups, "bridge" for `bridges`, "other" for
    a name with no group)."""
    if not areas:
        return bytes(data), [], {}
    sc = Scenery(data)
    unknown = sorted({t for a in areas for t in a.types} - set(sc.names[:len(sc.flags)]))
    said = [f"{', '.join(unknown)}: not on this map, so the erase areas take none of it"] if unknown else []
    cut = erase_plan(sc, areas, kinds, bridges, sizes, cancel)
    if cut is None:
        return bytes(data), [f"the erase area(s) cover nothing they may remove: {len(areas)} area(s), no change"] + said, {}
    weight, _where = sc.placings()
    inplace: dict[int, _Cut] = {}
    copies: dict[int, list] = {}
    # placements that lose the same objects from the same block share one copy of it, as the shipped maps share
    # blocks: a big erase (most of a map, its ground stickers kept) otherwise copies a wood's patch once for every
    # place it stands and passes what a map can hold (the owner's whole-map erase on M04_Cotentin, 2026-10-04)
    keyed: dict[int, tuple] = {}
    same: dict[tuple, _Cut] = {}
    alias: dict[int, _Cut] = {}  # id(a cut) -> the cut whose copy it shares

    def key(c: _Cut) -> tuple:
        k = keyed.get(id(c))
        if k is None:
            k = keyed[id(c)] = (c.block, frozenset(c.removed),
                                tuple(sorted((at, key(ch)) for at, ch in c.changes.items())))
        return k
    todo = [cut]
    while todo:
        c = todo.pop()
        if weight[c.block] == 1:
            inplace[c.block] = c
        else:
            first = same.setdefault(key(c), c)
            if first is not c:
                alias[id(c)] = first
                continue  # its children are the first one's too
            copies.setdefault(c.block, []).append(c)
        todo += c.changes.values()
    # the blocks out, in order: each block's copies right before it
    order: list[tuple[int, _Cut | None]] = []
    out_of_cut: dict[int, int] = {}
    out_of_block: dict[int, int] = {}
    for b in sc.blocks:
        for c in copies.get(b.index, []):
            out_of_cut[id(c)] = len(order)
            order.append((b.index, c))
        out_of_block[b.index] = len(order)
        if b.index in inplace:
            out_of_cut[id(inplace[b.index])] = len(order)
        order.append((b.index, inplace.get(b.index)))

    def targets(k: int):
        """(the child item, the output block it points to) for output block k's references that stay."""
        bi, c = order[k]
        for it in sc.blocks[bi].items:
            if it.kind != "child" or (c is not None and it.at in c.removed):
                continue
            ch = c.changes.get(it.at) if c is not None else None
            if ch is not None:
                ch = alias.get(id(ch), ch)
            yield it, (out_of_cut[id(ch)] if ch is not None else out_of_block[sc._by_offset[it.child_offset]])
    reached, todo_k = {out_of_block[0]}, [out_of_block[0]]
    while todo_k:
        k = todo_k.pop()
        for _it, t in targets(k):
            if t not in reached:
                reached.add(t)
                todo_k.append(t)
    kept = [k for k in range(len(order)) if k in reached]
    raws, maps, offset_of, pos = {}, {}, {}, 0
    for k in kept:
        bi, c = order[k]
        raws[k], maps[k] = _rebuilt(sc.blocks[bi], c.removed if c is not None else set())
        offset_of[k] = pos
        pos += len(raws[k])
    if pos > DATA_LIMIT:
        raise SceneryEditError(f"erasing there copies too many of the map's shared blocks: its scenery would grow to "
                               f"{pos:,} bytes, past the {DATA_LIMIT:,} a map can hold. Erase smaller areas")
    parts = []
    for k in kept:
        bi, _c = order[k]
        b = sc.blocks[bi]
        raw = bytearray(raws[k])
        start = (0x20 if b.long else 0x1C) + 4 * (struct.unpack_from("<I", raw)[0] & 0x7FFFFFFF) + len(b.nodes)
        for it, t in targets(k):
            struct.pack_into("<I", raw, start + maps[k][it.at], link_word(it.word, offset_of[t]))
        parts.append(bytes(raw))
    body = _assembled(sc, data, parts)
    by_group: dict[str, int] = {}
    for s, n in cut.gone.items():
        g = "bridge" if s in bridges else kinds.get(s, "other")
        by_group[g] = by_group.get(g, 0) + n
    n_copies = sum(len(v) for v in copies.values())
    dropped = len(sc.blocks) + n_copies - len(kept)
    notes = [f"{sum(cut.gone.values()):,} object(s) erased in {len(areas)} area(s): "
             + ", ".join(f"{n:,} {g}" for g, n in sorted(by_group.items(), key=lambda kv: -kv[1]))]
    if n_copies:
        grew = len(body) + 16 - len(data)
        notes.append(f"{n_copies} shared block(s) copied for the erased spots"
                     + (f", {dropped} no longer placed anywhere left out" if dropped else "")
                     + (f": the scenery grew by {grew:,} bytes" if grew >= 0 else
                        f": the scenery shrank by {-grew:,} bytes"))
    return hashlib.md5(body).digest() + body, notes + said, by_group


def _assembled(sc: Scenery, data: bytes, parts: list[bytes]) -> bytes:
    """The scenery file (without its MD5) holding the blocks `parts` (each as stored, in order, its references
    already pointing at the others' new offsets) in place of `sc`'s: the block table made again, and the tables after
    the data moved with its end."""
    body_data = b"".join(parts)
    f = list(sc.fields)
    tab_off, tab_n, data_off, data_len = f[0], f[1], f[2], f[3]
    if tab_off != 124 or data_off != tab_off + 4 * tab_n:
        raise SceneryError("the scenery file's tables aren't in the order this writer knows")
    end = data_off + data_len
    new_n = len(parts) + 1
    shift = (124 + 4 * new_n + len(body_data)) - end
    for k in (4, 6, 8, 10, 12, 20, 22, 24):  # the tables after the data move with its end
        if f[k] < end:
            raise SceneryError("the scenery file's tables aren't in the order this writer knows")
        f[k] += shift
    f[1], f[2], f[3] = new_n, 124 + 4 * new_n, len(body_data)
    table, at = [], 0
    for p in parts:
        table.append(at)
        at += len(p)
    table.append(len(body_data))
    return VERSION + struct.pack("<26I", *f) + struct.pack(f"<{len(table)}I", *table) + body_data + data[end:]


def take_out_road_pieces(data: bytes) -> tuple[bytes, list[str]]:
    """The scenery file with every road piece taken out (Item kind "road", the Route pieces the far roads are drawn
    with): each block holding any made again without them (_rebuilt, as an erase does), every reference pointed at the
    blocks' new places. Returns (the file, notes); a map with none gives the same bytes. Not seen in the game yet."""
    sc = Scenery(data)
    removed = [{it.at for it in b.items if it.kind == "road"} for b in sc.blocks]
    n = sum(len(r) for r in removed)
    if not n:
        return bytes(data), []
    raws, maps, offset_of, pos = [], [], [], 0
    for b in sc.blocks:
        raw, moved = _rebuilt(b, removed[b.index])
        raws.append(raw)
        maps.append(moved)
        offset_of.append(pos)
        pos += len(raw)
    parts = []
    for b in sc.blocks:
        raw = bytearray(raws[b.index])
        start = (0x20 if b.long else 0x1C) + 4 * (struct.unpack_from("<I", raw)[0] & 0x7FFFFFFF) + len(b.nodes)
        for it in b.items:
            if it.kind == "child":
                to = sc._by_offset[it.child_offset]
                struct.pack_into("<I", raw, start + maps[b.index][it.at], link_word(it.word, offset_of[to]))
        parts.append(bytes(raw))
    body = _assembled(sc, data, parts)
    return hashlib.md5(body).digest() + body, [f"{n:,} road piece(s) taken out (the roads drawn from far)"]


# the names of the map's road stickers (the close-up road: asphalt, cobbles, dirt tracks, their edges and junctions),
# by the kinds the shipped maps use; a crater's or a shelling's tracks (Chemin_traces) aren't a road
ROAD_STICKER = re.compile(r"(?i)route|bitum|bitu_|rte_bitu|asphalte_ruelle|chemin_terre|chemin_petit|cheminculture"
                          r"|paves|under_road")


def road_stickers(names, descs: dict) -> list[str]:
    """Of `names` (a map's scenery type names), its road stickers: decals whose category is a road's or whose name
    says it (ROAD_STICKER), never a crater's tracks."""
    out = []
    for n in names:
        d = descs.get(n)
        if d is None or d.group != "decal" or "chemin_traces" in n.lower():
            continue
        if "roads" in (d.category or "").lower() or ROAD_STICKER.search(n.rsplit("/", 1)[-1]):
            out.append(n)
    return out


def erase_count(data: bytes, areas: list[EraseArea], descs: dict[str, Descriptor], cancel=None) -> dict[str, int]:
    """What `areas` take off the map whose scenery file is `data`, per group as erase_objects counts them, worked out
    the way the build erases (so an erase too big for the map raises SceneryEditError, as the build refuses it). The
    Studio's Erase tool says it while circles are painted; nothing is written. `cancel`: erase_plan's."""
    names = Scenery(data).names
    kinds = {i: descs[n].group for i, n in enumerate(names) if n in descs}
    bridges = {i for i, n in enumerate(names) if n in descs and descs[n].bridge}
    return erase_objects(data, areas, kinds, bridges, cancel=cancel)[2]


# --- what hides painted ground up close (TESTS.md T21: with it taken off under a patch, the paint shows at every
# height; the game draws it only near the camera, over the ground's picture) ---
LOW_STONES = ("caillou", "champspierres", "pierres")  # the stone props T21 took off (by name: they share Props/Ferme)


def low_cover(descs: dict[str, Descriptor], names) -> list[str]:
    """Of `names` (a map's type names), the low cover besides the ground stickers (those go as a whole group, decal):
    the low plants (every vegetation type outside Vegetation/Arbres: crops, grass, bushes, flowers) and the stones."""
    out = []
    for nm in names:
        d = descs.get(nm)
        if d is None:
            continue
        if d.group == "vegetation" and not d.category.lower().startswith("vegetation/arbres"):
            out.append(nm)
        elif d.group == "prop" and nm.rsplit("/", 1)[-1].lower().startswith(LOW_STONES):
            out.append(nm)
    return sorted(out)


def sticker_reach(arc) -> dict[str, float]:
    """How far each sticker type reaches from its middle at size 1, across the ground (map units): from its
    descriptor's MinExtent and MaxExtent (Herbe_verte: 2,000 or 2,048 to each side, about 11 m from its middle), the
    largest where several decor sets define the name. From the unit-data pack `arc` (an Edat)."""
    from .ndf import Ndf
    out: dict[str, float] = {}
    for e in arc.entries:
        if not e.path.lower().startswith(SCENERY_DIR):
            continue
        n = Ndf(bytes(arc.read(e)))
        names = [p for p, _ in n.props]
        for i, o in enumerate(n.objects):
            d = {names[pi]: v for pi, v in o.props}
            lo, hi = d.get("MinExtent"), d.get("MaxExtent")
            if lo is None or hi is None or len(lo.payload) < 12 or len(hi.payload) < 12:
                continue
            v = d.get("RegistrationName")
            name = n.strings[struct.unpack("<I", v.payload)[0]] if v is not None and v.tc in (0x07, 0x1C) else ""
            if not name:
                path = n.exports.get(i) or ""
                name = path[2:] if path.startswith("$/TypeWarrior/") else ""
            if not name:
                continue
            (x0, y0, _z0), (x1, y1, _z1) = struct.unpack("<3f", lo.payload[:12]), struct.unpack("<3f", hi.payload[:12])
            r = math.hypot(max(abs(x0), abs(x1)), max(abs(y0), abs(y1)))
            if math.isfinite(r):
                out[name] = max(out.get(name, 0.0), r)
    return out


def model_reach(lib, d: Descriptor) -> float:
    """How far a type's close-up models reach from its middle across the ground at size 1 (map units); 0 when none is
    found. `lib`: a rusemod.models.Library."""
    far = 0.0
    for model in (d.models or ([d.model] if d.model else [])):
        name = lib.find(model)
        if name is None:
            continue
        for part, _tex in lib.parts(name):
            pos = part.positions
            for k in range(0, len(pos) - 2, 3):
                far = max(far, (pos[k] * pos[k] + pos[k + 1] * pos[k + 1]) ** 0.5)
    return far


def parse_erase(rows: list, where: str = "scenery.toml") -> list[EraseArea]:
    out = []
    for k, row in enumerate(rows):
        extra = sorted(set(row) - {"x", "y", "radius", "what", "types", "shape", "dx", "dy", "x2", "y2"})
        if extra:
            raise SceneryEditError(f"{where}: erase area {k + 1}: unknown key {extra[0]!r}")
        shape = row.get("shape", "round")
        if shape not in ("round", "square", "line"):
            raise SceneryEditError(f"{where}: erase area {k + 1}: shape must be round, square or line")
        try:
            dx, dy = float(row.get("dx", 1.0)), float(row.get("dy", 0.0))
            x2, y2 = float(row.get("x2", 0.0)), float(row.get("y2", 0.0))
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: erase area {k + 1}: dx, dy, x2 and y2 must be numbers") from None
        if shape == "line" and ("x2" not in row or "y2" not in row):
            raise SceneryEditError(f"{where}: erase area {k + 1}: a line needs x2 and y2 (where it ends)")
        if shape == "square" and dx == 0.0 and dy == 0.0:
            raise SceneryEditError(f"{where}: erase area {k + 1}: the square's direction dx, dy can't be 0, 0")
        try:
            x, y, r = float(row["x"]), float(row["y"]), float(row["radius"])
        except KeyError as exc:
            raise SceneryEditError(f"{where}: erase area {k + 1} has no {exc.args[0]}") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: erase area {k + 1}: x, y and radius must be numbers") from None
        if not all(math.isfinite(v) for v in (x, y, r)) or not 0 < r <= ERASE_MAX:
            raise SceneryEditError(f"{where}: erase area {k + 1}: the radius must be above 0 and at most "
                                   f"{ERASE_MAX:,.0f} map units ({ERASE_MAX / 100:,.0f} m)")
        what, types = row.get("what", list(ERASE_DEFAULT)), row.get("types", [])
        if not isinstance(what, list) or not all(isinstance(g, str) for g in what):
            raise SceneryEditError(f"{where}: erase area {k + 1}: what must be a list, like [\"vegetation\", \"prop\"]")
        bad = [g for g in what if g not in ERASE_GROUPS]
        if bad:
            raise SceneryEditError(f"{where}: erase area {k + 1}: {bad[0]!r} isn't something it can erase (one of "
                                   f"{', '.join(ERASE_GROUPS)}; a bridge or another type goes by its name in types)")
        if not isinstance(types, list) or not all(isinstance(t, str) and t for t in types):
            raise SceneryEditError(f"{where}: erase area {k + 1}: types must be a list of type names, like "
                                   f"[\"TypeWarrior/MairieNormande\"]")
        if not what and not types:
            raise SceneryEditError(f"{where}: erase area {k + 1} names nothing to erase (what and types are empty)")
        out.append(EraseArea(x, y, r, tuple(what), tuple(types), shape=shape, dx=dx, dy=dy, x2=x2, y2=y2))
    return out


# --- the map's own ground detail laid again somewhere else on it ([[copy]], MOD_FORMAT §8) -----------------------------
# Up close a shipped map's ground is its stickers (ground decals ~5 deep), low plants and stones, laid by Eugen's tools in
# patterns (fields tiled in rows, heath scattered, hedge feet in strips). A
# copy lays the map's own arrangement from one place in another, object by object, each with the LOD levels its shipped
# copy is drawn at: the same look, by construction, the first step to brushes that match the game (the owner,
# 2026-10-10: "at the very least, the paint and the textures we add on our studio are gonna load just like the game's").
COPY_LAYERS = ("stickers", "plants", "stones")  # ground decals (not road stickers); low plants; stone props (low_cover)
FIELD_COPY_LAYERS = COPY_LAYERS + ("trees", "props")  # and the rest of a field (expand_field_copy): trees, other props
                                                      # (hay, carts, tractors, fences); never buildings (not solid here)


LOW_COVER = "low cover"   # in an EraseArea's `types`: every low plant and stone type of the map (resolved at build)
FILL_GAP = {"plants": 260.0, "stones": 390.0, "stickers": 780.0, "trees": 260.0, "props": 130.0}   # the fill rule: a copied plant is left off within
# 1 m of a plant the map already has there, a stone within 1.5 m of a stone, a sticker within 3 m of one of its own
# kind (the owner, 2026-10-10: "I wouldn't want to like throw a plant on top of a plant"; a brush fills its layer up
# to the recipe, never past it, and never takes anything off)


RAISED = 0.3 * 260.0         # an object this far over the ground stands on something (CopyArea.src_avoid)
BUILDING_REACH = 3.0 * 260.0  # and within this of a building's model box, on that building: D-Day's raised wall plants
                              # (veget_EU_033/035/036) lie within 1 m of one 72-78% of the time, within 3 m 83-85%;
                              # objects on the ground 2.6% (measured 2026-10-16)


def _in_places(places, x: float, y: float) -> bool:
    """Whether (x, y) lies in one of `places`: (x, y, r) circles or (x, y, half u, half v, ux, uy, gap) rectangles
    and all within `gap` of them (CopyArea.avoid)."""
    for p in places:
        if len(p) == 3:
            if (x - p[0]) ** 2 + (y - p[1]) ** 2 < p[2] * p[2]:
                return True
            continue
        cx, cy, hu, hv, ux, uy, gap = p
        du = abs((x - cx) * ux + (y - cy) * uy) - hu
        dv = abs(-(x - cx) * uy + (y - cy) * ux) - hv
        if max(du, 0.0) ** 2 + max(dv, 0.0) ** 2 < gap * gap or (du < 0.0 and dv < 0.0):
            return True
    return False


@dataclass(frozen=True)
class CopyArea:
    """A shape whose ground detail comes from elsewhere on a map: the source is the shape moved by (sx, sy) and
    turned `turn` degrees about its own middle; every object of `layers` whose middle lies in the source is laid again
    in the shape, turned with it. Nothing is taken off the shape: an [[erase]] there does that. `source`: the map pack
    whose shipped scenery the source is read from ("" = this map's). `within`: a bigger footprint (shape, x, y,
    radius, dx, dy) the copy is clipped to (a preset's tile at the preset's edge). `fill`: the fill rule (FILL_GAP):
    an object is left off where the map already has one of its layer (its kind, for a sticker) right there. What
    earlier copies of the same build laid counts the same way whatever the mode (a brush is many dabs that overlap:
    none throws a plant on a plant), except among copies of one `group` (a preset's own tiles, which meet edge to
    edge and must not thin each other along their joins); 0 = no group, every other copy counts. `along`: a square's
    half-length along dx, dy when not `radius` (a rectangle: a field's tile, whole rows each way; 0 = a square).
    The field brush's copies (expand_field_brush) also take: `only`, name prefixes of the objects copied (its crops);
    `near` and `near_r`, places of the target map an object must land within near_r of (the stickers of the field
    painted over, so nothing lands on its hedges, the road or the meadow beside it); `src_clip`, a rectangle of the
    source (x, y, half across, dx, dy, half along: the source field's inside) the objects must come from; `avoid`,
    places of the target no object may land in: (x, y, r) a circle, (x, y, half u, half v, ux, uy, gap) a rectangle
    (a building's footprint: its middle, half sizes along its u axis (ux, uy) and the v axis square to it) and all
    within `gap` of it; `harvest`, where a crop landing is laid harvested (round the hay and machines left on a field):
    (x, y, r) a circle, the crop as HARVESTED says for its kind, or (x, y, r, height, lift, kind) the spot of one of
    the map's own harvested crops, a crop of its kind laid as it is (its height and lift; the nearest such spot); `skip`,
    name prefixes of objects not copied; `inside`, a test (x, y) -> bool an object must land where it holds
    (FieldInside: a field's interior, for its dressing)."""
    x: float
    y: float
    radius: float
    sx: float
    sy: float
    turn: float = 0.0
    layers: tuple = COPY_LAYERS
    shape: str = "square"  # round or square (sides along dx, dy, `radius` from its middle to each side)
    dx: float = 1.0
    dy: float = 0.0
    source: str = ""
    within: tuple | None = None
    fill: bool = False
    group: int = 0
    along: float = 0.0
    only: tuple = ()
    near: tuple = ()
    near_r: float = 0.0
    src_clip: tuple | None = None
    avoid: tuple = ()
    harvest: tuple = ()
    src_avoid: tuple = ()   # buildings of the SOURCE (avoid's rectangles) the copy doesn't take: an object raised
                            # more than RAISED over the ground with its source place in one (or within its gap) stood
                            # on that building (wall plants, window boxes), and is left out (expand_field_copy)
    skip: tuple = ()
    inside: object = field(default=None, compare=False)

    def footprint(self):
        from .brush import Footprint
        if self.shape == "square":
            return Footprint("square", self.x, self.y, self.radius, self.dx, self.dy, along=self.along)
        return Footprint("round", self.x, self.y, self.radius)

    def avoids(self, x: float, y: float) -> bool:
        """Whether (x, y) lies in one of the `avoid` places."""
        return _in_places(self.avoid, x, y)

    def source_clip(self):
        """The source rectangle the copy's objects must come from (`src_clip`), or None."""
        if not self.src_clip:
            return None
        from .brush import Footprint
        x, y, r, dx, dy, along = self.src_clip
        return Footprint("square", x, y, r, dx, dy, along=along)

    def clip(self):
        """The footprint the copy must also lie in (`within`), or None."""
        if not self.within:
            return None
        from .brush import Footprint
        shape, x, y, r, dx, dy = self.within
        return Footprint("square", x, y, r, dx, dy) if shape == "square" else Footprint("round", x, y, r)

    def to_target(self) -> tuple:
        """The transform (3x4) that takes a source point to its place in the shape."""
        t = math.radians(self.turn)
        c, s = math.cos(t), math.sin(t)
        ox, oy = self.x + self.sx, self.y + self.sy
        return (c, -s, 0.0, self.x - (c * ox - s * oy), s, c, 0.0, self.y - (s * ox + c * oy), 0.0, 0.0, 1.0, 0.0)


def parse_copies(rows: list, where: str = "scenery.toml") -> list[CopyArea]:
    out = []
    for k, row in enumerate(rows):
        extra = sorted(set(row) - {"x", "y", "radius", "sx", "sy", "turn", "layers", "shape", "dx", "dy", "fill",
                                   "source"})
        if extra:
            raise SceneryEditError(f"{where}: copy {k + 1}: unknown key {extra[0]!r}")
        shape = row.get("shape", "square")
        if shape not in ("round", "square"):
            raise SceneryEditError(f"{where}: copy {k + 1}: shape must be round or square")
        try:
            x, y, r = float(row["x"]), float(row["y"]), float(row["radius"])
            sx, sy, turn = float(row["sx"]), float(row["sy"]), float(row.get("turn", 0.0))
            dx, dy = float(row.get("dx", 1.0)), float(row.get("dy", 0.0))
        except KeyError as exc:
            raise SceneryEditError(f"{where}: copy {k + 1} has no {exc.args[0]}") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: copy {k + 1}: x, y, radius, sx, sy, turn, dx and dy must be "
                                   f"numbers") from None
        if not all(math.isfinite(v) for v in (x, y, r, sx, sy, turn, dx, dy)) or not 0 < r <= ERASE_MAX:
            raise SceneryEditError(f"{where}: copy {k + 1}: the radius must be above 0 and at most "
                                   f"{ERASE_MAX:,.0f} map units")
        if shape == "square" and dx == 0.0 and dy == 0.0:
            raise SceneryEditError(f"{where}: copy {k + 1}: the square's direction dx, dy can't be 0, 0")
        layers = row.get("layers", list(COPY_LAYERS))
        if (not isinstance(layers, list) or not layers or not all(isinstance(g, str) for g in layers)
                or any(g not in COPY_LAYERS for g in layers)):
            raise SceneryEditError(f"{where}: copy {k + 1}: layers must be a list of {', '.join(COPY_LAYERS)}")
        fill, source = row.get("fill", False), row.get("source", "")
        if not isinstance(fill, bool):
            raise SceneryEditError(f"{where}: copy {k + 1}: fill must be true or false")
        if not isinstance(source, str):
            raise SceneryEditError(f"{where}: copy {k + 1}: source must be a map pack name")
        out.append(CopyArea(x, y, r, sx, sy, turn, tuple(layers), shape, dx, dy, source, None, fill))
    return out


# --- presets: a map's ground kinds laid over an area (MOD_FORMAT §8 [[preset]]) ---------------------------------
PRESET_MODES = ("add", "replace")
TILE = 13000.0   # a preset's tile, 50 m (260 map units a metre): the size of the library's source squares
PRESET_FILE = "ground_presets.toml"   # beside this module: the library (name, description, map, sources)
BORDERS = ("none", "edge", "hedge")   # what a preset may lay along its outline: nothing, or the [[border]] so named
BORDER_WIDTH = 520.0   # the band a border's strips lie in: 2 m across, centred on the outline (strips: 0.8-1.5 m)
BORDER_LAYERS = ("plants", "stones")   # what a border copies: its strip, not the ground stickers it lay on
BORDER_SAG = 65.0      # a round area's outline is chords that stray at most this far inside it (25 cm)


@dataclass(frozen=True)
class PresetArea:
    """A shape filled with one of the library's ground kinds ("Wheat field", ...): tiles of TILE across it, each laid
    from one of the kind's source squares on its map (stickers, low plants and stones with the game's own detail
    levels, and the ground picture stamped). `mode` add: the fill rule, nothing of the map's taken off; replace: the
    shape's own stickers, low plants and stones taken off first. `seed` picks which source each tile gets. `border`:
    the game's own strips laid along the outline (BORDERS: none, edge, hedge; expand_border)."""
    name: str
    x: float
    y: float
    radius: float
    mode: str = "add"
    shape: str = "square"
    dx: float = 1.0
    dy: float = 0.0
    seed: int = 0
    border: str = "none"

    def footprint(self):
        from .brush import Footprint
        if self.shape == "square":
            return Footprint("square", self.x, self.y, self.radius, self.dx, self.dy)
        return Footprint("round", self.x, self.y, self.radius)


def parse_presets(rows: list, where: str = "scenery.toml") -> list[PresetArea]:
    out = []
    for k, row in enumerate(rows):
        extra = sorted(set(row) - {"name", "x", "y", "radius", "mode", "shape", "dx", "dy", "seed", "border"})
        if extra:
            raise SceneryEditError(f"{where}: preset {k + 1}: unknown key {extra[0]!r}")
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            raise SceneryEditError(f"{where}: preset {k + 1} has no name")
        shape = row.get("shape", "square")
        if shape not in ("round", "square"):
            raise SceneryEditError(f"{where}: preset {k + 1}: shape must be round or square")
        mode = row.get("mode", "add")
        if mode not in PRESET_MODES:
            raise SceneryEditError(f"{where}: preset {k + 1}: mode must be add or replace")
        border = row.get("border", "none")
        if border not in BORDERS:
            raise SceneryEditError(f"{where}: preset {k + 1}: border must be {', '.join(BORDERS[:-1])} or "
                                   f"{BORDERS[-1]}")
        try:
            x, y, r = float(row["x"]), float(row["y"]), float(row["radius"])
            dx, dy = float(row.get("dx", 1.0)), float(row.get("dy", 0.0))
            seed = int(row.get("seed", 0))
        except KeyError as exc:
            raise SceneryEditError(f"{where}: preset {k + 1} has no {exc.args[0]}") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: preset {k + 1}: x, y, radius, dx, dy and seed must be numbers") from None
        if not all(math.isfinite(v) for v in (x, y, r, dx, dy)) or not 0 < r <= ERASE_MAX:
            raise SceneryEditError(f"{where}: preset {k + 1}: the radius must be above 0 and at most "
                                   f"{ERASE_MAX:,.0f} map units")
        if shape == "square" and dx == 0.0 and dy == 0.0:
            raise SceneryEditError(f"{where}: preset {k + 1}: the square's direction dx, dy can't be 0, 0")
        out.append(PresetArea(name.strip(), x, y, r, mode, shape, dx, dy, seed, border))
    return out


def preset_library(path=None) -> dict[str, dict]:
    """The ground presets, by name: {"description", "map" (the pack whose squares they are), "sources" [(x, y)...]
    (50 m squares' middles), "aligned" (rows run one way)}; a field kind's also its "swatch" (the palette swatch its
    picture is laid with, groundtex: swatch:<theme>:<name>; "" none). From ground_presets.toml beside this module."""
    import tomllib
    from pathlib import Path
    file = Path(path) if path else Path(__file__).with_name(PRESET_FILE)
    data = tomllib.loads(file.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for row in data.get("preset", []):
        name = str(row.get("name", "")).strip()
        sources = [(float(s[0]), float(s[1])) for s in row.get("sources", [])]
        if not name or not sources or not row.get("map"):
            raise SceneryEditError(f"{file.name}: a preset needs a name, a map and sources")
        out[name] = {"type": "tile", "description": str(row.get("description", "")), "map": str(row["map"]),
                     "sources": sources, "aligned": bool(row.get("aligned", False))}
    for row in data.get("field", []):   # a field kind: one real field's rows tiled over the area (expand_field)
        name = str(row.get("name", "")).strip()
        sources = []
        for s in row.get("sources", []):
            if len(s) != 7:
                raise SceneryEditError(f"{file.name}: a field source is [x, y, angle, window along, window across, "
                                       f"pitch along, pitch across]")
            sources.append(FieldSource(*(float(v) for v in s)))
        if not name or not sources or not row.get("map"):
            raise SceneryEditError(f"{file.name}: a field needs a name, a map and sources")
        if any(s.pitch_u <= 0 or s.pitch_v <= 0 or s.window_u < s.pitch_u or s.window_v < s.pitch_v for s in sources):
            raise SceneryEditError(f"{file.name}: field {name!r}: a window must hold whole pitches above 0")
        swatch = str(row.get("swatch", ""))
        if swatch:
            from .groundtex import TextureError, check_ref
            try:
                check_ref(swatch)
            except TextureError as exc:
                raise SceneryEditError(f"{file.name}: field {name!r}: {exc}") from None
        out[name] = {"type": "field", "description": str(row.get("description", "")), "map": str(row["map"]),
                     "sources": sources, "aligned": True, "swatch": swatch}
    return out


@dataclass(frozen=True)
class FieldSource:
    """One real field to lay a field kind from: the middle of a window inside it (map units), the direction its
    rows run (degrees, from +x toward +y), the window's extent along and across the rows, and the rows' pitch along
    (sticker to sticker) and across (row to row). A window of whole pitches tiles seamlessly: the rows run on."""
    x: float
    y: float
    angle: float
    window_u: float
    window_v: float
    pitch_u: float
    pitch_v: float


def hedgerow_library(path=None) -> dict[str, dict]:
    """What a field's hedgerow carries besides its strips, per map: the trees along a field's edge (name, share,
    LOD levels) and how many there are per 100 m, and the fence piece (name, levels, length). From the [[hedgerow]]
    tables of ground_presets.toml beside this module."""
    import tomllib
    from pathlib import Path
    file = Path(path) if path else Path(__file__).with_name(PRESET_FILE)
    data = tomllib.loads(file.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for row in data.get("hedgerow", []):
        if not row.get("map"):
            raise SceneryEditError(f"{file.name}: a hedgerow needs a map")
        trees = [(str(t[0]), float(t[1]), int(t[2])) for t in row.get("trees", [])]
        fence = row.get("fence")
        out[str(row["map"])] = {"trees_per_100m": float(row.get("trees_per_100m", 0.0)), "trees": trees,
                                "fence": (str(fence[0]), int(fence[1]), float(fence[2])) if fence else None}
    return out


HEDGEROW_OUT = 1.5 * 260.0   # a hedgerow's trees stand this far outside the outline (the strips lie on it)
FENCE_OUT = 0.6 * 260.0      # the fence line, just outside the strips


def expand_hedgerow(area: PresetArea, hedgerow: dict | None, seed: int = 0) -> list[NewObject]:
    """The trees and the fence a field's border carries (a field kind with a border, from hedgerow_library's entry
    for its map): along each run of the outline, fence pieces end to end FENCE_OUT outside it, and with a hedge
    (border "hedge"; a field's plain "edge" has the fence alone) trees at the map's count per 100 m (species by
    share, each where the map draws its kind), stood HEDGEROW_OUT outside with a little scatter. Only drawn (solid
    false): the strips under them hold the ground. Nothing without a hedgerow entry for the map."""
    import random
    if not hedgerow or area.border == "none":
        return []
    hedge = area.border == "hedge"
    rng = random.Random(seed * 7919 + 1)
    out: list[NewObject] = []
    trees, per = hedgerow.get("trees") or [], hedgerow.get("trees_per_100m", 0.0)
    fence = hedgerow.get("fence")
    for (x0, y0), (x1, y1) in border_outline(area):
        run = math.hypot(x1 - x0, y1 - y0)
        if run <= 0.0:
            continue
        ux, uy = (x1 - x0) / run, (y1 - y0) / run
        vx, vy = -uy, ux   # outward, away from the area's middle (a square's outline and a circle's go round
        if (x0 + x1) / 2 * vx + (y0 + y1) / 2 * vy < area.x * vx + area.y * vy:   # opposite ways)
            vx, vy = -vx, -vy
        along = math.degrees(math.atan2(uy, ux))
        if fence:
            name, levels, piece = fence
            count = max(1, int(math.ceil(run / piece)))
            for p in range(count):
                d = min((p + 0.5) * piece, run - piece / 2)
                out.append(NewObject(name, x0 + ux * d + vx * FENCE_OUT, y0 + uy * d + vy * FENCE_OUT, along, 1.0,
                                     solid=False, levels=levels))
        if hedge and trees and per > 0.0:
            count = int(round(run / 260.0 * per / 100.0))
            for t in range(count):
                d = (t + rng.uniform(0.25, 0.75)) * run / count
                r = rng.random()
                name, levels = trees[-1][0], trees[-1][2]
                for nm, share, lv in trees:
                    r -= share
                    if r <= 0.0:
                        name, levels = nm, lv
                        break
                off = HEDGEROW_OUT + rng.uniform(-0.5, 0.5) * 260.0
                out.append(NewObject(name, x0 + ux * d + vx * off, y0 + uy * d + vy * off, rng.uniform(0.0, 360.0),
                                     1.0, solid=False, levels=levels))
    return out


def expand_field(area: PresetArea, kind: dict, group: int = 1) -> tuple[list[CopyArea], list]:
    """A field kind laid as the editor laid a field: ONE source field (kind["sources"], FieldSource, picked by
    area.seed), its window tiled over the area with the rows running along the area's dx, dy. A tile is a
    rectangle of whole pitches each way (the window floored to sticker pitches along the rows and row pitches
    across), laid edge to edge: the rows run on from tile to tile both ways, nothing is laid twice (2026-10-14:
    square tiles overlapping by a pitch along the rows laid a ploughed field's crops and stones twice in every
    overlap, 360 tiles on a 100 m square). Every tile copies the same window, turned from the source's row
    direction to the area's (CopyArea.turn), clipped to the area, with the preset's group. The ground picture is the
    kind's palette swatch (kind["swatch"], groundtex.palette: a square of the same map's picture, so it lays the same
    on any map) as ONE texture stroke over the area, its rows turned with the copied stickers' (a source's angle is its
    row stickers' own axis, which lies across the rows: the rows run at the angle + 90); a kind without one stamps
    the window, squares as wide as a tile along it (unturned: a stamp copies by offset, so from the map it is laid on:
    right only on the kind's own map)."""
    from .brush import HARD_EDGE, Stroke
    sources = kind["sources"]
    src = sources[area.seed % len(sources)]
    n = math.hypot(area.dx, area.dy) or 1.0
    ux, uy = area.dx / n, area.dy / n
    vx, vy = -uy, ux
    long = max(1, int(src.window_u // src.pitch_u)) * src.pitch_u   # along the rows
    wide = max(1, int(src.window_v // src.pitch_v)) * src.pitch_v   # across them
    turn = math.degrees(math.atan2(uy, ux)) - src.angle
    foot = area.footprint()
    within = (area.shape, area.x, area.y, area.radius, area.dx, area.dy)
    steps_u = int(math.ceil(area.radius / long)) + 1
    steps_v = int(math.ceil(area.radius / wide)) + 1
    dabs = max(1, int(math.ceil(long / wide)))   # stamps along a tile, each `wide` across
    swatch = kind.get("swatch") or ""
    copies, stamps = [], []
    if swatch:   # the rows: the area's direction (the stickers' axis, turned to it) + 90
        rows = (math.degrees(math.atan2(uy, ux)) + 90.0) % 180.0
        square = area.shape == "square"
        stamps.append(Stroke("texture", area.x, area.y, area.radius / HARD_EDGE, shape=area.shape, edge="hard",
                             dx=area.dx if square else 1.0, dy=area.dy if square else 0.0, texture=swatch, turn=rows,
                             clear=False))
    for j in range(-steps_v, steps_v + 1):
        for i in range(-steps_u, steps_u + 1):
            du, dv = (i + 0.5) * long, (j + 0.5) * wide
            cx, cy = area.x + du * ux + dv * vx, area.y + du * uy + dv * vy
            # a tile is laid when any of its corners lies in the area (the clip cuts the rest)
            corners = [(cx + a * ux + b * vx, cy + a * uy + b * vy) for a in (-long / 2, long / 2)
                       for b in (-wide / 2, wide / 2)]
            if all(foot.t2(x, y) >= 1.0 for x, y in corners) and foot.t2(cx, cy) >= 1.0:
                continue
            copies.append(CopyArea(cx, cy, wide / 2, src.x - cx, src.y - cy, turn, COPY_LAYERS, "square", area.dx,
                                   area.dy, kind["map"], within, area.mode == "add", group, along=long / 2))
            for k in range(0 if swatch else dabs):
                a = (k + 0.5) * long / dabs - long / 2
                stamps.append(Stroke("stamp", cx + a * ux, cy + a * uy, wide / 2 / HARD_EDGE, sx=src.x - cx,
                                     sy=src.y - cy, shape="square", edge="hard", dx=area.dx, dy=area.dy, clear=False))
    return copies, stamps


def expand_preset(area: PresetArea, lib: dict, group: int = 1, borders: dict | None = None,
                  hedgerows: dict | None = None) -> tuple[list[CopyArea], list[EraseArea], list, list]:
    """What a preset area lays, as (copies, erases, stamps, objects): a CopyArea per tile (its source square the
    kind's, round-robin from `seed`, clipped
    to the area, the fill rule in add mode, all of one `group`: the build gives each preset its own, so its tiles
    never thin each other along their joins while other areas' objects count), an EraseArea of the area's low cover
    in replace mode, and a stamp stroke per tile (the source square's ground picture). Tiles are TILE across, in
    rows along the area's dx, dy, centred on the area; a tile is laid when its middle lies in the area. With a
    border (area.border, from `borders`, default border_library()), the tiles are clipped half a BORDER_WIDTH inside
    the outline and expand_border's strips and band erase are added: the game's fields end at hedge feet and field
    edges, not in a hard line of crops. A FIELD kind (the library's [[field]] tables) is laid by expand_field
    instead of tiles, and its border also carries the map's hedgerow trees and fence (expand_hedgerow, from
    `hedgerows`, default hedgerow_library()): the objects returned last.

    The stamps reach past their tiles: a hard edge is full strength only out to HARD_EDGE of the radius and fades to
    nothing at it, so stamps of exactly a tile each left the ground underneath along every join (Preset D-Day,
    2026-10-11: a dark cross through each wheat square, 40 % darker than the tiles, a bright one on the sand). At
    TILE / 2 / HARD_EDGE a stamp is full over its whole tile and its fade lies over the next tile, where the later
    stamp paints full again, or past the area's edge, where it softens into the ground around."""
    from .brush import HARD_EDGE, Stroke
    if area.name not in lib:
        known = ", ".join(sorted(lib)) or "none"
        raise SceneryEditError(f"no ground preset is called {area.name!r} (the presets: {known})")
    kind = lib[area.name]
    objects: list = []
    if kind.get("type") == "field":
        copies, stamps = expand_field(area, kind, group)
    else:
        sources = kind["sources"]
        foot = area.footprint()
        n = math.hypot(area.dx, area.dy) or 1.0
        ux, uy = area.dx / n, area.dy / n          # along a row of tiles
        vx, vy = -uy, ux                           # across the rows
        steps = int(math.ceil(area.radius / TILE)) + 1
        within = (area.shape, area.x, area.y, area.radius, area.dx, area.dy)
        copies, stamps = [], []
        k = area.seed
        for j in range(-steps, steps + 1):
            for i in range(-steps, steps + 1):
                # tile middles at odd multiples of half a tile when the area is wider than one tile, else the middle
                cx = area.x + (i + 0.5) * TILE * ux + (j + 0.5) * TILE * vx if area.radius > TILE / 2 else area.x
                cy = area.y + (i + 0.5) * TILE * uy + (j + 0.5) * TILE * vy if area.radius > TILE / 2 else area.y
                if foot.t2(cx, cy) >= 1.0:
                    continue
                sx, sy = sources[k % len(sources)]
                k += 1
                copies.append(CopyArea(cx, cy, TILE / 2, sx - cx, sy - cy, 0.0, COPY_LAYERS, "square", area.dx,
                                       area.dy, kind["map"], within, area.mode == "add", group))
                stamps.append(Stroke("stamp", cx, cy, TILE / 2 / HARD_EDGE, sx=sx - cx, sy=sy - cy, shape="square",
                                     edge="hard", dx=area.dx, dy=area.dy, clear=False))
                if area.radius <= TILE / 2:
                    break
            if area.radius <= TILE / 2 and copies:
                break
    erases = []
    if area.mode == "replace":
        erases.append(EraseArea(area.x, area.y, area.radius, ("decal",), (LOW_COVER,), shape=area.shape, dx=area.dx,
                                dy=area.dy))
    if area.border != "none":   # the tiles stop short of the border's band; its strips and erase follow (expand_border)
        from dataclasses import replace as _with
        inner = (area.shape, area.x, area.y, max(area.radius - BORDER_WIDTH / 2, area.radius / 2), area.dx, area.dy)
        copies = [_with(c, within=inner) for c in copies]
        strips, band = expand_border(area, border_library() if borders is None else borders, group)
        copies += strips
        erases += band
        if kind.get("type") == "field":
            rows = hedgerow_library() if hedgerows is None else hedgerows
            objects = expand_hedgerow(area, rows.get(kind["map"]), area.seed + group)
    return copies, erases, stamps, objects


@dataclass(frozen=True)
class FieldBrush:
    """A dab of the field brush ([[fieldbrush]] in scenery.toml, MOD_FORMAT §8; the owner, 2026-10-14: "a field
    brush ... that modifies what's there", only the strip under it, round or square): the map's own fields under it
    turned into `look` (look_library). Only the fields change (expand_field_brush): their row stickers swap kind
    where they lie, their crops are laid anew from a real field of the look turned to their rows, and the ground
    picture under each sticker is stamped from that field. Hedges, fences, trees, the meadow and roads stay."""
    look: str
    x: float
    y: float
    radius: float
    shape: str = "round"   # round, or square (sides along dx, dy, `radius` from its middle to each side)
    dx: float = 1.0
    dy: float = 0.0
    seed: int = 0

    def footprint(self):
        from .brush import Footprint
        if self.shape == "square":
            return Footprint("square", self.x, self.y, self.radius, self.dx, self.dy)
        return Footprint("round", self.x, self.y, self.radius)


def parse_field_brushes(rows: list, where: str = "scenery.toml") -> list[FieldBrush]:
    out = []
    for k, row in enumerate(rows):
        extra = sorted(set(row) - {"look", "x", "y", "radius", "shape", "dx", "dy", "seed"})
        if extra:
            raise SceneryEditError(f"{where}: fieldbrush {k + 1}: unknown key {extra[0]!r}")
        look = row.get("look")
        if not isinstance(look, str) or not look.strip():
            raise SceneryEditError(f"{where}: fieldbrush {k + 1} has no look")
        shape = row.get("shape", "round")
        if shape not in ("round", "square"):
            raise SceneryEditError(f"{where}: fieldbrush {k + 1}: shape must be round or square")
        try:
            x, y, r = float(row["x"]), float(row["y"]), float(row["radius"])
            dx, dy = float(row.get("dx", 1.0)), float(row.get("dy", 0.0))
            seed = int(row.get("seed", 0))
        except KeyError as exc:
            raise SceneryEditError(f"{where}: fieldbrush {k + 1} has no {exc.args[0]}") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: fieldbrush {k + 1}: x, y, radius, dx, dy and seed must be "
                                   f"numbers") from None
        if not all(math.isfinite(v) for v in (x, y, r, dx, dy)) or not 0 < r <= ERASE_MAX:
            raise SceneryEditError(f"{where}: fieldbrush {k + 1}: the radius must be above 0 and at most "
                                   f"{ERASE_MAX:,.0f} map units")
        if shape == "square" and dx == 0.0 and dy == 0.0:
            raise SceneryEditError(f"{where}: fieldbrush {k + 1}: the square's direction dx, dy can't be 0, 0")
        out.append(FieldBrush(look.strip(), x, y, r, shape, dx, dy, seed))
    return out


@dataclass(frozen=True)
class CliffArea:
    """Cliff faces made of rock scans ([[cliffs]] in scenery.toml, MOD_FORMAT §8; the owner, 2026-10-17: "try ... the
    generation test with some of these rock faces. Automatically generating maybe inside of each other all together,
    mixed around ... on these mountain sides or cliff faces"): the steep ground inside the circle (x, y, radius, map
    units) covered with `types` (scans: their fronts turned to face downhill), mixed, `size` times their own size,
    overlapping (a scan every `spacing` times its width), leaned back toward the slope (`lean`: 0 upright, 1 square
    to the ground) and sunk by `sink` times their height. Laid by the build on the ground as built
    (rusemod.cliffs.cliff_layer)."""
    types: tuple
    x: float
    y: float
    radius: float
    size: tuple = (1.0, 2.0)
    steep: float = 30.0      # degrees: the least slope a scan stands on
    spacing: float = 0.6     # times a scan's width between neighbours (under 1: they overlap)
    lean: float = 0.5
    sink: float = 0.2
    seed: int = 0


def parse_cliffs(rows: list, where: str = "scenery.toml") -> list[CliffArea]:
    out = []
    keys = {"types", "x", "y", "radius", "size", "steep", "spacing", "lean", "sink", "seed"}
    for k, row in enumerate(rows):
        extra = sorted(set(row) - keys)
        if extra:
            raise SceneryEditError(f"{where}: cliffs {k + 1}: unknown key {extra[0]!r}")
        types = row.get("types")
        if not isinstance(types, list) or not types or not all(isinstance(t, str) and t.strip() for t in types):
            raise SceneryEditError(f"{where}: cliffs {k + 1}: types is a list of scenery types (the rock scans)")
        try:
            x, y, r = float(row["x"]), float(row["y"]), float(row["radius"])
            size = tuple(float(v) for v in row.get("size", (1.0, 2.0)))
            steep, spacing = float(row.get("steep", 30.0)), float(row.get("spacing", 0.6))
            lean, sink, seed = float(row.get("lean", 0.5)), float(row.get("sink", 0.2)), int(row.get("seed", 0))
        except KeyError as exc:
            raise SceneryEditError(f"{where}: cliffs {k + 1} has no {exc.args[0]}") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: cliffs {k + 1}: x, y, radius, size, steep, spacing, lean, sink and seed "
                                   f"must be numbers") from None
        if not all(math.isfinite(v) for v in (x, y, r)) or not 0 < r <= ERASE_MAX:
            raise SceneryEditError(f"{where}: cliffs {k + 1}: the radius must be above 0 and at most "
                                   f"{ERASE_MAX:,.0f} map units")
        if len(size) != 2 or not 0.05 <= size[0] <= size[1] <= 50:
            raise SceneryEditError(f"{where}: cliffs {k + 1}: size is [least, most], 0.05 to 50")
        if not (0.0 <= steep < 90.0 and 0.1 <= spacing <= 5.0 and 0.0 <= lean <= 1.0 and 0.0 <= sink <= 1.0):
            raise SceneryEditError(f"{where}: cliffs {k + 1}: steep is 0 to 90 degrees, spacing 0.1 to 5, lean and "
                                   f"sink 0 to 1")
        out.append(CliffArea(tuple(t.strip() for t in types), x, y, r, size, steep, spacing, lean, sink, seed))
    return out


SECTION_NAME = re.compile(r"^[a-z0-9_\-]{1,64}$")
SECTION_SIDE_MOST = 2000.0 * 260.0   # map units: a section's square at most 2 km a side (D-Day's tiles: ~280 m)
SECTION_PLACES_MOST = 200000         # places one [[section]] lists at most


@dataclass(frozen=True)
class SectionArea:
    """A square of a map's scenery copied ONCE and placed again many times ([[section]] in scenery.toml, MOD_FORMAT
    §8; the owner, 2026-10-17: the game's own stickers, plants and stones up close on generated ground; a town's
    blocks copied and put back together): what `layers` (COPY_LAYERS, trees, props) lay in the square of side `side`
    round (sx, sy) on the map as it comes in (or on `source`, another map's shipped scenery), each object kept at its
    place about the square's middle and at the levels its shipped copy is drawn at; placed with that middle at each of
    `places` ((x, y, turn): map units, and degrees as NewObject.turn), every place a reference to the one copy, as the
    shipped maps place their landscape tiles (D-Day: tiles of about 280 m, each placed 37 to 56 times turned; 15.2
    million placements in 10 MB). Written by add_sections."""
    name: str
    sx: float
    sy: float
    side: float
    places: tuple            # ((x, y, turn), ...)
    layers: tuple = COPY_LAYERS
    source: str = ""
    objects: tuple = ()      # instead of a square copied: its objects listed, each (type, x, y, turn, size, levels,
                             # height) about its middle (map units, degrees; levels as NewObject.levels, 0 = all;
                             # height 0 = its size): a section made elsewhere (the dressing a mod generates)

    def new_objects(self) -> list:
        """Its listed objects as NewObjects (drawn only: solid = false)."""
        return [NewObject(t, x, y, turn, size, solid=False, levels=lv, height=hgt)
                for t, x, y, turn, size, lv, hgt in self.objects]

    def copy_area(self, group: int = 0) -> "CopyArea":
        """What copy_objects reads for it: the square, its middle laid at (0, 0) (the copy's own coordinates), its
        objects kept off by nothing but each other's fill rule within `group` (so all of the square comes)."""
        return CopyArea(0.0, 0.0, self.side / 2, self.sx, self.sy, layers=self.layers, shape="square",
                        source=self.source, group=group)


def _section_objects(rows, where: str, name: str) -> tuple:
    """A [[section]]'s `objects`: each [type, x, y, turn, size, levels] or with a height after them."""
    if not isinstance(rows, list) or not rows or len(rows) > BLOCK_MOST:
        raise SceneryEditError(f"{where}: section {name}: objects is a list of [type, x, y, turn, size, levels] or "
                               f"[..., height] (1 to {BLOCK_MOST:,})")
    out = []
    for r in rows:
        try:
            if not isinstance(r, list) or len(r) not in (6, 7) or not isinstance(r[0], str) or not r[0].strip():
                raise ValueError
            t, x, y, turn, size, lv = r[0].strip(), float(r[1]), float(r[2]), float(r[3]), float(r[4]), int(r[5])
            hgt = float(r[6]) if len(r) == 7 else 0.0
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: section {name}: each object is [type, x, y, turn, size, levels] or "
                                   f"[..., height] (found {r!r})") from None
        if not all(math.isfinite(v) for v in (x, y, turn, size, hgt)) or not 0.05 <= size <= 50 \
                or not 0 <= lv <= ALL_TIERS or not 0.0 <= hgt <= 50:
            raise SceneryEditError(f"{where}: section {name}: an object's size is 0.05 to 50, its levels 0 to "
                                   f"{ALL_TIERS} and its height 0 to 50 ({r!r})")
        out.append((t, x, y, turn, size, lv, hgt))
    return tuple(out)


def parse_sections(rows: list, where: str = "scenery.toml") -> list[SectionArea]:
    out = []
    keys = {"name", "sx", "sy", "side", "places", "layers", "map", "objects"}
    for k, row in enumerate(rows):
        extra = sorted(set(row) - keys)
        if extra:
            raise SceneryEditError(f"{where}: section {k + 1}: unknown key {extra[0]!r}")
        name = row.get("name", "")
        if not isinstance(name, str) or not SECTION_NAME.match(name):
            raise SceneryEditError(f"{where}: section {k + 1}: name is 1 to 64 of a-z, 0-9, _ and -")
        objects = _section_objects(row["objects"], where, name) if "objects" in row else ()
        if objects and any(key in row for key in ("sx", "sy", "side", "layers", "map")):
            raise SceneryEditError(f"{where}: section {name}: a section lists its objects or copies a square "
                                   f"(sx, sy, side), not both")
        try:
            sx, sy, side = (0.0, 0.0, 0.0) if objects else (float(row["sx"]), float(row["sy"]), float(row["side"]))
        except KeyError as exc:
            raise SceneryEditError(f"{where}: section {name} has no {exc.args[0]}") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: section {name}: sx, sy and side must be numbers") from None
        if not objects and (not all(math.isfinite(v) for v in (sx, sy, side)) or not 0 < side <= SECTION_SIDE_MOST):
            raise SceneryEditError(f"{where}: section {name}: side must be above 0 and at most "
                                   f"{SECTION_SIDE_MOST:,.0f} map units")
        layers = row.get("layers", list(COPY_LAYERS))
        if not isinstance(layers, list) or not layers or any(g not in FIELD_COPY_LAYERS for g in layers):
            raise SceneryEditError(f"{where}: section {name}: layers is a list of {', '.join(FIELD_COPY_LAYERS)}")
        source = row.get("map", "")
        if not isinstance(source, str):
            raise SceneryEditError(f"{where}: section {name}: map is a map pack's name")
        places = row.get("places")
        if not isinstance(places, list) or not places or len(places) > SECTION_PLACES_MOST:
            raise SceneryEditError(f"{where}: section {name}: places is a list of [x, y] or [x, y, turn] (1 to "
                                   f"{SECTION_PLACES_MOST:,})")
        got = []
        for p in places:
            try:
                if not isinstance(p, list) or len(p) not in (2, 3):
                    raise ValueError
                x, y, turn = float(p[0]), float(p[1]), float(p[2]) if len(p) == 3 else 0.0
            except (TypeError, ValueError):
                raise SceneryEditError(f"{where}: section {name}: each place is [x, y] or [x, y, turn], numbers "
                                       f"(found {p!r})") from None
            if not all(math.isfinite(v) for v in (x, y, turn)):
                raise SceneryEditError(f"{where}: section {name}: a place isn't a finite number ({p!r})")
            got.append((x, y, turn))
        out.append(SectionArea(name, sx, sy, side, tuple(got), tuple(dict.fromkeys(layers)), source.strip(), objects))
    return out


def sections_toml(sections: list[SectionArea], header: str = "") -> str:
    """[[section]] tables for a mod's scenery.toml (parse_sections reads them back), places 3 to a line."""
    out = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for s in sections:
        out += ["[[section]]", f"name = {json.dumps(s.name)}"]
        if s.objects:
            out.append("objects = [")
            out += [f"  [{json.dumps(t)}, {x:.1f}, {y:.1f}, {turn:.1f}, {size:.3f}, {lv}"
                    + (f", {hgt:.3f}]," if hgt else "],") for t, x, y, turn, size, lv, hgt in s.objects]
            out.append("]")
        else:
            out += [f"sx = {s.sx!r}", f"sy = {s.sy!r}", f"side = {s.side!r}"]
        if s.layers != COPY_LAYERS and not s.objects:
            out.append("layers = [" + ", ".join(json.dumps(g) for g in s.layers) + "]")
        if s.source:
            out.append(f"map = {json.dumps(s.source)}")
        rows = [f"[{x:.1f}, {y:.1f}, {t:.1f}]" for x, y, t in s.places]
        out.append("places = [")
        out += ["  " + ", ".join(rows[i:i + 3]) + "," for i in range(0, len(rows), 3)]
        out += ["]", ""]
    return "\n".join(out)


@dataclass(frozen=True)
class FieldCopy:
    """A real field of the map laid again whole somewhere else ([[fieldcopy]] in scenery.toml, MOD_FORMAT §8): the
    ploppable field, for a blank map (the owner, 2026-10-15). Eugen built his fields as prefab blocks and placed the
    same block several times, each turned its own way; the ground picture under each was
    painted place by place. So the copy takes the field under (sx, sy) whole: everything inside its outline and a
    `border` (map units) round it (rows, crops, fences, hay, carts, trees, the hedge's foot) and the picture under
    it, turned `turn` degrees round its middle and laid with that middle at (x, y) (expand_field_copy)."""
    x: float
    y: float
    sx: float
    sy: float
    turn: float = 0.0
    border: float = 6.0 * 260.0


def parse_field_copies(rows: list, where: str = "scenery.toml") -> list[FieldCopy]:
    out = []
    for k, row in enumerate(rows):
        extra = sorted(set(row) - {"x", "y", "sx", "sy", "turn", "border"})
        if extra:
            raise SceneryEditError(f"{where}: fieldcopy {k + 1}: unknown key {extra[0]!r}")
        try:
            x, y, sx, sy = float(row["x"]), float(row["y"]), float(row["sx"]), float(row["sy"])
            turn, border = float(row.get("turn", 0.0)), float(row.get("border", 6.0 * 260.0))
        except KeyError as exc:
            raise SceneryEditError(f"{where}: fieldcopy {k + 1} has no {exc.args[0]} (x, y: where it goes; sx, sy: a "
                                   f"point in the field it copies)") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: fieldcopy {k + 1}: x, y, sx, sy, turn and border must be numbers") from None
        if not all(math.isfinite(v) for v in (x, y, sx, sy, turn, border)) or not 0.0 <= border <= 50.0 * 260.0:
            raise SceneryEditError(f"{where}: fieldcopy {k + 1}: border must be 0 to 13,000 map units (50 m)")
        out.append(FieldCopy(x, y, sx, sy, turn, border))
    return out


FIELD_KINDS = ("Labourage", "Paille")   # the row stickers a field is made of, every decor set


def field_under(sc: Scenery, x: float, y: float, halves: dict | None = None) -> list | None:
    """The field (brush_fields' list of its row stickers) at (x, y): the biggest whose squares hold the point, else
    the one whose sticker's middle is nearest within 15 m (a field's middle can fall between its stickers), else
    None."""
    fields = brush_fields(FieldBrush("", x, y, 15.0 * 260.0), {"field_kinds": FIELD_KINDS}, sc, halves)

    def holds(field):
        for _s, m, _k, h in field:
            t = math.atan2(m[4], m[0])
            u = (x - m[3]) * math.cos(t) + (y - m[7]) * math.sin(t)
            v = -(x - m[3]) * math.sin(t) + (y - m[7]) * math.cos(t)
            if abs(u) <= h and abs(v) <= h:
                return True
        return False
    holding = [f for f in fields if holds(f)]
    if holding:
        return max(holding, key=len)
    if not fields:
        return None
    return min(fields, key=lambda f: min(math.hypot(m[3] - x, m[7] - y) for _s, m, _k, _h in f))


def expand_field_copy(fc: FieldCopy, sc: Scenery, group: int = 0, halves: dict | None = None,
                      buildings: dict | None = None):
    """What a field copy does to the map whose scenery is `sc` (as it ships): (erases, copies, stamps, notes). The
    field is brush_fields' field under (sx, sy) (the biggest, where two meet there); every point within `border` of
    one of its row stickers' squares is copied, turned `turn` round the field's middle onto (x, y): first what was
    there is erased (every kind, square by square), then every object standing there in the source is copied
    (CopyArea, all layers, landing only on the grown squares), then the picture (a hard stamp per grown square,
    turned). Buildings aren't copied, so with `buildings` (building_table) what stood raised on one of the source's
    (within BUILDING_REACH of its model box: wall plants, window boxes) is left out too: copied alone it floated (the
    blank farm's field 3, flowers 3-5 m up, 2026-10-16). Nothing is done where there's no field at (sx, sy)."""
    from .brush import Stroke
    field = field_under(sc, fc.sx, fc.sy, halves)
    if field is None:
        return [], [], [], [f"field copy to ({fc.x:.0f}, {fc.y:.0f}): no field at ({fc.sx:.0f}, {fc.sy:.0f}), "
                            f"nothing done"]
    xs = [m[3] for _s, m, _k, _h in field]
    ys = [m[7] for _s, m, _k, _h in field]
    fx, fy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0   # its middle
    c, s = math.cos(math.radians(fc.turn)), math.sin(math.radians(fc.turn))

    def there(px, py):   # a source point's place in the copy
        ox, oy = px - fx, py - fy
        return fc.x + ox * c - oy * s, fc.y + ox * s + oy * c
    grown = []   # each square in the copy: (x, y, half + border, dx, dy)
    for _s, m, _k, half in field:
        t = math.atan2(m[4], m[0]) + math.radians(fc.turn)
        x, y = there(m[3], m[7])
        grown.append((x, y, half + fc.border, math.cos(t), math.sin(t)))
    erases = [EraseArea(x, y, h, ERASE_DEFAULT, (), shape="square", dx=dx, dy=dy) for x, y, h, dx, dy in grown]
    reach = max(math.hypot(x - fc.x, y - fc.y) + h * math.sqrt(2.0) for x, y, h, _dx, _dy in grown)
    on = ()
    if buildings:   # the source's buildings round the field, which the copy leaves behind
        pad = max(h for _s, _m, _k, h in field) + fc.border + BUILDING_REACH
        box = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
        on = tuple((cx, cy, hu, hv, ux, uy, BUILDING_REACH)
                   for _t, cx, cy, hu, hv, ux, uy, _gap in building_rects(sc, buildings, box))
    copies = [CopyArea(fc.x, fc.y, reach, fx - fc.x, fy - fc.y, fc.turn, FIELD_COPY_LAYERS, "square", 1.0, 0.0, "", None,
                       False, group, near=tuple(grown), near_r=max(h for _x, _y, h, _dx, _dy in grown),
                       src_avoid=on)]
    stamps = []
    for x, y, h, dx, dy in grown:   # the picture: what lies under each grown square in the source, turned
        qx, qy = fx + (x - fc.x) * c + (y - fc.y) * s, fy - (x - fc.x) * s + (y - fc.y) * c
        stamps.append(Stroke("stamp", x, y, h, sx=qx - x, sy=qy - y, turn=fc.turn, clear=False, shape="square",
                             edge="hard", dx=dx, dy=dy))
    notes = [f"field copy: the field of {len(field)} row sticker(s) round ({fx:.0f}, {fy:.0f}) laid at "
             f"({fc.x:.0f}, {fc.y:.0f}) turned {fc.turn:.0f} degrees, with {fc.border / 260.0:.0f} m round it"]
    return erases, copies, stamps, notes


def look_library(path=None) -> dict[str, dict]:
    """The field brush's looks, by name: {"description", "map" (whose fields they are measured on and copied from),
    "field_kinds" (name prefixes of the map's field stickers the brush swaps), "crops" (name prefixes of the crop
    plants it replaces), "stickers" [(kind, share)] (the row stickers it lays), "sources" [(x, y, the rows' facing
    in degrees, inside along, inside across, its crops' turn against that facing, its ground colour "#rrggbb" or "",
    its row sticker kind or "")] (real fields of the look: a brushed field takes one source's colour, row sticker
    kind and crops, so it is that field near and far), "colour" ("#rrggbb": the look's ground colour on the map, for
    a source without its own; "" none), "hay" (whether the map's own fields of the look carry hay; without, the hay
    and carts on a field it makes go), "trees_within" (the deepest, metres from a field's edge, the look's fields
    carry trees; None: any depth), "masks" ([{detail-ring flag: count}] per source: its row pieces')}. From the
    [[look]] tables of ground_presets.toml beside this module."""
    import tomllib
    from pathlib import Path
    file = Path(path) if path else Path(__file__).with_name(PRESET_FILE)
    data = tomllib.loads(file.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for row in data.get("look", []):
        name = str(row.get("name", "")).strip()
        sources = []
        for s in row.get("sources", []):
            try:
                nums = tuple(float(v) for v in s[:6])
                words = tuple(str(v) for v in s[6:])
            except (TypeError, ValueError):
                nums, words = (), ("", "", "")
            if len(nums) not in (5, 6) or len(words) > 2 or nums[3] <= 0 or nums[4] <= 0 or \
                    (len(nums) == 5 and words):
                raise SceneryEditError(f"{file.name}: look {name!r}: a source is [x, y, facing, inside along, inside "
                                       f"across(, its crops' turn against the facing(, its colour, its row sticker "
                                       f"kind))], both sizes above 0")
            sources.append(nums + (0.0,) * (6 - len(nums)) + words + ("",) * (2 - len(words)))
        stickers = [(str(s[0]), float(s[1])) for s in row.get("stickers", [])]
        if not name or not row.get("map") or not sources or not stickers:
            raise SceneryEditError(f"{file.name}: a look needs a name, a map, stickers and sources")
        masks = []
        for text in row.get("masks", []):   # per source: "flag:count ..." of its row pieces' detail-ring flags
            got = {}
            for part in str(text).split():
                k, _sep, n = part.partition(":")
                got[int(k)] = int(n)
            masks.append(got)
        tw = row.get("trees_within")
        out[name] = {"description": str(row.get("description", "")), "map": str(row["map"]),
                     "field_kinds": tuple(row.get("field_kinds", ["Labourage", "Paille"])),
                     "crops": tuple(row.get("crops", ["Champs_"])), "stickers": stickers,
                     "sources": sources, "colour": str(row.get("colour", "")), "hay": bool(row.get("hay", True)),
                     "trees_within": float(tw) if tw is not None else None, "masks": masks}
    return out


def building_gaps(path=None) -> tuple[float, dict[str, float]]:
    """(default, {building type's short name: gap}) in metres: how far from its walls (its model's box) the field
    brush keeps new standing crops off each building type, as the map keeps its own (the [building_gaps] table of
    ground_presets.toml beside this module: D-Day's closest quarter of each type's placements beside standing
    crops); a type not listed takes the default. (0.0, {}) when the file has none."""
    import tomllib
    from pathlib import Path
    file = Path(path) if path else Path(__file__).with_name(PRESET_FILE)
    table = dict(tomllib.loads(file.read_text(encoding="utf-8")).get("building_gaps", {}))
    default = float(table.pop("default", 0.0))
    return default, {str(k): float(v) for k, v in table.items()}


def building_rects(sc: "Scenery", buildings: dict, box: tuple) -> list:
    """The buildings of `buildings` (building_table) whose middles lie in `box` (x0, y0, x1, y1), each once, as
    (type, x, y, half u, half v, ux, uy, gap): its model's box through its placement (middle, half sizes along its own
    x axis (ux, uy) and square to it) and its type's gap: CopyArea.avoid's rectangles with the type in front."""
    syms = {i for i, n in enumerate(sc.names) if n in buildings}
    out, seen = [], set()
    for sym, m, _mask in walk_levels(sc, box, syms):
        key = (sym, round(m[3], 1), round(m[7], 1))
        if key in seen:
            continue
        seen.add(key)
        x0, y0, x1, y1, gap = buildings[sc.names[sym]]
        sx, sy = math.hypot(m[0], m[4]), math.hypot(m[1], m[5])
        if not sx or not sy:
            continue
        bx, by = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        out.append((sc.names[sym], m[3] + m[0] * bx + m[1] * by, m[7] + m[4] * bx + m[5] * by, (x1 - x0) / 2.0 * sx,
                    (y1 - y0) / 2.0 * sy, m[0] / sx, m[4] / sx, gap))
    return out


def building_table(names: list, descs: dict, box_of, gaps: tuple | None = None) -> dict:
    """{building type: (x0, y0, x1, y1, gap)}, map units, for expand_field_brush: each of the map's building types
    (`names`, by their descriptors `descs`) with its model's box as the mesh packs list it (`box_of(model)` -> (min
    x, y, z, max x, y, z) or None: models.Library.box; a composite's models together) and the gap new standing crops
    keep from it (`gaps`: building_gaps(), read when None). A type whose model isn't found is left out."""
    default, by_type = gaps if gaps is not None else building_gaps()
    out = {}
    for n in names:
        d = descs.get(n)
        if d is None or d.group != "building":
            continue
        got = [b for b in (box_of(m) for m in (d.models or ((d.model,) if d.model else ()))) if b]
        if not got:
            continue
        gap = by_type.get(n.rsplit("/", 1)[-1], default) * 260.0   # 260 map units a metre
        out[n] = (min(b[0] for b in got), min(b[1] for b in got), max(b[3] for b in got), max(b[4] for b in got), gap)
    return out


FIELD_HALF = 2048.0        # a field sticker's square, middle to side at size 1 (MinExtent/MaxExtent -2048..2048 in
                           # every decor set: 15.75 m pieces); `halves` overrides it per type
BRUSH_ANGLE = 12.0         # degrees: stickers whose facings are this alike are one field's rows
# Two row stickers of one facing are one field when their middles lie under these many (half + half) apart along
# the rows and across them. Measured on D-Day's 150,318 row stickers (2026-10-15): the
# nearest one along the rows lies 0.8-1.1 away (their squares just meet), across 0.6-0.9 (rows overlap), and a second
# bump across at 1.1-1.3 is the plot on the far side of a hedge or a track.
FIELD_ALONG = 1.12
FIELD_ACROSS = 1.0
FIELD_REACH = 400.0 * 260.0  # the farthest a field's stickers are looked for round the brush
# A field's picture stamp reaches this much past its row sticker's square: a hard stroke is full to HARD_EDGE (0.85)
# and fades out past it, so it is full to about the sticker's own edge, and closes the gaps between a field's squares
# (up to 0.12 of two halves along the rows, wedges where facings differ) that left the old colour in lines through
# the field, seen from above 2026-10-15. The field's one map makes the overlaps read the same spot.
FIELD_STAMP = 1.15
SMALL_FIELD = 4   # whole row stickers: a field of fewer is a fragment between bigger plots, painted as the dab's biggest

# What stands on a field besides its crops (rusemod.maplayout reads the same): hay, and the farm machines.
FARM_HAY = ("Foin",)
FARM_MACHINES = ("Charrette", "Tracteur", "Remorque", "Faucheuse", "Moissonneuse", "Herse", "Charrue", "Botteleuse")
TRACTORS = ("Tracteur",)
# Hay and machines left standing on a field the brush changes keep a harvested patch round them, as Eugen lays one
# (D-Day, 2026-10-15; the owner's E: bales left in a full field of standing wheat): his crops round hay on wheat
# plots are 97% laid harvested within 2 m, half-way back to the plot's own share by 4.1 m; round a machine with no
# hay near it on a wheat plot no standing crop at all (measured on D-Day, 2026-10-15). Harvested,
# the wheat is squashed to a quarter and sunk 0.13 m (131,257 of the 314,412 harvested Champs_Bles within 3 m of hay;
# next half height, 0.26 m down), the green crop squashed to about half; the light green and border
# crops he leaves standing.
HAY_PATCH = 4.0 * 260.0
HARVESTED = {"Champs_Bles": (0.25, -0.13 * 260.0), "Champs_Verts": (0.48, 0.0)}   # height (up scale), lift
# A look without hay (look["hay"] false: D-Day's 1,310 ploughed plots carry none): the hay and carts on a field it
# makes go, and its tractors past this far in (the 281 machines on D-Day's ploughed plots are tractors within 3 m of
# the edge).
NO_HAY_MACHINE_DEPTH = 3.0 * 260.0
# Eugen's harvested crops round hay and machines are theirs out to here: on D-Day's wheat plots the share of crops laid
# harvested falls from 97% at the hay to the plot's own (about 30%) by 7 m (2026-10-15). Within it the
# brush keeps Eugen's harvested ground as he shaped it, a block along the rows (E's cluster: 25 x 20 m), not circles:
# a new crop within HARVESTED_SPOT of one of his harvested crops is laid as that crop is (its height, its sink).
HAY_REACH = 7.0 * 260.0
HARVESTED_SPOT = 1.0 * 260.0   # (a clump's 16 crops stand 0.75 m apart: 1 m round each fills his block solid)
# A field's dressing besides its rows and crops is its look too (the owner's 2026-10-15 shots: R up close littered with
# the ploughed field's stones, Q with its old grass patches, W's old hedgerow trees in the middle of new wheat): from
# FIELD_EDGE in, its low plants, stones, ground stickers and trees are the source field's, as Eugen dressed it. Along
# the edge they stay the map's: D-Day's low plants stand 2,000-3,800 a hectare within 2 m of a field's edge (the hedge
# foot) and 150-800 inside, its wheat fields' trees 34 a hectare there and none past 6 m.
FIELD_EDGE = 2.0 * 260.0
DRESSING_LAYERS = ("stickers", "plants", "stones", "trees")


class FieldInside:
    """Whether a point lies at least `edge` inside the union of a field's squares (x, y, half, facing radians): its
    middle in a square and a ring of 12 points `edge` round it too. Called (x, y), or (x, y, reach) as an erase area's
    mask (EraseArea.mask)."""

    def __init__(self, squares, edge: float):
        self.squares = [(x, y, h, math.cos(t), math.sin(t)) for x, y, h, t in squares]
        self.edge = edge
        self.cell = 2.0 * max((h for _x, _y, h, _c, _s in self.squares), default=1.0)
        self.grid: dict = {}
        for k, (x, y, h, _c, _s) in enumerate(self.squares):
            r = h * 1.4143
            for i in range(int((x - r) // self.cell), int((x + r) // self.cell) + 1):
                for j in range(int((y - r) // self.cell), int((y + r) // self.cell) + 1):
                    self.grid.setdefault((i, j), []).append(k)
        self.ring = [(math.cos(k * math.pi / 6), math.sin(k * math.pi / 6)) for k in range(12)]

    def holds(self, x: float, y: float) -> bool:
        """Whether (x, y) lies in one of the squares."""
        for k in self.grid.get((int(x // self.cell), int(y // self.cell)), ()):
            cx, cy, h, c, s = self.squares[k]
            if abs((x - cx) * c + (y - cy) * s) <= h and abs(-(x - cx) * s + (y - cy) * c) <= h:
                return True
        return False

    def __call__(self, x: float, y: float, _reach: float = 0.0) -> bool:
        return self.holds(x, y) and all(self.holds(x + self.edge * c, y + self.edge * s) for c, s in self.ring)


OUTLINE_CELL = 160.0           # map units a cell of a field's painted outline: the finest picture's pixel (61.5 cm)
OUTLINE_REACH = 3.0 * 260.0    # how far past its row stickers' squares a field's paint may reach
OUTLINE_COLOUR = 45.0          # how far (RGB distance) a pixel may be from the field's own median colour


def field_outline(squares: list, picture, cell: float = OUTLINE_CELL, reach: float = OUTLINE_REACH,
                  tolerance: float = OUTLINE_COLOUR) -> tuple:
    """A field's PAINTED outline, as the map's own ground picture draws it (`picture`: (x, y) -> rgb or None, the
    finest level), for a stamp's clip (brush.Stroke.clip): from the field's row sticker squares (`squares`: (x, y,
    half, facing radians)), every cell of `cell` map units reachable from the squares' middles through cells of the
    field's own colour (within `tolerance` of the median under the squares) and inside the squares grown by `reach`,
    plus the holes that leaves inside (a shadow, a patch: still the field). A dark boundary line (the hedge's foot,
    a track) stops it, so the field's paint ends where the map's own did, and the line stays. () when the picture
    has nothing there. Returns (x0, y0, cell, columns, rows, bytes)."""
    if not squares:
        return ()
    grown = [(x, y, h + reach, math.cos(t), math.sin(t)) for x, y, h, t in squares]
    x0 = min(x - h * 1.4143 for x, _y, h, _c, _s in grown)
    x1 = max(x + h * 1.4143 for x, _y, h, _c, _s in grown)
    y0 = min(y - h * 1.4143 for _x, y, h, _c, _s in grown)
    y1 = max(y + h * 1.4143 for _x, y, h, _c, _s in grown)
    x0, y0 = math.floor(x0 / cell) * cell, math.floor(y0 / cell) * cell
    w, h = int(math.ceil((x1 - x0) / cell)), int(math.ceil((y1 - y0) / cell))
    near = [[] for _ in range(w * h)]   # (the grown squares reaching each cell, by their boxes)
    for k, (x, y, r, _c, _s) in enumerate(grown):
        e = r * 1.4143
        for j in range(max(0, int((y - e - y0) // cell)), min(h, int((y + e - y0) // cell) + 1)):
            for i in range(max(0, int((x - e - x0) // cell)), min(w, int((x + e - x0) // cell) + 1)):
                near[j * w + i].append(k)

    def in_grown(i, j):
        px, py = x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell
        for k in near[j * w + i]:
            x, y, r, c, s = grown[k]
            if abs((px - x) * c + (py - y) * s) <= r and abs(-(px - x) * s + (py - y) * c) <= r:
                return True
        return False
    colour: dict = {}

    def col(i, j):
        got = colour.get((i, j), False)
        if got is False:
            got = colour[(i, j)] = picture(x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell)
        return got
    samples = []
    for x, y, half, t in squares:
        for a, b in ((0, 0), (-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
            px = x + (a * math.cos(t) - b * math.sin(t)) * half
            py = y + (a * math.sin(t) + b * math.cos(t)) * half
            c = picture(px, py)
            if c is not None:
                samples.append(c)
    if not samples:
        return ()
    ref = [sorted(c[q] for c in samples)[len(samples) // 2] for q in range(3)]
    tol2 = tolerance * tolerance

    def own(i, j):
        c = col(i, j)
        return c is not None and sum((c[q] - ref[q]) ** 2 for q in range(3)) <= tol2 and in_grown(i, j)
    inside = bytearray(w * h)
    todo = []
    for x, y, _half, _t in squares:
        i, j = int((x - x0) // cell), int((y - y0) // cell)
        if 0 <= i < w and 0 <= j < h and not inside[j * w + i] and own(i, j):
            inside[j * w + i] = 1
            todo.append((i, j))
    while todo:
        i, j = todo.pop()
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= a < w and 0 <= b < h and not inside[b * w + a] and own(a, b):
                inside[b * w + a] = 1
                todo.append((a, b))
    if not any(inside):
        return ()
    # the holes: cells the outside can't reach without crossing the field
    outside = bytearray(w * h)
    todo = [(i, j) for i in range(w) for j in (0, h - 1)] + [(i, j) for j in range(h) for i in (0, w - 1)]
    for i, j in todo:
        outside[j * w + i] = 0 if inside[j * w + i] else 1
    todo = [(i, j) for i, j in todo if outside[j * w + i]]
    while todo:
        i, j = todo.pop()
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= a < w and 0 <= b < h and not outside[b * w + a] and not inside[b * w + a]:
                outside[b * w + a] = 1
                todo.append((a, b))
    bits = bytes(1 if inside[k] or (not outside[k] and in_grown(k % w, k // w)) else 0 for k in range(w * h))
    return (x0, y0, cell, w, h, bits)


def _stamp_rect(x: float, y: float, half: float, t: float, squares: list) -> tuple:
    """(middle x, y, half across, half along) of the field brush's picture stamp on a row sticker's square (middle
    x, y, `half`, facing t radians): FIELD_STAMP of its half past each side beyond which another of its field's
    squares (`squares`: (x, y, half, facing)) lies in line (along the rows or across them, within 1.3 of the two
    halves: its neighbours), its own edge on every other side (the field's outline)."""
    c, s = math.cos(t), math.sin(t)
    ext = {"+u": half, "-u": half, "+v": half, "-v": half}
    for qx, qy, qh, _qt in squares:
        du, dv = (qx - x) * c + (qy - y) * s, -(qx - x) * s + (qy - y) * c
        if du == 0.0 and dv == 0.0:
            continue
        reach, side = (half + qh) * 1.3, (half + qh) * 0.5
        if abs(dv) < side and 0.0 < abs(du) < reach:
            ext["+u" if du > 0 else "-u"] = half * FIELD_STAMP
        if abs(du) < side and 0.0 < abs(dv) < reach:
            ext["+v" if dv > 0 else "-v"] = half * FIELD_STAMP
    hu, hv = (ext["+u"] + ext["-u"]) / 2.0, (ext["+v"] + ext["-v"]) / 2.0
    mu, mv = (ext["+u"] - ext["-u"]) / 2.0, (ext["+v"] - ext["-v"]) / 2.0
    return x + mu * c - mv * s, y + mu * s + mv * c, hv, hu


def _facing(m) -> float:
    return math.degrees(math.atan2(m[4], m[0])) % 180.0


def _mean_facing(group: list) -> float:
    c = sum(math.cos(math.radians(2 * _facing(m))) for _s, m, _k in group)
    s = sum(math.sin(math.radians(2 * _facing(m))) for _s, m, _k in group)
    return (math.degrees(math.atan2(s, c)) / 2) % 180.0


def _cut(name: str) -> str:
    """A row sticker's cut: "triangle" or "demi" (the pieces the map lays at a field's corners and ends), else ""."""
    short = name.rsplit("/", 1)[-1]
    return next((c for c in ("triangle", "demi") if short.endswith("_" + c)), "")


def _alike(a: float, b: float) -> bool:
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d) <= BRUSH_ANGLE


def sticker_half(sc: Scenery, sym: int, m, halves: dict | None = None) -> float:
    """A placed field sticker's square, middle to side (map units): its type's half extent times its size."""
    return (halves or {}).get(sc.names[sym], FIELD_HALF) * math.hypot(m[0], m[4])


def brush_fields(brush: "FieldBrush", look: dict, sc: Scenery, halves: dict | None = None) -> list[list]:
    """The WHOLE fields a field brush dab touches (the owner, 2026-10-15: Eugen's field is its prefab's stickers and
    the ground painted under the whole field, so the brush changes whole fields): each field is the stickers of one
    facing joined square to square from those whose middles lie under the brush (within FIELD_ALONG and FIELD_ACROSS
    of their sizes: not across a hedge or a track), so its shape is the union of its own stickers' squares, as
    Eugen's prefab laid them; with them any plot lying wholly inside them. Each sticker
    (name index, transform, LOD mask, its half size). [] when no field sticker lies under the brush."""
    foot = brush.footprint()
    x0, x1, y0, y1 = foot.box()
    short = [n.rsplit("/", 1)[-1] for n in sc.names]
    syms = {i for i, n in enumerate(short) if n.startswith(tuple(look["field_kinds"]))}
    found: dict = {}
    for sym, m, mask in walk_levels(sc, (x0 - FIELD_REACH, y0 - FIELD_REACH, x1 + FIELD_REACH, y1 + FIELD_REACH), syms):
        key = (sym, round(m[3], 1), round(m[7], 1))
        if key in found:
            found[key][2] |= mask
        else:
            found[key] = [sym, m, mask, sticker_half(sc, sym, m, halves)]
    pts = list(found.values())
    if not pts:
        return []
    cell = 2.0 * max(p[3] for p in pts)
    grid: dict = {}
    for k, p in enumerate(pts):
        grid.setdefault((int(p[1][3] // cell), int(p[1][7] // cell)), []).append(k)

    def joined(a, b) -> bool:
        pa, pb = pts[a], pts[b]
        if not _alike(_facing(pa[1]), _facing(pb[1])):
            return False
        t = math.radians(_facing(pa[1]))
        ux, uy = math.cos(t), math.sin(t)
        dx, dy = pb[1][3] - pa[1][3], pb[1][7] - pa[1][7]
        s = pa[3] + pb[3]
        return abs(dx * ux + dy * uy) < FIELD_ALONG * s and abs(-dx * uy + dy * ux) < FIELD_ACROSS * s

    seeds = [k for k, p in enumerate(pts) if foot.t2(p[1][3], p[1][7]) < 1.0]
    taken: set = set()
    fields = []
    for s in seeds:
        if s in taken:
            continue
        todo, field = [s], []
        taken.add(s)
        while todo:
            a = todo.pop()
            field.append(tuple(pts[a]))
            gx, gy = int(pts[a][1][3] // cell), int(pts[a][1][7] // cell)
            for i in (gx - 1, gx, gx + 1):
                for j in (gy - 1, gy, gy + 1):
                    for b in grid.get((i, j), ()):
                        if b not in taken and joined(a, b):
                            taken.add(b)
                            todo.append(b)
        fields.append(field)
    # a plot lying wholly inside those fields (every sticker's middle in their squares: a corner or headland piece, a
    # stray sticker laid at another facing, one or two stickers each) is part of them and changes with them (seven
    # such straw plots stayed straw inside a field made ploughed: the bands in Q, the owner's 2026-10-15 shots)
    if fields:
        sq = [(p[1][3], p[1][7], p[3], math.radians(_facing(p[1]))) for f in fields for p in f]

        def inside(k) -> bool:
            x, y = pts[k][1][3], pts[k][1][7]
            return any(abs((x - cx) * math.cos(t) + (y - cy) * math.sin(t)) < h
                       and abs(-(x - cx) * math.sin(t) + (y - cy) * math.cos(t)) < h for cx, cy, h, t in sq)
        looked: set = set()
        for s in range(len(pts)):
            if s in taken or s in looked or not inside(s):
                continue
            todo, members = [s], [s]
            looked.add(s)
            while todo:
                a = todo.pop()
                gx, gy = int(pts[a][1][3] // cell), int(pts[a][1][7] // cell)
                for i in (gx - 1, gx, gx + 1):
                    for j in (gy - 1, gy, gy + 1):
                        for b in grid.get((i, j), ()):
                            if b not in taken and b not in looked and joined(a, b):
                                looked.add(b)
                                members.append(b)
                                todo.append(b)
            if all(inside(k) for k in members):
                taken.update(members)
                fields.append([tuple(pts[k]) for k in members])
    return fields


def field_key(field: list) -> frozenset:
    """A field's identity: its row stickers (name index, x, y), as brush_fields finds them."""
    return frozenset((s, round(m[3], 1), round(m[7], 1)) for s, m, _k, _h in field)


def own_fields(dabs: list, looks: dict, sc: Scenery, halves: dict | None = None) -> tuple[list, set]:
    """For a map's field brush dabs in order: each dab's fields that are its own (a field two dabs touch is the
    LATER dab's, as a later stroke paints over an earlier one), and every row sticker any of them changes (so no
    dab lays one of them again as an untouched neighbour)."""
    found = [brush_fields(d, looks[d.look], sc, halves) for d in dabs]
    last = {}
    for k, fields in enumerate(found):
        for f in fields:
            last[field_key(f)] = k
    own = [[f for f in fields if last[field_key(f)] == k] for k, fields in enumerate(found)]
    changed = set().union(*last) if last else set()
    return own, changed


def expand_field_brush(brush: "FieldBrush", look: dict, sc: Scenery, group: int = 0, halves: dict | None = None,
                       fields: list | None = None, changed: set | None = None,
                       relaid: set | None = None, picture=None, buildings: dict | None = None,
                       descs: dict | None = None, parcel=None, ground=None, others=()):
    """What a field brush dab does to the map whose scenery is `sc` (as it ships, before the build erases anything),
    as (erases, objects, copies, stamps, notes). Each WHOLE field it touches (brush_fields) becomes ONE real field of
    the look, near and far: the source (look["sources"]) whose crops run nearest its rows gives
      - its row sticker kind: the field's row stickers are taken off and laid again where they were, the same size,
        facing and levels, all of that kind (a corner piece that kind's corner piece where the map has one, else as
        it was; a source without one, the look's main kind);
      - its crops: the field's crops (look["crops"]) go, and the source's are copied from the square in its middle,
        their own run turned onto these rows, landing only on the field (within its stickers' squares); a field
        bigger than that square is laid in cells of its size;
      - its ground picture (Eugen paints each field's picture its own colour, under the whole field): a hard turned
        "stamp" on each whole row sticker's square copies the source's picture through the same cells, its stripes
        turned onto these rows, so the field's own shape shows that field's colour and grain.
    What the erases take of ANOTHER plot's row stickers (squares overlap across a hedge: their middles lie in the
    field's squares) is laid again where it was as the field's kind (each overlapping sticker goes with the plot
    holding its middle), unless `changed` (own_fields: every row sticker the map's dabs change) holds it, or `relaid`
    does (the stickers an earlier dab of the map laid again; this dab adds its own: two dabs' erases over one sticker
    laid it twice). `fields`: this dab's own fields (own_fields), else every field it touches.
    `picture`: the map's ground picture, finest level ((x, y) -> rgb or None): each field's paint is then one stamp
    clipped to the field's painted outline (field_outline); without it, a stamp per row sticker.
    What stands on a field stays as the map has it, as Eugen's own fields have it (measured on D-Day): its hay
    and farm machines keep their harvested ground (a new crop where one of the map's own harvested crops within
    HAY_REACH of them lay is laid as that one is; within HAY_PATCH of them at least as HARVESTED says), and on a look
    whose fields carry no hay (look["hay"] false: ploughed) the hay and carts go, and the tractors past
    NO_HAY_MACHINE_DEPTH in. `buildings` (building_table): no new crop lands in a building's box or within its type's
    gap of it. `descs` (the game's scenery descriptors): the field's dressing from FIELD_EDGE in (its low plants,
    stones, ground stickers and trees: DRESSING_LAYERS) is taken off and the source's laid there, as its crops are.
    `parcel` (parcels.Parcel, with `ground`: parcels.FieldGround): the dab's parcel, the ground the map's paint gives
    the field under it; the dab is then expand_field_parcel's, not this.
    Nothing is done where there's no field under the brush."""
    if parcel is not None:
        return expand_field_parcel(brush, look, sc, parcel, group, halves, buildings, ground, others)
    from .brush import HARD_EDGE, Stroke
    given = fields is not None
    fields = brush_fields(brush, look, sc, halves) if fields is None else fields
    if not fields:
        why = "every field under it is painted by a later dab" if given else "no field under it"
        return [], [], [], [], [f"field brush at ({brush.x:.0f}, {brush.y:.0f}): {why}, nothing done"]
    full = {}
    for n in sc.names:
        full.setdefault(n.rsplit("/", 1)[-1], n)
    shares = [(full[n], s) for n, s in look["stickers"] if n in full]
    if not shares:
        raise SceneryEditError(f"the look's row stickers ({', '.join(n for n, _s in look['stickers'])}) aren't on "
                               f"this map")
    main = max((s for s in shares if not _cut(s[0])), key=lambda s: s[1], default=shares[0])[0]
    short = [n.rsplit("/", 1)[-1] for n in sc.names]
    field_syms = {i for i, n in enumerate(short) if n.startswith(tuple(look["field_kinds"]))}
    crop_names = tuple(sorted({sc.names[i] for i, n in enumerate(short) if n.startswith(tuple(look["crops"]))}))
    kinds = tuple(sorted({sc.names[i] for i in field_syms}))
    erases, objects, copies, stamps, notes = [], [], [], [], []
    mine: set = set()   # (sym, x, y) of every sticker of the fields changed
    for field in fields:
        mine.update((s, round(m[3], 1), round(m[7], 1)) for s, m, _k, _h in field)
    sources = look["sources"]
    farm_syms = {i for i, n in enumerate(short) if n.startswith(FARM_HAY + FARM_MACHINES)}
    on_field: set = set()   # (sym, x, y) of the hay and machines already seen on one of the fields
    farm_erases = []        # (each one object alone: kept out of the neighbour re-lay's footprints below)
    reach_b = max((max(abs(v) for v in b[:4]) * 1.4143 + b[4] for b in (buildings or {}).values()), default=0.0)

    # each field's plan: ONE real field of the look for the whole field, near and far, the source whose crops run
    # nearest its rows giving its ground picture, its row sticker kind and its crops (the look's median colour and one
    # kind for all its fields laid every look olive-brown, ploughed dark green up close: the owner's 2026-10-15
    # shots); its picture through one turned map, its middle onto the source's, read folded back (as in a mirror) into
    # the source's even middle square where the field is bigger: no seam in it, never the hedges round that square
    def layout(field, ang, k):
        sx0, sy0, sang, along, across, crop, colour, row = sources[k]
        ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        o = math.radians(abs(crop))
        side = min(along, across) / (math.cos(o) + math.sin(o))
        us = [m[3] * ux + m[7] * uy for _s, m, _k, _h in field]
        vs = [-m[3] * uy + m[7] * ux for _s, m, _k, _h in field]
        reach = max(h for _s, _m, _k, h in field)
        u0, u1, v0, v1 = min(us) - reach, max(us) + reach, min(vs) - reach, max(vs) + reach
        mu, mv = (u0 + u1) / 2.0, (v0 + v1) / 2.0
        return {"k": k, "ang": ang, "ux": ux, "uy": uy, "side": side, "reach": reach, "box": (u0, u1, v0, v1),
                "pturn": (ang - sang + 90.0) % 180.0 - 90.0, "mx": mu * ux - mv * uy, "my": mu * uy + mv * ux}

    def pick(ang, g):
        def off(src):
            d = abs(src[2] + src[5] - ang) % 180.0
            return min(d, 180.0 - d)
        ranked = sorted(range(len(sources)), key=lambda k: (round(off(sources[k])), k))
        close = [k for k in ranked if off(sources[k]) <= off(sources[ranked[0]]) + 5.0]
        return close[(brush.seed + g) % len(close)]
    angs = [_mean_facing([(s, m, k) for s, m, k, _h in field]) for field in fields]
    plans = [layout(field, angs[g], pick(angs[g], g)) for g, field in enumerate(fields)]
    pictures = list(plans)
    # a field of a few stickers (a fragment wedged between bigger plots) is the dab's biggest field's: its source and
    # its picture through that field's map, so it isn't a patch of another real field at its own angle (R's middle)
    big = max(range(len(fields)), key=lambda g: len(fields[g]))
    for g, field in enumerate(fields):
        if g != big and sum(1 for s, _m, _k, _h in field if not _cut(sc.names[s])) < SMALL_FIELD:
            plans[g] = layout(field, angs[g], plans[big]["k"])
            pictures[g] = pictures[big]

    # what stands on the fields stays as the map has it, as Eugen's own fields have it: their hay and farm
    # machines, the crops round them laid harvested (HAY_PATCH: round those just over a field's edge too, a
    # neighbour's or the next changed field's: the new crops of a field facing another way came within 0.6 m of the
    # hay on the field beside it at E); on a look whose fields carry no hay, the hay and carts go, and the tractors
    # past NO_HAY_MACHINE_DEPTH in (bales left in a full field of new wheat at E, the owner's 2026-10-15 shots)
    field_squares = [[(m[3], m[7], half, math.radians(_facing(m))) for _s, m, _k, half in field] for field in fields]

    def depth(sq, x, y):   # how far (x, y) lies inside a field's squares (below 0 outside them)
        return max(h - max(abs((x - qx) * math.cos(t) + (y - qy) * math.sin(t)),
                           abs(-(x - qx) * math.sin(t) + (y - qy) * math.cos(t))) for qx, qy, h, t in sq)

    def box_of(sq, grow=0.0):
        return (min(x - h * 1.4143 for x, _y, h, _t in sq) - grow, min(y - h * 1.4143 for _x, y, h, _t in sq) - grow,
                max(x + h * 1.4143 for x, _y, h, _t in sq) + grow, max(y + h * 1.4143 for _x, y, h, _t in sq) + grow)
    standing_on, gone_from, taken = [0] * len(fields), [0] * len(fields), set()
    for g, sq in enumerate(field_squares):
        for sym, m, _mask in walk_levels(sc, box_of(sq), farm_syms):
            key = (sym, round(m[3], 1), round(m[7], 1))
            if key in on_field or depth(sq, m[3], m[7]) < 0.0:
                continue
            on_field.add(key)
            if not look.get("hay", True) and (short[sym].startswith(FARM_HAY) or not short[sym].startswith(TRACTORS)
                                              or depth(sq, m[3], m[7]) > NO_HAY_MACHINE_DEPTH):
                farm_erases.append(EraseArea(m[3], m[7], 13.0, (), (sc.names[sym],)))   # (that one object: 5 cm)
                taken.add(key)
                gone_from[g] += 1
            else:
                standing_on[g] += 1
    patch, near_seen = [], set()
    for sq in field_squares:
        for sym, m, _mask in walk_levels(sc, box_of(sq, HAY_PATCH), farm_syms):
            key = (sym, round(m[3], 1), round(m[7], 1))
            if key in taken or key in near_seen or depth(sq, m[3], m[7]) < -HAY_PATCH:
                continue
            near_seen.add(key)
            patch.append((m[3], m[7], HAY_PATCH))
    # Eugen's own harvested ground round them: his crops laid harvested (squashed under 0.6 or sunk past 0.1 m) within
    # HAY_REACH of a hay piece or machine that stays, on these fields; a new crop at one of their spots is laid as he
    # laid it (E's harvested block, 25 x 20 m along the rows, came out as a circle round each bale: the owner's "the
    # hay bales look like poop", 2026-10-15)
    crop_syms = {i for i, n in enumerate(short) if n.startswith(tuple(look["crops"]))}
    if patch:
        hay_cells: dict = {}
        for p in patch:
            hay_cells.setdefault((int(p[0] // HAY_REACH), int(p[1] // HAY_REACH)), []).append((p[0], p[1]))
        crop_seen: set = set()
        for sq in field_squares:
            for sym, m, _mask in walk_levels(sc, box_of(sq), crop_syms):
                key = (sym, round(m[3], 1), round(m[7], 1))
                if key in crop_seen or depth(sq, m[3], m[7]) < 0.0:
                    continue
                crop_seen.add(key)
                height = m[10] or math.hypot(m[0], m[4])
                if height >= 0.6 and m[11] >= -0.1 * 260.0:   # (standing)
                    continue
                cx, cy = int(m[3] // HAY_REACH), int(m[7] // HAY_REACH)
                if any((m[3] - hx) ** 2 + (m[7] - hy) ** 2 <= HAY_REACH * HAY_REACH
                       for i in (cx - 1, cx, cx + 1) for j in (cy - 1, cy, cy + 1) for hx, hy in hay_cells.get((i, j), ())):
                    patch.append((m[3], m[7], HARVESTED_SPOT, height, m[11], short[sym]))
    # the dressing (descs given): its kinds, every kind of the layers but the rows, the crops and the hay
    skip_names = tuple(look["field_kinds"]) + tuple(look["crops"]) + FARM_HAY + FARM_MACHINES
    dressing_types: tuple = ()
    if descs is not None:
        in_layers = copy_layers(sc.names, descs)
        dressing_types = tuple(sorted({sc.names[i] for g in DRESSING_LAYERS for i in in_layers[g]
                                       if not short[i].startswith(skip_names)}))
    dressing_erases = []   # (kept out of the neighbour re-lay's footprints below, as the farm erases)
    kinds_here: list = []  # each field's row sticker kind, for the other plots' stickers with their middle in it
    for g, field in enumerate(fields):
        plan, pic = plans[g], pictures[g]
        ang = plan["ang"]
        sx0, sy0, sang, along, across, crop, colour, row = sources[plan["k"]]
        colour = colour or look.get("colour", "")
        kind_here = full.get(row, main) if row else main
        kinds_here.append(kind_here)
        turn = ang - (sang + crop)
        turn = (turn + 90.0) % 180.0 - 90.0   # rows have no front: the least turn
        ux, uy = plan["ux"], plan["uy"]
        su, sv = math.cos(math.radians(sang)), math.sin(math.radians(sang))
        side, reach = plan["side"], plan["reach"]
        u0, u1, v0, v1 = plan["box"]
        cell = side   # the crops: the source's middle laid over the field's box in cells, edge to edge
        nu, nv = max(1, math.ceil((u1 - u0) / cell)), max(1, math.ceil((v1 - v0) / cell))
        psx, psy, pang, pcrop = sources[pic["k"]][0], sources[pic["k"]][1], sources[pic["k"]][2], sources[pic["k"]][5]
        pturn = pic["pturn"]
        pc, ps = math.cos(math.radians(pturn)), math.sin(math.radians(pturn))
        pside = pic["side"]
        squares = [(m[3], m[7], half, math.radians(_facing(m))) for _s, m, _k, half in field]
        field_stamps = []
        for sym, m, mask, half in field:
            f = _facing(m)
            t = math.radians(f)
            erases.append(EraseArea(m[3], m[7], half, (), kinds + crop_names, shape="square", dx=math.cos(t),
                                    dy=math.sin(t)))
            size = math.hypot(m[0], m[4])
            stretch = math.hypot(m[1], m[5]) / size if size else 1.0
            cut = _cut(sc.names[sym])
            kind = kind_here if not cut else (kind_here + "_" + cut if kind_here + "_" + cut in sc.names
                                              else sc.names[sym])
            objects.append(NewObject(kind, m[3], m[7], math.degrees(math.atan2(m[4], m[0])), size, solid=False,
                                     stretch=stretch, lift=m[11], levels=mask, height=m[10] or size))
            if cut:   # (a corner or half piece covers part of its square only)
                continue
            # the ground picture under it: the source field's own (its colour, its stripes and grain) through the
            # field's one map, a hard rectangle on its square reaching FIELD_STAMP past it only toward the field's own
            # stickers (closing the gaps between them) and stopping at its edge everywhere else: the field's own
            # outline, the plot boundary and the neighbour's ground kept (reaching past every side cut a stepped edge
            # into the neighbour and painted over the dark line under a boundary's grass, 2026-10-15)
            cx, cy, hv, hu = _stamp_rect(m[3], m[7], half, t, squares)
            ox, oy = cx - pic["mx"], cy - pic["my"]
            field_stamps.append(Stroke("stamp", cx, cy, hv, sx=psx + (ox * pc + oy * ps) - cx,
                                       sy=psy + (oy * pc - ox * ps) - cy, turn=pturn, fold=pside / 2.0, fx=psx,
                                       fy=psy, fturn=pang + pcrop, clear=False, shape="square", edge="hard",
                                       dx=math.cos(t), dy=math.sin(t), length=hu))
        # with the map's picture: ONE stamp over the field, clipped to its painted outline (field_outline), so the
        # new paint ends where the map's own paint of this field ended (a hedge line, the plot beyond) instead of
        # along its stickers' squares (a stepped edge into the neighbour at R's middle, 2026-10-15)
        clip = field_outline(squares, picture) if picture is not None else ()
        if clip:
            cx0, cy0, ccell, cw, chh, _bits = clip
            cx, cy = cx0 + cw * ccell / 2.0, cy0 + chh * ccell / 2.0
            r = max(cw, chh) * ccell / 2.0 / HARD_EDGE + ccell   # full strength over the whole mask
            ox, oy = cx - pic["mx"], cy - pic["my"]
            field_stamps = [Stroke("stamp", cx, cy, r, sx=psx + (ox * pc + oy * ps) - cx,
                                   sy=psy + (oy * pc - ox * ps) - cy, turn=pturn, fold=pside / 2.0, fx=psx, fy=psy,
                                   fturn=pang + pcrop, clear=False, shape="square", edge="hard", clip=clip)]
        stamps.extend(field_stamps)
        # the buildings round the field: its new crops kept off them by their type's gap (the barn full of wheat, E)
        rects = tuple(r[1:] for r in building_rects(sc, buildings, box_of(squares, reach_b))) if buildings else ()
        # its dressing from FIELD_EDGE in (descs given): the map's taken off, the source's laid as its crops are
        inside = None
        if dressing_types:
            whole = [(m[3], m[7], h, math.radians(_facing(m))) for s, m, _k, h in field if not _cut(sc.names[s])]
            if whole:
                inside = FieldInside(whole, FIELD_EDGE)
                wx0, wy0, wx1, wy1 = box_of(whole)
                dressing_erases.append(EraseArea((wx0 + wx1) / 2.0, (wy0 + wy1) / 2.0,
                                                 math.hypot(wx1 - wx0, wy1 - wy0) / 2.0, (), dressing_types,
                                                 mask=inside))
        # the crops: from that source's middle, turned onto these rows, cell by cell
        # the crops land inside the field's own sticker squares (its shape, the squares the erases take), never past
        # them (circles of the stickers' middle size let them spill up to 1.4 m past a smaller sticker's edge)
        pts = [(m[3], m[7], h, math.cos(math.radians(_facing(m))), math.sin(math.radians(_facing(m))))
               for _s, m, _k, h in field]
        near_r = reach
        pieces = 0
        for i in range(nu):
            for j in range(nv):
                cu, cv = u0 + (i + 0.5) * (u1 - u0) / nu, v0 + (j + 0.5) * (v1 - v0) / nv
                cx, cy = cu * ux - cv * uy, cu * uy + cv * ux
                here = tuple(p for p in pts if abs((p[0] - cx) * ux + (p[1] - cy) * uy) <= cell / 2 + reach
                             and abs(-(p[0] - cx) * uy + (p[1] - cy) * ux) <= cell / 2 + reach)
                if not here:
                    continue
                pr = math.hypot((u1 - u0) / nu / 2, (v1 - v0) / nv / 2) + reach   # (what can reach the piece)
                avoid = tuple(b for b in rects if math.hypot(b[0] - cx, b[1] - cy) < pr + max(b[2], b[3]) * 1.4143
                              + b[6])
                harvest = tuple(p for p in patch if math.hypot(p[0] - cx, p[1] - cy) < pr + p[2])
                # each piece its own cell alone (cells meet edge to edge; a piece a whole source square wide laid
                # the crops two and three times over where pieces overlapped: 10,029 on a field that had 301)
                copies.append(CopyArea(cx, cy, (v1 - v0) / nv / 2, sx0 - cx, sy0 - cy, turn, ("plants",), "square", ux, uy,
                                       look["map"], None, False, group, along=(u1 - u0) / nu / 2, only=tuple(look["crops"]),
                                       near=here, near_r=near_r, src_clip=(sx0, sy0, across / 2, su, sv, along / 2),
                                       avoid=avoid, harvest=harvest))
                if inside is not None:   # the source's dressing through the same cell, in the field's interior
                    copies.append(CopyArea(cx, cy, (v1 - v0) / nv / 2, sx0 - cx, sy0 - cy, turn, DRESSING_LAYERS,
                                           "square", ux, uy, look["map"], None, False, group, along=(u1 - u0) / nu / 2,
                                           skip=skip_names, near=here, near_r=near_r,
                                           src_clip=(sx0, sy0, across / 2, su, sv, along / 2), avoid=avoid,
                                           inside=inside))
                pieces += 1
        notes.append(f"field brush at ({brush.x:.0f}, {brush.y:.0f}): a whole field of {len(field)} row sticker(s) "
                     f"facing {ang:.0f} degrees made {brush.look} like the field at ({sx0:.0f}, {sy0:.0f}): its "
                     f"{kind_here.rsplit('/', 1)[-1]} rows, its ground picture{f' ({colour})' if colour else ''} "
                     f"turned {pturn:.0f} degrees and its crops turned {turn:.0f} degrees, in {pieces} piece(s)"
                     + (f"; {standing_on[g]} hay piece(s) and farm machine(s) left standing, the crops round them laid "
                        f"harvested" if standing_on[g] else "")
                     + (f"; {gone_from[g]} hay piece(s) and farm machine(s) taken off ({brush.look} fields carry none)"
                        if gone_from[g] else "")
                     + (f"; its crops kept off {len(rects)} building(s)" if rects else "")
                     + (f"; its dressing from {FIELD_EDGE / 260.0:.0f} m in (low plants, stones, ground stickers, "
                        f"trees) the source's" if inside is not None else ""))
    # another plot's row stickers the erases take (their middles lie in a changed field's squares: plots overlap
    # across a hedge) go with that field: laid again where they were as its kind (a straw sticker of a big neighbour
    # plot reached 14 m into Q made ploughed, the owner's 2026-10-15 shots); one whose middle lies outside isn't taken
    # and stays the neighbour's: each overlapping sticker goes with the plot holding its middle
    boxes = [e.footprint().box() for e in erases]
    bx0, bx1 = min(b[0] for b in boxes), max(b[1] for b in boxes)
    by0, by1 = min(b[2] for b in boxes), max(b[3] for b in boxes)
    feet = [e.footprint() for e in erases]
    kept = 0
    seen: set = set() if relaid is None else relaid
    for sym, m, mask in walk_levels(sc, (bx0, by0, bx1, by1), field_syms):
        key = (sym, round(m[3], 1), round(m[7], 1))
        if key in mine or key in (changed or ()) or key in seen or not any(ft.t2(m[3], m[7]) < 1.0 for ft in feet):
            continue
        seen.add(key)
        g = max(range(len(fields)), key=lambda q: depth(field_squares[q], m[3], m[7]))
        cut = _cut(sc.names[sym])
        kind = kinds_here[g] if not cut else (kinds_here[g] + "_" + cut if kinds_here[g] + "_" + cut in sc.names
                                              else sc.names[sym])
        size = math.hypot(m[0], m[4])
        objects.append(NewObject(kind, m[3], m[7], math.degrees(math.atan2(m[4], m[0])), size, solid=False,
                                 stretch=math.hypot(m[1], m[5]) / size if size else 1.0, lift=m[11], levels=mask,
                                 height=m[10] or size))
        kept += 1
    if kept:
        notes.append(f"field brush: {kept} row sticker(s) of other plots with their middle in a changed field laid "
                     f"again as its kind")
    return erases + farm_erases + dressing_erases, objects, copies, stamps, notes


def _pick_source(sources: list, ang: float, seed: int) -> int:
    """The source whose crops run nearest a field's rows facing `ang` degrees (several within 5 degrees of the best:
    one by `seed`)."""
    def off(src):
        d = abs(src[2] + src[5] - ang) % 180.0
        return min(d, 180.0 - d)
    ranked = sorted(range(len(sources)), key=lambda k: (round(off(sources[k])), k))
    close = [k for k in ranked if off(sources[k]) <= off(sources[ranked[0]]) + 5.0]
    return close[seed % len(close)]


def _ring_flag(dist: dict, x: float, y: float, old: int) -> int:
    """A row piece's detail-ring flags, drawn from `dist` ({flag: count}: its source field's pieces') by its place, so
    a field's pieces carry its source's in the same shares; `old` without one."""
    if not dist:
        return old
    total = sum(dist.values())
    h = ((int(round(x)) * 73856093) ^ (int(round(y)) * 19349663)) & 0xFFFFFFFF
    r = (h % 100003) / 100003.0 * total
    acc = 0
    for flag, n in sorted(dist.items()):
        acc += n
        if r < acc:
            return flag
    return old


ONE_FIELD = 45.0   # RGB distance under which the paint on every side of a tree or a hedge strip is one field's (a
                   # pasture's light and dark stripes 30 apart: W; two fields' paint 100 apart: E's yellow and brown)


def expand_field_parcel(brush: "FieldBrush", look: dict, sc: Scenery, parcel, group: int = 0,
                        halves: dict | None = None, buildings: dict | None = None, ground=None, others=()):
    """What a field brush dab does to the map whose scenery is `sc` (as it ships) where its PARCEL lies (parcel:
    rusemod.parcels.Parcel, the ground the map's own paint and borders give the field under the dab: FieldGround
    .parcel), as (erases, objects, copies, stamps, notes); expand_field_brush's way on the squares, the parcel deciding
    what is the field's (the owner, 2026-10-15: "Go with what you have planned"):
      - its row pieces: every one whose middle lies in it (whichever plot it belongs to) taken off and laid again where
        it was as the look's ONE source's kind, its detail-ring flags drawn from that source's own pieces' (R's pieces
        kept their old fields' flags: two greens at 77 m), never one outside it;
      - its paint: ONE stamp of the source's picture through one turned map, clipped to the parcel (it stops where the
        map's own paint of the field stops: R's green no longer over E's corner);
      - its crops: the old ones in it taken off, the source's laid over it in cells, landing only in it (W's tree
        line's strip, a corner piece's ground: Q's tiny spot);
      - its trees and border strips (hedge feet) in one field's paint more than look["trees_within"] metres in taken
        off (W's trees in the middle of the wheat), their ground then the field's; those between two fields' paint
        kept, a hedge foot's ground cut out of it, the new crops 0.8 m off a kept tree;
      - its hay and machines as expand_field_brush keeps them (Eugen's harvested ground round them; none on a look
        without hay), its new crops kept off `buildings` (building_table);
      - nothing else of its dressing changes (the source's copied in cells laid a bush line across Q's fence).
    `ground` (parcels.FieldGround): the map's paint, border strips and trees (without it: no trees or strips go);
    `others`: the map's other dabs' parcels, whose ground this one never takes (its gaps closed grew R's into E's)."""
    from .brush import HARD_EDGE, Stroke
    from .numpy2 import np
    P = parcel
    tree_syms = ground.tree_syms if ground is not None else None
    full = {}
    for n in sc.names:
        full.setdefault(n.rsplit("/", 1)[-1], n)
    shares = [(full[n], s) for n, s in look["stickers"] if n in full]
    if not shares:
        raise SceneryEditError(f"the look's row stickers ({', '.join(n for n, _s in look['stickers'])}) aren't on "
                               f"this map")
    main = max((s for s in shares if not _cut(s[0])), key=lambda s: s[1], default=shares[0])[0]
    short = [n.rsplit("/", 1)[-1] for n in sc.names]
    field_syms = {i for i, n in enumerate(short) if n.startswith(tuple(look["field_kinds"]))}
    crop_names = tuple(sorted({sc.names[i] for i, n in enumerate(short) if n.startswith(tuple(look["crops"]))}))
    crop_syms = {i for i, n in enumerate(short) if n.startswith(tuple(look["crops"]))}
    farm_syms = {i for i, n in enumerate(short) if n.startswith(FARM_HAY + FARM_MACHINES)}
    where = f"field brush at ({brush.x:.0f}, {brush.y:.0f})"
    erases, objects, copies, stamps, notes = [], [], [], [], []
    bx0, by0, bx1, by1 = P.box()
    # the row pieces whose middles lie in the parcel
    found: dict = {}
    for sym, m, mask in walk_levels(sc, (bx0, by0, bx1, by1), field_syms):
        if not P.holds(m[3], m[7]):
            continue
        key = (sym, round(m[3], 1), round(m[7], 1))
        if key in found:
            found[key][2] |= mask
        else:
            found[key] = [sym, m, mask, sticker_half(sc, sym, m, halves)]
    pieces = list(found.values())
    if not pieces:
        return [], [], [], [], [f"{where}: no field's row pieces on the ground under it, nothing done"]
    # the plan: the facing most of its pieces share, the source whose crops run nearest it
    angs = [_facing(m) for _s, m, _k, _h in pieces]
    best = max(([b for b in angs if _alike(a, b)] for a in angs), key=len)
    c = sum(math.cos(math.radians(2 * a)) for a in best)
    s_ = sum(math.sin(math.radians(2 * a)) for a in best)
    ang = (math.degrees(math.atan2(s_, c)) / 2) % 180.0
    sources = look["sources"]
    k = _pick_source(sources, ang, brush.seed)
    sx0, sy0, sang, along, across, crop, colour, row = sources[k]
    colour = colour or look.get("colour", "")
    kind_here = full.get(row, main) if row else main
    dist = (look.get("masks") or [])[k] if k < len(look.get("masks") or []) else None
    turn = (ang - (sang + crop) + 90.0) % 180.0 - 90.0
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    su, sv = math.cos(math.radians(sang)), math.sin(math.radians(sang))
    o = math.radians(abs(crop))
    side = min(along, across) / (math.cos(o) + math.sin(o))
    pturn = (ang - sang + 90.0) % 180.0 - 90.0
    pc, ps = math.cos(math.radians(pturn)), math.sin(math.radians(pturn))
    # what stands inside it: the trees and border strips (hedge feet) in ONE field's paint (the same colour all round
    # them: W's tree group and its strips, in the middle of one pasture's paint) more than look["trees_within"] in (to
    # the edge of the field's ground and its row squares, gaps under 6 m closed) go, their ground the field's; those
    # between two fields' paint (the hedge between E's two fields) stay, their ground cut out of the parcel (no crops on
    # a hedge foot). The trees that stay keep the new crops 0.8 m off (D-Day's wheat comes within 0.6-1.3 m).
    gone_trees = gone_strips = 0
    tw = look.get("trees_within")
    keep_off: list = []
    squares = [(m[3], m[7], h, math.radians(_facing(m))) for s, m, _k, h in pieces if not _cut(sc.names[s])]
    picture = getattr(ground, "picture", None)
    if ground is not None and squares:
        own = P.mask | _cells_in_squares(P, squares)
        from .parcels import _grow, _inside, _shrink
        closed = _shrink(_grow(own, 10), 10) | own
        deep_m = _inside(closed, P.cell)

        def deep(x, y):
            i, j = int((x - P.x0) // P.cell), int((y - P.y0) // P.cell)
            return tw is not None and 0 <= i < P.w and 0 <= j < P.h and deep_m[j, i] >= tw

        def one_field(x, y, dirs, off, loose=False):
            """Whether the ground `off` away on every side (dirs: unit vectors, in opposite pairs) is the parcel's
            and its paint one field's (`loose`: where the parcel isn't on both sides, the paint isn't asked: True)."""
            pts = [(x + ux_ * off, y + uy_ * off) for ux_, uy_ in dirs]
            if not all(P.holds(px_, py_) or _near_mask(P, px_, py_, 1.0 * 260.0) for px_, py_ in pts):
                return loose
            xs_ = [p[0] + a * 0.6 * 260.0 for p in pts for a in (-1, 0, 1)]
            ys_ = [p[1] + b * 0.6 * 260.0 for p in pts for b in (-1, 0, 1)]
            rgb, there = picture(xs_, ys_)
            if not there.all():
                return False
            means = rgb.reshape(len(pts), 3, 3).mean(axis=1)
            return float(np.sqrt(((means[:, None] - means[None]) ** 2).sum(-1)).max()) <= ONE_FIELD
        grown = np.zeros_like(P.mask)
        cut = np.zeros_like(P.mask)
        strip_kinds = ground.strip_kinds()
        for b, mt in ground.strips((bx0, by0, bx1, by1)):
            kind = strip_kinds.get(b)
            if kind is None:
                continue
            hl, hw, mx_, my_, sux, suy, types = kind
            x = mt[0] * mx_ + mt[1] * my_ + mt[3]
            y = mt[4] * mx_ + mt[5] * my_ + mt[7]
            ax, ay = mt[0] * sux + mt[1] * suy, mt[4] * sux + mt[5] * suy
            sc_ = math.hypot(ax, ay) or 1.0
            ax, ay = ax / sc_, ay / sc_
            L, Wd = hl * sc_, hw * sc_
            if not (P.holds(x, y) or _near_mask(P, x, y, Wd + 1.0 * 260.0)):
                continue
            pts = [(x + ax * L * t / 24.0, y + ay * L * t / 24.0) for t in range(-24, 25)]   # (every ~0.5 m)
            sides = ((-ay, ax), (ay, -ax))
            if (deep(x, y) and one_field(x, y, sides, Wd + 3.0 * 260.0)
                    and all(one_field(px_, py_, sides, Wd + 3.0 * 260.0, loose=True) for px_, py_ in pts[8:-8:8])):
                erases.append(EraseArea(x - ax * L, y - ay * L, Wd + 0.3 * 260.0, (), types, shape="line",
                                        x2=x + ax * L, y2=y + ay * L))
                gone_strips += 1
                for px_, py_ in pts:
                    _paint_disc(P, grown, px_, py_, Wd + 1.0 * 260.0)
            else:
                for px_, py_ in pts:
                    _paint_disc(P, cut, px_, py_, Wd + 0.3 * 260.0)
        if tw is not None and tree_syms:
            seen: set = set()
            dirs = [(math.cos(a * math.pi / 4), math.sin(a * math.pi / 4)) for a in range(8)]
            for sym, m, _mask in walk_levels(sc, (bx0, by0, bx1, by1), set(tree_syms)):
                key = (sym, round(m[3], 1), round(m[7], 1))
                if key in seen:
                    continue
                seen.add(key)
                if not (P.holds(m[3], m[7]) or _near_mask(P, m[3], m[7], 2.0 * 260.0)):
                    continue
                if deep(m[3], m[7]) and one_field(m[3], m[7], dirs, 5.0 * 260.0):
                    erases.append(EraseArea(m[3], m[7], 13.0, (), (sc.names[sym],)))
                    gone_trees += 1
                    _paint_disc(P, grown, m[3], m[7], 4.0 * 260.0)
                else:
                    keep_off.append((m[3], m[7], 0.8 * 260.0))
        elif tree_syms:
            for sym, m, _mask in walk_levels(sc, (bx0, by0, bx1, by1), set(tree_syms)):
                if P.holds(m[3], m[7]):
                    keep_off.append((m[3], m[7], 0.8 * 260.0))
        # its ground: the gone ones' and the gaps under 7 m in it the field's (within 3 m of its own row squares: W's
        # strips run where no square lies), then the kept hedge feet cut out
        from .parcels import _depth as _sq_depth
        own_sq = _sq_depth(squares, P.x0, P.y0, P.cell, P.w, P.h) > -3.0 * 260.0
        closed = _shrink(_grow(P.mask, 6), 6)
        P.mask = (P.mask | ((grown | closed) & own_sq)) & ~cut
        from .parcels import _components
        holes, nh = _components(~P.mask)
        edge_ids = set(np.unique(np.concatenate([holes[0], holes[-1], holes[:, 0], holes[:, -1]])).tolist())
        for k_ in range(1, nh + 1):
            if k_ not in edge_ids:
                P.mask |= (holes == k_) & ~cut
        P.inside = _parcel_inside(P)
        from .parcels import subtract as _subtract
        for q in others:   # (another dab's ground stays its own)
            if q is not None and q is not P:
                _subtract(P, q)
    # its row pieces, again: the ground it gained (gaps closed, hedges gone) holds some
    if ground is not None and squares:
        found = {}
        for sym, m, mask in walk_levels(sc, P.box(), field_syms):
            if not P.holds(m[3], m[7]):
                continue
            key = (sym, round(m[3], 1), round(m[7], 1))
            if key in found:
                found[key][2] |= mask
            else:
                found[key] = [sym, m, mask, sticker_half(sc, sym, m, halves)]
        pieces = list(found.values())
        bx0, by0, bx1, by1 = P.box()
    # its row pieces: laid again as the source's kind, with the source's detail-ring flags in the source's shares
    # exactly (each piece's by its place's hash, in order: a hash per piece alone laid W's 18% close against 35%)
    flags: dict = {}
    if dist:
        import hashlib
        order = sorted(pieces, key=lambda p: hashlib.blake2b(f"{p[1][3]:.1f},{p[1][7]:.1f}".encode(),
                                                             digest_size=8).digest())
        total, acc, i = sum(dist.values()), 0, 0
        for flag, n_ in sorted(dist.items()):
            acc += n_
            upto = round(acc / total * len(order))
            while i < upto:
                flags[id(order[i])] = flag
                i += 1
    for piece in pieces:
        sym, m, mask, _half = piece
        erases.append(EraseArea(m[3], m[7], 13.0, (), (sc.names[sym],)))   # (that one piece: 5 cm)
        size = math.hypot(m[0], m[4])
        stretch = math.hypot(m[1], m[5]) / size if size else 1.0
        cut = _cut(sc.names[sym])
        kind = kind_here if not cut else (kind_here + "_" + cut if kind_here + "_" + cut in sc.names else sc.names[sym])
        objects.append(NewObject(kind, m[3], m[7], math.degrees(math.atan2(m[4], m[0])), size, solid=False,
                                 stretch=stretch, lift=m[11], levels=flags.get(id(piece), mask),
                                 height=m[10] or size))
    # its crops: the old ones in it off
    R = math.hypot(bx1 - bx0, by1 - by0) / 2.0
    erases.append(EraseArea((bx0 + bx1) / 2.0, (by0 + by1) / 2.0, R, (), crop_names, mask=P.holds))
    # its extent along the rows
    jj, ii = np.nonzero(P.mask)
    cxs = P.x0 + (ii + 0.5) * P.cell
    cys = P.y0 + (jj + 0.5) * P.cell
    us, vs = cxs * ux + cys * uy, -cxs * uy + cys * ux
    u0, u1 = float(us.min()) - P.cell, float(us.max()) + P.cell
    v0, v1 = float(vs.min()) - P.cell, float(vs.max()) + P.cell
    mu, mv = (u0 + u1) / 2.0, (v0 + v1) / 2.0
    mx, my = mu * ux - mv * uy, mu * uy + mv * ux
    # its paint: one stamp of the source's picture over it, clipped to it
    cx, cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
    r = max(bx1 - bx0, by1 - by0) / 2.0 / HARD_EDGE + P.cell
    ox, oy = cx - mx, cy - my
    stamps.append(Stroke("stamp", cx, cy, r, sx=sx0 + (ox * pc + oy * ps) - cx, sy=sy0 + (oy * pc - ox * ps) - cy,
                         turn=pturn, fold=side / 2.0, fx=sx0, fy=sy0, fturn=sang + crop, clear=False, shape="square",
                         edge="hard", clip=P.clip()))
    # what stands on it: hay and machines (expand_field_brush's rules, on the parcel)
    patch, gone_farm, standing = [], 0, 0
    taken: set = set()
    for sym, m, _mask in walk_levels(sc, (bx0 - HAY_PATCH, by0 - HAY_PATCH, bx1 + HAY_PATCH, by1 + HAY_PATCH), farm_syms):
        key = (sym, round(m[3], 1), round(m[7], 1))
        if key in taken:
            continue
        taken.add(key)
        on = P.holds(m[3], m[7])
        if on and not look.get("hay", True) and (short[sym].startswith(FARM_HAY) or not short[sym].startswith(TRACTORS)
                                                 or P.depth(m[3], m[7]) * 260.0 > NO_HAY_MACHINE_DEPTH):
            erases.append(EraseArea(m[3], m[7], 13.0, (), (sc.names[sym],)))
            gone_farm += 1
            continue
        standing += on
        if on or _near_mask(P, m[3], m[7], HAY_PATCH):
            patch.append((m[3], m[7], HAY_PATCH))
    if patch:   # Eugen's own harvested ground round them
        cells_: dict = {}
        for p in patch:
            cells_.setdefault((int(p[0] // HAY_REACH), int(p[1] // HAY_REACH)), []).append((p[0], p[1]))
        seen_c: set = set()
        for sym, m, _mask in walk_levels(sc, (bx0, by0, bx1, by1), crop_syms):
            key = (sym, round(m[3], 1), round(m[7], 1))
            if key in seen_c or not P.holds(m[3], m[7]):
                continue
            seen_c.add(key)
            height = m[10] or math.hypot(m[0], m[4])
            if height >= 0.6 and m[11] >= -0.1 * 260.0:
                continue
            gx, gy = int(m[3] // HAY_REACH), int(m[7] // HAY_REACH)
            if any((m[3] - hx) ** 2 + (m[7] - hy) ** 2 <= HAY_REACH * HAY_REACH
                   for i in (gx - 1, gx, gx + 1) for j in (gy - 1, gy, gy + 1) for hx, hy in cells_.get((i, j), ())):
                patch.append((m[3], m[7], HARVESTED_SPOT, height, m[11], short[sym]))
    rects = tuple(b[1:] for b in building_rects(sc, buildings, (bx0 - 40 * 260.0, by0 - 40 * 260.0,
                                                                bx1 + 40 * 260.0, by1 + 40 * 260.0))) if buildings else ()
    # its crops: the source's middle laid over it in cells of that square, edge to edge, landing only in it
    nu, nv = max(1, math.ceil((u1 - u0) / side)), max(1, math.ceil((v1 - v0) / side))
    pieces_laid = 0
    for i in range(nu):
        for j in range(nv):
            cu, cv = u0 + (i + 0.5) * (u1 - u0) / nu, v0 + (j + 0.5) * (v1 - v0) / nv
            px, py = cu * ux - cv * uy, cu * uy + cv * ux
            hu, hv = (u1 - u0) / nu / 2, (v1 - v0) / nv / 2
            if not _cell_meets_mask(P, px, py, hu, hv, ux, uy):
                continue
            pr = math.hypot(hu, hv)
            avoid = tuple(b for b in rects if math.hypot(b[0] - px, b[1] - py) < pr + max(b[2], b[3]) * 1.4143 + b[6])
            avoid += tuple(t for t in keep_off if math.hypot(t[0] - px, t[1] - py) < pr + t[2])
            harvest = tuple(p for p in patch if math.hypot(p[0] - px, p[1] - py) < pr + p[2])
            copies.append(CopyArea(px, py, hv, sx0 - px, sy0 - py, turn, ("plants",), "square", ux, uy, look["map"],
                                   None, False, group, along=hu, only=tuple(look["crops"]),
                                   src_clip=(sx0, sy0, across / 2, su, sv, along / 2), avoid=avoid, harvest=harvest,
                                   inside=P.holds))
            pieces_laid += 1
    notes.append(f"{where}: its field's ground ({P.area_m2():,.0f} m2, as the map paints it) made {brush.look} like the "
                 f"field at ({sx0:.0f}, {sy0:.0f}): {len(pieces)} row piece(s) its "
                 f"{kind_here.rsplit('/', 1)[-1]} rows, facing {ang:.0f} degrees, the source's ring flags; its ground "
                 f"picture{f' ({colour})' if colour else ''} turned {pturn:.0f} degrees, its crops turned {turn:.0f} "
                 f"degrees in {pieces_laid} piece(s)"
                 + (f"; {standing} hay piece(s) and farm machine(s) left standing on Eugen's harvested ground"
                    if standing else "")
                 + (f"; {gone_farm} hay piece(s) and farm machine(s) taken off ({brush.look} fields carry none)"
                    if gone_farm else "")
                 + (f"; {gone_trees} tree(s) and {gone_strips} hedge strip(s) more than {tw:g} m in taken off "
                    f"({brush.look} fields have none so deep)" if gone_trees or gone_strips else "")
                 + (f"; its crops kept off {len(rects)} building(s)" if rects else ""))
    return erases, objects, copies, stamps, notes


def _near_mask(P, x: float, y: float, r: float) -> bool:
    """Whether a parcel holds a cell within r of (x, y)."""
    i0, i1 = max(0, int((x - r - P.x0) // P.cell)), min(P.w, int((x + r - P.x0) // P.cell) + 1)
    j0, j1 = max(0, int((y - r - P.y0) // P.cell)), min(P.h, int((y + r - P.y0) // P.cell) + 1)
    return i0 < i1 and j0 < j1 and bool(P.mask[j0:j1, i0:i1].any())


def _paint_disc(P, grid, x: float, y: float, r: float) -> None:
    """Marks a parcel grid's cells within r of (x, y)."""
    from .numpy2 import np
    i0, i1 = max(0, int((x - r - P.x0) // P.cell)), min(P.w, int((x + r - P.x0) // P.cell) + 1)
    j0, j1 = max(0, int((y - r - P.y0) // P.cell)), min(P.h, int((y + r - P.y0) // P.cell) + 1)
    if i0 >= i1 or j0 >= j1:
        return
    X, Y = np.meshgrid(P.x0 + (np.arange(i0, i1) + 0.5) * P.cell - x, P.y0 + (np.arange(j0, j1) + 0.5) * P.cell - y)
    grid[j0:j1, i0:i1] |= X * X + Y * Y <= r * r


def _cells_in_squares(P, squares: list):
    """The parcel grid's cells inside the squares (x, y, half, facing radians)."""
    from .parcels import _depth
    return _depth(squares, P.x0, P.y0, P.cell, P.w, P.h) >= 0.0


def _parcel_inside(P):
    from .parcels import _inside
    return _inside(P.mask, P.cell)


def _cell_meets_mask(P, x: float, y: float, hu: float, hv: float, ux: float, uy: float) -> bool:
    """Whether a turned cell (middle x, y; half sizes hu along (ux, uy), hv across) holds any of the parcel."""
    r = math.hypot(hu, hv)
    i0, i1 = max(0, int((x - r - P.x0) // P.cell)), min(P.w, int((x + r - P.x0) // P.cell) + 1)
    j0, j1 = max(0, int((y - r - P.y0) // P.cell)), min(P.h, int((y + r - P.y0) // P.cell) + 1)
    if i0 >= i1 or j0 >= j1:
        return False
    from .numpy2 import np
    X, Y = np.meshgrid(P.x0 + (np.arange(i0, i1) + 0.5) * P.cell - x, P.y0 + (np.arange(j0, j1) + 0.5) * P.cell - y)
    inside = (np.abs(X * ux + Y * uy) <= hu) & (np.abs(-X * uy + Y * ux) <= hv)
    return bool((inside & P.mask[j0:j1, i0:i1]).any())


def border_library(path=None) -> dict[str, dict]:
    """The border strips a preset can lay along its outline, by name ("edge", "hedge"): {"description", "map" (the
    pack whose strips they are), "sources" [(x, y, dx, dy, length)...]}: each a straight strip of the map's own, by
    its middle, its direction and its length (map units). From the [[border]] tables of ground_presets.toml beside
    this module."""
    import tomllib
    from pathlib import Path
    file = Path(path) if path else Path(__file__).with_name(PRESET_FILE)
    data = tomllib.loads(file.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for row in data.get("border", []):
        name = str(row.get("name", "")).strip()
        if not name or not row.get("sources") or not row.get("map"):
            raise SceneryEditError(f"{file.name}: a border needs a name, a map and sources")
        sources = []
        for s in row["sources"]:
            try:
                x, y, dx, dy, length = (float(v) for v in s)
            except (TypeError, ValueError):
                raise SceneryEditError(f"{file.name}: border {name}: a source is x, y, dx, dy, length") from None
            if not all(math.isfinite(v) for v in (x, y, dx, dy, length)) or length <= 0 or dx == dy == 0.0:
                raise SceneryEditError(f"{file.name}: border {name}: a source needs a length above 0 and a "
                                       f"direction dx, dy other than 0, 0")
            sources.append((x, y, dx, dy, length))
        out[name] = {"description": str(row.get("description", "")), "map": str(row["map"]), "sources": sources}
    return out


def border_outline(area: PresetArea) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """The area's outline as straight runs, each (start, end) going round it: a square's four sides (turned with its
    dx, dy), a circle's chords, as many as keep each within BORDER_SAG of the circle (8 at least)."""
    if area.shape == "square":
        cs = area.footprint().corners()
        return [(cs[k], cs[(k + 1) % 4]) for k in range(4)]
    chord = math.sqrt(8.0 * area.radius * BORDER_SAG)   # a chord c strays c² / 8r inside the circle
    n = max(8, math.ceil(2.0 * math.pi * area.radius / chord))
    step = 2.0 * math.pi / n
    pts = [(area.x + area.radius * math.cos(step * k), area.y + area.radius * math.sin(step * k)) for k in range(n)]
    return [(pts[k], pts[(k + 1) % n]) for k in range(n)]


def expand_border(area: PresetArea, borders: dict, group: int = 0) -> tuple[list[CopyArea], list[EraseArea]]:
    """What a preset's border lays (area.border, a name in `borders`: border_library): along each run of its outline
    (border_outline), an EraseArea of the band BORDER_WIDTH across centred on it (the stickers, low plants and stones
    of the map there, so the strips never sit in its crops), and the run cut in equal pieces no longer than the
    kind's shortest strip, each a CopyArea of the middle of one of the kind's strips (round-robin from area.seed)
    turned to lie along the run, its plants and stones only (BORDER_LAYERS), at the LOD levels they are drawn at on
    their map. A copy's square and its clip (`within`), as long as the piece and moved apart across the run, overlap
    in the band alone. The copies take the preset's `group`, so the tiles beside them don't thin them."""
    if area.border == "none":
        return [], []
    if area.border not in borders:
        known = ", ".join(sorted(borders)) or "none"
        raise SceneryEditError(f"no border is called {area.border!r} (the borders: {known})")
    kind = borders[area.border]
    sources = kind["sources"]
    shortest = min(s[4] for s in sources)
    half = BORDER_WIDTH / 2
    copies, erases = [], []
    k = area.seed
    for (x0, y0), (x1, y1) in border_outline(area):
        run = math.hypot(x1 - x0, y1 - y0)
        if run <= 0.0:
            continue
        ux, uy = (x1 - x0) / run, (y1 - y0) / run
        vx, vy = -uy, ux
        erases.append(EraseArea(x0, y0, half, ("decal",), (LOW_COVER,), shape="line", x2=x1, y2=y1))
        pieces = max(1, math.ceil(run / shortest))
        s = run / pieces / 2
        a = max(s - half, 0.0)
        for p in range(pieces):
            cx, cy = x0 + ux * (2 * p + 1) * s, y0 + uy * (2 * p + 1) * s
            px, py, pdx, pdy, _length = sources[k % len(sources)]
            k += 1
            norm = math.hypot(pdx, pdy)
            pdx, pdy = pdx / norm, pdy / norm
            turn = math.degrees(math.atan2(uy, ux) - math.atan2(pdy, pdx))
            ax, ay = cx + vx * a, cy + vy * a
            fx, fy = px - pdy * a, py + pdx * a   # the source's point under the square's middle
            copies.append(CopyArea(ax, ay, s, fx - ax, fy - ay, turn, BORDER_LAYERS, "square", ux, uy, kind["map"],
                                   ("square", cx - vx * a, cy - vy * a, s, ux, uy), False, group))
    return copies, erases


def entry_masks(b: Block) -> dict[int, int]:
    """{entry index: the LOD mask of the deepest node of the block's draw tree listing it}: what the decor dresser goes
    by (bits 1/2 close, 4 middle, 0x10 middle with GroundQuality, 8 far)."""
    out: dict[int, int] = {}
    count = len(b.nodes) // 8
    todo = [(0, 0, len(b.entries))] if count else []
    while todo:
        i, lo, hi = todo.pop()
        if i >= count:
            continue
        word, split = struct.unpack_from("<IH", b.nodes, 8 * i)
        for k in range(lo, hi):
            out[k] = (word >> 20) & 0x1F
        if word & (1 << 28):
            continue
        if not word & (1 << 30):
            todo.append((i + 1, lo, split))
        if not word & (1 << 31):
            todo.append((i + ((word & 0xFFFFF) >> 2), split, hi))
    return out


def walk_levels(sc: Scenery, box: tuple, only: set[int]):
    """(name index, 3x4 transform in map coordinates, LOD mask) for every object of `only` whose middle lies in `box`
    (x0, y0, x1, y1, map units): the mask the dresser draws it at, its own entries' (entry_masks) ANDed with every
    block reference's above it. Blocks whose box misses `box` aren't walked."""
    x0, y0, x1, y1 = box
    keep = sc.holding(only)
    own: dict[int, dict[int, int]] = {}

    def item_masks(b: Block) -> dict[int, int]:
        got = own.get(b.index)
        if got is None:
            masks = entry_masks(b)
            got = {}
            for k, at in enumerate(b.entries):
                got[at] = got.get(at, 0) | masks.get(k, 0)
            own[b.index] = got
        return got

    def meets(b: Block, m: tuple) -> bool:
        bx0, by0, bx1, by1 = b.bbox
        xs = [m[0] * x + m[1] * y + m[3] for x, y in ((bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1))]
        ys = [m[4] * x + m[5] * y + m[7] for x, y in ((bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1))]
        return max(xs) >= x0 and min(xs) <= x1 and max(ys) >= y0 and min(ys) <= y1

    todo = [(r, IDENTITY, ALL_TIERS) for r in sc.roots()]
    while todo:
        i, m, above = todo.pop()
        b = sc.blocks[i]
        if not keep[i] or not above:
            continue
        masks = item_masks(b)
        for it in b.items:
            if it.kind == "object":
                if it.symbol in only:
                    w = compose(m, it.matrix())
                    if x0 <= w[3] <= x1 and y0 <= w[7] <= y1:
                        yield it.symbol, w, above & masks.get(it.at, 0)
            elif it.kind == "child":
                j = sc._by_offset[it.child_offset]
                if keep[j]:
                    w = compose(m, it.matrix())
                    if meets(sc.blocks[j], w):
                        todo.append((j, w, above & masks.get(it.at, 0)))


def copy_layers(names: list[str], descs: dict) -> dict[str, set[int]]:
    """{layer: the name indexes of a map's types in it} (FIELD_COPY_LAYERS): stickers are its decals but road
    stickers, plants and stones its low cover (low_cover), trees its other vegetation, props its other props."""
    roads = set(road_stickers(names, descs))
    low = set(low_cover(descs, names))
    out: dict[str, set[int]] = {g: set() for g in FIELD_COPY_LAYERS}
    for i, n in enumerate(names):
        d = descs.get(n)
        if d is None:
            continue
        if d.group == "decal" and n not in roads:
            out["stickers"].add(i)
        elif n in low:
            out["plants" if d.group == "vegetation" else "stones"].add(i)
        elif d.group == "vegetation":
            out["trees"].add(i)
        elif d.group == "prop":
            out["props"].add(i)
    return out


class _Taken:
    """Points for the fill rule, by layer (plants, stones) or by sticker type name, in cells of the widest gap, asked
    "is one within `gap` of (x, y)?": what the map already has in a footprint (built from the scenery), or what the
    build has laid so far (empty, then `add`ed, each point with the copy's group)."""

    def __init__(self, sc: Scenery | None = None, box: tuple | None = None, layer_of: dict | None = None):
        self.cell = max(FILL_GAP.values())
        self.points: dict[tuple, list] = {}
        if sc is not None:
            for sym, m, _mask in walk_levels(sc, box, set(layer_of)):
                self.add(sc.names[sym] if layer_of[sym] == "stickers" else layer_of[sym], m[3], m[7])

    def add(self, key, x: float, y: float, group: int = 0) -> None:
        self.points.setdefault((key, int(x // self.cell), int(y // self.cell)), []).append((x, y, group))

    def near(self, key, x: float, y: float, gap: float, group: int = 0) -> bool:
        """Whether a point of `key` lies within `gap`, points of the same group (not 0) left out."""
        cx, cy = int(x // self.cell), int(y // self.cell)
        g2 = gap * gap
        for i in (cx - 1, cx, cx + 1):
            for j in (cy - 1, cy, cy + 1):
                for px, py, g in self.points.get((key, i, j), ()):
                    if (px - x) ** 2 + (py - y) ** 2 < g2 and not (group and g == group):
                        return True
        return False


def copy_objects(data: bytes, areas: list[CopyArea], descs: dict,
                 sources: dict[str, bytes] | None = None) -> tuple[list[NewObject], list[str]]:
    """The objects `areas` lay (each a NewObject with its shipped copy's LOD levels, solid = false), read from the
    scenery file `data` as the map ships it (or from `sources[area.source]`, another map's shipped scenery, when the
    area names one), and notes: per area how many of each layer, and any object left out (a mirrored one, one sized
    past what a placed object may be, or one the fill rule left off: FILL_GAP, against the map in fill mode and
    against what the areas before it laid in any mode, CopyArea.group)."""
    sc = Scenery(data)
    layers = copy_layers(sc.names, descs)
    read: dict[str, tuple] = {"": (sc, layers)}
    out: list[NewObject] = []
    notes: list[str] = []
    laid = _Taken()
    for n, a in enumerate(areas, 1):
        if a.source and a.source not in read:
            if not sources or a.source not in sources:
                raise SceneryEditError(f"copy {n} takes its ground from {a.source}, whose scenery wasn't given")
            src_sc = Scenery(sources[a.source])
            read[a.source] = (src_sc, copy_layers(src_sc.names, descs))
        src_sc, src_layers = read[a.source]
        only = set().union(*(src_layers[g] for g in a.layers))
        if a.only:   # (the field brush's crops alone)
            only = {i for i in only if src_sc.names[i].rsplit("/", 1)[-1].startswith(tuple(a.only))}
        if a.skip:   # (the field brush's dressing: not the rows, the crops, the hay)
            only = {i for i in only if not src_sc.names[i].rsplit("/", 1)[-1].startswith(tuple(a.skip))}
        layer_of = {i: g for g in a.layers for i in src_layers[g]}
        spots: dict = {}   # the map's own harvested crops' spots (harvest entries of six), by HARVESTED_SPOT cell
        for h in a.harvest:
            if len(h) == 6:
                spots.setdefault((int(h[0] // HARVESTED_SPOT), int(h[1] // HARVESTED_SPOT)), []).append(h)
        circles = [h for h in a.harvest if len(h) == 3]

        def harvested(x, y, kind):
            """(height, lift) of a crop of `kind` landing at (x, y) where the map's own crops are harvested, or None."""
            best, bd = None, None
            cx, cy = int(x // HARVESTED_SPOT), int(y // HARVESTED_SPOT)
            for i in (cx - 1, cx, cx + 1):
                for j in (cy - 1, cy, cy + 1):
                    for hx, hy, hr, hh, hl, hk in spots.get((i, j), ()):
                        d = (x - hx) ** 2 + (y - hy) ** 2
                        if d < hr * hr and (bd is None or d < bd):
                            best, bd = (hh, hl, hk), d
            if best is not None:   # the nearest of his: as it is, if the same kind; else as that kind lies harvested
                return (best[0], best[1]) if best[2] == kind else HARVESTED.get(kind)
            if any((x - hx) ** 2 + (y - hy) ** 2 < hr * hr for hx, hy, hr in circles):
                return HARVESTED.get(kind)
            return None
        foot = a.footprint()
        clip = a.clip()
        sclip = a.source_clip()
        near = None
        if a.near:   # the places an object must land in, filed in cells of near_r: a point (x, y) is a circle of
            near = collections.defaultdict(list)   # near_r round it, a square (x, y, half, dx, dy) its own square
            for p in a.near:
                near[(int(p[0] // a.near_r), int(p[1] // a.near_r))].append(p)
        r2 = a.near_r * a.near_r

        def lands(x, y) -> bool:
            cx, cy = int(x // a.near_r), int(y // a.near_r)
            for i in (cx - 1, cx, cx + 1):
                for j in (cy - 1, cy, cy + 1):
                    for p in near.get((i, j), ()):
                        if len(p) == 2:
                            if (p[0] - x) ** 2 + (p[1] - y) ** 2 <= r2:
                                return True
                        elif (abs((x - p[0]) * p[3] + (y - p[1]) * p[4]) < p[2]
                              and abs(-(x - p[0]) * p[4] + (y - p[1]) * p[3]) < p[2]):
                            return True
            return False
        to = a.to_target()
        back = _inverse(to)
        tx0, tx1, ty0, ty1 = foot.box()
        corners = [(back[0] * x + back[1] * y + back[3], back[4] * x + back[5] * y + back[7])
                   for x, y in ((tx0, ty0), (tx1, ty0), (tx0, ty1), (tx1, ty1))]
        src = (min(c[0] for c in corners), min(c[1] for c in corners),
               max(c[0] for c in corners), max(c[1] for c in corners))
        taken = None
        if a.fill:
            here = {i: g for g in a.layers for i in layers[g]}
            pad = max(FILL_GAP.values())   # what sits just outside the shape counts too
            taken = _Taken(sc, (tx0 - pad, ty0 - pad, tx1 + pad, ty1 + pad), here)
        counts = {g: 0 for g in a.layers}
        mirrored = sized = off = dup = kept_off = cut = on_building = 0
        for sym, m, mask in walk_levels(src_sc, src, only):
            if sclip is not None and sclip.t2(m[3], m[7]) >= 1.0:
                continue
            w = compose(to, m)
            if foot.t2(w[3], w[7]) >= 1.0 or not mask or (clip is not None and clip.t2(w[3], w[7]) >= 1.0):
                continue
            if near is not None and not lands(w[3], w[7]):
                continue
            if a.inside is not None and not a.inside(w[3], w[7]):
                continue
            if a.avoid and a.avoids(w[3], w[7]):
                kept_off += 1
                continue
            if a.src_avoid and m[11] > RAISED and _in_places(a.src_avoid, m[3], m[7]):
                on_building += 1   # it stood on a building the copy doesn't take: it would float
                continue
            size = math.hypot(w[0], w[4])
            if w[0] * w[5] - w[1] * w[4] < 0:
                mirrored += 1
                continue
            stretch = math.hypot(w[1], w[5]) / size if size else 1.0
            if not (0.05 <= size <= 50 and 0.2 <= stretch <= 5):
                sized += 1
                continue
            layer = layer_of[sym]
            key = src_sc.names[sym] if layer == "stickers" else layer
            if taken is not None and taken.near(key, w[3], w[7], FILL_GAP[layer]):
                off += 1
                continue
            if laid.near(key, w[3], w[7], FILL_GAP[layer], a.group):
                dup += 1
                continue
            height, lift = w[10] or size, w[11]
            if a.harvest:   # round hay and machines left on a field: the crop as Eugen lays it harvested there
                low = harvested(w[3], w[7], src_sc.names[sym].rsplit("/", 1)[-1])
                if low is not None:
                    height, lift = low
                    cut += 1
            out.append(NewObject(src_sc.names[sym], w[3], w[7], math.degrees(math.atan2(w[4], w[0])), size,
                                 solid=False, stretch=stretch, lift=lift, levels=mask, height=height))
            laid.add(key, w[3], w[7], a.group)
            counts[layer] += 1
        notes.append(f"copy {n}: " + ", ".join(f"{c:,} {g}" for g, c in counts.items())
                     + f" from {a.sx / 260:+.0f} m, {a.sy / 260:+.0f} m away"   # 260 map units a metre
                     + (f" on {a.source}" if a.source else "")
                     + (f", turned {a.turn:g} degrees" if a.turn else "")
                     + (f"; {off:,} left off where the map already has one (fill rule)" if off else "")
                     + (f"; {dup:,} left off where an earlier copy laid one (fill rule)" if dup else "")
                     + (f"; {kept_off:,} kept off a building" if kept_off else "")
                     + (f"; {on_building:,} that stood on a building left behind left out" if on_building else "")
                     + (f"; {cut:,} laid harvested round hay and farm machines" if cut else "")
                     + (f"; {mirrored} mirrored left out" if mirrored else "")
                     + (f"; {sized} sized past 0.05-50 (or stretched past 0.2-5) left out" if sized else ""))
    return out, notes


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


def _tree(b: Block) -> list[tuple[int, int, int, int]]:
    """A block's search tree, one (word, split, b1, b2) per node. A node holds the entries [lo, hi) it's reached with:
    its left side [lo, split) is the next node, its right side [split, hi) the node (word & 0xFFFFF) >> 2 further on;
    word flag 0x40000000 makes the left side a leaf, 0x80000000 the right, 0x10000000 the whole node. Bits 20-24
    are its LOD mask, bit 25 the road mark; it splits its box along x (word & 3 == 0) or y, at b1 (the left side's
    top) and b2 (the right side's bottom), shares /255 of its extent."""
    return [struct.unpack_from("<IHBB", b.nodes, 8 * k) for k in range(len(b.nodes) // 8)]


def _path(nodes: list, e: int) -> list[int]:
    """The nodes from the root down to the leaf that holds entry `e`."""
    out, k = [], 0
    while True:
        if not 0 <= k < len(nodes) or len(out) > len(nodes):
            raise SceneryError("a block's tree points outside itself")
        out.append(k)
        w, split = nodes[k][0], nodes[k][1]
        if w & 0x10000000:
            return out
        if e < split:
            if w & 0x40000000:
                return out
            k += 1
        else:
            if w & 0x80000000:
                return out
            k += (w & 0xFFFFF) >> 2


def _leaf_boxes(b: Block) -> dict[int, tuple]:
    """Entry index -> the box of the leaf that holds it, in the block's own coordinates (the root's box is the
    block's)."""
    nodes, out, steps = _tree(b), {}, 0
    if not nodes:
        return out
    todo = [(0, 0, len(b.entries), tuple(b.bbox))]
    while todo:
        k, lo, hi, (x0, y0, x1, y1) = todo.pop()
        steps += 1
        if not 0 <= k < len(nodes) or steps > len(nodes):
            raise SceneryError("a block's tree points outside itself")
        w, split, b1, b2 = nodes[k]
        if w & 0x10000000:
            out.update((e, (x0, y0, x1, y1)) for e in range(lo, hi))
            continue
        if w & 3 == 0:
            left, right = (x0, y0, x0 + b1 / 255 * (x1 - x0), y1), (x0 + b2 / 255 * (x1 - x0), y0, x1, y1)
        else:
            left, right = (x0, y0, x1, y0 + b1 / 255 * (y1 - y0)), (x0, y0 + b2 / 255 * (y1 - y0), x1, y1)
        if w & 0x40000000:
            out.update((e, left) for e in range(lo, split))
        else:
            todo.append((k + 1, lo, split, left))
        if w & 0x80000000:
            out.update((e, right) for e in range(split, hi))
        else:
            todo.append((k + ((w & 0xFFFFF) >> 2), split, hi, right))
    return out


def _mark_road_path(raw: bytearray, b: Block, at: int, base: int = 0) -> None:
    """Give the road mark to every node of block `b`'s tree on the way to item `at`: to its entries in the full list
    when the root is seen from far (the game then starts the road pass at the root's right side), else to all of
    them. A node with no LOD mask is left alone (the mark would leave it the road pass only). `raw` holds the block
    at `base`."""
    nodes = _tree(b)
    if not nodes:
        return
    w0, split = nodes[0][0], nodes[0][1]
    skip = split if (w0 >> 20) & 0x08 else 0
    start = base + (0x20 if b.long else 0x1C) + 4 * len(b.entries)
    for e, a in enumerate(b.entries):
        if a != at or e < skip:
            continue
        for k in _path(nodes, e):
            w = nodes[k][0]
            if (w >> 20) & ALL_TIERS:
                struct.pack_into("<I", raw, start + 8 * k, w | ROAD_BIT)


def _mark_for_roads(sc: Scenery, blob: bytearray, bi: int, at: int) -> None:
    """The road mark on the way to item `at` of block `bi`, and on up through every block that places it, to the
    map's top. `blob`: the file's blocks, from the data's start."""
    parents: dict[int, list] = {}
    for b in sc.blocks:
        for it in b.items:
            if it.kind == "child":
                parents.setdefault(sc._by_offset[it.child_offset], []).append((b.index, it.at))
    todo, seen = [(bi, at)], set()
    while todo:
        i, a = todo.pop()
        if (i, a) in seen:
            continue
        seen.add((i, a))
        _mark_road_path(blob, sc.blocks[i], a, sc.blocks[i].offset)
        todo += parents.get(i, [])


@dataclass
class _Carrier:
    at: int                 # the reference's offset among the top block's items
    far: list               # its leaf boxes in the far-view list (map coordinates: the top block is placed as is)
    full: list              # and in the list of every item
    marked: bool = False    # its path to the full list's leaf already has the road mark
    mask: int = 0           # the LOD levels its full-list listings carry (their nodes' masks, or'ed): the game ANDs
                            # a node's mask down the chain, so a block hung on it is drawn at these levels at most


def _needs(p) -> int:
    """The LOD levels (but far) a new object asks of the block it hangs on: its own, else every one."""
    return (getattr(p, "levels", 0) or ALL_TIERS) & ALL_TIERS & ~0x08


def _carriers(sc: Scenery, things: list, roads: bool = False) -> tuple[list[tuple[int, list]], list, list]:
    """New things per carrier, as [(the top block's reference's `at`, its things)], the things in no carrier's
    boxes, and the things that hang on a carrier listed at fewer levels than they ask. The game finds a block's items only through the leaf boxes of the top block's tree, and draws an object
    only while it walks the cell its origin lies in, so a thing has to lie in its carrier's leaf box (on D-Day 416
    of the 431 shipped road middles do; one carrier for a whole road left up to 1.8 km of it outside, and on Edge
    3 in 10 new objects 300 m off a village). Road pieces (walked by the road pass through the full list) go on a far-listed
    reference whose full-list box holds their middle, one whose path has the road mark first. Objects go on a
    far-listed reference whose far and full boxes both hold them (drawn at every distance), else on any reference
    whose full-list box does (drawn from middle distance in). The fewest carriers win; what lies in no box goes with
    the nearest far-listed block. The boxes are never widened: a node's bounds are shares of its parent's, so
    widening one moves every node below it."""
    top, far = sc.blocks[0], _far_children(sc)
    nodes = _tree(top)
    boxes = _leaf_boxes(top)
    masks = entry_masks(top)
    split = nodes[0][1]
    far_at = {it.at for it in far}
    children = {it.at for it in top.items if it.kind == "child"}
    cands: dict[int, _Carrier] = {}
    for e, a in enumerate(top.entries):
        if a not in children or e not in boxes:
            continue
        c = cands.setdefault(a, _Carrier(a, [], [], True))
        if e < split:
            c.far.append(boxes[e])
        else:
            c.full.append(boxes[e])
            c.marked = c.marked and all(nodes[k][0] & ROAD_BIT for k in _path(nodes, e))
            c.mask |= masks.get(e, 0)

    def inside(bs, p):
        return any(b[0] <= p.x <= b[2] and b[1] <= p.y <= b[3] for b in bs)

    def meets(bs, p, size):  # a box meets the grid cell (of `size`) that p lies in: the game walks that leaf there
        x0, y0 = math.floor(p.x / size) * size, math.floor(p.y / size) * size
        return any(b[0] <= x0 + size and x0 <= b[2] and b[1] <= y0 + size and y0 <= b[3] for b in bs)

    def draws(c, p):  # the carrier's listings carry every level the thing asks (2026-10-11: a meadow hung on a
        return (c.mask & _needs(p)) == _needs(p)   # block listed without the close level lost it up close)
    close, far_cell = GRID_CELL[2], GRID_CELL[0]
    if roads:
        rounds = [(lambda c, p: c.at in far_at and inside(c.full, p), lambda c: c.marked)]
    else:
        # first the carriers whose levels cover the thing's; the same rounds without that last, so nothing is left
        # out for it (such a thing is drawn at fewer levels than it asks: add_objects says so)
        rounds = [(lambda c, p: c.at in far_at and meets(c.full, p, close) and meets(c.far, p, far_cell)
                   and draws(c, p), lambda c: True),
                  (lambda c, p: meets(c.full, p, close) and draws(c, p), lambda c: c.at in far_at),
                  (lambda c, p: c.at in far_at and meets(c.full, p, close) and meets(c.far, p, far_cell),
                   lambda c: True),
                  (lambda c, p: meets(c.full, p, close), lambda c: c.at in far_at)]
    # between carriers that hold as many, the one whose block is nearest the things (on M03_Italie every far-listed
    # reference's boxes are the whole map: the first one, 13.8 km off a test road, took them all)
    world = {it.at: _world_box(sc, it) for it in top.items if it.kind == "child"}

    def off(c, mx, my):
        x0, y0, x1, y1 = world[c.at]
        return math.hypot(max(x0 - mx, 0.0, mx - x1), max(y0 - my, 0.0, my - y1))
    out: dict[int, list] = {}
    left = list(things)
    if not roads:
        # An object's rounds look only at the cells it lies in (close and far) and the levels it asks, so each
        # carrier is asked once for each such key instead of for every object: the same answers, so the same
        # carriers in the same order, many times sooner (the side-by-side test's presets: ~70 s here, 2026-10-14).
        # Every round asks meets(c.full, p, close) first: the keys a carrier's full boxes meet are found once.
        def cell_of(p):
            return (math.floor(p.x / close), math.floor(p.y / close), math.floor(p.x / far_cell),
                    math.floor(p.y / far_cell), _needs(p))
        key_of = [cell_of(p) for p in things]
        at_of = {id(p): k for p, k in zip(things, key_of)}
        keys = set(key_of)

        def meets_cell(bs, fx, fy, size):  # meets(), from the cell's own numbers
            x0, y0 = fx * size, fy * size
            return any(b[0] <= x0 + size and x0 <= b[2] and b[1] <= y0 + size and y0 <= b[3] for b in bs)
        near: dict[int, list] = {}
        for c in cands.values():
            if not c.full:
                continue
            bx0, by0 = min(b[0] for b in c.full), min(b[1] for b in c.full)
            bx1, by1 = max(b[2] for b in c.full), max(b[3] for b in c.full)
            near[c.at] = [k for k in keys if bx0 <= (k[0] + 1) * close and k[0] * close <= bx1
                          and by0 <= (k[1] + 1) * close and k[1] * close <= by1 and meets_cell(c.full, k[0], k[1], close)]
        key_rounds = [
            (lambda c, k: c.at in far_at and meets_cell(c.far, k[2], k[3], far_cell) and draws_mask(c, k[4]),
             lambda c: True),
            (lambda c, k: draws_mask(c, k[4]), lambda c: c.at in far_at),
            (lambda c, k: c.at in far_at and meets_cell(c.far, k[2], k[3], far_cell), lambda c: True),
            (lambda c, k: True, lambda c: c.at in far_at)]

        def draws_mask(c, needs):
            return (c.mask & needs) == needs
        for holds, better in key_rounds:
            pool = [c for c in cands.values() if c.full]
            held = {c.at: {k for k in near[c.at] if holds(c, k)} for c in pool}
            while left and pool:
                mx, my = sum(p.x for p in left) / len(left), sum(p.y for p in left) / len(left)
                count: dict = {}
                for p in left:
                    k = at_of[id(p)]
                    count[k] = count.get(k, 0) + 1
                best = max(pool, key=lambda c: (sum(count.get(k, 0) for k in held[c.at]), better(c),
                                                -off(c, mx, my)))
                mine = held[best.at]
                got = [p for p in left if at_of[id(p)] in mine]
                if not got:
                    break
                out.setdefault(best.at, []).extend(got)
                left = [p for p in left if at_of[id(p)] not in mine]
        rounds = []  # (done above)
    for holds, better in rounds:
        pool = [c for c in cands.values() if c.full]
        while left and pool:
            mx, my = sum(p.x for p in left) / len(left), sum(p.y for p in left) / len(left)
            best = max(pool, key=lambda c: (sum(holds(c, p) for p in left), better(c), -off(c, mx, my)))
            got = [p for p in left if holds(best, p)]
            if not got:
                break
            out.setdefault(best.at, []).extend(got)
            left = [p for p in left if not holds(best, p)]
    for p in left:  # in no carrier's box: the nearest far-listed block
        def gap(it):
            x0, y0, x1, y1 = _world_box(sc, it)
            return math.hypot(max(x0 - p.x, 0.0, p.x - x1), max(y0 - p.y, 0.0, p.y - y1)), (x1 - x0) * (y1 - y0)
        out.setdefault(min(far, key=gap).at, []).append(p)
    def short_of(at, p):  # listed at fewer levels than it asks, or asks to be drawn from far (a tree: the shipped
        if at not in cands or (cands[at].mask & _needs(p)) != _needs(p):   # copy's own far bit) and the carrier
            return at in cands                                             # isn't listed for far view over it
        return bool(getattr(p, "levels", 0) & 0x08) and not (at in far_at and meets(cands[at].far, p, far_cell))
    short = [] if roads else [p for at, group in out.items() for p in group if short_of(at, p)]
    return list(out.items()), left, short


def _widen(sc: Scenery, data: bytes, things: list, levels: int = 0, far: bool = False,
           avoid=()) -> tuple[bytes, int | None, list[str]]:
    """For new objects in no carrier's box (_carriers: open ground, away from the map's villages, farms and woods),
    or only in boxes of carriers listed at fewer levels than they ask (`levels`: the levels they ask together; only
    a reference whose full-list listing carries them all is widened, none: (data, None, []); `far`: some ask to be
    drawn from far too, so only a far-listed reference, its far-list leaf box widened as well; `avoid`: references
    already given others, passed over while another will do, so no block wraps another),
    one reference of the top block, its leaf box in the full list widened over all their cells: the shares of the
    nodes on the way down to it grown, every other node's box still holding what it held (its shares worked out
    again, rounded outward), so the game reaches that reference, and the block that will wrap it, wherever they lie,
    from middle distance in, and nothing the map had is lost. Objects past the top block's own box (past the last
    of the map's own scenery: on the decals test copy, 26,960 of them) grow that box too, and so every node's. On
    M03_Italie, a shipped map, every far-listed reference's boxes are the whole map. Picks the reference whose block
    lies nearest them (_widen_choice). Returns (the file, that reference's `at`, notes); (data, None, []) when none
    can: a map whose top block has no tree."""
    top = sc.blocks[0]
    nodes = _tree(top)
    if not nodes or not things:
        return bytes(data), None, []
    close = GRID_CELL[2]
    want = (min(math.floor(p.x / close) * close for p in things),  # every cell they lie in
            min(math.floor(p.y / close) * close for p in things),
            max(math.floor(p.x / close) * close + close for p in things),
            max(math.floor(p.y / close) * close + close for p in things))
    x0, y0, x1, y1 = top.bbox
    root = tuple(top.bbox)
    if not (x0 <= want[0] and y0 <= want[1] and x1 >= want[2] and y1 >= want[3]):  # grown, as the file keeps it
        root = struct.unpack("<4f", struct.pack("<4f", min(x0, want[0] - 1.0), min(y0, want[1] - 1.0),
                                                max(x1, want[2] + 1.0), max(y1, want[3] + 1.0)))
    boxes = _leaf_boxes(top)
    split0 = nodes[0][1]
    children = {it.at for it in top.items if it.kind == "child"}
    far_at = {it.at for it in _far_children(sc)}
    cands = [(e, a) for e, a in enumerate(top.entries) if e >= split0 and a in children and e in boxes]
    if levels:  # every node on its way down carries them (the game ANDs the masks down the chain)
        cands = [(e, a) for e, a in cands
                 if all((nodes[k][0] >> 20) & levels == levels for k in _path(nodes, e))]
    far_entry: dict[int, int] = {}   # a far-listed reference's entry in the far list, its path drawn from far
    if far:
        for ef, a in enumerate(top.entries[:split0]):
            if a in children and ef in boxes and a not in far_entry and \
                    all((nodes[k][0] >> 20) & 0x08 for k in _path(nodes, ef)):
                far_entry[a] = ef
        cands = [(e, a) for e, a in cands if a in far_entry]
    fresh = [c for c in cands if c[1] not in avoid]
    cands = fresh or cands
    if not cands:
        return bytes(data), None, []
    e, at = _widen_choice(sc, cands, things, nodes, far_at)
    toward: dict[int, set] = {}  # the nodes on the way down to entry e (and its far entry): the sides each takes
    for entry in (e, far_entry[at]) if far else (e,):
        for k in _path(nodes, entry):
            toward.setdefault(k, set()).add("L" if entry < nodes[k][1] else "R")
    old: dict = {}  # every node's box and its sides' boxes, as they were
    todo = [(0, tuple(top.bbox))]
    while todo:
        k, box = todo.pop()
        w = nodes[k][0]
        old[k] = (box, *_sides(nodes[k], box))
        if w & 0x10000000:
            continue
        if not w & 0x40000000:
            todo.append((k + 1, old[k][1]))
        if not w & 0x80000000:
            todo.append((k + ((w & 0xFFFFF) >> 2), old[k][2]))

    def union(a, b):
        return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
    new = [list(n) for n in nodes]
    changed = 0
    todo = [(0, root)]
    while todo:
        k, box = todo.pop()
        w, _s, b1, b2 = nodes[k]
        if w & 0x10000000:
            continue
        was, lw, rw = old[k]
        sides = toward.get(k, ())
        lw = union(lw, want) if "L" in sides else lw
        rw = union(rw, want) if "R" in sides else rw
        axis = 0 if w & 3 == 0 else 1
        a0, ext = (box[0], box[2] - box[0]) if axis == 0 else (box[1], box[3] - box[1])
        if box == was:  # its own box as it was: its shares only grow, and only toward entry e
            n1 = max(b1, _share(lw[axis + 2], a0, ext, up=True)) if "L" in sides else b1
            n2 = min(b2, _share(rw[axis], a0, ext, up=False)) if "R" in sides else b2
        else:  # its box grew: shares worked out again to hold what its sides held
            n1, n2 = _share(lw[axis + 2], a0, ext, up=True), _share(rw[axis], a0, ext, up=False)
        new[k][2:] = [n1, n2]
        changed += (n1, n2) != (b1, b2)
        lb, rb = _sides(new[k], box)
        if not w & 0x40000000:
            todo.append((k + 1, lb))
        if not w & 0x80000000:
            todo.append((k + ((w & 0xFFFFF) >> 2), rb))
    if not changed and root == tuple(top.bbox):
        return bytes(data), at, []
    raw = bytearray(top.raw)
    start = (0x20 if top.long else 0x1C) + 4 * len(top.entries)
    if bytes(raw[start:start + len(top.nodes)]) != top.nodes:
        raise SceneryError("the top block's tree isn't where this writer expects it")
    for k, n in enumerate(new):
        struct.pack_into("<IHBB", raw, start + 8 * k, *n)
    struct.pack_into("<4f", raw, 8, *root)  # the block's own box, as Scenery reads it
    out = bytearray(data)
    at_file = sc.data_off + top.offset
    out[at_file:at_file + len(raw)] = raw
    out[:16] = hashlib.md5(bytes(out[16:])).digest()
    grown = Scenery(bytes(out))  # nothing the map had is lost: every entry's leaf box holds its old one
    after = _leaf_boxes(grown.blocks[0])
    if any(not (after[i][0] <= b[0] and after[i][1] <= b[1] and after[i][2] >= b[2] and after[i][3] >= b[3])
           for i, b in boxes.items()) or \
            any(not (after[i][0] <= want[0] and after[i][1] <= want[1] and after[i][2] >= want[2]
                     and after[i][3] >= want[3]) for i in ((e, far_entry[at]) if far else (e,))):
        raise SceneryError("widening the top block's tree lost a box")
    where = ("away from the map's own scenery listed at their detail levels" if levels else
             "in open ground, away from the map's own scenery")
    it = next(i for i in top.items if i.at == at)
    gap = _box_gap(_world_box(sc, it), things) / 260.0
    return bytes(out), at, [f"{len(things)} new object(s) {where}: one block's box in the map's draw tree widened to "
                            f"reach them{' (its far view too)' if far else ''}, a block {gap:.0f} m from them "
                            f"({changed} of the tree's {len(nodes)} node(s) changed)"]


def _box_gap(box: tuple, things: list) -> float:
    """How far (map units) a world box (x0, y0, x1, y1) lies from the middle of `things`."""
    mx, my = sum(p.x for p in things) / len(things), sum(p.y for p in things) / len(things)
    x0, y0, x1, y1 = box
    return math.hypot(max(x0 - mx, 0.0, mx - x1), max(y0 - my, 0.0, my - y1))


def _widen_choice(sc: Scenery, cands: list, things: list, nodes: list, far_at: set) -> tuple[int, int]:
    """Which (full-list entry, reference `at`) _widen stretches over `things`: the reference whose block lies nearest
    them, then the one fewest nodes down. (Before 2026-10-15 it was the fewest nodes down, far-listed first, the
    biggest box: on the blank farm a block 5.6 km off took 30,183 copied plants in four nested blocks, and none was
    drawn in the game; field 7's, hung on a block 218 m off, were.)"""
    items = {it.at: it for it in sc.blocks[0].items}
    return min(cands, key=lambda c: (_box_gap(_world_box(sc, items[c[1]]), things), len(_path(nodes, c[0]))))


# --- road pieces filed where the map files its own: among a block's items, in the leaf of its tree that holds them ---
@dataclass
class _Leaf:
    node: int      # the tree node it hangs from
    side: str      # "L" or "R": that node's left or right side; "W": the node is a leaf itself
    lo: int        # its entries: [lo, hi)
    hi: int
    box: tuple     # in its block's own coordinates
    path: list     # [(node, "L" / "R" / "W")] from the root down to it


def _leaves(nodes: list, n: int, bbox: tuple) -> list[_Leaf]:
    """Every leaf of a block's tree (`nodes` as _tree gives them, over `n` entries), empty ones too, but the far-view
    list's (a root seen from far lists those items on its left side, and the shipped maps list no road piece there)
    and a side whose entries run backwards: a node that splits before its own first entry, as the full list's node
    does in the top block of M03_Italie and 8 other maps (113 such sides in the blocks the maps place once). The
    game's walk finds nothing on such a side, and an entry added at its end went in front of the block's far-view
    list, so the game drew the new entries from far instead of what the list held (on M03_Italie: the whole map)."""
    out, steps = [], 0
    if not nodes:
        return out
    far = bool((nodes[0][0] >> 20) & 0x08)
    todo = [(0, 0, n, tuple(bbox), [])]
    while todo:
        k, lo, hi, box, path = todo.pop()
        steps += 1
        if not 0 <= k < len(nodes) or steps > len(nodes):
            raise SceneryError("a block's tree points outside itself")
        w, split, b1, b2 = nodes[k]
        if w & 0x10000000:
            out.append(_Leaf(k, "W", lo, hi, box, path + [(k, "W")]))
            continue
        x0, y0, x1, y1 = box
        if w & 3 == 0:
            left, right = (x0, y0, x0 + b1 / 255 * (x1 - x0), y1), (x0 + b2 / 255 * (x1 - x0), y0, x1, y1)
        else:
            left, right = (x0, y0, x1, y0 + b1 / 255 * (y1 - y0)), (x0, y0 + b2 / 255 * (y1 - y0), x1, y1)
        if not (k == 0 and far) and lo <= split <= hi:
            if w & 0x40000000:
                out.append(_Leaf(k, "L", lo, split, left, path + [(k, "L")]))
            else:
                todo.append((k + 1, lo, split, left, path + [(k, "L")]))
        if split <= hi:
            if w & 0x80000000:
                out.append(_Leaf(k, "R", max(split, lo), hi, right, path + [(k, "R")]))
            else:
                todo.append((k + ((w & 0xFFFFF) >> 2), max(split, lo), hi, right, path + [(k, "R")]))
    return out


def _one_more(nodes: list, path: list) -> None:
    """`nodes` ([word, split, b1, b2] each) with one entry added at the end of the leaf `path` leads to: a node whose
    left side holds that leaf, or that comes after it in the entries' order, splits one entry later; the rest keep
    their splits (a node that's a leaf itself has none: 0 on every shipped map)."""
    way = dict(path)
    todo = [(0, "on")]
    while todo:
        k, where = todo.pop()
        w = nodes[k][0]
        if w & 0x10000000:
            continue
        if where == "on":
            left, right = ("on", "after") if way[k] == "L" else ("before", "on")
        else:
            left = right = where
        if where == "after" or (where == "on" and way[k] == "L"):
            if nodes[k][1] >= 0xFFFF:
                raise SceneryEditError("a block of the map's scenery holds too many items to take more")
            nodes[k][1] += 1
        for child, side, leaf in ((k + 1, left, 0x40000000), (k + ((w & 0xFFFFF) >> 2), right, 0x80000000)):
            if not w & leaf and side != "before":
                todo.append((child, side))


def _grown(b: Block, adds: list, count: int | None = None) -> tuple[bytes, list[int]]:
    """Block `b` with items added, each at the end of its leaf's entries (`adds`: [((node, side), the item's bytes)])
    and after the block's last item, the nodes on the way to it given the road mark (those with a LOD mask), its
    road pieces' count word set to `count` (None: left as it is), padded to 16 bytes as the shipped blocks are.
    Every item it had keeps its offset and its leaf. Returns (the block, the new items' offsets)."""
    nodes = [list(n) for n in _tree(b)]
    entries = list(b.entries)
    head = 0x20 if b.long else 0x1C
    end = max((it.at + 4 + len(it.data) for it in b.items), default=4)
    body = bytearray(b.raw[b.items_start:b.items_start + end])
    if count is not None:
        for it in b.items:
            if it.kind == "road":
                struct.pack_into("<I", body, it.at + 4 + 48, count)
    ats = []
    for key, item in adds:
        leaf = next((lf for lf in _leaves(nodes, len(entries), b.bbox) if (lf.node, lf.side) == key), None)
        if leaf is None:
            raise SceneryError(f"block {b.index} has no leaf {key} to add to")
        entries.insert(leaf.hi, len(body))
        _one_more(nodes, leaf.path)
        for k, _d in leaf.path:
            if (nodes[k][0] >> 20) & ALL_TIERS:
                nodes[k][0] |= ROAD_BIT
        ats.append(len(body))
        body += item
    if nodes and (nodes[0][0] >> 20) & 0x08:  # a block seen from far keeps its far-view list exactly as it was
        far = struct.unpack_from("<H", b.nodes, 4)[0]
        if nodes[0][1] != far or entries[:far] != list(b.entries[:far]):
            # not a game rule: a check on this writer's own output
            raise SceneryError(f"block {b.index}: a road piece would have gone into its far-view list (a mistake in "
                               f"this writer, not in the mod: please report it)")
    (w0,) = struct.unpack_from("<I", b.raw)
    out = (struct.pack("<I", (w0 & 0x80000000) | len(entries)) + b.raw[4:head]
           + struct.pack(f"<{len(entries)}I", *entries) + b"".join(struct.pack("<IHBB", *n) for n in nodes)
           + bytes(body))
    return out + b"\0" * (-len(out) % 16), ats


def _with_blocks(sc: Scenery, data: bytes, raws: dict[int, bytes]) -> bytes:
    """The scenery file with blocks replaced by `raws` (block index -> its new bytes, as _grown makes them), every
    reference, theirs and the new ones alike, pointed at where its block now starts, and the tables after the blocks
    moved with their end."""
    starts, pos = {}, 0
    for b in sc.blocks:
        starts[b.offset] = pos
        pos += len(raws.get(b.index, b.raw))
    if pos > DATA_LIMIT:
        raise SceneryEditError(f"the map's scenery would grow to {pos:,} bytes, past the {DATA_LIMIT:,} a map can hold")
    parts = []
    for b in sc.blocks:
        raw = bytearray(raws.get(b.index, b.raw))
        grown = sc._block(b.index, starts[b.offset], bytes(raw))
        for it in grown.items:
            if it.kind == "child":
                if it.child_offset not in starts:
                    raise SceneryError(f"block {b.index}: a child points at {it.child_offset}, which isn't a block's start")
                struct.pack_into("<I", raw, grown.items_start + it.at, link_word(it.word, starts[it.child_offset]))
        parts.append(bytes(raw))
    f = list(sc.fields)
    tab_off, tab_n, data_off, data_len = f[0], f[1], f[2], f[3]
    if tab_off != 124 or data_off != tab_off + 4 * tab_n:
        raise SceneryError("the scenery file's tables aren't in the order this writer knows")
    end = data_off + data_len
    for k in (4, 6, 8, 10, 12, 20, 22, 24):  # the tables after the blocks move with their end
        if f[k] < end:
            raise SceneryError("the scenery file's tables aren't in the order this writer knows")
        f[k] += pos - data_len
    f[3] = pos
    table = [starts[b.offset] for b in sc.blocks] + [pos]
    body = VERSION + struct.pack("<26I", *f) + struct.pack(f"<{tab_n}I", *table) + b"".join(parts) + data[end:]
    return hashlib.md5(body).digest() + body


def _homes(sc: Scenery) -> list[tuple]:
    """Where a road piece can be filed: every full-list leaf of every block the map places once, as (block index,
    (node, side), its bounds on the map, its way down already has the road mark, its area on the map, its box in the
    block's own coordinates, the map-to-block transform). A leaf whose way down has a node with neither a LOD mask nor
    the road mark is left out (marking it would leave that node the road pass only)."""
    _weight, where = sc.placings()
    out = []
    for b in sc.blocks:
        m = where[b.index]
        if m is None or not b.nodes:
            continue
        to_local = _inverse(m)
        scale = abs(m[0] * m[5] - m[1] * m[4])
        nodes = _tree(b)
        for leaf in _leaves(nodes, len(b.entries), b.bbox):
            words = [nodes[k][0] for k, _d in leaf.path]
            marked = all(w & ROAD_BIT for w in words)
            if not marked and not all(w & ROAD_BIT or (w >> 20) & ALL_TIERS for w in words):
                continue
            x0, y0, x1, y1 = leaf.box
            xs = [m[0] * x + m[1] * y + m[3] for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
            ys = [m[4] * x + m[5] * y + m[7] for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
            out.append((b.index, (leaf.node, leaf.side), (min(xs), min(ys), max(xs), max(ys)), marked,
                        (x1 - x0) * (y1 - y0) * scale, leaf.box, to_local))
    return out


def _holds(home: tuple, x: float, y: float) -> bool:
    """Whether a _homes leaf holds the map point (x, y): within its bounds on the map, then within its own box (a
    turned block's leaf covers less than its bounds)."""
    bx0, by0, bx1, by1 = home[2]
    if not (bx0 <= x <= bx1 and by0 <= y <= by1):
        return False
    m, (x0, y0, x1, y1) = home[6], home[5]
    lx, ly = m[0] * x + m[1] * y + m[3], m[4] * x + m[5] * y + m[7]
    return x0 <= lx <= x1 and y0 <= ly <= y1


def file_roads(data: bytes, pieces: list[RoadPiece]) -> tuple[bytes, list[RoadPiece], list[str]]:
    """Road pieces filed the way the map files its own: each among the items of a block the map places once, in the
    leaf of that block's tree whose box holds the piece's middle (the smallest such leaf, one whose way down already
    has the road mark first), listed for close view only, with the block's count of pieces on every piece of it (on
    D-Day the top block files 25 of the map's own pieces so, out in the open, and all 77 of a new 480 m road find a
    leaf there). No block is added and no item moves; the nodes on the way down, in the block and in the blocks that
    place it, get the road mark. Returns (file, the pieces no leaf holds, notes)."""
    if not pieces:
        return bytes(data), [], []
    sc = Scenery(data)
    style = _road_style(sc)
    if style is None:
        return bytes(data), list(pieces), []
    homes = _homes(sc)
    filed: dict[int, list] = {}
    left = []
    for p in pieces:
        hold = [h for h in homes if _holds(h, p.x, p.y)]
        if not hold:
            left.append(p)
            continue
        home = min(hold, key=lambda h: (not h[3], h[4]))
        filed.setdefault(home[0], []).append((home[1], p))
    if not filed:
        return bytes(data), left, []
    _weight, where = sc.placings()
    raws, added = {}, {}
    for bi, got in filed.items():
        b = sc.blocks[bi]
        count = sum(1 for it in b.items if it.kind == "road") + len(got)
        to_local = _inverse(where[bi])
        adds = [(key, _road_item(p, to_local, style, count)[0]) for key, p in got]
        raws[bi], added[bi] = _grown(b, adds, count)
    out = _with_blocks(sc, data, raws)
    # the road mark on the way down to each new piece, from the map's top (a block placed once has one way)
    grown = Scenery(out)
    lo, n = grown.data_off, grown.fields[3]
    blob = bytearray(out[lo:lo + n])
    for bi, ats in added.items():
        for at in ats:
            _mark_for_roads(grown, blob, bi, at)
    body = out[16:lo] + bytes(blob) + out[lo + n:]
    out = hashlib.md5(body).digest() + body
    where_to = ", ".join(f"{'the top block' if bi == 0 else f'block {bi}'} ({len(got)})" for bi, got in filed.items())
    return out, left, [f"{sum(len(g) for g in filed.values())} road sticker piece(s) filed with the map's own, in the "
                       f"leaf of a block's tree that holds each: {where_to}"]


# The scenery's three grids, one record per cell: the game walks a cell at a level of detail only when its record
# says it holds something (checked on all 32 shipped maps: no placed object lies in a cell its level skips).
GRID_CELL = (81920.0, 20480.0, 5120.0)   # far, middle, close: map units a cell is across
GRID_RECORD = (4, 5, 3)                  # bytes a cell's record has; its third byte counts the cell's objects (/64)


def _cell_walked(rec: bytes, level: int) -> bool:
    if level == 2:
        return 1 <= rec[2] <= 0xFE
    if rec[2] == 0xFF:
        return False
    return any(rec[2:4]) if level == 0 else any(rec[2:5])


def _grids_hold(data: bytes, points: list[tuple[float, float]]) -> tuple[bytes, int]:
    """The scenery file with every cell that holds one of `points` (new objects' places) marked as holding something
    at all three levels of detail, so the game walks it (an empty cell is skipped: a new object there would be
    skipped at that distance: in a built D-Day, 2 of 4 new bridges lay in such cells, found in the file, not seen in
    the game). Returns (file, cells marked). Raises
    SceneryEditError for a point outside a grid: the game never walks there."""
    sc = Scenery(data)
    out = bytearray(data)
    marked = set()
    for x, y in points:
        for level in range(3):
            w, h = sc.grid_dims[2 * level], sc.grid_dims[2 * level + 1]
            cx, cy = math.floor(x / GRID_CELL[level]), math.floor(y / GRID_CELL[level])
            if not (0 <= cx < w and 0 <= cy < h):
                # rule: scenery-grid
                raise SceneryEditError(f"({x:.0f}, {y:.0f}) is outside the map's scenery grid ({w} x {h} cells of "
                                       f"{GRID_CELL[level]:.0f}), where the game draws nothing")
            at = sc.grids[level][0] + (cx * h + cy) * GRID_RECORD[level]
            if at + GRID_RECORD[level] > sc.grids[level][0] + sc.grids[level][1]:
                raise SceneryError("the scenery file's grid is shorter than its size says")
            if not _cell_walked(out[at:at + GRID_RECORD[level]], level):
                out[at + 2] = 1
                marked.add((level, cx, cy))
    if not marked:
        return bytes(data), 0
    out[:16] = hashlib.md5(bytes(out[16:])).digest()
    return bytes(out), len(marked)


def _wrap(sc: Scenery, data: bytes, objects: list[NewObject], far: list[Item],
          carrier: Item | None = None) -> tuple[bytes, list[str]]:
    """`objects` in a new block that wraps a block the top block lists for far view: `carrier`, the reference to it,
    else the one nearest the objects (add_objects)."""
    index = {name: i for i, name in enumerate(sc.names[:len(sc.flags)]) if sc.flags[i] == 1}
    words: dict[int, int] = {}
    for b in sc.blocks:
        for it in b.items:
            if it.kind == "object":
                words.setdefault(it.symbol, it.word & WORD_KEEP)
    cx, cy = sum(o.x for o in objects) / len(objects), sum(o.y for o in objects) / len(objects)

    def score(it):  # how far the group's middle is from the block's box (0 inside), then the smaller box
        x0, y0, x1, y1 = _world_box(sc, it)
        return math.hypot(max(x0 - cx, 0.0, cx - x1), max(y0 - cy, 0.0, cy - y1)), (x1 - x0) * (y1 - y0)
    if carrier is None:
        carrier = min(far, key=score)
    roads = sum(1 for o in objects if isinstance(o, RoadPiece))
    top = sc.blocks[0]
    ins = top.offset + len(top.raw)  # the new block goes right after the top block
    if len(sc.blocks) > 1 and sc.blocks[1].offset != ins:
        raise SceneryError("the scenery file's blocks aren't in the order this writer knows")
    to_local = _inverse(carrier.matrix())
    inner = sc.block_at(carrier.child_offset)
    items, xs, ys = [], [inner.bbox[0], inner.bbox[2]], [inner.bbox[1], inner.bbox[3]]
    boxes = [tuple(inner.bbox)]  # each item's box in the new block, for its tree: the old block's own first
    levels = [0]                 # each item's LOD mask (NewObject.levels): the old block drawn as before
    style = _road_style(sc)
    for o in objects:
        if isinstance(o, RoadPiece):
            if style is None:
                raise SceneryEditError("this map has no road stickers to copy, so a new road can't get road pieces")
            body, px, py = _road_item(o, to_local, style, roads)
            items.append(body)
            xs += px
            ys += py
            boxes.append((min(px), min(py), max(px), max(py)))
            levels.append(0)
            continue
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
        boxes.append((local[3] - pad, local[7] - pad, local[3] + pad, local[7] + pad))
        levels.append(o.levels)
    probe = _new_block([b"\0" * 4] + items, (0.0, 0.0, 0.0, 0.0), boxes, levels)  # its size: where the old block moves
    shift = len(probe)
    moved_to = carrier.child_offset + shift
    if sc.fields[3] + shift > DATA_LIMIT:
        raise SceneryEditError("the map's scenery is too big for a new block to be referenced")
    # the old block, placed where it was (no transform: the reference to the new block keeps the old one's)
    first = struct.pack("<I", link_word(carrier.word & 0xFF000000, moved_to) | T_IDENTITY)
    new = _new_block([first] + items, (min(xs), min(ys), max(xs), max(ys)), boxes, levels)
    if len(new) != shift:
        raise SceneryError("a new block came out a different size than measured")
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
            struct.pack_into("<I", raw, at, link_word(it.word, target))
        if b.index == 0 and roads:  # the top block's nodes down to the new block's reference: road-marked
            _mark_road_path(raw, b, carrier.at)
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
        f"{_counted(objects)} added in a new block with block {inner.index} (drawn from far, {far_m:.0f} m "
        f"from them), placed where the top block had it"]


def _counted(items: list) -> str:
    pieces = sum(1 for o in items if isinstance(o, RoadPiece))
    parts = [f"{len(items) - pieces} object(s)" if len(items) > pieces else "",
             f"{pieces} road sticker piece(s)" if pieces else ""]
    return " and ".join(p for p in parts if p)


def _add_block(data: bytes, objects: list[NewObject]) -> tuple[bytes, list[str]]:
    sc = Scenery(data)
    index = {name: i for i, name in enumerate(sc.names[:len(sc.flags)]) if sc.flags[i] == 1}  # not Route etc.
    words: dict[int, int] = {}  # a placed item's high bits (its LOD tier and variation) per type
    for b in sc.blocks:
        for it in b.items:
            if it.kind == "object":
                words.setdefault(it.symbol, it.word & WORD_KEEP)
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
    style = _road_style(sc)
    roads = sum(1 for o in objects if isinstance(o, RoadPiece))
    for o in objects:
        if isinstance(o, RoadPiece):
            if style is None:
                raise SceneryEditError("this map has no road stickers to copy, so a new road can't get road pieces")
            body, px, py = _road_item(o, to_local, style, roads)
            items.append(body)
            xs += px
            ys += py
            continue
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
    pad = MARGIN * max([1.0] + [o.size for o in objects if not isinstance(o, RoadPiece)])
    new = _new_block(items, (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad))
    f = list(sc.fields)
    tab_off, tab_n, data_off, data_len = f[0], f[1], f[2], f[3]
    if tab_off != 124 or data_off != tab_off + 4 * tab_n:
        raise SceneryEditError("the scenery file's tables aren't in the order this writer knows")
    offset = data_len  # the new block goes after every other block: all references stay forward
    if offset > DATA_LIMIT:
        raise SceneryEditError("the map's scenery is too big for a new block to be referenced")
    ref = link_word(carrier.word & 0x0C000000, offset) | carrier.tform
    patched = bytearray(data[data_off:data_off + data_len])
    at = block.offset + block.items_start + carrier.at
    patched[at:at + 4 + len(carrier.data)] = struct.pack("<I", ref) + _identity_data(carrier.tform)
    if roads:  # every tree node from the map's top down to the new block's reference: road-marked
        _mark_for_roads(sc, patched, block.index, carrier.at)
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
    notes.append(f"{_counted(objects)} added in a new block, hung on {sc.names[carrier.symbol]} in block "
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


# --- the map's own objects moved, turned, resized or taken away ([[own]], MOD_FORMAT §8; the owner, 2026-10-16:
# "select move and delete things already placed, including what's on the map") ---
OWN_PICK = 26.0   # map units (a tenth of a metre): how near an [[own]] row's place an object of its type must stand to
                  # be the one it means; the row holds the place the map's file has, read by the Studio (objects_near)


@dataclass(frozen=True)
class OwnEdit:
    """One of the map's own objects: the one of `type` standing at (x, y) in the map's file goes (an erase of that
    object alone), and unless `gone` the same type is placed again at (to_x, to_y), turned and sized, as a placed
    object (units go round it when `solid`: a building). `open`: how far round its old place the ground opens to every
    unit and loses its blocked mark (a building's reach times its size, worked out by the Studio as a placed
    building's footprint is: nav.solid_blocks); 0 for anything else. Made of the two things the game already takes
    from a mod (an erase, a placed object), so a moved object is a placed one."""
    type: str
    x: float
    y: float
    gone: bool = False
    to_x: float = 0.0
    to_y: float = 0.0
    turn: float = 0.0     # degrees, as a placed object's
    size: float = 1.0
    lift: float = 0.0
    solid: bool = False
    open: float = 0.0

    def expand(self) -> list:
        """What the build makes of it: the erase, then the object placed again (unless it's gone)."""
        out: list = [EraseArea(self.x, self.y, OWN_PICK, (), (self.type,), opens=self.open)]
        if not self.gone:
            out.append(NewObject(self.type, self.to_x, self.to_y, self.turn, self.size, self.solid, lift=self.lift))
        return out


OWN_KEYS = ("type", "x", "y", "gone", "to_x", "to_y", "turn", "size", "lift", "solid", "open")


def parse_own(rows: list, where: str = "scenery.toml") -> list[OwnEdit]:
    out = []
    for k, row in enumerate(rows):
        extra = sorted(set(row) - set(OWN_KEYS))
        if extra:
            raise SceneryEditError(f"{where}: own object {k + 1}: unknown key {extra[0]!r}")
        for flag in ("gone", "solid"):
            if not isinstance(row.get(flag, False), bool):
                raise SceneryEditError(f"{where}: own object {k + 1}: {flag} must be true or false")
        gone = row.get("gone", False)
        if not gone and ("to_x" not in row or "to_y" not in row):
            raise SceneryEditError(f"{where}: own object {k + 1}: say where it goes (to_x, to_y), or gone = true")
        try:
            e = OwnEdit(str(row["type"]), float(row["x"]), float(row["y"]), gone, float(row.get("to_x", 0.0)),
                        float(row.get("to_y", 0.0)), float(row.get("turn", 0.0)), float(row.get("size", 1.0)),
                        float(row.get("lift", 0.0)), row.get("solid", False), float(row.get("open", 0.0)))
        except KeyError as exc:
            raise SceneryEditError(f"{where}: own object {k + 1} has no {exc.args[0]}") from None
        except (TypeError, ValueError):
            raise SceneryEditError(f"{where}: own object {k + 1}: x, y, to_x, to_y, turn, size, lift and open must be "
                                   f"numbers") from None
        nums = (e.x, e.y, e.to_x, e.to_y, e.turn, e.size, e.lift, e.open)
        if (not e.type or not all(math.isfinite(v) for v in nums) or not 0.05 <= e.size <= 50 or abs(e.lift) > 100000
                or not 0 <= e.open <= ERASE_MAX):
            raise SceneryEditError(f"{where}: own object {k + 1}: a number is out of range (size: 0.05 to 50, lift: "
                                   f"within 100,000, open: 0 to {ERASE_MAX:,.0f})")
        out.append(e)
    return out


def _own_lines(e: OwnEdit) -> list[str]:
    lines = ["[[own]]", f'type = "{e.type}"', f"x = {e.x!r}", f"y = {e.y!r}"]
    if e.gone:
        lines.append("gone = true")
    else:
        lines += [f"to_x = {e.to_x!r}", f"to_y = {e.to_y!r}", f"turn = {e.turn!r}", f"size = {e.size!r}"]
        lines += ([f"lift = {e.lift!r}"] if e.lift else []) + (["solid = true"] if e.solid else [])
    return lines + ([f"open = {e.open!r}"] if e.open else []) + [""]


def objects_near(sc: Scenery, x: float, y: float, radius: float, only=None, placed=None) -> list[tuple]:
    """(distance, name index, transform in map coordinates) of every object whose middle lies within `radius` of
    (x, y), nearest first. Only the blocks whose box reaches the circle are opened (a map places millions of objects:
    D-Day 13.6 million trees, props and buildings, 45 s to walk all of them). `only`: name indexes; `placed`:
    _placed_items(sc) made once for the map (it reads every block)."""
    items, boxes = placed if placed is not None else _placed_items(sc)
    r2, out = radius * radius, []
    todo = [(r, IDENTITY) for r in sc.roots()]
    while todo:
        bi, m = todo.pop()
        box = boxes[bi]
        if box is None:
            continue
        xs = [m[0] * bx + m[1] * by + m[3] for bx, by in ((box[0], box[1]), (box[2], box[1]), (box[0], box[3]),
                                                          (box[2], box[3]))]
        ys = [m[4] * bx + m[5] * by + m[7] for bx, by in ((box[0], box[1]), (box[2], box[1]), (box[0], box[3]),
                                                          (box[2], box[3]))]
        if x + radius < min(xs) or x - radius > max(xs) or y + radius < min(ys) or y - radius > max(ys):
            continue
        hits = []
        for entry in items[bi]:
            if entry[1] == -1:
                todo.append((entry[2], compose(m, entry[3])))
                continue
            at, sym, ox, oy, oz = entry[:5]
            if only is not None and sym not in only:
                continue
            wx = m[0] * ox + m[1] * oy + m[2] * oz + m[3]
            wy = m[4] * ox + m[5] * oy + m[6] * oz + m[7]
            d2 = (wx - x) ** 2 + (wy - y) ** 2
            if d2 <= r2:
                hits.append((d2, at, sym))
        if hits:
            by_at = {it.at: it for it in sc.blocks[bi].items}
            out += [(math.sqrt(d2), sym, compose(m, by_at[at].matrix())) for d2, at, sym in hits]
    out.sort(key=lambda h: h[0])
    return out


def objects_toml(objects: list[NewObject], header: str = "", erase: list[EraseArea] = (),
                 own: list[OwnEdit] = ()) -> str:
    lines = [f"# {ln}" if ln else "#" for ln in header.splitlines()] + ([""] if header else [])
    for a in erase:
        lines += ["[[erase]]", f"x = {a.x!r}", f"y = {a.y!r}", f"radius = {a.radius!r}"]
        if a.shape != "round":
            lines.append(f'shape = "{a.shape}"')
        if a.shape == "square" and (a.dx, a.dy) != (1.0, 0.0):
            lines += [f"dx = {a.dx!r}", f"dy = {a.dy!r}"]
        if a.shape == "line":
            lines += [f"x2 = {a.x2!r}", f"y2 = {a.y2!r}"]
        lines += [f"what = [{', '.join(json.dumps(g) for g in a.what)}]"] if tuple(a.what) != ERASE_DEFAULT else []
        lines += ([f"types = [{', '.join(json.dumps(t) for t in a.types)}]"] if a.types else []) + [""]
    for o in objects:
        lines += ["[[object]]", f'type = "{o.type}"', f"x = {o.x!r}", f"y = {o.y!r}", f"turn = {o.turn!r}",
                  f"size = {o.size!r}"] + ([] if o.solid else ["solid = false"])
        lines += ([f"stretch = {o.stretch!r}"] if o.stretch != 1.0 else []) + ([f"lift = {o.lift!r}"] if o.lift else []) + [""]
    for e in own:
        lines += _own_lines(e)
    return "\n".join(lines) + "\n" if lines else "\n"


def placement(m: tuple) -> tuple[float, float, float, float]:
    """x, y, the turn (radians, counterclockwise from +x) and the size (the scale along the object's own x) of a
    placed object's transform."""
    return m[3], m[7], math.atan2(m[4], m[0]), math.hypot(m[0], m[4])
