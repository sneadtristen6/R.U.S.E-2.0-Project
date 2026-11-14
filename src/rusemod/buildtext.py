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
SOURCES = ("rusemod/build.py", "rusemod/play.py", "ruse_studio/api.py", "ruse_launcher/api.py", "ruse_studio/homemove.py")
CALLS = {"say": 0, "warn": 0, "Finding": 1}
# a job's last words, in the files whose jobs the apps start (the units scenarios' U-16, 2026-11-14: Test in game's "R.U.S.E.
# is starting from ..." and Play's were English in every language): Job.start's words for a job done, Job.fail's for
# one refused before it starts, the words a job ends with when it broke (webui), the installs' and the backups' done
# words as their callers give them, and Play's and Test in game's own refusals (play.py's BuildError: "These mods have
# errors (listed above). Nothing was changed."). Only those calls of these files: their other lines are the page's
# step names ("unpack", "installing"), not words.
ENDS = {
    "ruse_studio/api.py": {"start": 1},
    "ruse_studio/era_units.py": {"start": 1},
    "ruse_studio/groundtex_calls.py": {"start": 1},
    "ruse_studio/horse_squad.py": {"start": 1},
    "ruse_studio/nations.py": {"start": 1},
    "ruse_studio/homemove.py": {"start": 1},
    "ruse_launcher/api.py": {"start": 1, "fail": 0, "_install_job": 1},
    "rusemod/backup.py": {"_backup_start": 2, "BackupError": 0},
    "rusemod/update.py": {"start": 1, "UpdateError": 0},
    "rusemod/webui.py": {"_said": 0},
    "rusemod/play.py": {"BuildError": 0},
    # the refusals of the calls both apps share (a backup's, the updates', the sign-in's: rusemod.update.words says
    # them, in both apps' page_error and the update check) and why a download failed (rusemod.mod_index plain's words,
    # said inside "GitHub couldn't be reached to look for updates (...)")
    "rusemod/ownedpass.py": {"OwnedPassError": 0},
    "rusemod/mod_index.py": {"_why": 0},
}

# how the build marks a finding in its lines: "warning: ..." (said at once) and "  error    ..." (the report)
_MARKED = re.compile(r"(?P<lead>\s*)(?P<level>warning|error|note)(?P<gap>:\s+|\s+)(?P<rest>\S.*)", re.S)
LEVELS = {  # the finding's level as the lines say it, in the apps' languages
    "warning": {"fr": "avertissement", "ger": "Warnung", "ita": "avviso", "spa": "aviso", "pol": "ostrzeżenie",
                "ru": "предупреждение", "cz": "varování", "jpn": "警告", "sc": "警告", "fa": "هشدار"},
    "error": {"fr": "erreur", "ger": "Fehler", "ita": "errore", "spa": "error", "pol": "błąd", "ru": "ошибка",
              "cz": "chyba", "jpn": "エラー", "sc": "错误", "fa": "خطا"},
    "note": {"fr": "remarque", "ger": "Hinweis", "ita": "nota", "spa": "nota", "pol": "uwaga", "ru": "заметка",
             "cz": "poznámka", "jpn": "注記", "sc": "备注", "fa": "یادداشت"},
}


def templates() -> list[str]:
    """Every build text in the code (SOURCES), then every job's last words (ENDS), as templates, each once."""
    out = wordedtext.templates_in([ROOT / s for s in SOURCES], CALLS, loose=True)
    for rel, calls in ENDS.items():
        out += [t for t in wordedtext.templates_in([ROOT / rel], calls, loose=True) if t not in out]
    return out


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
