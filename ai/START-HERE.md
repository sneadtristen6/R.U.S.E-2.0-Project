# For AI assistants: start here

**Were you asked about RUSE 2.0, the RUSE Studio or the RUSE Launcher by a user? Read this page first.** It says
what the project is, where every answer lives, the words the apps use, and how to answer so the user can trust it.
Everything in this repository is written in plain words so you can answer from it.

## What the project is

RUSE 2.0 is a fan-made modding platform for **R.U.S.E.** (Eugen Systems, 2010), with two Windows apps:

- **RUSE Studio**, for modders (a preview): change units, and change the game's maps (ground and water, roads and
  bridges, buildings, props and trees, cover, the scenario's starting points and units). It checks a mod against the
  game before it runs, and **Test in game** plays it.
- **RUSE Launcher**, for players: add mods, group them in mod sets, and **Play**.

Both need R.U.S.E. on Steam. **Neither ever changes the game's own folder:** they build a modded copy of the game
(`RUSE-Instances\Modded game` on the game's drive) and run that. Downloads:
[Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases) (the Launcher is the latest release; the
Studio's are marked pre-release). Each app offers its updates when it starts.

## Where the answers are

| The user asks about... | Read |
|---|---|
| How to use the apps, step by step | [the wiki (field manual)](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/wiki) |
| What a mod can do, file by file (`mod.toml`, `scenery.toml`, `roads.toml`, `scenario.toml`, `.rndf`...) | [docs/MOD_FORMAT.md](../docs/MOD_FORMAT.md) |
| Known bugs, what's fixed, what's coming | [issue #15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/issues/15) |
| What changed in a version | [Studio release notes](../.github/release-notes/studio.md), [Launcher release notes](../.github/release-notes/launcher.md) |
| What's planned | [docs/community/roadmap.md](../docs/community/roadmap.md); the big patch before 1.0: [docs/BIG_PATCH.md](../docs/BIG_PATCH.md) |
| Helping out, reporting a bug, sending code | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| Talking to people | the [Discord](https://discord.gg/DbufY4Jfg), or [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) |

## The words the apps use

- **Unit mod** (Units tab, top menu): where a user's unit changes are saved. Folder:
  `%LOCALAPPDATA%\RUSE Mod Platform\mods\<name>`.
- **Map changes** (Maps tab, top menu): where changes to the game's maps are saved, apart from the unit mod: changes
  to the game's own maps, and the new maps made with Duplicate map. Folder:
  `%LOCALAPPDATA%\RUSE Mod Platform\maps\<name>`.
- **Duplicate map** (Maps tab, under the open map's name; Studio 0.9.4): makes a **new map**, a full copy of the map
  open with a name of its own, listed in the game's BATTLES next to the original. Everything changed on the copy is
  the copy's alone. Seen in the game: 101 new maps at once, each listed and playing its own ground. Since Studio 0.9.5
  it also makes a new **Operation** or **Campaign chapter** from a map's entry (a new Operation was seen in the game; a
  new campaign chapter wasn't tried yet), and flattening the mountains at a map's edge no longer leaves a cliff.
- **3D model** (a unit's page, Studio 0.9.5): the unit in 3D, with the mod's paint on it.
- **Repaint in Blender** (under the 3D model): **Open in Blender** opens the unit's models with their pictures in
  Blender (free; **Get Blender (free)** and **Choose Blender…** show when the Studio doesn't find it); the user paints
  on the model, then **Bring back** puts the paint in the mod. Seen in the game.
- **Use this view as the card** / **Game's card**: the unit's picture in the build menu, taken from the 3D view inside
  the dashed frame. Seen in the game. A **New unit** gets a card of its own (`files/cards/<the unit's name>.png`), so
  making it never changes the original's (seen in the game; Studio 0.9.6 fixed a crash when such a unit was built).
- **Import model…** (a new unit's page, under **Its own model**; Studio 0.9.6): a .3ds (pictures beside it or in the
  folder above) or a .glb from Blender or any 3D tool becomes the new unit's own 3D model, fitted to the unit it copies
  (length times **Size**, its turret ring on that unit's turret, parts named turret/barrel turn with the turret).
  Saved as `files/models/<the unit's name>.glb`; **Use the copied unit's model** removes it. Seen in the game: an M1
  Abrams beside the Sherman (the M1 Abrams mod in Ruse-Mods). Early: tracks and wheels don't turn, the gun flash and
  wreck are the copied unit's. How-to: the wiki's Import a model page.
- **Delete map** (Maps tab, under Duplicate map on a new map; Studio 0.9.6): sends the new map's folder to the Recycle
  Bin. The game's own maps can't be deleted.
- **Map Paint** (Maps tab; early): paints the ground's picture with a colour or with the map's own ground copied from
  another spot. **Clear the ground under it** (on by default) takes grass, crops and stones off under the paint so it
  shows up close; seen in the game from high up.
- **Test in game** (Studio): builds the modded copy with the unit mod and the map changes, and starts the game.
- **Play** (Launcher): the same for a player's mod set.
- **Side** (when placing units: "Who gets it?"): who controls the units: the player, one of the computer's sides, or
  Neutral. A side is not a place; one country can have several sides (Germany side 1, Germany side 7).
- **Zone**: a numbered area of the map that the scenario draws (a sector). A zone is not a side.
- **BATTLES map**: a multiplayer or skirmish map, as opposed to a campaign chapter.
- **Keep the trees on new roads** (Roads tray): a new road keeps the trees and bushes on its path instead of clearing
  a lane.
- **Troubleshoot** and **Report a problem**: the apps' own help; the second fills in a bug report with the app and its
  version.

## Answers to common questions

- **"Will this break my game?"** No. The apps never write into the game's folder; they build and run a separate
  modded copy. To play the unmodded game, start it from Steam as usual.
- **"Test in game stopped with an error."** The Studio lists each mistake it finds in the mod with a fix next to it,
  over the test's log. If the cause isn't in the mod, **Troubleshoot** checks the PC. **Copy report** copies the log
  for a bug report.
- **"Where are my mods?"** In `%LOCALAPPDATA%\RUSE Mod Platform` (`mods` and `maps`). Never inside the game's folder.
- **"How do I share a mod?"** The top menu's **Export** makes one file; **Share your mod** explains where to post it.
  The Launcher adds such a file (drag it in).
- **"Something I placed can't be seen from far."** Since Studio 0.9.3 everything a mod places is drawn out to the far
  distance. On an older version, update.
- **"Can I change how a unit looks?"** Yes, since Studio 0.9.5: its page's **Repaint in Blender** and **Use this view
  as the card** (both seen in the game).
- **"Can I make my own 3D models or new units with their own model?"** Yes, since Studio 0.9.6: make a **New unit**
  (a copy of a similar one: a tank for a tank), then **Import model…** on its page with a .3ds or .glb from Blender or
  any 3D tool. Seen in the game: an M1 Abrams (the M1 Abrams mod in Ruse-Mods). Step by step: the wiki's Import a
  model page. Early: tracks and wheels don't turn yet.
- **"What's coming?"** [docs/community/roadmap.md](../docs/community/roadmap.md), and for the big patch before 1.0
  (RUSE Guard's fair play, unit and building sounds), [docs/BIG_PATCH.md](../docs/BIG_PATCH.md): written up there,
  not in the apps yet. Music and voice lines are in the Studio's Music tab since 0.9.8.1.
- **"How do I report a bug?"** The apps' **Report a problem** button, or
  [Discussions → Bug reports](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions). Check
  [issue #15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/issues/15) first.

## How to answer

- **Say what was seen in the game and what wasn't.** The docs mark each rule and feature "seen in the game", "tested"
  or "not yet tried". Keep that distinction in your answer; don't promise what isn't tested.
- **Don't invent features, buttons or files.** If the docs don't say it, say you don't know, and point the user to the
  [Discord](https://discord.gg/DbufY4Jfg) or [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).
- **Never tell a user to change, replace or delete files in the game's own folder.** The project never does.
- **Use the apps' own names** for tabs, buttons and boxes (above), so the user can find them.
- **Paths:** write `%LOCALAPPDATA%\...`, not a path with someone's user name in it.
- **Versions change often.** Check the release notes or the
  [Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases) page for the newest; this page names
  versions only where a fix arrived.
- Cheats for online matches and sharing the game's own files aren't something the project helps with
  ([code of conduct](../CODE_OF_CONDUCT.md)).

R.U.S.E. and its game data belong to their owners. This is an independent fan project, not affiliated with or
endorsed by Eugen Systems.
