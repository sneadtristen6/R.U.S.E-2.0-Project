# Import a model

> **For:** modders · **You need:** RUSE Studio 0.9.6 or later, a mod, and a 3D model (.3ds, .glb or .gltf) ·
> **Takes:** a few minutes

Give a new unit a 3D model of its own, from Blender or any other 3D tool. That's how the
[M1 Abrams mod](https://github.com/sneadtristen6/Ruse-Mods) was made: the first model brought into R.U.S.E. from
another 3D program, seen in the game.

A model can also go on a new building, in place of a piece of its look (see
[[Buildings and build menus|Buildings-and-Build-Menus]]), or on your map as a rock, prop, bush or tree of your own
(see [[Place buildings and trees|Place-Buildings-and-Trees]]). Both: Studio 0.9.8.8, seen in the game.

## 1. Get a model

A **.3ds** with its pictures (.tga or .png), or a **.glb** or **.gltf** (pictures inside it: PNG, JPG or WebP). A
model the importer can't read (compressed meshes, KTX2 pictures) says so and how to fix it in Blender.

- **From Blender:** File > Export > glTF 2.0, format **glTF Binary (.glb)**.
- **From a free-model site:** many tanks come as .3ds with a folder of .tga pictures. Keep the folder as it came: the
  Studio finds the pictures beside the .3ds or in the folder above, even under the shortened names .3ds files use
  (`MAIN_DEF.TGA` for `Main_Defuse.tga`).
- Check the model's license before you share your mod, and credit its author in your mod's README.

**What helps:** parts named for what they are. The Studio turns a part with *turret* in its name (or *tourelle*,
*tower*) with the turret, and one with *barrel*, *gun* or *cannon* with it too. A part sitting on the turret turns
with it as well. Everything else moves with the hull. The gun should point straight ahead.

The Abrams example: **"Tank Abrams" by ags**, free at
[downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/) (a .3ds and its .tga pictures,
parts named Main_Body, Main_Turre, Main_Barre...).

## 2. Make the unit

In the **Units** tab, click **New unit (import a model)** at the top, then pick the unit to start from (for a tank,
a tank: the Sherman for the Abrams). Give it a name and click **Create**: the new unit's page opens at
**Import model…**. The new unit's model will turn and drive like this unit's. A game unit's page has the same way
in: **New unit from this one…** under **Its own model**. (Studio 0.9.6 has neither button yet: open the unit and
choose **New unit…** on its page.)

## 3. Import

On the new unit's page, under **Its own model**:

1. Set **Size**: its length over the copied unit's. **1** is as long; an M1 Abrams over a Sherman is **1.36** (their
   real lengths).
2. Click **Import model…** and pick the .3ds or .glb.

The Studio fits it to the unit: facing forward (the way its gun points), its length, placed where the copied unit
stands, its turret turning where it is on your model, standing on the ground. Its pictures become textures of its own. The page shows it in 3D, with which
parts turn with the turret. If a picture wasn't found, it says which: put the pictures beside the model and import
again.

It's saved in your mod as `files/models/<the unit's name>.glb`. **Use the copied unit's model** takes it out again.

**Its size later:** the slider under the size box goes from **Tiny** to **Huge** (0.05 to 20), with **Game size** (1)
and, for an era unit, **Real life** marked; click **Resize** and the model is fitted again from its own file. With
several new planes (or ground units), one click resizes them all. The game reads a model when it loads, so a new size
shows from the next build.

**Where it sits:** a new model is put on the middle of the unit it copies, so most models need nothing here. If yours
doesn't sit right, open **Move it** under the size (it stays open on a model you have moved). It takes three numbers,
**Forward**, **Right** and **Up**, in the game's units (the page says how long the unit it copies is, in those units). A minus goes the other way, and 0, 0, 0 puts it
back where it was fitted. Click **Move** and the model is fitted again from its own file, that far away; its turret and
propellers go with it, so they still turn in the right place. In the 3D view the blue ring is where the unit it copies
stands, and the mark on the ring is the front. A new size keeps the move. A model rigged to the unit's own bones (a
soldier, a gun's crew) stays where its bones are: move that one in Blender.

**Planes:** a plane opened in Blender from the Studio and brought back faces forward and keeps its propellers where
your model has them, as many as it has, whatever the plane it copies had: blades on the ground, spinning discs in the
air. Seen in the game. A model from anywhere else keeps its propellers as it drew them, standing still: the importer
can't tell yet which parts of it are propellers.

## 4. Its card, then test

Turn the 3D view until the new model looks right in the dashed frame and click **Use this view as the card** (see
[[Edit units|Edit-Units]]). Then **Test in game**: the unit is at its factory in a battle.

## Change it in Blender

`files/models/<the unit's name>.glb` opens in Blender like any .glb. Keep the two object names (`chassis` for the
hull, `tourelle_01` for the turret) and export it over the same file (glTF Binary): the next build uses it.

**Open in Blender** on a unit's page names each part's bone as the game does, so one of the game's own tanks opened in
Blender and imported back keeps its turret turning (Studio 0.9.8.8; a model exported before keeps its old names: open
it in Blender again).

**A model that sat in the wrong place** (Studio 0.9.8.7 and earlier, on new units made from the Panther and 85 other
units whose turrets the Studio misread): use **Import model…** again on that unit, and it sits on the turret.

## Early

- Tracks and wheels don't turn yet: they move with the hull.
- The gun's flash and the wreck are the copied unit's.
- Pictures are made at most 1024 across, like the game's own unit pictures.

From the command line, the same: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. Add `--move 50 0 -10` to move it 50 forward and 10
down from where it's fitted (forward, right, up).

**Next:** [[Export and share|Export-and-Share]]
