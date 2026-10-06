"""The computer players (rusemod.ai, the Studio's AI tab): their sets of values (Default, the difficulties, the
profiles), the units they're keener to build and the ruse cards, read, changed and built, on a made-up game."""
import struct
import tempfile
import tomllib
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod import Edat, Ndf, ai
from rusemod.build import build_pack, load_mod
from rusemod.dic import name_to_key
from rusemod.index import Index, build_index
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError

ROOT = Path(__file__).resolve().parents[1]
LANGS = {"us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"}


def i32(v):
    return val(0x02, struct.pack("<i", v))


def f32(v):
    return val(0x05, struct.pack("<f", v))


def flag(v):
    return val(0x00, struct.pack("<B", v))


def key(name):
    return val(0x1D, struct.pack("<Q", name_to_key(name)))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def lst(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(items))


CLASSES = ["TIAProfilList", "TAIConfigurationList", "TAIConfiguration", "TIAProfil", "TBluffZoneManager",
           "TBluffCardDescriptor", "TAISpecificBonusList", "TAISpecificBonus", "TUniteAuSolDescriptor"]
PROPS = [("DefaultAndDifficultyAndProfil", 0), ("Items", 1), ("Name", 2), ("OverridenParams", 2),
         ("AttaqueTempsActivation", 3), ("OffensiveNbMissionMax", 3), ("HarcelementActif", 3), ("DeviseBonusIA", 3),
         ("BluffCardDescriptors", 4), ("Title", 5), ("Description", 5), ("LifeDuration", 5), ("PositionInMenu", 5),
         ("ShowInMenu", 5), ("SpecificBonusList", 6), ("UnitIDs", 7), ("WarModes", 7), ("AIDifficulties", 7),
         ("AIProfiles", 7), ("ConsiderStackAsOneEnnemy", 7), ("BonusValue", 7), ("DescriptorId", 8),
         ("NameInMenuToken", 8), ("PlacementSound", 5), ("TypeForAcknow", 5)]
P = {name: i for i, (name, _c) in enumerate(PROPS)}


def everything() -> bytes:
    """The game's AI data as the game lays it out, made small: the profile list's three lists (Default; Easy and Hard;
    Regular and the lobby's Random, which has no values of its own), four ruse cards (one the texts don't name), the
    bonus for one unit, and that unit."""
    objects = [
        (0, [(P["DefaultAndDifficultyAndProfil"], lst(ref(1, 1), ref(4, 1), ref(9, 1)))]),       # 0 the profile list
        (1, [(P["Items"], lst(ref(2, 2)))]),                                                      # 1 Default's list
        (2, [(P["Name"], key("DEFAUT")), (P["OverridenParams"], ref(3, 3))]),                     # 2
        (3, [(P["AttaqueTempsActivation"], f32(30)), (P["OffensiveNbMissionMax"], i32(-1)),       # 3 Default
             (P["HarcelementActif"], flag(1))]),
        (1, [(P["Items"], lst(ref(5, 2), ref(7, 2)))]),                                           # 4 the difficulties
        (2, [(P["Name"], key("EASY")), (P["OverridenParams"], ref(6, 3))]),                       # 5
        (3, [(P["AttaqueTempsActivation"], f32(300)), (P["OffensiveNbMissionMax"], i32(-1))]),    # 6 Easy
        (2, [(P["Name"], key("HARD")), (P["OverridenParams"], ref(8, 3))]),                       # 7
        (3, [(P["OffensiveNbMissionMax"], i32(-1)), (P["HarcelementActif"], flag(1)),             # 8 Hard
             (P["DeviseBonusIA"], i32(150))]),
        (1, [(P["Items"], lst(ref(10, 2), ref(12, 2)))]),                                         # 9 the profiles
        (2, [(P["Name"], key("PROFILE_0")), (P["OverridenParams"], ref(11, 3))]),                 # 10
        (3, [(P["AttaqueTempsActivation"], f32(30)), (P["OffensiveNbMissionMax"], i32(2))]),      # 11 Regular
        (2, [(P["Name"], key("PROFILE_6"))]),                                                     # 12 Random
        (4, [(P["BluffCardDescriptors"], lst(ref(14, 5), ref(15, 5), ref(16, 5), ref(17, 5)))]),  # 13
        (5, [(P["Title"], key("SpyPlan")), (P["Description"], key("DSpyPlan")), (P["LifeDuration"], f32(60)),
             (P["PositionInMenu"], i32(60)), (P["ShowInMenu"], flag(1)),
             (P["PlacementSound"], val(0x07, struct.pack("<I", 0))), (P["TypeForAcknow"], i32(43))]),  # 14 Spy
        (5, [(P["Title"], key("BlitzPlan")), (P["Description"], key("DBlitzPlan")), (P["LifeDuration"], f32(120)),
             (P["PositionInMenu"], i32(5)), (P["ShowInMenu"], flag(1))]),                         # 15 Blitz
        (5, [(P["Title"], key("DecoyAT")), (P["LifeDuration"], f32(360)), (P["PositionInMenu"], i32(10))]),  # 16
        (5, [(P["Title"], key("Anihilati")), (P["PositionInMenu"], i32(300))]),                   # 17 no name
        (6, [(P["SpecificBonusList"], lst(ref(19, 7)))]),                                         # 18
        (7, [(P["UnitIDs"], lst(i32(3008))), (P["WarModes"], lst(i32(4))),                        # 19 the bonus
             (P["AIDifficulties"], lst(i32(0), i32(1))), (P["AIProfiles"], lst(i32(0), i32(6))),
             (P["ConsiderStackAsOneEnnemy"], flag(1)), (P["BonusValue"], i32(400))]),
        (8, [(P["DescriptorId"], i32(3008)), (P["NameInMenuToken"], key("N_UNI_114"))]),          # 20 a unit
    ]
    return make_ndf(objects=objects, classes=CLASSES, props=PROPS, strings=["placement_ruse_Espion"],
                    exports={0: "GFX/Everything/AIConfiguration", 4: "GFX/Everything/AIConfiguration/AIDifficultyList",
                             9: "GFX/Everything/AIConfiguration/AIDescriptorList",
                             13: "GFX/Everything/BluffZoneManager", 18: "GFX/Everything/AISpecificBonusList",
                             20: "GFX/Everything/Descriptor_Unit_Canon_atomique_US"},
                    topo=[0, 4, 9, 13, 18, 20])


TEXTS = {"us": {"EASY": "Easy", "HARD": "Hard", "PROFILE_0": "Regular", "PROFILE_6": "Random", "NAME_AI": "AI",
                "BtnAIDiff": "Difficulty", "BtnAIType": "Profile", "DLC_GML_02": "Nuclear mode",
                "AI_HPROF0": "This AI will behave as a standard general", "SpyPlan": "SPY",
                "DSpyPlan": "Reveals all unidentified units in the sector.", "BlitzPlan": "BLITZ",
                "DBlitzPlan": "Increases your units' speed in the sector by 50%.", "DecoyAT": "DECOY AT BASE",
                "N_UNI_114": "NUCLEAR LONG TOM"},
         "fr": {"EASY": "Facile", "HARD": "Difficile", "PROFILE_0": "Standard", "NAME_AI": "IA", "SpyPlan": "ESPIONNAGE"}}
LISTS = "$/GFX/Everything/AIConfiguration"
DEFAULT = f"{LISTS}:DefaultAndDifficultyAndProfil[0].Items[class=TAIConfiguration].OverridenParams"
EASY, HARD = f"{LISTS}/AIDifficultyList:Items[0].OverridenParams", f"{LISTS}/AIDifficultyList:Items[1].OverridenParams"
REGULAR = f"{LISTS}/AIDescriptorList:Items[0].OverridenParams"
SPY, BLITZ, DECOY_AT = (f"$/GFX/Everything/BluffZoneManager:BluffCardDescriptors[{i}]" for i in (0, 1, 2))
BONUS = "$/GFX/Everything/AISpecificBonusList:SpecificBonusList[class=TAISpecificBonus]"


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\gfx\\", [
        ("file", "everything.cpp.gladndfbin", everything())])]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", f"{lang}\\", [("file", "flash_txt.dic", make_dic([(name_to_key(k), t) for k, t in texts.items()]))])
        for lang, texts in TEXTS.items()])]))


class Words(unittest.TestCase):
    def test_every_value_and_group_has_its_words(self):
        props = tomllib.loads((ROOT / "src" / "rusemod" / "labels.toml").read_text(encoding="utf-8"))["props"]
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        every = ai.PROFILE_PROPS + ai.CARD_PROPS + ai.BONUS_PROPS
        self.assertEqual(len(ai.PROFILE_PROPS), len(set(ai.PROFILE_PROPS)))
        for prop in every:
            with self.subTest(prop=prop):
                self.assertLessEqual(LANGS, set(props[prop]))
        for group in [g for g, _props in ai.PROFILE_GROUPS] + ["other"]:
            with self.subTest(group=group):
                self.assertEqual(set(words[f"ai_group_{group}"]), LANGS)
        for k in ("ai_tab", "ai_title", "tip_tab_ai", "ai_help", "ai_how_title", "ai_mix", "ai_default",
                  "ai_same_default", "ai_none", "ai_bonus_title", "ai_bonus_help", "ai_cards_title", "ai_cards_help",
                  "ai_not_in_menu", "tip_ai_reset"):
            with self.subTest(key=k):
                self.assertEqual(set(words[k]), LANGS)

    def test_the_tab_is_on_the_page(self):
        html = (ROOT / "src" / "ruse_studio" / "ui" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        fake = (ROOT / "src" / "ruse_studio" / "ui" / "fake-api.js").read_text(encoding="utf-8")
        for needle in ('id="tab-ai"', 'id="ai-view"', 'id="ai-pick"', 'id="ai-groups"', 'id="ai-bonuses"',
                       'id="ai-cards"'):
            self.assertIn(needle, html)
        for needle in ("function renderAI", "api().ai(", "api().ai_edit(", "api().ai_reset(", 'showView("ai")'):
            self.assertIn(needle, app)
        for needle in ("ai: async", "ai_edit: async", "ai_reset: async"):
            self.assertIn(needle, fake)


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

    def rows(self, page, address):
        p = next(p for p in page["profiles"] if p["id"] == address)
        return {r["prop"]: r for g in p["groups"] for r in g["rows"]}

    def test_the_profile_list_in_the_game_s_order(self):
        ix = Index(self.index)
        try:
            found = ai.configurations(ix)
        finally:
            ix.close()
        self.assertEqual([(c["kind"], c["index"], c["key"], c["address"]) for c in found],
                         [("default", 0, "DEFAUT", DEFAULT), ("difficulty", 0, "EASY", EASY),
                          ("difficulty", 1, "HARD", HARD), ("personality", 0, "PROFILE_0", REGULAR),
                          ("personality", 1, "PROFILE_6", None)])  # the lobby's Random: no values of its own

    def test_what_the_tab_shows(self):
        page = self.api.ai("us")
        self.assertTrue(page["ready"])
        self.assertEqual(page["words"], {"ai": "AI", "difficulty": "Difficulty", "profile": "Profile",
                                         "nuclear": "Nuclear mode"})
        self.assertEqual([(p["kind"], p["name"], p["hint"]) for p in page["profiles"]],
                         [("default", None, None), ("difficulty", "Easy", None), ("difficulty", "Hard", None),
                          ("personality", "Regular", "This AI will behave as a standard general")])
        default = self.rows(page, DEFAULT)
        self.assertEqual({p: (r["label"], r["type"], r["game"], r["value"]) for p, r in default.items()},
                         {"AttaqueTempsActivation": ("Seconds before it starts attacking", "float32", 30, None),
                          "OffensiveNbMissionMax": ("Most attacks at once (-1: no limit)", "int32", -1, None),
                          "HarcelementActif": ("Harasses the enemy", "bool", 1, None)})
        self.assertNotIn("same_default", default["AttaqueTempsActivation"])
        # a difficulty's or profile's value the same as Default's doesn't count; one Default doesn't list counts as 0
        self.assertEqual({p: r["same_default"] for p, r in self.rows(page, EASY).items()},
                         {"AttaqueTempsActivation": False, "OffensiveNbMissionMax": True})
        self.assertEqual({p: r["same_default"] for p, r in self.rows(page, HARD).items()},
                         {"OffensiveNbMissionMax": True, "HarcelementActif": True, "DeviseBonusIA": False})
        self.assertEqual({p: r["same_default"] for p, r in self.rows(page, REGULAR).items()},
                         {"AttaqueTempsActivation": True, "OffensiveNbMissionMax": False})
        groups = [g["id"] for g in page["profiles"][2]["groups"] if g["rows"]]
        self.assertEqual(groups, ["attack", "harass", "money"])
        self.assertEqual(self.rows(self.api.ai("base"), DEFAULT)["AttaqueTempsActivation"]["label"],
                         "AttaqueTempsActivation")  # the code names

        self.assertEqual([(c["id"], c["name"], c["in_menu"], [r["prop"] for r in c["rows"]]) for c in page["cards"]],
                         [(BLITZ, "BLITZ", True, ["LifeDuration", "ShowInMenu", "PositionInMenu"]),
                          (DECOY_AT, "DECOY AT BASE", False, ["LifeDuration", "PositionInMenu"]),
                          (SPY, "SPY", True, ["LifeDuration", "ShowInMenu", "PositionInMenu"])])  # by menu slot
        self.assertEqual(page["cards"][2]["about"], "Reveals all unidentified units in the sector.")
        self.assertEqual(page["cards"][0]["rows"][0]["label"], "How long it lasts (seconds)")

        (bonus,) = page["bonuses"]
        self.assertEqual(bonus["id"], BONUS)
        self.assertEqual({r["prop"]: (r["game"], r.get("names")) for r in bonus["rows"]},
                         {"BonusValue": (400, None), "ConsiderStackAsOneEnnemy": (1, None),
                          "UnitIDs": ([3008], ["NUCLEAR LONG TOM"]), "WarModes": ([4], ["Nuclear mode"]),
                          "AIDifficulties": ([0, 1], ["Easy", "Hard"]), "AIProfiles": ([0, 6], ["Regular", "6"])})

    def test_in_another_language(self):
        page = self.api.ai("fr")
        self.assertEqual([p["name"] for p in page["profiles"]], [None, "Facile", "Difficile", "Standard"])
        self.assertEqual(page["words"]["ai"], "IA")
        self.assertEqual(self.rows(page, DEFAULT)["AttaqueTempsActivation"]["label"], "Secondes avant de commencer à attaquer")
        self.assertEqual([c["name"] for c in page["cards"]], ["ESPIONNAGE"])  # only the cards the French texts name

    def test_changes_are_saved_and_built(self):
        with self.assertRaises(StudioError):
            self.api.ai_edit(HARD, "DeviseBonusIA", 300)  # no mod to save it in yet
        self.api.new_mod("Tough")
        folder = self.home / "mods" / "tough"
        self.assertEqual(self.api.ai_edit(HARD, "DeviseBonusIA", 299.6), {
            "saved": str(folder / "src" / "studio.rndf"), "value": 300, "same_default": False})  # whole numbers
        self.assertEqual(self.api.ai_edit(EASY, "AttaqueTempsActivation", 30)["same_default"], True)  # now Default's
        self.assertEqual(self.api.ai_edit(DEFAULT, "AttaqueTempsActivation", 45)["same_default"], None)
        self.assertEqual(self.rows(self.api.ai("us"), EASY)["AttaqueTempsActivation"]["same_default"], False)
        self.api.ai_edit(REGULAR, "OffensiveNbMissionMax", 3)
        self.api.ai_edit(DEFAULT, "HarcelementActif", 0)
        self.api.ai_edit(BLITZ, "LifeDuration", 90.5)
        self.api.ai_edit(SPY, "ShowInMenu", 0)
        self.api.ai_edit(BONUS, "BonusValue", 800)
        self.api.ai_edit(BONUS, "AIProfiles", [0, 4])
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        for block in (f"\npatch {LISTS}:DefaultAndDifficultyAndProfil[0].Items[class=TAIConfiguration].OverridenParams\n"
                      "(\n    AttaqueTempsActivation = 45\n    HarcelementActif = 0\n)\n",
                      f"\npatch {LISTS}/AIDifficultyList:Items[1].OverridenParams\n(\n    DeviseBonusIA = 300\n)\n",
                      f"\npatch {LISTS}/AIDescriptorList:Items[0].OverridenParams\n(\n    OffensiveNbMissionMax = 3\n)\n",
                      "\npatch $/GFX/Everything/BluffZoneManager:BluffCardDescriptors[0]\n(\n    ShowInMenu = 0\n)\n",
                      "\npatch $/GFX/Everything/BluffZoneManager:BluffCardDescriptors[1]\n(\n    LifeDuration = 90.5\n)\n",
                      f"\npatch {BONUS}\n(\n    AIProfiles = [0, 4]\n    BonusValue = 800\n)\n"):
            self.assertIn(block, text)
        page = self.api.ai("us")
        self.assertEqual(self.rows(page, HARD)["DeviseBonusIA"]["value"], 300)
        self.assertEqual({r["prop"]: r.get("names") for r in page["bonuses"][0]["rows"]}["AIProfiles"],
                         ["Regular", "4"])  # the mod's list, by name

        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        nd = Ndf(new.read(new.find("everything.cpp.gladndfbin")))

        def value(obj, prop):
            return nd.objects[obj].get(P[prop])

        self.assertEqual(round(struct.unpack("<f", value(3, "AttaqueTempsActivation").payload)[0]), 45)
        self.assertEqual(value(3, "HarcelementActif").scalar(), 0)
        self.assertEqual(value(6, "AttaqueTempsActivation").payload, struct.pack("<f", 30))  # Easy's, as Default had it
        self.assertEqual(value(8, "DeviseBonusIA").scalar(), 300)
        self.assertEqual(value(11, "OffensiveNbMissionMax").scalar(), 3)
        self.assertEqual(struct.unpack("<f", value(15, "LifeDuration").payload)[0], 90.5)
        self.assertEqual(value(14, "ShowInMenu").scalar(), 0)
        self.assertEqual(value(19, "BonusValue").scalar(), 800)
        self.assertEqual(value(19, "AIProfiles").payload, lst(i32(0), i32(4))[4:])
        self.assertEqual(value(16, "LifeDuration").payload, struct.pack("<f", 360))  # untouched

    def test_back_to_the_game_s_value(self):
        self.api.new_mod("Tough")
        self.api.ai_edit(HARD, "DeviseBonusIA", 500)
        self.api.ai_edit(HARD, "DeviseBonusIA", 150)  # the game's own value again: no change left
        self.assertIsNone(self.rows(self.api.ai("us"), HARD)["DeviseBonusIA"]["value"])
        self.api.ai_edit(EASY, "OffensiveNbMissionMax", 4)
        self.assertEqual(self.api.ai_reset(EASY, "OffensiveNbMissionMax")["same_default"], True)
        self.assertIsNone(self.rows(self.api.ai("us"), EASY)["OffensiveNbMissionMax"]["value"])
        self.api.ai_edit(SPY, "PositionInMenu", 1)
        self.assertEqual(self.api.ai_reset(SPY, "PositionInMenu")["same_default"], None)
        text = (self.home / "mods" / "tough" / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertNotIn("patch", text)

    def test_what_is_refused(self):
        self.api.new_mod("Tough")
        for address, prop, value, why in (
                ("$/GFX/Everything/Nothing", "BonusValue", 1, "isn't one of the AI tab's"),
                (f"{LISTS}/AIDescriptorList:Items[1]", "Name", 1, "isn't one of the AI tab's"),  # Random: no values
                (EASY, "DeviseBonusIA", 100, "can't be changed here"),  # one Easy doesn't list
                (EASY, "NoSuchValue", 1, "can't be changed here"),
                (SPY, "TypeForAcknow", 1, "can't be changed here"),  # not one the tab offers
                (SPY, "PlacementSound", 1, "can't be changed here"),
                (DECOY_AT, "ShowInMenu", 1, "can't be changed here"),  # a card out of the menu stays out
                (HARD, "DeviseBonusIA", "lots", "numbers only"),
                (HARD, "DeviseBonusIA", True, "numbers only"),
                (HARD, "DeviseBonusIA", [1, 2], "one number"),
                (BONUS, "AIProfiles", [1, 2, 3], "expected 2 numbers"),
                (BONUS, "AIProfiles", 1, "expected 2 numbers"),
                (DEFAULT, "HarcelementActif", 2, "doesn't fit")):
            with self.subTest(address=address, prop=prop, value=value), self.assertRaisesRegex(StudioError, why):
                self.api.ai_edit(address, prop, value)
        self.assertFalse((self.home / "mods" / "tough" / "src" / "studio.rndf").is_file())  # nothing half-saved


if __name__ == "__main__":
    unittest.main()
