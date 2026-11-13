"""The one Blender button of a unit's page (ruse_studio.oneblender; the owner, 2026-11-13: "you can either take the whole
unit or ... select which ones you want to bring into Blender ... I want to bring everything but the bones. So then you
just uncheck the bones"; "Why is there two different buttons doing the same thing that then break sometimes?"): which
Blender its ticks open and which bring-back it then calls, with the doors themselves standing in (their own tests are
test_modelblender, test_squadblender; the keepers' are test_modelblender BonesKept and PaintKept)."""
import json
import tempfile
import unittest
from pathlib import Path

from ruse_studio.api import StudioError
from ruse_studio.oneblender import ONE, OneBlenderCalls

E = "$/GFX/Everything/"


class Stand(OneBlenderCalls):
    """A Studio with one mod, a unit in it, and every door recording its call."""

    def __init__(self, root: Path, squad=False, own_bones=False, game_unit=False):
        self.root, self.squad, self.own_bones_, self.game_unit = root, squad, own_bones, game_unit
        self.calls = []

    def _mod_dir(self):
        return self.root / "mod"

    def _soldiers(self, address):
        return self.squad

    def _own_model_file(self, address):
        return None if self.game_unit else self.root / "mod/files/models" / (address.rsplit("/", 1)[-1] + ".glb")

    def _own_bones(self, address):
        return self.own_bones_

    def _kind_rows(self, address):
        return [{"kind": None}, {"kind": "bazooka", "label": "Bazooka man"}]

    def _kind_file(self, address, kind):
        return self.root / "mod/files/models" / f"{address.rsplit('/', 1)[-1]}@{kind}.glb"

    def squad_info(self, address, lang="us"):
        return {"soldiers": [{"id": "1", "label": "Rifleman 1"}, {"id": "2", "label": "Rifleman 2"},
                             {"id": "3", "label": "Bazooka man 3"}]}

    def model_blender(self, address, lang="us", kind=None):
        self.calls.append(("model_blender", kind))
        return {"work": "w"}

    def model_blender_back(self, address, size=1.0, kind=None, keep_bones=False, keep_paint=False):
        self.calls.append(("model_blender_back", kind, keep_bones, keep_paint))
        return {"model": {}}

    def _into_blender(self, address, lang, only=None):
        self.calls.append(("squad_blender", only))
        return {"opened": only}

    def squad_blender_back(self, address, lang="us", keep_bones=False, keep_paint=False):
        self.calls.append(("squad_blender_back", keep_bones, keep_paint))
        return {"changed": []}

    def look_open(self, address):
        self.calls.append(("look_open",))
        return {"message": "opened"}

    def look_bring_back(self, address):
        self.calls.append(("look_bring_back",))
        return {"brought": []}


class OneButton(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_a_unit_with_everything_ticked_opens_its_model_and_brings_it_back_whole(self):
        s = Stand(self.root)
        parts = s.blender_parts(E + "Descriptor_Unit_Tank")
        self.assertEqual((parts["route"], [p["id"] for p in parts["parts"]]), ("model", ["model", "paint"]))
        s.blender_open(E + "Descriptor_Unit_Tank", {"model": True, "paint": True})
        s.blender_back(E + "Descriptor_Unit_Tank")
        self.assertEqual(s.calls, [("model_blender", None), ("model_blender_back", None, False, False)])

    def test_unticked_bones_and_paint_come_back_as_they_were(self):
        s = Stand(self.root, own_bones=True)
        s.blender_open(E + "Descriptor_Unit_Beast", {"model": True, "bones": False, "paint": False})
        s.blender_back(E + "Descriptor_Unit_Beast")
        self.assertEqual(s.calls[-1], ("model_blender_back", None, True, True))

    def test_the_paint_alone_opens_the_paint_and_brings_the_paint_back(self):
        s = Stand(self.root)
        s.blender_open(E + "Descriptor_Unit_Tank", {"model": False, "paint": True})
        s.blender_back(E + "Descriptor_Unit_Tank")
        self.assertEqual(s.calls, [("look_open",), ("look_bring_back",)])

    def test_nothing_ticked_is_refused_and_nothing_opened(self):
        s = Stand(self.root)
        with self.assertRaises(StudioError):
            s.blender_open(E + "Descriptor_Unit_Tank", {"model": False, "paint": False})
        self.assertEqual(s.calls, [])

    def test_a_squad_of_game_soldiers_opens_the_soldiers_ticked_side_by_side(self):
        s = Stand(self.root, squad=True)
        parts = s.blender_parts(E + "Descriptor_Unit_My_Riflemen")
        self.assertEqual(parts["route"], "squad")
        self.assertEqual([x["id"] for x in parts["soldiers"]], ["1", "2", "3"])
        s.blender_open(E + "Descriptor_Unit_My_Riflemen", {"model": True, "soldiers": ["1", "3"], "bones": False})
        s.blender_back(E + "Descriptor_Unit_My_Riflemen")
        self.assertEqual(s.calls, [("squad_blender", ["1", "3"]), ("squad_blender_back", True, False)])

    def test_a_squad_on_bones_of_its_own_opens_one_model_never_the_whole_squad(self):
        """The Generic Horse through the squad's side-by-side Blender came back off the riflemen's bones, "that can stop
        the game", with every soldier's animations (walked with real Blender 2026-11-13): it opens one model at a time."""
        s = Stand(self.root, squad=True, own_bones=True)
        parts = s.blender_parts(E + "Descriptor_Unit_Generic_Horse")
        self.assertEqual(parts["route"], "kinds")
        self.assertEqual([k["id"] for k in parts["kinds"]], ["", "bazooka"])
        s.blender_open(E + "Descriptor_Unit_Generic_Horse", {"model": True, "kind": "bazooka"})
        s.blender_open(E + "Descriptor_Unit_Generic_Horse", {"model": True, "kind": ""})
        self.assertEqual(s.calls, [("model_blender", "bazooka"), ("model_blender", None)])
        self.assertNotIn("squad_blender", [c[0] for c in s.calls])

    def test_a_game_unit_cant_go_and_bring_back_before_open_is_refused(self):
        s = Stand(self.root, game_unit=True)
        self.assertFalse(s.blender_parts(E + "Descriptor_Unit_Soldat_US_Leger")["can"])
        with self.assertRaises(StudioError):
            s.blender_open(E + "Descriptor_Unit_Soldat_US_Leger", {"model": True})
        t = Stand(self.root)
        with self.assertRaises(StudioError):
            t.blender_back(E + "Descriptor_Unit_Tank")
        self.assertEqual(s.calls + t.calls, [])

    def test_what_was_opened_is_remembered_beside_the_units_blender_files(self):
        s = Stand(self.root)
        s.blender_open(E + "Descriptor_Unit_Tank", {"model": True, "bones": False})
        one = self.root / "mod/blender/Descriptor_Unit_Tank" / ONE
        self.assertEqual(json.loads(one.read_text(encoding="utf-8"))["door"], "model")
        self.assertTrue(s.blender_parts(E + "Descriptor_Unit_Tank")["open"])
        s.blender_back(E + "Descriptor_Unit_Tank")
        self.assertFalse(s.blender_parts(E + "Descriptor_Unit_Tank")["open"])


if __name__ == "__main__":
    unittest.main()
