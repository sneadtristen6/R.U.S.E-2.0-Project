"""Display names for the game's data (labels.toml, the start of the schema DB, PLAN.md L2), for every app and tool.

The default is always the game's own names (`base`), which mods use. A modder can pick one of the game's ten
languages to read the tools in: property names, groups and nations. Anything without a translation falls back to
the game's name. Each app keeps its own screen words (the Studio's: ruse_studio/words.toml).
"""
from __future__ import annotations

import functools
import re
import tomllib
from pathlib import Path

LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")
BASE = "base"


@functools.cache
def _data() -> dict:
    return tomllib.loads(Path(__file__).with_name("labels.toml").read_text(encoding="utf-8"))


def languages() -> list[dict]:
    """The choices for the language selector, the game's names first."""
    names = _data()["languages"]
    return [{"code": BASE, "name": None}] + [{"code": c, "name": names[c]} for c in LANGS]


def _prop(path: str) -> str:
    return re.split(r"[\[.]", path, maxsplit=1)[0]


def label(path: str, lang: str = BASE) -> str:
    """A property's display name: `ProductionPrice[2]` in French is `Prix [2]`; the game's name when there's none."""
    prop = _prop(path)
    text = _data()["props"].get(prop, {}).get(lang) if lang != BASE else None
    return (text + path[len(prop):].replace("[", " [")) if text else path


def group(path: str) -> str:
    return _data()["props"].get(_prop(path), {}).get("group", "other")


def group_name(key: str, lang: str = BASE) -> str:
    names = _data()["groups"].get(key, {})
    return names.get(lang) or names.get("us") or key


GROUP_ORDER = ("identity", "cost", "combat", "movement", "vision", "menu", "weapon", "other")


def nation(n, lang: str = BASE) -> str:
    table = _data()["nations"]
    names = table.get(lang) or table[BASE]
    n = int(n)
    return names[n] if 0 <= n < len(names) else str(n)
