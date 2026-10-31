"""RUSE Guard, the Launcher's side (rusemod.guard): signed tokens in DomesticNukes' format, dev keys, signed mod
manifests, the in-game record, the process scan, and a match's evidence bundle kept or sent."""
import json
import shutil
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

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
        p = self.dir / "crashdump.dmp"
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
        # a real lock-crash dump holds both; the filled-in line is the evidence, the template is a useless constant
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
        (local / "Temp" / "CrashRpt_abc" / "crashdump.dmp").write_bytes(self.DUMP)
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
                    (dumps / "crashdump.dmp").write_bytes(Bundle.DUMP)
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
        (local / "Temp" / "CrashRpt_abc" / "crashdump.dmp").write_bytes(self.DUMP)
        guard.collect_stops(self.home, since=0, username="", server="", now=1791000200, local=str(local),
                            say=lambda s: None)
        body = json.loads(next((self.home / guard.OUTBOX).glob("*.json")).read_text(encoding="utf-8"))
        self.assertTrue(guard.check_bundle(body))
        self.assertEqual(body["evidence"]["player"], "player-" + body["client_key"][:12])
        self.assertIn("a cheat copy was stopped", body["evidence"]["stop"]["text"])

    def _watch_scan(self, consent):
        # run a MatchWatch with the program check's module functions stubbed, and return (findings, whether it looked)
        looked = []
        orig = (guard.signatures, guard.live_multiplayer, guard.scan)
        self.addCleanup(lambda: setattr_many(guard, orig))
        guard.signatures = lambda home, server="", *a, **k: (looked.append(1), [{"name": "x.exe", "what": "tool"}])[1]
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
    mod.signatures, mod.live_multiplayer, mod.scan = values


if __name__ == "__main__":
    unittest.main()
