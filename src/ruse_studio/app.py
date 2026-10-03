"""Open the Studio window (needs pywebview: `py -3 -m pip install pywebview`). The installed app runs this too
(installers/studio.py)."""
from __future__ import annotations

import argparse
from pathlib import Path

from rusemod import schema
from rusemod.webui import open_window, self_test

from . import __version__
from .api import StudioApi, words

UI = Path(__file__).with_name("ui")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ruse_studio", description="RUSE Studio: make mods for R.U.S.E.")
    ap.add_argument("--game", help="the R.U.S.E. folder (default: found through Steam)")
    ap.add_argument("--index", help="the game index file (default: the one for this game build)")
    ap.add_argument("--spike", action="store_true", help="open the 3D check instead of the Studio")
    ap.add_argument("--self-test", metavar="REPORT", help="check this copy of the app is complete and write REPORT, "
                                                           "without opening a window (the build uses it)")
    ap.add_argument("--version", action="version", version=f"RUSE Studio {__version__}")
    args = ap.parse_args(argv)
    api = StudioApi(index_path=args.index, game_dir=args.game)
    if args.self_test:
        return self_test(args.self_test, UI, ["index.html", "app.js", "maps.js", "style.css", "spike3d.html"], [
            ("the Studio answers", lambda: api.status()),
            ("the Studio's words", lambda: f"{len(words('fr'))} in French, e.g. {words('fr')['search']!r}"),
            ("the game's names", lambda: f"ProductionPrice in Chinese is {schema.label('ProductionPrice', 'sc')!r}"),
        ])
    from rusemod.update import fix_app_list_version, installed_app
    if installed_app():  # Windows' app list shows this version (issue #15)
        fix_app_list_version("studio", __version__)
    page = "spike3d.html" if args.spike else "index.html"
    return open_window("RUSE Studio", UI, page, api, extra={"cache": api.cache_dir})
