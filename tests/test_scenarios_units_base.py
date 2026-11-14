"""The scenario tests' shared parts (no tests of its own). The owner, 2026-11-13 overnight: "really limit test some of
the unique situations players can find themselves in when building new things with ... our apps"; "Not just unusual.
Usual and unusual situations. Player can find themselves in when making new mods in our apps."

A made-up game with a unit of every kind a player copies: the USA's Armor Base (10) with M1, M2 (an upgrade of M1), L1
and H1; its Anti-Tank Base (11) with T1; its Artillery Base (13) with A1; its Barracks (8) with S1, an infantry squad;
its Airfield (9) with P1, a fighter, and P2, an upgrade of P1. Germany's Armor Base with G1 and G2 (an upgrade of G1),
its Barracks with GS. The USA's Armor Base and Barracks buildings and Germany's Armor Base building. The USSR has no
build menus. Every unit has a card type (TypeUnitHintToken), so the Studio puts copies in the group of their kind. The
game's ten languages each have their own names for every unit.

`Player`: a Studio on that game (or on test_studio's, `GAME = "studio"`), a fresh platform folder per test, the calls
made as the page makes them (rusemod.webui.page_api: a refusal said in the Studio's language as the page shows it), and
the mod built as the Studio tests build it (test_studio NewUnits.build, test_delete_goes_through
OnTheStudio.build_errors).

Checked our_tools.json: none of its tools is for this; this file reads no program: the made-up game gets a two-byte
stand-in RUSE.exe, as tests/test_studio.py's does."""
import os
import re
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod import Edat, Ndf, loc, schema
from rusemod.build import build_pack, load_mod
from rusemod.dic import Dic, name_to_key
from rusemod.index import build_index
from rusemod.play import Starter
from rusemod.webui import page_api
from ruse_studio.api import StudioApi
from ruse_studio.errortext import worded

LANGS = schema.APP_LANGS            # the apps' eleven: the game's ten and Persian
GAME_LANGS = schema.LANGS           # the game's ten: its own texts


def i32(v):
    return val(0x02, struct.pack("<i", v))


def flag(v):
    return val(0x00, struct.pack("<B", v))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def ints(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(i32(x) for x in items))


def key(name):
    return val(0x1D, struct.pack("<Q", name_to_key(name)))


E = "$/GFX/Everything/"
U = E + "Descriptor_Unit_"
M1, M2, L1, H1, T1, A1, S1, P1, P2, G1, G2, GS = (U + n for n in (
    "M1", "M2", "L1", "H1", "T1", "A1", "S1", "P1", "P2", "G1", "G2", "GS"))
ARMOR_US, BARRACKS_US, ARMOR_GER = (E + "Descriptor_Building_" + n for n in ("ArmorBase_US", "Barracks_US",
                                                                              "ArmorBase_GER"))
CLASSES = ["TUniteAuSolDescriptor", "TAvionDescriptor", "TBatimentDescriptor", "TInfanterieDescriptor"]
UNIT_PROPS = ("Nationalite", "Factory", "PositionInMenu", "ShowInMenu", "UpgradeRequire", "IsUpgrade", "UpgradePrice",
              "UpgradeTime", "ProductionPrice", "NameInMenuToken", "TypeUnitHintToken", "SeuilMort")
BUILDING_PROPS = ("Nationalite", "TypeBatiment", "Menu", "ShowInMenu", "ProductionPrice", "NameInMenuToken")
PROPS = ([(n, 0) for n in UNIT_PROPS] + [(n, 1) for n in UNIT_PROPS] + [(n, 2) for n in BUILDING_PROPS]
         + [(n, 3) for n in UNIT_PROPS])
P = [{n: i for i, (n, c) in enumerate(PROPS) if c == k} for k in range(4)]
ALL = (1, 1, 1, 1, 1)
# (export name tail, class, nation or None, factory, place in the menu, card type key, research parent's index)
UNITS = [("M1", 0, None, 10, 301, "TANK_m", None),    # 0
         ("M2", 0, None, 10, 302, "TANK_m", 0),       # 1 an upgrade of M1
         ("L1", 0, None, 10, 303, "TANK_l", None),    # 2
         ("H1", 0, None, 10, 304, "TANK_h", None),    # 3
         ("T1", 0, None, 11, 401, "TD", None),        # 4
         ("A1", 0, None, 13, 601, "ART_h", None),     # 5
         ("S1", 3, None, 8, 201, "INF_r", None),      # 6 an infantry squad
         ("P1", 1, None, 9, 501, "AIR_f", None),      # 7 a fighter
         ("P2", 1, None, 9, 502, "AIR_f", 7),         # 8 an upgrade of P1
         ("G1", 0, 1, 10, 301, "TANK_m", None),       # 9 Germany's
         ("G2", 0, 1, 10, 302, "TANK_h", 9),          # 10 an upgrade of G1
         ("GS", 3, 1, 8, 201, "INF_r", None)]         # 11
# (export name tail, nation, building kind, name key)
BUILDINGS = [("ArmorBase_US", 0, 10, "N_ARMOR"), ("Barracks_US", 0, 8, "N_BARR"), ("ArmorBase_GER", 1, 10, "N_ARMORG")]
ENGLISH = {"N_M1": "M One", "N_M2": "M Two", "N_L1": "L One", "N_H1": "H One", "N_T1": "T One", "N_A1": "A One",
           "N_S1": "Rifle Squad", "N_P1": "P One", "N_P2": "P Two", "N_G1": "G One", "N_G2": "G Two",
           "N_GS": "German Squad", "N_ARMOR": "Armor Base", "N_BARR": "Barracks", "N_ARMORG": "Armor Base",
           "TANK_m": "Medium Tank", "TANK_l": "Light Tank", "TANK_h": "Heavy Tank", "TD": "Tank Destroyer",
           "ART_h": "Heavy Artillery", "INF_r": "Infantry", "AIR_f": "Fighter"}


def menus_units() -> bytes:
    objects, exports = [], {}
    for k, (tail, cls, nation, factory, slot, card, parent) in enumerate(UNITS):
        p = P[cls]
        values = [(p["Factory"], i32(factory)), (p["PositionInMenu"], i32(slot)), (p["ShowInMenu"], ints(*ALL)),
                  (p["ProductionPrice"], ints(30, 30, 30, 30, 30)), (p["NameInMenuToken"], key("N_" + tail)),
                  (p["TypeUnitHintToken"], key(card)), (p["SeuilMort"], i32(12))]
        if nation is not None:
            values.insert(0, (p["Nationalite"], i32(nation)))
        if parent is not None:
            values += [(p["UpgradeRequire"], ref(parent, UNITS[parent][1])), (p["IsUpgrade"], flag(1)),
                       (p["UpgradePrice"], i32(25)), (p["UpgradeTime"], i32(75))]
        objects.append((cls, values))
        exports[k] = "GFX/Everything/Descriptor_Unit_" + tail
    for tail, nation, kind, name in BUILDINGS:
        p = P[2]
        exports[len(objects)] = "GFX/Everything/Descriptor_Building_" + tail
        objects.append((2, [(p["Nationalite"], i32(nation)), (p["TypeBatiment"], i32(kind)), (p["Menu"], i32(1)),
                            (p["ShowInMenu"], ints(*ALL)), (p["ProductionPrice"], ints(40, 40, 40, 40, 40)),
                            (p["NameInMenuToken"], key(name))]))
    return make_ndf(objects=objects, classes=CLASSES, props=PROPS, exports=exports, topo=list(range(len(objects))))


def game_text(lang: str, english: str) -> str:
    """A text of the made-up game in `lang`: the English one, marked with its language (the English as it is)."""
    return english if lang == "us" else f"{english} [{lang}]"


def write_menus_game(root: Path) -> None:
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\gfx\\", [
        ("file", "everything.cpp.gladndfbin", menus_units())])]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", f"{lang}\\", [("file", "baseunite.dic", make_dic(
            [(name_to_key(k), game_text(lang, t)) for k, t in ENGLISH.items()]))]) for lang in GAME_LANGS])]))


def write_studio_game(root: Path) -> None:
    """test_studio's made-up game (its M4 with a gun, an ammo shared with the Panzer, a flag list)."""
    from test_studio import write_game
    write_game(root)


GAMES = {"menus": write_menus_game, "studio": write_studio_game}
GAME_EXE = "RUSE.exe"   # the made-up game's two-byte stand-in program file (the scenario files take it from here)
TMP = os.environ.get("RUSE_TEST_TMP") or None
# what a player must never see in a page's words: the game's code names, an address, Python's quotes round a name
CODE_NAME = re.compile(r"Descriptor_|\$/GFX|GFX/Everything|Ammo_[A-Z]|TUniteAuSol|TInfanterie|TAvion|TBatiment")
PYTHON_WORDS = re.compile(r"Traceback|Errno|WinError|\bNone\b|object has no attribute|unexpected keyword|"
                          r"positional argument|codec can't|not subscriptable|is not iterable|KeyError|ValueError|"
                          r"TypeError|Escaped character|Unicode scalar|TOMLDecodeError|invalid literal")


class Refused(Exception):
    """A page call the Studio refused: `text` as the page shows it, `kind` the error's class name."""

    def __init__(self, text: str, kind: str):
        super().__init__(text)
        self.text, self.kind = text, kind


class Player(unittest.TestCase):
    """A Studio on a made-up game (GAME: "menus", this file's, or "studio", test_studio's), with a fresh platform
    folder per test; nothing starts."""

    GAME = "menus"

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(dir=TMP)
        cls.game = Path(cls.tmp.name, "game")
        GAMES[cls.GAME](cls.game)
        (cls.game / GAME_EXE).write_bytes(b"MZ")
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.started = []
        self.api = self.studio()
        self.page = page_api(self.api)

    def studio(self, home: Path | None = None) -> StudioApi:
        """A Studio on the made-up game with this test's platform folder (or `home`): a start of the app."""
        starter = Starter(open_url=lambda url: None, start_game=self.started.append, steam_running=lambda: True,
                          wait=lambda s: None)
        home = home or self.home
        return StudioApi(index_path=self.index, game_dir=self.game, home=home, starter=starter,
                         instances=home / "copies")

    def restart(self) -> None:
        """The Studio closed and started again on the same platform folder."""
        self.api = self.studio()
        self.page = page_api(self.api)

    # --- the page's calls ---
    def call(self, name: str, *args, lang: str = "us", **kw):
        """`name` called as the page calls it, with the Studio's language `lang`: its answer, or Refused with the words
        the page shows."""
        self.api.set_pref("lang", None if lang in ("us", "base") else lang)
        try:
            return getattr(self.page, name)(*args, **kw)
        except Exception as exc:  # noqa: BLE001 - every error the page can get
            raise Refused(str(exc), type(exc).__name__) from exc
        finally:
            self.api.set_pref("lang", None)

    def refusal(self, name: str, *args, **kw) -> dict:
        """The words of a refused page call in every one of the apps' languages: {lang: text}; the call must be
        refused in each (it changes nothing when refused)."""
        out = {}
        for lang in LANGS:
            try:
                self.call(name, *args, lang=lang, **kw)
            except Refused as r:
                out[lang] = r.text
                continue
            self.fail(f"{name}{args} wasn't refused in {lang}")
        return out

    def english_left(self, said: dict) -> list:
        """The languages (but English) whose words are the English ones: a refusal not said in that language."""
        return [lang for lang, text in said.items() if lang != "us" and text == said["us"]]

    def assert_plain(self, text: str):
        """Words a player can be shown: no code name, no Python words."""
        self.assertIsNone(CODE_NAME.search(text), f"a code name in what the page says: {text!r}")
        self.assertIsNone(PYTHON_WORDS.search(text), f"Python's words in what the page says: {text!r}")

    # --- the mod ---
    def mod(self, name: str = "Scenario") -> Path:
        """A new mod made as the page makes it (New mod..., its name trimmed): its folder."""
        return Path(self.call("new_mod", name.strip(), "mod")["current"])

    def build(self, folder: Path):
        """The mod in `folder` built on the made-up game's packs, as the Studio tests build it: (its errors' words,
        the built unit data, the built texts)."""
        rev = self.game / "Data" / "PC" / "190852"
        arc, texts = Edat((rev / "ZZ_GladPatchableWin.dat").read_bytes()), Edat((rev / "ZZ_Win.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)], text_arc=texts)
        errors = [e.message for e in result.errors]
        if errors:
            return errors, None, None
        new = Edat(arc.to_bytes(result.changed))
        return errors, Ndf(new.read(new.find("everything.cpp.gladndfbin"))), Edat(texts.to_bytes(result.text_changed))

    def built_names(self, ndf: Ndf, texts: Edat, address: str) -> dict:
        """The name the built game shows for the unit at `address`, in each of the game's languages."""
        o = ndf.objects[next(k for k, name in ndf.exports.items() if name == address)]
        token = next(v for pi, v in o.props if ndf.prop_name(pi) == "NameInMenuToken")
        k = struct.unpack("<Q", token.payload)[0]
        return {lang: Dic(texts.read(texts.find(loc.member("baseunite", lang)))).text(k) for lang in GAME_LANGS}

    def value(self, ndf: Ndf, address: str, prop: str):
        """A built object's value `prop` (None when it has none)."""
        i = next(k for k, name in ndf.exports.items() if name == address)
        return next((v for pi, v in ndf.objects[i].props if ndf.prop_name(pi) == prop), None)

    def files(self, folder: Path) -> dict:
        """Every file in a mod folder: {its path in it: its bytes}."""
        return {p.relative_to(folder).as_posix(): p.read_bytes() for p in Path(folder).rglob("*") if p.is_file()}


def translated(text: str, lang: str) -> bool:
    """Whether errors.toml says an English refusal `text` in `lang` (rusemod.wordedtext)."""
    return worded(text, lang) != text
