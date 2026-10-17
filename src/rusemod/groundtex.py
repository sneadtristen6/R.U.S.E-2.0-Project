"""Map Paint's textures: what the Texture brush paints with when a picture is picked (`brush = "texture"`, MOD_FORMAT
§8), besides a spot of the same map (the stamp). A texture is named by `ref`:

  game:<theatre>/<folder>/<name>   one of the game's own ground textures (grass, fields, earth, sand, snow, rock,
                                   cobbles...), read from the player's own game when a mod is built: none of them is in
                                   the mod, or in this repository
  map:<map pack>:<x>:<y>           a square of a map's ground picture, MAP_SIDE across, centred at (x, y) on it
  file:<name>.png                  the mod's own picture, files/ground/<name>.png (any PNG: its middle square is used)
  swatch:<theme>:<name>            one material of a theme's palette (palette(): "D-Day: wheat"), a patch of ONE
                                   material measured on the theme's own map ([[swatch]] in ground_presets.toml), taken
                                   turned so a field's rows run along it; it travels to any map (Map Paint plan step 4)

A palette swatch's repeats are not all the same: each is mirrored along and/or across its columns' way (a field's
rows), chosen per repeat by mirror_of, so the same repeat doesn't show over and over from afar. Made seamless as any
texture is (its left edge runs on into its right, its top into its bottom), it meets a mirrored neighbour with no
seam too: the two show the same edge. (Not turned a quarter: a seamless picture's sides don't join its top and
bottom; and its border isn't blended toward the mean of its turnings: on D-Day's swatches that showed as a blurred
grid, 2026-10-16.)

Each is laid repeating across the ground, from the map's corner (0, 0), `size` map units a repeat (0: its own size,
Swatch.period: for a game texture the size the game itself lays it at; for the mod's own picture the metres its
sidecar files/ground/<name>.toml says it covers (read_credit: a picture from the Studio's Online textures has one),
else FILE_PERIOD). Every texture is made seamless first
(seamless: its edges blended with its own middle, so no line shows where it repeats). Each level of the ground's tiles
samples the texture's own smaller copy (its mips) whose pixels are nearest the level's (Swatch.mip_for), nearest
pixel. A see-through texture lays as much as it shows: its alpha times the stroke's share.

The game's ground textures (catalogue): every colour picture among them, the same picture in several theatres listed
once; pictures that aren't colours aren't textures to paint with.

What the game shows of them is not tried yet: they are painted by groundpaint.paint_strokes, as the colour and the
stamp are (those seen in the game)."""
from __future__ import annotations

import hashlib
import math
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

from . import dxt, tgu1
from .tmst import Tgv, zipo_unpack

GAME_DIR = "gen\\ww2\\res2d\\decors\\"
SCENERY_DIR = "genglad\\patchable\\scenery\\"
FINEST = 160.0        # map units across a pixel of the ground's finest tiles: the same on all 32 maps (2026-10-09);
                      # a test copy whose tile set goes deeper paints for its own finer pixels (it sets this)
PICTURE = 160.0       # map units across a pixel of a shipped map's finest ground picture, what a palette swatch is cut
                      # from (FINEST as shipped, whatever FINEST is set to)
DETAIL_SPLIT = 4.0 * PICTURE   # a palette swatch with a detail texture: its own colour from this size up, the
                               # detail's grain below it (with_detail)
DETAIL_MOST = (0.35, 2.2)      # how far the detail may darken or lighten a pixel against its neighbourhood
GRAIN_UNIT = 100.0             # a grain pixel's byte for 1 (no change): 35 darkens to 0.35, 220 lightens to 2.2
OWN_PERIOD = 8192.0   # a game texture's repeat where the game's data doesn't say it (32 m: the most common)
MAP_SIDE = 81920.0    # a map square: 512 of its finest pixels across (320 m)
FILE_PERIOD = 8192.0  # the mod's own picture: one repeat 32 m across until the stroke says otherwise
METRE = 260.0         # map units in a metre (the Studio's METRE: the game's distances, 260,000 to a kilometre)
MOST = 1024           # pixels across a texture keeps at most (the game's own are 1,024 at most)
GROUND = Path("files") / "ground"  # the mod's own pictures to paint with
SEAM = 8              # seamless: the strip blended along each edge is 1/SEAM of the texture across
NEAREST_MIP = 2 ** 0.5  # a ground pixel samples the mip whose pixels are nearest its size: up to this many times it
_REF = re.compile(r"^(game):([a-z0-9_]+/[a-z0-9_]+/[a-z0-9_]+)$|^(map):([A-Za-z0-9_]+):(-?[0-9.]+):(-?[0-9.]+)$"
                  r"|^(file):([A-Za-z0-9_][A-Za-z0-9_ .-]{0,80}\.png)$|^(swatch):([a-z0-9_]+):([a-z0-9_]+)$")
_NOT_COLOUR = re.compile(r"(?i)_(nm|p)$")
_FOLDERS = re.compile(r"(?i)^gen\\ww2\\res2d\\decors\\([^\\]+)\\(stickers[^\\]*)\\([^\\]+)\.tgv$")


class TextureError(ValueError):
    pass


def check_ref(ref: str) -> str:
    """`ref` if it names a texture the way this module reads them (the module's words), else TextureError."""
    if not isinstance(ref, str) or not _REF.match(ref):  # not a game rule: how this module names a texture
        raise TextureError(f"texture {ref!r} isn't one: game:<set>/<folder>/<name>, map:<map>:<x>:<y>, "
                           f"file:<name>.png or swatch:<theme>:<name>")
    return ref


def game_member(ref: str) -> str:
    """game:france/stickers01/herbe_verte -> gen\\ww2\\res2d\\decors\\france\\stickers01\\herbe_verte.tgv."""
    return GAME_DIR + ref.split(":", 1)[1].replace("/", "\\") + ".tgv"


def game_ref(member: str) -> str | None:
    """The ref of a game texture member (its folders as _FOLDERS knows them), or None."""
    m = _FOLDERS.match(member)
    if not m:
        return None
    return "game:" + "/".join(p.lower() for p in m.groups())


# --- pixels -----------------------------------------------------------------------------------------------------
def _mip_size(tex: Tgv, k: int, payload: bytes, dxt5: bool) -> tuple[int, int]:
    """Mip `k`'s width and height in pixels, from its payload: a TGU1 header says; a ZIPO one is the full size halved
    as many times as there are mips after it, checked against its bytes (a mip under 4 pixels is still one block)."""
    if payload[:4] == b"TGU1":
        head = tgu1.Header.parse(payload)
        return head.width * 4, head.height * 4
    shift = len(tex.mips) - 1 - k
    w, h = max(1, tex.width >> shift), max(1, tex.height >> shift)
    w4, h4 = max(4, (w + 3) // 4 * 4), max(4, (h + 3) // 4 * 4)
    if len(zipo_unpack(payload)) != w4 * h4 // (1 if dxt5 else 2):
        raise TextureError(f"a mip of {tex.width}x{tex.height} holds an unexpected number of bytes")
    return w4, h4


def tgv_rgba(raw: bytes, want: int = MOST) -> tuple[int, int, bytes]:
    """A game texture's pixels (width, height, RGBA rows top to bottom) at its smallest mip at least `want` across
    (its full size when none is): the mips run smallest first. DXT1 and DXT5 pictures only (TextureError else)."""
    tex = Tgv(raw)
    fmt = tex.format.upper()
    if not fmt.startswith(("DXT1", "DXT5")):
        raise TextureError(f"a {tex.format} picture isn't a colour picture")
    dxt5 = fmt.startswith("DXT5")
    pick = len(tex.mips) - 1
    for k in range(len(tex.mips)):
        payload = tex.payload(k)
        if min(_mip_size(tex, k, payload, dxt5)) >= min(want, tex.width, tex.height):
            pick = k
            break
    payload = tex.payload(pick)
    w, h = _mip_size(tex, pick, payload, dxt5)
    if payload[:4] == b"TGU1":
        blocks = tgu1.decode(payload)
    elif payload[:4] == b"ZIPO":
        blocks = zipo_unpack(payload)
    else:
        raise TextureError(f"unknown picture codec {payload[:4]!r}")
    return w, h, bytes(dxt.decode_rgba(bytes(blocks), w, h, "DXT5" if dxt5 else "DXT1"))


def square(w: int, h: int, rgba: bytes, most: int = MOST) -> tuple[int, bytes]:
    """The middle square of a picture, as n x n RGBA pixels, n the largest power of two no more than its side or
    `most`: each pixel the picture's pixel under its middle."""
    side = min(w, h)
    n = 1
    while n * 2 <= min(side, most):
        n *= 2
    x0, y0 = (w - side) // 2, (h - side) // 2
    out = bytearray(n * n * 4)
    cols = [x0 + int((i + 0.5) * side / n) for i in range(n)]
    for j in range(n):
        row = (y0 + int((j + 0.5) * side / n)) * w
        for i, c in enumerate(cols):
            k = 4 * (row + c)
            out[4 * (j * n + i):4 * (j * n + i) + 4] = rgba[k:k + 4]
    return n, bytes(out)


def edge_weights(n: int) -> list[float]:
    """How much of the picture itself stays at each column (row) in seamless: 1 inside, falling smoothly (3t² - 2t³)
    to 0 at its edges across a strip n / SEAM wide."""
    strip = n / SEAM
    out = []
    for i in range(n):
        t = min(i + 0.5, n - i - 0.5) / strip
        out.append(1.0 if t >= 1.0 else t * t * (3.0 - 2.0 * t))
    return out


def seamless(n: int, px: bytes) -> bytes:
    """The picture made to repeat without a seam: along its edges it gives way to itself moved by half its size (whose
    edges are its own middle), so its own edges never meet; its middle stays as it is. A plain mix of the two, every
    channel (a pattern that lines up with its moved self, a checker's squares, stays as it is). Under 8 pixels across,
    as it is."""
    if n < 8:
        return px
    keep = edge_weights(n)
    h = n // 2
    out = bytearray(len(px))
    for j in range(n):
        tj = keep[j]
        mj = ((j + h) % n) * n
        for i in range(n):
            m = keep[i] * tj
            k = 4 * (j * n + i)
            r = 4 * (mj + (i + h) % n)
            for c in range(4):
                out[k + c] = int(m * px[k + c] + (1.0 - m) * px[r + c] + 0.5)
    return bytes(out)


def coin(k: int, salt: int) -> int:
    """0 or 1 for a whole number k, as by a coin: whole-number sums that stay under 2^53, so Python, numpy and the
    Studio page's JavaScript all give the same (squared twice modulo the prime MIX: each as often, the next k's alike
    as often as chance)."""
    h = (k * 92821 + salt) % MIX
    h = (h * h + 12345) % MIX
    h = (h * h + 54321) % MIX
    return h * 2 // MIX


def mirror_of(ci: int, cj: int) -> int:
    """How the repeat at column ci, row cj (each floor(coordinate / repeat)) of a palette swatch is laid: bit 1
    mirrored along the columns' way (i: a field's rows), the same all down its column of repeats; bit 2 across it
    (j), the same all along its row. (A repeat mirrored along i beside one above it that isn't would meet it with a
    seam: their shared edge read one way and the other.)"""
    return coin(ci, 7) | coin(cj, 68917) << 1


MIX = 65521  # the largest prime under 2^16: coin's squares stay under 2^32


def halve(n: int, px: bytes) -> bytes:
    """An n x n RGBA picture at half its size: each pixel the mean of the four under it, rounded half up."""
    h = n // 2
    out = bytearray(h * h * 4)
    for j in range(h):
        a, b = 8 * j * n, 4 * (2 * j + 1) * n
        for i in range(h):
            k0, k1 = a + 8 * i, b + 8 * i
            o = 4 * (j * h + i)
            for c in range(4):
                out[o + c] = (px[k0 + c] + px[k0 + 4 + c] + px[k1 + c] + px[k1 + 4 + c] + 2) // 4
    return bytes(out)


@dataclass
class Swatch:
    """A texture ready to lay: its mips (n x n RGBA, n halving to 1; mips[0] the largest), what one repeat covers at
    its own size (map units), and a fingerprint of its pixels (for the build's kept tiles)."""
    ref: str
    period: float
    mips: list
    digest: str = ""
    mirrored: bool = False  # a palette swatch: each repeat mirrored its own way (mirror_of); else all the same
    grain: list = field(default_factory=list)   # a palette swatch's grain (grain_of): its mips (n x n, one byte a
    grain_period: float = 0.0                   # pixel, GRAIN_UNIT = 1), laid this many map units a repeat
                                                # unmirrored and unturned over the colour (so no fold line shows)

    @classmethod
    def make(cls, ref: str, n: int, px: bytes, period: float, mirrored: bool = False, grain=None) -> "Swatch":
        """`grain`: (n, its pixels, map units a repeat) from grain_of, or None."""
        px = seamless(n, px)
        mips = [(n, px)]
        while n > 1:
            px = halve(n, px)
            n //= 2
            mips.append((n, px))
        said = struct.pack("<IdB", mips[0][0], period, 1) if mirrored else struct.pack("<Id", mips[0][0], period)
        gmips, gperiod = [], 0.0
        if grain is not None:
            gn, gpx, gperiod = grain
            gmips = [(gn, gpx)]
            while gn > 1:
                gpx = _halve_plane(gn, gpx)
                gn //= 2
                gmips.append((gn, gpx))
            said += struct.pack("<Id", gmips[0][0], gperiod) + gmips[0][1]
        digest = hashlib.blake2b(mips[0][1] + said, digest_size=16).hexdigest()
        return cls(ref, period, mips, digest, mirrored, gmips, gperiod)

    def grain_sampler(self, rep: float, pixel: float):
        """(x, y) -> how much the grain lightens (over 1) or darkens the colour there, or None without a grain: laid
        from (0, 0) as the colour, its repeat scaled as the stroke scales the colour's (`rep` against the period),
        neither turned nor mirrored, at the mip whose pixels are nearest `pixel`."""
        if not self.grain:
            return None
        grep = self.grain_period * rep / self.period
        m, most = 0, pixel * NEAREST_MIP
        while m + 1 < len(self.grain) and grep / self.grain[m + 1][0] <= most:
            m += 1
        n, g = self.grain[m]
        last = n - 1

        def at(x: float, y: float) -> float:
            i = int((x / grep) % 1.0 * n)
            j = int((y / grep) % 1.0 * n)
            return g[(j if j < last else last) * n + (i if i < last else last)] / GRAIN_UNIT
        return at

    def mip_for(self, rep: float, pixel: float) -> int:
        """The mip a ground pixel `pixel` map units across samples, the texture laid `rep` map units a repeat: the one
        whose pixels are nearest its size (the smallest whose pixels are no bigger than it times the square root of
        2; the largest mip when even its pixels are bigger)."""
        m, most = 0, pixel * NEAREST_MIP
        while m + 1 < len(self.mips) and rep / self.mips[m + 1][0] <= most:
            m += 1
        return m

    def sampler(self, rep: float, pixel: float, turn: float = 0.0):
        """(x, y) -> (r, g, b, a): the texture laid `rep` map units a repeat from (0, 0), at the mip for `pixel`,
        turned `turn` degrees round (0, 0) (anticlockwise, as a stamp's turn: a point reads the texture at itself
        turned back by it), so its columns' way runs along `turn`."""
        n, px = self.mips[self.mip_for(rep, pixel)]
        last = n - 1
        mirrored = self.mirrored
        c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        grain = self.grain_sampler(rep, pixel)

        def at(x: float, y: float) -> tuple[int, int, int, int]:
            g = grain(x, y) if grain else 1.0
            if turn:
                x, y = x * c + y * s, y * c - x * s
            i = int((x / rep) % 1.0 * n)
            j = int((y / rep) % 1.0 * n)
            i, j = (i if i < last else last), (j if j < last else last)
            if mirrored:   # this repeat's own way (mirror_of)
                v = mirror_of(math.floor(x / rep), math.floor(y / rep))
                if v & 1:
                    i = last - i
                if v & 2:
                    j = last - j
            k = 4 * (j * n + i)
            if g == 1.0:
                return px[k], px[k + 1], px[k + 2], px[k + 3]
            return (min(255, int(px[k] * g + 0.5)), min(255, int(px[k + 1] * g + 0.5)),
                    min(255, int(px[k + 2] * g + 0.5)), px[k + 3])
        return at


def rep_of(stroke, swatch: Swatch) -> float:
    """Map units one repeat of a texture stroke covers: its `size`, or the texture's own."""
    return stroke.size if stroke.size > 0.0 else swatch.period


def need(rep: float) -> int:
    """Pixels across a texture laid `rep` map units a repeat needs, so its pixels are no bigger than the ground's
    finest: a power of two, MOST at most."""
    n = 1
    while n < MOST and rep / n > FINEST:
        n *= 2
    return n


# --- the game's ground textures ---------------------------------------------------------------------------------
def _string(nd, v) -> str | None:
    if v is None or v.tc not in (0x07, 0x1C) or len(v.payload) < 4:
        return None
    i = struct.unpack_from("<I", v.payload)[0]
    return nd.strings[i] if i < len(nd.strings) else None


def own_periods(glad_arc) -> dict[str, float]:
    """{texture member (lower case): map units it repeats every} at the size the game lays it at; where it's laid at
    several sizes, the most common. From ZZ_GladPatchableWin.dat (`glad_arc`, an Edat)."""
    from collections import Counter
    from .ndf import Ndf, local_ref, sub_values
    seen: dict = {}
    for e in glad_arc.entries:
        low = e.path.lower()
        if not (low.startswith(SCENERY_DIR) and low.endswith("decors.cpp.gladndfbin")):
            continue
        nd = Ndf(bytes(glad_arc.read(e)))
        names = [p for p, _ in nd.props]

        def value_of(v):
            """A parameter's number: the Value of the object a local reference points at."""
            at = local_ref(v) if v is not None else None
            if at is None or at >= len(nd.objects):
                return None
            for pi, x in nd.objects[at].props:
                if names[pi] == "Value":
                    return x
            return None
        for o in nd.objects:
            props = {names[pi]: v for pi, v in o.props}
            textures, params = props.get("Textures"), props.get("ParameterDico")
            if textures is None or params is None or textures.tc != 0x12 or params.tc != 0x12:
                continue
            colour = None
            items = sub_values(textures)
            for k in range(0, len(items) - 1, 2):
                if _string(nd, items[k]) == "OARTexture0" and items[k + 1].tc == 0x22:
                    colour = _string(nd, sub_values(items[k + 1])[0])
            if not colour:
                continue
            tile = extent = None
            items = sub_values(params)
            for k in range(0, len(items) - 1, 2):
                key = _string(nd, items[k])
                if key == "TexDiffuseTile":
                    v = value_of(items[k + 1])
                    tile = struct.unpack("<f", v.payload[:4])[0] if v is not None and v.tc == 0x05 else None
                elif key == "StickerExtents":
                    v = value_of(items[k + 1])
                    extent = struct.unpack("<f", v.payload[:4])[0] if v is not None and v.tc == 0x0B else None
            if not tile or not extent or not (tile > 0 and extent > 0):
                continue
            member = ("gen\\" + colour.replace("/", "\\").lower().rsplit(".", 1)[0] + ".tgv")
            seen.setdefault(member, Counter())[round(extent / tile, 3)] += 1
    return {m: float(c.most_common(1)[0][0]) for m, c in seen.items()}


# what a game texture's name says it is: its group, and the words of its name worth saying (both words.toml keys:
# gtex_group_<group>, gtex_<word>). The first group whose pattern matches the name wins.
GROUPS = [
    ("marks", r"logo|marquage|gd_trait|patternneutre"),
    ("damage", r"gravats|impact|cratere|brule|tracesdechar|salissure|_dest"),
    ("town", r"decoupe|ville|village|tourdemaison|tour_arbre|cour|paves|pavets|trottoir|dalle|plancher|planches"
             r"|tranchee|rails"),
    ("roads", r"route|bitume|asphalte|chemin|traces|piste|contour|liaison|petiteroute"),
    ("snow", r"givre|neige"),
    ("water", r"marais|fleuve|bord_de_mer|turquoise|humide"),
    ("rock", r"roche|cailloux|caillou"),
    ("sand", r"sable|dune|ondes"),
    ("fields", r"labour|paille|culture|grain|jachere"),
    ("grass", r"herbe|veget|broussailles|palmiers|sousbois"),
    ("earth", r"terre|sol_|sol$|boue"),
]
GROUP_ORDER = ["grass", "fields", "earth", "sand", "rock", "snow", "water", "roads", "town", "damage", "marks",
               "other"]
# words in a texture's name -> the word said for it (words.toml gtex_<word>), longest first where one holds another
WORDS = [
    ("verteclaire", "light_green"), ("vertvif", "bright_green"), ("vertanis", "pale_green"), ("verte", "green"),
    ("vert", "green"), ("herbeanis", "grassy"), ("herbeuse", "grassy"), ("herbe", "grass"),
    ("paquerette", "daisies"), ("rouge", "red"), ("vieille", "dry"), ("foncee", "dark"), ("fonce", "dark"),
    ("sombre", "dark"), ("dark", "dark"), ("claire", "light"), ("clair", "light"), ("leger", "light"),
    ("labourage", "ploughed"), ("laboure", "ploughed"), ("paille", "straw"), ("culture", "crops"),
    ("grain", "grain"), ("jachere", "fallow"), ("terre", "earth"), ("ocre", "ochre"), ("details", "details"),
    ("sablecailloux", "pebbles"), ("sabletracesnoires", "dark_tracks"), ("sablehumide", "wet"), ("sable", "sand"),
    ("dune", "dunes"), ("ondes", "ripples"), ("givre", "frost"), ("neige", "snow"), ("marais", "marsh"),
    ("solhumide", "wet"), ("solsec", "dry"), ("humide", "wet"), ("fleuve", "river"), ("bord_de_mer", "seashore"),
    ("turquoise", "turquoise"), ("roche", "rock"), ("cailloux", "pebbles"), ("caillouteuse", "stony"),
    ("gravats", "rubble"), ("impact", "crater"), ("cratere", "crater"), ("brule", "burnt"),
    ("tracesdechar", "tank_tracks"), ("pneus", "tyre_tracks"), ("salissure", "stain"), ("sousbois", "forest_floor"),
    ("broussailles", "scrub"), ("veget", "plants"), ("palmiers", "palms"), ("asphalte", "asphalt"),
    ("bitume", "tarmac"), ("ruelle", "alley"), ("degrade", "worn"), ("route", "road"), ("rte", "road"),
    ("chemin", "track"), ("petitchemin", "track"), ("piste", "track"), ("bords", "edges"), ("bord", "edges"),
    ("bordure", "edges"), ("croisement", "crossing"), ("tournant", "bend"), ("liaison", "junction"),
    ("demi", "half"), ("large", "wide"), ("paves", "cobbles"), ("pavets", "cobbles"), ("cour", "yard"),
    ("trottoir", "pavement"), ("dallebrick", "brick"), ("dalles", "slabs"), ("rails", "rails"),
    ("tour_arbre", "tree_ring"), ("tourdemaison", "house_edge"), ("boue", "mud"), ("plancher", "wooden_floor"),
    ("planches", "planks"), ("tranchee", "trench"), ("decoupe", "layout"), ("ville", "town"),
    ("village", "village"), ("logo", "emblem"), ("marquageblanc", "white_markings"),
    ("marquagejaune", "yellow_markings"), ("trait", "line"), ("sol", "ground"), ("traces", "tracks"),
]
THEATRES = ("france", "allemagne", "hollande", "italie", "ardennes", "afrique", "communs")


def describe(name: str, folder: str = "") -> tuple[str, list[str]]:
    """(group, words) for a game texture's file name (and its folder: stickers_destructions is battle damage)."""
    low = name.lower()
    group = "damage" if "destruction" in folder.lower() else next(
        (g for g, pat in GROUPS if re.search(pat, low)), "other")
    said, rest = [], re.sub(r"^coc_stickers_(tunisie_)?|^coc_|^stickers_|^s1_|_\d+$|\d+$|_[ad]$|_sc$|_sg$", "", low)
    for word, key in WORDS:
        if word in rest:
            rest = rest.replace(word, " ")
            if key not in said:
                said.append(key)
    return group, said


@dataclass
class GameTexture:
    ref: str           # game:<theatre>/<folder>/<name>
    theatres: list     # the theatres it's in (the same picture in several is listed once)
    group: str
    words: list
    period: float      # map units it repeats every in the game
    width: int
    height: int
    see_through: bool  # it has see-through parts: it lays over what's there


def catalogue(zz_arc, glad_arc=None) -> list[GameTexture]:
    """Every one of the game's ground textures that is a colour picture (ZZ_Win.dat, `zz_arc`), the same bytes in
    several theatres once, in GROUP_ORDER then name order. With `glad_arc` (ZZ_GladPatchableWin.dat) each one's own
    repeat (own_periods); OWN_PERIOD where the game's data doesn't say."""
    periods = own_periods(glad_arc) if glad_arc is not None else {}
    by_bytes: dict = {}
    for e in zz_arc.entries:
        m = _FOLDERS.match(e.path)
        if not m or _NOT_COLOUR.search(m.group(3)):
            continue
        raw = bytes(zz_arc.read(e))
        try:
            tex = Tgv(raw)
        except (ValueError, struct.error):
            continue
        fmt = tex.format.upper()
        if not fmt.startswith(("DXT1", "DXT5")):
            continue
        key = hashlib.blake2b(raw, digest_size=16).digest()
        theatre, folder, name = (p.lower() for p in m.groups())
        if key in by_bytes:
            if theatre not in by_bytes[key].theatres:
                by_bytes[key].theatres.append(theatre)
            continue
        group, words = describe(name, folder)
        by_bytes[key] = GameTexture(game_ref(e.path), [theatre], group, words,
                                    periods.get(e.path.lower(), OWN_PERIOD), tex.width, tex.height,
                                    fmt.startswith("DXT5"))
    out = list(by_bytes.values())
    out.sort(key=lambda t: (GROUP_ORDER.index(t.group) if t.group in GROUP_ORDER else len(GROUP_ORDER), t.ref))
    return out


# --- the game's own decals over painted ground (`decals`, a texture stroke's) ---------------------------------------
# Up close the ground's picture is 0.6 m a pixel; the game's maps show their detail there with decals, scenery objects
# laid on the ground (rusemod.scenery). A game texture's own decal types are laid over the ground it paints, on one
# even grid, each point taking the decal of the texture that shows on top there. Not tried in the game yet.
DECAL_SIZE = 2.5   # decals laid this much bigger than the game lays them (its road decals: 2.0): fewer cover an area
DECAL_STEP = 0.75  # grid points this share of a decal's width apart: neighbours overlap, so their soft edges meet
DECAL_TURN = 360.0
DECAL_AT = 0.5     # a point takes a decal where its stroke paints at least this strongly (as `clear` takes off)
SETS = {"france": "France", "allemagne": "Allemagne", "hollande": "Hollande", "italie": "Italie",
        "ardennes": "Ardennes", "afrique": "Africa", "communs": "Common"}  # theatre folder -> its decor set's name
SCENERY_FOLDERS = {"africa": "afrique", "commonset": "communs"}  # a decor set's folder -> its textures' theatre
_SET = re.compile(r"ClusterLoad_(\w+?)DecorsSet")


@dataclass
class DecalType:
    name: str      # the scenery type (TypeWarrior/Herbe_verte)
    theatre: str   # the decor set's folder it is defined in (france, communs, ...)
    half: float    # map units from its middle to its side at size 1
    colour: str    # its colour picture (the texture member, lower case)


def decal_types(glad_arc) -> dict[str, list[DecalType]]:
    """{texture member (lower case): the decal types that lay it}, from the game's decor sets (ZZ_GladPatchableWin.dat,
    `glad_arc`): each type's registered name, its set and its size (MaxExtent)."""
    from .ndf import Ndf, local_ref, sub_values
    out: dict = {}
    for e in glad_arc.entries:
        low = e.path.lower()
        if not (low.startswith(SCENERY_DIR) and low.endswith("decors.cpp.gladndfbin")):
            continue
        folder = low[len(SCENERY_DIR):].split("\\", 1)[0]
        theatre = SCENERY_FOLDERS.get(folder, folder)
        nd = Ndf(bytes(glad_arc.read(e)))
        names = [p for p, _ in nd.props]

        def props(i):
            return {names[pi]: v for pi, v in nd.objects[i].props}
        for i, o in enumerate(nd.objects):
            if not nd.classes[o.cls].endswith("Sticker"):
                continue
            p = props(i)
            reg, hi = _string(nd, p.get("RegistrationName")), p.get("MaxExtent")
            handler = local_ref(p["SceneryMeshBucketHandler"]) if "SceneryMeshBucketHandler" in p else None
            if not reg or hi is None or len(hi.payload) < 12 or handler is None:
                continue
            mat = props(handler).get("AdditionalDataMeshMaterial")
            mat = local_ref(mat) if mat is not None else None
            textures = props(mat).get("Textures") if mat is not None else None
            if textures is None or textures.tc != 0x12:
                continue
            items = sub_values(textures)
            colour = next((_string(nd, sub_values(items[k + 1])[0]) for k in range(0, len(items) - 1, 2)
                           if _string(nd, items[k]) == "OARTexture0" and items[k + 1].tc == 0x22), None)
            half = struct.unpack("<f", hi.payload[:4])[0]
            if not colour or not half > 0:
                continue
            member = "gen\\" + colour.replace("/", "\\").lower().rsplit(".", 1)[0] + ".tgv"
            out.setdefault(member, []).append(DecalType(reg, theatre, half, member))
    return out


def map_sets(glad_arc, pack: str) -> set[str]:
    """The decor sets a map loads (theatre folders: france, communs, ...): the sets its cluster names
    (genglad\\patchable\\map\\<map>\\clustermap.cpp.gladndfbin), and the sets those load in turn
    (genglad\\patchable\\scenery\\clustersets.cpp.gladndfbin; France's loads the common one). Empty when not found."""
    from .ndf import Ndf
    wanted = {name.lower(): t for t, name in SETS.items()}

    def strings(member):
        e = glad_arc.entry(member)
        if e is None:
            return []
        nd = Ndf(bytes(glad_arc.read(e)))
        return [s for s in list(nd.strings) + list(nd.exports.values()) + list(nd.imports.values())
                if isinstance(s, str)]
    named = {m.group(1).lower() for s in strings(f"genglad\\patchable\\map\\{pack.lower()}\\clustermap.cpp.gladndfbin")
             for m in _SET.finditer(s)}
    out = {wanted[n] for n in named if n in wanted}
    if out:
        from .ndf import local_ref
        e = glad_arc.entry("genglad\\patchable\\scenery\\clustersets.cpp.gladndfbin")
        if e is not None:  # a set that loads another (France's: the common one)
            from .ndf import sub_values
            nd = Ndf(bytes(glad_arc.read(e)))
            props = [p for p, _ in nd.props]
            for i, path in nd.exports.items():
                m = _SET.search(path or "")
                if not m or m.group(1).lower() not in named or path.count("/") > 2 or i >= len(nd.objects):
                    continue
                for pi, v in nd.objects[i].props:
                    if props[pi] != "SubClusterList":
                        continue
                    for item in sub_values(v):
                        at = local_ref(item)
                        m2 = _SET.search(nd.exports.get(at, "") or "") if at is not None else None
                        if m2 and m2.group(1).lower() in wanted:
                            out.add(wanted[m2.group(1).lower()])
    return out


DECAL_BYTES = 40  # what one decal adds to a map's scenery, about: its 4-byte word, a 24-byte turn-and-place, two list
                  # entries of 4 (scenery.add_objects's blocks), and a little for its block
SCENERY_MOST = 0xFFFFFC  # a map's scenery data can't grow past this: a block link holds its place in 24 bits
ROOM_KEPT = 256 * 1024   # left free under it, for the blocks and grid cells the new objects need


def decal_room(scenery_len: int) -> int:
    """How many decals a map's scenery of `scenery_len` bytes of data has room for (decal_grid's `most`)."""
    return max(0, (SCENERY_MOST - ROOM_KEPT - scenery_len) // DECAL_BYTES)


def decal_grid(strokes: list, types: dict, sets: set[str], seed: str = "", most: int | None = None,
               inside: tuple[float, float] | None = None) -> tuple[list, dict]:
    """The decals over painted ground: (scenery.NewObject list, {"types": {type: count}, "missing": [textures with no
    decal the map loads], "step": map units between points, "thinned": whether the grid was spread out to fit}). Each
    texture its own grid over its strokes' boxes, a point every DECAL_STEP of its smallest decal's laid width; each
    point takes the stroke on top there (the last one painting it at least DECAL_AT strongly); if that is a texture
    stroke of a game texture with `decals` on, one of that texture's decal types the map loads (`sets`), turned and
    sized a little at random (the same every build: `seed`). With `inside` (the scenery grid's width and height), no
    point off it: the game draws nothing there and the build refuses one. With `most` (decal_room), a grid that would
    lay more is spread out evenly until it fits: the same look, fewer and further apart."""
    out, said = _decal_grid(strokes, types, sets, seed, 1.0, inside)
    spread = 1.0
    while most is not None and len(out) > most and spread < 64.0:
        spread *= max(1.05, math.sqrt(len(out) / max(1, most)) * 1.02)
        out, said = _decal_grid(strokes, types, sets, seed, spread, inside)
        said["thinned"] = True
    if most is not None and len(out) > most:
        out = []
    said.setdefault("thinned", False)
    return out, said


def _decal_grid(strokes: list, types: dict, sets: set[str], seed: str, spread: float,
                inside: tuple[float, float] | None) -> tuple[list, dict]:
    import random
    from .brush import PAINT_KINDS
    from .scenery import NewObject
    lay = [s for s in strokes if s.kind.kind == "texture" and s.decals and s.texture.startswith("game:")]
    if not lay:
        return [], {"types": {}, "missing": [], "step": 0.0}
    usable, missing = {}, []
    for ref in dict.fromkeys(s.texture for s in lay):
        here = [t for t in types.get(game_member(ref).lower(), []) if t.theatre in sets]
        if here:
            usable[ref] = here
        else:
            missing.append(ref)
    if not usable:
        return [], {"types": {}, "missing": missing, "step": 0.0}
    # each texture its own grid, a point every DECAL_STEP of its smallest decal's laid width, over its own strokes
    steps = {ref: DECAL_STEP * 2 * DECAL_SIZE * min(t.half for t in ts) * spread for ref, ts in usable.items()}
    paint = [s for s in strokes if s.kind.kind in PAINT_KINDS]
    boxes = [s.box() for s in paint]
    bucket = 4 * max(steps.values())  # strokes filed by the cells their boxes reach, to find the ones over a point
    cells: dict = {}
    for k, (bx0, bx1, by0, by1) in enumerate(boxes):
        for cx in range(int(bx0 // bucket), int(bx1 // bucket) + 1):
            for cy in range(int(by0 // bucket), int(by1 // bucket) + 1):
                cells.setdefault((cx, cy), []).append(k)

    def top_at(x, y):
        """The stroke that shows on top at (x, y): the last one painting it at least DECAL_AT strongly."""
        for k in reversed(cells.get((int(x // bucket), int(y // bucket)), [])):
            bx0, bx1, by0, by1 = boxes[k]
            if bx0 <= x <= bx1 and by0 <= y <= by1 and paint[k].strength_at(x, y) * paint[k].weight >= DECAL_AT:
                return paint[k]
        return None
    out, counts = [], {}
    for ref, kinds in usable.items():
        step, done = steps[ref], set()
        for s in lay:
            if s.texture != ref:
                continue
            bx0, bx1, by0, by1 = s.box()
            for iy in range(math.floor(by0 / step), math.floor(by1 / step) + 1):
                for ix in range(math.floor(bx0 / step), math.floor(bx1 / step) + 1):
                    if (ix, iy) in done:
                        continue
                    done.add((ix, iy))
                    rnd = random.Random(f"decals {seed} {ref} {ix} {iy} {spread}")  # the same every build
                    x = (ix + 0.5 + rnd.uniform(-0.3, 0.3)) * step
                    y = (iy + 0.5 + rnd.uniform(-0.3, 0.3)) * step
                    if inside is not None and not (0.0 <= x < inside[0] and 0.0 <= y < inside[1]):
                        continue
                    top = top_at(x, y)
                    if top is None or top.kind.kind != "texture" or top.texture != ref or not top.decals:
                        continue
                    t = kinds[rnd.randrange(len(kinds))]
                    out.append(NewObject(t.name, x, y, rnd.uniform(0.0, DECAL_TURN),
                                         round(DECAL_SIZE * rnd.uniform(0.85, 1.15), 3), solid=False))
                    counts[t.name] = counts.get(t.name, 0) + 1
    return out, {"types": counts, "missing": missing, "step": min(steps.values())}


# --- a map's square ---------------------------------------------------------------------------------------------
def map_square(read, x: float, y: float, cache=None, n: int = 512) -> tuple[int, bytes]:
    """A square of a map's ground picture MAP_SIDE across, centred at (x, y), from its finest tiles: n x n RGBA, each
    pixel the picture at its middle (opaque; off the map, the nearest edge's). `read(member)`: the map pack's."""
    from .groundpaint import _picture_sampler, map_bounds
    from .tmst import Tmst
    mesh = read("output\\highdef.tms")
    index, chunk = read("output\\highdef.tmst_pc"), read("output\\highdef.tmst_chunk_pc")
    if mesh is None or index is None or chunk is None:
        raise TextureError("that map has no ground picture to take a square of")
    bounds = map_bounds(mesh)
    at = _picture_sampler(Tmst(index, chunk), bounds, 0, cache)
    x0, y0, x1, y1 = bounds
    step = MAP_SIDE / n
    out = bytearray(n * n * 4)
    for j in range(n):
        py = min(max(y - MAP_SIDE / 2 + (j + 0.5) * step, y0 + 1.0), y1 - 1.0)
        for i in range(n):
            px = min(max(x - MAP_SIDE / 2 + (i + 0.5) * step, x0 + 1.0), x1 - 1.0)
            c = at(px, py) or (0, 0, 0)
            k = 4 * (j * n + i)
            out[k:k + 4] = bytes((c[0], c[1], c[2], 255))
    return n, bytes(out)


def map_patch(read, x: float, y: float, side: float, facing: float, n: int, cache=None) -> tuple[int, bytes]:
    """A palette swatch's pixels: the square `side` map units across centred at (x, y) on a map's ground picture,
    turned so the direction `facing` (degrees, from +x toward +y: a field's rows) runs along its columns' way (i), as
    n x n RGBA (opaque). Each pixel is the picture between its four nearest pixels' middles (PICTURE apart, from the
    ground's corner), weighed by nearness: the patch's pixels lie turned across the picture's. `read(member)`: the
    map pack's."""
    from .groundpaint import _picture_sampler, map_bounds
    from .tmst import Tmst
    mesh = read("output\\highdef.tms")
    index, chunk = read("output\\highdef.tmst_pc"), read("output\\highdef.tmst_chunk_pc")
    if mesh is None or index is None or chunk is None:
        raise TextureError("that map has no ground picture to take a swatch of")
    bounds = map_bounds(mesh)
    at = _picture_sampler(Tmst(index, chunk), bounds, 0, cache)
    x0, y0, x1, y1 = bounds
    c, s = math.cos(math.radians(facing)), math.sin(math.radians(facing))
    step = side / n
    out = bytearray(n * n * 4)
    for j in range(n):
        b = (j + 0.5) * step - side / 2.0
        for i in range(n):
            a = (i + 0.5) * step - side / 2.0
            fx, fy = (x + a * c - b * s - x0) / PICTURE - 0.5, (y + a * s + b * c - y0) / PICTURE - 0.5
            gx, gy = math.floor(fx), math.floor(fy)
            tx, ty = fx - gx, fy - gy
            sums = [0.0, 0.0, 0.0]
            for dx, dy, w in ((0, 0, (1 - tx) * (1 - ty)), (1, 0, tx * (1 - ty)), (0, 1, (1 - tx) * ty),
                              (1, 1, tx * ty)):
                px = min(max(x0 + (gx + dx + 0.5) * PICTURE, x0 + 1.0), x1 - 1.0)
                py = min(max(y0 + (gy + dy + 0.5) * PICTURE, y0 + 1.0), y1 - 1.0)
                got = at(px, py) or (0, 0, 0)
                for ch in range(3):
                    sums[ch] += w * got[ch]
            k = 4 * (j * n + i)
            out[k:k + 4] = bytes((int(sums[0] + 0.5), int(sums[1] + 0.5), int(sums[2] + 0.5), 255))
    return n, bytes(out)


def _blur_wrap(n: int, plane: list[float], r: int) -> list[float]:
    """A tiling n x n plane averaged over the (2r + 1)-pixel square round each pixel, wrapping at its edges (its
    repeats meet): two passes of running sums."""
    if r <= 0:
        return list(plane)
    w = 2 * r + 1
    tmp = [0.0] * (n * n)
    for j in range(n):
        row = plane[j * n:(j + 1) * n]
        s = sum(row[i % n] for i in range(-r, r + 1))
        for i in range(n):
            tmp[j * n + i] = s / w
            s += row[(i + r + 1) % n] - row[(i - r) % n]
    out = [0.0] * (n * n)
    for i in range(n):
        s = sum(tmp[(j % n) * n + i] for j in range(-r, r + 1))
        for j in range(n):
            out[j * n + i] = s / w
            s += tmp[((j + r + 1) % n) * n + i] - tmp[((j - r) % n) * n + i]
    return out


def detail_repeats(side: float, detail_side: float) -> int:
    """How many times a swatch `side` across lays its detail texture across it: the whole number nearest the detail's
    own size (`detail_side`), so the two repeat together."""
    return max(1, round(side / detail_side))


def low_pass(n: int, px: bytes, side: float, split: float) -> bytes:
    """A tiling n x n RGBA picture `side` map units across averaged over squares `split` across (wrapping): what a
    palette swatch with a grain keeps of its own picture, the grain giving what's finer (grain_of)."""
    r = max(0, int(round(split / (side / n) / 2.0)))
    chans = [_blur_wrap(n, [float(px[4 * q + c]) for q in range(n * n)], r) for c in range(3)]
    out = bytearray(n * n * 4)
    for q in range(n * n):
        out[4 * q:4 * q + 4] = bytes((int(chans[0][q] + 0.5), int(chans[1][q] + 0.5), int(chans[2][q] + 0.5), 255))
    return bytes(out)


def grain_of(dn: int, dpx: bytes, rep: float, split: float) -> bytes:
    """A detail texture's grain: dn x dn of it (RGBA, `rep` map units across) as how much each pixel lightens
    or darkens against its own average over `split` (its brightness over that, DETAIL_MOST at most each way), one
    byte a pixel, GRAIN_UNIT = 1, made to repeat without a seam. Averaged over `split` it is about 1: laid over a
    colour averaged that way (low_pass), the colour is the same from afar and the grain shows up close."""
    lum = [0.299 * dpx[4 * q] + 0.587 * dpx[4 * q + 1] + 0.114 * dpx[4 * q + 2] for q in range(dn * dn)]
    low = _blur_wrap(dn, lum, max(0, int(round(split / (rep / dn) / 2.0))))
    lo, hi = DETAIL_MOST
    out = bytearray(4 * dn * dn)
    for q in range(dn * dn):
        f = lum[q] / low[q] if low[q] > 0.5 else 1.0
        v = int(round((lo if f < lo else hi if f > hi else f) * GRAIN_UNIT))
        out[4 * q:4 * q + 4] = bytes((v, v, v, 255))
    return seamless(dn, bytes(out))[0::4]


def _halve_plane(n: int, g: bytes) -> bytes:
    """An n x n one-byte picture at half its size: each pixel the mean of the four under it, rounded half up."""
    h = n // 2
    return bytes((g[2 * j * n + 2 * i] + g[2 * j * n + 2 * i + 1] + g[(2 * j + 1) * n + 2 * i]
                  + g[(2 * j + 1) * n + 2 * i + 1] + 2) // 4 for j in range(h) for i in range(h))


def swatch_pixels(got, read, n: int, zz=None, cache=None) -> tuple[int, bytes, tuple | None]:
    """A palette swatch as the build lays it: (n, its n x n pixels, its grain or None). Its square of its map's
    picture (map_patch, `read` that map pack's members); when it names a detail and `zz` (the game's ZZ_Win.dat) is
    there, that picture averaged over DETAIL_SPLIT (a field's over PICTURE: its rows are finer) and the detail's
    grain (grain_of: (pixels across, its bytes, map units a repeat), the detail laid detail_repeats times across the
    swatch, at the pixels the ground's finest level needs). The grain is laid by itself, unmirrored (Swatch.make):
    baked into the mirrored colour, each mirrored repeat's fold showed as a line (2026-10-16). The Studio's preview
    and the build both make them here."""
    side, px = map_patch(read, got.x, got.y, got.side, got.facing, n, cache)
    if not got.detail or zz is None:
        return side, px, None
    e = zz.entry(got.detail)
    if e is None:  # not a game rule: the palette names a file the game doesn't have
        raise TextureError(f"the game has no texture {got.detail} for the palette's {got.label}")
    split = PICTURE if got.kind == "rows" else DETAIL_SPLIT
    rep = got.side / detail_repeats(got.side, got.detail_side)
    # the game's own mip about as fine as the ground's pixels (a finer one sampled coarser aliases: a kaleidoscope)
    dw, dh, dpx = tgv_rgba(bytes(zz.read(e)), need(rep))
    dn, dpx = square(dw, dh, dpx, need(rep))
    return side, low_pass(side, px, got.side, split), (dn, grain_of(dn, dpx, rep, split), rep)


# --- the named palette (Map Paint plan step 4) -------------------------------------------------------------------
PALETTE_FILE = "ground_presets.toml"   # beside this module: its [themes] table and [[swatch]] tables
SWATCH_KINDS = ("rows", "plain")  # a field's rows (laid turned to run with the field's) or a material with no way


@dataclass(frozen=True)
class PaletteSwatch:
    """One material of a theme's palette: a square of its own map's ground picture (middle x, y and side in map
    units; `facing` the way its rows run, degrees from +x toward +y, for a field), its kind (rows or plain) and why
    that spot (what was measured there). `detail`: the game's own texture its stickers give that ground near the
    camera (a ZZ_Win.dat member) and `detail_side` how big the game lays it (map units): its grain under the
    swatch's colour (with_detail)."""
    theme: str
    name: str
    label: str
    theme_label: str
    map: str
    x: float
    y: float
    side: float
    facing: float = 0.0
    kind: str = "plain"
    why: str = ""
    detail: str = ""
    detail_side: float = 0.0

    @property
    def ref(self) -> str:
        return f"swatch:{self.theme}:{self.name}"


def palette(path=None) -> dict[str, PaletteSwatch]:
    """{ref: PaletteSwatch} of every theme's palette, from the [themes] table ({theme: its label}) and the [[swatch]]
    tables of ground_presets.toml beside this module, in the file's order (TextureError for a swatch that doesn't
    read: its theme listed, a name, a map, a side above 0, a kind of SWATCH_KINDS)."""
    import tomllib
    file = Path(path) if path else Path(__file__).with_name(PALETTE_FILE)
    data = tomllib.loads(file.read_text(encoding="utf-8"))
    themes = {str(k): str(v) for k, v in data.get("themes", {}).items()}
    out: dict[str, PaletteSwatch] = {}
    for k, row in enumerate(data.get("swatch", [])):
        theme, name = str(row.get("theme", "")), str(row.get("name", ""))
        try:
            got = PaletteSwatch(theme, name, str(row.get("label", name)), themes.get(theme, ""), str(row["map"]),
                                float(row["x"]), float(row["y"]), float(row["side"]), float(row.get("facing", 0.0)),
                                str(row.get("kind", "plain")), str(row.get("why", "")), str(row.get("detail", "")),
                                float(row.get("detail_side", 0.0)))
        except (KeyError, TypeError, ValueError):
            got = None
        if (got is None or theme not in themes or not _REF.match(got.ref) or got.kind not in SWATCH_KINDS
                or not got.side > 0.0 or got.ref in out or (got.detail and not got.detail_side > 0.0)):
            raise TextureError(f"{file.name}: swatch {k + 1}: it needs a listed theme, a name (a-z, 0-9, _) not used "
                               f"before in it, a map, x, y, a side above 0, a kind ({' or '.join(SWATCH_KINDS)}) "
                               f"and, with a detail, its detail_side above 0")
        out[got.ref] = got
    return out


# --- the mod's own pictures -------------------------------------------------------------------------------------
def picture_rgba(data: bytes) -> tuple[int, int, bytes]:
    """A PNG's pixels as RGBA (grey, grey + alpha and RGB made RGBA)."""
    from .png import read_png
    w, h, px = read_png(data)
    channels = len(px) // (w * h) if w and h else 0
    if channels == 4:
        return w, h, bytes(px)
    out = bytearray(w * h * 4)
    for k in range(w * h):
        if channels == 3:
            out[4 * k:4 * k + 4] = bytes((px[3 * k], px[3 * k + 1], px[3 * k + 2], 255))
        elif channels == 2:
            g = px[2 * k]
            out[4 * k:4 * k + 4] = bytes((g, g, g, px[2 * k + 1]))
        elif channels == 1:
            g = px[k]
            out[4 * k:4 * k + 4] = bytes((g, g, g, 255))
        else:
            raise TextureError("that picture's pixels can't be read")
    return w, h, bytes(out)


def file_name_ok(name: str) -> bool:
    return bool(_REF.match(f"file:{name}"))


# the sidecar beside a mod's own picture (files/ground/<name>.toml): how much ground the picture covers and whose it is
CREDIT_KEYS = ("source", "author", "licence", "url")
METRES_MOST = 100000.0  # a picture covering more than 100 km isn't a ground texture


def credit_path(picture) -> Path:
    """files/ground/<name>.png -> files/ground/<name>.toml."""
    return Path(picture).with_suffix(".toml")


def read_credit(picture) -> dict:
    """What the sidecar beside a mod's own picture says: {"metres": real metres the picture covers across, "source",
    "author", "licence", "url"}, each as far as it says it (metres only when a number above 0, up to METRES_MOST);
    {} without a sidecar, or one that can't be read."""
    import math
    import tomllib
    try:
        data = tomllib.loads(credit_path(picture).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, TypeError):
        return {}
    out: dict = {}
    m = data.get("metres")
    if isinstance(m, (int, float)) and not isinstance(m, bool) and math.isfinite(m) and 0 < m <= METRES_MOST:
        out["metres"] = float(m)
    for k in CREDIT_KEYS:
        if isinstance(data.get(k), str) and data[k].strip():
            out[k] = data[k].strip()
    return out


def credit_toml(metres: float | None, credit: dict | None) -> str:
    """The sidecar's text: metres (when known) and the credit's source, author, licence and url."""
    import json
    lines = ["# Where this picture comes from and how much ground it covers (rusemod.groundtex.read_credit)"]
    if metres:
        lines.append(f"metres = {float(metres)!r}")
    for k in CREDIT_KEYS:
        v = (credit or {}).get(k)
        v = re.sub(r"[\x00-\x1f\x7f]+", " ", v).strip() if isinstance(v, str) else ""
        if v:
            lines.append(f"{k} = {json.dumps(v, ensure_ascii=False)}")  # (a JSON string without controls is TOML's)
    return "\n".join(lines) + "\n"


def file_period(picture) -> float:
    """Map units one repeat of the mod's own picture covers at its own size: its sidecar's metres, else FILE_PERIOD."""
    m = read_credit(picture).get("metres") if picture is not None else None
    return m * METRE if m else FILE_PERIOD


# --- resolving the strokes' textures, for a build ----------------------------------------------------------------
class Library:
    """Finds and makes the textures a build's strokes name, each once. `zz` and `glad` open the game's ZZ_Win.dat and
    ZZ_GladPatchableWin.dat (an Edat each, or None when not there); `map_reader(pack)` gives a map pack's member
    reader (or None for a map that isn't there); `files` maps a mod's own picture (file:<mod id>/<name>, as the build
    names them) to its path (its sidecar, when it has one, beside it: read_credit). `cache`: groundpaint's."""

    def __init__(self, zz=None, glad=None, map_reader=None, files=None, cache=None, periods=None, swatches=None):
        self.zz, self.glad, self.map_reader, self.files, self.cache = zz, glad, map_reader, files or {}, cache
        self._periods = periods  # (own_periods's answer when it's already known: the Studio's list has it)
        self._palette = swatches  # palette()'s answer (read when first wanted)
        self._made: dict = {}

    def palette_swatch(self, ref: str) -> PaletteSwatch:
        if self._palette is None:
            self._palette = palette()
        got = self._palette.get(ref)
        if got is None:  # not a game rule: the palette's own list
            raise TextureError(f"the palette has no {ref[7:]}")
        return got

    def period_of(self, ref: str) -> float:
        """Map units a texture repeats every at its own size."""
        kind = ref.split(":", 1)[0]
        if kind == "map":
            return MAP_SIDE
        if kind == "swatch":
            return self.palette_swatch(ref).side
        if kind == "file":
            return file_period(self.files.get(ref))  # (its sidecar beside the picture, files/ground/<name>.toml)
        if self._periods is None:
            self._periods = own_periods(self.glad) if self.glad is not None else {}
        return self._periods.get(game_member(ref).lower(), OWN_PERIOD)

    def swatch(self, ref: str, n: int) -> Swatch:
        """The texture `ref` with at least `n` pixels across where it has them (TextureError when it can't be had)."""
        key = (ref, n)
        if key in self._made:
            return self._made[key]
        kind = ref.split(":", 1)[0]
        if kind == "game":
            if self.zz is None:  # not a game rule: the game's file isn't there to read
                raise TextureError("the game's ZZ_Win.dat isn't found, so its ground textures can't be read")
            member = game_member(ref)
            e = self.zz.entry(member)
            if e is None:  # not a game rule: no such file in the game's archive
                raise TextureError(f"the game has no ground texture {ref[5:]}")
            w, h, px = tgv_rgba(bytes(self.zz.read(e)), n)
            side, px = square(w, h, px)
            made = Swatch.make(ref, side, px, self.period_of(ref))
        elif kind == "map":
            _, pack, x, y = ref.split(":")
            read = self.map_reader(pack) if self.map_reader else None
            if read is None:  # not a game rule: the map's file isn't in the game folder
                raise TextureError(f"the map {pack} isn't in this game")
            side, px = map_square(read, float(x), float(y), self.cache)
            made = Swatch.make(ref, side, px, MAP_SIDE)
        elif kind == "swatch":
            got = self.palette_swatch(ref)
            read = self.map_reader(got.map) if self.map_reader else None
            if read is None:  # not a game rule: the map's file isn't in the game folder
                raise TextureError(f"the map {got.map} ({got.theme_label or got.theme}) isn't in this game")
            side, px, grain = swatch_pixels(got, read, min(MOST, max(8, n)), self.zz, self.cache)
            made = Swatch.make(ref, side, px, got.side, mirrored=True, grain=grain)
        elif kind == "file":
            path = self.files.get(ref)
            if path is None or not Path(path).is_file():
                raise TextureError(f"the picture {ref[5:]} isn't in the mod's {GROUND.as_posix()} folder")
            w, h, px = picture_rgba(Path(path).read_bytes())
            side, px = square(w, h, px)
            made = Swatch.make(ref, side, px, self.period_of(ref))
        else:
            raise TextureError(f"texture {ref!r} isn't one this build knows")
        self._made[key] = made
        return made

    def for_strokes(self, strokes: list) -> dict:
        """{ref: Swatch} for every texture stroke, each made big enough for the largest repeat it's laid at."""
        want: dict = {}
        for s in strokes:
            if s.kind.kind == "texture":
                want.setdefault(s.texture, []).append(s.size)
        return {ref: self.swatch(ref, need(max(z if z > 0.0 else self.period_of(ref) for z in sizes)))
                for ref, sizes in want.items()}
