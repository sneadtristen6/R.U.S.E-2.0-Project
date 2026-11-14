"""Every test run's Studio home is a scratch folder of its own, never the real one.

The owner, 2026-11-13 ("Yes, make it", to: the tests' shared setup points the Studio home at its own scratch folder,
so no test can write into the real Studio home again). That night the tests' Export builds wrote four cache files into
the real home on his PC: Export's build keeps its cache in rusemod.home.default_home(), whatever home a test gives the
Studio, and default_home() is the folder RUSE_PLATFORM_HOME names (his real one on that PC; else the app's own folder
in LOCALAPPDATA, a player's or a developer's real one).

So every test file imports this module FIRST (tests/test_home_guard.py checks each one): it points RUSE_PLATFORM_HOME
at a fresh folder for this run (under RUSE_TEST_TMP when that is set), which every process the tests start inherits
too. Whatever a test reaches through the default home (the build cache, a Studio or Launcher made without a home, the
start logs, the game index's place) lands there, and the folder goes when the run ends.

The game index the real home holds (the Studio builds it once, from the game) is still READ from there, read only, by
the two tests that check the real game's missions against it: game_index().
"""
import atexit
import os
import shutil
import tempfile
from pathlib import Path


def _real_home() -> Path:
    """The home default_home() gives without this module (rusemod.home.default_home's own rule)."""
    if os.environ.get("RUSE_PLATFORM_HOME"):
        return Path(os.environ["RUSE_PLATFORM_HOME"])
    if os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "RUSE Mod Platform"
    return Path.home() / ".local" / "share" / "ruse-mod-platform"


REAL = _real_home()
HOME = Path(tempfile.mkdtemp(prefix="ruse-test-home-", dir=os.environ.get("RUSE_TEST_TMP") or None))
os.environ["RUSE_PLATFORM_HOME"] = str(HOME)
atexit.register(shutil.rmtree, HOME, True)


def game_index(game) -> Path:
    """The game index of `game` as the real home holds it, for READING only (rusemod.index.Index opens it read
    only): the path rusemod.index.default_path gives in the real home."""
    from rusemod.index import build_key
    return REAL / "index" / f"{build_key(Path(game))}.sqlite"
