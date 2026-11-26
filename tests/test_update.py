"""Updating the installed apps from GitHub Releases (rusemod.update), on made-up releases: no network is used. An update
installs only with the owner's signature (rusemod.releasesig; his decision 26 A of 2026-11-25); the keys here are the
RFC 8032 test vectors' published secrets, never a real key (a release build refuses them: test_releasesig)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import dataclasses
import hashlib
import http.client
import io
import json
import re
import tempfile
import tomllib
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from rusemod import ed25519, releasesig, update
from rusemod.update import Release, UpdateCalls, UpdateError, download, latest, run_installer

SETUP = b"MZ pretend installer " * 100
SHA = hashlib.sha256(SETUP).hexdigest()
SECRET1 = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")   # RFC 8032 TEST 1
SECRET2 = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")   # RFC 8032 TEST 2
KEYS = {"release-1": ed25519.public_key(SECRET1), "release-2": ed25519.public_key(SECRET2)}
REPO = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project"
DL = REPO + "/releases/download/"
NOTES_EN = ("**0.4.0:** the newest.\n| Before | Now |\n|---|---|\n| Old four. | New four. |\n\n"
            "**0.2.0:** new.\n| Before | Now |\n|---|---|\n| Old. | New. |\n")
BOOK = json.dumps({"us": NOTES_EN, "fr": "**0.2.0:** nouveau.\n| Avant | Maintenant |\n|---|---|\n| Ancien. | Nouveau. |\n"}
                  ).encode("utf-8")
SIGS = {}   # the made-up releases' signature files, by address (fetch_sig)


def fetch_sig(url):
    return SIGS.get(url)


def names(tag):
    app, version = tag.split("-v")
    big = "Launcher" if app == "launcher" else "Studio"
    return app, version, f"RUSE-{big}-Setup-{version}.exe", f"RUSE-{big}-notes.json"


def statement(tag, *, required="", size=len(SETUP), sha=SHA, book=BOOK):
    app, version, setup, notes = names(tag)
    return {"app": app, "version": version, "tag": tag, "file": setup, "size": size, "sha256": sha, "notes_file": notes,
            "notes_size": len(book), "notes_sha256": hashlib.sha256(book).hexdigest(), "required": required,
            "commit": "ab" * 20}


def release(tag, *, draft=False, signed=True, required="", digest=True, size=None, setup=None, body="", sig=None,
            secret=SECRET1, key="release-1", **change):
    """A release as GitHub's API lists it, its signature file (made with `secret`) kept in SIGS."""
    app, version, name, notes = names(tag)
    asset = {"name": setup or name, "size": len(SETUP) if size is None else size,
             "browser_download_url": f"{DL}{tag}/{setup or name}"}
    if digest:
        asset["digest"] = "sha256:" + (digest if isinstance(digest, str) else SHA)
    assets = [asset, {"name": notes, "size": len(BOOK), "browser_download_url": f"{DL}{tag}/{notes}"}]
    if signed:
        assets.append({"name": name + ".sig", "size": 1, "browser_download_url": f"{DL}{tag}/{name}.sig"})
        SIGS[f"{DL}{tag}/{name}.sig"] = sig if sig is not None else releasesig.make(
            dict(statement(tag, required=required), **change), secret, key).encode("ascii")
    return {"tag_name": tag, "draft": draft, "prerelease": app == "studio", "assets": assets,
            "html_url": f"{REPO}/releases/tag/{tag}", "body": body}


class Keyed(unittest.TestCase):
    """The test keys stand for the owner's while each test runs (nothing else changes them)."""

    def setUp(self):
        self.enterContext(mock.patch.object(releasesig, "RELEASE_KEYS", KEYS))
        SIGS.clear()


def find(app, current, rels, **kw):
    return latest(app, current, fetch=lambda url: rels, fetch_sig=kw.pop("fetch_sig", fetch_sig), **kw)


class Finding(Keyed):
    def test_the_newest_signed_release_of_this_app(self):
        rels = [release("launcher-v0.2.0"), release("launcher-v0.10.0", draft=True), release("studio-v9.0.0"),
                release("launcher-v0.3.1"), release("launcher-v0.1.0")]
        rel = find("launcher", "0.1.0", rels)
        self.assertEqual((rel.version, rel.asset, rel.sha256, rel.size, rel.key),
                         ("0.3.1", "RUSE-Launcher-Setup-0.3.1.exe", SHA, len(SETUP), "release-1"))
        self.assertEqual((rel.url, rel.page), (f"{DL}launcher-v0.3.1/RUSE-Launcher-Setup-0.3.1.exe",
                                               f"{REPO}/releases/tag/launcher-v0.3.1"))
        self.assertEqual((rel.refused, rel.ignored), ("", []))
        self.assertIsNone(find("launcher", "0.3.1", rels))
        self.assertEqual(find("studio", "0.4.1", [release("studio-v0.5.0")]).version, "0.5.0")  # pre-releases count

    def test_a_small_fix_with_a_fourth_number(self):
        """The owner, 2026-10-03: small fixes between releases (studio-v0.9.4.1) are offered like any other."""
        rels = [release("studio-v0.9.4"), release("studio-v0.9.4.1"), release("studio-v0.9.3")]
        self.assertEqual(find("studio", "0.9.4", rels).asset, "RUSE-Studio-Setup-0.9.4.1.exe")
        self.assertIsNone(find("studio", "0.9.4.1", rels))
        self.assertIsNone(find("studio", "0.9.3", [release("studio-v0.9.4.1.2")]))

    def test_a_release_without_his_signature_is_never_offered(self):
        """A release made or changed by anyone but the owner (a taken-over account, a collaborator, a workflow) has no
        statement that fits: nothing is offered, and the answer says which version was skipped."""
        token = releasesig.make(statement("launcher-v0.2.0"), SECRET1, "release-1").encode()
        changed = token[:-2] + (b"A" if token[-2:-1] != b"A" else b"B") + token[-1:]   # one letter of the signature
        moved = releasesig.make(statement("launcher-v0.3.0"), SECRET1, "release-1").encode()  # another release's
        for why, made in (("no .sig", lambda: release("launcher-v0.2.0", signed=False)),
                          ("an unknown key", lambda: release("launcher-v0.2.0", secret=bytes(range(32)), key="release-9")),
                          ("signed by a key not his", lambda: release("launcher-v0.2.0", secret=bytes(range(32)))),
                          ("a changed byte", lambda: release("launcher-v0.2.0", sig=changed)),
                          ("another release's statement", lambda: release("launcher-v0.2.0", sig=moved)),
                          ("not text", lambda: release("launcher-v0.2.0", sig=b"\xff" * 20000))):
            SIGS.clear()
            with self.subTest(why=why), self.assertRaisesRegex(UpdateError, "can't confirm it's ours") as caught:
                find("launcher", "0.1.0", [made()])
            self.assertTrue(caught.exception.final)
            self.assertEqual(caught.exception.version, "0.2.0")
        self.assertEqual(find("launcher", "0.1.0", [release("launcher-v0.2.0", sig=token)]).version, "0.2.0")  # CONTROL
        rel = release("launcher-v0.2.0", secret=SECRET2, key="release-2")
        self.assertEqual(find("launcher", "0.1.0", [rel]).key, "release-2")   # the backup key is his too

    def test_an_unsigned_one_above_a_signed_one_is_skipped_and_named(self):
        rels = [release("launcher-v99.0.0", signed=False), release("launcher-v0.9.9.1", required="0.9.9.1")]
        rel = find("launcher", "0.9.8", rels)
        self.assertEqual((rel.version, rel.required, rel.ignored), ("0.9.9.1", "0.9.9.1", ["99.0.0"]))

    def test_at_most_five_newer_ones_are_looked_at(self):
        asked = []
        rels = [release(f"launcher-v1.0.{n}", signed=False) for n in range(7)] + [release("launcher-v0.9.0")]
        with self.assertRaises(UpdateError) as caught:
            find("launcher", "0.1.0", rels, fetch_sig=lambda url: asked.append(url))
        self.assertEqual((caught.exception.final, caught.exception.version), (True, "1.0.6"))
        self.assertEqual(asked, [])   # not listed: not even asked for
        self.assertEqual(find("launcher", "0.1.0", rels[3:]).version, "0.9.0")  # four above it: found

    def test_github_s_listing_of_another_file_refuses_it(self):
        for why, rel in (("isn't the one we signed", release("launcher-v0.2.0", size=len(SETUP) + 1)),
                         ("isn't the one we signed", release("launcher-v0.2.0", digest="0" * 64)),
                         ("isn't in the release", release("launcher-v0.2.0", setup="other.exe"))):
            with self.subTest(why=why):
                self.assertIn(why, find("launcher", "0.1.0", [rel]).refused)
        self.assertEqual(find("launcher", "0.1.0", [release("launcher-v0.2.0", digest=False)]).refused, "")  # CONTROL

    def test_the_release_text_is_not_trusted(self):
        """The text anyone with push access can edit: its hash, its required line and its notes are not his word."""
        body = f"compare its SHA-256 with `{'0' * 64}`\n\n**0.2.0:** x\n<!-- required update -->\n"
        rel = find("launcher", "0.1.0", [release("launcher-v0.2.0", body=body)])
        self.assertEqual((rel.sha256, rel.required, rel.changes), (SHA, "", []))
        with self.assertRaises(UpdateError):
            find("launcher", "0.1.0", [release("launcher-v0.2.0", body=body, signed=False)])

    def test_the_release_feed_when_the_api_refuses(self):
        """GitHub allows 60 API calls an hour per internet address; when they're used up (by anything on it), the
        release feed answers: the signature at its download address, the sizes checked on the download."""
        feed = ("<feed><entry><link rel=\"alternate\" href=\"" + REPO + "/releases/tag/studio-v0.6.1\"/>"
                "<content type=\"html\">notes</content></entry>"
                "<entry><link rel=\"alternate\" href=\"" + REPO + "/releases/tag/launcher-v0.2.4\"/>"
                "<content type=\"html\">notes</content></entry></feed>")
        refused = mock.Mock(side_effect=OSError("HTTP Error 403: rate limit exceeded"))
        SIGS[f"{DL}studio-v0.6.1/RUSE-Studio-Setup-0.6.1.exe.sig"] = releasesig.make(
            statement("studio-v0.6.1"), SECRET1, "release-1").encode()
        rel = latest("studio", "0.6.0", fetch=refused, fetch_text=lambda url: feed, fetch_sig=fetch_sig)
        self.assertEqual((rel.version, rel.sha256, rel.url, rel.refused),
                         ("0.6.1", SHA, f"{DL}studio-v0.6.1/RUSE-Studio-Setup-0.6.1.exe", ""))
        with self.assertRaises(UpdateError) as caught:   # no signature there (GitHub's 404): not ours
            latest("launcher", "0.2.3", fetch=refused, fetch_text=lambda url: feed, fetch_sig=fetch_sig)
        self.assertTrue(caught.exception.final)
        self.assertIsNone(latest("studio", "0.6.1", fetch=refused, fetch_text=lambda url: feed, fetch_sig=fetch_sig))

    def test_github_out_of_reach_is_not_a_refusal(self):
        with self.assertRaisesRegex(UpdateError, "couldn't be reached") as caught:
            latest("launcher", "0.1.0", fetch=mock.Mock(side_effect=OSError("offline")),
                   fetch_text=mock.Mock(side_effect=OSError("offline")), fetch_sig=fetch_sig)
        self.assertFalse(caught.exception.final)
        for failure in (urllib.error.HTTPError("x", 503, "busy", {}, None), OSError("cut"),
                        http.client.IncompleteRead(b"")):
            with self.subTest(failure=type(failure).__name__), \
                    mock.patch.object(update, "_open", mock.Mock(side_effect=failure)):
                with self.assertRaisesRegex(UpdateError, "signature couldn't be downloaded now") as caught:
                    find("launcher", "0.1.0", [release("launcher-v0.2.0")], fetch_sig=update._get_sig)
                self.assertFalse(caught.exception.final)
        with mock.patch.object(update, "_open", mock.Mock(side_effect=urllib.error.HTTPError("x", 404, "no", {}, None))):
            self.assertIsNone(update._get_sig("https://github.com/x.sig"))   # none there: no signature


class Response(io.BytesIO):
    def __init__(self, data, url="https://objects.githubusercontent.com/x", headers=None):
        super().__init__(data)
        self._url, self.headers = url, headers or {}

    def geturl(self):
        return self._url


class Cut(Response):
    def read(self, n=-1):
        raise http.client.IncompleteRead(b"x", 5)


class Downloading(unittest.TestCase):
    REL = Release("launcher", "0.2.0", "launcher-v0.2.0", "", "RUSE-Launcher-Setup-0.2.0.exe", "https://github.com/x",
                  len(SETUP), SHA)

    def test_checked_against_the_signed_size_and_sha256_as_it_comes(self):
        with tempfile.TemporaryDirectory() as d:
            seen = []
            path = download(self.REL, Path(d), lambda done, total: seen.append(done), opener=lambda url: Response(SETUP))
            self.assertEqual((path.read_bytes(), seen[-1]), (SETUP, len(SETUP)))  # CONTROL
            other = bytes(len(SETUP))
            for i, (why, data, headers, final) in enumerate((
                    ("isn't the one we signed", other, None, True),
                    ("bigger than the one we signed", SETUP + b"!", None, True),
                    ("its size differs", SETUP, {"Content-Length": str(len(SETUP) + 1)}, True),
                    ("stopped before the end", SETUP[:-5], {"Content-Length": str(len(SETUP))}, False),
                    ("stopped before the end", SETUP[:-5], None, False))):
                with self.subTest(why=why, i=i):
                    folder = Path(d) / str(i)
                    with self.assertRaisesRegex(UpdateError, why) as caught:
                        download(self.REL, folder, opener=lambda url, b=data, h=headers: Response(b, headers=h))
                    self.assertEqual(caught.exception.final, final)
                    self.assertEqual(list(folder.iterdir()), [])  # nothing left behind
            for failure, why in ((lambda url: Cut(b""), "stopped before the end"),
                                 (mock.Mock(side_effect=OSError("cut")), "the download stopped"),
                                 (mock.Mock(side_effect=urllib.error.HTTPError("x", 404, "no", {}, None)),
                                  "the server answered 404")):
                with self.subTest(why=why):
                    with self.assertRaisesRegex(UpdateError, why) as caught:
                        download(self.REL, Path(d) / "c", opener=failure)
                    self.assertFalse(caught.exception.final)   # a try that failed: it may work later
                    self.assertNotIn("IncompleteRead", str(caught.exception))

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
            self.assertEqual(u["changes"], [{"version": "0.2.0", "before": "Old.", "now": "New."}])


FRENCH = """**Studio RUSE, un aperçu.** Intro.

**0.8.1 :** pas un titre de version (l'espace avant les deux-points).

**0.8.1:** des unités de toutes les nations.
| Avant | Maintenant |
|---|---|
| Une unité d'une autre nation faisait planter le jeu. | Elle marche dans toutes les parties. |
"""


def book_release(book, version="0.8.1"):
    return Release("launcher", version, f"launcher-v{version}", "", "x.exe", "https://github.com/x", 1, SHA, [],
                   f"{DL}launcher-v{version}/RUSE-Launcher-notes.json", "", len(book), hashlib.sha256(book).hexdigest())


class Languages(unittest.TestCase):
    """The update panel in the app's own language (the owner, 2026-10-05: a French player's panel was in English):
    every language's notes in one file published beside the installer, English ("us") when a language has none, and
    only from that file as the owner signed it."""

    def test_a_translated_table_s_header_is_no_change(self):
        self.assertEqual([(r["before"], r["now"]) for r in update.changes_since(FRENCH, "0.8.0", "0.8.1")],
                         [("Une unité d'une autre nation faisait planter le jeu.", "Elle marche dans toutes les parties.")])

    def test_the_language_asked_for_else_english(self):
        book = json.dumps({"us": NOTES, "fr": FRENCH}).encode("utf-8")
        rel = book_release(book)
        self.assertEqual(update.changes_in(rel, "fr", "0.8.0", opener=lambda url: Response(book))[0]["now"],
                         "Elle marche dans toutes les parties.")
        english = [r["now"] for r in update.changes_since(NOTES, "0.8.0", "0.8.1")]
        for lang in ("ger", "us", "base"):  # no German notes; English; the game's own names
            with self.subTest(lang=lang):
                self.assertEqual([r["now"] for r in update.changes_in(rel, lang, "0.8.0", opener=lambda url: Response(book))],
                                 english)

    def test_only_the_signed_notes_file(self):
        book = json.dumps({"us": NOTES, "fr": FRENCH}).encode("utf-8")
        rel = book_release(book)
        for why, opener in (("another file", lambda url: Response(bytes([book[0] ^ 1]) + book[1:])),
                            ("one byte more", lambda url: Response(book + b" ")),
                            ("cut short", lambda url: Response(book[:-1])),
                            ("offline", mock.Mock(side_effect=OSError("offline"))),
                            ("a cut reply", lambda url: Cut(b""))):
            for lang in ("us", "fr"):
                with self.subTest(why=why, lang=lang):
                    self.assertEqual(update.changes_in(rel, lang, "0.8.0", opener=opener), [])  # nothing shown
        self.assertEqual(update.changes_in(dataclasses.replace(rel, notes_url=""), "us", "0.8.0",
                                           opener=lambda url: Response(book)), [])   # no signed notes file: none
        self.assertTrue(update.changes_in(rel, "us", "0.8.0", opener=lambda url: Response(book)))  # CONTROL

    def test_a_version_never_translated_stays_english_beside_the_translated_one(self):
        book = json.dumps({"us": NOTES, "fr": FRENCH}).encode("utf-8")   # 0.8.1 only, in French
        got = update.changes_in(book_release(book), "fr", "0.7.6", opener=lambda url: Response(book))
        self.assertEqual([(r["version"], r["now"]) for r in got], [
            ("0.8.1", "Elle marche dans toutes les parties."), ("0.8.0", "**New brushes**"), ("0.8.0", "**Check this map**")])

    def test_the_check_takes_the_language(self):
        with tempfile.TemporaryDirectory() as d:
            app = App(d)
            self.assertEqual(app.update_check("fr")["changes"], [{"version": "0.2.0", "before": "Ancien.", "now": "Nouveau."}])
            self.assertEqual(app.update_check()["changes"], [{"version": "0.2.0", "before": "Old.", "now": "New."}])


class App(UpdateCalls):
    UPDATE_APP, UPDATE_VERSION = "launcher", "0.1.0"

    def __init__(self, home, installed=True, rels=None):
        self._home, self._jobs = home, {}
        self.rels = rels if rels is not None else [release("launcher-v0.2.0")]
        self._update_fetch = lambda url: self.rels
        self._update_fetch_sig = fetch_sig
        self._update_opener = lambda url: Response(BOOK if url.endswith("notes.json") else SETUP)
        self._update_popen = mock.Mock()
        self._update_quit = mock.Mock()
        self._update_installed = lambda: installed
        self._update_open_url = mock.Mock()

    def update_check(self, lang="us"):
        with mock.patch.object(releasesig, "RELEASE_KEYS", KEYS):   # the test keys stand for the owner's
            return super().update_check(lang)


def finish(app, job):
    for _ in range(300):
        if app._jobs[job].state != "running":
            break
        time.sleep(0.02)
    return app._jobs[job].view()


def kept(d):
    return json.loads((Path(d) / "settings.json").read_text(encoding="utf-8"))


class Calls(unittest.TestCase):
    def test_check_then_install(self):
        with tempfile.TemporaryDirectory() as d:
            app = App(d)
            self.assertEqual(app.update_check()["version"], "0.2.0")
            app.update_page()
            app._update_open_url.assert_called_once_with(f"{REPO}/releases/tag/launcher-v0.2.0")
            view = finish(app, app.update_install()["job"])
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
            quiet = App(d, rels=[release("launcher-v0.1.0")])
            self.assertEqual(quiet.update_check(), {"available": False, "version": "0.1.0", "current": "0.1.0"})

    def test_an_update_not_signed_by_him_is_not_installed_and_points_to_his_discord(self):
        from rusemod.owned import DISCORD
        with tempfile.TemporaryDirectory() as d:
            app = App(d, rels=[release("launcher-v0.2.0", signed=False, body="<!-- required update -->")])
            said = app.update_check()
            self.assertEqual((said["available"], said["unconfirmed"], said["unconfirmed_version"], said["version"]),
                             (False, True, "0.2.0", "0.1.0"))   # "version" stays the running one
            self.assertNotIn("required", said)
            with self.assertRaisesRegex(UpdateError, "no update to install"):
                app.update_install()
            app._update_popen.assert_not_called()
            self.assertEqual(app.update_page(), {"opened": DISCORD})
            app._update_open_url.assert_called_once_with(DISCORD)

    def test_the_wrong_file_is_refused_and_the_refusal_kept(self):
        from rusemod.owned import DISCORD
        with tempfile.TemporaryDirectory() as d:
            app = App(d)
            app.update_check()
            app._update_opener = lambda url: Response(bytes(len(SETUP)))   # the same size, other bytes
            view = finish(app, app.update_install()["job"])
            self.assertEqual(view["state"], "failed")
            self.assertIn("isn't the one we signed", view["message"])
            app._update_popen.assert_not_called()
            again = App(d)            # the next start: refused, not offered, our Discord
            said = again.update_check()
            self.assertEqual((said["available"], said["refused"], said["version"]), (False, True, "0.2.0"))
            self.assertIn("isn't the one we signed", said["why"])
            self.assertEqual(again.update_page(), {"opened": DISCORD})
            listed = App(d, rels=[release("launcher-v0.2.0", size=5)])   # GitHub's listing already shows another file
            said = listed.update_check()
            self.assertEqual((said["available"], said["refused"]), (False, True))
            with self.assertRaisesRegex(UpdateError, "isn't the one we signed"):
                listed.update_install()
            newer = App(d, rels=[release("launcher-v0.3.0")])   # a newer signed release: offered again
            self.assertTrue(newer.update_check()["available"])

    def test_after_three_failed_tries_it_stops_by_itself_and_points_to_the_release_page(self):
        with tempfile.TemporaryDirectory() as d:
            for n in range(1, update.TRIES + 1):
                app = App(d)
                said = app.update_check()
                self.assertNotIn("gave_up", said)
                app._update_opener = mock.Mock(side_effect=OSError("no connection"))
                view = finish(app, app.update_install()["job"])
                self.assertEqual(view["state"], "failed")
                self.assertEqual(kept(d)["update_tries"]["launcher"]["count"], n)
            app = App(d)
            said = app.update_check()
            self.assertEqual((said["available"], said["gave_up"], said["tries"]), (True, True, update.TRIES))
            self.assertEqual(app.update_page(), {"opened": f"{REPO}/releases/tag/launcher-v0.2.0"})
            view = finish(app, app.update_install()["job"])   # Try again still works, by hand
            self.assertEqual(view["state"], "done")


class Required(unittest.TestCase):
    """A required update (the owner, 2026-10-30: "a box it can't skip ... it should update by itself without
    asking"): the owner's signed threshold marks it; the app keeps it, says it, and Play and Test in game wait."""

    def app(self, d, rels):
        app = App(d, rels=rels)
        app.strings = lambda lang="us": {"update_required_refused": "{app} has a required update to install first."}
        app.prefs = lambda: {}
        app._starter = mock.Mock(required=None)
        app.use_required_updates()
        return app

    def test_only_the_signed_threshold_makes_it_required(self):
        with tempfile.TemporaryDirectory() as d:
            text = "**0.4.0:** the newest\n\n**0.3.0:** required\n<!-- required update -->\n"
            plain = self.app(d, [release("launcher-v0.4.0", body=text)])      # the text says it, he didn't sign it
            self.assertEqual(plain.update_check()["required"], False)
            self.assertIsNone(plain._update_refusal())
            signed = self.app(d, [release("launcher-v0.4.0", required="0.3.0")])
            said = signed.update_check()
            self.assertEqual((said["version"], said["required"]), ("0.4.0", True))
            self.assertEqual(kept(d)["required_signed"], {"launcher": "0.3.0"})
            self.assertEqual(signed._update_refusal(), "RUSE Launcher has a required update to install first.")
            above = self.app(d, [release("launcher-v0.4.0", required="0.3.0")])
            above.UPDATE_VERSION = "0.3.0"                                    # at the threshold: offered, not forced
            self.assertEqual(above.update_check()["required"], False)

    def test_kept_while_offline_and_never_from_the_old_unsigned_key(self):
        with tempfile.TemporaryDirectory() as d:
            self.app(d, [release("launcher-v0.4.0", required="0.3.0")]).update_check()
            offline = self.app(d, [])

            def unreachable(url):
                raise OSError("no connection")
            offline._update_fetch = offline._update_fetch_text = unreachable
            said = offline.update_check()
            self.assertEqual((said["required"], said["offline"], said["version"]), (True, True, "0.3.0"))
            self.assertTrue(offline._update_refusal())
            done = self.app(d, [release("launcher-v0.4.0", required="0.3.0")])
            done.UPDATE_VERSION = "0.4.0"   # once it's in, nothing is required or kept
            self.assertEqual(done.update_check()["available"], False)
            self.assertNotIn("launcher", kept(d)["required_signed"])
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "settings.json").write_text(json.dumps({"required_update": {"launcher": "99.0.0"}}), encoding="utf-8")
            old = self.app(d, [])
            old._update_fetch = old._update_fetch_text = unreachable
            self.assertNotIn("required", old.update_check())   # what unsigned text once marked blocks nothing
            self.assertIsNone(old._update_refusal())

    def test_a_required_one_keeps_its_block_when_it_fails(self):
        """His words of 2026-11-25: after a few failed tries, stop retrying and point to the release page; a file not
        signed by him points to his Discord; the required update keeps its block meanwhile."""
        with tempfile.TemporaryDirectory() as d:
            for _ in range(update.TRIES):
                app = self.app(d, [release("launcher-v0.4.0", required="0.4.0")])
                app.update_check()
                app._update_opener = mock.Mock(side_effect=OSError("no connection"))
                finish(app, app.update_install()["job"])
            app = self.app(d, [release("launcher-v0.4.0", required="0.4.0")])
            said = app.update_check()
            self.assertEqual((said["required"], said["gave_up"]), (True, True))
            self.assertTrue(app._update_refusal())          # Play and Test in game still wait
            wrong = self.app(d, [release("launcher-v0.4.0", required="0.4.0", digest="0" * 64)])
            said = wrong.update_check()
            self.assertEqual((said["required"], said["refused"]), (True, True))
            self.assertTrue(wrong._update_refusal())

    def test_when_github_answers_with_nothing_of_his_the_kept_block_goes_as_before(self):
        with tempfile.TemporaryDirectory() as d:
            self.app(d, [release("launcher-v0.4.0", required="0.4.0")]).update_check()
            gone = self.app(d, [release("launcher-v0.5.0", signed=False)])   # GitHub answers: nothing of his requires it
            self.assertTrue(gone.update_check()["unconfirmed"])
            self.assertIsNone(gone._update_refusal())

    def test_play_and_test_in_game_wait_for_it(self):
        from rusemod.build import BuildError
        from rusemod.play import Starter
        starter = Starter()
        starter.required = lambda: "RUSE Studio has a required update to install first."
        starter.owned = mock.Mock(return_value=None)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BuildError, "required update"):
                starter.modded(Path(d) / "game", [], Path(d) / "copies" / "Modded game", "set", lambda line: None)
        starter.owned.assert_not_called()  # nothing else is looked at first

    def test_both_apps_show_the_box_and_install_by_itself(self):
        root = Path(__file__).resolve().parents[1] / "src"
        self.assertEqual((root / "ruse_studio/ui/required.js").read_bytes(), (root / "ruse_launcher/ui/required.js").read_bytes())
        required = (root / "ruse_launcher/ui/required.js").read_text(encoding="utf-8")
        for word in ("update_required_not_ours", "update_required_gave_up", "update_discord", "release_page",
                     "tip_update_discord", "tip_release_page", "v.page && v.page()"):
            self.assertIn(word, required)
        for app in ("ruse_studio", "ruse_launcher"):
            with self.subTest(app=app):
                page = (root / app / "ui/index.html").read_text(encoding="utf-8")
                self.assertLess(page.index('<script src="required.js"></script>'), page.index('<script src="app.js"></script>'))
                self.assertIn('id="update-page"', page)
                js = (root / app / "ui/app.js").read_text(encoding="utf-8")
                self.assertIn("window.requiredUpdate(", js)
                self.assertIn("u.required && u.available && u.installed && !u.gave_up && !state.updating) installUpdate()", js)
                self.assertIn('if (j.state === "failed") checkUpdate(false);', js)   # a failed try's result shows at once
                self.assertIn('$("update-page").addEventListener("click", () => api().update_page()', js)
                self.assertIn("api.use_required_updates()", (root / app / "app.py").read_text(encoding="utf-8"))
                self.assertIn('"required.js"', (root / app / "app.py").read_text(encoding="utf-8"))


class Words(unittest.TestCase):
    def test_every_new_word_in_both_apps_in_every_language(self):
        from rusemod.wordedtext import LANGS
        root = Path(__file__).resolve().parents[1] / "src"
        for app in ("ruse_studio", "ruse_launcher"):
            words = tomllib.loads((root / app / "words.toml").read_text(encoding="utf-8"))
            for key in ("update_not_ours", "update_ignored", "update_gave_up", "update_discord", "tip_update_discord",
                        "tip_release_page", "update_required_not_ours", "update_required_gave_up"):
                for lang in LANGS:
                    with self.subTest(app=app, key=key, lang=lang):
                        self.assertTrue(words[key][lang].strip())
                        self.assertEqual(sorted(set(re.findall(r"\{(\w+)\}", words[key][lang]))),
                                         sorted(set(re.findall(r"\{(\w+)\}", words[key]["us"]))))

    def test_the_refusals_in_the_player_s_language(self):
        said = update.words(UpdateError("Launcher 0.2.0 is out, but we can't confirm it's ours, so it isn't installed.",
                                        final=True), "ger")
        self.assertEqual(said, "Launcher 0.2.0 ist erschienen, aber wir können nicht bestätigen, dass es von uns ist, "
                               "deshalb wird es nicht installiert.")
        self.assertEqual(type(UpdateError("x", final=True)).__name__, "UpdateError")   # still matched by class name
        self.assertIn("UpdateError", update.SHARED_REFUSALS)


class NotesFiles(unittest.TestCase):
    def test_no_release_notes_hold_a_sha256(self):
        """Apps before the signature check take the first 64-hex string in a release's text as its installer's hash:
        the notes we write must never hold one."""
        notes = Path(__file__).resolve().parents[1] / ".github" / "release-notes"
        for path in sorted(notes.glob("*.md")):
            with self.subTest(path=path.name):
                self.assertIsNone(re.search(r"\b[0-9a-fA-F]{64}\b", path.read_text(encoding="utf-8")))


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
