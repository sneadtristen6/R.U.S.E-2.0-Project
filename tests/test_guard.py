"""RUSE Guard, the Launcher's side (rusemod.guard): signed tokens in DomesticNukes' format, dev keys, signed mod
manifests, the in-game record, the process scan, its list inside the app and the game's lines that say a match is on,
and a match's evidence bundle kept or sent.

These tests read no program: where they name the game's program file, it is a made-up path handed to a stand-in for
starting a program."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import io
import json
import os
import re
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


def game_report(data: bytes, program: str | None = None) -> bytes:
    """A small crash report file of the game (or of another `program`, by its path) with `data` in its memory, laid
    out as tests/test_bugwatch.py's Crashes.dump makes one: only the game's own crash reports are read
    (rusemod.bugwatch.game_report)."""
    import test_bugwatch
    return test_bugwatch.Crashes.dump(None, extra=b"\0" + data, program=program)


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
                             manifests=[], say=lambda s: None, sleep=lambda s: None)
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


STAMP = 1791000000   # the game's clock time in the lines below; the tests' Launcher clock says the same
LIVE = b"gc: collectable <RUSEGUARD-MATCH live multi 1 coop 0 at 1791000000 instance at 00000000029A3B20>\r\n"   # as the game says them
COOP = b"gc: collectable <RUSEGUARD-MATCH live multi 0 coop 1 at 1791000000 instance at 00000000029A3B20>\r\n"
END = b"gc: collectable <RUSEGUARD-MATCH end at 1791000000 instance at 00000000029A3C40>\r\n"


def said_at(words: str, stamp: int) -> bytes:
    return f"gc: collectable <RUSEGUARD-MATCH {words} at {stamp} instance at 00000000029A3B20>\r\n".encode()
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
        # these stand-in games count one poll as one scan time (the check slept SCAN_EVERY between polls); the
        # watch now polls every POLL_EVERY and scans every SCAN_EVERY // POLL_EVERY polls: that timing is pinned
        # by Stop.test_the_watch_looks_every_second_and_checks_programs_every_thirty
        patch = mock.patch.object(guard, "SCAN_EVERY", guard.POLL_EVERY)
        patch.start()
        self.addCleanup(patch.stop)

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
                             say=lambda s: None, sleep=lambda s: None).run()
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
                             sleep=lambda s: None).run()
        self.assertTrue(any("list of known cheat tools" in s for s in said), said)

    def test_only_the_match_lines_are_kept(self):
        clock = [1000.0]
        lines = guard.GameLines(io.BytesIO(b""), clock=lambda: clock[0], wall=lambda: STAMP + clock[0] - 1000)
        for raw in (STEAM, b"gc: collectable <TSomeGameClass instance at 0000000012345678>\n",
                    b"RUSEGUARD-MATCH live multi 0 coop 0 at 1791000000\n", b"RUSEGUARD-MATCH started\n", b"\n",
                    b"RUSEGUARD-MATCH live multi 1 coop 0\n"):   # no game time in it: not one of ours
            lines.take(raw)
        self.assertEqual(lines.matches, [])          # nothing kept from any other line, the Steam one least of all
        self.assertIsNone(lines.live())
        lines.take(LIVE)
        on = lines.live()
        self.assertEqual((on["multi"], on["coop"], on["ended"], on["started"], on["findings"]),
                         (True, False, None, STAMP, []))
        clock[0] += guard.LIVE_FOR - 1
        self.assertIs(lines.live(), on)              # the next line is due every 30 seconds of game time
        clock[0] += 2
        self.assertIsNone(lines.live())              # none for LIVE_FOR seconds: not on any more
        now = STAMP + int(clock[0]) - 1000
        lines.take(said_at("live multi 1 coop 0", now))
        self.assertIsNot(lines.live(), on)           # a new one (a new match, or after a long pause)
        lines.take(STEAM)
        lines.take(END)
        self.assertIsNone(lines.live())
        lines.take(END)                              # a second end changes nothing
        lines.take(said_at("live multi 0 coop 1", now))
        self.assertEqual((lines.live()["multi"], lines.live()["coop"]), (False, True))
        self.assertEqual([(m["multi"], m["coop"], m["ended"] is not None) for m in lines.matches],
                         [(True, False, False), (True, False, True), (False, True, False)])
        self.assertNotIn("76561198012345678", json.dumps(lines.matches))

    def test_lines_handed_over_late_say_nothing_about_now(self):
        """A C runtime may hold the game's error lines back and hand them over all at once (judgment: an old one
        did): a match's "live" lines of two minutes ago, read now, must not make the match count as on."""
        clock = [5000.0]
        lines = guard.GameLines(io.BytesIO(b""), clock=lambda: clock[0], wall=lambda: STAMP + 100)
        burst = b"".join(said_at("live multi 1 coop 0", STAMP + t) for t in (-20, 10, 40, 70)) + \
            said_at("end", STAMP + 80) + said_at("live multi 1 coop 0", STAMP + 85)   # the last: after the end, 15 s old
        for raw in burst.splitlines(True):
            lines.take(raw)
        self.assertIsNone(lines.live())
        clock[0] += 1000
        self.assertIsNone(lines.live())              # and later still no match from them
        lines.take(said_at("live multi 1 coop 0", STAMP + 100))   # a line of this moment does count
        self.assertEqual(lines.live()["started"], STAMP + 100)
        lines.take(said_at("live multi 1 coop 0", STAMP + 400))   # a stamp from the future: not trusted
        self.assertEqual(len(lines.matches), 1)

    def test_the_scan_stops_two_minutes_after_the_last_live_line(self):
        """The owner's 6 (2026-11-25): "keep 2 minutes". The number is written out here, not read from LIVE_FOR (a
        test that reads it passes with any value): a scan up to 120 seconds after the last "live" line finds the
        match, one more than 120 seconds after it finds none."""
        self.assertEqual(guard.LIVE_FOR, 120)
        (self.home / "guard").mkdir()
        (self.home / guard.SIGNATURES).write_text(json.dumps([{"name": "squalr.exe", "what": "a memory editor"}]),
                                                  encoding="utf-8")
        clock, scans = [1000.0], []
        lines = guard.GameLines(io.BytesIO(b""), clock=lambda: clock[0], wall=lambda: STAMP)

        class Game:
            guard_lines = lines
            steps = [("live", 0), ("wait", 119), ("wait", 1), ("wait", 1)]   # seconds since the last line: 0, 119, 120, 121

            def poll(self):
                if not self.steps:
                    return 0
                what, seconds = self.steps.pop(0)
                if what == "live":
                    lines.take(LIVE)
                clock[0] += seconds
                return None

        def listed():
            scans.append(clock[0] - 1000.0)
            return ["explorer.exe", "squalr.exe"]
        with mock.patch.object(guard, "running_programs", listed):
            guard.MatchWatch(Game(), self.home, self.game, self.copy, username="Nick#4821",
                             consent={"terms": guard.TERMS_VERSION, "server": ""}, manifests=[], say=lambda s: None,
                             sleep=lambda s: None).run()
        self.assertEqual(scans, [0.0, 119.0, 120.0])   # at 121 seconds the match is over: no scan

    def _watch(self, script, consent=None, programs=("explorer.exe", "steam.exe", "Squalr.exe", "notepad.exe")):
        """A MatchWatch beside a stand-in game: at its i-th poll the game says script[i] (a line, or None), then it
        closes. Returns (how many times the programs were listed, what the watch said)."""
        scans, said = [], []
        lines = guard.GameLines(io.BytesIO(b""), wall=lambda: STAMP)

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
                             say=said.append, sleep=lambda s: None).run()
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
                             sleep=lambda s: None).run()
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
        The game's program file named here is a made-up path handed to a stand-in for starting a program, never read."""
        import inspect
        from rusemod import play
        from ruse_launcher.api import LauncherApi
        launcher_start = inspect.signature(LauncherApi.__init__).parameters["start_game"].default
        self.assertIs(play.Starter().start_game, play.start_game)

        made = []

        class Popen:
            def __init__(self, args, **kwargs):
                made.append((args, kwargs))
                now = int(time.time())
                self.stderr = io.BytesIO(STEAM + said_at("live multi 1 coop 0", now) + said_at("end", now))
        with mock.patch.object(play.subprocess, "Popen", Popen):
            process = launcher_start(self.dir / "RUSE.exe")  # (a made-up path, never read)
        self.assertEqual(made, [([str(self.dir / "RUSE.exe")], {"cwd": str(self.dir), "stdin": play.subprocess.DEVNULL,
                                                                 "stdout": play.subprocess.DEVNULL,
                                                                 "stderr": play.subprocess.PIPE})])
        process.guard_lines.join(10)
        self.assertEqual([(m["multi"], m["ended"] is not None) for m in process.guard_lines.matches], [(True, True)])
        self.assertTrue(process.stderr.closed)       # read to its end, then closed

    @unittest.skipUnless(sys.platform == "win32", "a Windows command file stands in for the game")
    def test_a_real_programs_error_output_is_read_while_it_runs(self):
        exe = self.dir / "copy" / "RUSE.cmd"
        now = int(time.time())
        exe.write_text("@echo off\r\n"
                       "echo Caching Steam ID: 76561198012345678 1>&2\r\n"
                       f"echo gc: collectable RUSEGUARD-MATCH live multi 1 coop 0 at {now} instance at 0 1>&2\r\n"
                       "ping -n 2 127.0.0.1 >nul\r\n"
                       f"echo gc: collectable RUSEGUARD-MATCH end at {now} instance at 0 1>&2\r\n", encoding="ascii")
        from rusemod import play
        process = play.start_game_watched(exe)
        self.assertEqual(process.wait(60), 0)
        process.guard_lines.join(10)
        self.assertFalse(process.guard_lines.is_alive())
        self.assertEqual([(m["multi"], m["coop"], m["ended"] is not None) for m in process.guard_lines.matches],
                         [(True, False, True)])
        self.assertNotIn("76561198012345678", json.dumps(process.guard_lines.matches))
        self.assertTrue(process.stderr.closed)


class Game:
    """The game's process as the match watch sees it: running for `polls` looks, then closed with `code`."""

    def __init__(self, code, polls=1, during=None):
        self.code, self.polls, self.during, self.seen = code, polls, during, 0

    def poll(self):
        self.seen += 1
        if self.seen <= self.polls:
            if self.during:
                self.during(self.seen)
            return None
        return self.code


class Stop(unittest.TestCase):
    """A cheat copy's stop goes only to our server (the owner, 2026-11-24: "Fine, change it to only go to our
    server."): the copy's lock closes the game with RUSE Guard's close number, and the Launcher's match watch, which
    started the game, files a small signed note when it sees that number; no crash report is read at all."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.home, self.game, self.copy = self.dir / "home", self.dir / "Steam/steamapps/common/RUSE", self.dir / "copy"
        for p in (self.home, self.game, self.copy):
            p.mkdir(parents=True)
        self.said = []

    def cheat_record(self, lock=None, folder=None):
        from rusemod import fairplay
        cheat = fairplay.FairPlay([fairplay.ModCheck("dev", "Dev", cheat=True)])
        lock = lock or fairplay.build_code("24687178", b"\1" * 32, [("dev", "1.0.0")])
        return fairplay.write_record(folder or self.copy, "24687178", b"\1" * 32, [("dev", "1.0.0")], cheat, [], lock)

    def watch(self, process, terms=None, **kw):
        w = guard.MatchWatch(process, self.home, self.game, self.copy, username=kw.pop("username", "Nick#4821"),
                             consent={"terms": guard.TERMS_VERSION if terms is None else terms, "server": ""},
                             manifests=[], say=self.said.append, sleep=kw.pop("sleep", lambda s: None), **kw)
        w.run()
        return w

    def kept(self) -> list:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.home / guard.OUTBOX).glob("*.json"))]

    def test_the_close_number_files_one_note_once_the_terms_are_accepted(self):
        from rusemod import fairplay
        self.cheat_record()
        w = self.watch(Game(fairplay.LOCK_EXIT))
        notes = self.kept()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["evidence"]["stop"], {"text": guard.STOP_TEXT, "code": "0x52474c4b"})
        self.assertTrue(any(line.startswith("RUSE Guard: a cheat copy was stopped (") for line in self.said), self.said)
        self.assertEqual((w.code, w.take_stop(), w.take_stop()), (fairplay.LOCK_EXIT, True, False))  # said once
        # before the terms are accepted: nothing filed, nothing said to the player
        shutil.rmtree(self.home / "guard")
        w = self.watch(Game(fairplay.LOCK_EXIT), terms=0)
        self.assertEqual((self.kept(), w.take_stop()), ([], False))

    def test_no_crash_report_is_read(self):
        """The stop never goes through the game's crash reporter: a crash report on this PC that carries the 0.9.8.22
        lock's marked line (a cheat copy stopped by a crash) is not read, and nothing is filed for it (until 0.9.8.22
        the Launcher read that line out of the report and sent it)."""
        local = self.dir / "LocalAppData"
        (local / "Temp" / "CrashRpt_abc").mkdir(parents=True)
        (local / "Temp" / "CrashRpt_abc" / "report.dmp").write_bytes(
            b"junk RUSEGUARD-LOCK a cheat copy was stopped: it surrendered and left the match. multi 1 coop 0 local 0 "
            b"RUSEGUARD-END junk")
        soon = time.time() + 60
        os.utime(local / "Temp" / "CrashRpt_abc" / "report.dmp", (soon, soon))
        self.cheat_record()
        with mock.patch.dict("os.environ", {"LOCALAPPDATA": str(local)}):
            self.watch(Game(0x29A))
        self.assertEqual(self.kept(), [])
        # read_stop stays at the join: it only reads a crash file on this PC, nothing is sent, and the crash list's
        # CodeWatch (rusemod.bugwatch) uses it to pass over an old cheat copy's stop crash; what sent it is gone
        self.assertEqual([name for name in ("collect_stops", "stop_dumps_since", "GUARD_DUMPS")
                          if hasattr(guard, name)], [])

    def test_every_other_exit_code_files_nothing(self):
        # the game's own endings (0, 1, 5, 9, -1 as 0xFFFFFFFF, the stack check's 0xC0000409), a script error's
        # stop (0x29a, the 0.9.8.22 lock's), a Windows crash (0xC0000005): no note
        self.cheat_record()
        for code in (0, 1, 5, 9, 0x29A, 0xFFFFFFFF, 0xC0000005, 0xC0000409, -1):
            w = self.watch(Game(code))
            self.assertEqual((self.kept(), w.take_stop()), ([], False), code)
        self.assertEqual([line for line in self.said if "stopped" in line], [])

    def test_only_a_copy_whose_lock_closes_the_game_gets_a_note(self):
        """The number alone isn't enough: no record, an honest copy's, or a 0.9.8.22 cheat copy's (a lock that crashes,
        no stop) files nothing and says one line; a lock with no build code (thirteen zeros) is a lock."""
        from rusemod import fairplay
        honest = fairplay.write_record(self.copy, "24687178", b"\1" * 32, [("maps", "1.0.0")], fairplay.FairPlay(), [])
        old = dict(self.cheat_record(), stop=None)
        for record in (None, honest, old):
            (self.copy / fairplay.RECORD).unlink(missing_ok=True)
            if record is not None:
                (self.copy / fairplay.RECORD).write_text(json.dumps(record), encoding="utf-8")
            self.said.clear()
            w = self.watch(Game(fairplay.LOCK_EXIT))
            self.assertEqual((self.kept(), w.take_stop()), ([], False), record)
            self.assertEqual(self.said, ["RUSE Guard: the game closed with RUSE Guard's close number, but this copy has "
                                         "no lock that closes it; nothing was sent"])
        self.cheat_record(fairplay.NO_BUILD_CODE)
        self.watch(Game(fairplay.LOCK_EXIT))
        self.assertEqual(len(self.kept()), 1)

    def test_the_record_is_read_when_the_game_starts(self):
        # the copy is built again (or taken away) while the game runs or right after: the note still goes out
        from rusemod import fairplay
        self.cheat_record()

        def gone(_n):
            (self.copy / fairplay.RECORD).unlink()
        self.watch(Game(fairplay.LOCK_EXIT, during=gone))
        self.assertEqual(len(self.kept()), 1)

    def test_a_trouble_with_the_match_records_never_costs_the_note(self):
        from rusemod import fairplay
        self.cheat_record()
        with mock.patch.object(guard, "collect", side_effect=OSError("the copy's folder went away")):
            self.watch(Game(fairplay.LOCK_EXIT))
        self.assertEqual(len(self.kept()), 1)
        self.assertIn("RUSE Guard: the match records couldn't be read or sent: OSError: the copy's folder went away",
                      self.said)
        # and a note that can't be made is said, never silent
        shutil.rmtree(self.home / "guard")
        self.said.clear()
        with mock.patch.object(guard, "bundle", side_effect=ValueError("no key")):
            w = self.watch(Game(fairplay.LOCK_EXIT))
        self.assertEqual((self.kept(), w.take_stop()), ([], False))
        self.assertEqual(self.said, ["RUSE Guard: the note that a cheat copy was stopped couldn't be made: "
                                     "ValueError: no key"])

    def test_the_note_holds_only_the_handle_the_two_times_and_the_stop(self):
        from rusemod import fairplay
        self.cheat_record()
        before = int(time.time())
        line = guard.file_stop(self.home, fairplay.read_record(self.copy), before - 60, username="Nick#4821",
                               say=self.said.append)
        note = self.kept()[0]
        self.assertTrue(guard.check_bundle(note))
        self.assertIn(note["bundle_id"], line)
        self.assertIsInstance(note["match"]["ended"], int)   # the review server's intake needs a whole number
        self.assertTrue(before <= note["match"]["ended"] <= int(time.time()) + 1)
        self.assertEqual(note["match"]["started"], before - 60)
        self.assertEqual({k: v for k, v in note["match"].items() if v not in ("", [], {}, False, None)},
                         {"is_multiplayer": True, "players": ["Nick#4821"], "mode": "multiplayer",
                          "started": before - 60, "ended": note["match"]["ended"]})
        self.assertEqual({k: v for k, v in note["evidence"].items() if v not in ("", [], {}, False, None)},
                         {"player": "Nick#4821", "username": "Nick#4821",
                          "stop": {"text": guard.STOP_TEXT, "code": "0x52474c4b"}})
        self.assertEqual(note["replay"], "")
        whole = json.dumps(note)
        self.assertIsNone(re.search(r"7656\d{13}", whole))   # no Steam ID shape anywhere
        record = fairplay.read_record(self.copy)
        for value in (record["lock"], record["code"], record["fingerprint"]):  # no build or join code, no fingerprint
            self.assertNotIn(value, whole)
        # without a username: this install's anonymous id, as every bundle
        shutil.rmtree(self.home / "guard" / "outbox")
        guard.file_stop(self.home, fairplay.read_record(self.copy), before, username="", say=self.said.append)
        anon = self.kept()[0]
        self.assertEqual(anon["evidence"]["player"], "player-" + anon["client_key"][:12])

    def test_the_watch_looks_every_second_and_checks_programs_every_thirty(self):
        from rusemod import fairplay
        self.cheat_record()
        slept, scans = [], []
        with mock.patch.object(guard, "cheat_tools", lambda *a, **k: [{"name": "x.exe"}]), \
                mock.patch.object(guard, "live_multiplayer", lambda copy: True), \
                mock.patch.object(guard, "scan", lambda sigs, programs=None: scans.append(len(slept)) or []):
            self.watch(Game(fairplay.LOCK_EXIT, polls=95), sleep=slept.append)
        self.assertEqual((guard.POLL_EVERY, set(slept), len(slept)), (1, {1}, 95))   # the close seen within a second
        self.assertEqual(scans, [0, 30, 60, 90])                                   # the program check as before
        self.assertEqual(len(self.kept()), 1)

    def test_a_failing_program_check_never_ends_the_watch(self):
        from rusemod import fairplay
        self.cheat_record()
        with mock.patch.object(guard, "cheat_tools", lambda *a, **k: [{"name": "x.exe"}]), \
                mock.patch.object(guard, "live_multiplayer", mock.Mock(side_effect=OSError("tasklist is missing"))):
            self.watch(Game(fairplay.LOCK_EXIT, polls=3))
        self.assertEqual(len(self.kept()), 1)
        self.assertIn("RUSE Guard: the program check couldn't look this time: OSError: tasklist is missing", self.said)

    @unittest.skipUnless(sys.platform == "win32", "a Windows program's exit code")
    def test_a_real_program_s_exit_code_reaches_the_watch(self):
        """A real program the watch follows, started as play.start_game starts the game (Popen), ends with RUSE
        Guard's close number through Windows' own ExitProcess: Popen reads the whole 32-bit number, and the watch
        files the note."""
        import subprocess
        from rusemod import fairplay
        self.cheat_record()
        child = subprocess.Popen([sys.executable, "-c", "import ctypes; ctypes.windll.kernel32.ExitProcess(0x52474C4B)"])
        w = self.watch(child, sleep=time.sleep)
        self.assertEqual((child.returncode, w.code), (fairplay.LOCK_EXIT, fairplay.LOCK_EXIT))
        self.assertEqual(len(self.kept()), 1)
        ended = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"])
        self.assertEqual(self.watch(ended, sleep=time.sleep).code, 0)
        self.assertEqual(len(self.kept()), 1)   # an ordinary end: nothing more


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
