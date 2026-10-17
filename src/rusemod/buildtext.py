"""The build's errors, warnings and lines in the player's language (the owner, 2026-10-16: "Translate the 79 build
errors and warnings and the build's progress lines"), the way the Studio's errors are (rusemod.wordedtext).

The build and the apps' build jobs say their lines in English as before (say(...), warn(...), Finding(level, ...)).
buildtext.toml holds each as a template in the ten languages; a job's lines, its message and a failed build's errors
are said again in the player's language when the app hands them to its page (StudioApi.job / test_problems,
LauncherApi.job). A line made of words from deeper down (a file's own mistake, a step's notes) stays English, and so
do the engine's own checks of a mod's files, for later (the owner's choice, 2026-10-16). tests/test_buildtext.py lists
every such text in the code and fails when one has no entry, a language or a blank."""
from __future__ import annotations

import re
from pathlib import Path

from . import wordedtext

FILE = Path(__file__).with_name("buildtext.toml")
ROOT = Path(__file__).parents[1]
# the files whose say / warn / Finding texts go to the player, and which argument holds the text
SOURCES = ("rusemod/build.py", "rusemod/play.py", "ruse_studio/api.py", "ruse_launcher/api.py")
CALLS = {"say": 0, "warn": 0, "Finding": 1}

# how the build marks a finding in its lines: "warning: ..." (said at once) and "  error    ..." (the report)
_MARKED = re.compile(r"(?P<lead>\s*)(?P<level>warning|error|note)(?P<gap>:\s+|\s+)(?P<rest>\S.*)", re.S)
LEVELS = {  # the finding's level as the lines say it, in the ten languages
    "warning": {"fr": "avertissement", "ger": "Warnung", "ita": "avviso", "spa": "aviso", "pol": "ostrzeżenie",
                "ru": "предупреждение", "cz": "varování", "jpn": "警告", "sc": "警告"},
    "error": {"fr": "erreur", "ger": "Fehler", "ita": "errore", "spa": "error", "pol": "błąd", "ru": "ошибка",
              "cz": "chyba", "jpn": "エラー", "sc": "错误"},
    "note": {"fr": "remarque", "ger": "Hinweis", "ita": "nota", "spa": "nota", "pol": "uwaga", "ru": "заметка",
             "cz": "poznámka", "jpn": "注記", "sc": "备注"},
}


def templates() -> list[str]:
    """Every build text in the code (SOURCES), as templates."""
    return wordedtext.templates_in([ROOT / s for s in SOURCES], CALLS, loose=True)


def worded(text: str, lang: str) -> str:
    """A build text, line or finding in `lang` (as it is in English, for "us" and "base", and for what no template
    makes)."""
    if not isinstance(text, str) or lang in ("us", "base") or lang not in wordedtext.LANGS:
        return text
    m = _MARKED.fullmatch(text)  # a finding as the lines mark it: its own words first (else "warning: {0}" would
    if m is not None:            # take the line and leave the finding English)
        rest = wordedtext.worded(FILE, m["rest"], lang)
        if rest != m["rest"]:
            return f"{m['lead']}{LEVELS[m['level']].get(lang, m['level'])}{m['gap']}{rest}"
    return wordedtext.worded(FILE, text, lang)


def worded_view(view: dict, lang: str) -> dict:
    """A job's view (rusemod.webui Job.view) with its lines, message and errors in `lang`."""
    if lang in ("us", "base") or lang not in wordedtext.LANGS:
        return view
    out = dict(view)
    if isinstance(out.get("lines"), list):
        out["lines"] = [worded(line, lang) for line in out["lines"]]
    if isinstance(out.get("message"), str):
        out["message"] = worded(out["message"], lang)
    if isinstance(out.get("errors"), list):
        out["errors"] = [worded(e, lang) for e in out["errors"]]
    return out
