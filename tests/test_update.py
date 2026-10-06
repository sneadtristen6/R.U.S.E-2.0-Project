"""Updating the installed apps from GitHub Releases (rusemod.update), on made-up releases: no network is used."""
import hashlib
import io
import json
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
             "browser_download_url": url or f"https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/download/{tag}/x.exe"}
    if digest:
        asset["digest"] = "sha256:" + (digest if isinstance(digest, str) else SHA)
    return {"tag_name": tag, "draft": draft, "prerelease": pre, "assets": [asset],
            "html_url": f"https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/{tag}",
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

    def test_a_small_fix_with_a_fourth_number(self):
        """The owner, 2026-10-03: small fixes between releases (studio-v0.9.4.1) are offered like any other."""
        rels = [release("studio-v0.9.4", pre=True), release("studio-v0.9.4.1", pre=True), release("studio-v0.9.3", pre=True)]
        rel = latest("studio", "0.9.4", fetch=lambda url: rels)
        self.assertEqual((rel.version, rel.asset), ("0.9.4.1", "RUSE-Studio-Setup-0.9.4.1.exe"))
        self.assertIsNone(latest("studio", "0.9.4.1", fetch=lambda url: rels))
        self.assertEqual(latest("studio", "0.9.3", fetch=lambda url: rels).version, "0.9.4.1")
        self.assertIsNone(latest("studio", "0.9.3", fetch=lambda url: [release("studio-v0.9.4.1.2", pre=True)]))

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
            latest("launcher", "0.1.0", fetch=mock.Mock(side_effect=OSError("offline")),
                   fetch_text=mock.Mock(side_effect=OSError("offline")))

    def test_the_release_feed_when_the_api_refuses(self):
        """GitHub allows 60 API calls an hour per internet address; when they're used up (by anything on it), the
        release feed answers, with the installer's SHA-256 from the release notes as the check."""
        base = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases"
        feed = ("<feed><entry><link rel=\"alternate\" href=\"" + base + "/tag/studio-v0.6.1\"/>"
                "<content type=\"html\">&lt;p&gt;SHA-256 `" + SHA + "`&lt;/p&gt;</content></entry>"
                "<entry><link rel=\"alternate\" href=\"" + base + "/tag/launcher-v0.2.4\"/>"
                "<content type=\"html\">no hash</content></entry></feed>")
        refused = mock.Mock(side_effect=OSError("HTTP Error 403: rate limit exceeded"))
        rel = latest("studio", "0.6.0", fetch=refused, fetch_text=lambda url: feed)
        self.assertEqual((rel.version, rel.sha256, rel.url),
                         ("0.6.1", SHA, base + "/download/studio-v0.6.1/RUSE-Studio-Setup-0.6.1.exe"))
        with self.assertRaisesRegex(UpdateError, "can't be checked"):  # no hash in its notes: not installed
            latest("launcher", "0.2.3", fetch=refused, fetch_text=lambda url: feed)
        self.assertIsNone(latest("studio", "0.6.1", fetch=refused, fetch_text=lambda url: feed))


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


NOTES = """**RUSE Studio, a preview.** Intro.

**0.9.0:** a later one.
| Before | Now |
|---|---|
| No height slider. | A slider for the zones' height. |

**0.8.1:** units from any nation.
| Before | Now |
| --- | --- |
| A unit from another nation crashed the game. | It works in any match. |
| No transparency. | Sliders for the layers. |

**0.8.0:** the map editor grows up.
- **New brushes**
- **Check this map**

**0.7.6:** older.
"""


class Changes(unittest.TestCase):
    def test_before_and_after_since_the_running_version(self):
        rows = update.changes_since(NOTES, "0.7.6", "0.8.1")
        self.assertEqual([(r["version"], r["before"], r["now"]) for r in rows], [
            ("0.8.1", "A unit from another nation crashed the game.", "It works in any match."),
            ("0.8.1", "No transparency.", "Sliders for the layers."),
            ("0.8.0", "", "**New brushes**"),
            ("0.8.0", "", "**Check this map**")])

    def test_only_the_versions_between(self):
        self.assertEqual([r["version"] for r in update.changes_since(NOTES, "0.8.1", "0.9.0")], ["0.9.0"])
        self.assertEqual(update.changes_since(NOTES, "0.9.0", "0.9.0"), [])
        self.assertEqual(update.changes_since("", "0.1.0", "0.2.0"), [])

    def test_a_version_with_a_fourth_number(self):
        """The owner, 2026-10-06: "make releases go another digit longer until 1.0" (0.9.8.1): its notes are read."""
        notes = ("**0.9.9:** next.\n| Before | Now |\n|---|---|\n| Old. | Newer. |\n\n"
                 "**0.9.8.1:** small.\n| Before | Now |\n|---|---|\n| Slow. | Fast. |\n\n"
                 "**0.9.8:** older.\n- **A thing**\n")
        self.assertEqual([(r["version"], r["before"], r["now"]) for r in update.changes_since(notes, "0.9.8", "0.9.8.1")],
                         [("0.9.8.1", "Slow.", "Fast.")])
        self.assertEqual([r["version"] for r in update.changes_since(notes, "0.9.7", "0.9.9")],
                         ["0.9.9", "0.9.8.1", "0.9.8"])
        self.assertEqual(update.changes_since(notes, "0.9.8.1", "0.9.8.1"), [])

    def test_the_check_says_both_versions(self):
        with tempfile.TemporaryDirectory() as d:
            app = App(d)
            self.assertEqual(app.app_version(), {"app": "Launcher", "version": "0.1.0"})
            u = app.update_check()
            self.assertEqual((u["current"], u["version"]), ("0.1.0", "0.2.0"))
            self.assertIsInstance(u["changes"], list)


FRENCH = """**Studio RUSE, un aperçu.** Intro.

**0.8.1 :** pas un titre de version (l'espace avant les deux-points).

**0.8.1:** des unités de toutes les nations.
| Avant | Maintenant |
|---|---|
| Une unité d'une autre nation faisait planter le jeu. | Elle marche dans toutes les parties. |
"""


class Languages(unittest.TestCase):
    """The update panel in the app's own language (the owner, 2026-10-05: a French player's panel was in English):
    every language's notes in one file published beside the installer; English when a language has none."""
    BOOK = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/download/launcher-v0.2.0/RUSE-Launcher-notes.json"

    def rel(self, notes_url=BOOK):
        return Release("launcher", "0.8.1", "launcher-v0.8.1", "", "x.exe", "https://github.com/x", 1, SHA,
                       update.changes_since(NOTES, "0.8.0", "0.8.1"), notes_url)

    def test_a_translated_table_s_header_is_no_change(self):
        self.assertEqual([(r["before"], r["now"]) for r in update.changes_since(FRENCH, "0.8.0", "0.8.1")],
                         [("Une unité d'une autre nation faisait planter le jeu.", "Elle marche dans toutes les parties.")])

    def test_the_language_asked_for_else_english(self):
        book = json.dumps({"us": NOTES, "fr": FRENCH}).encode("utf-8")
        fr = update.changes_in(self.rel(), "fr", "0.8.0", opener=lambda url: Response(book))
        self.assertEqual(fr[0]["now"], "Elle marche dans toutes les parties.")
        english = [r["now"] for r in self.rel().changes]
        for lang, opener in (("ger", lambda url: Response(book)),  # no German notes
                             ("us", None), ("base", None),  # English, and the game's own names
                             ("fr", mock.Mock(side_effect=OSError("offline"))),
                             ("fr", lambda url: Response(b"not json")),
                             ("fr", lambda url: Response(b" " * (update.NOTES_MAX + 1)))):
            with self.subTest(lang=lang):
                self.assertEqual([r["now"] for r in update.changes_in(self.rel(), lang, "0.8.0", opener=opener)], english)
        self.assertEqual([r["now"] for r in update.changes_in(self.rel(""), "fr", "0.8.0", opener=lambda url: Response(book))],
                         english)  # a release without the file

    def test_a_version_never_translated_stays_english_beside_the_translated_one(self):
        rel = Release("launcher", "0.8.1", "launcher-v0.8.1", "", "x.exe", "https://github.com/x", 1, SHA,
                      update.changes_since(NOTES, "0.7.6", "0.8.1"), self.BOOK)  # someone on 0.7.6: 0.8.1 and 0.8.0
        book = json.dumps({"fr": FRENCH}).encode("utf-8")  # 0.8.1 only, in French
        got = update.changes_in(rel, "fr", "0.7.6", opener=lambda url: Response(book))
        self.assertEqual([(r["version"], r["now"]) for r in got], [
            ("0.8.1", "Elle marche dans toutes les parties."), ("0.8.0", "**New brushes**"), ("0.8.0", "**Check this map**")])

    def test_the_file_is_found_beside_the_installer_on_github_only(self):
        rel = release("launcher-v0.2.0")
        rel["assets"].append({"name": "RUSE-Launcher-notes.json", "browser_download_url": self.BOOK})
        self.assertEqual(latest("launcher", "0.1.0", fetch=lambda url: [rel]).notes_url, self.BOOK)
        rel["assets"][-1]["browser_download_url"] = "https://evil.example/notes.json"
        self.assertEqual(latest("launcher", "0.1.0", fetch=lambda url: [rel]).notes_url, "")
        self.assertEqual(latest("launcher", "0.1.0", fetch=lambda url: [release("launcher-v0.2.0")]).notes_url, "")
        # the release feed (when the API refuses) names it at its download address
        feed = ("<feed><entry><link rel=\"alternate\" href=\"https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases"
                "/tag/studio-v0.6.1\"/><content type=\"html\">SHA-256 `" + SHA + "`</content></entry></feed>")
        got = latest("studio", "0.6.0", fetch=mock.Mock(side_effect=OSError("403")), fetch_text=lambda url: feed)
        self.assertTrue(got.notes_url.endswith("/releases/download/studio-v0.6.1/RUSE-Studio-notes.json"))

    def test_the_check_takes_the_language(self):
        with tempfile.TemporaryDirectory() as d:
            app = App(d)
            rel = release("launcher-v0.2.0")
            rel["body"] += "\n\n**0.2.0:** new.\n| Before | Now |\n|---|---|\n| Old. | New. |\n"
            rel["assets"].append({"name": "RUSE-Launcher-notes.json", "browser_download_url": self.BOOK})
            app._update_fetch = lambda url: [rel]
            book = json.dumps({"fr": "**0.2.0:** nouveau.\n| Avant | Maintenant |\n|---|---|\n| Ancien. | Nouveau. |\n"})
            app._update_opener = lambda url: Response(book.encode("utf-8"))
            self.assertEqual(app.update_check("fr")["changes"], [{"version": "0.2.0", "before": "Ancien.", "now": "Nouveau."}])
            self.assertEqual(app.update_check()["changes"], [{"version": "0.2.0", "before": "Old.", "now": "New."}])


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
            self.assertEqual(quiet.update_check(), {"available": False, "version": "0.1.0", "current": "0.1.0"})


class FakeReg:
    """Just enough of winreg for fix_app_list_version: one HKCU with uninstall keys."""
    HKEY_CURRENT_USER, KEY_READ, KEY_SET_VALUE, REG_SZ = "HKCU", 1, 2, 1

    def __init__(self, keys):
        self.keys = keys

    def OpenKey(self, root, path, _reserved, _access):
        if path not in self.keys:
            raise FileNotFoundError(path)
        return mock.MagicMock(__enter__=lambda s: path, __exit__=lambda s, *a: False)

    def QueryValueEx(self, path, name):
        if name not in self.keys[path]:
            raise FileNotFoundError(name)
        return self.keys[path][name], self.REG_SZ

    def SetValueEx(self, path, name, _reserved, _kind, value):
        self.keys[path][name] = value


class AppList(unittest.TestCase):
    """Windows' list of installed apps showed the Launcher as 0.1.0 with 0.3.1 installed (issue #15): the installed
    app sets its own entry's version."""

    def test_a_stale_version_is_put_right_and_a_right_one_left(self):
        key = update.UNINSTALL + r"\{96F731B1-F85A-48E8-A810-49128DF99706}_is1"
        reg = FakeReg({key: {"DisplayVersion": "0.1.0", "DisplayName": "RUSE Launcher"}})
        self.assertEqual(update.fix_app_list_version("launcher", "0.4.0", reg), "0.1.0")
        self.assertEqual(reg.keys[key]["DisplayVersion"], "0.4.0")
        self.assertIsNone(update.fix_app_list_version("launcher", "0.4.0", reg))  # already right: untouched
        self.assertIsNone(update.fix_app_list_version("studio", "0.9.0", reg))  # no entry (run from the repo, say)

    def test_the_ids_are_the_installers(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("build_app", Path(__file__).parents[1] / "installers" / "build_app.py")
        build_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build_app)
        self.assertEqual({a: v["id"] for a, v in build_app.APPS.items()}, update.APP_IDS)


if __name__ == "__main__":
    unittest.main()
