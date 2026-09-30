"""The game's 3D models, for drawing in the Studio: every mesh pack's models found by name (rusemod.spk), decoded,
and their texture atlases as pictures. Read-only.

Built on the notes of DomesticNukes and his Claude (2026-09-29): a scenery type's descriptor names its model
(`ModelASE`, e.g. ww2\\res3d\\decors\\vegetation_eu\\022lod0.ase2ndfbin); the name is a key in one mesh pack's name
table; each draw call's material names an atlas image (`ZZ:\\GenTexGroup\\...\\X01.png`), which is the texture
`gen\\...\\x01.tgv` in ZZ_Win.dat; each vertex's UV is already moved into its part of the atlas (spk.Part.uvs).

`map_models` writes everything one map needs into a cache folder, once: a binary file with every model's buffers
and one PNG per atlas, plus the index the Studio's map view reads (JSON-ready).
"""
from __future__ import annotations

import hashlib
import json
import struct
import zlib
from array import array
from pathlib import Path

from .build import find_pack
from .edat import Edat
from .spk import Spk, SpkError

PACKS = "gen_5\\pack\\"
TEXTURE_ROLES = ("diffuseTexture", "CombinedDSCTexture", "CombinedDSTexture")  # the picture to draw, best first
MEDIUM = "_lodmedium"  # a lighter version some models have, for the middle distance (what a map view mostly shows)
PICTURE_SIDE = 512     # atlases are drawn from a mip level at most this wide: plenty from the map view's distance


def medium_name(model: str) -> str:
    """The lighter model's name next to a close-up one: ...\\batimentvillage_alod0.ase2ndfbin ->
    ...\\batimentvillage_a_lodmediumlod0.ase2ndfbin."""
    return model[:-len("lod0.ase2ndfbin")] + MEDIUM + "lod0.ase2ndfbin" if model.endswith("lod0.ase2ndfbin") else model


def texture_member(path: str) -> str:
    """The .tgv in ZZ_Win.dat behind a material's image name: ZZ:\\GenTexGroup\\WW2\\...\\X01.png ->
    gen\\ww2\\...\\x01.tgv."""
    p = path.replace("/", "\\")
    for head in ("zz:\\gentexgroup\\", "zz:\\"):
        if p.lower().startswith(head):
            p = "gen\\" + p[len(head):]
            break
    if p.lower().endswith((".png", ".tga", ".dds")):
        p = p[:-4] + ".tgv"
    return p.lower()


class Library:
    """The models of the game at `game`, found by name across its mesh packs (their name tables are read once:
    about a tenth of a second for all of them)."""

    def __init__(self, game: Path):
        path = find_pack(Path(game), "ZZ_Win.dat")
        if path is None:
            raise FileNotFoundError(f"ZZ_Win.dat isn't in {game}")
        self.arc = Edat.open(str(path))
        self.where: dict[str, Spk] = {}
        for e in self.arc.entries:
            p = e.path.lower()
            if not (p.startswith(PACKS) and p.endswith(".spk")):
                continue
            try:
                spk = Spk(bytes(self.arc.read(e)))
            except SpkError:  # a skeleton pack
                continue
            for name in spk.items:
                self.where.setdefault(name, spk)

    def close(self) -> None:
        self.arc.close()

    def find(self, model: str, lighter: bool = True) -> str | None:
        """The name to draw for a descriptor's model: its lighter version when there is one (and `lighter`), else
        the model itself; None when no pack has it."""
        model = model.replace("/", "\\").lower()
        if model.startswith("datadir:\\"):
            model = model[len("datadir:\\"):]
        if lighter and medium_name(model) in self.where:
            return medium_name(model)
        return model if model in self.where else None

    def parts(self, name: str) -> list[tuple]:
        """A model's draw calls as (part, texture path or None)."""
        spk = self.where[name]
        mats = spk.materials()
        out = []
        for part in spk.model(name):
            mat = mats[part.material] if part.material < len(mats) else {"textures": {}}
            tex = next((mat["textures"][r] for r in TEXTURE_ROLES if r in mat["textures"]), None)
            out.append((part, tex))
        return out

    def picture(self, texture: str) -> tuple[int, int, bytes] | None:
        """An atlas as RGBA pixels (width, height, bytes), from a mip level at most PICTURE_SIDE wide; None when it
        isn't there or its codec isn't read yet (TGU1 with alpha)."""
        from . import dxt, tgu1
        from .tmst import Tgv, zipo_unpack
        entry = self.arc.entry(texture_member(texture))
        if entry is None:
            return None
        tgv = Tgv(bytes(self.arc.read(entry)))
        # mip levels are listed smallest first: the last one is the full picture, each one before it half as wide
        mip, w, h = len(tgv.mips) - 1, tgv.width, tgv.height
        while max(w, h) > PICTURE_SIDE and mip > 0:
            mip, w, h = mip - 1, max(4, w // 2), max(4, h // 2)
        payload = tgv.payload(mip)
        try:
            if payload[:4] == b"TGU1":
                head = tgu1.Header.parse(payload)
                w, h = head.width * 4, head.height * 4  # its own size, in blocks (a TGV can say more than it stores)
                blocks = tgu1.decode(payload)  # DXT1 only: TGU1 with alpha isn't read yet
            elif payload[:4] == b"ZIPO":
                blocks = zipo_unpack(payload)
            else:
                blocks = payload
            return w, h, bytes(dxt.decode_rgba(blocks, w, h, tgv.format))
        except (ValueError, struct.error, IndexError, KeyError, zlib.error):  # a variant not read yet
            return None


def map_models(game: Path, types: list, out_dir: Path, say=None) -> dict:
    """Everything a map view needs to draw `types` (the map's scenery types, [short name, group, category, model,
    [every model]] as rusemod.scenery.view gives them) as real models, written into `out_dir`: `<key>.bin` (every model's buffers,
    little-endian) and one PNG per atlas. Returns the index: {"bin": file name, "models": {type number: [part]},
    "textures": {texture: png file name or null}}, a part being {"texture", "vertices", "triangles", "positions",
    "normals", "uvs", "indices"} with byte offsets into the .bin (positions: 3 f32, normals: 4 i8, uvs: 2 f32 per
    vertex; indices: u32). Model units are the map's; x east, y south, z up."""
    lib = Library(game)
    try:
        # each type's models (a tree: its leaves and its trunk), as the packs name them
        names = {}
        for i, t in enumerate(types):
            wanted = t[4] if len(t) > 4 and t[4] else ([t[3]] if t[3] else [])
            found = [n for n in (lib.find(w) for w in wanted) if n]
            if found:
                names[i] = tuple(found)
        key = hashlib.sha1(json.dumps(sorted(set(names.values()))).encode()).hexdigest()[:16]
        out_dir.mkdir(parents=True, exist_ok=True)
        index_file = out_dir / f"{key}.json"
        if index_file.is_file():
            return json.loads(index_file.read_text(encoding="utf-8"))
        blob = bytearray()
        models: dict[str, list] = {}
        textures: dict[str, str | None] = {}
        done: dict[str, list] = {}
        for i, group in names.items():
            if group not in done:
                parts = []
                for part, tex in (pt for name in group for pt in lib.parts(name)):
                    n = len(part.positions) // 3
                    if not n or not part.indices:
                        continue
                    rec = {"texture": tex, "vertices": n, "triangles": len(part.indices) // 3}
                    for field, typed in (("positions", array("f", part.positions)),
                                         ("normals", array("b", [max(-127, min(127, round(c * 127)))
                                                                 for k in range(n) for c in
                                                                 (part.normals[3 * k:3 * k + 3] or [0, 0, 1]) + [0]])),
                                         ("uvs", array("f", part.uvs if len(part.uvs) == 2 * n else [0.0] * (2 * n))),
                                         ("indices", array("I", part.indices))):
                        rec[field] = len(blob)
                        blob += typed.tobytes()
                        blob += bytes(-len(blob) % 4)
                    parts.append(rec)
                    if tex is not None:
                        textures.setdefault(tex, None)
                done[group] = parts
            models[str(i)] = done[group]
        for k, tex in enumerate(sorted(textures)):
            if say:
                say(f"{k + 1}/{len(textures)}")
            pic = lib.picture(tex)
            if pic is None:
                continue
            from .dxt import png_bytes
            w, h, rgba = pic
            png = hashlib.sha1(tex.lower().encode()).hexdigest()[:16] + ".png"
            (out_dir / png).write_bytes(png_bytes(rgba, w, h, channels=4))
            textures[tex] = png
        (out_dir / f"{key}.bin").write_bytes(bytes(blob))
        index = {"bin": f"{key}.bin", "models": models, "textures": textures}
        part_file = index_file.with_name(index_file.name + ".part")
        part_file.write_text(json.dumps(index), encoding="utf-8")
        part_file.replace(index_file)
        return index
    finally:
        lib.close()
