"""A unit's models in the Studio (StudioApi._unit_models; the owner, 2026-10-11: "there's no 3D models for infantry"):
a vehicle's from its GfxDescriptor as before, infantry's soldiers from its other graphics when GfxDescriptor reaches
no model, with a model part another infantry unit shares followed and the wreck the game reuses for fallen soldiers
left out. And a new unit's own copy of the model it copies (rusemod.unitmodel.write_unit_copy; the owner: "duplicate
that part"): the same mesh and bones, its own textures, painted or not, so a repaint changes that unit only."""
import struct
import tempfile
import unittest
from pathlib import Path

from test_unitmodel import MESHES, PROXIES, SKELETONS, TANK, TEX, UNIT_PACK, zz_win
from rusemod import Edat, tgu1, unitmodel
from rusemod.build import build_pack, load_mod
from rusemod.dxt import decode_rgba, png_bytes
from rusemod.model import load
from rusemod.spk import Spk
from rusemod.tmst import Tgv
from rusemod.unitpacks import MeshPack, Proxy, ProxyPack, proxy_name
from ruse_studio.api import StudioApi

E = "$/GFX/Everything/"


class FakeIndex:
    """The game index's `uses` (prop, kind, what) for a few made-up objects."""

    def __init__(self, uses: dict):
        self._uses = uses

    def uses(self, address):
        return self._uses.get(address, [])


TANK_UNIT = E + "Descriptor_Unit_Tank"
SOLDIERS = E + "Descriptor_Unit_Soldat_Leger"
HEAVY = E + "Descriptor_Unit_Soldat_Lourd"
INDEX = FakeIndex({
    TANK_UNIT: [("GfxDescriptor", "object", TANK_UNIT + ":GfxDescriptor"),
           ("GfxDescriptorCadavre", "object", TANK_UNIT + ":GfxDescriptorCadavre")],
    TANK_UNIT + ":GfxDescriptor": [("MeshDescriptor", "object", TANK_UNIT + ":GfxDescriptor.MeshDescriptor"),
                              ("Smoke", "object", E + "Shared:Smoke")],
    TANK_UNIT + ":GfxDescriptor.MeshDescriptor": [("FileName", "file", "ww2/res3d/units/tank/tanklod0.ase2ndfbin")],
    E + "Shared:Smoke": [("FileName", "file", "ww2/res3d/nonclasse/smokelod0.ase2ndfbin")],
    TANK_UNIT + ":GfxDescriptorCadavre": [("MeshDescriptor", "object", TANK_UNIT + ":GfxDescriptorCadavre.MeshDescriptor")],
    TANK_UNIT + ":GfxDescriptorCadavre.MeshDescriptor": [("FileName", "file", "ww2/res3d/units/tank/tank_destlod0.ase2ndfbin")],
    SOLDIERS: [("GfxDescriptor", "object", SOLDIERS + ":GfxDescriptor"),
               ("GfxDescriptorBazooka", "object", SOLDIERS + ":GfxDescriptorBazooka"),
               ("GfxDescriptorIconeCadavre", "object", SOLDIERS + ":GfxDescriptorIconeCadavre"),
               ("GfxDescriptorCadavre", "object", SOLDIERS + ":GfxDescriptorCadavre")],
    SOLDIERS + ":GfxDescriptor": [("MeshDescriptor", "object", E + "Shared:Smoke")],
    SOLDIERS + ":GfxDescriptorBazooka": [("MeshDescriptor", "object", SOLDIERS + ":GfxDescriptorBazooka.MeshDescriptor")],
    SOLDIERS + ":GfxDescriptorBazooka.MeshDescriptor": [("FileName", "file", "ww2/res3d/units/us/infanterie/us_soldier_bazooka_modellod0.ase2ndfbin")],
    SOLDIERS + ":GfxDescriptorIconeCadavre": [("MeshDescriptor", "object", SOLDIERS + ":GfxDescriptorIconeCadavre.MeshDescriptor")],
    SOLDIERS + ":GfxDescriptorIconeCadavre.MeshDescriptor": [("FileName", "file", "ww2/res3d/units/us/infanterie/us_soldier_modellod0.ase2ndfbin")],
    SOLDIERS + ":GfxDescriptorCadavre": [("MeshDescriptor", "object", E + "Wreck:MeshDescriptor")],
    E + "Wreck:MeshDescriptor": [("FileName", "file", "ww2/res3d/units/us/char/us_m36_jackson_destlod0.ase2ndfbin")],
    HEAVY: [("GfxDescriptor", "object", HEAVY + ":GfxDescriptor"),
            ("GfxDescriptorIconeCadavre", "object", HEAVY + ":GfxDescriptorIconeCadavre")],
    HEAVY + ":GfxDescriptorIconeCadavre": [("MeshDescriptor", "object", SOLDIERS + ":GfxDescriptorIconeCadavre.MeshDescriptor")],
})

# the King Tiger (Panzer_VI_B_Tigre_II): its parts' meshes are another unit's objects (KingTigerAS's); a gun: its own
# mesh and a shared crew; an atomic gun: only shared meshes (the Long Tom's and the crew); a squad whose graphics reach
# only a building's effect mesh (Soldat_US_Para_SOLO)
KING, GUN, ATOMIC, SOLO = (E + "Descriptor_Unit_" + n for n in ("Panzer_VI_B_Tigre_II", "Gun", "Canon_atomique_US",
                                                              "Soldat_US_Para_SOLO"))
CREW = E + "Descriptor_Unit_Crew:GfxDescriptor.MeshDescriptor"
CREW_FILE = "ww2/res3d/units/us/infanterie/us_servant_modellod0.ase2ndfbin"
SHARED = FakeIndex({
    KING: [("GfxDescriptor", "object", KING + ":GfxDescriptor"),
           ("GfxDescriptorIcone", "object", E + "Descriptor_Unit_KingTigerAS:GfxDescriptorIcone")],
    KING + ":GfxDescriptor": [("SousElements[0].v", "object", KING + ":GfxDescriptor.SousElements[0].v")],
    KING + ":GfxDescriptor.SousElements[0].v": [
        ("MeshDescriptor", "object", E + "Descriptor_Unit_KingTigerAS:GfxDescriptor.MeshDescriptor")],
    E + "Descriptor_Unit_KingTigerAS:GfxDescriptor.MeshDescriptor": [
        ("FileName", "file", "ww2/res3d/units/ger/char/ger_tigre_ii/ger_tigre_iilod0.ase2ndfbin")],
    GUN: [("GfxDescriptor", "object", GUN + ":GfxDescriptor")],
    GUN + ":GfxDescriptor": [("MeshDescriptor", "object", GUN + ":GfxDescriptor.MeshDescriptor"),
                             ("SousElements[0].v", "object", GUN + ":GfxDescriptor.SousElements[0].v")],
    GUN + ":GfxDescriptor.MeshDescriptor": [("FileName", "file", "ww2/res3d/units/us/canon/gunlod0.ase2ndfbin")],
    GUN + ":GfxDescriptor.SousElements[0].v": [("MeshDescriptor", "object", CREW)],
    CREW: [("FileName", "file", CREW_FILE)],
    ATOMIC: [("GfxDescriptor", "object", ATOMIC + ":GfxDescriptor")],
    ATOMIC + ":GfxDescriptor": [("SousElements[0].v", "object", ATOMIC + ":GfxDescriptor.SousElements[0].v"),
                                ("SousElements[1].v", "object", ATOMIC + ":GfxDescriptor.SousElements[1].v")],
    ATOMIC + ":GfxDescriptor.SousElements[0].v": [
        ("MeshDescriptor", "object", E + "Descriptor_Unit_Long_Tom:GfxDescriptor.MeshDescriptor")],
    E + "Descriptor_Unit_Long_Tom:GfxDescriptor.MeshDescriptor": [
        ("FileName", "file", "ww2/res3d/units/us/canon/us155mm_long_tomlod0.ase2ndfbin")],
    ATOMIC + ":GfxDescriptor.SousElements[1].v": [("MeshDescriptor", "object", CREW)],
    SOLO: [("GfxDescriptor", "object", SOLO + ":GfxDescriptor")],
    SOLO + ":GfxDescriptor": [("SousElements[0].v", "object", SOLO + ":GfxDescriptor.SousElements[0].v")],
    SOLO + ":GfxDescriptor.SousElements[0].v": [("MeshDescriptor", "object", E + "Fx:MeshDescriptor")],
    E + "Fx:MeshDescriptor": [("FileName", "file", "ww2/res3d/nonclasse/fxbatimentlod0.ase2ndfbin")],
})


class Models(unittest.TestCase):
    def test_a_vehicle_keeps_its_own(self):
        self.assertEqual(StudioApi._unit_models(INDEX, TANK_UNIT), ["ww2\\res3d\\units\\tank\\tanklod0.ase2ndfbin"])

    def test_infantry_shows_its_soldiers(self):
        self.assertEqual(StudioApi._unit_models(INDEX, SOLDIERS),
                         ["ww2\\res3d\\units\\us\\infanterie\\us_soldier_bazooka_modellod0.ase2ndfbin",
                          "ww2\\res3d\\units\\us\\infanterie\\us_soldier_modellod0.ase2ndfbin"])

    def test_a_soldier_model_part_shared_with_other_infantry(self):
        self.assertEqual(StudioApi._unit_models(INDEX, HEAVY),
                         ["ww2\\res3d\\units\\us\\infanterie\\us_soldier_modellod0.ase2ndfbin"])

    # a modder's report, 2026-10-17: "the window for changing the model never opens" (no models: no model box). 17 of
    # the game's units drew only other units' meshes; those are followed when nothing of the unit's own is found
    def test_parts_drawn_with_another_units_mesh(self):
        self.assertEqual(StudioApi._unit_models(SHARED, KING),
                         ["ww2\\res3d\\units\\ger\\char\\ger_tigre_ii\\ger_tigre_iilod0.ase2ndfbin"])

    def test_a_gun_with_its_own_mesh_keeps_the_crew_out(self):
        # (the crew's uniform in every gun's paint: a gun's repaint would recolour every crew)
        self.assertEqual(StudioApi._unit_models(SHARED, GUN), ["ww2\\res3d\\units\\us\\canon\\gunlod0.ase2ndfbin"])

    def test_only_shared_meshes_the_gun_not_its_crew(self):
        self.assertEqual(StudioApi._unit_models(SHARED, ATOMIC),
                         ["ww2\\res3d\\units\\us\\canon\\us155mm_long_tomlod0.ase2ndfbin"])

    def test_an_effect_mesh_is_no_model(self):
        self.assertEqual(StudioApi._unit_models(SHARED, SOLO), [])

    def test_units_with_no_model_are_not_a_new_unit_s_start(self):
        """The owner, 2026-10-17: "if those units don't have models, just don't include them": a unit whose models
        aren't in the mesh packs (the SOLO gun names a file the game hasn't got) or that has none (the SOLO
        paratroopers) is left out of New unit; a building isn't (its look is a layout of pieces, not a model)."""
        from unittest import mock
        from rusemod import models

        class Library:  # the mesh packs: the King Tiger's model is there, the gun's file isn't
            def __init__(self, game):
                self.where = {"tigre_ii": None}   # some mesh pack was read (with none, nothing is left out)

            def find(self, name, lighter=False):
                return name if "tigre_ii" in name else None

            def close(self):
                pass

        index = FakeIndex({**SHARED._uses, GUN + ":GfxDescriptor.MeshDescriptor": [
            ("FileName", "file", "ww2/res3d/units/us/canon/gun/canon_fire_reloadlod0.ase2ndfbin")]})
        index.path = "index.sqlite"
        api = object.__new__(StudioApi)
        api._no_model, api._units = None, [{"address": a, "class": c} for a, c in (
            (KING, "TUniteAuSolDescriptor"), (GUN, "TUniteAuSolDescriptor"), (SOLO, "TInfanterieDescriptor"),
            (E + "Descriptor_Building_Depot", "TBatimentDescriptor"))]
        with mock.patch.object(StudioApi, "_game", return_value=Path("game")), \
                mock.patch.object(models, "Library", Library):
            self.assertEqual(api._modelless(index), {GUN, SOLO})
            self.assertIs(api._modelless(index), api._modelless(index))  # worked out once


# --- a new unit's own copy of its model ---
MEMBER = unitmodel.texture_member(TEX)             # the Panzer's texture in ZZ_Win.dat
COPY_TEX = "ZZ:\\GenTexGroup\\WW2\\Res3D\\Units\\GER\\Tank\\TSCComb_Panzer_Red_CombinedDSCTexture01.png"
COPY_MEMBER = unitmodel.texture_member(COPY_TEX)
NEW = "ww2\\res3d\\units\\ger\\tank\\panzer_redlod0.ase2ndfbin"
BLUE, RED = (30, 60, 200), (200, 30, 30)


def zz_with_texture() -> Edat:
    """The made-up game's ZZ_Win.dat with the Panzer's texture (8 x 8 blue) and a stand-in of it that's a picture."""
    px = bytes(BLUE + (255,)) * 64
    standin = ProxyPack([Proxy(b"K" * 8, unitmodel.new_standin(px, 8, 8), struct.pack("<HHI", 0, 0, 0xAAAAAAAA),
                               proxy_name(TEX).encode().ljust(256, b"\0"))], [0])
    zz = zz_win()
    return Edat(zz.to_bytes(replace={PROXIES: standin.to_bytes()}, add={MEMBER: unitmodel.new_texture(px, 8, 8)}))


def top_colour(texture: bytes) -> tuple:
    g = Tgv(texture)
    return tuple(decode_rgba(tgu1.decode(g.payload(len(g.mips) - 1)), g.width, g.height, g.format)[:3])


class Copy(unittest.TestCase):
    def setUp(self):
        self.zz = zz_with_texture()

    def test_the_same_model_with_textures_of_its_own(self):
        w = unitmodel.write_unit_copy(self.zz, TANK, "Panzer_Red")
        self.assertEqual(w.model, NEW)
        self.assertEqual(sorted(w.changed), sorted([MESHES, SKELETONS, PROXIES]))
        spk, old = Spk(w.changed[MESHES]), Spk(bytes(self.zz.read(self.zz.entry(MESHES))))
        self.assertEqual(set(spk.items), {TANK, NEW})
        mats = spk.materials()
        for name in (TANK, NEW):
            first, count = spk.meshes[spk.items[name].mesh]
            self.assertEqual(count, 1)
            part = spk.part(first)
            ofirst, _ = old.meshes[old.items[TANK].mesh]
            self.assertEqual(part.positions, old.part(ofirst).positions)       # the very same mesh
            self.assertEqual(list(mats[part.material]["textures"].values()), [TEX if name == TANK else COPY_TEX])
            self.assertEqual(mats[part.material]["skinning"], [0, 1])         # on the same bones
        pack = MeshPack.read(w.changed[MESHES])
        self.assertEqual((len(pack.ibs), len(pack.vbs)), (1, 1))                # its buffers shared, not copied
        skel = MeshPack.read(w.changed[SKELETONS])
        self.assertEqual(skel.items[NEW][2], skel.items[TANK][2])
        self.assertEqual(list(w.added), [COPY_MEMBER])
        self.assertEqual(w.added[COPY_MEMBER], bytes(self.zz.read(self.zz.entry(MEMBER))))  # unpainted: the same
        proxies = ProxyPack.read(w.changed[PROXIES])
        names = proxies.names()
        self.assertIn(unitmodel.standin_member(COPY_MEMBER), names)
        new_stand = proxies.proxies[names.index(unitmodel.standin_member(COPY_MEMBER))]
        self.assertEqual(new_stand.key, unitmodel.standin_key(unitmodel.standin_member(COPY_MEMBER)))
        self.assertEqual(new_stand.data, proxies.proxies[names.index(proxy_name(TEX))].data)
        self.assertEqual(w.report["painted"], [])

    def test_painted_the_copy_only(self):
        with tempfile.TemporaryDirectory() as d:
            red = Path(d, "red.png")
            red.write_bytes(png_bytes(bytes(RED + (255,)) * 64, 8, 8, channels=4))
            w = unitmodel.write_unit_copy(self.zz, TANK, "Panzer_Red", {MEMBER: (red, None)})
        self.assertLessEqual(max(abs(a - b) for a, b in zip(top_colour(w.added[COPY_MEMBER]), RED)), 8)
        self.assertNotIn(MEMBER, w.added)                                        # the game's texture as it was
        self.assertLessEqual(max(abs(a - b) for a, b in zip(top_colour(bytes(self.zz.read(self.zz.entry(MEMBER)))),
                                                              BLUE)), 8)
        self.assertEqual(w.report["painted"], [COPY_MEMBER])
        proxies = ProxyPack.read(w.changed[PROXIES])
        names = proxies.names()
        self.assertNotEqual(proxies.proxies[names.index(unitmodel.standin_member(COPY_MEMBER))].data,
                            proxies.proxies[names.index(proxy_name(TEX))].data)

    def test_refused(self):
        with self.assertRaisesRegex(unitmodel.UnitModelError, "no mesh pack holds"):
            unitmodel.write_unit_copy(self.zz, "ww2\\nothing\\nonelod0.ase2ndfbin", "x")
        w = unitmodel.write_unit_copy(self.zz, TANK, "Panzer_Red")
        with self.assertRaisesRegex(unitmodel.UnitModelError, "already have a model"):
            unitmodel.write_unit_copy(Edat(self.zz.to_bytes(replace=w.changed)), TANK, "Panzer_Red")

    def test_copy_name_keeps_the_texture_group(self):
        self.assertEqual(unitmodel.copy_name("ZZ:\\A\\B\\TSCCombCS_CombinedDSCTexture01.png", "Sherman_Red"),
                         "ZZ:\\A\\B\\TSCCombCS_Sherman_Red_CombinedDSCTexture01.png")

    def test_the_copies_names(self):
        self.assertEqual(unitmodel.copy_model_name("DataDir:\\WW2\\Inf\\US_Ranger_modellod0.Ase2NdfBin", "Rangers"),
                         "WW2\\Inf\\Rangerslod0.Ase2ndfbin")
        self.assertEqual(unitmodel.copy_model_name("WW2\\Inf\\US_Ranger_modellod0.Ase2NdfBin", "Rangers", True),
                         "WW2\\Inf\\Rangers_US_Ranger_modellod0.Ase2ndfbin")
        self.assertEqual(unitmodel.model_key("DataDir:/WW2/Inf/X.Ase2NdfBin"), "ww2\\inf\\x.ase2ndfbin")


SECOND = "ww2\\res3d\\units\\ger\\tank\\ger_panzeriv_bazookalod0.ase2ndfbin"


def zz_with_two_models() -> Edat:
    """zz_with_texture with a second model drawn as the Panzer is, with its materials, so its texture too (as a
    squad's soldier and its bazooka man share their picture)."""
    zz = zz_with_texture()
    changed = {}
    for path in (MESHES, SKELETONS):
        raw = bytes(zz.read(zz.entry(path)))
        pack, holder = MeshPack.read(raw), MeshPack.read(raw)
        holder.items[SECOND] = list(holder.items[TANK])
        pack.add(holder, SECOND)
        changed[path] = pack.to_bytes()
    return Edat(zz.to_bytes(replace=changed))


class SquadCopy(unittest.TestCase):
    """A squad's custom uniform (the owner, 2026-10-11, T48: one US squad repainted turned every US soldier, gun crew
    and vehicle crew blue): copies of each of its soldier models, sharing one copied texture, and only its own model
    parts pointing at them (a part other units link to as well is copied into the squad first)."""

    def test_several_models_one_texture(self):
        zz = zz_with_two_models()
        copies = {m: unitmodel.copy_model_name(m, "Squad", True) for m in (TANK, SECOND)}
        w = unitmodel.write_unit_copy(zz, copies, "Squad")
        squad_tex = unitmodel.texture_member(TEX.replace("TSCComb_", "TSCComb_Squad_"))
        self.assertEqual(list(w.added), [squad_tex])                       # one picture for the squad's soldiers
        spk = Spk(w.changed[MESHES])
        mats = spk.materials()
        for game, new in copies.items():
            new = unitmodel.model_key(new)
            self.assertIn(new, spk.items)
            first, _count = spk.meshes[spk.items[new].mesh]
            self.assertEqual(unitmodel.texture_member(list(mats[spk.part(first).material]["textures"].values())[0]),
                             squad_tex)
            gfirst, _ = spk.meshes[spk.items[game].mesh]
            self.assertEqual(list(mats[spk.part(gfirst).material]["textures"].values()), [TEX])  # the game's as it was
        skel = MeshPack.read(w.changed[SKELETONS])
        self.assertTrue(all(unitmodel.model_key(n) in skel.items for n in copies.values()))
        self.assertEqual(sorted(w.report["models"]), sorted(copies))

    def test_only_the_squad_s_parts_point_at_the_copies(self):
        from types import SimpleNamespace
        from rusemod.build import _point_at_copies
        from rusemod.patch import Game, Inline, Obj, Ref, Text, lazy_copy
        soldier = "WW2\\Inf\\US_Soldier_modellod0.Ase2NdfBin"
        mesh = Obj("TResourceMultiMaterialMesh", {"FileName": Text("path", soldier)}, origin=("f", 1))
        icon = Obj("TGfxDescriptorPileJeton", {"PawnDescriptor": Inline(Obj("TPawnDescriptor", {
            "PawnDrawer": Ref(E + "DefaultPawnDrawer"),
            "DescriptorFigurine": Inline(Obj("TGfxDescriptorBiped", {"MeshDescriptor": Ref("f#1")}, origin=("f", 4))),
        }, origin=("f", 5)))}, origin=("f", 2))
        squad = Obj("TInfanterieDescriptor", {
            "GfxDescriptorIconeCadavre": Inline(Obj("TGfxDescriptorBiped", {"MeshDescriptor": Ref("f#1")},
                                                    origin=("f", 6))),
            "GfxDescriptorIcone": Ref("f#2"), "TransportPourMorphe": Ref(E + "Truck")}, origin=("f", 3))
        other = Obj("TInfanterieDescriptor", {"GfxDescriptorIcone": Ref("f#2"), "GfxDescriptorFusilier": Inline(
            Obj("TGfxDescriptorBiped", {"MeshDescriptor": Ref("f#1")}, origin=("f", 8)))}, origin=("f", 7))
        drawer = Obj("TPawnDrawer", {}, origin=("f", 9))
        base = Game({"f#1": mesh, "f#2": icon, E + "Squad": squad, E + "Other": other, E + "DefaultPawnDrawer": drawer})
        run = SimpleNamespace(game=lazy_copy(base))
        new = "WW2\\Inf\\Squad_US_Soldier_modellod0.Ase2ndfbin"
        self.assertEqual(_point_at_copies(run, E + "Squad", {unitmodel.model_key(soldier): new}), 2)
        got = run.game.objects[E + "Squad"]
        self.assertEqual(got.props["GfxDescriptorIconeCadavre"].obj.props["MeshDescriptor"].obj.props["FileName"],
                         Text("path", new))
        fig = got.props["GfxDescriptorIcone"].obj.props["PawnDescriptor"].obj.props["DescriptorFigurine"].obj
        self.assertEqual(fig.props["MeshDescriptor"].obj.props["FileName"], Text("path", new))  # its token's figure
        self.assertEqual(got.props["TransportPourMorphe"], Ref(E + "Truck"))
        self.assertEqual(run.game.objects[E + "Other"], other)                   # the other squad: the game's
        self.assertEqual(mesh.props["FileName"], Text("path", soldier))           # the shared parts as they were
        self.assertIs(base.objects[E + "Squad"], squad)
        self.assertEqual(squad.props["GfxDescriptorIcone"], Ref("f#2"))
        self.assertEqual(_point_at_copies(run, E + "Other", {"ww2\\inf\\nothinglod0.ase2ndfbin": new}), 0)


class CopyInTheBuild(unittest.TestCase):
    def build(self, copy=True, glb=False, paint=False):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d, "mod")
            (mod / "src").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "m"\nname = "M"\nversion = "0.1.0"\n', encoding="utf-8")
            (mod / "src" / "units.rndf").write_text("export Panzer_Red is clone $/Panzer ( DescriptorId = 3 )\n",
                                                    encoding="utf-8")
            models = mod / "files" / "models"
            models.mkdir(parents=True)
            if copy:
                (models / "Panzer_Red.copy.toml").write_text(copy if isinstance(copy, str) else
                                                             'of = ["WW2\\\\Res3D\\\\Units\\\\GER\\\\Tank\\\\'
                                                             'GER_PanzerIVlod0.Ase2NdfBin"]\n', encoding="utf-8")
            if paint:
                to = models / "Panzer_Red" / (MEMBER.replace("\\", "/") + ".png")
                to.parent.mkdir(parents=True)
                to.write_bytes(png_bytes(bytes(RED + (255,)) * 64, 8, 8, channels=4))
            if glb:
                (models / "Panzer_Red.glb").write_bytes(b"glTF")
            info = load_mod(mod)
            return info, build_pack(Edat(UNIT_PACK), [info], text_arc=zz_with_texture())

    def test_the_copy_names_its_model(self):
        for copy in (True, "# a first copy's file, naming no model\n"):  # (no `of`: the one its GfxDescriptor draws)
            info, result = self.build(copy=copy, paint=True)
            self.assertEqual(list(info[0].model_copies), ["Panzer_Red"])
            self.assertEqual(result.errors, [])
            copies, paint, mod_id = result.own_copies["Panzer_Red"]
            self.assertEqual((copies, list(paint), mod_id), (
                {TANK: "WW2\\Res3D\\Units\\GER\\Tank\\Panzer_Redlod0.Ase2ndfbin"}, [MEMBER], "m"))
            game, _files = load(result.changed)
            unit = game.objects[next(k for k in game.objects if k.rsplit("/", 1)[-1] == "Panzer_Red")]
            self.assertEqual(unit.props["GfxDescriptor"].obj.props["MeshDescriptor"].obj.props["FileName"].value,
                             "WW2\\Res3D\\Units\\GER\\Tank\\Panzer_Redlod0.Ase2ndfbin")

    def test_a_unit_can_t_have_both(self):
        _info, result = self.build(glb=True)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("has an imported model too", result.errors[0].message)

    def test_a_model_it_doesn_t_draw(self):
        _info, result = self.build(copy='of = ["WW2\\\\Res3D\\\\Other\\\\Nonelod0.Ase2NdfBin"]\n')
        self.assertEqual(len(result.errors), 1)
        self.assertIn("draws no ww2\\res3d\\other\\nonelod0.ase2ndfbin", result.errors[0].message)

    def test_a_file_that_can_t_be_read(self):
        from rusemod.build import BuildError
        with self.assertRaisesRegex(BuildError, "can't be read"):
            self.build(copy="of = [\n")


class StudioCopy(unittest.TestCase):
    """The Studio's Give it its own copy of the model, and its paint kept in the copy's folder (files/models/<name>/)
    instead of files/replace, with the game's models stood in for."""
    TEX = "gen\\ww2\\x\\a01.tgv"
    NEW = "$/GFX/Everything/Descriptor_Unit_R2_Red"

    def setUp(self):
        from ruse_studio.edits import NewUnit
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "R.U.S.E" / "Data" / "PC" / "190852").mkdir(parents=True)
        self.mod = root / "mod"
        self.mod.mkdir()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._look_models = lambda address: (["ww2\\x\\tanklod0.ase2ndfbin"], [self.TEX])
        self.api._mod_dir = lambda kind="mod": self.mod
        self.api._copy_models = lambda address: ["ww2\\x\\tanklod0.ase2ndfbin"]
        self.api._soldiers = lambda address: "Soldat" in address
        unit = NewUnit(self.NEW, "$/GFX/Everything/Descriptor_Unit_Test", "Red")
        new = self.NEW

        class Edits:
            def new_unit_of(self, a):
                return unit if a.split(":")[0] == new else None
        self.api._edits = lambda: Edits()

    def test_give_it_a_copy_and_take_it_back(self):
        from ruse_studio.api import StudioError
        self.assertFalse(self.api.look(self.NEW)["own_copy"])
        res = self.api.model_copy(self.NEW)
        marker = self.mod / "files" / "models" / "Descriptor_Unit_R2_Red.copy.toml"
        self.assertTrue(marker.is_file())
        self.assertIn('of = ["ww2\\\\x\\\\tanklod0.ase2ndfbin"]', marker.read_text(encoding="utf-8"))
        self.assertTrue(res["own_copy"])
        self.assertEqual(unitmodel.mod_copies(self.mod), {"Descriptor_Unit_R2_Red": (["ww2\\x\\tanklod0.ase2ndfbin"],
                                                                                    {})})
        # its paint: in the copy's folder, never files/replace (the game's texture, every unit drawn with it)
        folder = self.mod / "files" / "models" / "Descriptor_Unit_R2_Red"
        self.assertEqual(self.api._paint_root(self.NEW), folder)
        pic = folder / "gen" / "ww2" / "x" / "a01.tgv.png"
        pic.parent.mkdir(parents=True)
        pic.write_bytes(png_bytes(bytes((200, 30, 30, 255)), 1, 1, channels=4))
        self.assertEqual(self.api.look(self.NEW)["painted"], [self.TEX])
        self.assertEqual(self.api.look("$/GFX/Everything/Descriptor_Unit_Test")["painted"], [])
        res = self.api.model_copy_remove(self.NEW)
        self.assertFalse(res["own_copy"] or marker.exists())
        self.assertTrue(pic.is_file())  # its paint stays, for a copy made again
        self.assertEqual(self.api.look(self.NEW)["painted"], [])
        with self.assertRaisesRegex(StudioError, "Only a unit"):
            self.api.model_copy("$/GFX/Everything/Descriptor_Unit_Test:GfxDescriptor")

    def test_a_game_squad_s_custom_uniform(self):
        from ruse_studio.api import StudioError
        squad = "$/GFX/Everything/Descriptor_Unit_Soldat_US_Lourd"
        self.api._copy_models = lambda address: ["ww2\\inf\\us_ranger_modellod0.ase2ndfbin",
                                                 "ww2\\inf\\us_ranger_bazooka_modellod0.ase2ndfbin"]
        info = self.api.look(squad)
        self.assertTrue(info["soldiers"])
        self.assertFalse(info["own_copy"])
        with self.assertRaisesRegex(StudioError, "Pick Custom uniform first"):  # the default uniform: not repainted
            self.api._custom_uniform_first(squad)
        res = self.api.model_copy(squad)
        self.assertIn("uniform of its own", res["message"])
        self.assertTrue(res["own_copy"])
        self.assertEqual(unitmodel.mod_copies(self.mod)["Descriptor_Unit_Soldat_US_Lourd"][0],
                         ["ww2\\inf\\us_ranger_modellod0.ase2ndfbin", "ww2\\inf\\us_ranger_bazooka_modellod0.ase2ndfbin"])
        self.assertEqual(self.api._paint_root(squad), self.mod / "files" / "models" / "Descriptor_Unit_Soldat_US_Lourd")
        self.api._custom_uniform_first(squad)  # (now it's its own: painted here)
        self.assertIn("default uniform again", self.api.model_copy_remove(squad)["message"])

    def test_what_can_t_get_a_copy(self):
        from ruse_studio.api import StudioError
        self.api._copy_models = lambda address: []
        with self.assertRaisesRegex(StudioError, "no model the Studio can copy"):
            self.api.model_copy(self.NEW)
        self.api._copy_models = lambda address: ["ww2\\x\\tanklod0.ase2ndfbin"]
        glb = self.mod / "files" / "models" / "Descriptor_Unit_R2_Red.glb"
        glb.parent.mkdir(parents=True)
        glb.write_bytes(b"glTF")
        with self.assertRaisesRegex(StudioError, "imported model"):
            self.api.model_copy(self.NEW)

    def test_bring_back_into_the_copy(self):
        import json
        from rusemod import unitlook
        with tempfile.TemporaryDirectory() as d:
            work, root = Path(d, "work"), Path(d, "copy")
            work.mkdir()
            (work / "a.png").write_bytes(png_bytes(bytes((1, 2, 3, 255)), 1, 1, channels=4))
            (work / unitlook.LOOK_FILE).write_text(json.dumps({"models": [], "pictures": {
                "a.png": {"texture": self.TEX, "kind": "colour", "hash": "painted since"}}}), encoding="utf-8")
            done = unitlook.bring_back(work, self.mod, root)
            self.assertEqual(Path(done[0]["to"]), root / "gen" / "ww2" / "x" / "a01.tgv.png")
            self.assertFalse((self.mod / "files" / "replace").exists())


class RidesIn(unittest.TestCase):
    """The truck a squad rides in on the roads (StudioApi.rides_in; the owner, 2026-10-11: "rangers versus GI, getting
    a different truck"): the game's trucks of its kind and the mod's copies of a truck, saved as its
    TransportPourMorphe; the game's own truck again takes the change out."""
    TRUCK, GER, GUNS = E + "Descriptor_Unit_TransportSoldier", E + "Descriptor_Unit_TransportSoldier_GER", \
        E + "Descriptor_Unit_TransportCanon"
    RANGERS, TANK = E + "Descriptor_Unit_Soldat_US_Lourd", E + "Descriptor_Unit_M4_Sherman"

    def setUp(self):
        from ruse_studio.edits import ModEdits
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.mod = Path(tmp.name) / "mod"
        (self.mod / "src").mkdir(parents=True)
        self.api = StudioApi(game_dir=Path(tmp.name) / "R.U.S.E", home=Path(tmp.name) / "home")
        rides = {self.RANGERS: self.TRUCK, E + "Descriptor_Unit_Soldat_GER": self.GER, E + "Descriptor_Unit_Gun": self.GUNS}

        class Ix:
            def uses(self, a):
                return [("TransportPourMorphe", "object", rides[a])] if a in rides else []

            def links(self, path):
                return dict(rides) if path == "TransportPourMorphe" else {}

            def close(self):
                pass
        self.api._open = lambda: Ix()
        self.api._names = lambda ix, addresses, lang, new_units=None: {a: a.rsplit("_", 1)[-1] for a in addresses}
        self.api._edits = lambda: ModEdits(self.mod)
        edits = ModEdits(self.mod)
        edits.add_unit(E + "Descriptor_Unit_Ranger_Truck", self.TRUCK, "Ranger Truck", {})

    def test_its_choices_and_the_choice_saved(self):
        info = self.api.rides_in(self.RANGERS)
        self.assertEqual((info["now"], info["game"]), (self.TRUCK, self.TRUCK))
        self.assertEqual([c["address"] for c in info["choices"]],
                         [self.TRUCK, self.GER, E + "Descriptor_Unit_Ranger_Truck"])  # troop trucks, and the mod's
        self.assertEqual([c["new"] for c in info["choices"]], [False, False, True])
        res = self.api.rides_in_set(self.RANGERS, E + "Descriptor_Unit_Ranger_Truck")
        self.assertEqual(res["now"], E + "Descriptor_Unit_Ranger_Truck")
        text = (self.mod / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn("TransportPourMorphe = $/GFX/Everything/Descriptor_Unit_Ranger_Truck", text)
        self.assertEqual(self.api.rides_in_set(self.RANGERS, self.TRUCK)["now"], self.TRUCK)  # the game's: no change
        self.assertNotIn("TransportPourMorphe", (self.mod / "src" / "studio.rndf").read_text(encoding="utf-8"))

    def test_what_isn_t_a_choice(self):
        from ruse_studio.api import StudioError
        self.assertEqual(self.api.rides_in(self.TANK), {})
        with self.assertRaisesRegex(StudioError, "doesn't ride in a truck"):
            self.api.rides_in_set(self.TANK, self.TRUCK)
        with self.assertRaisesRegex(StudioError, "isn't one of the trucks"):
            self.api.rides_in_set(self.RANGERS, self.GUNS)  # a gun truck for a squad


class Page(unittest.TestCase):
    def test_the_words_and_the_buttons(self):
        import tomllib
        root = Path(__file__).resolve().parents[1]
        words = tomllib.loads((root / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        for key in ("model_copy", "tip_model_copy", "model_copy_how", "model_copy_has", "model_copy_remove",
                    "tip_model_copy_remove", "uniform_title", "uniform_default", "uniform_custom", "tip_uniform_custom",
                    "uniform_has", "uniform_default_again", "tip_uniform_default_again", "uniform_shared_paint",
                    "card_stale", "card_take", "tip_card_take", "card_choose", "tip_card_choose", "rides_in",
                    "tip_rides_in", "rides_in_how", "rides_in_game", "rides_in_mine", "rides_in_open",
                    "tip_rides_in_open"):
            self.assertEqual(len(words[key]), 10, key)
        app = (root / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        fake = (root / "src" / "ruse_studio" / "ui" / "fake-api.js").read_text(encoding="utf-8")
        for needle in ('copyAction("model_copy"', 'copyAction("model_copy_remove"', "info.own_copy", "uniformBox(",
                       'act("model_copy"', "ridesInBox(u)", "rides_in_set(", "cardRow(u, info.card, painted > 0)",
                       "cardFromFile("):
            self.assertIn(needle, app)
        for needle in ("model_copy: async", "model_copy_remove: async", "rides_in: async", "rides_in_set: async",
                       "soldiers: fakeSquad(address)"):
            self.assertIn(needle, fake)


if __name__ == "__main__":
    unittest.main()
