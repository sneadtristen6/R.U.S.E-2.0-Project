"""Microsoft's WebView2 offered, never forced (rusemod.webview2; the owner, 2026-11-24): whether this PC has it, where its
installer is, running it on the player's yes, and Settings' card in both apps. The box at an app's start is in
test_browsermode (TheWindowOrTheBrowser); the build and the installer's ticked box in test_installers."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from rusemod import browsermode, webview2


def registry(values: dict):
    """A stand-in for the registry: {(root, key): pv}."""
    return lambda root, key: values.get((root, key), "")


MACHINE = webview2.KEYS[0]
USER = webview2.KEYS[2]


def with_setup(tmp) -> Path:
    path = Path(tmp, "webview2", "MicrosoftEdgeWebview2Setup.exe")
    path.parent.mkdir(parents=True)
    path.write_bytes(b"MZ")
    return path


class TheInstalledVersion(unittest.TestCase):
    def test_read_where_microsoft_says_none_means_missing(self):
        self.assertEqual(webview2.version(registry({})), "")
        self.assertEqual(webview2.version(registry({MACHINE: "0.0.0.0"})), "")  # Microsoft: 0.0.0.0 = not installed
        self.assertEqual(webview2.version(registry({USER: "143.0.3650.80"})), "143.0.3650.80")  # a per-user install
        self.assertEqual(webview2.version(registry({MACHINE: "143.0.1.1", USER: "142.0.1.1"})), "143.0.1.1")
        # the same keys installers/installer.iss reads
        script = (Path(__file__).parents[1] / "installers" / "installer.iss").read_text(encoding="utf-8")
        self.assertIn(webview2.CLIENT.split("\\")[-1], script)


class OfferedOrNot(unittest.TestCase):
    def offered(self, tmp, platform="win32", wine=False):
        with mock.patch.object(webview2.sys, "platform", platform), \
                mock.patch.object(browsermode, "under_wine", return_value=wine):
            return webview2.offered(Path(tmp))

    def test_only_on_windows_never_under_wine_and_only_with_microsofts_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(webview2.setup_file(Path(tmp)))
            self.assertFalse(self.offered(tmp))  # run from the repo: no installer came with it
            setup = with_setup(tmp)
            self.assertEqual(webview2.setup_file(Path(tmp)), setup)
            self.assertTrue(self.offered(tmp))
            self.assertFalse(self.offered(tmp, wine=True))  # Linux, the Steam Deck: null
            self.assertFalse(self.offered(tmp, platform="linux"))


class RunningIt(unittest.TestCase):
    def test_microsofts_installer_runs_as_a_player_runs_it_and_its_result_is_read_back(self):
        ran, waits = [], []
        found = {}

        def run(cmd, check):
            ran.append(cmd)
            found[USER] = "143.0.3650.80"
        version = webview2.install(Path("C:/app/webview2/MicrosoftEdgeWebview2Setup.exe"), run=run,
                                   read=registry(found), wait=waits.append)
        self.assertEqual(version, "143.0.3650.80")
        self.assertEqual(ran, [[str(Path("C:/app/webview2/MicrosoftEdgeWebview2Setup.exe"))]])  # no switches
        self.assertEqual(waits, [])

    def test_a_version_written_a_moment_later_counts_and_none_at_all_says_so(self):
        found, waits = {}, []

        def wait(seconds):
            waits.append(seconds)
            if len(waits) == 3:
                found[MACHINE] = "143.0.1.1"
        self.assertEqual(webview2.install(Path("s.exe"), run=lambda cmd, check: None, read=registry(found), wait=wait),
                         "143.0.1.1")
        self.assertEqual(len(waits), 3)
        waits.clear()
        self.assertEqual(webview2.install(Path("s.exe"), run=lambda cmd, check: None, read=registry({}),
                                          wait=waits.append, settle=5), "")
        self.assertEqual(len(waits), 5)  # it gave up after `settle` seconds

    def test_the_app_starts_again_apart_from_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp, "RUSE Launcher.exe")
            exe.write_bytes(b"MZ")
            started = []
            webview2.start_again([str(Path(tmp, "RUSE Launcher")), "--browser-off"],
                                 popen=lambda cmd, **kw: started.append((cmd, kw)))
            self.assertEqual(started[0][0], [str(exe.resolve()), "--browser-off"])  # ".exe" found when left off
            flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            self.assertEqual(started[0][1]["creationflags"], flags)


class SettingsCard(unittest.TestCase):
    """WebView2Calls, as both apps' window API has it."""

    def api(self, tmp, found, run):
        class Api(webview2.WebView2Calls):
            pass
        api = Api()
        api._webview2_folder, api._webview2_read, api._webview2_run = Path(tmp), registry(found), run
        api._webview2_wait = lambda seconds: None
        return api

    def wait_until(self, api, test):
        for _ in range(200):
            status = api.webview2_status()
            if test(status):
                return status
            time.sleep(0.01)
        self.fail(f"never got there: {api.webview2_status()}")

    def test_install_from_settings_then_its_result(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(webview2.sys, "platform", "win32"), \
                mock.patch.object(browsermode, "under_wine", return_value=False):
            with_setup(tmp)
            found, go, ran = {}, threading.Event(), []

            def run(cmd, check):  # Microsoft's installer, open until the test lets it end
                ran.append(cmd)
                go.wait(5)
                found[USER] = "143.0.3650.80"
            api = self.api(tmp, found, run)
            self.assertEqual(api.webview2_status(), {"offered": True, "version": "", "installing": False,
                                                     "tried": False, "failed": False})
            self.assertTrue(api.webview2_install()["installing"])
            self.assertTrue(api.webview2_install()["installing"])  # a second click while it runs starts nothing
            go.set()
            done = self.wait_until(api, lambda s: not s["installing"])
            self.assertEqual(done, {"offered": True, "version": "143.0.3650.80", "installing": False, "tried": True,
                                    "failed": False})
            self.assertEqual(len(ran), 1)

    def test_an_install_that_ends_without_it_or_cant_start_says_so(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(webview2.sys, "platform", "win32"), \
                mock.patch.object(browsermode, "under_wine", return_value=False), \
                mock.patch("builtins.print"):
            with_setup(tmp)
            for run in (lambda cmd, check: None, mock.Mock(side_effect=OSError(5, "Access is denied"))):
                api = self.api(tmp, {}, run)
                api.webview2_install()
                done = self.wait_until(api, lambda s: not s["installing"])
                self.assertEqual((done["tried"], done["failed"], done["version"]), (True, True, ""))

    def test_nothing_runs_where_it_isnt_offered(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(webview2.sys, "platform", "win32"), \
                mock.patch.object(browsermode, "under_wine", return_value=True):
            with_setup(tmp)
            run = mock.Mock()
            api = self.api(tmp, {}, run)
            self.assertEqual(api.webview2_install()["offered"], False)
            run.assert_not_called()

    def test_both_apps_have_the_card(self):
        from ruse_launcher.api import LauncherApi
        from ruse_studio.api import StudioApi
        root = Path(__file__).parents[1] / "src"
        for cls, app in ((LauncherApi, "ruse_launcher"), (StudioApi, "ruse_studio")):
            with self.subTest(app=app):
                self.assertTrue(issubclass(cls, webview2.WebView2Calls))
                page = (root / app / "ui" / "index.html").read_text(encoding="utf-8")
                script = (root / app / "ui" / "app.js").read_text(encoding="utf-8")
                fake = (root / app / "ui" / "fake-api.js").read_text(encoding="utf-8")
                self.assertIn('<section class="setting hidden" id="set-webview2">', page)  # hidden until offered
                for call in ("webview2_status", "webview2_install"):
                    self.assertIn(f"api().{call}()", script)
                    self.assertIn(f"{call}: async", fake)
                self.assertIn('$("set-webview2-install").addEventListener("click", installWebview2)', script)


if __name__ == "__main__":
    unittest.main()
