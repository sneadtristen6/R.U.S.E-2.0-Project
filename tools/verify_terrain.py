r"""Check terrain edits (rusemod.terrain_edit) on every map, and make the in-game hill test (PLAN.md §7 MT, T2).

Without --make-test (READ-ONLY on the game): on every Maps\PC\DataMap*_v09.dat a test hill goes, in memory, on the
dry land nearest the middle of the map, and the four ground files are checked:
  A. all four change and read back,
  B. in each file the point nearest the hill's centre rose by what the brush says, to within the file's height step,
  C. every gameplay-ground point still has the height of the close-up mesh point it sat on (same x, y and height;
     the mesh can hold several points at one x, y, a cliff's top and foot, so x and y alone don't say which),
  D. the mesh cells and tree parts the hill doesn't reach keep their exact bytes.
One line per map with the time it took, then a summary. Nothing is written.

With --make-test MAP COPY: builds a modded copy of the game at COPY (never the Steam install) with that hill on MAP,
through the same build as `ruse build` and the Studio's "Test in game", and says where the hill is and what to look
for in the game.

Usage:  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_terrain.py [game_dir] [--only Name]
        py -3 tools\verify_terrain.py [game_dir] --make-test TwoIslands D:\RUSE-Instances\hill [--radius R] [--height H]
"""
import glob
import math
import os
import struct
import sys
import tempfile
import time
import zlib
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat  # noqa: E402
from rusemod.brush import Stroke, strokes_toml  # noqa: E402
from rusemod.kdt import Kdt  # noqa: E402
from rusemod.terrain_edit import FILES, LABELS, edit_map  # noqa: E402
from rusemod.tms import Q_MAX, Tms  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"
RADIUS_SHARE = 0.05    # the test hill's radius, as a share of the map's width
HEIGHT_SHARE = 0.8     # its height, as a share of the room between the ground there and the map's highest point


def reader(arc):
    def read(member):
        try:
            return bytes(arc.read(arc.find(member)))
        except KeyError:
            return None
    return read


def test_hill(hd: Tms, radius: float | None = None, height: float | None = None) -> Stroke:
    """The test hill: on the dry land (ground above its water) nearest the middle of the map."""
    b = hd.bounds
    cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
    best = None
    for cell in hd.cells:
        for qx, qy, qz, qw in cell.positions():
            if qz <= qw or qx in (0, Q_MAX) or qy in (0, Q_MAX):
                continue
            x, y = hd.to_world(0, qx), hd.to_world(1, qy)
            d = (x - cx) ** 2 + (y - cy) ** 2
            if best is None or d < best[0]:
                best = (d, x, y, hd.to_world(2, qz))
    if best is None:  # no dry land at all: the middle of the map
        best = (0.0, cx, cy, hd.to_world(2, 0))
    _d, x, y, z = best
    if radius is None:
        radius = RADIUS_SHARE * (b[3] - b[0])
    if height is None:
        height = HEIGHT_SHARE * (b[5] - z)
    return Stroke("hill", x, y, radius, height=height)


def nearest(points, x, y):
    return min(points, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)


def world_points_mesh(t: Tms):
    return [(t.to_world(0, p[0]), t.to_world(1, p[1]), t.to_world(2, p[2]), k, i)
            for k, c in enumerate(t.cells) for i, p in enumerate(c.positions())]


def world_points_tree(t: Kdt):
    return [(t.to_world(0, p[0]), t.to_world(1, p[1]), t.to_world(2, p[2]), s, i)
            for s in range(len(t.subtrees)) for i, p in enumerate(t.positions(s))]


def check(read, name: str) -> tuple[list[str], str]:
    """Problems (empty = OK) and a summary for one map."""
    problems = []
    raw = {key: read(member) for key, member in FILES.items()}
    if raw["highdef"] is None:
        return ["no close-up mesh"], ""
    hd = Tms(raw["highdef"])
    hill = test_hill(hd)
    t0 = time.time()
    changed, notes = edit_map(read, [hill], name)
    took = time.time() - t0
    # A
    for key, member in FILES.items():
        if raw[key] is not None and member not in changed:
            problems.append(f"the {LABELS[key]} didn't change")
    new = {}
    try:
        for member, data in changed.items():
            k = next(k for k, m in FILES.items() if m == member)
            new[k] = Tms(data) if k in ("highdef", "lowdef") else Kdt(data)
    except (ValueError, struct.error, zlib.error) as exc:
        return problems + [f"an edited file doesn't read back: {exc}"], ""
    # B
    for key, obj in new.items():
        old = Tms(raw[key]) if key in ("highdef", "lowdef") else Kdt(raw[key])
        pts = world_points_mesh(old) if key in ("highdef", "lowdef") else world_points_tree(old)
        x, y, z, part, i = nearest([p for p in pts if hill.covers(p[0], p[1])] or pts, hill.x, hill.y)
        if key in ("highdef", "lowdef"):
            q = obj.cells[part].positions()[i][2]
            lo, hi = obj.bounds[2], obj.bounds[5]
        else:
            q = obj.positions(part)[i][2]
            lo, hi = obj.bounds_min[2], obj.bounds_max[2]
        want = min(max(hill.height_at(x, y, z), lo), hi)
        got = obj.to_world(2, q)
        step = (hi - lo) / Q_MAX
        if abs(got - want) > step:
            problems.append(f"the {LABELS[key]} rose to {got:.1f} at the hill's centre, not {want:.1f}")
    # C: the close-up mesh can hold several points at one x, y at different heights (a cliff's top and foot: every
    # shipped mesh has hundreds), so each gameplay-ground point is matched, before the edit, to the mesh point it
    # sits on (same quantized x, y and height; all 32 shipped maps: every ground point has one) and must have that
    # point's height after it, exactly
    if "ground" in new and "highdef" in new:
        g, h = new["ground"], new["highdef"]
        if tuple(g.bounds_min) == tuple(h.bounds[:3]) and tuple(g.bounds_max) == tuple(h.bounds[3:]):
            after: dict[tuple, set] = {}   # close-up mesh point (x, y, height before) -> its heights after
            for a, b in zip(Tms(raw["highdef"]).cells, h.cells):
                for p, q in zip(a.positions(), b.positions()):
                    after.setdefault(p[:3], set()).add(q[2])
            old_g = Kdt(raw["ground"])
            off = lost = 0
            for s in range(len(g.subtrees)):
                for p, q in zip(old_g.positions(s), g.positions(s)):
                    heights = after.get(p)
                    if heights is None:
                        lost += 1
                    elif heights != {q[2]}:
                        off += 1
            if off:
                problems.append(f"{off} gameplay-ground point(s) differ from the close-up mesh")
            if lost:
                problems.append(f"{lost} gameplay-ground point(s) sit on no close-up mesh point (before the edit)")
    # D
    for key in ("highdef", "lowdef"):
        if key in new:
            old = Tms(raw[key])
            for k, (a, b) in enumerate(zip(old.cells, new[key].cells)):
                reach = any(hill.covers(old.to_world(0, p[0]), old.to_world(1, p[1])) for p in a.positions())
                if not reach and a.vb != b.vb:
                    problems.append(f"{LABELS[key]} cell {k} changed though the hill doesn't reach it")
    for key in ("ground", "camera"):
        if key in new:
            old = Kdt(raw[key])
            for s, (a, b) in enumerate(zip(old.subtrees, new[key].subtrees)):
                reach = any(hill.covers(old.to_world(0, p[0]), old.to_world(1, p[1])) for p in old.positions(s))
                if not reach and a.positions != b.positions:
                    problems.append(f"{LABELS[key]} part {s} changed though the hill doesn't reach it")
    summary = (f"hill at ({hill.x:.0f}, {hill.y:.0f}), radius {hill.radius:.0f}, height {hill.height:.0f}; "
               f"{notes[0].split(': ', 1)[1]}; {took:.1f} s")
    return problems, summary


def make_test(game: str, name: str, copy: str, radius=None, height=None) -> int:
    from rusemod.build import build_and_write, load_mod
    pack = os.path.join(game, "Maps", "PC", f"DataMap{name}_v09.dat")
    if not os.path.isfile(pack):
        print(f"{pack} doesn't exist")
        return 2
    with Edat.open(pack) as arc:
        hd = Tms(bytes(arc.read(arc.find(FILES["highdef"]))))
    hill = test_hill(hd, radius, height)
    b = hd.bounds
    with tempfile.TemporaryDirectory() as tmp:
        mod = Path(tmp, "hill-test")
        (mod / "maps" / name).mkdir(parents=True)
        (mod / "mod.toml").write_text('[mod]\nid = "hill-test"\nname = "Hill test"\nversion = "0.1.0"\n',
                                      encoding="utf-8")
        (mod / "maps" / name / "terrain.toml").write_text(
            strokes_toml([hill], "The in-game hill test (tools/verify_terrain.py --make-test)."), encoding="utf-8")
        result = build_and_write(Path(game), [load_mod(mod)], instance=Path(copy), say=print)
    if result.errors:
        return 1
    east = (hill.x - b[0]) / (b[3] - b[0]) * 100
    south = (hill.y - b[1]) / (b[4] - b[1]) * 100
    print(f"""
The hill: {east:.0f}% of the way from the map's west edge and {south:.0f}% from its north edge (the dry land nearest
the middle), with a radius of {hill.radius:.0f} units and {hill.height:.0f} units high at its top.
Start RUSE.exe in {copy} (Steam running), play a skirmish on this map and check:
  1. the hill is drawn, close up and zoomed out, with no holes or seams around it;
  2. units drive up it and stop on top; move orders on its slopes work;
  3. the camera stays above the hill when you fly over it;
  4. line of sight: a unit behind the hill can't see one on the other side.
Screenshot the hill from the side, close and far.""")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    def option(flag, cast=float):
        if flag in argv:
            i = argv.index(flag)
            value = cast(argv[i + 1])
            del argv[i:i + 2]
            return value
        return None

    only = option("--only", str)
    radius, height = option("--radius"), option("--height")
    if "--make-test" in argv:
        i = argv.index("--make-test")
        name, copy = argv[i + 1], argv[i + 2]
        del argv[i:i + 3]
        return make_test(argv[0] if argv else DEFAULT_GAME, name, copy, radius, height)
    game = argv[0] if argv else DEFAULT_GAME
    paths = sorted(glob.glob(os.path.join(game, "Maps", "PC", "DataMap*_v09.dat")))
    if only:
        paths = [p for p in paths if os.path.basename(p) == f"DataMap{only}_v09.dat"]
    if not paths:
        print(f"no map packs found under {game}")
        return 2
    fails = 0
    for path in paths:
        name = os.path.basename(path)[7:-8]
        with Edat.open(path) as arc:
            try:
                problems, summary = check(reader(arc), name)
            except (ValueError, struct.error, zlib.error) as exc:
                problems, summary = [str(exc)], ""
        fails += bool(problems)
        print(f"{name:24s} {'OK' if not problems else 'FAIL: ' + '; '.join(problems[:3])}  {summary}", flush=True)
    print(f"\n{len(paths)} maps, {fails} failures")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
