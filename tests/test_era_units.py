"""Era units in the Units tab (ruse_studio.era_units) on the Studio tests' made-up game: the library read from
RUSE_ERA_UNITS, an era's units listed and filtered like the Units list, every one out of the mod until added, an era
unit's page with the game units it can start from (the suggestion first), adding one from the suggestion or from
another unit with its own name and price, its credit in the mod's CREDITS-era-units.md, the same name in two eras,
taking it out again. And the download: an era from the release's list, each file checked, updated when a newer one is
out, refused when a file isn't right. Its size (its real width against the start unit, else 1) and the unit it's
researched from (the build menu's units, a suggestion, chains of era units), and the add form's words and tooltips."""
import hashlib
import json
import os
import re
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_studio import M4, WithMod
from ruse_studio import era_units
from ruse_studio.api import StudioError

PANZER = "$/GFX/Everything/Descriptor_Unit_Panzer_IV_G"


def entry(era, nation, name, card, copies, extra="", air=False):
    return {"key": f"{era}|{nation}|{name}", "era": era, "nation": nation, "name": name, "in_place_of": "",
            "card": card, "building": "Armor base", "copies": copies, "copies_name": "", "game_nation": 0,
            "factory": 10, "aircraft": air, "model": None, "fits": True, "picture": None,
            "credit": {"title": f"{name} model", "author": "maker", "licence": "CC-BY 4.0",
                       "url": f"https://example.org/{name.replace(' ', '_')}", "extra": extra}}


UNITS = [entry("WWI", "USA", "Mark VIII Liberty", "Heavy Tank", M4),
         entry("Cold War", "USA", "Patton", "Medium Tank", M4, extra="Scan of Jo's 1:35 model"),
         entry("Modern", "USA", "Patton", "Medium Tank", M4),
         entry("Modern", "China", "Type 99", "Main Battle Tank", PANZER),
         entry("Modern", "USA", "F-35", "Advanced Fighter", M4, air=True)]


class EraUnits(WithMod):
    def setUp(self):
        super().setUp()
        self.lib = Path(tempfile.mkdtemp(dir=self.tmp.name))
        (self.lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": UNITS}),
                                                 encoding="utf-8")
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(self.lib)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_listed_by_era_and_filtered_like_the_units_list(self):
        self.assertEqual(era_units.library_dir(), self.lib)
        modern = self.api.era_units_list("Modern")
        self.assertTrue(modern["library"])
        self.assertEqual([u["name"] for u in modern["units"]], ["Patton", "Type 99", "F-35"])
        self.assertEqual([u["added"] for u in modern["units"]], [None, None, None])     # nothing added by itself
        self.assertEqual(modern["types"], ["Advanced Fighter", "Main Battle Tank", "Medium Tank"])
        self.assertEqual([u["name"] for u in self.api.era_units_list("Modern", kind="air")["units"]], ["F-35"])
        self.assertEqual([u["name"] for u in self.api.era_units_list("Modern", nation=7)["units"]], ["Type 99"])
        self.assertEqual([u["code"] for u in modern["units"]], [0, 7, 0])                  # China: chip 7
        self.assertEqual([u["name"] for u in self.api.era_units_list("Modern", search="pat")["units"]], ["Patton"])
        self.assertEqual([u["name"] for u in self.api.era_units_list("Modern", group="type:Main Battle Tank")["units"]],
                         ["Type 99"])

    def test_page_offers_any_unit_of_its_kind_to_start_from(self):
        page = self.api.era_unit_page("WWI|USA|Mark VIII Liberty")
        self.assertEqual((page["name"], page["added"], page["has_model"], page["picture"]),
                         ("Mark VIII Liberty", None, False, None))
        self.assertEqual(page["start"][0]["address"], M4)                                  # the suggestion first
        self.assertTrue(page["start"][0]["suggested"])
        self.assertIn(PANZER, [s["address"] for s in page["start"]])                       # any ground unit
        self.assertEqual(self.api.era_start_price(PANZER)["price"], 45.0)
        with self.assertRaises(StudioError):
            self.api.era_unit_page("Nope|USA|Nothing")

    def test_added_from_the_suggestion_and_taken_out(self):
        with self.assertRaises(StudioError):
            self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)                       # no mod yet
        folder = Path(self.api.new_mod("Eras")["current"])
        made = self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)
        self.assertEqual((made["name"], made["model"], made["model_note"]), ("Mark VIII Liberty", None, "no_model"))
        listed = {u["address"]: u for u in self.api.units()["units"]}
        self.assertEqual((listed[made["address"]]["new"], listed[made["address"]]["source"]), (True, M4))
        self.assertEqual(json.loads((folder / "era_units.json").read_text(encoding="utf-8")),
                         {"WWI|USA|Mark VIII Liberty": made["address"]})
        credits = (folder / "CREDITS-era-units.md").read_text(encoding="utf-8")
        self.assertIn('- Mark VIII Liberty (WWI, USA): "Mark VIII Liberty model" by maker, CC-BY 4.0, '
                      'https://example.org/Mark_VIII_Liberty.', credits)
        self.assertEqual(self.api.era_units_list("WWI")["units"][0]["added"], made["address"])
        self.assertEqual(self.api.era_unit_page("WWI|USA|Mark VIII Liberty")["added"], made["address"])
        with self.assertRaises(StudioError):
            self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)                       # already in
        self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")
        self.assertNotIn(made["address"], {u["address"] for u in self.api.units()["units"]})
        self.assertFalse((folder / "CREDITS-era-units.md").exists())
        with self.assertRaises(StudioError):
            self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")                           # not in any more

    def test_its_card_comes_with_it(self):
        """The library's card picture (its model drawn at the game's card size) becomes the new unit's own card, for the
        build menu and the selection to show, not the card of the unit it started from (2026-10-08 test: an F-4 showed
        the Bf 109's; their own cards seen in the build menus, test 5); out of the mod, it goes too. Its kind of card ("card": Heavy Tank) stays what it was."""
        from rusemod.dxt import png_bytes
        (self.lib / "WWI" / "USA").mkdir(parents=True)
        card = png_bytes(bytes([90, 110, 130, 255]) * (360 * 184), 360, 184, channels=4)
        (self.lib / "WWI" / "USA" / "Liberty.png").write_bytes(card)
        units = [dict(u, card_picture="WWI/USA/Liberty.png") if u["name"] == "Mark VIII Liberty" else u for u in UNITS]
        (self.lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": units}),
                                                 encoding="utf-8")
        folder = Path(self.api.new_mod("Cards")["current"])
        made = self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)
        self.assertTrue(made["card"])
        own = folder / "files" / "cards" / f"{made['address'].rsplit('/', 1)[-1]}.png"
        self.assertEqual(own.read_bytes(), card)
        self.assertEqual(self.api.era_units_list("WWI")["types"], ["Heavy Tank"])
        self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")
        self.assertFalse(own.exists())
        # one the library names outside its own folders is never read
        units = [dict(u, card_picture="../Liberty.png") if u["name"] == "Mark VIII Liberty" else u for u in UNITS]
        (self.lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": units}),
                                                 encoding="utf-8")
        (self.lib.parent / "Liberty.png").write_bytes(card)
        self.assertFalse(self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)["card"])

    def test_its_model_keeps_the_way_it_faces(self):
        """The library's model is already in the game's axes, its front +x (some pinned by hand when fitted: no rule
        of the importer's could tell): added, it's fitted with that facing, not worked out again."""
        (self.lib / "WWI" / "USA").mkdir(parents=True)
        (self.lib / "WWI" / "USA" / "Liberty.glb").write_bytes(b"glb")
        units = [dict(u, model="WWI/USA/Liberty.glb") if u["name"] == "Mark VIII Liberty" else u for u in UNITS]
        (self.lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": units}),
                                                 encoding="utf-8")
        self.api.new_mod("Facing")
        with mock.patch.object(self.api, "model_import", return_value={"model": {"parts": []}}) as fitted:
            self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)
        self.assertEqual(fitted.call_args.kwargs.get("facing"), [0, 1])

    def test_started_from_another_unit_with_its_own_name_and_price(self):
        folder = Path(self.api.new_mod("Own values")["current"])
        made = self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 1, 10, source=PANZER, name="Liberty", price=99)
        self.assertEqual(made["name"], "Liberty")
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"is clone {PANZER}", rndf)                                           # the Panzer's values
        self.assertIn("ProductionPrice = [99, 99]", rndf)

    def test_same_name_in_two_eras_and_the_extra_credit(self):
        folder = Path(self.api.new_mod("Two Pattons")["current"])
        first = self.api.era_unit_add("Cold War|USA|Patton", 0, 10)
        second = self.api.era_unit_add("Modern|USA|Patton", 0, 10)
        self.assertEqual((first["name"], second["name"]), ("Patton", "Patton (Modern)"))
        credits = (folder / "CREDITS-era-units.md").read_text(encoding="utf-8")
        self.assertIn('"Patton model" by maker, CC-BY 4.0, https://example.org/Patton. Scan of Jo\'s 1:35 model.',
                      credits)

    def test_no_library(self):
        with mock.patch.object(era_units, "library_dir", return_value=None):
            self.assertEqual(self.api.era_units_list("WWI"),
                             {"library": False, "installed": False, "types": [], "units": []})

    def test_start_units_by_their_game_names(self):
        """The add form's start units and research choices go by the game's names, never its code names (the
        Studio's rule), English in the code names' mode."""
        start = {s["address"]: s["name"] for s in self.api.era_unit_page("WWI|USA|Mark VIII Liberty")["start"]}
        self.assertEqual((start[M4], start[PANZER]), ("M4 Sherman", "Panzer IV"))
        start = {s["address"]: s["name"] for s in self.api.era_unit_page("WWI|USA|Mark VIII Liberty", "fr")["start"]}
        self.assertEqual(start[M4], "M4 Sherman (fr)")

    def test_a_start_unit_without_a_model_has_no_length(self):
        """The start unit's hull is the importer's own measure (find_source), kept in the cache folder for the next
        start; this made-up game has no models, so it's not known (None), and the size stays 1."""
        self.assertIsNone(self.api._era_like(M4))
        kept = json.loads((self.api.cache_dir / "eras" / "likes.json").read_text(encoding="utf-8"))
        self.assertEqual(list(kept.values()), [None])
        self.assertTrue(next(iter(kept)).endswith("|" + M4))

    def test_no_research_where_the_game_has_none(self):
        """This made-up game's units have no UpgradeRequire: nothing is offered to research them from, and adding one
        writes no research."""
        research = self.api.era_unit_page("WWI|USA|Mark VIII Liberty")["research"]
        self.assertEqual(research, {"offered": False, "choices": [], "suggested": None, "why": ""})
        folder = Path(self.api.new_mod("No research")["current"])
        made = self.api.era_unit_add("Cold War|USA|Patton", 0, 10)
        self.assertIsNone(made["research_from"])
        self.assertNotIn("Upgrade", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(StudioError, "can't be researched from"):
            self.api.era_unit_add("Modern|USA|Patton", 0, 10, research_from=M4)


# --- real size: a made-up .glb in the library ---
def box_glb(boxes: list) -> bytes:
    """A .glb of boxes [(name, (x0, y0, z0), (x1, y1, z1))] given in the importer's axes (rusemod.modelin: x forward, y
    across, z up; read_glb takes a glTF point (x, y, z) as (x, -z, y))."""
    from rusemod.gltf import FLOAT, UINT, _Glb
    from test_unitmodel import BOX_FACES
    g = _Glb()
    for k, (name, (x0, y0, z0), (x1, y1, z1)) in enumerate(boxes):
        pts = [(x, y, z) for z in (z0, z1) for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        gl = [(float(x), float(z), float(-y)) for x, y, z in pts]
        attrs = {"POSITION": g.accessor(gl, "VEC3", FLOAT)}
        idx = [i for f in BOX_FACES for i in f]
        g.doc["meshes"].append({"name": name, "primitives": [{"attributes": attrs,
                                                              "indices": g.accessor(idx, "SCALAR", UINT, 34963)}]})
        g.doc["nodes"].append({"name": name, "mesh": k})
    g.doc["scenes"], g.doc["scene"] = [{"nodes": list(range(len(boxes)))}], 0
    return g.to_bytes()


# a tank 4 long and 2 wide (its hull), its turret narrower; a plane 3 long with wings 9 across
TANK_BOXES = [("Hull", (-2, -1, 0), (2, 1, 1)), ("Turret", (-0.5, -0.6, 1), (0.5, 0.6, 1.5))]
PLANE_BOXES = [("Fuselage", (-1.5, -0.25, 0), (1.5, 0.25, 0.5)), ("Wings", (-0.25, -4.5, 0.2), (0.25, 4.5, 0.3))]
LIKES = {M4: {"length": 1000.0, "width": 470.0}, PANZER: {"length": 800.0, "width": 400.0}}


class EraSize(WithMod):
    """The import size suggested for an era unit: the one that gives it its real width (an aircraft: its wingspan) in
    the game's units against the start unit picked; 1 (as before) when that can't be worked out; clamped to the
    importer's 0.2 to 5. The library gives the real sizes ("real") and the game's units in a metre ("units_per_metre");
    the start unit's hull length is the importer's own (find_source: here made up, as the made-up game has no
    models)."""

    def setUp(self):
        super().setUp()
        self.lib = Path(tempfile.mkdtemp(dir=self.tmp.name))
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(self.lib)})
        patcher.start()
        self.addCleanup(patcher.stop)
        (self.lib / "WWI" / "USA").mkdir(parents=True)
        (self.lib / "WWI" / "USA" / "Liberty.glb").write_bytes(box_glb(TANK_BOXES))
        (self.lib / "WWI" / "USA" / "F35.glb").write_bytes(box_glb(PLANE_BOXES))
        self.library({"Mark VIII Liberty": {"width_m": 3.0}, "F-35": {"span_m": 10.7, "width_m": 99.0}},
                     {"ground": 180.0, "air": 150.0})
        patcher = mock.patch.object(self.api, "_era_like", side_effect=lambda source: LIKES.get(source))
        patcher.start()
        self.addCleanup(patcher.stop)

    def library(self, real: dict, scale: dict | None):
        units = [dict(u, model="WWI/USA/Liberty.glb", real=real.get(u["name"])) if u["name"] == "Mark VIII Liberty"
                 else dict(u, model="WWI/USA/F35.glb", real=real.get(u["name"])) if u["name"] == "F-35" else u
                 for u in UNITS]
        doc = {"version": 1, "note": "", **({"units_per_metre": scale} if scale else {}), "units": units}
        (self.lib / "era_units.json").write_text(json.dumps(doc), encoding="utf-8")

    def test_its_real_width_against_the_start_unit(self):
        page = self.api.era_unit_page("WWI|USA|Mark VIII Liberty")
        # 3 m x 180 units a metre = 540 units wide; its hull 4 long, 2 wide; the M4's hull 1000 long:
        # s = 540 x 4 / (2 x 1000) = 1.08
        self.assertAlmostEqual(page["size"], 1.08)
        self.assertEqual({k: page["size_info"][k] for k in ("real", "clamped", "real_m", "what", "why")},
                         {"real": True, "clamped": None, "real_m": 3.0, "what": "width", "why": ""})
        self.assertAlmostEqual(self.api.era_unit_start("WWI|USA|Mark VIII Liberty", PANZER, 1, 10)["size"], 1.35)
        # fitted at that size by the importer itself, it's 540 game units wide
        from rusemod import modelin
        model = modelin.read_model(self.lib / "WWI" / "USA" / "Liberty.glb")
        like = {"length": 1000.0, "pivot": (0.0, 0.0), "ground": 0.0, "facing": [0, 1]}
        prep = modelin.prepare(model, [], like, size=page["size"])
        hull = next(p for p in prep.parts if p.bone == "chassis")
        ys = [p[1] for p in hull.positions]
        xs = [p[0] for p in hull.positions]
        self.assertAlmostEqual(max(ys) - min(ys), 540.0, places=6)
        self.assertAlmostEqual(max(xs) - min(xs), 1080.0, places=6)    # as long as 1.08 M4 hulls

    def test_an_aircraft_by_its_wingspan(self):
        info = self.api.era_unit_page("Modern|USA|F-35")
        # 10.7 m x 150 = 1605 units across its wings; it's 3 long, its hull (the whole plane) 9 across
        self.assertAlmostEqual(info["size"], 10.7 * 150 * 3 / (9 * 1000))
        self.assertEqual((info["size_info"]["what"], info["size_info"]["real_m"]), ("span", 10.7))

    def test_added_at_the_size_given_or_suggested(self):
        self.api.new_mod("Sizes")
        with mock.patch.object(self.api, "model_import", return_value={"model": {"parts": []}}) as fitted:
            made = self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)
            self.assertAlmostEqual(fitted.call_args.args[2], 1.08)
            self.assertAlmostEqual(made["size"], 1.08)
            self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")
            self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10, size=2.5)
            self.assertEqual(fitted.call_args.args[2], 2.5)
            self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")
            self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10, source=PANZER)    # against the Panzer's hull
            self.assertAlmostEqual(fitted.call_args.args[2], 1.35)
            self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")
            for bad in (0.1, 6, "big", True, float("nan")):
                with self.subTest(size=bad), self.assertRaisesRegex(StudioError, "from 0.2 to 5"):
                    self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10, size=bad)
        self.assertEqual(self.api.era_units_list("WWI")["units"][0]["added"], None)        # nothing half made

    def test_clamped_to_the_importers_sizes(self):
        self.library({"Mark VIII Liberty": {"width_m": 30.0}}, {"ground": 180.0})
        info = self.api.era_unit_page("WWI|USA|Mark VIII Liberty")
        self.assertEqual(info["size"], 5.0)
        self.assertAlmostEqual(info["size_info"]["clamped"], 10.8)          # 30 x 180 x 4 / (2 x 1000)
        self.assertTrue(info["size_info"]["real"])
        self.library({"Mark VIII Liberty": {"width_m": 0.1}}, {"ground": 180.0})
        info = self.api.era_unit_page("WWI|USA|Mark VIII Liberty")
        self.assertEqual(info["size"], 0.2)
        self.assertAlmostEqual(info["size_info"]["clamped"], 0.036)

    def test_one_when_it_cant_be_worked_out(self):
        """Not known is 1 (as long as the start unit, as before), never a guess: each reason said."""
        def why(key="WWI|USA|Mark VIII Liberty", source=M4):
            got = self.api.era_unit_start(key, source, 0, 10)
            return got["size"], got["size_info"]["real"], got["size_info"]["why"]
        self.library({}, {"ground": 180.0})
        self.assertEqual(why(), (1.0, False, "no_real"))
        self.library({"Mark VIII Liberty": {"width_m": -3}}, {"ground": 180.0})
        self.assertEqual(why(), (1.0, False, "no_real"))
        self.library({"Mark VIII Liberty": {"width_m": 3.0}}, None)
        self.assertEqual(why(), (1.0, False, "no_scale"))
        self.library({"Mark VIII Liberty": {"width_m": 3.0}}, {"air": 150.0})            # only the aircraft's
        self.assertEqual(why(), (1.0, False, "no_scale"))
        self.library({"Mark VIII Liberty": {"width_m": 3.0}}, {"ground": 180.0})
        self.assertEqual(why(source=DEPOT_LESS), (1.0, False, "start_unread"))
        (self.lib / "WWI" / "USA" / "Liberty.glb").write_bytes(b"glb")                   # a model that isn't one
        self.assertEqual(why(), (1.0, False, "model_unread"))
        self.assertEqual(why("Cold War|USA|Patton"), (1.0, False, "no_model"))

    def test_the_download_keeps_the_games_units_in_a_metre(self):
        """A downloaded era's library keeps the release list's "units_per_metre" and each unit's "real"."""
        good = {"era": "WWI", "version": "a" * 64, "units": [{"key": "k", "era": "WWI", "real": {"width_m": 2.5}}],
                "parts": [{"file": "era-units-WWI-1.zip", "size": 10, "sha256": "b" * 64}]}
        listed = era_units.parse_list(json.dumps({"format": 1, "units_per_metre": {"ground": 180.0, "air": "x"},
                                                  "sections": [good]}).encode())
        self.assertEqual(listed[0]["units_per_metre"], {"ground": 180.0})
        root = Path(tempfile.mkdtemp(dir=self.tmp.name))
        era_units.install_section(root, listed[0], [])
        index = json.loads((root / era_units.INDEX).read_text(encoding="utf-8"))
        self.assertEqual((index["units_per_metre"], index["units"][0]["real"]), ({"ground": 180.0}, {"width_m": 2.5}))
        era_units.write_index(root)                                                     # written again: kept
        self.assertEqual(json.loads((root / era_units.INDEX).read_text(encoding="utf-8"))["units_per_metre"],
                         {"ground": 180.0})


DEPOT_LESS = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger"      # a start unit with no model to measure


# --- researched from: a made-up game with upgrades (test_upgrades') ---
class EraResearch(unittest.TestCase):
    """Researched from, in the add form: the units of the build menu picked (the Upgrade box's choices, the mod's new
    units too, so era units chain) or none (buyable from the start), with a research price and time; the suggestion:
    the start unit when it's in that menu, else the unit the era unit stands in for, else for Cold War and Modern
    units the dearest of the menu, else none. Linked as the Upgrade box links it, and changed there later."""

    @classmethod
    def setUpClass(cls):
        from rusemod.index import build_index
        from test_upgrades import write_game
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        from rusemod.play import Starter
        from ruse_studio.api import StudioApi
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: True,
                          wait=lambda s: None)
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home, starter=starter,
                             instances=self.home / "copies")
        self.lib = Path(tempfile.mkdtemp(dir=self.tmp.name))
        units = [entry("Cold War", "USSR", "T-80", "Main Battle Tank", UB),     # starts from B, an upgrade of A
                 entry("Modern", "Russia", "T-90", "Main Battle Tank", UC),
                 entry("Cold War", "USA", "Patton", "Medium Tank", UD),         # starts from a German unit
                 entry("WWI", "USA", "Liberty", "Heavy Tank", UD),
                 dict(entry("WWII", "USA", "Easy Eight", "Medium Tank", UD), in_place_of="unit_c")]
        (self.lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": units}),
                                                 encoding="utf-8")
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(self.lib)})
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def names(research):
        return [c["address"] for c in research["choices"]]

    def test_the_menus_units_and_the_suggestion(self):
        t80 = self.api.era_unit_page("Cold War|USSR|T-80")["research"]
        self.assertEqual((t80["offered"], self.names(t80)), (True, [UA, UB, UC]))   # US menu 10 (F is in 11, D German)
        self.assertEqual([c["name"] for c in t80["choices"]], ["Unit_A", "Unit_B", "Unit_C"])
        self.assertEqual((t80["suggested"], t80["why"]), (UB, "start"))
        german = self.api.era_unit_start("Cold War|USSR|T-80", UD, 1, 10)["research"]  # another menu picked
        self.assertEqual((self.names(german), german["suggested"], german["why"]), ([UD], UD, "start"))
        patton = self.api.era_unit_page("Cold War|USA|Patton")["research"]
        self.assertEqual((patton["suggested"], patton["why"]), (UC, "dearest"))    # C costs 40, B 30, A 20
        self.assertEqual(self.api.era_unit_start("Cold War|USA|Patton", UD, 0, 11)["research"]["suggested"], UF)
        liberty = self.api.era_unit_page("WWI|USA|Liberty")["research"]
        self.assertEqual((liberty["suggested"], liberty["why"]), (None, ""))         # WWI: nothing behind research
        easy = self.api.era_unit_page("WWII|USA|Easy Eight")["research"]
        self.assertEqual((easy["suggested"], easy["why"]), (UC, "in_place_of"))      # the unit it stands in for
        self.assertEqual(self.api.era_unit_start("Cold War|USSR|T-80", UB, 0, 99)["research"]["choices"], [])

    def test_a_unit_never_shown_isnt_suggested(self):
        """The dearest unit the build menu never shows (ShowInMenu 0 at every battle date, as the game's DEMO, film and
        empty units) isn't suggested: an era unit researched from it could never be researched. It stays a choice."""
        from ruse_studio.edits import ModEdits
        self.api.new_mod("Hidden")
        edits = ModEdits(self.home / "mods" / "hidden")
        edits.set(UC, "ShowInMenu", [0, 0, 0, 0, 0])
        edits.save()
        patton = self.api.era_unit_page("Cold War|USA|Patton")["research"]
        self.assertEqual((patton["suggested"], patton["why"]), (UB, "dearest"))    # C (40) never shown: B (30)
        self.assertIn(UC, self.names(patton))
        # shown at the last battle date only (as the game's atomic units), while the new unit, as its start unit D,
        # is shown at all five: not suggested either
        edits = ModEdits(self.home / "mods" / "hidden")
        edits.set(UC, "ShowInMenu", [0, 0, 0, 0, 1])
        edits.set(UD, "ShowInMenu", [1, 1, 1, 1, 1])
        edits.save()
        patton = self.api.era_unit_page("Cold War|USA|Patton")["research"]
        self.assertEqual((patton["suggested"], patton["why"]), (UB, "dearest"))

    def test_added_researched_and_chained(self):
        self.api.new_mod("Research")
        folder = self.home / "mods" / "research"
        t80 = self.api.era_unit_add("Cold War|USSR|T-80", 0, 10)                     # the suggestion: from B
        self.assertEqual(t80["research_from"], UB)
        info = self.api.upgrade(t80["address"])
        self.assertEqual(info["parent"]["address"], UB)
        self.assertEqual({p: r["value"] for p, r in info["research"].items()}, {"UpgradePrice": 50, "UpgradeTime": 50})
        # the T-90 researched from the T-80 (a unit of the mod), for its own price and time
        offered = self.api.era_unit_page("Modern|Russia|T-90")["research"]
        self.assertIn(t80["address"], self.names(offered))
        self.assertIn("T-80", [c["name"] for c in offered["choices"]])
        t90 = self.api.era_unit_add("Modern|Russia|T-90", 0, 10, research_from=t80["address"], research_price=120,
                                    research_time=90)
        info = self.api.upgrade(t90["address"])
        self.assertEqual(info["parent"]["address"], t80["address"])
        self.assertEqual({p: r["value"] for p, r in info["research"].items()}, {"UpgradePrice": 120, "UpgradeTime": 90})
        self.assertEqual([c["address"] for c in self.api.upgrade(t80["address"])["children"]], [t90["address"]])
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"UpgradeRequire = {UB}", text)
        self.assertIn(f"UpgradeRequire = {t80['address']}", text)
        # the Upgrade box changes it afterwards: buyable from the start
        self.assertIsNone(self.api.set_upgrade(t90["address"], None)["parent"])
        # a research price the game can't keep is refused before the unit is made: nothing half made (0.9.8.2 review)
        before = json.loads((folder / "era_units.json").read_text(encoding="utf-8"))
        with self.assertRaisesRegex(StudioError, "UpgradePrice: 3000000000 doesn't fit"):
            self.api.era_unit_add("Cold War|USA|Patton", 0, 10, research_price=3_000_000_000)
        self.assertEqual(json.loads((folder / "era_units.json").read_text(encoding="utf-8")), before)

    def test_taken_out_with_a_unit_researched_from_it(self):
        """The T-80 taken out while the T-90 is researched from it, as the modder chose (Settings > Research): warned
        first, or refused, with nothing changed; re-linked, the T-90 is researched from what the T-80 was (B), and the
        T-80 goes."""
        self.api.new_mod("Research")
        t80 = self.api.era_unit_add("Cold War|USSR|T-80", 0, 10)
        t90 = self.api.era_unit_add("Modern|Russia|T-90", 0, 10, research_from=t80["address"])
        res = self.api.era_unit_remove("Cold War|USSR|T-80")
        self.assertEqual((res["removed"], [c["address"] for c in res["ask"]]), (None, [t90["address"]]))
        self.assertEqual(self.api.era_unit_page("Cold War|USSR|T-80")["added"], t80["address"])
        self.api.set_pref("research_gone", "refuse")
        with self.assertRaisesRegex(StudioError, "stays in the mod"):
            self.api.era_unit_remove("Cold War|USSR|T-80")
        self.assertEqual(self.api.era_unit_page("Cold War|USSR|T-80")["added"], t80["address"])
        self.assertIn(t80["address"], self.api._new_units())
        self.api.set_pref("research_gone", "relink")
        res = self.api.era_unit_remove("Cold War|USSR|T-80")
        self.assertEqual(res["removed"], t80["address"])
        self.assertEqual([(r["address"], r["to"]["address"]) for r in res["relinked"]], [(t90["address"], UB)])
        self.assertEqual(self.api.upgrade(t90["address"])["parent"]["address"], UB)
        self.assertIsNone(self.api.era_unit_page("Cold War|USSR|T-80")["added"])
        self.assertNotIn(t80["address"], self.api._new_units())

    def test_buyable_from_the_start(self):
        """None: no research, even when the start unit is an upgrade in its own menu (B, of A): its link goes."""
        self.api.new_mod("Buyable")
        made = self.api.era_unit_add("Cold War|USSR|T-80", 0, 10, research_from=None)
        self.assertIsNone(made["research_from"])
        self.assertIsNone(self.api.upgrade(made["address"])["parent"])
        text = (self.home / "mods" / "buyable" / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("delete UpgradeRequire", text)

    def test_what_is_refused_leaves_nothing_made(self):
        self.api.new_mod("Refused")
        for kwargs, why in (({"research_from": UD}, "can't be researched from"),        # another nation
                            ({"research_from": UF}, "can't be researched from"),        # another build menu
                            ({"research_from": UA, "research_price": -5}, "a number from 0 up"),
                            ({"research_from": UA, "research_time": "long"}, "a number from 0 up")):
            with self.subTest(**kwargs), self.assertRaisesRegex(StudioError, why):
                self.api.era_unit_add("Cold War|USA|Patton", 0, 10, **kwargs)
        self.assertEqual(self.api.era_units_list("Cold War")["units"][1]["added"], None)
        self.assertEqual(self.api._new_units(), {})


UA, UB, UC, UD, UF = (f"$/GFX/Everything/Unit_{n}" for n in "ABCDF")


class EraUnitsScreen(unittest.TestCase):
    """The era units' add form (ui/eraunits.js): every word it shows is in the words file in all ten languages, and
    every control it makes has a tooltip (the Studio's rule)."""

    def test_every_word_and_every_tooltip(self):
        from ruse_studio.api import _words
        ui = Path(__file__).parents[1] / "src" / "ruse_studio" / "ui"
        js = (ui / "eraunits.js").read_text(encoding="utf-8")
        used = set(re.findall(r"(?:\bw|W\(\)|state\.words)\.([a-z_0-9]+)", js)) | set(
            re.findall(r'"((?:eras?|tip)_[a-z_0-9]+)"', js))
        self.assertGreater(len(used), 40)
        words = _words()
        self.assertEqual(sorted(used - set(words)), [])
        from rusemod import schema
        for key in sorted(used):
            self.assertEqual([lang for lang in schema.LANGS if not words[key].get(lang)], [], key)
        controls = []
        for m in re.finditer(r'el\("(?:button|input|select)", \{', js):     # each control's properties, braces paired
            depth, at = 0, m.end() - 1
            for at in range(m.end() - 1, len(js)):
                depth += {"{": 1, "}": -1}.get(js[at], 0)
                if depth == 0:
                    break
            controls.append(js[m.end():at])
        self.assertGreater(len(controls), 10)
        self.assertEqual([c for c in controls if "title:" not in c], [])
        # every call it makes is the Studio's, and the browser preview (fake-api.js) answers it too
        from ruse_studio.api import StudioApi
        calls = set(re.findall(r"api\(\)\.(\w+)\(", js))
        self.assertIn("era_unit_start", calls)
        fake = (ui / "fake-api.js").read_text(encoding="utf-8")
        self.assertEqual(sorted(c for c in calls if not callable(getattr(StudioApi, c, None))), [])
        self.assertEqual(sorted(c for c in calls if f"{c}: async" not in fake), [])


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class EraDownload(WithMod):
    """An era downloaded from the release's list (a folder standing in for GitHub): every file checked, unpacked into
    the platform folder's era_units, listed; a newer version updates it; a file that isn't right installs nothing."""

    def setUp(self):
        super().setUp()
        self.release = Path(tempfile.mkdtemp(dir=self.tmp.name))
        patcher = mock.patch.dict(os.environ, {era_units.URL_ENV: self.release.as_posix() + "/"})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(era_units.LIBRARY_ENV, None)
        self.root = self.home / era_units.DOWNLOADED

    def publish(self, files: dict, units: list, era="WWI", name="era-units-WWI-1.zip", size=None, digest=None):
        """The release: one .zip of `files` (path -> bytes) and the list naming it with `units`."""
        with zipfile.ZipFile(self.release / name, "w") as z:
            for path, data in files.items():
                z.writestr(path, data)
        data = (self.release / name).read_bytes()
        version = sha(json.dumps([sorted(files), units]).encode())
        part = {"file": name, "size": size or len(data), "sha256": digest or sha(data)}
        (self.release / era_units.LIST).write_text(json.dumps(
            {"format": 1, "sections": [{"era": era, "version": version, "parts": [part], "units": units}]}),
            encoding="utf-8")
        self.api._era_kept = None   # the list asked for again

    def run_job(self, era="WWI"):
        job = self.api.era_download(era)["job"]
        end = time.time() + 20
        while (got := self.api.job(job))["state"] == "running" and time.time() < end:
            time.sleep(0.05)
        return got

    def unit(self, name, picture):
        u = entry("WWI", "USA", name, "Heavy Tank", M4)
        return dict(u, model=f"WWI/USA/{name}.glb", picture=picture)

    def test_downloaded_listed_and_updated(self):
        self.publish({"WWI/USA/Liberty.glb": b"glb one", "pictures/a.jpg": b"jpg a"},
                     [self.unit("Liberty", "pictures/a.jpg")])
        self.assertEqual(self.api.era_units_list("WWI")["installed"], False)
        self.assertEqual(self.api.era_sections()["sections"][0] | {"size": 0},
                         {"era": "WWI", "units": 1, "size": 0, "state": "new"})
        self.assertEqual(self.api.era_sections(downloaded_only=True), {"sections": [], "message": ""})
        got = self.run_job()
        self.assertEqual((got["state"], got["lines"][-1]), ("done", "unpack"), got)
        self.assertEqual(era_units.library_dir(self.home), self.root)
        listed = self.api.era_units_list("WWI")
        self.assertEqual((listed["installed"], [u["name"] for u in listed["units"]]), (True, ["Liberty"]))
        page = self.api.era_unit_page("WWI|USA|Liberty")
        self.assertTrue(page["has_model"])
        self.assertEqual((self.root / "WWI/USA/Liberty.glb").read_bytes(), b"glb one")
        self.assertFalse((self.root / ".download").exists() and any((self.root / ".download").iterdir()))
        self.assertEqual(self.api.era_sections()["sections"][0]["state"], "current")
        # a newer version: another unit, the old picture gone
        self.publish({"WWI/USA/Whippet.glb": b"glb two", "pictures/b.jpg": b"jpg b"},
                     [self.unit("Whippet", "pictures/b.jpg")])
        self.assertEqual(self.api.era_sections(downloaded_only=True)["sections"][0]["state"], "update")
        self.assertEqual(self.run_job()["state"], "done")
        self.assertEqual([u["name"] for u in self.api.era_units_list("WWI")["units"]], ["Whippet"])
        self.assertFalse((self.root / "pictures/a.jpg").exists())
        self.assertFalse((self.root / "WWI/USA/Liberty.glb").exists())

    def test_a_units_card_comes_with_its_era(self):
        unit = dict(self.unit("Liberty", None), card_picture="WWI/USA/Liberty.png")
        self.publish({"WWI/USA/Liberty.glb": b"glb", "WWI/USA/Liberty.png": b"png"}, [unit])
        self.assertEqual(self.run_job()["state"], "done")
        self.assertEqual((self.root / "WWI/USA/Liberty.png").read_bytes(), b"png")
        self.publish({"WWI/USA/Liberty.glb": b"glb"}, [unit])        # the list names a card the files don't hold
        self.assertIn("don't hold", self.run_job()["message"])

    def test_an_era_in_the_librarys_folder_name(self):
        u = dict(entry("Cold War", "USA", "Patton", "Medium Tank", M4), model="Cold_War/USA/Patton.glb")
        self.publish({"Cold_War/USA/Patton.glb": b"glb"}, [u], era="Cold War", name="era-units-Cold_War-1.zip")
        self.assertEqual(self.run_job("Cold War")["state"], "done")
        self.assertEqual([x["name"] for x in self.api.era_units_list("Cold War")["units"]], ["Patton"])
        self.assertTrue(self.api.era_unit_page("Cold War|USA|Patton")["has_model"])

    def test_a_file_outside_the_era_installs_nothing(self):
        for bad in ("../evil.glb", "WWII/USA/x.glb", "WWI/USA/run.exe", "WWI/a/b/c.glb"):
            self.publish({"WWI/USA/Liberty.glb": b"glb", bad: b"x"}, [self.unit("Liberty", None)])
            got = self.run_job()
            self.assertEqual(got["state"], "failed", bad)
            self.assertIn("nothing was installed", got["message"])
            self.assertFalse((self.root / era_units.INDEX).exists())
            self.assertFalse(Path(self.root, "WWI").exists())

    def test_a_file_not_as_the_list_promises_is_refused(self):
        self.publish({"WWI/USA/Liberty.glb": b"glb"}, [self.unit("Liberty", None)], digest="0" * 64)
        got = self.run_job()
        self.assertEqual(got["state"], "failed")
        self.assertIn("isn't the file the era units list promises", got["message"])
        self.assertFalse((self.root / era_units.INDEX).exists())
        self.publish({"WWI/USA/Other.glb": b"glb"}, [self.unit("Liberty", None)])   # the list names what isn't there
        self.assertIn("don't hold", self.run_job()["message"])

    def test_the_list_checked(self):
        good = {"era": "WWI", "version": "a" * 64, "units": [{"key": "k", "era": "WWI", "model": "WWI/USA/x.glb"}],
                "parts": [{"file": "era-units-WWI-1.zip", "size": 10, "sha256": "b" * 64}]}
        bad = [dict(good, era="Space"), dict(good, version="x"), dict(good, units=[]),
               dict(good, parts=[{"file": "../era-units-x.zip", "size": 10, "sha256": "b" * 64}]),
               dict(good, parts=[{"file": "era-units-WWI-1.zip", "size": 2_000_000_001, "sha256": "b" * 64}]),
               dict(good, units=[{"key": "k", "era": "WWI", "model": "C:/x.glb"}]),
               dict(good, units=[{"key": "k", "era": "WWI", "model": "WWI/USA/x.glb", "card_picture": "../x.png"}])]
        for b in bad:
            self.assertEqual(era_units.parse_list(json.dumps({"format": 1, "sections": [b]}).encode()), [], b)
        self.assertEqual(len(era_units.parse_list(json.dumps({"format": 1, "sections": [good, good]}).encode())), 1)
        with self.assertRaises(era_units.EraDownloadError):
            era_units.parse_list(b'{"format": 2, "sections": []}')
        self.assertTrue(era_units.safe_member("Cold War/USA/M1 Abrams.glb"))
        self.assertTrue(era_units.safe_member("Cold_War/China/An_12_Chinese.glb"))   # as the library names it
        for name in ("pictures/../x.jpg", "WWI\\USA\\x.glb", "pictures/a/b.jpg", "WWI/USA/x.py", "/WWI/USA/x.glb"):
            self.assertFalse(era_units.safe_member(name), name)

    def test_no_list_yet_and_a_list_that_cant_be_read(self):
        (self.release / era_units.LIST).unlink(missing_ok=True)   # none published yet: no units yet, no problem
        self.assertEqual(self.api.era_sections(), {"sections": [], "message": ""})
        with self.assertRaises(StudioError) as caught:
            self.api.era_download("WWI")
        self.assertIn("No WWI units are out yet", str(caught.exception))
        self.assertEqual(self.api.era_units_list("WWI")["installed"], False)
        (self.release / era_units.LIST).write_text("{not a list", encoding="utf-8")
        self.api._era_kept = None
        self.assertIn("can't be read", self.api.era_sections()["message"])


if __name__ == "__main__":
    unittest.main()
