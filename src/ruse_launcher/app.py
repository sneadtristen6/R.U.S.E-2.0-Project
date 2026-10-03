"""Open the launcher window. The screens (ui/) are served to the window from this PC only (127.0.0.1), and talk to
LauncherApi through pywebview's bridge. Needs pywebview: `py -3 -m pip install pywebview` (Windows 10/11 already have
the web engine it uses, WebView2). The installed app runs this too (installers/launcher.py).

  py -3 -m ruse_launcher [--game DIR]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rusemod.webui import on_file_drop, open_window, pick_file, pick_folder, self_test

from . import __version__
from .api import MOD_FILES, LauncherApi, LauncherError, words

UI = Path(__file__).with_name("ui")


def dropped(api: LauncherApi, window, paths) -> None:
    """Files dropped on the window: add each as a mod, then tell the page what happened (the page never sees a
    dropped file's path itself; pywebview hands it to us)."""
    for path in paths:
        try:
            event = {"ok": True, **api.add_mod(path)}
        except LauncherError as exc:
            event = {"ok": False, "message": str(exc)}
        window.evaluate_js(f"window.dispatchEvent(new CustomEvent('mod-dropped', {{detail: {json.dumps(event)}}}))")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ruse_launcher", description="RUSE Launcher: play R.U.S.E. with mods.")
    ap.add_argument("--game", help="the R.U.S.E. folder (default: found through Steam)")
    ap.add_argument("--self-test", metavar="REPORT", help="check this copy of the app is complete and write REPORT, "
                                                           "without opening a window (the build uses it)")
    ap.add_argument("--version", action="version", version=f"RUSE Launcher {__version__}")
    args = ap.parse_args(argv)
    api = LauncherApi(game_dir=args.game)
    if args.self_test:
        return self_test(args.self_test, UI, ["index.html", "app.js", "style.css"], [
            ("the launcher answers", lambda: f"{len(api.mod_sets())} mod set(s), {len(api.library())} mod(s) in the "
                                             f"library; {api.status()['message']}"),
            ("the launcher's words", lambda: f"{len(words('fr'))} in French, e.g. {words('fr')['play']!r}"),
        ])
    from rusemod.update import fix_app_list_version, installed_app
    if installed_app():  # Windows' app list shows this version (issue #15: it said 0.1.0 when 0.3.1 was installed)
        fix_app_list_version("launcher", __version__)
    api._pick_folder = lambda: pick_folder(api._window)
    api._pick_file = lambda: pick_file(api._window, MOD_FILES)
    return open_window("RUSE Launcher", UI, "index.html", api, width=1120, height=740,
                       setup=lambda window: on_file_drop(window, lambda paths: dropped(api, window, paths)))
