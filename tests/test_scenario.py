"""A map's scenario file (rusemod.scenario): its zones and design items, on a made-up file laid out like the game's
(the real ones are checked by tools, on all 102 the game ships)."""
import struct
import unittest

from fixtures import make_ndf, val
from rusemod.edat import Edat
from rusemod.scenario import AREA, MAGIC, Scenario, ScenarioError, with_checksum


def u32(*vs) -> bytes:
    return struct.pack(f"<{len(vs)}I", *vs)


def f32s(*vs) -> bytes:
    return struct.pack(f"<{len(vs)}f", *vs)


def zone(number: int, name: str, square: float) -> bytes:
    """A square zone of side `square` cut into 2 triangles, its 4 corners its border."""
    raw = name.encode()
    body = AREA + u32(2, number, len(raw)) + raw + bytes(-len(raw) % 4)
    body += AREA + f32s(square / 2, square / 2, 100.0)
    body += AREA + u32(1) + u32(0, 2, 0, 4)
    body += AREA + u32(0, 2, 0, 4)
    body += AREA + u32(0, 4)
    corners = [(0, 0), (square, 0), (square, square), (0, square)]
    body += AREA + u32(4, 2) + b"".join(f32s(x, y, 100.0, 0.0, 0.0) for x, y in corners)
    body += AREA + u32(0, 1, 2, 0, 2, 3)
    body += AREA + u32(4, 0, 1, 2, 3) + AREA + b"END0"
    return body


def design_items() -> bytes:
    """One starting point (alliance 2, turned 1.5 radians) and one spawn with a unit class, as TGameDesignItems,
    listed by a TGameDesignItemList as in the game's files."""
    def s(i):
        return val(0x07, struct.pack("<I", i))

    def ref(i, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))

    def vec(x, y, z):
        return val(0x0B, struct.pack("<3f", x, y, z))

    return make_ndf(
        objects=[(0, [(0, vec(1000.0, 2000.0, 50.0)), (1, val(0x05, struct.pack("<f", 1.5))), (2, ref(2, 1))]),
                 (0, [(0, vec(3000.0, 4000.0, 60.0)), (2, ref(3, 2))]),
                 (1, [(3, val(0x02, struct.pack("<i", 2))), (4, s(0))]),
                 (2, [(5, s(1))]),
                 (3, [(6, val(0x11, struct.pack("<I", 2) + ref(0, 0) + ref(1, 0)))])],
        classes=["TGameDesignItem", "TGameDesignAddOn_StartingPoint", "TGameDesignAddOn_Spawn", "TGameDesignItemList"],
        props=[("Position", 0), ("Rotation", 0), ("AddOn", 0), ("AllianceNum", 1), ("Name", 1),
               ("PythonClassName", 2), ("GameDesignItemList", 3)],
        strings=["HQ_Allies", "front.parametres.Classes.Unit_M4_Sherman"], topo=[4])


def scenario(zones=(("zone_a", 1000.0), ("zone_b", 500.0)), items=True) -> bytes:
    data = u32(len(zones)) + b"".join(zone(k, n, sq) for k, (n, sq) in enumerate(zones))
    out = MAGIC + bytes(16) + bytes(2) + u32(4, 1) + u32(len(data)) + data
    if items:
        nd = design_items()
        out += u32(len(nd)) + nd
    return with_checksum(out)


class Reading(unittest.TestCase):
    def test_zones(self):
        s = Scenario.read(scenario())
        self.assertEqual(s.version, 4)
        self.assertEqual([(z.number, z.name) for z in s.zones], [(0, "zone_a"), (1, "zone_b")])
        a = s.zones[0]
        self.assertEqual((a.anchor, len(a.vertices), a.triangles), ((500.0, 500.0, 100.0), 4, [(0, 1, 2), (0, 2, 3)]))
        self.assertEqual(a.outline_points(), [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)])
        self.assertEqual(a.outline, [0, 1, 2, 3])

    def test_design_items(self):
        start, spawn = Scenario.read(scenario()).items
        self.assertEqual((start.kind, start.position, start.rotation), ("StartingPoint", (1000.0, 2000.0, 50.0), 1.5))
        self.assertEqual(start.values, {"AllianceNum": 2, "Name": "HQ_Allies"})
        self.assertEqual((spawn.kind, spawn.rotation, spawn.values["PythonClassName"]),
                         ("Spawn", 0.0, "front.parametres.Classes.Unit_M4_Sherman"))

    def test_a_file_without_items_and_broken_files(self):
        self.assertEqual(Scenario.read(scenario(items=False)).items, [])
        with self.assertRaises(ScenarioError):
            Scenario.read(b"NOTASCENARIO" + bytes(40))
        broken = bytearray(scenario())
        broken[broken.find(b"END0")] = ord("X")
        with self.assertRaises(ScenarioError):
            Scenario.read(bytes(broken))


class Writing(unittest.TestCase):
    """Unchanged, the file comes back byte for byte (all 102 of the game's, by the round-trip check); a moved item
    reads back where it was put, and everything else stays."""

    def test_unchanged_is_byte_for_byte(self):
        for data in (scenario(), scenario(items=False), scenario(zones=())):
            self.assertEqual(Scenario.read(data).to_bytes(), data)

    def test_moving_a_starting_point(self):
        s = Scenario.read(scenario())
        s.move(0, 1500.0, 2500.0, rotation=0.5)
        back = Scenario.read(s.to_bytes())
        start, spawn = back.items
        self.assertEqual((start.position, start.rotation), ((1500.0, 2500.0, 50.0), 0.5))
        self.assertEqual(start.values, {"AllianceNum": 2, "Name": "HQ_Allies"})
        self.assertEqual(spawn.position, (3000.0, 4000.0, 60.0))
        self.assertEqual([z.name for z in back.zones], ["zone_a", "zone_b"])
        with self.assertRaises(ScenarioError):  # the spawn has no rotation to change
            s.move(1, 0.0, 0.0, rotation=1.0)

    def test_a_rewritten_ndf_keeps_the_padding_to_4_bytes(self):
        """The game pads the design items' NDF with zeros to a multiple of 4; without it the game crashed at start
        (2026-09-30). Rewritten unchanged, every shipped file comes back byte for byte this way."""
        s = Scenario.read(scenario())
        s.changed = True
        data = s.to_bytes()
        zones = struct.unpack_from("<I", data, 36)[0]
        size = struct.unpack_from("<I", data, 40 + zones)[0]
        self.assertEqual((size % 4, len(data) - (44 + zones + size)), (0, 0))  # padded, and nothing after it
        back = Scenario.read(data)
        self.assertEqual([(i.kind, i.position, i.values) for i in back.items],
                         [(i.kind, i.position, i.values) for i in Scenario.read(scenario()).items])

    def test_the_checksum_is_made_again(self):
        """The 16 bytes after the magic are the MD5 of bytes 0-9 and 28-end (LittleGroove's rule, true of all 102
        shipped files); the game checks it at launch and crashed on a moved starting point without it."""
        import hashlib
        s = Scenario.read(scenario())
        s.move(0, 7.0, 8.0)
        data = s.to_bytes()
        self.assertEqual(data[10:26], hashlib.md5(data[:10] + data[28:]).digest())
        self.assertNotEqual(data[10:26], bytes(16))

    def test_a_renamed_zone_is_written_with_its_new_name(self):
        s = Scenario.read(scenario())
        s.zones[1].name = "zone_new_longer_name"
        self.assertEqual([z.name for z in Scenario.read(s.to_bytes()).zones], ["zone_a", "zone_new_longer_name"])


def two_team_items() -> bytes:
    """Two starting points like the game's: team 1 place 1 and team 2 place 1, each with its camera (a point), its
    warm-up camera path and its angles."""
    def s(i):
        return val(0x07, struct.pack("<I", i))

    def ref(i, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))

    def vec(x, y, z):
        return val(0x0B, struct.pack("<3f", x, y, z))

    def i32(v):
        return val(0x02, struct.pack("<i", v))

    def f32(v):
        return val(0x05, struct.pack("<f", v))
    return make_ndf(
        objects=[(0, [(0, vec(1000.0, 2000.0, 50.0)), (1, f32(1.5)), (2, ref(2, 1))]),
                 (0, [(0, vec(9000.0, 8000.0, 70.0)), (1, f32(-1.5)), (2, ref(3, 1))]),
                 (1, [(3, i32(1)), (4, i32(1)), (5, vec(1100.0, 2600.0, 900.0)), (6, s(0)), (7, f32(-130.0))]),
                 (1, [(3, i32(2)), (4, i32(1)), (5, vec(8900.0, 7400.0, 900.0)), (6, s(1)), (7, f32(-270.0))]),
                 (2, [(8, val(0x11, struct.pack("<I", 2) + ref(0, 0) + ref(1, 0)))])],
        classes=["TGameDesignItem", "TGameDesignAddOn_StartingPoint", "TGameDesignItemList"],
        props=[("Position", 0), ("Rotation", 0), ("AddOn", 0), ("AllianceNum", 1), ("AlliancePriority", 1),
               ("PositionCamera", 1), ("WarmupCamPath", 1), ("Azimut", 1), ("GameDesignItemList", 2)],
        strings=["Warmup_J1", "Warmup_J4"], topo=[4])


def two_teams() -> bytes:
    nd = two_team_items()
    return with_checksum(MAGIC + bytes(16) + bytes(2) + u32(4, 1) + u32(4) + u32(0) + u32(len(nd)) + nd)


def campaths(paths=(("Warmup_J1", [(5000.0, 2000.0, 3000.0), (1600.0, 2000.0, 900.0)]),
                    ("Warmup_J4", [(5000.0, 8000.0, 3000.0), (9400.0, 8000.0, 900.0)]))) -> bytes:
    """A made-up campaths file laid out as the game's (TCameraPath: PositionKeyVector, DirectionKeyVector, Name; each
    key a TCameraPathKey with its Coord), one look direction per key (straight down the x axis)."""
    def ref(i, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))

    def vec(x, y, z):
        return val(0x0B, struct.pack("<3f", x, y, z))
    objects, strings = [], []
    for name, keys in paths:
        at = len(objects)
        keys_at = [at + 1 + k for k in range(len(keys))]
        dirs_at = [at + 1 + len(keys) + k for k in range(len(keys))]
        strings.append(name)
        objects.append((0, [(0, val(0x11, struct.pack("<I", len(keys)) + b"".join(ref(k, 1) for k in keys_at))),
                            (1, val(0x11, struct.pack("<I", len(keys)) + b"".join(ref(k, 1) for k in dirs_at))),
                            (2, val(0x07, struct.pack("<I", len(strings) - 1)))]))
        objects += [(1, [(3, vec(*p))]) for p in keys]
        objects += [(1, [(3, vec(-1.0, 0.0, 0.0))]) for _p in keys]
    return make_ndf(objects=objects, classes=["TCameraPath", "TCameraPathKey"],
                    props=[("PositionKeyVector", 0), ("DirectionKeyVector", 0), ("Name", 0), ("Coord", 1)],
                    strings=strings)


class Starts(unittest.TestCase):
    """More players need more starting points (PLAN A10): a new one copies a teammate's."""

    def test_a_new_place_for_a_team(self):
        s = Scenario.read(two_teams())
        self.assertEqual(s.places(), {1: {1}, 2: {1}})
        n = s.add_start(1500.0, 2300.0, 1, z=64.0)
        back = Scenario.read(s.to_bytes())
        it = back.items[n]
        self.assertEqual((it.kind, it.position, it.rotation), ("StartingPoint", (1500.0, 2300.0, 64.0), 1.5))
        self.assertEqual((it.values["AllianceNum"], it.values["AlliancePriority"], it.values["WarmupCamPath"],
                          it.values["Azimut"]), (1, 2, "Warmup_J1", -130.0))
        camera = struct.unpack("<3f", bytes.fromhex(it.values["PositionCamera"]))
        self.assertEqual(camera, (1600.0, 2900.0, 900.0))  # moved with it, same height
        self.assertEqual(back.places(), {1: {1, 2}, 2: {1}})
        self.assertEqual(back.items[1].position, (9000.0, 8000.0, 70.0))  # the others stay

    def test_a_moved_start_takes_its_camera_along(self):
        """The game opens a skirmish looking from the start's PositionCamera when it has one, so a moved start's
        camera moves by the same offset (a start shaped like Chess's, which carry one each); z is the given height."""
        from rusemod.scenario import Move, apply_moves, folder_of
        s = Scenario.read(two_teams())
        s.move(0, 1000.0 + 5000.0, 2000.0 + 5000.0, z=77.0)
        back = Scenario.read(s.to_bytes())
        it = back.items[0]
        self.assertEqual(it.position, (6000.0, 7000.0, 77.0))
        self.assertEqual(struct.unpack("<3f", bytes.fromhex(it.values["PositionCamera"])), (6100.0, 7600.0, 900.0))
        self.assertEqual(struct.unpack("<3f", bytes.fromhex(back.items[1].values["PositionCamera"])),
                         (8900.0, 7400.0, 900.0))  # the other start's stays
        member = folder_of("Blitz") + "leveldesign.scenario"
        new, notes = apply_moves({member: two_teams()}.get, "Blitz",
                                 [Move("leveldesign.scenario", 1, "StartingPoint", 100.0, 200.0, z=5.0)])
        it = Scenario.read(new[member]).items[1]
        self.assertEqual(it.position, (100.0, 200.0, 5.0))
        self.assertEqual(struct.unpack("<3f", bytes.fromhex(it.values["PositionCamera"])), (0.0, -400.0, 900.0))
        self.assertEqual(notes, ["Blitz: leveldesign.scenario: 1 item(s) moved"])  # no camera file: nothing to carry

    def test_the_warm_up_camera_comes_along(self):
        """The match opens on the start's warm-up camera path (LittleGroove: PositionCamera is inert): a moved start
        takes its path along, a new start gets a copy of the one it copies, a shared path is copied first."""
        from rusemod.scenario import Move, Start, apply_moves, campath_member, campaths as read_paths, folder_of
        member, cam = folder_of("Blitz") + "leveldesign.scenario", campath_member("Blitz", "leveldesign.scenario")
        files = {member: two_teams(), cam: campaths()}
        new, notes = apply_moves(files.get, "Blitz", [Move("leveldesign.scenario", 1, "StartingPoint", 100.0, 200.0)])
        paths = read_paths(new[cam])
        self.assertEqual(paths["Warmup_J4"]["path"], [[-3900.0, 200.0, 3000.0], [500.0, 200.0, 900.0]])  # by -8900,-7800
        self.assertEqual(paths["Warmup_J1"]["path"], [[5000.0, 2000.0, 3000.0], [1600.0, 2000.0, 900.0]])  # the other's
        self.assertEqual(paths["Warmup_J4"]["looks"], [[-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]])  # the same view
        self.assertTrue(any("takes its warm-up camera (Warmup_J4) along" in n for n in notes), notes)
        # a new start for team 1: its own copy of Warmup_J1, moved as far as it stands from team 1's start
        new, _ = apply_moves(files.get, "Blitz", [Start("leveldesign.scenario", 1, 3000.0, 2000.0)])
        s, paths = Scenario.read(new[member]), read_paths(new[cam])
        self.assertEqual(s.items[-1].values["WarmupCamPath"], "Warmup_J1_mod1")
        self.assertEqual(paths["Warmup_J1_mod1"]["path"], [[7000.0, 2000.0, 3000.0], [3600.0, 2000.0, 900.0]])
        self.assertEqual(paths["Warmup_J1"]["path"][1], [1600.0, 2000.0, 900.0])  # team 1's own stays
        self.assertEqual(s.items[0].values["WarmupCamPath"], "Warmup_J1")
        # two starts on one path: the moved one gets its own copy, the other keeps the path where it was
        shared = {member: two_teams(), cam: campaths()}
        two = Scenario.read(shared[member])
        two.set_warmup(1, "Warmup_J1")
        shared[member] = two.to_bytes()
        new, _ = apply_moves(shared.get, "Blitz", [Move("leveldesign.scenario", 1, "StartingPoint", 9900.0, 8000.0)])
        s, paths = Scenario.read(new[member]), read_paths(new[cam])
        self.assertEqual((s.items[0].values["WarmupCamPath"], s.items[1].values["WarmupCamPath"]),
                         ("Warmup_J1", "Warmup_J1_mod1"))
        self.assertEqual(paths["Warmup_J1"]["path"][1], [1600.0, 2000.0, 900.0])
        self.assertEqual(paths["Warmup_J1_mod1"]["path"][1], [2500.0, 2000.0, 900.0])  # moved by +900, 0

    def test_the_warm_up_camera_turned_round_its_start(self):
        """LittleGroove's camera ring: the path goes round the start (radius and height kept), its looks turn as much."""
        import math
        import tomllib
        from rusemod.scenario import Move, Start, apply_moves, campath_member, campaths as read_paths, folder_of
        from rusemod.scenario import moves_toml, parse_moves, parse_starts, starts_toml
        member, cam = folder_of("Blitz") + "leveldesign.scenario", campath_member("Blitz", "leveldesign.scenario")
        files = {member: two_teams(), cam: campaths()}
        turn = Move("leveldesign.scenario", 1, "StartingPoint", 9000.0, 8000.0, camera=math.pi / 2)  # where it stands
        new, notes = apply_moves(files.get, "Blitz", [turn])
        paths = read_paths(new[cam])
        self.assertEqual(paths["Warmup_J4"]["path"], [[9000.0, 4000.0, 3000.0], [9000.0, 8400.0, 900.0]])
        self.assertEqual(paths["Warmup_J4"]["looks"], [[0.0, -1.0, 0.0], [0.0, -1.0, 0.0]])
        self.assertEqual(paths["Warmup_J1"]["path"][1], [1600.0, 2000.0, 900.0])  # the other start's stays
        self.assertTrue(any("turned 90 degrees" in n for n in notes), notes)
        self.assertFalse(any("takes its warm-up camera" in n for n in notes), notes)  # not moved
        # a new start's copy turns about the new start
        new, _ = apply_moves(files.get, "Blitz", [Start("leveldesign.scenario", 1, 3000.0, 2000.0, camera=math.pi)])
        self.assertEqual(read_paths(new[cam])["Warmup_J1_mod1"]["path"], [[-1000.0, 2000.0, 3000.0], [2400.0, 2000.0, 900.0]])
        # kept in the mod file; only a starting point has a camera
        self.assertEqual(parse_moves(tomllib.loads(moves_toml([turn]))["move"]), [turn])
        st = Start("leveldesign.scenario", 1, 3000.0, 2000.0, camera=-0.5)
        self.assertEqual(parse_starts(tomllib.loads(starts_toml([st]))["start"]), [st])
        with self.assertRaisesRegex(ScenarioError, "only a starting point has a camera"):
            parse_moves([{"file": "a.scenario", "item": 3, "kind": "Spawn", "x": 1, "y": 2, "camera": 1.0}])
        with self.assertRaisesRegex(ScenarioError, "numbers"):
            parse_starts([{"file": "a.scenario", "team": 1, "x": 1, "y": 2, "camera": "left"}])

    def test_a_start_without_a_camera_of_its_own(self):
        s = Scenario.read(scenario())  # its start has no PositionCamera: the game looks at the start itself
        s.move(0, 10.0, 20.0)
        self.assertNotIn("PositionCamera", Scenario.read(s.to_bytes()).items[0].values)

    def test_a_team_with_no_start_yet_and_refusals(self):
        s = Scenario.read(two_teams())
        n = s.add_start(8500.0, 7000.0, 3, rotation=0.25)  # copies the nearest: team 2's, keeps its height
        it = s.items[n]
        self.assertEqual((it.values["AllianceNum"], it.values["AlliancePriority"], it.position[2], it.rotation),
                         (3, 1, 70.0, 0.25))
        with self.assertRaisesRegex(ScenarioError, "already has a starting point at place 1"):
            s.add_start(0.0, 0.0, 2, place=1)
        with self.assertRaisesRegex(ScenarioError, "no starting point to copy"):
            Scenario.read(scenario(items=False)).add_start(0.0, 0.0, 1)

    def test_the_mod_file(self):
        import tomllib
        from rusemod.scenario import Start, parse_starts, starts_toml
        starts = [Start("leveldesign_3v3_v01.scenario", 1, 2710720.0, 1774720.0),
                  Start("leveldesign_3v3_v01.scenario", 2, 1959360.0, 1831360.0, place=4, rotation=1.5)]
        self.assertEqual(parse_starts(tomllib.loads(starts_toml(starts))["start"]), starts)
        for bad, why in (({"file": "a.scenario", "team": 0, "x": 1, "y": 2}, "1 to 8"),
                         ({"file": "a.scenario", "team": 9, "x": 1, "y": 2}, "1 to 8"),
                         ({"file": "a.scenario", "team": True, "x": 1, "y": 2}, "whole numbers"),
                         ({"file": "a.txt", "team": 1, "x": 1, "y": 2}, "scenario's name"),
                         ({"file": "a.scenario", "team": 1, "x": 1}, "y is missing"),
                         ({"file": "a.scenario", "team": 1, "x": 1, "y": 2, "camp": 1}, "unknown key 'camp'")):
            with self.assertRaisesRegex(ScenarioError, why):
                parse_starts([bad])

    def test_applied_with_the_moves(self):
        from rusemod.scenario import Start, apply_moves, folder_of
        member = folder_of("Blitz") + "leveldesign.scenario"
        new, notes = apply_moves({member: two_teams()}.get, "Blitz",
                                 [Start("leveldesign.scenario", 1, 1500.0, 2300.0),
                                  Start("leveldesign.scenario", 2, 8000.0, 7000.0)])
        self.assertEqual(Scenario.read(new[member]).places(), {1: {1, 2}, 2: {1, 2}})
        self.assertIn("2 starting point(s) added", notes[0])


class Removes(unittest.TestCase):
    """The map's own items taken out (LittleGroove's way): off the design item list the game loads, the object kept,
    so every item keeps its number. Every item of the 102 shipped scenarios is on its list (not yet seen in the
    game taken off)."""
    MEMBER = "test\\map\\blitz\\leveldesign.scenario"

    def test_a_spawn_taken_off_the_list(self):
        from rusemod.ndf import local_ref, sub_values
        from rusemod.scenario import view
        s = Scenario.read(scenario())
        s.remove(1)
        back = Scenario.read(s.to_bytes())
        self.assertEqual([(i.kind, i.listed) for i in back.items], [("StartingPoint", True), ("Spawn", False)])
        self.assertEqual(back.items[1].position, (3000.0, 4000.0, 60.0))  # still there, at its number
        holder = next(o for o in back.ndf.objects if back.ndf.classes[o.cls] == "TGameDesignItemList")
        self.assertEqual([local_ref(x) for _pi, v in holder.props for x in sub_values(v)], [back.items[0].obj])
        self.assertEqual([it.get("gone", False) for it in view(back)["items"]], [False, True])
        with self.assertRaisesRegex(ScenarioError, "off the scenario's list already"):
            back.remove(1)

    def test_the_last_item_leaves_no_list(self):
        """With nothing on it the list is left out, as 11 shipped scenarios have it."""
        s = Scenario.read(scenario())
        s.remove(1)
        s.remove(0)
        back = Scenario.read(s.to_bytes())
        holder = next(o for o in back.ndf.objects if back.ndf.classes[o.cls] == "TGameDesignItemList")
        self.assertEqual(holder.props, [])
        self.assertEqual([i.listed for i in back.items], [False, False])

    def test_the_mod_file(self):
        import tomllib
        from rusemod.scenario import Remove, parse_removes, removes_toml
        removes = [Remove("leveldesign_3v3_v01.scenario", 41, "Spawn"),
                   Remove("leveldesign_3v3_v01.scenario", 3, "LabelVille")]
        self.assertEqual(parse_removes(tomllib.loads(removes_toml(removes))["remove"]), removes)
        for bad, why in (({"file": "a.scenario", "item": 0, "kind": "StartingPoint"}, "every player needs one"),
                         ({"file": "a.scenario", "item": 0, "kind": "Tree"}, "kind must be one of"),
                         ({"file": "a.scenario", "item": -1, "kind": "Spawn"}, "whole number, 0 or more"),
                         ({"file": "a.scenario", "item": 1.5, "kind": "Spawn"}, "whole number, 0 or more"),
                         ({"file": "a.txt", "item": 0, "kind": "Spawn"}, "scenario's name"),
                         ({"file": "a.scenario", "kind": "Spawn"}, "item is missing"),
                         ({"file": "a.scenario", "item": 0, "kind": "Spawn", "x": 1}, "unknown key 'x'")):
            with self.assertRaisesRegex(ScenarioError, why):
                parse_removes([bad])

    def test_applied_with_the_moves(self):
        from rusemod.scenario import Move, Remove, apply_moves
        read = {self.MEMBER: scenario()}.get
        new, notes = apply_moves(read, "Blitz", [Move("leveldesign.scenario", 0, "StartingPoint", 1500.0, 2500.0),
                                                 Remove("leveldesign.scenario", 1, "Spawn"),
                                                 Remove("leveldesign.scenario", 1, "Spawn")])  # two mods: once is enough
        back = Scenario.read(new[self.MEMBER])
        self.assertEqual([(i.position[:2], i.listed) for i in back.items], [((1500.0, 2500.0), True),
                                                                             ((3000.0, 4000.0), False)])
        self.assertIn("1 item(s) moved, 1 of its own item(s) taken out", notes[0])
        with self.assertRaisesRegex(ScenarioError, "item 0 is a StartingPoint, not a Spawn: the mod was made for "
                                                   "another version of this map"):
            apply_moves(read, "Blitz", [Remove("leveldesign.scenario", 0, "Spawn")])
        with self.assertRaisesRegex(ScenarioError, "has 2 design items, not 6"):
            apply_moves(read, "Blitz", [Remove("leveldesign.scenario", 5, "Spawn")])


def detail_items() -> bytes:
    """Items with values to change, as the 102 shipped scenarios keep them: a supply depot with its trucks
    (ChampInteger) and side (Camp), a depot without trucks, a unit spawn without a Camp (read as camp 0), a circle zone
    (Radius) and a rectangle zone (Width, Height), all float32s and whole numbers as the game has them."""
    def s(i):
        return val(0x07, struct.pack("<I", i))

    def i32(v):
        return val(0x02, struct.pack("<i", v))

    def f32(v):
        return val(0x05, struct.pack("<f", v))

    def ref(i, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))

    def item(k, addon, cls):
        return (0, [(0, val(0x0B, struct.pack("<3f", 100.0 * k, 200.0, 10.0))), (1, f32(0.0)), (2, ref(addon, cls))])
    return make_ndf(
        objects=[item(0, 5, 1), item(1, 6, 1), item(2, 7, 1), item(3, 8, 2), item(4, 9, 3),
                 (1, [(3, s(0)), (4, i32(25)), (5, i32(-1))]),       # 5 a depot: trucks, then its side
                 (1, [(3, s(0)), (5, i32(1))]),                       # 6 a depot without trucks
                 (1, [(3, s(1))]),                                    # 7 a unit without a Camp
                 (2, [(6, s(2)), (7, f32(50000.0))]),                 # 8 a circle zone
                 (3, [(8, s(3)), (9, f32(2000.0)), (10, f32(3000.0))]),  # 9 a rectangle zone
                 (4, [(11, val(0x11, struct.pack("<I", 5) + b"".join(ref(i, 0) for i in range(5))))])],
        classes=["TGameDesignItem", "TGameDesignAddOn_Spawn", "TGameDesignAddOn_CircularZone",
                 "TGameDesignAddOn_RectangleZone", "TGameDesignItemList"],
        props=[("Position", 0), ("Rotation", 0), ("AddOn", 0), ("PythonClassName", 1), ("ChampInteger", 1), ("Camp", 1),
               ("Name", 2), ("Radius", 2), ("Name", 3), ("Width", 3), ("Height", 3), ("GameDesignItemList", 4)],
        strings=["front.batiment_depot.DalleBatimentDepot", "front.parametres.Classes.Unit_M4_Sherman", "zone_a",
                 "zone_b"], topo=[10])


def detail_scenario() -> bytes:
    nd = detail_items()
    return with_checksum(MAGIC + bytes(16) + bytes(2) + u32(4, 1) + u32(4) + u32(0) + u32(len(nd)) + nd)


class Changes(unittest.TestCase):
    """The map's own items with some of their values changed (maps/<map>/items.toml, LittleGroove's Details panel):
    a spawn's side, a supply depot's trucks, a zone's size, each written in the type the item has it in. Not yet seen
    in the game."""
    MEMBER = "test\\map\\blitz\\leveldesign.scenario"

    def test_values_written_in_the_items_own_types(self):
        s = Scenario.read(detail_scenario())
        self.assertEqual([i.kind for i in s.items], ["Spawn", "Spawn", "Spawn", "CircularZone", "RectangleZone"])
        s.set_value(0, "trucks", 40)
        s.set_value(0, "camp", 2)
        s.set_value(1, "trucks", 30)    # a depot without trucks gets them, before its Camp as the shipped ones have it
        s.set_value(2, "camp", 3)       # a spawn without a Camp gets one
        s.set_value(3, "radius", 75000.5)
        s.set_value(4, "width", 2500)
        s.set_value(4, "height", 3500.25)
        for i, field in ((2, "trucks"), (0, "radius"), (3, "width")):
            with self.subTest(item=i, field=field), self.assertRaisesRegex(ScenarioError, "has no"):
                s.set_value(i, field, 1)
        back = Scenario.read(s.to_bytes())
        self.assertEqual([i.values for i in back.items], [
            {"PythonClassName": "front.batiment_depot.DalleBatimentDepot", "ChampInteger": 40, "Camp": 2},
            {"PythonClassName": "front.batiment_depot.DalleBatimentDepot", "ChampInteger": 30, "Camp": 1},
            {"PythonClassName": "front.parametres.Classes.Unit_M4_Sherman", "Camp": 3},
            {"Name": "zone_a", "Radius": 75000.5}, {"Name": "zone_b", "Width": 2500.0, "Height": 3500.25}])
        nd = back.ndf
        depot = nd.objects[6]  # the depot that had no trucks: PythonClassName, ChampInteger, Camp
        self.assertEqual([(nd.prop_name(pi), v.tc) for pi, v in depot.props],
                         [("PythonClassName", 0x07), ("ChampInteger", 0x02), ("Camp", 0x02)])
        self.assertEqual([(nd.prop_name(pi), v.tc) for pi, v in nd.objects[8].props], [("Name", 0x07), ("Radius", 0x05)])
        from rusemod.scenario import view
        self.assertEqual([(it.get("camp"), it.get("trucks")) for it in view(back)["items"][:3]],
                         [(2, 40), (1, 30), (3, None)])

    def test_the_mod_file(self):
        import tomllib
        from rusemod.scenario import Change, changes_toml, parse_changes
        changes = [Change("a.scenario", 0, "Spawn", {"camp": -1, "trucks": 40}),
                   Change("a.scenario", 3, "CircularZone", {"radius": 75000.0}),
                   Change("a.scenario", 4, "RectangleZone", {"width": 2500, "height": 3500.5})]
        text = changes_toml(changes, "a header\nof two lines")
        self.assertTrue(text.startswith("# a header\n# of two lines\n"))
        self.assertEqual(parse_changes(tomllib.loads(text)["set"]), changes)
        for bad, why in (({"kind": "StartingPoint"}, "kind must be one of"),
                         ({"kind": "Spawn", "radius": 5}, "unknown key 'radius'"),
                         ({"kind": "Spawn", "camp": -2}, "camp is -1"),
                         ({"kind": "Spawn", "camp": 1.5}, "camp is -1"),
                         ({"kind": "Spawn", "camp": True}, "camp is a number"),
                         ({"kind": "Spawn", "trucks": 1001}, "0 to 1000"),
                         ({"kind": "CircularZone", "radius": 0}, "more than 0"),
                         ({"kind": "CircularZone", "radius": float("nan")}, "more than 0"),
                         ({"kind": "Spawn"}, "changes nothing"),
                         ({"kind": "Spawn", "item": -1, "camp": 1}, "whole number, 0 or more"),
                         ({"kind": "Spawn", "file": "a.txt", "camp": 1}, "scenario's name")):
            with self.subTest(bad=bad), self.assertRaisesRegex(ScenarioError, why):
                parse_changes([{"file": "a.scenario", "item": 0, **bad}])

    def test_applied_after_the_moves(self):
        from rusemod.scenario import Change, Move, apply_moves
        read = {self.MEMBER: detail_scenario()}.get
        new, notes = apply_moves(read, "Blitz", [Move("leveldesign.scenario", 0, "Spawn", 10.0, 20.0),
                                                 Change("leveldesign.scenario", 0, "Spawn", {"trucks": 60}),
                                                 Change("leveldesign.scenario", 3, "CircularZone", {"radius": 9000})])
        back = Scenario.read(new[self.MEMBER])
        self.assertEqual((back.items[0].position[:2], back.items[0].values["ChampInteger"], back.items[3].values["Radius"]),
                         ((10.0, 20.0), 60, 9000.0))
        self.assertIn("1 item(s) moved, 2 of its own item(s) changed", notes[0])
        with self.assertRaisesRegex(ScenarioError, "item 3 is a CircularZone, not a Spawn"):
            apply_moves(read, "Blitz", [Change("leveldesign.scenario", 3, "Spawn", {"camp": 1})])
        # a skirmish scenario's items stay neutral, as its spawns do (the game leaves the others out)
        with self.assertRaisesRegex(ScenarioError, "item 1 of leveldesign.scenario is given camp 2, but "
                                                   "leveldesign.scenario is a skirmish map's scenario"):
            apply_moves(read, "Blitz", [Change("leveldesign.scenario", 1, "Spawn", {"camp": 2})], {"leveldesign.scenario"})
        new, _notes = apply_moves(read, "Blitz", [Change("leveldesign.scenario", 1, "Spawn", {"camp": -1})],
                                  {"leveldesign.scenario"})
        self.assertEqual(Scenario.read(new[self.MEMBER]).items[1].values["Camp"], -1)

    def test_the_build_reads_them_after_the_scenario_files_edits(self):
        import tempfile
        from pathlib import Path
        from rusemod.build import load_mod
        from rusemod.scenario import Change, Remove
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp, "items-test")
            (mod / "maps" / "Blitz").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "items-test"\nversion = "0.1.0"\n', encoding="utf-8")
            (mod / "maps" / "Blitz" / "scenario.toml").write_text(
                '[[remove]]\nfile = "leveldesign.scenario"\nitem = 2\nkind = "Spawn"\n', encoding="utf-8")
            (mod / "maps" / "Blitz" / "items.toml").write_text(
                '[[set]]\nfile = "leveldesign.scenario"\nitem = 0\nkind = "Spawn"\ntrucks = 50\n', encoding="utf-8")
            info, _ops = load_mod(mod)
        self.assertEqual(info.scenario["Blitz"], [Remove("leveldesign.scenario", 2, "Spawn"),
                                                  Change("leveldesign.scenario", 0, "Spawn", {"trucks": 50})])


class Spawns(unittest.TestCase):
    """New spawns as the game takes them: a skirmish game spawns only neutral items (camp -1), a spawn without a
    Camp reads as camp 0, a depot slab starts with ChampInteger trucks, and every shipped spawn has the ground's z."""
    MEMBER = "test\\map\\blitz\\leveldesign.scenario"

    def apply(self, spawns, skirmish=(), warned=None):
        from rusemod.scenario import apply_moves
        new, _notes = apply_moves({self.MEMBER: scenario()}.get, "Blitz", spawns, skirmish,
                                  warned.append if warned is not None else None)
        return Scenario.read(new[self.MEMBER]).items[-1]

    def test_a_skirmish_scenario_takes_only_neutral_spawns(self):
        from rusemod.scenario import Spawn
        with self.assertRaisesRegex(ScenarioError, "scenario.toml: the spawn of Unit_M4_Sherman .* is for camp 1, but "
                                                   "leveldesign.scenario is a skirmish map's scenario.*camp = -1"):
            self.apply([Spawn("leveldesign.scenario", "Unit_M4_Sherman", 5.0, 6.0, camp=1)], {"leveldesign.scenario"})
        it = self.apply([Spawn("leveldesign.scenario", "Unit_M4_Sherman", 5.0, 6.0, camp=-1)], {"leveldesign.scenario"})
        self.assertEqual(it.values["Camp"], -1)
        it = self.apply([Spawn("leveldesign.scenario", "Unit_M4_Sherman", 5.0, 6.0)], {"leveldesign.scenario"})
        self.assertEqual(it.values["Camp"], -1)  # no camp given: written neutral, never left out (camp 0)

    def test_a_camp_the_scenario_never_spawns_for_warns(self):
        from rusemod.scenario import Spawn
        warned = []
        self.apply([Spawn("leveldesign.scenario", "Unit_M4_Sherman", 5.0, 6.0, camp=3)], warned=warned)
        self.assertEqual(len(warned), 1)
        self.assertIn("camp 3, which none of the scenario's own spawns use (theirs: 0)", warned[0])
        warned.clear()
        self.apply([Spawn("leveldesign.scenario", "Unit_M4_Sherman", 5.0, 6.0, camp=-1)], warned=warned)
        self.assertEqual(warned, [])

    def test_a_camp_its_mission_lists_is_fine_and_one_it_doesnt_warns(self):
        # the tester, 2026-10-03: French units for M03_Italie's camp 2 and British ones for camp 4 were warned "may
        # never appear", as no shipped spawn uses those camps; the chapter's mission lists both (France, Britain)
        from rusemod.missions import Camp
        from rusemod.scenario import Spawn, apply_moves
        camps = [Camp(0, "IR_763", True, "Player", "EU", 1), Camp(2, "IR_761", False, "Scripted", "France", 1),
                 Camp(4, "IR_759", False, "Scripted", "RU", 1)]
        warned = []
        for camp in (0, 2, 4, -1):  # the player's camp (0, refused before) and two the shipped spawns never use
            apply_moves({self.MEMBER: scenario()}.get, "Blitz", [Spawn("leveldesign.scenario", "Unit_X", 5.0, 6.0,
                        camp=camp)], (), warned.append, mission=lambda file: camps)
        self.assertEqual(warned, [])
        apply_moves({self.MEMBER: scenario()}.get, "Blitz", [Spawn("leveldesign.scenario", "Unit_X", 5.0, 6.0, camp=7)],
                    (), warned.append, mission=lambda file: camps)
        self.assertEqual(len(warned), 1)
        self.assertIn("camp 7, which isn't one of the camps its mission lists (0 (the player, EU), 2 (the computer, "
                      "France), 4 (the computer, RU))", warned[0])

    def test_a_depot_takes_the_shipped_class_path_and_trucks(self):
        from rusemod.scenario import DEPOT, Spawn
        it = self.apply([Spawn("leveldesign.scenario", "DalleBatimentDepot", 5.0, 6.0)])
        self.assertEqual(it.values, {"PythonClassName": DEPOT, "ChampInteger": 25, "Camp": -1})
        it = self.apply([Spawn("leveldesign.scenario", "DalleBatimentDepot", 5.0, 6.0, trucks=40)])
        self.assertEqual(it.values["ChampInteger"], 40)
        it = self.apply([Spawn("leveldesign.scenario", "Unit_M4_Sherman", 5.0, 6.0)])
        self.assertNotIn("ChampInteger", it.values)

    def test_the_height(self):
        from rusemod.scenario import Spawn
        self.assertEqual(self.apply([Spawn("leveldesign.scenario", "Unit_M4_Sherman", 5.0, 6.0, z=33.0)]).position,
                         (5.0, 6.0, 33.0))
        # no ground given: the nearest design item's height (the start at 1000, 2000 is at 50), never 0 under a hill
        self.assertEqual(self.apply([Spawn("leveldesign.scenario", "Unit_M4_Sherman", 900.0, 2100.0)]).position[2],
                         50.0)

    def test_classes_the_game_can_find(self):
        from rusemod.scenario import Spawn, spawn_class_problems
        shipped = {"front.parametres.generated_data.ParamsUnites.Unit_LCVP"}
        spawns = [Spawn("a.scenario", w, 1.0, 2.0) for w in (
            "Unit_M4_Sherman", "DalleBatimentDepot", "parametres.Classes.Unit_M4_Sherman", "Unit_Ghost",
            "front.parametres.generated_data.ParamsUnites.Unit_LCVP", "front.parametres.generated_data.ParamsUnites.Unit_X")]
        wrong = spawn_class_problems("Blitz", spawns, {"Unit_M4_Sherman"}, lambda: shipped)
        self.assertEqual(len(wrong), 2, wrong)
        self.assertIn("the spawn of Unit_Ghost in a.scenario: the game's unit list has no class Unit_Ghost", wrong[0])
        self.assertIn("ParamsUnites.Unit_X isn't a class path any shipped spawn uses", wrong[1])
        # the unit list can't be read: its classes aren't checked, the other paths still are
        self.assertEqual(len(spawn_class_problems("Blitz", spawns, None, lambda: shipped)), 1)

    def test_the_mod_file(self):
        import tomllib
        from rusemod.scenario import Spawn, parse_spawns, spawns_toml
        spawns = [Spawn("a.scenario", "DalleBatimentDepot", 1.0, 2.0, -1, 0.5, 30), Spawn("a.scenario", "Unit_X", 3.0, 4.0, 2)]
        self.assertEqual(parse_spawns(tomllib.loads(spawns_toml(spawns))["spawn"]), spawns)
        self.assertEqual(parse_spawns([{"file": "a.scenario", "what": "Unit_X", "x": 1, "y": 2,
                                        "camp": 0}])[0].camp, 0)
        for bad, why in (({"camp": -2}, "camp is -1"), ({"camp": True}, "whole numbers"),
                         ({"trucks": 5}, "only for a supply depot"),
                         ({"what": "DalleBatimentDepot", "trucks": -1}, "0 to 1000"),
                         ({"x": float("inf")}, "finite")):
            with self.subTest(bad=bad), self.assertRaisesRegex(ScenarioError, why):
                parse_spawns([{"file": "a.scenario", "what": "Unit_X", "x": 1, "y": 2, **bad}])


def mapinfo(road_y=2000.0) -> bytes:
    """A made-up mapinfo.win: test_nav's row of three ground circles along y 2000 (x 2000 to 10000) for infantry and
    vehicles, and one road along y `road_y` from x 0 to 12000."""
    from rusemod import nav
    from rusemod.roadnet import RoadNet, build_tree
    from test_nav import row
    net = RoadNet([(0.0, road_y), (12000.0, road_y)], [])
    net.links = [(0, 1, net._cost(0, 1))]
    net.tree = build_tree(net.points, net.links)
    head = b"INFOIA\r\n" + bytes(16) + struct.pack("<II4f", 20, 6, 0.0, 0.0, 16000.0, 16000.0)
    return nav.replace_buffers(head + b"".join(struct.pack("<I", len(b)) + b for b in (
        net.to_bytes(), row().to_bytes(), row().to_bytes(), b"cover")) + b"tail", {})


class StartGround(unittest.TestCase):
    """A starting point where no ground unit can stand gets its HQ wherever the game finds room, possibly far away: a
    new or moved one is checked on the map's final movement and roads. A wood (closed to vehicles only) is fine: the
    owner, 2026-10-02, an HQ there works and supply trucks drive through woods."""

    def test_a_wood_is_fine_ground_no_unit_can_use_is_not(self):
        from rusemod.cover import member
        from rusemod.nav import Block, apply_blocks
        from rusemod.scenario import Start, start_ground_problems
        wood = {member("Blitz"): mapinfo()}
        new, _notes = apply_blocks(wood.get, "Blitz", [Block(2000.0, 2000.0, 1500.0, "vehicles")])
        wood.update(new)  # circle A closed to vehicles only, as a wood is
        here = [Start("a.scenario", 1, 2000.0, 2000.0)]
        self.assertEqual(start_ground_problems(wood.get, "Blitz", here), ([], []))
        closed = {member("Blitz"): mapinfo()}
        new, _notes = apply_blocks(closed.get, "Blitz", [Block(2000.0, 2000.0, 1500.0, "all")])
        closed.update(new)  # closed to every unit
        errors, _ = start_ground_problems(closed.get, "Blitz", here)
        self.assertEqual(len(errors), 1)
        self.assertIn("where no ground unit can stand", errors[0])

    def test_on_the_ground_off_it_and_far_from_a_road(self):
        from rusemod.cover import member
        from rusemod.scenario import Move, Start, start_ground_problems
        read = {member("Blitz"): mapinfo()}.get
        ok = [Start("a.scenario", 1, 2000.0, 2000.0), Move("a.scenario", 0, "StartingPoint", 7000.0, 2500.0)]
        self.assertEqual(start_ground_problems(read, "Blitz", ok), ([], []))
        errors, warnings = start_ground_problems(read, "Blitz", [Start("a.scenario", 2, 50000.0, 9000.0),
                                                                 Move("a.scenario", 3, "StartingPoint", 2000.0, 7000.0)])
        self.assertEqual((len(errors), warnings), (2, []))
        self.assertIn("Blitz: scenario.toml: the new starting point for team 2 at (50000, 9000) in a.scenario is where "
                      "no ground unit can stand", errors[0])
        self.assertIn("the starting point moved (item 3)", errors[1])
        far = {member("Blitz"): mapinfo(road_y=40000.0)}.get
        errors, warnings = start_ground_problems(far, "Blitz", ok)
        self.assertEqual((errors, len(warnings)), ([], 2))
        self.assertIn("38,000 map units from the nearest road", warnings[0])
        # a spawn, a label, or a map without its mapinfo.win: nothing to check
        self.assertEqual(start_ground_problems(read, "Blitz", [Move("a.scenario", 1, "LabelVille", 9e9, 9e9)]), ([], []))
        self.assertEqual(start_ground_problems({}.get, "Blitz", ok), ([], []))


class Kinds(unittest.TestCase):
    """What each scenario is, from the game's map list and menus: a map-list entry loads a scenario through its
    cluster (ClusterLoads -> TNDFTransaction.BaseName -> that ClusterMap's ScenarioPath); the menus list the entry as
    a multiplayer map, a campaign chapter or a challenge (an Operation)."""

    def glad(self):
        from fixtures import make_edat, make_ndf
        from rusemod.dic import name_to_key
        bs = chr(92)

        def s(i):
            return val(0x07, struct.pack("<I", i))

        def ref(i, cls):
            return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))

        def mapv(*pairs):
            return val(0x12, struct.pack("<I", len(pairs)) + b"".join(k + v for k, v in pairs))

        guid_a, guid_b, guid_c = bytes(range(16)), bytes(range(16, 32)), bytes(range(32, 48))
        # three entries on Blitz: a skirmish (menus: multiplayer), an Operation (menus: challenge), a test (no menu)
        mapinfo = make_ndf(
            objects=[(0, [(0, s(0)), (1, s(1)), (2, val(0x1A, guid_a)), (3, mapv((s(2), ref(3, 1))))]),
                     (0, [(0, s(3)), (1, s(1)), (2, val(0x1A, guid_b)), (3, mapv((s(2), ref(4, 1))))]),
                     (0, [(0, s(4)), (1, s(1)), (2, val(0x1A, guid_c)), (3, mapv((s(2), ref(5, 1))))]),
                     (1, [(4, ref(6, 2))]), (1, [(4, ref(7, 2))]), (1, [(4, ref(8, 2))]),
                     (2, [(5, s(5))]), (2, [(5, s(6))]), (2, [(5, s(7))])],
            classes=["TMapLoadInfo", "TClusterWithNDFLoadedSubCluster", "TNDFTransaction"],
            props=[("Name", 0), ("RootDatapackName", 0), ("GUID", 0), ("ClusterLoads", 0), ("NdfTransaction", 1),
                   ("BaseName", 2)],
            strings=["(2) Blitz", "Blitz", "Std", "Challenge - Blitz", "Tech: Test IA",
                     bs.join(["Patchable", "Scenario", "Blitz", "Scenario", "ClusterMap"]),
                     bs.join(["Patchable", "Scenario", "Blitz", "Scenario_Challenge", "ClusterMap"]),
                     bs.join(["Patchable", "Scenario", "Blitz", "Scenario_TestIA", "ClusterMap"])])
        globals_ = make_ndf(
            objects=[(0, [(0, val(0x1A, guid_a)), (1, val(0x1D, struct.pack("<Q", name_to_key("BLITZ"))))]),
                     (1, [(0, val(0x1A, guid_b)), (1, val(0x1D, struct.pack("<Q", name_to_key("ANZIO"))))])],
            classes=["TMultiMapInfo", "TChallengeMapInfo"], props=[("GUID", 0), ("Description", 0)])

        def cluster(file):
            return make_ndf(objects=[(0, [(0, s(0))])], classes=["TScenarioPath"], props=[("ScenarioPath", 0)],
                            strings=["DataDir:" + bs + "Test" + bs + "Map" + bs + "Blitz/" + file])
        scen = [("dir", folder + bs, [("file", "clustermap.cpp.gladndfbin", cluster(f))])
                for folder, f in (("scenario", "LevelDesign_Normal.scenario"),
                                  ("scenario_challenge", "LevelDesign_Challenge.scenario"),
                                  ("scenario_testia", "LevelDesign_TestIA.scenario"))]
        return Edat(make_edat([("dir", "genglad" + bs + "patchable" + bs, [
            ("file", "mapinfo.cpp.gladndfbin", mapinfo),
            ("dir", "misc" + bs, [("file", "globals.cpp.gladndfbin", globals_)]),
            ("dir", "scenario" + bs + "blitz" + bs, scen)])]))

    def test_each_scenario_gets_its_kind_and_entries(self):
        from rusemod.dic import name_to_key
        from rusemod.scenario import kinds_of
        k = kinds_of(self.glad(), "Blitz")
        self.assertEqual({f: [(e["name"], e["kind"]) for e in es] for f, es in k.items()},
                         {"leveldesign_normal.scenario": [("(2) Blitz", "skirmish")],
                          "leveldesign_challenge.scenario": [("Challenge - Blitz", "operation")],
                          "leveldesign_testia.scenario": [("Tech: Test IA", "test")]})
        self.assertEqual(k["leveldesign_challenge.scenario"][0]["key"], name_to_key("ANZIO"))
        self.assertEqual(kinds_of(self.glad(), "OtherMap"), {})


class ForTheMapView(unittest.TestCase):
    def test_folders_and_the_view(self):
        from rusemod.scenario import folder_of, of_map, view
        self.assertEqual(folder_of("SuperCrossRoads4"), "test/map/supercrossroads4/".replace("/", "\\"))
        self.assertEqual(folder_of("Flat_France"), "test/map/flat/france/".replace("/", "\\"))
        v = view(Scenario.read(scenario()))
        self.assertEqual([z["name"] for z in v["zones"]], ["zone_a", "zone_b"])
        self.assertEqual(v["zones"][0]["points"][:4], [0.0, 0.0, 1000.0, 0.0])
        self.assertEqual(v["zones"][0]["triangles"], [0, 1, 2, 0, 2, 3])
        start, spawn = v["items"]
        self.assertEqual((start["kind"], start["alliance"], start["name"]), ("StartingPoint", 2, "HQ_Allies"))
        self.assertEqual((spawn["kind"], spawn["what"]), ("Spawn", "Unit_M4_Sherman"))

        class Entry:
            def __init__(self, path):
                self.path = path

        files = {p.replace("/", "\\"): data for p, data in (
            ("test/map/blitz/leveldesign.scenario", scenario()), ("test/map/blitz/bad.scenario", b"junk"),
            ("test/map/blitz/sub/leveldesign.scenario", scenario()), ("test/map/other/leveldesign.scenario", scenario()))}

        class Arc:
            entries = [Entry(p) for p in files]

            @staticmethod
            def read(e):
                return files[e.path]

        self.assertEqual(list(of_map(Arc, "Blitz")), ["leveldesign.scenario"])  # not the bad one, the sub folder or others


if __name__ == "__main__":
    unittest.main()
