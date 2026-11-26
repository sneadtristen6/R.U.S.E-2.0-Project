"""Our list of known crashes at a game the apps started (rusemod.bugwatch.GameWatch with rusemod.knowncrashes), and
the crash code every player gets after a game the Launcher started crashed, Bug Watch on or off (rusemod.crashcode;
with it off rusemod.bugwatch.CodeWatch, with it on GameWatch's notice), and the Launcher page's crash notice with its
Copy code button and its GitHub link (app.js sayCrash, run in Node).

The list is fetched while the game runs, only under version 5 of the agreement, from a fake of the Bug Watch server
(no network: test_knowncrashes.keep_off_the_network); with no list on the PC a crash of the game itself is told as
"couldn't check", and counted. The crash code: made on the PC from where the game stopped, told to the window, and
nothing more counted, kept or sent for it.

These tests read no program and no real
crash report: the made-up reports and program files are test_bugwatch's (Crashes, KnownCrashes), every number made up.
"""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import threading
import time
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
        code = told["notice"].pop("code")   # (the Studio's watch: the crash code too, the owner's "13, yes")
        self.assertEqual(crashcode.read(code)["module"], "game")
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
        """The Launcher's player who accepted version 5 (the version whose words say so), Bug Watch on or off (the
        owner, 2026-11-26: every player); a CodeWatch only with Bug Watch off (with it on, GameWatch gives the same code
        with what it tells more); the Studio's player too, after a Test in game (the owner's "13, yes", 2026-11-26)."""
        launcher = bugwatch.Watch(self.home, "launcher", "0.4.8.22", opener=tb.Server())
        studio = bugwatch.Watch(self.home, "studio", "0.9.8.22", opener=tb.Server())
        self.assertTrue(bugwatch.crash_code_watched(launcher))
        self.assertTrue(bugwatch.crash_code_given(launcher))
        self.assertTrue(bugwatch.crash_code_watched(studio))
        self.assertTrue(bugwatch.crash_code_given(studio))
        self.assertFalse(bugwatch.crash_code_watched(None))
        self.assertFalse(bugwatch.crash_code_given(None))
        self.accept(4)
        self.assertFalse(bugwatch.crash_code_watched(launcher))
        self.assertFalse(bugwatch.crash_code_given(launcher))
        self.accept(5)
        bugwatch.turn_on(self.home, "Nick")
        self.assertFalse(bugwatch.crash_code_watched(launcher))   # (GameWatch watches the game)
        self.assertTrue(bugwatch.crash_code_given(launcher))      # and gives the code
        self.assertTrue(bugwatch.crash_code_given(studio))
        self.assertFalse(bugwatch.crash_code_watched(studio))


class TheCodeWithBugWatchOn(tb.BugWatchTest):
    """The owner, 2026-11-26 (v5/QUESTIONS-ROUND2-DRAFT.md, "HIS CRASH NOTICE"): "Maybe we need to make some sort of
    notice so that these players, when their mod crashes, it's like, hey, send this report to me on either GitHub or
    Discord. ... And then be like, copy code."; settled as every player after a crash of a game the Launcher started,
    Bug Watch on or off. With Bug Watch on, GameWatch's notice carries the same code CodeWatch gives, under the unit's
    line or alone, under version 5 only, for the Launcher and the Studio (the owner's "13, yes"); what Bug Watch keeps and sends doesn't change."""

    BASE, UNIT = tb.KnownCrashes.BASE, tb.KnownCrashes.UNIT
    # (KnownCrashes' made-up reports and game, borrowed as TheListAtAGame borrows them; run_game asks self.watch())
    accept, program, description, report, run_game = (tb.KnownCrashes.accept, tb.KnownCrashes.program,
                                                       tb.KnownCrashes.description, tb.KnownCrashes.report,
                                                       tb.KnownCrashes.run_game)

    def setUp(self):
        super().setUp()
        self.made = next(at for at, (key, _chain, _stack) in MadeUp.PLACES.items() if key == "made")
        self.create = MadeUp.CREATING[0] + 0x40
        self.app = "launcher"
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._notice = None

    def tearDown(self):
        bugwatch._notice = None
        super().tearDown()

    def watch(self, server=None, clock=time.time):
        """The app's Watch, as its window starts it: the Launcher's (self.app)."""
        return bugwatch.Watch(self.home, self.app, "0.4.8.22", opener=server or tb.Server(), clock=clock)

    def made_report(self, **over) -> bytes:
        return self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)], **over).read_bytes()

    def code_of(self, report: bytes) -> str:
        """The code a player without Bug Watch gets for `report` (CodeWatch reads it so)."""
        path = self.home / "one.dmp"
        path.write_bytes(report)
        return crashcode.make(bugwatch.read_dump(path))

    def test_a_crash_we_know_tells_its_code_too(self):
        program = self.program([self.create])
        self.accept(5)
        report = self.made_report()
        _sent, told, _ = self.run_game(report, {"name": "Horse Squad", "added": True}, program)
        self.assertEqual(told["notice"], {"why": "made", "unit": "Horse Squad", "added": True, "list": True,
                                          "code": self.code_of(report)})
        self.assertEqual(crashcode.read(told["notice"]["code"])["module"], "game")
        self.assertIsNone(bugwatch.crash_notice()["notice"])      # handed over once

    def test_the_code_is_the_one_a_player_without_bug_watch_gets(self):
        """The same crash report, read by CodeWatch (Bug Watch off) and by GameWatch (on): the same code."""
        program = self.program([self.create])
        self.accept(5)
        report = self.made_report()
        local = self.home / "off"
        dump = local / "Temp" / "CrashRpt_0" / "report.dmp"
        dump.parent.mkdir(parents=True, exist_ok=True)
        dump.write_bytes(report)
        os.utime(dump, (1500, 1500))

        class Closed:
            def poll(self):
                return 0
        times = iter([1000.0])
        bugwatch.CodeWatch(Closed(), sleep=lambda _s: None, clock=lambda: next(times), local=str(local)).run()
        without = bugwatch.crash_notice()["notice"]["code"]
        _sent, told, _ = self.run_game(report, {"name": "Horse Squad", "added": True}, program)
        self.assertEqual(told["notice"]["code"], without)

    def test_a_crash_we_dont_know_tells_its_code_alone(self):
        """Before 2026-11-26 a crash not on our list told a Bug Watch player nothing."""
        program = self.program([self.create])
        self.accept(5)
        report = self.made_report(place=0x4321)
        _sent, told, _ = self.run_game(report, {"name": "Horse Squad", "added": True}, program)
        self.assertEqual(told["notice"], {"code": self.code_of(report)})
        self.assertEqual(crashcode.read(told["notice"]["code"])["offset"], 0x4321)

    def test_with_no_list_the_code_comes_under_couldnt_check(self):
        program = self.program([self.create])
        self.accept(5)
        report = self.made_report()
        with mock.patch.object(net, "urlopen", ListServer(error=OSError("offline"))):
            _sent, told, _ = self.run_game(report, {"name": "Horse Squad", "added": True}, program, kept=False)
        self.assertEqual(told["notice"], {"why": None, "unit": None, "added": False, "list": False,
                                          "code": self.code_of(report)})

    def test_a_later_report_of_the_same_game_never_takes_the_units_line_away(self):
        """Two crash reports of one game (the game's crash reporter's and Windows' own, say): the one we know is told
        with its unit and its code; another one after it that we don't know doesn't put a code alone in its place."""
        self.accept(5)
        local = self.home / "local"
        for i, report in enumerate((self.made_report(), self.made_report(place=0x4321))):
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
        with mock.patch.object(w, "send_waiting"), mock.patch.object(bugwatch, "unit_named",
                                                                     return_value={"name": "Tiger", "added": False}):
            g.run()
        notice = bugwatch.crash_notice()["notice"]
        self.assertEqual((notice["why"], notice["unit"]), ("made", "Tiger"))
        self.assertEqual(notice["code"], self.code_of(self.made_report()))

    def test_before_version_5_no_code(self):
        """Part 3's crash code acts only once version 5 is accepted: under version 4 the notice is as it was."""
        program = self.program([self.create])
        self.accept(4)
        _sent, told, _ = self.run_game(self.made_report(), {"name": "Horse Squad", "added": True}, program)
        self.assertEqual(told["notice"], {"why": "made", "unit": "Horse Squad", "added": True, "list": True})
        _sent, told, _ = self.run_game(self.made_report(place=0x4321), {"name": "Horse Squad", "added": True},
                                       program)
        self.assertIsNone(told["notice"])

    def test_the_studios_watch_gives_the_same_code(self):
        """The owner's "13, yes" (2026-11-26): the Studio's notice after a Test in game carries the crash code, the
        same the Launcher's gives for the same report."""
        program = self.program([self.create])
        self.accept(5)
        self.app = "studio"
        report = self.made_report()
        _sent, told, _ = self.run_game(report, {"name": "Horse Squad", "added": True}, program)
        self.assertEqual(told["notice"].pop("code"), self.code_of(report))
        self.assertEqual(told["notice"], {"why": "made", "unit": "Horse Squad", "added": True, "list": True})

    def test_what_bug_watch_keeps_and_sends_doesnt_change(self):
        """The code is the player's only: the crash report Bug Watch sends is the same with it as with no code given,
        and nothing Bug Watch keeps on the PC holds it."""
        program = self.program([self.create])
        self.accept(5)
        report = self.made_report()
        horse = {"name": "Horse Squad", "added": True}
        sent, told, _ = self.run_game(report, horse, program)
        code = told["notice"]["code"]
        with mock.patch.object(bugwatch, "crash_code_given", return_value=False):
            plain, told_plain, _ = self.run_game(report, horse, program)
        self.assertNotIn("code", told_plain["notice"])            # (the control: no code given)
        self.assertEqual(sent, plain)
        self.assertNotIn(code, json.dumps(sent))
        self.assertNotIn(code.replace("-", ""), json.dumps(sent))
        for path in (self.home / bugwatch.FOLDER).rglob("*"):
            if path.is_file():
                self.assertNotIn(code, path.read_text(encoding="utf-8", errors="replace"), path.name)


UI = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher"
DISCORD_ID = "328197688749195277"   # the owner's Discord user ID: never in the notice (the lead's settlement 3)


def node_exe() -> str | None:
    import shutil
    node = os.environ.get("RUSE_NODE") or shutil.which("node") or next(
        (str(p) for p in sorted(Path("D:/RUSE-2.0/tools").glob("node-v*/node.exe"))[::-1]), None)
    return node if node and Path(node).is_file() else None


def launcher_words() -> dict:
    import tomllib
    return tomllib.loads((UI / "words.toml").read_text(encoding="utf-8"))


def run_node(test: unittest.TestCase, script: str, *args: str) -> str:
    """`script` run in Node with `args`: what it printed (the test skipped with no Node, failed when Node fails)."""
    import subprocess
    import tempfile
    node = node_exe()
    if node is None:
        test.skipTest("no Node")
    with tempfile.TemporaryDirectory(dir=os.environ.get("TEMP")) as d:
        f = Path(d) / "page.js"
        f.write_text(script, encoding="utf-8")
        ran = subprocess.run([node, str(f), *args], capture_output=True, text=True, encoding="utf-8", timeout=120)
    test.assertEqual(ran.returncode, 0, ran.stderr[-3000:])
    return ran.stdout


# The Launcher's own ui/app.js, run in Node over a small stand-in of the page's elements: each case's notice said by
# sayCrash in its words; then its Copy code button pressed (the timers that follow run), its GitHub link pressed, and
# (when the case asks) the message's Report link. What the page showed and what each press reached comes back.
PAGE = r"""
const fs = require("fs"), vm = require("vm");
const [appFile, casesFile] = process.argv.slice(-2);
const app = fs.readFileSync(appFile, "utf8");

class El {   // the few parts of a page element the crash notice uses
  constructor(tag) {
    Object.assign(this, { tagName: tag.toUpperCase(), childNodes: [], parentNode: null, on: {}, className: "",
      title: "", type: "", value: "", style: {} });
  }
  get textContent() { return this.childNodes.map((k) => (typeof k === "string" ? k : k.textContent)).join(""); }
  set textContent(v) { this.replaceChildren(String(v)); }
  get firstChild() { return this.childNodes[0] || null; }
  append(...kids) {
    for (const k of kids) {
      if (typeof k !== "string") { if (k.parentNode) k.remove(); k.parentNode = this; }
      this.childNodes.push(k);
    }
  }
  replaceChildren(...kids) {
    for (const k of this.childNodes) if (typeof k !== "string") k.parentNode = null;
    this.childNodes = [];
    this.append(...kids);
  }
  remove() {
    if (this.parentNode) this.parentNode.childNodes = this.parentNode.childNodes.filter((k) => k !== this);
    this.parentNode = null;
  }
  addEventListener(type, fn) { (this.on[type] = this.on[type] || []).push(fn); }
  async click() { for (const fn of this.on.click || []) await fn({ stopPropagation() {}, preventDefault() {} }); }
  select() {}
  focus() {}
  setAttribute() {}
}

(async () => {
  const out = [];
  for (const c of JSON.parse(fs.readFileSync(casesFile, "utf8"))) {
    const seen = { clipboard: [], exec: [], selected: [], opened: [], reported: [] }, timers = [], ids = {};
    const body = new El("body");
    const document = {
      body, addEventListener() {},
      getElementById: (id) => ids[id] || (ids[id] = new El("p")),
      createElement: (tag) => new El(tag),
      execCommand: (what) => {
        const box = body.childNodes.find((k) => k.tagName === "TEXTAREA");
        seen.exec.push([what, box ? box.value : null]);
        return c.exec;
      },
    };
    const navigator = c.clipboard === "works" ? { clipboard: { writeText: async (t) => { seen.clipboard.push(t); } } }
      : c.clipboard === "refused" ? { clipboard: { writeText: async () => { throw new Error("not allowed"); } } } : {};
    const window = { addEventListener() {},
      getSelection: () => ({ removeAllRanges() {}, selectAllChildren: (n) => seen.selected.push(n.textContent) }) };
    const ctx = vm.createContext({ console, document, navigator, window, localStorage: {}, location: { search: "" },
      URLSearchParams, setTimeout: (fn) => { timers.push(fn); return timers.length; }, clearTimeout: () => {} });
    vm.runInContext(app, ctx, { filename: "app.js" });
    window.pywebview = { api: {
      open_help: async (what) => { seen.opened.push(what); return { opened: what }; },
      report_problem: async (message) => { seen.reported.push(message); return { opened: "" }; } } };
    Object.assign(ctx, { WORDS: c.words, NOTICE: c.notice });
    vm.runInContext("state.words = WORDS; sayCrash(NOTICE);", ctx);
    const said = ids["play-message"];
    const parts = said.childNodes.map((k) => (typeof k === "string" ? { text: k }
      : { tag: k.tagName, cls: k.className, text: k.textContent, title: k.title }));
    const find = (cls) => said.childNodes.find((k) => typeof k !== "string" && k.className.split(" ").includes(cls));
    const copy = find("crash-copy"), github = find("crash-github");
    const report = said.childNodes.filter((k) => typeof k !== "string" && k.className === "link").pop();
    let pressed = null, later = null;
    if (copy) {
      await copy.click();
      pressed = copy.textContent;
      while (timers.length) timers.shift()();
      later = copy.textContent;
    }
    if (github) await github.click();
    if (report && c.report) await report.click();
    out.push({ kind: said.className, parts, pressed, later, left: body.childNodes.length, ...seen });
  }
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error((e && e.stack) || String(e)); process.exit(1); });
"""


class ThePage(unittest.TestCase):
    """The Launcher page's crash notice (app.js crashText and sayCrash, run in Node with each language's words): the
    crash code alone (Bug Watch off, or a crash not on our list), under the unit's line or under "couldn't check" (Bug
    Watch on), and a crash that couldn't be checked; each in its language with no blank left. The words the owner
    asked for (2026-11-26): send the code and a screenshot to XUL on Discord (XUL6x3) or on GitHub, his Discord user ID
    never shown; a Copy code button that copies the code alone."""

    CODE = crashcode.make({"code": "0xc0000005", "module": "RUSE.exe", "offset": "0x4321"})
    KNOWN = {"why": "made", "unit": "Horse Squad", "added": True, "list": True}
    NO_LIST = {"why": None, "unit": None, "added": False, "list": False}

    def expected(self, words: dict, lang: str, notice: dict) -> str:
        """What the notice says in `lang`, from words.toml alone."""
        code = notice.get("code")
        if notice.get("list") is False:
            head = words["crash_no_list"][lang]
        elif notice.get("why"):
            head = (words["crash_mod_unit"][lang].replace("{unit}", notice["unit"])
                    .replace("{why}", words[f"crash_why_{notice['why']}"][lang]))
        else:
            head = ""
        if not code:
            return head
        if not head:
            return words["crash_code"][lang].replace("{code}", code)
        return head + "\n" + words["crash_code_under"][lang].replace("{code}", code)

    def test_the_crash_lines_in_every_language(self):
        import re
        from rusemod import schema
        words = launcher_words()
        js = (UI / "ui" / "app.js").read_text(encoding="utf-8")

        def function(name: str) -> str:
            start = js.index(f"function {name}(")
            return js[start:js.index("\n}\n", start) + 2]
        langs = sorted(schema.APP_LANGS)
        all_words = {lang: {k: v[lang] for k, v in words.items() if isinstance(v, dict) and lang in v} for lang in langs}
        notices = [{"code": self.CODE}, self.NO_LIST, {**self.KNOWN, "code": self.CODE},
                   {**self.NO_LIST, "code": self.CODE}, self.KNOWN]
        script = (function("fill") + function("crashText") + "const state = { words: null };\n"
                  f"const all = {json.dumps(all_words, ensure_ascii=False)};\n"
                  f"const notices = {json.dumps(notices)};\n"
                  "const out = {};\n"
                  "for (const lang of Object.keys(all)) { state.words = all[lang];"
                  " out[lang] = notices.map((n) => crashText(n)); }\n"
                  "console.log(JSON.stringify(out));\n")
        said = json.loads(run_node(self, script))
        for lang in langs:
            with self.subTest(lang=lang):
                for notice, text in zip(notices, said[lang]):
                    self.assertEqual(text, self.expected(words, lang, notice))
                    self.assertNotIn("{", text)
                    self.assertNotIn("undefined", text)
                alone, under = words["crash_code"][lang], words["crash_code_under"][lang]
                self.assertEqual(said[lang][0], alone.replace("{code}", self.CODE))
                self.assertEqual(said[lang][2].split("\n")[1], under.replace("{code}", self.CODE))
                for text in (alone, under):
                    self.assertEqual(text.count("{code}"), 1)
                    for name in ("XUL", "XUL6x3", "Discord"):
                        self.assertIn(name, text)
                    self.assertEqual(len(re.findall(r"GitHub[A-Za-z]*", text)), 1)   # the one link
                    self.assertNotIn(DISCORD_ID, text)
                # the code alone starts with the game's "The game crashed." (crash_no_unit's own first sentence); under
                # a line that already says so, that sentence goes and the request after the code stays word for word
                self.assertTrue(alone.startswith(words["crash_no_unit"][lang].split("{why}")[0].strip()))
                self.assertNotIn(words["crash_no_unit"][lang].split("{why}")[0].strip(), under)
                self.assertEqual(alone.split("{code}")[1], under.split("{code}")[1])
                if lang != "us":
                    self.assertNotEqual(said[lang][1], words["crash_no_list"]["us"])
                    self.assertNotEqual(alone, words["crash_code"]["us"])
                    self.assertNotEqual(under, words["crash_code_under"]["us"])
        self.assertEqual(words["crash_code"]["us"],
                         "The game crashed. Its crash code is {code}. Please send this code and a screenshot of this "
                         "message to XUL on Discord (XUL6x3) or on GitHub, so we can look into why.")
        self.assertNotIn(DISCORD_ID, (UI / "words.toml").read_text(encoding="utf-8"))
        self.assertNotIn(DISCORD_ID, js)

    def page(self, cases: list) -> list:
        import tempfile
        with tempfile.TemporaryDirectory(dir=os.environ.get("TEMP")) as d:
            f = Path(d) / "cases.json"
            f.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
            return json.loads(run_node(self, PAGE, str(UI / "ui" / "app.js"), str(f)))

    @staticmethod
    def words_before_the_button(parts: list) -> str:
        """The notice's words as shown: its text up to the Copy code button, a line break as a new line."""
        out = []
        for p in parts:
            if "crash-copy" in (p.get("cls") or "").split():
                break
            out.append("\n" if p.get("tag") == "BR" else p["text"])
        return "".join(out).rstrip(" ")

    def test_the_notice_copies_only_the_code_and_opens_github(self):
        """The owner, 2026-11-26: "... please send this to him. Send this screenshot. And then be like, copy code. And
        then we'll have the exact code to know what went wrong." In every language: the notice's words, the code as
        one piece of its own, the word GitHub a link to the project's GitHub issues page (api.open_help("issues")) and a
        Copy code button that puts the code alone on the clipboard, then says Copied for a moment; the message keeps
        its Report link, whose bug report carries the code. A window whose clipboard API refuses copies the old way
        (execCommand, as owned.js does); where neither works, the code is selected (Ctrl+C copies it) and no Copied is
        said. Bug Watch on: the unit's line, then the code's under it. No code (before version 5): the notice as
        before, no button."""
        from rusemod import schema
        words = launcher_words()
        langs = sorted(schema.APP_LANGS)
        mine = {lang: {k: v[lang] for k, v in words.items() if isinstance(v, dict) and lang in v} for lang in langs}
        alone = {"code": self.CODE}
        cases = [{"words": mine[lang], "notice": alone, "clipboard": "works", "exec": False, "report": lang == "us"}
                 for lang in langs]
        cases += [{"words": mine["us"], "notice": {**self.KNOWN, "code": self.CODE}, "clipboard": "works",
                   "exec": False},
                  {"words": mine["us"], "notice": {**self.NO_LIST, "code": self.CODE}, "clipboard": "works",
                   "exec": False},
                  {"words": mine["us"], "notice": alone, "clipboard": "refused", "exec": True},
                  {"words": mine["us"], "notice": alone, "clipboard": "none", "exec": False},
                  {"words": mine["us"], "notice": self.KNOWN, "clipboard": "works", "exec": False}]
        seen = self.page(cases)
        for lang, got in zip(langs, seen):
            with self.subTest(lang=lang):
                self.assertEqual(got["kind"], "message bad")
                self.assertEqual(self.words_before_the_button(got["parts"]), self.expected(words, lang, alone))
                codes = [p for p in got["parts"] if p.get("tag") == "CODE"]
                self.assertEqual([p["text"] for p in codes], [self.CODE])          # the code, as one piece
                links = [p for p in got["parts"] if "crash-github" in (p.get("cls") or "").split()]
                self.assertEqual(len(links), 1)
                self.assertTrue(links[0]["text"].startswith("GitHub"), links[0])
                self.assertEqual(links[0]["title"], words["tip_crash_github"][lang])
                (button,) = [p for p in got["parts"] if "crash-copy" in (p.get("cls") or "").split()]
                self.assertEqual((button["tag"], button["text"], button["title"]),
                                 ("BUTTON", words["crash_copy"][lang], words["tip_crash_copy"][lang]))
                self.assertEqual(got["clipboard"], [self.CODE])                   # the code alone, nothing else
                self.assertEqual((got["pressed"], got["later"]),
                                 (words["crash_copied"][lang], words["crash_copy"][lang]))
                self.assertEqual(got["opened"], ["issues"])
                self.assertEqual(got["exec"], [])
        us = seen[langs.index("us")]
        self.assertEqual(us["reported"], [self.expected(words, "us", alone)])  # the Report link's bug report: the code
        known, no_list, refused, none, before = seen[len(langs):]
        for got, notice in ((known, {**self.KNOWN, "code": self.CODE}), (no_list, {**self.NO_LIST, "code": self.CODE})):
            shown = self.words_before_the_button(got["parts"])
            self.assertEqual(shown, self.expected(words, "us", notice))
            self.assertEqual([p.get("tag") for p in got["parts"]].count("BR"), 1)   # the code's line under the first
            self.assertEqual(got["clipboard"], [self.CODE])
        self.assertEqual((refused["clipboard"], refused["exec"]), ([], [["copy", self.CODE]]))   # the old way
        self.assertEqual((refused["pressed"], refused["later"], refused["left"]),
                         (words["crash_copied"]["us"], words["crash_copy"]["us"], 0))     # (its box taken away)
        self.assertEqual((none["exec"], none["selected"]), ([["copy", self.CODE]], [self.CODE]))
        self.assertEqual((none["pressed"], none["later"], none["left"]),
                         (words["crash_copy"]["us"], words["crash_copy"]["us"], 0))       # no Copied said
        self.assertEqual(before["parts"][0], {"text": self.expected(words, "us", self.KNOWN)})
        self.assertFalse([p for p in before["parts"] if p.get("tag") in ("CODE", "BR")
                          or {"crash-copy", "crash-github"} & set((p.get("cls") or "").split())])
        self.assertEqual((before["clipboard"], before["opened"]), ([], []))


if __name__ == "__main__":
    unittest.main()
