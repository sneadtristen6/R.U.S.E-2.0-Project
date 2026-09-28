"""Open the Studio window (needs pywebview: `py -3 -m pip install pywebview`)."""
from __future__ import annotations

import argparse
from pathlib import Path

from ..webui import open_window
from .api import StudioApi

UI = Path(__file__).with_name("ui")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rusemod.studio", description="The R.U.S.E. modding Studio.")
    ap.add_argument("--game", help="the R.U.S.E. folder (default: found through Steam)")
    ap.add_argument("--index", help="the game index file (default: the one for this game build)")
    args = ap.parse_args(argv)
    return open_window("RUSE Mod Platform · Studio", UI, "index.html", StudioApi(index_path=args.index, game_dir=args.game))
