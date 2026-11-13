# Import a model

> **For:** modders · **You need:** RUSE Studio 0.9.6 or later, a mod, and a 3D model (.3ds, .glb or .gltf) ·
> **Takes:** a few minutes

Give a new unit a 3D model of its own, from Blender or any other 3D tool. That's how the
[M1 Abrams mod](https://github.com/sneadtristen6/Ruse-Mods) was made: the first model brought into R.U.S.E. from
another 3D program, seen in the game.

A model can also go on a new building, in place of a piece of its look (see
[[Buildings and build menus|Buildings-and-Build-Menus]]), or on your map as a rock, prop, bush or tree of your own
(see [[Place buildings and trees|Place-Buildings-and-Trees]]). Both: Studio 0.9.8.8, seen in the game.

On the unit's page all of this is in **Look and moves**: **Import model…** is the **Model** row's button, and the rest of the model's options (its size, **Move it**) are under that row's **More**. What the model's animations do is under the **Sounds and animation** row's **More**. A squad's page starts with its soldiers instead, on its squad card: see [[Change a squad|Change-a-Squad]].

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
in: **New unit from this one…** on the **Model** row of **Look and moves**. (Studio 0.9.6 has neither button yet: open the unit and
choose **New unit…** on its page.)

## 3. Import

On the new unit's page, on the **Model** row of **Look and moves**:

1. Click **More** and set **Size**: its length over the copied unit's. **1** is as long; an M1 Abrams over a Sherman is **1.36** (their
   real lengths).
2. Click **Import model…** (the row's button) and pick the .3ds or .glb.

The Studio fits it to the unit: facing forward (the way its gun points), its length, placed where the copied unit
stands, its turret turning where it is on your model, standing on the ground. Its pictures become textures of its own. The page shows it in 3D, with which
parts turn with the turret. If a picture wasn't found, it says which: put the pictures beside the model and import
again.

It's saved in your mod as `files/models/<the unit's name>.glb`. **Use the copied unit's model** takes it out again.

**Where it is on your PC:** the **Model** row's **More** starts with it (a squad's page says it under **More options**, below its soldiers): the whole path, `Documents\RUSE 2.0\Mods\<your mod>\files\models\<the unit's name>.glb`, and **Show in folder**, which opens that folder. Before the unit has a model of its own, it says where the file will be. A unit with its own copy of the model (**Give it its own copy of the model**, or a squad's **Custom uniform**) is kept in the same folder, as `<the unit's name>.copy.toml`, its paint in the folder of the same name.

**Its size later:** the slider under the size box goes from **Tiny** to **Huge** (0.05 to 20), with **Game size** (1)
and, for an era unit, **Real life** marked; click **Resize** and the model is fitted again from its own file. With
several new planes (or ground units), one click resizes them all. The game reads a model when it loads, so a new size
shows from the next build.

**Where it sits:** a new model is put on the middle of the unit it copies, so most models need nothing here. If yours
doesn't sit right, use **Move it** under the size, in the Model row's **More**. It takes three numbers,
**Forward**, **Right** and **Up**, in the game's units (the page says how long the unit it copies is, in those units). A minus goes the other way, and 0, 0, 0 puts it
back where it was fitted. Click **Move** and the model is fitted again from its own file, that far away; its turret and
propellers go with it, so they still turn in the right place. In the 3D view the blue ring is where the unit it copies
stands, and the mark on the ring is the front. A new size keeps the move. A model rigged to the unit's own bones (a
soldier, a gun's crew) stays where its bones are: move that one in Blender. A model imported before Studio 0.9.8.17
keeps its old place (its turret on the copied unit's turret), even resized, until you import it again or move it; the
era units' models keep theirs.

**Planes:** a plane opened in Blender from the Studio and brought back faces forward and keeps its propellers where
your model has them, as many as it has, whatever the plane it copies had: blades on the ground, spinning discs in the
air. Seen in the game. A model from anywhere else keeps its propellers as it drew them, standing still: the importer
can't tell yet which parts of it are propellers. In the 3D view a plane's discs show see-through, the way the game
draws a spinning propeller.

**Soldiers, crews and more planes:** soldiers, a gun's crew and the planes the Studio couldn't fit a model to before
(the P-47, for one) take a model of their own too, if it is rigged to the unit's own bones: one of the game's models
opened in Blender from the Studio and changed there, say. It goes on those bones as it is, nothing moved or scaled,
and a squad's other men drawn with the same model wear it too. Seen in the game with a rifle squad, a gun's crew and the P-47.
A heavy-weapon soldier the game draws with a model of his own (the US rifle squad's bazooka man) keeps it until you give
him one on his own line of the squad's page (below).

**Your players:** a mod with a model imported by Studio 0.9.8.17 or later needs Launcher 0.4.8.17 or newer: an older
one gives the model the copied unit's skeleton, so its turret turns around the wrong point. 0.4.8.17 is a required
update, so the Launcher installs it by itself.

## Your own soldier, step by step

For a squad (riflemen, paratroopers, any infantry) the Studio does the Blender part with you. A squad's page starts with
its squad card and a line for each of its soldiers; [[Change a squad|Change-a-Squad]] goes through them.

1. **Make the squad** as in step 2 above, starting from a squad (the US rifle squad, say).
2. **Open the squad in Blender.** On the squad card, click **Change the squad in Blender**. Blender opens with every soldier of the squad side by side, each on his bones, each with his own copy of his pictures. No Blender yet? **Get Blender (free)** installs it; **Choose Blender…** shows the Studio where it is.
3. **Change a soldier, or put your own model on his bones.** To change him, edit him there. To use a model of your own: **File > Import** it into the same scene and place it over the soldier; click your model, **Shift+click** his bones, then press **Ctrl+P > With Automatic Weights**. Delete the game's soldier if you don't keep him.
4. **Send it.** Click **Send to the R.U.S.E. Studio** at the top of Blender.
5. **Bring it back.** On the squad card, click **Bring my changes back**. Each soldier gets only what was done to him, and one you didn't touch stays as he was: the card says who changed and who didn't. **Test in game** shows it.

Good to know:
- The US rifle squad's four riflemen are one figure in Blender: the game gives them one model, so what you do to it, all four wear. Its bazooka man is a figure of his own.
- Your Blender files stay in your mod's folder: `Documents\RUSE 2.0\Mods\<your mod>\blender\<the unit's name>\squad\`. They aren't packed into your mod when you share it. **More options**, under the soldiers, says where they are, and its **Show in folder** opens the folder they're in.
- Closed Blender before you brought your changes back? The small **Bring my changes back** under the big button takes what you sent last.
- If some points of your model have no bone (Blender's automatic weights miss a few), the page says how many: they move with the soldier's hips only. Paint them onto a bone in Blender's **Weight Paint**, then send again.
- A squad with a **Custom uniform**: your model takes the uniform's place (its paint stays in your mod); once every soldier is back to the game's look (**Back to the game's look** on his line), the uniform comes back.
- Already have a .glb made on the game soldier's bones? **Import a model…** on that soldier's line takes it as it is.
- Your mod keeps each soldier's model in `files\models\`: the riflemen's as `<the unit's name>.glb`, the heavy-weapon soldier's as `<the unit's name>@bazooka.glb`. **More options** says where each is kept (or will be), and which of the squad's other figures are drawn with it: the fallen soldier, and the figure seen from far away (the US rifle squad's is drawn with its bazooka man's).
- The whole squad in one Blender, each soldier brought back on his own, is new: not tried in the game yet.

## Its animations: which one each action plays

A model on bones of its own (a horse, a horse and its rider, any creature) brings its animations with it. On the
unit's page, **Its animations** shows what the unit plays for each thing it does in the game:

- **Stands still**, **Walks** and **Runs** come first: the least a model needs. If one of them has nothing of its own,
  the page says so, and what it plays instead.
- Each action is a list of the model's animations. Pick one, or leave it on **Nearest**: it then plays the closest one
  the model has, and the list says which. Nearest means, in order: an animation named for that action (stand or idle,
  walk, run or gallop, fire, death...), else what the nearest action plays (a walk the run, a run the walk, then the
  stand; a fire the aim, then the stand; any death the plain death). The build uses the same rule, so what the page
  says is what the game plays.
- An animation whose name starts with t_ or b_ (hr_t_fire, hr_b_run) plays on the top or the bottom half of the body
  only: a rider's on top, his horse's below.
- **Every other action** lists the rest, by kind: standing still, moving, aiming and firing, the heavy weapon,
  getting hit, dying.
- **On long moves** the game puts a squad in its truck. A unit with animations of its own goes as itself instead,
  playing the animation picked there (its run, when left on Nearest), as fast as its truck. Pick **In its truck** to
  keep the truck.

**A copy keeps its animations:** a unit copied from one with animations of its own plays the same ones. To change one
for it alone, click **Change in RUSE Decoy** on its **Sounds and animation** row, then **Only this unit**.

The Generic Horse made this way in the Studio played in the game (November 2026).
## A model with its own bones and animations

A horse, a horse with its rider, any creature: a model on bones of its own goes on a squad with its animations.

1. **Make it in Blender**: your model on an armature with bones of your own (named as you like), and an action for each animation. Name the actions for what they show: **stand** (or **idle**), **walk** and **run** at least; **death**, **fire**, **reload**, **hit**, **crouch**, **aim**, **look**, **flee** and **grenade** are known too.
2. **Export it**: **File > Export > glTF 2.0**, format **glTF Binary (.glb)**, with **Animation** ticked.
3. **Make the squad** as in step 2 above. On its page, click **Import a model…** on the riflemen's line, under **Each soldier**, and pick your .glb. The Studio sees that its bones aren't the soldier's and takes it with its own bones and every animation. The page shows how many bones it has, each animation with its length, and how many of the squad's actions play it.
4. **Test in game** shows it.

Good to know:
- Each action of the squad plays the animation named for it. An action no animation is named for has none yet: the page says how many.
- Changed it in Blender? Import it again: each action keeps its animation while one of that name is still in the file.
- Your mod keeps the model and every animation: `files\models\<the unit's name>.glb`, and each animation as `files\anim\own\<the unit's name>\<its name>.baf`.
- **Back to the game's look** on that line takes the model out again, with its animations.
- A squad with a heavy-weapon soldier: give him his own horse and rider with **Import a model…** on his line, made on the same bones as the riflemen's, and he plays their animations. On other bones he plays what he played in the copied squad, and the page warns you: that can stop the game. Taking the riflemen's model out takes his out with it.
- The Generic Horse made this way in the Studio played in the game (November 2026); nothing else made this way has been tried in the game yet.

## Its animations, changed in Blender

Animations are changed in RUSE Decoy. On the unit's page, in its **Sounds and animation** row, click **Change in RUSE Decoy**, then **Change its animations in Blender** under its animations. Blender opens with the unit and every animation it plays (standing, walking, running, firing, dying…), each named after what it does in it, with the game's own name after it: `Run, aiming (fusilier_course_vise)`.

1. **Pick one.** At the bottom of Blender, the Action Editor lists them: pick the one to change. **Space** plays it.
2. **Pose the bones.** Click a bone, press **Ctrl+Tab** for Pose Mode, **R** to turn it (**G** moves it), then **I** to keep the pose at this frame. Do it at every frame you change: Blender goes from one kept pose to the next by itself.
3. **Send it.** Click **Send to the R.U.S.E. Studio**: every animation goes, changed or not.
4. **Bring it back.** In RUSE Decoy, click **Bring my changes back**. It says which came back changed: those are this unit's own now, and RUSE Decoy shows them under **Only this unit**. Every other unit, and every animation you didn't touch, stays the game's.

Good to know:
- The game plays animations at 30 frames a second, and Blender opens them so. An animation opens as long as the game plays it; make it longer or shorter in Blender and it comes back so.
- An animation made in Blender (a copy of one, renamed) comes back too, but no action plays it yet: the Studio says so. A renamed one counts as new, and the one it was plays as before.
- Bones none of the soldier's points lean on (the gun's muzzle point, the second gun's hand) can be animated, but Blender's automatic weights leave them out.
- Only a new unit made in your mod gets animations of its own: for one of the game's units, make a new unit from it first.
- A model on bones of its own (a horse, any creature) sends its own animations, under their own names. One you change takes its place: every action that played it plays it changed, and the unit's **Sounds and animation** row lists it with the others.
- Checked with Blender 4.5 and the Studio's own tests; not tried in the game yet.

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
- Tried in the game with the game's own models (the Sherman, two planes, a rifle squad, a gun's crew): not yet with a
  model from anywhere else, another turret tank, a turret that turns all the way round, or a plane copying a unit with
  no propellers.
- A new unit copied from a towed gun, the FCM F1, the Puma, a half-track, the Bren carrier, a paratroop plane, some
  bunkers and a few others takes a model from anywhere too, not only one rigged to its bones, and it's drawn the way
  that unit is. Not tried in the game yet.

From the command line: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. With `--move`, it's fitted the way the Studio fits
it: `--move 50 0 -10` moves it 50 forward and 10 down from where it's fitted (forward, right, up), and `--move 0 0 0`
leaves it there. Without `--move`, the command still fits it the old way, its turret on the copied unit's turret.

**Next:** [[Export and share|Export-and-Share]]
