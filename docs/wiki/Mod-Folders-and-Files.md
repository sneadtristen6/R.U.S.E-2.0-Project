# Mod folders and files

> **Reference** · You never need to touch these by hand: the Studio writes them. This page is for when something
> looks wrong, or for modders who edit files directly.

## Where things are

| What | Where |
|---|---|
| The Studio's mods | `%LOCALAPPDATA%\RUSE Mod Platform\mods\<mod>` (paste that into File Explorer's address bar) |
| The launcher's installed mods | `%LOCALAPPDATA%\RUSE Mod Platform\library` |
| Modded copies of the game | `RUSE-Instances` on the same drive as the game (for example `D:\RUSE-Instances`) |
| The game itself | Never changed |

## Inside a mod

```
my-mod/
  mod.toml                    the mod's name, id, version, author (required)
  src/studio.rndf             unit changes made in the Studio
  text/studio.baseunite.csv   names of new units
  files/replace/gen/...png    a unit's paint (from Blender) or a unit's card, under the game texture it changes
  files/cards/<unit>.png      a new unit's own card in the build menu, named after the new unit
  files/models/<unit>.glb     a new unit's own 3D model (Import model), named after the new unit
  maps/<map pack name>/       one folder per map the mod changes:
    terrain.toml                ground brushes (also water, cover and block brushes)
    scenery.toml                buildings, props and trees placed
    scenario.toml               starting points and spawns moved, units added
    cover.toml, movement.toml   cover and movement written by hand
    map.toml                    how many players; or, for a new map, the map it copies and its name
```

## The map folder's name is the map's pack name, not its title

Players know a map by its title (**Blitz**); the game's files use its pack name (**SuperCrossRoads4**). A map folder
must use the pack name: `maps/SuperCrossRoads4/`, not `maps/Blitz/`. Every map's pair is in [[Map names|Map-Names]],
and the Studio's map list shows both: the title first, the pack name after the dot.

## A new map

A mod can add a map of its own to BATTLES: a copy of a shipped map or a blank start, under a name of its own, that the mod's other
files then reshape. Its folder's name is the new map's pack name (letters, digits and `_`), and its `map.toml` says
which map it copies and what the menus call it:

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from (its pack name: Blitz)

[name]
us = "Blitz Twin"              # English, used where a language is left out
fr = "Blitz jumeau"
```

`maps/BlitzTwin/terrain.toml` and the rest then edit the copy, and Blitz stays as it was. Any map BATTLES lists can be
copied; campaign and Operation maps can't. Two players need the same mod to play it together, like any mod. New
maps play in the game (2026-10-03), and the Studio's **Duplicate map** makes this folder for you.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| The zip holds a folder inside a folder | The launcher looks one folder down and finds it. Two or more down, it says it found no mod. | Zip the folder that holds `mod.toml`. |
| A map folder named after the map's title | The build says it isn't a map's pack name. | Rename it to the pack name. |
| A file edited by hand has a typo | The mod check names the file and the line. | Fix it, or **Set aside** in the Studio. |
| A `.exe`, `.dll` or PC script inside the mod | Refused: mods carry data only (the game's own mission scripts, as the Studio saves them, are the one exception). | Take it out. |

If a file can't be read, the Studio never writes over it: your work is never lost. **Set aside** renames it
`<name>.broken.toml` next to the original.
