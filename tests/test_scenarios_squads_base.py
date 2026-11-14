"""Scenario tests' base: a squad soldier by soldier, as a player meets it in the RUSE Studio (the owner, overnight
2026-11-13: "really limit test some of the unique situations players can find themselves in when building new things
with ... our apps"; "Not just unusual. Usual and unusual situations. Player can find themselves in when making new mods
in our apps.").

The made-up game is the squad tests' own (tests/test_squadcount.py unit_data, tests/test_animactions.py clips_pack, as
test_squadcount's InTheStudio builds its index): a squad with riflemen and a bazooka man drawing two models, its fallen
soldier and its far-away figure, a rifle and a bazooka whose ammunition has NeedModelChange; a squad of three charges
(each NeedModelChange); a tank; the game's one setting for every squad (5 soldiers). A fresh platform folder per test,
a mod made with New mod and the squad copied with New unit, every call made as the page makes it (rusemod.webui.page_api:
a refusal said in the Studio's language), in each of the Studio's 11 languages where the page says something.

Stood in, as the squad tests do, for what a test can't run: Blender (it is never started: what it would write when a
squad opens and when it sends is written here), the game's 3D model library and its export (the made-up game has no
model packs: test_squadblender's Lib and game_glb), and the fitting of a model file (rusemod.unitmodel.import_model:
a real .glb with the fitting's report is written, as Import model writes one, so the build reads it). Everything else
is the Studio's and the build's own: the records, the files, the squad's number, the soldiers' looks, the words.

Each scenario ends with what the page says (every language's words), the mod's files, the mod's build on the made-up
game (rusemod.build.build_pack, as test_squadcount's InTheBuild builds) and the Studio's own check of the mod (check_mod,
which the window runs when a mod is picked and before Test in game).

FOR: the squads scenarios (release 0.9.8.20, overnight 2026-11-13/14, D:/RUSE-2.0/scratch/release-0920/scenarios/squads).
USED-BY: tests/test_scenarios_squads_*.py."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rusemod import build
from rusemod.edat import Edat
from rusemod.modelin import RIGGED, Part, Prepared, write_glb
from rusemod.webui import page_api
from test_animactions import clips_pack
from test_squadblender import Closed, Lib, game_glb
from test_squadcount import E, HEAVY, RIFLE, unit_data

GAME_SQUAD = E + "Descriptor_Unit_Squad"        # the made-up game's squad: riflemen and a bazooka man
CHARGES = E + "Descriptor_Unit_Charges"         # its squad of three charges (each fired by one of its last men)
TANK = E + "Descriptor_Unit_Tank"
NAME = "My Squad"
STEM = "Descriptor_Unit_My_Squad"
SQUAD = E + STEM
RIFLE_MODEL, HEAVY_MODEL = RIFLE.lower(), HEAVY.lower()
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
PYTHON_WORDS = ("Traceback", "Errno", "WinError", "KeyError", "TypeError", "ValueError", "NoneType", "object has no")


def tree(folder: Path) -> dict:
    """{path inside `folder`: its bytes} of every file in it."""
    folder = Path(folder)
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def model_glb(like: str, mark: bytes = b"") -> bytes:
    """A soldier's model as Import model saves it (rusemod.modelin.write_glb): a rigged part on the soldier's bones, one
    picture (its colour holding `mark`, so two looks differ), fitted to the game model `like`."""
    part = Part(RIGGED, 0, [(0.0, 0.0, 100.0), (5.0, 0.0, 150.0), (6.0, 1.0, 195.0)], [(0.0, 0.0, 1.0)] * 3,
                [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], [(0, 1, 2)],
                skin=[[("bip01", 255)], [("bip01 spine", 200), ("bip01", 55)], [("bip01 head", 255)]])
    pixels = (bytes([200, 100, 50, 77]) * 15) + (mark[:4].ljust(4, b"\0"))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "m.glb"
        write_glb(Prepared([part], [["body.png", 4, 4, pixels]], {"rigged": True}), out, like)
        return out.read_bytes()


class GameLib(Lib):
    """test_squadblender's model library stand-in (no packs) with no pack read (`where` empty), as the Units list asks
    it (StudioApi._modelless: nothing known, nothing left out)."""
    where: dict = {}


class MadeUpSquadGame(unittest.TestCase):
    """The made-up game with the squad, its index built once for the class (test_squadcount's InTheStudio)."""

    @classmethod
    def setUpClass(cls):
        from rusemod.index import build_index
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        data = cls.game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_GladPatchableWin.dat").write_bytes(unit_data())
        (data / "ZZ_Win.dat").write_bytes(clips_pack())
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()


class SquadScenario(MadeUpSquadGame):
    """A player's mod with a new squad copying the game's (New mod, New unit), the Studio called as the page calls it.
    `self.opened`: each Blender the Studio would have started ([manifest]); `self.fits`: each fitting asked for."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home)
        self.api._look_models = lambda address: ([RIFLE_MODEL, HEAVY_MODEL], [])   # (no model packs here)
        self.api._blender = lambda: self.home / "blender" / "blender.exe"
        self.page = page_api(self.api)
        self.opened, self.fits = [], []
        for target, stand in (("rusemod.unitmodel.import_model", self.fitted), ("rusemod.models.Library", GameLib),
                              ("rusemod.gltf.model_glb",
                               lambda lib, name, side=2048, rest_bones=False: game_glb(name)),
                              ("rusemod.blender.open_squad_to_change",
                               lambda b, manifest: self.opened.append(manifest) or Closed())):
            patcher = mock.patch(target, stand)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.addCleanup(self.api.set_pref, "lang", "us")
        self.mod = Path(self.page.new_mod("Squads")["current"])
        self.squad = self.page.new_unit(GAME_SQUAD, NAME, 50)["address"]
        self.assertEqual(self.squad, SQUAD)
        self.models = self.mod / "files" / "models"
        self.work = self.mod / "blender" / STEM / "squad"

    # --- stand-ins ---
    def fitted(self, game, source_model, model_file, out, **kw):
        """rusemod.unitmodel.import_model stood in (test_unitmodel has the fitting): the file fitted to `source_model`
        written as Import model writes one, its report."""
        self.fits.append((Path(model_file).name, source_model))
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        mark = bytes.fromhex(sha(Path(model_file).read_bytes())[:8]) if Path(model_file).is_file() else b""
        Path(out).write_bytes(model_glb(source_model, mark))    # (another file's bytes: another look)
        return {"file": Path(model_file).name, "vertices": 3, "triangles": 1, "rigged": True, "like": source_model}

    def model_file(self, name: str, data: bytes = b"glTF") -> Path:
        """A model file of the modder's own on his PC (what Import model's file picker would give)."""
        f = self.home / "his models" / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        return f

    def manifest(self) -> dict:
        return json.loads((self.work / "squad.json").read_text(encoding="utf-8"))

    def blender_opened(self) -> None:
        """What Blender writes when the squad opens (rusemod.blender_model.open_squad): each soldier as he opened."""
        m = self.manifest()
        base = Path(m["base"])
        base.mkdir(parents=True, exist_ok=True)
        listed = {}
        for s in m["soldiers"]:
            data = Path(s["file"]).read_bytes()
            (base / f"{s['id']}.glb").write_bytes(data)
            listed[s["id"]] = {"file": str(base / f"{s['id']}.glb"), "sha256": sha(data)}
        (base / "base.json").write_text(json.dumps({"session": m["session"], "soldiers": listed}), encoding="utf-8")

    def blender_sends(self, changed: dict) -> None:
        """What Blender's Send writes (rusemod.blender_model.send_squad): one file per soldier ({id: its bytes} for the
        ones the modder changed, the others as they opened)."""
        m = self.manifest()
        sent = Path(m["sent"])
        sent.parent.mkdir(parents=True, exist_ok=True)
        listed = {}
        for s in m["soldiers"]:
            data = changed.get(s["id"]) or (Path(m["base"]) / f"{s['id']}.glb").read_bytes()
            f = sent.parent / f"{s['id']}.glb"
            f.write_bytes(data)
            listed[s["id"]] = {"file": str(f), "sha256": sha(data), "objects": [s["name"]], "alpha": s.get("alpha") or {}}
        sent.write_text(json.dumps({"session": m["session"], "soldiers": listed, "left_out": []}), encoding="utf-8")

    # --- what the page says ---
    def refused(self, name: str, *args) -> dict:
        """`name` called as the page calls it, once per language: {lang: the refusal's words} (None: not refused)."""
        from ruse_studio.api import StudioError
        out = {}
        for lang in LANGS:
            self.api.set_pref("lang", lang)
            try:
                getattr(self.page, name)(*args)
                out[lang] = None
            except StudioError as exc:
                out[lang] = str(exc)
        self.api.set_pref("lang", "us")
        return out

    def assert_worded(self, said: dict, english: str | None = None) -> None:
        """Every language's words for one thing the page says: English as `english` when given, every other language
        its own words (never the English left in, never Python's words, no blank left unfilled)."""
        if english is not None:
            self.assertEqual(said["us"], english)
        for lang in LANGS:
            with self.subTest(lang=lang):
                text = said[lang]
                self.assertTrue(text, lang)
                if lang != "us":
                    self.assertNotEqual(text, said["us"], f"{lang}: English left in")
                for bad in PYTHON_WORDS:
                    self.assertNotIn(bad, text, lang)
                self.assertNotRegex(text, r"\{[a-z_0-9]*\}", lang)

    def words(self, lang: str) -> dict:
        from ruse_studio.api import words
        return words(lang)

    def info(self, lang: str = "us", address: str = SQUAD) -> dict:
        return self.page.squad_info(address, lang)

    def every_language_info(self, address: str = SQUAD) -> dict:
        return {lang: self.info(lang, address) for lang in LANGS}

    # --- the mod ---
    def files(self) -> dict:
        return tree(self.mod)

    def soldier_files(self) -> list:
        return sorted(p.name for p in self.models.iterdir()) if self.models.is_dir() else []

    def built(self, *mods: Path):
        """The mods (this one when none given) built on the made-up game, as the build reads them: (result, the built
        objects or None when nothing changed)."""
        arc = Edat(unit_data())
        result = build.build_pack(arc, [build.load_mod(m) for m in (mods or (self.mod,))], "0", Edat(clips_pack()))
        loaded = build.load_pack(Edat(arc.to_bytes(result.changed))) if result.changed else None
        return result, loaded

    def errors(self, result) -> list:
        return [f.message for f in result.errors]

    def problems(self) -> list:
        """The Studio's own check of the mod (check_mod): each problem's words."""
        return [p.get("problem") for p in self.page.check_mod()["problems"]]
