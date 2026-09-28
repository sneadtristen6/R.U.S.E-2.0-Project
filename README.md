# R.U.S.E. Mod Platform (working name)

A foundational modding platform and player launcher for R.U.S.E. (Eugen Systems, 2010), built for the long run:
new units, maps, models, missions and one-click modded multiplayer. The content goals on top are RUSE 2.0 and Pacific Island Defense.

Status: **M0 done; M1 next** (the design for M1–M3 is written up). Nothing here modifies the game install.

**Current stage (2026-09-28):** C4 passed: a mod written as text (`examples/half-price-buildings`), built by
`ruse build`, worked in-game. C3 passed too (new maps can ship their own pack). The M1.5 terrain work has started:
the terrain mesh and tile files can be read and rewritten losslessly (`rusemod.tms`, `rusemod.tmst`), and the map
pack "checksum" turned out to be a random ID. Next on the PC: in-game terrain tests (a raised mesa, swapped tiles,
checkerboard tiles), the TGU1 texture codec, and **C5, a new unit in the build menu** (ready to run, PLAN.md §7).
On the cloud side, adding units and naming them are done (C5 and C6 are ready to run); next is the launcher
(PLAN.md §10).
Decided: RUSE 2.0 gets a real 8th nation, China (PLAN.md §6, decision 19); the order is the mod system, then the
launcher; multiplayer is tested solo until there's a second player (decision 20).
The full list is in PLAN.md §10 "Next steps"; the latest decisions are in PLAN.md §6.

| Doc | What it covers |
|---|---|
| [docs/PLAN.md](docs/PLAN.md) | vision, principles, architecture, roadmap, risks, open decisions |
| [docs/FORMATS.md](docs/FORMATS.md) | what we know about every game file format (the project's memory) |
| [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) | draft spec of the mod package format |
| [docs/RESEARCH.md](docs/RESEARCH.md) | what others already built, and the chosen tech stack |
| [docs/LITTLEGROOVE_STUDY.md](docs/LITTLEGROOVE_STUDY.md) | what RUSE-Mod-Manager does, where it stops, and how we go further |
| [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md) | ideas learned from studying the game's own files (esp. its Python scripting layer) |

## Code so far

- **The `ruse` tool** (`src/rusemod/cli.py`): with `PYTHONPATH=src`, run `py -3 -m rusemod <command>`
  (or `pip install -e .` once, then just `ruse <command>`). It never writes into the game folder.
  ```
  ruse detect                                   find R.U.S.E. through Steam, show build and branch
  ruse ls ZZ_GladPatchableWin.dat gfx           list files in a pack (nested packs: ZZ_Win.dat!eugen.ipk)
  ruse names ZZ_GladPatchableWin.dat Sherman    list named objects
  ruse dump ZZ_GladPatchableWin.dat everything.cpp.gladndfbin Tourelle_MG   show data as text
  ruse extract ZZ_GladPatchableWin.dat mapinfo  copy files out, into extracted/ (ignored by git)
  ruse build mymod/ other.rndf --instance D:\RUSE-Instances\test   build mods into a modded copy of the game
  ```
  `build` takes mod folders (`mod.toml` + `src/**/*.rndf`, [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md)) or single
  `.rndf` files, shows the load order and every error / warning / note, and writes nothing if there's an error.
  Value changes work end to end (C4). New objects work too: a copied unit gets its own id, debug name and build-menu
  slot ([`src/rusemod/identity.py`](src/rusemod/identity.py)); the in-game test is C5
  ([`examples/cloned-unit/`](examples/cloned-unit/), PLAN.md §7). New units get their own names from a mod's
  `text/*.csv` ([`src/rusemod/loc.py`](src/rusemod/loc.py); in-game test C6,
  [`examples/named-unit/`](examples/named-unit/)).

- [`ruse_edat.py`](ruse_edat.py): read-only EDAT archive reader.
  ```
  py -3 ruse_edat.py list    <archive.dat>
  py -3 ruse_edat.py stats   <archive.dat> [...]
  py -3 ruse_edat.py extract <archive.dat> <substring> <out_dir>
  ```
- [`listings/`](listings): full file lists of all 38 archives (build 190852).
- **Mod rules engine** ([`src/rusemod/patch.py`](src/rusemod/patch.py), [`src/rusemod/resolve.py`](src/rusemod/resolve.py)):
  load order and every rule in [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) §10 (stacking, rounding, the conflict table,
  clones, shared parts, `patch every`, the final pass, `when mod`), tested on made-up data. It runs on the real game
  files through the bridge ([`src/rusemod/model.py`](src/rusemod/model.py)), which writes changed values, new objects
  and deletes back into them.
- **Fingerprints and join codes** ([`src/rusemod/lock.py`](src/rusemod/lock.py)): the multiplayer "seal number" and
  the pasteable join code from [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) §12.
- **Mod file reader** ([`src/rusemod/rndf.py`](src/rusemod/rndf.py)): reads `.rndf` mod text (MOD_FORMAT §5, WARNO
  spellings) into operations for the engine, with errors that give file, line and column.
- **Terrain** ([`src/rusemod/tms.py`](src/rusemod/tms.py), [`src/rusemod/tmst.py`](src/rusemod/tmst.py)): read and
  write the terrain mesh (heights, with a height-edit tool) and the texture-tile store. Proven lossless on every map
  by [`tools/verify_tms.py`](tools/verify_tms.py) and [`tools/verify_tmst.py`](tools/verify_tmst.py) (which also build
  the in-game test packs). Not yet tried in the game.
- [`tools/c3_survey.py`](tools/c3_survey.py): check C3 step 1, a read-only survey of how the game mounts packs.
- [`tools/topo_check.py`](tools/topo_check.py), [`tools/dic_check.py`](tools/dic_check.py): read-only checks of the
  TOPO and text-file leads from [docs/RESEARCH.md](docs/RESEARCH.md) §5.
- [`tools/nation_scan.py`](tools/nation_scan.py): read-only count of everything in the game data built around the
  7 nations (the data side of adding China, [docs/RESEARCH.md](docs/RESEARCH.md) §6).
- [`tools/names_check.py`](tools/names_check.py), [`tools/identity_check.py`](tools/identity_check.py): read-only
  checks before adding units: the object-name writer against every shipped file, and the fresh-identity rules
  (ids, debug names, build menus) against the unit data.
- [`tests/`](tests): tests on small made-up files, no game needed: `py -3 -m unittest discover -s tests` (with `PYTHONPATH=src`).
  GitHub runs them on every push, on Windows and Linux ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)).
- [`prototypes/spike-2026-09-28/`](prototypes/spike-2026-09-28): throwaway spike code (NDF object parser, script reader, PE analysis).
