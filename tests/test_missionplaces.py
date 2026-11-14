"""How the build reads what a mission needs on its map (rusemod.missionplaces; the owner, 2026-11-13, items 31 and 32:
"It should be warning on every version if there's an error", and for a check of any mod whose map lacks places a
mission needs, "use your best judgment"), and the unit-model check for the units of a set made only of .rmod mods
(build.rmod_unit_models; item 29: "A"). On made-up files laid out like the game's (tests/test_buildchecks.py makes
them; no game files needed) and, with RUSE_GAME naming the game, on the real one read only: an .rmod made here is
applied in memory, nothing is written to the game, and nothing of the game is kept in the apps (the build reads it at
build time).

What a mission needs from its start: the zones (TagZoneDetection, found by name in its layout) that the units-in-zone
conditions on its start-up list (PostInit) watch; the game as sold misses none. What is said: only what the set adds,
and which change is why (the layout, the script, or the two together); a cluster pointing a chapter at a script that
watches nothing (as 1 VS 7 AI's does) leaves nothing to miss."""
import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_buildchecks import (BS, CLUSTER, DATA, ELSEWHERE, GLAD, GUIDS, IA, LAYOUT, LEIPZIG, OTHER_CLUSTER, REV, SCRIPT,
                              MadeUpGame, cluster, game_files, layout, menus, mission, rmod_text)
from rusemod import missionplaces as mp
from rusemod.build import BuildResult, rmod_unit_models
from rusemod.edat import Edat
from rusemod.pyscript import ScriptError
from rusemod.scenario import Scenario, ScenarioError


def readers(files: dict) -> tuple:
    def reader(members):
        low = {k.lower(): v for k, v in members.items()}
        return lambda member: low.get(member.replace("/", BS).lower())
    return tuple(reader(files[name]) for name in (GLAD, DATA, IA))


def changed(files: dict, pack: str, **members) -> dict:
    """`files` with members of `pack` replaced or added (layout, script, cluster or elsewhere = bytes)."""
    out = {k: dict(v) for k, v in files.items()}
    for key, data in members.items():
        out[pack][{"layout": LAYOUT, "script": SCRIPT, "cluster": CLUSTER, "elsewhere": ELSEWHERE}[key]] = data
    return out


class TheNames(unittest.TestCase):
    def test_the_packs_and_files_are_the_game_s(self):
        self.assertEqual((mp.GLAD, mp.DATA, mp.IA), (GLAD, DATA, IA))
        from rusemod.players import GLOBALS, MAPINFO
        from rusemod import fairplay
        self.assertEqual((mp.MAPINFO, mp.GLOBALS, mp.SCRIPT_ROOT), (MAPINFO, GLOBALS, fairplay.SCRIPT_ROOT))


class Scripts(unittest.TestCase):
    def test_the_zones_watched_from_the_start(self):
        self.assertEqual(mp.start_zones(mission(("Zone_A", "Zone_B"), later=("Zone_C",))), {"Zone_A", "Zone_B"})

    def test_a_zone_found_in_the_condition_itself(self):
        self.assertEqual(mp.start_zones(mission((), inline=("Zone_D",))), {"Zone_D"})

    def test_a_script_watching_nothing(self):
        self.assertEqual(mp.start_zones(mission(())), set())

    def test_what_isnt_a_script_is_said(self):
        with self.assertRaises(ScriptError):
            mp.start_zones(b"not a script at all")


class Layouts(unittest.TestCase):
    def test_its_listed_names(self):
        self.assertEqual(mp.place_names(layout("Zone_A", "Zone_B", hidden=("Gone",))), {"Zone_A", "Zone_B"})

    def test_bytes_after_the_design_items(self):
        raw = layout("Zone_A", tail=bytes(20))
        with self.assertRaises(ScenarioError):
            Scenario.read(raw)   # (our scenario reader refuses it, as it did two of the Balanced Realism Mod's)
        self.assertEqual(mp.place_names(raw), {"Zone_A"})

    def test_a_file_no_reader_takes_is_searched_as_text(self):
        self.assertIsNone(mp.place_names(b"garbage holding Zone_A"))
        self.assertEqual(mp._held(b"garbage holding Zone_A", {"Zone_A", "Zone_B"}), {"Zone_A"})
        self.assertEqual(mp._held(None, {"Zone_A"}), set())


class Missions(unittest.TestCase):
    def test_the_menus_a_mission_is_in(self):
        entries = [LEIPZIG, ("Challenge - Alpha", GUIDS["alpha"], "Patchable\\Scenario\\Alpha\\Scenario_BH\\ClusterMap",
                             "operation"),
                   ("(2) Alpha", GUIDS["battle"], "Patchable\\Scenario\\Alpha\\Scenario\\ClusterMap", "battles"),
                   ("M03_Italie_demo_final", GUIDS["tuto"], "Patchable\\Scenario\\Demo\\Scenario\\ClusterMap",
                    "tutorial"),
                   ("Never listed", GUIDS["unlisted"], "Patchable\\Scenario\\X\\Scenario\\ClusterMap", "unlisted")]
        mapinfo, globals_ = menus(entries)
        files = {mp.MAPINFO: mapinfo, mp.GLOBALS: globals_, CLUSTER: cluster(), OTHER_CLUSTER: cluster(),
                 BS.join(["genglad", "patchable", "scenario", "demo", "scenario", "clustermap.cpp.gladndfbin"]): cluster(),
                 BS.join(["genglad", "patchable", "scenario", "alpha", "scenario", "clustermap.cpp.gladndfbin"]): cluster()}
        got = mp.missions(readers({GLAD: files, DATA: {}, IA: {}})[0])
        self.assertEqual([(m.kind, m.name) for m in got], [("campaign", "M01_Leipzig"),
                                                           ("operation", "Challenge - Alpha"),
                                                           ("tutorial", "M03_Italie_demo_final")])   # BATTLES: no script
        self.assertEqual((got[0].cluster, got[0].layouts), (CLUSTER, (LAYOUT,)))
        self.assertEqual(got[0].scripts, (SCRIPT, SCRIPT.replace("effetmap.xyz", "effetmapmultiplayer.xyz")))

    def test_one_entry_in_two_menus_is_both(self):
        """1 VS 7 AI adds an Operation on the Ardennes chapter 1's own map-list entry."""
        mapinfo, _g = menus([LEIPZIG])
        _m, globals_ = menus([LEIPZIG, LEIPZIG[:3] + ("operation",)])
        got = mp.missions(readers({GLAD: {mp.MAPINFO: mapinfo, mp.GLOBALS: globals_, CLUSTER: cluster()},
                                   DATA: {}, IA: {}})[0])
        self.assertEqual([(m.kind, m.name) for m in got], [("campaign", "M01_Leipzig"), ("operation", "M01_Leipzig")])

    def test_no_menus_no_missions(self):
        self.assertEqual(mp.missions(lambda member: None), [])


class Check(unittest.TestCase):
    def setUp(self):
        self.shipped = game_files()

    def check(self, final):
        return mp.check(readers(final), readers(self.shipped))

    def test_the_game_as_shipped_isnt_looked_at(self):
        found = self.check(self.shipped)
        self.assertEqual((found.missing, found.unread), ([], []))

    def test_a_layout_without_a_zone_watched_from_the_start(self):
        found = self.check(changed(self.shipped, DATA, layout=layout("Zone_B", "Other")))
        [x] = found.missing
        self.assertEqual((x.mission.name, x.mission.kind, x.zones, x.layout, x.script, x.repointed),
                         ("M01_Leipzig", "campaign", ["Zone_A"], True, False, False))

    def test_a_layout_keeping_its_watched_zones(self):
        found = self.check(changed(self.shipped, DATA, layout=layout("Zone_A", "Brand_new")))
        self.assertEqual(found.missing, [])

    def test_a_zone_watched_later_isnt_said(self):
        shipped = game_files(scripts={SCRIPT: mission(("Zone_A",), later=("Zone_B",))})
        found = mp.check(readers(changed(shipped, DATA, layout=layout("Zone_A"))), readers(shipped))
        self.assertEqual(found.missing, [])

    def test_a_script_watching_a_zone_its_map_lacks(self):
        found = self.check(changed(self.shipped, IA, script=mission(("Zone_A", "Zone_Z"))))
        [x] = found.missing
        self.assertEqual((x.zones, x.layout, x.script), (["Zone_Z"], False, True))

    def test_a_script_changed_but_watching_what_its_map_has(self):
        """As the Campaign Red Zone Fix's 19 scripts: other code, the same zones."""
        found = self.check(changed(self.shipped, IA, script=mission(("Zone_B",), later=("Zone_Q",))))
        self.assertEqual(found.missing, [])

    def test_a_cluster_naming_a_script_that_watches_nothing(self):
        """As 1 VS 7 AI: the chapter's cluster names another folder, whose script (the mod's) watches no zone; its
        layout lacks the chapter's own zones, but nothing looks for them."""
        final = changed(self.shipped, GLAD,
                        cluster=cluster(folder="DataDir:\\Test\\map\\TwoIslands\\Scripting_challenge"))
        final = changed(final, IA, elsewhere=mission(()))
        final = changed(final, DATA, layout=layout("Some_battle_place"))
        self.assertEqual(self.check(final).missing, [])
        # ... and the same with the cluster naming the chapter's own folder again: found
        back = changed(final, GLAD, cluster=cluster())
        [x] = self.check(back).missing
        self.assertEqual((x.zones, x.layout, x.repointed), (["Zone_A"], True, False))

    def test_a_cluster_naming_another_layout(self):
        final = changed(self.shipped, GLAD,
                        cluster=cluster(layout_path="DataDir:\\Test\\Map\\M01_Leipzig\\Other.scenario"))
        final[DATA][BS.join(["test", "map", "m01_leipzig", "other.scenario"])] = layout("Nothing_named_so")
        [x] = self.check(final).missing
        self.assertEqual((x.zones, x.layout, x.script, x.repointed), (["Zone_A"], True, False, True))

    def test_only_what_the_set_adds(self):
        """A zone the mission as shipped lacks already isn't the set's doing."""
        shipped = game_files(scripts={SCRIPT: mission(("Zone_A", "Never_there"))})
        found = mp.check(readers(changed(shipped, DATA, layout=layout("Zone_B"))), readers(shipped))
        [x] = found.missing
        self.assertEqual(x.zones, ["Zone_A"])

    def test_only_the_two_together(self):
        """A layout without Zone_B (which the game's script doesn't watch) and a script watching Zone_B (which the
        game's layout has): each alone is fine, together the mission stops."""
        final = changed(self.shipped, DATA, layout=layout("Zone_A"))
        final = changed(final, IA, script=mission(("Zone_A", "Zone_B")))
        [x] = self.check(final).missing
        self.assertEqual((x.zones, x.layout, x.script), (["Zone_B"], True, True))

    def test_a_changed_script_that_cant_be_read(self):
        found = self.check(changed(self.shipped, IA, script=b"XYZ0 not a script"))
        self.assertEqual((found.missing, [(m.name, bool(why)) for m, why in found.unread]),
                         ([], [("M01_Leipzig", True)]))

    def test_a_changed_cluster_that_cant_be_read(self):
        found = self.check(changed(self.shipped, GLAD, cluster=b"not a cluster"))
        self.assertEqual((found.missing, [(m.name, why) for m, why in found.unread]),
                         ([], [("M01_Leipzig", "not an NDF binary")]))
        # the same cluster as shipped (the game's own, were one so): not the set's doing, not said
        broken = changed(self.shipped, GLAD, cluster=b"not a cluster")
        self.assertEqual(mp.check(readers(broken), readers(broken)).unread, [])

    def test_the_tutorial_and_an_operation(self):
        entries = [LEIPZIG[:3] + ("tutorial",), ("Challenge - Alpha", GUIDS["alpha"],
                                                  "Patchable\\Scenario\\Alpha\\Scenario_BH\\ClusterMap", "operation")]
        alpha_layout = BS.join(["test", "map", "alpha", "leveldesign_bh.scenario"])
        alpha_script = BS.join(["genpython", "1000", "test", "map", "alpha", "scripting_bh", "effetmap.xyz"])
        shipped = game_files(entries, layouts={LAYOUT: layout("Zone_A"), alpha_layout: layout("Zone_A")},
                             scripts={SCRIPT: mission(), alpha_script: mission()},
                             clusters={CLUSTER: cluster(), OTHER_CLUSTER: cluster(
                                 "DataDir:\\Test\\map\\Alpha\\LevelDesign_BH.scenario",
                                 "DataDir:\\Test\\map\\Alpha\\Scripting_BH")})
        final = {k: dict(v) for k, v in shipped.items()}
        final[DATA] = {LAYOUT: layout(), alpha_layout: layout()}
        found = mp.check(readers(final), readers(shipped))
        self.assertEqual([(x.mission.kind, x.mission.name) for x in found.missing],
                         [("tutorial", "M01_Leipzig"), ("operation", "Challenge - Alpha")])


class OnlyWarns(MadeUpGame):
    def test_the_copy_is_the_same_with_and_without_the_check(self):
        """The copy's files and its join code are those of the same build without the check: it only warns."""
        mod = self.rmod("Maps.rmod", "Map Pack", "1.0", {(DATA, "test/map/m01_leipzig/leveldesign.scenario"):
                                                         layout("A_battle_place")})
        warned, _ = self.build(mod, out="a")
        with mock.patch.object(mp, "check", return_value=mp.Found()):
            quiet, _ = self.build(mod, out="b")
        self.assertEqual(len(self.warnings(warned)), 1)
        self.assertEqual(self.warnings(quiet), [])
        self.assertEqual(warned.fingerprint, quiet.fingerprint)
        for pack in sorted(p.name for p in (self.root / "a").iterdir()):
            self.assertEqual((self.root / "a" / pack).read_bytes(), (self.root / "b" / pack).read_bytes(), pack)

    def test_menus_that_cant_be_read_are_a_note_and_the_build_goes_on(self):
        mod = self.rmod("Maps.rmod", "Map Pack", "1.0", {(DATA, "test/map/m01_leipzig/leveldesign.scenario"):
                                                         layout("A_battle_place")})
        with mock.patch.object(mp, "check", side_effect=ValueError("no OBJE section")):
            result, lines = self.build(mod)
        self.assertEqual((result.errors, self.warnings(result)), ([], []))
        self.assertIn("the places the missions watch from their start couldn't be checked: the menus or a mission's "
                      "files can't be read (no OBJE section)", [f.message for f in result.findings])
        self.assertTrue((self.root / "out" / DATA).is_file())

    def test_a_cluster_that_cant_be_read_is_a_note(self):
        """Not one mission left out without a word: the build says which it couldn't read, and goes on."""
        mod = self.rmod("Broken.rmod", "Broken", "1.0",
                        {(GLAD, "genglad/patchable/scenario/m01_leipzig/scenario/clustermap.cpp.gladndfbin"):
                         b"not a cluster"})
        result, _lines = self.build(mod)
        self.assertEqual((result.errors, self.warnings(result)), ([], []))
        self.assertIn("M01_Leipzig: a file of its mission can't be read (not an NDF binary), so whether its map holds "
                      "every place the mission watches from its start wasn't checked",
                      [f.message for f in result.findings])

    def test_a_script_that_cant_be_read_is_a_note(self):
        mod = self.rmod("Bad.rmod", "Bad Script", "1.0",
                        {(IA, "genpython/1000/test/map/m01_leipzig/scripting/effetmap.xyz"): b"XYZ0 not a script"})
        result, lines = self.build(mod)
        notes = [f.message for f in result.findings if f.level == "note" and "can't be read" in f.message]
        self.assertEqual(len(notes), 1, result.findings)
        self.assertTrue(notes[0].startswith("M01_Leipzig: a file of its mission can't be read ("), notes)
        self.assertTrue(any(line.startswith("  note") and "can't be read" in line for line in lines), lines)


# --- item 29: an .rmod-only set's units -----------------------------------------------------------------------------
class RmodUnits(unittest.TestCase):
    """The units of a set made only of .rmod mods get the unit-model check (the owner, item 29: "A")."""

    def world(self, change=None):
        """(the game as shipped, an engine run over the data as the mods leave it): test_unitcheck's army with the
        cluster maps whose loaders the check can force."""
        from test_unitcheck import LoadedEverywhere, army
        from rusemod.patch import Engine
        shipped = army()
        shipped.objects.update(copy.deepcopy(LoadedEverywhere.MAPS))
        final = army()
        final.objects.update(copy.deepcopy(LoadedEverywhere.MAPS))
        if change:
            change(final)
        return shipped, Engine(final).run([])

    def test_a_unit_moved_to_a_nation_without_its_model(self):
        from test_unitcheck import num, zz_win
        shipped, run = self.world(lambda g: g.objects["$/Panzer"].props.__setitem__("Nationalite", num(0)))
        result = BuildResult()
        self.assertTrue(rmod_unit_models(run, shipped, zz_win, result))
        self.assertEqual(result.errors, [])
        said = "\n".join(f.message for f in result.findings)
        # (said to a player, with no code names: the review of 95e9b910; its name made readable, no card here)
        self.assertIn("Panzer, in US's army, has a model of Germany's units", said)
        self.assertIn("Germany's unit models now load in every skirmish", said)

    def test_a_new_unit_with_another_nation_s_model(self):
        from test_unitcheck import num, zz_win

        def add(g):
            g.objects["$/Sherman_GER"] = copy.deepcopy(g.objects["$/Sherman"])
            g.objects["$/Sherman_GER"].props["Nationalite"] = num(1)
            g.objects["$/Sherman_GER"].props["DescriptorId"] = num(99, "uint32")
        shipped, run = self.world(add)
        result = BuildResult()
        self.assertTrue(rmod_unit_models(run, shipped, zz_win, result))
        self.assertIn("US's unit models now load in every skirmish", "\n".join(f.message for f in result.findings))

    def test_a_unit_changed_otherwise_is_left(self):
        """Its id changed, its nation and models as shipped: nothing to look at, ZZ_Win.dat not even opened."""
        from test_unitcheck import num
        shipped, run = self.world(lambda g: g.objects["$/Panzer"].props.__setitem__("DescriptorId", num(77, "uint32")))
        result, opened = BuildResult(), []
        self.assertFalse(rmod_unit_models(run, shipped, lambda: opened.append(1), result))
        self.assertEqual((result.findings, opened), ([], []))


# --- on the game itself ---------------------------------------------------------------------------------------------
GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None


@unittest.skipUnless(GAME is not None and (GAME / REV / IA).is_file(), "RUSE_GAME names no game folder")
class OnTheGame(unittest.TestCase):
    """The player's own game, read only: the check reads what the missions need from it at build time."""

    @classmethod
    def setUpClass(cls):
        from rusemod.build import find_pack
        cls.arcs = {name: Edat.open(str(find_pack(GAME, name))) for name in (GLAD, DATA, IA)}

    @classmethod
    def tearDownClass(cls):
        for a in cls.arcs.values():
            a.close()

    @staticmethod
    def reader(arc):
        def read(member):
            e = arc.entry(member)
            return bytes(arc.read(e)) if e is not None else None
        return read

    def shipped(self):
        return tuple(self.reader(self.arcs[n]) for n in (GLAD, DATA, IA))

    def test_the_game_as_sold_misses_none(self):
        """Every mission a player can pick holds every zone it watches from its start (read here, from the game)."""
        glad, data, ia = self.shipped()
        missions = mp.missions(glad)
        self.assertGreater(len([m for m in missions if m.kind == "campaign"]), 20)
        self.assertEqual(len([m for m in missions if m.kind == "tutorial"]), 1)
        watched = 0
        for m in missions:
            zones = set()
            for member in m.scripts:
                raw = ia(member)
                if raw is not None:
                    zones |= mp.start_zones(raw)
            watched += len(zones)
            self.assertEqual(mp._lacks(zones, [data(x) for x in m.layouts]), set(), m.name)
        self.assertGreater(watched, 100)
        self.assertEqual(mp.check(self.shipped(), self.shipped()).missing, [])

    def applied(self, files):
        """The game's three packs with an .rmod made here applied in memory (rusemod.rmod.apply, read only)."""
        from rusemod import rmod
        from rusemod.build import build_of, find_pack
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "Made.rmod")
            path.write_text(rmod_text("Made Here", "1.0", files), encoding="utf-8")
            run = rmod.apply(GAME, [path], build_of(GAME), say=lambda s: None)
        self.addCleanup(run.close)
        return tuple(self.reader(run.layered(find_pack(GAME, n)) or self.arcs[n]) for n in (GLAD, DATA, IA))

    def test_a_battle_layout_in_place_of_a_chapter_s(self):
        """What the Pinnacle Map Pack does: a BATTLES map's layout (no named place a chapter's script watches) in place
        of the first chapter's: any battle layout, any bytes."""
        for battle in ("test/map/alpha/leveldesign.scenario", "test/map/beta/leveldesign.scenario"):
            with self.subTest(battle):
                raw = self.shipped()[1](battle)
                final = self.applied({(DATA, "test/map/m01_leipzig/leveldesign.scenario"): raw})
                found = mp.check(final, self.shipped())
                self.assertEqual([(x.mission.kind, x.mission.name, x.layout, x.script) for x in found.missing],
                                 [("campaign", "M01_Leipzig", True, False)])
                self.assertTrue(found.missing[0].zones)

    def test_a_chapter_s_layout_with_a_place_more(self):
        """A mod that changes a chapter's layout but keeps its places isn't warned about."""
        s = Scenario.read(self.shipped()[1]("test/map/m01_leipzig/leveldesign.scenario"))
        s.add_place("CircularZone", 1000.0, 1000.0, name="Made_here", radius=500.0)
        final = self.applied({(DATA, "test/map/m01_leipzig/leveldesign.scenario"): s.to_bytes()})
        self.assertEqual(mp.check(final, self.shipped()).missing, [])


if __name__ == "__main__":
    unittest.main()
