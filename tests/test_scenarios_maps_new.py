"""Scenarios: a player makes a new map in the Studio's Maps tab (Duplicate map, New map: start from scratch), the usual
way and the unusual ones, on the made-up game of test_scenarios_maps_base. Each checks what the page is told, the
map's files, and that the map still builds (Test in game).

FOR: the overnight scenario tests of map mods (owner, 2026-11-13). USED-BY: the release check of 0.9.8.20."""
import tomllib
import unittest

from test_scenarios_maps_base import APP_LANGS, BATTLES_ENTRY, BLITZ, LANGS, MapGame, page_said
from rusemod import newmap
from rusemod.dic import name_to_key
from ruse_studio.api import StudioApi, StudioError

SCEN = "leveldesign_normal.scenario"   # the made-up Blitz's scenario: a start for team 2 (item 0) and a Sherman


class NewMaps(MapGame):
    """The usual ways: a copy, Blank Terrain, Blank Ocean, a copy of a copy; each builds."""

    def test_a_plain_copy_builds_with_its_name_in_the_menus(self):
        res = self.api.duplicate_map(BLITZ, "Blitz at Dusk")
        self.assertEqual(res["pack"], "BlitzAtDusk")
        self.assertEqual([m["pack"] for m in res["maps"]], [BLITZ, "BlitzAtDusk"])  # right after the map it copies
        row = res["maps"][1]
        self.assertEqual((row["copy_of"], row["kinds"], row["blank"]), (BLITZ, ["skirmish"], False))
        self.assertEqual(self.toml("BlitzAtDusk"), {"copy_of": BLITZ, "name": "Blitz at Dusk"})
        self.assertBuilds()
        self.assertEqual(len(self.started), 1)
        self.assertTrue(self.copy().joinpath("Maps", "PC", "DataMapBlitzAtDusk_v09.dat").is_file())
        for lang in LANGS:  # one name typed: every language's menus show it
            self.assertEqual(self.copy_texts(lang).text(name_to_key("M_D_31")), "Blitz at Dusk", lang)
        self.game_untouched()

    def test_from_scratch_with_no_map_project_yet(self):
        """New map: start from scratch before any map project is picked: one is made, named after the map."""
        self.assertIsNone(self.map_dir())
        pack = self.api.duplicate_map(BLITZ, "Fresh Start", preset="blank_terrain")["pack"]
        self.assertEqual((self.map_dir().name, pack), ("fresh-start", "FreshStart"))
        self.assertEqual(self.api.mods("map")["current"], str(self.map_dir()))
        self.assertEqual(self.api.mods("mod")["current"], None)  # the Units tab's mod stays unpicked

    def place_hqs(self, pack: str):
        """Scenario, Each player's HQ, as a player does it on a blank map: the copied start moved (team 2) and team 1's
        added."""
        self.api.scenario_move(pack, SCEN, 0, 1200.0, 1200.0)
        return self.api.scenario_add_start(pack, SCEN, 1, 2400.0, 2400.0)

    def test_blank_terrain_and_blank_ocean_build_once_each_hq_is_placed(self):
        for preset, sea in (("blank_terrain", False), ("blank_ocean", True)):
            with self.subTest(preset=preset):
                pack = self.api.duplicate_map(BLITZ, f"Blitz {preset}", preset=preset)["pack"]
                folder = self.map_folder(pack)
                self.assertEqual(sorted(f.name for f in folder.iterdir()),
                                 ["map.toml", "menu-wide.png", "menu.png", "roads.toml", "scenario.toml", "scenery.toml",
                                  "terrain.toml"])
                self.assertEqual(self.toml(pack)["blank"], preset.removeprefix("blank_"))
                view = self.api.map_scenarios(pack)
                self.assertTrue(view["blank"])
                items = view["scenarios"][0]["items"]
                self.assertEqual([(it["kind"], it.get("placed"), it.get("gone", False)) for it in items],
                                 [("StartingPoint", False, False), ("Spawn", None, True)])  # nothing but the start
                got = self.build()
                self.assertEqual(got["state"], "failed")
                said = [e for e in got.get("errors", [])] or got["lines"]
                self.assertTrue(any("these HQs aren't placed yet: team 2, HQ 1" in str(x) for x in said), got)
                self.place_hqs(pack)
                self.assertBuilds(preset)
                strokes = tomllib.loads((folder / "terrain.toml").read_text(encoding="utf-8"))["stroke"]
                self.assertEqual([s["brush"] for s in strokes],
                                 ["level", "water", "paint"] if sea else ["level", "drain", "paint"])
                self.api.delete_map(pack)  # (each preset built alone)

    def test_a_copy_of_a_copy_keeps_its_edits_and_a_copy_of_a_blank_stays_blank(self):
        first = self.api.duplicate_map(BLITZ, "Blitz One")["pack"]
        self.api.terrain_add(first, [{"brush": "hill", "x": 1500.0, "y": 1500.0, "radius": 600.0, "height": 400.0}])
        second = self.api.duplicate_map(first, "Blitz Two")["pack"]
        self.assertEqual(self.toml(second)["copy_of"], BLITZ)
        self.assertEqual(self.api.terrain(second)["strokes"][0]["brush"], "hill")
        blank = self.api.duplicate_map(BLITZ, "Blank One", preset="blank_terrain")["pack"]
        self.place_hqs(blank)
        again = self.api.duplicate_map(blank, "Blank Two")["pack"]
        self.assertEqual((self.toml(again)["blank"], self.toml(again)["ground"]), ("terrain", "generated"))
        self.assertTrue(next(m for m in self.api.maps()["maps"] if m["pack"] == again)["blank"])
        self.assertEqual(len([it for it in self.api.map_scenarios(again)["scenarios"][0]["items"]
                              if it["kind"] == "StartingPoint"]), 2)  # its HQs came along
        self.assertBuilds()
        names = {self.copy_texts("us").text(name_to_key(f"M_D_{n}")) for n in range(31, 35)}
        self.assertEqual(names, {"Blitz One", "Blitz Two", "Blank One", "Blank Two"})

    def test_sizes_a_blank_map_takes_and_refuses(self):
        """Map size: every even size from 2 to 128 cells a side taken, the rest refused in plain words, and the
        refusal said in the player's language. (The made-up map is too small to build a size: the real install's dry
        builds do that.)"""
        pack = self.api.duplicate_map(BLITZ, "Big Blank", preset="blank_terrain")["pack"]
        for across, down in ((2, 2), (4, 2), (128, 2), (2, 128), (128, 128), (64, 64)):
            got = self.api.set_map_size(pack, across, down)
            self.assertEqual(got["cells"], [across, down])
            self.assertEqual(self.toml(pack)["size"], [across, down])
        for bad in ((3, 3), (0, 0), (130, 2), (-2, 2), (2, 1)):
            with self.subTest(bad=bad), self.assertRaises(StudioError):
                self.api.set_map_size(pack, *bad)
        self.assertEqual(self.toml(pack)["size"], [64, 64])  # nothing written by a refusal
        with self.assertRaisesRegex(StudioError, "even number of squares"):
            self.api.set_map_size(pack, 66, 64, first_x=1)
        self.in_lang("fr")  # the one refusal the page's buttons can lead to (a strip is two squares) is said in French
        self.assertNotIn("A strip is two squares wide", page_said(self.api, "set_map_size", pack, 66, 64, 1))
        copy = self.api.duplicate_map(BLITZ, "Plain Copy")["pack"]
        self.assertEqual(self.api.map_size(copy)["why"], "copy")
        with self.assertRaises(StudioError):
            self.api.set_map_size(copy, 4, 4)


class Names(MapGame):
    """A new map's name: every script the apps' languages use, long ones, symbols, Windows' reserved names, one taken."""

    NAMES = {"us": "Blitz at Dusk", "fr": "Côte d'Opale : l'aube", "ger": "Straße nach Köln", "ita": "Città del Vaticano",
             "spa": "Señorío de Peñíscola", "pol": "Łódź, Żółć", "ru": "Блиц у реки", "cz": "Příbram Ústí",
             "jpn": "電撃戦・夜明け", "sc": "闪电战黎明", "fa": "حمله‌ی رعدآسا"}

    def test_a_name_in_every_script_the_apps_use(self):
        self.assertEqual(sorted(self.NAMES), sorted(APP_LANGS))
        packs = {}
        for lang, name in self.NAMES.items():
            packs[lang] = self.api.duplicate_map(BLITZ, name)["pack"]
            newmap.check_name(packs[lang])  # a pack name the game's files carry
        self.assertEqual(len(set(p.lower() for p in packs.values())), len(packs))  # each its own
        rows = {m["pack"]: m for m in self.api.maps()["maps"]}
        for lang, name in self.NAMES.items():
            self.assertEqual(rows[packs[lang]]["titles"]["us"], [name], lang)
            self.assertEqual(self.toml(packs[lang])["name"], name, lang)
        self.assertBuilds()
        shown = {self.copy_texts("us").text(name_to_key(f"M_D_{n}")) for n in range(31, 31 + len(self.NAMES))}
        self.assertEqual(shown, set(self.NAMES.values()))  # every name exactly as typed, in the menus' texts

    def test_long_names_and_symbols(self):
        ok = {"x" * newmap.NAME_LONGEST: None, 'Blitz "at" Dusk \\ / : * ? < > |': None, "Blitz 🌙 at night": None,
              "   Blitz \t at \n dusk  ": "Blitz at dusk", "#1 — l'été": None, "Ё" * newmap.NAME_LONGEST: None}
        for name, kept in ok.items():
            with self.subTest(name=name):
                pack = self.api.duplicate_map(BLITZ, name)["pack"]
                newmap.check_name(pack)
                self.assertEqual(self.toml(pack)["name"], kept or name)
        for name, why in (("x" * (newmap.NAME_LONGEST + 1), "the menus take 60"), ("   ", "Give the new map a name"),
                          ("", "Give the new map a name")):
            with self.subTest(name=name), self.assertRaisesRegex(StudioError, why):
                self.api.duplicate_map(BLITZ, name)
        self.assertBuilds()

    def test_a_name_taken(self):
        """The same name twice, in other letters' case, and the shipped map's pack name: each map its own folder, all
        listed, all built."""
        one = self.api.duplicate_map(BLITZ, "Blitz at Dusk")["pack"]
        two = self.api.duplicate_map(BLITZ, "Blitz at Dusk")["pack"]
        three = self.api.duplicate_map(BLITZ, BLITZ)["pack"]
        four = self.api.duplicate_map(BLITZ, "BLITZ AT DUSK")["pack"]
        five = self.api.duplicate_map(BLITZ, "BLITZ")["pack"]
        self.assertEqual([one, two, three, four, five], ["BlitzAtDusk", "BlitzAtDusk2", BLITZ + "2", "BLITZATDUSK3",
                                                         "BLITZ"])
        self.assertEqual(self.listed()[0], BLITZ)
        self.assertEqual(sorted(self.listed()[1:]), sorted([one, two, three, four, five]))  # (by folder name)
        self.assertEqual(self.api.check_mod()["problems"], [])
        self.assertBuilds()
        shown = [self.copy_texts("us").text(name_to_key(f"M_D_{n}")) for n in range(31, 36)]
        self.assertEqual(sorted(shown), sorted(["Blitz at Dusk", "Blitz at Dusk", BLITZ, "BLITZ AT DUSK", "BLITZ"]))

    # FINDING F2: Duplicate map takes the copied map's own name ("Blitz") without a word, then no Test in game of the
    # map changes builds: "maps/Blitz: the map list already has an entry called like the new map; give it another
    # name" (every map of the project stopped with it). The Studio has no way to rename a new map.
    @unittest.expectedFailure
    def test_f2_a_copy_called_like_the_map_it_copies(self):
        self.api.duplicate_map(BLITZ, "Blitz at Dusk")  # the player's other work in the same map changes
        said = page_said(self.api, "duplicate_map", BLITZ, "Blitz")
        if said:  # refused at once, in words, is fine too: nothing made
            self.assertEqual(self.listed(), [BLITZ, "BlitzAtDusk"])
        self.assertBuilds()

    def test_windows_reserved_names(self):
        """Names Windows keeps for its devices, typed as a whole map name (on this PC's Windows 11 only NUL still
        refuses a folder; older Windows refuse CON, PRN, AUX and COM1-9, LPT1-9 too)."""
        for name in ("Con", "Aux", "Prn", "Com1", "Lpt1"):
            with self.subTest(name=name):
                pack = self.api.duplicate_map(BLITZ, name)["pack"]
                self.assertTrue((self.map_folder(pack) / "map.toml").is_file(), pack)

    # FINDING F1: a map called "Nul" (Windows' NUL device name) can't be made. As the first map (no map changes yet)
    # the page is told "<home>\maps\nul\maps isn't there."; in a map project already made, Duplicate map stops on its
    # pack folder maps/Nul the same way. The name is a fine one for the menus.
    @unittest.expectedFailure
    def test_f1_a_first_map_called_nul_is_made(self):
        self.assertEqual(page_said(self.api, "duplicate_map", BLITZ, "Nul"), "")
        pack = next(m["pack"] for m in self.api.maps()["maps"] if m["pack"] != BLITZ)
        self.assertTrue((self.map_folder(pack) / "map.toml").is_file())
        self.assertBuilds()

    @unittest.expectedFailure
    def test_f1_a_map_called_nul_in_a_map_project_is_made(self):
        self.api.new_mod("My maps", "map")
        self.assertEqual(page_said(self.api, "duplicate_map", BLITZ, "Nul"), "")
        self.assertBuilds()

    @unittest.expectedFailure
    def test_f1_the_first_map_changes_called_nul_are_made(self):
        self.assertEqual(page_said(self.api, "new_mod", "Nul", "map"), "")  # (no maps folder made yet)
        self.assertTrue((self.map_dir() / "mod.toml").is_file())

    def test_map_changes_called_nul_once_the_maps_folder_is_there(self):
        """The control for F1: with the maps folder already made, map changes called Nul get the folder nul-2."""
        self.api.new_mod("My maps", "map")
        self.assertEqual(page_said(self.api, "new_mod", "Nul", "map"), "")
        self.assertEqual(self.map_dir().name, "nul-2")

    def test_refusals_in_the_players_language(self):
        for lang in ("fr", "ru", "fa", "jpn"):
            self.in_lang(lang)
            said = page_said(self.api, "duplicate_map", BLITZ, "   ")
            self.assertNotEqual(said, "Give the new map a name.", lang)
            self.assertTrue(said, lang)


class Menus(MapGame):
    """Duplicate map's entries and the maps it can't copy."""

    def test_a_map_no_menu_offers(self):
        opts = self.api.duplicate_options("M01_Leipzig")
        self.assertEqual(opts["entries"], [])
        self.assertIn("No menu offers this map", opts["why"])
        with self.assertRaisesRegex(StudioError, "No menu offers this map"):
            self.api.duplicate_map("M01_Leipzig", "Leipzig Twin")
        self.assertIsNone(self.map_dir())  # nothing made for a refusal

    def test_an_entry_the_map_hasnt(self):
        with self.assertRaisesRegex(StudioError, "has no entry"):
            self.api.duplicate_map(BLITZ, "Odd", entry="(8) Nowhere")
        pack = self.api.duplicate_map(BLITZ, "Named Entry", entry=BATTLES_ENTRY)["pack"]
        self.assertNotIn("entry", self.toml(pack))  # the one BATTLES entry needn't be written

    def test_a_preset_the_studio_hasnt(self):
        with self.assertRaisesRegex(StudioError, "There's no 'blank_moon'"):
            self.api.duplicate_map(BLITZ, "Moon", preset="blank_moon")
        self.assertIsNone(self.map_dir())


if __name__ == "__main__":
    unittest.main()
