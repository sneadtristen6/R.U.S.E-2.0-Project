"""Bug Watch says WHICH refusal or failure it was, not only its kind (rusemod.bugwatch reason_key, site_of).

Players' reports of 2026-11-02 to 11-09 said "BuildError at job:play", "BuildError at job:test_in_game" and
"FileNotFoundError at call:nations_view" and nothing more: three faults that could not be told apart from a hundred
others. Now every failed call and job is also counted, with the problems shown, by where in our own code it came
from ("play:rusemod.play:327": a module's name and a line, which the app's version turns back into the line), a build's
listed mistakes by where the build found each, the troubleshooter's checks that said something is wrong by their keys,
and the day's report names the game's build. A crash report's script error text is the copy that reaches the error's
own line. Never the words: they hold what the player typed and the names in the player's own mods.
No network, no game.
"""
import inspect
import os
import re
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import bugwatch, webui  # noqa: E402
from rusemod.build import BuildError, load_mod  # noqa: E402
from rusemod.patch import Finding  # noqa: E402

SRC = Path(__file__).resolve().parents[1] / "src"


def source_line(key: str) -> str:
    """The line of our code a "…:package.module:line" key names."""
    module, line = key.rsplit(":", 2)[-2:]
    return (SRC / (module.replace(".", "/") + ".py")).read_text(encoding="utf-8").splitlines()[int(line) - 1]


class Reasons(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TEMP"))
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()
        self._on = bugwatch.ON
        bugwatch.ON = True
        os.environ.pop("RUSE_NO_BUGWATCH", None)
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._current = bugwatch.Watch(self.home, "studio", "0.9.8.19", opener=mock.Mock())

    def tearDown(self):
        bugwatch.ON = self._on
        bugwatch._current = None
        self.tmp.cleanup()

    def day(self) -> dict:
        return bugwatch._current.days[bugwatch._today()]

    def test_a_failed_call_is_counted_by_where_in_our_code_it_came_from(self):
        typed = "Nick's Secret Mod"

        class Api:
            def load(self):
                load_mod(Path(self_tmp) / "a-mod", as_id=typed)   # the build refuses that id: BuildError in rusemod.build

        self_tmp = self.tmp.name
        page = webui.page_api(Api())
        with self.assertRaises(BuildError):
            page.load()
        day = self.day()
        self.assertEqual(day["calls"]["load"]["errors"], {"BuildError": 1})   # as before: the kind
        (key, n), = day["messages"].items()
        self.assertRegex(key, r"^load:rusemod\.build:\d+$")
        self.assertEqual(n, 1)
        self.assertIn("can't be a mod's id", source_line(key))             # the very line that refused
        self.assertNotIn("Secret", key)
        self.assertRegex(key, bugwatch.NAME_RE)                             # what the server takes as a key
        self.assertLessEqual(len(key), 64)

    def test_an_error_s_own_key_comes_first(self):
        error = BuildError("words for the player")
        error.words_key = "set_no_mods"
        self.assertEqual(bugwatch.reason_key("new_set", error), "set_no_mods")

    def test_an_error_from_outside_our_code_is_placed_at_our_line_that_called_it(self):
        def ours():
            return bugwatch.Watch("\0", "studio", "1").file.read_text()    # the library refuses; the caller is ours

        try:
            ours()
        except (OSError, ValueError) as exc:
            self.assertEqual(bugwatch.site_of(exc), "")                     # no line of our packages on the way here
        try:
            bugwatch.username_of(None)                                      # (fails inside rusemod.bugwatch itself)
        except Exception as exc:  # noqa: BLE001
            self.assertRegex(bugwatch.site_of(exc), r"^rusemod\.bugwatch:\d+$")
        self.assertEqual(bugwatch.site_of(ValueError("never raised")), "")
        self.assertIsNone(bugwatch.reason_key("x", ValueError("never raised")))

    def test_a_long_call_name_still_gives_a_key_the_server_takes(self):
        try:
            load_mod(Path(self.tmp.name) / "a-mod", as_id="NOT AN ID")
        except BuildError as exc:
            key = bugwatch.reason_key("a_call_with_a_very_long_name_" * 4, exc)
        self.assertLessEqual(len(key), 64)
        self.assertRegex(key, r":rusemod\.build:\d+$")
        self.assertRegex(key, bugwatch.NAME_RE)

    def test_a_finding_knows_where_the_build_made_it(self):
        line = inspect.currentframe().f_lineno + 1
        found = Finding("error", "Unit_Nicks_Tank: no such field")
        self.assertEqual(found.site, f"{__name__}:{line}")
        other = Finding("error", "Unit_Nicks_Tank: no such field")
        self.assertNotEqual(found.site, other.site)
        self.assertEqual(found, other)                                       # the site is not what a finding is
        self.assertNotIn("site", repr(found))
        self.assertEqual(Finding("note", "x", site="rusemod.build:7").site, "rusemod.build:7")

    def test_a_build_s_mistakes_are_counted_by_where_the_build_found_them(self):
        def work(say):
            try:
                load_mod(Path(self.tmp.name) / "a-mod", as_id="NOT AN ID")
            except BuildError as refused:
                refused.errors = ["Unit_Nicks_Tank: no such field", "Unit_Nicks_Tank: bad value", "another"]
                refused.error_sites = ["rusemod.build:1208", "rusemod.build:1208", "rusemod.patch:77"]
                raise

        bugwatch.call_started("test_in_game")
        job = webui.Job()
        job.start(work, "done", plain=(BuildError,))
        for _ in range(500):   # the job's own thread counts it right after it ends
            counted = bugwatch._current.days.get(bugwatch._today(), {}).get("jobs", {})
            if job.state != "running" and "test_in_game" in counted:
                break
            time.sleep(0.01)
        day = self.day()
        self.assertEqual(day["jobs"]["test_in_game"]["build_errors"], 3)
        messages = dict(day["messages"])
        self.assertEqual(messages.pop("mistake:rusemod.build:1208"), 2)
        self.assertEqual(messages.pop("mistake:rusemod.patch:77"), 1)
        (key, n), = messages.items()                                         # and the refusal itself, once
        self.assertRegex(key, r"^test_in_game:rusemod\.build:\d+$")
        self.assertEqual(n, 1)
        self.assertFalse(any("Nicks" in k for k in day["messages"]))

    def test_a_job_that_went_well_counts_no_reason(self):
        bugwatch._current.job("play", True, 3.0, None, 0, mistakes=["rusemod.build:1"])
        self.assertEqual(self.day()["messages"], {})

    def test_the_troubleshooter_s_bad_findings_are_counted_by_key(self):
        bugwatch.checks([{"key": "game", "level": "fail", "say": "doc_game_missing", "data": {"path": "C:/x"}},
                         {"key": "steam", "level": "ok"}, {"key": "drive", "level": "warn"},
                         {"key": "copies", "level": "info"}, {"level": "fail"}, "not a finding"])
        bugwatch.checks([{"key": "game", "level": "fail"}])
        self.assertEqual(self.day()["checks"], {"game": 2, "drive": 1})

    def test_the_day_s_report_names_the_game_s_build(self):
        watch = bugwatch._current
        watch.game_build("24670294")
        watch.game_build("C:\\Users\\Nick\\a path is never a build")       # not a build number: left out
        watch.game_build(None)
        day = bugwatch._today()
        self.assertEqual(watch.payload(day, watch.days[day])["setup"]["game_build"], "24670294")
        fresh = bugwatch.Watch(self.home / "other", "studio", "0.9.8.19", opener=mock.Mock())
        self.assertNotIn("game_build", fresh.payload(day, bugwatch._blank_day("0.9.8.19"))["setup"])

    def test_nothing_is_counted_when_bug_watch_is_off(self):
        bugwatch.turn_off(self.home)
        bugwatch.checks([{"key": "game", "level": "fail"}])
        bugwatch._current.game_build("24670294")
        try:
            load_mod(Path(self.tmp.name) / "a-mod", as_id="NOT AN ID")
        except BuildError as exc:
            bugwatch._current.call("load", 0.1, exc)
            bugwatch._current.job("play", False, 0.1, exc, 1, mistakes=["rusemod.build:1"])
        self.assertEqual(bugwatch._current.days, {})


HEAD = b"Traceback (most recent call last):\n"
FRAMES = (b'  File "datadir:\\codeia\\python\\eugen\\game\\world.py", line 114, in on_timer_task\n'
          b'  File "datadir:\\codeia\\python\\eugensolo\\leveldesignsolo\\condition.py", line 280, in scan\n')
LAST = b'  File "datadir:\\codeia\\python\\eugensolo\\leveldesignsolo\\condition.py", line 324, in get_unit_list\n'
ERROR = b"AttributeError: 'NoneType' object has no attribute 'radius'"
WHOLE = (HEAD + FRAMES + LAST + ERROR).decode()


class ScriptErrorText(unittest.TestCase):
    def test_the_copy_that_reaches_the_error_s_line_wins(self):
        cut = HEAD + FRAMES + b'  File "datadir:\\codeia\\python\\eugensolo\\leveldesigns'   # as two players' reports ended
        data = b"\x01\x02junk\x00" + cut + b"\x00" + b"\xff" * 40 + HEAD + FRAMES + LAST + ERROR + b"\n\xb0N\xd2v\x00more"
        self.assertEqual(bugwatch.script_error_text(data), WHOLE)
        self.assertEqual(bugwatch.script_error_text(HEAD + FRAMES + LAST + ERROR + b"\n\xab\x00" + b"\x00" + cut), WHOLE)

    def test_nothing_after_the_error_s_line_is_kept(self):
        for tail in (b"\n\xab", b"\n\xc8\n\n", b"\n", b"", b"\nsome other text in memory\nTraceback of nothing"):
            self.assertEqual(bugwatch.script_error_text(HEAD + FRAMES + LAST + ERROR + tail + b"\x00"), WHOLE, tail)

    def test_a_cut_copy_alone_is_still_given(self):
        cut = HEAD + FRAMES + b'  File "datadir:\\codeia\\python\\eugensolo\\leveldesigns'
        text = bugwatch.script_error_text(b"..." + cut + b"\x00")
        self.assertTrue(text.startswith("Traceback (most recent call last):"))
        self.assertTrue(text.endswith("leveldesigns"))
        self.assertEqual(bugwatch.script_error_text(b"..." + HEAD + b"\x00" + cut + b"\x00"), text)   # the longest

    def test_an_error_with_no_words_and_one_with_a_dotted_kind(self):
        self.assertTrue(bugwatch.script_error_text(HEAD + FRAMES + b"KeyboardInterrupt\n\x00").endswith("\nKeyboardInterrupt"))
        text = bugwatch.script_error_text(HEAD + FRAMES + b"parametres.Erreur: non\n\x00")
        self.assertTrue(text.endswith("\nparametres.Erreur: non"))

    def test_no_text_no_answer_and_a_long_one_is_bounded(self):
        self.assertEqual(bugwatch.script_error_text(b"\x00" * 100), "")
        many = HEAD + FRAMES * 400 + ERROR
        self.assertLessEqual(len(bugwatch.script_error_text(many)), bugwatch.TRACEBACK_CHARS)

    def test_control_characters_are_dropped_and_paths_still_go(self):
        text = bugwatch.script_error_text(HEAD + FRAMES + b"IOError: can't open C:\\Users\\Nick\\Documents\\a.txt\x07\n\x00")
        self.assertNotIn("\x07", text)
        self.assertNotIn("Nick", bugwatch.no_paths(text))


class TheTwoProjectRefusals(unittest.TestCase):
    """A required update and a copy that isn't confirmed stop Play at the same line of rusemod.play, so by the place
    alone they were one count. Each has a key of its own, and the day's report tells them apart."""

    def starter(self):
        from rusemod.play import Starter
        return Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: True,
                       wait=lambda s: None)

    def refused(self, **hooks):
        with tempfile.TemporaryDirectory() as tmp:
            starter = self.starter()
            for name, hook in hooks.items():
                setattr(starter, name, hook)
            with self.assertRaises(BuildError) as caught:
                starter.modded(Path(tmp), [], Path(tmp) / "copies" / "Modded game", "test", lambda line: None)
            self.assertFalse((Path(tmp) / "copies").exists())  # nothing made
            return caught.exception

    def test_each_has_its_own_key_and_the_player_still_reads_the_words(self):
        update = self.refused(required=lambda: "RUSE Launcher has a required update to install first.")
        self.assertEqual(bugwatch.reason_key("play", update), "play_update_required")
        copy = self.refused(owned=lambda game: "This copy isn't confirmed.")
        self.assertEqual(bugwatch.reason_key("play", copy), "play_copy_not_confirmed")
        self.assertEqual(str(copy), "This copy isn't confirmed.")
        for key in ("play_update_required", "play_copy_not_confirmed"):
            self.assertRegex(key, bugwatch.NAME_RE)  # what the server takes as a key

    def test_the_update_comes_first_and_the_copy_isn_t_asked_then(self):
        asked = []
        both = self.refused(required=lambda: "update first", owned=lambda game: asked.append(game) or "not confirmed")
        self.assertEqual((str(both), both.words_key, asked), ("update first", "play_update_required", []))

    def test_neither_refusing_no_key_is_made(self):
        with tempfile.TemporaryDirectory() as tmp:
            starter = self.starter()
            starter.required, starter.owned = (lambda: None), (lambda game: None)
            with self.assertRaises(Exception) as caught:  # (an empty folder is no game: the build says so)
                starter.modded(Path(tmp), [], Path(tmp) / "copies" / "Modded game", "test", lambda line: None)
            self.assertIsNone(getattr(caught.exception, "words_key", None))


if __name__ == "__main__":
    unittest.main()
