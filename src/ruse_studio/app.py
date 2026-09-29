"""Open the Studio window (needs pywebview: `py -3 -m pip install pywebview`)."""
from __future__ import annotations

import argparse
from pathlib import Path

from rusemod.webui import open_window

from .api import StudioApi

UI = Path(__file__).with_name("ui")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ruse_studio", description="RUSE Studio: make mods for R.U.S.E.")
    ap.add_argument("--game", help="the R.U.S.E. folder (default: found through Steam)")
    ap.add_argument("--index", help="the game index file (default: the one for this game build)")
    ap.add_argument("--spike", action="store_true", help="open the 3D check instead of the Studio")
    args = ap.parse_args(argv)
    page = "spike3d.html" if args.spike else "index.html"
    return open_window("RUSE Studio", UI, page, StudioApi(index_path=args.index, game_dir=args.game))
