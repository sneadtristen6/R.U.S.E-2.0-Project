# R.U.S.E. Mod Platform: Log

History moved out of [PLAN.md](PLAN.md) on 2026-09-29 so a session reads less. Section numbers (§7, L5, L6)
refer to PLAN.md. Newest entries go at the end of part 2.

## 1. Passed checks (from PLAN §7)

### C3: can the game load an extra pack of ours? (moved up; can run now)

**Why:** all game text (`.dic`) lives in ZZ_Win.dat (2.3 GB). Without an extra pack, every mod that adds text, which
means every new unit name, rebuilds that whole pack (L5). With one, a mod ships a small pack of its own.

**Known so far** ([FORMATS.md](FORMATS.md) §1, §5, §6):
- The game loads the six core packs by fixed names and doesn't pick up extra `.dat` files.
- Map packs are mounted by NDF data: each map's `clustermap.cpp` has `TClusterMountMapDataPack{ DataPack
  'MapDat:\DataMap<Name>_v09.dat', DatasMapDirectory 'GenDatasmap/<Name>', MountingPoint 'Datasmap' }`.
- Script packs are registered by NDF too (`TResourceDescriptorPythonPack 'Eugen.ipk'`, `TClusterAddPythonPath`).
- Likely places for startup-time mounting: `genglad\patchable\clusterinitialisationpatchable.cpp` and
  `genglad\patchable\clusters\*.cpp` (names from `listings/`).

**Steps, cheapest first.** All in an instance; the Steam install is never touched.
1. **Survey (read-only):** list every NDF class whose name contains `Mount`, `DataPack`, `Pack` or `Cluster`, across
   all NDF files: where each is used and with which properties. Record
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

**Result (2026-09-28): step 2 passed; step 3 has no route found so far.**
- **Step 1** (survey): the only mounting class is `TClusterMountMapDataPack`, run when a map loads; no startup mount
  of an arbitrary pack exists in the data (FORMATS.md open question 3; one lead left: `TestOption/LocalDataPath`).
- **Step 2** ([`tools/make_c3_instance.py`](../tools/make_c3_instance.py)): in an instance, Two Islands' pack existed
  only as `DataMapTwoIslandz_v09.dat` and `clustermap.cpp` named it. The owner played "(6) Centre de gravite" on it:
  **loaded and played normally.** So a map pack is found by the name in the data, and its file name isn't checked.
- **Meaning:** new maps ship their own pack (no core-pack rebuild). Game-wide text still needs the ZZ_Win.dat rebuild,
  which the streaming writer handles (until the runtime extender, M10, can mount packs). The map pack's header "checksum" turned out to be a
  random GUID, not a hash of the contents (FORMATS §6), so edited packs can't fail on it. The M1.5 terrain test
  confirms this in-game.

### C4: a text mod through the whole pipeline (passed 2026-09-28)

C2 proved the game loads a pack we rebuilt with a script. C4 proves the real pipeline: a mod written as text
([`examples/half-price-buildings/`](../examples/half-price-buildings/)), put through load order, the rules engine and the
bridge, then written into a modded copy.

    set PYTHONPATH=<repo>\src
    py -3 -m rusemod build examples\half-price-buildings --instance D:\RUSE-Instances\c4-half-price

- The build prints the load order and every note (one per building without a price), then "modded copy ready".
  It reports, as notes, any object name used in two files (an open question in MOD_FORMAT.md §14).
- Launch `RUSE.exe` from the instance with Steam running, start a skirmish, open the build menu: every building costs
  half of normal (x.5 rounds up).
- Record the result, the build's output and how long it took, in FORMATS.md or here.

**Result (2026-09-28): C4 passed.** The owner launched the instance and the build menu showed every building at half
price. Before launch, a check confirmed all 134 priced buildings halved and rounded up in the rebuilt pack (e.g.
French barracks 25 → 13, artillery factory 35/30 → 18/15, HQ 140 → 70). Build output, 33 s:

    load order: half-price-buildings
    note  $/GFX/Everything/... is named in both ...everything.cpp.gladndfbin and ...everything_debuginfo.cpp.gladndfbin  (×10,762)
    note  half-price-buildings (src/prices.rndf:4): $/GFX/Everything/Descriptor_Building_DalleBatimentDepot has no ProductionPrice; skipped
    note  half-price-buildings (src/prices.rndf:4): genglad/patchable/gfx/everything_debuginfo.cpp.gladndfbin#63542 has no ProductionPrice; skipped
    0 error(s), 0 warning(s), 10764 note(s)
    changed: genglad\patchable\gfx\everything.cpp.gladndfbin
    changed: genglad\patchable\gfx\everything_debuginfo.cpp.gladndfbin
    fingerprint: S1HP-X6PM
    modded copy ready: D:\RUSE-Instances\c4-half-price  {'linked': 37, 'copied': 23, 'written': 1}

- **The whole text-mod pipeline works in-game.**
- **Fixed (cloud session, 2026-09-28):** builds now leave the four `*_debuginfo` copies exactly as shipped (they're
  skipped, so no duplicate names and `patch every` can't reach them; C2 showed the game runs with them untouched), and
  similar notes collapse to three plus a count (`ruse build --all` shows every one). If a later test shows the game
  reads these copies (e.g. a cloned unit misbehaving), builds can mirror changes into them instead.
- **Was to fix:**
  - The duplicate-name notes are noise. The game's `*_debuginfo.cpp.gladndfbin` files (everything, vfx_bank, …)
    repeat every name of their main file. Treat `_debuginfo` files as shadows: don't report their names, and hide or
    collapse the notes in normal output.
  - Decide whether rules should touch `_debuginfo` at all. `patch every` also rewrote `everything_debuginfo`, and
    the game ran fine with it. C2 left it alone, and it's unknown whether the game reads it.

### C5: a new unit in the build menu (ready to run)

C4 changed values that already exist. C5 adds something new: a copy of the M3 Lee
([`examples/cloned-unit/`](../examples/cloned-unit/)) that costs 1, with its own name, id and menu slot
(MOD_FORMAT.md §10.5, "Fresh identity"). It is the "1 cloned unit (reused visuals)" of the M2 exit test.

1. **Two read-only checks** (they only read the game):

       set PYTHONPATH=<repo>\src
       py -3 tools\names_check.py
       py -3 tools\identity_check.py > identity.txt

   - `names_check`: A must say every EXPR and IMPR tree rebuilt byte-identical, with no "miss" lines. The build
     writes the clone's name into that tree.
   - `identity_check` (`identity.txt`):
     - **A** lists, for each unit class, the values no two units share. "NOT refreshed: check it" means the build
       copies that one as is. If it's an id number (a name ending in `Id`), add it to `IDS` in
       `src/rusemod/identity.py`; otherwise note it with the results.
     - **D** shows every build menu, row by row. Note the Sherman's row and how many columns it has.
     - **F** shows the Sherman and what a copy of it gets. If the Sherman is missing, not in a factory, or an upgrade
       (`UpgradeRequire` set), pick another US tank from D and change the name in
       `examples/cloned-unit/src/units.rndf`.
2. **Build** (about 30 s):

       py -3 -m rusemod build examples\cloned-unit --instance D:\RUSE-Instances\c5-clone

   Expect one note, "…Descriptor_Unit_R2_Sherman_Test gets its own DescriptorId … -> …, ClassNameForDebug
   'Unit_M4_Sherman' -> 'Unit_R2_Sherman_Test', PositionInMenu … -> …", no warnings or errors, and `changed:` the
   unit data file. The new PositionInMenu is where to look: row = slot ÷ 100, column = the last two digits.
3. **In game** (owner): launch `RUSE.exe` from the instance with Steam running, start a skirmish as the US in a mode
   where the Sherman is available, build an armour factory and open its menu.
   - **Pass:** a second Sherman at the new slot, costing 1, in the same row as the normal one (which keeps its usual
     price). Build it: it drives and fights like a Sherman.
   - Record the result, a screenshot of the menu, the build output and how long it took, here or in FORMATS.md.
4. **If it fails**, record what happened and when:
   - **The copy isn't in the menu:** its column may be past the last one the menu shows. Give it a free slot in
     another row this menu already uses (D lists them) by adding `PositionInMenu = <slot>` to the clone in
     `units.rndf`, and rebuild.
   - **The game crashes** at start or when the menu opens: the likely suspect is the debug-info copy of the unit data,
     which doesn't have the new unit (builds leave it as shipped). Next try: mirror new objects into it.
   - **Wrong price, or the original changed too:** send the build output.

**C5 prepared on the PC (2026-09-28):** `names_check` passed (EXPR and IMPR trees rebuild byte-identical in 2,176 of
2,176 files, no "miss" lines; only 446 of 3,614 multi-child nodes are in name order). `identity_check`: the Sherman
is an **upgrade** (`UpgradeRequire` = the M3 Lee, `IsUpgrade`), so C5 copies the **M3 Lee** instead (not an
upgrade, shown in every mode, row 3 of the US armour menu: 301 Greyhound, 302 Stuart, 303 Chaffee, 304 Lee, 305
Sherman). `Key` is set on 8 ground units, 2 infantry and 7 planes and isn't refreshed; the Lee has none. The first
build failed on the Lee's text key `LD_UNI_135`: the key writer refused names over 8 characters, but the game uses up
to 10 (fixed in `dic.py`). Build, 14 s, 0 errors: `Descriptor_Unit_R2_Lee_Test gets its own DescriptorId 1141 ->
4059, ClassNameForDebug 'Unit_M3_Lee' -> 'Unit_R2_Lee_Test', PositionInMenu 304 -> 306`, `changed:` the unit data
file, fingerprint `BPJC-0PK0`, instance `D:\RUSE-Instances\c5-clone`. Checked in the rebuilt file: the copy costs 1
at slot 306 (a 6th button in the Lee's row), the Lee is unchanged. The build printed 8,537 notes: 1,476 "named in
both" (names shared by every map's files, e.g. `$/ClusterTerrain/MapInstance`) and hundreds of "… and N more like
this" lines. **For the cloud session:** collapse these to one summary line per kind.

**C5 in-game (2026-09-28): the copy did not appear** in the US armour factory menu (no crash, the game ran).
What was checked next:
- Nothing in the game data refers to the Lee except the Sherman's `UpgradeRequire`, so the menu isn't a list of
  references; the game seems to scan the units.
- A 6th column isn't the problem: Japan's tank row shows units at 306 (Type 5 Chi-Ri) and 310 (Ta-Se).
- **The likely cause:** our copy kept the Lee's name key (`N_UNI_135`). RUSE-Mod-Manager's clone, which works for
  its users, always gives the copy a new `NameInMenuToken`. Eugen's own film copy of the Lee has its own key too
  (`N_UNI_136`). If the menu tells units apart by name key, a copy that shares one is dropped. C6 gives the copy its
  own key, so it tests this.
- For later (M9): `ZZ_Win.dat!genpython/eugenpatchable.ipk` → `parametres/classes.xyz` defines a Python class per
  unit (`Unit_M3_Lee` → `Database.GetObject('$/GFX/Everything/Descriptor_Unit_M3_Lee')`) for the AI and the mission
  scripts. The AI won't use a new unit until it has an entry there.

**C6 built (2026-09-28)** with the Lee copy, 18 s, 0 errors: `NameInMenuToken` = `C6000001`, "Lee C6-Test" in all 11
`baseunite.dic` files, fingerprint `NA86-7RBG`, instance `D:\RUSE-Instances\c6-named`.

**C6 in-game (2026-09-28): the named copy didn't appear either**, so a shared name key isn't the (whole) cause.
Checked next: RUSE-Mod-Manager's docs say its editor **can't** make new units yet (its `clone.py` isn't offered, and
nothing claims in-game success), so no public tool makes new units that work (modders have made some by hand; the owner, 2026-09-29). The `*_debuginfo` copy is a full
duplicate of `everything` (the same 63,686 objects, 363 extra debug strings); nothing shows the game using it for the
unit list. The Japanese units at 306 and 310 don't prove a 6th button exists in the US menu (306 is an upgrade).
**C6b, the slot probe** (a test mod, removed after C6d): the copy takes the Lee's own slot 304
("Lee Probe", $1, key `C6B00001`) and the Lee moves to 306. Instance `D:\RUSE-Instances\c6b-slot-probe`,
fingerprint `W77E-1S9T`. If "Lee Probe" shows where the Lee was, copies work and the menu only has buttons for the
slots it ships with (then the build must pick shipped slots); if the slot is empty, the game ignores new units.

**C6b in-game (2026-09-28):** "Lee Probe" did **not** show at 304. The real Lee, moved to 306, showed after the
Sherman at $20 (the Sherman, now first, appeared as the upgrade). So a 6th slot works (the menu lays units out in
slot order), and **the game ignores copied units whatever their slot.** Not the cause either: `CHNK` is `(0, object
count)` and the writer updates it; `TrackingId` (1–60, a small table) is shared by 42 groups of visible units, the
Lee's with the Jagdpanther.
**C6c, three probes at once** (a test mod, removed after C6d; instance
`D:\RUSE-Instances\c6c-id-probe`, fingerprint `W6BS-XP65`), US armour menu after the Sherman:
- "Probe A" ($1, slot 307) keeps the Lee's `ClassNameForDebug` 'Unit_M3_Lee'. The game's Python unit list
  (`parametres/classes.xyz`) has one class per unit named exactly like this, and a renamed copy has none.
- "Probe B" ($2, slot 308) gets `DescriptorId` 2000, inside the shipped range (copies got 4059, past the highest
  shipped id, 4058).
- "Probe C" ($3, slot 309) has both.

**C6c in-game (2026-09-28): none of the three probes showed**; the Lee stayed at $20. So neither the class name nor
the id is the gate. **Found:** the game only uses units that have a class in its Python unit list (FORMATS §5, "The
unit registry"), and no copy had one. **C6d:** the C6 instance (`D:\RUSE-Instances\c6-named`, the Lee copy "Lee
C6-Test" at slot 306) now also has `class Unit_R2_Lee_Named(front.unit.TankUnit)` and its `base_class` line, added
to its `ZZ_Win.dat` by a scratch probe. The owner chose to go ahead under the safety rules of decision 23. Pass:
"Lee C6-Test" ($1) shows after the Sherman.
**C6d passed in-game (2026-09-29): "Lee C6-Test" shows at $1, under the $20 Lee.** Our first new unit, and the first public tool that makes them (other modders have made units before):
a copy in `everything`, its own name in the text files, and its class in the Python unit list. So C5 and C6 pass with
the class added. **Built (2026-09-29):** `ruse build` adds the class itself for every copied unit (`rusemod.pyscript`: a Python 2.5
marshal reader, the one fixed template, and `check_added`, which proves the module is the old one plus exactly the
template's statements), and every build, the launcher's included, refuses mods that contain scripts or programs.
`ruse build examples/named-unit` now does all of C6d by itself ("unit list: 1 class(es) added"), and its unit
list is byte-identical to the probe's that worked in-game. Tests: `tests/test_pyscript.py`; the real game:
`tools/verify_pyscript.py`.

### C6: a new unit with its own name (ready to run, after C5)

C5 proves a new unit works. C6 gives it its own name through the new text step: C5's M3 Lee copy with the name
"Lee C6-Test" ([`examples/named-unit/`](../examples/named-unit/): the unit in `src/units.rndf`, the name in
`text/baseunite.csv`). Every language shows the English name (a missing language falls back to `us`).

1. **Build** (a few minutes: the text pack, ZZ_Win.dat, is 2.3 GB and gets rebuilt into the copy, so the drive needs
   that much free space):

       set PYTHONPATH=<repo>\src
       py -3 -m rusemod build examples\named-unit --instance D:\RUSE-Instances\c6-named

   Expect the fresh-identity note from C5, `texts: 11 file(s) in ZZ_Win.dat (baseunite.dic ×11)` (ten languages and
   `dev`), no warnings or errors.
2. **In game** (owner): skirmish as the US, armour factory menu.
   - **Pass:** the new Lee copy (costing 1) is called "Lee C6-Test"; the normal Lee keeps its name.
   - Record the result, a screenshot, the build output and how long the build took.
3. **If the name is blank or shows a code:** unit names may not come from `baseunite.dic` (RUSE-Mod-Manager's note).
   Check which `.dic` holds the Sherman's own name key (`ruse dump` shows it on `NameInMenuToken`), rename
   `text/baseunite.csv` to that dictionary, and rebuild.

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

## 2. Session log, 2026-09-28 to 2026-09-29 (from PLAN §10)


**Re-evaluation (2026-09-29)**, after the community wiki and guides, another modder's research notes and the owner's calls:
- **Where we stand.** Others are ahead on terrain, scenery, pathing and AI data, reading models, and sound. Nobody else has mods built from the installed game (so they survive updates), a player launcher, join codes or a public unit editor. Community mods target the old `compat` build; ours build from whatever is installed.
- **Next, in order:**
  1. ~~C7~~ **passed (2026-09-29):** the owner built "Lee C6-Test" in a skirmish and attacked with it: it works (the wiki's crash report doesn't apply). **Also passed:** the plain-tile texture test (FORMATS §6), so terrain textures can be written without a TGU1 encoder.
  2. **MT, the terrain editor in the Studio** (§7, decision 24), starting with T1 (the `.kdt` files). **Started
     (2026-09-29):** the Studio's Maps view (T4, read-only so far) lists the game's maps and shows each in 3D with
     its real ground mesh, the game's own normals and its real ground textures (decoded once per map, cached).
     The owner wants it to look like R.U.S.E.: next come finer textures up close, the map's own lighting, then
     trees, buildings and roads (the scenery file and 3D models).
  2b. **Units in the Studio too** (owner): making new units from the window (copy, name, price, menu), on the
     engine that already does it (C6d, C7).
  3. **Launcher v0.2** (players never touch a file, below), then join codes in the launcher.
  4. **China, step 2** (M10): the data test.
- **Dropped:** the mesa test (M1.5) and the program add-on (ADR 3).
- **RUSE 2.0** is developed privately and shown to Eugen before release (decision 19).
- **Other modders** (decision 25): what they share guides our own code; we credit them the way they want.

Done so far: M0 (C1 and C2), the repo on GitHub, and the design for M1–M3 on paper (Progress, §7).

1. **PC session:** ~~C3 step 1, TOPO check, text-file check~~ **done 2026-09-28**, results in FORMATS.md:
   - **TOPO:** adding objects is unblocked. Rule: a new named object goes in; a clone goes in if its source is; append
     (order looks irrelevant). Final proof = the M2 cloned-unit test in-game.
   - **Text (`.dic`):** layout and writer confirmed on all 1,232 files; keys are readable names; 10 languages. **For the
     text writer (cloud session):** each file has one special entry, key `0x8000000000000000`, listing every character
     the file uses. Adding text with a new character must add it there. **Done (cloud session):** the writer now adds
     new characters to the end of that list and stores texts without a null, like the game.
   - **C3 step 1:** the only mounting class is `TClusterMountMapDataPack`, run when a map loads. No startup mount of an
     arbitrary pack was found (one lead: `TestOption/LocalDataPath`). So maps can ship their own pack; game-wide text
     likely needs the ZZ_Win.dat rebuild.
   - ~~C3 step 2~~ **passed 2026-09-28:** a renamed map pack loads when the data names it (§7 "Result"). New maps
     can ship their own pack. Reusable instance builder: `src/rusemod/instance.py` (tested).
   - ~~C4~~ **passed 2026-09-28:** the half-price mod built with `ruse build` worked in-game (§7 "Result").
   - **M1.5 terrain, started 2026-09-28** (FORMATS §6 "Terrain"): readers and writers for the terrain mesh
     (`rusemod.tms`) and the tile container (`rusemod.tmst`), proven lossless on all 64 sets. The map pack's
     "checksum" is a random GUID, so it can't block edits. A TGU1 texture codec (`rusemod.tgu1`, `rusemod.dxt`) is in
     progress.
   - **Next on the PC, needs the owner at the game** (one instance per test, map Two Islands, "(6) Centre de gravite"):
     1. ~~**Mesa**~~ **dropped (2026-09-29):** it changes only the visual mesh; the gameplay ground (`.kdt`) must change too (MT).
     2. **Mirror:** `py -3 tools\verify_tmst.py --make-test TwoIslands OUT.dat mirror` swaps every tile with its
        left-right twin (the game's own tile bytes). Proves the game reads our rebuilt tile store.
     3. **Checker:** the same with `checker` makes every tile a coloured ZIPO checkerboard (colour = detail level).
        If it shows, terrain textures can be written without a TGU1 encoder.
     Build each into an instance with `rusemod.instance.build_instance(..., replace={r"Maps\PC\DataMapTwoIslands_v09.dat": pack})`.
     4. **C5, a new unit** (§7 C5): two read-only checks, one build, then look for a second Sherman, costing 1, in the
        US armour factory's menu.
     5. **Nation scan** (read-only, no game launch needed): `py -3 tools\nation_scan.py > nations.txt`. Record its
        summary and the starred lines of B in FORMATS.md §3: that's the data side of the new nation (decision 19).
     6. **C6, a unit with its own name** (§7 C6), after C5: one build, then look for "Lee C6-Test" in the menu.
     7. **Launcher v0.1 and the 3D check** (needs the owner at the PC). The launcher and the Studio are two separate
        apps now (decision 22), each started on its own:
        - Once: `py -3 -m pip install pywebview` (Windows 10/11 already have the web engine it uses).
        - `py -3 -m ruse_studio --spike` (the 3D check belongs to the Studio, for its map and model views): a rotating island. Record the lines in the box (WebGL 2, GPU, frames per
          second). **Pass: 30+ frames per second.** It loads the 3D library from the internet, so the PC must be online.
        - `py -3 -m ruse_launcher`: the window is called "RUSE Launcher"; the home screen should say "Found R.U.S.E. on D: (build …)". Press "Open mod
          sets folder" and save a file `half-price.toml` there with `name = "Half-price test"` and
          `mods = ["<repo>/examples/half-price-buildings"]` (forward slashes). Pick it and press Play: the Details box
          shows the build, then the game starts from `D:\RUSE-Instances\half-price` with every building at half price.
        - Record what worked and anything confusing on the screen.
     8. **The game index** (read-only, no game launch):
        **Done on the PC (2026-09-28):** `index build` took 35 s and wrote a 269 MB file
        (`<platform folder>\index¦70294-190852.sqlite`): 38 packs and 217 nested ones (both match `listings/`),
        241,160 objects, 605,961 references, 27,522 shared objects and 130,845 texts (the same count as the decodable
        `.dic` keys). The queries take 0.3–0.45 s each: `show` lists the Sherman's values; `clone` lists what a copy
        copies, shares and references; `filter … ProductionPrice[0] gt 100` finds none, correctly, since the priciest
        units cost 80 (the atomic cannons; `gt 40` finds 39); `texts Sherman` finds the name `N_UNI_137` and 13
        dialog and description lines. Nothing wrong. Only noise: the build's summary prints a line for each of 20 sound
        files found in 44 packs. (In Git Bash, set `MSYS_NO_PATHCONV=1`, or `$/GFX/...` gets turned into a Windows path.)
        - `py -3 -m rusemod index build`: indexes every pack, file, object, reference and text (target: about a
          minute). Record its counts, time and file size here or in FORMATS.md, and whether the file counts match
          `listings/` (38 packs, 217 nested).
        - Try it: `py -3 -m rusemod index show $/GFX/Everything/Descriptor_Unit_M4_Sherman` (its values, owner,
          what uses it and what it uses), `... index clone $/GFX/Everything/Descriptor_Unit_M4_Sherman` (what a copy
          copies and shares), `... index filter TUniteAuSolDescriptor ProductionPrice[0] gt 100`, `... index texts
          Sherman`. Note anything wrong or slow.
     9. **Studio v0.2** (after item 8; needs pywebview like the launcher; build the index again first, it now
        records list types): `py -3 -m ruse_studio`. Browse units, open the M4 Sherman, switch the language (top
        right) through a few languages. Then make a mod ("Mod" menu → "New mod…", call it `studio-test`), set the
        M4 Sherman's price to 1 in every box, press "Test in game" and check the price in a skirmish (the launcher
        isn't needed for this). Record anything wrong, slow or badly translated (translations: the game's words in
        `src/rusemod/labels.toml`, the Studio's own in `src/ruse_studio/words.toml`).
        - Optional: `py -3 -m pip install -e .[apps]` once gives two commands, `ruse-launcher` and `ruse-studio`,
          which open the apps without a console window.
    10. **The installers** (needs the owner at the PC; `installers/README.md`): on GitHub, Actions → the latest
        **apps** run → Artifacts → download `launcher-installer` and `studio-installer`, unzip, run each setup.
        Windows warns once ("Windows protected your PC": More info → Run anyway; they aren't signed yet). Check: both
        appear in the Start menu with their own icons, both open, the launcher finds the game, the Studio opens the
        M4 Sherman, and Windows' "Installed apps" can uninstall each. Record anything odd.
2. **PC session, then M1:** build the game model from L2 (the combined file view and the index), the `.dic` reader and
   writer, and the `ruse` CLI (`detect index ls extract dump verify`). It needs the game files, so it runs on the PC.
3. **Cloud sessions (no game needed):** done 2026-09-28: tests that GitHub runs on every push (Windows and Linux), the
   `ruse` tool (detect, ls, names, dump, extract), the `.dic` reader/writer, load order, the mod rules engine
   (all of MOD_FORMAT §10), the `.rndf` reader, fingerprints and join codes (see README "Code so far"), and the
   bridge between game files and the engine for value changes, with `ruse build` (C4 is ready).
   ~~Next: the bridge adds and removes objects~~ **done 2026-09-28:** new objects get their export name, TOPO entry
   (the PC's rule) and imports; deleted ones keep every index; clones get their own id, debug name and build-menu
   slot (`rusemod.identity`, MOD_FORMAT §10.5). **C5 is ready for the PC** (§7).
   ~~Also from C4: the `*_debuginfo` notes~~ **done:** debug-info copies are left as shipped, similar notes collapse.
   ~~Next (cloud): names for new units~~ **done:** text mods (`text/*.csv` into the game's `.dic` files, `loc()` in
   `.rndf`, `rusemod.loc`); `ruse build` rebuilds ZZ_Win.dat too when mods have texts, streamed into the modded copy.
   Modded copies now keep the last working copy until a new one is complete, and fall back to full copies on another
   drive. **C6 is ready for the PC** (§7). Also done: the new nation's step 1 (RESEARCH.md §6, `tools/nation_scan.py`).
   **Launcher v0.1 done (2026-09-28):** the window (web-style, decided by the owner) with the home screen: finds the
   game (or "Choose folder…"), lists mod sets, and Play builds the set's modded copy (the same code as `ruse build`),
   starts Steam if needed and starts the game; Vanilla starts through Steam. Mod sets are hand-written files for now
   (`%LOCALAPPDATA%\RUSE Mod Platform\sets\*.toml`, see `ruse_launcher/api.py`). Plus the 3D check page (now in
   the Studio). The PC tries both (item 1.7).
   **Tried on the PC (2026-09-28), installed from the test build:** the download was verified (its SHA-256 matched
   GitHub's record, Defender clean) and it installed. The window works (the Edge engine, finds the game, build
   24670294). The mod set only appeared after the owner made the file by hand and dropped it into the sets folder.
   **The owner: "this needs to be worked out, it will be hard for people who aren't techy."** Found on the way:
   - The installed app's `--self-test` fails its window check ("WebView2Loader.dll isn't next to the program or on
     the search path") although the window works: pywebview loads it from `webview\lib\runtimes\win-x64\native\`.
     The check should look where pywebview looks.
   - The PC session's tools run inside the Claude app's Windows package, which redirects its AppData writes, so an
     installer or file it starts isn't seen by the owner's apps. The owner runs installs; the PC session puts files
     on D:\.
   **Launcher v0.2 requirement, before any player uses it: players never touch a file.**
   - **Mod sets are made in the window:** "New mod set" (name it, tick the mods), then edit, rename, duplicate and
     delete from the set's menu. The launcher stores them itself; players never see TOML.
   - **Adding mods takes one action:** Install from "Browse mods" (the index, L6); an "Add a mod file…" button; drag
     a mod file onto the window; double-click a mod file in Explorer (the installer registers the file type) and
     the launcher asks "Install this mod?". Later, `ruse://` links from a web page.
   - **Join codes** (MOD_FORMAT §12): paste a code, and the launcher installs what's missing and makes the set.
   - Lists update by themselves when something changes (no restart), and every error says what to do next in plain
     words.
   - Mod folders like `examples/` stay the modders' format (the Studio). Players get packaged mods.
   **The game index done (2026-09-28)**: `rusemod.index`, `ruse index` (L2 "Built"). The PC runs it (item 1.8).
   The owner (2026-09-28): the launcher stays at v0.1 for now; the core tools come first.
   **Studio v0.1 done (2026-09-28)**: browse units, a unit's values, parts and users, the language selector with
   the game's names by default (decision 21). **v0.2 done (2026-09-28)**: the owner asked to edit units right on
   their page instead of copying them first: numbers are edited in place, saved in the mod's `src/studio.rndf`,
   and "Test in game" starts it (L5). The PC tries it (item 1.9).
   **Two apps (2026-09-29, decision 22):** the owner asked for the Studio and the launcher to be separate apps. They
   are: `ruse_launcher` (RUSE Launcher) and `ruse_studio` (RUSE Studio), each with its own window and start command,
   both on the engine `rusemod`; starting the game moved into the engine (`rusemod.play`), the game folder picked by
   hand is shared (`rusemod.home`), and the Studio's screen words moved into the Studio (`words.toml`).
   **Installers (2026-09-29, ADR 9):** the owner asked for both apps as real Windows installers; built by GitHub on
   every push (`installers/`, `.github/workflows/apps.yml`), each checked by installing it on GitHub's Windows machine.
   The PC tries them (item 1.10).
   **Studio v0.3 (2026-09-29):** parts several units share can be changed for one unit only or for all (L5), proven
   down to the built game data by a test.
   Next (cloud), the owner's order: names, moving a unit to another menu or nation, then new units (copies).
   Later (cloud), launcher steps, one at a time: installing mods into the launcher's library (from a folder or zip,
   then RUSE-Mod-Manager's `.rmod`), mod sets made on screen, the join-a-friend screen (join codes), then the
   installers (Nuitka + Inno Setup; one for each app) and browsing the mod index. And whatever C5/C6 turn up.
4. **You:** the open decisions in §9 (name, outreach timing, the unit to clone in M2, a second player).

**Who does the work (from 2026-09-29)**
- The cloud session has ended (its credit is used up). The PC session now does everything: design, code, and the
  checks and tests that need the game.
- **GitHub `main` is still the record.** Anything a later session needs goes into the repo. Push when done, and
  keep README's "Current stage" line and this section up to date.


**2026-09-29, Studio 0.4.1 verified in-game (owner):** the M4 Sherman set to price 1 in the single price box costs 1 in a skirmish. The earlier "the Studio does not change values" report was the five unlabelled per-date price boxes (only the first was edited); the build had been right all along. The shared repo (private) mirrors main and has the `private` branch with the research handover and community guides; the owner pushes there.

**2026-09-29, `rusemod.kdt` (MT step T1, first half):** the gameplay-ground `.kdt` container is read and rebuilt
byte for byte on all 32 maps (ground and camera files, 3.5 million vertices), positions, parents and normals decoded
and re-encoded exactly, the opaque parts (index buffers, triangle lists, MainNode, subtree nodes) carried as is; a
vertex can be moved and the file rebuilt. `tools/verify_kdt.py` checks a game folder. Learned from the data: the
fill after the parent codes is junk (0xAA on half the maps, 0xDD and stray bytes on the rest); seven ground files
omit `BoundingBoxMin` (it is zero); `TriangleCount` is less than the subtrees' sum (border triangles repeat); some
chunks stop one byte short of the flush marker. Built by a three-agent job (implement, verify on every map, review);
the reviewer's alignment concern was checked and left as a comment (every shipped MainNode is a multiple of 8).
Also: TASKS.md Tasks C–G for the cloud sessions (mod package, browse mods, join codes, Studio follow-ups, `.rmod`
import); the cloud tab's pull request #1 (Task A) is under review.

### 2026-09-29, cloud session: new units from the Studio (TASKS.md A, pull request `cloud/studio-new-unit`)

- **What a modder sees:** on a unit's page, **New unit…** asks for a name (one name, shown in every language), a
  price (one number, every battle date) and the build menu: the same as the unit's, or another nation's factory
  (factories are shown by the units they hold, since the game has no names for them). The copy opens as its own
  page, listed first under its nation and marked *new*; it's edited like any other unit (its own values, its parts,
  a shared part for it only or for all) and **Delete this unit** removes everything about it. Test in game builds it.
- **How it's kept:** the copy is a `clone` block at the top of the mod's `src/studio.rndf` (its own values inside the
  block, its parts' changes as `patch` blocks after it); its name is a row in `text/studio.baseunite.csv` with a
  game key made from the unit's address (the same on every PC). The engine now reads `<anything>.<dictionary>.csv`
  (MOD_FORMAT §6), so the Studio's names file never touches a hand-written `text/baseunite.csv`.
- **Addresses:** `$/GFX/Everything/Descriptor_Unit_<Name>` with an ASCII-safe name (accents dropped); a name the
  game or the mod already has is refused; a name without any A–Z letter or digit (Japanese, say) gets
  `Descriptor_Unit_New_1`, and the shown name stays as typed. The debug name and the class in the game's Python unit
  list follow from it (MOD_FORMAT §10.5).
- **Tests:** the mod files written and read back, the build down to the game data on the fixtures (own gun, own ammo
  copy, the name in both fixture languages, another nation's menu), listing, deleting, name clashes, a broken
  names file left alone. The browser preview (`index.html?fake`) shows the whole flow.
- **Not done, on purpose:** per-language names (the names file gets their columns then; today it's rewritten with one), moving an existing
  unit to another menu, and the release (no version bump: the PC session's in-game check comes first).

### 2026-09-29, cloud session: mod sets made in the launcher (TASKS.md B, pull request `cloud/launcher-mod-sets`)

- **What a player sees:** under the mod sets, a **Mod library**: "Add a mod file…" opens a file dialog (a `.zip`, or
  a mod's `mod.toml`); dropping a mod folder or `.zip` anywhere on the window does the same. Each mod is checked
  first (the engine reads it the way a build would; scripts and programs are refused) and listed with its name,
  version, author, description, the game build it was made for (and a note when that isn't the installed one) and
  how many mod sets use it; **Remove** takes it out again. **New mod set…** asks for a name and the mods to tick, in
  order (the lower one wins when two change the same thing; the set's order now counts in the build,
  `rusemod.play.keep_order`). A set's page has **Edit** (mods and order), **Rename**, **Duplicate** and **Delete**.
  Every change comes back with the fresh lists, so nothing needs a restart, and every refusal says what to do next.
  The launcher starts in the PC's own language when the game has it (`words.toml`, ten languages, a selector at
  the top right); nothing on screen mentions a file.
- **How it's kept:** the library is `<home>/library/<mod id>/`; sets stay TOML files in `<home>/sets/`, now listing
  library mods by id (a hand-written set with folder paths still works, and can be edited on screen). A dropped
  file's path never reaches the page's JavaScript: pywebview's Windows side hands it to a Python drop handler
  (`rusemod.webui.on_file_drop`), which adds the mod and tells the page. That part needs the real window, so the PC
  session checks it.
- **Tests:** the library (a folder, the file inside it, a zip from its top or one folder, a newer version replacing
  the old, refusals: a broken `.rndf`, a script inside, no `mod.toml`, a bad id, a zip that would write outside its
  folder), removing (sets that used it say so), the file dialog and dropped paths, sets (new, edit and reorder,
  rename, duplicate, delete, unique ids, refusals with plain messages), Play from a set made on screen in both
  orders (the later mod wins), hand-written sets, the words (complete, all used) and the start language.
- **Not done, on purpose:** double-clicking a mod file in Explorer (the installer's file type), join codes, Browse
  mods, and the release (no version bump: the PC session's check with the real window comes first).

### 2026-09-29, cloud session: a mod as one file (TASKS.md C, pull request `cloud/mod-package`)

- **What a modder sees:** "Export mod…" in the Studio's Mod menu asks for the version, author and description
  (kept in the mod's `mod.toml` for next time), opens the window's "save as" dialog with `<id>-<version>.rusemod`
  suggested, builds the mod on the game to record the game build and the mod's fingerprint (MOD_FORMAT §12) in the
  file's manifest, and says where the file went. A mod with a mistake isn't exported; without the game the file is
  made without the build mark, and the report says so.
- **What a player sees:** "Add a mod file…" (and dropping a file on the window) takes the `.rusemod`; the library
  shows its name, version, author, description and build; a broken file is refused with a plain message.
- **Engine:** `rusemod.package`: pack (the §2 layout only: never caches, hidden files or build output; scripts and
  programs refused), check (one mod folder, nothing that would land outside it, a sane size, the manifest's id and
  version, and the mod read the way a build reads it), unpack (nothing written before the check passes), and a
  manifest editor that changes values in place and keeps everything else. The launcher's library unpacks through it.
- **Tests:** pack/check/unpack round trip and every refusal; the Studio's export (build mark, fingerprint, kept
  values, cancel, a broken mod, no game); the launcher installing a file made by `pack` and playing a set with it.
- **Not done, on purpose:** the installer's file type (double-clicking a `.rusemod` in Explorer), join codes, and
  the release.

### 2026-09-29, cloud session: Browse mods (TASKS.md D, pull request `cloud/browse-mods`)

- **What a player sees:** "Browse mods" at the bottom of the launcher opens the community's list: each mod with its
  name, version, author, size, description, tags, the game build it was made on and a link to its page; a search
  box; Install (or "Update to 1.1.0", or "Installed"). Install downloads the file, checks its size and checksum
  against the list, puts it in the library and says so; the mod then appears in the library and can be ticked in a
  mod set. Offline, the list is the copy from before, and a line says from when.
- **The index:** a public GitHub repository's `index.toml` (MOD_FORMAT §15: the file, the required fields, how a
  modder adds an entry by pull request). `rusemod.mod_index` fetches it with a timeout, keeps the copy in
  `<home>/index/`, checks every entry (a bad one is skipped and named, not the whole list), verifies downloads by
  size and SHA-256, and marks entries against the library. The launcher's `index_url` setting points elsewhere for
  tests and mirrors.
- **Tests:** the index on a local web server (read online, the copy offline, entries checked one by one, downloads
  refused when the file isn't the promised one or is missing); the launcher's list, states and search, an install
  that then plays in a set, refusals, and offline.
- **Not done, on purpose:** the index repository itself (the owner's), screenshots and ratings (PLAN L5 later),
  and the release.

### 2026-09-29, cloud session: community mods rebuilt in our format (branch `cloud/community-mods`)

- **What came in:** 41 files from the owner: 38 RUSE-Mod-Manager `.rmod` mods (37 distinct) and three zips that are
  whole replacement copies of `ZZ_GladPatchableWin.dat` for the "Compat 2" branch (Tharshey's Extreme Nations v5 and
  Extreme AI, Val's Reworked Nations). The `.rmod` format is now written down in MOD_FORMAT §13 (one JSON file;
  objects matched by debug name, ammunition id, class, anchor or file position; typed values; texts by the game's own
  keys written byte by byte; whole files; terrain bit layers). What the mods teach about the game's data (flag bits,
  the constants, the AI profiles, ammunition, aircraft altitudes, where the music, videos and scripts live) is in
  FORMATS.md §2, marked as the modders' findings.
- **Engine:** objects found by a property (`@TClass[Prop=value]`, any class with `@[…]`) as patch targets, clone
  sources and references; `patch every` reaches unnamed parts and takes a filter, and finding nothing is an error; a
  reference to a game object's part makes the part a shared object with a name of its own (`<file>#<index>`, which
  the writer encodes in place); `+=` / `-=` on number lists keep the list's type and never add an item twice.
  Tests for each (`test_patch`, `test_rndf`, `test_model`).
- **Mods:** `tools/rmod_to_mod.py`, our own reader, rebuilt 32 mods; the owner chose the 18 that go into `mods/`
  (the gameplay ones, the cheat mod for testing, and the Navy mod as the seed for landing ships), each with a README
  of what carried over and the assumptions to check in-game (`mods/README.md` is the index; moved to the private repo on 2026-09-29: most are DomesticNukes' work, published only with his OK). Left out: two other
  authors' mods, three that are only files (a song, a video, recompiled mission scripts), and the three whole-pack
  zips, which would need a "compare two packs" tool and the pristine Compat 2 pack. A synthetic `.rmod` runs through
  the tool and the engine in `tests/test_tools.py`.
- **Not done, on purpose:** no in-game check (the owner's; the launcher builds a modded copy, never the Steam
  install), no release, and Task G's launcher side (accepting `.rmod` files directly) stays in the queue.

### 2026-09-29, cloud session: terrain brushes, engine side (PLAN §7 MT, T2–T3; branch `cloud/terrain-brushes`)

- **Owner's call:** start on map editing. First the engine, so the one in-game check can happen before the Studio
  offers brushes.
- **Brushes** (`rusemod.brush`): hill, raise, lower, crater, plateau, flatten, smooth. A stroke is one dab: centre,
  radius, and a height, a level or a weight. Shapes are polynomials (no crease, full at the centre, nothing at the
  edge); only arithmetic and square roots, so every PC computes the same heights. Smooth pulls toward the local
  average of a height grid sampled from the close-up mesh, which follows every stroke, so every file moves toward
  the same surface.
- **All four files together** (`rusemod.terrain_edit`): every stroke moves the points of the close-up and far meshes,
  the gameplay ground and the camera floor inside its circle by the same function of position and height, so
  shared points stay equal (the gameplay ground's points are the close-up mesh's: exactly equal after the edit).
  The map edge never moves; heights stop at each file's own range and the report counts them; mesh normals and patch
  bounds are recomputed around moved points (`Tms.set_heights`); a moved tree point takes the normal of the nearest
  close-up mesh point; untouched cells and tree parts keep their bytes.
- **In mods and the build:** `maps/<map pack>/terrain.toml` (MOD_FORMAT §8); `ruse build`, the launcher's Play and
  the Studio's "Test in game" apply the strokes of every mod in load order and put the rebuilt map pack into the
  modded copy; the reshaped files count in the fingerprint. A map that isn't in the game, a bad stroke or a bad
  folder name is refused with a plain message.
- **The in-game check** (next, on the PC): `tools/verify_terrain.py` checks every map in memory (all four files
  change and read back, the hill's centre rose by what the brush says in each, shared points agree, nothing far away
  changed); `--make-test TwoIslands <copy>` builds a copy with one hill on the dry land nearest the middle of Centre
  of Gravity and says what to look for (drawn near and far, units drive up it, camera, line of sight).
- **Tests:** brushes (shapes, each brush, the file written and read back, every mistake, the local average), a
  made-up map's four files edited together (a hill, a plateau level in every file, smoothing, the top of the range,
  normals, the edge, a stroke outside the map, a missing file, the same bytes twice), the build (the copy, the
  fingerprint, two mods on one map, refusals) and the check tool.
- **Not done, on purpose:** the Studio's brushes (T4, next, after the hill passes in-game), ground above the map's
  highest point, water following the ground, re-meshing.

### 2026-09-29, cloud session: the Studio's brushes (PLAN §7 MT, T4; branch `cloud/studio-brushes`, on top of `cloud/terrain-brushes`)

- **Owner's call:** on with the map editor; think Cities: Skylines, kept simple (PLAN §12). Two map ideas
  (strongpoints troops can hold, tunnels and trenches) are written down in §12 and nothing more.
- **The Maps view paints strokes.** A "Shape the ground" panel with the seven brushes, Size and Strength sliders,
  "Look around" (the camera again), Undo and the count of strokes on the map. Click stamps one dab (hill, crater,
  plateau); dragging paints dabs along the path (raise, lower, flatten, smooth), a third of a radius apart. The
  view reshapes the drawn mesh at once with the same maths as `rusemod.brush` (a copy in `maps.js`; the build's
  copy decides), recomputes normals where the ground moved and keeps the game's own everywhere else. The size is a
  share of the map's width, the strength a share of the map's height range; plateau levels at the click's height
  plus the strength, flatten at the height where the drag started.
- **Saved in the mod:** `StudioApi.terrain`, `terrain_add` and `terrain_undo` read and rewrite
  `maps/<map pack>/terrain.toml` in the current mod (the build's own format, `strokes_toml`), one write at a time;
  the file and its empty folders go when the last stroke is undone; a file the Studio can't read is never written
  over. Picking another mod swaps the strokes drawn. Undo takes back the last click or the whole last drag. Without
  a mod the panel says to pick one and paints nothing.
- **Checked in Chromium** with the preview data: three hills, a 40-dab drag, a crater, Undo twice, the words in
  French, the no-mod case. The preview island's triangles were wound the wrong way (it drew dark), fixed.
- **Tests:** the terrain calls (no mod, saved and read back by the build's reader, per mod, refusals, a broken file)
  and every word the panel uses in all ten languages. 377 tests.
- **Not done:** the in-game hill check (PC session, from pull request #6) decides whether any of this ships; a ramp
  tool and water that follows the ground are next (TASKS "Later").

### 2026-09-29, cloud session: the ramp and Start over (PLAN §7 MT, T4; branch `cloud/ramp-tool`, on top of `cloud/studio-brushes`)

- **Owner's call:** "1 then 2": the ramp first, then painting the ground (PLAN §12). The owner is not a coder: the
  sessions decide and build, the owner clicks and reports.
- **The ramp** (`rusemod.brush`, brush `ramp`): an even slope from `level` at (x, y) to `level2` at (x2, y2),
  `radius` half its width. Inside its band the ground goes to the line between the two heights, flat across the
  middle half of the width and easing back to the old ground at the sides and beyond the ends; `weight` says how
  far. The maths is a projection onto the centre line and the flat shape: + − × ÷ and one square root, so every
  PC agrees. `Stroke` grew `x2`, `y2`, `level2` (0 for the other brushes); the terrain file writes them for ramps
  only; a ramp whose two points are the same is refused.
- **In the Studio:** the Ramp brush takes two clicks: the start (the ground's height there), then the end; a ring
  marks the start and a line follows the pointer; Esc, another brush, Look around, another map or mod drop a
  half-made ramp. Size is half the ramp's width, Strength how far the ground goes to it. **Start over** removes
  every stroke on the map after a question under the button.
- **Checked in Chromium** with the preview data: a ramp from low ground up a hill (two clicks, one stroke saved
  with the two heights), Esc, Undo, the Start over question, No, then Yes (the file is gone, the button greys out).
- **Tests:** the ramp's heights, band and box, the file written and read back, its two refusals; on the made-up
  map, the ground inside the band lies on the ramp's line in all four files. 379 tests.

### 2026-09-29, PC session: .rmod mods in our builds, through LittleGroove's engine (PLAN decision 26)

- **Owner's call:** use LittleGroove's RUSE-Mod-Manager code directly. His engine is in `src/ruse_mod_engine`
  (from his v1.1.9, as it is, two comments reworded); `rusemod.rmod` puts it in our builds.
- **How:** his applier runs on `Layered` packs: the game's pack read-only (memory-mapped) with the changes so far
  on top; his writes are recorded, and the build writes the changed packs into the modded copy like every other
  change. So nothing is copied first (his own way copies each whole pack, 2.4 GB for `ZZ_Win.dat`) and the install
  is never touched. `.rmod` mods apply first, in set order, our mods on top. A mod stamped for another build is moved
  with his version maps. `rusemod.edat` can now add files to a pack (his way: new top-level entries in front of the
  dictionary, their data at the end; read back by his reader in a test).
- **Owner's call, scripts:** a `.rmod` may replace the game's own scripts (`.xyz`, `.ipk`); the build report warns.
  Programs are still refused. Our own mod format keeps decision 23.
- **Launcher:** "Add a mod file…" takes a `.rmod` (kept as it is, next to a `mod.toml` made from it); `ruse build`
  takes `.rmod` files too.
- **Checked on the real game, read-only:** all 75 `.rmod` files on D:\ (the 74 community mods + Dev Toolkit) apply
  with 0 errors; the game's packs unchanged. Warnings: the 9 with game scripts; RCRBM 2 (made for compat-2) has 388
  changes on values the game changed since, applied anyway (his rule). A modded copy with Dev Toolkit + 10x
  Artillery Price (`D:\RUSE-Instances\rmod-test`) has exactly the expected files changed (3 NDFs, which our reader
  reads, and the script archive with its 2 scripts), every other file byte-identical. **In-game: passed** (the
  owner started it: "works").
- **Tests:** 450.
- **Owner, the same evening:** Eugen has never said the game's program can't be edited. The docs said he had; fixed
  (PLAN L4 and decision 3, FORMATS §10, TASKS rules). Keeping the public code data-only is the owner's rule;
  program work is allowed in the private repo, for editing game files and mods.

### 2026-09-30, PC session: the terrain fix, and three community tools read

- **Terrain (the owner's in-game report: orders refused, the camera falling through, trees at the old height,
  steps):** DomesticNukes and his Claude's recipe is in: strokes move the gameplay `.kdt` only; the drawn meshes and
  the camera floor move by the change of its surface (barycentric, inside its triangles); both `.kdt` files widen
  every height limit over a moved triangle, in the subtree trees and the MainNode, and a part whose moved triangle
  changes sides of a height split gets a new x/y tree (`rusemod.kdt_edit`). `tools/verify_terrain.py` now also
  checks the trees: 32 of 32 maps pass. Test copy for the owner: `D:\RUSE-Instances\terrain` (Blitz: a hill, a pit
  east of it, a flattened patch west of it). The pit reaches the map's lowest height (16 points clamp), so its floor
  is flat.
- **Three tools downloaded to `D:\research\` at the owner's request, read only:**
  - RugnirViking/moddingSuite (enohka's Wargame suite, forked for R.U.S.E.; GPL-2.0): its `.scenario` reader gave us
    the zone layout. R.U.S.E.'s files match except for one list per zone; `rusemod.scenario` (our own code) reads
    all 102: zones, starting points, spawns, labels, waypoints. It also has Wargame's mesh, TGV, `.ess` and save
    readers, which we already have or don't need.
  - mathieujaumain/IrisZoomDataAPI (LGPL-3.0): a C# reader for NDF binaries and EDAT packs, the same ground as
    `rusemod.ndf` and `rusemod.edat`. Nothing new for us.
  - Ulibos/ndf-parse (MIT): parses WARNO's **text** NDF. R.U.S.E. ships binary `.ndfbin`, so it doesn't apply.
  Only format facts were taken, never code (the first two are GPL/LGPL).

### 2026-09-30, in-game: the terrain fix and a moved starting point PASSED (owner)

- **Blitz test copy** (`D:\RUSE-Instances\terrain`): a hill, a pit and a flattened patch (terrain fix: the gameplay
  ground leads, the height limits widened), and player 1's starting point moved onto the flattened patch
  (`maps/SuperCrossRoads4/scenario.toml`). The game starts, the HQ is at the new place, units drive up the hill and
  take orders there, the ground and trees draw right. First in-game proof that the terrain editor works.
- **Two crashes on the way, both fixed:** the scenario's design-item NDF must be zero-padded to 4 bytes, and the 16
  bytes after `SCENARIO\r\n` are an MD5 (bytes 0-9 and 28-end, LittleGroove's rule) the game checks at launch; a
  moved item without it crashed 8 seconds in. The terrain-only copy (`D:\RUSE-Instances\terrain-only`) split the
  cause in one start.
- **A rule, enforced:** `tests/test_source.py` fails on Python strings whose backslashes mangle Windows paths (it
  happened four times that day).

### 2026-09-30, night: movement edits pass in the game

Blitz, one modded copy: a blocked pit (`movement.toml`), 24 placed buildings made solid, and the ground the
shrunk circles gave up filled back with new circles. Units can't enter the pit, drive between the placed towers,
reach the hill, and a building placed in the game on that ground works. Four crashes on the way, all in the
navigation graphs' spatial index, read from the crash dumps: it's one bounding-interval tree whose branches hold
a jump to their right half; a tree appended at the end is never reached, and a leaf grown without fresh jumps sends
the walk astray. `rusemod.nav` writes it the game's way (all 1,307 shipped graphs byte-identical).

### 2026-09-30, night: Studio 0.7.0, the tools along the bottom

The map view's movement side: a **Where units go** overlay (the two navigation graphs drawn as cells: red closed to
every unit, yellow to vehicles only, purple to infantry only), the **Block**, **Block infantry** and **Block
vehicles** brushes painting on it, and a **Solid** box for placed buildings. Cover and movement share one overlay
engine in `maps.js`. The owner found the right panel crowded ("use bottom like city skylines"; "look at what the game
looks like, don't make it up"), so the tools moved to a dock along the bottom: a bar of kinds (Look, Ground, Water,
Cover, Movement, Buildings, Objects, Trees, Scenario) and the picked kind's tray above it; the open kind again, or
Esc, closes it. Its look comes from the game's own HUD, read (not copied) from the in-game screenshots and the
`res2d/interface` textures (`objectives_panel_cadre`, `hint_unit_info`: translucent black, a thin grey frame,
gunmetal bands; raw A8R8G8B8): the player bar's blue marks what's picked, the money's gold names the tray. The
scenario's four drop-downs became chips and a list.

### 2026-09-30, afternoon: Studio 0.7.1 and Launcher 0.2.7, the wiki and Discussions

The owner hit "stroke 1: the water brush needs level" on Test in game: the Studio wrote water strokes without their
level (`brush.strokes_toml` only wrote it for the level brushes), then refused its own file. Fixed; and every file
the Studio writes (terrain, scenery, scenario, unit edits) is now parsed back before it's saved, so it can't write a
file it can't read. The **mod check** reads every file of the mod as the build does (the five map-file readers now
share `build.read_map_file`), when a mod is picked and before Test in game: a red bar per problem, **Set aside**
(renamed `.broken.toml`, never lost) for a broken map file, **Rename** for a map folder named after the map's title
(`terrain.pack_for`: any case, any of the ten languages' titles; the build's errors give the same hint).

Owner requests, built: **several units at once** (1-10) in a **line, column, wedge, box or circle**, facing up the
screen, with rings under the pointer (`scenario_spawn_many`, one save); the **map list folds away**.

The **wiki** is a field manual (task pages, not the README's pitch; the owner asked for the distinction, and for a
real "Ask a question" page instead of an empty FAQ), `docs/wiki` pushed to the GitHub wiki. **Discussions**: the
Welcome and Roadmap posts from `docs/community` via `tools/post_discussions.py` (the owner's `gh` login; the API
can't make categories or pin), and a bug-report form with two self-checks. Both apps: **Help** / **Report a
problem** (`rusemod.community`: a pre-filled report; the Windows user name taken out of paths; nothing sent).
Screenshots of the new windows for the README: from the owner, after updating.

### 2026-09-30, evening: roads, steps 1 to 3 (owner away; one in-game test waiting)

- **The map's roads drawn in the Studio** (the Roads box): the scenery's road pieces are cubic Béziers (start, its
  handle, end, its handle, as offsets; the type `Route`; the chain's length in the first trailing word), placed with
  their blocks' transforms (`Scenery.roads`; Blitz: 1,389 pieces).
- **The road network decoded:** `mapinfo.win` buffer 0 is points on the road curves (~9 m apart), links (cost =
  distance / 10), per-point link lists, and a k-d tree over the links (x then y; the navigation index's jump rule).
  `rusemod.roadnet` writes it back byte-identical on all 33 maps (`tools/verify_roadnet.py`); `add_road` chains a new
  road and joins its ends to the nearest road; `maps/<map>/roads.toml` builds it (MOD_FORMAT §8).
- **Found:** the roads a player sees are **painted into the ground's texture tiles**; the pieces lie exactly on them.
  A visible new road will need ground painting (A6) as well.
- **Test copy waiting:** `D:\RUSE-Instances\roads` (scratch `make_road_test.py`): one straight shortcut road on Blitz,
  network only, west of player 1's HQ, 2.9× shorter than the existing way round, a water tower beside each end.
  Question: do vehicles take it, and are they faster on it than beside it?

**In the game (owner, 2026-09-30, 15:19): the road network is what supply routes follow.** Placing a supply depot
west of the HQ, the game's route preview runs along the roads, then straight north through open fields where no
road is painted: the network-only road added by `roads.toml`. A road that exists only in buffer 0 is a road to the
game's supply routing. Still to see: a truck driving it, and whether vehicles are faster on it.

### 2026-09-30, late: Studio 0.7.2 and Launcher 0.2.8, the road tool

The road tool (Straight, Curve, Freeform; ends snap onto the map's roads and the mod's; blue ribbons like the game's
supply routes; `roads.toml` through `StudioApi.road_add`). The owner couldn't tell how to see spawned units: the
Studio called the game's modes by our own words ("Skirmish"), which the game never uses. Its main menu says BATTLES,
OPERATION, CAMPAIGN (text keys `BTN_SKIRMI`, `BTN_CHALLE`, `BTN_CAMPAI`); the Studio now reads those from the
installed game in the player's language, shows under the scenario menu where each setup plays, and Test in game
ends with what to open (e.g. "BATTLES > D-Day"). The middle mouse button zoomed in look-around mode and turned the
view in every tool: it turns the view everywhere now. The launcher runs the mod check when a mod is added.

### 2026-09-30, evening: roads painted and bridged; Studio 0.7.4 and Launcher 0.2.9

**In the game (owner): painted roads show**, in the map's road colour, and bridges draw where a road crosses water.
But the first bridges tipped into the river (a V or an X per crossing): each crossing got several pieces end to end,
and each piece had one end out over the water. Every shipped bridge on every map (measured: `bridge_fit.py` in the
scratchpad, 60+ bridges) is **one piece with both ends on dry bank**, stretched along its length to fit (0.91 to
1.91 times), sunk 130 to 850 units by its kind, its deck along the model's own y. The game sets a "TangeantFloor"
bridge on the ground under its ends. Now: one bridge per crossing, centred on the water, stretched bank to bank
(`scenery.toml` objects take `stretch` and `lift`), sunk to the median of the map's own bridges of that kind.
Owner's rule: **a road over one of the map's own bridges replaces it** (the old one sunk out of sight in place,
`scenery.bury_objects`; its deck over water closed to units, `nav.Graph.block`, and to the road network,
`RoadNet.cut`). **In the game (owner, 17:15): the rebuilt D-Day copy shows one straight bridge per crossing, bank to
bank, the painted roads meeting it.** Units on them: not tried yet (TESTS.md T8).

**A player's report:** *Test in game* failed every time with `[WinError 5] Access is denied:
'E:\RUSE-Instances\studio-cascade-test.partial\Data\PC\190852\ZZ_GladPatchableWin.dat'`. Reproduced
(scratch `perm_probe.py`): a copy of a read-only file keeps the mark (`shutil.copy2`), a hard link shares it, and
Windows won't delete either; `rmtree(ignore_errors=True)` left them silently, and the next build's `rmtree` raised.
A swap that failed while the game ran from the copy left the `.partial` behind in the first place. `rusemod.instance`
now never marks a copy read-only (a read-only pack is copied, not linked), removes the instance's own read-only
files, drops a read-only link left by an older version while putting the mark back on the game's file, and says
plainly when the copy is in use. `tests/test_instance.py` ReadOnlyGame rebuilds the report's state: the old code
fails all four tests, the new one passes. The owner's rule behind it: a mistake that repeats gets a guard (a test,
a hook), not another rule.

Also: a road shows its length while it's drawn (the owner, "so you know how far a straight line is").

**In the game (owner, 17:18): units go under the new bridges.** A unit ordered across crossed along the deck's line
(the movement graphs opened there work) but on the riverbed, under the deck. Where the game keeps shipped bridges'
floors: not the gameplay ground (`occlusioninfo_terrainonly.kdt` dips into the river under them, same z as the
visible ground), not the movement graphs (ordinary circles), but a third tree in each map pack,
**`output\occlusioninfo_objectsonly.kdt`** (D-Day: 6 KB, 556 triangles, 690 points, one subtree, its points in
clusters exactly at the map's 21 bridges; scratch `bridge_floor.py`). New bridges need their decks written there.
Also seen: a tank couldn't take a new road into the woods, infantry could; the owner wants that as a choice per road.

### 2026-09-30, night: 8 players on a map (PLAN A10), built

The owner's call: at least 8 players; past 8 later. What sets a map's count: its menu entry `TMultiMapInfo` in
`misc\globals.cpp` (D-Day: MP22, `NbPlayers` 6, `CategoryId` 2, `GameType` 3, `DispoMulti2Teams`), tied by GUID to
its `TMapLoadInfo` (name "(6) Cotentin (3v3)"), and a starting point per player in the entry's scenario: a point is a
team (`AllianceNum`) and a place in it (`AlliancePriority`), with a camera (`PositionCamera`, `Azimut`, `Site`) and a
warm-up camera path (`WarmupCamPath` = `Warmup_J<n>`). D-Day's 3v3 has team 1 and 2 in places 1-3 and teams 3-6 in
place 1; the 8-player Valley has teams 1 and 2 in places 1-4 and more. Game types seen: 1v1 = 1, 2v2 = 2, 3v3 = 3,
2v2v2 = 5, 2v2v2v2 = 6 (4v4 = 4 inferred). Every shipped starting point sits at the ground's height
(`Tms.height_at` matches them within one unit). Built: `rusemod.players` (map.toml), `Scenario.add_start`
(`[[start]]`), the Studio's Add starting point and Players row; D-Day for 8 at `D:\RUSE-Instances\eight` (team 1's
fourth start in a 150 m field 690 m from the nearest start, team 2's in a 205 m field 960 m away). Not tried in the
game yet (TESTS.md T12).

### 2026-09-30, night: floors for new bridges

What units stand on at a bridge is each map pack's `occlusioninfo_objectsonly.kdt` (FORMATS §6). Measured on D-Day's
21 bridges (scratch `floor_probe.py`): a floor runs straight (the stone ones arched) from end to end, 5 to 60 units
above the ground at the deck's ends; Pont_Metallique_02's is 8 triangles in four sections along the deck. The height
I first read as "7,500 above the ground" was a comparison with the wrong place: the floors sit on their own banks.
`rusemod.floors`: a new bridge gets the floor of the flattest shipped bridge of its kind on the map, each point kept
as (along, across, height above the line between the ends' ground) and put back on the new banks; the file is built
again as one subtree with its own k-d tree (every node clipped to its triangles, split at the middle of the longest
side, leaves of at most 8; every triangle found from its middle). D-Day's own 556 triangles rebuilt: every point
exactly where it was; with the test mod's two bridges: 572, each new floor 47 above its banks.

**In the game (owner, 18:19): tanks drive on the new bridges' decks** (the floors work). Two things left, both seen in
the same test: one tank was in the water beside a bridge (the ground opened along a deck reached 2,560 either side
of its line; the deck is about 1,200: now 1,280, the smallest circle any shipped map uses), and a painted road
vanished near the camera. The close-up road: the scenery's road pieces are `Route` items, a **STICKERS** type (the
descriptor `TypeWarrior/Route`, no model): decals along the curves, what draws a road up close; the painted pyramid
is the far view. New roads now get sticker pieces the shipped way (about 16 m, straight, handles a tenth, the chain's
count and the map's two constant words), added with the placed objects (`scenery.RoadPiece`). On the way:
`div_map.tgv_pc` decoded (DXT5, the whole map about 5 m a pixel); roads are only a faint lift there, so it isn't the
close-up road (a painter for it is kept, unused).

**The narrowed bridges crashed the game (owner, 18:43), and why.** The move-order crash again (an empty route). On the
copy the owner played, every circle along the two new decks was cut off from the rest of both movement graphs: with
circles of 1,280, no deck reached the ground units use (its nearest edge 1,060 to 7,444 past a deck's end). Every
shipped movement graph turns out to be **one piece** (66 of 66 main graphs on 33 maps, and all their sub-graphs), so
the game never expects ground it can't reach. The 18:19 build (circles of 2,560) had been lucky: one deck a dead end,
the other an island for infantry, and only tanks were tried. The owner's "buildings on the road blocked the tanks near
the bridge" is the same thing from the land side: past the first bridge's west end the road runs 7,400 units through a
farmyard no circle ever covered. Now `Graph.open` joins each end of a deck to the graph's main part, with an approach
along the road (circles every 960, until one overlaps the ground units use; at most 62 m), leaves closed a deck it
can't join, and refuses to write a graph that isn't one piece; `Graph.find` walks the index as the lookup does
(it finds all 6,499 and 7,292 of D-Day's shipped circle centres, and every point along the new decks). Also found:
most shipped bridges have a local graph whose small circles (320 to 1,280) line the deck, the walls that keep units
on it; and a crossing is the road through a circle, its last two u16 road network links (7,862 of 7,862 on 4 maps),
so `RoadNet.cut` now renumbers them in both graphs (`Graph.renumber_roads`). Details and the probes: the handoff for
DomesticNukes in the private repo.

**A player's every-second-Test failure on 0.7.4, found and fixed** ("An old modded copy at
`E:\RUSE-Instances\studio-cascade-test-2.old` can't be removed: Windows refused ...ZZ_GladPatchableWin.dat (Access is
denied)"). The first press moved the old copy aside and couldn't delete it (silently); every press after it stopped
on it. Checked on this PC, case by case: a folder rename is stopped by any open file inside it, or a process's
current folder; a delete is refused for a read-only file, a running program's own file, and a file mapped into memory
where the volume deletes the old way; a rename still works in those three. The code path that gives the player's
exact text with no game running: a read-only hard link left by 0.7.3 whose game file was replaced since (another mod
manager): the 0.7.4 cleanup only cleared the mark on a link that was still the game's file. Now (`rusemod.instance`,
`rusemod.winfiles`): such files go by a POSIX delete that ignores the mark (only that name goes, the other keeps its
mark); a leftover Windows won't delete is moved into `RUSE-Instances\.trash` and removed on a later build; a game still
running from the copy is refused before building, by name; the Studio's Test button can't start two builds at once
(a double click did), and neither can the Launcher's Play.

**Studio 0.7.5 and Launcher 0.2.10 never came out: the repo rename skipped every workflow.** The owner renamed
the repo to R.U.S.E-2.0-Project. Every job ran only `if: github.repository == 'sneadtristen6/Ruse-Mod-Platform'`
(so the shared private repo, which mirrors .github/, doesn't build), which never matched again: tests, app builds,
the private sync and both releases were skipped, and a skipped run isn't a failed one, so nothing said so. The
jobs now check `github.repository_id` (1393317090), which a rename keeps, and `tests/test_installers.py`
WorkflowGuards fails on a check by name. Moving the two pushed tags to the fix needs a force-push, which Claude
Code's safety check refuses even when the owner says go; so the same release went out as Studio 0.7.6 and
Launcher 0.2.11 (new tags, nothing forced), and every link to the old repo name now uses the new one.
**Rule:** a release tag that didn't build is never moved: the next version number goes out instead.

### 2026-09-30, night: a clean game backup in both apps

The owner: "backup restore clean version of game in studio or launcher ... that way files stay clean". Our apps never
change the game's folder (they build modded copies), but other mod managers and hand edits do, and every copy built
from a changed game carries their changes. `rusemod.backup` (Settings, "Clean game backup", in the Launcher and the
Studio, one shared mixin `BackupCalls`):
- **Make backup:** a full copy of every file of the game folder (never hard links: a link shares the game file's
  content and would change with it) in `RUSE-Backup\<Steam build>` on the game's drive, with `manifest.json` (build,
  date, every folder, and each file's size, date and SHA-256). Made in `<build>.partial` and renamed when complete, so a
  half-made one is never listed or used; the free space is checked first and the refusal says how much is needed.
  One per build; making it again asks first (the game may not be clean any more: Verify with Steam first).
- **Check game files:** changed, missing and added files. Fast by default (size and date; only a file whose date
  differs is hashed, so a touched file isn't "changed"); "Compare every byte" hashes everything.
- **Restore clean files:** checks, lists what will change, asks; then copies the changed and missing files back (each
  written next to its target, checked against the manifest's SHA-256, then swapped in; a read-only file keeps its mark;
  a damaged backup copy is left out and named), and moves added files into `RUSE-Backup\set-aside-<date>`. Nothing is
  deleted. Refused while R.U.S.E. runs from the game folder **or from a modded copy** (a copy's packs are hard links to
  the game's own files), while a Play or a Test in game is building, and when Steam has updated the game since the
  backup (another build). A Play or a Test waits for a restore.
- **Verify with Steam:** `steam://validate/21970`, Steam's own repair, no backup needed.

It's the only place either app writes into the game's own folder. Two changes from the first design: the set-aside
folder sits beside the backups, not inside one (making a backup again would have taken a player's set-aside files
with the old one), and the manifest lists folders too, so a restore puts back the install's empty `EmptySteamDepot`
and never removes a folder the game has. Checked read-only on this PC's install (61 files, 5.3 GB, build 24670294):
a fast check takes 0.01 s, a subset's deep check finds a planted checksum change; nothing was written. No real backup
was made (tests only), and the previews (`index.html?fake=backup`, `oldbackup`, `nospace`, `running`) show every state.

### 2026-09-30, late: a local map for every new bridge (units keep to the deck)

The owner's screenshots: units stepped off a new bridge's side, went down the bank and walked under the deck. The
deck was a chain of plain main-graph circles of radius 1,280, and the game straightens a route anywhere inside the
circles it runs through: 1,280 either side of the deck's line, against a floor of 663. The game's own bridges have a
**local map** instead (FORMATS §6, "Movement graphs"): one big owner circle over the crossing, and inside it units
stand only on the local map's small circles along the deck. Local map k belongs to main circle k for k below the
header's count NX, and nothing else ties them (worked out by DomesticNukes and his Claude, and checked by us); nobody
had added one before.

`Graph.open` now gives each new deck (a road's bridge or one placed by hand) the same: an owner centred at the deck's
middle, as small as holds the deck and meets the ground at both ends by 320 or more, never so big that another
circle's middle is inside it or it overlaps another owner (no shipped map has either). It's put in at circle number
NX, so every later circle moves up one: links (kept sorted by their second circle), lists, crossings (their links'
numbers) and the index (renumbered, the owner listed by the nearest old circle, the branches widened to reach it) all
follow; NX goes up one, the offset table gets one more entry, the local map goes last. The local map: the deck's
circles (radius 640, at most 640 apart, on the deck's line), a copy of every main circle the owner overlaps (the banks
inside it stay ground exactly as before, and every point where the owner's links meet them is on its ground: the
copies are our shortcut, DomesticNukes' recipe fans new circles over the banks), and approach circles whose middles
fall in the owner (a road that turns back, or runs along the bank). Its index is built as the shipped ones are
(median split, x first, leaves of up to 4). The approaches to ground units use stay in the main graph, now never with
any of their disc over water (16 points on the rim and 8 inside tested, not the middle only). A deck whose middle is
in an old owner (a road over a bridge of the map's) goes into that owner's local map instead: its circles over the
water near the new deck go (with what only they held to the rest: Korsun and Square have rows of small circles beside
their decks), the deck's come in, and closing the old deck no longer empties the owner. An old deck of plain main
circles (3 of D-Day's bridges) goes from the main graph the same way, its land circles at the ends kept in the new
local map shrunk off the water, unless that leaves ground units can't reach. A deck with no room for an owner is left
closed, with a note. Before anything is written: the graph in no more pieces, every new
local map one piece, every point where a new link meets an owner on its local map's ground, each owner holding its
deck and no other circle's middle, every place along each deck ground units can stand on (`Graph.walkable`, the
game's rule: the circle the index finds, then its local map's), and the graph read back as written.

The owner's D-Day test (two new bridges), built into a temporary folder and probed: water within 4,000 of each deck's
line and 4,000 past its ends, sampled every 100, walkable by the game's rule:

| deck | water samples | shipped map | before (circles of 1,280) | now |
|---|---|---|---|---|
| (1578973, 1315630), 12,802 long | 7,906 | 0 | 2,247; 1,063 more than 663 off the deck (up to 1,200) | 1,133; none more than 600 off |
| (1561274, 1325836), 12,783 long | 6,698 | 0 | 2,049; 957 more than 663 off (up to 1,200) | 1,039; none more than 600 off |

The same in both graphs. Each owner has radius 6,720 (52 m across) and a local map of 24 and 23 circles (21 on each
deck, the rest copies of the approaches), one piece, both of its links' meeting points on its ground; both graphs one
piece, the 44 old local maps byte-identical, every old circle found by the index where it was (6,499 and 7,292), and
the graph read back as written. The map check finds what it found before. The probe on two of D-Day's own bridges of
the same kind: water walkable only within about 1,300 and 1,200 of their decks (their local circles are wider than
ours), none farther; with their local maps ignored, all of it would be. A road over those two bridges: they go into
their own owners' local maps (gates 8 of 8 and 7 of 7 still on ground, one piece, the new deck walkable end to end;
water more than 663 off the deck: 428 and 231 samples before, from the old decks' circles, none now); their old local
crossings over the old deck go with its circles (15 to 4, 12 to 2). A road over every bridge of 7 maps (91, D-Day,
M07_Allemagne, Dolly, Valley, Korsun, Mireille, Square), both graphs: 85 go into their old owner, 3 get an owner of
their own (D-Day's plain-circle decks), 3 stay closed (Mireille's deck 11 runs past its owner's edge; D-Day's 19 and
20 lie in an owner with no ground near them), no error, and no water anywhere units can stand on that they couldn't
before. Not tried in the game yet: whether it takes a graph with more local maps than it shipped with. The test: units
across both bridges and back, an order onto the water beside a deck, an order onto bank ground inside an owner.

**Bridge ends and the map's buildings (2026-10-01, the owner's 23:05 test of the local maps).** Three of the four new
bridges' decks held units; but at one, "end of bridge hits buildings": its road runs straight through a farm, and the
deck's approach (the chain of circles that joins a deck to ground units already use) had covered the farmyard, which the
map's own movement leaves out, so units were sent through the buildings. Now the build reads the map's buildings along
the roads near each new deck (`mapcheck.map_objects`, buildings only: rocks and jetties on a bank don't count) and an
approach never reaches within 480 of one that the graph keeps units off (`bridges.apply_spans` obstacles, `HOLE`);
where a full circle of 1,280 won't fit, one of 960 or 640 squeezes past (3/4 spacing keeps circles of half the radius
overlapping by 320, so they still link). A deck whose road meets water, a town's ground or ground closed to units
before reaching ground units use is left closed, and the note now says what it met and where ("23 m past its west end
the road meets ground closed to units ... at (x, y): move the road clear of it"). On the owner's test: three bridges
open with clean approaches (11 m at most), the fourth closed at the farm, whose stable stands 3.5 m off the road. The
retest and the rule the owner asked for ("the road can't be built into buildings, it shows red like Cities") are next.

**A new bridge's deck is narrower than its floor (2026-10-01, after the owner's third in-game test).** With the local
maps of the night before, units still stood in the river beside a deck. The movement file itself was right (its
owners, offset table and local maps read back as the game's own do, and by the game's rule no water was walkable), so
either the game does not honour a local map we added, or it leaves a route inside the owner circle; either way the
owner circle is 26 m of ground over the river that only the local map keeps units off. So new bridges no longer get
one. `Graph.open_narrow`: a deck is a chain of circles 640 wide (`DECK_RADIUS`) on its line, in the main graph, with
no owner and no local map. 640 is less than the 663 of the bridge floors units stand on, so every place the build
opens is over the deck: there is no ground beside it to be on, whatever the game does with routes. A deck whose
middle lies in an owner the map already has (a town, a bridge of the map's) still goes into that owner's local map,
which is the game's own arrangement and needs no new owner. Checked on the owner's D-Day test, all four bridges, both
graphs: every point along each deck walkable end to end, and not one walkable point more than 663 off a deck's line
that the shipped map did not already have (82 and 93 by two decks' ends, the same count as the map's own). The
local-map code stays for a map whose bridge needs it and for the record.

**A new bridge's floor is made wider than the deck's movement (2026-10-01).** With the narrow decks, units were still
at the water under a bridge in the game. The floor a unit stands on reached about 660 either side of a deck's line
(the width of the shipped floor it is copied from), and the movement on the deck reaches 640: a unit at the band's
edge, or nudged over it by another unit, found no floor and dropped to the riverbed, which is what standing "under the
bridge" looked like. A new bridge's floor is now carried 1.5 times as wide (`floors.WIDEN`, about 950 either side),
so every place a unit can stand has floor under it with about 1.2 m to spare. The floor isn't drawn, so a wider one
only means a unit at the deck's edge still stands at the deck's height. On the owner's D-Day test: the floor covers
the whole span out to 900 either side, flat to 0.01 m, and the movement still reaches only 640.

**A mod's blocks were opening the water beside the map's own bridges (2026-10-01).** The owner's screenshots of an
infantry squad standing in the river turned out to be at a bridge of the map's own, on a copy built from a mod that
had only placed some buildings there. Diffing the built movement against the game's: two of the map's 44 local maps
changed, several of its largest circles were shrunk (one of 67,200 to 8,320, one emptied outright), and 961 places
beside each of two of its own bridges had been opened to vehicles. The cause is in `apply_blocks`: a building becomes
a block zone, and a zone shrinks every circle it reaches into - including the circles that own a local map. The game
decides what is ground inside such a circle from its local map, so shrinking the owner opens everything its local map
kept closed, the water beside a bridge included. `apply_blocks` now passes `keep_owners=True`, as the bridge code
already did: owners keep their size and the block goes into their local maps instead (`Graph.block` walks them).
After it, on the owner's D-Day test: 0 of the map's 21 own bridges have any ground changed beside them (was 2), and
its local maps change only where a building really stands. `tests/test_nav.py` has the case.

**A new bridge's floor reaches out over the water, as the game's metal bridges' do (2026-10-01, round 6).** Tanks held
the deck; infantry beside it still stood in the river ("they are in water not like vanilla ruse ... vanilla ruse they
float"). Where a unit is comes from the movement graph, how high it stands from the topmost floor under that point,
and nothing ties the two. A tank is one point. An infantry squad is five men on an arc 2,828 wide (the game data's
`Dispersion` 500 for `NbSoldatInGroupeCombat` 5; a man strays up to `DispersionMax` 620 x 4 = 2,480 from the squad's
place), each man on the floor under his own feet, and only the squad's own place is ever held to the movement graph.
So beside a deck 640 wide two of the five are 2,054 from its line. Measured on D-Day: each metal bridge's floor is
three slabs, the deck's band (440 to 670 either side) and two flat aprons the length of the band reaching 12,170 to
17,230 from the line over open river, so the game's infantry stand at the deck's height there (740 to 840 above the
water's surface); its five stone bridges have the band alone (1,400), and infantry stand in the river beside them.
Our copy of a bridge's floor kept only the triangles within 2,500 of the deck's line (`floors.ACROSS`): the band,
never the aprons. The men beside our decks had the riverbed, about 2,000 below the surface.

`floors.apron`: beside each new deck's band, floor in the band's own plane out to 3,200 either side (`APRON`: the
deck's 640 and the squad's limit 2,480), tested in cells of 160: a cell is floor when its corners and middle are over
water with the riverbed 150 or more below (at the water's edge a corner may be on dry ground no more than 200 below
the floor: a steep bank's top), so a unit on dry ground is never lifted, and a bank at an angle to the deck (dry
beside the deck, water farther out) still gets floor over its water. Cells clear alike join into one piece; pieces
lap the band and each other by 150 (the file's points sit on a grid, 61 by 40 map units on D-Day). A sunk bridge's
aprons go with its band (`beside_deck`). The ground under thousands of test points comes from `bridges.Ground` (the
mesh bucketed by place: `Tms.height_at` scans every cell, 55 ms a point on D-Day, which made the build take 12
minutes; the same answers 5,000 times faster).

Three rules of the game's floor files, found from the owner's 04:14 screenshots (men lying sideways on the decks, on
one of the map's own stone bridges too) and now kept by `floors.rebuild`: every triangle faces up by the order of its
points (all 556 of D-Day's; the first aprons had one side's the other way round, 161 triangles); every point's normal
is the one word `0x7FFDFFF5`, straight up, whatever the slope (all 45,188 points on the 29 maps with a floor file; we
wrote normals worked out from the triangles, changing 207 of D-Day's 690 shipped points; the game turns a man to the
normal of what he stands on); no triangle is a sliver on the file's grid (3 were).

The check before the game test, on the built copy (`D:\RUSE-Instances\bridges`, the owner's `test` mod, 4 new
bridges): a squad placed everywhere the movement lets it stand on each deck, walking either way, its five men at their
places on the arc. Before: 1,777 to 2,159 of about 4,600 men per bridge under the water (down to 2,060 below the
surface; 6,430 at one). After: 31 to 53, all within a cell of the water's edge (283 to 446 below; 1,098 at one steep
bank). No floor below the water's surface, no dry ground a unit may walk on lifted by the aprons, the map's own 556
floor triangles and 690 points unchanged, every triangle found by the file's tree, the movement file byte for byte
what it was. 889 triangles (333 new). What the game should show: a squad on a new bridge as on one of the map's own
metal bridges, the men beside the deck upright at its height over the water. [LESSONS.md](LESSONS.md) has why this
took six rounds.

**T8 passed in the game (owner, 2026-10-01, 04:27).** On the rebuilt D-Day copy: tanks, infantry squads and a supply
truck cross the four new bridges on their decks, every man upright at the deck's height, the ones by the rails too
("FINALLY WE CAN MOVE ON"). Screenshots in `docs/images/bridge-*.jpg` and the README. Still open from the same test:
new roads' close-up texture (the road stickers).
