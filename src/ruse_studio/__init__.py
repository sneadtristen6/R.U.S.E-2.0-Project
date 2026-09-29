"""RUSE Studio, the modders' app (PLAN.md L5, M4): the unit editor now, and later the map, model and scenario tools.
A separate app from the launcher (decision 22); both are built on the platform's engine, `rusemod`, and neither needs
the other.

v0.2: browse every unit and building by kind, nation and name; see a unit's values grouped (cost, combat,
movement…), its parts and what uses it, and change its numbers right there, saved in a mod (edits.py). Test in game
builds the mod and starts R.U.S.E. Everything about the game comes from the game index (`ruse index build`). The
language selector keeps the game's own names by default and can show the Studio in any of the game's ten languages.

  api.py      what the screens can ask for
  edits.py    the Studio's changes, kept in the mod's src/studio.rndf
  app.py      opens the window; `--spike` opens the 3D check (can the window draw 3D well enough for map and model views?)
  words.toml  the Studio's own words in ten languages
  ui/         the screens; fake-api.js lets them run in a normal browser (index.html?fake)

  py -3 -m ruse_studio [--game DIR] [--index FILE] [--spike]
"""
