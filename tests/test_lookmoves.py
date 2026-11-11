"""The unit page's Look and moves section (ui/app.js lookMovesBox) and the start screen without a new mod's steps
(ui/startflow.js).

The owner, 2026-11-11: "Make sure there's a clear path and workflow for someone to think about someone making a big mod
with lots of new units. It should be easy to work with rather than being difficult having to remember every little
step where to save it here and there"; "easy while at the same time still having the ability to be complex enough to
produce really cool things ... I'm not saying to have buttons layered inside buttons"; "Yes, start working on this";
and "Yes, in this patch, take the guided step out of the studio for now". Checks of the page's code (no browser here):
its rows in the order a modder works, a tooltip on every control, every word in the eleven languages and on the
stand-in page, no fold inside a row's More, every call the Studio's and the stand-in page's, the unit page built with
it (a building's page as before); the start screen's Start a new mod opening the Studio's own New mod box, and a new
mod's steps called from nowhere. RUSE Decoy's own_clips count is in test_decoy (OnlyThisUnit)."""
import re
import tomllib
import unittest
from pathlib import Path

from ruse_studio.api import StudioApi

UI = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
BLANK = re.compile(r"\{(\w+)\}")


def read(name: str) -> str:
    return (UI / name).read_text(encoding="utf-8")


def function_text(js: str, name: str) -> str:
    """A top-level function's text, to the next top-level function or const."""
    m = re.search(rf"^(?:async )?function {name}\(", js, re.M)
    if m is None:
        raise AssertionError(f"no function {name}")
    nxt = re.search(r"^(?:async function |function |const )", js[m.end():], re.M)
    return js[m.start(): m.end() + (nxt.start() if nxt else len(js) - m.end())]


def controls(js: str) -> list:
    """The option braces of every button, select and input the code makes."""
    out = []
    for m in re.finditer(r'el\("(?:button|input|select)", \{', js):
        depth, at = 0, m.end() - 1
        for at in range(m.end() - 1, len(js)):
            depth += {"{": 1, "}": -1}.get(js[at], 0)
            if depth == 0:
                break
        out.append(js[m.end():at])
    return out


class TheSection(unittest.TestCase):
    def setUp(self):
        self.app = read("app.js")
        self.section = function_text(self.app, "lookMovesBox") + function_text(self.app, "repaintBox") + \
            function_text(self.app, "kindImport")

    def rows(self) -> list:
        """LM_ROWS as (key, word, tip) triples."""
        rows = re.search(r"const LM_ROWS = (\[.*?\]\]);", self.app, re.S)
        self.assertIsNotNone(rows)
        return re.findall(r'\["(\w+)", "(\w+)", "(\w+)"\]', rows.group(1))

    def test_its_rows_in_the_order_a_modder_works(self):
        # (sounds and animations one row with one button since the owner's 11-11 "The sound and animation button should
        # be one button. I don't understand why it's two different things")
        self.assertEqual([k for k, _w, _t in self.rows()], ["model", "soldiers", "decoy", "rides"])
        self.assertEqual(self.section.count("decoyButton(d)"), 1)   # (one RUSE Decoy button on the section)

    def test_a_tooltip_on_every_control(self):
        made = controls(self.section)
        self.assertGreaterEqual(len(made), 10)
        self.assertEqual([c for c in made if "title" not in c], [])

    def test_every_word_in_eleven_languages_and_on_the_stand_in_page(self):
        words = tomllib.loads((UI.parent / "words.toml").read_text(encoding="utf-8"))
        fake = read("fake-api.js")
        used = set(re.findall(r"\bw\.(\w+)", self.section)) | {x for _k, word, tip in self.rows() for x in (word, tip)}
        self.assertGreater(len(used), 40)
        for key in sorted(used):
            with self.subTest(key=key):
                self.assertIn(key, words)
                self.assertEqual(set(words[key]), set(LANGS))
                for lang in LANGS:
                    self.assertTrue(words[key][lang].strip(), lang)
                    self.assertEqual(sorted(BLANK.findall(words[key][lang])), sorted(BLANK.findall(words[key]["us"])),
                                     lang)
        for key in sorted(k for k in used if re.fullmatch(r"(tip_)?lm_\w+", k)):
            self.assertIn(f'"{key}":', fake, key)   # (the stand-in page, index.html?fake, shows the words too)

    def test_no_fold_inside_a_row(self):
        # (not "buttons layered inside buttons": a row's More is the one fold; nothing under it folds again)
        for name in ("lookMovesBox", "repaintBox", "modelBox", "kindsBox", "fitBox", "halvesBox", "ownAnimationsBox",
                     "uniformBox"):
            self.assertNotIn('el("details"', function_text(self.app, name), name)
        actions = function_text(self.app, "unitActionsBox")
        self.assertIn('const fold = inRow ? el("div", { className: "unit-actions-more" }', actions)  # (folds on a building's page only)

    def test_every_call_is_the_studio_s_and_the_stand_in_page_s(self):
        fake = read("fake-api.js")
        calls = set(re.findall(r"api\(\)\.(\w+)\(", self.section))
        self.assertTrue({"look", "unit_actions", "decoy_unit", "rides_in", "rides_in_set", "model_import"} <= calls, calls)
        self.assertEqual(sorted(c for c in calls if not callable(getattr(StudioApi, c, None))), [])
        self.assertEqual(sorted(c for c in calls if not re.search(rf"\b{c}: async", fake)), [])
        self.assertIn("own_clips:", fake)

    def test_the_unit_page_is_built_with_it(self):
        show = function_text(self.app, "showUnit")
        self.assertIn("lookMovesBox(u, view, copyForm && copyForm.openForm)", show)
        # a building's page as before: its Look box, the sounds in its values' column
        self.assertIn("buildingLookBox(u, copyForm && copyForm.openForm)", show)
        self.assertIn("if ((u.named || u.new) && building) parts.push(unitSoundsGroup(u));", show)
        self.assertNotIn("function lookBox(", self.app)   # (the old Look box: its unit half is the Model row now)

    def test_import_model_is_the_model_row_s_button(self):
        self.assertIn("main = [model.pick];", self.section)
        model = function_text(self.app, "modelBox")
        self.assertNotIn("pick, drop)", model)    # (Import again is the row's button, not in the box under More)
        self.assertNotIn("kindsBox(", model)      # (a squad's soldiers by kind: their own row)
        self.assertNotIn("ownAnimationsBox(", model)   # (what came in with it: the Animations row)


class TheNationsTab(unittest.TestCase):
    """What only a new mod's steps offered, on the Nations tab since 2026-11-11 (the owner: "Yes, add those to nations
    tab"; "put a start nation and no research back"): each nation's Keep its units / Start it empty, and Research for
    the whole mod, with the steps' own names."""

    def setUp(self):
        self.js = read("nations.js")
        self.words = tomllib.loads((UI.parent / "words.toml").read_text(encoding="utf-8"))

    def test_each_nation_s_choice_whenever_a_mod_is_picked(self):
        self.assertIn("if (N.data && N.data.mod) head.append(keepOrEmpty(x, name));", self.js)
        self.assertNotIn("if (N.flow) head.append(keepOrEmpty", self.js)
        keep = function_text(self.js.replace("  function ", "function "), "keepOrEmpty")
        self.assertIn('[["keep", "flow_keep", "tip_nations_keep"], ["empty", "flow_empty", "tip_nations_empty"]]', keep)
        self.assertIn("const now = all && out === all ? \"empty\" : out === 0 ? \"keep\" : null;", keep)   # the mod's state
        self.assertIn("api().nation_units_hide(x.nation, empty, N.lang)", keep)

    def test_research_for_the_whole_mod_asked_first(self):
        box = function_text(self.js.replace("  function ", "function "), "researchBox")
        self.assertIn('act("research_clear_all", "nations_research_none_ask")', box)
        self.assertIn('act("research_reset_all", "nations_research_keep_ask")', box)
        self.assertIn("if (!window.confirm(w[ask])) return;", box)
        self.assertIn("textContent: w.flow_research_none", box)
        self.assertIn("textContent: w.flow_research_keep", box)
        self.assertIn('id="nations-research"', read("index.html"))

    def test_its_words_in_eleven_languages_and_on_the_stand_in_page(self):
        used = set(re.findall(r"\bw\.(\w+)", self.js)) | {"nations_research_none_ask", "nations_research_keep_ask",
                                                          "flow_keep", "flow_empty", "tip_nations_keep", "tip_nations_empty"}
        for key in sorted(used):
            with self.subTest(key=key):
                self.assertEqual(set(self.words[key]), set(LANGS))
                for lang in LANGS:
                    self.assertEqual(sorted(BLANK.findall(self.words[key][lang])),
                                     sorted(BLANK.findall(self.words[key]["us"])), lang)
        fake = read("fake-api.js")
        for key in ("tip_nations_keep", "tip_nations_empty", "nations_some_hidden", "nations_research_none_ask",
                    "nations_research_keep_ask"):
            self.assertIn(f'"{key}":', fake)
        self.assertIn("own: own.length, hidden: own.filter((a) => nationHidden.has(a)).length", fake)


class TheStartScreen(unittest.TestCase):
    def test_start_a_new_mod_opens_the_studio_s_own_new_mod_box(self):
        flow = read("startflow.js")
        self.assertIn('big("ss_new", "tip_ss_new", () => { closeStart(); pickMod({ target: { value: NEW } }, "mod"); }',
                      flow)
        self.assertIn('if (mods.length) choices.push(big("ss_carry"', flow)   # (the screen's other choices stay)
        self.assertIn('choices.push(big("ss_skip", "tip_ss_skip", closeStart, "ghost"));', flow)

    def test_a_new_mod_s_steps_are_called_from_nowhere(self):
        flow = read("startflow.js")
        calls = [m.start() for m in re.finditer(r"\bstartFlow\(", flow)]
        defined = flow.index("function startFlow(")
        self.assertEqual([c for c in calls if c != defined + len("function ")], [])   # (only its own definition)
        for path in UI.glob("*.js"):
            if path.name != "startflow.js":
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"startFlow\(", path.name)

    def test_its_tooltip_no_longer_speaks_of_steps(self):
        words = tomllib.loads((UI.parent / "words.toml").read_text(encoding="utf-8"))
        self.assertNotIn("step", words["tip_ss_new"]["us"].lower())
        self.assertEqual(set(words["tip_ss_new"]), set(LANGS))


if __name__ == "__main__":
    unittest.main()
