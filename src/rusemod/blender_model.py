"""Run by Blender, not by Python (`blender --python blender_model.py -- <model.glb> <send.glb> <words.json>`, as the
Studio's Change it in Blender does): a new unit's model opened to be CHANGED, not painted (rusemod.blender_open is the
painting one). Clears Blender's starting scene, imports the model with its bones (the Studio writes them at their real
places, so Blender's own tools work on them: Ctrl+P > With Automatic Weights puts a model of the modder's own on
them), shows them, and sends the model back to the Studio:
- with the "Send to the R.U.S.E. Studio" button in the 3D view's header,
- and when the Studio's Bring back the model asks (it writes SEND_REQUEST beside the file; this answers SEND_DONE).
The model is written as glTF Binary to <send.glb> (a file beside it first, then put in place: the Studio never reads
half of one); the Studio's Import model then takes it as the unit's own model. The words shown (the button, two lines
of help) come from <words.json>, in the Studio's language. Uses only Blender's own modules, so it never imports
rusemod. Anything that goes wrong is printed to Blender's console (Window > Toggle System Console).

Why (the owner's order of 2026-11-10, item 4, scratch/animmodels/item4/FINDINGS.md): a squad's soldier only reached
Blender through Custom uniform, its bones all sat at one spot, and nothing brought a changed model back.

A whole squad (`blender --python blender_model.py -- --squad <squad.json>`, the Studio's Change the squad in Blender,
ruse_studio.squadblender; the owner, 2026-11-11: "if you change one unit's appearance in Blender, that it just comes
back like that normally", "you change one soldier's color, only that soldier should change color"): every soldier
line of the squad in one scene, side by side, each imported from his own file into a collection of his own, with his
own armature, objects, materials and pictures (none shared with another soldier, so painting one never paints
another). Right after opening, each soldier is written once as he was opened (the manifest's "base" folder): what the
Studio compares his sendings with, written the same way (Blender 4.5 writes an untouched soldier byte for byte the
same, measured 2026-11-11, scratch/animmodels/squadblender/measure.json). Send writes ONE FILE PER SOLDIER, each at his
own place (the side-by-side move taken off), then the list of what was sent (the manifest's "sent", the file the
Studio's Bring my changes back waits for). A soldier's file holds what is his: his armature and imported objects,
anything parented to them or on his bones, anything with an Armature modifier on his bones, anything else in his
collection; an object on none of them is sent with nobody and named in the list ("left_out"). An object parented to
one of his bones goes in made skinned on that bone (a copy for the file only), so Import model hangs it on that bone
and it moves with it in the game; parented that way, Blender writes it with no skin and Import model would hang it
on the root bone."""
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

import blf
import bpy
from mathutils import Vector

ARGS =sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SQUAD_FLAG = "--squad"   # the same as rusemod.blender's
SQUAD_FILE = Path(ARGS[1]) if len(ARGS) > 1 and ARGS[0] == SQUAD_FLAG else None
SQUAD = None
if SQUAD_FILE is not None:
    try:
        SQUAD = json.loads(SQUAD_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        traceback.print_exc()
SOURCE = ARGS[0] if ARGS and SQUAD_FILE is None else None
SEND = Path(ARGS[1]) if len(ARGS) > 1 and SQUAD_FILE is None else Path(SQUAD["sent"]) if SQUAD else None
WORDS_FILE = Path(ARGS[2]) if len(ARGS) > 2 and SQUAD_FILE is None else None
SEND_REQUEST, SEND_DONE = "send.request", "send.done"  # the same names as rusemod.blender's
WORDS = {"send": "Send to the R.U.S.E. Studio", "sent": "Sent. Now click Bring back the model in the R.U.S.E. Studio.",
         "hint": []}
try:
    if WORDS_FILE is not None and WORDS_FILE.is_file():
        WORDS.update(json.loads(WORDS_FILE.read_text(encoding="utf-8")))
    elif SQUAD and isinstance(SQUAD.get("words"), dict):
        WORDS.update(SQUAD["words"])
except (OSError, ValueError):
    traceback.print_exc()
SOLDIER = "ruse_soldier"   # custom property: the soldier an object or collection is (his id, as the manifest names him)
OFFSET = "ruse_offset"     # custom property of a soldier's collection: how far he stands from his own place
ALPHA = "ruse_alpha"       # custom property of a material: the alpha picture (side colour / shine) the Studio gave it


def clear_start_scene() -> None:
    """Remove the starting cube, light and camera (anything in the scene) before importing (as blender_open does)."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def send() -> str:
    """Write the whole scene (the bones and every model on them) as glTF Binary to SEND; returns its path. A squad
    (SQUAD): send_squad's."""
    if SQUAD:
        return send_squad()
    part = SEND.with_name(SEND.stem + ".sending.glb")
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.export_scene.gltf(filepath=str(part), export_format="GLB")
    os.replace(part, SEND)
    print("rusemod: sent", SEND)
    return str(SEND)


# --- a whole squad (SQUAD) ---
def import_file(path: str) -> list:
    """Import one .glb as the single model is imported (its bones without the importer's bone sphere); returns the
    objects it made."""
    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=path, disable_bone_shape=True)
    except TypeError:  # an older Blender without that option
        bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for obj in list(new):  # the importer's bone sphere, when it made one
        if obj.type == "MESH" and obj.name.startswith("Icosphere") and not obj.data.materials:
            new.remove(obj)
            bpy.data.objects.remove(obj, do_unlink=True)
    return new


def soldier_ids() -> list:
    return [s["id"] for s in SQUAD["soldiers"]]


def collection_of(sid: str):
    return next((c for c in bpy.data.collections if c.get(SOLDIER) == sid), None)


def owner_of(obj):
    """The soldier an object goes with (his id), or None: the first of its parents that is a soldier's (an object put
    on his bones or parented to his armature), else the armature its Armature modifier follows, else its own (one of
    his imported objects), else the soldier's collection it's in."""
    up = obj.parent
    while up is not None:
        if up.get(SOLDIER):
            return up[SOLDIER]
        up = up.parent
    for m in getattr(obj, "modifiers", ()):
        if m.type == "ARMATURE" and m.object is not None and m.object.get(SOLDIER):
            return m.object[SOLDIER]
    if obj.get(SOLDIER):
        return obj[SOLDIER]
    for c in obj.users_collection:
        if c.get(SOLDIER):
            return c[SOLDIER]
    return None


def materials_of(objs) -> list:
    out = []
    for o in objs:
        if o.type == "MESH":
            for m in o.data.materials:
                if m is not None and m not in out:
                    out.append(m)
    return out


def images_of(mat) -> list:
    return [n.image for n in (mat.node_tree.nodes if mat.node_tree else ()) if n.type == "TEX_IMAGE" and n.image]


def own_copies(owned: dict) -> None:
    """Each soldier with his own materials and pictures: one another soldier also uses is copied for him (Blender's
    glTF import already gives each file its own, measured 2026-11-11; this keeps it so whatever the import does)."""
    seen_mats, seen_imgs = {}, {}
    for sid, objs in owned.items():
        for o in objs:
            if o.type != "MESH":
                continue
            for k, mat in enumerate(o.data.materials):
                if mat is None:
                    continue
                if seen_mats.setdefault(mat.name, sid) != sid:
                    mat = mat.copy()
                    o.data.materials[k] = mat
                    seen_mats[mat.name] = sid
                for node in (mat.node_tree.nodes if mat.node_tree else ()):
                    if node.type == "TEX_IMAGE" and node.image is not None:
                        if seen_imgs.setdefault(node.image.name, sid) != sid:
                            node.image = node.image.copy()
                            seen_imgs[node.image.name] = sid


def world_box(objs):
    """(lowest x, highest x, highest z) of these objects' meshes in the scene, or None."""
    xs, zs = [], []
    for o in objs:
        if o.type != "MESH":
            continue
        for corner in o.bound_box:
            p = o.matrix_world @ Vector(corner)
            xs.append(p.x)
            zs.append(p.z)
    return (min(xs), max(xs), max(zs)) if xs else None


def open_squad() -> None:
    """Every soldier of SQUAD from his own file into one scene, side by side, then each written as opened (base)."""
    clear_start_scene()
    owned = {}
    for s in SQUAD["soldiers"]:
        new = import_file(s["file"])
        coll = bpy.data.collections.new(s["name"])
        bpy.context.scene.collection.children.link(coll)
        coll[SOLDIER] = s["id"]
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            coll.objects.link(o)
            o[SOLDIER] = s["id"]
            if o.type == "ARMATURE":
                o.name = s["name"]
                o.data.name = s["name"]
        alphas = s.get("alpha") or {}
        for mat in materials_of(new):
            if mat.name in alphas:
                mat[ALPHA] = alphas[mat.name]
        owned[s["id"]] = new
    own_copies(owned)
    # side by side along x, the first where he stands, each next one past the one before, a quarter of the tallest
    # one's height apart
    boxes = {sid: world_box(objs) for sid, objs in owned.items()}
    tall = max((b[2] for b in boxes.values() if b), default=2.0)
    edge = None
    for s in SQUAD["soldiers"]:
        box, coll = boxes.get(s["id"]), collection_of(s["id"])
        dx = 0.0
        if box is not None:
            if edge is not None:
                dx = edge + tall * 0.25 - box[0]
            edge = box[1] + dx
        coll[OFFSET] = [dx, 0.0, 0.0]
        for o in owned[s["id"]]:
            if o.parent is None:
                o.location.x += dx
    bpy.context.view_layer.update()
    base = Path(SQUAD["base"])
    base.mkdir(parents=True, exist_ok=True)
    listed = {}
    for s in SQUAD["soldiers"]:
        listed[s["id"]] = write_soldier(s["id"], base / f"{s['id']}.glb")
    (base / "base.json.part").write_text(json.dumps({"session": SQUAD.get("session"), "soldiers": listed}),
                                         encoding="utf-8")
    os.replace(base / "base.json.part", base / "base.json")
    print("rusemod: squad opened,", len(owned), "soldiers")


def write_soldier(sid: str, path: Path) -> dict:
    """Write one soldier as glTF Binary to `path` (a file beside it first, then put in place), at his own place:
    everything that goes with him (owner_of), an object on one of his bones made skinned on that bone (a copy, for the
    file only), nothing else. Returns {"file", "sha256", "objects", "alpha": {material: its alpha picture}}; a soldier
    with nothing left on him (every object of his deleted) is written nowhere: "file" and "sha256" None."""
    coll = collection_of(sid)
    offset = list(coll.get(OFFSET, (0.0, 0.0, 0.0))) if coll is not None else [0.0, 0.0, 0.0]
    mine = [o for o in bpy.context.scene.objects if owner_of(o) == sid]
    if not mine:
        path.unlink(missing_ok=True)
        return {"file": None, "sha256": None, "objects": [], "alpha": {}}
    send = bpy.data.collections.new("ruse_send")
    bpy.context.scene.collection.children.link(send)
    made = []
    try:
        for o in mine:
            if (o.type == "MESH" and o.parent is not None and o.parent_type == "BONE" and o.parent.type == "ARMATURE"
                    and o.parent_bone in o.parent.data.bones):
                dup = o.copy()
                dup.data = o.data.copy()
                send.objects.link(dup)
                world = o.matrix_world.copy()
                dup.parent = o.parent
                dup.parent_type = "OBJECT"
                dup.matrix_world = world
                dup.vertex_groups.clear()
                group = dup.vertex_groups.new(name=o.parent_bone)
                group.add(list(range(len(dup.data.vertices))), 1.0, "REPLACE")
                for m in list(dup.modifiers):
                    if m.type == "ARMATURE":
                        dup.modifiers.remove(m)
                dup.modifiers.new("Armature", "ARMATURE").object = o.parent
                made.append(dup)
            else:
                send.objects.link(o)
        roots = [o for o in mine if o.parent is None]
        for o in roots:
            for i in range(3):
                o.location[i] -= offset[i]
        bpy.context.view_layer.update()
        before = bpy.context.view_layer.active_layer_collection
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[send.name]
        part = path.with_name(path.stem + ".sending.glb")
        try:
            bpy.ops.export_scene.gltf(filepath=str(part), export_format="GLB", use_active_collection=True)
        finally:
            bpy.context.view_layer.active_layer_collection = before
            for o in roots:
                for i in range(3):
                    o.location[i] += offset[i]
            bpy.context.view_layer.update()
        os.replace(part, path)
    finally:
        for dup in made:
            data = dup.data
            bpy.data.objects.remove(dup, do_unlink=True)
            bpy.data.meshes.remove(data)
        bpy.data.collections.remove(send)
    alpha = {m.name: m[ALPHA] for m in materials_of(mine) if m.get(ALPHA)}
    return {"file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "objects": sorted(o.name for o in mine), "alpha": alpha}


def send_squad() -> str:
    """Write every soldier to his own file (write_soldier) in the folder of SEND, then the list of what was sent to
    SEND itself; returns SEND's path."""
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    folder = SEND.parent
    folder.mkdir(parents=True, exist_ok=True)
    listed = {sid: write_soldier(sid, folder / f"{sid}.glb") for sid in soldier_ids()}
    left = sorted(o.name for o in bpy.context.scene.objects
                  if owner_of(o) is None and o.type not in ("CAMERA", "LIGHT"))
    part = SEND.with_name(SEND.name + ".part")
    part.write_text(json.dumps({"session": SQUAD.get("session"), "soldiers": listed, "left_out": left}, indent=1),
                    encoding="utf-8")
    os.replace(part, SEND)
    print("rusemod: sent", len(listed), "soldiers to", folder, "; on no soldier:", left)
    return str(SEND)


def watch():
    """Every half second: answer the Studio's Bring back the model."""
    try:
        request = SEND.parent / SEND_REQUEST
        if request.exists():
            sent = send()
            done = SEND.parent / (SEND_DONE + ".part")
            done.write_text(json.dumps({"file": sent}), encoding="utf-8")
            os.replace(done, SEND.parent / SEND_DONE)
            request.unlink(missing_ok=True)
    except Exception:  # noqa: BLE001  (shown in Blender's console)
        traceback.print_exc()
    return 0.5


class RUSE_OT_send_model(bpy.types.Operator):
    """Send this model to the R.U.S.E. Studio: then click Bring back the model there"""
    bl_idname = "ruse.send_model"
    bl_label = "Send to the R.U.S.E. Studio"

    def execute(self, context):
        try:
            send()
        except Exception as exc:  # noqa: BLE001
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, WORDS["sent"])
        if SQUAD:
            try:
                left = json.loads(SEND.read_text(encoding="utf-8")).get("left_out") or []
            except (OSError, ValueError):
                left = []
            if left and WORDS.get("left_out"):
                self.report({"WARNING"}, WORDS["left_out"].replace("{names}", ", ".join(left)))
        return {"FINISHED"}


def header_button(self, context):
    self.layout.operator(RUSE_OT_send_model.bl_idname, text=WORDS["send"], icon="EXPORT")


def draw_hint():
    """The few things to know, at the top of the 3D view under its name."""
    try:
        scale = bpy.context.preferences.system.ui_scale
        top = bpy.context.region.height
        blf.size(0, 14 * scale)
        blf.enable(0, blf.SHADOW)
        blf.shadow(0, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(0, 1, -1)
        blf.color(0, 1.0, 0.95, 0.75, 1.0)
        for i, line in enumerate(WORDS.get("hint") or []):
            blf.position(0, 60 * scale, top - (128 + 20 * i) * scale, 0)
            blf.draw(0, line)
        blf.disable(0, blf.SHADOW)
    except Exception:  # noqa: BLE001
        pass


def add_sending() -> None:
    bpy.utils.register_class(RUSE_OT_send_model)
    bpy.types.VIEW3D_HT_header.prepend(header_button)
    bpy.types.SpaceView3D.draw_handler_add(draw_hint, (), "WINDOW", "POST_PIXEL")
    if SEND is not None:
        bpy.app.timers.register(watch, first_interval=1.0, persistent=True)


def show() -> None:
    """The model selected and framed in the Layout workspace, shaded with its pictures, its bones drawn in front."""
    try:
        meshes = [o for o in bpy.data.objects if o.type == "MESH"]
        for o in bpy.data.objects:
            if o.type == "ARMATURE":
                o.show_in_front = True
            o.select_set(o in meshes)
        if meshes:
            bpy.context.view_layer.objects.active = meshes[0]
        layout = bpy.data.workspaces.get("Layout")
        if layout is not None:
            bpy.context.window_manager.windows[0].workspace = layout
        bpy.app.timers.register(frame, first_interval=0.5)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    return None


def frame() -> None:
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != "VIEW_3D":
                    continue
                area.spaces.active.shading.type = "MATERIAL"
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                if region is not None:
                    with bpy.context.temp_override(window=window, area=area, region=region):
                        bpy.ops.view3d.view_selected()
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    return None


try:
    if SQUAD:
        open_squad()
    else:
        clear_start_scene()
    if SOURCE:
        try:
            bpy.ops.import_scene.gltf(filepath=SOURCE, disable_bone_shape=True)
        except TypeError:  # an older Blender without that option
            bpy.ops.import_scene.gltf(filepath=SOURCE)
        for obj in list(bpy.data.objects):  # the importer's bone sphere, when it made one
            if obj.type == "MESH" and obj.name.startswith("Icosphere") and not obj.data.materials:
                bpy.data.objects.remove(obj, do_unlink=True)
    add_sending()
except Exception:  # noqa: BLE001
    traceback.print_exc()
if not bpy.app.background:
    bpy.app.timers.register(show, first_interval=1.0)
