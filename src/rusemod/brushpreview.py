"""The field brush's preview: what one dab would do to a map, worked out exactly as the build does it (brush_fields
and expand_field_brush on the map's own scenery, copy_objects for the crops, paint_strokes for the ground picture
under it) without building anything, and set against the map's layout (rusemod.maplayout): which plots change and
into what, what stays standing on them (hay, farm machines, fences, trees), the buildings round them and how near the
new crops come, compared with what the map itself does (maplayout.facts). A picture of the ground from above, before
and after, with the plots drawn, comes with it (render).

    got = preview(dab, look, sc, raw, lay, store, bounds, halves, descs, facts)
    render(got, "preview.png")
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

M = 260.0


@dataclass
class Preview:
    dab: object
    look: str
    plots: list                         # [{id, stickers, look before, rows before, rows after, source, area m2}]
    neighbours: list                    # plot ids round the changed ones (unchanged)
    stays: list                         # [{plot, name, x, y, depth m, stays}] hay, machines on the changed plots
    buildings: list                     # [{name, x, y, gap m, nearest new standing crop m}] from its walls
    warnings: list                      # plain sentences: what the map itself never does
    notes: list                         # the brush's own notes
    box: tuple                          # x0, y0, x1, y1 (map units) the pictures cover
    before: object = None               # (x, y) -> rgb sampler of the shipped picture
    after: object = None                # the same after the dab's paint
    squares: dict = field(default_factory=dict)   # plot id -> [(x, y, half, facing radians)]
    crops_laid: int = 0
    crops: list = field(default_factory=list)     # [(x, y, standing)] every crop the dab lays
    rects: list = field(default_factory=list)     # the buildings' boxes round the plots, scenery.building_rects
    parcel: object = None                         # parcels.Parcel: the ground the dab changed (with a FieldGround)


def _plot_of_sticker(lay) -> dict:
    out = {}
    for p in lay.plots:
        for k in p.stickers:
            sym, m, _mask, _h = lay.stickers[k]
            out[(sym, round(m[3], 1), round(m[7], 1))] = p.id
    return out


def preview(dab, look: dict, sc, raw: bytes, lay, store, bounds, halves: dict | None, descs: dict,
            facts: dict | None = None, margin: float = 40.0 * M, buildings: dict | None = None,
            ground=None) -> Preview:
    """What `dab` (scenery.FieldBrush) with `look` (look_library()[name]) does to the map whose shipped scenery is
    `sc` (its bytes `raw`), ground picture `store` (Tmst, highdef) over `bounds`, layout `lay` (maplayout.Layout),
    its buildings' boxes and gaps `buildings` (scenery.building_table): see the module."""
    from .groundpaint import _picture_sampler, paint_strokes
    from .scenery import HARVESTED, HAY_PATCH, brush_fields, building_rects, copy_objects, expand_field_brush
    from .tmst import Tmst
    fields = brush_fields(dab, look, sc, halves)
    before = _picture_sampler(store, bounds, 0) if store is not None else None
    parcel = None
    if ground is not None:   # (as the build: the dab's parcel, rusemod.parcels)
        from .scenery import _facing
        parcel = ground.parcel(dab.footprint(), [(m[3], m[7], h, math.radians(_facing(m)))
                                                 for f in fields for _s, m, _k, h in f])
    erases, objects, copies, stamps, notes = expand_field_brush(dab, look, sc, halves=halves, fields=fields,
                                                                buildings=buildings, descs=descs, parcel=parcel,
                                                                ground=ground)
    owner = _plot_of_sticker(lay)
    plots = {p.id: p for p in lay.plots}
    laid_rows: dict = {}
    for o in objects:   # the rows the brush lays (and neighbours' laid back as they were)
        laid_rows[(round(o.x, 1), round(o.y, 1))] = o.type.rsplit("/", 1)[-1]
    rows_out = []
    if parcel is not None:   # the plots holding a piece laid again: what of each the parcel changed
        changed_pieces: dict = {}
        for (sym, x, y), pid in owner.items():
            if (x, y) in laid_rows:
                changed_pieces.setdefault(pid, []).append(laid_rows[(x, y)])
        changed = sorted(changed_pieces)
        note = next((n for n in notes if "like the field at " in n), "")
        source = note.split("like the field at ", 1)[1].split(":", 1)[0] if note else ""
        for pid in changed:
            p = plots[pid]
            after: dict = {}
            for kind in changed_pieces[pid]:
                after[kind] = after.get(kind, 0) + 1
            rows_out.append({"id": pid, "stickers": len(p.stickers), "look before": p.look, "rows before": p.rows,
                             "rows after": after, "source": source, "area m2": p.area_m2,
                             "picture before": p.picture})
    else:
        by_field = []
        for f in fields:
            ids = {owner.get((s, round(m[3], 1), round(m[7], 1))) for s, m, _k, _h in f}
            by_field.append(sorted(i for i in ids if i is not None))
        changed = sorted({i for ids in by_field for i in ids})
        field_notes = [n for n in notes if "a whole field of " in n]   # (one a field, in the fields' order)
        for g, f in enumerate(fields):
            after = {}
            for _s, m, _k, _h in f:
                kind = laid_rows.get((round(m[3], 1), round(m[7], 1)), "?")
                after[kind] = after.get(kind, 0) + 1
            note = field_notes[g] if g < len(field_notes) else ""
            source = note.split("like the field at ", 1)[1].split(":", 1)[0] if "like the field at " in note else ""
            for pid in by_field[g]:
                p = plots[pid]
                rows_out.append({"id": pid, "stickers": len(p.stickers), "look before": p.look, "rows before": p.rows,
                                 "rows after": after, "source": source, "area m2": p.area_m2,
                                 "picture before": p.picture})
    neighbours = sorted({n for pid in changed for n in plots[pid].neighbours} - set(changed))
    # the hay and machines on the changed plots: which the brush takes off (one-object erases), which stay
    gone = {(e.types[0].rsplit("/", 1)[-1], round(e.x), round(e.y)) for e in erases if len(e.types) == 1}
    stays = []
    for pid in changed:
        for name, x, y, depth, _crops6 in plots[pid].hay:
            stays.append({"plot": pid, "name": name, "x": x, "y": y, "depth m": depth,
                          "stays": (name, round(x), round(y)) not in gone})
    # the crops the copies lay: standing ones (not laid harvested: squashed under 0.6 or sunk past 0.1 m) near what
    # stays, and how near they come to the walls of the buildings round the changed plots
    laid, _cn = copy_objects(raw, copies, descs, {look.get("map", ""): raw} if look.get("map") else None)
    crops = [(o.x, o.y) for o in laid]
    standing = [(o.x, o.y, o.type.rsplit("/", 1)[-1]) for o in laid if (o.height or 1.0) >= 0.6 and o.lift >= -0.1 * M]
    warnings = []
    for s in stays:   # (of the kinds Eugen lays harvested round hay: the light green and border crops he leaves)
        if s["stays"]:
            d, kind = min(((math.hypot(cx - s["x"], cy - s["y"]), k) for cx, cy, k in standing if k in HARVESTED),
                          default=(None, ""))
            if d is not None and d < 2.0 * M:
                warnings.append(f"{s['name']} stays on plot {s['plot']} with new standing crops ({kind}) {d / M:.1f} m"
                                f" from it (round Eugen's hay and machines his are harvested: {HAY_PATCH / M:.0f} m)")
    xs = [lay.stickers[k][1][3] for pid in changed for k in plots[pid].stickers] or [dab.x]
    ys = [lay.stickers[k][1][7] for pid in changed for k in plots[pid].stickers] or [dab.y]
    if parcel is not None:   # (the picture round the parcel)
        px0, py0, px1, py1 = parcel.box()
        xs, ys = [px0, px1], [py0, py1]
    buildings_out = []
    rects = building_rects(sc, buildings, (min(xs) - margin, min(ys) - margin, max(xs) + margin,
                                           max(ys) + margin)) if buildings else []
    if buildings:
        for name, cx, cy, hu, hv, ux, uy, gap in rects:
            best = None
            for x, y, _k in standing:
                du = abs((x - cx) * ux + (y - cy) * uy) - hu
                dv = abs(-(x - cx) * uy + (y - cy) * ux) - hv
                d = math.hypot(max(du, 0.0), max(dv, 0.0))
                if best is None or d < best:
                    best = d
            if best is None or best > 40.0 * M:
                continue
            buildings_out.append({"name": name.rsplit("/", 1)[-1], "x": cx, "y": cy, "gap m": round(gap / M, 2),
                                  "nearest new standing crop m": round(best / M, 2)})
            if best < gap - 1.0:
                warnings.append(f"new standing crops come {best / M:.1f} m from the walls of {name.rsplit('/', 1)[-1]}"
                                f" (its type keeps {gap / M:.1f} m on D-Day)")
    buildings = buildings_out
    # the pictures
    box = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
    after = None
    if store is not None:   # (no picture: the plots, what stays and the buildings alone)
        painted = paint_strokes(store, bounds, stamps)
        after_store = Tmst(*store.rebuild(painted)) if painted else store
        after = _picture_sampler(after_store, bounds, 0)
    squares = {}
    for pid in set(changed) | set(neighbours):
        squares[pid] = [(lay.stickers[k][1][3], lay.stickers[k][1][7], lay.stickers[k][3],
                         math.atan2(lay.stickers[k][1][4], lay.stickers[k][1][0])) for k in plots[pid].stickers]
    return Preview(dab, dab.look, rows_out, neighbours, stays, buildings, warnings, notes, box, before, after, squares,
                   len(crops), [(o.x, o.y, (o.height or 1.0) >= 0.6 and o.lift >= -0.1 * M) for o in laid], rects,
                   parcel)


def render(pv: Preview, path, px: float = 0.6 * M, changed_colour=(255, 255, 255), outlines: bool = True,
           box: tuple | None = None, crops: bool = False) -> None:
    """The ground from above, before (left) and after (right), north up: the changed plots' squares in white, the
    plots round them in blue, hay and farm machines yellow, the buildings near them red, the dab dotted. `outlines`
    False: the ground alone; `box` (x0, y0, x1, y1 map units): that part only; `crops`: on the after side every crop
    the dab lays (standing white, harvested orange), the hay and machines (yellow rings: staying, red crosses: taken
    off) and the buildings' boxes (blue)."""
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = box or pv.box
    w, h = int((x1 - x0) / px), int((y1 - y0) / px)
    img = Image.new("RGB", (2 * w + 10, h), (0, 0, 0))
    for side, at in ((0, pv.before), (w + 10, pv.after)):
        for j in range(h):
            y = y1 - (j + 0.5) * px
            for i in range(w):
                c = at(x0 + (i + 0.5) * px, y)
                if c is not None:
                    img.putpixel((side + i, j), tuple(int(v) for v in c[:3]))
    d = ImageDraw.Draw(img)
    if crops:
        def at_after(x, y):
            return w + 10 + (x - x0) / px, (y1 - y) / px
        for x, y, up in pv.crops:
            if x0 <= x <= x1 and y0 <= y <= y1:
                cx, cy = at_after(x, y)
                d.ellipse((cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5), fill=(255, 255, 255) if up else (255, 140, 0))
        for _n, cx, cy, hu, hv, ux, uy, _gap in pv.rects:
            if not (x0 + max(hu, hv) * 1.42 <= cx <= x1 - max(hu, hv) * 1.42
                    and y0 + max(hu, hv) * 1.42 <= cy <= y1 - max(hu, hv) * 1.42):
                continue   # (one the picture holds whole only: the after side alone)
            pts = [at_after(cx + a * hu * ux - b * hv * uy, cy + a * hu * uy + b * hv * ux)
                   for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            d.polygon(pts, outline=(60, 120, 255), width=2)
        for s in pv.stays:
            cx, cy = at_after(s["x"], s["y"])
            if s["stays"]:
                d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), outline=(255, 220, 0), width=2)
            else:
                d.line((cx - 4, cy - 4, cx + 4, cy + 4), fill=(255, 40, 40), width=2)
                d.line((cx - 4, cy + 4, cx + 4, cy - 4), fill=(255, 40, 40), width=2)
    if not outlines:
        img.save(str(path))
        return
    changed = {r["id"] for r in pv.plots}

    def to(side, x, y):
        return side + (x - x0) / px, (y1 - y) / px
    for side in (0, w + 10):
        for pid, sq in pv.squares.items():
            colour, width = (changed_colour, 1) if pid in changed else ((90, 140, 255), 1)
            for x, y, half, t in sq:
                c, s = math.cos(t), math.sin(t)
                pts = [to(side, x + a * half * c - b * half * s, y + a * half * s + b * half * c)
                       for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                d.polygon(pts, outline=colour, width=width)
        for s in pv.stays:
            cx, cy = to(side, s["x"], s["y"])
            d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(255, 220, 0))
        for b in pv.buildings:
            cx, cy = to(side, b["x"], b["y"])
            d.rectangle((cx - 4, cy - 4, cx + 4, cy + 4), outline=(255, 40, 40), width=2)
        foot = pv.dab.footprint()
        for k in range(0, 360, 6):
            a = math.radians(k)
            r = pv.dab.radius
            if pv.dab.shape == "square":
                c, s = pv.dab.dx, pv.dab.dy
                n = math.hypot(c, s) or 1.0
                c, s = c / n, s / n
                u, v = math.cos(a), math.sin(a)
                kk = max(abs(u), abs(v))
                u, v = u / kk * r, v / kk * r
                px_, py_ = pv.dab.x + u * c - v * s, pv.dab.y + u * s + v * c
            else:
                px_, py_ = pv.dab.x + r * math.cos(a), pv.dab.y + r * math.sin(a)
            cx, cy = to(side, px_, py_)
            d.point((cx, cy), fill=(255, 255, 255))
        del foot
    img.save(str(path))
