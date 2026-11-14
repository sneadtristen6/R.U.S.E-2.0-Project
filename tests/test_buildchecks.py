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


def menus(entries, titles=None) -> tuple[bytes, bytes]:
    """(the map list, the menus) for `entries` [(map-list name, GUID, cluster base name, menu: campaign, operation,
    tutorial, battles or unlisted)], laid out like the game's (rusemod.newmap's reading). `titles`: {GUID: the text
    key of its name in the menus}, given as its menu entry's Description, as the game's are."""
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
    g_objects = [(classes[menu], [(0, val(0x1A, guid))]
                  + ([(5, val(0x1D, struct.pack("<Q", titles[guid])))] if titles and guid in titles else []))
                 for _n, guid, _b, menu in entries]
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
                        props=[("GUID", 0), ("ChapterList", 3), ("ChallengeList", 4), ("MultiList", 5), ("IsTuto", 3),
                               ("Description", 0)],
                        topo=[len(g_objects)], compress=True)
    return mapinfo, globals_


def cluster(layout_path="DataDir:\\Test\\Map\\M01_Leipzig/LevelDesign.scenario",
            folder="DataDir:\\Test\\map\\M01_Leipzig\\scripting") -> bytes:
    """A scenario cluster naming its layout and its script folder, as the game's do (TClusterAddPythonPath)."""
    return make_ndf(objects=[(0, [(0, s(0))]), (1, [(1, val(0x11, struct.pack("<I", 1) + s(1)))])],
                    classes=["TScenarioLoader", "TClusterAddPythonPath"],
                    props=[("FileName", 0), ("DirectoryList", 1)], strings=[layout_path, folder], compress=True)


LEIPZIG = ("M01_Leipzig", GUIDS["leipzig"], "Patchable\\Scenario\\M01_Leipzig\\Scenario\\ClusterMap", "campaign")


def game_files(entries=(LEIPZIG,), layouts=None, scripts=None, clusters=None, titles=None, texts=None) -> dict:
    """{pack: {member: bytes}}: the made-up game's three packs, one chapter by default (M01_Leipzig: its layout holds
    Zone_A and Zone_B, its script watches Zone_A from its start). `titles` as menus' ; `texts`: ZZ_Win.dat's members,
    when the game should have that pack too."""
    mapinfo, globals_ = menus(entries, titles)
    return {GLAD: {MAPINFO: mapinfo, GLOBALS: globals_, **(clusters or {CLUSTER: cluster()})},
            DATA: layouts or {LAYOUT: layout("Zone_A", "Zone_B")},
            IA: scripts or {SCRIPT: mission()}, **({"ZZ_Win.dat": texts} if texts else {})}


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
def army_ndf(card=None) -> bytes:
    """test_unitcheck's German tank (its model's mesh an unnamed object) with a class name, as the game's units have:
    what an .rmod mod's change finds it by. `card`: the text key of its name on its card (NameInMenuToken), if any."""
    from test_unitcheck import PANZER_MODEL, path_text, ref as uref
    named = [(6, val(0x1D, struct.pack("<Q", card)))] if card is not None else []
    return make_ndf(objects=[(0, [(0, val(0x03, struct.pack("<I", 2))), (1, val(0x02, struct.pack("<i", 1))),
                                  (2, uref(1, 1)), (5, val(0x07, struct.pack("<I", 1)))] + named),
                             (1, [(3, uref(2, 2))]),
                             (2, [(4, path_text(0))])],
                    classes=["TUniteAuSolDescriptor", "TGfxDescriptorModeleWithAnimation", "TResourceMultiMaterialMesh"],
                    props=[("DescriptorId", 0), ("Nationalite", 0), ("GfxDescriptor", 0), ("MeshDescriptor", 1),
                           ("FileName", 2), ("ClassNameForDebug", 0), ("NameInMenuToken", 0)],
                    strings=["WW2\\Res3D\\Units\\" + PANZER_MODEL, "Unit_Panzer"], exports={0: "Panzer"}, compress=True)


class UnitGame(unittest.TestCase):
    """A made-up game with a unit, a cluster map and the skirmish mesh packs, and builds of a Panzer Mod (.rmod) on it."""

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


class RmodOnlyUnits(UnitGame):
    """build_and_write with a set made only of .rmod mods: a German tank an .rmod gives to the US makes Germany's packs
    load in every skirmish."""

    def test_a_german_tank_for_the_us(self):
        from rusemod import unitcheck
        from rusemod.model import load
        result, lines = self.build("Nationalite", 0, "moved")
        self.assertEqual(result.errors, [], lines)
        said = "\n".join(f.message for f in result.findings)
        # (said to a player, with no code names: the review of 95e9b910; the made-up game has no card texts, so the
        # unit's name in the data, made readable)
        self.assertIn("Panzer Mod: Panzer, in US's army, has a model of Germany's units", said)
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


# --- the review of 95e9b910 (2026-11-14): its six faults, each as a kind -------------------------------------------
class MixedSetUnits(UnitGame):
    """Review fault 1: item 29 ("A": run the unit-model check for .rmod mods' units) reached only sets made of .rmod mods
    alone; as soon as any mod of ours was in the set (every test copy has two), an .rmod mod's units were never looked
    at. The same German tank an .rmod mod gives to the US, with a folder mod beside it."""

    def folder_mod(self, name="beside"):
        from test_build import write_mod
        return load_mod(write_mod(self.root / "mods", name, {}))

    def build_with(self, value_name, value, out, *beside):
        text = json.dumps({"$schema": "ruse-mod/v1", "id": "panzer-mod", "name": "Panzer Mod", "version": "1.0",
                           "author": "Tester", "description": "made up", "game_version": "",
                           "patches": [{"dat": f"{REV}/{GLAD}", "ndf": "genglad/patchable/gfx/everything.cpp.gladndfbin",
                                        "changes": [{"action": "patch", "table": "TUniteAuSolDescriptor",
                                                     "match": {"ClassNameForDebug": "Unit_Panzer"},
                                                     "set": {value_name: {"type": "Int32", "value": value}}}]}]})
        path = self.root / f"{out}.rmod"
        path.write_text(text, encoding="utf-8")
        lines = []
        result = build_and_write(self.game, [load_mod(path), *beside], out=self.root / out, say=lines.append)
        return result, lines

    def test_an_rmod_mods_tank_in_a_set_with_a_folder_mod(self):
        from rusemod import unitcheck
        from rusemod.model import load
        result, lines = self.build_with("Nationalite", 0, "mixed", self.folder_mod())
        self.assertEqual(result.errors, [], lines)
        said = "\n".join(f.message for f in result.findings)
        self.assertIn("Panzer Mod: Panzer, in US's army, has a model of Germany's units", said)
        written = Edat((self.root / "mixed" / GLAD).read_bytes())
        g, _ = load({self.cluster_map: bytes(written.read(written.find(self.cluster_map)))})
        self.assertEqual([int(part.props["ForceLoadBitFieldIfSkirmish"].value)
                          for _t, _p, part in unitcheck.loaders(g)], [2] * 3)

    def test_controls_a_mixed_set_whose_rmod_moves_no_unit_and_a_folder_mod_alone(self):
        result, lines = self.build_with("DescriptorId", 7, "priced-mixed", self.folder_mod())
        self.assertEqual(result.errors, [], lines)
        self.assertFalse(any("now load in every skirmish" in f.message for f in result.findings))
        lines = []
        alone = build_and_write(self.game, [self.folder_mod("alone")], out=self.root / "alone", say=lines.append)
        self.assertEqual(alone.errors, [], lines)
        self.assertFalse(any("now load in every skirmish" in f.message for f in alone.findings))

    def test_its_name_on_its_card(self):
        """Review fault 6 (b): a player reads an .rmod mod's unit by its name on its card (here the game's own tank's,
        "PANZER IV"), never its path in the data, its nation's number or its model's file."""
        from test_dic import make_dic
        from rusemod import loc
        from rusemod.dic import name_to_key
        rev = self.game / REV
        old = Edat((rev / GLAD).read_bytes())
        members = {e.path: bytes(old.read(e)) for e in old.entries}
        members["genglad\\patchable\\gfx\\everything.cpp.gladndfbin"] = army_ndf(card=name_to_key("UNI_PZ"))
        (rev / GLAD).write_bytes(make_edat([("file", m, d) for m, d in sorted(members.items())]))
        old = Edat((rev / "ZZ_Win.dat").read_bytes())
        members = {e.path: bytes(old.read(e)) for e in old.entries}
        members[loc.member("baseunite", "us")] = make_dic([(name_to_key("UNI_PZ"), "PANZER IV")])
        (rev / "ZZ_Win.dat").write_bytes(make_edat([("file", m, d) for m, d in sorted(members.items())]))
        result, lines = self.build("Nationalite", 0, "carded")
        self.assertEqual(result.errors, [], lines)
        said = "\n".join(f.message for f in result.findings)
        self.assertIn("Panzer Mod: PANZER IV, in US's army, has a model of Germany's units", said)
        for code in ("$/", "Nationalite", ".ase2ndfbin", "Descriptor_"):
            self.assertNotIn(code, said, said)


class MixedSetUnitsTheOldWay(UnitGame):
    """Review fault 1 with FORCE_LOAD off (the old way, kept; no build uses it): the models of an .rmod mod's unit are
    copied into its nation's skirmish packs, and those copies reach the ZZ_Win.dat the build writes in a set with a
    folder mod that needs no texts too, as they do in a set of .rmod mods alone (the control)."""
    folder_mod = MixedSetUnits.folder_mod
    build_with = MixedSetUnits.build_with

    def setUp(self):
        super().setUp()
        import rusemod.build as b
        self.addCleanup(setattr, b, "FORCE_LOAD", b.FORCE_LOAD)
        b.FORCE_LOAD = False

    def copied(self, out) -> bool:
        """Whether the US's skirmish mesh pack in the ZZ_Win.dat written to `out` has the German tank's model."""
        from rusemod.spk import Spk
        from test_unitcheck import PANZER_MODEL
        written = self.root / out / "ZZ_Win.dat"
        if not written.exists():
            return False
        zz = Edat(written.read_bytes())
        member = zz.entry("gen_5\\pack\\gfxdescriptor\\meshskirmish_us.spk")
        return member is not None and f"ww2\\res3d\\units\\{PANZER_MODEL}" in Spk(bytes(zz.read(member))).items

    def test_an_rmod_mods_tank_in_a_set_with_a_folder_mod(self):
        result, lines = self.build_with("Nationalite", 0, "old-mixed", self.folder_mod())
        self.assertEqual(result.errors, [], lines)
        self.assertTrue(any("its models go into US's skirmish packs too" in f.message for f in result.findings),
                        [f.message for f in result.findings])
        self.assertTrue(self.copied("old-mixed"), lines)

    def test_control_the_rmod_mod_alone(self):
        result, lines = self.build("Nationalite", 0, "old-alone")
        self.assertEqual(result.errors, [], lines)
        self.assertTrue(self.copied("old-alone"), lines)


class WhoMovedIt(UnitGame):
    """Review fault 3's kind in an .rmod mod's unit note: the mod named is the one that gives the unit another nation
    or other models, not every .rmod mod that changes it (every test copy's cheat mod re-prices most units, and was
    named beside the mod that moved the unit)."""
    NOTE = ("Panzer Mod: Panzer, in US's army, has a model of Germany's units: Germany's unit models now load in every "
            "skirmish, so it shows in matches where no player has Germany too")

    def rmod_setting(self, mod_id, name, values, file_name):
        text = json.dumps({"$schema": "ruse-mod/v1", "id": mod_id, "name": name, "version": "1.0", "author": "Tester",
                           "description": "made up", "game_version": "",
                           "patches": [{"dat": f"{REV}/{GLAD}", "ndf": "genglad/patchable/gfx/everything.cpp.gladndfbin",
                                        "changes": [{"action": "patch", "table": "TUniteAuSolDescriptor",
                                                     "match": {"ClassNameForDebug": "Unit_Panzer"},
                                                     "set": {k: {"type": "Int32", "value": v}
                                                             for k, v in values.items()}}]}]})
        path = self.root / f"{file_name}.rmod"
        path.write_text(text, encoding="utf-8")
        return load_mod(path)

    def unit_notes(self, mods, out):
        lines = []
        result = build_and_write(self.game, list(mods), out=self.root / out, say=lines.append)
        self.assertEqual(result.errors, [], lines)
        return [f.message for f in result.findings if "has a model of" in f.message]

    def test_a_mod_that_only_reprices_the_moved_unit_isnt_named(self):
        moves = self.rmod_setting("panzer-mod", "Panzer Mod", {"Nationalite": 0}, "moves")
        prices = self.rmod_setting("price-mod", "Price Mod", {"DescriptorId": 7}, "prices")
        self.assertEqual(self.unit_notes((prices, moves), "a"), [self.NOTE])
        self.assertEqual(self.unit_notes((moves, prices), "b"), [self.NOTE])

    def test_control_the_mod_that_moves_it_and_reprices_it(self):
        both = self.rmod_setting("panzer-mod", "Panzer Mod", {"Nationalite": 0, "DescriptorId": 7}, "both")
        self.assertEqual(self.unit_notes((both,), "c"), [self.NOTE])


def spawning(*classes, hidden=()) -> bytes:
    """A layout whose listed design items spawn units of `classes` (the last part of the Python class path the game's
    layouts give a spawn: front.parametres.Classes.Unit_M4_Sherman); `hidden`: spawns not on the list (not loaded)."""
    every = list(classes) + list(hidden)
    objects, listed = [], []
    for k, _cls in enumerate(every):
        objects.append((0, [(0, val(0x0B, struct.pack("<3f", 1000.0 * k, 500.0, 0.0))), (1, ref(2 * k + 1, 1))]))
        objects.append((1, [(2, val(0x07, struct.pack("<I", k))), (3, val(0x02, struct.pack("<i", 0)))]))
        if k < len(classes):
            listed.append(2 * k)
    objects.append((2, [(4, val(0x11, struct.pack("<I", len(listed)) + b"".join(ref(i, 0) for i in listed)))]))
    nd = make_ndf(objects=objects, classes=["TGameDesignItem", "TGameDesignAddOn_Spawn", "TGameDesignItemList"],
                  props=[("Position", 0), ("AddOn", 0), ("PythonClassName", 1), ("Camp", 1), ("GameDesignItemList", 2)],
                  strings=[f"front.parametres.Classes.{c}" for c in every], topo=[len(objects) - 1])
    head = MAGIC + bytes(16) + bytes(2) + struct.pack("<4I", 4, 1, 4, 0)
    return with_checksum(head + struct.pack("<I", len(nd)) + nd)


SPAWN_LAYOUT = BS.join(["test", "map", "alpha", "leveldesign_bh.scenario"])


class RmodSpawns(UnitGame):
    """The review's suspicion 5, of fault 1's kind (an .rmod mod's units with no unit-model check): the units an .rmod
    mod's layouts spawn get the spawn check our mods' spawns get (spawn_models), alone and beside a folder mod: a German
    tank spawned on a map whose layout as the game ships it spawns none makes Germany's packs load in every match."""
    folder_mod = MixedSetUnits.folder_mod

    def setUp(self):
        super().setUp()
        self.shipped(spawning("Unit_Jeep"))

    def shipped(self, layout_bytes):
        (self.game / REV / DATA).write_bytes(make_edat([("file", SPAWN_LAYOUT, layout_bytes)]))

    def spawn_mod(self, layout_bytes, out, *beside):
        path = self.root / f"{out}.rmod"
        path.write_text(rmod_text("Spawn Mod", "1.0", {(DATA, SPAWN_LAYOUT.replace(BS, "/")): layout_bytes}),
                        encoding="utf-8")
        lines = []
        result = build_and_write(self.game, [load_mod(path), *beside], out=self.root / out, say=lines.append)
        return result, lines

    def forced(self, out):
        """The force bits of the cluster map's loaders in the unit data written to `out`, or None when not written."""
        from rusemod import unitcheck
        from rusemod.model import load
        if not (self.root / out / GLAD).exists():
            return None
        written = Edat((self.root / out / GLAD).read_bytes())
        g, _ = load({self.cluster_map: bytes(written.read(written.find(self.cluster_map)))})
        return [int(part.props["ForceLoadBitFieldIfSkirmish"].value) for _t, _p, part in unitcheck.loaders(g)]

    def test_an_rmod_mods_layout_spawning_a_german_tank(self):
        result, lines = self.spawn_mod(spawning("Unit_Jeep", "Unit_Panzer"), "alone")
        self.assertEqual(result.errors, [], lines)
        self.assertIn("Spawn Mod: the spawned Panzer use Germany's unit models, which a skirmish loads only when a "
                      "player has Germany: they now load in every skirmish (3 loaders in 1 cluster maps)",
                      [f.message for f in result.findings])
        self.assertEqual(self.forced("alone"), [2] * 3)

    def test_the_same_beside_a_folder_mod(self):
        result, lines = self.spawn_mod(spawning("Unit_Panzer"), "mixed", self.folder_mod())
        self.assertEqual(result.errors, [], lines)
        self.assertIn("Spawn Mod: the spawned Panzer use Germany's unit models, which a skirmish loads only when a "
                      "player has Germany: they now load in every skirmish (3 loaders in 1 cluster maps)",
                      [f.message for f in result.findings])
        self.assertEqual(self.forced("mixed"), [2] * 3)

    def test_said_by_its_name_on_its_card(self):
        """(as review fault 6 (b) asks of an .rmod mod's units: a player reads the unit by its card's name)"""
        from test_dic import make_dic
        from rusemod import loc
        from rusemod.dic import name_to_key
        rev = self.game / REV
        old = Edat((rev / GLAD).read_bytes())
        members = {e.path: bytes(old.read(e)) for e in old.entries}
        members["genglad\\patchable\\gfx\\everything.cpp.gladndfbin"] = army_ndf(card=name_to_key("UNI_PZ"))
        (rev / GLAD).write_bytes(make_edat([("file", m, d) for m, d in sorted(members.items())]))
        old = Edat((rev / "ZZ_Win.dat").read_bytes())
        members = {e.path: bytes(old.read(e)) for e in old.entries}
        members[loc.member("baseunite", "us")] = make_dic([(name_to_key("UNI_PZ"), "PANZER IV")])
        (rev / "ZZ_Win.dat").write_bytes(make_edat([("file", m, d) for m, d in sorted(members.items())]))
        result, lines = self.spawn_mod(spawning("Unit_Panzer"), "carded")
        self.assertEqual(result.errors, [], lines)
        self.assertIn("Spawn Mod: the spawned PANZER IV use Germany's unit models, which a skirmish loads only when a "
                      "player has Germany: they now load in every skirmish (3 loaders in 1 cluster maps)",
                      [f.message for f in result.findings])

    def test_a_layout_that_cant_be_read_is_said(self):
        result, lines = self.spawn_mod(b"not a layout", "unread")
        self.assertEqual(result.errors, [], lines)
        self.assertIn("Spawn Mod: a map layout it changes can't be read, so whether the units it spawns have their "
                      "models in every match wasn't checked", [f.message for f in result.findings])

    def test_control_a_spawn_not_on_the_list(self):
        result, lines = self.spawn_mod(spawning("Unit_Jeep", hidden=("Unit_Panzer",)), "hidden")   # (not loaded)
        self.assertEqual(result.errors, [], lines)
        self.assertFalse([f.message for f in result.findings if "spawned" in f.message])
        self.assertIsNone(self.forced("hidden"))

    def test_controls_what_the_games_own_layout_of_that_map_spawns(self):
        self.shipped(spawning("Unit_Panzer"))   # (the game's layout of that map spawns the tank already)
        for out, beside in (("own", ()), ("own-mixed", (self.folder_mod(),))):
            result, lines = self.spawn_mod(spawning("Unit_Panzer", "Unit_Jeep"), out, *beside)
            self.assertEqual(result.errors, [], lines)
            self.assertFalse([f.message for f in result.findings if "spawned" in f.message], out)
            self.assertFalse(any(self.forced(out) or []), out)


class WhoIsNamed(MadeUpGame):
    """Review fault 3: a mod whose edits take out or rename only places the mission doesn't lack is not named for it."""

    def studio(self, name, toml_name, text):
        from test_build import write_mod
        folder = write_mod(self.root / "mods", name, {})
        (folder / "maps" / "M01_Leipzig").mkdir(parents=True)
        (folder / "maps" / "M01_Leipzig" / toml_name).write_text(text, encoding="utf-8")
        return load_mod(folder)

    def test_a_studio_edit_on_top_of_an_rmods_layout_that_lacks_the_zone(self):
        nameless = self.rmod("A.rmod", "Nameless Maps", "1.0",
                             {(DATA, "test/map/m01_leipzig/leveldesign.scenario"): layout("Zone_B", "Other")})
        other_out = self.studio("takes-other-out", "scenario.toml",
                                '[[remove]]\nfile = "leveldesign.scenario"\nitem = 1\nkind = "CircularZone"\n')
        result, lines = self.build(nameless, other_out)
        self.assertEqual(result.errors, [], lines)
        self.assertEqual(self.warnings(result), [
            "Nameless Maps replaces the maps of 1 campaign chapter(s) with ones that lack places their missions use: "
            "with it on, those chapters stop about a second after they start"])

    def test_control_a_studio_rename_of_the_watched_zone_is_named(self):
        renamer = self.studio("renamer", "items.toml", '[[set]]\nfile = "leveldesign.scenario"\nitem = 0\n'
                                                       'kind = "CircularZone"\nname = "Zone_Renamed"\n')
        result, lines = self.build(renamer)
        self.assertEqual(result.errors, [], lines)
        self.assertEqual(self.warnings(result), [
            "renamer replaces the maps of 1 campaign chapter(s) with ones that lack places their missions use: with it "
            "on, those chapters stop about a second after they start"])

    def test_an_rmods_scenario_edits_by_name_and_by_object(self):
        """The same for an .rmod mod's edits of a layout's design items: by name, or by its object's number (resolved
        on the layout as shipped); one that can't be told is named as before."""
        from types import SimpleNamespace
        from rusemod import missionplaces as mp
        from rusemod.build import _mission_blame, _mission_changers
        shipped = layout("Zone_A", "Zone_B")   # (objects: Zone_A's item 0 and AddOn 1, Zone_B's item 2 and AddOn 3)
        member = "test\\map\\m01_leipzig\\leveldesign.scenario"

        def rmod_with(name, changes):
            path = self.root / f"{name}.rmod"
            path.write_text(json.dumps({"$schema": "ruse-mod/v1", "id": name, "name": name, "version": "1.0",
                                        "author": "Tester", "description": "made up", "game_version": "",
                                        "scenario_patches": [{"dat": f"{REV}/{DATA}",
                                                              "scenario": "test/map/m01_leipzig/leveldesign.scenario",
                                                              "changes": changes}]}), encoding="utf-8")
            return SimpleNamespace(id=name, rmod=path)
        mods = [rmod_with("by-name-b", [{"action": "delete", "table": "TGameDesignAddOn_CircularZone",
                                         "match": {"Name": "Zone_B"}}]),
                rmod_with("by-object-b", [{"action": "delete", "table": "TGameDesignAddOn_CircularZone",
                                           "match": {"_index": "3"}}]),
                rmod_with("by-name-a", [{"action": "delete", "table": "TGameDesignAddOn_CircularZone",
                                         "match": {"Name": "Zone_A"}}]),
                rmod_with("unknown", [{"action": "delete", "table": "TGameDesignAddOn_CircularZone",
                                       "match": {"Position": "1"}}])]
        changers = _mission_changers(mods, [], [], SimpleNamespace(new_maps={}, mission_scripts={}),
                                     before=lambda _m: shipped, shipped=lambda m: shipped if m.lower() == member else None)
        mission = mp.Mission("campaign", "M01_Leipzig", CLUSTER.lower(), (member,), (SCRIPT.lower(),))
        missing = mp.Missing(mission, ["Zone_A"], True, False, False)
        named, _ = _mission_blame(missing, changers, {DATA.lower(): lambda _m: layout("Zone_B")})
        self.assertEqual(named, ["by-name-a", "unknown"])


class OddMenus(MadeUpGame):
    """Review fault 4: the check only warns, so nothing in it ever stops a build that built before: menus holding a
    list where the tutorial's flag is, or anything else going wrong in the check, is one note and the build goes on."""

    def odd_menus(self):
        mapinfo, globals_ = menus([LEIPZIG])
        nd_objects = [(0, [(0, val(0x1A, GUIDS["leipzig"]))]),
                      (1, [(1, val(0x11, struct.pack("<I", 1) + ref(0, 0))), (2, val(0x11, struct.pack("<I", 0)))])]
        odd = make_ndf(objects=nd_objects, classes=["TChapterMapInfo", "TChapterPack"],
                       props=[("GUID", 0), ("ChapterList", 1), ("IsTuto", 1)], topo=[1], compress=True)
        return self.rmod("M.rmod", "Odd Menus", "1.0", {(GLAD, "genglad/patchable/misc/globals.cpp.gladndfbin"): odd})

    def test_menus_with_a_list_where_the_tutorials_flag_is(self):
        result, lines = self.build(self.odd_menus())
        self.assertEqual(result.errors, [], lines)
        self.assertTrue((self.root / "out").exists() and any((self.root / "out").iterdir()), lines)
        self.assertTrue(any(f.level == "note" and "couldn't be checked: the menus or a mission's files can't be read"
                            in f.message for f in result.findings), result.findings)

    def test_anything_going_wrong_in_the_check(self):
        from unittest import mock
        mod = self.rmod("Maps.rmod", "Map Pack", "1.0", {(DATA, "test/map/m01_leipzig/leveldesign.scenario"):
                                                         layout("A_battle_place")})
        with mock.patch("rusemod.missionplaces.check", side_effect=RuntimeError("something went wrong")):
            result, lines = self.build(mod)
        self.assertEqual(result.errors, [], lines)
        # (a fault of the check itself is not said to be a file that can't be read)
        self.assertIn("the places the missions watch from their start couldn't be checked (something went wrong)",
                      [f.message for f in result.findings if f.level == "note"])
        result, _ = self.build(mod, out="again")   # (the control: the same set, the check as it is, warns)
        self.assertEqual(len(self.warnings(result)), 1)


class CountLine(MadeUpGame):
    """Review fault 5: the report's count line counts every finding of the build, the missions' warnings too (the
    six's warning used to be counted)."""

    def test_the_count_line_counts_the_missions_warning(self):
        mod = self.rmod("Maps.rmod", "Map Pack", "1.0", {(DATA, "test/map/m01_leipzig/leveldesign.scenario"):
                                                         layout("A_battle_place")})
        result, lines = self.build(mod)
        warnings = len([f for f in result.findings if f.level == "warning"])
        notes = len([f for f in result.findings if f.level == "note"])
        self.assertEqual(warnings, 1)
        counted = [ln for ln in lines if ln.endswith("note(s)")]
        self.assertEqual(counted, [f"0 error(s), {warnings} warning(s), {notes} note(s)"])
        said_at = next(i for i, ln in enumerate(lines) if "1 campaign chapter(s)" in ln)
        self.assertGreater(lines.index(counted[0]), said_at)   # (said once every finding is in)

    def test_control_a_build_stopped_by_an_error_says_its_count_first(self):
        from test_build import write_mod
        folder = write_mod(self.root / "mods", "broken", {"x.rndf": "patch $/Nope ( P = 1 )"})
        result, lines = self.build(load_mod(folder))
        self.assertTrue(result.errors, lines)
        counted = [i for i, ln in enumerate(lines) if ln.endswith("note(s)")]
        self.assertEqual(len(counted), 1, lines)
        self.assertEqual(lines[counted[0] + 1], "Nothing was written.")

    def test_control_a_build_stopped_later_by_a_raised_error_says_its_count_once(self):
        """As before the review's fixes: a build that stops on an error raised in its later work (a map's BuildError;
        here one made up where the missions are checked) still says its count, once."""
        from unittest import mock
        from rusemod.build import BuildError
        mod = self.rmod("Maps.rmod", "Map Pack", "1.0", {(DATA, "test/map/m01_leipzig/leveldesign.scenario"):
                                                         layout("A_battle_place")})
        lines = []
        with mock.patch("rusemod.build.mission_places", side_effect=BuildError("a map can't be built")):
            with self.assertRaises(BuildError):
                build_and_write(self.game, [mod], out=self.root / "out", say=lines.append)
        self.assertEqual(len([ln for ln in lines if ln.endswith("note(s)")]), 1, lines)


TITLE_KEY = 0x00000007653A5042   # (a made-up text key of a chapter's name in the menus)


def titled_game_files() -> dict:
    """game_files, the chapter's name in the menus given, and the game's menu texts holding it."""
    from test_dic import make_dic
    from rusemod import loc
    return game_files(titles={GUIDS["leipzig"]: TITLE_KEY},
                      texts={loc.member("flash_txt", "us"): make_dic([(TITLE_KEY, "1. COLDITZ CASTLE")])})


class MenuNames(MadeUpGame):
    """Review fault 6 (a): a note on a mission names it as the menus do (the game's own text of its name), never by
    its name in the map list, and its reason without a class name of our code."""
    files = staticmethod(titled_game_files)

    def test_an_unread_missions_note(self):
        from unittest import mock
        mod = self.rmod("Bad.rmod", "Bad Script", "1.0",
                        {(IA, "genpython/1000/test/map/m01_leipzig/scripting/effetmap.xyz"): b"XYZ0 not a script"})
        with mock.patch("rusemod.fairplay.ON", False):   # (this made-up ZZ_Win.dat holds the menus' texts only)
            result, _lines = self.build(mod)
        notes = [f.message for f in result.findings if f.level == "note" and "can't be read" in f.message]
        self.assertEqual(len(notes), 1, result.findings)
        self.assertTrue(notes[0].startswith("1. COLDITZ CASTLE: a file of its mission can't be read ("), notes)
        self.assertNotIn("M01_Leipzig", notes[0])
        self.assertNotIn("Error", notes[0])


if __name__ == "__main__":
    unittest.main()
