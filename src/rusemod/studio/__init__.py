"""The Studio: the modders' tool (PLAN.md L5, M4), in the same web-style window as the launcher (ADR 2).

v0.1: browse every unit and building by kind, nation and name; see a unit's values grouped (cost, combat,
movement…), its parts (its own and shared ones) and what uses it. Everything comes from the game index
(`ruse index build`). The language selector keeps the game's own names by default and can show the tool, the
property names and the units' in-game names in any of the game's ten languages.

  py -3 -m rusemod.studio [--game DIR] [--index FILE]
"""
