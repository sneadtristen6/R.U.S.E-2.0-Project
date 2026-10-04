"""Unit model packs written (rusemod.unitpacks): the name trie, mesh and skeleton packs, texture stand-in packs and
animation packs, each written back as read and with models copied in; and a unit's models given to another nation,
on made-up packs. tools/verify_unitpacks.py runs the same on every pack the game ships."""
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_empty_edat, make_ndf, val
from rusemod import Edat
from rusemod.build import build_pack, load_mod
from rusemod.spk import Spk
from rusemod.unitpacks import (COMMON, NAMES_HEAD, Buffer, MeshPack, PackError, Packs, Proxy, ProxyPack,
                               animation_name, archive_with, header_id, pack_paths, proxy_name, read_names,
                               write_names)

BONES = "$/M3D/System/VERTEXTYPE/TVertex__Position_3f__NormalIn01_4ubn__BlW_4ubn__BlIdx_4ub"
PLAIN = "$/M3D/System/VERTEXTYPE/TVertex__Position_3f__NormalIn01_4ubn"
UNITS = "ww2\\res3d\\units\\"
TANK = UNITS + "ger\\tank\\ger_panzerivlod0.ase2ndfbin"
TANK_DEAD = UNITS + "ger\\tank\\ger_panzeriv_destlod0.ase2ndfbin"
TANK_GUN = UNITS + "ger\\tank\\turret_idlelod0.ase2ndfbin"   # an animation only
SHERMAN = UNITS + "us\\tank\\us_shermanlod0.ase2ndfbin"
JEEP = UNITS + "common\\jeeplod0.ase2ndfbin"
TEX = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Units\\GER\\Tank\\TSCComb_CombinedDSCTexture01.png"
TEX_US = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Units\\US\\Tank\\TSCComb_CombinedDSCTexture01.png"
TEX_JEEP = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Units\\Common\\TSCComb_CombinedDSCTexture01.png"


# --- made-up packs ---
def ref(index, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))


def materials(textures) -> bytes:
    """A materials NDF as the game's: a root list of one TMeshMaterial per texture, each with a ParameterDico that
    refers to one shared float."""
    n = len(textures)
    strings = ["specularPower", "CombinedDSCTexture"] + [f"mat{k}" for k in range(n)] + list(textures)
    param = n + 1
    objects = [(0, [(0, val(0x11, struct.pack("<I", n) + b"".join(ref(k + 1, 1) for k in range(n))))])]
    for k in range(n):
        dico = val(0x12, struct.pack("<I", 1) + val(0x07, struct.pack("<I", 0)) + ref(param, 2))
        tex = val(0x12, struct.pack("<I", 1) + val(0x07, struct.pack("<I", 1))
                  + val(0x22, val(0x1C, struct.pack("<I", 2 + n + k)) + val(0x03, bytes(4))))
        objects.append((1, [(1, dico), (2, tex), (3, val(0x07, struct.pack("<I", 2 + k)))]))
    objects.append((2, [(4, val(0x05, struct.pack("<f", 32.0)))]))
    return make_ndf(objects, ["TEugBListPBaseClass", "TMeshMaterial", "TEugBFloat"],
                    [("Value", 0), ("ParameterDico", 1), ("Textures", 1), ("MaterialName", 1), ("Value", 2)],
                    strings=strings, topo=(0,))


def quad(x, bones=True) -> bytes:
    """Four stored vertices at x (positions, an up normal, and bone 0 when `bones`)."""
    pts = [(x, 0.0, 0.0), (x + 10, 0.0, 0.0), (x + 10, 10.0, 0.0), (x, 10.0, 0.0)]
    tail = struct.pack("<4B4B", 255, 0, 0, 0, 0, 0, 0, 0) if bones else b""
    return b"".join(struct.pack("<3f4B", *p, 128, 128, 255, 0) + tail for p in pts)


TRIANGLES = {6: (0, 1, 2, 0, 2, 3), 3: (0, 1, 2)}


def mesh_pack(models: dict, textures) -> MeshPack:
    """{name: (x, bones, material, 6 or 3 indices)} -> a pack, one draw call per model; models with the same
    triangles share their index buffer."""
    pack = MeshPack(formats=[BONES.encode().ljust(256, b"\0"), PLAIN.encode().ljust(256, b"\0")],
                    materials=materials(textures), material_count=len(textures))
    ibs = []
    for k, name in enumerate(sorted(models, key=lambda n: n.replace("\\", "\0"))):
        x, bones, mat, n = models[name]
        if n not in ibs:
            ibs.append(n)
            pack.ibs.append(Buffer(struct.pack(f"<{n}H", *TRIANGLES[n]), 2 * n, n, 1, 0))
        pack.vbs.append(Buffer(quad(x, bones), len(quad(x, bones)), 4, 0 if bones else 1, 0))
        pack.draws.append((k, mat, ibs.index(n), k, 0xFFFF, 0xCDCD))  # first field: its own mesh's number
        pack.meshes.append((k, 1))
        pack.items[name] = [struct.pack("<6fI", x, 0, 0, x + 10, 10, 0, 1), k, 0xCDCD]
    return pack


def skeleton_pack(models: dict) -> MeshPack:
    """{name: skeleton bytes} -> a skeleton pack (models with the same bytes share one)."""
    pack = MeshPack(formats=[], materials=materials([]), material_count=0)
    for name, blob in models.items():
        if blob not in pack.skeletons:
            pack.skeletons.append(blob)
        pack.items[name] = [bytes(28), 0xCDCD, pack.skeletons.index(blob)]
    return pack


def proxy_pack(names, picture=b"TGV:") -> ProxyPack:
    pack = ProxyPack()
    for k, name in enumerate(sorted(names, key=lambda n: n.replace("\\", "\0"))):
        key = hashlib.md5(name.encode()).digest()[:8]
        pack.proxies.append(Proxy(key, picture + name.encode()[-8:], struct.pack("<HHI", 0, 0, 0xAAAAAAAA),
                                  name.encode().ljust(256, b"\0")))
        pack.shared.append(k)
    return pack


def anim_pack(files) -> bytes:
    return archive_with(make_empty_edat(), files)


def zz_win(without=(), skeleton_of_tank=b"SKEL" * 4, stand_in=True):
    """A ZZ_Win.dat with Germany's, the US's and the common skirmish packs: Germany has the Panzer IV (its wreck
    shares its skeleton and texture), the US the Sherman (in both mesh packs), common the jeep."""
    ger_mesh = mesh_pack({TANK: (0.0, True, 0, 6), TANK_DEAD: (20.0, True, 0, 6)}, [TEX])
    us_mesh = mesh_pack({SHERMAN: (40.0, True, 0, 3)}, [TEX_US])
    common_mesh = mesh_pack({JEEP: (60.0, False, 0, 6)}, [TEX_JEEP])
    skel = {TANK: skeleton_of_tank, TANK_DEAD: skeleton_of_tank} if skeleton_of_tank else {}
    packs = {
        "gen_5\\pack\\gfxdescriptor\\meshskirmish_ger.spk": ger_mesh.to_bytes(),
        "gen_5\\pack\\gfxdescriptor\\meshskirmish_us.spk": us_mesh.to_bytes(),
        "gen_5\\pack\\gfxdescriptor\\meshskirmishwitboat_us.spk": us_mesh.to_bytes(),
        "gen_5\\pack\\gfxdescriptor\\meshskirmish_common.spk": common_mesh.to_bytes(),
        "gen_5\\pack\\gfxdescriptor\\skeleton_ger.spk": skeleton_pack(skel).to_bytes(),
        "gen_5\\pack\\gfxdescriptor\\skeleton_us.spk": skeleton_pack({SHERMAN: b"US__" * 2}).to_bytes(),
        "gen_5\\pack\\gfxdescriptor\\skeleton_common.spk": skeleton_pack({JEEP: b"JEEP"}).to_bytes(),
        "gentexproxy\\pack\\gfxdescriptor\\proxyskirmish_ger.ppk":
            proxy_pack([proxy_name(TEX)] if stand_in else []).to_bytes(),
        "gentexproxy\\pack\\gfxdescriptor\\proxyskirmish_us.ppk": proxy_pack([proxy_name(TEX_US)]).to_bytes(),
        "gentexproxy\\pack\\gfxdescriptor\\proxyskirmishwitboat_us.ppk": proxy_pack([proxy_name(TEX_US)]).to_bytes(),
        "gentexproxy\\pack\\gfxdescriptor\\proxyskirmish_common.ppk": proxy_pack([proxy_name(TEX_JEEP)]).to_bytes(),
        "genanim_15\\pack\\gfxdescriptor_ger.apk": anim_pack({animation_name(TANK_GUN): b"BAF-gun"}),
        "genanim_15\\pack\\gfxdescriptor_us.apk": anim_pack({}),
        "genanim_15\\pack\\gfxdescriptor_common.apk": anim_pack({}),
    }
    tree = {}
    for path, data in packs.items():
        if path not in without:
            folder, _, name = path.rpartition("\\")
            tree.setdefault(folder + "\\", []).append(("file", name, data))
    return Edat(make_edat([("dir", folder, files) for folder, files in tree.items()]))


# --- the trie ---
class Names(unittest.TestCase):
    def test_laid_out_as_the_game_s(self):
        # a folder holds what its names share; siblings split on their first character; nodes take even bytes
        out = write_names([("ac", b"\x02\x00"), ("ab", b"\x01\x00")])
        self.assertEqual(out, struct.pack("<II", 10, 0) + b"a\0"
                         + struct.pack("<II", 0, 12) + b"\x01\x00b\0" + struct.pack("<II", 0, 0) + b"\x02\x00c\0")
        self.assertEqual(read_names(out, 0, len(out), 2), [("ab", b"\x01\x00"), ("ac", b"\x02\x00")])

    def test_the_folder_separator_sorts_first(self):
        names = ["a\\us_10\\y", "a\\us_1\\x", "a\\us_1-x", "a\\us_1.x"]
        out = write_names([(n, b"") for n in names])
        self.assertEqual([n for n, _ in read_names(out, 0, len(out), 0)],
                         ["a\\us_1\\x", "a\\us_1-x", "a\\us_1.x", "a\\us_10\\y"])

    def test_what_a_trie_can_t_hold(self):
        with self.assertRaises(PackError):
            write_names([("ab", b""), ("ab", b"")])
        with self.assertRaises(PackError):
            write_names([("ab", b""), ("abc", b"")])


# --- mesh and skeleton packs ---
class Meshes(unittest.TestCase):
    def setUp(self):
        self.ger = mesh_pack({TANK: (0.0, True, 0, 6), TANK_DEAD: (20.0, True, 0, 6)}, [TEX])
        self.raw = self.ger.to_bytes()

    def test_written_back_as_read(self):
        self.assertEqual(MeshPack.read(self.raw).to_bytes(), self.raw)
        spk = Spk(self.raw)  # and the reader the Studio draws with reads it
        self.assertEqual(sorted(spk.items), sorted([TANK, TANK_DEAD]))
        (part,) = spk.model(TANK)
        self.assertEqual(part.indices, [0, 1, 2, 0, 2, 3])
        self.assertEqual(part.positions[:3], [0.0, 0.0, 0.0])
        self.assertEqual(spk.materials()[0]["textures"], {"CombinedDSCTexture": TEX})

    def test_the_layout(self):
        raw = mesh_pack({TANK: (0.0, True, 0, 6), SHERMAN: (40.0, True, 0, 3)}, [TEX]).to_bytes()
        sections = [struct.unpack_from("<III", raw, 0x34 + 12 * i) for i in range(8)]
        self.assertEqual(sections[0][0], 0xC4)
        for off, size, _count in sections:
            if size:
                self.assertEqual(off % 4, 0)
        # the 6-index triangle list is 12 bytes, the 3-index one 6: 0x7E up to the next multiple of 4 between them
        ib_data = struct.unpack_from("<I", raw, 0x94)[0]
        rows = [struct.unpack_from("<IIIHH", raw, sections[7][0] + 16 * i) for i in range(2)]
        self.assertEqual([r[:3] for r in rows], [(0, 12, 6), (12, 6, 3)])
        self.assertEqual(struct.unpack_from("<II", raw, 0x20), (0, ib_data))
        self.assertEqual(struct.unpack_from("<I", raw, 0x0C)[0], len(raw))
        self.assertEqual(struct.unpack_from("<I", raw, 0x30)[0], 2)
        self.assertEqual(raw[sections[0][0]:sections[0][0] + 10], NAMES_HEAD)
        names_end = sections[0][0] + sections[0][1]
        self.assertEqual(set(raw[names_end:sections[1][0]]), {0x7E} if names_end % 4 else set())

    def test_a_model_copied_in(self):
        us = mesh_pack({SHERMAN: (40.0, True, 0, 3)}, [TEX_US])
        before = Spk(us.to_bytes())
        us.add(self.ger, TANK)
        us.add(self.ger, TANK_DEAD)
        raw = us.to_bytes()
        self.assertEqual(MeshPack.read(raw).to_bytes(), raw)
        after, src = Spk(raw), Spk(self.raw)
        old = before.model(SHERMAN)[0]
        self.assertEqual(after.model(SHERMAN)[0].positions, old.positions)  # the old model reads the same
        self.assertEqual(after.materials()[after.model(SHERMAN)[0].material]["textures"], {"CombinedDSCTexture": TEX_US})
        for name in (TANK, TANK_DEAD):  # the copies read as in their own pack
            a, b = after.model(name)[0], src.model(name)[0]
            self.assertEqual((a.positions, a.indices, a.normals), (b.positions, b.indices, b.normals))
            self.assertEqual(after.materials()[a.material]["textures"], {"CombinedDSCTexture": TEX})
            self.assertEqual(after.items[name].box, src.items[name].box)
        # meshes in name order (ger before us), the draw calls after each other; the triangles, the format and the
        # material the two German models share are copied once
        pack = MeshPack.read(raw)
        self.assertEqual([pack.items[n][1] for n in (TANK_DEAD, TANK, SHERMAN)], [0, 1, 2])
        self.assertEqual(pack.meshes, [(0, 1), (1, 1), (2, 1)])
        # as in every shipped pack, each draw call's first field is its own mesh's number, the last 0xCDCD
        self.assertEqual([d[0] for d in pack.draws], [0, 1, 2])
        self.assertEqual({d[5] for d in pack.draws}, {0xCDCD})
        self.assertEqual((len(pack.ibs), len(pack.vbs), len(pack.formats), pack.material_count), (2, 3, 2, 2))
        with self.assertRaises(PackError):
            pack.add(self.ger, TANK)

    def test_bones_and_textures(self):
        plain = mesh_pack({JEEP: (0.0, False, 0, 6)}, [TEX_JEEP])
        self.assertTrue(self.ger.bones(TANK))
        self.assertFalse(plain.bones(JEEP))
        self.assertEqual(self.ger.textures(TANK), [TEX])

    def test_skeletons(self):
        ger = skeleton_pack({TANK: b"SKEL" * 4, TANK_DEAD: b"SKEL" * 4})
        raw = ger.to_bytes()
        self.assertEqual(MeshPack.read(raw).to_bytes(), raw)
        self.assertEqual(struct.unpack_from("<III", raw, 0xB0)[1:], (8, 1))  # one skeleton, shared
        us = skeleton_pack({SHERMAN: b"US__" * 2})
        us.add(MeshPack.read(raw), TANK)
        us.add(MeshPack.read(raw), TANK_DEAD)
        self.assertEqual(us.skeletons, [b"US__" * 2, b"SKEL" * 4])
        self.assertEqual({n: s for n, (_d, _m, s) in us.items.items()}, {SHERMAN: 0, TANK: 1, TANK_DEAD: 1})
        again = MeshPack.read(us.to_bytes())
        self.assertEqual(again.skeletons[again.items[TANK][2]], b"SKEL" * 4)

    def test_header_id_follows_the_size(self):  # the game drops a pack whose id isn't this MD5 (T32 run 1)
        pack = MeshPack.read(self.raw)
        pack.items[UNITS + "ger\\tank\\ger_panzeriv_talllod0.ase2ndfbin"] = list(pack.items[TANK])  # a new name
        grown = pack.to_bytes()
        self.assertGreater(len(grown), len(self.raw))
        for raw in (self.raw, grown):
            self.assertEqual(raw[0x10:0x20], hashlib.md5(raw[:0x10] + raw[0x20:0x30]).digest())
        self.assertNotEqual(grown[0x10:0x20], self.raw[0x10:0x20])
        self.assertEqual(header_id(grown), grown[0x10:0x20])

    def test_not_a_pack(self):
        with self.assertRaises(PackError):
            MeshPack.read(b"MESHPCPC" + struct.pack("<I", 3) + bytes(200))


# --- texture stand-ins ---
class StandIns(unittest.TestCase):
    def test_written_back_and_copied_in_name_order(self):
        names = [proxy_name(TEX_US), "gentexproxy\\ww2\\a.tgv"]
        us = proxy_pack(names)
        us.shared[1] = 0  # (a texture with the same picture as another: written once)
        us.proxies[1].data = us.proxies[0].data
        raw = us.to_bytes()
        self.assertEqual(ProxyPack.read(raw).to_bytes(), raw)
        self.assertEqual(struct.unpack_from("<5I", raw, 0x20)[1:], (48, 0x70, len(us.proxies[0].data), 2))
        ger = proxy_pack([proxy_name(TEX)])
        pack = ProxyPack.read(raw)
        pack.add(ger, proxy_name(TEX))
        self.assertEqual(pack.names(), ["gentexproxy\\ww2\\a.tgv", proxy_name(TEX), proxy_name(TEX_US)])
        again = ProxyPack.read(pack.to_bytes())
        self.assertEqual([p.data for p in again.proxies],
                         [us.proxies[0].data, ger.proxies[0].data, us.proxies[0].data])
        self.assertEqual(again.proxies[1].key, ger.proxies[0].key)
        with self.assertRaises(PackError):
            pack.add(ger, proxy_name(TEX))

    def test_names(self):
        self.assertEqual(proxy_name(TEX), "gentexproxy\\ww2\\res3d\\units\\ger\\tank\\tsccomb_combineddsctexture01.tgv")
        self.assertEqual(animation_name(TANK_GUN), "genanim_15\\" + TANK_GUN[:-len(".ase2ndfbin")] + ".baf")


# --- animation packs ---
class Animations(unittest.TestCase):
    def test_files_put_in_name_order(self):
        raw = make_edat([("dir", "genanim_15\\ww2\\", [("file", "b.baf", b"BB"), ("file", "d.baf", b"DDD")])])
        once = archive_with(raw, {})
        self.assertEqual(archive_with(once, {}), once)  # laid out as the game's: stays as it is
        out = archive_with(once, {"genanim_15\\ww2\\c.baf": b"C", "genanim_15\\a.baf": b"A"})
        arc = Edat(out)
        self.assertEqual([e.path for e in arc.entries],
                         ["genanim_15\\a.baf", "genanim_15\\ww2\\b.baf", "genanim_15\\ww2\\c.baf", "genanim_15\\ww2\\d.baf"])
        self.assertEqual([bytes(arc.read(e)) for e in arc.entries], [b"A", b"BB", b"C", b"DDD"])
        self.assertEqual(sorted(e.offset for e in arc.entries), [0, 1, 3, 4])
        with self.assertRaises(PackError):
            archive_with(out, {"genanim_15\\a.baf": b"again"})


# --- a unit's models given to a nation ---
class Giving(unittest.TestCase):
    def test_a_german_tank_for_the_us(self):
        packs = Packs(zz_win())
        given, why = packs.give(sorted([TANK, TANK_DEAD, TANK_GUN, JEEP]), "us", ["ger"])
        self.assertEqual(why, [])
        self.assertEqual(given.summary(), "2 meshes, 2 skeletons, 1 animation, 1 texture stand-in")
        self.assertEqual(given.sources, ["ger"])
        out = packs.output()
        self.assertEqual(sorted(out), sorted(p for kind in pack_paths("us").values() for p in kind))
        for path in pack_paths("us")["mesh"]:  # both US mesh packs: the Sherman as it was, the tank in
            spk = Spk(out[path])
            self.assertEqual(sorted(spk.items), sorted([SHERMAN, TANK, TANK_DEAD]))
            self.assertEqual(spk.model(TANK)[0].positions[:3], [0.0, 0.0, 0.0])
            self.assertEqual(out[path][0x10:0x20], header_id(out[path]))  # the id the game checks
        skel = MeshPack.read(out["gen_5\\pack\\gfxdescriptor\\skeleton_us.spk"])
        self.assertEqual(skel.skeletons[skel.items[TANK_DEAD][2]], b"SKEL" * 4)
        for path in pack_paths("us")["proxy"]:
            self.assertIn(proxy_name(TEX), ProxyPack.read(out[path]).names())
        anim = Edat(out["genanim_15\\pack\\gfxdescriptor_us.apk"])
        self.assertEqual(bytes(anim.read(anim.entry(animation_name(TANK_GUN)))), b"BAF-gun")
        # a second unit on the same models: nothing more to copy
        again, why = packs.give([TANK], "us", ["ger"])
        self.assertEqual((bool(again), why), (False, []))

    def test_what_every_match_has_or_the_nation_has_stays(self):
        packs = Packs(zz_win())
        given, why = packs.give([JEEP, SHERMAN], "us")
        self.assertEqual((bool(given), why, packs.output()), (False, [], {}))

    def test_spawned_units_go_into_the_common_packs(self):
        packs = Packs(zz_win())
        given, why = packs.give([TANK, SHERMAN], COMMON, ["ger"])
        self.assertEqual((why, given.sources), ([], ["ger", "us"]))
        out = packs.output()
        self.assertEqual(sorted(Spk(out["gen_5\\pack\\gfxdescriptor\\meshskirmish_common.spk"]).items),
                         sorted([JEEP, SHERMAN, TANK]))

    def test_what_can_t_be_copied(self):
        packs = Packs(zz_win(skeleton_of_tank=None))
        given, why = packs.give([TANK], "us", ["ger"])
        self.assertEqual(why, [f"no skeleton pack has the skeleton of {TANK}, which its mesh needs"])
        self.assertEqual((bool(given), packs.output()), (False, {}))
        packs = Packs(zz_win(stand_in=False))
        self.assertEqual(packs.give([TANK], "us", ["ger"])[1],
                         [f"no texture stand-in pack has {proxy_name(TEX)}, a texture of {TANK}"])
        packs = Packs(zz_win(without=["gen_5\\pack\\gfxdescriptor\\skeleton_us.spk"]))
        self.assertEqual(packs.give([TANK], "us", ["ger"])[1],
                         [f"ZZ_Win.dat has no skeleton_us.spk to copy {TANK} into"])


# --- the build ---
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
    """The build with FORCE_LOAD off (the old way, kept): models copied into the unit's own nation's packs."""

    def setUp(self):
        import rusemod.build as b
        self.addCleanup(setattr, b, "FORCE_LOAD", b.FORCE_LOAD)
        b.FORCE_LOAD = False

    def build(self, text, zz=None):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d, "moved.rndf")
            mod.write_text(text, encoding="utf-8")
            return build_pack(Edat(UNIT_PACK), [load_mod(mod)], text_arc=zz or zz_win())

    def test_a_german_tank_for_the_us(self):
        result = self.build("export Panzer_US is clone $/Panzer ( Nationalite = 0 )\n")
        self.assertEqual(result.errors, [])
        self.assertIn("its models go into US's skirmish packs too (1 mesh, 1 skeleton, 1 texture stand-in copied in "
                      "from Germany's packs), so it loads with US's own units",
                      "\n".join(f.message for f in result.findings))
        self.assertEqual(sorted(result.model_changed), sorted(p for k in ("mesh", "skeleton", "proxy")
                                                              for p in pack_paths("us")[k]))
        self.assertIn(TANK, Spk(result.model_changed["gen_5\\pack\\gfxdescriptor\\meshskirmish_us.spk"]).items)

    def test_refused_with_the_reason(self):
        result = self.build("patch $/Panzer ( Nationalite = 0 )\n", zz_win(skeleton_of_tank=None))
        self.assertEqual(len(result.errors), 1)
        self.assertIn(f"it can't be copied into US's skirmish packs: no skeleton pack has the skeleton of {TANK}",
                      result.errors[0].message)
        self.assertEqual((result.model_changed, result.changed), ({}, {}))

    def test_a_copy_that_stays_home_copies_nothing(self):
        result = self.build("export Panzer_2 is clone $/Panzer ( DescriptorId = 3 )\n")
        self.assertEqual((result.errors, result.model_changed), ([], {}))


if __name__ == "__main__":
    unittest.main()
