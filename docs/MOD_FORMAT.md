# Mod Package Format: Draft Spec v0.1

Status: draft for discussion (2026-09-28). Nothing here is final until M2 proves it in-game.

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
    studio.baseunite.csv   the Studio's new units' names (rewritten by the Studio; goes into the game's unit names)
  files/
    replace/<game path>    replaces an existing game file (cooked from a source format)
    add/<new path>         adds a new file (under mods/<mod id>/...)
    game/<pack>/<path>.rdelta  a game file changed whole, as a delta (the Studio's Files tab; see §7)
    game/<pack>/mods/<mod id>/<path>  a file added to a game pack (§7)
  maps/<MapId>/            map sources (see §8)
  scripts/<map>/<part>/    the game's mission scripts it changes, as the Studio saves them (see §9)
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

[made_with]                         # the tool that made it: Export mod… writes it; the mod list shows it
tool    = "RUSE Studio"
version = "0.9.8"
page    = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project"

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
| Export path | `$/GFX/Everything/Descriptor_Unit_M4_Sherman` | a named object, by the game's own names |
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
classes or from scripts; truly new mechanics would take more than data, which is outside this project.

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

Built: `src/rusemod/loc.py`, run by `ruse build`.

```csv
key,game_key,us,fr,ger,ita,spa,pol
r2.unit.us_marines.name,R2MARINE,US Marines,Marines US,US-Marines,Marines USA,Marines de EE. UU.,Piechota morska USA
```

- **The file name picks the game's text table:** `text/baseunite.csv` goes into the unit names (`baseunite`, in every
  language). A table the game doesn't have is an error. A file called `<anything>.<table>.csv` goes into that table
  too (`text/studio.baseunite.csv` is the Studio's, which it rewrites; a mod's hand-written `text/baseunite.csv` stays
  its own).
- **Using a text:** `NameInMenuToken = loc('r2.unit.us_marines.name')` in a `.rndf` file becomes that row's game key.
  A `loc()` that no mod in the set defines is an error.
- **Where it goes:** into the modded copy's texts, in every language. Texts are cosmetic: they don't change the
  fingerprint (§10.8). The `dev` language gets the `us` text.

- **Language columns** use the game's own language folders: `us fr ger ita spa pol cz ru jpn sc` (from
  RUSE-Mod-Manager's notes; confirmed on the game). The usual codes are accepted too:
  `en de it es pl cs ja zh`. Missing cells fall back to `us`.
- **Text keys are readable names.** The game's keys pack a name of up to 10 characters (0-9, A-Z, _, a-z) into a
  number. Each row gets one: the `game_key` column sets it (`R2MARINE`), or when it's
  empty, the builder makes one from the manifest's `text_prefix` plus a number, assigned in sorted `key` order so it's
  the same on every PC (`R2000001`, `R2000002`, …). A key the game or another mod in the set already uses is an error
  that names both.
- Existing game texts can be overridden by name, `game:M_D_01`, or by number, `game:0x…`, for a key that isn't a name.
- The Studio keeps the game texts it changes (the All values tab's "Change the words…", a town's name on the Maps tab)
  in `text/studio-words.<table>.csv`, a `game:<key>` row each with every language written: a missing cell would give
  that language the English words.

## 7. Assets

| Kind | Source format | Notes |
|---|---|---|
| Texture | PNG | a repaint of a game picture (below) |
| Model | glTF 2.0 (+ textures) | a new unit's own model (below) |
| Sound | WAV | a new song or sound in place of the game's (below) |

- `files/replace/<game path>.png` repaints an existing picture: the Studio's **Open in Blender** and
  `ruse export-model` write the pictures with their paths, so a repaint goes back where it came from.
- **Built for textures (2026-10-03, `rusemod.unitlook`; seen in the game):** the picture is the texture's own size
  (what `ruse export-model` and the Studio's Open in Blender write). Its alpha channel is never used: the texture keeps
  the game's alpha (on vehicles the player's side colour and shine) unless a grey picture of the same name ending in
  `.alpha.png` instead of `.png` is there too.
  Only the parts that were painted change; the rest stay the game's, byte for byte. A later mod's picture wins over
  an earlier one's. A repaint changes every unit drawn with that texture (one picture can serve a nation's whole
  infantry).
- **A unit's card** (its picture in the build menu, the unit's `TextureForInterface`) is replaced the same way, at the
  card's own size (360 x 184 for most units), everywhere the build menu shows it. Seen in the game.
- **A new unit's own card:** a copied unit starts with its source's card, so the two look alike in the build menu.
  `files/cards/<the new unit's name>.png` (`files/cards/Descriptor_Unit_R2_M4_Sherman_Tall.png`), the source's card's
  size, gives it a card of its own: the build points the new unit's `TextureForInterface` at a card of its own and
  adds it wherever the build menu shows the source's. The source's card is left as it is. A picture there for a unit
  no mod in the set makes is an error. The Studio writes it there when the card is made on a new unit's page, and
  removes it with the unit. Not yet seen in the game.
- **A new unit's own model:** `files/models/<the new unit's name>.glb` (`files/models/Descriptor_Unit_R2_M1_Abrams.glb`)
  gives a copied unit a model of its own. The build points its model part (`GfxDescriptor.MeshDescriptor.FileName`) at
  a new model of its own, following the source's bones: the parts in the node called `chassis` move with the hull,
  those in `tourelle_01` turn with the turret. Each picture in the .glb becomes a texture of its own. The file is what
  `ruse import-model` (or the Studio's *Import model*) writes from a .3ds or
  .glb from any 3D tool: fitted to the source unit (its length, its turret's turning point, its ground), in the axes
  `ruse export-model` writes, so it opens in Blender and can be changed there and saved over (keep the node names).
  The source's wreck stays its own. A model there for a unit no mod in the set makes is an error. Not yet seen in the
  game.
- **The Studio's unit page** shows the unit's 3D model, turning, with the mod's paint on it (a .glb made once per game
  build in the Studio's cache). A dashed frame on it marks the card: *Use this view as the card* saves what's inside
  it, over a backdrop like the game's cards, as the mod's card; *Game's card* removes it. Under it, *Open in Blender* writes the unit's models and pictures to a work folder
  outside the mod and opens Blender with them in its Texture Paint workspace, each texture linked to its picture;
  *Bring back* asks that Blender to save the paint (it also saves on Ctrl+S, on its "Save paint" button and every
  10 seconds) and copies the pictures painted since into the mod's `files/replace`. The game's models never go into
  a mod.
- **Songs and sounds (2026-10-07, `rusemod.sound`; heard in the game: the main menu song, the songs of battle lists
  1 and 2 and a unit's voice lines, each replaced this way; the rest not tried yet):** `files/replace/<the sound's path in
  ZZ_Win.dat>.wav` plays in place of the game's sound, e.g.
  `files/replace/gen_sound/ww2/sons/atp_music/battle1.ess.wav` for the battle song "Battle 1". A 16-bit WAV, any
  length; one channel, two or six (as the game's own sounds have), at its own rate. The build makes the game's kind
  of file from it, once (the build cache keeps it), and updates what the game reads about the sound wherever the game
  keeps that. A later mod's WAV wins over an earlier one's. Music and most unit voices can be replaced this way; the
  short sound effects of the other kind can't yet (the build says so). The Studio's **Music** tab lists every song
  the game plays by where it plays (the menus, the three lists battles play from, the end of a match, mission goals,
  the campaign chapters and Operations that name them, and the few no part of the game plays), plays each one, and
  replaces it in a small editor of its own: a sound file dropped or chosen (the Studio's window reads WAV, MP3, OGG
  and FLAC itself), cut with two handles, faded in and out, made louder or quieter (or as loud as the game's), heard,
  then *Use this* saves it in the mod as above, in the game song's own format. Nothing to install. A unit's page has
  a **Voice** section the same way: what the unit says in the game, by moment (the game's own words for them: Move,
  Attack, Spawn...), each line heard and replaced in the same editor. A unit speaks the lines of its nation and kind,
  so the page names the units that share them (a line changed there is heard from all of them); a copied unit speaks
  its source's.
- **New songs (2026-10-07; heard in the game: a new song in battle lists 1 and 2):** `files/music/list1/<name>.wav` (and `list2`, `list3`) adds a
  song of the mod's own, with a name of its own, to that one of the three lists battles play from: the build makes
  the song (as above), adds it beside the game's songs with its description, and adds a new song object naming it at
  the end of the list. The name is letters, digits and `_`. The Music tab's **Add a song…** under each list writes it
  there (the editor asks for its name); the song then shows in that list, marked New, with Change… and Remove.
- **A map's background sound (2026-10-07; not tried in the game yet):** under the battle each map plays one long
  sound over and over, made of three stereo layers played together (how loud the game plays each, and when, isn't
  known yet). Many maps share one. `maps/<map pack>/background_1.wav` (and `_2`, `_3`) puts a layer of the mod's own
  in place of that layer: a 16-bit stereo WAV at 48,000 a second, any length (a shorter one is repeated until the
  longest ends; the layers not given stay the map's). The build makes a background for that map alone from them, so
  the maps that shared the old one keep it. `maps/<map pack>/sound.toml` with `background = '<another background, as
  the Studio names it>'` starts the map from the one another map plays instead (its layers then come from that one).
  A new map gets its own the same way. The Maps tab's **Background sound…** shows the map's: what it starts from (its
  own, or the one another map plays), and its three layers, each heard and replaced in the Music tab's editor; *Hear
  all three together* plays them as the build will put them together.
- `files/add/mods/<mod id>/<name>.<source ext>` adds a new file, referenced from `.rndf` by its game path.
- **Any game file, whole (2026-10-08, `rusemod.gamefiles`; not tried in the game yet):** the Studio's **Files** tab
  shows every file in the game's packs; *Change it with a file of mine…* puts a file of the modder's in place of the
  game's, and *Add a file of mine to this pack…* adds a new one. The safeguards the owner asked for:
  - The game's packs are never written: the build puts the files into the modded copy only.
  - A changed file is kept in the mod as a **delta**, `files/game/<pack>/<its path in the pack>.rdelta`, never as
    the game's file: only the bytes the modder changed are in it, with a check of the game file it was made from.
    When the game's file isn't that one any more (a game update), the build stops and says so; the mod has to be
    made again from the new file.
  - Every file is checked as its kind before the game gets it, the changed file as the delta makes it as well as an
    added one: textures, PNG pictures, text tables, game data, scenarios, XML, fonts (TrueType and OpenType, one or a
    collection), the menus made in Flash and the shader file. A kind not on that list is refused (songs and sounds go
    through the Music tab, above). Videos are checked too (WebM, a VP9 picture, Vorbis sound) but not taken yet: they
    wait for a safe way to hand the game a video from outside. A file inside a pack inside the pack is changed the
    same way: `files/game/<pack>/<the inner pack's path>/<its path in it>.rdelta`.
  - No scripts or programs from outside: a menu's layout, shapes and words can change, its code stays the game's
    (and a new menu holds none); the shaders stay the game's. (Programs RUSE 2.0 has approved: planned.)
  - A file a mod adds goes in its own folder in the pack, `files/game/<pack>/mods/<mod id>/...`, so it never stands
    in for one of the game's.
  - At most 32 MB a file and 256 MB of game files a mod, for now. (Later, maybe: a higher limit for particular packs,
    for an overhaul.)
  - Two mods changing the same file: the lower one in the load order wins, the build says which, and the Launcher
    shows it before Play with *Use the one from <the other mod>*, which moves that mod just below (§10.4).
  - Value patches (`.rndf`) run on top of a changed game data file, the same as on the game's own.

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
  sound.toml      # the background sound it starts from (§7)
  background_<n>.wav  # a layer of its background sound of the mod's own (§7)
```

A map's files live in a folder named after the map's pack name (`TwoIslands` for Centre of Gravity,
`SuperCrossRoads4` for Blitz: the Studio's Maps tab names each map's); a mod holds only the files it needs. A mod can also make a **new map**, a copy of a
shipped one under a name of its own, which its other files then edit like any map (below). Terrain from scratch comes
later (M8).

### A new map: `maps/<NewName>/map.toml` with `copy_of` (built: `rusemod.newmap`)

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from, by its pack name (this one is Blitz)
entry = "(2) Blitz"            # optional: which of its entries, by the map list's name: a BATTLES map (needed when it
                               # has several), or an Operation's or a campaign chapter's (the copy is then one too)
players = 4                    # optional: as on any map (below), for the copy
picture = "menu.png"           # optional: its own pictures in the menus, PNGs in this folder (below; any map can)
wide_picture = "menu-wide.png"
start_dots = true

[name]                         # what the menus call it, or one name for every language: name = "Blitz Twin"
us = "Blitz Twin"              # English, which the languages left out fall back to
fr = "Blitz jumeau"            # us fr ger ita spa pol ru cz jpn sc (en de it es pl cs ja zh work too)
```

- The folder's name is the new map's pack name: a letter, then up to 39 letters, digits and `_` (`BlitzTwin`). The
  mod's other files in that folder (`terrain.toml`, `scenery.toml`, `scenario.toml`, `cover.toml`, `movement.toml`,
  `roads.toml`) edit the copy; the shipped map stays as it was.
- The build adds the copy's own map, its place in the map list and in BATTLES (after the maps of its size), its
  scenario, its cover and movement, and its name in every language: each a copy of the shipped map's, pointed at the
  copy.
- Everything else is the shipped map's, only read: its models, sounds, lighting, camera paths, menu pictures (unless
  `picture` or `wide_picture` gives its own: below) and in-mission texts. The copy plays the shipped entry's scenario
  (Blitz: `leveldesign_normal.scenario`), so its `scenario.toml` names that file; its sectors get a zone map of their
  own, so `[sectors]` can change them without changing the shipped map's.
- The ids come from the name, so every PC that builds the mod gets the same files: a multiplayer game needs the mod on
  both PCs, like any mod. The copy isn't offered in ranked games (the shipped map's ladder place stays its own).
- **An Operation or a campaign chapter:** `entry` names it (`"Challenge - 1v1 39 Blitz_2 (Anzio)"` for Anzio,
  `"M02_Tunisie_chapter1"` for Tunisia's first chapter). The copy is then a new Operation, last in OPERATIONS, or a
  new chapter, last in the campaign, with the shipped one's briefing, pictures, bonus times and population caps. Its
  mission script, cutscenes and dialog are the shipped one's. **Seen in the game:** a new Operation (Anzio Twin). A
  new chapter isn't tried yet; the game
  opens a chapter only when the one before it in its list is finished, so a copy put last opens after the campaign's
  last chapter.
- Refused, with the reason: `copy_of` a map the game hasn't got, or one BATTLES doesn't list (campaign and Operation
  maps); a name the game's map list already has, or one starting `flat_` (the game's test maps); a map with several
  BATTLES entries and no `entry`; two mods making maps of one name; `name` without `copy_of` (a shipped map's menu name
  isn't changed here).
- **The Studio makes one:** **Duplicate map** (Maps tab, under the open map's name) asks for the name, writes this
  file in the map changes (a new one is made when none is picked) and copies the changes made to the map so far.
  The new map is listed right after the map it copies and opens like any map: the view reads the shipped map's files
  and shows the copy's own edits on top, which go to `maps/<NewName>/`. The folder name comes from the menu name
  ("Blitz at Dusk" → `BlitzAtDusk`, a number added when it's taken).
- **Seen in the game:** a new map is listed in BATTLES and plays its own ground (Blitz Twin
  flattened, with a hill in the middle); 101 new maps at once were all listed, the map row scrolling, and played.
  Names over about 35 characters are cut off in the menus. Copies of maps other than Blitz build but weren't tried in
  the game yet. Flattening the mountains at a map's edge left a wall along it (the outermost row of points kept its
  height); the edge now moves with the ground and the curtain hanging from it follows (built, not yet seen in the
  game).
- **Start blank:** **New map: start from scratch…** (Maps tab, before a map is open, and on the open map's panel) or
  Duplicate map's *Start from* Blank Terrain or Blank Ocean (a Battles map's copy; `rusemod.presets`). The window
  says why a new map sits on a game map (the game can't load one made from nothing) and asks which one it's *Built
  on*: that map gives it its size, its player count and its starting points, nothing else. It
  writes the copy's files from the shipped map's own: the whole map flat (land, or the sea over it), everything on it
  erased, its roads and bridges taken out, only the starting points kept, the sectors over the whole map, and its own
  menu pictures with `start_dots` (below). Seen in the game (both, 2026-10-05).

### A map's pictures in the menus: `picture`, `wide_picture`, `start_dots` in `map.toml` (built: `rusemod.menupicture`)

Every map shows two pictures in the game's menus: a **big picture** (640 x 360, a view of its land or sea) and a **3D
map** (680 x 200, the map as a slab with a white dot where each player starts). A mod gives a map its own:

```toml
picture = "menu.png"           # the big picture: a PNG in the map's folder
wide_picture = "menu-wide.png" # the 3D map: a PNG there too (left out: made from `picture`)
start_dots = true              # the build draws the start dots on the 3D map (needs `wide_picture`)
```

- Any PNG, any size up to 8192 a side: each is cut to its shape from its middle and scaled (see-through pixels, as
  round a 3D map, keep the edges they meet clean).
- **A new map** (`copy_of`) gets picture files of its own; the map it copies keeps its pictures. **A shipped map**
  (`map.toml` without `copy_of`) has the pictures its BATTLES entry shows replaced (or the entry `entry` names): a
  themed mod can picture every map its own way. A picture another of the map's entries shows too changes there as
  well; the build and the Studio say which.
- `start_dots`: the white dots aren't part of the picture: the build draws one on each place players start, where the
  map's starting points are once the mods' edits are in (`rusemod.menudraw`), so moving a starting point moves its
  dot. The 3D map must be drawn the way the Studio draws one: a blank map's, or one made in Blender from the Studio's
  scene. The game's own 3D maps have their dots drawn in, so `start_dots` needs `wide_picture`.
- **The Studio:** **Menu pictures…** (Maps tab, under the open map's name) shows both as the menus will, with **Pick a
  PNG…**, **Back to the game's own** and the start dots for each map, and **Make in Blender…**: Blender opens the
  map's own 3D model (its ground and water with its ground picture, or a blank map's flat sea or grass) as two scenes,
  *Big picture* and *3D map*, their cameras set like the game's; the modder changes anything, clicks *Save menu
  pictures* in Blender, then **Bring back** (the big picture framed like the game's own, start dots on). The scene is
  kept outside the mod and opens as it was left (**New scene** starts again). `rusemod.menuscene` writes it,
  `rusemod.blender_menu` builds it in Blender.
- **Seen in the game (2026-10-05):** Blank Ocean's and Blank Terrain's own pictures with the start dots the build
  drew, and a copy of D-Day with pictures made in Blender (**Make in Blender…**, **Bring back**) beside D-Day's own,
  on the Choose map screen: the big picture is the card in the middle, the 3D map the slab under the map's name. A
  shipped map's own pictures replaced (no `copy_of`) are built but not tried in the game yet.

### Reshaping an existing map's ground (built: `rusemod.brush`, `rusemod.terrain_edit`)

```
maps/TwoIslands/
  terrain.toml    # brush strokes on that map's ground, applied in order (the Studio rewrites this file)
```

The folder's name is the map's pack name (`TwoIslands` for Centre of Gravity; the Studio's Maps
list shows it under each map). The file holds strokes, one dab of a brush each:

```toml
[[stroke]]
brush  = "hill"      # hill, raise, lower, crater, plateau, flatten, smooth, ramp, water, drain, cover, uncover, …
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
| `paint` | the Studio's Map Paint **Colour**: lays `colour` ("#rrggbb") on the ground's picture at `weight` (its opacity, 0..1, 1 when left out), on every level of both tile sets; the ground doesn't move. With `clear` (true when left out) the build also takes off what hides it up close (below). Seen in the game | round hump weighting (a hard edge: full nearly to the edge) |
| `stamp` | Map Paint's **Texture**: lays the map's own picture from (`x` + `sx`, `y` + `sy`) at `weight`, as the map was before any paint, at every level; the map's close-up picture takes that spot's values too, so it blends up close as the spot does. `clear` as for `paint`. Seen in the game with `clear` (a light field copied into a riverbed reads as a road: copy from ground like its surroundings) | round hump weighting |

```toml
[[stroke]]
brush  = "paint"
x      = 806088.0
y      = 881645.0
radius = 10400.0
colour = "#e02020"   # paint: the colour, red, green, blue in hex
weight = 1.0         # paint, stamp: the opacity, 0..1

[[stroke]]
brush  = "stamp"
x      = 741088.0
y      = 959645.0
radius = 26000.0
sx     = 110000.0    # stamp: where the ground it copies lies, from each point it paints (world units)
sy     = 110000.0
weight = 1.0
clear  = false       # paint, stamp: leave what hides it up close (true when left out: it goes)
```

Paint strokes apply in their order, each over what's below it (a stroke on the same place again builds up), before
the mod's new roads are painted, so a road drawn over paint shows on top.

**What hides paint up close** (`clear`, `rusemod.groundpaint.paint_clearing`): near the camera the game draws the map's
ground stickers, low plants (crops, grass, bushes, flowers) and stones over the ground's picture, so paint under them
shows only from afar (seen in the game). With `clear` the build takes them off wherever the stroke
paints at least half strength (its opacity times its fall-off): every sticker, low plant and stone that reaches in,
by its own size (a sticker's descriptor extent, a plant's model; times the size it's placed at), since a sticker
20 m across centred outside a patch still covers its edge. Trees, buildings, the cover and the movement stay.
Seen in the game: a patch cleared this way shows at every height. A stroke weaker than half clears nothing.
Clearing a very large patch copies many of the map's shared blocks and can pass what its scenery holds (see Erase
areas); the build then refuses it: paint smaller, or set `clear = false` on the biggest strokes.

Block and open strokes apply in their order, so where two meet the later one wins. The Studio's **Forest** brush
isn't a brush of its own in the file: one drag writes the trees it scatters to `scenery.toml` (as Place, Area would)
and `cover` strokes over the same circles here; its Undo takes back both.

- **Water.** Water brushes run after the height brushes. They change the water surface of the two drawn meshes and
  the map's three water textures, never the ground units walk on. Units are kept out of water by the map's
  movement graphs (ground under water is never walkable on a shipped map), so the build blocks every new water (a
  water stroke's, or ground a height brush lowered under the water) in both graphs, as `movement.toml` blocks would
  (`rusemod.nav.water_blocks`: circles over it, sampled every 640 map units or more, reaching about half a step past
  the shore at most). Drained ground (a bed the water left) has no ground in the movement, so the build opens it to
  units (its own opens over the dried bed, the widest stretches in big circles). A water stroke with
  `block = false` (the Studio's Water over the whole map: a square over all of it, its surface Strength above the
  ground's middle height) is a thin layer units go under, like a navy map's painted sea: the movement takes its
  place for dry ground, so it closes nothing, and the old water under it (a river, the sea) is opened as a drained
  bed is. It is drawn as any water is (seen in the game on Blank Ocean, 2026-10-05; units going under it not tried
  yet). What is written follows the rules every shipped
  map keeps (`rusemod.water`). A height brush near water also keeps the water triangles and textures in step. A
  water stroke sets the water at the map's outer edge too, and the water's side hanging from the edge follows it:
  left at the old rivers' levels, the edge stood as walls of water round Blank Ocean's sea (seen in the game,
  2026-10-05, and gone in the game the same day with this fix).

- **All four files together.** A map's ground is held four times over: the close-up and far ground
  the game draws, the ground units walk on, and the camera floor. Every stroke moves the points of all four inside its
  circle by a function of position and height only, so points they share stay at the same height. The map's outer
  edge moves like the rest: the curtain hanging from it (the map's side when zoomed out) follows, the water's side
  where sea or river met the edge folds away under ground raised above the water, and the camera floor's ring past
  the edge moves with the edge beside it. A stroke that goes toward a height (plateau, flatten, level, ramp, smooth)
  also takes away the drawn meshes' own bumps off the gameplay ground as far as it flattens, so a flattened map is flat
  from far too; the camera floor keeps its height above the ground (not yet seen in the game).
- **What was drawn for the old ground follows.** The road model (the white roads seen from high up and in the map
  view) holds the ground's height at every point; it moves with the ground (on flattened Blitz Twin it stood off the
  roads painted on the ground). A riverbed the strokes raise flat (an old hollow, more than 1.5 m deep, that the new
  ground no longer has, in a stretch that reaches the old ground's water; one still a dip is left, and so is a dry
  valley raised flat, whose picture was a field's already) still showed its old banks: up close the river's rock
  stickers, from high up the banks painted into the picture. Its picture (both tile sets) and its
  close-up map are mended from both banks (`rusemod.mend`), and the ground stickers, low plants and stones that reach
  into it are taken off; trees, buildings, cover and movement stay. When taking them off would make the map's
  scenery bigger than a map holds, they stay, with a warning (the pictures are mended all the same). That look passed
  in the game, laid on a test copy; the build doing it itself is not seen yet, nor the road model
  moving.
- **Big maps: kept, and shared across the cores.** The mend looks only where the old ground had water under the
  strokes, in squares of 2 km, and shares them and the picture tiles out to worker programs (one per core but one;
  the same bytes as one program). A reshaped map is kept in the build cache (`rusemod.mapkeep`, named by its pack,
  the strokes, its water depth and the app's code), so the next build with the same strokes on it takes its ground
  from there. Measured, all of Blitz Twin flattened: the mend about 7 minutes in 0.9.6, now 65 s with 7 workers; the
  whole build 239 s the first time, 121 s the next (the map from the cache in 3 s).
- **The same on every PC.** Only arithmetic and square roots, which every PC rounds the same way, so two PCs build the
  same bytes. The reshaped map counts for multiplayer: its files are part of the fingerprint (§12).
- **Load order:** when several mods reshape one map, their strokes run in load order, one mod's after another's.
- **Not yet:** raising the ground above the map's highest point or below its lowest (points stop at the highest
  and lowest the map can hold, and the build says how many did), water in the movement data, and cutting the mesh finer. The game's acceptance of moved ground is the next in-game check.

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

- The build adds them to the map's scenery (`rusemod.scenery.add_objects`) the way DomesticNukes proved in the
  game. Nothing else moves.
- **For looks only:** scenery doesn't block units, give cover or change the AI's map (those are other layers).
  Objects stand on the ground wherever the ground is, also after a terrain edit.
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
radius = 5000.0                         # map units (about 256 = 1 m), at most 4,000,000 (any map, whole)
# optional:
what  = ["vegetation", "prop"]          # what it takes: vegetation, prop, decal, building (default: trees and props)
types = ["TypeWarrior/Pont_Normandie"]  # and these types, whatever they are (the only way to erase a bridge)
```

- An object goes when its place lies in the circle. Road pieces and level-design markers always stay; buildings and
  decals only when `what` names them, bridges only when `types` does.
- **A circle that takes buildings opens its ground**: the build opens the whole circle to every unit, after the mod's
  own movement edits (`rusemod.build.cleared_woods`). A town's movement closes whole blocks (houses, yards, walls),
  so the circle opens whole, not each house's own ground. Proven in the game 2026-10-04: tanks and
  infantry drive through where Blitz's town stood, and infantry there no longer act as in a town. Buildings erased by
  name only (`types`, without `"building"` in `what`) keep their ground closed, with a warning.
- **Bridges are drawn only**: the map's movement still has them, so an erased bridge's deck stays open over the
  water. The build says so as a warning.
- **A lighthouse takes its light with it**: a lighthouse's turning light belongs to the map's effects (beside its
  rain, seagulls and sounds), not to the lighthouse, so erased lighthouses left their lights turning over Blank
  Ocean's empty sea (seen in the game 2026-10-05). The build gives such a map its own copy of its effects without
  those lights, and its scenarios start the copy; the game's own effects keep them for every map that keeps its
  lighthouses (`rusemod.lighthouses`; D-Day has two, Swamps and Blitz one each). Seen in the game 2026-10-05: Blank
  Ocean's lights gone.
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

A map's scenarios (skirmish, challenges, campaign chapters) each have a file of their own (the Studio's Scenario
list names them). A mod moves their design items, one table each:

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

- The build writes the changed scenarios into the modded copy; everything else in them stays byte for byte.
- `kind` guards against a file that isn't the one the mod was made for: a move whose item is another kind is refused
  with the reason, and nothing is built.
- Moves apply in load order; two mods moving one item: the later wins.
- A moved starting point takes its opening camera along by the same distance, and its warm-up camera path too (the
  match opens where it ends, as LittleGroove's RUSE-Mod-Manager found). A path another start shares is copied first, so the
  other start's stays. A moved starting point or spawn stands at the ground's height there.
- `camera` turns a starting point's warm-up camera path round it (LittleGroove's camera ring): every keyframe goes
  round on its circle, keeping its distance and height, and its look turns as much, so the match opens framing the
  start as before, from another side. A turn of a start that isn't moved is a move to where it stands. Not yet seen
  in the game.

A mod takes the map's own items out, one table each (the Studio's Take out, or Take out every depot / every map name):

```toml
[[remove]]
file = "leveldesign_3v3_v01.scenario"
item = 41                              # the item's number in that file, as for [[move]]
kind = "Spawn"                         # Spawn (a depot, a unit, a building), LabelVille, LabelMontagne, Name,
                                       # CircularZone or RectangleZone: never a StartingPoint, every player needs one
```

- The match leaves the item out: the build takes it off the list of items the scenario starts with. The item stays
  in the file, so every other item keeps its number and the mod's other moves still name the right ones
  (LittleGroove's RUSE-Mod-Manager deletes a placement the same way). Seen in the game: every supply depot and town
  name of D-Day taken out, the match played without them.
- `kind` guards as it does for a move. Two mods taking one item out: once is enough.

A mod makes the map's sectors reach over the whole map (the Studio's Sectors over the whole map):

```toml
[sectors]
whole_map = true   # every scenario of the map: each place its sectors leave out goes to the sector nearest it
```

- Every scenario of the map with sectors gets them made again: each place a sector held stays in it, and each place
  none held (the sea, the edges) goes to the sector nearest it, so the sectors meet the map's edges all round. The
  sectors keep their numbers, names and labels; neighbours share one border, point for point.
- The sectors drawn and the sectors played are made from the same outlines, so they agree, each point at the
  reshaped ground's height. The borders are traced on a grid of the map (4 m on D-Day): the map's own borders move
  by a few metres at most.
- A sector with another inside it can't be made (none of the shipped scenarios has one): that scenario keeps the
  map's own sectors, and the build warns.
- The last mod that has a `[sectors]` table decides.
- Seen in the game (2026-10-05, a drained D-Day, then Blank Ocean and Blank Terrain): the sectors meet the map's
  edges all round, and a ruse card takes on a sector that was sea.

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
- In other scenarios (Operations, campaign chapters) the camps are the mission's own. Its script lists them,
  and a camp's number is its place in that list unless it sets its own (as LittleGroove's engine documents it). The
  camp it marks as the player's is the human player's: camp 0 in every campaign chapter (all eight campaign maps'). A spawn for a camp the mission
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

### The map's own items' values: `maps/<map pack>/items.toml` (built: `rusemod.scenario`; not yet seen in the game)

A mod changes some values of the map's own design items, one table each (the Studio's Maps tab: pick an item, then
This item's values; LittleGroove's Details panel):

```toml
[[set]]
file = "leveldesign_normal.scenario"   # which of the map's scenarios, as for [[move]]
item = 41                              # the item's number in that file, as for [[move]]
kind = "Spawn"                         # Spawn, CircularZone, RectangleZone, Name, LabelVille or LabelMontagne
camp = 2                               # a spawn: who gets it, -1 neutral or one of the scenario's camps (0 up)
trucks = 40                            # a supply depot: its trucks, 0 to 1000 (the shipped depots have 15 to 72)
# radius = 75000.0                     # a circle zone: its radius, in map units
# width = 120000.0                     # a rectangle zone: its width and height, in map units
# height = 80000.0
# name = "zone_beach"                  # a spawn, named point or zone: the name the mission scripts find it by
# text = "BirelGoubi"                  # a town's or hill's name: the game text it shows (below)
```

- A file of its own beside `scenario.toml`: the build applies it after that file's moves, removes, starting points
  and spawns and after `places.toml`, to the map's own items only (numbered as for `[[move]]`).
- Each value is written in the type the item already has it in. A spawn without a camp gets one, and a supply depot
  without trucks gets them, as new spawns get them; a spawn, named point or zone without a name gets one; any other
  value an item hasn't got is refused. A name is one line of up to 200 letters a scenario file keeps in one byte each.
- `kind` guards as it does for a move. A skirmish scenario's items stay neutral: a camp other than -1 there is
  refused, as it is for a new spawn.
- Zones and names are used by the scenario's mission script (§9): a size changed here changes where things happen,
  and a name changed here is lost to a script that still uses the old one.
- A town's or hill's name on the map is one of the game's texts, in its `ville_multi` table: the label's text names
  the key by its first 10 letters (the shipped scenarios, 2026-10-07: every town's and 31 of the 42 hills'; the other
  hills' texts, like "Hill 111", have a space and name no key). The Studio changes its words in every language with a
  `game:<key>` row (§6) in the map project's `text/studio-words.<table>.csv`.
- An item's turn is kept with its move (`rotation` in its `[[move]]`), for an item that has one (most named points,
  spawns and starting points, some zones; labels have none).

### New names, named points and zones: `maps/<map pack>/places.toml` (built: `rusemod.scenario`; not yet seen in the game)

A mod adds town and hill names, named points and zones to a map's scenarios, one table each (the Studio's Maps tab:
Add a name or zone; LittleGroove's + Placement):

```toml
[[place]]
file = "leveldesign_normal.scenario"   # which of the map's scenarios
kind = "Name"                          # LabelVille, LabelMontagne, Name, CircularZone or RectangleZone
x = 655000.0                           # where, in map units (the build puts it at the ground's height)
y = 500000.0
name = "landing_spot"                  # a named point (needed) or a zone: what the mission scripts find it by
rotation = 0.5                         # a named point or zone: its turn, in radians (a label has none)
# radius = 50000.0                     # a circle zone (needed)
# width = 50000.0                      # a rectangle zone (both needed)
# height = 50000.0
# text = "Spring_k3x"                  # a town's or hill's name (needed): the game text it shows
```

- Each is written as most of the game's own of its kind are (checked byte for byte against shipped ones,
  2026-10-07), added at the end of the scenario's items like a spawn, so the map's own items keep their numbers.
- A new town's or hill's name shows a game text of the mod's own: the Studio adds a row with a `game_key` of its own
  (a key of up to 10 letters, `Spring_k3x`) to the map project's `text/studio-words.ville_multi.csv` (§6), its words
  the same in every language until the words panel changes one; taking the label back takes the row with it.
- Named points and zones matter only to a mission script that uses their names (§9: the Studio's script editor).

### How many players: `maps/<map pack>/map.toml`

```toml
players = 8                   # 2 to 8 (the game's lobby has 8 seats: a map set to 10 still seats 8, tried 2026-10-02)
entry = "(6) Cotentin (3v3)"  # optional: which of the map's entries, when it has several (the map list's name)
```

- A map played online and in BATTLES has an entry in the menus. The build sets its number of players, its size group
  (as the shipped maps of that many players have it), a two-team map's game type (1v1, 2v2, 3v3; past 3v3 it stays
  as the map has it: no shipped map is 4v4, so how the menus list one is untested), and the name's count
  ("(6) Cotentin (3v3)" becomes "(8) Cotentin (4v4)").
- It refuses a count the entry's scenario can't seat, naming each starting point that's missing (`[[start]]` above,
  or the Studio's Add starting point). It counts a team's points, not their place numbers: every shipped entry seats
  its own count this way.
- A map that offers three teams with a count that isn't a multiple of 3 gets a warning: whether that layout is still
  offered, or gives uneven teams, is untested.
- Tried in the game on 2026-10-02 (Strategists set to 10): the lobby showed "Number of players 10", so
  the count reaches the menus; the lobby still had 8 seats and the match loaded with 8. A count from 2 to 8 on a map
  that had fewer isn't tried yet. The menus show the map's English name ("Strategists"), not the
  map-list name, so the "(10)" in that name wasn't seen.
- A team with fewer starting points than players: the team's first lobby slot takes the point and the
  next player starts with no HQ and no units, without a message; the build refuses it for that reason.

### Cover and blocked ground: `maps/<map pack>/cover.toml`

Where units hide is baked into each map: a grid of cells with layers, two of which matter here (as LittleGroove's
RUSE-Mod-Manager paints them): "in forest" (units there are hidden, and ambush), and **"AI: blocked"**. Eugen drew them as zones, not from
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
- `rusemod.cover` changes exactly the cells in the circles and nothing else (checked on every shipped map).
- Circles apply in load order, a later mod's over an earlier one's.
- Whether units hide in painted cover the way they do in a wood is the next in-game check.

### Ground units can't use: `maps/<map pack>/movement.toml`

Where units can go is each map's movement, one for infantry and one for vehicles (`rusemod.nav`). A mod takes
ground away, one table each:

```toml
[[block]]
x = 871088.0
y = 881645.0
radius = 26000.0
units = "all"        # or "infantry" or "vehicles"
```

- The ground inside a block is closed to those units, and the ground around it is given back, so only the block
  itself is lost.
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

- Opening adds ground for those units where the map has none, joined to the ground they already use
  (`rusemod.nav.Graph.open_ground`), in pieces of 5 m or more (in a town or on a bridge, 1.25 m). Ground no unit
  could reach (an island the open doesn't join to the rest) stays closed: an order onto such ground would crash
  the game. The map's own ground and roads stay as they were.
- A file's blocks apply before its opens; the Studio's strokes after both, in their order. Where a block and an open
  meet, the later one wins. Bridges, new roads and the cover check keep clear of blocks only.
- **Water:** an open over water is allowed, with a warning naming the spot: units stand on whatever ground is
  there, so an opened river puts them on the riverbed. Buildings in an opened town are walked through.
- An open that opens nothing (the ground was open already, it is smaller than 5 m, or it touches no ground units
  use) gets a note. The AI's grid follows the vehicles' movement (`rusemod.aigrid`).

### Worked-out answers: `maps/<map pack>/solved.bin` (built: `rusemod.solved`; not seen in the game yet)

A map changed all over asks the build some long questions. On the most extreme map we have (a drained sea), working
out where units can go takes two of the PC's cores several minutes, beside the ground being painted. The modder
waits for that once. Players shouldn't: the Studio's **Export mod…** puts what the build worked out into the mod, and
a player's build takes it from there.

- **Never written by hand.** The export writes it; delete it any time and the build works everything out again.
- **No game files in it.** It holds our own numbers only: where the new movement circles go. Nothing in it is a
  file of the game's or a piece of one, and a mod with this file still changes data only.
- **Locked with the game.** The file is locked with a key made from the game's own movement file for that map, as
  shipped. Without the game it can't be read, the key is in no code of ours, and a file somebody changed without the
  game doesn't open. It isn't hidden from someone who has the game: their copy has to read it.
- **Only for the exact same question.** Every answer is named by a fingerprint of everything it was worked out from
  (the map's movement as the build has it, the zones, the limits). Another version of the game, another version of
  the mod or another mod changing the same map asks another question, gets no answer and works it out.
- **Never trusted as it is.** A build weighs every answer it takes (on the grid, inside the opened ground, off the
  ground units already have, reachable) and works out the ones that fail. A file that doesn't open is left out with
  a note; the build goes on without it.
- **The same game files either way.** On the extreme map the build with the answers gave the same game files, byte
  for byte, as the build that worked them out (nothing kept: the modder's build and a player's first build with the
  answers both under 10 minutes, the player's the shorter). So the fingerprint and the join code (§12) don't depend
  on who had the file.
- **Today it carries the movement step only.** The other long map steps (ground painting, riverbeds) are still made
  on each PC from the mod's strokes, then kept in the build cache.

### New roads: `maps/<map pack>/roads.toml`

The roads supply trucks and units follow are each map's road network (`rusemod.roadnet`). A mod adds a road as its
line, in map units:

```toml
[[road]]
points = [[500000.0, 650000.0], [640000.0, 700000.0], [800000.0, 650000.0]]
join = 20000.0       # an end this near a road joins it (a junction); else it's a dead end (default 20000, ~77 m)
```

- The line gets points about 2,300 map units apart, linked in a chain; each end is linked to the nearest road point
  within `join`.
- Proven in the game (Blitz, 2026-09-30): **supply routes follow it** (a depot's route took a new shortcut road).
- Units plan along a road only where the movement says they can follow it. The build adds that for the new road in
  both the infantry and the vehicles' movement, the way the shipped maps have it for theirs, never through a `movement.toml` block or a solid building of that movement's
  units, nor across a town's buildings. A road that gets none in a movement (all of it in one circle, or through
  woods vehicles can't enter) is said in the build's notes: units go across country there. Not tried in the game
  yet.
- `paint = true` (the default) makes it look like the map's own roads, from afar and up close (**proven in the game
  on D-Day, 2026-10-02**):
  - **From afar:** it's painted into the ground's texture tiles the way the map's own roads are across: their colour
    in the middle and their shoulders, measured on up to 300 of the map's road pieces, and the same mark in the
    map's close-up ground map. Each map gets its own.
  - **Up close:** the map's own asphalt stickers are laid along it the way the map lays its own, each with an edge
    sticker either side. The desert maps' are laid the same way; only D-Day's have been seen in the game. A map with
    none of them gets the paint only.
  - **Its path cleared:** the map's plants and props within 1,500 map units (about 6 m) of the road's line are taken
    off, as an erase area would, but its woods' cover and movement stay as they were, and its buildings stay.
    `keep_trees = true` (default false; the Studio's "Keep the trees on new roads") keeps the trees and bushes on
    its path (props still go): a road under the trees. Where such a road runs through one of the map's woods, the
    ground's picture shows it fainter and greyer (a third as strong); a road that clears its trees is painted
    through woods as the map's own roads are (seen in the game 2026-10-03).
  - The map's own road pieces and road model are written too, as before.
  `bridges = true` (the default) puts the map's own bridge kind where it
  crosses water, one piece stretched
  bank to bank (rusemod.bridges), with a floor units stand on: the floor of a shipped bridge of its kind, carried
  onto the new banks (rusemod.floors). A bridge placed by hand in
  `scenery.toml` gets one the same way.

A mod also takes the map's own roads and bridges out (the Studio's Roads dock: Take out the map's roads, Take out
the map's bridges), a line before the `[[road]]` tables:

```toml
take_out = ["roads", "bridges"]   # either, or both
```

- `"roads"`: the map's road network goes, with every link the movement has to it (supply trucks and units should
  then plan their way across country, as on a map with no roads); so do the roads drawn from high up and on the map
  table, and the road stickers up close (asphalt, cobbles, dirt tracks, their edges and junctions). The mod's own
  `[[road]]` go in afterwards, in the look the map's own had, and must still make one network between them.
- `"bridges"`: the map's own bridges are erased, both the objects and the model the map draws them with, and the
  floors units stood on are sunk under the ground. The movement over their decks stays: units still cross there, on
  the ground under them. Drain the rivers (the water brushes) to cross anywhere.
- Every mod's `take_out` counts: one taking the roads out and another the bridges takes both.
- Seen in the game (2026-10-05, a drained D-Day): the map's road lines gone. Not tried yet: supply trucks and units
  planning across country without them, and the bridges checked one by one.

## 9. Scripts

- A mod in our own format brings no scripts or programs of its own: the build refuses them (below). New units get
  their place in the game's unit list from the build itself.
- **The game's mission scripts** (the scripts of its maps in `IA_Common.dat`: the campaign's chapters, challenges,
  Operations) are the one exception (the owner, 2026-10-07: "allow a tool to edit mission scripts"; LittleGroove's
  Mission Script editor brought over). A mod changes one by bringing its whole text, as the Studio's script editor
  (the AI tab) saves it, with the script as the game runs it beside it:

  ```
  scripts/<map>/<part>/<file>.py     the text (a game script's map, part and file as the Studio's list names them:
  scripts/<map>/<part>/<file>.xyz    scripts/m04_cotentin/scripting_chapter1/effetmap.py); and the game's form of it
  ```

  The Studio only saves a text the game's own Python (2.5.1) reads, and makes the `.xyz` with it. A build with that
  Python at hand makes the `.xyz` again from the text and stops when the two differ (changed by another tool); a
  build without it (the Launcher) uses the `.xyz`, and stops when only the text is there. A script the game hasn't
  got, or one changed by two mods, stops the build too. Each mod that changes scripts gets a warning: scripts run
  inside the game, so a player should use it only if they trust its author. The game's own text again (saved
  unchanged) takes the mod's script out. Not tried in the game yet.
- A RUSE-Mod-Manager mod (`.rmod`, §13) may replace the game's own scripts; the build warns when it does.

## 10. Build semantics

A mod is a list of instructions ("set this", "multiply that", "clone this unit"), never a copy of game files.
Every build starts from the untouched game and replays the instructions of every mod in a fixed order, so the result
depends only on the game build, the mods and their order.

### 10.1 Steps

1. **Resolve:** pick the mods and versions and put them in load order (§10.6).
2. **Read:** turn each mod's `.rndf`, `.csv` and `files/` entries into operations (the patch IR).
   Every operation remembers its mod, file and line.
3. **Apply:** start from the base game for this build and apply the operations one at a time: mods in load order;
   inside a mod, files sorted by path; inside a file, top to bottom. Then the `final` operations, in the same order
   (§10.6).
4. **Check, cook, pack, fingerprint.**

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
- **Math on an absent property is an error**, because the engine's default isn't stored in the data (a default
  `Nationalite` of 0 is simply not written). The fix is to `set` it first.
- **Deleting is risky.** Game scripts look objects up by name (`Database.GetObject`),
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
| change a game file whole → the same (§7) | B's file wins; the Launcher offers *Use the one from A* (moves A below B) | warning |

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
- **A copy of that moment:** a clone copies its source as it is at that point in the load order. Later patches to the
  source don't reach the clone, and patches to the clone never reach the source.
- **The game's unit list:** R.U.S.E. only uses the units it lists, so the build lists every copy of a listed unit
  too, as its source is listed (named after the copy's `ClassNameForDebug`). A unit made from scratch, or a copy of an
  unlisted one, gets a warning: the game ignores it. Deleting a listed unit is an error for now (the list would point
  at nothing).
- **Mods never contain scripts or programs** (`.py`, `.exe`, `.dll`, `.bat`, the game's compiled scripts, …): the
  build refuses them, apart from the game's own mission scripts a mod changes under `scripts/` (§9). Listing new
  units (above) is the only such change a build makes itself, from one fixed pattern, and checked.
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
   final-fixes stage and ModuleManager's `:FINAL` work the same way.)
5. **Conditional blocks:** `when mod <id> ( … )` applies its contents only if that mod is in the set; `when not mod`
   is the opposite, and a version range can follow the id (`when mod better-ai >=1.2`). A mod named in a `when`
   counts as an optional dependency, so a compatibility patch always runs after the mod it patches. (Like
   ModuleManager's `:NEEDS`.)

### 10.7 Worked example

Three mods on build 190852. The prices are invented.

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
| **Gameplay** | the game's data (unit data, maps, scenarios, even the few files that are probably the interface only), everything about a map's ground, scenery, cover and movement, and scripts | must be identical on every PC |
| **Cosmetic** | pictures, models, animations, sounds, videos, fonts, the interface's look and the texts | may differ between players |

- A mod set counts as gameplay if it changes even one gameplay file. Only gameplay files go into the fingerprint (§12).
- A file whose content ends up identical to the game's own doesn't count as changed.
- Cautious on purpose: when in doubt, a file is gameplay. A wrong "gameplay" only makes players match when they didn't
  strictly have to; a wrong "cosmetic" causes desyncs.
- To confirm in the 2-PC tests, models especially: in some games a model's size changes what
  can be seen or hit.

### 10.9 Determinism

- stable ordering everywhere, no timestamps
- canonical number formatting
- fixed compression settings
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

- **Shape follows Modrinth's `.mrpack`:** each resolved file lists `path`,
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

- **Canonical content:** the game's data files are hashed as their content, uncompressed, so compression can't change
  the fingerprint. Every other file is hashed as written.
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

Built: `tools/rmod_to_mod.py` rebuilds an `.rmod` as a mod of ours, for editing. Builds and the launcher apply
`.rmod` files as they are, with LittleGroove's own engine (`src/ruse_mod_engine`).

- **One JSON file**, RUSE-Mod-Manager's own format: the mod's name, version, author and the game build it was made
  on, then its changes: values of the game's data (objects found by a property such as `ClassNameForDebug`, or by
  their place in a file), texts, whole files it replaces (music, videos, scripts, scenarios, pictures) and the
  map layers it paints.
- **What carries over** (`tools/rmod_to_mod.py`):

  | In the `.rmod` | In our mod |
  |---|---|
  | match by a property | `patch @TClass[Prop=value]` (§4) |
  | `{}` | `patch every TClass` |
  | anchor | `patch shared @[Prop='v']:steps` |
  | `create`, `delete_props` | `Name is TClass ( … )`, `delete Prop` |
  | `$ref`, `stable_ref`, anchor references, `TransRef` | `~/Name`, `@TClass[Prop='v']`, `@[…]:path`, `$/…` |
  | texts | `text/<table>.csv`: `game:N_UNI_15` rows; new texts keep the original key as `game_key` |
  | objects found by their place in a file, whole files, map layers | not carried, never guessed: the statement stays in the `.rndf` as a comment with the original's values, and the mod's README lists it |

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
  | script | two mods replace the same file inside the same archive with different bytes | **refused** |
  | archive | one mod replaces a whole archive, another edits files inside it (either order) | **refused** |
  | create | two mods add a new object with the same name (`ClassNameForDebug`, `AmmunitionId` or `_ShortDatabaseName`) in the same file | **refused** |
  | value, text | a later mod changes values (or texts, or map layers) an earlier one changed | allowed; the later wins, and the launcher says so before Play, pair by pair |

  Refused means the build stops before building anything and names every clash; the launcher greys out Play and
  shows the reasons in a red box. Identical bytes in two mods aren't a clash. Our own mods keep their rules (§10.4,
  §10.6).

## 14. Not yet

- A mod can't add sounds yet, nor a whole new data file: its new objects go beside the ones they are copied from.
- The gameplay and cosmetic split (§10.8) is cautious on purpose; the two-PC tests will tell where it can relax.

## 15. The mod index (Supported mods)

Built: `src/rusemod/mod_index.py`, the launcher's "Supported mods" tab (2026-09-29; called "Browse
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
  copy (`download` left empty: an entry left so is skipped) and the credit line to paste where the mod is shared
  ("Made with RUSE Studio <version> (<the project's page>)", from the manifest's `[made_with]`). **Publish to the mod
  list** (`StudioApi.publish_mod`) opens the list repository's **Add my mod** form
  (`.github/ISSUE_TEMPLATE/add-mod.yml` there) with its boxes filled in from the file (`mod_index.submit_url`: name,
  version, credit, what it does, the entry, the game build, made with), and saves a `.zip` copy of the file beside
  it (the same bytes; GitHub takes `.zip` attachments) with its folder open. The modder says what the mod changes and
  what its code does, attaches the `.zip` and submits. Nothing is sent from the Studio. On the list repository, a
  workflow (`check-submission.yml`, `tools/check_submission.py`) reads the attached file without running anything in
  it and comments: programs, files outside the game's data archives and paths that leave the folder are against the
  list's guidelines (`GUIDELINES.md`); changes to the game's own scripts get a maintainer's look. A maintainer then
  tries the mod, uploads it to a release and adds the entry. A pull request that adds the entry works too. A new
  version is a new entry line: change `version`, `download`, `size`, `sha256` (a published file never changes, §12).
- **Credit:** an entry may carry `made_with = "RUSE Studio 0.9.8"` (the Studio's export writes it into the entry);
  launchers that don't know the field skip it.
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
