# Research: what already exists and how best to build (2026-09-28)

Three focused web studies: reusable code, beginner-friendly launchers, tech stack. Sources are linked;
uncertain items are marked. Decisions that follow from this are reflected in [PLAN.md](PLAN.md).

## 1. Reusable code: most of the map formats are already reverse-engineered

**LittleGroove/RUSE-Mod-Manager** (GPLv3) already decodes most map formats. Its `source/ruse_mod_engine/` has:

| Module | What it decodes | Our open question it answers |
|---|---|---|
| `terrain_codec.py` | `.tmst_pc` / `.tmst_chunk_pc` terrain **and** the `TGU1` texture mip encoding: a custom JPEG-like codec (YCbCr endpoint planes, 2-bit selectors, Rice/Exp-Golomb coded 4×4 DCT, zlib). `TGU1` flags 256 = terrain, 257 = `.tgv` | FORMATS #5 (TGU1) and #8 (terrain) |
| `scenario.py` | `.scenario` | FORMATS #6 |
| `sdb.py` | map AI layers (forest / movement quadtrees) | FORMATS #6 |
| `kdt.py` | capture-zone meshes (`.kdt`, 10-byte vertex records) | capture-zone rebuild (M6) |
| `terrain_mesh.py`, `terrain_relief.py`, `terrain_tiles.py` | terrain geometry and tiles | M8 |
| `xyz_compile.py` + `python251/` | compiles Python 2.5 by running a **real CPython 2.5.1** in a subprocess (PSF license) | M9 compile route |

Source: https://github.com/LittleGroove/RUSE-Mod-Manager. The terrain codec's comment credits the reverse-engineering
to **ProLution (RUSE Modding Database)** and says the *format knowledge* is CC0. ⚠ Uncertain: not independently confirmed.

**License consequence** (2026-09-28; since 2026-09-30 this project is GPL-3.0 itself, see the reuse rule below):
GPLv3 code can't be copied into an MIT project. We can read it and re-implement from the
format knowledge, or change our license, or ask the authors (see decision below).

**Other sources**
- **kilivan4iK/warno-blender-plugin** (no license → reference only): documents SPK mesh section tables for
  WARNO/Red Dragon/Steel Division and bone/skinning decoding. R.U.S.E.'s `MESHPCPC` v4 isn't covered, but the
  approach transfers. It can't read `TGU1` either. https://github.com/kilivan4iK/warno-blender-plugin
- **kilivan4iK/moddingSuite** (MIT, C#): useful to cross-check NDF decoding. https://github.com/kilivan4iK/moddingSuite
- Text-NDF parsers for WARNO (Ulibos/ndf-parse, WarnoModEditor, warnoMod): low value, since we already solved the binary format.
- No public Wargame terrain/heightmap editor exists.
- **Python 2.5 tooling:** uncompyle6 decompiles 2.5 (GPLv3, fine as an external dev tool); xdis / xasm (GPLv2) are reference only.
  Compiling: bundle real CPython 2.5.1 (PSF), same as LittleGroove.

## 2. Beginner-friendly launchers: what to copy

- **Modpack format → copy Modrinth's `.mrpack` shape:** `files[]` with `path`, `hashes` (sha1/sha512), `downloads[]`
  (HTTPS mirrors), `fileSize`, plus `dependencies` and an `overrides/` folder. Packs reference files instead of
  bundling them, so they stay tiny and work with files hosted anywhere.
  https://support.modrinth.com/en/articles/8802351-modrinth-modpack-format-mrpack
- **Instances:**
  - Prism Launcher gives each modpack its own folder and builds it in a staging folder, so half-built instances never show up.
  - Gale (a Thunderstore manager) shares one copy of each mod across profiles via **hard links**, the same approach C2 proved for us.
  - https://github.com/Kesomannen/gale/wiki/Features
- **First run:** auto-detect the game (Steam's `libraryfolders.vdf`), then one Install button. No manual paths.
- **Joining lobbies:** Forged Alliance Forever auto-downloads the maps and mods a lobby needs.
  https://wiki.faforever.com/en/Play/Client/Map-&-Mod-Vault
- **Hosting, realistic order:**
  1. **Self-host now** (GitHub Releases).
  2. **Thunderstore** once real mods exist. Needs "pre-existing mod developer interest"; request in their Discord; free, MIT-friendly.
     https://wiki.thunderstore.io/ecosystem/adding-a-new-game
  3. **CurseForge** last. Free game onboarding with approval. But its API key may not ship in apps or be cached,
     so a launcher needs its own proxy server (Prism hit this).
     https://docs.curseforge.com/docs/getting-started/setting-up-your-game/ · https://github.com/PrismLauncher/PrismLauncher/issues/263
- **Updates:** keep launcher self-update separate from mod-content updates (hash-diffed manifests).
- **Safety:**
  - Neither Modrinth nor Thunderstore signs or sandboxes mods; both rely on scanning, review and reputation.
    A malicious Modrinth update slipped through in 2024.
  - Our specific risk is script mods (Python bytecode), so any mod containing scripts gets manual review.

## 3. Tech stack

| Area | Recommendation | Why |
|---|---|---|
| UI | **pywebview + TypeScript/three.js** (keeps ADR-2) | one Python process, no Rust glue, WebGL via WebView2 |
| Packaging | **Nuitka** (onefile) | faster start and fewer antivirus false positives than PyInstaller |
| Installer | **Inno Setup** via GitHub Actions | simple, scriptable, well-trodden |
| Updates | **Velopack** (spike first), fallback **tufup** | single self-updating installer; Python path unverified |
| Steam detection | **python-vdf** parsing `libraryfolders.vdf` + `appmanifest_*.acf`, registry fallback | reliable, existing libraries |
| Instances | `os.link` (NTFS, same drive, no admin), full-copy fallback | proven by C2 |
| Signing | defer until public release; then Azure Trusted Signing ($9.99/mo), later free SignPath (needs release history) | signing no longer gives instant SmartScreen trust (2024) |
| CI | GitHub Actions `windows-latest`, tag-triggered releases | standard |

**Top risks:**
1. **WebGL inside the embedded webview** can be unstable, which threatens the 3D viewer. Prototype it early.
2. **Antivirus/SmartScreen trust** builds slowly, even when signed.
3. **Velopack + Nuitka** is unproven together.

Stack sources:
- https://github.com/r0x0r/pywebview
- https://github.com/Nuitka/Nuitka/issues/2757
- https://velopack.io/
- https://www.todesktop.com/blog/posts/windows-apps-psa-ev-certs-do-not-grant-immediate-reputation-anymore

## 4. What this changes (efficiency)

1. **Don't reverse-engineer map formats from scratch.** Before each map reader, read LittleGroove's module as
   reference. This cuts M6/M8 effort sharply and makes terrain painting (TGU1) realistic.
2. **License decision needed before map work** (see PLAN open decisions): ask LittleGroove/ProLution for
   permission to reuse under MIT, or switch our license to GPLv3 to reuse their code directly.
3. **Python 2.5 compile route is solved:** bundle CPython 2.5.1 (a download, so ask first). M9 risk drops.
4. **Lockfile/modpack = `.mrpack` shape.** Don't invent our own.
5. **Spike early, cheaply:** a three.js scene in pywebview, and a Nuitka + Velopack hello-world build.
6. **Signing and CurseForge cost money or setup.** Defer both until there's a public release and real mods.

## 5. Prior art for the next steps (2026-09-28, second pass)

Who already solved pieces of what we build next, what we take from them, and whether their code can be reused.
**Reuse rule:** MIT code can be reused with credit; GPL and CC BY-SA code is read for ideas only, never copied.
**Since 2026-09-30 (GPL-3.0):** MIT, BSD, Apache-2.0 and GPL-3.0 code can be reused with credit, under GPL-3.0;
GPL-2.0-only and anything unlicensed are still read for ideas only.

| Our next step | Who did it | License | What we take |
|---|---|---|---|
| Finding the game | RUSE-Mod-Manager `steam.py`; [python-vdf](https://github.com/ValvePython/vdf) | GPLv3 (ideas); MIT | registry `SteamPath` → `libraryfolders.vdf`, looked for in **both** `config/` and `steamapps/` → `appmanifest_21970.acf`. It also tells the `compat` branch from the current one by build id. python-vdf for the launcher |
| Adding objects (TOPO) | [moddingSuite](https://github.com/enohka/moddingSuite) `NdfbinReader.cs`, `NdfbinWriter.cs` (Wargame; lists R.U.S.E. too) | MIT | TOPO = the file's "top objects": their indices, written sorted by class; every new top-level object is added to it. **Check:** `tools/topo_check.py` |
| Text files (`.dic`) | RUSE-Mod-Manager `dic.py`; moddingSuite `TradManager.cs` (Wargame's `TRAD`) | GPLv3 (ideas); MIT | offsets count from the file start; several entries can share one text; keys sorted; 10 language folders (`us fr ger ita spa pol cz ru jpn sc`, plus `dev`); a new entry can be added without touching the old text block. **Check:** `tools/dic_check.py` |
| Text keys | moddingSuite `Utils.CreateLocalisationHash` | MIT | not a hash: a name of up to 8 characters, 6 bits each (0-9, A-Z, _, a-z). Two R.U.S.E. keys from RUSE-Mod-Manager's notes decode to `M_D_01` and `M_D_30`. Now in `src/rusemod/dic.py` |
| Text form of NDF (`dump`, `.rndf`) | [tree-sitter-ndf](https://github.com/Ulibos/tree-sitter-ndf) + [ndf-parse](https://github.com/Ulibos/ndf-parse) (WARNO); moddingSuite `NdfTextWriter.cs` | MIT | WARNO's spelling: `export X is T ( … )`, `MAP [ … ]`, `RGBA[…]`, `GUID:{…}`, `nil`, `true`/`false`, `$/…` and `~/…` references, `//`, `/* */` and `(* *)` comments. The grammar is a ready reference for ours |
| Mod patch language | KSP [ModuleManager](https://github.com/sarbian/ModuleManager/wiki/Module-Manager-Syntax) | CC BY-SA (ideas only) | almost our operator set: `@` edit, `+` copy, `-` delete, `*=` `+=`, wildcards and `:HAS` filters (our `patch every`). Extra ideas: a FINAL pass, patches that apply only if another mod is present (`:NEEDS`), edit-or-create (`%`) |
| Load order | [Factorio](https://lua-api.factorio.com/latest/auxiliary/data-lifecycle.html) | docs | dependency depth first, then natural name order (like ours); three passes (data, updates, final fixes) so mods can adjust each other without declaring dependencies |
| Multiplayer check | Paradox (HOI4) checksum | docs | a checksum over the game files, shown in-game; mods change it, DLC doesn't. Windows/Linux file-name case differences broke it for cross-platform play; our fingerprint lowercases paths, so it can't |
| Share-a-mod-set codes | r2modman / Thunderstore profile codes | docs | codes are temporary and stored on Thunderstore's server; they carry mods, versions and settings. Ours need no server and don't expire, but carry no settings |

**Changes this suggests** (all four decided 2026-09-28; now in [MOD_FORMAT.md](MOD_FORMAT.md) §5, §6 and §10.6):
1. A `final` pass for balance mods, so they apply after every unit mod without listing them (Factorio, ModuleManager).
2. Patches that apply only when another mod is present, for compatibility patches (ModuleManager `:NEEDS`).
3. Spell values the WARNO way (`RGBA[…]`, `GUID:{…}`, `nil`) so Eugen modders feel at home.
4. New text keys as readable names (`R2U00001`) instead of made-up numbers, and show every key's name in the index.

Sources: the repositories linked above; RUSE-Mod-Manager at https://github.com/LittleGroove/RUSE-Mod-Manager (v1.1.9);
HOI4 checksum threads on the Paradox forums (https://forum.paradoxplaza.com/forum/threads/checksum-multiplayer-problem.1076652/);
r2modman profile codes (https://deepwiki.com/ebkr/r2modmanPlus/6.3-profile-import-and-export).

## 6. Adding a new nation: what other games' modders learned (2026-09-28)

The owner wants a real new nation (China) in RUSE 2.0, not a renamed one (PLAN.md decision 19). **We found no mod that
adds a nation to R.U.S.E.:** the ones on ModDB (Ruse Overhaul and others) rebalance the seven. So the lessons come from
other games whose number of factions was fixed.

| Game | The limit | What modders did | Lesson for us |
|---|---|---|---|
| **Wargame: Red Dragon** (Eugen, the studio's next game after R.U.S.E.) | its nation list | We found no mod that added a nation. The biggest nation mod, *Asia in Conflict*, **replaces** some existing nations with Asian ones. Modders describe Red Dragon's modding as limited by the engine. | The closest game to ours, by the same studio: nations were swapped, not added. Fits FORMATS.md §3 (the nation list is in the program). |
| **C&C: Yuri's Revenge** (*Ares*) | *"You could not add to, remove or reorder the 10 countries or 3 sides"* | Ares, an add-on that loads with the game and never changes the game's file, allows *"up to 16 fully functional countries and sides"*, each with its own flag, UI, score screen and AI settings. | A runtime add-on can lift a hard-coded faction limit; 16 is plenty. But limits hide in many places: *"Certain flags work properly for up to 32 countries, and yet others fail after merely 16"*. Every place that assumes the old number has to be found. |
| **Medieval II: Total War** (*M2TWEOP*, then *M2EX*) | 31 factions | M2TWEOP hooks the game in memory and lifted many limits, but not this one: *"distinct limits that have not been breached due to their complexity, most notably the limit of factions"*. A newer tool, M2EX, removed it almost 20 years after the game came out, with a much bigger rework (64-bit). | The faction count tends to be the hardest limit to move, harder than units or maps. Size it before committing. |
| **Supreme Commander: Forged Alliance** (*Nomads*, a 5th faction) | 4 factions | Played through the FAF community launcher as a "featured mod", which keeps everyone on the same version automatically. | A new faction in multiplayer needs everyone on the exact same version, which is the launcher's job. Ours already does it (fingerprint and join codes, PLAN.md L6). |

**What this tells us for China:**
1. **The data side is the known part**, and our tools can do most of it: an 8th entry wherever the data has a fixed 7
   (every map's `SubClusterNationaliteList`, flag-icon lists, per-nation mesh packs, the
   `BitFieldNationaliteIfNotSkirmish` bit field, all in [FORMATS.md](FORMATS.md) §3). `tools/nation_scan.py` counts
   them, so the data job has a size before anything else.
2. **The program side is the real question.** With the nation list in the program (FORMATS.md §3) and Red Dragon's
   modders swapping nations rather than adding them, R.U.S.E. most likely needs the runtime add-on (PLAN.md ADR 3,
   M10). Ares shows that approach can work.
3. **Find every place that assumes 7 before changing anything** (Ares' lesson), and expect the count itself to be the
   stubborn part (Medieval II's lesson). That's M10 step 2, after the data scan.
4. **Everyone in a match needs the identical add-on and data** (Nomads). The launcher's fingerprint covers the data;
   the add-on gets the same treatment.
5. **The add-on never touches the Steam install** (Ares doesn't change the game's file either; ours sits only in the
   modded copy, ADR 3). Principle 1 holds.

**First step (read-only, data only):** `tools/nation_scan.py` counts, in the shipped data, every structure sized to the
7 nations and every kind of object tagged with a `Nationalite`. It sizes the data work for China.

**Not for us:** the Red Dragon route (swapping a nation out for the new one). The owner keeps all 7 factions
(PLAN.md decision 19), so China is only ever added.

Sources: ModDB R.U.S.E. mods (https://www.moddb.com/games/ruse/mods) and *Ruse Overhaul*
(https://www.moddb.com/mods/ruse-overhaul-mod); *Wargame: Asia in Conflict* (https://www.moddb.com/mods/wargame-asia-in-conflict);
Red Dragon mods on ModDB (https://www.moddb.com/games/wargame-red-dragon1/mods); Ares sides and countries
(https://ares-developers.github.io/Ares-docs/new/sidescountries/index.html) and the Ares page on the C&C wiki
(https://cnc.fandom.com/wiki/Ares); M2TWEOP (https://wiki.twcenter.net/index.php?title=M2TW_Engine_Overhaul_Project,
https://github.com/EOP-Labs/M2TWEOP-library) and M2EX (https://www.moddb.com/news/the-mapsize-region-and-faction-limits-have-been-broken);
FAF Nomads (https://github.com/FAForever/nomads).

