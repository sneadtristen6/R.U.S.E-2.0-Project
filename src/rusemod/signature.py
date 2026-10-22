"""R.U.S.E. 2.0's signature (the owner, 2026-10-22: "the loading screen should have Ruse 2.0 ... we should have a small
encoder ... on everything, including ... studio test builds. Should have this Ruse 2.0. It's one of our signatures"):
every modded copy the apps build shows the title as gold "R.U.S.E. 2.0":

- the main menu's logo (rusemod.menulogo: the 2.0 made from the logo's own letters, centred, gold, its shine kept);
- while a map loads, the title picture (ruse.tgv: the new letters in flat gold, in the picture's own size) and the
  background behind it (its blue turned gold);
- while the game starts, the video (loading.webm): its old letters taken out, R.U.S.E. 2.0 put back from the video's
  own letters, each frame turned gold (the curve he picked: VIDEO_CURVE), encoded again (VP9, through PyAV).

All of it is made on the player's PC from their own game files (nothing of the game's is shipped), the first time
it's needed, and kept in the build cache (only a new game version or a new recipe makes it again). The build puts it
in as changed game files under every mod's: a mod that changes one of the same files has its own used.
Settings in either app can turn it off (the owner, 2026-10-22: "a toggle somewhere in the settings to go back to
generic ruse"): the copy then has the game's own title. A file that isn't the one the title was fitted to (another
game version) is left as the game's, and the build says so."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path

from .gamefiles import GameFile

SETTING = "game_title"           # settings.json: "game" for the game's own title; anything else (or none): ours
TITLE = "R.U.S.E. 2.0 title"     # how the build names it in its lines
RECIPE = 1                       # raised when what's made changes: the cache's old files are then made again
GOLD = (1.0, 0.80, 0.40)         # the menu's gold (rusemod.menulogo.GOLD)
CURVE_BLACK, CURVE_POWER = 12.0, 0.92  # the loading video's gold, his pick ("the darker background ... stronger
#                                        rays. But not the super strong rays"): V = max(r, g, b),
#                                        V' = 255 * (max(0, V - 12) / 243) ^ 0.92, times GOLD

ZZ, COMMON = "ZZ_Win.dat", "Data_Common.dat"
MENU = "gengfx/ww2/resflash/interface_outgame.gpk/gengfx/ww2/resflash/interface_outgame/interface_outgame.gfx"
LOADING = "gen/ww2/res2d/interface/loading/"
PPK = "gen/pack/basesystem3d.ppk/"  # the loading pictures have a second copy in there
VIDEO = "ww2/videos/loading/loading.webm"
# the files the title was fitted to (SHA-256): the menu's logo shapes and the video's letters were measured on these
FITTED = {MENU: "6e3787ec711159f9505fff5f2d64185a6a296fa6aa9007c87a62ab912d8faa24",
          VIDEO: "cbf47c13fd68b5b397ee20ea9982babc85a392eff75685dfb9316374eebab59b"}
VIDEO_LETTERS = (455, 130, 821, 206)  # where the video's R.U.S.E. stands (x0, y0, x1, y1), measured on its pixels
SUPERSAMPLE = 4                       # a letter outline drawn this many times finer, then shrunk: soft edges


def title_on(home: Path | None) -> bool:
    """Whether the copies get R.U.S.E. 2.0's title (the default) or the game's own (Settings)."""
    from .home import settings
    return home is None or settings(home).get(SETTING) != "game"


def keep_title(home: Path, on: bool) -> None:
    """Keep the choice in settings.json, for both apps; the next Play or Test in game builds with it."""
    from .home import save_settings, settings
    values = settings(home)
    if on:
        values.pop(SETTING, None)
    else:
        values[SETTING] = "game"
    save_settings(home, values)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(open_pack, find_pack, pack: str, path: str) -> bytes | None:
    """A game file through the packs it's in (None when it isn't there, or a pack on the way doesn't open)."""
    from .edat import Edat
    where = find_pack(pack)
    if where is None:
        return None
    try:
        arc = open_pack(where)
        parts = path.split("/")
        at = 0
        for k in range(1, len(parts)):
            head = "\\".join(parts[at:k])
            if head.lower().endswith((".ppk", ".gpk")):
                e = arc.entry(head)
                if e is None:
                    return None
                arc, at = Edat(bytes(arc.read(e))), k
        e = arc.entry("\\".join(parts[at:]))
        return bytes(arc.read(e)) if e is not None else None
    except (OSError, ValueError, KeyError):  # (not a pack the title can be read from: it's left as the game's)
        return None


def game_files(open_pack, find_pack, cache: Path | None, say=print) -> list[GameFile]:
    """The title's changed game files for this game, made and kept in `cache` the first time ([GameFile], ours). A
    file that can't be made is left as the game's, with a line saying why."""
    read = lambda pack, path: _read(open_pack, find_pack, pack, path)  # noqa: E731
    out: list[GameFile] = []
    keep = Path(cache) / "signature" if cache is not None else None

    def kept(name: str, make):
        """The file made by `make()`, from the cache when it's there."""
        f = keep / name if keep is not None else None
        if f is not None and f.is_file():
            return f.read_bytes()
        data = make()
        if f is not None:
            f.parent.mkdir(parents=True, exist_ok=True)
            part = f.with_name(f.name + ".part")
            part.write_bytes(data)
            part.replace(f)
        return data

    def give(pack: str, path: str, data: bytes) -> None:
        out.append(GameFile(f"({TITLE})", pack, path, data, False, ours=True))

    menu = read(ZZ, MENU)
    new_menu = None
    if menu is None:
        pass  # (not a whole game: nothing to put the title on)
    elif _sha(menu) != FITTED[MENU]:
        say(f"{TITLE}: the main menu isn't the one it was fitted to, so it keeps the game's title")
    else:
        from . import menulogo
        try:
            new_menu = kept(f"menu-{RECIPE}-{_sha(menu)[:16]}.gfx", lambda: menulogo.two_point_oh(menu, GOLD)[0])
            give(ZZ, MENU, new_menu)
        except ImportError:
            say(f"{TITLE}: the letter maker (shapely) isn't in this install, so the menu keeps the game's title")
        except menulogo.LogoError as exc:
            say(f"{TITLE}: the main menu keeps the game's title ({exc})")
    for name in ("ruse.tgv", "background.tgv"):
        for path in (LOADING + name, PPK + LOADING + name):
            base = read(ZZ, path)
            if base is None or (name == "ruse.tgv" and new_menu is None):
                continue
            try:
                if name == "ruse.tgv":
                    data = kept(f"ruse-{RECIPE}-{_sha(base)[:16]}-{_sha(new_menu)[:16]}.tgv",
                                lambda: title_picture(base, new_menu))
                else:
                    data = kept(f"background-{RECIPE}-{_sha(base)[:16]}.tgv", lambda: gold_background(base))
            except ValueError as exc:
                say(f"{TITLE}: {path} keeps the game's look ({exc})")
                continue
            except ImportError:  # (a run from the source without numpy and Pillow: the installed apps carry both)
                say(f"{TITLE}: {path} keeps the game's look (numpy and Pillow aren't in this install)")
                continue
            give(ZZ, path, data)
    video = read(COMMON, VIDEO)
    if video is None or new_menu is None:
        pass  # (no video, or no menu logo whose letters it's fitted to)
    elif _sha(video) != FITTED[VIDEO]:
        say(f"{TITLE}: the loading video isn't the one it was fitted to, so it keeps the game's")
    else:
        name = f"loading-{RECIPE}-{_sha(video)[:16]}.webm"
        if keep is None or not (keep / name).is_file():
            say(f"{TITLE}: making the gold loading video (once; it's kept for the next builds)…")
        try:
            give(COMMON, VIDEO, kept(name, lambda: gold_video(video, menu)))
        except ImportError:
            say(f"{TITLE}: the video encoder isn't in this install, so the loading video keeps the game's")
    return out


# --- the pictures ---
def _plain_picture(raw: bytes):
    from .tmst import Tgv, zipo_unpack
    import numpy as np
    g = Tgv(raw)
    if not (g.format.upper().startswith("A8R8G8B8") and g.flag == 1 and len(g.mips) == 1):
        raise ValueError(f"not the plain one-level picture it was made for ({g.format})")
    px = np.frombuffer(zipo_unpack(g.payload(0)), np.uint8).reshape(g.height, g.width, 4)
    return g, px


def _picture(g, bgra) -> bytes:
    from .tmst import make_tgv, zipo_pack
    return make_tgv(g.width, g.height, g.format, [zipo_pack(bgra.tobytes())], flag=g.flag)


def video_curve(v):
    """The loading video's gold brightness from max(r, g, b) (his pick)."""
    import numpy as np
    return 255.0 * np.power(np.clip(v - CURVE_BLACK, 0, None) / (255.0 - CURVE_BLACK), CURVE_POWER)


def gold_background(raw: bytes) -> bytes:
    """The loading screen's background (a blue arc) turned gold the way the video is; its alpha kept."""
    import numpy as np
    g, px = _plain_picture(raw)
    v = video_curve(px[..., :3].max(axis=2, keepdims=True).astype(np.float64))
    bgr = np.clip(np.round(v * np.array(GOLD[::-1])), 0, 255)  # stored blue, green, red
    return _picture(g, np.concatenate([bgr, px[..., 3:]], axis=2).astype(np.uint8))


def fill_alpha(area, to_px, size: tuple[int, int], box=None):
    """An area (shapely, even-odd rings) drawn as alpha 0..1 on a picture of `size` (width, height): `to_px(x, y)`
    maps its units to pixels; `box` (x0, y0, x1, y1 in pixels) limits the drawing."""
    import numpy as np
    from PIL import Image, ImageChops, ImageDraw
    w, h = size
    x0, y0, x1, y1 = box or (0, 0, w, h)
    ss = SUPERSAMPLE
    big = Image.new("1", ((x1 - x0) * ss, (y1 - y0) * ss), 0)
    for pg in getattr(area, "geoms", [area]):
        for ring in [pg.exterior, *pg.interiors]:
            layer = Image.new("1", big.size, 0)
            pts = [((to_px(x, y)[0] - x0) * ss, (to_px(x, y)[1] - y0) * ss) for x, y in ring.coords]
            ImageDraw.Draw(layer).polygon(pts, fill=1)
            big = ImageChops.logical_xor(big, layer)
    small = np.asarray(big.convert("L").resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255.0
    out = np.zeros((h, w), np.float32)
    out[y0:y1, x0:x1] = small
    return out


def title_picture(raw: bytes, new_menu: bytes) -> bytes:
    """The loading screen's title picture (flat white letters) as "R.U.S.E. 2.0" in flat gold: the new menu logo's
    letters fitted into the picture's own size (so its place on the screen stays), centred."""
    import numpy as np
    from . import menulogo
    g, _px = _plain_picture(raw)
    area = menulogo.letters(new_menu)
    ax0, ay0, ax1, ay1 = area.bounds
    k = min(g.width / (ax1 - ax0), g.height / (ay1 - ay0))
    ox = (g.width - (ax1 - ax0) * k) / 2 - ax0 * k
    oy = (g.height - (ay1 - ay0) * k) / 2 - ay0 * k
    a = fill_alpha(area, lambda x, y: (ox + x * k, oy + y * k), (g.width, g.height))
    bgra = np.zeros((g.height, g.width, 4), np.uint8)
    bgra[..., 0], bgra[..., 1], bgra[..., 2] = (round(255 * c) for c in GOLD[::-1])
    bgra[..., 3] = np.round(a * 255).astype(np.uint8)
    return _picture(g, bgra)


# --- the video ---
def gold_video(raw: bytes, menu: bytes) -> bytes:
    """The loading video with gold "R.U.S.E. 2.0" (the module's notes), encoded as the game's: VP9, its size, 30
    frames a second, no sound. ImportError when the encoder (PyAV) isn't installed."""
    import av
    import numpy as np
    from . import menulogo
    src = av.open(io.BytesIO(raw))
    stream = src.streams.video[0]
    rate = stream.average_rate or 30
    alpha = None
    frames = []
    for fr in src.decode(stream):
        rgb = fr.to_ndarray(format="rgb24")
        if alpha is None:
            h, w = rgb.shape[:2]
            x0, y0, x1, y1 = VIDEO_LETTERS
            kx, ky = (x1 - x0) / menulogo.E_BOX[1], (y1 - y0) / (menulogo.BOTTOM - menulogo.TOP)
            alpha = fill_alpha(menulogo.letters(menu), lambda x, y: (x0 + x * kx, y0 + y * ky), (w, h),
                               (x0 - 8, y0 - 8, x1 + 8, y1 + 8))
        frames.append(_frame(rgb, alpha, kx, ky))
    src.close()
    buf = io.BytesIO()
    dst = av.open(buf, "w", format="webm")
    st = dst.add_stream("libvpx-vp9", rate=rate)
    st.width, st.height, st.pix_fmt = frames[0].shape[1], frames[0].shape[0], "yuv420p"
    st.options = {"crf": "28", "b": "0", "row-mt": "1", "cpu-used": "4"}
    for f in frames:
        for pkt in st.encode(av.VideoFrame.from_ndarray(f, format="rgb24")):
            dst.mux(pkt)
    for pkt in st.encode():
        dst.mux(pkt)
    dst.close()
    return buf.getvalue()


def _fill_in(img, hole, box, rounds=300):
    """The hole's pixels (inside `box`) replaced by repeated averaging of their neighbours: the rays' glow carried
    in where the old letters stood."""
    import numpy as np
    x0, y0, x1, y1 = box
    sub = img[y0:y1, x0:x1].astype(np.float32)
    m = hole[y0:y1, x0:x1]
    if (~m).any():
        sub[m] = sub[~m].mean(axis=0)
    for _ in range(rounds):
        avg = (np.roll(sub, 1, 0) + np.roll(sub, -1, 0) + np.roll(sub, 1, 1) + np.roll(sub, -1, 1)) / 4
        sub[m] = avg[m]
    out = img.copy()
    out[y0:y1, x0:x1] = sub
    return out


def _edge_colour(rgb, alpha, box):
    """The letters' soft edge pixels given the colour of the solid letter next to them (in the video they're half
    the old background, which shows as a fringe once a letter sits on another spot)."""
    import numpy as np
    x0, y0, x1, y1 = box
    col = rgb[y0:y1, x0:x1].astype(np.float32)
    known = alpha[y0:y1, x0:x1] >= 0.98
    for _ in range(4):
        total = np.zeros_like(col)
        count = np.zeros(known.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = np.roll(known, (dy, dx), (0, 1))
            total += np.roll(col, (dy, dx), (0, 1)) * k[..., None]
            count += k
        grow = (~known) & (count > 0)
        col[grow] = total[grow] / count[grow][:, None]
        known = known | grow
    out = rgb.copy()
    out[y0:y1, x0:x1] = np.clip(col, 0, 255).astype(np.uint8)
    return out


def _row_light(rgb, alpha):
    """The letters' lighting at each height of the frame: the middle colour of their solid pixels in that row (rims
    left out, 3 px in); rows without any take the nearest row's."""
    import numpy as np
    solid = alpha >= 0.98
    inner = solid.copy()
    for d in (1, 2, 3):
        inner &= np.roll(solid, d, 0) & np.roll(solid, -d, 0) & np.roll(solid, d, 1) & np.roll(solid, -d, 1)
    rows = np.nonzero(inner.any(axis=1))[0]
    have = np.array([np.median(rgb[y][inner[y]], axis=0) for y in rows], np.float32)
    ys = np.arange(rgb.shape[0])
    return np.stack([np.interp(ys, rows, have[:, c]) for c in range(3)], axis=1)


def _place(dest, src, box_px, at_px, mirror=False, flip=False, stretch=None):
    """Copy the letters' RGBA from `box_px` of `src` to `at_px` of `dest`, mirrored, flipped, or with a stretch
    (x0, x1 inside the piece, its new width)."""
    from PIL import Image
    x0, y0, x1, y1 = box_px
    piece = src.crop((round(x0), round(y0), round(x1), round(y1)))
    if mirror:
        piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
    if flip:
        piece = piece.transpose(Image.FLIP_TOP_BOTTOM)
    if stretch:
        a, b, new_w = stretch
        left = piece.crop((0, 0, a, piece.height))
        mid = piece.crop((a, 0, b, piece.height)).resize((max(1, round(new_w)), piece.height), Image.LANCZOS)
        right = piece.crop((b, 0, piece.width, piece.height))
        whole = Image.new("RGBA", (left.width + mid.width + right.width, piece.height))
        whole.paste(left, (0, 0))
        whole.paste(mid, (left.width, 0))
        whole.paste(right, (left.width + mid.width, 0))
        piece = whole
    dest.alpha_composite(piece, (round(at_px[0]), round(at_px[1])))


def _flipped_relit(letters, light, box_px, dest_y, mirror):
    """The piece at `box_px` turned upside down for `dest_y`, each row moved from the lighting of the height it came
    from to that of the height it lands at (the chrome is bright on top, dark at the foot)."""
    import numpy as np
    from PIL import Image
    x0, y0, x1, y1 = (round(v) for v in box_px)
    arr = np.asarray(letters.crop((x0, y0, x1, y1))).astype(np.float32)[::-1]
    dy = round(dest_y)
    src_rows = np.arange(y1 - 1, y0 - 1, -1)
    dst_rows = np.clip(np.arange(dy, dy + arr.shape[0]), 0, light.shape[0] - 1)
    arr[..., :3] += (light[dst_rows] - light[src_rows])[:, None, :]
    piece = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    if mirror:
        piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
    return piece, dy


def _frame(rgb, alpha, kx, ky):
    """One frame: the old letters out, R.U.S.E. 2.0 in from the frame's own letters, then gold."""
    import numpy as np
    from PIL import Image
    from . import menulogo as M
    h, w = alpha.shape
    X0, Y0, X1, Y1 = VIDEO_LETTERS
    edged = _edge_colour(rgb, alpha, (X0 - 6, Y0 - 6, X1 + 6, Y1 + 6))
    letters = Image.fromarray(np.dstack([edged, (alpha * 255).astype(np.uint8)]), "RGBA")
    light = _row_light(rgb, alpha)
    hole = alpha > 0.02
    hole = hole | np.roll(hole, 2, 0) | np.roll(hole, -2, 0) | np.roll(hole, 2, 1) | np.roll(hole, -2, 1)
    back = _fill_in(rgb.astype(np.float32), hole, (X0 - 12, Y0 - 12, X1 + 12, Y1 + 12))
    canvas = Image.fromarray(np.clip(back, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    px = lambda ux: X0 + ux * kx  # noqa: E731  logo units -> frame pixels
    py = lambda uy: Y0 + uy * ky  # noqa: E731
    lay = M.layout()
    shift = lay["shift"]
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    top, bottom = py(M.TOP) - 3, py(M.BOTTOM) + 3
    # R.U.S.E., moved
    _place(layer, letters, (px(-2), top, px(M.E_BOX[1] + 2), bottom), (px(-2 + shift), top))
    # "2": the S mirrored above the cut (its bottom-bar upturn left out), then the E's bottom band stretched
    s0, s1 = px(M.S_BOX[0]) - 1, px(M.S_BOX[1]) + 1
    two_x = px(lay["x_two"] + shift) - 1
    keep = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _place(keep, letters, (s0, top, s1, py(M.CUT)), (two_x, top), mirror=True)
    ka = np.asarray(keep).copy()
    ka[round(py(M.MID_BAR_BOTTOM)):round(py(M.CUT)) + 1, round(px(lay["x_two"] + shift + M.UPRIGHT_KEEP)):, 3] = 0
    layer.alpha_composite(Image.fromarray(ka, "RGBA"))
    e0, e1 = px(M.E_BOX[0]) - 1, px(M.E_BOX[1]) + 1
    a, b = px(M.E_STRETCH[0]) - e0, px(M.E_STRETCH[1]) - e0
    grow = (M.S_BOX[1] - M.S_BOX[0] - (M.E_BOX[1] - M.E_BOX[0])) * kx
    _place(layer, letters, (e0, py(M.CUT), e1, bottom), (two_x, py(M.CUT)), stretch=(round(a), round(b), (b - a) + grow))
    # "0": the U's bottom-left quarter four ways, the top two relit for the height they land at
    cx, cy = M.U_MID
    q = (px(M.U_BOX[0]) - 1, py(cy), px(cx), bottom)
    qw, qh = q[2] - q[0], q[3] - q[1]
    zx = px(lay["x_zero"] + shift) - 1
    _place(layer, letters, q, (zx, py(cy)))
    _place(layer, letters, q, (zx + qw, py(cy)), mirror=True)
    for dx, mirror in ((0, False), (qw, True)):
        piece, dy = _flipped_relit(letters, light, q, py(cy) - qh, mirror)
        layer.alpha_composite(piece, (round(zx + dx), dy))
    canvas.alpha_composite(layer)
    out = np.asarray(canvas.convert("RGB")).astype(np.float32)
    v = video_curve(out.max(axis=2, keepdims=True))
    return np.clip(v * np.array(GOLD), 0, 255).astype(np.uint8)
