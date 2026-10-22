"""Motion capture onto the game's soldiers: a .bvh file (100STYLE, the CMU database, Mixamo, Blender's export...)
made into one of the game's animation clips (rusemod.baf), on the skeleton of the clip it takes the place of.

How (the way retargeting tools do it, Expy Kit's and MotionBuilder's included):
  1. read the .bvh: its joints (offsets from their parents), the order of each joint's turns, and every frame;
  2. find the body's parts by their joints' names (hips, spine, chest, neck, head, both arms and legs); a file
     whose joints aren't named in any of the usual ways says which parts it lacks;
  3. turn the file's axes into the game's (forward, right, up: the file's own left and up found from its joints, so
     a file lying on its side or facing another way comes out the same);
  4. for each part, how the file's rest pose sits against the game's (a T-pose against the soldiers' arms down):
     the turn that lays the file's bone along the game's bone, with a second direction fixing its twist;
  5. every frame (at the game's 30 a second): each part's turn in the world, carried over onto the game's bone
     through that rest-pose turn; the bones that hang from others get their turn from their parent's, the legs
     (the soldiers' legs hang from nothing: they're kept in the model's space) their place too, from the hips down
     along the game's own leg lengths;
  6. the hips' place from the file, made the soldier's size (by the length of the legs), kept on the spot (the game
     moves the unit itself) and stood on the ground where the game's clip stands; the clip made to loop when the
     game's clip loops (its last pose eased into its first);
  7. every bone the file doesn't move (fingers on the rifle, the weapons, the helpers) keeps the game clip's keys.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from . import baf

FPS = 30.0          # the game's clips: 25 frames in 0.8 s, 61 in 2 s...


class MocapError(ValueError):
    pass


# --- reading a .bvh ---
@dataclass
class Bvh:
    names: list            # joints in the file's order (an end site is "<its joint>_end", no channels)
    parents: list          # -1: the root
    offsets: list          # (x, y, z) from the parent
    channels: list         # per joint: its channel names in order ("Xposition", "Yrotation"...)
    frame_time: float
    frames: list           # per frame: every channel's value, the joints' in order

    @property
    def seconds(self) -> float:
        return max(0, len(self.frames) - 1) * self.frame_time


def read_bvh(text: str) -> Bvh:
    tok = text.split()
    i = 0

    def take():
        nonlocal i
        if i >= len(tok):
            raise MocapError("the file ends too soon: not a whole .bvh")
        i += 1
        return tok[i - 1]

    if take().upper() != "HIERARCHY":
        raise MocapError("not a .bvh file: it doesn't start with HIERARCHY")
    names, parents, offsets, channels = [], [], [], []
    stack = []
    while True:
        t = take()
        u = t.upper()
        if u in ("ROOT", "JOINT"):
            names.append(take())
            parents.append(stack[-1] if stack else -1)
            offsets.append((0.0, 0.0, 0.0))
            channels.append([])
            if take() != "{":
                raise MocapError(f"{names[-1]}: a joint's block starts with {{")
            stack.append(len(names) - 1)
        elif u == "END":
            take()  # "Site"
            names.append(names[stack[-1]] + "_end")
            parents.append(stack[-1])
            offsets.append((0.0, 0.0, 0.0))
            channels.append([])
            if take() != "{":
                raise MocapError("an end site's block starts with {")
            stack.append(len(names) - 1)
        elif u == "OFFSET":
            offsets[stack[-1]] = (float(take()), float(take()), float(take()))
        elif u == "CHANNELS":
            channels[stack[-1]] = [take() for _ in range(int(take()))]
        elif t == "}":
            stack.pop()
            if not stack and i < len(tok) and tok[i].upper() == "MOTION":
                take()
                break
        elif u == "MOTION":
            break
        else:
            raise MocapError(f"not a .bvh file: {t!r} in its joints")
    if not names:
        raise MocapError("the file has no joints")
    take()  # "Frames:"
    n = int(take())
    take()  # "Frame"
    take()  # "Time:"
    ft = float(take())
    if not ft > 0:
        raise MocapError("the file's frame time isn't a time")
    width = sum(len(c) for c in channels)
    rest = tok[i:i + n * width]
    if len(rest) < n * width:
        n = len(rest) // width   # (some exporters say one frame more than they write)
    vals = [float(v) for v in rest[:n * width]]
    frames = [vals[k * width:(k + 1) * width] for k in range(n)]
    if not frames:
        raise MocapError("the file has no frames")
    return Bvh(names, parents, list(offsets), channels, ft, frames)


# --- small 3 x 3 sums (rows), no libraries ---
def _mm(a, b):
    return [[a[r][0] * b[0][c] + a[r][1] * b[1][c] + a[r][2] * b[2][c] for c in range(3)] for r in range(3)]


def _tr(a):
    return [[a[c][r] for c in range(3)] for r in range(3)]


def _mv(a, v):
    return (a[0][0] * v[0] + a[0][1] * v[1] + a[0][2] * v[2], a[1][0] * v[0] + a[1][1] * v[1] + a[1][2] * v[2],
            a[2][0] * v[0] + a[2][1] * v[1] + a[2][2] * v[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-9 else (0.0, 0.0, 0.0)


_I = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def _axis_m(axis: str, degrees: float):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    if axis == "X":
        return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]
    if axis == "Y":
        return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


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


def _q_to_m(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def _orthonormal(r):
    """The nearest turn to a 3x3 that may carry a size (Gram-Schmidt on its columns)."""
    c0 = _unit((r[0][0], r[1][0], r[2][0]))
    c1 = (r[0][1], r[1][1], r[2][1])
    c1 = _unit(_sub(c1, _mul(c0, _dot(c0, c1))))
    c2 = _cross(c0, c1)
    return [[c0[i], c1[i], c2[i]] for i in range(3)]


def _frame(primary, secondary, *spare):
    """A turn whose x is `primary` and whose y lies toward `secondary` (another of `spare` when the two line up)."""
    p = _unit(primary)
    for s in (secondary,) + spare:
        s2 = _sub(s, _mul(p, _dot(p, s)))
        if math.sqrt(_dot(s2, s2)) > 0.2 * math.sqrt(_dot(s, s)):
            y = _unit(s2)
            z = _cross(p, y)
            return [[p[i], y[i], z[i]] for i in range(3)]
    raise MocapError("a bone with no direction")


# --- the body's parts ---
PARTS = ["hips", "spine", "chest", "neck", "head",
         "l_clavicle", "l_upperarm", "l_forearm", "l_hand", "r_clavicle", "r_upperarm", "r_forearm", "r_hand",
         "l_thigh", "l_calf", "l_foot", "l_toe", "r_thigh", "r_calf", "r_foot", "r_toe"]
NEEDED = ["hips", "head", "l_upperarm", "l_forearm", "r_upperarm", "r_forearm", "l_thigh", "l_calf", "l_foot",
          "r_thigh", "r_calf", "r_foot"]
# the usual names of each part, first that the file has wins (and a joint is one part only): 100STYLE (Chest..Chest4,
# LeftCollar, LeftShoulder = the upper arm, LeftHip), the CMU database (LowerBack, Spine, Spine1, LHipJoint,
# LeftUpLeg), Mixamo ("mixamorig:" before the same names as CMU's), 3ds Max's biped, Blender's and others
_SIDE = {"l": ["left", "l", "l_", "lft"], "r": ["right", "r", "r_", "rgt"]}
_LIMB = {"clavicle": ["collar", "clavicle", "shoulder"], "upperarm": ["arm", "upperarm", "shoulder", "humerus"],
         "forearm": ["forearm", "elbow", "lowerarm", "radius"], "hand": ["hand", "wrist"],
         "thigh": ["upleg", "hip", "thigh", "upperleg", "femur"], "calf": ["leg", "knee", "lowerleg", "shin", "calf",
                                                                          "tibia"],
         "foot": ["foot", "ankle"], "toe": ["toebase", "toe", "toes", "toe0"]}
_TORSO = {"hips": ["hips", "pelvis", "hip", "root"], "spine": ["spine", "chest", "spine01", "lowerback"],
          "chest": ["spine2", "chest4", "chest3", "upperchest", "spine1", "chest2", "spine02", "spine3"],
          "neck": ["neck", "neck1"], "head": ["head"]}
GAME = {"hips": "bip01", "spine": "bip01 spine", "chest": "bip01 spine1", "neck": "bip01 neck", "head": "bip01 head",
        "l_clavicle": "bip01 l clavicle", "l_upperarm": "bip01 l upperarm", "l_forearm": "bip01 l forearm",
        "l_hand": "bip01 l hand", "r_clavicle": "bip01 r clavicle", "r_upperarm": "bip01 r upperarm",
        "r_forearm": "bip01 r forearm", "r_hand": "bip01 r hand", "l_thigh": "bip01 l thigh",
        "l_calf": "bip01 l calf", "l_foot": "bip01 l foot", "l_toe": "bip01 l toe0", "r_thigh": "bip01 r thigh",
        "r_calf": "bip01 r calf", "r_foot": "bip01 r foot", "r_toe": "bip01 r toe0"}
# each part's direction: toward this part's joint ("" = along the bone's own x, the file's: toward its own child)
_NEXT = {"spine": "chest", "chest": "neck", "neck": "head", "head": "",
         "l_clavicle": "l_upperarm", "l_upperarm": "l_forearm", "l_forearm": "l_hand", "l_hand": "",
         "r_clavicle": "r_upperarm", "r_upperarm": "r_forearm", "r_forearm": "r_hand", "r_hand": "",
         "l_thigh": "l_calf", "l_calf": "l_foot", "l_foot": "l_toe", "l_toe": "",
         "r_thigh": "r_calf", "r_calf": "r_foot", "r_foot": "r_toe", "r_toe": ""}
# and what fixes its twist: the body's left, forward or up (the next one when the bone lies along it)
_TWIST = {"hips": "left", "spine": "left", "chest": "left", "neck": "left", "head": "left",
          "clavicle": "forward", "upperarm": "forward", "forearm": "forward", "hand": "up",
          "thigh": "forward", "calf": "forward", "foot": "left", "toe": "left"}


def _key(name: str) -> str:
    n = name.rsplit(":", 1)[-1].rsplit("|", 1)[-1].lower()
    n = re.sub(r"^(bip0?1|mixamorig|def|bone)[ _.-]*", "", n)
    return re.sub(r"[^a-z0-9]", "", n)


def parts_of(bvh: Bvh) -> dict:
    """{part: joint index} for the parts the file's joint names show (see PARTS)."""
    keys = {}
    for j, n in enumerate(bvh.names):
        if not n.endswith("_end") or bvh.channels[j]:
            keys.setdefault(_key(n), j)
    used, out = set(), {}

    def pick(part, cands):
        for c in cands:
            j = keys.get(c)
            if j is not None and j not in used:
                used.add(j)
                out[part] = j
                return

    pick("hips", _TORSO["hips"])
    if "hips" not in out:   # the root, whatever it's called
        out["hips"] = bvh.parents.index(-1)
        used.add(out["hips"])
    for side in ("l", "r"):
        for limb in ("clavicle", "upperarm", "forearm", "hand", "thigh", "calf", "foot", "toe"):
            pick(f"{side}_{limb}", [s + c for c in _LIMB[limb] for s in _SIDE[side]])
    for part in ("spine", "chest", "neck", "head"):
        pick(part, _TORSO[part])
    return out


def missing(bvh: Bvh) -> list:
    """The parts a file needs and hasn't (by name): empty when it can be used."""
    got = parts_of(bvh)
    return [p for p in NEEDED if p not in got]


def credit_of(bvh: Bvh) -> str:
    """The credit a clip made from a known set must carry ("" when the set isn't known: the maker writes it)."""
    names = {n.lower() for n in bvh.names}
    if {"chest4", "leftcollar", "lefthip"} <= names:
        return ("100STYLE dataset by Ian Mason, Sebastian Starke and Taku Komura (2022), CC BY 4.0, "
                "https://zenodo.org/record/8127870; retargeted to R.U.S.E.'s soldiers")
    if {"lhipjoint", "lowerback", "leftupleg"} <= names:
        return ("Motion capture from mocap.cs.cmu.edu (created with funding from NSF EIA-0196217), BVH conversion by "
                "Bruce Hahne (cgspeed); retargeted to R.U.S.E.'s soldiers")
    return ""


# --- the file posed: every joint's turn and place in the world, frame by frame ---
def _rest_world(bvh: Bvh):
    pos = []
    for j, p in enumerate(bvh.parents):
        pos.append(bvh.offsets[j] if p < 0 else _add(pos[p], bvh.offsets[j]))
    return pos


def _pose(bvh: Bvh, frame: list):
    """Each joint's (turn, place) in the file's world at one frame."""
    rot, pos = [None] * len(bvh.names), [None] * len(bvh.names)
    k = 0
    for j, p in enumerate(bvh.parents):
        r, move = _I, list(bvh.offsets[j])
        for ch in bvh.channels[j]:
            v = frame[k]
            k += 1
            c = ch[0].upper()
            if ch[1:].lower() == "rotation":
                r = _mm(r, _axis_m(c, v))
            elif ch[1:].lower() == "position":
                move["XYZ".index(c)] += v
        if p < 0:
            rot[j], pos[j] = r, tuple(move)
        else:
            rot[j] = _mm(rot[p], r)
            pos[j] = _add(pos[p], _mv(rot[p], move))
    return rot, pos


def _snap(v):
    """The file's axis nearest to `v` (+-x, y or z), as a unit vector."""
    a = max(range(3), key=lambda i: abs(v[i]))
    out = [0.0, 0.0, 0.0]
    out[a] = math.copysign(1.0, v[a])
    return tuple(out)


def _child_dir(bvh: Bvh, rest: list, j: int):
    kids = [k for k, p in enumerate(bvh.parents) if p == j]
    if not kids:
        return None
    k = max(kids, key=lambda k: _dot(bvh.offsets[k], bvh.offsets[k]))
    return _sub(rest[k], rest[j])


# --- the game's skeleton ---
def _m34(m):
    return [list(m[0:3]), list(m[4:7]), list(m[8:11])], (m[3], m[7], m[11])


def game_rest(clip: baf.Clip) -> dict:
    """The game clip's skeleton: per bone its name, parent, rest turn and place from its parent and in the model."""
    s = baf.skeleton(clip.skeleton)
    local = [_m34(m) for m in s["local"]]
    world = [_m34(m) for m in s["world"]]
    return {"names": [n.lower() for n in s["names"]], "parents": s["parents"], "index": s["index"],
            "local": [(_orthonormal(r), t) for r, t in local], "world": [(_orthonormal(r), t) for r, t in world]}


# --- the clip ---
def retarget(bvh: Bvh, template: baf.Clip, start: float = 0.0, end: float | None = None, in_place: bool = True,
             loop: bool | None = None, face: bool = True) -> tuple[baf.Clip, dict]:
    """(the clip, {"frames", "seconds", "parts", "scale", "loop"}) from `bvh` between `start` and `end` seconds, on
    the skeleton of `template` (the game clip it takes the place of). `loop`: None = as the template (a clip whose
    first and last poses are the same loops)."""
    got = parts_of(bvh)
    lack = [p for p in NEEDED if p not in got]
    if lack:
        raise MocapError("the file's joints don't show: " + ", ".join(lack))
    g = game_rest(template)
    gi = {n: b for b, n in enumerate(g["names"])}
    if any(GAME[p] not in gi for p in NEEDED):
        raise MocapError("this animation isn't on a soldier's skeleton (bip01 bones): motion capture can't go on it")
    drive = {p: gi[GAME[p]] for p in got if GAME[p] in gi}

    # the file's axes against the game's (game: x forward, y right, z up)
    rest = _rest_world(bvh)
    hips = got["hips"]
    up_s = _snap(_sub(rest[got["head"]], rest[hips]))
    left_raw = _sub(rest[got["l_thigh"]], rest[got["r_thigh"]])
    left_s = _snap(_sub(left_raw, _mul(up_s, _dot(left_raw, up_s))))
    fwd_s = _cross(left_s, up_s)
    P = [list(fwd_s), list(_mul(left_s, -1.0)), list(up_s)]       # game = P x file
    Pt = _tr(P)
    rest_g = [_mv(P, p) for p in rest]
    left_g, up_g, fwd_g = (0.0, -1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)
    side = {"left": left_g, "up": up_g, "forward": fwd_g}
    spare = (left_g, up_g, fwd_g)

    # each part's rest turn in the file (F_s) and in the game (F_t): x along the bone, y toward its twist direction
    gw = g["world"]

    def gpos(part):
        return gw[drive[part]][1]
    F = {}
    for part, b in drive.items():
        twist = side[_TWIST[part.split("_", 1)[-1]]]
        if part == "hips":
            ps = _sub(rest_g[got["spine"] if "spine" in got else got["head"]], rest_g[hips])
            pt = _sub(gw[gi["bip01 spine"]][1] if "bip01 spine" in gi else gpos("head"), gpos("hips"))
        else:
            nxt = _NEXT[part]
            if nxt and nxt in got and nxt in drive:
                ps = _sub(rest_g[got[nxt]], rest_g[got[part]])
                pt = _sub(gpos(nxt), gpos(part))
            else:
                d = _child_dir(bvh, rest, got[part])
                ps = _mv(P, d) if d else None
                r = gw[b][0]
                pt = (r[0][0], r[1][0], r[2][0])          # the game's bones run along their own x
                if ps is None:
                    ps = pt
        F[part] = _mm(_frame(ps, twist, *spare), _tr(_frame(pt, twist, *spare)))   # F_s x F_t^T

    # frames at the game's rate
    last = len(bvh.frames) - 1
    t0 = max(0.0, min(start, bvh.seconds))
    t1 = bvh.seconds if end is None else max(t0, min(end, bvh.seconds))
    n = max(2, int(round((t1 - t0) * FPS)) + 1)
    picks = [min(last, int(round((t0 + k / FPS) / bvh.frame_time))) for k in range(n)]
    poses = [_pose(bvh, bvh.frames[f]) for f in picks]
    W = [[_mm(_mm(P, r), Pt) for r in rot] for rot, _pos in poses]
    hip_pos = [_mv(P, pos[hips]) for _rot, pos in poses]

    # facing the game's forward: the hips' facing on average turned to +x
    yaw = _I
    if face:
        fx = sum(w[hips][0][0] for w in W)
        fy = sum(w[hips][1][0] for w in W)
        a = -math.atan2(fy, fx)
        yaw = [[math.cos(a), -math.sin(a), 0.0], [math.sin(a), math.cos(a), 0.0], [0.0, 0.0, 1.0]]
    W = [[_mm(yaw, r) for r in w] for w in W]
    hip_pos = [_mv(yaw, p) for p in hip_pos]

    # the soldier's size: the legs' length
    def leg_s(s):
        return (math.dist(rest[got[f"{s}_thigh"]], rest[got[f"{s}_calf"]]) +
                math.dist(rest[got[f"{s}_calf"]], rest[got[f"{s}_foot"]]))

    def leg_t(s):
        return (math.dist(gpos(f"{s}_thigh"), gpos(f"{s}_calf")) + math.dist(gpos(f"{s}_calf"), gpos(f"{s}_foot")))
    scale = (leg_t("l") + leg_t("r")) / ((leg_s("l") + leg_s("r")) or 1.0)
    hip_pos = [_mul(p, scale) for p in hip_pos]
    if in_place:
        a, z = hip_pos[0], hip_pos[-1]
        hip_pos = [(p[0] - a[0] - (z[0] - a[0]) * k / (n - 1), p[1] - a[1] - (z[1] - a[1]) * k / (n - 1), p[2])
                   for k, p in enumerate(hip_pos)]
    root_rest = gw[gi["bip01"]][1]
    hip_pos = [(p[0] + root_rest[0], p[1] + root_rest[1], p[2]) for p in hip_pos]

    # every game bone's turn in the world, frame by frame, and the legs' places
    nb = len(g["names"])
    parents = g["parents"]
    order = sorted(range(nb), key=lambda b: _depth(parents, b))
    Wt = []        # [frame][bone] turn
    Pw = []        # [frame][bone] place (the driven parentless bones only)
    for k in range(n):
        wk, pk = [None] * nb, [None] * nb
        for part, b in drive.items():
            wk[b] = _mm(_mm(W[k][got[part]], F[part]), gw[b][0])
        for b in order:
            if wk[b] is None:
                p = parents[b]
                lr = g["local"][b][0]
                wk[b] = _mm(wk[p], lr) if p >= 0 else gw[b][0]
        pk[gi["bip01"]] = hip_pos[k]
        for s in ("l", "r"):   # the legs, from the hips down the game's own leg
            chain = [gi["bip01"]] + [drive[f"{s}_{x}"] for x in ("thigh", "calf", "foot", "toe") if f"{s}_{x}" in drive]
            for a, b in zip(chain, chain[1:]):
                pk[b] = _add(pk[a], _mv(wk[a], _mv(_tr(gw[a][0]), _sub(gw[b][1], gw[a][1]))))
        Wt.append(wk)
        Pw.append(pk)

    # stood on the ground where the game's clip stands: its lowest foot or toe over the clip
    feet = [drive[p] for p in ("l_foot", "r_foot", "l_toe", "r_toe") if p in drive]
    low_t = min(min(k[3] for k in template.tracks[g["index"].index(b)].T) for b in feet)
    low_m = min(Pw[k][b][2] for k in range(n) for b in feet)
    lift = low_t - low_m
    for pk in Pw:
        for b in range(nb):
            if pk[b] is not None:
                pk[b] = (pk[b][0], pk[b][1], pk[b][2] + lift)

    # the keys: turns from the parent (the parentless: in the model), places for the parentless
    R = {b: [] for b in drive.values()}
    T = {b: [] for b in drive.values() if parents[b] < 0}
    for k in range(n):
        for b in R:
            p = parents[b]
            loc = Wt[k][b] if p < 0 else _mm(_tr(Wt[k][p]), Wt[k][b])
            q = _m_to_q(loc)
            if R[b] and sum(x * y for x, y in zip(q, R[b][-1])) < 0:
                q = tuple(-x for x in q)
            R[b].append(q)
        for b in T:
            T[b].append(Pw[k][b])
    if loop is None:
        loop = _loops(template)
    if loop and n > 2:   # the last pose eased into the first, little by little over the clip
        for b, qs in R.items():
            fix = _qmul(_qconj(qs[-1]), qs[0])
            R[b] = [_qmul(q, baf.slerp((0.0, 0.0, 0.0, 1.0), fix, k / (n - 1))) for k, q in enumerate(qs)]
        for b, ps in T.items():
            d = _sub(ps[0], ps[-1])
            T[b] = [_add(p, _mul(d, k / (n - 1))) for k, p in enumerate(ps)]

    times = [baf.time_of(k / (n - 1)) for k in range(n)]
    tracks = []
    for u, tr in enumerate(template.tracks):
        b = g["index"][u]
        if b not in R:
            tracks.append(tr)
            continue
        if b in T:
            tk = [(times[k],) + tuple(T[b][k]) for k in range(n)]
        else:
            lt = g["local"][b][1]
            tk = [(0, lt[0], lt[1], lt[2])]
        rk = [(times[k],) + baf.pack_quat(*R[b][k]) for k in range(n)]
        tracks.append(baf.Track(tk, list(tr.S), rk))
    clip = baf.Clip((n - 1) / FPS, n, tracks, template.skeleton)
    baf.check(clip)
    return clip, {"frames": n, "seconds": round((n - 1) / FPS, 3), "parts": sorted(drive), "scale": round(scale, 4),
                  "loop": bool(loop)}


def _loops(clip: baf.Clip) -> bool:
    """Whether the game plays the clip round and round: its root ends where it starts, with the same turn."""
    s = baf.skeleton(clip.skeleton)
    names = [n.lower() for n in s["names"]]
    if "bip01" not in names:
        return False
    root = clip.tracks[s["index"].index(names.index("bip01"))]
    if len(root.T) < 3:
        return False
    same_turn = abs(sum(a * b for a, b in zip(baf.unpack_quat(root.R[0][1:5]), baf.unpack_quat(root.R[-1][1:5])))) > 0.9999
    return math.dist(root.T[0][1:4], root.T[-1][1:4]) < 0.01 and same_turn


def loops(raw: bytes) -> bool:
    """_loops of a clip's bytes."""
    return _loops(baf.parse(raw))


def _depth(parents, b):
    d = 0
    while parents[b] >= 0:
        b = parents[b]
        d += 1
    return d


def _qconj(q):
    return (-q[0], -q[1], -q[2], q[3])


def _qmul(a, b):
    return baf.qmul(a, b)
