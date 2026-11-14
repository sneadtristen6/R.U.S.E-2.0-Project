"""Scenarios: squads with soldiers of their own in a set with other mods, and a squad's mod exported and opened on
another PC: two mods each with a squad of its own number and looks built together in either order (as a Launcher set
or Test in game with several mods builds them); a mod with a squad (+1, a soldier's look, a Blender sending never
brought back) exported, added to another PC's Launcher library and opened there with Edit an installed mod. Each ends
with what the page says in every language, the files, the build on the made-up game and the Studio's check. The base,
its made-up game and its stand-ins: tests/test_scenarios_squads_base.py. (The Generic Horse in a set, and these on the
game: the dry builds of the scenarios' finished mods, scratch/release-0920/scenarios/squads.)

FOR: the squads scenarios (release 0.9.8.20, overnight 2026-11-13/14). USED-BY: the scenarios' run and report."""
import json
import tempfile
import unittest
from pathlib import Path

from test_scenarios_squads_adding import fill
from test_scenarios_squads_base import GAME_SQUAD, LANGS, RIFLE_MODEL, SQUAD, STEM, SquadScenario, model_glb, tree

THEIRS = "Descriptor_Unit_Their_Squad"


class InASet(SquadScenario):
    def own_count(self, loaded, stem: str) -> int:
        return int(loaded.base.objects["$/GFX/Everything/" + stem].props["R2Behaviour"].obj.props[
            "NbSoldatInGroupeCombat"].value)

    def test_two_mods_each_with_a_squad_of_its_own_in_either_order(self):
        """Usual: this mod's squad +1 (6) with soldier 2's own look; another mod's squad -1 (4) with soldier 1's own
        look. Built together, in either order: each squad its own number and look, the own-squads patch named once,
        no error; the same game data either way."""
        self.page.soldier_plus(SQUAD)
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        mine = self.mod
        theirs = Path(self.page.new_mod("Others")["current"])
        their_squad = self.page.new_unit(GAME_SQUAD, "Their Squad", 40)["address"]
        self.page.soldier_minus(their_squad)
        self.page.soldier_import(their_squad, "1", str(self.model_file("ranger.glb", b"glTF ranger")))
        self.assertEqual(self.problems(), [])
        got = []
        for order in ((mine, theirs), (theirs, mine)):
            with self.subTest(order=[m.name for m in order]):
                result, loaded = self.built(*order)
                self.assertEqual(self.errors(result), [])
                self.assertEqual((self.own_count(loaded, STEM), self.own_count(loaded, THEIRS)), (6, 4))
                self.assertEqual(sorted(result.own_models), [f"{STEM}@2", f"{THEIRS}@1"])
                self.assertEqual(result.game_patch, ["own-squads"])
                got.append(dict(result.changed))
        self.assertEqual(sorted(got[0]), sorted(got[1]))
        self.assertEqual([k for k in got[0] if got[0][k] != got[1][k]], [])


class ExportedAndOpenedAgain(SquadScenario):
    def test_a_squad_with_its_number_its_looks_and_a_blender_sending(self):
        """Usual: +1, soldier 2 a look of his own, and the squad opened in Blender, soldier 3 sent and not brought back;
        Export; on another PC, added to the Launcher's library and opened with Edit an installed mod: the squad has 6,
        soldier 2 his look (the page names its file in every language), the Blender sending stayed on the first PC
        (Export takes the mod's own files only: nothing waits to be brought back there), the copy builds as the mod did
        and the check finds nothing."""
        from ruse_studio.api import StudioApi
        from rusemod import package
        from rusemod.library import Library
        from rusemod.webui import page_api
        self.page.soldier_plus(SQUAD)
        self.page.soldier_import(SQUAD, "2", str(self.model_file("marine.glb", b"glTF marine")))
        self.page.blender_open(SQUAD, {"model": True, "paint": True, "soldiers": list("123456")}, "us")
        self.blender_opened()
        self.blender_sends({"3": model_glb(RIFLE_MODEL, b"CHG3")})
        before, _ = self.built()
        export = package.pack(self.mod, Path(tempfile.mkdtemp(dir=self.tmp.name)))
        other = StudioApi(index_path=self.index, game_dir=self.game, home=Path(tempfile.mkdtemp(dir=self.tmp.name)))
        other._look_models = self.api._look_models
        other._blender = self.api._blender
        page = page_api(other)
        info, _replaced = Library(other._home / "library").add(export)
        copy = Path(page.edit_installed(info["id"], "Squads (my copy)")["path"])
        page.choose_mod(str(copy))
        self.addCleanup(other.set_pref, "lang", "us")
        infos = {lang: page.squad_info(SQUAD, lang) for lang in LANGS}
        us = infos["us"]
        self.assertEqual((us["count"], [s["wears"] for s in us["soldiers"]]),
                         (6, ["game", "own", "game", "game", "game", "game"]))
        self.assertEqual((us["soldiers"][1]["from"], us["blender"]["waiting"], us["blender"]["made"]),
                         ("marine.glb", False, False))
        self.assert_worded({lang: fill(self.words(lang)["squad_now_file"], file=i["soldiers"][1]["from"])
                            for lang, i in infos.items()})
        self.assertEqual(sorted(n for n in tree(copy) if n.startswith("blender/")), [])
        # the files as the mod has them, the records naming the file each look was made from by its name alone
        # (Export's way: rusemod.package._record_want)
        mine = {n: v for n, v in tree(self.mod).items() if n.startswith("files/")}
        theirs = {n: v for n, v in tree(copy).items() if n.startswith("files/")}
        self.assertEqual(sorted(theirs), sorted(mine))
        for name in mine:
            with self.subTest(file=name):
                if not name.endswith(".json"):
                    self.assertEqual(theirs[name], mine[name])
                    continue
                a, b = json.loads(mine[name]), json.loads(theirs[name])
                if "from" in a:
                    self.assertEqual(Path(a.pop("from")).name, b.pop("from"))
                a.pop("report", None), b.pop("report", None)
                self.assertEqual(a, b)
        result, loaded = self.built(copy)
        self.assertEqual(self.errors(result), [])
        self.assertEqual(sorted(result.own_models), sorted(before.own_models))
        self.assertEqual(result.changed, before.changed)
        self.assertEqual([p.get("problem") for p in page.check_mod()["problems"]], [])


if __name__ == "__main__":
    unittest.main()
