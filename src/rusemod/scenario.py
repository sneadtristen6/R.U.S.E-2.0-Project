"""A map's scenario file (`test\\map\\<map>\\leveldesign*.scenario` in DataMap_Win.dat): its zones and its design
items (where players start, where reinforcements arrive, the names on the map). Read-only.

The layout was first worked out for Wargame by enohka's moddingSuite (and RugnirViking's RUSE fork of it); R.U.S.E.'s
files are the same except for the list at the end of each zone (Wargame writes it empty). Read from those notes and
checked on every scenario R.U.S.E. ships (102 files, every byte accounted for).

    "SCENARIO\\r\\n"            10 bytes
    16 bytes                    a checksum (not an MD5 of the rest)
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
"""
from __future__ import annotations

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
    name = r.take((n + 3) // 4 * 4)[:n].rstrip(b"\0").decode("utf-8", "replace")
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
    return Zone(number, name, anchor, vertices, triangles, parts, border_tri, border_vtx, outline)


@dataclass
class Scenario:
    version: int
    zones: list
    items: list

    @classmethod
    def read(cls, data: bytes) -> "Scenario":
        if data[:10] != MAGIC:
            raise ScenarioError("not a scenario file (no SCENARIO header)")
        r = _Reader(data)
        r.p = 28
        version = r.u32()
        r.u32()
        zone_data = r.take(r.u32())
        z = _Reader(zone_data)
        zones = [_zone(z) for _ in range(z.u32())]
        if z.p != len(zone_data):
            raise ScenarioError(f"{len(zone_data) - z.p} bytes after the last zone")
        items = []
        if r.p < len(data):
            items = _items(Ndf(r.take(r.u32())))
        return cls(version, zones, items)


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
        out.append(Item(kind, pos, rot, values))
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
