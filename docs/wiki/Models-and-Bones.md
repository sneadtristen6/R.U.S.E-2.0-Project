# Models and bones

> **You need:** RUSE Studio 0.9.8.20 or later, a mod with a new unit in it, and Blender (free) to change bones ·
> **Takes:** 10 minutes to read

Soldiers, horses and any creature move in R.U.S.E. because their 3D model has **bones**. This page says what bones
are, how the game uses them, and what every box about bones on a unit's page means and what to do with it. A tank
turns its turret and wheels without animations, so most of this page is about soldiers, horses and creatures.

## What bones are

- A **model** is a shell made of points, with pictures painted on it.
- Inside it, like a skeleton, are **bones**: an upper arm, a forearm, a hand, the head, each leg of a horse. Each bone
  hangs from another one (the hand from the forearm, the forearm from the upper arm), back to the first bone.
- Each point of the shell follows a bone, or a few: the points of a sleeve follow the arm. How much a point follows
  each bone is its **weight**.
- An **animation** moves the bones, frame after frame, and the shell follows them. That's how a soldier walks, aims
  and falls.
- In Blender, a model's bones are one object called an **armature**.

## How the game uses them

- The game moves a model's bones **by their place in its list of bones**, not by their names. So an animation made for
  one model only fits a model with the same bones, in the same order.
- Some bones have a job: a shot starts from a bone at the weapon's muzzle, the upper body turns toward its target at
  a bone of the spine, a weapon is shown and hidden on a bone, a turret or a wheel turns on one. The unit's page names
  each one your model is missing (see **Will it work in the game?** below).
- A soldier plays **two animations at once**: one on the upper half of his body (aiming, firing) and one on the lower
  half (walking, running). A horse and its rider do too: see **Its two halves** below.
- The game hasn't been seen animating a model with more than 64 bones.

## Two kinds of model

| | On the game soldier's bones | On bones of its own |
|---|---|---|
| **What it is** | A soldier changed in Blender, or a model of your own put on a soldier's bones | A horse, a horse and its rider, any creature, made in Blender on bones of your own |
| **How you make it** | **Open in Blender** on the squad's card: each soldier opens with his bones (see [[Open in Blender|Open-in-Blender]]) | In Blender, then **Import a model…** on a soldier's line, under **Each soldier** (see [[Import a model|Import-a-Model]]) |
| **Its animations** | The game's, as the soldier's | Its own, from its file |
| **Its two halves** | The game's own: nothing to choose | You pick them (the Studio suggests the bone) |
| **Its size and place** | As you made it in Blender, on his bones | As in its file |

The page says which one it is. On a model on the game soldier's bones: "Your model is on the game soldier's bones, so
it keeps the game's own two halves: nothing to choose." On a model on bones of its own: "It has bones of its own:" and
how many. The **Generic Horse** (**Units** tab, **WWII+**) is a squad on bones of its own: see
[[Units from other eras|Units-From-Other-Eras]].

## Where the page shows them

On a new unit's page, everything about bones is in **Look and moves**:

| Box | Where | What it tells you |
|---|---|---|
| **Its bones and animations** | The **Sounds and animation** row, **More** | How many bones the model has, and each animation with its length and how many of the unit's actions play it (a model on bones of its own) |
| **Its two halves** | The **Sounds and animation** row, **More** | Where the model splits into its upper and lower halves |
| **Its animations** | The **Sounds and animation** row, **More** | Which animation the unit plays for each thing it does: see [[Unit animations|Unit-Animations]] |
| **Will it work in the game?** | The **Model** row, **More**; on a squad's page, **More options** under the soldiers, then **Each soldier's model** | What in the model could stop the game or look wrong, and how to fix it |
| Points with no bone | The same place as **Will it work in the game?** | How many points of the model follow no bone |

## Its two halves

The game plays two animations on a soldier at the same time: one on his **upper half** (aiming, firing) and one on his
**lower half** (walking, running). A rider aims and fires while his horse runs: the rider is the upper half, the horse
the lower half.

- A model on the game soldier's bones keeps the game's own halves: the page says "nothing to choose".
- A model on bones of its own splits at **one bone**: that bone and every bone under it make the upper half, all the
  other bones the lower half.

To choose it:

1. On the unit's page, in **Look and moves**, click **More** on the **Sounds and animation** row.
2. Under **Its two halves**, the list **Upper half starts at** shows the Studio's suggestion first, marked
   "(suggested)". The Studio suggests the rider's first bone on a horse with a rider (**bip01** on the Generic Horse),
   else the first bone named spine (a soldier's way), else the bone where the skeleton first branches.
3. Most models are right with the suggestion: leave it. To change it, pick another bone in the list. It's saved at
   once, and shows in the game after the next build (**Test in game**).
4. Under the list, the page counts the bones of each half, and **Which bone goes where** lists every bone of the model,
   each marked upper half or lower half.
5. To go back to the suggestion, pick the first line of the list again.

Another split than the suggested one hasn't been tried in the game yet.

## Weights: which bone each point follows

When you put a model of your own (or a helmet, a backpack, a weapon) on a soldier's bones, Blender has to know which
bone each of its points follows. These are Blender's own steps.

**Your own model on a soldier, each point following the bones nearest to it:**

1. On the squad's card, click **Open in Blender**: Blender opens with the soldiers, each on his bones.
2. In Blender, **File > Import** your model and place it over the soldier.
3. Click your model, then **Shift+click** the soldier's bones: the bones last.
4. Press **Ctrl+P** and pick **With Automatic Weights**. Blender works the weights out for you.
5. Delete what you don't keep (the game soldier's own shape, if your model takes his place), but keep his bones.
6. Click **Send to the R.U.S.E. Studio** at the top of Blender's 3D view, then **Bring my changes back** in the Studio.

**A stiff part that follows one bone only (a helmet on the head):**

1. In Blender, click the helmet, then **Shift+click** the soldier's bones.
2. Press **Ctrl+Tab** for Pose Mode, and click the head bone.
3. Press **Ctrl+P** and pick **Bone**. The helmet now moves with the head, and only he gets it when you bring your
   changes back.

**Points with no bone.** Blender's automatic weights miss a few points now and then. The page then says "{n} point(s)
of your model have no bone, so they move with the soldier's hips only." To fix it:

1. **Open in Blender** again.
2. Click your model, then switch Blender's mode (top left of the 3D view) from **Object Mode** to **Weight Paint**.
3. In the model's properties (the green triangle), **Vertex Groups** has one group for each bone: pick the bone those
   points should follow.
4. Paint over the points.
5. **Send to the R.U.S.E. Studio**, then **Bring my changes back**.

## Will it work in the game?

The Studio checks a model on bones against the animations it plays and against the parts and shots of the unit it
copies. Building the mod checks again, with all your changes. A problem never stops you: it says what will happen,
and how to fix it.

**Where:** a new unit's page, **Look and moves**, the **Model** row, **More**. On a squad's page: **More options**,
under the soldiers, then **Each soldier's model**.

When all is well, it says: "Nothing found that would stop the game: every animation it plays has its bones, and every
bone its parts and shots need is there." (with how many bones).

### What each answer means

Each problem says three things: what doesn't fit, what the game does with it, and how to fix it. The middle line is
one of these:

| The page says | What it means | What to do |
|---|---|---|
| This can stop the game: it did in a test. | The game stopped like this in one of our tests. | Fix it before you test. |
| This can stop the game (not tried in the game yet). | It's expected to stop the game. | Fix it before you test. |
| The game plays it, but it will look wrong (not tried in the game yet). | The wrong bones would move. | Fix it, or test it and look. |
| The unit still fights, but its shots won't be seen: that happened in a test. | It does damage, but no shot shows. | Add the bone the page names. |
| Not tried in the game yet: the game may not animate it. | More bones than the game has been seen to animate. | Join or delete bones. |
| It still works, but it may not be what you want. | A note about its two halves. | Check **Its two halves**. |

### Each problem and its fix

**Animations that don't fit the model's bones.** The page says how many animations, for how many actions, and why
they don't fit: "They move {a} bones and your model has {b}." (or "only {b}"), or the same number of bones "named
differently", or "in another order". Those animations were made for other bones.

- If the unit plays the game's animations on your model: give those actions animations of your model's own. **Import
  model…** brings in every animation in your model's file, and you pick which one each action plays under **Its
  animations** ([[Unit animations|Unit-Animations]]).
- If they're your model's own animations, made for another model: make them again in Blender on this model's bones,
  then import the model again.

**A bone the unit needs.** For example: "Riflemen: shots start from a bone called Fx_Tir_01, and your model hasn't got
one." (or: the upper body turns toward the target at it, a weapon is shown and hidden on it, a part is held on it, a
turret or a wheel turns on it, the body rests on it, a towed gun hooks on at it). To add the bone in Blender:

1. Open the model in Blender: **Open in Blender** with **Its bones** ticked (see [[Open in Blender|Open-in-Blender]]),
   or your own Blender file.
2. Click the bones (the armature) and press **Tab** for Edit Mode.
3. Press **Shift+A**: a new bone appears where Blender's 3D cursor is.
4. Press **F2** and type the name the page says, exactly (for example `Fx_Tir_01`). If your model has the bone under
   another name, rename that one instead.
5. In the bone's properties (the bone icon), under **Relations**, set **Parent** to the bone the part moves with: for a
   shot, the bone the weapon moves with.
6. Press **G** and move the new bone to where the part belongs: for a shot, the end of the weapon's barrel.
7. Press **Tab** again, click **Send to the R.U.S.E. Studio**, then **Bring my changes back** (or export your own file
   and click **Import another…**). **Will it work in the game?** checks the model again.

**Too many bones.** "Your model has {n} bones. The game isn't seen to animate a model with more than 64." In Blender,
join or delete bones until it has 64 or fewer, then bring the model back.

**The split.** "The split at {bone}, your model's first bone, puts every bone in the upper half, so the lower half's
animations (walking, running) move nothing.": pick a bone further down under **Its two halves**, where the upper body
starts. "The bone you chose for the split, {bone}, isn't in your model any more, so it splits at {used}.": pick the
bone again.

**A squad's second model on other bones.** "His model is on bones of its own that aren't your riflemen's model's, so
he plays what he played in the unit it copies, made on the game soldier's bones: that can stop the game." A
heavy-weapon soldier's model has to be on the same bones as the riflemen's model to play their animations: make his
from the riflemen's model in Blender, then import it on his line. Taking the riflemen's model out takes his out too.

## Make a model with bones of its own in Blender

1. **Its bones:** your model on an armature with bones of your own, named as you like, and its weights
   (**Ctrl+P > With Automatic Weights**, above).
2. **Its animations:** an action for each animation (Blender's **Dope Sheet > Action Editor**). Name each one for what
   it shows: **stand** (or **idle**), **walk** and **run** (or **gallop**) at least; **fire**, **aim**, **reload**,
   **hit**, **death**, **crouch**, **look**, **flee** and **grenade** are known too. A name like **t_fire** (or
   **hr_t_fire**) plays on the upper half only, and **b_run** (or **hr_b_run**) on the lower half only: a rider's and his
   horse's.
3. **Export it:** **File > Export > glTF 2.0**, format **glTF Binary (.glb)**, with **Animation** ticked.
4. **Import it** on a new squad: see [[Import a model|Import-a-Model]], "A model with its own bones and animations".
5. **Check its page:** **Its bones and animations** (every animation came in, and how many actions play each), **Its
   two halves**, **Its animations**, **Will it work in the game?**
6. **Test in game.**

Changed it in Blender later? Import it again: each action keeps its animation while an animation of that name is still
in the file.

## What has been tried in the game

- The Generic Horse, made this way (riflemen and a bazooka man on horses, a model on bones of its own): firing, riding
  as themselves on long moves, each horse falling with its rider (November 2026).
- A squad's soldier changed in Blender on the game soldier's bones, with points weighted there (November 2026).
- Not tried in the game yet: another split than the suggested one, and each problem the page marks "not tried in the
  game yet".

Still stuck? Ask on the [Discord](https://discord.gg/h54t5baNsC), or see [[When something goes wrong|When-Something-Goes-Wrong]].

**Next:** [[Unit animations|Unit-Animations]] · [[Open in Blender|Open-in-Blender]]
