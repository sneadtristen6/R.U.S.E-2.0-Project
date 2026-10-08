"""Missions' places in the menus (rusemod.menuorder: a mod's menus.toml, LittleGroove's Move up / Move down): the file
read and written, a group's order put in its places, the moves worked out (rusemod.missionsteps.run/move), and, when
the game is here, the game's own menus: every mission named as his registry binds it, a group reordered in the menus'
file by the build's step, and the Studio's Move up and Game's order saving it in a mod."""
import tempfile
import tomllib
import types
import unittest
from pathlib import Path

from rusemod import menuorder, missionsteps
from rusemod.build import BuildError, load_mod
from rusemod.package import files_of

BH, TWO = "Alpha/LevelDesign_BH.scenario", "TwoIslands/leveldesign_challenge.scenario"


class File(unittest.TestCase):
    def test_read_as_written(self):
        orders = [menuorder.Order("operation", [BH, TWO]), menuorder.Order("battles", ["A/a.scenario", "B/b.scenario"])]
        self.assertEqual(menuorder.parse(tomllib.loads(menuorder.text(orders))), orders)

    def test_mistakes_said(self):
        two = ["A/a.scenario", "B/b.scenario"]
        for data in ({"orders": []},                                                    # not [[order]]
                     {"order": [{"menu": "skirmish", "missions": two}]},                 # no such menu
                     {"order": [{"menu": "battles", "missions": two[:1]}]},             # one mission: no order
                     {"order": [{"menu": "battles", "missions": ["A/a.scenario", "a/A.SCENARIO"]}]},  # twice
                     {"order": [{"menu": "battles", "missions": ["A/a.scenario", "b.scenario"]}]},   # no map
                     {"order": [{"menu": "battles", "missions": two, "after": "A/a.scenario"}]}):     # unknown key
            with self.subTest(data=data), self.assertRaises(menuorder.MenuOrderError):
                menuorder.parse(data)

    def test_put_in_the_places_they_had(self):
        self.assertEqual(menuorder.arrange([1, 2, 3, 4, 5], [4, 2]), [1, 4, 3, 2, 5])  # 3 keeps its place
        self.assertEqual(menuorder.arrange([1, 2, 3], [3, 9, 1]), [3, 2, 1])            # one it hasn't: left out
        self.assertEqual(menuorder.arrange([1, 2, 3], [2]), [1, 2, 3])

    def test_a_mod_s_menus_toml(self):
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp)
            (mod / "mod.toml").write_text('[mod]\nid = "order"\nversion = "1.0.0"\n', encoding="utf-8")
            (mod / "menus.toml").write_text(menuorder.text([menuorder.Order("operation", [TWO, BH])]), encoding="utf-8")
            info, _ops = load_mod(mod)
            self.assertEqual(info.menu_order, [menuorder.Order("operation", [TWO, BH])])
            self.assertIn(mod / "menus.toml", files_of(mod))  # exported with the mod
            (mod / "menus.toml").write_text('[[order]]\nmenu = "nope"\n', encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "menu must be one of"):
                load_mod(mod)


def entry(info, pack, group, this=False, name=None):
    return {"info": info, "pack": pack, "group": group, "this": this, "mission": name or f"M{info}/m.scenario"}


class Moves(unittest.TestCase):
    """A mission moves among the entries side by side with it in its pack's list with its group (his
    move_within_group)."""

    def test_within_its_group(self):
        order = [entry(1, 9, None), entry(2, 9, 1), entry(3, 9, 1, True), entry(4, 9, 1), entry(5, 8, 1)]
        self.assertEqual(missionsteps.run(order), (1, 4))  # not 1 (another group), not 5 (another pack's list)
        self.assertEqual(missionsteps.move(order, -1), ["M3/m.scenario", "M2/m.scenario", "M4/m.scenario"])
        self.assertEqual(missionsteps.move(order, 1), ["M2/m.scenario", "M4/m.scenario", "M3/m.scenario"])

    def test_not_past_its_group_or_its_list(self):
        first = [entry(1, 9, 0), entry(2, 9, 1, True), entry(3, 9, 1)]
        last = [entry(2, 9, 1), entry(3, 9, 1, True), entry(5, 9, 2)]
        other_list = [entry(2, 9, 1), entry(3, 9, 1, True), entry(5, 8, 1)]  # its group goes on in another pack's list
        with self.assertRaisesRegex(ValueError, "top"):
            missionsteps.move(first, -1)
        with self.assertRaisesRegex(ValueError, "bottom"):
            missionsteps.move(last, 1)
        with self.assertRaisesRegex(ValueError, "pack"):
            missionsteps.move(other_list, 1)
        unnamed = [entry(2, 9, 1), entry(3, 9, 1, True), dict(entry(4, 9, 1), mission=None)]
        with self.assertRaisesRegex(ValueError, "unnamed"):
            missionsteps.move(unnamed, -1)


class RealGame(unittest.TestCase):
    """The game's own menus (only when the game and its index are here)."""

    def setUp(self):
        from rusemod.index import default_path
        from rusemod.steam import find_game
        found = find_game()
        if found is None:
            self.skipTest("R.U.S.E. isn't installed here")
        self.game = Path(found["game_dir"])
        self.index = Path(default_path(self.game))

    def test_every_mission_named_and_a_group_reordered(self):
        from rusemod.build import _menu_orders, find_pack
        from rusemod.edat import Edat
        from rusemod.ndf import Ndf, local_ref, sub_values
        from rusemod.players import GLOBALS, MAPINFO
        from rusemod.resolve import ModInfo
        with missionsteps.PackStore(self.game) as store:
            def read(member):
                return store.get_raw("gameplay", member)
            records = menuorder.records(Ndf(read(MAPINFO)), Ndf(read(GLOBALS)), read)
            first = None
            for d, bs in missionsteps.bindings(store).items():
                for b in bs:
                    if b.kind in missionsteps.KINDS and b.has_file:
                        name = menuorder.mission(d, b.scenario_name + ".scenario")
                        menu = missionsteps.MENU_OF[b.kind]
                        self.assertEqual(records.get(menuorder.key(menu, name)), b.info_idx, name)  # as he binds it
                        if b.kind == "operation" and first is None:
                            first = missionsteps.Mission(d, b.scenario_name, b.kind, b.info_idx, b.pack_idx, None)
                        if b.kind == "campaign" and b.pack_idx is not None:
                            chapter = missionsteps.Mission(d, b.scenario_name, b.kind, b.info_idx, b.pack_idx, None)
            self.assertEqual(len(records), 68)
            # the campaign's groups leave out the tutorial's chapters (another menu), unless it's the one looked at
            from ruse_mod_engine import scenario_chain as chain_mod
            g_engine = store.get_ndf("gameplay", chain_mod.GLOBALS_PATH)
            shown = missionsteps.menu(store, chapter)["order"]
            tuto = {o["pack"] for o in shown if missionsteps._flag(g_engine, g_engine.instances[o["pack"]], "IsTuto")}
            self.assertTrue(tuto <= {chapter.pack_idx})
            order = missionsteps.menu(store, first)["order"]
            s, e = missionsteps.run(order)
            other = next(o for o in order if o["pack"] != order[s]["pack"])  # an Operation of another menu pack
            # a mission the game hasn't got is left out with a note; missions of two lists aren't put together
            _changes, notes, problems = menuorder.apply(read, [
                (menuorder.Order("operation", [order[s]["mission"], "Nowhere/none.scenario"]), "t"),
                (menuorder.Order("operation", [order[s]["mission"], other["mission"]]), "t")])
            self.assertTrue(any("Nowhere/none.scenario" in n for n in notes))
            self.assertEqual(len(problems), 1)
        self.assertGreaterEqual(e - s, 2)
        group = order[s:e]
        swapped = [group[1]["mission"], group[0]["mission"]] + [o["mission"] for o in group[2:]]
        info = ModInfo("order")
        info.menu_order = [menuorder.Order("operation", swapped)]
        result = types.SimpleNamespace(order=["order"], changed={}, findings=[])
        said = []
        with Edat.open(str(find_pack(self.game, "ZZ_GladPatchableWin.dat"))) as arc:
            _menu_orders(result, [(info, [])], arc, said.append)
        self.assertEqual(result.findings, [])
        self.assertEqual([m.lower() for m in result.changed], [GLOBALS])
        g = Ndf(next(iter(result.changed.values())))
        lists = [[local_ref(x) for x in sub_values(v)] for o in g.objects for _pi, v in o.props
                 if v.tc == 0x11 and group[0]["info"] in {local_ref(x) for x in sub_values(v)}]
        self.assertEqual(len(lists), 1)
        at = lists[0].index(group[1]["info"])
        self.assertEqual(lists[0][at:at + len(group)], [group[1]["info"], group[0]["info"]]
                         + [o["info"] for o in group[2:]])
        self.assertTrue(any("in that order" in line for line in said))

    def test_the_studio_s_move_up_and_game_s_order(self):
        if not self.index.is_file():
            self.skipTest("the game index isn't built here")
        from rusemod.play import Starter
        from ruse_studio.api import StudioApi
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            api = StudioApi(index_path=self.index, game_dir=self.game, home=home, instances=home / "copies",
                            starter=Starter(open_url=lambda url: None, start_game=lambda exe: None,
                                            steam_running=lambda: True, wait=lambda s: None))
            api.new_mod("Order")
            with missionsteps.PackStore(self.game) as store:
                ops = [(d, b.scenario_name + ".scenario") for d, bs in missionsteps.bindings(store).items()
                       for b in bs if b.kind == "operation" and b.has_file]
            for pack, file in ops:
                steps = api.mission_steps(pack, file, "us")
                if steps["menu"]["up"] is None:
                    break
            else:
                self.fail("no Operation can move up")
            before = [o["title"] for o in steps["menu"]["order"]]
            at = next(i for i, o in enumerate(steps["menu"]["order"]) if o["this"])
            self.assertFalse(steps["menu"]["mine"])
            groups = [o["group"] for o in steps["menu"]["order"]]
            self.assertEqual(groups, sorted(groups))  # the menu shows its groups from 0 up
            self.assertEqual(set(steps["menu"]["headings"]), {str(n) for n in groups})  # each under the game's words
            self.assertEqual(steps["menu"]["headings"]["1"], "1 vs 1")
            moved = api.mission_move(pack, file, -1, "us")
            target = home / "mods" / "order" / "menus.toml"
            self.assertTrue(target.is_file())
            self.assertTrue(moved["menu"]["mine"])
            self.assertTrue(moved["menu"]["order"][at - 1]["this"])
            after = [o["title"] for o in moved["menu"]["order"]]
            self.assertEqual(after[at - 1:at + 1], before[at - 1:at + 1][::-1])
            back = api.mission_order_reset(pack, file, "us")
            self.assertFalse(target.exists())
            self.assertEqual([o["title"] for o in back["menu"]["order"]], before)


if __name__ == "__main__":
    unittest.main()
