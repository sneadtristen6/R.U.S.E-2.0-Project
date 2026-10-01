"""A game screenshot turned into numbers, and our data drawn over it (read-only).

R.U.S.E. saves, next to each screenshot it takes (Documents\\EugenSystems\\RUSE\\Screenshots\\Scene_*.png), an .ini
with the exact camera: its position, the way it looks, its field of view and aspect, the map and the game's version.
So a screenshot can be read without looking at it: where the camera is on the map, the ground point in the middle
of the picture, which roads and bridges are in view and how far away; and an SVG with the screenshot underneath and
lines on top, put exactly where the game drew those things:

- the map's own roads (thin white) and, from a modded copy, the road sticker pieces it added (yellow);
- the new roads of a mod's roads.toml (cyan, dashed), when a mod folder is given;
- bridge floors: the game's own (thin blue outline) and the ones a modded copy added (magenta).

    py -3 tools/shot_overlay.py <Scene_...png> --map M04_cotentin [--copy D:\\RUSE-Instances\\bridges]
                                [--mod <mod folder>] [--out <folder>]

Writes <out>/<the screenshot's name>.svg (open it in a browser; the screenshot is copied next to it) and prints the
summary. If the lines sit beside the game's own roads and bridges instead of on them, the projection is wrong, not
the data: --flip mirrors left and right (see `project`)."""
from __future__ import annotations

import argparse
import math
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rusemod import floors as F  # noqa: E402
from rusemod import kdt as K  # noqa: E402
from rusemod.bridges import Ground  # noqa: E402
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.scenery import MEMBER, Scenery  # noqa: E402
from rusemod.steam import find_game  # noqa: E402
from rusemod.terrain import pack_file  # noqa: E402
from rusemod.tms import Tms  # noqa: E402

METRE = 260.0      # map units in a metre
REACH = 300000.0   # nothing farther from the camera than this is drawn (about 1.2 km)


def read_ini(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    section = None
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():  # (the game writes a BOM)
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            section = out.setdefault(line[1:-1], {})
        elif "=" in line and section is not None:
            k, v = line.split("=", 1)
            section[k.strip()] = v.strip()
    return out


def png_size(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path.name} isn't a PNG")
    return struct.unpack(">II", head[16:24])


class Camera:
    """The game's camera from a screenshot's .ini: position, direction (unit), up, vertical field of view, aspect."""

    def __init__(self, ini: dict, width: int, height: int, flip: bool = False):
        c = ini["Camera"]
        self.p = tuple(float(c[f"Position{a}"]) for a in "XYZ")
        d = tuple(float(c[f"Direction{a}"]) for a in "XYZ")
        n = math.sqrt(sum(v * v for v in d))
        self.d = tuple(v / n for v in d)
        up = tuple(float(c.get(f"Up{a}", "0")) for a in "XYZ")
        self.fov = float(c.get("FOV", "0.785398"))
        self.aspect = float(c.get("Aspect", str(width / height)))
        self.w, self.h = width, height
        r = _cross(self.d, up) if not flip else _cross(up, self.d)
        rn = math.sqrt(sum(v * v for v in r))
        self.r = tuple(v / rn for v in r)
        self.u = _cross(self.r, self.d) if not flip else _cross(self.d, self.r)
        self.near = float(c.get("FrontClipping", "100"))

    def project(self, x: float, y: float, z: float):
        """A map point (x, y, z) as a pixel (px, py) of the screenshot, or None behind the camera."""
        v = (x - self.p[0], y - self.p[1], z - self.p[2])
        fwd = _dot(v, self.d)
        if fwd <= self.near:
            return None
        t = math.tan(self.fov / 2)
        nx = _dot(v, self.r) / (fwd * t * self.aspect)
        ny = _dot(v, self.u) / (fwd * t)
        return (nx + 1) / 2 * self.w, (1 - ny) / 2 * self.h

    def ground_at_centre(self, height_at, step: float = 200.0, most: float = 2_000_000.0):
        """Where the ray through the middle of the picture meets the ground: (x, y, z, distance) or None."""
        s = 0.0
        while s < most:
            x, y, z = (self.p[a] + self.d[a] * s for a in range(3))
            g = height_at(x, y)
            if g is not None and z <= g:
                return x, y, g, s
            s += step if s < 50000 else step * 5
        return None


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _bezier(seg, n: int = 8):
    x0, y0, x1, y1, x2, y2, x3, y3 = seg
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3))
    return out


def _pack(game_or_copy: Path, name: str) -> Path | None:
    return find_pack(game_or_copy, name)


def _read(pack: Path, member: str) -> bytes:
    with Edat.open(str(pack)) as arc:
        return bytes(arc.read(arc.find(member)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("shot", type=Path)
    ap.add_argument("--map", required=True, help="the map's pack name, e.g. M04_cotentin or SuperCrossRoads4")
    ap.add_argument("--copy", type=Path, help="a modded copy (its packs give the new road pieces and floors)")
    ap.add_argument("--mod", type=Path, help="a mod folder (its maps/<map>/roads.toml lines are drawn)")
    ap.add_argument("--game", type=Path, help="the game folder (found through Steam by default)")
    ap.add_argument("--out", type=Path, default=Path.cwd() / "shot-overlays")
    ap.add_argument("--flip", action="store_true", help="mirror left and right (if the lines come out mirrored)")
    a = ap.parse_args(argv)

    ini_path = a.shot.with_suffix(".ini")
    if not ini_path.exists():
        print(f"no {ini_path.name} next to the screenshot: only the game's own screenshots (Scene_*.png) have one")
        return 2
    ini = read_ini(ini_path)
    w, h = png_size(a.shot)
    cam = Camera(ini, w, h, a.flip)
    game = a.game or (Path(find_game()["game_dir"]) if find_game() else None)
    if game is None:
        print("R.U.S.E. wasn't found: give --game")
        return 2
    gpack = _pack(game, pack_file(a.map))
    mesh = Tms(_read(gpack, "output\\highdef.tms"))
    ground = Ground(mesh)

    def gz(x, y):
        z = ground.height_at(x, y)
        return 0.0 if z is None else z

    def near(x, y):
        return math.hypot(x - cam.p[0], y - cam.p[1]) <= REACH

    layers = []  # (svg attributes, list of point lists in map units with z)

    def roads_of(pack):
        return Scenery(_read(pack, MEMBER)).roads()
    own = roads_of(gpack)
    own_keys = {tuple(round(v) for v in s[:2]) for s in own}
    layers.append(('stroke="white" stroke-width="1.5" stroke-opacity="0.7" fill="none"',
                   [[(x, y, gz(x, y)) for x, y in _bezier(s)] for s in own if near(s[0], s[1])]))
    new_pieces = []
    if a.copy:
        cpack = _pack(a.copy, pack_file(a.map))
        new_pieces = [s for s in roads_of(cpack) if tuple(round(v) for v in s[:2]) not in own_keys]
        layers.append(('stroke="yellow" stroke-width="3" fill="none"',
                       [[(x, y, gz(x, y)) for x, y in _bezier(s)] for s in new_pieces if near(s[0], s[1])]))
    if a.mod:
        import tomllib
        f = a.mod / "maps" / a.map / "roads.toml"
        if f.exists():
            data = tomllib.loads(f.read_text(encoding="utf-8"))
            lines = [[tuple(map(float, p)) for p in r.get("points", [])] for r in data.get("road", [])]
            layers.append(('stroke="cyan" stroke-width="2" stroke-dasharray="8 6" fill="none"',
                           [[(x, y, gz(x, y)) for x, y in ln] for ln in lines if ln]))
    shipped = F.triangles(K.Kdt(_read(gpack, F.MEMBER)))
    layers.append(('stroke="#4aa3ff" stroke-width="1" fill="none"',
                   [[*t, t[0]] for t in shipped if near(t[0][0], t[0][1])]))
    new_floor = []
    if a.copy:
        have = {tuple(round(v) for v in p) for t in shipped for p in t}
        new_floor = [t for t in F.triangles(K.Kdt(_read(cpack, F.MEMBER)))
                     if not all(tuple(round(v) for v in p) in have for p in t)]
        layers.append(('stroke="magenta" stroke-width="1.5" fill="magenta" fill-opacity="0.12"',
                       [[*t, t[0]] for t in new_floor if near(t[0][0], t[0][1])]))

    a.out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(a.shot, a.out / a.shot.name)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
             f'<image href="{a.shot.name}" width="{w}" height="{h}"/>']
    drawn = 0
    for attrs, polys in layers:
        for poly in polys:
            pts = [cam.project(*p) for p in poly]
            run = []
            for q in pts + [None]:
                if q is not None and -w < q[0] < 2 * w and -h < q[1] < 2 * h:
                    run.append(q)
                    continue
                if len(run) > 1:
                    parts.append(f'<polyline {attrs} points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in run) + '"/>')
                    drawn += 1
                run = []
    parts.append("</svg>")
    svg = a.out / (a.shot.stem + ".svg")
    svg.write_text("\n".join(parts), encoding="utf-8")

    centre = cam.ground_at_centre(ground.height_at)
    print(f"{a.shot.name}: map {a.map}, game version {ini.get('Version', {}).get('Version', '?')}, {w} x {h}")
    print(f"camera at ({cam.p[0]:.0f}, {cam.p[1]:.0f}), {cam.p[2] / METRE:.0f} m up; looking "
          f"{math.degrees(math.asin(-cam.d[2])):.0f} degrees down")
    if centre:
        print(f"the middle of the picture: ({centre[0]:.0f}, {centre[1]:.0f}) on the ground, "
              f"{centre[3] / METRE:.0f} m from the camera")
    if a.copy:
        def seen(x, y, z):
            q = cam.project(x, y, z)
            return q is not None and 0 <= q[0] <= w and 0 <= q[1] <= h
        in_view = [s for s in new_pieces if seen(s[0], s[1], gz(s[0], s[1]))]
        print(f"new road sticker pieces: {len(new_pieces)} in the copy, {len(in_view)} starting in the picture")
        floors_in = [t for t in new_floor if seen(*t[0])]
        print(f"new bridge floor triangles: {len(new_floor)} in the copy, {len(floors_in)} with a corner in the picture")
        if in_view:
            ds = sorted(math.dist(cam.p[:2], s[:2]) / METRE for s in in_view)
            print(f"  the nearest new road piece is {ds[0]:.0f} m from the camera, the farthest in view {ds[-1]:.0f} m")
    print(f"{drawn} line(s) drawn: {svg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
