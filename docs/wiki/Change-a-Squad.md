# Change a squad

> **For:** modders · **You need:** RUSE Studio, a mod, and Blender (free) to change soldiers in Blender ·
> **Takes:** a few minutes

Make the American GIs look like Marines, or give one soldier a look of his own. A squad's page starts with its
soldiers: the squad card at the top, then a line for each soldier.

## 1. Your own squad

In the **Units** tab, pick a squad (**Infantry**, the US rifle squad, say). Its card says what it is made of:
"5 soldiers: 4 riflemen with rifles, 1 bazooka man with a bazooka". The game's own squads aren't changed: click
**New unit from this one…** on the card, give your squad a name and click **Create**. Its page opens on its card.

## 2. The whole squad in Blender

1. Click **Change the squad in Blender** on the card. Blender opens with every soldier of the squad side by side. No
   Blender yet? **Get Blender (free)** installs it; **Choose Blender…** shows the Studio where it is.
2. Change any soldier: his shape, his colours, his gear. Each soldier has his own copy of his pictures, so painting
   one changes only him.
3. Your own helmet, backpack or bazooka on one soldier: **File > Import** it, put it on him, click it, **Shift+click**
   his bones, then **Ctrl+P > With Automatic Weights**.
4. Click **Send to the R.U.S.E. Studio** at the top of Blender.
5. Back in the Studio, the big button now reads **Bring my changes back**: click it. Each soldier gets only what was
   done to him, and the card says who changed and who didn't.
6. Click **Test in game** to see them.

The game gives the US rifle squad's four riflemen one model: in Blender they are one figure, and what you do to it,
all four wear. The bazooka man is a figure of his own.

## 3. One soldier from a model file

Under **Each soldier**, every soldier has a line: his picture, his name and how many there are ("Rifleman ×4"), and
what he fires.

- **Import a model…** gives him a model from a file made in Blender on the game soldier's bones, or a model with bones
  of its own (a horse and rider). The others keep theirs.
- **Back to the game's look** takes his model out of your mod again.

## Good to know

- **More options**, under the soldiers, says where your mod keeps each soldier's model and your Blender files;
  **Show in folder** opens the folder.
- Closed Blender before you brought your changes back? The small **Bring my changes back** under the big button takes
  what you sent last.
- The squad's uniform is in **Look and moves**, beside the values: **Custom uniform** gives the squad a uniform of its
  own that **Repaint in Blender** paints for every soldier at once. A squad wears either your models or a uniform.
- Not tried in the game yet: the whole squad in one Blender, each soldier brought back on his own. Adding and removing
  soldiers isn't in the Studio yet.

More about models, bones and animations: [[Import a model|Import-a-Model]].

**Next:** [[Export and share|Export-and-Share]]
