"""Scenarios: what a player meets around Play beside the build (the base, its made-up game and its stand-ins:
tests/test_scenarios_play_base.py): the first start's agreement (version 4) in both apps on one PC, accepted with Bug
Watch ticked and not, shown again to a player of version 3, closed without accepting; Bug Watch on and off at a Play;
the crash notice after a game a Play started stops at a crash we know, said by the Launcher's page in every language
(its own crashText, run in Node); a required update before Play and Test in game, in every language.

Bug Watch never reaches its server here: its Watch is made with a fake of the server (test_bugwatch's Server), its error
hooks and its save at the app's end aren't installed, and the crash reports it reads are the made-up ones a test writes
in this test's LOCALAPPDATA (the base). Our list of known crashes (rusemod.knowncrashes, fetched under version 5 of the
agreement) comes from a fake of its address too, and anything else that reaches for the network fails the test
(test_knowncrashes.keep_off_the_network). The made-up crash report, the made-up program file and the made-up list are
the crash piece's tests' own (test_bugwatch KnownCrashes, test_knowncrashes MadeUp: no detail of the game's program).
A crash of a game the Launcher started gets a crash code (rusemod.crashcode) under version 5, Bug Watch on or off (the
owner, 2026-11-26: every player).

FOR: the Test in game and Play scenarios (release 0.9.8.20, overnight 2026-11-14). USED-BY: the scenarios' run and
report."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from test_scenarios_play_base import LANGS, PlayScenario

AGREEMENT = Path(__file__).resolve().parents[1] / "src" / "rusemod" / "sharedui" / "agreement.js"
LAUNCHER_UI = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher" / "ui" / "app.js"


class Watched(PlayScenario):
    """Bug Watch as the apps start it, its sends to a fake server."""

    def setUp(self):
        super().setUp()
        from rusemod import bugwatch
        from test_bugwatch import Server
        from test_knowncrashes import keep_off_the_network
        keep_off_the_network(self)
        self.server = Server()
        real = bugwatch.Watch
        for target, stand in (("Watch", lambda home, app, version, **kw: real(home, app, version, opener=self.server,
                                                                              **kw)),
                              ("_hook_errors", lambda watch: None)):
            patcher = mock.patch.object(bugwatch, target, stand)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch("atexit.register", lambda *a, **kw: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self._on = bugwatch.ON
        bugwatch.ON = True
        self.addCleanup(setattr, bugwatch, "ON", self._on)
        self.addCleanup(setattr, bugwatch, "_current", None)
        self.addCleanup(setattr, bugwatch, "_notice", None)
        bugwatch._notice = None

    def settings(self) -> dict:
        from rusemod.home import settings
        return settings(self.home)

    def opens(self, api) -> bool:
        """Whether the agreement screen opens at this app's start (agreement.js open: fair play on, and the terms
        accepted are older than the version)."""
        st = api.guard_status()
        return api.fair_play_on()["on"] and (st.get("terms") or 0) < (st.get("terms_version") or 1)


class TheAgreement(Watched):
    def test_the_page_opens_it_by_the_version_and_has_no_way_but_accept(self):
        """The screen's own code: it opens while the terms accepted are older than the version; Accept is its one
        button (no Decline: closing the app is how a player declines, and the screen opens again at the next start)."""
        js = AGREEMENT.read_text(encoding="utf-8")
        self.assertIn("if ((st.terms || 0) >= (st.terms_version || 1)) return;", js)
        self.assertEqual(js.count('<button id="agree-'), 1)

    def test_first_start_accepted_with_bug_watch_in_the_launcher_and_the_studio_knows(self):
        """Usual: a first start of the Launcher: the agreement opens; Accept with Bug Watch ticked, then a username:
        version 4 accepted, Bug Watch on, the name made unique. The Studio on the same PC opens no agreement and has
        Bug Watch on under the same name."""
        la = self.launcher()
        self.assertTrue(self.opens(la))
        la.guard_accept_terms()                          # (the page's Accept)
        named = la.bugwatch_on("Nick")                   # (the page's username, Bug Watch ticked)
        self.assertRegex(named["name"], r"^Nick#\d{4}$")
        self.assertEqual(self.settings()["guard"]["terms"], 5)   # version 5: the v5 words (legal/agreement-v5)
        self.assertFalse(self.opens(la))
        self.assertFalse(self.opens(self.api))
        self.assertEqual(self.api.bugwatch_status()["name"], named["name"])
        self.assertTrue(self.api.bugwatch_status()["on"])

    def test_accepted_without_bug_watch(self):
        """Usual: Accept with Bug Watch unticked, a username all the same (RUSE Guard's): Bug Watch off, the name
        kept; a Play then: no game is watched, nothing counted or sent."""
        la = self.launcher()
        la.guard_accept_terms()
        la.set_username("Ann")
        self.assertEqual((la.bugwatch_status()["on"], bool(la.bugwatch_status()["name"])), (False, True))
        folder = self.a_mod()
        la.add_mod(str(folder))
        la.new_set("Mine", [folder.name])
        self.assertEqual(self.played(la, "mine")["state"], "done")
        self.assertEqual(la.bugwatch_crash(), {"watching": False, "notice": None})
        self.assertEqual(self.server.sent, [])

    def test_a_version_3_player_unticks_bug_watch_on_version_4(self):
        """Usual: a player who accepted version 3 with Bug Watch on: the agreement opens again for version 4, its Bug
        Watch box ticked as it is; he unticks it and accepts: version 4 accepted, Bug Watch off, his name kept (RUSE
        Guard keeps it)."""
        la = self.launcher()
        la.guard_accept_terms()
        la.bugwatch_on("Nick")
        values = self.settings()
        values["guard"]["terms"] = 3
        from rusemod.home import save_settings
        save_settings(self.home, values)
        self.assertTrue(self.opens(la))
        status = la.bugwatch_status()
        self.assertTrue(status["on"])                    # (the box starts ticked: agreement.js accept)
        la.guard_accept_terms()
        la.bugwatch_off()                                # (unticked: bw false, status.on true)
        self.assertEqual((self.settings()["guard"]["terms"], la.bugwatch_status()["on"]), (5, False))   # version 5 now
        self.assertEqual(la.bugwatch_status()["name"], status["name"])

    def test_closed_without_accepting(self):
        """Unusual: a player of version 3 (Bug Watch on) closes the app at the agreement: nothing changes, it opens
        again at the next start, and until he accepts what version 4 added is never counted or sent
        (bugwatch.allows_v4), nor does RUSE Guard collect a match (its terms are version 4's)."""
        from rusemod import bugwatch, guard
        la = self.launcher()
        la.guard_accept_terms()
        la.bugwatch_on("Nick")
        values = self.settings()
        values["guard"]["terms"] = 3
        from rusemod.home import save_settings
        save_settings(self.home, values)
        self.assertTrue(self.opens(self.launcher()))
        self.assertFalse(bugwatch.allows_v4(self.home))

        class Closed:
            def poll(self):
                return 0
        with mock.patch.object(guard, "collect") as collected:
            guard.MatchWatch(Closed(), self.home, self.game, self.copy(), username="Nick#1234",
                             consent=la.guard_status(), manifests=[], sleep=lambda s: None).run()
        collected.assert_not_called()


def node() -> str | None:
    tools = Path("D:/RUSE-2.0/tools")
    found = os.environ.get("RUSE_NODE") or shutil.which("node")
    if not found and tools.is_dir():
        found = next((str(p) for p in sorted(tools.glob("node-v*/node.exe"))[-1:]), None)
    return found


def page_function(text: str, name: str) -> str:
    start = text.index(f"function {name}(")
    return text[start:text.index("\n}\n", start) + 2]


class CrashingGame(Watched):
    """A game an app started stops at a crash we know (the crash piece, item 25): the made-up program is the game's
    program file here, so the modded copy has it, and the made-up crash report is written where Bug Watch looks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_bugwatch import KnownCrashes
        kc = KnownCrashes("test_a_crash_we_know_says_why_and_which_unit")
        kc.setUp()
        try:
            cls.program = kc.program([kc.create]).read_bytes()
            cls.report = kc.report([0, kc.BASE + kc.create, kc.UNIT], [kc.description(4059)]).read_bytes()
            cls.unknown = kc.report([0, kc.BASE + kc.create, kc.UNIT], [kc.description(4059)], place=0x4321).read_bytes()
        finally:
            kc.tearDown()
            kc.doCleanups()   # (its setUp's patches end here, not at the end of the whole run)
        exe = next(p for p in cls.game.iterdir() if p.suffix.lower() == ".exe")
        exe.write_bytes(cls.program)

    def play_and_crash(self, report: bytes, named, accepted: int = 5, lang: str = "fr", ticked: bool = True) -> dict:
        """Bug Watch on (`ticked`; agreement `accepted`), a set played, the game it started closes leaving `report`
        (Bug Watch reads the copy's data for the unit's name: `named` stands in for it; our list of known crashes
        comes from the fake list address, self.lists): what the page is handed."""
        import threading
        from rusemod import bugwatch, net
        from test_knowncrashes import ListServer, MadeUp

        class Closed:
            def poll(self):
                return 0
        la = self.launcher(start_game=lambda exe: self.started.append(exe) or Closed())
        bugwatch.start(self.home, "launcher", "0.4.8.22")   # (as the Launcher's window does when it opens)
        la.set_pref("lang", lang)
        la.guard_accept_terms()
        if ticked:
            la.bugwatch_on("Nick")
        else:
            la.set_username("Nick")
        values = self.settings()
        values["guard"]["terms"] = accepted
        from rusemod.home import save_settings
        save_settings(self.home, values)
        folder = self.a_mod()
        la.add_mod(str(folder))
        la.new_set("Mine", [folder.name])
        dump = self.local / "Temp" / "CrashRpt_x" / "report.dmp"
        dump.parent.mkdir(parents=True, exist_ok=True)
        dump.write_bytes(report)
        later = time.time() + 3600
        os.utime(dump, (later, later))
        self.lists = getattr(self, "lists", None) or ListServer(MadeUp.blob())
        with mock.patch.object(bugwatch, "unit_named", return_value=named) as naming, \
                mock.patch.object(net, "urlopen", self.lists):
            j = self.wait(la.play("mine")["job"], la)
            self.assertEqual(j["state"], "done", j)
            end = time.time() + 30       # (asked as the page asks: a notice is handed over once, watching or not)
            seen = la.bugwatch_crash()
            while seen["watching"] and seen["notice"] is None and time.time() < end:
                time.sleep(0.05)
                seen = la.bugwatch_crash()
            # (the player is told first, before Bug Watch's own records: the watch, a fetch still on its way and the
            # sends it starts end here, at their fakes, before the test's folders go)
            for name in ("bug-watch-game", "crash-code-watch", "bug-watch-crash-list", "send_waiting"):
                for t in threading.enumerate():
                    if name in t.name and t is not threading.current_thread():
                        t.join(10)
        self.naming = naming
        return seen


class TheCrashNotice(CrashingGame):
    def code_of_the_report(self) -> str:
        """The crash code of the report this test's game left, made as for a player without Bug Watch."""
        from rusemod import bugwatch, crashcode
        return crashcode.make(bugwatch.read_dump(self.local / "Temp" / "CrashRpt_x" / "report.dmp"))

    def test_a_crash_we_know_tells_the_unit_and_why(self):
        """Usual: Bug Watch on under version 5; our list comes from the Bug Watch server while the game runs (one GET
        of its address); the game stops at a crash we know while making one of the game's own units: the page is
        handed the reason and the unit (named in the player's language), and the crash code a player without Bug Watch
        gets (the owner, 2026-11-26: every player), once."""
        seen = self.play_and_crash(self.report, {"name": "Panzer IV (fr)", "added": False})
        self.assertEqual(seen["notice"], {"why": "made", "unit": "Panzer IV (fr)", "added": False, "list": True,
                                          "code": self.code_of_the_report()})
        self.assertEqual(self.naming.call_args[0][3], "fr")
        from rusemod import bugwatch, knowncrashes
        self.assertIsNone(bugwatch.crash_notice()["notice"])
        self.assertEqual([r.full_url for r in self.lists.asked], [bugwatch.SERVER + knowncrashes.ROUTE])
        self.assertNotIn(seen["notice"]["code"], json.dumps([body for _route, body in self.server.sent]))

    def couldnt_check(self, accepted: int) -> None:
        """Unusual: the same crash for a player who accepted an older version only (the list is fetched only under
        version 5, whose words say so): nothing is fetched, and the page is told the crash couldn't be checked."""
        seen = self.play_and_crash(self.report, {"name": "Panzer IV (fr)", "added": False}, accepted=accepted)
        self.assertEqual(seen["notice"], {"why": None, "unit": None, "added": False, "list": False})
        self.assertEqual(self.lists.asked, [])

    def test_under_version_4_nothing_is_fetched_and_the_launcher_says_it_couldnt_check(self):
        self.couldnt_check(4)

    def test_under_version_3_nothing_is_fetched_and_the_launcher_says_it_couldnt_check(self):
        self.couldnt_check(3)

    def test_a_crash_we_dont_know_tells_its_code(self):
        """Until 2026-11-26 it told a Bug Watch player nothing; now its crash code, as a player without Bug Watch
        gets it."""
        seen = self.play_and_crash(self.unknown, {"name": "Panzer IV (fr)", "added": False})
        self.assertEqual(seen["notice"], {"code": self.code_of_the_report()})

    def test_the_page_says_it_in_every_language(self):
        """The Launcher page's own crashText (app.js, run in Node with each language's words): the game's unit, a mod's
        unit, no unit; every reason the list may have: each sentence in its language, the unit's name in it, no blank
        left, never the English sentence in another language."""
        from rusemod import knowncrashes
        exe = node()
        if exe is None:
            self.skipTest("no Node")
        js = LAUNCHER_UI.read_text(encoding="utf-8")
        notices = [{"why": why, "unit": unit, "added": added} for why in sorted(knowncrashes.REASONS)
                   for unit, added in (("Panzer IV", False), ("Horse Squad", True), (None, False))]
        words = {lang: self.launcher_words(lang) for lang in LANGS}
        script = (page_function(js, "fill") + page_function(js, "crashText") + "const state = { words: null };\n"
                  f"const all = {json.dumps(words, ensure_ascii=False)};\n"
                  f"const notices = {json.dumps(notices)};\n"
                  "const out = {};\n"
                  "for (const lang of Object.keys(all)) { state.words = all[lang];"
                  " out[lang] = notices.map((n) => crashText(n)); }\n"
                  "console.log(JSON.stringify(out));\n")
        with tempfile.TemporaryDirectory(dir=self.tmp.name) as d:
            f = Path(d) / "crash.js"
            f.write_text(script, encoding="utf-8")
            ran = subprocess.run([exe, str(f)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(ran.returncode, 0, ran.stderr)
        said = json.loads(ran.stdout)
        for k, n in enumerate(notices):
            with self.subTest(notice=n):
                self.assert_worded({lang: said[lang][k] for lang in LANGS})
                for lang in LANGS:
                    if n["unit"]:
                        self.assertIn(n["unit"], said[lang][k], lang)
                    self.assertIn(words[lang][f"crash_why_{n['why']}"], said[lang][k], lang)


class TheCrashCodeWithoutBugWatch(CrashingGame):
    def test_a_player_without_bug_watch_gets_a_code_and_nothing_is_fetched_or_sent(self):
        """Usual: accepted with Bug Watch unticked (version 5); the game a Play started stops: the page is handed a
        crash code made from where it stopped (the owner, 2026-11-14), once; our server is never asked (no list, no
        report), and nothing of Bug Watch's is kept on the PC."""
        from rusemod import bugwatch, crashcode
        seen = self.play_and_crash(self.report, None, ticked=False)
        code = seen["notice"]["code"]
        dump = self.local / "Temp" / "CrashRpt_x" / "report.dmp"
        self.assertEqual(code, crashcode.make(bugwatch.read_dump(dump)))
        self.assertEqual(crashcode.read(code)["module"], "game")
        self.assertEqual((self.lists.asked, self.server.sent), ([], []))
        self.assertFalse((self.home / bugwatch.FOLDER).exists())
        self.assertIsNone(bugwatch.crash_notice()["notice"])

    def test_before_version_5_no_code(self):
        seen = self.play_and_crash(self.report, None, accepted=4, ticked=False)
        self.assertIsNone(seen["notice"])


class TheCrashNoticeAfterTestInGame(CrashingGame):
    def test_the_studio_keeps_it_and_its_page_asks_for_it(self):
        """The owner's open question left by the crash piece's join ("whether the Studio's Test in game says the
        same"), answered 2026-11-26 (B9 A: "after the game crashes in a Studio Test in game, the Studio shows the same
        crash notice the Launcher shows after Play"): Bug Watch on under version 5 (the Studio fetches our list too),
        Test in game starts the game, it stops at a crash we know: the Studio's back end has the notice (its
        bugwatch_crash hands it over) and its page asks for it after a test that started the game, and when it opens
        (tests/test_codes.py runs that part of the page in Node); the notice goes when the next game starts."""
        import threading
        from rusemod import bugwatch, net
        from rusemod.home import save_settings
        from test_knowncrashes import ListServer, MadeUp

        class Closed:
            def poll(self):
                return 0
        self.api._starter.start_game = lambda exe: self.started.append(exe) or Closed()
        self.page.set_pref("lang", "fr")
        self.addCleanup(self.page.set_pref, "lang", "us")
        self.page.guard_accept_terms()
        self.page.bugwatch_on("Nick")
        values = self.settings()
        values["guard"]["terms"] = 5
        save_settings(self.home, values)
        self.a_mod()
        dump = self.local / "Temp" / "CrashRpt_s" / "report.dmp"
        dump.parent.mkdir(parents=True, exist_ok=True)
        dump.write_bytes(self.report)
        later = time.time() + 3600
        os.utime(dump, (later, later))
        lists = ListServer(MadeUp.blob())
        with mock.patch.object(bugwatch, "unit_named", return_value={"name": "Panzer IV (fr)", "added": False}), \
                mock.patch.object(net, "urlopen", lists):
            self.assertEqual(self.wait(self.page.test_in_game()["job"])["state"], "done")
            end = time.time() + 30
            seen = self.page.bugwatch_crash()
            while seen["watching"] and seen["notice"] is None and time.time() < end:
                time.sleep(0.05)
                seen = self.page.bugwatch_crash()
            for name in ("bug-watch-game", "bug-watch-crash-list", "send_waiting"):   # (as play_and_crash)
                for t in threading.enumerate():
                    if name in t.name and t is not threading.current_thread():
                        t.join(10)
        code = seen["notice"].pop("code")   # the crash code too (the owner's "13, yes": as the Launcher's)
        self.assertEqual(seen["notice"], {"why": "made", "unit": "Panzer IV (fr)", "added": False, "list": True})
        from rusemod import crashcode
        self.assertEqual(crashcode.read(code)["module"], "game")
        self.assertEqual(len(lists.asked), 1)
        studio_ui = (Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui" / "app.js").read_text(
            encoding="utf-8")
        self.assertIn("seen = await api().bugwatch_crash();", studio_ui)
        self.assertIn("if (ok) watchCrash();", studio_ui)


    def test_without_bug_watch_the_studio_gives_the_code_alone(self):
        """The owner's "13, yes" (2026-11-26): a Studio player without Bug Watch (version 5 accepted, a username
        only) whose Test in game stops at a crash gets the crash code alone (CodeWatch), as a Launcher player after a
        Play; nothing is fetched (no list) or sent, and nothing of Bug Watch's is kept."""
        import threading
        from rusemod import bugwatch, net
        from rusemod.home import save_settings
        from test_knowncrashes import ListServer, MadeUp

        class Closed:
            def poll(self):
                return 0
        self.api._starter.start_game = lambda exe: self.started.append(exe) or Closed()
        self.page.set_pref("lang", "fr")
        self.addCleanup(self.page.set_pref, "lang", "us")
        self.page.guard_accept_terms()
        self.page.set_username("Nick")
        bugwatch.start(self.home, "studio", "0.9.8.22")   # (as the Studio's window does at every start: app.py)
        values = self.settings()
        values["guard"]["terms"] = 5
        save_settings(self.home, values)
        self.a_mod()
        dump = self.local / "Temp" / "CrashRpt_s" / "report.dmp"
        dump.parent.mkdir(parents=True, exist_ok=True)
        dump.write_bytes(self.report)
        later = time.time() + 3600
        os.utime(dump, (later, later))
        lists = ListServer(MadeUp.blob())
        with mock.patch.object(bugwatch, "unit_named", return_value={"name": "Panzer IV (fr)", "added": False}), \
                mock.patch.object(net, "urlopen", lists):
            self.assertEqual(self.wait(self.page.test_in_game()["job"])["state"], "done")
            end = time.time() + 30
            seen = self.page.bugwatch_crash()
            while seen["watching"] and seen["notice"] is None and time.time() < end:
                time.sleep(0.05)
                seen = self.page.bugwatch_crash()
            for name in ("bug-watch-game", "bug-watch-crash-list", "send_waiting"):   # (as play_and_crash)
                for t in threading.enumerate():
                    if name in t.name and t is not threading.current_thread():
                        t.join(10)
        from rusemod import crashcode
        self.assertEqual(crashcode.read(seen["notice"]["code"])["module"], "game")
        self.assertEqual(set(seen["notice"]), {"code"})        # the code alone: no list was read
        self.assertEqual((lists.asked, self.server.sent), ([], []))
        self.assertFalse((self.home / bugwatch.FOLDER).exists())


class ARequiredUpdate(Watched):
    def test_play_and_test_in_game_wait_in_every_language(self):
        """Unusual: the Launcher has seen a required update of its own (kept in settings.json, the internet gone
        since): Play is refused in the player's language, nothing built or started; the Studio, with no required update
        of its own, still tests."""
        la = self.launcher()
        la.use_required_updates()
        from rusemod.home import save_settings
        values = self.settings()
        values["required_signed"] = {"launcher": "99.0.0"}   # (a threshold the owner signed: rusemod.update)
        save_settings(self.home, values)
        folder = self.a_mod()
        la.add_mod(str(folder))
        la.new_set("Mine", [folder.name])
        said = {lang: self.played(la, "mine", lang)["message"] for lang in LANGS}
        self.assert_worded(said, "RUSE Launcher has a required update to install first. It installs by itself when "
                                 "the app starts: start it again, connected to the internet.")
        self.assertEqual(self.started, [])
        self.api.use_required_updates()
        self.assertEqual(self.in_game()["state"], "done")


if __name__ == "__main__":
    unittest.main()
