"""Every animation clip the game has, as RUSE Decoy lists them: the 351 clips of ZZ_Win.dat (585 copies: loose, and
in the genanim_15 packs, several packs holding the same clip) by kind (infantry, gun crews, vehicles and guns, the HQ's
figures, animals and scenery), each with its length, frames and bones, the names the game's models give it ("idle1",
"t_course"...) and the models and units that play it.

A clip is reached from the data through an animation object (TGfxDescriptorAnimation for infantry,
TResourceMatrixArrayAnimation for the rest) whose FileName ("WW2\\Res3D\\Units\\Common\\Fusilier_Courselod0.Ase2NdfBin")
is the clip's path in the packs ("genanim_15\\ww2\\res3d\\units\\common\\fusilier_courselod0.baf"), held by a model's
ResourceAnimation (name -> animation); all 871 animation objects of the game name a clip the packs have.
"""
from __future__ import annotations

import re

B = "\\"
ROOT = "genanim_15" + B
KINDS = ("infantry", "crews", "vehicles", "hq", "scenery", "other")
INFANTRY = re.compile(r"^(fusilier|parachute|driver|soldat|officier)", re.I)
CREWS = re.compile(r"^servant|artillery_|dca_|salve", re.I)


def member_of(file_name: str) -> str:
    """A clip's path in the packs for the FileName the data gives it."""
    return ROOT + file_name.replace("/", B).rsplit(".", 1)[0].lower().lstrip(B) + ".baf"


def kind_of(member: str) -> str:
    parts = member.lower().split(B)
    stem = parts[-1]
    if "decors" in parts or "fx" in parts:
        return "scenery"
    if "hq" in parts:
        return "hq"
    if "units" in parts:
        if INFANTRY.match(stem):
            return "infantry"
        if CREWS.search(stem) or any(CREWS.search(p) for p in parts):
            return "crews"
        return "vehicles"
    return "other"


def words(member: str) -> str:
    """A clip's file name in words: "fusilier_course_droitelod0" -> "Fusilier course droite"."""
    stem = member.rsplit(B, 1)[-1].rsplit(".", 1)[0]
    stem = re.sub(r"lod0$", "", stem, flags=re.I)
    return re.sub(r"[_\-]+", " ", stem).strip().capitalize() or stem


UNIT = "$/GFX/Everything/Descriptor_Unit_"


def _units_above(db, model: int, depth: int = 4) -> list:
    """The units that play a model: those that point at it, or at a model that holds it (a gun's model holds its
    crew's: SousElements), up to `depth` steps."""
    seen, level, units = {model}, [model], []
    for _ in range(depth):
        nxt = []
        for oid in level:
            for src, address in db.execute("""SELECT o.id, o.address FROM ref r JOIN object o ON o.id = r.src
                                              WHERE r.dst = ? AND o.shadow = 0""", (oid,)):
                if address and address.startswith(UNIT) and ":" not in address:
                    if address not in units:
                        units.append(address)
                elif src not in seen:
                    seen.add(src)
                    nxt.append(src)
        level = nxt
        if not level:
            break
    return units


def _models_below(db, start: int, depth: int = 4) -> list:
    """The animated models a unit (or model) points at, and the ones those hold (a gun's crew), up to `depth`."""
    seen, level, models = {start}, [start], []
    for _ in range(depth):
        nxt = []
        for oid in level:
            for dst, cls in db.execute("""SELECT r.dst, o.class FROM ref r JOIN object o ON o.id = r.dst
                                          WHERE r.src = ? AND o.shadow = 0""", (oid,)):
                if dst in seen:
                    continue
                seen.add(dst)
                if cls in ("TGfxDescriptorModeleWithAnimation", "TGfxDescriptorBiped"):
                    models.append(dst)
                if cls.startswith("TGfx") or cls.startswith("TUnite") or cls.startswith("TInfanterie"):
                    nxt.append(dst)
        level = nxt
        if not level:
            break
    return models


def uses(db) -> dict:
    """{clip path: {"names": [the names models give it], "models": [model addresses], "units": [unit addresses]}}."""
    out: dict = {}
    anims = db.execute("""SELECT o.id, v.text FROM object o JOIN value v ON v.object = o.id AND v.path = 'FileName'
                          WHERE o.class IN ('TResourceMatrixArrayAnimation', 'TGfxDescriptorAnimation')
                          AND o.shadow = 0""").fetchall()
    model_units: dict = {}
    for oid, fname in anims:
        if not fname:
            continue
        got = out.setdefault(member_of(fname), {"names": [], "models": [], "units": []})
        for src, path in db.execute("SELECT src, path FROM ref WHERE dst = ? AND path LIKE 'ResourceAnimation[%'", (oid,)):
            key = db.execute("SELECT text FROM value WHERE object = ? AND path = ?",
                             (src, path.rsplit(".", 1)[0] + ".k")).fetchone()
            if key and key[0] and key[0] not in got["names"]:
                got["names"].append(key[0])
            model = db.execute("SELECT address FROM object WHERE id = ?", (src,)).fetchone()[0]
            if model not in got["models"]:
                got["models"].append(model)
            if src not in model_units:
                model_units[src] = _units_above(db, src)
            for u in model_units[src]:
                if u not in got["units"]:
                    got["units"].append(u)
    return out


def unit_clips(db, unit: str) -> list:
    """[(clip path, the name its model gives it)] for a unit: every model it points at, each model's animations."""
    out = []
    row = db.execute("SELECT id FROM object WHERE address = ? OR export = ? ORDER BY shadow LIMIT 1", (unit, unit)).fetchone()
    if row is None:
        return out
    for m in _models_below(db, row[0]):
        for path, dst in db.execute("SELECT path, dst FROM ref WHERE src = ? AND path LIKE 'ResourceAnimation[%].v'", (m,)):
            key = db.execute("SELECT text FROM value WHERE object = ? AND path = ?", (m, path[:-2] + ".k")).fetchone()
            f = db.execute("SELECT text FROM value WHERE object = ? AND path = 'FileName'", (dst,)).fetchone()
            if f and f[0]:
                item = (member_of(f[0]), key[0] if key else "")
                if item not in out:
                    out.append(item)
    return out


def catalogue(db, clips: dict) -> list:
    """Every clip: [{member, kind, name, seconds, frames, bones, packs, names, models, units}] for `clips` ({clip
    path: {"packs": [...], "seconds", "frames", "bones"}}), in the kinds' order then by path."""
    found = uses(db)
    rows = []
    for member, c in clips.items():
        u = found.get(member, {})
        rows.append({"member": member, "kind": kind_of(member), "name": words(member), "seconds": c["seconds"],
                     "frames": c["frames"], "bones": c["bones"], "packs": c["packs"], "names": u.get("names", []),
                     "models": u.get("models", []), "units": u.get("units", [])})
    order = {k: i for i, k in enumerate(KINDS)}
    rows.sort(key=lambda r: (order.get(r["kind"], len(KINDS)), r["member"]))
    return rows
