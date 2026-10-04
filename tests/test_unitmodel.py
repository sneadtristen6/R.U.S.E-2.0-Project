"""The model importer (rusemod.modelin, rusemod.unitmodel, rusemod.tga) on made-up files: a .3ds tank of three boxes
(hull, turret, barrel) with a .tga beside it, fitted to a made-up unit, saved as the mod's .glb and read back, then
written into made-up packs beside the unit's model. T35 (2026-10-04) is the same on the game's Sherman and a real
model; scratch tools ran it on the game's packs with every check exact."""
import math
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat, modelin, unitmodel
from rusemod.build import build_pack, load_mod
from rusemod.dxt import decode_rgba
from rusemod.model import load
from rusemod.spk import Spk
from rusemod.tga import TgaError, read_tga
from rusemod.tmst import Tgv
from rusemod.unitpacks import Buffer, MeshPack, Proxy, ProxyPack, proxy_name

SKIN = "$/M3D/System/VERTEXTYPE/TVertex__Position_3f__NormalIn01_4ubn__BlW_4ubn__BlIdx_4ub"
TANK = "ww2\\res3d\\units\\ger\\tank\\ger_panzerivlod0.ase2ndfbin"
TEX = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Units\\GER\\Tank\\TSCComb_CombinedDSCTexture01.png"
MESHES = "gen_5\\pack\\gfxdescriptor\\meshskirmish_ger.spk"
SKELETONS = "gen_5\\pack\\gfxdescriptor\\skeleton_ger.spk"
PROXIES = "gentexproxy\\pack\\gfxdescriptor\\proxyskirmish_ger.ppk"


# --- made-up files ---
def chunk(cid: int, body: bytes) -> bytes:
    return struct.pack("<HI", cid, 6 + len(body)) + body


BOX_FACES = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4), (3, 7, 6), (3, 6, 2), (0, 4, 7),
             (0, 7, 3), (1, 2, 6), (1, 6, 5)]  # each (b - a) x (c - a) points out of the box


def box_object(name: str, lo, hi) -> bytes:
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1),
           (x0, y1, z1)]
    uvs = [(0.25 * (k % 4), 0.5 * (k // 4)) for k in range(8)]
    verts = chunk(0x4110, struct.pack("<H", 8) + b"".join(struct.pack("<3f", *p) for p in pts))
    uv = chunk(0x4140, struct.pack("<H", 8) + b"".join(struct.pack("<2f", *u) for u in uvs))
    facemat = chunk(0x4130, b"Paint\0" + struct.pack("<H", 12) + struct.pack("<12H", *range(12)))
    faces = chunk(0x4120, struct.pack("<H", 12) + b"".join(struct.pack("<4H", *f, 0) for f in BOX_FACES) + facemat)
    return chunk(0x4000, name.encode() + b"\0" + chunk(0x4100, verts + uv + faces))


def tank_3ds() -> bytes:
    """Hull 40 x 100 x 20 (long along y), a turret on it, a barrel pointing to -y: the tank faces -y."""
    material = chunk(0xAFFF, chunk(0xA000, b"Paint\0") + chunk(0xA200, chunk(0xA300, b"PAINT_TE.TGA\0")))
    objects = (box_object("Hull", (-20, -50, 0), (20, 50, 20)) + box_object("Turret", (-12, -20, 20), (12, 10, 35))
               + box_object("Barrel", (-2, -80, 26), (2, -20, 29)))
    return chunk(0x4D4D, chunk(0x3D3D, material + objects))


def tga(w: int, h: int, rows_top_first: list, bits: int = 24) -> bytes:
    """An uncompressed .tga stored bottom row first (the usual way); rows given top first, as (r, g, b) each."""
    head = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, w, h, bits, 0)
    body = b"".join(bytes((b, g, r) + ((255,) if bits == 32 else ())) for row in reversed(rows_top_first)
                    for (r, g, b) in row)
    return head + body


RED, BLUE = (200, 10, 10), (10, 10, 200)
PICTURE = tga(8, 4, [[RED] * 8] + [[BLUE] * 8] * 3)
LIKE = {"length": 200.0, "pivot": (-70.0, 5.0), "ground": 2.0}


def ref(index, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))


def skinned_materials() -> bytes:
    """One TMeshMaterial as the game's body ones: its texture and a SkinningRemapping (local 0 -> bone 0, 1 -> 1)."""
    strings = ["CombinedDSCTexture", "Standard_1", TEX]
    tex = val(0x12, struct.pack("<I", 1) + val(0x07, struct.pack("<I", 0))
              + val(0x22, val(0x1C, struct.pack("<I", 2)) + val(0x03, bytes(4))))
    skin = val(0x11, struct.pack("<I", 2) + val(0x02, struct.pack("<i", 0)) + val(0x02, struct.pack("<i", 1)))
    objects = [(0, [(0, val(0x11, struct.pack("<I", 1) + ref(1, 1)))]),
               (1, [(1, tex), (2, val(0x07, struct.pack("<I", 1))), (3, skin)])]
    return make_ndf(objects, ["TEugBListPBaseClass", "TMeshMaterial"],
                    [("Value", 0), ("Textures", 1), ("MaterialName", 1), ("SkinningRemapping", 1)],
                    strings=strings, topo=(0,))


def skeleton(names, parents, pivots) -> bytes:
    """A skeleton entry laid out as the game's: header, name lengths at 0x24, 3 x 4 matrices (model -> bone: here
    a move by -pivot), parents, a second table, the names."""
    n = len(names)
    lens = struct.pack(f"<{n}H", *(len(x) for x in names))
    mats_at = (0x24 + len(lens) + 3) & ~3
    mats = b"".join(struct.pack("<12f", 1, 0, 0, -x, 0, 1, 0, -y, 0, 0, 1, -z) for x, y, z in pivots)
    parents_at = mats_at + len(mats)
    second_at = parents_at + 4 * n
    names_at = second_at + 4 * n
    head = struct.pack("<9I", 1, n, mats_at, parents_at, second_at, names_at, mats_at, 4 * n, 4 * n)
    body = head + lens
    body += bytes(mats_at - len(body)) + mats + struct.pack(f"<{n}i", *parents) + struct.pack(f"<{n}i", *range(n))
    return body + "".join(names).encode()


SKELETON = skeleton(["chassis", "tourelle_01"], [-1, 0], [(0.0, 0.0, 0.0), (-70.0, 5.0, 30.0)])


def unit_pack() -> MeshPack:
    """The Panzer: one draw call of a skinned quad on the chassis, 200 long (x -120..80), lowest at z 2."""
    pts = [(-120.0, -40.0, 2.0), (80.0, -40.0, 2.0), (80.0, 40.0, 2.0), (-120.0, 40.0, 2.0)]
    verts = b"".join(struct.pack("<3f4B4B4B", *p, 128, 128, 255, 0, 255, 0, 0, 0, 0, 0, 0, 0) for p in pts)
    pack = MeshPack(formats=[SKIN.encode().ljust(256, b"\0")], materials=skinned_materials(), material_count=1)
    pack.ibs.append(Buffer(struct.pack("<6H", 0, 1, 2, 0, 2, 3), 12, 6, 1, 0))
    pack.vbs.append(Buffer(verts, len(verts), 4, 0, 0))
    pack.draws.append((0, 0, 0, 0, 0xFFFF, 0xCDCD))
    pack.meshes.append((0, 1))
    pack.items[TANK] = [struct.pack("<6fI", -120, -40, 2, 80, 40, 2, 1), 0, 0xCDCD]
    return pack


def zz_win() -> Edat:
    skel = MeshPack(formats=[], materials=b"", material_count=0, has_formats=False)
    skel.materials = MeshPack.read(unit_pack().to_bytes()).materials
    skel.skeletons.append(SKELETON)
    skel.items[TANK] = [bytes(28), 0xCDCD, 0]
    proxies = ProxyPack([Proxy(b"K" * 8, b"OLD-STANDIN", struct.pack("<HHI", 0, 0, 0xAAAAAAAA),
                               proxy_name(TEX).encode().ljust(256, b"\0"))], [0])
    files = {MESHES: unit_pack().to_bytes(), SKELETONS: skel.to_bytes(), PROXIES: proxies.to_bytes()}
    tree: dict = {}
    for path, data in files.items():
        folder, _, name = path.rpartition("\\")
        tree.setdefault(folder + "\\", []).append(("file", name, data))
    return Edat(make_edat([("dir", folder, items) for folder, items in tree.items()]))


def signed_volume(part) -> float:
    total = 0.0
    for a, b, c in part.triangles:
        pa, pb, pc = part.positions[a], part.positions[b], part.positions[c]
        total += (pa[0] * (pb[1] * pc[2] - pb[2] * pc[1]) - pa[1] * (pb[0] * pc[2] - pb[2] * pc[0])
                  + pa[2] * (pb[0] * pc[1] - pb[1] * pc[0])) / 6
    return total


class Pictures(unittest.TestCase):
    def test_a_tga_bottom_row_first(self):
        w, h, px = read_tga(PICTURE)
        self.assertEqual((w, h), (8, 4))
        self.assertEqual(px[:4], bytes(RED) + b"\xff")      # top row first
        self.assertEqual(px[-4:], bytes(BLUE) + b"\xff")

    def test_a_tga_with_alpha_and_run_length(self):
        head = struct.pack("<BBBHHBHHHHBB", 0, 0, 10, 0, 0, 0, 0, 0, 3, 1, 32, 0x20)  # top row first
        body = bytes([0x82, 1, 2, 3, 77])                    # one pixel three times
        self.assertEqual(read_tga(head + body), (3, 1, bytes([3, 2, 1, 77]) * 3))

    def test_what_isn_t_read(self):
        with self.assertRaises(TgaError):
            read_tga(struct.pack("<BBBHHBHHHHBB", 0, 1, 1, 0, 0, 0, 0, 0, 2, 2, 8, 0) + bytes(4))

    def test_the_8_3_name_a_3ds_keeps(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "sub").mkdir()
            Path(d, "sub", "Paint_Texture.tga").write_bytes(PICTURE)
            Path(d, "Other.tga").write_bytes(PICTURE)
            self.assertEqual(modelin.find_picture("PAINT_TE.TGA", Path(d)), Path(d, "sub", "Paint_Texture.tga"))
            self.assertEqual(modelin.find_picture("other.tga", Path(d)), Path(d, "Other.tga"))
            self.assertIsNone(modelin.find_picture("NOTHERE.TGA", Path(d)))


class Fitting(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        (self.dir / "tank.3ds").write_bytes(tank_3ds())
        (self.dir / "Paint_Texture.tga").write_bytes(PICTURE)
        self.model = modelin.read_model(self.dir / "tank.3ds")

    def test_read(self):
        self.assertEqual([m.name for m in self.model.meshes], ["Hull", "Turret", "Barrel"])
        self.assertEqual(self.model.counts(), (24, 36))
        self.assertEqual([(m.name, m.picture) for m in self.model.materials], [("Paint", "PAINT_TE.TGA")])
        self.assertEqual(set(self.model.meshes[0].face_materials), {0})

    def test_roles_and_facing(self):
        parts = modelin.roles(self.model)
        self.assertEqual(parts, [modelin.HULL, modelin.TURRET, modelin.GUN])
        self.assertEqual(modelin.facing(self.model, parts), (1, -1))  # the barrel points to -y

    def test_a_part_on_the_turret_turns_with_it(self):
        raw = tank_3ds()
        extra = box_object("Hatch", (-3, -5, 35), (3, 5, 37))
        main = chunk(0x4D4D, chunk(0x3D3D, raw[12:] + extra))  # (the editor chunk's body, plus one more object)
        (self.dir / "more.3ds").write_bytes(main)
        model = modelin.read_model(self.dir / "more.3ds")
        self.assertEqual(modelin.roles(model)[-1], modelin.TURRET)

    def test_fitted_to_the_unit(self):
        prep = modelin.prepare(self.model, self.dir, LIKE)
        self.assertEqual(prep.report["facing"], ("y", -1))
        self.assertAlmostEqual(prep.report["scale"], 2.0)          # the hull's 100 to the unit's 200
        hull = next(p for p in prep.parts if p.bone == "chassis")
        turret = next(p for p in prep.parts if p.bone == "tourelle_01")
        self.assertEqual(len(prep.parts), 2)
        # forward (-y) is the game's x, right (-x) its y; the turret ring (x 0, y -5) onto the pivot; z 0 to 2
        xs, ys, zs = zip(*hull.positions)
        self.assertEqual((min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)), (-180, 20, -35, 45, 2, 42))
        ring = [p for p in turret.positions if p[2] < 45]
        self.assertAlmostEqual((min(p[0] for p in ring) + max(p[0] for p in ring)) / 2, -70)
        self.assertAlmostEqual((min(p[1] for p in ring) + max(p[1] for p in ring)) / 2, 5)
        for part in prep.parts:  # wound the game's way: every closed box's volume comes out positive
            self.assertGreater(signed_volume(part), 0)
            for n in part.normals:
                self.assertAlmostEqual(math.sqrt(sum(c * c for c in n)), 1.0, places=6)

    def test_pictures_and_their_corners(self):
        prep = modelin.prepare(self.model, self.dir, LIKE)
        name, w, h, px = prep.pictures[0]
        self.assertEqual((name, w, h), ("Paint_Texture.tga", 8, 4))
        self.assertEqual(px[:4], bytes(RED) + bytes([modelin.PLAIN_ALPHA]))  # colours kept, the game's plain alpha
        hull = next(p for p in prep.parts if p.bone == "chassis")
        self.assertIn((0.25, 0.5), hull.uvs)  # a .3ds (0.25, 0.5) runs up the picture; the game's down: 1 - v

    def test_size_and_a_model_without_a_turret(self):
        prep = modelin.prepare(self.model, self.dir, LIKE, size=1.5)
        self.assertAlmostEqual(prep.report["scale"], 3.0)
        lone = modelin.Model([self.model.meshes[0]], self.model.materials)
        prep = modelin.prepare(lone, self.dir, dict(LIKE, middle=-20.0))
        xs = [p[0] for p in prep.parts[0].positions]
        self.assertAlmostEqual((min(xs) + max(xs)) / 2, -20.0)


class ModFile(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        (self.dir / "tank.3ds").write_bytes(tank_3ds())
        (self.dir / "Paint_Texture.tga").write_bytes(PICTURE)
        self.prep = modelin.prepare(modelin.read_model(self.dir / "tank.3ds"), self.dir, LIKE)
        self.glb = self.dir / "files" / "models" / "Panzer_Model.glb"
        modelin.write_glb(self.prep, self.glb, TANK)

    def test_read_back_as_written(self):
        back = unitmodel.read_mod_glb(self.glb)
        self.assertEqual([(p.bone, p.picture, p.triangles) for p in back.parts],
                         [(p.bone, p.picture, p.triangles) for p in self.prep.parts])
        for a, b in zip(self.prep.parts, back.parts):
            for p, q in zip(a.positions + a.normals, b.positions + b.normals):
                for x, y in zip(p, q):
                    self.assertAlmostEqual(x, y, places=3)
            self.assertEqual(len(a.uvs), len(b.uvs))
        self.assertEqual(back.pictures[0][1:], self.prep.pictures[0][1:])  # colour and alpha, every pixel

    def test_a_glb_reads_as_a_model_too(self):
        model = modelin.read_model(self.glb)
        self.assertEqual(sorted({m.name for m in model.meshes}), ["chassis", "tourelle_01"])
        self.assertTrue(model.materials[0].data.startswith(b"\x89PNG"))
        self.assertEqual(unitmodel.mod_models(self.dir), {"Panzer_Model": self.glb})


class Packs(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "tank.3ds").write_bytes(tank_3ds())
        (d / "Paint_Texture.tga").write_bytes(PICTURE)
        self.zz = zz_win()
        self.source = unitmodel.find_source(self.zz, TANK)
        self.prep = modelin.prepare(modelin.read_model(d / "tank.3ds"), d, self.source.like)

    def test_the_key_a_stand_in_is_found_by(self):  # two of the game's 2,822, as stored
        self.assertEqual(unitmodel.standin_key(
            "gentexproxy\\ww2\\res3d\\units\\us\\char\\us_m4_sherman\\tsccombcs_combineddsctexture01.tgv").hex(),
            "884f737aa5ada32c")
        self.assertEqual(unitmodel.standin_key("gentexproxy\\ww2\\res2d\\stikers_impact\\coc_impact_01.tgv").hex(),
                         "4654a692532da282")

    def test_what_fitting_takes_from_the_unit(self):
        s = self.source
        self.assertEqual((s.mesh_packs.keys(), s.skeleton_packs.keys()), ({MESHES}, {SKELETONS}))
        self.assertEqual(s.skeleton.names, ["chassis", "tourelle_01"])
        self.assertEqual(s.like, {"length": 200.0, "pivot": (-70.0, 5.0), "ground": 2.0, "middle": -20.0})
        self.assertEqual(s.body_texture, TEX)

    def test_written_beside_the_unit_s_model(self):
        w = unitmodel.write_unit_model(self.zz, TANK, "panzer_model", self.prep)
        new = "ww2\\res3d\\units\\ger\\tank\\panzer_modellod0.ase2ndfbin"
        self.assertEqual(w.model, new)
        self.assertEqual(sorted(w.changed), sorted([MESHES, SKELETONS, PROXIES]))
        spk = Spk(w.changed[MESHES])
        self.assertEqual(set(spk.items), {TANK, new})
        old = Spk(bytes(self.zz.read(self.zz.entry(MESHES))))
        self.assertEqual(spk.part(spk.meshes[spk.items[TANK].mesh][0]).positions,
                         old.part(old.meshes[old.items[TANK].mesh][0]).positions)
        first, count = spk.meshes[spk.items[new].mesh]
        self.assertEqual(count, 2)
        mats = spk.materials()
        for k in range(count):
            part, exp = spk.part(first + k), self.prep.parts[k]
            self.assertEqual(len(part.positions) // 3, len(exp.positions))
            self.assertEqual([tuple(part.indices[i:i + 3]) for i in range(0, len(part.indices), 3)], exp.triangles)
            self.assertEqual({tuple(b) for b in part.bones}, {(0 if exp.bone == "chassis" else 1, 0, 0, 0)})
            self.assertEqual(mats[part.material]["skinning"], [0, 1])
            self.assertEqual(list(mats[part.material]["textures"].values()),
                             ["ZZ:\\GenTexGroup\\WW2\\Res3D\\Units\\GER\\Tank\\panzer_model_01.png"])
            u, v = exp.uvs[0]
            self.assertEqual(tuple(part.uvs[0:2]), struct.unpack("<2f", struct.pack("<2f", u, v - 1.0)))
        skel = MeshPack.read(w.changed[SKELETONS])
        self.assertEqual(skel.skeletons, [SKELETON])
        self.assertEqual(skel.items[new][2], skel.items[TANK][2])
        member = "gen\\ww2\\res3d\\units\\ger\\tank\\panzer_model_01.tgv"
        self.assertEqual(list(w.added), [member])
        g = Tgv(w.added[member])
        self.assertEqual((g.width, g.height, g.format, len(g.mips)), (8, 4, "DXT5", 2))
        top = g.payload(len(g.mips) - 1)
        first = decode_rgba(top[32:], 8, 4, "DXT5")[:4]
        self.assertLessEqual(max(abs(a - b) for a, b in zip(first[:3], RED)), 4)  # (5-6-5 colours)
        self.assertEqual(first[3], modelin.PLAIN_ALPHA)
        proxies = ProxyPack.read(w.changed[PROXIES])
        name = "gentexproxy\\ww2\\res3d\\units\\ger\\tank\\panzer_model_01.tgv"
        self.assertIn(name, proxies.names())
        p = proxies.proxies[proxies.names().index(name)]
        self.assertEqual((p.key, p.extra), (unitmodel.standin_key(name), struct.pack("<HHI", 0, 0, 0xAAAAAAAA)))
        self.assertEqual(Tgv(p.data).flag, 0)
        self.assertEqual(proxies.proxies[proxies.names().index(proxy_name(TEX))].data, b"OLD-STANDIN")

    def test_refused(self):
        with self.assertRaisesRegex(unitmodel.UnitModelError, "no mesh pack holds"):
            unitmodel.write_unit_model(self.zz, "ww2\\nothing\\nonelod0.ase2ndfbin", "x", self.prep)
        w = unitmodel.write_unit_model(self.zz, TANK, "panzer_model", self.prep)
        later = {**w.changed}
        with self.assertRaisesRegex(unitmodel.UnitModelError, "already have a model"):
            unitmodel.write_unit_model(_with(self.zz, later), TANK, "panzer_model", self.prep)


def _with(zz: Edat, changed: dict) -> Edat:
    return Edat(zz.to_bytes(replace=changed))


ARMY = make_ndf(objects=[(0, [(0, val(0x03, struct.pack("<I", 2))), (1, val(0x02, struct.pack("<i", 1))),
                              (2, ref(1, 1))]),
                         (1, [(3, ref(2, 2))]),
                         (2, [(4, val(0x1C, struct.pack("<I", 0)))])],
                classes=["TUniteAuSolDescriptor", "TGfxDescriptorModeleWithAnimation", "TResourceMultiMaterialMesh"],
                props=[("DescriptorId", 0), ("Nationalite", 0), ("GfxDescriptor", 0), ("MeshDescriptor", 1),
                       ("FileName", 2)],
                strings=["WW2\\Res3D\\Units\\GER\\Tank\\GER_PanzerIVlod0.Ase2NdfBin"], exports={0: "Panzer"},
                compress=True)
UNIT_PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ARMY)])])


class TheBuild(unittest.TestCase):
    def build(self, rndf: str, models=("Panzer_Model",)):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d, "mod")
            (mod / "src").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "m"\nname = "M"\nversion = "0.1.0"\n', encoding="utf-8")
            (mod / "src" / "units.rndf").write_text(rndf, encoding="utf-8")
            (mod / "files" / "models").mkdir(parents=True)
            for unit in models:
                (mod / "files" / "models" / f"{unit}.glb").write_bytes(b"glTF")
            info = load_mod(mod)
            self.assertEqual(sorted(info[0].models), sorted(models))
            return build_pack(Edat(UNIT_PACK), [info], text_arc=zz_win())

    def test_the_new_unit_names_its_own_model(self):
        result = self.build("export Panzer_Model is clone $/Panzer ( DescriptorId = 3 )\n")
        self.assertEqual(result.errors, [])
        source, glb, mod_id = result.own_models["Panzer_Model"]
        self.assertEqual((source, glb.name, mod_id),
                         ("WW2\\Res3D\\Units\\GER\\Tank\\GER_PanzerIVlod0.Ase2NdfBin", "Panzer_Model.glb", "m"))
        game, _files = load(result.changed)
        names = {}
        for unit in ("Panzer_Model", "Panzer"):
            obj = game.objects[next(k for k in game.objects if k.rsplit("/", 1)[-1] == unit)]
            names[unit] = obj.props["GfxDescriptor"].obj.props["MeshDescriptor"].obj.props["FileName"].value \
                if unit == "Panzer_Model" else None
        self.assertEqual(names["Panzer_Model"], "WW2\\Res3D\\Units\\GER\\Tank\\Panzer_Modellod0.Ase2ndfbin")

    def test_a_model_for_no_new_unit(self):
        result = self.build("export Panzer_2 is clone $/Panzer ( DescriptorId = 3 )\n")
        self.assertEqual(len(result.errors), 1)
        self.assertIn("no mod in the set makes a new unit Panzer_Model", result.errors[0].message)


if __name__ == "__main__":
    unittest.main()
