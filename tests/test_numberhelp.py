"""The number guide (rusemod.numberinfo; the owner, 2026-10-15: "We need to know everything that has a number behind
it that relates to these units and buildings", "Include all numbers"): every number of the game's units and buildings
and of the parts they own or link to has an entry (tests/data/unit_numbers.tsv: each class and property, read from
the game's data of build 24670294), its unit shows in plain units, and the page has its words. No game files
needed."""
import math
import tomllib
import unittest
from pathlib import Path

from rusemod import numberinfo

ROOT = Path(__file__).resolve().parents[1]


class Guide(unittest.TestCase):
    def test_every_number_of_the_game_s_units_has_an_entry(self):
        pairs = [line.split("\t") for line in (ROOT / "tests" / "data" / "unit_numbers.tsv").read_text(
            encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual(len(pairs), 378)
        missing = [f"{c}.{p}" for c, p in pairs if numberinfo.lookup(c, p) is None]
        self.assertEqual(missing, [])

    def test_each_entry_says_what_it_is_and_how_to_read_it(self):
        units = {"m", "kmh", "kmh_air", "accel", "s", "deg", "degs", "money", "pts", "count", "times", "share",
                 "level", "choice", "yesno", "id", "mask", "frame", "raw"}
        for key, e in numberinfo.guide().items():
            with self.subTest(key=key):
                self.assertIn(e["group"], numberinfo.GROUPS)
                self.assertIn(e["unit"], units)
                self.assertIn(e["sure"], numberinfo.SURE)
                self.assertTrue(e["what"] and e["does"])

    def test_looks_only_ones_say_so(self):
        for key, e in numberinfo.guide().items():
            if e["group"] in ("looks", "sound") and e["unit"] not in ("mask",):
                with self.subTest(key=key):
                    self.assertTrue(e["does"].startswith(("Looks only", "Sound only", "Bits", "Which", "What",
                                                          "1:", "How")), e["does"])

    def test_every_language_explains_every_number(self):
        from rusemod import schema
        root = Path(numberinfo.__file__).parent
        english = numberinfo.guide("us")
        for lang in schema.LANGS:
            if lang == "us":
                continue
            with self.subTest(lang=lang):
                own = tomllib.loads((root / f"numberinfo_{lang}.toml").read_text(encoding="utf-8"))
                self.assertEqual(sorted(own), sorted(english))
                for key in english:
                    for text in numberinfo.TEXTS:
                        self.assertTrue(own[key].get(text), (lang, key, text))
                g = numberinfo.guide(lang)
                self.assertNotEqual(g["SeuilMort"]["does"], english["SeuilMort"]["does"])
                self.assertEqual(g["SeuilMort"]["unit"], english["SeuilMort"]["unit"])  # unit and sure stay English's

    def test_a_class_s_own_meaning_comes_first(self):
        self.assertEqual(numberinfo.lookup("TAvionDescriptor", "VitesseLineaire")["unit"], "kmh_air")
        self.assertEqual(numberinfo.lookup("TUniteAuSolDescriptor", "VitesseLineaire")["unit"], "kmh")
        self.assertIsNone(numberinfo.lookup("TUniteAuSolDescriptor", "NoSuchThing"))

    def test_plain_units(self):
        self.assertAlmostEqual(numberinfo.plain("m", 104000), 400)
        self.assertAlmostEqual(numberinfo.plain("kmh", 4550), 35)
        self.assertAlmostEqual(numberinfo.plain("deg", math.pi), 180)
        self.assertAlmostEqual(numberinfo.plain("share", 0.6), 60)
        self.assertIsNone(numberinfo.plain("pts", 400))


class Page(unittest.TestCase):
    def test_the_words_and_the_page(self):
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        for key in ("number_about_value", "unit_m", "unit_kmh", "unit_ms2", "unit_deg", "unit_degs", "unit_s",
                    "unit_money", "unit_pct", "number_base", "number_from_base", "number_slider", "tip_number_slider",
                    "number_this_unit", "number_among", "number_scale_unmeasured",
                    *[f"number_sure_{s}" for s in numberinfo.SURE]):
            self.assertEqual(len(words[key]), 10, key)
        app = (ROOT / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        for needle in ("numberHelp(u, r, th, cell", "api().number_scale(", "api().numbers(", "base-slider"):
            self.assertIn(needle, app)
        fake = (ROOT / "src" / "ruse_studio" / "ui" / "fake-api.js").read_text(encoding="utf-8")
        for needle in ("numbers: async", "number_scale: async"):
            self.assertIn(needle, fake)


if __name__ == "__main__":
    unittest.main()
