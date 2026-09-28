# R.U.S.E. Mod Platform (working name)

A foundational modding platform and player launcher for R.U.S.E. (Eugen Systems, 2010), built for the long run:
new units, maps, models, missions and one-click modded multiplayer. The content goals on top are RUSE 2.0 and Pacific Island Defense.

Status: **M0 done; M1 next** (the design for M1–M3 is written up). Nothing here modifies the game install.

**Current stage (2026-09-28):** C3 is done (a renamed map pack loads in-game, so new maps can ship their own pack),
and the TOPO and text-file checks passed (adding new objects is unblocked; results in [docs/FORMATS.md](docs/FORMATS.md)).
Next: M1 on the PC (the combined file view and index; scenario / AI-layer / capture-zone readers), and the M1.5
frontier tests.
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
  Value changes work end to end; adding new objects (units) is the next step.

- [`ruse_edat.py`](ruse_edat.py): read-only EDAT archive reader.
  ```
  py -3 ruse_edat.py list    <archive.dat>
  py -3 ruse_edat.py stats   <archive.dat> [...]
  py -3 ruse_edat.py extract <archive.dat> <substring> <out_dir>
  ```
- [`listings/`](listings): full file lists of all 38 archives (build 190852).
- **Mod rules engine** ([`src/rusemod/patch.py`](src/rusemod/patch.py), [`src/rusemod/resolve.py`](src/rusemod/resolve.py)):
  load order and every rule in [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) §10 (stacking, rounding, the conflict table,
  clones, shared parts, `patch every`, the final pass, `when mod`), tested on made-up data. Hooking it to the real
  game files comes in M2.
- **Fingerprints and join codes** ([`src/rusemod/lock.py`](src/rusemod/lock.py)): the multiplayer "seal number" and
  the pasteable join code from [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) §12.
- **Mod file reader** ([`src/rusemod/rndf.py`](src/rusemod/rndf.py)): reads `.rndf` mod text (MOD_FORMAT §5, WARNO
  spellings) into operations for the engine, with errors that give file, line and column.
- [`tools/c3_survey.py`](tools/c3_survey.py): check C3 step 1, a read-only survey of how the game mounts packs.
- [`tools/topo_check.py`](tools/topo_check.py), [`tools/dic_check.py`](tools/dic_check.py): read-only checks of the
  TOPO and text-file leads from [docs/RESEARCH.md](docs/RESEARCH.md) §5.
- [`tests/`](tests): tests on small made-up files, no game needed: `py -3 -m unittest discover -s tests` (with `PYTHONPATH=src`).
  GitHub runs them on every push, on Windows and Linux ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)).
- [`prototypes/spike-2026-09-28/`](prototypes/spike-2026-09-28): throwaway spike code (NDF object parser, script reader, PE analysis).
