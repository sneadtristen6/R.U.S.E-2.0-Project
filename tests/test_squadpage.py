"""A squad's page starts with its soldiers (ui/squad.js, app.js showUnit and lookMovesBox; the squad contracts' section 4,
2026-11-11). The owner, of the page before: "so stupidly laid out", "a ton of scrolling", "squint down at this tiny
text", "so many things that say change it in Blender, bring back the model. It's overwhelming"; who it is for: someone
"not very good with computers", "an older person", who wants to "change the whole squad at once ... or be able to
change each one individually"; his "Yes, it matches" to the contracts' list.

Checks of the page's code (no browser here, as tests/test_lookmoves.py does it): the squad card at the top with ONE
Blender button that reads Bring my changes back while its Blender is open; a line per soldier with Import a model… and
Back to the game's look; a tooltip on every control; every word in the eleven languages, word for word on the stand-in
page, the buttons a sentence names named as they are, no code names, nothing smaller than the page's normal text on
the card; Add a soldier and Remove only when the Studio says a squad can; a unit that isn't a squad, or a Studio without
squad_info, drawn as before; the stand-in page's answers shaped as the contracts' section 4; and, once the Studio's own
calls are joined, their parameters as the contracts name them."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import inspect
import json
import re
import tomllib
import unittest
from pathlib import Path

from ruse_studio.api import StudioApi
from test_lookmoves import BLANK, LANGS, controls, function_text, read

UI = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"
WORDS = UI.parent / "words.toml"
# the Studio's calls the page draws (the contracts' section 4): Phase 1's (agent B's), and a later step's (agent D's);
# the squad's own Blender pair (squad_blender, squad_blender_back) since 2026-11-13 behind the one Blender button
# (ruse_studio.oneblender: blender_parts, blender_open, blender_back; the owner: "Why is there two different buttons
# doing the same thing")
PHASE1 = {"squad_info": ["address", "lang"], "blender_parts": ["address", "lang"],
          "blender_open": ["address", "ticks", "lang"], "blender_back": ["address", "lang"],
          "soldier_import": ["address", "soldier", "file", "size"], "soldier_reset": ["address", "soldier"]}
LATER = {"soldier_add": ["address", "source", "of", "unit", "file"], "soldier_remove": ["address", "soldier"],
         "soldier_plus": ["address"], "soldier_minus": ["address"]}   # (−1 and +1: the owner, 2026-11-12)


def inner(js: str, name: str) -> str:
    """A function's text inside squad.js's section(): `const name = ... => {` to the next line at the same depth."""
    m = re.search(rf"^( +)const {name} = (?:async )?\(", js, re.M)
    if m is None:
        raise AssertionError(f"no {name} in squad.js")
    end = re.search(rf"^{m.group(1)}}};$", js[m.end():], re.M)
    return js[m.start(): m.end() + end.end()]


class TheWords(unittest.TestCase):
    def setUp(self):
        self.squad, self.app = read("squad.js"), read("app.js")
        self.words = tomllib.loads(WORDS.read_text(encoding="utf-8"))
        self.used = set(re.findall(r"\bw\.(\w+)", self.squad)) | \
            set(re.findall(r"\bw\.((?:tip_)?squad_\w+)", self.app))

    def test_every_word_of_the_page_in_eleven_languages(self):
        self.assertGreater(len(self.used), 70)
        for key in sorted(self.used):
            with self.subTest(key=key):
                self.assertIn(key, self.words)
                self.assertEqual(set(self.words[key]), set(LANGS))
                for lang in LANGS:
                    text = self.words[key][lang]
                    self.assertTrue(text.strip(), lang)
                    self.assertEqual(sorted(BLANK.findall(text)), sorted(BLANK.findall(self.words[key]["us"])), lang)
        # (its own words start squad_ or tip_squad_; every one of them is used, none left behind)
        own = {k for k in self.words if re.fullmatch(r"(tip_)?squad_\w+", k)}
        self.assertEqual(sorted(own - self.used), [])

    def test_its_words_word_for_word_on_the_stand_in_page(self):
        fake = read("fake-api.js")
        for key in sorted(k for k in self.used if re.fullmatch(r"(tip_)?squad_\w+", k)):
            for lang in ("us", "fr", "sc"):
                with self.subTest(key=key, lang=lang):
                    self.assertIn(f'"{key}": {json.dumps(self.words[key][lang], ensure_ascii=False)}', fake)

    def test_no_code_names_and_no_long_dashes(self):
        # (the brief: no "fusilier", "kind", ".glb", "NeedModelChange" on the page)
        for key in sorted(k for k in self.words if re.fullmatch(r"(tip_)?squad_\w+", k)):
            for lang in LANGS:
                text = self.words[key][lang]
                with self.subTest(key=key, lang=lang):
                    self.assertNotRegex(text, r"(?i)\.glb\b|fusilier\b|NeedModelChange|Descriptor_|\bbazooka@")
                    self.assertNotRegex(text, "[–—]")
            self.assertNotRegex(self.words[key]["us"], r"\bkinds?\b", key)

    def test_a_sentence_names_each_button_as_it_is(self):
        names = {  # a sentence, and the words of the buttons (and boxes) it names
            "squad_blender_open_how": ("blender_model_send", "squad_blender_back"),
            "squad_blender_opened": ("blender_model_send", "squad_blender_back"),
            "tip_squad_blender_back_closed": ("blender_model_send",),
            "squad_back_none": ("blender_model_send",), "squad_back_some": ("test_in_game",),
            "squad_back_all": ("test_in_game",), "squad_import_done": ("test_in_game",),
            "tip_squad_import": ("test_in_game",), "tip_squad_import_all": ("test_in_game",),
            "squad_blender_needs": ("look_get_blender", "look_choose_blender"),
            # (the one Blender button, Open in Blender, and its Bring my changes back)
            "tip_squad_folder_none": ("squad_import", "look_open"), "tip_squad_blender_folder_none": ("look_open",),
            "tip_one_open": ("squad_blender_back",), "tip_one_parts": ("squad_blender_back",),
            "one_how_model": ("squad_blender_back",),
            "squad_uniform_own_model": ("squad_reset",), "tip_squad_uniform_custom_own_model": ("squad_reset",),
            "squad_both": ("uniform_default_again", "uniform_title", "squad_reset", "test_in_game"),
            "squad_more_bones": ("squad_import",),
            "squad_add_opened": ("blender_model_send", "squad_blender_back"), "squad_minus_kept": ("squad_more",)}
        for key, labels in names.items():
            for lang in LANGS:
                for label in labels:
                    with self.subTest(key=key, lang=lang, label=label):
                        self.assertIn(self.words[label][lang], self.words[key][lang])

    def test_the_card_s_text_is_no_smaller_than_the_page_s(self):
        css = read("style.css")
        normal = int(re.search(r"html, body \{[^}]*font: (\d+)px", css).group(1))
        self.assertEqual(normal, 14)
        for selector in (".squad-words", ".squad-line", ".squad-go button", ".squad-go button.squad-big", ".squad-how",
                         ".squad-result", ".squad-who", ".squad-who strong", ".squad-now", ".squad-acts button",
                         ".squad-each"):
            with self.subTest(selector=selector):
                rule = re.search(rf"^{re.escape(selector)} \{{([^}}]*)\}}", css, re.M)
                self.assertIsNotNone(rule)
                self.assertGreaterEqual(int(re.search(r"font-size: (\d+)px", rule.group(1)).group(1)), normal)
        # (the card's own small print, its 3D view's hint and Use this view as the card, at the page's size there)
        self.assertIn(".squad-picture .unit-view .hint, .squad-picture .small, .squad-picture h2 { font-size: 14px; }", css)


class ThePage(unittest.TestCase):
    def setUp(self):
        self.squad, self.app = read("squad.js"), read("app.js")

    def test_a_tooltip_on_every_control(self):
        made = controls(self.squad) + controls(function_text(self.app, "uniformBox"))
        self.assertGreaterEqual(len(made), 15)
        self.assertEqual([c for c in made if "title" not in c], [])

    def test_squad_js_comes_after_app_js(self):
        page = read("index.html")
        self.assertLess(page.index('<script src="app.js"></script>'), page.index('<script src="squad.js"></script>'))
        self.assertIn("window.SquadView = { infoOf, section };", self.squad)

    def test_one_big_blender_button(self):
        # the one Blender button (the owner, 2026-11-13: one button, "select which ones you want to bring into Blender")
        big = inner(self.squad, "blenderParts")
        self.assertIn("textContent: open ? w.squad_blender_back : w.look_open, "
                      "title: open ? w.tip_one_back : w.tip_one_open", big)
        self.assertIn('big.addEventListener("click", open ? bringBack : openBlender);', big)
        self.assertIn("const open = Boolean(info.blender && info.blender.open) || Boolean(S.parts && S.parts.open);", big)
        # What goes to Blender beside it while it opens, its ticks kept when the card is drawn again
        self.assertIn("S.ticks = !open && S.parts && S.parts.can ? oneBlenderTicks(S.parts, S.ticks ? S.ticks.ticks() "
                      ": null) : null;", big)
        opening = inner(self.squad, "openBlender")
        self.assertIn("api().blender_open(address, ticks, state.lang)", opening)
        # (the ticks read before the card is drawn again: a redraw had ticked everything again, so an unticked part
        # went to Blender all the same; found on the stand-in page, 2026-11-13)
        self.assertLess(opening.index("S.ticks.ticks()"), opening.index("drawCard();"))
        # (only the squad's own Blender answers with squad_info: the model's, the Generic Horse's, answers with the
        # unit's look, which has soldiers too; taken as the squad's, the card's redraw threw, 2026-11-13)
        self.assertIn('if (r && r.door === "squad" && r.soldiers) S.info = r;', opening)
        self.assertNotIn("if (r && r.soldiers) S.info = r;", opening)
        self.assertIn("api().blender_back(address, state.lang)", inner(self.squad, "bringBack"))
        self.assertNotRegex(self.squad, r"api\(\)\.squad_blender")
        # who changed and who didn't, said plainly on the card
        back = inner(self.squad, "bringBack")
        self.assertIn("const changed = r.changed || [], same = r.unchanged || [];", back)
        for word in ("w.squad_back_none", "w.squad_back_some", "w.squad_back_all"):
            self.assertIn(word, back)
        # no other Blender button on a squad's page: none in squad.js, and its Look and moves row keeps only its uniform
        self.assertNotRegex(self.squad, r"api\(\)\.model_blender")
        look = function_text(self.app, "lookMovesBox")
        branch = look[look.index("if (squadPage) {"):look.index("const more = [];")]
        self.assertIn("[uniformBox(address, info, drawLook, changed, true)]", branch)
        self.assertNotIn("modelBox(", branch)
        self.assertNotIn("kindsBox(", branch)
        self.assertIn('hide("soldiers");', branch)

    def test_a_line_per_soldier(self):
        line = inner(self.squad, "soldierLine")
        self.assertIn("textContent: w.squad_import", line)
        self.assertIn("if (can.reset && s.own_model) {", line)
        self.assertIn("textContent: w.squad_reset", line)
        self.assertIn("api().soldier_import(address, s.id)", inner(self.squad, "importFor"))
        reset = inner(self.squad, "resetOf")
        self.assertIn("api().soldier_reset(address, s.id)", reset)
        # what went with it said as the page always has: kinds_out, and a Custom uniform that came back
        self.assertIn("r.kinds_out", reset)
        self.assertIn('fill(w.model_kinds_out, { who: gone.join(", ") })', reset)
        self.assertIn("r.copy_back ? w.squad_reset_uniform", reset)
        # "Soldier 3: Rifleman", one line per soldier, and what he fires (the game's rule, squad_info's "fires"); a line
        # of several from before ("Rifleman ×4")
        words = function_text(self.squad.replace("  function ", "function "), "soldierWords")
        self.assertIn("fill(fires.length ? w.squad_soldier_one_fires : w.squad_soldier_one,", words)
        self.assertIn("{ who: s.label, n: s.number, weapons: fires.join(\", \") }", words)
        self.assertIn("fill(fires.length ? w.squad_soldier_fires : w.squad_soldier,", words)

    def test_add_and_remove_only_when_the_studio_says_so(self):
        card = inner(self.squad, "drawCard")
        self.assertIn("if (mine() && info.can && info.can.add) parts.push(...addParts());", card)
        self.assertIn("if (can.remove) acts.append(...removeParts(s));", inner(self.squad, "soldierLine"))
        # drawn nowhere else
        self.assertEqual(len(re.findall(r"\baddParts\(\)", self.squad)), 1)
        self.assertEqual(len(re.findall(r"\bremoveParts\(s\)", self.squad)), 1)
        self.assertEqual(len(re.findall(r"api\(\)\.soldier_add\(", self.squad)), 1)
        self.assertEqual(len(re.findall(r"api\(\)\.soldier_remove\(", self.squad)), 1)
        # the stand-in page says so only with ?fake=squad2 (one line per soldier, at most 8, at least 2)
        fake = read("fake-api.js")
        self.assertIn("can: { blender: own, import: own, reset: own, add: false, remove: false },", fake)
        self.assertIn('if (mode === "squad2") return fakeSquadInfo2(address, lang, made, game, kinds);', fake)
        self.assertIn("add: own && count < 8 && !open,\n        remove: own && count > fewest && !open },", fake)
        # when it can't, the limits say why: Add a soldier's on the card, Remove's under the soldiers
        self.assertIn("else if (mine() && info.limits && info.limits.add) parts.push(el(\"p\", { className: "
                      "\"squad-limit\", textContent: info.limits.add }));", card)
        self.assertIn("textContent: info.limits.remove", inner(self.squad, "drawLines"))
        # Add a soldier ends in Blender with him (he joins on Bring my changes back, which says so)
        add = inner(self.squad, "addSoldier")
        self.assertIn("say(w.squad_add_opened, \"ok\");", add)
        self.assertNotIn("reload(", add)
        self.assertIn("r.joined ? fill(w.squad_added, { n: r.count })", inner(self.squad, "bringBack"))

    def test_minus_one_and_plus_one_at_once(self):
        """−1 and +1 on the card, no Blender (the owner, 2026-11-12: "I would like to add the +1 button because that
        seems a lot easier than 4 steps to add 1 unit"; "You should be able to subtract from the base unit. And add."),
        each only when the Studio says the squad can (Remove's and Add a soldier's "can"), what changed said."""
        card = inner(self.squad, "drawCard")
        self.assertIn("if (mine()) parts.push(countParts());", card)
        self.assertLess(card.index("countParts()"), card.index("addParts()"))   # (above Add a soldier, below Blender's)
        count = inner(self.squad, "countParts")
        self.assertIn("textContent: w.squad_minus,\n        title: w.tip_squad_minus, disabled: S.busy || !can.remove", count)
        self.assertIn("textContent: w.squad_plus,\n        title: w.tip_squad_plus, disabled: S.busy || !can.add", count)
        self.assertLess(count.index("w.squad_minus"), count.index("w.squad_plus"))
        by = inner(self.squad, "countBy")
        self.assertIn("step > 0 ? await api().soldier_plus(address) : await api().soldier_minus(address)", by)
        self.assertIn("fill(w.squad_added, { n: r.count })", by)
        self.assertIn("fill(w.squad_removed, { number: r.removed, n: r.count }), r.look_kept ? w.squad_minus_kept", by)
        self.assertIn("r.copy_back ? w.squad_reset_uniform", by)
        self.assertIn("await reload(true);", by)
        self.assertEqual(len(re.findall(r"\bcountParts\(\)", self.squad)), 1)
        for call in ("soldier_plus", "soldier_minus"):
            self.assertEqual(len(re.findall(rf"api\(\)\.{call}\(", self.squad)), 1)
        # the stand-in page: +1 before the bazooka man, −1 the soldier standing there, as Remove takes one out
        fake = read("fake-api.js")
        self.assertIn("const at = list.includes(\"bazooka\") ? list.length : list.length + 1;",
                      fake[fake.index("soldier_plus: async"):])
        self.assertIn("window.pywebview.api.soldier_remove(address, String(list.includes(\"bazooka\") ? list.length - 1 "
                      ": list.length));", fake)

    def test_a_game_squad_says_why_and_offers_its_way_to_a_new_unit(self):
        card = inner(self.squad, "drawCard")
        self.assertIn("textContent: w.model_want_button,\n          title: w.tip_model_want, disabled: !page.startNew", card)
        self.assertIn("textContent: info.why_not || w.squad_game", card)
        self.assertIn("const mine = () => !S.info.why_not && S.info.own !== false;", self.squad)
        self.assertIn("if (mine()) {", inner(self.squad, "soldierLine"))   # (its lines say what it is, no buttons)

    def test_a_unit_that_isn_t_a_squad_draws_no_card(self):
        show = function_text(self.app, "showUnit")
        self.assertIn("const squad = building || !window.SquadView ? null : await window.SquadView.infoOf(u.address);",
                      show)
        self.assertEqual(show.count("window.SquadView.section("), 1)
        at = show.index("window.SquadView.section(")
        self.assertIn("} else if (squad && !squad.error) {", show[:at])
        # every other unit's page as before: its 3D view and Look and moves beside its values
        self.assertIn('side = el("aside", { className: "unit-side" }, view, lookMovesBox(u, view, copyForm && '
                      'copyForm.openForm));', show)
        # squad_info: null for a unit that isn't a squad; a Studio without the call: as before; an error: said, as before
        info = function_text(self.squad.replace("  async function ", "async function "), "infoOf")
        self.assertIn('if (typeof api().squad_info !== "function") return null;', info)
        self.assertIn("return (await api().squad_info(address, state.lang)) || null;", info)
        self.assertIn("return { error: (err && err.message) || String(err) };", info)
        self.assertIn("fill(w.squad_unreadable, { why: squad.error })", show)
        self.assertIn("if (!kinds) return null;", read("fake-api.js"))

    def test_more_options_says_where_the_files_are(self):
        more = inner(self.squad, "drawMore")
        self.assertIn('keptRow(address, "model", fill(s.own_model ? w.squad_kept : w.squad_kept_later, { who: s.label }), s.kept,',
                      more)
        self.assertIn('keptRow(address, "blender", info.blender.made ? w.squad_blender_kept : w.squad_blender_kept_later,', more)
        self.assertIn("w.model_kept_uniform", more)
        # (small and folded: the main path is never under it)
        self.assertIn('className: "ghost small squad-more-toggle", title: W().tip_squad_more', self.squad)
        self.assertIn('const moreBody = el("div", { className: "squad-more-body" + (opened ? "" : " hidden") });', self.squad)

    def test_its_uniform_stays_in_look_and_moves(self):
        look = function_text(self.app, "lookMovesBox")
        self.assertIn("function lookMovesBox(u, view, startNew, squadPage = false) {", self.app)
        self.assertIn("label.textContent = w.uniform_title;", look)
        self.assertIn("label.title = w.tip_squad_uniform_row;", look)
        # (a squad of this mod paints through its card's one Blender button, its Paint ticked: no second Open in
        # Blender in its Uniform row; a game squad's row keeps it)
        self.assertIn("if (squad && paintable && !(info.new_unit && state.mod)) rest.push(repaintBox(address, info, "
                      "drawLook, changed));", look)
        uniform = function_text(self.app, "uniformBox")
        self.assertIn("squadPage ? w.tip_squad_uniform_custom_own_model : w.tip_uniform_custom_own_model", uniform)
        self.assertIn("squadPage ? w.squad_uniform_own_model : w.uniform_own_model", uniform)
        self.assertIn("lookMovesBox(u, view, copyForm && copyForm.openForm, true)", function_text(self.app, "showUnit"))

    def test_every_call_is_the_studio_s_or_the_contracts_and_the_stand_in_page_s(self):
        fake = read("fake-api.js")
        calls = set(re.findall(r"api\(\)\.(\w+)\(", self.squad))
        self.assertTrue(set(PHASE1) | set(LATER) <= calls, calls)
        others = calls - set(PHASE1) - set(LATER)
        self.assertEqual(sorted(c for c in others if not callable(getattr(StudioApi, c, None))), [])
        for call in sorted(calls):
            with self.subTest(call=call):
                self.assertRegex(fake, rf"\b{call}: async")
        # the stand-ins take the contracts' parameters, in their order
        for call, names in {**PHASE1, **LATER}.items():
            got = re.search(rf"\b{call}: async \(([^)]*)\) =>", fake)
            self.assertIsNotNone(got, call)
            self.assertEqual([p.split("=")[0].strip() for p in got.group(1).split(",")], names, call)

    def test_the_stand_in_answers_shaped_as_the_contracts(self):
        fake = read("fake-api.js")
        info = function_text(fake.replace("  function ", "function "), "fakeSquadInfo")
        for key in ("name:", "copies:", "own:", "count,", "line:", "soldiers,", "blender:", "can:", "why_not:",
                    "id: kind,", "label:", "count: counts[kind]", "fires:", "preview:", "own_model:", "from:",
                    "blender_changed:", "kept:", "open:", "work:", "made:", "import: own,", "reset: own,"):
            self.assertIn(key, info)
        # the US rifle squad (4 riflemen, 1 bazooka man) and a squad whose soldiers are all one kind
        self.assertIn('Soldat_US_Leger: [["fusilier", 4], ["bazooka", 1]],', fake)
        self.assertIn('Soldat_Russe_Para: [["fusilier", 5]] };', fake)
        back = fake[fake.index("squad_blender_back: async"):fake.index("soldier_import: async")]
        self.assertIn("changed, unchanged:", back)


class TheWiki(unittest.TestCase):
    """The field manual's page on changing a squad, in each of the eleven languages, names the page's buttons as the
    page says them in that language (words.toml), and the Import a model page leads to it."""
    PAGES = {"us": "Change-a-Squad", "fr": "fr/Changer-une-escouade", "ger": "ger/Einen-Trupp-ändern",
             "ita": "ita/Cambiare-una-squadra", "spa": "spa/Cambiar-un-pelotón", "pol": "pol/Zmiana-oddziału",
             "ru": "ru/Изменение-отряда", "cz": "cz/Změna-družstva", "jpn": "jpn/分隊の変更", "sc": "sc/修改小队",
             "fa": "fa/تغییر-جوخه"}
    BUTTONS = ("look_open", "one_parts", "squad_blender_back", "squad_import", "squad_reset", "squad_each", "squad_more",
               "where_show", "look_get_blender", "look_choose_blender", "blender_model_send", "test_in_game",
               # (Its paint, not Repaint in Blender: a squad of this mod paints its Custom uniform through its card's
               # one Blender button since 2026-11-13; the Repaint box stays a game squad's only)
               "model_want_button", "create", "units_tab", "uniform_custom", "one_part_paint", "lm_title",
               # (a soldier more or fewer: the owner, 2026-11-12, "Yes, update it" to the page's own update)
               "squad_plus", "squad_minus", "squad_add", "squad_add_copy", "squad_add_unit", "squad_add_file",
               "squad_remove")

    def test_its_buttons_named_as_the_page_names_them(self):
        wiki = UI.parents[2] / "docs" / "wiki"
        words = tomllib.loads(WORDS.read_text(encoding="utf-8"))
        self.assertEqual(set(self.PAGES), set(LANGS))
        for lang, page in self.PAGES.items():
            text = (wiki / f"{page}.md").read_text(encoding="utf-8")
            for key in self.BUTTONS:
                with self.subTest(lang=lang, key=key):
                    self.assertIn(f"**{words[key][lang]}**", text)
            # (and the language's Import a model page leads to it, by the page's name)
            name = page.split("/")[-1]
            leads = [p for p in (wiki / (page.split("/")[0] if "/" in page else "")).glob("*.md")
                     if f"|{name}]]" in p.read_text(encoding="utf-8") and p.stem != name]
            self.assertGreaterEqual(len(leads), 2, lang)   # (its Import a model page and its home page)


@unittest.skipUnless(all(callable(getattr(StudioApi, c, None)) for c in PHASE1),
                     "the Studio's squad calls aren't joined yet (agent B's branch)")
class TheStudioCalls(unittest.TestCase):
    """Once the Studio's own calls are joined: the parameters the page sends, as the contracts' section 4 names them."""

    def test_their_parameters(self):
        for call, names in {**PHASE1, **LATER, "soldier_blender": ["address", "soldier", "lang"]}.items():
            with self.subTest(call=call):
                got = [p for p in inspect.signature(getattr(StudioApi, call)).parameters if p != "self"]
                self.assertEqual(got, names)


if __name__ == "__main__":
    unittest.main()
