# Tasks for cloud sessions

Cloud sessions have no game files. They do design, code and tests here, on a branch, and open a pull request to
`main`. The PC session reviews, tests in-game where needed, merges and tags releases. Read
[PLAN.md](PLAN.md) §10 first (the order and the rules), then the task below. Everything that isn't in the task's
scope is out of scope.

**Rules for every task**
- Public code is data-only: it never patches, injects into or reads addresses of RUSE.exe. MIT; never copy
  RUSE-Mod-Manager's code (LITTLEGROOVE_STUDY.md is a study, not a source).
- Never commit game files or anything extracted from the game.
- Tests: `PYTHONPATH=src python3 -m unittest discover -s tests` (Windows: `py -3`). Add tests for what you build;
  the suite must pass on Linux and Windows (GitHub runs both on every push).
- Screen words go in `src/ruse_studio/words.toml` or `src/ruse_launcher/words.toml` in all ten languages, plain
  words a non-programmer understands; `tests/test_studio.py` checks that every word used in the JS exists.
- `fake-api.js` gets the same new calls, so the page works in a plain browser (the UI preview).
- Keep the change small enough to review; explain it in the pull request in plain words. Update README's
  "Code so far" lines, [PLAN.md](PLAN.md) §10 and [LOG.md](LOG.md) for what you finished.
- Branch names: `cloud/<task>`. Do not release (no version bump, no tag): the PC session does that after an
  in-game check.

## Task A: new units from the Studio (Studio 0.5) — branch `cloud/studio-new-unit`

**Status (2026-09-29): code done, in a pull request from `cloud/studio-new-unit`.** The PC session tests it in-game
(an M4 Sherman copy) and releases 0.5.0.

**Goal:** a non-programmer makes a new unit from a unit's page and presses "Test in game".

Today the Studio edits a unit's numbers in place (`src/ruse_studio/api.py` `edit`, saved by `edits.py` into the
mod's `src/studio.rndf`, MOD_FORMAT §5) and "Test in game" builds the mod with the engine. The engine already
makes new units correctly: a `clone` statement in `.rndf` (MOD_FORMAT §10.5), its identity (`rusemod.identity`:
own id, debug name, build-menu slot), its class in the game's Python unit list (`rusemod.pyscript`, PLAN
decision 23), and its name in all languages (`rusemod.loc`, `text/*.csv`). Proven in-game (C5–C7, LOG.md §1).

**Build:**
1. A "New unit" button on a unit's page. It asks for: the new unit's name (one name, used for every language, with
   an optional per-language override later), its price (one number, all five battle dates), and its menu: keep
   the source's nation and factory, or pick another nation (`nations()`) and one of that nation's factories.
2. `api.new_unit(source, name, price, nation, factory)` writes the clone, the price patch and the name into the
   mod (`edits.py` grows a clone section; keep `src/studio.rndf` readable by `rusemod.rndf`), then returns the
   new unit's address so the page opens it. The new unit is listed under its nation with a marker (new), and its
   page can be edited like any other. Deleting a new unit removes its clone, patches and texts.
3. The address of a new unit: `$/GFX/Everything/Descriptor_Unit_<Name>` with a safe ASCII name; refuse names
   that clash with the game or the mod.
4. Tests in `tests/test_studio.py`: the mod file written for a new unit, the build of that mod down to the game
   data on the fixtures (like the v0.3 shared-parts test), listing and deleting, name clashes.

**Done when:** the tests pass, the browser preview shows the flow with `fake-api.js`, and the PR describes what a
player sees. The PC session then makes one in-game (an M4 Sherman copy) and releases 0.5.0.

## Task B: mod sets made in the launcher (Launcher 0.2) — branch `cloud/launcher-mod-sets`

**Goal (PLAN §10 step 3):** players never touch a file.

Today (`src/ruse_launcher/api.py`): the launcher finds the game, lists mod sets read from
`%LOCALAPPDATA%\RUSE Mod Platform\sets\*.toml` (hand-written), and Play builds a set's modded copy and starts it.
The owner's verdict: "this needs to be worked out, it will be hard for people who aren't techy."

**Build:**
1. A mod library: "Add a mod file…" installs a mod folder or zip (a folder with `mod.toml`, MOD_FORMAT §2) into
   the launcher's own library folder, checking it first (the rules engine says whether it's valid, and which game
   build it was made for). Dropping a mod file onto the window does the same. The library lists each mod's name,
   version, author and description; a mod can be removed.
2. Mod sets made on screen: "New mod set" (name it, tick the mods in the library, order them), then edit, rename,
   duplicate and delete from the set's menu. The launcher stores them itself (the same TOML files are fine as
   storage, but nothing on screen mentions files).
3. Lists update by themselves when something changes (the API returns the fresh lists after every call), and every
   error says what to do next in plain words.
4. Tests in `tests/test_launcher.py`: the library (add a folder, add a zip, refuse an invalid mod, remove), sets
   (new, edit, rename, duplicate, delete, order kept), and that Play still builds from a set made on screen.

**Done when:** the tests pass, the browser preview shows the flow with `fake-api.js`, and the PR describes what a
player sees. The PC session then tries it with the real game and releases 0.2.0.

## Later (not yet assigned)

- **Browse mods** (PLAN §10 step 5): a GitHub repository as the mod index, and a launcher tab that installs from it.
- **Join codes in the launcher** (MOD_FORMAT §12).
