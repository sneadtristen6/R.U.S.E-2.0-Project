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

Writing: `Scenario.to_bytes()` gives the file back; unchanged, byte for byte (all 102). `move()` puts a design item
somewhere else (its Position, and its Rotation when it has one); the NDF is then written again by rusemod.ndf.
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
        return out


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


def apply_moves(read, map_pack: str, moves: list[Move]) -> tuple[dict[str, bytes], list[str]]:
    """Apply `moves` (in order) to a map's scenarios. `read(member)` gives a DataMap_Win.dat member's bytes, or None.
    Returns ({member: new bytes}, report lines). A move whose file or item isn't there, or whose item is another
    kind (the file isn't the one the mod was made for), raises ScenarioError."""
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
        if m.item >= len(s.items):
            raise ScenarioError(f"{map_pack}: {m.file} has {len(s.items)} design items, not {m.item + 1}")
        if s.items[m.item].kind != m.kind:
            raise ScenarioError(f"{map_pack}: {m.file} item {m.item} is a {s.items[m.item].kind or 'plain item'}, "
                                f"not a {m.kind}: the mod was made for another version of this map")
        s.move(m.item, m.x, m.y, rotation=m.rotation)  # an item without a rotation can't be turned: move() says so
    for member, s in files.values():
        notes.append(f"{map_pack}: {member.rsplit(chr(92), 1)[-1]}: "
                     f"{sum(1 for m in moves if (folder + m.file).lower() == member.lower())} item(s) moved")
    return {member: s.to_bytes() for member, s in files.values()}, notes
