"""Scenarios: what a player meets around Play beside the build (the base, its made-up game and its stand-ins:
tests/test_scenarios_play_base.py): the first start's agreement (version 4) in both apps on one PC, accepted with Bug
Watch ticked and not, shown again to a player of version 3, closed without accepting; Bug Watch on and off at a Play;
the crash notice after a game a Play started stops at a crash we know, said by the Launcher's page in every language
(its own crashText, run in Node); a required update before Play and Test in game, in every language.

Bug Watch never reaches its server here: its Watch is made with a fake of the server (test_bugwatch's Server), its error
hooks and its save at the app's end aren't installed, and the crash reports it reads are the made-up ones a test writes
in this test's LOCALAPPDATA (the base). The made-up crash report and the made-up program file are the crash piece's
tests' own (test_bugwatch KnownCrashes: laid out by rusemod.crashplaces' table, no detail of the game's program).

FOR: the Test in game and Play scenarios (release 0.9.8.20, overnight 2026-11-14). USED-BY: the scenarios' run and
report."""
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
        self.assertEqual(self.settings()["guard"]["terms"], 4)
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
        self.assertEqual((self.settings()["guard"]["terms"], la.bugwatch_status()["on"]), (4, False))
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
        exe = next(p for p in cls.game.iterdir() if p.suffix.lower() == ".exe")
        exe.write_bytes(cls.program)

    def play_and_crash(self, report: bytes, named, accepted: int = 4, lang: str = "fr") -> dict:
        """Bug Watch on (agreement `accepted`), a set played, the game it started closes leaving `report` (Bug Watch
        reads the copy's data for the unit's name: `named` stands in for it): what the page is handed."""
        from rusemod import bugwatch

        class Closed:
            def poll(self):
                return 0
        la = self.launcher(start_game=lambda exe: self.started.append(exe) or Closed())
        la.set_pref("lang", lang)
        la.guard_accept_terms()
        la.bugwatch_on("Nick")
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
        with mock.patch.object(bugwatch, "unit_named", return_value=named) as naming:
            j = self.wait(la.play("mine")["job"], la)
            self.assertEqual(j["state"], "done", j)
            end = time.time() + 30       # (asked as the page asks: a notice is handed over once, watching or not)
            seen = la.bugwatch_crash()
            while seen["watching"] and seen["notice"] is None and time.time() < end:
                time.sleep(0.05)
                seen = la.bugwatch_crash()
        self.naming = naming
        return seen


class TheCrashNotice(CrashingGame):
    def test_a_crash_we_know_tells_the_unit_and_why(self):
        """Usual: Bug Watch on under version 4; the game stops at a crash we know while making one of the game's own
        units: the page is handed the reason and the unit (named in the player's language), once."""
        seen = self.play_and_crash(self.report, {"name": "Panzer IV (fr)", "added": False})
        self.assertEqual(seen["notice"], {"why": "made", "unit": "Panzer IV (fr)", "added": False})
        self.assertEqual(self.naming.call_args[0][3], "fr")
        from rusemod import bugwatch
        self.assertIsNone(bugwatch.crash_notice()["notice"])

    def test_under_version_3_only_why(self):
        """Usual: the same crash for a player who accepted version 3 only: the reason, no unit."""
        seen = self.play_and_crash(self.report, {"name": "Panzer IV (fr)", "added": False}, accepted=3)
        self.assertEqual(seen["notice"], {"why": "made", "unit": None, "added": False})

    def test_a_crash_we_dont_know_tells_nothing(self):
        seen = self.play_and_crash(self.unknown, {"name": "Panzer IV (fr)", "added": False})
        self.assertIsNone(seen["notice"])

    def test_the_page_says_it_in_every_language(self):
        """The Launcher page's own crashText (app.js, run in Node with each language's words): the game's unit, a mod's
        unit, no unit; every reason the table has: each sentence in its language, the unit's name in it, no blank
        left, never the English sentence in another language."""
        from rusemod import crashplaces
        exe = node()
        if exe is None:
            self.skipTest("no Node")
        js = LAUNCHER_UI.read_text(encoding="utf-8")
        notices = [{"why": why, "unit": unit, "added": added} for why in sorted(crashplaces.REASONS)
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


class TheCrashNoticeAfterTestInGame(CrashingGame):
    def test_the_studio_keeps_it_and_its_page_never_asks(self):
        """Today's state, for the owner's open question left by the crash piece's join ("whether the Studio's Test in
        game says the same"): Bug Watch on under version 4, Test in game starts the game, it stops at a crash we know:
        the Studio's back end has the notice (its bugwatch_crash hands it over) but its page never asks for it (no
        bugwatch_crash in the Studio's app.js), so a Studio player is told nothing; the notice goes when the next game
        starts."""
        from rusemod import bugwatch

        class Closed:
            def poll(self):
                return 0
        self.api._starter.start_game = lambda exe: self.started.append(exe) or Closed()
        self.page.set_pref("lang", "fr")
        self.addCleanup(self.page.set_pref, "lang", "us")
        self.page.guard_accept_terms()
        self.page.bugwatch_on("Nick")
        self.a_mod()
        dump = self.local / "Temp" / "CrashRpt_s" / "report.dmp"
        dump.parent.mkdir(parents=True, exist_ok=True)
        dump.write_bytes(self.report)
        later = time.time() + 3600
        os.utime(dump, (later, later))
        with mock.patch.object(bugwatch, "unit_named", return_value={"name": "Panzer IV (fr)", "added": False}):
            self.assertEqual(self.wait(self.page.test_in_game()["job"])["state"], "done")
            end = time.time() + 30
            seen = self.page.bugwatch_crash()
            while seen["watching"] and seen["notice"] is None and time.time() < end:
                time.sleep(0.05)
                seen = self.page.bugwatch_crash()
        self.assertEqual(seen["notice"], {"why": "made", "unit": "Panzer IV (fr)", "added": False})
        studio_ui = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui" / "app.js"
        self.assertNotIn("bugwatch_crash", studio_ui.read_text(encoding="utf-8"))


class ARequiredUpdate(Watched):
    def test_play_and_test_in_game_wait_in_every_language(self):
        """Unusual: the Launcher has seen a required update of its own (kept in settings.json, the internet gone
        since): Play is refused in the player's language, nothing built or started; the Studio, with no required update
        of its own, still tests."""
        la = self.launcher()
        la.use_required_updates()
        from rusemod.home import save_settings
        values = self.settings()
        values["required_update"] = {"launcher": "99.0.0"}
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
