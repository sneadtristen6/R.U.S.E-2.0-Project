"""Every file of the game's packs, read only: LittleGroove's Raw / Asset Editor's Browse / Files brought over (the Studio's
Files tab). The six packs of the game's data revision and each map's own pack (Maps/PC), their files listed by path
with a kind and a size, a pack stored inside a pack opened as one (as deep as they go), one file shown as what it is
(a summary of an NDF file, a texture or a picture as a PNG, a text table's rows, a mission script as text, a text, or
its first bytes), and any of them saved out. Nothing here writes into the game: changing a file is the build's
(mods change the game through the formats of docs/MOD_FORMAT.md)."""
from __future__ import annotations

import struct
import zlib
from collections import Counter
from pathlib import Path, PurePosixPath

from .edat import MAGIC as PACK_MAGIC, Edat

# the six packs of the game's data revision, in his editor's order: (id, file name)
PACKS = (("gameplay", "ZZ_GladPatchableWin.dat"), ("gameplay_fixed", "ZZ_GladNotPatchableWin.dat"),
         ("scripts", "IA_Common.dat"), ("maps", "DataMap_Win.dat"), ("texts", "ZZ_Win.dat"),
         ("common", "Data_Common.dat"))
MAP_PREFIX = "map:"     # a map's own pack: map:<its file name>
LISTED_MOST = 6000      # the most files a list shows (the count says how many match)
BYTES_SHOWN = 8192      # the first bytes shown of a file of no other kind
TEXT_MOST = 200_000     # the most letters of a text shown
ROWS_MOST = 4000        # the most rows of a text table shown
PICTURE_MOST = 720      # a picture's preview: at most this wide or high

KINDS = {  # a file's kind by its ending (his editor's table); a pack is also found by what it starts with
    "ndf": (".gladndfbin", ".ndfbin", ".truendfbin"),
    "texture": (".tgv", ".tgv_pc"),
    "image": (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tga", ".dds"),
    "table": (".dic",),
    "script": (".xyz",),
    "text": (".xml", ".txt", ".ndf", ".lua", ".cfg", ".ini", ".csv", ".json", ".scenario"),
    "pack": (".ipk", ".apk", ".mpk", ".ppk", ".dat"),
}


class PackFileError(ValueError):
    """What can't be shown (a pack or a file that isn't there, a nested file that isn't a pack)."""


def kind_of(path: str) -> str:
    low = path.lower()
    return next((k for k, ends in KINDS.items() if low.endswith(ends)), "binary")


def packs(game: Path) -> list[dict]:
    """[{id, file, size, map}] of the packs there are: the six of the newest data revision, then each map's pack."""
    from .build import find_pack
    out = []
    for pid, name in PACKS:
        p = find_pack(game, name)
        if p is not None and p.parent.parent.name.lower() != "maps":
            out.append({"id": pid, "file": p.name, "size": p.stat().st_size, "map": False})
    maps = Path(game) / "Maps" / "PC"
    for p in sorted(maps.glob("*.dat"), key=lambda f: f.name.lower()) if maps.is_dir() else []:
        out.append({"id": MAP_PREFIX + p.name, "file": p.name, "size": p.stat().st_size, "map": True})
    return out


def pack_path(game: Path, pack_id: str) -> Path:
    """The file of pack `pack_id` (packs()'s id)."""
    from .build import find_pack
    if pack_id.startswith(MAP_PREFIX):
        name = pack_id[len(MAP_PREFIX):]
        p = Path(game) / "Maps" / "PC" / name
        if PurePosixPath(name).name != name or not p.is_file():
            raise PackFileError(f"there's no map pack {name}")
        return p
    name = dict(PACKS).get(pack_id)
    p = find_pack(game, name) if name else None
    if p is None:
        # not a game rule: the page asked for a pack this copy of the game hasn't got
        raise PackFileError(f"there's no pack {pack_id!r} in this game")
    return p


class Opened:
    """Pack `pack_id`, and the packs inside it `nested` names (each a file's path in the one before), opened: `arc` is
    the innermost. Close it (a with block) to let the game's file go."""

    def __init__(self, game: Path, pack_id: str, nested=()):
        self._top = Edat.open(str(pack_path(game, pack_id)))
        self.arc = self._top
        try:
            for path in nested or ():
                e = self.arc.entry(str(path))
                if e is None:
                    raise PackFileError(f"there's no {path} in the pack")
                raw = bytes(self.arc.read(e))
                if raw[:4] != PACK_MAGIC:
                    raise PackFileError(f"{path} isn't a pack")
                self.arc = Edat(raw)
        except Exception:
            self._top.close()
            raise

    def read(self, path: str) -> bytes:
        e = self.arc.entry(str(path))
        if e is None:
            raise PackFileError(f"there's no {path} in the pack")
        return bytes(self.arc.read(e))

    def __enter__(self) -> "Opened":
        return self

    def __exit__(self, *exc) -> None:
        self._top.close()


def listing(game: Path, pack_id: str, nested=(), words: str = "") -> dict:
    """The files of a pack (or of a pack inside it), by path: {files: [{path, kind, size}], total, matching}, the ones
    whose path has `words` (any case), at most LISTED_MOST."""
    words = words.strip().lower().replace("/", "\\")
    with Opened(game, pack_id, nested) as o:
        found = [e for e in o.arc.entries if not words or words in e.path.lower()]
        total = len(o.arc.entries)
    return {"files": [{"path": e.path, "kind": kind_of(e.path), "size": e.size} for e in found[:LISTED_MOST]],
            "total": total, "matching": len(found)}


def _hex(raw: bytes) -> list[str]:
    """The first BYTES_SHOWN bytes as hex dump lines: offset, 16 bytes, and their printable letters."""
    out = []
    for at in range(0, min(len(raw), BYTES_SHOWN), 16):
        row = raw[at:at + 16]
        out.append(f"{at:08x}  {row.hex(' '):<47}  " + "".join(chr(b) if 32 <= b < 127 else "." for b in row))
    return out


def texture_rgba(raw: bytes, most: int = PICTURE_MOST) -> tuple[int, int, bytes]:
    """A TGV texture as RGBA pixels (width, height, bytes), from its largest mip level at most `most` wide or high
    (models.Models.picture's way). ValueError when its codec or format isn't read."""
    from . import dxt, tgu1
    from .tmst import Tgv, zipo_unpack
    tgv = Tgv(raw)
    mip, w, h = len(tgv.mips) - 1, tgv.width, tgv.height  # (smallest first: the last is the full picture)
    while max(w, h) > most and mip > 0:
        mip, w, h = mip - 1, max(4, w // 2), max(4, h // 2)
    payload = tgv.payload(mip)
    fmt = tgv.format.upper().removesuffix("_LIN")  # (the game's formats, 2026-10-08: DXT1, DXT5, A8R8G8B8, L8, A8L8)
    try:
        if payload[:4] == b"TGU1":
            head = tgu1.Header.parse(payload)
            w, h = head.width * 4, head.height * 4
            data = tgu1.decode(payload)
        elif payload[:4] == b"ZIPO":
            data = zipo_unpack(payload)
        else:
            data = payload
        if fmt in ("DXT1", "DXT5"):
            return w, h, bytes(dxt.decode_rgba(data, w, h, fmt))
        per = {"A8R8G8B8": 4, "X8R8G8B8": 4, "L8": 1, "A8L8": 2}.get(fmt)
        if per is None or len(data) < w * h * per:
            raise ValueError(f"{tgv.format} isn't read here" if per is None
                             else f"{len(data)} bytes for a {w}x{h} {tgv.format} picture")
        px = bytearray(w * h * 4)
        if per == 4:  # B, G, R, A in memory
            px[0::4], px[1::4], px[2::4] = data[2:w * h * 4:4], data[1:w * h * 4:4], data[0:w * h * 4:4]
            px[3::4] = data[3:w * h * 4:4] if fmt == "A8R8G8B8" else bytes([255]) * (w * h)
        elif per == 1:
            px[0::4] = px[1::4] = px[2::4] = data[:w * h]
            px[3::4] = bytes([255]) * (w * h)
        else:  # L, A
            px[0::4] = px[1::4] = px[2::4] = data[0:w * h * 2:2]
            px[3::4] = data[1:w * h * 2:2]
        return w, h, bytes(px)
    except (struct.error, IndexError, KeyError, zlib.error) as exc:
        raise ValueError(f"{tgv.format} texture not read: {exc}") from None


def _png_rgba(w: int, h: int, rgba: bytes) -> bytes:
    from .dxt import png_bytes
    return png_bytes(rgba, w, h, channels=4)


def preview(game: Path, pack_id: str, nested, path: str) -> dict:
    """One file shown as what it is: {path, kind, size, ...}: "ndf" (objects, kinds of object, property names,
    packed, the 12 most used kinds), "picture" (png: the PNG's bytes, width, height, format), "table" (rows: [key, text]
    of a text table, its count), "script" (text), "scenario" (zones, items: [kind, how many]), "text" (text), "pack"
    (files: how many), else "bytes" (lines: a hex dump of its first bytes, `more`: how many bytes aren't shown). A file
    not read as its kind is shown as bytes, with `why`."""
    with Opened(game, pack_id, nested) as o:
        raw = o.read(path)
    return preview_bytes(path, raw)


def preview_bytes(path: str, raw: bytes) -> dict:
    """preview() of a file's bytes (`path` names its kind): the game's, or a mod's version of it."""
    kind = "pack" if raw[:4] == PACK_MAGIC else kind_of(path)
    out = {"path": path, "kind": kind, "size": len(raw)}
    try:
        if kind == "pack":
            return out | {"files": len(Edat(raw).entries)}
        if kind == "ndf":
            from .ndf import Ndf
            nd = Ndf(raw)
            used = Counter(nd.classes[ob.cls] for ob in nd.objects)
            return out | {"objects": len(nd.objects), "classes": len(nd.classes), "props": len(nd.props),
                          "packed": bool(nd.flags & 0x80), "top": used.most_common(12)}
        if kind == "texture":
            from .tmst import Tgv
            w, h, rgba = texture_rgba(raw)
            return out | {"kind": "picture", "png": _png_rgba(w, h, rgba), "width": w, "height": h,
                          "full": [Tgv(raw).width, Tgv(raw).height], "format": Tgv(raw).format}
        if kind == "image" and raw[:8] == b"\x89PNG\r\n\x1a\n":
            from .png import read_png
            w, h, _px = read_png(raw)
            return out | {"kind": "picture", "png": raw, "width": w, "height": h, "full": [w, h], "format": "PNG"}
        if kind == "table":
            from .dic import GLYPH_KEY, Dic
            d = Dic(raw)
            rows = [[e.name or f"0x{e.key:016X}", e.text] for e in d.entries if e.key != GLYPH_KEY]
            return out | {"rows": rows[:ROWS_MOST], "count": len(rows)}
        if kind == "script":
            from . import mapscripts
            if mapscripts.missing() is None:
                return out | {"text": mapscripts.text(raw)[:TEXT_MOST]}
            out["why"] = "this copy of the apps can't show scripts"
        elif path.lower().endswith(".scenario"):
            from .scenario import Scenario
            s = Scenario.read(raw)
            return out | {"kind": "scenario", "zones": len(s.zones),
                          "items": Counter(it.kind or "plain" for it in s.items).most_common()}
        elif _looks_like_text(raw):
            return out | {"kind": "text", "text": _decoded(raw)[:TEXT_MOST]}
    except (ValueError, struct.error, IndexError, KeyError, zlib.error, UnicodeError) as exc:
        out["why"] = f"{type(exc).__name__}: {exc}"
    return out | {"kind": "bytes", "lines": _hex(raw), "more": max(0, len(raw) - BYTES_SHOWN)}


def _decoded(raw: bytes) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", "replace")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _looks_like_text(raw: bytes) -> bool:
    """Whether a file of no known kind is a text: its first bytes are printable (UTF-8 or UTF-16 with a mark)."""
    head = raw[:4096]
    if not head or head[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return bool(head)
    try:
        s = head.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return all(c.isprintable() or c in "\r\n\t" for c in s)


def save_out(game: Path, pack_id: str, nested, path: str, out: Path) -> Path:
    """Save one file of a pack (or of a pack inside it) out to `out`, as the game has it."""
    with Opened(game, pack_id, nested) as o:
        raw = o.read(path)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    return out
