"""The Studio's error messages in the player's language (the owner, 2026-10-16: "Yes, fix the errors"; the Studio's
words were in ten languages but its errors in English only).

Each error is raised in English where it happens, as before (`raise StudioError(f"... {x} ...")`). errors.toml holds
every one of them as a template, its f-string's values as numbered blanks ({0}, {1}...), in the game's ten
languages (rusemod.wordedtext). When an error goes to the page (rusemod.webui page_api, StudioApi.page_error), its
English text is matched against the templates and said again in the player's language with the same values filled
in. A test lists every StudioError in the Studio's code and fails when one has no entry, or an entry lacks a language
or a blank (tests/test_errortext.py), so a new error can't stay English unseen.

A value that is itself a message from deeper down (a file's mistake, the game's own words) stays as it came."""
from __future__ import annotations

from pathlib import Path

from rusemod import wordedtext
from rusemod.wordedtext import LANGS, key_of, template_of  # noqa: F401  (the Studio's names for them)

FILE = Path(__file__).with_name("errors.toml")


def templates_in(paths) -> list[str]:
    """Every StudioError template in these Python files, each once, in the order first met."""
    return wordedtext.templates_in(paths, {"StudioError": 0}, min_text=0)


def worded(text: str, lang: str) -> str:
    """`text` (an error as raised, in English) in `lang` (the game's language codes; "us" or "base": as it is). A text
    no template makes, or a template not in that language yet, stays as it is."""
    return wordedtext.worded(FILE, text, lang)
