"""Which mod versions to use, and in which order to apply them. The rules are in docs/MOD_FORMAT.md §10.6.

- Versions: for every mod, the newest version that every range asking for it accepts.
- Order: a dependency (or an optional dependency that is present, or a mod named in a `when mod` block) loads before
  the mod that needs it; `load.after` / `load.before` add more arrows; when several mods are free to go next, the one
  whose id sorts first goes. A loop is an error that names it. `[conflicts]` stops everything first.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


class ResolveError(Exception):
    pass


@dataclass
class ModInfo:
    id: str
    version: str = "0.0.0"
    depends: dict[str, str] = field(default_factory=dict)    # id -> version range
    optional: dict[str, str] = field(default_factory=dict)   # id -> version range
    after: list[str] = field(default_factory=list)
    before: list[str] = field(default_factory=list)
    conflicts: dict[str, str] = field(default_factory=dict)  # id -> version range
    when_mods: set[str] = field(default_factory=set)         # ids named in `when mod` blocks
    text_prefix: str = ""                                    # start of the text keys the mod hands out (§6)
    texts: list = field(default_factory=list)                # loc.TextRow from text/*.csv
    terrain: dict = field(default_factory=dict)              # map pack name -> [brush.Stroke] (§8)


# --- versions ---
def parse_version(s: str) -> tuple[int, int, int]:
    parts = [int(p) for p in s.strip().split(".")]
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"bad version {s!r}")
    return tuple(parts + [0] * (3 - len(parts)))  # type: ignore[return-value]


_CONSTRAINT = re.compile(r"^\s*(>=|<=|==|=|>|<|\^|~)?\s*([0-9][0-9.]*)\s*$")


def matches(version: str, spec: str) -> bool:
    """Does `version` satisfy `spec`? Specs: "*", ">=0.1, <0.2", "^0.3", "~1.2", "1.2.0" (exact)."""
    v = parse_version(version)
    for part in spec.split(","):
        part = part.strip()
        if part in ("*", ""):
            continue
        m = _CONSTRAINT.match(part)
        if not m:
            raise ValueError(f"bad version range {spec!r}")
        op, raw = m.group(1) or "=", m.group(2)
        w = parse_version(raw)
        if op == "^":  # up to the next breaking change: 1.2.3 -> <2.0.0, 0.3.1 -> <0.4.0, 0.0.4 -> <0.0.5
            n = len(raw.split("."))
            top = (w[0] + 1, 0, 0) if w[0] or n == 1 else (0, w[1] + 1, 0) if w[1] or n == 2 else (0, 0, w[2] + 1)
            ok = w <= v < top
        elif op == "~":  # same minor version
            ok = w <= v < (w[0], w[1] + 1, 0)
        else:
            ok = {">=": v >= w, "<=": v <= w, ">": v > w, "<": v < w, "=": v == w, "==": v == w}[op]
        if not ok:
            return False
    return True


def pick_versions(requested: dict[str, str], catalog: dict[str, list[ModInfo]]) -> dict[str, ModInfo]:
    """Choose one version per mod: the newest that every range asking for it accepts (dependencies included)."""
    wants: dict[str, list[tuple[str, str]]] = {mid: [("you", rng)] for mid, rng in requested.items()}
    chosen: dict[str, ModInfo] = {}
    for _ in range(100):
        new: dict[str, ModInfo] = {}
        for mid, asks in wants.items():
            if mid not in catalog:
                who = ", ".join(w for w, _ in asks)
                raise ResolveError(f"mod {mid!r} is needed by {who} but isn't available")
            ok = [m for m in catalog[mid] if all(matches(m.version, rng) for _, rng in asks)]
            if not ok:
                detail = "; ".join(f"{w} wants {rng}" for w, rng in asks)
                have = ", ".join(m.version for m in catalog[mid])
                raise ResolveError(f"no version of {mid!r} fits everyone ({detail}; available: {have})")
            new[mid] = max(ok, key=lambda m: parse_version(m.version))
        if {k: v.version for k, v in new.items()} == {k: v.version for k, v in chosen.items()}:
            return chosen
        chosen = new
        wants = {mid: [("you", rng)] for mid, rng in requested.items()}
        for m in chosen.values():
            for dep, rng in m.depends.items():
                wants.setdefault(dep, []).append((f"{m.id} {m.version}", rng))
    raise ResolveError("version choice doesn't settle (dependencies keep changing each other)")


# --- order ---
def load_order(mods: list[ModInfo]) -> list[ModInfo]:
    by_id = {m.id: m for m in mods}
    for m in mods:
        for dep, rng in m.depends.items():
            if dep not in by_id:
                raise ResolveError(f"{m.id} needs {dep}, which isn't in the mod set")
            if not matches(by_id[dep].version, rng):
                raise ResolveError(f"{m.id} needs {dep} {rng}, but the set has {by_id[dep].version}")
        for other, rng in m.conflicts.items():
            if other in by_id and matches(by_id[other].version, rng):
                raise ResolveError(f"{m.id} can't be used together with {other} {by_id[other].version}")
    before: dict[str, set[str]] = {m.id: set() for m in mods}  # id -> ids that must load before it
    for m in mods:
        for dep in list(m.depends) + [d for d in m.optional if d in by_id] + [d for d in m.when_mods if d in by_id] \
                + [a for a in m.after if a in by_id]:
            if dep != m.id:
                before[m.id].add(dep)
        for b in m.before:
            if b in by_id and b != m.id:
                before[b].add(m.id)
    order: list[ModInfo] = []
    placed: set[str] = set()
    while len(order) < len(mods):
        ready = sorted(mid for mid in before if mid not in placed and before[mid] <= placed)
        if not ready:
            raise ResolveError("load order loop: " + " -> ".join(_find_loop(before, placed)))
        order.append(by_id[ready[0]])
        placed.add(ready[0])
    return order


def _find_loop(before: dict[str, set[str]], placed: set[str]) -> list[str]:
    start = sorted(mid for mid in before if mid not in placed)[0]
    path, seen = [start], {start}
    node = start
    while True:
        node = sorted(d for d in before[node] if d not in placed)[0]
        if node in seen:
            return path[path.index(node):] + [node]
        path.append(node)
        seen.add(node)
