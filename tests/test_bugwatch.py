"""Bug Watch (rusemod.bugwatch): opt-in counts, what's sent and when, crashes. No network: the sends go to a fake.

Checked our_tools.json: none of its tools reads a crash report; these tests read nothing of the game, only a small
crash report file they make themselves (one module named like the game).
"""
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

from rusemod import bugwatch, home as homes, webui  # noqa: E402


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

    def dump(self, code=0x29A, address=0x7FF612341234, base=0x7FF612340000, extra=b""):
        """A small crash report file: the header, an ExceptionStream, a ModuleListStream with one module, and `extra`."""
        name = "C:\\Games\\R.U.S.E\\RUSE.exe".encode("utf-16-le")
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
        # the older layout (no registers, no thread list) still reads as before
        p.write_bytes(self.dump(code=0xC0000005))
        self.assertEqual(sorted(bugwatch.read_dump(p, self.exe())), ["code", "module", "offset"])

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
        w.game_crash(found, ["cool-mod@1.2"], 0, send=False, holds=holds)   # no own mod on: nothing about them
        newest = max(w.outbox.glob("crash-*.json"), key=lambda f: f.name)
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
    """Item 25 (the owner, 2026-11-13: "if their unit was crashing the game, they should be told that" and "they
    should also be told why that unit made the game crash"): a crash at a place rusemod.crashplaces knows gets its
    plain reason, and under version 4 of the agreement the unit the game was making, read from the crash report the
    way the held reports keep it (the creating step's caller holds the unit's description); the unit goes out only as
    version 4 says ("one of the game's own units by its number; a unit a mod added only as "a mod's unit""), the
    reason and the unit's name never. Made-up reports and program files only: every number of the program is the
    table's own (crashplaces), none is written here."""

    BASE = Crashes.BASE
    UNIT, OTHER = 0x16145E50, 0x26145E50   # where the made-up reports keep units' descriptions

    def setUp(self):
        super().setUp()
        from rusemod import crashplaces
        self.places = crashplaces
        self.made = next(at for at, (key, _needs) in crashplaces.PLACES.items() if key == "made")
        self.create = crashplaces.CREATING[0] + 0x40    # a place right after a call in the unit-creation step
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
        """The memory a report keeps round a unit's description (from 256 bytes before it): its kind's table first,
        its number where the game keeps it."""
        blob = bytearray(0x400)
        kind = min(self.places.UNIT_CLASSES) if kind is None else kind
        struct.pack_into("<Q", blob, 0x100, self.BASE + kind)
        struct.pack_into("<I", blob, 0x100 + self.places.UNIT_NUMBER, number)
        return ((at or self.UNIT) - 0x100, bytes(blob))

    def report(self, words=(), kept=(), place=None, build=None, below=()) -> Path:
        p = self.home / "report.dmp"
        p.write_bytes(Crashes.dump_with_stack(self, list(below), list(words), place=self.made if place is None else place,
                                              build=build or self.places.BUILD, kept=list(kept)))
        return p

    def test_a_crash_we_know_says_why_and_which_unit(self):
        program = self.program([self.create])
        p = self.report([0x1234, self.BASE + self.create, 0, self.UNIT, self.UNIT], [self.description(4059)])
        found = bugwatch.read_dump(p, program, unit=True)
        self.assertEqual((found["reason"], found["unit"]), ("made", 4059))
        asked = bugwatch.read_dump(p, program)                    # the unit only when asked (version 4: GameWatch)
        self.assertEqual((asked["reason"], "unit" in asked), ("made", False))
        alone = bugwatch.read_dump(p, unit=True)                  # no copy's program: no chain, so no unit; the place
        self.assertEqual((alone["reason"], "unit" in alone), ("made", False))   # alone still says why
        build = self.places.BUILD
        big = (build[0] + 0x1000,) + build[1:]                    # a copy with the big-packs game patch: a page longer
        found = bugwatch.read_dump(self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)],
                                               build=big), program, unit=True)
        self.assertEqual((found["reason"], found["unit"]), ("made", 4059))
        self.assertEqual(self.places.BUILDS, {build, big})        # those two only

    def test_no_reason_or_unit_where_it_cant_be_sure(self):
        program = self.program([self.create])
        making, one = [0, self.BASE + self.create, self.UNIT], [self.description(4059)]
        other_build = self.places.BUILD[:2] + (self.places.BUILD[2] + 1,)
        longer = (self.places.BUILD[0] + 0x2000,) + self.places.BUILD[1:]
        for place, build in ((0x4321, None), (self.made, other_build), (self.made, longer)):
            # a place we don't know, or another build of the program (its places may be other code): nothing
            found = bugwatch.read_dump(self.report(making, one, place=place, build=build), program, unit=True)
            self.assertEqual((found.get("reason"), found.get("unit")), (None, None))
            self.assertEqual(found["code"], "0xc0000005")         # the rest is read as before
        two = bugwatch.read_dump(self.report(making + [self.OTHER], one + [self.description(4404, self.OTHER)]),
                                 program, unit=True)              # two different units: none said
        self.assertEqual((two["reason"], two.get("unit")), ("made", None))
        for words in ([self.UNIT, self.BASE + self.create, 0],   # only below the creating step's return (deeper)
                      [0, self.UNIT]):                           # no return into the creating step at all
            self.assertIsNone(bugwatch.read_dump(self.report(words, one), program, unit=True).get("unit"))
        not_a_unit = [self.description(4059, kind=0x1234)]       # something else than a unit's description there
        self.assertIsNone(bugwatch.read_dump(self.report(making, not_a_unit), program, unit=True).get("unit"))
        nested = [0, self.BASE + self.create, self.UNIT, self.BASE + self.create, self.OTHER]  # an outer creation's
        found = bugwatch.read_dump(self.report(nested, one + [self.description(4404, self.OTHER)]), program, unit=True)
        self.assertEqual(found["unit"], 4059)                     # unit beyond the next return isn't read
        with mock.patch.object(bugwatch, "_kept_memory", side_effect=struct.error("cut short")):
            found = bugwatch.read_dump(self.report(making, one), program, unit=True)
        self.assertEqual((found["reason"], found.get("unit")), ("made", None))   # the report itself is still read

    def test_the_name_search_place_counts_only_with_a_turret_in_its_chain(self):
        search = next(at for at, (_key, needs) in self.places.PLACES.items() if needs)
        part, turret = self.places.PART_BY_NAME[0] + 0x40, self.places.TWO_AXIS[0][0] + 0x40
        program = self.program([part, turret])
        both = [self.BASE + part, self.BASE + turret]
        self.assertEqual(bugwatch.read_dump(self.report(both, place=search), program)["reason"], "turret")
        for words in (both[:1], both[1:], []):
            self.assertNotIn("reason", bugwatch.read_dump(self.report(words, place=search), program))
        self.assertNotIn("reason", bugwatch.read_dump(self.report(both, place=search)))  # no program, no chain

    def test_every_reason_has_its_words_in_every_language(self):
        import re
        import tomllib
        from rusemod import schema
        self.assertEqual({key for key, _needs in self.places.PLACES.values()}, set(self.places.REASONS))
        root = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher"
        words = tomllib.loads((root / "words.toml").read_text(encoding="utf-8"))
        for key in [f"crash_why_{r}" for r in self.places.REASONS] + ["crash_unit", "crash_mod_unit", "crash_no_unit"]:
            self.assertEqual(sorted(words[key]), sorted(schema.APP_LANGS), key)
            blanks = {tuple(sorted(re.findall(r"\{(\w+)\}", text))) for text in words[key].values()}
            self.assertEqual(len(blanks), 1, key)                 # the same {blanks} in every language
        app = (root / "ui" / "app.js").read_text(encoding="utf-8")
        self.assertIn("api().bugwatch_crash()", app)              # the page asks after a Play, and says it
        self.assertIn('if (j.state === "done") watchCrash();', app)
        self.assertIn("bugwatch_crash:", (root / "ui" / "fake-api.js").read_text(encoding="utf-8"))

    def run_game(self, report: bytes, named, program):
        """A game the app started that closed leaving `report`: what went out, what the window is told, and the
        stand-in that named the unit (`named`: unit_named's answer)."""
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

        g = bugwatch.GameWatch(w, Game(), [], 1, sleep=sleep, clock=lambda: next(times), local=str(local),
                               exe=program, game=self.home / "game")
        with mock.patch.object(w, "send_waiting"), mock.patch.object(bugwatch, "unit_named",
                                                                     return_value=named) as naming:
            g.run()
        files = list(w.outbox.glob("crash-*.json"))
        (sent,) = [json.loads(f.read_text()) for f in files]
        for f in files:
            f.unlink()
        return sent, bugwatch.crash_notice(), naming

    def test_the_game_watch_tells_the_player_and_sends_the_unit_as_version_4_says(self):
        program = self.program([self.create])
        report = self.report([0, self.BASE + self.create, self.UNIT], [self.description(4059)]).read_bytes()
        horse = {"name": "Horse Squad", "added": True}
        self.accept(3)                                            # version 3: why only; no unit read, named or sent
        sent, told, naming = self.run_game(report, horse, program)
        self.assertEqual(told, {"watching": False, "notice": {"why": "made", "unit": None, "added": False}})
        naming.assert_not_called()
        self.assertNotIn("unit", sent)
        self.accept(4)                                            # a mod's unit: named for the player, sent as added
        sent, told, naming = self.run_game(report, horse, program)
        self.assertEqual(told["notice"], {"why": "made", "unit": "Horse Squad", "added": True})
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

    def test_version_4_of_the_agreement(self):
        """The agreement's version 4 (2026-11-13): the apps show it again (TERMS_VERSION), Bug Watch's version 4 fields
        wait for it (AGREEMENT_V4), and its text, the same in both apps, says what they are in every language."""
        import tomllib
        from rusemod import guard
        self.assertEqual(guard.TERMS_VERSION, 4)
        self.assertEqual(bugwatch.AGREEMENT_V4, guard.TERMS_VERSION)
        texts = [tomllib.loads((self.SRC / app / "words.toml").read_text(encoding="utf-8"))["agree_full"]
                 for app in ("ruse_launcher", "ruse_studio")]
        self.assertEqual(texts[0], texts[1])
        english = texts[0]["us"]
        for said in ("Version 4, ", "how many mods of your own you had and what kinds of things they hold",
                     "the map it was on", "the game mode", "the unit the game was making",
                     "which version of this agreement you accepted", "or the names and words of your own mods"):
            self.assertIn(said, english)
        self.assertNotIn("how many of our own mods", english)   # (version 3's slip: it meant the player's own)
        for lang, text in texts[0].items():
            lines = text.split("\n")
            self.assertEqual(len(lines), len(english.split("\n")), lang)
            self.assertRegex(lines[1], r"4|۴", lang)

    def test_a_new_version_keeps_the_username_and_says_what_is_on(self):
        """Shown a new version, a player who has a username keeps it (asked again, a new #number would replace it);
        the Bug Watch tick starts as Bug Watch is, and accepting with it changed turns Bug Watch on or off."""
        js = (self.SRC / "rusemod" / "sharedui" / "agreement.js").read_text(encoding="utf-8")
        self.assertIn('$("agree-bugwatch").checked = Boolean(status.available && status.on);', js)
        kept = js[js.index("if (status.name) {"):js.index("await askUsername(api, words, bw);")]
        self.assertIn("if (bw && !status.on) await api.bugwatch_on(status.name);", kept)
        self.assertIn("else if (!bw && status.on) await api.bugwatch_off();", kept)
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
