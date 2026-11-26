"""A cheat copy's stop, the apps' side (Part 5 of the legal fixes of 2026-11-24; the owner, 2026-11-24: "Fine, change it
to only go to our server."; his 22 A, 23 and 35 A of 2026-11-25). A copy built with cheats or test tools that leaves a
multiplayer match closes the game at that match's end-of-match screen with RUSE Guard's close number (the lock:
tests/gamescripts_sim.py25 plays it under the game's own Python); here what the apps do around it:

- the lock's lines speak the player's language: the app's own words, written into the copy when it is built (both
  apps), and a cheat copy is built again when the player's language changes; a copy without the lock never is;
- the Launcher, which started the game, sees the close number and files the note (rusemod.guard.MatchWatch), and its
  page says it in one line in the player's language, once;
- the Launcher asks before it closes while a game it started is still running;
- the Studio's Test in game starts no match watch, so it files no stop on our server.

Nothing starts and nothing leaves the PC: the build is a stand-in that writes the copy's record as the build does, the
game is a stand-in process, and no RUSE Guard server is set (a note stays in the outbox).

This test reads nothing of the game: its build stand-in only writes a few bytes under the game's file name into a
temporary copy, where the Starter looks for the game to start (rusemod.play)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from rusemod import fairplay, guard
from rusemod.play import Starter, built_from
from test_build import write_mod
from test_play_reuse import make_game

LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")


class Process:
    """The game's process as the apps see it: running until `code` is set, then closed with it."""

    def __init__(self, code=None):
        self.code = code

    def poll(self):
        return self.code


class Built:
    """What a build hands back (rusemod.build.build_and_write): no mistakes."""
    errors, order = [], []


class Around(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = make_game(self.root)
        self.home = self.root / "home"
        self.home.mkdir()
        self.copy = self.root / "RUSE-Instances" / "Modded game"
        self.cheat = write_mod(self.root / "mods", "dev", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"},
                               'tags = ["Cheat"]\n')
        self.plain = write_mod(self.root / "mods", "econ", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.builds = []   # the FairPlay each build was given

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, game, mods, *, instance, fairplay, **kw):
        """The build's stand-in: the copy and its record as the build leaves them (rusemod.build.build_and_write), a
        cheat copy's with its lock code."""
        self.builds.append(fairplay)
        instance.mkdir(parents=True, exist_ok=True)
        (instance / "RUSE.exe").write_bytes(b"MZ the game")
        mods_of = [(m.id, m.version) for m, _ops in mods]
        lock = FAIRPLAY.build_code("24687178", b"\1" * 32, mods_of) if fairplay.locked else None
        FAIRPLAY.write_record(instance, "24687178", b"\1" * 32, mods_of, fairplay, [], lock)
        return Built()

    def play(self, starter, mod, words=None):
        with mock.patch("rusemod.play.build_and_write", self.build), \
                mock.patch("rusemod.play.built_from", wraps=built_from) as made, \
                mock.patch("rusemod.instance.needs_build", lambda *a: True):
            starter.modded(self.game, [str(mod)], self.copy, "test", lambda line: None, words=words)
        return [call.kwargs.get("lock_lines") for call in made.call_args_list]


FAIRPLAY = fairplay   # (the build stand-in's own argument is named as the build's: `fairplay`)


class TheLocksLines(Around):
    def test_a_cheat_copy_s_lock_gets_the_player_s_lines_from_the_app_s_words(self):
        from ruse_launcher.api import words
        starter = Starter(open_url=lambda u: None, start_game=lambda exe: None, steam_running=lambda: True)
        french = fairplay.lock_lines(words("fr"))
        self.assertEqual(self.play(starter, self.cheat, words("fr")), [french, french])  # before and after the build
        self.assertEqual(self.builds[-1].lines, french)
        lock = self.builds[-1].patches(fairplay.build_code("24687178", b"\1" * 32, [("dev", "1.0.0")]))[0]
        self.assertEqual(fairplay.lock_words_of(lock), french)
        # English: nothing to fill in, the lock's own English
        self.assertEqual(self.play(starter, self.cheat, words("us")), [None, None])
        self.assertEqual(fairplay.lock_words_of(self.builds[-1].patches()[0]), ("", "", "", ""))

    def test_control_a_copy_without_the_lock_never_takes_them(self):
        from ruse_launcher.api import words
        starter = Starter(open_url=lambda u: None, start_game=lambda exe: None, steam_running=lambda: True)
        self.assertEqual(self.play(starter, self.plain, words("fr")), [None, None])
        self.assertFalse(self.builds[-1].locked)
        self.assertEqual([fairplay.lock_code_of(p) for p in self.builds[-1].patches()], [None, None])

    def test_another_language_builds_a_cheat_copy_again_and_only_a_cheat_copy(self):
        from ruse_launcher.api import words
        french, german = fairplay.lock_lines(words("fr")), fairplay.lock_lines(words("ger"))
        keys = {name: built_from(self.game, [str(self.cheat)], lock_lines=lines)["key"]
                for name, lines in (("english", None), ("french", french), ("german", german))}
        self.assertEqual(len(set(keys.values())), 3)
        self.assertEqual(built_from(self.game, [str(self.cheat)], lock_lines=french)["key"], keys["french"])
        # no lines (English, or a copy without the lock): the key as it always was
        self.assertEqual(built_from(self.game, [str(self.cheat)])["key"], keys["english"])
        self.assertNotIn("lock_lines", built_from(self.game, [str(self.plain)]))


class TheLauncher(Around):
    def launcher(self, start_game):
        from ruse_launcher.api import LauncherApi
        return LauncherApi(game_dir=self.game, home=self.home, instances=self.copy.parent, open_url=lambda u: None,
                           start_game=start_game, steam_running=lambda: True, wait=lambda s: None, find=lambda: None)

    def wait(self, api, job):
        end = time.time() + 30
        while api.job(job)["state"] == "running" and time.time() < end:
            time.sleep(0.02)
        return api.job(job)

    def played(self, api, game_code):
        """Play a cheat set in the Launcher: the game it starts closes at once with `game_code`; then wait for the
        match watch to finish. Returns what the page was told (guard_stop)."""
        api.guard_accept_terms()
        api.add_mod(str(self.cheat))
        set_id = api.new_set("Cheats", ["dev"])["set"]
        with mock.patch("rusemod.play.build_and_write", self.build), \
                mock.patch("rusemod.instance.needs_build", lambda *a: True):
            self.assertEqual(self.wait(api, api.play(set_id)["job"])["state"], "done")
            end = time.time() + 30
            seen = api.guard_stop()
            while seen["notice"] is None and seen["watching"] and time.time() < end:
                time.sleep(0.02)
                seen = api.guard_stop()
        return seen

    def notes(self):
        return [json.loads(p.read_text(encoding="utf-8")) for p in (self.home / guard.OUTBOX).glob("*.json")]

    def test_a_play_whose_cheat_copy_closed_with_the_number_files_the_note_and_says_so_once(self):
        """The whole way through the Launcher: Play (the player's language French) builds the cheat copy with its lock
        in French, starts the game, the game closes with RUSE Guard's close number, the match watch files the note
        (kept: no server set), and the page is told once, in French."""
        from ruse_launcher.api import words
        api = self.launcher(lambda exe: Process(fairplay.LOCK_EXIT))   # the game closes at once with the number
        api.set_pref("lang", "fr")
        seen = self.played(api, fairplay.LOCK_EXIT)
        self.assertEqual(self.builds[-1].lines, fairplay.lock_lines(words("fr")))
        self.assertEqual(seen["notice"], words("fr")["guard_closed_game"])
        self.assertEqual(api.guard_stop(), {"watching": False, "notice": None})   # said once
        self.assertEqual([n["evidence"]["stop"]["code"] for n in self.notes()], ["0x52474c4b"])
        self.assertIsNone(api.closing_check())   # the game has closed: nothing to ask

    def test_a_real_play_records_the_started_game_so_the_launcher_asks_while_it_runs(self):
        """Review finding 2: the question before closing rests on Play keeping the game it started (play.py: the
        Starter's game). A stand-in game that keeps running: through a real Play the Launcher's closing_check gives its
        question, in the player's language; once the game closes, it gives None."""
        from ruse_launcher.api import words
        running = Process(None)
        api = self.launcher(lambda exe: running)
        api.set_pref("lang", "fr")
        api.guard_accept_terms()
        api.add_mod(str(self.cheat))
        set_id = api.new_set("Cheats", ["dev"])["set"]
        with mock.patch("rusemod.play.build_and_write", self.build), \
                mock.patch("rusemod.instance.needs_build", lambda *a: True):
            self.assertEqual(self.wait(api, api.play(set_id)["job"])["state"], "done")
        try:
            check = api.closing_check()
            self.assertEqual(check, {"title": words("fr")["close_game_running_title"],
                                     "text": words("fr")["close_game_running_text"]})
        finally:
            running.code = 0   # the game closes (and the match watch's thread ends)
        self.assertIsNone(api.closing_check())
        end = time.time() + 30
        while api.guard_stop()["watching"] and time.time() < end:
            time.sleep(0.05)

    def test_control_an_ordinary_close_files_nothing_and_says_nothing(self):
        api = self.launcher(lambda exe: Process(0))
        self.assertEqual(self.played(api, 0), {"watching": False, "notice": None})
        self.assertEqual(self.notes(), [])

    def test_the_page_says_the_line_once_and_stops_asking(self):
        """The Launcher page's own watchGuard (app.js, run in Node with a stand-in API): it asks while RUSE Guard
        watches the game, says the line once, plainly (no troubleshooter or bug report link: nothing went wrong in
        the apps), stops asking once the watch has ended, and gives up after a few failed calls in a row."""
        import re
        import subprocess
        from test_scenarios_play_watch import LAUNCHER_UI, node, page_function
        exe = node()
        if exe is None:
            self.skipTest("no Node")
        js = LAUNCHER_UI.read_text(encoding="utf-8")
        tries = re.search(r"const GUARD_TRIES = (\d+);", js).group(1)
        cases = [[{"watching": True, "notice": None}, {"watching": True, "notice": None},
                  {"watching": False, "notice": "RUSE Guard closed the game."}],
                 [{"watching": False, "notice": None}],
                 [{"throw": True}] * 9]
        script = (f"let guardWatch = null;\nconst GUARD_TRIES = {tries};\n" + page_function(js, "watchGuard") +
                  "let answers = [], calls = 0, said = [], queue = [];\n"
                  "function api() { return { guard_stop: async () => { const a = answers[calls++];"
                  " if (!a || a.throw) throw new Error('down'); return a; } }; }\n"
                  "function setMessage(m, kind) { said.push([m, kind === undefined ? null : kind]); }\n"
                  "function setTimeout(fn, ms) { queue.push(fn); return queue.length; }\n"
                  "function clearTimeout(id) {}\n"
                  f"const cases = {json.dumps(cases)};\n"
                  "(async () => { const out = [];\n"
                  "  for (const c of cases) { answers = c; calls = 0; said = []; queue = []; watchGuard(0);\n"
                  "    while (queue.length) { await queue.shift()(); }\n"
                  "    out.push({ said, calls }); }\n"
                  "  console.log(JSON.stringify(out)); })();\n")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "guard.js"
            f.write_text(script, encoding="utf-8")
            ran = subprocess.run([exe, str(f)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(ran.returncode, 0, ran.stderr)
        self.assertEqual(json.loads(ran.stdout), [{"said": [["RUSE Guard closed the game.", None]], "calls": 3},
                                                  {"said": [], "calls": 1},
                                                  {"said": [], "calls": int(tries)}])
        self.assertIn('if (j.state === "done") watchGuard();', js)   # asked after a Play
        self.assertIn("watchGuard(0);", js)                           # and when the page opens

    def test_the_line_in_every_language(self):
        from ruse_launcher.api import words
        said = {lang: words(lang)["guard_closed_game"] for lang in LANGS}
        self.assertTrue(said["us"].startswith("RUSE Guard closed the game."))
        for lang in LANGS[1:]:
            self.assertNotEqual(said[lang], said["us"], lang)
            self.assertIn("RUSE Guard", said[lang], lang)

    def test_the_launcher_asks_before_it_closes_while_its_game_runs(self):
        """The owner's 23: "the Launcher asks before it closes while a game it started is still running"; Windows'
        own Yes/No box (rusemod.webui.ask_before_closing), in the Launcher's language."""
        from ruse_launcher.api import words
        api = self.launcher(lambda exe: None)
        self.assertIsNone(api.closing_check())          # no game started: it closes at once
        running = Process()
        api._starter.game = running
        for lang in LANGS:
            api.set_pref("lang", lang)
            ask = api.closing_check()
            self.assertEqual(ask, {"title": words(lang)["close_game_running_title"],
                                   "text": words(lang)["close_game_running_text"]}, lang)
            if lang != "us":
                self.assertNotEqual(ask["text"], words("us")["close_game_running_text"], lang)
        running.code = 0                                 # the game closed: nothing to ask any more
        self.assertIsNone(api.closing_check())

    def test_the_window_asks_with_the_launcher_s_words(self):
        """The window's closing handler (rusemod.webui.ask_before_closing) asks Windows' Yes/No box with the
        Launcher's words while the game runs: No keeps the Launcher open; once the game has closed, no box."""
        import sys
        from rusemod import browsermode, webui
        api = self.launcher(lambda exe: None)
        api._starter.game = Process()

        class Event:
            def __init__(self):
                self.handlers = []

            def __iadd__(self, handler):  # (pywebview's window events take their handlers with +=)
                self.handlers.append(handler)
                return self

        class Window:
            def __init__(self):
                self.events = type("Events", (), {})()
                self.events.closing = Event()
        window = Window()
        handlers = window.events.closing.handlers
        webui.ask_before_closing(window, api.closing_check)
        asked = []
        with mock.patch.object(sys, "platform", "win32"), \
                mock.patch.object(browsermode, "message_box", lambda text, title, flags: asked.append(title) or 7):
            self.assertFalse(handlers[0]())             # No (7): the Launcher stays open
            api._starter.game.code = 0
            self.assertTrue(handlers[0]())              # the game has closed: no box, it closes
        self.assertEqual(asked, ["Close RUSE Launcher?"])


class TheStudio(unittest.TestCase):
    def test_test_in_game_starts_no_match_watch_so_it_files_no_stop(self):
        """The owner's 23: "the Studio's Test in game sends no stop to our server". It passes the Studio's own words
        (the lock's lines in the player's language, for a cheat copy it builds) and no RUSE Guard watch."""
        from test_studio import WithMod

        class Studio(WithMod):
            def runTest(self):
                pass
        Studio.setUpClass()
        self.addCleanup(Studio.tearDownClass)
        case = Studio()
        case.setUp()
        api = case.api
        api.new_mod("Tank Test")
        api.set_pref("lang", "ger")
        self.addCleanup(api.set_pref, "lang", "us")
        with mock.patch.object(api._starter, "modded") as modded, \
                mock.patch.object(guard, "MatchWatch", side_effect=AssertionError("a match watch started")):
            job = api.test_in_game()["job"]
            end = time.time() + 30
            while api.job(job)["state"] == "running" and time.time() < end:
                time.sleep(0.02)
        self.assertEqual(api.job(job)["state"], "done")
        kwargs = modded.call_args.kwargs
        self.assertNotIn("guard", kwargs)
        from ruse_studio.api import words
        self.assertEqual(fairplay.lock_lines(kwargs["words"]), fairplay.lock_lines(words("ger")))
        self.assertIsNotNone(fairplay.lock_lines(words("ger")))
        shutil.rmtree(case.home, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
