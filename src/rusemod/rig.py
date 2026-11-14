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
notes say so. A file back from the model's own Blender also carries, in each animation's extras, the clip that went out
under its name (CLIP_OUT): kept_clip keeps an animation that came back as it went out byte for byte (item 45)."""
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
    meshes: list = field(default_factory=list, repr=False)        # the nodes of its meshes on bones (a skin's)

    @property
    def names(self) -> list:
        return [j.name for j in self.joints]

    def node_world(self, n: int) -> tuple:
        """A node's rest in the model, every node above it counted in (as a bone's `world` is)."""
        m = IDENTITY
        while n >= 0:
            m = mul(_rest_matrix(self.node_rest[n]), m)
            n = self.node_parent[n]
        return m

    def record(self) -> bytes:
        """The skeleton's record, as the game keeps one (rusemod.baf.skeleton_bytes): the file's own when it carries
        one its bones still match, else worked out from its bones (track order depth by depth)."""
        if self.kept is not None:
            return self.kept
        return baf.skeleton_bytes(self.names, [j.parent for j in self.joints], [j.bind for j in self.joints],
                                  [j.local for j in self.joints], [j.world for j in self.joints])

    # --- an animation, frame by frame ---
    def frames(self, anim: Animation, fps: int = baf.FPS, rate: float | None = None) -> tuple[float, int]:
        """(its length as a clip keeps it, its frames): `fps` frames a second from its first key to its last; one frame
        of 1 second for an animation that doesn't move in time (as the game's one-frame clip). `rate`: the frames a
        second the file was sampled at when that isn't `fps` (Blender's scene set to another rate: sampled_rate):
        each of the file's frames is one of the clip's, `fps` a second, so every pose sent is a frame of the clip as
        it was sent (the clip runs at the game's speed, not the file's)."""
        if anim.seconds <= 1e-9:
            return 1.0, 1
        if rate:
            frames = max(2, round(anim.seconds * rate) + 1)
            return (frames - 1) / fps, frames
        return anim.seconds, max(2, round(anim.seconds * fps) + 1)

    def _sampler(self, anim: Animation, fps: int, rate: float | None = None) -> tuple[float, int, dict, object]:
        """(its length, its frames, {node: what moves it}, trs(node, frame): the node's (move, turn, size) at that
        frame, or its matrix for a node given as one) for poses() and worlds()."""
        length, frames = self.frames(anim, fps, rate)
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
        return length, frames, by_node, trs

    def worlds(self, anim: Animation, fps: int = baf.FPS, rate: float | None = None) -> tuple[float, list]:
        """(its length, each frame's [each bone's pose in the model (a 3 x 4), in the rig's bone order]), the nodes
        between bones counted in, as poses() samples them (`rate`: frames()'s)."""
        length, frames, _by_node, trs = self._sampler(anim, fps, rate)
        out = []
        for k in range(frames):
            w = []
            for j, joint in enumerate(self.joints):
                m = w[joint.parent] if joint.parent >= 0 else IDENTITY
                for n in self.chains[j] + [joint.node]:
                    part = trs(n, k)
                    m = mul(m, compose(*part) if isinstance(part[0], tuple) else part)
                w.append(m)
            out.append(w)
        return length, out

    def poses(self, anim: Animation, fps: int = baf.FPS) -> tuple[float, list]:
        """(its length in seconds, each bone's (moves, turns, sizes) at each of its frames, in the game's axes and
        units, as rusemod.baf.from_frames takes them). Each bone's pose is from its parent bone: a node between them
        counts in (their matrices multiplied and taken apart again); a bone the animation doesn't move keeps its rest."""
        length, frames, by_node, trs = self._sampler(anim, fps)
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


EVEN = 1e-3   # keys this close to one step apart (a share of the step) are evenly spaced: a float's time isn't exact


def sampled_rate(rig: Rig) -> float | None:
    """The frames a second a file's animations were sampled at, when every channel of every one of them has a key at
    each frame, all at one step (Blender's Send samples every frame of an action at its scene's rate): 30 for the
    game's, 24 for a scene set to 24. None when that can't be told (keys not evenly spaced, or none two apart)."""
    steps = []
    for anim in rig.animations:
        for ch in anim.channels:
            if len(ch.times) < 2:
                continue
            gaps = [b - a for a, b in zip(ch.times, ch.times[1:])]
            if min(gaps) <= 0 or max(gaps) - min(gaps) > EVEN * max(gaps):
                return None
            steps.append(sum(gaps) / len(gaps))
    if not steps or max(steps) - min(steps) > EVEN * max(steps):
        return None
    return len(steps) / sum(steps)


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
    rig = Rig(out, animations, None, notes, parent, rest, chains,
              [n for n in order if "mesh" in nodes[n] and "skin" in nodes[n]])
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


# --- a file whose bones were laid out for Blender, back in the game's frames (rusemod.animglb's notes) ---
# A pose that comes back within these of the clip that went out is the same: what Blender's own sums leave, and what
# its File > Export's Optimize Animation Size (on by default; the Studio's Send turns it off) flattens, a channel that
# moves less than 0.0001 over an action cut to its first and last key: 0.01 of the game's units a bone, a few down a
# chain of them (Blender 4.5's exporter, fcurve_is_constant; measured on the US rifleman's 41 clips,
# scratch/animmodels/agent5-4). 0.05 of the game's units is 0.3 mm on a soldier 312 units tall; a deliberate change
# is far more.
TOL_BACK_MOVE = 5e-2     # the game's units, as it shows in the model
TOL_BACK_FRAME = 5e-4    # the 3 x 3 of turn and size together (about 0.03 degrees): a mirrored bone's turn and size
#                          can be taken apart two ways (a minus on one axis or another), the same pose either way
_UNTURN = (0.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)   # rusemod.gltf.TURN's inverse, 12 numbers


@dataclass
class Back:
    """How a file's bones are the game's again (back_of): the bones in the game's order (`names`: the reference's
    that the file has, then those it adds), each one's parent there (-1: none), its bone in the rig (`joint`), the
    fixed turn that takes its pose in the file to the game's (`fix`: game = file x fix), its rest pose in the model,
    and the record: the reference itself while no bone moved, was added or went, else worked out from the file."""
    names: list
    parents: list
    joint: list
    fix: list
    world: list
    record: bytes
    turned: bool
    kept: bool
    moved: list = field(default_factory=list)
    new: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    hung: list = field(default_factory=list)


def _turn_off(a, b) -> float:
    """How far apart two poses' turns are (the largest difference of their 3 x 3 numbers, each column made length
    one first, so a size doesn't count)."""
    out = 0.0
    for j in range(3):
        ca = [a[i * 4 + j] for i in range(3)]
        cb = [b[i * 4 + j] for i in range(3)]
        na = math.sqrt(sum(v * v for v in ca)) or 1.0
        nb_ = math.sqrt(sum(v * v for v in cb)) or 1.0
        out = max(out, max(abs(x / na - y / nb_) for x, y in zip(ca, cb)))
    return out


def back_of(rig: Rig, reference: bytes) -> Back | None:
    """How the bones of a file read by rig_of are the game's again, against `reference`, the skeleton record they were
    laid out from (rusemod.gltf.rest_poses: turned by gltf.TURN, or as they are for a skeleton made in Blender; legs
    hung; sized bones as plain turns): which of the two layouts the file is in is read from its bones' turns at rest
    (most bones the reference has decide), then each bone the reference has takes the fixed turn that layout gave it,
    and a bone it hasn't got (made in Blender) the layout's turn back. A bone at its place gets the reference's own rest
    pose; the record is the reference's, byte for byte, while every bone is at its place and none was added or went.
    None when there is nothing to do: the file's bones are the game's frames already, under the game's parents (a file
    of the game's own frames, or one with no bone of the reference)."""
    from .gltf import rest_poses
    sk = baf.skeleton(reference)
    nb = sk["bones"]
    ref = [n.lower() for n in sk["names"]]
    at = {n: j for j, n in enumerate(rig.names)}
    common = [b for b in range(nb) if ref[b] in at]
    if not common:
        return None
    lay = {t: rest_poses(reference, list(range(nb)), turn=t) for t in (True, False)}
    score = {t: sorted(_turn_off(lay[t]["frames"][b], rig.joints[at[ref[b]]].world) for b in common) for t in lay}
    turned = score[True][len(common) // 2] < score[False][len(common) // 2]
    frames = lay[turned]["frames"]
    names, parents, joint, fix, world = [], [], [], [], []
    moved, missing, hung = [], [], []
    pos: dict = {}
    for b in range(nb):
        if ref[b] not in at:
            missing.append(sk["names"][b])
            continue
        j = at[ref[b]]
        # (a bone the file holds as the game has it, size and all, needs nothing: a model of the game's own frames)
        f = IDENTITY if near(rig.joints[j].world, sk["world"][b]) <= 1.0 else mul(inverse(frames[b]), sk["world"][b])
        w = mul(rig.joints[j].world, f)
        if near(w, sk["world"][b]) <= 1.0:
            w = tuple(sk["world"][b])
        else:
            moved.append(sk["names"][b])
        p = sk["parents"][b]
        while p >= 0 and ref[p] not in at:      # (its parent went: the nearest bone above it that's still there)
            p = sk["parents"][p]
        up = rig.joints[j].parent
        if (rig.names[up] if up >= 0 else None) != (ref[p] if p >= 0 else None):
            hung.append(sk["names"][b])
        pos[ref[b]] = len(names)
        names.append(sk["names"][b])
        parents.append(pos[ref[p]] if p >= 0 else -1)
        joint.append(j)
        fix.append(f)
        world.append(w)
    new = []
    back = _UNTURN if turned else IDENTITY
    for j, jt in enumerate(rig.joints):
        if jt.name in pos:
            continue
        new.append(jt.name)
        pos[jt.name] = len(names)
        names.append(jt.name)
        parents.append(pos[rig.names[jt.parent]] if jt.parent >= 0 else -1)
        joint.append(j)
        fix.append(back)
        world.append(mul(jt.world, back))
    if not turned and not hung and all(near(f, IDENTITY) <= 1.0 for f in fix):
        return None
    kept = not moved and not new and not missing
    if kept:
        record = bytes(reference)
    else:
        local = [w if p < 0 else mul(inverse(world[p]), w) for w, p in zip(world, parents)]
        record = baf.skeleton_bytes(names, parents, [inverse(w) for w in world], local, world)
    return Back(names, parents, joint, fix, world, record, turned, kept, moved, new, missing, hung)


def off_points(rig: Rig, back: Back, reference: bytes) -> list[str]:
    """The bones of `reference` (as it spells them, in its order) whose rest in the file moved away from the model's
    points: Blender's Edit mode moves a bone's rest and leaves the points where they were, so there they stay put,
    while a model keeping the reference's rest moves them with the bone. Each of back_of's moved bones' move from the
    reference's rest (its rest the game's way after the reference's inverse) is set against where each mesh on the
    bones sits in the file: the whole armature moved in Object mode takes its meshes along (real Blender 4.5 sends the
    bones and the mesh moved alike, 2026-11-12), so a bone moved with them is not off its points."""
    if not back.moved:
        return []
    sk = baf.skeleton(reference)
    at = {n.lower(): b for b, n in enumerate(sk["names"])}
    places = [rig.node_world(n) for n in rig.meshes] or [IDENTITY]
    moved = set(back.moved)
    out = []
    for i, name in enumerate(back.names):
        b = at.get(name.lower())
        if b is None or name not in moved:
            continue
        delta = mul(back.world[i], inverse(sk["world"][b]))
        if all(near(delta, m) > 1.0 for m in places):
            out.append((b, sk["names"][b]))
    return [n for _b, n in sorted(out)]


def weighted(doc: dict, binary: bytes) -> set:
    """The bones (lower case) some point of the file's meshes on bones leans on: a weight above nothing."""
    nodes = doc.get("nodes") or []
    out = set()
    for node in nodes:
        if "mesh" not in node or "skin" not in node:
            continue
        joints = ((doc.get("skins") or [])[node["skin"]]).get("joints") or []
        for prim in ((doc.get("meshes") or [])[node["mesh"]]).get("primitives") or []:
            attrs = prim.get("attributes") or {}
            k = 0
            while f"JOINTS_{k}" in attrs and f"WEIGHTS_{k}" in attrs:
                for js, ws in zip(glb_accessor(doc, binary, attrs[f"JOINTS_{k}"]),
                                  glb_accessor(doc, binary, attrs[f"WEIGHTS_{k}"])):
                    for j, wt in zip(js, ws):
                        if wt > 0 and 0 <= int(j) < len(joints):
                            out.add(str(nodes[joints[int(j)]].get("name", "")).lower())
                k += 1
    out.discard("")
    return out


def back_poses(rig: Rig, back: Back, anim: Animation, fps: int = baf.FPS,
               rate: float | None = None) -> tuple[float, list]:
    """An animation of the file as the game's poses: (its length, each of `back`'s bones' (moves, turns, sizes) at
    each frame, from its parent in the game, as rusemod.baf.from_frames takes them): each bone's pose in the model
    (Rig.worlds) times its fix, then taken from its game parent's. Turns on one side, each next one by the one before
    (rusemod.baf.same_side). `rate`: Rig.frames'."""
    length, frames = rig.worlds(anim, fps, rate)
    out = [([], [], []) for _ in back.names]
    for w in frames:
        game = [mul(w[j], f) for j, f in zip(back.joint, back.fix)]
        for i, p in enumerate(back.parents):
            move, turn, size, _off = decompose(game[i] if p < 0 else mul(inverse(game[p]), game[i]))
            out[i][0].append(tuple(move))
            out[i][1].append(tuple(turn))
            out[i][2].append(tuple(size))
    return length, [(m, baf.same_side(t), s) for m, t, s in out]


def _carried(doc: dict) -> bytes | None:
    """The record a file's skin carries (SKELETON_EXTRA), or None."""
    for skin in doc.get("skins") or []:
        given = (skin.get("extras") or {}).get(SKELETON_EXTRA)
        if given:
            try:
                return base64.b64decode(given, validate=True)
            except (ValueError, TypeError):
                return None
    return None


def _under_held(back: Back, reference: bytes, poses: list, orig: baf.Clip | None, frames: int) -> list:
    """back_poses' `poses` with each bone whose parent in `reference` the file hasn't got (back_of hangs it from the
    nearest bone above that the file has) taken from that parent again, as the clip will hold it: a bone the file
    hasn't got held as the clip that went out (`orig`) has it, else at its rest (clips_back's way). So each bone the
    file has is where the file puts it in the model, and a missing bone's pose isn't counted twice under it."""
    sk = baf.skeleton(reference)
    ref = [n.lower() for n in sk["names"]]
    pos = {n.lower(): i for i, n in enumerate(back.names)}
    track = {}
    if orig is not None:
        osk = baf.skeleton(orig.skeleton)
        for u, t in enumerate(orig.tracks):
            name = osk["names"][osk["index"][u]].lower()
            if name in ref:
                track[ref.index(name)] = t

    def held(b: int, k: int) -> tuple:
        if b in track:
            return compose(*baf.sample(track[b], k / (frames - 1) if frames > 1 else 0.0))
        return tuple(sk["local"][b])
    out = list(poses)
    for b in range(sk["bones"]):
        i, p = pos.get(ref[b]), sk["parents"][b]
        if i is None or p < 0 or ref[p] in pos:
            continue
        chain = []      # (the bones the file hasn't got, from the nearest one above that it has down to b's parent)
        while p >= 0 and ref[p] not in pos:
            chain.insert(0, p)
            p = sk["parents"][p]
        moves, turns, sizes = poses[i]
        got = ([], [], [])
        for k in range(frames):
            h = IDENTITY
            for m in chain:
                h = mul(h, held(m, k))
            move, turn, size, _off = decompose(mul(inverse(h), compose(moves[k], turns[k], sizes[k])))
            for part, v in zip(got, (move, turn, size)):
                part.append(tuple(v))
        out[i] = (got[0], baf.same_side(got[1]), got[2])
    return out


def _settle(rig: Rig, back: Back, anim: Animation, raw: bytes | None, rate: float | None = None,
            reference: bytes | None = None) -> tuple[float, list, dict]:
    """An animation's poses as back_poses gives them, with each bone the modder didn't change (its poses at every frame
    within TOL_BACK_* of the clip that went out, `raw`: its bytes, or None) given that clip's own poses, exactly.
    `rate`: Rig.frames'. `reference`: the skeleton the poses are for, when it isn't `back`'s own (clips_back's: a bone
    the file hasn't got stays in it, _under_held). Returns (its length, the poses in `back`'s order, {"clip": the clip
    that went out (None: none, or one of other bones, or of another length), "untouched": {back's bone: that clip's
    track}, "frames"})."""
    length, poses = back_poses(rig, back, anim, rate=rate)
    frames = len(poses[0][0]) if poses else 1
    orig = baf.parse(raw) if raw else None
    if orig is not None and not (orig.frames == frames and (frames == 1 or abs(orig.duration - length) < 1e-4)):
        orig = None
    if reference is not None and back.missing:
        poses = _under_held(back, reference, poses, orig, frames)
    untouched = {}
    if orig is not None:
        osk = baf.skeleton(orig.skeleton)
        names = [n.lower() for n in osk["names"]]
        track = {osk["index"][u]: t for u, t in enumerate(orig.tracks)}
        worlds = _clip_worlds(orig, osk, frames)
        for i, name in enumerate(back.names):
            b = names.index(name.lower()) if name.lower() in names else None
            if b is None or b not in track:
                continue
            p = osk["parents"][b]
            if _same_track(track[b], poses[i], frames, [w[p] for w in worlds] if p >= 0 else None):
                got = [baf.sample(track[b], k / (frames - 1) if frames > 1 else 0.0) for k in range(frames)]
                poses[i] = ([g[0] for g in got], baf.same_side([g[1] for g in got]), [g[2] for g in got])
                untouched[i] = track[b]
    return length, poses, {"clip": orig, "untouched": untouched, "frames": frames}


def turn_back(raw: bytes, reference: bytes | None = None, label: str = "the file",
              originals: dict | None = None) -> tuple[bytes | None, dict]:
    """A .glb whose bones were laid out for Blender (rusemod.gltf.model_glb's `clips`, rusemod.animglb.own_glb; and
    the same sent back by Blender, which keeps no extras) as a .glb in the game's own frames, for Import model and the
    unit's clips to read as any other: each bone under its game parent at its rest pose the game's way (back_of), the
    skins' joints in the record's order (the points' bone numbers with them) and their inverse bind matrices from those
    rest poses, the record in the skins' extras (the reference byte for byte while no bone moved), and every animation
    as the game's poses at each of its frames (back_poses; with `originals`, {the animation's name: the bytes of the
    clip that went out under it}, each bone the modder didn't change as that clip has it, exactly: _settle).
    `reference`: the skeleton record the bones were laid out from; None: the one the file carries. Returns (the new
    file, or None when there was nothing to turn back; {"turned", "kept", "moved", "new", "missing", "hung",
    "animations": [{"name", "frames", "seconds", "changed": the bones that came back changed, of a clip that went out
    under its name (None: no such clip)}]})."""
    from .gltf import FLOAT, USHORT, _Glb
    try:
        doc, binary = glb_document(raw)
    except (ValueError, struct.error) as exc:
        raise ModelError(f"{label}: {exc}") from None
    reference = reference or _carried(doc)
    if reference is None:
        return None, {"turned": False}
    rig = rig_of(doc, binary, label)
    back = back_of(rig, reference)
    if back is None:
        return None, {"turned": False}
    sk = baf.skeleton(back.record)
    g = _Glb()
    g.doc, g.bin = doc, bytearray(binary)
    nodes = doc["nodes"]
    joint_node = [rig.joints[j].node for j in back.joint]
    taken = {j.node for j in rig.joints}
    roots = [j for j in rig.joints if j.parent < 0]
    holder = None
    if roots:       # the node the bones hang from (Blender's armature), the nearest one above the first that isn't one
        up = rig.node_parent[roots[0].node]
        holder = up if up >= 0 else None
    for node in nodes:
        if "children" in node:
            node["children"] = [c for c in node["children"] if c not in taken]
            if not node["children"]:
                del node["children"]
    scene = (doc.get("scenes") or [{"nodes": []}])[doc.get("scene", 0)]
    scene["nodes"] = [n for n in scene.get("nodes", []) if n not in taken]
    h_world = IDENTITY
    if holder is not None:
        m, n = IDENTITY, holder
        while n >= 0:
            m = mul(_rest_matrix(rig.node_rest[n]), m)
            n = rig.node_parent[n]
        h_world = m
    for i, node_i in enumerate(joint_node):
        p = back.parents[i]
        local = sk["local"][i] if back.kept and (p >= 0 or holder is None or near(h_world, IDENTITY) == 0.0) else \
            (mul(inverse(back.world[p]), back.world[i]) if p >= 0 else mul(inverse(h_world), back.world[i]))
        move, turn, size, _off = decompose(local)
        node = nodes[node_i]
        node.pop("matrix", None)
        node.update(translation=list(move_out(move)), rotation=list(turn_out(turn)), scale=list(size_out(size)))
        if p >= 0:
            nodes[joint_node[p]].setdefault("children", []).append(node_i)
        elif holder is not None:
            nodes[holder].setdefault("children", []).append(node_i)
        else:
            scene["nodes"].append(node_i)
    order = {node: i for i, node in enumerate(joint_node)}
    for s, skin in enumerate(doc.get("skins") or []):
        old = list(skin.get("joints") or [])
        if not old or any(n not in order for n in old):
            continue
        remap = {k: order[n] for k, n in enumerate(old)}
        skin["joints"] = list(joint_node)
        ibm = [v for i in range(len(joint_node)) for v in matrix_out(sk["bind"][i])]
        g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(ibm)}f", *ibm)), "componentType": FLOAT,
                                   "count": len(joint_node), "type": "MAT4"})
        skin["inverseBindMatrices"] = len(g.doc["accessors"]) - 1
        skin.setdefault("extras", {})[SKELETON_EXTRA] = skeleton_extra(back.record)
        if remap == {k: k for k in range(len(old))}:
            continue
        for node in nodes:      # the points' bone numbers, as the joints now stand
            if node.get("skin") != s or "mesh" not in node:
                continue
            for prim in doc["meshes"][node["mesh"]]["primitives"]:
                for key in [k for k in prim.get("attributes", {}) if k.startswith("JOINTS_")]:
                    js = [tuple(remap.get(int(x), 0) for x in v) for v in glb_accessor(doc, binary, prim["attributes"][key])]
                    prim["attributes"][key] = g.accessor(js, "VEC4", USHORT)
    animations, said = [], []
    for anim in rig.animations:
        length, poses, settled = _settle(rig, back, anim, (originals or {}).get(anim.name))
        frames = settled["frames"]
        step = length / (frames - 1) if frames > 1 else 0.0
        times = [k * step for k in range(frames)]
        samplers, channels = [], []
        tin = g.accessor(times, "SCALAR", FLOAT, target=None)
        g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(times)], [max(times)]
        for i, (moves, turns, sizes) in enumerate(poses):
            for path, vals, out_of in (("translation", moves, move_out), ("rotation", turns, turn_out),
                                       ("scale", sizes, size_out)):
                tout = g.accessor([tuple(out_of(v)) for v in vals], "VEC4" if path == "rotation" else "VEC3", FLOAT,
                                  target=None)
                samplers.append({"input": tin, "output": tout, "interpolation": "LINEAR"})
                channels.append({"sampler": len(samplers) - 1, "target": {"node": joint_node[i], "path": path}})
        animations.append({"name": anim.name, "samplers": samplers, "channels": channels})
        said.append({"name": anim.name, "frames": frames, "seconds": round(length, 4),
                     "changed": [n for i, n in enumerate(back.names) if i not in settled["untouched"]]
                     if settled["clip"] is not None else None})
    if animations:
        doc["animations"] = animations
    else:
        doc.pop("animations", None)
    return g.to_bytes(), {"turned": back.turned, "kept": back.kept, "moved": back.moved, "new": back.new,
                          "missing": back.missing, "hung": back.hung, "animations": said}


def clips_back(rig: Rig, back: Back, reference: bytes, originals: dict | None = None,
               rate: float | None = None) -> list[dict]:
    """Each animation of the file as a game clip on the skeleton `reference` (a model on the game soldier's bones: the
    game's record, every one of its bones a track, as every clip the soldier plays has): its poses the game's way
    (back_poses), a bone the file hasn't got held as the clip that went out has it, or at its rest, and each bone under
    it taken from it (_under_held: where the file puts it in the model). `originals`: {the animation's name: the bytes
    of the clip that went out under it}; a clip of the same frames and length keeps every track the modder didn't
    change (each frame within TOL_BACK_* of it) as that clip's own, byte for byte, and its skeleton part; the others
    are written at each frame (rusemod.baf.from_frames). `rate`: the frames a second the file was sampled at when it
    isn't the game's (sampled_rate): each of its frames a frame of the clip (Rig.frames). Returns [{"name", "clip": its
    bytes, "changed": the bones whose track came back changed (all of them for an animation with no clip that went
    out), "same": whether it is the clip that went out, byte for byte, "frames", "seconds"}]."""
    sk = baf.skeleton(reference)
    nb = sk["bones"]
    ref = [n.lower() for n in sk["names"]]
    pos = {n.lower(): i for i, n in enumerate(back.names)}
    rest = [decompose(m)[:3] for m in sk["local"]]
    out = []
    for anim in rig.animations:
        raw = (originals or {}).get(anim.name)
        if raw and [n.lower() for n in baf.skeleton(baf.parse(raw).skeleton)["names"]] != ref:
            raw = None      # (a clip of other bones: not one to keep tracks of)
        length, poses, settled = _settle(rig, back, anim, raw, rate, reference)
        frames, orig = settled["frames"], settled["clip"]
        track = {}
        if orig is not None:
            osk = baf.skeleton(orig.skeleton)
            track = {osk["index"][u]: t for u, t in enumerate(orig.tracks)}
        full = []
        for b in range(nb):
            i = pos.get(ref[b])
            if i is not None:
                full.append(poses[i])
            elif b in track:        # (a bone the file hasn't got: as the clip that went out has it)
                got = [baf.sample(track[b], k / (frames - 1) if frames > 1 else 0.0) for k in range(frames)]
                full.append(([g[0] for g in got], baf.same_side([g[1] for g in got]), [g[2] for g in got]))
            else:
                full.append(([rest[b][0]] * frames, [rest[b][1]] * frames, [rest[b][2]] * frames))
        part = orig.skeleton if orig is not None else bytes(reference)
        clip = baf.from_frames(orig.duration if orig is not None else length, full, part)
        if orig is not None:
            kept = {ref.index(back.names[i].lower()) for i in settled["untouched"]}
            psk = baf.skeleton(part)
            changed = []
            for u, b in enumerate(psk["index"]):
                if b in kept or (ref[b] not in pos and b in track):
                    clip.tracks[u] = track[b]
                else:
                    changed.append(sk["names"][b])
            clip = baf.Clip(orig.duration, orig.frames, clip.tracks, part)
        else:
            changed = list(sk["names"])
        data = baf.build(clip, max(baf.MOST_BONES, nb))
        out.append({"name": anim.name, "clip": data, "changed": changed,
                    "same": orig is not None and data == bytes(raw), "frames": frames, "seconds": round(length, 4)})
    return out


def _clip_worlds(clip: baf.Clip, sk: dict, frames: int) -> list:
    """Each frame's [each bone's pose in the model (a 3 x 4)] as the clip plays them, bone by bone in its skeleton's
    order (parents first)."""
    track = {sk["index"][u]: t for u, t in enumerate(clip.tracks)}
    out = []
    for k in range(frames):
        frac = k / (frames - 1) if frames > 1 else 0.0
        w = [None] * sk["bones"]
        for b in range(sk["bones"]):
            m = compose(*baf.sample(track[b], frac)) if b in track else tuple(sk["local"][b])
            w[b] = m if sk["parents"][b] < 0 else mul(w[sk["parents"][b]], m)
        out.append(w)
    return out


def _same_track(track: baf.Track, poses: tuple, frames: int, parent: list | None = None) -> bool:
    """Whether a bone's poses at every frame are the track's, within TOL_BACK_*: its turn and size together (the 3 x 3
    they make), and its move as far as it shows in the model, through its parent's pose at that frame (`parent`, a
    3 x 4 a frame; None: it has none), so a bone under one the game sizes down to hide it (the rifle's muzzle point
    while the bazooka is out, sized 0.001) isn't held to a thousand times what shows."""
    moves, turns, sizes = poses
    for k in range(frames):
        a = compose(*baf.sample(track, k / (frames - 1) if frames > 1 else 0.0))
        b = compose(moves[k], turns[k], sizes[k])
        if max(abs(a[4 * i + j] - b[4 * i + j]) for i in range(3) for j in range(3)) > TOL_BACK_FRAME:
            return False
        d = [a[3] - b[3], a[7] - b[7], a[11] - b[11]]
        if parent is not None:
            m = parent[k]
            d = [m[4 * i] * d[0] + m[4 * i + 1] * d[1] + m[4 * i + 2] * d[2] for i in range(3)]
        if max(abs(x) for x in d) > TOL_BACK_MOVE:
            return False
    return True


# --- a model on bones of its own back from Blender: each animation as it went out where it came back the same ---
# The owner, 2026-11-13, item 45 ("A trip through Blender with nothing changed still rewrites all 25 of the horse's
# animation files, with a key at every frame"): "Yes, an animation that comes back from Bundler should come back the
# exact same." The model's own Blender (ruse_studio.modelblender) sends a model on bones of its own out with the
# animations the mod plays and, on its way back, writes into the file it takes in the skeleton record that went out
# (with_record: Blender keeps no extras) and each clip that went out, in its animation's extras (with_went_out), in the
# order they went out in. Whatever takes that file in (ruse_studio.animmodel_calls: Bring back, and every Resize or
# Move after, which fit the model again from it) keeps each animation that came back the same as the clip that went
# out, byte for byte, and of a changed one every bone that wasn't changed (kept_clip), as RUSE Decoy's own Blender
# button does with its clips (clips_back). A clip whose keys aren't on the game's 30 frames a second went out to
# Blender on them (ruse_studio.animblender.on_game_frames, RUSE Decoy's way too): what came back is set against that.
CLIP_OUT = "rusemod_clip_out"       # an animation's extras in a file back from Blender: the clip that went out (base64)
CLIP_GIVEN = "rusemod_clip_given"   # ... and what Blender was given of it, when that isn't the clip itself (base64)


def clips_out(doc: dict) -> dict:
    """{each animation's name: (the clip that went out to Blender under it, what Blender was given of it or None: the
    clip itself)}, as a file back from Blender carries them (CLIP_OUT, CLIP_GIVEN: with_went_out), named as rig_of
    names them; the first of a name the file gives twice (rusemod.unitmodel.own_clips numbers the second: never set
    against one). {} for none; one that can't be read is left out (that animation is taken in as Blender sent it)."""
    out: dict = {}
    for a, anim in enumerate(doc.get("animations") or []):
        if not isinstance(anim, dict):
            continue
        name = anim.get("name") or f"animation {a + 1}"
        extras = anim.get("extras") if isinstance(anim.get("extras"), dict) else {}
        if name in out or not isinstance(extras.get(CLIP_OUT), str):
            continue
        try:
            went = base64.b64decode(extras[CLIP_OUT], validate=True)
            given = extras.get(CLIP_GIVEN)
            out[name] = (went, base64.b64decode(given, validate=True) if isinstance(given, str) else None)
        except (ValueError, TypeError):
            continue
    return out


def with_went_out(raw: bytes, went: dict, given: dict | None = None) -> bytes:
    """A .glb Blender sent back with its animations in the order they went out in (`went`, {an animation's name: the
    clip that went out under it}, in that order; one made in Blender after them, in Blender's order: its export writes
    them in an order of its own, and the unit's animations are listed in the order the file gives them, so the mod's
    list stays as it was), each that went out carrying its clip in its extras (CLIP_OUT) and, when Blender was given it
    otherwise (`given`, {name: what Blender was given}), that too (CLIP_GIVEN): clips_out reads them. As it is when
    none of its animations went out."""
    from .gltf import glb_views, pack_glb
    given = given or {}
    doc, views = glb_views(raw)
    anims = [a for a in doc.get("animations") or [] if isinstance(a, dict)]
    named = [(a.get("name") or f"animation {k + 1}", a) for k, a in enumerate(anims)]
    if not any(name in went for name, _a in named):
        return raw
    first: dict = {}        # (each name's first animation: the one set against the clip that went out under it)
    for k, (name, _a) in enumerate(named):
        first.setdefault(name, k)
    for name, k in first.items():
        if name in went:
            a = named[k][1]
            extras = {key: v for key, v in (a.get("extras") if isinstance(a.get("extras"), dict) else {}).items()
                      if key not in (CLIP_OUT, CLIP_GIVEN)}
            extras[CLIP_OUT] = base64.b64encode(bytes(went[name])).decode("ascii")
            if given.get(name) is not None and bytes(given[name]) != bytes(went[name]):
                extras[CLIP_GIVEN] = base64.b64encode(bytes(given[name])).decode("ascii")
            a["extras"] = extras
    back = [named[first[name]][1] for name in went if name in first]
    doc["animations"] = back + [a for k, (name, a) in enumerate(named) if not (name in went and first[name] == k)]
    return pack_glb(doc, views)


def bones_of(raw: bytes, record: bytes) -> bool:
    """Whether a .glb's bones are the skeleton record `record`'s, within float noise (the same names and parents, every
    rest matrix within NEAR_*: _kept_record's measure); False for one that can't be read so."""
    try:
        doc, binary = glb_document(raw)
        doc["animations"] = []          # (its bones alone: the animations aren't read for this)
        return _kept_record(skeleton_extra(record), rig_of(doc, binary)) is not None
    except (ModelError, ValueError, KeyError, IndexError, TypeError, struct.error):
        return False


def with_record(raw: bytes, record: bytes) -> bytes:
    """A .glb Blender sent back (it keeps no extras) with the skeleton record that went out (`record`) in its skins'
    extras again (SKELETON_EXTRA), when its bones still match it (bones_of), so rig_of keeps that record byte for byte
    and every clip made on it keeps its skeleton part. As it is when they don't (a bone moved, added or renamed in
    Blender: its record is worked out again from its bones, as before), when it carries a record already, or when it
    can't be read so."""
    from .gltf import glb_views, pack_glb
    try:
        doc, views = glb_views(raw)
        if _carried(doc) is not None or not bones_of(raw, record):
            return raw
    except (ModelError, ValueError, KeyError, IndexError, TypeError, struct.error):
        return raw
    for skin in doc.get("skins") or []:
        extras = skin.get("extras") if isinstance(skin.get("extras"), dict) else {}
        skin["extras"] = {**extras, SKELETON_EXTRA: skeleton_extra(record)}
    return pack_glb(doc, views)


def _track_frames(track: baf.Track, frames: int) -> list:
    """A track's (move, turn, size) at each of `frames` frames, as rusemod.baf.sample gives them (one key holds, two go
    straight across the whole clip, more by time), the keys walked once instead of looked up again for every frame (a
    track of a clip made from Blender's has a key at every frame)."""
    fracs = [k / (frames - 1) if frames > 1 else 0.0 for k in range(frames)]

    def walk(keys: list, value, between) -> list:
        if len(keys) == 1:
            return [value(keys[0])] * frames
        if len(keys) == 2:
            a, b = value(keys[0]), value(keys[1])
            return [between(a, b, f) for f in fracs]
        times = [k[0] for k in keys]
        values = [value(k) for k in keys]
        out, j = [], 1
        for f in fracs:
            t = baf.time_of(f)
            while j < len(times) - 1 and times[j] < t:    # (rusemod.baf._segment's, from where the last frame was)
                j += 1
            t0, t1 = times[j - 1], times[j]
            out.append(between(values[j - 1], values[j], min(1.0, max(0.0, (t - t0) / (t1 - t0) if t1 > t0 else 0.0))))
        return out

    def vec(k):
        return tuple(k[1:4])

    def lerp(a, b, f):
        return tuple(a[i] + (b[i] - a[i]) * f for i in range(3))
    moves = walk(track.T, vec, lerp)
    turns = walk(track.R, lambda k: baf.unpack_quat(k[1:5]), baf.slerp)
    sizes = walk(track.S, vec, lerp)
    return list(zip(moves, turns, sizes))


def _same_frames(a: list, b: list, parent: list | None) -> bool:
    """_same_track's measure on two tracks' poses at each frame (_track_frames'): within TOL_BACK_* at every one."""
    for k, (pa, pb) in enumerate(zip(a, b)):
        x, y = compose(*pa), compose(*pb)
        if max(abs(x[4 * i + j] - y[4 * i + j]) for i in range(3) for j in range(3)) > TOL_BACK_FRAME:
            return False
        d = [x[3] - y[3], x[7] - y[7], x[11] - y[11]]
        if parent is not None:
            m = parent[k]
            d = [m[4 * i] * d[0] + m[4 * i + 1] * d[1] + m[4 * i + 2] * d[2] for i in range(3)]
        if max(abs(v) for v in d) > TOL_BACK_MOVE:
            return False
    return True


def kept_clip(made: bytes, went: bytes, given: bytes | None = None,
              poses: list | None = None) -> tuple[bytes, list | None]:
    """An animation taken in from a file back from Blender (`made`: the clip rusemod.unitmodel.own_clips made of it,
    from `poses`: Rig.poses' each bone's (moves, turns, sizes) at each frame, as the file has them) set against what
    went out to Blender under its name, as RUSE Decoy's Blender button sets its clips (_settle): `went`, the clip as the
    mod had it, and `given`, what Blender was given of it when that isn't the clip itself (on the game's frames:
    ruse_studio.animblender.on_game_frames). Each bone whose pose comes back within TOL_BACK_* of what Blender was given
    at every frame keeps that track, byte for byte, and the clip its length; every bone so, on the same skeleton
    record: `went` itself, byte for byte. Its poses as the file has them, never `made`'s own tracks, are what's
    measured: a turn near half a turn is packed with its w no closer than about 0.001 (rusemod.baf), so a clip packed
    again from Blender's numbers moved such a turn by more than TOL_BACK_FRAME (real Blender 4.5.14, the Generic
    Horse's clavicles, 2026-11-13) where Blender hadn't (None: `made`'s tracks, for a caller without the file). Set
    against each other only when both are on the same bones (names, parents and track order) with the same frames
    and length (within 1e-4 of a second, _settle's); else `made` as it is (its bones or timing changed in Blender).
    Returns (the clip, the bones whose track came back changed, in track order; None when the two couldn't be set
    against each other)."""
    against = bytes(given) if given is not None else bytes(went)
    clip, changed = _kept_tracks(bytes(made), against, poses)
    if changed == [] and clip == against:      # (came back as Blender was given it: the clip as the mod had it)
        return bytes(went), []
    return clip, changed


def _kept_tracks(made: bytes, went: bytes, poses: list | None = None) -> tuple[bytes, list | None]:
    """kept_clip's work, `made` set against one clip (`went`): each bone's track as `went` has it where its pose
    (`poses`, else `made`'s track) came back within TOL_BACK_*, else as `made` has it; all of them so, on the same
    record: `went` itself."""
    if made == went:
        return went, []
    try:
        m, w = baf.parse(made), baf.parse(went)
        msk, wsk = baf.skeleton(m.skeleton), baf.skeleton(w.skeleton)
    except (ValueError, IndexError, struct.error, UnicodeDecodeError):    # (baf.ClipError is a ValueError)
        return made, None
    frames = m.frames
    if (msk["names"] != wsk["names"] or msk["parents"] != wsk["parents"] or msk["index"] != wsk["index"]
            or len(m.tracks) != len(w.tracks) or len(w.tracks) != wsk["bones"] or w.frames != frames
            or (frames > 1 and abs(m.duration - w.duration) >= 1e-4)
            or (poses is not None and (len(poses) != wsk["bones"] or any(len(ch) != frames for p in poses
                                                                         for ch in p)))):
        return made, None
    was = [_track_frames(t, frames) for t in w.tracks]
    worlds = None
    tracks, changed = [], []
    for u, (mt, wt) in enumerate(zip(m.tracks, w.tracks)):
        b = wsk["index"][u]
        same = mt == wt
        if not same:
            if worlds is None:      # (each bone's pose in the model at each frame, as the clip that went out plays)
                by_bone = {wsk["index"][v]: was[v] for v in range(len(w.tracks))}
                worlds = []
                for k in range(frames):
                    row = [None] * wsk["bones"]
                    for c in range(wsk["bones"]):
                        here = compose(*by_bone[c][k])
                        row[c] = here if wsk["parents"][c] < 0 else mul(row[wsk["parents"][c]], here)
                    worlds.append(row)
            p = wsk["parents"][b]
            back = list(zip(*poses[b])) if poses is not None else _track_frames(mt, frames)
            same = _same_frames(was[u], back, [x[p] for x in worlds] if p >= 0 else None)
        tracks.append(wt if same else mt)
        if not same:
            changed.append(wsk["names"][b])
    if not changed and m.skeleton == w.skeleton:
        return went, []
    return baf.build(baf.Clip(w.duration, w.frames, tracks, m.skeleton), max(baf.MOST_BONES, len(tracks))), changed


def kept_clips(made: dict, out: dict, rig: Rig | None = None) -> tuple[dict, dict]:
    """kept_clip for each animation of `made` ({name: its clip}, in its order: rusemod.unitmodel.own_clips' of `rig`,
    the file's, whose poses are measured) that went out under its name (`out`: clips_out's, {name: (the clip, what
    Blender was given or None)}): ({name: the clip}, {name: the bones that came back changed, or None: not set against
    one})."""
    poses: dict = {}
    if rig is not None:
        for anim in rig.animations:     # (named as own_clips names them: a name given twice numbered)
            name, k = anim.name, 2
            while name in poses:
                name, k = f"{anim.name} {k}", k + 1
            poses[name] = anim
    kept, changed = {}, {}
    for name, data in made.items():
        if name in out:
            anim = poses.get(name)
            kept[name], changed[name] = kept_clip(data, *out[name],
                                                  poses=rig.poses(anim)[1] if anim is not None else None)
        else:
            kept[name], changed[name] = data, None
    return kept, changed
