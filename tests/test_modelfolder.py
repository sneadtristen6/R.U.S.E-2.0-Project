"""Where the mod keeps a unit's own model, and Show in folder (StudioApi.show_model_folder; look()'s, _kind_rows' and
building_look()'s "kept"; ui/app.js keptRow, modelKeptRow, modelBox, kindsBox, buildingModelBox). A modder, Angelo,
2026-11-10 on Discord: "is it the possibility of changing infantry models a WIP? i can't find a way to do it for now";
the page named the file he had picked, never the mod's own copy of it (Documents\\RUSE 2.0\\Mods\\<mod>\\files\\models\\
<unit>.glb), had no button to open that folder, and named Change it in Blender's work folder only once that was
clicked. Step 3 of the owner's one-patch plan: "Angelo's leftovers: a model-folder button".

Every place a unit's own model is kept in the mod, each opened by the call with the starter stood in (nothing opens on
the PC): a new unit's own model (files/models/<its name>.glb), a squad's heavy-weapon soldier's (files/models/<its
name>@bazooka.glb), its own copy of the model it draws, a new unit's and a game unit's (files/models/<its name>.copy.toml,
its paint beside it), a new building's (files/buildings/<its name>/) and Change it in Blender's work folder
(<mod>/blender/<its name>/); refused without a mod, for a game unit with nothing of its own, and while nothing is there
yet, the page saying where it will be. The fitting (rusemod.unitmodel.import_model) and Blender are stood in for:
test_soldierkinds and test_modelblender have them. Then the page's code (no browser here): the Model row's More starts
with the row, Show in folder has its tooltip and calls the Studio, each place on the page, the words in the eleven
languages and on the stand-in page."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import re
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod.play import Starter
from ruse_studio import errortext
from ruse_studio.api import StudioApi, StudioError
from test_animactions import clips_pack
from test_lookmoves import BLANK, LANGS, controls, function_text, read
from test_soldierkinds import E, HEAVY, RIFLE, unit_data

WORDS = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "words.toml"
NEW_WORDS = ("model_kept", "model_kept_later", "model_kept_copy", "model_kept_uniform", "tip_model_folder",
             "tip_model_folder_none", "model_blender_kept", "model_blender_kept_later", "tip_model_blender_folder",
             "tip_model_blender_folder_none")
NO_MODEL = "This unit has no model of its own in your mod yet: click Import model… to give it one."
NO_BLENDER = "There are no Blender files for this unit yet: click Change it in Blender first."


def tail(address: str) -> str:
    return address.rsplit("/", 1)[-1]


class TheCall(unittest.TestCase):
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

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.opened = []   # (the starter stood in: what would open on the PC)
        self.api = self.studio(self.home)
        self.mod = Path(self.home, "mods", "kept")
        (self.mod / "src").mkdir(parents=True)
        (self.mod / "mod.toml").write_text('[mod]\nid = "kept"\nversion = "1.0.0"\n', encoding="utf-8")
        self.api.choose_mod(str(self.mod))
        # (the made-up game: a squad whose riflemen and heavy-weapon soldier draw two models, and a squad of one model)
        self.squad = self.api.new_unit(E + "Descriptor_Unit_Squad", "Kept Squad", 5)["address"]
        self.one = self.api.new_unit(E + "Descriptor_Unit_One", "Kept One", 5)["address"]
        self.models = self.mod / "files" / "models"
        self.source = Path(self.home, "rider.glb")
        self.source.write_bytes(b"glTF")

    def studio(self, home):
        api = StudioApi(index_path=self.index, game_dir=self.game, home=home, starter=Starter(open_url=self.opened.append))
        # (the models the game's packs hold, as Library.find names them: the made-up game has no model packs)
        api._look_models = lambda address: ([RIFLE.lower(), HEAVY.lower()] if "One" not in address else [RIFLE.lower()], [])
        api._blender = lambda: None    # (no Blender looked for on this PC)
        return api

    @staticmethod
    def fitted(game, source_model, model_file, out, **kw):
        """rusemod.unitmodel.import_model stood in for: the file written, its report."""
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_bytes(b"glTF fitted")
        return {"file": Path(model_file).name, "vertices": 3, "triangles": 1, "rigged": True, "like": source_model}

    def imported(self, address, kind=None):
        with mock.patch("rusemod.unitmodel.import_model", self.fitted):
            return self.api.model_import(address, str(self.source), kind=kind)

    def test_a_new_unit_s_own_model_where_it_will_be_then_where_it_is(self):
        file = self.models / f"{tail(self.one)}.glb"
        kept = self.api.look(self.one)["kept"]
        self.assertEqual(kept, {"file": str(file), "file_made": False, "copy": False, "folder": str(self.models),
                                "made": False, "blender": str(self.mod / "blender" / tail(self.one)),
                                "blender_made": False})
        with self.assertRaises(StudioError) as said:
            self.api.show_model_folder(self.one)
        self.assertEqual(str(said.exception), NO_MODEL)
        self.assertEqual(self.opened, [])
        kept = self.imported(self.one)["kept"]
        self.assertEqual((kept["file"], kept["file_made"], kept["made"], kept["copy"]), (str(file), True, True, False))
        self.assertEqual(self.api.show_model_folder(self.one), {"opened": str(self.models)})
        self.assertEqual(self.opened, [str(self.models)])
        # (taken out again: the page says where it will be, and the folder isn't opened for it)
        self.api.model_import_remove(self.one)
        self.assertFalse(self.api.look(self.one)["kept"]["made"])
        with self.assertRaisesRegex(StudioError, "no model of its own in your mod yet"):
            self.api.show_model_folder(self.one)
        self.assertEqual(self.opened, [str(self.models)])

    def test_a_squad_s_heavy_weapon_soldier_s_own_model(self):
        """His own (files/models/<its name>@bazooka.glb) with none for the riflemen yet: the Model row names the
        riflemen's file, still to come, and its Show in folder opens the folder his is in."""
        res = self.imported(self.squad, "bazooka")
        his = self.models / f"{tail(self.squad)}@bazooka.glb"
        self.assertTrue(his.is_file())
        rows = {r["kind"]: r for r in res["kinds"]}
        self.assertEqual((rows["fusilier"]["kept"], rows["fusilier"]["own"]),
                         (str(self.models / f"{tail(self.squad)}.glb"), False))
        self.assertEqual((rows["bazooka"]["kept"], rows["bazooka"]["own"]), (str(his), True))
        kept = res["kept"]
        self.assertEqual((kept["file"], kept["file_made"], kept["made"]),
                         (str(self.models / f"{tail(self.squad)}.glb"), False, True))
        self.assertEqual(self.api.show_model_folder(self.squad), {"opened": str(self.models)})
        self.assertEqual(self.opened, [str(self.models)])

    def test_its_own_copy_a_new_unit_s_and_a_game_unit_s(self):
        self.api.model_copy(self.one)
        copy = self.models / f"{tail(self.one)}.copy.toml"
        kept = self.api.look(self.one)["kept"]
        self.assertEqual((kept["file"], kept["file_made"], kept["copy"], kept["made"]), (str(copy), True, True, True))
        self.assertEqual(self.api.show_model_folder(self.one), {"opened": str(self.models)})
        # a game unit: nothing of it in the mod until it has its own copy (a squad's Custom uniform)
        game = E + "Descriptor_Unit_Squad"
        self.assertIsNone(self.api.look(game)["kept"])
        with self.assertRaisesRegex(StudioError, "Only a new unit made in this mod can get a model of its own"):
            self.api.show_model_folder(game)
        self.api.model_copy(game)
        kept = self.api.look(game)["kept"]
        self.assertEqual((kept["file"], kept["copy"], kept["made"], kept["blender"]),
                         (str(self.models / "Descriptor_Unit_Squad.copy.toml"), True, True, None))
        self.assertEqual(self.api.show_model_folder(game), {"opened": str(self.models)})
        with self.assertRaisesRegex(StudioError, "Only a new unit made in this mod can get a model of its own"):
            self.api.show_model_folder(game, "blender")     # (Change it in Blender is a new unit's)
        self.assertEqual(self.opened, [str(self.models)] * 2)

    def test_a_new_building_s_model(self):
        """files/buildings/<its name>/ (rusemod.buildinglook: building.toml beside its model), made by hand here as
        building_look_import makes it (its fitting needs numpy: test_buildinglook)."""
        folder = self.mod / "files" / "buildings" / tail(self.one)
        stand_ins = {"_building_symbol": "US_Factory", "_piece_table": {"US_Factory": []}, "_card_view": None,
                     "_asset_view": dict.fromkeys(("file", "size", "two_sided", "credit", "triangles", "versions"))}
        patches = [mock.patch.object(StudioApi, k, return_value=v) for k, v in stand_ins.items()]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        file = folder / f"{tail(self.one)}.glb"
        self.assertEqual(self.api.building_look(self.one)["kept"],
                         {"file": str(file), "file_made": False, "made": False, "folder": str(folder)})
        with self.assertRaisesRegex(StudioError, "This building has no model of its own yet"):
            self.api.show_model_folder(self.one, "building")
        folder.mkdir(parents=True)
        file.write_bytes(b"glTF")
        (folder / "building.toml").write_text(f'piece = "Prototype_building"\nmodel = "{file.name}"\n', encoding="utf-8")
        self.assertEqual(self.api.building_look(self.one)["kept"],
                         {"file": str(file), "file_made": True, "made": True, "folder": str(folder)})
        self.assertEqual(self.api.show_model_folder(self.one, "building"), {"opened": str(folder)})
        with self.assertRaisesRegex(StudioError, "Only a new building made in this mod"):
            self.api.show_model_folder(E + "Descriptor_Unit_Squad", "building")
        self.assertIsNone(self.api.building_look(E + "Descriptor_Unit_Squad")["kept"])
        self.assertEqual(self.opened, [str(folder)])

    def test_change_it_in_blender_s_work_folder(self):
        work = self.mod / "blender" / tail(self.squad)
        kept = self.api.look(self.squad)["kept"]
        self.assertEqual((kept["blender"], kept["blender_made"]), (str(work), False))
        with self.assertRaises(StudioError) as said:
            self.api.show_model_folder(self.squad, "blender")
        self.assertEqual(str(said.exception), NO_BLENDER)
        # Change it in Blender makes it (the game model's export and Blender stood in, as in test_modelblender)

        def export(lib, names, out, side=2048, rest_bones=False):
            f = Path(out) / "us_soldier_model.glb"
            f.write_bytes(b"glTF-game")
            return [{"file": str(f)}]

        class Lib:
            def __init__(self, _game):
                pass

            def close(self):
                pass
        self.api._blender = lambda: Path("C:/b/blender.exe")
        with mock.patch("rusemod.models.Library", Lib), mock.patch("rusemod.gltf.export", export), \
                mock.patch("rusemod.blender.open_model_to_change", lambda *a: "proc"):
            res = self.api.model_blender(self.squad)
        self.assertEqual(res["work"], str(work))
        self.assertEqual((res["kept"]["blender"], res["kept"]["blender_made"]), (str(work), True))
        self.assertEqual(self.api.show_model_folder(self.squad, "blender"), {"opened": str(work)})
        self.assertEqual(self.opened, [str(work)])

    def test_each_soldier_s_own_blender_folder(self):
        """A squad's heavy-weapon soldier changed in Blender on his own (the owner, 2026-11-11: "edit any individual in
        like a normal rifleman squad ... inside Blender"): his work folder <mod>/blender/<its name>@bazooka, beside the
        riflemen's, on his row before a click and opened by his Show in folder once there."""
        work = self.mod / "blender" / tail(self.squad)
        his = self.mod / "blender" / f"{tail(self.squad)}@bazooka"
        rows = {r["kind"]: r for r in self.api.look(self.squad)["kinds"]}
        self.assertEqual({k: (r["blender"], r["blender_made"]) for k, r in rows.items()},
                         {"fusilier": (str(work), False), "bazooka": (str(his), False)})
        with self.assertRaises(StudioError) as said:
            self.api.show_model_folder(self.squad, "blender", "bazooka")
        self.assertEqual(str(said.exception), NO_BLENDER)

        def export(lib, names, out, side=2048, rest_bones=False):
            f = Path(out) / "us_soldier_bazooka_model.glb"
            f.write_bytes(b"glTF-game")
            return [{"file": str(f)}]

        class Lib:
            def __init__(self, _game):
                pass

            def close(self):
                pass
        self.api._blender = lambda: Path("C:/b/blender.exe")
        with mock.patch("rusemod.models.Library", Lib), mock.patch("rusemod.gltf.export", export), \
                mock.patch("rusemod.blender.open_model_to_change", lambda *a: "proc"):
            res = self.api.model_blender(self.squad, "us", "bazooka")
        self.assertEqual((res["work"], res["kind"]), (str(his), "bazooka"))
        rows = {r["kind"]: r for r in res["kinds"]}
        self.assertEqual((rows["fusilier"]["blender_made"], rows["bazooka"]["blender_made"]), (False, True))
        self.assertEqual(res["kept"]["blender_made"], False)          # (the Model row's is the riflemen's: still to come)
        self.assertEqual(self.api.show_model_folder(self.squad, "blender", "bazooka"), {"opened": str(his)})
        self.assertEqual(self.opened, [str(his)])
        with self.assertRaisesRegex(StudioError, "This squad has no soldier called medic"):
            self.api.show_model_folder(self.squad, "blender", "medic")
        with self.assertRaisesRegex(StudioError, "no soldiers of another kind"):   # (a squad of one model)
            self.api.show_model_folder(self.one, "blender", "bazooka")
        self.assertEqual(self.opened, [str(his)])

    def test_refused_without_a_mod_or_for_a_folder_it_doesn_t_have(self):
        api = self.studio(Path(tempfile.mkdtemp(dir=self.tmp.name)))   # (no mod picked)
        for what in ("model", "building", "blender"):
            for address in (self.squad, E + "Descriptor_Unit_Squad"):
                with self.subTest(what=what, address=address), self.assertRaises(StudioError) as said:
                    api.show_model_folder(address, what)
                self.assertEqual(str(said.exception), "Pick or make a mod first.")
        self.assertIsNone(api.look(E + "Descriptor_Unit_Squad")["kept"])
        for what in ("C:/Windows", "mods", ""):
            with self.subTest(what=what), self.assertRaisesRegex(StudioError, "isn't one of the Studio's folders"):
                self.api.show_model_folder(self.squad, what)
        self.assertEqual(self.opened, [])

    def test_its_refusals_said_in_the_studio_s_language_naming_the_page_s_buttons(self):
        words = tomllib.loads(WORDS.read_text(encoding="utf-8"))
        entries = tomllib.loads(errortext.FILE.read_text(encoding="utf-8"))
        for text, label in ((NO_MODEL, "model_import"), (NO_BLENDER, "model_blender")):
            entry = entries[errortext.key_of(text)]
            for lang in LANGS:
                with self.subTest(text=text[:20], lang=lang):
                    self.assertIn(words[label][lang], entry[lang])
        self.api.set_pref("lang", "fr")
        self.assertEqual(str(self.api.page_error(StudioError(NO_MODEL))), entries[errortext.key_of(NO_MODEL)]["fr"])


class ThePage(unittest.TestCase):
    def setUp(self):
        self.app = read("app.js")
        self.fake = read("fake-api.js")
        self.words = tomllib.loads(WORDS.read_text(encoding="utf-8"))

    def test_the_model_row_says_where_first_under_more(self):
        look = function_text(self.app, "lookMovesBox")
        self.assertIn("if (info.kept) more.push(modelKeptRow(address, info.kept, squad));", look)
        first = look.index("more.push(modelKeptRow(")
        self.assertEqual([m.start() for m in re.finditer(r"\bmore\.(?:push|unshift)\(", look) if m.start() < first], [])
        row = function_text(self.app, "modelKeptRow")
        for word in ("w.model_kept_uniform", "w.model_kept_copy", "w.model_kept", "w.model_kept_later",
                     "w.tip_model_folder_none"):
            self.assertIn(word, row)
        self.assertIn('keptRow(address, "model", said, kept.file, kept.folder, kept.made', row)

    def test_show_in_folder_its_tooltip_and_its_call(self):
        row = function_text(self.app, "keptRow")
        made = controls(row)
        self.assertEqual(len(made), 1)
        self.assertIn("textContent: w.where_show", made[0])
        self.assertIn("title: made ? fill(tip, { folder }) : tipNone, disabled: !made", made[0])
        self.assertIn('const tip = what === "blender" ? w.tip_model_blender_folder : w.tip_model_folder;', row)
        # (`kind`: a squad's other soldier's own Blender folder, kindsBox's; null for every other place)
        self.assertIn("await api().show_model_folder(address, what, kind);", row)
        self.assertIn("function keptRow(address, what, said, path, folder, made, tipNone, kind = null) {", self.app)
        self.assertIn("say(fill(w.where_opened, { path: r.opened }), \"ok\");", row)
        self.assertIn('el("code", { className: "where-path", textContent: path })', row)

    def test_each_place_on_the_page(self):
        model = function_text(self.app, "modelBox")    # (a squad's Change it in Blender: its folder before a click)
        self.assertIn('keptRow(address, "blender",', model)
        self.assertIn("if (info.kept && info.kept.blender) showWhere(info.kept.blender, info.kept.blender_made);", model)
        self.assertIn("if (r.work) showWhere(r.work, true);", model)
        self.assertIn("w.model_blender_kept : w.model_blender_kept_later", model)
        kinds = function_text(self.app, "kindsBox")    # (each kind of a squad's soldiers: his file)
        self.assertIn("row.own ? w.model_kept : w.model_kept_later", kinds)
        self.assertIn('textContent: row.kept', kinds)
        # ...and his own Change it in Blender, Bring back the model and Blender folder (the owner, 2026-11-11)
        self.assertIn("if (row.blender) showWhere(row.blender, row.blender_made);", kinds)
        self.assertIn("w.tip_model_blender_folder_none, row.kind)", kinds)
        self.assertIn("api().model_blender(address, state.lang, row.kind)", kinds)
        self.assertIn("api().model_blender_back(address, 1, row.kind)", kinds)
        made = controls(kinds)
        self.assertIn('textContent: w.model_blender, title: w.tip_model_kind_blender', " ".join(made))
        self.assertIn('textContent: w.model_blender_back, title: w.tip_model_kind_blender_back', " ".join(made))
        building = function_text(self.app, "buildingModelBox")
        self.assertIn('keptRow(address, "building", info.kept.made ? w.model_kept : w.model_kept_later, info.kept.file',
                      building)
        self.assertNotIn("model_blender_where", self.app)

    def test_its_words_in_eleven_languages_and_on_the_stand_in_page(self):
        for key in NEW_WORDS + ("where_show", "where_opened"):
            with self.subTest(key=key):
                self.assertEqual(set(self.words[key]), set(LANGS))
                for lang in LANGS:
                    v = self.words[key][lang]
                    self.assertTrue(v.strip(), lang)
                    self.assertEqual(sorted(BLANK.findall(v)), sorted(BLANK.findall(self.words[key]["us"])), lang)
                    self.assertNotRegex(v, "[\u2013\u2014]", lang)
        for key in NEW_WORDS:
            self.assertIn(f'"{key}": {json.dumps(self.words[key]["us"], ensure_ascii=False)}', self.fake, key)
        for key, label in (("tip_model_folder_none", "model_import"), ("tip_model_blender_folder_none", "model_blender"),
                           ("model_kept_uniform", "uniform_custom")):
            for lang in LANGS:
                self.assertIn(self.words[label][lang], self.words[key][lang], (key, lang))
        self.assertNotIn("model_blender_where", self.words)   # (said only after the click: the Blender row's now)
        self.assertNotIn("model_blender_where", self.fake)
        # each soldier's own Blender buttons' tooltips, and the how-tos that name them, in the eleven languages
        for key in ("tip_model_kind_blender", "tip_model_kind_blender_back"):
            with self.subTest(key=key):
                self.assertEqual(set(self.words[key]), set(LANGS))
                self.assertIn(f'"{key}": {json.dumps(self.words[key]["us"], ensure_ascii=False)}', self.fake)
        for key in ("model_kinds_how", "model_blender_how_kinds"):
            for lang in LANGS:
                self.assertIn(self.words["model_blender"][lang], self.words[key][lang], (key, lang))

    def test_the_call_is_the_studio_s_and_the_stand_in_page_s(self):
        self.assertTrue(callable(getattr(StudioApi, "show_model_folder", None)))
        self.assertEqual(StudioApi.UNIT_FOLDERS, ("model", "building", "blender"))
        calls = {m.group(1) for name in ("keptRow", "modelKeptRow", "modelBox", "kindsBox", "buildingModelBox")
                 for m in re.finditer(r"api\(\)\.(\w+)\(", function_text(self.app, name))}
        self.assertIn("show_model_folder", calls)
        self.assertEqual(sorted(c for c in calls if not callable(getattr(StudioApi, c, None))), [])
        self.assertEqual(sorted(c for c in calls if not re.search(rf"\b{c}: async", self.fake)), [])
        self.assertIn('show_model_folder: async (address, what = "model", kind = null) =>', self.fake)
        self.assertIn('if (!["model", "building", "blender"].includes(what))', self.fake)
        self.assertIn("model_blender: async (address, lang, kind = null) =>", self.fake)
        self.assertIn("model_blender_back: async (address, size, kind = null) =>", self.fake)
        # the stand-in page's units say where, as look(), _kind_rows and building_look do
        self.assertIn("kept: fakeKept(address)", self.fake)
        self.assertIn("kept: `${kept}@bazooka.glb`", self.fake)
        self.assertIn("own, kept: made && folder ?", self.fake)


if __name__ == "__main__":
    unittest.main()
