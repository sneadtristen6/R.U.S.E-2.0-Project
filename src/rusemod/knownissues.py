"""Two library mods the build warns about by their .rmod file's bytes, 1 VS 7 AI and 1 VS 15 AI (the owner, 2026-11-14:
"Just keep a warning about 1v7 and 1v15."), until the campaign chapter they change, 16. WACHT AM RHEIN, is tried in the
game with them on; then this list goes, with build.known_issue_findings, its call in build.build_and_write and their
tests.

FOR: the build's warning when a set holds one of them (rusemod.build.known_issue_findings); the mod list's note on them
is the list's own data (its index.toml `known_issues`, shown on the Launcher's Supported mods:
rusemod.mod_index.KNOWN_ISSUES). USED BY: rusemod.build.build_and_write.

Why only these two: the build reads every mission a player can pick in the player's own game, as the set leaves it
(rusemod.missionplaces), and warns about any mod, any version, that leaves one without a zone it watches from its
start. That finds the other four of the six library mods this list held before (the Pinnacle Map Pack, the Balanced
Realism Mod, Monte Cassino Demo MP, RSCBM2), but not these two: each replaces that chapter's layout with one lacking
every zone the chapter's own scripts watch from its start, and points the chapter at the match script of an Operation
(The Maginot Line's), which it replaces with one that watches no zone, so nothing is left to miss (read with this
code's readers on 2026-11-14, each mod applied alone, in memory, to the game as sold). Whether the chapter then plays
or stops was never tried in the game. The missions check says nothing more of these mods' campaign chapters (one
warning a mod: build.mission_place_findings' `besides`).

Each is known by its .rmod file's exact bytes (SHA-256, the file inside the mod list's package and in the library
alike), so a new version of one of them is not warned about here: the missions check reads it as it reads any mod."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MissionsStop:
    name: str        # the mod's name, as the mod list shows it (and as the .rmod file names itself)
    listed: str      # its id and version in the mod list, for whoever reads this table
    count: int       # how many campaign chapters (those a player can pick in the menu) it is said to stop


# the .rmod file's SHA-256 -> what it is said to stop; its size first, so most files are never hashed
KNOWN: dict[str, MissionsStop] = {
    "f9b63e9b24ab5f1592cd04d27dd86a84987cf78bdd68ce536c6b35489fc52e4a":
        MissionsStop("1 VS 7 AI", "1-vs-7-ai-v1@1.0.0", 1),
    "dae4d007f3f67062706de3431da988c86d8819dbae0bca1dbdfa1b49738c4b09":
        MissionsStop("1 VS 15 AI", "1-vs-15-ai-v1@1.0.0", 1),
}
SIZES = {127342, 127347}   # the two files' sizes in bytes, in KNOWN's order


def missions_stop(rmod_file) -> MissionsStop | None:
    """What this .rmod file is known to stop, or None (a file that can't be read is not known either)."""
    try:
        path = Path(rmod_file)
        if path.stat().st_size not in SIZES:
            return None
        return KNOWN.get(hashlib.sha256(path.read_bytes()).hexdigest())
    except (OSError, TypeError, ValueError):
        return None
