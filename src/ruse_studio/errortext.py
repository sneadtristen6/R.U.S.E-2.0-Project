"""The Studio's error messages in the player's language (the owner, 2026-10-16: "Yes, fix the errors"; the Studio's
words were in ten languages but its errors in English only).

Each error is raised in English where it happens, as before (`raise StudioError(f"... {x} ...")`). errors.toml holds
every one of them as a template, its f-string's values as numbered blanks ({0}, {1}...), in the game's ten
languages. When an error goes to the page (rusemod.webui page_api, StudioApi.page_error), its English text is
matched against the templates and said again in the player's language with the same values filled in. A test lists
every StudioError in the Studio's code and fails when one has no entry, or an entry lacks a language or a blank
(tests/test_errortext.py), so a new error can't stay English unseen.

A value that is itself a message from deeper down (a file's mistake, the game's own words) stays as it came."""
from __future__ import annotations

import ast
import hashlib
import re
import tomllib
from functools import lru_cache
from pathlib import Path

FILE = Path(__file__).with_name("errors.toml")
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")
MIN_TEXT = 6   # a template with fewer letters of its own than this (a bare "{0}") isn't matched: it would take any text


def key_of(template: str) -> str:
    """An entry's name in errors.toml: from its English template, so it stays the same while the words do."""
    return "e" + hashlib.sha1(template.encode("utf-8")).hexdigest()[:10]


def template_of(node) -> str | None:
    """The English template of a StudioError's first argument (a string, an f-string, or such added together), or
    None when it's made otherwise (another error's text passed on)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.replace("{", "{{").replace("}", "}}")
    if isinstance(node, ast.JoinedStr):
        out, k = [], 0
        for v in node.values:
            if isinstance(v, ast.Constant):
                out.append(v.value.replace("{", "{{").replace("}", "}}"))
            else:
                out.append("{" + str(k) + "}")
                k += 1
        return "".join(out)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = template_of(node.left), template_of(node.right)
        if a is None or b is None:
            return None
        n = len(re.findall(r"(?<!\{)\{(\d+)\}(?!\})", a))  # the right side's blanks come after the left side's
        return a + re.sub(r"(?<!\{)\{(\d+)\}(?!\})", lambda m: "{" + str(int(m[1]) + n) + "}", b)
    return None


def templates_in(paths) -> list[str]:
    """Every StudioError template in these Python files, each once, in the order first met."""
    seen: dict[str, None] = {}
    for path in paths:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "StudioError" and n.args:
                t = template_of(n.args[0])
                if t is not None:
                    seen.setdefault(t, None)
    return list(seen)


def _literal(template: str) -> str:
    return re.sub(r"(?<!\{)\{\d+\}(?!\})", "", template).replace("{{", "{").replace("}}", "}")


def _pattern(template: str) -> re.Pattern:
    """A template as a pattern matching the whole of a text made from it: its words as they are, each blank as any
    text (as little as can still match)."""
    out, pos = [], 0
    for m in re.finditer(r"\{\{|\}\}|\{(\d+)\}", template):
        out.append(re.escape(template[pos:m.start()]))
        out.append(re.escape(m[0][0]) if m[1] is None else f"(?P<b{m[1]}>.*?)")
        pos = m.end()
    out.append(re.escape(template[pos:]))
    return re.compile("".join(out), re.S)


@lru_cache(maxsize=1)
def _entries() -> list[tuple[re.Pattern, dict, int]]:
    """(pattern, the entry's words by language, its own letters) for every entry, the most words of their own first:
    a text matching two templates is the more particular one's."""
    if not FILE.is_file():
        return []
    data = tomllib.loads(FILE.read_text(encoding="utf-8"))
    out = []
    for words in data.values():
        if not isinstance(words, dict) or "us" not in words:
            continue
        own = len(_literal(words["us"]).strip())
        if own >= MIN_TEXT:
            out.append((_pattern(words["us"]), words, own))
    out.sort(key=lambda e: -e[2])
    return out


def worded(text: str, lang: str) -> str:
    """`text` (an error as raised, in English) in `lang` (the game's language codes; "us" or "base": as it is). A text
    no template makes, or a template not in that language yet, stays as it is."""
    if lang not in LANGS or lang == "us":
        return text
    for pattern, words, _own in _entries():
        m = pattern.fullmatch(text)
        if m is None:
            continue
        said = words.get(lang)
        if not said:
            return text
        blanks = sorted((int(k[1:]), v) for k, v in m.groupdict().items())
        try:
            return said.format(*[v for _k, v in blanks])
        except (IndexError, KeyError, ValueError):
            return text
    return text
