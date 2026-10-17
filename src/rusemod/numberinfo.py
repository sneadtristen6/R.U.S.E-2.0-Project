"""The number guide: what every number of the game's units and buildings, and of the parts they own or link to, means
(numberinfo.toml): its group, its unit and how to show it in plain units (metres, km/h, seconds, degrees, $, %), how
sure we are, and what it does, looks-only ones included (the owner, 2026-10-15: "We need to know everything that has
a number behind it", "Include the looks only. But just describe what the look is", "Include all numbers").

A key is a property's name, or "Class.Property" where the same name means something else on that class; lookup()
tries the class's own first."""
from __future__ import annotations

import math
import tomllib
from functools import lru_cache
from pathlib import Path

TEXTS = ("what", "does")  # the words of a number: numberinfo_<lang>.toml has them in that language
# how each unit is shown in plain units: (game units to one plain unit, the plain unit's word in words.toml)
# (no plain form for an acceleration: the game adds a fifth of it to the speed every 0.2 s, so the Units tab shows the
# unit's speed divided by it, the seconds to full speed or to a stop)
PLAIN = {"m": (260.0, "unit_m"), "kmh": (130.0, "unit_kmh"), "kmh_air": (57.78, "unit_kmh"),
         "deg": (math.pi / 180, "unit_deg"), "degs": (math.pi / 180, "unit_degs"),
         "s": (1.0, "unit_s"), "money": (1.0, "unit_money"), "share": (0.01, "unit_pct"), "pct": (1.0, "unit_pct"),
         "min": (1.0, "unit_min")}
# units a modder changes as an amount (the base-stat slider makes them smaller or larger); the rest name a kind, a
# switch or an id, typed as they are
AMOUNTS = {"m", "kmh", "kmh_air", "accel", "s", "deg", "degs", "money", "pts", "count", "times", "share", "level",
           "raw", "pct", "min"}
# the game's five game modes, by number: a unit's ProductionPrice and ShowInMenu hold one value for each, in this order
# (the game picks the item at the battle's mode; its lobby's own table names them; the game's late-war tanks are shown
# at 0, 3 and 4 only). English here; the Studio shows the game's own names in each language.
MODES = ("1945", "1942", "1939", "Total War", "Nuclear")
GROUPS = ("health", "movement", "sight", "combat", "ammo", "production", "menu", "identity", "computer", "flight",
          "turret", "looks", "sound", "interface", "effects")
SURE = ("tried", "known", "community", "name")
# the game's units and buildings: "units" in an entry's `classes` (a name some other kind of object has too, meaning
# something else there: the main menu's Factory, a map shape's Radius, a cutscene's Key)
UNIT_CLASSES = ("TUniteAuSolDescriptor", "TBatimentDescriptor", "TAvionDescriptor", "TInfanterieDescriptor",
                "TTruckDescriptor", "TUniteDescriptor")


@lru_cache(maxsize=16)
def guide(lang: str = "us") -> dict[str, dict]:
    """{key: {group, unit, sure, what, does[, classes]}}, the words in `lang` (numberinfo_<lang>.toml; English for a
    language or a text that has none). "classes": the only kinds of object a property-name key is about (the All values
    tab shows every kind); none: every kind that has it."""
    raw = tomllib.loads(Path(__file__).with_name("numberinfo.toml").read_text(encoding="utf-8"))
    own = Path(__file__).with_name(f"numberinfo_{lang}.toml")
    words = tomllib.loads(own.read_text(encoding="utf-8")) if lang not in ("us", "base") and own.is_file() else {}
    return {k: {"group": e["group"], "unit": e["unit"], "sure": e["sure"],
                **{t: (words.get(k) or {}).get(t) or e[t] for t in TEXTS},
                **({"classes": [c for name in e["classes"] for c in (UNIT_CLASSES if name == "units" else (name,))]}
                   if "classes" in e else {})} for k, e in raw.items()}


def lookup(cls: str, prop: str, lang: str = "us") -> dict | None:
    """The guide's entry for property `prop` of an object of class `cls`, or None when the guide has none (or its
    entry is about other kinds of object)."""
    g = guide(lang)
    e = g.get(f"{cls}.{prop}") or g.get(prop)
    return e if e is None or "classes" not in e or cls in e["classes"] else None


def plain(unit: str, value: float) -> float | None:
    """`value` in plain units (metres, km/h, degrees, %...), or None when `unit` has no plain form."""
    if unit not in PLAIN or value is None:
        return None
    return value / PLAIN[unit][0]
