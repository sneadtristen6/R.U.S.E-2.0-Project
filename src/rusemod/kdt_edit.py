"""Keeping a .kdt's trees true after its points move up or down (the recipe of DomesticNukes and his Claude,
2026-09-29, checked in the game on Blitz).

A .kdt is the ground the game asks "where does this ray hit?": a click for a move order, the camera's floor. Its
k-d trees wrap the ground tightly in z. A triangle moved outside the z limits on its path is simply not found, so
the click lands on nothing (the order is refused) and the camera falls through. Movement itself runs on other files.

  refit(kdt, s, moved)   subtree s's own tree after vertices `moved` changed height: every z clip over a moved
                         triangle is widened to cover it (keep-below clips raised to its top, keep-above clips lowered
                         to its bottom). A z split can't be widened without breaking its other side, so when a moved
                         triangle no longer touches exactly the sides of one it's listed on, the subtree's tree is
                         built again (`rebuild`)
  rebuild(kdt, s)        a new tree over the same triangles, split on x and y only (at the median of the triangles'
                         centres), leaves of at most MAX_LEAF triangles. The game accepts trees with no z clips; they
                         are only a little slower
  widen_main(kdt, subs)  the MainNode, the tree over the subtrees: every z clip on a moved subtree's path is widened to
                         the subtree's new height range. Its x and y are unchanged
  check(kdt, s)          the rule a written tree must keep: every triangle a leaf lists touches the leaf's cell

Widening is always safe: a ray then tests a few more triangles. Values in a subtree's tree are quantized like its
positions; the MainNode's are world units (float32), widened by half a step so rounding can't pull them back in.
"""
from __future__ import annotations

from .kdt import Clip, Kdt, Leaf, Split, leaves, main_regions

MAX_LEAF = 48      # triangles per leaf in a rebuilt tree (DomesticNukes' builder; the game's leaves hold up to 256)


def triangles(kdt: Kdt, s: int) -> tuple[list, list]:
    """Subtree `s`'s positions (quantized) and its triangles as vertex triples."""
    pos = kdt.positions(s)
    idx = kdt.indices(s)
    return pos, [tuple(idx[k:k + 3]) for k in range(0, len(idx), 3)]


def refit(kdt: Kdt, s: int, moved: set[int]) -> str:
    """Fit subtree `s`'s tree to its moved vertices (their new heights are already written). Returns "" when no
    triangle moved, "kept" when every limit already covered them, "widened" or "rebuilt"."""
    pos, tris = triangles(kdt, s)
    zbox = {}
    for t, (a, b, c) in enumerate(tris):
        if a in moved or b in moved or c in moved:
            za, zb, zc = pos[a][2], pos[b][2], pos[c][2]
            zbox[t] = (min(za, zb, zc), max(za, zb, zc))
    if not zbox:
        return ""
    root = kdt.tree(s)
    lists = kdt.trilists(s, root)
    state = {"leaf": 0, "changed": False, "crossed": False}
    empty: frozenset = frozenset()

    def walk(n):
        """The moved triangles listed under `n`, widening the clips on the way back up."""
        if isinstance(n, Leaf):
            listed = lists[state["leaf"]]
            state["leaf"] += 1
            found = {t for t in listed if t in zbox}
            return found or empty
        if isinstance(n, Split):
            above, below = walk(n.above), walk(n.below)
            if n.axis == 2 and (above or below):
                v = n.value
                # a moved triangle must be listed on exactly the sides it touches now: missing from one, rays there
                # won't find it; left on one it no longer touches, the tree breaks the containment rule
                for t in above | below:
                    lo, hi = zbox[t]
                    if (hi >= v) != (t in above) or (lo <= v) != (t in below):
                        state["crossed"] = True
                        break
            return above | below if above and below else above or below
        under = walk(n.child)
        if n.axis == 2 and under:
            if n.keep_above:
                lo = min(zbox[t][0] for t in under)
                if lo < n.value:
                    n.value, state["changed"] = lo, True
            else:
                hi = max(zbox[t][1] for t in under)
                if hi > n.value:
                    n.value, state["changed"] = hi, True
        return under

    walk(root)
    if state["crossed"]:
        rebuild(kdt, s, pos, tris)
        return "rebuilt"
    if state["changed"]:
        kdt.set_tree(s, root, lists)
        return "widened"
    return "kept"


def rebuild(kdt: Kdt, s: int, pos=None, tris=None) -> None:
    """Give subtree `s` a new tree over its triangles: x/y splits at the median of the triangles' centres (on the
    wider axis), a triangle going to each side it touches (the first child: max >= v; the second: min <= v), leaves
    of at most MAX_LEAF triangles."""
    if pos is None or tris is None:
        pos, tris = triangles(kdt, s)
    box = []
    for a, b, c in tris:
        xs, ys = (pos[a][0], pos[b][0], pos[c][0]), (pos[a][1], pos[b][1], pos[c][1])
        box.append(((min(xs), max(xs)), (min(ys), max(ys))))
    lists: list[list[int]] = []

    def build(ts: list[int]):
        if len(ts) <= MAX_LEAF:
            lists.append(ts or [0])        # an empty leaf lists triangle 0, as the game's do
            return Leaf(max(1, len(ts)))
        # both sides must hold fewer triangles than the node, or the split never ends: the median of the centres
        # first, then other points, on the wider axis first (long triangles can straddle the middle)
        for share in (2, 4, 1.333, 8, 1.143):
            for axis in _axes(ts, box):
                centres = sorted(box[t][axis][0] + box[t][axis][1] for t in ts)
                v = centres[min(len(centres) - 1, int(len(centres) / share))] // 2
                above = [t for t in ts if box[t][axis][1] >= v]
                below = [t for t in ts if box[t][axis][0] <= v]
                if len(above) < len(ts) and len(below) < len(ts):
                    return Split(axis, v, build(above), build(below))
        if len(ts) <= 256:                 # nothing separates them (every one spans the middle): one big leaf
            lists.append(ts)
            return Leaf(len(ts))
        raise ValueError(f"subtree {s}: {len(ts)} triangles overlap too much to split into leaves")

    root = build(list(range(len(tris))))
    kdt.set_tree(s, root, lists)


def _axes(ts: list[int], box: list) -> tuple[int, int]:
    """x then y, or y then x: the axis the triangles' centres spread over most first."""
    spread = []
    for axis in (0, 1):
        lo = min(box[t][axis][0] for t in ts)
        hi = max(box[t][axis][1] for t in ts)
        spread.append(hi - lo)
    return (0, 1) if spread[0] >= spread[1] else (1, 0)


def widen_main(kdt: Kdt, subtrees) -> int:
    """Widen the MainNode's z clips on the path of every subtree in `subtrees` to cover its vertices' heights now.
    Returns how many clips changed."""
    entries = kdt.main_entries()
    regions = main_regions(entries)
    half = (kdt.bounds_max[2] - kdt.bounds_min[2]) / (2 * 0x7FFF)
    changed = 0
    for s in sorted(set(subtrees)):
        zs = [p[2] for p in kdt.positions(s)]
        if not zs or s not in regions:
            continue
        lo, hi = kdt.to_world(2, min(zs)) - half, kdt.to_world(2, max(zs)) + half
        for i in regions[s][2]:
            t, axis, rest, v = entries[i]
            if axis != 2:
                continue
            if t in (0, 1) and v < hi:
                entries[i] = (t, axis, rest, hi)
                changed += 1
            elif t in (2, 3) and v > lo:
                entries[i] = (t, axis, rest, lo)
                changed += 1
    if changed:
        kdt.set_main_entries(entries)
    return changed


def check(kdt: Kdt, s: int) -> list[str]:
    """What's wrong with subtree `s`'s tree: triangles a leaf lists that don't touch the leaf's cell (on any axis),
    and triangle numbers past the end. Empty when it's right."""
    pos, tris = triangles(kdt, s)
    root = kdt.tree(s)
    problems = []
    for k, ((leaf, lo, hi), listed) in enumerate(zip(leaves(root), kdt.trilists(s, root))):
        for t in listed:
            if t >= len(tris):
                problems.append(f"subtree {s} leaf {k}: triangle {t} past the end ({len(tris)})")
                continue
            corners = [pos[v] for v in tris[t]]
            for axis in range(3):
                tmin = min(c[axis] for c in corners)
                tmax = max(c[axis] for c in corners)
                if (lo[axis] is not None and tmax < lo[axis]) or (hi[axis] is not None and tmin > hi[axis]):
                    problems.append(f"subtree {s} leaf {k}: triangle {t} is outside the cell on axis {'xyz'[axis]}")
                    break
    return problems


def check_main(kdt: Kdt, subtrees) -> list[str]:
    """Subtrees whose vertices poke out of their MainNode region in z."""
    entries = kdt.main_entries()
    regions = main_regions(entries)
    step = (kdt.bounds_max[2] - kdt.bounds_min[2]) / 0x7FFF
    out = []
    for s in sorted(set(subtrees)):
        lo, hi, _path = regions[s]
        zs = [kdt.to_world(2, p[2]) for p in kdt.positions(s)]
        if (lo[2] is not None and min(zs) < lo[2] - step) or (hi[2] is not None and max(zs) > hi[2] + step):
            out.append(f"subtree {s}: heights {min(zs):.0f}..{max(zs):.0f} outside its region "
                       f"{lo[2] if lo[2] is not None else '-inf'}..{hi[2] if hi[2] is not None else 'inf'}")
    return out
