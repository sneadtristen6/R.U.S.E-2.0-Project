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
    """One starting point (alliance 2, turned 1.5 radians) and one spawn with a unit class, as TGameDesignItems."""
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
                 (2, [(5, s(1))])],
        classes=["TGameDesignItem", "TGameDesignAddOn_StartingPoint", "TGameDesignAddOn_Spawn"],
        props=[("Position", 0), ("Rotation", 0), ("AddOn", 0), ("AllianceNum", 1), ("Name", 1),
               ("PythonClassName", 2)],
        strings=["HQ_Allies", "front.parametres.Classes.Unit_M4_Sherman"])


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
        self.assertEqual(data, scenario())
        size = struct.unpack_from("<I", data, len(data) - len(s.ndf_raw) - 4)[0]
        self.assertEqual(size % 4, 0)
        s.move(0, 1.0, 2.0)
        self.assertEqual(len(s.to_bytes()) % 4, len(data) % 4)

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
