"""The mod check's problems in plain words, each with a fix the window can offer (the owner, 2026-10-10: "all of the
error messages should be able to have a fix or like a fix button or like a how-to fix in like plain people
language").

A problem as a reader says it ("maps/SuperCrossRoads4/terrain.toml: stroke 1: the water brush needs level") is read
back into its parts: the file and its map, the item of the file it's about (stroke 1), and what's wrong (a missing
value, a setting the game doesn't know, a value it can't use, a file it can't read). The window says it in the
player's language from those parts (words.toml `pp_*`) and keeps the reader's own words under Details.

The fixes, best first:
- fill: a missing value the Studio knows a safe one for (a water stroke's level is the map's own water height:
  Studio 0.7.0 saved water strokes without it);
- remove_key: take out a setting the game doesn't know;
- remove_item: take out only that item (a stroke, an object, a spawn...); the rest of the file stays;
- set_aside: the whole file put aside (renamed, never lost), the last resort.
The edits themselves (`edit`) work on the file's text, so everything else in it stays as written, and each is checked
by reading the file back: only the item or setting fixed may differ.
"""
from __future__ import annotations

import re
import tomllib

# the items of a map file, as its reader names them in a problem -> (its table in the file, its words key)
ITEMS = {"stroke": "stroke", "erase area": "erase", "object": "object", "move": "move", "remove": "remove",
         "set": "set", "place": "place", "spawn": "spawn", "start": "start", "paint": "paint", "block": "block",
         "open": "open", "road": "road"}
_AT = re.compile(r"^(?P<file>maps/(?P<map>[^/:]+)/(?P<name>[\w.-]+\.toml)): (?:(?P<item>"
                 + "|".join(sorted(map(re.escape, ITEMS), key=len, reverse=True))
                 + r") (?P<n>\d+)(?::\s*|\s+))?(?P<rest>.*)$", re.S)
_RNDF = re.compile(r"^(?P<file>src/[^:]+\.rndf):(?P<line>\d+)(?::\d+)?: (?P<rest>.*)$", re.S)
_CSV = re.compile(r"^(?P<file>text/[^:]+\.csv):(?P<line>\d+): (?P<rest>.*)$", re.S)
_MANIFEST = re.compile(r"(?:^|[\\/])mod\.toml: (?P<rest>.*)$", re.S)
_TOML_SYNTAX = re.compile(r"\(at line \d+, column \d+\)|^Invalid |^Expected |^Unclosed |^Illegal |^Unterminated ")
_NEEDS = [re.compile(p) for p in (r"^the \w+ brush needs (?P<keys>[\w, ]+)$", r"^(?P<keys>[\w]+) is missing$",
                                  r"^has no (?P<keys>\w+)$", r"^an? [\w ]+? needs (?:its )?(?P<keys>\w+(?: and \w+)?)\b")]
_UNKNOWN = re.compile(r"^unknown key '(?P<key>[^']+)'")
_BAD = re.compile(r"^(?P<key>[a-z_]\w*)(?:,| (?:must|is|are|goes|can't|has)\b)")

# the safe values the Studio can fill in, by (table, key)
FILLS = {("stroke", "level")}


def _keys(text: str) -> list[str]:
    return [k for k in re.split(r",\s*|\s+and\s+", text.strip()) if k]


def explain(problem: dict) -> dict:
    """The problem (a dict of the mod check) with its plain parts and its fixes added: "plain" {kind, file, map,
    table (the file's table for its item), item (the item's words key), n (its number, from 1), key / keys} and
    "fixes" [{fix, file, table, n, key}], best first. Kinds: missing, unknown_key, bad_value, unreadable, map_file
    (wrong in a way the parts don't say), unit_file, text_file, manifest, other."""
    raw = str(problem.get("problem", ""))
    out = dict(problem)
    plain: dict = {"kind": "other", "file": problem.get("file")}
    fixes: list = []
    m = _AT.match(raw)
    if m:
        plain.update(file=m["file"], map=m["map"])
        rest = m["rest"].strip()
        if m["item"]:
            table = ITEMS[m["item"]]
            n = int(m["n"])
            plain.update(table=table, item=table, n=n)
            base = {"file": m["file"], "table": table, "n": n}
            needs = next((x for x in (p.match(rest) for p in _NEEDS) if x), None)
            unknown = _UNKNOWN.match(rest)
            if needs:
                keys = _keys(needs["keys"])
                plain.update(kind="missing", keys=keys, key=keys[0])
                fixes += [dict(base, fix="fill", key=k) for k in keys if (table, k) in FILLS]
            elif unknown:
                plain.update(kind="unknown_key", key=unknown["key"])
                fixes.append(dict(base, fix="remove_key", key=unknown["key"]))
            else:
                bad = _BAD.match(rest)
                plain.update(kind="bad_value", key=bad["key"] if bad else None)
            fixes.append(dict(base, fix="remove_item"))
        elif _TOML_SYNTAX.search(rest):
            plain["kind"] = "unreadable"
        else:
            plain["kind"] = "map_file"
    elif (m := _RNDF.match(raw)) or (m := _CSV.match(raw)):
        plain.update(kind="unit_file" if m["file"].endswith(".rndf") else "text_file", file=m["file"],
                     line=int(m["line"]))
        fixes.append({"fix": "set_aside", "file": m["file"]})
    elif _MANIFEST.search(raw):
        plain.update(kind="manifest", file="mod.toml")
    if problem.get("set_aside") and not any(f["fix"] == "set_aside" for f in fixes):
        fixes.append({"fix": "set_aside", "file": problem.get("file") or plain.get("file")})
    out["plain"] = plain
    out["fixes"] = fixes
    return out


# --- the edits, on the file's text -------------------------------------------------------------------------------
_HEADER = re.compile(r"^\[\[?\s*[A-Za-z_][\w.-]*\s*\]\]?\s*(?:#.*)?$")
_ARRAY_HEADER = re.compile(r"^\[\[\s*(?P<t>[A-Za-z_][\w.-]*)\s*\]\]\s*(?:#.*)?$")


class FixError(ValueError):
    """A fix that can't be made safely: the file isn't laid out as expected, or the result would differ from the
    original in more than the item or setting fixed."""


def _blocks(lines: list[str], table: str) -> list[tuple[int, int]]:
    """(first line, line after the last) of each [[table]] block, in order. A block runs to the next table header
    written at the start of a line."""
    heads = [i for i, ln in enumerate(lines) if _HEADER.match(ln)]
    out = []
    for k, i in enumerate(heads):
        m = _ARRAY_HEADER.match(lines[i])
        if m and m["t"] == table:
            out.append((i, heads[k + 1] if k + 1 < len(heads) else len(lines)))
    return out


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(round(v, 3))
    raise FixError(f"can't write {v!r}")


def edit(text: str, fix: str, table: str, n: int, key: str | None = None, value=None) -> str:
    """`text` (a map file) with item `n` (from 1) of [[table]] taken out (remove_item), its setting `key` taken out
    (remove_key) or `key = value` written into it (fill). FixError when it can't be done safely: the result is read
    back, and only that item may have changed, in only that way."""
    try:
        before = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        before = None
    lines = text.splitlines(keepends=True)
    blocks = _blocks([ln.rstrip("\r\n") for ln in lines], table)
    if not 1 <= n <= len(blocks):
        raise FixError(f"there's no {table} {n} to fix")
    start, end = blocks[n - 1]
    if isinstance(value, float):
        value = round(value, 3)  # as written (_toml_value), so the read-back check compares like with like
    if fix == "remove_item":
        new_lines = lines[:start] + lines[end:]
    elif fix in ("remove_key", "fill"):
        if not key or not re.fullmatch(r"[A-Za-z_][\w-]*", key):
            raise FixError(f"{key!r} isn't a setting's name")
        own = re.compile(rf"^\s*{re.escape(key)}\s*=")
        at = [i for i in range(start + 1, end) if own.match(lines[i])]
        if fix == "remove_key":
            if len(at) != 1:
                raise FixError(f"{table} {n} has its {key} on {len(at)} lines")
            line = lines[at[0]]
            if line.count("[") != line.count("]") or line.count("{") != line.count("}"):
                raise FixError(f"{table} {n}'s {key} runs over several lines")
            new_lines = lines[:at[0]] + lines[at[0] + 1:]
        else:
            if at:
                raise FixError(f"{table} {n} has its {key} already")
            last = end
            while last > start + 1 and not lines[last - 1].strip():
                last -= 1
            newline = "\r\n" if lines[start].endswith("\r\n") else "\n"
            new_lines = lines[:last] + [f"{key} = {_toml_value(value)}{newline}"] + lines[last:]
    else:
        raise FixError(f"{fix!r} isn't a fix")
    new = "".join(new_lines)
    try:
        after = tomllib.loads(new)
    except tomllib.TOMLDecodeError as exc:
        raise FixError(f"the file wouldn't read back ({exc})") from None
    if before is not None:  # only that item, in only that way
        want = {k: v for k, v in before.items()}
        items = list(before.get(table, []))
        if fix == "remove_item":
            items = items[:n - 1] + items[n:]
        elif fix == "remove_key":
            items[n - 1] = {k: v for k, v in items[n - 1].items() if k != key}
        else:
            items[n - 1] = dict(items[n - 1], **{key: value})
        if items:
            want[table] = items
        else:
            want.pop(table, None)
        if after != want:
            raise FixError("the file would change in more than that item")
    return new
