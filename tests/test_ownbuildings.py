"""Buildings with units of their own (rusemod.ownbuildings): the compiled templates are of their sources, the build
fills in which tabs the mods have, joins each after the game's module only when every name it reads is there, and
writes the build bar's entries."""
import unittest

from rusemod import ownbuildings as ob
from rusemod import pyscript
from rusemod.build import _own_kinds_planned
from rusemod.rndf import parse

LOAD_CONST, STORE_NAME, RETURN_VALUE = 100, 90, 83


def game_module(names) -> bytes:
    """A made-up game module (marshal, Python 2.5) that sets `names` to None and ends with `return None`."""
    code = b""
    for i in range(len(names)):
        code += bytes([LOAD_CONST, 0, 0, STORE_NAME, i, 0])
    code += bytes([LOAD_CONST, 0, 0, RETURN_VALUE])
    mod = pyscript.Code(0, 0, 1, 64, code, (None,), tuple(names), (), (), (), b"game.py", b"<module>", 1, b"")
    return pyscript.dump(mod)


NEEDS = {"menu_builder": (b"Hud", b"MenuBuilderUnit", b"_enum_for_game_play"),
         "paramsmainmenu": (b"MainMenuDescriptor", b"_enum_for_game_play"),
         "camp": (b"camp", b"_virtual_factory", b"_enum_for_game_play")}


class TemplatesTest(unittest.TestCase):
    def test_compiled_of_their_sources(self):
        for name in ob.SOURCES:
            code = ob.template(name)
            self.assertIsInstance(code, pyscript.Code)

    def test_filled_with_the_mods_tabs(self):
        for name in ob.SOURCES:
            code = pyscript.with_value(ob.template(name), b"_r2_own", (b"R2Own1",))
            self.assertIn((b"R2Own1",), code.consts)
            self.assertNotIn((b"R2Own1", b"R2Own2", b"R2Own3"), code.consts)

    def test_joined_after_the_game_module(self):
        for name, needs in NEEDS.items():
            game = game_module(needs)
            template = pyscript.with_value(ob.template(name), b"_r2_own", (b"R2Own1", b"R2Own3"))
            joined = pyscript.load(pyscript.append_module(game, template))
            before = pyscript.load(game)
            self.assertEqual(joined.code[:len(before.code) - 4], before.code[:-4])
            self.assertEqual(joined.consts[:len(before.consts)], before.consts)
            self.assertEqual(joined.consts[len(before.consts):], template.consts)
            self.assertEqual(joined.names, before.names + template.names)
            self.assertEqual(len(joined.code), len(before.code) - 4 + len(template.code))

    def test_refused_when_the_game_module_lacks_a_name(self):
        game = game_module((b"Hud", b"_enum_for_game_play"))
        with self.assertRaisesRegex(pyscript.ScriptError, "MenuBuilderUnit"):
            pyscript.append_module(game, ob.template("menu_builder"))

    def test_keys(self):
        self.assertEqual(ob.keys_for([7, 6]), ("R2Own1", "R2Own3"))
        self.assertEqual(ob.MENU_OF, {6: 8, 4: 9, 7: 10})


class TabsTest(unittest.TestCase):
    GAME_KEYS = ["Automotors", "Bluff", "Canons", "Dev", "DevBluff", "Experiments", "Infantry", "NestBuildings", "Nuke",
                 "Planes", "Tanks"]

    def test_bar_entries(self):
        text = ob.tabs_rndf([(6, "studio.Descriptor_Building_X.name"), (7, None)], self.GAME_KEYS)
        ops = parse(text, file="t", mod="t")
        clones = [op for op in ops if op.kind == "clone"]
        self.assertEqual([op.target.rsplit("/", 1)[-1] for op in clones],
                         ["MainMenuInfos_R2_R2Own1", "MainMenuInfos_R2_R2Own3"])
        self.assertTrue(all(op.source.endswith("MainMenuInfosDico[5].v") for op in clones))
        self.assertIn("('Tanks', $/GFX/Everything/InterfaceInGameResourceMainMenuInfos:MainMenuInfosDico[10].v)", text)
        self.assertIn("('R2Own3', ~/MainMenuInfos_R2_R2Own3)", text)
        self.assertIn("PositionInMenu = 14", text)
        self.assertEqual(text.count("TitleToken = loc('studio.Descriptor_Building_X.name')"), 1)


def xyz(names) -> bytes:
    return pyscript.write_xyz(pyscript.Xyz(b"\0" * 16, game_module(names)))


def made_up_zz_win() -> bytes:
    """ZZ_Win.dat with the three game modules the templates go after, as made-up modules setting what they need."""
    from fixtures import make_edat
    eugen = make_edat([("dir", "genpython\\1000\\codeia\\python\\eugen\\", [
        ("dir", "base\\", [("file", "camp.xyz", xyz(NEEDS["camp"]))]),
        ("dir", "headup\\", [("file", "menu_builder.xyz", xyz(NEEDS["menu_builder"]))])])])
    patchable = make_edat([("dir", "genpython\\1000\\codeia\\python\\eugenpatchable\\parametres\\", [
        ("file", "paramsmainmenu.xyz", xyz(NEEDS["paramsmainmenu"]))])])
    return make_edat([("dir", "genpython\\", [("file", "eugen.ipk", eugen), ("file", "eugenpatchable.ipk", patchable)])])


class InTheBuild(unittest.TestCase):
    def run_with(self, buildings, planned):
        from types import SimpleNamespace
        from rusemod.build import BuildResult, own_buildings
        from rusemod.edat import Edat
        from rusemod.model import Obj
        from rusemod.patch import num
        objects = {name: Obj("TBatimentDescriptor", {"TypeBatiment": num(k), "Menu": num(m)})
                   for name, (k, m) in buildings.items()}
        result, scripts = BuildResult(), {}
        own_buildings(SimpleNamespace(game=SimpleNamespace(objects=objects)), Edat(made_up_zz_win()), planned, result,
                      scripts)
        return result, scripts

    def test_tabs_scripts_and_the_patch(self):
        result, scripts = self.run_with({"$/W": (6, 8), "$/X": (7, 10), "$/Armor": (10, 1)}, {6: None, 7: None})
        self.assertEqual(result.errors, [])
        self.assertEqual((result.own_kinds, result.game_patch), ([6, 7], "more-buildings"))
        members = {m.rsplit("\\", 1)[-1] for _pack, changed in scripts.values() for m in changed}
        self.assertEqual(members, {"camp.xyz", "menu_builder.xyz", "paramsmainmenu.xyz"})
        for _pack, changed in scripts.values():
            for data in changed.values():
                code = pyscript.load(pyscript.read_xyz(data).payload)
                self.assertIn((b"R2Own1", b"R2Own3"), code.consts)      # the mod's tabs, filled in

    def test_kind_6_alone_needs_no_patch(self):
        result, _scripts = self.run_with({"$/W": (6, 8)}, {6: None})
        self.assertEqual((result.errors, result.game_patch), ([], None))

    def test_a_building_in_another_menu_is_refused(self):
        result, _scripts = self.run_with({"$/W": (4, 8)}, {4: None})
        self.assertTrue(any("needs build menu 9" in f.message for f in result.errors))


class PlannedTest(unittest.TestCase):
    def test_read_from_the_mods_files(self):
        ops = parse("export Descriptor_Building_W is clone $/GFX/Everything/Descriptor_Building_ExperimentalFactory\n"
                    "(\n    NameInMenuToken = loc('studio.W.name')\n    TypeBatiment = 4\n    Menu = 9\n)\n"
                    "export Descriptor_Building_A is clone $/GFX/Everything/Descriptor_Building_VehiculeFactory\n"
                    "(\n    TypeBatiment = 10\n)\n", file="t", mod="t")
        self.assertEqual(_own_kinds_planned([ops]), {4: "studio.W.name"})


if __name__ == "__main__":
    unittest.main()
