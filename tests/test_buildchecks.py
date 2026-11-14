"""The build's checks of the owner's items 29, 31 and 32 (2026-11-13), through `ruse build` (build_and_write) on
made-up games laid out like the real one (no game files needed). This module asks only what a build says and writes,
so it runs on the code before these checks too: on e9a092c3 the warnings and the loaders below are missing.

- 31 and 32 (rusemod.missionplaces): "It should be warning on every version if there's an error", and for any mod whose
  map lacks places a mission needs, "use your best judgment". A campaign chapter whose map, as the set leaves it, lacks
  a zone that a units-in-zone condition on its start-up list watches stops about a second after it starts: any mod
  leaving one so is warned about, any version of it, a player's own too; a mod keeping the places, or not touching
  missions, isn't.
- 29: "Sets made only of .rmod mods skip the unit-model check: (A) run it; (B) warn only; (C) leave it." -> "A": a unit
  an .rmod mod gives to a nation whose matches don't load its model gets that model's nation's packs loaded in every
  skirmish, as a folder mod's unit does.

The made-up files (a compiled match script, a layout, the menus, a cluster) are also what tests/test_missionplaces.py
checks the reading on."""
import base64
import json
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod.build import build_and_write, load_mod
from rusemod.edat import Edat
from rusemod.pyscript import Code, Xyz, dump, write_xyz
from rusemod.scenario import MAGIC, with_checksum

BS = "\\"
REV = "Data/PC/190852"
GLAD, DATA, IA = "ZZ_GladPatchableWin.dat", "DataMap_Win.dat", "IA_Common.dat"
MAPINFO = "genglad\\patchable\\mapinfo.cpp.gladndfbin"
GLOBALS = "genglad\\patchable\\misc\\globals.cpp.gladndfbin"
CLUSTER = BS.join(["genglad", "patchable", "scenario", "m01_leipzig", "scenario", "clustermap.cpp.gladndfbin"])
OTHER_CLUSTER = BS.join(["genglad", "patchable", "scenario", "alpha", "scenario_bh", "clustermap.cpp.gladndfbin"])
LAYOUT = BS.join(["test", "map", "m01_leipzig", "leveldesign.scenario"])
SCRIPT = BS.join(["genpython", "1000", "test", "map", "m01_leipzig", "scripting", "effetmap.xyz"])
ELSEWHERE = BS.join(["genpython", "1000", "test", "map", "twoislands", "scripting_challenge", "effetmap.xyz"])
GUIDS = {name: bytes([k] * 16) for k, name in enumerate(("leipzig", "alpha", "battle", "tuto", "unlisted"), 1)}


# --- a match script, compiled as the game's are (Python 2.5's code object, marshalled, in an .xyz) ------------------
def compiled(statements) -> bytes:
    """`statements`: [(variable, callee "a.b.C", [positional values], {keyword: value})], a value being ("const", x),
    ("name", variable), ("list", [values]) or ("call", callee, [values], {keyword: value})."""
    names, consts, code = [], [], bytearray()

    def at(table, v):
        if v not in table:
            table.append(v)
        return table.index(v)

    def op(o, arg=None):
        code.append(o)
        if arg is not None:
            code.extend(struct.pack("<H", arg))

    def push(v):
        if v[0] == "const":
            op(100, at(consts, v[1]))                         # LOAD_CONST
        elif v[0] == "name":
            op(101, at(names, v[1].encode()))                 # LOAD_NAME
        elif v[0] == "list":
            for x in v[1]:
                push(x)
            op(103, len(v[1]))                                # BUILD_LIST
        else:
            call(*v[1:])

    def call(callee, args=(), kwargs=None):
        first, *rest = callee.split(".")
        op(101, at(names, first.encode()))
        for part in rest:
            op(105, at(names, part.encode()))                 # LOAD_ATTR
        for a in args:
            push(a)
        for k, v in (kwargs or {}).items():
            op(100, at(consts, k.encode()))
            push(v)
        op(131, len(args) | len(kwargs or {}) << 8)           # CALL_FUNCTION
    for var, callee, args, kwargs in statements:
        call(callee, args, kwargs)
        op(90, at(names, var.encode()))                       # STORE_NAME
    op(100, at(consts, None))
    op(83)                                                    # RETURN_VALUE
    module = Code(0, 0, 16, 0x40, bytes(code), tuple(consts), tuple(names), (), (), (), b"effetmap.py", b"<module>",
                  1, b"")
    return write_xyz(Xyz(bytes(16), dump(module)))


TAG = "leveldesignsolo.helper.TagZoneDetection"
CONDITION = "leveldesignsolo.condition.ConditionDetectUnitDansZoneDetection"
LAUNCH = "leveldesign.launcheffetmap.DescriptorLaunchEffetMap"


def mission(on_start=("Zone_A",), later=(), inline=()) -> bytes:
    """A mission's match script as the game's are made: each zone found by its name, a units-in-zone condition watching
    it, and the launch descriptor whose start-up list (PostInit) holds the conditions of `on_start` (and of `inline`,
    whose zone is found in the condition itself), not those of `later`; a named position on the list too."""
    rows, post = [], []
    for k, zone in enumerate(list(on_start) + list(later), 1):
        rows.append((f"IT_{k}", TAG, [("const", zone.encode())], {}))
        rows.append((f"IR_{k}", CONDITION, [], {"Detecteur": ("name", f"IT_{k}"), "OrbitIgnore": ("const", True)}))
        if zone in on_start:
            post.append(("name", f"IR_{k}"))
    for k, zone in enumerate(inline, 50):
        rows.append((f"IR_{k}", CONDITION, [], {"Detecteur": ("call", TAG, [], {"name": ("const", zone.encode())})}))
        post.append(("name", f"IR_{k}"))
    rows.append(("IT_99", "leveldesignsolo.helper.TagPosition", [("const", b"Spot")], {}))
    post.append(("name", "IT_99"))
    rows.append(("ER_100", LAUNCH, [], {"CampList": ("list", []), "PostInit": ("list", post)}))
    return compiled(rows)


# --- a layout (.scenario): circle zones as its named design items -------------------------------------------------
def layout(*names, hidden=(), tail=b"") -> bytes:
    """A layout whose listed design items are circle zones named `names`; `hidden`: zones not on the list (the game
    doesn't load those); `tail`: bytes after the design items (two of the Balanced Realism Mod's layouts have 20)."""
    every = list(names) + list(hidden)
    objects, listed = [], []
    for k, _n in enumerate(every):
        objects.append((0, [(0, val(0x0B, struct.pack("<3f", 1000.0 * k, 500.0, 0.0))), (1, ref(2 * k + 1, 1))]))
        objects.append((1, [(2, val(0x07, struct.pack("<I", k)))]))
        if k < len(names):
            listed.append(2 * k)
    objects.append((2, [(3, val(0x11, struct.pack("<I", len(listed)) + b"".join(ref(i, 0) for i in listed)))]))
    nd = make_ndf(objects=objects, classes=["TGameDesignItem", "TGameDesignAddOn_CircularZone", "TGameDesignItemList"],
                  props=[("Position", 0), ("AddOn", 0), ("Name", 1), ("GameDesignItemList", 2)], strings=every,
                  topo=[len(objects) - 1])
    head = MAGIC + bytes(16) + bytes(2) + struct.pack("<4I", 4, 1, 4, 0)   # version 4, 1, the zones: none
    return with_checksum(head + struct.pack("<I", len(nd)) + nd) + tail


# --- the menus and a mission's cluster ------------------------------------------------------------------------------
def s(i):
    return val(0x07, struct.pack("<I", i))


def ref(i, cls=0):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def menus(entries) -> tuple[bytes, bytes]:
    """(the map list, the menus) for `entries` [(map-list name, GUID, cluster base name, menu: campaign, operation,
    tutorial, battles or unlisted)], laid out like the game's (rusemod.newmap's reading)."""
    m_objects, strings = [], []
    for name, guid, base, _menu in entries:
        at = len(m_objects)
        strings += [name, base]
        m_objects.append((0, [(0, s(len(strings) - 2)), (1, val(0x1A, guid)),
                              (2, val(0x12, struct.pack("<I", 1) + s(len(strings) - 2) + ref(at + 1, 1)))]))
        m_objects.append((1, [(3, ref(at + 2, 2))]))
        m_objects.append((2, [(4, s(len(strings) - 1))]))
    mapinfo = make_ndf(objects=m_objects, classes=["TMapLoadInfo", "TClusterWithNDFLoadedSubCluster", "TNDFTransaction"],
                       props=[("Name", 0), ("GUID", 0), ("ClusterLoads", 0), ("NdfTransaction", 1), ("BaseName", 2)],
                       strings=strings, topo=[0], compress=True)
    classes = {"campaign": 0, "tutorial": 0, "operation": 1, "battles": 2, "unlisted": 0}
    g_objects = [(classes[menu], [(0, val(0x1A, guid))]) for _n, guid, _b, menu in entries]
    packs = []
    for cls, list_prop, menu, tuto in ((3, 1, "campaign", False), (3, 1, "tutorial", True), (4, 2, "operation", False),
                                       (5, 3, "battles", False)):
        listed = [ref(k, classes[m]) for k, (_n, _g, _b, m) in enumerate(entries) if m == menu]
        if listed:
            packs.append((cls, [(list_prop, val(0x11, struct.pack("<I", len(listed)) + b"".join(listed)))]
                          + ([(4, val(0x00, b"\x01"))] if tuto else [])))
    globals_ = make_ndf(objects=g_objects + packs,
                        classes=["TChapterMapInfo", "TChallengeMapInfo", "TMultiMapInfo", "TChapterPack",
                                 "TChallengePack", "TMultiPack"],
                        props=[("GUID", 0), ("ChapterList", 3), ("ChallengeList", 4), ("MultiList", 5), ("IsTuto", 3)],
                        topo=[len(g_objects)], compress=True)
    return mapinfo, globals_


def cluster(layout_path="DataDir:\\Test\\Map\\M01_Leipzig/LevelDesign.scenario",
            folder="DataDir:\\Test\\map\\M01_Leipzig\\scripting") -> bytes:
    """A scenario cluster naming its layout and its script folder, as the game's do (TClusterAddPythonPath)."""
    return make_ndf(objects=[(0, [(0, s(0))]), (1, [(1, val(0x11, struct.pack("<I", 1) + s(1)))])],
                    classes=["TScenarioLoader", "TClusterAddPythonPath"],
                    props=[("FileName", 0), ("DirectoryList", 1)], strings=[layout_path, folder], compress=True)


LEIPZIG = ("M01_Leipzig", GUIDS["leipzig"], "Patchable\\Scenario\\M01_Leipzig\\Scenario\\ClusterMap", "campaign")


def game_files(entries=(LEIPZIG,), layouts=None, scripts=None, clusters=None) -> dict:
    """{pack: {member: bytes}}: the made-up game's three packs, one chapter by default (M01_Leipzig: its layout holds
    Zone_A and Zone_B, its script watches Zone_A from its start)."""
    mapinfo, globals_ = menus(entries)
    return {GLAD: {MAPINFO: mapinfo, GLOBALS: globals_, **(clusters or {CLUSTER: cluster()})},
            DATA: layouts or {LAYOUT: layout("Zone_A", "Zone_B")},
            IA: scripts or {SCRIPT: mission()}}


def rmod_text(name, version, files, mod_id=None) -> str:
    """An .rmod replacing whole files: {(pack, path with /): bytes}."""
    groups = {}
    for (pack, path), data in files.items():
        groups.setdefault(pack, []).append({"path": path, "data": base64.b64encode(data).decode()})
    return json.dumps({"$schema": "ruse-mod/v1", "id": mod_id or name.replace(" ", "-"), "name": name,
                       "version": version, "author": "Tester", "description": "made up", "game_version": "",
                       "file_patches": [{"dat": f"{REV}/{pack}", "files": fs} for pack, fs in groups.items()]})


class MadeUpGame(unittest.TestCase):
    """A made-up game holding one campaign chapter (game_files), and builds of it into folders."""
    files = staticmethod(game_files)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = self.root / "R.U.S.E"
        rev = self.game / REV
        rev.mkdir(parents=True)
        for pack, members in self.files().items():
            (rev / pack).write_bytes(make_edat([("file", m, d) for m, d in sorted(members.items())]))

    def tearDown(self):
        self.tmp.cleanup()

    def rmod(self, file_name, name, version, files):
        path = self.root / file_name
        path.write_text(rmod_text(name, version, files), encoding="utf-8")
        return load_mod(path)

    def build(self, *mods, out="out"):
        lines = []
        result = build_and_write(self.game, list(mods), out=self.root / out, say=lines.append)
        return result, lines

    @staticmethod
    def warnings(result):
        return [f.message for f in result.findings if f.level == "warning" and "about a second" in f.message]


class MissionWarnings(MadeUpGame):
    def test_a_mod_replacing_a_chapter_s_layout_is_warned_about(self):
        mod = self.rmod("Maps.rmod", "Map Pack", "1.0", {(DATA, "test/map/m01_leipzig/leveldesign.scenario"):
                                                         layout("A_battle_place")})
        result, lines = self.build(mod)
        self.assertEqual(result.errors, [])
        self.assertEqual(self.warnings(result), [
            "Map Pack replaces the maps of 1 campaign chapter(s) with ones that lack places their missions use: with "
            "it on, those chapters stop about a second after they start"])
        self.assertTrue(any(line.startswith("  warning") and "1 campaign chapter(s)" in line for line in lines), lines)

    def test_every_version_of_it(self):
        """The owner, item 31: "It should be warning on every version if there's an error"."""
        for version, places in (("1.0", ("A_battle_place",)), ("1.1", ("Other_place", "Zone_B")), ("2.0", ())):
            with self.subTest(version):
                mod = self.rmod(f"Maps-{version}.rmod", "Map Pack", version,
                                {(DATA, "test/map/m01_leipzig/leveldesign.scenario"): layout(*places)})
                result, _lines = self.build(mod, out=f"out-{version}")
                self.assertEqual(len(self.warnings(result)), 1, result.findings)

    def test_a_mod_keeping_the_places_or_not_touching_missions_isnt(self):
        keeps = self.rmod("Keeps.rmod", "Keeps", "1.0", {(DATA, "test/map/m01_leipzig/leveldesign.scenario"):
                                                         layout("Zone_A", "Zone_B", "More")})
        other = self.rmod("Other.rmod", "Other", "1.0", {(DATA, "test/map/m01_leipzig/notes.txt"): b"hello"})
        for mod in (keeps, other):
            result, _lines = self.build(mod)
            self.assertEqual((result.errors, self.warnings(result)), ([], []))

    def test_a_studio_mod_taking_a_watched_zone_out(self):
        """A player's own mod: its scenario.toml takes the chapter's Zone_A out (the Studio's remove)."""
        from test_build import write_mod
        folder = write_mod(self.root / "mods", "my-edit", {})
        (folder / "maps" / "M01_Leipzig").mkdir(parents=True)
        (folder / "maps" / "M01_Leipzig" / "scenario.toml").write_text(
            '[[remove]]\nfile = "leveldesign.scenario"\nitem = 0\nkind = "CircularZone"\n', encoding="utf-8")
        result, _lines = self.build(load_mod(folder))
        self.assertEqual(result.errors, [])
        self.assertEqual(self.warnings(result), [
            "my-edit replaces the maps of 1 campaign chapter(s) with ones that lack places their missions use: with "
            "it on, those chapters stop about a second after they start"])

    def test_a_studio_mod_taking_out_a_zone_nothing_watches(self):
        from test_build import write_mod
        folder = write_mod(self.root / "mods", "my-edit", {})
        (folder / "maps" / "M01_Leipzig").mkdir(parents=True)
        (folder / "maps" / "M01_Leipzig" / "scenario.toml").write_text(
            '[[remove]]\nfile = "leveldesign.scenario"\nitem = 1\nkind = "CircularZone"\n', encoding="utf-8")
        result, _lines = self.build(load_mod(folder))
        self.assertEqual((result.errors, self.warnings(result)), ([], []))

    def test_a_mod_s_script_watching_a_zone_the_map_lacks(self):
        mod = self.rmod("Script.rmod", "Script Mod", "1.0",
                        {(IA, "genpython/1000/test/map/m01_leipzig/scripting/effetmap.xyz"):
                         mission(("Zone_A", "Zone_Missing"))})
        result, _lines = self.build(mod)
        self.assertEqual(self.warnings(result), [
            "Script Mod replaces the missions of 1 campaign chapter(s) with ones that use places their maps lack: with "
            "it on, those chapters stop about a second after they start"])


# --- item 29: a set made only of .rmod mods -------------------------------------------------------------------------
def army_ndf() -> bytes:
    """test_unitcheck's German tank (its model's mesh an unnamed object) with a class name, as the game's units have:
    what an .rmod mod's change finds it by."""
    from test_unitcheck import PANZER_MODEL, path_text, ref as uref
    return make_ndf(objects=[(0, [(0, val(0x03, struct.pack("<I", 2))), (1, val(0x02, struct.pack("<i", 1))),
                                  (2, uref(1, 1)), (5, val(0x07, struct.pack("<I", 1)))]),
                             (1, [(3, uref(2, 2))]),
                             (2, [(4, path_text(0))])],
                    classes=["TUniteAuSolDescriptor", "TGfxDescriptorModeleWithAnimation", "TResourceMultiMaterialMesh"],
                    props=[("DescriptorId", 0), ("Nationalite", 0), ("GfxDescriptor", 0), ("MeshDescriptor", 1),
                           ("FileName", 2), ("ClassNameForDebug", 0)],
                    strings=["WW2\\Res3D\\Units\\" + PANZER_MODEL, "Unit_Panzer"], exports={0: "Panzer"}, compress=True)


class RmodOnlyUnits(unittest.TestCase):
    """build_and_write with a set made only of .rmod mods, on a made-up game with a unit, a cluster map and the
    skirmish mesh packs: a German tank an .rmod gives to the US makes Germany's packs load in every skirmish."""

    def setUp(self):
        from test_unitcheck import CLUSTER as UNIT_CLUSTER, CLUSTER_MAP, PACKS, mesh_pack
        self.cluster_map = CLUSTER_MAP
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = self.root / "R.U.S.E"
        rev = self.game / REV
        rev.mkdir(parents=True)
        (rev / GLAD).write_bytes(make_edat([("dir", "genglad\\patchable\\", [
            ("dir", "gfx\\", [("file", "everything.cpp.gladndfbin", army_ndf())]),
            ("dir", "scenario\\alpha\\scenario\\", [("file", "clustermap.cpp.gladndfbin", UNIT_CLUSTER)])])]))
        files = [("file", f"meshskirmish{'' if tag.startswith('witboat') else '_'}{tag}.spk", mesh_pack(models))
                 for tag, models in PACKS.items()]
        (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "gen_5\\pack\\gfxdescriptor\\", files)]))

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, value_name, value, out):
        text = json.dumps({"$schema": "ruse-mod/v1", "id": "panzer-mod", "name": "Panzer Mod", "version": "1.0",
                           "author": "Tester", "description": "made up", "game_version": "",
                           "patches": [{"dat": f"{REV}/{GLAD}", "ndf": "genglad/patchable/gfx/everything.cpp.gladndfbin",
                                        "changes": [{"action": "patch", "table": "TUniteAuSolDescriptor",
                                                     "match": {"ClassNameForDebug": "Unit_Panzer"},
                                                     "set": {value_name: {"type": "Int32", "value": value}}}]}]})
        path = self.root / f"{out}.rmod"
        path.write_text(text, encoding="utf-8")
        lines = []
        result = build_and_write(self.game, [load_mod(path)], out=self.root / out, say=lines.append)
        return result, lines

    def test_a_german_tank_for_the_us(self):
        from rusemod import unitcheck
        from rusemod.model import load
        result, lines = self.build("Nationalite", 0, "moved")
        self.assertEqual(result.errors, [], lines)
        said = "\n".join(f.message for f in result.findings)
        self.assertIn("Panzer Mod: $/Panzer is in US's army (Nationalite 0)", said)
        self.assertIn("Germany's unit models now load in every skirmish", said)
        written = Edat((self.root / "moved" / GLAD).read_bytes())
        g, _ = load({self.cluster_map: bytes(written.read(written.find(self.cluster_map)))})
        self.assertEqual([int(part.props["ForceLoadBitFieldIfSkirmish"].value)
                          for _t, _p, part in unitcheck.loaders(g)], [2] * 3)

    def test_a_value_changed_otherwise_leaves_the_cluster_maps(self):
        result, lines = self.build("DescriptorId", 7, "priced")
        self.assertEqual(result.errors, [], lines)
        self.assertFalse(any("now load in every skirmish" in f.message for f in result.findings))
        self.assertNotIn(self.cluster_map, result.changed)


if __name__ == "__main__":
    unittest.main()
