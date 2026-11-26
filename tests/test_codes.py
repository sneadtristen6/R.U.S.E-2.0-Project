"""Proper codes for Bug Watch (the owner's ask of 2026-11-24, "our studio and launcher should be giving us proper code so
that the bug watch is super effective", and his answers of 2026-11-26, B6 B to B11 B: rusemod.codes, rusemod.bugwatch).

The one list of codes is the code's (codes.toml in step with it, a number never given twice); a day's send lists each
failure the player met by its code, with how far it got, its set's shape and numbers only, and only under the
agreement version that describes it (one constant), the old keys beside it as before; FL-97's refusals each by their
own code (the two pairs one key each had, the set file not written with its Windows number, the set saved and the lists
then failing); a Play's and a Test in game's steps; the build's checks whose keys hid the cause (load_mod's, the load
order's, the patch engine's), each its own BLD code; what sent nothing (the mod list, the update check, sign-in
answers, a game that ended badly with its exit number, an unreadable crash report); the Studio's crash notice after a
test (B9 A), its player-entry refusals sending nothing (B10 A), its page's own script errors and a game it was closed
under (B11 B). Nothing that names a player in any of it.

No network, no game: made-up homes, stand-in servers and processes; the pages' functions run in Node when there is one.
"""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import ast
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import bugwatch, codes, webui  # noqa: E402
from rusemod import home as homes  # noqa: E402
from rusemod.build import BuildError, load_mod  # noqa: E402
from rusemod.codes import code_of, coded  # noqa: E402
from test_checkkeys import SECRET, entry, folders  # noqa: E402

SRC = Path(__file__).resolve().parents[1] / "src"
SERVER_CODE = re.compile(r"^(?:[LSR]-)?[A-Z]{2,6}-[0-9]{1,4}$")  # Bug Watch 1.4.0's worker.js FAILURE_CODE_RE
MOD = '[mod]\nid = "{id}"\nname = "{id}"\nversion = "1.0.0"\n'


def node() -> str | None:
    found = os.environ.get("RUSE_NODE") or shutil.which("node") or next(
        (str(p) for p in sorted(Path("D:/RUSE-2.0/tools").glob("node-v*/node.exe"))[::-1]), None)
    return found if found and Path(found).is_file() else None


class WithBugWatch(unittest.TestCase):
    """A player who ticked Bug Watch and accepted the agreement version that describes the codes (5 by default)."""
    APP, AGREEMENT = "launcher", 5

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TEMP"))
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self._on = bugwatch.ON
        bugwatch.ON = True
        os.environ.pop("RUSE_NO_BUGWATCH", None)
        bugwatch.turn_on(self.home, "Nick")
        self.agree(self.AGREEMENT)
        bugwatch._current = bugwatch.Watch(self.home, self.APP, "0.4.8.23", opener=mock.Mock())

    def tearDown(self):
        bugwatch.ON = self._on
        bugwatch._current = None
        self.tmp.cleanup()

    def agree(self, version: int) -> None:
        homes.save_settings(self.home, {**homes.settings(self.home), "guard": {"terms": version}})

    def day(self) -> dict:
        return bugwatch._current.days.get(bugwatch._today(), {})

    def failures(self) -> list:
        return self.day().get("failures", [])

    def codes(self) -> list:
        return [f["code"] for f in self.failures()]

    def sent(self) -> dict:
        return bugwatch._current.payload(bugwatch._today(), self.day())


# --- the one list, and the code in step with it -------------------------------------------------------------------
class TheList(unittest.TestCase):
    def test_the_file_says_what_the_code_says(self):
        self.assertEqual(codes.stale(), [], "run rusemod.codes.write() and give a code by hand its entry")

    def test_every_code_is_one_the_server_takes_and_no_place_is_a_line(self):
        entries = codes.read()
        self.assertGreater(len(entries), 400)
        for code, e in entries.items():
            with self.subTest(code):
                for app in ("launcher", "studio"):
                    self.assertRegex(codes.wire(code, app), SERVER_CODE)
                self.assertRegex(e["place"], r"^[A-Za-z0-9_.<>]+$")           # a module and a function, never a line
                self.assertNotIn(":", e["place"])
        self.assertEqual((codes.wire("SET-08", "launcher"), codes.wire("PLAY-08", "studio"),
                          codes.wire("BLD-046", "studio"), codes.wire("nonsense", "studio")),
                         ("L-SET-08", "S-PLAY-08", "BLD-046", ""))

    def test_every_build_check_has_its_code_and_the_old_key_stays_with_it(self):
        check = entry(words="has no mod.toml")["check"]
        code = codes.bld_of(check)
        self.assertRegex(code, r"^BLD-\d{3}$")
        self.assertEqual(codes.read()[code]["check"], check)
        self.assertEqual(codes.bld_of("studio.test.game-not-found"), "")  # (the apps' own steps: PLAY and TST codes)

    def test_a_number_once_given_stays_and_is_never_given_twice(self):
        """write(): a build check keeps its code; a new one gets the next number nobody had; a code whose check is gone
        stays, marked gone, its number never given again."""
        checks = codes._build_checks()
        first = next(iter(checks))
        with tempfile.TemporaryDirectory(dir=os.environ.get("TEMP")) as tmp:
            path = Path(tmp) / "codes.toml"
            path.write_text(f'[BLD-001]\nplace = "{checks[first]}"\ncheck = "{first}"\nsince = "1"\n\n'
                            f'[BLD-007]\nplace = "build.gone"\ncheck = "build.no-such-check"\nsince = "1"\n',
                            encoding="utf-8")
            self.assertEqual(codes.write(path), {"new": len(checks) - 1, "gone": 1})
            again = codes.read(path)
            self.assertEqual(again["BLD-001"]["check"], first)
            self.assertEqual((again["BLD-007"]["check"], again["BLD-007"]["gone"]), ("build.no-such-check", codes.SINCE))
            numbers = sorted(int(c[4:]) for c in again)
            self.assertEqual(numbers[:3], [1, 7, 8])                     # (2 to 6 never given: 7 was the highest)
            self.assertEqual(codes.write(path), {"new": 0, "gone": 0})   # (as it was: nothing moves)
            self.assertEqual(codes.read(path), again)

    def test_the_code_travels_on_the_error_and_the_player_reads_the_same(self):
        from ruse_launcher.api import LauncherError
        error = coded(LauncherError("Tick at least one mod for this mod set.", key="set_no_mods"), "SET-06")
        self.assertEqual((str(error), error.words_key, code_of(error)), ("Tick at least one mod for this mod set.",
                                                                        "set_no_mods", "SET-06"))
        coded(error, "SET-15", n=2)                                      # said again higher up: the first says why
        self.assertEqual((error.bw_code, error.bw_detail), ("SET-15", {"why": "SET-06", "n": 2}))
        self.assertIs(coded(error, ""), error)
        try:  # a build check's code, by its key (not assertRaises: it drops the traceback, which says where)
            load_mod(Path(tempfile.gettempdir()) / f"{SECRET}-not-there")
        except BuildError as exc:
            self.assertEqual(code_of(exc), codes.bld_of(entry(words="has no mod.toml")["check"]))
            self.assertTrue(code_of(exc))
        # an error of Python's own raised where a check's text is only blanks ("{0}": the Play's project refusal) is
        # none of its: no code by its words; one of ours is (the control)
        with mock.patch("rusemod.checkkeys.where_of", return_value="rusemod.play:_modded"):
            self.assertEqual(code_of(KeyError("Unit_Nicks_Tank")), "")
            self.assertTrue(code_of(BuildError("Install the update first.")))


class TheDaysList(WithBugWatch):
    def test_nothing_new_below_the_agreement_version_that_describes_it(self):
        for version in (0, 3, 4):
            self.agree(version)
            bugwatch._current.call("new_set", 0.1, coded(OSError(28, "full"), "SET-14"))
            bugwatch._current.failure("LIST-01", http=503)
            bugwatch._current.page_error("units", "TypeError")
            self.assertEqual(self.failures(), [], version)
            self.assertNotIn("failures", self.sent())
            self.assertFalse(any(k.startswith("page_error:") for k in self.day()["messages"]))
        self.assertEqual(self.day()["calls"]["new_set"]["failed"], 3)          # (counted as before)
        self.agree(5)
        bugwatch._current.failure("LIST-01", http=503)
        self.assertEqual(self.sent()["failures"], [{"code": "L-LIST-01", "detail": {"http": 503}}])
        self.agree(4)                                   # (a version below it since: what waits isn't sent either)
        self.assertNotIn("failures", self.sent())

    def test_a_window_call_s_own_code_for_a_failure_no_other_code_says(self):
        """codes.toml `calls`: the Launcher's Play and its set check, the Studio's Test in game, before their jobs."""
        for name in ("play", "check_mods", "set_check", "test_in_game", "new_set"):
            bugwatch._current.call(name, 0.1, KeyError("x"))
        bugwatch._current.call("play", 0.1, coded(KeyError("x"), "PLAY-02"))  # (a code of its own comes first)
        self.assertEqual(self.codes(), ["L-PLAY-06", "L-SET-26", "L-PLAY-02"])
        bugwatch._current = bugwatch.Watch(self.home, "studio", "0.9.8.23", opener=mock.Mock())
        for name in ("play", "test_in_game"):
            bugwatch._current.call(name, 0.1, KeyError("x"))
        self.assertEqual(self.codes(), ["S-TST-06"])

    def test_one_constant_says_from_which_version(self):
        self.agree(4)
        with mock.patch.object(bugwatch, "CODES_AGREEMENT", 4):
            bugwatch._current.failure("UPD-02")
            self.assertEqual(self.sent()["failures"], [{"code": "L-UPD-02"}])
        self.assertEqual(bugwatch.CODES_AGREEMENT, 5)                   # (the legal session's version 5 notice)

    def test_an_entry_holds_codes_fixed_words_and_numbers_only(self):
        said = bugwatch.failure_entry("launcher", "SET-14", "build", "L1-F0-R0",
                                      {"win": 32, "http": 999, "exit": -1073741819, "n": 3, "why": "BLD-012",
                                       "words": "Nick's secret set", "file": "held", "path": "D:/Users/Nick"})
        self.assertEqual(said, {"code": "L-SET-14", "stage": "build", "set": "L1-F0-R0",
                                "detail": {"win": 32, "exit": 3221225477, "n": 3, "why": "BLD-012"}})
        self.assertEqual(bugwatch.failure_entry("studio", "PLAY-20", "elsewhere", "Nick's set", {"why": "SET-22"}),
                         {"code": "S-PLAY-20", "detail": {"why": "S-SET-22"}})
        self.assertIsNone(bugwatch.failure_entry("studio", "not a code"))
        self.assertIsNone(bugwatch.failure_entry("studio", ""))

    def test_each_failure_once_and_at_most_twenty_with_nothing_naming_the_player(self):
        for n in range(25):
            bugwatch._current.failure("SET-14", win=n)
        bugwatch._current.failure("SET-14", win=0)                     # (one the list holds already)
        self.assertEqual(len(self.failures()), bugwatch.FAILURES_MOST)
        self.assertEqual([f["detail"]["win"] for f in self.failures()], list(range(20)))
        player = homes.settings(self.home)["player"]
        listed = json.dumps(self.sent()["failures"])
        for private in (player["name"], player["id"], "Nick"):
            self.assertNotIn(private, listed)


# --- FL-97: the Launcher's New / Save mod set -----------------------------------------------------------------------
class ModSets(WithBugWatch):
    def setUp(self):
        super().setUp()
        (self.home / "library" / "tanks").mkdir(parents=True)
        (self.home / "library" / "tanks" / "mod.toml").write_text(MOD.format(id="tanks"), encoding="utf-8")
        from ruse_launcher.api import LauncherApi
        self.api = LauncherApi(home=self.home, game_dir=self.root / "nowhere", find=lambda: None)
        self.page = webui.page_api(self.api)

    def refused(self, call, *args) -> Exception:
        try:
            getattr(self.page, call)(*args)
        except Exception as exc:  # noqa: BLE001
            return exc
        self.fail(f"{call} went through")

    def test_each_refusal_has_its_own_code_and_the_old_keys_go_on(self):
        typed = "Nick's secret set"
        self.refused("new_set", "  ", ["tanks"])
        self.refused("new_set", typed, [])
        self.refused("new_set", typed, "tanks")                         # not a list
        self.refused("new_set", typed, ["tanks", " "])                  # a blank entry: the same code, once
        self.refused("new_set", typed, ["tanks", "tanks"])
        self.refused("new_set", typed, ["not-in-the-library"])
        self.refused("new_set", typed, [str(self.root / "folder-gone")])  # a hand-written set's folder, gone
        made = self.page.new_set("Tanks", ["tanks"])["set"]
        self.refused("save_set", "vanilla", typed, ["tanks"])
        self.refused("save_set", "deleted-meanwhile", typed, ["tanks"])
        self.refused("rename_set", made + "-gone", typed)
        self.assertEqual(self.codes(), ["L-SET-02", "L-SET-06", "L-SET-05", "L-SET-07", "L-SET-08", "L-SET-09",
                                        "L-SET-11", "L-SET-10"])
        self.assertEqual(self.day()["messages"], {                      # (the keys as before, the pairs still one)
            "new_set:set_no_name": 1, "new_set:set_no_mods": 3, "new_set:set_mod_twice": 1,
            "new_set:set_mod_missing": 2, "save_set:set_vanilla": 1, "save_set:set_gone": 1, "rename_set:set_gone": 1})
        sent = json.dumps(self.sent())
        for private in ("secret", "not-in-the-library", "folder-gone", "deleted-meanwhile", "tanks"):
            self.assertNotIn(private, json.dumps(self.sent().get("failures")))
        self.assertNotIn("secret", sent)

    def test_the_set_file_not_written_says_its_windows_error_number(self):
        (self.home / "sets").write_text("a file where the folder goes", encoding="utf-8")
        self.refused("new_set", "Tanks", ["tanks"])                     # (the player's words: as before, file_words)
        self.assertEqual(self.day()["calls"]["new_set"]["errors"], {"FileExistsError": 1})
        (said,) = self.failures()
        self.assertEqual(said, {"code": "L-SET-14", "detail": {"win": 183 if os.name == "nt" else 17}})

    def test_a_set_saved_then_the_lists_failing_has_its_own_code(self):
        """FL-97's path 12: the set IS written, then reading the lists again fails, and the call fails as before."""
        held = PermissionError(13, "held by another program")
        with mock.patch.object(self.api, "library", side_effect=held):
            error = self.refused("new_set", "Tanks", ["tanks"])
        self.assertIs(error, held)
        self.assertTrue((self.home / "sets" / "tanks.toml").is_file())   # (saved)
        self.assertEqual(self.failures(), [{"code": "L-SET-15", "detail": {"win": 13}}])

    def test_a_mod_whose_files_change_while_listed_doesn_t_fail_a_saved_set(self):
        """FL-97's path 12, its cause in the code: one library mod's files changing while the lists are read (a mod
        installed meanwhile: a file listed is gone at its stat) failed the whole list, so a set that WAS saved came
        back as a failure, and saving it again made tanks-2. The lists now come; Play's own check still stops."""
        from rusemod import fairplay
        gone = FileNotFoundError(2, "gone while it was listed")
        with mock.patch.object(fairplay, "ON", True), mock.patch.object(self.api, "_fair_of", side_effect=gone):
            got = self.page.new_set("Tanks", ["tanks"])
            with self.assertRaises(FileNotFoundError):
                self.api._untrusted({"folders": [str(self.home / "library" / "tanks")]})
        self.assertEqual((got["set"], [m["id"] for m in got["library"]]), ("tanks", ["tanks"]))
        self.assertEqual(sorted(p.name for p in (self.home / "sets").iterdir()), ["tanks.toml"])   # (one set)
        self.assertEqual(self.failures(), [])

    def test_a_play_refused_by_a_set_file_s_mistake_says_which(self):
        sets = self.home / "sets"
        sets.mkdir()
        (sets / "empty.toml").write_text('name = "x"\nmods = []\n', encoding="utf-8")
        (sets / "nolib.toml").write_text('name = "x"\nmods = ["nicks-missing-mod"]\n', encoding="utf-8")
        (sets / "broken.toml").write_text('name = "x\n', encoding="utf-8")
        (sets / "Bad Name.toml").write_text('name = "x"\nmods = ["tanks"]\n', encoding="utf-8")
        (sets / "tanks.toml").write_text('name = "x"\nmods = ["tanks"]\n', encoding="utf-8")
        for set_id in ("empty", "nolib", "broken", "bad name", "no-such-set"):
            self.api.play(set_id)
        with mock.patch.object(self.api, "_starting", return_value=True):
            self.api.play("tanks")
        with mock.patch.object(self.api, "_restoring", return_value=True):
            self.api.play("tanks")
        with mock.patch("rusemod.fairplay.ON", True), mock.patch.object(self.api, "_untrusted", return_value=["x"]), \
                mock.patch.object(self.api, "check_mods", return_value={"hard": []}):
            self.api.play("tanks")
        self.assertEqual(self.failures(), [
            {"code": "L-PLAY-04", "detail": {"why": "L-SET-22"}}, {"code": "L-PLAY-04", "detail": {"why": "L-SET-23"}},
            {"code": "L-PLAY-04", "detail": {"why": "L-SET-25"}}, {"code": "L-PLAY-04", "detail": {"why": "L-SET-21"}},
            {"code": "L-PLAY-03"}, {"code": "L-PLAY-01"}, {"code": "L-PLAY-02"}, {"code": "L-PLAY-05", "detail": {"n": 1}}])
        self.assertEqual(self.day()["messages"]["play:play_set_mistake"], 4)  # (the old key, as before)
        self.assertNotIn("error_code", json.dumps(self.api.mod_sets()))     # (the page gets what it got)


# --- FL-98 and FL-99: a Play's and a Test in game's steps, and the build's checks --------------------------------
class PlaysAndTests(WithBugWatch):
    def play(self, mods, steam=True, **hooks):
        from rusemod.play import Starter
        starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: steam,
                          wait=lambda s: None)
        for name, hook in hooks.items():
            setattr(starter, name, hook)
        try:
            starter.modded(self.root / "game", mods, self.root / "copies" / "Modded game", "test", lambda line: None)
        except Exception as exc:  # noqa: BLE001
            bugwatch._current.job("play", False, 0.5, exc, len(getattr(exc, "errors", [])),
                                  mistakes=getattr(exc, "error_sites", []))
            return exc
        self.fail("the Play went through")

    def test_refused_before_any_build(self):
        from rusemod.owned import Refusal
        (self.root / "game").mkdir()
        mods = folders(self.root / "mods")
        self.play(mods, required=lambda: "Install the update first.")
        refusal = Refusal("This copy isn't confirmed.")
        refusal.why, refusal.n = "OWN-02", 2
        self.play(mods, owned=lambda game: refusal)
        with mock.patch("rusemod.backup._claim", return_value=None):  # (the other app's build holds the lock)
            self.play(mods)
        self.assertEqual(self.failures(), [
            {"code": "L-PLAY-08", "stage": "before", "set": "L1-F1-R1"},
            {"code": "L-PLAY-09", "stage": "before", "set": "L1-F1-R1", "detail": {"why": "L-OWN-02", "n": 2}},
            {"code": "L-PLAY-11", "stage": "before", "set": "L1-F1-R1"}])
        self.assertIn("play:play_copy_not_confirmed", self.day()["messages"])    # (the old keys beside)

    def test_the_build_listed_mistakes_each_by_its_code(self):
        from rusemod.patch import Finding, PatchError
        e = entry("nation-models")
        try:
            raise coded(PatchError("m (m.rndf:1): [x] matches 0 items"), "BLD-047")
        except PatchError:
            caught = Finding("error", "m (m.rndf:1): [x] matches 0 items")  # (made while handling it: its code)
        found = [Finding("error", e["us"].replace("{", "").replace("}", ""), where=e["where"], check="nation-models"),
                 caught, Finding("error", "words no check of ours says")]
        self.assertEqual(caught.code, "BLD-047")
        result = SimpleNamespace(errors=found, order=[])
        (self.root / "game").mkdir()
        with mock.patch("rusemod.play.build_and_write", return_value=result), \
                mock.patch("rusemod.play.read_mods", return_value=[]):
            error = self.play(folders(self.root / "mods")[:2])
        rule = codes.bld_of("nation-models")
        self.assertEqual(error.error_codes, [rule, "BLD-047", ""])
        self.assertEqual(self.failures(), [
            {"code": "L-PLAY-20", "stage": "listed", "set": "L1-F1-R0", "detail": {"n": 3, "why": rule}},
            {"code": rule, "stage": "listed", "set": "L1-F1-R0"}, {"code": "BLD-047", "stage": "listed",
                                                                   "set": "L1-F1-R0"}])

    def test_the_build_raised_on_an_error_no_code_says_and_the_game_didn_t_start(self):
        (self.root / "game").mkdir()
        with mock.patch("rusemod.play.read_mods", side_effect=KeyError("x")):
            self.play([])
        copy = self.root / "copies" / "Modded game"
        copy.mkdir(parents=True)
        (copy / "RUSE.exe").write_bytes(b"MZ")
        with mock.patch("rusemod.instance.needs_build", return_value=False):
            self.play([], steam=False)
        self.assertEqual(self.failures(), [{"code": "L-PLAY-26", "stage": "build", "set": "L0-F0-R0"},
                                           {"code": "L-PLAY-24", "stage": "start", "set": "L0-F0-R0"}])

    def test_the_game_folder_not_found_and_a_studio_test_s_letter(self):
        from ruse_launcher.api import LauncherApi
        api = LauncherApi(home=self.home, game_dir=None, find=lambda: None)
        with mock.patch.object(api, "_game", return_value=(None, {})):
            with self.assertRaises(BuildError) as raised:
                api._play({"id": "x", "name": "x", "folders": []}, lambda line: None)
        self.assertEqual(code_of(raised.exception), "PLAY-07")
        bugwatch._current = bugwatch.Watch(self.home, "studio", "0.9.8.23", opener=mock.Mock())
        (self.root / "game").mkdir()
        self.play([], steam=False, required=lambda: "Install the update first.")
        self.assertEqual(self.codes(), ["S-PLAY-08"])


class HiddenCauses(WithBugWatch):
    """The checks whose keys hid the cause (round 4's box): load_mod's nine raises of one key and two of another, the
    load order's refusals (one key, "load order: {0}"), the patch engine's refusals (one key per function at best):
    each its own BLD code."""

    def test_load_mod_s_shape_only_refusals_each_have_their_own_code(self):
        from rusemod.checkkeys import _template
        tree = ast.parse((SRC / "rusemod" / "build.py").read_text(encoding="utf-8"))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "load_mod")
        given = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                call = node.exc.args[0] if getattr(node.exc.func, "id", "") == "coded" else node.exc
                template = _template(call.args[0]) if call.args else ""
                if getattr(call.func, "id", "") == "BuildError" and template in ("{0}", "{0}: {1}"):
                    self.assertEqual(getattr(node.exc.func, "id", ""), "coded", node.lineno)
                    given.append(node.exc.args[1].value)
        self.assertEqual(len(given), 11)
        self.assertEqual(len(set(given)), 11)

    def test_load_mod_says_which_file_by_its_code(self):
        from rusemod.menuorder import MenuOrderError
        from rusemod.squads import SquadError
        mod = self.root / "mod"
        mod.mkdir()
        (mod / "mod.toml").write_text('[mod]\nid = "x"\nversion = ', encoding="utf-8")
        with self.assertRaises(BuildError) as raised:
            load_mod(mod)
        said = [code_of(raised.exception)]
        (mod / "mod.toml").write_text(MOD.format(id="x"), encoding="utf-8")
        for target, error in (("rusemod.menuorder.read_mod", MenuOrderError("menus.toml: x")),
                              ("rusemod.squads.mod_squads", SquadError("files/models/x.squad.toml: x"))):
            with mock.patch(target, side_effect=error), self.assertRaises(BuildError) as raised:
                load_mod(mod)
            said.append(code_of(raised.exception))
        self.assertEqual(said, ["BLD-001", "BLD-003", "BLD-007"])

    def test_the_load_order_s_refusals_each_have_their_code(self):
        from rusemod.resolve import ModInfo, ResolveError, load_order, pick_versions
        cases = [[ModInfo("a"), ModInfo("a")], [ModInfo("a", depends={"b": "*"})],
                 [ModInfo("a", depends={"b": ">=2"}), ModInfo("b", "1.0.0")],
                 [ModInfo("a", conflicts={"b": "*"}), ModInfo("b")],
                 [ModInfo("a", after=["b"]), ModInfo("b", after=["a"])]]
        said = []
        for mods in cases:
            with self.assertRaises(ResolveError) as raised:
                load_order(mods)
            said.append(code_of(raised.exception))
        with self.assertRaises(ResolveError) as raised:
            pick_versions({"a": "*"}, {})
        said.append(code_of(raised.exception))
        self.assertEqual(said, ["BLD-020", "BLD-021", "BLD-022", "BLD-023", "BLD-024", "BLD-017"])
        source = (SRC / "rusemod" / "build.py").read_text(encoding="utf-8")   # (the build says it again with its code)
        self.assertIn('raise coded(BuildError(f"load order: {exc}"), getattr(exc, "bw_code", "")) from None', source)

    def test_the_patch_engine_s_refusals_each_have_their_code(self):
        """The settled case first: patch._select's two refusals arrived as one key (round 4, lead_settled.json)."""
        from rusemod.patch import Op, num
        from test_patch import named, run
        none = run(("m", [Op("set", "$/MG", "Weapons[class=TNope].Ammunition.Puissance", num(1), share="shared")]))
        many = run(("m", [Op("set", "@[class=TUniteAuSolDescriptor]", "Nationalite", num(1))]), game=named())
        every = run(("m", [Op("set", path="X", value=num(1), every="TNope")]), game=named())
        said = [(r.errors[0].code, codes.finding_code(r.errors[0])) for r in (none, many, every)]
        self.assertEqual(said, [("BLD-047", "BLD-047"), ("BLD-050", "BLD-050"), ("BLD-028", "BLD-028")])
        # one failure, one code: a refusal with a code of its own and an exact check of its own is that check's code
        for code, check in (("BLD-014", "build._reliefs-2"), ("BLD-015", "build._area_clips-3"),
                            ("BLD-016", "build._area_clips-4"), ("BLD-028", "patch.apply"),
                            ("BLD-036", "patch._file_op"), ("BLD-047", "patch._select"), ("BLD-049", "patch._target"),
                            ("BLD-050", "patch._target-2"), ("BLD-054", "patch._share")):
            self.assertEqual(codes.bld_of(check), code, check)
        found = codes.found_in_code()
        patch_codes = {c for c, places in found.items() if places[0][0].startswith("patch.")}
        source = (SRC / "rusemod" / "patch.py").read_text(encoding="utf-8")
        self.assertEqual(len(patch_codes), source.count("coded(PatchError(") + 1)  # (+1: an object's reference gone)


# --- what sent nothing ------------------------------------------------------------------------------------------
class SentNothingBefore(WithBugWatch):
    def test_the_mod_list_that_couldn_t_be_had(self):
        from rusemod import mod_index
        from rusemod.mod_index import ModIndexError, fetch
        cache = self.root / "index"

        def answer(status):
            return urllib.error.HTTPError("https://example.invalid/index.toml", status, "no", {}, io.BytesIO(b""))
        for status in (503, 404):
            with mock.patch.object(mod_index, "_get", side_effect=answer(status)), self.assertRaises(ModIndexError):
                fetch("https://example.invalid/index.toml", cache)
        good = b'[[mod]]\nid = "cool-mod"\nversion = "1.0.0"\ndownload = "https://example.invalid/c"\nsize = 1\n' \
               b'sha256 = "' + b"0" * 64 + b'"\n[[mod]]\nid = "Bad Id"\n'
        with mock.patch.object(mod_index, "_get", return_value=good):
            fetch("https://example.invalid/index.toml", cache)                 # (one entry skipped as bad)
        with mock.patch.object(mod_index, "_get", side_effect=answer(503)):
            self.assertEqual(fetch("https://example.invalid/index.toml", cache).source, "cache")
        with mock.patch.object(mod_index, "_get", return_value=b"not [ toml"):
            fetch("https://example.invalid/index.toml", cache)
        self.assertEqual(self.failures(), [{"code": "L-LIST-01", "detail": {"http": 503}},
                                           {"code": "L-LIST-02", "detail": {"http": 404}},
                                           {"code": "L-LIST-05", "detail": {"n": 1}},
                                           {"code": "L-LIST-03", "detail": {"http": 503}}, {"code": "L-LIST-04"}])

    def test_the_update_check_that_failed(self):
        from rusemod import update

        class App(update.UpdateCalls):
            UPDATE_APP, UPDATE_VERSION = "launcher", "0.4.8.22"
            _home = self.home

            def prefs(self):
                return {}

        app = App()
        refused = urllib.error.HTTPError(update.API, 403, "rate limit", {}, None)
        app._update_fetch = mock.Mock(side_effect=refused)
        app._update_fetch_text = mock.Mock(side_effect=OSError("no internet"))
        self.assertTrue(app.update_check()["error"])                            # (the call itself goes well)
        # a newer release we signed whose installer isn't in it yet (since the signed updates, a release with no
        # signature of ours is "not ours", which Bug Watch counts nothing for: legal/signed-updates)
        from rusemod import releasesig
        from test_update import KEYS, fetch_sig, release
        app._update_fetch = mock.Mock(return_value=[release("launcher-v0.4.8.99",
                                                            setup="RUSE-Launcher-Setup-elsewhere.exe")])
        app._update_fetch_sig = fetch_sig
        with mock.patch.object(releasesig, "RELEASE_KEYS", KEYS):
            app.update_check()
        self.assertEqual(self.failures(), [{"code": "L-UPD-01", "detail": {"http": 403}}, {"code": "L-UPD-02"}])

    def test_the_sign_in_answers_that_aren_t_errors(self):
        from rusemod import owned, ownedpass
        home = self.home

        class App(ownedpass.OwnedPassCalls, owned.OwnedCalls):
            _home = home

            def prefs(self):
                return {"lang": "us"}

            def _game(self):
                return None

        app = App()
        with mock.patch.object(ownedpass, "ON", True):
            for answer in ({"status": "not-owned"}, {"status": "private"}, {"status": "expired"},
                           {"status": "steam-error"}, {"status": "pending"}, {}):
                with mock.patch.object(ownedpass, "_call", return_value=(200, answer)):
                    app.owned_sign_in_poll("abc")
            with mock.patch.object(ownedpass, "_call", side_effect=urllib.error.URLError("no internet")):
                self.assertEqual(app.owned_sign_in_poll("abc"), {"status": "steam-error"})
            with mock.patch.object(ownedpass, "_call", return_value=(200, {"status": "owned", "pass": "x.y.z"})):
                self.assertEqual(app.owned_sign_in_poll("abc")["status"], "bad-pass")
            self.assertTrue(app.owned_unlock("ABCDE-FGHIJ")["bad_code"])
            with self.assertRaises(ownedpass.OwnedPassError) as raised:
                ownedpass.start("not an address")
        self.assertEqual(code_of(raised.exception), "SIGN-01")
        self.assertEqual(self.codes(), ["L-SIGN-05", "L-SIGN-06", "L-SIGN-07", "L-SIGN-08", "L-SIGN-10",
                                        "L-SIGN-09", "L-SIGN-12", "L-SIGN-16"])
        self.assertEqual(self.failures()[4], {"code": "L-SIGN-10", "detail": {"http": 200}})
        self.assertEqual(self.failures()[6], {"code": "L-SIGN-12", "detail": {"why": "L-PASS-01"}})

    def test_a_server_that_couldn_t_be_reached_says_the_windows_error_number(self):
        # (the newest pull, 2026-11-26: 26 of 39 sign-in starts failed "We couldn't reach the sign-in server", while
        # the server answered here; without the number Bug Watch can't say why)
        import socket
        import ssl
        from rusemod import owned, ownedpass, update
        from rusemod.bugwatch import detail_of, os_number
        refused = OSError(None, "refused", None, 10061)              # (as Windows gives it: its winerror)
        self.assertEqual(os_number(urllib.error.URLError(refused)), 10061)
        self.assertEqual(os_number(urllib.error.URLError(socket.gaierror(11001, "getaddrinfo failed"))), 11001)
        self.assertEqual(os_number(refused), 10061)
        for none in (urllib.error.URLError(TimeoutError("timed out")), urllib.error.URLError("no internet"),
                     urllib.error.URLError(ssl.SSLCertVerificationError(1, "certificate verify failed")),
                     urllib.error.HTTPError("https://example.invalid", 503, "no", {}, None), ValueError("bad")):
            self.assertIsNone(os_number(none), none)
        self.assertEqual(detail_of(urllib.error.URLError(refused)), {"win": 10061})
        home = self.home

        class Pass(ownedpass.OwnedPassCalls, owned.OwnedCalls):
            _home = home

            def prefs(self):
                return {"lang": "us"}

            def _game(self):
                return None

        class Update(update.UpdateCalls):
            UPDATE_APP, UPDATE_VERSION = "launcher", "0.4.8.22"
            _home = home

            def prefs(self):
                return {}
        with mock.patch.object(ownedpass, "ON", True), \
                mock.patch.object(ownedpass, "_call", side_effect=urllib.error.URLError(refused)):
            with self.assertRaises(ownedpass.OwnedPassError) as raised:
                ownedpass.start("https://example.invalid")
            self.assertEqual(Pass().owned_sign_in_poll("abc"), {"status": "steam-error"})
        self.assertEqual((code_of(raised.exception), raised.exception.bw_detail), ("SIGN-02", {"win": 10061}))
        self.assertEqual(str(raised.exception), "We couldn't reach the sign-in server. Check your connection and try "
                                                "again.")                     # (what the player reads: the same)
        app = Update()
        app._update_fetch = mock.Mock(side_effect=urllib.error.URLError(refused))
        app._update_fetch_text = mock.Mock(side_effect=urllib.error.URLError(socket.gaierror(11001, "getaddrinfo")))
        self.assertTrue(app.update_check()["error"])
        app._update_fetch = mock.Mock(side_effect=urllib.error.HTTPError(update.API, 403, "rate limit", {}, None))
        self.assertTrue(app.update_check()["error"])
        self.assertEqual(self.failures(), [{"code": "L-SIGN-09", "detail": {"win": 10061}},
                                           {"code": "L-UPD-01", "detail": {"win": 10061}},
                                           {"code": "L-UPD-01", "detail": {"http": 403, "win": 11001}}])

    def test_a_game_that_ended_badly_with_its_exit_number(self):
        local = self.root / "local"
        (local / "Temp" / "CrashRpt_x").mkdir(parents=True)

        def game(ran, ended, dump=None):
            if dump is not None:
                (local / "Temp" / "CrashRpt_x" / "x.dmp").write_bytes(dump)
            times = iter([1000.0, 1000.0 + ran])
            bugwatch.GameWatch(bugwatch._current, SimpleNamespace(poll=lambda: ended), ["cool-mod@1.2"], 0,
                               sleep=lambda s: None, clock=lambda: next(times), local=str(local)).run()
            (local / "Temp" / "CrashRpt_x" / "x.dmp").unlink(missing_ok=True)
        game(20, 1)                                   # closed within a minute
        game(600, 3221225477)                         # ended badly after ten minutes, no crash report
        game(900, 0)                                  # quit as it should: nothing
        game(600, 5, dump=b"not a crash report")      # a report that isn't one
        self.assertEqual(self.failures(), [{"code": "L-CRASH-01", "detail": {"exit": 1}},
                                           {"code": "L-CRASH-05", "detail": {"exit": 3221225477}},
                                           {"code": "L-CRASH-04", "detail": {"exit": 5}}])
        self.assertEqual(self.day()["messages"], {"game:closed-under-1-min": 1})   # (the old key, as before)


# --- the Studio: B9 A, B10 A, B11 B ---------------------------------------------------------------------------------
STUDIO_UI = SRC / "ruse_studio" / "ui"
FUNCTIONS_IN_NODE = r"""
const fs = require("fs"), vm = require("vm");
const [code, casesFile] = process.argv.slice(-2);
(async () => {
  const out = [];
  for (const c of JSON.parse(fs.readFileSync(casesFile, "utf8"))) {
    const timers = [], said = [], asked = [], answers = (c.answers || []).slice();
    const ctx = vm.createContext({ console, Promise, Set, String,
      setTimeout: (fn, ms) => { timers.push({ fn, ms }); return timers.length; }, clearTimeout: () => {},
      window: { addEventListener() {} }, state: { words: c.words || {}, view: c.view || "units" },
      say: (text, kind) => { said.push([text, kind]); return {}; },
      addToastAction: (card, a) => { said.push(["button", a.label]); return {}; },
      api: () => ({ bugwatch_crash: async () => {
        const a = answers.shift();
        if (a === undefined || a === "throw") throw new Error("the window was busy");
        return a;
      }, bugwatch_page_error: async (screen, name) => { asked.push([screen, name]); return { ok: true }; } }) });
    vm.runInContext(fs.readFileSync(code, "utf8"), ctx, { filename: "app.js" });
    vm.runInContext(c.call, ctx);
    const delays = [];
    for (let i = 0; i < 40 && timers.length; i++) {
      const { fn, ms } = timers.shift();
      delays.push(ms);
      await fn();
    }
    await new Promise((done) => setImmediate(done));
    out.push({ delays, said, asked });
  }
  process.stdout.write(JSON.stringify(out));
})();
"""


def app_js() -> str:
    return (STUDIO_UI / "app.js").read_text(encoding="utf-8")


def part(code: str, start: str, end: str) -> str:
    at = code.index(start)
    return code[at:code.index(end, at)]


class ModInstalls(WithBugWatch):
    """FL-123 (the owner 2026-11-26: "places a mod install can fail. fix"; Bug Watch's newest pull: install_mods failed
    2 of 5 with one key for every reason): each place an install from the mod list can fail says which by its code,
    with its numbers, and a download that didn't come whole is tried once more."""
    BODY = b"a mod file's bytes " * 100

    def entry(self, **over):
        import hashlib
        return {"id": "cool-mod", "name": "Cool mod", "version": "1.0.0", "download": "https://example.invalid/c",
                "size": len(self.BODY), "sha256": hashlib.sha256(self.BODY).hexdigest(), **over}

    @staticmethod
    def answers(*answers):
        """A stand-in for net.urlopen giving each answer in turn: bytes (the body as it comes), an error raised on
        opening, or ("broke", bytes): those bytes, then the answer breaks off as http.client says it (IncompleteRead)."""
        import http.client
        calls = []

        class Response:
            def __init__(self, body, broke):
                self.chunks, self.broke = [body[i:i + 65536] for i in range(0, len(body), 65536)], broke

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, n):
                if self.chunks:
                    return self.chunks.pop(0)
                if self.broke:
                    raise http.client.IncompleteRead(b"", 10)
                return b""

        def opener(req, timeout):
            calls.append(req.full_url)
            a = answers[len(calls) - 1]
            if isinstance(a, BaseException):
                raise a
            return Response(a[1], True) if isinstance(a, tuple) else Response(a, False)
        return opener, calls

    def test_a_download_that_didn_t_come_whole_is_tried_once_more_and_each_end_has_its_code(self):
        from rusemod import mod_index
        into = self.root / "downloads"
        opener, calls = self.answers(("broke", self.BODY[:500]), self.BODY)
        with mock.patch.object(mod_index.net, "urlopen", opener):
            got = mod_index.download(self.entry(), into)
        self.assertEqual((got.read_bytes(), len(calls)), (self.BODY, 2))
        refused = OSError(None, "refused", None, 10061)                      # (as Windows gives it: its winerror)

        def http(status):
            return urllib.error.HTTPError("https://example.invalid/c", status, "no", {}, io.BytesIO(b""))
        cases = [  # (its answers, its code, its numbers, how many tries)
            ((("broke", self.BODY[:500]), self.BODY[:900]), "LIST-07", {}, 2),   # broke off, then cut short
            ((self.BODY[:-1] + b"X",), "LIST-08", {}, 1),                        # whole, another checksum: at once
            ((self.BODY + b"more",), "LIST-08", {}, 1),                          # bigger: at once
            ((http(404),), "LIST-06", {"http": 404}, 1),                         # the web server refused: at once
            ((http(503), http(503)), "LIST-06", {"http": 503}, 2),               # a server error: once more
            ((urllib.error.URLError(refused), urllib.error.URLError(refused)), "LIST-06", {"win": 10061}, 2),
        ]
        for answers, code, numbers, tries in cases:
            with self.subTest(code=code, tries=tries):
                opener, calls = self.answers(*answers)
                with mock.patch.object(mod_index.net, "urlopen", opener), \
                        self.assertRaises(mod_index.ModIndexError) as raised:
                    mod_index.download(self.entry(), into)
                self.assertEqual((code_of(raised.exception), raised.exception.bw_detail, len(calls)),
                                 (code, numbers, tries))
        self.assertEqual([p.name for p in into.iterdir()], ["cool-mod-1.0.0.rusemod"])  # (no .part left behind)

    def test_the_launcher_s_places_each_say_which_and_each_mod_s_reason_is_counted(self):
        from rusemod.library import LibraryError
        from rusemod.mod_index import ModIndexError
        from ruse_launcher.api import LauncherApi
        downloaded = self.root / "cool-mod-1.0.0.rusemod"
        library = mock.Mock()
        stub = SimpleNamespace(_home=self.root, _library=library)

        def one(add_error):
            downloaded.write_bytes(b"x")
            library.add = mock.Mock(side_effect=add_error)
            with mock.patch("rusemod.mod_index.download", return_value=downloaded), \
                    self.assertRaises((ModIndexError, OSError)) as raised:
                LauncherApi._install_one(stub, self.entry(), lambda s: None)
            self.assertFalse(downloaded.exists())                            # (the download goes either way)
            return raised.exception
        refused, disk = one(LibraryError("This mod wasn't added: an edit")), one(OSError(None, "full", None, 112))
        self.assertEqual((type(refused), code_of(refused), str(refused)),
                         (ModIndexError, "LIST-09", "This mod wasn't added: an edit"))  # (what the player reads)
        self.assertIsInstance(disk, OSError)
        self.assertEqual((code_of(disk), bugwatch.detail_of(disk)), ("LIST-10", {"win": 112}))

        entries = [self.entry(id=i, name=n) for i, n in (("a-mod", "A mod"), ("b-mod", "B mod"), ("c-mod", "C mod"))]

        def install(entry, say):
            if entry["id"] == "a-mod":
                raise coded(ModIndexError("A mod couldn't be downloaded (no internet)."), "LIST-06", win=10061)
            if entry["id"] == "c-mod":
                raise coded(OSError(None, "full", None, 112), "LIST-10")
        stub = SimpleNamespace(_entries=lambda ids: entries, _install_job=lambda work, done: work(lambda s: None),
                               _install_one=install, _not_all_installed=LauncherApi._not_all_installed)
        with self.assertRaises(ModIndexError) as raised:
            LauncherApi.install_mods(stub, ["a-mod", "b-mod", "c-mod"])
        self.assertEqual((code_of(raised.exception), raised.exception.bw_detail), ("LIST-11", {"n": 2}))
        self.assertTrue(str(raised.exception).startswith("1 of 3 mods were installed. Not installed: A mod (A mod "
                                                         "couldn't be downloaded (no internet)); C mod ("))
        self.assertEqual(self.failures(), [{"code": "L-LIST-06", "detail": {"win": 10061}},
                                           {"code": "L-LIST-10", "detail": {"win": 112}}])


class Studio(WithBugWatch):
    APP = "studio"

    def in_node(self, functions: str, cases: list) -> list:
        found = node()
        if not found:
            self.skipTest("no Node")
        (self.root / "functions.js").write_text("function fill(word, values) {\n  return Object.entries(values || {})"
                                                ".reduce((s, [k, v]) => s.split(`{${k}}`).join(String(v)), word || "
                                                "\"\");\n}\n" + functions, encoding="utf-8")
        (self.root / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
        ran = subprocess.run([found, "-e", FUNCTIONS_IN_NODE, "--", str(self.root / "functions.js"),
                              str(self.root / "cases.json")], capture_output=True, text=True, encoding="utf-8",
                             timeout=120)
        self.assertEqual(ran.returncode, 0, ran.stderr[-2000:])
        return json.loads(ran.stdout)

    def test_b9_the_crash_notice_after_a_test_in_the_launcher_s_words(self):
        import tomllib
        from rusemod import knowncrashes, schema
        studio = tomllib.loads((SRC / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        launcher = tomllib.loads((SRC / "ruse_launcher" / "words.toml").read_text(encoding="utf-8"))
        keys = [f"crash_why_{r}" for r in knowncrashes.REASONS] + ["crash_unit", "crash_mod_unit", "crash_no_unit",
                                                                  "crash_code", "crash_code_under", "crash_copy",
                                                                  "crash_copied", "tip_crash_copy"]
        for key in keys:
            self.assertEqual(studio[key], launcher[key], key)                # (the Launcher's words, all of them)
            self.assertEqual(sorted(studio[key]), sorted(schema.APP_LANGS), key)
        code = app_js()
        test = part(code, "async function testInGame()", "\n}\n")
        self.assertIn("if (ok) watchCrash();", test)
        start = part(code, "async function start()", "\n}\n")
        self.assertIn("watchCrash(0);", start)
        self.assertIn("bugwatch_crash:", (STUDIO_UI / "fake-api.js").read_text(encoding="utf-8"))
        words = {k: v["us"] for k, v in studio.items() if k.startswith("crash_")}
        notice = {"why": "made", "unit": "Horse Squad", "added": True}
        told, after_test = self.in_node(part(code, "let crashWatch = null;", "\n// --- the page's own script errors"), [
            {"call": "watchCrash(0)", "words": words, "answers": ["throw", {"watching": True, "notice": None},
                                                                 {"watching": False, "notice": notice}]},
            {"call": "watchCrash()", "words": words, "answers": [{"watching": False, "notice": None}]}])
        said = words["crash_mod_unit"].replace("{unit}", "Horse Squad").replace("{why}", words["crash_why_made"])
        self.assertEqual((told["delays"], told["said"]), ([0, 3000, 3000], [[said, "error"]]))
        self.assertEqual(after_test, {"delays": [3000], "said": [], "asked": []})
        # the owner's "13, yes": with a crash code, the code after the crash's line, and a Copy code button
        coded = dict(notice, code="R2-TEST", list=True)
        (told,) = self.in_node(part(code, "let crashWatch = null;", "\n// --- the page's own script errors"), [
            {"call": "watchCrash(0)", "words": words, "answers": [{"watching": False, "notice": coded}]}])
        under = words["crash_code_under"].replace("{code}", "R2-TEST")
        self.assertEqual(told["said"], [[said + " " + under, "error"], ["button", words["crash_copy"]]])
        self.assertIn("crash_no_list", studio)                           # (its own words: "the Studio couldn't")
        self.assertIn("Studio", studio["crash_no_list"]["us"])

    def test_b10_a_refusal_of_what_the_modder_entered_sends_nothing(self):
        from ruse_studio.api import EntryError, StudioError

        class Api:
            def scenario_turn(self):
                raise EntryError("the turn must be a number")

            def scenario_save(self):
                raise coded(StudioError("something that is no entry of his"), "TST-05")
        page = webui.page_api(Api())
        for call in (page.scenario_turn, page.scenario_save):
            with self.assertRaises(StudioError):
                call()
        bugwatch._current.job("export_mod", False, 0.5, EntryError("The version should be three numbers."))
        calls = self.day()["calls"]
        self.assertNotIn("scenario_turn", calls)                             # (not even the try)
        self.assertNotIn("export_mod", self.day()["jobs"])
        self.assertEqual(calls["scenario_save"]["failed"], 1)                 # (the control)
        self.assertFalse(any(k.startswith(("scenario_turn", "export_mod")) for k in self.day()["messages"]))
        self.assertEqual(self.codes(), ["S-TST-05"])
        source = (SRC / "ruse_studio" / "api.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("raise EntryError("), 124)            # (the 125 places of B10, one a page's own)
        self.assertIn('raise EntryError("Pick or make a mod or a map first.")', source)
        self.assertIn("raise coded(StudioError(\"A test is already being built", source)

    def test_b11_the_page_s_own_script_errors_its_screen_and_error_name(self):
        api = SimpleNamespace(_home=self.home)
        said = bugwatch.BugWatchCalls.bugwatch_page_error(api, "Units/../../C:", "TypeError: x of undefined")
        self.assertEqual(said, {"ok": True})
        bugwatch.BugWatchCalls.bugwatch_page_error(api, "maps", "ReferenceError")
        self.assertEqual({k: v for k, v in self.day()["messages"].items()},
                         {"page_error:unitsc:TypeErrorxofundefined": 1, "page_error:maps:ReferenceError": 1})
        self.assertEqual(self.codes(), ["S-PAGE-01"])
        self.agree(4)                                                          # (below it: nothing)
        bugwatch.BugWatchCalls.bugwatch_page_error(api, "maps", "RangeError")
        self.assertNotIn("page_error:maps:RangeError", self.day()["messages"])
        code = app_js()
        self.assertIn('window.addEventListener("error", (e) => tellPageError(e.error, false));', code)
        self.assertIn('window.addEventListener("unhandledrejection", (e) => tellPageError(e.reason, true));', code)
        self.assertIn("bugwatch_page_error:", (STUDIO_UI / "fake-api.js").read_text(encoding="utf-8"))
        functions = part(code, "const PAGE_ERRORS", 'window.addEventListener("error"')
        once, own_only = self.in_node(functions, [
            {"view": "units", "call": 'tellPageError(new TypeError("Nick\'s words"), false); '
                                      'tellPageError(new TypeError("again"), false); tellPageError("x", false)'},
            {"view": "maps", "call": 'tellPageError({ name: "StudioError" }, true); '
                                     'tellPageError(new RangeError("y"), true)'}])
        self.assertEqual(once["asked"], [["units", "TypeError"], ["units", "Error"]])
        self.assertEqual(own_only["asked"], [["maps", "RangeError"]])

    @staticmethod
    def dump(program: str, offset: int = 0x1234) -> bytes:
        """A small crash report (as tests/test_bugwatch.py makes one): a bad memory access in RUSE.exe at `offset`,
        the module kept at the path `program`."""
        import struct
        base, name = 0x7FF612340000, program.encode("utf-16-le")
        header = b"MDMP" + struct.pack("<IIIIIQ", 0xA793, 2, 32, 0, 0, 0)
        exception = struct.pack("<II", 1, 0) + struct.pack("<IIQQII", 0xC0000005, 0, 0, base + offset, 0, 0) \
            + b"\0" * 120
        mods_at = 32 + 24 + len(exception)
        mods = struct.pack("<I", 1) + struct.pack("<QIIII", base, 0x200000, 0, 0, mods_at + 4 + 108) + b"\0" * 84
        directory = struct.pack("<III", 6, len(exception), 56) + struct.pack("<III", 4, len(mods), mods_at)
        return header + directory + exception + mods + struct.pack("<I", len(name)) + name

    def test_b11_a_report_counts_for_the_copy_s_game_only(self):
        copy = Path("D:/RUSE-Instances/Modded game")
        report = self.root / "x.dmp"
        for program, ours in (("D:\\RUSE-Instances\\Modded game\\RUSE.exe", True),
                              ("\\\\?\\D:\\RUSE-Instances\\MODDED GAME\\RUSE.exe", True),
                              ("\\Device\\HarddiskVolume3\\RUSE-Instances\\Modded game\\RUSE.exe", True),
                              ("D:\\Steam\\steamapps\\common\\R.U.S.E\\RUSE.exe", False),
                              ("D:\\Other\\Modded game\\RUSE.exe", False)):
            report.write_bytes(self.dump(program))
            found = bugwatch.read_dump(report, copy=copy)
            self.assertEqual(found is not None, ours, program)
            self.assertEqual(bugwatch.read_dump(report)["offset"], "0x1234")   # (without a copy: as before)
            self.assertFalse(re.search(r"Instances|Steam|Device|Other", json.dumps(found)))  # (its path never kept)

    def test_b11_a_game_the_app_was_closed_under_counts_at_its_next_start(self):
        copy, local = self.root / "RUSE-Instances" / "Modded game", self.root / "local"
        copy.mkdir(parents=True)
        (copy / "RUSE.exe").write_bytes(b"MZ")
        started = time.time() - 3600
        watched = bugwatch.GameWatch(bugwatch._current, SimpleNamespace(poll=lambda: None), ["cool-mod@1.2"], 1,
                                     clock=lambda: started, exe=copy / "RUSE.exe", game=self.root / "game",
                                     local=str(local))
        watched._write_note()
        watched._write_note(started + 600)          # (seen running ten minutes on: then the app was closed)
        (note,) = (self.home / "bugwatch" / "games").glob("studio-*.json")
        self.assertNotIn("Nick", note.read_text(encoding="utf-8"))
        later = bugwatch.Watch(self.home, "studio", "0.9.8.23", opener=mock.Mock())
        with mock.patch.object(bugwatch, "_runs_from", return_value=True):      # the game still runs: later
            self.assertEqual(bugwatch.notes_left(later, local=str(local)), 0)
        self.assertTrue(note.is_file())
        reports = local / "Temp" / "CrashRpt_x"
        reports.mkdir(parents=True)
        for name, program, at in (("a", copy / "RUSE.exe", 900),               # its crash, fifteen minutes in
                                  ("b", self.root / "R.U.S.E" / "RUSE.exe", 1000),   # a game started outside the apps
                                  ("c", copy / "RUSE.exe", 2000)):            # the next game's, from the copy
            (reports / f"{name}.dmp").write_bytes(self.dump(str(program).replace("/", "\\"), offset=at))
            os.utime(reports / f"{name}.dmp", (started + at, started + at))
        nxt = bugwatch.GameWatch(bugwatch._current, SimpleNamespace(poll=lambda: None), [], 0,
                                 clock=lambda: started + 1500, exe=copy / "RUSE.exe", local=str(local))
        nxt._close_notes()                          # (the next game starts from the copy: the earlier one has ended)
        self.assertEqual(json.loads(note.read_text(encoding="utf-8"))["until"], started + 1500)
        with mock.patch.object(bugwatch, "_runs_from", return_value=True):      # (that next game runs now)
            self.assertEqual(bugwatch.notes_left(later, local=str(local)), 1)
        self.assertFalse(note.exists())
        self.assertEqual(later.days[bugwatch._today()]["played"], {"total": 15, "mods": {"cool-mod@1.2": 15}})
        (sent,) = [json.loads(p.read_text(encoding="utf-8")) for p in later.outbox.glob("crash-*.json")]
        self.assertEqual((sent["code"], sent["offset"], sent["mods"], sent["own_mods"]),
                         ("0xc0000005", hex(900), ["cool-mod@1.2"], 1))

    def test_b11_the_note_only_under_the_version_and_gone_when_the_game_ends_watched(self):
        def watched(poll):
            times = iter([1000.0] * 3 + [1090.0] * 3)
            return bugwatch.GameWatch(bugwatch._current, SimpleNamespace(poll=poll), [], 0, sleep=lambda s: None,
                                      clock=lambda: next(times), local=str(self.root / "local"))
        game = watched(lambda: 0)
        game._write_note()
        self.assertTrue(game.note.is_file())
        game.run()                                                              # it ended while watched: no note
        self.assertEqual(list((self.home / "bugwatch" / "games").glob("*.json")), [])
        self.agree(4)
        game = watched(lambda: 0)
        game._write_note()
        self.assertIsNone(game.note)                                            # below the version: no note
        (self.home / "bugwatch" / "games" / "studio-1.json").write_text(json.dumps({"started": time.time()}),
                                                                        encoding="utf-8")
        self.assertEqual(bugwatch.notes_left(bugwatch._current), 0)            # (and one left goes unread)
        self.assertEqual(list((self.home / "bugwatch" / "games").glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
