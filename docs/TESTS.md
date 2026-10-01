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
- **Then, if it passes:** past 8 (a 10-player copy, 5v5) tells whether the program caps it.

## T13. A unit given to another nation (Studio 0.7.7)

A nation's unit models only load in a match where a player has that nation. So for a unit given to another nation,
the build now has its models' nation load in every skirmish. Untested in the game until now.
1. In the Studio, make a mod (or pick a test one), open the German **Ju 87** (`Descriptor_Avion_Junkers_87`) and
   click **New unit…**. Name it "Stuka US", set price 5, and put it in **another nation's factory**: the US air
   factory.
2. Click **Test in game**. The build's report has two notes: `Germany's unit models and animations now load in every
   skirmish ... (255 loaders in 85 cluster maps ...)`, and one saying the Stuka US uses Germany's models. There are no
   errors.
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

## T11. Launcher 0.2.9

- **Pass:** the launcher offers 0.2.9 when it opens; **Update** installs it and it starts again; **Play** works.

## Later

- **Browse mods:** once `sneadtristen6/Ruse-Mods` exists with an `index.toml`.
- **China, an 8th nation:** step 2 of M10, when its test copy is built.
