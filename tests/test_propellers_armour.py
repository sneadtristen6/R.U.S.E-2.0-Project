"""Two fixes from a player's report (2026-10-10), on made-up files:
- an imported plane keeps its spinning propeller discs: the discs `ruse export-model` writes (<model>_propeller) go
  on the copied plane's own disc bones, drawn with a copy of its propeller material (rusemod.modelin.fit_discs,
  rusemod.unitmodel); before, they came back as plain squares painted with the whole picture. Checked on the game's
  34 planes the importer can copy, each exported and imported back: every disc on its bone and in its place;
- a unit's armour is picked as one of the game's levels (StudioApi.armour / set_armour): the unit points at the game's
  own armour object of that level, so the shield on its card matches what it fights with (before, a number changed
  inside the armour part fought as 4 while the card still said 2). Checked on the game: a copy of the Semovente 105
  given level 4 builds with the game's own armour object of BaseBlindage 8."""
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from test_unitmodel import BOX_FACES, MESHES, PROXIES, SKELETONS, SKIN, TANK, TEX, ref, skeleton, zz_win
from rusemod import Edat, modelin, unitmodel
from rusemod.build import find_pack, load_mod, load_pack
from rusemod.dic import name_to_key
from rusemod.index import build_index
from rusemod.patch import Engine, Ref
from rusemod.spk import Spk
from rusemod.unitpacks import Buffer, MeshPack, Proxy, ProxyPack, proxy_name
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import ModEdits

PLANE = "ww2\\res3d\\units\\uk\\avion\\uk_testplane\\uk_testplanelod0.ase2ndfbin"
DISC_CENTRE, DISC_RADIUS = (100.0, 0.0, 10.0), 30.0


# --- a made-up plane: a body on the chassis, one propeller disc on helice_hs_1 ---
def plane_materials() -> bytes:
    """Two TMeshMaterials as a plane's: the body (Standard) and the disc (helice_1), the same picture and remapping."""
    strings = ["CombinedDSCTexture", "Standard_1", TEX, "$helice_1$", "helice_1", "Standard"]
    tex = val(0x12, struct.pack("<I", 1) + val(0x07, struct.pack("<I", 0))
              + val(0x22, val(0x1C, struct.pack("<I", 2)) + val(0x03, bytes(4))))
    skin = val(0x11, struct.pack("<I", 2) + val(0x02, struct.pack("<i", 0)) + val(0x02, struct.pack("<i", 1)))

    def s(i):
        return val(0x07, struct.pack("<I", i))
    objects = [(0, [(0, val(0x11, struct.pack("<I", 2) + ref(1, 1) + ref(2, 1)))]),
               (1, [(1, tex), (2, s(1)), (3, skin), (4, s(5))]),
               (1, [(1, tex), (2, s(3)), (3, skin), (4, s(4))])]
    return make_ndf(objects, ["TEugBListPBaseClass", "TMeshMaterial"],
                    [("Value", 0), ("Textures", 1), ("MaterialName", 1), ("SkinningRemapping", 1),
                     ("MaterialType", 1)], strings=strings, topo=(0,))


PLANE_SKELETON = skeleton(["chassis", "helice_hs_1"], [-1, 0], [(0.0, 0.0, 0.0), DISC_CENTRE])


def _quad(points, bone: int) -> bytes:
    return b"".join(struct.pack("<3f4B4B4B", *p, 128, 128, 255, 0, 255, 0, 0, 0, bone, 0, 0, 0) for p in points)


def plane_pack() -> MeshPack:
    """The body: a flat quad 200 long (x -120..80) at z 2; the disc: a square 60 across at x 100, middle z 10."""
    body = [(-120.0, -40.0, 2.0), (80.0, -40.0, 2.0), (80.0, 40.0, 2.0), (-120.0, 40.0, 2.0)]
    x, (_cx, cy, cz), r = DISC_CENTRE[0], DISC_CENTRE, DISC_RADIUS
    disc = [(x, cy - r, cz - r), (x, cy + r, cz - r), (x, cy + r, cz + r), (x, cy - r, cz + r)]
    pack = MeshPack(formats=[SKIN.encode().ljust(256, b"\0")], materials=plane_materials(), material_count=2)
    for k, (pts, bone) in enumerate(((body, 0), (disc, 1))):
        verts = _quad(pts, bone)
        pack.ibs.append(Buffer(struct.pack("<6H", 0, 1, 2, 0, 2, 3), 12, 6, 1, 0))
        pack.vbs.append(Buffer(verts, len(verts), 4, 0, 0))
        pack.draws.append((0, k, k, k, 0xFFFF, 0xCDCD))
    pack.meshes.append((0, 2))
    pack.items[PLANE] = [struct.pack("<6fI", -120, -40, -20, 100, 40, 40, 1), 0, 0xCDCD]
    return pack


def plane_zz() -> Edat:
    skel = MeshPack(formats=[], materials=b"", material_count=0, has_formats=False)
    skel.materials = MeshPack.read(plane_pack().to_bytes()).materials
    skel.skeletons.append(PLANE_SKELETON)
    skel.items[PLANE] = [bytes(28), 0xCDCD, 0]
    proxies = ProxyPack([Proxy(b"K" * 8, b"OLD-STANDIN", struct.pack("<HHI", 0, 0, 0xAAAAAAAA),
                               proxy_name(TEX).encode().ljust(256, b"\0"))], [0])
    files = {MESHES: plane_pack().to_bytes(), SKELETONS: skel.to_bytes(), PROXIES: proxies.to_bytes()}
    tree: dict = {}
    for path, data in files.items():
        folder, _, name = path.rpartition("\\")
        tree.setdefault(folder + "\\", []).append(("file", name, data))
    return Edat(make_edat([("dir", folder, items) for folder, items in tree.items()]))


def box(name: str, lo, hi) -> modelin.Mesh:
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1),
           (x0, y1, z1)]
    return modelin.Mesh(name, pts, list(BOX_FACES), [(0.5, 0.5)] * 8, [0] * 12)


def discs(name: str, centres) -> modelin.Mesh:
    """Flat squares 60 across standing across x, as rusemod.gltf exports a plane's discs (one mesh for them all)."""
    pts, tris = [], []
    for cx, cy, cz in centres:
        n = len(pts)
        pts += [(cx, cy - 30, cz - 30), (cx, cy + 30, cz - 30), (cx, cy + 30, cz + 30), (cx, cy - 30, cz + 30)]
        tris += [(n, n + 1, n + 2), (n, n + 2, n + 3)]
    return modelin.Mesh(name, pts, tris, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)] * len(centres),
                        [0] * len(tris))


def plane_model(*meshes) -> modelin.Model:
    """A plane in the game's axes, as an exported one comes back: its body the copied plane's size and place."""
    body = box("uk_testplane", (-120, -40, 2), (80, 40, 12))
    return modelin.Model([body, *meshes], [modelin.Material("paint", colour=(0.5, 0.5, 0.5))], "plane.glb")


class PropellerDiscs(unittest.TestCase):
    def setUp(self):
        self.zz = plane_zz()
        self.source = unitmodel.find_source(self.zz, PLANE)
        self.like = dict(self.source.like, aircraft=True)

    def test_the_copied_planes_discs(self):
        self.assertEqual(self.source.like["propellers"],
                         [{"bone": "helice_hs_1", "centre": DISC_CENTRE, "radius": DISC_RADIUS}])
        self.assertEqual(unitmodel.find_source(zz_win(), TANK).like["propellers"], [])

    def test_only_a_mesh_of_discs_is_one(self):
        m = plane_model(discs("uk_testplane_propeller.001", [(101, 0, 9)]), box("Spitfire_Propeller", (90, -5, 0),
                                                                                 (95, 5, 20)))
        self.assertEqual(modelin.roles(m), ["hull", "propeller", "hull"])  # blades named so stay a part of the plane
        self.assertIsNone(modelin.disc_pieces(m.meshes[2]))
        self.assertEqual(len(modelin.disc_pieces(m.meshes[1])), 1)

    def test_a_disc_goes_on_the_copied_planes_disc_bone_where_its_disc_is(self):
        prep = modelin.prepare(plane_model(discs("uk_testplane_propeller", [(101, 0, 9)])), [], self.like)
        self.assertEqual(prep.report["propellers"], {"kept": 1, "left_out": 0, "why": ""})
        self.assertEqual(prep.report["facing"], ("x", 1))
        disc = [p for p in prep.parts if p.bone == "helice_hs_1"]
        self.assertEqual(len(disc), 1)
        xs, ys, zs = zip(*disc[0].positions)
        middle = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
        self.assertEqual(tuple(round(c, 6) for c in middle), DISC_CENTRE)  # moved 1 back and 1 up onto it
        self.assertEqual(len(disc[0].triangles), 2)
        self.assertNotIn(modelin.BONES[modelin.PROPELLER], {p.bone for p in prep.parts})

    def test_discs_left_out_say_why(self):
        far = modelin.prepare(plane_model(discs("uk_testplane_propeller", [(101, 0, 9), (100, 200, 10)])), [],
                              self.like)
        self.assertEqual(far.report["propellers"], {"kept": 1, "left_out": 1, "why": "far"})
        none = modelin.prepare(plane_model(discs("uk_testplane_propeller", [(101, 0, 9)])), [],
                               dict(self.like, propellers=[]))
        self.assertEqual(none.report["propellers"], {"kept": 0, "left_out": 1, "why": "none"})
        self.assertEqual({p.bone for p in none.parts}, {"chassis"})
        self.assertIn("propeller disc(s) left out", none.report["notes"][-1])

    def test_a_disc_spins_with_the_planes_propeller_material(self):
        prep = modelin.prepare(plane_model(discs("uk_testplane_propeller", [(101, 0, 9)])), [], self.like)
        w = unitmodel.write_unit_model(self.zz, PLANE, "testplane_new", prep)
        spk = Spk(w.changed[MESHES])
        mats = spk.materials()
        got = {}
        for part in spk.model(w.model):
            m = mats[part.material]
            got[m["type"]] = ({tuple(b) for b in part.bones}, m["name"], list(m["textures"].values()))
        new_picture = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Units\\GER\\Tank\\TSCComb_testplane_new_01.png"
        self.assertEqual(got["helice_1"], ({(1, 0, 0, 0)}, "$helice_1$", [new_picture]))  # bone 1: helice_hs_1
        self.assertEqual(got["Standard"], ({(0, 0, 0, 0)}, "Standard_1", [new_picture]))
        disc = next(p for p in spk.model(w.model) if mats[p.material]["type"] == "helice_1")
        self.assertEqual(unitmodel._discs(disc, mats[disc.material]["skinning"], self.source.skeleton),
                         self.source.like["propellers"])

    def test_a_plane_exported_by_us_faces_the_games_way(self):
        """Its discs say it's the game's own plane, in the game's axes: +x, whatever the rules would guess (the Kyushu
        Shinden, its propeller at its tail, came back backwards by them)."""
        m = plane_model(discs("uk_testplane_propeller", [(-125, 0, 9)]))
        parts = modelin.roles(m)
        self.assertEqual(modelin.facing_of(m, parts, self.like), (0, 1))
        self.assertEqual(modelin.facing_of(m, parts, dict(self.like, facing=[1, -1])), (1, -1))  # pinned wins


# --- a made-up game with armour levels ---
TANKNAME = name_to_key("TANK")


def i32(v):
    return val(0x02, struct.pack("<i", v))


def lst(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(items))


def objref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


UNITS = make_ndf(
    objects=[(0, [(0, lst(i32(30))), (1, val(0x1D, struct.pack("<Q", TANKNAME))), (2, objref(2, 1))]),  # 0 a tank
             (0, [(0, lst(i32(10))), (2, objref(4, 1))]),                                               # 1 a truck
             (1, [(3, i32(6))]),                                                                        # 2 level 6
             (1, [(3, i32(8))]),                                                                        # 3 level 8
             (1, [(3, i32(4))]),                                                                        # 4 level 4
             (1, [])],                                                                                  # 5 buildings
    classes=["TUniteAuSolDescriptor", "TArmorDescriptor"],
    props=[("ProductionPrice", 0), ("NameInMenuToken", 0), ("ArmorDescriptor", 0), ("BaseBlindage", 1)],
    exports={0: "GFX/Everything/Descriptor_Unit_Tank", 1: "GFX/Everything/Descriptor_Unit_Truck"},
    topo=[0, 1])
TANK_UNIT = "$/GFX/Everything/Descriptor_Unit_Tank"


class Armour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        rev = cls.game / "Data" / "PC" / "190852"
        rev.mkdir(parents=True)
        (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "everything.cpp.gladndfbin", UNITS)]))
        (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
            ("dir", "us\\", [("file", "baseunite.dic", make_dic([(TANKNAME, "Tank")]))])])]))
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=Path(home.name))
        self.api.new_mod("Armour test")

    def test_the_levels_and_the_units_own(self):
        a = self.api.armour(TANK_UNIT)
        self.assertEqual([lv["value"] for lv in a["levels"]], [6, 8, 4])  # tanks' first, as the game has them
        self.assertEqual(a["levels"][0], {"value": 6, "word": "armour_tank", "n": 2})
        self.assertEqual((a["game"], a["value"], a["old"], a["editable"]), (6, None, None, True))
        self.assertTrue(self.api.unit(TANK_UNIT)["has_armour"])

    def test_a_level_picked_points_at_the_games_own_armour_and_builds(self):
        res = self.api.set_armour(TANK_UNIT, 8)
        self.assertEqual((res["value"], res["game"]), (8, 6))
        folder = Path(self.api._edits().folder)
        self.assertIn("ArmorDescriptor = @TArmorDescriptor[BaseBlindage=8]",
                      (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        arc = Edat.open(str(find_pack(self.game, "ZZ_GladPatchableWin.dat")))
        try:
            info, ops = load_mod(folder)
            run = Engine(load_pack(arc).base).run([(info, ops)])
        finally:
            arc.close()
        self.assertEqual([f.message for f in run.findings if f.level == "error"], [])
        armour = run.game.objects[TANK_UNIT].props["ArmorDescriptor"]
        self.assertIsInstance(armour, Ref)
        self.assertEqual(run.game.objects[armour.target].props["BaseBlindage"].value, 8)
        self.assertEqual(self.api.set_armour(TANK_UNIT, 6)["value"], None)  # the game's own again: no change kept
        self.assertNotIn("ArmorDescriptor", (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))

    def test_the_old_way_is_said_and_mended(self):
        edits = self.api._edits()
        edits.set(f"{TANK_UNIT}:ArmorDescriptor", "BaseBlindage", 8, "own")
        self.assertEqual(self.api.armour(TANK_UNIT)["old"], 8)
        res = self.api.set_armour(TANK_UNIT, 8)
        self.assertEqual((res["value"], res["old"]), (8, None))
        self.assertEqual([k for k in ModEdits(edits.folder).edits if k[1].startswith("ArmorDescriptor.")], [])

    def test_an_armour_part_is_changed_on_its_units_page(self):
        part = self.api.unit(f"{TANK_UNIT}:ArmorDescriptor", via=TANK_UNIT)
        self.assertEqual((part["editable"], part["why_not"]), (False, "armour_on_unit"))
        with self.assertRaises(StudioError):
            self.api.edit(f"{TANK_UNIT}:ArmorDescriptor", "BaseBlindage", 8, "own", TANK_UNIT)
        with self.assertRaisesRegex(StudioError, "armour level from the list"):
            self.api.set_armour(TANK_UNIT, 7)


if __name__ == "__main__":
    unittest.main()
