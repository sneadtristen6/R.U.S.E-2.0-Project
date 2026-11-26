"""Settings' "Terms, credits and licences" section, shared by the Launcher and the Studio (both include TermsCalls in
their API): the version of the agreement the player accepted, and the credits (THIRD_PARTY_NOTICES.md) and the licence
(LICENSE) the app ships. The agreement's own words come from the app's words.toml (agree_full), the same text the
first-start screen shows (shared/agreement.js). The owner, 2026-11-25: "Yes, for 19, add a second setting for that."

The two files sit beside the installed program (installers/build_app.py licence_files) and at the top of the
repository when the apps run from source. Nothing here touches the network or the player's settings.
"""
from __future__ import annotations

import sys
from pathlib import Path

from rusemod import guard
from rusemod.home import settings

FILES = {"notices": "THIRD_PARTY_NOTICES.md", "licence": "LICENSE"}
LIMIT = 2_000_000   # characters one file may show (the credits file is about 240 000)


def roots() -> list[Path]:
    """Where the files may be: beside the running program (an installed app), then the repository's top folder."""
    found = []
    for start in (sys.argv[0] if sys.argv else "", sys.executable):
        if start:
            found.append(Path(start).resolve().parent)
    found.append(Path(__file__).resolve().parents[2])
    return found


def read_shipped(name: str, where: list[Path] | None = None) -> str | None:
    """The file's text, or None when it isn't there or can't be read (said as such, never replaced by other text)."""
    for root in where if where is not None else roots():
        try:
            return (root / name).read_text(encoding="utf-8", errors="replace")[:LIMIT]
        except OSError:
            continue
    return None


class TermsCalls:
    def terms_info(self) -> dict:
        """What the section shows: `accepted` (the agreement's version the player accepted, 0 for none), `current`
        (the version this app shows), and `notices` / `licence` (the shipped files' text; None when one is missing)."""
        return {"accepted": guard.settings_of(settings(self._home))["terms"], "current": guard.TERMS_VERSION,
                "notices": read_shipped(FILES["notices"]), "licence": read_shipped(FILES["licence"])}
