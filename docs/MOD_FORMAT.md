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

A package is one file: the folder zipped, named `<id>-<version>.rusemod` (a plain zip inside, so it opens anywhere;
`rusemod.package`). The Studio's "Export mod…" makes it and the launcher's "Add a mod file…" installs it; a `.zip` of
the folder is accepted too. Built outputs are never part of the source package. An optional
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
fingerprint   = "K7Q2-M9XD"         # this mod alone on that build (§12); Export mod… writes these three lines

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
| Map key | `…:SomeMap{'key'}` | an entry of an NDF map (planned) |
| Map entry | `…:GfxDescriptor.SousElements[39].v.BinderEffets[0].v` | an entry of an NDF map by its place: `[i].k` is its key, `[i].v` its value (the game index names map parts this way). A key or value can be set, not deleted. The Studio uses it to give a weapon another unit's shot |
| Mod-local | `~/Descriptor_Unit_R2_US_Marines` | an object declared in this mod |
| Found by a property | `@TAmmunition[AmmunitionId=1120]`, `@[ClassNameForDebug='Unit_M4_Sherman']` | the one object of that class (or of any class, `@[…]`) whose property has that value, named or an unnamed part of another object; an error unless exactly one matches. Works wherever an object is named: patch targets, clone sources, references. `:path` reaches a part of it. This is how RUSE-Mod-Manager mods find things (§13) |
| Every match | `patch every TAmmunition [AmmunitionId=1120]` | every object of the class whose property has that value; at least one, or an error |

A reference to a part of a game object (`Ammunition = $/…/Descriptor_Unit_M4_Sherman:Weapons[0].Ammunition`, or
`@[ClassNameForDebug='Unit_Hotchkiss_H_39']:SoundMotorDescriptor`) makes that part a shared object: it keeps its
place in its file and gets a name of its own (`<file>#<index>`), and from then on a patch that reaches it through its
owner has to say `own` or `shared` (§10.5). Parts of objects a mod made can't be referred to that way yet.

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

// Found by a property, the way RUSE-Mod-Manager mods find things (§4, §13): the one object that matches...
patch @TAmmunition[AmmunitionId=1120] ( NbTirParSalves = 40 )
// ...or every object of a class that matches
patch every TUniteAuSolDescriptor [Nationalite=1] ( SeuilMort += 10 )
// A copy of a part, and a reference to another unit's part (which makes that part shared, §4)
Ammo_R2_Rifle is clone @[ClassNameForDebug='Unit_Soldat_US_Leger']:WeaponDescriptor.TurretDescriptorList[0].MountedWeaponDescriptorList[0].Ammunition ( Puissance = 8 )
patch $/GFX/Everything/Descriptor_Unit_M4_Sherman ( SoundMotorDescriptor = @[ClassNameForDebug='Unit_Hotchkiss_H_39']:SoundMotorDescriptor )

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
- **Text keys are readable names.** The game's keys pack a name of up to 10 characters (0-9, A-Z, _, a-z) into a
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
maps/<map pack>/
  map.toml        # how many players; for a new map, the shipped map it copies and its name
  terrain.toml    # brush strokes on the ground
  scenery.toml    # objects placed, and areas cleared
  scenario.toml   # starting points, spawns and names moved or added
  cover.toml      # where units hide, and the AI's blocked ground
  movement.toml   # ground units can't use, or can again
  roads.toml      # new roads
```

A map's files live in a folder named after its pack (`TwoIslands` for `Maps\PC\DataMapTwoIslands_v09.dat`,
`SuperCrossRoads4` for Blitz); a mod holds only the files it needs. A mod can also make a **new map**, a copy of a
shipped one under a name of its own, which its other files then edit like any map (below). Terrain from scratch comes
later (M8).

### A new map: `maps/<NewName>/map.toml` with `copy_of` (built: `rusemod.newmap`; PLAN §13, level 2)

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from, by its pack name (this one is Blitz)
entry = "(2) Blitz"            # optional: which of its entries, by the map list's name: a BATTLES map (needed when it
                               # has several), or an Operation's or a campaign chapter's (the copy is then one too)
players = 4                    # optional: as on any map (below), for the copy

[name]                         # what the menus call it, or one name for every language: name = "Blitz Twin"
us = "Blitz Twin"              # English, which the languages left out fall back to
fr = "Blitz jumeau"            # us fr ger ita spa pol ru cz jpn sc (en de it es pl cs ja zh work too)
```

- The folder's name is the new map's pack name: a letter, then up to 39 letters, digits and `_` (`BlitzTwin`:
  `Maps\PC\DataMapBlitzTwin_v09.dat`). The mod's other files in that folder (`terrain.toml`, `scenery.toml`,
  `scenario.toml`, `cover.toml`, `movement.toml`, `roads.toml`) edit the copy; the shipped map stays as it was.
- The build adds (FORMATS §6, "A new map"), each file a copy of the shipped map's pointed at the copy:
  - the map pack, with an id of its own in its header;
  - in `ZZ_GladPatchableWin.dat`: the map's cluster (which mounts the new pack), its constants (which name the folder
    of its grid), the scenario's cluster (which names the new scenario and map cluster), a map-list entry
    (`TMapLoadInfo`) and a BATTLES entry (`TMultiMapInfo`, in the menu pack that lists the shipped map, after the maps
    of its size), tied by a GUID of their own;
  - in `DataMap_Win.dat`: the scenario (`test\map\<new>\`) and the grid (`datasmap\<new>\mapinfo.win`);
  - in `ZZ_Win.dat`: its name under a new text key (`M_D_31`, then `M_D_32`, ...) in every language's menu texts.
- Everything else is the shipped map's, only read: its models, sounds, lighting, camera paths, menu picture and
  in-mission texts. The copy plays the shipped entry's scenario (Blitz: `leveldesign_normal.scenario`), so its
  `scenario.toml` names that file.
- The ids come from the name, so every PC that builds the mod gets the same files: a multiplayer game needs the mod on
  both PCs, like any mod. The copy isn't offered in ranked games (the shipped map's ladder place stays its own).
- **An Operation or a campaign chapter:** `entry` names it (`"Challenge - 1v1 39 Blitz_2 (Anzio)"` for Anzio,
  `"M02_Tunisie_chapter1"` for Tunisia's first chapter). The copy is then a new Operation, last in OPERATIONS (a
  `TChallengeMapInfo` in the shipped one's pack, tracking id from `CH40`), or a new chapter, last in the campaign (a
  `TChapterMapInfo`, from `M24`), with the shipped one's briefing, pictures, bonus times and population caps. Its
  mission script, cutscenes and dialog are the shipped one's: the copied scenario still names the shipped scripting
  folder. **Seen in the game:** a new Operation (Anzio Twin, `TESTS.md` T17). A new chapter isn't tried yet; the game
  opens a chapter only when the one before it in its list is finished, so a copy put last opens after the campaign's
  last chapter.
- Refused, with the reason: `copy_of` a map the game hasn't got, or one BATTLES doesn't list (campaign and Operation
  maps); a name the game's map list already has, or one starting `flat_` (the game's test maps); a map with several
  BATTLES entries and no `entry`; two mods making maps of one name; `name` without `copy_of` (a shipped map's menu name
  isn't changed here).
- `tools/verify_newmap.py <modded copy> <new map> <copy_of>` reads a built copy back and checks every registration and
  file of the new map, and that nothing else of the game changed.
- **The Studio makes one:** **Duplicate map** (Maps tab, under the open map's name) asks for the name, writes this
  file in the map changes (a new one is made when none is picked) and copies the changes made to the map so far.
  The new map is listed right after the map it copies and opens like any map: the view reads the shipped map's files
  and shows the copy's own edits on top, which go to `maps/<NewName>/`. The folder name comes from the menu name
  ("Blitz at Dusk" → `BlitzAtDusk`, a number added when it's taken).
- **Seen in the game** (`TESTS.md` T15b, T16): a new map is listed in BATTLES and plays its own ground (Blitz Twin
  flattened, with a hill in the middle); 101 new maps at once were all listed, the map row scrolling, and played.
  Names over about 35 characters are cut off in the menus. Copies of maps other than Blitz build but weren't tried in
  the game yet. Known bug: flattening the mountains at a map's edge leaves a cliff along the edge (its outermost row
  of points keeps its height).

### Reshaping an existing map's ground (built: `rusemod.brush`, `rusemod.terrain_edit`; PLAN §7 MT, T2–T3)

```
maps/TwoIslands/
  terrain.toml    # brush strokes on that map's ground, applied in order (the Studio rewrites this file)
```

The folder's name is the map's pack name (`TwoIslands` for `Maps\PC\DataMapTwoIslands_v09.dat`; the Studio's Maps
list shows it under each map). The file holds strokes, one dab of a brush each:

```toml
[[stroke]]
brush  = "hill"      # hill, raise, lower, crater, plateau, flatten, smooth, ramp, water, drain, cover, uncover
x      = 983040.0    # the centre, in world units: x grows east, y grows south
y      = 983040.0
radius = 60000.0
height = 12000.0     # hill, raise, lower, crater: how much (for crater, the bowl's depth)

[[stroke]]
brush  = "plateau"
x      = 700000.0
y      = 400000.0
radius = 40000.0
level  = 21000.0     # plateau, flatten: the height (world z) the ground goes to
weight = 1.0         # plateau, flatten, smooth, ramp: how far toward it, 0..1 (smooth: 0.5 when left out)

[[stroke]]
brush  = "ramp"
x      = 300000.0    # where the ramp starts, at height `level`…
y      = 500000.0
x2     = 520000.0    # …and where it ends, at height `level2`
y2     = 610000.0
radius = 30000.0     # half the ramp's width
level  = 14000.0
level2 = 26000.0
weight = 1.0

[[stroke]]
brush  = "water"
x      = 284160.0
y      = 376320.0
radius = 24000.0
level  = 23500.0     # water: the water surface (world z); the ground under it floods
```

| Brush | Does | Shape |
|---|---|---|
| `hill`, `raise` | ground up by `height` | round hump: full at the centre, nothing at the edge |
| `lower` | ground down by `height` | the same hump, downward |
| `crater` | a bowl `height` deep with a rim a third as high | bowl out to 3/4 of the radius, rim around 4/5 |
| `plateau` | ground to `level` | flat across the middle half, then an S-curve back to the old ground |
| `flatten` | ground toward `level`, most at the centre | round hump weighting |
| `smooth` | ground toward its local average (the mean over about a third of the radius) | round hump weighting |
| `ramp` | an even slope from `level` at (`x`, `y`) to `level2` at (`x2`, `y2`); `radius` is half its width | flat across the middle half of the width, then an S-curve back to the old ground at the sides and beyond the ends |
| `water` | the water surface to `level`: wherever the ground is lower, it floods (a lake); the ground doesn't move | the whole circle; end it on higher ground so the shore follows the ground |
| `drain` | the water surface back to the map's base level: lakes and rivers inside dry up | the whole circle |
| `cover` | cover (units there are hidden, as in a wood; proven in the game): the build paints the circle on the map's cover grid, as a `cover.toml` circle after the mod's own; the ground doesn't move. `square = true` paints a square along the map's axes instead, `radius` from its middle to each side | the cells whose centres are inside |
| `uncover` | the same, taking cover away (also `square = true`) | the cells whose centres are inside |
| `block`, `block_infantry`, `block_vehicles` | ground units can't use (all of them, infantry or vehicles): a `movement.toml` block after the mod's own; the ground doesn't move | the circle |
| `open`, `open_infantry`, `open_vehicles` | ground units can use where the map has none (the reverse of block): a `movement.toml` open after the mod's own; the ground doesn't move | the circle, in circles of 5 m or more (towns: 1.2 m) |

Block and open strokes apply in their order, so where two meet the later one wins. The Studio's **Forest** brush
isn't a brush of its own in the file: one drag writes the trees it scatters to `scenery.toml` (as Place, Area would)
and `cover` strokes over the same circles here; its Undo takes back both.

- **Water.** Water brushes run after the height brushes. They change the water surface of the two drawn meshes and
  the map's three water textures, never the ground or the `.kdt` files. Units are kept out of water by the map's
  movement graphs (ground under water is never walkable on a shipped map), so the build blocks every new water (a
  water stroke's, or ground a height brush lowered under the water) in both graphs, as `movement.toml` blocks would
  (`rusemod.nav.water_blocks`: circles over it, sampled every 640 map units or more, reaching about half a step past
  the shore at most). Drained ground stays closed to units, as it was under the water: the build warns; an `open`
  stroke over it opens it. What is
  written follows the rules every shipped map keeps (the water triangles, the per-cell patch bounds, the far mesh's
  water about 150 lower, the textures' depth, tiles and cell flags; `rusemod.water`). A height brush near water
  also keeps the water triangles and textures in step.

- **All four files together.** A map's ground is in four files (FORMATS.md §6): the close-up and far meshes the game
  draws, the gameplay ground and the camera floor (`.kdt`). Every stroke moves the points of all four inside its
  circle by a function of position and height only, so points they share stay at the same height. The map's outer
  edge never moves (the drawn mesh's curtain hangs from it).
- **The same on every PC.** Only arithmetic and square roots, which every PC rounds the same way, so two PCs build the
  same bytes. The reshaped map counts for multiplayer: its files are part of the fingerprint (§12).
- **Load order:** when several mods reshape one map, their strokes run in load order, one mod's after another's.
- **Not yet:** raising the ground above the map's highest point or below its lowest (points stop at the file's
  height range, and the build says how many did), water in the movement data, and cutting the mesh finer. The game's acceptance of moved ground is the next in-game check
  (`tools/verify_terrain.py --make-test`).

### Scenery: `maps/<map pack>/scenery.toml`

Objects a mod adds to a map (buildings, props, trees), one table each:

```toml
[[object]]
type = "TypeWarrior/Chateau_dEau_03"   # a scenery type the map already uses (the Studio lists them)
x    = 672688.0                         # map units: x grows east, y grows south
y    = 659281.0
turn = 45.0                             # degrees, from east toward south (clockwise on the minimap)
size = 1.5                              # 0.05 to 50
# optional:
solid   = false                         # walk-through (a building is solid unless this says otherwise)
stretch = 1.2                           # a further scale along the object's own y only, 0.2 to 5: a bridge's
                                        # length (the shipped maps stretch theirs 0.9 to 1.9 to fit the river)
lift    = -225.0                        # its height against the ground the game sets it on (map units; the
                                        # shipped bridges sit 130 to 850 below)
```

- **Bridges** (a type whose editor category ends `/Ponts`) are coded as bridges: never solid, and the ground along
  their deck is opened to units. The game sets such a bridge on the ground under its two ends: both must be on dry
  bank, or it tips into the water. The build's own bridges for new roads (`roads.toml`) follow that rule.

- The build adds them to the map's `output\save.boobspc` (`rusemod.scenery.add_objects`) the way DomesticNukes
  proved in the game: one object of a block placed once becomes a same-size reference to a new block at the end,
  which holds that object and the new ones. Nothing else moves; the file's MD5 is set again.
- **For looks only:** scenery doesn't block units, give cover or change the AI's map (those are other layers, FORMATS
  §6). Objects stand on the ground wherever the ground is, also after a terrain edit.
- **Only types the map already uses**: a type from another theatre isn't loaded on that map. Moving shipped objects
  isn't offered yet.
- Several mods' objects are added in load order.
- **Seen from far:** the game draws a scenery type only out to the distances its descriptor has a mode for (close
  20,000 map units from the camera, middle 100,000, far 500,000 or more by the graphics settings), and most props and
  bushes have a close or middle mode alone. So a mod's object of such a type is drawn with a copy of its type named
  `<type>_R2Seen`, which also serves the farther distances (rusemod.visibility); the map's own objects keep the shipped
  types. Seen in the game 2026-10-03: placed rocks shown at every height while the map's own vanish. The build notes
  name every type that got a copy.

The same file takes the map's own scenery away, one circle each:

```toml
[[erase]]
x      = 672688.0                       # the circle's middle (map units)
y      = 659281.0
radius = 5000.0                         # map units (about 256 = 1 m), at most 200,000
# optional:
what  = ["vegetation", "prop"]          # what it takes: vegetation, prop, decal, building (default: trees and props)
types = ["TypeWarrior/Pont_Normandie"]  # and these types, whatever they are (the only way to erase a bridge)
```

- An object goes when its place lies in the circle. Road pieces and level-design markers always stay; buildings and
  decals only when `what` names them, bridges only when `types` does.
- **Buildings and bridges are drawn only**: the map's movement still has them, so where an erased building stood stays
  closed to units, and an erased bridge's deck stays open over the water. The build says so as a warning.
- **A circle that takes trees clears a wood**: the build also opens its ground to every unit and takes the forest
  cover away there, after the mod's own movement and cover edits (`rusemod.build.cleared_woods`; proven in the game
  2026-10-01: tanks drive in, infantry there are seen).
- The Studio's **Erase** tool (Maps view) paints these circles along a drag: trees and props, buildings too when
  picked. It tints red what they take, and counts it the way the build erases (`rusemod.scenery.erase_count`).
- Erase areas are applied before the mod's own objects are added, so objects placed inside a circle stay.
- Most of a map's trees are in blocks it places many times, so the build copies each such block for the erased spot
  (`rusemod.scenery.erase_objects`; a 200 m circle in a wood adds about 300 KB). A map's scenery holds at most
  16 MB of blocks (D-Day: about 6 MB left); a build past that is refused: erase smaller areas.

### Starting points, spawns and names: `maps/<map pack>/scenario.toml`

A map's scenarios (skirmish, challenges, campaign chapters) are its `.scenario` files in `DataMap_Win.dat`
(`test\map\<map>\`, FORMATS §2). A mod moves their design items, one table each:

```toml
[[move]]
file = "leveldesign_normal.scenario"   # which of the map's scenarios (the Studio's Scenario list names them)
item = 3                               # the item's number in that file (rusemod.scenario reads them in order)
kind = "StartingPoint"                 # what it must be: StartingPoint, Spawn, LabelVille, LabelMontagne, ...
x = 458772.0                           # map units: x grows east, y grows south
y = 655380.0
rotation = 0.95                        # radians, optional: only items that have a turn
camera = 1.57                          # radians, optional, a starting point only: its warm-up camera turned round it
```

- The build writes the changed scenario files into `DataMap_Win.dat` in the modded copy; everything else in them
  stays byte for byte (all 102 shipped files write back unchanged).
- `kind` guards against a file that isn't the one the mod was made for: a move whose item is another kind is refused
  with the reason, and nothing is built.
- Moves apply in load order; two mods moving one item: the later wins.
- A moved starting point takes its opening camera along by the same offset: `PositionCamera` when it has one, and
  its warm-up camera path (`WarmupCamPath`, a path in `test\map\<map>\campath\campaths_<scenario>.ndfbin`; the match
  opens where it ends, LittleGroove's RUSE-Mod-Manager found). A path another start shares is copied first, so the
  other start's stays. A moved starting point or spawn stands at the ground's height there.
- `camera` turns a starting point's warm-up camera path round it (LittleGroove's camera ring): every keyframe goes
  round on its circle, keeping its distance and height, and its look turns as much, so the match opens framing the
  start as before, from another side. A turn of a start that isn't moved is a move to where it stands. Not yet seen
  in the game.

A mod also adds units and buildings a scenario spawns when it starts, one table each (the shipped campaigns and
Operations spawn theirs this way; skirmish maps spawn only their supply depots):

```toml
[[spawn]]
file = "leveldesign_normal.scenario"
what = "Unit_M4_Sherman"      # a unit's or building's class name (or the full class path the game's spawns use)
x = 470000.0
y = 650000.0
camp = 0                      # who gets it: -1 neutral (the default), else one of the scenario's own camps (0 up)
rotation = 0.5                # radians, optional
trucks = 25                   # a supply depot (what = "DalleBatimentDepot") only: its trucks (default 25)
```

- The build adds a design item (`TGameDesignItem` + `TGameDesignAddOn_Spawn`) to the scenario's list; moves are
  applied first, so their item numbers stay the shipped ones. It stands at the ground's height there (every shipped
  spawn does), and a depot gets its trucks (`ChampInteger`; the game gives a depot without it none).
- `what` must be a class the game finds, or the map fails to load: a class name (or a `...parametres.Classes.X`
  path) must be a class of the game's Python unit list (a mod's new unit gets one when it's a copy of a listed unit),
  and any other full path must be one a shipped spawn uses. A depot is `what = "DalleBatimentDepot"` (written as the
  shipped depots' `front.batiment_depot.DalleBatimentDepot`). Anything else is refused.
- **A skirmish game spawns only neutral items** (camp -1): a spawn for a player's side in a scenario that a
  skirmish or online entry loads is refused, since the game would leave it out without a word. A spawn left without
  a camp is written as -1 (the game reads no camp as camp 0, which in a campaign chapter is the player's).
- In other scenarios (Operations, campaign chapters) the camps are the mission's own. Its script (in `IA_Common.dat`)
  lists them (`CampList`), and a camp's number is its place in that list unless it sets its own `CampNumber` (the
  rule as LittleGroove's engine documents it, from the game's own launch code). The camp it marks `NiveauIA.Player` is
  the human player's: camp 0 in every campaign chapter (all eight campaign maps'). A spawn for a camp the mission
  doesn't list gets a warning: the game gives a spawn only to a camp the list has (not yet seen in the game). The
  Studio's Add unit offers the mission's camps, as Player or Computer with each one's country. A scenario with no
  script to read is checked against the camps its own spawns use instead.

A mod adds starting points, one table each: a player starts at a point of their team (the game's `AllianceNum`); the
game hands a team's points out in order of their place (`AlliancePriority`, lowest first), whatever the numbers are,
so a team of N players needs N points. A two-team 8-player game needs 4 in teams 1 and 2; free-for-all, 1 in each
of teams 1-8 (see `map.toml` below):

```toml
[[start]]
file = "leveldesign_3v3_v01.scenario"
team = 1              # 1 to 8
x = 2710720.0
y = 1774720.0
place = 4             # optional: the team's next place when left out
rotation = 1.2        # radians, optional: as its teammate when left out
camera = -0.5         # radians, optional: its warm-up camera turned round it, as a move's
```

- The build copies a starting point of the same team (the one with the highest place; else the nearest of any
  team): its camera moved by the same offset, a copy of its warm-up camera path moved as far (then turned by
  `camera`), its angles. It stands at the ground's height
  there, read from the map (every shipped starting point matches its ground).
- New and moved starting points are checked on the map's movement and roads as the build leaves them (after its
  blocks, bridges and roads): one where no ground unit can stand (water, a cliff, a block for every unit, off the
  map) is refused, since the game would build that player's HQ wherever it finds room, possibly far away. A wood is
  fine (the owner, 2026-10-02: an HQ there works, and supply trucks drive through woods; only tanks and other
  vehicles with flags 11/21/55 are kept out). One more than about 30,000 map units from a road gets a warning: 95% of
  the shipped starting points are that close, a pattern, not a rule.

### How many players: `maps/<map pack>/map.toml`

```toml
players = 8                   # 2 to 8 (the game's lobby has 8 seats: a map set to 10 still seats 8, tried 2026-10-02)
entry = "(6) Cotentin (3v3)"  # optional: which of the map's entries, when it has several (the map list's name)
```

- A map played online and in BATTLES has an entry in the menus (`TMultiMapInfo` in `misc\globals.cpp`, tied by GUID
  to its `TMapLoadInfo` in `mapinfo.cpp`). The build sets its `NbPlayers`, its size group `CategoryId` (the shipped
  maps: none for 2 players, 1 for 3-4, 2 for 6, 3 for 8), a two-team map's `GameType` (1v1 = 1, 2v2 = 2, 3v3 = 3;
  past 3v3 it stays as the map has it: no shipped map is 4v4, so where the menus would list a type 4 is untested),
  and the name's count ("(6) Cotentin (3v3)" becomes "(8) Cotentin (4v4)"), in `ZZ_GladPatchableWin.dat`.
- It refuses a count the entry's scenario can't seat, naming each starting point that's missing (`[[start]]` above,
  or the Studio's Add starting point). It counts a team's points, not their place numbers: every shipped entry seats
  its own count this way.
- A map that offers three teams with a count that isn't a multiple of 3 gets a warning: whether that layout is still
  offered, or gives uneven teams, is untested.
- Tried in the game on 2026-10-02 (rule test B, Strategists set to 10): the lobby showed "Number of players 10", so
  the count reaches the menus; the lobby still had 8 seats and the match loaded with 8. A count from 2 to 8 on a map
  that had fewer isn't tried yet (`TESTS.md` T12). The menus show the map's English name ("Strategists"), not the
  map-list name, so the "(10)" in that name wasn't seen.
- A team with fewer starting points than players (rule test A): the team's first lobby slot takes the point and the
  next player starts with no HQ and no units, without a message; the build refuses it for that reason.

### Cover and blocked ground: `maps/<map pack>/cover.toml`

Where units hide is baked into each map: a grid in `datasmap\<map>\mapinfo.win` (`DataMap_Win.dat`; its fourth
buffer, an SDB quadtree, FORMATS §2). A cell's byte holds layers; the game asks two (LittleGroove's notes): 0x08,
"in forest" (units there are hidden, and ambush), and 0x04, **"AI: blocked"**. Eugen drew them as zones, not from
the trees: a town or a wood a mod adds gives cover only where cover is painted. A mod paints circles (or squares), in
order:

```toml
[[paint]]
x = 801088.0        # map units, like a scenario's positions
y = 881645.0
radius = 20000.0    # a cell is painted when its centre is inside (Blitz: 1,024 cells a side, 1,280 units each)
layer = "cover"     # or "blocked"
erase = true        # optional: clears the layer instead (a wood's cover taken away)
square = true       # optional: a square along the map's axes, `radius` (map units) from its middle to each side;
                    # its edges follow the grid's rows and columns
```

- **`blocked` doesn't stop units.** It is what the AI asks about ground (its sight lines, where it builds and
  defends, and the AI grid's clearance); units move by the movement graphs alone, and walk on shipped "blocked" cells
  too (from 3% of them on SuperCrossroads4 to half on Ardennes). To keep units off, add a `movement.toml` block with
  the same x, y and radius: the build warns about a blocked paint with no block holding its middle.
- `square` is written by hand for now, here or on a `cover` / `uncover` stroke in terrain.toml: the Studio's cover
  brushes paint circles (its map view draws a square stroke of terrain.toml as a square).
- `rusemod.cover` edits the tree in place: leaves no circle touches keep their bytes, a leaf a circle's edge
  crosses becomes a node of four, and both checksums are made again. Checked on all 34 shipped grids: exactly the
  cells in the circles change.
- Circles apply in load order, a later mod's over an earlier one's.
- Whether units hide in painted cover the way they do in a wood is the next in-game check.

### Ground units can't use: `maps/<map pack>/movement.toml`

Where units can go is each map's two navigation graphs in `mapinfo.win` (buffers 1 and 2: infantry and vehicles;
`rusemod.nav`, FORMATS §2): overlapping circles units plan through. A mod takes ground away, one table each:

```toml
[[block]]
x = 871088.0
y = 881645.0
radius = 26000.0
units = "all"        # or "infantry" or "vehicles"
```

- A circle whose middle is inside a block is emptied; one reaching into it shrinks to keep clear (in steps of 320);
  the links and route costs through what's gone are taken out. The ground those circles gave up outside the block
  gets new circles (numbered after the old ones, listed in the spatial index as one more tree) and links, so only
  the block itself is lost.
- **Placed buildings are solid:** every building in the mod's `scenery.toml` becomes a block as wide as its model
  reaches, times its size (`rusemod.nav.solid_blocks`); `solid = false` on an object leaves it walk-through.
- Proven in the game (Blitz, 2026-09-30): units can't enter a blocked pit.

A mod gives ground back the same way (the reverse of a block; the Studio's Open brushes):

```toml
[[open]]
x = 871088.0
y = 881645.0
radius = 26000.0
units = "vehicles"   # or "all" or "infantry": a wood vehicles couldn't drive into
```

- Ground a map closes has no circle over it at all (FORMATS §6, movement graphs), so opening it adds circles where the graph has
  none: on the 320 grid, the largest first, each inside the open, linked to the circles it overlaps, grown out from
  the ground units already use (`rusemod.nav.Graph.open_ground`). The main graph's circles are 1,280 or more (5 m);
  inside a town's or a bridge's own movement (its local map), which decides there, the open adds circles of 320 or
  more to that map instead. Ground no unit could reach (an island the open doesn't join to the rest) stays closed,
  so the graphs stay in one piece; the old circles keep their numbers, links and road crossings.
- A file's blocks apply before its opens; the Studio's strokes after both, in their order. Where a block and an open
  meet, the later one wins. Bridges, new roads and the cover check keep clear of blocks only.
- **Water:** an open over water is allowed, with a warning naming the spot: units stand on whatever ground is
  there, so an opened river puts them on the riverbed. Buildings in an opened town are walked through.
- An open that opens nothing (the ground was open already, it is smaller than 5 m, or it touches no ground units
  use) gets a note. The AI's grid follows the vehicles' movement (`rusemod.aigrid`).

### New roads: `maps/<map pack>/roads.toml`

The roads units follow are each map's road network in `mapinfo.win` (buffer 0; `rusemod.roadnet`, FORMATS §2): points
on the road curves about 9 m apart, linked (each link's cost the game works out from its length; one flag bit, set
where the vehicles' movement has ground at the link's middle, as on most shipped links), and a k-d tree over the
links. A mod
adds a road as its line, in map units:

```toml
[[road]]
points = [[500000.0, 650000.0], [640000.0, 700000.0], [800000.0, 650000.0]]
join = 20000.0       # an end this near a road joins it (a junction); else it's a dead end (default 20000, ~77 m)
```

- The line gets points about 2,300 map units apart, linked in a chain; each end is linked to the nearest road point
  within `join`. The network's index is built again the game's way (x then y, at the middle of the links).
- Proven in the game (Blitz, 2026-09-30): **supply routes follow it** (a depot's route took a new shortcut road).
- Units plan along a road only through the movement's *crossings* (FORMATS.md, the movement graphs): a stretch of
  road through a circle, from one of its gates to another. The build makes them for the new road in both the
  infantry and the vehicles' movement, the way the shipped maps have theirs (D-Day's own made again: 92% and 95% the
  same, `tools/verify_crossings.py`), never through a `movement.toml` block or a solid building of that movement's
  units, nor across a town's buildings. A road that gets none in a movement (all of it in one circle, or through
  woods vehicles can't enter) is said in the build's notes: units go across country there. Not tried in the game
  yet.
- `paint = true` (the default) makes it look like the map's own roads, from afar and up close (**proven in the game
  on D-Day, 2026-10-02**, TESTS.md T12; the story: [ROADS.md](ROADS.md)):
  - **From afar:** it's painted into the ground's texture tiles the way the map's own roads are across: their colour
    in the middle and their shoulders, measured on up to 300 of the map's road pieces, and the same mark in the
    map's close-up ground map. Each map gets its own.
  - **Up close:** the map's own asphalt stickers are laid along it the way the map lays them (D-Day's `Route_Bitume`
    every 1,590 map units, size 2, turned along the road), each with an edge sticker either side (`Route_Bitume_Bords`,
    1,380 across). The desert maps' pairs (`RouteBitume` / `Bords_Route`, and Tunisia's) are laid the same way, at
    their own spacing; only D-Day's has been seen in the game. A map with none of them gets the paint only.
  - **Its path cleared:** the map's plants and props within 1,500 map units (about 6 m) of the road's line are taken
    off, as an erase area would, but its woods' cover and movement stay as they were, and its buildings stay.
    `keep_trees = true` (default false; the Studio's "Keep the trees on new roads") keeps the trees and bushes on
    its path (props still go): a road under the trees. Where such a road runs through one of the map's woods, the
    ground's picture shows it fainter and greyer (a third as strong); a road that clears its trees is painted
    through woods as the map's own roads are (seen in the game 2026-10-03).
  - The map's own road pieces (`Route`) and road model are written too, as before.
  `bridges = true` (the default) puts the map's own bridge kind where it
  crosses water, one piece stretched
  bank to bank (rusemod.bridges), with a floor units stand on: the floor of a shipped bridge of its kind, carried
  onto the new banks, in the map's `occlusioninfo_objectsonly.kdt` (rusemod.floors). A bridge placed by hand in
  `scenery.toml` gets one the same way.

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
| append | `P += [a, b]` | a list | the items go at the end, in the order written; one that's already in the list isn't added twice | the property isn't a list |
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
  including clones from mods loaded earlier and unnamed parts inside other objects (a weapon's ammunition). With a
  filter, `patch every TAmmunition [AmmunitionId=1120]`, only the objects whose property has that value. Objects that
  lack a property the body does math on are skipped and listed in the report, instead of stopping the build; finding
  no object at all is an error (the class or the value doesn't exist in this game build).
- **Numbers in lists keep the list's type:** an item added to, removed from or inserted into a list of numbers takes
  the type the list has (a flag added to a `uint32` list is a `uint32`), so `InitialFlagSet += [71]` is enough.

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
  - `DescriptorId`, `TrackingId`, `AmmunitionId`: one more than the highest in the game, if the class uses them as
    ids (no two of its objects share a value). A copied ammunition (a weapon's own ammo) gets its own id, so mods
    that find ammo by id (`@TAmmunition[AmmunitionId=…]`) never find the copy by mistake.
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

Built: `tools/rmod_to_mod.py` rebuilds an `.rmod` as a mod of ours, for editing (the mods rebuilt that way are kept
in the private shared repo until their authors agree). Builds and the launcher apply `.rmod` files as they are, with
LittleGroove's own engine (`src/ruse_mod_engine`, PLAN.md decision 26). The format, as our own reader read it from
37 mods:

- **One JSON file.** `$schema` `ruse-mod/v1`; `id`, `name`, `version`, `author`, `description`, `game_version` (the
  Steam build it was made on: 24670294, 24087620 and 23661872 seen). Then up to four lists:
  - `patches`: each names a pack (`dat`), a data file in it (`ndf`) and its `changes`. A change is an `action`
    (`patch`, `create`, `delete_props`), a class (`table`), how to find the object (`match`) and `set`: property →
    `{"type": T, "value": V}`. Types seen: `Float32 Int32 UInt32 Int8 Bool StringRef PathRef LocHash Guid TransRef
    ObjRef List<T> Map<StringRef,ObjRef>`. A `create` has a `local_id` (and `top_object` when it's a whole unit);
    later values say `{"$ref": local_id}`. `delete_props` lists `props`.
  - `match`: `{"ClassNameForDebug": "Unit_X"}` (most), `{"AmmunitionId": 1120}`, `{"TrackingId": "CH32"}`,
    `{"PackName": "…"}`, `{}` (every object of the class), `{"_index": "44823"}` (the object's position in the file),
    or an anchor: `{"anchor": {"root": ["ClassNameForDebug", "Unit_X"], "steps": [["WeaponDescriptor"],
    ["TurretDescriptorList", "[0]"], …]}}`, a named object plus steps into it (`"<v0>"` picks a map value by position).
  - references (`ObjRef`): an anchor as above, `{"inst": 60322}` (a position), `{"stable_ref": "ClassNameForDebug",
    "key_val": "Unit_X", "class_name": …}`, or `{"$ref"/"local_id": …}`. `TransRef` is `{"trans": "$/M3D/…"}`: an
    import of a named object.
  - `LocHash` values are the game's 64-bit text keys (§6) written byte by byte in file order: `86504ed857620000` is
    the key `N_UNI_15`.
  - `loc_patches`: a pack, a `.dic` path (language folder included) and `entries` of `key` (as above) and `value`;
    `"add": true` marks a new text.
  - `file_patches`: a pack and files as `path` + base64 `data` (music, videos, compiled `.xyz` scripts, `.scenario`
    files, icons). RUSE-Mod-Manager writes each into the pack the original file lives in (§14, question 1).
  - `sdb_patches`: per map (`DataMap_Win.dat`, `datasmap\<map>\mapinfo.win`), a `grid_size` and `layers` of `bit` +
    a zlib+base64 `mask`: terrain bit layers.
- **What carries over** (`tools/rmod_to_mod.py`):

  | In the `.rmod` | In our mod |
  |---|---|
  | match by a property | `patch @TClass[Prop=value]` (§4) |
  | `{}` | `patch every TClass` |
  | anchor | `patch shared @[Prop='v']:steps` |
  | `create`, `delete_props` | `Name is TClass ( … )`, `delete Prop` |
  | `$ref`, `stable_ref`, anchor references, `TransRef` | `~/Name`, `@TClass[Prop='v']`, `@[…]:path`, `$/…` |
  | `loc_patches` | `text/<dictionary>.csv`: `game:N_UNI_15` rows; new texts keep the original key as `game_key` |
  | `_index`, `inst`, `<v0>` steps, `file_patches`, `sdb_patches` | not carried, never guessed: the statement stays in the `.rndf` as a comment with the original's values, and the mod's README lists it |

  A few mods have recipes in the tool (a flag that is added or removed instead of the whole list rewritten, a copy
  of a unit instead of one built from scratch, a path for an object the original matched by position); each is
  written into the README as an assumption to check in-game. The manifest records the origin (`[origin]`: `format`,
  `file`, `id`, `game_version`) and the build in `[game] builds`, so the launcher can say "made on another build".
- **Builds.** Matches by property survive a build change; positions don't. A rebuilt mod is built against the
  installed game whatever build the original was made on (the values are the author's, the objects are found by name).
- **Export** (later): the subset of operations `.rmod` can express, so RUSE-Mod-Manager users can install our mods.
- **Mods that don't go together** (built: `rusemod.rmod.clashes`, 2026-09-30). Before any `.rmod` set is built, and
  live while a set is edited in the launcher, the `.rmod` files are compared (read only, no pack opened: under a
  second for 75 mods). Found after DomesticNukes put all 75 community mods in one set: the build said 0 errors and the
  game crashed (seven mods each brought their own copy of one map script, and only the last one's survived).

  | Kind | When | What happens |
  |---|---|---|
  | file | two mods replace the same whole file (a script, video, sound, picture, map file, text file or game data) with different bytes | **refused** |
  | script | two mods replace the same file inside the same archive (`.ipk`…) with different bytes | **refused** |
  | archive | one mod replaces a whole archive, another edits files inside it (either order) | **refused** |
  | create | two mods add a new object with the same name (`ClassNameForDebug`, `AmmunitionId` or `_ShortDatabaseName`) in the same file | **refused** |
  | value, text | a later mod changes values (or texts, or map layers) an earlier one changed | allowed; the later wins, and the launcher says so before Play, pair by pair |

  Refused means the build stops before building anything and names every clash; the launcher greys out Play and
  shows the reasons in a red box. Identical bytes in two mods aren't a clash. Our own mods keep their rules (§10.4,
  §10.6).

## 14. Open questions

1. Which pack receives new files and new NDF objects (depends on whether NDF can mount an extra pack)?
   RUSE-Mod-Manager's answer (§13): each file goes into the pack the original lives in (ZZ_Win.dat for music and unit
   cards, Data_Common.dat for videos, IA_Common.dat for mission scripts, DataMap_Win.dat for scenarios and terrain
   layers). Our build writes the unit-data pack and ZZ_Win.dat so far.
2. Can a mod add a whole new NDF file, or only objects inside existing ones?
3. How does the engine react to duplicate export names across files?
4. ~~Language list~~ **Answered (FORMATS.md §4):** `us`, `fr`, `ger`, `ita`, `spa`, `pol`, `ru`, `cz`, `jpn`, `sc`
   (112 `.dic` files each). New text must also update each file's character list (key `0x8000000000000000`).
5. The exact gameplay/cosmetic split (depends on what the desync checker hashes).
6. Scenario source format: design it once the binary format is decoded (M6).

## 15. The mod index (Supported mods)

Built: `src/rusemod/mod_index.py`, the launcher's "Supported mods" tab (TASKS.md D, 2026-09-29; called "Browse
mods" until Launcher 0.3.0, which added ticking several mods, the cheats' group and the first run's "Choose your
mods"). No server of ours: a
small public git repository is the index, GitHub serves its file, and GitHub Releases hold the packages.

- **The repository:** [`sneadtristen6/Ruse-Mods`](https://github.com/sneadtristen6/Ruse-Mods) (published
  2026-10-01: the 75 mods of the launcher's library, their packages in the release `mods-2026-10-01`, and a README
  that lists them with a download link each). Its `index.toml` is what the launcher reads
  (`https://raw.githubusercontent.com/sneadtristen6/Ruse-Mods/main/index.toml`); the `index_url` setting in
  `settings.json` points the launcher at another copy.
- **The file:**

  ```toml
  format = 1

  [[mod]]
  id          = "airfield-capacity"                # the mod's id (mod.toml), lowercase letters, digits and -
  name        = "Airfield Capacity"
  version     = "1.0.0"
  author      = "…"
  description = "Airfields hold 128 planes instead of 8."
  homepage    = "https://github.com/…"             # optional: "More about this mod"
  download    = "https://github.com/…/releases/download/airfield-capacity-1.0.0/airfield-capacity-1.0.0.rusemod"
  size        = 1234                               # bytes of the package
  sha256      = "…"                                # 64 hex characters, of the package
  game_build  = "24670294"                         # the build it was made on (mod.toml [game] builds)
  fingerprint = "K7Q2-M9XD"                        # from the export (§12), for join codes later
  tags        = ["gameplay", "air"]               # "cheat": a cheat or a test tool (below)
  ```

  `id`, `version`, `download` (an `https://` link), `size` and `sha256` are required; an entry that lacks one, or
  repeats an id, is skipped and listed in the launcher's log, never the whole list. A `format` above 1 means "made
  for a newer launcher". `tags` is a list of words (a single word is taken as one tag); anything else skips the
  entry.
- **Cheats and test tools:** an entry tagged `"cheat"` (any case) is shown in its own group, "Cheats and test tools
  (optional)", after the others. It is never ticked for the player, on the Supported mods tab or on the first run,
  and only the mods the player ticks are downloaded.
- **Adding a mod:** export it from the Studio (§2). The export says the file's size and SHA-256, and the Studio's
  "Share your mod" (opened after the export, and from the Mod menu) shows them with the `[[mod]]` entry ready to
  copy, `download` left empty (an entry left so is skipped). Attach the `.rusemod` to a GitHub Release (of the mod's
  own repository, or of the index repository), put its link in `download`, and open a pull request to the index
  repository that adds the entry; or post the mod in the Discussions and it's added for you. A new version is a new
  entry line: change `version`, `download`, `size`, `sha256` (a published file never changes, §12).
- **What the launcher does:** fetches the list (10 s timeout), keeps a copy in `<home>/index/` and shows that copy
  when offline, saying from when it is; marks each entry against the library ("new", "update available",
  "installed"); on Install, downloads the package, checks the size and the SHA-256 against the entry (anything else
  is deleted and refused), then adds it through the library like a file the player picked (§2). The list is
  searched by id, name, author, description and tags. Several ticked mods install in one go, one after another; one
  that fails (a download cut off, a checksum that differs) is named and the others still install. One install runs
  at a time. "See the list on GitHub" opens the repository's page.
- **The first run:** while the library is empty and the player hasn't chosen yet, the launcher opens "Choose your
  mods": the list with every mod ticked except the cheats, and Install or Skip. Either one is kept in
  `settings.json` (`launcher_mods_chosen`), so it isn't shown again. Offline it shows the copy from before; with no
  copy at all it says so and offers only Skip.
