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

## T11. Launcher 0.2.9

- **Pass:** the launcher offers 0.2.9 when it opens; **Update** installs it and it starts again; **Play** works.

## Later

- **Browse mods:** once `sneadtristen6/Ruse-Mods` exists with an `index.toml`.
- **China, an 8th nation:** step 2 of M10, when its test copy is built.
