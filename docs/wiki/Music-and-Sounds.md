# Music and sounds

> **For:** modders · **You need:** RUSE Studio 0.9.8.8 or later, a mod; for a sound of your own a sound file (WAV,
> MP3, OGG or FLAC), for moves of your own a motion capture file (.bvh) · **Takes:** a few minutes each

Everything here is done inside the Studio, on the **RUSE Decoy** tab, the sound and animation designer (it took the
Music tab's place in Studio 0.9.8.8). No other program to install.

## Every sound in the game

**RUSE Decoy** lists every sound the game has, by kind, on the left: weapons near and far away, impacts and
destruction, engines and footsteps, surroundings, map backgrounds, the interface, ruse cards, unit voices, HQ and
intelligence, radio chatter, mission dialogue (with what each line says), music and jingles. The search box finds a
sound by its name or by the words said in it.

For each sound:

- **Play** hears it.
- **Volume:** drag it. 100% is the game's own, up to 200%.
- **Replace…** opens the editor below, to put a sound of your own in its place.

Changes are saved in your mod and go into the game when you test or export it.

## Replace a sound or a song

1. Drop a sound file on the editor, or choose one. Yours can be any length: the Studio makes it the game's format.
2. Cut it with the two handles, **Fade in** and **Fade out**, set the **Volume**, and hear it.
3. **Use this** saves it in your mod. Later, **Change…** opens it again and **Remove** puts the game's sound back.

## Add a song

Under **Music and jingles**, the songs are listed by where they play: the main menu, the credits, the three lists
battles play from, the end of a match, mission goals, and the campaign chapters and Operations that name them. The
three battle lists: a calm one while players build up, a fighting one once shots land, and ruse music when a ruse card
is played.

Under each battle list, **Add a song…**: give it a name, drop a sound file, cut it, then **Use this**. It joins the
songs the game plays from that list, marked New.

## Animations

Under **Animations**: how units move, from running, firing and reloading to dying and a gun's crew at work. Each says
what the game calls it and how many units play it. **Watch and change…** shows it in 3D on a unit that plays it (drag
to turn it, the wheel zooms; the 3D view needs the internet once):

- **Speed:** 100% is the game's, 200% twice as fast, 50% half as fast.
- **Use instead:** another animation of the same body in its place (riflemen could run the way they flee, for
  instance).
- **A bone**, with **Size** and **Turn about** / **Turn**: one part of the body made bigger, or turned, all along the
  animation (what's attached to it grows with it).
- **Back to the game's** takes every change to it out.

Which animation a unit plays for each thing it does, a change for one unit only, a copy for the units you pick, and a
new unit's animations in Blender: [[Unit animations|Unit-Animations]].

## Motion capture

Put a real person's movement on an animation, under **Motion capture**: pick a move from the motion library (3,205
free moves from the CMU motion capture database and 100STYLE, each downloaded when you pick it), or **Pick a motion
capture file…** of your own (.bvh, from Mixamo, Blender or any motion capture program).

1. Choose the part of it to use: **From** (in seconds) and **How long**. For a walk or a run, one whole step with each
   foot; for a death, start just before the fall.
2. **Keep on the spot** keeps walks and runs where the game moves the unit; **Make it loop** smooths the last pose
   into the first, for an animation the game plays over and over.
3. **Credit (who made the motion):** filled in for the library's moves; for any other file, write who made it and its
   licence. It goes wherever your mod goes.
4. **Watch it**, then **Use it**. Speed and bone changes still apply on top; **Back to the game's** takes it out.

## A unit's sounds and animations

A unit's page has a **Sounds and animation** row in **Look and moves**: its own voice lines and engine sounds, and its
animations. **Change in RUSE Decoy** opens RUSE Decoy on that unit's own (a building's page has its own **Sounds and
animation** box). A unit speaks the lines of its nation and kind, so a line changed there is heard from every unit
that shares it. Its guns and hits are under the weapons and impacts kinds.

## A map's background sound

On the **Maps** tab, **Background sound…** shows the map's: what it starts from, and its three layers, each heard and
replaced in the same editor. A map can also start from the background another map plays.

## What's been seen in the game

Seen in the game: RUSE Decoy's sounds and animations (Studio 0.9.8.8), the main menu song, the songs of battle lists 1
and 2, new songs added to them, and a unit's voice lines. Not tried yet: a map's background sound, and the ruse music
list (known from how the game works). RUSE Decoy's error messages are in English only for now.
