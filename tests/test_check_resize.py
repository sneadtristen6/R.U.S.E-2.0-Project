"""The owner's one check of group "resize" on the joined code (join/final1 + 4a38ed65): a model's record written whole
or not at all, and a RUSE Decoy change kept or named through Resize, Move and Import model again when a record write
stops.

1. WriteStoppedAtThePart: the route tests/test_recheck_resize2.py was written for (a Resize whose record write stops
   part way, then Resize and Move refused, then Import model again putting the change back unsaid), by a setup that
   still works now the record goes through a .part file: the write stopped AT the .part (the disk full), or the
   .part not put in place (another program holding the record). Passes when the route is closed.
2. ImportAgainDiskFull: the fixer's own "not done" (round 3): Import model again with the disk full at the record
   write. The clips are already the file's when the record write fails; the modder is told "Make room on it, then try
   again"; trying again names nothing. FAILS by design while that stays so.
3. AnotherFileDiskFull: Import model of ANOTHER file stopped the same way, then Resize: what the mod holds then.
On test_animmodel's made-up game (tests/test_refit_keeps.py's stand-ins): no game needed."""
import json
import os
import unittest
from pathlib import Path
from unittest import mock

import test_refit_keeps as base
from ruse_studio.animmodel_calls import NOT_KEPT
from ruse_studio.api import StudioError

ADDRESS, UNIT, beast_glb = base.ADDRESS, base.UNIT, base.beast_glb


class _Check(base.Refit):
    def path(self) -> Path:
        return self.target.with_suffix(".json")

    def part(self) -> Path:
        return self.path().with_name(self.path().name + ".part")

    def named(self, got: dict):
        return (got.get("model") or {}).get(NOT_KEPT)

    def full_at_record(self):
        """Path.write_text with the disk full a third of the way into a write of the model's record (or its .part)."""
        real = Path.write_text
        record = self.path().name

        def full(path, data, *args, **kwargs):
            if Path(path).name.startswith(record):
                real(path, data[:len(data) // 3], *args, **kwargs)
                raise OSError(28, "No space left on device")
            return real(path, data, *args, **kwargs)
        return mock.patch.object(Path, "write_text", full)

    def held_at_replace(self):
        """os.replace refused for the record, as Windows refuses when another program has it open."""
        real = os.replace
        record = self.path()

        def held(src, dst, *args, **kwargs):
            if Path(dst) == record:
                raise PermissionError(13, "Access is denied", str(dst))
            return real(src, dst, *args, **kwargs)
        return mock.patch("os.replace", held)


class WriteStoppedAtThePart(_Check):
    def test_the_old_tests_route_is_closed(self):
        """recheck2's route: a Resize whose record write stops, then Resize and Move, then Import model again."""
        for how, stop in (("disk full at the .part", self.full_at_record), ("record held at the replace",
                                                                           self.held_at_replace)):
            with self.subTest(how=how):
                self.imported(beast_glb())
                self.imported(beast_glb())
                changed = self.decoy("Walk")
                before = self.path().read_bytes()
                with stop(), self.assertRaises(StudioError) as said:    # (in words, not Python's own)
                    self.api.model_resize(ADDRESS, 1.4)
                self.assertNotIn("Errno", str(said.exception))
                self.assertEqual(self.path().read_bytes(), before)     # (the record as it was, readable)
                json.loads(self.path().read_text(encoding="utf-8"))
                self.assertFalse(self.part().exists())
                self.assertEqual(self.clips()["Walk"], changed)        # (the Resize itself kept it)
                # Resize and Move are NOT refused now (the old test's "import one first"), and keep the change
                got = self.api.model_resize(ADDRESS, 1.0)
                self.assertEqual((self.clips()["Walk"], self.named(got)), (changed, None))
                got = self.api.model_place(ADDRESS, [10, 0, 0])
                self.assertEqual((self.clips()["Walk"], self.named(got)), (changed, None))
                # Import model again: names it
                got = self.imported(beast_glb())
                self.assertEqual((self.named(got) or {}).get("animations"), ["Walk"])

    def test_a_record_cut_short_as_an_older_studio_s_stopped_write_left_it(self):
        """A record left cut short (an in-place write stopped, before the .part): Resize refused in words naming the
        record, and Import model again names the change (the old test's last check)."""
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        text = self.path().read_text(encoding="utf-8")
        self.path().write_text(text[:len(text) // 3], encoding="utf-8")
        with self.assertRaises(StudioError) as said:
            self.api.model_resize(ADDRESS, 1.0)
        self.assertIn(f"{UNIT}.json", str(said.exception))
        self.assertEqual(self.clips()["Walk"], changed)
        got = self.imported(beast_glb())
        kept = self.clips()["Walk"] == changed
        named = (self.named(got) or {}).get("animations")
        self.assertTrue(kept or named == ["Walk"], f"named {named}")

    def test_a_part_left_from_an_earlier_stop_is_written_over(self):
        """A .part left behind (the Studio killed between the write and the replace): the next fit writes over it and
        leaves none."""
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        self.part().write_text('{"from": "half', encoding="utf-8")
        got = self.api.model_resize(ADDRESS, 1.2)
        self.assertEqual((self.clips()["Walk"], self.named(got)), (changed, None))
        self.assertFalse(self.part().exists())
        self.assertEqual(json.loads(self.path().read_text(encoding="utf-8"))["size"], 1.2)


class ImportAgainDiskFull(_Check):
    def test_import_model_again_stopped_at_the_record_then_tried_again_names_the_change(self):
        """The fixer's round-3 "not done". FAILS by design while the retry the words ask for loses the change unsaid."""
        self.imported(beast_glb())
        changed = self.decoy("Walk")
        old = self.path().read_bytes()
        with self.full_at_record(), self.assertRaises(StudioError) as said:
            self.imported(beast_glb())
        words = str(said.exception)
        facts = {"said": words,
                 "walk_is_the_file_s_now": self.clips()["Walk"] == self.clips_of_file()["Walk"],
                 "record_as_it_was": self.path().read_bytes() == old,
                 "part_left": self.part().exists()}
        # (what the modder is told: the disk, and to try again; nothing of the change)
        self.assertIn("Make room on it, then try again", words, facts)
        # space freed: tried again, as the words say
        got = self.imported(beast_glb())
        facts["retry_named"] = self.named(got)
        facts["walk_kept"] = self.clips()["Walk"] == changed
        print("\nIMPORT-AGAIN-DISK-FULL FACTS:", json.dumps(facts))
        self.assertTrue(facts["walk_kept"] or "Walk" in (words + json.dumps(facts["retry_named"])),
                        f"the RUSE Decoy change to Walk is gone and no word named it: {facts}")

    def test_resize_after_it_works_and_the_mod_stays_whole(self):
        """After the stopped Import model again: Resize and Move still go on (no stop), the record readable."""
        self.imported(beast_glb())
        self.decoy("Walk")
        with self.full_at_record(), self.assertRaises(StudioError):
            self.imported(beast_glb())
        self.api.model_resize(ADDRESS, 1.3)
        self.api.model_place(ADDRESS, [5, 0, 0])
        rec = json.loads(self.path().read_text(encoding="utf-8"))
        self.assertEqual(rec["size"], 1.3)
        self.assertEqual(sorted(a["name"] for a in rec["animations"]), sorted(self.clips()))


class AnotherFileDiskFull(_Check):
    def test_import_of_another_file_stopped_at_the_record_then_resize(self):
        """Import model of ANOTHER file (its Run made faster) with the disk full at the record write; the modder makes
        room and clicks Resize. Reports what the mod holds: which file's animations, and whether anything was said."""
        self.imported(beast_glb())
        a_run = self.clips()["Run"]
        other = self.src.with_name("other.glb")
        other.write_bytes(beast_glb(step=0.3))
        with self.full_at_record(), self.assertRaises(StudioError):
            self.api.model_import(ADDRESS, str(other))
        between = self.clips()["Run"]
        rec = json.loads(self.path().read_text(encoding="utf-8"))
        facts = {"between_run_is_other": between != a_run, "record_from_is_first": rec.get("from") == str(self.src)}
        got = self.api.model_resize(ADDRESS, 1.0)
        facts["after_resize_run_is_other"] = self.clips()["Run"] != a_run
        facts["resize_named"] = self.named(got)
        print("\nANOTHER-FILE-DISK-FULL FACTS:", json.dumps(facts))
        # (a fact for the owner: the model the mod held between, the other file's, and what Resize then fitted)
        self.assertTrue(facts["after_resize_run_is_other"] or facts["resize_named"], facts)


class ARecordNotAnObject(_Check):
    """Round 3's class "a record ... not a JSON object" (its own test writes "[1, 2]"): Import model again, Resize and
    Move say it in words. The unit page's model box (look()) and Take it out read the same record too. FAIL while they
    stop with Python's own error (AttributeError) and nothing says what to change."""
    def damaged(self, text: str) -> None:
        self.imported(beast_glb())
        self.path().write_text(text, encoding="utf-8")

    def test_the_unit_page_s_model_box_opens(self):
        from ruse_studio.api import StudioApi
        api = self.api
        api._paint_of = lambda address: []
        api._blender = lambda: None
        api._kind_rows = lambda address: []
        api._look_folder = lambda address: self.mod / "look"
        api._soldiers = lambda address: False
        api._model_kept = lambda address, kinds=None: None
        for text in ("[1, 2]", "null", "\"text\""):
            with self.subTest(record=text):
                self.damaged(text)
                try:
                    got = StudioApi.look(api, ADDRESS)
                except StudioError:
                    continue      # (in words: fine)
                except Exception as exc:  # noqa: BLE001
                    self.fail(f"the unit page's model box stops with Python's words: {type(exc).__name__}: {exc}")
                self.assertIsInstance(got.get("own_model"), dict)

    def test_take_it_out_takes_it_out(self):
        self.api._soldier_kinds = lambda address: {}
        for text in ("[1, 2]", "null"):
            with self.subTest(record=text):
                self.damaged(text)
                try:
                    got = self.api.model_import_remove(ADDRESS)
                except StudioError:
                    continue
                except Exception as exc:  # noqa: BLE001
                    self.fail(f"Take it out stops with Python's words: {type(exc).__name__}: {exc}")
                self.assertTrue(got["model_out"])
                self.assertFalse(self.target.exists())


class APartLeftGoesOut(unittest.TestCase):
    def test_a_record_s_part_left_behind_carries_no_folder_into_an_export(self):
        """A <unit>.json.part left behind (the Studio killed between write_record's write and its replace): Export
        packs every file under files/ (rusemod.package.files_of), and only .json/.glb/text files have the maker's
        folders taken out (packed_bytes). FAILS while a .part goes out as it is. Likelihood: the Studio must end in
        the instant between the two."""
        import tempfile
        from rusemod.package import files_of, packed_bytes
        with tempfile.TemporaryDirectory() as tmp:
            mod = Path(tmp)
            (mod / "mod.toml").write_text('id = "m"\nversion = "1.0.0"\n', encoding="utf-8")
            part = mod / "files" / "models" / f"{UNIT}.json.part"
            part.parent.mkdir(parents=True)
            part.write_text(json.dumps({"from": "C:\\Users\\someone\\models\\beast.glb"}, indent=1), encoding="utf-8")
            if part not in files_of(mod):
                return
            out = packed_bytes(part)
            data = part.read_bytes() if out is None else out
            self.assertNotIn(b"someone", data, "a record's .part goes out with the maker's folder in it")


for _cls in (_Check, WriteStoppedAtThePart, ImportAgainDiskFull, AnotherFileDiskFull, ARecordNotAnObject):
    for _name in dir(base.Refit):   # (Refit's own tests run in test_refit_keeps)
        if _name.startswith("test_") and _name not in _cls.__dict__:
            setattr(_cls, _name, None)
del _cls, _name   # (left at the module's top, the loader would run the last class twice)


if __name__ == "__main__":
    unittest.main()
