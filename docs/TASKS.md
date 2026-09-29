# Tasks for cloud sessions

Cloud sessions have no game files. They do design, code and tests here, on a branch, and open a pull request to
`main`. The PC session reviews, tests in-game where needed, merges and tags releases. Read
[PLAN.md](PLAN.md) §10 first (the order and the rules), then the task below. Everything that isn't in the task's
scope is out of scope.

## Handover from the cloud session (2026-09-29, evening): read this first

The PC session ran out of credit in the afternoon; the cloud session carried on. The owner is not a coder: **the PC
session runs every command itself; the owner only installs, plays and screenshots.** Give click-level steps.

**All of it is merged into `main` (later that evening):** #2, #4, #5 (the launcher: mod sets, a mod as one file,
Browse mods), #3 (the community mods), #6, #7, #8 (the terrain editor: the engine, the Studio's brushes, the ramp
and Start over) and #9 (this note). Each was re-read in full and green on the repository's own checks (tests on
Linux and Windows, CodeQL) before merging, under the standing rule below; the branches clashed only in the docs and
were joined by merging `main` into each (both sides kept). `main` passes 422 tests. **No version bump, tag or
release was made:** those wait for the owner's in-game tests. The red `github-advanced-security` check on those
pull requests is GitHub's own scanner failing on GitHub's side before it reads any code ("The requested model is
not supported"); it is commented on each; ignore it, or turn it off under Settings → Advanced Security → Code
scanning (the AI/Copilot switch; keep CodeQL on).

**What the PC session does now, in order:** 1) `git pull` on `main`; 2) the hill test below (one game start);
3) the owner's other tests, one game start each (below; each pull request's "Test for the owner" section has the
steps); 4) releases once the tests pass: the launcher (B, C and D together; 0.2 or 0.3, the PC session picks) and
the Studio (A, the brushes and the ramp: 0.6). A failed test goes back to the cloud with exactly what happened, not
into a release. The cloud session that did all this ran out of credit right after; its next piece of work is
painting the ground (below), not started.

**The one test that matters most: the hill (#6).** It decides whether the game accepts ground we move. Run
`py -3 tools\verify_terrain.py` (read-only; every map should say OK), then
`py -3 tools\verify_terrain.py --make-test TwoIslands D:\RUSE-Instances\hill`; the owner starts `RUSE.exe` from that
copy (Steam running), plays Centre de gravite and looks for the hill near the middle (the tool prints where):
drawn close up and zoomed out, tanks drive up it, orders and the camera work.
- Passes → release Studio 0.6 (the brushes, the ramp); the cloud's next is painting the ground (below).
- Fails → write down exactly what happened (a crash at load, holes or seams, units walking through it, the camera)
  in pull request #6. Likely causes, in order: the `.kdt` index buffers and triangle lists (still opaque, FORMATS
  §6) no longer matching moved points; patch bounds; normals. The cloud can then move only the mesh points, or a
  smaller hill, to split the cause.

**Other tests waiting for the owner** (the steps are in each pull request): Studio 0.5's new unit (A, merged),
mod sets in the launcher (B), a mod as one file (C), the community mods (G: `airfield-capacity`, then
`cheat-mod-v2`; in the private repo's `private/mods/` until their authors agree), Browse mods (D: needs the owner to create the public repository `sneadtristen6/Ruse-Mods`
with an `index.toml`, MOD_FORMAT §15). One game start per test.

**Findings since the PC stopped** (details in [LOG.md](LOG.md)):
- The community `.rmod` files showed the patch forms modders need (`@TClass[Prop=value]`, `patch every`, a
  reference to a part) and real values worth keeping (FORMATS §2); 18 mods are rebuilt in `mods/`, other authors'
  work left out (MOD_FORMAT §13).
- A map's ground is four files that must move together; the engine moves them by one rule, keeps every untouched
  byte, and builds the same bytes on every PC (multiplayer fingerprints match). Unverified in the game until the
  hill test.
- The Studio's brushes work in a browser on the preview island: hill, a painted drag, crater, plateau, ramp, Undo,
  Start over, the words in all ten languages.
- Discord got an update with pictures (a Studio unit, the launcher, Browse mods, the map view) and the GitHub link.

**The cloud's plan now (the owner's order, PLAN §12):** 1) **painting the ground**: a brush that paints sand,
grass, rock or snow onto the map's texture tiles (the game already draws tiles we write, so this rests on an
in-game fact; the cloud studies `tmst`/`tgu1` and the tile grid first and writes the format into MOD_FORMAT §8
before building); 2) **water that follows the ground** (T5); 3) scenery and roads (M6) after the ground works
in-game. Two ideas the owner parked are in PLAN §12 (strongpoints troops can hold; tunnels and trenches):
documented, not planned.

**The owner's standing wishes:** think Cities: Skylines but simpler; no jargon; the sessions decide small things
themselves and never ask the owner to type commands.

**Terrain paused (owner, 2026-09-29):** no terrain work (painting the ground, water, brush changes) until DomesticNukes has caught up and reviewed; see PLAN §10 "Terrain work waits". Join codes (E) and the Studio follow-ups (F) go ahead.

**Queue (2026-09-29, keep this order):** A, B, C, D and G are done (pull requests #1, #2, #4, #5 and #3, all
merged) → **E** (join codes, next) → F; the terrain editor's own order is in PLAN §12. Take the first task not started; one task per session; one pull request per task; resolve
conflicts with `main` by merging `main` into the branch (in docs/LOG.md keep both entries). When the PC session
is out of credit (it says so here or in the pull request), a cloud session may merge its own pull request once
GitHub's tests are green and it has re-read the whole diff; version bumps, tags and releases still wait for the
owner's in-game check.

**Tell the owner what to test.** Cloud sessions have no game, so every pull request ends with a section
**"Test for the owner"**: at most five numbered steps in plain words (which app to install from the Actions run,
which button to press, what should appear), what counts as a pass, and what to screenshot. Post the same steps as
the last comment on the pull request when it is merged. The owner's tests so far:
- **A (new units):** install the Studio from the Actions run on `main`; open the M4 Sherman, "New unit…", name it
  "Sherman Test", price 5, same menu; "Test in game"; in a skirmish the US armour factory offers "Sherman Test" at 5
  and it builds and fights. Screenshot the factory menu.
- **B (mod sets):** install the launcher; "New mod set", tick a mod, Play: the game starts with the set; rename and
  delete a set without touching any file.
- **C (a mod as one file):** export a Studio mod, install the file in the launcher with "Add a mod file…", play it.
- **D (browse mods):** open "Browse mods", install a listed mod, play it; then unplug the network and open the tab
  again (the cached list shows).
- **E (join codes):** make a set, copy its code, paste it into a second launcher home (or a friend's PC): the same
  set appears and plays.
- **F, G:** as their briefs say; F re-runs the A test with a unit moved to another menu.

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

**Status (2026-09-29): code done, in a pull request from `cloud/launcher-mod-sets`** (built on top of Task A's
branch, so the docs don't clash; merge A first). The PC session tries it with the real game, checks that a file
dropped on the window arrives (pywebview's own drop support; it can't be tried without the window) and releases 0.2.0.

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

## Next five (added 2026-09-29, after Tasks A and B)

Order: C, then D, then E (each builds on the one before). F and G can be done at any time, on their own branches.

### Task C: a mod as one file — branch `cloud/mod-package`

**Status (2026-09-29): code done, in a pull request from `cloud/mod-package` (it sits on Task B's branch until pull
request #2 merges).** The PC session tests the loop with the real game.

**Goal:** the loop from modder to player. The Studio turns a mod folder into one file; a player installs that file
with the launcher's "Add a mod file…" (Task B).

**Build:**
1. The package is the mod folder zipped (MOD_FORMAT §2 layout, §3 manifest): `mod.toml` with name, version,
   author, description, the game build it was made from and the mod's fingerprint (§12), plus `src/*.rndf`,
   `text/*.csv` and assets. If §2 doesn't fix the file extension, use `.rusemod` and write it into §2.
2. Engine: one module used by both apps: pack a folder into a package, check a package (manifest, files, nothing
   that isn't allowed such as scripts, PLAN decision 23) and report problems in plain words, unpack into the
   launcher's library.
3. Studio: "Export mod…" on the Mod menu asks for version, author and description (kept in `mod.toml` for next
   time), writes `<name>-<version>.rusemod` where the modder chooses, and shows where it went.
4. Launcher: "Add a mod file…" accepts the package; the library shows name, version, author, description and the
   build; a broken package is refused with a plain message.
5. Tests: pack and unpack round trip, the checks, the Studio's export, the launcher's install, and a set using the
   installed package builds on the fixtures.

**Done when:** a mod made in the Studio is exported, installed in the launcher from the file, and plays in a set.

### Task D: Browse mods — branch `cloud/browse-mods` (PLAN §10 step 5)

**Status (2026-09-29): code done, in a pull request from `cloud/browse-mods` (on Task C's branch until pull requests
#2 and #4 merge).** Waiting on the owner: create the public repository `sneadtristen6/Ruse-Mods` with an
`index.toml` (MOD_FORMAT §15 shows one), then test with the real launcher.

**Goal:** players find and install mods inside the launcher. No server: a GitHub repository is the index.

**Build:**
1. The index: a small public repository (the owner creates `sneadtristen6/Ruse-Mods`; until then work on a local
   copy) holding `index.toml`, one entry per mod: id, name, version, author, description, homepage, download URL
   (a GitHub Release asset: the package from Task C), size, sha256, game build, fingerprint, tags. Document the
   file and how a modder adds an entry (a pull request to that repository) in a new MOD_FORMAT section.
2. Engine: fetch the index with a timeout and keep a cached copy for offline use; verify a download's size and
   sha256 before installing; install through the library code of Tasks B and C.
3. Launcher: a "Browse mods" tab: search, and for each mod its name, author, version, description, size, build
   and an Install button; "Installed" and "Update available" states; offline shows the cached list and says so.
4. Tests with a local HTTP server serving a fixture index and package (no internet in tests).

**Done when:** from a fixture index the launcher lists mods, installs one, and a set using it builds.

### Task E: join codes in the launcher — branch `cloud/join-codes` (PLAN §10 step 7; needs D)

**Goal:** a friend pastes a code and plays the same mods (MOD_FORMAT §12; the engine's fingerprint and join-code
code is in `src/rusemod/lock.py` and its tests).

**Build:**
1. "Share this set": the launcher shows the set's join code and copies it.
2. "Join a friend…": paste a code; the launcher shows what the set holds and what's missing, installs the missing
   mods from the index (Task D) or asks for the file, makes the set, and refuses to play if the fingerprint
   doesn't match, saying what differs.
3. Tests: a code made in one launcher home (a temp folder) reproduces the set in another temp home from the
   fixture index.

**Done when:** two temp launcher homes end with byte-identical mod sets from one code.

### Task F: Studio follow-ups from Task A — branch `cloud/studio-names-menus`

1. Names per language: on a new unit's page, "Names in other languages…" with the ten languages; blank means the
   one name (the names file already has the columns).
2. Moving an existing unit to another factory or nation ("Build menu" on any unit's page; the engine's identity
   code gives it a free slot), undoable.
3. The review notes on pull request #1 (two reviewers, 2026-09-29; nothing blocking, all tests passed):
   - `app.js` ~351: the "Another one" nation list never preselects the unit's own nation (`unit()` returns no
     `nation` field, in the API and in `fake-api.js`).
   - `app.js` ~382: if `menus()` fails after "Another one" is ticked, Create silently falls back to the source's
     menu; it should say so instead.
   - `api.py` ~621: the new-unit errors are hard-coded English with internal names ("Descriptor_Unit_…"); use
     `words.toml` and the unit's shown name.
   - `api.py` ~634 and ~632: a huge or NaN price raises a raw exception instead of a StudioError; a source without
     an editable price silently drops the typed price.
   - `api.py` ~315: `unit()` looks up edits by the address as given instead of the index's canonical address, so
     a shared part opened through an alias no longer shows its "shared" edit (main used the canonical one).
   - `edits.py` ~219: `save()` sorts clone blocks by address, so a hand-written clone of another Studio clone can
     be moved before its source and the mod stops building.
   - `MOD_FORMAT.md` §6: game keys are said to be up to 8 characters; the Studio writes 10 (`dic.name_to_key`
     accepts up to 10). Fix the wording.
   - `LOG.md`: "the names file has room for the columns" overstates it; `save()` rewrites the file with only the
     columns it knows.
4. Tests as in Task A.

**Done when:** the browser preview shows both flows and the build on the fixtures places the unit in its new menu.

### Task G: import RUSE-Mod-Manager `.rmod` mods — branch `cloud/rmod-import` (PLAN M3)

**Status (2026-09-29):** the reader exists as `tools/rmod_to_mod.py` (branch `cloud/community-mods`: 18 mods rebuilt
into `mods/`, the format written down in MOD_FORMAT §13, a test on a synthetic `.rmod` in `tests/test_tools.py`).
G now means: move the reader into the engine (`rusemod/rmod.py`, built on the tool), the launcher's "Add a mod file…"
accepting `.rmod` (it becomes a mod folder in the library, marked with its build), and the launcher tests.

**Goal:** players keep the mods they already have.

**Build:**
1. Our own `.rmod` reader (MIT; never copy RUSE-Mod-Manager's code; the format as documented in MOD_FORMAT §13 and
   docs/LITTLEGROOVE_STUDY.md) that turns an `.rmod` into a package of ours (Task C), with `mod.toml` marking the
   game build it was made for (the `compat` branch). If the documents don't pin the format down, write what's
   missing into MOD_FORMAT §14 and stop.
2. Launcher: "Add a mod file…" accepts `.rmod`; the library shows the build mark and says "made for the old build"
   when the installed game differs.
3. Tests with a synthetic `.rmod` the test builds from the documented format.

**Done when:** a synthetic `.rmod` installs and its changes appear in a set built on the fixtures.

## Later

- Launcher: an update check against GitHub Releases ("a newer version is out", one click to get it).
- ~~Studio: the terrain editor's brushes~~ (code done 2026-09-29, branch `cloud/studio-brushes`, on top of
  `cloud/terrain-brushes`; waits for the in-game hill check).
- ~~Studio: a ramp tool and Start over~~ (code done 2026-09-29, branch `cloud/ramp-tool`, on top of
  `cloud/studio-brushes`).
- Studio: painting the ground (the owner's next, PLAN §12), then water that follows the ground.
