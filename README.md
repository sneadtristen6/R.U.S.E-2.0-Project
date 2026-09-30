<div align="center">

# R.U.S.E. 2.0

**A mod launcher and a mod editor for R.U.S.E. (Eugen Systems, 2010).**

[![Launcher release](https://img.shields.io/github/v/release/sneadtristen6/Ruse-Mod-Platform?filter=launcher-v*&label=launcher)](https://github.com/sneadtristen6/Ruse-Mod-Platform/releases?q=launcher)
[![Studio release](https://img.shields.io/github/v/release/sneadtristen6/Ruse-Mod-Platform?filter=studio-v*&include_prereleases&label=studio)](https://github.com/sneadtristen6/Ruse-Mod-Platform/releases?q=studio)
[![tests](https://github.com/sneadtristen6/Ruse-Mod-Platform/actions/workflows/tests.yml/badge.svg)](https://github.com/sneadtristen6/Ruse-Mod-Platform/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[![Download RUSE Launcher](https://img.shields.io/badge/Download-RUSE%20Launcher-b8913a?style=for-the-badge)](https://github.com/sneadtristen6/Ruse-Mod-Platform/releases?q=launcher)
&nbsp;&nbsp;
[![Download RUSE Studio](https://img.shields.io/badge/Download-RUSE%20Studio-b8913a?style=for-the-badge)](https://github.com/sneadtristen6/Ruse-Mod-Platform/releases?q=studio)

**Launcher** for players (latest: 0.2.6) &middot; **Studio** for modders, a preview (latest: 0.6.4) &middot; Windows &middot; needs R.U.S.E. on Steam

</div>

<p align="center">
  <img src="docs/images/studio-maps.jpg" alt="RUSE Studio's Maps view: Leipzig in 3D, with its rivers, lakes and real ground" width="800">
  <br>
  <sub>RUSE Studio's Maps view: every map the game ships, in 3D, with its real ground and water. Here, Leipzig.</sub>
</p>

A modding platform for R.U.S.E. Its aim, step by step: new units, maps, models, missions and one-click modded
multiplayer (today: units, and the first map tools). The content goals on top are RUSE 2.0 and Pacific Island
Defense.

**Your Steam install is never changed.** Mods are built into a separate modded copy of the game (hard links to the
game's packs, plus the packs a mod rebuilds), and Play starts that copy.

## What you can do

**Players, with RUSE Launcher**

- Pick a mod set and press **Play**: the launcher builds a modded copy of the game and starts it.
- Add a mod file (a `.rusemod` from the Studio, a community `.rmod` used as it is, or a `.zip`), or drop it on the
  window.
- Make and reorder mod sets in the window.
- Share a mod set's load order with a friend, or import one. It's the same text RUSE-Mod-Manager copies and reads,
  so load orders go both ways.
- Browse the community's mods and install them. *Coming* (the list isn't published yet).
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
- See each map's scenarios: zones, starting points, spawns and town names; mods can move starting points.
- Place buildings, props and trees, and export a mod as one file.
- The Studio offers its own new versions.

*Coming* means merged and in the test builds, not in a release yet.

Modders who write mods by hand can also use the `ruse` command-line tool, from the source (see
[For contributors](#for-contributors) below).

<table>
  <tr>
    <td width="50%" valign="top">
      <img src="docs/images/launcher.jpg" alt="RUSE Launcher: mod sets on the left, Play on the right" width="380"><br>
      <sub>RUSE Launcher: a set of 75 mods, and why they can't be played together.</sub>
    </td>
    <td width="50%" valign="top">
      <img src="docs/images/studio-unit.jpg" alt="RUSE Studio: a unit's values, ready to edit" width="380"><br>
      <sub>RUSE Studio: a unit's values, flags and price, ready to edit.</sub>
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center" valign="top">
      <img src="docs/images/studio-units.jpg" alt="RUSE Studio: the unit list, with filters by type and nation" width="380"><br>
      <sub>RUSE Studio: the unit list, with filters by type and nation.</sub>
    </td>
  </tr>
</table>

### Terrain editing, in the game

<table>
  <tr>
    <td width="50%" valign="top">
      <img src="docs/images/terrain-ingame-hill.jpg" alt="R.U.S.E. in game on Blitz: a hill raised with the Studio's brushes, units driving up it" width="380"><br>
      <sub>Blitz, in the game: a hill raised with the Studio's brushes. Units drive up it and take orders on it, and
      the player's HQ starts at a place the mod moved it to.</sub>
    </td>
    <td width="50%" valign="top">
      <img src="docs/images/terrain-ingame-units.jpg" alt="R.U.S.E. in game: units on top of the raised hill, the town of Cahir lifted with it" width="380"><br>
      <sub>On top of the hill: the town of Cahir and its trees rise with the ground (2026-09-30). The recipe is
      DomesticNukes and his Claude's.</sub>
    </td>
  </tr>
</table>

## Install in three steps

1. **Download** the installer from [Releases](https://github.com/sneadtristen6/Ruse-Mod-Platform/releases):
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

## Status

Early, and moving fast. **Proven in the game:** value and text mods, new names in all ten languages, new units that
are built and fight, maps with their own pack, terrain texture tiles we write ourselves, and a first `.rmod` check
(Dev Toolkit and 10x Artillery Price in one modded copy). **Not yet checked in the game:** a new unit made in the
Studio's window, mod sets made in the launcher's window, a mod exported as one file, the launcher's mod library and
sharing a load order, terrain brushes, placing scenery, Browse mods, and the apps updating themselves. The tests,
step by step for anyone with the game: [docs/TESTS.md](docs/TESTS.md).

<details>
<summary><b>Current stage (2026-09-29)</b></summary>

- **Scenery** (merged, not yet checked in-game): mods can add buildings, props and trees to a map
  (`maps/<map>/scenery.toml`, MOD_FORMAT §8). The Studio's Maps view shows each map's buildings and a share of its
  props and trees, and its Place tool adds more. The scenery file's layout follows the notes of DomesticNukes and his
  Claude.
- **Terrain brushes** (merged, not yet checked in-game): mods can reshape a map's ground, and the Studio's Maps view
  paints the strokes (hill, raise, lower, crater, plateau, flatten, smooth, and a two-click ramp; size, strength,
  Undo, Start over). The first in-game check is one hill on Centre of Gravity; it waits for DomesticNukes' review of
  the ground files (PLAN.md §10).
- **The ground files:** the map's gameplay ground (`.kdt`) now decodes and re-encodes in every part, lossless on all
  64 shipped files (`src/rusemod/kdt.py`, checked by `tools/verify_kdt.py`), from the notes of DomesticNukes and
  his Claude.
- **Community mods:** `.rmod` files (RUSE-Mod-Manager, by LittleGroove) work as they are: the build applies them with
  LittleGroove's own engine (PLAN.md decision 26). All 75 on hand apply with 0 errors (a read-only check), and a
  modded copy with Dev Toolkit and 10x Artillery Price passed in-game. Their format is written down in MOD_FORMAT
  §13, and what they teach about the game's data is in FORMATS.md §2. The community mods we rebuilt in our own
  format (`tools/rmod_to_mod.py`) are kept in the private shared repo until their authors agree.
- **Sharing a load order** (Launcher 0.2.0, not yet checked in-game): the launcher gives a mod set's load order as text to
  paste to a friend, and "Import a load order…" makes a set from one. It's RUSE-Mod-Manager's own block, so load
  orders go both ways between the two apps.
- **Browse mods** (merged, not yet checked in-game): the launcher lists the community's mods from a GitHub index and
  installs them. It goes live when the index's repository exists.
- **A mod as one file** (merged, not yet checked in-game): the Studio exports `<id>-<version>.rusemod`, the launcher
  installs it.
- **New units work in-game:** a copy of the M3 Lee named "Lee C6-Test", costing $1, in the US armour factory; it's
  built and fights like any other unit (C7). `ruse build` gives every copied unit the class the game's Python unit
  list needs, under the safety rules of PLAN.md decision 23 (our own mod format never carries scripts; a community
  `.rmod` may replace the game's own scripts, with a warning in the build report, decision 26).
- **Text mods work end to end** (check C4), with new names in all ten languages (C6). The launcher's Play builds the
  modded copy and starts it.
- **Maps:** new maps can ship their own pack (C3). The terrain mesh and tile files can be read and rewritten
  losslessly, and the game draws terrain textures we write ourselves.
- **The apps update themselves** (Launcher 0.2.0 and Studio 0.5.0 on, not yet checked in-game): on start they look for a newer release on
  GitHub, and Update downloads it, checks its SHA-256 and installs it; the app starts again by itself.
- **Next:** the in-game tests in [docs/TESTS.md](docs/TESTS.md) (scenery, water, community mods, the hill, a new
  unit from the Studio, the launcher), then the releases that ship them.
- Decided: RUSE 2.0 gets a real 8th nation, China (PLAN.md §6, decision 19).

The order is in [PLAN.md §10 "Now"](docs/PLAN.md#10-now); the latest decisions are in PLAN.md §6.

</details>

## Docs

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

## For contributors

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

- **RUSE Launcher** ([`src/ruse_launcher/`](src/ruse_launcher/), released 0.1.0), for players: it finds the game,
  lists your mod sets and has a big Play button that builds the set's modded copy and starts the game (Vanilla
  starts through Steam). `py -3 -m ruse_launcher`. **Merged, not released yet: players never touch a file.** A
  mod library ("Add a mod file…" for a `.rusemod` from the Studio, a `.rmod` or a `.zip`, or drop a mod file or
  folder on the window; each mod is checked first), mod sets made on screen (new, edit and reorder, rename,
  duplicate, delete), Share and "Import a load order…" for a mod set (RUSE-Mod-Manager's own text, so load orders
  go both ways; [`src/rusemod/loadorder.py`](src/rusemod/loadorder.py)), a three-step guide on Vanilla ("Playing
  with mods, in three steps"), and the launcher in the PC's own language (any of the game's ten). **Also merged:
  "Browse mods"**, a list of the community's mods from a GitHub repository (MOD_FORMAT §15), with Install: the file
  is checked against the list before it goes into the library; offline, the last copy of the list.
- **RUSE Studio** ([`src/ruse_studio/`](src/ruse_studio/), released 0.6.4), for modders: browse every unit and
  building, see a unit's values, parts and what uses it, and pick a language: the game's own names by default, or
  any of the game's ten languages. Pick or make a mod and change a unit's numbers right on its page: each change is
  saved in the mod's `src/studio.rndf` (with Undo); a part several units share changes for one of them or all.
  "Test in game" builds the mod and starts the game. **Maps** (released in 0.4): every map the game lists, in 3D
  with its real ground mesh and ground textures (decoded once per map and kept). **Merged, not released yet:**
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

MIT for this project's own code ([LICENSE](LICENSE)). [`src/ruse_mod_engine`](src/ruse_mod_engine/) is
LittleGroove's RUSE-Mod-Manager engine, used as it is (see Credits); `src/ruse_mod_engine/python251` carries
Python's license ([its LICENSE.txt](src/ruse_mod_engine/python251/LICENSE.txt)). This is an independent, fan-made
tool, not affiliated with or endorsed by Eugen Systems. R.U.S.E. and its game data belong to their owners; this
project ships no game files and works only on a copy of a game you own.
