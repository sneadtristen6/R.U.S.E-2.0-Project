"""The resize recheck (round 1, fix/resize at e469d4d4), a second read of the same kind as tests/test_recheck_resize.py's
ADamagedClipFile: before a fit again of a model on bones of its own, AnimModelCalls._bones_now (new in e86eabec) reads
the skeleton of the mod's own model file (files/models/<unit>.glb) and catches OSError and ValueError only. A model file
cut short at 16 bytes (as a write stopped early leaves it: "glTF" and its header, no JSON chunk) makes
rusemod.modelin.glb_document raise struct.error there, so:
- Resize stops with Python's own words ("unpack_from requires a buffer of at least 20 bytes ..."), where before the fix
  (db2abbfb) the fit wrote the model file anew from the file it was made from;
- the resize of every ground unit at once fails for every unit after it ("Something went wrong: error: ...").
FAILS on e469d4d4 by design until fixed, passes on db2abbfb. On test_animmodel's made-up game (the stand-ins of
tests/test_recheck_resize.py): no game needed."""
import unittest

import test_recheck_resize as base
from ruse_studio.api import StudioError
from test_horse_squad import finished


class AModelFileCutShort(base.ADamagedClipFile):
    # (ADamagedClipFile's made-up game and stand-ins, not its tests)
    test_resize_and_move_take_the_file_s_clip_in_its_place = None
    test_every_ground_unit_at_once_goes_on_past_it = None

    def cut(self) -> bytes:
        whole = self.target.read_bytes()
        self.target.write_bytes(whole[:16])
        return whole

    def test_resize_writes_it_anew_or_says_why_not_in_words(self):
        self.imported(base.beast_glb())
        whole = self.cut()
        try:
            self.api.model_resize(base.ADDRESS, 1.0)
        except StudioError:                  # (refused in the Studio's own words)
            return
        self.assertEqual(self.target.read_bytes(), whole)

    def test_every_ground_unit_at_once_goes_on_past_it(self):
        self.imported(base.beast_glb())
        self.cut()
        view = finished(self.api, self.api.models_resize_all("ground", "game")["job"], 120)
        self.assertEqual(view["state"], "done", view.get("message"))


if __name__ == "__main__":
    unittest.main()
