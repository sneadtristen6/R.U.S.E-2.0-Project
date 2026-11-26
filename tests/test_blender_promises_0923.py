"""The 0.9.8.22 announcement's promises for squads, Blender and animations that were built for 0.9.8.23 (the owner,
2026-11-26: "The 60 promises should be built into this release"; his picks 21 to 52 of REVIEW-0920.md, "everything that
you agreed to, 21 through 52"): each promise's words in the eleven languages, and where the page shows them.

One class per promise (ITEM: its number in D:/RUSE-2.0/scratch/release-next/audit-2026-11-26/results/
plan_squads-blender.json's order; the sentence names the promise). These read the page's code and the words (there is
no browser here, as tests/test_lookmoves.py and tests/test_squadpage.py do it); what a page then looks like in the
game's window is not checked here.

FOR: the squads, Blender and animations promises of release 0.9.8.23 (24, 29, 52a-52y, 51f, 51j, 21, 22).
USED-BY: gentle.py, -m unittest."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import re
import tomllib
import unittest
from pathlib import Path
from urllib.parse import quote

from rusemod.community import REPO_URL, WIKI_TOPICS, wiki_url

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "src" / "ruse_studio" / "ui"
LANGS = ["us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa"]
WORDS = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
ERRORS = tomllib.loads((ROOT / "src" / "ruse_studio" / "errors.toml").read_text(encoding="utf-8"))
BLANK = re.compile(r"\{\w+\}")


def js(name: str) -> str:
    return (UI / name).read_text(encoding="utf-8")


def function_text(source: str, name: str) -> str:
    """`function name(` to the next line that is a closing brace at column 0."""
    start = source.index(f"function {name}(")
    return source[start: source.index("\n}\n", start)]


class InElevenLanguages(unittest.TestCase):
    def words_in_eleven_languages(self, keys, english_left_in=False):
        """Each key has every language, the same blanks as the English, nothing empty (and, for a new sentence, no
        language left as the English)."""
        for key in keys:
            with self.subTest(key=key):
                self.assertIn(key, WORDS)
                self.assertEqual(set(WORDS[key]), set(LANGS))
                for lang in LANGS:
                    self.assertTrue(WORDS[key][lang].strip(), lang)
                    self.assertEqual(sorted(BLANK.findall(WORDS[key][lang])), sorted(BLANK.findall(WORDS[key]["us"])), lang)
                    if english_left_in and lang != "us":
                        self.assertNotEqual(WORDS[key][lang], WORDS[key]["us"], lang)

    def names_in_every_language(self, line_key, button_keys):
        """A line names each of those buttons by the page's own word, in every language."""
        for lang in LANGS:
            for button in button_keys:
                with self.subTest(line=line_key, button=button, lang=lang):
                    self.assertIn(WORDS[button][lang], WORDS[line_key][lang])


class Item3FirstHintOnATank(InElevenLanguages):
    """Pick 24: Blender's first hint says "Change the model" for a unit that isn't a squad (the behaviour is in
    test_modelblender); here: it is another sentence in every language and says the model, not the soldier."""
    ITEM = "3"

    def test_the_model_wording(self):
        self.words_in_eleven_languages(["blender_model_hint1_model"], english_left_in=True)
        self.assertTrue(WORDS["blender_model_hint1_model"]["us"].startswith("Change the model, or bring in your own model"))
        self.assertNotIn("soldier", WORDS["blender_model_hint1_model"]["us"])
        self.assertIn("soldier", WORDS["blender_model_hint1"]["us"])


class Item9UniformWordsInEveryLanguage(InElevenLanguages):
    """51j: Custom uniform and Back to the default uniform answer in the Studio's language (the behaviour is
    test_scenarios_squads_soldiers' SQ-11)."""
    ITEM = "9"

    def test_the_four_sentences_name_no_button_the_page_hasnt(self):
        keys = ["uniform_custom_done", "copy_own_done", "uniform_default_done", "copy_default_done"]
        self.words_in_eleven_languages(keys, english_left_in=True)
        for key in ("uniform_custom_done", "copy_own_done"):
            self.assertNotIn("Repaint in Blender", WORDS[key]["us"])
            self.names_in_every_language(key, ["look_open"])

    def test_the_calls_take_the_language(self):
        import inspect
        from ruse_studio.api import StudioApi
        for call in ("model_copy", "model_copy_remove"):
            self.assertIn("lang", inspect.signature(getattr(StudioApi, call)).parameters, call)


class Item8LeftOutAnimations(InElevenLanguages):
    """51f: Import model says what it left out of a model's animations (the behaviour is
    test_scenarios_models_import's M-2 tests): the page says the report's not_kept "left_out"."""
    ITEM = "8"

    def test_the_page_says_it(self):
        text = function_text(js("app.js"), "notKeptSaid")
        self.assertIn("lost.left_out", text)
        self.assertIn("w.model_kept_not_left_out", text)
        self.words_in_eleven_languages(["model_kept_not_left_out"], english_left_in=True)
        self.assertIn("{names}", WORDS["model_kept_not_left_out"]["us"])


class Item11BonesBoxLink(InElevenLanguages):
    ITEM = "11"

    def test_52a_the_box_has_the_having_trouble_link(self):
        self.assertIn('troubleLink("bones")', function_text(js("app.js"), "ownAnimationsBox"))


class Item12ImportTooltips(InElevenLanguages):
    ITEM = "12"

    def test_52b_the_soldiers_import_tooltips_say_open_in_blender_opens_him_with_his_bones(self):
        self.words_in_eleven_languages(["tip_squad_import", "tip_squad_import_all"])
        for key in ("tip_squad_import", "tip_squad_import_all"):
            self.names_in_every_language(key, ["look_open"])
        self.assertIn("Open in Blender opens him with his bones", WORDS["tip_squad_import"]["us"])


class Item13SplitLine(InElevenLanguages):
    ITEM = "13"

    def test_52c_one_line_above_the_bone_list(self):
        text = function_text(js("app.js"), "halvesBox")
        self.assertIn("w.fit_split_leave", text)
        self.assertLess(text.index("w.fit_split_leave"), text.index(", tree);"))   # (the list comes after the line)
        self.words_in_eleven_languages(["fit_split_leave"], english_left_in=True)
        self.assertEqual(WORDS["fit_split_leave"]["us"], "Leave it on the suggested bone unless, in the game, the top "
                                                         "of the body walks or the legs aim.")


class Item14PointsWithNoBone(InElevenLanguages):
    ITEM = "14"

    def test_52d_points_that_follow_no_bone(self):
        self.words_in_eleven_languages(["model_no_bone"])
        us = WORDS["model_no_bone"]["us"]
        self.assertIn("Open in Blender", us)
        self.assertNotIn("go to Weight Paint", us)
        self.names_in_every_language("model_no_bone", ["look_open"])
        for name in ("app.js", "squad.js"):   # (shown on both pages, each with the link)
            self.assertRegex(js(name), r'helpLine\(fill\(w\.model_no_bone, \{ n: own\.no_bone \}\), "bones", "notice warn"\)')


class WikiPages(InElevenLanguages):
    def topic_opens_each_language_s_page(self, topic, us, fr):
        self.assertEqual(sorted(WIKI_TOPICS[topic]), sorted(LANGS))
        self.assertEqual(wiki_url("us", topic), f"{REPO_URL}/wiki/{quote(us)}")
        self.assertEqual(wiki_url("fr", topic), f"{REPO_URL}/wiki/{quote(fr)}")
        for lang, page in WIKI_TOPICS[topic].items():
            folder = ROOT / "docs" / "wiki" / ("" if lang == "us" else lang)
            self.assertTrue((folder / f"{page}.md").is_file(), (topic, lang))
        self.words_in_eleven_languages([f"tip_help_trouble_{topic}"])


class Item15SquadLink(WikiPages):
    ITEM = "15"

    def test_52e_own_helmet_backpack_or_bazooka_links_to_the_step_by_step(self):
        self.topic_opens_each_language_s_page("squad", "Change-a-Squad", "Changer-une-escouade")
        self.assertIn('helpLine(w.squad_more_asset, "squad", "squad-note")', js("squad.js"))


class Item16ImportLink(WikiPages):
    ITEM = "16"

    def test_52f_own_bones_and_animations_link_to_the_how_to(self):
        self.topic_opens_each_language_s_page("import", "Import-a-Model", "Importer-un-modèle")
        self.assertIn('helpLine(w.squad_more_bones, "import", "squad-note")', js("squad.js"))


class Item17OtherBonesWarning(InElevenLanguages):
    ITEM = "17"

    def test_52g_the_other_bones_warning_is_shorter_and_the_note_uses_it(self):
        self.words_in_eleven_languages(["model_kind_bones_other"])
        us = WORDS["model_kind_bones_other"]["us"]
        self.assertLess(len(us), 180)    # (it was 233 characters)
        api = (ROOT / "src" / "ruse_studio" / "api.py").read_text(encoding="utf-8")
        self.assertIn('words(schema.BASE)["model_kind_bones_other"]', api)
        self.assertNotIn("This model is on bones of its own, and the riflemen's model isn't on the same bones", api)


class Item18RecordUnread(InElevenLanguages):
    ITEM = "18"

    def test_52h_the_record_line_names_the_button_of_the_page_it_is_shown_on(self):
        self.words_in_eleven_languages(["model_record_unread", "model_record_unread_own"])
        self.assertIn("w.model_record_unread_own", js("app.js"))   # (the Model row's: its button reads Import another…)
        self.names_in_every_language("model_record_unread_own", ["model_import_again"])
        self.names_in_every_language("model_record_unread", ["model_import"])   # (a soldier's line: Import model…)
        self.assertNotIn("Import model again", WORDS["model_record_unread"]["us"])


AUTOMATIC = {"us": "Automatic", "fr": "Automatique", "ger": "Automatisch", "ita": "Automatica", "spa": "Automática",
             "pol": "Automatycznie", "ru": "Автоматически", "cz": "Automaticky", "jpn": "自動", "sc": "自动",
             "fa": "خودکار"}
OLD_END = {"us": "Not tried in the game yet.", "fr": "Pas encore essayé dans le jeu.",
           "ger": "Noch nicht im Spiel ausprobiert.", "ita": "Non ancora provato nel gioco.",
           "spa": "Aún no probado en el juego.", "pol": "Jeszcze niesprawdzone w grze.",
           "ru": "В игре ещё не проверено.", "cz": "Ve hře zatím nevyzkoušeno.",
           "jpn": "ゲーム内ではまだ試していません。", "sc": "尚未在游戏中试过。", "fa": "هنوز در بازی امتحان نشده است."}


class Item19Automatic(InElevenLanguages):
    ITEM = "19"

    def test_52i_automatic_in_place_of_nearest(self):
        keys = ["actions_nearest", "actions_how", "tip_actions_pick"]
        self.words_in_eleven_languages(keys)
        for key in keys:
            self.assertNotIn("Nearest", WORDS[key]["us"], key)
            for lang in LANGS:
                self.assertIn(AUTOMATIC[lang], WORDS[key][lang], (key, lang))


class Item20RidesIn(InElevenLanguages):
    ITEM = "20"

    def test_52j_rides_in_names_the_real_place(self):
        self.words_in_eleven_languages(["lm_rides_itself_how"])
        us = WORDS["lm_rides_itself_how"]["us"]
        self.assertNotIn("(set under Animations)", us)
        self.assertIn("long trips by road", us)
        # the Sounds and animation row, its More, and the Its animations box in it
        self.names_in_every_language("lm_rides_itself_how", ["decoy_unit_title", "actions_title"])


class Item21OnlyThisUnitTooltip(InElevenLanguages):
    ITEM = "21"

    def test_52k_only_this_unit_s_tooltip_no_longer_says_not_tried(self):
        self.words_in_eleven_languages(["tip_decoy_anim_for_unit"])
        for lang in LANGS:
            self.assertNotIn(OLD_END[lang], WORDS["tip_decoy_anim_for_unit"][lang], lang)


class Item22CopyTooltip(InElevenLanguages):
    ITEM = "22"

    def test_52l_copy_this_animation_s_tooltip_no_longer_says_not_tried(self):
        self.words_in_eleven_languages(["tip_decoy_copy_make"])
        for lang in LANGS:
            self.assertNotIn(OLD_END[lang], WORDS["tip_decoy_copy_make"][lang], lang)


class Item23CopyUndo(InElevenLanguages):
    ITEM = "23"

    def test_52m_the_copy_s_button_reads_undo_the_copy_s_changes(self):
        self.words_in_eleven_languages(["decoy_copy_reset", "tip_decoy_copy_reset"])
        self.assertEqual(WORDS["decoy_copy_reset"]["us"], "Undo the copy's changes")
        wiki = (ROOT / "docs" / "wiki" / "Unit-Animations.md").read_text(encoding="utf-8")
        self.assertIn("**Undo the copy's changes**", wiki)    # (the field manual names the button as the page does)
        self.assertNotIn("Back to the game's animation", wiki)


class Item24SetAsideLine(InElevenLanguages):
    ITEM = "24"

    def test_52n_the_set_aside_line_and_its_buttons(self):
        self.words_in_eleven_languages(["decoy_blender_aside", "decoy_blender_aside_recycle", "decoy_blender_aside_when",
                                        "decoy_blender_set_aside", "tip_decoy_blender_aside_recycle"])
        self.assertEqual(WORDS["decoy_blender_aside"]["us"], "Bring them back")
        self.assertEqual(WORDS["decoy_blender_aside_recycle"]["us"], "Put them in the Recycle Bin")
        self.assertEqual(WORDS["decoy_blender_aside_when"]["us"], "Changes you sent from Blender on {when} and never brought back.")
        self.names_in_every_language("decoy_blender_set_aside", ["decoy_blender_aside"])
        wiki = (ROOT / "docs" / "wiki" / "Open-in-Blender.md").read_text(encoding="utf-8")
        self.assertIn("**Bring them back**", wiki)
        self.assertNotIn("set-aside sending", wiki)


class Item25OpenInBlenderOnTheModelRow(InElevenLanguages):
    ITEM = "25"

    def test_52o_open_in_blender_is_the_model_row_s_own_button(self):
        app = js("app.js")
        self.assertIn("function oneBlenderBox(address, info, draw, changed, head = null)", app)
        self.assertIn("more.push(oneBlenderBox(address, info, drawLook, changed, head));\n      main = [...main, head];", app)
        box = function_text(app, "oneBlenderBox")
        self.assertIn("if (head) head.replaceChildren(big);", box)
        self.assertIn("...(head ? [] : [big])", box)    # (drawn alone, the box keeps its own button)


class Item26RepaintHeading(InElevenLanguages):
    ITEM = "26"

    def test_52p_a_game_unit_s_box_is_headed_repaint_in_blender(self):
        box = function_text(js("app.js"), "oneBlenderBox")
        self.assertIn("heading.textContent = paintOnly ? w.unit_look : w.model_blender;", box)
        self.assertEqual(WORDS["unit_look"]["us"], "Repaint in Blender")


class Item27UntickedLine(InElevenLanguages):
    ITEM = "27"

    def test_52q_what_unticked_means_on_both_pages(self):
        self.words_in_eleven_languages(["one_parts_unticked"], english_left_in=True)
        self.assertEqual(WORDS["one_parts_unticked"]["us"], "Unticked: kept as it is now, whatever Blender does to it.")
        ticks = function_text(js("app.js"), "oneBlenderTicks")    # (the unit's page and a squad's card both draw it)
        self.assertIn("w.one_parts_unticked", ticks)
        self.assertIn("oneBlenderTicks(", js("squad.js"))


class Item28BringBackLast(InElevenLanguages):
    ITEM = "28"

    def test_52r_the_small_button_under_a_squad_card(self):
        self.words_in_eleven_languages(["squad_blender_back_last"], english_left_in=True)
        self.assertIn('className: "ghost squad-again", textContent: w.squad_blender_back_last', js("squad.js"))
        self.assertEqual(WORDS["squad_blender_back_last"]["us"], "Bring back what I sent last")


class Item29OpenLine(InElevenLanguages):
    ITEM = "29"

    def test_52s_while_blender_is_open_a_line_on_the_card(self):
        self.words_in_eleven_languages(["squad_blender_open_line"], english_left_in=True)
        self.assertIn('...(open ? [el("p", { className: "muted small squad-open-line", textContent: w.squad_blender_open_line })] : [])',
                      js("squad.js"))
        self.names_in_every_language("squad_blender_open_line", ["squad_blender_back", "blender_model_send"])


class Item31CustomUniformLine(InElevenLanguages):
    ITEM = "31"

    def test_52u_the_custom_uniform_line_says_how_to_paint_it(self):
        self.words_in_eleven_languages(["uniform_has"])
        self.names_in_every_language("uniform_has", ["one_parts", "one_part_soldiers", "one_part_paint", "look_open"])


        #                                         code says the same words, for every refusal)


if __name__ == "__main__":
    unittest.main()
