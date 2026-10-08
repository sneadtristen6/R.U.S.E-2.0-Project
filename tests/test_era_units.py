"""Era units in the Units tab (ruse_studio.era_units) on the Studio tests' made-up game: the library read from
RUSE_ERA_UNITS, an era's units listed and filtered like the Units list, every one out of the mod until added, an era
unit's page with the game units it can start from (the suggestion first), adding one from the suggestion or from
another unit with its own name and price, its credit in the mod's CREDITS-era-units.md, the same name in two eras,
taking it out again."""
import json
import os
import tempfile
import unittest
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
            self.assertEqual(self.api.era_units_list("WWI"), {"library": False, "types": [], "units": []})


if __name__ == "__main__":
    unittest.main()
