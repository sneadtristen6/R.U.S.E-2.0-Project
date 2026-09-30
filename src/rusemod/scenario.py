"""A map's scenario file (`test\\map\\<map>\\leveldesign*.scenario` in DataMap_Win.dat): its zones and its design
items (where players start, where reinforcements arrive, the names on the map). Read-only.

The layout was first worked out for Wargame by enohka's moddingSuite (and RugnirViking's RUSE fork of it); R.U.S.E.'s
files are the same except for the list at the end of each zone (Wargame writes it empty). Read from those notes and
checked on every scenario R.U.S.E. ships (102 files, every byte accounted for).

    "SCENARIO\\r\\n"            10 bytes
    16 bytes                    MD5 of bytes 0-9 and of byte 28 to the end (LittleGroove's rule; the game checks it)
    2 bytes                     0
    u32 version                 4
    u32 1
    u32 n, n bytes              the zones (below)
    u32 n, n bytes              an NDF (EUG0/CNDF): the design items

The zones: u32 count, then per zone (every `AREA` is those 4 bytes):
    AREA, u32 2, u32 number, u32 name length, the name (UTF-8, zero-padded to a multiple of 4: `zone_<guid>`)
    AREA, 3 f32: the point the zone hangs from (x, y, z)
    AREA, u32 n, n x (u32 first triangle, u32 triangles, u32 first vertex, u32 vertices): the zone cut into parts
    AREA, 4 u32: the border's triangles (first, count, first vertex, count)
    AREA, 2 u32: the border's vertices (first, count)
    AREA, u32 vertices, u32 triangles, per vertex 5 f32 (x, y, z, w, and a 0/1 "centre" flag), AREA,
        per triangle 3 u32 (vertex numbers)
    AREA, u32 n, n u32 (R.U.S.E.: which border vertices close the outline; Wargame: n = 0), AREA, "END0"

The design items (TGameDesignItem, listed by the one TGameDesignItemList): a Position (3 f32, world units), an
optional Rotation (f32, radians) and an AddOn saying what it is: TGameDesignAddOn_StartingPoint (a player's start),
_Spawn (where reinforcements arrive), _LabelVille and _LabelMontagne (a town's or a mountain's name on the map), and
others on some maps.

Writing: `Scenario.to_bytes()` gives the file back; unchanged, byte for byte (all 102). `move()` puts a design item
somewhere else (its Position, and its Rotation when it has one); the NDF is then written again by rusemod.ndf, and
the checksum made again.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field

from .ndf import Ndf, local_ref

MAGIC = b"SCENARIO\r\n"
AREA = b"AREA"


class ScenarioError(ValueError):
    pass


@dataclass
class Zone:
    number: int
    name: str
    anchor: tuple                                    # x, y, z
    vertices: list = field(default_factory=list)     # (x, y, z, w, centre)
    triangles: list = field(default_factory=list)    # (a, b, c)
    parts: list = field(default_factory=list)        # (first triangle, triangles, first vertex, vertices)
    border_triangles: tuple = (0, 0, 0, 0)
    border_vertices: tuple = (0, 0)
    outline: list = field(default_factory=list)      # the list at the end (R.U.S.E. only)
    stored_name: tuple = (0, b"")                    # (length, bytes with their padding) as read, to write back

    def outline_points(self) -> list[tuple]:
        """The zone's border as (x, y) points: its border vertices in order."""
        first, count = self.border_vertices
        return [self.vertices[i][:2] for i in range(first, first + count) if i < len(self.vertices)]


@dataclass
class Item:
    kind: str            # the AddOn's class without "TGameDesignAddOn_": StartingPoint, Spawn, LabelVille, ...
    position: tuple      # x, y, z
    rotation: float      # radians (0 when the item has none)
    values: dict         # the AddOn's own values: name -> number or text
    obj: int = -1        # its object in the scenario's NDF (for moving it)


class _Reader:
    def __init__(self, data: bytes):
        self.d, self.p = data, 0

    def u32(self) -> int:
        v = struct.unpack_from("<I", self.d, self.p)[0]
        self.p += 4
        return v

    def f32(self) -> float:
        v = struct.unpack_from("<f", self.d, self.p)[0]
        self.p += 4
        return v

    def take(self, n: int) -> bytes:
        v = self.d[self.p:self.p + n]
        if len(v) != n:
            raise ScenarioError(f"the file ends {n - len(v)} bytes early")
        self.p += n
        return v

    def area(self) -> None:
        if self.take(4) != AREA:
            raise ScenarioError(f"AREA expected at byte {self.p - 4}")


def _zone(r: _Reader) -> Zone:
    r.area()
    if r.u32() != 2:
        raise ScenarioError("a zone of another version than 2")
    number = r.u32()
    n = r.u32()
    stored = r.take((n + 3) // 4 * 4)
    name = stored[:n].rstrip(b"\0").decode("utf-8", "replace")
    r.area()
    anchor = (r.f32(), r.f32(), r.f32())
    r.area()
    parts = [(r.u32(), r.u32(), r.u32(), r.u32()) for _ in range(r.u32())]
    r.area()
    border_tri = (r.u32(), r.u32(), r.u32(), r.u32())
    r.area()
    border_vtx = (r.u32(), r.u32())
    r.area()
    nv, nt = r.u32(), r.u32()
    vertices = [(r.f32(), r.f32(), r.f32(), r.f32(), r.f32()) for _ in range(nv)]
    r.area()
    triangles = [(r.u32(), r.u32(), r.u32()) for _ in range(nt)]
    r.area()
    outline = [r.u32() for _ in range(r.u32())]
    r.area()
    if r.take(4) != b"END0":
        raise ScenarioError(f"END0 expected at byte {r.p - 4}")
    return Zone(number, name, anchor, vertices, triangles, parts, border_tri, border_vtx, outline, (n, stored))


def _zone_bytes(z: Zone) -> bytes:
    """A zone as stored (the reverse of _zone). A zone read from a file keeps its name's stored bytes."""
    n, stored = z.stored_name
    if not stored or stored[:n].rstrip(b"\0").decode("utf-8", "replace") != z.name:
        raw = z.name.encode("utf-8")
        n, stored = len(raw), raw + bytes(-len(raw) % 4)
    out = bytearray(AREA + struct.pack("<3I", 2, z.number, n) + stored)
    out += AREA + struct.pack("<3f", *z.anchor)
    out += AREA + struct.pack("<I", len(z.parts)) + b"".join(struct.pack("<4I", *pt) for pt in z.parts)
    out += AREA + struct.pack("<4I", *z.border_triangles)
    out += AREA + struct.pack("<2I", *z.border_vertices)
    out += AREA + struct.pack("<2I", len(z.vertices), len(z.triangles))
    out += b"".join(struct.pack("<5f", *v) for v in z.vertices)
    out += AREA + b"".join(struct.pack("<3I", *tri) for tri in z.triangles)
    out += AREA + struct.pack("<I", len(z.outline)) + b"".join(struct.pack("<I", i) for i in z.outline)
    out += AREA + b"END0"
    return bytes(out)


@dataclass
class Scenario:
    version: int
    zones: list
    items: list
    head: bytes = MAGIC + bytes(18)   # the header up to the version: magic, the 16-byte checksum, 2 zero bytes
    one: int = 1                      # the u32 after the version
    ndf: Ndf | None = None            # the design items' NDF, as read
    ndf_raw: bytes = b""              # its bytes as read (written back as they are until something moves)
    changed: bool = False

    @classmethod
    def read(cls, data: bytes) -> "Scenario":
        if data[:10] != MAGIC:
            raise ScenarioError("not a scenario file (no SCENARIO header)")
        r = _Reader(data)
        r.p = 28
        version = r.u32()
        one = r.u32()
        zone_data = r.take(r.u32())
        z = _Reader(zone_data)
        zones = [_zone(z) for _ in range(z.u32())]
        if z.p != len(zone_data):
            raise ScenarioError(f"{len(zone_data) - z.p} bytes after the last zone")
        items, nd, raw = [], None, b""
        if r.p < len(data):
            raw = r.take(r.u32())
            nd = Ndf(raw)
            items = _items(nd)
        if r.p != len(data):
            raise ScenarioError(f"{len(data) - r.p} bytes after the design items")
        return cls(version, zones, items, bytes(data[:28]), one, nd, raw)

    def move(self, item: int, x: float, y: float, z: float | None = None, rotation: float | None = None) -> None:
        """Put design item number `item` (in `items`) at x, y (and z; else it keeps its height), turned to `rotation`
        radians when given (only items that have a Rotation can turn)."""
        it = self.items[item]
        o = self.ndf.objects[it.obj]
        props = {self.ndf.prop_name(pi): v for pi, v in o.props}
        pos = props["Position"]
        z = it.position[2] if z is None else z
        pos.payload = struct.pack("<3f", x, y, z) + pos.payload[12:]
        it.position = struct.unpack("<3f", pos.payload[:12])
        if rotation is not None:
            if "Rotation" not in props:
                raise ScenarioError(f"design item {item} ({it.kind}) has no rotation to change")
            props["Rotation"].payload = struct.pack("<f", rotation)
            it.rotation = struct.unpack("<f", props["Rotation"].payload)[0]
        self.changed = True

    def add_spawn(self, x: float, y: float, what: str, camp: int | None = None, rotation: float = 0.0,
                  z: float = 0.0, name: str | None = None) -> int:
        """A new design item that spawns `what` at x, y (world units) when the scenario starts, for side `camp`
        (None: no side, like the shipped depots' -1 is written as it's given), turned `rotation` radians. `what` is
        the game's Python class path of a unit or building (front.parametres.Classes.Unit_M4_Sherman), as the shipped
        spawns name theirs. Returns the new item's number in `items`."""
        from .ndf import Value
        nd = self.ndf
        if nd is None:
            raise ScenarioError("this scenario has no design items to add a spawn to")
        what.encode("latin-1")
        lists = [o for o in nd.objects if nd.classes[o.cls] == "TGameDesignItemList"]
        if len(lists) != 1:
            raise ScenarioError("this scenario's design items aren't in one list")

        def prop(name, cls):
            for i, (n, c) in enumerate(nd.props):
                if n == name and c == cls:
                    return i
            return nd.add_prop(name, cls)

        def string(text):
            i = nd.string_index(text)
            return nd.add_string(text) if i is None else i
        item_cls = nd.class_index("TGameDesignItem")
        spawn_cls = nd.class_index("TGameDesignAddOn_Spawn")
        addon_props = [(prop("PythonClassName", spawn_cls), Value(0x07, struct.pack("<I", string(what))))]
        if camp is not None:
            addon_props.insert(0, (prop("Camp", spawn_cls), Value(0x02, struct.pack("<i", int(camp)))))
        if name:
            addon_props.insert(0, (prop("Name", spawn_cls), Value(0x07, struct.pack("<I", string(name)))))
        addon = nd.add_object(spawn_cls, addon_props)
        item = nd.add_object(item_cls, [
            (prop("Position", item_cls), Value(0x0B, struct.pack("<3f", x, y, z))),
            (prop("Rotation", item_cls), Value(0x05, struct.pack("<f", rotation))),
            (prop("AddOn", item_cls), Value(0x09, struct.pack("<III", 0xBBBBBBBB, addon, spawn_cls)))])
        holder = lists[0]
        ref = Value(0x09, struct.pack("<III", 0xBBBBBBBB, item, item_cls)).encode()
        for k, (pi, v) in enumerate(holder.props):
            if v.tc == 0x11:
                count = struct.unpack_from("<I", v.payload)[0]
                holder.props[k] = (pi, Value(0x11, struct.pack("<I", count + 1) + v.payload[4:] + ref))
                break
        else:  # an empty list is left out of the file (11 shipped scenarios): it gets its first item
            holder.props.append((prop("GameDesignItemList", holder.cls), Value(0x11, struct.pack("<I", 1) + ref)))
        self.items = _items(nd)
        self.changed = True
        return next(i for i, it in enumerate(self.items) if it.obj == item)

    def places(self) -> dict[int, set[int]]:
        """Where players can start: {team (AllianceNum): {places (AlliancePriority)}}."""
        out: dict[int, set[int]] = {}
        for it in self.items:
            if it.kind == "StartingPoint" and isinstance(it.values.get("AllianceNum"), int):
                out.setdefault(it.values["AllianceNum"], set()).add(int(it.values.get("AlliancePriority") or 1))
        return out

    def add_start(self, x: float, y: float, team: int, place: int | None = None,
                  rotation: float | None = None, z: float | None = None) -> int:
        """A new starting point at x, y (and height z: the ground's, as every shipped one has it) for `team`
        (AllianceNum), at `place` (AlliancePriority; default: the team's next). It copies a starting point of the same
        team (the one with the highest place; else the nearest of any team): its camera shifted by the same offset,
        its warm-up camera path, its angles, its height when z isn't given and, unless `rotation` is given, its turn.
        Returns the new item's number in `items`."""
        from .ndf import Value
        nd = self.ndf
        starts = [it for it in self.items if it.kind == "StartingPoint"]
        if nd is None or not starts:
            raise ScenarioError("this scenario has no starting point to copy a new one from")
        mine = [it for it in starts if it.values.get("AllianceNum") == team]
        if place is None:
            place = max((int(it.values.get("AlliancePriority") or 1) for it in mine), default=0) + 1
        if any(int(it.values.get("AlliancePriority") or 1) == place for it in mine):
            raise ScenarioError(f"team {team} already has a starting point at place {place}")
        model = (max(mine, key=lambda it: int(it.values.get("AlliancePriority") or 1)) if mine else
                 min(starts, key=lambda it: (it.position[0] - x) ** 2 + (it.position[1] - y) ** 2))
        lists = [o for o in nd.objects if nd.classes[o.cls] == "TGameDesignItemList"]
        if len(lists) != 1:
            raise ScenarioError("this scenario's design items aren't in one list")
        mo = nd.objects[model.obj]
        mprops = {nd.prop_name(pi): v for pi, v in mo.props}
        addon_at = local_ref(mprops["AddOn"])
        maddon = nd.objects[addon_at]
        dx, dy = x - model.position[0], y - model.position[1]
        props = []
        for pi, v in maddon.props:
            name, payload = nd.prop_name(pi), bytes(v.payload)
            if name == "AllianceNum":
                payload = struct.pack("<i", int(team))
            elif name == "AlliancePriority":
                payload = struct.pack("<i", int(place))
            elif name == "PositionCamera" and len(payload) >= 12:
                cx, cy, cz = struct.unpack_from("<3f", payload)
                payload = struct.pack("<3f", cx + dx, cy + dy, cz) + payload[12:]
            props.append((pi, Value(v.tc, payload)))
        if not any(nd.prop_name(pi) == "AlliancePriority" for pi, _v in props):
            pi = next((i for i, (n, c) in enumerate(nd.props) if n == "AlliancePriority" and c == maddon.cls), None)
            props.append((pi if pi is not None else nd.add_prop("AlliancePriority", maddon.cls),
                          Value(0x02, struct.pack("<i", int(place)))))
        addon = nd.add_object(maddon.cls, props)
        item_props = []
        for pi, v in mo.props:
            name = nd.prop_name(pi)
            if name == "Position":
                h = model.position[2] if z is None else z
                item_props.append((pi, Value(v.tc, struct.pack("<3f", x, y, h) + bytes(v.payload[12:]))))
            elif name == "Rotation" and rotation is not None:
                item_props.append((pi, Value(v.tc, struct.pack("<f", rotation))))
            elif name == "AddOn":
                item_props.append((pi, Value(0x09, struct.pack("<III", 0xBBBBBBBB, addon, maddon.cls))))
            else:
                item_props.append((pi, Value(v.tc, bytes(v.payload))))
        item = nd.add_object(mo.cls, item_props)
        holder = lists[0]
        ref = Value(0x09, struct.pack("<III", 0xBBBBBBBB, item, mo.cls)).encode()
        for k, (pi, v) in enumerate(holder.props):
            if v.tc == 0x11:
                count = struct.unpack_from("<I", v.payload)[0]
                holder.props[k] = (pi, Value(0x11, struct.pack("<I", count + 1) + v.payload[4:] + ref))
                break
        else:
            raise ScenarioError("this scenario's design item list is empty")
        self.items = _items(nd)
        self.changed = True
        return next(i for i, it in enumerate(self.items) if it.obj == item)

    def to_bytes(self) -> bytes:
        zones = struct.pack("<I", len(self.zones)) + b"".join(_zone_bytes(z) for z in self.zones)
        out = self.head + struct.pack("<3I", self.version, self.one, len(zones)) + zones
        if self.ndf is not None:
            if self.changed:  # the file pads the NDF with zeros to a multiple of 4 bytes (all 102 shipped files)
                nd = self.ndf.to_member(compress=bool(self.ndf.flags & 0x80))
                nd += bytes(-len(nd) % 4)
            else:
                nd = self.ndf_raw
            out += struct.pack("<I", len(nd)) + nd
        return with_checksum(out)


def checksum(data: bytes) -> bytes:
    """The 16 bytes at 10-25: the MD5 of bytes 0-9 and of byte 28 to the end (the rule in LittleGroove's
    RUSE-Mod-Manager, scenario.py; true of all 102 shipped files). The game checks it when it starts: a moved
    starting point without it crashed the game at launch (2026-09-30)."""
    return hashlib.md5(bytes(data[:10]) + bytes(data[28:])).digest()


def with_checksum(data: bytes) -> bytes:
    return bytes(data[:10]) + checksum(data) + bytes(data[26:])


def _items(nd: Ndf) -> list[Item]:
    names = [p for p, _ in nd.props]
    objs = [{names[pi]: v for pi, v in o.props} for o in nd.objects]
    out = []
    for o, props in zip(nd.objects, objs):
        if nd.classes[o.cls] != "TGameDesignItem" or "Position" not in props:
            continue
        pos = struct.unpack("<3f", props["Position"].payload[:12])
        rot = struct.unpack("<f", props["Rotation"].payload[:4])[0] if "Rotation" in props else 0.0
        kind, values = "", {}
        addon = local_ref(props["AddOn"]) if "AddOn" in props else None
        if addon is not None:
            kind = nd.classes[nd.objects[addon].cls].removeprefix("TGameDesignAddOn_")
            for name, v in objs[addon].items():
                values[name] = _plain(nd, v)
        out.append(Item(kind, pos, rot, values, nd.objects.index(o)))
    return out


def _plain(nd: Ndf, v):
    """A value as a number or a text when it's one of those; else its bytes in hex."""
    if v.tc in (0x07, 0x1C):
        return nd.strings[struct.unpack("<I", v.payload[:4])[0]]
    for tc, fmt in ((0x02, "<i"), (0x03, "<I"), (0x05, "<f"), (0x06, "<d"), (0x00, "<B")):
        if v.tc == tc:
            return struct.unpack(fmt, v.payload[:struct.calcsize(fmt)])[0]
    p = v.payload
    if len(p) >= 4 and struct.unpack_from("<I", p)[0] == len(p) - 4 and len(p) % 2 == 0:  # a label's own text
        return p[4:].decode("utf-16-le", "replace")
    return p.hex()


PACK = "DataMap_Win.dat"

# What each scenario is, from the game's own map list and menus (ZZ_GladPatchableWin.dat): an entry of the map list
# (TMapLoadInfo) loads a scenario through its cluster (ClusterLoads -> TNDFTransaction.BaseName =
# Patchable\Scenario\<map>\<scenario folder>\ClusterMap, whose ScenarioPath names the .scenario file), and the
# menus list the entry as a multiplayer map, a campaign chapter or a challenge (an Operation, in the game's menus).
KINDS = ("skirmish", "operation", "campaign", "demo", "test", "unused")
_MENU_KIND = {0: "skirmish", 1: "campaign", 2: "operation"}   # rusemod.terrain.MENU_CLASSES' order


def _text(nd: Ndf, v) -> str | None:
    return nd.strings[struct.unpack("<I", v.payload[:4])[0]] if v.tc in (0x07, 0x1C) else None


def kinds_of(glad_arc, map_pack: str) -> dict[str, list[dict]]:
    """What the game does with each scenario of a map: {scenario file name (lower case): [{"name": the map list's
    name for it, "kind": skirmish / operation / campaign / demo / test, "key": the menu text's key or None}]}, from
    an open ZZ_GladPatchableWin.dat. A scenario no entry loads isn't listed (it's unused)."""
    from .ndf import sub_values
    from .terrain import MAP_LIST, MENUS, menu_keys
    nd = Ndf(bytes(glad_arc.read(glad_arc.find(MAP_LIST[1]))))
    menu = glad_arc.entry(MENUS)
    menus = menu_keys(Ndf(bytes(glad_arc.read(menu)))) if menu is not None else {}
    out: dict[str, list[dict]] = {}
    clusters: dict[str, str | None] = {}
    for o in nd.objects:
        if nd.classes[o.cls] != "TMapLoadInfo":
            continue
        props = {nd.prop_name(pi): v for pi, v in o.props}
        name = _text(nd, props["Name"]) if "Name" in props else None
        root = next((_text(nd, props[k]) for k in ("RootDatapackName", "Path") if k in props), None)
        if not name or not root or root.lower() != map_pack.lower() or "ClusterLoads" not in props:
            continue
        base = None
        for v in sub_values(props["ClusterLoads"])[1::2]:
            cluster = local_ref(v)
            if cluster is None:
                continue
            cprops = {nd.prop_name(pi): x for pi, x in nd.objects[cluster].props}
            tr = local_ref(cprops["NdfTransaction"]) if "NdfTransaction" in cprops else None
            if tr is not None:
                tprops = {nd.prop_name(pi): x for pi, x in nd.objects[tr].props}
                base = _text(nd, tprops["BaseName"]) if "BaseName" in tprops else None
                if base:
                    break
        if not base:
            continue
        if base not in clusters:
            clusters[base] = _scenario_file(glad_arc, base)
        file = clusters[base]
        if not file:
            continue
        guid = bytes(props["GUID"].payload) if "GUID" in props else b""
        ranked = sorted(menus.get(guid, []), key=lambda rk: rk[0])
        low = name.lower()
        if ranked:
            kind, key = _MENU_KIND.get(ranked[0][0], "skirmish"), ranked[0][1]
        else:
            kind, key = ("demo" if "demo" in low else "test"), None
        out.setdefault(file, []).append({"name": name, "kind": kind, "key": key})
    return out


def _scenario_file(glad_arc, base: str) -> str | None:
    """The .scenario file (its name, lower case) a scenario cluster loads: its ClusterMap's ScenarioPath."""
    member = "genglad\\" + base.lower() + ".cpp.gladndfbin"
    e = glad_arc.entry(member)
    if e is None:
        return None
    try:
        nd = Ndf(bytes(glad_arc.read(e)))
    except (ValueError, struct.error):
        return None
    for s in nd.strings:
        if s.lower().endswith(".scenario"):
            return s.replace("/", "\\").rsplit("\\", 1)[-1].lower()
    return None


def folder_of(map_pack: str) -> str:
    """Where a map's scenarios live in DataMap_Win.dat: test/map/<pack>/ (the flat test maps: test/map/flat/<x>/),
    with the pack's backslashes."""
    name = map_pack.lower()
    if name.startswith("flat_"):
        name = "flat\\" + name[len("flat_"):]
    return "test\\map\\" + name + "\\"


def of_map(arc, map_pack: str) -> dict[str, "Scenario"]:
    """Every scenario of one map, by file name (leveldesign.scenario, leveldesign_challenge.scenario, ...), from an
    open DataMap_Win.dat. Files that can't be read are left out."""
    folder = folder_of(map_pack)
    out = {}
    for e in arc.entries:
        p = e.path.lower()
        if p.startswith(folder) and p.endswith(".scenario") and "\\" not in p[len(folder):]:
            try:
                out[e.path[len(folder):]] = Scenario.read(bytes(arc.read(e)))
            except (ScenarioError, ValueError, struct.error):
                continue
    return dict(sorted(out.items()))


def view(s: "Scenario") -> dict:
    """A scenario for the map view: zones as their triangles (x, y pairs, flat) and the design items that have a place
    on the map (starting points, spawns, circle and rectangle zones, labels, waypoints), in world units."""
    zones = []
    for z in s.zones:
        zones.append({"name": z.name, "number": z.number,
                      "points": [round(c, 1) for v in z.vertices for c in v[:2]],
                      "triangles": [i for t in z.triangles for i in t]})
    items = []
    for it in s.items:
        v = it.values
        entry = {"kind": it.kind, "x": round(it.position[0], 1), "y": round(it.position[1], 1),
                 "turn": round(it.rotation, 3), "name": str(v.get("Name", "") or "")}
        if it.kind == "StartingPoint":
            entry["alliance"] = v.get("AllianceNum")
            entry["place"] = v.get("AlliancePriority") or 1
        elif it.kind == "Spawn":
            entry["camp"] = v.get("Camp")
            entry["what"] = str(v.get("PythonClassName", "") or "").rsplit(".", 1)[-1]
        elif it.kind == "CircularZone":
            entry["radius"] = v.get("Radius")
        elif it.kind == "RectangleZone":
            entry["width"], entry["height"] = v.get("Width"), v.get("Height")
        elif it.kind in ("LabelVille", "LabelMontagne"):
            text = v.get("ChampTexte")
            entry["text"] = text if isinstance(text, str) and not all(c in "0123456789abcdef" for c in text) else entry["name"]
        items.append(entry)
    return {"zones": zones, "items": items}


# --- mods: design items moved (maps/<map pack>/scenario.toml, MOD_FORMAT §8) ---
KINDS_MOVABLE = ("StartingPoint", "Spawn", "LabelVille", "LabelMontagne", "CircularZone", "RectangleZone", "Name")


@dataclass
class Move:
    """One design item put somewhere else: in scenario `file` of the map, item number `item` (its place in the file's
    item list, as rusemod.scenario reads it), which must be a `kind` there, to x, y (world units), turned to
    `rotation` radians when given."""
    file: str
    item: int
    kind: str
    x: float
    y: float
    rotation: float | None = None


def parse_moves(items, where: str = "scenario.toml") -> list[Move]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: move {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        extra = sorted(set(m) - {"file", "item", "kind", "x", "y", "rotation"})
        if extra:
            raise ScenarioError(f"{at}: unknown key {extra[0]!r}")
        for k in ("file", "item", "kind", "x", "y"):
            if k not in m:
                raise ScenarioError(f"{at}: {k} is missing")
        f = str(m["file"])
        if not f.lower().endswith(".scenario") or "/" in f or "\\" in f:
            raise ScenarioError(f"{at}: file must be a scenario's name, like leveldesign.scenario")
        if m["kind"] not in KINDS_MOVABLE:
            raise ScenarioError(f"{at}: kind must be one of {', '.join(KINDS_MOVABLE)}")
        try:
            item = int(m["item"])
            x, y = float(m["x"]), float(m["y"])
            rot = float(m["rotation"]) if "rotation" in m else None
        except (TypeError, ValueError):
            raise ScenarioError(f"{at}: item is a whole number; x, y and rotation are numbers") from None
        if item < 0:
            raise ScenarioError(f"{at}: item can't be negative")
        out.append(Move(f, item, str(m["kind"]), x, y, rot))
    return out


def moves_toml(moves: list[Move], header: str = "") -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for m in moves:
        lines += ["[[move]]", f'file = "{m.file}"', f"item = {m.item}", f'kind = "{m.kind}"', f"x = {m.x!r}", f"y = {m.y!r}"]
        if m.rotation is not None:
            lines.append(f"rotation = {m.rotation!r}")
        lines.append("")
    return "\n".join(lines)


CLASS_PATH = "front.parametres.Classes."  # where the shipped spawns name most units and buildings


@dataclass
class Spawn:
    """A unit or building spawned when scenario `file` starts: `what` (a class name, Unit_M4_Sherman, or the full
    class path the shipped spawns use), for side `camp` (None: no side), at x, y, turned `rotation` radians."""
    file: str
    what: str
    x: float
    y: float
    camp: int | None = None
    rotation: float = 0.0

    @property
    def class_path(self) -> str:
        return self.what if "." in self.what else CLASS_PATH + self.what


def parse_spawns(items, where: str = "scenario.toml") -> list[Spawn]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: spawn {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        extra = sorted(set(m) - {"file", "what", "x", "y", "camp", "rotation"})
        if extra:
            raise ScenarioError(f"{at}: unknown key {extra[0]!r}")
        for k in ("file", "what", "x", "y"):
            if k not in m:
                raise ScenarioError(f"{at}: {k} is missing")
        f, what = str(m["file"]), str(m["what"])
        if not f.lower().endswith(".scenario") or "/" in f or "\\" in f:
            raise ScenarioError(f"{at}: file must be a scenario's name, like leveldesign.scenario")
        if not what or not all(c.isalnum() or c in "._" for c in what):
            raise ScenarioError(f"{at}: what must be a unit's or building's class name, like Unit_M4_Sherman")
        try:
            x, y = float(m["x"]), float(m["y"])
            camp = int(m["camp"]) if "camp" in m else None
            rot = float(m.get("rotation", 0.0))
        except (TypeError, ValueError):
            raise ScenarioError(f"{at}: x, y and rotation are numbers, camp a whole number") from None
        out.append(Spawn(f, what, x, y, camp, rot))
    return out


def spawns_toml(spawns: list[Spawn]) -> str:
    lines = []
    for s in spawns:
        lines += ["[[spawn]]", f'file = "{s.file}"', f'what = "{s.what}"', f"x = {s.x!r}", f"y = {s.y!r}"]
        if s.camp is not None:
            lines.append(f"camp = {s.camp}")
        if s.rotation:
            lines.append(f"rotation = {s.rotation!r}")
        lines.append("")
    return "\n".join(lines)


@dataclass
class Start:
    """A new starting point in scenario `file`: where a player of `team` (the game's AllianceNum) starts, at `place`
    in the team (AlliancePriority; None: the team's next), at x, y, turned `rotation` radians (None: as its
    teammate). More players on a map need one per player (rusemod.players, PLAN A10)."""
    file: str
    team: int
    x: float
    y: float
    place: int | None = None
    rotation: float | None = None
    z: float | None = None   # the ground's height there: the build fills it from the map (the shipped ones match it)


def parse_starts(items, where: str = "scenario.toml") -> list[Start]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: start {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        extra = sorted(set(m) - {"file", "team", "x", "y", "place", "rotation"})
        if extra:
            raise ScenarioError(f"{at}: unknown key {extra[0]!r}")
        for k in ("file", "team", "x", "y"):
            if k not in m:
                raise ScenarioError(f"{at}: {k} is missing")
        f = str(m["file"])
        if not f.lower().endswith(".scenario") or "/" in f or "\\" in f:
            raise ScenarioError(f"{at}: file must be a scenario's name, like leveldesign.scenario")
        try:
            if any(isinstance(m.get(k), bool) for k in ("team", "place")):
                raise TypeError
            team, x, y = int(m["team"]), float(m["x"]), float(m["y"])
            place = int(m["place"]) if "place" in m else None
            rot = float(m["rotation"]) if "rotation" in m else None
        except (TypeError, ValueError):
            raise ScenarioError(f"{at}: team and place are whole numbers; x, y and rotation are numbers") from None
        if not 1 <= team <= 8 or (place is not None and not 1 <= place <= 8):
            raise ScenarioError(f"{at}: team and place go from 1 to 8")
        out.append(Start(f, team, x, y, place, rot))
    return out


def starts_toml(starts: list[Start]) -> str:
    lines = []
    for s in starts:
        lines += ["[[start]]", f'file = "{s.file}"', f"team = {s.team}", f"x = {s.x!r}", f"y = {s.y!r}"]
        if s.place is not None:
            lines.append(f"place = {s.place}")
        if s.rotation is not None:
            lines.append(f"rotation = {s.rotation!r}")
        lines.append("")
    return "\n".join(lines)


def apply_moves(read, map_pack: str, moves: list) -> tuple[dict[str, bytes], list[str]]:
    """Apply a mod's scenario edits (in order: Move and Spawn) to a map's scenarios. `read(member)` gives a
    DataMap_Win.dat member's bytes, or None. Returns ({member: new bytes}, report lines). A move whose file or item
    isn't there, or whose item is another kind (the file isn't the one the mod was made for), raises ScenarioError;
    so does a spawn in a scenario that isn't there."""
    folder = folder_of(map_pack)
    files: dict[str, Scenario] = {}
    notes = []
    for m in moves:
        member = folder + m.file
        if member.lower() not in files:
            raw = read(member)
            if raw is None:
                raise ScenarioError(f"{map_pack}: it has no scenario {m.file}")
            files[member.lower()] = (member, Scenario.read(raw))
        member, s = files[member.lower()]
        if isinstance(m, Spawn):
            s.add_spawn(m.x, m.y, m.class_path, camp=m.camp, rotation=m.rotation)
            continue
        if isinstance(m, Start):
            s.add_start(m.x, m.y, m.team, m.place, m.rotation, m.z)
            continue
        if m.item >= len(s.items):
            raise ScenarioError(f"{map_pack}: {m.file} has {len(s.items)} design items, not {m.item + 1}")
        if s.items[m.item].kind != m.kind:
            raise ScenarioError(f"{map_pack}: {m.file} item {m.item} is a {s.items[m.item].kind or 'plain item'}, "
                                f"not a {m.kind}: the mod was made for another version of this map")
        s.move(m.item, m.x, m.y, rotation=m.rotation)  # an item without a rotation can't be turned: move() says so
    for member, s in files.values():
        mine = [m for m in moves if (folder + m.file).lower() == member.lower()]
        moved, spawned = sum(1 for m in mine if isinstance(m, Move)), sum(1 for m in mine if isinstance(m, Spawn))
        started = sum(1 for m in mine if isinstance(m, Start))
        notes.append(f"{map_pack}: {member.rsplit(chr(92), 1)[-1]}: " + ", ".join(
            p for p in (f"{moved} item(s) moved" if moved else "", f"{started} starting point(s) added" if started else "",
                        f"{spawned} spawn(s) added" if spawned else "") if p))
    return {member: s.to_bytes() for member, s in files.values()}, notes
