"""The files the apps' builds read from the app itself (FL-57): data files inside the installed app, next to its code.

How this list was found (2026-11-26, from the code): every place the build and the steps Play and Test in game run
open a file from the app's own folders: `Path(__file__).with_name(...)` (fairplay.SCRIPTS gamescripts/*.bin, guard.KEYS,
motionlib.LIST, groundtex.PALETTE_FILE, buildtext, schema labels.toml, owned texts, flaginfo/numberinfo by language),
`importlib.resources` (signature: pictures/startup_scene.png, sounds/bf109start.ogg), presets (pictures/blank_*.png)
and ruse_mod_engine's `data_dir()` (data/*.json, migrations, version_maps); and the installer's own list of the files it
ships (installers/build_app.data_files). tests/test_appfiles.py keeps APP_FILES and NOT_READ together equal to that
installer list, and checks the file names the code writes in its source are all in APP_FILES, so a data file added
later without a line here fails a test.

Paths are relative to the app's folder (the one holding rusemod and ruse_mod_engine), as in the built app."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # the app's folder: beside rusemod/ and ruse_mod_engine/ (src/ from source)


def _in(folder: str, *names: str) -> tuple[str, ...]:
    return tuple(f"{folder}/{n}" for n in names)


_LANGS = ("", "_cz", "_fa", "_fr", "_ger", "_ita", "_jpn", "_pol", "_ru", "_sc", "_spa")
_VERSIONS = {"v23660935": ("v23661872", "v23738184", "v23762668", "v24003166", "v24087620", "v24670294", "v24687178"),
             "v23661872": ("v23738184", "v23762668", "v24003166", "v24087620", "v24670294", "v24687178"),
             "v23738184": ("v23762668", "v24003166", "v24087620", "v24670294", "v24687178"),
             "v23762668": ("v24003166", "v24087620", "v24670294", "v24687178"),
             "v24003166": ("v24087620", "v24670294", "v24687178"),
             "v24087620": ("v24670294", "v24687178"),
             "v24670294": ("v24687178",)}

APP_FILES: tuple[str, ...] = (
    _in("rusemod", "buildtext.toml", "checkkeys.toml", "codes.toml", "ground_presets.toml", "guard_cheat_tools.toml",
        "guard_keys.toml", "labels.toml", "motions.json.gz", "ownedsignintext.toml", "ownedtext.toml",
        "release_keys.toml", "sharedui/agreement.js")
    + _in("rusemod", *(f"flaginfo{s}.toml" for s in _LANGS), *(f"numberinfo{s}.toml" for s in _LANGS))
    + _in("rusemod/gamescripts", "fairplay_lock.bin", "fairplay_watch.bin", "guard_hash.bin")
    + _in("rusemod/pictures", "blank_ocean.png", "blank_terrain.png", "startup_scene.png")
    + _in("rusemod/sounds", "bf109start.ogg")
    + _in("ruse_mod_engine/data", "class_catalog.json", "dsl_catalog.json", "dsl_catalog_overlay.json",
          "game_versions.json", "placement_classes.json", "placement_icon_roles.json")
    + _in("ruse_mod_engine/data/migrations", "v23660935_to_v23738184.json", "v23661872_to_v23660935.json",
          "v23738184_to_v24003166.json", "v3591_to_v23661872.json")
    + _in("ruse_mod_engine/data/version_maps", *(f"{a}_{b}.json.gz" for a, bs in _VERSIONS.items() for b in bs))
)

# Shipped in the app but not read by a build: the game scripts' source (only tools and tests compare it with the .bin).
NOT_READ: tuple[str, ...] = _in("rusemod/gamescripts", "fairplay_lock.py25", "fairplay_watch.py25", "guard_hash.py25")


def missing(root: Path | None = None) -> list[str]:
    """The APP_FILES that aren't there or can't be read in the app folder `root` (default: this app), as listed."""
    base = Path(root) if root is not None else ROOT
    gone = []
    for rel in APP_FILES:
        try:
            with open(base / rel, "rb") as f:
                f.read(1)
        except OSError:
            gone.append(rel)
    return gone
