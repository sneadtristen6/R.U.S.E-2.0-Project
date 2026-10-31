"""Bug Watch (rusemod.bugwatch): opt-in counts, what's sent and when, crashes. No network: the sends go to a fake.

Checked our_tools.json: none of its tools reads a crash report; these tests read nothing of the game, only a small
crash report file they make themselves (one module named like the game).
"""
import json
import os
import struct
import sys
import tempfile
import time
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import bugwatch, home as homes, webui  # noqa: E402


class Answer:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Server:
    """A fake of the Bug Watch server: answers each POST with `status` and keeps what was sent."""

    def __init__(self, status=200):
        self.status, self.sent = status, []

    def __call__(self, req, timeout=None):
        self.sent.append(("/".join(req.full_url.rsplit("/", 2)[-2:]), json.loads(req.data.decode("utf-8"))))
        if self.status >= 400:
            raise urllib.error.HTTPError(req.full_url, self.status, "no", {}, None)
        return Answer(self.status)


def is_clean(value) -> bool:
    """No string or key anywhere that the server would refuse as a path (worker.js PATH_PATTERNS)."""
    if isinstance(value, dict):
        return all(is_clean(k) and is_clean(v) for k, v in value.items())
    if isinstance(value, list):
        return all(is_clean(v) for v in value)
    return not (isinstance(value, str) and bugwatch.LOOKS_LIKE_PATH.search(value))


class BugWatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TEMP"))
        self.home = Path(self.tmp.name)
        self._on = bugwatch.ON
        bugwatch.ON = True
        os.environ.pop("RUSE_NO_BUGWATCH", None)

    def tearDown(self):
        bugwatch.ON = self._on
        bugwatch._current = None
        self.tmp.cleanup()

    def watch(self, server=None, clock=time.time):
        return bugwatch.Watch(self.home, "studio", "0.9.8.9", opener=server or Server(), clock=clock)


class Consent(BugWatchTest):
    def test_on_in_the_code_for_the_release(self):
        self.assertTrue(self._on)  # switched on for the release (the owner, 2026-10-31); the opt-in below still decides

    def test_nothing_is_counted_without_the_players_yes(self):
        w = self.watch()
        w.call("build_map", 0.5)
        self.assertEqual(w.days, {})
        self.assertFalse(bugwatch.enabled(self.home))

    def test_turn_on_makes_an_id_and_a_username(self):
        out = bugwatch.turn_on(self.home, "Nick")
        values = homes.settings(self.home)
        self.assertEqual(len(values["player"]["id"]), 32)
        self.assertRegex(values["player"]["name"], r"^Nick#\d{4}$")
        self.assertEqual(out["code"], values["player"]["id"][:8])
        self.assertTrue(bugwatch.enabled(self.home))
        again = bugwatch.turn_on(self.home, values["player"]["name"])  # the same ID, the name kept as it is
        self.assertEqual(again["code"], out["code"])
        self.assertEqual(homes.settings(self.home)["player"]["name"], values["player"]["name"])

    def test_set_username_shares_an_id_without_turning_bugwatch_on(self):
        # the agreement's guard-only case (program check on, Bug Watch off) still needs a username (plan §3a)
        out = bugwatch.set_username(self.home, "Nick")
        values = homes.settings(self.home)
        self.assertRegex(values["player"]["name"], r"^Nick#\d{4}$")
        self.assertEqual(len(values["player"]["id"]), 32)
        self.assertEqual(out["code"], values["player"]["id"][:8])
        self.assertFalse((values.get("bugwatch") or {}).get("on"))   # Bug Watch is left off
        self.assertFalse(bugwatch.enabled(self.home))
        on = bugwatch.turn_on(self.home, values["player"]["name"])   # ticking it later keeps the same ID and name
        self.assertEqual(on["code"], out["code"])
        self.assertEqual(homes.settings(self.home)["player"]["name"], values["player"]["name"])
        self.assertTrue(bugwatch.enabled(self.home))

    def test_set_username_works_even_when_bugwatch_is_off_in_code(self):
        bugwatch.ON = False   # the username is for RUSE Guard too, so it must work before Bug Watch is switched on
        out = bugwatch.set_username(self.home, "Ann")
        self.assertRegex(out["name"], r"^Ann#\d{4}$")
        self.assertEqual(len(homes.settings(self.home)["player"]["id"]), 32)

    def test_a_username_is_made_safe(self):
        self.assertEqual(bugwatch.username_of("  a/b\\c`d#e  ", 1234), "abcde#1234")
        self.assertEqual(bugwatch.username_of("", 42), "player#0042")
        self.assertLessEqual(len(bugwatch.username_of("x" * 99, 1000)), 40)

    def test_turn_off_forgets_everything(self):
        bugwatch.turn_on(self.home, "Nick")
        w = self.watch()
        w.call("x", 0.1)
        w.save()
        w.crash({"kind": "app", "error": "KeyError", "frames": []}, send=False)
        bugwatch.turn_off(self.home)
        self.assertFalse(bugwatch.enabled(self.home))
        self.assertNotIn("player", homes.settings(self.home))
        self.assertEqual(list((self.home / bugwatch.FOLDER).rglob("*.json")), [])

    def test_the_id_stays_for_ruse_guards_program_check(self):
        bugwatch.turn_on(self.home, "Nick")
        values = homes.settings(self.home)
        values["guard"] = {"terms": 1}   # RUSE Guard accepted: its mandatory program check keeps the shared username
        homes.save_settings(self.home, values)
        bugwatch.turn_off(self.home)
        self.assertIn("player", homes.settings(self.home))

    def test_the_environment_switch(self):
        bugwatch.turn_on(self.home, "Nick")
        with mock.patch.dict(os.environ, {"RUSE_NO_BUGWATCH": "1"}):
            self.assertFalse(bugwatch.enabled(self.home))


class Counting(BugWatchTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")

    def test_calls_jobs_and_the_rest(self):
        w = self.watch()
        w.call("build_map", 0.4)
        w.call("build_map", 12.0, OSError("disk"))
        w.call("open project", 0.1)  # a space isn't in a name: it becomes _
        w.job("play", True, 70)
        w.job("play", False, 2, error=ValueError("x"), build_errors=3)
        w.count("screens", "units")
        w.count("messages", "bad_name")
        w.count("checks", "game_folder_missing")
        w.count("updates", "installed")
        w.count("updates", "nonsense")  # not one of the three: ignored
        w.played(42.4, ["cool-mod@1.2", "x:\\bad@1"], 2)
        day = w.days[bugwatch._today()]
        self.assertEqual(day["calls"]["build_map"], {"n": 2, "failed": 1, "errors": {"OSError": 1},
                                                     "time": [1, 0, 1, 0, 0]})
        self.assertIn("open_project", day["calls"])
        self.assertEqual(day["jobs"]["play"]["done"], 1)
        self.assertEqual(day["jobs"]["play"]["failed"], 1)
        self.assertEqual(day["jobs"]["play"]["build_errors"], 3)
        self.assertEqual(day["jobs"]["play"]["time"], [0, 1, 0, 1, 0])
        self.assertEqual(day["updates"]["installed"], 1)
        self.assertEqual(day["played"], {"total": 42, "mods": {"cool-mod@1.2": 42}})
        self.assertEqual(day["own_mods"], 2)

    def test_counts_survive_a_restart(self):
        w = self.watch()
        w.call("a", 0.1)
        w.save()
        self.assertEqual(self.watch().days[bugwatch._today()]["calls"]["a"]["n"], 1)


class WhatIsSent(BugWatchTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")

    def test_a_day_fits_the_servers_rules(self):
        w = self.watch()
        for i in range(200):  # more calls than the server takes
            for _ in range(i % 5 + 1):
                w.call(f"call{i:03d}", 0.2, KeyError() if i % 3 else None)
        for i in range(40):
            w.job(f"job{i}", i % 2 == 0, 3, RuntimeError())
        out = w.payload(bugwatch._today(), w.days[bugwatch._today()])
        self.assertEqual(out["v"], 1)
        self.assertEqual(out["app"], "studio")
        self.assertEqual(len(out["id"]), 32)
        self.assertRegex(out["user"], r"^Nick#\d{4}$")
        self.assertLessEqual(len(out["calls"]), 150)
        self.assertLessEqual(len(out["jobs"]), 30)
        kinds = sum(len(v.get("errors", {})) for g in ("calls", "jobs") for v in out[g].values())
        self.assertLessEqual(kinds, 100)
        self.assertLessEqual(len(json.dumps(out, separators=(",", ":")).encode()), 64 * 1024)
        for name in list(out["calls"]) + list(out["jobs"]):
            self.assertRegex(name, r"^[A-Za-z0-9_.:-]{1,64}$")
        self.assertTrue(is_clean(out))
        self.assertIn("call199", out["calls"])  # the most-used are the ones kept

    def test_finished_days_go_to_the_outbox_and_old_ones_are_dropped(self):
        w = self.watch()
        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        too_old = (now - timedelta(days=31)).strftime("%Y-%m-%d")
        w.days = {yesterday: bugwatch._blank_day("0.9.8.8"), too_old: bugwatch._blank_day("0.9.8.1")}
        w.days[yesterday]["calls"]["x"] = {"n": 1, "failed": 0, "errors": {}, "time": [1, 0, 0, 0, 0]}
        self.assertEqual(w.roll(), 1)
        sent = json.loads((w.outbox / f"day-studio-{yesterday}.json").read_text())
        self.assertEqual(sent["day"], yesterday)
        self.assertEqual(sent["version"], "0.9.8.8")  # the version of that day, not today's
        self.assertEqual(w.days, {})

    def test_sending(self):
        server = Server(200)
        w = self.watch(server)
        w._write_out("day-studio-2026-10-29.json", {"v": 1, "day": "2026-10-29"})
        w.crash({"kind": "app", "error": "KeyError", "frames": []}, send=False)
        self.assertEqual(w.send_waiting(), {"sent": 2, "waiting": 0, "dropped": 0})
        self.assertEqual(sorted(p for p, _ in server.sent), ["v1/crash", "v1/day"])
        self.assertEqual(list(w.outbox.glob("*.json")), [])
        self.assertGreater(homes.settings(self.home)["bugwatch"]["last_send"], 0)

    def test_days_go_once_a_day_crashes_at_once(self):
        server = Server(200)
        w = self.watch(server)
        values = homes.settings(self.home)
        values["bugwatch"]["last_send"] = int(time.time())  # just sent
        homes.save_settings(self.home, values)
        w._write_out("day-studio-2026-10-29.json", {"v": 1})
        w.crash({"kind": "app", "error": "KeyError", "frames": []}, send=False)
        self.assertEqual(w.send_waiting(), {"sent": 1, "waiting": 1, "dropped": 0})
        self.assertEqual([p for p, _ in server.sent], ["v1/crash"])

    def test_switched_off_or_offline_waits_refused_goes(self):
        for status, kept in ((503, True), (500, True), (400, False), (413, False), (429, False)):
            w = self.watch(Server(status))
            w.crash({"kind": "app", "error": "KeyError", "frames": []}, send=False)
            w.send_waiting()
            self.assertEqual(bool(list(w.outbox.glob("*.json"))), kept, status)
            for p in w.outbox.glob("*.json"):
                p.unlink()

    def test_nothing_goes_without_the_players_yes(self):
        server = Server(200)
        w = self.watch(server)
        w._write_out("day-studio-2026-10-29.json", {"v": 1})
        bugwatch.turn_off(self.home)
        w.send_waiting(force=True)
        self.assertEqual(server.sent, [])


class Crashes(BugWatchTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")

    def test_an_app_crash_names_only_our_own_lines(self):
        w = self.watch()
        from types import SimpleNamespace as Frame  # (a Mock takes name= as its own label)
        fake = [Frame(filename="C:\\Python312\\Lib\\json\\decoder.py", lineno=3, name="decode"),
                Frame(filename="D:\\RUSE-2.0\\code\\src\\ruse_studio\\api.py", lineno=9, name="open_project")]
        with mock.patch.object(w, "send_waiting"), mock.patch("traceback.extract_tb", return_value=fake):
            w.app_crash(ValueError, ValueError("x"), None)
        files = list(w.outbox.glob("crash-*.json"))
        self.assertEqual(len(files), 1)
        body = json.loads(files[0].read_text())
        self.assertEqual(body["kind"], "app")
        self.assertEqual(body["error"], "ValueError")
        self.assertEqual(body["frames"], [["ruse_studio/api.py", 9, "open_project"]])
        self.assertTrue(is_clean(body))
        self.assertEqual(w.days[bugwatch._today()]["app_crashes"], 1)

    def test_no_paths(self):
        text = bugwatch.no_paths('File "D:\\RUSE-2.0\\tests\\instances\\x\\scripts\\a.py", line 4 C:/Users/me/x')
        self.assertNotRegex(text, r"(?:^|[^A-Za-z0-9])[A-Za-z]:[\\/]")
        self.assertIn("a.py", text)
        self.assertTrue(is_clean(text))

    def dump(self, code=0x29A, address=0x7FF612341234, base=0x7FF612340000, extra=b""):
        """A small crash report file: the header, an ExceptionStream, a ModuleListStream with one module, and `extra`."""
        name = "C:\\Games\\R.U.S.E\\RUSE.exe".encode("utf-16-le")
        header = b"MDMP" + struct.pack("<IIIIIQ", 0xA793, 2, 32, 0, 0, 0)
        exc_at = 32 + 24
        exception = struct.pack("<II", 1, 0) + struct.pack("<IIQQII", code, 0, 0, address, 0, 0) + b"\0" * 120
        mods_at = exc_at + len(exception)
        name_at = mods_at + 4 + 108
        module = struct.pack("<QIIII", base, 0x200000, 0, 0, name_at) + b"\0" * (108 - 24)
        mods = struct.pack("<I", 1) + module
        directory = struct.pack("<III", 6, len(exception), exc_at) + struct.pack("<III", 4, len(mods), mods_at)
        return header + directory + exception + mods + struct.pack("<I", len(name)) + name + extra

    def test_reading_a_game_crash_report(self):
        text = b'Traceback (most recent call last):\n  File "D:\\RUSE-2.0\\x\\events.py", line 40\nKeyError: 1\x00'
        p = self.home / "report.dmp"
        p.write_bytes(self.dump(extra=b"\0junk\0" + text))
        found = bugwatch.read_dump(p)
        self.assertEqual(found["code"], "0x29a")
        self.assertEqual(found["module"], "RUSE.exe")
        self.assertEqual(found["offset"], "0x1234")
        self.assertIn("KeyError: 1", found["traceback"])
        self.assertNotIn("D:\\", found["traceback"])
        p.write_bytes(self.dump(code=0xC0000005))
        self.assertNotIn("traceback", bugwatch.read_dump(p))
        p.write_bytes(b"not a dump")
        self.assertIsNone(bugwatch.read_dump(p))

    def test_the_game_watch(self):
        local = self.home / "local"
        rpt = local / "Temp" / "CrashRpt_x"
        rpt.mkdir(parents=True)
        polls = iter([None, None, 0])

        class Game:
            def poll(self):
                return next(polls)

        times = iter([1000.0, 1600.0, 1600.0, 1600.0])
        w = self.watch()

        def sleep(_seconds):
            (rpt / "report.dmp").write_bytes(self.dump(code=0xC0000005))
            os.utime(rpt / "report.dmp", (1500, 1500))

        g = bugwatch.GameWatch(w, Game(), ["cool-mod@1.2"], 1, sleep=sleep, clock=lambda: next(times),
                               local=str(local))
        with mock.patch.object(w, "send_waiting"):
            g.run()
        day = w.days[bugwatch._today()]
        self.assertEqual(day["played"]["total"], 10)
        crashes = [json.loads(p.read_text()) for p in w.outbox.glob("crash-*.json")]
        self.assertEqual(len(crashes), 1)
        self.assertEqual(crashes[0]["kind"], "game")
        self.assertEqual(crashes[0]["code"], "0xc0000005")
        self.assertEqual(crashes[0]["mods"], ["cool-mod@1.2"])
        self.assertEqual(crashes[0]["own_mods"], 1)
        self.assertTrue(is_clean(crashes[0]))

    def test_mods_of(self):
        listed = self.home / "listed"
        listed.mkdir()
        (listed / "mod.toml").write_text('[mod]\nid = "cool-mod"\nversion = "1.2"\n')
        (listed / "tags.toml").write_text('tags = ["units"]\n')
        own = self.home / "own"
        own.mkdir()
        (own / "mod.toml").write_text('[mod]\nid = "secret"\nversion = "0.1"\n')
        self.assertEqual(bugwatch.mods_of([listed, own]), (["cool-mod@1.2"], 1))


class Hooks(BugWatchTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._current = self.watch()

    def test_window_calls_and_jobs_are_counted(self):
        jobs = {}

        class Api:
            def good(self):
                return 1

            def bad(self):
                raise ValueError("no")

            def long(self):
                job = webui.Job()
                jobs["j"] = job
                return job.start(lambda say: say("x"), "done")

        page = webui.page_api(Api())
        self.assertEqual(page.good(), 1)
        with self.assertRaises(ValueError):
            page.bad()
        page.long()
        for _ in range(200):
            if jobs["j"].state != "running":
                break
            time.sleep(0.02)
        time.sleep(0.1)
        day = bugwatch._current.days[bugwatch._today()]
        self.assertEqual(day["calls"]["good"]["n"], 1)
        self.assertEqual(day["calls"]["bad"]["errors"], {"ValueError": 1})
        self.assertEqual(day["jobs"]["long"]["done"], 1)  # the job takes the name of the call that started it

    def test_its_own_calls_arent_counted(self):
        started = bugwatch.call_started("bugwatch_status")
        bugwatch.call_ended("bugwatch_status", started)
        self.assertNotIn("bugwatch_status", bugwatch._current.days.get(bugwatch._today(), {}).get("calls", {}))


class TheCardInBothApps(unittest.TestCase):
    """The Bug Watch Settings card is in the Launcher AND the Studio, with the same words in all ten languages and the
    same controls and app.js wiring. Guards the Studio mirror against drifting from the Launcher (card added 2026-10-30)."""

    SRC = Path(__file__).resolve().parents[1] / "src"
    LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")
    KEYS = ("set_bugwatch_title", "set_bugwatch_help", "bugwatch_on_label", "bugwatch_name_hint", "bugwatch_save",
            "bugwatch_code", "bugwatch_show", "bugwatch_need_name", "bugwatch_now_on", "bugwatch_now_off",
            "tip_bugwatch_on", "tip_bugwatch_name", "tip_bugwatch_save", "tip_bugwatch_show")
    IDS = ("set-bugwatch", "bugwatch-name", "bugwatch-save", "bugwatch-on", "bugwatch-on-label", "bugwatch-code",
           "bugwatch-show", "bugwatch-sent", "bugwatch-note")
    FUNCS = ("loadBugwatch", "renderBugwatch", "changeBugwatch", "showBugwatch")

    def _words(self, app):
        import tomllib
        return tomllib.load(open(self.SRC / app / "words.toml", "rb"))

    def test_both_apps_have_every_word_in_every_language(self):
        for app in ("ruse_launcher", "ruse_studio"):
            words = self._words(app)
            for key in self.KEYS:
                self.assertIn(key, words, f"{app}: {key} missing")
                self.assertEqual([lang for lang in self.LANGS if not words[key].get(lang)], [],
                                 f"{app}: {key} missing a language")

    def test_both_apps_have_the_controls_and_wiring(self):
        for app in ("ruse_launcher", "ruse_studio"):
            html = (self.SRC / app / "ui" / "index.html").read_text(encoding="utf-8")
            for name in self.IDS:
                self.assertIn(f'id="{name}"', html, f"{app}: {name} not in index.html")
            js = (self.SRC / app / "ui" / "app.js").read_text(encoding="utf-8")
            for func in self.FUNCS:
                self.assertIn(func, js, f"{app}: {func} not in app.js")
            self.assertIn('{ id: "bugwatch"', js, f"{app}: the bugwatch Settings entry is missing")


class TheAgreementScreen(unittest.TestCase):
    """The first-start agreement + username is ONE shared screen (rusemod/sharedui/agreement.js) that both apps load
    and the web layer serves at shared/ (plan §3a; built then made shared 2026-10-30). Both apps call it at startup,
    carry its words, and expose the guard calls it needs (rusemod.guardcalls.GuardCalls)."""

    SRC = Path(__file__).resolve().parents[1] / "src"
    KEYS = ("agree_title", "agree_intro", "agree_guard_title", "agree_guard",
            "agree_full_toggle", "agree_full", "agree_accept_note", "agree_accept", "username_title", "username_help",
            "username_save", "username_need")
    IDS = ("agree", "agree-bugwatch", "agree-bugwatch-row", "agree-full", "agree-accept",
           "username", "username-name", "username-save")

    def test_one_shared_module_has_the_screen_and_flow(self):
        js = (self.SRC / "rusemod" / "sharedui" / "agreement.js").read_text(encoding="utf-8")
        for name in self.IDS:
            self.assertIn(f'id="{name}"', js, f"{name} not injected by the shared module")
        self.assertIn("window.Agreement", js)
        for call in ("guard_status", "guard_accept_terms", "set_username", "bugwatch_on"):
            self.assertIn(call, js, f"{call} not wired in the shared module")
        # the program check is mandatory, part of RUSE Guard -- not a choice: no scan checkbox, no guard_set_scan call
        self.assertNotIn("agree-scan", js)
        self.assertNotIn("guard_set_scan", js)

    def test_both_apps_load_and_call_the_one_module(self):
        for app in ("ruse_launcher", "ruse_studio"):
            html = (self.SRC / app / "ui" / "index.html").read_text(encoding="utf-8")
            self.assertIn('src="shared/agreement.js"', html, f"{app} doesn't load the shared module")
            js = (self.SRC / app / "ui" / "app.js").read_text(encoding="utf-8")
            self.assertIn("window.Agreement.open", js, f"{app} doesn't call the shared agreement")

    def test_both_apps_have_the_words(self):
        import tomllib
        for app in ("ruse_launcher", "ruse_studio"):
            words = tomllib.load(open(self.SRC / app / "words.toml", "rb"))
            for key in self.KEYS:
                self.assertIn(key, words, f"{app}: {key} missing")
                self.assertTrue(words[key].get("us"), f"{app}: {key} has no English")

    def test_the_web_layer_serves_it_and_both_apis_have_the_guard_calls(self):
        webui = (self.SRC / "rusemod" / "webui.py").read_text(encoding="utf-8")
        self.assertIn('"shared": SHARED_UI', webui, "webui doesn't mount shared/")
        # the mount must be on BOTH paths: the window (serve) AND the web browser (_in_browser), or --browser 404s
        # shared/agreement.js and the agreement never shows there
        browser_body = webui.split("def _in_browser", 1)[-1].split("\ndef ", 1)[0]
        self.assertIn('"shared": SHARED_UI', browser_body, "the --browser path (_in_browser) doesn't mount shared/")
        for app in ("ruse_launcher", "ruse_studio"):
            api = (self.SRC / app / "api.py").read_text(encoding="utf-8")
            self.assertIn("GuardCalls", api, f"{app} api doesn't include GuardCalls")


if __name__ == "__main__":
    unittest.main()
