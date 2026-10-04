"""Run by Blender, not by Python (`blender --python blender_open.py -- <model.glb> ...`, as the Studio's Open in
Blender and `ruse export-model --open` do): clear Blender's starting scene, import the .glb files, and show the
models textured and framed in the Texture Paint workspace, ready to paint. Uses only Blender's own modules, so it
never imports rusemod.

The bones stay in the file (every vertex keeps them, for writing models back later) but are hidden: the skeleton
files' bone positions aren't read yet, so all of a model's bones sit at one point, and the importer would draw each
one as a sphere in front of the model (and leave its sphere shape in the scene). Propeller discs (rusemod.gltf
writes them as `<model>_propeller`) are hidden too: the game draws them with a shader of its own, so here they're
only a square covered with the whole picture.

Saving the paint needs no menu (2026-10-04: Image > Save was hard to find): each texture is linked to its picture
beside the .glb, and every painted picture is saved
- when the Studio's Bring back asks (it writes SAVE_REQUEST in the folder; this answers with SAVE_DONE),
- with Ctrl+S or the "Save paint" button in the 3D view's and the picture's header,
- and on its own every AUTOSAVE seconds while there's unsaved paint, so closing Blender loses little.
Each picture is written to a file beside it first and then put in place, so the Studio never reads half of one.

The scene is cleared through Blender's data, not by reloading factory settings: reloading while Blender's window
is starting broke the import (2026-10-03: only the bone sphere arrived). Anything that goes wrong is printed to
Blender's console (Window > Toggle System Console)."""
import json
import os
import sys
import time
import traceback
from pathlib import Path

import blf
import bpy

files = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FOLDER = Path(files[0]).resolve().parent if files else None
SAVE_REQUEST, SAVE_DONE = "save.request", "save.done"  # the same names as rusemod.blender's
AUTOSAVE = 10.0  # seconds
HINT = ("Paint with the left mouse button.  Colour: the first colour square at the top.  Brush size: F.",
        "Ctrl+S saves your paint. Then click Bring back in the R.U.S.E. Studio.")


def clear_start_scene() -> None:
    """Remove the starting cube, light and camera (and anything else in the scene) before importing."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def tidy() -> list:
    """Hide the bones and the propeller discs, drop the importer's bone sphere; returns the models to paint."""
    models = []
    for obj in list(bpy.data.objects):
        if obj.type == "ARMATURE":
            for pb in obj.pose.bones:
                pb.custom_shape = None
            obj.show_in_front = False
            obj.hide_set(True)
        elif obj.type == "MESH" and obj.name.startswith("Icosphere") and not obj.data.materials:
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type == "MESH" and "_propeller" in obj.name:
            obj.hide_set(True)
            obj.hide_render = True
        elif obj.type == "MESH":
            models.append(obj)
    for coll in list(bpy.data.collections):
        if coll.name.startswith("glTF_not_exported") and not coll.objects:
            bpy.data.collections.remove(coll)
    return models


def link_pictures(glb: str, new_images: list) -> None:
    """Point each texture the import brought at its colour picture beside the .glb (<stem>_<texture>_colour.png,
    as rusemod.gltf writes it), so painting and saving write that file, which the Studio's Bring back takes into
    the mod."""
    folder, stem = Path(glb).parent, Path(glb).stem
    for img in new_images:
        base = img.name.rsplit(".", 1)[0] if img.name[-4:-3] == "." and img.name[-3:].isdigit() else img.name
        pic = folder / f"{stem}_{base}_colour.png"
        if not pic.is_file():
            continue
        linked = bpy.data.images.load(str(pic), check_existing=True)
        img.user_remap(linked)
        bpy.data.images.remove(img)
        linked.name = base
        print("rusemod: painting saves to", pic)


# --- saving the paint ---
def _ours(img) -> bool:
    """A picture of the folder the models came from (not one the user loaded from elsewhere)."""
    if FOLDER is None or img.source != "FILE" or not img.filepath:
        return False
    try:
        return Path(bpy.path.abspath(img.filepath)).resolve().parent == FOLDER
    except OSError:
        return False


def save_paint() -> list:
    """Save every painted (unsaved) picture of the models; returns their file names."""
    saved = []
    for img in bpy.data.images:
        if not (_ours(img) and img.is_dirty):
            continue
        real = Path(bpy.path.abspath(img.filepath))
        part = real.with_name(real.stem + ".saving.png")
        img.save(filepath=str(part))
        os.replace(part, real)
        saved.append(real.name)
    if saved:
        print("rusemod: saved", saved)
    return saved


_last_save = [time.monotonic()]


def watch():
    """Every half second: answer the Studio's Bring back, and save unsaved paint every AUTOSAVE seconds."""
    try:
        request = FOLDER / SAVE_REQUEST
        if request.exists():
            saved = save_paint()
            done = FOLDER / (SAVE_DONE + ".part")
            done.write_text(json.dumps(saved), encoding="utf-8")
            os.replace(done, FOLDER / SAVE_DONE)
            request.unlink(missing_ok=True)
            _last_save[0] = time.monotonic()
        elif time.monotonic() - _last_save[0] >= AUTOSAVE:
            save_paint()
            _last_save[0] = time.monotonic()
    except Exception:  # noqa: BLE001  (shown in Blender's console)
        traceback.print_exc()
    return 0.5


class RUSE_OT_save_paint(bpy.types.Operator):
    """Save what you painted, so the Studio's Bring back takes it into your mod"""
    bl_idname = "ruse.save_paint"
    bl_label = "Save paint"

    def execute(self, context):
        saved = save_paint()
        self.report({"INFO"}, f"Saved {len(saved)} picture(s). Now click Bring back in the Studio." if saved
                    else "Your paint is already saved. Click Bring back in the Studio.")
        return {"FINISHED"}


def header_button(self, context):
    self.layout.operator(RUSE_OT_save_paint.bl_idname, text="Save paint (Ctrl+S)", icon="FILE_TICK")


def draw_hint():
    """The few things to know, written at the top of the 3D view under its name (the brushes' shelf covers the
    bottom of it in the Texture Paint workspace)."""
    try:
        scale = bpy.context.preferences.system.ui_scale
        top = bpy.context.region.height
        blf.size(0, 14 * scale)
        blf.enable(0, blf.SHADOW)
        blf.shadow(0, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(0, 1, -1)
        blf.color(0, 1.0, 0.95, 0.75, 1.0)
        for i, line in enumerate(HINT):
            blf.position(0, 60 * scale, top - (128 + 20 * i) * scale, 0)  # under the view's name and object
            blf.draw(0, line)
        blf.disable(0, blf.SHADOW)
    except Exception:  # noqa: BLE001
        pass


def add_saving() -> None:
    """The Save paint button, Ctrl+S for it (it would save Blender's own scene file otherwise), the hint, and the
    watch on the folder."""
    bpy.utils.register_class(RUSE_OT_save_paint)
    bpy.types.VIEW3D_HT_header.prepend(header_button)
    bpy.types.IMAGE_HT_header.prepend(header_button)
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is not None:
        km = kc.keymaps.new(name="Window", space_type="EMPTY")
        km.keymap_items.new(RUSE_OT_save_paint.bl_idname, "S", "PRESS", ctrl=True)
    bpy.types.SpaceView3D.draw_handler_add(draw_hint, (), "WINDOW", "POST_PIXEL")
    if FOLDER is not None:
        bpy.app.timers.register(watch, first_interval=1.0, persistent=True)


# --- showing the models ---
def show() -> None:
    """Select the models and go to the Texture Paint workspace (the model in paint mode, its picture beside it)."""
    try:
        models = tidy_models()
        for o in models:
            o.select_set(True)
        if models:
            bpy.context.view_layer.objects.active = models[0]
        paint = bpy.data.workspaces.get("Texture Paint")
        window = bpy.context.window_manager.windows[0]
        if paint is not None:
            window.workspace = paint
        bpy.app.timers.register(frame, first_interval=0.5)
        print("rusemod: showing", [o.name for o in models])
    except Exception:  # noqa: BLE001  (shown in Blender's console)
        traceback.print_exc()
    return None


def tidy_models() -> list:
    return [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_get()]


def frame() -> None:
    """Textured shading and the models filling each 3D view (after the workspace change has taken place)."""
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
    for path in files:
        before = set(bpy.data.images)
        try:
            bpy.ops.import_scene.gltf(filepath=path, disable_bone_shape=True)
        except TypeError:  # an older Blender without that option
            bpy.ops.import_scene.gltf(filepath=path)
        link_pictures(path, [i for i in bpy.data.images if i not in before])
    print("rusemod: imported", [o.name for o in tidy()])
    add_saving()
except Exception:  # noqa: BLE001
    traceback.print_exc()
bpy.app.timers.register(show, first_interval=1.0)
