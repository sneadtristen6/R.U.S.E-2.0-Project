"""A new building's look of its own (rusemod.buildinglook) on made-up files: its look (a symbol of the base-building
scenery file) copied with one piece swapped, its model standing where that piece stands, the piece's scenery type
copied with our models, the mod's files/buildings, and the build pointing the new building at its own look."""
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_scenery import block, compact, moved
from test_sceneryasset import NO_NUMPY, TMP, _np, ref, scenery_pack, standins, write_gltf, zz_win

from rusemod import buildinglook as bl
from rusemod import sceneryasset as sa
from rusemod.edat import Edat
from rusemod.rndf import parse
from rusemod.scenery import Scenery
from rusemod.spk import Spk

HALL = "ww2\\res3d\\decors\\us_buildings\\us_buildings_10\\prototype_buildinglod0.ase2ndfbin"
HALL_PIC = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Decors\\US_Buildings\\TSCForceDXT1_diffuseTexture01.png"
NAMES = ["TypeWarrior/Prototype_building", "TypeWarrior/US_silo", "FX_Batiment_Base_Construction",
         "Herbe04_base"]


def base_building(blocks: list, names: list, symbols: dict) -> bytes:
    """A base-building scenery file as the game's are laid out: its blocks, type names, then its symbols' block offsets
    and names (`symbols`: {name: block index}), one grid."""
    offsets, pos = [], 0
    for b in blocks:
        offsets.append(pos)
        pos += len(b)
    data = b"".join(blocks)

    def named(values):
        return b"".join(struct.pack("<I", len(n)) + n.encode() for n in values)
    name_blob, flags = named(names + [""]), bytes([1] * len(names))
    opt = struct.pack(f"<{len(symbols)}I", *(offsets[i] for i in symbols.values()))
    names2 = named(list(symbols) + [""])
    grid = bytes(8)
    tab_off = 124
    data_off = tab_off + 4 * (len(blocks) + 1)
    names_off = data_off + len(data)
    flags_off = names_off + len(name_blob)
    opt_off = flags_off + len(flags)
    names2_off = opt_off + len(opt)
    layers_off = names2_off + len(names2)
    grid_off = layers_off
    fields = [tab_off, len(blocks) + 1, data_off, len(data), flags_off, len(flags), names_off, len(name_blob),
              opt_off, len(opt), names2_off, len(names2), layers_off, 0, 1, 1, 1, 1, 1, 1, grid_off, len(grid),
              0, 0, 0, 0]
    body = (b"0.6\0" + struct.pack("<26I", *fields) + struct.pack(f"<{len(blocks) + 1}I", *offsets, len(data)) + data
            + name_blob + flags + opt + names2 + grid)
    import hashlib
    return hashlib.md5(body).digest() + body


def factory() -> bytes:
    """Two looks: US_Factory (block 0: its hall, a marker, and block 1 twice; block 1: a silo and a sticker) and
    US_Depot (block 2: a silo)."""
    yard = block([compact(1, 0.0, 0.0), moved(0x80000000 | 3 << 4, 500.0, 0.0)])
    head = block([compact(0, 0.0, 0.0), moved(0x80000000 | 2 << 4, 2000.0, 0.0), moved(0, 0, 0), moved(0, 0, 0)])
    root = block([compact(0, 0.0, 0.0), moved(0x80000000 | 2 << 4, 2000.0, 0.0), moved(len(head), 0.0, 3000.0),
                  moved(len(head), 0.0, -3000.0)])
    depot = block([compact(1, 0.0, 0.0)])
    return base_building([root, yard, depot], NAMES, {"US_Factory": 0, "US_Depot": 2})


class TheLookFile(unittest.TestCase):
    def test_a_look_copied_with_its_piece_swapped(self):
        raw = factory()
        self.assertEqual(sorted(bl.symbols(raw)), ["US_Depot", "US_Factory"])
        self.assertEqual(bl.symbol_pieces(raw, "US_Factory"),
                         {"TypeWarrior/Prototype_building": 1, "FX_Batiment_Base_Construction": 1,
                          "TypeWarrior/US_silo": 2, "Herbe04_base": 2})
        swap = {"TypeWarrior/US_silo": "TypeWarrior/R2_LookMine"}
        new = bl.clone_symbol(raw, "US_Factory", "R2_Mine", swap)
        Scenery(new)   # (its MD5 and every table read)
        self.assertIn("2 of them now TypeWarrior/R2_LookMine", bl.check_clone(raw, new, "US_Factory", "R2_Mine", swap))
        self.assertEqual(bl.symbol_pieces(new, "R2_Mine"),
                         {"TypeWarrior/Prototype_building": 1, "FX_Batiment_Base_Construction": 1,
                          "TypeWarrior/R2_LookMine": 2, "Herbe04_base": 2})
        for old in ("US_Factory", "US_Depot"):   # (the game's own looks as they were)
            self.assertEqual(bl.symbol_pieces(new, old), bl.symbol_pieces(raw, old))
        # a second building's look after the first, from the same one
        again = bl.clone_symbol(new, "US_Factory", "R2_Other", {"Prototype_building": "TypeWarrior/R2_LookOther"})
        self.assertEqual(sorted(bl.symbols(again)), ["R2_Mine", "R2_Other", "US_Depot", "US_Factory"])
        self.assertEqual(bl.symbol_pieces(again, "R2_Other")["TypeWarrior/R2_LookOther"], 1)   # (named either way)
        self.assertEqual(bl.symbol_pieces(again, "R2_Mine"), bl.symbol_pieces(new, "R2_Mine"))

    def test_refused(self):
        raw = factory()
        for args, why in ((("US_Nothing", "R2_A", {}), "no symbol US_Nothing"),
                          (("US_Factory", "US_Depot", {}), "already has a symbol US_Depot"),
                          (("US_Depot", "R2_A", {"TypeWarrior/Prototype_building": "TypeWarrior/R2_X"}),
                           "has no TypeWarrior/Prototype_building")):
            with self.subTest(args=args), self.assertRaisesRegex(bl.BuildingLookError, why):
                bl.clone_symbol(raw, *args)
        self.assertEqual(bl.symbol_file_of(lambda m: raw if m == bl.SYMBOL_FILES[1] else None, "US_Depot"),
                         (bl.SYMBOL_FILES[1], raw))
        self.assertIsNone(bl.symbol_file_of(lambda m: raw, "R2_Nowhere"))

    def test_names(self):
        self.assertEqual(bl.symbol_name("Descriptor_Building_R2_Foundry"), "R2_Building_R2_Foundry")
        self.assertEqual(bl.look_name("Descriptor_Building_R2_Foundry"), "LookBuildingR2Foundry")
        self.assertEqual(sa.type_name(bl.look_name("Descriptor_Building_R2_Foundry")),
                         "TypeWarrior/R2_LookBuildingR2Foundry")


def piece_asset(path, size=1.0) -> sa.Asset:
    return sa.Asset("LookTest", sa.BUILDING, path, size,
                    piece=sa.Kind("TypeWarrior/Prototype_building", (HALL,), "building piece"))


@unittest.skipIf(_np is None, NO_NUMPY)
class ThePieceModel(unittest.TestCase):
    def test_standing_where_the_piece_stands(self):
        """The piece's model (a 20 x 20 square, 5 high, round 0, 0) in the US pack: ours (a triangle 1 m wide, 2 m
        deep) beside it, its longer side as long as the piece's times size, the middle of its footprint on the
        piece's, its foot on the floor; every version so too."""
        files = {"gen_5\\pack\\basebuilding\\us.spk": scenery_pack(HALL, HALL_PIC),
                 "gen_5\\pack\\basebuilding\\ger.spk": scenery_pack("ww2\\x\\autrelod0.ase2ndfbin", HALL_PIC),
                 "gentexproxy\\pack\\basebuilding\\us.ppk": standins(HALL_PIC)}
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            path = write_gltf(Path(d), [("brick", False)])
            w = sa.write_asset(zz_win(files), piece_asset(path, 0.5))
        self.assertEqual(sorted(w.changed), ["gen_5\\pack\\basebuilding\\us.spk",
                                             "gentexproxy\\pack\\basebuilding\\us.ppk"])
        back = Spk(w.changed["gen_5\\pack\\basebuilding\\us.spk"])
        for ring in ("", "medium", "far"):
            name = sa.model_name(HALL, "LookTest", ring=ring)
            pts = [p for g in back.model(name) for p in zip(*[iter(g.positions)] * 3)]
            xs, ys, zs = zip(*pts)
            self.assertAlmostEqual(max(max(xs) - min(xs), max(ys) - min(ys)), 20 * 0.5, places=3)
            self.assertAlmostEqual((max(ys) + min(ys)) / 2, 0.0, places=3)
            self.assertAlmostEqual((max(xs) + min(xs)) / 2, 0.0, places=3)
            self.assertAlmostEqual(min(zs), 0.0, places=3)
        self.assertEqual(w.report["models"], {"main": sa.model_name(HALL, "LookTest")})
        self.assertIn("r2looktestlod0", w.report["models"]["main"])

    def test_its_type(self):
        text = sa.rndf(sa.BUILDING, "LookTest", {ring: sa.model_names(sa.BUILDING, "LookTest", ring, like=HALL)
                                                 for ring in ("", "medium", "far")}, ["a.ndf"],
                       piece=sa.Kind("TypeWarrior/Prototype_building", (HALL,), "building piece"))
        parse(text, file="looks.rndf", mod="test")
        self.assertIn("R2Asset_LookTest_0 is clone @[RegistrationName='TypeWarrior/Prototype_building', file='a.ndf']",
                      text)
        self.assertIn("patch ~/R2Asset_LookTest_0:SDTrue ( RegistrationName = 'TypeWarrior/R2_LookTest_Dest' )", text)
        for e, ring in enumerate(("close", "medium", "far")):
            self.assertIn(f"patch ~/R2Asset_LookTest_0:SDFalse.ModeEntry[{e}] ( SceneryDescriptor = "
                          f"~/R2Asset_LookTest_0_{ring} )", text)
        self.assertIn("us_buildings_10\\r2looktestfarlod0.ASE2NdfBin", text)


def piece_game(shared_entry: bool = False):
    """A made-up game: the hall's scenery type laid out as the game's building pieces (close, middle, far, and its
    destroyed state); `shared_entry`: its middle entry another type's too."""
    from decimal import Decimal
    from rusemod.patch import Game, Inline, ListV, Num, Obj, Ref, Text

    def model(name):
        return Inline(Obj("TSceneryDescriptorModel3DFromFile", {"ModelASE": Text("path", f"DataDir:\\{name}")}))

    def entry(mask, name):
        return Obj("TSceneryDescriptorMultiModeEntry", {"ModeMask": Num("uint32", Decimal(mask)),
                                                        "SceneryDescriptor": model(name)})

    def modes(names):
        return Inline(Obj("TSceneryDescriptorMultiMode", {"ModeEntry": ListV(
            [Ref("set.cpp#9") if shared_entry and k == 1 else Inline(entry(m, n))
             for k, (m, n) in enumerate(zip((2, 4, 8), names))])}))
    dest = Obj("TSceneryDescriptorMultiState", {"RegistrationName": Text("string", "TypeWarrior/Prototype_building_Dest"),
                                                "SDFalse": modes(["dest", "dest_m", "dest_f"])})
    hall = Obj("TSceneryDescriptorMultiState", {
        "RegistrationName": Text("string", "TypeWarrior/Prototype_building"),
        "SDFalse": modes(["WW2\\Res3D\\Decors\\US_Buildings\\US_Buildings_10\\Prototype_buildinglod0.ASE2NdfBin",
                          "hall_m", "hall_f"]),
        "SDTrue": Inline(dest)}, origin=("usbuildingsset.cpp", 1))
    return Game(objects={"$/Hall": hall, "set.cpp#9": entry(4, "shared")}), Inline


class TheType(unittest.TestCase):
    def test_run_on_a_piece_laid_out_as_the_games(self):
        """The piece's type copied: its three entries ours, its destroyed state renamed; the game's piece as it was."""
        from rusemod.patch import Engine
        from rusemod.resolve import ModInfo
        from rusemod.visibility import descriptors_named, entries
        game, Inline = piece_game()
        kind = bl.piece_kind(game, "TypeWarrior/Prototype_building")
        self.assertEqual(kind.like, HALL)
        asset = sa.Asset("LookTest", sa.BUILDING, None, piece=kind)
        run = Engine(game).run([(ModInfo("r2-assets"), parse(sa.rules(game, [asset]), file="files/assets",
                                                             mod="r2-assets"))])
        self.assertEqual([f.message for f in run.findings if f.level == "error"], [])
        found = descriptors_named(run.game, {"TypeWarrior/R2_LookTest", "TypeWarrior/Prototype_building",
                                             "TypeWarrior/R2_LookTest_Dest"})

        def models(name):
            (_n, _f, o), = found[name]
            return [(m, e.props["SceneryDescriptor"].obj.props["ModelASE"].value.rsplit("\\", 1)[-1]
                     if isinstance(e.props["SceneryDescriptor"], Inline)
                     else run.game.objects[e.props["SceneryDescriptor"].target].props["ModelASE"].value.rsplit("\\", 1)[-1])
                    for m, e, _own in entries(o, run.game.objects)]
        self.assertEqual(models("TypeWarrior/R2_LookTest"), [(2, "r2looktestlod0.ASE2NdfBin"),
                                                              (4, "r2looktestmediumlod0.ASE2NdfBin"),
                                                              (8, "r2looktestfarlod0.ASE2NdfBin")])
        self.assertEqual(models("TypeWarrior/Prototype_building"), [(2, "Prototype_buildinglod0.ASE2NdfBin"),
                                                                    (4, "hall_m"), (8, "hall_f")])
        (_n, _f, mine), = found["TypeWarrior/R2_LookTest"]
        self.assertEqual(mine.props["SDTrue"].obj.props["RegistrationName"].value, "TypeWarrior/R2_LookTest_Dest")
        (_n, _f, theirs), = found["TypeWarrior/Prototype_building"]
        self.assertEqual(theirs.props["SDTrue"].obj.props["RegistrationName"].value,
                         "TypeWarrior/Prototype_building_Dest")

    def test_a_piece_laid_out_otherwise_refused(self):
        game, _Inline = piece_game(shared_entry=True)
        asset = sa.Asset("LookTest", sa.BUILDING, None, piece=bl.piece_kind(game, "TypeWarrior/Prototype_building"))
        with self.assertRaisesRegex(sa.AssetError, "isn't laid out as building pieces are"):
            sa.rules(game, [asset])
        with self.assertRaisesRegex(bl.BuildingLookError, "no scenery type TypeWarrior/Nothing"):
            bl.piece_kind(game, "TypeWarrior/Nothing")


class ModFiles(unittest.TestCase):
    def test_written_and_read_back(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            folder = Path(d) / "files" / "buildings" / "Descriptor_Building_R2_Foundry"
            folder.mkdir(parents=True)
            (folder / "hall.glb").write_bytes(b"x")
            (folder / "building.toml").write_text(bl.look_toml("TypeWarrior/Prototype_building", "hall.glb", 0.8,
                                                               credit={"author": "me"}), encoding="utf-8")
            look, = bl.mod_looks(d).values()
            self.assertEqual((look.unit, look.piece, look.asset.kind, look.asset.size, look.asset.name,
                              look.asset.credit), ("Descriptor_Building_R2_Foundry", "TypeWarrior/Prototype_building",
                                                   "building", 0.8, "LookBuildingR2Foundry", {"author": "me"}))
            self.assertIn('piece = "Prototype_building"', (folder / "building.toml").read_text(encoding="utf-8"))
            for text, why in (('model = "hall.glb"\n', "piece must name"),
                              ('piece = "X"\nmodel = "none.glb"\n', "model must name"),
                              ('piece = "X"\nmodel = "hall.glb"\nsize = 500\n', "size is a number")):
                (folder / "building.toml").write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaisesRegex(bl.BuildingLookError, why):
                    bl.mod_looks(d)

    @unittest.skipIf(_np is None, NO_NUMPY)
    def test_imported(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            src = write_gltf(Path(d), [("brick", False)])
            look = bl.import_look(src, Path(d) / "mod", "Descriptor_Building_R2_Foundry", "Prototype_building", 1.2,
                                  credit={"licence": "CC0"})
            folder = Path(d) / "mod" / "files" / "buildings" / "Descriptor_Building_R2_Foundry"
            self.assertEqual(sorted(p.name for p in folder.iterdir()),
                             ["Descriptor_Building_R2_Foundry.glb", "Descriptor_Building_R2_Foundry_far.glb",
                              "Descriptor_Building_R2_Foundry_medium.glb", "building.toml"])
            self.assertEqual((look.piece, look.asset.size, sorted(look.asset.versions)),
                             ("TypeWarrior/Prototype_building", 1.2, ["far", "medium"]))
            with self.assertRaisesRegex(sa.AssetError, "CC0 or CC-BY"):
                bl.import_look(src, Path(d) / "mod", "Descriptor_Building_R2_Foundry", "Prototype_building",
                               credit={"licence": "CC-BY-NC"})


@unittest.skipIf(_np is None, NO_NUMPY)
class StudioCalls(unittest.TestCase):
    """The Units tab's building Look (StudioApi.building_look, building_look_import, building_look_change,
    building_look_remove): the look's pieces, a new building's model in place of one, changed and removed."""

    def setUp(self):
        from unittest import mock
        from ruse_studio.api import StudioApi
        tmp = tempfile.TemporaryDirectory(dir=TMP)
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.mod = self.root / "mod"
        self.folder = self.mod / "files" / "buildings" / "Descriptor_Building_R2_Foundry"
        self.api = StudioApi(home=self.root / "home", game_dir=self.root / "game")
        self.new = True
        for name, value in (("_building_symbol", lambda a: "US_Factory"),
                            ("_piece_table", lambda: {"US_Factory": [["TypeWarrior/Prototype_building", 1, 33.4, 29.2,
                                                                      12.8], ["TypeWarrior/US_silo", 2, 5.0, 5.0, 9.0]]}),
                            ("_card_view", lambda a: None),
                            ("_own_look_folder", lambda a: self.folder if self.new else None)):
            patch = mock.patch.object(StudioApi, name, side_effect=value)
            patch.start()
            self.addCleanup(patch.stop)
        gone = mock.patch("rusemod.recycle.to_recycle_bin", side_effect=lambda p: __import__("shutil").rmtree(p))
        gone.start()
        self.addCleanup(gone.stop)
        self.gltf = write_gltf(self.root, [("brick", False)])

    def test_imported_changed_and_removed(self):
        from ruse_studio.api import StudioError
        got = self.api.building_look("$/X")
        self.assertEqual((got["building"], got["new_unit"], got["own"]), (True, True, None))
        self.assertEqual([(p["name"], p["count"], p["size"]) for p in got["pieces"]],
                         [("Prototype_building", 1, [33.4, 29.2, 12.8]), ("US_silo", 2, [5.0, 5.0, 9.0])])
        with self.assertRaisesRegex(StudioError, "isn't one of the pieces"):
            self.api.building_look_import("$/X", "TypeWarrior/Nothing", str(self.gltf))
        got = self.api.building_look_import("$/X", "TypeWarrior/Prototype_building", str(self.gltf), 1.5,
                                            licence="CC0", author="me")
        own = got["own"]
        self.assertTrue(got["done"])
        self.assertEqual((own["piece"], own["size"], own["triangles"], own["credit"]),
                         ("TypeWarrior/Prototype_building", 1.5, 1, {"author": "me", "licence": "CC0"}))
        self.assertEqual(sorted(own["versions"]), ["far", "medium"])
        self.assertEqual(self.api.building_look_change("$/X", size=0.8)["own"]["size"], 0.8)
        with self.assertRaisesRegex(StudioError, "CC0 or CC-BY"):
            self.api.building_look_change("$/X", licence="CC-BY-NC")
        self.assertIsNone(self.api.building_look_remove("$/X")["own"])
        self.assertFalse(self.folder.exists())

    def test_only_a_new_building(self):
        from ruse_studio.api import StudioError
        self.new = False
        self.assertFalse(self.api.building_look("$/X")["new_unit"])
        with self.assertRaisesRegex(StudioError, "copy the building first"):
            self.api.building_look_import("$/X", "TypeWarrior/Prototype_building", str(self.gltf))


@unittest.skipIf(_np is None, NO_NUMPY)
class ThroughTheBuild(unittest.TestCase):
    def test_a_new_building_gets_its_own_look(self):
        """A mod's copy of a building with files/buildings/<its name>: the copy's two look names point at its own
        look, the game's building keeps its own; the piece's type copied with our model; a look for a building no
        mod makes refused."""
        from rusemod.build import build_pack, load_mod
        from rusemod.model import load
        S = lambda i: val(0x07, struct.pack("<I", i))   # noqa: E731  (a string of the table)
        data = make_ndf(
            # (class, props) an object; ref(object, its class)
            objects=[(0, [(0, ref(1, 1))]),                                           # 0 the factory: its look part
                     (1, [(1, ref(2, 2)), (2, ref(3, 3))]),
                     (2, [(3, S(0))]),                                                # 2 SymbolName
                     (3, [(4, ref(4, 4))]),                                           # 3 ModificationAction
                     (4, [(3, S(0))]),                                                # 4 SymbolName
                     (5, [(5, S(1)), (6, ref(6, 6)), (7, ref(10, 5))]),               # 5 the hall's type
                     (6, [(8, val(0x11, struct.pack("<I", 3) + ref(7, 7) + ref(8, 7) + ref(9, 7)))]),
                     (7, [(9, val(0x03, struct.pack("<I", 2))), (10, ref(11, 8))]),   # 7-9 close, middle, far
                     (7, [(9, val(0x03, struct.pack("<I", 4))), (10, ref(12, 8))]),
                     (7, [(9, val(0x03, struct.pack("<I", 8))), (10, ref(13, 8))]),
                     (5, [(5, S(2)), (6, ref(14, 6))]),                               # 10 its destroyed state
                     (8, [(11, val(0x1C, struct.pack("<I", 3)))]),
                     (8, [(11, val(0x1C, struct.pack("<I", 3)))]),
                     (8, [(11, val(0x1C, struct.pack("<I", 3)))]),
                     (6, [(8, val(0x11, struct.pack("<I", 0)))])],
            classes=["TBatimentDescriptor", "TGfxDescriptorModifyLevelBuild", "TGfxLevelBuildGeoDatabaseModification",
                     "TGfxLevelBuildStateGeoDatabaseModification",
                     "TGfxLevelBuildStateGeoDatabaseModificationActionStateModifier", "TSceneryDescriptorMultiState",
                     "TSceneryDescriptorMultiMode", "TSceneryDescriptorMultiModeEntry",
                     "TSceneryDescriptorModel3DFromFile"],
            props=[("GfxDescriptor", 0), ("LevelBuildGeoDatabaseModification", 1),
                   ("LevelBuildStateGeoDatabaseModification", 1), ("SymbolName", 2), ("ModificationAction", 3),
                   ("RegistrationName", 5), ("SDFalse", 5), ("SDTrue", 5), ("ModeEntry", 6), ("ModeMask", 7),
                   ("SceneryDescriptor", 7), ("ModelASE", 8)],
            strings=["US_Factory", "TypeWarrior/Prototype_building", "TypeWarrior/Prototype_building_Dest",
                     "DataDir:\\" + HALL[:-len(".ase2ndfbin")] + ".ASE2NdfBin"],
            exports={0: "Descriptor_Building_Factory", 5: "Hall"}, compress=True)
        arc = Edat(make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", data)])]))
        files = {"gen_5\\pack\\basebuilding\\us.spk": scenery_pack(HALL, HALL_PIC),
                 "gentexproxy\\pack\\basebuilding\\us.ppk": standins(HALL_PIC)}
        new = "Descriptor_Building_R2_Foundry"
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            mod = Path(d, "m")
            (mod / "src").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "m"\nname = "M"\nversion = "0.1.0"\n', encoding="utf-8")
            (mod / "src" / "foundry.rndf").write_text(
                f"{new} is clone $/Descriptor_Building_Factory ( )\n", encoding="utf-8")
            bl.import_look(write_gltf(Path(d), [("brick", False)]), mod, new, "Prototype_building")
            result = build_pack(arc, [load_mod(mod)], text_arc=zz_win(files))
            (mod / "files" / "buildings" / new).rename(mod / "files" / "buildings" / "Descriptor_Building_R2_Nobody")
            nobody = build_pack(arc, [load_mod(mod)], text_arc=zz_win(files))
        self.assertEqual(result.errors, [])
        self.assertEqual(result.look_symbols, {new: ("US_Factory", "R2_Building_R2_Foundry")})
        built, _files = load(result.changed)

        def symbols_of(name):
            gfx = built.objects[name].props["GfxDescriptor"].obj
            return (gfx.props["LevelBuildGeoDatabaseModification"].obj.props["SymbolName"].value,
                    gfx.props["LevelBuildStateGeoDatabaseModification"].obj.props["ModificationAction"].obj
                    .props["SymbolName"].value)
        mine = next(n for n in built.objects if n.endswith(new))
        theirs = next(n for n in built.objects if n.endswith("Descriptor_Building_Factory"))
        self.assertEqual(symbols_of(mine), ("R2_Building_R2_Foundry",) * 2)
        self.assertEqual(symbols_of(theirs), ("US_Factory",) * 2)
        regs = {o.props["RegistrationName"].value for o in built.objects.values() if "RegistrationName" in o.props}
        self.assertLessEqual({"TypeWarrior/R2_LookBuildingR2Foundry", "TypeWarrior/Prototype_building"}, regs)
        self.assertIn("no mod in the set makes a new building Descriptor_Building_R2_Nobody",
                      " ".join(f.message for f in nobody.errors))
