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


class Item32ModelsOrUniformLink(InElevenLanguages):
    ITEM = "32"

    def test_52v_models_or_uniform_said_with_the_link(self):
        self.assertIn('helpLine(fill(w.squad_both, { who: s.label }), "squad", "notice warn")', js("squad.js"))
        app = js("app.js")
        self.assertIn('helpLine(squadPage ? w.squad_uniform_own_model : w.uniform_own_model, "squad")', app)
        self.assertIn('helpLine(w.model_both_squad, "squad", "notice warn")', app)


class Item33HorseBonesLink(InElevenLanguages):
    ITEM = "33"

    def test_52w_the_generic_horse_s_page_has_the_models_and_bones_line(self):
        self.assertIn('helpLine(w.eras_horse_bones_link, "bones")', js("eraunits.js"))
        self.words_in_eleven_languages(["eras_horse_bones_link"], english_left_in=True)


class Item35GroupWords(InElevenLanguages):
    ITEM = "35"

    def test_52y_group_without_card_type(self):
        self.words_in_eleven_languages(["eras_group_pick_why"])
        self.assertNotIn("card type", WORDS["eras_group_pick_why"]["us"])
        self.assertEqual(WORDS["eras_group_pick_why"]["us"], "Pick the row of the build menu it goes in above first: the "
                         "Studio can't tell which row is its kind's for this unit.")
        us = [t["us"] for t in ERRORS.values() if isinstance(t, dict) and "us" in t]
        self.assertFalse([t for t in us if "no card type" in t])
        from rusemod.wordedtext import key_of
        text = next(t for t in us if t.startswith("This unit has no kind the Studio can read"))
        self.assertIn(key_of(text), ERRORS)    # (an entry is named from its English: tests/test_errortext checks the
        #                                         code says the same words, for every refusal)


class Item7UntickedBonesKeepTheAnimations(InElevenLanguages):
    """Pick 29 (2026-11-14): with Its bones unticked the bones go back as the mod has them, and so do the animations.
    On the made-up skeleton and clips of test_animglb (as test_anim_back's Trip, whose module needs numpy for its other
    classes): the spine plays 20 degrees more in the run, as Blender plays an animation on a bone it moved."""
    ITEM = "7"

    def setUp(self):
        from rusemod import baf, modelin
        from test_animglb import CLIPS, own_model_file
        self.baf, self.CLIPS = baf, CLIPS
        self.originals = {name: baf.build(clip) for name, clip, _x in CLIPS}
        self.start = modelin.own_animations_glb(own_model_file(), self.originals, blender=True)

    def taken_in(self, raw: bytes) -> tuple:
        """(the clips the import keeps of a file brought back, {name: the bones that came back changed}):
        animmodel_calls._went_out_kept's way."""
        from rusemod import modelin, rig, unitmodel
        doc, binary = modelin.glb_document(raw)
        r = rig.rig_of(doc, binary, "test.glb")
        record, _notes = unitmodel.own_skeleton(r)
        made, _notes = unitmodel.own_clips(r, record)
        return rig.kept_clips(made, rig.clips_out(doc), r)

    def test_the_animations_come_back_as_they_went_out_though_a_bone_was_played_differently(self):
        from rusemod import gltf, rig
        from ruse_studio import modelblender
        from test_animglb import Blenderish
        from test_gltf_bones import RECORD
        name = self.CLIPS[0][0]
        sending = Blenderish(self.start).send(change=(name, "bip01 spine", self.baf.axis_angle("x", 20.0)))
        raw = rig.with_record(gltf.joints_like(sending, self.start), RECORD)    # (its bones put back, as bones_like does)
        # the control: bones ticked, the change is Blender's
        kept, changed = self.taken_in(rig.with_went_out(raw, self.originals, None))
        self.assertEqual(changed[name], ["bip01 spine"])
        self.assertNotEqual(kept[name], self.originals[name])
        # unticked: every animation is the clip that went out, byte for byte, and none is named as changed
        given = modelblender.played_as_sent(raw, self.originals, dict(self.originals), {})
        kept, changed = self.taken_in(rig.with_went_out(raw, self.originals, given))
        self.assertEqual(kept, self.originals)
        self.assertEqual(changed, {n: [] for n in self.originals})
        # one the Studio changed since is left to _settled: it keeps what it was given
        mine = {name: (self.originals[name], self.originals[name])}
        self.assertEqual(modelblender.played_as_sent(raw, self.originals, dict(self.originals), mine)[name],
                         self.originals[name])
        # a file that can't be read: what it was given, never an exception
        self.assertEqual(modelblender.played_as_sent(b"not a model", self.originals, dict(self.originals), {}),
                         self.originals)

    def test_the_page_says_the_animations_were_kept_too(self):
        self.words_in_eleven_languages(["one_kept_animations"], english_left_in=True)
        self.assertIn('kept.animations === "kept"', function_text(js("app.js"), "oneKeptSaid"))


class Item1BlenderWorkSetAside(InElevenLanguages):
    """Picks 21 and 22 (2026-11-14): the Blender work of a deleted unit, or of a model another file replaced, is set aside
    under another name, never picked up by a unit made again (the whole path is test_scenarios_models_blender's SQ-5 and
    M-5); here the move itself and what the page says."""
    ITEM = "1"

    def setUp(self):
        import tempfile
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.mod = Path(self.dir.name)
        self.work = self.mod / "blender"
        for sub in ("Descriptor_Unit_X", "Descriptor_Unit_X@2", "Descriptor_Unit_XY", "Descriptor_Unit_X/animations"):
            (self.work / sub).mkdir(parents=True)
            (self.work / sub / "send.glb").write_bytes(b"glTF" + sub.encode())

    def test_a_deleted_unit_s_work_and_its_soldiers_go_aside_and_nothing_else(self):
        from ruse_studio.modelblender import set_aside_work
        aside, held = set_aside_work(self.mod, "Descriptor_Unit_X", kinds=True)
        self.assertEqual(held, [])
        self.assertEqual(len(aside), 2)
        self.assertTrue(all("-set-aside-" in a for a in aside))
        names = sorted(p.name for p in self.work.iterdir())
        self.assertEqual(sorted(n for n in names if "-set-aside-" not in n), ["Descriptor_Unit_XY"])   # (another unit's stays)
        self.assertFalse((self.work / "Descriptor_Unit_X").exists())
        moved = next(self.work / a for a in aside if a.startswith("Descriptor_Unit_X-set-aside-"))
        self.assertEqual((moved / "send.glb").read_bytes(), b"glTFDescriptor_Unit_X")      # (nothing lost)
        self.assertTrue((moved / "animations" / "send.glb").is_file())
        # a second time sets nothing more aside (what is aside isn't the unit's work)
        self.assertEqual(set_aside_work(self.mod, "Descriptor_Unit_X", kinds=True), ([], []))

    def test_an_import_keeps_the_animations_page_where_it_is(self):
        from ruse_studio.modelblender import set_aside_work
        aside, held = set_aside_work(self.mod, "Descriptor_Unit_X", keep=("animations",))
        self.assertEqual((len(aside), held), (1, []))
        self.assertTrue((self.work / "Descriptor_Unit_X" / "animations" / "send.glb").is_file())
        self.assertFalse((self.work / "Descriptor_Unit_X" / "send.glb").exists())
        self.assertTrue((self.work / aside[0] / "send.glb").is_file())
        self.assertTrue((self.work / "Descriptor_Unit_X@2" / "send.glb").is_file())    # (another soldier's: not asked)

    def test_a_folder_another_program_holds_stays_and_is_said(self):
        from unittest import mock
        from ruse_studio.modelblender import set_aside_work
        with mock.patch.object(Path, "rename", side_effect=PermissionError("held")):
            aside, held = set_aside_work(self.mod, "Descriptor_Unit_X", kinds=True)
        self.assertEqual(aside, [])
        self.assertEqual(sorted(held), ["Descriptor_Unit_X", "Descriptor_Unit_X@2"])
        self.assertTrue((self.work / "Descriptor_Unit_X" / "send.glb").is_file())

    def test_the_page_says_where_it_went_in_every_language(self):
        app = js("app.js")
        self.assertIn("w.model_kept_not_blender_aside", function_text(app, "notKeptSaid"))
        self.assertIn("w.blender_aside_deleted", function_text(app, "researchTold"))
        keys = ["model_kept_not_blender_aside", "blender_aside_deleted", "blender_aside_held"]
        self.words_in_eleven_languages(keys, english_left_in=True)
        for key in keys:
            for lang in LANGS:
                self.assertIn("{folders}", WORDS[key][lang], (key, lang))


if __name__ == "__main__":
    unittest.main()
