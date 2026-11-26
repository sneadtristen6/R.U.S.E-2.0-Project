"""The owner's decisions of 2026-11-25 on RUSE Guard and around it (the legal fixes, QUESTIONS.md), on the apps' side:

- 13 A: the app builds Steam's sign-in address itself and never opens a link the sign-in server gives;
- 11 A, on this PC: refused RUSE Guard records are cleared after 30 days, and an update's installer is deleted once
  it's installed;
- 36 B: the Launcher's Vanilla always builds a plain copy (the game's own title, RUSE Guard in it like every copy) and
  starts it through the Launcher's own path, with Play's checks and watches, never Steam's start link;
- 18 B: the apps' first update check waits until the agreement is accepted.

Nothing here reaches a server or starts anything: the sign-in server, GitHub, the RUSE Guard server and the game are
stand-ins (a made-up game folder, faked calls, a local web server).

These tests read none of the game's code. The RUSE.exe named here is the made-up game's two-byte stand-in that
test_launcher's Base writes, handed to a stand-in that "starts" it."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import re
import shutil
import tempfile
import threading
import time
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

from rusemod import fairplay, guard, ownedpass, update
from rusemod.home import save_settings, settings
from rusemod.play import SHARED, STEAM_PLAY
from test_launcher import Base, wait_for

ROOT = Path(__file__).resolve().parents[1]
DAY = 86400
CODE = "Ab0_-" * 8 + "Zz9"   # 43 characters: a sign-in code's shape (worker.js CODE_SHAPE)


class SignInApi(ownedpass.OwnedPassCalls):
    """The sign-in calls as both apps have them, with the browser replaced: what would be opened is kept."""

    def __init__(self, home):
        self._home = Path(home)
        self.opened = []

    def prefs(self):
        return {"lang": "us"}

    def _community_open(self, url):
        self.opened.append(url)
        return {"opened": url}


class SteamSignInAddress(unittest.TestCase):
    """13 A: "the app makes the Steam sign-in address itself" (QUESTIONS.md 13: "today a changed server could make the
    app open a program"). Whatever the server answers, the browser is sent only to Steam's own sign-in page, with the
    return address on our sign-in server that the app already knows."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, True)
        self.api = SignInApi(self.home)
        patcher = mock.patch.object(ownedpass, "ON", True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def server_answers(self, body, status=200):
        asked = []

        def call(url, data=None, timeout=30):
            asked.append(url)
            return status, body
        patcher = mock.patch.object(ownedpass, "_call", call)
        patcher.start()
        self.addCleanup(patcher.stop)
        return asked

    def fields(self, address):
        parts = urllib.parse.urlsplit(address)
        self.assertEqual(f"{parts.scheme}://{parts.netloc}{parts.path}", "https://steamcommunity.com/openid/login")
        return dict(urllib.parse.parse_qsl(parts.query, strict_parsing=True))

    def test_a_link_the_server_gives_is_never_opened(self):
        # a changed server: its "login link" a program on the PC, a file share, another site
        for link in ("C:\\Windows\\System32\\calc.exe", "\\\\attacker\\share\\setup.cmd", "file:///C:/x.bat",
                     "https://steamcommunity.example/openid/login", "ms-settings:privacy"):
            with self.subTest(link=link):
                self.api.opened.clear()
                self.server_answers({"code": CODE, "login_url": link, "poll_every": 3, "expires_in": 600})
                out = self.api.owned_sign_in_start()
                self.assertEqual(len(self.api.opened), 1)
                opened = self.api.opened[0]
                self.assertNotIn(link, opened)
                self.assertTrue(opened.startswith("https://steamcommunity.com/openid/login?"), opened)
                self.assertEqual((out["on"], out["code"], out["login_url"]), (True, CODE, opened))

    def test_the_address_is_the_one_the_server_s_own_login_sends_the_browser_to(self):
        # the fields of the sign-in server's /v1/steam/login (ruse-owned worker.js login()), whose /v1/steam/return
        # checks openid.return_to against exactly this return address
        self.server_answers({"code": CODE, "login_url": "https://anything", "poll_every": 3, "expires_in": 600})
        self.api.owned_sign_in_start()
        self.assertEqual(self.fields(self.api.opened[0]), {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": f"{ownedpass.SERVER}/v1/steam/return?code={CODE}",
            "openid.realm": f"{ownedpass.SERVER}/",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        })

    def test_the_return_address_is_the_server_s_origin_as_the_server_names_it(self):
        for server, origin in (("https://ruse-owned.sneadtristen6.workers.dev", "https://ruse-owned.sneadtristen6.workers.dev"),
                               ("HTTPS://Ruse-Owned.Example:443/", "https://ruse-owned.example"),
                               ("http://127.0.0.1:8787/v1", "http://127.0.0.1:8787"),
                               ("http://[::1]:80", "http://[::1]")):
            with self.subTest(server=server):
                fields = self.fields(ownedpass.steam_login_url(server, CODE))
                self.assertEqual((fields["openid.return_to"], fields["openid.realm"]),
                                 (f"{origin}/v1/steam/return?code={CODE}", f"{origin}/"))

    def test_a_server_moved_in_settings_is_the_return_address(self):
        save_settings(self.home, {ownedpass.SERVER_SETTING: "http://127.0.0.1:8787"})
        asked = self.server_answers({"code": CODE, "poll_every": 3, "expires_in": 600})   # (no link at all: fine)
        self.api.owned_sign_in_start()
        self.assertEqual(asked, ["http://127.0.0.1:8787/v1/steam/start"])
        self.assertEqual(self.fields(self.api.opened[0])["openid.return_to"],
                         f"http://127.0.0.1:8787/v1/steam/return?code={CODE}")

    def test_a_code_that_isnt_a_sign_in_code_opens_nothing(self):
        for code in ("short", CODE + "x", CODE[:-1] + "&", "x&openid.return_to=https://elsewhere" + "a" * 8, "", 42):
            with self.subTest(code=code):
                self.api.opened.clear()
                self.server_answers({"code": code, "login_url": "https://ruse-owned.example/v1/steam/login",
                                     "poll_every": 3, "expires_in": 600})
                with self.assertRaises(ownedpass.OwnedPassError):
                    self.api.owned_sign_in_start()
                self.assertEqual(self.api.opened, [])
        with self.assertRaises(ValueError):
            ownedpass.steam_login_url("https://ruse-owned.example", "short")
        for server in ("ftp://ruse-owned.example", "C:\\server", "https://user:pw@ruse-owned.example", "https://"):
            with self.subTest(server=server), self.assertRaises(ValueError):
                ownedpass.steam_login_url(server, CODE)

    def test_start_passes_no_link_on(self):
        self.server_answers({"code": CODE, "login_url": "C:\\Windows\\System32\\calc.exe", "poll_every": 5,
                             "expires_in": 300})
        self.assertEqual(ownedpass.start("https://ruse-owned.example"),
                         {"code": CODE, "poll_every": 5, "expires_in": 300})


class RefusedRecordsGo(unittest.TestCase):
    """11 A on this PC: "refused RUSE Guard records are cleared after 30 days". A bundle the server refused for good is
    set aside (guard.REFUSED) for a look, and deleted 30 days after it was refused, at a delivery or an app's start."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.home = self.dir / "home"
        self.outbox, self.refused = self.home / guard.OUTBOX, self.home / guard.REFUSED
        self.outbox.mkdir(parents=True)

    def kept(self, name, age_days):
        """A bundle kept in the outbox `age_days` ago (its file's time)."""
        p = self.outbox / f"{name}.json"
        p.write_text(json.dumps({"bundle_id": name}), encoding="utf-8")
        then = time.time() - age_days * DAY
        os.utime(p, (then, then))
        return p

    def aside(self, name, age_days):
        """A bundle refused `age_days` ago, as set_aside leaves it."""
        self.refused.mkdir(parents=True, exist_ok=True)
        p = self.refused / f"{name}.json"
        p.write_text("{}", encoding="utf-8")
        then = time.time() - age_days * DAY
        os.utime(p, (then, then))
        return p

    def names(self):
        return sorted(p.stem for p in self.refused.glob("*.json"))

    def test_gone_30_days_after_it_was_refused(self):
        guard.set_aside(self.home, self.kept("old-match", 45))   # kept 45 days (no server), refused now
        now = time.time()
        self.assertEqual(guard.clear_refused(self.home, now), 0)                   # its days count from the refusal
        self.assertEqual(guard.clear_refused(self.home, now + 30 * DAY - 60), 0)  # a minute short of 30 days
        self.assertEqual(self.names(), ["old-match"])
        self.assertEqual(guard.clear_refused(self.home, now + 30 * DAY + 1), 1)
        self.assertEqual(self.names(), [])

    def test_only_those_past_30_days_go(self):
        for name, age in (("a-31", 31), ("b-30", 30.001), ("c-29", 29), ("d-today", 0)):
            self.aside(name, age)
        (self.refused / "notes.txt").write_text("not a bundle", encoding="utf-8")
        self.assertEqual(guard.clear_refused(self.home), 2)
        self.assertEqual(self.names(), ["c-29", "d-today"])
        self.assertTrue((self.refused / "notes.txt").is_file())   # only refused bundles are ours to clear
        self.assertEqual(guard.clear_refused(self.dir / "no-home-yet"), 0)

    def test_a_delivery_clears_the_old_ones(self):
        class Takes(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"accepted": true}')

            def log_message(self, *a):
                pass
        server = HTTPServer(("127.0.0.1", 0), Takes)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.aside("refused-long-ago", 31)
        self.aside("refused-last-week", 7)
        log = guard.MatchLog(started=1791000000, multiplayer=True, coop=False, local="1", states=[(10.0, "a")])
        body = guard.bundle(self.home, log, username="Nick#4821", record={}, replay=None, manifests=[],
                            dev=guard.DevKey(False, "none"), findings=[], ended=1791000600)
        said = guard.deliver(self.home, body, f"http://127.0.0.1:{server.server_port}")
        self.assertEqual(said, "sent 1; 0 waiting")
        self.assertEqual(self.names(), ["refused-last-week"])

    def test_both_apps_clear_them_as_they_start(self):
        for app in ("ruse_launcher", "ruse_studio"):
            with self.subTest(app=app):
                src = (ROOT / "src" / app / "app.py").read_text(encoding="utf-8")
                self.assertIn("clear_refused(api._home)", src)


class InstallersGo(unittest.TestCase):
    """11 A on this PC: "an update's installer is deleted once installed". The app downloads it into <home>/updates
    (rusemod.update.update_install), the installer puts the new version in and starts the app again, and that start
    deletes it."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, True)
        self.updates = self.home / "updates"
        self.updates.mkdir()

    def file(self, name):
        (self.updates / name).write_bytes(b"MZ")

    def left(self):
        return sorted(p.name for p in self.updates.iterdir())

    def test_the_installed_one_and_older_go_the_rest_stay(self):
        for name in ("RUSE-Launcher-Setup-0.4.8.21.exe", "RUSE-Launcher-Setup-0.4.8.22.exe",
                     "RUSE-Launcher-Setup-0.4.8.22.part", "RUSE-Launcher-Setup-0.4.8.23.exe",
                     "RUSE-Launcher-Setup-0.4.9.exe", "RUSE-Studio-Setup-0.9.8.22.exe", "notes.txt"):
            self.file(name)
        gone = update.clear_installed(self.home, "launcher", "0.4.8.22")
        self.assertEqual(sorted(gone), ["RUSE-Launcher-Setup-0.4.8.21.exe", "RUSE-Launcher-Setup-0.4.8.22.exe",
                                        "RUSE-Launcher-Setup-0.4.8.22.part"])
        # a newer one not installed yet, the other app's and anything else stay
        self.assertEqual(self.left(), ["RUSE-Launcher-Setup-0.4.8.23.exe", "RUSE-Launcher-Setup-0.4.9.exe",
                                       "RUSE-Studio-Setup-0.9.8.22.exe", "notes.txt"])
        self.assertEqual(update.clear_installed(self.home, "studio", "0.9.8.22"), ["RUSE-Studio-Setup-0.9.8.22.exe"])
        self.assertEqual(update.clear_installed(self.home / "nothing-here", "studio", "1.0.0"), [])

    def test_the_downloaded_installer_goes_at_the_first_start_after_it(self):
        from test_update import App
        app = App(self.home)                                   # Launcher 0.1.0, 0.2.0 out
        self.assertEqual(app.update_check()["version"], "0.2.0")
        job = app.update_install()["job"]
        for _ in range(250):
            if app._jobs[job].state != "running":
                break
            time.sleep(0.02)
        self.assertEqual(app._jobs[job].state, "done", app._jobs[job].view())
        self.assertEqual(self.left(), ["RUSE-Launcher-Setup-0.2.0.exe"])   # run (a stand-in), the app quits
        self.assertEqual(update.clear_installed(self.home, "launcher", "0.1.0"), [])   # (not in yet: it stays)
        # the installer starts the app again, now 0.2.0
        self.assertEqual(update.clear_installed(self.home, "launcher", "0.2.0"), ["RUSE-Launcher-Setup-0.2.0.exe"])
        self.assertEqual(self.left(), [])

    def test_both_apps_clear_them_as_they_start(self):
        for app, name in (("ruse_launcher", "launcher"), ("ruse_studio", "studio")):
            with self.subTest(app=app):
                src = (ROOT / "src" / app / "app.py").read_text(encoding="utf-8")
                self.assertIn(f'clear_installed(api._home, "{name}", __version__)', src)


class VanillaIsOurCopy(Base):
    """36 B: "the Launcher's Vanilla always builds a plain copy, with the game's own title and RUSE Guard in it like
    every copy, and starts it through the Launcher's own path with its watches and checks, never Steam's start link"
    (the owner: "if they're using our apps, they should be using [RUSE] Guard. If they want to play vanilla [R.U.S.E.],
    they can just go in on Steam").

    The made-up game has no map-scripts pack for RUSE Guard's scripts to go into, so with no mods its build changes
    nothing and writes no copy (build_and_write: "The mods change nothing in these packs."); in the game they always go
    in (tests/test_fairplay.py Scripts). Where a copy has to come out, the build is a stand-in here (built): it is
    handed what the real one would be, and writes the copy's program file."""

    def built(self):
        """build_and_write's stand-in: what it was handed, each time; it leaves a copy with the program file in it."""
        calls = []

        def build(game, mods, *, instance=None, signature=False, fairplay=None, **kw):
            calls.append({"game": game, "mods": list(mods), "instance": instance, "signature": signature,
                          "fairplay": fairplay})
            Path(instance).mkdir(parents=True, exist_ok=True)
            (Path(instance) / "RUSE.exe").write_bytes(b"MZ")
            return type("Result", (), {"errors": [], "order": []})()
        patcher = mock.patch("rusemod.play.build_and_write", build)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def test_vanilla_with_the_game_s_own_title_builds_a_plain_copy_and_starts_it(self):
        builds = self.built()
        api = self.api()
        api.set_game_title(False)
        j = wait_for(api, api.play("vanilla")["job"])
        self.assertEqual(j["state"], "done", j)
        copy = self.instances / SHARED
        (build,) = builds
        self.assertEqual((build["game"], build["mods"], build["instance"], build["signature"]),
                         (self.game, [], copy, False))                 # no mods, the game's own title
        self.assertEqual(build["fairplay"].patches(), [fairplay.game_script(fairplay.WATCH),
                                                       fairplay.game_script(fairplay.GUARD)])  # RUSE Guard in it
        self.assertEqual(self.started, [copy / "RUSE.exe"])       # started from our copy
        self.assertNotIn(STEAM_PLAY, self.urls)                    # never Steam's start link
        self.assertEqual(self.urls, [])
        self.assertIn("Starting R.U.S.E. from the modded copy…", j["lines"])

    def test_on_this_made_up_game_the_real_build_says_why_no_copy_came(self):
        # the control for the stand-in: the real build, with nothing to change here, writes no copy and says so; and
        # never Steam's start link instead
        api = self.api()
        api.set_game_title(False)
        j = wait_for(api, api.play("vanilla")["job"])
        self.assertEqual(j["state"], "failed", j)
        self.assertIn("The mods change nothing in these packs.", j["lines"])
        self.assertIn("no RUSE Guard watcher", " ".join(j["lines"]))
        self.assertEqual((self.urls, self.started), ([], []))

    def test_both_titles_go_the_same_way_with_ruse_guard(self):
        for title in (False, True):
            with self.subTest(title=title):
                api = self.api()
                api.set_game_title(title)
                with mock.patch("rusemod.play.Starter.modded", autospec=True) as modded:
                    j = wait_for(api, api.play("vanilla")["job"])
                self.assertEqual((j["state"], self.urls), ("done", []), j)
                (_starter, game, folders, instance, name, _say), kw = modded.call_args
                self.assertEqual((game, folders, instance, name, kw["title"]),
                                 (self.game, [], self.instances / SHARED, "Vanilla", title))
                # RUSE Guard's side, as for every set: the platform folder and the player's RUSE Guard settings
                self.assertTrue(fairplay.ON)
                self.assertEqual(kw["guard"]["home"], self.home)
                self.assertEqual(kw["guard"]["consent"], api.guard_status())

    def test_the_copy_gets_ruse_guard_s_scripts_and_the_match_watch_follows_the_game(self):
        class Game:   # the game's process, as start_game hands it back
            def poll(self):
                return 0
        game = Game()
        self.built()
        api = self.api(start_game=lambda exe: (self.started.append(exe), game)[1])
        api.set_game_title(False)
        checked = []
        real_check = fairplay.check
        with mock.patch("rusemod.fairplay.check", lambda folders, *a, **kw: checked.append(list(folders))
                        or real_check(folders, *a, **kw)), \
                mock.patch("rusemod.guard.MatchWatch") as watch:
            j = wait_for(api, api.play("vanilla")["job"])
        self.assertEqual(j["state"], "done", j)
        self.assertEqual(checked, [[]])   # the fair play check of a copy with no mods: RUSE Guard's scripts go in
        self.assertEqual(fairplay.check([]).patches(), [fairplay.game_script(fairplay.WATCH),
                                                        fairplay.game_script(fairplay.GUARD)])
        watch.assert_called_once()
        args, kw = watch.call_args
        self.assertEqual(args[:4], (game, self.home, self.game, self.instances / SHARED))
        watch.return_value.start.assert_called_once()

    def test_vanilla_meets_play_s_checks(self):
        refusals = {"required": "RUSE Launcher has a required update to install first.",
                    "owned": "This copy of R.U.S.E. couldn't be confirmed as one you own."}
        for which, said in refusals.items():
            with self.subTest(which=which):
                api = self.api()
                api.set_game_title(False)
                if which == "required":
                    api._starter.required = lambda said=said: said
                else:
                    api._starter.owned = lambda game, said=said: said
                j = wait_for(api, api.play("vanilla")["job"])
                self.assertEqual((j["state"], j["message"]), ("failed", said))
                self.assertEqual((self.urls, self.started), ([], []))   # nothing started, Steam's link least of all

    def test_the_launcher_s_words_no_longer_say_vanilla_starts_through_steam(self):
        from ruse_launcher.api import words
        langs = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
        for lang in langs:
            w = words(lang)
            for key in ("set_title_help", "title_off_note"):
                with self.subTest(lang=lang, key=key):
                    self.assertNotIn("Steam", w[key])
        self.assertEqual(words("us")["title_off_note"], "The next Play gives your game the game's own R.U.S.E. title "
                                                        "and Eugen's logo video, Vanilla too.")

    def test_no_start_through_steam_is_left(self):
        from rusemod.play import Starter
        self.assertFalse(hasattr(Starter, "vanilla"))
        api_src = (ROOT / "src" / "ruse_launcher" / "api.py").read_text(encoding="utf-8")
        self.assertNotIn("_starter.vanilla(", api_src)
        self.assertNotIn("STEAM_PLAY", (ROOT / "src" / "rusemod" / "play.py").read_text(encoding="utf-8")
                         .split("STEAM_PLAY =", 1)[1])   # named once, used nowhere


class UpdatesAfterTheAgreement(unittest.TestCase):
    """18 B: "the apps' first update check waits until the agreement is accepted". The page asks only after its
    agreement screen; the back end holds every check until then too (use_agreement_first, from each app's window)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        from ruse_launcher.api import LauncherApi
        from ruse_studio.api import StudioApi
        self.apps = {"launcher": LauncherApi(home=self.tmp / "home", game_dir=self.tmp / "nowhere"),
                     "studio": StudioApi(home=self.tmp / "home", game_dir=self.tmp / "nowhere",
                                         index_path=self.tmp / "x.sqlite")}
        self.asked = []
        for name, api in self.apps.items():
            api._update_fetch = lambda url, name=name: (self.asked.append(name), [])[1]
            api._update_fetch_text = lambda url, name=name: (self.asked.append(name), "")[1]
            api.use_agreement_first()

    def check_all(self):
        return {name: api.update_check() for name, api in self.apps.items()}

    def test_nothing_is_asked_before_the_agreement_then_it_is(self):
        self.assertTrue(fairplay.ON)
        for name, said in self.check_all().items():
            with self.subTest(app=name):
                self.assertEqual(said, {"available": False, "current": self.apps[name].UPDATE_VERSION,
                                        "waiting": "agreement"})
        self.assertEqual(self.asked, [])   # GitHub was never asked
        self.apps["launcher"].guard_accept_terms()   # the first-start screen's Accept (either app: one settings file)
        for name, said in self.check_all().items():
            with self.subTest(app=name):
                self.assertNotIn("waiting", said)
                self.assertFalse(said["available"])   # (the made-up GitHub has no release)
        self.assertEqual(sorted(self.asked), ["launcher", "studio"])

    def test_an_agreement_shown_again_holds_it_until_accepted_again(self):
        save_settings(self.tmp / "home", {"guard": {"terms": guard.TERMS_VERSION - 1}})   # accepted an older version
        self.assertEqual({n: s.get("waiting") for n, s in self.check_all().items()},
                         {"launcher": "agreement", "studio": "agreement"})
        self.apps["studio"].guard_accept_terms()
        self.assertEqual(settings(self.tmp / "home")["guard"]["terms"], guard.TERMS_VERSION)
        self.assertEqual({n: s.get("waiting") for n, s in self.check_all().items()},
                         {"launcher": None, "studio": None})

    def test_with_fair_play_off_there_is_no_agreement_to_wait_for(self):
        with mock.patch.object(fairplay, "ON", False):
            said = self.check_all()
        self.assertEqual({n: s.get("waiting") for n, s in said.items()}, {"launcher": None, "studio": None})
        self.assertEqual(sorted(self.asked), ["launcher", "studio"])

    def test_both_windows_hold_it_and_both_pages_ask_only_after_the_agreement(self):
        for app in ("ruse_launcher", "ruse_studio"):
            with self.subTest(app=app):
                self.assertIn("api.use_agreement_first()", (ROOT / "src" / app / "app.py").read_text(encoding="utf-8"))
                js = (ROOT / "src" / app / "ui" / "app.js").read_text(encoding="utf-8")
                start = js[js.index("async function start()"):]
                start = start[:start.index("\n}\n")]
                calls = [m.start() for m in re.finditer(r"\bcheckUpdate\(\)", start)]
                self.assertEqual(len(calls), 1, "one update check as the app starts")
                self.assertGreater(calls[0], start.index("await window.Agreement.open("))
                self.assertLess(start.index("showVersion();"), start.index("await openLangPick(true)"))


if __name__ == "__main__":
    unittest.main()
