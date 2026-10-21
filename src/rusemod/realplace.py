"""A real place made a map (the owner, 2026-10-18: "Take a real place. And put it in the game"; MOD_FORMAT §8, a new
map's relief): its ground from open elevation tiles, its land from OpenStreetMap, laid on a blank map of its size.

What comes in, and how it is laid (the ways the build already has, each seen in the game):
  - the ground: the elevation tiles (Terrarium PNGs: height = R x 256 + G + B / 256 - 32768 metres) sampled over the
    map's square into the relief's heightmap (rusemod.relief, `brush = "relief"`), the sea's floor sloped down from
    the shore (the tiles hold the sea at 0 m) and each river's bed cut below its banks;
  - the water: the sea a water stroke over the whole map at SEA metres, each river a run of water strokes along it at
    its banks' height less RIVER_DROP;
  - the land's look: every area OpenStreetMap draws (a field, a meadow, a wood, a marsh, sand, a village, rock, a
    pond) and, where it draws none, the land cut into fields FIELD metres or so across (the bocage's fields, as the
    game's own Normandy has them), each laid with one of D-Day's own ground swatches (rusemod.groundtex.palette:
    wheat, ploughed, green crop with their rows turned along the field, the grasses, forest floor, sand, mud, rock):
    one texture stroke an area, painting only within it (`within`: the relief's area picture, rusemod.relief), over
    the relief's picture (each area in its swatch's mean colour: what the Studio's view and the far ground show).

Coordinates: metres east (x) and south (y) of the place's reference point, as a map's world x and y run (x east, y
south); a map unit is 1 / M metre. A degree of latitude is EARTH metres, of longitude EARTH x cos(the reference's
latitude): flat over a map's few kilometres (the shape off by under 0.1% at 10 km).

The data's licences go with the map: OpenStreetMap's data is (c) OpenStreetMap contributors (ODbL), the elevation
tiles are open data (Terrain Tiles: SRTM and others). credit_toml writes both beside the heightmap.

numpy only (rusemod.numpy2); the import runs once (in the Studio) and writes files, which the build reads as any
relief's."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

M = 260.0                 # map units a metre
EARTH = 111320.0          # metres a degree of latitude
SEA = 0.5                 # metres: the sea's surface (the tiles' sea is 0)
SEA_FLOOR = -3.0          # metres: the sea's floor away from the shore
SHORE = 60.0              # metres: the floor slopes from the shore down to SEA_FLOOR over this
RIVER_DROP = 1.2          # metres: a river's water under its banks
RIVER_DEPTH = 2.5         # metres: its bed under its banks
RIVER_WIDTH = {"river": 24.0, "canal": 16.0}   # metres, when the data gives none; streams and ditches aren't cut
WATER_STEP = 30.0         # metres between a river's water strokes
FIELD = 180.0             # metres: about how far across the fields cut where the data draws none
HEIGHT_STEP = 5.0         # metres between the heightmap's samples
AREA_CELL = 2.0           # metres an area picture's pixel is across
PICTURE_CELL = 4.0        # metres the relief's picture's pixel is across
THEME = "dday"            # the palette the land is laid with (groundtex.palette)
CREDIT = {"osm": "(c) OpenStreetMap contributors, ODbL (openstreetmap.org/copyright)",
          "elevation": "Terrain Tiles (open data on AWS: SRTM, GMTED, ETOPO1 and others)"}


class PlaceError(ValueError):
    pass


@dataclass(frozen=True)
class Frame:
    """The map's square over the place: the reference point (lat, lon), and the square's first (north-west) corner
    `x0`, `y0` metres from it and its side, `side` metres."""
    lat: float
    lon: float
    x0: float
    y0: float
    side: float

    @property
    def per_lon(self) -> float:
        return EARTH * math.cos(math.radians(self.lat))

    def metres(self, lat, lon):
        """(x east, y south) metres from the reference (numbers or numpy arrays)."""
        return (lon - self.lon) * self.per_lon, (self.lat - lat) * EARTH

    def lonlat(self, x, y):
        return self.lon + x / self.per_lon, self.lat - y / EARTH

    def world(self, x, y):
        """Map units on the new map (its corner at 0, 0)."""
        return (x - self.x0) * M, (y - self.y0) * M

    def bbox(self, margin: float = 0.0) -> tuple[float, float, float, float]:
        """(south, west, north, east) degrees round the square (and `margin` metres more): what to download."""
        w, n = self.lonlat(self.x0 - margin, self.y0 - margin)
        e, s = self.lonlat(self.x0 + self.side + margin, self.y0 + self.side + margin)
        return s, w, n, e


# --- the ground ------------------------------------------------------------------------------------------------------
def tiles_needed(frame: Frame, zoom: int, margin: float = 100.0) -> list[tuple[int, int]]:
    """The (x, y) of every Terrarium tile at `zoom` over the square (and `margin` metres round it)."""
    s, w, n, e = frame.bbox(margin)
    (x0, y0), (x1, y1) = tile_of(n, w, zoom), tile_of(s, e, zoom)
    return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]


def tile_of(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    n = 2 ** zoom
    return int((lon + 180.0) / 360.0 * n), int((1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n)


def terrarium(png: bytes):
    """A Terrarium tile's heights, metres, as a [row, column] float array (rows from its north)."""
    from .numpy2 import np
    from .png import read_png
    w, h, px = read_png(png)
    a = np.frombuffer(px, dtype=np.uint8).reshape(h, w, 4).astype(np.float64)
    return a[..., 0] * 256.0 + a[..., 1] + a[..., 2] / 256.0 - 32768.0


def ground_heights(frame: Frame, tiles: dict, zoom: int, step: float = HEIGHT_STEP):
    """The heights (metres) over the square every `step` metres, sample (row, column) at the middle of its square, row
    0 the north side: the tiles ({(x, y): PNG bytes}) put together and read between their pixels (bilinear)."""
    from .numpy2 import np
    xs = sorted({x for x, _y in tiles})
    ys = sorted({y for _x, y in tiles})
    whole = np.zeros((len(ys) * 256, len(xs) * 256))
    for (tx, ty), data in tiles.items():
        whole[(ty - ys[0]) * 256:(ty - ys[0] + 1) * 256, (tx - xs[0]) * 256:(tx - xs[0] + 1) * 256] = terrarium(data)
    if any((x, y) not in tiles for x in range(xs[0], xs[-1] + 1) for y in range(ys[0], ys[-1] + 1)):
        raise PlaceError("the elevation tiles don't make one whole square: one or more are missing")
    n = int(round(frame.side / step))
    mid = (np.arange(n) + 0.5) * step
    lon, _ = frame.lonlat(frame.x0 + mid, 0.0)
    _, lat = frame.lonlat(0.0, frame.y0 + mid)
    k = 2 ** zoom
    px = ((lon + 180.0) / 360.0 * k - xs[0]) * 256.0 - 0.5
    py = ((1.0 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2.0 * k - ys[0]) * 256.0 - 0.5
    if px.min() < 0 or py.min() < 0 or px.max() > whole.shape[1] - 1 or py.max() > whole.shape[0] - 1:
        raise PlaceError("the elevation tiles don't cover the whole square")
    i, j = np.floor(px).astype(np.int64), np.floor(py).astype(np.int64)
    tx, ty = px - i, py - j
    i1, j1 = np.minimum(i + 1, whole.shape[1] - 1), np.minimum(j + 1, whole.shape[0] - 1)
    top = whole[j][:, i] * (1 - tx) + whole[j][:, i1] * tx
    bottom = whole[j1][:, i] * (1 - tx) + whole[j1][:, i1] * tx
    return top * (1 - ty)[:, None] + bottom * ty[:, None]


def resample(a, n: int):
    """A square [row, column] grid read at an n x n grid's sample middles over the same square (bilinear; the edge's
    samples held past it)."""
    from .numpy2 import np
    k = a.shape[0]
    f = np.clip((np.arange(n) + 0.5) * k / n - 0.5, 0.0, k - 1.0)
    i = np.minimum(f.astype(np.int64), k - 2)
    t = f - i
    rows = a[i] * (1 - t)[:, None] + a[i + 1] * t[:, None]
    return rows[:, i] * (1 - t)[None, :] + rows[:, i + 1] * t[None, :]


def box_blur(a, r: int):
    """`a` averaged over the (2r + 1)-sample square round each sample (the edge's samples held past it)."""
    from .numpy2 import np
    if r <= 0:
        return a.copy()
    p = np.pad(a, r, mode="edge")
    c = np.cumsum(np.cumsum(p, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)))
    w = 2 * r + 1
    return (c[w:, w:] - c[:-w, w:] - c[w:, :-w] + c[:-w, :-w]) / (w * w)


def shape_sea(h, step: float = HEIGHT_STEP):
    """The heights with the sea's floor made: the tiles hold the sea at 0 m exactly (and nothing under it); there the
    floor goes from the shore's height down to SEA_FLOOR over SHORE metres. Returns (heights, sea mask)."""
    from .numpy2 import np
    sea = h <= 0.0
    if not sea.any():
        return h, sea
    land = box_blur((~sea).astype(np.float64), max(1, int(round(SHORE / step))))
    floor = SEA_FLOOR + (SEA - 0.3 - SEA_FLOOR) * np.clip(land * 2.0, 0.0, 1.0)
    out = np.where(sea, floor, h)
    return out, sea


# --- OpenStreetMap -------------------------------------------------------------------------------------------------
# an area's kind from its tags: (tag, values, kind); the first that matches
AREA_TAGS = [
    ("natural", ("bare_rock", "rock", "scree", "cliff", "stone"), "rock"),
    ("natural", ("water",), "water"), ("waterway", ("riverbank",), "water"), ("landuse", ("basin", "reservoir"), "water"),
    ("wetland", ("tidalflat",), "mud"),
    ("natural", ("sand", "beach", "dune", "shingle"), "sand"),
    ("natural", ("wetland",), "marsh"),
    ("natural", ("wood",), "wood"), ("landuse", ("forest",), "wood"),
    ("natural", ("scrub", "heath", "shrubbery"), "scrub"),
    ("landuse", ("farmland",), "field"),
    ("landuse", ("orchard", "vineyard", "plant_nursery"), "orchard"),
    ("landuse", ("meadow", "grass", "village_green", "recreation_ground", "greenfield"), "meadow"),
    ("natural", ("grassland",), "meadow"),
    ("leisure", ("park", "garden", "pitch", "golf_course", "playground"), "meadow"),
    ("landuse", ("residential", "farmyard", "industrial", "commercial", "retail", "construction", "cemetery",
                 "allotments", "railway", "garages", "religious", "brownfield"), "town"),
]
# the order areas are laid in, under to over: what the data draws inside another (a pond in a field) wins
LAYERS = ("land", "field", "meadow", "orchard", "town", "scrub", "wood", "marsh", "sand", "mud", "water", "rock",
          "sea")
# each kind's swatches from the theme (one picked an area by its number, as `pick` does), and whether rows turn
SWATCHES = {"field": ("wheat", "ploughed", "green_crop"), "meadow": ("grass", "light_grass"),
            "orchard": ("dark_grass",), "town": ("earth", "light_grass"), "scrub": ("dark_grass",),
            "wood": ("forest_floor",), "marsh": ("dark_grass",), "sand": ("sand",), "mud": ("mud",),
            "water": ("mud",), "rock": ("rock",), "sea": ("mud",),
            "land": ("grass", "grass", "dark_grass", "light_grass", "green_crop", "wheat", "ploughed")}
ROWS = {"wheat", "ploughed", "green_crop"}


def area_kind(tags: dict) -> str | None:
    for key, values, kind in AREA_TAGS:
        if tags.get(key) in values:
            return kind
    return None


@dataclass
class Area:
    kind: str
    rings: list            # numpy [n, 2] arrays of (x, y) metres; inside = an odd number of rings round it
    tags: dict = field(default_factory=dict)


@dataclass
class Line:
    kind: str              # the highway's, waterway's or barrier's value
    what: str              # "highway", "waterway", "barrier", "natural" (a tree row), "railway"
    points: object         # numpy [n, 2] (x, y) metres
    tags: dict = field(default_factory=dict)


def osm_features(doc: dict, frame: Frame) -> tuple[list[Area], list[Line]]:
    """The areas and lines of an Overpass answer (`out geom`: each way's points, each relation's members' points) in
    the frame's metres. A closed way with an area's tags is an area; a multipolygon or boundary relation's rings are
    one area (outer and inner alike: inside is inside an odd number of them)."""
    from .numpy2 import np
    areas, lines = [], []

    def pts(geom):
        lat = np.array([p["lat"] for p in geom])
        lon = np.array([p["lon"] for p in geom])
        x, y = frame.metres(lat, lon)
        return np.stack([x, y], axis=1)
    for el in doc.get("elements", []):
        tags = el.get("tags", {})
        if el.get("type") == "way" and el.get("geometry"):
            p = pts(el["geometry"])
            kind = area_kind(tags)
            closed = len(p) >= 4 and np.allclose(p[0], p[-1])
            if kind and closed and tags.get("area") != "no":
                areas.append(Area(kind, [p], tags))
                continue
            for what in ("highway", "waterway", "barrier", "railway"):
                if what in tags:
                    lines.append(Line(tags[what], what, p, tags))
                    break
            else:
                if tags.get("natural") == "tree_row":
                    lines.append(Line("tree_row", "natural", p, tags))
        elif el.get("type") == "relation" and tags.get("type") in ("multipolygon", "boundary"):
            kind = area_kind(tags)
            if not kind:
                continue
            rings = [pts(m["geometry"]) for m in el.get("members", []) if m.get("type") == "way" and m.get("geometry")]
            rings = _joined(rings)
            if rings:
                areas.append(Area(kind, rings, tags))
    return areas, lines


def _joined(parts: list) -> list:
    """A relation's member ways joined end to end into closed rings (the open ones left, closed, as they come)."""
    from .numpy2 import np
    rings, open_ = [], []
    for p in parts:
        (rings if len(p) >= 4 and np.allclose(p[0], p[-1]) else open_).append(p)
    while open_:
        cur = open_.pop(0)
        grew = True
        while grew and not np.allclose(cur[0], cur[-1]):
            grew = False
            for k, q in enumerate(open_):
                if np.allclose(cur[-1], q[0]):
                    cur = np.concatenate([cur, q[1:]])
                elif np.allclose(cur[-1], q[-1]):
                    cur = np.concatenate([cur, q[::-1][1:]])
                elif np.allclose(cur[0], q[-1]):
                    cur = np.concatenate([q, cur[1:]])
                elif np.allclose(cur[0], q[0]):
                    cur = np.concatenate([q[::-1], cur[1:]])
                else:
                    continue
                open_.pop(k)
                grew = True
                break
        rings.append(cur if np.allclose(cur[0], cur[-1]) else np.concatenate([cur, cur[:1]]))
    return [r for r in rings if len(r) >= 4]


def fill(rings: list, x0: float, y0: float, cell: float, cols: int, rows: int):
    """Which cells (their middles) of a grid (`cols` x `rows`, `cell` metres, its first corner at x0, y0; row 0 at y0)
    lie inside the rings (an odd number of them round it), as a [row, column] bool array, and the rows and columns
    it spans: (mask over the box, row from, column from). None when it covers no cell."""
    from .numpy2 import np
    allp = np.concatenate(rings)
    c0 = max(0, int(math.floor((allp[:, 0].min() - x0) / cell)))
    c1 = min(cols, int(math.ceil((allp[:, 0].max() - x0) / cell)))
    r0 = max(0, int(math.floor((allp[:, 1].min() - y0) / cell)))
    r1 = min(rows, int(math.ceil((allp[:, 1].max() - y0) / cell)))
    if c0 >= c1 or r0 >= r1:
        return None
    ax = np.concatenate([r[:-1, 0] for r in rings])
    ay = np.concatenate([r[:-1, 1] for r in rings])
    bx = np.concatenate([r[1:, 0] for r in rings])
    by = np.concatenate([r[1:, 1] for r in rings])
    flat = ay != by
    ax, ay, bx, by = ax[flat], ay[flat], bx[flat], by[flat]
    mask = np.zeros((r1 - r0, c1 - c0), dtype=bool)
    for start in range(r0, r1, 256):   # rows by the batch: crossings [rows, edges]
        stop = min(r1, start + 256)
        yy = (y0 + (np.arange(start, stop) + 0.5) * cell)[:, None]
        hit = (ay[None, :] <= yy) != (by[None, :] <= yy)   # (an edge's lower end in, its upper end out)
        with np.errstate(divide="ignore", invalid="ignore"):
            cx = ax[None, :] + (yy - ay[None, :]) * (bx - ax)[None, :] / (by - ay)[None, :]
        cx = np.where(hit, cx, np.inf)
        cx.sort(axis=1)
        # inside between the 1st and 2nd crossing, the 3rd and 4th, ...: the cells whose middles lie between
        for row in range(stop - start):
            xs_ = cx[row][np.isfinite(cx[row])]
            starts = np.ceil((xs_[0::2] - x0) / cell - 0.5).astype(np.int64)
            ends = np.ceil((xs_[1::2] - x0) / cell - 0.5).astype(np.int64)
            for a, b in zip(starts, ends):
                a, b = max(int(a), c0), min(int(b), c1)
                if a < b:
                    mask[start - r0 + row, a - c0:b - c0] = True
    return mask, r0, c0


def stretch_way(rings: list) -> float:
    """The way an area is longest (degrees from +x toward +y, 0..180): its edges' own ways averaged by their lengths
    (doubled angles, so a way and its reverse agree): a field's rows run along it."""
    sx = sy = 0.0
    for r in rings:
        d = r[1:] - r[:-1]
        length = (d[:, 0] ** 2 + d[:, 1] ** 2) ** 0.5
        ang = [math.atan2(dy, dx) for dx, dy in d]
        sx += float(sum(length[k] * math.cos(2 * a) for k, a in enumerate(ang)))
        sy += float(sum(length[k] * math.sin(2 * a) for k, a in enumerate(ang)))
    return (math.degrees(math.atan2(sy, sx) / 2.0)) % 180.0


def pick(options: tuple, k: int) -> str:
    """One of `options` for area number k, the same every time (a whole-number hash)."""
    h = (k * 2654435761 + 97) % 4294967296
    h = (h ^ (h >> 13)) * 1274126177 % 4294967296
    return options[h % len(options)]


# --- the plan: the areas laid, the strokes ------------------------------------------------------------------------
@dataclass
class AreaPlan:
    number: int            # its number in the area picture (1..65535)
    kind: str
    swatch: str            # the palette swatch's name (groundtex.palette: "swatch:<theme>:<name>")
    turn: float            # degrees: a field's rows run this way (0 for the rest)
    box: tuple             # x min, x max, y min, y max, metres
    cells: int             # how many of the picture's cells it holds


@dataclass
class Place:
    frame: Frame
    heights: object        # [row, column] metres every HEIGHT_STEP, row 0 north
    sea: object            # [row, column] bool: under the sea, every AREA_CELL, row 0 north
    areas: object          # [row, column] uint16 every AREA_CELL, row 0 north
    plans: list            # AreaPlan for each number in `areas`
    rivers: list           # Line: the rivers cut and filled
    lines: list            # every Line (roads, streams, hedges...)
    notes: list = field(default_factory=list)


def make_place(frame: Frame, tiles: dict, zoom: int, doc: dict) -> Place:
    """The place over `frame` from its elevation tiles ({(x, y): PNG}, at `zoom`) and its OpenStreetMap data (`doc`, an
    Overpass answer with each element's points): the ground shaped (the sea's floor, the rivers' beds), every area
    laid in the area picture under a number of its own, and the land the data leaves bare cut into fields."""
    from .numpy2 import np
    h = ground_heights(frame, tiles, zoom)
    h, sea = shape_sea(h)
    areas_, lines = osm_features(doc, frame)
    rivers = [ln for ln in lines if ln.what == "waterway" and ln.kind in RIVER_WIDTH]
    cut = cut_rivers(h, rivers, frame)
    n = int(round(frame.side / AREA_CELL))
    grid = np.zeros((n, n), dtype=np.uint16)
    plans: list[AreaPlan] = []
    notes = []
    # what lies under water at each area cell (the heights read between their samples, so the shore runs smooth): the
    # sea's floor, a river's bed (laid last, over what the data draws)
    sea_cells = resample(cut, n) < SEA
    bed_cells = (resample(cut - h, n) < -0.5) & ~sea_cells
    h = cut
    # the land the data leaves bare: fields of about FIELD metres (rusemod's own cut, _fields), under the data's own
    land_cells, windows = _fields(frame, n)
    order = {kind: i for i, kind in enumerate(LAYERS)}
    drawn = []
    for a in areas_:
        got = fill(a.rings, frame.x0, frame.y0, AREA_CELL, n, n)
        if got is None:
            continue
        mask, r0, c0 = got
        if not mask.any():
            continue
        drawn.append((order[a.kind], -int(mask.sum()), a, mask, r0, c0))
    drawn.sort(key=lambda d: (d[0], d[1]))   # by layer, and in a layer the biggest first (the smaller over it)
    number = 0

    def add(kind, mask, r0, c0, rings=None, salt=0):
        nonlocal number
        number += 1
        if number > 65535:
            raise PlaceError("the place has more than 65,535 areas: take a smaller square")
        sw = pick(SWATCHES[kind], number * 31 + salt)
        sub = grid[r0:r0 + mask.shape[0], c0:c0 + mask.shape[1]]
        sub[mask] = number
        turn = 0.0
        if sw in ROWS:
            turn = stretch_way(rings) if rings else float(pick(tuple(range(0, 180, 15)), number))
        rr, cc = np.nonzero(mask)
        box = (frame.x0 + (c0 + cc.min()) * AREA_CELL, frame.x0 + (c0 + cc.max() + 1) * AREA_CELL,
               frame.y0 + (r0 + rr.min()) * AREA_CELL, frame.y0 + (r0 + rr.max() + 1) * AREA_CELL)
        plans.append(AreaPlan(number, kind, sw, turn, box, int(mask.sum())))
    # the bare land's fields under all
    for f, (r0, r1, c0, c1) in enumerate(windows, start=1):
        mask = land_cells[r0:r1, c0:c1] == f
        if mask.any():
            rr, cc = np.nonzero(mask)
            add("land", mask[rr.min():rr.max() + 1, cc.min():cc.max() + 1], r0 + int(rr.min()), c0 + int(cc.min()),
                salt=f)
    for _layer, _size, a, mask, r0, c0 in drawn:
        add(a.kind, mask, r0, c0, a.rings)
    if bed_cells.any():
        add("water", bed_cells, 0, 0)
    if sea_cells.any():
        add("sea", sea_cells, 0, 0)
    # keep only the areas still showing (one drawn over whole is gone)
    seen = np.bincount(grid.ravel(), minlength=number + 1)
    kept = [p for p in plans if seen[p.number] > 0]
    for p in kept:
        p.cells = int(seen[p.number])
    notes.append(f"{len(areas_)} area(s) and {len(lines)} line(s) in the data; {len(kept)} area(s) laid "
                 f"({sum(1 for p in kept if p.kind == 'land')} of them fields where the data draws none); "
                 f"{len(rivers)} river line(s)")
    return Place(frame, h, sea_cells, grid, kept, rivers, lines, notes)


def _fields(frame: Frame, n: int):
    """The square cut into fields about FIELD metres across: (each AREA_CELL cell's field number, 1 up; for each field
    the rows and columns it can reach, (row from, row to, column from, column to)). A field is the cells nearest one
    of points laid a FIELD apart, each nudged by up to a third of that (pick's hash: the same every time)."""
    from .numpy2 import np
    k = max(1, int(round(frame.side / FIELD)))
    step = frame.side / k
    nudge = tuple(range(-30, 31))
    pts = []
    for j in range(-1, k + 1):
        for i in range(-1, k + 1):
            q = (j + 2) * 4099 + (i + 2)
            pts.append(((i + 0.5) * step + pick(nudge, q) / 90.0 * step,
                        (j + 0.5) * step + pick(nudge, q * 7 + 3) / 90.0 * step))
    mid = (np.arange(n) + 0.5) * AREA_CELL
    out = np.zeros((n, n), dtype=np.int32)
    best = np.full((n, n), np.inf)
    windows = []
    for f, (px, py) in enumerate(pts, start=1):
        # only cells within a step and a half can be nearest to it (its neighbours are a step off, nudged a third)
        c0, c1 = (int(v) for v in np.searchsorted(mid, (px - 1.5 * step, px + 1.5 * step)))
        r0, r1 = (int(v) for v in np.searchsorted(mid, (py - 1.5 * step, py + 1.5 * step)))
        windows.append((r0, r1, c0, c1))
        if c0 >= c1 or r0 >= r1:
            continue
        d = (mid[c0:c1][None, :] - px) ** 2 + (mid[r0:r1][:, None] - py) ** 2
        sub_best = best[r0:r1, c0:c1]
        closer = d < sub_best
        sub_best[closer] = d[closer]
        out[r0:r1, c0:c1][closer] = f
    return out, windows


def cut_rivers(h, rivers: list, frame: Frame, step: float = HEIGHT_STEP):
    """The heights with each river's bed cut: RIVER_DEPTH under its banks' height (the ground beside it, the lowest
    of the two sides' median), RIVER_WIDTH wide (or its own width tag), the sides sloping back over its width."""
    from .numpy2 import np
    out = h.copy()
    n = h.shape[0]
    mid = (np.arange(n) + 0.5) * step
    for ln in rivers:
        width = _width(ln)
        bank = river_banks(h, ln, frame, step)
        p = ln.points - (frame.x0, frame.y0)
        for k in range(len(p) - 1):
            (ax, ay), (bx, by) = p[k], p[k + 1]
            reach = width * 1.5
            c0, c1 = np.searchsorted(mid, min(ax, bx) - reach), np.searchsorted(mid, max(ax, bx) + reach)
            r0, r1 = np.searchsorted(mid, min(ay, by) - reach), np.searchsorted(mid, max(ay, by) + reach)
            if c0 >= c1 or r0 >= r1:
                continue
            gx, gy = mid[c0:c1][None, :], mid[r0:r1][:, None]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy or 1.0
            t = np.clip(((gx - ax) * dx + (gy - ay) * dy) / L2, 0.0, 1.0)
            d = np.hypot(gx - (ax + t * dx), gy - (ay + t * dy))
            bed = bank[k] - RIVER_DEPTH
            w = np.clip((d - width / 2) / (width / 2), 0.0, 1.0)
            want = bed + (out[r0:r1, c0:c1] - bed) * (w * w * (3 - 2 * w))
            out[r0:r1, c0:c1] = np.minimum(out[r0:r1, c0:c1], want)
    return out


def _width(ln: Line) -> float:
    try:
        return max(4.0, float(str(ln.tags.get("width", "")).split()[0]))
    except (ValueError, IndexError):
        return RIVER_WIDTH.get(ln.kind, 10.0)


def river_banks(h, ln: Line, frame: Frame, step: float = HEIGHT_STEP) -> list[float]:
    """A river's banks' height at each of its points (metres): the ground a width and a half off its line on either
    side, the lower of the two, never rising downstream (the water runs down)."""
    from .numpy2 import np
    n = h.shape[0]
    width = _width(ln)
    p = ln.points - (frame.x0, frame.y0)
    out = []
    for k in range(len(p)):
        a, b = p[max(0, k - 1)], p[min(len(p) - 1, k + 1)]
        d = b - a
        L = float(np.hypot(d[0], d[1])) or 1.0
        nx, ny = -d[1] / L, d[0] / L
        sides = []
        for s in (1.0, -1.0):
            x, y = p[k][0] + s * nx * width * 1.5, p[k][1] + s * ny * width * 1.5
            i, j = int(x / step), int(y / step)
            if 0 <= i < n and 0 <= j < n:
                sides.append(float(h[j, i]))
        out.append(min(sides) if sides else 0.0)
    for k in range(1, len(out)):     # never higher than upstream: OpenStreetMap draws a river downstream
        out[k] = min(out[k], out[k - 1])
    return out


# --- the files ------------------------------------------------------------------------------------------------------
def heightmap(place: Place) -> tuple[bytes, float, float]:
    """(the relief's heightmap PNG, its lowest and highest metres): 16-bit, rows from the south (the relief's top row
    is its high y side)."""
    from .numpy2 import np
    from .png import grey16_bytes
    h = place.heights
    lo, hi = float(h.min()), float(h.max())
    span = (hi - lo) or 1.0
    q = np.round((h - lo) / span * 65535.0).astype(">u2")[::-1]
    return grey16_bytes(q.shape[1], q.shape[0], np.ascontiguousarray(q).tobytes()), lo, hi


def area_picture(place: Place) -> bytes:
    """The relief's area picture (relief.areas_file): 16-bit, rows from the south."""
    from .numpy2 import np
    from .png import grey16_bytes
    a = np.ascontiguousarray(place.areas.astype(">u2")[::-1])
    return grey16_bytes(a.shape[1], a.shape[0], a.tobytes())


def ground_picture(place: Place, colour_of) -> tuple[int, int, bytes]:
    """The relief's picture (relief.files_of's <name>-ground.png): each area in its swatch's mean colour
    (`colour_of(swatch name)` -> (r, g, b)), every PICTURE_CELL metres, rows from the south. (width, height, RGB)."""
    from .numpy2 import np
    k = int(round(PICTURE_CELL / AREA_CELL))
    a = place.areas[k // 2::k, k // 2::k]
    table = np.zeros((int(place.areas.max()) + 1, 3), dtype=np.uint8)
    for p in place.plans:
        table[p.number] = colour_of(p.swatch)
    rgb = np.ascontiguousarray(table[a][::-1])
    return rgb.shape[1], rgb.shape[0], rgb.tobytes()


def strokes(place: Place, name: str, base: float, theme: str = THEME) -> list:
    """The map's strokes after its blank start's: the relief (its square the whole map, `base` the z of its lowest
    point), the sea and the rivers' water, and a texture stroke within each area."""
    from .brush import Stroke
    f = place.frame
    lo, hi = float(place.heights.min()), float(place.heights.max())
    half = f.side / 2 * M
    mid = f.side / 2 * M
    out = [Stroke("relief", mid, mid, half, level=base, level2=base + (hi - lo) * M, weight=1.0, shape="square",
                  edge="hard", relief=name)]

    def z(metres: float) -> float:
        return base + (metres - lo) * M
    if place.sea.any():
        out.append(Stroke("water", mid, mid, half * 1.02, level=z(SEA), shape="square", edge="hard"))
    for ln in place.rivers:
        bank = river_banks(place.heights, ln, f)
        width = _width(ln)
        p = ln.points
        for k in range(len(p) - 1):
            ax, ay = p[k]
            bx, by = p[k + 1]
            L = math.hypot(bx - ax, by - ay)
            steps = max(1, math.ceil(L / WATER_STEP - 1e-6))   # never more than WATER_STEP apart
            for s in range(steps):
                t = (s + 0.5) / steps
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                if not (f.x0 < x < f.x0 + f.side and f.y0 < y < f.y0 + f.side):
                    continue
                wx, wy = f.world(x, y)
                level = bank[k] + (bank[k + 1] - bank[k]) * t - RIVER_DROP
                out.append(Stroke("water", wx, wy, width * 0.75 * M, level=z(level)))
    for p in sorted(place.plans, key=lambda p: (LAYERS.index(p.kind), p.number)):
        x0, x1, y0, y1 = p.box
        (wx0, wy0), (wx1, wy1) = f.world(x0, y0), f.world(x1, y1)
        out.append(Stroke("texture", (wx0 + wx1) / 2, (wy0 + wy1) / 2, max(wx1 - wx0, wy1 - wy0) / 2 + 2 * M,
                          shape="square", edge="hard", texture=f"swatch:{theme}:{p.swatch}", turn=p.turn,
                          clear=False, within=f"{name}:{p.number}"))
    return out


def credit_toml(place: Place, title: str) -> str:
    """What the map is made from, and the data's licences, kept beside its heightmap."""
    f = place.frame
    s, w, n, e = f.bbox()
    return (f"# {title}: a real place made a map (rusemod.realplace). Keep this with the map: OpenStreetMap's licence "
            f"asks that its data be credited.\n"
            f'place = "{title}"\n'
            f"south = {s:.6f}\nwest = {w:.6f}\nnorth = {n:.6f}\neast = {e:.6f}\n"
            f'osm = "{CREDIT["osm"]}"\n'
            f'elevation = "{CREDIT["elevation"]}"\n')
