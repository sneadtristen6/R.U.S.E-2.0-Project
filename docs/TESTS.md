# In-game tests

The checks only the game itself can answer. Each one decides a release, so they're the project's bottleneck:
**DomesticNukes, if you can take any of these, please do** (the owner's request, PLAN.md §10). Anyone with the game
and this repo can run them.

**Rules for every test**
- Only ever in a **modded copy** (`--instance` below): a folder of links to your game plus the changed files. Your
  Steam install is never changed. A copy on the game's drive costs almost no disk space.
- Steam must be running. Start `RUSE.exe` **inside the modded copy's folder**.
- Stop at the first failure. Report what you did, what you saw, a screenshot, and the copy's build output. Post it
  in the Discord or open a GitHub issue.

**Setup, once:** Python 3.11 or newer (<https://python.org>), then in a terminal at the top of this repo:

```
set PYTHONPATH=src
py -3 -m rusemod detect
```

`detect` should find your game and its build. In the commands below, `D:\RUSE-Instances` stands for any folder on the
same drive as your game.

## T1. Placing scenery (the Studio's Place tool; Studio 0.6)

```
py -3 -m rusemod build examples\blitz-scenery-test --instance D:\RUSE-Instances\scenery-test
```

Play **Blitz**. Around the town in the middle of the map, look for a ring of **8 water towers**, bigger than normal,
and **12 big oaks** further out.
- **Pass:** they stand on the ground, close up and from far away. The map loads and plays normally.
- **Report:** anything missing or floating, anything fading out, the game running out of memory, or a crash.

## T2. Water brushes (DomesticNukes' pull request #11)

Check out the branch `domesticnukes/water-brushes`, then build its example:

```
py -3 -m rusemod build examples\blitz-water-test --instance D:\RUSE-Instances\water-test
```

Play **Blitz**. Look for a new lake in the dry basin in the north-west hills, and check that the lake north-east of
Cashel is gone.
- **Pass:** both look like the game's own water, close up. The new lake isn't drawn from far away yet.
- **Report:** dark or flat water, water where the ground is higher, or water missing.

## T3. Community `.rmod` mods through our build (LittleGroove's engine)

`.rmod` files are community mods (not in this repo). For each one, build it alone and play a skirmish:

```
py -3 -m rusemod build "D:\path\to\Passable_Forests_V1.rmod" --instance D:\RUSE-Instances\rmod-test
```

Try these five, each changes something different:
1. **Passable Forests:** tanks can drive into forests.
2. **Navy Mod:** adds 21 textures and changes a script (the build warns about the script; that's expected).
3. **Argonne Forest:** forest cover on 31 maps.
4. **Pinnacle Map Pack:** its maps and scenarios.
5. **RCRBM 2:** made for an older version of the game (compat-2), moved to yours by the build.

- **Pass:** the game starts, the mod's change shows, and a skirmish plays to the end.
- **Report:** the build's warnings if the game crashes or the change doesn't show.

## T4. A reshaped hill (terrain brushes; pull request #6)

```
py -3 tools\verify_terrain.py --make-test TwoIslands D:\RUSE-Instances\hill
```

Play **Centre of Gravity** (Two Islands) and find the hill.
- **Pass:** the hill is drawn close up and from far away, tanks drive up it, move orders onto it work, and the camera
  behaves normally over it.
- **Report:** if move orders into the area are refused, the camera jumps, or the ground looks torn.

## T5. A new unit made in the Studio (Studio 0.5)

Run `py -m pip install pywebview` once, and `py -3 -m rusemod index build` once per game build. Then open the
Studio with `py -3 -m ruse_studio`.
1. Make a mod.
2. Open the **M4 Sherman** and click **New unit…**.
3. Name it "Sherman Test", set price 5, and put it in the US armour factory.
4. Click **Test in game**.
- **Pass:** it's in the US armour factory, costs 5, and gets built and fights.

## T6. Placing scenery from the Studio

1. In the Studio's **Maps** view, pick a map and a mod.
2. Under **Place on the map**, pick a building, click **Place**, then click the ground a few times.
3. Click **Test in game**.
- **Pass:** the objects stand where they were placed (turned and sized as set).

## T7. The launcher: mod sets, sharing and importing (launcher 0.2)

Install RUSE Launcher 0.2.0 from [Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher)
(or run `py -3 -m ruse_launcher` from the repo).
1. Click **Add a mod file…** and add a `.rmod`. Then make a mod set with it and press **Play**.
2. On the set, click **Share**. Then use **Import a load order…** with that text.
- **Pass:** the mod works in-game, and the imported set has the same mods in the same order.
- **Extra:** a load order copied from RUSE Mod Manager imports too.
- **Extra, when 0.2.1 is out:** the launcher offers it; **Update** installs it and the launcher starts again.
- **First report (DomesticNukes, 2026-09-29):** 12 `.rmod` mods in one set built with 0 errors and the game started,
  then failed. His suspect: No Fog of War. Next: the same set without it, then No Fog of War alone.

## T8. Bridges where new roads cross water (Studio 0.7.4)

The copy: `D:\RUSE-Instances\bridges` on the owner's PC (the Studio mod `test`), or build one from a mod whose
`maps/M04_cotentin/roads.toml` crosses the river:
`py -3 -m rusemod build <the mod's folder> --instance D:\RUSE-Instances\bridges`. In the game: **BATTLES > D-Day**.
The two new bridges stand where the new roads cross the river, between Briqueville and Les Pieux.
1. **Look:** each crossing has one straight bridge, level, both ends on the banks. **Passed (owner, 2026-09-30,
   17:15):** one piece per crossing, bank to bank, the painted roads meeting it (the first build tipped into the river).
2. **Units:** order a tank, then an infantry squad, to a point across the river right behind a new bridge.
   - **Pass:** they drive over the bridge. **Fail:** they stop at the bank, go the long way round, or walk on water.
   - **First try (owner, 2026-09-30, 17:18): failed.** The unit crossed along the deck's line, but under it, on the
     riverbed: the decks units stand on are in `occlusioninfo_objectsonly.kdt`, which new bridges weren't in.
   - **Rebuilt (2026-09-30, night):** each new bridge now has a floor there (a shipped Pont_Metallique_02's, carried
     onto its banks, 47 units above them). **Passed (owner, 18:19): tanks drive on the deck.** One tank was down in
     the water beside a bridge: the ground opened along a deck was 2,560 each side of its line, the deck about 1,200.
     Now 1,280 (the smallest circle any shipped map uses). Again: does every unit stay on the deck?
   - **Rebuilt with 1,280 (owner, 18:43): the game crashed** on a move order (the empty-route crash, as with the first
     movement builds). A tank also went under a deck, and buildings on the road blocked tanks near a bridge. Found:
     the new decks' circles reached no ground units use, so each deck was an island; and every shipped movement graph
     is one piece, so the game never expects that. Even the 18:19 build had a dead-end deck, and one that was an
     island for infantry. **Rebuilt (2026-09-30, evening):** a deck that doesn't reach the ground units use gets an
     approach along the road until it does (D-Day: the longest 33 m for infantry, 37 m for vehicles, one through the
     farmyard west of the first bridge); a deck that can't be joined within 62 m is left closed, with a note; and the
     build refuses to write a movement graph that isn't one piece. Again: order a tank, then infantry, across each
     bridge and back; any crash?
   - **The roads up close:** a painted road vanished near the camera (owner, 18:18): up close the game draws a road
     with its road stickers (`Route` pieces), not the painted ground. The new roads now get them. Zoom in on a new
     road: does it stay?
   - **Seen on the way (owner):** a tank couldn't take a new road into the woods, infantry could; the owner likes
     that, and wants it as a choice per road (PLAN §10, next steps).
3. **Supply:** place a supply depot so its route needs the new road across the river.
   - **Pass:** the route line and the trucks use the bridge.
4. **The glow** (seen once: the ground glows, then turns normal): if it comes back, a screenshot while it glows and
   where the camera is (on the painted roads, or everywhere?).
5. While there: the mod's spawned units on this map (PLAN A8): which side they're on, and whether a formation faces
   the way it was drawn.

## T12. New roads up close (Studio 0.7.7)

The copy: `D:\RUSE-Instances\bridges` (rebuilt 2026-10-01 from the Studio mod `test` with the road fix). In the game:
**BATTLES > D-Day**, the new roads between Briqueville and Les Pieux.
1. Zoom the camera right down onto a new road, away from the bridges.
   - **Pass:** the road's texture stays as the camera comes close (as the map's own roads do).
   - **Fail:** it fades out near the camera, as on 2026-10-01.
2. Pan along each new road up close, then onto one of the map's own roads near them: both stay drawn.
3. While there: the bridges as in T8 (one tank and one squad across), to see nothing went back.

**Result: PASSED on 2026-10-02 (owner, probe 5: "holy fuck, we cracked it", "night and day"),** after failing
again and again from 2026-10-01 (batches 1-12). What draws a road up close is the map's **asphalt stickers**
(`Route_Bitume` on D-Day) laid along it, each with an **edge sticker** either side (`Route_Bitume_Bords`), on ground
painted the way the map's own roads are across, with the plants and props on the road's path taken off. The paint is
what shows from afar; the stickers take over near the camera. Built into `ruse build` for Studio 0.9 / Launcher 0.4
(scenery.road_decals, road_clearing; groundpaint.road_profile). The full story: [ROADS.md](ROADS.md).

The history below is kept: **FAILED, again and again** (owner, 2026-10-01, in batches 1-3 and his screenshots: "roads
visible up close is not working, I told you that many times").

**The record of every road probe** (2026-10-02, owner; only what was seen in the game counts):
- Batches 1-3: new roads painted into the ground's tiles show from afar, vanish near the camera.
- Batch 4: the new road added to the map's road model (staticmeshes `road`): still vanishes up close.
- Batch 5: batch 4 plus the close-up map (`div_map`) marked like the map's own roads: still vanishes up close,
  piece by piece, nearest the camera first.
- Batch 6: four roads whose road pieces are stored different ways, one of them (C) a copy of the map's own road
  pieces: the result isn't recorded (ask the owner).
- Batch 11: the `Route` strip's colour (mode 128, in the map's terrain settings) set to red: roads came out **blue
  from high up**; the map's own close-up road (textured asphalt, a dashed centre line) unchanged.
- Batch 12: the road model's vertices (staticmeshes `road`) lifted and recoloured red: the result isn't recorded
  (a note first credited batch 11's blue to it: wrong). **No batch ever showed a red road.**
- Probe 1 (2026-10-02): a road with D-Day's asphalt stickers laid along it, the same road without, the stickers
  without a road. **Up close the stickered road drew asphalt with a dashed centre line; the bare one vanished.** The
  first time a new road showed up close. It looked pale.
- Probe 2: edge stickers added (every asphalt sticker on D-Day has two), and a lane with the asphalt laid twice:
  gravel shoulders appeared; doubling made no difference.
- Probe 3: the same with one more file changed: no real change (that file turned out not to be the one the game
  reads).
- Probe 4: the ground paint and the close-up ground marks measured on the map's own roads and copied (ours had been
  twice as strong and twice as wide): "barely passes, needs better blending".
- Probe 5, five lanes, one change each: the junction copied from a stock T (a hard square block), the colour of the
  nearest road (no clear difference), the stickers turned the stock dead end's way (a cracked join the owner liked),
  and **the plants and props on the road's path taken off (lane 4): the owner's pick, "it even blends with the grass
  really nicely"**. Built as the recipe.

## T9. A road over one of the map's own bridges (Studio 0.7.4)

The owner's rule: the old bridge goes and the new road's bridge takes its place. The copy is built first (next
session): a mod with a road drawn across the river over one of D-Day's own bridges (the Studio: **Roads >
Straight**, across the gold road where it crosses the river). The build says `1 old bridge(s) replaced`.
- **Pass:** the old bridge is gone (not even its shadow), the new one runs along the new road, units cross on it,
  and nothing walks or drives on the water where the old one stood; supply routes don't cross there either.

## T10. Test in game with a read-only game folder (Studio 0.7.4, Launcher 0.2.9)

From a player's report: every **Test in game** failed with "[WinError 5] Access is denied" on a file in
`...\RUSE-Instances\<name>.partial`. Whoever had it (he offered to help):
1. Update to Studio 0.7.4 (the Studio offers it when it opens, or **Settings > Updates > Check now**).
2. **Test in game** again, without deleting anything first.
- **Pass:** the game starts; the old half-built copy is gone. **Also tell us:** is the R.U.S.E. folder marked
  **Read-only** (right-click it > Properties)? Was R.U.S.E. still running from an earlier test when it first failed?
- **Fail:** the whole message (the new one names the file and says why).

## T14. D-Day for 8 players (PLAN A10)

The copy: `D:\RUSE-Instances\eight` on the owner's PC; anywhere, from the test mod
(`maps/M04_cotentin/map.toml` with `players = 8`, and `scenario.toml` with a `[[start]]` for team 1 and one for
team 2): `py -3 -m rusemod build <the mod's folder> --instance D:\RUSE-Instances\eight`. The build says
`'(6) Cotentin (3v3)': 6 -> 8 players, named '(8) Cotentin (4v4)'`.
1. **BATTLES**: is D-Day listed as `(8) ... (4v4)`, and does its lobby have 8 slots?
2. Fill them (AI players are fine) and start.
- **Pass:** the game starts with 8 players, each on their own starting point (the new ones: team 1's north-west of
  its others, team 2's east of its others, on open fields).
- **Fail:** what the lobby shows, or where it stops. If the lobby shows 8 but the game refuses, try with 7.
- **Then, if it passes:** past 8 (a 10-player copy, 5v5) tells whether the game caps it.

## T13. A unit given to another nation (Studio 0.7.7)

A nation's unit models only load in a match where a player has that nation. So for a unit given to another nation,
the build copies its models (meshes, skeletons, animations, texture stand-ins) into the skirmish packs of the nation
it now belongs to, so they load with that nation's own units (`rusemod.unitpacks`; FORMATS §8). The first way, having
the other nation's packs load in every skirmish, crashed the game in batch 1 and is off (`build.FORCE_LOAD`).
1. In the Studio, make a mod (or pick a test one), open the German **Ju 87** (`Descriptor_Avion_Junkers_87`) and
   click **New unit…**. Name it "Stuka US", set price 5, and put it in **another nation's factory**: the US air
   factory.
2. Click **Test in game**. The build's report has a note saying the Stuka US's models go into the US's skirmish packs
   too (`1 mesh, 1 skeleton, 1 texture stand-in copied in from Germany's packs`; the skeleton holds the rear gunner's
   turret bones), and the line `unit models: 5 skirmish pack(s) in ZZ_Win.dat (...)`. There are no errors.
   - Without the Studio: a mod whose `src/stuka.rndf` holds
     `export Descriptor_Avion_Stuka_US is clone $/GFX/Everything/Descriptor_Avion_Junkers_87 ( Nationalite = 0 )`
     (every nation's aircraft are factory 9), built with
     `py -3 -m rusemod build <the mod's folder> --instance D:\RUSE-Instances\nations`.
3. Play a skirmish as the **US** against an AI of any nation **but Germany** (UK or USSR), on any map.
4. Build an airfield, then the Stuka US.
   - **Pass:** it's in the US air factory, it's drawn (a Stuka, not invisible), it takes off, flies to an order,
     dive-bombs a target and comes back, with its sounds. The match plays on normally.
   - **Fail:** an invisible plane, a plane with no animation (frozen propeller, no dive), a crash when it's built or
     first seen, or the match failing to load. Note which, and the build's notes.
5. Then one more skirmish **with** a German player (US against Germany): the Stuka US and the German Stukas both
   look and fly normally.
6. **Also tell us:** does the match take noticeably longer to load than an unmodded one?

## Batch 1 for Studio 0.8.0: T12, T13 and units on new roads in one game (2026-10-01)

The copy: `D:\RUSE-Instances\batch1`, built from a copy of the owner's Studio mod `test` (`D:\ruse-test-mods\batch1`)
with two changes the build now asks for: its spawns made neutral (a skirmish spawns only neutral items) and its road 2
left out (it joins no other road); plus T13's Stuka US. Start `RUSE.exe` inside the copy's folder, Steam running.

**One skirmish: BATTLES > D-Day, as the US against a UK or USSR AI (no German player).**
1. **T12, roads up close:** zoom right down onto a new road (between Briqueville and Les Pieux), away from the
   bridges. **Pass:** its texture stays as the camera comes close; pan along it onto one of the map's own roads, both
   stay drawn.
2. **Units on new roads:** order a tank, then an infantry squad, from one end of a new road to the other. **Pass:**
   they drive along the road, not across the fields beside it, and never through a building.
3. **T8 again:** one tank and one squad across a new bridge, on the deck.
4. **T13:** build an airfield, then the **Stuka US** in the US air factory. **Pass:** it's drawn (not invisible),
   takes off, dive-bombs a target and comes back.
5. **Tell us:** did the match take noticeably longer to load than usual?

Optional second game (T13 step 5): the US against Germany; the Stuka US and the German Stukas both look normal.
**Result (owner, 2026-10-01):** the copy crashed at match start (57 Japanese units spawned, no Japanese player: their
models never load; the build now refuses such spawns), then, rebuilt without them, when the Stuka US was built (its
gunner's model wasn't ready: units given to another nation are refused for now). US planes flew fine. A dried stretch
of river stopped tanks (dried beds are opened to units now).

## Batch 2 for Studio 0.8.0: only what could break the game, next to the player's HQ (2026-10-01)

The copy `D:\RUSE-Instances\batch2`, from `D:\ruse-test-mods\batch2` (batch 1's mod without the Stuka, plus the
a cheat mod for money and the US's ground units 3 times as fast; the AI gets neither). **BATTLES > D-Day, as the US
against one AI of another nation.** The US HQ is moved beside the river 750 m south-east of Toulaville; the camera
opens facing west.
1. **The dried river** (to the right of the HQ, 250 m north): send a tank and a squad across the dry bed. **Pass:** they
   cross it.
2. **The lone bridge** (straight ahead, 300 m west: a stone bridge with no road onto it): send a tank and a squad
   across. **Pass:** they cross on the deck, not in the water.
3. **The cleared wood** (ahead-right, 350 m north-west, past the dried river): a round clearing 100 m across in the
   wood. **Pass:** no trees in it at any zoom, the wood around it unchanged.
4. **The new roads** (ahead-left, 600 m south-west of the HQ, where two new roads meet): send a tank along one of
   them for a kilometre. **Pass:** it drives along the road, not across the fields beside it.
5. Money: the build menu's **Dev** tab gives +500 a click.

**Result (owner, 2026-10-01):** units walked the dried bed; the cleared spot (hedgerow trees among fields) wasn't
recognisable; tanks didn't keep to the new roads (see batch 3). The owner's old 10x upper-storey houses in the mod
floated 47 m up: our bug (a model starting above its base point), fixed in the build (`5c5a34f`).

## Batch 3 for Studio 0.8.0: a clean test mod, everything beside the HQ (2026-10-01)

`D:\RUSE-Instances\batch3` from `D:\ruse-test-mods\batch3` (made by a script: none of the owner's old edits), with
town names shown from any height (`D:\ruse-test-mods\townnames`) and a cheat mod. The HQ is moved onto the main
road east of Toulaville; a top-down map of the test spots goes with it.
1. **Infantry on a new "^" road** to a water tower 700 m north. **Passed:** infantry find the fastest way to the road
   and take it. Tanks don't: US tanks have no road bonus in the game's data (the Sherman and the Lee have no
   `SpeedBonusOnRoad`; infantry +83%, the Greyhound +16%), so they take the shortest way, on the map's own roads too.
2. **A hole cleared in a dense wood** (4,135 trees) with a water tower in it. **Failed:** tanks couldn't drive in: the
   map's movement still kept vehicles off the old wood. Fixed (`eac6fd0`): a cleared wood is opened to every unit and
   loses its forest cover.
   - **Checked again** (`batch3b`): a tank drives in. **Passed.** Infantry in the hole still showed the purple
     "hidden" glow. **Failed:** the hole's cover was never cleared. D-Day isn't square, and the cover grid of such a
     map is a square reaching past its short side, stored as two corners; the build read it as a corner and a size,
     so the paint landed 1.3 km south of the hole (8 shipped maps are like this; on the square ones, Blitz among
     them, cover was always painted in place). Fixed in `rusemod.cover`: in `batch3c` the hole's 946 cover cells
     are clear and the wood around it keeps its own.
   - **Checked again** (`D:\RUSE-Instances\batch3c`): infantry sent into the hole with the water tower. **Passed**
     (owner, 2026-10-01, 15:46: "works great"): the squad in the hole looks as it does in the open, a tank beside it.
3. **A 10x house** beside the HQ. **Passed:** it stands on the ground.
4. **A lone stone bridge** placed by hand. **Passed:** units cross on the deck.

## Batch 4: roads up close, units from another nation, Blitz Twin (2026-10-01)

`D:\RUSE-Instances\batch4` from `D:\ruse-test-mods\batch4` (batch 3's clean mod plus `src/nations.rndf`: the German
Ju 87 and Tiger copied for the US), with Blitz Twin (`D:\ruse-test-mods\newmap-agent`), the town names and a cheat
mod; built from branch `batch4` (the Erase tool, new maps, roads up close, the launcher's new look and the unit
packs, merged). No spawned units in it. The build: 0 errors, 1 warning (the cheat mod's scripts). The HQ is where
batch 3 had it, on the main road east of Toulaville; a top-down map of the spots goes with it. Start `RUSE.exe` inside
the copy's folder, Steam running.

**BATTLES > D-Day, as the US against one UK or USSR AI (no German player).**
1. **T12, roads up close:** the new road leaves the map's road 50 m north of the HQ and runs north-west. Zoom the
   camera right down onto it 200 m north-west of the HQ (the ring on the map), then pan along it to where it joins
   the map's road and onto that road. The build now adds a new road to the map's road model, what the game draws near
   the camera (77 pieces here).
   - **Pass:** the new road's texture stays as the camera comes close, and both roads stay drawn as you pan.
   - **Fail:** the new road fades out near the camera (as in batches 1-3), or the map's road does.
2. **T13, units from another nation:** a tank factory and an airfield (the build menu's **Dev** tab gives +500 a
   click), then the **Tiger US** in the US tank factory and the **Stuka US** in the US air factory (40 and 20, the
   German prices). Their models are now copied into the US's own skirmish packs (the Stuka: its mesh, its skeleton
   with the rear gunner's turret, a texture stand-in; the Tiger: the meshes and skeletons of the tank and its wreck,
   two texture stand-ins). The Tiger US keeps a Tiger's speed (the 3x is for the US's own units).
   - **Pass:** both are in their factories and drawn (not invisible); the Tiger drives and fights; the Stuka takes
     off, dive-bombs a target and comes back; no crash, when they're built or later.
   - **Fail:** a unit missing from its factory, invisible or frozen, or a crash (note when: built, first seen,
     firing). Batch 1's Stuka US crashed the game when it was built.
3. **T15, Blitz Twin:** after the D-Day game, back in BATTLES, T15's steps 1-5 below in this copy.
   - **Pass / Fail:** as there.
4. **Optional, spawned units:** `D:\RUSE-Instances\batch4-spawn` (from `D:\ruse-test-mods\batch4-spawn`: batch 3's
   HQ move and 3 neutral German Tigers spawned 150 m south of the US HQ, nothing else; their models copied into the
   packs every skirmish loads). BATTLES > D-Day as the US against a UK or USSR AI.
   - **Pass:** the match starts and the 3 Tigers stand south of the HQ, drawn.
   - **Fail:** a crash as the match starts (as batch 1's Japanese spawns did), or Tigers that aren't drawn.
- **Tell us:** did D-Day take noticeably longer to load than in batch 3?

**Result (owner, 2026-10-01, evening): FAILED twice.** (1) T12: the new road still draws only from higher up and
disappears as the camera comes down, as in every batch before; adding it to the map's road model changed nothing in
the game. (2) The game crashed as soon as the US tank factory was placed (playing the US). The build had rewritten the US's skirmish unit packs for the Tiger US and Stuka US, and
every one of the 71 US models in them had been given another number. Both are being worked out from how the game
itself does it before any new copy.

**Batch 5** (`D:\RUSE-Instances\batch5`, batch 4's mod with the close-up map's road mark): the new road still
disappears as the camera comes down, piece by piece, the pieces nearest the camera first, once they're in range;
higher up it's whole. The factories weren't tried.

## Batch 6: roads up close three ways side by side, and the factories in order (2026-10-01)

`D:\RUSE-Instances\batch6` from `D:\ruse-test-mods\batch6` (batch 4's mod plus three short test roads), with the town
names and a cheat mod; built from branch `roads-filed`: 0 errors, 1 warning (the cheat mod's scripts). The HQ
is where batch 3 had it. A top-down picture of the spots goes with it (north up). Start `RUSE.exe` inside the copy's
folder, Steam running. **BATTLES > D-Day, as the US against one UK or USSR AI.** Do the roads first: a crash in step 2
ends the game.
1. **T12, roads up close, four roads.** Every road gets the same paint and road model from afar; only how its
   close-up pieces (the map's road stickers) are stored differs:
   - **LONG** (batch 4's road, north of the HQ, north-west then north-east) and **B** (205 m south of the HQ, 230 m
     east-west): stored the way the map stores its own road pieces in open country, among its top block's items.
   - **A** (105 m south of the HQ): stored as in batches 1-5, in a block of its own.
   - **C** (305 m south of the HQ): not our pieces at all: a piece of the map's own road (8 pieces, a slight S-bend)
     placed there again.
   Zoom the camera right down onto each and pan along it.
   - **Tell us for each of A, B, C and LONG:** does it stay drawn all the way down, or disappear piece by piece as
     in batch 5?
2. **T13, the factories, in this order** (the build menu's **Dev** tab gives +500 a click); the units are as in
   batch 4 (the Tiger US and Stuka US models copied into the US's packs; nothing about units has changed since its
   crash):
   1. a **barracks** (or any building that isn't the tank factory or the airfield);
   2. an **airfield**, then the **Stuka US** in the US air factory;
   3. a **tank factory**, then the **Tiger US** in it.
   - **Pass:** no crash; both units drawn, the Tiger drives, the Stuka flies.
   - **Tell us** which step crashed, if one did (as the building is placed, or as the unit is built).

## T15. A new map in the menus: Blitz Twin (PLAN §13)

A mod can now make a new map: a copy of a shipped one under its own name and pack, listed in BATTLES beside it, which
the mod's other map files then edit (MOD_FORMAT §8, "A new map"). The test mod `D:\ruse-test-mods\newmap-agent`
copies **Blitz** as **Blitz Twin** (`maps/BlitzTwin/map.toml`: `copy_of = "SuperCrossRoads4"`, its name in six
languages) and gives only the copy a big hill (`terrain.toml`, in the copy's own pack) and a spot no ground unit can
enter (`movement.toml`, in the copy's own grid), so the game shows which files it loaded.

The copy: `D:\RUSE-Instances\newmap-agent-check` on the owner's PC (built 2026-10-01); anywhere:
`py -3 -m rusemod build D:\ruse-test-mods\newmap-agent --instance D:\RUSE-Instances\newmap-agent-check`. The build
says `new map: BlitzTwin` and `new: DataMapBlitzTwin_v09.dat, a copy of DataMapSuperCrossroads4_v09.dat`.
`py -3 tools\verify_newmap.py D:\RUSE-Instances\newmap-agent-check BlitzTwin SuperCrossRoads4` reads the copy back:
46 checks, 0 failed (2026-10-01).

Start `RUSE.exe` inside `D:\RUSE-Instances\newmap-agent-check` (Steam running).
1. **BATTLES**, the map list: at the end of the 2-player maps (in the data's order: after **Behind Enemy Lines**,
   before **Tripartite**), a map called **Blitz Twin** (in French *Blitz jumeau*, in German *Blitz-Zwilling*),
   2 players, with Blitz's picture.
   - **Pass:** it's listed with that name.
   - **Fail:** it isn't there, its name is blank or a code (`M_D_31`), or BATTLES freezes or the game crashes when it
     opens. Note which.
2. Pick **Blitz Twin**, 1v1 against one AI, and start.
   - **Pass:** it loads and plays like Blitz.
   - **Fail:** a crash while loading (at what point of the loading screen) or as the match starts.
3. **The copy's own pack:** find the HQ in the **south-east** (team 1's starting point; if you start in the
   north-west, scroll to the other one). **1.4 km south of it**, toward the map's southern edge, a **big round hill**
   (about 120 m high, 700 m across) where Blitz has none. It's there to be seen (units don't go there on Blitz either).
   - **Fail:** no hill (the game loaded Blitz's own pack), or ground that looks torn.
4. **The copy's own grid:** **700 m south of that HQ**, between it and the hill, a circle 300 m across that no ground
   unit can enter (nothing marks it on the ground). Order a tank, then an infantry squad, to its middle.
   - **Pass:** they stop at its edge (as in the blocked pit on Blitz, 2026-09-30).
   - **Fail:** they reach the middle (the game read Blitz's grid, not the copy's), or the game crashes on the order.
5. Back in **BATTLES**, play the shipped **Blitz** once: **no hill**, and a tank drives into that spot (the shipped map
   is untouched).
6. **Tell us:** the lobby's map name and the picture shown, and whether loading took as long as Blitz's.
- **Later, once this passes:** the same copy on two PCs in one multiplayer game (the map's ids come from its name, so
  both builds match); then a new map's own menu picture.

**Results (owner, 2026-10-03), in his words:**
- `D:\RUSE-Instances\blitz-twin-check` (16:01): Blitz Twin was not listed in the main menu; Blitz showed and
  loaded Blitz; no hill seen.
- `D:\RUSE-Instances\map-slot-check` (16:22; the same mod plus a second new map, **Blitz Borrowed**, whose BATTLES
  entry was pointed at the game's hidden slot "Tech: Test IA SuperCrossRoads", and Blitz given Tank Graveyard's
  picture):
  - Blitz showed Tank Graveyard's picture, so the game reads our map list.
  - **Blitz Twin was listed**, and he loaded both Blitz and Blitz Twin fine.
  - Blitz Borrowed was not there: an entry pointed at a hidden slot doesn't show.
  - No test hill seen in either map.
- Blitz Twin's BATTLES entry and map-list slot are byte-identical in the two copies (only reference numbers
  shift), so why it showed in the second and not the first is not known.
- **Next:** `D:\ruse-test-mods\newmap-flat` (T15b below), Blitz Twin's whole ground flattened with one big hill in
  the middle, to see whether it plays its own ground.

## T15b. Blitz Twin flat (2026-10-03)

`D:\RUSE-Instances\flat-twin-check` from `D:\ruse-test-mods\newmap-flat` plus the cheat mod: 0 errors. Only
Blitz Twin changes. Its whole ground goes flat at 31,000 (above Blitz's highest river, so the rivers, lakes and sea
go under the ground too), and one hill stands in the middle, about 940 m across and 155 m high. The outermost row of
points keeps its height. Bridges keep theirs too, so they end buried or in the air. Scenery and towns stay where
they were.
1. BATTLES: pick **Blitz Twin**, 1v1 against one AI.
   - **Pass:** flat ground everywhere with one big hill in the middle.
   - **Fail:** Blitz's own mountains and rivers (the game plays Blitz's ground), or a crash while loading.
2. Play **Blitz** once: its mountains and rivers as always.

**Result (owner, 2026-10-03): PASSED** ("That works"). A new map plays its own ground. One small visual bug where
the edge mountains were flattened (the outer row of points keeps its height), to work out later.

## T16. How many new maps fit (2026-10-03)

`D:\RUSE-Instances\many-maps-check` from `D:\ruse-test-mods\newmap-many` (written by a script: Blitz Twin flat as in
T15b, plus Blitz 1 to Blitz 100, each a new map of its own) and the cheat mod. Blitz 1 to 11 each have one change
named in the menu (hill left of your HQ, hill right of it, hill in the middle, crater in the middle, rivers gone, all
flat, flat-top mountain in the middle, wall of hills between the HQs, ring of hills round your HQ, hills left and
right of it, unchanged). Blitz 12 to 100 are plain copies. Left and right are as the match opens, from his HQ.
1. BATTLES: go through the whole map row.
   - **Tell us:** the highest Blitz number listed, whether the row still works (scrolling, picking), and anything
     odd (a crash, a freeze, blank names).
2. Play a few: Blitz 4 (crater), Blitz 9 (ring of hills), and the highest one listed.
   - **Pass:** each shows the change in its name.

**Result (owner, 2026-10-03, 16:53-16:55): PASSED** ("cracked"). All 101 new maps were listed: the map row scrolls
(Blitz 99, Blitz 100, then Blitz Twin), and he played Blitz 4 (crater in the middle) and Blitz 8 (wall of hills between
the HQs). No limit found at 101. Long names don't fit: "Blitz 7: flat-top mountain in the middle" (40 characters) is
cut off in CHOOSE MAP's title, and "Blitz 8: wall of hills between the HQs" (38) in the lobby.

## T17. A new Operation and a new campaign chapter (2026-10-03)

`D:\RUSE-Instances\ops-check` from `D:\ruse-test-mods\newmap-ops` plus the cheat mod: 0 errors. Two new maps made
the way Blitz Twin was, from another menu's entry (`entry` in map.toml), each flattened whole with one big hill in the
middle so it's plain which ground it plays:
- **Anzio Twin:** a copy of the Operation Anzio (Blitz, `Challenge - 1v1 39 Blitz_2 (Anzio)`), listed last in
  OPERATIONS. Its mission script is Anzio's own: the copied scenario still names Anzio's scripting folder.
- **Taking Command Twin:** a copy of Tunisia's first chapter (`M02_Tunisie_chapter1`, "2. TAKING COMMAND!"),
  listed last in the campaign, with the shipped chapter's script. The game marks each chapter unlocked from saved
  progress, so the copy may show locked.
1. OPERATIONS: is **Anzio Twin** listed? Play it.
   - **Pass:** flat ground with a big hill in the middle, and Anzio's mission runs (briefing, objectives, the enemy
     acting, a way to win or lose).
2. CAMPAIGN: is **Taking Command Twin** listed, and can it be started (or is it locked)? Play it if it starts.
   - **Pass:** flat Tunisia with a big hill in the middle, and the chapter's mission runs.
- **Tell us** anything odd: a crash while loading, a mission that never starts, texts missing.

**Result (owner, 2026-10-03): the Operation PASSED** ("operations worked"). The campaign chapter wasn't tried: his
campaign isn't all unlocked, and the game's own code opens a chapter only when the one before it in its list is
finished (the first of a list is always open), so a copy put last stays locked until the last chapter is done. He'll
try a campaign copy himself; cutscenes and dialog may need their own work ("an extended campaign with new scenes").

## T18. Blitz Twin flat to the edge (2026-10-03)

The edge bug from T15b, fixed: flattening kept the map's outermost row of points at their old height (the curtain
that hangs from the edge, the map's side seen when zoomed out, hung from them), which left a wall of old mountain one
point thick along the edge (his shots 16:42-16:43: tall striped walls on the skyline). Now the edge moves with the
ground in all four ground files, the curtain follows it, the water's side (where the sea or a river met the edge)
folds away under ground raised above the water, and the camera floor's ring past the edge moves with the edge beside
it. Under a plateau the far mesh also drops its own bumps, so the map is flat from far too (it kept up to 12 m of
them where the mountains were).

`D:\RUSE-Instances\flat-edge-check` from `D:\ruse-test-mods\newmap-flat-edge` (T15b's two strokes: the whole map flat
at 31,000, one hill in the middle) plus the cheat mod: 0 errors. Read back: every edge point of the four files at
31,000, the curtain's top one straight line at 31,001, the water's side folded flat, both trees' checks clean.
Checked in memory on all 32 maps (`tools/verify_terrain.py --edges`: the whole map flattened, then a hill on one
edge): the edge and the skirt where they should be on every map.
1. BATTLES: **Blitz Twin**, 1v1 against one AI. From your HQ, look out to the map's edges ahead, behind, left and
   right, low over the ground and from higher up.
   - **Pass:** flat ground right to the edge; no striped walls or rims of mountain along it.
   - **Fail:** walls or mountain shapes along an edge (as in T15b), or a hole where the edge should be.
2. Zoom all the way out to the table: its sides all round.
   - **Pass:** a clean, straight side everywhere.
   - **Fail:** gaps you can see through, jagged mountain shapes on a side, or a strip of water standing on a side.
3. Fly the camera to an edge and along it, low.
   - **Tell us:** whether it climbs over places where mountains used to be (the camera floor keeps its own height
     above the ground, which was set for the mountains).
4. As in T15b: the hill in the middle; towns and trees where they were; bridges buried or hanging.

**Result (owner, 2026-10-03, 19:15-19:17): PASSED** ("boom fixed", "The mountains work. That's confirmed."). In his
words: the bridge "looks completely fine. It's on the same level perfectly"; "even the rocky beach looks pretty okay";
"the lighthouse is still there". New: where the map went "super flat", the old riverbed (and the old coastal cliffs)
"looks like shit and has a lot of tearing. Especially when you're approaching it ... not necessarily like once you're
there and have it loaded in"; "up close, you definitely get some texture issues"; "I feel like you're merging a lot of
mesh layers". His idea: "just have a limit to how low it can go". Read back, the ground there is flat in both meshes;
the shipped rock props and stickers there are small and sit on the ground, so they aren't it. Being looked into: the
close-up ground (`div_map`, the weights the ground blends its detail textures by near the camera) still marks rock
there.

## T19. An artillery strike added to a mission (2026-10-03)

The first step to scripted strikes in campaigns and Operations ("I definitely want the scripts. To have it fire
directly on the spot"): before the Studio gets the tool, a strike is added by hand to a shipped mission, the Operation
**Anzio**, to see that the game runs it. `D:\RUSE-Instances\strike-test` (the cheat mod, plus Anzio changed by a test
script): four new **M7 Priests** for you beside your HQ, two named spots, and two strikes the mission starts on its
own, the game's own artillery strike order:
- about **30 seconds** in: the **first pair** of Priests (the two side by side) both fire at **spot 1**, beyond your
  AT guns, about 500 m from your HQ ("all the guns");
- about **60 seconds** in: of the **second pair**, only the Priest nearer **spot 2** fires at it ("the nearest gun
  only"); spot 2 is beyond your Wolverines, about 500 m from your HQ.

Start `RUSE.exe` inside `D:\RUSE-Instances\strike-test` (Steam running).
1. OPERATIONS: **Anzio**. Don't give the four Priests any orders; watch them from the start.
   - **Pass:** at about 0:30 two Priests fire together and the shells land on one place; at about 1:00 one more
     Priest fires at another place. The mission runs as usual (briefing, objectives, the enemy acting).
   - **Fail:** a crash while loading or at 0:30 / 1:00, the mission never starting, or the Priests never firing.
2. **Tell us:** how long they keep firing (one salvo, or until something stops them), whether a Priest drives
   somewhere first, whether the shells land on one exact spot or spread out, and whether both Priests of the second
   pair fired. Screenshots welcome (full and zoomed).

**Superseded by T22 (2026-10-03):** T22's four Priests fired a scripted strike in the game ("the priest fire"); this
copy wasn't run and is removed. Not tested: the nearest-gun-only form (only one gun of the group fires).

## T20. Map Paint on Blitz (2026-10-03)

The Studio's new Map Paint tile paints the ground's picture (Colour and Texture brushes). This is the first look in
the game: `D:\RUSE-Instances\paint-test` (the cheat mod, plus `D:\ruse-test-mods\paint-test`: 10 strokes, the same
five spots round each of Blitz's two starting points, so they're by your HQ wherever you start). Read back from the
copy's own tiles before the test: every spot is there.
- a **ginormous red patch**, 1 km across, beside your HQ (its near edge about 460 m away);
- a **blue circle**, 100 m across, close to your HQ;
- a **soft sand-coloured patch**, about 230 m across, see-through at its edge;
- a **dark dirt track**, a straight line 400 m long and 20 m wide;
- a **copied patch**, about 200 m across: the map's own ground from 600 m away laid on it.

Start `RUSE.exe` inside `D:\RUSE-Instances\paint-test` (Steam running).
1. BATTLES: **Blitz**, 1v1 against one AI. Look at the spots from far (zoomed out) and from close (zoomed right in).
   - **Pass:** the red patch and the other spots show on the ground from far and from close, with the map's
     buildings, trees and units on top of them as usual.
   - **Fail:** a crash while loading, the ground black or striped, or nothing painted.
2. **Tell us:** up close, is the red still red, or does the map's own ground pattern show through it (the game blends
   detail textures over the picture near the camera)? Does the copied patch look like ground from elsewhere, blended
   at its edge? Screenshots welcome (full and zoomed).

**Result (owner, 2026-10-03, 21:55): FAILED up close.** "The same issue as roads did: it doesn't show up close but
it shows up high." In his two shots, the red patch is where it should be from high up (placed with the shot's own
camera, it lines up with the red). Low over it, the camera just outside the patch, the red shows only from about the
middle of the screen on, and its near edge follows field edges. Read back from the copy, every level of both tile
sets (the close camera's and the far one's) is red at the patch, so the picture isn't what's missing. What Blitz
places inside the patch: about 263,000 objects drawn only near the camera, mostly crops (`Champs_Bles`,
`Champs_Verts`), tall grass, bushes, stones and 22,000 ground stickers (`Herbe_verte`, `Herbe_fonce`,
`Labourage_herbeclaire`, `traces_*`). The likely cover; T21 tests it.

## T21. Map Paint up close: what covers it (2026-10-03)

T20's paint shows from high up but not near the camera, where the map's crops, grass and ground stickers are drawn
over the ground. This test takes them off under some patches to see which ones hide the paint.
`D:\RUSE-Instances\paint-close` (the cheat mod, plus `D:\ruse-test-mods\paint-close`, made by
`D:\ruse-scratch\make_paint_close.py`): three patches in a ring round each of Blitz's starting points, all 460 m
across and about 960 m from the HQ, each its own colour:
- **red:** paint only (as T20);
- **blue:** paint, and the map's **ground stickers** under it taken off;
- **yellow:** paint, and under it the ground stickers, the **crops, grass, bushes, flowers and stones** taken off.
Trees, buildings, fences and other props stay under all three; the ground's cover and movement are unchanged.
Read back from the copy: each patch's colour at its middle on the finest tiles of both sets; under blue 0 stickers
left (Steam: 3,573 and 3,865), under yellow 0 stickers, 0 low plants, 0 stones; trees, props and buildings as in
Steam everywhere. The build took off 64,024 objects (the scenery grew 2.1 MB).

Start `RUSE.exe` inside `D:\RUSE-Instances\paint-close` (Steam running).
1. BATTLES: **Blitz**, 1v1 against one AI. Fly low over each patch, then come down close inside it.
   - **Pass (the fix found):** a patch stays its colour right up to the camera.
2. **Tell us**, for each colour: does it stay coloured up close, and what does the ground there look like up close
   (flat colour, or a pattern showing through)? Anything odd: holes, things floating, the game slower. Screenshots
   welcome (full and zoomed).

**Result (owner, 2026-10-03, 22:18): yellow wins.** "The red does not work. Same issue as before." "The yellow one
works fantastic ... it colors everything." "The blue one also works well, but it has a weird, like, fade." Of yellow:
"It has a weird render. Up close and down. Like it works, but it doesn't work great. Yellow wins." His shots: the
yellow patch yellow right up to the camera with its trees standing on it; the red patch stopping along a line near
the camera as in T20. So what hides paint up close is the low cover (ground stickers, crops, grass, bushes, stones);
taking it off under the paint shows the paint. The lag he had was his PC (another job held the processor at 100%).
Open: what blue's "fade" and yellow's "weird render" look like (to ask, with a shot).

## T25. Erased town buildings: the ground opened to units (2026-10-03)

The owner's "buildings bug": units still go around where erased buildings stood. Read from Blitz's movement: in its
towns the ground under almost every building is closed (1,108 of 1,156 in the town by HQ 1), while lone farm
buildings stand on open ground. `D:\RUSE-Instances\town-open` (the cheat mod, plus `D:\ruse-test-mods\town-open`,
made by `D:\ruse-scratch\make_town_open.py`): in the town nearest each starting point, two spots 120 m across, about
300 to 500 m from the HQ and 190 m apart. At both, everything but the trees is taken off (buildings, props, ground
stickers, crops, grass, stones: 914 building pieces in all) and the ground is painted, the low cover gone so the paint
shows up close:
- **red:** the movement left as it is, as the build does today;
- **blue:** the ground opened to all units (`[[open]]`) over the same circle.
Read back from the copy: at the blue spots the ground units can stand on went from 31-36% to 100% (vehicles and
infantry); at the red spots it stays 23-25%, as in Steam.

Start `RUSE.exe` inside `D:\RUSE-Instances\town-open` (Steam running).
1. BATTLES: **Blitz**, 1v1 against one AI. Take a tank and an infantry squad to the town. Order each to the middle of
   the red spot, then to the middle of the blue spot, then straight across each.
   - **Pass (the fix found):** at blue they drive in and across where the houses stood; at red they stop short or
     go around the old houses' places.
   - **Fail:** blue acts like red, or a crash on an order.
2. **Tell us** anything odd: units stuck, odd paths, the town's capture or the game slower.

**Result (owner, 2026-10-04, ~00:26): PASSED.** "The blue one works. The red one acts like buildings. Blue one, it's
completely gone, but there's still trees visible. The infantry doesn't go into ... hiding mode or anything, so ...
the blue one is for sure good. This works." Both spots' paint showed up close at every height ("the paint works
perfectly"). So opening the ground where erased town buildings stood lets units through, and infantry there no
longer act as in a town. Also seen: the BATTLES menu showed Blitz as 3 players with four seats. Not our build: the
cheat mod in every test copy (Dev_Toolkit_V1.rmod) sets Blitz's entry to 3 players with 3-team and free-for-all
layouts on purpose ("Blitz gets a spectator slot"); Steam's says 2.

## T26. The flattened riverbed up close (2026-10-03)

T18's "tearing" where Blitz Twin's old riverbed was flattened, "especially when you're approaching it". In his shot
19:16:22 the near part of the riverbed (about 210 m from the camera) looks like jagged rock and the far part (about
630 m) a smooth brown band: the river's steep banks are painted into the ground's picture with their light and
shadow (seen 2026-10-03), and up close the finest picture and the low cover take over. Two possible fixes, side by
side. `D:\RUSE-Instances\river-repaint` (the cheat mod, plus `D:\ruse-test-mods\river-repaint`, made by
`D:\ruse-scratch\make_river_repaint.py`): Blitz Twin flattened as in T18, and four stretches of the old riverbed near
each starting point (300 to 660 m from the HQ), each 120 m across, with a disc 30 m across painted on the bank beside
it:
- **red disc:** the stretch repainted with the map's own ground from a dry field 200 m away (Map Paint's Texture:
  the picture and the close-up ground map);
- **blue disc:** the stretch's low cover taken off (ground stickers, props, crops, grass, bushes, stones; the trees
  stay);
- **yellow disc:** both;
- **white disc:** nothing changed (as T18).
All eight stretches were checked in the map's own picture first: each is the same painted rocky river as the one in
his shot. Read back from the copy: the repainted stretches hold the field's picture and close-up values (within the
texture blocks' rounding, up to 9 of 255), the cleared ones hold no stickers, props, low plants or stones (trees as in
Steam), the others are Steam's, and each disc has its colour.

Start `RUSE.exe` inside `D:\RUSE-Instances\river-repaint` (Steam running).
1. BATTLES: **Blitz Twin**, 1v1 against one AI. Find the four discs on the river banks near your HQ. At each, fly
   low along the old riverbed beside it, approaching from far, then stop close over it.
   - **Pass:** the white stretch tears as in T18 and at least one of the others doesn't: that colour is the fix.
2. **Tell us**, for each colour: does it still tear when approaching, and how it looks once you're close.

**First look (owner, 2026-10-04, 00:04-00:06): "better and worse"; the yellow stretch is fixed.** "At some angles,
but then other angles, it's doing that tearing thing. Still, it's still very much there ... this is atrocious right
here ... a road pops through ... The bridge still appears here." His shots, placed with each shot's own camera (the
discs land where they show, so the placing is right):
- 00:05:16, the **yellow** stretch (repainted and cleared), 227 m away: smooth light ground inside the stretch's
  circle; the jagged rock starts again right past both of its ends. The owner, shown it marked: this is "the road
  popping through ... that's the river it's following": the repainted riverbed reads as a light road between the
  tree rows. The rock is gone there, but a copied field in a 120 m circle doesn't blend.
- The test's wording didn't work: "What blue stretch? ... there's no blue stretch". Only the discs are coloured; the
  river beside each disc is what changed. A next test marks the changed river itself.
- 00:05:58, the **blue** stretch (cleared), 172 m away: a smooth brown riverbed there, but the smooth part runs past
  the circle too, so this shot alone doesn't settle blue. To ask.
- 00:05:44, the **white** stretch (unchanged), 125 m away: jagged 3D rock, as T18.
- 00:04:48-00:05:00 and 00:05:31-:33 (the two bridges): river parts no stretch touches: unchanged.
Up close the old riverbed is 3D rock (lumps, spikes, flat walls with stretched texture), not a flat picture. The
types most tied to Blitz's rivers are ground stickers of the "AutoBuild" kind: `Stickers_France_AutoBuild_Rocher_
parallaxe_off_03` (832 of its 833 by a river), `..._sable_7`, `..._roche_6`, `..._roche_2`, `..._terre_5`,
`..._herbroche_8/9`. Likely: stickers shaped to the old banks, standing up on the flat ground (to confirm with blue).
The discs: on this map they show up close only in part (cut in field shapes), unlike T25's town spots: the big crop
patches whose middles lie outside a 30 m disc still cover it, since an erase takes an object by where its middle is.

**After (2026-10-04): the rock isn't objects** (wrong: see T27's result; it's the river's bank stickers). Where he saw the worst of it (the white stretch; under both bridges,
placed with each shot's camera), the riverbed holds what any dry field holds within 40 m: crops, bushes, a few stones,
the road's edge stickers; none of the river's AutoBuild stickers, no rock props (`D:\ruse-scratch\rock_spots.py`). The
river's stickers lie flat (none leans). The build already rebuilds the mesh's underwater triangles when ground moves
(`Tms._water_lists`; FORMATS' "not rebuilt" was stale). Left: the ground's two pictures, both made for the old gorge:
the picture (the tile sets, its steep banks painted with their light and shadow) and the close-up ground map
(`div_map`). The yellow stretch had both replaced. T27 separates them.

## T27. The flattened riverbed: picture or close-up map? (2026-10-04)

`D:\RUSE-Instances\river-layers` (the cheat mod, plus `D:\ruse-test-mods\river-layers`, made by
`D:\ruse-scratch\make_river_layers.py`, then `river_layers_post.py` on the copy): Blitz Twin flattened as in T18,
and four pieces of the old riverbed near each starting point (300 to 900 m from the HQ). Each piece is a square
120 m across lined up with the river, **inside a painted frame of its colour** (lines 6 m wide, 30 m outside the
piece). Each piece gets the map's own ground from a dry field 200 m away:
- **red frame:** in the close-up ground map only (the picture as it was);
- **blue frame:** in the picture only (the close-up map as it was);
- **yellow frame:** in both (as T26's yellow stretch, without its clearing);
- **white frame:** nothing.
The frames are Map Paint lines with the new clearing (stickers, low plants and stones taken off by how far each
reaches): its first test up close. Read back from the copy: each piece holds exactly its layers (red: the picture
untouched, the close-up values the field's; blue the reverse; yellow both; within the texture blocks' rounding, up
to 11 of 255); all 32 frame lines their colour, and nothing that could hide them left reaching onto them. The build
took off 13,479 objects under the frames.

Start `RUSE.exe` inside `D:\RUSE-Instances\river-layers` (Steam running).
1. BATTLES: **Blitz Twin**, 1v1 against one AI. Find the four frames on the river near your HQ. At each, fly in low
   from far, then stop close over the river inside the frame.
   - **Tell us**, for each colour: is the jagged rock still there up close inside the frame? The white one should
     have it, as T18.
   - **And:** do the frames show at every height, close up included?

**Result (owner, 2026-10-04, 01:19-01:20): no layer fixes it.** "Red's a complete fail." Yellow "is very close up high
but once you get down low it looks like a bunch of rock ... maybe if that was like a combination of the two and
blended in it wouldn't look that bad ... it looks really bad up close." Blue "looks good up [high] ... is it supposed to
show a road? But then up close, it looks shit." "White looks bad up front, too." His shots 01:19:34 to 01:20:35 (the
three before them, 01:17:51 to 01:18:06, are of another map: their map Id differs). Read after:
- **The rock is the river's bank stickers, not the ground's pictures.** The copy's mesh at the pieces is flat at
  31,000, every normal straight up, no water triangles. What reaches over the middle of all three river pieces (by
  each object's full size) and not over a dry field: 2-3 of `Stickers_France_AutoBuild_Rocher_parallaxe_off_03`, the
  river's rock sticker (30 m square; class `STICKERS_AutoBuild/France`; a rock picture with strata and a bump map,
  drawn up close only). T26's yellow stretch, the one place the rock went, also had its stickers taken off; T27's
  yellow had the same two pictures without that. So T26's "After: the rock isn't objects" was wrong: that check counted
  objects by where their middle is, within 40 m, at spots placed from his shots.
- **Blue's road:** the dry field the blue piece's picture was copied from has a road through it (34 asphalt pieces and
  dirt tracks in its 120 m square): the copy brought it.
- The frames (Map Paint lines with the new clearing): his shots show them from about 50 to 540 m up; whether they
  hold right down close is to ask.

## T28. The flattened riverbed: bank stickers off, ground mended from both banks (2026-10-04)

The fix T27 points to, in two parts, side by side. `D:\RUSE-Instances\river-mend` (the cheat mod, plus
`D:\ruse-test-mods\river-mend`, made by `D:\ruse-scratch\make_river_mend.py`, then `river_mend_post.py` on the copy):
Blitz Twin flattened as in T18, and three pieces of the old riverbed near each starting point, at the spots of T27's
frames (500 to 750 m from the HQ). Each piece is a square 160 m across lined up with the river, marked by **four
corner marks of its colour** (6 m wide, 30 m long, 12 m outside the square, on the banks: no mark crosses the river,
so none clears it). The old riverbed in each square (the old ground's hollows, `rusemod.mend.Gorge`: deeper than its
banks by more than 1.5 m, plus 4 m round for the painted rims) gets:
- **orange:** the river's bank stickers taken off: those of the `STICKERS_AutoBuild` classes reaching into it (17
  and 15, every one the rock sticker). Nothing else: its pictures are the old river's.
- **green:** those taken off (21 each: 15 and 16 rock stickers, the rest bank stickers of tracks and grass), and the
  riverbed's picture (both tile sets, every level) and close-up map
  **mended from both banks** (`rusemod.mend`): each side of the bed takes the ground beyond its own bank, moved
  across by the bed's width, mirrored only within 6 m of the bank so its edge meets its own ground, the two sides
  cross-fading through the middle (the owner, T27: "a combination of the two and blended in").
- **purple:** all the low cover reaching into it taken off (every ground sticker, low plant and stone: 401 and 1,660;
  T26's yellow had that), and mended as green.
The river outside each square is as it was: the "before", right beside it. Read back from the copy: at orange and
green no bank sticker reaches into the riverbed any more, at purple nothing low; green and purple's pictures differ
from Steam's by more than 12 of 255 at 78 to 83% of the riverbed's sample points (a mended point can land near the
old value) and the close-up map at 79 to 88%, orange's at none; of the dry ground in the squares, 2 to 4 points changed at each mended piece, every one
within 1.5 m of the mended bed (re-encoded with it in one 4x4 block of the picture), none at orange; every mark its
colour. Seen from above (`D:\ruse-scratch\shots\t28_*`): the mended beds take the fields round them and their tracks;
some of Steam's own painted boulders lie on the banks just outside.

Start `RUSE.exe` inside `D:\RUSE-Instances\river-mend` (Steam running).
1. BATTLES: **Blitz Twin**, 1v1 against one AI. Find the three marked pieces near your HQ (orange where T27's blue
   frame was, green where yellow was, purple where white was). At each, fly in low from far, then stop close over
   the riverbed inside the marks.
   - **Tell us**, for each colour: is the jagged rock gone up close? How does the ground there look, high and close:
     like the fields round it, a road, odd patterns?
   - **Pass (the fix):** green (or purple) has no rock up close and looks like part of the fields from every height.
     Orange tells whether the stickers alone take the rock away.

**Result (owner, 2026-10-04, ~02:15): purple wins.** "It's looking like the purple test wins. I like some of the idea of
the darker riverbed, but I think it's just better to make it look like grass when it's super, super flat." So where
ground edits fill a hollow flat, the build takes off all the low cover reaching into it and mends its pictures (to
build; started, see below).

**A bug he caught (same shots, 02:13-02:15, the map view):** "The brighter white road set is just not there. And it's
not aligned with the actual roads ... When you zoom in, the darker, dirt roads that are more tan are like the actual
roads." Read after: the white roads seen from high up are the map's road model (`output\staticmeshes.spkpc`, model
`road`), which holds the ground's height at every vertex; the build raised the ground 27 to 54 m and left the model at
the old heights. The model's middle line projected with shot 02:15:17's own camera lies on the white roads at its
stored heights and on the tan painted roads at the new ground's (`D:\ruse-scratch\road_project.py`, marked crop
`D:\ruse-scratch\shots\021517_roads_a.png`). **Fixed in the build (local, not seen in the game yet):** a terrain edit
moves the road model's vertices with the close-up mesh (`terrain_edit._reseat_roads`, `roadstrips.StaticMeshes.
with_heights`), each part's box made again as all 4,701 shipped parts have it (its vertices' bounds, the top 10 higher)
and the model's box as all 33 shipped models (its parts' and the corner 0, 0, 0). Tests: test_roadstrips (moved and
moved back gives the very bytes), test_terrain_edit (moves by the mesh's change under each vertex).

**Where it stopped (paused by the owner, 2026-10-04):** wiring purple into the build. Timed on Blitz: the old hollows
over the whole map 18 s (11.8% of it); mend_tiles over a 1 km square of the finest level 79 s, so a whole flattened
map would take tens of minutes as it is. Next: work out each pixel's sources on the 2.5 m hollow grid and sample the
fine picture through them (keeps the fields' grain), then the build step (filled = an old hollow the new ground no
longer has; low cover reaching into it off by size; mend both tile sets and the close-up map), then one test copy
with the road model fix.

## T22. A mission of our own, in its own folder (2026-10-03)

The first step to scripted Operations and campaign missions with their own end goals (PLAN §12 idea 5; the owner:
"build a test, just make sure the test is very obvious for me to see"). A new Operation, **MISSION TEST** (a copy of
Anzio on Blitz's ground, listed last in OPERATIONS), runs a mission we wrote: its own script folder, its own texts in
every language, and everything at your HQ. It also covers T19's question (does a scripted artillery strike fire).
`D:\RUSE-Instances\mission-test` from `D:\ruse-test-mods\mission-test` (plus the cheat mod; US units 3 times as
fast), made by a test build that adds the mission's files: 0 errors. Read back from the copy: the script, the 11 text
files, the scenario's new spots and circle, Anzio's own mission unchanged. Every block and setting the mission uses
is written the way the game's own missions write it (all 67 names and 157 settings found in them). The map of the
spots: `D:\ruse-test-mods\mission-test\t20_map_clean.svg`.

What should happen, in order (the Italians get no orders: they stay where they are):
1. About 3 s in: a popup, **"MISSION TEST is running: this is our own mission ..."**, and a new goal, **"MISSION
   TEST: DRIVE A TANK INTO THE CIRCLE"**, in the goals list and marked on the map.
2. About 13 s: **6 Shermans** appear beside your HQ (yours), with a popup.
3. About 23 s: **4 M7 Priests** appear on the other side of your HQ (yours), with a popup. Leave them alone.
4. Drive a Sherman about 300 m from your HQ to **the circle: where the road goes into the big wood** (the map). When
   it's in: goal done, a popup **"Circle reached! ..."**, and a second goal, **"WATCH THE ARTILLERY STRIKE"**.
5. 10 s later the **4 Priests fire** at a field about 450 m from your HQ, beside a road (the map).
6. 30 s after that: goal 2 done, a popup **"Strike over ..."**, then the **VICTORY** screen 10 s later.
- **Pass:** all six happen.
- **Tell us** the first step that didn't happen (a crash, the loading screen never ending, no popup, no goal, no
  units, the circle doing nothing, no shells, no victory), and whether the texts were our English ones. Screenshots
  welcome.

**Result (owner, 2026-10-03, 22:13-22:15): PASSED.** "Everything's worked so far ... Victory in 10 seconds, the
mission test is done. Besides the lag, it worked like a charm": all six steps, the Priests fired, the victory screen.
In his shots: our popups and goals in English, goal 1's marker over the wood, goal 2 after the Sherman reached the
circle. The lag at each step was his PC ("without a doubt my computer": another job had the processor at 100% the
whole time). Still open:
- Anzio's own objectives showed somewhere ("you didn't get rid of the main mission's objectives"): where (the
  Operation's briefing in the menu, or in the game) is to ask; the mission itself holds none of them.
- Goal 1 came up as a **BONUS OBJECTIVE**, goal 2 as a NEW OBJECTIVE. Goal 1's label is drawn at a spot (style 1, as
  the game's spot-marked goals are), goal 2's over a group (style 12, as Anzio's main goal): which setting makes a
  goal a main one isn't known yet.

## T23. Three US tanks repainted: does the game take a unit texture we wrote? (2026-10-03)

The first step to changing how units look (PLAN §14 idea 6; China's units are repaints of borrowed models). Three
US tank textures are changed in `D:\RUSE-Instances\unit-paint` (from `D:\ruse-test-mods\unit-paint`, plus the cheat
mod; US ground units 3 times as fast), by a test build outside the apps: 0 errors. Each texture is written the way
the game stores its own small texture levels (blocks as they are, every level), and its small stand-in the same way.
Checked on the copy itself: all 24,058 files in its `ZZ_Win.dat`, 24,051 the game's byte for byte and the 7 changed
ones exactly as made; in each changed texture, the part that should stay the same is the game's byte for byte.

| Tank | Built in | What was changed |
|---|---|---|
| M4 Sherman | Armor Base | its colour turned red (each colour's brightness kept, so its pattern and shading stay) |
| M3A1 Stuart | Armor Base | its alpha set to 0 everywhere (colour unchanged) |
| M10 Wolverine | Anti-Tank Base | its alpha set to 255 everywhere (colour unchanged) |

Play a skirmish as the **US** against an AI of **Germany** (not the US or the UK: their tanks could share these
pictures), any map. Build one of each, look at each one up close beside any other US tank (unchanged), then zoom
out slowly. If one of the three isn't in its base's menu, say which: the other two still answer most of it.
- **Pass (step 1):** the Sherman is red. That proves the game takes a unit texture we wrote.
- **Tell us (step 2):** how the Stuart and the Wolverine differ from a normal tank: the star and other markings,
  shine, darker or lighter, and the player colour (up close and from far out). This tells us what the alpha does.
- **Fail:** a crash or an invisible tank (say when), or all three look normal.

**First try (owner, 2026-10-03, 22:46): the game crashed when a tank was built.** Our fault, in the small stand-ins:
the game's are flagged as raw blocks (flag 0, all 2,822 of them), ours were written with flag 1 (a codec tag first),
so the game read the Stuart's blocks as a codec header and copied a nonsense size. Rebuilt with each stand-in changed
in place (every byte outside its blocks the game's, flag 0 kept); the full textures were right (flag 1, as all
3,831 of the game's). Checked again on the rebuilt copy: all 24,058 files, 24,051 the game's byte for byte, the 7
changed ones exactly as made, the stand-ins' flag 0. A test now guards the flag (`test_tmst`).

**Result (owner, 2026-10-03, 22:56-22:58): PASSED, no crash.** The game takes a unit texture we wrote: "The
Sherman's the answer. It's completely red at all levels", up close and as the zoomed-out piece. What he saw:
- **Sherman (colour red):** red everywhere, "except there's a little visual bug with it. When you zoom in really,
  really, really close, there's like a blue line" (his crops 22:57:47 and :53: blue stripes across the hull).
- **Wolverine (alpha 255):** "Is the Wolverine supposed to be white? ... I think that could be the sun ... it's
  only at certain angles" (crops 22:57:12 and :16).
- **Stuart (alpha 0):** no blue-line issue up close; "the Stuart doesn't load up high", and "at high distances,
  nothing" (crops 22:58:18 and :23 up close, 22:58:29 the zoomed-out pieces).
What it points to (to confirm with the owner): a vehicle's alpha is the side colour where it's low (the Stuart
up close in his crops looks all in his blue) and shine where it's high (the Wolverine white in the sun). The
Sherman's blue lines would then be the game's own: its alpha (kept byte for byte) is black in two stripes; the red
only makes them stand out. The side colour seems to apply only up close; the paint shows at every distance.

## T24. Formations on keys (2026-10-03)

The first step to formations (PLAN §14 idea 7, a mod until RUSE 2.0). `D:\RUSE-Instances\formation-test` (the cheat
mod, plus `D:\ruse-test-mods\formation-test\formations-test.rmod`): 0 errors, one warning (it changes one of the
game's scripts, the one that turns clicks into orders; the game's own script is kept inside it, unchanged, and the
mod's code runs after it). Checked on the copy: of the 140 scripts in its pack, 139 are the game's byte for byte and
the changed one is exactly as built; the shapes were checked outside the game (each unit gets one order, the selection
comes back). Keys: **1** V, **2** square, **3** line, **4** column, **5** circle, **0** the game's own formation.

Skirmish, any map. Make about six tanks and select them all.
1. Press **1**, right-click open ground well away from them. Then **2**, **3**, **4**, **5**, each with a right-click.
   - **Pass:** they end in a V (point towards where they drove), a square of two rows, a line across their way, a
     column, a ring.
2. (Dropped in test 0.2: a drag's release never reaches the scripts. The game's own drag stays on **0**.)
3. Press **0**, then right-click and right-drag as usual.
   - **Pass:** the game's own behaviour, its rectangle included.
4. With a shape picked, right-click an enemy unit or building.
   - **Pass:** they attack it as normal.
- **Tell us:** whether a number key also does something else in the game; whether the game's own rectangle shows up
  when a shape is picked; how it looks when the faster units arrive first.
- **Fail:** right-click does nothing with a shape picked (press 0 to get normal orders back), units go to wrong
  places, or a crash. The game writes `formation_log.txt` in the copy's folder for us.

**First build (owner, 2026-10-03, 22:52): crashed after the lobby.** The crash report holds the game's own Python
error: "NotImplementedError: exec statement". The game's Python has `exec` turned off, and the first build ran the
game's script through it. Rebuilt the same night without it: one script made of the game's own code, unchanged, then
the mod's; every Python operation and built-in it uses also appears in the game's own 245 scripts. 0 errors; the copy
checked again (139 of 140 scripts the game's byte for byte, the changed one exactly as built).

**Second build (owner, 2026-10-03, ~23:00): loads; keys reach the mod; orders stuck.** After 1-5, right-click sent no
order at all; **0** gave orders back (confirmed). Cause: the game calls a button's release through a table it fills
once when the input class is made, so the mod's release code never ran and every click waited for it. In his words,
the game's own formation "goes nine wide and then goes back" (his shots 23:00-23:01): rows of nine as the game's data
says (rows up to 200 m, 25 m apart). Third build the same night: the release goes into that table too, a click whose
release never comes is dropped at the next click, and the outside-the-game check now clicks through the game's own
button code. 0 errors; 139 of 140 scripts the game's byte for byte, the changed one exactly as built. No sign on
screen yet when a key picks a shape.

**Third build (owner, 2026-10-03, ~23:07-23:09): orders go out, no shapes; a drag sends nothing.** His shots: the
group in a loose cluster after **1**, a fan of order arrows (several orders, each to the whole group), units "having an
aneurysm". Cause: the game's order goes to what the selection object gives back (its `selection` list); setting the
selection the way the game's own fast-strike button does only lands a frame later, so every one-unit order went to
the whole group. A drag: the release never reaches the scripts (the game's own drag takes it), so nothing was sent.
Fourth build (test 0.2) the same night: each unit's order is given with the selection list pointed at that unit alone,
then the real list put back; the shape is placed on the click (no drag in a shape: the game's own drag stays on 0);
15 m between units (25 m made a V of 30 tanks some 375 m a side). 0 errors; the copy checked as before.

**Test 0.2 (owner, 2026-10-03, 23:15-23:17): the shapes WORK** ("it seems like all the formations are working",
"seems to be working pretty well"; his shots of 1-5 with about ten Stuarts: a V, two rows of five, a line, a
column, a ring). To fix, in his words: it isn't "taking into account how many units are there ... to keep the
formation even" (the V's arms came out uneven), and nothing shows which shape is picked. Test 0.3 the same night: a
V's arms are always the same length (an even count puts two at the point); a square takes full rows whenever the
count allows (9 = 3 x 3, 10 = 2 x 5, 12 = 3 x 4), a short last row centred; a ring's neighbours 25 m apart (at 15 m
ten tanks made a lump); the HUD's message line says "Formation: V (0: off)" while a shape is picked (the line the
game's own placing messages use), cleared on 0. Checked outside the game for every shape and every count from 1 to
40. 0 errors; the copy checked as before.

**Test 0.3 (owner, 2026-10-03, 23:22-23:24): PASSED** ("V formation with an odd number. V formation with an even
number ... Much better. Okay, formations work"; his shots: an even V, the square, the line, a wider ring; of the label:
"It's coming up"). His word: push it to the mod list. Packed as Formations 0.3.0 (`D:\ruse-test-mods\formations-mod`,
the script byte for byte the one tested), checked and built from the package: 0 errors, the script warning.

## T27. Paint a unit in Blender from the Studio, and see it in the game (2026-10-03)

The Blender bridge, step 2 (PLAN §14 idea 6), in the Studio run from the project folder (not released yet). A unit's
page has a new box, **3D model and paint**: *Open in Blender* opens the unit textured in Blender; *Bring back* puts
what was painted and saved there into the mod; *Test in game* then shows it. When Blender isn't found, the box offers
*Get Blender (free)* (blender.org) and *Choose Blender…*. Checked before handing over, without the window: the whole
loop on the T-26 (Blender's own save of a painted picture, Bring back, then a full build on the game's files: only
the painted blocks encoded again, the stand-in in its 3 packs, 0 errors); the box's buttons in the preview window.

1. Start the Studio from the project folder (the command in the reply), pick or make a mod.
2. Open a unit you can build and see easily (the M4 Sherman, US Armor Base), find **3D model and paint**.
3. *Open in Blender*. In Blender: the **Texture Paint** tab, paint something big and bright on the tank, then
   **Image > Save** (Alt+S). Close Blender.
4. Back in the Studio: *Bring back* (it should say it brought back 1 picture), then *Test in game*.
5. In the game, build that unit.
- **Pass:** the unit wears what you painted, up close and zoomed out.
- **Tell us:** which step didn't work and what it said, or anything that looked wrong (Blender, the Studio box,
  the unit in the game).

**First go (2026-10-04, his words and shots):** the box was there and Blender opened the P-51 Mustang textured, but
"The model isn't in studio though. I want to be able to see an example of the model" (on the page's empty right
side); the Mustang "loaded in super weirdly" (a flat square through its nose: the propeller disc, which the game draws
with a shader of its own over the whole picture); and he couldn't find where to save ("I am not seeing top left where
you save"). Changed the same day, before he tries again:
- the unit's page shows its model on the right, turning, drag to turn and scroll to zoom, with the mod's paint on it
  once brought back (checked in the preview window with the real Mustang and T-26);
- propeller discs are a hidden piece of their own, in Blender and the Studio;
- no saving step: Blender opens in Texture Paint with a hint written on the view; Bring back asks it to save; Ctrl+S
  and a **Save paint (Ctrl+S)** button at the top left save too, and it saves on its own every 10 seconds. Checked
  in Blender's window: Ctrl+S saved (no file dialog), the Studio's ask was answered in 0.2 to 0.6 s, and Bring back
  took the picture.
- Not a bug: the Mustang's page is `Descriptor_Avion_Junkers_87_GR` in the game's own data (an old name; its text is
  P51 MUSTANG and its model the Mustang's).

**Second go, steps now:** 1 and 2 as above (the page shows the model on the right); 3. *Open in Blender*, paint on
the tank with the left mouse button (the colour: the first colour square at the top); 4. back in the Studio, *Bring
back* (Blender can stay open; the model on the page changes to your paint), then *Test in game*; 5. build the unit.

**Second go (2026-10-04, 01:00):** "So far, everything's worked with the studio and Blender": the Sherman showed on
its page, he painted it (teal, blue, green and black on the hull, green on the tracks), Bring back took both pictures.
Then two crashes:
- **The Studio's copy (01:04)** stopped itself when the map loaded. Not the paint: the game's own error text names the
  fair play watcher, another session's unfinished work that the Studio run from the project folder put in the copy.
  That session keeps its scripts out of every build now.
- **A paint-only copy without the watcher (`paint-check`, 01:08)** crashed with a memory fault, in a thread with none
  of the game's own code on its stack (so the dump doesn't show what the game was doing). What this copy did that
  T23's never did: the Sherman's track stand-in shares its picture with the Firefly's, the Calliope's and the
  flamethrower Sherman's. In 2 packs the build gave it its own copy (the pack grew by 1,064 bytes; T23's packs all
  kept their size), and in the other 2 it painted it in place, so the Calliope's and the flamethrower's far-off tracks
  changed too (a real bug either way). The leading suspect, not proven.
- **Fixed:** a shared stand-in is now left as the game has it (only that texture's far-off look keeps the old
  colours). `paint-check-2` (same paint, no watcher): every stand-in pack keeps the game's size, and its only changed
  bytes are the hull stand-in's (1,130 in each of 4 packs).

**PASSED (2026-10-04, 01:18), `paint-check-2`.** In his words: "It normally would fail when I hit launch game just to
start loading in, so I haven't made it this far yet ... yep sweet works like a charm." His shots: the Sherman built
from the Armor Base wears the paint (teal turret, green tracks, blue on the hull), up close and from higher up. Both
crashes came as the game started loading the map, which fits the grown stand-in packs for the second one (still not
proven). Left over: the build menu's card still shows the game's picture of the Sherman
(`ww2/res2d/texanimationuniticone/eu/m4_sherman.png`, the unit's `TextureForInterface`: 360 x 184, DXT1, one level,
ZIPO-packed, like the ground tiles we already write). Copy recycled.

## T31. A unit's build-menu card made in the Studio (2026-10-04)

The owner, after T27: "the only thing is changing what it looks like in the factory now"; his go for the Studio way:
"It just takes a screenshot of the model at whatever angle they want ... Add it to the Studio." A unit's page now
has a dashed **Card** frame on its 3D view and, under it, the card now (a thumbnail), **Use this view as the card**
and **Game's card**. The button takes what's inside the frame at the card's own size (360 x 184 for the Sherman),
with the mod's paint, over a backdrop like the game's cards, into the mod (`files/replace/<card>.tgv.png`); the build
writes it the way the game stores all 450 of its cards (one DXT1_LIN level, ZIPO). Checked before handing over, on
the real game: the Studio found the Sherman's card and saved a capture of his painted Sherman; the build (0 errors,
32 s) wrote it; read back from the copy, the header and format are the game's and the picture matches the capture
(mean difference 3.5 of 255, DXT1's rounding). `D:\RUSE-Instances\card-check`: his Sherman paint plus that card, no
fair play watcher.

1. Start `card-check` (Steam running), a skirmish as the US.
2. Open the Armor Base's build menu and point at the Sherman.
- **Pass:** the Sherman's card is the green-and-teal Sherman on a hazy sky and sandy ground.
- **Tell us:** a crash (and when), the old card, or a broken picture (stripes, wrong colours).

**Run 1 (2026-10-04, 01:51): the old card.** His shots: the painted Sherman placed from the Armor Base (so this copy),
the game's own card in its build menu. Cause, found in the files: the game's cards are also inside the menu packs,
archives of their own inside ZZ_Win.dat (`gen\pack\menuus.ppk`, 62 US cards; `outgame.ppk`, 273; one per nation, and
a few more: 64 nested packs, 13 with cards), each with an identical copy of the card; only the loose `.tgv` had been
replaced. The build now replaces a changed card in every nested pack that holds a copy (all 64 rebuild byte for byte).
`card-check` recycled. **Run 2:** `D:\RUSE-Instances\card-check-2` (same paint and card): 0 errors, 36 s; the card
replaced in `menuus.ppk` and `outgame.ppk` too, identical to the loose one there, every other member of both packs
the game's byte for byte.

**PASSED (2026-10-04, 02:01), run 2.** In his words: "worked". His shot: the Armor Base's build menu shows the
Sherman's card as the green-and-teal Sherman from the Studio's 3D view (under the game's blue tint while it's being
researched). Copy recycled.

## T32. Does the game draw a model shape we wrote? (2026-10-04)

The owner, on "the game may not accept a model it didn't ship with until we test it": "TEST". The first step of new
models (PLAN M7): the M4 Sherman's model reshaped and written back into the four model packs that hold it (the
all-units pack, the US skirmish one, the US one with boats, the level-design one): everything above the tracks 1.8
times taller (hull top, turret, gun; the box in its name record from 772 to 1,150), the wheels and tracks as they are
(they turn round their own axles), its three vertex buffers stored plain (the game's own level-design pack already
stores two of them plain). Checked before handing over: in each pack, every other model, buffer and material is the
game's byte for byte, and the Sherman reads back with the new shape (6,842 vertices, 3,278 stretched); read back from
the copy too. A side-by-side render, game's and ours: `D:\ruse-scratch\look\sherman_pair.png`. The copy also has the
T27 paint and the T31 card, so it's easy to spot. `D:\RUSE-Instances\model-check` (no fair play scripts).

1. Start `model-check` (Steam running), a skirmish as the US, build a Sherman (Armor Base).
- **Pass:** a tall Sherman (turret and hull top stretched up, wheels and tracks normal) with the paint, drawn up
  close and zoomed out; it drives, turns its turret and fires.
- **Tell us:** a crash (and when), an invisible or broken tank (spikes, holes, a normal-height Sherman), or anything
  odd when it moves or fires.

**Run 1 (2026-10-04, 02:17): crashed when he started building the Armor Base** ("broke once i went to build armor
base"). The dump: a model in the world asked for its size and had no model behind it (a null mesh). So a model of
one of the rewritten packs didn't load, before any Sherman was built. The packs had grown (the plain buffers: +173 KB
each); every change that has worked in the game kept the packs' sizes, and the one other time US model packs were
rebuilt bigger (2026-10-01, other nations' models copied in) the game also crashed at a factory placement. `model-check`
recycled.
**Run 2:** the same question with no size change: the whole Sherman 1.6 times taller (from the ground up), done by
patching the stored z range of its packed position streams (the floats are stored literals, so the streams keep
their size; each decoded and compared) and the z of its two plain buffers, and its box; every pack the game's size,
only those bytes changed (24 in each US pack, 3,260 in the level-design one). Wheels are stretched too, so they may
look odd turning. `D:\RUSE-Instances\model-check-2`.
First go (02:27): the game froze ("just stopped responding no crash"); its dump is a copy into memory it never got
(a write at 0x2aaaa0), with no game code named. Windows had 1.6 GB of memory left to give out right after (C: had 2.3
GB free, so the page file couldn't grow, and four leftover memory-plugin servers held 6.4 GB): the PC, not the model.
**PASSED (2026-10-04), second go.** The tall Sherman is built and drawn ("This isn't a normal Sherman, right?
... it looks like a [Stuart] almost"). **The game draws a model shape we wrote**, when the packs keep their size. As
built, it replaces the Sherman (no second unit): the owner wants both, a new unit with its own model. That needs a new
model in the packs, so they grow: the run 1 crash. Next: why a grown pack loses a model.
**Why run 1 crashed (found the same night):** each mesh and texture stand-in pack carries a 16-byte id at 0x10, the
MD5 of its bytes 0x00-0x0F and 0x20-0x2F (magic, version, file size, the places of the two parts the game reads). The
game checks it when it opens a pack and leaves out a pack whose id doesn't match. All 156 such packs the game ships
match; run 1's four grown packs kept their old ids, so none matched, and every model in them was missing. Our pack
writer (`rusemod.unitpacks`) now always writes the id (`header_id`); the 156 game packs still write back byte for byte.
`model-check-2` recycled.

## T33. Two Shermans: a new unit with its own model (2026-10-04)

The owner: "I want to have both Sherman". The game's M4 Sherman, unchanged, AND a second unit, **Tall Sherman**: a
clone of the Sherman (its own id 4059, menu place 306, its name, its class in the game's unit list) whose model is a
new one, `us_m4_sherman\coc_shermanm4tall_tirlod0`: the Sherman 1.6 times taller (T32 run 2's shape, which the game
drew). The new model is ADDED beside the Sherman's in its four mesh packs (they grow 48 to 77 KB, with the right ids),
and its name in the two skeleton packs (the Sherman's skeleton, shared). Checked before handing over: every game model
in those packs byte for byte as it was; the new one's vertices read back 1.6 times taller with everything else the
Sherman's; read back from the copy; the Tall Sherman's model link names the new model and the Sherman's the game's.
Plus the cheat mod. Mod: `D:\ruse-test-mods\two-shermans`; builder: private `testcopy\build_two_shermans.py`.
`D:\RUSE-Instances\two-shermans`.

1. Skirmish as the US, build the Armor Base.
- **Pass:** the build menu has both the M4 Sherman and the Tall Sherman (with the Sherman's card for now); the
  Sherman builds normal height, the Tall Sherman tall; both drive, turn their turrets and fire.
- **Tell us:** a crash (and when), a missing or invisible one, or both looking the same.

**PASSED (2026-10-04, 03:09-03:12).** The owner: "MADE TWO UNITS". His shots: the Armor Base menu lists SHERMAN and
Tall Sherman (at $25 before the upgrade, $1 after with the cheat mod); both built and standing side by side, the Tall
Sherman visibly taller. So packs that grow load when their ids are right, a model added under a new name is drawn,
and a cloned unit can name it. His UI bug: **both have the same picture** in the menu (the clone shares the Sherman's
card); a new unit needs its own. (Also seen, not raised: the new name is mixed case where the game's are capitals;
before the upgrade the Lee's upgrade row showed both Shermans.) The copy was rebuilt for T34.

## T34. A new unit's own card (2026-10-04)

The owner's UI bug from T33: the Tall Sherman showed the Sherman's picture. A new unit now gets its own card:
`files/cards/<the unit's name>.png` in its mod (the Studio puts it there when you make the card on a new unit's page,
instead of over its source's). The build points the clone's TextureForInterface at a file of its own beside its
source's (`DataDir:\WW2\Res2D\TexAnimationUnitIcone\EU\descriptor_unit_r2_m4_sherman_tall.png`, written as the game
writes its own), makes the picture from the source's card (same format and size) and adds it to the menu packs that
hold the source's (menuus.ppk 62 -> 63 files, outgame.ppk 273 -> 274; every game file in them unchanged; laid out as
the game's, which all 64 menu packs give back byte for byte). It isn't added loose in ZZ_Win.dat: the build menu shows
the menu packs' copies (T31). The copy is T33's (both Shermans, cheat mod) plus the Tall Sherman's card: the Sherman's,
flipped and tinted red. Read back from the copy. `D:\RUSE-Instances\two-shermans`.

1. Skirmish as the US, Armor Base.
- **Pass:** the Sherman's card as always, the Tall Sherman's red and facing the other way.
- **Tell us:** the Tall Sherman with no picture (a blank or missing card), still the Sherman's, or a crash.

**Answered by T35 run 1 (2026-10-04):** a new unit's own card shows in the build menu, and the game crashed when that
unit was built (the card wasn't a file of ZZ_Win.dat's own; fixed, retested in T35 run 2). This copy wasn't run; it
was recycled.

## T35. The first imported model: an M1 Abrams (2026-10-04)

The model importer's first test. A free M1 Abrams model (a .3ds with its .tga pictures, from a free-model site; test
only, never shipped) fitted to the Sherman by `rusemod.modelin` (its parts named hull, turret, barrel...; facing the
way its gun points; 1.36 times the Sherman's length, the real ratio; its turret ring on the Sherman's turret point)
and written as the mod's `files/models/Descriptor_Unit_R2_M1_Abrams.glb`. The build gives the new unit (a copy of the
Sherman, "M1 Abrams") that model: 17,122 points, 13,828 triangles, 5 draw calls (one per picture) in the four mesh
packs that hold the Sherman's; the Sherman's skeleton under the new name in both skeleton packs; its 4 pictures as new
textures loose in ZZ_Win.dat (DXT5, every level), each with a stand-in in the four stand-in packs that hold the
Sherman's (keyed by the CRC of its name). Every game model, stand-in and texture in those packs read back unchanged;
every pack's id right. Its own card too (T34's way). The test mod: `D:\ruse-test-mods\abrams` (with the cheat mod).
`D:\RUSE-Instances\abrams`.

1. Skirmish as the US, Armor Base: the M1 Abrams with its own card (the Abrams on a desert backdrop).
2. Build one, look at it up close and far off, move it, let it fight.
- **Pass:** the Abrams' shape and desert paint; bigger than a Sherman; its turret and gun turn to aim; it drives and
  fires.
- **Known, not a fail:** its wheels and tracks don't turn (they ride on the hull bone yet); the gun's flash shows
  where the Sherman's muzzle is (part way along the Abrams' longer gun); its wreck is the Sherman's; no side colour on
  it.
- **Tell us:** a crash (when?), no model or a Sherman instead, black/white/garbled paint, parts in the wrong place, or
  the turret swinging off its ring.

**Run 1 (owner, 2026-10-04 11:47): the game loaded, the Armor Base deployed, the M1 Abrams showed in its build menu
with its own card, researched and was bought; the game crashed when it was built.** The crash: a read of address 0
in the game's texture loading for its interface pictures, which asks every loaded source for the file by name and
got none. A unit's card is read from ZZ_Win.dat's own files once the unit is on the map (all 450 of the game's cards
are there as well as in the menu packs); the build had put the Abrams' card in the menu packs only (T34's way, which
is why the build menu showed it). Fixed: a new unit's card is also a file of ZZ_Win.dat's own. T34's copy
(`two-shermans`) has the same fault.

**Run 2 (rebuilt 2026-10-04):** the fix, the colour fix in the texture encoder, and a second unit, **M1 Abrams B**:
the same model with the Sherman's card, to tell the model from the card.
1. Build **M1 Abrams B first**. A crash then is the model; none, and the model works.
2. Then the **M1 Abrams**: its own card, now also a loose file.

**Run 2 (owner, 2026-10-04 12:13): both listed, both researched; building M1 Abrams B crashed the game, at the same
spot.** B has the Sherman's own card, so the card wasn't the cause (its fix stays: cards are loose files in the game
too). The cause, read from the game's code: a model's picture (`ZZ:\GenTexGroup\...\X.png`) is found through its
texture group, which is the start of the picture's own file name up to the first `_` (`TSCCombCS_CombinedDSC...`:
`TSCCombCS`, the group of every unit body picture). Ours were named `descriptor_unit_r2_m1_abrams_01.png`, a group
`descriptor` the game doesn't have, and the lookup's empty answer was used. Fixed: a new picture's name starts with
its copied body texture's group (`TSCCombCS_descriptor_unit_r2_m1_abrams_01.png`).

**Run 3 (rebuilt 2026-10-04):** the same two units with the pictures renamed; read back from the copy. Build M1
Abrams B first again, then the M1 Abrams.

## T30. Iwo Jima groundwork (2026-10-04)

(First written up as T27; that number was also taken by the Blender test above, so this one is T30.)

The pieces the Iwo Jima showcase rests on (`docs/IWO_JIMA.md`), in one Operation, all round your HQ. A new Operation,
**IWO JIMA TEST** (listed last in OPERATIONS): a copy of Swamps' US-against-Japan Operation, Gold for the Brave, so
Japan's units are at home, running a mission of ours, with your HQ moved onto Swamps' shore. Its scenario loads the US
models "with boats" (as the game's own D-Day and Italy chapters do), so the game's own hidden fleet can sail.
`D:\RUSE-Instances\iwo-groundwork` from `D:\ruse-test-mods\iwo-groundwork` (plus the cheat mod; US units 3 times as
fast): 0 errors. Read back from the copy: the mission and its texts, the packs, the scenario, and the ground: the bay
now under the sea, the island 23 m out of it, the cone 66 m up with its crater. The map of the spots:
`D:\ruse-test-mods\iwo-groundwork\t26_map.svg`.

Look round your HQ first (the map): **A** a new bay (land sunk into the sea), **B** a small new island raised out of the
sea with a causeway down to it from the cliff top, **C** a volcano cone, and **the US fleet** offshore (a battleship, a
cruiser, a destroyer, an LST, two LCVPs). Then, on their own:
1. About 3 s in: a popup and the goal **"WATCH THE FLEET AND THE BOMBERS"**.
2. About 23 s: **the fleet opens fire** on a spot on the far side of the bay (map 1).
3. About 48 s: **three bombers** come in from the sea and bomb a spot beyond the cone (map 2).
4. About 1:23: **three Japanese pillboxes** appear (map 3), with **two Crocodiles** and four Shermans for you by your HQ;
   goal **"BURN OUT THE 3 PILLBOXES"**. The Crocodiles' flame and the pillboxes' guns both reach about 300 m.
5. Then the goal **"DRIVE A TANK INTO THE CIRCLE"** (map 4). A tank in it: **"THEY'RE COMING OUT OF THE GROUND!"**,
   six squads of Japanese infantry appear there and go for your tanks; 20 s later, **another wave**.
6. Beat both waves: **VICTORY** 10 s later.
- **Tell us**, as far as you get:
  - **The bay:** sea from high up and up close? Do your units keep out of it?
  - **The island:** out of the sea? Can a tank drive down the causeway onto it? How does it look up close?
  - **The cone:** clear from your HQ?
  - **The ships:** there, on the water, the right way up? Does the battleship fire, and where do the shells land?
  - **The bombers:** do they come in and bomb?
  - **Pillboxes:** does the flame burn them out?
  - **The wave:** does it come out and charge?
  - **The goals:** main or bonus? The circle goal's label is drawn in the main goals' style, to see what decides it.
  - The first step that didn't happen, and anything odd (a crash, lag, a ship somewhere strange).
- Expected oddities: some of Gold for the Brave's own US units stay at its old start (far from your HQ); your HQ is
  about 760 m from the nearest road (supply isn't part of this test).

**Run 1 (2026-10-04): the fleet fired and the bombers came; the game stopped when the pillboxes were due.** In the
owner's words, it "made it through the bombers", the battleships kept shooting, and it stopped "when the pillboxes
started appearing". The game's own error text named the cause: our mission asked for `Unit_Bunker_enterre_JAP`.
That is the pillbox's gun unit, and it carries the building flag. The game's create step sends anything with that
flag to its building placer, which only takes a building, so it stopped with an error.
- **The fix:** the pillbox is the building, `Building_Def_Bunker_enterre_JAP`. It brings its gun unit with it. Eugen's
  missions always create defences by their `Building_` name (the Siegfried line in 12 missions, MG nests in 9), and
  none creates a defence's gun unit.
- **The guard:** the mission build now refuses a created unit that carries the building flag without being a building,
  and a unit name with no unit behind it. It passes every unit type the game's own missions create (228).
- Rebuilt the same day, 0 errors, and read back: the script names the building, and everything else is as before.
- Steps 1 to 3 were seen. The rest, and the "Tell us" list, wait for run 2.

**Run 2 (2026-10-04): passed, start to victory, no crash.** In the owner's words:
- "I made it through the objective", the fleet and bombers goal.
- "The pillbox is spawned. I can move my guys around. I can build the base."
- "Crocodiles killed the pillboxes."
- "They're coming out of the ground": the wave came and charged.
- "Another wave, man. Really didn't let me have a chance": the second wave came, and it was beaten.
- "Iwo Jima test is done. Nice. No crashes."

So every piece of our own mission works in the game. That covers the pillboxes made by the mission and burned out by
the Crocodiles, the "group is empty" goal on buildings, Japanese infantry made at a spot, the attack order on the
player's tanks, the repeat wave, and the victory.
- **Tuning for the real map:**
  - The wave spawned "like on top of me": it appears right where the player's tank enters the circle. In the
    Operation the tunnel exit should sit apart from the spot that sets it off, in the trees, so the Japanese rush out
    at the column instead of appearing inside it.
  - 20 s between waves left no breathing room. The next wave could wait for the last one to be beaten, or come later.
- **The black box:** "every time we're in one of these test operations, that black box appears and says nothing"
  (T22 and this one). It "appears right at the start. It's normally where the objectives are listed, but yours are on
  the side." It's the goals panel: our missions open it 4 s in (`DescriptorObjectifsPanel`, copied from Anzio), and
  nothing else in the game opens it except the Escape menu. In Eugen's missions it lists the goals; in ours it comes
  up empty, and why isn't found from reading alone. As the owner suggested, our missions no longer open it; the goals
  still show on the side. Not seen in the game yet: the next mission test shows whether the box is gone.
- **The owner's answers:**
  - "The bay looked kind of like the sea, but it's really small. There's no, like, mountain or anything. It's just a
    bigger map with a small beach." The cone was only 66 m tall and about 400 m across: a hill on Swamps' scale.
  - "Ships were sitting on the water, yep."
  - "They said main and bonus, I think." By the game's own goal code, all four of ours were main goals: a goal's
    label style decides it. Styles 0 (`Objectif_Primaire_Right`) and 12 (`Objectif_Primaire_Right_Folded`) are main;
    1 (`Objectif_Bonus_Right`) and 23 (`Objectif_Bonus_LowPosition`) are bonus. Ours were all 12. This answers
    T22's open question.
- Recorded; the copy `D:\RUSE-Instances\iwo-groundwork` goes to the Recycle Bin (the mod source stays).

## F1-F3. RUSE Guard, our half (fair play; 2026-10-04, not run yet; parked: fair play is switched off until the owner says)

Fair play (`rusemod.fairplay`, PLAN §14): a mod set with a cheat or a test tool makes an **offline** copy, which
leaves multiplayer and co-op matches; every other copy has a **join code** to compare with the people you play with;
mods that run scripts wait for **"I trust this author"**; the **watcher**, in every modded copy, says on screen
when a match sees a cheat order. The lock and the watcher go in every map's own script folder (68 folders, the
1.5 MB IA_Common.dat; the game looks there before its own scripts, as Eugen's co-op maps' own multiplayer scripts
show); the 2.4 GB ZZ_Win.dat stays a free link. Checked before handing over, without the game: the map's skirmish
script (the game's own, then ours) run under the game's Python version against stand-ins, with the game's real match
rules module (an offline match: the watcher only; an online one: the message, then the surrender 5 s in; a spawn
order and a +530 money jump flagged; a second script in the same session switches nothing on twice);
`tests/test_fairplay.py` (on the game's own files too). **No test copy built yet.** The one thing only the game can
show: that a map's own folder copy is the one that runs. If F1's message never shows, that's the place to look.
**Until F1 and F3 pass, everyday builds leave our game scripts out** (`fairplay.IN_BUILDS = False`): an earlier form
of them stopped the owner's game at map load on 2026-10-04 (a Studio Test in game built from the project folder; they
ran inside the game's match rules module while it was still loading). The F1/F3 copies are built with them on.

**F1. The offline lock in a real match** (needs a second player: a friend, or a second PC and Steam account).
1. Build a set with a cheat in it (the cheat mod) and press Play. The build log says "offline only: …"; the Join code
   box says the copy is for offline play.
2. Skirmish against the AI: plays as normal (nothing on screen, no surrender).
3. Host or join a multiplayer match with the other player (vanilla on their side is fine).
- **Pass:** at the start the message "This copy of R.U.S.E. was built with cheats or test tools…" shows, and about
  5 s in the match is given up for you; the other player sees you surrender.
- **Tell us:** whether the message showed, whether the surrender came, anything else (a crash, a stuck screen).

**F2. The Launcher: join codes, the trust tick, the cheat badge** (the Launcher run from the project folder; no match).
1. Library: a mod that runs scripts (Formations, or any .rmod with scripts) has a red "Runs scripts" badge. Play a set
   with it: Play stops and asks for the tick. Tick "I trust this author": Play goes on, the badge turns blue.
2. A cheat from Supported mods shows a red "Cheat" badge.
3. Play a set without cheats, then "Join code" at the bottom: a code starting RUSE1:, Copy works. Paste the same code
   and Compare: "Same game". Paste a code from a different set: what differs is listed.
4. "Check every file of the copy": "Every file checked…" after a few seconds.
- **Pass:** each step as said.

**F3. The watcher, offline** (skirmish against the AI; the test tool's own +500 button stands in for a cheater).
1. Make a set with Dev Toolkit (it's a test tool, so the copy is offline; that only matters online) and press Play.
2. Play a skirmish about 10 minutes normally: supply trucks, buildings, the AI. **Note any watcher message**: none
   should show.
3. Then the Dev tab's +500: "player N got 500 money at once".
- **Pass:** step 3's message, and nothing in step 2. A message in step 2 means normal money comes in steps of 400
  or more somewhere: tell us what you were doing, and the step gets raised. No message in step 3 means the map's
  folder copy didn't run (see above).

**F4. RUSE Guard's in-game record** (two PCs, an honest multiplayer match; needs fair play switched on and the
in-game scripts allowed in the build).
1. Both players Play the same mod set (the same join code) and play a multiplayer skirmish for 5 minutes.
2. After the game closes, each copy's folder had `ruse_guard_match.txt`: the Launcher collected it into its outbox.
- **Pass:** the file was written at all (the game's scripts may write files), its `state` lines came every 10 s,
  and the two players' `state` lines are identical (DomesticNukes' T3: two honest games give the same series).
- **Tell us:** no file (the game refused to write it), or the first line where the two differ.

## T29. Another nation's units in a campaign chapter (2026-10-03)

(First written up as T22, a number another test, our own mission, also took; renumbered when both met.)

A player (Oozaru, Discord) crashed loading Holland's campaign map with a build that spawned French units. Campaign
chapters and Operations load the unit models of only the nations they play (Holland's chapters: US, Germany, UK), and
the build's fix for other nations' units reached skirmishes only. Now a nation a mod needs is added to every mission's
own list too (France here: 29 loaders in 14 missions). `D:\RUSE-Instances\campaign-fr` from
`D:\ruse-test-mods\campaign-fr` (plus the cheat mod): 0 errors. Read back from the copy: Holland's and Colditz's
lists hold France's packs, France's skeletons ride with the other nations', and the spawns are the player's.
1. CAMPAIGN: **1. COLDITZ CASTLE** (always open). Beside your starting Pershings: 4 French **B1 Bis** tanks and 2
   French infantry squads, yours.
   - **Pass:** the mission loads; the French units are drawn, can be selected and move.
   - **Fail:** a crash while loading or as the mission starts, or the French units invisible.
2. If it's unlocked: **13. SCREAMING EAGLES**, the player's map. 4 B1 Bis on one side of your HQ, 2 French squads
   on the other, 120 m from it. Pass / Fail as above.

**Result (owner, 2026-10-03, 22:42): Colditz PASSED** ("colditz worked fine", two shots): the mission loaded and ran
("ADVANCE UPON THE FRONT"), the 4 B1 Bis drawn beside his Pershings, the French infantry there too. Screaming Eagles
wasn't tried (not unlocked in his campaign); it gets the same change.

## T11. Launcher 0.2.9

- **Pass:** the launcher offers 0.2.9 when it opens; **Update** installs it and it starts again; **Play** works.

## Later

- **Browse mods:** once `sneadtristen6/Ruse-Mods` exists with an `index.toml`.
- **China, an 8th nation:** step 2 of M10, when its test copy is built.
