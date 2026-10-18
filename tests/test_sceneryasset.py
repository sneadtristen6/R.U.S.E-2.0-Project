"""The map asset importer (rusemod.sceneryasset) on made-up files: a model made the game's (its units, its mirror, its
draws of at most 65,535 points, a tree's leaves and wood apart), its pictures (a mask as their alpha), written into
every mesh pack holding its kind's game model and read back, its textures and stand-ins added, a mod's asset.toml read,
and its scenery type's rules."""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fixtures import make_edat, make_ndf, val
from rusemod import sceneryasset as sa
from rusemod.dxt import png_bytes
from rusemod.edat import Edat
from rusemod.modelin import Material, Mesh, Model
from rusemod.rndf import parse
from rusemod.spk import Spk
from rusemod.tmst import Tgv
from rusemod.unitpacks import Buffer, MeshPack, Proxy, ProxyPack, proxy_name

TMP = "D:/RUSE-2.0/scratch/tmp"
FMT = "$/M3D/System/VERTEXTYPE/" + sa.FORMAT
ROCK = "ww2\\res3d\\decors\\props\\props_2\\rocher_1lod0.ase2ndfbin"
OAK = "ww2\\res3d\\decors\\vegetation_eu\\chene_01_feuilleslod0.ase2ndfbin"
ROCK_PIC = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Decors\\Props\\TSCForceDXT1_Rocher01.png"
OAK_PIC = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Decors\\Vegetation\\TSCVegetation_Chene01.png"


def ref(index, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))


def materials(picture: str) -> bytes:
    """One TMeshMaterial naming `picture`, as a scenery model's."""
    tex = val(0x12, struct.pack("<I", 1) + val(0x07, struct.pack("<I", 0))
              + val(0x22, val(0x1C, struct.pack("<I", 2)) + val(0x03, bytes(4))))
    objects = [(0, [(0, val(0x11, struct.pack("<I", 1) + ref(1, 1)))]),
               (1, [(1, tex), (2, val(0x07, struct.pack("<I", 1)))])]
    return make_ndf(objects, ["TEugBListPBaseClass", "TMeshMaterial"],
                    [("Value", 0), ("Textures", 1), ("MaterialName", 1)],
                    strings=["DiffuseTexture", "Standard", picture], topo=(0,))


def scenery_pack(model: str, picture: str) -> bytes:
    """A mesh pack holding the game's `model`: one draw of a quad, its picture `picture`."""
    pts = [(-10.0, -10.0, 0.0), (10.0, -10.0, 0.0), (10.0, 10.0, 5.0), (-10.0, 10.0, 5.0)]
    verts = b"".join(struct.pack("<3f4B2f4B", *p, 128, 128, 255, 0, 0.0, 0.0, 0, 0, 255, 255) for p in pts)
    pack = MeshPack(formats=[FMT.encode().ljust(256, b"\0")], materials=materials(picture), material_count=1)
    pack.ibs.append(Buffer(struct.pack("<6H", 0, 1, 2, 0, 2, 3), 12, 6, 1, 0))
    pack.vbs.append(Buffer(verts, len(verts), 4, 0, 0))
    pack.draws.append((0, 0, 0, 0, 0xFFFF, 0xCDCD))
    pack.meshes.append((0, 1))
    pack.items[model] = [struct.pack("<6fI", -10, -10, 0, 10, 10, 5, 3), 0, 0xCDCD]
    return pack.to_bytes()


def standins(*pictures) -> bytes:
    return ProxyPack([Proxy(bytes([k]) * 8, b"OLD", struct.pack("<HHI", 0, 0, 0xAAAAAAAA),
                            proxy_name(p).encode().ljust(256, b"\0")) for k, p in enumerate(pictures)],
                     list(range(len(pictures)))).to_bytes()


def zz_win(files: dict) -> Edat:
    tree: dict = {}
    for path, data in files.items():
        folder, _, name = path.rpartition("\\")
        tree.setdefault(folder + "\\", []).append(("file", name, data))
    return Edat(make_edat([("dir", folder, items) for folder, items in tree.items()]))


def game() -> dict:
    """The rock in two theatre packs (not a third), the oak's leaves in the vegetation pack, their stand-ins."""
    return {"gen_5\\pack\\france.spk": scenery_pack(ROCK, ROCK_PIC),
            "gen_5\\pack\\italie.spk": scenery_pack(ROCK, ROCK_PIC),
            "gen_5\\pack\\other.spk": scenery_pack("ww2\\res3d\\decors\\props\\x\\autrelod0.ase2ndfbin", ROCK_PIC),
            "gen_5\\pack\\europeset_vegetation.spk": scenery_pack(OAK, OAK_PIC),
            "gentexproxy\\pack\\decors.ppk": standins(ROCK_PIC, OAK_PIC)}


def write_gltf(folder: Path, mats: list, *, scale: float = 1.0) -> Path:
    """A .gltf of one triangle a material (`mats`: (name, cutout) each; a cutout one gets its mask beside its picture
    as Poly Haven's come), its colour picture 8 x 4, its triangle 1 m across (glTF y up) and `scale` times that."""
    blob, views, accessors, prims, images, materials_ = b"", [], [], [], [], []
    for k, (name, cutout) in enumerate(mats):
        pos = struct.pack("<9f", *(scale * c for c in (k, 0, 0, k + 1, 0, 0, k, 2, 0)))
        uv = struct.pack("<6f", 0, 0, 1, 0, 0, 1)
        idx = struct.pack("<3H", 0, 1, 2) + b"\0\0"
        for data, comp, count, kind in ((pos, 5126, 3, "VEC3"), (uv, 5126, 3, "VEC2"), (idx, 5123, 3, "SCALAR")):
            views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": 6 if kind == "SCALAR" else len(data)})
            accessors.append({"bufferView": len(views) - 1, "componentType": comp, "count": count, "type": kind})
            blob += data
        prims.append({"attributes": {"POSITION": 3 * k, "TEXCOORD_0": 3 * k + 1}, "indices": 3 * k + 2,
                      "material": k})
        (folder / f"{name}_diff_2k.png").write_bytes(png_bytes(bytes([40 * k, 120, 20] * 32), 8, 4))
        images.append({"uri": f"{name}_diff_2k.png"})
        mat = {"name": name, "pbrMetallicRoughness": {"baseColorTexture": {"index": k}}}
        if cutout:
            mat["alphaMode"] = "MASK"
            (folder / f"{name}_alpha_2k.png").write_bytes(png_bytes(bytes([255, 255, 255, 0, 0, 0] * 16), 8, 4))
        materials_.append(mat)
    (folder / "model.bin").write_bytes(blob)
    doc = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
           "meshes": [{"primitives": prims}], "materials": materials_,
           "textures": [{"source": k} for k in range(len(mats))], "images": images,
           "buffers": [{"uri": "model.bin", "byteLength": len(blob)}], "bufferViews": views, "accessors": accessors}
    path = folder / "model_2k.gltf"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def quad(materials_=(0, 1)) -> Model:
    """Two triangles (z up, metres), each its own material, with UVs and normals up."""
    mesh = Mesh("m", [(0, 0, 0), (1, 0, 0), (1, 2, 0), (0, 2, 3)], [(0, 1, 2), (0, 2, 3)],
                uvs=[(0, 0), (1, 0), (1, 1), (0, 0.25)], face_materials=list(materials_),
                normals=[(0, 0, 1)] * 4)
    return Model([mesh], [Material("bark", colour=(1.0, 0.5, 0.0)), Material("leaf", cutout="MASK")], "quad")


def points(part):
    return [struct.unpack_from("<3f", d.vertices, 28 * i) for d in part.draws for i in range(d.points)]


class TheModel(unittest.TestCase):
    def test_names(self):
        self.assertEqual(sa.asset_name("rock_face_01"), "RockFace01")
        self.assertEqual(sa.asset_name("big  rock-2"), "BigRock2")
        with self.assertRaises(sa.AssetError):
            sa.asset_name("__")
        self.assertEqual(sa.model_name(ROCK, "RockFace01"),
                         "ww2\\res3d\\decors\\props\\props_2\\r2rockface01lod0.ase2ndfbin")
        self.assertEqual(sa.model_name(OAK, "Oak", "leaves"),
                         "ww2\\res3d\\decors\\vegetation_eu\\r2oakleaveslod0.ase2ndfbin")
        self.assertEqual(sa.image_path(ROCK_PIC, "R2Rock01"),
                         "ZZ:\\GenTexGroup\\WW2\\Res3D\\Decors\\Props\\TSCForceDXT1_R2Rock01.png")
        self.assertEqual(sa.type_name("Rock"), "TypeWarrior/R2_Rock")
        self.assertEqual(sa.data_path("ww2\\a\\r2rocklod0.ase2ndfbin"), "DataDir:\\ww2\\a\\r2rocklod0.ASE2NdfBin")

    def test_made_the_games(self):
        """260 units a metre times its size, y turned round and so each triangle's corners, v as the game's, normals
        in bytes, the box of what it draws."""
        made = sa.parts(quad(), 2.0)
        self.assertEqual(list(made), ["main"])
        part = made["main"]
        self.assertEqual(part.counts, (6, 2))   # (a draw a material: their points apart)
        self.assertEqual([d.material for d in part.draws], [0, 1])
        self.assertEqual(points(part)[:3], [(0, 0, 0), (520, 0, 0), (520, -1040, 0)])
        self.assertEqual(struct.unpack("<3H", part.draws[0].indices), (0, 2, 1))
        self.assertEqual(struct.unpack_from("<4B2f4B", part.draws[0].vertices, 12 + 28 * 2),
                         (128, 128, 255, 0, 1.0, -1.0, 0, 0, 255, 255))
        self.assertEqual(part.box, (0.0, -1040.0, 0.0, 520.0, 0.0, 1560.0))

    def test_a_trees_leaves_and_wood(self):
        made = sa.parts(quad(), 1.0, sa.leaf_materials(quad()))
        self.assertEqual(sa.leaf_materials(quad()), {1})
        self.assertEqual({r: p.counts for r, p in made.items()}, {"leaves": (3, 1), "wood": (3, 1)})
        self.assertEqual(made["leaves"].box, (0.0, -520.0, 0.0, 260.0, 0.0, 780.0))
        self.assertEqual(list(sa.parts(quad((0, 0)), 1.0, {1})), ["wood"])   # (no leaves drawn: no leaves model)

    def test_draws_never_past_the_games_indices(self):
        """A draw names at most 65,535 points (16-bit indices): a material's triangles go in as many draws as that
        takes, every triangle once."""
        n = 10
        mesh = Mesh("strip", [(i, j, 0) for i in range(n + 1) for j in (0, 1)],
                    [t for i in range(n) for t in ((2 * i, 2 * i + 2, 2 * i + 1), (2 * i + 1, 2 * i + 2, 2 * i + 3))],
                    face_materials=[0] * (2 * n))
        with mock.patch.object(sa, "CHUNK", 3):
            part = sa.parts(Model([mesh], [Material("a")]))["main"]
        self.assertEqual([d.triangles for d in part.draws], [3] * 6 + [2])
        self.assertEqual(sum(d.triangles for d in part.draws), 2 * n)
        for d in part.draws:
            self.assertLessEqual(max(struct.unpack(f"<{3 * d.triangles}H", d.indices)), d.points - 1)
        self.assertEqual(sa.MOST_POINTS, 0xFFFF)
        self.assertLessEqual(3 * sa.CHUNK, sa.MOST_POINTS)

    def test_nothing_to_draw_refused(self):
        with self.assertRaises(sa.AssetError):
            sa.parts(Model([Mesh("m", [(0, 0, 0)], [])], [Material("a")], "empty"))


class Pictures(unittest.TestCase):
    def test_a_masks_grey_is_its_alpha(self):
        colour = png_bytes(bytes([10, 20, 30] * 16), 4, 4)
        mask = png_bytes(bytes([255] * 3 * 8 + [0] * 3 * 8), 4, 4)
        model = Model([], [Material("leaf", "leaf.png", data=colour, cutout="MASK", mask=mask),
                           Material("bark", "bark.png", data=colour), Material("plain", colour=(1.0, 0.0, 0.5))])
        leaf, bark, plain = sa.pictures(model)
        self.assertEqual((leaf.width, leaf.height, leaf.see_through), (4, 4, True))
        self.assertEqual(list(leaf.rgba[3::4]), [255] * 8 + [0] * 8)
        self.assertEqual(leaf.rgba[:3], bytes([10, 20, 30]))
        self.assertEqual((set(bark.rgba[3::4]), bark.see_through), ({255}, False))
        self.assertEqual((plain.width, plain.rgba[:4]), (4, bytes([255, 0, 128, 255])))

    def test_a_mask_of_another_size_fits(self):
        colour = png_bytes(bytes([10, 20, 30] * 64), 8, 8)
        mask = png_bytes(bytes([255] * 3 * 8 + [0] * 3 * 8), 4, 4)   # (top half white)
        leaf, = sa.pictures(Model([], [Material("leaf", "leaf.png", data=colour, cutout="MASK", mask=mask)]))
        alpha = leaf.rgba[3::4]
        self.assertEqual((leaf.width, leaf.height), (8, 8))
        self.assertEqual(list(alpha[:32]), [255] * 32)
        self.assertEqual(list(alpha[32:]), [0] * 32)

    def test_a_jpg_is_left_to_the_studio(self):
        with self.assertRaisesRegex(sa.AssetError, "Studio turns"):
            sa.pictures(Model([], [Material("a", "a_diff_2k.jpg", data=b"\xff\xd8\xff\xe0 not read here")]))


class Packs(unittest.TestCase):
    def test_written_and_read_back(self):
        made = sa.parts(quad(), 1.0)
        mine = sa.model_name(ROCK, "Rock")
        raw = sa.write_models(scenery_pack(ROCK, ROCK_PIC), {mine: made["main"]}, ROCK,
                              {0: sa.image_path(ROCK_PIC, "R2Rock01"), 1: sa.image_path(ROCK_PIC, "R2Rock02")})
        back = Spk(raw)
        self.assertEqual(set(back.items), {ROCK, mine})
        got = back.model(mine)
        self.assertEqual([len(g.indices) // 3 for g in got], [1, 1])
        self.assertEqual([tuple(round(c, 3) for c in g.positions[:3]) for g in got][0], (0, 0, 0))
        self.assertEqual(len(back.model(ROCK)[0].indices), 6)          # (the game's own as it was)
        pics = [next(iter(back.materials()[g.material]["textures"].values())) for g in got]
        self.assertEqual(pics, [sa.image_path(ROCK_PIC, "R2Rock01"), sa.image_path(ROCK_PIC, "R2Rock02")])
        self.assertEqual(next(iter(back.materials()[back.model(ROCK)[0].material]["textures"].values())), ROCK_PIC)
        with self.assertRaisesRegex(sa.AssetError, "already has"):
            sa.write_models(raw, {mine: made["main"]}, ROCK, {0: sa.image_path(ROCK_PIC, "R2Rock01")})

    def test_a_pack_without_the_format_refused(self):
        pack = MeshPack.read(scenery_pack(ROCK, ROCK_PIC))
        pack.formats = [b"$/M3D/System/VERTEXTYPE/TVertex__Position_3f".ljust(256, b"\0")]
        with self.assertRaisesRegex(sa.AssetError, "format"):
            sa.write_models(pack.to_bytes(), {sa.model_name(ROCK, "R"): sa.parts(quad())["main"]}, ROCK,
                            {0: "x", 1: "y"})

    def test_an_asset_into_every_pack_holding_its_kind(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            path = write_gltf(Path(d), [("stone", False)], scale=2.0)
            w = sa.write_asset(zz_win(game()), sa.Asset("Stone", "rock", path, 1.5))
        mine = sa.model_name(ROCK, "Stone")
        self.assertEqual(sorted(w.changed), ["gen_5\\pack\\france.spk", "gen_5\\pack\\italie.spk",
                                             "gentexproxy\\pack\\decors.ppk"])
        for p in ("gen_5\\pack\\france.spk", "gen_5\\pack\\italie.spk"):
            back = Spk(w.changed[p])
            self.assertEqual([round(max(g.positions[0::3]), 2) for g in back.model(mine)], [260 * 2 * 1.5])
        member = "gen\\ww2\\res3d\\decors\\props\\tscforcedxt1_r2stone01.tgv"
        self.assertEqual(list(w.added), [member])
        tex = Tgv(w.added[member])
        self.assertEqual((tex.width, tex.height), (8, 4))
        proxies = ProxyPack.read(w.changed["gentexproxy\\pack\\decors.ppk"])
        self.assertIn("gentexproxy\\ww2\\res3d\\decors\\props\\tscforcedxt1_r2stone01.tgv", proxies.names())
        self.assertEqual(len(proxies.names()), 3)
        self.assertEqual(w.model, mine)
        self.assertEqual((w.report["triangles"], w.report["pictures"], w.report["see_through"]), ({"main": 1}, 1, 0))
        # its middle and far versions beside it in every pack (made here: a triangle 3 m across keeps its one)
        for ring in ("medium", "far"):
            name = sa.model_name(ROCK, "Stone", ring=ring)
            for p in ("gen_5\\pack\\france.spk", "gen_5\\pack\\italie.spk"):
                self.assertEqual([len(g.indices) // 3 for g in Spk(w.changed[p]).model(name)], [1], (ring, p))
        self.assertEqual(w.report["versions"], {"medium": {"main": 1}, "far": {"main": 1}})
        self.assertEqual(w.report["versions_from"], {"medium": "made", "far": "made"})

    def test_two_sided_every_version(self):
        """two_sided: the full model and each version with every triangle also facing the other way."""
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            w = sa.write_asset(zz_win(game()), sa.Asset("Scan", "rock", write_gltf(Path(d), [("s", False)]),
                                                        two_sided=True))
        self.assertEqual(w.report["triangles"], {"main": 2})
        self.assertEqual(w.report["versions"], {"medium": {"main": 2}, "far": {"main": 2}})

    def test_a_version_of_the_mods_own(self):
        """A version the mod has (asset.toml's medium, far) goes in as it is, sharing the model's pictures."""
        from rusemod import meshlod
        from rusemod.modelin import read_model
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            path = write_gltf(Path(d), [("stone", False)])
            full = read_model(path)
            mesh = full.meshes[0]
            two = Model([Mesh("lite", mesh.positions + [(5.0, 5.0, 0.0)], [(0, 1, 2), (0, 2, 3)],
                              mesh.uvs + [(1.0, 1.0)], [0, 0])], full.materials)
            own = Path(d) / "stone_medium.glb"
            own.write_bytes(meshlod.glb_bytes(two, d))
            w = sa.write_asset(zz_win(game()), sa.Asset("Stone", "rock", path, versions={"medium": own}))
            many = Model([Mesh("m", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)], face_materials=[1])],
                         [Material("a"), Material("b")])
            (Path(d) / "many.glb").write_bytes(meshlod.glb_bytes(many, d))
            with self.assertRaisesRegex(sa.AssetError, "2 materials, the model 1"):
                sa.write_asset(zz_win(game()), sa.Asset("Stone", "rock", path, versions={"far": Path(d) / "many.glb"}))
        self.assertEqual(w.report["versions"], {"medium": {"main": 2}, "far": {"main": 1}})
        self.assertEqual(w.report["versions_from"], {"medium": "stone_medium.glb", "far": "made"})
        back = Spk(w.changed["gen_5\\pack\\france.spk"])
        lite = back.model(sa.model_name(ROCK, "Stone", ring="medium"))
        close = back.model(sa.model_name(ROCK, "Stone"))
        self.assertEqual([len(g.indices) // 3 for g in lite], [2])
        self.assertEqual(lite[0].material, close[0].material)   # (the same picture)

    def test_a_tree_is_leaves_and_wood(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            path = write_gltf(Path(d), [("bark", False), ("leaf", True)])
            w = sa.write_asset(zz_win(game()), sa.Asset("Oak", "tree", path))
            bare = write_gltf(Path(d), [("bark", False)])
            with self.assertRaisesRegex(sa.AssetError, "needs leaves"):
                sa.write_asset(zz_win(game()), sa.Asset("Bare", "tree", bare))
        back = Spk(w.changed["gen_5\\pack\\europeset_vegetation.spk"])
        names = {r: sa.model_name(OAK, "Oak", r) for r in ("leaves", "wood")}
        self.assertEqual(w.report["models"], names)
        for role, name in names.items():
            self.assertEqual([len(g.indices) // 3 for g in back.model(name)], [1], role)
        for ring in ("medium", "far"):   # (its middle and far versions: 3D, as a rock's)
            for role, name in sa.model_names("tree", "Oak", ring).items():
                self.assertEqual([len(g.indices) // 3 for g in back.model(name)], [1], (ring, role))
        self.assertEqual(list(w.report["versions"]), ["medium", "far"])
        leaf = Tgv(w.added["gen\\ww2\\res3d\\decors\\vegetation\\tscvegetation_r2oak02.tgv"])
        self.assertEqual(leaf.format, "DXT5")
        self.assertEqual(w.report["see_through"], 1)

    def test_a_pack_with_the_model_in_another_folder(self):
        """A pack holding the kind's game model in a folder of its own (the African vegetation pack's bushes) gets
        ours too, under the name our type gives it; a pack without the model gets nothing. Our pictures go beside the
        picture of the very model our type copies, whichever pack comes first."""
        bush = sa.KINDS["plant"].like
        africa = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Decors\\Vegetation_Africa\\TSCVegetation_Buisson01.png"
        files = {"gen_5\\pack\\africaset_vegetation.spk": scenery_pack(bush.replace("vegetation_eu", "vegetation_af"),
                                                                       africa),
                 "gen_5\\pack\\europeset_vegetation.spk": scenery_pack(bush, OAK_PIC),
                 "gen_5\\pack\\france.spk": scenery_pack(ROCK, ROCK_PIC),
                 "gentexproxy\\pack\\decors.ppk": standins(ROCK_PIC, OAK_PIC)}
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            w = sa.write_asset(zz_win(files), sa.Asset("Fern", "plant", write_gltf(Path(d), [("f", True)])))
        mine = sa.model_name(bush, "Fern")
        self.assertEqual(sorted(p for p in w.changed if p.endswith(".spk")),
                         ["gen_5\\pack\\africaset_vegetation.spk", "gen_5\\pack\\europeset_vegetation.spk"])
        for p in ("gen_5\\pack\\africaset_vegetation.spk", "gen_5\\pack\\europeset_vegetation.spk"):
            back = Spk(w.changed[p])
            self.assertIn(mine, back.items)
            self.assertEqual(next(iter(back.materials()[back.model(mine)[0].material]["textures"].values())),
                             sa.image_path(OAK_PIC, "R2Fern01"))
        self.assertEqual(list(w.added), ["gen\\ww2\\res3d\\decors\\vegetation\\tscvegetation_r2fern01.tgv"])

    def test_each_build_step_after_the_last(self):
        """`earlier`: what other build steps changed is where ours goes in, not the pack as the game has it."""
        files = game()
        mine = sa.model_name(ROCK, "Before")
        earlier = {"gen_5\\pack\\france.spk": sa.write_models(files["gen_5\\pack\\france.spk"],
                                                              {mine: sa.parts(quad())["main"]}, ROCK, {0: "a", 1: "b"})}
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            w = sa.write_asset(zz_win(files), sa.Asset("Stone", "rock", write_gltf(Path(d), [("s", False)])), earlier)
        self.assertIn(mine, Spk(w.changed["gen_5\\pack\\france.spk"]).items)
        self.assertNotIn(mine, Spk(w.changed["gen_5\\pack\\italie.spk"]).items)

    def test_no_pack_holding_its_kind(self):
        files = {k: v for k, v in game().items() if "europeset" not in k}
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            with self.assertRaisesRegex(sa.AssetError, "no mesh pack"):
                sa.write_asset(zz_win(files), sa.Asset("Oak", "tree", write_gltf(Path(d), [("b", False), ("l", True)])))
            with self.assertRaisesRegex(sa.AssetError, "needs wood"):
                sa.write_asset(zz_win(game()), sa.Asset("Oak", "tree", write_gltf(Path(d), [("l", True)])))


class ModFiles(unittest.TestCase):
    def asset(self, root: Path, name: str, text: str, model: str = "model_2k.gltf") -> None:
        folder = root / "files" / "assets" / name
        folder.mkdir(parents=True)
        if model:
            write_gltf(folder, [("a", False)])
        (folder / "asset.toml").write_text(text, encoding="utf-8")

    def test_read(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            self.assertEqual(sa.mod_assets(d), {})
            self.asset(Path(d), "rock_face_01", 'kind = "rock"\nmodel = "model_2k.gltf"\nsize = 2\n'
                       'source = "polyhaven.com"\nauthor = "someone"\nlicence = "CC0"\ntwo_sided = true\n')
            self.asset(Path(d), "Fern", 'kind = "plant"\nmodel = "model_2k.gltf"\nmedium = "model_2k.gltf"\n')
            got = sa.mod_assets(d)
        self.assertEqual(sorted(got), ["Fern", "RockFace01"])
        rock = got["RockFace01"]
        self.assertEqual((rock.kind, rock.size, rock.model.name), ("rock", 2.0, "model_2k.gltf"))
        self.assertEqual(rock.credit, {"source": "polyhaven.com", "author": "someone", "licence": "CC0"})
        self.assertEqual(rock.versions, {})
        self.assertEqual((rock.two_sided, got["Fern"].two_sided), (True, False))
        self.assertEqual(got["Fern"].size, 1.0)
        self.assertEqual({k: v.name for k, v in got["Fern"].versions.items()}, {"medium": "model_2k.gltf"})

    def test_versions_saved_beside_the_model(self):
        """save_versions: each version as <model>_<ring>.glb beside the model, named in asset.toml, read back by the
        build; a version the modder named is left as it is unless forced."""
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            self.asset(Path(d), "Stone", 'kind = "rock"\nmodel = "model_2k.gltf"\nsize = 2\n')
            folder = Path(d) / "files" / "assets" / "Stone"
            got = sa.save_versions(folder)
            self.assertEqual(got, {"medium": ("model_2k_medium.glb", 1, True), "far": ("model_2k_far.glb", 1, True)})
            text = (folder / "asset.toml").read_text(encoding="utf-8")
            self.assertIn('medium = "model_2k_medium.glb"\nfar = "model_2k_far.glb"\n', text)
            self.assertIn("size = 2\n", text)
            stone = sa.mod_assets(d)["Stone"]
            self.assertEqual({k: v.name for k, v in stone.versions.items()},
                             {"medium": "model_2k_medium.glb", "far": "model_2k_far.glb"})
            (folder / "model_2k_far.glb").write_bytes((folder / "model_2k_medium.glb").read_bytes())
            mine = (folder / "model_2k_far.glb").stat().st_mtime_ns
            self.assertEqual(sa.save_versions(folder)["far"], ("model_2k_far.glb", 1, False))
            self.assertEqual((folder / "model_2k_far.glb").stat().st_mtime_ns, mine)
            self.assertTrue(sa.save_versions(folder, force=True)["far"][2])
            self.assertEqual((folder / "asset.toml").read_text(encoding="utf-8").count("far ="), 1)
            plant = Path(d) / "files" / "assets" / "Fern"
            self.asset(Path(d), "Fern", 'kind = "plant"\nmodel = "model_2k.gltf"\n')
            self.assertEqual(list(sa.save_versions(plant)), ["medium", "far"])

    def test_refused(self):
        for text, why in (('kind = "house"\nmodel = "model_2k.gltf"\n', "kind must be"),
                          ('kind = "rock"\n', "model must"),
                          ('kind = "rock"\nmodel = "nothing.glb"\n', "model must"),
                          ('kind = "rock"\nmodel = "../outside/model_2k.gltf"\n', "model must"),
                          ('kind = "rock"\nmodel = "model_2k.gltf"\nsize = 0\n', "size is"),
                          ('kind = "rock"\nmodel = "model_2k.gltf"\nsize = true\n', "size is"),
                          ('kind = "rock"\nmodel = "model_2k.gltf"\nfar = "none.glb"\n', "far must"),
                          ('kind = "rock"\nmodel = "model_2k.gltf"\ntwo_sided = "yes"\n', "two_sided is true or"),
                          ('kind = "rock"\nmodel = \n', "asset.toml")):
            with tempfile.TemporaryDirectory(dir=TMP) as d:
                outside = Path(d) / "files" / "assets" / "outside"
                outside.mkdir(parents=True)
                write_gltf(outside, [("a", False)])
                (outside / "asset.toml").write_text('kind = "rock"\nmodel = "model_2k.gltf"\n', encoding="utf-8")
                self.asset(Path(d), "x", text)
                with self.assertRaisesRegex(sa.AssetError, why):
                    sa.mod_assets(d)


class TheType(unittest.TestCase):
    def rules(self, kind, off=frozenset()):
        return sa.rndf(kind, "Test", sa.all_model_names(kind, "Test"), ["a.ndf", "b.ndf"], off)

    def test_every_kind_parses(self):
        for kind in sa.KINDS:
            text = self.rules(kind)
            parse(text, file="assets.rndf", mod="test")
            self.assertEqual(text.count("RegistrationName = 'TypeWarrior/R2_Test'"), 2, kind)   # (once a file)
            self.assertIn(sa.KINDS[kind].template, text)

    def test_each_distance_its_own_version(self):
        """A rock's full model close, its middle and far versions in entries of their own (as the game's buildings);
        a plant's and a tree's middle and far versions 3D too, in the entries the game's draw their picture with."""
        rock = self.rules("rock")
        self.assertNotIn("ModeMask = 31", rock)
        for ring, bit in (("medium", 4), ("far", 8)):
            self.assertIn(f"R2Asset_Test_0_{ring} is clone ~/R2Asset_Test_0:SDFalse.ModeEntry[0] ( ModeMask = {bit} )",
                          rock)
            self.assertEqual(rock.count(f"r2test{ring}lod0.ASE2NdfBin"), 2, ring)   # (once a file)
        self.assertIn("patch ~/R2Asset_Test_1 ( SDFalse.ModeEntry += [~/R2Asset_Test_1_medium, ~/R2Asset_Test_1_far] )",
                      rock)
        self.assertEqual(rock.count("r2testlod0.ASE2NdfBin"), 2)
        self.assertNotIn("GraphicOptionDeactivated", rock)
        self.assertEqual(self.rules("rock", {1}).count("delete GraphicOptionDeactivated"), 1)
        plant = self.rules("plant")
        self.assertEqual([plant.count(f"r2test{r}lod0.ASE2NdfBin") for r in ("", "medium", "far")], [2, 2, 2])
        self.assertIn("R2Asset_Test_0_medium is clone ~/R2Asset_Test_0:SDFalse.ModeEntry[0].SceneryDescriptor "
                      "( ModelASE = path('DataDir:\\ww2\\res3d\\decors\\vegetation_eu\\r2testmediumlod0.ASE2NdfBin') )",
                      plant)
        self.assertIn("patch ~/R2Asset_Test_1:SDFalse.ModeEntry[1] ( SceneryDescriptor = ~/R2Asset_Test_1_medium )", plant)
        tree = self.rules("tree")
        for j in (0, 1):
            for e, ring in ((1, "medium"), (2, "far")):
                self.assertIn(f"R2Asset_Test_{j}_{ring} is clone ~/R2Asset_Test_{j}:SDFalse.ModeEntry[0].SceneryDescriptor",
                              tree)
                self.assertIn(f"patch ~/R2Asset_Test_{j}:SDFalse.ModeEntry[{e}] "
                              f"( SceneryDescriptor = ~/R2Asset_Test_{j}_{ring} )", tree)
        for model in ("r2testleaveslod0", "r2testwoodlod0", "r2testleavesmediumlod0", "r2testwoodmediumlod0",
                      "r2testleavesfarlod0", "r2testwoodfarlod0"):
            self.assertEqual(tree.count(model + ".ASE2NdfBin"), 2, model)

    def test_run_on_types_shaped_as_the_games(self):
        """The rules run by the build's engine on a made-up game whose four types are laid out as the game's (the
        rock and the prop one close entry, the rock's switched off by a graphics option, the bush a close model and a
        middle picture made of it, the oak its leaves and trunk close and a middle and far picture it shares with
        other oaks): ours name our models, each distance its own version, ours never switched off; the game's, and
        the oaks' shared picture, as they were."""
        from decimal import Decimal
        from rusemod.patch import Engine, Game, Inline, ListV, Num, Obj, Ref, Text
        from rusemod.resolve import ModInfo
        from rusemod.visibility import descriptors_named

        def model(name):
            return Inline(Obj("TSceneryDescriptorModel3D", {"ModelASE": Text("path", f"DataDir:\\{name}")}))

        def entry(mask, desc, off=False):
            props = {"ModeMask": Num("uint32", Decimal(mask)), "SceneryDescriptor": desc}
            if off:
                props["GraphicOptionDeactivated"] = Num("bool", Decimal(1))
            return Inline(Obj("TSceneryDescriptorMultiModeEntry", props))

        def kind(name, entries, at):
            multi = Obj("TSceneryDescriptorMultiMode", {"ModeEntry": ListV(entries)})
            return Obj("TSceneryDescriptorMultiState", {"RegistrationName": Text("string", name),
                                                        "SDFalse": Inline(multi)}, origin=("scenery.cpp", at))
        imposter = Obj("TSceneryDescriptorImposteur", {"SceneryDescriptor": ListV([model("leaves"),
                                                                                    model("trunk")])},
                       origin=("scenery.cpp", 9))
        bush_far = Inline(Obj("TSceneryDescriptorImposteur", {"SceneryDescriptor": ListV([model("bush")])}))
        oak = Inline(Obj("TSceneryDescriptorComposite", {"DescriptorComposition": ListV([model("leaves"),
                                                                                         model("trunk")])}))
        game = Game(objects={
            "scenery.cpp#9": imposter,
            "$/Rock": kind(sa.KINDS["rock"].template, [entry(1, model("rock"), off=True)], 1),
            "$/Prop": kind(sa.KINDS["prop"].template, [entry(1, model("prop"))], 2),
            "$/Bush": kind(sa.KINDS["plant"].template, [entry(1, model("bush")), entry(4, bush_far)], 3),
            "$/Oak": kind(sa.KINDS["tree"].template, [entry(2, oak), entry(4, Ref("scenery.cpp#9")),
                                                      entry(8, Ref("scenery.cpp#9"))], 4),
            "$/Oak2": kind("TypeWarrior/Chene_02", [entry(2, oak), entry(4, Ref("scenery.cpp#9"))], 5)})
        assets = [sa.Asset(k.capitalize(), k, None) for k in sa.KINDS]
        run = Engine(game).run([(ModInfo("r2-assets"), parse(sa.rules(game, assets), file="files/assets",
                                                             mod="r2-assets"))])
        self.assertEqual([f.message for f in run.findings if f.level == "error"], [])
        after = run.game

        def models_of(obj, out):
            for k, v in obj.props.items():
                for x in (v.items if isinstance(v, ListV) else [v]):
                    o = x.obj if isinstance(x, Inline) else after.objects.get(x.target) if isinstance(x, Ref) else None
                    if k == "ModelASE":
                        out.append(x.value.rsplit("\\", 1)[-1])
                    elif o is not None:
                        models_of(o, out)
            return out

        def entry_objects(name):
            (_n, _f, o), = descriptors_named(after, {name})[name]
            return [e.obj if isinstance(e, Inline) else after.objects[e.target]
                    for e in o.props["SDFalse"].obj.props["ModeEntry"].items]

        def entries_of(name):
            return [(int(e.props["ModeMask"].value), models_of(e, [])) for e in entry_objects(name)]
        for k in ("rock", "prop"):
            n = k.capitalize()
            self.assertEqual(entries_of(f"TypeWarrior/R2_{n}"), [(1, [f"r2{k}lod0.ASE2NdfBin"]),
                                                                 (4, [f"r2{k}mediumlod0.ASE2NdfBin"]),
                                                                 (8, [f"r2{k}farlod0.ASE2NdfBin"])])
        self.assertEqual([("GraphicOptionDeactivated" in e.props) for e in entry_objects("TypeWarrior/R2_Rock")],
                         [False] * 3)
        self.assertEqual(entries_of("TypeWarrior/R2_Plant"), [(1, ["r2plantlod0.ASE2NdfBin"]),
                                                              (4, ["r2plantmediumlod0.ASE2NdfBin"]),
                                                              (8, ["r2plantfarlod0.ASE2NdfBin"])])
        middle = entry_objects("TypeWarrior/R2_Plant")[1].props["SceneryDescriptor"]
        self.assertIsInstance(middle, Ref)   # (our copy of the close one: 3D, not the game's picture)
        self.assertEqual(after.objects[middle.target].cls, "TSceneryDescriptorModel3D")
        tree = [(m, sorted(ms)) for m, ms in entries_of("TypeWarrior/R2_Tree")]
        self.assertEqual(tree, [(2, ["r2treeleaveslod0.ASE2NdfBin", "r2treewoodlod0.ASE2NdfBin"]),
                                (4, ["r2treeleavesmediumlod0.ASE2NdfBin", "r2treewoodmediumlod0.ASE2NdfBin"]),
                                (8, ["r2treeleavesfarlod0.ASE2NdfBin", "r2treewoodfarlod0.ASE2NdfBin"])])
        self.assertEqual(after.objects["scenery.cpp#9"].props["SceneryDescriptor"].items[0].obj.props["ModelASE"].value,
                         "DataDir:\\leaves")   # (the oaks' shared picture as it was)
        from rusemod.visibility import type_levels   # (what their placed objects ask of the blocks they hang on)
        self.assertEqual(type_levels(after, {sa.type_name(k.capitalize()) for k in sa.KINDS}),
                         {"TypeWarrior/R2_Rock": 0x0D, "TypeWarrior/R2_Prop": 0x0D, "TypeWarrior/R2_Plant": 0x0D,
                          "TypeWarrior/R2_Tree": 0x0E})
        self.assertEqual(entries_of(sa.KINDS["rock"].template), [(1, ["rock"])])
        self.assertTrue(entry_objects(sa.KINDS["rock"].template)[0].props["GraphicOptionDeactivated"].value)
        self.assertEqual(entries_of(sa.KINDS["plant"].template), [(1, ["bush"]), (4, ["bush"])])
        self.assertEqual(entries_of(sa.KINDS["tree"].template), [(2, ["leaves", "trunk"])] + [(m, ["leaves", "trunk"])
                                                                                          for m in (4, 8)])
        self.assertEqual(entries_of("TypeWarrior/Chene_02"), [(2, ["leaves", "trunk"]), (4, ["leaves", "trunk"])])

    def test_a_mods_asset_through_the_build(self):
        """files/assets/<name>/asset.toml read with the mod, its type made by the build's rules (before the mod's
        own: they may change it), the game's rock as it was; two mods' assets of one name refused."""
        from rusemod.build import build_pack, load_mod
        from rusemod.model import load
        from rusemod.patch import Inline
        data = make_ndf(
            objects=[(0, [(0, val(0x07, struct.pack("<I", 0))), (1, ref(1, 1))]),
                     (1, [(2, val(0x11, struct.pack("<I", 1) + ref(2, 2)))]),
                     (2, [(3, val(0x03, struct.pack("<I", 1))), (4, ref(3, 3))]),
                     (3, [(5, val(0x1C, struct.pack("<I", 1)))])],
            classes=["TSceneryDescriptorMultiState", "TSceneryDescriptorMultiMode", "TSceneryDescriptorMultiModeEntry",
                     "TSceneryDescriptorModel3D"],
            props=[("RegistrationName", 0), ("SDFalse", 0), ("ModeEntry", 1), ("ModeMask", 2),
                   ("SceneryDescriptor", 2), ("ModelASE", 3)],
            strings=[sa.KINDS["rock"].template, "DataDir:\\" + ROCK[:-len(".ase2ndfbin")] + ".ASE2NdfBin"],
            exports={0: "Rocher"}, compress=True)
        arc = Edat(make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", data)])]))
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            mods = []
            for mod_id in ("m", "n"):
                mod = Path(d, mod_id)
                (mod / "src").mkdir(parents=True)
                (mod / "mod.toml").write_text(f'[mod]\nid = "{mod_id}"\nname = "M"\nversion = "0.1.0"\n',
                                              encoding="utf-8")
                folder = mod / "files" / "assets" / "Stone"
                folder.mkdir(parents=True)
                write_gltf(folder, [("s", False)])
                (folder / "asset.toml").write_text('kind = "rock"\nmodel = "model_2k.gltf"\n', encoding="utf-8")
                mods.append(load_mod(mod))
            (Path(d, "m") / "src" / "rocks.rndf").write_text(
                "patch @[RegistrationName='TypeWarrior/R2_Stone'] ( RegistrationName = 'TypeWarrior/R2_Stone' )\n",
                encoding="utf-8")
            one = load_mod(Path(d, "m"))
            self.assertEqual(list(one[0].assets), ["Stone"])
            result = build_pack(arc, [one], text_arc=zz_win(game()))
            both = build_pack(arc, mods, text_arc=zz_win(game()))
            alone = build_pack(arc, [one])
        self.assertEqual(result.errors, [])
        self.assertEqual({n: (a.kind, m) for n, (a, m) in result.own_assets.items()}, {"Stone": ("rock", "m")})
        built, _files = load(result.changed)
        found = {}
        for o in built.objects.values():
            reg = o.props.get("RegistrationName")
            if reg is not None:
                found[reg.value] = [e.obj if isinstance(e, Inline) else built.objects[e.target]
                                    for e in o.props["SDFalse"].obj.props["ModeEntry"].items]
        self.assertEqual(sorted(found), ["TypeWarrior/R2_Stone", sa.KINDS["rock"].template])
        mine = found["TypeWarrior/R2_Stone"]
        self.assertEqual([(int(e.props["ModeMask"].value), e.props["SceneryDescriptor"].obj.props["ModelASE"].value)
                          for e in mine],
                         [(1, sa.data_path(sa.model_name(ROCK, "Stone"))),
                          (4, sa.data_path(sa.model_name(ROCK, "Stone", ring="medium"))),
                          (8, sa.data_path(sa.model_name(ROCK, "Stone", ring="far")))])
        theirs, = found[sa.KINDS["rock"].template]
        self.assertEqual(int(theirs.props["ModeMask"].value), 1)
        self.assertTrue(theirs.props["SceneryDescriptor"].obj.props["ModelASE"].value.endswith("rocher_1lod0.ASE2NdfBin"))
        self.assertEqual(len(both.errors), 1)
        self.assertIn("files/assets/Stone: m has an asset of that name too", both.errors[0].message)
        self.assertIn("it wasn't given", alone.errors[0].message)

    def test_the_map_lists_the_types_it_places(self):
        """A map's scenery takes only the types its name table lists (scenery.add_objects): the build adds the asset
        types the mods place there first (the first in-game build refused TypeWarrior/R2_RockFace01, 2026-10-17)."""
        import re
        src = (Path(__file__).resolve().parents[1] / "src/rusemod/build.py").read_text(encoding="utf-8")
        named = re.search(r"if result\.own_assets:  # the mods' own map assets' types.*?raw = add_names\(raw, ", src,
                          re.S)
        self.assertIsNotNone(named)
        self.assertIn("mine = {type_name(n)", named.group(0))
        # and every placed object asking for nothing asks for its type's levels, far included (the second in-game test,
        # 2026-10-17, drew nothing past 385 m), after the objects are set on the ground (grounded() leaves objects with
        # levels alone) and before they go in
        asks = src.index("objects = [_replace(o, levels=asks[o.type])")
        self.assertLess(src.index("objects, lowered = grounded(objects, descs, lowest)"), asks)
        self.assertLess(asks, src.index("changed_members[member], notes = add_objects(raw, objects)"))
        self.assertIn("result.type_levels = visibility.type_levels(run.game, ", src)
        self.assertLess(named.end(), src.index("changed_members[member], notes = add_objects(raw, objects)"))

    def test_no_type_to_copy(self):
        from rusemod.patch import Game
        with self.assertRaisesRegex(sa.AssetError, "no TypeWarrior/RocherNormandie_01"):
            sa.rules(Game(objects={}), [sa.Asset("Rock", "rock", None)])


if __name__ == "__main__":
    unittest.main()
