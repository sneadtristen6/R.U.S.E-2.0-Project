"""The Studio's error messages in the player's language (the owner, 2026-10-16: "Yes, fix the errors"; the Studio's
words were in ten languages but its errors in English only).

Each error is raised in English where it happens, as before (`raise StudioError(f"... {x} ...")`). errors.toml holds
every one of them as a template, its f-string's values as numbered blanks ({0}, {1}...), in the game's ten
languages (rusemod.wordedtext). When an error goes to the page (rusemod.webui page_api, StudioApi.page_error), its
English text is matched against the templates and said again in the player's language with the same values filled
in. A test lists every StudioError in the Studio's code and fails when one has no entry, or an entry lacks a language
or a blank (tests/test_errortext.py), so a new error can't stay English unseen.

A value that is itself a message from deeper down (a file's mistake, the game's own words) stays as it came, but in a
frame of WITHIN: its blank holds a message of its own whose every wording is in errors.toml too (the test lists them
from the code that makes them; each entry marked with its frame, "within"), said in the player's language with the
frame, so no English is left inside it. Only those entries say that blank: a message none of them makes stays as it
came, never taken apart by a short entry for other texts ("{0} has no {1}")."""
from __future__ import annotations

from pathlib import Path

from rusemod import wordedtext
from rusemod.wordedtext import LANGS, key_of, template_of  # noqa: F401  (the Studio's names for them)

FILE = Path(__file__).with_name("errors.toml")
# Frames whose blank holds a message made deeper down: {the frame's template: (the file making those messages, {the
# call making one: which argument holds its text})}. The Horse Squad's builder (rusemod.horsesquad) refuses in plain
# words (HorseSquadError), and horse_squad.py passes its refusal on inside this frame (review 2026-11-12: the frame was
# said in the player's language with the builder's sentence left English inside it).
WITHIN = {"The Generic Horse can't be made from your game: {0}":
          (Path(__file__).parents[1] / "rusemod" / "horsesquad.py", {"HorseSquadError": 0}),
          # why the era units list or one of its files couldn't be downloaded (rusemod.mod_index plain's words: the
          # units scenarios' U-12, "[WinError 10061] No connection could be made..." inside English words)
          "the era units list couldn't be loaded ({0})": (Path(__file__).parents[1] / "rusemod" / "mod_index.py",
                                                          {"_why": 0}),
          "{0} couldn't be downloaded ({1})": (Path(__file__).parents[1] / "rusemod" / "mod_index.py", {"_why": 0})}
# the Studio's other refusals that reach the page whole, said in the player's language like a StudioError: the era
# units list's and downloads' (era_units.py: a download job's refusal, and why the list couldn't be had), and the mod's
# changes file broken by hand (edits.py EditsFileError: the units scenarios' U-11, its frame in every language now; the
# mistake it names inside, the file reader's own words, stays as it came)
OTHERS = {"EraDownloadError": 0, "EditsFileError": 0}


def templates_in(paths) -> list[str]:
    """Every StudioError template in these Python files (and of OTHERS), each once, in the order first met; then, for
    each frame of WITHIN among them, every template of the messages its blank holds (said in the player's language
    too)."""
    out = wordedtext.templates_in(paths, {"StudioError": 0, **OTHERS}, min_text=0)
    for frame, (source, calls) in WITHIN.items():
        if frame in out:
            out += [t for t in wordedtext.templates_in([source], calls, min_text=0) if t not in out]
    return out


def worded(text: str, lang: str) -> str:
    """`text` (an error as raised, in English) in `lang` (the game's language codes; "us" or "base": as it is). A text
    no template makes, or a template not in that language yet, stays as it is; a frame of WITHIN has its blank said in
    `lang` too."""
    return wordedtext.worded(FILE, text, lang, within=frozenset(WITHIN))
