"""The Launcher's refusals in the player's language, the way the Studio's are (ruse_studio.errortext; the export
scenarios' FE-9, 2026-11-14: every refusal of the Launcher was English, whatever its language; the owner, 2026-11-14:
"There shouldn't be anywhere where it's like relying too heavily on them to understand things.").

Each refusal is raised in English where it happens, as before (`raise LauncherError(f"... {x} ...")`). The refusals
the Launcher passes on as they came are the same words: the library's (rusemod.library LibraryError, a mod file's
rusemod.package PackageError inside it), the mod list's (rusemod.mod_index ModIndexError) and a join code's
(rusemod.lock CodeError). errors.toml holds every one of them as a template, its f-string's values as numbered blanks
({0}, {1}...), in the apps' eleven languages (rusemod.wordedtext). When a page call is refused (rusemod.webui
page_api, LauncherApi.page_error), or a job fails (LauncherApi.job), its English is matched against the templates and
said again in the Launcher's language with the same values filled in. A test lists every such refusal in the code and
fails when one has no entry, or an entry lacks a language or a blank (tests/test_launcher_errortext.py).

A value that is itself a message from deeper down stays as it came, but in a frame of WITHIN its blank is said in the
Launcher's language too, by entries marked with that frame ("within"): why a download failed (rusemod.mod_index
plain's words) inside the mod list's refusals."""
from __future__ import annotations

from pathlib import Path

from rusemod import wordedtext
from rusemod.wordedtext import LANGS, key_of, template_of  # noqa: F401  (the Launcher's names for them)

FILE = Path(__file__).with_name("errors.toml")
SRC = Path(__file__).parents[1]
# the files whose refusals reach the Launcher's page, and the calls making them ({call: which argument holds its text})
SOURCES = {
    "ruse_launcher/api.py": {"LauncherError": 0, "ModIndexError": 0, "_say": 0},   # (_say: a sentence for the screen)
    "rusemod/library.py": {"LibraryError": 0},
    "rusemod/package.py": {"PackageError": 0},
    "rusemod/mod_index.py": {"ModIndexError": 0},
    "rusemod/lock.py": {"CodeError": 0},
}
# frames whose blank holds a message made deeper down: {the frame's template: (the file making those messages, {the call
# making one: which argument holds its text})}
WITHIN = {f: (SRC / "rusemod" / "mod_index.py", {"_why": 0}) for f in (
    "The mod list couldn't be loaded ({0}), and there's no copy from before.",
    "{0} couldn't be downloaded ({1}).",
)}


def templates() -> list[str]:
    """Every refusal of the Launcher's in the code (SOURCES), each once, in the order first met; then, for each frame
    of WITHIN among them, every template of the messages its blank holds."""
    out: list[str] = []
    for rel, calls in SOURCES.items():
        out += [t for t in wordedtext.templates_in([SRC / rel], calls, min_text=0) if t not in out]
    for frame, (source, calls) in WITHIN.items():
        if frame in out:
            out += [t for t in wordedtext.templates_in([source], calls, min_text=0) if t not in out]
    return out


def worded(text: str, lang: str) -> str:
    """`text` (a refusal as raised, in English) in `lang` (the apps' language codes; "us" or "base": as it is). A text
    no template makes, or a template not in that language yet, stays as it is; a frame of WITHIN has its blank said in
    `lang` too."""
    return wordedtext.worded(FILE, text, lang, within=frozenset(WITHIN))
