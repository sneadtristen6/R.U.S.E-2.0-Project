<div align="center">

# R.U.S.E. 2.0

**Build the battlefield, then fight on it.**

<img src="docs/images/bridge-infantry-at-deck-height.jpg" alt="R.U.S.E. in game: two infantry squads and a supply truck crossing a new bridge, every man standing at the deck's height" width="800">

[![Download RUSE Launcher](https://img.shields.io/badge/Download-RUSE%20Launcher-b8913a?style=for-the-badge)](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher)
&nbsp;&nbsp;
[![Download RUSE Studio](https://img.shields.io/badge/Download-RUSE%20Studio-b8913a?style=for-the-badge)](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio)

<sub>Windows. Needs R.U.S.E. on Steam. Never touches your Steam install.</sub>

</div>

## What R.U.S.E. 2.0 is

**A game that plays a game with R.U.S.E.** It learns how R.U.S.E. reads every file it uses, and checks your mod the
way the game will before the game ever starts: anything that would break in the game is stopped first, with a note
saying what to change. The goal: what you make works in the game every time, the first time.

## Bridges work. Map making starts here.

Reshape any R.U.S.E. map. Hills, towns, roads, and bridges your units actually cross. Draw a road in RUSE Studio.
Where it meets water, the build puts the map's own kind of bridge across it, and tanks, infantry, and supply trucks
cross on the deck. Roads and bridges are what new maps get built on, so this is the piece everything else stands on.

<table>
  <tr>
    <th width="50%">Before</th>
    <th width="50%">After</th>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <img src="docs/images/bridge-before-in-the-river.jpg" alt="R.U.S.E. in game: the new bridges before the fix, a tank and squads standing in the river under the decks" width="400">
    </td>
    <td width="50%" valign="top">
      <img src="docs/images/bridge-two-crossings.jpg" alt="R.U.S.E. in game on D-Day: two new bridges over the same river, units crossing both" width="400">
    </td>
  </tr>
</table>

Twelve hours, six rounds of testing. [The full story](docs/LESSONS.md)

## What you can do on a map

<table>
  <tr>
    <td width="33%" valign="top">
      <img src="docs/images/terrain-ingame-hill.jpg" alt="R.U.S.E. in game on Blitz: a hill raised with the Studio's brushes, units driving up it" width="260"><br>
      <sub>A hill raised with brushes. Units drive up it.</sub>
    </td>
    <td width="33%" valign="top">
      <img src="docs/images/terrain-ingame-units.jpg" alt="R.U.S.E. in game: units on top of the raised hill, the town of Cahir lifted with it" width="260"><br>
      <sub>The town and its trees rise with the ground.</sub>
    </td>
    <td width="33%" valign="top">
      <img src="docs/images/map-cover-hidden.jpg" alt="R.U.S.E. in game on Blitz: infantry on top of a painted cover patch, shown as hidden" width="260"><br>
      <sub>Painted cover. Infantry on it are hidden.</sub>
    </td>
  </tr>
  <tr>
    <td width="33%" valign="top">
      <img src="docs/images/map-placed-buildings.jpg" alt="R.U.S.E. in game on Blitz: water towers at 8 times their size around a hill, barns at 6 times around a pit" width="260"><br>
      <sub>Buildings placed by a mod, up to 8x size.</sub>
    </td>
    <td width="33%" valign="top">
      <img src="docs/images/movement-solid-towers.jpg" alt="R.U.S.E. in game on Blitz: a tank stopped between two giant placed water towers instead of driving through them" width="260"><br>
      <sub>Placed buildings are solid. Tanks go around.</sub>
    </td>
    <td width="33%" valign="top">
      <img src="docs/images/roads-bridges-ingame.jpg" alt="R.U.S.E. in game on D-Day: new roads drawn in the Studio, painted on the ground, with a new bridge where each crosses the river" width="260"><br>
      <sub>Roads drawn in the Studio, bridges over water.</sub>
    </td>
  </tr>
  <tr>
    <td width="33%" valign="top">
      <img src="docs/images/cleared-wood-infantry-not-hidden.jpg" alt="R.U.S.E. in game on D-Day: a round hole cleared in a dense wood by a mod, an infantry squad standing in it, not hidden" width="260"><br>
      <sub>A wood cleared by a mod. Tanks drive in, infantry aren't hidden there.</sub>
    </td>
    <td width="33%" valign="top">
      <img src="docs/images/dried-riverbed-walked.jpg" alt="R.U.S.E. in game on D-Day: infantry and a tank walking along a river bed a mod drained" width="260"><br>
      <sub>A river drained by a mod. Units walk its bed.</sub>
    </td>
    <td width="33%" valign="top">
    </td>
  </tr>
</table>

| For players | For modders |
|---|---|
| Pick a mod set and press Play | Change any unit's numbers, then test in game |
| Drop mod files on the window to add them | Make new units |
| Run community mods as they are | Shape the ground with brushes |
| Share a load order with a friend | Draw roads with bridges over water |
| New versions install themselves | Place buildings, cover, and starting points |
| Tick mods from our supported list | Clear the map's own woods and props |
| Troubleshoot finds what stops Play, and fixes it | Check a map before you test it |

<details>
<summary><b>Everything the apps can do</b></summary>

A modding platform for R.U.S.E. Its aim, step by step: new units, maps, models, missions and one-click modded
multiplayer (today: units, and the first map tools). The content goals on top are RUSE 2.0 and Pacific Island
Defense.

**Your Steam install is never changed.** Mods are built into a separate modded copy of the game (hard links to the
game's packs, plus the packs a mod rebuilds), and Play starts that copy.

<p align="center">
  <img src="docs/images/studio-maps.jpg" alt="RUSE Studio's Maps view: D-Day in 3D with its towns, the battle's zones and starting points, and the map tools along the bottom" width="800">
  <br>
  <sub>RUSE Studio's Maps view: every map the game ships, in 3D, with its real ground, water and towns. Here, D-Day
  with its battle's zones and starting points, and the map tools along the bottom.</sub>
</p>

**Players, with RUSE Launcher**

- Pick a mod set and press **Play**: the launcher builds a modded copy of the game and starts it.
- Add a mod file (a `.rusemod` from the Studio, a community `.rmod` used as it is, or a `.zip`), or drop it on the
  window.
- Make and reorder mod sets in the window.
- Share a mod set's load order with a friend, or import one. It's the same text RUSE-Mod-Manager copies and reads,
  so load orders go both ways.
- **Supported mods:** tick mods from our list and they're downloaded and checked; cheat mods are kept apart and
  never ticked for you (Launcher 0.3.0).
- **Troubleshoot** checks in one go what can stop **Play** and fixes what it can, and a **clean game backup** puts
  back game files another mod manager changed (Launcher 0.3.0, Studio 0.8.0).
- Get new versions without downloading by hand: the launcher offers them, checks the file and installs it (from
  0.2.0 on).

**Modders, with RUSE Studio**

- Browse every unit and building by its code name or in any of the game's ten languages.
- Change a unit's numbers in your own mod, with Undo, then **Test in game**.
- See every map in 3D with its real ground, listed by the name players know (in any of the ten languages) next to
  its code name, with the game's own 3D models of its buildings and trees.
- Make new units, and give a weapon another unit's ammo (its muzzle flash and sound come with it).
- Shape a map's ground with brushes (hills, craters, ramps, level, lakes) that **work in the game**: units drive on
  it and take orders there (checked on Blitz, 2026-09-30).
- **Make towns and woods units hide in:** the map view shows where units hide (in green), and the Cover, Uncover and
  Town brushes paint it (Town: click a town, cover goes around all its buildings). Infantry on painted cover are
  hidden in the game (2026-09-30).
- See each map's scenarios, grouped as the game uses them (skirmish, Operations, campaign): zones, starting points,
  spawns and town names. **Move** starting points and spawns, and **add units and buildings** a scenario starts with
  (pick the kind, the type, the unit and its side).
- Place buildings, props and trees, up to 10× their size, and export a mod as one file. Placed buildings show in the
  game (2026-09-30, Studio 0.6.9).
- **Say where units can go:** the map view shows it (red: no unit, yellow: infantry only), the Block brushes close
  ground to every unit, to infantry or to vehicles, and placed buildings stop units (Solid). Proven in the game
  (2026-09-30, Studio 0.7.0).
- The map tools sit in a bar along the bottom, Cities: Skylines style, in R.U.S.E.'s own HUD look (Studio 0.7.0).
- **Draw roads**, Cities: Skylines style (straight, curved, freeform; ends snap onto roads; their length shown as
  you draw): supply routes use them, they're painted on the ground, and a road over water gets a bridge units drive
  across, all in the game (2026-09-30, Studio 0.7.2 to 0.7.6). Tanks, infantry and supply trucks cross a new
  bridge on its deck, and infantry follow new roads (2026-10-01, Studio 0.8.0).
- **Clear woods and props** (`[[erase]]` in scenery.toml): units drive into a cleared wood and infantry there are no
  longer hidden; a **Bridges dock** places a bridge by hand; **Check this map** lists what would go wrong before you
  test; Open and Forest brushes (2026-10-01, Studio 0.8.0).
- **More players on a map, up to 8:** a Players count and an Add starting point tool (D-Day as a 4v4; built, the
  in-game check is next).
- **Add units in formations:** 1 to 10 at once, in a line, column, wedge, box or circle (Studio 0.7.1).
- A **mod check** reads every file of your mod the way the game build does, names each problem and offers the fix
  (set a broken file aside, rename a map folder to the map's pack name) (Studio 0.7.1).
- **Help at hand:** both apps open the wiki, Discussions and a ready-filled bug report (Studio 0.7.1, Launcher
  0.2.7).
- Units, buildings and ammunition sorted by type (factories, money, forts, decoys; AP, HE, anti-aircraft...).
- A Settings tab (language, keys, game folder, updates), kept through updates. The Studio offers its own new
  versions.

Modders who write mods by hand can also use the `ruse` command-line tool, from the source (see
[For contributors](#for-contributors) below).

<table>
  <tr>
    <td width="50%" valign="top">
      <img src="docs/images/launcher.jpg" alt="RUSE Launcher: mod sets on the left, how to play with mods in three steps, and Play" width="380"><br>
      <sub>RUSE Launcher: pick a mod set and press Play. It builds a separate modded copy of the game; your Steam
      game stays as it is.</sub>
    </td>
    <td width="50%" valign="top">
      <img src="docs/images/launcher-set.jpg" alt="RUSE Launcher: a set of 75 mods, with why it can't be played and which mods overwrite which" width="380"><br>
      <sub>A set of 75 community mods: the launcher says which can't go together, and which overwrite which.</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <img src="docs/images/studio-unit.jpg" alt="RUSE Studio: a unit's values, ready to edit" width="380"><br>
      <sub>RUSE Studio: a unit's values, flags and price, ready to edit.</sub>
    </td>
    <td width="50%" valign="top">
      <img src="docs/images/studio-units.jpg" alt="RUSE Studio: the unit list, with filters by type and nation" width="380"><br>
      <sub>RUSE Studio: the unit list, with filters by type and nation.</sub>
    </td>
  </tr>
</table>

**Map making, in the game, in more detail:**

- Blitz, in the game: a hill raised with the Studio's brushes. Units drive up it and take orders on it, and the
  player's HQ starts at a place the mod moved it to.
- On top of the hill: the town of Cahir and its trees rise with the ground (2026-09-30). The recipe is
  DomesticNukes and his Claude's.
- Cover painted on open ground (here on a test hill): the infantry standing on it are hidden, as in a wood. That's
  how new towns and woods hide units.
- Buildings placed by a mod: water towers at 8× their size ring the hill, barns at 6× ring a pit next to it
  (2026-09-30).
- Movement, later the same day: placed buildings are solid (the tank threads between the towers), and a pit is
  blocked for every unit. The map's own movement data is read and written now.
- D-Day: roads drawn in the Studio, painted into the ground, and a bridge where each crosses the river: the map's own
  kind, one piece stretched bank to bank as the game's own are (2026-09-30).

<table>
  <tr>
    <td width="50%" valign="top">
      <img src="docs/images/movement-building-on-hill.jpg" alt="R.U.S.E. in game on Blitz: a building being placed by the player on the edited hill" width="380"><br>
      <sub>Building on the edited ground in the game works too. Four crashes on the way were read from the game's
      crash dumps and fixed the same evening (docs/LOG.md).</sub>
    </td>
    <td width="50%" valign="top">
      <img src="docs/images/bridge-tanks-ingame.jpg" alt="R.U.S.E. in game on D-Day: tanks driving across a new bridge, on its deck" width="380"><br>
      <sub>Tanks crossing on a new bridge. Each gets the floor of a shipped bridge of its kind, so units drive on the
      deck, not the riverbed under it (2026-09-30).</sub>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <img src="docs/images/bridge-tank-and-squad.jpg" alt="R.U.S.E. in game on D-Day: a tank and an infantry squad crossing a new bridge the build placed where a road drawn in the Studio meets the river" width="380"><br>
      <sub>A road drawn in the Studio meets the river, the build puts the map's own kind of bridge across it, and units
      take it: a tank and a squad on the deck (D-Day, in the game, 2026-10-01).</sub>
    </td>
    <td width="50%" valign="top">
      <img src="docs/images/bridge-tank-column.jpg" alt="R.U.S.E. in game on D-Day: a column of tanks crossing a new bridge" width="380"><br>
      <sub>A tank column on its way over.</sub>
    </td>
  </tr>
</table>

**The bridge night (2026-10-01).** One night, twelve hours, six rounds of building a bridge and testing it in the
game. Five rounds changed where units may *walk*. What settled it was working out how the game places a unit: its
position comes from the map's movement circles, its height from the floor under it, and nothing ties the two. An
infantry squad is five men spread 11 m wide, each standing on whatever floor is under his own feet. The game's metal
bridges carry invisible floor 47 to 66 m out over the river beside the deck; ours had the deck alone, so the men
beside it stood on the riverbed. New bridges now get floor 12 m out each side, over water only, in the deck's own
plane. On the way: decks joined to the roads units already use, never through a farmyard; a mod's buildings no
longer open the water beside the map's own bridges; the floor file keeps the game's own rules (men stopped lying
sideways). The full story and the checks that came out of it: [docs/LESSONS.md](docs/LESSONS.md). The movement-map
reading is shared with DomesticNukes and his Claude.

</details>

## Install in three steps

1. **Download** the installer from [Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases):
   `RUSE-Launcher-Setup-<version>.exe` for players, `RUSE-Studio-Setup-<version>.exe` for modders. Windows only. You
   need R.U.S.E. in your Steam library, installed.
2. **Run it.** No admin rights and no Python needed. The installers are not code-signed yet, so Windows may warn once
   ("Windows protected your PC"): click **More info**, then **Run anyway**. Your browser may also warn about a new
   download. To check you have the real file, compare its SHA-256 with the one in the release notes.
3. **Start it** from the Start menu. It finds R.U.S.E. through Steam. In the launcher, pick a mod set and press
   **Play**. In the Studio, build the game index once when it asks (about a minute), then pick or make a mod.

Uninstalling keeps your mods and settings. The apps need Microsoft Edge WebView2, which Windows 11 has; if a PC
doesn't, the app says so. The Studio's 3D map view needs the internet the first time it opens (it loads its 3D
library from the web). To try what is merged but not released yet: the repo's **Actions** tab, the latest **apps**
run, **Artifacts** (needs a GitHub login; the files expire after 90 days). More in
[installers/README.md](installers/README.md), including what to do about browser warnings.

<details>
<summary><b>Status</b></summary>

[![Launcher release](https://img.shields.io/github/v/release/sneadtristen6/R.U.S.E-2.0-Project?filter=launcher-v*&label=launcher)](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher)
[![Studio release](https://img.shields.io/github/v/release/sneadtristen6/R.U.S.E-2.0-Project?filter=studio-v*&include_prereleases&label=studio)](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio)
[![tests](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/actions/workflows/tests.yml/badge.svg)](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/actions/workflows/tests.yml)
[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue)](LICENSE)

**Launcher** for players (latest: 0.3.0) &middot; **Studio** for modders, a preview (latest: 0.8.0) &middot; Windows &middot; needs R.U.S.E. on Steam

Early, and moving fast. **Proven in the game:** value and text mods, new names in all ten languages, new units that
are built and fight, maps with their own pack, terrain texture tiles we write ourselves, a first `.rmod` check
(two community mods in one modded copy), and on 2026-09-30: terrain brushes (hills, pits, level
ground that units drive on and take orders on), a moved starting point, painted cover that hides infantry, placed
buildings (at up to 8× their size), and both apps updating themselves; on 2026-10-01, roads with new bridges
that tanks, infantry and supply trucks cross, infantry following new roads, a bridge placed by hand, a building at
10× standing on the ground, a dried riverbed units walk, and a cleared wood tanks drive into and infantry no longer
hide in. **Not yet checked in the game:** a new unit
made in the Studio's window, mod sets made in the launcher's window, a mod exported as one file, sharing a load
order, units a skirmish spawns, and Browse mods. The tests, step by step for anyone with the game:
[docs/TESTS.md](docs/TESTS.md).

<details>
<summary><b>Current stage (2026-10-01)</b></summary>

- **Studio 0.8.0 and Launcher 0.3.0** (2026-10-01): the audit of every file the build writes against what the game
  does with it (a mod that would break in the game is refused, with why), units following new roads, woods and props
  cleared by a mod (`[[erase]]`), placed objects on the ground at any size, cover painted in place on the 8 maps that
  aren't square, the Bridges dock, Check this map, Open and Forest brushes, Troubleshoot and a clean game backup in
  both apps, and the Supported mods list in the launcher. Tested in the game in three batches
  ([docs/TESTS.md](docs/TESTS.md)). Known issue: new roads aren't drawn up close yet.

- **Map making works in the game** (Blitz, 2026-09-30): the Studio's terrain brushes (the recipe is DomesticNukes
  and his Claude's), a moved starting point, painted cover (`maps/<map>/cover.toml`, or the Studio's Cover, Uncover
  and Town brushes: units there are hidden), and placed buildings, which now go in a new block wrapped around a block
  the map draws from far (FORMATS.md §6).
- **Scenarios:** every map's scenarios read and shown on the map; mods move starting points and spawns and add units
  and buildings a scenario starts with (`maps/<map>/scenario.toml`). Which side number is the player in a skirmish
  is the next in-game check.
- **Movement works in the game** (Blitz, the same night): the map's navigation graphs (`mapinfo.win`, one for
  infantry and one for vehicles: circles units plan through, with a spatial index) are read and written
  byte-identical (`rusemod.nav`). Mods block ground (`maps/<map>/movement.toml`), the ground freed around a block is
  filled back, and every building a mod places is solid. The road network is the same file's first part; the road
  tool will write it.
- **Community mods:** `.rmod` files (RUSE-Mod-Manager, by LittleGroove) work as they are, through LittleGroove's own
  engine (PLAN.md decision 26); all 75 on hand apply with 0 errors.
- **Roads and bridges in the game** (D-Day, 2026-09-30): a new road is a road to supply trucks (the network,
  `mapinfo.win`'s first part) and painted into the ground's picture (seen from afar); laying the game's road stickers
  along it too (the Route pieces, what draws a road up close) is built, but **doesn't work yet: up close a new road
  disappears** (TESTS.md T12, failed in the game; being worked on). Where it
  crosses water it gets the map's own bridge, one
  piece stretched bank to bank, with a floor copied from a shipped bridge of its kind (`occlusioninfo_objectsonly.kdt`,
  what units stand on): units cross on the deck. Each deck is joined to the ground units already use along the
  road, and the build never writes ground units can't reach (that crashed the game: every shipped movement graph
  is one piece). **Units cross in the game, infantry at the deck's height** (2026-10-01): a new bridge's floor
  reaches out over the water beside the deck, as the game's metal bridges' does (an infantry squad's men each stand
  on the floor under their own feet); see the milestone above and [docs/LESSONS.md](docs/LESSONS.md).
- **Test in game / Play always rebuild** (Studio 0.7.6, Launcher 0.2.11): a modded copy Windows won't delete is
  moved aside into `RUSE-Instances\.trash` instead of stopping the game, and a game still running from the copy is
  named.
- **8 players:** a map's count is its menu entry (`TMultiMapInfo`) and a starting point per player; mods set both
  (`maps/<map>/map.toml`, `[[start]]`). D-Day as a 4v4 is built; the lobby check is next.
- **Next** (PLAN.md §10): new roads drawn up close; units from another nation that work (a captured Tiger for the
  US); the map maker the Cities: Skylines way: an Erase tool in the Studio, forest tracks for infantry only, ruse
  areas, ground painting, finer terrain; then new maps in the game's menus and join codes.
- Decided: RUSE 2.0 gets a real 8th nation, China (PLAN.md §6, decision 19).

The order is in [PLAN.md §10 "Now"](docs/PLAN.md#10-now); the latest decisions are in PLAN.md §6.

</details>

</details>

<details>
<summary><b>Docs</b></summary>

**[Field manual (wiki)](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/wiki)** &middot;
**[Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions)**: questions, ideas, bug reports and
mods to show

| Doc | What it covers |
|---|---|
| [docs/PLAN.md](docs/PLAN.md) | vision, principles, architecture, roadmap, risks, open decisions |
| [docs/FORMATS.md](docs/FORMATS.md) | what we know about every game file format (the project's memory) |
| [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) | draft spec of the mod package format |
| [docs/RESEARCH.md](docs/RESEARCH.md) | what others already built, and the chosen tech stack |
| [docs/LITTLEGROOVE_STUDY.md](docs/LITTLEGROOVE_STUDY.md) | what RUSE-Mod-Manager does, where it stops, and how we go further |
| [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md) | ideas learned from studying the game's own files (esp. its Python scripting layer) |
| [docs/TESTS.md](docs/TESTS.md) | the in-game tests, step by step, for anyone with the game |
| [docs/TASKS.md](docs/TASKS.md) | briefs for the cloud sessions |
| [docs/LOG.md](docs/LOG.md) | what each session did, newest last |
| [docs/ANNOUNCEMENTS.md](docs/ANNOUNCEMENTS.md) | what we post to the community, newest first |

</details>

<a name="for-contributors"></a>
<details>
<summary><b>For contributors</b></summary>

<details>
<summary><b>Code so far</b>: the engine, the <code>ruse</code> tool and what it builds</summary>

Four parts, in `src/`: `rusemod` (the game's files, the mod system, building modded copies, the `ruse` tool),
`ruse_mod_engine` (LittleGroove's RUSE-Mod-Manager engine, used as it is for `.rmod` mods), and two apps built on
them, `ruse_launcher` and `ruse_studio`.

- **The `ruse` tool** ([`src/rusemod/cli.py`](src/rusemod/cli.py)): with `PYTHONPATH=src`, run
  `py -3 -m rusemod <command>` (or `pip install -e .` once, then just `ruse <command>`). It never writes into the
  game folder.
  ```
  ruse detect                                   find R.U.S.E. through Steam, show build and branch
  ruse ls ZZ_GladPatchableWin.dat gfx           list files in a pack (nested packs: ZZ_Win.dat!eugen.ipk)
  ruse names ZZ_GladPatchableWin.dat Sherman    list named objects
  ruse dump ZZ_GladPatchableWin.dat everything.cpp.gladndfbin Tourelle_MG   show data as text
  ruse extract ZZ_GladPatchableWin.dat mapinfo  copy files out, into extracted/ (ignored by git)
  ruse build mymod/ other.rndf --instance D:\RUSE-Instances\test   build mods into a modded copy of the game
  ruse index build                              index the whole game once per game build (read-only)
  ruse index show $/GFX/Everything/Descriptor_Unit_M4_Sherman   an object, what uses it and what it uses
  ruse index filter TUniteAuSolDescriptor ProductionPrice[0] gt 100   units by their numbers
  ruse index clone $/GFX/Everything/Descriptor_Unit_M4_Sherman   what a copy would copy and share
  ruse index texts Sherman                      search the game's texts
  ```
  `build` takes mod folders (`mod.toml` + `src/**/*.rndf`, [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md)), `.rmod` files
  or single `.rndf` files, shows the load order and every error / warning / note, and writes nothing if there's an
  error. Value changes work end to end (C4). New units work too (C7): a copied unit gets its own id, debug name and
  build-menu slot ([`src/rusemod/identity.py`](src/rusemod/identity.py);
  [`examples/cloned-unit/`](examples/cloned-unit/), PLAN.md §7). New units get their own names from a mod's
  `text/*.csv` ([`src/rusemod/loc.py`](src/rusemod/loc.py); C6, [`examples/named-unit/`](examples/named-unit/)).

- **Mod rules engine** ([`src/rusemod/patch.py`](src/rusemod/patch.py), [`src/rusemod/resolve.py`](src/rusemod/resolve.py)):
  load order and every rule in [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) §10 (stacking, rounding, the conflict table,
  clones, shared parts, `patch every`, the final pass, `when mod`), tested on made-up data. It runs on the real game
  files through the bridge ([`src/rusemod/model.py`](src/rusemod/model.py)), which writes changed values, new objects
  and deletes back into them.
- **Mod file reader** ([`src/rusemod/rndf.py`](src/rusemod/rndf.py)): reads `.rndf` mod text (MOD_FORMAT §5, WARNO
  spellings) into operations for the engine, with errors that give file, line and column. Mods can find an object by
  a property (`@TAmmunition[AmmunitionId=1120]`, `patch every TUniteAuSolDescriptor [Nationalite=1]`), reach unnamed
  parts, and refer to a game object's part (MOD_FORMAT §4).
- **New units** ([`src/rusemod/pyscript.py`](src/rusemod/pyscript.py)): the game only uses units that have a class
  in its Python unit list, so `ruse build` gives every copied unit one, from a single fixed template that's checked
  before it's written. Mods in our own format can never bring scripts (PLAN.md decision 23); the one exception is a
  `.rmod`, which may replace the game's own scripts, with a warning (decision 26, see Community mods below).
  [`tools/verify_pyscript.py`](tools/verify_pyscript.py) checks it against the real game.
- **Community mods** ([`src/rusemod/rmod.py`](src/rusemod/rmod.py), [`src/ruse_mod_engine/`](src/ruse_mod_engine/)):
  `.rmod` mods are applied by LittleGroove's own engine, in memory on top of the game's packs, then written into the
  modded copy like every other change (PLAN.md decision 26). `.rmod` mods apply first, in set order, our mods on top;
  a mod made for another game build is moved with LittleGroove's version maps. A `.rmod` may replace the game's own
  scripts, with a warning in the build report; programs are refused. [`tools/rmod_to_mod.py`](tools/rmod_to_mod.py),
  our own reader of the format ([docs/MOD_FORMAT.md §13](docs/MOD_FORMAT.md)), still rebuilds one as a mod of ours
  for editing; the mods rebuilt that way are kept in the private shared repo until their authors agree.
- **Load orders** ([`src/rusemod/loadorder.py`](src/rusemod/loadorder.py)): a mod set's load order as text to share,
  in RUSE-Mod-Manager's own block (`=== R.U.S.E. Load Order ===`), so the launcher's Share and "Import a load
  order…" work both ways with it.
- **Updates** ([`src/rusemod/update.py`](src/rusemod/update.py)): both apps ask GitHub Releases for their newer
  release; the installer is checked against GitHub's SHA-256 and the release notes' before it runs silently.
- **Fingerprints and join codes** ([`src/rusemod/lock.py`](src/rusemod/lock.py)): the multiplayer "seal number" and
  the pasteable join code from [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) §12.
- **Terrain brushes** ([`src/rusemod/brush.py`](src/rusemod/brush.py), [`terrain_edit.py`](src/rusemod/terrain_edit.py),
  not yet checked in-game; painted in the Studio's Maps view): a mod reshapes a map's ground with brush strokes
  (hill, raise, lower, crater, plateau, flatten, smooth, ramp) in `maps/<map>/terrain.toml`; `ruse build` applies
  them to all four files that hold the ground, together, and puts the map in the modded copy
  ([docs/MOD_FORMAT.md §8](docs/MOD_FORMAT.md)). The in-game check comes first:
  `py -3 tools\verify_terrain.py --make-test TwoIslands D:\RUSE-Instances\hill` builds a copy with one hill
  (TwoIslands is Centre of Gravity's pack).
- **Scenery** ([`src/rusemod/scenery.py`](src/rusemod/scenery.py), not yet checked in-game): reads a map's scenery
  file (every building, prop, tree and road piece, each resolved to its scenery type) for the Studio's Maps view, and
  adds the objects a mod lists in `maps/<map>/scenery.toml` ([docs/MOD_FORMAT.md §8](docs/MOD_FORMAT.md)); only
  types the map already uses. The layout follows the notes of DomesticNukes and his Claude (FORMATS.md §6).
  [`tools/verify_scenery.py`](tools/verify_scenery.py) reads every map.
- **Terrain** ([`src/rusemod/tms.py`](src/rusemod/tms.py), [`src/rusemod/tmst.py`](src/rusemod/tmst.py)): read and
  write the terrain mesh (heights, with a height-edit tool) and the texture-tile store. Proven lossless on every map
  by [`tools/verify_tms.py`](tools/verify_tms.py) and [`tools/verify_tmst.py`](tools/verify_tmst.py) (which also build
  the in-game test packs). In the game: our own plain texture tiles are drawn (2026-09-29). The gameplay ground and
  the camera floor (`.kdt`) are read and written by [`src/rusemod/kdt.py`](src/rusemod/kdt.py): every part decodes
  and re-encodes (vertices, normals, index buffers, triangle lists, the tree), lossless on every map by
  [`tools/verify_kdt.py`](tools/verify_kdt.py). The texture tiles' own codec is read by
  [`src/rusemod/tgu1.py`](src/rusemod/tgu1.py); [`src/rusemod/terrain.py`](src/rusemod/terrain.py) gives the Studio
  the map list, the ground mesh and the stitched ground picture.

</details>

<details>
<summary><b>The two apps from source, and the installers</b></summary>

The two apps run on the engine, separate from each other (neither needs the other; PLAN.md decision 22). Both are
desktop windows built like web pages; once: `py -3 -m pip install pywebview`. Their screens also open in a normal
browser with made-up data: `src/ruse_launcher/ui/index.html?fake`, `src/ruse_studio/ui/index.html?fake`.

- **RUSE Launcher** ([`src/ruse_launcher/`](src/ruse_launcher/), released 0.3.0), for players: it finds the game,
  lists your mod sets and has a big Play button that builds the set's modded copy and starts the game (Vanilla
  starts through Steam). `py -3 -m ruse_launcher`. **Players never touch a file.** A
  mod library ("Add a mod file…" for a `.rusemod` from the Studio, a `.rmod` or a `.zip`, or drop a mod file or
  folder on the window; each mod is checked first), mod sets made on screen (new, edit and reorder, rename,
  duplicate, delete), Share and "Import a load order…" for a mod set (RUSE-Mod-Manager's own text, so load orders
  go both ways; [`src/rusemod/loadorder.py`](src/rusemod/loadorder.py)), a three-step guide on Vanilla ("Playing
  with mods, in three steps"), and the launcher in the PC's own language (any of the game's ten). **Supported
  mods** (0.3.0): our list of mods (a GitHub repository, MOD_FORMAT §15) with tick boxes, several installed at once,
  each file checked against the list before it goes into the library, cheat mods kept apart; offline, the last
  copy of the list.
- **RUSE Studio** ([`src/ruse_studio/`](src/ruse_studio/), released 0.8.0), for modders: browse every unit and
  building, see a unit's values, parts and what uses it, and pick a language: the game's own names by default, or
  any of the game's ten languages. Pick or make a mod and change a unit's numbers right on its page: each change is
  saved in the mod's `src/studio.rndf` (with Undo); a part several units share changes for one of them or all.
  "Test in game" builds the mod and starts the game. **Maps** (released in 0.4): every map the game lists, in 3D
  with its real ground mesh and ground textures (decoded once per map and kept). **Also:**
  - **"Export mod…"** turns the mod into one file, `<id>-<version>.rusemod`, with the game build and the mod's
    fingerprint inside, for the launcher's "Add a mod file…" (the loop from modder to player, TASKS C).
  - **New unit…** on a unit's page makes a copy with its own name (one name, shown in all ten languages), price and
    build menu (the same nation and factory, or another nation's); it's listed as new, edited like any other unit,
    and can be deleted.
  - **In Maps:** each map's buildings and a share of its props and trees. Pick a brush and click or drag on the
    ground to shape it: each stroke is drawn at once and saved in the mod's `maps/<map>/terrain.toml`; a ramp takes
    two clicks (its start, its end), Undo takes a stroke back, Start over clears the map. "Place on the map" lists
    the map's own types (most used first, with a search); set Turn and Size, click the ground, and the object is
    saved in the mod's `maps/<map>/scenery.toml`. "Test in game" builds it all into the map.

  `py -3 -m ruse_studio` (after `ruse index build`); `--spike` opens the 3D check.
- `py -3 -m pip install -e .[apps]` once gives two commands, `ruse-launcher` and `ruse-studio`, that open them
  without a console window.
- **Installers** ([`installers/`](installers/README.md)): GitHub builds `RUSE-Launcher-Setup-<version>.exe` and
  `RUSE-Studio-Setup-<version>.exe` on every push that changes the apps (Actions, **apps**, Artifacts). A tag
  `launcher-v<version>` or `studio-v<version>` publishes one as a Release. No Python or Git needed, no admin rights.
  Not signed yet, so Windows warns once ("More info", then "Run anyway").

</details>

</details>

<details>
<summary><b>Tools and checks</b></summary>

- [`ruse_edat.py`](ruse_edat.py): read-only EDAT archive reader.
  ```
  py -3 ruse_edat.py list    <archive.dat>
  py -3 ruse_edat.py stats   <archive.dat> [...]
  py -3 ruse_edat.py extract <archive.dat> <substring> <out_dir>
  ```
- [`listings/`](listings): full file lists of all 38 archives (Steam build 24670294, data revision 190852).
- [`tools/check_public.py`](tools/check_public.py): run by GitHub on every push; fails if private material, game
  files or details of the game's program would reach this public repo.
- [`tools/verify_all.py`](tools/verify_all.py), [`tools/verify_writer.py`](tools/verify_writer.py): read-only checks
  that every archive and data file in the game rebuilds byte-identically, and that a value edit changes only that
  value.
- [`tools/make_test_instance.py`](tools/make_test_instance.py), [`tools/make_c3_instance.py`](tools/make_c3_instance.py):
  build the modded copies for checks C2 and C3 (the Steam install is never changed).
- [`tools/verify_tms.py`](tools/verify_tms.py), [`tools/verify_tmst.py`](tools/verify_tmst.py),
  [`tools/verify_kdt.py`](tools/verify_kdt.py): the terrain files read and written back losslessly, on every map.
- [`tools/verify_terrain.py`](tools/verify_terrain.py): terrain brushes checked on every map in memory;
  `--make-test` builds the in-game hill copy.
- [`tools/verify_scenery.py`](tools/verify_scenery.py): every map's scenery file read.
- [`tools/verify_pyscript.py`](tools/verify_pyscript.py): the new-unit class template against the real game.
- [`tools/rmod_to_mod.py`](tools/rmod_to_mod.py): rebuilds a RUSE-Mod-Manager `.rmod` as a mod of ours.
- [`tools/c3_survey.py`](tools/c3_survey.py): check C3 step 1, a read-only survey of how the game mounts packs.
- [`tools/topo_check.py`](tools/topo_check.py), [`tools/dic_check.py`](tools/dic_check.py): read-only checks of the
  TOPO and text-file leads from [docs/RESEARCH.md](docs/RESEARCH.md) §5.
- [`tools/nation_scan.py`](tools/nation_scan.py): read-only count of everything in the game data built around the
  7 nations (the data side of adding China, [docs/RESEARCH.md](docs/RESEARCH.md) §6).
- [`tools/names_check.py`](tools/names_check.py), [`tools/identity_check.py`](tools/identity_check.py): read-only
  checks before adding units: the object-name writer against every shipped file, and the fresh-identity rules
  (ids, debug names, build menus) against the unit data.
- [`prototypes/spike-2026-09-28/`](prototypes/spike-2026-09-28): throwaway spike code (NDF object parser, script reader).

</details>

<details>
<summary><b>Running the tests</b></summary>

[`tests/`](tests) holds tests on small made-up files; no game needed:

```
py -3 -m unittest discover -s tests
```

(with `PYTHONPATH=src`). GitHub runs them on every push, on Windows and Linux
([`.github/workflows/tests.yml`](.github/workflows/tests.yml)).

</details>

## Credits

- **LittleGroove**: RUSE-Mod-Manager and its `.rmod` format. His engine is in
  [`src/ruse_mod_engine`](src/ruse_mod_engine/), used as it is, and applies `.rmod` mods in our builds.
- **DomesticNukes and his Claude**: the notes on the map ground (`.kdt`) and scenery files that our readers follow.

## License

GNU General Public License, version 3 ([LICENSE](LICENSE), GPL-3.0): copyright (C) 2026 sneadtristen6 and the
RUSE Mod Platform contributors. The apps ship [`src/ruse_mod_engine`](src/ruse_mod_engine/), LittleGroove's
RUSE-Mod-Manager engine (GPLv3), used as it is (see Credits), and its license needs the whole program under
GPL-3.0 (it was MIT until 2026-09-30). `src/ruse_mod_engine/python251` carries
Python's license ([its LICENSE.txt](src/ruse_mod_engine/python251/LICENSE.txt)). This is an independent, fan-made
tool, not affiliated with or endorsed by Eugen Systems. R.U.S.E. and its game data belong to their owners; this
project ships no game files and works only on a copy of a game you own.
