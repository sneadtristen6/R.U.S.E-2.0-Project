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
| Whether something was tested in the game, and how to test it | [docs/TESTS.md](../docs/TESTS.md) |
| New roads, bridges and how they look | [docs/ROADS.md](../docs/ROADS.md) |
| Known bugs, what's fixed, what's coming | [issue #15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/issues/15) |
| What changed in a version | [Studio release notes](../.github/release-notes/studio.md), [Launcher release notes](../.github/release-notes/launcher.md) |
| What's planned | [docs/PLAN.md](../docs/PLAN.md) (the "Now" section first) |
| Helping out, reporting a bug, sending code | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| The game's file formats (for programmers) | [docs/FORMATS.md](../docs/FORMATS.md) |
| Talking to people | the [Discord](https://discord.gg/DbufY4Jfg), or [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) |

## The words the apps use

- **Unit mod** (Units tab, top menu): where a user's unit changes are saved. Folder:
  `%LOCALAPPDATA%\RUSE Mod Platform\mods\<name>`.
- **Map changes** (Maps tab, top menu): where changes to the game's maps are saved, apart from the unit mod. It
  holds changes to the game's own maps; it doesn't make a brand-new map. Folder:
  `%LOCALAPPDATA%\RUSE Mod Platform\maps\<name>`.
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
