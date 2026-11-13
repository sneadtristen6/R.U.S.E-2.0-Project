"""The resize recheck, round 2 (fix/resize at 7c3a5408): a model record of the mod that can't be read.

A fit writes the model's record (files/models/<unit>.json) in place (StudioApi._fit_model: Path.write_text, not through
a .part file as RUSE Decoy's _record_lengths does). A write stopped part way (here: the disk full during a Resize, the
first third written, OSError 28; a Studio closed while writing leaves the same) leaves a record that isn't JSON. Then:
- Resize and Move are refused in words: "This unit has no model of its own to resize: import one first."
  (_own_model_record reads None), nothing changed: sound;
- Import model again, the same file, as that refusal says: _fit_model reads the record as {} (its except (OSError,
  ValueError)), so AnimModelCalls._record_more takes the unit for one with no model on bones of its own before
  (was_own False, no fingerprints, no _last_fit, no _carried_before), and the animation changed in RUSE Decoy goes back
  to the file's with nothing named: the report has no "not_kept", the page says "Model imported". The same mod's
  model file still carries its skeleton record and what the last fit took in (the reading _last_fit uses for a record
  from before the fingerprints), and the file it was made from is still there.
The fixer's own rule for the class (animmodel_calls.py's note): "A clip file or model file of the mod that can't be read
is never a reason to stop a fit: the file's animation takes its place and is named". Here the record is the file that
can't be read, and nothing is named. By reading, the same read (before = {}) also drops without a word what else of
the modder's the record held: the split chosen on the page (modelfit.kept_choices reads the same record) and the Custom
uniform the model took the place of ("copy_kept", which Take it out gives back). FAILS on 7c3a5408 by design until
fixed, at its last check; on db2abbfb it fails earlier, the Resize itself putting the change back (the review's F2):
not a regression, the class not closed on this route. On test_animmodel's made-up game (the round-1 recheck's
stand-ins, tests/test_recheck_resize.py, written so they run on the code before the fix too): no game needed."""
import unittest
from pathlib import Path
from unittest import mock

import test_recheck_resize as base
from ruse_studio.api import StudioError


class ARecordThatCantBeRead(base.ARecordFromBefore):
    # (ADamagedClipFile's made-up game and ARecordFromBefore's RUSE Decoy stand-in, not their tests)
    test_import_model_again_names_or_keeps_the_change_it_would_put_back = None

    def resize_with_the_disk_full(self) -> None:
        """A Resize whose record write stops a third of the way, OSError 28, as Python's own write leaves a file when
        the disk fills (the file opened and emptied first, then written).

        SETUP CHANGED by fixer B (the one check's mend, 2026-11-13), at the lead's call; every assertion of the test
        below is as it was. The record is now written through a .part file (animmodel_calls.write_record) and a fit is
        written together or not at all (FitUndo), so a Resize stopped there no longer leaves the record cut short: the
        stopped Resize is refused in words (a StudioError, not the OSError this setup asserted before) with the mod
        as it was. The state this test was written for, a record cut short by a write stopped in place, is what a
        Studio before the .part file left: it is made here as that write left it, the first third of the record's
        text, as tests/test_check_resize.py's test_a_record_cut_short_as_an_older_studio_s_stopped_write_left_it
        does."""
        record = self.target.with_suffix(".json")
        real = Path.write_text

        def full(path, data, *args, **kwargs):
            if Path(path).name.startswith(record.name):    # (the record's .part now)
                real(path, data[:len(data) // 3], *args, **kwargs)
                raise OSError(28, "No space left on device")
            return real(path, data, *args, **kwargs)
        with mock.patch.object(Path, "write_text", full), self.assertRaises(StudioError):
            self.api.model_resize(base.ADDRESS, 1.0)
        # (what an older Studio's in-place write stopped there left: the record cut to its first third)
        text = record.read_text(encoding="utf-8")
        record.write_text(text[:len(text) // 3], encoding="utf-8")

    def test_import_model_again_over_it_names_or_keeps_the_change_it_would_put_back(self):
        self.imported(base.beast_glb())
        changed = self.decoy("Walk")
        self.resize_with_the_disk_full()
        self.assertEqual(self.clips()["Walk"], changed)          # (the Resize itself kept it)
        # (space freed) Resize and Move: refused in words, nothing changed
        for call in (lambda: self.api.model_resize(base.ADDRESS, 1.0),
                     lambda: self.api.model_place(base.ADDRESS, [10, 0, 0])):
            with self.assertRaises(StudioError):
                call()
        self.assertEqual(self.clips()["Walk"], changed)
        # Import model again, the same file, as the refusal says
        got = self.imported(base.beast_glb())
        kept = self.clips()["Walk"] == changed
        named = ((got.get("model") or {}).get("not_kept") or {}).get("animations")
        self.assertTrue(kept or named == ["Walk"],
                        f"Import model again over a record that can't be read put the file's Walk back and named "
                        f"{named or 'nothing'}")


if __name__ == "__main__":
    unittest.main()
