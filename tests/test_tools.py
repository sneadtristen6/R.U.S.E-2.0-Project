"""tools/rmod_to_mod.py, run on made-up mods (no game files needed)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
import rmod_to_mod  # noqa: E402
from rusemod.build import load_mod  # noqa: E402
from rusemod.dic import name_to_key  # noqa: E402
from rusemod.patch import Engine, Game, Inline, ListV, Obj, Ref, Text, num, nums  # noqa: E402
from rusemod.resolve import ModInfo  # noqa: E402


def loc_hash(name: str) -> str:
    """How a .rmod writes a text key: the 64-bit key's eight bytes in file order, as hex."""
    return name_to_key(name).to_bytes(8, "little").hex()


NDF = "genglad/patchable/gfx/everything.cpp.gladndfbin"
SYNTHETIC_RMOD = {
    "$schema": "ruse-mod/v1", "id": "synthetic", "name": "Synthetic", "version": "1.2.0", "author": "tests",
    "description": "A made-up mod with one of everything.", "game_version": "24087620",
    "patches": [{"dat": "Data/PC/190852/ZZ_GladPatchableWin.dat", "ndf": NDF, "changes": [
        {"action": "patch", "table": "TUniteAuSolDescriptor", "match": {"ClassNameForDebug": "Unit_X"},
         "set": {"SeuilMort": {"type": "Float32", "value": 250.0},
                 "InitialFlagSet": {"type": "List<UInt32>", "value": [10, 71]}}},
        {"action": "patch", "table": "TAmmunition", "match": {"AmmunitionId": "1120"},
         "set": {"NbTirParSalves": {"type": "Int32", "value": 40}}},
        {"action": "patch", "table": "TIAProfil", "match": {}, "set": {"NbProdIdleInfanterie": {"type": "Int32", "value": 3}}},
        {"action": "patch", "table": "TTunableConstante", "match": {"_index": "0"},
         "set": {"NbAvionsParAeroport": {"type": "Int32", "value": 24}}},
        {"action": "create", "table": "TAmmunition", "local_id": "inst_new", "top_object": True,
         "set": {"AmmunitionId": {"type": "UInt32", "value": 9000}, "Name": {"type": "LocHash", "value": loc_hash("NEWGUN1")},
                 "Icon": {"type": "ObjRef", "value": {"anchor": {"root": ["ClassNameForDebug", "Unit_X"],
                                                                 "steps": [["Weapons", "[0]"], ["Ammunition"]]}}}}},
        {"action": "patch", "table": "TWeapon", "match": {"anchor": {"root": ["ClassNameForDebug", "Unit_X"],
                                                                     "steps": [["Weapons", "[0]"]]}},
         "set": {"Ammunition": {"$ref": "inst_new"}}},
        {"action": "patch", "table": "TIAProfil", "match": {"_index": "77"}, "set": {"NbProdIdleTank": {"type": "Int32", "value": 9}}},
        {"action": "delete_props", "table": "TUniteAuSolDescriptor", "match": {"ClassNameForDebug": "Unit_X"}, "props": ["SeuilPinned"]},
    ]}],
    "loc_patches": [{"dat": "Data/PC/190852/ZZ_Win.dat", "dic": f"genlocalisation/ww2/localisation/translations/{lang}/baseunite.dic",
                     "entries": [{"key": loc_hash("N_UNI_15"), "value": "Speed bump"},
                                 {"key": loc_hash("NEWGUN1"), "value": "New gun", "add": True}]} for lang in ("us", "fr")],
    "file_patches": [{"dat": "Data/PC/190852/Data_Common.dat", "files": [{"path": "ww2\\videos\\logo\\eugen.webm", "data": "AAAA"}]}],
}


def synthetic_game() -> Game:
    ammo = Inline(Obj("TAmmunition", {"AmmunitionId": num(1120, "uint32"), "NbTirParSalves": num(8)}, origin=("f", 3)))
    return Game(objects={
        "$/GFX/Everything/Descriptor_Unit_X": Obj("TUniteAuSolDescriptor", {
            "ClassNameForDebug": Text("string", "Unit_X"), "SeuilMort": num("100", "float32"),
            "SeuilPinned": num("50", "float32"), "InitialFlagSet": nums([10], "uint32"),
            "Weapons": ListV([Inline(Obj("TWeapon", {"Ammunition": ammo}, origin=("f", 2)))])}, origin=("f", 1)),
        "$/Const": Obj("TTunableConstante", {"NbAvionsParAeroport": num(8)}, origin=("f", 4)),
        "$/IA/A": Obj("TIAProfil", {"NbProdIdleInfanterie": num(0)}, origin=("f", 5)),
        "$/IA/B": Obj("TIAProfil", {"NbProdIdleInfanterie": num(1)}, origin=("f", 6)),
    })


class RmodToMod(unittest.TestCase):
    """A made-up RUSE-Mod-Manager mod becomes a mod of ours that the engine runs (MOD_FORMAT §13)."""

    def convert(self, data, name="Synthetic_V1.rmod"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        src = os.path.join(tmp.name, name)
        with open(src, "w", encoding="utf-8") as f:
            json.dump(data, f)
        out = os.path.join(tmp.name, "mods")
        with contextlib.redirect_stdout(io.StringIO()) as said:
            rmod_to_mod.main([src, "--out", out])
        self.assertIn(data["id"], said.getvalue())
        return os.path.join(out, data["id"])

    def test_a_copied_unit_is_named_by_its_export_path_so_it_matches_one_object(self):
        """A copy keeps its source's debug name while the mod runs, so a debug-name match would find two objects."""
        by_debug = {"anchor": {"root": ["ClassNameForDebug", "Unit_X"], "steps": [["Weapons", "[0]"]]}}
        data = {"$schema": "ruse-mod/v1", "id": "armed-factories", "name": "Copies", "version": "1.0.0", "patches": [
            {"dat": "Data/PC/190852/ZZ_GladPatchableWin.dat", "ndf": NDF, "changes": [
                {"action": "create", "table": "TUniteAuSolDescriptor", "local_id": "inst_afg_unit", "top_object": True,
                 "set": {"ClassNameForDebug": {"type": "StringRef", "value": "Unit_Guard"},
                         "SeuilMort": {"type": "Float32", "value": 300.0},
                         "Weapons": {"type": "List<ObjRef>", "value": [by_debug]}}},
                {"action": "patch", "table": "TUniteAuSolDescriptor", "match": {"ClassNameForDebug": "Unit_X"},
                 "set": {"SeuilPinned": {"type": "Float32", "value": 60.0}}},
            ]}]}
        saved = rmod_to_mod.RECIPES.get("armed-factories")
        rmod_to_mod.RECIPES["armed-factories"] = {"create_as_clone": {"inst_afg_unit": "@[ClassNameForDebug='Unit_X']"}}
        try:
            folder = self.convert(data, "Copies_V1.rmod")
        finally:
            rmod_to_mod.RECIPES["armed-factories"] = saved
        with open(os.path.join(folder, "src", "armed-factories.rndf"), encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("ClassNameForDebug='Unit_X'", text)
        self.assertIn("is clone $/GFX/Everything/Descriptor_Unit_X", text)
        info, ops = load_mod(folder)
        r = Engine(synthetic_game()).run([(ModInfo("armed-factories"), ops)])
        self.assertEqual([f.message for f in r.errors], [])  # it failed: "matches 2 objects"
        self.assertEqual(r.game.objects["$/GFX/Everything/Descriptor_Unit_X"].props["SeuilPinned"].value, 60)
        guard = r.game.objects["$/GFX/Everything/Descriptor_Unit_Guard"]
        self.assertEqual(guard.props["SeuilMort"].value, 300)

    def test_a_renamed_unit_is_still_found_by_later_changes(self):
        """RUSE-Mod-Manager lets a mod rename a unit (its debug name) and change it again under the old name."""
        data = {"$schema": "ruse-mod/v1", "id": "renames", "name": "Renames", "version": "1.0.0", "patches": [
            {"dat": "Data/PC/190852/ZZ_GladPatchableWin.dat", "ndf": NDF, "changes": [
                {"action": "patch", "table": "TWeapon",
                 "match": {"anchor": {"root": ["ClassNameForDebug", "Unit_X"], "steps": [["Weapons", "[0]"]]}},
                 "set": {"Portee": {"type": "Float32", "value": 5.0}}},
                {"action": "patch", "table": "TUniteAuSolDescriptor", "match": {"ClassNameForDebug": "Unit_X"},
                 "set": {"SeuilMort": {"type": "Float32", "value": 80.0},
                         "ClassNameForDebug": {"type": "StringRef", "value": "Unit_Renamed"},
                         "SeuilPinned": {"type": "Float32", "value": 70.0}}},
                {"action": "delete_props", "table": "TUniteAuSolDescriptor", "match": {"ClassNameForDebug": "Unit_X"},
                 "props": ["InitialFlagSet"]},
            ]}]}
        folder = self.convert(data, "Renames_V1.rmod")
        info, ops = load_mod(folder)
        r = Engine(synthetic_game()).run([(ModInfo("renames"), ops)])
        self.assertEqual([f.message for f in r.errors], [])  # it failed: "[ClassNameForDebug='Unit_X'] doesn't exist"
        unit = r.game.objects["$/GFX/Everything/Descriptor_Unit_X"]
        self.assertEqual((unit.props["SeuilMort"].value, unit.props["SeuilPinned"].value), (80, 70))
        self.assertEqual(unit.props["ClassNameForDebug"], Text("string", "Unit_Renamed"))
        self.assertNotIn("InitialFlagSet", unit.props)
        self.assertEqual(unit.props["Weapons"].items[0].obj.props["Portee"].value, 5)

    def test_new_objects_with_numbered_ids_get_names_the_engine_accepts(self):
        """RUSE-Mod-Manager numbers the objects a mod adds (inst_63686, 254); a name of ours starts with a letter."""
        weapon = {"anchor": {"root": ["ClassNameForDebug", "Unit_X"], "steps": [["Weapons", "[0]"]]}}
        data = {"$schema": "ruse-mod/v1", "id": "numbered", "name": "Numbered", "version": "1.0.0", "patches": [
            {"dat": "Data/PC/190852/ZZ_GladPatchableWin.dat", "ndf": NDF, "changes": [
                {"action": "create", "table": "TAmmunition", "local_id": "inst_63686", "top_object": True,
                 "set": {"AmmunitionId": {"type": "UInt32", "value": 9001}}},
                {"action": "create", "table": "TAmmunition", "local_id": "63686",
                 "set": {"AmmunitionId": {"type": "UInt32", "value": 9002}}},
                {"action": "create", "table": "TUIResourceTexture", "local_id": "254", "set": {}},
                {"action": "patch", "table": "TWeapon", "match": weapon, "set": {"Ammunition": {"$ref": "inst_63686"}}},
                # a value that can't be rebuilt becomes a note: it must not swallow the statement's closing bracket
                {"action": "patch", "table": "TUniteAuSolDescriptor", "match": {"ClassNameForDebug": "Unit_X"},
                 "set": {"SeuilMort": {"type": "Float32", "value": 9.0}, "Scale": {"type": "Vector3", "value": [9.0, 9.0, 9.0]}}},
                # a text key that doesn't decode to a name of ours is written as its number
                {"action": "patch", "table": "TTunableConstante", "match": {},
                 "set": {"Title": {"type": "LocHash", "value": loc_hash("3mbieWeap")}}},
            ]}]}
        self.assertEqual(rmod_to_mod.our_name("inst_63686", {"table": "TAmmunition"}), "Ammunition_63686")
        self.assertEqual(rmod_to_mod.our_name("254", {"table": "TUIResourceTexture"}), "UIResourceTexture_254")
        self.assertEqual(rmod_to_mod.our_name("inst_new_gun", {"table": "TAmmunition"}), "New_Gun")  # as before
        self.assertEqual(rmod_to_mod.unique_names({"a": "X", "b": "X", "c": "X_2", "d": "Y"}),
                         {"a": "X", "b": "X_3", "c": "X_2", "d": "Y"})
        folder = self.convert(data, "Numbered_V1.rmod")
        info, ops = load_mod(folder)  # it failed here: "expected the new object's name (found '63686')"
        r = Engine(synthetic_game()).run([(ModInfo("numbered"), ops)])
        self.assertEqual([f.message for f in r.errors], [])
        made = sorted(n.rsplit("/", 1)[1] for n in r.game.objects if "63686" in n or "254" in n)
        self.assertEqual(made, ["Ammunition_63686", "Ammunition_63686_2", "UIResourceTexture_254"])
        unit = r.game.objects["$/GFX/Everything/Descriptor_Unit_X"]
        self.assertEqual(unit.props["Weapons"].items[0].obj.props["Ammunition"], Ref("$/GFX/Everything/Ammunition_63686"))
        self.assertEqual(unit.props["SeuilMort"].value, 9)
        self.assertEqual(r.game.objects["$/Const"].props["Title"], Text("key", f"0x{name_to_key('3mbieWeap'):016X}"))
        with open(os.path.join(folder, "src", "numbered.rndf"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("// not rebuilt: Scale", text)
        for path in Path(folder).rglob("*"):  # the same bytes on every PC: no Windows line ends
            if path.is_file():
                self.assertNotIn(b"\r", path.read_bytes(), path.name)
        for line in text.splitlines():  # no statement line carries a note before its closing bracket
            if line.lstrip().startswith(("patch", "export")) or " is " in line.split("//")[0]:
                self.assertFalse("//" in line and line.rstrip().endswith(")"), line)

    def test_everything_carries_over_and_runs(self):
        folder = self.convert(SYNTHETIC_RMOD)
        info, ops = load_mod(folder)
        self.assertEqual((info.id, info.version), ("synthetic", "1.2.0"))
        rows = {r.key: r for r in info.texts}
        self.assertEqual(rows["game:N_UNI_15"].texts, {"us": "Speed bump"})  # the same text in both languages: one column
        self.assertEqual((rows["synthetic.NEWGUN1"].game_key, rows["synthetic.NEWGUN1"].texts["us"]), ("NEWGUN1", "New gun"))
        r = Engine(synthetic_game()).run([(ModInfo("synthetic"), ops)])
        self.assertEqual([f.message for f in r.errors], [])
        unit = r.game.objects["$/GFX/Everything/Descriptor_Unit_X"]
        self.assertEqual(unit.props["SeuilMort"].value, 250)
        self.assertEqual([(int(n.value), n.kind) for n in unit.props["InitialFlagSet"].items], [(10, "uint32"), (71, "uint32")])
        self.assertNotIn("SeuilPinned", unit.props)
        new = r.game.objects["$/GFX/Everything/New"]  # the created ammunition, named after its local id
        self.assertEqual(unit.props["Weapons"].items[0].obj.props["Ammunition"], Ref("$/GFX/Everything/New"))
        self.assertEqual(new.props["Name"], Text("loc", "synthetic.NEWGUN1"))
        self.assertEqual(new.props["Icon"], Ref("f#3"))  # the old ammunition, now shared under a name of its own
        self.assertEqual(r.game.objects["f#3"].props["NbTirParSalves"].value, 40)  # found by AmmunitionId
        self.assertEqual([r.game.objects[n].props["NbProdIdleInfanterie"].value for n in ("$/IA/A", "$/IA/B")], [3, 3])
        self.assertEqual(r.game.objects["$/Const"].props["NbAvionsParAeroport"].value, 24)
        with open(os.path.join(folder, "mod.toml"), encoding="utf-8") as f:
            manifest = f.read()
        self.assertIn('builds = ["24087620"]', manifest)
        self.assertIn('file         = "Synthetic_V1.rmod"', manifest)
        with open(os.path.join(folder, "README.md"), encoding="utf-8") as f:
            readme = f.read()
        self.assertIn("TIAProfil object #77", readme)  # matched by position: not rebuilt, said so
        self.assertIn("eugen.webm", readme)
        with open(os.path.join(folder, "src", "synthetic.rndf"), encoding="utf-8") as f:
            rndf = f.read()
        self.assertIn("// Not rebuilt (TIAProfil object #77", rndf)
        self.assertIn("//     NbProdIdleTank = 9", rndf)  # the values stay, as comments

    def test_a_flag_recipe_turns_a_whole_list_into_a_list_edit(self):
        data = dict(SYNTHETIC_RMOD, id="all-around-awareness", loc_patches=[], file_patches=[])
        data["patches"] = [{"dat": "x", "ndf": NDF, "changes": [SYNTHETIC_RMOD["patches"][0]["changes"][0]]}]
        folder = self.convert(data, "All_Around_Awareness_V1.rmod")
        info, ops = load_mod(folder)
        r = Engine(synthetic_game()).run([(ModInfo(info.id), ops)])
        flags = r.game.objects["$/GFX/Everything/Descriptor_Unit_X"].props["InitialFlagSet"].items
        self.assertEqual([(int(n.value), n.kind) for n in flags], [(10, "uint32"), (71, "uint32")])
        self.assertEqual([o.kind for o in ops], ["set", "append"])


if __name__ == "__main__":
    unittest.main()
