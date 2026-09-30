"""Updating the installed apps from GitHub Releases (rusemod.update), on made-up releases: no network is used."""
import hashlib
import io
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from rusemod import update
from rusemod.update import Release, UpdateCalls, UpdateError, download, latest, run_installer

SETUP = b"MZ pretend installer " * 100
SHA = hashlib.sha256(SETUP).hexdigest()


def release(tag, *, draft=False, digest=True, notes=True, name=None, url=None, pre=False):
    version = tag.split("-v")[1]
    app = "Launcher" if tag.startswith("launcher") else "Studio"
    asset = {"name": name or f"RUSE-{app}-Setup-{version}.exe", "size": len(SETUP),
             "browser_download_url": url or f"https://github.com/sneadtristen6/Ruse-Mod-Platform/releases/download/{tag}/x.exe"}
    if digest:
        asset["digest"] = "sha256:" + (digest if isinstance(digest, str) else SHA)
    return {"tag_name": tag, "draft": draft, "prerelease": pre, "assets": [asset],
            "html_url": f"https://github.com/sneadtristen6/Ruse-Mod-Platform/releases/tag/{tag}",
            "body": f"compare its SHA-256 with `{SHA}`" if notes else "no hash here"}


class Finding(unittest.TestCase):
    def test_the_newest_release_of_this_app(self):
        rels = [release("launcher-v0.2.0"), release("launcher-v0.10.0", draft=True), release("studio-v9.0.0"),
                release("launcher-v0.3.1"), release("launcher-v0.1.0")]
        rel = latest("launcher", "0.1.0", fetch=lambda url: rels)
        self.assertEqual((rel.version, rel.asset, rel.sha256), ("0.3.1", "RUSE-Launcher-Setup-0.3.1.exe", SHA))
        self.assertIsNone(latest("launcher", "0.3.1", fetch=lambda url: rels))
        self.assertEqual(latest("studio", "0.4.1", fetch=lambda url: [release("studio-v0.5.0", pre=True)]).version,
                         "0.5.0")  # the Studio's releases are pre-releases, and count

    def test_only_a_release_that_can_be_checked(self):
        for rel, why in ((release("launcher-v0.2.0", digest=False, notes=False), "can't be checked"),
                         (release("launcher-v0.2.0", digest="0" * 64), "can't be checked"),
                         (release("launcher-v0.2.0", name="other.exe"), "isn't in the release"),
                         (release("launcher-v0.2.0", url="https://evil.example/x.exe"), "isn't on GitHub")):
            with self.subTest(why=why), self.assertRaisesRegex(UpdateError, why):
                latest("launcher", "0.1.0", fetch=lambda url, r=rel: [r])
        self.assertEqual(latest("launcher", "0.1.0", fetch=lambda url: [release("launcher-v0.2.0", digest=False)])
                         .sha256, SHA)  # the release notes' hash alone is enough
        with self.assertRaisesRegex(UpdateError, "couldn't be reached"):
            latest("launcher", "0.1.0", fetch=mock.Mock(side_effect=OSError("offline")))


class Response(io.BytesIO):
    def __init__(self, data, url="https://objects.githubusercontent.com/x"):
        super().__init__(data)
        self._url = url

    def geturl(self):
        return self._url


class Downloading(unittest.TestCase):
    REL = Release("launcher", "0.2.0", "launcher-v0.2.0", "", "RUSE-Launcher-Setup-0.2.0.exe", "https://github.com/x",
                  len(SETUP), SHA)

    def test_checked_as_it_comes(self):
        with tempfile.TemporaryDirectory() as d:
            seen = []
            path = download(self.REL, Path(d), lambda done, total: seen.append(done), opener=lambda url: Response(SETUP))
            self.assertEqual((path.read_bytes(), seen[-1]), (SETUP, len(SETUP)))
            with self.assertRaisesRegex(UpdateError, "isn't the published one"):
                download(self.REL, Path(d) / "b", opener=lambda url: Response(SETUP + b"!"))
            self.assertEqual(list((Path(d) / "b").iterdir()), [])  # nothing left behind

    def test_downloads_come_only_from_github(self):
        with mock.patch("urllib.request.urlopen", return_value=Response(SETUP, "https://evil.example/x.exe")):
            with self.assertRaisesRegex(UpdateError, "isn't GitHub"):
                update._open("https://github.com/x")

    def test_the_installer_runs_silently_and_opens_the_app_again(self):
        popen = mock.Mock()
        run_installer(Path("C:/x/setup.exe"), popen=popen)
        args = popen.call_args[0][0]
        self.assertEqual(args[1:3], ["/SILENT", "/SUPPRESSMSGBOXES"])
        self.assertIn("/relaunch=1", args)


class App(UpdateCalls):
    UPDATE_APP, UPDATE_VERSION = "launcher", "0.1.0"

    def __init__(self, home, installed=True):
        self._home, self._jobs = home, {}
        self._update_fetch = lambda url: [release("launcher-v0.2.0")]
        self._update_opener = lambda url: Response(SETUP)
        self._update_popen = mock.Mock()
        self._update_quit = mock.Mock()
        self._update_installed = lambda: installed
        self._update_open_url = mock.Mock()


class Calls(unittest.TestCase):
    def test_check_then_install(self):
        with tempfile.TemporaryDirectory() as d:
            app = App(d)
            self.assertEqual(app.update_check()["version"], "0.2.0")
            app.update_page()
            app._update_open_url.assert_called_once()
            job = app.update_install()["job"]
            for _ in range(200):
                if app._jobs[job].state != "running":
                    break
                time.sleep(0.02)
            view = app._jobs[job].view()
            self.assertEqual((view["state"], view["lines"][-1]), ("done", "installing"), view)
            self.assertTrue((Path(d) / "updates" / "RUSE-Launcher-Setup-0.2.0.exe").is_file())
            app._update_popen.assert_called_once()
            app._update_quit.assert_called_once()

    def test_a_copy_from_the_repo_is_told_to_pull(self):
        with tempfile.TemporaryDirectory() as d:
            app = App(d, installed=False)
            self.assertEqual(app.update_check()["installed"], False)
            with self.assertRaisesRegex(UpdateError, "git pull"):
                app.update_install()
            self.assertEqual(App(d).update_check()["available"], True)
            quiet = App(d)
            quiet._update_fetch = lambda url: [release("launcher-v0.1.0")]
            self.assertEqual(quiet.update_check(), {"available": False, "version": "0.1.0"})


if __name__ == "__main__":
    unittest.main()
