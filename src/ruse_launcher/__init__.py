"""RUSE Launcher, the players' app (PLAN.md L5, M3): finds the game, loads mods and starts the game. A separate app
from the Studio (decision 22); both are built on the platform's engine, `rusemod`, and neither needs the other.

  api.py   what the screens can ask for (find the game, list mod sets, Play), in plain JSON-friendly data
  app.py   opens the window (pywebview) and serves the screens from ui/ on this PC only
  ui/      the screens: index.html + app.js + style.css; fake-api.js lets them run in a normal browser

Run it with `py -3 -m ruse_launcher` (after `py -3 -m pip install pywebview`).
"""

__version__ = "0.1.0"
