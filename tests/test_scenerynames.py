"""English names for the map's scenery types (rusemod.scenerynames). The owner, 2026-10-03: the Props tab's
"Cotentin_PanierOsier ... what is that? ... They're all in French ... this has to be more detailed." Every
type the shipped maps offer to place (tests/scenery_types.txt, read from all 32 maps) must read in English."""
import unittest
from pathlib import Path

from rusemod.scenerynames import kind, plain, unknown

TYPES = [line.split("\t") for line in (Path(__file__).parent / "scenery_types.txt").read_text(encoding="utf-8").splitlines()
         if line and not line.startswith("#")]


class EveryType(unittest.TestCase):
    def test_every_word_of_every_type_has_its_english(self):
        missing = {name: unknown(name) for name, _cat in TYPES if unknown(name)}
        self.assertEqual(missing, {}, "a scenery type's word with no English in rusemod.scenerynames.WORDS")
        self.assertGreater(len(TYPES), 1000)

    def test_every_type_says_what_it_is(self):
        self.assertEqual([name for name, cat in TYPES if not kind(cat)], [])

    def test_names_read_in_english(self):
        self.assertEqual(plain("Cotentin_PanierOsier1"), "Wicker basket 1 (Cotentin)")
        self.assertEqual(plain("Bouleau_02_G"), "Birch 2, winter look")
        self.assertEqual(plain("BuissonSec04_France"), "Dry bush 4 (France)")
        self.assertEqual(plain("ChampsPierres_02"), "Stony field 2")
        self.assertEqual(plain("RocherNormandie_03"), "Rock 3 (Normandy)")
        self.assertEqual(plain("borne_incendie_g"), "Fire hydrant, winter look")
        self.assertEqual(plain("AbreuvoirEnBois"), "Wooden drinking trough")
        self.assertEqual(kind("Vegetation/Arbres"), "tree")
        self.assertEqual(kind("Props/Ville/Cimetiere"), "cemetery")


if __name__ == "__main__":
    unittest.main()
