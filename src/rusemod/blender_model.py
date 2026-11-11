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
Blender through Custom uniform, its bones all sat at one spot, and nothing brought a changed model back."""
import json
import os
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
WORDS = {"send": "Send to the R.U.S.E. Studio", "sent": "Sent. Now click Bring back the model in the Studio.",
         "hint": []}
try:
    if WORDS_FILE is not None and WORDS_FILE.is_file():
        WORDS.update(json.loads(WORDS_FILE.read_text(encoding="utf-8")))
except (OSError, ValueError):
    traceback.print_exc()


def clear_start_scene() -> None:
    """Remove the starting cube, light and camera (anything in the scene) before importing (as blender_open does)."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def send() -> str:
    """Write the whole scene (the bones and every model on them) as glTF Binary to SEND; returns its path."""
    part = SEND.with_name(SEND.stem + ".sending.glb")
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
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
