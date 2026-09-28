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

### L1 Formats
- Each format is one plugin module: `parse(bytes) -> model`, `write(model) -> bytes`, a status
  (unknown / read / write / round-trip) and golden tests.
- Big packs are accessed lazily and streamed (ZZ_Win.dat is 2.4 GB).
- Unknown bytes are kept raw so round trips stay exact. For example, some NDF bools store `0x4E` instead of 0/1.

### L2 Game model

Built from the install once per game build (read-only), then cached. Everything above it (the mod builder, launcher,
Studio, CLI) asks the game model instead of opening packs itself. This is the next thing to build (M1); it's written
out here so it can be built straight from this section.

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
| `prop_seen` | class + property + type | how often it appears, min and max for numbers, an example (feeds the schema DB) |
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
annotation files:
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
- **Launcher (players):**
  - detects the game and build
  - browses and installs mods from the index; manages mod sets and join codes
  - one-click join, updates, instances, self-update
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
- **Studio (modders):**
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

## 6. Key design decisions (this table is the decision record)

| ADR | Decision | Choice | Why | Alternatives |
|---|---|---|---|---|
| 1 | Core language | Python 3.11+ with type hints | runs inside Blender; same language as community tools; fastest for reverse engineering; AI-friendly | C#/.NET, Rust |
| 2 | UI stack | Web UI (TypeScript, three.js for 3D) in a desktop window (pywebview), served by the local service | best 3D and UI ecosystem; one UI codebase for Launcher and Studio; runs on Linux/Deck | Qt / PySide6 |
| 3 | Runtime extender | C++ x64 proxy DLL, optional, instance-only | exe has no DRM/ASLR; `version.dll` is imported | none (repack only) |
| 4 | Deployment | Modded instances via hard links | never touch the Steam install; mod sets side by side | in-place swap with backups (fallback) |
| 5 | Mod identity | Engine export paths + owner paths + selectors | stable across updates, human-readable | indices (.rmod `index_map`) |
| 6 | Source format | NDF-style text + CSV + standard asset formats | familiar to Eugen modders (WARNO/SD2 use text NDF); git-friendly | JSON / YAML |
| 7 | Determinism | Fingerprint over canonical content, bundled runtime, fixed ordering | lockstep multiplayer | hashes of raw bytes only |
| 8 | License | **MIT (decided 2026-09-28)**. RUSE-Mod-Manager's GPLv3 code is never copied: we study what it does and build our own better version | maximum reuse by community tools and Eugen; independence | GPLv3 (rejected) |
| 9 | Packaging & install | Nuitka onefile + Inno Setup, built by GitHub Actions | faster start and fewer antivirus false positives than PyInstaller | PyInstaller, Briefcase |
| 10 | Updates | Velopack (spike first), fallback tufup | single self-updating installer | manual downloads |
| 11 | Modpack / lockfile | Modrinth `.mrpack` shape (`files[]` with path, hashes, download mirrors, size; `dependencies`) | proven, tiny packs, host-anywhere | our own format |
| 12 | Mod hosting | GitHub Releases now; Thunderstore once real mods exist; CurseForge last (needs a proxy server) | cheapest path that still scales | CurseForge first |
| 13 | Code signing | deferred to first public release; Azure Trusted Signing, then free SignPath | costs money; no instant trust anyway | sign from day one |
| 14 | Mod conflicts | Fixed load order; every pair of operations has a defined result (error, warning or note); math is exact and rounds once, half away from zero | predictable, identical on every PC | last mod wins, nothing else |
| 15 | Shared data in clones | A clone copies only what its source owns; editing shared data through one unit needs `own` or `shared` | no silent changes to other units | silent shared edits |
| 16 | Join codes | Game build + mod ids + versions + fingerprint; a published mod version never changes | about half the length of a full lockfile, checked end to end | the whole compressed lockfile |
| 17 | Extra-pack test | Moved up to M2 as check C3 | without it, every new unit name rebuilds the 2.3 GB ZZ_Win.dat | test in M5/M6 |

## 7. Roadmap

Estimates are in sessions like today's. Every milestone ends with something usable.

| Milestone | Deliverables | Exit criteria | Est. | Risk |
|---|---|---|---|---|
| **M0 Foundations** | repo, ADRs, docs, dev environment; checks C1–C2 | decisions recorded, both checks answered | 2–3 | low |
| **M1 Core I/O** | EDAT r/w, NDF r/w incl. TOPO, `.dic` r/w, `.xyz` read, scenario/mapinfo read, VFS, registry, CLI `dump`/`verify` | every shipped file of these types round-trips byte-identically | 4–6 | medium |
| **M2 Mod system slice** | text NDF (dump the whole game, compile patches), package v1, resolver, builder, instances, fingerprint, `.rmod` import, extra-pack mount test | the **pipeline** works end-to-end: a throwaway value tweak + 1 cloned unit (reused visuals) builds, loads in-game and matches in a 2-PC test. This proves the tool, not a balance mod | 4–6 | medium |
| **M3 Launcher v1** | mod index, mod sets, join codes, one-click join, updates | public alpha on GitHub, ModDB, Nexus | 3–5 | low |
| **M4 Studio v1** | content browser, reference viewer, property/unit editor, clone wizard, validation, diff/rebase | a non-programmer builds a balance mod + a new unit | 5–8 | low–medium |
| **M5 Textures & icons** | TGV r/w, UI icon/flag pipeline | retextured unit with its own icon in-game | 3–5 | medium |
| **M6 Maps I** | map cloning, scenario editor, capture-zone/AI-layer rebuild, island maps on existing terrain | a new map listed and playable in multiplayer | 5–8 | medium–high |
| **M7 Models** | SPK → glTF, Blender bridge, glTF → SPK (static, then skinned/animated) | a new vehicle model in-game | 6–12 | high |
| **M8 Maps II / terrain** | terrain texture + heights + scenery, maps from scratch, tropical scenery set | a new island map built from a heightmap | 8–15+ | high |
| **M9 Scripting** | `.xyz` decompile, Python 2.5 compile route, mission/mode scripting | a new game mode (e.g. Island Defense) | 4–8 | medium–high |
| **M10 Runtime extender** | proxy DLL, pack overlay, lobby tagging, 8th-nation research | opt-in extender works on the current build | 3 spike + 6–10 | high |
| **M11 Sound** | `.ess` codec, WAV import | a replaced sound plays in-game | 4–10 | high |

**Content comes after the tool.** Per the owner's direction (2026-09-28), no balance/unit-stat/roster
**content** is produced until the tool is usable (through M4). Value changes before then exist only to test the
pipeline, never as shipped balance. Study of Eugen's own data and scripts for design ideas is encouraged
throughout (see [ENGINE_NOTES.md](ENGINE_NOTES.md)) — read-only, nothing from the install is committed.

**Content track** (starts after M4, then dogfoods each later milestone):
- **RUSE 2.0 Core** — balance, cloned units, tactics — begins once Studio (M4) exists.
- **Pacific Island Defense** needs M5–M7, plus M9 for a custom mode. US vs Japan fits the existing nation slots.

**Totals:** the first public release (M0–M3) is about 13–20 sessions. The full vision is many months, and the
uncertainty sits in M7, M8, M10 and M11.

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
| Map-pack header checksum enforced and unknown | edited map packs rejected | test in M6 |
| 7 nations hard-coded | no new nations | Pacific needs none; "variant" mods reuse slots; research in M10 |
| SPK model format complexity | no new models | export first; static meshes before skinned ones |
| Terrain formats unknown | no new terrain | M8 is late on purpose; cooperate with the RUSE-Mod-Manager team (they decode terrain chunks) |
| Python 2.5 toolchain | no new scripts | uncompyle6 to decompile; old CPython 2.5 or a bytecode assembler to compile (a download, so your OK first) |
| Game updates | mods and tools break | per-build registry, rebase, byte-pattern hooks, CI on fixtures |
| Non-determinism across PCs | desyncs | canonical fingerprints, bundled runtime, 2-PC tests |
| Community split | low adoption | `.rmod` import/export; talk to LittleGroove and Prolution; publish everywhere |
| Legal | takedown | ship no game files; ask Eugen for an OK |
| Malicious mods | user harm | scripts only from the index or with consent; signed releases; no native code from peers |
| Small team (you + AI) | work stalls | docs, ADRs, tests, open source, contributor guide |
| WebGL unstable in the embedded webview | 3D map/model viewer blocked | prototype a three.js scene in pywebview early (cheap spike) |
| Antivirus / SmartScreen distrust of the installer | players scared off | Nuitka, signing at first public release, trust builds over releases |
| Reinventing formats others already decoded | wasted credits | read RUSE-Mod-Manager's modules first ([RESEARCH.md](RESEARCH.md)); settle the license question before map work |

## 9. Open decisions

1. Working name. Ideas: *RUSE Reforged*, *OpenRUSE*, *RUSE Forever* (a nod to FAF).
2. ~~License~~ **Decided: MIT.** We study RUSE-Mod-Manager's approach (terrain, `TGU1`, scenarios, AI layers,
   capture zones) as reference and write our own, better version. Never copy its code.
3. ~~GitHub account/org and repo, project folder, git~~ **Done:** github.com/sneadtristen6/Ruse-Mod-Platform.
4. UI stack: confirm web UI vs Qt.
5. Outreach timing. Recommended: LittleGroove now (align on `.rmod` import/export), Eugen after the M2 demo.
6. Which unit to clone as the M2 test (suggestion: a US infantry unit, for Pacific later).

## 10. Next steps

Done so far: M0 (C1 and C2), the repo on GitHub, and the design for M1–M3 on paper (Progress, §7).

1. **PC session, now:** run **C3** (§7): can the game load an extra pack of ours? Steps 1–2 need only the existing
   `src/rusemod` code plus a small string-patch helper.
2. **PC session, then M1:** build the game model from L2 (the combined file view and the index), the `.dic` reader and
   writer, and the `ruse` CLI (`detect index ls extract dump verify`). It needs the game files, so it runs on the PC.
3. **Cloud sessions (no game needed):** tests on small made-up files that run on every push, and the CLI skeleton.
4. **You:** the open decisions in §9 (name, UI stack, outreach timing, the unit to clone in M2).

**How the two sessions share the work**
- **Cloud session:** research and design, nothing that needs the game files. It writes its results into these docs.
- **PC session:** everything that needs the game: running checks and tests, building against the install, editing
  files on the PC.
- **GitHub `main` is the shared state.** The sessions can't see each other's chats, so anything the other one needs
  goes into the repo. Pull `main` before starting, push to it when done, and keep README's "Current stage" line and
  this section up to date.
