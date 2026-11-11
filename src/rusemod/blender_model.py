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

A file with animations (the unit's, rusemod.animglb's: item 5 of his list, "fully editable in the studio") opens at
the game's 30 frames a second, so every key of a clip falls on a whole frame; each animation is an action of its name
(Blender's importer makes one each, the first playing) whose custom properties say which of the unit's actions play it
("actions", read from the file's own animation extras, which Blender's importer doesn't carry over); the bones no
point of the model leans on (an effect point, the gun's second hand) are left out of Blender's automatic weights; and
the timeline at the bottom shows the Action Editor. Sending writes every action as an animation of the file, each
frame sampled (send's settings, named whatever Blender's defaults are), so the Studio gets every one back."""
import json
import os
import struct
import sys
import traceback
from pathlib import Path

import blf
import bpy

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SOURCE = ARGS[0] if ARGS else None
SEND = Path(ARGS[1]) if len(ARGS) > 1 else None
WORDS_FILE = Path(ARGS[2]) if len(ARGS) > 2 else None
SEND_REQUEST, SEND_DONE = "send.request", "send.done"  # the same names as rusemod.blender's
FPS = 30  # every clip of the game runs at 30 frames a second (rusemod.baf.FPS)
WORDS = {"send": "Send to the R.U.S.E. Studio", "sent": "Sent. Now click Bring back the model in the Studio.",
         "hint": [], "hint_animations": []}
try:
    if WORDS_FILE is not None and WORDS_FILE.is_file():
        WORDS.update(json.loads(WORDS_FILE.read_text(encoding="utf-8")))
except (OSError, ValueError):
    traceback.print_exc()
ANIMATED = False  # the opened file has animations


def clear_start_scene() -> None:
    """Remove the starting cube, light and camera (anything in the scene) before importing (as blender_open does)."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def file_animations(path: str) -> list:
    """The .glb's animations as its JSON part lists them ({"name", "extras"}): [] for none, or a file that can't be
    read that way."""
    try:
        with open(path, "rb") as f:
            head = f.read(20)
            length = struct.unpack_from("<I", head, 12)[0]
            doc = json.loads(f.read(length))
    except (OSError, ValueError, struct.error):
        return []
    return [{"name": a.get("name", ""), "extras": a.get("extras") or {}} for a in doc.get("animations") or []]


def label_actions(animations: list, new_actions: list) -> None:
    """Give each action the import made the names of the unit's actions that play it (its animation's extras,
    rusemod_actions) as its custom property "actions" ("-": none of them). An action Blender renamed (name.001) is
    found by its name before the number."""
    extras = {a["name"]: a["extras"] for a in animations}
    for action in new_actions:
        name = action.name
        if name not in extras and name[-4:-3] == "." and name[-3:].isdigit():
            name = name[:-4]
        got = extras.get(name)
        if got is not None:
            action["actions"] = ", ".join(got.get("rusemod_actions") or []) or "-"


def leave_out_unweighted() -> None:
    """Bones no point of the models leans on (an effect point, a gun's second hand) don't deform: Blender's automatic
    weights then never give them a point of a model of the modder's own (the game moves them as the clips say). They
    are all still sent: the clips move them."""
    weighted = set()
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        used = {g.group for v in obj.data.vertices for g in v.groups if g.weight > 0}
        weighted |= {g.name for g in obj.vertex_groups if g.index in used}
    for obj in bpy.data.objects:
        if obj.type == "ARMATURE":
            for bone in obj.data.bones:
                if bone.name not in weighted:
                    bone.use_deform = False


def send() -> str:
    """Write the whole scene (the bones, every model on them and every action) as glTF Binary to SEND; returns its
    path. The animation settings are named (all but one Blender's defaults today): every action an animation, each
    frame sampled and every sample kept, every bone, the pose put back to rest between them. Blender's Optimize
    Animation Size (on by default) is off: it keeps only the first and last key of any channel that moves less than
    0.0001 over the whole action (0.01 of the game's units; Blender 4.5's exporter, fcurve_is_constant), and a bone's
    small moves are the game's too."""
    part = SEND.with_name(SEND.stem + ".sending.glb")
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    settings = dict(export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
                    export_frame_step=1, export_frame_range=False, export_anim_slide_to_zero=False,
                    export_anim_single_armature=True, export_reset_pose_bones=True, export_def_bones=False,
                    export_optimize_animation_size=False)
    try:
        bpy.ops.export_scene.gltf(filepath=str(part), export_format="GLB", **settings)
    except TypeError:  # an older Blender without one of them: its own
        bpy.ops.export_scene.gltf(filepath=str(part), export_format="GLB")
    os.replace(part, SEND)
    print("rusemod: sent", SEND)
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
        return {"FINISHED"}


def header_button(self, context):
    self.layout.operator(RUSE_OT_send_model.bl_idname, text=WORDS["send"], icon="EXPORT")


def draw_hint():
    """The few things to know, at the top of the 3D view under its name (and how to change an animation, for a file
    with animations)."""
    try:
        scale = bpy.context.preferences.system.ui_scale
        top = bpy.context.region.height
        blf.size(0, 14 * scale)
        blf.enable(0, blf.SHADOW)
        blf.shadow(0, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(0, 1, -1)
        blf.color(0, 1.0, 0.95, 0.75, 1.0)
        lines = list(WORDS.get("hint") or []) + (list(WORDS.get("hint_animations") or []) if ANIMATED else [])
        for i, line in enumerate(lines):
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
    """The model selected and framed in the Layout workspace, shaded with its pictures, its bones drawn in front; with
    animations, the scene as long as the playing one and the timeline at the bottom the Action Editor (pick an
    animation there)."""
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
        if ANIMATED:
            bpy.app.timers.register(action_editor, first_interval=0.3)
        bpy.app.timers.register(frame, first_interval=0.5)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    return None


def playing_range() -> None:
    """The scene's frames: the playing action's."""
    rig = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
    action = rig.animation_data.action if rig is not None and rig.animation_data else None
    if action is not None:
        scene = bpy.context.scene
        scene.frame_start, scene.frame_end = int(action.frame_range[0]), int(action.frame_range[1])


def action_editor() -> None:
    """The timeline at the bottom of the Layout workspace shown as the Action Editor (where the animations are picked
    and their keys are)."""
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "DOPESHEET_EDITOR":
                    area.spaces.active.ui_mode = "ACTION"
                    return None
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
    clear_start_scene()
    if SOURCE:
        ANIMATIONS = file_animations(SOURCE)
        ANIMATED = bool(ANIMATIONS)
        if ANIMATED:  # the game's clips are at 30 frames a second: each key on a whole frame
            bpy.context.scene.render.fps, bpy.context.scene.render.fps_base = FPS, 1.0
        acted = set(bpy.data.actions)
        try:
            bpy.ops.import_scene.gltf(filepath=SOURCE, disable_bone_shape=True)
        except TypeError:  # an older Blender without that option
            bpy.ops.import_scene.gltf(filepath=SOURCE)
        for obj in list(bpy.data.objects):  # the importer's bone sphere, when it made one
            if obj.type == "MESH" and obj.name.startswith("Icosphere") and not obj.data.materials:
                bpy.data.objects.remove(obj, do_unlink=True)
        if ANIMATED:
            label_actions(ANIMATIONS, [a for a in bpy.data.actions if a not in acted])
            leave_out_unweighted()
            playing_range()
    add_sending()
except Exception:  # noqa: BLE001
    traceback.print_exc()
if not bpy.app.background:
    bpy.app.timers.register(show, first_interval=1.0)
