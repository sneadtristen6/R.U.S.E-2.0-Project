"""Which language the apps suggest on their first start, for both apps' "Choose your language" screen.

The best clue is the language R.U.S.E. itself is set to in Steam (the game's Properties > Language, kept in its
manifest as `UserConfig/language`): a player who plays the game in French wants the apps in French, even on a PC
whose own screens are in English. Then this PC's own language, then English. The screen always opens on the first
start, so a wrong guess costs one click.
"""
from __future__ import annotations

import locale
import os
import re
import sys

# Steam's names for a game's language (its API language codes) -> the game's language folders
STEAM_CODES = {"english": "us", "french": "fr", "german": "ger", "italian": "ita", "spanish": "spa", "latam": "spa",
               "polish": "pol", "russian": "ru", "czech": "cz", "japanese": "jpn", "schinese": "sc"}

# A language tag's first part, as Windows or Python gives it ("fr-FR", "de_DE", "zh_CN") -> the game's folder
_TAG_CODES = {"en": "us", "fr": "fr", "de": "ger", "it": "ita", "es": "spa", "pl": "pol", "ru": "ru", "cs": "cz",
              "ja": "jpn", "zh": "sc"}


def language_code(tag: str) -> str:
    """A language tag as Windows or Python gives it ("fr-FR", "de_DE", "zh_CN") -> the game's code, or "us"."""
    head = re.split(r"[-_.@]", (tag or "").strip().lower())[0]
    return _TAG_CODES.get(head, "us")


def steam_code(name: str | None) -> str | None:
    """Steam's name for a language ("french") -> the game's code ("fr"), or None for one the game doesn't have."""
    return STEAM_CODES.get((name or "").strip().lower())


def pc_language() -> str:
    """The language this PC shows its own screens in, as a tag."""
    if sys.platform == "win32":
        import ctypes
        return locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), "en")
    return locale.getlocale()[0] or os.environ.get("LANG", "") or "en"


def suggest(steam_language: str | None, pc_tag: str | None) -> tuple[str, str]:
    """(code, where it came from): "steam" (the game's language in Steam), "pc" (this PC's language, when the game
    has it) or "default" (English)."""
    code = steam_code(steam_language)
    if code:
        return code, "steam"
    head = re.split(r"[-_.@]", (pc_tag or "").strip().lower())[0]
    if head in _TAG_CODES:
        return _TAG_CODES[head], "pc"
    return "us", "default"


class LanguageCalls:
    """The window API's "Choose your language" calls, for both apps (a mixin next to home.PrefsCalls: the API has
    `_find`, and may have `_ui_language`, a stand-in for this PC's language in tests)."""

    def _steam_language(self) -> str | None:
        try:
            found = self._find()
        except Exception:  # noqa: BLE001  (no Steam, or its files unreadable: the PC's language decides)
            return None
        return (found or {}).get("language")

    def _pc_tag(self) -> str | None:
        try:
            return getattr(self, "_ui_language", pc_language)()
        except Exception:  # noqa: BLE001  (a PC whose language can't be read still gets an app)
            return None

    def language_choice(self) -> dict:
        """What "Choose your language" starts on and whether it opens by itself: `suggested` (a game code), `from`
        ("steam", "pc" or "default"), `chosen` (the player has picked one on that screen: then it only opens from the
        language button)."""
        code, source = suggest(self._steam_language(), self._pc_tag())
        return {"suggested": code, "from": source, "chosen": bool(self.prefs().get("lang_chosen"))}
