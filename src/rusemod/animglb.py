"""A game model on its real skeleton, playing one of the game's animation clips, as one .glb: what RUSE Decoy's 3D
preview plays (three.js's AnimationMixer) and what Blender opens.

Mesh, UVs, normals, textures, bone numbers and weights come the way rusemod.gltf exports a model (the same axes,
mirror and 0.01 scale). What this adds (DomesticNukes' way, 2026-10-05: soldiers and horses seen running in Blender):
  - the skeleton from the model's skeleton pack (laid out as a clip's skeleton part): one node per bone at its rest
    pose from its parent, the inverse bind matrices from the inverse rest poses;
  - the clip (rusemod.baf): each bone's keys found by name (a clip moves the bones it names), every move, size and turn
    through the export's mirror M (x, y, z -> x, z, y): A' = M A M, moves x 0.01.

A unit's animations for changing in Blender (add_animations, own_glb; the Studio's Change it in Blender, item 5 of the
owner's list, 2026-11-10: "fully editable in the studio") go on the bones as rusemod.gltf.rest_poses lays them out for
Blender: each bone's frame turned so it runs along the axis Blender draws a bone on, a bone the game gives no parent
(a soldier's legs) hung from the bone above it, a bone the game sizes as the plain turn nearest it. A bone's pose in
the model is then the game's times a fixed turn of its own (its "fix", W'(t) = W(t) x F, F = the bone's rest pose in
the game, inverted, times its rest pose in the file), so the points move exactly as the game moves them; each key of
the file is that pose from the bone's parent in the file. A bone under the same parent in both, turned the same, has
the clip's own keys, every number swapped and negated (exact); any other (a hung or sized one) has its pose worked out
at each of the clip's frames (30 a second). Blender draws a turn between two keys along a straight line through its
four numbers, not along the arc the game takes (the two part by up to 0.03 degrees for a key 30 degrees on): a key is
added wherever that line would miss a frame's turn by more than half a step of a clip's packing (rusemod.baf), so
Blender shows, and sends back, every frame as the game plays it. rusemod.rig.turn_back undoes all of it on the way back.
"""
from __future__ import annotations

import base64
import math
import struct

from . import baf, gltf
from .gltf import FLOAT, UINT, USHORT, _Glb, _point, _split, png_bytes, texture_member
from .unitpacks import NONE, MeshPack


class AnimGlbError(ValueError):
    pass


def _q_to_m(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def _m_to_q(r):
    tr = r[0][0] + r[1][1] + r[2][2]
    if tr > 0:
        k = math.sqrt(tr + 1.0) * 2
        q = ((r[2][1] - r[1][2]) / k, (r[0][2] - r[2][0]) / k, (r[1][0] - r[0][1]) / k, 0.25 * k)
    elif r[0][0] > r[1][1] and r[0][0] > r[2][2]:
        k = math.sqrt(1.0 + r[0][0] - r[1][1] - r[2][2]) * 2
        q = (0.25 * k, (r[0][1] + r[1][0]) / k, (r[0][2] + r[2][0]) / k, (r[2][1] - r[1][2]) / k)
    elif r[1][1] > r[2][2]:
        k = math.sqrt(1.0 + r[1][1] - r[0][0] - r[2][2]) * 2
        q = ((r[0][1] + r[1][0]) / k, 0.25 * k, (r[1][2] + r[2][1]) / k, (r[0][2] - r[2][0]) / k)
    else:
        k = math.sqrt(1.0 + r[2][2] - r[0][0] - r[1][1]) * 2
        q = ((r[0][2] + r[2][0]) / k, (r[1][2] + r[2][1]) / k, 0.25 * k, (r[1][0] - r[0][1]) / k)
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    return tuple(c / n for c in q)


_P = (0, 2, 1)   # the mirror: game axis _P[i] -> glTF axis i


def _mirror3(r):
    return [[r[_P[i]][_P[j]] for j in range(3)] for i in range(3)]


def _mirror_q(q):
    return _m_to_q(_mirror3(_q_to_m(q)))


def _rows(m):
    return [list(m[0:4]), list(m[4:8]), list(m[8:12])]


def _trs(m):
    """A 3x4 (the game's) -> glTF move, turn, size after the mirror."""
    m = _rows(m)
    r = _mirror3([row[:3] for row in m])
    t = _point(m[0][3], m[1][3], m[2][3])
    s = [math.sqrt(sum(r[i][j] ** 2 for i in range(3))) or 1.0 for j in range(3)]
    rot = [[r[i][j] / s[j] for j in range(3)] for i in range(3)]
    return list(t), list(_m_to_q(rot)), s


def _ibm(m):
    """A 3x4 (the game's, model -> bone) -> glTF column-major 4x4 after the mirror."""
    m = _rows(m)
    r = _mirror3([row[:3] for row in m])
    t = _point(m[0][3], m[1][3], m[2][3])
    return [r[0][0], r[1][0], r[2][0], 0.0, r[0][1], r[1][1], r[2][1], 0.0,
            r[0][2], r[1][2], r[2][2], 0.0, t[0], t[1], t[2], 1.0]


def model_skeleton(lib, model: str) -> dict | None:
    """A model's skeleton (rusemod.baf.skeleton's layout) from the game's skeleton packs, or None (no bones)."""
    for e in lib.arc.entries:
        p = e.path.lower()
        if not (p.startswith("gen_5\\pack\\") and p.endswith(".spk")):
            continue
        raw = bytes(lib.arc.read(e))
        if raw[:8] != b"MESHPCPC":
            continue
        try:
            pack = MeshPack.read(raw)
        except ValueError:
            continue
        item = pack.items.get(model)
        if item is not None and item[2] != NONE:
            return baf.skeleton(pack.skeletons[item[2]])
    return None


def glb(lib, model: str, clip: baf.Clip, side: int = 1024) -> tuple[bytes, dict]:
    """(the .glb, {"bones", "matched", "clip_bones", "seconds"}) for `model` (a name rusemod.models.Library knows)
    playing `clip`. A clip made for another skeleton moves only the bones whose names it shares."""
    sk = model_skeleton(lib, model)
    if sk is None:
        raise AnimGlbError(f"{model} has no skeleton: it can't play a clip")
    nb = sk["bones"]
    spk = lib.where[model]
    mats = spk.materials()
    parts = lib.parts(model)
    g = _Glb()
    stem = model.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", "").replace(".ase2ndfbin", "")

    texture_of = {}
    for _part, tex in parts:
        if tex is None or tex in texture_of:
            continue
        pic = lib.picture(tex, most=side)
        if pic is None:
            continue
        w, h, rgba = pic
        colour, _grey = _split(rgba)
        tname = tex.rsplit("\\", 1)[-1].rsplit(".", 1)[0]
        idx = g.image(png_bytes(colour, w, h), tname)
        g.doc["materials"].append({"name": tname, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": idx}, "metallicFactor": 0.0, "roughnessFactor": 0.8},
            "doubleSided": True, "extras": {"rusemod_texture": texture_member(tex)}})
        texture_of[tex] = len(g.doc["materials"]) - 1

    def skeleton_bone(part, local):
        remap = mats[part.material].get("skinning") if part.material < len(mats) else None
        return remap[local] if remap and local < len(remap) else local

    prims = []
    for part, tex in parts:
        n = len(part.positions) // 3
        attrs = {"POSITION": g.accessor([_point(*part.positions[3 * i:3 * i + 3]) for i in range(n)], "VEC3", FLOAT,
                                        minmax=True)}
        if part.normals:
            nrm = []
            for i in range(n):
                x, y, z = _point(*part.normals[3 * i:3 * i + 3], scale=1.0)
                L = math.sqrt(x * x + y * y + z * z) or 1.0
                nrm.append((x / L, y / L, z / L))
            attrs["NORMAL"] = g.accessor(nrm, "VEC3", FLOAT)
        if part.uvs:
            attrs["TEXCOORD_0"] = g.accessor([(part.uvs[2 * i], part.uvs[2 * i + 1]) for i in range(n)], "VEC2", FLOAT)
        js, ws = [], []
        for i in range(n):
            b = part.bones[i] if i < len(part.bones) else [0, 0, 0, 0]
            w = part.weights[i] if i < len(part.weights) else [255, 0, 0, 0]
            tot = sum(w)
            if not tot:
                js.append((0, 0, 0, 0))
                ws.append((1.0, 0.0, 0.0, 0.0))
                continue
            js.append(tuple(min(nb - 1, skeleton_bone(part, x)) if wx else 0 for x, wx in zip(b, w)))
            ws.append(tuple(wx / tot for wx in w))
        attrs["JOINTS_0"] = g.accessor(js, "VEC4", USHORT)
        attrs["WEIGHTS_0"] = g.accessor(ws, "VEC4", FLOAT)
        tri = list(part.indices)
        for k in range(0, len(tri) - 2, 3):
            tri[k + 1], tri[k + 2] = tri[k + 2], tri[k + 1]
        prim = {"attributes": attrs, "indices": g.accessor(tri, "SCALAR", UINT if n > 65535 else USHORT, 34963)}
        if tex in texture_of:
            prim["material"] = texture_of[tex]
        prims.append(prim)
    g.doc["meshes"].append({"name": stem, "primitives": prims})

    # the skeleton: node 0 the mesh, node 1 + b bone b
    g.doc["nodes"].append({"name": stem, "mesh": 0, "skin": 0})
    first = 1
    for b in range(nb):
        t, r, s = _trs(sk["local"][b])
        g.doc["nodes"].append({"name": sk["names"][b], "translation": t, "rotation": r, "scale": s})
    for b, p in enumerate(sk["parents"]):
        if p >= 0:
            g.doc["nodes"][first + p].setdefault("children", []).append(first + b)
    rig = len(g.doc["nodes"])
    g.doc["nodes"].append({"name": f"{stem}_rig", "children": [first + b for b, p in enumerate(sk["parents"]) if p < 0]})
    ibm = []
    for b in range(nb):
        ibm += _ibm(sk["bind"][b])
    g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(ibm)}f", *ibm)), "componentType": FLOAT,
                               "count": nb, "type": "MAT4"})
    g.doc["skins"] = [{"name": f"{stem}_skin", "joints": list(range(first, first + nb)),
                       "inverseBindMatrices": len(g.doc["accessors"]) - 1, "skeleton": rig}]
    g.doc["scenes"] = [{"name": stem, "nodes": [0, rig]}]
    g.doc["scene"] = 0

    # the clip, bone by bone by name
    csk = baf.skeleton(clip.skeleton)
    dur = clip.duration if clip.frames > 1 and clip.duration > 0 else 1 / 30
    by_name = {n.lower(): i for i, n in enumerate(sk["names"])}
    samplers, channels, matched = [], [], 0
    for u, track in enumerate(clip.tracks):
        b = by_name.get(csk["names"][csk["index"][u]].lower())
        if b is None:
            continue
        matched += 1
        for path, keys in (("translation", track.T), ("scale", track.S), ("rotation", track.R)):
            ts = [0.0, dur] if len(keys) <= 2 else [k[0] / baf.LAST_TIME * dur for k in keys]
            if path == "translation":
                vals = [_point(*k[1:4]) for k in keys]
            elif path == "scale":
                vals = [(k[1], k[3], k[2]) for k in keys]
            else:
                vals = [_mirror_q(baf.unpack_quat(k[1:5])) for k in keys]
                for k in range(1, len(vals)):   # neighbours on the same side: no flips through 360 degrees
                    if sum(x * y for x, y in zip(vals[k], vals[k - 1])) < 0:
                        vals[k] = tuple(-x for x in vals[k])
            if len(keys) == 1:
                vals = vals * 2
            tin = g.accessor(ts, "SCALAR", FLOAT, target=None)
            g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(ts)], [max(ts)]
            tout = g.accessor([tuple(v) for v in vals], "VEC4" if path == "rotation" else "VEC3", FLOAT, target=None)
            samplers.append({"input": tin, "output": tout, "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": first + b, "path": path}})
    g.doc["animations"] = [{"name": "clip", "samplers": samplers, "channels": channels}]
    return g.to_bytes(), {"bones": nb, "matched": matched, "clip_bones": clip.bones, "seconds": round(dur, 3)}


# --- a unit's animations on the bones rusemod.gltf.rest_poses lays out for Blender (the module's notes) ---
TOL_TURN = baf.SCALE / 2   # a turn's four numbers: half a step of a clip's packing (rusemod.baf)
TOL_MOVE = 1e-4            # a move, in the game's units (a soldier is about 312 tall)
TOL_SIZE = 1e-6            # a size
_TURN_Q = (0.0, math.sqrt(0.5), 0.0, math.sqrt(0.5))   # rusemod.gltf.TURN as a turn: a quarter turn about y


def animation_name(clip: str) -> str:
    """A clip's file name without folder, ending and lod0 (genanim_15\\...\\fusilier_standlod0.baf ->
    fusilier_stand)."""
    stem = clip.replace("/", "\\").rsplit("\\", 1)[-1].rsplit(".", 1)[0]
    return stem[:-4] if stem.lower().endswith("lod0") else stem


def runs_along_x(record: bytes) -> bool:
    """Whether a skeleton's bones run along their own +x, the game's way (every skeleton of the game's units: the US
    rifleman's 19 of 30 bone-to-child steps within 7 degrees of it), rather than along +z (a skeleton made in Blender,
    whose bones run along their +y there, through the export's mirror): each step from a bone to a child votes for
    the axis it runs along. No vote either way: the game's."""
    sk = baf.skeleton(record)
    votes = [0, 0]
    for c, p in enumerate(sk["parents"]):
        if p < 0:
            continue
        t = (sk["local"][c][3], sk["local"][c][7], sk["local"][c][11])
        n = math.sqrt(sum(v * v for v in t))
        if n < 1e-6:
            continue
        if t[0] / n > 0.9:
            votes[0] += 1
        elif t[2] / n > 0.9:
            votes[1] += 1
    return votes[0] >= votes[1]


def _nlerp(a, b, s):
    q = tuple(x + (y - x) * s for x, y in zip(a, b))
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    return tuple(c / n for c in q)


def _apart(q, r) -> float:
    """How far apart two turns' numbers are, the nearer of r and -r (one turn)."""
    if sum(x * y for x, y in zip(q, r)) < 0:
        r = tuple(-c for c in r)
    return max(abs(x - y) for x, y in zip(q, r))


def blender_keys(values: list, path: str) -> list[int]:
    """The frames of one channel (`values`: one a frame; a turn's on one side, each next one's numbers nearer the one
    before than its negative) to key, so that Blender, drawing straight lines between keys (a turn's four numbers each
    on a line, then made length one), gives every frame back within the module's tolerances: the first frame and the
    last always (they give the animation its length), and from each kept frame the farthest it reaches."""
    n = len(values)
    if n <= 2:
        return list(range(n))
    if path == "rotation":
        def near(a, e, m):
            return _apart(_nlerp(values[a], values[e], (m - a) / (e - a)), values[m]) <= TOL_TURN
    else:
        tol = TOL_MOVE if path == "translation" else TOL_SIZE

        def near(a, e, m):
            s = (m - a) / (e - a)
            return all(abs(x + (y - x) * s - v) <= tol for x, y, v in zip(values[a], values[e], values[m]))
    keep, a = [0], 0
    while a < n - 1:
        e = a + 1
        while e + 1 < n and all(near(a, e + 1, m) for m in range(e, a, -1)):
            e += 1
        keep.append(e)
        a = e
    return keep


def _keyed(sk: dict, rest: dict, b: int) -> bool:
    """Whether bone b's pose in the file is the clip's own, each number swapped and negated (the module's notes):
    written as the record has it, and from the same parent in both (or from none in both), that one too."""
    p, up = sk["parents"][b], rest["parents"][b]
    if not rest["plain"][b]:
        return False
    if p < 0:
        return up is None
    return up == p and rest["plain"][p]


def _file_trs(move, turn, size, root: bool, turned: bool) -> tuple:
    """A keyed bone's pose from its parent (the game's: move, turn (x, y, z, w), size) as the file has it: its frame
    and its parent's turned by gltf.TURN, T^-1 L T (a root: L T); not turned: as it is."""
    if not turned:
        return tuple(move), tuple(turn), tuple(size)
    size = (size[2], size[1], size[0])
    if root:
        return tuple(move), baf.qmul(turn, _TURN_Q), size
    x, y, z, w = turn
    return (-move[2], move[1], move[0]), (-z, y, x, w), size


def add_animations(g: _Glb, record: bytes, nodes, rest: dict, clips: list, turned: bool = True) -> list[dict]:
    """Each clip of `clips` ([(the animation's name, a rusemod.baf.Clip, its extras)]) as an animation of `g`, on the
    bones of the skeleton `record` laid out as `rest` (rusemod.gltf.rest_poses of every bone, `turned` as it was given)
    places them: `nodes`, bone b's node (a list), or the first bone's when they follow each other (an int). A clip
    moves the bones it names (a bone it hasn't got keeps its rest pose); its keys are worked out at each of its frames
    and kept where Blender needs them (blender_keys), each a channel LINEAR at the clip's times (a frame k of a clip
    of n frames at k x its length / (n - 1); one frame: one key). The animation's extras are `extras` with
    rusemod_seconds and rusemod_frames. Returns each one's {"name", "seconds", "frames", "bones" (the clip's),
    "matched", "missing" (its bones the model hasn't got), "keys", "slant" (the farthest a pose worked out isn't a
    move, turn and size: 0 for none)}."""
    from .rig import compose, decompose, inverse, move_out, mul, size_out, turn_out
    sk = baf.skeleton(record)
    nb = sk["bones"]
    nodes = [nodes + b for b in range(nb)] if isinstance(nodes, int) else list(nodes)
    by_name = {n.lower(): b for b, n in enumerate(sk["names"])}
    keyed = [_keyed(sk, rest, b) for b in range(nb)]
    worked = [b for b in range(nb) if not keyed[b]]
    fix = [mul(inverse(sk["world"][b]), rest["frames"][b]) for b in range(nb)]   # W'(t) = W(t) x fix
    rest_local = [decompose(sk["local"][b])[:3] for b in range(nb)]
    out = []
    for name, clip, extras in clips:
        csk = baf.skeleton(clip.skeleton)
        track_of, missing = {}, []
        for u in range(clip.bones):
            bone = csk["names"][csk["index"][u]]
            b = by_name.get(bone.lower())
            if b is None:
                missing.append(bone)
            else:
                track_of[b] = clip.tracks[u]
        frames = max(1, clip.frames)
        dur = clip.duration
        step = 1.0 / baf.FPS if frames > 1 and abs(dur - (frames - 1) / baf.FPS) < 1e-6 else \
            (dur / (frames - 1) if frames > 1 else 0.0)
        values = [[[], [], []] for _ in range(nb)]     # each bone's moves, turns, sizes in the file, a frame each
        slant = 0.0
        for k in range(frames):
            frac = k / (frames - 1) if frames > 1 else 0.0
            local = [baf.sample(track_of[b], frac) if b in track_of else rest_local[b] for b in range(nb)]
            if worked:      # (poses in the model: only for a bone whose pose is worked out)
                world = [None] * nb
                for b in range(nb):         # (parents come first in every record)
                    m = compose(local[b][0], local[b][1], local[b][2])
                    world[b] = m if sk["parents"][b] < 0 else mul(world[sk["parents"][b]], m)
                filed = [mul(world[b], fix[b]) for b in range(nb)]
            for b in range(nb):
                if keyed[b]:
                    move, turn, size = _file_trs(local[b][0], local[b][1], local[b][2], sk["parents"][b] < 0, turned)
                else:
                    up = rest["parents"][b]
                    m = filed[b] if up is None else mul(inverse(filed[up]), filed[b])
                    move, turn, size, off = decompose(m)
                    slant = max(slant, off)
                values[b][0].append(tuple(move))
                values[b][1].append(tuple(turn))
                values[b][2].append(tuple(size))
        samplers, channels, keys = [], [], 0
        for b in sorted(set(track_of) | set(worked)):     # (a bone the clip doesn't move, keyed: its rest pose holds)
            moves, turns, sizes = values[b]
            turns = baf.same_side(turns)
            for path, vals, out_of in (("translation", moves, move_out), ("rotation", turns, turn_out),
                                       ("scale", sizes, size_out)):
                kept = blender_keys(vals, path) if frames > 1 else [0]
                times = [k * step for k in kept]
                tin = g.accessor(times, "SCALAR", FLOAT, target=None)
                g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(times)], [max(times)]
                tout = g.accessor([tuple(out_of(vals[k])) for k in kept], "VEC4" if path == "rotation" else "VEC3",
                                  FLOAT, target=None)
                samplers.append({"input": tin, "output": tout, "interpolation": "LINEAR"})
                channels.append({"sampler": len(samplers) - 1, "target": {"node": nodes[b], "path": path}})
                keys += len(kept)
        seconds = (frames - 1) * step
        g.doc.setdefault("animations", []).append({
            "name": name, "samplers": samplers, "channels": channels,
            "extras": {**(extras or {}), "rusemod_seconds": clip.duration, "rusemod_frames": clip.frames}})
        out.append({"name": name, "seconds": round(seconds, 4), "frames": frames, "bones": clip.bones,
                    "matched": len(track_of), "missing": missing, "keys": keys, "slant": slant})
    return out


def own_glb(raw: bytes, clips: list, turned: bool | None = None) -> tuple[bytes, dict]:
    """A model on bones of its own as the mod keeps it (files/models/<unit>.glb, rusemod.modelin.write_glb's: its
    skeleton record in its skin's extras, every bone at its rest pose in the game's frames) laid out for Blender as
    rusemod.gltf.model_glb's `clips` lays out a game model: every bone on its rest pose as rest_poses places it,
    turned when its bones run along their +x as the game's do (runs_along_x; `turned` says it instead), with `clips`
    as its animations (add_animations). The points, pictures and record stay as they are. Returns (the .glb, {"bones",
    "turned", "hung", "plain_turns", "animations"})."""
    from .modelin import glb_document
    from .rig import SKELETON_EXTRA
    try:
        doc, binary = glb_document(raw)
    except (ValueError, struct.error) as exc:
        raise AnimGlbError(f"the model's file can't be read: {exc}") from None
    skin = next((s for s in doc.get("skins") or [] if (s.get("extras") or {}).get(SKELETON_EXTRA)), None)
    if skin is None:
        # not a game rule: only a model on bones of its own keeps its skeleton in its file
        raise AnimGlbError("the model's file has no skeleton of its own")
    record = base64.b64decode(skin["extras"][SKELETON_EXTRA])
    sk = baf.skeleton(record)
    nb, joints = sk["bones"], list(skin.get("joints") or [])
    if len(joints) != nb or [doc["nodes"][j].get("name", "").lower() for j in joints] != [n.lower() for n in sk["names"]]:
        # not a game rule: the file's bones aren't its record's (a file not written by the Studio)
        raise AnimGlbError("the model's bones aren't the ones its skeleton record names")
    turned = runs_along_x(record) if turned is None else bool(turned)
    rest = gltf.rest_poses(record, list(range(nb)), turn=turned)
    taken = set(joints)
    for node in doc["nodes"]:       # the bones' tree laid out again
        if "children" in node:
            node["children"] = [c for c in node["children"] if c not in taken]
            if not node["children"]:
                del node["children"]
    holder = skin.get("skeleton")
    if holder is None:
        holder = len(doc["nodes"])
        doc["nodes"].append({"name": "bones"})
        scene = (doc.get("scenes") or [{}])[doc.get("scene", 0)]
        scene.setdefault("nodes", []).append(holder)
        skin["skeleton"] = holder
    for b in range(nb):
        node = doc["nodes"][joints[b]]
        node.pop("matrix", None)
        t, r, s = rest["trs"][b]
        node.update(translation=list(t), rotation=list(r), scale=list(s))
        up = rest["parents"][b]
        doc["nodes"][joints[up] if up is not None else holder].setdefault("children", []).append(joints[b])
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    ibm = [v for m in rest["ibm"] for v in m]
    g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(ibm)}f", *ibm)), "componentType": FLOAT,
                               "count": nb, "type": "MAT4"})
    skin["inverseBindMatrices"] = len(g.doc["accessors"]) - 1
    doc.pop("animations", None)
    animations = add_animations(g, record, joints, rest, clips, turned)
    return g.to_bytes(), {"bones": nb, "turned": turned, "hung": rest["hung"], "plain_turns": rest["plain_turns"],
                          "animations": animations}
