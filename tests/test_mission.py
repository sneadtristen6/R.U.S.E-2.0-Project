"""A new Operation's or chapter's own mission (rusemod.mission, missionscript, missionbuild; MOD_FORMAT §8
mission.toml). The script is written the way Python 2.5 compiles it; the pinned bytes below were compared with Python
2.5.1's own compile of the same source, every field of every code object (2026-10-10), so a change to what's written
shows here even where no Python 2.5 is installed."""
import hashlib
import struct
import tomllib
import unittest

from fixtures import make_ndf, val
from rusemod import mission as M
from rusemod import missionbuild as MB
from rusemod.dic import name_to_key
from rusemod.missionscript import (ALLOWED, LOAD_NAME, WRITTEN_OPS, Attr, Long, Ref, assemble, call, check,
                                   instructions_used, source)
from rusemod.ndf import Ndf, sub_values
from rusemod.pyscript import Code, ScriptError, instructions, load

E = "_enum_for_game_play"


def tiny():
    imports = ["_enum_for_game_play", "leveldesign.descriptor", "leveldesign.launcheffetmap",
               "leveldesignsolo.descriptor"]
    defs = [
        ("W", call("leveldesign.descriptor.DescriptorWaitDuree", Duree=2.5)),
        ("H", call("leveldesignsolo.descriptor.DescriptorAfficheHint", Info=Long(995078763793236320), Pause=False,
                   Time=10)),
        ("S", call("leveldesign.descriptor.DescriptorSequential", Repeat=True, SubActions=[Ref("W"), Ref("H")])),
        ("ER", call("leveldesign.launcheffetmap.DescriptorLaunchEffetMap", CampList=[], CampaignInfo=None,
                    EffetMap=Ref("S"), GameRules=None, MapChapterPos=None, PostInit=[], TagList=[],
                    UnitToSpawnList=[], GameMode=Attr("_enum_for_game_play.TGameTimerMode.Clock"), Big=3000000000,
                    Neg=-1)),
    ]
    return imports, defs


FILENAME = "datadir:\\test\\map\\t\\scripting_mission\\effetmap.py"


class Script(unittest.TestCase):
    def test_written_as_python_2_5_compiles_it(self):
        imports, defs = tiny()
        data = assemble(imports, defs, "ER", FILENAME)
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         "42534681e4e22bd22db2da6030131a481bce1c68fc595d8ce849095f0a429ad0")
        mod = load(data)
        self.assertEqual((mod.flags, mod.name, mod.firstlineno), (0xE040, b"<module>", 1))
        launch = next(c for c in mod.consts if isinstance(c, Code))
        self.assertEqual((launch.name, launch.varnames, launch.flags), (b"launch", (b"leveldesign",), 0xE043))
        self.assertLessEqual(instructions_used(data), WRITTEN_OPS)
        self.assertIn(b"True", mod.names)  # Python 2's True and False are names
        self.assertIn(995078763793236320, mod.consts)  # a text key: a long
        self.assertIn(3000000000, mod.consts)
        self.assertIn(-1, mod.consts)

    def test_none_is_the_constant_unless_a_statement_is_long(self):
        """Python 2.5's optimiser turns the name None into the constant, but leaves a code object alone when one
        statement's code is over 255 bytes (its line table then holds a 255)."""
        imports, defs = tiny()
        mod = load(assemble(imports, defs, "ER", FILENAME))
        none = mod.names.index(b"None")
        self.assertFalse([1 for _a, op, arg in instructions(mod.code) if op == LOAD_NAME and arg == none])
        many = {f"K{i}": i for i in range(60)}  # one long statement
        defs.insert(0, ("LONG", call("leveldesign.descriptor.DescriptorWaitDuree", X=None, **many)))
        mod = load(assemble(imports, defs, "ER", FILENAME))
        self.assertIn(255, mod.lnotab)
        none = mod.names.index(b"None")
        self.assertTrue([1 for _a, op, arg in instructions(mod.code) if op == LOAD_NAME and arg == none])

    def test_source_is_the_same_mission(self):
        imports, defs = tiny()
        text = source(imports, defs, "ER")
        self.assertIn("W = leveldesign.descriptor.DescriptorWaitDuree(Duree=2.5)", text)
        self.assertIn("Info=995078763793236320L", text)
        self.assertTrue(text.endswith("    return leveldesign.launcher.launch(ER)\n"))

    def test_only_the_allowed_blocks_and_plain_values(self):
        imports, defs = tiny()
        for bad in (call("os.system", "x"), call("leveldesign.descriptor.DescriptorWaitDuree", Duree=Ref("NOPE")),
                    call("leveldesign.descriptor.DescriptorWaitDuree", Duree=Attr("os.environ")),
                    call("leveldesignsolo.descriptor.DescriptorAfficheHint", Info="café"),
                    call("leveldesign.descriptor.DescriptorWaitDuree", Duree={"a": 1})):
            with self.subTest(bad=bad), self.assertRaises(ScriptError):
                check(imports, [("BAD", bad)] + defs, "ER")
        with self.assertRaises(ScriptError):
            check(imports, defs + [("launch", call("leveldesign.descriptor.DescriptorWaitDuree", Duree=1))], "ER")
        with self.assertRaises(ScriptError):
            check(imports, defs, "NOT_MADE")


SAMPLE = '''
[mission]
time_limit = 30
time_up = "defeat"
opening = "Flyby"

[[side]]
number = 0
money = 250

[[side]]
number = 1
nation = "Germany"
difficulty = "hard"
plays = "ai"

[[goal]]
id = "reach"
text = { us = "DRIVE INTO THE CIRCLE", fr = "ENTREZ DANS LE CERCLE" }
done = "zone"
zone = "Circle"
marker = "Mark"

[[goal]]
id = "counter"
text = "DESTROY THE COUNTER-ATTACK"
done = "destroyed"
group = "wave"
start = "event"

[[event]]
id = "entered"
when = "goal"
goal = "reach"
do = [
  { do = "message", text = "Coming!" },
  { do = "spawn", unit = "Unit_M4_Sherman", count = 3, side = 1, at = "From", group = "wave" },
  { do = "goal", goal = "counter" },
  { do = "attack", group = "wave", target = "wave" },
]

[[event]]
id = "waves"
when = "time"
at = 60
repeat = 90
do = [{ do = "message", text = "Again" }]

[[camera]]
name = "Flyby"
seconds = 12
points = [[0, 0, 50000], [100000, 0, 40000]]
look = [50000, 50000, 0]
'''


def base():
    camps = [("P", 0, "leveldesign.camps.VariableCamp",
              {"Alliance": 1, "NiveauIA": Attr(f"{E}.NiveauIA.Player"), "Nationalite": Attr(f"{E}.Nationalite.EU"),
               "CampNumber": -1}, True),
             ("C", 1, "leveldesign.camps.VariableCamp",
              {"Alliance": 2, "NiveauIA": Attr(f"{E}.NiveauIA.Scripted"), "Nationalite": Attr(f"{E}.Nationalite.Italie"),
               "CampNumber": -1, "LocalizedName": Ref("B_N")}, False)]
    support = [("N", call("leveldesign.camps.LocalizedCampName", AllianceName=Long(5), TeamName=Long(6)))]
    return M.Base(camps, support, None, False)


def ctx(**more):
    c = M.Context("Test", "operation", {"Mark", "From"}, {"Circle"}, set(), {"Warmup"}, {}, None)
    for k, v in more.items():
        setattr(c, k, v)
    return c


class MissionFile(unittest.TestCase):
    def test_reads_and_writes_back(self):
        m = M.parse(tomllib.loads(SAMPLE))
        self.assertEqual((m.time_limit, m.opening, len(m.sides), len(m.goals), len(m.events), len(m.cameras)),
                         (30, "Flyby", 2, 2, 2, 1))
        self.assertEqual(m.goals[0].text.get("fr"), "ENTREZ DANS LE CERCLE")
        self.assertEqual(m.goals[0].text.get("ger"), "DRIVE INTO THE CIRCLE")  # a language left out: the English
        self.assertEqual([a.do for a in m.events[0].actions], ["message", "spawn", "goal", "attack"])
        again = M.parse(tomllib.loads(M.to_toml(m, "a header")))
        self.assertEqual(M.to_toml(again), M.to_toml(m))

    def test_says_what_to_change(self):
        for text, said in (('[mission]\nspeed = 2', "unknown key 'speed'"),
                           ('[[goal]]\nid = "a"\ntext = "x"\ndone = "maybe"', "done must be one of"),
                           ('[[goal]]\nid = "a"\ntext = "x"\ndone = "zone"', "zone"),
                           ('[[event]]\nid = "a"\nwhen = "zone"\nzone = "Z"\nrepeat = 30', "repeat is for"),
                           ('[[event]]\nid = "a"\nwhen = "start"\ndo = [{ do = "fly" }]', "do must be one of"),
                           ('[[event]]\nid = "a"\nwhen = "start"\ndo = [{ do = "spawn", unit = "U" }]', "needs at"),
                           ('[[goal]]\nid = "a"\ntext = "x"\nzone = "Z"\n[[event]]\nid = "a"\nwhen = "start"',
                            "used twice"),
                           ('[[camera]]\nname = "C"\npoints = [[0, 0, 0]]\nlook = [0, 0, 0]', "2 to"),
                           ('[[side]]\nnumber = 0\nplays = "everyone"', "plays must be one of"),
                           ('[[goal]]\nid = "a"\ntext = { us = "x", xx = "y" }\nzone = "Z"', "languages")):
            with self.subTest(text=text), self.assertRaises(M.MissionError) as c:
                M.parse(tomllib.loads(text))
            self.assertIn(said, str(c.exception))

    def test_checks_against_the_map_and_the_copied_mission(self):
        m = M.parse(tomllib.loads(SAMPLE))
        self.assertEqual([p for p in M.problems(m, base(), ctx()) if p[0] == "error"], [])
        bad = M.parse(tomllib.loads(SAMPLE.replace('zone = "Circle"', 'zone = "Nowhere"')
                                    .replace('target = "wave"', 'target = "ghosts"')))
        errors = [msg for level, msg in M.problems(bad, base(), ctx()) if level == "error"]
        self.assertTrue(any("'Nowhere' isn't a zone" in e for e in errors))
        self.assertTrue(any("group 'ghosts'" in e for e in errors))
        player = M.parse(tomllib.loads(SAMPLE.replace('number = 1\nnation', 'number = 0\nnation')
                                       .replace('[[side]]\nnumber = 0\nmoney = 250\n', '')))
        self.assertTrue(any("played by a person" in msg for _l, msg in M.problems(player, base(), ctx())))
        unknown = M.problems(m, base(), ctx(classes={"Unit_Other"}))
        self.assertTrue(any("isn't a unit class the game knows" in msg for _l, msg in unknown))


class MissionScript(unittest.TestCase):
    def setUp(self):
        self.m = M.parse(tomllib.loads(SAMPLE))
        self.imports, self.defs, self.launch = M.script(self.m, base(), ctx(), name_to_key)
        self.text = source(self.imports, self.defs, self.launch)

    def test_assembles_with_only_the_allowed_blocks(self):
        data = assemble(self.imports, self.defs, self.launch, FILENAME)
        self.assertLessEqual(instructions_used(data), WRITTEN_OPS)

    def test_the_goals_panel_opens_a_second_after_the_goals_start(self):
        """An Operation's goals panel holds Escape until it's closed, and lists only the goals already going (T41's
        Escape lock): the panel shows a second after the start goals, never before."""
        names = dict(self.defs)
        self.assertIn("ObjectifsList=[GOAL_G0_reach]", source([], [("P", names["PANEL"])], "P").splitlines()[0])
        main = names["MAIN"]
        sim = dict(main.kwargs)["SubActions"][1]
        parts = dict(sim.kwargs)["SubActions"]
        self.assertEqual(parts[0], Ref("RUN_G0_reach"))
        self.assertEqual(parts[1], Ref("PANEL_AFTER"))
        self.assertIn("DescriptorPlayEffetAfterWait(Action=PANEL, Duree=1)", self.text)

    def test_the_computer_side_block_comes_from_strategic_ia(self):
        """DescriptorIAAll lives in leveldesignsolo.strategic_ia (Fortress Europa imports it
        so). T45 named leveldesignsolo.camps and the mission stopped on the script error (2026-10-10)."""
        self.assertIn("import leveldesignsolo.strategic_ia", self.text)
        self.assertIn("leveldesignsolo.strategic_ia.DescriptorIAAll(Camp=SIDE_1)", self.text)
        self.assertNotIn("DescriptorIAAll", ALLOWED["leveldesignsolo.camps"])

    def test_sides_rules_events_and_cameras(self):
        t = self.text
        self.assertIn("Nationalite=_enum_for_game_play.Nationalite.Allemagne", t)
        self.assertIn("DescriptorIAAll(Camp=SIDE_1)", t)                   # plays = "ai"
        self.assertIn("DescriptorSetRessourceCamp(Camp=SIDE_0, Quantite=250)", t)
        self.assertIn("GameTime=1815", t)                                    # 30 minutes, and 15 s
        self.assertIn("CameraPathName='Flyby'", t)
        self.assertIn("DescriptorSequential(Repeat=True", t)                # the repeating event
        self.assertIn("DescriptorDeclencheVictoireChallenge()", t)          # an Operation's victory
        self.assertIn("TagZoneDetection('Circle')", t)
        self.assertIn("LocalizedName=B_N", t)                               # the copied side's name, kept
        entered = dict(self.defs)["EVENT_E0_entered"]
        acts = dict(entered.kwargs)["SubActions"]
        # the goal shown runs beside the rest: the attack doesn't wait for the goal to be done
        self.assertEqual(acts[-1].func, "leveldesign.descriptor.DescriptorSimultaneous")

    def test_a_chapter_wins_with_its_own_victory(self):
        imports, defs, launch = M.script(self.m, base(), ctx(kind="campaign"), name_to_key)
        text = source(imports, defs, launch)
        self.assertIn("DescriptorDeclencheVictoire(Chapter=1, DeclencheCredits=False, IdMapSoloForLadder=-1)", text)
        self.assertIn("MapChapterPos=CHPOS", text)

    def test_texts_have_keys_the_game_takes(self):
        words = M.texts(self.m, "Test")
        self.assertEqual(len(words), 4)
        for name in words:
            self.assertEqual(len(name), 10)
            name_to_key(name)  # (raises if the game couldn't take it)
        self.assertEqual(M.text_key_name("Test", "G_reach"), M.text_key_name("test", "G_reach"))


class PlacedGroups(unittest.TestCase):
    """A unit placed on the map (scenario.toml) can join a group of the map's mission: the scenario pass names its
    design item MG_<group>_<n> and the mission gathers it by that name (TagUnit, as T30's fleet: proven)."""

    def test_named_the_same_way_by_both(self):
        from rusemod import scenario as S
        rows = S.parse_spawns([
            {"file": "a.scenario", "what": "Unit_M4_Sherman", "x": 1, "y": 2, "camp": 1, "group": "column"},
            {"file": "a.scenario", "what": "Unit_M4_Sherman", "x": 3, "y": 4, "camp": 1},
            {"file": "b.scenario", "what": "Unit_M4_Sherman", "x": 5, "y": 6, "group": "column"},
            {"file": "a.scenario", "what": "Unit_M10", "x": 7, "y": 8, "camp": 1, "group": "column"}])
        self.assertEqual(S.group_names(rows), ["MG_column_1", None, "MG_column_1", "MG_column_2"])
        self.assertEqual(S.placed_groups(rows, "A.scenario"), {"column": ["MG_column_1", "MG_column_2"]})
        back = S.parse_spawns(tomllib.loads(S.spawns_toml(rows))["spawn"])
        self.assertEqual([s.group for s in back], ["column", None, "column", "column"])
        with self.assertRaises(S.ScenarioError):
            S.parse_spawns([{"file": "a.scenario", "what": "Unit_M10", "x": 1, "y": 1, "group": "no spaces"}])

    def test_the_mission_gathers_them(self):
        m = M.parse(tomllib.loads(SAMPLE.replace('group = "wave"\nstart = "event"', 'group = "fleet"\nstart = "event"')))
        c = ctx(placed={"fleet": ["MG_fleet_1", "MG_fleet_2"]})
        self.assertFalse([p for p in M.problems(m, base(), c) if "fleet" in p[1]])
        imports, defs, launch = M.script(m, base(), c, name_to_key)
        text = source(imports, defs, launch)
        self.assertIn("U_MG_fleet_1 = leveldesignsolo.helper.TagUnit('MG_fleet_1')", text)
        self.assertIn("VariableUnitGroup(UnitList=[U_MG_fleet_1, U_MG_fleet_2])", text)


def camera_file() -> bytes:
    classes = ["TCameraPath", "TCameraPathKey"]
    props = [("PositionKeyVector", 0), ("DirectionKeyVector", 0), ("Name", 0), ("Coord", 1)]

    def ref(i, cls):
        return struct.pack("<I", 0x09) + struct.pack("<III", 0xBBBBBBBB, i, cls)

    def lst(items):
        return val(0x11, struct.pack("<I", len(items)) + b"".join(items))
    path = (0, [(0, lst([ref(1, 1), ref(2, 1)])), (1, lst([ref(3, 1), ref(4, 1)])), (2, val(0x07, struct.pack("<I", 0)))])
    keys = [(1, [(3, val(0x0B, struct.pack("<3f", float(i), 0.0, 1.0)))]) for i in range(4)]
    return make_ndf([path] + keys, classes, props, strings=["Warmup"], topo=[0])


class CameraFile(unittest.TestCase):
    def test_a_new_path_is_listed_in_the_topo_table(self):
        """The game makes only the objects the TOPO table lists; T41's own path,
        left out of it, never played."""
        cam = M.Camera("Flyby", [(0.0, 0.0, 50000.0), (100000.0, 0.0, 40000.0), (100000.0, 100000.0, 30000.0)],
                       (50000.0, 50000.0, 0.0), 12.0)
        out = MB.with_cameras(camera_file(), [cam])
        nd = Ndf(out)
        self.assertEqual(MB.camera_paths(out), ["Warmup", "Flyby"])
        self.assertEqual(nd.topo, [0, 5])
        fly = nd.objects[5]
        refs = sub_values({nd.prop_name(pi): v for pi, v in fly.props}["DirectionKeyVector"])
        first = nd.objects[struct.unpack_from("<I", refs[0].payload, 4)[0]]
        d = struct.unpack("<3f", bytes(first.props[0][1].payload)[:12])
        self.assertAlmostEqual(sum(v * v for v in d), 1.0, places=5)  # a unit direction, towards the look spot
        with self.assertRaises(MB.MissionBuildError):
            MB.with_cameras(camera_file(), [M.Camera("Warmup", cam.points, cam.look)])


if __name__ == "__main__":
    unittest.main()
