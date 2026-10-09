"""The apps' start-up log (rusemod.startlog): each start one line of seconds since the program started, written as it
goes, the last 20 kept, never more than 25 KB, never stopping an app; the window's steps and the page's first calls
(rusemod.webui.open_window, with a stand-in for pywebview); and the troubleshooter's report carrying it."""
import inspect
import os
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

from rusemod import doctor, startlog, webui


def entries(line: str) -> dict:
    """A log line's entries: name -> (seconds, duration or None; "?" while unanswered)."""
    out = {}
    for part in line.split(": ", 1)[1].removesuffix(" ...").split(", "):
        name, _, value = part.rpartition(" ")
        at, _, took = value.partition("+")
        out[name] = (float(at), None if not took else took if took == "?" else float(took))
    return out


class Api(startlog.StartCalls):
    """A window back end like the apps': plain methods, a property, a job."""

    def __init__(self):
        self.jobs = {}

    def status(self):
        return {"ready": True}

    def units(self, lang="base", kind="all"):
        return [lang, kind]

    def slow(self):
        time.sleep(0.05)
        return {}

    def broken(self):
        raise ValueError("no")

    def backup_make(self, replace=False):
        self.jobs["j1"] = "running"
        return {"job": "j1"}

    def job(self, job_id, since=0):
        return {"id": job_id, "state": self.jobs.get(job_id, "failed"), "lines": [], "count": 0}

    def both(self):  # one method calling others, as set_pref calls prefs
        return [self.status(), self.units()]

    @property
    def cache_dir(self):
        raise AssertionError("a property is never read by the log")


class Base(unittest.TestCase):
    def setUp(self):
        startlog.stop()
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(startlog.stop)

    def log(self, app="studio", version="9.9"):
        return startlog.begin(app, version, home=self.home)

    def lines(self, app="studio"):
        """The log file's lines, the latest changes in (the writer thread writes them WAIT seconds later)."""
        if startlog.current() is not None:
            startlog.current().flush()
        path = self.home / "logs" / f"{app}-start.log"
        return path.read_text(encoding="utf-8").splitlines() if path.is_file() else []


class OneStart(Base):
    def test_nothing_is_written_before_go_then_each_step_at_once(self):
        log = self.log()
        log.mark("imports")
        log.mark("api")
        self.assertEqual(self.lines(), [])  # a self-test stops it before this point
        log.go()
        self.assertEqual(len(self.lines()), 1)
        log.mark("window")
        line = self.lines()[0]
        self.assertTrue(line.startswith(time.strftime("%Y-%m-%d ", time.localtime(log.started)) ), line)
        self.assertIn(" studio 9.9: python ", line)
        got = entries(line)
        self.assertEqual(list(got), ["python", "imports", "api", "window"])
        self.assertTrue(got["python"][0] <= got["imports"][0] <= got["api"][0] <= got["window"][0])
        log.mark("window")  # a step marked again keeps its first time
        self.assertEqual(entries(self.lines()[0])["window"], got["window"])

    def test_seconds_count_from_the_programs_start(self):
        started = startlog.process_start()
        if sys.platform == "win32":
            self.assertIsNotNone(started)
            self.assertTrue(time.time() - 86_400 < started <= time.time())  # this test's own Python, today
            self.assertAlmostEqual(self.log().started, started, places=3)
        else:
            self.assertIsNone(started)
        self.assertEqual(startlog._num(4.5), "4.5")
        self.assertEqual(startlog._num(0.001), "0")
        self.assertEqual(startlog._num(360.0), "360")
        self.assertEqual(startlog._num(12.345), "12.35")

    def test_calls_jobs_and_the_pages_ready(self):
        log = self.log()
        log.go()
        api = startlog.timed(Api(), log)
        self.assertEqual(api.units("fr", "air"), ["fr", "air"])  # answers as before
        api.units("us")  # the first of each kind only
        api.slow()
        with self.assertRaises(ValueError):
            api.broken()  # its error goes on to the window, its time is kept
        api.job("j1")  # following a job is never listed
        self.assertEqual(api.backup_make(), {"job": "j1"})
        api.start_mark("ready")
        api.start_mark("<b>anything else</b>")  # only the page's own marks
        api.job("j1")
        api.jobs["j1"] = "done"
        api.job("j1")
        api.job("j1")  # an ended job is noted once
        got = entries(self.lines()[0])
        self.assertEqual(list(got), ["python", "units", "slow", "broken", "backup_make", "ready", "backup_make done"])
        self.assertGreaterEqual(got["slow"][1], 0.04)
        self.assertNotIn("start_mark", got)
        self.assertNotIn("job", got)

    def test_a_call_that_never_answers_still_shows(self):
        log = self.log()
        log.go()
        log.call_started("status")
        self.assertEqual(entries(self.lines()[0])["status"][1], "?")

    def test_the_window_gets_the_same_parameters(self):
        """pywebview hands a method to the page by reading its parameters (getfullargspec(...).args[1:])."""
        plain = Api()
        api = startlog.timed(Api(), self.log())
        for name in ("status", "units", "backup_make", "job", "start_mark"):
            self.assertTrue(inspect.isfunction(getattr(api, name)) or inspect.ismethod(getattr(api, name)))
            self.assertEqual(inspect.getfullargspec(getattr(api, name)).args[1:],
                             inspect.getfullargspec(getattr(plain, name)).args[1:], name)
        self.assertEqual(api.units.__doc__, Api.units.__doc__)

    def test_a_back_end_that_cant_be_wrapped_stays_as_it_is(self):
        class Fixed:  # no instance attributes can be set
            __slots__ = ()

            def status(self):
                return {"ready": True}

        api = startlog.timed(Fixed(), self.log())
        self.assertEqual(api.status(), {"ready": True})

    def test_first_calls_stop_counting_after_the_start(self):
        log = self.log()
        log.go()
        for n in range(startlog.CALLS + 5):
            log.call_ended(log.call_started(f"call{n}"), f"call{n}")
        self.assertEqual(len(log.calls), startlog.CALLS)
        late = self.log()
        late.calls.clear()
        late.ready_at = late._now() - startlog.AFTER_READY - 1  # the page was ready long ago
        self.assertIsNone(late.call_started("export_mod"))
        late.mark("closed")
        self.assertFalse(late.watching())


class TheFile(Base):
    def test_the_last_20_starts_and_never_more_than_25_kb(self):
        logs = self.home / "logs"
        logs.mkdir()
        (logs / "studio-start.log").write_text("x" * 5000 + "\n" + "\n".join(f"old {n}" for n in range(30)) + "\n",
                                               encoding="utf-8")
        log = self.log()
        log.go()
        for n in range(200):  # far more calls than a line holds: the latest give way
            log.call_ended(log.call_started(f"a_rather_long_call_name_that_goes_on_and_on_and_on_{n}"), "x")
        log.mark("ready")
        log.mark("closed")  # written at once, and the writer thread stops
        lines = self.lines()
        self.assertEqual(len(lines), startlog.KEEP)
        self.assertEqual(lines[:-1], [f"old {n}" for n in range(11, 30)])
        self.assertLessEqual(len(lines[-1]), startlog.LINE)
        self.assertTrue(lines[-1].endswith(" ..."), lines[-1])
        self.assertIn("ready", entries(lines[-1]))  # the steps stay
        self.assertLess((logs / "studio-start.log").stat().st_size, 25_000)
        self.assertEqual([p.name for p in logs.iterdir()], ["studio-start.log"])  # no temporary file left

    def test_a_log_that_cant_be_written_never_stops_the_app(self):
        (self.home / "logs" / "studio-start.log").mkdir(parents=True)  # a folder where the file should be
        log = self.log()
        log.go()
        log.mark("window")
        startlog.timed(Api(), log).status()
        log.mark("closed")
        self.assertEqual(startlog.recent("studio", self.home), [])
        self.assertEqual([p.name for p in (self.home / "logs").iterdir()], ["studio-start.log"])  # no file left

    def test_recent_starts_for_the_report(self):
        for n in range(8):
            startlog.stop()
            log = startlog.begin("launcher", "1.0", home=self.home)
            log.started -= 10 * (8 - n)  # each start its own second
            log.go()
        got = startlog.recent("launcher", self.home)
        self.assertEqual(len(got), startlog.REPORT)
        self.assertTrue(all(" launcher 1.0: python " in line for line in got))
        self.assertEqual(startlog.recent("studio", self.home), [])

    def test_the_troubleshooters_report_carries_them(self):
        text = doctor.report([], "RUSE Studio", "9.9", ["2026-10-04 14:02:11 studio 9.9: python 0.41, ready 4.62"])
        self.assertIn("Start-up times, in seconds since the program started", text)
        self.assertTrue(text.endswith("\n  2026-10-04 14:02:11 studio 9.9: python 0.41, ready 4.62"), text)
        self.assertNotIn("Start-up", doctor.report([], "RUSE Studio", "9.9"))

    def test_both_apps_reports(self):
        from ruse_launcher.api import LauncherApi
        from ruse_studio.api import StudioApi
        from rusemod.play import Starter
        game = self.home / "game"
        game.mkdir()
        (game / "RUSE.exe").write_bytes(b"MZ")
        for app, make in (("studio", lambda: StudioApi(game_dir=game, home=self.home, instances=self.home / "c",
                                                       starter=Starter(steam_running=lambda: True))),
                          ("launcher", lambda: LauncherApi(game_dir=game, home=self.home, instances=self.home / "c",
                                                           steam_running=lambda: True))):
            startlog.stop()
            log = startlog.begin(app, "9.9", home=self.home)
            log.go()
            api = make()
            api.start_mark("ready")
            log.flush()  # the writer thread would write it a moment later
            with mock.patch("rusemod.winfiles.processes", return_value=[]):
                report = api.troubleshoot()["report"]
            self.assertIn(f" {app} 9.9: python ", report)
            self.assertIn(", ready ", report)


class FakeEvent:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def set(self):
        for handler in self.handlers:  # pywebview calls a handler without parameters with none
            handler()


def fake_webview(calls):
    """A stand-in for pywebview: start() shows the window, loads the page and makes the page's `calls` the way
    pywebview does (the method looked up by name on the API object, for each call)."""
    module = types.ModuleType("webview")

    def create_window(title, url, js_api=None, **kwargs):
        module.window = types.SimpleNamespace(api=js_api, url=url, events=types.SimpleNamespace(
            shown=FakeEvent(), before_load=FakeEvent(), loaded=FakeEvent()))
        return module.window

    def start(**kwargs):
        w = module.window
        for event in (w.events.shown, w.events.before_load, w.events.loaded):
            event.set()
        for name, args in calls:
            getattr(w.api, name)(*args)

    module.create_window, module.start = create_window, start
    return module


class TheWindow(Base):
    def test_each_step_from_the_window_to_the_pages_first_calls(self):
        log = self.log()
        log.mark("imports")
        log.mark("api")
        log.go()
        api = Api()
        calls = [("status", []), ("units", ["fr"]), ("backup_make", []), ("start_mark", ["ready"]), ("job", ["j1"])]
        with mock.patch.dict(sys.modules, {"webview": fake_webview(calls)}), \
                mock.patch.object(webui, "web_engine", return_value="ok"):
            self.assertEqual(webui.open_window("RUSE Studio", Path(webui.__file__).parent, "x.html", api), 0)
        got = entries(self.lines()[0])
        self.assertEqual(list(got), ["python", "imports", "api", "pywebview", "engine", "window", "shown", "page",
                                     "loaded", "status", "units", "backup_make", "ready", "closed"])
        self.assertTrue(all(got[a][0] <= got[b][0] for a, b in zip(got, list(got)[1:])))

    def test_only_the_pages_own_calls_are_listed(self):
        log = self.log()
        log.go()
        with mock.patch.dict(sys.modules, {"webview": fake_webview([("both", []), ("start_mark", ["ready"])])}), \
                mock.patch.object(webui, "web_engine", return_value="ok"):
            self.assertEqual(webui.open_window("RUSE Studio", Path(webui.__file__).parent, "x.html", Api()), 0)
        got = entries(self.lines()[0])
        self.assertIn("both", got)
        self.assertNotIn("status", got)  # called by `both`, not by the page
        self.assertNotIn("units", got)

    def test_without_a_log_the_window_is_as_before(self):
        api = Api()
        with mock.patch.dict(sys.modules, {"webview": fake_webview([("status", [])])}), \
                mock.patch.object(webui, "web_engine", return_value="ok"):
            self.assertEqual(webui.open_window("RUSE Studio", Path(webui.__file__).parent, "x.html", api), 0)
        self.assertNotIn("status", vars(api))  # nothing wrapped
        self.assertEqual(self.lines(), [])

    def test_a_self_test_isnt_a_start(self):
        from ruse_launcher import app
        with mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(self.home)}):
            app.main(["--game", str(self.home / "no-game"), "--self-test", str(self.home / "report.txt")])
        self.assertTrue((self.home / "report.txt").is_file())
        self.assertFalse((self.home / "logs" / "launcher-start.log").exists())
        self.assertIsNone(startlog.current())


if __name__ == "__main__":
    unittest.main()
