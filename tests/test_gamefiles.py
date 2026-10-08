"""Whole game files changed or added by a mod (rusemod.gamefiles, MOD_FORMAT §7), the safe way the owner asked for
(2026-10-08): a mod carries only a delta against the game's own file, made for that one version of it; every file is
checked as its kind before the game gets it; added files only in the mod's own folder; a later mod's version of a file
wins, and the build says so; the game's packs are never written."""
import random
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf
from rusemod import gamefiles
from rusemod.build import BuildError, build_and_write, load_mod
from rusemod.edat import Edat
from rusemod.tmst import make_tgv, zipo_pack

PIXELS = bytes([0, 0, 255, 255, 0, 255, 0, 255, 255, 0, 0, 255, 255, 255, 255, 128])
TEXTURE = make_tgv(2, 2, "A8R8G8B8_LIN", [zipo_pack(PIXELS)])
GREEN = make_tgv(2, 2, "A8R8G8B8_LIN", [zipo_pack(bytes([0, 255, 0, 255]) * 4)])
BLUE = make_tgv(2, 2, "A8R8G8B8_LIN", [zipo_pack(bytes([255, 0, 0, 255]) * 4)])
INNER = make_edat([("file", "gen\\inner\\card.tgv", TEXTURE)])
NDF = make_ndf(objects=[(0, [])], classes=["TUnit"], props=[])


def literals(delta: bytes) -> bytes:
    """What a delta carries itself (its "add" runs), unpacked."""
    body, out, p = zlib.decompress(delta[88:]), b"", 4
    for _ in range(struct.unpack_from("<I", body, 0)[0]):
        if body[p:p + 1] == b"C":
            p += 13
        else:
            n = struct.unpack_from("<I", body, p + 1)[0]
            out += body[p + 5:p + 5 + n]
            p += 5 + n
    return out


class Deltas(unittest.TestCase):
    def test_made_and_applied(self):
        rng = random.Random(7)
        base = bytes(rng.randrange(256) for _ in range(20000))
        new = base[:5000] + b"MODDED!" * 30 + base[5000:12000] + base[15000:] + b"tail"
        delta = gamefiles.make_delta(base, new)
        self.assertEqual(gamefiles.apply_delta(base, delta), new)
        self.assertLess(len(delta), 1000)  # the game's own runs aren't carried
        self.assertEqual(literals(delta), b"MODDED!" * 30 + b"tail")
        self.assertEqual(gamefiles.delta_base(delta), __import__("hashlib").sha256(base).hexdigest())
        for empty_case in ((b"", b"x"), (b"abc", b""), (base, base)):
            with self.subTest(case=len(empty_case[0])):
                self.assertEqual(gamefiles.apply_delta(empty_case[0], gamefiles.make_delta(*empty_case)), empty_case[1])

    def test_only_for_the_file_it_was_made_from(self):
        base, new = b"A" * 1000 + b"B" * 1000, b"A" * 1000 + b"C" * 1000
        delta = gamefiles.make_delta(base, new)
        with self.assertRaisesRegex(gamefiles.GameFileError, "another version of this game file"):
            gamefiles.apply_delta(base[:-1] + b"X", delta)
        broken = delta[:90] + bytes([delta[90] ^ 1]) + delta[91:]
        with self.assertRaisesRegex(gamefiles.GameFileError, "damaged"):
            gamefiles.apply_delta(base, broken)
        with self.assertRaisesRegex(gamefiles.GameFileError, "not a delta"):
            gamefiles.apply_delta(base, b"nope")


class Kinds(unittest.TestCase):
    def test_each_file_checked_as_its_kind(self):
        from rusemod.dxt import png_bytes
        self.assertEqual(gamefiles.check_kind("gen/a.tgv", TEXTURE), "texture")
        self.assertEqual(gamefiles.check_kind("gen/a.png", png_bytes(b"\0\0\0", 1, 1)), "picture")
        self.assertEqual(gamefiles.check_kind("a/b.gladndfbin", NDF), "game data")
        self.assertEqual(gamefiles.check_kind("a/b.xml", b"<a><b/></a>"), "XML text")
        for path, data, why in (("gen/a.tgv", TEXTURE[:40], "isn't a good texture"),
                                ("a/b.dic", b"nope", "isn't a good text table"),
                                ("a/b.xml", b"<a>", "isn't a good XML text"),
                                ("v/x.webm", b"x", "isn't set up yet"), ("ui/menu.gfx", b"x", "not a Flash menu"),
                                ("v/x.bik", b"x", "can't be checked by the build yet"),
                                ("genpython/a.xyz", b"x", "holds code"),
                                ("gen_sound/a.ess", b"x", "Music tab")):
            with self.subTest(path=path), self.assertRaisesRegex(gamefiles.GameFileError, why):
                gamefiles.check_kind(path, data)
        with mock.patch.object(gamefiles, "FILE_MOST", 10), self.assertRaisesRegex(gamefiles.GameFileError, "at most"):
            gamefiles.check_kind("gen/a.tgv", TEXTURE)


def write_game(root: Path) -> Path:
    game = root / "game"
    rev = game / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "genglad\\patchable\\gfx\\x.gladndfbin", NDF)]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "gen\\", [("file", "flag.tgv", TEXTURE),
                                                                    ("file", "menu.ppk", INNER)])]))
    (game / "RUSE.exe").write_bytes(b"MZ")
    return game


def make_mod(root: Path, mod_id: str, files: dict) -> Path:
    mod = root / mod_id
    (mod / "src").mkdir(parents=True)
    (mod / "mod.toml").write_text(f'[mod]\nid = "{mod_id}"\nversion = "0.1.0"\n', encoding="utf-8")
    for rel, data in files.items():
        f = mod / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
    return mod


class InAMod(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = write_game(self.root)
        self.before = {p: p.read_bytes() for p in self.game.rglob("*.dat")}

    def tearDown(self):
        self.assertEqual({p: p.read_bytes() for p in self.game.rglob("*.dat")}, self.before)  # never written
        self.tmp.cleanup()

    def built(self, *mods):
        lines = []
        result = build_and_write(self.game, [load_mod(m) for m in mods], out=self.root / "out", say=lines.append)
        zz = self.root / "out" / "ZZ_Win.dat"
        arc = Edat(zz.read_bytes()) if zz.is_file() else None
        return result, lines, arc

    def test_read_from_the_mod(self):
        delta = gamefiles.make_delta(TEXTURE, GREEN)
        mod = make_mod(self.root, "paint", {"files/game/ZZ_Win.dat/gen/flag.tgv.rdelta": delta,
                                            "files/game/ZZ_Win.dat/mods/paint/new.tgv": BLUE})
        found = load_mod(mod)[0].game_files
        self.assertEqual([(g.pack, g.path, g.added) for g in found],
                         [("ZZ_Win.dat", "gen/flag.tgv", False), ("ZZ_Win.dat", "mods/paint/new.tgv", True)])
        for rel, data, why in (("files/game/ZZ_Win.dat/gen/new.tgv", BLUE, "its own folder in the pack"),
                               ("files/game/ZZ_Win.dat/mods/other/new.tgv", BLUE, "its own folder"),
                               ("files/game/ZZ_Win.dat/mods/bad/x.bik", b"x", "can't be checked"),
                               ("files/game/ZZ_Win.dat/gen/x.xyz.rdelta", delta, "holds code"),
                               ("files/game/flag.tgv.rdelta", delta, "files/game/<the game's pack>"),
                               ("files/game/ZZ_Win.dat/gen/flag.tgv.rdelta", b"not a delta", "not a delta")):
            with self.subTest(rel=rel), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(BuildError, why):
                    load_mod(make_mod(Path(tmp), "bad", {rel: data}))
        with mock.patch.object(gamefiles, "MOD_MOST", 100), self.assertRaisesRegex(BuildError, "more than"):
            load_mod(mod)

    def test_built_into_the_copy(self):
        mod = make_mod(self.root, "paint", {
            "files/game/ZZ_Win.dat/gen/flag.tgv.rdelta": gamefiles.make_delta(TEXTURE, GREEN),
            "files/game/ZZ_Win.dat/gen/menu.ppk/gen/inner/card.tgv.rdelta": gamefiles.make_delta(TEXTURE, BLUE),
            "files/game/ZZ_Win.dat/mods/paint/new.tgv": BLUE})
        result, lines, arc = self.built(mod)
        self.assertEqual(result.errors, [], lines)
        got = {e.path: bytes(arc.read(e)) for e in arc.entries}
        self.assertEqual(got["gen\\flag.tgv"], GREEN)
        inner = Edat(got["gen\\menu.ppk"])
        self.assertEqual(bytes(inner.read(inner.entry("gen\\inner\\card.tgv"))), BLUE)
        self.assertIn("game file: ZZ_Win.dat: mods/paint/new.tgv (added, from paint)", lines)
        self.assertIsNotNone(result.fingerprint)

    def test_value_patches_go_on_top_of_a_changed_game_data_file(self):
        # (point 6 of the owner's 2026-10-08 list was skipped: a whole data file and value patches go together, the
        # file first, whatever the order of the mods)
        from test_build import NDF as UNITS_NDF, PACK as UNITS_PACK, ints, price, write_mod
        (self.game / "Data/PC/190852/ZZ_GladPatchableWin.dat").write_bytes(UNITS_PACK)
        self.before = {p: p.read_bytes() for p in self.game.rglob("*.dat")}
        dearer = make_ndf(objects=[(0, [(0, ints([200] * 5))])], classes=["TBatimentDescriptor"],
                          props=[("ProductionPrice", 0)], exports={0: "B"}, compress=True)
        data = make_mod(self.root, "dearer", {
            "files/game/ZZ_GladPatchableWin.dat/genglad/patchable/gfx/everything.cpp.gladndfbin.rdelta":
                gamefiles.make_delta(UNITS_NDF, dearer)})
        half = write_mod(self.root, "half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        for order in ((data, half), (half, data)):
            with self.subTest(order=[m.name for m in order]):
                lines = []
                result = build_and_write(self.game, [load_mod(m) for m in order], out=self.root / "out",
                                         say=lines.append)
                self.assertEqual(result.errors, [], lines)
                self.assertEqual(price((self.root / "out" / "ZZ_GladPatchableWin.dat").read_bytes()), [100] * 5)

    def test_two_mods_one_file_the_lower_wins_and_the_build_says_so(self):
        a = make_mod(self.root, "aaa", {"files/game/ZZ_Win.dat/gen/flag.tgv.rdelta": gamefiles.make_delta(TEXTURE, GREEN)})
        b = make_mod(self.root, "bbb", {"files/game/ZZ_Win.dat/gen/flag.tgv.rdelta": gamefiles.make_delta(TEXTURE, BLUE)})
        result, lines, arc = self.built(a, b)
        self.assertEqual(result.errors, [])
        self.assertEqual(bytes(arc.read(arc.entry("gen\\flag.tgv"))), BLUE)
        self.assertTrue(any("aaa and bbb both change ZZ_Win.dat: gen/flag.tgv; bbb's is used" in f.message
                            and "put aaa below bbb" in f.message for f in result.findings), result.findings)

    def test_the_files_two_mods_change_are_found_without_reading_them(self):
        # what the Launcher shows before Play, with "Use the one from <mod>" (the owner, 2026-10-08: "give a solution")
        a = make_mod(self.root, "aaa", {"files/game/ZZ_Win.dat/gen/flag.tgv.rdelta": b"x",
                                        "files/game/ZZ_Win.dat/mods/aaa/new.tgv": b"x"})
        b = make_mod(self.root, "bbb", {"files/game/zz_win.dat/GEN/Flag.tgv.rdelta": b"x"})
        c = make_mod(self.root, "ccc", {"files/game/ZZ_Win.dat/gen/flag.tgv.rdelta": b"x",
                                        "files/game/ZZ_Win.dat/gen/other.tgv.rdelta": b"x"})
        self.assertEqual(gamefiles.touched(a), {("zz_win.dat", "gen/flag.tgv"): "ZZ_Win.dat: gen/flag.tgv",
                                                ("zz_win.dat", "mods/aaa/new.tgv"): "ZZ_Win.dat: mods/aaa/new.tgv"})
        self.assertEqual(gamefiles.overlaps([("A", a), ("B", b), ("C", c)]),
                         [{"file": "ZZ_Win.dat: gen/flag.tgv", "a": "A", "b": "C"},
                          {"file": "ZZ_Win.dat: gen/flag.tgv", "a": "B", "b": "C"}])
        self.assertEqual(gamefiles.overlaps([("A", a), ("C", c), ("B", b)])[-1]["b"], "B")
        self.assertEqual(gamefiles.overlaps([("C", c), ("X", self.root / "no-such-mod")]), [])

    def test_a_game_update_or_a_bad_result_stops_the_build(self):
        other = make_mod(self.root, "old", {
            "files/game/ZZ_Win.dat/gen/flag.tgv.rdelta": gamefiles.make_delta(TEXTURE[:-4] + b"OLD!", GREEN)})
        result, lines, _arc = self.built(other)
        self.assertTrue(any("another version of this game file" in f.message for f in result.errors), result.findings)
        self.assertIn("Nothing was written.", lines)
        broken = make_mod(self.root, "broken", {
            "files/game/ZZ_Win.dat/gen/flag.tgv.rdelta": gamefiles.make_delta(TEXTURE, TEXTURE[:40])})
        result, _lines, _arc = self.built(broken)
        self.assertTrue(any("isn't a good texture" in f.message for f in result.errors), result.findings)
        missing = make_mod(self.root, "missing", {
            "files/game/ZZ_Win.dat/gen/none.tgv.rdelta": gamefiles.make_delta(TEXTURE, GREEN)})
        result, _lines, _arc = self.built(missing)
        self.assertTrue(any("the game has no gen\\none.tgv" in f.message for f in result.errors), result.findings)


if __name__ == "__main__":
    unittest.main()
