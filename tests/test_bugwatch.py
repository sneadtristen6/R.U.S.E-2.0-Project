"""Bug Watch (rusemod.bugwatch): opt-in counts, what's sent and when, crashes. No network: the sends go to a fake.

Checked our_tools.json: none of its tools reads a crash report; these tests read nothing of the game, only a small
crash report file they make themselves (one module named like the game).
"""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import struct
import sys
import tempfile
import time
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import bugwatch, home as homes, knowncrashes, net, webui  # noqa: E402
from test_knowncrashes import ListServer, MadeUp, keep_off_the_network  # noqa: E402


class Answer:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Server:
    """A fake of the Bug Watch server: answers each POST with `status` and keeps what was sent."""

    def __init__(self, status=200):
        self.status, self.sent = status, []

    def __call__(self, req, timeout=None):
        self.sent.append(("/".join(req.full_url.rsplit("/", 2)[-2:]), json.loads(req.data.decode("utf-8"))))
        if self.status >= 400:
            raise urllib.error.HTTPError(req.full_url, self.status, "no", {}, None)
        return Answer(self.status)


def is_clean(value) -> bool:
    """No string or key anywhere that the server would refuse as a path (worker.js PATH_PATTERNS)."""
    if isinstance(value, dict):
        return all(is_clean(k) and is_clean(v) for k, v in value.items())
    if isinstance(value, list):
        return all(is_clean(v) for v in value)
    return not (isinstance(value, str) and bugwatch.LOOKS_LIKE_PATH.search(value))


class BugWatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TEMP"))
        self.home = Path(self.tmp.name)
        self._on = bugwatch.ON
        bugwatch.ON = True
        os.environ.pop("RUSE_NO_BUGWATCH", None)
        # no test reaches the network (the list of known crashes goes through net.urlopen: a test that fetches it
        # gives its own fake), and the made-up list is signed with the published test key (test_knowncrashes)
        self.no_network = keep_off_the_network(self)

    def tearDown(self):
        bugwatch.ON = self._on
        bugwatch._current = None
        self.tmp.cleanup()

    def watch(self, server=None, clock=time.time):
        return bugwatch.Watch(self.home, "studio", "0.9.8.9", opener=server or Server(), clock=clock)


class Consent(BugWatchTest):
    def test_on_in_the_code_for_the_release(self):
        self.assertTrue(self._on)  # switched on for the release (the owner, 2026-10-31); the opt-in below still decides

    def test_nothing_is_counted_without_the_players_yes(self):
        w = self.watch()
        w.call("build_map", 0.5)
        self.assertEqual(w.days, {})
        self.assertFalse(bugwatch.enabled(self.home))

    def test_turn_on_makes_an_id_and_a_username(self):
        out = bugwatch.turn_on(self.home, "Nick")
        values = homes.settings(self.home)
        self.assertEqual(len(values["player"]["id"]), 32)
        self.assertRegex(values["player"]["name"], r"^Nick#\d{4}$")
        self.assertEqual(out["code"], values["player"]["id"][:8])
        self.assertTrue(bugwatch.enabled(self.home))
        again = bugwatch.turn_on(self.home, values["player"]["name"])  # the same ID, the name kept as it is
        self.assertEqual(again["code"], out["code"])
        self.assertEqual(homes.settings(self.home)["player"]["name"], values["player"]["name"])

    def test_set_username_shares_an_id_without_turning_bugwatch_on(self):
        # the agreement's guard-only case (program check on, Bug Watch off) still needs a username (plan §3a)
        out = bugwatch.set_username(self.home, "Nick")
        values = homes.settings(self.home)
        self.assertRegex(values["player"]["name"], r"^Nick#\d{4}$")
        self.assertEqual(len(values["player"]["id"]), 32)
        self.assertEqual(out["code"], values["player"]["id"][:8])
        self.assertFalse((values.get("bugwatch") or {}).get("on"))   # Bug Watch is left off
        self.assertFalse(bugwatch.enabled(self.home))
        on = bugwatch.turn_on(self.home, values["player"]["name"])   # ticking it later keeps the same ID and name
        self.assertEqual(on["code"], out["code"])
        self.assertEqual(homes.settings(self.home)["player"]["name"], values["player"]["name"])
        self.assertTrue(bugwatch.enabled(self.home))

    def test_set_username_works_even_when_bugwatch_is_off_in_code(self):
        bugwatch.ON = False   # the username is for RUSE Guard too, so it must work before Bug Watch is switched on
        out = bugwatch.set_username(self.home, "Ann")
        self.assertRegex(out["name"], r"^Ann#\d{4}$")
        self.assertEqual(len(homes.settings(self.home)["player"]["id"]), 32)

    def test_a_username_is_made_safe(self):
        self.assertEqual(bugwatch.username_of("  a/b\\c`d#e  ", 1234), "abcde#1234")
        self.assertEqual(bugwatch.username_of("", 42), "player#0042")
        self.assertLessEqual(len(bugwatch.username_of("x" * 99, 1000)), 40)

    def test_turn_off_forgets_everything(self):
        bugwatch.turn_on(self.home, "Nick")
        w = self.watch()
        w.call("x", 0.1)
        w.save()
        w.crash({"kind": "app", "error": "KeyError", "frames": []}, send=False)
        bugwatch.turn_off(self.home)
        self.assertFalse(bugwatch.enabled(self.home))
        self.assertNotIn("player", homes.settings(self.home))
        self.assertEqual(list((self.home / bugwatch.FOLDER).rglob("*.json")), [])

    def test_the_id_stays_for_ruse_guards_program_check(self):
        bugwatch.turn_on(self.home, "Nick")
        values = homes.settings(self.home)
        values["guard"] = {"terms": 1}   # RUSE Guard accepted: its mandatory program check keeps the shared username
        homes.save_settings(self.home, values)
        bugwatch.turn_off(self.home)
        self.assertIn("player", homes.settings(self.home))

    def test_the_environment_switch(self):
        bugwatch.turn_on(self.home, "Nick")
        with mock.patch.dict(os.environ, {"RUSE_NO_BUGWATCH": "1"}):
            self.assertFalse(bugwatch.enabled(self.home))


class Counting(BugWatchTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")

    def test_calls_jobs_and_the_rest(self):
        w = self.watch()
        w.call("build_map", 0.4)
        w.call("build_map", 12.0, OSError("disk"))
        w.call("open project", 0.1)  # a space isn't in a name: it becomes _
        w.job("play", True, 70)
        w.job("play", False, 2, error=ValueError("x"), build_errors=3)
        w.count("screens", "units")
        w.count("messages", "bad_name")
        w.count("checks", "game_folder_missing")
        w.count("updates", "installed")
        w.count("updates", "nonsense")  # not one of the three: ignored
        w.played(42.4, ["cool-mod@1.2", "x:\\bad@1"], 2)
        day = w.days[bugwatch._today()]
        self.assertEqual(day["calls"]["build_map"], {"n": 2, "failed": 1, "errors": {"OSError": 1},
                                                     "time": [1, 0, 1, 0, 0]})
        self.assertIn("open_project", day["calls"])
        self.assertEqual(day["jobs"]["play"]["done"], 1)
        self.assertEqual(day["jobs"]["play"]["failed"], 1)
        self.assertEqual(day["jobs"]["play"]["build_errors"], 3)
        self.assertEqual(day["jobs"]["play"]["time"], [0, 1, 0, 1, 0])
        self.assertEqual(day["updates"]["installed"], 1)
        self.assertEqual(day["played"], {"total": 42, "mods": {"cool-mod@1.2": 42}})
        self.assertEqual(day["own_mods"], 2)

    def test_counts_survive_a_restart(self):
        w = self.watch()
        w.call("a", 0.1)
        w.save()
        self.assertEqual(self.watch().days[bugwatch._today()]["calls"]["a"]["n"], 1)


class WhatIsSent(BugWatchTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")

    def test_a_day_fits_the_servers_rules(self):
        w = self.watch()
        for i in range(200):  # more calls than the server takes
            for _ in range(i % 5 + 1):
                w.call(f"call{i:03d}", 0.2, KeyError() if i % 3 else None)
        for i in range(40):
            w.job(f"job{i}", i % 2 == 0, 3, RuntimeError())
        out = w.payload(bugwatch._today(), w.days[bugwatch._today()])
        self.assertEqual(out["v"], 1)
        self.assertEqual(out["app"], "studio")
        self.assertEqual(len(out["id"]), 32)
        self.assertRegex(out["user"], r"^Nick#\d{4}$")
        self.assertLessEqual(len(out["calls"]), 150)
        self.assertLessEqual(len(out["jobs"]), 30)
        kinds = sum(len(v.get("errors", {})) for g in ("calls", "jobs") for v in out[g].values())
        self.assertLessEqual(kinds, 100)
        self.assertLessEqual(len(json.dumps(out, separators=(",", ":")).encode()), 64 * 1024)
        for name in list(out["calls"]) + list(out["jobs"]):
            self.assertRegex(name, r"^[A-Za-z0-9_.:-]{1,64}$")
        self.assertTrue(is_clean(out))
        self.assertIn("call199", out["calls"])  # the most-used are the ones kept

    def test_finished_days_go_to_the_outbox_and_old_ones_are_dropped(self):
        w = self.watch()
        now = datetime.now(timezone.utc)
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        too_old = (now - timedelta(days=31)).strftime("%Y-%m-%d")
        w.days = {yesterday: bugwatch._blank_day("0.9.8.8"), too_old: bugwatch._blank_day("0.9.8.1")}
        w.days[yesterday]["calls"]["x"] = {"n": 1, "failed": 0, "errors": {}, "time": [1, 0, 0, 0, 0]}
        self.assertEqual(w.roll(), 1)
        sent = json.loads((w.outbox / f"day-studio-{yesterday}.json").read_text())
        self.assertEqual(sent["day"], yesterday)
        self.assertEqual(sent["version"], "0.9.8.8")  # the version of that day, not today's
        self.assertEqual(w.days, {})

    def test_sending(self):
        server = Server(200)
        w = self.watch(server)
        w._write_out("day-studio-2026-10-29.json", {"v": 1, "day": "2026-10-29"})
        w.crash({"kind": "app", "error": "KeyError", "frames": []}, send=False)
        self.assertEqual(w.send_waiting(), {"sent": 2, "waiting": 0, "dropped": 0})
        self.assertEqual(sorted(p for p, _ in server.sent), ["v1/crash", "v1/day"])
        self.assertEqual(list(w.outbox.glob("*.json")), [])
        self.assertGreater(homes.settings(self.home)["bugwatch"]["last_send"], 0)

    def test_days_go_once_a_day_crashes_at_once(self):
        server = Server(200)
        w = self.watch(server)
        values = homes.settings(self.home)
        values["bugwatch"]["last_send"] = int(time.time())  # just sent
        homes.save_settings(self.home, values)
        w._write_out("day-studio-2026-10-29.json", {"v": 1})
        w.crash({"kind": "app", "error": "KeyError", "frames": []}, send=False)
        self.assertEqual(w.send_waiting(), {"sent": 1, "waiting": 1, "dropped": 0})
        self.assertEqual([p for p, _ in server.sent], ["v1/crash"])

    def test_switched_off_or_offline_waits_refused_goes(self):
        for status, kept in ((503, True), (500, True), (400, False), (413, False), (429, False)):
            w = self.watch(Server(status))
            w.crash({"kind": "app", "error": "KeyError", "frames": []}, send=False)
            w.send_waiting()
            self.assertEqual(bool(list(w.outbox.glob("*.json"))), kept, status)
            for p in w.outbox.glob("*.json"):
                p.unlink()

    def test_nothing_goes_without_the_players_yes(self):
        server = Server(200)
        w = self.watch(server)
        w._write_out("day-studio-2026-10-29.json", {"v": 1})
        bugwatch.turn_off(self.home)
        w.send_waiting(force=True)
        self.assertEqual(server.sent, [])


class Crashes(BugWatchTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")

    def test_an_app_crash_names_only_our_own_lines(self):
        w = self.watch()
        from types import SimpleNamespace as Frame  # (a Mock takes name= as its own label)
        fake = [Frame(filename="C:\\Python312\\Lib\\json\\decoder.py", lineno=3, name="decode"),
                Frame(filename="D:\\RUSE-2.0\\code\\src\\ruse_studio\\api.py", lineno=9, name="open_project")]
        with mock.patch.object(w, "send_waiting"), mock.patch("traceback.extract_tb", return_value=fake):
            w.app_crash(ValueError, ValueError("x"), None)
        files = list(w.outbox.glob("crash-*.json"))
        self.assertEqual(len(files), 1)
        body = json.loads(files[0].read_text())
        self.assertEqual(body["kind"], "app")
        self.assertEqual(body["error"], "ValueError")
        self.assertEqual(body["frames"], [["ruse_studio/api.py", 9, "open_project"]])
        self.assertTrue(is_clean(body))
        self.assertEqual(w.days[bugwatch._today()]["app_crashes"], 1)

    def test_no_paths(self):
        text = bugwatch.no_paths('File "D:\\RUSE-2.0\\tests\\instances\\x\\scripts\\a.py", line 4 C:/Users/me/x')
        self.assertNotRegex(text, r"(?:^|[^A-Za-z0-9])[A-Za-z]:[\\/]")
        self.assertIn("a.py", text)
        self.assertTrue(is_clean(text))

    def dump(self, code=0x29A, address=0x7FF612341234, base=0x7FF612340000, extra=b"", program=None):
        """A small crash report file: the header, an ExceptionStream, a ModuleListStream with one module, and `extra`.
        The module is the game's program; with `program` (a path), that program's instead: another program's report."""
        name = "C:\\Games\\R.U.S.E\\RUSE.exe".encode("utf-16-le")
        if program is not None:
            name = program.encode("utf-16-le")
        header = b"MDMP" + struct.pack("<IIIIIQ", 0xA793, 2, 32, 0, 0, 0)
        exc_at = 32 + 24
        exception = struct.pack("<II", 1, 0) + struct.pack("<IIQQII", code, 0, 0, address, 0, 0) + b"\0" * 120
        mods_at = exc_at + len(exception)
        name_at = mods_at + 4 + 108
        module = struct.pack("<QIIII", base, 0x200000, 0, 0, name_at) + b"\0" * (108 - 24)
        mods = struct.pack("<I", 1) + module
        directory = struct.pack("<III", 6, len(exception), exc_at) + struct.pack("<III", 4, len(mods), mods_at)
        return header + directory + exception + mods + struct.pack("<I", len(name)) + name + extra

    def test_reading_a_game_crash_report(self):
        text = b'Traceback (most recent call last):\n  File "D:\\RUSE-2.0\\x\\events.py", line 40\nKeyError: 1\x00'
        p = self.home / "report.dmp"
        p.write_bytes(self.dump(extra=b"\0junk\0" + text))
        found = bugwatch.read_dump(p)
        self.assertEqual(found["code"], "0x29a")
        self.assertEqual(found["module"], "RUSE.exe")
        self.assertEqual(found["offset"], "0x1234")
        self.assertIn("KeyError: 1", found["traceback"])
        self.assertNotIn("D:\\", found["traceback"])
        p.write_bytes(self.dump(code=0xC0000005))
        self.assertNotIn("traceback", bugwatch.read_dump(p))
        p.write_bytes(b"not a dump")
        self.assertIsNone(bugwatch.read_dump(p))

    def test_the_game_watch(self):
        local = self.home / "local"
        rpt = local / "Temp" / "CrashRpt_x"
        rpt.mkdir(parents=True)
        polls = iter([None, None, 0])

        class Game:
            def poll(self):
                return next(polls)

        times = iter([1000.0, 1600.0, 1600.0, 1600.0])
        w = self.watch()

        def sleep(_seconds):
            (rpt / "report.dmp").write_bytes(self.dump(code=0xC0000005))
            os.utime(rpt / "report.dmp", (1500, 1500))

        g = bugwatch.GameWatch(w, Game(), ["cool-mod@1.2"], 1, sleep=sleep, clock=lambda: next(times),
                               local=str(local))
        with mock.patch.object(w, "send_waiting"):
            g.run()
        day = w.days[bugwatch._today()]
        self.assertEqual(day["played"]["total"], 10)
        crashes = [json.loads(p.read_text()) for p in w.outbox.glob("crash-*.json")]
        self.assertEqual(len(crashes), 1)
        self.assertEqual(crashes[0]["kind"], "game")
        self.assertEqual(crashes[0]["code"], "0xc0000005")
        self.assertEqual(crashes[0]["mods"], ["cool-mod@1.2"])
        self.assertEqual(crashes[0]["own_mods"], 1)
        self.assertTrue(is_clean(crashes[0]))

    BASE = 0x7FF612340000

    def exe(self) -> Path:
        """A small program file: one runnable section (.text) at 0x1000, with a call ending right before 0x1105
        (e8 rel32), 0x1206 (ff 15) and 0x1405 (e8), and nothing like a call before 0x1300."""
        raw = bytearray(0x2400)
        struct.pack_into("<I", raw, 0x3C, 0x80)
        raw[0x80:0x84] = b"PE\0\0"
        struct.pack_into("<HH", raw, 0x84, 0x8664, 1)
        struct.pack_into("<H", raw, 0x94, 0xF0)
        struct.pack_into("<8sIIIIIIHHI", raw, 0x98 + 0xF0, b".text", 0x2000, 0x1000, 0x2000, 0x400, 0, 0, 0, 0,
                         0x60000020)
        raw[0x400 + 0x105 - 5] = 0xE8
        raw[0x400 + 0x206 - 6:0x400 + 0x206 - 4] = b"\xff\x15"
        raw[0x400 + 0x405 - 5] = 0xE8
        p = self.home / "copy" / "RUSE.exe"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(bytes(raw))
        return p

    def dump_with_stack(self, words_before: list, words: list, access=(0, 0x20), memory_list=False, place=0x4321,
                        build=(0x2000000, 0, 0), kept=()) -> bytes:
        """A crash report file of a bad memory access in RUSE.exe (+0x4321) by thread 7: its exception record with
        `access` (what, where) and its registers (the stack's top after `words_before`), the module list, and the
        thread list with its stack: `words_before` (under the top: not the chain's) then `words`. `memory_list`: as
        the game's own crash reporter writes it, the thread's stack named at 0 and kept in a memory list instead."""
        name = "C:\\Games\\R.U.S.E\\RUSE.exe".encode("utf-16-le")
        # (item 25) `place`: where it stopped, from the program's start; `build`: the program's size, checksum and time
        # stamp in the module list; `kept`: more memory the report kept, [(address, bytes)], in the memory list too
        stack = b"".join(struct.pack("<Q", w) for w in words_before + words)
        stack_start = 0x000000E5F7F00000
        memory_list = memory_list or bool(kept)
        streams = 4 if memory_list else 3
        exc_at = 32 + 12 * streams          # the parts, one after another, after the header and the directory
        ctx_at = exc_at + 168
        mods_at = ctx_at + 0x4D0
        name_at = mods_at + 4 + 108
        threads_at = name_at + 4 + len(name)
        stack_at = threads_at + 4 + 48
        memory_at = stack_at + len(stack)
        exception = (struct.pack("<II", 7, 0) + struct.pack("<IIQQII", 0xC0000005, 0, 0, self.BASE + place, 2, 0)
                     + struct.pack("<QQ", *access) + b"\0" * 104 + struct.pack("<II", 0x4D0, ctx_at))
        context = bytearray(0x4D0)
        struct.pack_into("<Q", context, 0x98, stack_start + 8 * len(words_before))
        mods = struct.pack("<I", 1) + struct.pack("<QIIII", self.BASE, *build, name_at) + b"\0" * (108 - 24)
        threads = struct.pack("<I", 1) + struct.pack("<IIIIQQIIII", 7, 0, 0, 0, 0, stack_start, len(stack),
                                                     0 if memory_list else stack_at, 0x4D0, ctx_at)
        memory = struct.pack("<I", 1 + len(kept)) + struct.pack("<QII", stack_start, len(stack), stack_at)
        where = memory_at + 4 + 16 * (1 + len(kept))   # the kept pieces' bytes, after the memory list
        for start, blob in kept:
            memory += struct.pack("<QII", start, len(blob), where)
            where += len(blob)
        memory += b"".join(blob for _start, blob in kept)
        header = b"MDMP" + struct.pack("<IIIIIQ", 0xA793, streams, 32, 0, 0, 0)
        directory = (struct.pack("<III", 6, len(exception), exc_at) + struct.pack("<III", 4, len(mods), mods_at)
                     + struct.pack("<III", 3, len(threads), threads_at))
        if memory_list:
            directory += struct.pack("<III", 5, len(memory), memory_at)
        return (header + directory + exception + bytes(context) + mods + struct.pack("<I", len(name)) + name
                + threads + stack + (memory if memory_list else b""))

    def test_a_game_crash_names_what_it_tried_and_its_chain(self):
        b = self.BASE
        p = self.home / "report.dmp"
        p.write_bytes(self.dump_with_stack(
            words_before=[b + 0x1405],                                   # under the stack's top: not the chain's
            words=[b + 0x1300, 0x1234, b + 0x1105, 0x41414141, b + 0x1105, b + 0x1206, b + 0x3000000]))
        found = bugwatch.read_dump(p, self.exe())
        self.assertEqual((found["code"], found["module"], found["offset"]), ("0xc0000005", "RUSE.exe", "0x4321"))
        self.assertEqual(found["access"], "read 0x20")
        # only the words right after a call (not 0x1300), each once, nearest first; none from outside RUSE.exe
        self.assertEqual(found["chain"], ["RUSE.exe+0x1105", "RUSE.exe+0x1206"])
        # without the copy's RUSE.exe there's no chain (a word into the program could be any pointer), the rest stays
        alone = bugwatch.read_dump(p)
        self.assertEqual((alone["access"], "chain" in alone), ("read 0x20", False))
        self.assertIsNone(bugwatch.read_dump(p, self.home / "no such RUSE.exe").get("chain"))
        p.write_bytes(self.dump_with_stack([], [b + 0x1105], access=(1, 0xDEAD0000)))
        self.assertEqual(bugwatch.read_dump(p, self.exe())["access"], "write 0xdead0000")
        # the game's own crash reporter keeps the stacks in a memory list (each thread's stack named at 0): read there,
        # never from the file's start
        p.write_bytes(self.dump_with_stack([b + 0x1405], [b + 0x1300, b + 0x1206, b + 0x1105], memory_list=True))
        self.assertEqual(bugwatch.read_dump(p, self.exe())["chain"], ["RUSE.exe+0x1206", "RUSE.exe+0x1105"])
        # the older layout (no registers, no thread list) still reads as before; "build", the program's size,
        # checksum and time stamp from the module list, is for the crash code only (never sent: game_crash)
        p.write_bytes(self.dump(code=0xC0000005))
        found = bugwatch.read_dump(p, self.exe())
        self.assertEqual(sorted(found), ["build", "code", "module", "offset"])
        self.assertEqual(found["build"], [0x200000, 0, 0])

    def test_the_chain_and_access_go_with_the_crash(self):
        p = self.home / "report.dmp"
        p.write_bytes(self.dump_with_stack([], [self.BASE + 0x1105, self.BASE + 0x1206]))
        w = self.watch()
        w.game_crash(bugwatch.read_dump(p, self.exe()), [], 1, send=False)
        (sent,) = [json.loads(f.read_text()) for f in w.outbox.glob("crash-*.json")]
        self.assertEqual((sent["access"], sent["chain"]), ("read 0x20", ["RUSE.exe+0x1105", "RUSE.exe+0x1206"]))
        self.assertTrue(is_clean(sent))

    def test_the_game_watch_reads_the_chain_with_the_copys_program(self):
        local = self.home / "local"
        rpt = local / "Temp" / "CrashRpt_x"
        rpt.mkdir(parents=True)
        polls = iter([None, 0])

        class Game:
            def poll(self):
                return next(polls)

        times = iter([1000.0, 1600.0, 1600.0])
        w = self.watch()

        def sleep(_seconds):
            (rpt / "report.dmp").write_bytes(self.dump_with_stack([], [self.BASE + 0x1206]))
            os.utime(rpt / "report.dmp", (1500, 1500))

        g = bugwatch.GameWatch(w, Game(), [], 0, sleep=sleep, clock=lambda: next(times), local=str(local),
                               exe=self.exe())
        with mock.patch.object(w, "send_waiting"):
            g.run()
        (sent,) = [json.loads(f.read_text()) for f in w.outbox.glob("crash-*.json")]
        self.assertEqual(sent["chain"], ["RUSE.exe+0x1206"])

    def test_mods_of(self):
        listed = self.home / "listed"
        listed.mkdir()
        (listed / "mod.toml").write_text('[mod]\nid = "cool-mod"\nversion = "1.2"\n')
        (listed / "tags.toml").write_text('tags = ["units"]\n')
        own = self.home / "own"
        own.mkdir()
        (own / "mod.toml").write_text('[mod]\nid = "secret"\nversion = "0.1"\n')
        self.assertEqual(bugwatch.mods_of([listed, own]), (["cool-mod@1.2"], 1))


class VersionFour(BugWatchTest):
    """What version 4 of the agreement added (the owner, 2026-11-13, "sure"): it goes only for a player who accepted
    version 4 and ticked Bug Watch; a mod's own map, its units' and files' names, its words and paths never."""

    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")
        self.game = self.home / "game"
        (self.game / "Maps" / "PC").mkdir(parents=True)
        for name in ("SuperCrossroads4", "M04_Cotentin"):
            (self.game / "Maps" / "PC" / f"DataMap{name}_v09.dat").write_bytes(b"")

    def accept(self, version):
        values = homes.settings(self.home)
        values["guard"] = {"terms": version}
        homes.save_settings(self.home, values)

    def report(self, current_map=None, ignored=0, code=0x29A):
        """A crash report file holding the game's script-error text as its error hook writes it."""
        text = b"Revision Data: 190852 - ruse.player.release\n\n"
        if current_map:
            text += b"Current Map: DataDir:\\DATASMAP\\" + current_map + b"\n\n"
        if ignored:
            text += b"Previously ignored errors: %d\n\n" % ignored
        text += b'Traceback (most recent call last):\n  File "DataDir:\\x\\menu.py", line 40, in f\nKeyError: 1\x00'
        p = self.home / "report.dmp"
        p.write_bytes(Crashes.dump(self, code=code, extra=b"\0junk\0" + text))
        return p

    def own_mods(self):
        """A mod from our list, an own folder mod (units, texts, a map's file, a mission script) and an own .rmod mod
        (a whole script, a map file, a value, a new unit, a text)."""
        from test_rmod import new_unit, rmod_json, set_values
        listed, own, rmodded = self.home / "cool-mod", self.home / "nicks-secret-mod", self.home / "nicks-rmod"
        for f in (listed, own, rmodded):
            f.mkdir()
        (listed / "mod.toml").write_text('[mod]\nid = "cool-mod"\nversion = "1.2"\n')
        (listed / "tags.toml").write_text('tags = ["units"]\n')
        (listed / "src").mkdir()
        (listed / "src" / "a.rndf").write_text("patch $/GFX/Everything/Descriptor_Unit_M3_Lee ( ProductionPrice = [1] )\n")
        (own / "mod.toml").write_text('[mod]\nid = "nicks-secret-mod"\nversion = "0.1"\n')
        (own / "src").mkdir()
        (own / "src" / "units.rndf").write_text("Nicks_Tank is clone $/GFX/Everything/Descriptor_Unit_M3_Lee\n"
                                                "(\n    ProductionPrice = [1, 1, 1, 1, 1]\n)\n")
        (own / "text").mkdir()
        (own / "text" / "baseunite.csv").write_text("key,us\nNICKS,Nick's tank\n")
        (own / "maps" / "nicks_island").mkdir(parents=True)
        (own / "maps" / "nicks_island" / "scenery.toml").write_text("\n")
        (own / "scripts" / "m06_ardennes" / "scripting_chapter1").mkdir(parents=True)
        (own / "scripts" / "m06_ardennes" / "scripting_chapter1" / "effetmap.py").write_text("x = 1\n")
        (rmodded / "mod.toml").write_text('[mod]\nid = "nicks-rmod"\nversion = "1.0.0"\n\n[rmod]\nfile = "N.rmod"\n')
        (rmodded / "N.rmod").write_text(rmod_json({"genpython/map/effetmap.xyz": b"XYZ0", "test/map/a/x.scenario": b"S"},
                                                  patches=[set_values("Unit_Battleship", VitesseLineaire=1),
                                                           new_unit("Unit_Nicks_Ship")], texts={"0123456789abcdef": "Nick"}))
        return [listed, own, rmodded]

    def test_only_with_version_4_accepted_and_bug_watch_on(self):
        self.assertEqual((bugwatch.agreement(self.home), bugwatch.allows_v4(self.home)), (0, False))
        for terms, allowed in ((3, False), (4, True), (5, True), (True, False), ("4", False)):
            self.accept(terms)
            self.assertEqual(bugwatch.allows_v4(self.home), allowed, terms)
        bugwatch.turn_off(self.home)
        self.assertFalse(bugwatch.allows_v4(self.home))   # version 4 accepted, Bug Watch off: nothing goes

    def test_the_map_by_the_games_own_name_or_said_as_a_mods(self):
        found = bugwatch.read_dump(self.report(b"SuperCrossRoads4"), install=self.game)
        self.assertEqual(found["map"], "SuperCrossroads4")     # the pack's own name, whatever the case in the text
        self.assertEqual(bugwatch.read_dump(self.report(b"IwoGround"), install=self.game)["map"], "own")
        self.assertNotIn("map", bugwatch.read_dump(self.report(), install=self.game))      # the text names none
        self.assertNotIn("map", bugwatch.read_dump(self.report(b"M04_cotentin")))       # no install given: none
        self.assertNotIn("map", bugwatch.read_dump(self.report(b"Edge", code=0xC0000005), install=self.game))

    def test_the_count_of_errors_let_pass_before_the_stop(self):
        """The game's own "Previously ignored errors: N" line (each of our script guards adds 1 when it steps in):
        the game's own error text, which version 3 lists."""
        self.assertEqual(bugwatch.read_dump(self.report(b"Edge", ignored=3))["ignored"], 3)
        self.assertNotIn("ignored", bugwatch.read_dump(self.report(b"Edge")))

    def test_a_game_crash_under_version_3_and_under_version_4(self):
        found = bugwatch.read_dump(self.report(b"IwoGround", ignored=2), install=self.game)
        holds = {"folder": 1, "maps": 1, "nonsense": 4}
        w = self.watch()
        self.accept(3)
        w.game_crash(found, ["cool-mod@1.2"], 1, send=False, holds=holds)
        self.accept(4)
        w.game_crash(found, ["cool-mod@1.2"], 1, send=False, holds=holds)
        v3, v4 = sorted((json.loads(f.read_text()) for f in w.outbox.glob("crash-*.json")), key=lambda b: "agreement" in b)
        self.assertEqual({"agreement", "map", "own"} & set(v3), set())
        self.assertEqual(v3["ignored"], 2)
        self.assertEqual((v4["agreement"], v4["map"], v4["own"], v4["ignored"]), (4, "own", {"folder": 1, "maps": 1}, 2))
        self.assertNotIn("IwoGround", json.dumps(v4))
        self.assertTrue(is_clean(v4))
        before = set(w.outbox.glob("crash-*.json"))
        w.game_crash(found, ["cool-mod@1.2"], 0, send=False, holds=holds)   # no own mod on: nothing about them
        # the file this call wrote: a name holds the millisecond and a random part, so two in one millisecond (seen on
        # GitHub's Linux job, 0.9.8.21) don't sort by when they were written
        (newest,) = set(w.outbox.glob("crash-*.json")) - before
        self.assertNotIn("own", json.loads(newest.read_text()))

    def test_the_day_under_version_3_and_under_version_4(self):
        w = self.watch()
        self.accept(3)
        w.played(10, ["cool-mod@1.2"], 1, {"folder": 1, "scripts": 1})
        out = w.payload(bugwatch._today(), w.days[bugwatch._today()])
        self.assertNotIn("own_holds", w.days[bugwatch._today()])
        self.assertEqual(("agreement" in out, "holds" in out["mods"]), (False, False))
        self.accept(4)
        w.played(5, [], 2, {"folder": 2, "scripts": 1, "maps": 1})
        w.played(5, [], 1, {"folder": 1, "texts": 1, "nonsense": 9})
        out = w.payload(bugwatch._today(), w.days[bugwatch._today()])
        self.assertEqual(out["agreement"], 4)
        self.assertEqual(out["mods"]["holds"], {"folder": 2, "scripts": 1, "maps": 1, "texts": 1})  # each kind's most
        self.assertTrue(is_clean(out))

    def test_what_the_players_own_mods_hold(self):
        mods = self.own_mods()
        self.assertEqual(bugwatch.own_holds(mods), {"folder": 1, "rmod": 1, "data": 2, "new_objects": 2, "texts": 2,
                                                    "maps": 2, "scripts": 2})
        self.assertEqual(bugwatch.own_holds(mods[:1]), {})                    # one from our list: named, not counted
        self.assertEqual(bugwatch.own_holds([self.home / "no such mod"]), {"folder": 1})   # unreadable: its format
        self.assertEqual(list(bugwatch.own_holds(mods)), [k for k in bugwatch.OWN_KINDS if k in bugwatch.own_holds(mods)])

    def test_the_game_watch_sends_them_under_version_4(self):
        self.accept(4)
        mods = self.own_mods()
        local = self.home / "local"
        rpt = local / "Temp" / "CrashRpt_x"
        rpt.mkdir(parents=True)
        polls = iter([None, 0])

        class Game:
            def poll(self):
                return next(polls)

        times = iter([1000.0, 1600.0, 1600.0])
        w = self.watch()
        report = self.report(b"IwoGround")

        def sleep(_seconds):
            (rpt / "report.dmp").write_bytes(report.read_bytes())
            os.utime(rpt / "report.dmp", (1500, 1500))

        g = bugwatch.GameWatch(w, Game(), ["cool-mod@1.2"], 2, sleep=sleep, clock=lambda: next(times),
                               local=str(local), folders=mods, game=self.game)
        with mock.patch.object(w, "send_waiting"):
            g.run()
        (sent,) = [json.loads(f.read_text()) for f in w.outbox.glob("crash-*.json")]
        self.assertEqual((sent["map"], sent["own"]["scripts"], sent["agreement"]), ("own", 2, 4))
        self.assertEqual(w.days[bugwatch._today()]["own_holds"]["new_objects"], 2)
        text = json.dumps(sent) + json.dumps(w.days)
        for secret in ("nicks", "Nick's", "Nicks_Tank", "Unit_Nicks_Ship", "ardennes", "IwoGround", "N.rmod"):
            self.assertNotIn(secret, text)


class KnownCrashes(BugWatchTest):
    """Item 25 (the owner, 2026-11-13: "... if their unit was crashing the game, they should be told that." and "For
    25, they should also be told why that unit made the game crash. ..."): a crash at a place our list of known crashes
    knows gets its plain reason, and under version 4 of the agreement the unit the game was making, read from the crash
    report as knowncrashes.unit_number reads it; the unit goes out only as version 4 says ("one of the game's own
    units by its number; a unit a mod added only as "a mod's unit""), the reason and the unit's name never. The list is
    private since 2026-11-24 (rusemod.knowncrashes): these tests run on the made-up list (test_knowncrashes.MadeUp:
    the real list's reasons and ties, every number made up), kept on the PC as a fetch leaves it. Made-up reports and
    program files only: no number or detail of the game's program is written here."""

    BASE = Crashes.BASE
    UNIT, OTHER = 0x10000400, 0x20000400   # where the made-up reports keep units' descriptions (made up)

    def setUp(self):
        super().setUp()
        self.places = MadeUp
        self.known = MadeUp.known()
        self.made = next(at for at, (key, _chain, _stack) in MadeUp.PLACES.items() if key == "made")
        self.create = MadeUp.CREATING[0] + 0x40    # in the list's unit-creation range (a call right before it)
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._notice = None

    def tearDown(self):
        bugwatch._notice = None
        super().tearDown()

    def accept(self, version):
        VersionFour.accept(self, version)

    def program(self, places) -> Path:
        """A made-up program file: a call right before each of `places` (offsets from its start), one 4 KB runnable
        section for each place's page, and nothing else like a call."""
        pages = sorted({p & ~0xFFF for p in places})
        raw = bytearray(0x400 + 0x1000 * len(pages))
        struct.pack_into("<I", raw, 0x3C, 0x80)
        raw[0x80:0x84] = b"PE\0\0"
        struct.pack_into("<HH", raw, 0x84, 0x8664, len(pages))
        struct.pack_into("<H", raw, 0x94, 0xF0)
        for i, page in enumerate(pages):
            struct.pack_into("<8sIIIIIIHHI", raw, 0x188 + 40 * i, b".text", 0x1000, page, 0x1000, 0x400 + 0x1000 * i,
                             0, 0, 0, 0, 0x60000020)
        for p in places:
            raw[0x400 + 0x1000 * pages.index(p & ~0xFFF) + (p & 0xFFF) - 5] = 0xE8
        path = self.home / "copy" / "program.exe"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes(raw))
        return path

    def description(self, number, at=None, kind=None):
        """A made-up unit description as knowncrashes.unit_number reads one (one of the list's kinds first, the
        number where the list says), as a piece of memory a made-up report keeps (from 256 bytes before it)."""
        blob = bytearray(0x400)
        kind = min(MadeUp.KINDS) if kind is None else kind
        struct.pack_into("<Q", blob, 0x100, self.BASE + kind)
        struct.pack_into("<I", blob, 0x100 + MadeUp.NUMBER_AT, number)
        return ((at or self.UNIT) - 0x100, bytes(blob))

    def report(self, words=(), kept=(), place=None, build=None, below=()) -> Path:
        p = self.home / "report.dmp"
        p.write_bytes(Crashes.dump_with_stack(self, list(below), list(words), place=self.made if place is None else place,
                                              build=build or MadeUp.BUILD, kept=list(kept)))
        return p

    def test_a_crash_we_know_says_why_and_which_unit(self):
        program = self.program([self.create])
        p = self.report([0x1234, self.BASE + self.create, 0, self.UNIT, self.UNIT], [self.description(4059)])
        found = bugwatch.read_dump(p, program, unit=True, known=self.known)
        self.assertEqual((found["reason"], found["unit"]), ("made", 4059))
        asked = bugwatch.read_dump(p, program, known=self.known)  # the unit only when asked (version 4: GameWatch)
        self.assertEqual((asked["reason"], "unit" in asked), ("made", False))
        alone = bugwatch.read_dump(p, unit=True, known=self.known)   # no copy's program: no chain or stack to tie
        self.assertEqual((alone.get("reason"), "unit" in alone), (None, False))   # the place to a unit: nothing said
        build = MadeUp.BUILD
        big = (build[0] + 0x1000,) + build[1:]                    # the list's other build
        found = bugwatch.read_dump(self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)],
                                               build=big), program, unit=True, known=self.known)
        self.assertEqual((found["reason"], found["unit"]), ("made", 4059))
        self.assertEqual(self.known.builds, {build, big})         # those two only

    def test_with_no_list_no_reason_and_no_unit_and_the_rest_as_it_was(self):
        """No list on the PC (offline, the first start): read_dump says no reason and reads no unit; what a crash
        report sends (its code, module, place, access and chain) is the same as with the list. A list whose check
        raises costs the same, never the report."""
        program = self.program([self.create])
        p = self.report([0x1234, self.BASE + self.create, 0, self.UNIT], [self.description(4059)])
        with_list = bugwatch.read_dump(p, program, unit=True, known=self.known)
        without = bugwatch.read_dump(p, program, unit=True)
        self.assertEqual(("reason" in without, "unit" in without), (False, False))
        sent = ("code", "module", "offset", "access", "chain", "build")
        self.assertEqual({k: without.get(k) for k in sent}, {k: with_list.get(k) for k in sent})
        with mock.patch.object(knowncrashes, "reason", side_effect=RuntimeError("a list that fails")):
            failing = bugwatch.read_dump(p, program, unit=True, known=self.known)
        self.assertEqual(("reason" in failing, "unit" in failing), (False, False))
        self.assertEqual({k: failing.get(k) for k in sent}, {k: with_list.get(k) for k in sent})
        self.assertTrue(failing["list_error"])                    # (said, never silent: GameWatch counts it)
        self.assertNotIn("list_error", with_list)

    def test_no_reason_or_unit_where_it_cant_be_sure(self):
        program = self.program([self.create])
        making, one = [0, self.BASE + self.create, self.UNIT], [self.description(4059)]
        other_build = MadeUp.BUILD[:2] + (MadeUp.BUILD[2] + 1,)
        longer = (MadeUp.BUILD[0] + 0x2000,) + MadeUp.BUILD[1:]
        for place, build in ((0x4321, None), (self.made, other_build), (self.made, longer)):
            # a place we don't know, or another build of the program (its places may be other code): nothing
            found = bugwatch.read_dump(self.report(making, one, place=place, build=build), program, unit=True,
                                       known=self.known)
            self.assertEqual((found.get("reason"), found.get("unit")), (None, None))
            self.assertEqual(found["code"], "0xc0000005")         # the rest is read as before
        two = bugwatch.read_dump(self.report(making + [self.OTHER], one + [self.description(4404, self.OTHER)]),
                                 program, unit=True, known=self.known)   # two different units: none said
        self.assertEqual((two["reason"], two.get("unit")), ("made", None))
        for words in ([self.UNIT, self.BASE + self.create, 0],   # only below the creating step's return (nearer)
                      [0, self.UNIT]):                           # no return into it at all
            self.assertIsNone(bugwatch.read_dump(self.report(words, one), program, unit=True,
                                                 known=self.known).get("unit"))
        not_a_unit = [self.description(4059, kind=0x1234)]       # not one of the list's kinds there
        self.assertIsNone(bugwatch.read_dump(self.report(making, not_a_unit), program, unit=True,
                                             known=self.known).get("unit"))
        nested = [0, self.BASE + self.create, self.UNIT, self.BASE + self.create, self.OTHER]  # beyond the next
        found = bugwatch.read_dump(self.report(nested, one + [self.description(4404, self.OTHER)]), program, unit=True,
                                   known=self.known)
        self.assertEqual(found["unit"], 4059)                     # return into the creating step: not read
        with mock.patch.object(bugwatch, "_kept_memory", side_effect=struct.error("cut short")):
            found = bugwatch.read_dump(self.report(making, one), program, unit=True, known=self.known)
        self.assertEqual((found["reason"], found.get("unit")), ("made", None))   # the report itself is still read

    ELSEWHERE = 0x40   # a made-up place in none of the list's ranges (the made-up program has a call right before it)

    def said(self, place, returns, program) -> str | None:
        """The reason read_dump gives a made-up crash at `place` whose stack returns to `returns` (offsets)."""
        found = bugwatch.read_dump(self.report([self.BASE + r for r in returns], place=place), program,
                                   known=self.known)
        return found.get("reason")

    def test_a_place_is_told_only_with_what_ties_it_to_its_reason(self):
        """Review defect 1 (2026-11-13): the part place is told only with the two-axis turret's steps in its chain,
        the made place only with the unit-creation step in the stack (the list's chain and stack groups); the same
        crash reached from elsewhere gets no reason."""
        part = next(at for at, (key, _chain, _stack) in MadeUp.PLACES.items() if key == "part")
        turret = MadeUp.TWO_AXIS[1][0] + 0x40
        program = self.program([turret, self.create, self.ELSEWHERE])
        self.assertIsNone(self.said(part, [self.ELSEWHERE], program))       # reached from elsewhere: nothing
        self.assertEqual(self.said(part, [turret], program), "part")        # the turret's step in the chain
        self.assertIsNone(self.said(self.made, [self.ELSEWHERE], program))  # no unit-creation step in the stack
        self.assertEqual(self.said(self.made, [self.ELSEWHERE, self.create], program), "made")

    def test_every_place_needs_all_that_ties_it_and_nothing_else(self):
        """The same for every place of the list (its chain groups and its stack groups): all it needs, told; any one
        of it missing, or a crash there reached from elsewhere, not told; a place that needs nothing, always told."""
        for place, (key, chain, stack) in MadeUp.PLACES.items():
            groups = list(chain) + list(stack)
            ties = [group[0][0] + 0x40 for group in groups]        # one place in each group
            program = self.program(ties + [self.ELSEWHERE])
            self.assertEqual(self.said(place, ties, program), key, hex(place))
            for i in range(len(ties)):
                self.assertIsNone(self.said(place, ties[:i] + ties[i + 1:], program), hex(place))
            if groups:
                self.assertIsNone(self.said(place, [self.ELSEWHERE], program), hex(place))
            self.assertEqual(bugwatch.read_dump(self.report([self.BASE + t for t in ties], place=place),
                                                known=self.known).get("reason"),
                             None if groups else key, hex(place))  # no copy's program: no chain to tie it with

    def test_what_ties_a_place_is_found_further_up_than_the_chain_a_report_sends(self):
        """The unit-creation step can be further up the stack than the 16 places a report sends (two of the held
        reports): read_dump looks for it in the whole stack it reads, and the chain sent is still the nearest 16."""
        nearer = [0x40 * (i + 1) for i in range(bugwatch.CHAIN_MOST)]   # 16 made-up places before it
        program = self.program(nearer + [self.create])
        found = bugwatch.read_dump(self.report([self.BASE + n for n in nearer + [self.create]], place=self.made),
                                   program, known=self.known)
        self.assertEqual(found["reason"], "made")
        self.assertEqual([c.rsplit("+", 1)[1] for c in found["chain"]], [f"0x{n:x}" for n in nearer])

    def test_a_reason_for_a_place_nothing_ties_to_a_unit_doesnt_say_a_unit(self):
        """The setup and mesh places: the list ties them to no unit (no chain or stack they need), so their reasons
        say "a model", in every language, never a unit's (each language's word for unit). The made place, tied to a
        unit being created, says the unit's model (the control)."""
        import tomllib
        unit = {"us": "unit", "fr": "unité", "ger": "einheit", "ita": "unità", "spa": "unidad", "pol": "jednost",
                "ru": "юнит", "cz": "jednotk", "jpn": "ユニット", "sc": "单位", "fa": "یگان"}
        words = tomllib.loads((Path(__file__).resolve().parents[1] / "src" / "ruse_launcher" / "words.toml")
                              .read_text(encoding="utf-8"))
        for key in ("setup", "mesh"):
            places = [p for p, (k, _chain, _stack) in MadeUp.PLACES.items() if k == key]
            self.assertTrue(places and not any(MadeUp.PLACES[p][1] or MadeUp.PLACES[p][2] for p in places),
                            key)                                  # (nothing ties them)
            for lang, text in words[f"crash_why_{key}"].items():
                self.assertNotIn(unit[lang], text.lower(), f"{key} {lang}")
        for lang, text in words["crash_why_made"].items():               # (the control: a unit being created)
            self.assertIn(unit[lang], text.lower(), lang)

    def test_every_reason_has_its_words_in_every_language(self):
        import re
        import tomllib
        from rusemod import schema
        self.assertEqual({key for key, _chain, _stack in MadeUp.PLACES.values()}, set(knowncrashes.REASONS))
        root = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher"
        words = tomllib.loads((root / "words.toml").read_text(encoding="utf-8"))
        crash_words = ["crash_unit", "crash_mod_unit", "crash_no_unit", "crash_no_list", "crash_code",
                       "crash_code_under", "crash_copy", "crash_copied", "tip_crash_copy", "tip_crash_github"]
        for key in [f"crash_why_{r}" for r in knowncrashes.REASONS] + crash_words:
            self.assertEqual(sorted(words[key]), sorted(schema.APP_LANGS), key)
            blanks = {tuple(sorted(re.findall(r"\{(\w+)\}", text))) for text in words[key].values()}
            self.assertEqual(len(blanks), 1, key)                 # the same {blanks} in every language
        app = (root / "ui" / "app.js").read_text(encoding="utf-8")
        self.assertIn("api().bugwatch_crash()", app)              # the page asks after a Play, and says it
        self.assertIn('if (j.state === "done") watchCrash();', app)
        self.assertIn("bugwatch_crash:", (root / "ui" / "fake-api.js").read_text(encoding="utf-8"))

    def run_game(self, report: bytes, named, program, kept=True):
        """A game the app started that closed leaving `report`: what went out, what the window is told, and the
        stand-in that named the unit (`named`: unit_named's answer). `kept`: the made-up list is on the PC (as a fetch
        left it), when no list file is there yet."""
        local = self.home / "local"
        rpt = local / "Temp" / "CrashRpt_x"
        rpt.mkdir(parents=True, exist_ok=True)
        polls = iter([None, 0])

        class Game:
            def poll(self):
                return next(polls)

        times = iter([1000.0, 1600.0, 1600.0])
        w = self.watch()

        def sleep(_seconds):
            (rpt / "report.dmp").write_bytes(report)
            os.utime(rpt / "report.dmp", (1500, 1500))

        if kept and not (self.home / bugwatch.FOLDER / knowncrashes.LIST_FILE).exists():
            MadeUp.keep(self.home)                                # (as a fetch under version 5 left it)
        g = bugwatch.GameWatch(w, Game(), [], 1, sleep=sleep, clock=lambda: next(times), local=str(local),
                               exe=program, game=self.home / "game")
        with mock.patch.object(w, "send_waiting"), mock.patch.object(bugwatch, "unit_named",
                                                                     return_value=named) as naming:
            g.run()
            if g.refreshing is not None:
                g.refreshing.join(10)
        self.game_watch = g
        files = list(w.outbox.glob("crash-*.json"))
        (sent,) = [json.loads(f.read_text()) for f in files]
        for f in files:
            f.unlink()
        self.days = w.days
        return sent, bugwatch.crash_notice(), naming

    def test_the_game_watch_tells_the_player_and_sends_the_unit_as_version_4_says(self):
        program = self.program([self.create])
        report = self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)]).read_bytes()
        horse = {"name": "Horse Squad", "added": True}
        self.accept(3)                                            # version 3: why only; no unit read, named or sent
        sent, told, naming = self.run_game(report, horse, program)
        self.assertEqual(told, {"watching": False, "notice": {"why": "made", "unit": None, "added": False,
                                                              "list": True}})
        naming.assert_not_called()
        self.assertNotIn("unit", sent)
        self.accept(4)                                            # a mod's unit: named for the player, sent as added
        sent, told, naming = self.run_game(report, horse, program)
        self.assertEqual(told["notice"], {"why": "made", "unit": "Horse Squad", "added": True, "list": True})
        self.assertEqual((sent["unit"], sent["agreement"]), ({"added": True}, 4))
        self.assertEqual(naming.call_args[0][:2], (4059, program.parent))    # named from the crashed copy's data
        bodies = [sent]
        sent, told, _ = self.run_game(report, {"name": "DECOY AIRFIELD", "added": False}, program)
        self.assertEqual((sent["unit"], told["notice"]["unit"]), ({"game": 4059}, "DECOY AIRFIELD"))  # the game's own
        bodies.append(sent)
        for named in (None, {"name": "Horse Squad", "added": None}):   # not found, or whose it is isn't known
            sent, told, _ = self.run_game(report, named, program)
            self.assertNotIn("unit", sent)
            self.assertEqual(told["notice"]["why"], "made")
            bodies.append(sent)
        for body in bodies:                                       # never the reason or a name in what goes out
            self.assertFalse({"reason", "unit_name", "unit_added"} & set(body))
            self.assertNotIn("Horse", json.dumps(body))
            self.assertNotIn("DECOY", json.dumps(body))
            self.assertTrue(is_clean(body))
        self.assertIsNone(bugwatch.crash_notice()["notice"])      # handed over once
        unknown = self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)], place=0x4321)
        sent, told, _ = self.run_game(unknown.read_bytes(), horse, program)   # a crash we don't know: nothing told
        self.assertEqual((told["notice"], "unit" in sent), (None, False))

    def test_the_window_waits_while_a_game_is_watched(self):
        import threading
        closed = threading.Event()

        class Game:
            def poll(self):
                return 0 if closed.is_set() else None

        class Api(bugwatch.BugWatchCalls):
            _home = str(self.home)

        g = bugwatch.GameWatch(self.watch(), Game(), [], 0, sleep=lambda _s: closed.wait(0.01),
                               local=str(self.home / "none"))
        g.start()
        try:
            self.assertEqual(Api().bugwatch_crash(), {"watching": True, "notice": None})
        finally:
            closed.set()
            g.join(10)
        self.assertEqual(Api().bugwatch_crash(), {"watching": False, "notice": None})

    def finished_game(self, report: bytes, program, named, w=None):
        """A game the app started that has closed, leaving `report`, watched to the end here (GameWatch.run; the unit
        named as `named` says): its Watch. The window isn't asked: the notice stays kept, as when no page asked."""
        local = self.home / "local"
        dump = local / "Temp" / "CrashRpt_x" / "report.dmp"
        dump.parent.mkdir(parents=True, exist_ok=True)
        dump.write_bytes(report)
        os.utime(dump, (1500, 1500))

        class Closed:
            def poll(self):
                return 0

        times = iter([1000.0, 1600.0])
        w = w or self.watch()
        if not (self.home / bugwatch.FOLDER / knowncrashes.LIST_FILE).exists():
            MadeUp.keep(self.home)                                # (as a fetch under version 5 left it)
        g = bugwatch.GameWatch(w, Closed(), [], 1, sleep=lambda _s: None, clock=lambda: next(times), local=str(local),
                               exe=program, game=self.home / "game")
        with mock.patch.object(w, "send_waiting"), mock.patch.object(bugwatch, "unit_named", return_value=named):
            g.run()
        return w

    def test_a_notice_the_window_never_took_goes_when_the_next_game_starts(self):
        """Review defect 3 (2026-11-13): game 1 stops at a crash we know while no page asks (a browser tab reloaded or
        closed, a call that failed); the player plays again: while game 2 runs, game 1's notice is never said. The
        control: game 2's own crash we know is told."""
        import threading
        program = self.program([self.create])
        report = self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)]).read_bytes()
        self.accept(4)
        w = self.finished_game(report, program, {"name": "Horse Squad", "added": True})
        self.assertIsNotNone(bugwatch._notice)                    # game 1's, kept: nobody took it
        running = threading.Event()

        class Running:
            def poll(self):
                return 0 if running.is_set() else None

        local = self.home / "local"
        g2 = bugwatch.GameWatch(w, Running(), [], 1, sleep=lambda _s: running.wait(0.01), local=str(local),
                                exe=program, game=self.home / "game")
        with mock.patch.object(w, "send_waiting"), mock.patch.object(bugwatch, "unit_named",
                                                                     return_value={"name": "Tiger", "added": False}):
            g2.start()
            try:
                self.assertEqual(bugwatch.crash_notice(), {"watching": True, "notice": None})   # game 2 running
                dump = local / "Temp" / "CrashRpt_y" / "report.dmp"   # then game 2 stops at a crash we know too
                dump.parent.mkdir(parents=True, exist_ok=True)
                dump.write_bytes(report)
                os.utime(dump, (g2.started + 1, g2.started + 1))
            finally:
                running.set()
                g2.join(10)
        self.assertEqual(bugwatch.crash_notice(), {"watching": False,
                                                   "notice": {"why": "made", "unit": "Tiger", "added": False,
                                                              "list": True}})

    def test_the_player_is_told_when_bug_watch_cant_write_its_records(self):
        """Review defect 4 (2026-11-13): Bug Watch's outbox can't be written (a full disk, a folder another program
        holds): the player is told all the same, and its other records are kept. And when a record before the crash
        report can't be written, the notice and the crash report still are."""
        program = self.program([self.create])
        report = self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)]).read_bytes()
        self.accept(4)
        horse = {"name": "Horse Squad", "added": True}
        with mock.patch.object(bugwatch.Watch, "_write_out", side_effect=OSError("disk full")):
            w = self.finished_game(report, program, horse)        # (no error out of the watch)
        self.assertEqual(bugwatch.crash_notice()["notice"], {"why": "made", "unit": "Horse Squad", "added": True,
                                                             "list": True})
        self.assertEqual(w.days[bugwatch._today()]["played"]["total"], 10)   # the minutes played: kept
        with mock.patch.object(bugwatch.Watch, "played", side_effect=OSError("held")):
            w = self.finished_game(report, program, horse)
        self.assertEqual(bugwatch.crash_notice()["notice"]["unit"], "Horse Squad")
        self.assertEqual(len(list(w.outbox.glob("crash-*.json"))), 1)        # the crash report: written

    def test_a_crash_report_gone_while_it_is_listed_doesnt_stop_the_watch(self):
        """The same kind: a crash report gone between two looks (taken away meanwhile) costs only itself; the others
        are still listed (in the order they were written), and the watch goes on to tell the player."""
        local = self.home / "local"
        gone, kept = (local / "Temp" / "CrashRpt_a" / "report.dmp", local / "Temp" / "CrashRpt_b" / "report.dmp")
        for i, p in enumerate((gone, kept)):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"MDMP")
            os.utime(p, (1500 + i, 1500 + i))
        real, looks = Path.stat, {}

        def stat(path, *args, **kwargs):                          # taken away after its first look
            looks[str(path)] = looks.get(str(path), 0) + 1
            if str(path) == str(gone) and looks[str(path)] > 1:
                raise FileNotFoundError(str(path))
            return real(path, *args, **kwargs)
        with mock.patch.object(Path, "stat", stat):
            self.assertEqual(bugwatch.crash_dumps_since(1000, str(local)), [gone, kept])
        self.assertEqual(bugwatch.crash_dumps_since(1501, str(local)), [kept])   # (the control: by its time)

    @unittest.skipUnless(os.name == "nt", "Windows refuses to replace a file that is held")
    def test_a_copys_unit_data_is_let_go_before_its_units_are_read(self):
        """Review suspicion 4 (2026-11-13): naming a unit reads the crashed copy's unit data for a few seconds after
        the game closed; all that time the file must not be held, so a build of that copy just then can put a new one
        in its place (Windows refuses that for a file held open or mapped)."""
        from fixtures import make_edat
        pack = self.home / "copy" / bugwatch.UNIT_DATA
        pack.parent.mkdir(parents=True, exist_ok=True)
        pack.write_bytes(make_edat([("file", "x.bin", b"x")]))
        newer, replaced = self.home / "newer.dat", []

        def load_pack(_arc, _cache):                              # while its units are read: a build's new file
            newer.write_bytes(b"newer")
            try:
                os.replace(newer, pack)
                replaced.append("replaced")
            except OSError as exc:
                replaced.append(type(exc).__name__)
            return mock.Mock(base=mock.Mock(objects={}))
        with mock.patch("rusemod.build.load_pack", load_pack):
            self.assertEqual(bugwatch._units_in(pack), {})
        self.assertEqual(replaced, ["replaced"])
        self.assertEqual(pack.read_bytes(), b"newer")

    PAGE_IN_NODE = r"""
const fs = require("fs"), vm = require("vm");
const [appFile, casesFile] = process.argv.slice(-2);
const anything = new Proxy(function () {}, { get: (t, k) => (k === Symbol.toPrimitive ? () => "" : anything),
  apply: () => anything, set: () => true });
(async () => {
  const out = [];
  for (const c of JSON.parse(fs.readFileSync(casesFile, "utf8"))) {
    const timers = [], said = [], answers = c.answers.slice();
    let asks = 0;
    const ctx = vm.createContext({ console, document: anything, localStorage: anything, location: { search: "" },
      window: { addEventListener() {} }, URLSearchParams,
      setTimeout: (fn, ms) => { timers.push({ fn, ms }); return timers.length; }, clearTimeout: () => {} });
    vm.runInContext(fs.readFileSync(appFile, "utf8"), ctx, { filename: "app.js" });
    ctx.window.pywebview = { api: { bugwatch_crash: async () => {
      asks += 1;
      const a = answers.shift();
      if (a === undefined || a === "throw") throw new Error("the window was busy");
      return a;
    } } };
    Object.assign(ctx, { WORDS: c.words, SAID: said });
    vm.runInContext("state.words = WORDS; setMessage = (text, kind) => SAID.push([text, kind]);", ctx);
    vm.runInContext(c.call, ctx);
    const delays = [];
    for (let i = 0; i < 40 && timers.length; i++) {
      const { fn, ms } = timers.shift();
      delays.push(ms);
      await fn();
    }
    out.push({ asks, delays, said });
  }
  process.stdout.write(JSON.stringify(out));
})();
"""

    def test_the_page_asks_when_it_opens_and_again_after_a_call_that_failed(self):
        """Review defect 3, the page's side: the Launcher's own ui/app.js (as it is) run in Node, its calls stood in.
        Its start asks at once (a page opened again still tells the game it started: start() calls watchCrash(0)); a
        call that fails is asked again, up to a few in a row, and the notice then said; after a Play it asks a few
        seconds on, and stops when no game is watched. Skipped when no Node is found."""
        import re
        import shutil
        import subprocess
        import tomllib
        node = os.environ.get("RUSE_NODE") or shutil.which("node") or next(
            (str(p) for p in sorted(Path("D:/RUSE-2.0/tools").glob("node-v*/node.exe"))[::-1]), None)
        if not node or not Path(node).is_file():
            self.skipTest("no Node")
        ui = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher" / "ui"
        app = (ui / "app.js").read_text(encoding="utf-8")
        words = {k: v["us"] for k, v in tomllib.loads((ui.parent / "words.toml").read_text(encoding="utf-8")).items()
                 if k.startswith("crash_")}
        notice = {"why": "made", "unit": "Horse Squad", "added": True}
        cases = [{"call": "watchCrash(0)", "words": words,              # two calls fail, then the game is told
                  "answers": ["throw", "throw", {"watching": True, "notice": None},
                              {"watching": False, "notice": notice}]},
                 {"call": "watchCrash(0)", "words": words, "answers": ["throw"] * 9},   # failing on: it stops
                 {"call": "watchCrash()", "words": words, "answers": [{"watching": False, "notice": None}]}]
        (self.home / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
        ran = subprocess.run([node, "-e", self.PAGE_IN_NODE, "--", str(ui / "app.js"), str(self.home / "cases.json")],
                             capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(ran.returncode, 0, ran.stderr[-2000:])
        told, failing, after_play = json.loads(ran.stdout)
        said = words["crash_mod_unit"].replace("{unit}", "Horse Squad").replace("{why}", words["crash_why_made"])
        self.assertEqual((told["asks"], told["delays"][0], told["said"]), (4, 0, [[said, "bad"]]))
        tries = re.search(r"const CRASH_TRIES = (\d+)", app)
        self.assertEqual((failing["asks"], failing["said"]), (int(tries.group(1)) if tries else None, []))
        self.assertEqual(after_play, {"asks": 1, "delays": [3000], "said": []})   # (the control: after a Play)
        start = app[app.index("async function start()"):]
        self.assertTrue("watchCrash(0)" in start[:start.index("\n}\n")], "start() doesn't ask")   # when it opens

    def test_a_units_name_and_whether_a_mod_added_it(self):
        copy, game = self.home / "copy", self.home / "game"
        for folder in (copy, game):
            folder.mkdir(exist_ok=True)
            (folder / bugwatch.UNIT_DATA).write_bytes(b"x")
        units = {copy: {12: [("$/GFX/Everything/Descriptor_Unit_M3_Lee", "lee")],
                        4059: [("$/GFX/Everything/Descriptor_Unit_Horse_Squad", "horse")],
                        14: [("$/GFX/Everything/Descriptor_Unit_Nicks_Tank", "nick")],
                        13: [("Descriptor_Unit_A", "a"), ("Descriptor_Unit_B", "b")]},
                 game: {12: [("$/GFX/Everything/Descriptor_Unit_M3_Lee", "lee")],
                        14: [("$/GFX/Everything/Descriptor_Unit_Panther", "panther")]}}
        with mock.patch("rusemod.build.find_pack",
                        lambda folder, name: Path(folder) / name if (Path(folder) / name).is_file() else None), \
                mock.patch.object(bugwatch, "_units_in", lambda pack: units[Path(pack).parent]), \
                mock.patch.object(bugwatch, "_card_name", lambda _copy, obj, _lang: {"lee": "M3 LEE"}.get(obj)):
            self.assertEqual(bugwatch.unit_named(12, copy, game), {"name": "M3 LEE", "added": False})  # by its card
            self.assertEqual(bugwatch.unit_named(4059, copy, game), {"name": "Horse Squad", "added": True})
            self.assertEqual(bugwatch.unit_named(14, copy, game)["added"], True)   # the game's number, another unit
            self.assertIsNone(bugwatch.unit_named(13, copy, game))                # two units of one number: unsure
            self.assertIsNone(bugwatch.unit_named(99, copy, game))                # no such unit in the copy
            self.assertEqual(bugwatch.unit_named(12, copy, None)["added"], None)  # no install: not known
            self.assertIsNone(bugwatch.unit_named(12, self.home / "gone", game))  # no copy data
        with mock.patch.object(bugwatch, "_unit_named", side_effect=OSError("held")):
            self.assertIsNone(bugwatch.unit_named(12, copy, game))                # never raises

    @unittest.skipUnless(os.environ.get("RUSE_GAME") and Path(os.environ.get("RUSE_GAME", ""), "Data").is_dir(),
                         "needs the game (RUSE_GAME)")
    def test_a_game_units_name_from_the_games_own_data(self):
        game = Path(os.environ["RUSE_GAME"])
        from rusemod.build import DEFAULT_PACK, find_pack
        numbers = sorted(bugwatch._units_in(find_pack(game, DEFAULT_PACK)))
        self.assertEqual(bugwatch.UNIT_DATA, DEFAULT_PACK)
        for lang in ("us", "fr", "fa"):                           # (Persian: the game's English)
            named = bugwatch.unit_named(numbers[-1], game, game, lang)
            self.assertEqual(named["added"], False)
            self.assertTrue(named["name"].strip())


class Hooks(BugWatchTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._current = self.watch()

    def test_window_calls_and_jobs_are_counted(self):
        jobs = {}

        class Api:
            def good(self):
                return 1

            def bad(self):
                raise ValueError("no")

            def long(self):
                job = webui.Job()
                jobs["j"] = job
                return job.start(lambda say: say("x"), "done")

        page = webui.page_api(Api())
        self.assertEqual(page.good(), 1)
        with self.assertRaises(ValueError):
            page.bad()
        page.long()
        for _ in range(500):   # the job's own thread counts it right after its state changes: wait for the count
            with bugwatch._current.lock:   # all of one job's counts go in under the lock: read them whole, never half
                if "long" in bugwatch._current.days.get(bugwatch._today(), {}).get("jobs", {}):
                    break
            time.sleep(0.01)
        day = bugwatch._current.days[bugwatch._today()]
        self.assertEqual(day["calls"]["good"]["n"], 1)
        self.assertEqual(day["calls"]["bad"]["errors"], {"ValueError": 1})
        self.assertEqual(day["jobs"]["long"]["done"], 1)  # the job takes the name of the call that started it

    def test_its_own_calls_arent_counted(self):
        started = bugwatch.call_started("bugwatch_status")
        bugwatch.call_ended("bugwatch_status", started)
        self.assertNotIn("bugwatch_status", bugwatch._current.days.get(bugwatch._today(), {}).get("calls", {}))


class WhatTheAgreementSays(BugWatchTest):
    """What the agreement says of Bug Watch and RUSE Guard, made true (2026-11-24): Settings' "Save username" saves the
    name only; an untick deletes what the PC kept and nothing comes back, in either app; the agreement shown again
    shows Bug Watch as it is; the game's error text goes out through RUSE Guard's own cleaning; only the game's own
    crash reports are read. Each test fails on the release before (0.9.8.22) and passes since. The pages' own app.js
    and agreement.js run in Node as they are, their calls stood in (Save username's then made on Bug Watch itself);
    those two are skipped when no Node is found."""

    SRC = Path(__file__).resolve().parents[1] / "src"
    OTHER = "C:\\Program Files\\Paint\\paint.exe"   # another program, whose crash report can lie beside the game's

    SAVE_IN_NODE = r"""
const fs = require("fs"), vm = require("vm");
const [appFile, casesFile] = process.argv.slice(-2);
const anything = new Proxy(function () {}, { get: (t, k) => (k === Symbol.toPrimitive ? () => "" : anything),
  apply: () => anything, set: () => true });
class Observer { observe() {} unobserve() {} disconnect() {} }
class Input { get value() { return ""; } set value(v) {} }
const src = fs.readFileSync(appFile, "utf8");
const bound = /\$\("bugwatch-save"\)\.addEventListener\("click", ([^\r\n]+?)\);\r?\n/.exec(src);
(async () => {
  const out = [];
  for (const c of JSON.parse(fs.readFileSync(casesFile, "utf8"))) {
    const els = {}, calls = [];
    const element = (id) => els[id] || (els[id] = new Proxy({ id, value: "", checked: false, textContent: "",
      className: "", placeholder: "", classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
      addEventListener() {} }, { get: (t, k) => (k in t ? t[k] : anything) }));
    const document = new Proxy({ getElementById: element, activeElement: null },
      { get: (t, k) => (k in t ? t[k] : anything) });
    const api = new Proxy({}, { get: (t, name) => async (...args) => {
      calls.push([name, ...args]);
      return name === "bugwatch_status" ? c.before : {};
    } });
    const window = { addEventListener() {} };
    const ctx = vm.createContext({ console, document, localStorage: anything, location: { search: "" },
      navigator: anything, window, URLSearchParams,
      setTimeout: () => 0, clearTimeout: () => {}, setInterval: () => 0, clearInterval: () => {},
      ResizeObserver: Observer, MutationObserver: Observer, IntersectionObserver: Observer, HTMLInputElement: Input,
      HTMLElement: Input, requestAnimationFrame: () => 0, matchMedia: () => anything,
      getComputedStyle: () => anything });
    vm.runInContext(src, ctx, { filename: "app.js" });
    window.pywebview = { api };   // (after the page is read: it starts itself when the window's API is there)
    Object.assign(ctx, { WORDS: c.words, BUGWATCH: c.before });
    vm.runInContext("state.words = WORDS; state.bugwatch = BUGWATCH; state.settings = true;", ctx);
    element("bugwatch-name").value = c.typed;
    await vm.runInContext(`(${bound[1]})`, ctx)({ target: element("bugwatch-save") });
    out.push({ handler: bound[1], calls, note: element("bugwatch-note").textContent });
  }
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { process.stderr.write(String((e && e.stack) || e)); process.exit(1); });
"""

    AGREEMENT_IN_NODE = r"""
const fs = require("fs"), vm = require("vm");
const [file, casesFile] = process.argv.slice(-2);
const settle = () => new Promise((ok) => setImmediate(ok));
function element(id) {
  const on = {}, classes = new Set();
  return { id, value: "", checked: false, textContent: "", className: "", placeholder: "", disabled: false,
    childNodes: [], innerHTML: "", style: {},
    classList: { add: (k) => classes.add(k), remove: (k) => classes.delete(k), contains: (k) => classes.has(k),
      toggle: (k, f) => ((f === undefined ? !classes.has(k) : f) ? classes.add(k) : classes.delete(k)) },
    addEventListener: (t, fn) => { (on[t] = on[t] || []).push(fn); },
    removeEventListener: (t, fn) => { on[t] = (on[t] || []).filter((g) => g !== fn); },
    fire: (t) => { for (const fn of (on[t] || []).slice()) fn({ key: "", preventDefault() {} }); },
    listening: (t) => (on[t] || []).length, focus() {}, append() {}, appendChild() {} };
}
(async () => {
  const out = [];
  for (const c of JSON.parse(fs.readFileSync(casesFile, "utf8"))) {
    const els = {}, calls = [], answers = c.status.slice(), waiting = [];
    const document = { getElementById: (id) => els[id] || (els[id] = element(id)), createElement: () => element(""),
      head: element("head"), body: element("body") };
    const window = element("window");
    // c.late: the window's calls come back only when a step says, as a real window's can (late, in any order): each
    // bugwatch_status after the one the screen opens with, and guard_accept_terms
    const api = new Proxy({}, { get: (t, name) => async (...args) => {
      calls.push([name, ...args]);
      if (name === "guard_status") return c.guard;
      if (name === "bugwatch_status") {
        const answer = answers.length > 1 ? answers.shift() : answers[0];
        if (!c.late || calls.filter((x) => x[0] === name).length === 1) return answer;
        return new Promise((ok) => waiting.push({ name, ok: () => ok(answer) }));
      }
      if (name === "guard_accept_terms" && c.late)
        return new Promise((ok, no) => waiting.push({ name, ok: () => ok({}), no: () => no(new Error("refused")) }));
      return {};
    } });
    vm.runInContext(fs.readFileSync(file, "utf8"), vm.createContext({ window, document, console }),
                    { filename: "agreement.js" });
    const opened = window.Agreement.open({ api, words: c.words, fairOn: true });
    await settle();
    const $ = document.getElementById, box = $("agree-bugwatch");
    const seen = { at_open: box.checked, row_hidden: $("agree-bugwatch-row").classList.contains("agree-hidden"),
      label: $("agree-bugwatch-label").textContent, note: $("agree-bugwatch-note").textContent,
      listening: window.listening("focus"), clicks: [] };
    let labelAtAccept = null;
    const click = () => { seen.clicks.push(box.checked); labelAtAccept = $("agree-bugwatch-label").textContent;
      $("agree-accept").fire("click"); };
    const answer = (name, how) => {   // the oldest call of that name still out comes back (or the newest)
      const names = waiting.map((x) => x.name);
      const i = how === "newest" ? names.lastIndexOf(name) : names.indexOf(name);
      if (i >= 0) { const x = waiting.splice(i, 1)[0]; (how === "fails" ? x.no : x.ok)(); }
    };
    for (const step of c.steps) {
      if (step === "tick" || step === "untick") box.checked = step === "tick";
      else if (step === "click") click();                              // the player clicks Accept
      else if (step === "status") answer("bugwatch_status");
      else if (step === "newest status") answer("bugwatch_status", "newest");
      else if (step === "accept") answer("guard_accept_terms");
      else if (step === "accept fails") answer("guard_accept_terms", "fails");
      else window.fire(step);   // "focus": this window comes back
      await settle();
    }
    if (!seen.clicks.length) {
      seen.at_accept = box.checked;
      click();
      await settle();
    }
    while (waiting.length) { waiting.shift().ok(); await settle(); }   // whatever is still out comes back
    seen.at_end = box.checked;
    seen.label_at_accept = labelAtAccept;
    if (c.name !== undefined) {   // the username screen (no username yet)
      $("username-name").value = c.name;
      $("username-save").fire("click");
      await settle();
    }
    let timer;
    const finished = await Promise.race([opened.then(() => true),
      new Promise((ok) => { timer = setTimeout(ok, 3000, false); })]);
    clearTimeout(timer);
    out.push({ ...seen, calls, finished });
  }
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { process.stderr.write(String((e && e.stack) || e)); process.exit(1); });
"""

    @staticmethod
    def node() -> str | None:
        import shutil
        found = os.environ.get("RUSE_NODE") or shutil.which("node") or next(
            (str(p) for p in sorted(Path("D:/RUSE-2.0/tools").glob("node-v*/node.exe"))[::-1]), None)
        return found if found and Path(found).is_file() else None

    def run_node(self, script: str, file: Path, cases: list) -> list:
        import subprocess
        node = self.node()
        if node is None:
            self.skipTest("no Node")
        (self.home / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
        ran = subprocess.run([node, "-e", script, "--", str(file), str(self.home / "cases.json")],
                             capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(ran.returncode, 0, ran.stderr[-2000:])
        return json.loads(ran.stdout)

    def words(self, app: str, *starts: str) -> dict:
        import tomllib
        words = tomllib.loads((self.SRC / app / "words.toml").read_text(encoding="utf-8"))
        return {k: v["us"] for k, v in words.items() if k.startswith(starts)}

    def test_1_save_username_saves_the_name_only(self):
        """Settings' "Save username" in both apps, their own app.js and its handler as it is bound there: the name
        only, by set_username as the first start saves a name without Bug Watch, its calls then made on Bug Watch
        itself. Bug Watch is never switched by it: off stays off, on stays on under the new name; the same name keeps
        its #number; with no name at all nothing is saved. (Until 0.9.8.22 it called bugwatch_on: Bug Watch went on.)"""

        class Api(bugwatch.BugWatchCalls):
            UPDATE_APP, UPDATE_VERSION = "launcher", "0.4.8.22"

        for app in ("ruse_launcher", "ruse_studio"):
            words = self.words(app, "bugwatch_", "username_")
            cases, made = [], []
            for on, typed in ((False, "Ann"), (False, "Bob"), (True, "Bob"), (True, "Ann"), (False, "")):
                home = self.home / app / f"{'on' if on else 'off'}-{typed or 'none'}"
                home.mkdir(parents=True)
                if typed:
                    (bugwatch.turn_on if on else bugwatch.set_username)(home, "Ann")
                page = Api()
                page._home = str(home)
                before = page.bugwatch_status()
                cases.append({"words": words, "before": before, "typed": typed})
                made.append((home, before, typed))
            got = self.run_node(self.SAVE_IN_NODE, self.SRC / app / "ui" / "app.js", cases)
            for (home, before, typed), said in zip(made, got):
                page = Api()
                page._home = str(home)
                with mock.patch("atexit.register"), mock.patch.object(bugwatch, "_hook_errors"):
                    for name, *args in said["calls"]:
                        getattr(page, name)(*args)                  # the page's calls, made on Bug Watch itself
                after = page.bugwatch_status()
                called = [c[0] for c in said["calls"]]
                with self.subTest(app=app, on=before["on"], typed=typed, handler=said["handler"]):
                    self.assertNotIn("bugwatch_on", called)
                    self.assertNotIn("bugwatch_off", called)
                    self.assertEqual(after["on"], before["on"])                    # off stays off, on stays on
                    if not typed:
                        self.assertEqual((called, said["note"]), ([], words["username_need"]))
                        continue
                    keep = before["name"] if typed == "Ann" else typed
                    self.assertIn(["set_username", keep], said["calls"])
                    self.assertEqual(after["code"], before["code"])                # the same install
                    if typed == "Ann":
                        self.assertEqual(after["name"], before["name"])            # its #number kept
                    else:
                        self.assertRegex(after["name"], r"^Bob#\d{4}$")
                    self.assertNotEqual(said["note"], words["bugwatch_now_on"])

    def test_2_an_untick_deletes_what_was_kept_and_nothing_comes_back(self):
        """The agreement: "Untick it any time in Settings: nothing more is counted or sent, and what was kept is
        deleted." Both apps run on one PC: the Studio (this app, its Watch the module's own) and the Launcher (the
        other app, its own Watch, which an untick in the Studio can't reach), each with counts made and saved. Unticked
        in the Studio: nothing either counted before is written back (each app's save at its end: start's atexit),
        shown or queued to be sent, not even after the player ticks it again while the other app still runs; what is
        counted after the new tick still goes (the control); and what an older version wrote back after an untick is
        deleted at the next start while Bug Watch is off. (Until 0.9.8.22 each app's save at its end wrote its counts
        back, and they went out after a later tick.)"""
        bugwatch.turn_on(self.home, "Nick")
        name = homes.settings(self.home)["player"]["name"]
        values = homes.settings(self.home)
        values["guard"] = {"terms": 4}   # RUSE Guard accepted, as by every player: the ID and the username stay
        homes.save_settings(self.home, values)
        folder = self.home / bugwatch.FOLDER

        def kept():
            return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*.json")) if folder.is_dir() else []

        class Api(bugwatch.BugWatchCalls):
            _home = str(self.home)

        def both_run():
            """The Studio (this app) and the Launcher (the other app), each with counts made and saved."""
            studio, launcher = self.watch(), bugwatch.Watch(self.home, "launcher", "0.4.8.22", opener=Server())
            bugwatch._current = studio
            for w in (studio, launcher):
                for _ in range(3):
                    w.call("list_sets", 0.1)
                w.save()
            self.assertEqual(kept(), ["days-launcher.json", "days-studio.json"])
            return studio, launcher
        # unticked in the Studio's Settings; then each app ends (its save at its end), Bug Watch still off
        studio, launcher = both_run()
        Api().bugwatch_off()
        self.assertEqual((kept(), studio.days), ([], {}))        # deleted; the Studio's counts in memory gone at once
        studio.save()
        launcher.save()
        self.assertEqual(kept(), [])                             # nothing written back, by either
        # unticked, then ticked again while the Launcher runs on, never told: then it ends
        Api().bugwatch_on(name)
        studio, launcher = both_run()
        Api().bugwatch_off()
        Api().bugwatch_on(name)
        launcher.save()
        self.assertEqual(kept(), [])                             # its counts from before the untick: never written
        # the same, and the Launcher's Settings show what would be sent
        studio, launcher = both_run()
        Api().bugwatch_off()
        Api().bugwatch_on(name)
        bugwatch._current = launcher
        self.assertNotIn("calls", Api().bugwatch_next_send()["today"])   # none counted before the untick
        launcher.call("play", 0.1)                               # counted after the new tick (the control)
        launcher.save()
        studio.save()
        today = bugwatch._today()
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        with mock.patch.object(bugwatch, "_today", return_value=tomorrow):
            for app in ("studio", "launcher"):                   # the next day's starts: finished days queued
                bugwatch.Watch(self.home, app, "0.9.8.22", opener=Server()).roll()
        self.assertEqual(kept(), [f"outbox/day-launcher-{today}.json"])
        queued = json.loads((folder / "outbox" / f"day-launcher-{today}.json").read_text(encoding="utf-8"))
        self.assertEqual(list(queued["calls"]), ["play"])        # never list_sets, counted before the untick
        Api().bugwatch_off()
        folder.mkdir(parents=True, exist_ok=True)                # an older version's save at an app's end wrote it back
        (folder / "days-launcher.json").write_text(json.dumps({today: bugwatch._blank_day("0.4.8.22")}),
                                                   encoding="utf-8")
        with mock.patch("atexit.register"), mock.patch.object(bugwatch, "_hook_errors"):
            bugwatch.start(self.home, "launcher", "0.4.8.23")    # the next start, Bug Watch off
        self.assertEqual(kept(), [])

    def test_2_at_its_edges_an_untick_meanwhile_and_a_half_written_settings_file(self):
        """The same promise at its edges. An untick in the other app that lands while this app's save writes its file
        (after the save's look at the setting, before its write ends) deletes the file again. And a settings file the
        other app is writing that very moment (half written) is no untick (the control): nothing is counted then, and
        nothing kept is dropped: the counts are all there once it can be read again."""
        bugwatch.turn_on(self.home, "Nick")
        w = self.watch()
        w.call("list_sets", 0.1)
        on = homes.settings(self.home)
        off = {**on, "bugwatch": {**on["bugwatch"], "on": False, "untick_mark": "0" * 16}}
        looks = iter([on, off])                                  # the save's look before it writes, and after
        with mock.patch.object(bugwatch, "_settings_now", lambda home, tries=3: next(looks), create=True):
            w.save()
        self.assertFalse(w.file.exists())
        self.assertEqual(w.days, {})
        w = self.watch()
        for _ in range(2):
            w.call("list_sets", 0.1)
        settings = self.home / "settings.json"
        whole = settings.read_text(encoding="utf-8")
        settings.write_text(whole[:len(whole) // 2], encoding="utf-8")   # being written by the other app
        w.call("list_sets", 0.1)                                 # not counted then
        w.save()
        settings.write_text(whole, encoding="utf-8")
        w.call("list_sets", 0.1)
        self.assertEqual(w.days[bugwatch._today()]["calls"]["list_sets"]["n"], 3)

    def test_2_an_untick_in_the_other_app_still_on_0_9_8_22(self):
        """The Studio and the Launcher update one at a time, so the other app can still be 0.9.8.22 while this one
        runs. Its untick deletes the kept files, as every untick does, but leaves no new untick mark. This app's Watch,
        its days file there before (written by it, or read at its start) and gone now, takes that for the untick it is:
        what it counted before is never written back, not even after the player ticked it again there while this app
        counted nothing. What it counts after the tick is kept, and the other app's own file going with that app's own
        roll is no untick here (the controls). (8fd4340b, the first of these changes, wrote those counts back. The
        limits that stay until both apps are updated: Watch._now_on.)"""
        bugwatch.turn_on(self.home, "Nick")
        values = homes.settings(self.home)
        values["guard"] = {"terms": 4}   # RUSE Guard accepted, as by every player: the ID and the username stay
        homes.save_settings(self.home, values)
        folder, today = self.home / bugwatch.FOLDER, bugwatch._today()

        def untick_and_tick_in_0_9_8_22():   # its turn_off, turn_on (6b265ec1): "on" alone; the untick deletes the files
            for on in (False, True):
                values = homes.settings(self.home)
                values["bugwatch"] = {**(values.get("bugwatch") or {}), "on": on}
                homes.save_settings(self.home, values)
                for p in sorted(folder.rglob("*.json"), reverse=True) if not on else []:
                    p.unlink()

        def counted(w):
            return {day: sorted(c["calls"]) for day, c in json.loads(w.file.read_text(encoding="utf-8")).items()}
        launcher = bugwatch.Watch(self.home, "launcher", "0.4.8.23", opener=Server())
        for _ in range(3):
            launcher.call("list_sets", 0.1)
        launcher.save()                                          # its file written
        untick_and_tick_in_0_9_8_22()                            # in the other app, this one idle meanwhile
        launcher.save()                                          # this app's save at its end
        self.assertFalse(launcher.file.exists())                 # nothing counted before the untick written back
        launcher.call("play", 0.1)                               # counted after the tick (the control)
        launcher.save()
        self.assertEqual(counted(launcher), {today: ["play"]})
        restarted = bugwatch.Watch(self.home, "launcher", "0.4.8.23", opener=Server())   # its file read at its start
        untick_and_tick_in_0_9_8_22()
        restarted.call("list_sets", 0.1)
        restarted.save()
        self.assertEqual(counted(restarted), {today: ["list_sets"]})   # never "play", counted before that untick
        studio = self.watch()                                    # the Studio, this version too, its counts saved
        studio.call("list_sets", 0.1)
        studio.save()
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        restarted.file.write_text(json.dumps({yesterday: bugwatch._blank_day("0.4.8.23")}), encoding="utf-8")
        bugwatch.Watch(self.home, "launcher", "0.4.8.23", opener=Server()).roll()   # a finished day out: its file goes
        self.assertEqual(sorted(p.name for p in folder.rglob("*.json")),
                         [f"day-launcher-{yesterday}.json", "days-studio.json"])
        studio.call("list_sets", 0.1)
        studio.save()
        self.assertEqual(json.loads(studio.file.read_text(encoding="utf-8"))[today]["calls"]["list_sets"]["n"], 2)

    def test_3_the_agreement_shown_again_shows_bug_watch_as_it_is(self):
        """The agreement shown again (a version accepted before, a new one out), the shared agreement.js as it is: its
        Bug Watch box shows Bug Watch as it is, never ticked for a player who has it off, even when it was switched in
        the other app while the screen was up (both apps can run at once: when this window comes back, the box
        follows); a change the player made to the box here stays, and accepting changes Bug Watch only as the player
        changed the box. A new player's very first start is as it was (the control): the box starts unticked and the
        other app never moves it. (Until 0.9.8.22 the box kept what it showed when the screen opened.)"""
        words = self.words("ruse_launcher", "agree_", "username_", "bugwatch_", "set_bugwatch_")
        nick = {"available": True, "on": True, "name": "Nick#4821", "code": "abcdefgh"}
        off, new = {**nick, "on": False}, {"available": True, "on": False, "name": "", "code": ""}
        again, first = {"terms": 3, "terms_version": 4}, {"terms": 0, "terms_version": 4}
        cases = [{"guard": again, "status": [nick, off], "steps": ["focus"]},         # unticked in the other app
                 {"guard": again, "status": [off], "steps": []},                      # off: unticked from the start
                 {"guard": again, "status": [nick], "steps": ["untick", "focus"]},    # unticked here: it stays so
                 {"guard": again, "status": [off], "steps": ["tick", "focus"]},       # ticked here: it stays so
                 {"guard": again, "status": [off, nick], "steps": ["focus"]},         # ticked in the other app
                 {"guard": first, "status": [new, {**new, "on": True}], "steps": ["focus"], "name": "Ann"},
                 {"guard": first, "status": [new], "steps": ["tick"], "name": "Ann"}]
        for c in cases:
            c["words"] = words
        got = self.run_node(self.AGREEMENT_IN_NODE, self.SRC / "rusemod" / "sharedui" / "agreement.js", cases)
        self.assertEqual([g["finished"] for g in got], [True] * len(cases))   # every screen went away, done
        self.assertEqual([(g["at_open"], g["at_accept"]) for g in got],
                         [(True, False), (False, False), (True, False), (False, True), (False, True),
                          (False, False), (False, True)])
        made = [[c for c in g["calls"] if c[0] in ("bugwatch_on", "bugwatch_off", "set_username")] for g in got]
        self.assertEqual(made, [[], [], [["bugwatch_off"]], [["bugwatch_on", "Nick#4821"]], [],
                                [["set_username", "Ann"]], [["bugwatch_on", "Ann"]]])
        self.assertTrue(all(["guard_accept_terms"] in g["calls"] for g in got))
        first_start = got[5]
        self.assertEqual((first_start["row_hidden"], first_start["listening"], first_start["label"],
                          first_start["note"]), (False, 0, words["bugwatch_on_label"], words["set_bugwatch_help"]))

    def test_3_a_player_with_bug_watch_on_is_asked_to_keep_it(self):
        """The agreement shown again (decision 38 C, 2026-11-25), the shared agreement.js as it is: a player who has
        Bug Watch on is asked "Keep Bug Watch on?" (ticked; leaving it keeps it on and changes nothing; unticking it
        turns Bug Watch off exactly as Settings' untick does, one bugwatch_off); everyone else (off, or never chose)
        gets the Bug Watch box again, unticked, with "(Recommended)" (decision 10). If Bug Watch is switched off in the
        other app meanwhile, the box is the plain one again. A new player's first start is as it was (the control:
        unticked, the plain box). (Release 0.9.8.22 showed every player the plain box, even ticked.)"""
        words = self.words("ruse_launcher", "agree_", "username_", "bugwatch_", "set_bugwatch_")
        nick = {"available": True, "on": True, "name": "Nick#4821", "code": "abcdefgh"}
        off = {**nick, "on": False}
        never = {"available": True, "on": False, "name": "Nick#4821", "code": ""}
        new = {"available": True, "on": False, "name": "", "code": ""}
        again, first = {"terms": 3, "terms_version": 4}, {"terms": 0, "terms_version": 4}
        cases = [{"guard": again, "status": [nick], "steps": []},                    # on: asked, yes
                 {"guard": again, "status": [nick], "steps": ["untick"]},            # on: asked, no
                 {"guard": again, "status": [off], "steps": []},                     # off: the plain box
                 {"guard": again, "status": [never], "steps": []},                   # never chose: the plain box
                 {"guard": again, "status": [nick, off], "steps": ["focus"]},        # switched off meanwhile
                 {"guard": first, "status": [new], "steps": [], "name": "Ann"}]      # a new player
        for c in cases:
            c["words"] = words
        got = self.run_node(self.AGREEMENT_IN_NODE, self.SRC / "rusemod" / "sharedui" / "agreement.js", cases)
        self.assertEqual([g["finished"] for g in got], [True] * len(cases))
        keep, plain = words["bugwatch_keep_label"], words["bugwatch_on_label"]
        self.assertEqual(keep, "Keep Bug Watch on?")
        self.assertIn("(Recommended)", plain)
        self.assertEqual([g["label"] for g in got], [keep, keep, plain, plain, keep, plain])
        self.assertEqual([g["label_at_accept"] for g in got], [keep, keep, plain, plain, plain, plain])
        asked, help_ = words["bugwatch_keep_note"], words["set_bugwatch_help"]
        self.assertEqual([g["note"] for g in got], [asked, asked, help_, help_, asked, help_])   # as opened
        self.assertEqual([g["at_open"] for g in got], [True, True, False, False, True, False])
        self.assertEqual([g["at_end"] for g in got], [True, False, False, False, False, False])
        made = [[c for c in g["calls"] if c[0] in ("bugwatch_on", "bugwatch_off", "set_username")] for g in got]
        self.assertEqual(made, [[], [["bugwatch_off"]], [], [], [], [["set_username", "Ann"]]])

    def test_3_the_keep_question_is_in_every_language_in_both_apps(self):
        """The two new keys (bugwatch_keep_label, bugwatch_keep_note) are in both apps' words in all 11 languages."""
        import tomllib
        for app in ("ruse_launcher", "ruse_studio"):
            data = tomllib.loads((self.SRC / app / "words.toml").read_text(encoding="utf-8"))
            for key in ("bugwatch_keep_label", "bugwatch_keep_note"):
                self.assertEqual(sorted(data[key]), sorted(["us", "fr", "ger", "ita", "spa", "pol", "ru", "cz",
                                                            "jpn", "sc", "fa"]), f"{app} {key}")
                self.assertTrue(all(v.strip() for v in data[key].values()), f"{app} {key}")

    def test_3_an_answer_that_comes_back_late_never_switches_bug_watch(self):
        """The agreement shown again, the shared agreement.js as it is, with the window's calls coming back late and in
        the orders a real window can give them: the click that brings this window back lands on Accept while Bug
        Watch's state, asked as the window came back, is still out, and comes back before Accept's own answer.
        Accepting never switches Bug Watch the player didn't switch here: not on again after an untick in the other
        app, not off (deleting what was kept) after a tick there. An older answer never undoes a newer one, and after a
        refused Accept the box follows Bug Watch again. The player's own change here still goes, with an answer out
        (the controls). (8fd4340b, the first of these changes, switched Bug Watch in the first two; the release 0.9.8.22
        made none, its box never following: its switches here are these.)"""
        words = self.words("ruse_launcher", "agree_", "username_", "bugwatch_", "set_bugwatch_")
        nick = {"available": True, "on": True, "name": "Nick#4821", "code": "abcdefgh"}
        off = {**nick, "on": False}
        again = {"terms": 3, "terms_version": 4}

        def late(status, steps):
            return {"guard": again, "status": status, "steps": steps, "late": True, "words": words}
        cases = [late([nick, off], ["focus", "click", "status", "accept"]),   # unticked in the other app
                 late([off, nick], ["focus", "click", "status", "accept"]),   # ticked in the other app
                 late([nick, off], ["focus", "click", "accept", "status"]),   # Accept's answer first
                 late([nick, off], ["focus", "status", "click", "accept"]),   # the box followed, then Accept
                 late([nick, off, nick], ["focus", "focus", "newest status", "status", "click", "accept"]),
                 late([nick, off], ["click", "accept fails", "focus", "status", "click", "accept"]),
                 late([nick, nick], ["focus", "untick", "status", "click", "accept"]),   # unticked here (control)
                 late([off, off], ["focus", "tick", "status", "click", "accept"])]       # ticked here (control)
        got = self.run_node(self.AGREEMENT_IN_NODE, self.SRC / "rusemod" / "sharedui" / "agreement.js", cases)
        self.assertEqual([g["finished"] for g in got], [True] * len(cases))   # every screen went away, done
        made = [[c for c in g["calls"] if c[0] in ("bugwatch_on", "bugwatch_off")] for g in got]
        self.assertEqual(made, [[], [], [], [], [], [], [["bugwatch_off"]], [["bugwatch_on", "Nick#4821"]]])
        # the box as the player clicked Accept: following Bug Watch where it had come back by then (the 4th, the
        # newer answer of the 5th, the 2nd Accept of the 6th); the player's own change (the 7th and 8th)
        self.assertEqual([g["clicks"] for g in got],
                         [[True], [False], [True], [False], [True], [True, False], [False], [True]])
        self.assertEqual([len([c for c in g["calls"] if c[0] == "guard_accept_terms"]) for g in got],
                         [1, 1, 1, 1, 1, 2, 1, 1])

    def test_4_the_games_error_text_goes_out_through_ruse_guards_cleaning(self):
        """The game's error text a game crash report sends (read_dump's traceback) goes through RUSE Guard's own
        cleaning of its line, the very function (guard.no_ids): no Steam ID, long number or path, as the agreement says
        ("Never sent: ... your Steam account, your files or paths"; RUSE Guard's line goes "with any Steam ID, long
        number or path removed"). What our developers need stays (the control): the game's own script names, the lines,
        the error. (Until 0.9.8.22 only paths were cut from it.)"""
        from rusemod import guard
        bugwatch.turn_on(self.home, "Nick")
        text = (b'Traceback (most recent call last):\n  File "DataDir:\\x\\menu.py", line 40, in f\n'
                b'  File "datadir:\\codeia\\python\\eugen\\game\\world.py", line 114, in on_timer_task\n'
                b"KeyError: 'player 76561198012345678 at C:\\Games\\x.py, account 226593310'\x00")
        p = self.home / "report.dmp"
        p.write_bytes(Crashes.dump(self, extra=b"\0junk\0" + text))
        found = bugwatch.read_dump(p)
        for secret in ("76561198012345678", "226593310", "C:\\"):
            self.assertNotIn(secret, found["traceback"])
        self.assertEqual(found["traceback"], 'Traceback (most recent call last):\n'
                                             '  File "DataDir:\\x\\menu.py", line 40, in f\n'
                                             '  File "datadir:\\codeia\\python\\eugen\\game\\world.py", line 114, in '
                                             'on_timer_task\n'
                                             "KeyError: 'player <id> at x.py, account <n>'")
        with mock.patch.object(guard, "no_ids", wraps=guard.no_ids) as cleaning:
            bugwatch.read_dump(p)
        cleaning.assert_called()                                 # RUSE Guard's own cleaning, not a copy of it
        w = self.watch()
        w.game_crash(found, [], 0, send=False)
        (sent,) = [json.loads(f.read_text()) for f in w.outbox.glob("crash-*.json")]
        self.assertEqual(sent["traceback"], found["traceback"])
        self.assertTrue(is_clean(sent))

    def test_4_a_path_with_spaces_doubled_backslashes_or_on_a_network_goes_too(self):
        """The same error text with the paths a real one can hold, the player's Windows account "Nick Smith": Python
        prints a path's \\ doubled, a folder can have a space in its name (the player's own, Program Files (x86),
        another account's), and a file can be on a network. None of the path goes out but its file's name, and the
        player's own folders as Windows names them for anyone; the game's own script names, the error and its file
        names stay (the controls). (Until these fixes a space or a network path let the rest of it through, names and
        all.)"""
        bugwatch.turn_on(self.home, "Nick")
        head = b'Traceback (most recent call last):\n  File "DataDir:\\x\\menu.py", line 40, in f\n'
        cases = {b"IOError: [Errno 2] No such file or directory: 'C:\\\\Users\\\\Nick Smith\\\\Documents\\\\My Games"
                 b"\\\\x.sav'": "IOError: [Errno 2] No such file or directory: '%USERPROFILE%\\\\Documents\\\\My Games"
                                "\\\\x.sav'",
                 b"IOError: no file C:\\Users\\Nick Smith\\Documents\\My Games\\x.sav here":
                     "IOError: no file %USERPROFILE%\\Documents\\My Games\\x.sav here",
                 b"IOError: no file C:/Users/Nick Smith/Documents/x.sav here":
                     "IOError: no file %USERPROFILE%/Documents/x.sav here",
                 b"IOError: no file C:\\Program Files (x86)\\Steam\\steamapps\\common\\R.U.S.E\\Nick\\x.sav here":
                     "IOError: no file x.sav here",
                 b"IOError: [Errno 2] No such file or directory: 'C:\\\\Program Files (x86)\\\\Steam\\\\R.U.S.E"
                 b"\\\\Nick\\\\my save.sav'": "IOError: [Errno 2] No such file or directory: 'my save.sav'",
                 b"IOError: no file \\\\nas\\Nick\\games\\x.sav here": "IOError: no file x.sav here",
                 b"IOError: [Errno 2] No such file or directory: '\\\\\\\\nas\\\\Nick\\\\x.sav'":
                     "IOError: [Errno 2] No such file or directory: 'x.sav'",
                 b"IOError: no file E:\\Users\\Ann Lee\\x.sav and D:/Users/bob/y":
                     "IOError: no file %USERPROFILE%\\x.sav and %USERPROFILE%/y",
                 b"IOError: [Errno 13] Permission denied: 'C:\\\\Users\\\\Ann Lee'":
                     "IOError: [Errno 13] Permission denied: '%USERPROFILE%'",
                 b"IOError: no file \\Users\\Nick Smith\\x.sav here":           # from the drive's root
                     "IOError: no file %USERPROFILE%\\x.sav here",
                 b"IOError: no file Z:\\home\\nick\\games\\x.sav or Z:\\home\\nick":   # Linux's home, as Wine shows it
                     "IOError: no file %USERPROFILE%\\games\\x.sav or %USERPROFILE%"}
        account = {"USERPROFILE": "C:\\Users\\Nick Smith", "LOCALAPPDATA": "C:\\Users\\Nick Smith\\AppData\\Local",
                   "APPDATA": "C:\\Users\\Nick Smith\\AppData\\Roaming"}
        p = self.home / "report.dmp"
        with mock.patch.dict(os.environ, account), mock.patch("rusemod.community._documents", return_value=None):
            for line, said in cases.items():
                p.write_bytes(Crashes.dump(self, extra=b"\0junk\0" + head + line + b"\x00"))
                found = bugwatch.read_dump(p)
                with self.subTest(line=line):
                    self.assertEqual(found["traceback"], head.decode() + said)
                    for private in ("Nick", "nick", "Smith", "Ann", "Lee", "bob", "nas", "Program Files", "Steam"):
                        self.assertNotIn(private, found["traceback"])
                    w = self.watch()
                    w.game_crash(found, [], 0, send=False)
                    self.assertTrue(all(is_clean(json.loads(f.read_text())) for f in w.outbox.glob("crash-*.json")))

class TheCardInBothApps(unittest.TestCase):
    """The Bug Watch Settings card is in the Launcher AND the Studio, with the same words in all ten languages and the
    same controls and app.js wiring. Guards the Studio mirror against drifting from the Launcher (card added 2026-10-30)."""

    SRC = Path(__file__).resolve().parents[1] / "src"
    LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")
    KEYS = ("set_bugwatch_title", "set_bugwatch_help", "bugwatch_on_label", "bugwatch_name_hint", "bugwatch_save",
            "bugwatch_code", "bugwatch_show", "bugwatch_need_name", "bugwatch_now_on", "bugwatch_now_off",
            "tip_bugwatch_on", "tip_bugwatch_name", "tip_bugwatch_save", "tip_bugwatch_show")
    IDS = ("set-bugwatch", "bugwatch-name", "bugwatch-save", "bugwatch-on", "bugwatch-on-label", "bugwatch-code",
           "bugwatch-show", "bugwatch-sent", "bugwatch-note")
    FUNCS = ("loadBugwatch", "renderBugwatch", "changeBugwatch", "showBugwatch")

    def _words(self, app):
        import tomllib
        return tomllib.load(open(self.SRC / app / "words.toml", "rb"))

    def test_both_apps_have_every_word_in_every_language(self):
        for app in ("ruse_launcher", "ruse_studio"):
            words = self._words(app)
            for key in self.KEYS:
                self.assertIn(key, words, f"{app}: {key} missing")
                self.assertEqual([lang for lang in self.LANGS if not words[key].get(lang)], [],
                                 f"{app}: {key} missing a language")

    def test_both_apps_have_the_controls_and_wiring(self):
        for app in ("ruse_launcher", "ruse_studio"):
            html = (self.SRC / app / "ui" / "index.html").read_text(encoding="utf-8")
            for name in self.IDS:
                self.assertIn(f'id="{name}"', html, f"{app}: {name} not in index.html")
            js = (self.SRC / app / "ui" / "app.js").read_text(encoding="utf-8")
            for func in self.FUNCS:
                self.assertIn(func, js, f"{app}: {func} not in app.js")
            self.assertIn('{ id: "bugwatch"', js, f"{app}: the bugwatch Settings entry is missing")


class TheAgreementScreen(unittest.TestCase):
    """The first-start agreement + username is ONE shared screen (rusemod/sharedui/agreement.js) that both apps load
    and the web layer serves at shared/ (plan §3a; built then made shared 2026-10-30). Both apps call it at startup,
    carry its words, and expose the guard calls it needs (rusemod.guardcalls.GuardCalls)."""

    SRC = Path(__file__).resolve().parents[1] / "src"
    KEYS = ("agree_title", "agree_intro", "agree_guard_title", "agree_guard",
            "agree_full_toggle", "agree_full", "agree_accept_note", "agree_accept", "username_title", "username_help",
            "username_save", "username_need")
    IDS = ("agree", "agree-bugwatch", "agree-bugwatch-row", "agree-full", "agree-accept",
           "username", "username-name", "username-save")

    def test_one_shared_module_has_the_screen_and_flow(self):
        js = (self.SRC / "rusemod" / "sharedui" / "agreement.js").read_text(encoding="utf-8")
        for name in self.IDS:
            self.assertIn(f'id="{name}"', js, f"{name} not injected by the shared module")
        self.assertIn("window.Agreement", js)
        for call in ("guard_status", "guard_accept_terms", "set_username", "bugwatch_on"):
            self.assertIn(call, js, f"{call} not wired in the shared module")
        # the program check is mandatory, part of RUSE Guard -- not a choice: no scan checkbox, no guard_set_scan call
        self.assertNotIn("agree-scan", js)
        self.assertNotIn("guard_set_scan", js)

    def test_both_apps_load_and_call_the_one_module(self):
        for app in ("ruse_launcher", "ruse_studio"):
            html = (self.SRC / app / "ui" / "index.html").read_text(encoding="utf-8")
            self.assertIn('src="shared/agreement.js"', html, f"{app} doesn't load the shared module")
            js = (self.SRC / app / "ui" / "app.js").read_text(encoding="utf-8")
            self.assertIn("window.Agreement.open", js, f"{app} doesn't call the shared agreement")

    def test_both_apps_have_the_words(self):
        import tomllib
        for app in ("ruse_launcher", "ruse_studio"):
            words = tomllib.load(open(self.SRC / app / "words.toml", "rb"))
            for key in self.KEYS:
                self.assertIn(key, words, f"{app}: {key} missing")
                self.assertTrue(words[key].get("us"), f"{app}: {key} has no English")

    def test_version_5_of_the_agreement(self):
        """The agreement's version 5 (2026-11-26, the terms of use and privacy notice): the apps show it again
        (TERMS_VERSION); Bug Watch's version 4 fields, which wait for version 4 or later (AGREEMENT_V4), still go under
        it, and its text, the same in both apps, says what they are in every language."""
        import tomllib
        from rusemod import guard
        self.assertEqual(guard.TERMS_VERSION, 5)
        self.assertLessEqual(bugwatch.AGREEMENT_V4, guard.TERMS_VERSION)
        texts = [tomllib.loads((self.SRC / app / "words.toml").read_text(encoding="utf-8"))["agree_full"]
                 for app in ("ruse_launcher", "ruse_studio")]
        self.assertEqual(texts[0], texts[1])
        english = texts[0]["us"]
        for said in ("Version 5, ", "how many mods of your own you had, and what kinds of things they hold",
                     "the map (one of the game's own maps by its name", "the unit the game was making",
                     "which version of these terms you accepted", "never named, and never their words, paths or files"):
            self.assertIn(said, english)
        self.assertNotIn("how many of our own mods", english)   # (version 3's slip: it meant the player's own)
        for lang, text in texts[0].items():
            lines = text.split("\n")
            self.assertEqual(len(lines), len(english.split("\n")), lang)
            self.assertRegex(lines[1], r"5|۵", lang)

    def test_a_new_version_keeps_the_username_and_says_what_is_on(self):
        """Shown a new version, a player who has a username keeps it (asked again, a new #number would replace it);
        the Bug Watch tick starts as Bug Watch is (and follows it while the screen is up: WhatTheAgreementSays), and
        accepting with it changed turns Bug Watch on or off."""
        js = (self.SRC / "rusemod" / "sharedui" / "agreement.js").read_text(encoding="utf-8")
        self.assertIn("let shown = Boolean(status.available && status.on);", js)
        self.assertIn("box.checked = shown;", js)
        self.assertIn("const bw = status.available && box.checked, was = shown;", js)
        kept = js[js.index("if (status.name) {"):js.index("await askUsername(api, words, bw);")]
        self.assertIn("if (bw && !was) await api.bugwatch_on(status.name);", kept)
        self.assertIn("else if (!bw && was) await api.bugwatch_off();", kept)
        self.assertIn("name: String(got.name || \"\")", js)

    def test_the_web_layer_serves_it_and_both_apis_have_the_guard_calls(self):
        webui = (self.SRC / "rusemod" / "webui.py").read_text(encoding="utf-8")
        self.assertIn('"shared": SHARED_UI', webui, "webui doesn't mount shared/")
        # the mount must be on BOTH paths: the window (serve) AND the web browser (_in_browser), or --browser 404s
        # shared/agreement.js and the agreement never shows there
        browser_body = webui.split("def _in_browser", 1)[-1].split("\ndef ", 1)[0]
        self.assertIn('"shared": SHARED_UI', browser_body, "the --browser path (_in_browser) doesn't mount shared/")
        for app in ("ruse_launcher", "ruse_studio"):
            api = (self.SRC / app / "api.py").read_text(encoding="utf-8")
            self.assertIn("GuardCalls", api, f"{app} api doesn't include GuardCalls")


if __name__ == "__main__":
    unittest.main()
