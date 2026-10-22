"""The improved computer player (rusemod.ai.IMPROVED, StudioApi.ai_improved, AI and player settings; the owner's AI
test 5 on Hard, 2026-10-22: "test worked well"): a difficulty given it attacks whatever the odds, never buys artillery
and starts with extra money; shown, written, built and taken out again, on a made-up game that has the values as the
game lays them out (the attack factors on every difficulty, only Hard's start money, the Howitzer's artillery
weight, Blitzkrieg's own attack factor)."""
import math
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf
from test_ai import f32, i32, key, lst, ref
from test_dic import make_dic
from rusemod import Edat, Ndf, ai
from rusemod.build import build_pack, load_mod
from rusemod.dic import name_to_key
from rusemod.index import build_index
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError

CLASSES = ["TIAProfilList", "TAIConfigurationList", "TAIConfiguration", "TIAProfil"]
PROPS = [("DefaultAndDifficultyAndProfil", 0), ("Items", 1), ("Name", 2), ("OverridenParams", 2),
         ("MissionFacteurLancementAttaque", 3), ("MissionFacteurEnoughToDestroy", 3), ("DeviseBonusIA", 3),
         ("BonusUnitesArtillerie", 3)]
P = {name: i for i, (name, _c) in enumerate(PROPS)}
LISTS = "$/GFX/Everything/AIConfiguration"
DEFAULT = f"{LISTS}:DefaultAndDifficultyAndProfil[0].Items[class=TAIConfiguration].OverridenParams"
EASY, HARD = f"{LISTS}/AIDifficultyList:Items[0].OverridenParams", f"{LISTS}/AIDifficultyList:Items[1].OverridenParams"
REGULAR = f"{LISTS}/AIDescriptorList:Items[0].OverridenParams"
TEXTS = {"us": {"EASY": "Easy", "HARD": "Hard", "PROFILE_0": "Regular", "PROFILE_5": "Howitzer",
                "PROFILE_7": "Blitzkrieg", "NAME_AI": "AI", "BtnAIDiff": "Difficulty", "BtnAIType": "Profile"}}


def everything(howitzer: bool = True) -> bytes:
    """Default, Easy and Hard, and three personalities: Regular (Default's factors), Howitzer (Default's factors and
    its own artillery weight; left out with howitzer=False, so no profile in the file uses that name) and Blitzkrieg
    (its own factors). Like the game's, each personality lists both factors: one a set doesn't list counts as 0, and
    a 0 that isn't Default's would win over the difficulty's."""
    personalities = [ref(10, 2)] + ([ref(12, 2)] if howitzer else []) + [ref(14, 2)]
    objects = [
        (0, [(P["DefaultAndDifficultyAndProfil"], lst(ref(1, 1), ref(4, 1), ref(9, 1)))]),      # 0 the profile list
        (1, [(P["Items"], lst(ref(2, 2)))]),                                                     # 1 Default's list
        (2, [(P["Name"], key("DEFAUT")), (P["OverridenParams"], ref(3, 3))]),                    # 2
        (3, [(P["MissionFacteurLancementAttaque"], f32(0.7)),                                    # 3 Default
             (P["MissionFacteurEnoughToDestroy"], f32(1.2))]),
        (1, [(P["Items"], lst(ref(5, 2), ref(7, 2)))]),                                          # 4 the difficulties
        (2, [(P["Name"], key("EASY")), (P["OverridenParams"], ref(6, 3))]),                      # 5
        (3, [(P["MissionFacteurLancementAttaque"], f32(0.2)),                                    # 6 Easy
             (P["MissionFacteurEnoughToDestroy"], f32(0.2))]),
        (2, [(P["Name"], key("HARD")), (P["OverridenParams"], ref(8, 3))]),                      # 7
        (3, [(P["MissionFacteurLancementAttaque"], f32(0.9)),                                    # 8 Hard
             (P["MissionFacteurEnoughToDestroy"], f32(1.8)), (P["DeviseBonusIA"], i32(150))]),
        (1, [(P["Items"], lst(*personalities))]),                                                # 9 the personalities
        (2, [(P["Name"], key("PROFILE_0")), (P["OverridenParams"], ref(11, 3))]),                # 10
        (3, [(P["MissionFacteurLancementAttaque"], f32(0.7)),                                    # 11 Regular
             (P["MissionFacteurEnoughToDestroy"], f32(1.2))]),
        (2, [(P["Name"], key("PROFILE_5")), (P["OverridenParams"], ref(13, 3))]),                # 12
        (3, [(P["MissionFacteurLancementAttaque"], f32(0.7)),                                    # 13 Howitzer
             (P["MissionFacteurEnoughToDestroy"], f32(1.2))]
         + ([(P["BonusUnitesArtillerie"], f32(8000))] if howitzer else [])),
        (2, [(P["Name"], key("PROFILE_7")), (P["OverridenParams"], ref(15, 3))]),                # 14
        (3, [(P["MissionFacteurLancementAttaque"], f32(0.2)),                                    # 15 Blitzkrieg
             (P["MissionFacteurEnoughToDestroy"], f32(1.5))]),
    ]
    return make_ndf(objects=objects, classes=CLASSES, props=PROPS, strings=[],
                    exports={0: "GFX/Everything/AIConfiguration", 4: "GFX/Everything/AIConfiguration/AIDifficultyList",
                             9: "GFX/Everything/AIConfiguration/AIDescriptorList"},
                    topo=[0, 4, 9])


def write_game(root: Path, howitzer: bool = True) -> None:
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\gfx\\", [
        ("file", "everything.cpp.gladndfbin", everything(howitzer))])]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", f"{lang}\\", [("file", "flash_txt.dic", make_dic([(name_to_key(k), t) for k, t in texts.items()]))])
        for lang, texts in TEXTS.items()])]))


def make_api(tmp: str, howitzer: bool = True) -> tuple[StudioApi, Path]:
    """A Studio on a made-up game of its own (in `tmp`) with a home of its own."""
    game = Path(tempfile.mkdtemp(dir=tmp)) / "game"
    write_game(game, howitzer)
    index = build_index(game, game.parent / "index.sqlite", say=lambda line: None)
    home = game.parent / "home"
    starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: True,
                      wait=lambda s: None)
    return StudioApi(index_path=index, game_dir=game, home=home, starter=starter, instances=home / "copies"), game


class Improved(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.api, self.game = make_api(self.tmp.name)

    def profile(self, address):
        return next(p for p in self.api.ai("us")["profiles"] if p["id"] == address)

    def built(self) -> Ndf:
        folder = self.api._mod_dir()
        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        return Ndf(new.read(new.find("everything.cpp.gladndfbin")))

    def test_the_values_are_the_ones_tried_in_the_game(self):
        self.assertEqual(ai.IMPROVED, {"MissionFacteurLancementAttaque": 0.000001,
                                       "MissionFacteurEnoughToDestroy": 0.000001, "BonusUnitesArtillerie": -100000.0})
        self.assertEqual((ai.IMPROVED_MONEY, ai.IMPROVED_MONEY_DEFAULT), ("DeviseBonusIA", 50000))
        # the money a player holds is kept x 840 in a 32-bit number: the most the Studio takes stays well under it
        self.assertLess(ai.IMPROVED_MONEY_MOST * 840, 2 ** 31)

    def test_shown_on_each_difficulty_off_at_first(self):
        page = self.api.ai("us")
        off = {"on": False, "money": None, "default_money": 50000, "most_money": 1000000}
        self.assertEqual({p["id"]: p.get("improved") for p in page["profiles"]},
                         {DEFAULT: None, EASY: off, HARD: off, REGULAR: None,
                          f"{LISTS}/AIDescriptorList:Items[1].OverridenParams": None,
                          f"{LISTS}/AIDescriptorList:Items[2].OverridenParams": None})
        # the personalities whose own values win over a difficulty's keep them: said by their names in the game
        self.assertEqual(page["improved_keeps"], {"attack": ["Blitzkrieg"], "artillery": ["Howitzer"]})

    def test_on_writes_its_values_and_the_build_makes_them(self):
        with self.assertRaises(StudioError):
            self.api.ai_improved(HARD, True)  # no mod to save it in yet
        self.api.new_mod("Rush")
        got = self.api.ai_improved(HARD, True)
        self.assertEqual({k: got[k] for k in ("on", "money")}, {"on": True, "money": 50000})
        text = (self.api._mod_dir() / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"\npatch {HARD}\n(\n    BonusUnitesArtillerie = -100000\n    DeviseBonusIA = 50000\n"
                      "    MissionFacteurEnoughToDestroy = 0.000001\n    MissionFacteurLancementAttaque = 0.000001\n)\n",
                      text)
        self.assertEqual(self.profile(HARD)["improved"]["on"], True)
        self.assertEqual(self.profile(EASY)["improved"]["on"], False)
        # what each value comes to in a battle counts the values it adds, a row of Hard's or not
        battle = self.api.ai("us")["battle"]
        self.assertEqual(battle["BonusUnitesArtillerie"], {"difficulties": [("Easy", 0), ("Hard", -100000.0)],
                                                           "personalities": [("Howitzer", 8000.0)]})
        self.assertEqual(battle["DeviseBonusIA"]["difficulties"], [("Easy", 0), ("Hard", 50000)])
        self.assertTrue(math.isclose(dict(battle["MissionFacteurLancementAttaque"]["difficulties"])["Hard"], 0.000001,
                                     rel_tol=1e-5))
        # Easy lists neither the start money nor the artillery weight: both are added to it
        self.api.ai_improved(EASY, True, 2000)
        nd = self.built()

        def value(obj, prop):
            return nd.objects[obj].get(P[prop]).scalar()
        for obj, money in ((8, 50000), (6, 2000)):
            with self.subTest(obj=obj):
                self.assertTrue(math.isclose(value(obj, "MissionFacteurLancementAttaque"), 0.000001, rel_tol=1e-5))
                self.assertTrue(math.isclose(value(obj, "MissionFacteurEnoughToDestroy"), 0.000001, rel_tol=1e-5))
                self.assertEqual(value(obj, "BonusUnitesArtillerie"), -100000)
                self.assertEqual(value(obj, "DeviseBonusIA"), money)
        self.assertEqual(value(13, "BonusUnitesArtillerie"), 8000)  # the Howitzer keeps its own
        self.assertTrue(math.isclose(value(15, "MissionFacteurLancementAttaque"), 0.2, rel_tol=1e-5))  # Blitzkrieg too

    def test_the_money_changes_while_it_is_on(self):
        self.api.new_mod("Rush money")
        self.api.ai_improved(HARD, True)
        self.assertEqual(self.api.ai_improved(HARD, True, 7000)["money"], 7000)
        self.assertEqual(self.profile(HARD)["improved"], {"on": True, "money": 7000, "default_money": 50000,
                                                          "most_money": 1000000})

    def test_off_puts_the_game_s_values_back(self):
        self.api.new_mod("Rush off")
        self.api.ai_improved(HARD, True, 9000)
        got = self.api.ai_improved(HARD, False)
        self.assertEqual({k: got[k] for k in ("on", "money")}, {"on": False, "money": None})
        text = (self.api._mod_dir() / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertNotIn(HARD, text)  # nothing of it is left in the mod
        nd = self.built()
        self.assertTrue(math.isclose(nd.objects[8].get(P["MissionFacteurLancementAttaque"]).scalar(), 0.9, rel_tol=1e-5))
        self.assertEqual(nd.objects[8].get(P["DeviseBonusIA"]).scalar(), 150)
        self.assertIsNone(nd.objects[8].get(P["BonusUnitesArtillerie"]))

    def test_refused(self):
        self.api.new_mod("Rush refused")
        for address, on, money, said in (
                (DEFAULT, True, None, "Only a difficulty"), (REGULAR, True, None, "Only a difficulty"),
                ("$/GFX/Everything/Nothing", True, None, "Only a difficulty"),
                (HARD, True, 0, "whole number"), (HARD, True, -5, "whole number"), (HARD, True, 1.5, "whole number"),
                (HARD, True, "lots", "whole number"), (HARD, True, True, "whole number"),
                (HARD, True, 2000000, "whole number")):
            with self.subTest(address=address, money=money):
                with self.assertRaisesRegex(StudioError, said):
                    self.api.ai_improved(address, on, money)
        self.assertEqual(self.profile(HARD)["improved"]["on"], False)  # nothing was written

    def test_a_game_with_no_artillery_weight_anywhere(self):
        # the build writes a value a profile doesn't list only under a name some profile in the file uses
        api, _game = make_api(self.tmp.name, howitzer=False)
        api.new_mod("No howitzer")
        with self.assertRaisesRegex(StudioError, "BonusUnitesArtillerie"):
            api.ai_improved(HARD, True)


if __name__ == "__main__":
    unittest.main()
