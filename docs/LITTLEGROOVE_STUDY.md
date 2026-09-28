# Study: LittleGroove/RUSE-Mod-Manager, and how we go further

Read-only study of https://github.com/LittleGroove/RUSE-Mod-Manager (GPLv3), 2026-09-28. **We never copy its
code.** This records *what* it does and *where it stops*, so our own (MIT) versions can be better and do more.
File paths refer to their repo.

## What it is

- A Tk desktop app for one job: patch an existing R.U.S.E. install with `.rmod` mods.
- Format/engine code lives in `source/ruse_mod_engine/` (49 files); the rest are ~20 editor tabs that mix UI with logic.
- No tests and no CI anywhere.
- Single maintainer, reactive release cadence. Public history was "reset for Eugen Systems compliance" at v1.0.160.
  ⚠ Worth finding out what Eugen asked for before our public release.

## By area: what it does, where it stops

### Maps and terrain

| Piece | Reads | Writes | Notes |
|---|---|---|---|
| Terrain texture tiles (`terrain_codec.py`, `TGU1`) | ✅ production grade | ⚠ stub: its own docs say "NOT game-valid", not wired in | custom DCT + Rice/Exp-Golomb + zlib codec; also used by `.tgv` |
| Terrain mesh / heights (`terrain_mesh.py`, `.tms`) | ✅ | ❌ none | quantized XY + elevation, custom LZ + delta prediction; one vertex field still unknown |
| Relief shading (`terrain_relief.py`) | display only | — | hill-shading from mesh normals |
| Scenario (`scenario.py`) | ✅ | ✅ (recomputes MD5) | zones addressed by bare integer index |
| AI layers (`sdb.py`) | ✅ | ✅ byte-identical edit-in-place | forest/concealment + blocked quadtrees |
| Capture zones (`kdt.py`, most advanced file) | ✅ | ✅ small reshapes | has a from-scratch KD-tree builder; the docs saying reshaping is impossible are out of date |
| Map editor GUI | — | — | only opens existing maps; "new scenario" = clone. No new-map or heightmap tools |

### Data and mods

- **NDF identity, three tiers:** stable key (e.g. `ClassNameForDebug`) → anchor (named ancestor + property path) →
  instance index as a last resort. Same philosophy as our export-path addressing. Their converter and migrator
  duplicate this matching logic.
- **Mods (`.rmod`):** match objects by property values, then create/patch/delete. Applied from a pristine backup into
  the live install. Heavy per-build special cases (e.g. a hard-coded "17 instances removed" fix).
  The conflict check admits it can't see a delete-vs-patch clash.
- **New units (`clone.py`):**
  - clones only 4 hard-coded classes
  - mints a new name, id and text hash, and finds a free build-menu slot
  - **keeps the source's 3D model and textures**
  - leaves cross-references (upgrade chains) to the user
- **Scripts:**
  - small edits re-marshal byte-identically
  - new code compiles through a bundled real Python 2.5.1
  - decompiling uses uncompyle6/xdis
- **Text:** `.dic` editing plus "where is this text used" tracing across NDF and scripts.
- **Multiplayer:** "SAFE" mods are baked into the app, so everyone's files match. New pairings need an app update; there are no join codes.
- **Self-update:** downloads the new exe from GitHub Releases and swaps it in, with no hash or signature check.

### Assets

- **Textures:** `.tgv` is decode-only (DXT); no encoder.
- **3D models (`.spk`), animations, sound, UI:** nothing.

## Gap map: our goals vs what exists

| Our goal | They cover | What we build |
|---|---|---|
| New units with **own visuals** | partial (clone keeps source visuals, 4 classes) | clone any class, re-point model/texture/icon, wire every cross-reference (menus, upgrades, AI lists) |
| **New maps / terrain** | none (decode only) | game-valid `TGU1` encoder, `.tms` mesh writer, heightmap import/export, new-map registration |
| Capture zones for new maps | partial (edits; builder needs a template map) | a stand-alone zone compiler from our own map sources |
| **3D models (Blender)** | none | SPK reader/writer + Blender bridge (nobody has this for R.U.S.E.) |
| Textures | decode only | encoder (DXT + `TGU1`) |
| New game modes / scripts | partial (compile route exists) | a Studio script workflow on the same idea: real Python 2.5 for compiling |
| New nations | none | still exe-bound (parked) |
| Launcher, modpacks, instances | none (patches the live install) | our instance + `.mrpack`-style launcher (proven by C2) |
| Multiplayer sync | via app updates | join codes + fingerprints |
| Survive game updates | good concept (tiered identity + index maps) | same concept as a documented public API, one tested implementation |
| Tests / CI | none | byte-identical round-trip gates (done: `tools/verify_all.py`) |

## More uses from the same knowledge

- **Terrain decode + hill-shading:** heightmap export, a terrain painter, and minimap thumbnails for the launcher's map browser.
- **Quadtree layer codec:** any paintable gameplay mask, not just forest and blocked.
- **KD-tree builder:** a compile step for capture zones in brand-new maps.
- **Free build-menu slot logic:** a visual roster / tech-tree editor in Studio.
- **Text where-used tracing:** a full translation manager (find orphans, missing languages).
- **Their conflict keys:** a pre-join collision check for multiplayer sync.
- **Lazy tile cache pattern:** a smooth Studio map viewport.

## How our versions will be better

1. **Every codec is a read/write pair** with byte-identical round-trip tests in CI. They have none; we already gate the whole game.
2. **Headless core, UI on top.** No logic in the GUI, so the command line, launcher, Studio and AI all use the same code.
3. **One schema drives validation and the editors.** Their list-property bug (issue #17) can't happen by construction.
4. **Stable, named IDs everywhere,** including zones and scenario objects, instead of bare indices.
5. **Creation for any class,** with a guided "wire it into the game" step.
6. **Never touch the install** (instances), and verify every download by hash.
7. **Our frontier, where nobody has gone:** game-valid terrain writing, new maps from scratch, 3D models, texture encoding.
