# R.U.S.E. Mod Platform: Master Plan

Status: draft v0.1, 2026-09-28. Working name: TBD (see [Open decisions](#9-open-decisions)).
Companion docs: [FORMATS.md](FORMATS.md) (everything we know about the game's files) and
[MOD_FORMAT.md](MOD_FORMAT.md) (draft mod package spec).

---

## 1. Vision

A foundational, long-lived platform that makes R.U.S.E. fully moddable, the way an engine SDK makes a
game moddable, plus a player launcher that makes modded play (including multiplayer) one click.
Content is built on top of it: **RUSE 2.0** (balance, units, tactics, nation rosters) and later
**Pacific Island Defense**.

**Goals**
- Modders can change or add anything the game's data allows: units, weapons, rosters, maps, textures,
  models and scripts. Sound comes last.
- Players never copy files by hand: pick mods or paste a join code, press Play.
- It survives game updates and years of maintenance by a small team (you + AI), and stays open to contributors.
- It runs on the existing Steam multiplayer. No game servers of our own.

**North star: the player experience (like Minecraft + CurseForge)**
1. Download one installer and run it. It finds R.U.S.E. on its own.
2. Browse mods in the launcher: screenshots, descriptions, ratings.
3. Click **Install**; required mods come along automatically.
4. Click **Play**.
- Modpacks (e.g. RUSE 2.0) install in one click and get their own instance, the way CurseForge does it.
- Joining a friend's modded game = clicking the Steam invite; the launcher fetches what's missing.
- A player **never** unzips files, copies anything into game folders, edits configs, or has to "verify game files".
- There's always a one-click way back to vanilla.

What that requires: the launcher ships as a single installer (no Python or Git needed); it auto-detects the Steam
library; installs, dependencies and updates are automatic; errors are in plain language. Longer term, publish on
CurseForge itself if they add R.U.S.E.

**Non-goals (for now)**
- A standalone game. Eugen's assets can't leave R.U.S.E. without their permission.
- Redistributing Eugen's files, cheats, piracy, or bypassing ownership checks.
- Replacing Steam lobbies or matchmaking.

## 2. Principles

These rules decide every design question.

1. **Never modify the Steam install.** Modded play runs from a *modded instance*: a folder of hard links
   to the original files plus our rebuilt packs (confirmed by check C2 on 2026-09-28).
2. **Lossless first.** A format is only written after it round-trips byte-identically on every shipped file.
3. **Mods are changes to named things**, never byte offsets or list positions, so they combine and survive updates.
4. **Deterministic builds.** Same game version + same mods = same result on every PC. Lockstep multiplayer depends on it.
5. **Gameplay vs cosmetic** is tracked for every change. Only gameplay content has to match in multiplayer.
6. **Headless first.** Everything works from the CLI and Python API; the GUIs sit on top. That's what lets AI build, test and maintain it.
7. **The repo is the memory.** Format knowledge, decisions (ADRs) and tests live in the repo, and every session starts from them.
8. **Version-aware by default.** Everything records the game build it came from. An update triggers a rebase, not breakage.
9. **Plugins everywhere.** Formats, importers, editors and validators register through one plugin API, and first-party features use it too.
10. **Respect ownership.** A legitimate Steam copy is required. Mods ship as changes, not copies of the game.
11. **Study the game freely, commit nothing of it.** We read Eugen's files (data and scripts) to learn from them
    (see [ENGINE_NOTES.md](ENGINE_NOTES.md)); no game file is ever stored in the repo (`.gitignore` enforces this).
12. **Tool before content.** Build the platform first; unit stats, balance and rosters wait until it's usable.
13. **New players first.** If a step can be automated, a player never sees it. Judge every launcher feature by
    the north star above: download, install, play.

## 3. What we know (evidence as of 2026-09-28)

Details and byte layouts are in [FORMATS.md](FORMATS.md).

| Area | Finding | Confidence | Consequence |
|---|---|---|---|
| Archives | EDAT v1 = header + path trie + raw data; no encryption, no container compression | verified | reader done, writer next |
| Unit data | NDF binaries (EUG0/CNDF, zlib). All 1,982 NDF files parse completely; 24-type value table verified; unit DB has 63,686 objects | verified | any gameplay value is editable |
| Writer gap | `TOPO` table (an object ordering present in 164 files) not decoded | open | must be solved before adding objects |
| Maps | 86 map entries in `mapinfo.cpp` NDF; map packs are mounted by NDF data (`TClusterMountMapDataPack`); RUSE.exe contains no map names | verified / medium | new maps look data-only |
| Map packs | 16-byte header checksum of Maps\PC packs unknown; `save.boobspc` and `output.sdb` carry plain MD5s | open / verified | could block edited map packs, so test early |
| Nations | 7 nations hard-coded in RUSE.exe (US, GER, UK, FR, ITA, USSR, JAP) and 7-slot data structures | medium | rosters are data-only; an 8th nation needs exe work; Pacific (US vs JAP) needs none |
| Scripts | `.xyz` = zlib-compressed Python 2.5 code objects; script packs are registered by NDF | verified | new missions/modes possible; needs a Python 2.5 compiler |
| RUSE.exe | x64, no DRM or packer, no ASLR, imports `version.dll` / `winmm.dll` | verified | an optional runtime extender (proxy DLL) is feasible |
| Multiplayer | Steam lobbies, lockstep with a desync checker, supports `connect_lobby` launches | verified (strings) | launcher can sync mods, then join a lobby |
| Updates | RUSE.exe built 2026-08-11; RUSE-Mod-Manager tracks 7 game builds since May | verified | design for updates anyway |
| Sound | `.ess` = Eugen's own variable-bitrate codec, no public decoder | verified | last priority |

## 4. What modders do today, and what that requires

Survey of 5 Nexus mods, 18 ModDB mods and the 41 mods bundled with RUSE-Mod-Manager:
- almost every mod edits the unit database (prices, HP, morale, speed, range, build times, menus)
- "new units" are existing units repurposed (Zombie Mode, goat-model aircraft, unlocked V2s)
- missions and game modes ship as whole replaced scenario files
- nobody has made new terrain, models or nations
- mods ship as whole `.dat` files for one game build, so they can't be combined and break on updates

Requirements derived from that:

| # | Requirement |
|---|---|
| R1 | Real new units: clone, own visuals, icons, names, build menus, AI usage |
| R2 | Combine many mods, with conflict reports |
| R3 | Survive game updates (rebase) |
| R4 | Import existing `.rmod` mods |
| R5 | Scenario editing piece by piece for mission makers |
| R6 | New maps (clone first, terrain later) |
| R7 | One-click modded multiplayer |

## 5. Architecture

```
        Players                                  Modders
           |                                        |
   +-------v-------+   +---------+   +--------------v--+   +----------------+
   |   Launcher    |   |   CLI   |   |     Studio      |   | Blender bridge |
   +-------+-------+   +----+----+   +--------+--------+   +--------+-------+
           +----------------+--------+--------+---------------------+
                         Local service  /  Python API
  +-----------------------------------------------------------------------------+
  | L4 Deploy & run   instances (hard links) - launch/join - runtime extender   |
  | L3 Mod system     packages - patch IR - resolver - builder - cache -        |
  |                   validator - fingerprint - rebase                          |
  | L2 Game model     build detection - VFS - asset registry - object graph -   |
  |                   schema DB                                                 |
  | L1 Formats        edat - ndf - dic - scenario - mapinfo - tgv - spk - xyz   |
  | L0 Knowledge      format docs - ADRs - test corpus manifests                |
  +-----------------------------------------------------------------------------+
  L6 Distribution     mod index (git) - mirrors (GitHub/Nexus/ModDB/...) - join codes
```

**Two separate apps on one engine (decision 22, the owner, 2026-09-29).** **RUSE Launcher** is the players' app: it
finds the game, loads mods and starts the game (`src/ruse_launcher/`). **RUSE Studio** is the modders' app: the unit
editor now, the map, model and scenario tools later (`src/ruse_studio/`). Both are built on the same engine, `rusemod`
(L1–L4, plus the `ruse` command), and neither needs the other: a test fails if one ever imports the other. They share
the platform folder (`%LOCALAPPDATA%\RUSE Mod Platform`): the game folder picked by hand, the game index, and `mods\`,
where the Studio saves the mods it makes. Each gets its own installer; a player never needs the Studio.

### L1 Formats
- Each format is one plugin module: `parse(bytes) -> model`, `write(model) -> bytes`, a status
  (unknown / read / write / round-trip) and golden tests.
- Big packs are accessed lazily and streamed (ZZ_Win.dat is 2.4 GB).
- Unknown bytes are kept raw so round trips stay exact. For example, some NDF bools store `0x4E` instead of 0/1.

### L2 Game model

Built from the install once per game build (read-only), then cached. Everything above it (the mod builder, launcher,
Studio, CLI) asks the game model instead of opening packs itself. This is the next thing to build (M1); it's written
out here so it can be built straight from this section.

**Built (cloud session, 2026-09-28): the index**, `src/rusemod/index.py` and `ruse index`: every table below except
`script`, the stable addresses (with class selectors), owners, imports resolved across files, and the questions
(`find`, `show`, `where`, `filter`, `texts`, `clone`, `report`). Debug-info copies are indexed but left out of answers.
Not yet: the `script` table, the quick start-up check of the packs, the schema annotation files, and the comparison
with `listings/`. The PC runs it on the real game (§10 item 1.8).

**Build detection**
- The **build key** is the Steam build id (`buildid` in `steamapps/appmanifest_21970.acf`) plus the data revision (the
  folder under `Data\PC`, e.g. `190852`).
- Every start runs a quick check (pack sizes and dates). Full pack hashes are computed once per build and cached. If
  they don't match the known values for that build, something changed the install (a tool that patches the live game,
  for example), and the launcher offers Steam's repair (L5).
- A new build key means a new game model. The old one is kept, because rebasing mods needs both
  ([MOD_FORMAT.md](MOD_FORMAT.md) §11).

**One combined file view (VFS)**

The game sees one tree of files assembled from many packs. We rebuild that tree the same way.

| Layer | Packs | Mounted |
|---|---|---|
| core | the six packs in `Data\PC\<rev>\`, names hard-coded in RUSE.exe | always |
| map | the 32 packs `Maps\PC\DataMap<Name>_v09.dat` | only while that map is loaded: its `clustermap.cpp` mounts `MapDat:\DataMap<Name>_v09.dat` at `Datasmap` |
| nested | the 217 packs inside other packs (`.ipk .apk .mpk .gpk`, some `.ppk`) | by whatever refers to them, e.g. `TResourceDescriptorPythonPack 'Eugen.ipk'` |

- Every file has two addresses:
  - **location**, where its bytes are: `pack!path`, with another `!path` inside a nested pack, e.g.
    `ZZ_Win.dat!genpython\eugen.ipk!…`
  - **game path**, what the engine asks for: lowercase with `/`, plus the mount point for map files. The original
    spelling is kept for display.
- **No clashes to resolve so far** (checked against `listings/`): no path appears in two core packs. 56 paths repeat
  across map packs (every map has its own `output\div_map.tgv_pc`, for example), which is fine because only one map is
  mounted at a time. The one open case is `mapinfo.cpp`, which exists in both `genglad\patchable` and
  `genglad\nonpatchable` (identical today). Which copy the game reads matters once we add maps; one in-game test (M6)
  settles it.

**The index** (SQLite, one file per build, in the tool's cache folder; it replaces the "asset registry" of earlier drafts)

| Table | One row per | Main columns |
|---|---|---|
| `pack` | archive, nested ones included | name, location, size, SHA-256, layer, parent pack |
| `file` | file in any pack | location, game path, size, SHA-1, type (read from its first bytes), map name for map files |
| `ndf` | NDF file | file; object, class, property and string counts; has TOPO; SHA-1 of the uncompressed bytes |
| `object` | NDF object | file, index, class, export path (if named), stable address (below), shared flag |
| `owner` | pair of (unnamed object, named owner) | which named objects reach it; more than one row means shared |
| `ref` | reference | from object + property path → an object, an import path, a file path or a text hash |
| `import` | IMPR entry | file, path, and the object it resolves to in another file (if found) |
| `prop_seen` | class + property + type | how often it appears, min and max for numbers, an example (feeds the schema DB); a list's items as `Prop[]` |
| `text` | `.dic` entry | file, language, hash, the text itself |
| `script` | `.xyz` module | file, module name, source MD5 |

It has to answer these in well under a second:
- where is this object used, and what does this unit use
- which units have a property above or below some value
- which files mention a path
- what cloning an object would copy and what it would share ([MOD_FORMAT.md](MOD_FORMAT.md) §10.5)
- where each text is used, and which texts nothing uses

Size guess: about 2,200 NDF files, and `everything.cpp` alone has 63,686 objects, so a few hundred thousand objects and
around a million references: tens of MB. It should build in about a minute (the whole-game verify reads everything in 24 s).

**A stable name for every object**

Mods, the index and the editors all use one address per object, in this order of preference:
1. **Export path** for named objects: `$/GFX/Everything/Descriptor_Unit_Tourelle_MG_US`.
2. **Owner path** for unnamed sub-objects: the nearest named owner, then property names and list positions,
   `…Descriptor_Unit_X:WeaponManager.Turrets[0]`. If there are several paths, the shortest wins, then the one that
   comes first in the file.
3. **Selector** instead of a list position when it picks out exactly one item: `Turrets[class=TTurretTwoAxisDescriptor]`.
   It survives game updates that reorder lists. The index works out the best selector for every list item.
4. **Last resort:** `<game path of the file>#<object index>` for objects no named object reaches. Marked unstable; the
   index counts them, so we learn how common they are.

Shared objects are addressed through the owner whose export path sorts first, and flagged with the full owner list.
It's the same idea as RUSE-Mod-Manager's three tiers ([LITTLEGROOVE_STUDY.md](LITTLEGROOVE_STUDY.md)), built once
and tested.

**Schema DB:** the types observed for each class/property across all NDF files (the `prop_seen` table), plus community
annotation files. **Started (2026-09-28): `src/rusemod/labels.toml`**, display names in the game's ten languages for
41 properties, their groups, the nations and the Studio's own words; the game's names stay the default (decision 21):
- English names for the French properties (`Puissance` → Power, `PorteeMaximale` → MaxRange)
- units, ranges, enum labels (nations 0–6) and editor hints

```toml
# schema/annotations/units.toml
[TUniteAuSolDescriptor.VitesseLineaire]
name  = "Speed"
group = "Movement"
```

The schema DB drives the editors and validation.

**Done when (M1):**
- the index builds for build 190852 in about a minute or less
- every file in the 38 packs and 217 nested packs is in it, and the counts match `listings/`
- every NDF object is in it and every local reference resolves; the share of imports that resolve is reported
- a report lists repeated paths, shared objects and last-resort addresses
- the CLI can list files, dump any object by its address, and show where it's used

**Decided (2026-09-28):** the index keeps all game text (unit names and descriptions, in every language), so you can
search by name and see where each text is used. It costs some disk space (a guess: tens of MB).

### L3 Mod system
- **Package** ([MOD_FORMAT.md](MOD_FORMAT.md)): a manifest plus readable sources: NDF-style text patches, CSV text,
  PNG/glTF assets, map folders and scripts.
- **Patch IR:** every editor, text file, CSV and script produces the same operations, each tagged with its source (mod, file, line):
  - set, multiply, add
  - list insert/remove
  - create, clone, delete
  - add/replace file
- **Resolver:** dependencies with version ranges, optional dependencies, load-after and topological sort.
  On a conflict the last mod wins and a warning is shown; an explicit `override` silences it.
  The exact rules for every operation and every conflict are in [MOD_FORMAT.md](MOD_FORMAT.md) §10.
- **Builder:** resolve → load base (per build) → apply IR in order → validate → cook → pack → fingerprint → output manifest.
  - cook: the NDF writer (incl. TOPO/IMPR/EXPR) and asset conversion
  - pack: the EDAT writer, with fixed ordering
  - It builds incrementally, using a cache keyed by input hashes and tool version.
- **Validator** checks:
  - dangling references, types and ranges
  - missing localisation
  - map consistency (capture zones vs the hidden ground map)
  - Python 2.5 script compilation
- **Fingerprint:** a hash over canonical *gameplay* content (decompressed NDF objects, scenarios, maps,
  scripts) plus the game build. Cosmetic assets are excluded. Exact recipe: [MOD_FORMAT.md](MOD_FORMAT.md) §12.
- **Rebase:** when the game updates, a 3-way merge (old base, new base, mod) produces a conflict report.

### L4 Deploy & run
- **Instances:** `D:\RUSE-Instances\<set>\` on the game's drive (hard links need the same volume).
  - Big read-only packs are hard-linked.
  - Small files the game might write (ini, logs) are copied.
  - Rebuilt packs are real files.
  - `steam_appid.txt` lets RUSE.exe start from that folder.

  Tools never write into a hard-linked file; they replace it. Several instances can sit side by side.
- **Launch/join:** Steam-compatible launch; `+connect_lobby <id>` when joining a lobby (checked in M3).
- **Runtime extender** (later, optional):
  - A proxy `version.dll` is placed only in the instance and loads our loader.
  - Hooks are found by byte patterns and checked against the build; RUSE.exe is never patched on disk.
  - Candidate features: mount extra packs (no rebuilds), tag lobbies and block mismatched joiners,
    raise the 7-nation limit, script hooks.

### L5 Front-ends
- **CLI `ruse`:** `detect index ls extract dump verify new-mod build check deploy launch fingerprint rebase import-rmod`.
- **Python API:** the same operations, for scripts and bulk edits ("all tanks +10 % HP").
- **Local service:** JSON-RPC on localhost, used by Studio and the Launcher.
- **RUSE Launcher (the players' app, `src/ruse_launcher/`):**
  - detects the game and build
  - browses and installs mods from the index; manages mod sets and join codes
  - one-click join, updates, instances, self-update
  - **installer (built 2026-09-29, `installers/`, ADR 9):** `RUSE-Launcher-Setup-<version>.exe`, made by GitHub on
    every push that changes the apps; no Python or Git needed, no admin rights. The Studio gets its own
    (`RUSE-Studio-Setup-<version>.exe`); a player never needs it.
  - **Steam integration (HOI4-style):** the user sets Steam's Launch Options once to
    `"<path>\launcher.exe" %command%`, so Steam's Play button opens our launcher instead of the game, and Steam
    lobby invites (`+connect_lobby`) route through it for mod sync before joining. No change to RUSE.exe.
    Later the launcher can offer to set this for the user (with their OK). To verify when the launcher exists.

  **The player's journey, screen by screen** (judged against the north star in §1: download, install, play)
  1. **Install:** one installer; no Python or Git needed. It opens the launcher when it's done.
  2. **Find the game (first run, automatic):** Steam's folder from the Windows registry → `steamapps\libraryfolders.vdf`
     → the library holding `appmanifest_21970.acf` → `steamapps\common\R.U.S.E`. The player sees "Found R.U.S.E. on D:
     (build 24687178)". Only if that fails: "Choose folder…". It has to be a Steam install (principle 10).
  3. **Check the game:** a known build with untouched packs is ready. Changed packs (a tool that patches the live game,
     for example) get a **Restore original files** button, which starts Steam's own file check (`steam://validate/21970`).
     A new game build: mods are checked against it before the first Play (rebase).
  4. **Where modded copies go:** a folder on the game's drive, `<drive>:\RUSE-Instances` by default, because sharing
     files with the game (hard links) only works on one drive. The launcher shows how much space that takes.
  5. **Steam's Play button (optional):** "Want Steam's Play button to open this launcher? [Show me how] [Skip]".
     v1 shows the steps; doing it for the player comes later, with their OK.
  6. **Home:** one big Play button with the active mod set ("Vanilla", "RUSE 2.0"), a switcher for mod sets,
     Join a friend, and Browse mods.
  7. **Browse:** mods from the index, with screenshots, description, author, and badges: "works with your game
     version", "multiplayer: must match" or "looks only", "contains scripts".
  8. **Install:** "This also installs: X (required)". It downloads from the first mirror that works, checks every
     file's hash, builds the modded copy in a side folder, and swaps it in only when it's complete (so a half-built
     copy never shows up). Then: "Installed. [Play]".
  9. **Play:** rebuilds only what changed (cache), starts Steam if it isn't running, then starts R.U.S.E. from the
     modded copy.
  10. **Join a friend:** paste a code, or it's read from the clipboard when a Steam invite opens the launcher (steps in L6).
  11. **Back to vanilla:** the "Vanilla" set runs the untouched Steam install. Uninstalling the launcher leaves the
      game exactly as Steam installed it; the uninstaller explains how to clear the Launch Options line.
  12. **Updates:** launcher updates download in the background and install when it closes. Mod updates show a badge.
      A mod set used with friends can be locked, so it only updates when the player chooses (the whole group has to
      update together). After a game update, mods that can't follow yet are paused with a message instead of
      breaking the game.

  **Disk space, a known cost:** an untouched modded copy costs almost nothing (hard links). A mod that only changes
  unit data rebuilds just the 3.5 MB `ZZ_GladPatchableWin.dat`. But a change to anything inside `ZZ_Win.dat` means a
  rebuilt 2.3 GB copy of that pack: textures, sounds, most scripts, and **text**. All `.dic` text lives in ZZ_Win ([FORMATS.md](FORMATS.md) §4),
  so every new unit with its own name triggers it. The cache keeps one copy per distinct result and hard-links it into
  every modded copy that uses it, but it's still heavy. This goes away if NDF data can mount an extra pack of our own
  (FORMATS.md open question 3): mods would then ship small packs of their own. Hence decision 1 below.

  **When something goes wrong** (multiplayer mismatches and desyncs are in L6)

  | What went wrong | The player sees | The launcher |
  |---|---|---|
  | game not found | "We couldn't find R.U.S.E. Is it installed through Steam? [Open in Steam] [Choose folder…]" | waits |
  | game files changed by another tool | "Your R.U.S.E. files were changed by another mod tool. [Restore original files]" | starts Steam's file check |
  | modded folder on another drive | "Mods need … GB here, because this drive can't share files with the game. [Continue] [Choose another folder]" | makes a full copy instead of hard links |
  | not enough space | "Not enough space on D: (needs … GB, … GB free)." | changes nothing until there's room |
  | Steam not running | nothing | starts Steam, then the game |
  | download failed | "Couldn't download RUSE 2.0 Core. Check your internet and try again." | tries every mirror first |
  | file damaged or tampered with | "The download of RUSE 2.0 Core didn't match its checksum, so it was deleted." | never installs an unchecked file |
  | two mods clash | "RUSE 2.0 Core and Old Units can't be used together: Old Units deletes a unit RUSE 2.0 Core changes. Remove one of them." | keeps the last working modded copy as it was |
  | game updated, mod not ready | "RUSE 2.0 Core doesn't support the new game version yet. Play vanilla, or wait for an update." | pauses that mod set |
  | game closes right after starting | "R.U.S.E. closed right after starting with RUSE 2.0. [Play vanilla] [Save a report]" | keeps the report for the mod's author |
  | antivirus or Windows blocks a file | "Windows or your antivirus is blocking a file: …. [How to fix this]" | links a help page |

  **Decided (2026-09-28):** test in M2 (moved up from M5/M6) whether the game can load an extra pack of ours. If it
  can, mods ship small packs and never rebuild the 2.3 GB one.
- **RUSE Studio (the modders' app, `src/ruse_studio/`, `py -3 -m ruse_studio`):** **v0.1 built (2026-09-28):** browse every unit
  and building by kind, nation and name; a unit's values in groups (cost, combat, movement…), its parts (its own or
  shared) and what uses it; all from the game index, which the Studio can also build. A language selector keeps the
  game's names by default and shows the tool, property names and units' in-game names in any of the game's ten
  languages (decision 21).
  **v0.2 (2026-09-28): edit in place.** The owner: a unit's page is where its stats get changed, not a copy step.
  Pick or make a mod at the top (new mods go in `<platform folder>\mods\`); every number on a unit's page is a box.
  A change is saved at once in the mod's `src/studio.rndf`, an ordinary `.rndf` file (MOD_FORMAT §2), and shows
  "was …" with Undo; changed units are marked in the list. Whole-number stats stay whole (rounded like the build),
  yes/no values are checkboxes. A unit's own parts (its gun, its turret) and the named objects it uses (weapons, ammo)
  open on their own page and edit the same way; for a named object several units use, the page says the change
  reaches all of them. **v0.3 (2026-09-29): parts several units share** (MOD_FORMAT §10.5): the page lists the units
  that use it and asks "Change it for: only <the unit you came from> (it gets its own copy) / all N of them"; saved
  as `patch own` or `patch shared` (changes for all of them go first, so an own copy has them too). Not yet: ids and
  nation (locked), texts and names. "Test in game" builds the mod into
  its own modded copy (`RUSE-Instances\studio-<mod>`) and starts the game with the engine's own code (`rusemod.play`,
  the same the launcher uses), so testing doesn't need the launcher. Later the launcher lists the mods in the shared
  `mods\` folder too, so a mod made in the Studio can be played from the launcher like any other.
  - content browser, reference viewer, schema-driven property editor
  - unit editor with a clone wizard
  - scenario/map workshop
  - diff and rebase views, build & test buttons
- **Blender bridge:** glTF export/import for models, later terrain and scenery.

### L6 Distribution & multiplayer sync
- **Mod index:** a git repo of manifests: id, versions, content hashes, download mirrors, game builds,
  gameplay/cosmetic flag. CI validates submissions. A published version is never changed; a fix is a new version.
- **Mirrors:** the files can live on GitHub releases, Nexus, ModDB, Thunderstore or CurseForge. The launcher
  verifies hashes whatever the source.
- **Mod sets and join codes:** a lockfile holds the exact mods, versions and hashes, plus the game build and platform version.
  - v1: the join code names the game build, the mods, their versions and the fingerprint
    ([MOD_FORMAT.md](MOD_FORMAT.md) §12). No server needed.
  - Later: an optional service for short codes and for transferring unpublished mods.
- **Safety:**
  - Scripts are code. They auto-install only from the index, or after explicit consent.
  - Native code (runtime extender plugins) is never taken from peers.

**How multiplayer stays in sync**

In short: everyone in a modded match plays through the launcher. The launcher's job is to make every player's game
files match; the match itself runs on R.U.S.E.'s own Steam multiplayer, like any other match. Players without the
launcher can still play normal (vanilla) matches, but not modded ones.

- R.U.S.E. multiplayer is lockstep ([FORMATS.md](FORMATS.md) §10: `TDesynchroChecker`). The PCs only send each other
  the players' orders; every PC runs the whole battle itself from its own copy of the game data. The battles stay
  identical only if every gameplay number is identical. One different price, speed or range and they drift apart, and
  the game's checker reports a desync.
- So gameplay files must match exactly while cosmetic files may differ ([MOD_FORMAT.md](MOD_FORMAT.md) §10.8), and the
  build must give the same result on every PC (§10.3, §10.9 there). The fingerprint proves both.
- Not known yet: whether the game compares any data when a player joins, or only notices mid-game. Test T3 answers it.

**Joining a friend, step by step (v1)**
1. The host picks a mod set and presses Play. The launcher shows the join code with a Copy button.
2. The host makes the lobby in the game, invites the friend on Steam, and sends the code in Steam chat or Discord.
3. The friend's launcher gets the code: pasted in, or read from the clipboard when a Steam invite opens the launcher
   (the Launch Options route, L5). It shows what's missing and how big the download is.
4. It downloads, checks every hash, builds, and compares fingerprints. If they match, it starts the game with
   `+connect_lobby <id>`.
5. Later, with the runtime extender (M10): the host's game writes the code into the Steam lobby itself, so clicking
   the invite is enough, and players with the wrong mods are stopped before they join. **Cheap test for M3:** can the
   launcher read or write the lobby's data while the game runs, without the extender? If yes, this comes much sooner.

**When something doesn't match**

| Situation | The player sees | The launcher |
|---|---|---|
| missing mods | "This game uses 2 mods you don't have: RUSE 2.0 Core 0.4.1, Better AI 1.2 (38 MB). Download and join?" | downloads, checks, builds |
| scripts not from the index | "These mods include scripts (code) that aren't from the mod index. Only continue if you trust the host." | waits for OK (safety rule above) |
| different game version | "Your friend is on a different version of R.U.S.E. (build …). Check you're both on the same Steam branch (Properties → Betas)." | does nothing else |
| mod not on the index | "Your friend is using a mod that isn't published (name). Ask them to publish it, or to send you their mod set file." | does nothing else (v2: direct transfer) |
| fingerprint differs after building | "Your game data doesn't match your friend's (K7Q2-M9XD vs …). Repair and try again?" | rebuilds the instance from scratch |
| desync during a game | "Your last game went out of sync. This usually means different mods." | offers to save the game's desync log for a bug report |

**2-PC test plan** (run on real PCs once M2 builds exist; record both build ids and fingerprints, the result, and any
desync log lines)

| Test | Setup | Expected | What it tells us |
|---|---|---|---|
| T1 vanilla baseline | both play from untouched instances (hard links only), 15-minute 1v1 skirmish | no desync | instances themselves are safe |
| T2 same gameplay mod | both have the $1-buildings mod from C2 | no desync | identical rebuilt packs play together |
| T3 mismatch on purpose | A has $1 buildings, B is vanilla | refused at join, or a desync | whether the game checks data at join or only mid-game, and what its checker compares ([MOD_FORMAT.md](MOD_FORMAT.md) §14 q5) |
| T4 tiny mismatch | one unit 1 % faster on A only; both build and use that unit | a desync | how sensitive the checker is; confirms "every NDF change is gameplay" |
| T5 cosmetic only | A has one changed text string (`.dic`), later a texture (M5) | no desync | the cosmetic list is right |
| T6 join through the launcher | Steam invite → launcher → `+connect_lobby` | joins with the right mods | the whole join flow (M3) |

**Solo tests (one PC, no second player)** cover most of the risk until a second player is available (decision 20):

| Test | Setup | Expected | What it tells us |
|---|---|---|---|
| S1 same build twice | build the same mods twice, into two new modded copies, from scratch | the rebuilt packs are identical byte for byte, same fingerprint | the build gives the same result every time (lockstep needs it); GitHub already runs the tests on Windows and Linux |
| S2 join flow on one PC | copy A's mod set gives a join code; a fresh copy B takes it (M3) | B ends up identical to A, same fingerprint | everything the launcher does to match two players |

What still needs a second player: a real match (T1–T5 above), to see that the game itself stays in sync. One Steam
account can't join its own game, and Steam Family Sharing doesn't let two people play one copy at the same time. So
the second player is either a second Steam account with its own copy of R.U.S.E. (on an old laptop, say), or a
volunteer from the R.U.S.E. community: with a join code, joining takes them a couple of minutes.

## 6. Key design decisions (this table is the decision record)

| ADR | Decision | Choice | Why | Alternatives |
|---|---|---|---|---|
| 1 | Core language | Python 3.11+ with type hints | runs inside Blender; same language as community tools; fastest for reverse engineering; AI-friendly | C#/.NET, Rust |
| 2 | UI stack | Web UI (TypeScript, three.js for 3D) in a desktop window (pywebview), served by the local service. **Confirmed by the owner 2026-09-28.** v0.1 uses plain JavaScript with no build step, and pywebview's bridge instead of a separate service; TypeScript once the screens grow | best 3D and UI ecosystem; one UI codebase for Launcher and Studio; runs on Linux/Deck | Qt / PySide6 |
| 3 | Runtime extender | C++ x64 proxy DLL, optional, instance-only | exe has no DRM/ASLR; `version.dll` is imported | none (repack only) |
| 4 | Deployment | Modded instances via hard links | never touch the Steam install; mod sets side by side | in-place swap with backups (fallback) |
| 5 | Mod identity | Engine export paths + owner paths + selectors | stable across updates, human-readable | indices (.rmod `index_map`) |
| 6 | Source format | NDF-style text + CSV + standard asset formats | familiar to Eugen modders (WARNO/SD2 use text NDF); git-friendly | JSON / YAML |
| 7 | Determinism | Fingerprint over canonical content, bundled runtime, fixed ordering | lockstep multiplayer | hashes of raw bytes only |
| 8 | License | **MIT (decided 2026-09-28)**. RUSE-Mod-Manager's GPLv3 code is never copied: we study what it does and build our own better version | maximum reuse by community tools and Eugen; independence | GPLv3 (rejected) |
| 9 | Packaging & install | Nuitka + Inno Setup, built by GitHub Actions: one installer per app (decision 22). **Built 2026-09-29** (`installers/`): each app becomes a program folder (not Nuitka's onefile: it's installed anyway, starts faster, and antivirus programs trust it more), checks itself, and is wrapped by Inno Setup; per-user install, no admin rights. Unsigned until the first public release, so Windows' SmartScreen warns once | faster start and fewer antivirus false positives than PyInstaller | PyInstaller, Briefcase |
| 10 | Updates | Velopack (spike first), fallback tufup | single self-updating installer | manual downloads |
| 11 | Modpack / lockfile | Modrinth `.mrpack` shape (`files[]` with path, hashes, download mirrors, size; `dependencies`) | proven, tiny packs, host-anywhere | our own format |
| 12 | Mod hosting | GitHub Releases now; Thunderstore once real mods exist; CurseForge last (needs a proxy server) | cheapest path that still scales | CurseForge first |
| 13 | Code signing | deferred to first public release; Azure Trusted Signing, then free SignPath | costs money; no instant trust anyway | sign from day one |
| 14 | Mod conflicts | Fixed load order; every pair of operations has a defined result (error, warning or note); math is exact and rounds once, half away from zero | predictable, identical on every PC | last mod wins, nothing else |
| 15 | Shared data in clones | A clone copies only what its source owns; editing shared data through one unit needs `own` or `shared` | no silent changes to other units | silent shared edits |
| 16 | Join codes | Game build + mod ids + versions + fingerprint; a published mod version never changes | about half the length of a full lockfile, checked end to end | the whole compressed lockfile |
| 17 | Extra-pack test | Moved up to M2 as check C3 | without it, every new unit name rebuilds the 2.3 GB ZZ_Win.dat | test in M5/M6 |
| 18 | Mod language details | A `final` pass; `when mod` blocks; WARNO's spellings; readable text keys | proven in Factorio, KSP ModuleManager and WARNO ([RESEARCH.md](RESEARCH.md) §5) | our own spellings, made-up hash keys |
| 19 | New nations | A real 8th nation (China, for RUSE 2.0): the runtime extender (ADR 3, M10) lifts the 7-nation limit, and the data gets an 8th entry wherever it has 7. Owner's call, 2026-09-28 | RUSE 2.0 wants a real nation, not a renamed one. **No faction is ever given up** (owner, 2026-09-28): there is no swap fallback; if the job turns out big, China comes later, never by replacing a nation | China takes over one of the 7 slots (**rejected**: it loses a faction) |
| 20 | Testing multiplayer alone | Solo tests S1–S2 (L6) until there's a second player; one real 2-PC match before the first public release | the owner has no second player yet; most of the risk (same build everywhere, the join flow) can be tested on one PC | wait for a friend |
| 21 | Display language in the tools | The game's own names are the default everywhere (mods use them); every modder can pick any of the game's ten languages for the tools, property names and unit names. Owner's call, 2026-09-28 | the community is international; no one language forced on modders | English by default |
| 22 | Apps | Two separate apps on one engine: **RUSE Launcher** (players: finds the game, loads mods, starts the game) and **RUSE Studio** (modders: the unit editor, later maps and models). Neither needs the other; each has its own window, start command and, later, installer. The Studio keeps its own "Test in game". Owner's call, 2026-09-29 | players get a small, simple app; modders get the full tools; each can change without breaking the other | one app with a modding mode |

## 7. Roadmap

Estimates are in sessions like today's. Every milestone ends with something usable.

| Milestone | Deliverables | Exit criteria | Est. | Risk |
|---|---|---|---|---|
| **M0 Foundations** ✅ | repo, docs; EDAT + NDF read/write; whole-game byte-identical check (38 archives, 2,176 NDF files); modded-instance launch | **done 2026-09-28** (C1, C2 passed) | — | — |
| **M1 Core tools** | combined file view + index (L2) ✅ (cloud session; the PC runs it); `.dic` r/w ✅ and `ruse` CLI basics ✅ (cloud session); scenario / AI-layer / capture-zone readers (our own code, informed by [LITTLEGROOVE_STUDY.md](LITTLEGROOVE_STUDY.md)) | every shipped file of these types round-trips byte-identically | 2–4 (was 4–6) | low |
| **M1.5 Frontier tests** (new) | short, capped tests of the riskiest unknowns: re-encode one terrain texture tile (`TGU1`) and one terrain mesh (`.tms`); read one 3D model (SPK) section table | clear yes/no: can we write new terrain? can we read models? Decides how big Pacific maps can be | ~3 | high (that's the point) |
| **M2 Mod system slice** | package v1; `.rndf` reader ✅, rules engine ✅, load order ✅, fingerprint + join codes ✅ (cloud session); the adapter between game files and the engine; `.rmod` import; extra-pack mount test (C3); instances already proven by C2 | the **pipeline** works end-to-end: a throwaway value tweak + 1 cloned unit (reused visuals) builds, loads in-game and matches in a 2-PC test (until there's a second player, the solo tests S1–S2 in L6 stand in; the 2-PC test comes before the first public release). This proves the tool, not a balance mod | 2–4 (was 4–6) | medium |
| **M3 Launcher v1** | Steam auto-detect ✅ (`ruse detect`), the window ✅ (v0.1: game status, mod sets, Play; its own app, `ruse_launcher`), one-click install into instances, modpacks, join codes; also installs the `.rmod` mods players already have, combinable and without patching the live install | first public alpha on GitHub, ModDB, Nexus | 3–5 | low |
| **M4 Studio v1** | content browser ✅ and unit view ✅ (v0.1, with the language selector), property editor ✅ (v0.2: numbers, in place, saved as a mod, Play), unit editor; clone **any** class with its **own** visuals, wired into menus, upgrades and AI; validation, diff/rebase | a non-programmer builds a new unit | 5–8 | low–medium |
| **M5 Textures & icons** | TGV r/w including a game-valid `TGU1` encoder (nobody has one), UI icon/flag pipeline | retextured unit with its own icon in-game | 3–5 | medium |
| **M6 Maps I** | map cloning, scenario editor, capture-zone compiler, AI layers, island maps on existing terrain | a new map listed and playable in multiplayer | 4–6 (was 5–8: formats now understood) | medium |
| **M7 Models** | SPK → glTF, Blender bridge, glTF → SPK (static, then skinned/animated). A first for R.U.S.E. | a new vehicle model in-game | 6–12 | high |
| **M8 Terrain / new maps** | terrain writer (heights + texture), heightmap import, maps from scratch, tropical scenery set | a new island map built from a heightmap | 8–15+ (sized by M1.5) | high |
| **M9 Scripting** | `.xyz` decompile, compile via a real CPython 2.5.1 (known route), mission/mode scripting | a new game mode (e.g. Island Defense) | 3–6 (was 4–8) | medium |
| **M10 Runtime extender** | **Un-parked 2026-09-28 (owner): RUSE 2.0 gets a real 8th nation, China.** The proxy DLL in the modded copy only (L4) raises the 7-nation limit; the data gets an 8th entry wherever it has 7 (every map's nation list, flags, menus). Later the same DLL can mount extra packs (no 2.3 GB rebuilds) and tag lobbies. **Step 1 (data):** `tools/nation_scan.py` counts every per-nation structure in the game data (read-only). **Step 2 (program):** find every place the game program assumes 7 nations, as the Red Alert 2 modders did before lifting their limit ([RESEARCH.md](RESEARCH.md) §6: what other games' modders learned) | China can be picked in a skirmish, with its own flag and units | unknown until the scan | high |
| **M11 Sound** | `.ess` codec, WAV import | a replaced sound plays in-game | 4–10 | high |

**Content comes after the tool.** Per the owner's direction (2026-09-28), no balance/unit-stat/roster
**content** is produced until the tool is usable (through M4). Value changes before then exist only to test the
pipeline, never as shipped balance. Study of Eugen's own data and scripts for design ideas is encouraged
throughout (see [ENGINE_NOTES.md](ENGINE_NOTES.md)) — read-only, nothing from the install is committed.

**Content track** (starts after M4, then dogfoods each later milestone):
- **RUSE 2.0 Core** — balance, cloned units, tactics — begins once Studio (M4) exists. It includes a new nation,
  **China** (owner, 2026-09-28), which needs M10 for the nation itself and M5 for its flag and icons. China is
  infantry first (§11): its units can borrow the game's models at first; its own models need M7.
- **Pacific Island Defense** needs M5–M8 (new islands need the terrain writer), plus M9 for a custom mode.
  US vs Japan fits the existing nation slots. M1.5 tells us early whether brand-new islands are realistic.

**Totals:** M0 is done. The first public release (M1, M1.5, M2, M3) is about 10–16 sessions. The full vision is
many months; the uncertainty sits in M7, M8, M10 and M11 (M10's size is known once its step 1 scan has run).

**Plan revision 2026-09-28 (PC session)**, after M0, the research, the LittleGroove study and the cloud session's
code: M0 closed; M1/M2 shrink (reader/writer, instances, `.dic`, CLI basics, rules engine, join codes done); M6/M9
risk drops (formats and compile route understood); new M1.5 tests the frontier early; the launcher gains immediate
value by installing existing `.rmod` mods safely; M10 parked.

### M0 checks (only two up front; everything else is checked when a milestone needs it)
| Check | Question | Needs you? |
|---|---|---|
| C1 | Does rewriting `everything.cpp` unchanged come out byte-identical? This decodes TOPO. | no |
| C2 | Does RUSE.exe run from a hard-linked instance with `steam_appid.txt`? It creates files outside the install; the install itself is not changed. | yes (run the game) |

Checked later, when needed: joining a lobby via `+connect_lobby` (M3). Mounting an extra pack from NDF data moved up
to **M2** (decided 2026-09-28): without it, every new unit name costs a 2.3 GB rebuild (L5).

### C3: can the game load an extra pack of ours? (moved up; can run now)

**Why:** all game text (`.dic`) lives in ZZ_Win.dat (2.3 GB). Without an extra pack, every mod that adds text, which
means every new unit name, rebuilds that whole pack (L5). With one, a mod ships a small pack of its own.

**Known so far** ([FORMATS.md](FORMATS.md) §1, §5, §6):
- RUSE.exe hard-codes the six core pack names and doesn't scan for extra `.dat` files.
- Map packs are mounted by NDF data: each map's `clustermap.cpp` has `TClusterMountMapDataPack{ DataPack
  'MapDat:\DataMap<Name>_v09.dat', DatasMapDirectory 'GenDatasmap/<Name>', MountingPoint 'Datasmap' }`.
- Script packs are registered by NDF too (`TResourceDescriptorPythonPack 'Eugen.ipk'`, `TClusterAddPythonPath`).
- Likely places for startup-time mounting: `genglad\patchable\clusterinitialisationpatchable.cpp` and
  `genglad\patchable\clusters\*.cpp` (names from `listings/`).

**Steps, cheapest first.** All in an instance; the Steam install is never touched.
1. **Survey (read-only):** list every NDF class whose name contains `Mount`, `DataPack`, `Pack` or `Cluster`, across
   all NDF files: where each is used and with which properties. Search RUSE.exe's strings for the same words. Record
   what's found in FORMATS.md. **Ready to run:** [`tools/c3_survey.py`](../tools/c3_survey.py) does all of this
   (`py -3 tools\c3_survey.py > c3_survey.txt`).
2. **Renamed map pack.** Proves a pack is found by the name in the data, and shows whether a pack's name is checked:
   - in an instance, copy `Maps\PC\DataMapTwoIslands_v09.dat` to a new name of the same length, e.g.
     `DataMapTwoIslandz_v09.dat`, then delete the original name from the instance's `Maps\PC` (that only removes the
     instance's hard link; the Steam file is untouched);
   - in `genglad\patchable\map\twoislands\clustermap.cpp`, change the `DataPack` text to the new name. Same length, so
     nothing else in the file moves. If the text lives in the STRG table (types 0x07 / 0x1C), use
     `Ndf.set_string(index, text)` (added for this, tested in `tests/`); the survey's "used Nx in file" note shows
     whether anything else in that file shares the string;
   - launch and start a skirmish on Two Islands. If it loads, packs are found by the name in the data (and a copied
     pack's header checksum doesn't depend on its file name). If not, write down the exact error.
3. **Startup mount.** If step 1 finds a mount object that runs at startup, point it at a small pack of our own holding
   one changed `.dic` string (a unit's name), and look for that name in-game. If this needs a new object or list item
   rather than a changed string, stop and write it down: adding objects waits for TOPO (FORMATS.md open question 1).
4. Write the result into FORMATS.md (open question 3) and MOD_FORMAT.md §7.

**What the results mean**
- Step 3 works: mods ship small packs, and ZZ_Win.dat is never rebuilt for text.
- Only step 2 works: map mods can ship packs of their own; text needs another route (the runtime extender's pack
  overlay, M10) or the 2.3 GB rebuild.
- Neither: the 2.3 GB rebuild stays until the runtime extender (M10).

**Result (2026-09-28): step 2 passed; step 3 has no route found so far.**
- **Step 1** (survey): the only mounting class is `TClusterMountMapDataPack`, run when a map loads; no startup mount
  of an arbitrary pack exists in the data (FORMATS.md open question 3; one lead left: `TestOption/LocalDataPath`).
- **Step 2** ([`tools/make_c3_instance.py`](../tools/make_c3_instance.py)): in an instance, Two Islands' pack existed
  only as `DataMapTwoIslandz_v09.dat` and `clustermap.cpp` named it. The owner played "(6) Centre de gravite" on it:
  **loaded and played normally.** So a map pack is found by the name in the data, and its file name isn't checked.
- **Meaning:** new maps ship their own pack (no core-pack rebuild). Game-wide text still needs the ZZ_Win.dat rebuild,
  which the streaming writer handles (until the runtime extender, M10, can mount packs). The map pack's header "checksum" turned out to be a
  random GUID, not a hash of the contents (FORMATS §6), so edited packs can't fail on it. The M1.5 terrain test
  confirms this in-game.

### C4: a text mod through the whole pipeline (passed 2026-09-28)

C2 proved the game loads a pack we rebuilt with a script. C4 proves the real pipeline: a mod written as text
([`examples/half-price-buildings/`](../examples/half-price-buildings/)), put through load order, the rules engine and the
bridge, then written into a modded copy.

    set PYTHONPATH=<repo>\src
    py -3 -m rusemod build examples\half-price-buildings --instance D:\RUSE-Instances\c4-half-price

- The build prints the load order and every note (one per building without a price), then "modded copy ready".
  It reports, as notes, any object name used in two files (an open question in MOD_FORMAT.md §14).
- Launch `RUSE.exe` from the instance with Steam running, start a skirmish, open the build menu: every building costs
  half of normal (x.5 rounds up).
- Record the result, the build's output and how long it took, in FORMATS.md or here.

**Result (2026-09-28): C4 passed.** The owner launched the instance and the build menu showed every building at half
price. Before launch, a check confirmed all 134 priced buildings halved and rounded up in the rebuilt pack (e.g.
French barracks 25 → 13, artillery factory 35/30 → 18/15, HQ 140 → 70). Build output, 33 s:

    load order: half-price-buildings
    note  $/GFX/Everything/... is named in both ...everything.cpp.gladndfbin and ...everything_debuginfo.cpp.gladndfbin  (×10,762)
    note  half-price-buildings (src/prices.rndf:4): $/GFX/Everything/Descriptor_Building_DalleBatimentDepot has no ProductionPrice; skipped
    note  half-price-buildings (src/prices.rndf:4): genglad/patchable/gfx/everything_debuginfo.cpp.gladndfbin#63542 has no ProductionPrice; skipped
    0 error(s), 0 warning(s), 10764 note(s)
    changed: genglad\patchable\gfx\everything.cpp.gladndfbin
    changed: genglad\patchable\gfx\everything_debuginfo.cpp.gladndfbin
    fingerprint: S1HP-X6PM
    modded copy ready: D:\RUSE-Instances\c4-half-price  {'linked': 37, 'copied': 23, 'written': 1}

- **The whole text-mod pipeline works in-game.**
- **Fixed (cloud session, 2026-09-28):** builds now leave the four `*_debuginfo` copies exactly as shipped (they're
  skipped, so no duplicate names and `patch every` can't reach them; C2 showed the game runs with them untouched), and
  similar notes collapse to three plus a count (`ruse build --all` shows every one). If a later test shows the game
  reads these copies (e.g. a cloned unit misbehaving), builds can mirror changes into them instead.
- **Was to fix:**
  - The duplicate-name notes are noise. The game's `*_debuginfo.cpp.gladndfbin` files (everything, vfx_bank, …)
    repeat every name of their main file. Treat `_debuginfo` files as shadows: don't report their names, and hide or
    collapse the notes in normal output.
  - Decide whether rules should touch `_debuginfo` at all. `patch every` also rewrote `everything_debuginfo`, and
    the game ran fine with it. C2 left it alone, and it's unknown whether the game reads it.

### C5: a new unit in the build menu (ready to run)

C4 changed values that already exist. C5 adds something new: a copy of the M3 Lee
([`examples/cloned-unit/`](../examples/cloned-unit/)) that costs 1, with its own name, id and menu slot
(MOD_FORMAT.md §10.5, "Fresh identity"). It is the "1 cloned unit (reused visuals)" of the M2 exit test.

1. **Two read-only checks** (they only read the game):

       set PYTHONPATH=<repo>\src
       py -3 tools\names_check.py
       py -3 tools\identity_check.py > identity.txt

   - `names_check`: A must say every EXPR and IMPR tree rebuilt byte-identical, with no "miss" lines. The build
     writes the clone's name into that tree.
   - `identity_check` (`identity.txt`):
     - **A** lists, for each unit class, the values no two units share. "NOT refreshed: check it" means the build
       copies that one as is. If it's an id number (a name ending in `Id`), add it to `IDS` in
       `src/rusemod/identity.py`; otherwise note it with the results.
     - **D** shows every build menu, row by row. Note the Sherman's row and how many columns it has.
     - **F** shows the Sherman and what a copy of it gets. If the Sherman is missing, not in a factory, or an upgrade
       (`UpgradeRequire` set), pick another US tank from D and change the name in
       `examples/cloned-unit/src/units.rndf`.
2. **Build** (about 30 s):

       py -3 -m rusemod build examples\cloned-unit --instance D:\RUSE-Instances\c5-clone

   Expect one note, "…Descriptor_Unit_R2_Sherman_Test gets its own DescriptorId … -> …, ClassNameForDebug
   'Unit_M4_Sherman' -> 'Unit_R2_Sherman_Test', PositionInMenu … -> …", no warnings or errors, and `changed:` the
   unit data file. The new PositionInMenu is where to look: row = slot ÷ 100, column = the last two digits.
3. **In game** (owner): launch `RUSE.exe` from the instance with Steam running, start a skirmish as the US in a mode
   where the Sherman is available, build an armour factory and open its menu.
   - **Pass:** a second Sherman at the new slot, costing 1, in the same row as the normal one (which keeps its usual
     price). Build it: it drives and fights like a Sherman.
   - Record the result, a screenshot of the menu, the build output and how long it took, here or in FORMATS.md.
4. **If it fails**, record what happened and when:
   - **The copy isn't in the menu:** its column may be past the last one the menu shows. Give it a free slot in
     another row this menu already uses (D lists them) by adding `PositionInMenu = <slot>` to the clone in
     `units.rndf`, and rebuild.
   - **The game crashes** at start or when the menu opens: the likely suspect is the debug-info copy of the unit data,
     which doesn't have the new unit (builds leave it as shipped). Next try: mirror new objects into it.
   - **Wrong price, or the original changed too:** send the build output.

**C5 prepared on the PC (2026-09-28):** `names_check` passed (EXPR and IMPR trees rebuild byte-identical in 2,176 of
2,176 files, no "miss" lines; only 446 of 3,614 multi-child nodes are in name order). `identity_check`: the Sherman
is an **upgrade** (`UpgradeRequire` = the M3 Lee, `IsUpgrade`), so C5 copies the **M3 Lee** instead (not an
upgrade, shown in every mode, row 3 of the US armour menu: 301 Greyhound, 302 Stuart, 303 Chaffee, 304 Lee, 305
Sherman). `Key` is set on 8 ground units, 2 infantry and 7 planes and isn't refreshed; the Lee has none. The first
build failed on the Lee's text key `LD_UNI_135`: the key writer refused names over 8 characters, but the game uses up
to 10 (fixed in `dic.py`). Build, 14 s, 0 errors: `Descriptor_Unit_R2_Lee_Test gets its own DescriptorId 1141 ->
4059, ClassNameForDebug 'Unit_M3_Lee' -> 'Unit_R2_Lee_Test', PositionInMenu 304 -> 306`, `changed:` the unit data
file, fingerprint `BPJC-0PK0`, instance `D:\RUSE-Instances\c5-clone`. Checked in the rebuilt file: the copy costs 1
at slot 306 (a 6th button in the Lee's row), the Lee is unchanged. The build printed 8,537 notes: 1,476 "named in
both" (names shared by every map's files, e.g. `$/ClusterTerrain/MapInstance`) and hundreds of "… and N more like
this" lines. **For the cloud session:** collapse these to one summary line per kind.

**C5 in-game (2026-09-28): the copy did not appear** in the US armour factory menu (no crash, the game ran).
What was checked next:
- Nothing in the game data refers to the Lee except the Sherman's `UpgradeRequire`, so the menu isn't a list of
  references; the game seems to scan the units.
- A 6th column isn't the problem: Japan's tank row shows units at 306 (Type 5 Chi-Ri) and 310 (Ta-Se).
- **The likely cause:** our copy kept the Lee's name key (`N_UNI_135`). RUSE-Mod-Manager's clone, which works for
  its users, always gives the copy a new `NameInMenuToken`. Eugen's own film copy of the Lee has its own key too
  (`N_UNI_136`). If the menu tells units apart by name key, a copy that shares one is dropped. C6 gives the copy its
  own key, so it tests this.
- For later (M9): `ZZ_Win.dat!genpython/eugenpatchable.ipk` → `parametres/classes.xyz` defines a Python class per
  unit (`Unit_M3_Lee` → `Database.GetObject('$/GFX/Everything/Descriptor_Unit_M3_Lee')`) for the AI and the mission
  scripts. The AI won't use a new unit until it has an entry there.

**C6 built (2026-09-28)** with the Lee copy, 18 s, 0 errors: `NameInMenuToken` = `C6000001`, "Lee C6-Test" in all 11
`baseunite.dic` files, fingerprint `NA86-7RBG`, instance `D:\RUSE-Instances\c6-named`.

**C6 in-game (2026-09-28): the named copy didn't appear either**, so a shared name key isn't the (whole) cause.
Checked next: RUSE-Mod-Manager's docs say its editor **can't** make new units yet (its `clone.py` isn't offered, and
nothing claims in-game success), so nobody has shown a new R.U.S.E. unit working. The `*_debuginfo` copy is a full
duplicate of `everything` (the same 63,686 objects, 363 extra debug strings); nothing shows the game using it for the
unit list. The Japanese units at 306 and 310 don't prove a 6th button exists in the US menu (306 is an upgrade).
**C6b, the slot probe** ([`examples/slot-probe/`](../examples/slot-probe/)): the copy takes the Lee's own slot 304
("Lee Probe", $1, key `C6B00001`) and the Lee moves to 306. Instance `D:\RUSE-Instances\c6b-slot-probe`,
fingerprint `W77E-1S9T`. If "Lee Probe" shows where the Lee was, copies work and the menu only has buttons for the
slots it ships with (then the build must pick shipped slots); if the slot is empty, the game ignores new units.

### C6: a new unit with its own name (ready to run, after C5)

C5 proves a new unit works. C6 gives it its own name through the new text step: C5's M3 Lee copy with the name
"Lee C6-Test" ([`examples/named-unit/`](../examples/named-unit/): the unit in `src/units.rndf`, the name in
`text/baseunite.csv`). Every language shows the English name (a missing language falls back to `us`).

1. **Build** (a few minutes: the text pack, ZZ_Win.dat, is 2.3 GB and gets rebuilt into the copy, so the drive needs
   that much free space):

       set PYTHONPATH=<repo>\src
       py -3 -m rusemod build examples\named-unit --instance D:\RUSE-Instances\c6-named

   Expect the fresh-identity note from C5, `texts: 11 file(s) in ZZ_Win.dat (baseunite.dic ×11)` (ten languages and
   `dev`), no warnings or errors.
2. **In game** (owner): skirmish as the US, armour factory menu.
   - **Pass:** the new Lee copy (costing 1) is called "Lee C6-Test"; the normal Lee keeps its name.
   - Record the result, a screenshot, the build output and how long the build took.
3. **If the name is blank or shows a code:** unit names may not come from `baseunite.dic` (RUSE-Mod-Manager's note).
   Check which `.dic` holds the Sherman's own name key (`ruse dump` shows it on `NameInMenuToken`), rename
   `text/baseunite.csv` to that dictionary, and rebuild.

**This plan is a living document.** We adjust it together as we learn.

**Progress (2026-09-28):** C1 passed (lossless NDF round-trip). First real library landed: `src/rusemod/`
(EDAT + NDF read/write with an editable object model). [`tools/verify_writer.py`](../tools/verify_writer.py)
proves, read-only against the install, that the archive rebuilds byte-identical, a value edit applies as a
minimal in-place change, and the edited archive reads back with all other members intact.

**C2 passed (2026-09-28): the game loads our rebuilt archives.** [`tools/make_test_instance.py`](../tools/make_test_instance.py)
set all 134 building prices to $1 and built a modded instance (`.dat` archives hard-linked, other files copied,
`steam_appid.txt`). Launched directly from the instance with Steam running, the game showed every building at $1.
The Steam install was verified untouched afterwards. This validates the member writer (including our own zlib
re-compression), the data mapping, and the instance deployment model. **M0 is complete.**

**Design written up (2026-09-28, cloud session, no game files needed):** the exact rules for how mods combine
([MOD_FORMAT.md](MOD_FORMAT.md) §10), the fingerprint and join codes (§12), the multiplayer flow and a 2-PC test plan
(L6), the game model ready to build (L2), and the launcher screen by screen (L5). The owner's decisions are recorded
next to each, and in §6 below.

Remaining for M1: `.dic`/scenario/mapinfo readers, the combined file view and the index (specified in L2), and the
`ruse` CLI.

## 8. Risks

| Risk | Impact | Mitigation / early warning |
|---|---|---|
| TOPO / NDF writer fidelity | can't add objects | C1 first; byte-identical gate |
| Instance launch fails | must touch the install | C2 first. Fallback: in-place swap with journal + backup (players), full copy (dev) |
| ~~Map-pack header checksum enforced and unknown~~ | — | retired: it's a random GUID, not a hash (FORMATS §6) |
| 7 nations hard-coded | no China for RUSE 2.0 | size the job early (M10 step 1, the data scan; step 2, the program side) and follow what worked elsewhere (RESEARCH.md §6). No swap fallback: the owner keeps all 7 factions, so China waits rather than replacing one |
| SPK model format complexity | no new models | export first; static meshes before skinned ones |
| Terrain can't be written | no new maps / islands | reading is solved elsewhere, writing is not: M1.5 tests re-encoding early; M8 sized by the result |
| Python 2.5 toolchain | no new scripts | route known: compile with a real CPython 2.5.1 (a download, so your OK first); uncompyle6 to decompile |
| Game updates | mods and tools break | per-build registry, rebase, byte-pattern hooks, CI on fixtures |
| Non-determinism across PCs | desyncs | canonical fingerprints, bundled runtime, 2-PC tests |
| Community split | low adoption | `.rmod` import/export; talk to LittleGroove and Prolution; publish everywhere |
| Legal | takedown | ship no game files; ask Eugen for an OK |
| Malicious mods | user harm | scripts only from the index or with consent; signed releases; no native code from peers |
| Small team (you + AI) | work stalls | docs, ADRs, tests, open source, contributor guide |
| WebGL unstable in the embedded webview | 3D map/model viewer blocked | prototype a three.js scene in pywebview early (cheap spike) |
| Antivirus / SmartScreen distrust of the installer | players scared off (**seen 2026-09-28:** Chrome called the first test build "dangerous"; the file was verified clean) | Nuitka; players download GitHub Releases, not test builds (`release.yml`); in-app updates so a browser only sees the first download; false-alarm reports per release; winget / Microsoft Store later; signing at first public release (installers/README.md "Browser warnings") |
| Publishing Eugen-owned content (RUSE-Mod-Manager reset its public history "for Eugen Systems compliance") | takedown | `.gitignore` blocks game files; never commit extracted assets or decoded game scripts; check before each push |
| Reinventing formats others already decoded | wasted credits | study RUSE-Mod-Manager's approach first ([LITTLEGROOVE_STUDY.md](LITTLEGROOVE_STUDY.md)); write our own (MIT, never copy) |

## 9. Open decisions

1. Working name. Ideas: *RUSE Reforged*, *OpenRUSE*, *RUSE Forever* (a nod to FAF).
2. ~~License~~ **Decided: MIT.** We study RUSE-Mod-Manager's approach (terrain, `TGU1`, scenarios, AI layers,
   capture zones) as reference and write our own, better version. Never copy its code.
3. ~~GitHub account/org and repo, project folder, git~~ **Done:** github.com/sneadtristen6/Ruse-Mod-Platform.
4. ~~UI stack~~ **Decided (owner, 2026-09-28): web-style** (ADR 2). The launcher v0.1 is built that way.
5. Outreach timing. Recommended: LittleGroove now (align on `.rmod` import/export), Eugen after the M2 demo.
6. Which unit to clone as the M2 test (suggestion: a US infantry unit, for Pacific later). **C5 uses the M4 Sherman**:
   a tank is easy to spot in its menu, and C5 only tests the pipeline. Infantry can follow once C5 passes.
7. A second player for the 2-PC tests (L6), needed before the first public release: a second Steam account with its
   own copy on another PC, or a community volunteer. Until then the solo tests S1–S2 stand in.

## 10. Next steps

Done so far: M0 (C1 and C2), the repo on GitHub, and the design for M1–M3 on paper (Progress, §7).

1. **PC session:** ~~C3 step 1, TOPO check, text-file check~~ **done 2026-09-28**, results in FORMATS.md:
   - **TOPO:** adding objects is unblocked. Rule: a new named object goes in; a clone goes in if its source is; append
     (order looks irrelevant). Final proof = the M2 cloned-unit test in-game.
   - **Text (`.dic`):** layout and writer confirmed on all 1,232 files; keys are readable names; 10 languages. **For the
     text writer (cloud session):** each file has one special entry, key `0x8000000000000000`, listing every character
     the file uses. Adding text with a new character must add it there. **Done (cloud session):** the writer now adds
     new characters to the end of that list and stores texts without a null, like the game.
   - **C3 step 1:** the only mounting class is `TClusterMountMapDataPack`, run when a map loads. No startup mount of an
     arbitrary pack was found (one lead: `TestOption/LocalDataPath`). So maps can ship their own pack; game-wide text
     likely needs the ZZ_Win.dat rebuild.
   - ~~C3 step 2~~ **passed 2026-09-28:** a renamed map pack loads when the data names it (§7 "Result"). New maps
     can ship their own pack. Reusable instance builder: `src/rusemod/instance.py` (tested).
   - ~~C4~~ **passed 2026-09-28:** the half-price mod built with `ruse build` worked in-game (§7 "Result").
   - **M1.5 terrain, started 2026-09-28** (FORMATS §6 "Terrain"): readers and writers for the terrain mesh
     (`rusemod.tms`) and the tile container (`rusemod.tmst`), proven lossless on all 64 sets. The map pack's
     "checksum" is a random GUID, so it can't block edits. A TGU1 texture codec (`rusemod.tgu1`, `rusemod.dxt`) is in
     progress.
   - **Next on the PC, needs the owner at the game** (one instance per test, map Two Islands, "(6) Centre de gravite"):
     1. **Mesa:** `py -3 tools\verify_tms.py --pack TwoIslands --out DIR` builds a pack with a flat-topped hill at the map
        centre. Is it drawn, and do units climb it or clip through (the `.kdt` copy isn't updated)?
     2. **Mirror:** `py -3 tools\verify_tmst.py --make-test TwoIslands OUT.dat mirror` swaps every tile with its
        left-right twin (the game's own tile bytes). Proves the game reads our rebuilt tile store.
     3. **Checker:** the same with `checker` makes every tile a coloured ZIPO checkerboard (colour = detail level).
        If it shows, terrain textures can be written without a TGU1 encoder.
     Build each into an instance with `rusemod.instance.build_instance(..., replace={r"Maps\PC\DataMapTwoIslands_v09.dat": pack})`.
     4. **C5, a new unit** (§7 C5): two read-only checks, one build, then look for a second Sherman, costing 1, in the
        US armour factory's menu.
     5. **Nation scan** (read-only, no game launch needed): `py -3 tools\nation_scan.py > nations.txt`. Record its
        summary and the starred lines of B in FORMATS.md §3: that's the data side of the new nation (decision 19).
     6. **C6, a unit with its own name** (§7 C6), after C5: one build, then look for "Lee C6-Test" in the menu.
     7. **Launcher v0.1 and the 3D check** (needs the owner at the PC). The launcher and the Studio are two separate
        apps now (decision 22), each started on its own:
        - Once: `py -3 -m pip install pywebview` (Windows 10/11 already have the web engine it uses).
        - `py -3 -m ruse_studio --spike` (the 3D check belongs to the Studio, for its map and model views): a rotating island. Record the lines in the box (WebGL 2, GPU, frames per
          second). **Pass: 30+ frames per second.** It loads the 3D library from the internet, so the PC must be online.
        - `py -3 -m ruse_launcher`: the window is called "RUSE Launcher"; the home screen should say "Found R.U.S.E. on D: (build …)". Press "Open mod
          sets folder" and save a file `half-price.toml` there with `name = "Half-price test"` and
          `mods = ["<repo>/examples/half-price-buildings"]` (forward slashes). Pick it and press Play: the Details box
          shows the build, then the game starts from `D:\RUSE-Instances\half-price` with every building at half price.
        - Record what worked and anything confusing on the screen.
     8. **The game index** (read-only, no game launch):
        **Done on the PC (2026-09-28):** `index build` took 35 s and wrote a 269 MB file
        (`<platform folder>\index¦70294-190852.sqlite`): 38 packs and 217 nested ones (both match `listings/`),
        241,160 objects, 605,961 references, 27,522 shared objects and 130,845 texts (the same count as the decodable
        `.dic` keys). The queries take 0.3–0.45 s each: `show` lists the Sherman's values; `clone` lists what a copy
        copies, shares and references; `filter … ProductionPrice[0] gt 100` finds none, correctly, since the priciest
        units cost 80 (the atomic cannons; `gt 40` finds 39); `texts Sherman` finds the name `N_UNI_137` and 13
        dialog and description lines. Nothing wrong. Only noise: the build's summary prints a line for each of 20 sound
        files found in 44 packs. (In Git Bash, set `MSYS_NO_PATHCONV=1`, or `$/GFX/...` gets turned into a Windows path.)
        - `py -3 -m rusemod index build`: indexes every pack, file, object, reference and text (target: about a
          minute). Record its counts, time and file size here or in FORMATS.md, and whether the file counts match
          `listings/` (38 packs, 217 nested).
        - Try it: `py -3 -m rusemod index show $/GFX/Everything/Descriptor_Unit_M4_Sherman` (its values, owner,
          what uses it and what it uses), `... index clone $/GFX/Everything/Descriptor_Unit_M4_Sherman` (what a copy
          copies and shares), `... index filter TUniteAuSolDescriptor ProductionPrice[0] gt 100`, `... index texts
          Sherman`. Note anything wrong or slow.
     9. **Studio v0.2** (after item 8; needs pywebview like the launcher; build the index again first, it now
        records list types): `py -3 -m ruse_studio`. Browse units, open the M4 Sherman, switch the language (top
        right) through a few languages. Then make a mod ("Mod" menu → "New mod…", call it `studio-test`), set the
        M4 Sherman's price to 1 in every box, press "Test in game" and check the price in a skirmish (the launcher
        isn't needed for this). Record anything wrong, slow or badly translated (translations: the game's words in
        `src/rusemod/labels.toml`, the Studio's own in `src/ruse_studio/words.toml`).
        - Optional: `py -3 -m pip install -e .[apps]` once gives two commands, `ruse-launcher` and `ruse-studio`,
          which open the apps without a console window.
    10. **The installers** (needs the owner at the PC; `installers/README.md`): on GitHub, Actions → the latest
        **apps** run → Artifacts → download `launcher-installer` and `studio-installer`, unzip, run each setup.
        Windows warns once ("Windows protected your PC": More info → Run anyway; they aren't signed yet). Check: both
        appear in the Start menu with their own icons, both open, the launcher finds the game, the Studio opens the
        M4 Sherman, and Windows' "Installed apps" can uninstall each. Record anything odd.
2. **PC session, then M1:** build the game model from L2 (the combined file view and the index), the `.dic` reader and
   writer, and the `ruse` CLI (`detect index ls extract dump verify`). It needs the game files, so it runs on the PC.
3. **Cloud sessions (no game needed):** done 2026-09-28: tests that GitHub runs on every push (Windows and Linux), the
   `ruse` tool (detect, ls, names, dump, extract), the `.dic` reader/writer, load order, the mod rules engine
   (all of MOD_FORMAT §10), the `.rndf` reader, fingerprints and join codes (see README "Code so far"), and the
   bridge between game files and the engine for value changes, with `ruse build` (C4 is ready).
   ~~Next: the bridge adds and removes objects~~ **done 2026-09-28:** new objects get their export name, TOPO entry
   (the PC's rule) and imports; deleted ones keep every index; clones get their own id, debug name and build-menu
   slot (`rusemod.identity`, MOD_FORMAT §10.5). **C5 is ready for the PC** (§7).
   ~~Also from C4: the `*_debuginfo` notes~~ **done:** debug-info copies are left as shipped, similar notes collapse.
   ~~Next (cloud): names for new units~~ **done:** text mods (`text/*.csv` into the game's `.dic` files, `loc()` in
   `.rndf`, `rusemod.loc`); `ruse build` rebuilds ZZ_Win.dat too when mods have texts, streamed into the modded copy.
   Modded copies now keep the last working copy until a new one is complete, and fall back to full copies on another
   drive. **C6 is ready for the PC** (§7). Also done: the new nation's step 1 (RESEARCH.md §6, `tools/nation_scan.py`).
   **Launcher v0.1 done (2026-09-28):** the window (web-style, decided by the owner) with the home screen: finds the
   game (or "Choose folder…"), lists mod sets, and Play builds the set's modded copy (the same code as `ruse build`),
   starts Steam if needed and starts the game; Vanilla starts through Steam. Mod sets are hand-written files for now
   (`%LOCALAPPDATA%\RUSE Mod Platform\sets\*.toml`, see `ruse_launcher/api.py`). Plus the 3D check page (now in
   the Studio). The PC tries both (item 1.7).
   **Tried on the PC (2026-09-28), installed from the test build:** the download was verified (its SHA-256 matched
   GitHub's record, Defender clean) and it installed. The window works (the Edge engine, finds the game, build
   24670294). The mod set only appeared after the owner made the file by hand and dropped it into the sets folder.
   **The owner: "this needs to be worked out, it will be hard for people who aren't techy."** Found on the way:
   - The installed app's `--self-test` fails its window check ("WebView2Loader.dll isn't next to the program or on
     the search path") although the window works: pywebview loads it from `webview\lib\runtimes\win-x64\native\`.
     The check should look where pywebview looks.
   - The PC session's tools run inside the Claude app's Windows package, which redirects its AppData writes, so an
     installer or file it starts isn't seen by the owner's apps. The owner runs installs; the PC session puts files
     on D:\.
   **Launcher v0.2 requirement, before any player uses it: players never touch a file.**
   - **Mod sets are made in the window:** "New mod set" (name it, tick the mods), then edit, rename, duplicate and
     delete from the set's menu. The launcher stores them itself; players never see TOML.
   - **Adding mods takes one action:** Install from "Browse mods" (the index, L6); an "Add a mod file…" button; drag
     a mod file onto the window; double-click a mod file in Explorer (the installer registers the file type) and
     the launcher asks "Install this mod?". Later, `ruse://` links from a web page.
   - **Join codes** (MOD_FORMAT §12): paste a code, and the launcher installs what's missing and makes the set.
   - Lists update by themselves when something changes (no restart), and every error says what to do next in plain
     words.
   - Mod folders like `examples/` stay the modders' format (the Studio). Players get packaged mods.
   **The game index done (2026-09-28)**: `rusemod.index`, `ruse index` (L2 "Built"). The PC runs it (item 1.8).
   The owner (2026-09-28): the launcher stays at v0.1 for now; the core tools come first.
   **Studio v0.1 done (2026-09-28)**: browse units, a unit's values, parts and users, the language selector with
   the game's names by default (decision 21). **v0.2 done (2026-09-28)**: the owner asked to edit units right on
   their page instead of copying them first: numbers are edited in place, saved in the mod's `src/studio.rndf`,
   and "Test in game" starts it (L5). The PC tries it (item 1.9).
   **Two apps (2026-09-29, decision 22):** the owner asked for the Studio and the launcher to be separate apps. They
   are: `ruse_launcher` (RUSE Launcher) and `ruse_studio` (RUSE Studio), each with its own window and start command,
   both on the engine `rusemod`; starting the game moved into the engine (`rusemod.play`), the game folder picked by
   hand is shared (`rusemod.home`), and the Studio's screen words moved into the Studio (`words.toml`).
   **Installers (2026-09-29, ADR 9):** the owner asked for both apps as real Windows installers; built by GitHub on
   every push (`installers/`, `.github/workflows/apps.yml`), each checked by installing it on GitHub's Windows machine.
   The PC tries them (item 1.10).
   **Studio v0.3 (2026-09-29):** parts several units share can be changed for one unit only or for all (L5), proven
   down to the built game data by a test.
   Next (cloud), the owner's order: names, moving a unit to another menu or nation, then new units (copies).
   Later (cloud), launcher steps, one at a time: installing mods into the launcher's library (from a folder or zip,
   then RUSE-Mod-Manager's `.rmod`), mod sets made on screen, the join-a-friend screen (join codes), then the
   installers (Nuitka + Inno Setup; one for each app) and browsing the mod index. And whatever C5/C6 turn up.
4. **You:** the open decisions in §9 (name, outreach timing, the unit to clone in M2, a second player).

**How the two sessions share the work**
- **Cloud session:** research and design, nothing that needs the game files. It writes its results into these docs.
- **PC session:** everything that needs the game: running checks and tests, building against the install, editing
  files on the PC.
- **GitHub `main` is the shared state.** The sessions can't see each other's chats, so anything the other one needs
  goes into the repo. Pull `main` before starting, push to it when done, and keep README's "Current stage" line and
  this section up to date.

## 11. RUSE 2.0 design notes (draft, 2026-09-28)

The owner's ideas, so nothing gets lost. **Content starts after M4** (the tool first, principle 12); nothing here is
built yet. **The rule for all of it: as simple as R.U.S.E. already is.** Every new unit is explainable in one line
(one strength, one weakness), and every counter is something both players can see.

**What R.U.S.E. already has** (the base to build on):
- Infantry: light and heavy in every nation, plus paratroopers. Some nations have extras: German anti-tank infantry,
  Italian recon infantry, Japanese snipers, pioneers and guard units.
- Terrain: forests give infantry 25% more resilience, and an ambush from a forest or a town does 3× damage. Infantry
  beats tanks up close from cover; tanks beat infantry in the open.
- Ten ruses, in four kinds: reveal (Spy, Decryption), hide (Radio Silence, Camouflage Net), decoy (Decoy Building,
  Decoy Offensive, Reverted Intel) and behaviour (Blitz, Terror, Fanaticism). A new card about every 2 minutes.

**China: infantry first (owner, 2026-09-28).** In WWII China's strength was its infantry, so in RUSE 2.0 infantry is
China's focus. It also gets a few light tanks and one medium (not the focus), **good mobile anti-aircraft** and
**solid artillery**, and a small, weak air force (below). China wins with ambushes, towns, numbers and the right
squad for each job, and defends the sky mostly from the ground.

**China's infantry (draft names).** Until China has its own models (M7), each squad borrows an existing infantry look
(the 88th Division can use the German heavy infantry: its German helmets are accurate).

| Squad | Type | History |
|---|---|---|
| NRA Rifle Squad | light | National Revolutionary Army regulars |
| 88th Division Infantry | heavy | German-trained division, Shanghai 1937 |
| Sihang Defenders | urban | the 88th Division battalion that held the Sihang Warehouse in Shanghai in late October 1937 ("the Eight Hundred Heroes") |
| Sharpshooters | sniper | |
| Flamethrower Squad | flamethrower | |
| Guerrillas | recon | resistance fighters behind Japanese lines |

The game already ships a Simplified Chinese language (`sc`, FORMATS.md §4), so Chinese players get the names in
Chinese; the other nine languages get the English or local names.

**China's vehicles and guns (draft; not the focus).** R.U.S.E.'s eras (1939, 1942, 1945) decide what's in the menu,
so China only ever has one or two of each at a time. Much of China's real equipment came from Germany and Sweden
before 1937, the Soviet Union from 1937 to 1941 (about 1,600 guns and 82 T-26 tanks) and the US from late 1941. So both Soviet and
American artillery are historical, in different eras.

| Unit | Type | Era | History | Looks like (for now) |
|---|---|---|---|---|
| Vickers 6-ton | light tank | 1939 | about 20 bought in 1935–36 | the UK's "Vickers" unit, if it's this tank (check) |
| T-26 | light tank | 1939–42 | 82 from Soviet aid | the Soviet T-26 |
| M3A3 Stuart | light tank | 1945 | 1st Provisional Tank Group, Burma 1944–45 | the US M3A1 Stuart |
| M4A4 Sherman | medium tank (the only one) | 1945 | same | the US M4 Sherman |
| 20 mm Solothurn truck | mobile anti-aircraft | 1939–42 | the Solothurn was China's main AA gun at Shanghai and Nanjing (1937); the truck is game licence | a light AA vehicle |
| Bofors 40 mm half-track | mobile anti-aircraft | 1945 | 80 Bofors 40 mm guns came through Lend-Lease; the half-track is game licence | a US AA half-track |
| 15 cm sFH 18 | heavy howitzer | 1939 | bought from Germany | the German sFH 18 |
| Bofors 75 mm mountain gun | light gun | 1939–42 | bought from Sweden | a 75 mm gun |
| Soviet 76 mm gun | field gun | 1942 | Soviet aid | the Soviet ZiS-3 |
| 75 mm pack howitzer | light howitzer | 1945 | US Lend-Lease, carried by mules in Burma | a light gun |
| 3.7 cm Pak 36 | anti-tank gun | 1939–42 | bought from Germany | the German Pak 36 |

China had almost no mobile anti-aircraft in real life; the owner wants it strong (China's air force is weak), so the
two AA vehicles take that liberty.

**China's air: small and weak on purpose (decided 2026-09-28).** No planes at all would leave China blind (R.U.S.E.
scouting leans on planes) and unable to chase off the enemy scout planes that find its hidden infantry. So:
- **Fighters and recon planes only, no bombers.** The fighter is the I-16 in every era (Soviet aid; the game's Soviet
  I-16 is an exact match). The recon plane borrows an existing look, picked when it's built.
- **One expensive airfield.** If the game can cap a building at one per player, cap it (check 4); if not, the high
  price does the job.
- It works with the rest: the Listening Post sees planes coming, the mobile AA shoots them down, the fighters chase
  off scouts anywhere on the map.
- If playtests show China is fine without planes, the airfield goes.

**Infantry: one strength, one weakness each**

| Type | Good at | Bad at |
|---|---|---|
| Light (riflemen) | cheap and fast; ambushes from forests and towns | tanks in the open |
| Heavy | tanks up close, and holds its own against infantry | slow and expensive |
| Urban | holding towns: tough, hard to pin down, deadly at the short range towns force | slow and outranged in the open |
| Sniper | infantry at long range; hard to spot | anything with armour; dies fast up close |
| Flamethrower | infantry and forts in cover | very short range; fragile |
| Guerrilla (recon) | hidden scouting and harassment; cheap | real fights |

**Towns: the game's town bonus is enough (owner).** No new rule. The urban squad holds towns with numbers the game
already has: more health, harder to pin down, and high damage at short range (fights in towns are short range because
buildings block sight).

**Flamethrower infantry:** an infantry squad carrying the flame weapon the flame tanks already have (the US Sherman
flamethrower, the Italian L6/40 Lanciafiamme), with a short range.

**New ruses (draft; for every nation, like the ten existing ones):**
- **Counter-Battery:** enemy artillery that fires in the sector is revealed (optional: the Listening Post covers most of it).
- **Monsoon:** planes can't attack in the sector (the Burma monsoon grounded air forces).
- **Tunnel Warfare:** your infantry in the sector's towns stays hidden after it fires (the tunnel villages of
  northern China). Needs balancing: it may be too strong.

Whether new ruses are possible at all depends on whether ruses are data or program (check 1).

**Pacific forts (draft):**
- **Coconut-log bunker:** very tough against artillery, weak against flamethrowers and close assault
  (Tarawa, Peleliu). Looks like Japan's buried bunker for now.
- **Cave position:** hidden until it fires; tough; narrow field of fire (Iwo Jima).
- **Coastal battery:** long-range gun against ships and landing craft; weak against bombers.
- **Jungle watchtower:** sees far, including into nearby forests; fragile. Looks like the UK's forward warning post.
- **Wufu Line bunker (China):** a concrete pillbox from the line built west of Shanghai with German advisers (1930s).

**Listening Post (the owner's pick, against late-game artillery and air raids).** A building that warns you: every
enemy plane, and every enemy gun that fires, inside its large listening radius shows on your map. It doesn't shoot;
you answer with your own units. It replaces the idea of a fort that shoots shells down (no WWII weapon could, and the
game almost certainly can't treat a shell as a target). Historical: China's *jing bao* warning network had observers
listening for planes and phoning in their position and heading; it warned the Flying Tigers before their first fight
(December 1941). Armies found enemy guns by sound too (sound ranging). **China only** (owner): its signature
building.

**Kamikaze (Japan, owner):** a plane that dives into its target: huge damage to one target, and the plane is lost.
Historically from October 1944 (Leyte Gulf), mostly against ships, which fits Pacific maps with the US Navy's ships.

**Voices and sounds:** needs the game's sound format decoded first (M11, last and riskiest). Then Chinese voice lines
recorded by Mandarin speakers (volunteers or paid). Until then China borrows an existing voice set.

**Checks before designing numbers** (PC, read-only, with `ruse dump` / `ruse names`):
1. Are ruses data (one object per ruse) or program? (new ruses)
2. What does the UK's forward warning post detect, and does artillery already reveal itself when it fires? (the
   Listening Post)
3. Can a plane be set to be lost when it attacks? (kamikaze; otherwise it needs the add-on, M10)
4. Can the game cap how many of a building a player has, e.g. one airfield? (China's air)

Sources: R.U.S.E. terrain and ambush rules (https://ruse.fandom.com/wiki/Ambush,
https://ruse.fandom.com/wiki/Strategies_and_Tactics), ruses (https://ruse.fandom.com/wiki/Ruses); the Sihang Warehouse
(https://en.wikipedia.org/wiki/Defense_of_Sihang_Warehouse); China's warning network
(https://historynet.com/american-volunteer-group-claire-l-chennault-and-the-flying-tigers/,
https://warfarehistorynetwork.com/article/top-flying-tiger-general-claire-chennault/); the first kamikaze attacks
(https://www.history.com/this-day-in-history/october-25/first-kamikaze-attack-of-the-war-begins); China's guns
(https://en.wikipedia.org/wiki/15_cm_sFH_18, https://en.wikipedia.org/wiki/Bofors_75_mm_mountain_gun,
https://en.wikipedia.org/wiki/Solothurn_ST-5, https://www.navweaps.com/Weapons/WNUS_4cm-56_mk12.php,
https://historynet.com/the-m-1-75mm-pack-howitzer/) and Soviet aid
(https://www.gw2ru.com/history/232540-how-the-ussr-helped-china-in-the-war-against-japan-photos); Chinese armour
(https://en.wikipedia.org/wiki/Vickers_6-ton, https://en.wikipedia.org/wiki/T-26); the unit lists in RUSE-Mod-Manager's
class catalog (facts only).
