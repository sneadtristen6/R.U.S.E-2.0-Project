"""The squad's Studio calls (ruse_studio.squadblender: squad_info, squad_blender, squad_blender_back, soldier_import,
soldier_reset) and the .glb helpers they use (rusemod.gltf: glb_views, pack_glb, rest_bones_glb), with stand-ins for
Blender, the game index and the game's model library, as tests/test_modelblender.py's StudioCalls and EachSoldier.
The owner, 2026-11-11 (#4462883, #4462962, #4463065): the whole squad in one Blender, and "you change one soldier's
color, only that soldier should change color". Blender's own side (rusemod.blender_model's squad mode) runs in real
Blender in scratch/animmodels/squadblender/walk_squad.py; here only what the Studio hands it and takes back."""
import hashlib
import json
import re
import struct
import tempfile
import threading
import time
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import blender, gltf, schema
from rusemod.modelin import RIGGED, Part, Prepared, glb_document, write_glb

E = "$/GFX/Everything/"
SQUAD = E + "Descriptor_Unit_My_Riflemen"
GAME_SQUAD = E + "Descriptor_Unit_Soldat_US_Leger"
RIFLEMAN = "ww2\\res3d\\units\\us\\infanterie\\us_soldier_modellod0.ase2ndfbin"
BAZOOKA = "ww2\\res3d\\units\\us\\infanterie\\us_soldier_bazooka_modellod0.ase2ndfbin"
UNIFORM = "ww2\\res3d\\units\\us\\infanterie\\us_soldier_d.tgv"   # (the soldiers' one picture, as a texture path)
STEM = "Descriptor_Unit_My_Riflemen"
WEAPONS = [("Ammo_Arme_infanterie_legere", "Infantry weapon · Light weapons"), ("Ammo_Bazooka", "Bazooka"),
           ("Ammo_Grenades_legeres", "Grenades · Light grenade")]
NAMES = {SQUAD: "My Riflemen", GAME_SQUAD: "G.I."}
VALUES = {E + "UniteBehaviourDescriptor": [("NbSoldatInGroupeCombat", 5.0, None)],
          E + "Ammo_Bazooka": [("NeedModelChange", 1.0, None)], E + "Ammo_Charge_AT": [("NeedModelChange", 1.0, None)],
          E + "Ammo_PanzerFaust": [("NeedModelChange", 1.0, None)],
          E + "Ammo_Arme_infanterie_legere": [], E + "Ammo_Grenades_legeres": []}


def sha(path: Path) -> str | None:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).is_file() else None


class FakeIndex:
    """What the squad calls read of the game index: an object's values (rusemod.index.Index.show)."""

    def show(self, address):
        if address not in VALUES:
            raise KeyError(address)
        return {"class": "T", "values": VALUES[address]}

    def close(self):
        pass


class FakeEdits:
    """What the squad calls read of a mod's changes (ruse_studio.edits.ModEdits)."""

    def __init__(self, units: dict, values: dict | None = None):
        self.new_units, self.values = units, values or {}

    def new_unit_of(self, address):
        return self.new_units.get(address.partition(":")[0])

    def get(self, address, prop, share=None):
        return self.values.get((address, prop))


def game_glb(name: str) -> tuple[bytes, dict, dict]:
    """A stand-in for rusemod.gltf.model_glb: one picture (its colour inside, as the game's export has it, its colour
    and alpha as pictures beside it) on one material that names its texture, as model_glb's do."""
    stem = name.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", "")
    g = gltf._Glb()
    tex = g.image(f"PNG-colour-{stem}".encode(), "TSCOther_diffuseTexture01")
    g.doc["materials"].append({"name": "TSCOther_diffuseTexture01", "pbrMetallicRoughness": {
        "baseColorTexture": {"index": tex}}, "extras": {"rusemod_texture": UNIFORM}})
    colour, alpha = f"{stem}_TSCOther_colour.png", f"{stem}_TSCOther_alpha.png"
    return (g.to_bytes(), {colour: f"PNG-colour-{stem}".encode(), alpha: f"PNG-alpha-{stem}".encode()},
            {"picture_of": {colour: (UNIFORM, "colour"), alpha: (UNIFORM, "alpha")}})


def own_glb(colour: bytes, alpha: bytes) -> bytes:
    """A soldier's own model as Import model saves it (rusemod.modelin.write_glb): a rigged part, its bones all at one
    spot, its picture with its alpha named in the material's extras (their bytes `colour` and `alpha`)."""
    part = Part(RIGGED, 0, [(0.0, 0.0, 100.0), (5.0, 0.0, 150.0), (6.0, 1.0, 195.0)], [(0.0, 0.0, 1.0)] * 3,
                [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], [(0, 1, 2)],
                skin=[[("bip01", 255)], [("bip01 spine", 200), ("bip01", 55)], [("bip01 head", 255)]])
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "m.glb"
        write_glb(Prepared([part], [["body.png", 4, 4, bytes([200, 100, 50, 77]) * 16]], {"rigged": True}), out, BAZOOKA)
        raw = out.read_bytes()
    doc, views = gltf.glb_views(raw)   # the picture and its alpha as given (write_glb makes them from the pixels)
    mat = doc["materials"][0]
    views[doc["images"][doc["textures"][mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]["bufferView"]] = colour
    views[doc["images"][doc["textures"][mat["extras"]["rusemod_alpha_texture"]]["source"]]["bufferView"]] = alpha
    return gltf.pack_glb(doc, views)


class Closed:
    """A stand-in for the Blender process the Studio started, closed again."""

    def poll(self):
        return 0


class Running:
    """... and one still open."""

    def poll(self):
        return None


class Lib:
    """A stand-in for rusemod.models.Library: no packs; its skeleton record as told."""
    skeleton_record = None

    def __init__(self, _game):
        pass

    def skeleton(self, _name):
        return Lib.skeleton_record

    def close(self):
        pass


class Squad(unittest.TestCase):
    """A new squad copying the US rifle squad: riflemen and a bazooka man drawing two models (StudioApi._soldier_kinds
    stood in), its weapons the GI squad's, the game index and model library stood in."""

    def setUp(self):
        from ruse_studio.api import StudioApi
        from ruse_studio.edits import NewUnit
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.mod.mkdir()
        self.models = self.mod / "files" / "models"
        self.edits = FakeEdits({SQUAD: NewUnit(SQUAD, GAME_SQUAD, "My Riflemen")})
        api = self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        api._mod_dir = lambda kind="mod": self.mod
        api._edits = lambda: self.edits
        api._open = FakeIndex
        api._names = lambda ix, addresses, lang, new_units=None: {a: NAMES.get(a, a) for a in addresses}
        api._soldiers = lambda address: True
        self.kinds = {"fusilier": RIFLEMAN, "bazooka": BAZOOKA}
        api._soldier_kinds = lambda address: dict(self.kinds)
        api._soldier_figures = lambda address: [("GfxDescriptorFusilier", RIFLEMAN), ("GfxDescriptorBazooka", BAZOOKA)]
        api._look_models = lambda address: ([BAZOOKA, RIFLEMAN], [UNIFORM])
        api._own_model_file = lambda address: self.models / f"{STEM}.glb" if address == SQUAD else None
        api._blender = lambda: Path("C:/b/blender.exe")
        self.weapons = list(WEAPONS)
        api.weapons = lambda address, lang="us": {"weapons": [{"ammo": {"address": E + a, "name": n}}
                                                               for a, n in self.weapons]}
        api.look = lambda address: {"look": True}
        self.work = self.mod / "blender" / STEM / "squad"
        self.started = []
        Lib.skeleton_record = None

    def tearDown(self):
        self.dir.cleanup()

    def patched(self):
        """The game's model library and its export stood in; Blender's start recorded, not run."""
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(mock.patch("rusemod.models.Library", Lib))
        stack.enter_context(mock.patch("rusemod.gltf.model_glb",
                                       lambda lib, name, side=2048, rest_bones=False: game_glb(name)))
        stack.enter_context(mock.patch("rusemod.blender.open_squad_to_change",
                                       lambda b, manifest: self.started.append((b, manifest)) or Closed()))
        return stack

    def info(self, lang="us", address=SQUAD):
        with self.patched():
            return self.api.squad_info(address, lang)

    def open_squad(self, lang="us") -> dict:
        with self.patched():
            return self.api.squad_blender(SQUAD, lang)

    def manifest(self) -> dict:
        return json.loads((self.work / "squad.json").read_text(encoding="utf-8"))

    def blender_opened(self, figures: dict | None = None) -> dict:
        """What Blender writes when the squad opens (rusemod.blender_model.open_squad): each soldier as opened in
        base/, and base.json. `figures`: {id: bytes}; returns them."""
        m = self.manifest()
        figures = figures or {s["id"]: glb_from(f"figure-{s['id']}".encode(), next(iter(s["alpha"]), "x"))
                              for s in m["soldiers"]}
        base = Path(m["base"])
        base.mkdir(parents=True, exist_ok=True)
        listed = {}
        for sid, data in figures.items():
            (base / f"{sid}.glb").write_bytes(data)
            listed[sid] = {"file": str(base / f"{sid}.glb"), "sha256": hashlib.sha256(data).hexdigest()}
        (base / "base.json").write_text(json.dumps({"session": m["session"], "soldiers": listed}), encoding="utf-8")
        return figures

    def blender_sends(self, figures: dict, left_out=(), session=None) -> None:
        """What Blender's Send writes (rusemod.blender_model.send_squad): one file per soldier and the list."""
        m = self.manifest()
        sent = Path(m["sent"])
        sent.parent.mkdir(parents=True, exist_ok=True)
        listed = {}
        for s in m["soldiers"]:
            if s["id"] not in figures:
                listed[s["id"]] = {"file": None, "sha256": None, "objects": [], "alpha": {}}
                continue
            f = sent.parent / f"{s['id']}.glb"
            f.write_bytes(figures[s["id"]])
            listed[s["id"]] = {"file": str(f), "sha256": hashlib.sha256(figures[s["id"]]).hexdigest(),
                               "objects": [s["name"]], "alpha": s["alpha"]}
        sent.write_text(json.dumps({"session": session or m["session"], "soldiers": listed,
                                    "left_out": list(left_out)}), encoding="utf-8")

    def taking_in(self):
        """Import model stood in: writes the soldier's model file and its record as model_import does, and says what
        it was given."""
        calls = []

        def model_import(address, file, size=1.0, kind=None, **_more):
            target = self.models / (f"{STEM}@{kind}.glb" if kind else f"{STEM}.glb")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(own_glb(b"PNG-from-" + sha(file)[:16].encode(), b"PNG-model-alpha"))
            target.with_suffix(".json").write_text(json.dumps({"from": str(file), "size": size}), encoding="utf-8")
            calls.append((address, Path(file).name, size, kind))
            return {"model": {"rigged": True, "file": Path(file).name}, "copy_out": False, "kind": kind}
        self.api.model_import = model_import
        return calls


def glb_from(figure: bytes, material: str = "Bazooka man 1") -> bytes:
    """A figure as a .glb Blender could have sent: one material named as the start file names it, one picture."""
    g = gltf._Glb()
    tex = g.image(figure, "picture")
    g.doc["materials"].append({"name": material, "pbrMetallicRoughness": {"baseColorTexture": {"index": tex}}})
    return g.to_bytes()


class SquadInfo(Squad):
    def test_the_two_kind_squad(self):
        info = self.info()
        self.assertEqual((info["name"], info["copies"], info["own"], info["count"]), ("My Riflemen", "G.I.", True, 5))
        self.assertEqual(info["line"], "5 soldiers: 4 riflemen (Infantry weapon, Grenades), 1 bazooka man (Bazooka).")
        self.assertEqual([(r["id"], r["label"], r["count"], r["fires"]) for r in info["soldiers"]],
                         [("fusilier", "Rifleman", 4, ["Infantry weapon · Light weapons", "Grenades · Light grenade"]),
                          ("bazooka", "Bazooka man", 1, ["Bazooka"])])
        rifle, bazooka = info["soldiers"]
        self.assertEqual((rifle["own_model"], rifle["from"], rifle["blender_changed"]), (False, None, False))
        self.assertEqual(rifle["kept"], str(self.models / f"{STEM}.glb"))
        self.assertEqual(bazooka["kept"], str(self.models / f"{STEM}@bazooka.glb"))
        self.assertTrue(rifle["preview"]["url"].startswith("cache/units/") and rifle["preview"]["url"].endswith(".glb"))
        self.assertNotEqual(rifle["preview"]["url"], bazooka["preview"]["url"])   # each his own figure
        self.assertEqual(info["blender"], {"open": False, "work": str(self.work), "made": False, "found": True,
                                           "waiting": False})
        self.assertEqual(info["can"], {"blender": True, "import": True, "reset": False, "add": False, "remove": False})
        self.assertIsNone(info["why_not"])

    def test_the_sentence_in_other_languages_counts_the_way_each_says_it(self):
        self.assertEqual(self.info("fr")["line"],
                         "5 soldats : 4 fusiliers (Infantry weapon, Grenades), 1 soldat au bazooka (Bazooka).")
        ru = self.info("ru")
        self.assertEqual(ru["line"], "5 солдат: 4 стрелка (Infantry weapon, Grenades), 1 гранатомётчик (Bazooka).")
        self.assertEqual([r["label"] for r in ru["soldiers"]], ["Стрелок", "Гранатомётчик"])
        self.assertEqual(self.info("jpn")["line"], "兵士5人：ライフル兵4人（Infantry weapon、Grenades）、バズーカ兵1人（Bazooka）。")

    def test_a_squad_of_one_look_is_one_line_and_its_last_man_still_carries_the_satchel_charge(self):
        self.kinds = {}   # (riflemen and bazooka man drawing one model: _soldier_kinds gives none)
        self.api._soldier_figures = lambda address: [("GfxDescriptorFusilier", RIFLEMAN),
                                                     ("GfxDescriptorBazooka", RIFLEMAN)]
        self.weapons = [("Ammo_Arme_infanterie_legere", "Infantry weapon · Light weapons"),
                        ("Ammo_Charge_AT", "Satchel charge"), ("Ammo_Grenades_legeres", "Grenades · Light grenade")]
        info = self.info()
        self.assertEqual(info["line"], "5 soldiers: 4 soldiers (Infantry weapon, Grenades), 1 soldier (Satchel charge).")
        self.assertEqual([(r["id"], r["label"], r["count"]) for r in info["soldiers"]], [("fusilier", "Soldier", 5)])
        self.assertEqual(info["soldiers"][0]["fires"], ["Infantry weapon · Light weapons", "Grenades · Light grenade",
                                                        "Satchel charge"])
        self.weapons = self.weapons[:1]
        self.assertEqual(self.info()["line"], "5 soldiers (Infantry weapon).")
        self.weapons = []
        self.assertEqual(self.info()["line"], "5 soldiers.")

    def test_a_game_unit_is_shown_and_can_t_be_changed(self):
        self.edits = FakeEdits({})
        info = self.info(address=GAME_SQUAD)
        self.assertEqual((info["name"], info["copies"], info["own"]), ("G.I.", None, False))
        self.assertEqual(info["can"], {"blender": False, "import": False, "reset": False, "add": False, "remove": False})
        self.assertIn("copy it first", info["why_not"])
        self.assertEqual([r["kept"] for r in info["soldiers"]], [None, None])
        self.assertEqual(info["blender"]["work"], None)

    def test_a_unit_that_isn_t_a_squad(self):
        self.api._soldiers = lambda address: False
        self.assertIsNone(self.info())

    def test_the_count_is_the_game_s_setting_with_the_mod_s_change(self):
        self.edits.values[(E + "UniteBehaviourDescriptor", "NbSoldatInGroupeCombat")] = 7
        info = self.info()
        self.assertEqual((info["count"], [r["count"] for r in info["soldiers"]]), (7, [6, 1]))
        self.assertTrue(info["line"].startswith("7 soldiers: 6 riflemen"))

    def test_who_fires_what_follows_the_game_s_rule(self):
        from ruse_studio.squadblender import SquadBlenderCalls
        lines = [{"id": "fusilier"}, {"id": "bazooka"}]
        rifle, faust, bazooka = ("Rifle", "Rifle", False), ("Panzerfaust", "Panzerfaust", True), ("Bazooka", "Bazooka", True)
        men = SquadBlenderCalls._squad_men(lines, 5, [rifle, faust, bazooka])
        # the last man wears the bazooka look and fires the first NeedModelChange weapon, the one before him the second
        self.assertEqual(men, [("fusilier", [rifle])] * 3 + [("fusilier", [bazooka]), ("bazooka", [faust])])
        self.assertEqual(SquadBlenderCalls._squad_men(lines, 1, [rifle, bazooka]), [("bazooka", [bazooka])])
        # a mod's ammo change: a squad with no NeedModelChange weapon has every man fire the others
        self.assertEqual(SquadBlenderCalls._squad_men(lines, 2, [rifle]), [("fusilier", [rifle]), ("bazooka", [rifle])])

    def test_each_language_s_number_forms(self):
        from ruse_studio.squadblender import plural_form
        self.assertEqual([plural_form("ru", n) for n in (1, 2, 4, 5, 11, 12, 21, 22, 25)],
                         ["one", "few", "few", "many", "many", "many", "one", "few", "many"])
        self.assertEqual([plural_form("pol", n) for n in (1, 2, 5, 12, 21, 22)], ["one", "few", "many", "many", "many", "few"])
        self.assertEqual([plural_form("cz", n) for n in (1, 3, 5)], ["one", "few", "many"])
        self.assertEqual([plural_form("fr", n) for n in (0, 1, 2)], ["one", "one", "many"])
        self.assertEqual([plural_form("us", n) for n in (1, 2)], ["one", "many"])

    def test_his_own_model_is_said_and_shown(self):
        target = self.models / f"{STEM}@bazooka.glb"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"glTF-his")
        target.with_suffix(".json").write_text(json.dumps({"from": str(self.mod / "blender" / STEM / "squad" / "kept" /
                                                                       f"{STEM}@bazooka.glb")}), encoding="utf-8")
        bazooka = self.info()["soldiers"][1]
        self.assertEqual((bazooka["own_model"], bazooka["from"], bazooka["blender_changed"]),
                         (True, f"{STEM}@bazooka.glb", True))
        self.assertTrue(bazooka["preview"]["url"].startswith("cache/units/own/"))
        self.assertEqual(self.info()["can"]["reset"], True)
        target.with_suffix(".json").write_text(json.dumps({"from": "C:/Users/x/Desktop/marine.glb"}), encoding="utf-8")
        self.assertEqual(self.info()["soldiers"][1]["blender_changed"], False)


class OpenTheSquad(Squad):
    def test_one_blender_with_both_soldiers_each_his_own_file_and_pictures(self):
        res = self.open_squad()
        self.assertEqual(self.started, [(Path("C:/b/blender.exe"), self.work / "squad.json")])
        self.assertIsInstance(self.api._blenders[str(self.work)], Closed)
        self.assertEqual((res["work"], res["opened"]), (str(self.work), ["fusilier", "bazooka"]))
        self.assertEqual(res["started"], {"fusilier": "game", "bazooka": "game"})
        m = self.manifest()
        self.assertEqual([(s["id"], s["name"]) for s in m["soldiers"]],
                         [("fusilier", "Rifleman (all 4)"), ("bazooka", "Bazooka man")])
        self.assertEqual((m["base"], m["sent"]), (str(self.work / "base"), str(self.work / "sent" / "sent.json")))
        self.assertEqual(m["words"]["hint"][0], "Each soldier is his own: change one, and only he changes. Painting one "
                                                "never paints another.")
        files = [Path(s["file"]) for s in m["soldiers"]]
        self.assertEqual(files, [self.work / "start" / "fusilier" / "fusilier.glb",
                                 self.work / "start" / "bazooka" / "bazooka.glb"])
        for s, f in zip(m["soldiers"], files):
            doc, binary = glb_document(f.read_bytes())
            label = "Rifleman" if s["id"] == "fusilier" else "Bazooka man"
            self.assertEqual([x["name"] for x in doc["materials"]], [f"{label} 1"])   # named after him
            self.assertEqual([x["name"] for x in doc["images"]], [f"{label} 1"])
            self.assertNotIn("rusemod_alpha_texture", doc["materials"][0].get("extras", {}))
            alpha = Path(s["alpha"][f"{label} 1"])
            self.assertEqual(alpha.parent, f.parent)   # his own copy, in his own folder
            stem = "us_soldier_model" if s["id"] == "fusilier" else "us_soldier_bazooka_model"
            self.assertEqual(alpha.read_bytes(), f"PNG-alpha-{stem}".encode())
        self.assertEqual(len({str(f.parent) for f in files}), 2)

    def test_the_words_blender_shows_are_in_the_studio_s_language(self):
        self.open_squad("ger")
        m = self.manifest()
        self.assertEqual(m["words"]["send"], "An das R.U.S.E. Studio senden")
        self.assertEqual([s["name"] for s in m["soldiers"]], ["Schütze (alle 4)", "Bazooka-Schütze"])

    def test_a_custom_uniform_s_paint_is_what_he_starts_in(self):
        copy = self.models / f"{STEM}.copy.toml"
        copy.parent.mkdir(parents=True)
        copy.write_text('of = ["x"]\n', encoding="utf-8")
        paint = self.models / STEM / (UNIFORM.replace("\\", "/") + ".png")
        paint.parent.mkdir(parents=True)
        paint.write_bytes(b"PNG-painted-uniform")
        paint.with_name(paint.name.replace(".tgv.png", ".tgv.alpha.png")).write_bytes(b"PNG-painted-alpha")
        res = self.open_squad()
        self.assertEqual(res["started"], {"fusilier": "uniform", "bazooka": "uniform"})
        for s in self.manifest()["soldiers"]:
            doc, binary = glb_document(Path(s["file"]).read_bytes())
            v = doc["bufferViews"][doc["images"][0]["bufferView"]]
            self.assertEqual(binary[v["byteOffset"]:v["byteOffset"] + v["byteLength"]], b"PNG-painted-uniform")
            self.assertEqual(Path(next(iter(s["alpha"].values()))).read_bytes(), b"PNG-painted-alpha")

    def test_his_own_model_from_a_file_is_what_he_starts_in(self):
        target = self.models / f"{STEM}@bazooka.glb"
        target.parent.mkdir(parents=True)
        target.write_bytes(own_glb(b"PNG-his-colour", b"PNG-his-alpha"))
        target.with_suffix(".json").write_text(json.dumps({"from": "C:/Users/x/Desktop/marine.glb",
                                                           "report": {"like": BAZOOKA}}), encoding="utf-8")
        res = self.open_squad()
        self.assertEqual(res["started"], {"fusilier": "game", "bazooka": "model"})
        s = self.manifest()["soldiers"][1]
        doc, binary = glb_document(Path(s["file"]).read_bytes())
        self.assertNotIn("rusemod_alpha_texture", doc["materials"][0].get("extras", {}))
        self.assertEqual(Path(s["alpha"]["Bazooka man 1"]).read_bytes(), b"PNG-his-alpha")

    def test_a_bring_back_is_where_he_starts_until_a_model_from_a_file_takes_its_place(self):
        self.open_squad()
        figures = self.blender_opened()
        calls = self.taking_in()
        self.blender_sends({**figures, "bazooka": glb_from(b"PNG-painted-red")})
        self.api.squad_blender_back(SQUAD)
        self.assertEqual([c[3] for c in calls], ["bazooka"])
        res = self.open_squad()
        self.assertEqual(res["started"], {"fusilier": "game", "bazooka": "kept"})   # his last bring-back
        # Import model from another file of the very same bytes: his model's record names that file now
        target = self.models / f"{STEM}@bazooka.glb"
        record = json.loads(target.with_suffix(".json").read_text(encoding="utf-8"))
        target.with_suffix(".json").write_text(json.dumps({**record, "from": "C:/Users/x/same.glb"}), encoding="utf-8")
        self.assertEqual(self.open_squad()["started"]["bazooka"], "model")
        target.with_suffix(".json").write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(self.open_squad()["started"]["bazooka"], "kept")
        # Import model from a file after the Blender trip: his model is that one now, never undone by the old sending
        target.write_bytes(own_glb(b"PNG-file-colour", b"PNG-file-alpha"))
        target.with_suffix(".json").write_text(json.dumps({"from": "C:/Users/x/marine.glb", "report": {}}),
                                               encoding="utf-8")
        res = self.open_squad()
        self.assertEqual(res["started"]["bazooka"], "model")
        doc, binary = glb_document(Path(self.manifest()["soldiers"][1]["file"]).read_bytes())
        v = doc["bufferViews"][doc["images"][doc["textures"][doc["materials"][0]["pbrMetallicRoughness"]
                                                             ["baseColorTexture"]["index"]]["source"]]["bufferView"]]
        self.assertEqual(binary[v["byteOffset"]:v["byteOffset"] + v["byteLength"]], b"PNG-file-colour")

    def test_a_second_open_while_it_s_open_opens_nothing(self):
        from ruse_studio.api import StudioError
        self.open_squad()
        self.api._blenders[str(self.work)] = Running()
        with self.assertRaisesRegex(StudioError, "This squad is open in Blender already"):
            self.open_squad()
        self.assertEqual(len(self.started), 1)
        self.assertTrue(self.info()["blender"]["open"])
        # (one soldier alone open in Blender, Change it in Blender's: the squad doesn't open on top of it)
        self.api._blenders = {str(self.mod / "blender" / f"{STEM}@bazooka"): Running()}
        with self.assertRaisesRegex(StudioError, "This squad is open in Blender already"):
            self.open_squad()

    def test_a_sending_never_brought_back_is_kept_aside(self):
        self.open_squad()
        self.blender_opened()
        self.blender_sends({"fusilier": b"a", "bazooka": b"b"})
        res = self.open_squad()
        aside = Path(res["set_aside"])
        self.assertTrue(aside.name.startswith("sent-not-brought-") and (aside / "sent.json").is_file())
        self.assertFalse((self.work / "sent").exists())
        self.assertIn(str(aside), res["message"])

    def test_the_refusals(self):
        from ruse_studio.api import StudioError
        self.api._blender = lambda: None
        with self.assertRaisesRegex(StudioError, "Blender isn't found on this PC"):
            self.open_squad()
        self.api._blender = lambda: Path("C:/b/blender.exe")
        with self.patched(), self.assertRaisesRegex(StudioError, "one of the game's own squads: copy it first"):
            self.api.squad_blender(GAME_SQUAD)
        self.api._soldiers = lambda address: False
        with self.patched(), self.assertRaisesRegex(StudioError, "This unit isn't a squad of soldiers"):
            self.api.squad_blender(SQUAD)
        self.assertFalse((self.mod / "blender").exists())
        self.assertEqual(self.started, [])


class BringItBack(Squad):
    def setUp(self):
        super().setUp()
        self.open_squad()
        self.figures = self.blender_opened()
        self.calls = self.taking_in()

    def back(self, lang="us"):
        with self.patched():
            return self.api.squad_blender_back(SQUAD, lang)

    def test_only_the_soldier_changed_is_taken_in_the_other_s_files_byte_for_byte(self):
        rifle = self.models / f"{STEM}.glb"
        rifle.parent.mkdir(parents=True, exist_ok=True)   # (the riflemen with a model already: it must stay)
        rifle.write_bytes(b"glTF-riflemen")
        rifle.with_suffix(".json").write_text('{"from": "C:/x/rifle.glb"}', encoding="utf-8")
        before = (sha(rifle), sha(rifle.with_suffix(".json")))
        painted = glb_from(b"PNG-painted-red")
        self.blender_sends({**self.figures, "bazooka": painted})
        res = self.back()
        self.assertEqual((res["changed"], res["unchanged"], res["uniform_kept"]), (["bazooka"], ["fusilier"], []))
        kept = self.work / "kept" / f"{STEM}@bazooka.glb"
        self.assertEqual(self.calls, [(SQUAD, kept.name, 1.0, "bazooka")])
        self.assertEqual((sha(rifle), sha(rifle.with_suffix(".json"))), before)
        self.assertEqual(res["message"], "Brought back: Bazooka man. As they were: Rifleman.")
        # his alpha back in the file Import model read: the start file's alpha for his material, named in its extras
        doc, binary = glb_document(kept.read_bytes())
        k = doc["materials"][0]["extras"]["rusemod_alpha_texture"]
        v = doc["bufferViews"][doc["images"][doc["textures"][k]["source"]]["bufferView"]]
        self.assertEqual(binary[v["byteOffset"]:v["byteOffset"] + v["byteLength"]], b"PNG-alpha-us_soldier_bazooka_model")
        state = json.loads((self.work / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["taken"]["bazooka"], {"kept": sha(kept), "model": sha(self.models / f"{STEM}@bazooka.glb")})

    def test_sent_again_unchanged_takes_nothing_and_then_the_riflemen_alone(self):
        painted = glb_from(b"PNG-painted-red")
        self.blender_sends({**self.figures, "bazooka": painted})
        self.back()
        his = self.models / f"{STEM}@bazooka.glb"
        his_before = (sha(his), sha(his.with_suffix(".json")))
        self.blender_sends({**self.figures, "bazooka": painted})   # Send again, nothing done since
        res = self.back()
        self.assertEqual((res["changed"], res["unchanged"]), ([], ["fusilier", "bazooka"]))
        self.assertEqual(res["message"], "Nothing was changed in Blender since the squad was opened or last brought "
                                         "back, so nothing changed here.")
        self.blender_sends({"fusilier": glb_from(b"figure-fusilier-moved", "Rifleman 1"), "bazooka": painted})
        res = self.back()
        self.assertEqual(res["changed"], ["fusilier"])
        self.assertEqual([c[3] for c in self.calls], ["bazooka", None])   # (the riflemen: Import model with no kind)
        self.assertEqual((sha(his), sha(his.with_suffix(".json"))), his_before)

    def test_nothing_changed_at_all(self):
        self.blender_sends(dict(self.figures))
        res = self.back()
        self.assertEqual((res["changed"], self.calls), ([], []))
        self.assertFalse(self.models.exists())

    def test_a_custom_uniform_stays_on_the_soldiers_not_changed(self):
        copy = self.models / f"{STEM}.copy.toml"
        copy.parent.mkdir(parents=True)
        copy.write_text('of = ["x"]\n', encoding="utf-8")
        self.blender_sends({**self.figures, "bazooka": glb_from(b"PNG-painted-red")})
        res = self.back()
        self.assertEqual((res["changed"], res["unchanged"], res["uniform_kept"]), (["bazooka"], ["fusilier"], ["fusilier"]))
        self.assertEqual([c[3] for c in self.calls], [None, "bazooka"])   # the riflemen first, as he was
        self.assertIn("Custom uniform", res["message"])

    def test_an_open_blender_is_asked_to_send(self):
        self.api._blenders[str(self.work)] = Running()
        sent = Path(self.manifest()["sent"])

        def blender_answers():
            end = time.monotonic() + 5
            while not (sent.parent / blender.SEND_REQUEST).exists() and time.monotonic() < end:
                time.sleep(0.02)
            self.blender_sends({**self.figures, "bazooka": glb_from(b"PNG-painted")})
            (sent.parent / blender.SEND_DONE).write_text(json.dumps({"file": str(sent)}), encoding="utf-8")
            (sent.parent / blender.SEND_REQUEST).unlink(missing_ok=True)
        sent.parent.mkdir(parents=True, exist_ok=True)
        t = threading.Thread(target=blender_answers)
        t.start()
        res = self.back()
        t.join()
        self.assertEqual(res["changed"], ["bazooka"])

    def test_an_open_blender_that_doesn_t_answer_takes_nothing(self):
        from ruse_studio.api import StudioError
        self.api._blenders[str(self.work)] = Running()
        self.blender_sends({**self.figures, "bazooka": glb_from(b"old")})
        with mock.patch("ruse_studio.squadblender.SEND_WAIT", 0.3), \
                self.assertRaisesRegex(StudioError, "Blender didn't answer in time"):
            self.back()
        self.assertEqual(self.calls, [])

    def test_the_refusals(self):
        from ruse_studio.api import StudioError
        with self.assertRaisesRegex(StudioError, "Nothing has come back from Blender yet"):
            self.back()
        self.blender_sends(dict(self.figures), session="an older Blender")
        with self.assertRaisesRegex(StudioError, "Nothing has come back from Blender yet"):
            self.back()
        self.blender_sends({"bazooka": b"x"})   # (every part of the riflemen deleted in Blender)
        with self.assertRaisesRegex(StudioError, "Blender sent nothing for Rifleman"):
            self.back()
        self.assertEqual(self.calls, [])

    def test_objects_on_no_soldier_are_said(self):
        self.blender_sends(dict(self.figures), left_out=["Cube"])
        res = self.back()
        self.assertEqual(res["left_out"], ["Cube"])
        self.assertIn("Cube", res["message"])


class OneSoldier(Squad):
    def test_import_and_reset_go_to_his_kind(self):
        got = []
        self.api.model_import = lambda address, file=None, size=1.0, kind=None: got.append(("import", file, size, kind)) \
            or {"model": {}, "kind": kind}
        self.api.model_import_remove = lambda address, kind=None: got.append(("reset", kind)) or {"kinds_out": []}
        self.assertEqual(self.api.soldier_import(SQUAD, "bazooka", "C:/m.glb", 1.2), {"model": {}, "kind": "bazooka"})
        self.api.soldier_import(SQUAD, "fusilier")
        self.api.soldier_reset(SQUAD, "bazooka")
        self.assertEqual(self.api.soldier_reset(SQUAD, "fusilier"), {"kinds_out": []})
        self.assertEqual(got, [("import", "C:/m.glb", 1.2, "bazooka"), ("import", None, 1.0, None), ("reset", "bazooka"),
                               ("reset", None)])

    def test_a_soldier_the_squad_hasn_t_got_or_a_unit_that_isn_t_a_squad(self):
        from ruse_studio.api import StudioError
        with self.assertRaisesRegex(StudioError, "This squad has no soldier called medic"):
            self.api.soldier_import(SQUAD, "medic")
        with self.assertRaisesRegex(StudioError, "This squad has no soldier called medic"):
            self.api.soldier_reset(SQUAD, "medic")
        self.api._soldiers = lambda address: False
        with self.assertRaisesRegex(StudioError, "This unit isn't a squad of soldiers"):
            self.api.soldier_reset(SQUAD, "fusilier")


class Words(unittest.TestCase):
    def test_every_blender_squad_word_in_every_language(self):
        words = tomllib.loads((Path(__file__).parents[1] / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        mine = sorted(k for k in words if k.startswith("blender_squad_"))
        self.assertGreater(len(mine), 25)
        for key in mine:
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), set(schema.APP_LANGS))
        src = "".join((Path(__file__).parents[1] / "src" / p).read_text(encoding="utf-8")
                      for p in ("ruse_studio/squadblender.py", "rusemod/blender_model.py"))
        used = set(re.findall(r'"(blender_squad_\w+)"', src))
        used |= {f"blender_squad_{w}_{f}" for w in ("soldiers", "riflemen", "bazookamen") for f in ("one", "few", "many")}
        used |= {f"blender_squad_{w}" for w in ("rifleman", "bazookaman", "soldier")}
        self.assertEqual(sorted(used - set(mine)), [])


class InBlender(unittest.TestCase):
    """What rusemod.blender_model's squad mode is started with, and its names matching rusemod.blender's."""

    def test_the_squad_mode_s_flag_and_file_names(self):
        source = blender.CHANGER.read_text(encoding="utf-8")
        self.assertEqual(re.search(r'^SQUAD_FLAG = "([^"]+)"', source, re.M).group(1), blender.SQUAD_FLAG)
        names = re.search(r'^SEND_REQUEST, SEND_DONE = "([^"]+)", "([^"]+)"', source, re.M).groups()
        self.assertEqual(names, (blender.SEND_REQUEST, blender.SEND_DONE))
        self.assertIn("use_active_collection=True", source)   # (a soldier's file: his objects, hidden ones too)
        with mock.patch("subprocess.Popen") as popen:
            blender.open_squad_to_change(Path("C:/b/blender.exe"), Path("w/squad.json"))
        self.assertEqual(popen.call_args[0][0][1:], ["--python", str(blender.CHANGER), "--", "--squad",
                                                     str(Path("w/squad.json"))])


class Glb(unittest.TestCase):
    """rusemod.gltf's glb_views, pack_glb and rest_bones_glb."""

    def test_written_again_every_view_keeps_its_bytes(self):
        raw = own_glb(b"PNG-c", b"PNG-a")
        doc, views = gltf.glb_views(raw)
        again = gltf.pack_glb(*gltf.glb_views(raw))
        self.assertEqual(gltf.glb_views(again)[1], views)
        n = gltf.add_view(doc, views, b"12345")
        doc2, views2 = gltf.glb_views(gltf.pack_glb(doc, views))
        self.assertEqual((views2[n], doc2["bufferViews"][n]["byteOffset"] % 4), (b"12345", 0))

    def test_a_rigged_model_s_bones_at_their_rest_poses(self):
        from test_gltf_bones import pose, record, turn
        rec = record(["bip01", "bip01 spine", "bip01 head"], [-1, 0, 1],
                     [pose(turn("z", 90), (0.0, 0.0, 100.0)), pose(turn("z", 90), (5.0, 0.0, 150.0)),
                      pose(turn("z", 90), (6.0, 1.0, 195.0))])
        raw = own_glb(b"PNG-c", b"PNG-a")
        placed = gltf.rest_bones_glb(raw, rec)
        before, after = gltf.glb_views(raw), gltf.glb_views(placed)
        doc = after[0]
        joints = doc["skins"][0]["joints"]
        self.assertEqual([doc["nodes"][j]["name"] for j in joints], ["bip01", "bip01 head", "bip01 spine"])
        self.assertTrue(all("translation" in doc["nodes"][j] for j in joints))
        holder = doc["skins"][0]["skeleton"]
        self.assertIn(holder, doc["scenes"][0]["nodes"])
        self.assertFalse(set(joints) & set(doc["scenes"][0]["nodes"]))   # (under the holder, not loose)
        rest = gltf.rest_poses(rec, [0, 2, 1])
        acc = doc["accessors"][doc["skins"][0]["inverseBindMatrices"]]
        ibm = struct.unpack(f"<{16 * len(joints)}f", after[1][acc["bufferView"]])
        self.assertEqual(ibm, struct.unpack(f"<{16 * len(joints)}f", struct.pack(f"<{16 * len(joints)}f",
                                                                                 *(v for m in rest["ibm"] for v in m))))
        # the points, weights and pictures the same bytes
        prim = doc["meshes"][0]["primitives"][0]
        for attr in ("POSITION", "JOINTS_0", "WEIGHTS_0"):
            v = doc["accessors"][prim["attributes"][attr]]["bufferView"]
            self.assertEqual(after[1][v], before[1][v])
        self.assertIsNone(gltf.rest_bones_glb(placed, rec))   # (placed already: as it is)
        other = record(["bip01", "bip01 spine"], [-1, 0], [pose(turn("z", 0), (0, 0, 0))] * 2)
        self.assertIsNone(gltf.rest_bones_glb(raw, other))   # (a bone the record hasn't got)


if __name__ == "__main__":
    unittest.main()
