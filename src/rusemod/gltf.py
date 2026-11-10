"""The game's 3D models out to glTF 2.0 binary files (.glb), which Blender and other 3D tools open. Read-only.

One model becomes one mesh: each of its draw calls a primitive with its own texture. A unit texture's colour goes
into the .glb; its alpha is not see-through but the player's side colour (low) and shine (high), so it is written
as a grey picture of its own beside the .glb, with the colour as a picture too (for painting).

Skinned models (every unit) keep their bones: one joint per skeleton bone the model uses (through each material's
SkinningRemapping), so the model shows as stored and every vertex keeps its bones and weights. By default the joints
are all at the origin with identity bind matrices, as the paint round trip has always had them. With `rest_bones`
each joint is at its rest pose from the model's skeleton record, laid out the way Blender draws bones (rest_poses:
each frame turned once so the bone runs along the game's +x, a bone the game gives no parent hung from the one that
leads to it), so in Blender the bones stand where the game has them and a mesh of the modder's own can take
Blender's automatic weights from them; the points, bone names and weights are the same bytes either way.

Axes: the game's model x, y, z (z up) are written as glTF's x, z, y (y up), times SCALE. That is a mirror, so
each triangle's winding is reversed too. Which way is right was checked on the T-26: its turret number reads
correctly in Blender this way. Each primitive's `extras` says which model, draw call and material it came from, and
each material's `extras` which texture (its .tgv in ZZ_Win.dat) it shows.

Propeller discs (material type `helice_1`, 43 draw calls on the planes, every one checked 2026-10-04) are a flat
square the game draws with a shader of its own, over the whole of the plane's picture. As a plain square that
picture is just in the way, so they go into a mesh of their own (`<model>_propeller`), which the Studio and Blender
keep hidden. Every unit model's other draw calls are material type `Standard`.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

from .dxt import png_bytes
from .models import texture_member

SCALE = 0.01          # game model units -> glTF metres (a soldier is about 312 units tall)
MIRROR = True         # the game's (x, y, z) -> glTF (x, z, y); False: (x, z, -y)
PROPELLER = "helice"  # material types starting with this are propeller discs
FLOAT, UBYTE, USHORT, UINT = 5126, 5121, 5123, 5125
TRACK_ATTRIBUTE = "_RUSE_TRACK"   # a tank's track number per point (in the game's vertex: the normal's 4th byte)


def _point(x: float, y: float, z: float, scale: float = SCALE) -> tuple[float, float, float]:
    return (x * scale, z * scale, y * scale) if MIRROR else (x * scale, z * scale, -y * scale)


class _Glb:
    """A glTF document being built, with one binary buffer."""

    def __init__(self):
        self.doc = {"asset": {"version": "2.0", "generator": "rusemod.gltf"}, "buffers": [], "bufferViews": [],
                    "accessors": [], "meshes": [], "nodes": [], "scenes": [], "materials": [], "textures": [],
                    "images": [], "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497,
                                                "wrapT": 10497}]}
        self.bin = bytearray()

    def view(self, data: bytes, target: int | None = None) -> int:
        while len(self.bin) % 4:
            self.bin.append(0)
        v = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            v["target"] = target
        self.bin += data
        self.doc["bufferViews"].append(v)
        return len(self.doc["bufferViews"]) - 1

    def accessor(self, values: list, kind: str, ctype: int, target: int | None = 34962, minmax: bool = False,
                 normalized: bool = False) -> int:
        width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[kind]
        code = {FLOAT: "f", UBYTE: "B", USHORT: "H", UINT: "I"}[ctype]
        flat = [c for v in values for c in (v if width > 1 else (v,))]
        data = struct.pack(f"<{len(flat)}{code}", *flat)
        low = [min(v[i] for v in values) for i in range(width)] if minmax else None
        high = [max(v[i] for v in values) for i in range(width)] if minmax else None
        return self.packed(data, len(values), kind, ctype, target, low=low, high=high, normalized=normalized)

    def packed(self, data: bytes, count: int, kind: str, ctype: int, target: int | None = 34962,
               low: list | None = None, high: list | None = None, normalized: bool = False) -> int:
        """An accessor of `count` values already packed (`data`), with their lowest and highest when given."""
        a = {"bufferView": self.view(data, target), "componentType": ctype, "count": count, "type": kind}
        if normalized:
            a["normalized"] = True
        if low is not None:
            a["min"] = low
            a["max"] = high
        self.doc["accessors"].append(a)
        return len(self.doc["accessors"]) - 1

    def image(self, png: bytes, name: str) -> int:
        self.doc["images"].append({"bufferView": self.view(png), "mimeType": "image/png", "name": name})
        self.doc["textures"].append({"sampler": 0, "source": len(self.doc["images"]) - 1})
        return len(self.doc["textures"]) - 1

    def to_bytes(self) -> bytes:
        self.doc["buffers"] = [{"byteLength": len(self.bin)}]
        doc = {k: v for k, v in self.doc.items() if v != []}
        js = json.dumps(doc, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        binary = bytes(self.bin) + b"\0" * (-len(self.bin) % 4)
        total = 12 + 8 + len(js) + 8 + len(binary)
        return (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
                + struct.pack("<I4s", len(binary), b"BIN\0") + binary)


def _split(rgba: bytes) -> tuple[bytes, bytes]:
    """RGBA pixels -> (RGB colour, alpha as grey RGB)."""
    colour = bytearray(len(rgba) // 4 * 3)
    colour[0::3], colour[1::3], colour[2::3] = rgba[0::4], rgba[1::4], rgba[2::4]
    grey = bytearray(len(rgba) // 4 * 3)
    grey[0::3] = grey[1::3] = grey[2::3] = rgba[3::4]
    return bytes(colour), bytes(grey)


PLAIN = 1e-3   # a rest pose whose axes are this close to length one and square to each other is a plain turn


def _rows(m) -> list:
    """A skeleton record's matrix (12 numbers: 3 rows of [r r r t], the game's) as 3 rows of 4."""
    return [list(m[0:4]), list(m[4:8]), list(m[8:12])]


def _flat(rows) -> tuple:
    return tuple(v for row in rows for v in row)


def _after(a, b) -> list:
    """The move `b`, then `a` (3 rows of 4 each)."""
    return [[sum(a[i][k] * b[k][j] for k in range(3)) + (a[i][3] if j == 3 else 0.0) for j in range(4)]
            for i in range(3)]


def _undo(f) -> list:
    """The inverse of a plain turn and move (3 rows of 4)."""
    return [[f[j][i] for j in range(3)] + [-sum(f[j][i] * f[j][3] for j in range(3))] for i in range(3)]


def _det3(r) -> float:
    """The determinant of 3 rows of 3 (below 0: a mirror)."""
    return (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1]) - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
            + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))


def _is_plain(m) -> bool:
    """Whether a rest pose (3 rows of 4) is a plain turn and move: no size, no mirror."""
    cols = [[m[i][j] for i in range(3)] for j in range(3)]
    if any(abs(sum(c * c for c in col) ** 0.5 - 1.0) > PLAIN for col in cols):
        return False
    if any(abs(sum(a * b for a, b in zip(cols[i], cols[j]))) > PLAIN for i, j in ((0, 1), (0, 2), (1, 2))):
        return False
    return _det3([row[:3] for row in m]) > 0


def _plain_turn(m) -> list:
    """The plain turn nearest a rest pose the game sizes or mirrors (3 rows of 4), at the same place: its axes made
    length one and square to each other, x first; a mirroring one's x axis turned round."""
    axes = []
    for j in range(3):
        v = [m[i][j] for i in range(3)]
        for u in axes:
            d = sum(a * b for a, b in zip(v, u))
            v = [a - d * b for a, b in zip(v, u)]
        n = sum(a * a for a in v) ** 0.5 or 1.0
        axes.append([a / n for a in v])
    if _det3(axes) < 0:     # (the axes as rows: the same determinant as the turn they make)
        axes[0] = [-a for a in axes[0]]
    return [[axes[j][i] for j in range(3)] + [m[i][3]] for i in range(3)]


# Blender draws a bone from its place along its own +y axis, which a joint's +y in a .glb becomes; the game's bones
# run along their own +x (the US rifleman's skeleton: 19 of its 30 bone-to-child pairs within 7.1 degrees of the
# bone's +x; the other 11 branch off: shoulders, fingers, weapons, effect points). So each joint's frame is turned
# once, by this quarter turn about the bone's own y: the game's +x onto the axis that becomes the .glb's +y after the
# mirror (the game's z). Rows of a turn and move: frame -> frame x TURN. It only swaps and negates numbers, so it is
# exact, and the game's frame is always the file's turned back.
TURN = ((0.0, 0.0, 1.0, 0.0), (0.0, 1.0, 0.0, 0.0), (-1.0, 0.0, 0.0, 0.0))
LEG = {"calf": "thigh", "foot": "calf", "toe0": "foot"}   # a Biped leg, hip to toe (the game's crews' skeletons)


def _turned(m) -> list:
    """A rest pose (3 rows of 4) with its frame turned by TURN: its axes x, y, z become -z, y, x; its place kept."""
    return [[-row[2], row[1], row[0], row[3]] for row in m]


def _turned_back(m) -> list:
    """TURN's inverse times a move (3 rows of 4): its rows x, y, z become -z, y, x."""
    return [[-v for v in m[2]], list(m[1]), list(m[0])]


def _hung_from(names: list, b: int, at: dict) -> int | None:
    """The joint a bone the game gives no parent hangs from in the file (Blender sizes a bone by the bones hanging
    from it, and one hanging from nothing by its distance from the model's origin: a soldier's thigh came out 1.7 m
    long): a Biped leg's next bone up (calf from thigh, foot from calf, toe from foot), its thigh from the skeleton's
    first bone, as anything else is (bone 0: a soldier's bip01, a gun's or plane's first part)."""
    name = names[b].lower()
    side, _, part = name.rpartition(" ")
    if side and part in LEG:
        above = next((k for k, n in enumerate(names) if n.lower() == f"{side} {LEG[part]}"), None)
        if above in at:
            return above
    return 0 if 0 in at and b != 0 else None


def rest_poses(record: bytes, joints: list[int]) -> dict | None:
    """Where model_glb's `joints` (skeleton bone numbers, in the skin's order) stand at rest, from the model's skeleton
    record (rusemod.baf.skeleton), laid out so Blender shows a skeleton a modder can use: {"parents": each joint's
    parent joint (its position in `joints`; None: it hangs from the skeleton node), "trs": each joint's move, turn and
    size from that parent, "ibm": each joint's inverse bind matrix (glTF's column-major 4 x 4), "plain_turns": the
    names of the joints written as a plain turn, "hung": {joint: the joint it hangs from} for those the game gives no
    parent}, in the export's axes and scale (the mirror and 0.01), through rusemod.animglb's _trs and _ibm (RUSE Decoy's
    preview's). Every joint stands at the record's place for it. Its frame is the record's turned by TURN (so its bone
    runs along the game's +x); a bone the game sizes or mirrors at rest (every bone of the P-47, a gun's effect points:
    none of a soldier's) is written as the plain turn nearest it, turned the same, its inverse bind matrix that turn's
    inverse: Blender keeps no size on a bone and would move the points on it otherwise. A joint whose parent bone isn't
    a joint hangs from its nearest forebear that is one; one the game gives no parent at all (a soldier's legs, a
    vehicle's wheels) hangs from the joint _hung_from picks. The points don't change either way. None when the record
    can't place them (a joint past its bones)."""
    from . import baf
    from .animglb import _ibm, _trs
    sk = baf.skeleton(record)
    nb, parent_of, names = sk["bones"], sk["parents"], sk["names"]
    if any(not 0 <= b < nb for b in joints):
        return None
    world = [_rows(m) for m in sk["world"]]
    plain = [_is_plain(w) for w in world]
    frame = [_turned(w if ok else _plain_turn(w)) for w, ok in zip(world, plain)]
    at = {b: k for k, b in enumerate(joints)}
    ups, hung = {}, {}
    for b in joints:
        up, steps = parent_of[b], 0
        while 0 <= up < nb and up not in at and steps < nb:     # its nearest forebear that is a joint
            up, steps = parent_of[up], steps + 1
        ups[b] = up if up in at else None
        if parent_of[b] < 0:
            ups[b] = _hung_from(names, b, at)
            if ups[b] is not None:
                hung[b] = ups[b]
    for b in list(hung):            # never a loop: one that would hang from a bone hanging from it hangs from nothing
        seen, up = {b}, ups[b]
        while up is not None and up not in seen:
            seen.add(up)
            up = ups[up]
        if up is not None:
            ups[b] = None
            del hung[b]
    out = {"parents": [], "trs": [], "ibm": [], "plain_turns": [],
           "hung": {names[b]: names[up] for b, up in hung.items()}}
    for b in joints:
        up = ups[b]
        if plain[b] and up is None and parent_of[b] < 0:
            local = _flat(_turned(_rows(sk["local"][b])))      # the record's own rest pose, turned
        elif plain[b] and up is not None and up == parent_of[b] and plain[up]:
            local = _flat(_turned_back(_turned(_rows(sk["local"][b]))))   # from its turned parent: TURN^-1 L TURN
        else:
            local = _flat(_after(_undo(frame[up]), frame[b]) if up is not None else frame[b])
        out["parents"].append(at[up] if up is not None else None)
        out["trs"].append(_trs(local))
        out["ibm"].append(_ibm(_flat(_turned_back(_rows(sk["bind"][b]))) if plain[b] else _flat(_undo(frame[b]))))
        if not plain[b]:
            out["plain_turns"].append(names[b])
    return out


def model_glb(lib, name: str, side: int = 2048, rest_bones: bool = False) -> tuple[bytes, dict[str, bytes], dict]:
    """One model of `lib` (rusemod.models.Library) as (.glb bytes, {picture file name: PNG bytes}, summary).
    Textures come from their mip level at most `side` pixels wide. `rest_bones`: a model with bones has each bone at
    its rest pose (rest_poses, from lib.skeleton), not all at one spot; the summary's "rest_bones" says whether they
    were placed (False: no skeleton record found for it, written as by default), "plain_turns" which were written as a
    plain turn and "hung" which hang from another joint than the game's. Without it every byte is as it always was."""
    spk = lib.where[name]
    mats = spk.materials()
    parts = lib.parts(name)
    g = _Glb()
    pictures, summary = {}, {"model": name, "draw_calls": len(parts), "vertices": 0, "triangles": 0}
    stem = name.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", "").replace(".ase2ndfbin", "")

    # textures: colour into the .glb, colour and alpha as pictures beside it
    texture_of: dict[str, int] = {}
    for _part, tex in parts:
        if tex is None or tex in texture_of:
            continue
        pic = lib.picture(tex, most=side)
        if pic is None:
            continue
        w, h, rgba = pic
        colour, grey = _split(rgba)
        tname = tex.rsplit("\\", 1)[-1].rsplit(".", 1)[0]
        cpng = png_bytes(colour, w, h)
        pictures[f"{stem}_{tname}_colour.png"] = cpng
        pictures[f"{stem}_{tname}_alpha.png"] = png_bytes(grey, w, h)
        member = texture_member(tex)
        summary.setdefault("picture_of", {}).update({f"{stem}_{tname}_colour.png": (member, "colour"),
                                                     f"{stem}_{tname}_alpha.png": (member, "alpha")})
        texture_of[tex] = g.image(cpng, tname)
        g.doc["materials"].append({"name": tname, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": texture_of[tex]}, "metallicFactor": 0.0, "roughnessFactor": 0.8},
            "doubleSided": True, "extras": {"rusemod_texture": member}})
        texture_of[tex] = len(g.doc["materials"]) - 1

    # bones: every skeleton bone a vertex leans on
    def skeleton_bone(part, local: int) -> int:
        remap = mats[part.material].get("skinning") if part.material < len(mats) else None
        return remap[local] if remap and local < len(remap) else local

    used = {0}
    for part, _tex in parts:
        for b, w in zip(part.bones, part.weights):
            used.update(skeleton_bone(part, i) for i, x in zip(b, w) if x)
    joints = sorted(used)
    joint_of = {b: i for i, b in enumerate(joints)}
    skinned = any(part.bones for part, _t in parts)

    primitives, propellers = [], []
    for d, (part, tex) in enumerate(parts):
        n = len(part.positions) // 3
        pos = [_point(*part.positions[3 * i:3 * i + 3]) for i in range(n)]
        attrs = {"POSITION": g.accessor(pos, "VEC3", FLOAT, minmax=True)}
        if part.normals:
            nrm = []
            for i in range(n):
                x, y, z = _point(*part.normals[3 * i:3 * i + 3], scale=1.0)
                length = math.sqrt(x * x + y * y + z * z) or 1.0
                nrm.append((x / length, y / length, z / length))
            attrs["NORMAL"] = g.accessor(nrm, "VEC3", FLOAT)
        if part.uvs:
            attrs["TEXCOORD_0"] = g.accessor([(part.uvs[2 * i], part.uvs[2 * i + 1]) for i in range(n)], "VEC2", FLOAT)
        if skinned:
            js, ws = [], []
            for i in range(n):
                b = part.bones[i] if i < len(part.bones) else [0, 0, 0, 0]
                w = part.weights[i] if i < len(part.weights) else [255, 0, 0, 0]
                total = sum(w) or 0
                if total == 0:
                    js.append((joint_of[0], 0, 0, 0))
                    ws.append((1.0, 0.0, 0.0, 0.0))
                    continue
                js.append(tuple(joint_of[skeleton_bone(part, x)] if wx else 0 for x, wx in zip(b, w)))
                ws.append(tuple(wx / total for wx in w))
            attrs["JOINTS_0"] = g.accessor(js, "VEC4", USHORT)
            attrs["WEIGHTS_0"] = g.accessor(ws, "VEC4", FLOAT)
        if part.tracks:      # a tank's track numbers, read back by modelin (a custom attribute; 3D tools leave it alone)
            attrs[TRACK_ATTRIBUTE] = g.accessor([(t, 0, 0, 0) for t in part.tracks], "VEC4", UBYTE)
        tri = list(part.indices)
        if MIRROR:
            for k in range(0, len(tri) - 2, 3):
                tri[k + 1], tri[k + 2] = tri[k + 2], tri[k + 1]
        prim = {"attributes": attrs, "indices": g.accessor(tri, "SCALAR", UINT if n > 65535 else USHORT, 34963),
                "extras": {"rusemod_draw": d, "rusemod_material": part.material,
                           "rusemod_material_name": mats[part.material]["name"] if part.material < len(mats) else "",
                           "rusemod_texture": tex or "", **({"rusemod_static": True} if not part.bones else {})}}
        if tex in texture_of:
            prim["material"] = texture_of[tex]
        kind = mats[part.material].get("type", "") if part.material < len(mats) else ""
        (propellers if kind.startswith(PROPELLER) else primitives).append(prim)
        summary["vertices"] += n
        summary["triangles"] += len(tri) // 3

    mesh_nodes = []
    for mesh_name, prims in ((stem, primitives), (f"{stem}_propeller", propellers)):
        if prims:
            g.doc["meshes"].append({"name": mesh_name, "primitives": prims})
            mesh_nodes.append({"name": mesh_name, "mesh": len(g.doc["meshes"]) - 1})
    g.doc["nodes"] += mesh_nodes
    roots = list(range(len(mesh_nodes)))
    summary["propellers"] = len(propellers)
    if skinned:
        first = len(g.doc["nodes"])
        # each bone named as the game names it (tourelle_01, canon_01...), so a model brought back into the Studio
        # knows its turret (modelin.by_bones); bone_<number> where its skeleton isn't found
        bones = lib.bone_names(name) if hasattr(lib, "bone_names") else None
        g.doc["nodes"] += [{"name": bones[b] if bones and b < len(bones) and bones[b] else f"bone_{b}"}
                           for b in joints]
        rig = len(g.doc["nodes"])
        rest = None
        if rest_bones:
            record = lib.skeleton(name) if hasattr(lib, "skeleton") else None
            rest = rest_poses(record, joints) if record is not None else None
            summary["rest_bones"] = rest is not None
        if rest is None:
            g.doc["nodes"].append({"name": f"{stem}_bones", "children": list(range(first, first + len(joints)))})
            identity = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]
            ibm = g.view(struct.pack(f"<{16 * len(joints)}f", *(identity * len(joints))))
        else:
            for k, (t, r, s) in enumerate(rest["trs"]):
                g.doc["nodes"][first + k].update({"translation": t, "rotation": r, "scale": s})
            for k, p in enumerate(rest["parents"]):
                if p is not None:
                    g.doc["nodes"][first + p].setdefault("children", []).append(first + k)
            g.doc["nodes"].append({"name": f"{stem}_bones",
                                   "children": [first + k for k, p in enumerate(rest["parents"]) if p is None]})
            ibm = g.view(struct.pack(f"<{16 * len(joints)}f", *(v for m in rest["ibm"] for v in m)))
            summary["plain_turns"], summary["hung"] = rest["plain_turns"], rest["hung"]
        g.doc["accessors"].append({"bufferView": ibm, "componentType": FLOAT, "count": len(joints), "type": "MAT4"})
        g.doc["skins"] = [{"name": f"{stem}_skin", "joints": list(range(first, first + len(joints))),
                           "inverseBindMatrices": len(g.doc["accessors"]) - 1, "skeleton": rig}]
        for node in mesh_nodes:
            node["skin"] = 0
        roots.append(rig)
        summary["bones"] = joints
    g.doc["scenes"] = [{"name": stem, "nodes": roots}]
    g.doc["scene"] = 0
    g.doc["asset"]["extras"] = {"rusemod_model": name, "rusemod_scale": SCALE, "rusemod_mirror": MIRROR}
    return g.to_bytes(), pictures, summary


def export(lib, names: list[str], out: Path, side: int = 2048, rest_bones: bool = False) -> list[dict]:
    """Write each model of `names` as <out>/<model>.glb with its pictures; returns each one's summary. `rest_bones`:
    model_glb's."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    done = []
    for name in names:
        glb, pictures, summary = model_glb(lib, name, side, rest_bones=rest_bones)
        stem = name.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", "").replace(".ase2ndfbin", "")
        (out / f"{stem}.glb").write_bytes(glb)
        for fname, png in pictures.items():
            (out / fname).write_bytes(png)
        summary["file"] = str(out / f"{stem}.glb")
        summary["pictures"] = sorted(pictures)  # (summary["picture_of"]: each one's texture path and kind)
        done.append(summary)
    return done
