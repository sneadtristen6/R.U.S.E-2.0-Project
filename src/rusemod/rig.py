"""A model's own skeleton and its animations, read from a glTF file (.glb, or .gltf with its files beside it) in the
game's axes and units: each bone's name, parent and rest pose, and every animation (Blender's actions) with its moves,
turns and sizes, played as glTF plays them (LINEAR, STEP and CUBICSPLINE). For a model whose bones are its own (a horse,
a horse and its rider, any creature): rusemod.unitmodel writes its skeleton record and its draws on those bones, and
turns each animation into a game clip through rusemod.baf.

The axes are rusemod.gltf's, undone: the export writes the game's (x, y, z) as glTF's (x, z, y) times SCALE, a mirror, so
a matrix A of the file is M A M in the game's axes (M: y and z swapped), a move is divided by SCALE, a turn (x, y, z, w)
becomes (-x, -z, -y, w) and a size (x, y, z) becomes (x, z, y) (rusemod.animglb does the same the other way). Every
matrix here is the game's 3 x 4, 12 numbers, rows of [r r r t], as a skeleton record keeps them.

A bone is a joint of a skin the file's meshes use; its parent is the nearest node above it that is a joint too, and a
node between them (Blender's armature object) counts towards its pose. Each bone has three rest matrices, as a record
has: `local` from its parent (the model for a root), `world` in the model, and `bind`, model to bone, the file's inverse
bind matrix (what its points were bound with). Bone names are kept in lower case, as every skeleton of the game has
them, and in the file's order with each parent before its children (all 633 different records of the game are so).

A file can carry the game's own record of its skeleton in its skin's extras (`rusemod_skeleton`, the record's bytes in
base64): it is kept, byte for byte, while the file's bones still match it (the same names and parents, every rest
matrix within float noise of it); a file whose bones were changed has its record worked out from them again, and the
notes say so."""
from __future__ import annotations

import base64
import bisect
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path

from . import baf
from .gltf import MIRROR, SCALE
from .modelin import ModelError, glb_accessor, glb_document, gltf_document

SKELETON_EXTRA = "rusemod_skeleton"   # a skin's extras: the game's record of its skeleton, base64
PATHS = ("translation", "rotation", "scale")
SNAP = 1e-3        # a key this close to a frame (in frames) is on it: a float's time from the file isn't exact
NEAR_TURN = 1e-4   # rest matrices the same within this (turn and size numbers) ...
NEAR_MOVE = 1e-2   # ... and this (moves, game units): float noise, a record kept
IDENTITY = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

# glTF's axis -> the game's: game[i] = _SIGN[i] * gltf[_AXIS[i]]; a turn's axis flips with a mirror (_DET -1)
_AXIS = (0, 2, 1)
_SIGN = (1.0, 1.0, 1.0) if MIRROR else (1.0, -1.0, 1.0)
_DET = -1.0 if MIRROR else 1.0


# --- the axes ---
def move_in(t) -> tuple:
    """A glTF move (metres, its axes) in the game's units and axes."""
    return tuple(_SIGN[i] * t[_AXIS[i]] / SCALE for i in range(3))


def move_out(g) -> tuple:
    out = [0.0, 0.0, 0.0]
    for i in range(3):
        out[_AXIS[i]] = _SIGN[i] * g[i] * SCALE
    return tuple(out)


def turn_in(q) -> tuple:
    """A glTF turn (x, y, z, w) in the game's axes."""
    return tuple(_DET * _SIGN[i] * q[_AXIS[i]] for i in range(3)) + (q[3],)


def turn_out(g) -> tuple:
    out = [0.0, 0.0, 0.0, g[3]]
    for i in range(3):
        out[_AXIS[i]] = _DET * _SIGN[i] * g[i]
    return tuple(out)


def size_in(s) -> tuple:
    return tuple(s[_AXIS[i]] for i in range(3))


def size_out(g) -> tuple:
    out = [0.0, 0.0, 0.0]
    for i in range(3):
        out[_AXIS[i]] = g[i]
    return tuple(out)


def matrix_in(m: list) -> tuple:
    """A glTF 4 x 4 matrix (16 numbers, column by column) in the game's axes: 12 numbers, rows of [r r r t]."""
    out = []
    for i in range(3):
        for j in range(3):
            out.append(_SIGN[i] * _SIGN[j] * m[_AXIS[j] * 4 + _AXIS[i]])
        out.append(_SIGN[i] * m[12 + _AXIS[i]] / SCALE)
    return tuple(out)


def matrix_out(g) -> list:
    """The game's 3 x 4 as a glTF 4 x 4 (16 numbers, column by column)."""
    m = [0.0] * 16
    m[15] = 1.0
    for i in range(3):
        for j in range(3):
            m[_AXIS[j] * 4 + _AXIS[i]] = _SIGN[i] * _SIGN[j] * g[i * 4 + j]
        m[12 + _AXIS[i]] = _SIGN[i] * g[i * 4 + 3] * SCALE
    return m


# --- 3 x 4 matrices (rows of [r r r t]) and turns (x, y, z, w) ---
def turn_matrix(q) -> list:
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def compose(move, turn, size) -> tuple:
    """move x turn x size, as one matrix."""
    r = turn_matrix(turn)
    return tuple(v for i in range(3) for v in (r[i][0] * size[0], r[i][1] * size[1], r[i][2] * size[2], move[i]))


def mul(a, b) -> tuple:
    """a x b (b first)."""
    out = []
    for i in range(3):
        for j in range(4):
            v = sum(a[i * 4 + k] * b[k * 4 + j] for k in range(3))
            out.append(v + a[i * 4 + 3] if j == 3 else v)
    return tuple(out)


def inverse(a) -> tuple:
    (r00, r01, r02, t0), (r10, r11, r12, t1), (r20, r21, r22, t2) = a[0:4], a[4:8], a[8:12]
    c = [[r11 * r22 - r12 * r21, r02 * r21 - r01 * r22, r01 * r12 - r02 * r11],
         [r12 * r20 - r10 * r22, r00 * r22 - r02 * r20, r02 * r10 - r00 * r12],
         [r10 * r21 - r11 * r20, r01 * r20 - r00 * r21, r00 * r11 - r01 * r10]]
    det = r00 * c[0][0] + r01 * c[1][0] + r02 * c[2][0]
    if abs(det) < 1e-30:
        raise ModelError("a bone whose rest pose squashes it flat (no inverse)")
    inv = [[c[i][j] / det for j in range(3)] for i in range(3)]
    t = (t0, t1, t2)
    return tuple(v for i in range(3) for v in (inv[i][0], inv[i][1], inv[i][2],
                                               -sum(inv[i][k] * t[k] for k in range(3))))


def turn_of(r) -> tuple:
    """A turn (x, y, z, w) from a 3 x 3 whose columns are of length one."""
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


def decompose(a) -> tuple:
    """(move, turn, size) of a 3 x 4, and how far it is from one (a slant the three can't hold: 0 for none)."""
    cols = [[a[i * 4 + j] for i in range(3)] for j in range(3)]
    size = [math.sqrt(sum(c * c for c in col)) or 1.0 for col in cols]
    det = (cols[0][0] * (cols[1][1] * cols[2][2] - cols[1][2] * cols[2][1])
           - cols[1][0] * (cols[0][1] * cols[2][2] - cols[0][2] * cols[2][1])
           + cols[2][0] * (cols[0][1] * cols[1][2] - cols[0][2] * cols[1][1]))
    if det < 0:
        size[0] = -size[0]
    r = [[cols[j][i] / size[j] for j in range(3)] for i in range(3)]
    turn = turn_of(r)
    move = (a[3], a[7], a[11])
    back = compose(move, turn, size)
    return move, turn, tuple(size), max(abs(x - y) for x, y in zip(back, a))


def near(a, b) -> float:
    """How far apart two 3 x 4s are, as a share of NEAR_TURN / NEAR_MOVE (1 or less: the same within float noise)."""
    turn = max(abs(a[k] - b[k]) for k in range(12) if k % 4 != 3)
    move = max(abs(a[k] - b[k]) for k in (3, 7, 11))
    return max(turn / NEAR_TURN, move / NEAR_MOVE)


# --- what is read ---
@dataclass
class Joint:
    name: str
    parent: int          # the parent bone's number, -1 for a root
    node: int            # its node in the file
    local: tuple         # its rest pose from its parent (from the model for a root)
    world: tuple         # its rest pose in the model
    bind: tuple          # model -> bone, as its points were bound


@dataclass
class Channel:
    node: int
    path: str            # "translation", "rotation" or "scale"
    times: list          # seconds
    values: list         # one a key in the game's axes and units; CUBICSPLINE: in-tangent, value, out-tangent a key
    interpolation: str   # "LINEAR", "STEP" or "CUBICSPLINE"


@dataclass
class Animation:
    name: str
    channels: list
    start: float         # its first key's time, seconds
    end: float           # its last key's

    @property
    def seconds(self) -> float:
        return self.end - self.start


@dataclass
class Rig:
    joints: list
    animations: list
    kept: bytes | None = None      # the game's record the file carries, while its bones still match it
    notes: list = field(default_factory=list)
    node_parent: list = field(default_factory=list, repr=False)   # each node's parent node (-1: none)
    node_rest: list = field(default_factory=list, repr=False)     # each node's rest: (move, turn, size), or a 3 x 4
    chains: list = field(default_factory=list, repr=False)        # each bone's nodes between its parent bone and it

    @property
    def names(self) -> list:
        return [j.name for j in self.joints]

    def record(self) -> bytes:
        """The skeleton's record, as the game keeps one (rusemod.baf.skeleton_bytes): the file's own when it carries
        one its bones still match, else worked out from its bones (track order depth by depth)."""
        if self.kept is not None:
            return self.kept
        return baf.skeleton_bytes(self.names, [j.parent for j in self.joints], [j.bind for j in self.joints],
                                  [j.local for j in self.joints], [j.world for j in self.joints])

    # --- an animation, frame by frame ---
    def frames(self, anim: Animation, fps: int = baf.FPS) -> tuple[float, int]:
        """(its length as a clip keeps it, its frames): `fps` frames a second from its first key to its last; one frame
        of 1 second for an animation that doesn't move in time (as the game's one-frame clip)."""
        if anim.seconds <= 1e-9:
            return 1.0, 1
        return anim.seconds, max(2, round(anim.seconds * fps) + 1)

    def poses(self, anim: Animation, fps: int = baf.FPS) -> tuple[float, list]:
        """(its length in seconds, each bone's (moves, turns, sizes) at each of its frames, in the game's axes and
        units, as rusemod.baf.from_frames takes them). Each bone's pose is from its parent bone: a node between them
        counts in (their matrices multiplied and taken apart again); a bone the animation doesn't move keeps its rest."""
        length, frames = self.frames(anim, fps)
        step = anim.seconds / (frames - 1) if frames > 1 else 0.0
        times = [anim.start + k * step for k in range(frames)]
        by_node: dict = {}
        for ch in anim.channels:
            snapped = []
            for t in ch.times:
                k = (t - anim.start) / step if step else 0.0
                snapped.append(anim.start + round(k) * step if step and abs(k - round(k)) <= SNAP else t)
            by_node.setdefault(ch.node, {})[ch.path] = (ch, snapped)

        def trs(node: int, k: int) -> tuple:
            rest = self.node_rest[node]
            got = by_node.get(node, {})
            if not isinstance(rest[0], tuple):      # a node with a matrix: never moved by an animation
                return rest
            out = []
            for path, value in zip(PATHS, rest):
                if path in got:
                    ch, snapped = got[path]
                    value = sample(ch, snapped, times[k])
                out.append(value)
            return tuple(out)

        poses, slant = [], []
        for j, joint in enumerate(self.joints):
            chain = self.chains[j]
            moved = any(n in by_node for n in chain)
            plain = not moved and all(_still(self.node_rest[n]) for n in chain)
            moves, turns, sizes = [], [], []
            for k in range(frames):
                part = trs(joint.node, k) if plain else None
                if part is not None and isinstance(part[0], tuple):
                    move, turn, size = part
                elif part is not None:      # (a bone given as a matrix: never moved, taken apart once a frame)
                    move, turn, size, _off = decompose(part)
                else:
                    m = IDENTITY
                    for n in chain + [joint.node]:
                        part = trs(n, k)
                        m = mul(m, compose(*part) if isinstance(part[0], tuple) else part)
                    move, turn, size, off = decompose(m)
                    if off > 1e-6 and joint.name not in slant:
                        slant.append(joint.name)
                moves.append(tuple(move))
                turns.append(tuple(turn))
                sizes.append(tuple(size))
            poses.append((moves, turns, sizes))
        if slant:
            self.notes.append(f"{anim.name}: {', '.join(slant[:6])} slanted by a node above, which a clip's move, turn "
                              "and size can't hold: kept as near as they go")
        return length, poses


def _still(rest) -> bool:
    """A node's rest that moves nothing."""
    if not isinstance(rest[0], tuple):
        return near(rest, IDENTITY) == 0.0
    move, turn, size = rest
    return (all(abs(c) < 1e-12 for c in move) and all(abs(c - 1.0) < 1e-12 for c in size)
            and abs(abs(turn[3]) - 1.0) < 1e-12)


def sample(ch: Channel, times: list, t: float):
    """A channel's value at time `t` (seconds), as glTF plays it: held before its first key and after its last; STEP
    holds each key; LINEAR goes straight between keys (turns along the shorter arc); CUBICSPLINE follows each key's
    tangents (a turn made length one after). `times`: the channel's key times (snapped to the frames)."""
    n = len(times)
    cubic = ch.interpolation == "CUBICSPLINE"

    def value(i):
        return ch.values[3 * i + 1] if cubic else ch.values[i]
    i = bisect.bisect_right(times, t) - 1
    if i < 0:
        return value(0)
    if i >= n - 1 or t == times[i]:
        return value(min(i, n - 1))
    t0, t1 = times[i], times[i + 1]
    s = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    if ch.interpolation == "STEP":
        return value(i)
    if cubic:
        d = t1 - t0
        p0, m0 = ch.values[3 * i + 1], ch.values[3 * i + 2]
        p1, m1 = ch.values[3 * (i + 1) + 1], ch.values[3 * (i + 1)]
        s2, s3 = s * s, s * s * s
        h00, h10, h01, h11 = 2 * s3 - 3 * s2 + 1, s3 - 2 * s2 + s, -2 * s3 + 3 * s2, s3 - s2
        v = tuple(h00 * a + h10 * d * b + h01 * c + h11 * d * e for a, b, c, e in zip(p0, m0, p1, m1))
        if ch.path == "rotation":
            norm = math.sqrt(sum(c * c for c in v)) or 1.0
            v = tuple(c / norm for c in v)
        return v
    a, b = value(i), value(i + 1)
    if ch.path == "rotation":
        return baf.slerp(a, b, s)
    return tuple(x + (y - x) * s for x, y in zip(a, b))


# --- reading ---
def read_rig(path) -> Rig:
    """A .glb's or .gltf's own skeleton and animations (rig_of)."""
    path = Path(path)
    try:
        if path.suffix.lower() == ".gltf":
            doc, binary = gltf_document(path)
        else:
            doc, binary = glb_document(path.read_bytes())
    except (OSError, ValueError, struct.error) as exc:
        raise ModelError(f"{path.name}: {exc}") from None
    return rig_of(doc, binary, path.name)


def _node_rest(node: dict):
    """A node's rest in the game's axes: (move, turn, size), or a 3 x 4 for a node given as a matrix."""
    if "matrix" in node:
        return matrix_in([float(v) for v in node["matrix"]])
    return (move_in([float(v) for v in node.get("translation", (0.0, 0.0, 0.0))]),
            turn_in([float(v) for v in node.get("rotation", (0.0, 0.0, 0.0, 1.0))]),
            size_in([float(v) for v in node.get("scale", (1.0, 1.0, 1.0))]))


def _rest_matrix(rest) -> tuple:
    return compose(*rest) if isinstance(rest[0], tuple) else rest


def rig_of(doc: dict, binary: bytes, label: str = "the file") -> Rig:
    """The skeleton and animations of a glTF document (rusemod.modelin.glb_document's or gltf_document's)."""
    nodes = doc.get("nodes", [])
    parent = [-1] * len(nodes)
    for n, node in enumerate(nodes):
        for c in node.get("children", []):
            parent[c] = n
    scenes = doc.get("scenes") or [{"nodes": [n for n in range(len(nodes)) if parent[n] < 0]}]
    seen, order = set(), []

    def walk(n: int) -> None:
        if n in seen:
            return
        seen.add(n)
        order.append(n)
        for c in nodes[n].get("children", []):
            walk(c)
    for n in scenes[doc.get("scene", 0)].get("nodes", []):
        walk(n)
    skins = []
    for n in order:
        if "mesh" in nodes[n] and "skin" in nodes[n] and nodes[n]["skin"] not in skins:
            skins.append(nodes[n]["skin"])
    if not skins:       # (bones and animations with no mesh on them: every skin the file has)
        skins = list(range(len(doc.get("skins") or [])))
    if not skins:
        # not a game rule: a model of its own bones needs them in the file
        raise ModelError(f"{label}: no bones in it (no mesh is skinned to an armature): in Blender, parent the mesh "
                         "to its armature with weights, then export it again")
    notes: list = []
    joints, bind_of = [], {}
    for s in skins:
        skin = doc["skins"][s]
        ibm = glb_accessor(doc, binary, skin["inverseBindMatrices"]) if "inverseBindMatrices" in skin else None
        if ibm is None:
            notes.append("its skin has no bind matrices: each taken as no move at all, as glTF says")
        for k, j in enumerate(skin.get("joints", [])):
            m = matrix_in([float(v) for v in ibm[k]]) if ibm is not None else IDENTITY
            if j in bind_of:
                if near(bind_of[j], m) > 1.0:
                    notes.append(f"{nodes[j].get('name', j)} is bound two ways in two skins: the first kept")
                continue
            bind_of[j] = m
            joints.append(j)
    is_joint = set(joints)
    names, lower = {}, {}
    for j in joints:
        name = nodes[j].get("name", "")
        if not name:
            # not a game rule: points lean on bones by name (rusemod.modelin.read_model)
            raise ModelError(f"{label}: a bone without a name (node {j}): name it in Blender")
        try:
            name.encode("latin-1")
        except UnicodeEncodeError:
            # not a game rule: the game's skeleton records keep names as single bytes
            raise ModelError(f"{label}: the bone name {name!r} has letters a skeleton can't hold: rename it with "
                             "plain letters in Blender") from None
        if name.lower() in lower:
            # not a game rule: points lean on bones by name, and the game's names are all different
            raise ModelError(f"{label}: two bones are called {name!r} (not counting capitals): rename one in Blender")
        lower[name.lower()] = j
        names[j] = name.lower()
    if any(n != nodes[j].get("name") for j, n in names.items()):
        notes.append("bone names kept in lower case, as every skeleton of the game has them")
    rest = [_node_rest(node) for node in nodes]
    world_of: dict = {}

    def world(n: int) -> tuple:
        if n not in world_of:
            m = _rest_matrix(rest[n])
            world_of[n] = m if parent[n] < 0 else mul(world(parent[n]), m)
        return world_of[n]

    up, chain_of = {}, {}
    for j in joints:
        chain, p = [], parent[j]
        while p >= 0 and p not in is_joint:
            chain.insert(0, p)
            p = parent[p]
        up[j], chain_of[j] = p, chain
    placed, ordered, pending = set(), [], list(joints)
    while pending:      # each parent before its children, the file's order kept otherwise
        later = []
        for j in pending:
            if up[j] < 0 or up[j] in placed:
                ordered.append(j)
                placed.add(j)
            else:
                later.append(j)
        if len(later) == len(pending):
            raise ModelError(f"{label}: its bones' parents go round in a loop")
        pending = later
    if ordered != joints:
        notes.append("bones put in the order the game keeps them: each parent before its children")
    number = {j: k for k, j in enumerate(ordered)}
    out, chains = [], []
    worst = 0.0
    for j in ordered:
        local = _rest_matrix(rest[j])
        for n in reversed(chain_of[j]):
            local = mul(_rest_matrix(rest[n]), local)
        w = world(j)
        out.append(Joint(names[j], number[up[j]] if up[j] >= 0 else -1, j, local, w, bind_of[j]))
        chains.append(chain_of[j])
        try:
            worst = max(worst, near(mul(bind_of[j], w), IDENTITY))
        except ModelError:
            worst = math.inf
    if worst > 1.0:
        notes.append("its points were bound to bones that weren't at their rest pose: they're drawn as they were bound")
    for n in order:
        if "mesh" in nodes[n] and "skin" in nodes[n] and near(world(n), IDENTITY) > 1.0:
            notes.append(f"the mesh {nodes[n].get('name', n)} sits on a node that moves it: in Blender, apply its "
                         "transforms (Ctrl+A) before exporting, or it won't be where the game draws it")
    animations = []
    on_bones = set(ordered) | {n for c in chains for n in c}
    for a, anim in enumerate(doc.get("animations", [])):
        name = anim.get("name") or f"animation {a + 1}"
        channels, left = [], set()
        for c in anim.get("channels", []):
            target = c.get("target", {})
            node, path = target.get("node"), target.get("path")
            if path == "weights":
                left.add("shape keys")
                continue
            if node is None or path not in PATHS:
                continue
            if node not in on_bones:
                left.add(nodes[node].get("name") or f"node {node}")
                continue
            sampler = anim["samplers"][c["sampler"]]
            how = sampler.get("interpolation", "LINEAR")
            times = [float(t) for t in glb_accessor(doc, binary, sampler["input"])]
            raw = glb_accessor(doc, binary, sampler["output"])
            conv = {"translation": move_in, "rotation": turn_in, "scale": size_in}[path]
            values = [conv([float(v) for v in x]) for x in raw]
            if not times or how not in ("LINEAR", "STEP", "CUBICSPLINE") \
                    or len(values) != len(times) * (3 if how == "CUBICSPLINE" else 1) or times != sorted(times):
                notes.append(f"{name}: a {path} channel laid out as glTF doesn't say: left out")
                continue
            channels.append(Channel(node, path, times, values, how))
        if left:
            notes.append(f"{name}: what moves things that aren't bones is left out ({', '.join(sorted(left)[:6])})")
        if not channels:
            notes.append(f"{name}: moves no bone: left out")
            continue
        animations.append(Animation(name, channels, min(c.times[0] for c in channels if c.times),
                                    max(c.times[-1] for c in channels if c.times)))
    rig = Rig(out, animations, None, notes, parent, rest, chains)
    for s in skins:
        given = (doc["skins"][s].get("extras") or {}).get(SKELETON_EXTRA)
        if given:
            rig.kept = _kept_record(given, rig)
            if rig.kept is None:
                notes.append("its bones were changed since its skeleton was written: worked out again from them")
            break
    return rig


def _kept_record(given, rig: Rig) -> bytes | None:
    """The record a skin's extras carry, when the file's bones still match it (names, parents, every rest matrix
    within float noise); else None."""
    try:
        record = base64.b64decode(given, validate=True)
        sk = baf.skeleton(record)
        if baf.skeleton_bytes(sk["names"], sk["parents"], sk["bind"], sk["local"], sk["world"], sk["index"]) != record:
            return None
    except (ValueError, TypeError, struct.error, UnicodeDecodeError, baf.ClipError):
        return None
    if sk["names"] != rig.names or sk["parents"] != [j.parent for j in rig.joints]:
        return None
    for b, j in enumerate(rig.joints):
        if max(near(sk["bind"][b], j.bind), near(sk["local"][b], j.local), near(sk["world"][b], j.world)) > 1.0:
            return None
    return record


def skeleton_extra(record: bytes) -> str:
    """A record as a skin's extras carry it (SKELETON_EXTRA)."""
    return base64.b64encode(record).decode("ascii")
