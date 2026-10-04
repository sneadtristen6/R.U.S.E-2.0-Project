# The big patch before 1.0 (DRAFT, not released)

What goes into the one big patch we make before 1.0 (not the 1.0 release itself), collected here as each part is
written: what it does and how. Nothing here is released yet; each part says where it stands.

## Music, sounds and campaign scenes

**Where it stands:** research and theory only (2026-10-04); nothing built, nothing tried in the game. The owner's
idea (PLAN §14 idea 8): new music for R.U.S.E. 2.0 and its Iwo Jima Operation for variety, different sounds for
units and buildings, and new campaign scenes. What follows is what the game's data says, and our best theory for each
open question, to be proved by one test copy. Format details: FORMATS §9.

**How it would work,** as the patch notes would say it:

**New music.** Mods can bring their own songs. Give the Studio a WAV file and it becomes a game track with a name of
its own: in battles it joins the calm, battle or ruse music (the game switches between those three as the fight goes);
in an Operation the mission plays it at the moment you choose, such as the landing or the victory. Only music you have
the rights to. *(Theory, not tested.)*

**Unit sounds.** A unit can have its own engine sound (running and idling; planes also diving) instead of the one its
kind shares, so a Tiger can roar like no Sherman. Shots, explosions and voices follow the same pattern: each is a
named sound that a mod can replace or point somewhere new. *(Theory, not tested.)*

**Building sounds.** Buildings react to what happens to them with effects: being built, damaged, destroyed, producing
(the smoke and the turning light) and captured. Building already has a sound, so the others can have sounds too: a
factory that hums while it makes a tank. A building given its own copy of those effects sounds different from the
rest. *(Theory, not tested.)*

**Map sound.** Each map has its own background sound. Iwo Jima can borrow what the game already has: the swamp
ambience and the volcano. *(Not tested.)*

**Campaign scenes.** Three kinds, all made by a mission: a camera flight with black bars, dialogue and music, made in
the game itself (missions of ours already play); a full-screen film; and a small film during the mission, a wide strip
or a tall panel. Films are made in Blender, which writes the game's exact video format. *(Films: theory, not tested.)*

**The theories, and why we think so** (the one test copy checks all of them):

1. **A new track needs its sound file and a small description file beside it.** The game reads the description
   (sample rate, channels, length, file size) before the sound, and a name without one stays silent rather than
   crashing. We know every field of it, so the Studio writes both. Expected: the new track plays in full.
2. **A replaced song may need its description updated too.** The song itself plays from its own header, but the
   description gives a read size and a length. The community song that replaced the menu music kept the old
   description and **works in the game** (owner, 2026-10-04). Still open: does it play to its end (4:08) or stop at
   the old track's length (about 2:55)? If it plays to the end, replaced songs need no description update. The
   Studio updates it anyway.
3. **A film from Blender plays.** The game's own films were made with FFmpeg 7, the same video library Blender uses,
   and our test film has the same layout. The game's player takes one VP9 video track, at most 30 frames a second,
   and Vorbis sound; one sound track plays in every language. Expected: plays, as long as the film keeps one of the
   game's shapes (1280×544 full screen, 1280×200 strip, about 416×720 panel) and 30 frames a second or fewer.
4. **A building's effects can carry a sound.** Construction does it already, through the same effects table that
   holds production, damage and capture. Expected: a sound added to the production effect plays while a factory
   works, and only for buildings given their own copy of the table.
5. **Sound effects carry a loudness track** (five levels for every 2048 samples) that music doesn't have. What the
   game uses it for isn't known; the Studio would measure it from the sound itself. Expected: no audible difference
   if it's only approximate.

**The test copy (when it's built):** a 30-second song added to the battle music and played by a mission; the menu
music replaced by a longer song with its description updated; a 5-second Blender film shown during the mission (strip
shape); a factory with a sound on its production effect. One game start answers all five.
