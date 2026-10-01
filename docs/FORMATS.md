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
| Map registration (`mapinfo.cpp`, `clustermap.cpp`) | ZZ_GladPatchable | 86 maps | ✅ R | P1 |
| Map support files (`save.boobspc`, `output.sdb`) | Maps\PC | per map | 🟡 checksums known | P1 |
| Scenario (`.scenario`) | DataMap_Win | 102 | ✅ R (zones and design items; `rusemod.scenario`, all 102) | P1 |
| AI map grids (`mapinfo.win`) | DataMap_Win | 34 | 🟡 buffer 0: the road network, read and written byte-identical on all 33 (`rusemod.roadnet`, `tools/verify_roadnet.py`: points on the road curves, links with cost = distance / 10, per-point link lists, a k-d tree over the links); buffers 1-2: the infantry and vehicle navigation graphs, read and written byte-identical (`rusemod.nav`, `tools/verify_nav.py`; every shipped one is one connected piece, and a crossing's last two u16 are road network links; their local maps understood, and new ones written for new bridges: "Movement graphs" in §6); buffer 4: the cover grid, written (`rusemod.cover`, from LittleGroove's `sdb.py`) | P1 |
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
    `datasmap\<map>\mapinfo.win` (DataMap_Win.dat; 2048² cells; bit 4 = blocked, bit 8 = forest, per the mods).
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
- The enum: **0 US, 1 GER, 2 UK, 3 FR, 4 ITA, 5 USSR, 6 JAP.**
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
  statement and the `base_class` line, the same opcodes the file already uses). New strings are written plain
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
- **Skirt:** a curtain from the map edge down to −3000 (own z scale, −3000..zmax); a second submesh ❔. Not edited.

Proven: all 64 files (1,390 cells) rebuild byte-identical; every cell re-encoded with our own LZ re-reads identical
(0.957× size, not byte-identical to Eugen's encoder); a mesa edit on Two Islands re-reads with exactly the new heights.
Open: in-game acceptance; `.kdt` copy; water list not rebuilt after edits; edge vertices skipped; raising above the
file's top height needs re-quantizing (edits are clamped).

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

#### Road stickers, and the close-up map (2026-09-30; code `rusemod.scenery.RoadPiece`)

The roads a player sees are drawn two ways. From afar: painted into the ground's tile pyramid (`highdef`/`lowdef`
`.tmst`). Up close: by the scenery's **road pieces**, `Route` items, whose descriptor `TypeWarrior/Route` is a
**STICKERS** type (category `STICKERS/Tunisie/AnciennesRoutes`, no model): decals laid along the curves (seen in the
game: a road painted only into the pyramid vanished near the camera). D-Day has 431 pieces, all `Route` (name flag 2),
in 40 blocks (many inside village blocks placed several times); a piece is 4 to 290 m long (about 16 m typical),
straight, its two handles a tenth of it along it; its three trailing words are its block's count of road pieces
(10,505 of 10,505 on the shipped maps), then two words the same on every piece of the map (D-Day 129840992 and
1567752; Blitz 129958752 and 1567752). The item word is `0x01000001 | symbol << 4`, no transform (the 15 words
follow). The game draws them up close only through draw-tree nodes with the road mark (§6, the draw tree), and never
lists one for far view (0 of 10,505).

`output\div_map.tgv_pc` (D-Day: 3072 x 2048 DXT5_LIN in one ZIPO mip, about 5 m a pixel; Blitz and Bulge 2048 x 2048)
is a colour and alpha picture of the whole map. The map's own roads are only a faint lift in it (alpha +7 to +20 over
the ground beside them, a little less green), so it isn't what shows a road up close.

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
| crossings | 28 bytes each: the road through a circle (f32 in x, y, out x, y, length; u16 the two links it goes between; u16 two road network links of buffer 0) |
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
  (checked on Blitz's ground picture) and draw the road up close (a road painted only into the tiles vanished near
  the camera, 2026-09-30); otherwise a child block (offset = bits 2–23, always after its parent). Transform by
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
  bit 31 the right, bit 28 the whole node. Bits 20-24 are the LOD mask (8 = far), **bit 25 the road mark**: road
  pieces are drawn up close only through nodes that carry it, from the block's root down (every shipped piece is).
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
- **Header table at field 12** ("layer boundaries", 4-8 u32s): not block starts on most maps; left as they are when
  a block is inserted, and the game ran fine.

## 7. Textures (`.tgv`, `.tgv_pc`)

| Offset | Meaning |
|---|---|
| 0x00 | u32 version = 1 |
| 0x04 | u32 1 |
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
  is the terrain's DXT1 codec (§6), except that its block count is smaller than width × height (meaning not known;
  decoding doesn't need it). TGU1 with alpha (DXT5, some leaf atlases) isn't read yet.

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
  b / 255 × 2 − 1; UVs u16 / 65535 or 2 f32; the atlas bytes below).
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
  t = 0.5, else max − (1 − t) × (max − min). UVs `_2f` the same with 2 values, `_2wn` a u16 mask then 2 × u16
  (uv = value / mask); normals and atlas bytes 4 × u8.
- **LZ** (§6) with two more cases: a stored block (bit 7 of the width byte: the units follow the first 8 bytes) and
  literals packed 5 or 11 bits wide.
- **Atlas bytes**: a vertex's (min u, min v, width, height) × 255 of its part of the atlas; the drawn UV is
  min + uv × size.
- **Scenery descriptors**: a tree is a `TSceneryDescriptorComposite` of two models, its leaves and its trunk
  (`DescriptorComposition`), so `rusemod.scenery` gives every descriptor all its models.
- Not read yet: skeleton packs, mirrored vertices (no shipped pack uses them), writing models (PLAN M7).
- `.apk` (nested EDAT), `.baf` (`0f000000`), `.ppk` (`PRXY` or nested EDAT), `.gpk` (UI, likely Scaleform GFx).
- Scenery sets are European/African only: africa, allemagne, ardennes, europe, france, givre, hollande, italie. There is no tropical set.

## 9. Sound (`.ess`) 🟡, last priority

- Big-endian header: `01 00 02 02`, u8 flag, u8 channels (1/2/6), u16 rate (11,025–48,000), u32 samples, u32 0,
  u32 samples, then a u32 table of block offsets.
- About 1,024 samples per block, variable block sizes, about 4.4 bits/sample: a custom variable-bitrate codec.
- All 17,462 files are compressed; there is no PCM variant. vgmstream doesn't support it.

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
