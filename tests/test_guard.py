"""RUSE Guard, the Launcher's side (rusemod.guard): signed tokens in DomesticNukes' format, dev keys, signed mod
manifests, the in-game record, the process scan, its list inside the app and the game's lines that say a match is on,
and a match's evidence bundle kept or sent.

Checked our_tools.json: none of its tools tests the Launcher's own code; these tests read no program: where they name
the game's program file, it is a made-up path handed to a stand-in for starting a program."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

from rusemod import ed25519, guard

SECRET = bytes(range(32))
PUBLIC = ed25519.public_key(SECRET)
OTHER = ed25519.public_key(bytes(32))


class Tokens(unittest.TestCase):
    def test_signed_checked_and_tampering_fails(self):
        token = guard.make_token({"key_id": "k1", "holder": "nuke"}, SECRET)
        payload, why = guard.read_token(token, PUBLIC)
        self.assertEqual((payload["holder"], why), ("nuke", "ok"))
        self.assertEqual(guard.read_token(token, OTHER), (None, "bad signature"))
        self.assertEqual(guard.read_token(token, b""), (None, "no key to check it with yet"))
        body, sig = token.split(".")
        forged = guard._b64(guard.canonical({"key_id": "k1", "holder": "cheater", "alg": "Ed25519"})) + "." + sig
        self.assertEqual(guard.read_token(forged, PUBLIC), (None, "bad signature"))
        spaced = guard._b64(json.dumps({"alg": "Ed25519", "holder": "nuke"}).encode()) + "." + sig
        self.assertEqual(guard.read_token(spaced, PUBLIC), (None, "non-canonical payload"))
        hmac_one = guard._b64(guard.canonical({"alg": "HS256", "holder": "x"})) + "." + sig
        self.assertEqual(guard.read_token(hmac_one, PUBLIC), (None, "not an Ed25519 token"))
        self.assertEqual(guard.read_token("rubbish", PUBLIC), (None, "malformed token"))


class Keys(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_dev_keys(self):
        self.assertEqual(guard.dev_key(self.dir, PUBLIC).reason, "none")
        (self.dir / "guard").mkdir()
        key = self.dir / guard.DEV_KEY
        key.write_text(guard.make_token({"key_id": "k1", "holder": "nuke", "capabilities": ["*"],
                                         "scope": "all_dev_lobby", "expires": 2000}, SECRET), encoding="utf-8")
        ok = guard.dev_key(self.dir, PUBLIC, now=1000)
        self.assertEqual((ok.valid, ok.key_id, ok.holder, ok.scope), (True, "k1", "nuke", "all_dev_lobby"))
        self.assertEqual(guard.dev_key(self.dir, PUBLIC, now=3000).reason, "expired")
        self.assertEqual(guard.dev_key(self.dir, PUBLIC, now=1000, revoked={"k1"}).reason, "revoked")
        self.assertEqual(guard.dev_key(self.dir, OTHER, now=1000).reason, "bad signature")

    def test_no_keys_shipped_yet(self):
        self.assertEqual(guard.keys(), {"dev": b"", "mods": b""})  # the owner makes them (guard_keys.toml)

    def test_signed_mod_manifests(self):
        mod = self.dir / "tanks"
        (mod / "src").mkdir(parents=True)
        (mod / "mod.toml").write_text("[mod]\nid = \"tanks\"\n", encoding="utf-8")
        (mod / "src" / "tanks.rndf").write_text("Tiger.Cost = 100\n", encoding="utf-8")
        self.assertEqual(guard.check_manifest(mod, PUBLIC).reason, "not signed")
        files = guard.mod_files(mod)
        self.assertEqual(sorted(files), ["mod.toml", "src/tanks.rndf"])
        (mod / guard.MANIFEST).write_text(guard.make_token({"mod_id": "tanks", "version": "1.0.0", "files": files},
                                                           SECRET), encoding="utf-8")
        ok = guard.check_manifest(mod, PUBLIC)
        self.assertEqual((ok.verified, ok.mod_id, ok.version), (True, "tanks", "1.0.0"))
        (mod / "src" / "tanks.rndf").write_text("Tiger.Cost = 1\n", encoding="utf-8")  # one edited byte
        (mod / "src" / "cheat.rndf").write_text("x\n", encoding="utf-8")
        bad = guard.check_manifest(mod, PUBLIC)
        self.assertEqual((bad.verified, bad.changed, bad.extra), (False, ["src/tanks.rndf"], ["src/cheat.rndf"]))
        self.assertEqual(guard.check_manifest(mod, PUBLIC, revoked={"tanks@1.0.0"}).reason, "revoked manifest")
        self.assertEqual(guard.check_manifest(mod, OTHER).reason, "bad signature")


LOG = """start 1791000000 multi 1 coop 0 local 1
hotkey DevMoney parametres._mod_dev_money
state 10.0 aaaa
state 20.0 bbbb
end 25.5
start 1791000500 multi 1 coop 0 local 2
state 10.0 cccc
"""


class Record(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_read(self):
        a, b = guard.read_match_log(LOG + "garbage line\nstate x y\n")
        self.assertEqual((a.started, a.multiplayer, a.local, a.hotkeys, a.states, a.ended),
                         (1791000000, True, "1", [("DevMoney", "parametres._mod_dev_money")],
                          [(10.0, "aaaa"), (20.0, "bbbb")], 25.5))
        self.assertEqual((b.local, b.states, b.ended), ("2", [(10.0, "cccc")], None))
        (self.dir / guard.MATCH_LOG).write_text(LOG, encoding="utf-8")
        self.assertTrue(guard.live_multiplayer(self.dir))  # the last match has no end yet
        (self.dir / guard.MATCH_LOG).write_text(LOG + "end 30.0\n", encoding="utf-8")
        self.assertFalse(guard.live_multiplayer(self.dir))

    def test_the_scan_names_only_listed_tools(self):
        sigs = [{"name": "memtool.exe", "what": "a memory editor"}, {"name": "trainer.exe", "what": "a trainer"}]
        self.assertEqual(guard.scan(sigs, ["explorer.exe", "MemTool.exe", "steam.exe"]),
                         [{"name": "memtool.exe", "what": "a memory editor"}])
        self.assertEqual(guard.scan(sigs, ["explorer.exe"]), [])


class Bundle(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.home, self.game, self.copy = self.dir / "home", self.dir / "Steam/steamapps/common/RUSE", self.dir / "copy"
        for p in (self.home, self.game, self.copy):
            p.mkdir(parents=True)
        replays = self.dir / "Steam/userdata/42/21970/local"
        replays.mkdir(parents=True)
        (replays / "PROFILE.ruse2").write_bytes(b"p")
        (replays / "me_04_10_2026_000.ruserpl").write_bytes(b"SAV0 replay")

    def test_signed_and_kept_without_a_server(self):
        log = guard.read_match_log(LOG)[0]
        body = guard.bundle(self.home, log, username="Nick#4821", record={"fingerprint": "K7Q2-M9XD", "code": "RUSE1:X",
                                                                   "files": {"Data/a.dat": {"sha256": "ab"}}},
                            replay=None, manifests=[], dev=guard.DevKey(False, "none"), findings=[], ended=1791000100)
        self.assertTrue(guard.check_bundle(body))
        self.assertEqual((body["match"]["is_multiplayer"], body["evidence"]["state_series"], body["evidence"]["files"]),
                         (True, [[10.0, "aaaa"], [20.0, "bbbb"]], {"Data/a.dat": "ab"}))
        # the match is filed under the chosen username, never the Steam account number (no-steam-account-risk)
        self.assertEqual((body["match"]["players"], body["evidence"]["username"], body["evidence"]["player"]),
                         (["Nick#4821"], "Nick#4821", "Nick#4821"))
        self.assertEqual(guard.local_player(self.game), "42")  # the function still reads it; it is NOT put in a bundle
        self.assertNotIn("42", (body["evidence"]["player"], body["evidence"]["username"]))
        body["evidence"]["state_series"][0][1] = "zzzz"  # changed on its way
        self.assertFalse(guard.check_bundle(body))

    def test_collect_after_the_game_closes(self):
        (self.copy / guard.MATCH_LOG).write_text("start 1 multi 0 coop 0 local 1\n" + LOG, encoding="utf-8")
        said = guard.collect(self.home, self.game, self.copy, username="Nick#4821", server="", now=int(time.time()) + 5,
                             say=lambda s: None)
        self.assertEqual(len(said), 2)  # the two multiplayer matches; the offline one is never sent
        kept = sorted((self.home / guard.OUTBOX).glob("*.json"))
        self.assertEqual(len(kept), 2)
        body = json.loads(kept[0].read_text(encoding="utf-8"))
        self.assertTrue(guard.check_bundle(body))
        self.assertTrue(body["replay"])  # the replay saved after the match started went in
        self.assertFalse((self.copy / guard.MATCH_LOG).exists())  # read once

    def test_sent_to_a_server(self):
        got = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                got.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"accepted": true}')

            def log_message(self, *a):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        body = guard.bundle(self.home, guard.read_match_log(LOG)[0], username="Nick#4821", record={}, replay=None,
                            manifests=[], dev=guard.DevKey(False, "none"), findings=[], ended=1)
        said = guard.deliver(self.home, body, f"http://127.0.0.1:{server.server_port}")
        self.assertEqual((said, got[0][0], guard.check_bundle(got[0][1])), ("sent 1; 0 waiting", "/api/bundle", True))
        with self.assertRaises(guard.GuardError):
            guard.send("ftp://nope", body)

    def test_a_refused_bundle_is_set_aside_and_the_rest_still_send(self):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                seen.append(body["evidence"]["player"])
                refuse = body["evidence"]["player"].startswith("refuse")
                self.send_response(400 if refuse else 200)
                self.end_headers()
                self.wfile.write(b'{"accepted": false, "reason": "not a RUSE Guard bundle"}' if refuse
                                 else b'{"accepted": true}')

            def log_message(self, *a):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        log = guard.read_match_log(LOG)[0]
        refused = guard.bundle(self.home, log, username="refuse#0001", record={}, replay=None, manifests=[],
                               dev=guard.DevKey(False, "none"), findings=[], ended=1)
        outbox = self.home / guard.OUTBOX
        outbox.mkdir(parents=True, exist_ok=True)
        # "0-refuse.json" sorts before the good one's hex id, so it would block it if it weren't set aside
        (outbox / "0-refuse.json").write_text(json.dumps(refused), encoding="utf-8")
        good = guard.bundle(self.home, log, username="Keep#0002", record={}, replay=None, manifests=[],
                            dev=guard.DevKey(False, "none"), findings=[], ended=1)
        said = guard.deliver(self.home, good, f"http://127.0.0.1:{server.server_port}")
        self.assertEqual(said, "sent 1; 0 waiting; 1 set aside")
        self.assertEqual(seen, ["refuse#0001", "Keep#0002"])  # tried the refused one first, still sent the good one
        self.assertEqual([p.name for p in (self.home / guard.REFUSED).glob("*.json")], ["0-refuse.json"])
        self.assertEqual(list(outbox.glob("*.json")), [])

    def test_a_server_that_is_down_keeps_the_whole_outbox(self):
        # a 5xx (down or full) is not a refusal: the bundle and the rest stay to try later, nothing set aside
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"accepted": false, "reason": "the server is full"}')

            def log_message(self, *a):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        good = guard.bundle(self.home, guard.read_match_log(LOG)[0], username="Nick#4821", record={}, replay=None,
                            manifests=[], dev=guard.DevKey(False, "none"), findings=[], ended=1)
        said = guard.deliver(self.home, good, f"http://127.0.0.1:{server.server_port}")
        self.assertEqual(said, "sent 0; 1 waiting")
        self.assertFalse((self.home / guard.REFUSED).exists())

    # the offline lock's crash evidence. The dump deliberately plants a Steam ID, an account number and a path both
    # inside and outside the RUSEGUARD mark, so the test proves they're stripped before anything leaves the PC.
    DUMP = (b"module list junk 76561198087654321 outside\x00"
            b"RUSEGUARD-LOCK a cheat copy was stopped: it surrendered and left the match. multi 1 coop 0 local 0; "
            b"steam 76561198012345678 at C:\\Users\\bob\\AppData\\Local\\Temp\\x.dmp acct 226593310 RUSEGUARD-END"
            b" trailing junk 76561198011112222")

    def _dump(self, data: bytes) -> Path:
        p = self.dir / "report.dmp"
        p.write_bytes(data)
        return p

    def test_read_stop_extracts_the_mark_and_strips_identifiers(self):
        stop = guard.read_stop(self._dump(self.DUMP))
        self.assertIsNotNone(stop)
        self.assertIn("a cheat copy was stopped", stop["text"])
        self.assertEqual(stop["code"], "0x29a")
        for secret in ("76561198012345678", "76561198087654321", "226593310", "bob", "C:\\Users"):
            self.assertNotIn(secret, stop["text"])
        self.assertIn("<id>", stop["text"])
        self.assertIn("multi 1 coop 0 local 0", stop["text"])  # the team numbers stay (short digits)

    def test_read_stop_is_none_without_a_mark(self):
        self.assertIsNone(guard.read_stop(self._dump(b"a normal crash, no guard mark, 76561198012345678")))

    # the static format template, as it sits in a guard copy's script memory for ANY crash (the real 10-31 dump had it)
    TEMPLATE = (b"RUSEGUARD-LOCK a cheat copy was stopped: it surrendered and left the match. "
                b"multi %d coop %d local %s RUSEGUARD-END")
    FILLED = (b"RUSEGUARD-LOCK a cheat copy was stopped: it surrendered and left the match. "
              b"multi 1 coop 0 local 0 RUSEGUARD-END")

    def test_read_stop_prefers_the_filled_in_mark_over_the_template(self):
        # a real lock-crash report holds both; the filled-in line is the evidence, the template is a useless constant
        stop = guard.read_stop(self._dump(b"junk " + self.TEMPLATE + b" ... " + self.FILLED + b" junk"))
        self.assertIsNotNone(stop)
        self.assertIn("multi 1 coop 0 local 0", stop["text"])
        self.assertNotIn("%", stop["text"])

    def test_read_stop_ignores_a_template_only_dump(self):
        # only the template (no lock actually fired): not a stop, so nothing is collected or sent
        self.assertIsNone(guard.read_stop(self._dump(b"a crash of a guard copy " + self.TEMPLATE + b" and more")))

    def test_collect_stops_bundles_a_lock_crash_with_no_steam_id(self):
        local = self.dir / "LocalAppData"
        (local / "Temp" / "CrashRpt_abc").mkdir(parents=True)
        (local / "Temp" / "CrashRpt_abc" / "report.dmp").write_bytes(self.DUMP)
        said = guard.collect_stops(self.home, since=0, username="Nick#4821", server="", now=1791000200,
                                   local=str(local), say=lambda s: None)
        self.assertEqual(len(said), 1)
        kept = sorted((self.home / guard.OUTBOX).glob("*.json"))
        self.assertEqual(len(kept), 1)
        body = json.loads(kept[0].read_text(encoding="utf-8"))
        self.assertTrue(guard.check_bundle(body))
        self.assertIn("a cheat copy was stopped", body["evidence"]["stop"]["text"])
        self.assertEqual((body["match"]["players"], body["evidence"]["username"]), (["Nick#4821"], "Nick#4821"))
        whole = json.dumps(body)   # nothing Steam-shaped anywhere in what would be sent
        for secret in ("76561198012345678", "76561198087654321", "226593310"):
            self.assertNotIn(secret, whole)

    def test_every_handle_is_one_the_server_takes(self):
        # the agreement asks for a username only when the program check or Bug Watch is ticked; the server refuses
        # an empty handle (cloudflare/guard worker.js fieldsOf: 1 to 200 characters), so bundle() never sends one
        log = guard.read_match_log(LOG)[0]
        for username in ("", "Nick#4821", "x" * 34 + "#1234"):   # none, a usual one, the longest bugwatch makes
            body = guard.bundle(self.home, log, username=username, record={}, replay=None, manifests=[],
                                dev=guard.DevKey(False, "none"), findings=[], ended=1)
            handle = body["evidence"]["player"]
            self.assertTrue(guard.check_bundle(body))
            self.assertTrue(1 <= len(handle) <= 200, handle)
            self.assertEqual((body["match"]["players"], body["evidence"]["username"]), ([handle], username))
        anon = guard.bundle(self.home, log, username="", record={}, replay=None, manifests=[],
                            dev=guard.DevKey(False, "none"), findings=[], ended=1)
        # this install's own anonymous id (the start of the key every bundle carries); no "#", so it can't pass for
        # a chosen username (always Name#1234), and never a Steam ID
        self.assertEqual(anon["evidence"]["player"], "player-" + anon["client_key"][:12])
        self.assertNotIn("#", anon["evidence"]["player"])

    def test_the_match_watch_keeps_a_lock_crash_after_the_game_closes(self):
        local = self.dir / "LocalAppData"
        dumps = local / "Temp" / "CrashRpt_abc"

        class Game:   # the game's process: the lock crashes it during the match, then it's gone
            def __init__(self):
                self.polls = 0

            def poll(self):
                self.polls += 1
                if self.polls == 1:
                    dumps.mkdir(parents=True, exist_ok=True)
                    dump = dumps / "report.dmp"
                    dump.write_bytes(Bundle.DUMP)
                    # a real lock crash comes minutes after the watch starts; a file written microseconds after it
                    # can read a hair earlier than the watch's start (72 of 500 quick writes on Windows), so it's
                    # dated a second on, as a crash during the match would be
                    soon = time.time() + 1
                    os.utime(dump, (soon, soon))
                    return None
                return 0x29A

        for terms, kept_count in ((0, 0), (guard.TERMS_VERSION, 1)):   # nothing before the terms are accepted
            shutil.rmtree(self.home / "guard", ignore_errors=True)
            shutil.rmtree(local, ignore_errors=True)
            said = []
            guard.MatchWatch(Game(), self.home, self.game, self.copy, username="Nick#4821",
                             consent={"terms": terms, "scan": False, "server": ""}, manifests=[], say=said.append,
                             sleep=lambda s: None, local=str(local)).run()
            kept = sorted((self.home / guard.OUTBOX).glob("*.json"))
            self.assertEqual(len(kept), kept_count, terms)
        body = json.loads(kept[0].read_text(encoding="utf-8"))
        self.assertTrue(guard.check_bundle(body))
        self.assertEqual(body["evidence"]["player"], "Nick#4821")
        self.assertIn("a cheat copy was stopped", body["evidence"]["stop"]["text"])
        self.assertTrue(any("a cheat copy was stopped" in s for s in said), said)

    def test_a_lock_crash_with_no_username_still_goes_out(self):
        local = self.dir / "LocalAppData"
        (local / "Temp" / "CrashRpt_abc").mkdir(parents=True)
        (local / "Temp" / "CrashRpt_abc" / "report.dmp").write_bytes(self.DUMP)
        guard.collect_stops(self.home, since=0, username="", server="", now=1791000200, local=str(local),
                            say=lambda s: None)
        body = json.loads(next((self.home / guard.OUTBOX).glob("*.json")).read_text(encoding="utf-8"))
        self.assertTrue(guard.check_bundle(body))
        self.assertEqual(body["evidence"]["player"], "player-" + body["client_key"][:12])
        self.assertIn("a cheat copy was stopped", body["evidence"]["stop"]["text"])

    def _watch_scan(self, consent):
        # run a MatchWatch with the program check's module functions stubbed, and return (findings, whether it looked)
        looked = []
        orig = (guard.cheat_tools, guard.live_multiplayer, guard.scan)
        self.addCleanup(lambda: setattr_many(guard, orig))
        guard.cheat_tools = lambda *a, **k: (looked.append(1), [{"name": "x.exe", "what": "tool"}])[1]
        guard.live_multiplayer = lambda copy: True
        guard.scan = lambda sigs, programs=None: list(sigs)

        class Game:
            def __init__(self):
                self.n = 0

            def poll(self):
                self.n += 1
                return None if self.n == 1 else 0
        w = guard.MatchWatch(Game(), self.home, self.game, self.copy, username="Nick#4821", consent=consent,
                             manifests=[], say=lambda s: None, sleep=lambda s: None, local=str(self.dir / "none"))
        w.run()
        return w.findings, bool(looked)

    def test_the_program_check_runs_whenever_terms_are_accepted(self):
        # mandatory, part of RUSE Guard: it runs with terms accepted even though the consent says scan False
        findings, looked = self._watch_scan({"terms": guard.TERMS_VERSION, "scan": False, "server": ""})
        self.assertEqual((findings, looked), ([{"name": "x.exe", "what": "tool"}], True))

    def test_no_program_check_before_the_terms_are_accepted(self):
        # not accepted (the agreement gates play): no scan, even with a stored scan True
        findings, looked = self._watch_scan({"terms": 0, "scan": True, "server": ""})
        self.assertEqual((findings, looked), ([], False))


def setattr_many(mod, values):
    mod.cheat_tools, mod.live_multiplayer, mod.scan = values


LIVE = b"gc: collectable <RUSEGUARD-MATCH live multi 1 coop 0 instance at 00000000029A3B20>\r\n"   # as the game says them
COOP = b"gc: collectable <RUSEGUARD-MATCH live multi 0 coop 1 instance at 00000000029A3B20>\r\n"
END = b"gc: collectable <RUSEGUARD-MATCH end instance at 00000000029A3C40>\r\n"
STEAM = b"Caching Steam ID:  76561198012345678 [API loaded no]\n"   # a line Steam's own library writes there


class ProgramCheck(unittest.TestCase):
    """The program check, repaired (the owner, 2026-11-25: "Repair it for 31", and for its list, question 14:
    "Fourteen's fine, go with your pick."): its list comes inside the app and nothing is downloaded for it; it looks
    only while the game's own lines say a multiplayer or co-op match is on; what it found goes out after the game,
    that and nothing more."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.home, self.game, self.copy = self.dir / "home", self.dir / "Steam/steamapps/common/RUSE", self.dir / "copy"
        for p in (self.home, self.game, self.copy):
            p.mkdir(parents=True)

    def test_nothing_is_downloaded_for_the_list(self):
        """Until Launcher 0.4.8.22 the watch of every game it started fetched the list from the server set."""
        asked = []

        def no_network(*args, **kwargs):
            asked.append(args)
            raise OSError("no network in this test")

        class Closed:
            def poll(self):
                return 0
        with mock.patch.object(guard.net, "urlopen", no_network):
            # the watch of a game the Launcher started, with the project's server set: the list isn't fetched
            guard.MatchWatch(Closed(), self.home, self.game, self.copy, username="Nick#4821",
                             consent={"terms": guard.TERMS_VERSION, "server": "http://127.0.0.1:9"}, manifests=[],
                             say=lambda s: None, sleep=lambda s: None, local=str(self.dir / "none")).run()
        self.assertEqual(asked, [])
        self.assertFalse((self.home / guard.SIGNATURES).exists())

    def test_the_list_comes_inside_the_app(self):
        tools = guard.cheat_tools()
        self.assertEqual(guard.CHEAT_TOOLS.parent, Path(guard.__file__).parent)  # a plain file inside the app
        names = [t["name"] for t in tools]
        self.assertEqual(len(tools), 10)                                         # today's list, 2026-11-25
        self.assertEqual(len(set(names)), 10)
        for t in tools:
            self.assertTrue(t["name"] == t["name"].lower() and t["name"].endswith(".exe") and t["what"], t)
        self.assertIn({"name": "squalr.exe", "what": "Squalr, a memory editor"}, tools)

    def test_a_list_that_cant_be_read_is_said_not_skipped(self):
        broken = self.dir / "list.toml"
        for text in ("[[tool]\nname = ", "# nothing listed\n"):
            broken.write_text(text, encoding="utf-8")
            with self.assertRaises(guard.GuardError):
                guard.cheat_tools(broken)
        said = []

        class Closed:
            def poll(self):
                return 0
        with mock.patch.object(guard, "CHEAT_TOOLS", self.dir / "missing.toml"):
            guard.MatchWatch(Closed(), self.home, self.game, self.copy, username="Nick#4821",
                             consent={"terms": guard.TERMS_VERSION, "server": ""}, manifests=[], say=said.append,
                             sleep=lambda s: None, local=str(self.dir / "none")).run()
        self.assertTrue(any("list of known cheat tools" in s for s in said), said)

    def test_only_the_match_lines_are_kept(self):
        clock = [1000.0]
        lines = guard.GameLines(io.BytesIO(b""), clock=lambda: clock[0], wall=lambda: 1791000000 + clock[0])
        for raw in (STEAM, b"gc: collectable <TSomeGameClass instance at 0000000012345678>\n",
                    b"RUSEGUARD-MATCH live multi 0 coop 0\n", b"RUSEGUARD-MATCH started\n", b"\n"):
            lines.take(raw)
        self.assertEqual(lines.matches, [])          # nothing kept from any other line, the Steam one least of all
        self.assertIsNone(lines.live())
        lines.take(LIVE)
        on = lines.live()
        self.assertEqual((on["multi"], on["coop"], on["ended"], on["started"], on["findings"]),
                         (True, False, None, 1791001000, []))
        clock[0] += guard.LIVE_FOR - 1
        self.assertIs(lines.live(), on)              # the next line is due every 30 seconds of game time
        clock[0] += 2
        self.assertIsNone(lines.live())              # none for LIVE_FOR seconds: not on any more
        lines.take(LIVE)
        self.assertIsNot(lines.live(), on)           # a new one (a new match, or after a long pause)
        lines.take(STEAM)
        lines.take(END)
        self.assertIsNone(lines.live())
        lines.take(END)                              # a second end changes nothing
        lines.take(COOP)
        self.assertEqual((lines.live()["multi"], lines.live()["coop"]), (False, True))
        self.assertEqual([(m["multi"], m["coop"], m["ended"] is not None) for m in lines.matches],
                         [(True, False, False), (True, False, True), (False, True, False)])
        self.assertNotIn("76561198012345678", json.dumps(lines.matches))

    def _watch(self, script, consent=None, programs=("explorer.exe", "steam.exe", "Squalr.exe", "notepad.exe")):
        """A MatchWatch beside a stand-in game: at its i-th poll the game says script[i] (a line, or None), then it
        closes. Returns (how many times the programs were listed, what the watch said)."""
        scans, said = [], []
        lines = guard.GameLines(io.BytesIO(b""))

        class Game:
            guard_lines = lines

            def __init__(self):
                self.n = 0

            def poll(self):
                if self.n < len(script):
                    if script[self.n]:
                        lines.take(script[self.n])
                    self.n += 1
                    return None
                return 0

        def listed():  # as running_programs gives them: Windows' task list, in lowercase
            scans.append(1)
            return sorted({p.lower() for p in programs})
        with mock.patch.object(guard, "running_programs", listed):
            guard.MatchWatch(Game(), self.home, self.game, self.copy, username="Nick#4821",
                             consent=consent or {"terms": guard.TERMS_VERSION, "server": ""}, manifests=[],
                             say=said.append, sleep=lambda s: None, local=str(self.dir / "none")).run()
        return len(scans), said

    def kept(self) -> list:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.home / guard.OUTBOX).glob("*.json"))]

    def test_the_watch_scans_while_the_games_lines_say_a_match_is_on(self):
        """The failure the owner's 31 repairs (findings F-147): the watch waited for a match record file the game
        can't write, so the check never ran in a match, even with its list at hand. The old list the release
        downloaded is in its place here, so only the match's start is missing from it; the watch now follows the
        game's own lines (a stand-in for the Launcher's reader, GameLines, fed by hand)."""
        (self.home / "guard").mkdir()
        (self.home / guard.SIGNATURES).write_text(json.dumps([{"name": "squalr.exe", "what": "a memory editor"}]),
                                                  encoding="utf-8")
        match = {"started": 1791000000, "multi": True, "coop": False, "ended": None, "findings": []}
        scans = []

        class Lines:
            matches, on = [match], None

            def live(self):
                return self.on

        class Game:
            guard_lines = Lines()

            def __init__(self):
                self.states = [None, match, match, None]   # the menu, the match twice, the menu again

            def poll(self):
                if self.states:
                    self.guard_lines.on = self.states.pop(0)
                    return None
                return 0

        def listed():
            scans.append(1)
            return ["explorer.exe", "squalr.exe"]
        with mock.patch.object(guard, "running_programs", listed):
            guard.MatchWatch(Game(), self.home, self.game, self.copy, username="Nick#4821",
                             consent={"terms": guard.TERMS_VERSION, "server": ""}, manifests=[], say=lambda s: None,
                             sleep=lambda s: None, local=str(self.dir / "none")).run()
        self.assertEqual(len(scans), 2)
        self.assertEqual([f["name"] for f in match["findings"]], ["squalr.exe"])

    def test_it_looks_only_while_a_match_is_on_and_reports_only_what_it_found(self):
        #            the menu, the match starts, still on, it ends, the menu again
        scans, said = self._watch([None, LIVE, STEAM, END, None])
        self.assertEqual(scans, 2)                   # in the match only
        bodies = self.kept()
        self.assertEqual(len(bodies), 1)
        body = bodies[0]
        self.assertTrue(guard.check_bundle(body))
        self.assertEqual(body["evidence"]["process_findings"], [{"name": "squalr.exe", "what": "Squalr, a memory editor"}])
        self.assertEqual((body["match"]["mode"], body["match"]["is_multiplayer"], body["evidence"]["player"],
                          body["match"]["players"], body["evidence"]["ended_in_game"]),
                         ("multiplayer", True, "Nick#4821", ["Nick#4821"], True))
        # that and nothing more: no replay, no record of the game, no files, no other program's name, no Steam ID
        self.assertEqual((body["replay"], body["evidence"]["state_series"], body["evidence"]["files"],
                          body["evidence"]["hotkeys"], body["evidence"]["mods"], body["evidence"]["stop"]),
                         ("", [], {}, [], [], {}))
        whole = json.dumps(body)
        for other in ("explorer.exe", "steam.exe", "notepad.exe", "76561198012345678"):
            self.assertNotIn(other, whole)
        self.assertTrue(any("the program check of match" in s for s in said), said)

    def test_a_co_op_match_is_one_too(self):
        scans, _said = self._watch([COOP, None])
        self.assertEqual(scans, 2)
        self.assertEqual([(b["match"]["mode"], b["evidence"]["ended_in_game"]) for b in self.kept()], [("coop", False)])

    def test_outside_a_match_it_never_looks(self):
        # the menu, a skirmish against the computer or the campaign, a replay: the record says nothing for them
        scans, said = self._watch([None, STEAM, b"gc: collectable <TCamp instance at 0>\n", None])
        self.assertEqual((scans, self.kept()), (0, []))
        # a match with nothing listed running: it looked, and sends nothing
        scans, said = self._watch([LIVE, None, END], programs=("explorer.exe", "steam.exe"))
        self.assertEqual((scans, self.kept()), (2, []))

    def test_nothing_before_the_terms_are_accepted(self):
        scans, said = self._watch([LIVE, None, END], consent={"terms": 0, "server": ""})
        self.assertEqual((scans, self.kept(), said), (0, [], []))

    def test_the_launcher_starts_the_game_with_its_error_output_read(self):
        """The Launcher starts the game with its error output on a pipe that is read (start_game_watched); the
        Studio's Test in game as before, without it. Until Launcher 0.4.8.22 the game's output wasn't read at all.
        Checked our_tools.json: no tool there covers this; the game's program file named here is a made-up path
        handed to a stand-in for starting a program, never read."""
        import inspect
        from rusemod import play
        from ruse_launcher.api import LauncherApi
        launcher_start = inspect.signature(LauncherApi.__init__).parameters["start_game"].default
        self.assertIs(play.Starter().start_game, play.start_game)

        made = []

        class Popen:
            def __init__(self, args, **kwargs):
                made.append((args, kwargs))
                self.stderr = io.BytesIO(STEAM + LIVE + END)
        with mock.patch.object(play.subprocess, "Popen", Popen):
            process = launcher_start(self.dir / "RUSE.exe")
        self.assertEqual(made, [([str(self.dir / "RUSE.exe")], {"cwd": str(self.dir), "stderr": play.subprocess.PIPE})])
        process.guard_lines.join(10)
        self.assertEqual([(m["multi"], m["ended"] is not None) for m in process.guard_lines.matches], [(True, True)])
        self.assertTrue(process.stderr.closed)       # read to its end, then closed

    @unittest.skipUnless(sys.platform == "win32", "a Windows command file stands in for the game")
    def test_a_real_programs_error_output_is_read_while_it_runs(self):
        exe = self.dir / "copy" / "RUSE.cmd"
        exe.write_text("@echo off\r\n"
                       "echo Caching Steam ID: 76561198012345678 1>&2\r\n"
                       "echo gc: collectable RUSEGUARD-MATCH live multi 1 coop 0 instance at 0 1>&2\r\n"
                       "ping -n 2 127.0.0.1 >nul\r\n"
                       "echo gc: collectable RUSEGUARD-MATCH end instance at 0 1>&2\r\n", encoding="ascii")
        from rusemod import play
        process = play.start_game_watched(exe)
        self.assertEqual(process.wait(60), 0)
        process.guard_lines.join(10)
        self.assertFalse(process.guard_lines.is_alive())
        self.assertEqual([(m["multi"], m["coop"], m["ended"] is not None) for m in process.guard_lines.matches],
                         [(True, False, True)])
        self.assertNotIn("76561198012345678", json.dumps(process.guard_lines.matches))
        self.assertTrue(process.stderr.closed)


class Server(unittest.TestCase):
    """The project's server is the default only from the app window (use_guard_server): a test's bundles stay in the
    outbox and never leave the PC."""

    def test_the_window_sets_the_projects_server_and_tests_keep_theirs(self):
        import tempfile
        from pathlib import Path
        from ruse_launcher.api import LauncherApi
        with tempfile.TemporaryDirectory() as tmp:
            api = LauncherApi(home=Path(tmp))
            self.assertEqual(api.guard_status()["server"], "")            # a test: nothing leaves the PC
            api.use_guard_server()
            self.assertEqual(api.guard_status()["server"], guard.SERVER)  # the app window: the project's server
        root = Path(__file__).resolve().parents[1]
        for app in ("ruse_launcher", "ruse_studio"):
            self.assertIn("api.use_guard_server()", (root / "src" / app / "app.py").read_text(encoding="utf-8"), app)


if __name__ == "__main__":
    unittest.main()
