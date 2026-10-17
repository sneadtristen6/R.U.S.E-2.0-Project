"""Repaint what moved, by rules (Map Paint plan step 8; MOD_FORMAT §8 `brush = "repaint"`): inside a repaint stroke,
the ground the mod's ground brushes moved by at least `height` (MOVED when 0) is painted by its new shape with a
theme's palette (groundtex.palette), as the shipped map paints such ground:

  steep (STEEP degrees and more)                         rock
  at or under a lake's surface (the mod's water strokes)  mud
  less than SHORE over a lake's surface (`beach` only)    sand
  anything else                                           grass

The numbers are the shipped map's own, measured on D-Day (2026-10-16): under 10 degrees its rock stickers are 1% of
the rock, grass and earth stickers, 18% at 15-20, a quarter from 20 to 40 and most of them only from 40; its beach is
in its ground picture, not its stickers, and is the beach's beige for the first 3 m over the sea (two thirds of the
ground near the sea at the lowest dry metre, under two fifths from 3 m up). Its rivers and marshes have no beach, so
the map's own water isn't a shore here: only the mod's new lakes are (each water stroke's level, inside its
footprint grown by SHORE_REACH). The sand is the stroke's choice (`beach`, off unless asked: not every lake has a
beach, the owner 2026-10-16, and D-Day's inland water has none; sand by hand where one is wanted). A new lake's bed
and, with `beach`, its shore are repainted (mud, sand) whether or not the ground there moved: a shore hardly moves,
and a lake dug with a soft brush left only its bed moving 2 m, so its beach didn't show.

On a blank map (its first height stroke levels the whole map, as Blank Terrain starts: start_level) what moved is
measured from that flat start, and the strokes go over its one-colour coat (coats), not under it.

The ground is read on a grid of CELL squares over each stroke (Tms.height_box), old and new alike: fine enough to
follow a drawn map's ground (a point every 9.85 m: rusemod.groundgen), its steps too small to see under the torn
edge (16 m squares made a staircase and lost a plateau's narrow foot: the retest, 10-16). Each run of squares along
x with one material becomes ONE texture stroke: a line through the run's middles, REACH squares wide each way,
hard-edged, with the Ragged edge brush pattern. Ragged tears a stroke in to RAG_IN of its reach and never further,
and a point between two rows lies half a reach from both: the ground between them is always covered (a rectangle of
the run, torn in by its own length, left the coat showing at the ends of long runs). The materials are laid in
LAID's order, rock last (its band is narrow: a neighbour's reach would eat it). They are laid before the mod's own
paint, so a brush stroke over them wins. They carry the stroke's `rocks`: on, the build lays the map's own 3D rocks
over the rock (rusemod.rocks)."""
from __future__ import annotations

import math

from .tms import Tms

CELL = 4.0 * 260.0    # map units a square of the grid is across (4 m), over each repaint stroke only
MOVED = 2.0 * 260.0   # the ground must have moved at least this much (2 m) to be repainted, unless the stroke says
STEEP = 40.0          # degrees: rock from here (D-Day's rock is most of the ground's stickers from 40)
SHORE = 3.0 * 260.0   # sand up to this over a lake's surface (D-Day's beach: its first 3 m over the sea)
SHORE_REACH = 1.3     # a lake's shore lies inside its footprint grown by this much
REACH = 1.0           # a run's stroke reaches this many squares from its line (torn in to brushmask.RAG_IN of it,
                      # at most, it still covers half a square each way at full strength under its hard edge)
MASK = "ragged"       # whole, its outline torn: the joins between materials don't show straight
MATERIALS = ("rock", "mud", "sand", "grass")
LAID = ("mud", "grass", "sand", "rock")   # the order the materials' strokes are laid: under the water first, a
                                            # beach over the grass's reach, the narrow rock band last


class RepaintError(ValueError):
    pass


def material(slope: float, z: float, under: list[float], near: list[float]) -> str:
    """The rule for a square of moved ground: its slope (degrees), its new height, the surfaces of the lakes over it
    (`under`: those whose footprint holds it) and near it (`near`: their footprints grown by SHORE_REACH)."""
    if slope >= STEEP:
        return "rock"
    if any(z <= w for w in under):
        return "mud"
    if any(z - w < SHORE for w in near):
        return "sand"
    return "grass"


def start_level(ground_strokes: list, mesh: bytes) -> float | None:
    """The height a map's ground starts from when its first height stroke levels the whole map (Blank Terrain, Blank
    Ocean, a map whose ground is drawn as our own: rusemod.groundgen), else None. On such a map what moved is what the
    later brushes moved from that flat start, not from the copied map's own ground: measured from that, a repaint
    stroke would paint all it covers (the whole map moved)."""
    from .brush import GROUND_UNCHANGED
    from .groundgen import _levels_all
    heights = [s for s in ground_strokes if s.kind.kind not in GROUND_UNCHANGED]
    if not heights:
        return None
    b = Tms(mesh).bounds
    return heights[0].level if _levels_all(heights[0], (b[0], b[1], b[3], b[4])) else None


def coats(paint_strokes: list, mesh: bytes) -> int:
    """How many of a map's paint strokes, from the first, coat the whole map at full strength (Blank Terrain's one
    colour, the start of a blank map's picture): what repaint lays goes over them and under the rest, as it goes
    over the map's own picture elsewhere (under the coat, it was never seen)."""
    from .brush import HARD_EDGE
    b = Tms(mesh).bounds
    corners = [(x, y) for x in (b[0], b[3]) for y in (b[1], b[4])]
    n = 0
    for s in paint_strokes:
        if not (s.brush == "paint" and s.edge == "hard" and s.weight >= 1.0 and not s.mask and not s.dither
                and all(s.footprint().t2(x, y) <= HARD_EDGE * HARD_EDGE for x, y in corners)):
            break
        n += 1
    return n


def expand(strokes: list, old_mesh: bytes, new_mesh: bytes, water_strokes: list,
           start: float | None = None) -> tuple[list, str]:
    """The texture strokes that paint what moved inside the repaint `strokes`, and what was done in words. `start`: the
    flat height the map's ground starts from (start_level), which stands for the old ground."""
    from dataclasses import replace
    from .brush import Stroke
    from .groundtex import palette
    new = Tms(new_mesh)
    old = Tms(old_mesh) if start is None else None
    lakes = [(w.level, w.footprint(), replace(w, radius=w.radius * SHORE_REACH).footprint()) for w in water_strokes]
    pal = palette()
    runs, counts = {m: [] for m in MATERIALS}, {m: 0 for m in MATERIALS}
    for rs in strokes:
        theme = rs.theme or "dday"
        refs = {m: f"swatch:{theme}:{m}" for m in MATERIALS}
        missing = [r for r in refs.values() if r not in pal]
        if missing:
            raise RepaintError(f"the {theme} palette has no {missing[0].split(':')[-1]}")
        moved = rs.height if rs.height > 0.0 else MOVED
        foot = rs.footprint()
        bx0, bx1, by0, by1 = foot.box()
        x0, y0 = bx0 - CELL, by0 - CELL   # the stroke's box and a square round it (for the slope at its edge)
        after = new.height_box(x0, y0, bx1 + CELL, by1 + CELL, CELL)
        if old is not None:
            before = old.height_box(x0, y0, bx1 + CELL, by1 + CELL, CELL)
        else:
            before = [[None if z is None else start for z in row] for row in after]
        rows, cols = len(after), len(after[0])
        sx = sy = CELL
        r0, r1, c0, c1 = 1, rows - 2, 1, cols - 2
        for r in range(r0, r1 + 1):
            run = None   # (material, first column, last column)
            for c in range(c0, c1 + 2):
                what = None
                if c <= c1:
                    x, y = x0 + (c + 0.5) * sx, y0 + (r + 0.5) * sy
                    a, b = before[r][c], after[r][c]
                    if b is not None and foot.t2(x, y) < 1.0:
                        went = a is not None and abs(b - a) >= moved
                        under = [lv for lv, f, _g in lakes if f.t2(x, y) < 1.0]
                        near = [lv for lv, _f, g in lakes if g.t2(x, y) < 1.0] if rs.beach else []
                        n = [after[r][c - 1], after[r][c + 1], after[r - 1][c], after[r + 1][c]]
                        if (went or under or near) and None not in n:
                            gx, gy = (n[1] - n[0]) / (2 * sx), (n[3] - n[2]) / (2 * sy)
                            slope = math.degrees(math.atan(math.sqrt(gx * gx + gy * gy)))
                            what = material(slope, b, under, near)
                            if not went and what not in ("mud", "sand"):   # unmoved: only a new lake's bed, shore
                                what = None
                if run and what == run[0]:
                    run = (what, run[1], c)
                    continue
                if run:
                    m, a0, a1 = run
                    ry = y0 + (r + 0.5) * sy
                    runs[m].append(Stroke("texture", x0 + (a0 + 0.5) * sx, ry, REACH * max(sx, sy), shape="line",
                                          x2=x0 + (a1 + 0.5) * sx, y2=ry, edge="hard", texture=refs[m], mask=MASK,
                                          rocks=rs.rocks))
                    counts[m] += a1 - a0 + 1
                run = (what, c, c) if what else None
    out = [s for m in LAID for s in runs[m]]
    said = (", ".join(f"{n} squares of {m}" for m, n in counts.items() if n) or "no ground moved enough") + \
        f" ({CELL / 260.0:.0f} m squares, {len(out)} strokes)"
    return out, said
