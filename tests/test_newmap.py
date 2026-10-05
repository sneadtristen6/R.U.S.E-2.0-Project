"""New maps (rusemod.newmap, maps/<NewName>/map.toml copy_of): a shipped map copied under a name of its own, on a
made-up game laid out like the real one: Blitz (SuperCrossRoads4) with its map-list entry, BATTLES entry, scenario
cluster, map cluster, constants, scenario, grid, menu texts and pack, and a campaign map BATTLES doesn't list."""
import struct
import tempfile
import tomllib
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_build import PACK, write_mod
from test_dic import make_dic
from rusemod import loc
from rusemod.build import BuildError, build_and_write, load_mod
from rusemod.dic import Dic, name_to_key
from rusemod.edat import Edat
from rusemod.ndf import Ndf, local_ref, sub_values
from rusemod.newmap import (Grown, NewMap, NewMapError, NewPack, check_name, guid_for, make, map_toml, menu_entries,
                            parse)
from rusemod.players import GLOBALS, MAPINFO, entries, skirmish_files

BS = chr(92)
GUID_BLITZ, GUID_OTHER, GUID_LEIPZIG = bytes(range(16)), bytes(range(16, 32)), bytes(range(32, 48))
PACK_ID = bytes(range(100, 116))
SCENARIO_CLUSTER = BS.join(["genglad", "patchable", "scenario", "supercrossroads4", "scenario", "clustermap.cpp.gladndfbin"])
MAP_CLUSTER = BS.join(["genglad", "patchable", "map", "supercrossroads4", "clustermap.cpp.gladndfbin"])
CONSTANTS = BS.join(["genglad", "patchable", "map", "supercrossroads4", "mapconstante.cpp.gladndfbin"])
SCENARIO = BS.join(["test", "map", "supercrossroads4", "leveldesign_normal.scenario"])
GRID = BS.join(["datasmap", "supercrossroads4", "mapinfo.win"])


def p(i):
    return val(0x1C, struct.pack("<I", i))


def s(i):
    return val(0x07, struct.pack("<I", i))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def i32(v):
    return val(0x02, struct.pack("<i", v))


def yes():
    return val(0x00, b"\x01")


def key(name):
    return val(0x1D, struct.pack("<Q", name_to_key(name)))


def glad_files() -> dict:
    """The made-up game's map registration in ZZ_GladPatchableWin.dat, laid out like Blitz's."""
    mapinfo = make_ndf(
        objects=[(0, [(0, s(0)), (1, p(1)), (2, s(1)), (3, val(0x1A, GUID_BLITZ)),
                      (4, val(0x12, struct.pack("<I", 1) + s(8) + ref(1, 1))), (5, ref(3, 3)), (10, ref(7, 3))]),
                 (1, [(6, ref(2, 2))]),
                 (2, [(7, p(2)), (8, p(3))]),
                 (3, [(9, p(4))]),
                 (0, [(0, s(5)), (2, s(6)), (3, val(0x1A, GUID_LEIPZIG)),
                      (4, val(0x12, struct.pack("<I", 1) + s(8) + ref(5, 1)))]),
                 (1, [(6, ref(6, 2))]),
                 (2, [(7, p(7))]),
                 (3, [(9, p(9))])],
        classes=["TMapLoadInfo", "TClusterWithNDFLoadedSubCluster", "TNDFTransaction", "TUIResourceTexture"],
        props=[("Name", 0), ("Path", 0), ("RootDatapackName", 0), ("GUID", 0), ("ClusterLoads", 0), ("Icone", 0),
               ("NdfTransaction", 1), ("BaseName", 2), ("OutputFileName", 2), ("FileName", 3), ("Icone2", 0)],
        strings=["(2) Blitz", "SuperCrossRoads4", BS.join(["Patchable", "Scenario", "SuperCrossRoads4", "Scenario", "ClusterMap"]),
                 BS.join(["map", "SuperCrossRoads4", "Scenario", "ClusterMap.ndfbin"]),
                 "DataDir:" + BS + BS.join(["Test", "map", "SuperCrossRoads4", "Minimap.png"]), "01. Leipzig", "M01_Leipzig",
                 BS.join(["Patchable", "Scenario", "M01_Leipzig", "Scenario", "ClusterMap"]), "Std",
                 "DataDir:" + BS + BS.join(["Test", "map", "SuperCrossRoads4", "Minimap2.png"])],
        topo=[0, 4], compress=True)
    globals_ = make_ndf(
        objects=[(0, [(0, key("M_D_01")), (1, val(0x1A, GUID_BLITZ)), (2, s(0)), (3, i32(2)), (4, i32(1)), (5, yes()),
                      (6, yes())]),
                 (0, [(0, key("M_D_08")), (1, val(0x1A, GUID_OTHER)), (2, s(1)), (3, i32(4)), (6, yes()), (7, i32(1))]),
                 (1, [(8, val(0x11, struct.pack("<I", 2) + ref(0, 0) + ref(1, 0)))])],
        classes=["TMultiMapInfo", "TMultiPack"],
        props=[("Description", 0), ("GUID", 0), ("TrackingId", 0), ("NbPlayers", 0), ("GameType", 0),
               ("DispoLadder1v1", 0), ("DispoMulti2Teams", 0), ("CategoryId", 0), ("MultiList", 1)],
        strings=["MP01", "MP31"], topo=[2], compress=True)
    scenario_cluster = make_ndf(
        objects=[(0, [(0, p(0))]), (1, [(1, p(1))]), (2, [(2, p(2)), (3, p(3)), (4, s(4))]), (3, [(5, p(5))]),
                 (2, [(2, p(6))])],
        classes=["TEugBString", "TScenarioLoader", "TNDFTransaction", "TResourceDescriptorSoundPack"],
        props=[("Value", 0), ("FileName", 1), ("BaseName", 2), ("OutputFileName", 2), ("NameSpace", 2), ("PackName", 3)],
        strings=["DataDir:" + BS + BS.join(["Test", "Map", "SuperCrossroads4/LevelDesign_Normal.scenario"]),
                 "DataDir:" + BS + BS.join(["Test", "map", "SuperCrossRoads4", "LevelDesign_Normal.scenario"]),
                 BS.join(["Patchable", "map", "SuperCrossRoads4", "ClusterMap"]),
                 BS.join(["map", "SuperCrossRoads4", "ClusterMap.ndfbin"]), "ClusterTerrain",
                 BS.join(["Pack", "map", "SuperCrossroads4Dialogues.mpk"]),
                 BS.join(["Patchable", "Scenario", "SuperCrossRoads4", "Scenario", "MapIA"])],
        compress=True)
    map_cluster = make_ndf(
        objects=[(0, [(0, p(0)), (1, s(1)), (2, s(2))]), (1, [(3, p(3)), (4, p(4))]), (1, [(3, p(5))])],
        classes=["TClusterMountMapDataPack", "TNDFTransaction"],
        props=[("DataPack", 0), ("DatasMapDirectory", 0), ("MountingPoint", 0), ("BaseName", 1), ("OutputFileName", 1)],
        strings=["MapDat:" + BS + "DataMapSuperCrossroads4_v09.dat", "GenDatasmap/SuperCrossroads4", "Datasmap",
                 BS.join(["Patchable", "map", "SuperCrossRoads4", "MapConstante"]),
                 BS.join(["map", "SuperCrossRoads4", "MapConstante.ndfbin"]),
                 BS.join(["Patchable", "map", "SuperCrossRoads4", "HQLoader"])],
        compress=True)
    constants = make_ndf(
        objects=[(0, [(0, p(0))]), (1, [(1, p(1))])], classes=["TCurrentMapInfo", "TResourceTextureCube"],
        props=[("MapPath", 0), ("FileName", 1)],
        strings=["DataDir:" + BS + BS.join(["datasmap", "SuperCrossRoads4"]),
                 "DataDir:" + BS + BS.join(["datasmap", "SuperCrossRoads4", "envmap", "ENV.cube"])],
        compress=True)
    return {MAPINFO: mapinfo, GLOBALS: globals_, SCENARIO_CLUSTER: scenario_cluster, MAP_CLUSTER: map_cluster,
            CONSTANTS: constants}


def data_files() -> dict:
    from test_scenario import mapinfo, scenario
    return {SCENARIO: scenario(), GRID: mapinfo()}


def text_files() -> dict:
    return {loc.member("flash_txt", lang): make_dic([(name_to_key("M_D_01"), text), (name_to_key("M_D_08"), "Other")])
            for lang, text in (("us", "Blitz"), ("fr", "Blitz"), ("dev", "Super crossroads"))}


def reader(files):
    low = {k.lower(): v for k, v in files.items()}
    return lambda member: low.get(member.replace("/", BS).lower())


def props(nd, o):
    return {nd.prop_name(pi): v for pi, v in o.props}


def text(nd, v):
    return nd.strings[struct.unpack("<I", v.payload[:4])[0]]


def made(name="BlitzAtDusk", spec=None, glad=None, data=None, texts=None):
    return make(name, spec or NewMap("SuperCrossRoads4", {"us": "Blitz at Dusk", "fr": "Blitz au crépuscule"}),
                reader(glad or glad_files()), reader(data or data_files()), reader(texts or text_files()))


class TheFile(unittest.TestCase):
    def test_map_toml(self):
        self.assertEqual(parse({"copy_of": "SuperCrossRoads4", "name": "Blitz at Dusk"}, folder="BlitzAtDusk"),
                         [NewMap("SuperCrossRoads4", {"us": "Blitz at Dusk"})])
        self.assertEqual(parse({"copy_of": "SuperCrossRoads4"}, folder="BlitzAtDusk"),  # no name: the folder's
                         [NewMap("SuperCrossRoads4", {"us": "BlitzAtDusk"})])
        self.assertEqual(parse({"copy_of": "M04_Cotentin", "name": {"en": "Omaha", "de": "Omaha (de)", "fr": " "},
                                "entry": "(6) Cotentin (3v3)"}),
                         [NewMap("M04_Cotentin", {"us": "Omaha", "ger": "Omaha (de)"}, "(6) Cotentin (3v3)")])
        self.assertEqual(parse({"players": 4}), [])
        for bad, why in (({"name": "x"}, "name is for a new map"), ({"copy_of": "Super Cross"}, "pack name"),
                         ({"copy_of": 4}, "pack name"), ({"copy_of": "blitzatdusk"}, "copy of itself"),
                         ({"copy_of": "A", "name": {"xx": "y", "us": "z"}}, "isn't a language"),
                         ({"copy_of": "A", "name": {"fr": "y"}}, "needs us"), ({"copy_of": "A", "name": 5}, "must be text"),
                         ({"copy_of": "A", "name": "x" * 61}, "the menus take 60"),
                         ({"copy_of": "A", "name": "a\tb"}, "control character"), ({"copy_of": "A", "name": ""}, "needs a name"),
                         ({"copy_of": "A", "entry": " "}, "map-list name")):
            with self.subTest(bad=bad), self.assertRaisesRegex(NewMapError, why):
                parse(bad, "maps/BlitzAtDusk/map.toml", "BlitzAtDusk")

    def test_the_studio_writes_what_the_build_reads(self):
        for spec, players in ((NewMap("SuperCrossRoads4", {"us": 'Blitz "at" Dusk'}), None),
                              (NewMap("M04_Cotentin", {"us": "Omaha", "fr": "Omaha (fr)"}, "(6) Cotentin (3v3)"), 8)):
            data = tomllib.loads(map_toml(spec, players, header="made by the Studio"))
            self.assertEqual(parse(data, folder="Omaha2"), [spec])
            self.assertEqual(data.get("players"), players)

    def test_names(self):
        check_name("BlitzAtDusk")
        check_name("B" + "x" * 39)
        for bad in ("Blitz at Dusk", "9Lives", "", "B" + "x" * 40, "Flat_Mine", "Blitz-2"):
            with self.subTest(bad=bad), self.assertRaises(NewMapError):
                check_name(bad)

    def test_ids_come_from_the_name(self):
        a = guid_for("BlitzAtDusk", "pack")
        self.assertEqual(a, guid_for("blitzatdusk", "pack"))           # the same on every PC, whatever the case
        self.assertNotEqual(a, guid_for("BlitzAtDusk", "entry"))
        self.assertNotEqual(a, guid_for("BlitzAtNoon", "pack"))
        import uuid
        u = uuid.UUID(bytes_le=a)
        self.assertEqual((u.version, u.variant), (4, uuid.RFC_4122))   # shaped like the shipped packs' ids


class Making(unittest.TestCase):
    def setUp(self):
        self.glad = glad_files()
        self.c = made(glad=self.glad)

    def test_the_new_files(self):
        c = self.c
        self.assertEqual(sorted(c.glad), [BS.join(["genglad", "patchable", "map", "blitzatdusk", n])
                                          for n in ("clustermap.cpp.gladndfbin", "mapconstante.cpp.gladndfbin")]
                         + [BS.join(["genglad", "patchable", "scenario", "blitzatdusk", "scenario", "clustermap.cpp.gladndfbin"])])
        self.assertEqual(c.data, {BS.join(["test", "map", "blitzatdusk", "leveldesign_normal.scenario"]): data_files()[SCENARIO],
                                  BS.join(["datasmap", "blitzatdusk", "mapinfo.win"]): data_files()[GRID]})
        self.assertEqual((c.scenario, c.map_folder, c.pack_from, c.key), ("leveldesign_normal.scenario", "SuperCrossRoads4",
                                                                          "DataMapSuperCrossroads4_v09.dat", "M_D_31"))
        self.assertEqual(c.pack_id, guid_for("BlitzAtDusk", "pack"))

    def test_the_scenario_cluster_names_the_new_scenario_and_map(self):
        nd = Ndf(self.c.glad[BS.join(["genglad", "patchable", "scenario", "blitzatdusk", "scenario", "clustermap.cpp.gladndfbin"])])
        self.assertEqual(nd.strings, [
            "DataDir:" + BS + BS.join(["Test", "Map", "BlitzAtDusk/LevelDesign_Normal.scenario"]),
            "DataDir:" + BS + BS.join(["Test", "map", "BlitzAtDusk", "LevelDesign_Normal.scenario"]),
            BS.join(["Patchable", "map", "BlitzAtDusk", "ClusterMap"]), BS.join(["map", "BlitzAtDusk", "ClusterMap.ndfbin"]),
            "ClusterTerrain", BS.join(["Pack", "map", "SuperCrossroads4Dialogues.mpk"]),       # the shipped map's sounds
            BS.join(["Patchable", "Scenario", "SuperCrossRoads4", "Scenario", "MapIA"])])     # and camera paths
        self.assertTrue(nd.flags & 0x80)  # compressed, as shipped

    def test_the_map_cluster_mounts_the_new_pack_and_loads_the_new_constants(self):
        nd = Ndf(self.c.glad[BS.join(["genglad", "patchable", "map", "blitzatdusk", "clustermap.cpp.gladndfbin"])])
        mount = props(nd, nd.objects[0])
        self.assertEqual(text(nd, mount["DataPack"]), "MapDat:" + BS + "DataMapBlitzAtDusk_v09.dat")
        self.assertEqual(text(nd, mount["DatasMapDirectory"]), "GenDatasmap/SuperCrossroads4")  # (not what mounts it)
        self.assertEqual([text(nd, v) for o in nd.objects[1:] for _pi, v in o.props],
                         [BS.join(["Patchable", "map", "BlitzAtDusk", "MapConstante"]),
                          BS.join(["map", "BlitzAtDusk", "MapConstante.ndfbin"]),
                          BS.join(["Patchable", "map", "SuperCrossRoads4", "HQLoader"])])       # the rest: the shipped map's

    def test_the_constants_name_the_new_grid(self):
        nd = Ndf(self.c.glad[BS.join(["genglad", "patchable", "map", "blitzatdusk", "mapconstante.cpp.gladndfbin"])])
        self.assertEqual(text(nd, props(nd, nd.objects[0])["MapPath"]), "DataDir:" + BS + BS.join(["datasmap", "BlitzAtDusk"]))
        self.assertEqual(text(nd, props(nd, nd.objects[1])["FileName"]),
                         "DataDir:" + BS + BS.join(["datasmap", "SuperCrossRoads4", "envmap", "ENV.cube"]))

    def test_the_map_list_and_battles(self):
        c = self.c
        m, g = Ndf(c.glad_changed[MAPINFO]), Ndf(c.glad_changed[GLOBALS])
        [(mi, gi, name)] = entries(m, g, "BlitzAtDusk")
        self.assertEqual(name, "(2) Blitz at Dusk")
        self.assertEqual(c.entry_name, name)
        self.assertEqual(m.topo, [0, 4, mi])                       # a top object, like every map-list entry
        load = props(m, m.objects[mi])
        self.assertEqual((text(m, load["Path"]), text(m, load["RootDatapackName"]), bytes(load["GUID"].payload)),
                         ("BlitzAtDusk", "BlitzAtDusk", guid_for("BlitzAtDusk", "entry")))
        icon = props(m, m.objects[local_ref(load["Icone"])])
        self.assertEqual(text(m, icon["FileName"]), "DataDir:" + BS + BS.join(["Test", "map", "SuperCrossRoads4", "Minimap.png"]))
        read = reader({**self.glad, **c.glad_changed, **c.glad})
        self.assertEqual(skirmish_files(read, "BlitzAtDusk"), {"leveldesign_normal.scenario"})
        self.assertEqual(skirmish_files(read, "SuperCrossRoads4"), {"leveldesign_normal.scenario"})
        old = props(m, m.objects[0])                               # the shipped entry as it was
        self.assertEqual((text(m, old["Name"]), text(m, old["Path"]), bytes(old["GUID"].payload)),
                         ("(2) Blitz", "SuperCrossRoads4", GUID_BLITZ))
        multi = props(g, g.objects[gi])
        self.assertEqual(struct.unpack("<Q", multi["Description"].payload)[0], name_to_key("M_D_31"))
        self.assertEqual(text(g, multi["TrackingId"]), "MP32")    # MP31 is taken
        self.assertEqual(multi["NbPlayers"].scalar(), 2)
        self.assertNotIn("DispoLadder1v1", multi)                   # ranked play stays the shipped map's
        self.assertNotIn(gi, g.topo)                                # reached through its pack only
        pack = props(g, g.objects[2])["MultiList"]
        self.assertEqual([local_ref(x) for x in sub_values(pack)], [0, gi, 1])  # after the 2-player maps

    def test_its_name_in_every_language(self):
        texts = {member: Dic(raw) for member, raw in self.c.texts.items()}
        self.assertEqual({m: d.text(name_to_key("M_D_31")) for m, d in texts.items()},
                         {loc.member("flash_txt", "us"): "Blitz at Dusk", loc.member("flash_txt", "fr"): "Blitz au crépuscule",
                          loc.member("flash_txt", "dev"): "Blitz at Dusk"})
        self.assertIn("Blitz at Dusk", self.c.notes[0])

    def test_a_second_map_gets_the_next_ids(self):
        c = self.c
        second = made("BlitzAtNoon", NewMap("SuperCrossRoads4", {"us": "Blitz at Noon"}),
                      {**self.glad, **c.glad_changed, **c.glad}, texts={**text_files(), **c.texts})
        self.assertEqual(second.key, "M_D_32")
        g = Ndf(second.glad_changed[GLOBALS])
        self.assertEqual(sorted(text(g, props(g, o)["TrackingId"]) for o in g.objects if "TrackingId" in props(g, o)),
                         ["MP01", "MP31", "MP32", "MP33"])
        with self.assertRaisesRegex(NewMapError, "already has a map called BlitzAtDusk"):
            made(glad={**self.glad, **c.glad_changed, **c.glad})

    def test_its_own_menu_picture(self):
        """map.toml picture: the copy's record names menu pictures of its own (its own copy of the shipped picture's
        record), made from the PNG and added to ZZ_Win.dat; the shipped record keeps its picture."""
        from rusemod.dxt import png_bytes
        from rusemod.tmst import Tgv
        spec = NewMap("SuperCrossRoads4", {"us": "Blitz at Dusk"}, picture="menu.png")
        spec.picture_data = png_bytes(bytes((10, 40, 200, 255)) * 16, 4, 4, channels=4)
        c = made(spec=spec, glad=self.glad)
        self.assertEqual(sorted(c.zz_new), [BS.join(["gen", "test", "map", "blitzatdusk", n])   # (the wide one from
                                            for n in ("minimap.tgv", "minimap2.tgv")])             # it too)
        self.assertEqual((Tgv(c.zz_new[BS.join(["gen", "test", "map", "blitzatdusk", "minimap.tgv"])]).width), 640)
        self.assertEqual((Tgv(c.zz_new[BS.join(["gen", "test", "map", "blitzatdusk", "minimap2.tgv"])]).width), 680)
        m = Ndf(c.glad_changed[MAPINFO])
        loads = [o for o in m.objects if m.classes[o.cls] == "TMapLoadInfo"]
        shipped, copy = loads[0], loads[-1]
        pics = [text(m, props(m, m.objects[local_ref(props(m, o)["Icone"])])["FileName"]) for o in (shipped, copy)]
        self.assertEqual(pics, ["DataDir:" + BS + BS.join(["Test", "map", "SuperCrossRoads4", "Minimap.png"]),
                                "DataDir:" + BS + BS.join(["Test", "map", "BlitzAtDusk", "Minimap.png"])])
        self.assertEqual(made(glad=self.glad).zz_new, {})            # no picture: the shipped one, as before
        self.assertEqual(parse({"copy_of": "SuperCrossRoads4", "picture": "menu.png"}, folder="BlitzAtDusk")[0].picture,
                         "menu.png")
        self.assertIn('picture = "menu.png"', map_toml(spec))
        for bad in ("menu.jpg", "../menu.png", 5, "a\\b.png"):
            with self.subTest(bad=bad), self.assertRaisesRegex(NewMapError, "picture must name a PNG"):
                parse({"copy_of": "SuperCrossRoads4", "picture": bad}, folder="BlitzAtDusk")

    def test_its_own_wide_picture_alone(self):
        """map.toml wide_picture: only the wide one (the 3D map) is the copy's own; its big one stays the shipped
        map's picture file, which the copy's record still names."""
        from rusemod.dxt import png_bytes
        spec = NewMap("SuperCrossRoads4", {"us": "Blitz at Dusk"}, wide_picture="wide.png", start_dots=True)
        spec.wide_picture_data = png_bytes(bytes((10, 140, 20, 255)) * 16, 4, 4, channels=4)
        c = made(spec=spec, glad=self.glad)
        self.assertEqual(sorted(c.zz_new), [BS.join(["gen", "test", "map", "blitzatdusk", "minimap2.tgv"])])
        m = Ndf(c.glad_changed[MAPINFO])
        copy = props(m, [o for o in m.objects if m.classes[o.cls] == "TMapLoadInfo"][-1])
        self.assertEqual([text(m, props(m, m.objects[local_ref(copy[k])])["FileName"]) for k in ("Icone", "Icone2")],
                         ["DataDir:" + BS + BS.join(["Test", "map", "SuperCrossRoads4", "Minimap.png"]),
                          "DataDir:" + BS + BS.join(["Test", "map", "BlitzAtDusk", "Minimap2.png"])])
        text_ = map_toml(spec)
        self.assertIn('wide_picture = "wide.png"', text_)
        self.assertIn("start_dots = true", text_)
        back = parse(tomllib.loads(text_), folder="BlitzAtDusk")[0]
        self.assertEqual((back.picture, back.wide_picture, back.start_dots), (None, "wide.png", True))
        with self.assertRaisesRegex(NewMapError, "start_dots puts the starting points on the map's own wide picture"):
            parse({"copy_of": "SuperCrossRoads4", "start_dots": True}, folder="BlitzAtDusk")

    def test_its_own_zone_map(self):
        """The scenario's MapIA names its zone map: the copy gets its own of both (rusemod.sectors can then make its
        sectors again), and its cluster loads its own MapIA; without a MapIA, everything as before."""
        glad = dict(self.glad)
        zone = "DataDir:" + BS + BS.join(["Test", "map", "SuperCrossRoads4", "ZoneBluff", "LevelDesign_Normal.Kdt"])
        cam = "DataDir:" + BS + BS.join(["Test", "Map", "SuperCrossRoads4", "CamPath", "CamPaths_Normal.ndfbin"])
        ia_member = BS.join(["genglad", "patchable", "scenario", "supercrossroads4", "scenario", "mapia.cpp.gladndfbin"])
        wide = zone.replace("map", "Map").encode("utf-16-le")   # D-Day's MapIA names its zone map twice
        glad[ia_member] = make_ndf(objects=[(0, [(0, p(0)), (1, p(1)), (2, val(0x08, struct.pack("<I", len(wide))
                                                                                + wide))])],
                                   classes=["TAreaManager"],
                                   props=[("StreamedMeshKdTreeFileName", 0), ("CamPath", 0), ("Name", 0)],
                                   strings=[zone, cam], compress=True)
        cluster = Ndf(glad[SCENARIO_CLUSTER])
        cluster.set_string(cluster.strings.index(BS.join(["Patchable", "Scenario", "SuperCrossRoads4", "Scenario",
                                                          "MapIA"])),
                           BS.join(["Patchable", "Scenario", "SuperCrossRoads4", "Scenario", "MapIA"]))
        data = dict(data_files())
        data[BS.join(["test", "map", "supercrossroads4", "zonebluff", "leveldesign_normal.kdt"])] = b"ZONES"
        c = made(glad=glad, data=data)
        new_ia = BS.join(["genglad", "patchable", "scenario", "blitzatdusk", "scenario", "mapia.cpp.gladndfbin"])
        nd_ia = Ndf(c.glad[new_ia])
        self.assertEqual(nd_ia.strings, [
            "DataDir:" + BS + BS.join(["Test", "map", "BlitzAtDusk", "ZoneBluff", "LevelDesign_Normal.Kdt"]), cam])
        [w] = [bytes(v.payload[4:]).decode("utf-16-le") for o in nd_ia.objects for _pi, v in o.props if v.tc == 0x08]
        self.assertEqual(w, "DataDir:" + BS + BS.join(["Test", "Map", "BlitzAtDusk", "ZoneBluff",
                                                        "LevelDesign_Normal.Kdt"]))
        self.assertEqual(c.data[BS.join(["test", "map", "blitzatdusk", "zonebluff", "leveldesign_normal.kdt"])], b"ZONES")
        nd = Ndf(c.glad[BS.join(["genglad", "patchable", "scenario", "blitzatdusk", "scenario",
                                 "clustermap.cpp.gladndfbin"])])
        self.assertIn(BS.join(["Patchable", "Scenario", "BlitzAtDusk", "Scenario", "MapIA"]), nd.strings)
        self.assertEqual(Ndf(glad[ia_member]).strings, [zone, cam])               # the shipped one as it was
        no_zone = dict(data_files())                                               # its zone map missing: as before
        self.assertEqual(sorted(made(glad=glad, data=no_zone).data), sorted(self.c.data))

    def test_what_cant_be_copied(self):
        for name, spec, why in (
                ("BlitzAtDusk", NewMap("Nowhere", {"us": "x"}), "isn't a map of this game"),
                ("BlitzAtDusk", NewMap("M01_Leipzig", {"us": "x"}), "no menu offers M01_Leipzig"),
                ("BlitzAtDusk", NewMap("SuperCrossRoads4", {"us": "x"}, "(4) Blitz"), r"has no entry '\(4\) Blitz'"),
                ("SuperCrossroads4", NewMap("Alpha", {"us": "x"}), "already has a map called"),
                ("Flat_X", NewMap("SuperCrossRoads4", {"us": "x"}), "test maps")):
            with self.subTest(why=why), self.assertRaisesRegex(NewMapError, why):
                made(name, spec)
        no_grid = data_files()
        del no_grid[GRID]
        with self.assertRaisesRegex(NewMapError, r"grid \(mapinfo.win\).*is missing"):
            made(data=no_grid)
        with self.assertRaisesRegex(NewMapError, "menus' texts"):
            made(texts={"x": b""})


def menu_globals(entry_cls: str, pack_cls: str, list_prop: str, track: str, tuto: bool = False) -> bytes:
    """globals.cpp with Blitz's one menu entry in another menu: an Operation (TChallengeMapInfo in a TChallengePack's
    ChallengeList) or a campaign chapter (TChapterMapInfo in a TChapterPack's ChapterList); `tuto`: the tutorial's
    chapter pack (IsTuto)."""
    return make_ndf(
        objects=[(0, [(0, key("M_D_01")), (1, val(0x1A, GUID_BLITZ)), (2, s(0)), (3, i32(1))]),
                 (0, [(0, key("M_D_08")), (1, val(0x1A, GUID_OTHER)), (2, s(1)), (3, i32(1))]),
                 (1, [(4, val(0x11, struct.pack("<I", 2) + ref(0, 0) + ref(1, 0)))] + ([(5, yes())] if tuto else []))],
        classes=[entry_cls, pack_cls],
        props=[("Description", 0), ("GUID", 0), ("TrackingId", 0), ("CategoryId", 0), (list_prop, 1), ("IsTuto", 1)],
        strings=[track, "X99"], topo=[2], compress=True)


class OperationsAndChapters(unittest.TestCase):
    """A copy of an Operation or a campaign chapter: the same files as a BATTLES map's, and its entry in that menu,
    last in its pack's list, with a tracking id of its own."""

    def made_in(self, entry_cls, pack_cls, list_prop, track, entry="(2) Blitz", tuto=False):
        glad = glad_files()
        glad[GLOBALS] = menu_globals(entry_cls, pack_cls, list_prop, track, tuto)
        return made("AnzioTwin", NewMap("SuperCrossRoads4", {"us": "Anzio Twin"}, entry), glad=glad)

    def check(self, c, cls, list_prop, track, menu):
        g = Ndf(c.glad_changed[GLOBALS])
        [k] = [i for i, o in enumerate(g.objects) if g.classes[o.cls] == cls and "GUID" in props(g, o)
               and bytes(props(g, o)["GUID"].payload) == c.guid]
        p = props(g, g.objects[k])
        self.assertEqual(text(g, p["TrackingId"]), track)
        self.assertEqual(struct.unpack("<Q", p["Description"].payload)[0], name_to_key(c.key))
        listed = props(g, g.objects[2])[list_prop]
        self.assertEqual([local_ref(x) for x in sub_values(listed)], [0, 1, k])  # last: the shipped ones keep their order
        self.assertIn(f"listed in {menu} as 'Anzio Twin'", c.notes[0])
        m = Ndf(c.glad_changed[MAPINFO])
        self.assertEqual([(f[2], f[3]) for f in menu_entries(m, g, "AnzioTwin")], [("(2) Anzio Twin", c.kind)])

    def test_an_operation(self):
        c = self.made_in("TChallengeMapInfo", "TChallengePack", "ChallengeList", "CH26")
        self.assertEqual(c.kind, "operation")
        self.check(c, "TChallengeMapInfo", "ChallengeList", "CH40", "OPERATIONS")

    def test_a_campaign_chapter(self):
        c = self.made_in("TChapterMapInfo", "TChapterPack", "ChapterList", "M01")
        self.assertEqual(c.kind, "campaign")
        self.check(c, "TChapterMapInfo", "ChapterList", "M24", "the CAMPAIGN")

    def test_named_by_its_entry(self):
        with self.assertRaisesRegex(NewMapError, r"isn't in BATTLES; to copy one of its Operations.*'\(2\) Blitz'"):
            self.made_in("TChallengeMapInfo", "TChallengePack", "ChallengeList", "CH26", entry=None)

    def test_not_the_tutorial(self):
        with self.assertRaisesRegex(NewMapError, "no menu offers SuperCrossRoads4"):
            self.made_in("TChapterMapInfo", "TChapterPack", "ChapterList", "M01", tuto=True)


class ThePacks(unittest.TestCase):
    def test_grown_reads_and_writes_new_members(self):
        base = Edat(make_edat([("dir", "a" + BS, [("file", "x.bin", b"xx"), ("file", "y.bin", b"yy")])]))
        g = Grown(base, {"b/new.bin": b"new"})
        self.assertEqual(bytes(g.read(g.find("b" + BS + "new.bin"))), b"new")
        self.assertEqual(bytes(g.read(g.find("new.bin"))), b"new")             # by its end, like any member
        self.assertEqual(bytes(g.read(g.entry("A/X.BIN"))), b"xx")
        self.assertEqual(len(g.entries), 3)
        self.assertTrue(g.is_changed)
        with self.assertRaises(ValueError):
            g.add("a" + BS + "x.bin", b"")
        out = Edat(g.to_bytes({"a" + BS + "y.bin": b"YY", "b" + BS + "new.bin": b"NEW"}))  # a change to an added one
        self.assertEqual({e.path: bytes(out.read(e)) for e in out.entries},
                         {"a" + BS + "x.bin": b"xx", "a" + BS + "y.bin": b"YY", "b" + BS + "new.bin": b"NEW"})
        self.assertEqual(g.added_with({"b/new.bin": b"NEW"}), {"b" + BS + "new.bin": b"NEW"})

    def test_a_new_pack_is_the_shipped_one_with_an_id_of_its_own(self):
        raw = bytearray(make_edat([("dir", "output" + BS, [("file", "a.bin", b"aa")])]))
        raw[8:24] = PACK_ID
        base = Edat(bytes(raw))
        new = NewPack(base, guid_for("BlitzAtDusk", "pack"), "DataMapX_v09.dat")
        out = Edat(new.to_bytes({"output" + BS + "a.bin": b"AA"}))
        self.assertEqual(bytes(out.checksum), guid_for("BlitzAtDusk", "pack"))
        self.assertEqual(bytes(out.read(out.find("a.bin"))), b"AA")
        self.assertEqual(new.to_bytes()[24:], bytes(raw)[24:])                 # the rest as shipped
        self.assertEqual(bytes(new.read(new.find("a.bin"))), b"aa")


class Building(unittest.TestCase):
    """`ruse build` with a mod that makes a new map and edits it: everything lands in the modded copy, and the shipped
    map stays as it was."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.root = Path(self.tmp.name)
        self.game = root / "steamapps" / "common" / "R.U.S.E"
        rev = self.game / "Data" / "PC" / "190852"
        rev.mkdir(parents=True)
        (self.game / "Maps" / "PC").mkdir(parents=True)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        units = Edat(PACK)
        files = {e.path: bytes(units.read(e)) for e in units.entries}
        (rev / "ZZ_GladPatchableWin.dat").write_bytes(flat_pack({**files, **glad_files()}))
        (rev / "DataMap_Win.dat").write_bytes(flat_pack(data_files()))
        (rev / "ZZ_Win.dat").write_bytes(flat_pack(text_files()))
        self.map_pack = map_pack()
        (self.game / "Maps" / "PC" / "DataMapSuperCrossroads4_v09.dat").write_bytes(self.map_pack)
        (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')

    def tearDown(self):
        self.tmp.cleanup()

    def mod(self, mod_id, files, name="BlitzAtDusk"):
        folder = write_mod(self.root / "mods", mod_id, {})
        (folder / "maps" / name).mkdir(parents=True)
        for f, body in files.items():
            (folder / "maps" / name / f).write_text(body, encoding="utf-8")
        return folder

    def build(self, *folders, copy="copy"):
        lines = []
        result = build_and_write(self.game, [load_mod(f) for f in folders], instance=self.root / copy, say=lines.append)
        return result, lines

    def copy(self, *parts):
        return Edat((self.root / "copy").joinpath(*parts).read_bytes())

    def test_its_own_menu_picture_goes_into_zz_win(self):
        """map.toml picture: the PNG beside it is read with the mod and its menu picture lands in the copy's ZZ_Win.dat;
        a picture that isn't there stops the build, naming it."""
        from rusemod.dxt import png_bytes
        from rusemod.tmst import Tgv
        dusk = self.mod("dusk", {"map.toml": 'copy_of = "SuperCrossRoads4"\nname = "Blitz at Dusk"\npicture = "menu.png"\n'})
        (dusk / "maps" / "BlitzAtDusk" / "menu.png").write_bytes(png_bytes(bytes((10, 40, 200, 255)) * 64, 8, 8,
                                                                           channels=4))
        result, lines = self.build(dusk)
        self.assertEqual(result.errors, [], "\n".join(lines))
        zz = self.copy("Data", "PC", "190852", "ZZ_Win.dat")
        pic = Tgv(bytes(zz.read(zz.find(BS.join(["gen", "test", "map", "blitzatdusk", "minimap.tgv"])))))
        self.assertEqual((pic.width, pic.height, pic.format), (640, 360, "DXT5_LIN"))
        (dusk / "maps" / "BlitzAtDusk" / "menu.png").unlink()
        with self.assertRaisesRegex(BuildError, "has no such picture"):
            load_mod(dusk)

    def wide_at(self, member, u, v):
        """The copy's wide picture `member` in ZZ_Win.dat: the colour where map point (u, v) is drawn."""
        import zlib
        from rusemod.dxt import decode_rgba
        from rusemod.menudraw import to_picture
        from rusemod.tmst import Tgv
        zz = self.copy("Data", "PC", "190852", "ZZ_Win.dat")
        t = Tgv(bytes(zz.read(zz.find(member))))
        px = decode_rgba(zlib.decompressobj().decompress(t.payload(0)[8:]), t.width, t.height, "DXT5")
        x, y = (int(c) for c in to_picture(u, v))
        return tuple(px[(y * t.width + x) * 4:(y * t.width + x) * 4 + 3])

    def test_its_starting_points_on_its_3d_map_wherever_they_are(self):
        """map.toml start_dots: the build draws a white dot on the wide picture where each starting point is once the
        mod's edits are in: moved, its dot moves (the owner, 2026-10-05: "where that's actually the spawn point")."""
        from rusemod.menudraw import slab_png
        from rusemod.tms import Tms
        from test_terrain_edit import make_map
        x0, y0, _z0, x1, y1, _z1 = Tms(make_map()["output" + BS + "highdef.tms"]).bounds
        start = ((1000.0 - x0) / (x1 - x0), (2000.0 - y0) / (y1 - y0))   # the made-up scenario's starting point
        moved = (0.75, 0.6)
        wide = BS.join(["gen", "test", "map", "blitzatdusk", "minimap2.tgv"])
        for move, dot, empty in ((False, start, moved), (True, moved, start)):
            files = {"map.toml": 'copy_of = "SuperCrossRoads4"\nname = "Blitz at Dusk"\nwide_picture = "wide.png"\n'
                                 'start_dots = true\n'}
            if move:
                files["scenario.toml"] = ('[[move]]\nfile = "leveldesign_normal.scenario"\nitem = 0\n'
                                          f'kind = "StartingPoint"\nx = {x0 + moved[0] * (x1 - x0)}\n'
                                          f'y = {y0 + moved[1] * (y1 - y0)}\n')
            dusk = self.mod(f"dusk{int(move)}", files)
            (dusk / "maps" / "BlitzAtDusk" / "wide.png").write_bytes(slab_png("land"))
            result, lines = self.build(dusk, copy="copy")
            self.assertEqual(result.errors, [], "\n".join(lines))
            self.assertIn("menu pictures: BlitzAtDusk: 1 start dot(s) on its 3D map picture, where its starting points "
                          "are", lines)
            with self.subTest(move=move):
                self.assertGreaterEqual(min(self.wide_at(wide, *dot)), 235)
                self.assertLess(min(self.wide_at(wide, *empty)), 200)

    def test_a_shipped_maps_own_pictures(self):
        """map.toml picture with no copy_of: the picture files the shipped map's BATTLES entry shows are replaced in
        ZZ_Win.dat, the files themselves kept where they are (the entry still names them)."""
        from rusemod.dxt import png_bytes
        from rusemod.tmst import Tgv
        zz = self.game / "Data" / "PC" / "190852" / "ZZ_Win.dat"
        big, wide = (BS.join(["gen", "test", "map", "supercrossroads4", n]) for n in ("minimap.tgv", "minimap2.tgv"))
        zz.write_bytes(flat_pack({**text_files(), big: b"old big", wide: b"old wide"}))
        themed = self.mod("themed", {"map.toml": 'picture = "menu.png"\n'}, name="SuperCrossRoads4")
        (themed / "maps" / "SuperCrossRoads4" / "menu.png").write_bytes(
            png_bytes(bytes((200, 30, 30, 255)) * 64, 8, 8, channels=4))
        result, lines = self.build(themed)
        self.assertEqual(result.errors, [], "\n".join(lines))
        self.assertIn("menu pictures: SuperCrossRoads4, from themed (2 picture file(s))", lines)
        built = self.copy("Data", "PC", "190852", "ZZ_Win.dat")
        self.assertEqual([(Tgv(bytes(built.read(built.find(m)))).width) for m in (big, wide)], [640, 680])
        glad = self.copy("Data", "PC", "190852", "ZZ_GladPatchableWin.dat")
        self.assertEqual(bytes(glad.read(glad.entry(MAPINFO))), glad_files()[MAPINFO])   # the map list as shipped

    def test_a_new_map_and_its_edits_go_into_the_modded_copy(self):
        from rusemod.cover import member as grid_of
        from rusemod.scenario import Scenario
        from rusemod.terrain_edit import FILES
        dusk = self.mod("dusk", {
            "map.toml": 'copy_of = "SuperCrossRoads4"\n\n[name]\nus = "Blitz at Dusk"\nfr = "Blitz au crépuscule"\n',
            "terrain.toml": '[[stroke]]\nbrush = "hill"\nx = 1500.0\ny = 1500.0\nradius = 600.0\nheight = 400.0\n',
            "scenario.toml": '[[move]]\nfile = "leveldesign_normal.scenario"\nitem = 0\nkind = "StartingPoint"\n'
                             'x = 2000.0\ny = 2000.0\n',
            "movement.toml": '[[block]]\nx = 10000.0\ny = 2000.0\nradius = 1600.0\n'})
        result, lines = self.build(dusk)
        self.assertEqual(result.errors, [], "\n".join(lines))
        for line in ("new map: BlitzAtDusk, from dusk", "terrain: BlitzAtDusk, from dusk", "scenario: BlitzAtDusk, from dusk",
                     "movement: BlitzAtDusk, from dusk"):
            self.assertIn(line, lines)
        self.assertTrue(any(ln.startswith("new: DataMapBlitzAtDusk_v09.dat, a copy of DataMapSuperCrossroads4_v09.dat "
                                          "(4 file(s) changed: ") for ln in lines), lines)
        # the new pack: the shipped one's members, the hill on it, an id of its own; the shipped pack as it was
        new = self.copy("Maps", "PC", "DataMapBlitzAtDusk_v09.dat")
        shipped = Edat(self.map_pack)
        self.assertEqual(bytes(new.checksum), guid_for("BlitzAtDusk", "pack"))
        self.assertEqual(sorted(e.path for e in new.entries), sorted(e.path for e in shipped.entries))
        self.assertNotEqual(bytes(new.read(new.find(FILES["highdef"]))), bytes(shipped.read(shipped.find(FILES["highdef"]))))
        self.assertEqual(self.copy("Maps", "PC", "DataMapSuperCrossroads4_v09.dat").raw, self.map_pack)
        # the registration and clusters in ZZ_GladPatchableWin.dat
        glad = self.copy("Data", "PC", "190852", "ZZ_GladPatchableWin.dat")
        read = lambda m: bytes(glad.read(glad.entry(m))) if glad.entry(m) is not None else None  # noqa: E731
        m, g = Ndf(read(MAPINFO)), Ndf(read(GLOBALS))
        [(_mi, _gi, name)] = entries(m, g, "BlitzAtDusk")
        self.assertEqual(name, "(2) Blitz at Dusk")
        self.assertEqual(skirmish_files(read, "BlitzAtDusk"), {"leveldesign_normal.scenario"})
        self.assertEqual(read(MAP_CLUSTER), glad_files()[MAP_CLUSTER])          # the shipped map's, untouched
        # its scenario and grid in DataMap_Win.dat, edited; the shipped ones untouched
        data = self.copy("Data", "PC", "190852", "DataMap_Win.dat")
        new_scen = Scenario.read(bytes(data.read(data.entry(BS.join(["test", "map", "blitzatdusk", "leveldesign_normal.scenario"])))))
        self.assertEqual(new_scen.items[0].position[:2], (2000.0, 2000.0))
        self.assertEqual(bytes(data.read(data.entry(SCENARIO))), data_files()[SCENARIO])
        self.assertNotEqual(bytes(data.read(data.entry(grid_of("BlitzAtDusk")))), data_files()[GRID])
        self.assertEqual(bytes(data.read(data.entry(GRID))), data_files()[GRID])
        self.assertIn(BS.join(["datasmap", "blitzatdusk", "mapinfo.win"]), result.added["DataMap_Win.dat"])
        # its name in the menus
        zz = self.copy("Data", "PC", "190852", "ZZ_Win.dat")
        us = Dic(bytes(zz.read(zz.entry(loc.member("flash_txt", "us")))))
        fr = Dic(bytes(zz.read(zz.entry(loc.member("flash_txt", "fr")))))
        self.assertEqual((us.text(name_to_key("M_D_31")), fr.text(name_to_key("M_D_31"))), ("Blitz at Dusk", "Blitz au crépuscule"))
        # the game folder untouched
        self.assertFalse((self.game / "Maps" / "PC" / "DataMapBlitzAtDusk_v09.dat").exists())

    def test_a_new_map_alone_and_the_fingerprint(self):
        result, lines = self.build(self.mod("dusk", {  # (the shipped scenario seats team 2 only: a start for team 1)
            "map.toml": 'copy_of = "SuperCrossRoads4"\nname = "Blitz at Dusk"\nplayers = 2\n',
            "scenario.toml": '[[start]]\nfile = "leveldesign_normal.scenario"\nteam = 1\nx = 2000.0\ny = 2000.0\n'}))
        self.assertEqual(result.errors, [], "\n".join(lines))
        self.assertIn("new: DataMapBlitzAtDusk_v09.dat, a copy of DataMapSuperCrossroads4_v09.dat", lines)
        self.assertIn("players: BlitzAtDusk, from dusk", lines)
        new = self.copy("Maps", "PC", "DataMapBlitzAtDusk_v09.dat")
        self.assertEqual(new.raw[24:], self.map_pack[24:])
        other, lines2 = self.build(self.mod("noon", {"map.toml": 'copy_of = "SuperCrossRoads4"\nname = "Blitz at Noon"\n'},
                                            name="BlitzAtNoon"), copy="copy2")
        self.assertEqual(other.errors, [], "\n".join(lines2))
        self.assertNotEqual(result.fingerprint, other.fingerprint)   # another map list: another game

    def test_mistakes(self):
        a = self.mod("aaa", {"map.toml": 'copy_of = "SuperCrossRoads4"\n'})
        b = self.mod("bbb", {"map.toml": 'copy_of = "SuperCrossRoads4"\n'}, name="blitzatdusk")
        result, lines = self.build(a, b)
        self.assertIn("aaa and bbb both make a new map called blitzatdusk", result.errors[0].message)
        self.assertIn("Nothing was written.", lines)
        result, lines = self.build(self.mod("campaign", {"map.toml": 'copy_of = "M01_Leipzig"\n'}, name="Leipzig2"))
        self.assertIn("campaign: maps/Leipzig2: no menu offers M01_Leipzig", result.errors[0].message)
        self.assertFalse((self.root / "copy").exists())
        result, lines = self.build(self.mod("ghost", {"terrain.toml": '[[stroke]]\nbrush = "hill"\nx = 1.0\ny = 1.0\n'
                                                                      'radius = 600.0\nheight = 4.0\n'}, name="NoSuchMap"))
        self.assertIn("the map NoSuchMap isn't in this game", result.errors[0].message)
        with self.assertRaisesRegex(BuildError, "name is for a new map"):
            load_mod(self.mod("named", {"map.toml": 'name = "x"\n'}, name="Named"))


class TheModCheck(unittest.TestCase):
    def test_a_new_maps_folder_is_its_own_pack(self):
        """The mod check flags map folders no map has (a title for a pack, say); a new map's folder is its pack."""
        from unittest import mock
        from rusemod.modcheck import folder_problems
        with tempfile.TemporaryDirectory() as d:
            for name, body in (("BlitzAtDusk", 'copy_of = "SuperCrossRoads4"\n'), ("Blitz", 'copy_of = "SuperCrossRoads4"\n'),
                               ("Nowhere", "players = 4\n")):
                (Path(d) / "maps" / name).mkdir(parents=True)
                (Path(d) / "maps" / name / "map.toml").write_text(body, encoding="utf-8")
            maps = [{"pack": "SuperCrossRoads4", "titles": {"us": ["Blitz"]}}]
            with mock.patch("rusemod.modcheck.map_list", return_value=maps):
                self.assertEqual([p["file"] for p in folder_problems(Path(d), Path(d))], ["maps/Nowhere"])


def flat_pack(files: dict) -> bytes:
    """An EDAT holding `files` (full member paths) as top-level entries."""
    return make_edat([("file", path, data) for path, data in files.items()])


def map_pack() -> bytes:
    """The made-up map's pack (test_terrain_edit's ground), with its scenery and sight layer (their checksums as the
    game has them) and an id in its header, like a shipped map pack."""
    import hashlib
    from test_terrain_edit import make_map
    boobs = b"0.6" + bytes(13)
    body = struct.pack("<II", 2, 4) + b"sdb!"
    files = {**make_map(), "output" + BS + "save.boobspc": hashlib.md5(boobs).digest() + boobs,
             "output" + BS + "output.sdb": b"SDB\r\n" + hashlib.md5(b"SDB\r\n" + body).digest() + body}
    raw = bytearray(make_edat([("dir", "output" + BS, [("file", m.split(BS)[-1], d) for m, d in files.items()])]))
    raw[8:24] = PACK_ID
    return bytes(raw)


if __name__ == "__main__":
    unittest.main()
