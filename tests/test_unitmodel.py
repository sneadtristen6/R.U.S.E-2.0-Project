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
from rusemod import Edat, modelin, tgu1, unitmodel
from rusemod.build import build_pack, load_mod
from rusemod.dxt import decode_rgba
from rusemod.model import load
from rusemod.patch import Inline, Ref
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

    def test_a_glb_painted_the_older_way(self):
        """A material in glTF's older specular-glossiness form names its colour picture and colour in that extension
        (2026-10-09: about 30 downloaded models came out plain grey, their paint never read)."""
        from rusemod.dxt import png_bytes
        from rusemod.gltf import FLOAT, UINT, _Glb
        paint = png_bytes(bytes(range(48)), 4, 4)
        g = _Glb()
        tex = g.image(paint, "paint")
        older = "KHR_materials_pbrSpecularGlossiness"
        g.doc["materials"] = [{"name": "Painted", "extensions": {older: {"diffuseTexture": {"index": tex}}}},
                              {"name": "Plain", "extensions": {older: {"diffuseFactor": [0.5, 0.25, 1.0, 1.0]}}},
                              {"name": "Newer", "pbrMetallicRoughness": {"baseColorFactor": [0.1, 0.2, 0.3, 1.0]},
                               "extensions": {older: {"diffuseFactor": [0.5, 0.25, 1.0, 1.0]}}}]
        for k in range(3):
            attrs = {"POSITION": g.accessor([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, float(k))], "VEC3", FLOAT),
                     "TEXCOORD_0": g.accessor([(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], "VEC2", FLOAT)}
            g.doc["meshes"].append({"name": f"m{k}", "primitives": [{"attributes": attrs, "material": k,
                                                                     "indices": g.accessor([0, 1, 2], "SCALAR", UINT,
                                                                                           34963)}]})
            g.doc["nodes"].append({"name": f"m{k}", "mesh": k})
        g.doc["scenes"], g.doc["scene"] = [{"nodes": [0, 1, 2]}], 0
        g.doc["extensionsUsed"] = [older]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "older.glb")
            path.write_bytes(g.to_bytes())
            mats = modelin.read_model(path).materials
        self.assertEqual((mats[0].picture, mats[0].data), ("paint", paint))
        self.assertEqual(mats[1].data, b"")
        self.assertEqual([round(c * 255) for c in mats[1].colour], [188, 137, 255])   # sRGB of the linear factor
        self.assertEqual([round(c * 255) for c in mats[2].colour], [89, 124, 149])    # the newer form's own first

    def test_a_glb_colour_is_linear(self):
        """glTF's colour factors are linear, a picture's bytes sRGB (2026-10-09: the Rapier's mustard, linear (0.138,
        0.112, 0.008), was written (35, 29, 2) and drew black; sRGB it is about (104, 94, 22))."""
        self.assertEqual([round(modelin._srgb(c) * 255) for c in (0.138, 0.112, 0.008)], [104, 94, 22])
        self.assertEqual([round(modelin._srgb(c) * 255) for c in (0.0, 0.002, 1.0, 1.5)], [0, 7, 255, 255])


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


class PlaneFacing(unittest.TestCase):
    """A plane is wider than it is long: fitted to a plane, its longer side is its wings, and its tail fin (its highest
    point) is at the back (2026-10-08: a P-51 came out sideways)."""
    def plane_model(self, fin_x=-4.0):
        fuselage = [(x, y, z) for x in (-4.5, 4.5) for y in (-0.5, 0.5) for z in (0.0, 1.0)]
        wings = [(x, y, 0.5) for x in (-0.5, 1.5) for y in (-5.5, 5.5)]
        fin = [(fin_x - 0.4, 0.0, 2.6), (fin_x + 0.4, 0.0, 1.0)]
        return modelin.Model([modelin.Mesh("body", fuselage + wings + fin, [(0, 1, 2)])], [])

    def test_plane(self):
        like = {"length": 9.8, "width": 11.3, "aircraft": True}            # a P-51's
        m = self.plane_model(fin_x=-4.0)                                     # its fin at -x: it faces +x
        self.assertEqual(modelin.facing(m, ["hull"]), (1, 1))               # longest side: the wings (wrong)
        self.assertEqual(modelin.facing(m, ["hull"], like), (0, 1))         # along the fuselage, nose at +x
        self.assertEqual(modelin.facing(self.plane_model(fin_x=4.0), ["hull"], like), (0, -1))   # fin at +x: -x

    def test_a_jet_copying_a_plane_wider_than_long(self):
        """A jet is longer than it is wide; copying a P-51 (wider than long), the ratio alone turned it sideways (an F-4
        copying a Bf 109, 2026-10-08). Its fin at one end of the fuselage, in the middle of the wings, says which way
        it lies."""
        fuselage = [(x, y, z) for x in (-9.5, 9.5) for y in (-0.8, 0.8) for z in (0.0, 1.5)]
        wings = [(x, y, 0.7) for x in (-3.0, 2.0) for y in (-5.8, 5.8)]
        fin = [(-8.8, 0.0, 5.0), (-7.0, 0.0, 1.5)]
        jet = modelin.Model([modelin.Mesh("body", fuselage + wings + fin, [(0, 1, 2)])], [])
        like = {"length": 9.8, "width": 11.3, "aircraft": True}
        self.assertEqual(modelin.facing(jet, ["hull"], like), (0, 1))          # along the fuselage, fin at -x
        turned = modelin.Model([modelin.Mesh("body", [(y, x, z) for x, y, z in fuselage + wings + fin], [(0, 1, 2)])],
                               [])
        self.assertEqual(modelin.facing(turned, ["hull"], like), (1, 1))       # the same jet along y

    @staticmethod
    def sheet(name, xs, ys, z):
        """A surface over xs x ys at height z(x, y), in triangles."""
        pts = [(x, y, z(x, y)) for x in xs for y in ys]
        n, tris = len(ys), []
        for i in range(len(xs) - 1):
            for j in range(n - 1):
                a, b, c, d = i * n + j, i * n + j + 1, (i + 1) * n + j, (i + 1) * n + j + 1
                tris += [(a, c, b), (b, c, d)]
        return modelin.Mesh(name, pts, tris)

    @staticmethod
    def steps(lo, hi, n):
        return [lo + (hi - lo) * k / (n - 1) for k in range(n)]

    def facing_both_ways(self, meshes, like):
        """facing() of the meshes, and of the same turned end for end (x -> -x)."""
        turned = [modelin.Mesh(m.name, [(-x, y, z) for x, y, z in m.positions], m.triangles) for m in meshes]
        return modelin.facing(modelin.Model(meshes, []), ["hull"] * len(meshes), like), \
            modelin.facing(modelin.Model(turned, []), ["hull"] * len(turned), like)

    def test_a_biplane_whose_top_wing_is_its_highest_point(self):
        """A biplane's top wing stands higher than its fin (2026-10-08: the Fokker Dr.I flew tail first, its top wing
        taken for the fin): the wings stand nearer the nose, so the nose is the end nearer them."""
        s, st = self.sheet, self.steps
        meshes = [s("fuselage", st(-3, 3, 13), (-0.4, 0.4), lambda x, y: 0.9),
                  s("lower", (-2.0, -1.5, -1.0), st(-4, 4, 17), lambda x, y: 0.6),
                  s("upper", st(-2, -1, 5), st(-4, 4, 17), lambda x, y: 2.0 + 0.01 * abs(y)),
                  s("tailplane", (2.4, 2.7, 3.0), st(-1.2, 1.2, 5), lambda x, y: 1.0),
                  modelin.Mesh("fin", [(2.4, 0.0, 1.0), (3.0, 0.0, 1.0), (2.4, 0.0, 1.8), (3.0, 0.0, 1.8)],
                               [(0, 1, 2), (1, 3, 2)])]
        like = {"length": 6.0, "width": 8.0, "aircraft": True}
        self.assertEqual(self.facing_both_ways(meshes, like), ((0, -1), (0, 1)))     # nose at -x, then at +x

    def test_a_plane_parked_tail_down(self):
        """Parked on its tail wheel, a plane's nose stands up and a propeller blade is its highest point, at its nose
        (2026-10-08: the Camel and the P-40 flew tail first, the blade taken for the fin): its tail end's underside is
        down on the ground, so that end is its tail."""
        s, st = self.sheet, self.steps
        meshes = [s("fuselage", st(-3, 3, 25), (-0.4, 0.4), lambda x, y: 1.0 - 0.2 * x),     # nose up at -x
                  s("cowling", (-3.0, -2.8, -2.6), st(-0.5, 0.5, 5), lambda x, y: 1.2),
                  s("wing", st(-2, -1, 5), st(-5, 5, 21), lambda x, y: 1.2),
                  s("tailplane", (2.4, 2.7, 3.0), st(-1.5, 1.5, 7), lambda x, y: 0.5),
                  modelin.Mesh("fin", [(2.6, 0.0, 0.4), (3.0, 0.0, 0.4), (2.8, 0.0, 1.3)], [(0, 1, 2)]),
                  modelin.Mesh("blade", [(-3.2, -0.1, 2.8), (-3.2, 0.1, 2.8), (-3.2, 0.0, 0.6)], [(0, 1, 2)])]
        like = {"length": 6.4, "width": 10.0, "aircraft": True}
        self.assertEqual(self.facing_both_ways(meshes, like), ((0, -1), (0, 1)))     # nose at -x, then at +x

    def test_a_tank_with_nothing_named_faces_its_gun(self):
        """No part called gun or turret (a scan's Object_12...): the end its gun reaches past the hull is its front
        (2026-10-08: 60-odd era tanks faced backwards)."""
        hull = [(x, y, z) for x in (-3.0, 3.0) for y in (-1.5, 1.5) for z in (0.0, 1.0)]
        turret = [(x, y, z) for x in (-1.0, 1.0) for y in (-1.0, 1.0) for z in (1.0, 2.0)]
        gun = [(-6.5, 0.0, 1.5), (-1.0, 0.1, 1.6)]                       # the gun out past the hull at -x
        tank = modelin.Model([modelin.Mesh("Object_1", hull + turret + gun, [(0, 1, 2)])], [])
        self.assertEqual(modelin.facing(tank, ["hull"], {"length": 6.5, "width": 3.6}), (0, -1))
        mirrored = modelin.Model([modelin.Mesh("Object_1", [(-x, y, z) for x, y, z in hull + turret + gun],
                                               [(0, 1, 2)])], [])
        self.assertEqual(modelin.facing(mirrored, ["hull"], {"length": 6.5, "width": 3.6}), (0, 1))

    def test_a_short_reach_is_no_gun(self):
        """Stowage reaching a little past the hull at the back, a short gun not past it at the front (the M2 Bradley
        scan, 2026-10-08: taken the wrong way round when any reach counted): no long gun, so no say from it."""
        hull = [(x, y, z) for x in (-3.0, 3.0) for y in (-1.5, 1.5) for z in (0.0, 1.0)]
        stowage = [(-3.5, 0.0, 0.6), (-3.0, 0.5, 0.8)]                    # 0.5 past the hull at -x
        gun = [(2.5, 0.0, 1.5), (0.5, 0.1, 1.6)]                         # short: inside the hull's length
        m = modelin.Model([modelin.Mesh("Object_1", hull + stowage + gun, [(0, 1, 2)])], [], source="ifv.glb")
        self.assertEqual(modelin.facing(m, ["hull"], {"length": 6.5, "width": 3.6}), (0, 1))

    def test_an_unarmed_gltf_model_faces_the_formats_front(self):
        """Nothing reaching past the hull either way (a truck): a glTF model faces the format's front, +Z, which
        read_glb turns into -y."""
        truck = [(x, y, z) for x in (-1.2, 1.2) for y in (-3.0, 3.0) for z in (0.0, 2.0)]
        m = modelin.Model([modelin.Mesh("Object_1", truck, [(0, 1, 2)])], [], source="truck.glb")
        self.assertEqual(modelin.facing(m, ["hull"], {"length": 6.0, "width": 2.4}), (1, -1))
        self.assertEqual(modelin.facing(modelin.Model(m.meshes, [], source="truck.3ds"), ["hull"],
                                        {"length": 6.0, "width": 2.4}), (1, 1))

    def test_a_facing_pinned_by_hand(self):
        """Whoever imports it can pin the facing when no rule can tell (a box-shaped truck): [axis, sign] in the
        like; anything else there is left to the rules."""
        truck = [(x, y, z) for x in (-1.2, 1.2) for y in (-3.0, 3.0) for z in (0.0, 2.0)]
        m = modelin.Model([modelin.Mesh("Object_1", truck, [(0, 1, 2)])], [], source="truck.glb")
        like = {"length": 6.0, "width": 2.4}
        self.assertEqual(modelin.facing(m, ["hull"], dict(like, facing=[1, 1])), (1, 1))
        self.assertEqual(modelin.facing(m, ["hull"], dict(like, facing=[2, 1])), (1, -1))      # not an axis

    def test_tank_unchanged(self):
        m = modelin.Model([modelin.Mesh("hull", [(x, y, 0.0) for x in (-3, 3) for y in (-1.5, 1.5)], [(0, 1, 2)])],
                          [])
        self.assertEqual(modelin.facing(m, ["hull"], {"length": 6.5, "width": 3.6}), (0, 1))


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

    def test_a_glb_s_own_normals_and_alpha_are_kept(self):
        """Imported again, a .glb keeps its own normals (not worked out again) and its own alpha picture (not the
        plain 144): before 2026-10-05 both were thrown away, so a model's weighted normals and shine map never
        reached the game."""
        own = [[_unit_vec((0.3, -0.2 + 0.01 * i, 1.0)) for i in range(len(p.positions))] for p in self.prep.parts]
        for p, n in zip(self.prep.parts, own):
            p.normals = n
        name, w, h, px = self.prep.pictures[0]
        ramp = bytearray(px)
        ramp[3::4] = bytes(112 + (i % 80) for i in range(w * h))
        self.prep.pictures[0][3] = bytes(ramp)
        modelin.write_glb(self.prep, self.glb, TANK)
        again = modelin.prepare(modelin.read_model(self.glb), self.dir, LIKE)
        self.assertEqual(again.report["normals"], "the model's own")
        self.assertEqual(set(again.report["alpha"].values()), {"the model's own"})
        self.assertEqual(again.pictures[0][3][3::4], bytes(ramp[3::4]))
        for a, b in zip(self.prep.parts, again.parts):
            for p, q in zip(a.positions + a.normals, b.positions + b.normals):
                for x, y in zip(p, q):
                    self.assertAlmostEqual(x, y, places=3)

    def test_without_its_own_normals_and_alpha(self):
        model = modelin.read_model(self.dir / "tank.3ds")
        prep = modelin.prepare(model, self.dir, LIKE)
        self.assertEqual(prep.report["normals"], "worked out")
        self.assertEqual(set(prep.report["alpha"].values()), {f"plain {modelin.PLAIN_ALPHA}"})


def _unit_vec(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


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
        self.assertEqual(s.like, {"length": 200.0, "width": 80.0, "pivot": (-70.0, 5.0), "ground": 2.0,
                                  "middle": -20.0})
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
            # named in the copied body texture's group (TSCComb_...): the game finds a picture through it
            self.assertEqual(list(mats[part.material]["textures"].values()),
                             ["ZZ:\\GenTexGroup\\WW2\\Res3D\\Units\\GER\\Tank\\TSCComb_panzer_model_01.png"])
            u, v = exp.uvs[0]
            self.assertEqual(tuple(part.uvs[0:2]), struct.unpack("<2f", struct.pack("<2f", u, v - 1.0)))
        skel = MeshPack.read(w.changed[SKELETONS])
        self.assertEqual(skel.skeletons, [SKELETON])
        self.assertEqual(skel.items[new][2], skel.items[TANK][2])
        member = "gen\\ww2\\res3d\\units\\ger\\tank\\tsccomb_panzer_model_01.tgv"
        self.assertEqual(list(w.added), [member])
        g = Tgv(w.added[member])
        self.assertEqual((g.width, g.height, g.format, len(g.mips)), (8, 4, "DXT5", 1))  # (its shorter side is 4)
        top = g.payload(len(g.mips) - 1)
        first = decode_rgba(top[32:], 8, 4, "DXT5")[:4]
        self.assertLessEqual(max(abs(a - b) for a, b in zip(first[:3], RED)), 4)  # (5-6-5 colours)
        self.assertEqual(first[3], modelin.PLAIN_ALPHA)
        proxies = ProxyPack.read(w.changed[PROXIES])
        name = "gentexproxy\\ww2\\res3d\\units\\ger\\tank\\tsccomb_panzer_model_01.tgv"
        self.assertIn(name, proxies.names())
        p = proxies.proxies[proxies.names().index(name)]
        self.assertEqual((p.key, p.extra), (unitmodel.standin_key(name), struct.pack("<HHI", 0, 0, 0xAAAAAAAA)))
        self.assertEqual(Tgv(p.data).flag, 0)
        self.assertEqual(proxies.proxies[proxies.names().index(proxy_name(TEX))].data, b"OLD-STANDIN")

    def test_texture_levels_fit_the_room_the_game_makes(self):
        """T35 run 3: the game makes room for level k of a w x h texture as (w * h / 16) >> 2k blocks and writes what
        the level holds; a 1024 x 512 texture taken down to 4 x 4 wrote a block past the room and corrupted the game's
        memory. Levels stop when the shorter side is 4, as every texture of the game's does."""
        for (w, h), count in (((1024, 512), 8), ((256, 128), 6), ((1024, 1024), 9), ((512, 128), 6), ((8, 4), 1),
                              ((4, 4), 1), ((128, 512), 6)):
            g = Tgv(unitmodel.new_texture(bytes(w * h * 4), w, h))
            self.assertEqual(len(g.mips), count, (w, h))
            for m in range(len(g.mips)):  # (smallest first)
                k = len(g.mips) - 1 - m
                head = tgu1.Header.parse(g.payload(m))
                self.assertEqual(head.width * head.height, unitmodel.level_room(w, h, k), (w, h, k))
                self.assertGreater(unitmodel.level_room(w, h, k), 0)
            stand = Tgv(unitmodel.new_standin(bytes(w * h * 4), w, h))
            self.assertEqual(len(stand.payload(0)), stand.width * stand.height)  # one level: 16 bytes a 4 x 4 block

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
PLANE_FILE = "WW2\\Res3D\\Units\\GER\\Avion\\GER_Bf_109lod0.Ase2NdfBin"
# planes as the game's: each one's GfxDescriptor written in it, their MeshDescriptor one object they share (two users:
# loaded as an object of its own, a Ref)
AIR = make_ndf(objects=[(0, [(0, val(0x03, struct.pack("<I", 2))), (1, val(0x02, struct.pack("<i", 1))),
                             (2, ref(1, 1))]),
                        (1, [(3, ref(2, 2))]),
                        (2, [(4, val(0x1C, struct.pack("<I", 0)))]),
                        (0, [(0, val(0x03, struct.pack("<I", 4))), (1, val(0x02, struct.pack("<i", 1))),
                             (2, ref(4, 1))]),
                        (1, [(3, ref(2, 2))])],
               classes=["TAvionDescriptor", "TGfxDescriptorModeleWithAnimation", "TResourceMultiMaterialMesh"],
               props=[("DescriptorId", 0), ("Nationalite", 0), ("GfxDescriptor", 0), ("MeshDescriptor", 1),
                      ("FileName", 2)],
               strings=[PLANE_FILE], exports={0: "Plane", 3: "Plane_PV"}, compress=True)


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

    def test_a_plane_whose_model_part_is_shared(self):
        """A plane's MeshDescriptor names an object of its own in the unit data (the Bf 109's, 2026-10-08), not one
        written in the unit: the copy gets its own copy of that part naming its own model; the copied plane and the
        shared part keep the game's model."""
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d, "mod")
            (mod / "src").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "m"\nname = "M"\nversion = "0.1.0"\n', encoding="utf-8")
            (mod / "src" / "units.rndf").write_text("export Plane_Model is clone $/Plane ( DescriptorId = 3 )\n",
                                                    encoding="utf-8")
            (mod / "files" / "models").mkdir(parents=True)
            (mod / "files" / "models" / "Plane_Model.glb").write_bytes(b"glTF")
            base, _files = load({"genglad\\patchable\\gfx\\everything.cpp.gladndfbin": AIR})
            plane = base.objects[next(k for k in base.objects if k.rsplit("/", 1)[-1] == "Plane")]
            shared = plane.props["GfxDescriptor"].obj.props["MeshDescriptor"]
            self.assertIsInstance(shared, Ref)                      # the fixture's part is the plane's kind
            result = build_pack(Edat(make_edat([("dir", "genglad\\patchable\\gfx\\",
                                                 [("file", "everything.cpp.gladndfbin", AIR)])])),
                                [load_mod(mod)], text_arc=zz_win())
        self.assertEqual(result.errors, [])
        source, glb, _mod_id = result.own_models["Plane_Model"]
        self.assertEqual((source, glb.name), (PLANE_FILE, "Plane_Model.glb"))
        game, _files = load(result.changed)
        objs = {k.rsplit("/", 1)[-1]: v for k, v in game.objects.items()}
        mine = objs["Plane_Model"].props["GfxDescriptor"].obj.props["MeshDescriptor"]
        self.assertIsInstance(mine, Inline)
        self.assertEqual(mine.obj.props["FileName"].value, "WW2\\Res3D\\Units\\GER\\Avion\\Plane_Modellod0.Ase2ndfbin")
        theirs = objs["Plane"].props["GfxDescriptor"].obj.props["MeshDescriptor"]
        self.assertIsInstance(theirs, Ref)
        self.assertEqual(game.objects[theirs.target].props["FileName"].value, PLANE_FILE)


if __name__ == "__main__":
    unittest.main()
