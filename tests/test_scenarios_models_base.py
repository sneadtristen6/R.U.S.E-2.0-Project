"""Scenario tests' base: a new unit's own model and Blender, as a player meets them in the RUSE Studio (the owner,
overnight 2026-11-13: "really limit test some of the unique situations players can find themselves in when building new
things with ... our apps"; "Not just unusual. Usual and unusual situations. Player can find themselves in when making
new mods in our apps.").

The made-up game: a tank (Descriptor_Unit_Panzer) drawing tests/test_unitmodel.py's made-up Panzer IV (its model pack
on two bones, its skeleton and its picture stand-in pack), its name in the game's ten languages. So Import model's own
reading and fitting run (rusemod.modelin, rusemod.unitmodel.import_model on that pack), and the build writes the mod's
model into the game's packs as a real build does (rusemod.build.build_pack, then its own-models step:
unitmodel.KeptModels and write_unit_model, as rusemod.build's copy step runs them).

Stood in, for what a test can't run: Blender (never started; what it opens and what its Send writes are written here,
as tests/test_modelblender.py's blender_sends: Blender 4.5's own changes to a file, measured 2026-11-12) and the game's
3D model export for Blender (test_modelblender's PaintedLibrary: a made-up model with two pictures, so a repaint can be
seen). Everything else is the Studio's and the build's own: the records, the files, the words.

Each scenario ends with what the page says (every language's words, rusemod.webui.page_api: a refusal said in the
Studio's language as the page shows it), the mod's files, and the mod's build on the made-up game.

FOR: the models and Blender scenarios (release 0.9.8.20, overnight 2026-11-14,
D:/RUSE-2.0/scratch/release-0920/scenarios/models).
USED-BY: tests/test_scenarios_models_*.py."""
import hashlib
import json
import struct
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from test_unitmodel import MESHES, PROXIES, SKELETONS, TANK, TEX, skeleton3, unit_pack
from rusemod import Edat, schema, unitmodel
from rusemod.build import build_pack, load_mod
from rusemod.dic import name_to_key
from rusemod.unitpacks import MeshPack, Proxy, ProxyPack, proxy_name
from rusemod.webui import page_api

E = "$/GFX/Everything/"
PANZER = E + "Descriptor_Unit_Panzer"
TANK_FILE = "WW2\\Res3D\\Units\\GER\\Tank\\GER_PanzerIVlod0.Ase2NdfBin"   # (test_unitmodel's TANK, as unit data names it)
NAME = "My Tank"
STEM = "Descriptor_Unit_My_Tank"
UNIT = E + STEM
# its skeleton as the game's are laid out (three matrices a bone): a hull, a turret, its gun, a wheel (test_unitmodel's
# OwnTurret), so a model with a turret of its own gets its own skeleton written as a real build writes it
BONES = skeleton3(["chassis", "tourelle_01", "canon_01", "roue_1"], [-1, 0, 1, 0],
                  [(0.0, 0.0, 0.0), (-70.0, 5.0, 30.0), (40.0, 5.0, 50.0), (100.0, -30.0, 0.0)])
LANGS = schema.APP_LANGS            # the apps' eleven: the game's ten and Persian
GAME_LANGS = schema.LANGS
PYTHON_WORDS = ("Traceback", "Errno", "WinError", "KeyError", "TypeError", "ValueError", "NoneType", "object has no",
                "struct.error", "UnicodeDecodeError", "JSONDecodeError")


def i32(v):
    return val(0x02, struct.pack("<i", v))


def u32(v):
    return val(0x03, struct.pack("<I", v))


def ref(index, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))


def key(name):
    return val(0x1D, struct.pack("<Q", name_to_key(name)))


def ints(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(i32(x) for x in items))


def unit_data() -> bytes:
    """The made-up game's unit data: the tank, its look naming its model."""
    ndf = make_ndf(
        objects=[(0, [(0, u32(2)), (1, i32(1)), (2, i32(10)), (3, ints(45, 45)), (4, key("PANZER")), (5, i32(12)),
                      (6, ref(1, 1))]),                                                       # 0 the tank
                 (1, [(7, ref(2, 2))]),                                                       # 1 its look
                 (2, [(8, val(0x1C, struct.pack("<I", 0)))])],                                # 2 its model
        classes=["TUniteAuSolDescriptor", "TGfxDescriptorModeleWithAnimation", "TResourceMultiMaterialMesh"],
        props=[("DescriptorId", 0), ("Nationalite", 0), ("Factory", 0), ("ProductionPrice", 0), ("NameInMenuToken", 0),
               ("SeuilMort", 0), ("GfxDescriptor", 0), ("MeshDescriptor", 1), ("FileName", 2)],
        strings=[TANK_FILE], exports={0: "GFX/Everything/Descriptor_Unit_Panzer"}, compress=True)
    return make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ndf)])])


def zz_win() -> bytes:
    """The made-up game's ZZ_Win.dat: test_unitmodel's Panzer model pack, skeleton and picture stand-ins, and the tank's
    name in the game's ten languages."""
    skel = MeshPack(formats=[], materials=b"", material_count=0, has_formats=False)
    skel.materials = MeshPack.read(unit_pack().to_bytes()).materials
    skel.skeletons.append(BONES)
    skel.items[TANK] = [bytes(28), 0xCDCD, 0]
    proxies = ProxyPack([Proxy(b"K" * 8, b"OLD-STANDIN", struct.pack("<HHI", 0, 0, 0xAAAAAAAA),
                               proxy_name(TEX).encode().ljust(256, b"\0"))], [0])
    files = {MESHES: unit_pack().to_bytes(), SKELETONS: skel.to_bytes(), PROXIES: proxies.to_bytes()}
    tree: dict = {}
    for path, data in files.items():
        folder, _, name = path.rpartition("\\")
        tree.setdefault(folder + "\\", []).append(("file", name, data))
    names = [("dir", f"{lang}\\", [("file", "baseunite.dic", make_dic([(name_to_key("PANZER"), "Panzer IV" if lang == "us"
                                                                         else f"Panzer IV [{lang}]")]))])
             for lang in GAME_LANGS]
    return make_edat([("dir", folder, items) for folder, items in tree.items()]
                     + [("dir", "genlocalisation\\ww2\\localisation\\translations\\", names)])


def tree(folder: Path) -> dict:
    """{path inside `folder`: its bytes} of every file in it."""
    folder = Path(folder)
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class MadeUpTankGame(unittest.TestCase):
    """The made-up game with the tank, its index built once for the class."""

    @classmethod
    def setUpClass(cls):
        from rusemod.index import build_index
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        data = cls.game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_GladPatchableWin.dat").write_bytes(unit_data())
        (data / "ZZ_Win.dat").write_bytes(zz_win())
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class ModelScenario(MadeUpTankGame):
    """A player's mod with a new tank copying the game's (New mod, New unit), the Studio called as the page calls it.
    `self.opened`: each file Blender would have opened (Change it in Blender, the one Blender button)."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home)
        self.api._blender = lambda: self.home / "blender" / "blender.exe"
        self.page = page_api(self.api)
        self.opened = []
        self.addCleanup(self.api.set_pref, "lang", "us")
        self.mod = Path(self.page.new_mod("Models")["current"])
        self.unit = self.page.new_unit(PANZER, NAME, 50, group="new")["address"]   # (a group of its own)
        self.assertEqual(self.unit, UNIT)
        self.models = self.mod / "files" / "models"
        self.work = self.mod / "blender" / STEM
        self.send = self.work / f"{STEM}.glb"

    def blender_stood_in(self) -> ExitStack:
        """Blender recorded, never started (what it opens: self.opened), and the game's model export for it made up."""
        from test_modelblender import PaintedLibrary
        stack = ExitStack()
        stack.enter_context(mock.patch("rusemod.blender.open_model_to_change",
                                       lambda b, model, send, words: self.opened.append(Path(model)) or None))
        real = __import__("rusemod.models", fromlist=["Library"]).Library

        class Library(PaintedLibrary):
            """The made-up game's own library for what the Studio looks up (find, parts), PaintedLibrary's model and
            pictures for what Blender is given."""

            def __init__(self, game=None):
                super().__init__(game)
                self._real = real(game) if game is not None else None

            def find(self, name, lighter=True):
                return self._real.find(name, lighter=lighter) if self._real is not None else name

            def close(self):
                if self._real is not None:
                    self._real.close()
        stack.enter_context(mock.patch("rusemod.models.Library", Library))
        return stack

    def his_file(self, name: str, data: bytes) -> Path:
        """A model file of the modder's own on his PC (what Import model's file picker would give)."""
        f = self.home / "his models" / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        return f

    # --- what the page says ---
    def said(self, name: str, *args, **kw) -> dict:
        """`name` called as the page calls it, once per language: {lang: its answer, or the refusal's words}."""
        from ruse_studio.api import StudioError
        out = {}
        for lang in LANGS:
            self.api.set_pref("lang", lang)
            try:
                out[lang] = getattr(self.page, name)(*args, **kw)
            except StudioError as exc:
                out[lang] = str(exc)
        self.api.set_pref("lang", "us")
        return out

    def refusal(self, name: str, *args, **kw) -> str | None:
        """`name` called as the page calls it, in English: the refusal's words, or None when it was done."""
        from ruse_studio.api import StudioError
        try:
            getattr(self.page, name)(*args, **kw)
            return None
        except StudioError as exc:
            return str(exc)

    def assert_worded(self, said: dict, english: str | None = None) -> None:
        """Every language's words for one thing the page says: English as `english` when given, every other language
        its own words (never the English left in, never Python's words, no blank left unfilled)."""
        if english is not None:
            self.assertEqual(said["us"], english)
        for lang in LANGS:
            with self.subTest(lang=lang):
                text = said[lang]
                self.assertIsInstance(text, str, lang)
                self.assertTrue(text, lang)
                if lang != "us":
                    self.assertNotEqual(text, said["us"], f"{lang}: English left in")
                for bad in PYTHON_WORDS:
                    self.assertNotIn(bad, text, lang)
                self.assertNotRegex(text, r"\{[a-z_0-9]*\}", lang)

    def words(self, lang: str = "us") -> dict:
        from ruse_studio.api import words
        return words(lang)

    # --- the mod ---
    def files(self) -> dict:
        return tree(self.mod)

    def model_files(self) -> list:
        return sorted(p.name for p in self.models.iterdir()) if self.models.is_dir() else []

    def record(self, stem: str = STEM) -> dict:
        return json.loads((self.models / f"{stem}.json").read_text(encoding="utf-8"))

    def built(self, *mods: Path):
        """The mods (this one when none given) built on the made-up game as the build makes a copy: build_pack, then
        each new unit's own model written into the game's model packs (KeptModels, write_unit_model, as rusemod.build's
        copy step). Returns (build_pack's result, {unit: write_unit_model's Written}, the words of a model that couldn't
        be written, as the build says them: "<mod>: files/models/<file>: <why>")."""
        result = build_pack(Edat(unit_data()), [load_mod(m) for m in (mods or (self.mod,))], "0", Edat(zz_win()))
        written, stopped = {}, []
        if result.errors or not result.own_models:
            return result, written, stopped
        from rusemod.build import _own_stem, _pack_full
        kept = unitmodel.KeptModels(None)
        try:
            for unit, (source, glb, mod_id) in sorted(result.own_models.items()):
                try:
                    prep, textures = kept.get(glb)
                    written[unit] = unitmodel.write_unit_model(Edat(zz_win()), source, _own_stem(unit), prep,
                                                               textures=textures)
                except (unitmodel.UnitModelError, ValueError, OSError, struct.error) as exc:
                    stopped.append(f"{mod_id}: files/models/{Path(glb).name}: {_pack_full(exc)}")
        finally:
            kept.close()
        return result, written, stopped

    def build_errors(self, result) -> list:
        return [f.message for f in result.errors]

    def problems(self) -> list:
        """The Studio's own check of the mod (check_mod): each problem's words."""
        return [p.get("problem") for p in self.page.check_mod()["problems"]]
