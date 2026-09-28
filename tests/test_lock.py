"""Fingerprints and join codes (MOD_FORMAT §12)."""
import unittest

from fixtures import make_ndf
from rusemod.lock import (CodeError, decode_join_code, encode_join_code, fingerprint, fingerprint_text, is_gameplay)

NDF = make_ndf(objects=[(0, [])], classes=["T"], props=[])
NDF_PACKED = make_ndf(objects=[(0, [])], classes=["T"], props=[], compress=True)
MODS = [("ruse2-core", "0.4.1"), ("better-ai", "1.2.0"), ("cheap-bunkers", "0.1.0")]


class Fingerprint(unittest.TestCase):
    def test_same_content_same_fingerprint_in_any_order_and_spelling(self):
        a = fingerprint("24687178", {"GenGlad\\Patchable\\A.ndfbin": NDF, "b.scenario": b"x"})
        b = fingerprint("24687178", {"b.scenario": b"x", "genglad/patchable/a.ndfbin": NDF})
        self.assertEqual(a, b)

    def test_compression_doesnt_matter_for_ndf(self):
        self.assertEqual(fingerprint("1", {"a.ndfbin": NDF}), fingerprint("1", {"a.ndfbin": NDF_PACKED}))

    def test_cosmetic_files_are_left_out(self):
        self.assertEqual(fingerprint("1", {"a.ndfbin": NDF}),
                         fingerprint("1", {"a.ndfbin": NDF, "gfx/tank.tgv": b"skin", "loc/us/units.dic": b"TRA"}))

    def test_gameplay_changes_build_and_deletes_all_count(self):
        base = fingerprint("1", {"a.ndfbin": NDF})
        self.assertNotEqual(base, fingerprint("2", {"a.ndfbin": NDF}))
        self.assertNotEqual(base, fingerprint("1", {"a.ndfbin": NDF, "b.scenario": b"x"}))
        self.assertNotEqual(base, fingerprint("1", {"a.ndfbin": None}))

    def test_vanilla_has_one_too(self):
        self.assertEqual(fingerprint("24687178", {}), fingerprint("24687178", {}))
        self.assertRegex(fingerprint_text(fingerprint("24687178", {})), r"^[0-9A-HJKMNP-TV-Z]{4}-[0-9A-HJKMNP-TV-Z]{4}$")

    def test_what_counts_as_gameplay(self):
        for p in ["x.gladndfbin", "a.scenario", "mapinfo.win", "Maps/PC/DataMapAlpha_v09.dat/tex.tgv", "eugen.ipk",
                  "something.unknown"]:
            self.assertTrue(is_gameplay(p), p)
        for p in ["tank.tgv", "tank.spk", "boom.ess", "intro.webm", "units.dic"]:
            self.assertFalse(is_gameplay(p), p)


class JoinCodes(unittest.TestCase):
    def setUp(self):
        self.fp = fingerprint("24687178", {"a.ndfbin": NDF})

    def test_round_trip(self):
        code = decode_join_code(encode_join_code("24687178", self.fp, MODS))
        self.assertEqual((code.build_id, code.mods), (24687178, MODS))
        self.assertTrue(code.matches(self.fp))
        self.assertFalse(code.matches(fingerprint("24687178", {})))

    def test_lengths_match_the_spec(self):  # MOD_FORMAT §12: about 60 / 110 / 260 characters
        ids = [(f"mod-{i:05d}", "1.0.0") for i in range(10)]  # 10-letter ids
        self.assertLessEqual(len(encode_join_code(1, self.fp, ids[:1])), 65)
        self.assertLessEqual(len(encode_join_code(1, self.fp, ids[:3])), 115)
        self.assertLessEqual(len(encode_join_code(1, self.fp, ids)), 265)

    def test_forgiving_about_case_spaces_and_lookalike_letters(self):
        code = encode_join_code("24687178", self.fp, MODS)
        messy = " " + code.lower().replace("1", "l").replace("0", "o") + " \n"
        self.assertEqual(decode_join_code(messy).mods, MODS)

    def test_typos_and_cut_off_pastes_are_caught(self):
        code = encode_join_code("24687178", self.fp, MODS)
        flipped = code[:20] + ("A" if code[20] != "A" else "B") + code[21:]
        for bad in [flipped, code[:-5]]:
            with self.assertRaisesRegex(CodeError, "damaged or cut off"):
                decode_join_code(bad)

    def test_not_a_code(self):
        with self.assertRaisesRegex(CodeError, "isn't a R.U.S.E. join code"):
            decode_join_code("hello")
        with self.assertRaisesRegex(CodeError, "characters that don't belong"):
            decode_join_code("RUSE1:ABC!")


if __name__ == "__main__":
    unittest.main()
