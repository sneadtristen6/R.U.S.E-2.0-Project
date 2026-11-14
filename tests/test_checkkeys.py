"""Which check refused a Play or a Test in game, or listed a mistake in the mods, by a key that never changes
(rusemod.checkkeys, rusemod.bugwatch; 2026-11-10, FL-98 and FL-99: a modder's two Test in game tries and two players'
Plays failed and the reports said only "BuildError" and how many mistakes the build listed).

The file of keys says what the code says (every refusal a build can end on and every mistake it can list, the .rmod
engine's errors, the apps' own steps before a build); a key once given stays; a text is found by the function that
made it; a failed Play says how far it got and which mods were on, the player's own only as counts. Never the words.
No network, no game: the game's program here is a two-byte stand-in file in a temporary folder.

Checked our_tools.json: none of its entries is for this; the test reads no program file, it only names a stand-in
file the way rusemod.play looks for the game's in a modded copy.
"""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import bugwatch, checkkeys, rules  # noqa: E402
from rusemod import home as homes  # noqa: E402
from rusemod.build import BuildError  # noqa: E402
from rusemod.patch import Finding  # noqa: E402

SECRET = "nicks-secret-mod"  # an own mod's id: never in a key
PROGRAM = "RUSE.exe"         # the name rusemod.play looks for in a modded copy (a stand-in file here)


def entry(check: str = None, words: str = None) -> dict:
    """The file's entry with this key, or whose words hold `words`."""
    return next(e for e in checkkeys.read().values()
                if (check is None or e["check"] == check) and (words is None or words in e["us"]))


def said(template: str, *values) -> str:
    """A text as the code makes it from its template."""
    return template.replace("{{", "\x00").replace("}}", "\x01").format(*values).replace("\x00", "{").replace("\x01", "}")


class TheFileIsTheCode(unittest.TestCase):
    def test_the_file_says_what_the_code_says(self):
        self.assertEqual(checkkeys.stale(), [], "run rusemod.checkkeys.write() and commit checkkeys.toml")

    def test_it_holds_every_kind_and_the_play_s_own_refusals(self):
        entries = list(checkkeys.read().values())
        self.assertEqual({e["kind"] for e in entries}, {"raise", "mistake", "tuple", "engine"})
        self.assertGreater(len(entries), 300)
        for check in ("play.project-refusal", "play.other-app-building", "play.mods-have-mistakes",
                      "play.copy-has-no-exe", "play.steam-didnt-start", "build.rmod-clash",
                      "studio.test.game-not-found", "launcher.play.game-not-found"):
            self.assertTrue(any(e["check"] == check for e in entries), check)
        modules = {e["where"].split(":")[0] for e in entries}
        for module in ("rusemod.build", "rusemod.patch", "rusemod.rmod", "rusemod.mission", "rusemod.unitcheck",
                       "ruse_mod_engine.applier", "ruse_studio.api", "ruse_launcher.api"):
            self.assertIn(module, modules)

    def test_a_rule_s_key_is_its_id_and_every_other_names_its_module(self):
        for e in checkkeys.read().values():
            with self.subTest(e["us"][:60]):
                if "." in e["check"]:
                    self.assertTrue(checkkeys.KEY.fullmatch(e["check"]))
                else:
                    self.assertIn(e["check"], rules.RULES)
                for job in ("test_in_game", "play"):
                    self.assertLessEqual(len(f"{job}:{e['check']}"), 64)       # what the server takes
                    self.assertRegex(f"{job}:{e['check']}", bugwatch.NAME_RE)

    def test_every_rule_a_build_applies_has_its_key(self):
        used = {e["check"] for e in checkkeys.read().values() if "." not in e["check"]}
        for rule in ("nation-models", "spawn-models", "unit-nation-range", "flag-59", "mission-ai-side",
                     "delete-unit-class", "own-units-menu"):
            self.assertIn(rule, used)


class KeysStay(unittest.TestCase):
    """A key once in the file stays: while its words stay, and when its function rewords its only changed text."""

    def found(self, where, us, rule="", base="build.load_mod"):
        return {"where": where, "us": us, "rule": rule, "base": base, "kind": "raise", "line": 1, "tagged": False}

    def test_kept_reworded_new_and_a_rule(self):
        w = "rusemod.build:load_mod"
        old = {checkkeys.entry_name(w, "a {0}"): {"check": "build.load_mod", "where": w, "us": "a {0}"},
               checkkeys.entry_name(w, "b {0}"): {"check": "build.load_mod-2", "where": w, "us": "b {0}"}}
        now = [self.found(w, "a {0}"), self.found(w, "b, said better {0}")]
        plan = checkkeys.plan(now, old)
        self.assertEqual([e["check"] for e in plan.values()], ["build.load_mod", "build.load_mod-2"])
        now += [self.found(w, "c {0}"), self.found(w, "d {0}", rule="nation-models")]
        plan = checkkeys.plan(now, plan)   # (the file as the first write left it)
        self.assertEqual([e["check"] for e in plan.values()],
                         ["build.load_mod", "build.load_mod-2", "build.load_mod-3", "nation-models"])

    def test_two_reworded_at_once_get_new_keys_never_an_old_one_s(self):
        w = "rusemod.build:load_mod"
        old = {checkkeys.entry_name(w, "a {0}"): {"check": "build.load_mod", "where": w, "us": "a {0}"},
               checkkeys.entry_name(w, "b {0}"): {"check": "build.load_mod-2", "where": w, "us": "b {0}"}}
        plan = checkkeys.plan([self.found(w, "x {0}"), self.found(w, "y {0}")], old)
        self.assertEqual(sorted(e["check"] for e in plan.values()), ["build.load_mod-3", "build.load_mod-4"])

    def test_a_key_given_by_hand_is_kept(self):
        self.assertEqual(entry("play.steam-didnt-start")["where"], "rusemod.play:_modded")


class FoundAtRunTime(unittest.TestCase):
    def test_a_refusal_is_found_by_its_function_and_words(self):
        e = entry("build.rmod-clash")
        text = said(e["us"], 1, "", "- A and B each replace the same map file ...")
        self.assertEqual(checkkeys.check_of(text, e["where"]), "build.rmod-clash")
        self.assertEqual(checkkeys.check_of(text, "rusemod.build:some_other_function"), "")
        self.assertEqual(checkkeys.check_of(None, e["where"]), "")

    def test_a_listed_mistake_by_its_rule_and_a_check_s_text_after_the_build_s_words(self):
        e = entry("nation-models")
        mistake = Finding("error", said(e["us"], *["Unit_Nicks_Tank"] * 12), where=e["where"])
        self.assertEqual(checkkeys.finding_key(mistake), ("nation-models", ""))
        why = entry("unit-nation-range")["us"]
        text = f"{SECRET} (units.toml:3): Unit_Nicks_Tank.Nationalite: " + said(why, "Nationalite", 9, "0 a, 1 b")
        made = Finding("error", text, where="rusemod.patch:_unit_rules")
        self.assertEqual(checkkeys.finding_key(made)[0], "unit-nation-range")

    def test_the_mod_rules_engine_s_own_mistakes(self):
        """Real runs of the engine a build runs (rusemod.patch.Engine), as tests/test_patch.py makes them: a unit put
        in an eighth nation (a check's ("error", ...) text after the engine's own words, its rule's id) and an
        operation the engine can't do (a caught error said again through Engine._find: its place)."""
        from test_patch import named, run
        from rusemod.patch import Op, num
        r = run((SECRET, [Op("set", "@[ClassNameForDebug='Unit_M3_Lee']", "Nationalite", num(9))]), game=named())
        (mistake,) = r.errors
        self.assertEqual(checkkeys.finding_key(mistake)[0], "unit-nation-range")
        self.assertEqual(mistake.where, "rusemod.patch:_unit_rules")          # (past the _find helper)
        r = run((SECRET, [Op("clone", "$/X", source="$/Lee:Nationalite")]), game=named())
        key, cause = checkkeys.finding_key(r.errors[0])
        self.assertTrue(key and cause, (key, cause))
        self.assertNotIn(SECRET, key + cause)

    def test_an_unknown_text_keeps_its_place(self):
        f = Finding("error", "words no check of ours says")
        self.assertEqual(checkkeys.finding_key(f), (f.site, ""))
        self.assertTrue(f.where.endswith(":test_an_unknown_text_keeps_its_place"))

    def test_the_rmod_engine_s_error_and_a_caught_refusal_said_again(self):
        self.assertEqual(checkkeys.engine_check("DAT file not found: C:/Users/Nick/x.dat"),
                         entry(words="DAT file not found")["check"])
        self.assertEqual(checkkeys.engine_check("nothing the engine says"), "")
        from rusemod import rmod
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / f"{SECRET}.rmod"
            bad.write_text("not a mod", encoding="utf-8")
            try:
                rmod.check(bad)
            except BuildError as exc:
                again = Finding("error", str(exc))                       # as rmod.apply says it in the build's list
        self.assertEqual(again.cause, entry(words="can't be read as a .rmod mod")["check"])


def folders(root: Path) -> list[Path]:
    """A set of three: a mod from our list (its tags beside it), an own folder mod, an own .rmod file."""
    listed, own, rmodded = root / "cheat-mod-v2", root / SECRET, root / "nicks-rmod"
    for f in (listed, own, rmodded):
        f.mkdir(parents=True)
    (listed / "mod.toml").write_text('[mod]\nid = "cheat-mod-v2"\nname = "Cheat Mod"\nversion = "2.0.0"\n', "utf-8")
    (listed / "tags.toml").write_text('tags = ["cheat"]\n', "utf-8")
    (own / "mod.toml").write_text(f'[mod]\nid = "{SECRET}"\nname = "Nick\'s Secret Mod"\nversion = "1.0.0"\n', "utf-8")
    (rmodded / "mod.toml").write_text('[mod]\nid = "nicks-rmod"\nname = "x"\nversion = "1.0.0"\n\n[rmod]\n'
                                      'file = "Nicks.rmod"\n', "utf-8")
    (rmodded / "Nicks.rmod").write_text("{}", "utf-8")
    return [listed, own, rmodded]


class HowFarAPlayGot(unittest.TestCase):
    """A failed Play or Test in game says how far it got and which mods were on, and Bug Watch counts it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TEMP"))
        self.root = Path(self.tmp.name)
        self.game = self.root / "game"
        self.game.mkdir()
        self.instance = self.root / "copies" / "Modded game"
        self.home = self.root / "home"
        self.home.mkdir()
        self._on = bugwatch.ON
        bugwatch.ON = True
        os.environ.pop("RUSE_NO_BUGWATCH", None)
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._current = bugwatch.Watch(self.home, "launcher", "0.4.8.19", opener=mock.Mock())

    def tearDown(self):
        bugwatch.ON = self._on
        bugwatch._current = None
        self.tmp.cleanup()

    def play(self, mods, steam=True, **hooks):
        from rusemod.play import Starter
        starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: steam,
                          wait=lambda s: None)
        for name, hook in hooks.items():
            setattr(starter, name, hook)
        try:  # (not assertRaises: it drops the traceback, which says where the error came from)
            starter.modded(self.game, mods, self.instance, "test", lambda line: None)
        except Exception as exc:  # noqa: BLE001
            return exc
        self.fail("the Play went through")

    def counted(self, error) -> dict:
        bugwatch._current.job("play", False, 0.5, error, len(getattr(error, "errors", [])),
                              mistakes=getattr(error, "error_sites", []))
        return dict(bugwatch._current.days[bugwatch._today()]["messages"])

    def test_refused_before_any_build(self):
        error = self.play(folders(self.root / "mods"), owned=lambda game: "This copy isn't confirmed.")
        self.assertEqual((error.stage, error.mod_set), ("before", (["cheat-mod-v2@2.0.0"], 1, 1)))
        # (version 3 of the agreement accepted, or none: the player's own mods are one number, "O")
        self.assertEqual(self.counted(error), {"play:play_copy_not_confirmed": 1, "play:stage:before": 1,
                                               "play:set:L1-O2": 1, "play:lib:cheat-mod-v2:2.0.0": 1})

    def test_the_build_raised(self):
        empty = self.root / "mods" / "not-a-mod"
        empty.mkdir(parents=True)
        error = self.play([empty])
        self.assertIsInstance(error, BuildError)
        self.assertEqual(error.stage, "build")
        messages = self.counted(error)
        self.assertEqual(messages.pop("play:stage:build"), 1)
        self.assertEqual(messages.pop("play:set:L0-O1"), 1)
        (key, n), = messages.items()
        self.assertEqual(key, "play:" + entry(words="has no mod.toml")["check"])

    def test_the_build_listed_mistakes(self):
        e = entry("nation-models")
        found = [Finding("error", said(e["us"], *[f"{SECRET} Unit_Nicks_Tank"] * 12), where=e["where"]),
                 Finding("error", "words no check of ours says")]
        result = SimpleNamespace(errors=found, order=["cheat-mod-v2", SECRET])
        mods = folders(self.root / "mods")[:2]
        with mock.patch("rusemod.play.build_and_write", return_value=result), \
                mock.patch("rusemod.play.read_mods", return_value=[]):
            error = self.play(mods)
        self.assertEqual((error.stage, len(error.errors)), ("listed", 2))
        self.assertEqual(error.error_keys, [("nation-models", ""), (found[1].site, "")])
        messages = self.counted(error)
        self.assertEqual(messages, {"play:play.mods-have-mistakes": 1, "play:stage:listed": 1, "play:set:L1-O1": 1,
                                    "play:lib:cheat-mod-v2:2.0.0": 1, "mistake:nation-models": 1,
                                    f"mistake:{found[1].site}": 1})
        self.assertFalse(any(SECRET in k or "Nick" in k for k in messages))

    def test_the_game_didn_t_start(self):
        self.instance.mkdir(parents=True)
        (self.instance / PROGRAM).write_bytes(b"MZ")
        with mock.patch("rusemod.instance.needs_build", return_value=False):
            error = self.play([], steam=False)
        self.assertEqual(error.stage, "start")
        self.assertEqual(self.counted(error), {"play:play.steam-didnt-start": 1, "play:stage:start": 1,
                                               "play:set:L0-O0": 1})

    def test_under_version_4_the_own_mods_by_format_and_what_they_hold(self):
        """Version 4 of the agreement accepted ("what a player's own mods hold by kind and count"): the own mods by
        format and, for each kind of thing they hold, how many hold it; never a name, a word or a path of them."""
        homes.save_settings(self.home, {**homes.settings(self.home), "guard": {"terms": 4}})
        mods = folders(self.root / "mods")
        own = mods[1]
        (own / "src").mkdir()
        (own / "src" / "units.rndf").write_text("Nicks_Secret_Tank is clone $/GFX/Everything/Descriptor_Unit_M3_Lee\n"
                                                "(\n    ProductionPrice = [1, 1, 1, 1, 1]\n)\n", "utf-8")
        (own / "text").mkdir()
        (own / "text" / "baseunite.csv").write_text(f"key,us\n{SECRET},Nick's tank\n", "utf-8")
        (own / "scripts" / "m06_ardennes" / "scripting_chapter1").mkdir(parents=True)
        (own / "scripts" / "m06_ardennes" / "scripting_chapter1" / "effetmap.py").write_text("x = 1\n", "utf-8")
        error = self.play(mods, owned=lambda game: "This copy isn't confirmed.")
        self.assertEqual(error.own_holds, {"folder": 1, "rmod": 1, "data": 1, "new_objects": 1, "texts": 1,
                                           "scripts": 1})
        messages = self.counted(error)
        self.assertEqual(messages, {"play:play_copy_not_confirmed": 1, "play:stage:before": 1, "play:set:L1-F1-R1": 1,
                                    "play:lib:cheat-mod-v2:2.0.0": 1, "play:own:data": 1, "play:own:new_objects": 1,
                                    "play:own:texts": 1, "play:own:scripts": 1})
        self.assertFalse(any(SECRET in k or "Nick" in k or "ardennes" in k for k in messages))

    def test_a_play_the_launcher_refused_before_its_job_started(self):
        """The Launcher's own refusals before a Play's job starts (one already starting, a restore, no such set, a set
        with a mistake, an author not trusted) never reached Bug Watch: the job never started."""
        from ruse_launcher.api import LauncherApi
        api = LauncherApi(home=self.home, game_dir=self.root / "nowhere")
        job = api.play(f"{SECRET}-set")["job"]
        self.assertEqual(api.job(job)["state"], "failed")
        day = bugwatch._current.days[bugwatch._today()]
        self.assertEqual((day["jobs"]["play"]["failed"], day["jobs"]["play"]["errors"]), (1, {"Refused": 1}))
        self.assertEqual(day["messages"], {"play:play_no_set": 1})  # the call's name in front of a key (FL-97)

    def test_a_game_that_closed_at_once(self):
        ended = SimpleNamespace(poll=lambda: 0)
        for ran in (20, 200):
            times = iter([1000.0, 1000.0 + ran])
            watch = bugwatch.GameWatch(bugwatch._current, ended, [], 0, sleep=lambda s: None,
                                       clock=lambda: next(times), local=self.tmp.name)
            watch.run()
            self.assertEqual(bugwatch._current.days[bugwatch._today()]["messages"].get("game:closed-under-1-min", 0),
                             1, ran)


if __name__ == "__main__":
    unittest.main()
