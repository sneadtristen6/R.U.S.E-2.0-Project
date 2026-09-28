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
  text/                    localisation tables (.csv)
    units.csv
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

// Brand-new object from scratch (every property explicit)
Ammo_R2_Flamethrower is TAmmunition
(
    Puissance      = 120
    PorteeMaximale = 3000
)

delete $/GFX/Everything/Descriptor_Unit_Unwanted
```

**Values**
- **Type follows the schema:** when you patch an existing property, the literal is converted to that property's
  type, so `ProductionTime = 10` just works. Explicit forms are available where ambiguous:
  `int8() int16() uint16() uint32() int64() f64() str('…') wstr("…") path('…') guid('{…}')
  vec3(x,y,z) float4(a,b,c,d) color(r,g,b,a) int2(a,b) float2(a,b) hash(0x…)`.
- Lists are `[a, b]`, maps `MAP[(k, v), …]`, pairs `(a, b)`.
- References are `$/…` export paths, `~/Name` for mod-local objects, and `null`.
- `loc('key')` refers to a row in `text/*.csv`. The builder assigns an unused 64-bit hash and writes it to NDF and every `.dic`.
- Comments are `//` and `/* */`. Files are UTF-8.

## 6. Localisation (`text/*.csv`)

```csv
key,en,fr,de,it,es,pl
r2.unit.us_marines.name,US Marines,Marines US,US-Marines,Marines USA,Marines de EE. UU.,Piechota morska USA
```

- Language columns match the languages the game ships (to be enumerated in M1).
- Missing cells fall back to `en`.
- Existing game strings can be overridden with `game:<hash>` keys.

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
- Which pack receives new files depends on whether NDF can mount an extra pack (checked in M5/M6). The preferred
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

- **Load order:**
  1. dependencies
  2. `load.after` / `load.before`
  3. mod id (alphabetical, so the order is deterministic)
- **Conflicts:** two mods setting the same property → the later one wins, with a warning. An `override` on the operation
  silences the warning. Arithmetic operations compose in load order. Patching a deleted object is an error.
- **Gameplay vs cosmetic** is classified automatically and conservatively:
  - Gameplay: any change to NDF, scenarios, `mapinfo.win`, map packs or scripts. These must match in multiplayer.
  - Cosmetic: texture, model, sound, video or font replacements that change no NDF. These may differ per player.
  - The rules get refined after 2-PC tests.
- **Determinism:**
  - stable ordering everywhere, no timestamps
  - canonical number formatting
  - fixed compression settings (or uncompressed NDF, which the engine accepts)
  - normalised text (UTF-8, LF)
  - fingerprints over canonical content, not raw bytes

## 11. Game updates

- At build time, the builder records a **base hash** for every object or file a mod touches.
- On a new game build:
  - unchanged targets rebase automatically
  - changed targets are flagged for a 3-way review (old base, new base, mod)
  - missing targets are errors
- `game.builds` in the manifest is updated when the author confirms.

## 12. Mod sets, lockfiles and join codes

```toml
# modset.lock
format     = 1
platform   = "0.3.0"
game_build = "24687178"

[[mod]]
id      = "ruse2-core"
version = "0.4.1"
sha256  = "…"
source  = "index"      # or a direct URL
```

- **Shape follows Modrinth's `.mrpack`** (see [RESEARCH.md](RESEARCH.md)): each resolved file lists `path`,
  `hashes` (sha1 + sha512), `downloads` (one or more HTTPS mirrors) and `fileSize`, so packs stay tiny and files can
  live on any host. The TOML above is the human-edited form; the launcher stores the resolved JSON.
- **Join code v1:** `RUSE1:` + base32 of the compressed canonical lockfile plus a checksum. It's self-contained, so no server is needed.
  It's typically 60–150 characters, fine for Steam chat or Discord.
- **v2 (optional service):** short codes, and direct transfer of unpublished mods.

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
4. Language list and `.dic` file set per language.
5. The exact gameplay/cosmetic split (depends on what the desync checker hashes).
6. Scenario source format: design it once the binary format is decoded (M6).
