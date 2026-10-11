"""A unit's models in the Studio (StudioApi._unit_models; the owner, 2026-10-11: "there's no 3D models for infantry"):
a vehicle's from its GfxDescriptor as before, infantry's soldiers from its other graphics when GfxDescriptor reaches
no model, with a model part another infantry unit shares followed and the wreck the game reuses for fallen soldiers
left out."""
import unittest

from ruse_studio.api import StudioApi

E = "$/GFX/Everything/"


class FakeIndex:
    """The game index's `uses` (prop, kind, what) for a few made-up objects."""

    def __init__(self, uses: dict):
        self._uses = uses

    def uses(self, address):
        return self._uses.get(address, [])


TANK = E + "Descriptor_Unit_Tank"
SOLDIERS = E + "Descriptor_Unit_Soldat_Leger"
HEAVY = E + "Descriptor_Unit_Soldat_Lourd"
INDEX = FakeIndex({
    TANK: [("GfxDescriptor", "object", TANK + ":GfxDescriptor"),
           ("GfxDescriptorCadavre", "object", TANK + ":GfxDescriptorCadavre")],
    TANK + ":GfxDescriptor": [("MeshDescriptor", "object", TANK + ":GfxDescriptor.MeshDescriptor"),
                              ("Smoke", "object", E + "Shared:Smoke")],
    TANK + ":GfxDescriptor.MeshDescriptor": [("FileName", "file", "ww2/res3d/units/tank/tanklod0.ase2ndfbin")],
    E + "Shared:Smoke": [("FileName", "file", "ww2/res3d/nonclasse/smokelod0.ase2ndfbin")],
    TANK + ":GfxDescriptorCadavre": [("MeshDescriptor", "object", TANK + ":GfxDescriptorCadavre.MeshDescriptor")],
    TANK + ":GfxDescriptorCadavre.MeshDescriptor": [("FileName", "file", "ww2/res3d/units/tank/tank_destlod0.ase2ndfbin")],
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
        self.assertEqual(StudioApi._unit_models(INDEX, TANK), ["ww2\\res3d\\units\\tank\\tanklod0.ase2ndfbin"])

    def test_infantry_shows_its_soldiers(self):
        self.assertEqual(StudioApi._unit_models(INDEX, SOLDIERS),
                         ["ww2\\res3d\\units\\us\\infanterie\\us_soldier_bazooka_modellod0.ase2ndfbin",
                          "ww2\\res3d\\units\\us\\infanterie\\us_soldier_modellod0.ase2ndfbin"])

    def test_a_soldier_model_part_shared_with_other_infantry(self):
        self.assertEqual(StudioApi._unit_models(INDEX, HEAVY),
                         ["ww2\\res3d\\units\\us\\infanterie\\us_soldier_modellod0.ase2ndfbin"])


if __name__ == "__main__":
    unittest.main()
