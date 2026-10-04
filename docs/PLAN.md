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

**What R.U.S.E. 2.0 is (the owner, 2026-10-01): a game that plays a game with R.U.S.E.** It understands how the base
game works with every file it reads, so whatever a modder makes works in the game every time, the first time; that is
the goal. In practice: every rule the game follows becomes a check in the build (the audit, LOG.md 2026-10-01), so a
mod that would break in the game is refused, with what to change, before anything is written.

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
| Maps | 86 map entries in `mapinfo.cpp` NDF; map packs are mounted by NDF data (`TClusterMountMapDataPack`); map names come from data | verified / medium | new maps look data-only |
| Map packs | 16-byte header checksum of Maps\PC packs unknown; `save.boobspc` and `output.sdb` carry plain MD5s | open / verified | could block edited map packs, so test early |
| Nations | 7 nations (US, GER, UK, FR, ITA, USSR, JAP) and 7-slot data structures | medium | rosters are data-only; an 8th nation through data alone is the open question; Pacific (US vs JAP) needs none |
| Scripts | `.xyz` = zlib-compressed Python 2.5 code objects; script packs are registered by NDF | verified | new missions/modes possible; needs a Python 2.5 compiler |
| Multiplayer | Steam lobbies, lockstep; mismatched mod files desync silently; `+connect_lobby` launches | medium | launcher must sync mods before joining a lobby |
| Updates | Steam build 24670294; RUSE-Mod-Manager tracks 7 game builds since May | verified | design for updates anyway |
| Sound | `.ess` = Eugen's own variable-bitrate codec, no public decoder | verified | last priority |
| Steam builds | Eugen re-released R.U.S.E. in May 2026. Steam's default branch is the new build (this PC: `public`, build 24670294); the `compat` beta branch keeps the old modding-era build, which every community mod targets | verified (wiki, `ruse detect`) | our mods build from whatever the player has installed; the launcher shows the branch |
| Terrain editing | another modder has height edits, re-meshing and brushes working in-game: the gameplay ground and the camera floor (`.kdt`) change with both `.tms` meshes | reported, with screenshots | the Studio's terrain editor (MT) builds on it; our `.tms` and `.tmst` writers are lossless |
| New units | a copy shows in the build menu with its own name (C6d), and is built and fights in a skirmish (C7, 2026-09-29); the wiki's crash report doesn't apply to our method | verified | new units are usable |

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
| core | the six packs in `Data\PC\<rev>\`, loaded by fixed names | always |
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
- **Instances:** one modded copy for the whole PC, `D:\RUSE-Instances\Modded game\` on the game's drive (hard links
  need the same volume), built by Play and Test in game of both apps (the owner, 2026-10-02: one copy, not one per
  mod set); the copies older versions made per set or mod are leftovers the troubleshooter clears. A Play with the
  same mods (every file), game build and app as the copy's last build, and the copy as that build left it, starts it
  with no build; a build takes the old copy's unchanged files as they are (`rusemod.instance`, 2026-10-04).
  - Big read-only packs are hard-linked.
  - Small files the game might write (ini, logs) are copied.
  - Rebuilt packs are real files.
  - `steam_appid.txt` lets RUSE.exe start from that folder.
  - `rusemod-copy.json` records what the copy was built from and how each file got there, written last.

  Tools never write into a hard-linked file; they replace it. Several instances can sit side by side.
- **Launch/join:** Steam-compatible launch; `+connect_lobby <id>` when joining a lobby (checked in M3).
- **Runtime extender: on hold (2026-09-29).** The public platform works only through data files and never changes
  or loads into the game's program. That's the owner's rule, not Eugen's (Eugen has never said the program can't be
  edited): program work happens in the private repo, where it may be used for editing game files and mods.
  China stays as a real 8th nation (owner): the route without program changes is being worked out.

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
  the PC's one modded copy (`RUSE-Instances\Modded game`) and starts the game with the engine's own code (`rusemod.play`,
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
| 1 | Core language | Python 3.11+ with type hints | runs inside Blender; same language as community tools; fastest for reading file formats; AI-friendly | C#/.NET, Rust |
| 2 | UI stack | Web UI (TypeScript, three.js for 3D) in a desktop window (pywebview), served by the local service. **Confirmed by the owner 2026-09-28.** v0.1 uses plain JavaScript with no build step, and pywebview's bridge instead of a separate service; TypeScript once the screens grow | best 3D and UI ecosystem; one UI codebase for Launcher and Studio; runs on Linux/Deck | Qt / PySide6 |
| 3 | Runtime extender | **On hold (2026-09-29):** data files only; nothing changes or loads into the game's program | the owner's rule: program work stays in the private repo (Eugen has never said the program can't be edited); keeps public mods safe to share | a program add-on |
| 4 | Deployment | Modded instances via hard links | never touch the Steam install; mod sets side by side | in-place swap with backups (fallback) |
| 5 | Mod identity | Engine export paths + owner paths + selectors | stable across updates, human-readable | indices (.rmod `index_map`) |
| 6 | Source format | NDF-style text + CSV + standard asset formats | familiar to Eugen modders (WARNO/SD2 use text NDF); git-friendly | JSON / YAML |
| 7 | Determinism | Fingerprint over canonical content, bundled runtime, fixed ordering | lockstep multiplayer | hashes of raw bytes only |
| 8 | License | **GPL-3.0 (owner, 2026-09-30, night; MIT before).** LittleGroove's RUSE-Mod-Manager engine is GPLv3 and the apps ship it (decision 26), so the whole program is GPL-3.0. GPL-3.0, MIT, BSD and Apache-2.0 code can be reused with credit | the apps can ship the engine every community mod needs | MIT (until 2026-09-30) |
| 9 | Packaging & install | Nuitka + Inno Setup, built by GitHub Actions: one installer per app (decision 22). **Built 2026-09-29** (`installers/`): each app becomes a program folder (not Nuitka's onefile: it's installed anyway, starts faster, and antivirus programs trust it more), checks itself, and is wrapped by Inno Setup; per-user install, no admin rights. Unsigned until the first public release, so Windows' SmartScreen warns once | faster start and fewer antivirus false positives than PyInstaller | PyInstaller, Briefcase |
| 10 | Updates | **Built 2026-09-29 (owner: "auto update for apps"):** each app asks GitHub Releases for its newer release on start (`rusemod.update`); Update downloads the installer, checks its SHA-256 against both GitHub's value and the release notes' before running it, installs silently for this user and starts the app again. From the repo it says to `git pull` | no framework needed on top of the installers we have; nothing runs unchecked | Velopack, tufup; manual downloads |
| 11 | Modpack / lockfile | Modrinth `.mrpack` shape (`files[]` with path, hashes, download mirrors, size; `dependencies`) | proven, tiny packs, host-anywhere | our own format |
| 12 | Mod hosting | GitHub Releases now; Thunderstore once real mods exist; CurseForge last (needs a proxy server) | cheapest path that still scales | CurseForge first |
| 13 | Code signing | deferred to first public release; Azure Trusted Signing, then free SignPath | costs money; no instant trust anyway | sign from day one |
| 14 | Mod conflicts | Fixed load order; every pair of operations has a defined result (error, warning or note); math is exact and rounds once, half away from zero | predictable, identical on every PC | last mod wins, nothing else |
| 15 | Shared data in clones | A clone copies only what its source owns; editing shared data through one unit needs `own` or `shared` | no silent changes to other units | silent shared edits |
| 16 | Join codes | Game build + mod ids + versions + fingerprint; a published mod version never changes | about half the length of a full lockfile, checked end to end | the whole compressed lockfile |
| 17 | Extra-pack test | Moved up to M2 as check C3 | without it, every new unit name rebuilds the 2.3 GB ZZ_Win.dat | test in M5/M6 |
| 18 | Mod language details | A `final` pass; `when mod` blocks; WARNO's spellings; readable text keys | proven in Factorio, KSP ModuleManager and WARNO ([RESEARCH.md](RESEARCH.md) §5) | our own spellings, made-up hash keys |
| 19 | New nations | A real 8th nation, China, for RUSE 2.0. **China stays** (owner, 2026-09-29): it's not negotiable, and no faction is ever given up. The data side comes first: a test with an 8th entry wherever the data has 7 (M10). RUSE 2.0 itself is developed privately and shown to Eugen before release (owner, 2026-09-29); this public platform stays data-only (ADR 3) | RUSE 2.0 wants a real nation, not a renamed one | China takes over one of the 7 slots (**rejected**: it loses a faction) |
| 20 | Testing multiplayer alone | Solo tests S1–S2 (L6) until there's a second player; one real 2-PC match before the first public release | the owner has no second player yet; most of the risk (same build everywhere, the join flow) can be tested on one PC | wait for a friend |
| 21 | Display language in the tools | The game's own names are the default everywhere (mods use them); every modder can pick any of the game's ten languages for the tools, property names and unit names. Owner's call, 2026-09-28 | the community is international; no one language forced on modders | English by default |
| 22 | Apps | Two separate apps on one engine: **RUSE Launcher** (players: finds the game, loads mods, starts the game) and **RUSE Studio** (modders: the unit editor, later maps and models). Neither needs the other; each has its own window, start command and, later, installer. The Studio keeps its own "Test in game". Owner's call, 2026-09-29 | players get a small, simple app; modders get the full tools; each can change without breaking the other | one app with a modding mode |
| 23 | Script entries for new units | A new unit needs its own entry in the game's compiled Python unit list (`parametres/classes.xyz`, FORMATS §5); the build adds it. **Owner's call, 2026-09-28, with safety rules:** (1) mods can never contain scripts, and the launcher refuses any mod that ships script files; (2) the build only writes this one fixed kind of entry, from checked data (a name of letters, digits and `_`, and a path to a unit in the mod itself), and never compiles text; (3) the generated script is checked to contain only the allowed instructions and names before it's written; mods stay pinned by fingerprint; (4) custom game modes (M9) get their own design (a safe mission language, not raw Python) | without the entry the game ignores new units; code the game runs is the one thing a shared mod could abuse (a remote-code-execution risk for every player) | reuse the few spare hidden units (data only); no new units |
| 24 | What comes next | **The terrain editor in the Studio (MT, §7). Owner's call, 2026-09-29.** Terrain editing belongs to the Studio; the launcher stays a player app. The Studio shows a map in 3D, modders shape it with brushes, and "Test in game" builds it | no public tool edits terrain (RUSE-Mod-Manager doesn't); maps come first for the owner; another modder has proven in-game what has to change, so the risk is known | the launcher's v0.2 first; models first |
| 25 | Knowledge from other modders | What others share guides our own code (LittleGroove's engine is the one exception, decision 26). What we verify ourselves goes into FORMATS.md, credited the way they want. Their notes stay private, and nothing about the game's program is ever published | trust, and a clean license | copy their code; publish their notes |
| 26 | .rmod mods | **Owner's call, 2026-09-29:** LittleGroove's RUSE-Mod-Manager engine (`src/ruse_mod_engine`) applies .rmod mods in our builds (`rusemod.rmod`): in memory onto the game's packs, then written into the modded copy (never the install); .rmod mods first, our mods on top; a mod made for another build is moved with his version maps. The launcher adds a .rmod as it is. A .rmod may replace the game's own scripts (`.xyz`, `.ipk`), with a warning in the build report; programs are still refused | every community mod works in the launcher as it is | convert every .rmod to our format first (`tools/rmod_to_mod.py`, kept for editing them) |

## 7. Roadmap

Estimates are in sessions like today's. Every milestone ends with something usable.

| Milestone | Deliverables | Exit criteria | Est. | Risk |
|---|---|---|---|---|
| **M0 Foundations** ✅ | repo, docs; EDAT + NDF read/write; whole-game byte-identical check (38 archives, 2,176 NDF files); modded-instance launch | **done 2026-09-28** (C1, C2 passed) | — | — |
| **M1 Core tools** | combined file view + index (L2) ✅ (cloud session; the PC runs it); `.dic` r/w ✅ and `ruse` CLI basics ✅ (cloud session); scenario / AI-layer / capture-zone readers (our own code, informed by [LITTLEGROOVE_STUDY.md](LITTLEGROOVE_STUDY.md)) | every shipped file of these types round-trips byte-identically | 2–4 (was 4–6) | low |
| **M1.5 Frontier tests** | ~~re-encode one `TGU1` tile and one `.tms`; read one SPK section table~~ **Folded into MT (2026-09-29):** the `.tms` and `.tmst` writers are lossless on every map; the mesa test is dropped (it changed only the visual mesh, and the gameplay ground must change too); the tile tests (mirror, checker) move into MT | — | — | — |
| **MT Terrain editor (Studio)**: next (decision 24) | **T1** the gameplay ground and the camera floor (`.kdt`) read and written, lossless on every map, and still right after their parts move; **T2** height edits that keep the ground, the camera floor and both `.tms` meshes in step, with patch bounds and water lists updated; **T3** terrain edits in a mod (brush strokes, applied the same way on every PC), built into the map's pack in the modded copy; **T4** the Studio's map view in 3D with brushes (hill, raise, lower, crater, plateau, flatten, smooth, a two-click ramp), Undo, Start over and "Test in game" (code done and merged 2026-09-29, pull requests #6, #7 and #8; the in-game hill check comes next); **T5** finer edits (re-meshing), lakes drained or filled, ground textures (plain tiles work in-game, 2026-09-29) | a modder raises a hill in the Studio and presses "Test in game": it's drawn near and far, units drive up it, orders and the camera work, trees and roads follow | 5–8 | medium (done in-game by another modder) |
| **M2 Mod system slice** | package v1; `.rndf` reader ✅, rules engine ✅, load order ✅, fingerprint + join codes ✅ (cloud session); the adapter between game files and the engine; `.rmod` import; extra-pack mount test (C3); instances already proven by C2 | the **pipeline** works end-to-end: a throwaway value tweak + 1 cloned unit (reused visuals) builds, loads in-game and matches in a 2-PC test (until there's a second player, the solo tests S1–S2 in L6 stand in; the 2-PC test comes before the first public release). This proves the tool, not a balance mod | 2–4 (was 4–6) | medium |
| **M3 Launcher v1** | Steam auto-detect ✅ (`ruse detect`), the window ✅ (v0.1: game status, mod sets, Play; its own app, `ruse_launcher`), one-click install into instances, modpacks, join codes; also installs the `.rmod` mods players already have, combinable and without patching the live install | first public alpha on GitHub, ModDB, Nexus | 3–5 | low |
| **M4 Studio v1** | content browser ✅ and unit view ✅ (v0.1, with the language selector), property editor ✅ (v0.2: numbers, in place, saved as a mod, Play), unit editor; clone **any** class with its **own** visuals, wired into menus, upgrades and AI; validation, diff/rebase | a non-programmer builds a new unit | 5–8 | low–medium |
| **M5 Textures & icons** | TGV r/w (terrain tiles: plain ZIPO tiles work in-game, so no `TGU1` encoder is needed there), UI icon/flag pipeline | retextured unit with its own icon in-game | 3–5 | medium |
| **M6 Maps I** | map cloning, scenario editor, capture-zone compiler, AI layers, island maps on existing terrain | a new map listed and playable in multiplayer | 4–6 (was 5–8: formats now understood) | medium |
| **M7 Models** | SPK → glTF, Blender bridge, glTF → SPK (static, then skinned/animated). A first for R.U.S.E. | a new vehicle model in-game | 6–12 | high |
| **M8 Terrain / new maps** | builds on MT: terrain textures, heightmap import, maps from scratch, scenery, movement and AI data (`mapinfo.win`), tropical scenery set | a new island map built from a heightmap | 6–12 (was 8–15+) | high |
| **M9 Scripting** | `.xyz` scripts read and compiled with a real CPython 2.5.1 (known route), mission/mode scripting | a new game mode (e.g. Island Defense) | 3–6 (was 4–8) | medium |
| **M10 China (8th nation)** | **China stays** (owner, 2026-09-29). Step 1 (done): `tools/nation_scan.py` counts every per-nation structure in the data. Step 2: a modded copy with an 8th entry wherever the data has 7: does the game offer an 8th nation? RUSE 2.0 itself is developed privately (decision 19) | China can be picked in a skirmish, with its own flag and units | unknown | high |
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

**Plan revision 2026-09-29 (evening), Fable sessions under a tighter limit:** §10 now orders cheap, certain
steps (new units from the Studio's window, mod sets in the launcher) before the terrain editor's reverse
engineering, which waits for DomesticNukes' notes; polish and the later milestones are parked until asked; the
passed checks C3–C6 and the session history moved to [LOG.md](LOG.md) so a session reads less.

### M0 checks (only two up front; everything else is checked when a milestone needs it)
| Check | Question | Needs you? |
|---|---|---|
| C1 | Does rewriting `everything.cpp` unchanged come out byte-identical? This decodes TOPO. | no |
| C2 | Does RUSE.exe run from a hard-linked instance with `steam_appid.txt`? It creates files outside the install; the install itself is not changed. | yes (run the game) |

Checked later, when needed: joining a lobby via `+connect_lobby` (M3). Mounting an extra pack from NDF data moved up
to **M2** (decided 2026-09-28): without it, every new unit name costs a 2.3 GB rebuild (L5).

### C3–C7: all passed
The extra map pack (C3), a text mod through the pipeline (C4), a new unit in the build menu (C5) and a unit with
its own name (C6) passed in-game on 2026-09-28; C7 (the copy is built and fights) on 2026-09-29. Their procedures
and results are in [LOG.md](LOG.md) §1.

## 8. Risks

| Risk | Impact | Mitigation / early warning |
|---|---|---|
| TOPO / NDF writer fidelity | can't add objects | C1 first; byte-identical gate |
| Instance launch fails | must touch the install | C2 first. Fallback: in-place swap with journal + backup (players), full copy (dev) |
| ~~Map-pack header checksum enforced and unknown~~ | — | retired: it's a random GUID, not a hash (FORMATS §6) |
| An 8th nation may not be possible through data | China waits | the data test first (M10 step 2); RUSE 2.0 is developed privately and shown to Eugen (decision 19). No swap: the owner keeps all 7 factions |
| ~~New units crash when built~~ | — | retired: C7 passed (2026-09-29), the copy was built and fought |
| Two game builds (Steam's default vs the `compat` branch) | community mods only run on `compat` | our mods build from the installed game; the launcher shows the branch; imported pre-built mods are marked with their build |
| Terrain edits break the game (crash, refused orders) | no terrain editor | follow the rules proven in-game (the meshes change together, moved parts relocated, bounds widened); each step checked in-game on one map before the Studio offers it |
| SPK model format complexity | no new models | export first; static meshes before skinned ones |
| Terrain can't be written | no new maps / islands | reading is solved elsewhere, writing is not: M1.5 tests re-encoding early; M8 sized by the result |
| Python 2.5 toolchain | no new scripts | route known: compile with a real CPython 2.5.1 (a download, so your OK first), and read them with it |
| Game updates | mods and tools break | per-build registry, rebase, CI on fixtures |
| Non-determinism across PCs, or mismatched mods (the game doesn't detect desyncs) | ruined matches | join codes are the only guard: the launcher refuses a mismatch before joining; canonical fingerprints, bundled runtime, 2-PC tests |
| Community split | low adoption | `.rmod` import/export; talk to LittleGroove and Prolution; publish everywhere |
| Legal | takedown | ship no game files; ask Eugen for an OK |
| Malicious mods | user harm | scripts only from the index or with consent; signed releases; no native code from peers |
| Small team (you + AI) | work stalls | docs, ADRs, tests, open source, contributor guide |
| WebGL unstable in the embedded webview | 3D map/model viewer blocked | prototype a three.js scene in pywebview early (cheap spike) |
| Antivirus / SmartScreen distrust of the installer | players scared off (**seen 2026-09-28:** Chrome called the first test build "dangerous"; the file was verified clean) | Nuitka; players download GitHub Releases, not test builds (`release.yml`); in-app updates so a browser only sees the first download; false-alarm reports per release; winget / Microsoft Store later; signing at first public release (installers/README.md "Browser warnings") |
| Publishing Eugen-owned content (RUSE-Mod-Manager reset its public history "for Eugen Systems compliance") | takedown | `.gitignore` blocks game files; never commit extracted assets or decoded game scripts; check before each push |
| Reinventing formats others already decoded | wasted credits | study RUSE-Mod-Manager's approach first ([LITTLEGROOVE_STUDY.md](LITTLEGROOVE_STUDY.md)); write our own, or since the switch to GPL-3.0 reuse GPL-3.0 code with credit |

## 9. Open decisions

1. Working name. Ideas: *RUSE Reforged*, *OpenRUSE*, *RUSE Forever* (a nod to FAF).
2. ~~License~~ **Decided: GPL-3.0** (owner, 2026-09-30, night; MIT from 2026-09-28): the apps ship LittleGroove's
   GPLv3 engine (decision 26). Our own readers were written before the switch and copy none of his code.
3. ~~GitHub account/org and repo, project folder, git~~ **Done:** github.com/sneadtristen6/R.U.S.E-2.0-Project.
4. ~~UI stack~~ **Decided (owner, 2026-09-28): web-style** (ADR 2). The launcher v0.1 is built that way.
5. Outreach timing. Recommended: LittleGroove now (align on `.rmod` import/export), Eugen after the M2 demo.
6. Which unit to clone as the M2 test (suggestion: a US infantry unit, for Pacific later). **C5 uses the M4 Sherman**:
   a tank is easy to spot in its menu, and C5 only tests the pipeline. Infantry can follow once C5 passes.
7. A second player for the 2-PC tests (L6), needed before the first public release: a second Steam account with its
   own copy on another PC, or a community volunteer. Until then the solo tests S1–S2 stand in.

## 10. Now

**Shorter sessions (from 2026-09-29).** The sessions run on Claude Fable 5.1 under a tighter usage limit, so each
one is shorter. Rules:
- **One goal per session**, and it ends with something usable: a release, a passed in-game check, or a decision
  written down. Anything found on the way goes into [LOG.md](LOG.md), not into the session.
- **Cheap and certain first.** Work the engine already does (new units, mod sets) ships before work on
  file layouts nobody has decoded yet. The uncertain part of the terrain editor (the `.kdt` codecs) waits for DomesticNukes'
  published research and our exchange; we crack it ourselves only if that falls through.
- **Agents: only with the owner's "go agents" for that launch** (2026-10-01, after a night that spent far too many
  tokens; a hook enforces it). Replies stay short.
- **No heredocs:** a hook (`~/.claude/hooks/no_heredoc.py`, on since 2026-09-30) refuses them in the shell; scripts
  and commit messages go in files (`git commit -F <file>`). A mistake that repeats gets a guard like this one, not
  another rule.
- **At most one in-game test per session**, batched: one modded copy, the owner runs it once and reports.
- **Reading budget:** a session reads this section, [TASKS.md](TASKS.md) if it is a cloud session, the memory
  notes and the files it changes. History is in
  LOG.md and is read only when a step needs it.
- **Polish waits.** "Look like R.U.S.E." (finer tiles up close, the map's lighting and sky, trees, buildings and
  roads) comes after the editor edits terrain, not before.

**Now (updated 2026-10-04, afternoon): start here.** **Studio 0.9.6 and Launcher 0.4.6: import your own 3D models**
(being readied; pushed on the owner's word, with RUSE MAIN's speed work in one release branch). **Import model** on a
new unit's page fits a .3ds or .glb to the unit it copies (rusemod.modelin, rusemod.unitmodel; MOD_FORMAT §7
`files/models`); T35 PASSED: an M1 Abrams beside the Sherman, built and turning its turret, after three faults the
game showed (a card only in the menu packs, pictures outside a texture group, one texture level too many: all
fixed, FORMATS §8). The Abrams is a mod in Ruse-Mods (model by ags, downloadfree3d.com, credited; pushed after the
Launcher release). Also: Test in game / Play start at once when nothing changed, Delete map, Erase the whole map,
and three new ones shipped untested at the owner's word (roads on reshaped ground, riverbed fill, erase's layout).
Next for models: tracks and wheels on their bones, the gun on its bones (recoil, flash at the new muzzle), its own
wreck, Bring back of a shape changed in Blender; then the picture-to-model idea (§14 item 14).

**Before (2026-10-04, morning):** **Studio 0.9.5 and Launcher 0.4.5: units get a look of their own** (the
owner's big update, everything from the sessions of 2026-10-03 and 04 that passed in the game; LOG.md and the release
notes). Firsts seen in the game: a unit repainted by a mod (T23) and in Blender (T27), a build-menu card made in the
Studio (T31), a second Sherman with a 3D model of its own (T32, T33: model packs that grow need the id the game
checks, now written), a mission of our own played to a victory (T22, a test builder), a new Operation (T17). Also:
another nation's units in campaign chapters and Operations, the map's edge following flattened mountains (T18),
erased buildings opening their ground (T25), Map Paint (early). Waiting: T34 (a new unit's own card). Kept out until
tested in the game: RUSE Guard (fair play, in the private repository, switched off), the road model following
reshaped ground, the riverbed mend. Next: making models in the Studio (a new unit with a model of its own, then new
shapes from Blender; the owner: the Japanese fort or tunnel).

**Before (2026-10-03, night):** **Studio 0.9.4 and Launcher 0.4.4 are out.** Roads were cracked
in 0.9.0 / 0.4.0 (T12 passed: a new road looks like the map's own from high up and up close; the story in
[ROADS.md](ROADS.md)). The owner: 0.9.x is the alpha, patch releases with plain notes; **1.0 is the launch**, with
videos and announcements of everything made during the alpha (new maps among the first). Fixes may go out before an
in-game test ("can be tested by a player later"), said so in the notes.

In 0.9.4 / 0.4.4:
- **New maps** (`rusemod.newmap`, the Studio's **Duplicate map**): a copy of any BATTLES map with a name of its own,
  listed in BATTLES next to it, edited like any map; the Studio opens it with the shipped map's files under the copy's
  own edits. **Seen in the game:** T15b (Blitz Twin flattened, a hill in the middle: it plays its own ground) and T16
  (101 new maps listed at once, two played). Known: flattening a map's edge mountains left a wall there (fixed after
  0.9.4: the edge moves and its curtain follows, T18 waiting); names over about 35 characters are cut off in the
  menus; copies of other maps than Blitz built, not yet played; a new map in multiplayer between two PCs not yet tried.
- Found 2026-10-03 (the all-maps edge check): on Alpha, Chess Mate, Compass Rose, Edge and Hurtgen, a stroke that
  moves a whole part of the gameplay ground across a height split of the file's top tree leaves that part on the
  wrong side of it (clicks there may miss); Blitz has no such split. Being looked into.
- Issue #15's bugs: maps open about 4 times faster the second time, the Unit mod and Map changes menus told apart,
  sides and zones explained, and a fourth version number for small fixes between releases.

Next (the owner, 2026-10-03: "test the bug when flattening ... then we got to figure out water. Then lastly, adding a
nation"): T18 passed (the edge fix); water, and "how a navy map would work"; a new nation. From T18 and after it, in
his words:
- the old riverbed and coastal cliffs on a flattened map "tearing ... when you're approaching it" (TESTS T18);
- "when the ground's flat and there's no river", the bridge could become a road;
- "the buildings bug where the units go around it ... would kind of fuck up new maps ... you can expand on the maps,
  but you can't really make it new" (units still steer round where removed buildings stood: fresh movement data, part
  of blank maps).
- Roads (the owner, 2026-10-03): "need a way to delete roads you've created. It's similar to being able to erase
  buildings and the buildings not be there for pathfinding", and "also just general roads on the map will go to the
  map editor so that way you can have a completely blank slate". Two steps: (1) a Delete tool in Roads & bridges that
  takes one of the mod's own roads out of roads.toml (today only Undo, the last one): everything the build makes from
  it goes with it (the paint, the far road, the stickers, the supply route, its bridges); (2) the map's own roads
  removable too, for a blank map: their supply routes out of the road network, their painted strip repainted
  (Map Paint's Texture), their far road model and stickers taken away, units' movement left as it is. Step 2 is
  research first: what each of those files holds for a shipped road, then a test copy.
- The Launcher (the owner, 2026-10-03): "embed into the launcher a crash log finder. So that way we can find game
  crashes and help fix bugs from their PC ... That way nobody ever has the code we have." The game's crash reporter
  leaves a folder per crash (CrashRpt) on the player's PC: the Launcher lists them (when, which mods were on, the
  modded copy's fingerprint), and with the player's OK packs one into a zip they send us (Discord or the bug report),
  never sent by itself. What's in them is read on our side with our own tools; the Launcher only finds and packs.
- "a script to have artillery fire wherever we want ... lets add this for everything that shoots a range slider in
  units tab": (1) the game's mission scripts have an artillery strike at a position (`DescriptorFrappeArtillerie`:
  Group or ToutesLesArtilleries, Position; 508 uses in the shipped missions), a bomber strike at a position
  (`DescriptorBombardement`, 333), a firing-range limit (`DescriptorUnitGroupPorteeDeTirLimitee`: Distance) and a
  rate-of-fire change (`DescriptorModifieCadenceTir`): a Scenario tool "artillery strike here" the build turns into
  checked script code, with our own scenarios' scripting; (2) a range slider on everything that shoots in the Units
  tab (each weapon's PorteeMaximale, today a number field).
  The owner's answer (2026-10-03): "keep it to like artillery fire. So like whatever unit has the artillery
  theoretically could. So if an infantry unit had in the future a mortar, you could [strike with] it". So the tool
  offers the units that carry flag 1 (artillerie: indirect fire; it works on any unit, tested), a mod's own ones
  too, and nothing is tied to a unit's type. In the shipped script the strike gives the game the group, the spot and
  ToutesLesArtilleries (all of them, or not); the game aims at an invisible aim point it places at the spot
  (`Descriptor_Unit_CibleArtillerie`, flags 18, 20, 42, 55, 57). Not tested: which units actually fire at it (a
  flag-1 infantry unit with a long-range ammo first). The tool waits for our scenarios' scripting.
  The owner (2026-10-03): "I definitely want the scripts. To have it fire directly on the spot for campaigns and
  operations." How a shipped mission does it (M02_Tunisie chapter 1 has 26): a named spot in the scenario (a `Name`
  design item, `TagPosition('PV1_GER_Art_2_strike_6')`), a unit group (`VariableUnitGroup(UnitList=[TagUnit(<a
  spawn's Name>), ...])`), the strike (`DescriptorFrappeArtillerie`) inside a sequence (`DescriptorPlayEffetAfterWait`
  = wait N seconds, then the strike); the launch descriptor lists every tag (`TagList`) and group (`PostInit`) and
  runs one root action (`EffetMap`, a `DescriptorSimultaneous` in Anzio). So a strike can be added at the end of any
  mission script: the tags and groups added to those lists, the root wrapped with the strikes beside it. The plan:
  1. T19: one such strike added by hand to Anzio (four Priests, "all guns" and "nearest gun only"); waiting for the
     owner's test.
  2. The build: a fixed, checked template (names of letters, digits and `_`, numbers, true/false; assembled like the
     new units' entries, rusemod.pyscript, with nothing else allowed), appended to the scenario's own script.
  3. The Studio's Scenario tab: "Artillery strike": click the spot, pick the guns (the scenario's units that carry
     flag 1, a mod's own too), all of them or the nearest, and when (after N seconds first; later: when a zone is
     entered or an objective is done).
  Found on the way: the platform finds a mission's script by the scenario's file name, which misses two Operations
  whose scenario cluster names another folder (Anzio and Seelow: `Scripting_challenge`), so their sides aren't read;
  the cluster's own folder is the right one (part of step 2).
- Done 2026-10-03: the Scenario's Add unit "how many" is a slider from 1 to 10 (a player asked for 3, 5, 7, 9).
- Done 2026-10-03 ("the range slider should go in now"): every range box (an ammo's max and min range) has a slider
  beside it and says about how far that is in metres (about 260 game units to a metre); each weapon on a unit's page
  has a Range line too. When other units fire the same ammo, the modder picks "only this unit" (the weapon gets its
  own copy of the ammo, Ammo_Range_<unit>_<n>, carrying the mod's other changes to it) or "all N units that fire
  this ammo"; Undo puts the game's range back and drops a copy it no longer needs (api.set_range). Tooltips in the
  ten languages. Also: the top-tree height splits above; a new map's
own menu picture; a new map in multiplayer between two PCs; blank maps (flat ground, no water, one ground texture,
empty scenery, fresh movement and sectors).

In 0.9.3 / 0.4.3 (the owner's detail-loading tests on his test2 copy of M03_Italie):
- **Everything a mod places is drawn from far** (rusemod.visibility): the game's decor levels reach 20,000 (close),
  100,000 (middle) and 500,000+ (far) from the camera, and most props have a close or middle mode alone; a mod's
  objects of such a type use a copy of it that serves the far pass too, the map's own unchanged. Shared mode entries
  are copied, never changed; copied buildings stay solid; all 706 types that get a copy checked through the engine.
  **Seen in the game:** placed rocks at every height.
- **New roads through woods** painted at every level like the map's own (seen in the game), and a road can keep its
  trees (`keep_trees`, the Studio's box): fainter and greyer in a wood (seen in the game).
- **Props, trees and buildings named in all ten languages** (rusemod.scenerynames_lang), switching with the
  language button.
- **Builds about three times faster** (306 to about 90 seconds for the owner's test2): a map's road look and the
  shipped tiles it paints on are measured once and kept (`cache/build` in the platform's folder), and clones with no
  ids skip the id scan.

Next: the texture flicker on a new road as the camera turns (the owner: minor); faster builds still (the engine's
copy of the game and its index, the ground tiles' writing); a campaign chapter's sectors; the tester's lake
screenshot (ask what's wrong first); more detailed graphics in the editor (the owner: "can be pushed later").

*In 0.9.2 / 0.4.2 (released 2026-10-03; from a tester's M03_Italie campaign mod; not yet seen in the game unless said):*
- **Bridges for new roads on every map with bridges:** the stone bridges' floors (one wide strip end to end, up to
  about 21,000 across) are found too; before, only the metal bridges' narrow ones, on 9 of the 29 maps.
- **Road ends snap only at the ends,** to a placed bridge first; a box turns snapping off.
- **The names a player knows** for units and buildings, and the game's own line for each.
- **Who gets it?** lists the scenario's own sides from its mission (rusemod.missions); the player's side (0) is
  allowed in the build, and only a side the mission doesn't list is warned.
- **Scenery from far:** a new road's pieces out in the open went in front of a block's far-view list where the full
  list's node splits before its own first entry (the top block of M03_Italie and 8 other maps, 113 blocks in all):
  from far the game drew the pieces instead of the map's blocks, and new props, with no far-listed block left to
  wrap, were hung on a grass decal and showed only up close (the tester's rocks). Fixed, with a guard; the owner's
  in-game check of detail loading is next.
- **Zones as borders on the ground** (Stellaris' way: a clear line, a see-through tint inside); a "Zones' fill"
  slider in place of the zones' height.

*In 0.9.1 / 0.4.1 (released 2026-10-03):*
- **Drag anything on the map, no tool needed:** starting points, supply depots, spawned units and opening cameras
  are grabbed and moved live, the way the camera ring already was. Depots and HQs still stick to roads while dragged
  (with the toggle on).
- **New map icons by kind:** a soldier, a tank, a truck for depots, a plane, guns, a clearly marked HQ, the armor
  base and the airfield different, and every bunker its own (anti-tank, machine gun, anti-aircraft, artillery, fort,
  lookout post). Buildings are square badges, units round ones, decoys dashed.
- **Show or hide each kind** in the Scenario tray (starts, cameras, depots, buildings, units, zones, towns), and an
  **icon size** slider; icons shrink as the camera pulls out, so they aren't bulky from high up. Kept per PC. Nothing
  added to the top-left toolbar (the owner: it's bulky enough).
- **Windows' installed apps list** shows the version actually installed (it showed the first installer's).
- **Choose your language** on the first start of both apps (and once for players updating), with the game's language
  in Steam marked; the language is a button at the top, no longer in Settings (the owner: a French player stayed on
  the code names, not knowing the apps speak French).
- **The game's own unit types** under Ground, Infantry and Air in the Studio's unit list (Light Tank, Heavy Bomber,
  Armored Recon...), on each unit's line and in the map's Add unit list.

**The bug list** ([issue #15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/issues/15)), still open: the Mod
and Map menus look the same; "New map..." isn't clear; the Studio is slow to start; a map is slow to open; removing
the map's own roads (step 17); team spawns on BATTLES maps and the rule tests (game rules: tested in the game first).

*Before 0.9 (2026-10-02):* **Studio 0.8.1 and Launcher 0.3.1** (smaller releases, the owner: "lets not
go .9 yet smaller releases"), from the branch `allnations`. Units from another nation work (tested in the game
2026-10-02: a German Tiger and Ju 87 and a Japanese Zero and Chi-Ha for the US, with no German or Japanese player).
Roads up close are still open. In them: both apps in R.U.S.E.'s blues with the owner's artwork as logos; the launcher's sidebar in two tabs
(the whole library reachable); the Studio's toolbar in groups (Ground & water, Cover & movement, Roads & bridges,
Buildings, Props & trees, Erase, Scenario, Check); the Erase tool; and, if batch 4 passes, new roads drawn up close
(the map's road model, step 5), units from another nation (step 6) and new maps in BATTLES (step 8). After the
release: steps 14-17 below, the owner's next asks.

Out in 0.8.0 / 0.3.0: the troubleshooter and the clean-game backup in both apps; every unit flag explained; square
cover; the road fix and all the audit's fixes (LOG.md, 2026-10-01); units following new roads; the mod list at
[sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods) (the launcher's Supported mods); the Studio's
Open and Forest brushes, Bridges dock and Check this map; erase areas (`[[erase]]`) with cleared woods units use and
don't hide in; placed objects on the ground at any size; cover painted in place on the 8 maps that aren't square.

*Testing plan* (steps and commands in [TESTS.md](TESTS.md); one game start each):

| Test | Who | Decides | State |
|---|---|---|---|
| **T8 Bridges:** units (a tank, then infantry) and a supply route cross the new D-Day bridges | owner, `D:\RUSE-Instances\bridges` | bridges done, or what to fix | **passed 2026-10-01, 04:27**: tanks, infantry and a supply truck cross on the decks, the men at the deck's height (the floor's aprons, `934d414`) |
| **T12 New roads up close:** a new road's texture still shows with the camera close to the ground | owner, `D:\RUSE-Instances\bridges` | the road fix (step 1) | **passed** (owner, probe 5, 2026-10-02: the new road shows up close like the map's own, built into 0.9.0; failed every batch before that, see ROADS.md) |
| **T9 A road over an old bridge:** the old one gone, units cross on the new one | owner | the replace rule | after T8 (the new deck goes into the old bridge's local map; the old floor and its aprons go) |
| **T10 Read-only game folder:** Test in game after updating | the player who reported it | the fix | waiting for him |
| **T11 Launcher 0.2.11:** the update is offered, Play works | owner | — | — |
| **T13 A unit from another nation's factory:** it shows and fights in a skirmish with no player of its own nation | owner | the unit packs fix | batch 4 (the force-load of batch 1 crashed) |

*Next steps* (in order):
1. **New roads up close: DONE in 0.9.0 (T12 passed, 2026-10-02; how in [ROADS.md](ROADS.md)).** The history below
   is kept for the record. A new road's texture showed from afar but disappeared near the camera. The fix of the morning (new scenery blocks
   marked as holding road pieces, each piece given what the map's own pieces have; LOG.md) didn't change that in
   the game. Open, listed as a known issue of 0.8.0; the next session on roads starts from the game's own road
   pieces up close (exe first). Never call it working before T12 passes.
2. **The audit (done 2026-10-01).** All five areas (map info, ground, scenery, units, scenario) were checked against
   what the game does with every file the build writes, and each rule became a check in the build with a test (LOG.md
   has every fix). Being finished on branches, merged before the release:
   - new roads in the movement graphs' crossings, so units follow them and not only supply trucks (`feat/crossings`);
   - a unit from another nation's factory: the build makes the game load that nation's models (`feat/nations`, T13);
   - the launcher's **Supported mods** (the mod list with tick boxes, cheats unticked and apart, a "Choose your mods"
     step on first run) and the Studio's **Share your mod** screen (how to add a mod to the list and become a
     contributor) (`feat/modlist`).
3. **Release** (done 2026-10-01): Studio 0.8.0 and Launcher 0.3.0, the owner's numbers and his go after batch 3.

*After the release* (planned 2026-10-01, evening; in order, cheap and certain first, one game start per test batch,
the test spots beside the player's HQ with a top-down map):
4. **Test batches** (done 2026-10-01, TESTS.md batches 1-3): what failed was fixed and checked again. T9 (a road over
   an old bridge) and T14 (D-Day for 8 players: the lobby) ride along in the next batch.
5. **New roads drawn up close (T12), first. Built 2026-10-01 (night), in-game test in batch 4.** Up close the game
   doesn't draw the scenery's road pieces at all: it draws the map's **road model** (`output\staticmeshes.spkpc`,
   model `road`, FORMATS.md), made from them by the map's tools. `rusemod.roadstrips` adds a new road to it as
   strips in the map's own look (all 28 maps that have one rebuild byte for byte). The history below is why the
   earlier fixes changed nothing.
   The release's one known issue, and the owner's most repeated report.
   The build already marks the new blocks and the path to them as holding road pieces, and a simulation of the game's
   walk reaches every piece, yet the game still drops a new road near the camera. Steps:
   1. find what the close view asks of a road piece beyond the scenery tree (how the game draws it, first);
   2. a probe copy: one of the map's own road pieces copied into a new block exactly as it is, beside a new road. If
      the copy draws up close, our pieces' own data is the cause; if it doesn't, the new block is;
   3. what the game's own road blocks always have and ours don't (the far list, the trailing word, the boxes);
   4. a guard test that simulates the close-up road pass after every build, then one test batch.
   Asked DomesticNukes too (his scenery notes; the shared repo's issue #11).
6. **Units from another nation that work** (owner, 2026-10-01: "have a tiger on the USA ... a special scenario where
   you captured a tiger"). Making the game load that nation's models in every match crashed it in T13 (a German Ju 87
   copy for the US crashed the game when its gunner was set up: its model wasn't ready for it), so that is off
   (`build.FORCE_LOAD`). **Built** (branch `feat/spk`, 2026-10-01): the build copies the unit's models (meshes,
   skeletons, animations, texture stand-ins) into the skirmish packs of the nation it now belongs to, so its matches
   load them with their own units, and a spawned unit's into the common packs (`rusemod.unitpacks`; every pack writes
   back byte for byte, every unit copied into every nation's packs reads back the same). In-game test in batch 4: a
   Ju 87 and a Tiger for the US (T13), and German Tigers spawned on D-Day.
7. **A community mod to look at:** Rastapopoulos' "Total War research fix" (ModDB, 2026-09-30; he offered it to us):
   in Total War mode, research the next era's units yourself instead of getting them free. If it works with our build,
   it goes on the mod list (sneadtristen6/Ruse-Mods); nothing of it goes into the apps unless it brings code we need.
   Downloading it waits for the owner's go.
8. **The Studio's Erase tool and new maps in the game's menus:** both merged into `next` (2026-10-01, night). A new
   map is a copy of a shipped one under its own name and pack (`maps/<NewName>/map.toml`, `copy_of`), listed in
   BATTLES. **Seen in the game 2026-10-03** (T15b: Blitz Twin flattened plays its own ground; T16: 101 new maps
   listed and played). The Studio makes one with **Duplicate map** and opens it like any map (0.9.4). Still to do: a
   menu picture of its own, the cliff left where a map's edge mountains are flattened, and a copy tried in a
   multiplayer game between two PCs.
9. **Small ones, when a session has room:** the town-names mod (names readable from any height, §14) on the mod list;
   the players' wishlist done in 0.8.0 (Open and Forest brushes, Bridges dock, Check this map) needs nothing more.
10. **A4 Remove scenery:** the build's side is out in 0.8.0 (`[[erase]]` circles, copy on write; a cleared wood is
   opened to units and loses its cover); the Studio's Erase tool is on the branch `feat/eraseui`. Measured 2026-09-30: only 0.2-0.3% of a map's trees (D-Day 11.6 million, Blitz 3.9 million) sit in blocks
   placed once, the only ones `bury_objects` can sink one by one; the rest are in blocks the map places many times.
   So erasing needs a block copied for the erased spot (copy on write, down from the top block) or whole placed
   patches sunk; which one is the first decision of A4. The same work builds the top block's tree again, which also
   reaches new objects in open ground far from the map's scenery (the audit's one open scenery case, LOG.md).
11. **A city template** (the wishlist): save a group of buildings, roads and cover, and stamp it on a map. Needs A4.
12. **Road kinds** (owner, 2026-09-30: "make a rule in editor where some roads can be in forests and not allow
   tanks"): a forest track (infantry only, out of the supply network) or a road that opens the woods to vehicles
   along it; which is the default is the owner's call.
13. **A5 Ruse areas, A6 ground painting** (the forest-floor texture for the forest brush), **A7 finer ground**
   (re-meshing): the smallest ground brush is 1% of the map's width (cover and block go four times finer), and below
   one cell of the gameplay ground a brush does nothing, so **smaller brushes** and finer ground up close come
   with A7.

*After 0.9.0 / 0.4.0* (the owner, 2026-10-01, night: "after this update and these bugs are fixed"; in this order):
14. **What it takes to make a new map**, not only a copy of a shipped one: what a map pack must hold for the game to
    load it, what we can already write, what we can't yet, and the first small new map.
15. **Units on that map that aren't just triangles:** the Studio's map view draws starting units and spawns as their
    real 3D models.
16. **3D unit models in the Units section, for every type of model** (ground, air, infantry, buildings), not only the
    ones shown today.
17. **Erase grows** (the owner: "that's the future of that tool", why it has its own tile): the map's own buildings
    (opened to units, not only out of sight), roads (painted ground, the road model, the supply network), shrubs and
    rocks, each its own pick.
    - **Removing the map's own roads** (owner, 2026-10-02: "you should be able to remove existing roads, and that's
      something we still don't know how to do"). A road shows in several places, and only some are known: the supply
      network (we write it), the road model drawn from high up (we write it), the painted ground; the textured road
      with its dashed line seen up close was the open question, answered by 0.9 (ROADS.md: the map's own asphalt
      and edge pieces in the scenery, which new roads now get too). So each place can now get its "take out"
      (not built, not tested); then a test copy shows the road gone from far and near, and trucks no longer using it.

*Planned (owner, 2026-09-30):* **A10**, at least 8 players on a map (D-Day first), past 8 tried later.

*Written down for later, not scheduled (owner, 2026-10-02: "look into how the ui would fit 10"):* **A10b, a lobby
for 10 players.** Tried in the game (rule test B): a map set to 10 shows "Number of players 10" in the lobby, but the
lobby has 8 seats and the match starts with 8, no crash. What's known and what isn't:
- The lobby is a screen file (the outgame `.gfx`). Its seat layouts are 2 teams of 2, 2 teams of 4, and one grid of
  4 rows x 2 columns (8 seats, used for free-for-all); the end-game score screen also holds at most 8 players. So
  more seats means a changed lobby screen and a changed end-game screen, not only map data.
- The game fills the seats and sends each player's team, slot, colour and nation to the screen; the screen only
  shows them and sends back clicks ("add AI to team t, slot s"). Whether the game itself accepts a 9th and 10th
  seat, and gives them a colour, a team and a starting point, is **not known**: the screen stops at 8 before that can
  be seen.
- What the work would be: (1) a 10-seat layout in the lobby screen (5 rows x 2, or 2 teams of 5); (2) the end-game
  screen's 8 rows to 10; (3) a test copy that seats 10 (AIs) and starts the match; (4) only if that works, the build
  and the Studio allow up to 10 (`players.PLAYERS_MOST`), and Strategists or D-Day get starting points for teams 9
  and 10. Colours past 8 and the AI's limits are unknown until (3).
- Changing the game's screen files is outside "data only"; this belongs with the RUSE 2.0 side (§11) unless it can
  be done as a mod file.

*Written down for later, not scheduled (owner, 2026-10-02: "log those features for later"):* **LittleGroove's map
editor tools the Studio doesn't have yet.** His RUSE-Mod-Manager map editor (GPL-3.0) gave 0.8.3 its road snapping,
the opening camera and the camera ring. Still to bring over, from going through his editor's tools:
- Remove the map's own scenario items (the Studio removes only the spawns and starts a mod adds): a new mod entry.
- A placed item's details: a depot's trucks, its side, its turn.
- Reshape sectors (zones) by dragging their corners (his sector and capture-zone mesh editing).
- Toggles for country flags and side numbers on the icons (the icon size slider and show/hide per kind are on
  `main` since 2026-10-03).
- Which game modes a map offers (1v1, 2v2, free-for-all), and making a new scenario.

*Asked for 1.0 (owner, 2026-10-01):* a R.U.S.E. 2.0 image when the game starts. Waits for the owner's artwork.

*The owner's ideas for later:* §12 (maps), §14 (the rest, e.g. game UI mods), §11 (RUSE 2.0's game).

*Open, the owner's to decide* (ideas, not decisions): "two tabs open" in the map builder; bridges for chokepoint maps.

*After the Studio is done* (owner, 2026-09-30, night: "we need to finish studio"): DomesticNukes' split of the parts
of R.U.S.E. nobody has worked on yet (the private repo's `notes/open-tasks-split-domesticnukes-2026-09-30.md`). Ours:
unit animations and skeletons (`skeleton_*.spk`); explosion and bomb effects (the FX bank); the menu screens that
aren't mapped yet and how menus animate; what `div_map.tgv_pc` is for; what reads `mapinfo.win`'s marker records;
how supply trucks cross water (probably the road network); how many AI personalities the lobby offers. His side
takes the data-side ones (sky reflections, cut nations and units, capturable vehicles, Eugen's AI test map, AI
production, Korsun's unused operations, flags 31 and 60).

**Order** (sessions are estimates for the shorter sessions):

| # | Step | Ships | Sessions | Needs |
|---|---|---|---|---|
| 1 | **Ask DomesticNukes** for the three `.kdt` encodings (index buffer, triangle lists, subtree node codes), format notes only; ours (framing, vertices, the normal word) go into FORMATS.md with the agreed credit | a message; FORMATS §6 (**done 2026-09-29**) | 0 (owner) | — |
| 2 | **Units in the Studio:** "New unit" from a unit's page (copy, name in all languages, price, menu and nation), on the engine that already does it (C6d, C7) (**done 2026-09-29**, pull request #1; the owner's in-game test and the 0.5.0 release follow) | Studio 0.5 | 1–2 | — |
| 3 | **Launcher v0.2:** mod sets made in the window (new, edit, rename, duplicate, delete), "Add a mod file…", drag-and-drop; players never see a file (**released as Launcher 0.2.0 on 2026-09-29**, the owner's call before T7, with ".rmod" files, sharing and importing a load order, and self-update; T7 still checks it) | Launcher 0.2, first public alpha | 2 | — |
| 4 | **Terrain editor** T1–T4 (§7 MT): `.kdt` read and written losslessly, height edits that keep the ground, the camera floor and both meshes in step, brushes in the Maps view, "Test in game" (**T2–T4 code done 2026-09-29**, branches `cloud/terrain-brushes` and `cloud/studio-brushes`: brushes, all four files in step, terrain edits in mods and in the build, and the brushes in the Studio's Maps view; the in-game hill check is next) | Studio 0.6 | 4–6 with the notes; +2–4 without | step 1 |
| 5 | **Browse mods:** a GitHub repo as the index, a launcher tab that installs from it (L6) (**code done 2026-09-29**, pull request `cloud/browse-mods`; the owner creates `sneadtristen6/Ruse-Mods` and tests) | Launcher 0.3 | 1–2 | step 3 |
| 6 | **China, step 2** (M10): a modded copy with an 8th entry wherever the data has 7; does the game offer it? | an answer | 1 (owner at the game) | — |
| 7 | **Join codes in the launcher** (MOD_FORMAT §12) and the 2-PC test (L6) | Launcher 0.4 | 1–2 + a second player | step 3 |

**Who does what (from 2026-09-29; DomesticNukes' part is a proposal until he agrees):**

| Who | Does | Next |
|---|---|---|
| **The owner** | plays the in-game tests below (one game start each, screenshots), makes the calls, talks to the community and DomesticNukes, makes GitHub repos and adds collaborators | the tests below; `sneadtristen6/Ruse-Mods` for Browse mods; add DomesticNukes to the shared repo when he sends his GitHub name |
| **DomesticNukes and his Claude** | what he knows best: the `.kdt` index buffers, triangle lists and tree nodes (needed to re-cut the ground, T5); scenery (trees, buildings, roads: the scenery file and its models); new unit textures and models (M5, M7); script know-how for the Pacific (beach landings, air drops; RUSE 2.0, private). Both Claudes review each other's notes. **A request from the owner (2026-09-29):** could he take on the in-game tests queued below ("The owner's tests"), if he can? They are the bottleneck: each one decides a release | the in-game tests below, if he can take them; then scenery |
| **The PC session** (has the game) | everything that needs game files: checks the cloud's work on the real maps, builds the test copies, merges, releases, the China data test | fix and re-check the terrain editor on every map; build the hill copy; releases after the tests |
| **The cloud sessions** (no game) | code and docs from [TASKS.md](TASKS.md): join codes (E), Studio follow-ups (F), painting the ground, water that follows the ground (§12) | E |

**Terrain work waits for DomesticNukes (owner, 2026-09-29):** no more terrain-engine changes and no hill test
until he has caught up and reviewed. Open for him, found by the PC session's check of the cloud's work:
1. The `.kdt` MainNode holds height limits per part of the tree (read as 8-byte records: split nodes, one leaf per
   subtree, many one-sided height planes; the root repeats the file's z range). The engine moves points but can't
   update these, and any raise at the test spot on Two Islands goes above them. A hill test can't tell a bad edit
   from a stale limit until they're understood; a flatten that stays inside every touched part's range would.
2. `.tms` normals are recomputed per cell, so points on a cell border get two different normals after an edit (a
   possible lighting seam); the test hill sits on a cell border.
3. Fixed and pushed: the terrain check compared ground points with the wrong point where the mesh stacks several at
   one spot (cliffs); the engine's normal lookup had the same flaw. All 32 maps pass.
4. Community mods: five hold absolute values that reveal the game's tables (speed, range, altitude, health); four
   could be relative (`*=`). Descriptions repeat the originals' "confirmed in-game" claims. The 17 mods that had no
   author listed are DomesticNukes' (owner, 2026-09-29). His FNAT mod was taken out of the public repo (kept in the
   private repo) until he agrees; it remains in the public repo's history.

**The owner's tests** (DomesticNukes, if he can take them; else the owner). Every step is in
[TESTS.md](TESTS.md), with the commands to build each modded copy from this repo on any PC. Stop at the first failure
and report what happened.
1. **T1 Placing scenery:** a ring of water towers and oaks on Blitz. Decides Studio 0.6, with T6.
2. **T2 Water brushes** (DomesticNukes' pull request #11): a new lake, and a drained one, on Blitz. Decides the merge.
3. **T3 Community `.rmod` mods** through our build: five that each change something different. Passed so far: Dev
   Toolkit with 10x Artillery Price (owner, 2026-09-29).
4. **T4 The hill** (terrain brushes, pull request #6). Decides whether the game accepts ground we move.
5. **T5 A new unit** made in the Studio (a Sherman copy). Decides Studio 0.5.
6. **T6 Placing scenery from the Studio.**
7. **T7 The launcher:** mod sets, sharing and importing a load order. Launcher 0.2.0 is already out (the owner's
   call); T7 checks it and the next version's self-update. First report (DomesticNukes, 2026-09-29): a set of 12
   `.rmod` mods built with 0 errors and the game started, then failed; his suspect is No Fog of War (every unit's
   vision set to 3,000,000). Next: the same set without it.
8. Later: **Browse mods** (after `sneadtristen6/Ruse-Mods` exists) and **China** (M10 step 2).

**Parked until asked:** the "look like R.U.S.E." polish and terrain T5; icons and unit textures (M5); map
cloning and scenarios (M6); models (M7); new maps from heightmaps (M8); scripting (M9); sound (M11).

**Standing:**
- **Two repos (owner, 2026-09-29):** `R.U.S.E-2.0-Project` (public; Ruse-Mod-Platform until 2026-09-30) releases only the Studio and the launcher.
  `R.U.S.E-2.0-Project-Shared` (private: the owner, DomesticNukes, the cloud sessions) holds the same code plus a
  `private/` folder (the research handover, community guides) and RUSE 2.0, which is never released publicly
  (decision 19). Code goes to the public `main`; the shared repo's `main` mirrors it; private work stays there.
- **DomesticNukes** is credited as "DomesticNukes and his Claude" (decision 25).
- **Cloud sessions** take their tasks from [TASKS.md](TASKS.md) and open pull requests; the PC session tests
  in-game, merges and releases.
- **GitHub `main` is the record.** Push when done; keep README's "Current stage", this section and LOG.md current.
- Open decisions in §9: the name, outreach timing, a second player.

**Where we stand (2026-09-30):** Launcher 0.2.3 (mod clashes refused with the reason, Put in best order, .rmod
mods) and Studio 0.5.2 (new units, ammo and flags with the shot following the ammo, real 3D models, map names,
brushes with Level, Water and Drain, the Place tool, keys you can change) are out; DomesticNukes' water brushes (#11)
merged after his in-game pass. **Open, found in the game (owner, 2026-09-30):** ground moved by the brushes refuses
move orders, the camera falls through it, trees stay at the old height, and big edits show steps. Cause and cure are
in DomesticNukes' notes (private `notes/terrain-editing-what-we-fixed-…`): the engine still moves all four files
separately and leaves the `.kdt` height limits stale.

**Where we stand (2026-09-30, evening):** Launcher 0.2.6 and Studio 0.6.8 are out. Passed in the game today:
terrain brushes (hill, pit, level; orders and trees right), a moved starting point, **painted cover hides infantry**
(Studio 0.6.8: Cover, Uncover and Town brushes), and **placed buildings show** once their new block wraps a block the
top block draws from far (FORMATS §6; ships as Studio 0.6.9 after the all-maps check). Found in the game: the
cover grid's "blocked" layer doesn't stop tanks, and units walk through placed buildings: movement lives in
`mapinfo.win`'s other buffers. Buffer 0 is the **road network** (its 1,263 points on Blitz lie exactly on the
scenery's road curves).

**Roadmap from here (owner, 2026-09-30: "plan ahead").** Phases in order; within one, steps in order. Each step
ends with one in-game test (batched, one game start) and a release. Sessions are estimates.

*Phase A: the map maker, on the shipped maps* (the owner's current focus: Cities: Skylines-style tools)
| # | Step | Needs | Sessions |
|---|---|---|---|
| A1 | Studio 0.6.9: placed objects that show (the far-view wrapper), after the all-maps check | — | done, releasing |
| A2 | **Movement: passed in the game (2026-09-30).** `mapinfo.win` buffers 1-2 are the infantry and vehicle navigation graphs (circles units plan through, linked where they meet, with a spatial index; water and off-map ground uncovered), read and written byte-identical (`rusemod.nav`). Mods block ground (`maps/<map>/movement.toml`), the freed ground is filled back with new circles, and every placed building is solid: on Blitz units go around a blocked pit and between placed towers, and a building placed in the game on edited ground works. The Studio side ships in 0.7.0 (Block brushes, a Solid toggle on placed buildings, the Where units go view), with the tools moved to a Cities: Skylines-style bar along the bottom in the game's HUD look | — | done |
| A3 | **Roads, Cities: Skylines style:** draw the map's roads in the view (done 2026-09-30: the Roads box, the scenery's road pieces decoded as Béziers); the road network (buffer 0) decoded, written back byte-identical on all 33 maps, and `RoadNet.add_road` (points along the curve, joined to the nearest road, index rebuilt; not tried in the game yet). Found: the roads a player sees are painted into the ground's texture tiles, the scenery's pieces lie on them, so a visible new road also needs ground painting (A6). **Proven in the game (2026-09-30): supply routes follow a network-only road** (the depot's route preview took the new shortcut). Still to test: vehicles' speed on it, and whether pieces draw anything; a road tool (click points, a curve follows, ends snap to roads) that writes the scenery's road pieces and the road network, and clears the trees along it (needs A4). Test: a new road, drawn? faster? | A2, A4 | 2-3 |
| A4 | **Remove scenery:** take out the map's own trees, props and buildings (an Erase brush; roads and towns use it) | — | 1 |
| A5 | **Ruse areas** (owner, 2026-09-30: "editing ruse areas for new maps and existing, along with how many per"): the areas ruses are played on, the scenario's `AREA` records (reader done): draw, move, reshape, add, remove and name them, on the shipped maps and on new maps (B1-B2). **How many ruses an area takes:** two, and no data value holds it (found 2026-09-30, §11), so the public apps can't change it; it's on RUSE 2.0's private list, unless a data value turns up. Test: a new area shows on the ruse map and takes a ruse | — | 1-2 |
| A6 | **Ground painting:** grass, sand, rock, road texture with a brush (plain tiles work in-game) | — | 1-2 |
| A7 | **Re-meshing:** finer ground only where brushes need it (adaptive, so no lag: far mesh and gameplay ground stay coarse); a warning when a brush is steeper than the mesh can show | DomesticNukes' index-buffer notes | 2-3 |
| A8 | Spawn checks: which camp is the player in a skirmish, and does a skirmish honour unit spawns; formations (Studio 0.7.1): do the units face the way the formation does | — | 0 (one test) |
| A9 | *Idea (owner, 2026-09-30):* units drawn as their real 3D models in the map view (a tank as a tank, infantry as soldiers) instead of markers, like the buildings already are | — | 1-2 |
| A10 | **More players on a map, at least 8** (owner, 2026-09-30: "add at least limit to 8; if it can go higher, try later on, just plan for it"). A map's player count is data: `NbPlayers` in its `TMultiMapInfo` (`misc/globals.cpp`; the 30 online maps use 2, 3, 4, 6 or 8, and MP23-MP24 are 8 already), its size group `CategoryId` (seen: 1 for 3-4 players, 2 for 6, 3 for 8), its team layouts (`DispoMulti2Teams` / `3Teams` / `FFA`), and a starting point per player in its scenario (D-Day's 3v3 has six); the "(6)" in its name is only text. So: raise a shipped map (D-Day first) to 8, and let new maps (B1) pick theirs: the Studio gets **Add starting point** (it moves them now; each has an alliance, a camera and a warm-up path), and the build sets the count, the group, the layouts and the name in ten languages. Test: 8 slots in the lobby, and an 8-player game starts with every player on their own starting point. **Built 2026-09-30:** `maps/<map>/map.toml` (`players`), `[[start]]` in scenario.toml (a teammate's point copied, at the ground's height), `rusemod.players` (the count, group, 4v4 game type and name set; a count the scenario can't seat refused), the Studio's **Add starting point** tool and **Players** row; the D-Day copy `D:\RUSE-Instances\eight` is ready (TESTS.md T14). **Past 8: later.** If no data value holds the limit, it's RUSE 2.0's (private); if one does, both apps | — | 1-2 |

*Phase B: new maps* (M6, M8)
| # | Step | Needs | Sessions |
|---|---|---|---|
| B1 | **Clone a map** under a new name and register it (map list, skirmish menu, name in ten languages, menu picture); "New map…" in the Studio. Test: it's listed and plays | — | 2 |
| B2 | A blank start (flattened copy), map sizes, **heightmap import**, and the new map's **ruse areas** (A5's tool) | B1, A5, A7 | 2-3 |
| B3 | The AI on edited maps: the 51×51 AI grid (`mapinfo.win`'s tail) and the other AI layers follow the new ground, roads and towns. Test: the AI plays the new map | A2 | 2 |
| B4 | Multiplayer check of a new map between two PCs (join codes, C4 below) | B1, C4 | 1 + a second player |
| B5 | The Pacific look: a tropical scenery set from the game's own assets (Italy, Tunisia), then new ones (M5, M7) | B1 | 2+ |

*Phase C: players and multiplayer* (M3)
| # | Step | Needs | Sessions |
|---|---|---|---|
| C0 | **Community (done 2026-09-30):** the wiki is a field manual (`docs/wiki`, pushed to the GitHub wiki by hand); Discussions has the Welcome and Roadmap posts (`docs/community`, posted and updated by `tools/post_discussions.py` through the owner's `gh`), a bug-report form (`.github/DISCUSSION_TEMPLATE`); both apps open the wiki, Discussions and a pre-filled report (`rusemod.community`; paths without the user name). Left for the owner: the categories (Help, Mods & maps, Bug reports) and the pins, on the website | — | done |
| C1 | **Browse mods:** the `sneadtristen6/Ruse-Mods` index repo (owner), install with dependencies in one click (code done). Until then, public mods live in Discussions > Mods & maps; the how-to is the wiki's Export and share | the repo | 1 |
| C2 | Modpacks as their own instance (RUSE 2.0 in one click); one-click back to vanilla | C1 | 1-2 |
| C3 | Studio: "Publish mod" to the index (a pull request made for the modder) | C1 | 1 |
| C4 | **Join codes** in the launcher, and the 2-PC test | a second player | 1-2 |
| C5 | Trust: code signing, a first public release on ModDB and Nexus; outreach (LittleGroove, Eugen) | C1-C4 | 1 + owner |
| C6 | **Self-checks, like a mod manager's** (owner: "a lot of self-checks built into this, like CurseForge has"). Done: files read back before saving, the mod check (every file as the build reads it, Set aside, map folders named by title renamed; `rusemod.modcheck`, shared), run by the launcher too when a mod is added (after 0.2.7). Next: a mod file recognized by its SHA-256 against the index whatever its name or folder, duplicate mod ids, a mod made on another game build, a zip nested two folders deep. How CurseForge, Nexus, ModDB and Thunderstore do it: `docs/RESEARCH-mod-platforms.md` | — | 1 |
| C7 | **Clean game backup** (owner, 2026-09-30: "backup restore clean version of game in studio or launcher ... that way files stay clean"). Our apps never change the game's folder, but other mod managers and hand edits do, and every modded copy then carries their changes. **Built 2026-09-30** (`rusemod.backup`, Settings in both apps): Make backup (a full copy of the game folder, never hard links, with a manifest of sizes, dates and SHA-256, in `RUSE-Backup\<build>` on the game's drive; one per build, made in `.partial` and renamed when complete, free space checked first), Check game files (changed, missing, added; fast by size and date, or every byte), Restore clean files (asks first, listing what changes; copies the files back, moves added ones into `RUSE-Backup\set-aside-<date>`, never deletes; refused while R.U.S.E. runs, while a Play or a Test in game builds, and when Steam has updated the game since), and Verify with Steam (`steam://validate/21970`). The only place either app writes into the game's own folder. Check on the PC: make a backup, change a file by hand, Check, Restore, then Play | — | built, not released |

*Phase D: the content tools* (M4, M5, M7, M9-M11)
| # | Step | Needs | Sessions |
|---|---|---|---|
| D1 | Studio v1: checks before a build (validation), rebasing mods across game updates | — | 2 |
| D2 | **Icons, flags and textures** (M5): unit cards, flags, retextured units | — | 3-5 |
| D3 | **China, step 2** (M10): an 8th entry wherever the data has 7; does the game offer it? | — | 1 (one test) |
| D4 | **Models** (M7): SPK to glTF and back, static then animated (with DomesticNukes) | D2 | 6-12 |
| D5 | **Scripting** (M9): compile Python 2.5 scripts; game modes (Island Defense) | a CPython 2.5.1 download (owner's OK) | 3-6 |
| D6 | Sound (M11), last | — | 4-10 |

*Phase E: content* (after the tools it needs): **RUSE 2.0** (private: balance, units, China) grows alongside
Phases A-D; **Pacific Island Defense** needs B, D2, D4 and D5.

**Waiting on others:** DomesticNukes (the `.kdt` index buffers for A7; scenery know-how for A3-A4; models for D4),
the owner (the in-game tests; the Ruse-Mods repo; a second player for C4 and B4; the name, outreach timing).

**Where we stood (2026-09-29):** C1–C7 passed (mods build from the installed game, load in-game, add texts and
new units that fight). Launcher v0.1 and Studio 0.4.1 are released (values edited in place, one box for a unit's
five per-date prices, the Maps view with each map's real ground in 3D). The terrain mesh and tile files read and
write losslessly, and plain tiles we write are drawn in-game. The `.kdt` gameplay ground reads and writes losslessly on every map (`rusemod.kdt`,
2026-09-29), and every part decodes and re-encodes, from DomesticNukes' notes (commit 39d7a76). A mod as one file (TASKS C): the Studio's "Export mod…" writes `<id>-<version>.rusemod`, the launcher installs it (merged 2026-09-29, not yet checked in-game). Community mods: `.rmod` files apply as they are through LittleGroove's engine (decision 26; a first mix passed in-game); the mods rebuilt in our format (`tools/rmod_to_mod.py`) are kept in the private shared repo until their authors agree. Scenery: every map's buildings, props and trees read, and mods add more (Studio Place tool). The apps update themselves from GitHub Releases. The in-game tests are in [TESTS.md](TESTS.md). Details: [LOG.md](LOG.md).

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

Whether new ruses are possible at all depends on whether ruses are in the game's data (check 1). Some rules
are known not to be in the data (the two ruses a sector takes, 2026-09-30: no data value holds it); those go on
RUSE 2.0's private list, to be handled together later, never through the public apps.

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
1. Are ruses in the data (one object per ruse)? (new ruses)
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

## 12. The map editor's direction, and map ideas parked (owner, 2026-09-29)

**Direction: shape maps the way Cities: Skylines does, only simpler.** A few brushes with a size and a strength
slider, painted straight onto the 3D ground, Undo, and one button to see it in the game. Nothing is set up in a
file. The first set (T4) is hill, raise, lower, crater, plateau, flatten and smooth, then the ramp (two clicks: the
ground slopes evenly between them, the way roads want it) and Start over (branch `cloud/ramp-tool`, 2026-09-29).
**The owner's order for what follows (2026-09-29): painting the ground** (sand, grass, rock, snow on the map's own
texture tiles; the game already draws tiles we write, so this rests on an in-game fact), **then water that follows
the ground** (T5). Scenery and roads come after the ground works in-game (M6, M8).

**Ideas parked, written down so they aren't lost. Nothing here is built or planned yet; the map editor comes first.**

1. **Strongpoints: buildings troops can hold.** Pre-made buildings like the game's armed ones (bunkers, forts), but
   infantry can go inside; on some maps they're indestructible and worth capturing, and units inside take less
   damage. What the data says so far: the game has armed buildings that shoot, and towns already hide infantry and
   make it tougher (PLAN §11), but no "troops go inside a building" mechanic has been found in the data, and the
   engine can't be given one (public code is data-only, decision 23). The closest buildable version: an
   indestructible armed building placed on a map, captured through the game's own capture rules (M6's capture-zone
   compiler, once it exists), with a town-style cover bonus around it. Whether a unit can be made "inside" (hidden and
   protected) is a check for later, not a promise.
2. **Caves, tunnels, trenches, an underground.** The ground is one surface: no overhangs, no second level, so real
   caves and tunnels aren't possible in this engine. Trenches can be dug today with the lower brush (a ditch), but
   the game's cover bonuses belong to forest and town zones, not to the shape of the ground, so a ditch is only a
   picture until a cover zone can be drawn on it (M6). A tunnel would have to be a gameplay trick (two connected
   points), and nothing in the data does that yet.
3. **An extended campaign with new scenes** (owner, 2026-10-03: "thinking a extended campaign with new scenes or
   something, idk just a thought"). New chapters after (or beside) the game's own, with cutscenes of their own. How
   the game does it: a chapter opens only when the one before it in its list is finished, and the first of a list is
   always open; a campaign is a chapter pack, and the menu reads every pack. So a campaign of our own (a new pack)
   should open at its first chapter (not tried yet). A copied chapter keeps the shipped chapter's cutscenes and
   dialog; new ones would need their own work.
4. **A navy map** (owner, 2026-10-03): a game mode like his YouTube channel's Crossing the T: carriers, battleships,
   destroyers and cruisers (no submarines); a wide-open sea with each side's harbour on a tiny island holding its
   supply depots, and a naval battle between them. Ships can't go on land (a blocker), they're slow, fire slowly,
   and need balancing across the game modes. What exists: the community Navy Mod adds a destroyer, a heavy cruiser
   and a battleship to every nation, but they drive on land; the game's movement data has ground for infantry and
   vehicles and treats water as closed to both, so whether ships can get water movement of their own is the first
   thing to find out (not known yet). Found 2026-10-03 (Iwo Jima research): the game itself ships a hidden US
   Battleship, Destroyer, Heavy Cruiser, LST and LCVP with their models, and its Salerno chapter places them on the
   sea and has them shell the shore. The owner (2026-10-03): a ship's wake, an animation behind a moving ship, for the
   Navy mod ("that's for another day"); the sea's textures and waves later.
5. **Scripted Operations and campaign missions with end goals** (owner, 2026-10-03: "scripted campaign and
   operation missions ... endgame goals, like Iwo Jima for the operation ... add new missions"). An Operation or a
   chapter of our own with its own mission: sides, goals ("take Mount Suribachi and hold it"), timed and triggered
   events (reinforcements, strikes, messages), a win and a loss, and for a campaign the next chapter. What's known
   (2026-10-03): the game's 45 shipped missions are lists of the game's own mission blocks (169 kinds in use: goals,
   timers, zone checks, orders, unit drops, victory and defeat), each mission with its own text file in every
   language; Prolution's Fortress Europa replaces a whole campaign mission and plays; LittleGroove's engine (in ours)
   has an Operation model with goal templates. **Seen in the game (T22, 2026-10-03):** a mission of ours in a folder
   of its own, on a new Operation: its own texts, popups, units it brings, a goal reached in a circle, an artillery
   strike, a second goal and the victory screen. Not tested yet: a campaign of our own opening at its first chapter,
   new spoken dialog, cutscenes; what makes a goal a main one rather than a bonus one.
6. **Iwo Jima, the showcase Operation** (owner, 2026-10-03: "start working on a potential map template of what Iwo
   Jima would look like. Scripting, that sort of thing for the operation", "this is going to be the showcase").
   His wishes: Mount Suribachi "very clear"; "the infamous bunkers that would have to be flamethrowered out";
   "tunnels ... a building or like quote unquote tunnel that like comes out of the trees, and they just like rush out
   of the ground"; and for maps in general: garrison orders, trenches, beach landings. Then: "it's too small ... I
   want it to be big ... work through the jungle and manage my units correctly in order to win ... waves of
   Japanese ... like it terrified those GIs. I want to capture that feeling", the fleet shelling, "maybe like a
   bombing run from an aircraft carrier" (a carrier and Navy planes: new models, the Blender work); and it must not
   look like D-Day ("I don't want to be able to load in and be like, oh, this is D-Day ... we might have to add a new
   tree, a jungle tree ... we really gotta be thinking about this"). A draft template
   (the map, the Operation phase by phase, what each piece rests on, the tests): [IWO_JIMA.md](IWO_JIMA.md). Nothing
   decided.

These go to §11 (RUSE 2.0 design notes) when they're taken up; until then this is the record.

## 13. Making a new map (design draft, 2026-09-30)

**What a map is, in files** (all read today; the checksums and layouts known):
- **Its pack** `Maps\PC\DataMap<Name>_v09.dat`: the drawn ground (`highdef.tms`, `lowdef.tms`, texture tiles), the
  gameplay ground and camera floor (`.kdt`), scenery (`save.boobspc`), water textures, the sight layer (`output.sdb`).
- **Its scenarios** in `DataMap_Win.dat` (`test\map\<name>\*.scenario`: zones, starting points, spawns, names), with
  `mapinfo.win` (the AI's grids and the movement graphs) and camera paths.
- **Its registration** in `ZZ_GladPatchableWin.dat`: a `TMapLoadInfo` in the map list (a GUID, the pack, its
  scenario clusters `genglad\patchable\scenario\<name>\<scenario>\clustermap` + `mapia`), and a menu entry
  (`TMultiMapInfo` for skirmish, `TChallengeMapInfo` for an Operation) with its name as a text key.

**Three levels, easiest first:**
1. **A new scenario on a shipped map** (a new skirmish layout or an Operation on Blitz's ground): clone a scenario
   under a new name and register it (LittleGroove's engine already does both: `scenario_gen.py`, and
   `registration.py`, proven in-game with his Overlord Operation), then edit it in the Studio: starting points,
   depots, spawned units (being built now), zones. Works with what exists.
2. **A new map from a shipped one's ground** (the main goal): copy a map's pack under a new name
   (`DataMap<New>_v09.dat`; new maps can ship their own pack, C3), register it, then reshape everything with the
   Studio: Start over and Level to flatten, brushes to sculpt (proven in-game 2026-09-30), water, scenery, the
   scenario. Missing pieces, in order: (a) cloning a pack and registering a new map (with its name in all ten
   languages and a menu picture): **built in the mod format and the build, 2026-10-01** (`maps/<New>/map.toml`
   `copy_of`, `rusemod.newmap`; every other map file edits the copy; all 31 BATTLES entries copy; **seen in the game
   2026-10-03**, T15b and T16: 101 new maps at once; the Studio's **Duplicate map** makes and opens one, 0.9.4);
   left: its own menu picture; (b) drawing zones (the
   sectors players capture); (c) ground painting (sand, grass,
   rock); (d) the movement graphs and AI grid in `mapinfo.win` following the new ground where it becomes
   impassable (hills are fine today: units drove up one; cliffs, new lakes and blocked valleys aren't); (e) the sight
   layer (`output.sdb`: forests and towns hiding units).
3. **A map from scratch** (a heightmap, any size): everything in 2, plus building the meshes, trees of the `.kdt`
   and texture tiles from nothing (M8). Only after 2 works.

**A blank canvas (research, 2026-10-01, night; the owner: "I want to make a new map", a blank one, and "like Cities:
Skylines, you start with that little notch... if that's how you have to do a map, that's fine").** Read from the game:
- **Sizes:** every map is a grid of cells of 327,680 map units (1.28 km): highdef 4×2 (Hurtgen) to 12×8 (D-Day), lowdef
  half as many cells of twice the size. Blitz is 4×4 (5.1 km). A map's settings name its size in a handful of values:
  `TTerrainGeometryLoader.NbCaseX/Y` (both loaders), `TWaterOnGPU.NbHighDefCaseX/Y` and `TCurrentMapInfo.NbCaseX/Y`
  (twice the cells), `MapSizeX/Y` and `AreaMaxX/Y` (map units), camera ranges; everything else in the 13 settings
  files is the theatre's look (lighting, water shading, sky, ambient sound).
- **Every pack holds the same 55 members** (ground meshes, texture pyramids, three `.kdt` trees, scenery, road model,
  sight layer, water-simulation pictures, sky cube, two overview PNGs); the map's other files are `mapinfo.win` (road
  network, two movement graphs, cover grid, AI grid), its scenarios (starting points, the **sectors**: Blitz's skirmish
  has 9 zone polygons), each scenario's bluff-zone `.kdt` (one subtree, 94 triangles on Blitz), camera paths, the
  minimaps and the theatre's packs in ZZ_Win.dat.
- **The plan, the owner's "starting tile":** blank canvases at the sizes the game ships (4×4 first), each made from a
  shipped map of that size and wiped: ground flat (the edits we do), water taken out (the mesh's under-water list
  rebuilt: to build), one ground texture (plain tiles, proven), an empty scenery file (to build), no roads (an empty
  network and road model: to build; does a map with no roads play?), movement graphs made fresh, open everywhere (to
  build from the graph writer), blank cover, AI and sight grids (formats known), sectors drawn new with their bluff
  tree (a tool to build; the tree writer exists for one subtree), starting points (the tool exists), registration
  (`rusemod.newmap`). The theatre's look (sky, light, sound, HQ models) comes with the starting map.
- **Any size** (e.g. 5×3) needs more from nothing: the ground mesh (its skirt and patch tables), the pyramids, the
  ground `.kdt` in many subtrees with a main tree over them, and every grid at the new size. Only if a size the game
  doesn't ship is wanted.
- **In-game unknowns** (one copy): a map with no roads at all (supply trucks), fresh movement graphs, new sectors
  (ruses apply there), a two-PC game.

**The Studio, for level 2:** "New map…" → pick the map to start from (its theatre: the trees, buildings and ground
textures available) and a name → a blank copy (flattened) opens in the map view → brushes, water, scenery,
scenario → "Test in game" plays it as a skirmish → Export shares it as one `.rusemod`, which carries the new pack.
Players get it through the launcher like any mod.

**Unknowns to check first (one game start each):** a copied pack under a new name loads as its own map; the menus
show a new skirmish entry (LittleGroove proved it for Operations); a map with its own GUID works in multiplayer
between two PCs with the mod. The first two are answered (2026-10-03, T15b and T16): a copied pack plays as its own
map, and the menus list new skirmish entries, 101 at once. Multiplayer between two PCs is still to try.

**The map tools, the way Cities: Skylines does them** (owner, 2026-09-30): click to lay things out, see them at
once, the game's rules follow. What the data says, and the order:
1. **Cover (where units hide), done in the build:** `maps/<map>/cover.toml` paints the cover (0x08) or blocked (0x04)
   layer of the map's grid in `mapinfo.win` (`rusemod.cover`, all 34 grids checked). Eugen drew these by hand (the
   editor set's forest and obstacle surfaces), so they don't follow the trees: a town or wood a mod adds gives cover
   only where it's painted. On Blitz, two thirds of the buildings stand on blocked cells and few on cover.
   In-game check waiting: `D:\RUSE-Instances\cover` (a cover patch 600 m east of player 1's HQ, ringed by water
   towers; a blocked patch 700 m further east). Then: a Cover brush in the Studio (paint, erase, see the grid).
2. **Town center:** pick buildings (or drag an area) and the Studio paints cover around them, a margin wide, so a
   placed town hides infantry like the game's own. Built on 1.
3. **Roads:** a road is a chain of curved pieces in the map's scenery (`save.boobspc` road items, 15 words: start
   point and direction, end point and direction, a road type 1/3/9, two fixed codes; 310 on Blitz). The tool: click
   points, a curve follows, ends snap to other roads; it clears the trees along it (removing scenery items: to build)
   and saves `maps/<map>/roads.toml`. Units have `SpeedBonusOnRoad`; whether the game finds roads from these pieces
   or from a road graph in `mapinfo.win` (its first buffer holds points) is the first in-game check: one new road
   on open ground, drawn? faster?
4. The rest follows the same way: zones (drawn sectors), ground painting, and every tool with click-and-see.

## 14. The owner's ideas for later (kept so none are lost)

The owner's standing ask (2026-10-01): every idea he has goes on a list, to be taken up later. **These are ideas,
not decisions or an order: the map editor comes first.** Map ideas are in §12, RUSE 2.0's game ideas in §11.

1. **Game UI mods (2026-10-01).** Change how the game looks and works on screen: the battle HUD (building, making
   units, managing them) and the main menu. Three layers, from cheapest:
   - **The look** is data: the menus are Flash screens drawn into texture tiles, one archive per screen (our tools
     open them; 428 tiles decoded), and the HUD's buttons, icons and flags are textures the data points to; every
     label is game text. A full reskin (new art, colours, a R.U.S.E. 2.0 menu, new icons) needs no code. The startup
     image (§10, asked for 1.0) is the same layer.
   - **How the HUD works** (which tabs and buttons, their order, what they do, hotkeys) is built by the game's own
     scripts. A shared mod of ours can't carry scripts (decision 23), so this would be a short list of safe changes
     the Studio offers (move, hide or add a button, a hotkey), turned by the build into checked script code, as it
     already does for new units' entries; or an `.rmod`, installed with a warning.
   - **How the menus move and behave** (their animation; the escape, end-of-game and controls screens) isn't mapped
     yet. A few parts aren't in the data at all (the two ruse slots on a sector's panel), out of a data mod's reach.
   First step when taken up: one study session (which archive and tiles make which screen, which script builds which
   part of the HUD), written up as what can be reskinned, what can be changed safely, and what can't.
2. **Town names you can read from far away (2026-10-01).** A mod that makes the map's town names big and visible
   from high up, so a town is an easy landmark ("the river 750 m south-east of Toulaville") without zooming in. The
   names are the scenarios' town labels (`LabelVille`); how far away they show and how big is to be found (likely the
   labels' display settings in the data). Handy for every test copy too.
3. **A showcase map to start with (2026-10-03).** One small 1v1 map, such as Centre of Gravity, made into a showcase
   mod: "this is how it works". The owner's YouTube video walks through it, the README gets a section about it, and
   the Studio offers it first ("Try this first, as seen in the video"), so a newcomer opens a working example
   instead of an empty mod.
4. **More detailed graphics in the Studio's map view (2026-10-03).** The owner: "it may not be possible, that's fine,
   that can be pushed later". Goes with "Polish waits" (§10).
5. **A compass (2026-10-03).** The owner can't tell north from east in the game or the Studio ("I have no way of
   telling which way is north"): a compass in the Studio's map view, and maybe one in the game through a UI mod.
6. **Changing how units look (2026-10-03).** The owner asked to think about the 3D unit models: editing units so
   they look different, and what that would look like for China. Steps, cheapest first: borrow another unit's model
   (already works: the Tiger and the Ju 87 given to the US); repaint (a unit's texture out as a picture, painted in
   any image editor or the Studio, written back as a new texture for that unit only); markings (a roundel, numbers,
   characters placed on the model); swapping parts between models; new models from Blender (M7). In the Studio: a
   "Look" tab on each unit, with its model turning in 3D. For China (§11): borrowed models repainted in Chinese
   uniform colours (the 88th Division keeps its German helmets), the Blue Sky with a White Sun on its planes and tanks.
   The owner also asked about new hats, uniforms and gun models (2026-10-03): uniforms are a repaint; a soldier's
   hat is part of his body model (another hat = borrow another nation's soldier, or edit the model); his gun is a
   separate piece of the model, so guns could be swapped between soldiers. T23 proved repaints load in the game.
   The owner's picture of it (2026-10-03): like creating a class in Call of Duty, in the Studio's Units tab: see the
   unit's model, click it, change its model, its paint, its parts. Blender itself can't run inside the Studio's
   window, but the Studio's 3D view (it already draws the game's models) could show the unit with slots (body from
   any nation, gun, paint, markings), and an "Edit in Blender" button could open the unit in Blender and take it
   back when saved. The owner chose to start with the Blender bridge (step 1: any unit out to Blender).
   After seeing the T-26 load in Blender (2026-10-03): "it's fine that Blender can't be in the studio", but the
   Studio should offer it: "want to make a new model? Here's the link to Blender", to add a new model seamlessly
   (a button that opens the unit in Blender, or a link to get Blender when it isn't installed).
   **Built 2026-10-03 (owner's go):** step 1 (`ruse export-model`) and step 2 with the Studio's buttons (Open in
   Blender, Bring back, Get Blender): mods repaint textures (MOD_FORMAT §7); passed in the game 2026-10-04 (TESTS T27: the Sherman wears its Blender paint); next there, the build-menu card picture.
   Next steps: a texture of China's own (a copy, so the Soviet T-26 keeps its paint), then model write-back (step 3).
7. **Formations when giving orders in game (2026-10-03).** The owner: choosing a shape for a group's move order
   should be as easy as the Studio's Add units tool (a shape, a preview under the pointer). What the game does today:
   a group sent to one point spreads into rows by unit type (tanks, infantry, AT guns, recon, AA, artillery), for
   most types rows 30 m apart, units 25 m apart, a row at most 200 m wide. Those numbers are game data
   (`FormationConstantes`), so a mod can change them now, for every order alike. A shape chosen per order (line,
   column, wedge, box, circle, as in the Studio; right-drag to set the front's width and direction) needs the game's
   own scripts: an `.rmod` or RUSE 2.0 (§11), not a shared mod (decision 23). Nothing tested in the game yet.
   Owner, later the same day: make it a mod (with the script warning) until RUSE 2.0, aimed at the next patch. The
   game's right-drag already makes its rectangle formation, so shapes go on keys: 1 a V, 2 a square, and so on.
8. **Sound, music and campaign scenes (2026-10-04).** The owner: new music for R.U.S.E. 2.0 and its Iwo Jima
   Operation, "just to add variation to the game"; maybe different sounds for buildings and units; and how campaign
   scenes could be added. What the data shows (read 2026-10-04, nothing tested in game; FORMATS §9):
   - **Music** is a list of named tracks (`$/Misc/Musics/*`, 34), each one file. The battle music picks from three
     playlists (calm, battle, ruse) driven by what happens in the fight; a mission can also play any track by name
     (`PlayMusic`, used 229 times in Eugen's missions). New tracks = a new sound file + a new name + added to a
     playlist or played by a mission. Needs our own sound encoder (the format is known; a community mod already
     replaced the menu music with a stereo song).
   - **Unit sounds:** engines are per unit (run and idle sounds, shared by kind: light, medium, heavy tank, jeep,
     truck, planes, infantry); a unit can be given its own. Weapon sounds belong to the shot's effect, voices to the
     nation and unit type (8 voice sets ship, a Japanese one among them).
   - **Building sounds:** none of their own today (one shared construction loop, capture/loss jingles). The scenery's
     animals play idle sound loops, a route to try for a building.
   - **Map ambience** is one setting per map (Swamps has its own swamp ambience, Two Islands a volcano sound).
   - **Campaign scenes**, three kinds: a full-screen film, a small picture-in-picture film during a mission (both
     WebM videos played by name), and in-game scenes made of a camera path, black bars, dialogue and music (pure
     mission data). Blender can make the films in the game's exact video format.

## 15. Painting the ground, brush types, and more detail (FIRM, owner 2026-10-03)

The owner, 2026-10-03, after T18 (a flattened riverbed shows the map's painted ravine lying flat): "implement painting
in the studio as a firm idea. Probably make like an editing tab or like a drawing tab and include the erase tool with
it ... your fine line, your brush tool ... there's no square like placement tool ... a certain angle on a beach or a
rock ... a color wheel palette and all that sort of stuff. You'll have to really think about it." Then: "Brush should be
included in every tool ... a couple of different Brush types. In every tool that has a brush." And on detail:
"increasing the totals game resolution ... how many textures or tiles ... are on the map ... to allow for better
shading, better textures, better graphics"; "how are object textures stored and can you double those?"

**What the ground is drawn from** (read 2026-10-03; FORMATS §6-7): the ground shader takes the map's picture pyramid
(`uniBigTextureTeinte`: the highdef and lowdef `.tmst` tiles, 512 × 512 DXT1, 160 map units = 0.6 m a pixel at the
finest level on Blitz), the whole-map pictures `terrain.png` / `terrainwithunit.png` where tiles aren't loaded, the
map's close-up picture (`uniDiversityMap`, `div_map.tgv_pc`, DXT5, about 5 m a pixel) and the shadows. There is no list
of shared detail textures in the shader settings: what a map looks like up close is its own painted pictures. The
game draws tiles we write (plain DXT1, proven 2026-09-29; roads painted into them, proven 2026-09-30). The riverbed and
cliffs of T18 are painted into those tiles with their light and shadow (seen 2026-10-03), so repainting is the fix.

**The design (first draft, for the owner's look):**
1. **A Paint tab** in the dock (the editing/drawing tab), holding Colour, Texture, Repaint and **Erase** (moved here
   from its own tile).
   - **Colour:** paints a colour onto the ground picture with an opacity: a colour wheel, a palette of the map's own
     ground colours (sampled from the map: its grass, fields, sand, rock, roads), an eyedropper, recent colours.
   - **Texture:** paints with the map's own ground copied from a spot you pick (a clone stamp: real grass or sand, not
     a flat colour), or with the game's own ground textures (the decors' `Herbe`, `Sable`, `Roche`, `Terre` sticker
     pictures); each stroke also gives the close-up picture the source's values, so it blends the same up close.
   - **Repaint what moved:** one click repaints every place the ground brushes moved by more than a few metres with a
     texture you pick (the T18 riverbed and coast).
   - Written as `maps/<map>/paint.toml` strokes, applied in order by the build to every level of both tile pyramids,
     the whole-map pictures and the close-up picture (rusemod.groundpaint's tile writer); the Studio's 3D view shows
     the paint at once on the map's picture.
2. **Brush types in every tool that has a brush** (ground, water, cover, movement, erase, paint): **soft round** (today's),
   **hard round**, **square** (turned to any angle: a beach's line, a field), and **line** (a fine line or a wide band
   between two clicks, Shift for straight). Size, strength or opacity, angle. The build's brush rules (rusemod.brush)
   learn the same shapes so the game gets what the Studio shows.
3. **More detail ("doubling"), each one tried in the game before it's offered:**
   - the ground picture with one finer level (each finest tile as four: twice the pixels each way, 0.3 m a pixel on
     Blitz); whether the game's terrain loader takes a deeper pyramid is not known (one test map);
   - the close-up picture at twice its size (2048 → 4096 on Blitz);
   - a finer ground mesh for better shading (cutting the mesh finer: not built);
   - **object textures** are `.tgv` files in `ZZ_Win.dat` (DXT1, DXT5 or A8R8G8B8, each picture zlib-packed or in the
     game's own TGU1 coding; buildings share atlases); a texture twice the size can be written (plain DXT, as the ground
     tiles), but its extra detail has to come from somewhere: plain upscaling only smooths, a sharper picture needs an
     upscaling program or new art. Not known yet: whether the game takes bigger textures (one test), and each doubled
     texture takes four times the memory.

Order proposed: brush types → the Paint tab (Colour, Texture, Erase moved in) → Repaint what moved, with a flat Blitz
Twin test copy → the detail tests (a deeper pyramid on one map, one doubled building atlas).

**Done 2026-10-03, step 2: the Map Paint tile** (the owner's name), holding **Paint** and **Erase** (moved in). Paint
has two brushes, each round, square (any angle) or a line, soft or hard edged, with Opacity:
- **Colour**: a colour wheel (hue ring, strength and lightness square), its #rrggbb, an eyedropper (or Alt+click), the
  map's own colours (its picture sampled: grass, fields, sand, rock, roads) and the last ones used;
- **Texture**: the map's own ground copied from a spot you pick (or Alt+click): the first stroke after picking sets
  the distance, a second ring shows where it copies from as the brush moves.
Saved as `paint` / `stamp` strokes in terrain.toml (MOD_FORMAT §8); the build lays them on every level of both tile
sets and, for Texture, the close-up picture (rusemod.groundpaint.paint_strokes, stamp_detail), before the new roads.
The Studio shows them at once on its copy of the map's picture. In the game (T20, owner 2026-10-03 21:55): **shows
from high up, not up close**, "the same issue as roads did". Every tile level is red in the copy; what Blitz draws near
the camera over the ground there is crops, grass, bushes, stones and ground stickers (263,000 objects in the 1 km
patch). T21 takes the stickers off under one patch and all of that low cover under another; if that's it, Map Paint
clears the low cover under strong paint the way a new road clears its path (rusemod.scenery.road_clearing).
**Built 2026-10-04 (local, no release until the models are done: owner):** T21 passed (yellow: all the low cover off
shows the paint up close), so Map Paint strokes `clear` by default (the Studio's "Clear the ground under it",
groundpaint.paint_clearing): stickers, low plants and stones go wherever the stroke is at least half strength, by
how far each reaches (scenery.EraseArea.by_size: a sticker 20 m across centred outside a patch still covered its
edge in T26). Its first in-game look: T27's frames. Also built the same day, from T25 (passed): an erase area that
takes buildings opens its ground to every unit (build.cleared_woods), so units drive where a town's houses stood.
Flattened rivers (T18's "tearing", T26, T27): the jagged rock up close is the river's rock sticker
(`Stickers_France_AutoBuild_Rocher_parallaxe_off_03`, 832 of Blitz's 833 in an old hollow), not either picture (T27:
neither alone took it away; T26's one clean stretch had its stickers off too). From high, the picture still shows the
old river. The fix, in T28 (not in the build until it passes): the bank stickers reaching into a filled hollow taken
off, and the hollow's picture and close-up map mended from both banks (`rusemod.mend`: each side takes the ground
beyond its own bank moved across, cross-fading in the middle; T26's copied field read as a road). Then the build does
it wherever its ground edits fill a hollow (the old mesh's hollows that the new ground no longer has). The same day, from
the owner: Map Paint's sizes run from 15 m to about 1.4 km across ("make like a ginormous patch red, not just a tiny
little" one; the build fills the blocks a solid stroke covers whole at once, and the DXT encoder is twice as fast,
the same bytes); and "a paint matcher so you can match the colors of certain objects": the eyedropper takes a
building's, prop's or tree's own colour (its picture's texel where clicked, without the light), tried in code only
(the Studio preview has no game models). Next in this list:
the game's own ground textures as Texture sources (the decors' sticker pictures), then step 3.
