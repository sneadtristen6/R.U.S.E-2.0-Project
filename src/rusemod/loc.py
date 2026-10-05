"""Text mods (docs/MOD_FORMAT.md §6): a mod's text/*.csv rows become entries in the game's text tables.

A mod's `text/<table>.csv` adds texts to that table, in every language: `text/baseunite.csv` goes into the unit names.
Columns: `key`, `game_key`, then one per language, with the game's names (us fr ger ita spa pol ru cz jpn sc) or the
usual codes (en de it es pl cs ja zh). An empty cell falls back to `us`, and the `dev` language gets the `us` text.

Mod data refers to a row by its key: `NameInMenuToken = loc('r2.unit.x.name')`. Each row gets a game key (a name of up
to 10 characters, as the game's own keys are): its `game_key` cell, or else the mod's `text_prefix` plus a number,
handed out in sorted key order so every PC gets the same. A key the game or another mod already uses is an error that
names both. A row whose key is `game:NAME` or `game:0x...` changes an existing game text instead."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from .dic import Dic, name_to_key

LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")
ALIASES = {"en": "us", "de": "ger", "it": "ita", "es": "spa", "pl": "pol", "cs": "cz", "ja": "jpn", "zh": "sc"}
DIC_DIR = "genlocalisation\\ww2\\localisation"
PACK = "ZZ_Win.dat"  # the pack holding every .dic


class TextError(Exception):
    pass


@dataclass
class TextRow:
    dictionary: str          # the game dictionary, from the csv's file name: "baseunite"
    key: str                 # the mod's key ("r2.unit.x.name"), or "game:NAME" / "game:0x..." to change a game text
    game_key: str            # the game key's name, or "" to hand one out
    texts: dict              # language folder -> text
    mod: str = ""
    file: str = ""
    line: int = 0

    def at(self) -> str:
        return f"{self.mod} ({self.file}:{self.line})"


@dataclass
class TextPlan:
    keys: dict = field(default_factory=dict)      # mod key -> game key name, for loc()
    changes: dict = field(default_factory=dict)   # dictionary -> {game key (int): (row, texts)}
    warnings: list = field(default_factory=list)  # (message, row)


def member(dictionary: str, lang: str) -> str:
    """The path of a dictionary inside ZZ_Win.dat, for a language folder or `dev`."""
    folder = "dev" if lang == "dev" else f"translations\\{lang}"
    return f"{DIC_DIR}\\{folder}\\{dictionary}.dic"


def read_csv(text: str, dictionary: str, mod: str = "", file: str = "") -> list[TextRow]:
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    if not rows:
        return []
    head = [h.strip().lower() for h in rows[0]]
    if "key" not in head:
        raise TextError(f"{file}:1: the first row must name the columns, starting with `key`")
    cols = {}
    for i, h in enumerate(head):
        if h in ("key", "game_key"):
            cols[h] = i
        elif h in LANGS or h in ALIASES:
            lang = ALIASES.get(h, h)
            if lang in cols:
                raise TextError(f"{file}:1: two columns for the language {lang}")
            cols[lang] = i
        elif h:
            raise TextError(f"{file}:1: unknown column {h!r}; languages are {' '.join(LANGS)} "
                            f"(or {' '.join(ALIASES)})")
    out, seen = [], {}
    for n, cells in enumerate(rows[1:], start=2):
        if not any(c.strip() for c in cells):
            continue
        get = lambda c: cells[cols[c]].strip() if c in cols and cols[c] < len(cells) else ""  # noqa: E731
        key = get("key")
        if not key:
            raise TextError(f"{file}:{n}: a row without a key")
        if key in seen:
            raise TextError(f"{file}:{n}: the key {key!r} is already on line {seen[key]}")
        seen[key] = n
        texts = {lang: get(lang) for lang in LANGS if get(lang)}
        if "us" not in texts:
            raise TextError(f"{file}:{n}: {key!r} has no `us` (English) text, which the other languages fall back to")
        game_key = get("game_key")
        if game_key:
            try:
                name_to_key(game_key)
            except ValueError as exc:
                raise TextError(f"{file}:{n}: {exc}") from None
        out.append(TextRow(dictionary, key, game_key, texts, mod, file, n))
    return out


def _game_key(spec: str) -> int:
    body = spec[len("game:"):]
    return int(body, 16) if body.lower().startswith("0x") else name_to_key(body)


def plan(mods, game_keys: dict) -> TextPlan:
    """`mods`: [(mod id, text_prefix, [TextRow])] in load order. `game_keys`: dictionary -> set of the keys the game
    already uses in it (any language). Hands out game keys and checks every clash."""
    result = TextPlan()
    taken: dict[tuple[str, int], TextRow] = {}   # (dictionary, key) -> the mod row that took it
    defined: dict[str, TextRow] = {}             # mod key -> row
    for mod_id, prefix, rows in mods:
        new = [r for r in rows if not r.key.startswith("game:")]
        auto = sorted((r for r in new if not r.game_key), key=lambda r: (r.key, r.dictionary))
        assigned: dict[int, str] = {}  # id(row) -> the game key handed out (rows themselves stay as read)
        if auto:
            width = 8 - len(prefix or "")
            if not prefix:
                raise TextError(f"{mod_id}: {len(auto)} text row(s) have no game_key; set text_prefix in mod.toml "
                                f"(e.g. text_prefix = \"R2\") or give each row a game_key")
            try:
                name_to_key(prefix)
            except ValueError:
                raise TextError(f"{mod_id}: text_prefix {prefix!r} must be 1-7 characters of 0-9 A-Z _ a-z") from None
            if len(auto) >= 10 ** width:
                raise TextError(f"{mod_id}: text_prefix {prefix!r} leaves room for {10 ** width - 1} texts, "
                                f"but the mod has {len(auto)}")
            for i, r in enumerate(auto, start=1):
                assigned[id(r)] = f"{prefix}{i:0{width}d}"
        for r in rows:
            if r.key.startswith("game:"):
                try:
                    k = _game_key(r.key)
                except ValueError as exc:
                    raise TextError(f"{r.at()}: {exc}") from None
                if k not in game_keys.get(r.dictionary, set()):
                    # not a game rule: our text keys
                    raise TextError(f"{r.at()}: {r.key} isn't a text in the game's {r.dictionary}.dic")
                prev = result.changes.get(r.dictionary, {}).get(k)
                if prev and prev[0].mod != r.mod:
                    result.warnings.append((f"{r.at()} changes the game text {r.key} in {r.dictionary}.dic, which "
                                            f"{prev[0].at()} changed too; the later one wins", r))
                result.changes.setdefault(r.dictionary, {})[k] = (r, r.texts)
                continue
            if r.key in defined:
                raise TextError(f"{r.at()}: the text key {r.key!r} is already defined by {defined[r.key].at()}")
            defined[r.key] = r
            game_key = r.game_key or assigned[id(r)]
            k = name_to_key(game_key)
            if k in game_keys.get(r.dictionary, set()):
                # not a game rule: our text keys
                raise TextError(f"{r.at()}: the game key {game_key} is already a text in the game's "
                                f"{r.dictionary}.dic; pick another game_key or text_prefix")
            if (r.dictionary, k) in taken:
                # not a game rule: our text keys
                raise TextError(f"{r.at()}: the game key {game_key} is already used by {taken[(r.dictionary, k)].at()}")
            taken[(r.dictionary, k)] = r
            result.keys[r.key] = game_key
            result.changes.setdefault(r.dictionary, {})[k] = (r, r.texts)
    return result


def apply(text_plan: TextPlan, read) -> tuple[dict, list[str]]:
    """Write the planned texts. `read(member path)` returns a .dic's bytes, or None if the pack doesn't have it.
    Returns ({member path: new bytes}, notes)."""
    changed, notes = {}, []
    for dictionary, entries in sorted(text_plan.changes.items()):
        missing = []
        for lang in LANGS + ("dev",):
            path = member(dictionary, lang)
            raw = read(path)
            if raw is None:
                missing.append(lang)
                continue
            dic = Dic(raw)
            for k, (_row, texts) in sorted(entries.items()):
                text = texts.get(lang) or texts["us"] if lang != "dev" else texts["us"]
                if dic.text(k) is None:
                    dic.add(k, text)
                elif dic.text(k) != text:
                    dic.set_text(k, text)
            data = dic.to_bytes()
            if data != raw:
                changed[path] = data
        if len(missing) == len(LANGS) + 1:
            # not a game rule: our text keys
            raise TextError(f"the game has no dictionary called {dictionary}.dic (text/{dictionary}.csv)")
        if missing:
            notes.append(f"{dictionary}.dic isn't in the {', '.join(missing)} folder(s); those languages don't get "
                         f"its texts")
    return changed, notes


def game_keys_of(read, dictionaries) -> dict:
    """dictionary -> every key the game uses in it, across all language folders."""
    out = {}
    for dictionary in dictionaries:
        keys = set()
        for lang in LANGS + ("dev",):
            raw = read(member(dictionary, lang))
            if raw is not None:
                keys |= {e.key for e in Dic(raw).entries}
        out[dictionary] = keys
    return out
