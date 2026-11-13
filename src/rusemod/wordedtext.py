"""Texts written in English in the code, said again in the player's language (the owner, 2026-10-16: the apps' errors
and the build's lines in the game's ten languages; 2026-10-30: and Persian).

A text stays where it's made, in English (`raise StudioError(f"... {x} ...")`, `say(f"... {x} ...")`). A catalogue
(a TOML file) holds each one as a template, its f-string's values as numbered blanks ({0}, {1}...), in the ten
languages, under a name made from its English words (key_of). A text going to the player is matched against the
templates and said again in their language with the same values (worded). The catalogues are made from the code
itself (templates_in), and each has a test that fails when a text in the code has no entry, an entry lacks a
language, or a translation lost a blank. Users: ruse_studio.errortext (the Studio's errors), rusemod.buildtext (the
build's errors, warnings and lines)."""
from __future__ import annotations

import ast
import hashlib
import re
import tomllib
from functools import lru_cache
from pathlib import Path

LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")  # the apps' eleven (schema.APP_LANGS)
MIN_TEXT = 6   # a template with fewer letters of its own than this (a bare "{0}") isn't matched: it would take any text
BLANK = re.compile(r"(?<!\{)\{(\d+)\}(?!\})")


def key_of(template: str) -> str:
    """An entry's name in a catalogue: from its English template, so it stays the same while the words do."""
    return "e" + hashlib.sha1(template.encode("utf-8")).hexdigest()[:10]


def template_of(node, loose: bool = False) -> str | None:
    """The English template of a text in the code (a string, an f-string, or such added together), or None when it's
    made otherwise. `loose`: a part added on that isn't a string (a list joined, a call) becomes a blank too."""
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
        a, b = template_of(node.left, loose), template_of(node.right, loose)
        if loose:
            a = "{0}" if a is None else a
            b = "{0}" if b is None else b
        if a is None or b is None:
            return None
        n = len(BLANK.findall(a))  # the right side's blanks come after the left side's
        return a + BLANK.sub(lambda m: "{" + str(int(m[1]) + n) + "}", b)
    return None


def templates_in(paths, calls, loose: bool = False, min_text: int = MIN_TEXT) -> list[str]:
    """Every template in these Python files given to one of `calls` ({function or method name: which argument holds
    the text}), each once, in the order first met; none with fewer than `min_text` letters of its own (worded leaves
    those alone)."""
    seen: dict[str, None] = {}
    for path in paths:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            name = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            at = calls.get(name)
            if at is None or len(n.args) <= at:
                continue
            t = template_of(n.args[at], loose)
            if t is not None and len(_literal(t).strip()) >= min_text:
                seen.setdefault(t, None)
    return list(seen)


def _literal(template: str) -> str:
    return BLANK.sub("", template).replace("{{", "{").replace("}}", "}")


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


@lru_cache(maxsize=8)
def _entries(path: str, stamp: float) -> list[tuple[re.Pattern, dict, int]]:
    """(pattern, the entry's words by language, its own letters) for every entry of the catalogue at `path`, the most
    words of their own first: a text matching two templates is the more particular one's. (`stamp`: the file's time,
    so an edited catalogue is read again.)"""
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for words in data.values():
        if not isinstance(words, dict) or "us" not in words:
            continue
        own = len(_literal(words["us"]).strip())
        if own >= MIN_TEXT:
            out.append((_pattern(words["us"]), words, own))
    out.sort(key=lambda e: -e[2])
    return out


def worded(catalogue: Path, text: str, lang: str, within=frozenset()) -> str:
    """`text` (as the code made it, in English) in `lang` (the game's language codes; "us" or "base": as it is), from
    the catalogue at `catalogue`. A text no template makes, or a template not in that language yet, stays as it is.
    `within`: templates (their English) whose blanks hold a message of their own made deeper down: each blank is said
    in `lang` too by the catalogue's entries for that message, those whose "within" names that template, so no English
    is left inside it; a blank none of them makes stays as it came (never taken apart by an entry for other texts).
    Those entries say only such a blank: a whole text is never theirs ("{0}: its points lean on a bone..." would take
    a frame with its blank, leaving the frame English)."""
    if lang not in LANGS or lang == "us" or not isinstance(text, str):
        return text
    try:
        entries = _entries(str(catalogue), catalogue.stat().st_mtime)
    except (OSError, tomllib.TOMLDecodeError):
        return text
    return _said(entries, text, lang, within, None)


def _said(entries: list, text: str, lang: str, within, inside: str | None) -> str:
    """worded's matching: `inside` None, every entry but those for a frame's blank; else only the entries whose
    "within" is `inside` (the template whose blank `text` is)."""
    for pattern, words, _own in entries:
        if words.get("within") != inside:
            continue
        m = pattern.fullmatch(text)
        if m is None:
            continue
        said = words.get(lang)
        if not said:
            return text
        values = [v for _k, v in sorted((int(k[1:]), v) for k, v in m.groupdict().items())]
        if words["us"] in within:
            values = [_said(entries, v, lang, within, words["us"]) for v in values]
        try:
            return said.format(*values)
        except (IndexError, KeyError, ValueError):
            return text
    return text


def missing(catalogue: Path, templates: list[str]) -> list[str]:
    """What a catalogue's test checks, said plainly: each template with no entry, an entry without one of the ten
    languages, or a language whose blanks aren't the English's (or that doesn't format)."""
    entries = tomllib.loads(catalogue.read_text(encoding="utf-8")) if catalogue.is_file() else {}
    out = []
    for t in templates:
        words = entries.get(key_of(t))
        if words is None:
            out.append(f"no entry: {t}")
            continue
        for lang in LANGS:
            said = words.get(lang)
            if said is None:
                out.append(f"no {lang}: {t}")
            elif sorted(BLANK.findall(said)) != sorted(BLANK.findall(t)):
                out.append(f"{lang} blanks differ: {t}")
            else:
                try:
                    said.format(*["x"] * (len(BLANK.findall(t)) + 1))
                except (IndexError, KeyError, ValueError):
                    out.append(f"{lang} doesn't format: {t}")
    return out
