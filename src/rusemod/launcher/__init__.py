"""The player launcher (PLAN.md L5, M3): a desktop window built like a web page (decided 2026-09-28, ADR 2).

  api.py   what the screens can ask for (find the game, list mod sets, Play), in plain JSON-friendly data
  app.py   opens the window (pywebview) and serves the screens from ui/ on this PC only
  ui/      the screens: index.html + app.js + style.css; fake-api.js lets them run in a normal browser; spike3d.html is
           the 3D check (can the window draw 3D well enough for the Studio's map and model views?)

Run it with `py -3 -m rusemod.launcher` (after `py -3 -m pip install pywebview`), or `--spike` for the 3D check.
"""
