"""A build list's groups and the most a group holds (the owner, 2026-10-31, after bigpacks13: "We just need to limit how
many can be in a certain group. Because it's buggy."; a 7th unit in a full group: "Refuse it"; his picks the same
night: the groups are the game's lines, each unit going into the line of its kind; counted over every battle date
together; a mod already over it when it's built: built, with a warning).

A group is one row of a building's build list (rusemod.menulines): a line as the game makes it, a unit and its
upgrades, each upgrade one place (its research card, then its unit), the game's own units counted with the mods'.
Counted from the game's unit files (10-31, the 366 era units' mod): the game's own lines hold 1 to 3, at most 8 of them
in one building. MOST is his limit, not the game's: whether the game's menu limits a row or the rows is not known.

A unit's group is the first unit up its research chain while it's an upgrade (IsUpgrade, UpgradeRequire), as the
game's script climbs it; a new unit bought from the start stands in the group the Studio put it in (the mod's
menu_groups.toml: its address = the address of the group's first unit, its own for a group of its own), else in the
group of the unit it was copied from (mods made before the file, as rusemod.menulines has always placed them)."""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

MOST = 6                    # his limit (2026-10-31), units and research cards alike, every battle date together
# the most groups (rows) one building's build list holds: his pick (2026-11-01, "10 groups") after his frames at 1920 x
# 1080 showed 11 unit rows on the screen, 10 while the row under the mouse is drawn twice as big (findings F-168, F-169:
# the game places every row, none cut or scrolled)
MOST_GROUPS = 10
FILE = "menu_groups.toml"   # in a mod folder, beside mod.toml
TABLE = "groups"


class MenuGroupsError(ValueError):
    pass


def read(folder) -> dict[str, str]:
    """A mod folder's groups, {a new unit's address: its group's first unit's address}; {} when it has none."""
    path = Path(folder) / FILE
    if not path.is_file():
        return {}
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise MenuGroupsError(f"{path}: {exc}") from None
    table = data.get(TABLE, {})
    if not isinstance(table, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in table.items()):
        # not a game rule: what this file holds
        raise MenuGroupsError(f"{path}: [{TABLE}] holds a unit's address = the address of its group's first unit")
    return dict(table)


def write(folder, groups: dict[str, str]) -> None:
    """Save `groups` as the mod's menu_groups.toml, sorted; no file when there are none."""
    path = Path(folder) / FILE
    if not groups:
        path.unlink(missing_ok=True)
        return
    lines = ["# Each new unit bought from the start and the group of its building's build list it stands in: its address",
             "# = the address of the group's first unit (its own: a group of its own). Written by the RUSE Studio.",
             f"[{TABLE}]"]
    # a JSON string is a TOML basic string for every address the game has (letters, digits, $ / _ -)
    lines += [f"{json.dumps(k, ensure_ascii=False)} = {json.dumps(v, ensure_ascii=False)}"
              for k, v in sorted(groups.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def roots(units: dict, groups: dict | None = None) -> dict[str, str]:
    """{address: its group's first unit} for `units` {address: {"parent": the unit it's researched from or None,
    "flag": whether it's an upgrade (IsUpgrade), "source": a new unit's clone source, None for the game's}}, `groups` the
    mods' menu_groups. Up the research chain while an upgrade; else to the group the mods give it (its own: there);
    else a new unit the way of the unit it was copied from. A step to a unit not in `units`, or a loop, stops there."""
    groups = groups or {}
    out = {}
    for start in units:
        at, seen = start, {start}
        while True:
            u = units[at]
            if u.get("flag") and u.get("parent") is not None:
                nxt = u["parent"]
            elif at in groups:
                nxt = groups[at]
            else:
                nxt = u.get("source")
            if nxt is None or nxt in seen or nxt not in units:
                break
            seen.add(nxt)
            at = nxt
        out[start] = at
    return out


def members(units: dict, roots_of: dict) -> dict[tuple, list[str]]:
    """The groups as the build lists show them: {(nation, building, first unit): [addresses]} of the units in a building
    (`units`[address]["factory"] not None) shown at some battle date (["shown"], default True)."""
    out: dict[tuple, list[str]] = {}
    for a, u in units.items():
        if u.get("factory") is not None and u.get("shown", True):
            out.setdefault((u.get("nation"), u["factory"], roots_of[a]), []).append(a)
    return out


def over(groups: dict[tuple, list[str]]) -> list[tuple[tuple, int]]:
    """The groups holding more than MOST: [((nation, building, first unit), how many)], the fullest first."""
    return sorted(((k, len(v)) for k, v in groups.items() if len(v) > MOST), key=lambda kv: (-kv[1], str(kv[0])))


def crowded(groups: dict[tuple, list[str]]) -> list[tuple[tuple, int]]:
    """The buildings whose build list has more than MOST_GROUPS groups: [((nation, building), how many)], the
    fullest first."""
    count: dict[tuple, int] = {}
    for n, f, _first in groups:
        count[(n, f)] = count.get((n, f), 0) + 1
    return sorted(((k, c) for k, c in count.items() if c > MOST_GROUPS), key=lambda kv: (-kv[1], str(kv[0])))
