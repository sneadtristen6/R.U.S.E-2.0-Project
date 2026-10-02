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
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq steam.exe", "/NH"], capture_output=True, text=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)  # no console flashing up from the apps
    return "steam.exe" in out.stdout.lower()


def instances_dir(game: Path) -> Path:
    """Where modded copies go: RUSE-Instances on the game's drive (sharing files with the game only works on one
    drive)."""
    return Path(game.anchor) / "RUSE-Instances"


SHARED = "Modded game"  # the one modded copy on the PC: both apps build every Play and Test in game into it (the owner,
# 2026-10-02: "only one stored ... version of game on whole pc needed"); one game runs at a time anyway
BUILDING = ".building"  # held while either app builds the copy (rusemod.backup._claim): the other one waits its turn


def shared_copy(game: Path, instances: Path | None = None) -> Path:
    """The modded copy both apps use: `RUSE-Instances\\Modded game` on the game's drive (or in `instances`)."""
    return (Path(instances) if instances else instances_dir(game)) / SHARED


def keep_order(mods) -> None:
    """Make the given order of `mods` [(ModInfo, ops)] count for the load order: each mod loads after the one before
    it, unless either of the two already says how they relate (a dependency, `after` or `before`)."""
    for (prev, _ops), (info, _o) in zip(mods, mods[1:]):
        related = prev.id in info.after or prev.id in info.before or prev.id in info.depends or \
            info.id in prev.after or info.id in prev.before or info.id in prev.depends
        if not related and prev.id != info.id:
            info.after.append(prev.id)


class Starter:
    """Starts the game. The arguments replace the real world in tests: opening links, starting the game, checking for
    Steam, and waiting for it."""

    def __init__(self, open_url=open_url, start_game=start_game, steam_running=steam_running, wait=time.sleep):
        self.open_url, self.start_game, self.steam_running, self.wait = open_url, start_game, steam_running, wait

    def vanilla(self, say) -> None:
        say("Starting R.U.S.E. through Steam…")
        self.open_url(STEAM_PLAY)

    def modded(self, game: Path, mod_folders, instance: Path, name: str, say) -> None:
        """Build these mod folders into the modded copy `instance` and start the game from it. The folders' order
        counts: a later mod comes after an earlier one, so it wins when both change the same value, unless the mods
        themselves say otherwise (MOD_FORMAT §10.6). A problem raises BuildError (or RndfError, OSError) with a
        message for the player, and nothing starts; so do .rmod mods that can't go together (the build refuses them
        before building anything, naming every clash: rusemod.rmod.clashes)."""
        from .backup import _claim, _release
        from .instance import refuse_if_running
        refuse_if_running(str(instance))  # before anything is built: a game still running from the copy is said at once
        mods = [load_mod(Path(m)) for m in mod_folders]
        keep_order(mods)
        lock = instance.parent / BUILDING
        lock.parent.mkdir(parents=True, exist_ok=True)
        fd = _claim(lock)
        if fd is None:
            raise BuildError("The other app (the Launcher or the Studio) is building the modded game right now: wait "
                             "for it to finish, then try again.")
        try:
            say(f"Building the modded copy of R.U.S.E. for {name} in {instance}…")
            result = build_and_write(game, mods, instance=instance, say=say)
        finally:
            _release(lock, fd)
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
