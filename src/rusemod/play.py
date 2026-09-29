"""Starting R.U.S.E. (PLAN.md L4), for both apps: the launcher's Play and the Studio's Test in game. Vanilla starts
through Steam; modded play builds the mods into a modded copy of the game (rusemod.instance) and starts the game from
there, after Steam. The Steam install is never touched.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from .build import BuildError, build_and_write, load_mod

STEAM_PLAY = "steam://rungameid/21970"
STEAM_OPEN = "steam://open/main"


def open_url(url: str) -> None:
    if sys.platform == "win32":
        os.startfile(url)  # steam:// links and folders open with their Windows handler
    else:
        webbrowser.open(url)


def start_game(exe: Path) -> None:
    subprocess.Popen([str(exe)], cwd=str(exe.parent))


def steam_running() -> bool:
    if sys.platform != "win32":
        return True
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq steam.exe", "/NH"], capture_output=True, text=True)
    return "steam.exe" in out.stdout.lower()


def instances_dir(game: Path) -> Path:
    """Where modded copies go: RUSE-Instances on the game's drive (sharing files with the game only works on one
    drive)."""
    return Path(game.anchor) / "RUSE-Instances"


class Starter:
    """Starts the game. The arguments replace the real world in tests: opening links, starting the game, checking for
    Steam, and waiting for it."""

    def __init__(self, open_url=open_url, start_game=start_game, steam_running=steam_running, wait=time.sleep):
        self.open_url, self.start_game, self.steam_running, self.wait = open_url, start_game, steam_running, wait

    def vanilla(self, say) -> None:
        say("Starting R.U.S.E. through Steam…")
        self.open_url(STEAM_PLAY)

    def modded(self, game: Path, mod_folders, instance: Path, name: str, say) -> None:
        """Build these mod folders into the modded copy `instance` and start the game from it. A problem raises
        BuildError (or RndfError, OSError) with a message for the player, and nothing starts."""
        mods = [load_mod(Path(m)) for m in mod_folders]
        say(f"Building the modded copy of R.U.S.E. for {name} in {instance}…")
        result = build_and_write(game, mods, instance=instance, say=say)
        if result.errors:
            raise BuildError("These mods have errors (listed above). Nothing was changed.")
        exe = next((p for p in instance.iterdir() if p.name.lower() == "ruse.exe"), None) if instance.is_dir() else None
        if exe is None:
            raise BuildError(f"The modded copy at {instance} has no RUSE.exe.")
        if not self._steam(say):
            raise BuildError("Steam didn't start. Start Steam, then try again.")
        say("Starting R.U.S.E. from the modded copy…")
        self.start_game(exe)

    def _steam(self, say) -> bool:
        if self.steam_running():
            return True
        say("Starting Steam…")
        self.open_url(STEAM_OPEN)
        for _ in range(60):
            self.wait(1)
            if self.steam_running():
                return True
        return False
