"""A squad's own soldiers: its own number of soldiers and each soldier a look of his own, for ONE squad, the one whose
data asks for it (the owner, 2026-11-12: "Program changes are completely fine. So I would only want to change it for
this one squad. Not every squad in the game."; his picks the same night: at least 2 soldiers, the game's own minimum;
at most 8 for now, the first try at 7; a bigger squad spreads out wider, as the game does; an added soldier adds a
figure only, the squad's health and weapons stay as set on its page; paratroopers wear each soldier's own look while
falling too). One set of rules for the build (rusemod.build.squad_soldiers) and the Studio (ruse_studio.squadblender).

Kept in a mod, in files/models beside the unit's own models:
- <unit>.squad.toml, `count = N`: the squad's own number of soldiers, FEWEST to MOST. Without it the squad has the
  game's one setting for every squad ($/GFX/Everything/UniteBehaviourDescriptor's NbSoldatInGroupeCombat: 5, or a
  mod's change of it).
- <unit>@<i>.glb and its record <unit>@<i>.json: soldier i's own look (i from 1 to N, soldier 1 first), as the
  Studio's Import model writes it for him: fitted to the model of the figure the game gives his place (the last
  soldier wears the squad's last man's figure, its bazooka man's; the others its riflemen's), read as any model file
  of the mod is; the build writes it as the model <unit>__<i> beside the one it was fitted to. A soldier's number is
  digits only, so it is never the name of a kind of soldier (<unit>@bazooka.glb, rusemod.build._unit_of).

What the build writes for such a squad, and for no other:
- R2Behaviour: the squad's own copy of that setting, as the mods leave it, with only NbSoldatInGroupeCombat its own;
  the squad's soldiers take it in place of the shared one (a bigger squad spreads out wider: the game's own rule);
- R2SoldierLooks: one entry per soldier, soldier 1 first: none (he wears what the game gives his place) or a copy of
  the figure the game gives his place drawing his own model;
- the own-squads game patch in the modded copy (rusemod.gamepatch), through which alone the game reads the two. A game
  without it leaves names it doesn't know aside, so such a mod loads there with the game's own squads (not tried).
Who fires what stays the game's rule: the weapons whose ammunition has NeedModelChange (a bazooka, a flamethrower, a
charge) go to the last soldier, a second one to the soldier before him; the squad's other weapons to the rest. So a
squad keeps at least as many soldiers as it has such weapons.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

FEWEST, MOST = 2, 8           # the owner's picks 1 and 2 (2026-11-12): the game's own minimum; 8 for now
SUFFIX = ".squad.toml"        # files/models/<unit>.squad.toml
MODELS = Path("files") / "models"
BEHAVIOUR = "$/GFX/Everything/UniteBehaviourDescriptor"   # the game's one setting, every squad's
COUNT = "NbSoldatInGroupeCombat"                          # its soldiers in a squad
NEED = "NeedModelChange"                                  # an ammunition fired by the squad's last soldiers
OWN_COUNT, OWN_LOOKS = "R2Behaviour", "R2SoldierLooks"    # the squad's own setting and its soldiers' looks
SQUAD_CLASS = "TInfanterieDescriptor"                      # the only class the game patch gives the two to
PATCH = "own-squads"                                       # rusemod.gamepatch.PATCHES
RIFLEMEN, LAST = "GfxDescriptorFusilier", "GfxDescriptorBazooka"   # the figures the game gives the places


class SquadError(Exception):
    """A squad's file that can't be read or says what can't be (its own mistake, said as it is)."""


def soldier_stem(unit: str, i: int) -> str:
    """The name of soldier `i`'s look file, without .glb: <unit>@<i>."""
    return f"{unit}@{int(i)}"


def soldier_of(stem: str) -> tuple[str, int] | None:
    """(unit, i) for a soldier's look file's name (<unit>@<i>, i a whole number from 1); None for any other."""
    unit, sep, rest = stem.partition("@")
    if not sep or not rest.isdigit() or rest.startswith("0"):
        return None
    return unit, int(rest)


def squad_file(folder, unit: str) -> Path:
    return Path(folder) / MODELS / f"{unit}{SUFFIX}"


def read_count(path) -> int:
    """The count a squad file gives; SquadError for one that can't be read or gives no whole number."""
    path = Path(path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise SquadError(f"{MODELS.as_posix()}/{path.name} can't be read ({exc})") from None
    count = data.get("count")
    if isinstance(count, bool) or not isinstance(count, int):
        raise SquadError(f"{MODELS.as_posix()}/{path.name}: count must be a whole number of soldiers (got {count!r})")
    return count


def mod_squads(folder) -> dict:
    """{a new squad's name: its own number of soldiers} from a mod's files/models/<the squad's name>.squad.toml (the
    numbers as the files give them: the build says which it can't take)."""
    root = Path(folder) / MODELS
    if not root.is_dir():
        return {}
    return {f.name[:-len(SUFFIX)]: read_count(f) for f in sorted(root.glob(f"*{SUFFIX}"))}


def write_count(folder, unit: str, count: int | None) -> None:
    """The squad's own number of soldiers into its file (None: the file goes, the squad has the game's setting)."""
    path = squad_file(folder, unit)
    if count is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_text("# Made by the RUSE Studio: this squad's own number of soldiers\n"
                    f"count = {int(count)}\n", encoding="utf-8")
    os.replace(part, path)


def place_figure(place: int, count: int, has_last: bool) -> str:
    """The figure the game gives soldier `place` (1 to `count`): the last man's (the squad's own second figure,
    `has_last`) to the last soldier, the riflemen's to the others."""
    return LAST if has_last and place == count else RIFLEMEN


def fewest(need: int) -> int:
    """The fewest soldiers a squad may have: FEWEST, or one for each weapon its last soldiers fire (`need`)."""
    return max(FEWEST, need)


def join_place(count: int, need: int, has_last: bool) -> int:
    """Where a new soldier goes in a squad of `count` (his number): before the soldiers at the end who fire the squad's
    `need` NeedModelChange weapons, or before its last man when he wears a figure of his own (`has_last`), so they keep
    their weapons and looks and the new one stands among the riflemen; at the end when neither."""
    tail = min(count, max(need, 1 if has_last else 0))
    return count + 1 - tail
