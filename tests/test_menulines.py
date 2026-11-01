"""A build list's lines as rows (rusemod.menulines): the compiled template is of its source and joins after the game's
menu module only when every name it reads is there; each new unit's line is the first unit of its upgrades or the unit
it was copied from; the build adds it when the mods make new objects, beside the own-buildings tabs in one pack."""
import unittest
from types import SimpleNamespace

from rusemod import menulines as ml
from rusemod import ownbuildings as ob
from rusemod import pyscript
from test_ownbuildings import NEEDS, game_module, xyz

MENU_NEEDS = (b"Menu",)


class TemplateTest(unittest.TestCase):
    def test_compiled_of_its_source(self):
        self.assertIsInstance(ml.template("menu"), pyscript.Code)

    def test_units_across(self):
        self.assertIn(f"_r2_across = {ml.ACROSS}\n", ml.SOURCES["menu"])

    def test_joined_after_the_game_module_with_the_lines(self):
        game = game_module(MENU_NEEDS)
        template = pyscript.with_value(ml.template("menu"), b"_r2_lines", ((b"Unit_N1", b"Unit_Kub"),))
        joined = pyscript.load(pyscript.append_module(game, template))
        before = pyscript.load(game)
        self.assertEqual(joined.code[:len(before.code) - 4], before.code[:-4])
        self.assertEqual(joined.names, before.names + template.names)
        self.assertIn(((b"Unit_N1", b"Unit_Kub"),), joined.consts)

    def test_refused_when_the_game_module_lacks_a_name(self):
        with self.assertRaisesRegex(pyscript.ScriptError, "Menu"):
            pyscript.append_module(game_module((b"headup",)), ml.template("menu"))


def obj(cls=None, upgrade=None):
    from rusemod.model import Obj
    from rusemod.patch import Ref, Text, num
    props = {}
    if cls:
        props["ClassNameForDebug"] = Text("string", cls)
    if upgrade:
        props["IsUpgrade"] = num(1)
        props["UpgradeRequire"] = Ref(upgrade)
    return Obj("TUniteDescriptor", props)


class LinesTest(unittest.TestCase):
    def test_each_new_unit_joins_its_line(self):
        g = "$/GFX/Everything/"
        objects = {g + "Kub": obj(), g + "222": obj(), g + "Puma": obj(upgrade=g + "222"),
                   g + "E1": obj("Unit_E1", upgrade=g + "Kub"),           # an upgrade of a game unit
                   g + "N1": obj("Unit_N1"),                              # bought from the start, a copy of Kub
                   g + "E2": obj("Unit_E2", upgrade=g + "N1"),            # an upgrade of a new unit
                   g + "P2": obj("Unit_P2")}                              # a copy of an upgrade (the Puma)
        by_path = {g + "Kub": "Unit_Kub", g + "222": "Unit_222", g + "Puma": "Unit_Puma"}
        clone = lambda source: SimpleNamespace(kind="clone", source=source)
        created = {g + "E1": clone(g + "Kub"), g + "N1": clone(g + "Kub"), g + "E2": clone(g + "Kub"),
                   g + "P2": clone(g + "Puma")}
        self.assertEqual(ml.lines_of(objects, by_path, created),
                         [("Unit_E1", "Unit_Kub"), ("Unit_E2", "Unit_Kub"), ("Unit_N1", "Unit_Kub"),
                          ("Unit_P2", "Unit_222")])


def made_up_zz_win() -> bytes:
    """ZZ_Win.dat with the game's menu module and the own-buildings ones, as made-up modules setting what they need."""
    from fixtures import make_edat
    eugen = make_edat([("dir", "genpython\\1000\\codeia\\python\\eugen\\", [
        ("dir", "base\\", [("file", "camp.xyz", xyz(NEEDS["camp"]))]),
        ("dir", "headup\\", [("file", "menu.xyz", xyz(MENU_NEEDS)),
                             ("file", "menu_builder.xyz", xyz(NEEDS["menu_builder"]))])])])
    patchable = make_edat([("dir", "genpython\\1000\\codeia\\python\\eugenpatchable\\parametres\\", [
        ("file", "paramsmainmenu.xyz", xyz(NEEDS["paramsmainmenu"]))])])
    return make_edat([("dir", "genpython\\", [("file", "eugen.ipk", eugen), ("file", "eugenpatchable.ipk", patchable)])])


class InTheBuild(unittest.TestCase):
    def run_with(self, created, own=False):
        from rusemod.build import BuildResult, menu_lines, own_buildings
        from rusemod.edat import Edat
        from rusemod.model import Obj
        from rusemod.patch import num
        zz = Edat(made_up_zz_win())
        objects = {"$/W": Obj("TBatimentDescriptor", {"TypeBatiment": num(6), "Menu": num(8)})} if own else {}
        run = SimpleNamespace(game=SimpleNamespace(objects=objects), created=created)
        result, scripts = BuildResult(), {}
        if own:
            own_buildings(run, zz, {6: None}, result, scripts)
        menu_lines(run, zz, result, scripts)
        return result, scripts

    def test_lines_when_the_mods_make_objects(self):
        result, scripts = self.run_with({"$/GFX/Everything/Descriptor_Unit_X": None})
        self.assertEqual(result.errors, [])
        (_pack, changed), = scripts.values()
        (member, data), = changed.items()
        self.assertTrue(member.endswith("\\menu.xyz"))
        self.assertIn(b"_r2_update_sub_buttons", pyscript.load(pyscript.read_xyz(data).payload).names)

    def test_none_when_the_mods_make_nothing(self):
        result, scripts = self.run_with({})
        self.assertEqual((result.errors, scripts), ([], {}))

    def test_beside_the_own_buildings_tabs_in_one_pack(self):
        result, scripts = self.run_with({"$/W": None}, own=True)
        self.assertEqual(result.errors, [])
        members = sorted(m.rsplit("\\", 1)[-1] for _pack, changed in scripts.values() for m in changed)
        self.assertEqual(members, ["camp.xyz", "menu.xyz", "menu_builder.xyz", "paramsmainmenu.xyz"])
        eugen = [changed for _pack, changed in scripts.values() if any(m.endswith("\\menu.xyz") for m in changed)]
        self.assertEqual(sorted(m.rsplit("\\", 1)[-1] for m in eugen[0]), ["camp.xyz", "menu.xyz", "menu_builder.xyz"])
        self.assertEqual(ob.SCRIPTS["menu_builder"][0], ml.SCRIPTS["menu"][0])


if __name__ == "__main__":
    unittest.main()
