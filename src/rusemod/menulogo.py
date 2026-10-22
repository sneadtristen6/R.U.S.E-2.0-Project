"""The main menu's logo as gold "R.U.S.E. 2.0" (the owner, 2026-10-22: "put 2.0 in there, but make sure it's ...
centered around both of them"; "It's one of our signatures"), made on the player's PC from the game's own menu
movie (interface_outgame.gfx), never shipped:

- "2." is the logo's S mirrored (top bar, the upright on the right, the middle bar, the upright on the left) above
  y = CUT, and below it the E's bottom band (its upright's foot, the bottom bar, the corner cut and the full stop's
  triangle) with the straight part of its bar stretched to the S's width; "0" is the U's bottom-left quarter (a
  rounded corner) mirrored into all four corners. They're made in every layer that draws letters (shape 649 the
  letters, 651 their mask, 657 the bevel, 658 its mask), so they have the logo's lettering, bevel, chrome, shadow and
  moving shine. R.U.S.E.'s own edges stay byte for byte; the new letters' edges are added after them.
- The chrome band (652) and the sheen (656) are widened to cover them, and the logo's place on the main menu
  (sprite 659 in sprite 660) moves left by half the added width, so the whole sits centred where R.U.S.E. was.
- Gold: a colour change (Flash's multiply per channel, GOLD) on every placement of the big logo and of the
  sub-menus' small logo picture (shape 387); the menu's code and animation stay the game's.

`letters()` gives a shape's letters as an area (for drawing them as a picture: rusemod.signature)."""
from __future__ import annotations

import struct

try:
    from shapely import affinity
    from shapely.geometry import MultiPolygon, Polygon, box
    from shapely.ops import unary_union
except ImportError:  # (the gold alone works without it; the letters need it: _need_shapely)
    affinity = MultiPolygon = Polygon = box = unary_union = None

GOLD = (1.0, 0.80, 0.40)  # the owner's pick, 2026-10-22 ("I like the gold"): red, green, blue multiplied
LOGOS = {659, 387}  # the big logo's sprite; the small logo's picture shape (placed inside sprite 388)
# the logo's letters, measured on shape 649, its own units (twips / 20)
S_BOX = (478.9, 703.2)   # the S, x
E_BOX = (722.2, 916.3)   # the E (and its full stop), x
U_BOX = (232.7, 463.7)   # the U, x
TOP, BOTTOM = 0.0, 180.1
CUT = 134.0              # where the S's top part meets the E's bottom band: inside the left upright, above both bars
MID_BAR_BOTTOM = 117.0   # just under the S's middle bar (73.5..115.3) and its bevel
UPRIGHT_KEEP = 70.0      # the left upright and its bevel (55 wide), kept below the middle bar
E_STRETCH = (800.0, 840.0)  # the straight run of the E's bottom bar that is stretched (no upright, no cut there)
U_MID = ((U_BOX[0] + U_BOX[1]) / 2, (TOP + BOTTOM) / 2)  # the U's centre
FRAME = {649: (0.0, 0.0), 651: (-429.45, -100.05), 657: (-429.45, -100.05), 658: (-429.45, -100.05)}
END_OF_RUSE = E_BOX[1]
WORD_GAP, LETTER_GAP = 55.0, 17.0  # R.U.S.E. to the 2, the 2 to the 0
PLACE_SCALE = 0.4  # the main menu shows the logo (sprite 659) at 0.4 of its size
STEPS = 10  # straight pieces per curve


class LogoError(ValueError):
    """The menu movie isn't the one the title was fitted to."""


def layout() -> dict:
    """Where the new letters go, in the logo's units: x_two, x_zero, right (the end of the 0), shift (the whole moved
    left so it's centred where R.U.S.E. was)."""
    x_two = END_OF_RUSE + WORD_GAP
    x_zero = x_two + (S_BOX[1] - S_BOX[0]) + LETTER_GAP
    right = x_zero + (U_BOX[1] - U_BOX[0])
    return {"x_two": x_two, "x_zero": x_zero, "right": right, "shift": (END_OF_RUSE - right) / 2}


# --- bits ---
class BitReader:
    def __init__(self, b, pos):
        self.b, self.pos, self.bit = b, pos, 0

    def ub(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | ((self.b[self.pos] >> (7 - self.bit)) & 1)
            self.bit += 1
            if self.bit == 8:
                self.bit, self.pos = 0, self.pos + 1
        return v

    def sb(self, n):
        v = self.ub(n)
        return v - (1 << n) if n and v & (1 << (n - 1)) else v

    def tell(self):
        return self.pos * 8 + self.bit

    def end(self):
        """The byte after the last bit read."""
        return self.pos + (1 if self.bit else 0)


class BitWriter:
    def __init__(self):
        self.bits = []

    def ub(self, v, n):
        self.bits += [(v >> (n - 1 - i)) & 1 for i in range(n)]

    def sb(self, v, n):
        self.ub(v & ((1 << n) - 1), n)

    def raw(self, bits):
        self.bits += bits

    def bytes(self):
        bits = self.bits + [0] * (-len(self.bits) % 8)
        return bytes(int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8))


def sbits(*vals):
    return max(max(abs(v).bit_length() + 1 for v in vals), 1)


def rect_bits(xmin, xmax, ymin, ymax) -> BitWriter:
    w = BitWriter()
    n = sbits(xmin, xmax, ymin, ymax)
    w.ub(n, 5)
    for v in (xmin, xmax, ymin, ymax):
        w.sb(v, n)
    return w


def skip_matrix(r: BitReader) -> None:
    if r.ub(1):
        r.ub(r.ub(5) * 2)
    if r.ub(1):
        r.ub(r.ub(5) * 2)
    r.ub(r.ub(5) * 2)


# --- tags ---
def tags_start(data: bytes) -> int:
    """Where an uncompressed movie's first tag starts."""
    if data[:3] != b"GFX":
        raise LogoError("the menu movie isn't an uncompressed Scaleform movie")
    nbits = data[8] >> 3
    return 8 + (5 + 4 * nbits + 7) // 8 + 4


def read_tags(b: bytes, pos: int, end: int) -> list:
    """[(tag, body, long header)] from pos to the End tag; the header's form is kept so an unchanged tag is written
    back byte for byte."""
    out = []
    while pos < end:
        cl = struct.unpack_from("<H", b, pos)[0]
        code, length = cl >> 6, cl & 0x3F
        head = 2
        if length == 0x3F:
            length = struct.unpack_from("<I", b, pos + 2)[0]
            head = 6
        out.append((code, b[pos + head:pos + head + length], head == 6))
        pos += head + length
        if code == 0:
            break
    return out


def tag_header(code: int, length: int, long_form: bool = False) -> bytes:
    if length < 0x3F and not long_form:
        return struct.pack("<H", (code << 6) | length)
    return struct.pack("<HI", (code << 6) | 0x3F, length)


def find_shape(data: bytes, shape_id: int) -> tuple[int, bytes]:
    """(tag, body) of a DefineShape by its id."""
    for code, body, _long in read_tags(data, tags_start(data), len(data)):
        if code in (2, 22, 32, 83) and struct.unpack_from("<H", body, 0)[0] == shape_id:
            return code, body
    raise LogoError(f"the menu movie has no shape {shape_id}")


# --- gold ---
def cxform(mult) -> bytes:
    """CXFORMWITHALPHA with multiply terms only (8.8 fixed point), alpha kept at 1."""
    vals = [round(m * 256) for m in mult] + [256]
    nbits = max(v.bit_length() for v in vals) + 1  # signed
    bits = "0" + "1" + format(nbits, "04b") + "".join(format(v & ((1 << nbits) - 1), f"0{nbits}b") for v in vals)
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def tinted_place(code: int, body: bytes, mult) -> bytes | None:
    """A PlaceObject2/3 body with the colour change set, or None when it doesn't place one of LOGOS."""
    flags = body[0]
    q = 1
    if code == 70:
        flags2 = body[q]
        q += 1
        if flags2 & 0x08:
            return None  # a class name: not the logo's placements
    q += 2  # depth
    if not flags & 0x02:
        return None
    cid = struct.unpack_from("<H", body, q)[0]
    if cid not in LOGOS:
        return None
    q += 2
    if flags & 0x08:
        raise LogoError(f"the placement of {cid} already has a colour change")
    if flags & 0x04:
        r = BitReader(body, q)
        skip_matrix(r)
        q = r.end()
    return bytes([flags | 0x08]) + body[1:q] + cxform(mult) + body[q:]


def tint(data: bytes, mult=GOLD) -> tuple[bytes, int]:
    """The movie with every placement of the logos coloured by `mult`; (movie, how many placements)."""
    start = tags_start(data)
    out = bytearray(data[:start])
    changed = 0
    for code, body, long_form in read_tags(data, start, len(data)):
        if code == 39:  # a sprite: its own tags, rebuilt with the logo's placements tinted
            inner = bytearray(body[:4])
            for c2, b2, long2 in read_tags(body, 4, len(body)):
                if c2 in (26, 70):
                    t = tinted_place(c2, b2, mult)
                    if t is not None:
                        b2, changed = t, changed + 1
                inner += tag_header(c2, len(b2), long2) + b2
            body = bytes(inner)
        elif code in (26, 70):
            t = tinted_place(code, body, mult)
            if t is not None:
                body, changed = t, changed + 1
        out += tag_header(code, len(body), long_form) + body
    struct.pack_into("<I", out, 4, len(out))
    return bytes(out), changed


# --- shapes ---
def read_shape(body: bytes, code: int) -> dict:
    """A DefineShape's header parts, its edges [(fill on the left, fill on the right, points)] in twips (curves as
    STEPS straight pieces), and where its end record starts (in bits)."""
    v = {2: 1, 22: 2, 32: 3, 83: 4}[code]
    sid = struct.unpack_from("<H", body, 0)[0]
    r = BitReader(body, 2)
    n = r.ub(5)
    bounds = [r.sb(n) for _ in range(4)]
    after_rect = r.end()
    p = after_rect
    if v == 4:
        r = BitReader(body, p)
        n = r.ub(5)
        [r.sb(n) for _ in range(4)]
        p = r.end() + 1
    p = _skip_fills(body, p, v)
    p = _skip_lines(body, p, v)
    r = BitReader(body, p)
    nf, nl = r.ub(4), r.ub(4)
    x = y = 0
    f0 = f1 = 0
    segs = []
    while True:
        here = r.tell()
        if r.ub(1) == 0:
            flags = r.ub(5)
            if flags == 0:
                end_bit = here
                break
            if flags & 1:
                k = r.ub(5)
                x, y = r.sb(k), r.sb(k)
            if flags & 2:
                f0 = r.ub(nf)
            if flags & 4:
                f1 = r.ub(nf)
            if flags & 8:
                r.ub(nl)
            if flags & 16:
                raise LogoError(f"shape {sid} has new styles inside it")
        else:
            if r.ub(1):
                k = r.ub(4) + 2
                if r.ub(1):
                    dx, dy = r.sb(k), r.sb(k)
                elif r.ub(1):
                    dx, dy = 0, r.sb(k)
                else:
                    dx, dy = r.sb(k), 0
                segs.append((f0, f1, [(x, y), (x + dx, y + dy)]))
                x, y = x + dx, y + dy
            else:
                k = r.ub(4) + 2
                cx, cy = x + r.sb(k), y + r.sb(k)
                ax, ay = cx + r.sb(k), cy + r.sb(k)
                pts = []
                for i in range(STEPS + 1):
                    t = i / STEPS
                    pts.append(((1 - t) ** 2 * x + 2 * (1 - t) * t * cx + t * t * ax,
                                (1 - t) ** 2 * y + 2 * (1 - t) * t * cy + t * t * ay))
                segs.append((f0, f1, pts))
                x, y = ax, ay
    return {"id": sid, "version": v, "bounds": bounds, "after_rect": after_rect, "records_byte": p, "nf": nf,
            "nl": nl, "segs": segs, "end_bit": end_bit}


def _skip_fills(b, p, v):
    n = b[p]
    p += 1
    if n == 0xFF:
        n = struct.unpack_from("<H", b, p)[0]
        p += 2
    for _ in range(n):
        kind = b[p]
        p += 1
        if kind == 0x00:
            p += 4 if v >= 3 else 3
        elif kind in (0x10, 0x12, 0x13):
            r = BitReader(b, p)
            skip_matrix(r)
            p = r.end()
            g = b[p]
            p += 1 + (g & 0x0F) * (1 + (4 if v >= 3 else 3))
            if kind == 0x13:
                p += 2
        elif kind in (0x40, 0x41, 0x42, 0x43):
            r = BitReader(b, p + 2)
            skip_matrix(r)
            p = r.end()
        else:
            raise LogoError(f"a fill of kind {kind:#x}")
    return p


def _skip_lines(b, p, v):
    n = b[p]
    p += 1
    if n == 0xFF:
        n = struct.unpack_from("<H", b, p)[0]
        p += 2
    if n and v == 4:
        raise LogoError("line styles of a DefineShape4")
    return p + n * (2 + (4 if v >= 3 else 3))


def areas(shape: dict) -> dict:
    """{fill style: its area}, in the shape's units: each style's edges (the style on an edge's right, as drawn; on
    its left, reversed) joined into rings, the rings combined even-odd."""
    chains: dict = {}
    for f0, f1, pts in shape["segs"]:
        if f1:
            chains.setdefault(f1, []).append(pts)
        if f0:
            chains.setdefault(f0, []).append(list(reversed(pts)))
    out = {}
    for style, parts in chains.items():
        starts: dict = {}
        for i, pts in enumerate(parts):
            starts.setdefault(_key(pts[0]), []).append(i)
        used = [False] * len(parts)
        rings = []
        for i in range(len(parts)):
            if used[i]:
                continue
            ring = list(parts[i])
            used[i] = True
            while True:
                nxt = next((j for j in starts.get(_key(ring[-1]), []) if not used[j]), None)
                if nxt is None:
                    break
                used[nxt] = True
                ring += parts[nxt][1:]
            if len(ring) > 3:
                rings.append(ring)
        geom = None
        for ring in rings:
            pg = Polygon([(x / 20, y / 20) for x, y in ring]).buffer(0)
            geom = pg if geom is None else geom.symmetric_difference(pg)
        if geom is not None and not geom.is_empty:
            out[style] = geom
    return out


def _key(pt):
    return (round(pt[0]), round(pt[1]))


def _need_shapely() -> None:
    if unary_union is None:
        raise ImportError("the letters are made with shapely, which isn't installed")


def letters(data: bytes, shape_id: int = 649):
    """The letters of a shape of the movie (every fill style), as one area in its units."""
    _need_shapely()
    code, body = find_shape(data, shape_id)
    return unary_union(list(areas(read_shape(body, code)).values()))


# --- the new letters, in 649's frame (dx, dy shift a layer's frame onto it) ---
def _clip(g, x0, y0, x1, y1):
    return g.intersection(box(x0, y0, x1, y1))


def letter_two(g, x_at: float):
    s_w = S_BOX[1] - S_BOX[0]
    top = _clip(g, S_BOX[0] - 2, TOP - 5, S_BOX[1] + 2, CUT)
    top = affinity.scale(top, xfact=-1, yfact=1, origin=((S_BOX[0] + S_BOX[1]) / 2, 0))
    # below its middle bar a "2" has only the upright on the left: the S's upturn at the end of its bottom bar
    # (mirrored to the right) is cut away
    top = top.difference(box(S_BOX[0] + UPRIGHT_KEEP, MID_BAR_BOTTOM, S_BOX[1] + 5, CUT + 1))
    top = affinity.translate(top, x_at - S_BOX[0])
    e_band = _clip(g, E_BOX[0] - 2, CUT, E_BOX[1] + 2, BOTTOM + 5)
    a, b = E_STRETCH
    left = _clip(e_band, E_BOX[0] - 2, CUT, a, BOTTOM + 5)
    mid = _clip(e_band, a, CUT, b, BOTTOM + 5)
    right = _clip(e_band, b, CUT, E_BOX[1] + 2, BOTTOM + 5)
    grow = s_w - (E_BOX[1] - E_BOX[0])
    mid = affinity.scale(mid, xfact=(b - a + grow) / (b - a), yfact=1, origin=(a, 0))
    right = affinity.translate(right, grow)
    band = affinity.translate(unary_union([left, mid, right]), x_at - E_BOX[0])
    return unary_union([top, band])


def letter_zero(g, x_at: float):
    cx, cy = U_MID
    q = _clip(g, U_BOX[0] - 2, cy, cx, BOTTOM + 5)
    lower = unary_union([q, affinity.scale(q, xfact=-1, yfact=1, origin=(cx, cy))])
    upper = affinity.scale(lower, xfact=1, yfact=-1, origin=(cx, cy))
    return affinity.translate(unary_union([lower, upper]), x_at - U_BOX[0])


def new_letters(style_areas: dict, frame, x_two: float, x_zero: float) -> dict:
    fx, fy = frame
    out = {}
    for style, g in style_areas.items():
        g649 = affinity.translate(g, -fx, -fy)
        parts = [letter_two(g649, x_two), letter_zero(g649, x_zero)]
        made = unary_union([p for p in parts if not p.is_empty])
        if not made.is_empty:
            out[style] = affinity.translate(made, fx, fy)
    return out


def area_records(new: dict, nf: int) -> list:
    """Shape records (bits) drawing each new area as rings with its style on the right of every edge."""
    bits = []
    for style, g in sorted(new.items()):
        polys = list(g.geoms) if isinstance(g, MultiPolygon) else [g] if isinstance(g, Polygon) else \
            [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]
        for pg in polys:
            if pg.is_empty or pg.area < 0.05:
                continue
            for ring in [pg.exterior, *pg.interiors]:
                pts = [(round(x * 20), round(y * 20)) for x, y in ring.coords]
                cleaned = [pts[0]]
                for q in pts[1:]:
                    if q != cleaned[-1]:
                        cleaned.append(q)
                if len(cleaned) < 4:
                    continue
                # the area on the right of the edges (y down): an outer ring clockwise on screen, a hole the other way
                if _signed_area(cleaned) * (1 if ring is pg.exterior else -1) < 0:
                    cleaned.reverse()
                w = BitWriter()
                x0, y0 = cleaned[0]
                k = sbits(x0, y0)
                w.ub(0, 1)
                w.ub(0b00111, 5)  # move, fill style 0, fill style 1
                w.ub(k, 5)
                w.sb(x0, k)
                w.sb(y0, k)
                w.ub(0, nf)        # nothing on the left
                w.ub(style, nf)    # the style on the right
                for (xa, ya), (xb, yb) in zip(cleaned, cleaned[1:]):
                    _edge(w, xb - xa, yb - ya)
                bits += w.bits
    return bits


def _edge(w: BitWriter, dx: int, dy: int) -> None:
    if dx == 0 and dy == 0:
        return
    k = max(sbits(dx, dy), 2)
    w.ub(1, 1)
    w.ub(1, 1)
    w.ub(k - 2, 4)
    if dx and dy:
        w.ub(1, 1)
        w.sb(dx, k)
        w.sb(dy, k)
    else:
        w.ub(0, 1)
        w.ub(1 if dx == 0 else 0, 1)
        w.sb(dy if dx == 0 else dx, k)


def _signed_area(pts):
    """Twice the signed area, positive when the ring runs clockwise on screen (y down)."""
    return sum(xa * yb - xb * ya for (xa, ya), (xb, yb) in zip(pts, pts[1:]))


def rebuild_shape(body: bytes, code: int, new: dict, extra_bounds) -> bytes:
    """The shape with its own records unchanged and `new`'s after them; its bounds grown to `extra_bounds`."""
    sh = read_shape(body, code)
    r = BitReader(body, sh["records_byte"])
    old_bits = [r.ub(1) for _ in range(sh["end_bit"] - sh["records_byte"] * 8)]
    w = BitWriter()
    w.raw(old_bits)  # NumFillBits, NumLineBits, then the shape's own records
    w.raw(area_records(new, sh["nf"]))
    w.ub(0, 6)  # the end record
    xmin, xmax, ymin, ymax = sh["bounds"]
    bx0, bx1, by0, by1 = extra_bounds
    xmin, xmax = min(xmin, round(bx0 * 20)), max(xmax, round(bx1 * 20))
    ymin, ymax = min(ymin, round(by0 * 20)), max(ymax, round(by1 * 20))
    head = struct.pack("<H", sh["id"]) + rect_bits(xmin, xmax, ymin, ymax).bytes()
    return head + body[sh["after_rect"]:sh["records_byte"]] + w.bytes()


def widen_rect_shape(body: bytes, code: int, grow: float) -> bytes:
    """A shape that is one rectangle (the chrome band, the sheen) made `grow` units wider to the right."""
    sh = read_shape(body, code)
    g = round(grow * 20)
    edges = sh["segs"]
    if len(edges) != 4:
        raise LogoError(f"shape {sh['id']} isn't one rectangle ({len(edges)} edges)")
    xmin, xmax, ymin, ymax = sh["bounds"]
    w = BitWriter()
    w.ub(sh["nf"], 4)
    w.ub(sh["nl"], 4)
    f0, f1, pts0 = edges[0]
    x0, y0 = pts0[0]
    shift = lambda x: x + g if x >= (xmin + xmax) / 2 else x  # noqa: E731  points on the right side move right
    k = sbits(shift(x0), y0)
    w.ub(0, 1)
    w.ub(0b00111, 5)
    w.ub(k, 5)
    w.sb(shift(x0), k)
    w.sb(y0, k)
    w.ub(f0, sh["nf"])
    w.ub(f1, sh["nf"])
    for _f0, _f1, pts in edges:
        (xa, ya), (xb, yb) = pts[0], pts[-1]
        _edge(w, shift(xb) - shift(xa), yb - ya)
    w.ub(0, 6)
    head = struct.pack("<H", sh["id"]) + rect_bits(xmin, xmax + g, ymin, ymax).bytes()
    return head + body[sh["after_rect"]:sh["records_byte"]] + w.bytes()


def moved_place(body: bytes, dx_twips: int) -> bytes:
    """A PlaceObject2 placing a character with a matrix, the matrix moved `dx_twips` along x."""
    q = 5  # flags, depth, character
    r = BitReader(body, q)
    sc = rot = None
    if r.ub(1):
        k = r.ub(5)
        sc = (r.sb(k), r.sb(k))
    if r.ub(1):
        k = r.ub(5)
        rot = (r.sb(k), r.sb(k))
    k = r.ub(5)
    tx, ty = r.sb(k), r.sb(k)
    end = r.end()
    w = BitWriter()
    for part in (sc, rot):
        if part is None:
            w.ub(0, 1)
        else:
            w.ub(1, 1)
            n = sbits(*part)
            w.ub(n, 5)
            w.sb(part[0], n)
            w.sb(part[1], n)
    tx += dx_twips
    n = sbits(tx, ty)
    w.ub(n, 5)
    w.sb(tx, n)
    w.sb(ty, n)
    return body[:q] + w.bytes() + body[end:]


def two_point_oh(data: bytes, mult=GOLD) -> tuple[bytes, dict]:
    """The menu movie with "R.U.S.E. 2.0" in gold (the module's notes); (movie, what was done). LogoError when its
    logo isn't the one the title was fitted to; ImportError without shapely."""
    _need_shapely()
    lay = layout()
    grow = lay["right"] - END_OF_RUSE
    start = tags_start(data)
    out = bytearray(data[:start])
    report = dict(lay)
    seen = set()
    for code, body, long_form in read_tags(data, start, len(data)):
        if code in (2, 22, 32, 83):
            sid = struct.unpack_from("<H", body, 0)[0]
            if sid in FRAME:
                made = new_letters(areas(read_shape(body, code)), FRAME[sid], lay["x_two"], lay["x_zero"])
                fx, fy = FRAME[sid]
                body = rebuild_shape(body, code, made, (fx - 2, fx + lay["right"] + 4, fy - 2, fy + BOTTOM + 4))
                report[sid] = sum(len(getattr(g, "geoms", [g])) for g in made.values())
                seen.add(sid)
            elif sid in (652, 656):
                body = widen_rect_shape(body, code, grow)
                seen.add(sid)
        elif code == 39 and struct.unpack_from("<H", body, 0)[0] == 660:
            inner = bytearray(body[:4])
            for c2, b2, long2 in read_tags(body, 4, len(body)):
                if c2 == 26 and b2[0] & 0x06 == 0x06 and not b2[0] & 0x01 \
                        and struct.unpack_from("<H", b2, 3)[0] == 659:
                    b2 = moved_place(b2, round(lay["shift"] * PLACE_SCALE * 20))
                    seen.add(660)
                inner += tag_header(c2, len(b2), long2) + b2
            body = bytes(inner)
        out += tag_header(code, len(body), long_form) + body
    missing = sorted({*FRAME, 652, 656, 660} - seen)
    if missing:
        raise LogoError(f"the menu movie's logo isn't the one the title was fitted to (no {missing})")
    struct.pack_into("<I", out, 4, len(out))
    gold, report["tinted"] = tint(bytes(out), mult)
    return gold, report
