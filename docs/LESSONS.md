# What went wrong on the bridges, and the guards that come out of it

Written 2026-10-01, after nine hours on one bug: units would not stay on a new bridge. The owner asked for an honest
account of why it took that long. The point of it is the guards at the end: a mistake that can repeat gets a check in
the code or the tests, not another rule to remember ([[guards-not-rules]]).

## The shape of the night

Five rounds, each one a build, a game test by the owner, and a fix:

| round | what we changed | what the game said |
|---|---|---|
| 1 | deck circles 2,560 wide | a tank stepped off the side into the river |
| 2 | deck circles 1,280 wide | units walked off the side and under the deck |
| 3 | an owner circle with a local map, deck circles 640 | units still in the river |
| 4 | no owner, plain deck circles 640; floor widened to 950 | the tank was fixed; infantry still in the river |
| 5 | blocks stopped shrinking the map's own owner circles | still being tested |

Three real bugs were found and fixed in rounds 3 to 5, and one of them (round 5) had nothing to do with bridges: any
mod that placed a building was damaging the map's own movement, including the water beside the game's own bridges.

## Why it took so long

**1. I built the big thing before the small thing.** The first research gave two options: give each new bridge its own
"local map" the way the game's bridges have one, or simply make the deck's circles narrower than the floor. It even
called the second one the cheap alternative, worth trying first because it would tell us whether width was the whole
problem. I built the first one. It was five hundred lines, it renumbered every circle in the file, it needed four new
checks to be safe, and it did not fix the bug. The narrow deck was about thirty lines, went in at round 4, and fixed
the tank immediately. **Three rounds of the owner's time went on the elaborate answer before the simple one was
tried.**

**2. I trusted my own model of the game over the owner's screenshots.** After round 3 the file said, correctly, that
no unit could stand on that water. The owner's picture said one was. I spent a long time re-measuring the file to
prove the picture wrong instead of asking what else could put a unit there. The file was right and useless: it
described where units may walk, not where they end up when something pushes them.

**3. I read the screenshots carelessly.** At round 4 the owner said a shot was of a normal bridge. I took that to mean
"the game does this too, so it is not our bug", wrote that up, and moved on. He meant the opposite: look at the
difference between the game's bridge and ours. His next two words ("look at diff") were the whole answer, and they led
straight to the round 5 bug, which was ours, serious, and nothing to do with bridges. **I had put a comfortable
reading on an ambiguous sentence** instead of doing the comparison that would have settled it. The comparison took
four minutes once I did it.

**4. I asked him to do my work.** Twice I stopped and asked which bridge he had tested, when I could have told the two
apart myself from the build report and the map. He had already sent the pictures. An hour earlier I had also asked him
to confirm something the file could answer. Every one of those questions cost him more than it cost me.

**5. I did not diff against the game until round 5.** The one tool that found the serious bug was: build the copy,
read the same file out of the game, and compare them. That is cheap, it needs no in-game test, and it should have been
the first thing after every build. It found two of the map's own local maps changed, its largest movement circle
emptied, and 961 places opened beside its own bridges, in about four minutes.

## The guards

Written as checks, not resolutions.

1. **A build must not change the map's own movement outside what the mod asked for.** `tests/test_nav.py` now has the
   case for the round 5 bug: a block may never shrink a circle that owns a local map. The build already refuses to
   write a graph in more pieces than it found; this is the same idea for the map's own structures.
2. **Diff the built file against the game's as part of the build check, not by hand.** The probe that found it lives in
   a scratch script. It belongs in `rusemod.mapcheck` as a check the Studio can run: *what did this build change that
   the mod did not ask for?* That is the next piece of work on the map check.
3. **Try the cheap option first, and write down why when not.** The bridge research named the cheap option. If a
   design note offers two and the expensive one is chosen, the reason belongs in the commit message, where the owner
   can object before the work is done rather than three rounds later.
4. **An in-game test is the scarcest thing we have.** One test per round, and the owner is the only one who can run
   it. Before asking for one: say in writing what the test will show if it passes and what it will show if it fails.
   Rounds 1 to 3 each spent a test on a change I could not have described that way.
5. **When a picture and the file disagree, the file is describing something else.** The file says where units may
   walk. It does not say where they are. Write down which question a measurement answers before using it to argue with
   what someone saw.

## Round 6: the cause, found by measuring the game's own bridges instead of guessing

The owner's two sentences were the whole diagnosis: "they are in water, not like vanilla" and "vanilla ruse they
float". Five rounds had changed where units may *walk*. The fault was in what they *stand on*.

- Where a unit is comes from the movement file. How high it stands comes from the floor under that point. Nothing in
  the game ties the two together.
- A tank is one point. An infantry squad is five men on an arc 2,828 wide (the game data's `Dispersion 500` for
  `NbSoldatInGroupeCombat 5`), and each man is put on the floor under his own feet. Only the squad's own point is
  ever tested against the movement file. So beside a deck 640 wide, two of the five men are 2,054 from its line, and
  a man who has drifted to the squad's limit (`DispersionMax 620`: 2,480) is 3,120 out.
- The game's metal bridges carry, beside the deck's band, two flat aprons the length of the band and 12,000 to 17,000
  wide. Its infantry stand on those, at the deck's height, over open river: they float. Our copy of a bridge's floor
  kept only triangles within 2,500 of the deck's line (`floors.ACROSS`), which threw the aprons away. Our men had the
  riverbed, 2,000 below the water.
- The game's own stone bridges have no apron, and its infantry stand in the river beside those too.

So rounds 1 to 3 narrowed something that was already narrower than the game's own, and round 3's local map could
never have helped: it changes where a squad may go, not where its men stand. The fix is in `rusemod.floors` (`apron`): a new bridge's floor reaches 3,200 either side of its line, over water only.

**6. The measurement that would have found it on the first night was never made.** We measured where units may walk
five times. We never measured, for one unit standing where the owner's screenshot showed it, *what it was standing on*
in our build and in the game's, until round 6. That comparison takes a minute and shows +750 against -2,000.

**7. When the same fix fails three times, the model is wrong, not the fix.** Rounds 1, 2 and 3 were the same idea
(narrow the movement) at three levels of effort. After the second failure the next step should have been working
out how the game places a unit, which is what round 6 did, not a third and more elaborate narrowing.

**8. One conversation ran in two windows.** For part of the night the desktop app and VS Code were both open on this
conversation, each with agents editing the same folder. Work was redone and reviews went stale under their reviewers.
One window at a time; a second window gets its own conversation.

More guards:

6. **The build checks a new bridge the way the game uses it**: `tests/test_floors.py` places a squad's men beside a
   deck and requires floor under every one who is over water. The offline check before any in-game test does the same
   on the real map (the formation check) and compares with the game's own bridges.
7. **Before a test, write what the test will look like if the fix is right** (guard 4), *and measure that same thing
   in the game's own data first*. If the game's own bridges do not pass the check either, the check is measuring the
   wrong thing.
