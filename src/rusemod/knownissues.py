"""Library mods known to stop some of the game's missions on their own (the owner, 2026-11-13, asked "Six library mods
break missions on their own (Pinnacle Map Pack, Balanced Realism, 1 VS 7 AI, 1 VS 15 AI, Monte Cassino Demo MP,
RSCBM2): a build warning, a note in the mod list, or both?", answered "build warning and a note so both").

FOR: the build's warning when a set holds one of them (rusemod.build.known_issue_findings); the mod list's note on the
same six is the list's own data (its index.toml `known_issues`, shown on the Launcher's Supported mods:
rusemod.mod_index.KNOWN_ISSUES). USED BY: rusemod.build.build_and_write.

What they do (Bug Watch, 2026-11-10, round 2 on FL-101; checked again 2026-11-13 with this code's own readers): each
replaces the layout of some of the game's missions' maps whole (campaign chapters, or the tutorial) with a battle
layout that holds no named place, while the mission's script looks for named places in it; the mission stops about a
second after it starts (a player's crash report of that week: a mission's place check failing, the Pinnacle Map Pack
on). Found for each mod ALONE across the whole library; a set's combinations and players' own mods are not covered: a
mod not in KNOWN is never warned about, which says nothing about it.

Each is known by its .rmod file's exact bytes (SHA-256, the file inside the list's package and in the library alike),
so a new version of one of them is not warned about until it is checked: the warning rests on the file that was
checked, not on the mod's name."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MissionsStop:
    name: str        # the mod's name, as the mod list shows it
    listed: str      # its id and version in the mod list, for whoever reads this table
    stops: str       # "campaign" (some of the campaign's chapters) or "tutorial"
    count: int       # how many of those missions (the campaign chapters a player can pick in the menu)


# the .rmod file's SHA-256 -> what it stops; its size first, so most files are never hashed
KNOWN: dict[str, MissionsStop] = {
    "928f15702ec77600f4634ee255dcb44c62dde352d4e6f83f6a379defc3cc2aae":
        MissionsStop("Pinnacle Map Pack", "ruse-pinnacle-map-pack-v1@1.0.0", "campaign", 11),
    "99768d798eac0aef1eae7d048f18a1111261391352efaba6299c66e0742e40e6":
        MissionsStop("Balanced Realism Mod", "balanced-realism-mod-v1@1.0.0", "campaign", 9),
    "f9b63e9b24ab5f1592cd04d27dd86a84987cf78bdd68ce536c6b35489fc52e4a":
        MissionsStop("1 VS 7 AI", "1-vs-7-ai-v1@1.0.0", "campaign", 1),
    "dae4d007f3f67062706de3431da988c86d8819dbae0bca1dbdfa1b49738c4b09":
        MissionsStop("1 VS 15 AI", "1-vs-15-ai-v1@1.0.0", "campaign", 1),
    "fbe183b91477cb6a4bde526d827deff0cc97d1abf410269a6035732190963568":
        MissionsStop("Monte Cassino Demo MP", "montecassinomp@1.0.0", "tutorial", 1),
    "d2841624ca80181190b4737422b3fe40220db48f6eddd7071da8bd37f81805c9":
        MissionsStop("RSCBM2", "rscbm2-v1@1.0.1", "tutorial", 1),
}
SIZES = {890824, 2899628, 127342, 127347, 79448, 182137}   # the six files' sizes in bytes, in KNOWN's order


def missions_stop(rmod_file) -> MissionsStop | None:
    """What this .rmod file is known to stop, or None (a file that can't be read is not known either)."""
    try:
        path = Path(rmod_file)
        if path.stat().st_size not in SIZES:
            return None
        return KNOWN.get(hashlib.sha256(path.read_bytes()).hexdigest())
    except (OSError, TypeError, ValueError):
        return None
