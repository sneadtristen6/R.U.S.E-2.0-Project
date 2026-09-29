# Mod Package Format: Draft Spec v0.1

Status: draft for discussion (2026-09-28). Nothing here is final until M2 proves it in-game.
Related: [PLAN.md](PLAN.md) · [FORMATS.md](FORMATS.md).

## 1. Goals

- **Readable and git-friendly:** text sources and standard asset formats, one thing per file.
- **Changes, not copies:** a mod describes what it changes, relative to names in the game, never byte offsets.
- **Composable:** many mods can be combined; conflicts are detected and reported.
- **Update-proof:** mods survive game updates, and anything that needs review is flagged.
- **Deterministic:** the same mods + the same game build produce the same result on every PC.
- **No Eugen files inside:** a package contains only the author's work and derived assets.

## 2. Package layout

```
ruse2-core/
  mod.toml                 manifest (required)
  src/                     text patches (.rndf), any folder structure
    units/marines.rndf
    balance/tanks.rndf
    studio.rndf            the Studio's changes (it rewrites this file; hand-written ones go in the others)
  text/                    localisation tables (.csv)
    units.csv
    studio.baseunite.csv   the Studio's new units' names (rewritten by the Studio; goes into baseunite.dic)
  files/
    replace/<game path>    replaces an existing game file (cooked from a source format)
    add/<new path>         adds a new file (under mods/<mod id>/...)
  maps/<MapId>/            map sources (see §8)
  scripts/<package>/       Python 2.5-compatible sources (see §9)
  README.md, LICENSE, CHANGELOG.md
```

A package is shared as a `.zip` of this folder. Built outputs are never part of the source package. An optional
`cache/` of cooked assets, keyed by tool version, can ship to speed up installs.

## 3. Manifest (`mod.toml`)

```toml
[mod]
id          = "ruse2-core"          # unique, lowercase, a-z 0-9 -
name        = "RUSE 2.0 Core"
version     = "0.1.0"               # semver
authors     = ["you"]
license     = "CC-BY-4.0"           # the mod content's license (author's choice)
description = "Balance, new units and tactics for RUSE 2.0."
text_prefix = "R2"                  # start of the text keys this mod creates (§6)
platform    = ">=0.1, <0.2"         # platform versions this mod works with

[game]
builds        = ["24687178"]        # Steam build ids the mod was tested on
data_revision = "190852"

[dependencies]                      # hard dependencies: id = version range
# "ruse2-assets" = "^0.3"

[optional]                          # load before this mod if present, no error if missing
# "better-ai" = "*"

[load]
after  = []                         # extra ordering hints
before = []

[conflicts]                         # mods that must not be combined with this one
# "some-other-overhaul" = "*"
```

`affects_gameplay` is **computed** by the builder (§10) and never declared by hand.

## 4. Addressing game objects

| Form | Example | Meaning |
|---|---|---|
| Export path | `$/GFX/Everything/Descriptor_Unit_M4_Sherman` | a named object, using the engine's own names (EXPR table) |
| Sub-object | `…Descriptor_Unit_M4_Sherman:WeaponManager.Turrets[0]` | a path from the nearest named owner: `.property`, `[index]` |
| Selector | `…:Turrets[class=TTurretTwoAxisDescriptor]`, `…:Weapons[Ammunition=$/GFX/…/Ammo_75mm]` | matches list items by class or a property value. More robust than an index across game updates |
| Map key | `…:SomeMap{'key'}` | an entry of an NDF map |
| Mod-local | `~/Descriptor_Unit_R2_US_Marines` | an object declared in this mod |

New objects are created in the same NDF file as the object they are cloned from, unless `in "<ndf file>"` is given.
Names must be unique. Convention: include a short mod prefix (`Descriptor_Unit_R2_…`).

Mods can only instantiate classes the engine already knows. New behaviour comes from combining existing
classes or from scripts; truly new mechanics need the runtime extender.

## 5. Text patches (`.rndf`)

The syntax is close to Eugen's NDF text (WARNO/Steel Division 2), plus patch operators.

```ndf
// Change an existing unit
patch $/GFX/Everything/Descriptor_Unit_M4_Sherman
(
    ProductionPrice = [30, 30, 30, 30, 30]   // set
    VitesseLineaire *= 1.10                   // multiply (element-wise on numeric lists)
    SeuilMort += 100                          // add
    delete SeuilPinned                        // remove property -> engine default
)

// New unit: deep-copies the objects owned only by the source; shared objects stay shared
Descriptor_Unit_R2_US_Marines is clone $/GFX/Everything/Descriptor_Unit_US_Rangers
(
    Name            = loc('r2.unit.us_marines.name')
    ProductionPrice = [15, 15, 15, 15, 15]
    ShowInMenu      = [1, 1, 1, 1, 1]
)

// Lists
patch $/GFX/Everything/SomeProductionList      // illustrative path
(
    Units += [~/Descriptor_Unit_R2_US_Marines]                       // append
    Units -= [$/GFX/Everything/Descriptor_Unit_Old]                  // remove matching items
    Units.insert(after=$/GFX/Everything/Descriptor_Unit_US_Rangers,
                 value=~/Descriptor_Unit_R2_US_Marines)              // positional insert
)

// Every object of a class at once, for balance passes (§10.2)
patch every TBatimentDescriptor
(
    ProductionPrice *= 0.9
)

// Something this unit shares with other units: say who the change is for (§10.5)
patch own $/GFX/Everything/Descriptor_Unit_M4_Sherman:Weapons[0].Ammunition   // `own`: only this unit
(
    Puissance += 10
)

// Replacing another mod's value on purpose: no warning (§10.4)
patch $/GFX/Everything/Descriptor_Unit_M4_Sherman
(
    override ProductionPrice = [25, 25, 25, 25, 25]
)

// Brand-new object from scratch (every property explicit)
Ammo_R2_Flamethrower is TAmmunition
(
    Puissance      = 120
    PorteeMaximale = 3000
)

delete $/GFX/Everything/Descriptor_Unit_Unwanted

// Runs after every mod's normal changes, so it reaches units other mods add too (§10.6)
final patch every TUniteAuSolDescriptor
(
    SeuilMort *= 1.1
)

// Only when another mod is in the set: a compatibility patch (§10.6)
when mod better-ai
(
    patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( ProductionPrice += 5 )   // +5 on each era's price
)
```

**Values**
- **Type follows the schema:** when you patch an existing property, the literal is converted to that property's
  type, so `ProductionTime = 10` just works. Explicit forms are spelled the way Eugen's own text NDF (WARNO) spells
  them wherever it has one: `Float2[a, b]`, `Float3[x, y, z]`, `Float4[a, b, c, d]`, `Int2[a, b]`, `RGBA[r, g, b, a]`,
  `GUID:{…}`. Ours cover the types WARNO's text doesn't tell apart: `int8() int16() uint16() uint32() int64() f64()
  str('…') wstr("…") path('…')`, and text keys `key(M_D_01)` (or `key(0x…)` for one that isn't a name).
- Lists are `[a, b]`, maps `MAP [ (k, v), … ]`, pairs `(a, b)`, booleans `true` / `false`.
- References are `$/…` export paths, `~/Name` for mod-local objects, and `nil`.
- `loc('key')` refers to a row in `text/*.csv` (§6).
- `export` in front of a new named object is allowed, as in WARNO; every named object a mod creates is exported anyway.
- Comments are `//`, `/* */` and `(* *)`. Files are UTF-8.

## 6. Localisation (`text/*.csv`)

Built: `src/rusemod/loc.py`, run by `ruse build` (PLAN.md §7, C6).

```csv
key,game_key,us,fr,ger,ita,spa,pol
r2.unit.us_marines.name,R2MARINE,US Marines,Marines US,US-Marines,Marines USA,Marines de EE. UU.,Piechota morska USA
```

- **The file name picks the game dictionary:** `text/baseunite.csv` goes into every `baseunite.dic` (unit names; the
  game has 112 dictionaries per language). A name the game doesn't have is an error. A file called
  `<anything>.<dictionary>.csv` goes into that dictionary too (`text/studio.baseunite.csv` is the Studio's, which it
  rewrites; a mod's hand-written `text/baseunite.csv` stays its own).
- **Using a text:** `NameInMenuToken = loc('r2.unit.us_marines.name')` in a `.rndf` file becomes that row's game key.
  A `loc()` that no mod in the set defines is an error.
- **Where it goes:** all texts live in `ZZ_Win.dat`, so a mod with texts also rebuilds that 2.3 GB pack (streamed, in
  the modded copy) until the game can load a pack of ours for text (PLAN.md L5, M10). Texts are cosmetic: they don't
  change the fingerprint (§10.8). The `dev` folder gets the `us` text.

- **Language columns** use the game's own language folders: `us fr ger ita spa pol cz ru jpn sc` (from
  RUSE-Mod-Manager's notes; `tools/dic_check.py` confirms them on the game). The usual codes are accepted too:
  `en de it es pl cs ja zh`. Missing cells fall back to `us`.
- **Text keys are readable names.** The game's keys pack a name of up to 8 characters (0-9, A-Z, _, a-z) into a
  number ([RESEARCH.md](RESEARCH.md) §5). Each row gets one: the `game_key` column sets it (`R2MARINE`), or when it's
  empty, the builder makes one from the manifest's `text_prefix` plus a number, assigned in sorted `key` order so it's
  the same on every PC (`R2000001`, `R2000002`, …). A key the game or another mod in the set already uses is an error
  that names both.
- Existing game texts can be overridden by name, `game:M_D_01`, or by number, `game:0x…`, for a key that isn't a name.

## 7. Assets

| Kind | Source format | Cooked to | Notes |
|---|---|---|---|
| Texture | PNG (or DDS) + optional `.toml` (format DXT1/DXT5/A8R8G8B8, mips) | `.tgv` | M5 |
| Model | glTF 2.0 (+ textures) | `.spk` | M7; static first |
| Sound | WAV | `.ess` | M11, last |
| Other | the game's own format | copied | escape hatch |

- `files/replace/<game path>.<source ext>` replaces an existing file. For example,
  `files/replace/gen/ww2/res3d/…/sherman.tgv.png` is cooked to that `.tgv`.
- `files/add/mods/<mod id>/<name>.<source ext>` adds a new file, referenced from `.rndf` by its game path.
- Which pack receives new files depends on whether NDF can mount an extra pack (tested in M2). The preferred
  answer is a mod-owned pack mounted by NDF.

## 8. Maps

```
maps/R2_Iwo/
  map.toml        # display name, players, modes, base map to clone (v1), minimap icons
  scenario.rndf   # start positions, depots, buildings, zones, objectives (semantic, not binary)
  layers/*.png    # AI concealment / movement-blocking layers
  terrain/        # later (M8): heightmap.png, texture layers, scenery.json
```

- **v1 (M6):** a map is a clone of an existing map (`base = "TwoIslands"`) plus changes.
- The builder then:
  - creates the new `TMapLoadInfo`, its GUID and cluster files
  - creates the map pack
  - creates the DataMap_Win and IA_Common entries
- Terrain comes later (M8).

## 9. Scripts

- `scripts/<package>/*.py` holds Python 2.5-compatible source.
- The builder compiles it to `.xyz`, packs it into a mod `.ipk`, and registers the pack through NDF
  (`TResourceDescriptorPythonPack`, `TClusterAddPythonPath`).
- Scripts are code: the launcher installs them only from the mod index or after explicit consent.

## 10. Build semantics

A mod is a list of instructions ("set this", "multiply that", "clone this unit"), never a copy of game files.
Every build starts from the untouched game and replays the instructions of every mod in a fixed order, so the result
depends only on the game build, the mods and their order.

### 10.1 Steps

1. **Resolve:** pick the mods and versions and put them in load order (§10.6).
2. **Read:** turn each mod's `.rndf`, `.csv` and `files/` entries into operations (the patch IR, [PLAN.md](PLAN.md) L3).
   Every operation remembers its mod, file and line.
3. **Apply:** start from the base game for this build and apply the operations one at a time: mods in load order;
   inside a mod, files sorted by path; inside a file, top to bottom. Then the `final` operations, in the same order
   (§10.6).
4. **Check, cook, pack, fingerprint** ([PLAN.md](PLAN.md) L3).

**One rule explains most of what follows:** every operation sees the game exactly as the operations before it left it.

### 10.2 Operations

| Operation | Written as | Works on | Result | Error when |
|---|---|---|---|---|
| set | `P = v` | any property | the value becomes `v`, converted to the property's type (§5). An absent property is added | the object doesn't exist; `v` can't convert |
| multiply | `P *= k` | a number, or each item of a list of numbers | value × k | the property is absent (below) or not numeric |
| add | `P += n` | a number, or each item of a list of numbers | value + n | same as multiply |
| append | `P += [a, b]` | a list | the items go at the end, in the order written | the property isn't a list |
| remove | `P -= [a]` | a list | every item equal to `a` is removed | never; if nothing matched, a warning |
| insert | `P.insert(after=x, value=v)` (also `before=`, `at=`) | a list | `v` goes next to the first item equal to `x` | `x` isn't in the list |
| delete property | `delete P` | any property | the property is removed, so the engine uses its built-in default | never |
| create | `Name is Class ( … )` | nothing yet | a new object with exactly the properties written | the name is taken; the engine doesn't know the class |
| clone | `Name is clone Src ( … )` | an object | a copy of `Src` (§10.5), then the body is applied to the copy | `Src` doesn't exist; the name is taken |
| delete object | `delete Obj` | an object | the object is removed | anything still refers to it once all mods have run (the validator's dangling-reference check) |
| replace file | `files/replace/<game path>` | a game file | the whole file is replaced | the game file doesn't exist |
| add file | `files/add/mods/<mod id>/…` | nothing yet | a new file | the path is taken |

- `+=` with a number is arithmetic; `+=` with a list `[…]` appends. It's the only operator with two meanings.
- **Math on an absent property is an error**, because the engine's default isn't stored in the data (FORMATS.md §3:
  a default `Nationalite` of 0 is simply not written). The fix is to `set` it first.
- **Deleting is risky.** Game scripts look objects up by name (`Database.GetObject`, [ENGINE_NOTES.md](ENGINE_NOTES.md)),
  which the validator can only partly check. Hiding a unit (`ShowInMenu = [0, 0, 0, 0, 0]`) is usually the safer choice.
- A target that doesn't exist in this game build is an error that suggests a rebase (§11). It's never skipped silently.
- **`patch every <class>`** applies its body to every object of that class that exists at that point in the load order,
  including clones from mods loaded earlier. Objects that lack a property the body does math on are skipped and listed
  in the report, instead of stopping the build.

### 10.3 Numbers

- Literals are read as exact decimals: `1.10` is exactly 1.10, not the nearest binary fraction.
- When several operations change the same number, the whole chain is computed exactly and **rounded once**, when the
  value is written: integers round the school way, half away from zero (52.5 → 53, like Excel's `ROUND`), `float32`
  values to the nearest float32.
- Same inputs, same answer on every PC. Multiplayer depends on it (§10.9).

### 10.4 When two mods touch the same thing

Three levels:
- **Error:** the build stops and nothing is deployed. The message names both mods, files and lines.
- **Warning:** the build goes ahead; the build report and the launcher's mod-set screen show it. `override` in front of
  the later operation (`override ProductionPrice = […]`) says "I mean it" and turns that warning into a note.
- **Note:** only in the build report.

Mod A loads before mod B, and both touch the same property, list, object or file:

| A does → B does | Result | Level |
|---|---|---|
| set → set | B's value wins | warning (none if the values are equal) |
| set → multiply / add | B's math runs on A's value | note |
| multiply / add → set | B's value wins; A's change is lost | warning |
| multiply / add → multiply / add | both apply, in load order (the order matters when × and + mix) | note |
| delete property → set | B puts a value back | warning |
| delete property → multiply / add | nothing to calculate with | **error** |
| set or math → delete property | A's change is lost | warning |
| append → append | both sets of items are added, A's first | none |
| append → remove (the same item) | B takes A's item out again | warning |
| remove → append (the same item) | B puts the item back | warning |
| remove → insert next to that item | the anchor is gone | **error** |
| set whole list → append / remove / insert | B edits A's new list | note |
| append / remove / insert → set whole list | A's list edits are lost | warning |
| patch object → delete object | A's changes are thrown away | warning |
| delete object → patch, clone or refer to it | the object is gone | **error** (the clash RUSE-Mod-Manager can't see) |
| create / clone → create / clone with the same name | two objects can't share a name | **error** |
| replace file → replace file | B's file wins | warning |
| replace file → patch inside that file | B's patch runs on A's replacement | note |

Also:
- In a list of references, an item that's already there isn't added twice (a note). Lists of plain values keep duplicates.
- Every final value keeps its history: for any property, the report shows the chain of operations that produced it
  (mod, file, line, and the value after each step).
- `[conflicts]` in a manifest (§3) is checked before anything is applied: if either mod lists the other, combining them
  is an error.

### 10.5 Clones: what's copied, what's shared

A unit is one named object plus unnamed sub-objects (weapon slots, turrets and so on), linked by references.
- **Owned sub-objects are copied.** An unnamed sub-object belongs to the source when the only way to reach it from any
  named object is through the source.
- **Shared sub-objects are not copied.** If other named objects also reach it (several units using one weapon object,
  say), the clone points to the same one.
- **Named objects are never copied.** References to anything with its own export path, and imports (`$/…` from other
  files), keep pointing to the original.
- **Fresh identity** (built: `src/rusemod/identity.py`): the clone gets its new export name, plus fresh values for
  what must differ between units:
  - `DescriptorId`, `TrackingId`: one more than the highest in the game, if the class uses them as ids (no two of its
    objects share a value).
  - `ClassNameForDebug`: the clone's own name, written like the source's (`Descriptor_Unit_R2_X` gives `Unit_R2_X`),
    with `_2`, `_3`, … added if that's taken.
  - `PositionInMenu` (slot = row × 100 + column): units with the same `Nationalite` and `Factory` share a build menu.
    The copied slot is kept if it's free in the clone's menu; otherwise the clone goes after the last unit of the
    same row.
  - Anything the clone sets itself is kept. The build report lists every fresh value, and warns when a new object
    ends up sharing one with another object (after a later patch, say).
  - The name shown in game (`NameInMenuToken`) stays the source's until text mods can supply names (§6).
  - `tools/identity_check.py` checks these rules against the real game (PLAN.md §7, C5).
- **A copy of that moment:** a clone copies its source as it is at that point in the load order. Later patches to the
  source don't reach the clone, and patches to the clone never reach the source.
- **The game's Python unit list** (FORMATS.md §5): R.U.S.E. only uses units that have a class there, so the build
  gives every copy of a listed unit its own class (named after the copy's `ClassNameForDebug`, with the source's
  base class). A unit made from scratch, or a copy of an unlisted one, gets a warning: the game ignores it.
  Deleting a listed unit is an error for now (the list would point at nothing).
- **Mods never contain scripts or programs** (`.py`, `.xyz`, `.ipk`, `.exe`, `.dll`, `.bat`, …): the build refuses
  them. The unit-list classes above are the only script change a build makes, written from one fixed template
  and checked (PLAN.md decision 23).
- **Giving a clone its own weapon:** clone the weapon or ammunition too, and point the clone at the copy:
  `Weapons[0].Ammunition = ~/Ammo_R2_Flamethrower`.

**Editing a shared sub-object through one unit** (`…Descriptor_Unit_X:Weapons[0].Ammunition`, when that ammunition is
used by other units too) would silently change every unit that uses it. So it's an error unless the patch says which
it means:
- `own`: give this unit its own copy first, then change the copy.
- `shared`: change it for every unit that uses it. The error message lists them, so the author can decide.

### 10.6 Load order and dependencies

1. **Versions:** each mod states the versions it accepts for its dependencies (§3). The resolver picks, for every mod,
   the newest version that all ranges accept. If none fits, the error names the mods that disagree.
   A mod set's lockfile (§12) pins exact versions, so a saved set never changes by itself.
2. **Order:** the mods and their rules form a graph:
   - a dependency loads before the mod that needs it
   - so does an optional dependency, when it's present
   - `load.after` / `load.before` add more arrows

   The builder walks the graph, and when several mods are free to go next it takes them alphabetically by id, so the
   order is always the same. A loop (A after B, B after A) is an error that names the loop.
3. **Mods that must not combine** (`[conflicts]`) stop the build before anything is applied.
4. **Final pass:** operations marked `final` (§5) run after every mod's normal operations, again in load order. So a
   balance pass marked `final` reaches the units every other mod adds, without listing those mods. (Factorio's
   final-fixes stage and ModuleManager's `:FINAL` work the same way; [RESEARCH.md](RESEARCH.md) §5.)
5. **Conditional blocks:** `when mod <id> ( … )` applies its contents only if that mod is in the set; `when not mod`
   is the opposite, and a version range can follow the id (`when mod better-ai >=1.2`). A mod named in a `when`
   counts as an optional dependency, so a compatibility patch always runs after the mod it patches. (Like
   ModuleManager's `:NEEDS`.)

### 10.7 Worked example

Three mods on build 190852. The prices are invented; the object names come from FORMATS.md and
`tools/make_test_instance.py`.

```ndf
// mod "econ-half" (loads first)
patch $/GFX/Everything/Descriptor_Building_BatimentAdministratif
(
    ProductionPrice *= 0.5
)

// mod "hardcore" (loads second)
patch $/GFX/Everything/Descriptor_Building_BatimentAdministratif
(
    ProductionPrice += 5
)

// mod "mg-nest" (loads third)
Descriptor_Unit_R2_MG_Nest is clone $/GFX/Everything/Descriptor_Unit_Tourelle_MG_US
(
    ProductionPrice = [20, 20, 20, 20, 20]
)
```

- With a base price of 105: econ-half then hardcore gives 105 × 0.5 + 5 = 57.5 → **58**. The other way round,
  (105 + 5) × 0.5 = **55**. Same mods, different order, different game. That's why the order is fixed and recorded.
- Both are math, so there's no warning, only a note showing the chain.
- The MG nest copies the turret's own sub-objects. Anything the turret shares with other units, and every named
  object it points to, stays shared.
- Add a fourth mod that deletes `Descriptor_Unit_Tourelle_MG_US`:
  - loaded **before** mg-nest: error. mg-nest clones an object that no longer exists.
  - loaded **after** mg-nest: the clone is fine, but anything that still refers to the turret (a build menu, for
    example) makes the validator stop the build until the fourth mod removes those references too.

### 10.8 Gameplay vs cosmetic

The builder sorts every file a mod set changes into one of two groups. Authors never declare it.

| Group | Files | In multiplayer |
|---|---|---|
| **Gameplay** | every NDF file (unit data, maps, scenario data, even the few that are probably UI-only), `.scenario`, `mapinfo.win`, `.kdt`, `save.boobspc`, `output.sdb`, anything inside a map pack, scripts (`.xyz`, `.ipk`) | must be identical on every PC |
| **Cosmetic** | textures, models, animations, sounds, videos, fonts, UI (`.gpk`), text (`.dic`) | may differ between players |

- A mod set counts as gameplay if it changes even one gameplay file. Only gameplay files go into the fingerprint (§12).
- A file whose content ends up identical to the game's own doesn't count as changed.
- Cautious on purpose: when in doubt, a file is gameplay. A wrong "gameplay" only makes players match when they didn't
  strictly have to; a wrong "cosmetic" causes desyncs.
- To confirm in the 2-PC tests ([PLAN.md](PLAN.md) L6), models especially: in some games a model's size changes what
  can be seen or hit.

### 10.9 Determinism

- stable ordering everywhere, no timestamps
- canonical number formatting
- fixed compression settings (or uncompressed NDF, which the engine accepts)
- normalised text (UTF-8, LF)
- fingerprints over canonical content, not raw bytes

### Decided (2026-09-28)

1. **Rounding:** the school way, half away from zero (52.5 → 53), the same as Excel's `ROUND`.
2. **Shared sub-objects:** editing one through a unit is an error unless the patch says `own` or `shared` (§10.5).
3. **Patch, then a later mod deletes the object:** a warning (§10.4).
4. **Patching many objects at once:** `patch every <class>` exists (§5, §10.2) for balance passes.
5. **A final pass** for balance mods (§10.6).
6. **Conditional blocks** for compatibility patches, `when mod <id>` (§10.6).
7. **WARNO's spellings** for values, references and comments (§5).
8. **Readable text keys** (§6).

## 11. Game updates

- At build time, the builder records a **base hash** for every object or file a mod touches.
- On a new game build:
  - unchanged targets rebase automatically
  - changed targets are flagged for a 3-way review (old base, new base, mod)
  - missing targets are errors
- `game.builds` in the manifest is updated when the author confirms.

## 12. Mod sets, lockfiles, fingerprints and join codes

```toml
# modset.lock
format      = 1
platform    = "0.3.0"
game_build  = "24687178"
fingerprint = "K7Q2-M9XD"   # written by the builder (below)

[[mod]]
id      = "ruse2-core"
version = "0.4.1"
sha256  = "…"
source  = "index"      # or a direct URL
```

- **Shape follows Modrinth's `.mrpack`** (see [RESEARCH.md](RESEARCH.md)): each resolved file lists `path`,
  `hashes` (sha1 + sha512), `downloads` (one or more HTTPS mirrors) and `fileSize`, so packs stay tiny and files can
  live on any host. The TOML above is the human-edited form; the launcher stores the resolved JSON.
- **A published mod version never changes.** A fix is always a new version. That's what lets a mod id + version stand
  for exact files everywhere: lockfiles, join codes and the index.

### Fingerprint

A short code that is the same on two PCs exactly when their gameplay content is the same.

```
SHA-256 over, in this order:
  "RUSEFP1\n"
  the Steam build id, "\n"
  for each gameplay file (§10.8) the mod set changes, adds or deletes,
  sorted by its lowercase game path with "/" separators:
    the path, "\n", the SHA-256 of its canonical content as 64 hex characters (or the word "deleted"), "\n"
```

- **Canonical content:** NDF files are hashed uncompressed (their logical bytes, with the header's "compressed" flag
  cleared), so compression can't change the fingerprint. Every other file is hashed as written.
- **Only changed files count.** Everything else is pinned by the Steam build id, so a fingerprint takes seconds, not a
  pass over 3 GB of game data.
- **Cosmetic files are left out**, so two players with different skins still match.
- **It's about content, not names:** two different mod sets that produce identical gameplay files get the same
  fingerprint, and that's correct, because they play together fine.
- **Shown to people as 8 characters** of Crockford base32 (digits and letters without I, L, O, U, so nothing is
  misread), e.g. `K7Q2-M9XD`. Vanilla has one too (no changed files), so "we're both on vanilla" is checked the same way.

### Join codes

v1 needs no server. A join code names the game build, the mods and their exact versions, and the fingerprint.

- `RUSE1:` + Crockford base32 of:
  - format (1 byte), Steam build id (4 bytes), fingerprint (the first 10 bytes of the SHA-256), mod count (1 byte)
  - per mod: its id (length + text) and version (3 bytes: major, minor, patch)
  - a 4-byte checksum (CRC-32) that catches typos and cut-off pastes
- Length, with typical 10-letter mod ids: about 60 characters for one mod, 110 for three, 260 for ten. Fine for Steam
  chat or Discord.
- **No file hashes needed:** published versions never change, so id + version already pins exact files, and the index
  has their hashes. After building, the joiner's fingerprint must equal the code's (all 10 bytes), or the launcher
  stops before the game starts and says so.
- Mods that aren't on the index can't go in a v1 code (they'd need a download link). The launcher says so and offers
  the full lockfile as a file to send instead.
- Changed from the first draft, which put the whole compressed lockfile in the code: the file hashes made codes about twice as
  long, and the fingerprint check makes them unnecessary.
- **v2 (optional service):** short codes, and direct transfer of unpublished mods.
- **Built:** [`src/rusemod/lock.py`](../src/rusemod/lock.py), tested in `tests/test_lock.py`. Reading a code forgives
  spaces, lower case, dashes, and I / L / O typed for 1 / 0.

### Decided (2026-09-28)

1. **A published mod version never changes;** a fix is always a new version, so a version number always means the same
   files (like a store's item number).
2. **Join codes carry mod names, versions and the fingerprint** instead of the whole lockfile.

## 13. Interop with RUSE-Mod-Manager (`.rmod`)

- **Import:**
  - `patch`, `create`, `delete` and `delete_props` become the matching operations.
  - Their instance indices are translated to our paths through the base build's registry.
  - `file_patches` become replace/add file operations.
  - Anything that can't be resolved is reported, never guessed.
- **Export** (later): the subset of operations `.rmod` can express, so RUSE-Mod-Manager users can install our mods.

## 14. Open questions

1. Which pack receives new files and new NDF objects (depends on whether NDF can mount an extra pack)?
2. Can a mod add a whole new NDF file, or only objects inside existing ones?
3. How does the engine react to duplicate export names across files?
4. ~~Language list~~ **Answered (FORMATS.md §4):** `us`, `fr`, `ger`, `ita`, `spa`, `pol`, `ru`, `cz`, `jpn`, `sc`
   (112 `.dic` files each). New text must also update each file's character list (key `0x8000000000000000`).
5. The exact gameplay/cosmetic split (depends on what the desync checker hashes).
6. Scenario source format: design it once the binary format is decoded (M6).
