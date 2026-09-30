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

Open the launcher with `py -3 -m ruse_launcher`.
1. Click **Add a mod file…** and add a `.rmod`. Then make a mod set with it and press **Play**.
2. On the set, click **Share**. Then use **Import a load order…** with that text.
- **Pass:** the mod works in-game, and the imported set has the same mods in the same order.
- **Extra:** a load order copied from RUSE Mod Manager imports too.

## Later

- **Browse mods:** once `sneadtristen6/Ruse-Mods` exists with an `index.toml`.
- **China, an 8th nation:** step 2 of M10, when its test copy is built.
