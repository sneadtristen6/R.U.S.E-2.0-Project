# Open in Blender

> **You need:** RUSE Studio 0.9.8.20 or later, a mod, and Blender (free) · **Takes:** 5 minutes to read

**Open in Blender** takes a unit into Blender, the free 3D program, to change its shape, its bones or its paint;
**Bring my changes back** puts what you did there into your mod. It's one button for the whole unit: **What goes to
Blender** beside it says what goes, and anything you untick stays as it is. This page goes through it step by step.

Animations aren't changed with this button: they're changed in RUSE Decoy (see [[Unit animations|Unit-Animations]]).
A model's own animations go to Blender with it and come back with it.

## Where the button is

| The unit | Where | What comes back |
|---|---|---|
| A squad you made (a new unit of your mod) | The big **Open in Blender** on its card, at the top of its page | Its soldiers, each on his own; their paint |
| Any other unit you made (a tank, a plane) | **Look and moves**, the **Model** row, **More**: the box **Change it in Blender** | Its whole model (its bones too, when they're its own), its paint |
| One of the game's units (not a squad) | The same box | Its paint only: paint on it, the rest stays the game's |
| One of the game's squads | Its card says to make a new unit from it first: **New unit from this one…** | Its **Custom uniform** only, painted from its **Uniform** row (**Open in Blender**, then **Bring back**) |

No Blender on this PC? The page shows **Get Blender (free)**, which opens Blender's download page, and **Choose
Blender…**, to show the Studio where `blender.exe` is if you have it already.

## What goes to Blender

Click **What goes to Blender ▾** beside the button. Everything is ticked to start. Untick a part to keep it as it is:
**Bring my changes back** then leaves it as it was, whatever Blender did to it.

| You see | It means |
|---|---|
| **Its soldiers**, then each soldier ("Rifleman 1", "Bazooka man 5"...) | The soldiers ticked open side by side in one Blender. Change any of them: only the one you change changes. |
| **Which model:** **The riflemen's model** or **The heavy-weapon soldier's model** | A squad on bones of its own (the Generic Horse): one model at a time, with its bones and its animations. |
| **Its model** | The unit's shape (a unit that isn't a squad). |
| **Its bones** | Its bones (a model on bones of its own only). Unticked, your mod's bones are put back as they were. |
| **Its paint** | Its pictures. Unticked, your mod's pictures are put back as they were. |

Good to know:

- **Its paint alone** (its model, or every soldier, unticked): Blender opens with the pictures to paint on, and only the
  paint comes back. That's how a squad's **Custom uniform** is painted, for every soldier at once. A squad wearing the
  default uniform can't: "Pick Custom uniform first" (the default uniform is worn by other squads and crews too). Pick
  **Custom uniform** on its **Uniform** row, in **Look and moves**, first.
- **Its bones** unticked, but a bone was added, removed or renamed in Blender: the bones can't be kept, so they come
  back as Blender sent them, and the Studio says so.
- A squad of game soldiers has no **Its bones**: its soldiers come back on the game soldier's bones whatever Blender did
  to them.
- Nothing ticked: the Studio says "Tick what goes to Blender first: the model, its bones or its paint."

## The round trip, step by step

1. **Open it.** Click **Open in Blender**. Blender opens (it takes a few seconds), with what you ticked.
2. **Change it.** Paint, reshape, put a model of your own on a soldier's bones (see
   [[Models and bones|Models-and-Bones]], "Weights"). The few things to know are written at the top of Blender's 3D view.
3. **Send it.** Click **Send to the R.U.S.E. Studio** at the top left of Blender's 3D view.
4. **Bring it back.** In the Studio, the button now reads **Bring my changes back**: click it. The page says what came
   in: who changed and who didn't on a squad, the model's file on any other unit, and what unticked was kept.
5. **Test in game** shows it.

You can keep Blender open and go round again: change, send, bring back.

## Bring my changes back

- **Blender still open?** **Bring my changes back** asks it to send first, and waits for it (up to a minute).
- **Closing Blender?** Click **Send to the R.U.S.E. Studio** before you do: what you didn't send stays in Blender, and
  the Studio never sees it.
- **Closed it after sending?** The button keeps reading **Bring my changes back** until you click it, and it takes what
  you sent last. On a squad's card, a sending that came after your last bring-back (or after **Add a soldier**) shows
  as a small **Bring my changes back** under the big button, once Blender is closed: it takes what you sent last.
- **Nothing sent yet:** "Nothing has come back from Blender yet: in Blender, click Send to the R.U.S.E. Studio at the
  top, then Bring my changes back here."
- One Blender at a time for a unit: while Blender has it, the Studio's button reads **Bring my changes back**.

## A sending set aside

A **sending** is what Blender sent with **Send to the R.U.S.E. Studio**. If you open Blender again before bringing the
last sending back:

- **A squad:** that sending is set aside in your mod's Blender folder, in a folder named `sent-not-brought-` and the
  date and time, and the new Blender starts from what your mod has. Nothing is lost, but the card doesn't say it yet,
  and it has no button to bring it back: the files are in `Documents\RUSE 2.0\Mods\<your mod>\blender\<the unit's
  name>\squad\`.
- **Any other unit, its model ticked:** nothing is set aside: the next **Open in Blender** starts from what you sent
  last.
- **RUSE Decoy's animations:** each sending set aside is listed above the unit's animations ("Sent from Blender, never
  brought back, set aside on ..."), with **Bring back the set-aside sending** to take it in, or **Put it in the Recycle
  Bin**.

## Where your Blender files are

In your mod's folder, `Documents\RUSE 2.0\Mods\<your mod>\blender\<the unit's name>\`: the squad's in `squad`, RUSE
Decoy's in `animations`. They aren't packed into your mod when you export it. On a squad's page, **More options** says
where they are, with **Show in folder**.

## What can go wrong

| What happens | Why, and what to do |
|---|---|
| Blender opens with nothing | Look in Blender's own window for an error (**Window > Toggle System Console**), and tell us on the Discord. |
| A soldier I didn't touch shows as changed | Anything that differs counts as changed, a renamed object too. His look stays as it was. |
| "Not on any soldier, so not sent: ..." | Something you brought into Blender isn't on a soldier's bones or in his collection: put it on him, then send again. |
| A point of my model moves with the hips only | It has no bone: see [[Models and bones|Models-and-Bones]], "Points with no bone". |
| Parts lost their shine or side colour | The page names them: a material renamed or new in Blender comes back plain. Keep the material names Blender opened with. |
| My game unit's new shape didn't come back | On one of the game's units, only the paint comes back. Make a new unit from it to change its shape. |

## What has been tried in the game

- Paint from Blender on a unit, seen up close and from far.
- A squad opened in Blender, one soldier changed and brought back on his own (November 2026).
- Not tried in the game yet: a tank's whole model through Blender, and what **What goes to Blender** keeps (tried with
  Blender and the Studio, outside the game).

Still stuck? Ask on the [Discord](https://discord.gg/h54t5baNsC), or see [[When something goes wrong|When-Something-Goes-Wrong]].

**Next:** [[Change a squad|Change-a-Squad]] · [[Models and bones|Models-and-Bones]] · [[Unit animations|Unit-Animations]]
