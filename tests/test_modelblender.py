"""A squad's soldier changed in Blender and brought back (ruse_studio.modelblender; rusemod.blender's
open_model_to_change and ask_to_send; rusemod.blender_model, run by Blender). The owner's order of 2026-11-10, item 4:
a player couldn't give a squad a model of his own (Open in Blender was a painting door behind Custom uniform).
ItsOwnShine: a tank, a plane or a soldier brought back keeps its own shine and side colour (the owner, 2026-11-12,
"Keep its own"), through the Studio's real export, Import model's real reading and fitting of pictures, and a
stand-in for what Blender does to materials and pictures."""
import json
import re
import tempfile
import threading
import time
import unittest
from collections import defaultdict
from pathlib import Path
from unittest import mock

from rusemod import blender, gltf, modelin
from rusemod.png import read_png
from test_gltf_bones import FakeLibrary, FakeSpk, parts

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
        kept = self.work / "kept" / self.send.name   # (what Blender sent, each alpha picture back in it: ItsOwnShine)
        self.assertEqual(imported, [(SQUAD, str(kept), 1.0)])
        self.assertEqual(self.send.read_bytes(), b"glTF-sent")
        self.assertEqual(kept.read_bytes(), b"glTF-sent")   # (not a .glb: as sent, and Import model says why)
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
        self.assertEqual(imported, [str(self.work / "kept" / self.send.name)])

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
        his_kept = self.his_work / "kept" / self.his_send.name
        self.assertEqual(imported, [(SQUAD, str(his_kept), 1.0, "bazooka")])   # Import model's kind: his alone
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


# --- its own shine and side colour (ItsOwnShine) ---
TANK = "$/GFX/Everything/Descriptor_Unit_My_Tank"
TANK_MODEL = "ww2\\res3d\\units\\us\\char\\test_tank\\test_tanklod0.ase2ndfbin"
HULL = "ww2\\res3d\\units\\us\\char\\test_tank\\test_tank_hull.tgv"
TURRET = "ww2\\res3d\\units\\us\\char\\test_tank\\test_tank_turret.tgv"
LIKE = {"length": 200.0, "pivot": (0.0, 0.0), "ground": 0.0}


def game_picture(seed: int, w: int, h: int) -> tuple:
    """A picture as the game's model library gives it, (width, height, RGBA): its alpha the side colour (0) where low
    and shine where high, as the game's pictures have it, with a value of its own nearly everywhere."""
    rgba = bytearray()
    for i in range(w * h):
        alpha = 0 if i % 7 == 3 else 250 - (i * seed) % 90
        rgba += bytes([(40 + 3 * i) % 256, (90 + seed) % 256, (11 * i) % 256, alpha])
    return w, h, bytes(rgba)


PICTURES = {HULL: game_picture(5, 8, 4), TURRET: game_picture(9, 4, 4)}
GAME_ALPHA = {"test_tank_hull": PICTURES[HULL][2][3::4], "test_tank_turret": PICTURES[TURRET][2][3::4]}


class PaintedLibrary(FakeLibrary):
    """test_gltf_bones' made-up model and skeleton under any model's name, each of its two draws with a game picture of
    its own (what rusemod.gltf.export reads of rusemod.models.Library)."""

    def __init__(self, _game=None):
        super().__init__()
        self.where = defaultdict(FakeSpk)

    def parts(self, name):
        (hull, _no), (turret, _none) = parts()
        return [(hull, HULL), (turret, TURRET)]

    def picture(self, texture, most=512):
        return PICTURES.get(texture)

    def close(self):
        pass


def blender_sends(start: Path, send: Path, rename: dict | None = None) -> None:
    """What Blender 4.5 does to a model's materials and pictures between the file the Studio opens in it and its Send
    (rusemod.blender_model), as the real one did it on 2026-11-12 with a Sherman, a P-47 and a soldier
    (scratch/animmodels/shine-door/proof-new/proof.json, each step's sent_file): every material and the picture it
    shows kept under its own name (`rename` {name: new name}: renamed there), no extras anywhere, and no picture a
    material doesn't show."""
    doc, views = gltf.glb_views(start.read_bytes())
    for part in ([doc.get("asset") or {}] + doc.get("nodes", []) + doc.get("meshes", []) + doc.get("skins", [])
                 + doc.get("materials", []) + [p for m in doc.get("meshes", []) for p in m.get("primitives", [])]):
        part.pop("extras", None)
    shown = sorted({doc["textures"][m["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]
                    for m in doc.get("materials", []) if (m.get("pbrMetallicRoughness") or {}).get("baseColorTexture")})
    image = {old: k for k, old in enumerate(shown)}
    textures = []
    for m in doc.get("materials", []):
        tex = (m.get("pbrMetallicRoughness") or {}).get("baseColorTexture")
        if tex:
            textures.append({"source": image[doc["textures"][tex["index"]]["source"]]})
            tex["index"] = len(textures) - 1
        m["name"] = (rename or {}).get(m.get("name"), m.get("name"))
    doc["images"], doc["textures"] = [doc["images"][k] for k in shown], textures
    send.parent.mkdir(parents=True, exist_ok=True)
    send.write_bytes(gltf.pack_glb(doc, views))


def fitted(game, source_model, model_file, out, size=1.0, **_more):
    """rusemod.unitmodel.import_model for a model of no game unit (test_unitmodel has the fitting): the file read and
    fitted the importer's own way, its pictures and their alpha too (rusemod.modelin), saved as the mod keeps it."""
    prep = modelin.prepare(modelin.read_model(Path(model_file)), Path(model_file).parent, LIKE, size=size)
    modelin.write_glb(prep, Path(out), source_model)
    return dict(prep.report)


def alphas_in(model: Path) -> dict:
    """{each picture of a model the mod keeps (rusemod.modelin.write_glb's): its alpha, a byte a pixel}."""
    doc, binary = modelin.glb_document(model.read_bytes())
    out = {}
    for m in doc["materials"]:
        k = m["extras"]["rusemod_alpha_texture"]
        _w, _h, rgba = read_png(modelin.glb_image(doc, binary, doc["textures"][k]["source"]))
        out[m["name"]] = bytes(rgba[0::4])
    return out


class ItsOwnShine(unittest.TestCase):
    """A new unit copied from a game tank (and a squad's soldier), changed in Blender and brought back, keeps each
    picture's own alpha (the owner, 2026-11-12: "Keep its own": "Its own shine and side-colour layer goes back in, the
    way the squad page already does it"), byte for byte, through a second trip and a Resize; a material renamed or new
    in Blender has the plain 144 and the import's report says so; a model imported from a file stays flat ("Keep it
    flat"). Real: the Studio's calls, rusemod.gltf.export of a made-up model with pictures, Import model's reading,
    fitting and saving (rusemod.modelin). Stood in: the game (PaintedLibrary), Blender (blender_sends), the fitting to
    a game unit's model (fitted)."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.models = self.mod / "files" / "models"
        api = self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        api._mod_dir = lambda: self.mod
        api._soldier_kinds = lambda address: {}
        api._look_models = lambda address: ([TANK_MODEL], [])
        api._own_model_file = lambda address: self.models / f"{address.rsplit('/', 1)[-1]}.glb"
        api._blender = lambda: Path("C:/b/blender.exe")
        api.look = lambda address: {"look": True}
        self.work = self.mod / "blender" / "Descriptor_Unit_My_Tank"
        self.send = self.work / "Descriptor_Unit_My_Tank.glb"
        self.opened = []

    def tearDown(self):
        self.dir.cleanup()

    def patched(self, fit=fitted):
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(mock.patch("rusemod.models.Library", PaintedLibrary))
        stack.enter_context(mock.patch("rusemod.blender.open_model_to_change",
                                       lambda b, model, send, words: self.opened.append(Path(model)) or None))
        stack.enter_context(mock.patch("rusemod.unitmodel.rigged_first", lambda game, file, models: list(models)))
        stack.enter_context(mock.patch("rusemod.unitmodel.import_model", fit))
        return stack

    def trip(self, address=TANK, kind=None, rename=None, before_back=None) -> dict:
        """Change it in Blender, Blender sends (`rename`: with those materials renamed), Bring back the model."""
        with self.patched():
            res = self.api.model_blender(address, "us", kind) if kind else self.api.model_blender(address)
            start = self.opened[-1]
            blender_sends(start, Path(res["work"]) / f"{Path(res['work']).name}.glb", rename)
            if before_back:
                before_back()
            return self.api.model_blender_back(address, 1.0, kind) if kind else self.api.model_blender_back(address)

    def record(self, stem="Descriptor_Unit_My_Tank") -> dict:
        return json.loads((self.models / f"{stem}.json").read_text(encoding="utf-8"))

    def test_a_tank_keeps_its_own_alpha_byte_for_byte(self):
        res = self.trip()
        self.assertEqual(alphas_in(self.models / "Descriptor_Unit_My_Tank.glb"), GAME_ALPHA)
        report = res["model"]
        self.assertEqual(report["alpha"], {"test_tank_hull": "the model's own", "test_tank_turret": "the model's own"})
        self.assertEqual(report["blender_alpha"], {"test_tank_hull": "its own, put back",
                                                   "test_tank_turret": "its own, put back"})
        self.assertFalse([n for n in report["notes"] if "Blender" in n])            # nothing lost, nothing to say
        self.assertEqual(self.record()["report"]["blender_alpha"], report["blender_alpha"])   # kept with the model
        # what went out: each material's alpha picture beside the game model's file, listed by the material's name
        listed = json.loads((self.work / "alpha.json").read_text(encoding="utf-8"))["alpha"]
        self.assertEqual(listed, {"test_tank_hull": "test_tank_test_tank_hull_alpha.png",
                                  "test_tank_turret": "test_tank_test_tank_turret_alpha.png"})

    def test_a_renamed_material_gets_the_plain_144_and_that_is_said(self):
        res = self.trip(rename={"test_tank_turret": "My turret"})
        got = alphas_in(self.models / "Descriptor_Unit_My_Tank.glb")
        self.assertEqual(got["test_tank_hull"], GAME_ALPHA["test_tank_hull"])        # the other one keeps its own
        self.assertEqual(got["test_tank_turret"], bytes([modelin.PLAIN_ALPHA]) * 16)  # (its picture keeps its name)
        report = res["model"]
        self.assertEqual(report["alpha"]["test_tank_turret"], "plain 144")
        self.assertEqual(report["blender_alpha"]["My turret"], "plain 144: no alpha picture went out to Blender with "
                                                               "a material of this name (renamed or new there)")
        self.assertEqual(report["blender_alpha"]["test_tank_hull"], "its own, put back")
        said = " ".join(report["notes"])
        self.assertIn("so with the plain 144 (no shine or side colour of their own): My turret.", said)
        self.assertIn("didn't come back under that name: test_tank_turret.", said)
        self.assertEqual(self.record()["report"]["notes"], report["notes"])          # in the model's record too

    def test_the_next_trip_and_a_resize_keep_it(self):
        self.trip()
        res = self.trip()                                     # Blender opens what it sent last, and sends it again
        self.assertEqual(self.opened[-1], self.send)
        self.assertEqual(alphas_in(self.models / "Descriptor_Unit_My_Tank.glb"), GAME_ALPHA)
        self.assertEqual(set(res["model"]["blender_alpha"].values()), {"its own, put back"})
        with self.patched():
            self.api.model_resize(TANK, 1.5)                   # fitted again from the file brought back
        self.assertEqual(self.record()["from"], str(self.work / "kept" / self.send.name))
        self.assertEqual(self.record()["size"], 1.5)
        self.assertEqual(alphas_in(self.models / "Descriptor_Unit_My_Tank.glb"), GAME_ALPHA)

    def test_a_blender_folder_from_before_keeps_it_too(self):
        """A work folder from a Studio before alpha.json: the game export's alpha pictures still beside, by name."""
        self.trip(before_back=lambda: (self.work / "alpha.json").unlink(missing_ok=True))
        self.assertEqual(alphas_in(self.models / "Descriptor_Unit_My_Tank.glb"), GAME_ALPHA)

    def test_an_alpha_picture_gone_from_the_folder_is_said(self):
        res = self.trip(before_back=lambda: (self.work / "test_tank_test_tank_hull_alpha.png").unlink())
        got = alphas_in(self.models / "Descriptor_Unit_My_Tank.glb")
        self.assertEqual(got["test_tank_hull"], bytes([modelin.PLAIN_ALPHA]) * 32)
        self.assertEqual(got["test_tank_turret"], GAME_ALPHA["test_tank_turret"])
        self.assertEqual(res["model"]["blender_alpha"]["test_tank_hull"],
                         "plain 144: the alpha picture that went out with it isn't in its Blender folder any more")

    def test_a_failed_import_leaves_the_file_it_was_made_from(self):
        from ruse_studio.api import StudioError
        self.trip()
        kept = self.work / "kept" / self.send.name
        made_from, model = kept.read_bytes(), (self.models / "Descriptor_Unit_My_Tank.glb").read_bytes()

        def refused(*_a, **_k):
            raise modelin.ModelError("the model has no points")
        with self.patched(fit=refused), self.assertRaisesRegex(StudioError, "the model has no points"):
            self.api.model_blender(TANK)
            blender_sends(self.send, self.send, {"test_tank_hull": "Changed"})
            self.api.model_blender_back(TANK)
        self.assertEqual(kept.read_bytes(), made_from)          # Resize and Move still fit from what was brought back
        self.assertEqual((self.models / "Descriptor_Unit_My_Tank.glb").read_bytes(), model)
        self.assertEqual(self.record()["from"], str(kept))

    def test_a_squad_s_soldier_keeps_his_own_too(self):
        """The bazooka man through his own Change it in Blender (EachSoldier's): agent B's real-Blender case of
        2026-11-11 (scratch/animmodels/squadblender/single_path_alpha.json: "plain 144")."""
        self.api._soldier_kinds = lambda address: {"fusilier": RIFLEMAN, "bazooka": BAZOOKA}
        self.api._look_models = lambda address: ([BAZOOKA, RIFLEMAN], [])
        res = self.trip(SQUAD, kind="bazooka")
        self.assertEqual(res["kind"], "bazooka")
        self.assertEqual(alphas_in(self.models / "Descriptor_Unit_My_Riflemen@bazooka.glb"), GAME_ALPHA)
        self.assertFalse((self.models / "Descriptor_Unit_My_Riflemen.glb").exists())   # the riflemen's untouched
        self.assertEqual(set(self.record("Descriptor_Unit_My_Riflemen@bazooka")["report"]["blender_alpha"].values()),
                         {"its own, put back"})

    def test_a_model_of_his_own_from_blender_or_a_file_stays_flat(self):
        """Controls (they pass before the change too): what the modder brings into Blender has no game alpha, so his
        own materials come back flat; and Import model from a file, even one whose materials are named as the game's
        pictures, keeps the plain 144 (the owner, 2026-11-12: "Keep it flat")."""
        def his_own():   # (every material his: none of the names that went out)
            blender_sends(self.send, self.send, {"test_tank_hull": "Hull paint", "test_tank_turret": "Turret paint"})
        self.trip(before_back=his_own)
        plain = bytes([modelin.PLAIN_ALPHA])
        flat = {"test_tank_hull": plain * 32, "test_tank_turret": plain * 16}
        self.assertEqual(alphas_in(self.models / "Descriptor_Unit_My_Tank.glb"), flat)
        outside = Path(self.dir.name) / "outside.glb"   # (named as the game model's materials, not from Blender)
        blender_sends(self.work / "test_tank.glb", outside)
        with self.patched():
            res = self.api.model_import(TANK, str(outside))
        self.assertEqual(alphas_in(self.models / "Descriptor_Unit_My_Tank.glb"), flat)
        self.assertEqual(set(res["model"]["alpha"].values()), {"plain 144"})
        self.assertNotIn("blender_alpha", res["model"])


class ItsOwnModel(unittest.TestCase):
    """Change it in Blender on a unit that has a model of its own and nothing sent yet opens that model, not the game's
    (the owner, 2026-11-13, to "The Generic Horse: should 'Change it in Blender' open its own model? A test waits on
    this.": "yes"; the squad page's Change the squad in Blender starts a soldier from his own model the same way). Its
    alpha pictures go out beside it, listed by material, and come back in by name. ItsOwnShine's stand-ins (borrowed:
    its own tests aren't run again here)."""
    setUp, tearDown = ItsOwnShine.setUp, ItsOwnShine.tearDown
    patched, trip, record = ItsOwnShine.patched, ItsOwnShine.trip, ItsOwnShine.record

    def own_model_then_nothing_sent(self, address=TANK, kind=None) -> Path:
        """A model of its own made by a first trip, then the work folder gone (a model made by Import model, by the
        squad page, or the Generic Horse's Add, before any Change it in Blender): the model's file."""
        import shutil
        self.trip(address, kind=kind)
        work = Path(self.mod / "blender")
        shutil.rmtree(work)
        self.opened.clear()
        return next(self.models.glob("*.glb")) if kind is None else self.models / f"{SQUAD.rsplit('/', 1)[-1]}@{kind}.glb"

    def test_its_own_model_opens_with_its_alpha_beside_it(self):
        own = self.own_model_then_nothing_sent()
        before = own.read_bytes()
        with self.patched():
            res = self.api.model_blender(TANK)
        start = self.opened[-1]
        self.assertEqual(start, self.work / "Descriptor_Unit_My_Tank_own.glb")
        self.assertEqual(res["file"], str(start))
        doc, _bin = modelin.glb_document(start.read_bytes())
        self.assertEqual([m["name"] for m in doc["materials"]], ["test_tank_hull", "test_tank_turret"])
        self.assertFalse([m for m in doc["materials"] if "rusemod_alpha_texture" in (m.get("extras") or {})])
        listed = json.loads((self.work / "alpha.json").read_text(encoding="utf-8"))
        self.assertEqual(listed["start"], start.name)
        self.assertEqual(sorted(listed["alpha"]), ["test_tank_hull", "test_tank_turret"])
        for material, file in listed["alpha"].items():
            _w, _h, rgba = read_png((self.work / file).read_bytes())
            self.assertEqual(bytes(rgba[0::4]), GAME_ALPHA[material], material)
        self.assertEqual(own.read_bytes(), before)                     # (opening it changes nothing in the mod)

    def test_brought_back_its_own_shine_stays(self):
        self.own_model_then_nothing_sent()
        with self.patched():
            res = self.api.model_blender(TANK)
            blender_sends(self.opened[-1], self.send)
            back = self.api.model_blender_back(TANK)
        self.assertEqual(res["file"], str(self.work / "Descriptor_Unit_My_Tank_own.glb"))
        self.assertEqual(alphas_in(self.models / "Descriptor_Unit_My_Tank.glb"), GAME_ALPHA)
        self.assertEqual(set(back["model"]["blender_alpha"].values()), {"its own, put back"})

    def test_a_model_on_bones_of_its_own_goes_out_as_it_is(self):
        """The Generic Horse's kind: its record says "skeleton": "own", so its file goes out with its own bones (no
        game skeleton is read to put them at rest)."""
        own = self.own_model_then_nothing_sent()
        record = json.loads(own.with_suffix(".json").read_text(encoding="utf-8"))
        own.with_suffix(".json").write_text(json.dumps(dict(record, skeleton="own")), encoding="utf-8")

        class NoLibrary:
            def __init__(self, _game=None):
                raise AssertionError("a model on bones of its own reads no game skeleton")
        with self.patched(), mock.patch("rusemod.models.Library", NoLibrary):
            self.api.model_blender(TANK)
        doc, _bin = modelin.glb_document(self.opened[-1].read_bytes())
        was, _b = modelin.glb_document(own.read_bytes())
        self.assertEqual(doc["nodes"], was["nodes"])

    def test_the_bazooka_man_s_own_opens_alone(self):
        self.api._soldier_kinds = lambda address: {"fusilier": RIFLEMAN, "bazooka": BAZOOKA}
        self.api._look_models = lambda address: ([BAZOOKA, RIFLEMAN], [])
        self.own_model_then_nothing_sent(SQUAD, kind="bazooka")
        with self.patched():
            res = self.api.model_blender(SQUAD, "us", "bazooka")
        self.assertEqual(self.opened[-1].name, "Descriptor_Unit_My_Riflemen@bazooka_own.glb")
        self.assertEqual(res["kind"], "bazooka")

    def test_its_own_model_unreadable_is_said_and_nothing_opens(self):
        from ruse_studio.api import StudioError
        own = self.own_model_then_nothing_sent()
        own.write_bytes(b"not a model")
        with self.patched(), self.assertRaisesRegex(StudioError, "Descriptor_Unit_My_Tank.glb"):
            self.api.model_blender(TANK)
        self.assertEqual(self.opened, [])


if __name__ == "__main__":
    unittest.main()
