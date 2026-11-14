"""Scenarios: a player makes missions in the Studio's Maps tab, Scenario side (the Mission, Goals & events and Camera
moves trays: StudioApi.mission / mission_save / mission_delete), and sets a map's starting points and players: the usual
way and the unusual ones (a side a person plays handed to the computer, units of a nation the copied mission doesn't
load, a mission with no events, many events), on the made-up Operation of test_scenarios_maps_base. Each checks what
the page is told, the map's files, and whether the map still builds (Test in game).

FOR: the overnight scenario tests of map mods (owner, 2026-11-13). USED-BY: the release check of 0.9.8.20."""
import tomllib
import unittest

from test_scenarios_maps_base import BLITZ, MapGame, OperationGame, page_said
from rusemod.dic import Dic, name_to_key
from ruse_studio.api import StudioError

SCEN = "leveldesign_normal.scenario"
ENTRY = "(2) Blitz"   # the made-up Operation's map-list name
SHERMAN = "Unit_M4_Sherman"   # a unit's class, as mission_unit gives it for a unit picked in a spawn's list


class Missions(OperationGame):
    def setUp(self):
        super().setUp()
        self.pack = self.api.duplicate_map(BLITZ, "Op Twin", entry=ENTRY)["pack"]
        self.api.scenario_place(self.pack, SCEN, "Name", 1500.0, 1500.0)          # point_1
        self.api.scenario_place(self.pack, SCEN, "CircularZone", 2000.0, 2000.0)  # zone_1

    def draft(self, **more):
        """The mission as the page holds it after mission(): the file's table, with `more` tables added."""
        d = self.api.mission(self.pack)["mission"]
        d.update(more)
        return d

    def errors(self, view):
        return [msg for level, msg in view["problems"] if level == "error"]

    def file(self):
        return tomllib.loads((self.map_folder(self.pack) / "mission.toml").read_text(encoding="utf-8"))

    def test_a_mission_of_its_own_built(self):
        view = self.api.mission(self.pack)
        self.assertEqual((view["allowed"], view["kind"], view["exists"]), (True, "operation", False))
        self.assertEqual([(s["number"], s["player"], s["nation"]) for s in view["sides"]],
                         [(0, True, "US"), (1, False, "Germany")])
        self.assertEqual((view["points"], view["zones"]), (["point_1"], ["zone_1"]))
        goal = {"id": "reach", "text": {"us": "REACH THE ZONE", "fr": "ATTEIGNEZ LA ZONE"}, "done": "zone",
                "zone": "zone_1", "main": True}
        event = {"id": "coming", "when": "time", "at": 30,
                 "do": [{"do": "message", "text": "They are coming!"},
                        {"do": "spawn", "unit": SHERMAN, "count": 3, "side": 1, "at": "point_1", "group": "wave"},
                        {"do": "attack", "group": "wave", "target": "wave"}]}
        view = self.api.mission_save(self.pack, self.draft(goal=[goal], event=[event]))
        self.assertTrue(view["exists"])
        self.assertEqual(self.errors(view), [])
        self.assertEqual([g["id"] for g in self.file()["goal"]], ["reach"])
        got = self.assertBuilds()
        self.assertTrue(any("its own mission: 1 goal(s), 1 event(s), 0 camera move(s)" in ln for ln in got["lines"]),
                        got["lines"])
        self.game_untouched()

    def test_a_mission_with_no_events_and_no_goals(self):
        """Start a mission and leave it as it is: the sides only. The page says what's missing as warnings."""
        view = self.api.mission_save(self.pack, self.draft())
        self.assertTrue(view["exists"])
        self.assertEqual(self.errors(view), [])
        self.assertEqual(sorted(level for level, _m in view["problems"]), ["warning", "warning"])
        self.assertBuilds()

    def test_a_side_a_person_plays_handed_to_the_computer_is_refused(self):
        event = {"id": "handover", "when": "time", "at": 30, "do": [{"do": "ai", "side": 0}]}
        view = self.api.mission_save(self.pack, self.draft(event=[event]))
        self.assertEqual(len(self.errors(view)), 1)
        self.assertIn("side 0 is played by a person", self.errors(view)[0])
        got = self.build()
        self.assertEqual(got["state"], "failed")
        self.assertIn("side 0 is played by a person", " ".join(got["errors"]))
        computer = {"id": "handover", "when": "time", "at": 30, "do": [{"do": "ai", "side": 1}]}
        self.assertEqual(self.errors(self.api.mission_save(self.pack, self.draft(event=[computer]))), [])
        self.assertBuilds()

    def test_units_of_a_nation_the_copied_mission_doesnt_load(self):
        """The computer's side given Japan, and Japanese units made for it. (This made-up game has no nation packs to
        load or unit list to check the class against: the real install's dry build checks what the game would load.)"""
        side = [{"number": 0}, {"number": 1, "nation": "Japan"}]
        event = {"id": "landing", "when": "time", "at": 10,
                 "do": [{"do": "spawn", "unit": "Unit_Type97_ChiHa", "count": 2, "side": 1, "at": "point_1"}]}
        view = self.api.mission_save(self.pack, self.draft(side=side, event=[event]))
        self.assertEqual(self.errors(view), [])
        self.assertEqual(self.file()["side"][1]["nation"], "Japan")
        self.assertBuilds()

    def test_many_events(self):
        """200 events, the most a mission holds, saved and built; one more refused in words (said in English: F3)."""
        events = [{"id": f"wave{k}", "when": "time", "at": 10 + k, "do": [{"do": "message", "text": f"Wave {k}"}]}
                  for k in range(200)]
        view = self.api.mission_save(self.pack, self.draft(event=events))
        self.assertEqual(self.errors(view), [])
        self.assertEqual(len(self.file()["event"]), 200)
        got = self.assertBuilds()
        self.assertTrue(any("its own mission: 0 goal(s), 200 event(s)" in ln for ln in got["lines"]))
        more = events + [{"id": "wave200", "when": "time", "at": 300, "do": [{"do": "message", "text": "One more"}]}]
        self.assertIn("up to 200 [[event]] tables", page_said(self.api, "mission_save", self.pack, self.draft(event=more)))
        self.assertEqual(len(self.file()["event"]), 200)  # the file as it was

    def test_texts_in_every_language_and_odd_ones(self):
        text = {"us": 'Hold "the" line \\ now 🌙', "fr": "Tenez l'été", "ru": "Держитесь", "jpn": "持ちこたえろ",
                "sc": "坚守", "pol": "Łódź", "cz": "Příbram", "ger": "Straße", "ita": "Città", "spa": "Señor"}
        long = "x" * 2000   # (the page's text box takes up to 2000)
        goal = {"id": "hold", "text": text, "done": "time", "seconds": 120, "main": True}
        event = {"id": "talk", "when": "start", "do": [{"do": "message", "text": long}]}
        view = self.api.mission_save(self.pack, self.draft(goal=[goal], event=[event]))
        self.assertEqual(self.errors(view), [])
        self.assertBuilds()

    def test_a_goal_on_a_zone_taken_off_the_map_afterwards(self):
        goal = {"id": "reach", "text": "REACH", "done": "zone", "zone": "zone_1", "main": True}
        self.api.mission_save(self.pack, self.draft(goal=[goal]))
        self.api.scenario_remove_place(self.pack, 1)   # zone_1 (place 1) taken back
        view = self.api.mission(self.pack)
        self.assertTrue(any("zone_1" in e for e in self.errors(view)), view["problems"])
        got = self.build()
        self.assertEqual(got["state"], "failed")

    def test_the_mission_taken_out(self):
        self.api.mission_save(self.pack, self.draft())
        view = self.api.mission_delete(self.pack)
        self.assertFalse(view["exists"])
        self.assertFalse((self.map_folder(self.pack) / "mission.toml").exists())
        self.assertBuilds()

    def test_blank_terrain_on_the_operation(self):
        pack = self.api.duplicate_map(BLITZ, "Op Blank", entry=ENTRY, preset="blank_terrain")["pack"]
        self.assertTrue((self.map_folder(pack) / "mission.toml").is_file())
        self.assertTrue(self.api.mission(pack)["exists"])
        self.assertIn("Blank Ocean starts from a Battles map",
                      page_said(self.api, "duplicate_map", BLITZ, "Op Sea", ENTRY, "blank_ocean"))
        self.api.scenario_move(pack, SCEN, 0, 1200.0, 1200.0)   # its one HQ placed
        got = self.assertBuilds()
        self.assertIn("OPERATION > Op Blank ((2) Op Blank)", got["message"])


class MissionWords(MapGame):
    """What a player is told about missions on a BATTLES copy, in the Studio's language."""

    # FINDING F3: the Mission trays' refusals (StudioApi.mission_save, mission_unit) are rusemod.mission.MissionError,
    # not StudioError, so the window passes them to the page as they are: English in every language. The problems the
    # trays list (mission()["problems"]) are English too.
    @unittest.expectedFailure
    def test_f3_a_battles_copys_mission_refused_in_french(self):
        pack = self.api.duplicate_map(BLITZ, "Blitz at Dusk")["pack"]
        self.assertFalse(self.api.mission(pack)["allowed"])
        self.in_lang("fr")
        said = page_said(self.api, "mission_save", pack, {})
        self.assertTrue(said)
        self.assertNotIn("A BATTLES map can't have a mission of its own yet", said)

    # F3 too: Map Paint's own pictures refuse with rusemod.groundtex.TextureError, not StudioError: English as well.
    @unittest.expectedFailure
    def test_f3_a_ground_picture_with_no_map_changes_refused_in_french(self):
        self.in_lang("fr")
        said = page_said(self.api, "add_ground_picture", "grass", "data:image/png;base64,AAAA")
        self.assertTrue(said)
        self.assertNotIn("Pick or make a mod first: its pictures are kept in it.", said)

    def test_the_tray_says_why_in_its_own_words(self):
        pack = self.api.duplicate_map(BLITZ, "Blitz at Dusk")["pack"]
        self.assertEqual(self.api.mission(pack), {"allowed": False, "why": "mission_why_battles", "kind": "skirmish"})
        self.assertEqual(self.api.mission(BLITZ), {"allowed": False, "why": "mission_why_copy"})
        from ruse_studio.api import _words
        for key in ("mission_why_battles", "mission_why_copy"):
            self.assertEqual([lang for lang in ("us", "fr", "ger", "ru", "jpn", "fa") if not _words()[key].get(lang)],
                             [], key)


class StartsAndPlayers(MapGame):
    """Each player's HQ and how many players a map takes, on a BATTLES copy."""

    def setUp(self):
        super().setUp()
        self.pack = self.api.duplicate_map(BLITZ, "Blitz Four")["pack"]

    def test_more_players_than_starts(self):
        got = self.api.set_players(self.pack, 4)
        self.assertEqual((got["mod"], got["missing"]), (4, [[1, 1], [1, 2], [2, 2]]))
        b = self.build()
        self.assertEqual(b["state"], "failed")
        self.assertIn("4 players need a starting point for each", " ".join(b["errors"]))
        self.assertIn("none for team 1, place 1, team 1, place 2, team 2, place 2", " ".join(b["errors"]))
        for team, x in ((1, 600.0), (1, 900.0), (2, 2400.0)):
            self.api.scenario_add_start(self.pack, SCEN, team, x, 1500.0)
        self.assertEqual(self.api.map_players(self.pack)["missing"], [])
        self.assertBuilds()
        self.assertEqual(self.toml(self.pack)["players"], 4)

    def test_player_counts_the_lobby_cant_seat(self):
        for n in (0, 1, 9, -1):
            self.assertIn("players must be a whole number from 2 to 8", page_said(self.api, "set_players", self.pack, n))
        self.assertNotIn("players", self.toml(self.pack))

    def test_the_last_start_cant_be_taken_out(self):
        self.assertIn("every player needs one", page_said(self.api, "scenario_remove", self.pack, SCEN, [0]))

    def test_a_side_on_a_skirmish_map(self):
        self.assertIn("a skirmish game spawns only neutral items",
                      page_said(self.api, "scenario_spawn", self.pack, SCEN, "$/GFX/Everything/Descriptor_Unit_M4_Sherman",
                                1500.0, 1500.0, 1))


if __name__ == "__main__":
    unittest.main()
