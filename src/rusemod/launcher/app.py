"""Open the launcher window. The screens (ui/) are served to the window from this PC only (127.0.0.1), and talk to
LauncherApi through pywebview's bridge. Needs pywebview: `py -3 -m pip install pywebview` (Windows 10/11 already have
the web engine it uses, WebView2).

  py -3 -m rusemod.launcher [--game DIR] [--spike]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from ..webui import serve
from .api import LauncherApi

UI = Path(__file__).with_name("ui")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rusemod.launcher", description="The R.U.S.E. mod launcher.")
    ap.add_argument("--game", help="the R.U.S.E. folder (default: found through Steam)")
    ap.add_argument("--spike", action="store_true", help="open the 3D check instead of the launcher")
    args = ap.parse_args(argv)
    try:
        import webview
    except ImportError:
        print("The launcher window needs pywebview. Install it once with:  py -3 -m pip install pywebview")
        return 2
    server, base = serve(UI)
    api = LauncherApi(game_dir=args.game)
    page = "spike3d.html" if args.spike else "index.html"
    window = webview.create_window("RUSE Mod Platform", f"{base}/{page}", js_api=api, width=1120, height=740,
                                   min_size=(900, 600), background_color="#15181b")

    def pick_folder():
        chosen = window.create_file_dialog(webview.FOLDER_DIALOG)
        return chosen[0] if chosen else None

    api._pick_folder = pick_folder
    try:
        webview.start()
    finally:
        server.shutdown()
        server.server_close()
    return 0
