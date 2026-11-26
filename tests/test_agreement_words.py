"""The agreement's version 5, the terms of use and privacy notice (2026-11-26; the owner's OK of the English, "2YES",
and his later answers, v5/CHANGES-V5-EN-2026-11-26.md), in the eleven languages of both apps. Version 4's crash point
(2026-11-13, his "Yes, agreement's fine.") stays true in it: Bug Watch's game crash details list the map, the unit the
game was making and the mods that were on, and never the game mode (nothing can read the mode from the game's crash
report)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import functools
import tomllib
import unittest
from pathlib import Path

from rusemod import guard, schema

SRC = Path(__file__).resolve().parents[1] / "src"
APPS = ("ruse_launcher", "ruse_studio")

# The game mode as each language said it in the crash point before his approval of version 4 (none may be in the
# game crash lines); each is also the apps' own word for the game mode in that language's number help (numberinfo),
# so the check can't pass on a misspelt word
MODE = {"us": "game mode", "fr": "mode de jeu", "ger": "spielmodus", "ita": "modalità di gioco", "spa": "modo de juego",
        "pol": "tryb gry", "ru": "режим игры", "cz": "herní režim", "jpn": "ゲームモード", "sc": "游戏模式",
        "fa": "حالت بازی"}   # (حالت بازی)
# The mode in ANY wording (a bare "der Modus", "режим", "モード", ...): each language's word for it alone, a piece of
# its phrase above; none may be in the game crash lines at all
MODE_ANY = {"us": "mode", "fr": "mode", "ger": "modus", "ita": "modalità", "spa": "modo", "pol": "tryb",
            "ru": "режим", "cz": "režim", "jpn": "モード", "sc": "模式", "fa": "حالت"}   # (حالت)
CRASH = "- right away, after a game the app started has crashed"   # the English line the game crash details start on


@functools.cache
def agreement(app: str) -> dict:
    return tomllib.loads((SRC / app / "words.toml").read_text(encoding="utf-8"))["agree_full"]


def crash_lines() -> range:
    """The lines of the game crash details: their first line and its sub-points (every language has the same lines,
    test_bugwatch.TheAgreementScreen)."""
    english = agreement("ruse_studio")["us"].split("\n")
    start = next(i for i, line in enumerate(english) if line.startswith(CRASH))
    end = start + 1
    while english[end].startswith("  - "):
        end += 1
    return range(start, end)


class VersionFiveAsApproved(unittest.TestCase):
    def test_the_game_mode_is_out_of_the_crash_details(self):
        rows = crash_lines()
        self.assertGreater(len(rows), 3)
        for app in APPS:
            full = agreement(app)
            self.assertEqual(sorted(full), sorted(schema.APP_LANGS), app)
            for lang, text in full.items():
                crash = " ".join(text.split("\n")[i] for i in rows).lower()
                self.assertNotIn(MODE[lang], crash, f"{app} {lang}")
                self.assertNotIn(MODE_ANY[lang], crash, f"{app} {lang}: the mode in another wording")
        for lang, word in MODE.items():   # the words looked for are the apps' own for the game mode
            help_file = SRC / "rusemod" / ("numberinfo.toml" if lang == "us" else f"numberinfo_{lang}.toml")
            self.assertIn(word, help_file.read_text(encoding="utf-8").lower(), lang)
            self.assertIn(MODE_ANY[lang], word, lang)

    def test_the_unit_and_the_map_stay_and_it_is_version_5(self):
        texts = [agreement(app) for app in APPS]
        self.assertEqual(texts[0], texts[1])                     # the same text in both apps
        self.assertEqual(guard.TERMS_VERSION, 5)
        english = texts[0]["us"].split("\n")
        crash = " ".join(english[i] for i in crash_lines())
        for said in ("the map (one of the game's own maps by its name", "a mod's map", "a mod's unit",
                     "the unit the game was making, when the apps can read it from the game's crash report",
                     "which mods were on"):
            self.assertIn(said, crash)
        unit = next(i for i in crash_lines() if "the unit the game was making" in english[i])
        for lang, text in texts[0].items():
            lines = text.split("\n")
            self.assertEqual(len(lines), len(english), lang)
            self.assertRegex(lines[1], r"5|۵", lang)               # the version line
            self.assertTrue(lines[unit].startswith("  - "), f"{lang}: {lines[unit][:60]}")
            self.assertNotIn("[fill", text, lang)                  # the release date is filled in


class TheStopAsTheLockDoesIt(unittest.TestCase):
    """The words follow the lock this branch ships. The owner's "A" of 2026-11-26: the release goes WITHOUT the clean
    stop (legal/clean-stop stays out of the join), so the lock still stops a cheat copy by an error on the end-of-match
    screen, a crash, and the Launcher sends RUSE Guard's line from the game's crash report. While the lock does that,
    the agreement must say so and must not promise a clean close; once a lock without that error comes in (the clean
    stop), this fails until the words change with it."""

    CRASH_WORDS = ("the game crashes to the desktop", "takes only ruse guard's line from the game's crash report")
    CLEAN_WORDS = ("without a crash", "closes the game at that match's end-of-match screen", "it then closes the game",
                   "it never reads the game's crash reports")

    def test_the_agreement_says_what_the_lock_does(self):
        lock = (SRC / "rusemod" / "gamescripts" / "fairplay_lock.py25").read_text(encoding="utf-8")
        crashes = "raise RuntimeError(mark())" in lock   # the end screen's stop: an error, so a crash
        for app in APPS:
            data = tomllib.loads((SRC / app / "words.toml").read_text(encoding="utf-8"))
            full, short = data["agree_full"]["us"].lower(), data["agree_guard"]["us"].lower()
            if crashes:
                for said in self.CRASH_WORDS:
                    self.assertIn(said, full, app)
                self.assertIn("stops the game with a crash", short, app)
                for promise in self.CLEAN_WORDS:
                    self.assertNotIn(promise, full, app)
                    self.assertNotIn(promise, short, app)
            else:
                for said in self.CRASH_WORDS + ("stops the game with a crash",):
                    self.assertNotIn(said, full + short, app)

    def test_the_launcher_line_for_a_cheat_copy_says_it_too(self):
        lock = (SRC / "rusemod" / "gamescripts" / "fairplay_lock.py25").read_text(encoding="utf-8")
        line = tomllib.loads((SRC / "ruse_launcher" / "words.toml").read_text(encoding="utf-8"))["fair_offline"]["us"]
        if "raise RuntimeError(mark())" in lock:
            self.assertIn("stops the game with a crash", line)
            self.assertNotIn("closes the game", line)


if __name__ == "__main__":
    unittest.main()
