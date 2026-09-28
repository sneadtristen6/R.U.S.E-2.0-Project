# R.U.S.E. Mod Platform (working name)

A foundational modding platform and player launcher for R.U.S.E. (Eugen Systems, 2010), built for the long run:
new units, maps, models, missions and one-click modded multiplayer. The content goals on top are RUSE 2.0 and Pacific Island Defense.

Status: **planning / M0**. Nothing here modifies the game install.

| Doc | What it covers |
|---|---|
| [docs/PLAN.md](docs/PLAN.md) | vision, principles, architecture, roadmap, risks, open decisions |
| [docs/FORMATS.md](docs/FORMATS.md) | what we know about every game file format (the project's memory) |
| [docs/MOD_FORMAT.md](docs/MOD_FORMAT.md) | draft spec of the mod package format |
| [docs/RESEARCH.md](docs/RESEARCH.md) | what others already built, and the chosen tech stack |
| [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md) | ideas learned from studying the game's own files (esp. its Python scripting layer) |

## Code so far

- [`ruse_edat.py`](ruse_edat.py): read-only EDAT archive reader.
  ```
  py -3 ruse_edat.py list    <archive.dat>
  py -3 ruse_edat.py stats   <archive.dat> [...]
  py -3 ruse_edat.py extract <archive.dat> <substring> <out_dir>
  ```
- [`listings/`](listings): full file lists of all 38 archives (build 190852).
- [`prototypes/spike-2026-09-28/`](prototypes/spike-2026-09-28): throwaway spike code (NDF object parser, script reader, PE analysis).
