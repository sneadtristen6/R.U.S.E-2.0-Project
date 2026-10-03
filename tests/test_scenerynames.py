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


class EveryLanguage(unittest.TestCase):
    """The owner, 2026-10-03: "just quickly make it all languages. Make a switch with the language thing." The names
    are in each of the Studio's ten languages, the Place list showing the Studio's own."""

    def test_every_english_word_has_all_nine_others(self):
        from rusemod import scenerynames as s
        from rusemod.scenerynames_lang import KEPT, LANGS, table
        t = table()
        used = set(s.PHRASES.values()) | set(s.WORDS.values()) | set(s.REGIONS.values()) | {k for _, k in s.KINDS}
        used = {w for w in used if w} | {"winter look"}
        self.assertEqual(sorted(w for w in used if w not in t and w not in KEPT), [])
        self.assertEqual(sorted(w for w in t if w not in used), [], "a row no name uses")
        self.assertEqual([w for w, row in t.items() if any(not row[lang] for lang in LANGS)], [])

    def test_names_in_each_language(self):
        from rusemod.scenerynames import LANGS, kinds, names
        self.assertEqual(len(LANGS), 10)
        n = names("Cotentin_PanierOsier1")
        self.assertEqual(sorted(n), sorted(LANGS))
        self.assertEqual((n["us"], n["fr"], n["ger"], n["ru"]), ("Wicker basket 1 (Cotentin)", "Panier en osier 1 (Cotentin)",
                                                                 "Weidenkorb 1 (Cotentin)", "Плетёная корзина 1 (Cotentin)"))
        self.assertEqual(plain("BuissonSec04_France", lang="fr"), "Buisson sec 4 (France)")  # the noun, then its adjective
        self.assertEqual(plain("BuissonSec04_France", lang="pol"), "Suchy krzak 4 (Francja)")
        self.assertEqual(plain("Bouleau_02_G", lang="ita"), "Betulla 2, aspetto invernale")
        self.assertEqual(plain("Caillou_10", lang="jpn"), "小石10")
        self.assertEqual(plain("Caillou_10", lang="base"), "Pebble 10")  # the game's own names: these have none
        self.assertEqual(kinds("Vegetation/Arbres")["spa"], "árbol")
        self.assertTrue(all(names(name, cat)["sc"] for name, cat in TYPES))


if __name__ == "__main__":
    unittest.main()
