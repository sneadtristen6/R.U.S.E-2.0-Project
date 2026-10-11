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
                (models / "Panzer_Red.copy.toml").write_text('of = "the Panzer\'s model"\n', encoding="utf-8")
            if paint:
                to = models / "Panzer_Red" / (MEMBER.replace("\\", "/") + ".png")
                to.parent.mkdir(parents=True)
                to.write_bytes(png_bytes(bytes(RED + (255,)) * 64, 8, 8, channels=4))
            if glb:
                (models / "Panzer_Red.glb").write_bytes(b"glTF")
            info = load_mod(mod)
            return info, build_pack(Edat(UNIT_PACK), [info], text_arc=zz_with_texture())

    def test_the_copy_names_its_model(self):
        info, result = self.build(paint=True)
        self.assertEqual(list(info[0].model_copies), ["Panzer_Red"])
        self.assertEqual(result.errors, [])
        source, paint, mod_id = result.own_copies["Panzer_Red"]
        self.assertEqual((source, list(paint), mod_id),
                         ("WW2\\Res3D\\Units\\GER\\Tank\\GER_PanzerIVlod0.Ase2NdfBin", [MEMBER], "m"))
        game, _files = load(result.changed)
        unit = game.objects[next(k for k in game.objects if k.rsplit("/", 1)[-1] == "Panzer_Red")]
        self.assertEqual(unit.props["GfxDescriptor"].obj.props["MeshDescriptor"].obj.props["FileName"].value,
                         "WW2\\Res3D\\Units\\GER\\Tank\\Panzer_Redlod0.Ase2ndfbin")

    def test_a_unit_can_t_have_both(self):
        _info, result = self.build(glb=True)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("has an imported model too", result.errors[0].message)


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
        self.api._copied_model = lambda address: "WW2\\X\\Tanklod0.Ase2NdfBin"
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
        self.assertIn('of = "WW2\\\\X\\\\Tanklod0.Ase2NdfBin"', marker.read_text(encoding="utf-8"))
        self.assertTrue(res["own_copy"])
        self.assertEqual(unitmodel.mod_copies(self.mod), {"Descriptor_Unit_R2_Red": {}})
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
        with self.assertRaisesRegex(StudioError, "Only a new unit"):
            self.api.model_copy("$/GFX/Everything/Descriptor_Unit_Test")

    def test_what_can_t_get_a_copy(self):
        from ruse_studio.api import StudioError
        self.api._copied_model = lambda address: None
        with self.assertRaisesRegex(StudioError, "not infantry"):
            self.api.model_copy(self.NEW)
        self.api._copied_model = lambda address: "WW2\\X\\Tanklod0.Ase2NdfBin"
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


class Page(unittest.TestCase):
    def test_the_words_and_the_buttons(self):
        import tomllib
        root = Path(__file__).resolve().parents[1]
        words = tomllib.loads((root / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        for key in ("model_copy", "tip_model_copy", "model_copy_how", "model_copy_has", "model_copy_remove",
                    "tip_model_copy_remove"):
            self.assertEqual(len(words[key]), 10, key)
        app = (root / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        fake = (root / "src" / "ruse_studio" / "ui" / "fake-api.js").read_text(encoding="utf-8")
        for needle in ('copyAction("model_copy"', 'copyAction("model_copy_remove"', "info.own_copy"):
            self.assertIn(needle, app)
        for needle in ("model_copy: async", "model_copy_remove: async"):
            self.assertIn(needle, fake)


if __name__ == "__main__":
    unittest.main()
