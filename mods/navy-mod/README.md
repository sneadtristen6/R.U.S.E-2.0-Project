# Navy Mod

Adds a Destroyer, Heavy Cruiser and Battleship to every nation in skirmish. Research and build them from the Experimental tab of the prototype base. Each nation gets its own historical ship names and descriptions. The ships drive on land. They are heavily armored, long-range, late-game units. Do not combine with other ship mods.

Rebuilt from the RUSE-Mod-Manager mod `Navy_Mod.rmod` (version 2.3.2, made on game build 24670294) with `tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set (docs/MOD_FORMAT.md §13). Numbers and names are the original's.

**In this mod:** 21 new objects, 26 objects changed, 85 values set, 66 texts.

## Assumptions to check in-game

- copies of @[ClassNameForDebug='Unit_Destroyer'] with the original's values on top, instead of units built from scratch (the original borrowed most parts from that unit): Descriptor_Unit_Destroyer_GER, Descriptor_Unit_Destroyer_UK, Descriptor_Unit_Destroyer_FR, Descriptor_Unit_Destroyer_ITA, Descriptor_Unit_Destroyer_URSS, Descriptor_Unit_Destroyer_JAP
- copies of @[ClassNameForDebug='Unit_Heavy_Cruiser'] with the original's values on top, instead of units built from scratch (the original borrowed most parts from that unit): Descriptor_Unit_Heavy_Cruiser_GER, Descriptor_Unit_Heavy_Cruiser_UK, Descriptor_Unit_Heavy_Cruiser_FR, Descriptor_Unit_Heavy_Cruiser_ITA, Descriptor_Unit_Heavy_Cruiser_URSS, Descriptor_Unit_Heavy_Cruiser_JAP
- copies of @[ClassNameForDebug='Unit_Battleship'] with the original's values on top, instead of units built from scratch (the original borrowed most parts from that unit): Descriptor_Unit_Battleship_GER, Descriptor_Unit_Battleship_UK, Descriptor_Unit_Battleship_FR, Descriptor_Unit_Battleship_ITA, Descriptor_Unit_Battleship_URSS, Descriptor_Unit_Battleship_JAP
- objects the original matched by their position in the file are taken to be: #60250 (TGfxDescriptorModeleWithAnimation) = `@[ClassNameForDebug='Unit_Battleship']:GfxDescriptor`, #60273 (TGfxDescriptorModeleWithAnimation) = `@[ClassNameForDebug='Unit_Heavy_Cruiser']:GfxDescriptor`, #60218 (TGfxDescriptorModeleWithAnimation) = `@[ClassNameForDebug='Unit_Destroyer']:GfxDescriptor`

## Not rebuilt

- new objects: FileName: needs a file the original ships (US_Battleship.png): Card_Unit_Battleship, Card_Unit_Battleship_Ger, Card_Unit_Battleship_Uk, Card_Unit_Battleship_Fr, Card_Unit_Battleship_Ita, Card_Unit_Battleship_Urss, Card_Unit_Battleship_Jap
- new objects: FileName: needs a file the original ships (US_Heavy_Cruiser.png): Card_Unit_Heavy_Cruiser, Card_Unit_Heavy_Cruiser_Ger, Card_Unit_Heavy_Cruiser_Uk, Card_Unit_Heavy_Cruiser_Fr, Card_Unit_Heavy_Cruiser_Ita, Card_Unit_Heavy_Cruiser_Urss, Card_Unit_Heavy_Cruiser_Jap
- new objects: FileName: needs a file the original ships (US_Destroyer.png): Card_Unit_Destroyer, Card_Unit_Destroyer_Ger, Card_Unit_Destroyer_Uk, Card_Unit_Destroyer_Fr, Card_Unit_Destroyer_Ita, Card_Unit_Destroyer_Urss, Card_Unit_Destroyer_Jap
- new objects: Operator_Translate_Vertical: a map entry reached by its position (SousElements<v2>); Operator_Rotate_Pente: a map entry reached by its position (SousElements<v2>); Operator_Rotate_Roulis: a map entry reached by its position (SousElements<v2>): Chassis_Unit_Battleship, Chassis_Unit_Heavy_Cruiser, Chassis_Unit_Destroyer
- kept from the copied unit: ArmorDescriptor (the original set a reference by file position (object #45062, TArmorDescriptor)): Descriptor_Unit_Destroyer_GER, Descriptor_Unit_Heavy_Cruiser_GER, Descriptor_Unit_Battleship_GER, Descriptor_Unit_Destroyer_UK, Descriptor_Unit_Heavy_Cruiser_UK, Descriptor_Unit_Battleship_UK, Descriptor_Unit_Destroyer_FR, Descriptor_Unit_Heavy_Cruiser_FR and 10 more
- kept from the copied unit: GfxDescriptor (the original set a reference by file position (object #60218, TGfxDescriptorModeleWithAnimation)): Descriptor_Unit_Destroyer_GER, Descriptor_Unit_Destroyer_UK, Descriptor_Unit_Destroyer_FR, Descriptor_Unit_Destroyer_ITA, Descriptor_Unit_Destroyer_URSS, Descriptor_Unit_Destroyer_JAP
- kept from the copied unit: GfxDescriptorIcone (the original set a reference by file position (object #54103, TGfxDescriptorPileJeton)): Descriptor_Unit_Destroyer_GER, Descriptor_Unit_Heavy_Cruiser_GER, Descriptor_Unit_Battleship_GER
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Destroyer_Ger, which couldn't be rebuilt): Descriptor_Unit_Destroyer_GER
- kept from the copied unit: GfxDescriptor (the original set a reference by file position (object #60273, TGfxDescriptorModeleWithAnimation)): Descriptor_Unit_Heavy_Cruiser_GER, Descriptor_Unit_Heavy_Cruiser_UK, Descriptor_Unit_Heavy_Cruiser_FR, Descriptor_Unit_Heavy_Cruiser_ITA, Descriptor_Unit_Heavy_Cruiser_URSS, Descriptor_Unit_Heavy_Cruiser_JAP
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Heavy_Cruiser_Ger, which couldn't be rebuilt): Descriptor_Unit_Heavy_Cruiser_GER
- kept from the copied unit: GfxDescriptor (the original set a reference by file position (object #60250, TGfxDescriptorModeleWithAnimation)): Descriptor_Unit_Battleship_GER, Descriptor_Unit_Battleship_UK, Descriptor_Unit_Battleship_FR, Descriptor_Unit_Battleship_ITA, Descriptor_Unit_Battleship_URSS, Descriptor_Unit_Battleship_JAP
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Battleship_Ger, which couldn't be rebuilt): Descriptor_Unit_Battleship_GER
- kept from the copied unit: GfxDescriptorIcone (the original set a reference by file position (object #54859, TGfxDescriptorPileJeton)): Descriptor_Unit_Destroyer_UK, Descriptor_Unit_Heavy_Cruiser_UK, Descriptor_Unit_Battleship_UK
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Destroyer_Uk, which couldn't be rebuilt): Descriptor_Unit_Destroyer_UK
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Heavy_Cruiser_Uk, which couldn't be rebuilt): Descriptor_Unit_Heavy_Cruiser_UK
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Battleship_Uk, which couldn't be rebuilt): Descriptor_Unit_Battleship_UK
- kept from the copied unit: GfxDescriptorIcone (the original set a reference by file position (object #54793, TGfxDescriptorPileJeton)): Descriptor_Unit_Destroyer_FR, Descriptor_Unit_Heavy_Cruiser_FR, Descriptor_Unit_Battleship_FR
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Destroyer_Fr, which couldn't be rebuilt): Descriptor_Unit_Destroyer_FR
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Heavy_Cruiser_Fr, which couldn't be rebuilt): Descriptor_Unit_Heavy_Cruiser_FR
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Battleship_Fr, which couldn't be rebuilt): Descriptor_Unit_Battleship_FR
- kept from the copied unit: GfxDescriptorIcone (the original set a reference by file position (object #54992, TGfxDescriptorPileJeton)): Descriptor_Unit_Destroyer_ITA, Descriptor_Unit_Heavy_Cruiser_ITA, Descriptor_Unit_Battleship_ITA
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Destroyer_Ita, which couldn't be rebuilt): Descriptor_Unit_Destroyer_ITA
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Heavy_Cruiser_Ita, which couldn't be rebuilt): Descriptor_Unit_Heavy_Cruiser_ITA
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Battleship_Ita, which couldn't be rebuilt): Descriptor_Unit_Battleship_ITA
- kept from the copied unit: GfxDescriptorIcone (the original set a reference by file position (object #54943, TGfxDescriptorPileJeton)): Descriptor_Unit_Destroyer_URSS, Descriptor_Unit_Heavy_Cruiser_URSS, Descriptor_Unit_Battleship_URSS
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Destroyer_Urss, which couldn't be rebuilt): Descriptor_Unit_Destroyer_URSS
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Heavy_Cruiser_Urss, which couldn't be rebuilt): Descriptor_Unit_Heavy_Cruiser_URSS
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Battleship_Urss, which couldn't be rebuilt): Descriptor_Unit_Battleship_URSS
- kept from the copied unit: GfxDescriptorIcone (the original set a reference by file position (object #61005, TGfxDescriptorPileJeton)): Descriptor_Unit_Destroyer_JAP, Descriptor_Unit_Heavy_Cruiser_JAP, Descriptor_Unit_Battleship_JAP
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Destroyer_Jap, which couldn't be rebuilt): Descriptor_Unit_Destroyer_JAP
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Heavy_Cruiser_Jap, which couldn't be rebuilt): Descriptor_Unit_Heavy_Cruiser_JAP
- kept from the copied unit: TextureForInterface (the original set a reference to Card_Unit_Battleship_Jap, which couldn't be rebuilt): Descriptor_Unit_Battleship_JAP
- TextureForInterface: a reference to Card_Unit_Battleship, which couldn't be rebuilt: @TUniteAuSolDescriptor[ClassNameForDebug='Unit_Battleship']
- SousElements: a map entry reached by its position (SousElements<v0>): shared @[ClassNameForDebug='Unit_Battleship']:GfxDescriptor, shared @[ClassNameForDebug='Unit_Heavy_Cruiser']:GfxDescriptor, shared @[ClassNameForDebug='Unit_Destroyer']:GfxDescriptor
- patch of TGfxDescriptorModeleWithAnimation: none of its values can be written
- TextureForInterface: a reference to Card_Unit_Heavy_Cruiser, which couldn't be rebuilt: @TUniteAuSolDescriptor[ClassNameForDebug='Unit_Heavy_Cruiser']
- TextureForInterface: a reference to Card_Unit_Destroyer, which couldn't be rebuilt: @TUniteAuSolDescriptor[ClassNameForDebug='Unit_Destroyer']
- FigurineBinderEffets: a map entry reached by its position (FigurineBinderEffets<v0>): shared @[ClassNameForDebug='Unit_Battleship']:GfxDescriptor, shared @[ClassNameForDebug='Unit_Heavy_Cruiser']:GfxDescriptor, shared @[ClassNameForDebug='Unit_Destroyer']:GfxDescriptor
- ArmorDescriptor: a reference by file position (object #45062, TArmorDescriptor): @TUniteAuSolDescriptor[ClassNameForDebug='Unit_Destroyer'], @TUniteAuSolDescriptor[ClassNameForDebug='Unit_Heavy_Cruiser'], @TUniteAuSolDescriptor[ClassNameForDebug='Unit_Battleship']
- patch of TAmmunition: TAmmunition object #44931 of everything.cpp.gladndfbin, matched by its position in the file
- patch of TAmmunition: TAmmunition object #44932 of everything.cpp.gladndfbin, matched by its position in the file
- patch of TResourceMultiMaterialMesh: TResourceMultiMaterialMesh object #60236 of everything.cpp.gladndfbin, matched by its position in the file
- patch of TResourceMultiMaterialMesh: TResourceMultiMaterialMesh object #60237 of everything.cpp.gladndfbin, matched by its position in the file
- patch of TResourceMultiMaterialMesh: TResourceMultiMaterialMesh object #60284 of everything.cpp.gladndfbin, matched by its position in the file
- patch of TResourceMultiMaterialMesh: TResourceMultiMaterialMesh object #60261 of everything.cpp.gladndfbin, matched by its position in the file
- patch of TClusterLoadResource: TClusterLoadResource object #50 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TClusterLoadResource: TClusterLoadResource object #55 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TClusterLoadResource: TClusterLoadResource object #60 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TClusterLoadResource: TClusterLoadResource object #65 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TClusterLoadResource: TClusterLoadResource object #77 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TClusterLoadResource: TClusterLoadResource object #82 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TClusterLoadResource: TClusterLoadResource object #102 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TResourceDescriptorMeshPack: TResourceDescriptorMeshPack object #70 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TResourceDescriptorProxyPack: TResourceDescriptorProxyPack object #71 of cluster.cpp.gladndfbin, matched by its position in the file
- patch of TResourceDescriptorMeshPack: TResourceDescriptorMeshPack object #73 of cluster.cpp.gladndfbin, matched by its position in the file
- 22 whole file(s) inside the original (mods of ours hold no game files or compiled scripts): `gen\ww2\res2d\texanimationuniticone\eu\us_destroyer.tgv` (11 KB), `gen\ww2\res2d\texanimationuniticone\eu\us_heavy_cruiser.tgv` (10 KB), `gen\ww2\res2d\texanimationuniticone\eu\us_battleship.tgv` (11 KB), `gen\ww2\res2d\texanimationuniticone\allemagne\us_destroyer.tgv` (11 KB), `gen\ww2\res2d\texanimationuniticone\allemagne\us_heavy_cruiser.tgv` (10 KB), `gen\ww2\res2d\texanimationuniticone\allemagne\us_battleship.tgv` (11 KB), …

Statements that could not be rebuilt stay in the `.rndf` file as comments, with the original's values, so a session with the game can finish them.
