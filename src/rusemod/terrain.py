"""Maps and their ground, for the Studio's map view: the game's own map list, and one map's terrain as flat buffers
ready to draw. Read-only: nothing here writes anything.

The ground is the map's visual mesh (`output\\highdef.tms`, or the coarser `output\\lowdef.tms`; FORMATS.md §6
"Terrain") with every cell merged: cell vertices are whole-map coordinates, so the cells simply stack. The picture
draped on it is the map's own overview texture (`output\\terrain.png`), north up like the minimap: world y grows
toward the south, so image row = y / map size, with no flip.
"""
from __future__ import annotations

import base64
import struct
import sys
import zlib
from array import array
from pathlib import Path

from . import loc
from .build import find_pack
from .dic import Dic
from .edat import Edat
from .ndf import Ndf
from .tms import Q_MAX, Tms

MAP_LIST = ("ZZ_GladPatchableWin.dat", "genglad\\patchable\\mapinfo.cpp.gladndfbin")
MENUS = "genglad\\patchable\\misc\\globals.cpp.gladndfbin"  # the menus' entries for the maps, in the same pack
# What the menus call a map, best first: a multiplayer map's name, else a campaign chapter's, else a challenge's.
MENU_CLASSES = ("TMultiMapInfo", "TChapterMapInfo", "TChallengeMapInfo")
MENU_TEXTS = "flash_txt"  # the dictionary those names are in, one per language (rusemod.loc)
LODS = {"highdef": "output\\highdef.tms", "lowdef": "output\\lowdef.tms"}
PICTURE = "output\\terrain.png"
_TEXT = (0x07, 0x1C)  # a string or a path: an index into the file's string table
_GUID, _TEXT_KEY = 0x1A, 0x1D  # 16 bytes; a text key (u64) into a .dic


def pack_file(root: str) -> str:
    """The map pack a map's `RootDatapackName` stands for (the name the game mounts it by, FORMATS.md §6)."""
    return f"DataMap{root}_v09.dat"


def menu_keys(nd: Ndf) -> dict[bytes, list[tuple[int, int]]]:
    """The menus' map entries (`MENUS`): GUID -> [(rank, text key)], the text keys of what the menus call the map a
    `TMapLoadInfo` with that GUID loads. Rank: the entry's class's place in `MENU_CLASSES` (0 = a multiplayer map)."""
    ranks = {c: r for r, c in enumerate(MENU_CLASSES)}
    out: dict[bytes, list[tuple[int, int]]] = {}
    for obj in nd.objects:
        rank = ranks.get(nd.classes[obj.cls])
        if rank is None:
            continue
        values = {nd.prop_name(pi): v for pi, v in obj.props}
        guid, name = values.get("GUID"), values.get("Description")
        if guid is None or name is None or guid.tc != _GUID or name.tc != _TEXT_KEY:
            continue
        out.setdefault(bytes(guid.payload), []).append((rank, struct.unpack("<Q", name.payload)[0]))
    return out


def maps_from_ndf(nd: Ndf, menus: dict | None = None) -> list[dict]:
    """Every `TMapLoadInfo` of the map list, grouped by terrain pack, in the game's order: {pack, names, paths, keys}.
    Several entries (a skirmish map and campaign missions, say) can share one pack, and a pack named in two
    spellings (M04_cotentin, M04_Cotentin) is one file. `keys`: the text keys of what the menus call its entries,
    best first (from `menus`, see `menu_keys`; none without)."""
    wanted = {i for i, c in enumerate(nd.classes) if c == "TMapLoadInfo"}
    by_pack: dict[str, dict] = {}
    ranked: dict[str, list[tuple[int, int]]] = {}
    for obj in nd.objects:
        if obj.cls not in wanted:
            continue
        texts = {nd.prop_name(pi): nd.strings[struct.unpack("<I", v.payload)[0]]
                 for pi, v in obj.props if v.tc in _TEXT}
        root = texts.get("RootDatapackName") or texts.get("Path")
        if not root:
            continue
        entry = by_pack.setdefault(root.lower(), {"pack": root, "names": [], "paths": [], "keys": []})
        if texts.get("Name") and texts["Name"] not in entry["names"]:
            entry["names"].append(texts["Name"])
        if texts.get("Path") and texts["Path"] not in entry["paths"]:
            entry["paths"].append(texts["Path"])
        guid = next((bytes(v.payload) for pi, v in obj.props if v.tc == _GUID and nd.prop_name(pi) == "GUID"), None)
        ranked.setdefault(root.lower(), []).extend((menus or {}).get(guid, []))
    for pack, keys in ranked.items():
        for _rank, key in sorted(keys, key=lambda rk: rk[0]):  # stable: the game's order within a rank
            if key not in by_pack[pack]["keys"]:
                by_pack[pack]["keys"].append(key)
    return list(by_pack.values())


def menu_texts(game: Path, keys) -> dict[str, dict[int, str]]:
    """Language -> {text key: text} for `keys`, from each language's menu texts (`MENU_TEXTS`); a language whose file
    isn't there is left out."""
    zz = find_pack(game, loc.PACK)
    if zz is None or not keys:
        return {}
    out = {}
    with Edat.open(str(zz)) as arc:
        for lang in loc.LANGS:
            e = arc.entry(loc.member(MENU_TEXTS, lang))
            if e is None:
                continue
            dic = Dic(bytes(arc.read(e)))
            out[lang] = {k: " ".join(t.split()) for k in keys if (t := dic.text(k)) and t.strip()}
    return out


def map_list(game: Path) -> list[dict]:
    """The game's maps, one per terrain pack: the names the game lists them by, whether the pack is there, and
    `titles`, what the menus call it in each language ({lang: [names]}, best first as in `MENU_CLASSES`; none for
    the test maps no menu shows)."""
    core = find_pack(game, MAP_LIST[0])
    if core is None:
        raise FileNotFoundError(f"{MAP_LIST[0]} isn't in {game}")
    with Edat.open(str(core)) as arc:
        nd = Ndf(bytes(arc.read(arc.find(MAP_LIST[1]))))
        menus = arc.entry(MENUS)
        menus = menu_keys(Ndf(bytes(arc.read(menus)))) if menus is not None else {}
    maps = maps_from_ndf(nd, menus)
    texts = menu_texts(game, {k for m in maps for k in m["keys"]})
    for m in maps:
        keys = m.pop("keys")
        m["titles"] = {lang: [t[k] for k in keys if k in t] for lang, t in texts.items()}
        m["file"] = pack_file(m["pack"])
        m["found"] = find_pack(game, m["file"]) is not None
    return maps


def _pack(a: array) -> str:
    """Little-endian array -> zlib -> base64 (the window unpacks it with DecompressionStream("deflate"))."""
    if sys.byteorder != "little":
        a = array(a.typecode, a)
        a.byteswap()
    return base64.b64encode(zlib.compress(a.tobytes(), 6)).decode("ascii")


def mesh_buffers(tms: Tms) -> dict:
    """All cells of a terrain mesh merged into flat buffers, each packed by `_pack`: `positions` (x, y, z per vertex,
    uint16, quantized 0..32767 over `bounds`), `normals` (the game's own: x, y, z bytes per vertex, n = b / 127.5 - 1),
    `water_heights` (each vertex's water surface, uint16, same z scale), `triangles` (vertex numbers, uint32) and
    `water` (the triangles under water). World = min + q / 32767 * (max - min) per axis; `bounds` = min x, y, z,
    max x, y, z (world units). Game axes: x east, y south, z up."""
    pos, nrm, wat, tri, wtri = array("H"), array("B"), array("H"), array("I"), array("I")
    base = 0
    for cell in tms.cells:
        verts = cell.positions()
        for (x, y, z, w), (nx, ny, nz, _) in zip(verts, cell.normals()):
            pos.extend((x, y, z))
            nrm.extend((nx, ny, nz))
            wat.append(w)
        tri.extend(base + i for i in cell.triangles(0))
        wtri.extend(base + i for i in cell.triangles(1))
        base += len(verts)
    if pos.itemsize != 2 or tri.itemsize != 4:
        raise RuntimeError("this Python's array sizes aren't 2 and 4 bytes")
    return {"bounds": list(tms.bounds), "q_max": Q_MAX, "vertices": base, "triangle_count": len(tri) // 3,
            "positions": _pack(pos), "normals": _pack(nrm), "water_heights": _pack(wat), "triangles": _pack(tri),
            "water": _pack(wtri)}


def _tile_rgb(tex) -> bytes:
    """One terrain tile (a one-mip DXT1 TGV) as RGB pixels: its TGU1 or ZIPO payload decoded (FORMATS.md §6)."""
    from . import dxt, tgu1
    payload = tex.payload(0)
    if payload[:4] == b"TGU1":
        blocks = tgu1.decode(payload)
    elif payload[:4] == b"ZIPO":
        blocks = zlib.decompressobj().decompress(payload[8:])
    else:
        raise ValueError(f"unknown tile payload {payload[:4]!r}")
    return bytes(dxt.decode(blocks, tex.width, tex.height))


def ground_picture(game: Path, pack: str, level: int | None = None, progress=None) -> tuple[int, int, bytes]:
    """The map's ground as one RGB picture, north up, stitched from its real texture tiles (the highdef tile store)
    at `level` (0 = the finest; default: the level with one tile per terrain cell, 3,072 px on Two Islands).
    `progress(done, total)` is called after each tile. Returns (width, height, RGB bytes)."""
    from .tmst import Tmst
    path = find_pack(game, pack_file(pack))
    if path is None:
        raise FileNotFoundError(f"{pack_file(pack)} isn't in {game}")
    with Edat.open(str(path)) as arc:
        store = Tmst.from_edat(arc, "highdef")
        if level is None:
            level = store.depth - 1
        tiles = [t for t in store.tiles if t.level == level]
        if not tiles:
            raise ValueError(f"{pack} has no terrain tiles at level {level}")
        side_w, side_h = max(t.x for t in tiles) + 1, max(t.y for t in tiles) + 1
        first = store.texture(tiles[0])
        tw, th = first.width, first.height
        width, height = side_w * tw, side_h * th
        out = bytearray(width * height * 3)
        for n, tile in enumerate(tiles, 1):
            tex = store.texture(tile)
            if (tex.width, tex.height) != (tw, th):
                raise ValueError(f"{pack}: tiles of level {level} differ in size")
            rgb = _tile_rgb(tex)
            row = tw * 3
            for r in range(th):
                start = ((tile.y * th + r) * width + tile.x * tw) * 3
                out[start:start + row] = rgb[r * row:(r + 1) * row]
            if progress:
                progress(n, len(tiles))
    return width, height, bytes(out)


def ground_png(game: Path, pack: str, out: Path, level: int | None = None, progress=None) -> Path:
    """Write `ground_picture` as a PNG (written next to `out` first, then moved into place)."""
    from .dxt import write_png
    width, height, rgb = ground_picture(game, pack, level, progress)
    out.parent.mkdir(parents=True, exist_ok=True)
    part = out.with_name(out.name + ".part")
    write_png(str(part), rgb, width, height)
    part.replace(out)
    return out


def terrain(game: Path, pack: str, lod: str = "highdef") -> dict:
    """One map's ground, ready to draw: `mesh_buffers` of its `lod` mesh plus its overview picture as a data URL."""
    if lod not in LODS:
        raise ValueError(f"lod must be one of {', '.join(LODS)}")
    path = find_pack(game, pack_file(pack))
    if path is None:
        raise FileNotFoundError(f"{pack_file(pack)} isn't in {game}")
    with Edat.open(str(path)) as arc:
        tms = Tms(bytes(arc.read(arc.find(LODS[lod]))))
        try:
            png = bytes(arc.read(arc.find(PICTURE)))
        except KeyError:
            png = b""
    view = mesh_buffers(tms)
    view.update(pack=pack, lod=lod,
                picture=("data:image/png;base64," + base64.b64encode(png).decode("ascii")) if png else "")
    return view
