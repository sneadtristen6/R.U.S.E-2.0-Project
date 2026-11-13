"""Fixer B's mend of the one check's findings 2, 3, 4, 5, 7, 11 and 12 (2026-11-13): a model's record the Studio can't
trust, said in words and never ending a click in Python's own error; a fit's model file, animations and record written
together or not at all (ruse_studio.animmodel_calls.FitUndo); "Resize every ground unit"'s message; another kind's record
that can't be read. Each mend with a case that failed before it and a legitimate case that must still work.

On test_refit_keeps' made-up game (a model on bones of its own, its animations, RUSE Decoy's change stood in) and
test_fix_notes' squad door (a squad's riflemen and bazooka man): no game needed."""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest import mock

import test_refit_keeps as base
from ruse_studio.animmodel_calls import NOT_KEPT, UNDO, FitUndo
from ruse_studio.api import StudioApi, StudioError

ADDRESS, UNIT, beast_glb = base.ADDRESS, base.UNIT, base.beast_glb


class _Case(base.Refit):
    def path(self) -> Path:
        return self.target.with_suffix(".json")

    def named(self, got: dict):
        return (got.get("model") or {}).get(NOT_KEPT)

    def state(self) -> dict:
        """The mod's model file, record and animations, byte for byte."""
        out = {"glb": self.target.read_bytes() if self.target.is_file() else None,
               "record": self.path().read_bytes() if self.path().is_file() else None}
        units = self.mod / "files" / "anim" / "units.toml"
        out["units"] = units.read_bytes() if units.is_file() else None
        own = self.mod / "files" / "anim" / "own" / UNIT
        out["own"] = {p.name: p.read_bytes() for p in sorted(own.iterdir())} if own.is_dir() else None
        return out

    def undo_left(self) -> bool:
        return (self.mod / UNDO).exists()

    def disk_full_at(self, name_starts: str):
        """Path.write_text with the disk full for a file whose name starts so (a third written first)."""
        real = Path.write_text

        def full(path, data, *args, **kwargs):
            if Path(path).name.startswith(name_starts):
                real(path, data[:len(data) // 3], *args, **kwargs)
                raise OSError(28, "No space left on device")
            return real(path, data, *args, **kwargs)
        return mock.patch.object(Path, "write_text", full)

    def studio_ends_at_the_record(self):
        """A Studio that ends between the animations' writes and the record's: nothing it wrote is put back (no
        failure to catch), its copies stay (FitUndo's list), as the Studio closed there leaves them."""
        real = StudioApi._fit_undone

        def killed(api, undos, exc):
            return None
        return mock.patch.multiple(StudioApi, _fit_undone=killed), real


class TheStops(_Case):
    """Findings 3 and 2's class: a record that isn't an object, a field of the wrong shape."""

    def test_a_record_not_an_object_is_said_on_the_page_and_import_again_mends_it(self):
        api = self.api
        api._paint_of = lambda address: []
        api._blender = lambda: None
        api._kind_rows = lambda address: []
        api._look_folder = lambda address: self.mod / "look"
        api._soldiers = lambda address: False
        api._model_kept = lambda address, kinds=None: None
        for text in ("null", "[1, 2]", "\"text\"", "{\"split\": \"bip01\"}"):
            with self.subTest(record=text):
                self.imported(beast_glb())
                self.path().write_text(text, encoding="utf-8")
                got = StudioApi.look(api, ADDRESS)
                self.assertTrue(got["own_model"].get("record_unread"), got["own_model"])
                with self.assertRaises(StudioError) as said:     # (Resize: in words, naming the record)
                    api.model_resize(ADDRESS, 1.2)
                self.assertIn(f"{UNIT}.json", str(said.exception))
                self.imported(beast_glb())                        # (Import model again mends it)
                self.assertFalse(StudioApi.look(api, ADDRESS)["own_model"].get("record_unread"))

    def test_a_readable_record_says_nothing_of_the_kind(self):
        api = self.api
        api._paint_of = lambda address: []
        api._blender = lambda: None
        api._kind_rows = lambda address: []
        api._look_folder = lambda address: self.mod / "look"
        api._soldiers = lambda address: False
        api._model_kept = lambda address, kinds=None: None
        self.imported(beast_glb())
        own = StudioApi.look(api, ADDRESS)["own_model"]
        self.assertNotIn("record_unread", own)
        self.assertEqual(own.get("file"), "beast.glb")

    def test_fields_of_the_wrong_shape_are_fields_that_aren_t_there(self):
        """model_sizes, Resize, Move and every unit at once read a record's size, move and report: one edited by
        hand never stops them in Python's words."""
        self.api._unit_kind = lambda address: "ground"
        self.api.model_size_marks = lambda address, lang="base": {}
        self.imported(beast_glb())
        rec = json.loads(self.path().read_text(encoding="utf-8"))
        rec.update({"size": "big", "move": 5, "facing": {"x": 1}})
        rec["report"] = ["not", "a report"]
        self.path().write_text(json.dumps(rec), encoding="utf-8")
        sizes = self.api.model_sizes(ADDRESS)
        self.assertEqual((sizes["size"], sizes["move"], sizes["length"]), (1.0, [0, 0, 0], None))
        try:
            self.api.model_place(ADDRESS, [5, 0, 0])
        except StudioError:
            pass
        lines = self.every_unit()
        self.assertFalse([ln for ln in lines if "Error" in ln or "TypeError" in ln], lines)

    def test_its_animations_box_with_fields_of_the_wrong_shape(self):
        self.api.unit_actions = lambda address: {"own": False}
        self.imported(beast_glb())
        rec = json.loads(self.path().read_text(encoding="utf-8"))
        good = self.api.model_animations(ADDRESS)
        self.assertEqual([a["name"] for a in good["animations"]], ["Walk", "Run", "Idle"])   # (the legitimate case)
        rec.update({"animations": {"Walk": 1}, "bones": 7, "split": ["x"]})
        self.path().write_text(json.dumps(rec), encoding="utf-8")
        got = self.api.model_animations(ADDRESS)
        self.assertEqual((got["animations"], got["bones"], got["split"]), ([], 0, None))

    def test_take_it_out_with_a_record_that_can_t_be_read_takes_its_animations_too_and_says_it(self):
        self.api._soldier_kinds = lambda address: {}
        self.api.look = lambda address: {}
        for text, unread in (("null", True), ("{ cut short", True), (None, False)):
            with self.subTest(record=text):
                self.imported(beast_glb())
                self.assertTrue(self.clips())
                if text is not None:
                    self.path().write_text(text, encoding="utf-8")
                got = self.api.model_import_remove(ADDRESS)
                self.assertTrue(got["model_out"])
                self.assertEqual(bool(got.get("record_unread")), unread)
                self.assertEqual(self.clips(), {})      # (its animations went with it, never left with no model)
                self.assertFalse(self.target.exists())


class TheWrites(_Case):
    """Findings 4 and 5: the model file, the animations and the record together or not at all."""

    def test_import_again_stopped_at_each_write_leaves_the_mod_as_it_was(self):
        """Stopped at the model file, at the animations, at the record: each time the mod is byte for byte as it was,
        said in words, no copies left; then the import tried again names the RUSE Decoy change it takes the place of."""
        from rusemod import anim
        stops = {
            "the record": lambda: self.disk_full_at(UNIT + ".json"),
            "the animations": lambda: mock.patch.object(anim, "set_animations",
                                                        side_effect=OSError(28, "No space left on device")),
            "a pick": lambda: mock.patch.object(anim, "set_pick", side_effect=OSError(28, "No space left on device")),
        }
        for how, stop in stops.items():
            with self.subTest(stopped_at=how):
                self.imported(beast_glb())
                changed = self.decoy("Walk")
                was = self.state()
                new = beast_glb(step=0.3, extras={"Idle": base.says("idle1")})   # (its word on an action: a pick)
                with stop(), self.assertRaises(StudioError) as said:
                    self.imported(new)
                self.assertNotIn("Errno", str(said.exception))
                self.assertEqual(self.state(), was)
                self.assertFalse(self.undo_left())
                self.assertEqual(self.clips()["Walk"], changed)
                got = self.imported(new)
                self.assertEqual((self.named(got) or {}).get("animations"), ["Walk"])
                self.assertFalse(self.undo_left())

    def test_a_squad_s_resize_stopped_at_its_second_model_puts_the_first_back(self):
        """A Resize fits the unit's model, then a squad's other kinds': stopped at the second, the first is put back
        too, so the squad is never left half resized."""
        self.imported(beast_glb())
        was = self.state()
        other = self.target.with_name(f"{UNIT}@bazooka.glb")
        other.write_bytes(b"his model")
        other.with_suffix(".json").write_text(json.dumps({"from": str(self.src), "size": 1.0}), encoding="utf-8")
        self.api._kind_records = lambda address: [("bazooka", {"from": str(self.src), "size": 1.0})]
        real = StudioApi._fit_model

        def fit(api, address, file, size, *args, **kwargs):
            if len(args) > 4 and args[4] == "bazooka":
                raise StudioError("his model can't be fitted")
            return real(api, address, file, size, *args, **kwargs)
        with mock.patch.object(StudioApi, "_fit_model", fit), self.assertRaises(StudioError):
            self.api.model_resize(ADDRESS, 1.6)
        self.assertEqual(self.state(), was)
        self.assertFalse(self.undo_left())

    def test_a_studio_that_ended_at_the_record_is_put_back_at_the_next_fit_and_said(self):
        """Finding 5 with a Studio closed (no failure to catch): an import of ANOTHER file got as far as its record,
        then Resize. The other file's model and animations are put back first, said, and Resize fits the first file
        with its own animations and the modder's RUSE Decoy change."""
        self.imported(beast_glb())
        a_run = self.clips()["Run"]
        changed = self.decoy("Walk")
        other = self.src.with_name("other.glb")
        other.write_bytes(beast_glb(step=0.3))
        killed, _real = self.studio_ends_at_the_record()
        with killed, self.disk_full_at(UNIT + ".json"), self.assertRaises(StudioError):
            self.api.model_import(ADDRESS, str(other))
        self.assertNotEqual(self.clips()["Run"], a_run)     # (as the closed Studio left it: the other file's)
        self.assertTrue(self.undo_left())
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertTrue((self.named(got) or {}).get("cut_off"), self.named(got))
        self.assertEqual(self.clips()["Run"], a_run)
        self.assertEqual(self.clips()["Walk"], changed)
        self.assertFalse(self.undo_left())

    def test_a_change_made_after_the_studio_ended_is_kept(self):
        """After the Studio ended mid-way the modder changed Walk in RUSE Decoy before any fit: put back only what is
        still as the stopped fit wrote it; his later change stays."""
        self.imported(beast_glb())
        a_run = self.clips()["Run"]
        other = self.src.with_name("other.glb")
        other.write_bytes(beast_glb(step=0.3))
        killed, _real = self.studio_ends_at_the_record()
        with killed, self.disk_full_at(UNIT + ".json"), self.assertRaises(StudioError):
            self.api.model_import(ADDRESS, str(other))
        later = self.decoy("Walk")
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertTrue((self.named(got) or {}).get("cut_off"))
        self.assertEqual(self.clips()["Run"], a_run)
        self.assertEqual(self.clips()["Walk"], later)

    def test_a_fit_that_got_to_its_end_is_never_put_back(self):
        """The Studio closed after the record was written, before its copies were cleared: nothing put back."""
        self.imported(beast_glb())
        with mock.patch.object(FitUndo, "finish", lambda undo: None):
            self.api.model_resize(ADDRESS, 1.5)
        self.assertTrue(self.undo_left())
        now = self.state()
        got = self.api.model_place(ADDRESS, [0, 0, 0])
        self.assertFalse((self.named(got) or {}).get("cut_off"))
        self.assertEqual(json.loads(self.path().read_text(encoding="utf-8"))["size"], 1.5)
        self.assertEqual(self.state()["own"], now["own"])
        self.assertFalse(self.undo_left())

    def test_what_can_t_be_put_back_now_is_said_and_put_back_at_the_next_fit(self):
        """An import of another file: its record write fails, and putting an animation back is refused too (another
        program holds it): said in words with what to do; the next Resize puts it back first and says so, and fits
        the first file with its own animations."""
        self.imported(beast_glb())
        was = self.state()
        other = self.src.with_name("other.glb")
        other.write_bytes(beast_glb(step=0.3))
        own = self.mod / "files" / "anim" / "own" / UNIT
        real = os.replace

        def held(src, dst, *args, **kwargs):
            if Path(dst).parent == own and UNDO in str(src):
                raise PermissionError(13, "Access is denied", str(dst))
            return real(src, dst, *args, **kwargs)
        with self.disk_full_at(UNIT + ".json"), mock.patch("os.replace", held), \
                self.assertRaises(StudioError) as said:
            self.api.model_import(ADDRESS, str(other))
        self.assertIn("puts it back first", str(said.exception))
        self.assertNotIn("Errno", str(said.exception))
        self.assertNotEqual(self.state()["own"], was["own"])    # (as it was left: not all put back)
        got = self.api.model_resize(ADDRESS, 1.0)
        self.assertTrue((self.named(got) or {}).get("cut_off"))
        self.assertEqual(self.state()["own"], was["own"])
        self.assertFalse(self.undo_left())

    def test_no_room_even_for_the_copies_changes_nothing(self):
        self.imported(beast_glb())
        was = self.state()
        with mock.patch("shutil.copyfile", side_effect=OSError(28, "No space left on device")), \
                self.assertRaises(StudioError) as said:
            self.api.model_resize(ADDRESS, 1.5)
        self.assertIn("Make room on it", str(said.exception))
        self.assertEqual(self.state(), was)
        self.assertFalse(self.undo_left())

    def test_ordinary_fits_leave_no_copies_and_export_never_packs_them(self):
        from rusemod.package import files_of
        self.imported(beast_glb())
        self.api.model_resize(ADDRESS, 1.3)
        self.api.model_place(ADDRESS, [4, 0, 0])
        self.assertFalse(self.undo_left())
        (self.mod / UNDO / "x.glb").mkdir(parents=True)
        (self.mod / UNDO / "x.glb" / "manifest.json").write_text("{}", encoding="utf-8")
        (self.mod / "mod.toml").write_text('id = "m"\nversion = "1.0.0"\n', encoding="utf-8")
        self.assertFalse([p for p in files_of(self.mod) if UNDO in p.parts])


class TheSentences(_Case):
    def test_every_unit_at_once_says_how_many_were_fitted_and_skipped(self):
        """Finding 11: the job's message counted the skipped ones as done."""
        from test_horse_squad import finished
        self.imported(beast_glb())
        view = finished(self.api, self.api.models_resize_all("ground", "game")["job"], 120)
        self.assertEqual(view["message"], "1 model(s) fitted, 0 skipped.")
        self.path().write_text("{ cut short", encoding="utf-8")
        view = finished(self.api, self.api.models_resize_all("ground", "game")["job"], 120)
        self.assertEqual(view["message"], "0 model(s) fitted, 1 skipped.")
        from rusemod import buildtext
        self.assertEqual(buildtext.worded(view["message"], "fr"), "0 modèle(s) ajusté(s), 1 ignoré(s).")


class AnotherKindsRecord(unittest.TestCase):
    """Finding 12 (and 3 on his row): the bazooka man's record that can't be read, on the squad door."""

    def door(self):
        from test_fix_notes import UnitDoor
        door = UnitDoor()
        self.addCleanup(door.close)
        door.trip()
        door.trip(kind="bazooka")
        return door

    def test_said_in_words_naming_his_record_and_on_his_row(self):
        door = self.door()
        path = door.t.models / "Descriptor_Unit_My_Riflemen@bazooka.json"
        for text in ("{ cut short", "[1, 2]", "{}"):
            with self.subTest(record=text):
                path.write_text(text, encoding="utf-8")
                for call in (lambda: door.api.model_resize(door.SQUAD, 1.2),
                             lambda: door.api.model_place(door.SQUAD, [5, 0, 0])):
                    with self.assertRaises(StudioError) as said:
                        call()
                    self.assertIn("Descriptor_Unit_My_Riflemen@bazooka.json", str(said.exception))
                    self.assertNotIn("(None)", str(said.exception))
                row = [r for r in door.look()["kinds"] if r["kind"] == "bazooka"][0]
                self.assertTrue(row.get("record_unread"), row)

    def test_with_his_record_whole_the_squad_resizes(self):
        door = self.door()
        door.api.model_resize(door.SQUAD, 1.2)
        self.assertEqual(door.record("bazooka")["size"], 1.2)
        row = [r for r in door.look()["kinds"] if r["kind"] == "bazooka"][0]
        self.assertNotIn("record_unread", row)


for _cls in (_Case, TheStops, TheWrites, TheSentences):
    for _name in dir(base.Refit):   # (Refit's own tests run in test_refit_keeps)
        if _name.startswith("test_") and _name not in _cls.__dict__:
            setattr(_cls, _name, None)
del _cls, _name


if __name__ == "__main__":
    unittest.main()
