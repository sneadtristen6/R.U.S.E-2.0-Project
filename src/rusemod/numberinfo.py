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
PLAIN = {"m": (260.0, "unit_m"), "kmh": (130.0, "unit_kmh"), "kmh_air": (57.78, "unit_kmh"),
         "accel": (260.0, "unit_ms2"), "deg": (math.pi / 180, "unit_deg"), "degs": (math.pi / 180, "unit_degs"),
         "s": (1.0, "unit_s"), "money": (1.0, "unit_money"), "share": (0.01, "unit_pct")}
# units a modder changes as an amount (the base-stat slider makes them smaller or larger); the rest name a kind, a
# switch or an id, typed as they are
AMOUNTS = {"m", "kmh", "kmh_air", "accel", "s", "deg", "degs", "money", "pts", "count", "times", "share", "level",
           "raw"}
GROUPS = ("health", "movement", "sight", "combat", "ammo", "production", "menu", "identity", "computer", "flight",
          "turret", "looks", "sound", "interface", "effects")
SURE = ("tried", "known", "community", "name")


@lru_cache(maxsize=16)
def guide(lang: str = "us") -> dict[str, dict]:
    """{key: {group, unit, sure, what, does}}, the words in `lang` (numberinfo_<lang>.toml; English for a language or
    a text that has none)."""
    raw = tomllib.loads(Path(__file__).with_name("numberinfo.toml").read_text(encoding="utf-8"))
    own = Path(__file__).with_name(f"numberinfo_{lang}.toml")
    words = tomllib.loads(own.read_text(encoding="utf-8")) if lang not in ("us", "base") and own.is_file() else {}
    return {k: {"group": e["group"], "unit": e["unit"], "sure": e["sure"],
                **{t: (words.get(k) or {}).get(t) or e[t] for t in TEXTS}} for k, e in raw.items()}


def lookup(cls: str, prop: str, lang: str = "us") -> dict | None:
    """The guide's entry for property `prop` of an object of class `cls`, or None when the guide has none."""
    g = guide(lang)
    return g.get(f"{cls}.{prop}") or g.get(prop)


def plain(unit: str, value: float) -> float | None:
    """`value` in plain units (metres, km/h, degrees, %...), or None when `unit` has no plain form."""
    if unit not in PLAIN or value is None:
        return None
    return value / PLAIN[unit][0]
