"""The Horse Squad's two models, made on the player's own PC from their own game (the owner, 2026-11-12: "Yes, like
era units": a unit anyone can add, off until a modder adds it, built from their own game when added, credited to
sneadtristen6). Nothing of the game's is in a download: the scenery horse, the US rifleman, the US bazooka man and
their animations are read from the game folder the Studio already uses, and the two .glb files are made from them.

What it makes is the Horse Squad that played and passed in the game (2026-11-11, horse-studio2: "test works  bazooka
there"), the same bytes as the two files that test imported, made the way they were made: the combined model of
2026-11-09 (own-horse10, "works. They shoot. And have different animations"), its .glb of 2026-11-10 and the horse's
fall of 2026-11-11 (FL-105). Four steps:
  1. THE SKELETON, 62 bones (the game takes an animated model of at most 64): the scenery horse's 32 that carry points
     or lead to them, renamed "horse ..." (the horse's bones have a soldier's names), then the rifleman's 30 from the
     hips up under their own names, his root hung on the horse's mid-back bone (SEAT_BONE), SEAT from the horse's
     origin. Bone b is track b.
  2. THE MODELS, in the game's own mesh pack layout: the horse's draw, then the soldier's body from the hips up (a
     point leaning on his legs more than half is dropped) and his weapon; one with the rifleman's rifle, one with the
     bazooka man's launcher; each draw a copy of the game's own material with a bone list of its own.
  3. THE CLIPS, 24: the rider's top half playing each clip the rifle squad's figures list, the horse held at its first
     standing frame (a clip that moves the whole man about, running, walking, routing or crouching, plays his standing
     or aiming pose instead: _top_source); the horse's stand, walk and run, the rider held standing; and the ride (the
     horse running, him standing), played on the long move. His root in a clip is carried onto the horse's back as the
     back is when the horse stands (_seat_in_clips), so he rocks with it when it moves.
  4. THE .glb FILES (_unit_glb, kept as it wrote them on 2026-11-10): each model on its 62 bones with the 24 clips as
     animations, each with the actions the squad's figures give it in its extras, the skeleton record in the asset's
     extras; then the horse's fall (_with_death): a 25th animation, hr_b_mort_balle, keyframed from DEATH_KEYS, and the
     rider's deaths re-based so he falls in the world as he did over the standing horse.
Every sum the files' numbers go through is plain Python in a fixed order (_fma, _mm, _mv3, _dot4, _sin_cos), not
numpy's matrix and dot products (they go to OpenBLAS, whose code is chosen by processor: its dot of four numbers was
fused on the PC that made the passed files and plain on the old PC, and the fall came out different there) nor
Windows' own sin and cos (not rounded to the nearest at 11 of the fall's 284 half-angles on that PC; whether they
differ between processors: not tested). The same bytes on two PCs (an AMD Zen 4, an Intel Coffee Lake); on others
with the same Python (its zlib packs the pictures): not tested.

    horse_squad_glbs(game, out, index=the Studio's game index) -> {"rifle": the riflemen's file, "bazooka": the
    heavy-weapon soldier's}; HorseSquadError when the game can't give what it needs.
"""
from __future__ import annotations

import base64
import functools
import json
import math
import shutil
import sqlite3
import struct
import tempfile
from pathlib import Path

import numpy as np

from . import baf
from .build import DEFAULT_PACK, find_pack
from .dxt import png_bytes
from .edat import Edat
from .gltf import FLOAT, MIRROR, PROPELLER, SCALE, TRACK_ATTRIBUTE, UBYTE, UINT, USHORT, _Glb, _point, _split
from .models import Library, texture_member
from .ndf import Ndf, Value
from .spk import Spk
from .unitmodel import SKINNED_2F, Skeleton, UnitModelError, _index_buffer, _rigged_buffer, pack_names, packs_holding
from .unitpacks import NONE, MeshPack, _copy_materials, _material_list, _subs


class HorseSquadError(ValueError):
    """The player's game can't give what the Horse Squad is made from (said in plain words)."""


# --- what it is made of (the 2026-11-09 build's, each picked by the owner or read from the game then) ---
B = "\\"
FOLDER = B.join(["ww2", "res3d", "units", "us", "infanterie"]) + B
SOLDIER = FOLDER + "us_soldier_modellod0.ase2ndfbin"             # the US rifleman: the rider and his rifle
BAZOOKA = FOLDER + "us_soldier_bazooka_modellod0.ase2ndfbin"     # the US bazooka man: the heavy-weapon rider
HORSE = B.join(["ww2", "res3d", "decors", "animaux", "animaux_1", "horse_standlod0.ase2ndfbin"])  # the scenery horse
NEW = {"rifle": FOLDER + "us_horserider_modellod0.ase2ndfbin",
       "bazooka": FOLDER + "us_horserider_bazooka_modellod0.ase2ndfbin"}   # the two models' names
MESH_PACK = "gen_5\\pack\\gfxdescriptor\\mesh_all.spk"   # the rifleman's pack the .glb files read the models from
CLIP_DIR = "genanim_15" + B + B.join(["ww2", "res3d", "units", "common"]) + B   # where the build puts unit clips
SEAT = (-21.5, 11.3, 70.0)   # forward, sideways, up, in the game's axes: his pick of height 70 (2026-11-09); sideways
#                              puts the rider's hips over the horse's spine (his own clips stand 11 to one side)
SEAT_BONE = "bip01 spine1"   # the horse's mid-back bone, under the saddle
HORSE_DROP = {"bip01 footsteps", "bip01 l toe0nub", "bip01 r toe0nub", "horse"}   # no point leans on them, nothing
#                                                                                    hangs from them
LEGS = {f"bip01 {s} {p}" for s in "lr" for p in ("thigh", "calf", "foot", "toe0")}
RIDER_DROP = LEGS | {"bip01 footsteps", "bip01 xtra01", "soldat"}
HORSE_CLIPS = {"stand": "horse_standlod0.baf", "walk": "horse_walklod0.baf", "run": "horse_runlod0.baf"}
RIDER_STAND = "fusilier_standlod0.baf"   # the rider's pose while the horse's clips play
UNIT = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Leger"   # the US rifle squad, whose figures' listings are read
TOKEN = "GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine"   # its far-zoom figure
LISTED = ("GfxDescriptorFusilier", "GfxDescriptorBazooka", TOKEN)   # the figures whose clips the rider plays
FIGURES = {"rifle": ["GfxDescriptorFusilier"], "bazooka": ["GfxDescriptorBazooka", TOKEN]}   # who drew which model
RIDE = "hr_ride"
RIDE_FIGURE = "Descriptor_Unit_Horse_Ride:GfxDescriptor"   # the 11-09 ride's figure: drew the rifle model, idle1
FILES = {"rifle": "horse-squad-rifle.glb", "bazooka": "horse-squad-bazooka.glb"}
# the names it writes while it works, its own (made_from's scratch folder: tempfile's 8 letters after WORK_PREFIX, a
# folder for each game model in it): short, so a deep folder leaves the most room under Windows' 260 characters (a
# platform folder of 140 characters stopped the Add on 2026-11-12, when they took 120: .making-<8>\horse-squad-<8>\
# bazooka\<the model's pictures' names>); the files it ends with (FILES) are named as before
WORK_PREFIX = "h"
WORK_PARTS = {SOLDIER: "r", BAZOOKA: "b", HORSE: "h"}


def longest_written(out: Path) -> int:
    """The length of the longest path horse_squad_glbs writes into `out` (its scratch folder's random letters
    counted), so a caller can tell before the long part whether Windows will take it."""
    out = Path(out)
    work = out / (WORK_PREFIX + "x" * 8)       # (tempfile.mkdtemp's names: the prefix and 8 letters)
    names = [work / part / (_stem_of(model) + ".glb") for model, part in WORK_PARTS.items()]
    names += [out / f for f in FILES.values()]
    return max(len(str(p)) for p in names)


def horse_squad_glbs(game: Path, out: Path, *, index: Path | None = None, say=print) -> dict:
    """The Horse Squad's two .glb files made from the game at `game` (its folder) into the folder `out` (made when
    missing; FILES's names): {"rifle": the riflemen's horse and rider, "bazooka": the heavy-weapon soldier's}, both on
    the same 62 bones with the same 25 animations, what the Studio's Import model takes (the riflemen's, then the
    other with kind "bazooka"). `index`: the Studio's game index (an SQLite file), for the squad's clip listings;
    None, or one that hasn't them: read from the game's unit data instead (about 2.5 s more). The same game gives the
    same bytes. HorseSquadError, in plain words, when the game can't give what it needs."""
    game, out = Path(game), Path(out)
    made = made_from(game, out, index=index, say=say)
    done = {}
    for variant in NEW:
        done[variant] = out / FILES[variant]
        done[variant].write_bytes(made["files"][variant])
    say(f"Generic Horse: {done['rifle'].name} and {done['bazooka'].name} made")
    return done


def made_from(game: Path, work_in: Path, *, index: Path | None = None, say=print) -> dict:
    """Everything horse_squad_glbs makes, kept in memory, step by step (for checking each against what the game test
    was made with): {"record": the 62-bone skeleton record, "pack": the rifleman's MESH_PACK with the two models in
    it, "clips": {name: clip bytes} (24), "listings": {figure part: [(action, clip stem)]}, "glbs": {variant: the
    .glb before the horse's fall}, "files": {variant: the finished .glb}}. `work_in`: a folder (made when missing) to
    hold a scratch folder of the game's models while they're read; it is removed after."""
    game, work_in = Path(game), Path(work_in)
    if find_pack(game, "ZZ_Win.dat") is None or find_pack(game, DEFAULT_PACK) is None:
        # not a game rule: the builder's own check of what the Horse Squad is made from
        raise HorseSquadError(f"The Generic Horse is made from your game's own files, and {game} isn't a R.U.S.E. game "
                              "folder (ZZ_Win.dat or ZZ_GladPatchableWin.dat isn't in it).")
    say("Generic Horse: reading the horse, the rifleman and the bazooka man from your game")
    listings = _listings(game, index)
    work_in.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=WORK_PREFIX, dir=work_in))
    zz = Edat.open(str(find_pack(game, "ZZ_Win.dat")))
    try:
        table = pack_names(zz)
        held = {m: _holding(zz, m, table) for m in (HORSE, SOLDIER, BAZOOKA)}
        horse_blob, rider_blob, bazooka_blob = (_record_of(*held[m]) for m in (HORSE, SOLDIER, BAZOOKA))
        rb, bb = baf.skeleton(rider_blob), baf.skeleton(bazooka_blob)
        if (rb["names"], rb["parents"]) != (bb["names"], bb["parents"]):
            # not a game rule: the builder's own check of what the Horse Squad is made from
            raise HorseSquadError("Your game's bazooka man isn't on the rifleman's bones: the Generic Horse can't be "
                                  "made from it.")
        bones = _combined(horse_blob, rider_blob)
        blob = baf.skeleton_bytes(bones.names, bones.parents, bones.bind, bones.local, bones.world,
                                  list(range(len(bones.names))))
        _check_record(blob)
        say("Generic Horse: making the models")
        lib = _Few(zz, held, {HORSE: horse_blob, SOLDIER: rider_blob, BAZOOKA: bazooka_blob})
        rifle = _rider_parts(_parts_of(lib, SOLDIER, work / WORK_PARTS[SOLDIER]))
        bazooka = _rider_parts(_parts_of(lib, BAZOOKA, work / WORK_PARTS[BAZOOKA]))
        horse = _horse_parts(_parts_of(lib, HORSE, work / WORK_PARTS[HORSE]))
        mesh_packs = held[SOLDIER][1]
        if sorted(held[BAZOOKA][1]) != sorted(mesh_packs) or MESH_PACK not in mesh_packs:
            # not a game rule: the builder's own check of what the Horse Squad is made from
            raise HorseSquadError("Your game's rifleman and bazooka man aren't in the packs the Generic Horse is made "
                                  "from.")
        plans = {NEW["rifle"]: (SOLDIER, [(p, "horse") for p in horse] + [(p, p.draw) for p in rifle]),
                 NEW["bazooka"]: (BAZOOKA, [(p, "horse") for p in horse] + [(p, p.draw) for p in bazooka])}
        car = _carrier(next(iter(mesh_packs.values())), next(iter(held[HORSE][1].values())), plans, bones.names, blob)
        pack = MeshPack.read(mesh_packs[MESH_PACK])
        for new in NEW.values():
            pack.add(car, new)
        pack_bytes = pack.to_bytes()
        mesh = Spk(pack_bytes)
        say("Generic Horse: making the animations")
        stems = {stem for rows in listings.values() for _key, stem in rows}
        top_of = {stem: _top_source(stem) for stem in sorted(stems)}
        tops = sorted(set(top_of.values()))
        wanted = {t + ".baf" for t in tops} | set(HORSE_CLIPS.values()) | {RIDER_STAND}
        raw = _clip_files(zz, wanted)
        missing = sorted(n for n in wanted if n not in raw)
        if missing:
            # not a game rule: the builder's own check of what the Horse Squad is made from
            raise HorseSquadError(f"Your game hasn't the animations the Generic Horse is made from: "
                                  f"{', '.join(missing)}.")
        maker = _Clips(raw, bones, _seat_in_clips(bones.horse, raw), blob)
        clips, top_names, bottom = {}, {}, {}
        for t in tops:
            short = "hr_t_" + t.replace("fusilier_", "").replace("lod0", "")
            clips[short] = maker.make(HORSE_CLIPS["stand"], t + ".baf", "rider")
            top_names[t] = short
        for key, file in HORSE_CLIPS.items():
            clips["hr_b_" + key] = maker.make(file, RIDER_STAND, "horse")
            bottom[key] = "hr_b_" + key
        clips[RIDE] = maker.make(HORSE_CLIPS["run"], RIDER_STAND, "horse")
        parsed = {name: baf.parse(clips[name]) for name in sorted(clips)}
        say("Generic Horse: making the two files")
        glbs, files, pictures = {}, {}, {}
        for variant, model in NEW.items():
            lib.where[model] = mesh
            rows = _animation_rows(variant, listings, {s: top_names[t] for s, t in top_of.items()}, bottom, parsed)
            glbs[variant] = _unit_glb(lib, model, rows, 1024, blob, pictures, extras={"rusemod_halves": {
                "top": [bones.names[i] for i in sorted(bones.rmap.values())],
                "bottom": [bones.names[i] for i in sorted(bones.hmap.values())]}})
            files[variant] = _with_death(glbs[variant])
        return {"record": blob, "pack": pack_bytes, "clips": clips, "listings": listings, "glbs": glbs,
                "files": files}
    finally:
        zz.close()
        shutil.rmtree(work, ignore_errors=True)


class _Few(Library):
    """A rusemod.models.Library of the three models the Horse Squad is made from alone (the whole one reads every mesh
    pack of the game, about 200 MB more): each model in the first pack of the archive holding its mesh (the one the
    whole library finds it in), its skeleton record as read; the archive `zz` is the caller's, left open."""

    def __init__(self, zz, held: dict, records: dict):
        self.arc = zz
        self.where = {}
        self._skeleton_packs = []
        self._skeletons = {name: records[model] for model, (name, _m, _s) in held.items()}
        read = {}
        for model, (name, meshes, _skels) in held.items():
            path, raw = next(iter(meshes.items()))
            if path not in read:
                read[path] = Spk(raw)
            self.where[name] = read[path]

    def close(self) -> None:
        pass


# --- the squad's listings: which clip each figure plays for each action ---
def _stem(file_name: str) -> str:
    """A listing's clip file as the clips' file names go (WW2\\...\\Fusilier_standlod0.Ase2NdfBin ->
    fusilier_standlod0)."""
    return file_name.replace("/", B).rsplit(B, 1)[-1].lower().replace(".ase2ndfbin", "")


def _listings(game: Path, index: Path | None) -> dict:
    """{figure part (LISTED): [(action, clip stem)] in the figure's order}, from the game index when it has them,
    else from the game's unit data, as the build walks a unit (the two agree on the game: tests/test_horsesquad.py)."""
    if index is not None and Path(index).is_file():
        got = _listings_in_index(Path(index))
        if got is not None:
            return got
    return _listings_in_game(game)


def _listings_in_index(index: Path) -> dict | None:
    try:
        db = sqlite3.connect(index.resolve().as_uri() + "?mode=ro", uri=True)   # (read-only, as rusemod.index opens it)
    except (sqlite3.Error, ValueError, OSError):
        return None
    try:
        out = {}
        for part in LISTED:
            row = db.execute("SELECT id FROM object WHERE address = ? AND shadow = 0", (UNIT + ":" + part,)).fetchone()
            if row is None:
                return None
            rows = []
            for p, d in db.execute("SELECT path, dst FROM ref WHERE src = ? AND path LIKE 'ResourceAnimation[%].v'",
                                   (row[0],)).fetchall():
                key = db.execute("SELECT text FROM value WHERE object = ? AND path = ?",
                                 (row[0], p[:-2] + ".k")).fetchone()
                file = db.execute("SELECT text FROM value WHERE object = ? AND path = 'FileName'", (d,)).fetchone()
                if not key or not file or not key[0] or not file[0]:
                    return None
                rows.append((int(p.split("[", 1)[1].split("]", 1)[0]), key[0], _stem(file[0])))
            out[part] = [(k, s) for _n, k, s in sorted(rows)]
        return out if all(out.values()) else None
    except sqlite3.Error:
        return None
    finally:
        db.close()


def _listings_in_game(game: Path) -> dict:
    from .animmodel import figures_of
    from .build import load_pack
    from .patch import Inline, Ref, Text
    pack = find_pack(game, DEFAULT_PACK)
    arc = Edat.open(str(pack))
    try:
        base = load_pack(arc).base
        figures = dict(figures_of(base, UNIT))
    except (KeyError, ValueError, OSError):
        # (a pack that can't be read is said as that, never as animations the game hasn't; by its file, never in the
        # reader's own English words: the Studio says this in the modder's language, errors.toml)
        # not a game rule: the builder's own check of what the Horse Squad is made from
        raise HorseSquadError(f"Your game's unit data in {pack} couldn't be read, so the Generic Horse can't be made "
                              f"from it.") from None
    finally:
        arc.close()
    out = {}
    for part in LISTED:
        fig = figures.get(part)
        rows = []
        for k, x in (fig.props["ResourceAnimation"].pairs if fig is not None else []):
            a = x.obj if isinstance(x, Inline) else base.objects.get(x.target) if isinstance(x, Ref) else None
            f = a.props.get("FileName") if a is not None else None
            if isinstance(k, Text) and isinstance(f, Text):
                rows.append((k.value, _stem(f.value)))
        if not rows:
            # not a game rule: the builder's own check of what the Horse Squad is made from
            raise HorseSquadError("Your game's US rifle squad hasn't the animations the Generic Horse's riders play.")
        out[part] = rows
    return out


def _top_source(stem: str) -> str:
    """The rifleman's clip the rider's top half plays for a listing naming `stem`: his own, but for the ones that move
    his whole body about (running, walking, routing, crouching), where he holds his standing or aiming pose."""
    n = stem.lower()
    if "course" in n or "marche" in n:
        return "fusilier_bazooka_viselod0" if "bazooka" in n else "fusilier_stand_viselod0" if "vise" in n \
            else "fusilier_standlod0"
    if "deroute" in n or "accroupi" in n:
        return "fusilier_standlod0"
    return n


def _bottom_source(action: str) -> str:
    """The horse's clip a listing that isn't a t_ one plays: walk for marche, run for course and deroute, else stand."""
    return "walk" if "marche" in action else "run" if ("course" in action or "deroute" in action) else "stand"


def _animation_rows(variant: str, listings: dict, top_of: dict, bottom: dict, clips: dict) -> list:
    """The animations of one file, in its order (the clips its figures play, in the order they first list them, then
    the others by name): [(name, clip, extras)], each with the actions and figures that play it."""
    actions, order = {}, []
    for part in FIGURES[variant]:
        for key, stem in listings[part]:
            clip = top_of[stem] if key.startswith("t_") else bottom[_bottom_source(key)]
            names = actions.setdefault(clip, {}).setdefault(part, [])
            if key not in names:
                names.append(key)
            if clip not in order:
                order.append(clip)
    if variant == "rifle":   # the ride drew the riflemen's model, its one action idle1
        actions.setdefault(RIDE, {})[RIDE_FIGURE] = ["idle1"]
        order.append(RIDE)
    rows = []
    for clip in order + sorted(c for c in clips if c not in order):
        figs = actions.get(clip, {})
        half = "whole" if clip == RIDE else "top" if clip.startswith("hr_t_") else "bottom"
        rows.append((clip, clips[clip], {"rusemod_clip": CLIP_DIR + clip + "lod0.baf",
                                         "rusemod_actions": sorted({k for keys in figs.values() for k in keys}),
                                         "rusemod_figures": figs, "rusemod_half": half}))
    return rows


# --- 1. the skeleton ---
def _holding(zz, model: str, table: list) -> tuple:
    """packs_holding's (name, mesh packs, skeleton packs) of `model`, or HorseSquadError."""
    try:
        return packs_holding(zz, model, table)
    except UnitModelError:
        # not a game rule: the builder's own check of what the Horse Squad is made from
        raise HorseSquadError(f"Your game hasn't the model the Generic Horse is made from: {model}.") from None


def _record_of(name: str, _meshes: dict, skels: dict) -> bytes:
    """The model's skeleton record, the same in every skeleton pack holding it."""
    blobs = set()
    for raw in skels.values():
        pack = MeshPack.read(raw)
        blobs.add(pack.skeletons[pack.items[name][2]])
    if len(blobs) != 1:
        # not a game rule: the builder's own check of what the Horse Squad is made from
        raise HorseSquadError(f"Your game's skeleton of {name} isn't one the Generic Horse can be made from "
                              f"({len(blobs)} records).")
    return blobs.pop()


# --- sums in plain Python, in a fixed order ---
# The passed files' numbers were worked out with numpy, which hands a matrix product or a dot product to OpenBLAS,
# whose code is chosen by processor: on the PC that made them (an AMD Zen 4) a dot of four numbers is a chain of fused
# multiply-adds, on the old PC (an Intel Coffee Lake) plain sums (measured: scratch/animmodels/horse-gen/
# numerics_probe.py on both), and the horse's fall came out different there (2026-11-12: 11 numbers near nought in one
# turn, which a 32-bit float keeps). So every sum the files' numbers go through is done here in plain Python, in the
# order and the rounding numpy had on the PC that made them (found by trying every order against it: numerics_probe*.py
# there), and the files came out the same bytes on both PCs.
def _fma(a: float, b: float, c: float) -> float:
    """a x b + c rounded once (a fused multiply-add), worked out exactly in whole numbers."""
    na, da = float(a).as_integer_ratio()
    nb, db = float(b).as_integer_ratio()
    nc, dc = float(c).as_integer_ratio()
    num = na * nb * dc + nc * da * db
    if num:
        return num / (da * db * dc)      # (a whole number over a whole number: rounded once, to the nearest)
    p = a * b
    return p + c if p == 0 and c == 0 else 0.0   # (an exact nought: its sign as a fused multiply-add gives it)


def _mm(a: list, b: list) -> list:
    """4 x 4 times 4 x 4 (lists of rows): each sum fused over k = 0, 1, 2, 3, as numpy's matrix product there."""
    return [[_fma(a[i][3], b[3][j], _fma(a[i][2], b[2][j], _fma(a[i][1], b[1][j], a[i][0] * b[0][j])))
             for j in range(4)] for i in range(4)]


def _mv3(m: list, v) -> list:
    """3 x 3 times a 3-vector, as numpy's product of the two there: element 1, then 0, then 2, fused."""
    return [_fma(m[i][2], v[2], _fma(m[i][0], v[0], m[i][1] * v[1])) for i in range(3)]


def _dot4(a, b) -> float:
    """The dot product of two 4-vectors, as numpy's there: fused over 0, 1, 2, 3."""
    return _fma(a[3], b[3], _fma(a[2], b[2], _fma(a[1], b[1], a[0] * b[0])))


def _inverse(m: list) -> list:
    """The inverse of a 4 x 4 that moves, turns and sizes (its last row 0 0 0 1), from its 3 x 3's cofactors."""
    (a, b, c), (d, e, f), (g, h, i) = m[0][:3], m[1][:3], m[2][:3]
    co = [[e * i - f * h, c * h - b * i, b * f - c * e], [f * g - d * i, a * i - c * g, c * d - a * f],
          [d * h - e * g, b * g - a * h, a * e - b * d]]
    det = (a * co[0][0] + b * co[1][0]) + c * co[2][0]
    inv = [[co[r][k] / det for k in range(3)] for r in range(3)]
    t = [m[0][3], m[1][3], m[2][3]]
    return [inv[r] + [-((inv[r][0] * t[0] + inv[r][1] * t[1]) + inv[r][2] * t[2])] for r in range(3)] + \
        [[0.0, 0.0, 0.0, 1.0]]


def _m4(rows12) -> list:
    """A record's 3 x 4 matrix (rows of [r r r t]) as 4 x 4."""
    v = [float(x) for x in rows12]
    return [v[0:4], v[4:8], v[8:12], [0.0, 0.0, 0.0, 1.0]]


def _rows12(m: list) -> tuple:
    return tuple(float(v) for row in m[:3] for v in row)


def _quat_m(q) -> list:
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def _trs4(move, turn, size) -> list:
    r = _quat_m(turn)
    s = [float(v) for v in size]
    return [[r[i][0] * s[0], r[i][1] * s[1], r[i][2] * s[2], float(move[i])] for i in range(3)] + \
        [[0.0, 0.0, 0.0, 1.0]]


def _posed(clip: baf.Clip, frac: float) -> tuple[dict, list]:
    """(the clip's skeleton, each bone's 4 x 4 matrix in the model at `frac` of the clip): its track's move x turn x
    size up its parents, track u driving bone index[u]."""
    sk = baf.skeleton(clip.skeleton)
    tb = {b: u for u, b in enumerate(sk["index"])}
    out = [None] * sk["bones"]

    def world(b):
        if out[b] is None:
            loc = _trs4(*baf.sample(clip.tracks[tb[b]], frac))
            p = sk["parents"][b]
            out[b] = loc if p < 0 else _mm(world(p), loc)
        return out[b]
    for b in range(sk["bones"]):
        world(b)
    return sk, out


def _horse_name(n: str) -> str:
    return "horse " + (n[6:] if n.startswith("bip01 ") else n)


class _Bones:
    """The combined skeleton: names, parents, the record's three matrix sets (bind: model -> bone, local: from the
    parent, world: bone -> model), the horse's and rider's records read (horse, rider) and where each of their bones
    went ({their bone: its number here}: hmap, rmap)."""

    def __init__(self):
        self.names, self.parents, self.bind, self.local, self.world = [], [], [], [], []
        self.hmap, self.rmap, self.horse, self.rider = {}, {}, None, None


def _combined(horse_blob: bytes, rider_blob: bytes) -> _Bones:
    """The 62 bones: the horse's (HORSE_DROP left out) in its tracks' order, renamed; then the rider's (RIDER_DROP
    left out) in his, his root on the horse's SEAT_BONE, each of his rest poses moved up by SEAT."""
    h, r = baf.skeleton(horse_blob), baf.skeleton(rider_blob)
    T, Ti = _m4((1.0, 0.0, 0.0, SEAT[0], 0.0, 1.0, 0.0, SEAT[1], 0.0, 0.0, 1.0, SEAT[2])), \
        _m4((1.0, 0.0, 0.0, -SEAT[0], 0.0, 1.0, 0.0, -SEAT[1], 0.0, 0.0, 1.0, -SEAT[2]))
    k = _Bones()
    k.horse, k.rider = h, r
    try:
        for b in h["index"]:        # the tracks' order: parents before children
            if h["names"][b] in HORSE_DROP:
                continue
            p = h["parents"][b]
            k.hmap[b] = len(k.names)
            k.names.append(_horse_name(h["names"][b]))
            k.parents.append(k.hmap[p] if p >= 0 else -1)
            k.bind.append(h["bind"][b])
            k.local.append(h["local"][b])
            k.world.append(h["world"][b])
        seat_bone = h["names"].index(SEAT_BONE)
        H0 = _m4(h["bind"][seat_bone])
        for b in r["index"]:
            if r["names"][b] in RIDER_DROP:
                continue
            p = r["parents"][b]
            W = _mm(T, _m4(r["world"][b]))
            k.rmap[b] = len(k.names)
            k.names.append(r["names"][b])
            if p < 0:
                if r["names"][b] != "bip01":
                    # not a game rule: the builder's own check of what the Horse Squad is made from
                    raise HorseSquadError("Your game's rifleman has a second root bone: the Generic Horse can't be made "
                                          "from him.")
                k.parents.append(k.hmap[seat_bone])
                k.local.append(_rows12(_mm(H0, W)))
            else:
                k.parents.append(k.rmap[p])
                k.local.append(r["local"][b])
            k.bind.append(_rows12(_mm(_m4(r["bind"][b]), Ti)))
            k.world.append(_rows12(W))
    except (KeyError, ValueError) as exc:
        if isinstance(exc, HorseSquadError):
            raise
        # not a game rule: the builder's own check of what the Horse Squad is made from
        raise HorseSquadError("Your game's horse or rifleman isn't built as the Generic Horse expects (a bone it rides "
                              "on is missing).") from None
    return k


def _check_record(blob: bytes) -> None:
    """The combined record is one the game takes: at most 64 bones, every parent before its child, every name its
    own, and its three matrix sets keeping the game's relations (bind x world = 1, parent's world x local = world)."""
    sk = baf.skeleton(blob)
    n, parents = sk["bones"], sk["parents"]
    one = _m4((1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0))

    def apart(a, b) -> float:
        return max(abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))
    worst0 = max(apart(_mm(_m4(sk["bind"][b]), _m4(sk["world"][b])), one) for b in range(n))
    worst1 = max(apart(_mm(_m4(sk["world"][parents[b]]) if parents[b] >= 0 else one, _m4(sk["local"][b])),
                       _m4(sk["world"][b])) for b in range(n))
    if n > baf.MOST_BONES or any(p >= b for b, p in enumerate(parents)) or len(set(sk["names"])) != n \
            or worst0 > 1e-3 or worst1 > 1e-2:
        # not a game rule: the builder's own check of what the Horse Squad is made from
        raise HorseSquadError("The Generic Horse's skeleton made from your game isn't one the game takes.")


# --- 2. the models ---
def _parts_of(lib, model: str, folder: Path) -> list:
    """The game model `model` as the importer reads a model rigged to its own bones (the Studio's own export, read
    back: every point on its bones, in the game's axes), each part keeping its draw. Only the .glb is written into
    `folder`, as rusemod.gltf.export names it (its pictures are inside it: the colour and alpha pictures export writes
    beside it, with long names, were never read here)."""
    from .gltf import model_glb
    from .modelin import ModelError, prepare, read_model
    folder.mkdir(parents=True)
    try:
        glb = folder / (_stem_of(model) + ".glb")
        glb.write_bytes(model_glb(lib, model, 64)[0])
        return prepare(read_model(glb, skin=True), folder, {"rigged": True, "root": "bip01"}, 1.0, 64).parts
    except (KeyError, ModelError, StopIteration):
        # not a game rule: the builder's own check of what the Horse Squad is made from
        raise HorseSquadError(f"Your game's model {model} couldn't be read for the Generic Horse.") from None


def _weights(pairs: list) -> list:
    """A point's bones' weights made up to 255 again, the largest taking what rounding leaves."""
    total = sum(w for _n, w in pairs)
    if not total:
        return []
    out = [[n, round(w * 255.0 / total)] for n, w in pairs]
    out[max(range(len(out)), key=lambda k: out[k][1])][1] += 255 - sum(w for _n, w in out)
    return [(n, w) for n, w in out if w > 0]


def _rider_parts(parts: list) -> list:
    """The soldier's draws from the hips up: a triangle with a corner leaning on the legs more than half left out, the
    rest moved up onto the horse (SEAT), their weights on RIDER_DROP bones given to the others."""
    from .modelin import Part
    out = []
    for part in parts:
        if part.static or part.tracks:
            # not a game rule: the builder's own check of what the Horse Squad is made from
            raise HorseSquadError("Your game's soldier has a draw with no bones: the Generic Horse can't be made from "
                                  "it.")
        keep = [sum(w for n, w in pairs if n in LEGS) <= 127 for pairs in part.skin]
        tris = [t for t in part.triangles if all(keep[v] for v in t)]
        used = sorted({v for t in tris for v in t})
        new = {v: k for k, v in enumerate(used)}
        p = Part(part.bone, part.picture, [], [], [], [], skin=[], tracks=None, draw=part.draw, static=False)
        for v in used:
            x, y, z = part.positions[v]
            p.positions.append((x + SEAT[0], y + SEAT[1], z + SEAT[2]))
            p.normals.append(part.normals[v])
            p.uvs.append(part.uvs[v])
            p.skin.append(_weights([(n, w) for n, w in part.skin[v] if n not in RIDER_DROP]) or [("bip01 pelvis", 255)])
        p.triangles = [tuple(new[v] for v in t) for t in tris]
        if p.triangles:
            out.append(p)
    return out


def _horse_parts(parts: list) -> list:
    """The horse's draws, their bones renamed as the combined skeleton names them."""
    from .modelin import Part
    out = []
    for part in parts:
        if part.static or part.tracks:
            # not a game rule: the builder's own check of what the Horse Squad is made from
            raise HorseSquadError("Your game's horse has a draw with no bones: the Generic Horse can't be made from it.")
        skin = []
        for pairs in part.skin:
            if any(n in HORSE_DROP for n, _w in pairs):
                # not a game rule: the builder's own check of what the Horse Squad is made from
                raise HorseSquadError("A point of your game's horse leans on a bone the Generic Horse leaves out.")
            skin.append([(_horse_name(n), w) for n, w in pairs])
        out.append(Part(part.bone, part.picture, list(part.positions), list(part.normals), list(part.uvs),
                        list(part.triangles), skin=skin, tracks=None, draw=part.draw, static=False))
    return out


def _draws_of(pack: MeshPack, name: str) -> list:
    _data, mesh, _skel = pack.items[name]
    first, count = pack.meshes[mesh]
    return [pack.draws[k] for k in range(first, first + count)]


def _carrier(first_raw: bytes, horse_raw: bytes, plans: dict, names: list, blob: bytes) -> MeshPack:
    """A copy of the pack `first_raw` holding the new models: `plans` {new name: (the soldier model it stands beside,
    [(part, "horse" or the soldier's draw number)])}, each draw on a copy of the horse's or that soldier draw's own
    material with its own bone list."""
    car = MeshPack.read(first_raw)
    horse_pack = MeshPack.read(horse_raw)
    horse_mat = _copy_materials(car, horse_pack, [_draws_of(horse_pack, HORSE)[0][1]])[0]
    nd = Ndf(car.materials)
    roots = _material_list(nd)
    bones = Skeleton(names, [], [])
    made: dict = {}

    def material(number: int, bone_list: list) -> int:
        key = (number, tuple(bone_list))
        if key not in made:
            obj = nd.objects[roots[number]]
            props, found = [], False
            for pi, v in obj.props:
                if nd.prop_name(pi) == "SkinningRemapping":
                    kind = _subs(v)[0].tc
                    v = Value(0x11, struct.pack("<I", len(bone_list))
                              + b"".join(Value(kind, struct.pack("<i", b)).encode() for b in bone_list))
                    found = True
                props.append((pi, v))
            if not found:
                # not a game rule: the builder's own check of what the Horse Squad is made from
                raise HorseSquadError("A material of your game's soldier or horse has no bone list.")
            roots.append(nd.add_object(obj.cls, props))
            made[key] = len(roots) - 1
        return made[key]
    if SKINNED_2F.encode() not in [f.split(b"\0", 1)[0] for f in car.formats]:
        car.formats.append(SKINNED_2F.encode().ljust(256, b"\0"))
    new_draws = {}
    for new, (beside, plan) in plans.items():
        data, _mesh, skel = car.items[beside]
        own = [d[1] for d in _draws_of(car, beside)]
        draws, pts = [], []
        for part, role in plan:
            bone_list = sorted({names.index(n) for pairs in part.skin for n, _w in pairs})
            mat = material(horse_mat if role == "horse" else own[role], bone_list)
            vb, kind = _rigged_buffer(part, bone_list, bones)
            vb.kind = [f.split(b"\0", 1)[0] for f in car.formats].index(kind.encode())
            car.vbs.append(vb)
            car.ibs.append(_index_buffer(part))
            draws.append((0, mat, len(car.ibs) - 1, len(car.vbs) - 1, 0xFFFF, 0xCDCD))
            pts += part.positions
        cols = [[p[i] for p in pts] for i in range(3)]
        box = tuple(min(c) - 30.0 for c in cols) + tuple(max(c) + 30.0 for c in cols)
        if skel != NONE:    # (a pack that keeps the skeleton beside the mesh)
            if blob not in car.skeletons:
                car.skeletons.append(blob)
            skel = car.skeletons.index(blob)
        car.items[new] = [struct.pack("<6fI", *box, struct.unpack_from("<I", data, 24)[0]), None, skel]
        new_draws[new] = draws
    root = nd.objects[nd.topo[0]]
    root.props[0] = (root.props[0][0], Value(0x11, struct.pack("<I", len(roots)) + b"".join(
        Value(0x09, struct.pack("<III", 0xBBBBBBBB, n, nd.objects[n].cls)).encode() for n in roots)))
    car.materials = nd.to_logical()
    car.material_count = len(roots)
    car._renumber(new_draws)
    return car


# --- 3. the clips ---
def _clip_files(zz, names: set) -> dict:
    """{file name: its bytes} of the clips named (lower case, with .baf), loose in ZZ_Win.dat or in its .apk
    archives, the first found of each in the archive's order."""
    out = {}
    for e in zz.entries:
        if len(out) == len(names):
            break
        p = e.path.lower()
        t = p.rsplit(B, 1)[-1]
        if p.endswith(".baf") and t in names:
            out.setdefault(t, bytes(zz.read(e)))
        elif p.endswith(".apk"):
            arc = Edat(bytes(zz.read(e)))
            for x in arc.entries:
                t = x.path.lower().rsplit(B, 1)[-1]
                if t in names:
                    out.setdefault(t, bytes(arc.read(x)))
    return out


def _mat_quat(R: list) -> tuple:
    """The turn (x, y, z, w) of a 3 x 3 turn (rows)."""
    t = (R[0][0] + R[1][1]) + R[2][2]          # (numpy's trace: the same order)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return ((R[2][1] - R[1][2]) / s, (R[0][2] - R[2][0]) / s, (R[1][0] - R[0][1]) / s, 0.25 * s)
    i = max(range(3), key=lambda n: R[n][n])    # (the first of the largest, as numpy's argmax)
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1.0 + R[i][i] - R[j][j] - R[k][k]) * 2
    q = [0.0, 0.0, 0.0, 0.0]
    q[i] = 0.25 * s
    q[j] = (R[j][i] + R[i][j]) / s
    q[k] = (R[k][i] + R[i][k]) / s
    q[3] = (R[k][j] - R[j][k]) / s
    return tuple(q)


def _held(mv, tn, sz) -> baf.Track:
    """A track holding one pose all along."""
    return baf.Track(T=[(0, float(mv[0]), float(mv[1]), float(mv[2]))],
                     S=[(0, float(sz[0]), float(sz[1]), float(sz[2]))], R=[(0, *baf.pack_quat(*tn))])


def _seat_in_clips(h: dict, raw: dict) -> list:
    """The rider's root in the clips, from the horse's mid-back bone (4 x 4): against that bone as it is when the horse
    STANDS (its stand clip's first frame), so he sits upright on a standing horse and rocks with its back when it
    moves; the same gap between his hips and that bone as in the model, drawn on the horse at rest."""
    seat_bone = h["names"].index(SEAT_BONE)
    _hs, stand_w = _posed(baf.parse(raw[HORSE_CLIPS["stand"]]), 0.0)
    rest = _m4(h["world"][seat_bone])
    gap = [(SEAT[i] + stand_w[seat_bone][i][3]) - rest[i][3] for i in range(3)]
    return _mm(_inverse(stand_w[seat_bone]), _m4((1.0, 0.0, 0.0, gap[0], 0.0, 1.0, 0.0, gap[1], 0.0, 0.0, 1.0, gap[2])))


class _Clips:
    """The combined clips: the horse's bones from one of its clips, the rider's from one of his."""

    def __init__(self, raw: dict, bones: _Bones, A: list, blob: bytes):
        self.raw, self.bones, self.blob = raw, bones, blob
        self.Ra, self.ta = [[float(v) for v in row[:3]] for row in A[:3]], [float(A[i][3]) for i in range(3)]
        self.qa = _mat_quat(self.Ra)
        back = _quat_m(self.qa)
        if max(abs(back[i][j] - self.Ra[i][j]) for i in range(3) for j in range(3)) > 1e-5:
            # not a game rule: the builder's own check of what the Horse Squad is made from
            raise HorseSquadError("The Generic Horse's seat on your game's horse doesn't read back.")
        self.order = sorted([("h", b, n) for b, n in bones.hmap.items()] + [("r", b, n) for b, n in bones.rmap.items()],
                            key=lambda x: x[2])

    @staticmethod
    def _by_name(clip: baf.Clip) -> dict:
        sk = baf.skeleton(clip.skeleton)
        return {sk["names"][b].lower(): clip.tracks[u] for u, b in enumerate(sk["index"])}

    def root(self, t: baf.Track) -> baf.Track:
        """The rider's root track, carried from the model's space onto the horse's mid-back bone."""
        T = [(k[0], *(v + d for v, d in zip(_mv3(self.Ra, k[1:4]), self.ta))) for k in t.T]
        R = [(k[0], *baf.pack_quat(*baf.qmul(self.qa, baf.unpack_quat(k[1:5])))) for k in t.R]
        return baf.Track(T=T, S=list(t.S), R=R)

    def rider_tracks(self, clip: baf.Clip, hold: bool) -> dict:
        by = self._by_name(clip)
        out = {}
        for b in self.bones.rmap:
            name = self.bones.rider["names"][b]
            if name not in by:
                # not a game rule: the builder's own check of what the Horse Squad is made from
                raise HorseSquadError(f"A clip of your game's rifleman hasn't his bone {name}.")
            t = self.root(by[name]) if name == "bip01" else by[name]
            out[b] = _held(*baf.sample(t, 0.0)) if hold else t
        return out

    def horse_tracks(self, clip: baf.Clip, hold: bool) -> dict:
        by = self._by_name(clip)
        out = {}
        for b in self.bones.hmap:
            name = self.bones.horse["names"][b]
            if name not in by:
                # not a game rule: the builder's own check of what the Horse Squad is made from
                raise HorseSquadError(f"A clip of your game's horse hasn't its bone {name}.")
            out[b] = _held(*baf.sample(by[name], 0.0)) if hold else by[name]
        return out

    def make(self, horse: str, rider: str, lead: str) -> bytes:
        """A combined clip: the horse's bones from `horse`, the rider's from `rider`; `lead` ("horse" or "rider")
        says whose clip sets the length, the other's bones held at its first frame."""
        hc, rc = baf.parse(self.raw[horse]), baf.parse(self.raw[rider])
        ht, rt = self.horse_tracks(hc, lead != "horse"), self.rider_tracks(rc, lead != "rider")
        src = hc if lead == "horse" else rc
        tracks = [ht[b] if kind == "h" else rt[b] for kind, b, _n in self.order]
        out = baf.build(baf.Clip(src.duration, src.frames, tracks, self.blob))
        back = baf.parse(out)
        if back.bones != len(self.bones.names) or baf.skeleton(back.skeleton)["names"] != self.bones.names:
            # not a game rule: the builder's own check of what the Horse Squad is made from
            raise HorseSquadError("A Generic Horse animation made from your game doesn't read back.")
        return out


# --- 4. the .glb: the models on their bones with their animations, laid out as written on 2026-11-10 ---
# (Kept here as it was, so the files are the bytes the game test passed with: the record in the asset's extras
# (rusemod_skeleton, base64); every bone a node at its rest pose from its parent under "<model>_rig"; JOINTS_0 the
# skeleton's own bone numbers; a bone the game sizes or mirrors at rest (_frame: the horse's bone04 and bone05) a
# plain turn in the file with its sizes in its node's extras (rusemod_rest_size) and moved into its keys
# (_sized_keys); each animation a clip's keys at their own times, LINEAR, a turn through the mirror exactly.)
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


def _rows(m):
    return [list(m[0:4]), list(m[4:8]), list(m[8:12])]


def _det3(r) -> float:
    return (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1]) - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
            + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))


def _trs(m):
    """A 3 x 4 (the game's) -> glTF move, turn, size after the mirror; a mirroring one gets a negative x size."""
    m = _rows(m)
    r = _mirror3([row[:3] for row in m])
    t = _point(m[0][3], m[1][3], m[2][3])
    s = [math.sqrt(sum(r[i][j] ** 2 for i in range(3))) or 1.0 for j in range(3)]
    if _det3(r) < 0:
        s[0] = -s[0]
    rot = [[r[i][j] / s[j] for j in range(3)] for i in range(3)]
    return list(t), list(_m_to_q(rot)), s


def _turn_mirrored(q) -> tuple:
    """A clip's turn (x, y, z, w) through the export's mirror, exactly and keeping its sign."""
    x, y, z, w = q
    return (-x, -z, -y, w)


PURE = 1e-4   # a rest pose whose axes are this close to length one and square to each other is a plain turn


def _frame(world) -> tuple | None:
    """A bone's rest pose in the model (12 numbers) as Blender can hold it: None when it is a plain turn and move
    already; else (F, k): F the nearest plain turn at the bone's place (3 rows of 4), k its sizes along F's axes
    (k[0] below 0 when it mirrors)."""
    m = _rows(world)
    cols = [[m[i][j] for i in range(3)] for j in range(3)]
    norms = [math.sqrt(sum(c * c for c in col)) for col in cols]
    dots = [sum(a * b for a, b in zip(cols[i], cols[j])) for i, j in ((0, 1), (0, 2), (1, 2))]
    det = _det3([row[:3] for row in m])
    if det > 0 and max(abs(n - 1.0) for n in norms) < PURE and max(abs(d) for d in dots) < PURE:
        return None
    if min(norms) < 1e-9:
        return None
    axes = []
    for col in cols:   # Gram-Schmidt, x first
        v = list(col)
        for u in axes:
            d = sum(a * b for a, b in zip(v, u))
            v = [a - d * b for a, b in zip(v, u)]
        n = math.sqrt(sum(a * a for a in v)) or 1.0
        axes.append([a / n for a in v])
    if det < 0:
        axes[0] = [-a for a in axes[0]]
    f = [[axes[j][i] for j in range(3)] + [m[i][3]] for i in range(3)]
    k = [sum(axes[j][i] * cols[j][i] for i in range(3)) for j in range(3)]
    return f, k


def _inverse_rigid(f) -> list:
    rt = [[f[j][i] for j in range(3)] for i in range(3)]
    return [rt[i] + [-sum(rt[i][j] * f[j][3] for j in range(3))] for i in range(3)]


def _compose(a, b) -> list:
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            + [sum(a[i][k] * b[k][3] for k in range(3)) + a[i][3]] for i in range(3)]


def _flat(m) -> tuple:
    return tuple(v for row in m for v in row)


def _ibm(m):
    """A 3 x 4 (the game's, model -> bone) -> glTF column-major 4 x 4 after the mirror."""
    m = _rows(m)
    r = _mirror3([row[:3] for row in m])
    t = _point(m[0][3], m[1][3], m[2][3])
    return [r[0][0], r[1][0], r[2][0], 0.0, r[0][1], r[1][1], r[2][1], 0.0,
            r[0][2], r[1][2], r[2][2], 0.0, t[0], t[1], t[2], 1.0]


def _sized_keys(path: str, keys: list, fix) -> list:
    """A track's keys for a bone whose frame or whose parent's is a plain turn in place of the game's sized one:
    `fix` (kp, kb), the parent's sizes and the bone's own; None: the keys as they are."""
    if fix is None:
        return [tuple(k[1:4]) if path != "rotation" else baf.unpack_quat(k[1:5]) for k in keys]
    kp, kb = fix
    if path == "translation":
        return [tuple(k[1 + i] * kp[i] for i in range(3)) for k in keys]
    if path == "scale":
        return [tuple(kp[i] * k[1 + i] / kb[i] for i in range(3)) for k in keys]
    d = [1.0 if v >= 0 else -1.0 for v in kp]
    det = d[0] * d[1] * d[2]
    out = []
    for k in keys:
        x, y, z, w = baf.unpack_quat(k[1:5])
        out.append((det * d[0] * x, det * d[1] * y, det * d[2] * z, w))
    return out


def _animation(g: _Glb, sk: dict, first: int, name: str, clip: baf.Clip, extras: dict, fix: list | None) -> None:
    """One clip as an animation of the file: a translation, rotation and scale channel on each bone it names."""
    csk = baf.skeleton(clip.skeleton)
    dur = clip.duration if clip.frames > 1 and clip.duration > 0 else 1 / 30
    by_name = {n.lower(): i for i, n in enumerate(sk["names"])}
    samplers, channels = [], []
    for u, track in enumerate(clip.tracks):
        bone = csk["names"][csk["index"][u]]
        b = by_name.get(bone.lower())
        if b is None:
            continue
        for path, keys in (("translation", track.T), ("rotation", track.R), ("scale", track.S)):
            times = [k[0] for k in keys]
            if len(keys) > 2 and any(t1 <= t0 for t0, t1 in zip(times, times[1:])):
                raise HorseSquadError(f"{name}: two keys of bone {bone} at one moment can't be written as an "
                                      "animation.")
            ts = [0.0, dur] if len(keys) <= 2 else [t / baf.LAST_TIME * dur for t in times]
            got = _sized_keys(path, keys, fix[b] if fix else None)
            if path == "translation":
                vals = [_point(*v) for v in got]
            elif path == "scale":
                vals = [(v[0], v[2], v[1]) for v in got]
            else:
                vals = [_turn_mirrored(v) for v in got]
                for k in range(1, len(vals)):   # neighbours on the same side: no spin through a whole turn
                    if sum(x * y for x, y in zip(vals[k], vals[k - 1])) < 0:
                        vals[k] = tuple(-x for x in vals[k])
            if len(keys) == 1:
                vals = vals * 2
            tin = g.accessor(ts, "SCALAR", FLOAT, target=None)
            g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(ts)], [max(ts)]
            tout = g.accessor([tuple(v) for v in vals], "VEC4" if path == "rotation" else "VEC3", FLOAT, target=None)
            samplers.append({"input": tin, "output": tout, "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": first + b, "path": path}})
    g.doc.setdefault("animations", []).append({
        "name": name, "samplers": samplers, "channels": channels,
        "extras": {**extras, "rusemod_seconds": clip.duration, "rusemod_frames": clip.frames}})


def _stem_of(name: str) -> str:
    return name.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", "").replace(".ase2ndfbin", "")


def _skeleton_bone(mats: list, part, local: int) -> int:
    remap = mats[part.material].get("skinning") if part.material < len(mats) else None
    return remap[local] if remap and local < len(remap) else local


def _model_mesh(g: _Glb, lib, name: str, mats: list, parts: list, side: int, joint_of: dict | None,
                pictures: dict) -> list:
    """Model `name`'s pictures, materials and draws written into `g` as rusemod.gltf writes a model's, a node for each
    of its meshes added to g's nodes; returns those nodes. `pictures`: {(texture, side): its colour as a PNG, or
    None}, filled as they're made (the two files share theirs, and a unit picture takes seconds to read)."""
    stem = _stem_of(name)
    texture_of: dict[str, int] = {}
    for _part, tex in parts:
        if tex is None or tex in texture_of:
            continue
        if (tex, side) not in pictures:
            pic = lib.picture(tex, most=side)
            if pic is not None:
                w, h, rgba = pic
                colour, _grey = _split(rgba)
                pic = png_bytes(colour, w, h)
            pictures[(tex, side)] = pic
        png = pictures[(tex, side)]
        if png is None:
            continue
        tname = tex.rsplit("\\", 1)[-1].rsplit(".", 1)[0]
        texture_of[tex] = g.image(png, tname)
        g.doc["materials"].append({"name": tname, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": texture_of[tex]}, "metallicFactor": 0.0, "roughnessFactor": 0.8},
            "doubleSided": True, "extras": {"rusemod_texture": texture_member(tex)}})
        texture_of[tex] = len(g.doc["materials"]) - 1
    skinned = joint_of is not None
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
                js.append(tuple(joint_of[_skeleton_bone(mats, part, x)] if wx else 0 for x, wx in zip(b, w)))
                ws.append(tuple(wx / total for wx in w))
            attrs["JOINTS_0"] = g.accessor(js, "VEC4", USHORT)
            attrs["WEIGHTS_0"] = g.accessor(ws, "VEC4", FLOAT)
        if part.tracks:
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
    mesh_nodes = []
    for mesh_name, prims in ((stem, primitives), (f"{stem}_propeller", propellers)):
        if prims:
            g.doc["meshes"].append({"name": mesh_name, "primitives": prims})
            mesh_nodes.append({"name": mesh_name, "mesh": len(g.doc["meshes"]) - 1})
    g.doc["nodes"] += mesh_nodes
    return mesh_nodes


def _unit_glb(lib, model: str, clips: list, side: int, record: bytes, pictures: dict, extras: dict) -> bytes:
    """`model` (a name `lib` knows) on the skeleton `record` with every clip of `clips` ([(name, a baf.Clip, its
    extras)]) as an animation of the file, the record and `extras` in the asset's extras; `pictures`: _model_mesh's."""
    sk = baf.skeleton(record)
    nb = sk["bones"]
    mats = lib.where[model].materials()
    parts = lib.parts(model)
    for part, _tex in parts:
        for b, w in zip(part.bones, part.weights):
            if any(_skeleton_bone(mats, part, i) >= nb for i, x in zip(b, w) if x):
                raise HorseSquadError(f"{model}: its points lean on a bone its skeleton hasn't got.")
    g = _Glb()
    stem = _stem_of(model)
    skinned = any(part.bones for part, _t in parts)
    mesh_nodes = _model_mesh(g, lib, model, mats, parts, side, {b: b for b in range(nb)} if skinned else None,
                             pictures)
    frames = [_frame(sk["world"][b]) for b in range(nb)]
    frame = [f[0] if f else _rows(sk["world"][b]) for b, f in enumerate(frames)]
    unit = (1.0, 1.0, 1.0)
    fix = [None if frames[b] is None and (p < 0 or frames[p] is None)
           else (frames[p][1] if p >= 0 and frames[p] else unit, frames[b][1] if frames[b] else unit)
           for b, p in enumerate(sk["parents"])]
    first = len(g.doc["nodes"])
    for b, p in enumerate(sk["parents"]):
        if fix[b] is None:
            t, r, s = _trs(sk["local"][b])          # the record's own rest pose
        else:
            t, r, s = _trs(_flat(frame[b] if p < 0 else _compose(_inverse_rigid(frame[p]), frame[b])))
        node = {"name": sk["names"][b], "translation": t, "rotation": r, "scale": s}
        if frames[b] is not None:
            node["extras"] = {"rusemod_rest_size": list(frames[b][1])}
        g.doc["nodes"].append(node)
    for b, p in enumerate(sk["parents"]):
        if p >= 0:
            g.doc["nodes"][first + p].setdefault("children", []).append(first + b)
    rig = len(g.doc["nodes"])
    g.doc["nodes"].append({"name": f"{stem}_rig",
                           "children": [first + b for b, p in enumerate(sk["parents"]) if p < 0]})
    if skinned:
        ibm = []
        for b in range(nb):
            ibm += _ibm(sk["bind"][b] if frames[b] is None else _flat(_inverse_rigid(frame[b])))
        g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(ibm)}f", *ibm)), "componentType": FLOAT,
                                   "count": nb, "type": "MAT4"})
        g.doc["skins"] = [{"name": f"{stem}_skin", "joints": list(range(first, first + nb)),
                           "inverseBindMatrices": len(g.doc["accessors"]) - 1, "skeleton": rig}]
        for node in mesh_nodes:
            node["skin"] = 0
    g.doc["scenes"] = [{"name": stem, "nodes": list(range(len(mesh_nodes))) + [rig]}]
    g.doc["scene"] = 0
    for name, clip, more in clips:
        _animation(g, sk, first, name, clip, more, fix)
    g.doc["asset"]["extras"] = {"rusemod_model": model, "rusemod_scale": SCALE, "rusemod_mirror": MIRROR,
                                "rusemod_skeleton": base64.b64encode(record).decode("ascii"), **extras}
    return g.to_bytes()


# --- the horse's fall (FL-105, the owner 2026-11-11: "The horse should fall over and die too") ---
# The game has no horse death (its only horse, a scenery animal, has stand, walk and run): this one is keyframed from
# the numbers below. Each keyed bone turns by an angle about the model's sideways axis taken into the bone's own frame
# at the standing pose (hr_b_stand's first frame), so a knee folds however the bone is set up; the hips also roll
# about the forward axis and drop toward the ground. 61 frames at 30 a second, each key a smooth step to the next.
DEATH = "hr_b_mort_balle"   # every death of the line falls back to it (the Studio's action rule)
DEATH_FPS, DEATH_FRAMES = 30, 61
_X, _Z = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)


def _legs(fore, upper, thigh, calf, link, neck, neck1, tail=0.0) -> dict:
    return {"horse l forearm": fore, "horse r forearm": fore, "horse l upperarm": upper, "horse r upperarm": upper,
            "horse l thigh": thigh, "horse r thigh": thigh, "horse l calf": calf, "horse r calf": calf,
            "horse l horselink": link, "horse r horselink": link, "horse neck": neck, "horse neck1": neck1,
            "horse tail": tail}


# (frame, roll degrees about the forward axis, the hips' height or None for standing, bends in degrees about the
# sideways axis): tuned 2026-11-11 so no leg goes under the ground mid-roll (the first try's steady drop put them 0.3
# under); the hips stay higher while the body turns over.
DEATH_KEYS = [
    (0, 0.0, None, _legs(0, 0, 0, 0, 0, 0, 0)),
    (10, 0.0, 1.45, _legs(-70, 15, 0, -25, 40, -15, -5)),
    (20, 10.0, 1.00, _legs(-115, 30, 15, -55, 80, -25, -10)),
    (28, 45.0, 0.80, _legs(-110, 30, 15, -55, 75, -20, -10, 5)),
    (36, 80.0, 0.42, _legs(-70, 20, 10, -40, 50, -10, -10, 10)),
    (46, 88.0, 0.34, _legs(-40, 10, 5, -20, 25, -5, -10, 15)),
    (60, 88.0, 0.34, _legs(-40, 10, 5, -20, 25, -5, -10, 15)),
]
RIDER_ROOT = "bip01"        # the rider's root, on the horse's back: his deaths are re-based
RIDER_DEATHS = "hr_t_mort"  # the rider's death animations: every one whose name starts so


def _q_mul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


def _q_inv(q):
    return np.array([-q[0], -q[1], -q[2], q[3]]) / _dot4(q, q)


@functools.lru_cache(maxsize=4096)
def _sin_cos(h: float) -> tuple:
    """(sin h, cos h), each summed to 60 digits (its series) and rounded once to the nearest. Windows' own sin and cos
    (math.sin) aren't always the nearest: on the PC that made the passed files 11 of the fall's 284 half-angles came
    out one step off (scratch/animmodels/horse-gen/sincos_check.py), and the files are the same bytes all the same
    (checked on two PCs); whether Windows' own differ between processors: not tested."""
    if h == 0:
        return h, 1.0
    from decimal import Decimal, localcontext
    with localcontext() as ctx:
        ctx.prec = 60
        x, term, k = Decimal(h), Decimal(1), 0
        s = c = Decimal(0)
        tiny = Decimal(10) ** -58
        while abs(term) >= tiny or k < 2:     # term = h^k / k!
            if k % 4 == 0:
                c += term
            elif k % 4 == 1:
                s += term
            elif k % 4 == 2:
                c -= term
            else:
                s -= term
            k += 1
            term = term * x / k
        return float(s), float(c)


def _q_axis(axis, deg):
    """The turn by `deg` degrees about the unit axis `axis` (x, y, z, w)."""
    h = math.radians(deg) / 2
    s, c = _sin_cos(h)
    return np.array([axis[0] * s, axis[1] * s, axis[2] * s, c])


def _q_rot(q, v):
    p = np.array([v[0], v[1], v[2], 0.0])
    return _q_mul(_q_mul(q, p), _q_inv(q))[:3]


def _smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def _with_death(raw: bytes) -> bytes:
    """The .glb `raw` with the horse's fall added (DEATH, on the horse's bones and hips) and the rider's deaths
    re-based: his root's place and turn at each frame, over the horse standing, taken into the horse's back as it is at
    the same moment of its fall (its last pose held after its 2 s), so he falls in the world as he did on a standing
    horse. The new data goes after the binary's (4-byte aligned); the samplers the re-based channels used stay, unused,
    so every other byte is as it was."""
    n = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + n])
    off = 20 + n
    bl = struct.unpack_from("<I", raw, off)[0]
    binary = bytearray(raw[off + 8:off + 8 + bl])
    before = bytes(binary)    # (what the file's own accessors read: appending never changes it)
    if any(a.get("name") == DEATH for a in doc.get("animations", [])):
        raise HorseSquadError(f"The Generic Horse's file has {DEATH} already.")
    nodes = doc["nodes"]
    parent = {c: i for i, nd in enumerate(nodes) for c in nd.get("children", [])}
    by_name = {nd.get("name"): i for i, nd in enumerate(nodes)}
    read: dict = {}

    def acc(i):
        if i not in read:
            a = doc["accessors"][i]
            bv = doc["bufferViews"][a["bufferView"]]
            nc = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]
            o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
            read[i] = np.frombuffer(before, dtype="f4", count=a["count"] * nc, offset=o).reshape(a["count"], nc)
        return read[i]

    stand = next((a for a in doc["animations"] if a["name"] == "hr_b_stand"), None)
    if stand is None or "horse bip01" not in by_name:
        raise HorseSquadError("The Generic Horse's file hasn't the horse's standing animation or its hips.")
    base_r = {i: np.array(nd.get("rotation", [0, 0, 0, 1]), float) for i, nd in enumerate(nodes)}
    base_t = {i: np.array(nd.get("translation", [0, 0, 0]), float) for i, nd in enumerate(nodes)}
    for ch in stand["channels"]:
        v = acc(stand["samplers"][ch["sampler"]]["output"])[0]
        if ch["target"]["path"] == "rotation":
            base_r[ch["target"]["node"]] = np.array(v, float)
        elif ch["target"]["path"] == "translation":
            base_t[ch["target"]["node"]] = np.array(v, float)
    world = {}

    def w(i):
        if i not in world:
            world[i] = _q_mul(w(parent[i]), base_r[i]) if i in parent else base_r[i]
        return world[i]
    hips = by_name["horse bip01"]
    if parent.get(hips) is not None and nodes[parent[hips]].get("rotation"):
        raise HorseSquadError("The horse's hips in the Generic Horse's file hang from a turned node.")
    start_y = float(base_t[hips][1])
    bones = sorted({b for _f, _r, _d, keyed in DEATH_KEYS for b in keyed})
    if any(b not in by_name for b in bones):
        raise HorseSquadError("The Generic Horse's file hasn't every bone of the horse.")

    def at(frame: int):
        """(roll, the hips' height, {bone: degrees}) at `frame`, each a smooth step between its keys."""
        for (f0, r0, h0, k0), (f1, r1, h1, k1) in zip(DEATH_KEYS, DEATH_KEYS[1:]):
            if f0 <= frame <= f1:
                u = _smooth((frame - f0) / (f1 - f0))
                h0 = start_y if h0 is None else h0
                h1 = start_y if h1 is None else h1
                bend = {b: k0.get(b, 0.0) + (k1.get(b, 0.0) - k0.get(b, 0.0)) * u for b in bones}
                return r0 + (r1 - r0) * u, h0 + (h1 - h0) * u, bend
        last = DEATH_KEYS[-1]
        return last[1], start_y if last[2] is None else last[2], {b: last[3].get(b, 0.0) for b in bones}

    rot = {b: [] for b in bones + ["horse bip01"]}
    hips_t = []
    for f in range(DEATH_FRAMES):
        roll, height, bend = at(f)
        rot["horse bip01"].append(_q_mul(_q_axis(_X, roll), base_r[hips]))
        hips_t.append(np.array([base_t[hips][0], height, base_t[hips][2]]))
        for b in bones:
            i = by_name[b]
            wb = w(i)   # the bone's standing world turn: the world's sideways axis taken into the bone's own frame
            delta = _q_mul(_q_mul(_q_inv(wb), _q_axis(_Z, bend[b])), wb)
            rot[b].append(_q_mul(base_r[i], delta))
    accessors, views = doc["accessors"], doc["bufferViews"]

    def add(arr: np.ndarray, kind: str, minmax: bool = False) -> int:
        while len(binary) % 4:
            binary.append(0)
        data = np.asarray(arr, dtype="<f4").tobytes()
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data)})
        binary.extend(data)
        a = {"bufferView": len(views) - 1, "componentType": 5126, "count": int(len(arr)), "type": kind}
        if minmax:
            a["min"], a["max"] = [float(np.min(arr))], [float(np.max(arr))]
        accessors.append(a)
        return len(accessors) - 1
    times = add(np.arange(DEATH_FRAMES, dtype=float).reshape(DEATH_FRAMES, 1) / DEATH_FPS, "SCALAR", minmax=True)
    samplers, channels = [], []
    for b, qs in rot.items():
        samplers.append({"input": times, "output": add(np.array(qs), "VEC4"), "interpolation": "LINEAR"})
        channels.append({"sampler": len(samplers) - 1, "target": {"node": by_name[b], "path": "rotation"}})
    samplers.append({"input": times, "output": add(np.array(hips_t), "VEC3"), "interpolation": "LINEAR"})
    channels.append({"sampler": len(samplers) - 1, "target": {"node": hips, "path": "translation"}})
    doc["animations"].append({"name": DEATH, "samplers": samplers, "channels": channels})

    # the rider's deaths re-based (they were made for a standing horse: with its back rolling onto its side his fall
    # would turn with it and go into the ground)
    rider = by_name.get(RIDER_ROOT)
    if rider is None or rider not in parent:
        raise HorseSquadError("The Generic Horse's file hasn't the rider on the horse's back.")
    chain = []
    k = parent[rider]
    while k in by_name.values() and (nodes[k].get("name") or "").startswith("horse"):
        chain.append(k)
        k = parent.get(k)
        if k is None:
            break
    chain.reverse()   # (from the horse's hips down to the bone the rider sits on)
    if any(abs(s - 1.0) > 1e-6 for k in chain for s in nodes[k].get("scale", [1, 1, 1])):
        raise HorseSquadError("A bone under the rider in the Generic Horse's file is sized.")

    def back_world(rots: dict, trans: dict):
        """(turn, place) of the bone the rider sits on, the hips' parent being the model's own root."""
        r, p = np.array([0, 0, 0, 1.0]), np.zeros(3)
        for k in chain:
            p = p + _q_rot(r, trans.get(k, base_t[k]))
            r = _q_mul(r, rots.get(k, base_r[k]))
        return r, p
    stand_back = back_world({}, {})
    fall_backs = []
    for f in range(DEATH_FRAMES):
        rots = {by_name[b]: rot[b][f] for b in rot}
        fall_backs.append(back_world(rots, {hips: hips_t[f]}))

    def sample(s, t):
        """A sampler's value at time t: straight lines between keys (turns the short way, renormalised)."""
        ts = acc(s["input"])[:, 0]
        vs = acc(s["output"])
        if t <= ts[0]:
            return np.array(vs[0], float)
        if t >= ts[-1]:
            return np.array(vs[-1], float)
        i = int(np.searchsorted(ts, t)) - 1
        u = (t - ts[i]) / (ts[i + 1] - ts[i])
        a, b = np.array(vs[i], float), np.array(vs[i + 1], float)
        if len(a) == 4:
            if _dot4(a, b) < 0:
                b = -b
            q = a + (b - a) * u
            return q / math.sqrt(_dot4(q, q))     # (numpy's length of q: the root of its dot product)
        return a + (b - a) * u
    for anim in doc["animations"]:
        if not anim["name"].startswith(RIDER_DEATHS):
            continue
        ch = {c["target"]["path"]: c for c in anim["channels"] if c["target"]["node"] == rider}
        if "rotation" not in ch or "translation" not in ch:
            continue
        rs, ts_ = anim["samplers"][ch["rotation"]["sampler"]], anim["samplers"][ch["translation"]["sampler"]]
        end = max(float(acc(rs["input"])[-1, 0]), float(acc(ts_["input"])[-1, 0]))
        frames = int(round(end * DEATH_FPS)) + 1
        new_r, new_t = [], []
        for f in range(frames):
            lr, lt = sample(rs, f / DEATH_FPS), sample(ts_, f / DEATH_FPS)
            wr = _q_mul(stand_back[0], lr)                    # where he is in the world over the standing horse ...
            wp = stand_back[1] + _q_rot(stand_back[0], lt)
            br, bp = fall_backs[min(f, DEATH_FRAMES - 1)]     # ... taken into the falling horse's back then
            inv = _q_inv(br)
            new_r.append(_q_mul(inv, wr))
            new_t.append(_q_rot(inv, wp - bp))
        tk = add(np.arange(frames, dtype=float).reshape(frames, 1) / DEATH_FPS, "SCALAR", minmax=True)
        anim["samplers"].append({"input": tk, "output": add(np.array(new_r), "VEC4"), "interpolation": "LINEAR"})
        ch["rotation"]["sampler"] = len(anim["samplers"]) - 1
        anim["samplers"].append({"input": tk, "output": add(np.array(new_t), "VEC3"), "interpolation": "LINEAR"})
        ch["translation"]["sampler"] = len(anim["samplers"]) - 1
    while len(binary) % 4:
        binary.append(0)
    doc["buffers"][0]["byteLength"] = len(binary)
    text = json.dumps(doc, separators=(",", ":")).encode("utf-8")
    text += b" " * (-len(text) % 4)
    body = (struct.pack("<II", len(text), 0x4E4F534A) + text + struct.pack("<II", len(binary), 0x004E4942)
            + bytes(binary))
    rest = raw[off + 8 + bl:]   # (any chunk after the binary, kept as it was)
    return struct.pack("<III", 0x46546C67, 2, 12 + len(body) + len(rest)) + body + rest
