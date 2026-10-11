"""An .rmod mod made into a mod the Studio can show and change (rusemod.rmodconvert, ruse_studio.rmodedit; the owner,
2026-10-10): on a made-up game, its value changes become Studio changes, everything else stays a smaller .rmod, the
build applies both, and the converted mod builds the same unit data as the original."""
import json
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from ruse_mod_engine import ndfbin
from rusemod import rmodconvert
from rusemod.build import build_and_write, load_mod
from rusemod.dic import name_to_key
from rusemod.edat import Edat
from rusemod.index import build_index
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import ModEdits
from ruse_studio.rmodedit import convert_folder

UNITS = "genglad/patchable/gfx/everything.cpp.gladndfbin"
PACK = "Data/PC/190852/ZZ_GladPatchableWin.dat"
CLASSES = ["TUniteAuSolDescriptor", "TWeaponDescriptor", "TAmmunition"]
PROPS = [("ClassNameForDebug", 0), ("SeuilMort", 0), ("ShowInMenu", 0), ("WeaponDescriptor", 0), ("Cost", 0),
         ("Puissance", 1), ("AmmunitionId", 2)]
P = {name: i for i, (name, _c) in enumerate(PROPS)}
A, B = "$/GFX/Everything/Descriptor_Unit_A", "$/GFX/Everything/Descriptor_Unit_B"


def f32(v):
    return val(0x05, struct.pack("<f", v))


def flags(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(val(0x00, struct.pack("<B", x)) for x in items))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def name(i):
    return val(0x07, struct.pack("<I", i))


def everything() -> bytes:
    """Two units, each with a weapon of its own (a part)."""
    objects = [
        (0, [(P["ClassNameForDebug"], name(0)), (P["SeuilMort"], f32(10)), (P["ShowInMenu"], flags(1, 1)),
             (P["WeaponDescriptor"], ref(2, 1))]),                                          # 0 unit A
        (0, [(P["ClassNameForDebug"], name(1)), (P["SeuilMort"], f32(20)), (P["ShowInMenu"], flags(1, 1)),
             (P["WeaponDescriptor"], ref(3, 1))]),                                          # 1 unit B
        (1, [(P["Puissance"], f32(5))]),                                                     # 2 A's weapon
        (1, [(P["Puissance"], f32(7))]),                                                     # 3 B's weapon
    ]
    return make_ndf(objects=objects, classes=CLASSES, props=PROPS, strings=["Unit_A", "Unit_B"],
                    exports={0: "GFX/Everything/Descriptor_Unit_A", 1: "GFX/Everything/Descriptor_Unit_B"},
                    topo=[0, 1])


def write_game(root: Path) -> Path:
    game = root / "R.U.S.E"
    rev = game / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\patchable\\gfx\\", [
        ("file", "everything.cpp.gladndfbin", everything())])]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", "us\\", [("file", "baseunite.dic", make_dic([(name_to_key("N_UNI_1"), "UNIT A")]))])])]))
    (game / "RUSE.exe").write_bytes(b"MZ")
    return game


def change(table, match, **values):
    return {"action": "patch", "table": table, "match": match,
            "set": {k: {"type": t, "value": v} for k, (t, v) in values.items()}}


CHANGES = [
    change("TUniteAuSolDescriptor", {"ClassNameForDebug": "Unit_A"}, SeuilMort=("Float32", 1.5),
           ShowInMenu=("List<Bool>", [0, 0])),                                  # by name: both Studio changes
    change("TWeaponDescriptor", {"_index": "3"}, Puissance=("Float32", 9.25)),   # a part, by number: a Studio change
    change("TUniteAuSolDescriptor", {"ClassNameForDebug": "Unit_B"}, Cost=("Int32", 5)),  # a value B hasn't got
    {"action": "create", "table": "TAmmunition", "match": {}, "local_id": "inst_4",
     "set": {"AmmunitionId": {"type": "UInt32", "value": 77}}},                 # a new object
]


def rmod_text(changes=CHANGES) -> str:
    return json.dumps({"$schema": "ruse-mod/v1", "id": "Mixed", "name": "Mixed Mod", "version": "1.0", "author": "Someone",
                       "description": "made up", "game_version": "",
                       "patches": [{"dat": PACK, "ndf": UNITS, "changes": changes}]})


def library_mod(folder: Path, changes=CHANGES) -> Path:
    """An .rmod mod as the Launcher keeps it: mod.toml + the file."""
    folder.mkdir(parents=True)
    (folder / "Mixed.rmod").write_text(rmod_text(changes), encoding="utf-8")
    (folder / "mod.toml").write_text('[mod]\nid = "mixed"\nname = "Mixed Mod"\nversion = "1.0.0"\n'
                                     'authors = ["Someone"]\n\n[rmod]\nfile = "Mixed.rmod"\n', encoding="utf-8")
    return folder


def unit_values(pack: Path) -> list:
    with Edat.open(str(pack)) as arc:
        ndf = ndfbin.read(bytes(arc.read(arc.entry(UNITS))))
    return [(ndf.classes[i.class_index].name,
             {ndf.properties[pv.prop_index].name: str(ndf.resolve_value(pv.value)) for pv in i.props})
            for i in ndf.instances]


class Convert(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.game = write_game(root)
        cls.index = build_index(cls.game, root / "index.sqlite", say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=self.tmp.name))

    def test_what_becomes_a_studio_change_and_what_stays(self):
        path = self.root / "Mixed.rmod"
        path.write_text(rmod_text(), encoding="utf-8")
        c = rmodconvert.convert(path, self.game, self.index)
        got = {(x.target, x.path, x.share): x.value for x in c.changes}
        self.assertEqual(got, {(A, "SeuilMort", ""): "1.5", (A, "ShowInMenu", ""): "[false, false]",
                               (B, "WeaponDescriptor.Puissance", "shared"): "9.25"})
        self.assertEqual(c.kept_counts(), {"values the Studio can't show yet": 1, "new objects": 1})
        kept = c.kept.patches[0].changes
        self.assertEqual([(k.action, dict(k.match), sorted(k.set_props)) for k in kept],
                         [("patch", {"ClassNameForDebug": "Unit_B"}, ["Cost"]), ("create", {}, ["AmmunitionId"])])

    def test_a_mod_with_only_values_leaves_no_rmod(self):
        folder = library_mod(self.root / "values", CHANGES[:2])
        c = convert_folder(folder, self.game, self.index)
        self.assertIsNone(c.kept)
        self.assertFalse((folder / "Mixed.rmod").exists())
        self.assertNotIn("[rmod]", (folder / "mod.toml").read_text(encoding="utf-8"))
        info, ops = load_mod(folder)
        self.assertIsNone(info.rmod)
        self.assertTrue(ops)

    def test_the_converted_mod_builds_the_same_unit_data(self):
        original = library_mod(self.root / "original")
        converted = library_mod(self.root / "converted")
        convert_folder(converted, self.game, self.index)
        edits = ModEdits(converted)
        self.assertEqual({(t, p): e.value for (t, p, _how), e in edits.edits.items()},
                         {(A, "SeuilMort"): 1.5, (A, "ShowInMenu"): [0, 0], (B, "WeaponDescriptor.Puissance"): 9.25})
        info, ops = load_mod(converted)
        self.assertEqual((info.rmod.name, bool(ops)), ("Mixed.rmod", True))  # both parts are built
        outs = []
        for folder in (original, converted):
            out = self.root / f"out-{folder.name}"
            result = build_and_write(self.game, [load_mod(folder)], out=out, say=lambda line: None)
            self.assertEqual(result.errors, [], folder.name)
            outs.append(unit_values(out / "ZZ_GladPatchableWin.dat"))
        self.assertEqual(outs[0], outs[1])
        self.assertEqual(outs[1][0][1]["SeuilMort"], "1.5")
        self.assertEqual(outs[1][3][1]["Puissance"], "9.25")
        self.assertEqual(len(outs[1]), 5)  # the new ammunition, from the .rmod kept

    def test_edit_an_installed_rmod_mod_in_the_studio(self):
        home = self.root / "home"
        library_mod(home / "library" / "mixed")
        api = StudioApi(index_path=self.index, game_dir=self.game, home=home)
        row = api.installed_mods()["mods"][0]
        self.assertTrue(row["older"])
        res = api.edit_installed("mixed", "Mixed Mine")
        self.assertEqual((res["copied"], res["values"], res["kept"]),
                         (True, 3, {"values the Studio can't show yet": 1, "new objects": 1}))
        self.assertIn("3 of Mixed Mod's changes are in the Studio now", res["message"])
        copy = Path(res["path"])
        self.assertTrue((copy / "src" / "studio.rndf").is_file())
        self.assertTrue((copy / "Mixed.rmod").is_file())
        self.assertEqual((home / "library" / "mixed" / "Mixed.rmod").read_text(encoding="utf-8"), rmod_text())
        self.assertIn(A, api.edited())  # the Units list marks what it changes
        nogame = StudioApi(index_path=self.root / "none.sqlite", find=lambda: None, home=home)
        with self.assertRaisesRegex(StudioError, "couldn't find R.U.S.E."):
            nogame.edit_installed("mixed", "Mixed Again")


if __name__ == "__main__":
    unittest.main()
