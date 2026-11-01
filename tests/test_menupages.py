"""Pages in a long build list (rusemod.menupages): the compiled template is of its source, joins after the game's menu
module only when every name it reads is there, and goes into the build when the mods make new objects, beside the
own-buildings tabs in the same script pack."""
import unittest

from rusemod import menupages as mp
from rusemod import ownbuildings as ob
from rusemod import pyscript
from test_ownbuildings import NEEDS, game_module, xyz

MENU_NEEDS = (b"headup", b"Menu")


class TemplateTest(unittest.TestCase):
    def test_compiled_of_its_source(self):
        self.assertIsInstance(mp.template("menu"), pyscript.Code)

    def test_rows_on_a_page(self):
        self.assertIn(f"_r2_rows = {mp.PAGE_ROWS}\n", mp.SOURCES["menu"])

    def test_joined_after_the_game_module(self):
        game = game_module(MENU_NEEDS)
        template = mp.template("menu")
        joined = pyscript.load(pyscript.append_module(game, template))
        before = pyscript.load(game)
        self.assertEqual(joined.code[:len(before.code) - 4], before.code[:-4])
        self.assertEqual(joined.names, before.names + template.names)
        self.assertEqual(joined.consts[len(before.consts):], template.consts)

    def test_refused_when_the_game_module_lacks_a_name(self):
        with self.assertRaisesRegex(pyscript.ScriptError, "Menu"):
            pyscript.append_module(game_module((b"headup",)), mp.template("menu"))


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
    def run_with(self, created, own=None):
        from types import SimpleNamespace
        from rusemod.build import BuildResult, menu_pages, own_buildings
        from rusemod.edat import Edat
        from rusemod.model import Obj
        from rusemod.patch import num
        zz = Edat(made_up_zz_win())
        objects = {"$/W": Obj("TBatimentDescriptor", {"TypeBatiment": num(6), "Menu": num(8)})} if own else {}
        run = SimpleNamespace(game=SimpleNamespace(objects=objects), created=created)
        result, scripts = BuildResult(), {}
        if own:
            own_buildings(run, zz, {6: None}, result, scripts)
        menu_pages(run, zz, result, scripts)
        return result, scripts

    def test_pages_when_the_mods_make_objects(self):
        result, scripts = self.run_with({"$/GFX/Everything/Descriptor_Unit_X": None})
        self.assertEqual(result.errors, [])
        members = {m.rsplit("\\", 1)[-1] for _pack, changed in scripts.values() for m in changed}
        self.assertEqual(members, {"menu.xyz"})
        code = pyscript.load(pyscript.read_xyz(next(iter(scripts.values()))[1][next(iter(
            next(iter(scripts.values()))[1]))]).payload)
        self.assertIn(b"_r2_liste_boutons", code.names)

    def test_none_when_the_mods_make_nothing(self):
        result, scripts = self.run_with({})
        self.assertEqual((result.errors, scripts), ([], {}))

    def test_beside_the_own_buildings_tabs_in_one_pack(self):
        result, scripts = self.run_with({"$/W": None}, own=True)
        self.assertEqual(result.errors, [])
        members = sorted(m.rsplit("\\", 1)[-1] for _pack, changed in scripts.values() for m in changed)
        self.assertEqual(members, ["camp.xyz", "menu.xyz", "menu_builder.xyz", "paramsmainmenu.xyz"])
        eugen = [changed for _pack, changed in scripts.values() if any(m.endswith("\\menu.xyz") for m in changed)]
        self.assertEqual(len(eugen), 1)
        self.assertEqual(sorted(m.rsplit("\\", 1)[-1] for m in eugen[0]), ["camp.xyz", "menu.xyz", "menu_builder.xyz"])
        self.assertEqual(ob.SCRIPTS["menu_builder"][0], mp.SCRIPTS["menu"][0])


if __name__ == "__main__":
    unittest.main()
