"""The economy (rusemod.economy, the Studio's Economy tab): values the game has twice (its usual game modes and the
Nuclear mode), changed in both from one value, on a made-up game."""
import struct
import tempfile
import tomllib
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat, Ndf, economy
from rusemod.build import build_pack, load_mod
from rusemod.index import build_index
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError

ROOT = Path(__file__).resolve().parents[1]
LANGS = {"us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"}
NORMAL, ATOMIC = economy.TARGETS["normal"], economy.TARGETS["atomic"]


def i32(v):
    return val(0x02, struct.pack("<i", v))


def u32(v):
    return val(0x03, struct.pack("<I", v))


def f32(v):
    return val(0x05, struct.pack("<f", v))


def flag(v):
    return val(0x00, struct.pack("<B", v))


def lst(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(items))


def floats(v) -> list[float]:
    """A built list (0x11) of float32 (0x05), back as numbers."""
    count = struct.unpack_from("<I", v.payload, 0)[0]
    return [struct.unpack_from("<f", v.payload, 4 + 8 * i + 4)[0] for i in range(count)]


PROPS = ["QteDeviseInitiale", "QteDeviseParCamion", "CheckAndCancelWaitingRequest",
         "PaliersTempsToChooseNewCardForAllianceTaille_1", "MaxProductionQueueSize", "UsePopCap",
         "MaxNbCardsPerZoneByAlliance"]


def constants(per_truck: int, card_times) -> bytes:
    """One copy of the constants as the game has it: one named object, a few of its values."""
    values = [i32(200), i32(per_truck), flag(1), lst(*(f32(t) for t in card_times)), u32(30), flag(0), i32(2)]
    return make_ndf(objects=[(0, list(enumerate(values)))], classes=["TTunableConstante"],
                    props=[(p, 0) for p in PROPS], exports={0: "GFX/Everything/Constantes"}, topo=[0])


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\gfx\\", [
        ("file", "gdconstanteatomic.cpp.gladndfbin", constants(6, (80, 160, 240))),
        ("file", "gdconstanteoriginal.cpp.gladndfbin", constants(3, (105, 210, 315)))])]))


class Labels(unittest.TestCase):
    def test_every_value_and_group_has_its_words(self):
        props = tomllib.loads((ROOT / "src" / "rusemod" / "labels.toml").read_text(encoding="utf-8"))["props"]
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        self.assertEqual(len(economy.PROPS), len(set(economy.PROPS)))
        for prop in economy.PROPS:
            with self.subTest(prop=prop):
                self.assertLessEqual(LANGS, set(props[prop]))
        for group, _props in economy.GROUPS:
            with self.subTest(group=group):
                self.assertEqual(set(words[f"economy_group_{group}"]), LANGS)
        for key in ("economy_tab", "economy_title", "economy_help", "economy_buildings", "economy_none",
                    "economy_atomic", "tip_tab_economy", "tip_economy_reset"):
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), LANGS)
        self.assertTrue(all("{v}" in text for text in words["economy_atomic"].values()))

    def test_the_tab_is_on_the_page(self):
        html = (ROOT / "src" / "ruse_studio" / "ui" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        for needle in ('id="tab-economy"', 'id="economy-view"', 'id="economy-groups"'):
            self.assertIn(needle, html)
        for needle in ("function renderEconomy", "api().economy(", "api().economy_edit(", "api().economy_reset(",
                       'showView("economy")'):
            self.assertIn(needle, app)


class Copies(unittest.TestCase):
    def test_each_copy_by_its_file(self):
        found = economy.copies([{"file": "ZZ.dat!genglad\\patchable\\gfx\\gdconstanteoriginal.cpp.gladndfbin", "n": 1},
                                {"file": "ZZ.dat!genglad\\patchable\\gfx\\gdconstanteatomic.cpp.gladndfbin", "n": 2}])
        self.assertEqual({mode: o["n"] for mode, o in found.items()}, {"normal": 1, "atomic": 2})
        self.assertEqual(economy.copies([]), {})
        self.assertEqual(NORMAL, '@TTunableConstante[file="gdconstanteoriginal"]')


class Tab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        (cls.game / "RUSE.exe").write_bytes(b"MZ")
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: True,
                          wait=lambda s: None)
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home, starter=starter,
                             instances=self.home / "copies")

    def rows(self, lang="us"):
        return {r["prop"]: r for g in self.api.economy(lang)["groups"] for r in g["rows"]}

    def test_the_values_as_the_game_has_them(self):
        page = self.api.economy("us")
        self.assertTrue(page["ready"])
        self.assertEqual([g["id"] for g in page["groups"]], [g for g, _p in economy.GROUPS])
        rows = self.rows()
        self.assertEqual(sorted(rows), sorted(p for p in PROPS if p in economy.PROPS))  # no pop cap
        money = rows["QteDeviseInitiale"]
        self.assertEqual((money["label"], money["game"], money["atomic"], money["value"], money["list"]),
                         ("Starting money", 200, None, None, False))
        self.assertEqual((rows["QteDeviseParCamion"]["game"], rows["QteDeviseParCamion"]["atomic"]), (3, 6))
        cards = rows["PaliersTempsToChooseNewCardForAllianceTaille_1"]
        self.assertEqual((cards["list"], cards["game"], cards["atomic"]), (True, [105, 210, 315], [80, 160, 240]))
        self.assertEqual(rows["CheckAndCancelWaitingRequest"]["type"], "bool")
        self.assertEqual(self.rows("base")["QteDeviseInitiale"]["label"], "QteDeviseInitiale")  # the code names

    def test_a_change_goes_to_both_copies_and_builds(self):
        with self.assertRaises(StudioError):
            self.api.economy_edit("QteDeviseInitiale", 800)  # no mod to save it in yet
        self.api.new_mod("Rich")
        folder = self.home / "mods" / "rich"
        self.assertEqual(self.api.economy_edit("QteDeviseInitiale", 812.6)["value"], 813)  # whole numbers
        self.api.economy_edit("QteDeviseParCamion", 6)  # the Nuclear mode's own value: only the usual modes change
        self.api.economy_edit("PaliersTempsToChooseNewCardForAllianceTaille_1", [60, 120, 180])
        self.api.economy_edit("CheckAndCancelWaitingRequest", 0)
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"\npatch {ATOMIC}\n(\n    CheckAndCancelWaitingRequest = 0\n"
                      "    PaliersTempsToChooseNewCardForAllianceTaille_1 = [60, 120, 180]\n"
                      "    QteDeviseInitiale = 813\n)\n", text)
        self.assertIn(f"\npatch {NORMAL}\n(\n    CheckAndCancelWaitingRequest = 0\n"
                      "    PaliersTempsToChooseNewCardForAllianceTaille_1 = [60, 120, 180]\n"
                      "    QteDeviseInitiale = 813\n    QteDeviseParCamion = 6\n)\n", text)
        rows = self.rows()
        self.assertEqual((rows["QteDeviseInitiale"]["value"], rows["QteDeviseParCamion"]["value"]), (813, 6))

        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        for name, per_truck in (("gdconstanteoriginal", 6), ("gdconstanteatomic", 6)):
            with self.subTest(copy=name):
                o = Ndf(new.read(new.find(f"{name}.cpp.gladndfbin"))).objects[0]
                self.assertEqual((o.get(0).scalar(), o.get(1).scalar(), o.get(2).scalar()), (813, per_truck, 0))
                self.assertEqual([round(x) for x in floats(o.get(3))], [60, 120, 180])
                self.assertEqual(o.get(4).scalar(), 30)  # untouched

    def test_back_to_the_game_s_value(self):
        self.api.new_mod("Rich")
        self.api.economy_edit("QteDeviseInitiale", 800)
        self.api.economy_edit("QteDeviseInitiale", 200)  # the game's own value again: no change left
        self.assertIsNone(self.rows()["QteDeviseInitiale"]["value"])
        self.api.economy_edit("QteDeviseParCamion", 9)
        self.api.economy_reset("QteDeviseParCamion")
        self.assertIsNone(self.rows()["QteDeviseParCamion"]["value"])
        text = (self.home / "mods" / "rich" / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertNotIn("patch", text)

    def test_what_is_refused(self):
        self.api.new_mod("Rich")
        for prop, value, why in (("UsePopCap", 1, "isn't one of the economy's values"),
                                 ("MaxNbCardsPerZoneByAlliance", 2, "isn't one of the economy's values"),
                                 ("NoSuchValue", 1, "isn't one of the economy's values"),
                                 ("QteDeviseInitiale", "lots", "numbers only"),
                                 ("QteDeviseInitiale", [1, 2], "one number"),
                                 ("PaliersTempsToChooseNewCardForAllianceTaille_1", [1, 2], "expected 3 numbers"),
                                 ("MaxProductionQueueSize", -1, "doesn't fit")):
            with self.subTest(prop=prop, value=value), self.assertRaisesRegex(StudioError, why):
                self.api.economy_edit(prop, value)
        self.assertFalse((self.home / "mods" / "rich" / "src" / "studio.rndf").is_file())  # nothing half-saved

    def test_more_than_two_ruses_per_sector_is_refused_in_the_build(self):
        """T37 (owner, 2026-10-06): a third ruse on one sector crashed the game; "dont want ppl messing w it yet". The
        Economy tab doesn't offer it, and the build refuses more than two from any mod (rusemod.rules ruses-per-sector)."""
        self.api.new_mod("Ruses")
        folder = self.home / "mods" / "ruses"
        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        for most, errors in ((3, 1), (2, 0), (1, 0)):
            with self.subTest(most=most):
                (folder / "src").mkdir(exist_ok=True)
                (folder / "src" / "hand.rndf").write_text(
                    f"patch {NORMAL} ( MaxNbCardsPerZoneByAlliance = {most} )\n", encoding="utf-8")
                found = [f.message for f in build_pack(arc, [load_mod(folder)]).errors]
                self.assertEqual(len(found), errors, found)
                if errors:
                    self.assertIn("hand.rndf", found[0])
                    self.assertIn("more than 2 ruse cards on one sector crashes the game", found[0])


if __name__ == "__main__":
    unittest.main()
