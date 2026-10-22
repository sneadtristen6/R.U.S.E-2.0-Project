"""The economy (rusemod.economy, the Studio's Economy tab): values the game has twice (its usual game modes and the
Nuclear mode), changed in both from one value, or in one mode (shown apart where the two differ), on a made-up game."""
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
         "MaxNbCardsPerZoneByAlliance", "NbCamionParConvoi"]


def constants(per_truck: int, card_times) -> bytes:
    """One copy of the constants as the game has it: one named object, a few of its values."""
    values = [i32(200), i32(per_truck), flag(1), lst(*(f32(t) for t in card_times)), u32(30), flag(0), i32(2), i32(3)]
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
        for key in ("play_players_title", "economy_help", "economy_buildings", "economy_none",
                    "economy_normal", "economy_nuclear", "tip_economy_normal", "tip_economy_nuclear",
                    "tip_economy_reset", "tip_economy_reset_one", "economy_depot_money",
                    "tip_economy_depot"):
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), LANGS)
        self.assertTrue(all("{trucks}" in text and "{money}" in text for text in words["economy_depot_money"].values()))

    def test_every_value_is_explained_in_every_language(self):
        """The number guide (rusemod/numberinfo.toml) says what each economy value does, in all ten languages: the
        Economy tab writes it under the value's name (as the AI tab does)."""
        from rusemod import numberinfo
        english = numberinfo.guide("us")
        for lang in LANGS:
            guide = numberinfo.guide(lang)
            for prop in economy.PROPS:
                with self.subTest(lang=lang, prop=prop):
                    self.assertIn(prop, guide)
                    self.assertTrue(guide[prop]["what"] and guide[prop]["does"])
                    if lang != "us":  # its own words, not the English fallen back to
                        self.assertNotEqual(guide[prop]["does"], english[prop]["does"])

    def test_the_tab_is_on_the_page(self):
        # the first half of AI and player settings since 2026-10-22 (the owner: "the economy AI and just those settings
        # should be in one comprehensive name"): its own tab is gone, its computer players' groups are in the second half
        html = (ROOT / "src" / "ruse_studio" / "ui" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        for needle in ('id="economy-groups"', 'id="ai-economy-groups"', 'id="play-players-title"'):
            self.assertIn(needle, html)
        for needle in ('id="tab-economy"', 'id="economy-view"'):
            self.assertNotIn(needle, html)
        for needle in ("function renderEconomy", "api().economy(", "api().economy_edit(", "api().economy_reset(",
                       'const ECONOMY_AI_GROUPS = ["computer", "decoys"]', "function renderPlay"):
            self.assertIn(needle, app)
        self.assertLessEqual({"computer", "decoys"}, {g for g, _props in economy.GROUPS})  # the groups the page moves


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
        # Normal and Nuclear apart where the game has them apart; one value for both elsewhere
        self.assertEqual({p for p, r in rows.items() if r["split"]},
                         {"QteDeviseParCamion", "PaliersTempsToChooseNewCardForAllianceTaille_1"})
        self.assertEqual((money["split"], money["atomic_value"]), (False, None))
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

    def test_one_mode_at_a_time(self):
        """The owner, 2026-10-17: "separate normal and nuclear for sure". A value changed for the Nuclear mode only
        (or the usual modes only) goes to that copy alone, and the tab shows the two apart from then on."""
        self.api.new_mod("Rich")
        folder = self.home / "mods" / "rich"
        self.assertEqual(self.api.economy_edit("QteDeviseParCamion", 9, "atomic")["value"], 9)
        self.api.economy_edit("QteDeviseInitiale", 300, "atomic")  # the same in both in the game: apart now
        self.api.economy_edit("PaliersTempsToChooseNewCardForAllianceTaille_1", [100, 200, 300], "normal")
        rows = self.rows()
        per_truck, money = rows["QteDeviseParCamion"], rows["QteDeviseInitiale"]
        self.assertEqual((per_truck["split"], per_truck["value"], per_truck["atomic_value"]), (True, None, 9))
        self.assertEqual((money["split"], money["value"], money["atomic_value"]), (True, None, 300))
        cards = rows["PaliersTempsToChooseNewCardForAllianceTaille_1"]
        self.assertEqual((cards["value"], cards["atomic_value"]), ([100, 200, 300], None))
        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        for name, start, per_truck_, cards_ in (("gdconstanteoriginal", 200, 3, [100, 200, 300]),
                                                ("gdconstanteatomic", 300, 9, [80, 160, 240])):
            with self.subTest(copy=name):
                o = Ndf(new.read(new.find(f"{name}.cpp.gladndfbin"))).objects[0]
                self.assertEqual((o.get(0).scalar(), o.get(1).scalar()), (start, per_truck_))
                self.assertEqual([round(x) for x in floats(o.get(3))], cards_)
        self.api.economy_reset("QteDeviseInitiale", "atomic")  # one mode's change out: the same in both again
        self.assertEqual((self.rows()["QteDeviseInitiale"]["split"], self.rows()["QteDeviseInitiale"]["value"]),
                         (False, None))
        self.assertEqual(self.rows()["QteDeviseParCamion"]["atomic_value"], 9)  # the other values keep theirs
        with self.assertRaisesRegex(StudioError, "isn't a game mode"):
            self.api.economy_edit("QteDeviseInitiale", 300, "1945")
        with self.assertRaisesRegex(StudioError, "isn't a game mode"):
            self.api.economy_reset("QteDeviseInitiale", "1945")

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

    def test_what_a_depot_holds(self):
        """The Maps tab's depots and the Economy tab's line (the owner, 2026-10-10: "no way to increase max amt of
        money in supply depot"): a depot holds about its trucks x the trucks in a convoy x the money each truck
        brings, with the mod's values where it changes them, else the game's."""
        m = self.api.depot_money()
        self.assertEqual((m["ready"], m["per_truck"], m["per_convoy"], m["usual"], m["shipped"], m["most"]),
                         (True, 3, 3, 25, [15, 72], 2 ** 31 - 1))
        self.api.new_mod("Rich")
        self.api.economy_edit("QteDeviseParCamion", 10)
        m = self.api.depot_money()
        self.assertEqual((m["per_truck"], m["per_truck_mine"], m["per_convoy"], m["per_convoy_mine"]), (10, True, 3, False))

    def test_depots_on_the_maps(self):
        """The Economy tab's Depots on the maps: every depot on all maps, or on one map picked, kept in the mod's
        depots.toml (the build sets each depot's trucks by it: test_build.DepotsOnTheMaps)."""
        with self.assertRaisesRegex(StudioError, "Pick or make a mod"):
            self.api.economy_depots_set("all", None, 2)
        self.assertEqual(self.api.economy_depots()["rules"], [])
        self.api.new_mod("Rich")
        file = self.home / "mods" / "rich" / "depots.toml"
        self.api.economy_depots_set("all", None, 2)
        page = self.api.economy_depots_set("M04_Cotentin", 60)
        self.assertEqual([(r["map"], r["trucks"], r["times"]) for r in page["rules"]],
                         [("all", None, 2.0), ("M04_Cotentin", 60, None)])  # all maps first
        self.assertTrue(page["can"])
        self.assertEqual(page["money"]["usual"], 25)
        self.assertIn("[all]\ntimes = 2.0\n\n[maps.M04_Cotentin]\ntrucks = 60\n", file.read_text(encoding="utf-8"))
        self.assertEqual(self.api.depot_money("m04_cotentin")["rule"], {"map": "m04_cotentin", "trucks": 60, "times": None})
        self.assertEqual(self.api.depot_money("Blitz")["rule"]["times"], 2.0)  # every other map: all maps'
        self.api.economy_depots_set("m04_cotentin", 80)  # the same map, any case: replaced
        self.assertEqual([r["trucks"] for r in self.api.economy_depots()["rules"]], [None, 80])
        for where, trucks, times, why in (("D Day", 5, None, "pack name"), ("all", 5, 2, "not both"),
                                          ("all", None, -1, "0 or more"), ("all", 2 ** 31, None, "whole number")):
            with self.subTest(where=where, trucks=trucks, times=times), self.assertRaisesRegex(StudioError, why):
                self.api.economy_depots_set(where, trucks, times)
        self.api.economy_depots_set("all")
        self.api.economy_depots_set("M04_Cotentin")  # taken off: no rule left, no file
        self.assertFalse(file.exists())

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
