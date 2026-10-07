"""A map's scenarios: their design items (where players start, where reinforcements arrive, the names on the map),
read, moved and added, and written back with everything else unchanged (byte for byte on every shipped scenario).
Reading them follows enohka's moddingSuite (made for Wargame), RugnirViking's R.U.S.E. fork of it, and LittleGroove's
RUSE-Mod-Manager."""
from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import dataclass, field

from .ndf import Ndf, local_ref, sub_values

MAGIC = b"SCENARIO\r\n"
AREA = b"AREA"
NEUTRAL = -1   # the camp of neutral items (the shipped depots); the only camp a skirmish game spawns


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
    listed: bool = True  # on the scenario's design item list, which is what the game loads (Scenario.remove takes it
                         # off; every item of the 102 shipped scenarios is on it)
    turns: bool = False  # it has a Rotation (only such an item can be turned: Scenario.move)


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
        radians when given (only items that have a Rotation can turn). A starting point's opening camera
        (PositionCamera, when it has one: the game opens a skirmish looking from there) moves by the same offset, as
        add_start does; its warm-up camera flight (WarmupCamPath, a path in the map's camera file) can't move."""
        it = self.items[item]
        o = self.ndf.objects[it.obj]
        props = {self.ndf.prop_name(pi): v for pi, v in o.props}
        if rotation is not None and "Rotation" not in props:
            raise ScenarioError(f"design item {item} ({it.kind}) has no rotation to change")
        pos = props["Position"]
        dx, dy = x - it.position[0], y - it.position[1]
        z = it.position[2] if z is None else z
        pos.payload = struct.pack("<3f", x, y, z) + pos.payload[12:]
        it.position = struct.unpack("<3f", pos.payload[:12])
        if rotation is not None:
            props["Rotation"].payload = struct.pack("<f", rotation)
            it.rotation = struct.unpack("<f", props["Rotation"].payload)[0]
        addon = local_ref(props["AddOn"]) if "AddOn" in props else None
        if it.kind == "StartingPoint" and addon is not None:
            for _pi, v in self.ndf.objects[addon].props:
                if self.ndf.prop_name(_pi) == "PositionCamera" and len(v.payload) >= 12:
                    cx, cy, cz = struct.unpack_from("<3f", v.payload)
                    if cx or cy:  # (0, 0): no camera of its own, the game looks at the start itself
                        v.payload = struct.pack("<3f", cx + dx, cy + dy, cz) + bytes(v.payload[12:])
                        it.values["PositionCamera"] = _plain(self.ndf, v)
        self.changed = True

    def add_spawn(self, x: float, y: float, what: str, camp: int | None = NEUTRAL, rotation: float = 0.0,
                  z: float = 0.0, name: str | None = None, trucks: int | None = None) -> int:
        """A new design item that spawns `what` at x, y, z (world units; z the ground's height, as every shipped
        spawn has it) when the scenario starts, for side `camp` (None: neutral, -1, as the shipped depots: the game
        reads a spawn without a Camp as camp 0, which no game plays), turned `rotation` radians. `what` is the game's
        Python class path of a unit or building (front.parametres.Classes.Unit_M4_Sherman), as the shipped spawns
        name theirs. `trucks`: a depot's trucks (ChampInteger), written when given. Returns the new item's number in
        `items`."""
        camp = NEUTRAL if camp is None else camp
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
        if trucks is not None:  # the shipped depots' order: PythonClassName, ChampInteger, Camp
            addon_props.append((prop("ChampInteger", spawn_cls), Value(0x02, struct.pack("<i", int(trucks)))))
        addon_props.append((prop("Camp", spawn_cls), Value(0x02, struct.pack("<i", int(camp)))))
        if name:
            addon_props.insert(0, (prop("Name", spawn_cls), Value(0x07, struct.pack("<I", string(name)))))
        addon = nd.add_object(spawn_cls, addon_props)
        item = nd.add_object(item_cls, [
            (prop("Position", item_cls), Value(0x0B, struct.pack("<3f", x, y, z))),
            (prop("Rotation", item_cls), Value(0x05, struct.pack("<f", rotation))),
            (prop("AddOn", item_cls), Value(0x09, struct.pack("<III", 0xBBBBBBBB, addon, spawn_cls)))])
        return self._list_item(lists[0], item, item_cls)

    def _list_item(self, holder, item: int, item_cls: int) -> int:
        """Put new design item object `item` at the end of the scenario's design item list `holder` (what the game
        loads); returns its number in `items`."""
        from .ndf import Value
        nd = self.ndf
        ref = Value(0x09, struct.pack("<III", 0xBBBBBBBB, item, item_cls)).encode()
        for k, (pi, v) in enumerate(holder.props):
            if v.tc == 0x11:
                count = struct.unpack_from("<I", v.payload)[0]
                holder.props[k] = (pi, Value(0x11, struct.pack("<I", count + 1) + v.payload[4:] + ref))
                break
        else:  # an empty list is left out of the file (11 shipped scenarios): it gets its first item
            holder.props.append((self._prop("GameDesignItemList", holder.cls), Value(0x11, struct.pack("<I", 1) + ref)))
        self.items = _items(nd)
        self.changed = True
        return next(i for i, it in enumerate(self.items) if it.obj == item)

    def _prop(self, name: str, cls: int) -> int:
        """The PROP entry for property `name` of class `cls`, added if the file doesn't have it."""
        nd = self.ndf
        for i, (n, c) in enumerate(nd.props):
            if n == name and c == cls:
                return i
        return nd.add_prop(name, cls)

    def _string(self, text: str) -> int:
        """The STRG entry holding `text`, added if the file doesn't have it."""
        i = self.ndf.string_index(text)
        return self.ndf.add_string(text) if i is None else i

    def _text_value(self, tc: int, text: str):
        """`text` as a value of type `tc`: a name (0x07, a STRG entry, which other values may share: never changed
        in place) or a label's text (0x08, its own UTF-16 text)."""
        from .ndf import Value
        if tc == 0x07:
            return Value(0x07, struct.pack("<I", self._string(text)))
        if tc == 0x08:
            return Value(0x08, _wide(text))
        raise ScenarioError(f"a text of type {tc:#x} can't be written")

    def add_place(self, kind: str, x: float, y: float, z: float = 0.0, *, name: str = "", text: str = "",
                  rotation: float | None = None, radius: float | None = None, width: float | None = None,
                  height: float | None = None) -> int:
        """A new design item of PLACE_KINDS at x, y, z (world units; z the ground's height, as every shipped one has
        it): a town's or a hill's name on the map (LabelVille, LabelMontagne: `text`, the game text its words are
        under), a named point the mission scripts find by its `name` (Name), or a circle (`radius`) or rectangle
        (`width`, `height`) zone they watch, named `name`. Written as most of the shipped ones are (the 102 shipped
        scenarios, 2026-10-07): a label's text alone, a named point's name, a circle zone's name then radius, a
        rectangle zone's name, height then width; the item's turn only when `rotation` is given (a label has none).
        Returns the new item's number in `items`. Not yet seen in the game."""
        from .ndf import Value
        nd = self.ndf
        if nd is None:
            raise ScenarioError("this scenario has no design items to add to")
        if kind not in PLACE_KINDS:
            raise ScenarioError(f"a {kind} can't be added here (only {', '.join(PLACE_KINDS)})")
        lists = [o for o in nd.objects if nd.classes[o.cls] == "TGameDesignItemList"]
        if len(lists) != 1:
            raise ScenarioError("this scenario's design items aren't in one list")
        item_cls = nd.class_index("TGameDesignItem")
        addon_cls = nd.class_index("TGameDesignAddOn_" + kind)
        props = []
        if kind in LABEL_KINDS:
            props.append((self._prop("ChampTexte", addon_cls), self._text_value(0x08, text)))
        else:
            if name:
                props.append((self._prop("Name", addon_cls), self._text_value(0x07, name)))
            sizes = {"CircularZone": (("Radius", radius),), "RectangleZone": (("Height", height), ("Width", width))}
            for prop_name, v in sizes.get(kind, ()):
                props.append((self._prop(prop_name, addon_cls), Value(0x05, struct.pack("<f", float(v)))))
        addon = nd.add_object(addon_cls, props)
        item_props = [(self._prop("Position", item_cls), Value(0x0B, struct.pack("<3f", x, y, z)))]
        if rotation is not None and kind not in LABEL_KINDS:
            item_props.append((self._prop("Rotation", item_cls), Value(0x05, struct.pack("<f", rotation))))
        item_props.append((self._prop("AddOn", item_cls), Value(0x09, struct.pack("<III", 0xBBBBBBBB, addon, addon_cls))))
        return self._list_item(lists[0], nd.add_object(item_cls, item_props), item_cls)

    def remove(self, item: int) -> None:
        """Take design item number `item` off the scenario's design item list, which is what the game loads: the
        item is left out of the match. Its object stays in the file, named by nothing, so every other item keeps
        its number (LittleGroove's RUSE-Mod-Manager deletes a placement the same way). No shipped scenario has an
        item off its list; not yet seen in the game."""
        from .ndf import Value
        it = self.items[item]
        nd = self.ndf
        lists = [o for o in nd.objects if nd.classes[o.cls] == "TGameDesignItemList"]
        if len(lists) != 1:
            raise ScenarioError("this scenario's design items aren't in one list")
        holder = lists[0]
        for k, (pi, v) in enumerate(holder.props):
            if v.tc != 0x11:
                continue
            entries = sub_values(v)
            kept = [x for x in entries if local_ref(x) != it.obj]
            if len(kept) == len(entries):
                raise ScenarioError(f"design item {item} ({it.kind}) is off the scenario's list already")
            if kept:
                holder.props[k] = (pi, Value(0x11, struct.pack("<I", len(kept)) + b"".join(x.encode() for x in kept)))
            else:  # no item left: the list is left out, as 11 shipped scenarios have it
                del holder.props[k]
            break
        else:
            raise ScenarioError(f"design item {item} ({it.kind}) is off the scenario's list already")
        it.listed = False
        self.changed = True

    def set_value(self, item: int, field: str, value) -> None:
        """Change one of design item `item`'s own values (a field of CHANGES: a spawn's camp, a depot's trucks, a
        zone's radius, width or height, the name the mission scripts find an item by, a label's text), in the type
        the item has it in. A spawn without a Camp (the game reads it as camp 0) gets one, and a supply depot without
        trucks gets them, as add_spawn writes both; a spawn, named point or zone without a name gets one (first, as
        add_spawn writes it); any other value the item hasn't got can't be changed. Not yet seen in the game."""
        from .ndf import Value
        name = CHANGES[field]
        it = self.items[item]
        nd = self.ndf
        props = {nd.prop_name(pi): v for pi, v in nd.objects[it.obj].props}
        addon = local_ref(props["AddOn"]) if "AddOn" in props else None
        if addon is None:
            raise ScenarioError(f"design item {item} ({it.kind or 'plain item'}) has no values of its own to change")
        a = nd.objects[addon]
        if field in TEXT_CHANGES:
            at = next((k for k, (pi, _v) in enumerate(a.props) if nd.prop_name(pi) == name), None)
            if at is not None:
                pi, v = a.props[at]
                a.props[at] = (pi, self._text_value(v.tc, str(value)))
            elif field == "name" and it.kind in NAMED_KINDS:
                a.props.insert(0, (self._prop(name, a.cls), self._text_value(0x07, str(value))))
            else:
                raise ScenarioError(f"design item {item} ({it.kind or 'plain item'}) has no {name} to change")
            it.values[name] = _plain(nd, next(v for pi, v in a.props if nd.prop_name(pi) == name))
            self.changed = True
            return
        for k, (pi, v) in enumerate(a.props):
            if nd.prop_name(pi) != name:
                continue
            fmt = {0x02: "<i", 0x03: "<I", 0x05: "<f", 0x06: "<d"}.get(v.tc)
            if fmt is None:
                raise ScenarioError(f"design item {item} ({it.kind}) keeps its {name} in a way that can't be changed")
            number = float(value) if fmt in ("<f", "<d") else int(value)
            a.props[k] = (pi, Value(v.tc, struct.pack(fmt, number)))
            break
        else:
            depot = str(it.values.get("PythonClassName", "")).endswith(DEPOT.rsplit(".", 1)[-1])
            if not (it.kind == "Spawn" and (field == "camp" or (field == "trucks" and depot))):
                raise ScenarioError(f"design item {item} ({it.kind or 'plain item'}) has no {name} to change")
            pi = next((i for i, (n, c) in enumerate(nd.props) if n == name and c == a.cls), None)
            pi = nd.add_prop(name, a.cls) if pi is None else pi
            new = (pi, Value(0x02, struct.pack("<i", int(value))))
            camp_at = next((k for k, (q, _v) in enumerate(a.props) if nd.prop_name(q) == "Camp"), None)
            if field == "trucks" and camp_at is not None:  # the shipped depots' order: ..., ChampInteger, Camp
                a.props.insert(camp_at, new)
            else:
                a.props.append(new)
        it.values[name] = _plain(nd, next(v for pi, v in a.props if nd.prop_name(pi) == name))
        self.changed = True

    def places(self) -> dict[int, set[int]]:
        """Where players can start: {team (AllianceNum): {places (AlliancePriority)}}."""
        out: dict[int, set[int]] = {}
        for it in self.items:
            if it.kind == "StartingPoint" and isinstance(it.values.get("AllianceNum"), int):
                out.setdefault(it.values["AllianceNum"], set()).add(int(it.values.get("AlliancePriority") or 1))
        return out

    def team_sizes(self) -> dict[int, int]:
        """How many players each team can seat: {team (AllianceNum): its starting points}. The game seats a team's
        players on its starting points in order of place (lowest first), whatever the places are, so a team seats
        as many players as it has starting points (rusemod.players.seats)."""
        out: dict[int, int] = {}
        for it in self.items:
            if it.kind == "StartingPoint" and isinstance(it.values.get("AllianceNum"), int):
                out[it.values["AllianceNum"]] = out.get(it.values["AllianceNum"], 0) + 1
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
        self.last_model = (model.position[0], model.position[1])  # where the start it copies stands (its camera's)
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

    def set_warmup(self, item: int, name: str) -> bool:
        """Point starting point `item` at warm-up camera path `name` (its WarmupCamPath). False when it has none."""
        it = self.items[item]
        props = {self.ndf.prop_name(pi): v for pi, v in self.ndf.objects[it.obj].props}
        addon = local_ref(props["AddOn"]) if "AddOn" in props else None
        if addon is None:
            return False
        for pi, v in self.ndf.objects[addon].props:
            if self.ndf.prop_name(pi) == "WarmupCamPath" and v.tc in (0x07, 0x1C):
                at = self.ndf.string_index(name)
                v.payload = struct.pack("<I", self.ndf.add_string(name) if at is None else at) + bytes(v.payload[4:])
                it.values["WarmupCamPath"] = name
                self.changed = True
                return True
        return False

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
    listed = {local_ref(x) for o in nd.objects if nd.classes[o.cls] == "TGameDesignItemList"
              for _pi, v in o.props if v.tc == 0x11 for x in sub_values(v)}
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
        index = nd.objects.index(o)
        out.append(Item(kind, pos, rot, values, index, index in listed, "Rotation" in props))
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


def _wide(text: str) -> bytes:
    """A label's own text as the scenarios keep it (type 0x08): its length in bytes, then UTF-16, no end mark."""
    raw = text.encode("utf-16-le")
    return struct.pack("<I", len(raw)) + raw


_KEY_LETTERS = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz")


def text_key(text) -> str | None:
    """The game text a town's or a hill's label shows the words of: the key named by the label's text's first 10
    letters (the game's keys pack a name of up to 10 of these letters: rusemod.loc), in the game's ville_multi table
    (the 102 shipped scenarios, 2026-10-07: 291 of 291 town texts, 31 of 42 hill texts; the 11 others, "Hill 111"
    and so on, have a space, so they name no key). None when the text can't name one."""
    if not isinstance(text, str) or not text or not set(text[:10]) <= _KEY_LETTERS:
        return None
    return text[:10]


LABEL_TABLE = "ville_multi"  # the game's text table of the towns' and hills' names on its maps


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


def campath_member(map_pack: str, scenario_file: str) -> str:
    """Where a scenario's warm-up camera paths are: `test\\map\\<map>\\campath\\campaths_<scenario>.ndfbin` in
    DataMap_Win.dat (LittleGroove's RUSE-Mod-Manager map editor reads them there)."""
    stem = scenario_file.rsplit(".", 1)[0]
    return folder_of(map_pack) + "campath\\campaths_" + stem + ".ndfbin"


def campaths(raw: bytes) -> dict:
    """A campaths file's camera paths: {name: {"path": [[x, y, z], ...] (each keyframe's position, in order),
    "looks": [[dx, dy, dz], ...] (each keyframe's look direction)}}. A starting point's WarmupCamPath names its path;
    the last keyframe is where the camera rests when the match opens (LittleGroove: "the REAL start camera;
    PositionCamera is inert"). On D-Day the 3v3 starts' paths rest 2 to 3 km from their HQ, looking at it."""
    nd = Ndf(raw)

    def props(o):
        return {nd.prop_name(pi): v for pi, v in o.props}
    out = {}
    for o in nd.objects:
        if nd.classes[o.cls] != "TCameraPath":
            continue
        p = props(o)
        name = _text(nd, p["Name"]) if "Name" in p else None
        if not name:
            continue
        got = {}
        for key, field in (("PositionKeyVector", "path"), ("DirectionKeyVector", "looks")):
            pts = []
            for v in sub_values(p[key]) if key in p else []:
                r = local_ref(v)
                c = props(nd.objects[r]).get("Coord") if r is not None else None
                if c is not None and len(c.payload) >= 12:
                    pts.append([round(x, 3) for x in struct.unpack("<3f", c.payload[:12])])
            got[field] = pts
        out[name] = got
    return out


class CamPaths:
    """A scenario's warm-up camera paths (campath_member), to carry a starting point's opening camera when the start
    moves, or give a new start its own: TCameraPath objects (Name, PositionKeyVector, DirectionKeyVector), each key a
    TCameraPathKey with its Coord. The game finds a path by its name (a start's WarmupCamPath; the file has no index).
    Written back only when something changed: same content, the compressed bytes re-made (as the scenario files')."""

    def __init__(self, raw: bytes):
        self.raw, self.nd, self.changed = raw, Ndf(raw), False

    def _props(self, i: int) -> dict:
        return {self.nd.prop_name(pi): v for pi, v in self.nd.objects[i].props}

    def _path(self, name: str) -> int | None:
        for i, o in enumerate(self.nd.objects):
            if self.nd.classes[o.cls] == "TCameraPath" and _text(self.nd, self._props(i).get("Name")) == name:
                return i
        return None

    def keys(self, name: str) -> tuple[list[int], list[int]]:
        """(position keys, direction keys) of path `name`, as object numbers; ([], []) when there's no such path."""
        i = self._path(name)
        if i is None:
            return [], []
        p = self._props(i)
        refs = lambda k: [r for v in sub_values(p[k]) if (r := local_ref(v)) is not None] if k in p else []  # noqa: E731
        return refs("PositionKeyVector"), refs("DirectionKeyVector")

    def _coord(self, i: int):
        return self._props(i).get("Coord")

    def shift(self, name: str, dx: float, dy: float) -> int:
        """Move path `name`'s keyframes by (dx, dy) on the map; their look directions stay (the same view of the
        same, moved start). Returns how many keys moved."""
        pos, _dirs = self.keys(name)
        for k in pos:
            c = self._coord(k)
            x, y, z = struct.unpack_from("<3f", c.payload)
            c.payload = struct.pack("<3f", x + dx, y + dy, z) + bytes(c.payload[12:])
        self.changed = self.changed or bool(pos and (dx or dy))
        return len(pos)

    def turn(self, name: str, x: float, y: float, angle: float) -> int:
        """Turn path `name` `angle` radians about (x, y), the start it opens on: its keyframes go round on their ring
        and their look directions turn as much, so the camera frames the start as before, from another side
        (LittleGroove's camera ring). Returns how many keys turned."""
        pos, dirs = self.keys(name)
        if not angle:
            return 0
        ca, sa = math.cos(angle), math.sin(angle)
        for k in pos:
            c = self._coord(k)
            px, py, pz = struct.unpack_from("<3f", c.payload)
            rx, ry = px - x, py - y
            c.payload = struct.pack("<3f", x + rx * ca - ry * sa, y + rx * sa + ry * ca, pz) + bytes(c.payload[12:])
        for k in dirs:
            c = self._coord(k)
            dx, dy, dz = struct.unpack_from("<3f", c.payload)
            c.payload = struct.pack("<3f", dx * ca - dy * sa, dx * sa + dy * ca, dz) + bytes(c.payload[12:])
        self.changed = self.changed or bool(pos)
        return len(pos)

    def copy(self, name: str, new_name: str) -> bool:
        """A new path `new_name`, a copy of `name` with keyframes of its own (so moving one leaves the other)."""
        from .ndf import Value
        i = self._path(name)
        if i is None:
            return False
        nd, o = self.nd, self.nd.objects[i]

        def clone(k):
            src = nd.objects[k]
            return nd.add_object(src.cls, [(pi, Value(v.tc, bytes(v.payload))) for pi, v in src.props])
        pos, dirs = self.keys(name)
        props = []
        for pi, v in o.props:
            key = nd.prop_name(pi)
            if key in ("PositionKeyVector", "DirectionKeyVector"):
                made = [clone(k) for k in (pos if key[0] == "P" else dirs)]
                cls = nd.objects[made[0]].cls if made else 0
                payload = struct.pack("<I", len(made)) + b"".join(
                    Value(0x09, struct.pack("<III", 0xBBBBBBBB, m, cls)).encode() for m in made)
                props.append((pi, Value(v.tc, payload)))
            elif key == "Name":
                at = nd.string_index(new_name)
                props.append((pi, Value(v.tc, struct.pack("<I", nd.add_string(new_name) if at is None else at))))
            else:
                props.append((pi, Value(v.tc, bytes(v.payload))))
        nd.add_object(o.cls, props)
        self.changed = True
        return True

    def to_bytes(self) -> bytes:
        return self.nd.to_member(compress=bool(self.nd.flags & 0x80)) if self.changed else self.raw


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
                 "turn": round(it.rotation, 3), "turns": it.turns, "name": str(v.get("Name", "") or "")}
        if it.kind == "StartingPoint":
            entry["alliance"] = v.get("AllianceNum")
            entry["place"] = v.get("AlliancePriority") or 1
            entry["warmup"] = v.get("WarmupCamPath") if isinstance(v.get("WarmupCamPath"), str) else None
        elif it.kind == "Spawn":
            entry["camp"] = v.get("Camp")
            entry["what"] = str(v.get("PythonClassName", "") or "").rsplit(".", 1)[-1]
            if isinstance(v.get("ChampInteger"), int):  # a supply depot's trucks
                entry["trucks"] = v["ChampInteger"]
        elif it.kind == "CircularZone":
            entry["radius"] = v.get("Radius")
        elif it.kind == "RectangleZone":
            entry["width"], entry["height"] = v.get("Width"), v.get("Height")
        elif it.kind in ("LabelVille", "LabelMontagne"):
            text = v.get("ChampTexte")
            entry["text"] = text if isinstance(text, str) and not all(c in "0123456789abcdef" for c in text) else entry["name"]
            entry["key"] = text_key(text)  # the game text its words are under (None: it names none)
        if not it.listed:
            entry["gone"] = True  # off the design item list: the game leaves it out (Scenario.remove)
        items.append(entry)
    return {"zones": zones, "items": items}


# --- mods: design items moved (maps/<map pack>/scenario.toml, MOD_FORMAT §8) ---
KINDS_MOVABLE = ("StartingPoint", "Spawn", "LabelVille", "LabelMontagne", "CircularZone", "RectangleZone", "Name")


@dataclass
class Move:
    """One design item put somewhere else: in scenario `file` of the map, item number `item` (its place in the file's
    item list, as rusemod.scenario reads it), which must be a `kind` there, to x, y (world units), turned to
    `rotation` radians when given. A starting point's `camera`: its warm-up camera path turned that many radians about
    it (LittleGroove's camera ring), so the match opens looking at it from another side."""
    file: str
    item: int
    kind: str
    x: float
    y: float
    rotation: float | None = None
    z: float | None = None   # the ground's height there: the build fills it for starting points and spawns
    camera: float | None = None


def parse_moves(items, where: str = "scenario.toml") -> list[Move]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: move {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        extra = sorted(set(m) - {"file", "item", "kind", "x", "y", "rotation", "camera"})
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
            cam = _camera_turn(m)
        except (TypeError, ValueError):
            raise ScenarioError(f"{at}: item is a whole number; x, y, rotation and camera are numbers") from None
        if item < 0:
            raise ScenarioError(f"{at}: item can't be negative")
        if cam is not None and m["kind"] != "StartingPoint":
            raise ScenarioError(f"{at}: only a starting point has a camera to turn")
        out.append(Move(f, item, str(m["kind"]), x, y, rot, camera=cam))
    return out


def _camera_turn(m: dict) -> float | None:
    """A table's `camera` turn (radians), None when it has none; ValueError when it isn't a finite number."""
    if "camera" not in m:
        return None
    if isinstance(m["camera"], bool):
        raise TypeError
    turn = float(m["camera"])
    if not math.isfinite(turn):
        raise ValueError
    return turn


KINDS_REMOVABLE = ("Spawn", "LabelVille", "LabelMontagne", "CircularZone", "RectangleZone", "Name")  # not a start:
# every player needs one (move it instead)


@dataclass
class Remove:
    """One of the map's own design items taken out: in scenario `file`, item number `item`, which must be a `kind`
    there (Scenario.remove: off the design item list, so the game leaves it out)."""
    file: str
    item: int
    kind: str


def parse_removes(items, where: str = "scenario.toml") -> list[Remove]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: remove {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        extra = sorted(set(m) - {"file", "item", "kind"})
        if extra:
            raise ScenarioError(f"{at}: unknown key {extra[0]!r}")
        for k in ("file", "item", "kind"):
            if k not in m:
                raise ScenarioError(f"{at}: {k} is missing")
        f = str(m["file"])
        if not f.lower().endswith(".scenario") or "/" in f or "\\" in f:
            raise ScenarioError(f"{at}: file must be a scenario's name, like leveldesign.scenario")
        if m["kind"] == "StartingPoint":
            # rule: seats-per-team
            raise ScenarioError(f"{at}: a starting point can't be removed, every player needs one: move it instead")
        if m["kind"] not in KINDS_REMOVABLE:
            raise ScenarioError(f"{at}: kind must be one of {', '.join(KINDS_REMOVABLE)}")
        if isinstance(m["item"], bool) or not isinstance(m["item"], int) or m["item"] < 0:
            raise ScenarioError(f"{at}: item is a whole number, 0 or more")
        out.append(Remove(f, m["item"], str(m["kind"])))
    return out


def scenario_toml(moves: list, starts: list, spawns: list, removes: list, header: str = "", sectors=None) -> str:
    """A scenario.toml holding all four kinds of edit and the sectors' setting (none is ever left out on a rewrite)."""
    from .sectors import sectors_toml
    table = sectors_toml(sectors)
    return (moves_toml(moves, header) + "\n" + removes_toml(removes) + "\n" + starts_toml(starts) + "\n"
            + spawns_toml(spawns) + ("\n" + table if table else ""))


def removes_toml(removes: list[Remove]) -> str:
    lines = []
    for m in removes:
        lines += ["[[remove]]", f'file = "{m.file}"', f"item = {m.item}", f'kind = "{m.kind}"', ""]
    return "\n".join(lines)


# --- mods: the map's own design items with some of their values changed (maps/<map pack>/items.toml, MOD_FORMAT §8;
# LittleGroove's map editor's Details panel). Each value is written in the type the item already has it in (the 102
# shipped scenarios: Camp and ChampInteger whole numbers, Radius, Width and Height float32s); a spawn's Camp, and a
# supply depot's trucks, are added when the item hasn't got one, as add_spawn writes them ---
CHANGES = {"camp": "Camp", "trucks": "ChampInteger", "radius": "Radius", "width": "Width", "height": "Height",
           "name": "Name", "text": "ChampTexte"}
KIND_CHANGES = {"Spawn": ("camp", "trucks", "name"), "CircularZone": ("radius", "name"),
                "RectangleZone": ("width", "height", "name"), "Name": ("name",), "LabelVille": ("text",),
                "LabelMontagne": ("text",)}
TEXT_CHANGES = ("name", "text")   # the fields that are texts: the name scripts find an item by, a label's text
NAMED_KINDS = ("Spawn", "Name", "CircularZone", "RectangleZone")  # the kinds the shipped scenarios name (and so may
# get a name: set_value)
TEXT_MOST = 200   # the longest name or label text taken (the shipped ones: 2 to 40 letters)


def _check_text(v, at: str, field: str) -> str:
    """A name or a label's text from a mod's file: one line of text the scenario file can hold."""
    if not isinstance(v, str):
        raise ScenarioError(f"{at}: {field} is a text, in quotes")
    if not v.strip() or len(v) > TEXT_MOST or any(c in v for c in "\r\n\t\0"):
        # not a game rule: one line of 1 to TEXT_MOST letters, as the Studio writes it
        raise ScenarioError(f"{at}: {field} is one line of 1 to {TEXT_MOST} letters")
    if field == "name":
        try:
            v.encode("latin-1")
        except UnicodeEncodeError:
            # not a game rule: a scenario file keeps names in one byte per letter (its STRG table)
            raise ScenarioError(f"{at}: name has a letter a scenario file can't keep (use letters, digits and _)") \
                from None
    return v


@dataclass
class Change:
    """One of the map's own design items with some of its values changed: in scenario `file`, item number `item`
    (as for [[move]]), which must be a `kind` there; `values` {field: value}, the fields of CHANGES its kind has
    (KIND_CHANGES): a spawn's side (`camp`) and a supply depot's `trucks`, a circle zone's `radius`, a rectangle zone's
    `width` and `height` (world units)."""
    file: str
    item: int
    kind: str
    values: dict


def parse_changes(items, where: str = "items.toml") -> list[Change]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: set {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        for k in ("file", "item", "kind"):
            if k not in m:
                raise ScenarioError(f"{at}: {k} is missing")
        kind = m["kind"]
        if kind not in KIND_CHANGES:
            raise ScenarioError(f"{at}: kind must be one of {', '.join(KIND_CHANGES)}")
        extra = sorted(set(m) - {"file", "item", "kind"} - set(KIND_CHANGES[kind]))
        if extra:
            raise ScenarioError(f"{at}: unknown key {extra[0]!r} (a {kind} has {', '.join(KIND_CHANGES[kind])})")
        f = str(m["file"])
        if not f.lower().endswith(".scenario") or "/" in f or "\\" in f:
            raise ScenarioError(f"{at}: file must be a scenario's name, like leveldesign.scenario")
        if isinstance(m["item"], bool) or not isinstance(m["item"], int) or m["item"] < 0:
            raise ScenarioError(f"{at}: item is a whole number, 0 or more")
        values = {}
        for k in KIND_CHANGES[kind]:
            if k not in m:
                continue
            v = m[k]
            if k in TEXT_CHANGES:
                values[k] = _check_text(v, at, k)
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ScenarioError(f"{at}: {k} is a number")
            if k == "camp":  # as a spawn's camp is checked (parse_spawns)
                if not isinstance(v, int) or not (v == NEUTRAL or 0 <= v <= 16):
                    raise ScenarioError(f"{at}: camp is -1 (neutral) or a scenario camp from 0 up")
            elif k == "trucks":  # as a new depot's trucks are checked (parse_spawns)
                if not isinstance(v, int) or not 0 <= v <= 1000:
                    raise ScenarioError(f"{at}: trucks goes from 0 to 1000 (the shipped depots have 15 to 72)")
            elif not (math.isfinite(v) and v > 0):
                raise ScenarioError(f"{at}: {k} is a size, more than 0")
            values[k] = v
        if not values:
            raise ScenarioError(f"{at}: it changes nothing (a {kind} has {', '.join(KIND_CHANGES[kind])})")
        out.append(Change(f, m["item"], str(kind), values))
    return out


def changes_toml(changes: list[Change], header: str = "") -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for c in changes:
        lines += ["[[set]]", f'file = "{c.file}"', f"item = {c.item}", f'kind = "{c.kind}"']
        lines += [f"{k} = {_toml_value(c.values[k])}" for k in KIND_CHANGES[c.kind] if k in c.values]
        lines.append("")
    return "\n".join(lines)


def _toml_value(v) -> str:
    """A number or a text as TOML writes it (a text in double quotes, its quotes and backslashes escaped)."""
    return json.dumps(v, ensure_ascii=False) if isinstance(v, str) else repr(v)


# --- mods: new labels, named points and zones (maps/<map pack>/places.toml, MOD_FORMAT §8; LittleGroove's map editor's
# + Placement for city and mountain labels, named points and circle and rectangle zones). A file of its own, as
# items.toml: none of the many rewrites of scenario.toml can drop them. Added at the end of a scenario's items, like
# spawns, so the shipped items keep their numbers ---
PLACE_KINDS = ("LabelVille", "LabelMontagne", "Name", "CircularZone", "RectangleZone")
LABEL_KINDS = ("LabelVille", "LabelMontagne")
PLACE_KEYS = {"LabelVille": ("text",), "LabelMontagne": ("text",), "Name": ("name", "rotation"),
              "CircularZone": ("name", "radius", "rotation"), "RectangleZone": ("name", "width", "height", "rotation")}


@dataclass
class Place:
    """A new design item of scenario `file` that isn't a unit (PLACE_KINDS), at x, y: a town's or a hill's name on
    the map (`text`: the game text its words are under, a key of LABEL_TABLE), a named point the mission scripts find
    by its `name`, or a circle (`radius`) or rectangle (`width`, `height`, world units) zone they watch, named `name`;
    a named point or a zone turned `rotation` radians when given (Scenario.add_place)."""
    file: str
    kind: str
    x: float
    y: float
    name: str = ""
    text: str = ""
    rotation: float | None = None
    radius: float | None = None
    width: float | None = None
    height: float | None = None
    z: float | None = None   # the ground's height there: the build fills it from the map (the shipped ones match it)


def parse_places(items, where: str = "places.toml") -> list[Place]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: place {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        for k in ("file", "kind", "x", "y"):
            if k not in m:
                raise ScenarioError(f"{at}: {k} is missing")
        kind = m["kind"]
        if kind not in PLACE_KINDS:
            raise ScenarioError(f"{at}: kind must be one of {', '.join(PLACE_KINDS)}")
        extra = sorted(set(m) - {"file", "kind", "x", "y"} - set(PLACE_KEYS[kind]))
        if extra:
            raise ScenarioError(f"{at}: unknown key {extra[0]!r} (a {kind} has {', '.join(PLACE_KEYS[kind])})")
        f = str(m["file"])
        if not f.lower().endswith(".scenario") or "/" in f or "\\" in f:
            raise ScenarioError(f"{at}: file must be a scenario's name, like leveldesign.scenario")
        numbers = {}
        for k in ("x", "y", "rotation", "radius", "width", "height"):
            if k not in m:
                continue
            v = m[k]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ScenarioError(f"{at}: {k} is a number")
            if k in ("radius", "width", "height") and not v > 0:
                raise ScenarioError(f"{at}: {k} is a size, more than 0")
            numbers[k] = float(v)
        for k in {"CircularZone": ("radius",), "RectangleZone": ("width", "height")}.get(kind, ()):
            if k not in numbers:
                raise ScenarioError(f"{at}: a {kind} needs its {k}")
        if kind in LABEL_KINDS and "text" not in m:
            # not a game rule: what the file must say to write a label as the game's are (its text alone)
            raise ScenarioError(f"{at}: a {kind} needs its text (the game text its words are under)")
        if kind == "Name" and "name" not in m:
            raise ScenarioError(f"{at}: a named point needs its name (what the mission scripts find it by)")
        texts = {k: _check_text(m[k], at, k) for k in ("name", "text") if k in m}
        out.append(Place(f, str(kind), numbers["x"], numbers["y"], texts.get("name", ""), texts.get("text", ""),
                         numbers.get("rotation"), numbers.get("radius"), numbers.get("width"), numbers.get("height")))
    return out


def places_toml(places: list[Place], header: str = "") -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for p in places:
        lines += ["[[place]]", f'file = "{p.file}"', f'kind = "{p.kind}"', f"x = {p.x!r}", f"y = {p.y!r}"]
        for k in PLACE_KEYS[p.kind]:
            v = getattr(p, k)
            if v is not None and v != "":
                lines.append(f"{k} = {_toml_value(v)}")
        lines.append("")
    return "\n".join(lines)


def moves_toml(moves: list[Move], header: str = "") -> str:
    lines = [f"# {line}" for line in header.splitlines()] + ([""] if header else [])
    for m in moves:
        lines += ["[[move]]", f'file = "{m.file}"', f"item = {m.item}", f'kind = "{m.kind}"', f"x = {m.x!r}", f"y = {m.y!r}"]
        if m.rotation is not None:
            lines.append(f"rotation = {m.rotation!r}")
        if m.camera is not None:
            lines.append(f"camera = {m.camera!r}")
        lines.append("")
    return "\n".join(lines)


CLASS_PATH = "front.parametres.Classes."  # where the shipped spawns name most units and buildings
DEPOT = "front.batiment_depot.DalleBatimentDepot"  # a supply depot's slab: the shipped spawns name it this way (1,625)
SHIPPED_PATHS = {"DalleBatimentDepot": DEPOT}       # class names the game finds elsewhere than CLASS_PATH
DEPOT_TRUCKS = 25   # the trucks a depot slab starts with (ChampInteger): what most shipped depots have (800 of them)


@dataclass
class Spawn:
    """A unit or building spawned when scenario `file` starts: `what` (a class name, Unit_M4_Sherman, or the full
    class path the shipped spawns use), for side `camp` (None: neutral, -1), at x, y, turned `rotation` radians.
    `trucks`: a depot's trucks (None: DEPOT_TRUCKS)."""
    file: str
    what: str
    x: float
    y: float
    camp: int | None = None
    rotation: float = 0.0
    trucks: int | None = None
    z: float | None = None   # the ground's height there: the build fills it from the map (the shipped ones match it)

    @property
    def class_path(self) -> str:
        return self.what if "." in self.what else SHIPPED_PATHS.get(self.what, CLASS_PATH + self.what)


def spawn_class_problems(map_pack: str, spawns: list[Spawn], registered, shipped_paths) -> list[str]:
    """Why the game couldn't find a spawn's class when the map loads (which makes loading it fail): one message per
    spawn whose class path ends in parametres.Classes.X when X isn't a class of the game's Python unit list
    (`registered`: its class names, the mods' new ones included; None when the list can't be read, and then these
    aren't checked), or whose other class path no shipped spawn uses (`shipped_paths()`: every shipped spawn's)."""
    out, shipped = [], None
    for s in spawns:
        path = s.class_path
        module, _dot, name = path.rpartition(".")
        at = f"{map_pack}: scenario.toml: the spawn of {s.what} in {s.file}"
        if module == "parametres.Classes" or module.endswith(".parametres.Classes"):
            if registered is not None and name not in registered:
                out.append(f"{at}: the game's unit list has no class {name}, so the map would fail to load. Use the "
                           f"class name (ClassNameForDebug) of a unit the list has; a new unit gets one when it's a "
                           f"copy of a listed unit")
            continue
        if path in SHIPPED_PATHS.values():  # (the depot slab's: 1,625 shipped spawns use it)
            continue
        if shipped is None:
            shipped = shipped_paths()
        if path not in shipped:
            out.append(f"{at}: {path} isn't a class path any shipped spawn uses, so the game may not find it and "
                       f"the map would fail to load. Use the unit's class name alone (what = \"Unit_...\"), or a path "
                       f"a shipped scenario uses")
    return out


def shipped_class_paths(arc) -> set[str]:
    """Every class path the shipped spawns use, from an open DataMap_Win.dat (all its scenarios)."""
    out = set()
    for e in arc.entries:
        if e.path.lower().endswith(".scenario"):
            try:
                s = Scenario.read(bytes(arc.read(e)))
            except (ScenarioError, ValueError, struct.error):
                continue
            out |= {str(it.values.get("PythonClassName")) for it in s.items if it.kind == "Spawn"}
    return out


def parse_spawns(items, where: str = "scenario.toml") -> list[Spawn]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: spawn {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        extra = sorted(set(m) - {"file", "what", "x", "y", "camp", "rotation", "trucks"})
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
            if any(isinstance(m.get(k), bool) for k in ("camp", "trucks")):
                raise TypeError
            x, y = float(m["x"]), float(m["y"])
            camp = int(m["camp"]) if "camp" in m else None
            rot = float(m.get("rotation", 0.0))
            trucks = int(m["trucks"]) if "trucks" in m else None
        except (TypeError, ValueError):
            raise ScenarioError(f"{at}: x, y and rotation are numbers; camp and trucks whole numbers") from None
        if not all(math.isfinite(v) for v in (x, y, rot)):
            raise ScenarioError(f"{at}: x, y and rotation must be finite numbers")
        if camp is not None and not (camp == NEUTRAL or 0 <= camp <= 16):
            raise ScenarioError(f"{at}: camp is -1 (neutral) or a scenario camp from 0 up")
        if trucks is not None:
            if Spawn(f, what, x, y).class_path != DEPOT:
                raise ScenarioError(f"{at}: trucks is only for a supply depot (what = \"DalleBatimentDepot\")")
            if not 0 <= trucks <= 1000:
                raise ScenarioError(f"{at}: trucks goes from 0 to 1000 (the shipped depots have 15 to 72)")
        out.append(Spawn(f, what, x, y, camp, rot, trucks))
    return out


def spawns_toml(spawns: list[Spawn]) -> str:
    lines = []
    for s in spawns:
        lines += ["[[spawn]]", f'file = "{s.file}"', f'what = "{s.what}"', f"x = {s.x!r}", f"y = {s.y!r}"]
        if s.camp is not None:
            lines.append(f"camp = {s.camp}")
        if s.rotation:
            lines.append(f"rotation = {s.rotation!r}")
        if s.trucks is not None:
            lines.append(f"trucks = {s.trucks}")
        lines.append("")
    return "\n".join(lines)


@dataclass
class Start:
    """A new starting point in scenario `file`: where a player of `team` (the game's AllianceNum) starts, at `place`
    in the team (AlliancePriority; None: the team's next), at x, y, turned `rotation` radians (None: as its
    teammate), its warm-up camera turned `camera` radians about it (as Move's). More players on a map need one per
    player (rusemod.players, PLAN A10)."""
    file: str
    team: int
    x: float
    y: float
    place: int | None = None
    rotation: float | None = None
    z: float | None = None   # the ground's height there: the build fills it from the map (the shipped ones match it)
    camera: float | None = None


def parse_starts(items, where: str = "scenario.toml") -> list[Start]:
    out = []
    for n, m in enumerate(items or [], start=1):
        at = f"{where}: start {n}"
        if not isinstance(m, dict):
            raise ScenarioError(f"{at} isn't a table")
        extra = sorted(set(m) - {"file", "team", "x", "y", "place", "rotation", "camera"})
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
            cam = _camera_turn(m)
        except (TypeError, ValueError):
            raise ScenarioError(f"{at}: team and place are whole numbers; x, y, rotation and camera are numbers") from None
        if not 1 <= team <= 8 or (place is not None and not 1 <= place <= 8):
            raise ScenarioError(f"{at}: team and place go from 1 to 8")
        out.append(Start(f, team, x, y, place, rot, camera=cam))
    return out


def starts_toml(starts: list[Start]) -> str:
    lines = []
    for s in starts:
        lines += ["[[start]]", f'file = "{s.file}"', f"team = {s.team}", f"x = {s.x!r}", f"y = {s.y!r}"]
        if s.place is not None:
            lines.append(f"place = {s.place}")
        if s.rotation is not None:
            lines.append(f"rotation = {s.rotation!r}")
        if s.camera is not None:
            lines.append(f"camera = {s.camera!r}")
        lines.append("")
    return "\n".join(lines)


ROAD_NEAR = 30000.0   # map units: 95% of the shipped starting points are this close to a road (the furthest 1,440,000)


def start_ground_problems(read, map_pack: str, moves: list) -> tuple[list[str], list[str]]:
    """(errors, warnings) for the mod's new and moved starting points on the map's movement and road network as the
    build leaves them (`read(member)`: DataMap_Win.dat's files after every map edit). A start where no ground unit can
    stand (the infantry's graph, buffer 1: water, a cliff, a block for every unit, off the map) is an error: the game
    builds the HQ wherever it finds room. Woods are fine (the owner, 2026-10-02: an HQ in a wood works, and supply
    trucks drive through woods; only tanks and other vehicles with flags 11/21/55 are kept out, the vehicles' graph).
    One far from any road is a warning: the shipped starts are near one (a pattern, not a rule of the game).
    A map whose mapinfo.win can't be read isn't checked."""
    from .cover import member
    from .nav import Graph
    from .roadnet import RoadNet
    starts = [m for m in moves if isinstance(m, Start) or (isinstance(m, Move) and m.kind == "StartingPoint")]
    win = read(member(map_pack)) if starts else None
    if win is None:
        return [], []
    try:
        from ruse_mod_engine import sdb
        bufs = sdb.split_mapinfo(win)[1]
        infantry = Graph.read(bufs[1])
    except (ValueError, IndexError, TypeError, struct.error):
        return [], []
    try:
        net = RoadNet.read(bufs[0])
        roads = [(net.points[a][:2], net.points[b][:2]) for a, b, _cost in net.links]
    except (ValueError, IndexError, struct.error):
        roads = []
    errors, warnings = [], []
    for m in starts:
        what = (f"the new starting point for team {m.team}" if isinstance(m, Start) else
                f"the starting point moved (item {m.item})")
        at = f"{map_pack}: scenario.toml: {what} at ({m.x:.0f}, {m.y:.0f}) in {m.file}"
        if not infantry.walkable(m.x, m.y):
            errors.append(f"{at} is where no ground unit can stand (water, a cliff, a block for every unit, or off the "
                          f"map): the game would build that player's HQ wherever it finds room, possibly far away. Put "
                          f"it on land (a wood is fine)")
            continue
        if roads:
            far = min(_to_segment(m.x, m.y, a, b) for a, b in roads)
            if far > ROAD_NEAR:
                warnings.append(f"{at} is {far:,.0f} map units from the nearest road; 95% of the game's own starting "
                                f"points are within about {ROAD_NEAR:,.0f} of one. That's how its maps are made, not a "
                                f"rule: leave it if you mean it, or move it nearer a road")
    return errors, warnings


def _to_segment(x: float, y: float, a, b) -> float:
    (ax, ay), (bx, by) = a, b
    vx, vy = bx - ax, by - ay
    n = vx * vx + vy * vy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / n))
    return math.hypot(x - ax - t * vx, y - ay - t * vy)


def apply_moves(read, map_pack: str, moves: list, skirmish=(), warn=None,
                mission=None) -> tuple[dict[str, bytes], list[str]]:
    """Apply a mod's scenario edits (in order: Move, Remove, Start, Spawn, the places.toml Places, then the items.toml
    Changes) to a map's
    scenarios. `read(member)` gives a DataMap_Win.dat member's bytes, or None. `skirmish`: the map's scenarios (file
    names, lower case) that its
    skirmish and online entries load (rusemod.players.skirmish_files). Returns ({member: new bytes}, report lines).
    A move or a remove whose file or item isn't there, or whose item is another kind (the file isn't the one the mod
    was made for), raises ScenarioError; so does a spawn in a scenario that isn't there, and a spawn for a player's camp in a
    skirmish scenario (a skirmish game spawns only neutral items: the game leaves the others out without a word).
    `mission(file)` gives a scenario's camps from its mission script (rusemod.missions.Camp list; [] for none), and
    `warn(message)` is told of a spawn for a camp the mission doesn't list (the game's launch code gives a spawn to its
    camp only when the camp list has that number); for a scenario with no script to read, of a spawn for a camp its own
    spawns never use."""
    folder = folder_of(map_pack)
    files: dict[str, Scenario] = {}
    camps: dict[str, set] = {}   # member (lower case) -> the camps its shipped spawns use (no Camp reads as 0)
    cams: dict[str, tuple] = {}  # scenario file (lower case) -> (its campaths member, CamPaths), read when needed
    notes, later = [], []

    def cam_of(file: str):
        if file.lower() not in cams:
            member = campath_member(map_pack, file)
            raw = read(member)
            cams[file.lower()] = (member, CamPaths(raw) if raw is not None else None)
        return cams[file.lower()][1]

    def own_path(cam, s, item, why):
        """Give starting point `item` a warm-up camera path of its own (a copy of the one it names), when another
        start uses the same one or it's a new start: the name of the path it now has, or None."""
        name = s.items[item].values.get("WarmupCamPath")
        if not (cam and isinstance(name, str) and name):
            return None
        users = sum(1 for it in s.items if it.kind == "StartingPoint" and it.values.get("WarmupCamPath") == name)
        if users <= 1 and why != "new":
            return name
        k = 1
        while cam._path(f"{name}_mod{k}") is not None:
            k += 1
        if not cam.copy(name, f"{name}_mod{k}"):
            return None
        s.set_warmup(item, f"{name}_mod{k}")
        return f"{name}_mod{k}"

    for m in moves:
        member = folder + m.file
        if member.lower() not in files:
            raw = read(member)
            if raw is None:
                raise ScenarioError(f"{map_pack}: it has no scenario {m.file}")
            files[member.lower()] = (member, Scenario.read(raw))
            camps[member.lower()] = {it.values.get("Camp", 0) for it in files[member.lower()][1].items
                                     if it.kind == "Spawn"}
        member, s = files[member.lower()]
        if isinstance(m, Spawn):
            camp = NEUTRAL if m.camp is None else m.camp
            at = f"{map_pack}: scenario.toml: the spawn of {m.what} at ({m.x:.0f}, {m.y:.0f}) in {m.file}"
            if m.file.lower() in skirmish and camp != NEUTRAL:
                # rule: skirmish-neutral-spawns
                raise ScenarioError(f"{at} is for camp {camp}, but {m.file} is a skirmish map's scenario, and a "
                                    f"skirmish game spawns only neutral items: the game would leave it out without a "
                                    f"word. Set camp = -1 (or leave camp out), or spawn it in an Operation's scenario")
            listed = mission(m.file) if mission is not None and camp != NEUTRAL else []
            if listed and camp not in {c.key for c in listed} and warn is not None:
                its = ", ".join(f"{c.key} ({'the player' if c.player else 'the computer'}"
                                f"{', ' + c.nation if c.nation else ''})" for c in sorted(listed, key=lambda c: c.key))
                warn(f"{at} is for camp {camp}, which isn't one of the camps its mission lists ({its}); the game "
                     f"gives a spawn only to a camp its mission lists, so it may never appear. Use one of those camps "
                     f"(not tested in the game)")
            elif not listed and camp != NEUTRAL and camp not in camps[member.lower()] and warn is not None:
                used = ", ".join(str(c) for c in sorted(camps[member.lower()])) or "none"
                warn(f"{at} is for camp {camp}, which none of the scenario's own spawns use (theirs: {used}); the game "
                     f"spawns items only for the camps the scenario plays, so it may never appear. Check it in the "
                     f"game, or use one of those camps")
            trucks = (DEPOT_TRUCKS if m.trucks is None else m.trucks) if m.class_path == DEPOT else m.trucks
            z = m.z
            if z is None:  # no ground to read: the height of the nearest design item, never 0 under a hill
                near = min(s.items, key=lambda it: (it.position[0] - m.x) ** 2 + (it.position[1] - m.y) ** 2,
                           default=None)
                z = near.position[2] if near is not None else 0.0
            s.add_spawn(m.x, m.y, m.class_path, camp=camp, rotation=m.rotation, z=z, trucks=trucks)
            continue
        if isinstance(m, Start):
            item = s.add_start(m.x, m.y, m.team, m.place, m.rotation, m.z)
            # its opening camera: a copy of the warm-up path of the start it copies, moved by the same offset
            cam = cam_of(m.file)
            name = own_path(cam, s, item, "new")
            if name:
                mx, my = s.last_model
                cam.shift(name, m.x - mx, m.y - my)
                if m.camera:
                    cam.turn(name, m.x, m.y, m.camera)
            continue
        if isinstance(m, Place):
            z = m.z
            if z is None:  # no ground to read: the height of the nearest design item, never 0 under a hill
                near = min(s.items, key=lambda it: (it.position[0] - m.x) ** 2 + (it.position[1] - m.y) ** 2,
                           default=None)
                z = near.position[2] if near is not None else 0.0
            s.add_place(m.kind, m.x, m.y, z, name=m.name, text=m.text, rotation=m.rotation, radius=m.radius,
                        width=m.width, height=m.height)
            continue
        if m.item >= len(s.items):
            raise ScenarioError(f"{map_pack}: {m.file} has {len(s.items)} design items, not {m.item + 1}")
        if s.items[m.item].kind != m.kind:
            raise ScenarioError(f"{map_pack}: {m.file} item {m.item} is a {s.items[m.item].kind or 'plain item'}, "
                                f"not a {m.kind}: the mod was made for another version of this map")
        if isinstance(m, Remove):
            if s.items[m.item].listed:  # (two mods may both take it out: once is enough)
                s.remove(m.item)
            continue
        if isinstance(m, Change):
            camp = m.values.get("camp")
            if camp is not None and camp != NEUTRAL and m.file.lower() in skirmish:
                # rule: skirmish-neutral-spawns
                raise ScenarioError(f"{map_pack}: items.toml: item {m.item} of {m.file} is given camp {camp}, but "
                                    f"{m.file} is a skirmish map's scenario, and a skirmish game spawns only neutral "
                                    f"items: the game would leave it out without a word. Keep camp = -1, or change it "
                                    f"in an Operation's scenario")
            for field, value in m.values.items():
                s.set_value(m.item, field, value)
            continue
        ox, oy = s.items[m.item].position[:2]
        s.move(m.item, m.x, m.y, m.z, rotation=m.rotation)  # an item without a rotation can't be turned: move() says so
        if m.kind == "StartingPoint":  # its warm-up camera comes along (a shared path is copied first)
            cam = cam_of(m.file)
            name = own_path(cam, s, m.item, "move")
            if name:
                cam.shift(name, m.x - ox, m.y - oy)
                if (m.x, m.y) != (ox, oy):
                    later.append(f"{map_pack}: {m.file}: the starting point moved (item {m.item}) takes its warm-up "
                                 f"camera ({name}) along: the match opens looking at it from where it looked before")
                if m.camera:
                    cam.turn(name, m.x, m.y, m.camera)
                    later.append(f"{map_pack}: {m.file}: starting point {m.item}'s warm-up camera ({name}) turned "
                                 f"{math.degrees(m.camera):.0f} degrees about it")
    for member, s in files.values():
        mine = [m for m in moves if (folder + m.file).lower() == member.lower()]
        moved, spawned = sum(1 for m in mine if isinstance(m, Move)), sum(1 for m in mine if isinstance(m, Spawn))
        started = sum(1 for m in mine if isinstance(m, Start))
        removed = len({m.item for m in mine if isinstance(m, Remove)})
        changed = len({m.item for m in mine if isinstance(m, Change)})
        placed = sum(1 for m in mine if isinstance(m, Place))
        notes.append(f"{map_pack}: {member.rsplit(chr(92), 1)[-1]}: " + ", ".join(
            p for p in (f"{moved} item(s) moved" if moved else "", f"{removed} of its own item(s) taken out" if removed
                        else "", f"{changed} of its own item(s) changed" if changed else "",
                        f"{started} starting point(s) added" if started else "",
                        f"{spawned} spawn(s) added" if spawned else "",
                        f"{placed} name(s), named point(s) or zone(s) added" if placed else "") if p))
    out = {member: s.to_bytes() for member, s in files.values()}
    out.update({member: cam.to_bytes() for member, cam in cams.values() if cam is not None and cam.changed})
    return out, notes + later
