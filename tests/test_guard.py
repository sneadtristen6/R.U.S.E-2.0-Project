"""RUSE Guard, the Launcher's side (rusemod.guard): signed tokens in DomesticNukes' format, dev keys, signed mod
manifests, the in-game record, the process scan, and a match's evidence bundle kept or sent."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
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
    mod.signatures, mod.live_multiplayer, mod.scan = values


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
        self.assertEqual([name for name in ("read_stop", "collect_stops", "stop_dumps_since", "GUARD_DUMPS")
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
        with mock.patch.object(guard, "signatures", lambda home, server="", *a, **k: [{"name": "x.exe"}]), \
                mock.patch.object(guard, "live_multiplayer", lambda copy: True), \
                mock.patch.object(guard, "scan", lambda sigs, programs=None: scans.append(len(slept)) or []):
            self.watch(Game(fairplay.LOCK_EXIT, polls=95), sleep=slept.append)
        self.assertEqual((guard.POLL_EVERY, set(slept), len(slept)), (1, {1}, 95))   # the close seen within a second
        self.assertEqual(scans, [0, 30, 60, 90])                                   # the program check as before
        self.assertEqual(len(self.kept()), 1)

    def test_a_failing_program_check_never_ends_the_watch(self):
        from rusemod import fairplay
        self.cheat_record()
        with mock.patch.object(guard, "signatures", lambda home, server="", *a, **k: [{"name": "x.exe"}]), \
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
