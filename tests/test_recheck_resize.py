"""The resize recheck (round 1, fix/resize at e469d4d4): what a fit again of a model on bones of its own (Resize, Move,
every ground unit at once) does with a clip file of the mod's that can't be read the way the Studio writes them
(ADamagedClipFile, a regression), and what Import model again does over a model record written before the fix
(ARecordFromBefore: the class not closed on that route).

Since e469d4d4 a fit again reads every one of the model's animations as the mod has them (AnimModelCalls._own_now) and
checks each one changed since the last fit (_record_more: "a clip file that isn't one any more: the file's takes its
place, said"). That check catches only rusemod.baf.ClipError. A clip file whose parts follow each other but whose
bones' table runs past its end (one number of it damaged: the bones' count) makes rusemod.baf.parse raise
struct.error instead, so:
- Resize and Move stop with Python's own words ("unpack_from requires a buffer of at least 4028 bytes ..."), where
  before the fix (db2abbfb) the file's clip took its place;
- the resize of every ground unit at once stops for every unit after it ("Something went wrong: error: ..."), where
  the job says one that can't be fitted leaves the rest.
Each test here FAILS on e469d4d4 by design until fixed; ADamagedClipFile's pass on db2abbfb, ARecordFromBefore's fails
there too. On test_animmodel's made-up game (the stand-ins of tests/test_refit_keeps.py, written out here so the file
runs on the code before the fix too): no game needed."""
import json
import struct
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from rusemod import anim, baf, unitmodel
from test_horse_squad import finished
from test_ownrig import little_glb

E = "$/GFX/Everything/"
UNIT = "Descriptor_Unit_Beast"
ADDRESS = E + UNIT

# a clip file of 36 bytes whose parts follow each other (its tracks' 8 bytes at 28, nothing after) but whose bones'
# count says 1000: its bones' table runs past its end
DAMAGED = struct.pack("<IfHHIIII", 15, 1.0, 1, 1000, 28, 36, 8, 0) + bytes(8)


def beast_glb(names=("Walk", "Run", "Idle")) -> bytes:
    """test_animmodel's little three-bone beast with an animation for each of `names` (its first bone moved)."""
    return little_glb([(n, [(1, "translation", [0.0, 1.0], [(0.0, 1.0, 0.0), (0.0, 1.0, 0.1 * (k + 1))], "LINEAR")])
                       for k, n in enumerate(names)], names=("Hips", "Spine", "Head"))


class ADamagedClipFile(unittest.TestCase):
    def setUp(self):
        from ruse_studio.api import StudioApi
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        root = Path(self.dir.name)
        data = root / "R.U.S.E" / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_Win.dat").write_bytes(b"zz")
        self.mod = root / "mod"
        self.mod.mkdir()
        self.api = StudioApi(game_dir=root / "R.U.S.E", home=root / "home")
        self.api._mod_dir = lambda: self.mod
        self.api._look_models = lambda address: (["the rifleman", "the bazooka man"], [])
        self.target = self.mod / "files" / "models" / f"{UNIT}.glb"
        self.api._own_model_file = lambda address: self.target
        self.api._own_copy_file = lambda address: None
        self.api._model_actions = lambda address, report: []
        self.api.look = lambda address: {"new_unit": True}
        self.api._own_models_of = lambda kind: [ADDRESS]
        self.api._new_units = lambda: {ADDRESS: SimpleNamespace(name="Beast")}
        self.src = root / "beast.glb"
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch("rusemod.unitmodel.import_model", self.fake_import()))
        stack.enter_context(mock.patch("rusemod.unitmodel.rigged_first", lambda game, file, models: list(models)))
        stack.enter_context(mock.patch("rusemod.animmodel.own_bones_on", lambda game, path, models: models[0]))

    @staticmethod
    def fake_import():
        """import_model as test_refit_keeps' (test_animmodel's): on bones of its own, the real import on
        test_unitmodel's made-up packs."""
        from rusemod.unitmodel import UnitModelError
        from test_unitmodel import TANK, zz_win
        real = unitmodel.import_model

        def fake(game, model, file, out, own_bones=False, clips=None, **kw):
            if not own_bones:
                raise UnitModelError(f"its bones aren't {model}'s: hips, spine")
            arc = zz_win()
            with mock.patch("rusemod.build.find_pack", lambda *_a: "zz"), \
                    mock.patch("rusemod.edat.Edat.open", lambda _p: arc):
                return real(Path("game"), TANK, file, out, own_bones=True, clips=clips, others=kw.get("others"))
        return fake

    def imported(self, data: bytes) -> dict:
        self.src.write_bytes(data)
        return self.api.model_import(ADDRESS, str(self.src))

    def clips(self) -> dict:
        own = anim.own_animations(self.mod, UNIT)["animations"]
        return {n: (self.mod / anim.OWN / UNIT / f).read_bytes() for n, f in own.items()}

    def damage(self, name: str = "Walk") -> None:
        f = self.mod / anim.OWN / UNIT / anim.own_animations(self.mod, UNIT)["animations"][name]
        f.write_bytes(DAMAGED)

    def test_resize_and_move_take_the_file_s_clip_in_its_place(self):
        from ruse_studio.api import StudioError
        self.imported(beast_glb())
        file = self.clips()
        for how, call in (("Resize", lambda: self.api.model_resize(ADDRESS, 1.0)),
                          ("Move", lambda: self.api.model_place(ADDRESS, [10, 0, 0]))):
            with self.subTest(how=how):
                self.damage()
                try:
                    call()
                except StudioError:          # (refused in the Studio's own words: the mod as it was)
                    continue
                self.assertEqual(self.clips()["Walk"], file["Walk"])

    def test_every_ground_unit_at_once_goes_on_past_it(self):
        self.imported(beast_glb())
        self.damage()
        view = finished(self.api, self.api.models_resize_all("ground", "game")["job"], 120)
        self.assertEqual(view["state"], "done", view.get("message"))
        said = view["lines"][0].split("\t")[0] if view["lines"] else None
        self.assertIn(said, ("resized", "skipped"), view["lines"])


class ARecordFromBefore(ADamagedClipFile):
    """A model record written before e86eabec has no fingerprints of what its fit took in ("from_file"): every own-bones
    record of this branch's mods made before the fix, such as the mod behind the owner's test copy decoy-blender2
    (its Horse Squad's RUSE Decoy changes of 2026-11-12: stand, run, ride; whether that mod is used again is not
    known). Import model again, the same file: the change made in RUSE Decoy goes back to the
    file's and nothing names it (the fixer's known limit: "Import model again over such a record can't name his
    changes"), though the same file tells it, as Resize tells it on such a record. FAILS on e469d4d4 and on db2abbfb
    (not a regression: the class not closed on this route)."""
    test_resize_and_move_take_the_file_s_clip_in_its_place = None
    test_every_ground_unit_at_once_goes_on_past_it = None

    def decoy(self, name: str = "Walk") -> bytes:
        """One of its animations changed as RUSE Decoy's Bring my changes back keeps it (decoyblender.py: the mod's
        animations with the changed one in its place by name, rusemod.anim.set_animations, and the record's
        lengths): its first bone turned and the animation half as fast. Returns the changed clip."""
        now = self.clips()
        c = baf.parse(now[name])
        changed = baf.build(baf.with_speed(baf.with_bone(c, baf.skeleton(c.skeleton)["names"][0], turn=("x", 20.0)),
                                           50.0))
        clips = {**now, name: changed}
        files = anim.set_animations(self.mod, UNIT, clips)
        self.api._record_lengths(ADDRESS, clips, files)
        return changed

    def test_import_model_again_names_or_keeps_the_change_it_would_put_back(self):
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        path = self.target.with_suffix(".json")
        record = json.loads(path.read_text(encoding="utf-8"))
        record.pop("from_file", None)                 # (as written before e86eabec)
        path.write_text(json.dumps(record, indent=1), encoding="utf-8")
        got = self.imported(beast_glb())
        kept = self.clips()["Walk"] == changed
        named = ((got.get("model") or {}).get("not_kept") or {}).get("animations")
        self.assertTrue(kept or named == ["Walk"],
                        f"Import model again put the file's Walk back and named {named or 'nothing'}")


if __name__ == "__main__":
    unittest.main()
