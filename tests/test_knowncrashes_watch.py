"""Our list of known crashes at a game the apps started (rusemod.bugwatch.GameWatch with rusemod.knowncrashes), and
the crash code a player without Bug Watch gets after a game the Launcher started crashed (rusemod.bugwatch.CodeWatch,
rusemod.crashcode).

The list is fetched while the game runs, only under version 5 of the agreement, from a fake of the Bug Watch server
(no network: test_knowncrashes.keep_off_the_network); with no list on the PC a crash of the game itself is told as
"couldn't check", and counted. The crash code: made on the PC from where the game stopped, told to the window, and
nothing counted, kept or sent.

Checked our_tools.json: crash_site.py, dump_survey.py, all_dump_rows.py and try_reader.py read real crash reports on
this PC for our research; none runs the apps' game watch on made-up ones. These tests read no program and no real
crash report: the made-up reports and program files are test_bugwatch's (Crashes, KnownCrashes), every number made up.
"""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import threading
import urllib.error
import unittest
from pathlib import Path
from unittest import mock

from rusemod import bugwatch, crashcode, home as homes, knowncrashes, net
import test_bugwatch as tb   # (the module, not its classes: their tests would run here a second time)
from test_knowncrashes import ListServer, MadeUp


class TheListAtAGame(tb.BugWatchTest):
    """GameWatch and our list of known crashes: fetched while the game runs (version 5), waited for at a crash,
    fetched once more when it failed, "couldn't check" without it, a list without this build counted, a report that
    can't be read costing only itself, and nothing of the list ever sent."""

    BASE, UNIT, OTHER = tb.KnownCrashes.BASE, tb.KnownCrashes.UNIT, tb.KnownCrashes.OTHER
    # (KnownCrashes' made-up reports and game, borrowed: plain functions, none of them calls super())
    accept, program, description, report, run_game = (tb.KnownCrashes.accept, tb.KnownCrashes.program,
                                                       tb.KnownCrashes.description, tb.KnownCrashes.report,
                                                       tb.KnownCrashes.run_game)

    def setUp(self):
        super().setUp()
        self.known = MadeUp.known()
        self.made = next(at for at, (key, _chain, _stack) in MadeUp.PLACES.items() if key == "made")
        self.create = MadeUp.CREATING[0] + 0x40    # in the list's unit-creation range (a call right before it)
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._notice = None

    def tearDown(self):
        bugwatch._notice = None
        super().tearDown()

    def made_report(self, **over) -> bytes:
        return self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)], **over).read_bytes()

    def crash_game(self, report: bytes, program, server=None):
        """run_game with no list kept, the list's address answered by `server` (net.urlopen's stand-in; offline
        when None)."""
        with mock.patch.object(net, "urlopen", server or ListServer(error=OSError("offline"))):
            return self.run_game(report, {"name": "Horse Squad", "added": True}, program, kept=False)

    def today(self) -> dict:
        return self.days[bugwatch._today()]

    def test_under_version_5_the_list_comes_while_the_game_runs(self):
        program = self.program([self.create])
        self.accept(5)
        server = ListServer(MadeUp.blob())
        sent, told, _ = self.crash_game(self.made_report(), program, server)
        self.assertEqual(told["notice"], {"why": "made", "unit": "Horse Squad", "added": True, "list": True})
        self.assertEqual([r.full_url for r in server.asked], [bugwatch.SERVER + knowncrashes.ROUTE])   # once
        self.assertEqual(sent["unit"], {"added": True})
        self.assertEqual(knowncrashes.load(self.home).n, 7)       # kept for the next game

    def test_with_no_list_a_crash_of_the_game_says_it_couldnt_check(self):
        """No list on the PC (before version 5 nothing is fetched): the player is told the Launcher couldn't check
        the crash, and it is counted; the crash report goes out as before, without the unit."""
        program = self.program([self.create])
        self.accept(4)
        sent, told, _ = self.crash_game(self.made_report(), program)
        self.assertEqual(told["notice"], {"why": None, "unit": None, "added": False, "list": False})
        self.assertEqual(self.today()["messages"]["crash_no_list"], 1)
        self.assertNotIn("unit", sent)
        self.assertEqual((sent["code"], sent["module"], sent["offset"]), ("0xc0000005", "RUSE.exe", hex(self.made)))
        self.assertIsNone(self.game_watch.refreshing)             # (nothing fetched under version 4)

    def test_offline_the_watch_fetches_once_more_at_the_crash_then_says_it(self):
        program = self.program([self.create])
        self.accept(5)
        server = ListServer(error=OSError("offline"))
        _sent, told, _ = self.crash_game(self.made_report(), program, server)
        self.assertEqual(told["notice"]["list"], False)
        self.assertEqual(len(server.asked), 2)                     # while the game ran, and once more at the crash
        messages = self.today()["messages"]
        self.assertEqual((messages["crashlist:offline"], messages["crash_no_list"]), (2, 1))

    def test_a_fetch_still_running_at_the_crash_is_waited_for(self):
        """The list is on its way when the game crashes: the watch waits for it (up to WAIT_AT_CRASH), and the
        crash is told with it; no second fetch."""
        program = self.program([self.create])
        self.accept(5)
        closed, answered = threading.Event(), []

        class Slow(ListServer):
            def __call__(self, req, timeout=None):
                closed.wait(10)                                    # (answers only once the game has closed)
                answered.append(True)
                return super().__call__(req, timeout)
        real_load = knowncrashes.load

        def load(home):                                            # the game closes: the list isn't there yet
            closed.set()
            return real_load(home)
        with mock.patch.object(knowncrashes, "load", load):
            _sent, told, _ = self.crash_game(self.made_report(), program, Slow(MadeUp.blob()))
        self.assertEqual((told["notice"]["why"], told["notice"]["list"]), ("made", True))
        self.assertEqual(answered, [True])

    def test_a_crash_elsewhere_with_no_list_tells_nothing(self):
        program = self.program([self.create])
        self.accept(4)
        sent, told, _ = self.crash_game(self.made_report(place=0x3000000), program)   # in no module the report lists
        self.assertIsNone(told["notice"])
        self.assertNotIn("crash_no_list", self.today()["messages"])
        self.assertEqual(sent["module"], "_")                      # (read_dump's "?", made safe)

    def two_crash_game(self, reports, read=None):
        """A game that closed leaving these crash reports (written in this order), watched with the list kept: its
        Watch. `read`: read_dump's stand-in."""
        local = self.home / "local"
        for i, report in enumerate(reports):
            dump = local / "Temp" / f"CrashRpt_{i}" / "report.dmp"
            dump.parent.mkdir(parents=True, exist_ok=True)
            dump.write_bytes(report)
            os.utime(dump, (1500 + i, 1500 + i))

        class Closed:
            def poll(self):
                return 0
        times = iter([1000.0, 1600.0])
        w = self.watch()
        MadeUp.keep(self.home)
        g = bugwatch.GameWatch(w, Closed(), [], 1, sleep=lambda _s: None, clock=lambda: next(times),
                               local=str(local), exe=self.program([self.create]), game=self.home / "game")
        with mock.patch.object(w, "send_waiting"), mock.patch.object(bugwatch, "unit_named", return_value=None), \
                mock.patch.object(bugwatch, "read_dump", read or bugwatch.read_dump):
            g.run()
        return w

    def test_a_list_without_this_builds_crashes_is_counted_once_a_game(self):
        self.accept(4)
        other = MadeUp.BUILD[:2] + (MadeUp.BUILD[2] + 1,)         # a new build of the game's program
        w = self.two_crash_game([self.made_report(build=other), self.made_report(build=other)])
        self.assertEqual(w.days[bugwatch._today()]["messages"]["crashlist:build-missing"], 1)
        self.assertIsNone(bugwatch.crash_notice()["notice"])      # (its places may be other code: nothing said)

    def test_a_report_that_cant_be_read_costs_only_itself(self):
        """Until 2026-11-25 an error other than a few while one crash report was read ended the watch: the game's
        minutes and every crash report were lost, and the player wasn't told."""
        self.accept(4)
        real, calls = bugwatch.read_dump, []

        def read(path, *args, **kwargs):
            calls.append(path)
            if len(calls) == 1:
                raise MemoryError("a report too big to read")
            return real(path, *args, **kwargs)
        w = self.two_crash_game([self.made_report(), self.made_report()], read=read)
        self.assertEqual(w.days[bugwatch._today()]["played"]["total"], 10)   # the game: recorded
        self.assertEqual(len(list(w.outbox.glob("crash-*.json"))), 1)        # the other report: read and kept
        self.assertEqual(bugwatch.crash_notice()["notice"]["why"], "made")   # and told

    def test_a_check_against_the_list_that_fails_is_counted_and_costs_only_the_notice(self):
        """Our own code failing on the list (a fault of ours, never the player's): no notice, the crash report sent as
        it would be without the list, and the failure counted ("crashlist:check-error"), never silent."""
        program = self.program([self.create])
        self.accept(4)
        with mock.patch.object(knowncrashes, "reason", side_effect=RuntimeError("our fault")):
            sent, told, _ = self.run_game(self.made_report(), {"name": "Horse Squad", "added": True}, program)
        self.assertIsNone(told["notice"])
        self.assertEqual(self.today()["messages"]["crashlist:check-error"], 1)
        self.assertEqual((sent["module"], "unit" in sent, "list_error" in sent), ("RUSE.exe", False, False))

    def test_a_failed_fetch_is_counted_by_its_kind(self):
        self.accept(5)

        class Closed:
            def poll(self):
                return 0
        w = self.watch()
        g = bugwatch.GameWatch(w, Closed(), [], 0, sleep=lambda _s: None, local=str(self.home / "none"))
        with mock.patch.object(net, "urlopen", ListServer(error=urllib.error.HTTPError("u", 503, "busy", {}, None))):
            g.run()
            g.refreshing.join(10)
        self.assertEqual(w.days[bugwatch._today()]["messages"]["crashlist:http-503"], 1)
        self.assertEqual(g.fetched, ["failed:http-503"])

    def test_nothing_of_the_list_goes_out(self):
        """What a crash report sends is what it sent with the table in the apps (the unit under version 4, when the
        list let it be read): never the list's number, the game program's build, the reason, or whether a list was
        there."""
        program = self.program([self.create])
        self.accept(4)
        with_list, _told, _ = self.run_game(self.made_report(), {"name": "Horse Squad", "added": True}, program)
        (self.home / bugwatch.FOLDER / knowncrashes.LIST_FILE).unlink()
        without, _told, _ = self.crash_game(self.made_report(), program)
        self.assertEqual(set(with_list) - set(without), {"unit"})
        self.assertEqual(set(without) - set(with_list), set())
        for body in (with_list, without):
            self.assertEqual({"build", "reason", "list", "list_error", "n", "unit_name", "unit_added"} & set(body),
                             set())
            self.assertNotIn(str(MadeUp.BUILD[1]), json.dumps(body))


class TheCrashCode(tb.BugWatchTest):
    """The owner, 2026-11-14: players without Bug Watch "should be given some sort of code that they can tell me that
    still tells us why it crashed, but maybe not be as specific if they don't select bug watch". After a game the
    Launcher started crashed: the code of where it stopped, told to the window once; nothing counted, kept or sent,
    and no server asked."""

    def setUp(self):
        super().setUp()
        bugwatch._notice = None
        self.accept(5)

    def tearDown(self):
        bugwatch._notice = None
        super().tearDown()

    BASE = tb.Crashes.BASE
    accept = tb.KnownCrashes.accept

    def stopped(self, place=0x4321, extra=b"") -> bytes:
        """A made-up crash report of the game's program stopping at `place` (and `extra` bytes after it)."""
        return tb.Crashes.dump_with_stack(self, [], [self.BASE + 0x1105], place=place, build=MadeUp.BUILD) + extra

    def code_game(self, *reports: bytes) -> dict:
        """A game that closed leaving `reports` (written in this order), watched by CodeWatch: what the window is
        told."""
        local = self.home / "local"
        for i, report in enumerate(reports):
            dump = local / "Temp" / f"CrashRpt_{i}" / "report.dmp"
            dump.parent.mkdir(parents=True, exist_ok=True)
            dump.write_bytes(report)
            os.utime(dump, (1500 + i, 1500 + i))

        class Closed:
            def poll(self):
                return 0
        times = iter([1000.0])
        bugwatch.CodeWatch(Closed(), sleep=lambda _s: None, clock=lambda: next(times), local=str(local)).run()
        return bugwatch.crash_notice()

    def code_of(self, report: bytes) -> str:
        path = self.home / "one.dmp"
        path.write_bytes(report)
        return crashcode.make(bugwatch.read_dump(path))

    def test_a_player_without_bug_watch_gets_a_code_and_nothing_else_happens(self):
        report = self.stopped()
        told = self.code_game(report)
        self.assertEqual(told, {"watching": False, "notice": {"code": self.code_of(report)}})
        self.assertEqual(crashcode.read(told["notice"]["code"])["offset"], 0x4321)   # where it stopped
        self.assertFalse((self.home / bugwatch.FOLDER).exists())  # nothing kept
        self.assertIsNone(bugwatch.crash_notice()["notice"])      # handed over once
        self.assertNotIn("bugwatch", homes.settings(self.home))   # Bug Watch left as it was: off

    def test_the_newest_report_gives_the_code(self):
        first, second = self.stopped(0x4321), self.stopped(0x5432)
        self.assertEqual(self.code_game(first, second)["notice"], {"code": self.code_of(second)})

    def test_a_cheat_copys_stop_is_no_crash_to_tell_us(self):
        """RUSE Guard stops a cheat copy taken into a multiplayer match (its marked lines in the report): no code."""
        stop = self.stopped(extra=b"\0RUSEGUARD-STOP multi 1 coop 0 local 0 RUSEGUARD-END\0")
        self.assertIsNone(self.code_game(stop)["notice"])
        self.assertIsNotNone(self.code_game(self.stopped())["notice"])   # (the control)

    def test_a_report_that_cant_be_read_costs_only_itself(self):
        real, calls = bugwatch.read_dump, []

        def read(path, *args, **kwargs):
            calls.append(path)
            if len(calls) == 1:
                raise MemoryError("a report too big to read")
            return real(path, *args, **kwargs)
        with mock.patch.object(bugwatch, "read_dump", read):
            told = self.code_game(self.stopped(0x4321), self.stopped(0x5432))
        self.assertEqual(crashcode.read(told["notice"]["code"])["offset"], 0x5432)

    def test_who_gets_a_crash_code(self):
        """The Launcher's player without Bug Watch who accepted version 5 (the version whose words say so); with Bug
        Watch on, GameWatch tells more; the Studio's page never asks."""
        launcher = bugwatch.Watch(self.home, "launcher", "0.4.8.22", opener=tb.Server())
        self.assertTrue(bugwatch.crash_code_watched(launcher))
        self.assertFalse(bugwatch.crash_code_watched(bugwatch.Watch(self.home, "studio", "0.9.8.22",
                                                                    opener=tb.Server())))
        self.assertFalse(bugwatch.crash_code_watched(None))
        self.accept(4)
        self.assertFalse(bugwatch.crash_code_watched(launcher))
        self.accept(5)
        bugwatch.turn_on(self.home, "Nick")
        self.assertFalse(bugwatch.crash_code_watched(launcher))


class ThePage(unittest.TestCase):
    """The Launcher page's crashText (app.js, run in Node with each language's words): a crash code, and a crash that
    couldn't be checked, each in its language with no blank left."""

    def test_the_two_new_lines_in_every_language(self):
        import shutil
        import subprocess
        import tempfile
        import tomllib
        from rusemod import schema
        node = os.environ.get("RUSE_NODE") or shutil.which("node") or next(
            (str(p) for p in sorted(Path("D:/RUSE-2.0/tools").glob("node-v*/node.exe"))[::-1]), None)
        if not node or not Path(node).is_file():
            self.skipTest("no Node")
        ui = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher"
        js = (ui / "ui" / "app.js").read_text(encoding="utf-8")

        def function(name: str) -> str:
            start = js.index(f"function {name}(")
            return js[start:js.index("\n}\n", start) + 2]
        words = tomllib.loads((ui / "words.toml").read_text(encoding="utf-8"))
        langs = sorted(schema.APP_LANGS)
        all_words = {lang: {k: v[lang] for k, v in words.items() if isinstance(v, dict) and lang in v} for lang in langs}
        code = crashcode.make({"code": "0xc0000005", "module": "RUSE.exe", "offset": "0x4321"})
        notices = [{"code": code}, {"why": None, "unit": None, "added": False, "list": False}]
        script = (function("fill") + function("crashText") + "const state = { words: null };\n"
                  f"const all = {json.dumps(all_words, ensure_ascii=False)};\n"
                  f"const notices = {json.dumps(notices)};\n"
                  "const out = {};\n"
                  "for (const lang of Object.keys(all)) { state.words = all[lang];"
                  " out[lang] = notices.map((n) => crashText(n)); }\n"
                  "console.log(JSON.stringify(out));\n")
        with tempfile.TemporaryDirectory(dir=os.environ.get("TEMP")) as d:
            f = Path(d) / "crash.js"
            f.write_text(script, encoding="utf-8")
            ran = subprocess.run([node, str(f)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(ran.returncode, 0, ran.stderr)
        said = json.loads(ran.stdout)
        for lang in langs:
            with_code, no_list = said[lang]
            self.assertIn(code, with_code, lang)
            self.assertEqual(with_code, words["crash_code"][lang].replace("{code}", code), lang)
            self.assertEqual(no_list, words["crash_no_list"][lang], lang)
            for text in (with_code, no_list):
                self.assertNotIn("{", text, lang)
                self.assertNotIn("undefined", text, lang)
            if lang != "us":
                self.assertNotEqual(no_list, words["crash_no_list"]["us"], lang)


if __name__ == "__main__":
    unittest.main()
