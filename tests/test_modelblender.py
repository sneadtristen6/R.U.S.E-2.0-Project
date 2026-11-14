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


def skinned(order: list, joints_of_points: list, names=("A", "B", "C")) -> bytes:
    """A .glb of three bones A (its children the others) on one skin whose joints are `names` in `order`, three points
    each leaning wholly on the bone named in `joints_of_points`, each bone's inverse bind matrix its own numbers."""
    import struct as st
    doc = {"asset": {"version": "2.0"}, "nodes": [{"name": names[0], "children": [1, 2]}, {"name": names[1]},
                                                  {"name": names[2]}, {"name": "mesh", "mesh": 0, "skin": 0}],
           "scenes": [{"nodes": [0, 3]}], "scene": 0, "accessors": [], "bufferViews": []}
    views = []

    def add(data: bytes, kind: str, comp: int, count: int) -> int:
        doc["bufferViews"].append({"buffer": 0, "byteOffset": 0, "byteLength": len(data)})
        views.append(data)
        doc["accessors"].append({"bufferView": len(views) - 1, "componentType": comp, "count": count, "type": kind})
        return len(doc["accessors"]) - 1
    joint_index = {names.index(n): k for k, n in enumerate(order)}   # node -> joint number
    pos = add(st.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0), "VEC3", 5126, 3)
    joints = add(bytes(b for n in joints_of_points for b in (joint_index[names.index(n)], 0, 0, 0)), "VEC4", 5121, 3)
    weights = add(st.pack("<12f", *([1.0, 0, 0, 0] * 3)), "VEC4", 5126, 3)
    ibm = add(b"".join(st.pack("<16f", *([float(names.index(n) + 1)] * 16)) for n in order), "MAT4", 5126, 3)
    doc["meshes"] = [{"primitives": [{"attributes": {"POSITION": pos, "JOINTS_0": joints, "WEIGHTS_0": weights}}]}]
    doc["skins"] = [{"joints": [names.index(n) for n in order], "inverseBindMatrices": ibm}]
    return gltf.pack_glb(doc, views)


class JointOrder(unittest.TestCase):
    """A file back from Blender with its bones in the order they went out in (gltf.joints_like): Blender 4.5's export
    wrote the Generic Horse's 62 joints in another order (measured 2026-11-13), and the riflemen's model came in on bones
    the bazooka man's wasn't on any more (rusemod.bonefit.skeleton_key)."""

    def joints(self, raw: bytes):
        doc, views = gltf.glb_views(raw)
        names = [doc["nodes"][j]["name"] for j in doc["skins"][0]["joints"]]
        acc = doc["accessors"][doc["meshes"][0]["primitives"][0]["attributes"]["JOINTS_0"]]
        data = views[acc["bufferView"]][acc.get("byteOffset", 0):][:12]
        ibm = doc["accessors"][doc["skins"][0]["inverseBindMatrices"]]
        firsts = [__import__("struct").unpack_from("<f", views[ibm["bufferView"]], ibm.get("byteOffset", 0) + 64 * k)[0]
                  for k in range(3)]
        return names, [names[data[4 * p]] for p in range(3)], firsts

    def test_back_in_the_order_it_went_out_in_each_point_on_its_own_bone(self):
        went = skinned(["A", "B", "C"], ["B", "C", "A"])
        sent = skinned(["A", "C", "B"], ["B", "C", "A"])
        self.assertEqual(self.joints(sent)[0], ["A", "C", "B"])
        got = gltf.joints_like(sent, went)
        names, leaning, ibm = self.joints(got)
        self.assertEqual(names, ["A", "B", "C"])
        self.assertEqual(leaning, ["B", "C", "A"])                  # (each point still on the bone it leaned on)
        self.assertEqual(ibm, [1.0, 2.0, 3.0])                       # (each bone's matrix moved with it)
        self.assertEqual(self.joints(got), self.joints(went))

    def test_left_as_it_is_when_the_bones_arent_the_same_or_already_in_order(self):
        went = skinned(["A", "B", "C"], ["B", "C", "A"])
        same = skinned(["A", "B", "C"], ["A", "A", "B"])
        self.assertEqual(gltf.joints_like(same, went), same)
        renamed = skinned(["A", "C", "D"], ["A", "C", "D"], names=("A", "D", "C"))
        self.assertEqual(gltf.joints_like(renamed, went), renamed)
        self.assertEqual(gltf.joints_like(b"not a model", went), b"not a model")

    def test_put_back_in_order_when_blender_named_the_armature_after_its_soldier(self):
        """Change the squad in Blender names each soldier's armature after him ("Rifleman 1"): the bones' parents among
        themselves are what count (measured 2026-11-13: with the armature's name compared, a Generic Horse rider came
        back off the riflemen's bones)."""
        went = armatured(["A", "B", "C"], "us_soldier_model_bones")
        sent = armatured(["A", "C", "B"], "Rifleman 1")
        names = [n["name"] for n in gltf.glb_views(gltf.joints_like(sent, went))[0]["nodes"]]
        got = gltf.glb_views(gltf.joints_like(sent, went))[0]
        self.assertEqual([got["nodes"][j]["name"] for j in got["skins"][0]["joints"]], ["A", "B", "C"])
        self.assertIn("Rifleman 1", names)                     # (the armature's own name stays Blender's)


def armatured(order: list, armature: str, moved: dict | None = None) -> bytes:
    """A .glb of bones A (its children B and C) under an armature node named `armature`, one skin with the joints in
    `order`, each bone placed at its own translation (A at 0, B at 1, C at 2 up) unless `moved` {name: its height},
    each bind matrix the inverse of its place; three points, one on each bone."""
    import struct as st
    heights = {"A": 0.0, "B": 1.0, "C": 2.0, **(moved or {})}
    doc = {"asset": {"version": "2.0"},
           "nodes": [{"name": armature, "children": [1]},
                     {"name": "A", "translation": [0.0, heights["A"], 0.0], "children": [2, 3]},
                     {"name": "B", "translation": [0.0, heights["B"] - heights["A"], 0.0]},
                     {"name": "C", "translation": [0.0, heights["C"] - heights["A"], 0.0]},
                     {"name": "mesh", "mesh": 0, "skin": 0}],
           "scenes": [{"nodes": [0, 4]}], "scene": 0, "accessors": [], "bufferViews": []}
    views = []

    def add(data: bytes, kind: str, comp: int, count: int) -> int:
        doc["bufferViews"].append({"buffer": 0, "byteOffset": 0, "byteLength": len(data)})
        views.append(data)
        doc["accessors"].append({"bufferView": len(views) - 1, "componentType": comp, "count": count, "type": kind})
        return len(doc["accessors"]) - 1
    node_of = {"A": 1, "B": 2, "C": 3}
    joint_of = {n: k for k, n in enumerate(order)}
    pos = add(st.pack("<9f", 0, 0, 0, 0, 1, 0, 0, 2, 0), "VEC3", 5126, 3)
    joints = add(bytes(b for n in ("A", "B", "C") for b in (joint_of[n], 0, 0, 0)), "VEC4", 5121, 3)
    weights = add(st.pack("<12f", *([1.0, 0, 0, 0] * 3)), "VEC4", 5126, 3)

    def inverse_place(n: str) -> tuple:   # (a bind matrix, by columns: the inverse of a move up by the bone's height)
        return (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, -heights[n], 0, 1)
    ibm = add(b"".join(st.pack("<16f", *inverse_place(n)) for n in order), "MAT4", 5126, 3)
    doc["meshes"] = [{"primitives": [{"attributes": {"POSITION": pos, "JOINTS_0": joints, "WEIGHTS_0": weights}}]}]
    doc["skins"] = [{"joints": [node_of[n] for n in order], "inverseBindMatrices": ibm}]
    return gltf.pack_glb(doc, views)


class BonesKept(unittest.TestCase):
    """The one Blender button's Bones unticked (the owner, 2026-11-13: "I want to bring everything but the bones. So
    then you just uncheck the bones"): gltf.bones_like puts the bones of the file that went out back into what Blender
    sent, the mesh and the rest as Blender sent them (a bone moved in Blender came back into the mod: measured on the
    Generic Horse the same day)."""

    def place(self, raw: bytes, name: str) -> tuple:
        doc, views = gltf.glb_views(raw)
        nodes = doc["nodes"]
        j = next(j for j in doc["skins"][0]["joints"] if nodes[j]["name"] == name)
        k = doc["skins"][0]["joints"].index(j)
        acc = doc["accessors"][doc["skins"][0]["inverseBindMatrices"]]
        bind = __import__("struct").unpack_from("<16f", views[acc["bufferView"]], acc.get("byteOffset", 0) + 64 * k)
        return tuple(nodes[j].get("translation", ())), bind[13]

    def test_a_bone_moved_in_blender_goes_back_where_it_was_and_the_mesh_stays_blenders(self):
        went = armatured(["A", "B", "C"], "bones")
        sent = armatured(["A", "B", "C"], "bones", moved={"B": 1.05})
        self.assertNotEqual(self.place(sent, "B"), self.place(went, "B"))
        got, word = gltf.bones_like(sent, went)
        self.assertEqual(word, gltf.BONES_KEPT)
        self.assertEqual(self.place(got, "B"), self.place(went, "B"))
        self.assertEqual(self.place(got, "A"), self.place(went, "A"))
        doc_sent, views_sent = gltf.glb_views(sent)
        doc_got, views_got = gltf.glb_views(got)
        self.assertEqual(doc_got["meshes"], doc_sent["meshes"])            # (the mesh as Blender sent it)
        pos = doc_got["accessors"][doc_got["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
        self.assertEqual(views_got[pos["bufferView"]], views_sent[pos["bufferView"]])

    def test_in_blenders_order_and_under_its_armature_name_each_bone_still_gets_its_own_place_back(self):
        went = armatured(["A", "B", "C"], "us_soldier_model_bones")
        sent = armatured(["A", "C", "B"], "Rifleman 1", moved={"C": 2.5})
        got, word = gltf.bones_like(sent, went)
        self.assertEqual(word, gltf.BONES_KEPT)
        for name in ("A", "B", "C"):
            self.assertEqual(self.place(got, name), self.place(went, name), name)

    def test_nothing_changed_said_so_and_the_file_as_it_was(self):
        went = armatured(["A", "B", "C"], "bones")
        got, word = gltf.bones_like(went, went)
        self.assertEqual((got, word), (went, gltf.BONES_SAME))

    def test_a_bone_renamed_or_the_file_unreadable_left_as_blender_sent_it_and_said(self):
        went = skinned(["A", "B", "C"], ["B", "C", "A"])
        renamed = skinned(["A", "C", "D"], ["A", "C", "D"], names=("A", "D", "C"))
        self.assertEqual(gltf.bones_like(renamed, went), (renamed, gltf.BONES_DIFFER))
        self.assertEqual(gltf.bones_like(b"not a model", went), (b"not a model", gltf.BONES_UNREAD))


def painted(pictures: dict) -> bytes:
    """A .glb of one triangle with a material per `pictures` {its name: its base colour picture's bytes}, each picture
    kept in the file."""
    import struct as st
    doc = {"asset": {"version": "2.0"}, "nodes": [{"name": "mesh", "mesh": 0}], "scenes": [{"nodes": [0]}], "scene": 0,
           "accessors": [], "bufferViews": [], "materials": [], "textures": [], "images": []}
    views = []
    pos = gltf.add_view(doc, views, st.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0))
    doc["accessors"].append({"bufferView": pos, "componentType": 5126, "count": 3, "type": "VEC3"})
    prims = []
    for name, data in pictures.items():
        doc["images"].append({"bufferView": gltf.add_view(doc, views, data), "mimeType": "image/png"})
        doc["textures"].append({"source": len(doc["images"]) - 1})
        doc["materials"].append({"name": name, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": len(doc["textures"]) - 1}}})
        prims.append({"attributes": {"POSITION": 0}, "material": len(doc["materials"]) - 1})
    doc["meshes"] = [{"primitives": prims}]
    return gltf.pack_glb(doc, views)


def repaint(send: Path, colours: dict) -> None:
    """Blender's paint changed in what it sent (`send`): each material named in `colours` ({name: (r, g, b)}) shows a
    picture of that one colour, its size kept (a picture of another size would get the plain 144: alpha_sizes)."""
    from rusemod.dxt import png_bytes
    doc, views = gltf.glb_views(send.read_bytes())
    for m in doc["materials"]:
        if m["name"] in colours:
            image = doc["images"][doc["textures"][m["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
            w, h, _rgba = read_png(views[image["bufferView"]])
            image["bufferView"] = gltf.add_view(doc, views, png_bytes(bytes(colours[m["name"]]) * (w * h), w, h))
    send.write_bytes(gltf.pack_glb(doc, views))


def colours_in(model: Path) -> dict:
    """{each picture of a model the mod keeps (rusemod.modelin.write_glb's): its colour, RGB a pixel}."""
    doc, binary = modelin.glb_document(model.read_bytes())
    out = {}
    for m in doc["materials"]:
        k = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
        _w, _h, rgba = read_png(modelin.glb_image(doc, binary, doc["textures"][k]["source"]))
        out[m["name"]] = bytes(b for i, b in enumerate(rgba) if i % 4 != 3)
    return out


RED, BLUE = (200, 30, 30), (30, 40, 210)


class UntickedPaintKeepsWhatItHasNow(unittest.TestCase):
    """The one Blender button's Paint unticked keeps the paint the unit's model has NOW (its "what was unticked stays as
    it was"), never the paint of the file Blender was first opened with: a repaint taken in by an earlier Bring back
    was put back to the first opening's picture while the page said "Its paint was kept as it was" (found by the anims
    fixer, 2026-11-14, on 0d5564eb; so since 8f48259e, the one Blender button's calls). ItsOwnShine's stand-ins: the
    made-up tank of a game model, its model's own Change it in Blender, and the bazooka man's own door (a kind's)."""
    setUp, tearDown = ItsOwnShine.setUp, ItsOwnShine.tearDown
    patched, record = ItsOwnShine.patched, ItsOwnShine.record

    def trip(self, address=TANK, kind=None, unticked=False, colours=None) -> dict:
        """Change it in Blender; Blender sends (`colours`: those materials repainted there); Bring back the model, its
        Paint unticked when `unticked` (blender_back's keep_paint)."""
        with self.patched():
            res = self.api.model_blender(address, "us", kind) if kind else self.api.model_blender(address)
            send = Path(res["work"]) / f"{Path(res['work']).name}.glb"
            blender_sends(self.opened[-1], send)
            if colours:
                repaint(send, colours)
            return self.api.model_blender_back(address, 1.0, kind, keep_paint=unticked)

    def model(self, stem="Descriptor_Unit_My_Tank") -> Path:
        return self.models / f"{stem}.glb"

    def test_a_repaint_brought_back_stays_when_a_later_trip_unticks_paint(self):
        """Paint ticked, the hull repainted red in Blender and brought back; then Paint unticked, nothing changed in
        Blender: the hull stays red, nothing is put back (0d5564eb put the game's hull back, and said it kept it)."""
        self.trip(colours={"test_tank_hull": RED})
        red = colours_in(self.model())
        self.assertEqual(red["test_tank_hull"], bytes(RED) * 32)
        res = self.trip(unticked=True)
        self.assertEqual(colours_in(self.model()), red)
        self.assertEqual(res["kept"]["paint"], [])

    def test_paint_unticked_puts_back_the_paint_it_has_now_over_blender_s(self):
        """Paint ticked, the hull repainted red and brought back; then Paint unticked and the hull repainted blue in
        Blender: the hull stays red, and that is said (0d5564eb put the game's hull back)."""
        self.trip(colours={"test_tank_hull": RED})
        red = colours_in(self.model())
        res = self.trip(unticked=True, colours={"test_tank_hull": BLUE})
        self.assertEqual(colours_in(self.model()), red)
        self.assertEqual(res["kept"]["paint"], ["test_tank_hull"])

    def test_a_resize_between_keeps_the_repaint_too(self):
        """A Resize between the two trips fits the model again from what the first Bring back took in: the hull stays
        red through a later trip with Paint unticked."""
        self.trip(colours={"test_tank_hull": RED})
        with self.patched():
            self.api.model_resize(TANK, 1.5)
        red = colours_in(self.model())
        self.assertEqual(red["test_tank_hull"], bytes(RED) * 32)
        self.trip(unticked=True, colours={"test_tank_hull": BLUE})
        self.assertEqual(colours_in(self.model()), red)

    def test_a_kind_s_own_door_keeps_his_paint_brought_back_too(self):
        """The bazooka man's own door (a squad's other kind, the Generic Horse's way): the same."""
        self.api._soldier_kinds = lambda address: {"fusilier": RIFLEMAN, "bazooka": BAZOOKA}
        self.api._look_models = lambda address: ([BAZOOKA, RIFLEMAN], [])
        self.trip(SQUAD, kind="bazooka", colours={"test_tank_hull": RED})
        his = self.model("Descriptor_Unit_My_Riflemen@bazooka")
        red = colours_in(his)
        self.trip(SQUAD, kind="bazooka", unticked=True)
        self.assertEqual(colours_in(his), red)
        self.assertFalse(self.model("Descriptor_Unit_My_Riflemen").exists())   # (the riflemen's untouched)

    def test_control_a_kind_left_unticked_keeps_his_files_byte_for_byte(self):
        """The control (so before too), the Generic Horse's way of one kind at a time: the bazooka man repainted and
        brought back, then a trip of the riflemen alone with Paint unticked: his model, record and kept file stay byte
        for byte."""
        self.api._soldier_kinds = lambda address: {"fusilier": RIFLEMAN, "bazooka": BAZOOKA}
        self.api._look_models = lambda address: ([BAZOOKA, RIFLEMAN], [])
        self.trip(SQUAD, kind="bazooka", colours={"test_tank_hull": RED})
        work = self.mod / "blender" / "Descriptor_Unit_My_Riflemen@bazooka"
        his = [self.model("Descriptor_Unit_My_Riflemen@bazooka"),
               self.models / "Descriptor_Unit_My_Riflemen@bazooka.json",
               work / "kept" / "Descriptor_Unit_My_Riflemen@bazooka.glb"]
        before = [f.read_bytes() for f in his]
        self.trip(SQUAD, unticked=True, colours={"test_tank_hull": BLUE})
        self.assertTrue(self.model("Descriptor_Unit_My_Riflemen").is_file())
        self.assertEqual([f.read_bytes() for f in his], before)

    def test_control_paint_unticked_on_the_first_trip_keeps_the_paint_it_went_out_with(self):
        """The control (so before too): Paint unticked on the first trip, the hull repainted in Blender: the hull keeps
        the game's picture it went out with, said."""
        res = self.trip(unticked=True, colours={"test_tank_hull": RED})
        game_hull = bytes(b for i, b in enumerate(PICTURES[HULL][2]) if i % 4 != 3)
        self.assertEqual(colours_in(self.model())["test_tank_hull"], game_hull)
        self.assertEqual(res["kept"]["paint"], ["test_tank_hull"])

    def test_control_paint_ticked_takes_each_repaint_in(self):
        """The control (so before too): Paint ticked on each trip, each repaint comes in."""
        self.trip(colours={"test_tank_hull": RED})
        self.assertEqual(colours_in(self.model())["test_tank_hull"], bytes(RED) * 32)
        res = self.trip(colours={"test_tank_hull": BLUE})
        self.assertEqual(colours_in(self.model())["test_tank_hull"], bytes(BLUE) * 32)
        self.assertIsNone(res["kept"]["paint"])


class PaintKept(unittest.TestCase):
    """The one Blender button's Paint unticked: gltf.paint_like puts each material's picture back as it went out, by the
    material's name; the rest as Blender sent it."""

    def picture(self, raw: bytes, name: str) -> bytes:
        doc, views = gltf.glb_views(raw)
        material = next(m for m in doc["materials"] if m["name"] == name)
        return gltf._base_picture(doc, views, material)[1]

    def test_a_picture_painted_in_blender_goes_back_as_it_went_out(self):
        went = painted({"body": b"old body", "tracks": b"old tracks"})
        sent = painted({"body": b"new paint", "tracks": b"old tracks"})
        got, put = gltf.paint_like(sent, went)
        self.assertEqual(put, ["body"])
        self.assertEqual(self.picture(got, "body"), b"old body")
        self.assertEqual(self.picture(got, "tracks"), b"old tracks")

    def test_a_material_new_or_renamed_in_blender_keeps_what_blender_wrote(self):
        went = painted({"body": b"old body"})
        sent = painted({"body": b"old body", "saddle_leather": b"leather"})
        got, put = gltf.paint_like(sent, went)
        self.assertEqual((got, put), (sent, []))
        self.assertEqual(gltf.paint_like(b"not a model", went), (b"not a model", []))


if __name__ == "__main__":
    unittest.main()
