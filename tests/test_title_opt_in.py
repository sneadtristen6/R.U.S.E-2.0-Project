"""R.U.S.E. 2.0's title and intro: the game's own by default, on only by the player's own choice (the owner, 2026-11-24:
"Yes, they should see the game's own title in the first message that pops up with the new update when we're giving
them the notice, the guard stuff. Allow them to have a selectable point where hey, if you want to have the Ruse 2.0
screen, do this. Click this." and "Eugen's logo should now be shown by default, just like normal [R.U.S.E.] does, and
you can opt in the settings to turn on the [R.U.S.E.] 2.0 intro and gold font.").

- Both apps' Settings switch, called as their pages call it (rusemod.webui.page_api) on one scratch home: nothing saved,
  the older apps' "game", the opt-in's value, on then off, one choice for both apps; the switch drawn unticked unless
  the answer says on, by each page's own code (run in Node by tests/title_switch_in_node.mjs), and a change kept.
- `ruse build`: the game's own title unless --ruse20-title.
- The agreement screen (rusemod/sharedui/agreement.js, run in Node by tests/agreement_in_node.mjs, every call answered
  by the real Launcher's or Studio's API on a scratch home): the box unticked, its words and tooltip in the player's
  language; Accept working without it and leaving the choice as it is; the box ticked keeping the opt-in, for both
  apps; a failure to keep it never holding Accept up, and said (open() hands the app the line, which both apps show);
  an Accept that fails keeping nothing until it works; shown again (an earlier version accepted), the box starting as
  the player's choice is and only a change the player makes kept; today's players (version 4 accepted) shown the box
  once the agreement's version goes up (skipped, and said so, while it is still 4: PLAN Part 6 raises it).
- The words: the box's and the switch's in both apps, every language; the ones both apps share the same in both.

The runs in Node (the agreement screen's, the switch's) are skipped when no Node is found: RUSE_NODE names node.exe,
else node on the PATH, else the project's tools folder's (D:/RUSE-2.0/tools/node-v*).

FOR: the title opt-in (the owner, 2026-11-24). USED-BY: the test runs (gentle.py, -m unittest)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from rusemod import bugwatch, guard, schema, signature
from rusemod.home import save_settings, settings
from rusemod.webui import page_api

SRC = Path(__file__).resolve().parents[1] / "src"
AGREEMENT = SRC / "rusemod" / "sharedui" / "agreement.js"
SCREEN = Path(__file__).resolve().with_name("agreement_in_node.mjs")
APPS = ("ruse_launcher", "ruse_studio")
TMP = os.environ.get("RUSE_TEST_TMP") or None
WAIT = 300   # seconds the screen's whole run may take
# the box's English: proposed by an AI, the "general counsel" role-played in the 2026-11-24 legal-review workflow
# (scratch/legal-fixes-2026-11-24/wf1/partial/lawyer__general-counsel.json, item P4); not the owner's words (he gave
# none for it) nor a lawyer's. Whether he has seen it word for word: not known
BOX = "Use the R.U.S.E. 2.0 title and intro on this PC (otherwise the game's own title and Eugen's logo video)"
# the words both apps have the same: the box's, its line when it couldn't be kept, and the switch's heading and label
SHARED_KEYS = ("agree_ruse20", "tip_agree_ruse20", "agree_ruse20_failed", "set_title_title", "title_gold")
TODAY = 4   # the agreement's version the released apps ask for (rusemod.guard.TERMS_VERSION at 0.9.8.22, 6b265ec1)
SWITCH_KEYS = ("set_title_help", "title_on_note", "title_off_note", "tip_title_gold")


def node() -> str | None:
    """node.exe: RUSE_NODE, else on the PATH, else the project's own (D:/RUSE-2.0/tools/node-v*), else None."""
    named = os.environ.get("RUSE_NODE")
    if named and Path(named).is_file():
        return named
    found = shutil.which("node")
    if found:
        return found
    tools = Path("D:/RUSE-2.0/tools")
    own = sorted(tools.glob("node-v*/node.exe")) if tools.is_dir() else []
    return str(own[-1]) if own else None


NODE = node()


def toml_words(app: str) -> dict:
    return tomllib.loads((SRC / app / "words.toml").read_text(encoding="utf-8"))


def app_words(app: str, lang: str) -> dict:
    """The words the app hands its page in `lang` (its api.words), only the ones the agreement screen reads."""
    if app == "ruse_launcher":
        from ruse_launcher.api import words
    else:
        from ruse_studio.api import words
    js = AGREEMENT.read_text(encoding="utf-8")
    used = set(re.findall(r"\bw\.([a-z_0-9]+)", js))
    every = words(lang)
    return {k: every[k] for k in sorted(used) if k in every}


def switch_words(app: str, lang: str = "us") -> dict:
    """The words the app hands its page in `lang` (its api.words) for Settings' title switch."""
    if app == "ruse_launcher":
        from ruse_launcher.api import words
    else:
        from ruse_studio.api import words
    every = words(lang)
    return {k: every[k] for k in ("set_title_title", "title_gold") + SWITCH_KEYS}


class OnePC(unittest.TestCase):
    """Both apps on one scratch home (they share settings.json), each called as its page calls it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=TMP)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"

    def app(self, name: str, home: Path | None = None):
        home = home or self.home
        nowhere = self.root / "no game"
        if name == "ruse_launcher":
            from ruse_launcher.api import LauncherApi
            return page_api(LauncherApi(game_dir=nowhere, home=home, find=lambda: None, open_url=lambda url: None,
                                        start_game=lambda path: None, steam_running=lambda: True, wait=lambda s: None))
        from ruse_studio.api import StudioApi
        return page_api(StudioApi(index_path=self.root / "none.sqlite", game_dir=nowhere, find=lambda: None, home=home))


class TheSwitch(OnePC):
    def test_both_apps_start_with_the_games_own_title_and_share_one_choice(self):
        la, st = self.app("ruse_launcher"), self.app("ruse_studio")
        self.assertEqual((la.game_title(), st.game_title()), ({"ruse20": False}, {"ruse20": False}))
        self.assertEqual(la.set_game_title(True), {"ruse20": True})
        self.assertEqual(st.game_title(), {"ruse20": True})                  # the other app sees the same choice
        self.assertEqual(settings(self.home)[signature.SETTING], signature.ON)
        self.assertEqual(st.set_game_title(False), {"ruse20": False})      # on, then off again
        self.assertEqual(la.game_title(), {"ruse20": False})
        self.assertEqual(settings(self.home)[signature.SETTING], "game")

    def test_what_the_older_apps_saved_is_the_games_own_title(self):
        # before this update: nothing saved was the gold title (the old default), "game" the switch unticked; both are
        # the game's own title now, for everyone, until the player ticks it
        for saved in ({"lang": "fr"}, {signature.SETTING: "game"}):
            with self.subTest(saved=saved):
                save_settings(self.home, saved)
                for name in APPS:
                    self.assertEqual(self.app(name).game_title(), {"ruse20": False}, name)

    def test_the_switch_is_drawn_unticked_unless_the_answer_says_on(self):
        # (a missing or unread answer never shows it ticked: the Launcher draws it before the answer comes)
        for app in APPS:
            js = (SRC / app / "ui" / "app.js").read_text(encoding="utf-8")
            self.assertNotIn("ruse20 !== false", js, app)
            self.assertIn("ruse20 === true", js, app)

    def test_each_pages_own_switch_is_ticked_only_when_on_and_keeps_a_change(self):
        # the pages' own code (tests/title_switch_in_node.mjs: the Launcher's loadTitle, renderTitle and changeTitle,
        # the Studio's Settings entry "title"), given each answer game_title() can give, then the player's change
        if NODE is None:
            self.skipTest("no Node found (RUSE_NODE, the PATH, the project's tools folder)")
        said = {"launcher": switch_words("ruse_launcher"), "studio": switch_words("ruse_studio")}
        cases = [  # (app, game_title's answer or None for an error, the player's change or None, what's drawn)
            *[(app, answer, None, ticked) for app in ("launcher", "studio")
              for answer, ticked in (({"ruse20": True}, True), ({"ruse20": False}, False), ({}, False),
                                     ({"ruse20": "yes"}, False), (None, False))],
            *[(app, {"ruse20": not on}, on, not on) for app in ("launcher", "studio") for on in (True, False)],
        ]
        given = Path(tempfile.mkdtemp(dir=TMP))
        self.addCleanup(shutil.rmtree, given, True)
        (given / "cases.json").write_text(json.dumps([{"app": app, "words": said[app], "answer": answer,
                                                        **({} if change is None else {"change": change})}
                                                       for app, answer, change, _t in cases]), encoding="utf-8")
        run = subprocess.run([NODE, str(Path(__file__).resolve().with_name("title_switch_in_node.mjs")),
                              str(SRC / "ruse_launcher" / "ui" / "app.js"), str(SRC / "ruse_studio" / "ui" / "app.js"),
                              str(given / "cases.json")], capture_output=True, text=True, encoding="utf-8",
                             timeout=WAIT)
        self.assertEqual(run.returncode, 0, run.stderr)
        results = json.loads(run.stdout)
        self.assertEqual(len(results), len(cases))
        for (app, answer, change, ticked), got in zip(cases, results):
            with self.subTest(app=app, answer=answer, change=change):
                self.assertNotIn("error", got, got.get("error"))
                self.assertIs(got["checked"], ticked)
                self.assertEqual(got["calls"][0], ["game_title", []])
                if app == "launcher":   # (not read yet, or an error: off and not to be changed, the error said)
                    self.assertIs(got["disabled"], not isinstance(answer, dict) or "ruse20" not in answer)
                    if answer is None:
                        self.assertEqual((got["note"], got["note_class"]),
                                         ("game_title failed (the test's)", "message bad"))
                elif answer is None:
                    self.assertEqual(got["problems"], ["render: game_title failed (the test's)"])
                if change is not None:
                    self.assertEqual(got["calls"][1:], [["set_game_title", [change]]])
                    self.assertIs(got["after"]["checked"], change)
                    note = said[app]["title_on_note" if change else "title_off_note"]
                    self.assertEqual((got["after"]["note"], got["after"]["note_class"]),
                                     (note, "message good" if app == "launcher" else "small good"))
                else:
                    self.assertEqual(len(got["calls"]), 1)


class TheCommandLine(unittest.TestCase):
    def test_a_copy_gets_the_games_own_title_unless_asked(self):
        from rusemod import cli
        from test_build import PACK, write_mod
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            game = Path(d) / "game"
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            mod = write_mod(d, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
            copy = ["--instance", str(Path(d) / "copy")]
            for given, want in (([*copy], False), ([*copy, "--ruse20-title"], True), ([*copy, "--game-title"], False),
                                ([*copy, "--ruse20-title", "--game-title"], False),
                                (["--out", str(Path(d) / "packs"), "--ruse20-title"], False)):   # (no copy, no title)
                with self.subTest(given=given), mock.patch.object(cli, "build_and_write") as built:
                    built.return_value.errors = []
                    self.assertEqual(cli.main(["--game", str(game), "build", str(mod), *given]), 0)
                    self.assertIs(built.call_args.kwargs["signature"], want)


class TheWords(unittest.TestCase):
    def test_every_language_in_both_apps_and_the_shared_ones_the_same(self):
        launcher, studio = toml_words("ruse_launcher"), toml_words("ruse_studio")
        for key in SHARED_KEYS + SWITCH_KEYS:
            for app, words in (("launcher", launcher), ("studio", studio)):
                with self.subTest(app=app, key=key):
                    self.assertEqual(sorted(words[key]), sorted(schema.APP_LANGS))
                    self.assertEqual([lang for lang, text in words[key].items() if not text.strip()], [])
        for key in SHARED_KEYS:
            self.assertEqual(launcher[key], studio[key], key)
        self.assertEqual(launcher["agree_ruse20"]["us"], BOX)
        # the line when the box couldn't be kept: says where to change it, by the switch's own words, every language
        for lang, line in launcher["agree_ruse20_failed"].items():
            with self.subTest(lang=lang):
                self.assertIn("R.U.S.E. 2.0", line)
                self.assertIn(launcher["set_title_title"][lang], line)
                if lang != "us":
                    self.assertNotEqual(line, launcher["agree_ruse20_failed"]["us"])

    def test_the_switch_says_it_is_off_until_ticked_and_names_eugens_logo_video(self):
        for app in APPS:
            words = toml_words(app)
            for key in ("set_title_help", "tip_title_gold"):
                english = words[key]["us"]
                self.assertIn("off unless you tick it", english, f"{app} {key}")
                self.assertNotIn("Untick", english, f"{app} {key}")
            self.assertEqual(words["title_gold"]["us"], "Use the gold R.U.S.E. 2.0 title and intro")
            # every language names the logo video the game keeps (Eugen's), the box's words and the switch's
            for key in ("agree_ruse20", "set_title_help", "title_off_note", "tip_title_gold"):
                for lang, text in words[key].items():
                    self.assertIn("Eugen", text, f"{app} {key} {lang}")
                    self.assertIn("R.U.S.E.", text, f"{app} {key} {lang}")
                    if lang != "us":
                        self.assertNotEqual(text, words[key]["us"], f"{app} {key} {lang}: English left in")

    def test_the_box_is_written_unticked_and_apart_from_accept(self):
        # (what it starts as and what Accept keeps: TheAgreementBox, the screen's own code run)
        js = AGREEMENT.read_text(encoding="utf-8")
        self.assertIn('<input id="agree-ruse20" type="checkbox">', js)    # no "checked" in its markup
        self.assertEqual(js.count('<button id="agree-'), 1)                 # Accept is still the one button

    def test_both_apps_say_the_line_when_the_box_could_not_be_kept(self):
        # open() hands it over ({problem}: TheAgreementBox); each app says it where it says its problems
        for app, says in (("ruse_launcher", 'setMessage(agreed.problem, "bad")'),
                          ("ruse_studio", 'say(agreed.problem, "error")')):
            js = (SRC / app / "ui" / "app.js").read_text(encoding="utf-8")
            self.assertIn("const agreed = await window.Agreement.open(", js, app)
            self.assertIn(f"if (agreed && agreed.problem) {says};", js, app)


class TheAgreementBox(OnePC):
    """The agreement screen's own code in Node, each call answered by the app's real API on the case's own home."""

    def screen(self, cases: list) -> dict:
        """Run `cases` on the screen: each {"name", "app": ruse_launcher or ruse_studio, "lang", "home", "tick",
        "untick", "accept": clicks, "fail": {call: how many of its first calls fail}, "words": the words to give the
        screen (else the app's in "lang")}; {name: agreement_in_node.mjs's "out"}."""
        if NODE is None:
            self.skipTest("no Node found (RUSE_NODE, the PATH, the project's tools folder)")
        by_name = {c["name"]: c for c in cases}
        apis = {c["name"]: self.app(c["app"], c["home"]) for c in cases}
        failing = {c["name"]: dict(c.get("fail") or {}) for c in cases}
        given = self.root / "scenario.json"
        given.write_text(json.dumps({"cases": [{"name": c["name"],
                                                "words": c.get("words") or app_words(c["app"], c.get("lang", "us")),
                                                "tick": bool(c.get("tick")), "untick": bool(c.get("untick")),
                                                "accept": c.get("accept", 1)}
                                               for c in cases]}, ensure_ascii=False), encoding="utf-8")
        errors = self.root / "node-errors.txt"
        out, current = {}, None
        with open(errors, "w", encoding="utf-8") as err:
            proc = subprocess.Popen([NODE, str(SCREEN), str(AGREEMENT), str(given)], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=err, text=True, encoding="utf-8")
            timer = threading.Timer(WAIT, proc.kill)
            timer.start()
            try:
                for line in proc.stdout:
                    m = json.loads(line)
                    reply = {"ok": True}
                    if "begin" in m:
                        current = m["begin"]
                    elif "call" in m:
                        left = failing[current].get(m["call"], 0)
                        if left:
                            failing[current][m["call"]] = left - 1
                            reply = {"error": f"{m['call']} failed (the test's)"}
                        else:
                            try:
                                value = getattr(apis[current], m["call"])(*m["args"])
                                reply = {"value": json.loads(json.dumps(value, default=str))}
                            except Exception as exc:  # (a call the app hasn't got: an error on the page, as there)
                                reply = {"error": str(exc)}
                    elif "end" in m:
                        out[m["end"]] = m["out"]
                    proc.stdin.write(json.dumps({"id": m["id"], **reply}) + "\n")
                    proc.stdin.flush()
                    if m.get("done"):
                        break
                proc.wait(timeout=WAIT)
            finally:
                timer.cancel()
                if proc.poll() is None:
                    proc.kill()
                    proc.wait()
                for f in (proc.stdin, proc.stdout):
                    try:
                        f.close()
                    except OSError:
                        pass
        said = errors.read_text(encoding="utf-8")
        self.assertEqual(proc.returncode, 0, said)
        self.assertEqual(sorted(out), sorted(by_name), said)
        for name, o in out.items():
            self.assertNotIn("error", o, f"{name}: {o.get('error')}\n{said}")
        return out

    def a_home(self, name: str) -> Path:
        return self.root / "homes" / name

    def earlier(self, name: str, title: bool | None, version: int | None = None) -> Path:
        """A home whose player accepted an earlier version of the agreement (`version`, else the one before this
        one), with a username, and R.U.S.E. 2.0's title on (True), turned off ("game": False) or never chosen (None,
        the old default)."""
        home = self.a_home(name)
        bugwatch.set_username(home, "Nick")
        values = settings(home)
        values["guard"] = {"terms": guard.TERMS_VERSION - 1 if version is None else version}
        save_settings(home, values)
        if title is not None:
            signature.keep_title(home, title)
        return home

    def assert_shown(self, o: dict, app: str, lang: str = "us", ticked: bool = False) -> None:
        words = app_words(app, lang)
        self.assertTrue(o["shown"]["agree"])
        self.assertEqual(o["shown"]["box"], {"type": "checkbox", "checked": ticked, "disabled": False,
                                             "title": words["tip_agree_ruse20"]})
        self.assertEqual(o["shown"]["row_title"], words["tip_agree_ruse20"])   # (the tooltip over its words too)
        self.assertTrue(o["shown"]["row_shown"])
        self.assertEqual(o["shown"]["label"], words["agree_ruse20"])
        self.assertTrue(o["finished"])
        self.assertEqual((o["agree_shown"], o["username_shown"]), (False, False))

    def assert_shown_unticked(self, o: dict, app: str, lang: str = "us") -> None:
        self.assert_shown(o, app, lang, ticked=False)

    @staticmethod
    def kept(o: dict) -> list:
        """What set_game_title was called with, call by call."""
        return [args for name, args in o["made"] if name == "set_game_title"]

    def test_unticked_accept_works_and_the_title_stays_the_games_own(self):
        cases = [{"name": app, "app": app, "home": self.a_home(app)} for app in APPS]
        out = self.screen(cases)
        for app in APPS:
            with self.subTest(app=app):
                o, home = out[app], self.a_home(app)
                self.assert_shown_unticked(o, app)
                self.assertEqual(o["shown"]["label"], BOX)
                self.assertIn("guard_accept_terms", o["calls"])
                self.assertNotIn("set_game_title", o["calls"])
                self.assertEqual(o["result"], {"problem": ""})   # (nothing for the app to say)
                self.assertEqual(settings(home)["guard"]["terms"], guard.TERMS_VERSION)
                self.assertTrue(settings(home)["player"]["name"].startswith("Tester#"))   # (the username asked)
                self.assertNotIn(signature.SETTING, settings(home))   # nothing saved: the game's own
                self.assertFalse(signature.title_on(home))
                for other in APPS:
                    self.assertEqual(self.app(other, home).game_title(), {"ruse20": False})

    def test_ticked_it_turns_the_title_on_for_both_apps(self):
        cases = [{"name": app, "app": app, "home": self.a_home(app), "tick": True} for app in APPS]
        out = self.screen(cases)
        for app in APPS:
            with self.subTest(app=app):
                o, home = out[app], self.a_home(app)
                self.assert_shown_unticked(o, app)   # (unticked when shown; the player ticked it)
                calls = o["calls"]
                self.assertEqual(self.kept(o), [[True]])
                self.assertLess(calls.index("guard_accept_terms"), calls.index("set_game_title"))   # after Accept
                self.assertEqual(o["result"], {"problem": ""})
                self.assertEqual(settings(home)["guard"]["terms"], guard.TERMS_VERSION)
                self.assertEqual(settings(home)[signature.SETTING], signature.ON)
                self.assertTrue(signature.title_on(home))
                for other in APPS:   # Settings in either app shows it on
                    self.assertEqual(self.app(other, home).game_title(), {"ruse20": True})

    def test_a_failure_to_keep_it_never_holds_accept_up_and_is_said(self):
        # the tick couldn't be kept: Accept still worked, the username was still asked, and open() hands the app the
        # line to say in the player's language (its words), or the error itself if the words haven't got it, so the
        # player's choice is never lost unsaid; Settings can still turn it on
        cases = [{"name": f"{app} {lang}", "app": app, "lang": lang, "home": self.a_home(f"fails-{app}-{lang}"),
                  "tick": True, "fail": {"set_game_title": 9}}
                 for app, lang in (("ruse_launcher", "us"), ("ruse_studio", "fr"), ("ruse_launcher", "fa"))]
        no_line = {k: v for k, v in app_words("ruse_studio", "us").items() if k != "agree_ruse20_failed"}
        cases.append({"name": "older words", "app": "ruse_studio", "home": self.a_home("fails-older"), "tick": True,
                      "words": no_line, "fail": {"set_game_title": 9}})
        out = self.screen(cases)
        for c in cases:
            with self.subTest(case=c["name"]):
                o, home = out[c["name"]], c["home"]
                self.assertTrue(o["finished"])
                self.assertEqual(self.kept(o), [[True]])
                self.assertEqual(settings(home)["guard"]["terms"], guard.TERMS_VERSION)
                self.assertIn("name", settings(home)["player"])   # and on to the username, as without the box
                self.assertFalse(signature.title_on(home))         # (Settings can still turn it on)
                line = app_words(c["app"], c.get("lang", "us"))["agree_ruse20_failed"] if "words" not in c \
                    else "set_game_title failed (the test's)"
                self.assertEqual(o["result"], {"problem": line})
                if c.get("lang", "us") != "us":
                    self.assertNotEqual(line, app_words(c["app"], "us")["agree_ruse20_failed"])

    def test_an_accept_that_fails_keeps_nothing_until_it_works(self):
        home = self.a_home("again")
        out = self.screen([{"name": "again", "app": "ruse_studio", "home": home, "tick": True, "accept": 2,
                            "fail": {"guard_accept_terms": 1}}])
        o, calls = out["again"], out["again"]["calls"]
        self.assertEqual(calls.count("guard_accept_terms"), 2)
        self.assertEqual(calls.count("set_game_title"), 1)
        accepted = max(i for i, call in enumerate(calls) if call == "guard_accept_terms")   # (the one that worked)
        self.assertGreater(calls.index("set_game_title"), accepted)
        self.assertTrue(o["finished"])
        self.assertTrue(o["box_after"])   # (the tick stayed through the failed Accept)
        self.assertTrue(signature.title_on(home))

    def test_shown_again_the_box_starts_as_the_choice_is_and_only_a_change_is_kept(self):
        # a player who accepted an earlier version: the screen shows again (his username stays), the box as his
        # choice is (ticked only if he turned the title on, in Settings or on that earlier screen), so it says what
        # accepting leaves on, as the Bug Watch box does; Accept with it as shown keeps his choice without a call,
        # and a box he changed is kept, on or off
        cases = [  # (name, the title before: True on, False "game", None nothing saved; what he does; on after)
            ("on, left ticked", True, {}, True),
            ("on, unticked", True, {"untick": True}, False),
            ("game, left unticked", False, {}, False),
            ("game, ticked", False, {"tick": True}, True),
            ("nothing saved, left unticked", None, {}, False),
            ("nothing saved, ticked", None, {"tick": True}, True),
        ]
        for name, before, does, _after in cases:
            app = "ruse_studio" if "game" in name else "ruse_launcher"
            does.update({"name": name, "app": app, "home": self.earlier(name.replace(",", ""), before)})
        out = self.screen([does for _n, _b, does, _a in cases])
        for name, before, does, after in cases:
            with self.subTest(case=name):
                o, home = out[name], does["home"]
                self.assert_shown(o, does["app"], ticked=before is True)
                self.assertNotIn("set_username", o["calls"])   # (his username stays)
                changed = does.get("tick", False) or does.get("untick", False)
                self.assertEqual(self.kept(o), [[after]] if changed else [])
                if changed:
                    self.assertLess(o["calls"].index("guard_accept_terms"), o["calls"].index("set_game_title"))
                self.assertIs(signature.title_on(home), after)
                self.assertEqual(o["result"], {"problem": ""})
                self.assertEqual(settings(home)["guard"]["terms"], guard.TERMS_VERSION)

    def test_a_choice_that_cannot_be_read_starts_the_box_unticked_and_keeps_only_a_tick(self):
        # game_title() failed when the screen opened: the box starts unticked, so Accept as shown keeps the choice
        # as it was (on stays on), and a tick still turns the title on
        cases = [{"name": "on, not read", "app": "ruse_launcher", "home": self.earlier("on-not-read", True),
                  "fail": {"game_title": 1}},
                 {"name": "new, not read, ticked", "app": "ruse_studio", "home": self.a_home("new-not-read"),
                  "tick": True, "fail": {"game_title": 1}}]
        out = self.screen(cases)
        for c in cases:
            with self.subTest(case=c["name"]):
                o = out[c["name"]]
                self.assertIn("game_title", o["calls"])
                self.assert_shown_unticked(o, c["app"])
                self.assertEqual(self.kept(o), [[True]] if c.get("tick") else [])
                self.assertTrue(signature.title_on(c["home"]))
                self.assertEqual(o["result"], {"problem": ""})

    def test_todays_players_are_shown_the_box_with_the_update(self):
        # the owner, 2026-11-24: "they should see the game's own title in the first message that pops up with the
        # new update": a player who accepted today's version (4) has the screen again only once the agreement's
        # version goes up (PLAN Part 6, version 5, in the same release); then he sees the box unticked, whatever
        # today's apps saved (nothing: the gold title, their default; "game": unticked), and only a tick turns it on
        if guard.TERMS_VERSION <= TODAY:
            self.skipTest(f"the agreement is still version {guard.TERMS_VERSION}: a player who accepted version "
                          f"{TODAY} isn't shown the screen, so not the box either, until PLAN Part 6 raises it")
        cases = [{"name": f"{TODAY}, {saved}, {'ticked' if tick else 'unticked'}", "app": app,
                  "home": self.earlier(f"today-{saved}-{tick}", None if saved == "nothing" else False, TODAY),
                  "tick": tick}
                 for saved, app in (("nothing", "ruse_launcher"), ("game", "ruse_studio")) for tick in (False, True)]
        out = self.screen(cases)
        for c in cases:
            with self.subTest(case=c["name"]):
                o = out[c["name"]]
                self.assert_shown_unticked(o, c["app"])
                self.assertEqual(self.kept(o), [[True]] if c["tick"] else [])
                self.assertIs(signature.title_on(c["home"]), c["tick"])
                self.assertEqual(settings(c["home"])["guard"]["terms"], guard.TERMS_VERSION)

    def test_the_box_in_every_language(self):
        cases = [{"name": f"{app} {lang}", "app": app, "lang": lang, "home": self.a_home(f"{app}-{lang}")}
                 for app in APPS for lang in schema.APP_LANGS]
        out = self.screen(cases)
        english = app_words("ruse_launcher", "us")
        for c in cases:
            with self.subTest(case=c["name"]):
                o = out[c["name"]]
                self.assert_shown_unticked(o, c["app"], c["lang"])
                if c["lang"] != "us":
                    self.assertNotEqual(o["shown"]["label"], english["agree_ruse20"])
                    self.assertNotEqual(o["shown"]["box"]["title"], english["tip_agree_ruse20"])
                self.assertFalse(signature.title_on(c["home"]))


if __name__ == "__main__":
    unittest.main()
