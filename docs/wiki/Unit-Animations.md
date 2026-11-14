# Unit animations

> **You need:** RUSE Studio 0.9.8.20 or later and a mod; Blender (free) to change a new unit's animations in Blender ·
> **Takes:** 10 minutes to read

How a unit moves (standing, walking, running, aiming, firing, dying) is its **animations**. This page says what the
game's animations are for, which one a unit plays for each thing it does, every way to change one (for one unit, for
every unit, for the units you pick, or in Blender), and how to get the game's back.

## What an animation is

- An animation moves a model's bones over time: one step of a run, a rifle raised to the shoulder, a fall (see
  [[Models and bones|Models-and-Bones]]).
- Each thing a unit does in the game (an **action**: stands still, walks, runs, fires...) plays one animation. A
  soldier plays two at once, one for each half of his body.
- Many units share the game's animations: every US rifleman runs the same run. So a change to an animation is, unless
  you pick otherwise, a change for every unit that plays it.
- Tanks turn their turret and wheels without animations: there's nothing to change here for them.

## The game's animations and what each is for

**RUSE Decoy** (its tab at the top of the Studio) lists every animation of the game on the left, under
**Animations**, by kind:

| Kind | What's in it |
|---|---|
| **Infantry** | Riflemen, bazookas, paratroopers and drivers: standing, walking, running, aiming, firing, reloading, fleeing, hit and dying (the top and bottom of the body each have their own) |
| **Gun crews** | The men round a gun: idling, walking it, getting it ready, firing and reloading |
| **Vehicles and guns** | Guns unlimbering and limbering, idling and firing, and other moving parts |
| **HQ figures** | The officers at the HQ table in a mission's scenes (played by no unit) |
| **Animals and scenery** | Cows, horses, goats, chickens, seagulls and windmills on the maps |

Each one says what the game calls it and how many units play it. On a unit's page, the actions are named for what the
unit does, grouped like this:

| Group | Its actions (some of them) |
|---|---|
| Standing still | Stands still, Crouches, Looks around |
| Moving | Walks, Walks backwards, Runs, Runs to the right, Runs backwards, Flees |
| Aiming and firing | Aims, standing; Aims while walking; Fires; Throws a grenade; Reloads |
| The heavy weapon | Aims the heavy weapon, Fires the heavy weapon, Raises the heavy weapon, Lowers the heavy weapon |
| Getting hit | Is hit, Is hit from behind, Is hit by a blast |
| Dying | Dies, shot; Dies in a blast; Lies fallen |
| Parachuting | Jumps out, Falls, Floats down under the parachute, Lands |
| A crew's actions | Waits, Walks forward with the gun, Goes to the gun, Sets the gun up, Fires (a crewman), Reloads the gun |

## Its animations: which one each action plays

A unit with animations of its own (a model on bones of its own: a horse, a horse and rider, any creature) has a table
on its page: **Look and moves**, the **Sounds and animation** row, **More**, then **Its animations**.

- **Stands still**, **Walks** and **Runs** come first: the least a model needs. If one has nothing of its own, the
  page says so, and what it plays instead.
- Each action has a list of the model's animations. Pick one, or leave it on the first line, **Nearest**: it then
  plays the closest one the model has, and the line says which. Nearest means, in this order: an animation named for
  that action (stand or idle, walk, run or gallop, fire, death...), else what the nearest action plays (a walk plays the
  run, a fire the aim or the stand). The game plays what the page says: the build uses the same rule.
- **Every other action** lists the rest, by group.
- **On long moves** is its last line. On a long trip by road the game puts a squad in its truck. A unit with
  animations of its own can go as itself instead, playing one of them on a loop (its run, when left on the first line),
  at its truck's speed. Pick **In its truck** to keep the truck.

A unit copied from one with animations of its own plays the same ones.

## Change an animation in RUSE Decoy

1. On the unit's page, in **Look and moves**, click **Change in RUSE Decoy** on the **Sounds and animation** row.
   RUSE Decoy opens on that unit: its sounds, then **Its animations** with every animation it plays. (Or open the
   **RUSE Decoy** tab and pick a kind under **Animations**.)
2. Click **Watch and change…** on an animation. It plays in 3D on a unit that plays it: drag to turn it, the wheel
   zooms. The 3D view needs the internet once.
3. Opened from a unit's page, the first line asks **Change it for**:
   - **Only this unit**: this unit plays its own copy of the animation, with your changes; every other unit plays it
     as before. It's picked to start with, unless the animation is already changed for every unit.
   - **Every unit that plays it**: the change goes to the animation itself, for every unit that plays it (the number
     says how many).
   - **Your copy** and its name: shown when this unit plays a copy of yours (below); it's then picked to start with.
4. Change it:
   - **Speed**: 100% is the game's, 200% twice as fast, 50% half as fast. Saved when you let go.
   - **Use instead**: another animation of the same body in its place (riflemen could run the way they flee).
   - **A bone**, with **Size**, **Turn about** and **Turn**: one part of the body made bigger, or turned, all along the
     animation.
   - **Motion capture**: a real person's movement in its place (see [[Music and sounds|Music-and-Sounds]]).
5. Click **Done**. Every change is saved in your mod at once, and goes into the game when you test or export it.

## A copy of an animation, for the units you pick

**Copy this animation…** makes a copy that only the units and soldiers you tick play: a run of your own for three of
your squads, say, and only the bazooka man of a fourth.

1. In the animation's window, click **Copy this animation…**, give the copy a name (only you see it), and click **Make
   the copy**. It starts as the animation looks now, and opens in the same window.
2. Change it as above.
3. Under **Who plays it**, tick the units that play the copy: **Your units** first, then **The game's units**. Under a
   unit with several soldiers or parts that play it, tick only some of them. **Find a unit** searches by name or
   country.
4. Nothing plays a copy until you tick a unit: the line under its name says "no unit plays it yet" until then.

Every copy is on RUSE Decoy's left under **Your copies**: open one there, or **Delete the copy**. A unit's own copy
(**Only this unit**) or an animation changed in Blender wins over a copy for that unit: the list says so beside it.

## Change a new unit's animations in Blender

For a new unit made in your mod (a game unit first needs a new unit made from it):

1. On the unit's page, click **Change in RUSE Decoy**. Above its animations, click **Change its animations in
   Blender**. Blender opens with the unit and every animation it plays, each named for what it does in it, with the
   game's own name after it: `Run, aiming (fusilier_course_vise)`.
2. At the bottom of Blender, the Action Editor lists them: pick one. **Space** plays it.
3. Click a bone, press **Ctrl+Tab** for Pose Mode, **R** to turn it (**G** moves it), then **I** to keep the pose at
   this frame. Do it at each frame you change: Blender goes from one kept pose to the next by itself.
4. Click **Send to the R.U.S.E. Studio** at the top of Blender's 3D view: every animation goes, changed or not.
5. In RUSE Decoy, click **Bring my changes back**. It says which came back changed: those are this unit's own now.
   Every other unit, and every animation you didn't touch, stays as it was.

Pose the bones only: don't rename them, delete them or move them in Edit Mode. The Studio then takes nothing in, and
says which bones.

A model on bones of its own (a horse, any creature) sends its own animations, under their own names. One you change
takes its place: every action that played it plays it changed.

## Get the game's animation back

| To take out | Click | Where |
|---|---|---|
| A change for every unit | **Back to the game's** | The animation's line in RUSE Decoy, or its window |
| This unit's own copy (**Only this unit**) | **Back to what every unit plays** | The animation's line on the unit's list, or its window |
| A copy's changes (its name and ticks stay) | **Back to the game's animation** | The copy's window |
| A copy, all of it | **Delete the copy** | **Your copies** |
| A change made in Blender | Undo it in Blender while that Blender is still open, then **Bring my changes back**: it's undone in your mod too | Blender, then RUSE Decoy |

The buttons above don't take out a change made in Blender.

## What Bring my changes back can tell you

| It says | What to do |
|---|---|
| "Changed in Blender, this unit's own now: ..." | Nothing: it worked. **Test in game** shows it. |
| "Every animation came back as it went out." | Nothing was changed. Did you keep each pose with **I**? |
| "Made in Blender, played by no action yet: ..." | A new animation isn't taken in. Save it in Blender (**File > Save**) to keep it. |
| "Not sent back (deleted or renamed in Blender), so they play as before: ..." | Name it back in Blender if you want your change in. |
| "These play on one half of the body only ... they may not show in the game" | The bones you moved belong to the other half: move the bones of the half that plays it. |
| "Bones made in Blender, which this unit's skeleton hasn't got ..." | A new bone can't be played; the rest came in. |
| "Blender's NLA editor plays these with timing of its own ..." | The game plays them as the Action Editor shows them. |
| "Blender's scene played at ... frames a second and the game plays at 30 ..." | Set Blender's frame rate to 30 to see the game's speed. |
| "Blender's scene has Time Stretching on ..." | Set Old and New to the same number to see the game's speed. |
| "No action of this unit plays these ..." | Pick one for an action under **Its animations** on the unit's page. |
| "Changed in the Studio since they went out to Blender, and sent back from Blender unchanged, so the Studio's change stays ..." | Nothing: your change in RUSE Decoy is kept. |
| "Changed in the Studio too since they went out to Blender: Blender's change takes the place of the Studio's ..." | Nothing, if Blender's change is the one you want; if not, make your change in RUSE Decoy again. |
| "Nothing new has come from Blender since your changes were last brought back." | Click **Send to the R.U.S.E. Studio** in Blender first. |

## What can go wrong

- **Nothing changes in the game:** a change for **Only this unit** plays only on that unit, and a copy only on the
  units ticked for it. A change made in Blender wins over a later change to the same animation with **Only this unit**
  or a copy, for that unit (the Studio's rule; not tried in the game yet).
- **"Only a new unit made in this mod gets animations of its own"**: the unit is one of the game's. Make a new unit from
  it first (**New unit from this one…** on its page).
- **Its animations is missing on the page:** the table is only for a unit with animations of its own (a model on bones
  of its own). Every other unit plays the game's: change them in RUSE Decoy.
- **A sending you never brought back:** opening Blender again sets it aside. RUSE Decoy shows it with **Bring back
  the set-aside sending** and **Put it in the Recycle Bin** (see [[Open in Blender|Open-in-Blender]]).

## What has been tried in the game

- RUSE Decoy's animation changes for every unit that plays them (Studio 0.9.8.8).
- **Only this unit**: a squad dancing on the spot while every other squad stood as before (November 2026).
- **Copy this animation…**: a copy played by one squad and by one soldier of another (November 2026).
- **Change its animations in Blender**: a squad standing and running with an arm raised, and Generic Horses holding
  their heads up (November 2026).
- The Generic Horse's own animations, picked by **Nearest**, and riding as itself on long moves (November 2026).
- Not tried in the game yet: a speed, a stand-in or a bone changed for one unit only, and another animation picked by
  hand under **Its animations**.

Still stuck? Ask on the [Discord](https://discord.gg/h54t5baNsC), or see [[When something goes wrong|When-Something-Goes-Wrong]].

**Next:** [[Open in Blender|Open-in-Blender]] · [[Models and bones|Models-and-Bones]]
