"""The game's own lettering on the Studio's and the Launcher's pages (the owner, 2026-10-22: "I want the studio font to
be ruse font. But just like the normal white that it already is").

The game draws its menus in Ubisoft's UbiGame Text: its menus' $TitleFont is the bold, $MainFont the regular (the
game's own setup of its menus' fonts); in Japanese it draws with RUSE_new, in Chinese with Source Han Sans (its font
table, genglad/nonpatchable/system3d/fonts.cpp, lists those four files). They are the game's files (UbiGame Text and
RUSE_new Ubisoft's, all rights reserved; Source Han Sans Adobe's), so the apps never carry them: at each start they
are copied from the player's own game into the app's cache, and the pages' style sheets name them first. A page
without the copies (no game found, an older game) keeps its usual font.
"""
from __future__ import annotations

from pathlib import Path

PACK = "Data_Common.dat"
FOLDER = "gamefont"  # in the app's cache, served to its pages as cache/gamefont/<name>
FONTS = {  # the copy's name -> the file in the game's pack
    "ruse-regular.ttf": "ww2\\res2d\\fonts\\ubigame text l reg v11.ttf",
    "ruse-bold.ttf": "ww2\\res2d\\fonts\\ubigame text l bold v07.ttf",
    "ruse-japanese.ttf": "ww2\\res2d\\fonts\\ruse_new_l reg v20_jpn.ttf",
    "ruse-chinese.ttc": "ww2\\res2d\\fonts\\sourcehansans-regular.ttc",
}


def copy_fonts(game: Path | None, cache: Path) -> list[str]:
    """Copy the game's fonts into `cache`/gamefont, each one the game has (a copy already there of the same size is
    kept). Returns the copies there now; none when the game or its pack isn't found."""
    from .build import find_pack
    from .edat import Edat
    pack = find_pack(Path(game), PACK) if game else None
    if pack is None:
        return []
    out = Path(cache) / FOLDER
    there = []
    with Edat.open(str(pack)) as arc:
        for name, member in FONTS.items():
            e = arc.entry(member)
            if e is None:
                continue
            target = out / name
            if not (target.is_file() and target.stat().st_size == e.size):
                out.mkdir(parents=True, exist_ok=True)
                part = target.with_suffix(target.suffix + ".part")
                part.write_bytes(bytes(arc.read(e)))
                part.replace(target)
            there.append(name)
    return there
