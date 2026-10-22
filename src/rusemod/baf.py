"""The game's animation clips (.baf, version 15): read and written byte for byte, sampled at any moment, and changed
(faster or slower, a bone made bigger or turned, another clip of the same skeleton in its place). RUSE Decoy's
animations (ruse_studio.decoy, rusemod.anim) are built on this.

The format was worked out by DomesticNukes (all 585 of the game's clips read and written again byte for byte, and a
changed clip seen in the game: "Big Heads", 2026-10-09). A clip is:
  - a 28-byte header: u32 15, f32 its length in seconds, u16 frames, u16 bones, u32 the tracks' offset (28), u32 the
    skeleton's offset, u32 the tracks' size, u32 the skeleton's size; then the tracks, then the skeleton, to the end;
  - the tracks: a u32 offset per bone (blocks back to back from 4 x bones on), each block u32 nT, nS, nR, then nT
    moves and nS sizes (u32 time, 3 x f32) and nR turns (u32 time, a quaternion packed in four u16); every bone has
    at least one key of each kind; one key holds all along, two go in a straight line over the whole clip (their
    times aren't used), more are looked up by time, so times ascend and, with more than two, end at 8,388,607;
  - a key's time: its place in the clip x 8,388,607 (2^23 - 1);
  - a turn: x, y, z in 21 bits each (field x 2/2^21 - 1), w from length one, its sign in the last bit;
  - track u moves skeleton bone index[u]; the skeleton (names, parents, rest poses) is the model's: a clip belongs to
    the skeleton it was made for, at most 64 bones.
A bone's pose is move x turn x size, from its parent; bones without a parent (a biped's legs too) are in the model's
own space.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

SCALE = 2.0 / (1 << 21)
LAST_TIME = 0x7FFFFF     # 8,388,607
MOST_BONES = 64          # an animated model's most


class ClipError(ValueError):
    pass


@dataclass
class Track:
    T: list = field(default_factory=list)   # moves [(time, x, y, z)]
    S: list = field(default_factory=list)   # sizes [(time, x, y, z)]
    R: list = field(default_factory=list)   # turns [(time, w0, w1, w2, w3)]: the packed quaternion's four words


@dataclass
class Clip:
    duration: float
    frames: int
    tracks: list          # in the file's order: track u moves skeleton bone index[u]
    skeleton: bytes       # the skeleton part as the file has it

    @property
    def bones(self) -> int:
        return len(self.tracks)


# --- turns ---
def unpack_quat(words) -> tuple:
    """(w0, w1, w2, w3) -> (x, y, z, w)."""
    w0, w1, w2, w3 = words
    x = (w0 << 5 | w1 >> 11) * SCALE - 1.0
    y = ((w1 & 0x7FF) << 10 | w2 >> 6) * SCALE - 1.0
    z = ((w2 & 0x3F) << 15 | w3 >> 1) * SCALE - 1.0
    w = math.sqrt(max(0.0, 1.0 - x * x - y * y - z * z))
    return x, y, z, (-w if w3 & 1 else w)


def pack_quat(x: float, y: float, z: float, w: float) -> tuple:
    """(x, y, z, w) -> the four words (made length one first; a w of -0.0 keeps its sign, as the game's files do)."""
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    top = (1 << 21) - 1
    f = [min(top, max(0, int(round((v + 1.0) / SCALE)))) for v in (x, y, z)]
    neg = 1 if math.copysign(1.0, w) < 0 else 0
    return (f[0] >> 5, ((f[0] & 0x1F) << 11) | (f[1] >> 10), ((f[1] & 0x3FF) << 6) | (f[2] >> 15),
            ((f[2] & 0x7FFF) << 1) | neg)


def qmul(a, b) -> tuple:
    """a then b's frame: the quaternion product a x b, (x, y, z, w)."""
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)


def axis_angle(axis: str, degrees: float) -> tuple:
    a = math.radians(degrees) / 2
    s = math.sin(a)
    return {"x": (s, 0.0, 0.0, math.cos(a)), "y": (0.0, s, 0.0, math.cos(a)), "z": (0.0, 0.0, s, math.cos(a))}[axis]


def time_of(fraction: float) -> int:
    """A place in the clip (0..1) as the file keeps it."""
    return min(LAST_TIME, max(0, int(round(fraction * LAST_TIME))))


# --- reading and writing ---
def parse(b: bytes) -> Clip:
    if len(b) < 28:
        raise ClipError("not an animation clip")
    ver, dur, frames, bones, t_off, s_off, t_size, s_size = struct.unpack_from("<IfHHIIII", b, 0)
    if ver != 15:
        raise ClipError(f"an animation clip of version {ver}, not 15")
    if not (t_off == 28 and t_off + t_size == s_off and s_off + s_size == len(b)):
        raise ClipError("an animation clip whose parts don't follow each other")
    offs = struct.unpack_from(f"<{bones}I", b, t_off)
    tracks, expect = [], 4 * bones
    for o in offs:
        if o != expect:
            raise ClipError("an animation clip whose bones' blocks aren't back to back")
        p = t_off + o
        nT, nS, nR = struct.unpack_from("<3I", b, p)
        q = p + 12
        T = [struct.unpack_from("<I3f", b, q + 16 * k) for k in range(nT)]
        q += 16 * nT
        S = [struct.unpack_from("<I3f", b, q + 16 * k) for k in range(nS)]
        q += 16 * nS
        R = [struct.unpack_from("<I4H", b, q + 12 * k) for k in range(nR)]
        tracks.append(Track(T, S, R))
        expect = o + 12 + 16 * (nT + nS) + 12 * nR
    if expect != t_size:
        raise ClipError("an animation clip whose tracks end where they shouldn't")
    return Clip(dur, frames, tracks, bytes(b[s_off:s_off + s_size]))


def check(c: Clip) -> None:
    """The rules a clip must keep for the game (above): a wrong clip fails here, not in the game."""
    if not 0 < c.bones <= MOST_BONES:
        raise ClipError(f"{c.bones} bones: an animated model has 1 to {MOST_BONES}")
    if c.frames < 1 or not c.duration > 0.0 or math.isinf(c.duration):
        raise ClipError("a clip needs frames and a length")
    for u, t in enumerate(c.tracks):
        if not (t.T and t.S and t.R):
            raise ClipError(f"bone {u}: every kind of key needs at least one")
        for keys in (t.T, t.S, t.R):
            times = [k[0] for k in keys]
            if any(not 0 <= v <= LAST_TIME for v in times) or times != sorted(times):
                raise ClipError(f"bone {u}: key times out of order")
            if len(keys) > 2 and times[-1] != LAST_TIME:
                raise ClipError(f"bone {u}: with more than two keys the last must be at the clip's end")


def build(c: Clip) -> bytes:
    check(c)
    blocks = []
    for t in c.tracks:
        out = bytearray(struct.pack("<3I", len(t.T), len(t.S), len(t.R)))
        for k in list(t.T) + list(t.S):
            out += struct.pack("<I3f", *k)
        for k in t.R:
            out += struct.pack("<I4H", *k)
        blocks.append(bytes(out))
    offs, o = [], 4 * c.bones
    for blk in blocks:
        offs.append(o)
        o += len(blk)
    head = struct.pack("<IfHHIIII", 15, c.duration, c.frames, c.bones, 28, 28 + o, o, len(c.skeleton))
    return head + struct.pack(f"<{c.bones}I", *offs) + b"".join(blocks) + c.skeleton


# --- the skeleton ---
def skeleton(part: bytes) -> dict:
    """A skeleton part (a clip's, or a model's skeleton file's, laid out the same): bone names, parents (-1: none),
    the track -> bone index, and the three sets of 3x4 matrices (rows of [r r r t]): "bind" the inverse of each
    bone's rest pose in the model, "local" its rest pose from its parent, "world" its rest pose in the model."""
    one, nb = struct.unpack_from("<II", part, 0)
    m_off, p_off, i_off, n_off, m_size, p_size, i_size = struct.unpack_from("<7I", part, 8)
    lens = struct.unpack_from(f"<{nb}H", part, 36)
    names, p = [], n_off
    for n in lens:
        names.append(part[p:p + n].decode("latin-1"))
        p += n
    mats = [struct.unpack_from("<12f", part, m_off + 48 * k) for k in range(3 * nb)]
    return {"bones": nb, "names": names, "parents": list(struct.unpack_from(f"<{nb}i", part, p_off)),
            "index": list(struct.unpack_from(f"<{nb}I", part, i_off)),
            "bind": mats[:nb], "local": mats[nb:2 * nb], "world": mats[2 * nb:]}


def track_of(c: Clip, bone: str) -> int:
    """The track that moves the bone called `bone` (any case)."""
    s = skeleton(c.skeleton)
    want = bone.lower()
    for i, n in enumerate(s["names"]):
        if n.lower() == want:
            return s["index"].index(i)
    raise ClipError(f"this clip has no bone called {bone}")


# --- sampling (as the game does: 1 key holds, 2 go straight across the whole clip, more by time) ---
def _segment(times, t):
    j = 1
    while j < len(times) - 1 and times[j] < t:
        j += 1
    t0, t1 = times[j - 1], times[j]
    return j - 1, j, min(1.0, max(0.0, (t - t0) / (t1 - t0) if t1 > t0 else 0.0))


def slerp(q0, q1, f):
    x0, y0, z0, w0 = q0
    x1, y1, z1, w1 = q1
    d = x0 * x1 + y0 * y1 + z0 * z1 + w0 * w1
    if d < 0.0:
        x1, y1, z1, w1, d = -x1, -y1, -z1, -w1, -d
    if d > 0.9995:
        q = (x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, z0 + (z1 - z0) * f, w0 + (w1 - w0) * f)
        n = math.sqrt(sum(v * v for v in q)) or 1.0
        return tuple(v / n for v in q)
    th = math.acos(min(1.0, d))
    s0, s1 = math.sin((1 - f) * th) / math.sin(th), math.sin(f * th) / math.sin(th)
    return (x0 * s0 + x1 * s1, y0 * s0 + y1 * s1, z0 * s0 + z1 * s1, w0 * s0 + w1 * s1)


def _vec(keys, frac):
    if len(keys) == 1:
        return tuple(keys[0][1:4])
    if len(keys) == 2:
        a, b = keys[0][1:4], keys[1][1:4]
        return tuple(a[i] + (b[i] - a[i]) * frac for i in range(3))
    a, b, f = _segment([k[0] for k in keys], time_of(frac))
    va, vb = keys[a][1:4], keys[b][1:4]
    return tuple(va[i] + (vb[i] - va[i]) * f for i in range(3))


def _rot(keys, frac):
    if len(keys) == 1:
        return unpack_quat(keys[0][1:5])
    if len(keys) == 2:
        return slerp(unpack_quat(keys[0][1:5]), unpack_quat(keys[1][1:5]), frac)
    a, b, f = _segment([k[0] for k in keys], time_of(frac))
    return slerp(unpack_quat(keys[a][1:5]), unpack_quat(keys[b][1:5]), f)


def sample(t: Track, frac: float) -> tuple:
    """A bone's (move, turn (x, y, z, w), size) at a place in the clip (0..1)."""
    return _vec(t.T, frac), _rot(t.R, frac), _vec(t.S, frac)


# --- changes ---
def with_speed(c: Clip, percent: float) -> Clip:
    """The clip played faster (over 100) or slower: the same keys over a shorter or longer time."""
    if not 1 <= percent <= 1000:
        raise ClipError("a speed is a percent from 1 to 1000")
    return Clip(c.duration * 100.0 / percent, c.frames, c.tracks, c.skeleton)


def with_bone(c: Clip, bone: str, size: float = 1.0, turn: tuple | None = None) -> Clip:
    """One bone made `size` times its size, and turned by `turn` ((axis "x"/"y"/"z", degrees), in its own frame) at
    every key of the clip; every other bone as it was."""
    u = track_of(c, bone)
    t = c.tracks[u]
    S = [(k[0], k[1] * size, k[2] * size, k[3] * size) for k in t.S]
    R = list(t.R)
    if turn:
        r = axis_angle(*turn)
        R = [(k[0],) + pack_quat(*qmul(unpack_quat(k[1:5]), r)) for k in t.R]
    tracks = list(c.tracks)
    tracks[u] = Track(list(t.T), S, R)
    return Clip(c.duration, c.frames, tracks, c.skeleton)


def same_skeleton(a: Clip, b: Clip) -> bool:
    """Whether `b` can stand in for `a`: the same bones, by name, in the same order."""
    sa, sb = skeleton(a.skeleton), skeleton(b.skeleton)
    return [n.lower() for n in sa["names"]] == [n.lower() for n in sb["names"]] and sa["index"] == sb["index"]
