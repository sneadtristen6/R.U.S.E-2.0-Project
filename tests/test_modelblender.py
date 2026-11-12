"""A squad's soldier changed in Blender and brought back (ruse_studio.modelblender; rusemod.blender's
open_model_to_change and ask_to_send; rusemod.blender_model, run by Blender). The owner's order of 2026-11-10, item 4:
a player couldn't give a squad a model of his own (Open in Blender was a painting door behind Custom uniform)."""
import json
import re
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from rusemod import blender

SQUAD = "$/GFX/Everything/Descriptor_Unit_My_Riflemen"
RIFLEMAN = "ww2\\res3d\\units\\us\\infanterie\\us_soldier_modellod0.ase2ndfbin"
BAZOOKA = "ww2\\res3d\\units\\us\\infanterie\\us_soldier_bazooka_modellod0.ase2ndfbin"


def answer_send(send: Path, before=None):
    """A stand-in for the Blender changing the model: waits for the Studio's request, sends, answers."""
    folder = send.parent

    def run():
        end = time.monotonic() + 5
        while not (folder / blender.SEND_REQUEST).exists() and time.monotonic() < end:
            time.sleep(0.02)
        if before:
            before()
        send.write_bytes(b"glTF-sent")
        (folder / blender.SEND_DONE).write_text(json.dumps({"file": str(send)}), encoding="utf-8")
        (folder / blender.SEND_REQUEST).unlink(missing_ok=True)
    t = threading.Thread(target=run)
    t.start()
    return t


class AskToSend(unittest.TestCase):
    def test_answered(self):
        with tempfile.TemporaryDirectory() as d:
            send = Path(d) / "My_Riflemen.glb"
            t = answer_send(send)
            self.assertEqual(blender.ask_to_send(send, timeout=5), str(send))
            t.join()
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), [send.name])  # request and answer both gone

    def test_no_blender_answers(self):
        with tempfile.TemporaryDirectory() as d:
            send = Path(d) / "My_Riflemen.glb"
            self.assertIsNone(blender.ask_to_send(send, timeout=0.3))
            self.assertFalse((Path(d) / blender.SEND_REQUEST).exists())  # a Blender opened later won't answer it

    def test_the_changer_uses_the_same_file_names(self):
        source = blender.CHANGER.read_text(encoding="utf-8")
        names = re.search(r'^SEND_REQUEST, SEND_DONE = "([^"]+)", "([^"]+)"', source, re.M).groups()
        self.assertEqual(names, (blender.SEND_REQUEST, blender.SEND_DONE))
        self.assertIn('export_format="GLB"', source)            # File > Export > glTF Binary, as a modder would
        self.assertIn("disable_bone_shape=True", source)         # the import the Studio's painting door uses

    def test_blender_is_started_with_the_changer(self):
        with mock.patch("subprocess.Popen") as popen:
            blender.open_model_to_change(Path("C:/b/blender.exe"), Path("w/m.glb"), Path("w/X.glb"), Path("w/words.json"))
        args = popen.call_args[0][0]
        self.assertEqual(args[:3], ["C:\\b\\blender.exe" if "\\" in str(Path("C:/b/blender.exe")) else "C:/b/blender.exe",
                                    "--python", str(blender.CHANGER)])
        self.assertEqual(args[3:], ["--", str(Path("w/m.glb")), str(Path("w/X.glb")), str(Path("w/words.json"))])


class StudioCalls(unittest.TestCase):
    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.mod.mkdir()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._mod_dir = lambda: self.mod
        self.api._look_models = lambda address: ([BAZOOKA, RIFLEMAN], [])
        self.api._own_model_file = lambda address: self.mod / "files" / "models" / "Descriptor_Unit_My_Riflemen.glb"
        self.api._blender = lambda: Path("C:/b/blender.exe")
        self.api.look = lambda address: {"models": [], "new_unit": True, "soldiers": True}
        self.work = self.mod / "blender" / "Descriptor_Unit_My_Riflemen"
        self.send = self.work / "Descriptor_Unit_My_Riflemen.glb"

    def tearDown(self):
        self.dir.cleanup()

    def _open(self, lang="us"):
        exported, started = [], []

        def export(lib, names, out, side=2048, rest_bones=False):
            exported.append((names, rest_bones))
            f = Path(out) / "us_soldier_model.glb"
            f.write_bytes(b"glTF-game")
            return [{"file": str(f)}]

        class Lib:
            def __init__(self, _game):
                pass

            def close(self):
                pass
        with mock.patch("rusemod.models.Library", Lib), mock.patch("rusemod.gltf.export", export), \
                mock.patch("rusemod.blender.open_model_to_change",
                           lambda b, model, send, words: started.append((model, send, words)) or "proc"):
            res = self.api.model_blender(SQUAD, lang)
        return res, exported, started

    def test_opens_the_rifleman_with_his_bones_in_place(self):
        res, exported, started = self._open()
        self.assertEqual(exported, [([RIFLEMAN], True)])          # the rifleman, not the bazooka man; real bones
        self.assertEqual(res["work"], str(self.work))               # the mod's blender folder, under the unit's name
        self.assertEqual(started[0][0], self.work / "us_soldier_model.glb")
        self.assertEqual(started[0][1], self.send)                  # what Blender sends lands here
        self.assertEqual(self.api._blenders[str(self.work)], "proc")
        words = json.loads((self.work / "words.json").read_text(encoding="utf-8"))
        self.assertEqual(words["send"], "Send to the R.U.S.E. Studio")
        self.assertEqual(len(words["hint"]), 2)

    def test_the_words_blender_shows_are_in_the_studio_s_language(self):
        self._open("fr")
        words = json.loads((self.work / "words.json").read_text(encoding="utf-8"))
        self.assertEqual(words["send"], "Envoyer au R.U.S.E. Studio")

    def test_work_goes_on_from_what_was_sent_last(self):
        self.work.mkdir(parents=True)
        self.send.write_bytes(b"glTF-mine")
        res, exported, started = self._open()
        self.assertEqual(exported, [])                              # the game's soldier isn't written again
        self.assertEqual(started[0][0], self.send)
        self.assertEqual(res["file"], str(self.send))

    def test_the_work_folder_is_never_packed_or_built(self):
        """Export packs only a mod's own files and src/, text/, files/, maps/, scripts/: the blender folder stays home."""
        from rusemod import package
        self.assertNotIn("blender", package.FOLDERS)
        self.assertNotIn("blender", package.TOP_FILES)

    def test_a_game_unit_or_no_blender_says_what_to_do(self):
        from ruse_studio.api import StudioError
        self.api._blender = lambda: None
        with self.assertRaisesRegex(StudioError, "Blender isn't found on this PC"):
            self.api.model_blender(SQUAD)
        self.api._own_model_file = lambda address: None
        with self.assertRaisesRegex(StudioError, "Only a new unit made in this mod"):
            self.api.model_blender(SQUAD)

    def test_bring_back_asks_an_open_blender_then_imports(self):
        self.work.mkdir(parents=True)
        imported = []
        self.api.model_import = lambda address, file, size=1.0: imported.append((address, file, size)) or {
            "model": {"rigged": True}}

        class Running:
            def poll(self):
                return None
        self.api._blenders[str(self.work)] = Running()
        t = answer_send(self.send)
        res = self.api.model_blender_back(SQUAD)
        t.join()
        self.assertEqual(imported, [(SQUAD, str(self.send), 1.0)])
        self.assertEqual(self.send.read_bytes(), b"glTF-sent")
        self.assertEqual(res["model"], {"rigged": True})
        self.assertEqual(res["work"], str(self.work))

    def test_bring_back_after_blender_closed_uses_what_it_sent(self):
        self.work.mkdir(parents=True)
        self.send.write_bytes(b"glTF-sent")
        imported = []
        self.api.model_import = lambda address, file, size=1.0: imported.append(file) or {"model": {}}

        class Closed:
            def poll(self):
                return 0
        self.api._blenders[str(self.work)] = Closed()
        with mock.patch("rusemod.blender.ask_to_send", side_effect=AssertionError("a closed Blender isn't asked")):
            self.api.model_blender_back(SQUAD)
        self.assertEqual(imported, [str(self.send)])

    def test_bring_back_with_nothing_sent_says_what_to_click(self):
        from ruse_studio.api import StudioError
        with self.assertRaisesRegex(StudioError, "Nothing has come back from Blender yet"):
            self.api.model_blender_back(SQUAD)


class EachSoldier(unittest.TestCase):
    """Each of a squad's soldiers changed in Blender on his own (the owner, 2026-11-11, on the step-4 test copy: the
    big-head squad's bazooka man "did not get scaled", Change it in Blender having opened the riflemen only; then
    "edit any individual in like a normal rifleman squad ... inside Blender. Or add a new model or attach it with
    bones"). The squad here: riflemen and a bazooka man drawing two models (StudioApi._soldier_kinds stood in)."""
    def setUp(self):
        StudioCalls.setUp(self)   # (the same made-up mod and stand-ins; its own tests aren't run again here)
        self.api._soldier_kinds = lambda address: {"fusilier": RIFLEMAN, "bazooka": BAZOOKA}
        self.his_work = self.mod / "blender" / "Descriptor_Unit_My_Riflemen@bazooka"
        self.his_send = self.his_work / "Descriptor_Unit_My_Riflemen@bazooka.glb"

    def tearDown(self):
        StudioCalls.tearDown(self)

    def _open(self, lang="us", kind=None):
        exported, started = [], []

        def export(lib, names, out, side=2048, rest_bones=False):
            exported.append((names, rest_bones))
            f = Path(out) / "game_soldier.glb"
            f.write_bytes(b"glTF-game")
            return [{"file": str(f)}]

        class Lib:
            def __init__(self, _game):
                pass

            def close(self):
                pass
        with mock.patch("rusemod.models.Library", Lib), mock.patch("rusemod.gltf.export", export), \
                mock.patch("rusemod.blender.open_model_to_change",
                           lambda b, model, send, words: started.append((model, send, words)) or "proc"):
            res = self.api.model_blender(SQUAD, lang, kind)
        return res, exported, started

    def test_his_own_opens_him_alone_with_his_bones_in_place(self):
        res, exported, started = self._open(kind="bazooka")
        self.assertEqual(exported, [([BAZOOKA], True)])             # his game model, not the riflemen's; real bones
        self.assertEqual((res["work"], res["kind"]), (str(self.his_work), "bazooka"))   # beside the unit's: <unit>@bazooka
        self.assertEqual(started[0][1], self.his_send)                # what Blender sends for him lands here
        self.assertEqual(self.api._blenders[str(self.his_work)], "proc")
        words = json.loads((self.his_work / "words.json").read_text(encoding="utf-8"))
        self.assertEqual(words["send"], "Send to the R.U.S.E. Studio")
        self.assertFalse(self.work.exists())                          # the riflemen's folder isn't touched

    def test_the_riflemen_by_name_are_the_model_row_s(self):
        res, exported, started = self._open(kind="fusilier")
        self.assertEqual(exported, [([RIFLEMAN], True)])
        self.assertEqual((res["work"], res["kind"]), (str(self.work), None))
        self.assertEqual(started[0][1], self.send)

    def test_each_goes_on_from_his_own_last_sending(self):
        for folder, send, data in ((self.work, self.send, b"glTF-riflemen"), (self.his_work, self.his_send, b"glTF-his")):
            folder.mkdir(parents=True)
            send.write_bytes(data)
        res, exported, started = self._open(kind="bazooka")
        self.assertEqual((exported, started[0][0], res["file"]), ([], self.his_send, str(self.his_send)))
        res, exported, started = self._open()
        self.assertEqual((exported, started[0][0]), ([], self.send))

    def test_bring_back_gives_the_model_to_him_alone(self):
        self.his_work.mkdir(parents=True)
        self.his_send.write_bytes(b"glTF-sent")
        imported = []
        self.api.model_import = lambda address, file, size=1.0, kind=None: imported.append((address, file, size, kind)) or {
            "model": {"rigged": True}}

        class Closed:
            def poll(self):
                return 0
        self.api._blenders[str(self.his_work)] = Closed()
        res = self.api.model_blender_back(SQUAD, 1.0, "bazooka")
        self.assertEqual(imported, [(SQUAD, str(self.his_send), 1.0, "bazooka")])   # Import model's kind: his alone
        self.assertEqual((res["work"], res["kind"]), (str(self.his_work), "bazooka"))
        from ruse_studio.api import StudioError
        with self.assertRaisesRegex(StudioError, "Nothing has come back from Blender yet"):   # (the riflemen sent nothing)
            self.api.model_blender_back(SQUAD)

    def test_a_soldier_the_squad_hasn_t_got_and_a_squad_of_one_model_are_refused(self):
        from ruse_studio.api import StudioError
        with self.assertRaisesRegex(StudioError, "This squad has no soldier called medic"):
            self.api.model_blender(SQUAD, "us", "medic")
        with self.assertRaisesRegex(StudioError, "This squad has no soldier called medic"):
            self.api.model_blender_back(SQUAD, 1.0, "medic")
        self.api._soldier_kinds = lambda address: {}
        with self.assertRaisesRegex(StudioError, "no soldiers of another kind"):
            self.api.model_blender(SQUAD, "us", "bazooka")
        self.assertFalse((self.mod / "blender").exists())

    def test_his_game_model_missing_is_said(self):
        from ruse_studio.api import StudioError
        self.api._look_models = lambda address: ([RIFLEMAN], [])
        with self.assertRaisesRegex(StudioError, "This soldier has no 3D model the Studio can open"):
            self._open(kind="bazooka")


if __name__ == "__main__":
    unittest.main()
