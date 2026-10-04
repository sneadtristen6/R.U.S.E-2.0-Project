# R.U.S.E. File Formats: Knowledge Base

Everything we know about the game's files, with evidence. Keep it updated: this file is the project's memory.
Game build examined: Steam re-release, Steam build 24670294, data revision **190852**.

**Status legend:** ✅ verified on all shipped files · 🟡 partially understood · ❔ unknown ·
**R** = we can read it · **W** = we can write it · **RT** = byte-identical round trip proven.

| Format | Where | Count | Status | Priority |
|---|---|---|---|---|
| EDAT archive (`.dat`, nested `.ipk .ppk .apk .mpk .gpk`) | everywhere | 38 packs | ✅ R | P0 |
| NDF binary (`.ndfbin .gladndfbin .truendfbin`) | Glad packs, ZZ_Win, DataMap_Win | 1,982 | ✅ R (TOPO ❔) | P0 |
| Localisation (`.dic`, `TRA\0`) | ZZ_Win | 1,232 (+31 `DICS`/`DICV`) | ✅ layout | P0 |
| Python scripts (`.xyz`) | `.ipk` in ZZ_Win, IA_Common | 327 | ✅ R | P2 |
| Map registration (`mapinfo.cpp`, `clustermap.cpp`) | ZZ_GladPatchable | 86 maps | ✅ R; W: a new map, a copy of a BATTLES map (`rusemod.newmap`, all 31 entries; seen in the game: T15b, T16, 101 at once) | P1 |
| Map support files (`save.boobspc`, `output.sdb`) | Maps\PC | per map | 🟡 checksums known | P1 |
| Scenario (`.scenario`) | DataMap_Win | 102 | ✅ R (zones and design items; `rusemod.scenario`, all 102) | P1 |
| AI map grids (`mapinfo.win`) | DataMap_Win | 34 | 🟡 buffer 0: the road network, read and written byte-identical on all 33 (`rusemod.roadnet`, `tools/verify_roadnet.py`: points on the road curves, links with a u16 word (the game works bits 1-15, the distance / 20, out again when it loads the map and keeps only bit 0 from the file, a flag set on most links where vehicles can go), per-point link lists, a k-d tree over the links, never more than 24 levels deep: the game walks it with a fixed stack of 32 entries, as it does the graphs' indexes); buffers 1-2: the infantry and vehicle navigation graphs, read and written byte-identical (`rusemod.nav`, `tools/verify_nav.py`; every shipped one is one connected piece, and a crossing's last two u16 are road network links; their local maps understood, and new ones written for new bridges: "Movement graphs" in §6); buffer 4: the cover grid, written (`rusemod.cover`, from LittleGroove's `sdb.py`) | P1 |
| Terrain mesh (`.tms`) | Maps\PC | 64 (hi + low per map) | ✅ R W RT (not yet tried in-game) | P1 |
| Terrain tiles (`.tmst_pc` + `.tmst_chunk_pc`) | Maps\PC | 64 sets, 29,254 tiles | ✅ container R W RT; plain tiles (ZIPO) work in-game; TGU1 body 🟡 (reading only) | P1 |
| Textures (`.tgv`, `.tgv_pc`) | ZZ_Win, Maps\PC | 3,831 + maps | 🟡 header | P1 |
| Meshes (`.spk`, `.spkpc`, `MESHPCPC`) | ZZ_Win, Maps\PC | 82 + maps | ❔ | P1 |
| Animations (`.apk`, `.baf`) | ZZ_Win | 53 / 43 | ❔ | P2 |
| UI (`.gpk`, Scaleform GFx) | ZZ_Win | 5 | ❔ | P2 |
| Sound (`.ess`) | ZZ_Win | 17,462 | 🟡 container only | P3 (last) |
| Video / fonts | Data_Common | 96 WebM, 4 fonts | ✅ standard formats | — |

---

## 1. EDAT archive (v1)

Little-endian. Reader: [`ruse_edat.py`](../ruse_edat.py).

| Offset | Type | Meaning |
|---|---|---|
| 0x00 | char[4] | `edat` |
| 0x04 | u32 | version = 1 |
| 0x08 | u8[16] | "checksum": all zero in Data\PC packs; in Maps\PC packs a random GUID, not a hash (see §6) |
| 0x18 | u8 | 0 |
| 0x19 | u32 | dictionary offset (always 0x40D) |
| 0x1D | u32 | dictionary length |
| 0x21 | u32 | data offset (= dictionary offset + length) |
| 0x25 | u32 | data length (file size = data offset + data length) |
| 0x29–0x40C | | zero |

**Dictionary** is a trie of path fragments. Entries are aligned to 2 bytes (relative to the dictionary start):
- **dir:** `u32 headerLen` (≠ 0; children start at entry + headerLen), `u32 nextSibling`, `cstring fragment`
- **file:** `u32 0`, `u32 nextSibling`, `u32 offset` (from data offset), `u32 size`, `u8 flag` (always 0 seen), `cstring fragment`
- `nextSibling` is relative to the entry start; 0 = last sibling. Full path = concatenated fragments (backslashes).
- An **empty archive** has a single root entry with `headerLen = 1` (shorter than the entry itself = "no children").

Files are stored contiguously, with no gaps, overlaps or container-level compression. Offsets and sizes are u32, so a pack is at most 4 GB.
**Writer proven (2026-09-28):** `src/rusemod/edat.py` rebuilds ZZ_GladPatchableWin.dat **byte-identical**
(741 members) and correctly replaces a member with a different-length blob (patches every entry's offset/size,
relays the data section, keeps the trie intact). Verified by [`tools/verify_writer.py`](../tools/verify_writer.py).
**Writer to-do (adding files):** how new fragments are split into the trie.

**Packs in build 190852**

| Pack | Size | Files | Content |
|---|---|---|---|
| Data_Common.dat | 901 MB | 102 | 96 WebM videos, fonts, 2 xml |
| IA_Common.dat | 1.5 MB | 82 | `.xyz` AI/effect-map scripts per map |
| DataMap_Win.dat | 33 MB | 374 | `mapinfo.win`, `.scenario`, `.boobspc`, `.kdt`, `.ndfbin` |
| ZZ_GladNotPatchableWin.dat | 0.1 MB | 39 | config/UI/sound/system NDF |
| ZZ_GladPatchableWin.dat | 3.5 MB | 741 | gameplay NDF: unit DB, maps, scenarios, scenery, AI |
| ZZ_Win.dat | 2.3 GB | 24,058 | textures, sounds, meshes, anims, UI, localisation, scripts, shader cache |
| Maps\PC\DataMap\<Name\>_v09.dat | 23–148 MB | ~50 each | per-map terrain, textures, mesh, baked data (32 packs) |

The game loads these six core packs by name; an extra `.dat` placed next to them isn't picked up.

## 2. NDF binary

Same family as Wargame/moddingSuite, with R.U.S.E.-specific differences (marked ⚠).
Prototype parser: [`prototypes/spike-2026-09-28/obje.py`](../prototypes/spike-2026-09-28/obje.py).

**Header (0x28 bytes):** `EUG0`, `u32 0`, `CNDF`, `u32 flags` (0x80 = zlib body), `u64 footerOffset`,
`u64 headerSize (0x28)`, `u64 fullSize`.
- If compressed, `u32 bodySize` sits at 0x28 and the zlib stream starts at 0x2C.
- ⚠ The zlib stream is **not terminated**: use `zlib.decompressobj().decompress()`. It yields exactly `bodySize` bytes.
- Logical file = header + body. `.truendfbin` files use flags 0 (uncompressed), so the engine accepts both.

**Footer** at footerOffset: `TOC0`, `u32 count`, then `count × (char[4] name, u32 0, u64 offset, u64 size)`:
`OBJE TOPO CHNK CLAS PROP STRG TRAN IMPR EXPR`.

| Table | Layout |
|---|---|
| CLAS | `u32 len + name` per class |
| PROP | `u32 len + name + u32 classIndex` per property |
| STRG, TRAN | `u32 len + string` |
| CHNK | always `(0, objectCount)` |
| IMPR / EXPR | name trees. Node = `u32 tranIndex, s32 leaf (-1 = none), u32 childCount, u32 childOffset[]` (offsets relative to the offset array). EXPR names objects (`$/GFX/Everything/Descriptor_Unit_Tourelle_MG_US`); IMPR lists imports |
| TOPO | ✅ enough to add objects. u32 object indices. **Checked on all 2,176 NDF files (2026-09-28, `tools/topo_check.py`):** every named (exported) object is in TOPO (2,176/2,176) and no unreferenced object is ever missing; some files also list referenced, unnamed objects. No single order rule: (class, index) holds in 1,601 files, plain index in 1,600, grouped by class in 1,700; the rest look like Eugen's compile order, so the order is probably irrelevant. **Rule for adding:** a new named object goes into TOPO; a cloned object goes in if its source is in TOPO; append. Confirm in-game with the M2 cloned-unit test |

**OBJE:** objects stored in sequence. Each is `u32 classIndex`, then repeated `(u32 propertyIndex, value)`
until `propertyIndex == 0xABABABAB`. A value is `u32 typeCode` + payload.

| Code | Type | Payload |
|---|---|---|
| 0x00 | bool | 1 byte; ⚠ any nonzero is true, and some files store e.g. `0x4E`, so keep the raw byte |
| 0x01 | int8 | 1 |
| 0x02 | int32 | 4 |
| 0x03 | uint32 | 4 |
| 0x05 | float32 | 4 |
| 0x06 | float64 | 8 |
| 0x07 | string | u32 index into STRG |
| 0x08 | wide string | u32 byte length + UTF-16LE |
| 0x09 | reference | ⚠ subtype `0xAAAAAAAA` = import (u32 IMPR leaf index); `0xBBBBBBBB` = local object (u32 instance, u32 class; `FFFFFFFF FFFFFFFF` = null). Swapped compared with Wargame |
| 0x0B | vec3f | 12 |
| 0x0C | float4 | 16 |
| 0x0D | color32 | 4 |
| 0x11 | list | u32 count + values |
| 0x12 | map | u32 count + (key value, value) pairs |
| 0x13 | int64 | 8 |
| 0x18 | int16 | 2 |
| 0x19 | uint16 | 2 |
| 0x1A | guid | 16 |
| 0x1C | path | u32 index into STRG |
| 0x1D | localisation hash | 8 (same 64-bit hashes as `.dic`) |
| 0x1F | int2 | 8 |
| 0x21 | float2 | 8 |
| 0x22 | pair | key value, value |
| 0x14 | blob | u32 length + raw bytes (e.g. zlib capture-zone mesh data in `.kdt`) |
| 0x1E | zip blob | u32 length + u8 flag + length bytes (u32 size + zlib); only in the shader cache |

No other codes occur. **Whole-game verification (`tools/verify_all.py`, 2026-09-28):** all 38 archives, 217 nested
archives (74 of them empty) and 2,176 NDF files (incl. `.kdt` and the shader cache) round-trip byte-identically.

**Lossless writer proven (C1, 2026-09-28).** [`prototypes/spike-2026-09-28/roundtrip.py`](../prototypes/spike-2026-09-28/roundtrip.py)
re-encodes every OBJE value of everything.cpp from its decoded form and reproduces the original OBJE bytes
**exactly** (63,686 objects, 212,827 values, 5.14 MB). So value editing in place is byte-exact and safe.
Still open before *adding* objects: TOPO semantics, and how the STRG/TRAN/PROP tables and IMPR/EXPR trees grow.
Note: recompressing the body needs fixed zlib settings for determinism, or we ship the NDF uncompressed (the engine reads `.truendfbin` uncompressed).

**Engine acceptance (C2, 2026-09-28):** the game loads a member re-compressed by us as a standard, terminated zlib
stream (level 9), inside an archive whose data section we re-laid. So the original's unterminated stream is not a
requirement, and the engine doesn't check member bytes against anything we changed.

**Unit database:** `ZZ_GladPatchableWin.dat` → `genglad\patchable\gfx\everything.cpp.gladndfbin`.
- 63,686 objects, 386 classes, 3,338 properties, 9,523 strings, 1,514 exported names, 686 imports.
- Main classes: TUniteAuSolDescriptor 204, TBatimentDescriptor 135, TAvionDescriptor 63,
  TInfanterieDescriptor 39, TTruckDescriptor 18, TUniteDescriptor 8, TWeaponDescriptor 259,
  TAmmunition 139, TArmorDescriptor 11.
- Property names are French. Examples seen in mods: `ProductionPrice` (list of 5), `ProductionTime`,
  `VitesseLineaire` (speed), `SeuilMort` (death threshold), `SeuilPinned`, `Puissance` (power),
  `PorteeMaximale` (max range), `DetectionBase`, `ShowInMenu`, `ArmorDescriptor`, `GfxDescriptor`, `Nationalite`.
- **What the game needs of a unit** (all 468 shipped units keep these; `ruse build` checks every unit a mod made or
  changed, `rusemod/unitcheck.py`, gap audit 2026-10-01):
  - `DescriptorId` is the unit's id across every kind of unit (`TUniteDescriptor` and its subclasses): one unit per
    id, never 0. A second unit with the same id, or id 0, is left out of its nation's unit list, and orders for it
    build the first one (or nothing). Clones get a fresh one (MOD_FORMAT §10.5).
  - `ProductionPrice` and `ShowInMenu` have exactly 5 items (one per battle date): at a date with no item the game's
    scripts make the unit free or hide it, and a `ShowInMenu` of 1 or 2 items is read past its end.
  - Flags (`InitialFlagSet`): the game reads 0–104 and ignores higher numbers. 2 (avion) is on all 63 aircraft and
    nothing else; 59 (transport_parachutiste) is on 10 aircraft, each with the unit it drops in `UniteTransportee`,
    and on anything else, or without that unit, the game crashes; 62 and 63 only on trucks (62 on all 18).
  - Salvos: a mounted weapon's `SalveNumber` is -1 (none) or 0–4, and then its weapon's `Salves[SalveNumber]` is
    above 0 (a weapon without `Salves` has none). Otherwise the game stops at load with a "Quit game ?" box. 14 of
    the 551 mounted weapons fire salvo 1; none is shared between two weapons.
- **Values and tricks from 37 community mods (2026-09-29; the mods' own findings, not checked by us in-game;
  the rebuilt ones are kept in the private repo until their authors agree):**
  - Units (`TUniteAuSolDescriptor`, `TInfanterieDescriptor`, `TAvionDescriptor`, `TTruckDescriptor`): `SeuilMort`
    (health) and `SeuilPinned` (pinned threshold: above `SeuilMort` = never pinned, 0 = pinned at once);
    `VitesseLineaire` / `VitesseCombat` (speeds; ground values go up to 57,200), `MaxAcceleration`,
    `MaxDeceleration`, planes also `VitesseLineaireAuSol`; `DetectionBase` and `PorteeVisionVolant` (vision on the
    ground / against aircraft), `PorteeAttackReflexSol` / `PorteeAttackReflexAir` (reflex-fire ranges); `ShowInMenu`
    (5 booleans, one per battle date) with `ProductionPrice` (5 numbers) and `ProductionTime` (hiding a unit = all
    five false plus an unaffordable price); `UpgradePrice`, `UpgradeTime`, `UpgradeRequire`; `Factory` (12 = the
    prototype base's experimental tab) and `PositionInMenu` (row × 100 + column); `StickToGround`, `ArmureHint`,
    `TextureForInterface` (the unit's card), `IconeType`, `Category`, `CategorieIA`, `TypeForAcknow`, `Radius`,
    `Scale`, `TempsDemiTour`; the hint texts `NameInMenuToken`, `TypeUnitHintToken`, `DescriptionUnitHintToken`,
    `LongDescriptionUnitHintToken`, `EfficaceHintToken` (keys such as `ND_12`, `D_mgGER`, `DD_mgGER`, `LD_UNI_167`,
    `VE_inf`); `UnitIdleManager`, `SoundMotorDescriptor`, `GfxDescriptorCadavre`, `GfxDescriptorIcone`.
  - `InitialFlagSet` (a list of uint32 bit numbers, up to 102): 1 is on the 54 artillery and gun pieces (indirect
    fire, the modders' reading); 11, 21 and 55 keep vehicles out of forests (recon units lack them); 71 = vision all
    round (artillery and turretless vehicles have it); 72 = no line-of-sight check (aircraft have it); 77 = never fires
    by reflex (the seven atomic cannons have it); 24, 40 and 43 are on every ground unit.
  - Buildings (`TBatimentDescriptor`, 135, of which 49 are production buildings): `BuildPolicy` 2 = free placement
    (the bunkers' value; production buildings normally need a truck and a depot), `UniteDefense` = a unit that guards
    the building (two decoy buildings use it), `TypeBatiment`.
  - Ammunition (`TAmmunition`, 139, shared between units): `AmmunitionId` (1000–1139; mods start new ones at 9110),
    `Puissance` (damage), `PorteeMaximale` / `PorteeMinimale` (range; the game's longest is 2,600,000),
    `TempsEntreDeuxTirs` (seconds between shots; the game's fastest is 0.2 and a mod reports 0.1 as the lowest that
    works), `NbTirParSalves` (shots per burst, on 66 of them), `AngleDispersion`, `TirIndirect`, `RayonPinned`,
    `Arme`, `ProjectileType`, `Level`, `Name` / `TypeName` (keys `N_ARM_30`, `T_ARM_6`), `Icon`, `StressManager`,
    `FX_vitesse_de_depart`, `FX_frottement`, `FX_tir_tendu`, `PourcentageTirDirect`. A unit's first gun is
    `WeaponDescriptor.TurretDescriptorList[0].MountedWeaponDescriptorList[0].Ammunition`; turrets are
    `TTurretOneAxisDescriptor` / `TTurretTwoAxisDescriptor` (`Tag`, `VitesseRotation`, `AngleRotationMax`,
    `AngleRotationMaxPitch`, `NbFX`, `MountedWeaponDescriptorList`), mounts `TMountedWeaponDescriptor`
    (`Ammunition`, `EffectTag`, `TirEnMouvement`), a unit's weapon `TWeaponDescriptor` (`TurretDescriptorList`).
  - Aircraft flight, in each plane's `MouvementHandlerInfo` (`TMouvementHandler_Avion_Info`): `AltitudeDeVol`,
    `ChaosAltitudeDeVol`, `AltitudeDownAttack`, `AltitudeDownAirport`, `AltitudeNoise`, `LoopingStartAltitude`,
    `LoopingAltitudeToHit`, `DiveAttackStartAltitude`, `DiveAttackEndAltitude` (scaling all of them together works).
  - Constants (`TTunableConstante`, one in `gdconstanteoriginal.cpp` and one in `gdconstanteatomic.cpp`):
    `NbAvionsParAeroport` 8, `SecondesEntreDeuxDecollages`, `SecondesEntreDeuxAtterrissages`,
    `RegenerationPinnedHorsCombat` 10, `MinProductionTime` 1 (a `ProductionTime` of 0 is held to it).
  - AI (`TIAProfil`, 10 objects in `everything.cpp`: regular, three difficulties, and the personalities turtle,
    howitzer, air force, prototype, blitzkrieg and random): `AttaqueTempsActivation`,
    `MissionFacteurLancementAttaque`, `MissionFacteurEnoughToDestroy`, `OffensiveNbMissionMax` (-1 = no cap),
    `DefenseMaxUnitOnPosition`, `DefenseNbMissionMax`, `HarcelementActif`, `UpgradeActifPourHarcelement`,
    `NbProdIdle*` (Infanterie, Tank, Antitank, Arti, DCA, Chasseur, Bomber, ChasseurBomber),
    `CashReserveTempsActivation`, `DefenseDistanceMenace`, `DefenseDistanceUrgent`,
    `PourcentChanceUtiliserCarteManipAuDebut`, `PercentMoneyToReserveForBatimentAdmin`,
    `TempsMemorisationUnitInvisible`, `ProbaRepereFake`, `Bonus*`. Their names on screen are the texts
    `PROFILE_<n>` in `ai-descriptors.dic` and `AI_PROF<n>` in `flash_txt.dic`.
  - Operations (`TChallengeMapInfo` in `misc/globals.cpp`): `TrackingId` (`CH32` Tobrouk co-op, `CH34` Zapad) and
    `NbPlayers` (1 makes a co-op operation start without a lobby, untested). Multiplayer maps are `TMultiMapInfo`
    (`GUID`, `TrackingId` `M09`…, `NbPlayers`, `GameType`, `GameModeMulti`, `DispoMulti2Teams` / `3Teams` / `FFA`,
    `MapSize`, `CategoryId`), listed in a `TMultiPack`.
  - Texts: unit names are `N_UNI_<n>` in `baseunite.dic` and long descriptions `LD_UNI_<n>` in
    `long_description_unite.dic` (230 and 189 of them).
  - Files: the menu music is `gen_sound\ww2\sons\atp_music\ruse_menu_ref-1.ess` (ZZ_Win.dat; an `.ess` stereo
    encoder exists in the community), the studio splash `ww2\videos\logo\eugen.webm` (Data_Common.dat; VP9/Vorbis,
    1280×720, 25 fps), mission scripts `genpython\1000\test\map\<mission>\scripting_chapter<n>\effetmap.xyz`
    (IA_Common.dat; the campaign's red-zone blockers are `DescriptorBloqueZoneForRuseAndOrder` calls there),
    scenarios `test\map\<map>\leveldesign*.scenario` (DataMap_Win.dat), unit cards
    `gen\ww2\res2d\texanimationuniticone\<nation>\<unit>.tgv` (ZZ_Win.dat). Per-map terrain bit layers live in
    `datasmap\<map>\mapinfo.win` (DataMap_Win.dat; 1024² to 4096² cells; 0x04 = "AI: blocked" (what the AI asks; units move by the movement graphs alone
    and walk on it), 0x08 = forest, per the mods). The grid is a square of square cells, its header holding its two
    corners (x0, y0, x1, y1): the map itself on a square map, and on the 8 maps that aren't (`hurtgen`,
    `m02_tunisie`, `m04_cotentin` = D-Day, `m05_hollande`, `m06_ardennes`, `m07_allemagne`, `mireille`, `testia`) a
    square as wide as the long side with the map in its middle, so it starts off the map (D-Day: y from -655360 to 3276800 on a map 2621440 tall). Seen in the
    game, 2026-10-01: cover cleared with the header read as a corner and a size left D-Day infantry hidden.
  - Ships: `Unit_Battleship`, `Unit_Heavy_Cruiser` and `Unit_Destroyer` boot, render, take orders and fire when made
    buildable; the battleship's model has no chassis bone, so it never moves visibly. The skirmish mesh packs
    `Pack\GFXDescriptor\MeshSkirmish_<nation>.spk` have `…WitBoat_…` variants (`ia/cluster.cpp`).

**Naval units exist:** `Descriptor_Unit_Battleship`, `_Destroyer` and `_LCVP` (ships named USS Texas, Nevada, Arkansas and
others: the Normandy mission). Whether players can control them in skirmish is untested.

**Debug-info copies:** ZZ_GladPatchableWin ships `*_debuginfo.cpp.gladndfbin` next to four data files (`everything`,
`vfx_bank`, `visibility`, `ia\launcher`). They repeat every export name of their main file; two are the same size as
their main file, the other two are larger. The game ran with them untouched while the main file was modded (C2) and
with them rewritten too (C4), so which one it reads, if any, is unknown. `ruse build` leaves them as shipped.

## 3. Nations

- `Nationalite` is an int32 on unit, infantry, aircraft, building, truck and acknowledgement descriptors.
  Stored values are 1–6; 0 is the default and is not written.
- The enum: **0 US, 1 GER, 2 UK, 3 FR, 4 ITA, 5 USSR, 6 JAP.** The game keeps its units in exactly seven
  per-nation lists, fixed in the game itself, not in its data: a unit with any other `Nationalite` corrupts the game
  as it loads, so `ruse build` refuses it. An 8th nation can't be added there through data.
- A nation's unit models are loaded only in a skirmish where a player has that nation, or that the cluster map
  forces. Each scenario's `clustermap` (`genglad\patchable\scenario\<map>\<scenario>\`, 85 in ZZ_GladPatchableWin)
  holds three `TClusterLoadSelectifResource` loaders, of the per-nation proxy, mesh and animation packs. Their
  `SkirmishPacks` list one pack per nation in `Nationalite` order (the mesh ones are the seven `MeshSkirmish_<nation>.spk`
  in ZZ_Win.dat, `gen_5\pack\gfxdescriptor\`: `us ger uk fr ita urss japan`, plus `MeshSkirmishWitBoat_US`). In a
  skirmish a loader loads its `SkirmishCommon` and `SkirmishPacks[i]` for each nation i in the match and each bit i
  set in its `ForceLoadBitFieldIfSkirmish` (a uint32; no shipped loader sets it); in other games (campaign chapters,
  Operations), its `NotSkirmishPacks` and nothing else, the force bit included. 55 cluster maps list one pack of every
  nation's there (`PackMesh_All`); the other 30 list only the nations their mission plays, one pack each (Holland's
  chapters: common, US, GER, UK; Colditz: common, US, GER; Italy and D-Day name `…SkirmishWithBoat_US`, which holds
  all 71 models of `MeshSkirmish_US` and five ships), so the build adds a needed nation's pack to those lists
  (`unitcheck.load_in_missions`; tested on Colditz, T29). `ForceLoadBitFieldNationalite` (set to 2 on 4 objects of one
  scenario) belongs to `TClusterInitialisationExecuteSelectifSubClusters`: it picks sub-clusters, not packs.
- A unit's models are the `.ase2ndfbin` files its `Gfx…` parts name (the mesh is an unnamed object they refer to).
  Every shipped buildable unit has its models in its own nation's pack or the common one, except the six non-US
  atomic cannons, which use the US Long Tom's. Moved to another nation, a buildable unit misses its model in every
  case (1,362 unit × nation pairs). Setting that nation's bit in every loader's `ForceLoadBitFieldIfSkirmish` (a Ju 87
  copy for the US: Germany's bit, 2, in 255 loaders of 85 cluster maps) crashed the game when the unit was built
  (T13, batch 1), so that is off (`build.FORCE_LOAD`). Instead `ruse build` copies such a unit's models into the
  skirmish packs of the nation it now belongs to, and a spawned unit's into the common ones (§8, "Skirmish unit
  packs"), and says so in a note; it refuses the unit only when a model can't be copied.
- Several structures have exactly 7 slots: `SubClusterNationaliteList` (every map), flag-icon lists, per-nation
  mesh packs, and the bit field `BitFieldNationaliteIfNotSkirmish` (values 0x3F, 0x403F…; bit 14 unexplained).
- **Conclusion (medium confidence):** rosters are data-only. Whether an 8th nation can be added through data alone
  is the open question (PLAN.md decision 19; China stays, and no faction is replaced).
- **Nation scan** (`tools/nation_scan.py`, PC 2026-09-28, 2,172 NDF files, the 4 debug-info copies skipped, 5 s).
  Summary: an 8th entry is needed in 5 named per-nation structures (518 objects in 86 files); Chinese versions of 6
  kinds of nation-tagged objects; 1 bit field.
  - Objects with a nation (US / GER / UK / FR / ITA / USSR / JAP): `TAcknowUnitDescriptor` 3,322 (481 / 467 / 475 /
    468 / 467 / 468 / 496), `TUniteAuSolDescriptor` 204 (43 / 37 / 26 / 24 / 26 / 24 / 24), `TBatimentDescriptor` 135
    (22 / 22 / 18 / 17 / 19 / 17 / 20), `TAvionDescriptor` 63 (15 / 13 / 8 / 6 / 6 / 8 / 7), `TInfanterieDescriptor` 39
    (7 / 6 / 4 / 4 / 7 / 4 / 7), `TTruckDescriptor` 18 (5 / 3 / 2 / 2 / 2 / 2 / 2).
  - The starred 7-item lists (named after nations, flags or countries):
    `TClusterInitialisationExecuteSelectifSubClusters.SubClusterNationaliteList` (510 objects, 85 files),
    `TUniteAuSolDescriptor.InitialFlagSet` (5 objects, 1 file), `TLoadingScreenMultiplayerDataBag.NationalityIcons`,
    `TPlayerLabelDescriptor.NationaliteIcones` and `TReplayPlayerInfosResource.NationaliteIcones` (1 each).
  - Unstarred 7-item lists that sit next to them and may also be per nation: `SubClusterPlayerList` (510 objects,
    85 files), `TClusterLoadSelectifResource.SkirmishPacks` (255, 85 files), `SubClusterList` (170, 86 files).
  - The bit field `BitFieldNationaliteIfNotSkirmish` uses 0x3 … 0x3F (bits 0–5) and 0x40 (bit 6, Japan), each also
    with bit 14 (0x4000) set: 0x403F ×224 is the most common value. Bit 14 is still unexplained.

## 4. Localisation (`.dic`)

`TRA\0`, `u32 count`, then `count × (u64 hash, u32 byteOffset, u32 lengthInUtf16Chars)`, **sorted by hash**, then
UTF-16LE strings. Verified on all 1,232 `TRA` files. NDF refers to strings by the same 64-bit hash (type 0x1D).
For new strings we can choose unused hash values, so we don't need to know Eugen's hash function.
**Verified on all 1,232 files (2026-09-28, `tools/dic_check.py`), 132,077 entries:**
- The 4th magic byte is **0 in every file** (RUSE-Mod-Manager's note that shipped files use 1 doesn't hold for this build).
- Keys are sorted everywhere; every text sits after the table (offsets from the file start); texts have no UTF-16 null.
- 33,965 entries share a text with another entry.
- **Keys are packed names, not hashes** (6 bits per character, as in Wargame): 130,845 of 132,077 decode, e.g.
  `64muIaV4q3` = "Afrikakorps". New keys can be minted with `name_to_key()`.
- The 1,232 that don't decode are **one special entry per file, key `0x8000000000000000`: the list of characters that
  file uses** (e.g. `" AIENSdDLirloeT…"`), probably so the game preloads those glyphs. **A writer must add any new
  character to it.** moddingSuite (Wargame) rebuilds it as every character, most used first, which matches the
  example; our writer (`src/rusemod/dic.py`) keeps the list as it is and adds new characters at the end.
- Languages: `us`, `fr`, `ger`, `ita`, `spa`, `pol`, `ru`, `cz`, `jpn`, `sc`: 112 files each, plus `dev` (48) and
  per-map script dictionaries (64).
- Writer check: adding an entry keeps every existing text readable and unchanged in all 1,232 files.
Other magics: `DICS` (18) and `DICV` (13) in `genvideos\…` (probably subtitles/video dictionaries) ❔.

## 5. Python scripts (`.xyz`, `.ipk`)

- `.ipk` = a nested EDAT pack of `.xyz` files.
  - eugen.ipk: 140 modules in package `eugen` (base, debug, defines, front, game, headup, interface, leveldesign, loadgame, tools)
  - eugenpatchable: 5 · eugensolo: 20 · eugentest: 15 · pythonpacklib25: 64 (standard library) · sonsgenerated: 1
- `.xyz` layout, all 327 files walked:

  | Field | Meaning |
  |---|---|
  | `XYZ0` | magic |
  | BE u32 `0x0A0DF2B3` | Python 2.5 magic 62131 |
  | BE u32 | size |
  | 16 bytes | MD5 of the `.py` source |
  | zlib stream at 0x1C | payload |

- The payload is a raw marshal code object with no `.pyc` header; `co_filename` looks like `datadir:\codeia\python\...`.
- Script packs and `sys.path` are declared in NDF (`TResourceDescriptorPythonPack 'Eugen.ipk'`, `TClusterAddPythonPath`),
  so a mod's script pack can be registered through data. Building one needs a real Python 2.5 compiler.
- **The unit registry (found 2026-09-28, checks C5–C6c):** `ZZ_Win.dat!genpython\eugenpatchable.ipk` →
  `parametres\classes.xyz` defines **456 classes**, one per unit, plane and building (bases `front.unit.*` 259,
  `front.avion.*` 63, `front.batiment.*` 134), e.g. `class Unit_M3_Lee(front.unit.TankUnit): descriptor =
  _ndf.Database.GetObject('$/GFX/Everything/Descriptor_Unit_M3_Lee')`. The module ends with one line per class,
  `Unit_M3_Lee.descriptor.base_class = Unit_M3_Lee`. **A unit with no class here is never used by the game**: copies in
  `everything` with a fresh id, name key, class name or slot never appeared in the menu, while the moved real Lee did.
  The level-design spawns name the class too (`PythonClassName = 'parametres.Classes.Unit_M3_Lee'`). The class name
  matches the unit's `ClassNameForDebug`. 111 registered units are hidden from every menu, but most are used behind the
  scenes (transports, HQs, planes for abilities); only a few (film and demo copies) are spare.
- **Adding a class without a Python 2.5 compiler** (probe C6d, `D:\RUSE-Instances\c6-named`): the module's code
  object gets 2 new constants (the class name and a class body copied from the source unit's, with the new
  descriptor path), 1 new name, and 14 instructions before its final `LOAD_CONST None; RETURN_VALUE` (the class
  statement and the `base_class` line, the same instructions the file already uses). New strings are written plain
  (marshal `s`), never interned (`t`), so the shared-string references (`R`) later in the file keep their numbering.
  Safety rules for this (PLAN decision 23) apply to every such edit.
- **Built (2026-09-29): `rusemod.pyscript`** reads Python 2.5 marshal data and `.xyz` files and adds classes from
  the one template; `ruse build` gives every copied unit its class. `tools/verify_pyscript.py` (read-only): all 327
  compiled scripts read; the unit list's 456 classes are all the standard template and all registered (bases:
  `unit.TankUnit` 183, `avion.AvionUnit` 63, `unit.Unit` 30, `unit.InfanterieUnit` 21, 19 building kinds); the
  build's output is byte-identical to the C6d probe that worked in-game.

## 6. Maps

**Registration:** `genglad\patchable\mapinfo.cpp.gladndfbin` (the non-patchable copy is identical) holds **86 `TMapLoadInfo`**
entries, each with a unique GUID. Fields:
- `Name`: display name with the player count as a prefix, e.g. "(6) Centre de gravite"
- `Path` and `RootDatapackName`: the folder name, e.g. `TwoIslands`
- `MapTypeMask`: 16 (68 maps), 1 (15), 18/20/24 once each
- `Show`: an import of `$/VersionOption/ShowOfficialMap` or `ShowEugenMap`
- `BakeThisMap`, two minimap icons, and `ClusterLoads{Std, WithoutRun}` → a `TNDFTransaction` listing source files compiled into `map\X\Scenario\ClusterMap.ndfbin`

Ladder variants (`Scenario_1v1 … 3v3_v01`) are separate entries.

**Pack mounting is data-driven:** each map's `clustermap.cpp` contains
`TClusterMountMapDataPack{ DataPack 'MapDat:\DataMapTwoIslands_v09.dat', DatasMapDirectory 'GenDatasmap/TwoIslands', MountingPoint 'Datasmap' }`.
Map names and paths all come from data. **Adding a map looks data-only.**

**One map spans 5 packs:**
- its own `Maps\PC\DataMap<Name>_v09.dat`
- DataMap_Win (`mapinfo.win`, `.scenario`)
- about 17 NDFs in ZZ_GladPatchable (`map\<name>\…`, `scenario\<name>\…`)
- env maps in ZZ_Win (`gen\datasmap\<name>\*.tgv`)
- `effetmap.xyz` in IA_Common

Map packs also hold models (`.spk`), textures, AI grids and sound banks.

**A new map** (built: `rusemod.newmap`, MOD_FORMAT §8; seen in the game 2026-10-03: listed in BATTLES and playing its
own ground, 101 new maps at once, `TESTS.md` T15b and T16). How a shipped map's files name
each other, which is what a copy under a new name changes (read from the data, 2026-10-01):
- Its map-list entry (`TMapLoadInfo`, a top object: TOPO lists exactly the 86) loads its scenario's cluster through
  `ClusterLoads` → `TClusterWithNDFLoadedSubCluster` → `TNDFTransaction.BaseName`
  (`Patchable\Scenario\<map>\<folder>\ClusterMap`, compiled as
  `genglad\patchable\scenario\<map>\<folder>\clustermap.cpp.gladndfbin`).
- That cluster names the scenario twice (`ScenarioPath` and `TScenarioLoader.FileName`:
  `DataDir:\Test\Map\<map>\<file>.scenario`, which is `test\map\<map>\<file>.scenario` in DataMap_Win.dat) and loads
  the map's cluster (`Patchable\map\<map>\ClusterMap`). Its other files (camera paths and bluff zones in `MapIA`,
  dialogue, the in-mission texts) a copy shares with the shipped map.
- The map's cluster mounts the pack (`TClusterMountMapDataPack.DataPack`, `MapDat:\DataMap<Name>_v09.dat`: the pack is
  found by that name alone, C3; `DatasMapDirectory` and `MapDirectory` stay as shipped) and loads the map's constants
  (`Patchable\map\<map>\MapConstante`), whose `TCurrentMapInfo.MapPath` names `DataDir:\datasmap\<map>`, the folder
  of `datasmap\<map>\mapinfo.win` (with `TMapInfoGeneratorInfo.MapInfoPath` `MapInfo.IA`).
- The BATTLES entry (`TMultiMapInfo`) has the map-list entry's GUID, is reached only through a `TMultiPack`'s
  `MultiList` (never a top object), and has its menu name as a text key in `flash_txt.dic` (the shipped 30 are
  `M_D_01`-`M_D_30`, their `TrackingId`s `MP01`-`MP30`).
- No member of a map pack, no scenario and no grid holds the map's name, and a pack's header id is named nowhere in
  ZZ_GladPatchableWin, DataMap_Win or IA_Common: a copy works under a new name, and gets a new id.
- All 31 BATTLES entries of the shipped game copy this way (a dry run of the build, 2026-10-01); the maps BATTLES
  doesn't list (the campaign's, the Operations', the test maps) are refused.

| File | What we know |
|---|---|
| Map pack header "checksum" | ✅ **not a checksum: a random ID.** The 16 bytes at 0x08 are a Windows GUID (`uuid.UUID(bytes_le=…)`), version 4 with the RFC variant, in all 32 map packs (chance by accident ≈ 64⁻³¹). The game can't check it against the contents. Gamma and Gam_Ostfriesland share one (same pack). Every other archive has zeros there. Edits keep it; a new map gets a fresh `uuid4()`. Its use (map identity in multiplayer or replays?) ❔ |
| `save.boobspc` | ✅ bytes 0–15 = MD5 of bytes 16..end; then version string `0.6`; uncompressed. The game checks it, so a rewrite must recompute it |
| `output.sdb` | ✅ `SDB\r\n` + MD5 of the whole file with the 16-byte hash (at 5–20) removed |
| `.scenario` | ✅ `SCENARIO\r\n` + 16 bytes, **the MD5 of bytes 0-9 and of byte 28 to the end** (LittleGroove's rule in RUSE-Mod-Manager; true of all 102 files; the game checks it at launch and crashes when it's wrong) + 2 zero bytes + u32 version 4 + u32 1, then the zones (u32 size + `AREA` records: a named polygon per zone, cut into triangles, with its border and a list that closes the outline, each ending `END0`) and the design items (u32 size + an NDF of `TGameDesignItem`s: Position, Rotation and an AddOn: `StartingPoint` (alliance, camera, warm-up path), `Spawn` (camp, the class that arrives), `CircularZone`, `RectangleZone`, `LabelVille`, `LabelMontagne` (text in UTF-16), `Name` (waypoints)). Every byte of all 102 files is read (`rusemod.scenario`; its docstring has the layout). The layout was worked out for Wargame by enohka's moddingSuite and RugnirViking's RUSE fork of it; R.U.S.E. differs only in the list at the end of each zone, which Wargame writes empty |
| `mapinfo.win` | `INFOIA\r\n` + 16 bytes (not an MD5 of the rest; probably the `.scenario` rule, the MD5 of the magic and of what follows the 16 bytes and 2 more: unchecked) + AI grids (concealment and movement-blocking layers) ❔ |
| `.tms`, `.tmst_pc`, `.tmst_chunk_pc` | ✅ terrain mesh and texture tiles: see "Terrain" below |
| `.kdt` | ✅ the gameplay ground and the camera floor: see "Gameplay ground" below |
| `.fpkpc` | `SFXS` ❔ |
| `.sourcefileid` | begins "Size" ❔; only for div_map, env_map faces and occlusioninfo (source-asset size/MD5), none for terrain |

### Terrain (M1.5, 2026-09-28; code `rusemod.tms`, `rusemod.tmst`; checks `tools/verify_tms.py`, `tools/verify_tmst.py`)

**How the game uses it** (from `genglad\patchable\map\<map>\mapterrain.cpp.gladndfbin`, class `TTerrainLoader`):
- Two terrain loaders per map, both covering the same square. **HighDef** is used for the close camera:
  `HighDef.TMS` (mesh) + `HighDef.TMST` (tiles), 6×6 cells of 327,680 units on Two Islands, 5 detail levels.
  **LowDef** is used for the far camera: `Lowdef.TMS` + `LowDef.TMST`, 3×3 cells of 655,360 units, 4 levels.
- Each loader also has a whole-map **global texture**, a plain PNG in the pack: `Terrain.png` (HighDef,
  64 px per cell, max 2048) and `TerrainWithUnit.png` (LowDef, 128 px per cell). It is drawn where tiles aren't streamed in.
- The water simulation reads other files (`WaterInputs`, `WaterAcceleration`, `RiverIndirectionSurface` as `.tgv_pc`).
- The player's `GroundQuality` option picks scenery density (`TDecorsHabilleurCaseLevelConfig`).

**Heights live in 3 places:** `highdef.tms`, `lowdef.tms` (an independent, coarser mesh: shared points differ by up
to 6,224 units) and `occlusioninfo_terrainonly.kdt` (NDF `TStreamedMeshKdTree`, same bounds as highdef, 197,703
triangles, vertices and normals decoded, see "Gameplay ground" below; probably what picking, line of sight and maybe
pathing use). An edit must change both `.tms` files and the `.kdt`; whether gameplay follows the `.kdt` is the
next thing to learn.

#### Mesh (`.tms`, magic `TMSG`), little-endian

Header (0x368 bytes):

| off | type | meaning |
|---|---|---|
| 0x00 | 4s | `TMSG` (the file also ends with `TMSG`) |
| 0x04 | u32 | version 3 |
| 0x08 | 4s | `PC\0\0` |
| 0x0C | u32 | file size |
| 0x10 | u32 ×3 | grid_w, grid_h (cells), patches per cell side = 8 |
| 0x1C | f32 ×2 | cell width, cell height (world units) |
| 0x24 | (u32 off, u32 len) ×3 | cell table (at 0x368, 48 B per cell), patch tables, geometry pool; contiguous |
| 0x3C | 512 B | vertex type, zero-padded: `$/M3D/System/VERTEXTYPE/TVertex__PositionIn4w_4w__NormalIn01_4ubn` |
| 0x23C | f32 ×6 | bounds min x,y,z / max x,y,z (world units; also the quantization range) |
| 0x254 | (u32 off, u32 len) ×2 | skirt descriptor (548 B), skirt data |
| 0x264 | — | zero up to 0x368 |

- **Cell record** (48 B, row-major): `flags, vb_off, vb_len, vertex_count, list0 (off, len, index_count), list1 (off, len,
  index_count), patch_off, patch_len`, all u32, offsets relative to their section. Flags: bit 0 = list 0 (always),
  bit 1 = list 1, bit 2 = 32-bit patch table. The pool holds per cell: vertex buffer, list 0, list 1, each 4-aligned.
- **Triangle lists:** u32 byte count, then zlib ended by a sync flush (no final block, no Adler). Data = u16 running
  differences (index k = sum of the first k+1 values, mod 65536). List 0 = the whole ground; list 1 repeats the
  list-0 triangles under water.
- **Patch table** (8×8 = 64 records): `vstart, vcount, i0start, i0count, i1start, i1count` (u16, or u32 with flag bit 2),
  then f32 zlo, f32 zhi. zhi = highest max(z, water) of the patch; zlo = lowest z, or exactly 0.0 without list 1.
- **Vertex buffer `VBUF`:** `VBUF`, u16 8, u8 0xA1 ❔, u16 stride 12, u16 2 elements, u8 flags 2; u32 length + a
  predictor stream; then per element `SUBP`, u16 12, u8 kind, u8 3 ❔, u8 mode 2, u16 bytes per vertex, u16 offset,
  3 zero bytes, u32 length, the stream. Position = kind 8 (4 × u16) at 0, starting with u16 mask 0xFFFF, u16 0.
  Normal = kind 4 (4 × u8) at 8.
- **Predictor:** vertices 0 and 1 have parent 0; then a 0 byte = previous vertex, else `0x80|hi, lo` = that many
  vertices back. Mode 2: value = (stored + parent's value) & mask, per component.
- **Vertex meaning:** (x, y, z, water) quantized 0..32767 over the header bounds (x, y span the full range whatever the
  aspect ratio; every file uses the full z range). Water = water-surface height on the z scale (the map's base level,
  e.g. 18,000 on Two Islands). Normal byte = round((n+1)·127.5), 4th byte 128; close to area-weighted face normals.
- **LZ stream** (vertex streams): 20-byte header `u8 1, u8 0x14, u8 method (8 = bytes, 16 = u16 units), u8 shift,
  u32 unit count, u32 literal count, u32 token count, u16 literal base, u16 token base`. u32 control words from 0x14,
  read from the lowest bit: 0 = copy the next literal, 1 = one token; a final single 1 bit ends the stream, then 4–7
  zero bytes. Tokens by the first byte's low bits: `11` + bit 2 clear = 2 B (len bits 3–6 + 4, dist bits 7–15 + 1);
  `11` + bit 2 set = 3 B (len bits 3–10 + 4, dist bits 11–23 + 1); else bit 2 set = 1 B (len low 2 bits + 1, dist
  bits 3–7 + 1); else 2 B (len low 2 bits + 1, dist bits 3–15 + 1). Units, overlapping copies allowed, max distance 8192.
- **Skirt** (what hangs from the map's edge; checked on all 32 maps): descriptor `u32 flags` (bit 0 the curtain,
  bit 1 the water's side), per submesh `u32 index bytes, vertex bytes, bounds bytes (0x60), part bytes (0x40)`, then
  the 512-byte vertex type `$/M3D/System/VERTEXTYPE/TVertex__PositionIn4w_4w`. Data per submesh: u16 indices,
  vertices 4 × u16 (x, y, z, 0), 4 parts' bounds (6 f32: min x, y, z, max x, y, z), 4 parts (u32 vstart, vcount,
  istart, icount). Submesh 1, the **curtain**: under every edge point a top at the ground's height and a foot at q 0,
  z on its own scale −3000..zmax (46,332 tops, the ground's height to within one step in 99.97%). Submesh 2, the
  **water's side** where the sea or a river meets the edge: from the ground up to the water surface, z on the mesh's
  own scale; 133 of its points lie between edge points, where the surface meets the bank. Hurtgen and Krak des
  Chevaliers have no water at their edges: flags 1, no submesh 2. Far meshes: all zero. Edits: the skirt follows
  moved edge points (`rusemod.tms`).

Proven: all 64 files (1,390 cells) rebuild byte-identical; every cell re-encoded with our own LZ re-reads identical
(0.957× size, not byte-identical to Eugen's encoder); a mesa edit on Two Islands re-reads with exactly the new heights.
Open: in-game acceptance; `.kdt` copy; raising above the file's top height needs re-quantizing (edits are clamped).
(The water list is rebuilt after edits: `Tms._water_lists`, wherever moved ground meets water.)

#### Texture tiles (`.tmst_pc` index + `.tmst_chunk_pc` store)

A tile set is a pyramid of 512×512 DXT1 tiles over the grid of cells. LowDef has half the cells per side, and its
level k matches HighDef level k+1 in area.

| off | type | meaning (`.tmst_pc`) |
|---|---|---|
| 0x00 | 4s | `TMST` (also the footer) |
| 0x04 | u32 | version 3 |
| 0x08 | 4s | `PC\0\0` |
| 0x0C | u32 | size of this file |
| 0x10 | u32 | key: opaque per set, also the record separator in the store (not CRC32/Adler/MD5 of the data; keep it) |
| 0x14 / 0x18 | u32 | grid width / height in cells |
| 0x1C | u32 | depth 3 (tiles per cell: 1, 2×2, 4×4) |
| 0x20 | u32 | size of the store (the only cross-reference; the writer updates it) |
| 0x24 / 0x28 | u32 | offset (0x4C) and length of the record table |
| 0x2C | u32 | 0 ❔ |
| 0x30–0x3C | u32 ×4 | (0x44, 0) and (0x48, 0): the empty ATEX and KEYS bodies (inferred) |
| 0x40 | 12 B | `ATEX` `KEYS` `TEXF` |
| 0x4C | (u32 off, u32 size) × n | one per tile, n = 1 + gw·gh·(1+4+16) |

- **Placement:** record 0 is a whole-map overview (next power of two of 64 px per HighDef cell). Then the levels coarse
  to fine: 1 tile per cell, 2×2, 4×4; cells row-major, tiles inside a cell row-major; x right, y down (the orientation
  of `terrain.png`). The proof is statistical (tile size vs terrain.png detail, r 0.68–0.89; the best layout in 32/32
  maps) plus the store order. No pixels were decoded, so a flip inside a tile wouldn't show.
- **Store:** `key`, then each record followed by `key`; records padded to 4 (the padding counts in the index size).
  The store order differs from the index order: column by column, overview last. Always go through the index.
- **Record** = a full TGV (see §7): `1, 1, w, h, w, h, u16 1 mip, u16 4, "DXT1", u32 0x28, u32 size`, then the payload.
  The payload is always **TGU1**: `"TGU1", u32 5, u32 w/4, u32 h/4, u32 80, u32 40, u32 block count, u32 256 (terrain;
  .tgv uses 257), u32 unpacked size`, then zlib ending in a sync flush. **The TGU1 body decodes** (`rusemod.tgu1`,
  2026-09-29): decoded tiles match each map's `terrain.png`, and the Studio draws maps with them (about 0.6 s per
  512 px tile in pure Python). Our encoder is experimental and isn't needed: the game accepts plain ZIPO tiles.
- **Integrity:** no other pack member records the terrain files' sizes, hashes or names (every member of all 32
  packs was searched). The pack's 16-byte header ID isn't a hash (see the table above).

Proven: unchanged rebuild byte-identical for 64/64 sets and 32/32 whole packs (2.2 GB, about 41 s); replaced tiles of
any size re-read correctly, with every other tile unchanged.
**In-game (2026-09-29): the game accepts our rebuilt store with every tile a ZIPO tile** (raw DXT1 + zlib) instead of
TGU1. The checker test (`verify_tmst.py --make-test TwoIslands OUT checker`, Two Islands = "Centre of Gravity") drew our
checkerboards at two detail levels (magenta/yellow and cyan/red) with no problem. **So terrain textures can be written as
plain DXT1: no TGU1 encoder is needed.** TGU1 decoding is still useful for reading the shipped textures.

#### Road stickers, the road model and the close-up map (2026-09-30, 2026-10-01; code `rusemod.scenery.RoadPiece`, `rusemod.roadstrips`)

**Seen in the game** (T12, passed 2026-10-02): from afar, roads are painted into the ground's tile pyramid
(`highdef`/`lowdef` `.tmst`). **Up close, a road is drawn by asphalt stickers**: ordinary scenery objects of a sticker
type (`Route_Bitume` on D-Day; the scenery decors' `TSceneryDescriptorSticker`), one every 1,506 to 1,598 map units
along the road, size 2.0, its x axis along the road, each with two edge stickers (`Route_Bitume_Bords`) at the same
place 1,361 to 1,405 across, the right one turned as the asphalt, the left one turned round (D-Day: 22,841 pairs).
The descriptors: footprint -512 to +512 (asphalt and edges), `EndLinkPos` 380 for the asphalt, `ZOrder` (a float)
edges 27, `Route_Bitu_Demi` 44, `Bitume_Base` 49, asphalt 56, the fade stickers 57 and 58; all Mode 16. Every shipped
map with roads lays them this way with one of three pairs (`Route_Bitume`/`Route_Bitume_Bords` on 27 maps,
`RouteBitume`/`Bords_Route` and `RouteBitumeTunisie`/`Bords_Route_Tunisie` on the desert maps). The road pieces and
road model below draw the far road, not the close one: batch 11 set the `Route` strip's colour to red and the roads
came out blue from high up, the close-up road unchanged. The story: [ROADS.md](ROADS.md).

The scenery's **road pieces** are what the road model was made from: `Route` items, whose
descriptor `TypeWarrior/Route` (category `LB`) is a `TSceneryDescriptorMultiMode` whose mode 128 is a
`TSceneryDescriptorBezierTriangleString` (Width 400, Color dcdcdc64, BezierMaxError 500), the strip. The maps' decor
levels gather modes 8, 4, 0x14 and 3, never 128; mode 128 is named by the static mesh `Road` (below). (Read from the
settings; how the game draws either isn't known.) D-Day has 431 pieces, all `Route` (name flag 2), in 40 blocks (many inside village blocks
placed several times); a piece is 4 to 290 m long (about 16 m typical), straight, its two handles a tenth of it along
it; its three trailing words are its block's count of road pieces (10,505 of 10,505 on the shipped maps), then two
words the same on every piece of the map (D-Day 129840992 and 1567752; Blitz 129958752 and 1567752). The item word is
`0x01000001 | symbol << 4`, no transform (the 15 words follow). Every shipped piece sits under draw-tree nodes with
the road mark (§6, the draw tree) and none is listed for far view (0 of 10,505); new pieces keep both.

**The road model (`output\staticmeshes.spkpc` or `output\staticmeshes_v02.spkpc`, model `road`; every map).** Each
map's terrain settings (`genglad\patchable\map\<map>\mapterrain`) hold a `TStaticLevelBuildManager` (CaseSize 81,920)
with two static meshes, `Road` (mode 128) and `Bridges` (mode 8192), from `DatasMap:\Output\StaticMeshes_v02` or,
missing that, `StaticMeshes`. Alpha, Gam_Ostfriesland, Gamma and Robert ship only the `_v02` file, Beta both, the rest
only `staticmeshes.spkpc` (2026-10-02; an earlier note said no map has `_v02`: wrong); which one the game loads when
both are there isn't tested, so the build writes new roads into both. A mesh pack (§8) of two models, `bridges` and
`road`, the same layout under either name. The road model is one draw call
(always the pack's last vertex and index buffer, stored as is, u16 indices) over the whole map:
- **vertex** (44 bytes, `TVertex__Position_3f__NormalIn01_4ubn__Normal2In01_4ubn__PSize_1f__Color0_col32__ArcLengths_2f__TexCoord0_2f`):
  position on the ground (z within a few units of `highdef.tms`), the road's direction, the flat side it widens to
  (b / 255 × 2 − 1), a width factor around 1 (0.9 to 1.8), colour dcdcdc64, two f32 0, (u, v): u −0.5, 0 or 0.5
  across the road, v 400 (the Width). Three vertices at each point.
- **strips**: every road piece is its own strip, two points (more on a curved piece: D-Day's 4,693 pieces make 4,678
  strips, 4,612 of two points), 12 indices `0 4 3 0 1 4 1 5 4 1 2 5` from its first vertex. Pieces that meet share
  the point's direction and width factor, so the strips join.
- **parts**: the pack's fourth section, 48 bytes each: the vertices' box (6 f32), u16 case, u16 filler, u32 first
  vertex, vertex count, first index, index count, u32 filler; the fifth section: u16 first part, u16 count per draw
  call, the draw call's fifth word naming its group (0xFFFF in the unit packs, whose two sections are empty). A draw
  call's parts are listed by case, one each, its buffers in that order with no gap; indices count from the buffer's
  start. A **case** is a square of 81,920 map units; the cases are numbered along a curve (`roadstrips.curve`, order
  ceil(log2) of the longer side) over the map's grid, the squares off it skipped: every road part of the 28 maps but
  5 edge ones lies in its case.
- **header**: the hash at 0x10 is MD5 of bytes 0-15 and 0x20-0x2F; 0x20 (0, start of the index data), 0x28 (start of
  the index data, the rest of the file's size); 0x30 the model count; 0xB0 (x, 0, 0, x, 0) with x the index-buffer
  table's start; after the materials, `~` up to a multiple of 4. `rusemod.roadstrips` rebuilds all 33 files (both names) byte for
  byte, and adds a new road's pieces as strips in the map's own look, in the parts of their middles' cases.

(An earlier note here said Alpha, Gam_Ostfriesland, Gamma and Robert have no road model: they have it, under the
`_v02` name, and new roads were left out of it there until 2026-10-02.)

`output\div_map.tgv_pc` (D-Day: 3072 x 2048 DXT5_LIN in one ZIPO mip, about 5 m a pixel; Blitz and Bulge 2048 x 2048)
is a colour and alpha picture of the whole map. The map's own roads are only a faint lift in it (alpha +7 to +20 over
the ground beside them, a little less green); marking a new road the same way changed nothing up close (batch 5).

#### Bridge floors (`output\occlusioninfo_objectsonly.kdt`; 2026-09-30; code `rusemod.floors`)

A third tree of the same kind, "objects only": what units stand on at bridges (the gameplay ground dips into the
river under them like the visible ground). D-Day's: one subtree, 556 triangles, 690 points, in clusters exactly at
its 21 bridges; each floor runs from end to end 5 to 60 units above the ground at the deck's ends (Pont_Metallique_02:
8 triangles in four sections along the deck; _03: 24; the stone Pont_TangeantFloor: 12, arched). Its MainNode is the
six bound clips and one leaf. A new bridge without a floor is drawn, but units walk the riverbed under it (seen in
the game, 2026-09-30). `rusemod.floors` rebuilds the file as one subtree (its own k-d tree, every triangle found from
its middle; D-Day's rebuilt keeps every shipped point exactly).

**A floor is the deck's band and, on the metal bridges, two aprons (2026-10-01).** The 8 (or 24) triangles above are
only the middle slab. Each metal bridge has three slabs that abut within 2 or 3 units: the band, 440 to 670 either
side of the deck's line, and beside it two flat aprons exactly as long as the band, 20 to 30 above it, reaching 12,170
(the short Pont_Metallique_02), 12,790 (_03) or 17,230 (_02_TangeantFloor) from the line, over open river. The five
stone bridges have the band alone, 1,400 either side. Why it matters: where a unit is comes from the movement graph
and how high it stands from the topmost floor under that point, with nothing tying the two; and an infantry squad is
five men on an arc 2,828 wide (the game data's `Dispersion` 500 for `NbSoldatInGroupeCombat` 5; a man strays up to
`DispersionMax` 620 x 4 = 2,480 from the squad's place), each man standing on the floor under his own feet. Beside a
metal bridge the men off the deck stand on the apron, at the deck's height (740 to 840 above the water's surface on
D-Day); beside a stone bridge, or a new bridge given the band alone, they stand on the riverbed (about 2,000 below
it). So `rusemod.floors.apron` gives a new bridge a floor out to 3,200 either side of its line, in its band's plane,
over water only (tested in cells of 320: never over dry ground, never within 150 of the ground's height), its pieces
lapping the band and each other by 150 (the file's points sit on a grid, 61 by 40 map units on D-Day).

**Three rules every shipped floor file keeps (checked on all 29 maps that have one; `floors.rebuild` keeps them):**
every triangle faces up by the order of its points (all 556 of D-Day's); every point's normal is the one word
`0x7FFDFFF5`, straight up, whatever the floor's slope (all 45,188 points; the ground trees' normals do vary); no
triangle is a sliver. The game turns each man to the normal of what he stands on. Before 2026-10-01 our rebuilt file
had normals worked out from its triangles (207 of D-Day's 690 shipped points changed, the map's own bridges
included), and the first aprons had the points of one side's triangles the other way round: in the game men lay
sideways on the decks (the owner's screenshots, 04:14).

#### Movement graphs (`mapinfo.win` buffers 1 and 2; 2026-09-30; code `rusemod.nav`; check `tools/verify_nav.py`)

Where units can go: buffer 1 for infantry, buffer 2 for vehicles, each a graph of overlapping circles of ground,
linked where two meet. Every shipped graph reads and writes back byte for byte (66 graphs on 33 maps). Little-endian:

| part | layout |
|---|---|
| header | 84 bytes: u32 x0, u32 y0 (0, 0), f32 the map's side; u16 circles, links, crossings, **NX** (local maps); then 64 zero bytes (all 66 main graphs and all 1,241 local maps: the game fills them in while it runs) |
| offsets | u32 × (5 + NX), from the graph's start: circles, links, lists, crossings, index, then **one per local map**. A local map added or taken away changes the table's length, and so every offset after it |
| circles | (circles + 1) × 16 bytes: f32 x, y, radius; u16 where its links start in the lists; u16 where its crossings start. The last record closes both lists. Centres are on a 320 grid and radii multiples of 320 almost everywhere (98% of local circles) |
| links | 12 bytes each: u16 circle a < b, f32 x, y (the meeting point, inside both); sorted by b |
| lists | u16 link numbers, each circle's in turn (every link twice) |
| crossings | 28 bytes each: the road through a circle (f32 in x, y, out x, y, length; u16 the two links it goes between; u16 two road network links of buffer 0). The in and out points are where the road crosses each gate's line (through the link's point, square to the line between the two circles' middles; 892 of 892 on D-Day's vehicle graph, within 0.4), the length is the shortest way along the roads between them (within 0.1), and the lower link comes first. A circle has one for each two gates a road passes in a row, heading into the circle at both. Units plan along roads only through these (`Graph.add_crossings` makes them for new roads) |
| index | a bounding-interval tree over the circles: branch (u16 tag, u16 jump, f32 the left half's far edge and the right half's near edge on the branch's axis, x and y by turns from x) or leaf (u16 byte length, u16 circle numbers). On all 1,307 shipped graphs each edge is exactly its half's reach, the circles are split by their centres on the axis, and leaves hold 1 to 7 circles |
| local maps | the same layout again, with NX 0, the main graph's box and zero header bytes |

**Local maps.** Local map k belongs to main circle k, for every k below NX, and nothing else ties them (no table,
flag or order): the owners are the first NX circles (largest first on every shipped graph, the other circles largest
first after them). D-Day has 44 per graph, Blitz 22. In the game, inside an owner circle:

- units stand only where its local map has a circle (a town's keeps them off its buildings, a bridge's on its deck);
- a route through the owner is searched again inside its local map, between where it comes in and where it leaves;
  if that search fails, the whole route fails, so a local map is one piece, and has a circle at the points where the
  main links meet its owner (11,830 of 12,007 shipped ones do; the others are only near one);
- an order into the owner goes to the nearest circle of its local map, kept inside the owner.

No other main circle's middle lies inside an owner on any shipped map; owners themselves rarely overlap (14 pairs in
66 graphs). Most bridges have one (215 of the 223 shipped bridges on 24 maps; D-Day: 16 of 21): an owner of 8,000 to
22,080 (median 18,240) over the crossing, and local circles along the deck, mostly of radius 640 (also 320, 960,
1,280), about 870 apart, with circles fanning out over the banks to the owner's edge; the water beside the deck is
left without circles, so it isn't ground. A local map's circles all have their middles inside its owner or another
main circle. How the game uses local maps was worked out by DomesticNukes and his Claude, and checked by us.

**New bridges** (`Graph.open`, 2026-09-30) get one the same way: an owner over the deck (centred at its middle; as
small as holds the deck and meets the ground at both ends by 320 or more; no other circle's middle inside it, no other
owner overlapped), put in at circle number NX: every later circle's number goes up one in the links, lists, crossings
(their links' numbers, as the links stay sorted) and the index (the owner listed beside the nearest old circle, the
branches on the way widened to reach it); NX goes up one, the offset table gets one more entry, and the new local map
goes after the old ones. Its circles: the deck (radius 640, at most 640 apart, end to end, within the 663 either side
our bridge kinds' floors give), copies of the main circles the owner overlaps (so the banks inside it stay ground just
as before, and every point where the owner's links meet them is on its ground) and the approach circles that fall in
the owner; its own index is built as the shipped ones are (median split, x first, leaves of up to 4). A deck whose
middle is in an old owner (a replaced bridge of the map's) goes into that owner's local map instead: its circles over
the water near the new deck go (with whatever only they held to the rest: some maps have a row of small circles beside
a deck), the deck's come in. An old deck of plain main circles (3 of D-Day's bridges) goes from the main graph the same
way before the new owner goes in. Tried on every bridge of 7 maps (91) with a road over it, both graphs: 88 open (85
in their old owner, 3 with an owner of their own), none with water units can stand on that they couldn't before; 3
stay closed (a deck past its owner's edge; two bridges with no ground of their owner anywhere near). Not tried in the
game yet: a graph with more local maps than it shipped with.

**Closed ground has no circles** (2026-10-01; TwoIslands, Valley and D-Day, both graphs, sampled 200 × 200 over the
map's square). No shipped graph has a circle of radius 0 or a live circle without links, main or local (6 of 6
graphs, every local map): ground the map closes to units is simply ground no circle covers. Water: 4 of 3,706 wet
samples walkable on TwoIslands (infantry), 0 of 17,145 on D-Day, 17 of 1,395 on Valley. Dry ground closed inside the
circles' reach: 7,370 samples on TwoIslands for infantry, 12,190 for vehicles (woods), 2,241 / 3,434 on D-Day,
8,570 / 12,213 on Valley; and every dry sample that is under a circle but closed is inside an owner whose local map
leaves it out (a town's buildings: 335 on TwoIslands' infantry graph, 160 on D-Day's, 235 on Valley's). So opening
ground (`Graph.open_ground`, the Open brushes) is adding circles: in the main graph where no circle is, and in the
local map where the ground is inside an owner. Tried in memory on those three maps (an open of 3,000 on a town's
building, on closed dry ground and on water, vehicles): 8 of 9 walkable after, the graph and its local maps still one
piece each, read back byte for byte; the ninth (TwoIslands' dry spot) reached no ground units use by 320 and stayed
closed, with a note.

#### Gameplay ground (`.kdt`; 2026-09-29; code `rusemod.kdt`; check `tools/verify_kdt.py`)

Two per map pack: `output\occlusioninfo_terrainonly.kdt`, the ground gameplay runs on (same bounds as `highdef.tms`;
every vertex sits on a `highdef.tms` vertex), and `output\occlusioninfo_camera.kdt`, the camera floor (fewer, larger
triangles). Each is an uncompressed NDF binary (§2) holding one object of class `TStreamedMeshKdTree`:

| property | type | meaning |
|---|---|---|
| `RTVersion` | u32 | 0 |
| `BoundingBoxMin`, `BoundingBoxMax` | 3 × f32 | world bounds, also the quantization range; the min is left out of the file when it is (0, 0, 0) (7 of the 32 ground files) |
| `TriangleCount` | u32 | triangles of the whole mesh; smaller than the sum of the subtrees' index counts (subtrees repeat the triangles on their borders) |
| `OffsetOf…` (8 of them) | u32 | where each region of `Storage` starts, see below |
| `IsStreamPacked`, `IsCompressed` | u8 | 1 |
| `SubtreeCount` | u32 | 11–312 |
| `Storage` | blob (0x14) | u32 length + the regions below |

- **Chunk:** u32 L, u32 inflated size, then a zlib stream of L − 4 bytes ended by a sync flush (no final block, no
  Adler), like the `.tms` triangle lists. A few hundred shipped chunks stop one byte short of the flush marker;
  zlib's `decompressobj` reads both, and the writer keeps a chunk's original bytes unless its content changed.
- **Storage regions, in this order** (each `OffsetOf*` property is a region's start; the regions touch, the last chunk
  ends the blob): per subtree a positions chunk then a normals chunk | `VertexBufferIndexes`: u32 per subtree, the
  offset of its positions chunk | `IndexBuffer`: per subtree u32 index count + one chunk (the index buffer, not
  decoded) | `IndexBufferIndexes`: u32 per subtree, relative to `IndexBuffer` | `TriangleIndexLists`: one chunk per
  subtree (not decoded) | `TriangleIndexBufferIndexes`: relative; then zero bytes so that `MainNode` starts 8-aligned
  | `MainNode`: raw bytes up to the next region (not decoded) | `CompressedSubtreeIndexBuffer`: u32 per subtree,
  relative to `CompressedSubtrees` | `CompressedSubtrees`: one chunk per subtree (not decoded).
- **Positions chunk, inflated:** u32 n, u32 mask 0x7FFF, 3n u16 residuals (x, y, z per vertex), the parent codes of
  the `.tms` predictor (0 = the previous vertex, `0x80|hi, lo` = that many vertices back; vertices 0 and 1 have parent
  0), then fill bytes up to 8 + 12n (0xAA in half the maps, mostly 0xDD with stray bytes in the other half: memory
  junk, ignore it; we write 0xAA). Coordinate = (residual + the parent's coordinate) & 0x7FFF: the position quantized
  over the object's bounds, 0..32767 like the `.tms`.
- **Normals chunk, inflated:** one u32 per vertex. Bits 0–3 = the dominant axis and its sign (0 −x, 1 +x, 2 −y, 3 +y,
  4 −z, 5 +z; about 94% are +z). With axis k, a = n[(k+1) mod 3] / |n[k]| and b = n[(k+2) mod 3] / |n[k]|; bits
  16–31 = round(a · 32768) + 32768, bits 4–15 = round(b · 8192) as 12-bit two's complement, which **wraps** when
  |b| > 0.25 (the shipped files do wrap, so a writer must too or its words differ). Decoding: unpack a and b, set the
  axis component to ±1, normalise. In the one exact tie between two axes in 3.5 M vertices the later axis (z over x)
  was used.

Proven (`tools/verify_kdt.py`, 64 files, 3.5 M vertices): every file rebuilds byte-identical from its parts (tables,
padding and offset properties recomputed); decoding then re-encoding every subtree's positions and normals reproduces
the shipped inflated bytes (positions up to the end of the parent codes); a replaced positions or normals chunk reads
back with the new content and every other part unchanged (on made-up data). Open: the index buffer, triangle list,
`MainNode` and subtree encodings (kept as bytes, so vertices can move but the mesh can't be re-cut); in-game
acceptance of a moved vertex.

The file's role and its container framing follow the notes of DomesticNukes and his Claude; the vertex and normal encodings were worked out here.

### Scenery: `output\save.boobspc` (code `rusemod.scenery`; check `tools/verify_scenery.py`)

Every tree, house, field, road piece and ground decal of a map. The layout follows the notes of DomesticNukes and
his Claude; checked here on all 32 maps.
- **Container:** bytes 0–15 = MD5 of the rest (the game refuses a wrong sum); `0.6\0`; 26 u32 fields, offsets from
  the file's start: block table (offset, count), block data (offset, size), per-name flags (offset, count), name
  table (offset, size), an optional table, a second name table, layer boundaries (u32s), the three grids' sizes
  (Low, Mid, Hi: 16×16, 64×64, 256×256 on Blitz) and each grid's (offset, size). Then the block table (one u32 per
  block, from the data's start, and the data size as an end marker), the data, the names (u32 length + text; one
  per flag byte, then an empty one), the flags (1 = a scenery type, 2 = special: `Route`, factory markers), the
  other tables and the grids.
- **Block:** u32 (bit 31 = long header, the rest = entry count), u32 tree-node count, bbox 4 × f32, then to +0x20
  (long) or +0x1C; the entries (u32 item offsets from the items' start; a block seen from far lists its far-view
  items first, then every item again), the tree's 8-byte nodes, the items.
- **Item:** a u32 word, then its transform. Bit 31 = an object (name index = bits 4–23); bit 24 = a road piece (15
  more words, a cubic Bézier: its start x, y, z, the start's handle as an offset from it, its end, the end's handle
  as an offset from the end, then 3 and two codes on every piece seen; pieces chain end to start with their handles
  in line; `Scenery.roads`). A road piece's name is the special type `Route` (flag 2); the first of its three
  last words is how many road pieces its block holds, the other two look like left-over editor addresses. **From
  afar, the roads a player sees are painted into the ground's texture tiles**; the pieces lie exactly on them
  (checked on Blitz's ground picture); up close the road is drawn by asphalt stickers, ordinary objects (above;
  T12, 2026-10-02); otherwise a child block (offset = bits 2–23, always after its parent). Transform by
  bits 0–1: 3 = 12 f32 (3 rows of 4), 2 = a move (3 f32), 1 = none, 0 = compact (4 int16 × 3/32767 for the 2×2 turn
  and scale, then x, y, z and the height scale as f32; so compact sizes stop at 3.0).
- **Objects stand at height 0**; the game sets them on the ground. A name is a scenery type: a descriptor in the
  unit-data pack under `genglad\patchable\scenery\` (by `RegistrationName`), whose `Classement` is the game
  editor's category and whose close-up model is a `ModelASE` path (through `SDFalse` and the nearest `ModeEntry`).
- **Counts:** 321,029,228 objects and 78,417 road pieces on the 32 maps (Blitz: 5,028,739 and 1,389, in 753
  blocks). A few names on Blitz, Chess, Cotentin and Swamps resolve to no descriptor in the game itself.
- **Proven in the game (DomesticNukes):** moving, turning and scaling objects in place; adding objects through a
  new block that an existing object's item is turned into (a same-size child reference). A child that points
  backward breaks the map.
- **The draw tree:** every map has one top block (block 0). A block's 8-byte nodes (u32 word, u16 split, two bytes)
  are a spatial tree over its entries: a node holds entries [lo, hi), its left side [lo, split) is the next node and
  its right side [split, hi) the node `(word & 0xFFFFF) >> 2` further on; word bit 30 makes the left side a leaf,
  bit 31 the right, bit 28 the whole node. Bits 20-24 are the LOD mask (8 = far), **bit 25 the road mark**: every
  shipped road piece sits under nodes that carry it, from the block's root down (the game draws the roads from the
  map's road model instead, below: the mark is kept on new pieces to match).
  A node splits its box along x (`word & 3` = 0) or y, the two bytes being the left side's top and the right side's
  bottom as shares /255 of its extent (the root's box is the block's), so each node's box is a share of its
  parent's: widening one moves every node below it. The first node's split is how many entries are listed for far
  view (listed first: 7,144 of Blitz's 18,770 top-block entries, 7,132 of them references to blocks, 12 objects:
  bridges and a lighthouse); with the far bit on the root, close-up drawing starts at its right side. The game reaches a block only through
  the tree node holding its reference: objects hung on a close-view decal 3 km away never showed (owner's test,
  2026-09-30). Proven the same day: new objects in a new block that wraps the nearest block the top block lists for
  far view (the reference points to the new block, which places the old one where it was and the new objects;
  inserted right after the top block, every later reference moved by its size) show in the game, at every zoom.
  Placed buildings are only drawn: units walk through them (movement lives in the map's movement data).
- **The three grids** (header fields 14-19 their cells across and down, 20-25 each one's offset and size): far,
  middle and close, cells 81,920, 20,480 and 5,120 map units across, records of 4, 5 and 3 bytes, column after
  column (`x * down + y`). The game draws a level only in the cells whose record says they hold something: the close
  grid's third byte from 1 to 0xFE, the others' not 0xFF and not all zero (the third byte counts the cell's objects,
  about one per 64). On all 32 shipped maps no placed object lies in a cell its level skips; a new object's cells
  are marked (`scenery._grids_hold`), and one outside the grids is refused.
- **An object item's word:** bits 26-27 its detail tier (an item above the player's scenery detail isn't drawn: a
  new object takes tier 0), bits 28-29 a variation the game turns the object by, from its own coordinates (a new
  object takes none, so it stands as placed).
- **Header table at field 12** ("layer boundaries", 4-8 u32s): not block starts on most maps; left as they are when
  a block is inserted, and the game ran fine.
- **Blocks are padded** to 16 bytes with zeros after their last item (on Blitz: 116 blocks end flush, the rest with 4,
  8 or 12 bytes), and **hundreds of shipped tree leaves are empty** (a node side holding no entry: 74 on Edge, 362 on
  D-Day), so a leaf may be left with nothing in it.
- **Erasing (2026-10-01; code `scenery.erase_objects`; check `tools/verify_erase.py`).** Almost every tree is in a
  block the map places many times (D-Day: 11,550,293 trees, 34,487 of them, 0.30%, in blocks placed once; Blitz
  0.25%, Ardennes 0.10%), so an object can't be taken out where it's stored without taking it out everywhere that
  block is placed. Two ways were measured read-only, 50 m and 200 m circles (radius) over each map's densest wood and
  densest town; trees and props erased:

  | map, spot, radius | erased | (a) copies | (a) bytes added | (b) wrongly lost |
  |---|---|---|---|---|
  | D-Day, wood, 50 m | 548 | 20 | 134,752 | 23,651 |
  | D-Day, wood, 200 m | 5,461 | 60 | 283,616 | 46,641 |
  | D-Day, town, 50 m | 74 | 13 | 4,916 | 137 |
  | D-Day, town, 200 m | 1,447 | 13 | −17,580 | 135 |
  | Blitz, wood, 50 m | 668 | 15 | 103,708 | 5,752 |
  | Blitz, wood, 200 m | 6,606 | 65 | 304,660 | 34,085 |
  | Blitz, town, 50 m | 249 | 8 | 140,896 | 17,961 |
  | Blitz, town, 200 m | 4,557 | 63 | 391,692 | 31,262 |
  | Ardennes, wood, 50 m | 332 | 11 | 37,196 | 33,230 |
  | Ardennes, wood, 200 m | 2,804 | 29 | 43,700 | 30,758 |
  | Ardennes, town, 50 m | 161 | 6 | 67,720 | 4,516 |
  | Ardennes, town, 200 m | 3,542 | 69 | 320,724 | 13,149 |

  (a) is copy on write: each placement that loses objects gets a copy of its block without them, from the top block
  down (the reference that placed it points to the copy; references to blocks under it that don't change still
  point to the shared ones); (b) sinks each whole shared placement that holds an erased object, losing everything
  else in it. (a) removes exactly what the circle covers for 5-400 KB a stroke (a placement left with nothing loses
  its reference instead, so a stroke can shrink the file), so it is the one built. Taking an item out of a block:
  its entries leave the lists, every tree node's split moves back by the entries taken out before it (the boxes and
  LOD masks stay: a box holding less is still right), the items close up and the block is padded again. A copy goes
  right before the block it copies (references still point forward); a block nothing places any more is left out.
  The grids and road marks stay as they are (roads are never erased). The check on D-Day, 100 m circles: the wood
  (2,125 erased, 37 copies, +135,620 bytes) and the town (723 erased, 13 copies, 1,476 bytes smaller) read back,
  nothing erasable is left inside, and every other object is drawn where it was through the same top-block leaves.
  The limit: a reference holds a block's offset in 24 bits, so the blocks' data stops at 16 MB (D-Day uses 10.3 MB:
  about 6 MB of copies, some 20 large strokes in woods); past it the build refuses.

## 7. Textures (`.tgv`, `.tgv_pc`)

| Offset | Meaning |
|---|---|
| 0x00 | u32 version = 1 |
| 0x04 | u32 flag: 1 = each mip payload starts with a codec tag (`TGU1`, `ZIPO`; all 3,831 textures), 0 = the payloads are the blocks as they are (all 2,822 texture stand-ins in `.ppk` packs). The game picks how it reads a payload by this flag: raw blocks under flag 1 crash it (T23, 2026-10-03) |
| 0x08 | u32 width, u32 height, u32 width, u32 height |
| 0x18 | u16 mipCount |
| 0x1A | u16 formatNameLength (4, or 12 for `A8R8G8B8`…) |
| 0x1C | char[] format |
| after format | u32 offset[mipCount], u32 size[mipCount] (smallest mip first) |

- Formats: A8R8(G8B8) 1,315 · DXT5 1,195 · DXT1 1,192 · L8 124 · A8L8 5.
- Mip payloads start with `ZIPO` + u32 uncompressed size (+ zlib, as in Wargame) or with `TGU1` + u32 ❔ (second variant, to decode).
- ✅ The offset table starts at `align4(28 + name length)`: all mip offsets, then all mip sizes; payloads and the
  file are 4-aligned. With several mips, mip 0 is the smallest. ZIPO = `"ZIPO", u32 unpacked size, zlib` ending in a
  sync flush with no final block (some recorded a byte short of `00 00 ff ff`; inflate doesn't mind); DXT data inside
  is the raw row-major block array. Python zlib level 9 + sync flush reproduces some shipped streams byte-exactly.
- ✅ A model atlas can say a bigger size in its header than its largest mip holds (a 2048-pixel France buildings
  atlas stores 512 × 512 blocks); each mip's own size is in its TGU1 header (in 4 × 4 blocks). TGU1 in model atlases
  is the terrain's DXT1 codec (§6). Its block count can be smaller than width × height: only that many blocks (rows
  from the top) carry selectors, and the rest are zero (an empty bottom of the atlas).
- ✅ **TGU1 with alpha (DXT5)** is read (`rusemod.tgu1`, 2026-10-03): every unit texture is DXT5 TGU1 version 5.
  Header bit 0x001 = DXT5, 0x100 = coded; the header is 32 bytes. A mip that isn't coded (flags 0x001: the
  units' mips up to 16 × 16 blocks) is the header and then its DXT5 blocks as they are. A coded one adds, after the
  colour banks, two alpha endpoint images (DCT tiles like the Y images; the second is how far alpha 1 lies below
  alpha 0; an equal pair becomes (a, a − 1), or (1, 0)) and an alpha selector bank (4 × the selector quality;
  value + 4, clamped to 0..7, is the position from alpha 0 to alpha 1: DXT5 indices 0, 2, 3, 4, 5, 6, 7, 1).
  Checked on every texture in `ZZ_Win.dat` (3,831 textures, 9,469 TGU1 payloads): every one decodes, every coded
  one using up every bit stream exactly. Each mip, halved, matches the next smaller one, alpha as closely as colour
  (unit textures: within 10 of 255 on average); the two far-off cases are explained: a gravel-noise decal (28,
  noise halves badly) and an atlas whose empty bottom is see-through black in its plain mips and zero blocks in
  its coded ones (alpha 131; unused space).
- **Unit textures** (2026-10-03): a vehicle has `TSCCombCS_CombinedDSCTexture01` (1024 × 1024, material role
  `CombinedDSCTexture`, tagged `Camp`) and a track `TSCCombDSTrack_CombinedDSTexture01` (128 × 128, tagged
  `IndexedChenilles`); a nation's infantry share one `TSCOther_diffuseTexture01` (2048 × 2048, plain
  `diffuseTexture`, no tag). The infantry picture is the real colours (faces, uniforms). The vehicle picture's colour
  is the paint and shading (the T-26: green camouflage and its turret number; the Sherman: a pale pattern), and its
  alpha holds markings (the Sherman's star is black there) and black patches. The shader settings tie the `Camp`
  tag to `CampColor` material packs (a side colour, with a distance fade). **Seen in the game (T23, 2026-10-03):**
  the colour is the paint at every distance (a Sherman turned red stayed red, up close and as the zoomed-out
  piece); alpha 0 everywhere made a Stuart the player's colour up close (still to confirm with the owner) but not
  from far; alpha 255 everywhere made a Wolverine white at some angles to the sun (shine). So low alpha = side
  colour, high = shine; the values in between aren't tested. A written texture loads like the game's own: stored
  as plain TGU1 mips (flag 0x001) under TGV flag 1.

## 8. Meshes, animations, UI 🟡

### Mesh packs (`.spk`): ✅ read (`src/rusemod/spk.py`)

From the notes of **DomesticNukes and his Claude** (2026-09-29), checked with our own reader on every pack
(`tools/verify_spk.py`): 61 mesh packs and 21 skeleton-only ones in `ZZ_Win.dat` `gen_5\pack\`; **9,650 of 9,650
draw calls decode** (6,793 stored as is, 2,857 compressed), every index below its vertex count, every material
number below the material count, every position inside its model's box.

| Offset | Content |
|---|---|
| 0x00 | `MESH` `PCPC`, u32 version 4, u32 file size, 16-byte hash |
| 0x34 | 8 × (u32 offset, size, count): names, vertex formats, materials, two empty, meshes, draw calls, index-buffer table |
| 0x94 | index-buffer data (offset, size) |
| 0x9C | vertex-buffer table (offset, size, count) |
| 0xA8 | vertex-buffer data (offset, size) |

- **Names**: u32 10, 6 bytes, then the same trie as an EDAT archive (§1): header length 0 is a model, followed by its
  box (6 f32), u32 flags, u16 mesh number, u16 skeleton record (0xCDCD in mesh packs), then its name's last piece.
  Full names are lowercase: `ww2\res3d\decors\vegetation_eu\022lod0.ase2ndfbin`, the `ModelASE` of a scenery
  descriptor without `DataDir:\`. Some models have a lighter `_lodmedium` version beside them.
- **Vertex formats**: u32 256, then 256-byte names that spell the layout, e.g.
  `TVertex__Position_3f__NormalIn01_4ubn__TexCoord0_2wn__TexPackedAtlas0_4ubn` (positions f32; normal bytes
  b / 255 × 2 − 1; UVs `_2wn` 2 signed 16-bit fractions (/ 32767: u 0..1, v −1..0, which wraps to v + 1) or
  2 f32; the atlas bytes below). **Corrected 2026-10-03:** `_2wn` had been read unsigned (u16 / 65535), so every
  model used only a quarter of its picture (u 0..0.5, v 0.5..1) and the Studio's map view drew buildings with the
  wrong part of their atlas. Proved by rendering: read signed, the T-26's turret number and a village house's
  window panes land where they belong. 99.7% of unit vertices and 91-99% of scenery vertices have their v word
  above the midpoint (negative), u below it.
- **Materials**: an NDF with one `TMeshMaterial` per material; `Textures` maps a role to (image, 0). The image is
  `diffuseTexture`, or `CombinedDSCTexture` / `CombinedDSTexture` on most buildings: `ZZ:\GenTexGroup\...\X01.png`
  is the texture `gen\...\x01.tgv` in `ZZ_Win.dat`, an atlas.
- **Mesh** u16 first draw call, u16 count; **draw call** u16, u16 material, u16 index buffer, u16 vertex buffer, u16
  0xFFFF, u16 0xCDCD; **buffer tables** 16 bytes: u32 offset, size, count, u16 (1 / vertex format), u16 flags
  (0xC000 compressed).
- **Compressed index buffer**: u32 size, then zlib (sync flush): u16 differences, summed.
- **Compressed vertex buffer**: a `VBUF` chunk like the terrain's (§6): a predictor (the same parent codes), then
  one `SUBP` stream per component (storage 0 raw, 1 zlib, 3 LZ; mode 2 = relative to the parent), sizes rounded up
  to 4. Positions: u16 Q, 3 f32 min, 3 f32 max, u16, then 3 × u16; t = q / Q, x = min + t × (max − min) up to
  t = 0.5, else max − (1 − t) × (max − min). UVs `_2f` the same with 2 values, `_2wn` a u16 mask (2,047 in all
  2,377 shipped streams) then 2 × u16: 11-bit values, the top bits of the signed 16-bit words above
  (`spk.wn_uv`); normals and atlas bytes 4 × u8.
- **LZ** (§6) with two more cases: a stored block (bit 7 of the width byte: the units follow the first 8 bytes) and
  literals packed 5 or 11 bits wide.
- **Atlas bytes**: a vertex's (min u, min v, width, height) × 255 of its part of the atlas; the drawn UV is
  min + uv × size.
- **Scenery descriptors**: a tree is a `TSceneryDescriptorComposite` of two models, its leaves and its trunk
  (`DescriptorComposition`), so `rusemod.scenery` gives every descriptor all its models.
- The game reads each buffer by its own flag (compressed or plain), whatever the model is for: unit models are all
  stored compressed, scenery mostly plain, so a unit model can be written plain (2026-10-03; not tried in game).
- **Soldiers** (2026-10-03): one skinned body piece (head, hat, uniform and gear; ~20 bones) and a separate gun
  piece held by skeleton bone 21 (and the root, bone 0). The German, Soviet and British soldiers checked all use
  bone 21 for the gun (the British bazooka man also 23); skeletons use 3ds Max Biped bone names (`bip01 r hand`).
  Whether bone 21 is the same named bone in every skeleton isn't read yet (the skeleton packs' bone lists).
- **Out to Blender** (2026-10-03, `ruse export-model`, `rusemod.gltf`): a model as glTF 2.0 (.glb) with its
  colour texture; the alpha (side colour and shine, not see-through) as a picture beside it. Model axes (x, y, z)
  are written as glTF (x, z, y) × 0.01, a mirror (triangles turned round): checked on the T-26, whose turret
  number reads right. Skinned models keep each vertex's bones and weights (through the material's
  `SkinningRemapping`), on joints at the origin (the skeleton packs' bone positions aren't read yet). Checked in
  Blender 4.5 LTS on a T-26, a Sherman and a German soldier (48, 46 and 35 bones, textures right).
- **Skeletons** (2026-10-04, `rusemod.unitmodel.read_skeleton`): an entry starts u32 1, the bone count, then the
  offsets of its bind matrices (3 x 4 f32 per bone, model to bone), the parents (i32, -1 for none), a second table,
  and the names; the names' lengths (u16) from byte 0x24. A bone turns round -R^T t of its matrix: the Sherman's 14
  road wheels land within 2 units of their own points' middle, its turret (`tourelle_01`) at (-70, 5, 326).
- **Triangles wind outward:** (b - a) x (c - a) points the way of the stored normals (all 5,287 of the Sherman's).
- **New models** (2026-10-04, `rusemod.modelin`, `rusemod.unitmodel`): written plain, in the skinned format with float
  texture coordinates (`..._BlW_4ubn__BlIdx_4ub__TexCoord0_2f__TexPackedAtlas0_4ubn`, 55 of the game's buffers), one
  bone per vertex at weight 255, atlas bytes (0, 0, 255, 255) as on every unit; the stored v is the picture's v - 1, as
  the game's own. Not seen in the game yet (TESTS T35).
- Not read yet: mirrored vertices (no shipped pack uses them).

### Skirmish unit packs: ✅ written (`src/rusemod/unitpacks.py`; check `tools/verify_unitpacks.py`)

A skirmish loads four packs of `ZZ_Win.dat` per nation in the match (§3), plus the `common` ones every skirmish loads
(`<tag>`: `us ger uk fr ita urss japan common`):

| Pack | Holds |
|---|---|
| `gen_5\pack\gfxdescriptor\meshskirmish_<tag>.spk` (the US also `meshskirmishwitboat_us.spk`) | the meshes |
| `gen_5\pack\gfxdescriptor\skeleton_<tag>.spk` | their skeletons, under the same names (a pack with no meshes or buffers) |
| `gentexproxy\pack\gfxdescriptor\proxyskirmish_<tag>.ppk` (the US: two again) | small stand-ins of their textures (`PRXYPCPC`) |
| `genanim_15\pack\gfxdescriptor_<tag>.apk` | their animations (`.baf`), an EDAT archive |

- The game's own packs already carry another nation's models where its units need them (Germany's hold the US Long
  Tom's mesh, skeleton and stand-in), so `rusemod.unitpacks` copies a unit's models the same way: what the target
  packs (or the common ones) lack, from the pack of the nation that has it. The full textures are loose files of
  `ZZ_Win.dat`, the same for every nation.
- **Each mesh and stand-in pack's id** (16 bytes at 0x10) is the MD5 of its bytes 0x00-0x0F (magic, version, file
  size) and 0x20-0x2F (the places of the two parts the game reads), in all 156 such packs of `ZZ_Win.dat`. The game
  checks it when it opens a pack and leaves out a pack whose id doesn't match, every model in it missing: four packs
  that grew with their old id crashed the game at the first factory (TESTS T32 run 1). Written with the right id,
  packs that grow load: a second Sherman with a model of its own, added beside the game's (T33).
- **A stand-in's key** (the 8 bytes before its offset in the table) is the 64-bit CRC of its name as stored
  (`gentexproxy\...\x01.tgv`): polynomial 0x42F0E1EBA9EA3693, highest bit first, starting and ending with every bit
  flipped. True of all 2,822 stand-ins in the game's 74 stand-in packs (2026-10-04); `rusemod.unitmodel.standin_key`.
- **A model's picture is found through its texture group:** the start of the picture's own file name up to the first
  `_` (`TSCCombCS_CombinedDSCTexture01.png` is in `TSCCombCS`, the group of every unit body picture; tracks
  `TSCCombDSTrack`, props `TSCForceDXT1`...). A picture whose name starts with a group the game doesn't have crashes it
  when the model is first drawn (TESTS T35 run 2), so `rusemod.unitmodel` names a new picture after its copied body
  texture's group.
- **A texture's levels must fit the room the game makes:** for level k (0 = full size) of a w x h DXT texture the game
  makes room for (w * h / 16) >> 2k blocks, rounded down, and writes as many blocks as the level says it holds. So the
  levels stop when the shorter side is 4 (1024 x 512: 8 levels, the last 8 x 4); one more level gets no room and its
  block lands past the end, corrupting the game's memory (TESTS T35 run 3). All 289 of the game's unit textures fit.
- The layout of each pack (offsets, the name trie, the section order and padding, the stand-ins' table) is in the
  module's docstring. Every `.spk`, `.ppk` and `.apk` in `ZZ_Win.dat` writes back byte for byte, and every unit's
  models copied into every other nation's packs and the common ones read back as in the pack they came from, the
  packs' own models unchanged (2026-10-01).
- `.apk` (nested EDAT), `.baf` (`0f000000`), `.ppk` (`PRXY` or nested EDAT), `.gpk` (UI, likely Scaleform GFx).
- Scenery sets are European/African only: africa, allemagne, ardennes, europe, france, givre, hollande, italie. There is no tropical set.

## 9. Sound (`.ess`) and video 🟡

- Big-endian header: `01 00 02 02`, u8 flag, u8 channels (1/2/6), u16 rate (11,025–48,000), u32 samples, u32 0,
  u32 samples, then a u32 table of block offsets.
- About 1,024 samples per block, variable block sizes, about 4.4 bits/sample: a custom variable-bitrate codec.
- All 17,462 files are compressed; there is no PCM variant. vgmstream doesn't support it. The codec is known in the
  community: RugnirViking's moddingSuite (GPL) reads it and writes mono, and a community stereo encoder made the
  "Custom Music" mod (the menu music replaced by a 48 kHz stereo song). We have no encoder of our own yet.
- **Names to files (2026-10-04):** the data names a source file and the game loads its built copy:
  `FileName = WW2\Sons\ATP_Music\Battle1.ogg` is `gen_sound\ww2\sons\atp_music\battle1.ess` in ZZ_Win.dat (same
  for `.wav` names). Each `.ess` also has a `.sformat` (same path, other extension) that the game reads first: no
  `.sformat`, no sound. They live in sound banks (edat archives): `gen_sound\pack\gfxdescriptor.mpk` (5,566 entries,
  loaded at start for everything under `WW2\Sons`) and per map `gen_sound\pack\map\<map>dialogues.mpk` (mission
  voices) and `<map>ambient.mpk`, loaded with the map.
- **`.sformat` layout** (little-endian): `06 01`, u8 how it's held (1 for music, 0 for short sounds), u8 channels,
  u8 0, u8 bytes per frame (channels × 2), u16 rate, u32 samples, u32 (4 for music, 44 for short sounds; meaning
  unknown), u32 the `.ess` file's size in bytes, u32 loop start, u32 loop end (0 and the sample count in every file
  seen). Music (`.ogg` names) ends there: 28 bytes. Short sounds (`.wav` names) go on with a loudness track: u32
  count, u16 2048 (samples per step), u8 10, u8 5 (bytes per step), then 5 rising bytes per 2048 samples (what the
  game does with it is not known). The `.ess` decodes from its own header, but the read size and the play length come
  from the `.sformat`. The Custom Music mod replaced `ruse_menu_ref-1.ess` (8,418,462 samples, 6.5 MB) with an
  11,923,456-sample, 13.8 MB song and left the `.sformat` as it was, and it works in the game (owner, 2026-10-04);
  whether all 4:08 play or it stops at the old 2:55 isn't recorded yet.
- **Who uses which sound** (game data, `ruse index where <path>`): music = `TSoundStream` objects `$/Misc/Musics/*`
  (musics.cpp in ZZ_GladNotPatchableWin.dat); in-battle music = `$/GFX/Everything/musicInGame` (playlists
  progression 1-5, battle 1-4, mystery 1-5 and 8, driven by gauges and events); missions call `PlayMusic` /
  `StopMusic` / `InitSoundAndMusic(MusicAuto=…)`. Engines = each unit's `SoundMotorDescriptor` (`Run_Snd`,
  `IdleAndStop_Snd`, planes also `Dive_Snd`), shared by kind. Shots = `$/VFX_Bank/SFX_Tir__*`. Voices =
  `$/GFX/Everything/AcknowManager` by nation and `TypeForAcknow` (sets fr, ger, it, jpn, pol, ru, spa, us). Map
  ambience = `$/MapConstante/MapInstance/Map_SoundConfig` (`AmbianceDecor_MultiPiste`), one per map. Buildings have
  no sound field; construction is `$/VFX_Bank/SFX_Construction__Batiment_Base`; scenery animals play idle loops.
  Mission dialogue voices: `gen_sound\test\map\<mission>\scripting\dialog\<lang>\*.ess`.
- **Video:** every shipped video (96, Data_Common.dat) is WebM written by FFmpeg 7 (muxer `Lavf61.3`/`Lavf61.7`):
  one VP9 track (profile 0), Vorbis audio at 48 kHz stereo, cues, simple blocks, no lacing. Four shapes: full-screen
  chapter films `ruse_cs_*` 1280×544 at 25 fps with **8 audio tracks** (one per language); in-mission films 1280×200
  strips (38) or about 416×720 panels (27) at 30 fps with one audio track; menu loops 1280×720 without sound. The
  game's player takes exactly one video track, VP9 only, at most 30 frames a second, and Vorbis audio only; with one
  audio track it plays that track in every language, with several it plays the one for the game's language.
  Cutscenes are `TActionDescriptorLaunchVideo` objects `$/CutSceneVideos/<name>` (per map,
  `map\<map>\cutscenevideos.cpp`, with subtitles) played by a mission's `LaunchVideoFXByName(CutScene=…,
  FullScreen=…)`. Blender 4.5's video output (FFmpeg 7.1, `Lavf61.7.102`) writes the same layout: VP9 profile 0 +
  Vorbis 48 kHz stereo, cues, simple blocks (checked 2026-10-04 with a test render; not tried in the game).
- **Building effects:** buildings share one effects table, `$/GFX/Everything/DefaultFxRemapper` (through the shared
  `Descriptor_Building_Aeroport:GfxDescriptor.LevelBuildGeoDatabaseModification.Descriptor`): construction (with its
  sound, `SFX_Construction__Batiment_Base`, looping until stopped), damage at 0/33/66 %, destruction (light, medium,
  heavy), production smoke at 33/66/100 %, the light that turns while producing, capture. Fake buildings use
  `FakeFxRemapper`.

## 10. The game's program

Out of scope here. The public platform works only through the game's data files and never changes, loads into or
publishes details of RUSE.exe. That's the owner's rule (PLAN.md decision 3), not Eugen's: Eugen has never said the
program can't be edited. Program work happens in the private repo.

## Open questions (ordered by impact)

1. ~~TOPO semantics~~ **Answered enough to add objects (2026-09-28):** see the TOPO row in §2. Final proof: the M2
   cloned-unit test in-game.
2. ~~Is the Maps\PC header checksum enforced, and how is it computed?~~ **Answered (2026-09-28): it isn't a checksum**,
   it's a random GUID per pack (see §6), so it can't be checked against the contents. The M1.5 in-game terrain test
   confirms that an edited pack loads.
3. Can NDF mount an extra data pack at startup (not just map packs)? Without it, every mod with new text (every new
   unit name) rebuilds the 2.3 GB ZZ_Win.dat, since all `.dic` files live there ([PLAN.md](PLAN.md) L5).
   **C3 step 1 survey (2026-09-28, `tools/c3_survey.py`, read-only):**
   - The only pack-mounting class is `TClusterMountMapDataPack` (43 objects, one per map's `clustermap.cpp`), run by
     `$/ClusterTerrain/MapInstance/Load`, i.e. **when a map loads**, not at startup. Fields: `DataPack`
     (`'MapDat:\DataMap<Name>_v09.dat'`), `MapDirectory` (`'DataDir:\Test\Map<Name>'`), `DatasMapDirectory`,
     `AdditionalPackDescriptorSection` (`'PC'`), `MountingPoint` (`'Datasmap'`).
   - Resource packs (meshes, textures, proxies, animations, sounds, scripts, video) are declared by `TResourceDescriptor*Pack`
     objects with a path **inside the already-mounted files**, e.g. `PackName = 'Pack\GFXDescriptor\Skeleton_Common.spk'`,
     loaded through `TClusterInitialisationWithSubClusters_LoadResourcePack` (668 objects).
   - No startup-time object that mounts an arbitrary `.dat` was found. One lead: `TClusterInitialisationDataPath` in
     `clusterbootstrapgame.cpp` has `RoamingDataDirectory = 'TestOption/LocalDataPath'` (a test option naming a local
     data folder; purpose unknown).
   - **C3 step 2 passed (in-game, 2026-09-28):** with Two Islands' pack present only under a new name
     (`DataMapTwoIslandz_v09.dat`) and `clustermap.cpp` pointing at it, the map loaded and played normally. **A map pack
     is found by the name in the data; its file name isn't checked.** New maps can ship their own pack.
   - Game-wide text still needs the ZZ_Win.dat rebuild (our streaming writer makes that practical) unless the
     `LocalDataPath` lead pans out.
4. ~~Does RUSE.exe run from a hard-linked instance with `steam_appid.txt`?~~ **Answered: yes (C2, 2026-09-28).**
5. `TGU1` texture payload encoding. **Known externally:** custom JPEG-like codec shared by `.tgv` (flags 257) and
   terrain `.tmst` (flags 256); decoded in RUSE-Mod-Manager's `terrain_codec.py` (GPLv3; format knowledge
   reportedly CC0 by ProLution, unconfirmed). See [RESEARCH.md](RESEARCH.md).
6. `.scenario` and AI-layer structure. **Known externally:** RUSE-Mod-Manager `scenario.py`, `sdb.py`; capture zones in `kdt.py`.
7. SPK mesh section table. Partial reference: kilivan4iK/warno-blender-plugin (WARNO/RD/SD2 layouts, no license).
8. Terrain streaming (`.tms`, `.tmst_chunk_pc`) and `save.boobspc` body. **Known externally:** RUSE-Mod-Manager
   `terrain_codec.py`, `terrain_mesh.py`, `terrain_relief.py`, `terrain_tiles.py`.
9. `DICS`/`DICV` dictionaries.
10. `.ess` codec.
