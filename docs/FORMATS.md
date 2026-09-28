# R.U.S.E. File Formats: Knowledge Base

Everything we know about the game's files, with evidence. Keep it updated: this file is the project's memory.
Game build examined: Steam re-release, data revision **190852**, RUSE.exe built 2026-08-11.

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
| Scenario (`.scenario`) | DataMap_Win | 102 | ❔ (RUSE-Mod-Manager edits it) | P1 |
| AI map grids (`mapinfo.win`) | DataMap_Win | 34 | ❔ (RUSE-Mod-Manager edits layers) | P1 |
| Terrain (`.tms`, `.tmst_pc`, `.tmst_chunk_pc`) | Maps\PC | per map | ❔ | P2 |
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

RUSE.exe hard-codes the six core pack names, `Data\PC`, `Maps/PC`, `MapDat` and
`####DATAREVISION####00190852####DATAREVISION####`. It does not scan for extra `.dat` files.

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

**Naval units exist:** `Descriptor_Unit_Battleship`, `_Destroyer` and `_LCVP` (ships named USS Texas, Nevada, Arkansas and
others: the Normandy mission). Whether players can control them in skirmish is untested.

## 3. Nations

- `Nationalite` is an int32 on unit, infantry, aircraft, building, truck and acknowledgement descriptors.
  Stored values are 1–6; 0 is the default and is not written.
- The enum: **0 US, 1 GER, 2 UK, 3 FR, 4 ITA, 5 USSR, 6 JAP.** RUSE.exe has the same table hard-coded
  (`.data`, VA 0x1417F8E10: EU, Allemagne, RU, France, Italie, URSS, Japon).
- Several structures have exactly 7 slots: `SubClusterNationaliteList` (every map), flag-icon lists, per-nation
  mesh packs, and the bit field `BitFieldNationaliteIfNotSkirmish` (values 0x3F, 0x403F…; bit 14 unexplained).
- **Conclusion (medium confidence, no disassembly):** rosters are data-only; an 8th nation needs exe changes.

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
- The Python 2.5 interpreter, Scaleform GFx and libcurl are statically linked into RUSE.exe.

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
RUSE.exe contains no map names. **Adding a map looks data-only.**

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
| `save.boobspc` | ✅ bytes 0–15 = MD5 of bytes 16..end; then version string `0.6`; uncompressed. RUSE.exe checks it ("Le Checksum du Boobs est invalide") |
| `output.sdb` | ✅ `SDB\r\n` + MD5 of the whole file with the 16-byte hash (at 5–20) removed |
| `.scenario` | `SCENARIO\r\n` + 16 bytes (not an MD5 of the rest) + records (`AREA`, zones, …) ❔ |
| `mapinfo.win` | `INFOIA\r\n` + 16 bytes (not an MD5 of the rest) + AI grids (concealment and movement-blocking layers) ❔ |
| `.tms` | `TMSG`, u32 3, `PC\0\0`, … ❔ (terrain streaming index?) |
| `.tmst_chunk_pc` | u32 id, u32 1, u32 1, u32 0x200, then high-entropy data (7.9 bits/byte), not raw deflate ❔; RUSE-Mod-Manager's team decodes these chunks for reference images |
| `.kdt` | starts `EUG0` ❔ |
| `.fpkpc` | `SFXS` ❔ |
| `.sourcefileid` | begins "Size" ❔ |

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

## 8. Meshes, animations, UI ❔

- `.spk` = `MESH` `PCPC` u32 4, u32 fileSize, 16-byte hash, then a section table. 82 packs (vehicles, scenery sets per theatre, base buildings).
- `.apk` (nested EDAT), `.baf` (`0f000000`), `.ppk` (`PRXY` or nested EDAT), `.gpk` (UI, likely Scaleform GFx).
- Scenery sets are European/African only: africa, allemagne, ardennes, europe, france, givre, hollande, italie. There is no tropical set.

## 9. Sound (`.ess`) 🟡, last priority

- Big-endian header: `01 00 02 02`, u8 flag, u8 channels (1/2/6), u16 rate (11,025–48,000), u32 samples, u32 0,
  u32 samples, then a u32 table of block offsets.
- About 1,024 samples per block, variable block sizes, about 4.4 bits/sample: a custom variable-bitrate codec.
- All 17,462 files are compressed; there is no PCM variant. RUSE.exe contains no known codec library strings; vgmstream doesn't support it.

## 10. RUSE.exe

- PE32+ x64, MSVC 14.x, `EugGame.Final.x64.pdb`, built 2026-08-11, Authenticode-signed.
- Protection:
  - No `.bind` (no SteamStub) and no packer.
  - No ASLR (fixed base 0x140000000) and no CFG.
  - One ordinary TLS callback.
- Imports 34 DLLs. Proxy candidates: **version.dll (4 functions)**, winmm.dll (1); also dbghelp, XINPUT9_1_0, X3DAudio1_6, d3dx9_42, d3d9, d3d11, dxgi, steam_api64 (11).
- Multiplayer strings: `connect_lobby`, `LobbyInvite`, `GameLobbyJoinRequested_t`, `TDesynchroChecker`, `LogDesynchro`, `Desynchronized: %d`.
- Integrity strings: `Le Checksum du Boobs est invalide`, `StateDB MD5 Mismatch`.
- Command line is parsed with `GetCommandLineW` / `CommandLineToArgvW`.

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
