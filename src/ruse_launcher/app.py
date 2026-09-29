"""Open the launcher window. The screens (ui/) are served to the window from this PC only (127.0.0.1), and talk to
LauncherApi through pywebview's bridge. Needs pywebview: `py -3 -m pip install pywebview` (Windows 10/11 already have
the web engine it uses, WebView2). The installed app runs this too (installers/launcher.py).

  py -3 -m ruse_launcher [--game DIR]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from rusemod.webui import open_window, pick_folder, self_test

from . import __version__
from .api import LauncherApi

UI = Path(__file__).with_name("ui")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ruse_launcher", description="RUSE Launcher: play R.U.S.E. with mods.")
    ap.add_argument("--game", help="the R.U.S.E. folder (default: found through Steam)")
    ap.add_argument("--self-test", metavar="REPORT", help="check this copy of the app is complete and write REPORT, "
                                                           "without opening a window (the build uses it)")
    ap.add_argument("--version", action="version", version=f"RUSE Launcher {__version__}")
    args = ap.parse_args(argv)
    api = LauncherApi(game_dir=args.game)
    if args.self_test:
        return self_test(args.self_test, UI, ["index.html", "app.js", "style.css"],
                         [("the launcher answers", lambda: f"{len(api.mod_sets())} mod set(s); {api.status()['message']}")])
    api._pick_folder = lambda: pick_folder(api._window)
    return open_window("RUSE Launcher", UI, "index.html", api, width=1120, height=740)
