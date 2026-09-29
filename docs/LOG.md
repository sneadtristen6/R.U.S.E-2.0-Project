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
