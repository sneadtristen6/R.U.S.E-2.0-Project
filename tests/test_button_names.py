"""Every line of the Studio that names one of its Blender buttons, or its Custom uniform, names it the way the page it
is shown on does, in every language: words.toml, errors.toml and buildtext.toml.

The project's rule: a naming fix reaches every place the Studio shows the name. Release 0.9.8.20's one Blender button
(ruse_studio.oneblender, ui/squad.js and app.js oneBlenderBox) took Change the squad in Blender off the page; Change it
in Blender and Bring back the model stay as buttons only on a squad shown without its card (its soldiers couldn't be
read: app.js modelBox and kindsBox), Change it in Blender also as the heading of the one button's box on any other unit;
Repaint in Blender and its Bring back stay only in the repaint box (a game squad's Custom uniform, a squad shown without
its card). The lines that named them where the page has other buttons were worded again (work/0920b-button-names): said
on two pages whose button differs, a line says what to do in plain words ("bring your changes back", "open it in
Blender"), as the Studio's other Blender refusals already did. And a line that named a button by another word than the
page's (the UX audit of 2026-11-14: Custom uniform in Spanish, Japanese and Persian; then Choose Blender… in German and
Japanese, Open in Blender turned into a verb, the repaint box's Bring back as Rapporter, Przywróć, Vrátit zpět) says the
page's own word.

What can't be read from the words alone stays the reviewer's: which page a line is shown on. ALLOWED below says it for
each line naming the card-less squad's or the repaint box's buttons, from the page's code."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ["us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa"]


def load(rel: str) -> dict:
    return tomllib.loads((ROOT / rel).read_text(encoding="utf-8"))


STUDIO = load("src/ruse_studio/words.toml")
LAUNCHER = load("src/ruse_launcher/words.toml")
TEXTS = {"words": STUDIO, "errors": load("src/ruse_studio/errors.toml"), "buildtext": load("src/rusemod/buildtext.toml")}

# the Blender and uniform buttons these lines name (their words.toml keys); a line names one when its English has the
# button's English (Bring back alone: not as part of a longer button's name)
BUTTONS = ["look_open", "squad_blender_back", "model_blender", "model_blender_back", "unit_look", "decoy_blender_aside",
           "decoy_blender", "blender_model_send", "one_parts", "uniform_custom", "look_back", "look_choose_blender",
           "look_get_blender", "uniform_default_again", "menu_blender"]
# the same English on another button: the menu pictures' Bring back (maps.js) in the menu pictures' own lines, RUSE
# Decoy's Bring my changes back
SAME_ENGLISH = {"look_back": ("menu_", "menu_bring_back"), "squad_blender_back": ("decoy_", "decoy_blender_back")}
# the squad's Blender button the one button took the place of (c0f8410d^ words.toml squad_blender), every language
OLD_SQUAD_BUTTON = {"us": "Change the squad in Blender", "fr": "Changer l'escouade dans Blender",
                    "ger": "Den Trupp in Blender ändern", "ita": "Cambia la squadra in Blender",
                    "spa": "Cambiar el pelotón en Blender", "pol": "Zmień oddział w Blenderze",
                    "ru": "Изменить отряд в Blender", "cz": "Změnit družstvo v Blenderu", "jpn": "分隊をBlenderで変更",
                    "sc": "在 Blender 中修改小队", "fa": "تغییر جوخه در Blender"}
# the lines that may name the card-less squad's Blender buttons (Change it in Blender, Bring back the model) or the
# repaint box's (Repaint in Blender, its Bring back), each with the page it is shown on (ui/app.js)
ALLOWED = {
    "model_blender": "the button (modelBox, kindsBox) and the heading of oneBlenderBox",
    "model_blender_back": "the button (modelBox, kindsBox)",
    "model_blender_how": "modelBox's own Blender, a squad shown without its card",
    "model_blender_how_kinds": "the same, a squad with soldiers of two kinds",
    "model_blender_opened": "said after modelBox's and kindsBox's Change it in Blender",
    "model_how_squad": "modelBox of a squad shown without its card, under its Change it in Blender",
    "model_how_kinds": "the same, a squad with soldiers of two kinds",
    "model_kinds_how": "kindsBox, beside the Model row's Change it in Blender",
    "tip_model_blender_folder_none": "the Blender folder's row in modelBox and kindsBox",
    "unit_look": "the repaint box's heading (repaintBox)",
    "look_back": "the repaint box's button",
    "look_how": "the repaint box's how-to (repaintBox)",
    "menu_bring_back": "the menu pictures' own Bring back (maps.js)",
    "menu_blender_how": "the menu pictures' how-to, beside their own Bring back (maps.js)",
}
# a line that names the Custom uniform as what a squad wears, not as the button to click: the language says it in the
# sentence's own case, as it would say any other noun (the strict check takes these forms there)
INFLECTED = {("model_kept_not_record", "pol"): "Własnego munduru", ("squad_both", "cz"): "Vlastní uniformu",
             ("blender_squad_uniform_kept", "fr"): "uniforme personnalisé",
             ("blender_squad_uniform_kept", "ger"): "eigenen Uniform",
             ("blender_squad_uniform_kept", "ita"): "uniforme personalizzata",
             ("blender_squad_uniform_kept", "spa"): "uniforme personalizado",
             ("blender_squad_uniform_kept", "pol"): "własnym mundurem",
             ("blender_squad_uniform_kept", "ru"): "своей формой",
             ("blender_squad_uniform_kept", "cz"): "vlastní uniformou"}
QUOTED = re.compile(r"«\s?([^»]+?)\s?»|„([^“”]+)[“”]|“([^”]+)”|「([^」]+)」|‘([^’]+)’|\"([^\"]+)\"")


def english_names(text: str) -> list:
    """The buttons (BUTTONS keys) a line's English names: the longest names first, so Bring back the model isn't also
    Bring back."""
    out, rest = [], text
    for key in sorted(BUTTONS, key=lambda k: len(STUDIO[k]["us"]), reverse=True):
        name = STUDIO[key]["us"]
        if name in rest:
            out.append(key)
            rest = rest.replace(name, "\0")
    return out


def page_words(lang: str) -> set:
    return {v[lang] for t in (STUDIO, LAUNCHER) for v in t.values() if isinstance(v, dict) and isinstance(v.get(lang), str)}


def lines(texts=TEXTS):
    """(file, key, entry) of every line of these files, but the buttons' own words."""
    for file, table in texts.items():
        for key, entry in table.items():
            if isinstance(entry, dict) and isinstance(entry.get("us"), str) and key not in BUTTONS:
                yield file, key, entry


def misnamed(texts=TEXTS) -> list:
    """Every (file, key, lang, button) whose line names the button in English but not by the page's word in lang."""
    out = []
    for file, key, entry in lines(texts):
        for button in english_names(entry["us"]):
            words = [STUDIO[button]]
            prefix, other = SAME_ENGLISH.get(button, (None, None))
            if prefix:
                words = [STUDIO[other]] if key.startswith(prefix) else [STUDIO[button], STUDIO[other]]
            for lang in LANGS[1:]:
                text = entry.get(lang)
                if not isinstance(text, str):
                    continue
                said = [w[lang] for w in words] + ([INFLECTED[(key, lang)]] if (key, lang) in INFLECTED else [])
                if not any(s in text for s in said):
                    out.append((file, key, lang, button))
    return out


def quoted_not_page(texts=TEXTS) -> list:
    """Every (file, key, lang, quoted) in a line naming one of the buttons whose quoted name isn't one of the page's
    words in that language (a quoted {blank}: the line's own value, left out)."""
    out = []
    for file, key, entry in lines(texts):
        if not english_names(entry["us"]):
            continue
        for lang in LANGS:
            text = entry.get(lang)
            if not isinstance(text, str):
                continue
            words = page_words(lang)
            for m in QUOTED.finditer(text):
                span = next(g for g in m.groups() if g)
                if "{" not in span and span not in words:
                    out.append((file, key, lang, span))
    return out


def named_where_not_allowed(texts=TEXTS) -> list:
    """Every (file, key) whose English names the card-less squad's or the repaint box's Blender buttons outside
    ALLOWED, and every (file, key, lang) naming the squad's old Blender button."""
    out = []
    for file, table in texts.items():
        for key, entry in table.items():
            if not isinstance(entry, dict) or not isinstance(entry.get("us"), str):
                continue
            names = english_names(entry["us"])
            if key not in ALLOWED and set(names) & {"model_blender", "model_blender_back", "unit_look", "look_back"}:
                out.append((file, key))
            for lang in LANGS:
                if isinstance(entry.get(lang), str) and OLD_SQUAD_BUTTON[lang] in entry[lang]:
                    out.append((file, key, lang))
    return out


class TheLines(unittest.TestCase):
    def test_no_line_names_a_button_where_the_page_hasnt_got_it(self):
        self.assertEqual(named_where_not_allowed(), [])
        for key in ALLOWED:   # (each allowed line is there: a key worded away is taken off the list too)
            with self.subTest(key=key):
                self.assertIn(key, STUDIO)

    def test_each_line_names_each_button_by_the_page_s_word_in_every_language(self):
        self.assertEqual(misnamed(), [])

    def test_every_quoted_button_name_is_one_of_the_page_s_words(self):
        self.assertEqual(quoted_not_page(), [])

    def test_the_lines_worded_again_here(self):
        """The paint of a unit's own copy is the one button's (Open in Blender, only Its paint ticked under What goes
        to Blender) on the page of a unit that isn't a squad, which has no Repaint in Blender any more; the lines said
        on two pages say what to do, never a button only one of them has."""
        for key in ("tip_model_copy", "model_copy_has"):
            for lang in LANGS:
                with self.subTest(key=key, lang=lang):
                    for button in ("look_open", "one_part_paint", "one_parts"):
                        self.assertIn(STUDIO[button][lang], STUDIO[key][lang])
                    self.assertNotIn(STUDIO["unit_look"][lang], STUDIO[key][lang])
        errors = TEXTS["errors"]
        for english in ("Open this unit in Blender first and paint it, then bring your paint back.",
                        "There are no Blender files for this unit yet: open it in Blender first.",
                        "This unit has no soldiers of another kind: open its model in Blender instead.",
                        "Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at the "
                        "top, then bring your changes back here."):
            entry = next(e for e in errors.values() if isinstance(e, dict) and e.get("us") == english)
            for lang in LANGS:
                with self.subTest(english=english[:30], lang=lang):
                    for button in ("model_blender", "model_blender_back"):
                        self.assertNotIn(STUDIO[button][lang], entry[lang])
        for key in ("blender_model_sent", "blender_model_hint2", "uniform_has"):
            for lang in LANGS:
                with self.subTest(key=key, lang=lang):
                    self.assertNotIn(STUDIO["model_blender_back"][lang], STUDIO[key][lang])


class TheChecksCatchTheOldWords(unittest.TestCase):
    """Controls: the release head's own lines (aa2c0a65), each check on them finds what this branch worded again."""

    def test_the_old_lines_are_found(self):
        old = {
            "errors": {
                "e7f3b115a6c": {"us": "Pick Custom uniform first: the default uniform is worn by other squads and by "
                                      "gun and vehicle crews too, so it isn't repainted here.",
                                "spa": "Elige primero Uniforme propio: el uniforme por defecto también lo llevan otros "
                                       "pelotones y las dotaciones de cañones y vehículos, así que no se repinta aquí.",
                                "jpn": "先に「専用の軍服」を選んでください。"},
                "e518cc1f08f": {"us": "Blender isn't found on this PC. Get it free from blender.org (Get Blender), "
                                      "then use Choose Blender… to show the Studio where blender.exe is.",
                                "ger": "Blender ist auf diesem PC nicht zu finden. Hol es kostenlos auf blender.org "
                                       "(Get Blender) und zeige dem Studio dann mit „Blender wählen…“, wo blender.exe "
                                       "liegt."},
                "e470775aa90": {"us": "There are no Blender files for this unit yet: click Change it in Blender "
                                      "first."},
            },
            "words": {
                "model_copy_has": {"us": "This unit has its own copy of the model: Repaint in Blender changes only "
                                         "this unit."},
                "some_line": {"us": "Change it in Blender, then save.", "fr": "Changer l'escouade dans Blender."},
            },
        }
        self.assertIn(("errors", "e7f3b115a6c", "spa", "uniform_custom"), misnamed(old))
        self.assertIn(("errors", "e518cc1f08f", "ger", "look_choose_blender"), misnamed(old))
        self.assertIn(("errors", "e7f3b115a6c", "jpn", "専用の軍服"), quoted_not_page(old))
        self.assertIn(("errors", "e518cc1f08f", "ger", "Blender wählen…"), quoted_not_page(old))
        found = named_where_not_allowed(old)
        for where in (("errors", "e470775aa90"), ("words", "model_copy_has"), ("words", "some_line"),
                      ("words", "some_line", "fr")):
            with self.subTest(where=where):
                self.assertIn(where, found)


if __name__ == "__main__":
    unittest.main()
