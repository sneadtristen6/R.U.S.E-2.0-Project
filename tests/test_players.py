"""How many players a map takes (rusemod.players, maps/<map>/map.toml), on a made-up map list and menus laid out like
the game's: an entry (TMapLoadInfo) loads its scenario through its cluster, and its menu entry (TMultiMapInfo, the
same GUID) holds the count."""
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_ndf, val
from rusemod.ndf import Ndf
from rusemod.players import (GLOBALS, MAPINFO, Players, PlayersError, apply_players, entries, map_toml, parse_map,
                             renamed, seats)

BS = chr(92)


def s(i):
    return val(0x07, struct.pack("<I", i))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def i32(v):
    return val(0x02, struct.pack("<i", v))


def mapv(*pairs):
    return val(0x12, struct.pack("<I", len(pairs)) + b"".join(k + v for k, v in pairs))


GUID_A, GUID_B = bytes(range(16)), bytes(range(16, 32))


def glad(two_entries=False):
    """The members of a made-up ZZ_GladPatchableWin.dat: D-Day's entry "(6) Cotentin (3v3)" (6 players, two teams),
    optionally a second one on the same map, and the ClusterMap that names its scenario."""
    objects = [(0, [(0, s(0)), (1, s(1)), (2, val(0x1A, GUID_A)), (3, mapv((s(2), ref(2, 1))))]),
               (0, [(0, s(4)), (1, s(1)), (2, val(0x1A, GUID_B)), (3, mapv((s(2), ref(2, 1))))]),
               (1, [(4, ref(3, 2))]),
               (2, [(5, s(3))])]
    if not two_entries:
        objects[1] = (0, [(0, s(4)), (1, s(5)), (2, val(0x1A, GUID_B)), (3, mapv((s(2), ref(2, 1))))])
    mapinfo = make_ndf(
        objects=objects, classes=["TMapLoadInfo", "TClusterWithNDFLoadedSubCluster", "TNDFTransaction"],
        props=[("Name", 0), ("RootDatapackName", 0), ("GUID", 0), ("ClusterLoads", 0), ("NdfTransaction", 1),
               ("BaseName", 2)],
        strings=["(6) Cotentin (3v3)", "M04_cotentin", "Std",
                 BS.join(["Patchable", "Scenario", "M04_Cotentin", "Scenario_3v3", "ClusterMap"]),
                 "(2) Cotentin (1v1)", "OtherMap"])
    globals_ = make_ndf(
        objects=[(0, [(0, val(0x1A, GUID_A)), (1, i32(6)), (2, i32(2)), (3, i32(3)), (4, val(0x00, b"\x01"))]),
                 (0, [(0, val(0x1A, GUID_B)), (1, i32(2)), (3, i32(1)), (4, val(0x00, b"\x01"))])],
        classes=["TMultiMapInfo"],
        props=[("GUID", 0), ("NbPlayers", 0), ("CategoryId", 0), ("GameType", 0), ("DispoMulti2Teams", 0)])
    cluster = make_ndf(objects=[(0, [(0, s(0))])], classes=["TScenarioPath"], props=[("ScenarioPath", 0)],
                       strings=["DataDir:" + BS.join(["Test", "Map", "M04_Cotentin", "LevelDesign_3v3_v01.scenario"])])
    return {MAPINFO: mapinfo, GLOBALS: globals_,
            "genglad" + BS + BS.join(["patchable", "scenario", "m04_cotentin", "scenario_3v3", "clustermap"])
            + ".cpp.gladndfbin": cluster}


def reader(files):
    low = {k.lower(): v for k, v in files.items()}
    return lambda member: low.get(member.lower())


SIX = {1: {1, 2, 3}, 2: {1, 2, 3}, 3: {1}, 4: {1}}   # D-Day's 3v3: teams 1 and 2 in places 1-3, and some extra


class TheFile(unittest.TestCase):
    def test_map_toml(self):
        self.assertEqual(parse_map({"players": 8}), [Players(8)])
        self.assertEqual(parse_map({"players": 8, "entry": "(6) Cotentin (3v3)"}), [Players(8, "(6) Cotentin (3v3)")])
        self.assertEqual(parse_map({}), [])
        for bad, why in (({"players": 9}, "2 to 8"), ({"players": 1}, "2 to 8"), ({"players": "8"}, "whole number"),
                         ({"players": True}, "whole number"), ({"entry": "x"}, "players is missing"),
                         ({"players": 4, "entry": " "}, "map-list name")):
            with self.assertRaisesRegex(PlayersError, why):
                parse_map(bad)
        import tomllib
        self.assertEqual(parse_map(tomllib.loads(map_toml(Players(8, "(6) Cotentin (3v3)"), "made by hand"))),
                         [Players(8, "(6) Cotentin (3v3)")])

    def test_the_build_reads_it(self):
        from rusemod.build import BuildError, MAP_FILES, read_map_file
        self.assertIn("map.toml", MAP_FILES)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            f = folder / "maps" / "M04_cotentin" / "map.toml"
            f.parent.mkdir(parents=True)
            f.write_text("players = 8\n", encoding="utf-8")
            self.assertEqual(read_map_file(folder, f), [Players(8)])
            f.write_text("players = 8\ncolour = 3\n", encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "unknown key 'colour'"):
                read_map_file(folder, f)


class Seats(unittest.TestCase):
    def test_what_each_layout_needs(self):
        self.assertEqual(seats(SIX, [2], 6), [])
        self.assertEqual(seats(SIX, [2], 8), [(1, 4), (2, 4)])
        self.assertEqual(seats(SIX, [0], 4), [])  # free-for-all: place 1 of teams 1-4
        self.assertEqual(seats(SIX, [0], 6), [(5, 1), (6, 1)])
        self.assertEqual(seats(SIX, [3], 8), [])  # 8 players can't make 3 even teams: the game won't offer it
        self.assertEqual(seats(SIX, [2, 0], 8), [(1, 4), (2, 4), (5, 1), (6, 1), (7, 1), (8, 1)])

    def test_a_team_seats_as_many_as_it_has_starting_points(self):
        """The game takes a team's starting points lowest place first, whatever the places are: shipped maps seat
        every player with places 3 and 4 for team 2 ('(4) Beta'), places left out ('(4) Face a face 2v2 01') or two
        starts at one place; only the count per team matters (made-up teams shaped like those)."""
        from rusemod.scenario import Item, Scenario

        def start(team, place=None):
            return Item("StartingPoint", (0.0, 0.0, 0.0), 0.0,
                        {"AllianceNum": team, **({"AlliancePriority": place} if place is not None else {})})
        for shape, players, layouts in (([(1, 1), (1, 2), (2, 3), (2, 4)], 4, [2]),       # Beta's team 2
                                        ([(1, None), (1, None), (2, None), (2, None)], 4, [2]),  # no places
                                        ([(1, 1), (1, 1), (2, 2), (2, 2), (3, 1), (3, 1), (4, 1), (4, 1)], 8, [4]),
                                        ([(t, 1) for t in range(1, 9)], 8, [0])):
            s = Scenario(4, [], [start(t, p) for t, p in shape])
            self.assertEqual(seats(s.team_sizes(), layouts, players), [], shape)
        s = Scenario(4, [], [start(1, 1), start(1, 1), start(2, 1)])
        self.assertEqual(seats(s.team_sizes(), [2], 4), [(2, 2)])  # team 2's second start is missing
        self.assertEqual(seats({1: 2, 2: 2}, [2], 4), [])  # counts or collections

    def test_the_name_follows(self):
        self.assertEqual(renamed("(6) Cotentin (3v3)", 8, True), "(8) Cotentin (4v4)")
        self.assertEqual(renamed("(4) Robert (2vs2)", 8, True), "(8) Robert (4vs4)")
        self.assertEqual(renamed("(8) 8 Strateges", 6, False), "(6) 8 Strateges")
        self.assertEqual(renamed("Blitz", 4, False), "(4) Blitz")


class Applying(unittest.TestCase):
    def test_eight_players_on_a_two_team_map(self):
        files = glad()
        with self.assertRaisesRegex(PlayersError, "none for team 1, place 4, team 2, place 4"):
            apply_players(reader(files), "M04_cotentin", Players(8), lambda f: SIX)
        asked = []

        def eight(file):
            asked.append(file)
            return {1: {1, 2, 3, 4}, 2: {1, 2, 3, 4}}
        new, notes = apply_players(reader(files), "M04_cotentin", Players(8), eight)
        self.assertEqual(asked, ["leveldesign_3v3_v01.scenario"])  # the scenario its cluster names
        g, m = Ndf(new[GLOBALS]), Ndf(new[MAPINFO])
        (mi, gi, name), = entries(m, g, "M04_cotentin")
        p = {g.prop_name(pi): v.scalar() for pi, v in g.objects[gi].props if v.tc in (0x00, 0x02)}
        self.assertEqual((p["NbPlayers"], p["CategoryId"], p["GameType"]), (8, 3, 3))  # no 4v4 type: untested
        self.assertEqual(name, "(8) Cotentin (4v4)")
        self.assertIn("6 -> 8 players", notes[0])
        self.assertIn("its game type stays 3", notes[0])
        other = {g.prop_name(pi): v.scalar() for pi, v in g.objects[1].props if v.tc in (0x00, 0x02)}
        self.assertEqual(other["NbPlayers"], 2)  # the other map's entry is left alone

    def test_up_to_3v3_the_game_type_follows(self):
        new, _notes = apply_players(reader(glad()), "M04_cotentin", Players(4), lambda f: {1: 2, 2: 2})
        g = Ndf(new[GLOBALS])
        p = {g.prop_name(pi): v.scalar() for pi, v in g.objects[0].props if v.tc in (0x00, 0x02)}
        self.assertEqual(p["GameType"], 2)

    def test_three_teams_and_a_count_that_isnt_a_multiple_of_3_warns(self):
        files = glad()
        g = Ndf(files[GLOBALS])
        g.objects[0].props.append((g.add_prop("DispoMulti3Teams", 0), g.objects[0].props[-1][1]))
        files[GLOBALS] = g.to_member(compress=bool(g.flags & 0x80))
        said = []
        apply_players(reader(files), "M04_cotentin", Players(8), lambda f: {t: 4 for t in (1, 2, 3)}, said.append)
        self.assertEqual(len(said), 1)
        self.assertIn("8 players can't make three even teams", said[0])
        said.clear()
        apply_players(reader(files), "M04_cotentin", Players(6), lambda f: {t: 3 for t in (1, 2, 3)}, said.append)
        self.assertEqual(said, [])

    def test_two_players_drop_the_size_group(self):
        new, _notes = apply_players(reader(glad()), "M04_cotentin", Players(2), lambda f: SIX)
        g = Ndf(new[GLOBALS])
        names = [g.prop_name(pi) for pi, _v in g.objects[0].props]
        self.assertNotIn("CategoryId", names)  # as the shipped 2-player maps have it

    def test_which_entry(self):
        files = glad(two_entries=True)
        with self.assertRaisesRegex(PlayersError, "several entries.*entry ="):
            apply_players(reader(files), "M04_cotentin", Players(8), lambda f: {1: {1, 2, 3, 4}, 2: {1, 2, 3, 4}})
        with self.assertRaisesRegex(PlayersError, "no entry 'nope'"):
            apply_players(reader(files), "M04_cotentin", Players(8, "nope"), lambda f: SIX)
        new, notes = apply_players(reader(files), "M04_cotentin", Players(4, "(2) Cotentin (1v1)"),
                                   lambda f: {1: {1, 2}, 2: {1, 2}})
        self.assertIn("'(2) Cotentin (1v1)': 2 -> 4 players, named '(4) Cotentin (2v2)'", notes[0])
        with self.assertRaisesRegex(PlayersError, "isn't played online"):
            apply_players(reader(files), "Elsewhere", Players(4), lambda f: SIX)


if __name__ == "__main__":
    unittest.main()
