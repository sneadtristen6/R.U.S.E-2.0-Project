"""The build's checks for fonts, videos, Flash menus and shaders a mod changes or adds (rusemod.gamefiles' safeguard 4:
every file is checked as its kind before the game gets it; the owner, 2026-10-08: "just write a check for those four
kinds"). Each reads the whole file as its kind, and refuses what doesn't read cleanly to its end.

The programs among them (a Flash menu's code, the shaders) are the game's own or nothing, until RUSE 2.0's approvals
exist (safeguard 5, the owner's question of 2026-10-08: "only RUSE 2.0 approved scripts and programs"): a Flash menu
may change its layout, shapes and words but keep the game's code; a changed shader is refused.
"""
from __future__ import annotations

import struct
import zlib


class CheckError(ValueError):
    """The file isn't a good one of its kind: the message says what's wrong."""


# --- fonts (TrueType / OpenType, one font or a collection) ---
FONT_NEEDS = ("cmap", "head", "hhea", "hmtx", "maxp", "name", "post")
CMAP_FORMATS = {0, 2, 4, 6, 8, 10, 12, 13, 14}


def check_font(data: bytes) -> int:
    """Check a .ttf/.otf (one font) or .ttc (a collection): every table where it says, the tables a font needs, its
    glyph count, metrics, glyph offsets and character maps in step. Returns how many fonts it holds."""
    if data[:4] == b"ttcf":
        if len(data) < 12:
            raise CheckError("the font collection is cut short")
        count = struct.unpack_from(">I", data, 8)[0]
        if not 1 <= count <= 256 or len(data) < 12 + 4 * count:
            raise CheckError(f"the font collection says it holds {count} fonts")
        for start in struct.unpack_from(f">{count}I", data, 12):
            _check_sfnt(data, start)
        return count
    _check_sfnt(data, 0)
    return 1


def _check_sfnt(data: bytes, start: int) -> None:
    if start + 12 > len(data):
        raise CheckError("a font's table list is past the file's end")
    version = data[start:start + 4]
    if version not in (b"\x00\x01\x00\x00", b"OTTO", b"true"):
        raise CheckError("not a TrueType or OpenType font")
    count = struct.unpack_from(">H", data, start + 4)[0]
    if not 1 <= count <= 200 or start + 12 + 16 * count > len(data):
        raise CheckError(f"a font's table list says {count} tables")
    tables = {}
    for i in range(count):
        tag, _sum, off, length = struct.unpack_from(">4sIII", data, start + 12 + 16 * i)
        name = tag.decode("latin-1")
        if name in tables:
            raise CheckError(f"two '{name}' tables")
        if off + length > len(data):
            raise CheckError(f"the '{name}' table is past the file's end")
        tables[name] = data[off:off + length]
    missing = [t for t in FONT_NEEDS if t not in tables]
    if missing or not ({"glyf", "loca"} <= set(tables) or "CFF " in tables or "CFF2" in tables):
        raise CheckError(f"a font without its {', '.join(missing) or 'glyph outlines'}")
    head, maxp, hhea = tables["head"], tables["maxp"], tables["hhea"]
    if len(head) < 54 or struct.unpack_from(">I", head, 12)[0] != 0x5F0F3CF5:
        raise CheckError("the font's 'head' table isn't one")
    units, loca_long = struct.unpack_from(">H", head, 18)[0], struct.unpack_from(">h", head, 50)[0]
    if not 16 <= units <= 16384 or loca_long not in (0, 1):
        raise CheckError("the font's 'head' table has values no font has")
    if len(maxp) < 6 or len(hhea) < 36:
        raise CheckError("the font's 'maxp' or 'hhea' table is cut short")
    glyphs = struct.unpack_from(">H", maxp, 4)[0]
    metrics = struct.unpack_from(">H", hhea, 34)[0]
    if glyphs == 0 or not 1 <= metrics <= glyphs or len(tables["hmtx"]) < 4 * metrics + 2 * (glyphs - metrics):
        raise CheckError("the font's glyph count and its metrics don't agree")
    if "loca" in tables and "glyf" in tables:
        size = 4 if loca_long else 2
        loca = tables["loca"]
        if len(loca) < size * (glyphs + 1):
            raise CheckError("the font's glyph offsets ('loca') are cut short")
        offsets = struct.unpack_from(f">{glyphs + 1}{'I' if loca_long else 'H'}", loca, 0)
        scale = 1 if loca_long else 2
        if any(b < a for a, b in zip(offsets, offsets[1:])) or offsets[-1] * scale > len(tables["glyf"]):
            raise CheckError("the font's glyph offsets ('loca') go backwards or past its glyphs")
    cmap = tables["cmap"]
    if len(cmap) < 4:
        raise CheckError("the font's character map is cut short")
    subs = struct.unpack_from(">H", cmap, 2)[0]
    if len(cmap) < 4 + 8 * subs:
        raise CheckError("the font's character map list is cut short")
    for i in range(subs):
        off = struct.unpack_from(">I", cmap, 4 + 8 * i + 4)[0]
        if off + 4 > len(cmap):
            raise CheckError("a character map is past the font's 'cmap' table")
        form = struct.unpack_from(">H", cmap, off)[0]
        if form not in CMAP_FORMATS:
            raise CheckError(f"a character map of a kind fonts don't have ({form})")
        if form in (8, 10, 12, 13):
            if off + 8 > len(cmap):
                raise CheckError("a character map is cut short")
            length = struct.unpack_from(">I", cmap, off + 4)[0]
        elif form == 14:
            if off + 6 > len(cmap):
                raise CheckError("a character map is cut short")
            length = struct.unpack_from(">I", cmap, off + 2)[0]
        else:
            length = struct.unpack_from(">H", cmap, off + 2)[0]
        if off + length > len(cmap):
            raise CheckError("a character map is past the font's 'cmap' table")


# --- videos (WebM: the game plays VP9 pictures with Vorbis sound and nothing else) ---
EBML_HEADER, DOC_TYPE, SEGMENT, TRACKS, TRACK_ENTRY, CODEC_ID, TRACK_TYPE = (
    0x1A45DFA3, 0x4282, 0x18538067, 0x1654AE6B, 0xAE, 0x86, 0x83)
# the elements that hold other elements (walked into, so every size inside is checked too)
EBML_MASTERS = {EBML_HEADER, SEGMENT, 0x114D9B74, 0x4DBB, 0x1549A966, TRACKS, TRACK_ENTRY, 0xE0, 0xE1, 0x6D80, 0x6240,
                0x5034, 0x5035, 0x1F43B675, 0xA0, 0x75A1, 0xA6, 0x8E, 0xE8, 0x1C53BB6B, 0xBB, 0xB7, 0xDB,
                0x1254C367, 0x7373, 0x63C0, 0x67C8, 0x55B0, 0x55D0}
ATTACHMENTS, CHAPTERS = 0x1941A469, 0x1043A770


def _vint(data: bytes, p: int, end: int, keep_marker: bool) -> tuple[int, int, bool]:
    if p >= end:
        raise CheckError("the video ends in the middle of an element")
    first = data[p]
    length = 8 - first.bit_length() + 1
    if first == 0 or keep_marker and length > 4:
        raise CheckError("the video has an element no WebM file has")
    if p + length > end:
        raise CheckError("the video ends in the middle of an element")
    value = first if keep_marker else first & ((1 << (8 - length)) - 1)
    for b in data[p + 1:p + length]:
        value = value << 8 | b
    unknown = not keep_marker and value == (1 << (7 * length)) - 1
    return value, p + length, unknown


def check_video(data: bytes) -> dict:
    """Check a .webm the game can play: a WebM file whose every element fits in the one holding it, with a VP9 picture
    and Vorbis sound tracks (the only kinds the game's player takes), no attachments. Returns {"video": n, "sound": n}."""
    found = {"doc": None, "codecs": []}

    def walk(p: int, end: int, depth: int) -> None:
        while p < end:
            ident, p, _ = _vint(data, p, end, True)
            size, p, unknown = _vint(data, p, end, False)
            if unknown:
                raise CheckError("the video has an element of unknown size: save it as an ordinary WebM file")
            if p + size > end:
                raise CheckError("an element of the video runs past the one holding it")
            if ident in (ATTACHMENTS, CHAPTERS):
                # not a game rule: a video carries its picture and sound, nothing more (the owner's safeguards)
                raise CheckError("the video carries attachments or chapters, which the game doesn't use")
            if ident == DOC_TYPE:
                found["doc"] = bytes(data[p:p + size]).rstrip(b"\0")
            elif ident == TRACK_ENTRY:
                found["codecs"].append(_track(p, p + size))
            if ident in EBML_MASTERS:
                if depth > 8:
                    raise CheckError("the video's elements are nested deeper than any WebM file's")
                walk(p, p + size, depth + 1)
            p += size

    def _track(p: int, end: int) -> tuple[int, bytes]:
        kind, codec = 0, b""
        while p < end:
            ident, p, _ = _vint(data, p, end, True)
            size, p, _ = _vint(data, p, end, False)
            if ident == TRACK_TYPE:
                kind = int.from_bytes(data[p:p + size], "big")
            elif ident == CODEC_ID:
                codec = bytes(data[p:p + size]).rstrip(b"\0")
            p += size
        return kind, codec

    if data[:4] != b"\x1a\x45\xdf\xa3":
        raise CheckError("not a WebM video")
    walk(0, len(data), 0)
    if found["doc"] != b"webm":
        raise CheckError("not a WebM video (it's another kind of Matroska file)")
    pictures = [c for k, c in found["codecs"] if k == 1]
    sounds = [c for k, c in found["codecs"] if k == 2]
    others = [c for k, c in found["codecs"] if k not in (1, 2)]
    if len(pictures) != 1 or pictures != [b"V_VP9"]:
        # rule: video-vp9-vorbis
        raise CheckError("the game plays VP9 videos only (one picture track): "
                         f"this one has {', '.join(c.decode('latin-1') for c in pictures) or 'no picture'}")
    if any(c != b"A_VORBIS" for c in sounds):  # (the campaign's long films carry several, all Vorbis)
        # rule: video-vp9-vorbis
        raise CheckError("the game plays a video's sound only in Vorbis")
    if others:
        raise CheckError("the video has tracks other than its picture and sound")
    return {"video": len(pictures), "sound": len(sounds)}


# --- Flash menus (.gfx: the game's menus) ---
# tags that are layout, shapes, words and fonts (a mod may change them); every other tag (code, files it loads,
# embedded pictures and sounds, anything unknown) must be the game's own, in the same place, byte for byte
FLASH_FREE = {0: "End", 1: "ShowFrame", 2: "DefineShape", 4: "PlaceObject", 5: "RemoveObject",
              9: "SetBackgroundColor", 10: "DefineFont", 11: "DefineText", 13: "DefineFontInfo", 22: "DefineShape2",
              26: "PlaceObject2", 28: "RemoveObject2", 32: "DefineShape3", 33: "DefineText2", 37: "DefineEditText",
              39: "DefineSprite", 43: "FrameLabel", 46: "DefineMorphShape", 48: "DefineFont2", 56: "ExportAssets",
              62: "DefineFontInfo2", 70: "PlaceObject3", 73: "DefineFontAlignZones", 74: "CSMTextSettings",
              75: "DefineFont3", 77: "Metadata", 78: "DefineScalingGrid", 83: "DefineShape4",
              84: "DefineMorphShape2", 86: "DefineSceneAndFrameLabelData", 88: "DefineFontName",
              1000: "ExporterInfo", 1001: "DefineExternalImage"}
# what in a text field's words makes it load a file or run code (HTML text: pictures, links calling functions)
FLASH_TEXT_CODE = (b"<img", b"asfunction", b"href", b"event:", b"<a ")
FLASH_CODE = {12: "DoAction", 59: "DoInitAction", 72: "DoABC", 82: "DoABC", 7: "DefineButton", 34: "DefineButton2",
              57: "ImportAssets", 71: "ImportAssets2", 58: "EnableDebugger", 64: "EnableDebugger2", 69: "FileAttributes"}


def flash_tags(data: bytes) -> list[tuple[int, int, bytes]]:
    """Every tag of a Flash menu, sprites' own tags included, in order: [(the sprite it's in or 0, tag, its bytes)].
    CheckError when the file doesn't read cleanly to its end."""
    if data[:3] == b"CFX" or data[:3] == b"CWS":
        try:
            body = zlib.decompress(data[8:])
        except zlib.error as exc:
            raise CheckError(f"the Flash menu doesn't unpack ({exc})") from None
        data = data[:8] + body
    elif data[:3] not in (b"GFX", b"FWS"):
        raise CheckError("not a Flash menu")
    if struct.unpack_from("<I", data, 4)[0] != len(data):
        raise CheckError("the Flash menu's length isn't what it says")
    bits = data[8] >> 3
    p = 8 + (5 + 4 * bits + 7) // 8 + 4
    out: list[tuple[int, int, bytes]] = []

    def read(p: int, end: int, sprite: int, depth: int) -> int:
        while p < end:
            if p + 2 > end:
                raise CheckError("the Flash menu ends in the middle of a tag")
            word = struct.unpack_from("<H", data, p)[0]
            code, length = word >> 6, word & 0x3F
            p += 2
            if length == 0x3F:
                if p + 4 > end:
                    raise CheckError("the Flash menu ends in the middle of a tag")
                length = struct.unpack_from("<I", data, p)[0]
                p += 4
            if p + length > end:
                raise CheckError("a tag of the Flash menu runs past its end")
            payload = bytes(data[p:p + length])
            out.append((sprite, code, payload))
            if code == 39:
                if depth > 32 or length < 4:
                    raise CheckError("a sprite of the Flash menu is cut short or nested too deep")
                inner_end = read(p + 4, p + length, struct.unpack_from("<H", payload, 0)[0], depth + 1)
                if inner_end != p + length:
                    raise CheckError("a sprite of the Flash menu doesn't end where it says")
            p += length
            if code == 0:
                return p
        if sprite:
            raise CheckError("a sprite of the Flash menu has no end")
        return p

    if read(p, len(data), 0, 0) != len(data):
        raise CheckError("the Flash menu has bytes past its end")
    return out


def _flash_code(tags: list[tuple[int, int, bytes]]) -> list[tuple[int, int, bytes]]:
    """The tags a mod may not change: code, the files it loads, and every tag that isn't layout, shapes or words."""
    out = []
    for sprite, code, payload in tags:
        if code in (26, 70) and payload and payload[0] & 0x80:  # a placed object carrying code of its own
            out.append((sprite, code, payload))
        elif code == 37 and any(m in payload.lower() for m in FLASH_TEXT_CODE):  # words that load or call
            out.append((sprite, code, payload))
        elif code == 1001:
            _external_image(payload)
        elif code not in FLASH_FREE:
            out.append((sprite, code, payload))
    return out


def _external_image(payload: bytes) -> None:
    """A picture the menu shows from beside it in its pack: by a plain file name, nothing else."""
    try:
        p = 8
        export = payload[p]
        p += 1 + export
        name = payload[p + 1:p + 1 + payload[p]].decode("ascii")
    except (IndexError, UnicodeDecodeError):
        raise CheckError("a picture the Flash menu shows has no proper file name") from None
    if not name or any(c in name for c in "/\\:") or ".." in name:
        raise CheckError(f"a picture the Flash menu shows names a file elsewhere ({name!r}): only a picture beside it")


def check_flash(data: bytes, base: bytes | None) -> int:
    """Check a Flash menu: every tag reads cleanly, and its code (and the files it loads) is the game's own menu's,
    `base`, unchanged. A new menu (no `base`) may hold no code at all. Returns how many tags it has."""
    tags = flash_tags(data)
    mine = _flash_code(tags)
    theirs = _flash_code(flash_tags(base)) if base is not None else []
    if mine != theirs:
        names = sorted({FLASH_CODE.get(c, f"tag {c}") for _s, c, _p in
                        [t for t in mine if t not in theirs] + [t for t in theirs if t not in mine]})
        # not a game rule: the owner's safeguard 5 (a program goes in only as the game's own, or RUSE 2.0-approved)
        raise CheckError(f"its code isn't the game's ({', '.join(names)} changed): a Flash menu's code can't be "
                         f"changed until RUSE 2.0 approves it")
    return len(tags)


# --- shaders (the game's shader file: compiled Direct3D 9 shaders, shader model 3) ---
SM3_OPCODES = set(range(0, 49)) | set(range(64, 97))  # the instructions of vs_3_0 / ps_3_0 (and the 1.x-2.x ones)
SHADER_CLASSES = ["TShaderCompiledCache", "TShaderCompiledCacheEntry", "TStreamedShaderParameterInfos",
                  "TShaderParameterInfo"]


def check_shader_code(code: bytes) -> str:
    """Check one compiled shader, instruction by instruction: a vs_3_0 or ps_3_0 version, each instruction a known one
    with all its words there, comments inside the shader, and the end mark at its very end. Returns "vs_3_0"..."""
    if len(code) < 8 or len(code) % 4:
        raise CheckError("a shader is cut short")
    words = struct.unpack_from(f"<{len(code) // 4}I", code, 0)
    version = words[0]
    if version >> 16 not in (0xFFFE, 0xFFFF) or (version >> 8) & 0xFF != 3:
        # rule: shader-model-3
        raise CheckError("a shader of another kind than the game's (vs_3_0 / ps_3_0)")
    i = 1
    while i < len(words):
        w = words[i]
        op = w & 0xFFFF
        if w == 0x0000FFFF:
            if i != len(words) - 1:
                raise CheckError("a shader has words past its end mark")
            return ("ps" if version >> 16 == 0xFFFF else "vs") + "_3_0"
        if op == 0xFFFE:
            i += 1 + (w >> 16)
        elif op in SM3_OPCODES and not w & 0x80000000:
            i += 1 + ((w >> 24) & 0x0F)
        else:
            raise CheckError(f"a shader has an instruction no shader has ({w:#010x})")
        if i > len(words):
            raise CheckError("a shader's last instruction is cut short")
    raise CheckError("a shader has no end mark")


def shader_programs(data: bytes) -> list[bytes]:
    """Every compiled shader in the game's shader file, unpacked, in order; CheckError when the file or a shader in it
    doesn't read as one."""
    from .ndf import Ndf
    try:
        ndf = Ndf(data)
    except Exception as exc:  # the reader says what's wrong its own way
        # not a game rule: the file isn't the kind its name says
        raise CheckError(f"not the game's shader file ({type(exc).__name__}: {exc})") from None
    if ndf.classes != SHADER_CLASSES:
        # not a game rule: the file isn't the kind its name says
        raise CheckError("not the game's shader file (it holds other things)")
    code_i = ndf.prop_index("ObjectCode")
    out = []
    for obj in ndf.objects:
        v = obj.get(code_i)
        if v is None:
            continue
        p = v.payload
        if len(p) < 9:
            raise CheckError("a shader in the file is cut short")
        packed, _flag, size = struct.unpack_from("<IBI", p, 0)
        z = zlib.decompressobj()
        try:
            code = z.decompress(p[9:], size + 1)
        except zlib.error as exc:
            raise CheckError(f"a shader in the file doesn't unpack ({exc})") from None
        if len(code) != size or packed != len(p) - 5:
            raise CheckError("a shader in the file isn't the size it says")
        check_shader_code(code)
        out.append(code)
    return out


def check_shaders(data: bytes, base: bytes | None, approved=frozenset()) -> int:
    """Check the game's shader file: every shader in it reads as one (check_shader_code), and each is the game's own
    (`base`'s) or one RUSE 2.0 approved (`approved`: SHA-256s, none until the approvals exist). Returns how many."""
    import hashlib
    mine = shader_programs(data)
    theirs = set(shader_programs(base)) if base is not None else set()
    changed = [c for c in mine if c not in theirs and hashlib.sha256(c).hexdigest() not in approved]
    if changed:
        raise CheckError(f"{len(changed)} shader{'s' if len(changed) != 1 else ''} in it changed: a shader can't be "
                         f"changed until RUSE 2.0 approves it")
    return len(mine)
