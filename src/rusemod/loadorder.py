"""A mod set's load order as text to share: the block RUSE Mod Manager (LittleGroove) copies and reads, so load orders
go both ways between the two apps. A friend pastes it, and gets the same mods in the same order.

    === R.U.S.E. Load Order ===
    1. Passable Forests | v1.0.0
    2. [COMPAT] Old Mod
    === End Load Order ===

The header says the game's data layout ("R.U.S.E." for the Steam release, "R.U.S.E. COMPAT" for the original). Each
numbered line is a mod's name, then " | v" and its version if it has one; "[COMPAT] " marks a mod made for the original
layout. RUSE Mod Manager reads only the numbered lines, so the extra lines we add ("Set: ...", "Game build: ...") are
safe. Mods are matched by name (any case), then by version. Later mods win where two change the same thing, in both
apps.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_NUM = re.compile(r"^\d+\.\s+(.+)$")
COMPAT_TAG = "[COMPAT] "
MODES = {"public": "R.U.S.E.", "compat": "R.U.S.E. COMPAT"}


@dataclass
class Entry:
    name: str
    version: str = ""
    compat: bool = False


@dataclass
class Shared:
    entries: list = field(default_factory=list)   # Entry, in load order
    mode: str | None = None                       # "public", "compat", or None when there's no header
    set_name: str = ""
    build: str = ""


def share_text(mods: list[dict], mode: str = "public", set_name: str = "", build: str = "") -> str:
    """The text for mods [{"name", "version", "compat"}] in load order."""
    lines = [f"=== {MODES.get(mode, MODES['public'])} Load Order ==="]
    if set_name:
        lines.append(f"Set: {set_name}")
    if build:
        lines.append(f"Game build: {build}")
    for i, m in enumerate(mods, 1):
        name = " ".join(str(m.get("name", "")).split())
        tag = COMPAT_TAG if m.get("compat") else ""
        version = str(m.get("version") or "").strip()
        lines.append(f"{i}. {tag}{name}" + (f" | v{version}" if version else ""))
    lines.append("=== End Load Order ===")
    return "\n".join(lines) + "\n"


def parse(text: str) -> Shared:
    """The load order in a pasted text (the first block in it). No block: an empty Shared."""
    out = Shared()
    inside = False
    for line in (text or "").splitlines():
        s = line.strip()
        if "Load Order" in s and "R.U.S.E." in s and not inside:
            if "End Load Order" in s:
                continue
            inside = True
            out.mode = "compat" if "COMPAT" in s else "public"
            continue
        if not inside:
            continue
        if "End Load Order" in s:
            break
        if s.lower().startswith("set:"):
            out.set_name = s[4:].strip()
            continue
        if s.lower().startswith("game build:"):
            out.build = s[11:].strip()
            continue
        m = _NUM.match(s)
        if not m:
            continue
        body = m.group(1).strip()
        name, version = (body.rsplit(" | v", 1) if " | v" in body else (body, ""))
        name, version = name.strip(), version.strip()
        compat = name.startswith(COMPAT_TAG)
        out.entries.append(Entry(name[len(COMPAT_TAG):] if compat else name, version, compat))
    return out


@dataclass
class Match:
    found: list = field(default_factory=list)      # (Entry, the library mod) in load order
    missing: list = field(default_factory=list)    # Entry
    other_version: list = field(default_factory=list)  # (Entry, the library mod): found, but not that version
    repeated: list = field(default_factory=list)   # Entry listed again (only the first counts)


def match(shared: Shared, library: list[dict]) -> Match:
    """Find each shared mod in `library` (dicts with "id", "name", "version"): by name, any case and spacing, the same
    version first. A mod listed twice counts once."""
    def key(s: str) -> str:
        return " ".join(str(s).split()).lower()
    by_name: dict[str, list] = {}
    for mod in library:
        by_name.setdefault(key(mod.get("name", "")), []).append(mod)
        if key(mod.get("id", "")) != key(mod.get("name", "")):
            by_name.setdefault(key(mod.get("id", "")), []).append(mod)
    out = Match()
    used = set()
    for e in shared.entries:
        candidates = by_name.get(key(e.name), [])
        if not candidates:
            out.missing.append(e)
            continue
        same = [m for m in candidates if not e.version or str(m.get("version", "")) == e.version]
        mod = (same or candidates)[0]
        if mod["id"] in used:
            out.repeated.append(e)
            continue
        used.add(mod["id"])
        out.found.append((e, mod))
        if not same:
            out.other_version.append((e, mod))
    return out
