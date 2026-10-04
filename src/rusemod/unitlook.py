"""Unit looks: painted textures from a mod into the game (MOD_FORMAT §7), and the work folder the Studio's
"Open in Blender" / "Bring back" buttons use.

A mod repaints a texture with `files/replace/<game path>.png`, where <game path> is the texture's path in
ZZ_Win.dat: `files/replace/gen/ww2/res3d/units/urss/char/urss_t-26/tsccombcs_combineddsctexture01.tgv.png` is the
T-26's colour. Its alpha (on vehicles: the player's side colour where low, shine where high; TESTS T23) stays the
game's, byte for byte, unless `<game path>.alpha.png` (grey) is there too; a colour picture's own alpha channel is
never used (Blender saves 255 there). A picture must be the texture's own size (the size `ruse export-model` writes).

The build writes the texture the way the game stores its own small levels: every level a plain TGU1 payload (its
32-byte header, then the blocks as they are) under TGV flag 1, as proven in the game (T23). Each level's picture is
the one above halved (2 x 2 average). A 4 x 4 block nobody painted keeps the game's own block, byte for byte, in
every level; a painted one is encoded again (rusemod.dxt). The texture's 64 x 64 stand-in, in every stand-in pack
that has one, gets the same, in place (its TGV flag 0: raw blocks), unless other textures' stand-ins share its
picture: then it's left as the game has it (T27).

A unit's card, its picture in the build menu (`TextureForInterface`, e.g. `files/replace/gen/ww2/res2d/
texanimationuniticone/eu/m4_sherman.tgv.png`), is replaced the same way: all 450 of the game's are one DXT1_LIN
level packed as ZIPO (410 of them 360 x 184), with no stand-ins; the changed blocks are encoded again and the level
packed again (make_picture). The game shows a card from the menu packs, archives of their own inside ZZ_Win.dat that
hold copies of the cards (gen\\pack\\menuus.ppk for the US build menus, outgame.ppk, ...): replacing only the loose
.tgv left the game's card in the build menu (T31, 2026-10-04). So every changed texture is replaced in each nested
pack that has a copy too (in_nested_packs); all 64 of them rebuild byte for byte. With that, the card showed in the
game's build menu (T31 passed).

A new unit (a clone) starts with its source's card, the same picture file (T33: the Sherman and the Tall Sherman
looked the same in the menu). Its own card is `files/cards/<the unit's name>.png` (`Descriptor_Unit_R2_X.png`): the
build gives the clone's TextureForInterface a file of its own beside its source's (own_card_name), made from the
source's card the way make_picture writes one, and adds it to each menu pack that holds the source's card
(own_cards), laid out the way the game's packs are (unitpacks.archive_with gives all 64 back byte for byte).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
from pathlib import Path

from . import dxt, tgu1
from .edat import Edat
from .png import read_png
from .tmst import Tgv, make_tgv, zipo_pack, zipo_unpack
from .unitpacks import ProxyPack

REPLACE = Path("files") / "replace"
CARDS = Path("files") / "cards"  # new units' own cards: <the unit's name>.png
LOOK_FILE = "look.json"


class LookError(ValueError):
    pass


# --- pictures ---
def halve(px: bytes, w: int, h: int, channels: int = 4) -> bytes:
    """A picture at half the size (each pixel the rounded average of a 2 x 2 square)."""
    nw, nh = max(1, w // 2), max(1, h // 2)
    out = bytearray(nw * nh * channels)
    for y in range(nh):
        r0, r1 = (2 * y) * w, min(2 * y + 1, h - 1) * w
        for x in range(nw):
            a, b = 2 * x, min(2 * x + 1, w - 1)
            for c in range(channels):
                s = (px[(r0 + a) * channels + c] + px[(r0 + b) * channels + c]
                     + px[(r1 + a) * channels + c] + px[(r1 + b) * channels + c])
                out[(y * nw + x) * channels + c] = (s + 2) // 4
    return bytes(out)


def block_pixels(px: bytes, w: int, bx: int, by: int, channels: int = 4, take: int = 3) -> list[tuple]:
    """The 16 pixels (row-major) of the 4 x 4 block (bx, by), each its first `take` channels."""
    out = []
    for r in range(4):
        o = ((by * 4 + r) * w + bx * 4) * channels
        out.extend(tuple(px[o + c * channels:o + c * channels + take]) for c in range(4))
    return out


def alpha_block(values: list[int]) -> bytes:
    """16 alpha values (row-major) -> the 8-byte alpha half of a DXT5 block (8 steps from the highest to the
    lowest; the same index order the game's decoder gives: 0 = alpha 0, 1 = alpha 1, 2..7 in between)."""
    hi, lo = max(values), min(values)
    if hi == lo:
        return bytes([hi, lo]) + bytes(6)
    pal = [hi, lo] + [((7 - k) * hi + k * lo + 3) // 7 for k in range(1, 7)]
    word = 0
    for i, v in enumerate(values):
        word |= min(range(8), key=lambda j: abs(pal[j] - v)) << (3 * i)
    return bytes([hi, lo]) + word.to_bytes(6, "little")


def _changed(new: bytes, old: bytes, w: int, h: int, offset: int, width: int) -> list[bool]:
    """For each 4 x 4 block (row by row): whether any pixel's channels [offset, offset + width) differ."""
    bw, bh = w // 4, h // 4
    out = []
    for by in range(bh):
        for bx in range(bw):
            diff = False
            for r in range(4):
                o = ((by * 4 + r) * w + bx * 4) * 4
                a, b = new[o:o + 16], old[o:o + 16]
                if any(a[4 * c + offset:4 * c + offset + width] != b[4 * c + offset:4 * c + offset + width]
                       for c in range(4)):
                    diff = True
                    break
            out.append(diff)
    return out


def _pool(changed: list[bool], bw: int, bh: int, nbw: int, nbh: int) -> list[bool]:
    """Block flags at a smaller level: a block there is changed when any block it covers is."""
    sx, sy = max(1, bw // nbw), max(1, bh // nbh)
    out = []
    for by in range(nbh):
        for bx in range(nbw):
            out.append(any(changed[(y * bw) + x] for y in range(by * sy, min(bh, (by + 1) * sy))
                           for x in range(bx * sx, min(bw, (bx + 1) * sx))))
    return out


def _level_blocks(old_blocks: bytes, size: int, pic: bytes, alpha_pic: bytes | None, w: int,
                  colour_changed: list[bool], alpha_changed: list[bool]) -> tuple[bytes, int]:
    """One level's blocks: the game's where nothing changed, encoded again where it did. Returns (blocks, count of
    blocks encoded again)."""
    bw = w // 4
    out, again = bytearray(), 0
    for i in range(len(old_blocks) // size):
        old = old_blocks[size * i:size * (i + 1)]
        bx, by = i % bw, i // bw
        if not colour_changed[i] and not alpha_changed[i]:
            out += old
            continue
        again += 1
        if size == 16:
            alpha = alpha_block([p[0] for p in block_pixels(alpha_pic, w, bx, by, 1, 1)]) \
                if alpha_changed[i] else old[:8]
            colour = dxt.encode_block(block_pixels(pic, w, bx, by)) if colour_changed[i] else old[8:]
            out += alpha + colour
        else:
            out += dxt.encode_block(block_pixels(pic, w, bx, by))
    return bytes(out), again


def _grey(rgba: bytes) -> bytes:
    return bytes(rgba[0::4])


def make_texture(original: bytes, colour: bytes | None, alpha: bytes | None, w: int, h: int) -> tuple[bytes, dict]:
    """A texture (.tgv bytes, as shipped) repainted: `colour` RGBA pixels (its alpha channel unused) and/or `alpha`
    RGBA pixels of a grey picture (its red channel used), both w x h, the texture's own size. Returns the new .tgv
    and a report {levels, blocks, encoded}; nothing painted: (original, report with encoded 0)."""
    g = Tgv(original)
    if g.format not in ("DXT1", "DXT5") or g.flag != 1:
        raise LookError(f"a {g.format} texture (flag {g.flag}) can't be repainted yet: only DXT1 and DXT5 ones")
    payloads = [g.payload(m) for m in range(len(g.mips))]  # smallest first
    if any(p[:4] != b"TGU1" for p in payloads):
        raise LookError("this texture's levels aren't TGU1: it can't be repainted yet")
    heads = [tgu1.Header.parse(p) for p in payloads]
    size = 16 if g.format == "DXT5" else 8
    big = heads[-1]
    W, H = big.width * 4, big.height * 4
    if (w, h) != (W, H):
        raise LookError(f"the picture is {w} x {h}; this texture is {W} x {H}: paint on the picture the export wrote")
    if alpha is not None and size != 16:
        raise LookError("this texture has no alpha (DXT1): leave the alpha picture out")
    old_blocks = [tgu1.decode(p) for p in payloads]
    old_px = dxt.decode_rgba(old_blocks[-1], W, H, g.format)
    colour_changed = _changed(colour, old_px, W, H, 0, 3) if colour is not None else [False] * (W * H // 16)
    alpha_changed = [False] * (W * H // 16)
    if alpha is not None:  # compare the grey picture's red with the old alpha
        merged = bytearray(old_px)
        merged[3::4] = alpha[0::4]
        alpha_changed = _changed(bytes(merged), old_px, W, H, 3, 1)
    report = {"levels": len(payloads), "blocks": 0, "encoded": 0}
    if not any(colour_changed) and not any(alpha_changed):
        return original, report
    pic = colour if colour is not None else old_px
    apic = _grey(alpha) if alpha is not None else None
    levels = []
    cw, ch, cc, ac = W, H, colour_changed, alpha_changed
    for k in range(len(payloads) - 1, -1, -1):  # largest first
        head = heads[k]
        lw, lh = head.width * 4, head.height * 4
        while cw > lw or ch > lh:  # this level's picture and flags
            nbw, nbh = max(1, cw // 8), max(1, ch // 8)
            cc = _pool(cc, cw // 4, ch // 4, nbw, nbh)
            ac = _pool(ac, cw // 4, ch // 4, nbw, nbh)
            pic = halve(pic, cw, ch)
            if apic is not None:
                apic = halve(apic, cw, ch, 1)
            cw, ch = max(4, cw // 2), max(4, ch // 2)
        blocks, again = _level_blocks(old_blocks[k], size, pic, apic, lw, cc, ac)
        report["blocks"] += len(blocks) // size
        report["encoded"] += again
        flags = tgu1.FLAG_ALPHA if size == 16 else 0
        head_bytes = tgu1.Header(tgu1.VERSION, head.width, head.height, head.color_quality, head.selector_quality,
                                 head.width * head.height, flags).pack()[:tgu1.PLAIN_HEADER]
        levels.append(head_bytes + blocks)
    levels.reverse()  # smallest first, as the game's
    return make_tgv(g.width, g.height, g.format, levels, flag=g.flag), report


def make_standin(original: bytes, colour: bytes | None, alpha: bytes | None, w: int, h: int,
                 colour_changed_full: list[bool], alpha_changed_full: list[bool]) -> bytes:
    """A texture's stand-in (.tgv, flag 0: one raw level) repainted from the full-size pictures, in place: every
    byte outside its blocks stays the game's; its blocks change only where the full picture was painted."""
    g = Tgv(original)
    if g.flag != 0 or len(g.mips) != 1 or g.format not in ("DXT1", "DXT5"):
        raise LookError("a stand-in that isn't one raw DXT level")
    size = 16 if g.format == "DXT5" else 8
    off, length = g.mips[0]
    sw, sh = g.width, g.height
    if length != (sw // 4) * (sh // 4) * size:
        # not a game rule: a stand-in unlike every one the game ships, which this writer can't change safely
        raise LookError("a stand-in whose size doesn't match its blocks")
    old = original[off:off + length]
    old_px = dxt.decode_rgba(old, sw, sh, g.format)
    pic, apic, cw, ch = colour, (_grey(alpha) if alpha is not None else None), w, h
    cc, ac = colour_changed_full, alpha_changed_full
    while cw > sw or ch > sh:
        nbw, nbh = max(1, cw // 8), max(1, ch // 8)
        cc, ac = _pool(cc, cw // 4, ch // 4, nbw, nbh), _pool(ac, cw // 4, ch // 4, nbw, nbh)
        pic = halve(pic, cw, ch) if pic is not None else None
        apic = halve(apic, cw, ch, 1) if apic is not None else None
        cw, ch = max(4, cw // 2), max(4, ch // 2)
    if pic is None:
        pic = old_px
    blocks, _again = _level_blocks(old, size, pic, apic, sw, cc, ac)
    return original[:off] + blocks + original[off + length:]


def is_picture(original: bytes) -> bool:
    """Whether a texture is a one-level ZIPO picture (a unit's card), which make_picture writes."""
    g = Tgv(original)
    return len(g.mips) == 1 and g.codec == "ZIPO"


def make_picture(original: bytes, colour: bytes, w: int, h: int) -> tuple[bytes, dict]:
    """A one-level ZIPO DXT1 picture (a unit's card) replaced by `colour` (RGBA pixels, w x h, its alpha unused):
    the 4 x 4 blocks that changed are encoded again, the others stay the game's byte for byte, and the level is
    packed again as ZIPO under the same TGV header. Returns (the new .tgv, report); nothing changed: (original, ...)."""
    g = Tgv(original)
    if not is_picture(original) or not g.format.upper().startswith("DXT1") or g.flag != 1:
        # not a game rule: a picture unlike the game's cards, which this writer can't change safely
        raise LookError(f"a {g.format} picture with {len(g.mips)} level(s) can't be replaced yet: only cards (one "
                        f"DXT1 level, ZIPO)")
    if (w, h) != (g.width, g.height):
        raise LookError(f"the picture is {w} x {h}; this one is {g.width} x {g.height}")
    old = zipo_unpack(g.payload(0))
    if len(old) != (w // 4) * (h // 4) * 8:
        # not a game rule: a picture unlike the game's cards, which this writer can't change safely
        raise LookError("a picture whose size doesn't match its blocks")
    old_px = dxt.decode_rgba(old, w, h, g.format)
    changed = _changed(colour, old_px, w, h, 0, 3)
    report = {"levels": 1, "blocks": len(changed), "encoded": sum(changed)}
    if not any(changed):
        return original, report
    blocks, _again = _level_blocks(old, 8, colour, None, w, changed, [False] * len(changed))
    return make_tgv(g.width, g.height, g.format, [zipo_pack(blocks)], flag=g.flag), report


def card_member(file_name: str) -> str:
    """A unit's card picture as its TextureForInterface names it -> its .tgv in ZZ_Win.dat:
    datadir:/ww2/res2d/texanimationuniticone/eu/m4_sherman.png -> gen\\ww2\\res2d\\texanimationuniticone\\eu\\m4_sherman.tgv
    (all 788 units' cards are there)."""
    p = file_name.replace("/", "\\").lower()
    if p.startswith("datadir:\\"):
        p = "gen\\" + p[len("datadir:\\"):]
    return p[:-4] + ".tgv" if p.endswith((".png", ".tga", ".dds")) else p


def own_card_name(file_name: str, unit: str) -> str:
    """The card file of a new unit `unit` (its name, Descriptor_Unit_R2_X) whose source's card is `file_name`, as a
    TextureForInterface names it: beside the source's, named after the unit, written as the game writes it (its data
    has DataDir:\\WW2\\Res2D\\TexAnimationUnitIcone\\EU\\M4_Sherman.png -> DataDir:\\WW2\\Res2D\\TexAnimationUnitIcone\\EU\\
    descriptor_unit_r2_x.png)."""
    cut = max(file_name.rfind("/"), file_name.rfind("\\"))
    return f"{file_name[:cut + 1]}{unit.lower()}.png"


def mod_cards(folder: Path) -> dict:
    """{a new unit's name: its card picture} from a mod's files/cards/<name>.png."""
    root = Path(folder) / CARDS
    if not root.is_dir():
        return {}
    return {f.stem: f for f in sorted(root.glob("*.png"))}


def own_cards(zz, cards: dict, earlier: dict | None = None, say=print, loose: dict | None = None) -> dict:
    """{nested pack's path in ZZ_Win.dat: its new bytes} for new units' own cards ({card member to add: (its source's
    card member, the PNG)}): each picture made from the source's card (make_picture: its format, size and header) and
    added to every menu pack that holds the source's card. `earlier`: members other build steps already changed
    (path -> bytes), the source's card (if a mod repainted it too) and the packs taken from there. `loose` (a dict)
    gets each card as a file of ZZ_Win.dat's own too ({member: bytes}): all 450 of the game's cards are there as well
    as in the menu packs, and the game reads them there once a unit is on the map (T35, 2026-10-04: an Abrams with
    its card only in the menu packs showed in the build menu and crashed the game when built)."""
    from .unitpacks import archive_with
    before = {k.lower().replace("/", "\\"): v for k, v in (earlier or {}).items()}
    made: dict = {}  # source member (lower) -> {new member: bytes}
    for new, (source, png) in sorted(cards.items()):
        e = zz.entry(source)
        if e is None:
            # not a game rule: the clone's card names a picture this game doesn't have
            raise LookError(f"{png}: the unit's card {source} isn't in the game, so its own card can't be made from it")
        if zz.entry(new) is not None:
            # not a game rule: the name our card would get is taken (a game card of that name)
            raise LookError(f"{png}: the game already has a card {new}")
        original = before.get(e.path.lower()) or bytes(zz.read(e))
        try:
            w, h, px = read_png(Path(png).read_bytes())
            data, _report = make_picture(original, px, w, h)
        except (ValueError, LookError) as exc:
            raise LookError(f"{png}: {exc}") from None
        made.setdefault(e.path.lower(), {})[new] = data
        if loose is not None:
            loose[new] = data
        say(f"card {new}: its own, made from {source}")
    out: dict = {}
    for e in zz.entries:
        if not e.path.lower().endswith(".ppk"):
            continue
        raw = before.get(e.path.lower()) or bytes(zz.read(e))
        if raw[:4] != b"edat":
            continue
        inner = Edat(raw)
        add = {n: d for m in inner.entries if m.path.lower() in made for n, d in made[m.path.lower()].items()}
        if add:
            out[e.path] = archive_with(raw, add)
            say(f"  in {e.path}: {', '.join(sorted(n.rsplit(chr(92), 1)[-1] for n in add))}")
    if made and not out:
        # not a game rule: the source's card is in no menu pack, so the build menu wouldn't find the new one
        raise LookError(f"no menu pack holds {', '.join(sorted(made))}, so the new cards can't be shown")
    return out


def picture_rgba(original: bytes) -> tuple[int, int, bytes]:
    """A one-level ZIPO picture (a card) as (width, height, RGBA pixels)."""
    g = Tgv(original)
    return g.width, g.height, dxt.decode_rgba(zipo_unpack(g.payload(0)), g.width, g.height, g.format)


def standin_name(member: str) -> str:
    """The stand-in of a texture: gen\\ww2\\...\\x01.tgv -> gentexproxy\\ww2\\...\\x01.tgv."""
    m = member.replace("/", "\\").lower()
    return "gentexproxy\\" + (m[4:] if m.startswith("gen\\") else m)


# --- a mod's painted textures ---
def mod_textures(folder: Path) -> dict:
    """{texture path in ZZ_Win.dat (backslashes, lower case): (colour picture or None, alpha picture or None)}
    from a mod's files/replace/**/<name>.tgv.png and <name>.tgv.alpha.png."""
    root = Path(folder) / REPLACE
    out: dict = {}
    if not root.is_dir():
        return out
    for f in sorted(root.rglob("*.png")):
        rel = f.relative_to(root).as_posix().lower()
        if rel.endswith(".tgv.alpha.png"):
            member, kind = rel[:-len(".alpha.png")], 1
        elif rel.endswith(".tgv.png"):
            member, kind = rel[:-len(".png")], 0
        else:
            continue
        key = member.replace("/", "\\")
        pair = list(out.get(key, (None, None)))
        pair[kind] = f
        out[key] = tuple(pair)
    return out


def changes(zz, textures: dict, say=print, before: dict | None = None) -> dict:
    """{member path in ZZ_Win.dat: new bytes} for the painted `textures` ({member: (colour PNG, alpha PNG)}):
    each texture and its stand-ins in every stand-in pack (.ppk, PRXYPCPC) that has one. `before`: members other
    build steps already changed ({path: bytes}); a stand-in pack among them is changed from that version."""
    earlier = {k.lower().replace("/", "\\"): v for k, v in (before or {}).items()}
    out: dict = {}
    standins: dict = {}  # stand-in name -> (colour px, alpha px, w, h, colour flags, alpha flags)
    for member, (colour_file, alpha_file) in sorted(textures.items()):
        e = zz.entry(member)
        if e is None:
            # not a game rule: the picture is named for a texture this game doesn't have (a typo, another game build)
            raise LookError(f"files/replace/{member.replace(chr(92), '/')}.png: the game has no texture {member}")
        original = bytes(zz.read(e))
        pics = []
        for f in (colour_file, alpha_file):
            if f is None:
                pics.append((0, 0, None))
                continue
            try:
                pics.append(read_png(Path(f).read_bytes()))
            except ValueError as exc:
                raise LookError(f"{f}: {exc}") from None
        (cw, ch, cpx), (aw, ah, apx) = pics
        w, h = (cw, ch) if cpx is not None else (aw, ah)
        if cpx is not None and apx is not None and (cw, ch) != (aw, ah):
            raise LookError(f"{alpha_file}: {aw} x {ah}, but its colour picture is {cw} x {ch}")
        if is_picture(original):  # a unit's card: one level, no stand-ins
            if apx is not None or cpx is None:
                raise LookError(f"{alpha_file or colour_file}: a card has no alpha picture, only its colour")
            try:
                new, report = make_picture(original, cpx, w, h)
            except LookError as exc:
                raise LookError(f"{colour_file}: {exc}") from None
            if new is not original:
                out[e.path] = new
            say(f"card {member}: {report['encoded']:,} of {report['blocks']:,} blocks changed")
            continue
        try:
            new, report = make_texture(original, cpx, apx, w, h)
        except LookError as exc:
            raise LookError(f"{colour_file or alpha_file}: {exc}") from None
        if new is original:
            say(f"texture {member}: the picture is the game's own (nothing painted): left as it is")
            continue
        out[e.path] = new
        say(f"texture {member}: {report['encoded']:,} of {report['blocks']:,} blocks painted, in {report['levels']} levels")
        g = Tgv(original)
        old_px = dxt.decode_rgba(tgu1.decode(g.payload(len(g.mips) - 1)), w, h, g.format)
        cflags = _changed(cpx, old_px, w, h, 0, 3) if cpx is not None else [False] * (w * h // 16)
        aflags = [False] * (w * h // 16)
        if apx is not None:
            merged = bytearray(old_px)
            merged[3::4] = apx[0::4]
            aflags = _changed(bytes(merged), old_px, w, h, 3, 1)
        standins[standin_name(member)] = (cpx, apx, w, h, cflags, aflags)
    if standins:
        # A stand-in whose picture other stand-ins share (the M4 Sherman's tracks with the Firefly's, the Calliope's and
        # the flamethrower's) is left as the game has it: painting it in place repaints the others, and giving it its
        # own copy makes the pack bigger, which no game test has tried (T23's packs kept their size; the first copy
        # that grew one crashed, T27 2026-10-04, cause not proven). Only its far-off look keeps the old colours.
        found = {n: 0 for n in standins}
        kept = {n: 0 for n in standins}
        for e in zz.entries:
            if not e.path.lower().endswith(".ppk"):
                continue
            raw = earlier.get(e.path.lower()) or bytes(zz.read(e))
            if raw[:8] != b"PRXYPCPC":
                continue
            pack = ProxyPack.read(raw)
            names = pack.names()
            hits = [n for n in standins if n in names]
            changed = False
            for n in hits:
                i = names.index(n)
                if any(s == pack.shared[i] for j, s in enumerate(pack.shared) if j != i):
                    kept[n] += 1
                    continue
                cpx, apx, w, h, cflags, aflags = standins[n]
                pack.proxies[i].data = make_standin(pack.proxies[i].data, cpx, apx, w, h, cflags, aflags)
                found[n] += 1
                changed = True
            if changed:
                out[e.path] = pack.to_bytes()
        for n in standins:
            if found[n]:
                say(f"  its stand-in {n}: in {found[n]} pack(s)")
            if kept[n]:
                say(f"  its stand-in {n}: shares its picture with other textures' in {kept[n]} pack(s), so it's left "
                    f"as the game has it there (far off, that texture keeps the game's look)")
    out.update(in_nested_packs(zz, {p: d for p, d in out.items() if p.lower().endswith(".tgv")}, earlier, say))
    return out


def in_nested_packs(zz, changed: dict, earlier: dict | None = None, say=print) -> dict:
    """{nested pack's path in ZZ_Win.dat: its new bytes} for every pack inside ZZ_Win.dat that is an archive of its
    own (gen\\pack\\*.ppk, starting `edat`) holding a copy of a `changed` texture ({member: new bytes}): the menu
    packs hold the cards the build menu shows. `earlier`: packs other build steps already changed (lower-case
    path -> bytes), changed from that version."""
    want = {p.lower(): d for p, d in changed.items()}
    out: dict = {}
    if not want:
        return out
    for e in zz.entries:
        if not e.path.lower().endswith(".ppk"):
            continue
        raw = (earlier or {}).get(e.path.lower()) or bytes(zz.read(e))
        if raw[:4] != b"edat":
            continue
        inner = Edat(raw)
        hits = {m.path: want[m.path.lower()] for m in inner.entries if m.path.lower() in want}
        if hits:
            out[e.path] = inner.to_bytes(replace=hits)
            say(f"  in {e.path}: {', '.join(sorted(h.rsplit(chr(92), 1)[-1] for h in hits))}")
    return out


# --- the Studio's work folder: a unit out to Blender, its paint back into the mod ---
def _pixels_hash(path: Path, alpha: bool) -> str:
    w, h, px = read_png(Path(path).read_bytes())
    data = px[0::4] if alpha else b"".join(px[i:i + 3] for i in range(0, len(px), 4))
    return hashlib.sha1(struct.pack("<II", w, h) + data).hexdigest()


def prepare(lib, models: list[str], folder: Path, side: int = 4096) -> dict:
    """Write `models` (names in `lib`, a rusemod.models.Library) into `folder` as .glb files with their pictures,
    and look.json: which picture is which texture's colour or alpha, and a hash of each one as exported (so Bring
    back takes only what was painted). Returns that record."""
    from . import gltf
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    record = {"models": [], "pictures": {}}
    for s in gltf.export(lib, models, folder, side=side):
        record["models"].append(s["file"])
        for name, (member, kind) in s.get("picture_of", {}).items():
            record["pictures"][name] = {"texture": member, "kind": kind,
                                        "hash": _pixels_hash(folder / name, kind == "alpha")}
    (folder / LOOK_FILE).write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def bring_back(folder: Path, mod: Path) -> list[dict]:
    """Copy every picture in `folder` (made by prepare) that was painted since into the mod's files/replace, named
    for its texture. Returns [{picture, texture, kind, to}] of what was copied (a texture whose colour and alpha
    pictures are both untouched is left as the mod has it)."""
    folder, mod = Path(folder), Path(mod)
    record = json.loads((folder / LOOK_FILE).read_text(encoding="utf-8"))
    done = []
    for name, info in sorted(record["pictures"].items()):
        pic = folder / name
        if not pic.is_file() or _pixels_hash(pic, info["kind"] == "alpha") == info["hash"]:
            continue
        rel = info["texture"].replace("\\", "/") + (".alpha.png" if info["kind"] == "alpha" else ".png")
        to = mod / REPLACE / rel
        to.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pic, to)
        done.append({"picture": name, "texture": info["texture"], "kind": info["kind"], "to": str(to)})
    return done
