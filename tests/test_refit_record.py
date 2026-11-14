"""A new unit's model record (files/models/<unit>.json) that can't be read, is gone, or no longer says what the model
is (the resize recheck, round 2: Import model again over one put a RUSE Decoy change back and named nothing; the fit
wrote the record in place, so a write stopped part way left it that way).

- Every record the Studio writes of a model goes whole or not at all (ruse_studio.animmodel_calls.write_record): a write
  that stops part way leaves the record as it was.
- Over a record that tells nothing, Resize and Move are refused in words that say so (not "import one first", of a
  model the page still shows); every unit at once says it skipped it, and why.
- Import model again and Bring back the model then read what the last fit took in from the model's own file in the mod,
  so a change of the modder's is named, never put back without a word; what else the record held (a split chosen on the
  page, a Custom uniform the model took the place of) is said as not kept ("record").
On test_animmodel's made-up game (tests/test_refit_keeps.py's stand-ins): no game needed."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import test_refit_keeps as base
from ruse_studio.animmodel_calls import NOT_KEPT
from ruse_studio.api import StudioError
from test_horse_squad import finished

ADDRESS, UNIT, beast_glb = base.ADDRESS, base.UNIT, base.beast_glb


class RecordLost(base.Refit):
    def path(self) -> Path:
        return self.target.with_suffix(".json")

    def cut_short(self) -> None:
        text = self.path().read_text(encoding="utf-8")
        self.path().write_text(text[:len(text) // 3], encoding="utf-8")

    def named(self, got: dict):
        return (got.get("model") or {}).get(NOT_KEPT)

    # --- the record written whole or not at all ---
    def test_a_record_write_that_stops_leaves_the_record_as_it_was(self):
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        before = self.path().read_bytes()
        real = Path.write_text

        def full(path, data, *args, **kwargs):   # (the disk full a third of the way into any write of a record)
            if Path(path).name.startswith(self.path().name):
                real(path, data[:len(data) // 3], *args, **kwargs)
                raise OSError(28, "No space left on device")
            return real(path, data, *args, **kwargs)
        for how, call in (("Resize", lambda: self.api.model_resize(ADDRESS, 1.4)),
                          ("Move", lambda: self.api.model_place(ADDRESS, [10, 0, 0])),
                          ("Take it out keeping a uniform", lambda: self.api._keep_in_model_record(ADDRESS, "u"))):
            with self.subTest(how=how):
                # (the final join: a fit's failed record write is said in words, a StudioError raised from the
                # OSError, fix/horse-add's file_error; Take it out's own write still raises the OSError itself)
                with mock.patch.object(Path, "write_text", full), self.assertRaises((OSError, StudioError)):
                    call()
                self.assertEqual(self.path().read_bytes(), before)
                self.assertFalse(self.path().with_name(self.path().name + ".part").exists())
        # (space freed) Resize goes on, the change kept
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertEqual((self.clips()["Walk"], self.named(got)), (changed, None))
        # Import model again stopped the same way: the record readable, as it was
        before = self.path().read_bytes()
        with mock.patch.object(Path, "write_text", full), self.assertRaises((OSError, StudioError)):
            self.imported(beast_glb())
        self.assertEqual(self.path().read_bytes(), before)

    def test_the_record_s_text_is_as_before(self):
        """Written as before (json, indent 1), so a mod's record reads and compares the same."""
        self.imported(beast_glb())
        data = json.loads(self.path().read_text(encoding="utf-8"))
        self.assertEqual(self.path().read_text(encoding="utf-8"), json.dumps(data, indent=1))

    # --- over a record that tells nothing: refused in words, named, never put back unsaid ---
    def test_resize_and_move_say_the_record_can_t_be_read(self):
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        self.cut_short()
        for call in (lambda: self.api.model_resize(ADDRESS, 1.0), lambda: self.api.model_place(ADDRESS, [1, 0, 0])):
            with self.assertRaises(StudioError) as said:
                call()
            self.assertIn("can't be read or is missing", str(said.exception))
            self.assertIn(f"{UNIT}.json", str(said.exception))
        self.assertEqual(self.clips()["Walk"], changed)

    def test_its_refusal_is_in_every_language(self):
        from ruse_studio import errortext
        self.imported(beast_glb())
        self.cut_short()
        with self.assertRaises(StudioError) as said:
            self.api.model_resize(ADDRESS, 1.0)
        for lang in errortext.LANGS:
            if lang in ("us", "base"):
                continue
            with self.subTest(lang=lang):
                worded = errortext.worded(str(said.exception), lang)
                self.assertNotEqual(worded, str(said.exception))
                self.assertIn(f"{UNIT}.json", worded)

    def test_every_unit_at_once_says_it_skipped_it(self):
        del self.api._own_models_of            # (the Studio's own listing, the unit's kind given)
        self.api._unit_kinds = lambda addresses: {a: "ground" for a in addresses}
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        self.cut_short()
        view = finished(self.api, self.api.models_resize_all("ground", "game")["job"], 120)
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(len(view["lines"]), 1, view["lines"])
        self.assertTrue(view["lines"][0].startswith("skipped\tBeast\t"), view["lines"])
        self.assertIn("can't be read or is missing", view["lines"][0])
        self.assertEqual(self.clips()["Walk"], changed)

    def test_import_model_again_names_the_change(self):
        for how in ("cut short", "not JSON of a record", "gone", "the split alone"):
            with self.subTest(how=how):
                self.imported(beast_glb())
                self.imported(beast_glb())   # (nothing of his: nothing named)
                self.decoy("Walk")
                if how == "cut short":
                    self.cut_short()
                elif how == "not JSON of a record":
                    self.path().write_text("[1, 2]", encoding="utf-8")
                elif how == "gone":
                    self.path().unlink()
                else:   # (the page's split saved over one that couldn't be read: rusemod.bonefit.save_split)
                    self.path().write_text(json.dumps({"split": "spine"}), encoding="utf-8")
                got = self.imported(beast_glb())
                self.assertEqual(self.clips(), self.clips_of_file())
                said = self.named(got) or {}
                self.assertEqual(said.get("animations"), ["Walk"])
                self.assertEqual(said.get("record", False), how in ("cut short", "not JSON of a record"))
                got = self.imported(beast_glb())   # (the record whole again: nothing of his left)
                self.assertIsNone(self.named(got))

    def test_nothing_changed_is_named_nothing_but_the_record(self):
        self.imported(beast_glb())
        self.cut_short()
        got = self.imported(beast_glb())
        self.assertEqual(self.named(got), {"animations": [], "picks": [], "record": True})
        self.path().unlink()
        got = self.imported(beast_glb())
        self.assertIsNone(self.named(got))

    def test_another_file_imported_names_the_change_only(self):
        self.imported(beast_glb())
        self.decoy("Run")
        self.path().unlink()
        got = self.imported(beast_glb(step=0.3))
        self.assertEqual(self.named(got)["animations"], ["Run"])

    def test_the_model_s_own_file_unread_too_names_every_animation_it_puts_back(self):
        """Nothing left to tell his changes by: every animation the new model's take the place of is named (one equal to
        the new model's, byte for byte, isn't taken the place of)."""
        self.imported(beast_glb())
        self.decoy("Walk")
        self.cut_short()
        self.target.write_bytes(self.target.read_bytes()[:16])
        got = self.imported(beast_glb())
        self.assertEqual(self.named(got)["animations"], ["Walk"])
        self.decoy("Walk")
        self.cut_short()
        self.target.write_bytes(self.target.read_bytes()[:16])
        got = self.imported(beast_glb(step=0.3))
        self.assertEqual(sorted(self.named(got)["animations"]), ["Idle", "Run", "Walk"])

    def test_bring_back_the_model_names_the_change(self):
        from ruse_studio.modelblender import WORK
        self.imported(beast_glb())
        self.decoy("Walk")
        self.cut_short()
        work = self.mod / WORK / UNIT
        work.mkdir(parents=True)
        (work / f"{UNIT}.glb").write_bytes(beast_glb())
        got = self.api.model_blender_back(ADDRESS, 1.0)
        self.assertEqual(self.clips(), self.clips_of_file())
        self.assertEqual(self.named(got)["animations"], ["Walk"])

    def test_a_model_on_the_game_soldier_s_bones_in_its_place_takes_the_animations_out_and_names_the_change(self):
        """Before: over a record that couldn't be read the own-bones animations stayed, played on the soldier's bones."""
        self.imported(beast_glb())
        self.decoy("Walk")
        self.cut_short()
        self.soldier = True
        got = self.imported(beast_glb())
        self.assertEqual(self.clips(), {})
        self.assertEqual(self.named(got)["animations"], ["Walk"])

    def test_a_custom_uniform_kept_over_a_record_that_can_t_be_read(self):
        """Take it out keeps the uniform in a model still there (_keep_in_model_record): over a record that can't be
        read it's kept all the same, never a stop with Python's words."""
        self.imported(beast_glb())
        self.cut_short()
        self.api._keep_in_model_record(ADDRESS, "the uniform")
        self.assertEqual(json.loads(self.path().read_text(encoding="utf-8")), {"copy_kept": "the uniform"})
        got = self.imported(beast_glb())
        self.assertIsNone(self.named(got))
        self.assertEqual(json.loads(self.path().read_text(encoding="utf-8"))["copy_kept"], "the uniform")


for _name in dir(base.Refit):   # (Refit's own tests run in test_refit_keeps)
    if _name.startswith("test_") and _name not in RecordLost.__dict__:
        setattr(RecordLost, _name, None)


class ThePage(unittest.TestCase):
    def test_the_page_says_the_record_in_every_language(self):
        import tomllib
        from ruse_studio import api
        words = tomllib.loads(Path(api.__file__).with_name("words.toml").read_text(encoding="utf-8"))
        row = words["model_kept_not_record"]
        self.assertEqual(sorted(row), sorted(["us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa"]))
        self.assertEqual(len(set(row.values())), 11)
        js = (Path(api.__file__).parent / "ui" / "app.js").read_text(encoding="utf-8")
        self.assertIn("if (lost.record) said.push(w.model_kept_not_record)", js)


if __name__ == "__main__":
    unittest.main()
