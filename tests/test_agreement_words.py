"""The agreement's version 4 as the owner approved it (2026-11-13, his "Yes, agreement's fine." to the text he was
shown; his items 24 and 26): Bug Watch's game crash point lists the map, the unit the game was making and the mods
that were on, and no longer the game mode (nothing can read the mode from the game's crash report), in the eleven
languages of both apps. The unit stays (his answer to 25), and RUSE Guard's own match details keep their mode."""
import functools
import tomllib
import unittest
from pathlib import Path

from rusemod import guard, schema

SRC = Path(__file__).resolve().parents[1] / "src"
APPS = ("ruse_launcher", "ruse_studio")

# The approved crash point, whole (English)
CRASH = ("- when an app crashes: the kind of error and where in our code; when the game crashes: its crash code, where "
         "in the game it stopped and up to 16 places in the game that led there, the place in memory it was trying to "
         "read, write or run, the game's own error text with any file path shortened, the map it was on (one of the "
         "game's own maps by its name; a map a mod made only as \"a mod's map\", never its name), the unit the game was "
         "making (one of the game's own units by its number; a unit a mod added only as \"a mod's unit\"), and the mods "
         "that were on. The apps send the unit only when they can read it from the game's crash report.")
# The crash point's last sentence in each language: the unit alone, "it" (not "them")
SENT = {
    "us": "The apps send the unit only when they can read it from the game's crash report.",
    "fr": "Les applications n'envoient l'unité que lorsqu'elles peuvent la lire dans le rapport de plantage du jeu.",
    "ger": "Die Einheit senden die Apps nur, wenn sie sie aus dem Absturzbericht des Spiels lesen können.",
    "ita": "Le app inviano l'unità solo quando riescono a leggerla dal rapporto di crash del gioco.",
    "spa": "Las aplicaciones envían la unidad solo cuando pueden leerla en el informe de fallo del juego.",
    "pol": "Jednostkę aplikacje wysyłają tylko wtedy, gdy potrafią ją odczytać z raportu o awarii gry.",
    "ru": "Юнит приложения отправляют, только когда могут прочитать его из отчёта игры о сбое.",
    "cz": "Jednotku aplikace posílají, jen když ji dokážou přečíst z hlášení hry o pádu.",
    "jpn": "。ユニットは、アプリがゲームのクラッシュレポートから読み取れるときだけ送ります。",   # (the old one ended so too)
    "sc": "只有当应用能从游戏的崩溃报告中读出单位时，才会发送它。",
    # "برنامه‌ها یگان را فقط وقتی می‌فرستند که بتوانند آن را از گزارش خرابی بازی بخوانند."
    "fa": "برنامه‌ها یگان را فقط "
          "وقتی می‌فرستند که "
          "بتوانند آن را از گزارش "
          "خرابی بازی بخوانند.",
}
# The game mode as each language said it in the crash point before his approval (none may be left there); each is
# also the apps' own word for the game mode in that language's number help (numberinfo), so the check can't pass on
# a misspelt word
MODE = {"us": "game mode", "fr": "mode de jeu", "ger": "spielmodus", "ita": "modalità di gioco", "spa": "modo de juego",
        "pol": "tryb gry", "ru": "режим игры", "cz": "herní režim", "jpn": "ゲームモード", "sc": "游戏模式",
        "fa": "حالت بازی"}   # (حالت بازی)
# The mode in ANY wording (a bare "der Modus", "режим", "モード", ...): each language's word for it alone, a piece of
# its phrase above and RUSE Guard's own in its match details below; none may be in the crash point at all
MODE_ANY = {"us": "mode", "fr": "mode", "ger": "modus", "ita": "modalità", "spa": "modo", "pol": "tryb",
            "ru": "режим", "cz": "režim", "jpn": "モード", "sc": "模式", "fa": "حالت"}   # (حالت)
# The unit the game was making, as each language says it in the crash point (it stays)
UNIT = {"us": "the unit the game was making", "fr": "l'unité que le jeu était en train de créer",
        "ger": "die Einheit, die das Spiel gerade erstellte", "ita": "l'unità che il gioco stava creando",
        "spa": "la unidad que el juego estaba creando", "pol": "jednostka, którą gra właśnie tworzyła",
        "ru": "юнит, который игра создавала", "cz": "jednotku, kterou hra právě vytvářela",
        "jpn": "ゲームが作っていたユニット", "sc": "游戏当时正在创建的单位",
        "fa": "یگانی که بازی در حال "
              "ساختنش بود"}   # (یگانی که بازی در حال ساختنش بود)
# RUSE Guard's match details (map, mode, ...), as each language starts them: RUSE Guard's own, not Bug Watch's
MATCH = {"us": "the match's details (map, mode, players' in-game names, result, times)", "fr": "(carte, mode, ",
         "ger": "(Karte, Modus, ", "ita": "(mappa, modalità, ", "spa": "(mapa, modo, ", "pol": "(mapa, tryb, ",
         "ru": "(карта, режим, ", "cz": "(mapa, režim, ", "jpn": "（マップ、モード、", "sc": "（地图、模式、",
         "fa": "(نقشه، حالت، "}   # ((نقشه، حالت، )


@functools.cache
def agreement(app: str) -> dict:
    return tomllib.loads((SRC / app / "words.toml").read_text(encoding="utf-8"))["agree_full"]


def point(text: str, starts: str) -> str:
    """The line of the agreement in `text` at the place of the English line that starts with `starts` (every
    language has the same lines, test_bugwatch.TheAgreementScreen)."""
    english = agreement("ruse_studio")["us"].split("\n")
    return text.split("\n")[next(i for i, line in enumerate(english) if line.startswith(starts))]


class VersionFourAsApproved(unittest.TestCase):
    def test_the_game_mode_is_out_of_the_crash_point(self):
        for app in APPS:
            full = agreement(app)
            self.assertEqual(sorted(full), sorted(schema.APP_LANGS), app)
            self.assertEqual(point(full["us"], "- when an app crashes:"), CRASH, app)
            for lang, text in full.items():
                crash = point(text, "- when an app crashes:")
                self.assertNotIn(MODE[lang], crash.lower(), f"{app} {lang}")
                self.assertNotIn(MODE_ANY[lang], crash.lower(), f"{app} {lang}: the mode in another wording")
                self.assertTrue(crash.endswith(SENT[lang]), f"{app} {lang}: {crash[-120:]}")
        for lang, word in MODE.items():   # the words looked for are the apps' own for the game mode
            help_file = SRC / "rusemod" / ("numberinfo.toml" if lang == "us" else f"numberinfo_{lang}.toml")
            self.assertIn(word, help_file.read_text(encoding="utf-8").lower(), lang)
            self.assertIn(MODE_ANY[lang], word, lang)
            self.assertIn(MODE_ANY[lang], MATCH[lang].lower(), lang)

    def test_the_unit_the_map_and_ruse_guards_match_mode_stay(self):
        texts = [agreement(app) for app in APPS]
        self.assertEqual(texts[0], texts[1])                     # the same text in both apps
        self.assertEqual(guard.TERMS_VERSION, 4)                  # still version 4: not released yet
        english = texts[0]["us"]
        for said in ("the map it was on", "a mod's map", "a mod's unit", "and the mods that were on"):
            self.assertIn(said, point(english, "- when an app crashes:"))
        for lang, text in texts[0].items():
            self.assertRegex(text.split("\n")[1], r"4|۴", lang)  # the version line
            self.assertIn(UNIT[lang], point(text, "- when an app crashes:"), lang)
            self.assertIn(MATCH[lang], point(text, "- What it may collect"), lang)


if __name__ == "__main__":
    unittest.main()
