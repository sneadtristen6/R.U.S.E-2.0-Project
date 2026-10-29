"""R.U.S.E. 2.0's signature (the owner, 2026-10-22: "the loading screen should have Ruse 2.0 ... we should have a small
encoder ... on everything, including ... studio test builds. Should have this Ruse 2.0. It's one of our signatures"):
every modded copy the apps build shows the title as gold "R.U.S.E. 2.0":

- the main menu's logo (rusemod.menulogo: the 2.0 made from the logo's own letters, centred, gold, its shine kept),
  the small logo on the other screens as R.U.S.E. 2.0 too (small_logo_picture), and every white or grey outline in
  the menus in the same gold (the movie's lines, the frame lines drawn into its pictures: gold_frames);
- the menus' loading popup (it shows as the intro ends, just before the main menu) in our style: the start-up
  screen's still (title_still), its spinning globe and its text hidden;
- the game's own loading screen's "LOADING" and tip in gold (gold_loading_screen);
- before the game starts, in place of the company logo video, our intro: the start-up video below, with an engine
  turning over and starting as its sound;
- while a map loads, the title picture (ruse.tgv: the new letters in flat gold, in the picture's own size) and the
  background behind it (its blue turned gold);
- while the game starts, the video (loading.webm): our battle scene held still behind the gold R.U.S.E. 2.0, made
  from the video's own letters, with a glow breathing to the video's own light (notes at gold_video), encoded again
  (VP9, through PyAV).

All of it is made on the player's PC from their own game files (nothing of the game's is shipped; the scene is our
own picture), the first time it's needed, and kept in the build cache (only a new game version or a new recipe makes
it again). The build puts it
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
RECIPE = 7                       # raised when what's made changes: the cache's old files are then made again
#                                  (2: the start-up video over the battle scene; the menus' hover frames gold;
#                                  3: every grey or white outline in the menus gold, the intro in the logo video's place;
#                                  4: the intro's sound, an engine starting; 5: the intro over the battle scene, the
#                                  sub-menus' small logo R.U.S.E. 2.0; 6: the loading popup before the main menu as
#                                  the start-up screen, the game's loading screen's "LOADING" and tip gold; 7: those
#                                  colours in the game's byte order, blue first)
GOLD = (1.0, 0.80, 0.40)         # the menu's gold (rusemod.menulogo.GOLD)
CURVE_BLACK, CURVE_POWER = 12.0, 0.92  # the loading video's gold, his pick ("the darker background ... stronger
#                                        rays. But not the super strong rays"): V = max(r, g, b),
#                                        V' = 255 * (max(0, V - 12) / 243) ^ 0.92, times GOLD

ZZ, COMMON, GLAD = "ZZ_Win.dat", "Data_Common.dat", "ZZ_GladNotPatchableWin.dat"
OUTGAME = "gengfx/ww2/resflash/interface_outgame.gpk"   # the menus' movie and its pictures
MENU = OUTGAME + "/gengfx/ww2/resflash/interface_outgame/interface_outgame.gfx"
LOADING = "gen/ww2/res2d/interface/loading/"
PPK = "gen/pack/basesystem3d.ppk/"  # the loading pictures have a second copy in there
VIDEO = "ww2/videos/loading/loading.webm"
INTRO = "ww2/videos/logo/eugen.webm"   # the company logo before it: our intro in its place (with_sound)
# the game's own loading screen (drawn by the game, not the menus): its parts and their text styles
LOADING_SCREEN = "genglad/nonpatchable/system3d/visualdebuginfohandler.cpp.gladndfbin"   # in GLAD
# the files the title was fitted to (SHA-256): the menu's logo shapes and the video's letters were measured on these
FITTED = {MENU: "6e3787ec711159f9505fff5f2d64185a6a296fa6aa9007c87a62ab912d8faa24",
          VIDEO: "cbf47c13fd68b5b397ee20ea9982babc85a392eff75685dfb9316374eebab59b",
          LOADING_SCREEN: "1e6b56c9955b5e4bb111a9e642077eec45d1f41afef3f24b0ad4d9af4198fa85"}
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

    def give(pack: str, path: str, data: bytes, added: bool = False) -> None:
        out.append(GameFile(f"({TITLE})", pack, path, data, added, ours=True))

    menu = read(ZZ, MENU)
    video = read(COMMON, VIDEO)
    # the loading popup's backdrop is the start-up screen's still: only when that can be made here
    still = video is not None and _sha(video) == FITTED[VIDEO] and _can_encode()
    new_menu = small = None
    if menu is None:
        pass  # (not a whole game: nothing to put the title on)
    elif _sha(menu) != FITTED[MENU]:
        say(f"{TITLE}: the main menu isn't the one it was fitted to, so it keeps the game's title")
    else:
        from . import menulogo
        small = _in_pack(read(ZZ, OUTGAME), SMALL)
        try:
            new_menu = kept(f"menu-{RECIPE}-{_sha(menu)[:16]}{'-still' if still else ''}.gfx",
                            lambda: _new_menu(menu, small, still))
            give(ZZ, MENU, new_menu)
        except ImportError:
            say(f"{TITLE}: the letter maker (shapely) isn't in this install, so the menu keeps the game's title")
        except menulogo.LogoError as exc:
            say(f"{TITLE}: the main menu keeps the game's title ({exc})")
    if new_menu is not None:  # the frame lines drawn into the menus' pictures, gold like the menus' outlines
        for path, data in _menu_frames(read(ZZ, OUTGAME), kept):
            give(ZZ, f"{OUTGAME}/{path}", data)
        if small is not None and _small_made(new_menu):   # the sub-menus' small logo, its picture
            give(ZZ, f"{OUTGAME}/{SMALL}", kept(f"small-{RECIPE}-{_sha(small)[:16]}-{_sha(new_menu)[:16]}.tgv",
                                                lambda: small_logo_picture(small, new_menu)))
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
    if video is None or new_menu is None:
        pass  # (no video, or no menu logo whose letters it's fitted to)
    elif _sha(video) != FITTED[VIDEO]:
        say(f"{TITLE}: the loading video isn't the one it was fitted to, so it keeps the game's")
    else:
        name = f"loading-{RECIPE}-{_sha(video)[:16]}.webm"
        if keep is None or not (keep / name).is_file():
            say(f"{TITLE}: making the start-up video (once; it's kept for the next builds)…")
        try:
            start_up = kept(name, lambda: gold_video(video, menu))
            give(COMMON, VIDEO, start_up)
            if read(COMMON, INTRO) is not None:  # (a game without the company logo video: nothing in its place)
                give(COMMON, INTRO, kept(f"intro-{RECIPE}-{_sha(start_up)[:16]}.webm", lambda: with_sound(start_up)))
            if still:   # the loading popup's backdrop, a picture the menus' pack hasn't got: added to it
                give(ZZ, f"{OUTGAME}/{BACKDROP}", kept(f"backdrop-{RECIPE}-{_sha(video)[:16]}.tgv",
                                                       lambda: backdrop_picture(title_still(video, menu))), added=True)
        except ImportError:
            say(f"{TITLE}: the video encoder isn't in this install, so the videos keep the game's")
    screen = read(GLAD, LOADING_SCREEN)
    if screen is not None and _sha(screen) == FITTED[LOADING_SCREEN]:   # (another version: the game's, unsaid)
        give(GLAD, LOADING_SCREEN, kept(f"loadingscreen-{RECIPE}-{_sha(screen)[:16]}.gladndfbin",
                                        lambda: gold_loading_screen(screen)))
    return out


# The game's own loading screen (the owner, 2026-10-22: "loading and the tip ... pop up just before it switches to
# [the R.U.S.E.] 2.0 menu is not gold"): the game draws it itself over the start-up video, before the main menu and
# while a map loads, its "LOADING" word (TLoadingScreenElementDicMessage, light grey 200) and its tip
# (TLoadingScreenElementTotd, white; its text style also draws the version text) in the text styles they name. Their
# colours (top and bottom of the letters) times GOLD, as the menus' outlines, so their shades stay apart. A colour is
# stored blue, green, red, alpha: seen in game 2026-10-22, when gold written red first showed as light blue.
LOADING_TEXTS = ("TLoadingScreenElementDicMessage", "TLoadingScreenElementTotd")


def gold_loading_screen(raw: bytes) -> bytes:
    """The loading screen's game data file with its "LOADING" and tip text styles gold. ValueError when it doesn't
    have the two styles it was made for."""
    import struct
    from .ndf import Ndf
    ndf = Ndf(raw)
    styles = set()
    for o in ndf.objects:
        if ndf.classes[o.cls] in LOADING_TEXTS:
            for pi, v in o.props:   # a link to an object of this file: 0xBBBBBBBB, its number, ...
                if ndf.prop_name(pi) == "TextStyle" and v.tc == 0x09 and v.payload[:4] == b"\xbb" * 4:
                    styles.add(struct.unpack_from("<I", v.payload, 4)[0])
    changed = 0
    for s in sorted(styles):
        for pi, v in ndf.objects[s].props:
            if ndf.prop_name(pi) in ("ColorUp", "ColorBottom") and v.tc == 0x0D:   # blue, green, red, alpha
                v.payload = bytes([round(c * k) for c, k in zip(v.payload[:3], GOLD[::-1])]) + v.payload[3:]
                changed += 1
    if len(styles) != 2 or changed != 4:
        raise ValueError(f"the loading screen's text styles aren't the ones it was made for ({len(styles)} styles, "
                         f"{changed} colours)")
    return ndf.to_member()


def _can_encode() -> bool:
    try:
        import av  # noqa: F401
        return True
    except ImportError:
        return False


def _new_menu(menu: bytes, small: bytes | None, still: bool = False) -> bytes:
    """The menu movie with the title: the main logo (menulogo.two_point_oh); the small logo's shape made for its
    wider picture, drawn as wide as the old one was (the owner's pick, 2026-10-22: "C: today's width", of the three
    sizes he saw in his lobby; the bigger ones run into the lobby's map picture), unless its picture isn't the plain
    one it was made for; with `still`, the loading popup before the main menu as the start-up screen's still, nothing
    on it (menulogo.our_loading_popup)."""
    from . import menulogo
    from .tmst import Tgv
    out = menulogo.two_point_oh(menu, GOLD)[0]
    if small is not None:
        try:
            width = Tgv(small_logo_picture(small, out)).width
        except ValueError:
            width = None
        if width is not None:
            out = menulogo.small_logo(out, width, menulogo.SMALL_W / width)[0]
    return menulogo.our_loading_popup(out)[0] if still else out


def _small_made(new_menu: bytes) -> bool:
    """Whether the movie's small logo was made for the wider picture (its picture's size no longer the game's)."""
    import struct
    from . import menulogo
    for code, body, _long in menulogo.read_tags(new_menu, menulogo.tags_start(new_menu), len(new_menu)):
        if code == 1001 and struct.unpack_from("<H", body, 0)[0] == menulogo.SMALL_IMAGE:
            return struct.unpack_from("<H", body, 4)[0] != menulogo.SMALL_W
    return False


def _in_pack(gpk: bytes | None, path: str) -> bytes | None:
    """A file inside a pack held in memory (the menus' pack), or None."""
    from .edat import Edat
    if gpk is None:
        return None
    arc = Edat(gpk)
    for e in arc.entries:
        if e.path.replace("\\", "/").lower() == path:
            return bytes(arc.read(e))
    return None


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


def _frame_lines(px):
    """Which pixels of a picture (h, w, 4: any order of colour channels, then alpha) are its frame lines: bright grey
    pixels (each channel within 10, at least 120, mostly opaque) in rows or columns of its outer 3 pixels where they
    run along at least half that edge, at most 3 rows or columns thick (the lobby's panels: a 1 px 238 grey line)."""
    import numpy as np
    c = px[..., :3].astype(np.int16)
    grey = (c.max(axis=2) - c.min(axis=2) <= 10) & (c.max(axis=2) >= 120) & (px[..., 3] >= 128)
    h, w = grey.shape
    mask = np.zeros_like(grey)
    for along, count in ((1, h), (0, w)):   # runs along a row, then along a column
        full = np.nonzero(grey.sum(axis=along) >= 0.5 * (w if along == 1 else h))[0]
        groups = np.split(full, np.nonzero(np.diff(full) != 1)[0] + 1) if len(full) else []
        for g in groups:
            if len(g) <= 3 and (g[0] <= 3 or g[-1] >= count - 4):
                if along == 1:
                    mask[g, :] |= grey[g, :]
                else:
                    mask[:, g] |= grey[:, g]
    return mask


# Only the menus' own look goes gold (the owner, 2026-10-22: "Don't change the actual in-game, like, troop selection
# buttons. I just want the menu aesthetic to be gold"): panels, banners and bars, at least this long on their long
# side; the unit buttons (120 x 64), unit-type icons (52 x 52), flags (135 x 121), small markers and logos are smaller
FRAME_PICTURE_MIN = 300


def gold_frames(raw: bytes) -> bytes:
    """A menu picture with its frame lines (_frame_lines) in gold (times GOLD, so their shading stays); b"" when it has
    none or is smaller than FRAME_PICTURE_MIN on its long side. ValueError when it isn't a plain one-level picture."""
    import numpy as np
    g, px = _plain_picture(raw)
    if max(px.shape[:2]) < FRAME_PICTURE_MIN:
        return b""
    mask = _frame_lines(px)
    if not mask.any():
        return b""
    out = px.astype(np.float32)
    out[..., :3][mask] *= np.array(GOLD[::-1])   # stored blue, green, red
    return _picture(g, np.clip(np.round(out), 0, 255).astype(np.uint8))


def _menu_frames(gpk: bytes | None, kept):
    """(path in the menus' pack, picture) for each of its pictures with frame lines, made gold (kept in the cache)."""
    from .edat import Edat
    if gpk is None:
        return []
    out = []
    arc = Edat(gpk)
    for e in arc.entries:
        if not e.path.lower().endswith(".tgv"):
            continue
        raw = bytes(arc.read(e))
        try:
            data = kept(f"frame-{RECIPE}-{_sha(raw)[:16]}.tgv", lambda: gold_frames(raw))
        except (ValueError, ImportError):  # (not a plain picture; or no numpy: the installed apps carry it)
            continue
        if data:
            out.append((e.path.replace("\\", "/"), data))
    return out


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


# The sub-menus' small logo (the owner, 2026-10-22: "all these screens should have Ruse 2.0"): a picture in the menus'
# pack (white letters with a dark shadow down and to the right, 258 x 53; shape 387 fills with it, sprite 388 places
# that on 24 screens). Its R.U.S.E. stays as it is; the main logo's new "2.0" is drawn after it the same way, measured
# by matching the main logo's letters to the picture's (scratch small_shadow.py): SMALL_SCALE pixels per unit across
# and down from SMALL_AT, the shadow the letters moved SMALL_SHADOW[:2] pixels, blurred SMALL_SHADOW[2], in a colour
# SMALL_SHADOW[3] of white, opaque.
SMALL = "gen/ww2/resflash/interface_outgame/interface_outgame_i182.tgv"   # in OUTGAME
# the loading popup's picture (menulogo.our_loading_popup), a new one in OUTGAME: menulogo.backdrop_file() as stored
BACKDROP = "gen/ww2/resflash/interface_outgame/interface_outgame_i977.tgv"
SMALL_SCALE, SMALL_AT, SMALL_SHADOW = (0.27883, 0.28251), (0.5, 0.25), (1.5, 1.5, 0.4, 0.08)


def small_logo_picture(raw: bytes, new_menu: bytes) -> bytes:
    """The small logo picture as "R.U.S.E. 2.0": wider, its own R.U.S.E. pixels kept, the new letters after them
    (the notes above). ValueError when it isn't a plain one-level picture."""
    import math

    import numpy as np
    from . import menulogo
    g, px = _plain_picture(raw)
    area = menulogo.letters(new_menu)
    two = area.intersection(menulogo.box(menulogo.END_OF_RUSE + 1, -1e4, 1e5, 1e4))   # the new letters only
    (kx, ky), (ox, oy), (dx, dy, soft, dark) = SMALL_SCALE, SMALL_AT, SMALL_SHADOW
    width = math.ceil(ox + area.bounds[2] * kx + dx + 1)
    letters = fill_alpha(two, lambda x, y: (ox + x * kx, oy + y * ky), (width, g.height))
    shadow = _blur(fill_alpha(two, lambda x, y: (ox + dx + x * kx, oy + dy + y * ky), (width, g.height)), soft)
    new_a = letters + shadow * (1 - letters)
    new_c = (letters + shadow * (1 - letters) * dark) * 255     # (premultiplied)
    old = np.zeros((g.height, width, 4), np.float32)
    old[:, :g.width] = px
    old_a = old[..., 3:] / 255
    alpha = new_a[..., None] + old_a * (1 - new_a[..., None])   # the new letters laid over the picture
    colour = (new_c[..., None] + old[..., :3] * old_a * (1 - new_a[..., None])) / np.maximum(alpha, 1e-6)
    bgra = np.round(np.concatenate([np.clip(colour, 0, 255), alpha * 255], axis=2)).astype(np.uint8)
    untouched = np.round(new_a * 255) == 0      # (there the picture's own pixels, exactly)
    bgra[untouched] = old[untouched].astype(np.uint8)
    from .tmst import make_tgv, zipo_pack
    return make_tgv(width, g.height, g.format, [zipo_pack(bgra.tobytes())], flag=g.flag)


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
# The start-up video (the owner's pick, 2026-10-22: "It looks good", the third strength he saw): the battle scene
# (pictures/startup_scene.png, our own render of 14 CC-BY models, THIRD_PARTY_NOTICES) held still behind; the gold
# R.U.S.E. 2.0 over it, made from the video's own letters each frame; a dark edge round each letter and a soft dark
# plate behind the word; a deep amber glow round the word and a short flare, breathing with the game video's own
# light round its letters (measured each frame on the player's copy: dark, three swells, dark again, so it loops); the
# title's light on the water; a shine crossing the letters at each swell's peak.
SCENE = "startup_scene.png"     # in rusemod/pictures: 1280 x 720, the size of the game's video
HORIZON = 233                   # the scene's horizon row
AMBER, RED_AMBER = (1.0, 0.52, 0.14), (0.85, 0.32, 0.07)   # the glow's colours: deeper than the letters' gold
PLATE, EDGE, GLOW_GAIN, FLARE, WATER = 0.35, 0.6, 1.1, 0.7, 70.0   # his "dull back a little bit" strengths
# the letters: their red at the top of a swell (measured on the clip he picked: 220-224), and how far they dim
# between swells (to 86 %, following the video's own letters' light; the video's own swing, 151..207, is wider)
LETTER_RED, LETTER_LOW = 220.0, 0.86
# and how much their brightness varies inside them: a steady part of it (the red's spread over its mean, measured on
# that clip: 0.093-0.098; the video's chrome left as it is varies 2-3.6 times as much, harder than what he picked)
LETTER_CONTRAST = 0.097
# The intro in place of the game's company logo video (the owner, 2026-10-22: "It still shows the [Eugen] logo ... You
# should replace the [Eugen] screen with [R.U.S.E.] 2.0", then of the title on black: "why is the battle scene not on
# the first screen?"): the start-up video itself, with a sound (with_sound).
# Its sound in place of the logo video's (the owner, 2026-10-22: the engine where it "turns over once or twice then
# starts" ... "The first clip is perfect"): his bf109start, 7.5 s from its second turn-over (it catches 4.1 s in, near
# the title's brightest swell), at the level of the game's own logo sound (RMS -20 dBFS, peaks under -1 dBFS), in
# rusemod/sounds as Vorbis 48 kHz stereo like the game's, and copied into the intro as it is (not encoded again).
INTRO_SOUND = "bf109start.ogg"


def gold_video(raw: bytes, menu: bytes) -> bytes:
    """The start-up video (the notes above), encoded as the game's: VP9, its size, its 30 frames a second, no sound.
    Two passes over the game's video (its light first, then each frame), so its frames aren't all held at once.
    ImportError when the encoder (PyAV) isn't installed."""
    import av
    frames, look, made, swell, peaks, lit = _title_parts(raw, menu)
    h, w = look["alpha"].shape
    src = av.open(io.BytesIO(raw))
    rate = src.streams.video[0].average_rate or 30
    src.close()
    buf = io.BytesIO()
    dst = av.open(buf, "w", format="webm")
    st = dst.add_stream("libvpx-vp9", rate=rate)
    st.width, st.height, st.pix_fmt = w, h, "yuv420p"
    st.options = {"crf": "26", "b": "0", "row-mt": "1", "cpu-used": "4"}
    for f, rgb in enumerate(frames()):
        frame = _video_frame(look, made(rgb), swell[f], lit[f], _shine(look, peaks, f))
        for pkt in st.encode(av.VideoFrame.from_ndarray(frame, format="rgb24")):
            dst.mux(pkt)
    for pkt in st.encode():
        dst.mux(pkt)
    dst.close()
    return buf.getvalue()


def title_still(raw: bytes, menu: bytes):
    """The start-up screen at its brightest (the frame the swell peaks highest), without the shine crossing it: the
    menus' loading popup (the owner, 2026-10-22: "Just make the loading thing gold. And in our style" ... "I don't
    want the ... world logo randomly in the middle of the screen and the loading"). RGB, the video's size.
    ImportError without PyAV."""
    import itertools

    import numpy as np
    frames, look, made, swell, _peaks, lit = _title_parts(raw, menu)
    f = int(np.argmax(swell))
    rgb = next(itertools.islice(frames(), f, None))
    return _video_frame(look, made(rgb), swell[f], lit[f], np.zeros(look["alpha"].shape, np.float32))


def backdrop_picture(still) -> bytes:
    """The loading popup's backdrop picture (menulogo.BACKDROP_SIZE) from the still, as the menus' own pictures are
    stored (A8R8G8B8, one level, opaque)."""
    import numpy as np
    from . import menulogo
    from .tmst import make_tgv, zipo_pack
    w, h = menulogo.BACKDROP_SIZE
    if still.shape[:2] != (h, w):
        raise ValueError(f"the still is {still.shape[1]} x {still.shape[0]}, not {w} x {h}")
    bgra = np.dstack([still[..., 2], still[..., 1], still[..., 0], np.full((h, w), 255, np.uint8)])
    return make_tgv(w, h, "A8R8G8B8_LIN", [zipo_pack(np.ascontiguousarray(bgra).tobytes())], flag=1)


def _title_parts(raw: bytes, menu: bytes):
    """What the start-up screen is made from, out of the game's own video: (a function giving its frames again, the
    title's look, the new letters made from a frame, the swell, its peaks, the letters' light)."""
    import av
    from . import menulogo

    def frames():
        src = av.open(io.BytesIO(raw))
        try:
            yield from (fr.to_ndarray(format="rgb24") for fr in src.decode(src.streams.video[0]))
        finally:
            src.close()

    # the light round the old letters, frame by frame (the original's timing)
    first = next(frames())
    h, w = first.shape[:2]
    x0, y0, x1, y1 = VIDEO_LETTERS
    kx, ky = (x1 - x0) / menulogo.E_BOX[1], (y1 - y0) / (menulogo.BOTTOM - menulogo.TOP)
    old = menulogo.letters(menu)
    alpha = fill_alpha(old, lambda x, y: (x0 + x * kx, y0 + y * ky), (w, h), (x0 - 8, y0 - 8, x1 + 8, y1 + 8))
    swell, peaks, lit = _swell(frames(), alpha)
    # the video squeezes the logo's letters (its R.U.S.E. is 4.82 times as wide as high, the logo's own 5.09): the
    # new letters widened back to the logo's proportions, as on the main menu
    ox0, oy0, ox1, oy1 = old.bounds
    widen = ((ox1 - ox0) / (oy1 - oy0)) / ((x1 - x0) / (y1 - y0))
    made = lambda rgb: _widened(_letters(rgb, alpha, kx, ky), widen)  # noqa: E731
    # the title's look over the scene, from the new letters' outline
    look = _title_look(made(first)[..., 3] / 255.0)
    return frames, look, made, swell, peaks, lit


def with_sound(video: bytes) -> bytes:
    """The intro: the start-up video's pictures with INTRO_SOUND as its sound, both copied in as they are (nothing
    encoded again). ImportError when PyAV isn't installed."""
    from importlib import resources

    import av
    src = av.open(io.BytesIO(video))
    sound = av.open(io.BytesIO((resources.files(__package__) / "sounds" / INTRO_SOUND).read_bytes()))
    buf = io.BytesIO()
    dst = av.open(buf, "w", format="webm")
    try:
        # both tracks added before the first packet (the file's header names them); the pictures' made as
        # gold_video's, so the header keeps their frame length as the game's own videos do
        v = src.streams.video[0]
        picture = dst.add_stream("libvpx-vp9", rate=v.average_rate)
        picture.width, picture.height, picture.pix_fmt = v.width, v.height, "yuv420p"
        pairs = [(src, v), (sound, sound.streams.audio[0])]
        tracks = [picture, dst.add_stream_from_template(sound.streams.audio[0])]
        for (f, stream), track in zip(pairs, tracks):
            for pkt in f.demux(stream):
                if pkt.dts is not None and pkt.size:
                    pkt.stream = track
                    dst.mux(pkt)
    finally:
        dst.close()
        src.close()
        sound.close()
    return buf.getvalue()


def _swell(frames, alpha):
    """For each frame: how bright the light round the old letters is, 0 (its darkest) .. 1 (its brightest); the
    frames where it peaks (the swells); how bright the letters themselves are, LETTER_LOW .. 1."""
    import numpy as np
    near = _grow(alpha > 0.1, 30) & ~_grow(alpha > 0.1, 2)
    inside = alpha > 0.9
    light, letters = [], []
    for rgb in frames:
        v = rgb.max(axis=2)
        light.append(v[near].mean())
        letters.append(v[inside].mean())
    light, letters = np.array(light), np.array(letters)
    swell = (light - light.min()) / max(float(light.max() - light.min()), 1e-6)
    peaks = [f for f in range(3, len(swell) - 3) if swell[f] == swell[f - 3:f + 4].max() and swell[f] > 0.6]
    lit = LETTER_LOW + (1 - LETTER_LOW) * (letters - letters.min()) / max(float(letters.max() - letters.min()), 1e-6)
    return swell, peaks, lit


def _widened(layer, k):
    """The letters' RGBA stretched sideways by `k` about their middle."""
    import numpy as np
    from PIL import Image
    xs = np.nonzero(layer[..., 3].max(axis=0) > 0)[0]
    cx = (xs.min() + xs.max() + 1) / 2
    im = Image.fromarray(layer, "RGBA")
    return np.asarray(im.transform(im.size, Image.Transform.AFFINE, (1 / k, 0, cx - cx / k, 0, 1, 0),
                                   resample=Image.Resampling.BICUBIC))


def _norm(x):
    return x / max(float(x.max()), 1e-6)


# --- the few picture steps the title's look needs, in numpy (scipy's ndimage does the same, but only the Studio
# carries scipy: these keep the Launcher as it is). Each as scipy's: a Gaussian kernel to 4 sigmas, edges mirrored;
# grow and shrink by the four neighbours, nothing outside the picture.
def _blur1d(a, sigma, axis=-1):
    import numpy as np
    r = int(4.0 * sigma + 0.5)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    a = np.moveaxis(np.asarray(a, np.float64), axis, -1)
    p = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(r, r)], mode="symmetric")
    n = p.shape[-1] + len(k) - 1
    out = np.fft.irfft(np.fft.rfft(p, n) * np.fft.rfft(k, n), n)[..., 2 * r:2 * r + a.shape[-1]]
    return np.moveaxis(out, -1, axis).astype(np.float32)


def _blur(a, sigma):
    sy, sx = sigma if isinstance(sigma, tuple) else (sigma, sigma)
    return _blur1d(_blur1d(a, sy, 0), sx, 1)


def _grow(m, n):
    """A mask grown by n pixels (each step: the four neighbours)."""
    for _ in range(n):
        g = m.copy()
        g[1:] |= m[:-1]
        g[:-1] |= m[1:]
        g[:, 1:] |= m[:, :-1]
        g[:, :-1] |= m[:, 1:]
        m = g
    return m


def _shrink(m, n):
    """A mask shrunk by n pixels (each step: the four neighbours; outside the picture counts as empty)."""
    for _ in range(n):
        g = m.copy()
        g[1:] &= m[:-1]
        g[:-1] &= m[1:]
        g[:, 1:] &= m[:, :-1]
        g[:, :-1] &= m[:, 1:]
        g[0], g[-1], g[:, 0], g[:, -1] = False, False, False, False
        m = g
    return m


def _close(m, half):
    """A mask's gaps filled: grown by a square of `half` pixels each way, then shrunk by the same."""
    g = m.copy()
    for s in range(1, half + 1):
        g[s:] |= m[:-s]
        g[:-s] |= m[s:]
    m2 = g.copy()
    for s in range(1, half + 1):
        m2[:, s:] |= g[:, :-s]
        m2[:, :-s] |= g[:, s:]
    out = m2.copy()
    for s in range(1, half + 1):
        out[s:] &= m2[:-s]
        out[:-s] &= m2[s:]
    out[:half], out[-half:] = False, False
    final = out.copy()
    for s in range(1, half + 1):
        final[:, s:] &= out[:, :-s]
        final[:, :-s] &= out[:, s:]
    final[:, :half], final[:, -half:] = False, False
    return final


def _title_look(alpha) -> dict:
    """What every frame shares: the scene with its focus on the title, the plate and the letters' dark edge; the glow,
    the flare and the light on the water (each to be scaled by the swell); the letters' outline."""
    import numpy as np
    from importlib import resources
    from PIL import Image
    h, w = alpha.shape
    letters = alpha > 0.1
    scene = np.asarray(Image.open(resources.files(__package__) / "pictures" / SCENE).convert("RGB")
                       .resize((w, h), Image.LANCZOS)).astype(np.float32)
    ys, xs = np.nonzero(letters)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # the eye to the title: the scene a little darker toward the edges and the bottom
    focus = 1 - 0.35 * np.clip(np.hypot((xx - cx) / (w * 0.62), (yy - cy) / (h * 0.78)), 0, 1) ** 1.6
    # the dark edge round each letter, the word's closed shape (its gaps filled), the plate behind it
    clear = 1 - np.clip(_blur(_grow(letters, 3).astype(np.float32), 1.2) * 1.4, 0, 1)
    closed = _close(letters, 24)   # (two 25 x 25 squares)
    word = _blur(closed.astype(np.float32), 3)
    plate = _norm(_blur(_grow(closed, 12).astype(np.float32), 34))
    base = scene * (focus * (1 - PLATE * plate) * (1 - EDGE * (1 - clear)))[..., None]
    # the glow round the word (a third of it inside the word's shape), the short flare out to the sides
    shade = (clear * (1 - 0.67 * word))[..., None]
    glow = (95 * _norm(_blur(alpha, 12))[..., None] * np.array(AMBER)
            + 70 * _norm(_blur(closed.astype(np.float32), 40))[..., None] * np.array(RED_AMBER)) * shade
    flare = (_norm(_blur(closed.astype(np.float32), (10, 170))) * (1 - word) * 75)[..., None] \
        * np.array(AMBER) * clear[..., None]
    # the title's light on the water: as wide as the title, fading down the sea, in the sea's own glints
    across = _norm(_blur1d(alpha.sum(axis=0), 30, 0))
    down = np.where(yy > HORIZON, np.exp(-(yy - HORIZON) / 170.0), 0.0)
    lum = scene.max(axis=2)
    ripple = lum - _blur(lum, 6)
    glints = np.clip(0.55 + ripple / max(float(np.percentile(np.abs(ripple), 95)), 1e-6) * 0.6, 0, 1.6)
    water = (WATER * across[None, :] * down * glints)[..., None] * np.array((1.0, 0.78, 0.42))
    slant = xx + 0.35 * yy        # the shine's band leans like the letters' cut corners
    solid = _shrink(alpha > 0.9, 2)   # inside the letters, their soft rims left out
    return {"alpha": alpha, "solid": solid, "base": base, "glow": glow, "flare": flare, "water": water, "slant": slant,
            "shine": (xs.min() + 0.35 * ys.min() - 90, xs.max() + 0.35 * ys.max() + 90)}


def _shine(look, peaks, f):
    """The bright band crossing the letters on frame f: 24 frames round each swell's peak."""
    import numpy as np
    out = np.zeros(look["alpha"].shape, np.float32)
    a, b = look["shine"]
    for p in peaks:
        k = (f - (p - 12)) / 24
        if 0 <= k <= 1:
            out += np.exp(-((look["slant"] - (a + (b - a) * k)) / 24) ** 2) * np.sin(np.pi * k)
    return out


def _video_frame(look, layer, swell, lit, shine):
    """One frame: the scene and the title's light at this swell, the gold letters (the frame's own chrome, at LETTER_RED
    times `lit`) on top."""
    import numpy as np
    alpha = look["alpha"][..., None]
    light = look["glow"] * (0.15 + 0.85 * swell) + look["flare"] * swell * FLARE
    ground = look["base"] + light * GLOW_GAIN + look["water"] * (0.45 + 0.55 * swell)
    gold = video_curve(layer[..., :3].max(axis=2, keepdims=True).astype(np.float32)) * np.array(GOLD)
    solid = look["solid"]
    red = gold[..., 0][solid]
    gold *= LETTER_RED * lit / max(float(red.mean()), 1e-6)
    red = gold[..., 0][solid]
    mean = gold[solid].mean(axis=0)
    gold = mean + (gold - mean) * min(1.0, LETTER_CONTRAST * float(red.mean()) / max(float(red.std()), 1e-6))
    letters = gold + (shine * 80)[..., None] * np.array((1.0, 0.95, 0.85))
    out = np.clip(ground, 0, 255) * (1 - alpha) + np.clip(letters, 0, 255) * alpha
    return np.clip(out, 0, 255).astype(np.uint8)


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


def _letters(rgb, alpha, kx, ky):
    """R.U.S.E. 2.0 from the frame's own letters (the chrome, lit as the frame lights them), alone: RGBA (h, w, 4)."""
    import numpy as np
    from PIL import Image
    from . import menulogo as M
    h, w = alpha.shape
    X0, Y0, X1, Y1 = VIDEO_LETTERS
    edged = _edge_colour(rgb, alpha, (X0 - 6, Y0 - 6, X1 + 6, Y1 + 6))
    letters = Image.fromarray(np.dstack([edged, (alpha * 255).astype(np.uint8)]), "RGBA")
    light = _row_light(rgb, alpha)
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
    return np.asarray(layer)
