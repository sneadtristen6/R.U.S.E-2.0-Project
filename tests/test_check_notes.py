"""The one check of the fix group "notes" on the joined code (join/final1, 2026-11-12): what a Bring back from Blender
couldn't keep of a part's shine and side colour, said on the page, where it meets the other groups' changes (resize's
single reading of the record before the fit and its not-kept words, the record written whole).

Routes tried, each with the Studio's own calls (test_fix_notes' doors: test_modelblender's and test_squadblender's
stand-ins for the game and Blender) and, where it is the page's, the page's own code run in Node (page_in_node.mjs,
as test_recheck_notes and test_fix_notes run it), in all 11 languages:
- Resize and Move after a Bring back whose record's words on the loss are damaged (by hand, or by another program):
  a refusal in words, never Python's own error;
- a record written by the Studio before this fix (feat/anim-decoy-blender 07a688b5: "blender_alpha" and the English
  notes, no "blender_alpha_lost"): what it says is still said;
- a Bring back that both couldn't read the model's record (resize's not-kept words) and couldn't keep a part's shine:
  both said in its pop-up, and the pop-up waits to be closed; on the Model row and on the heavy-weapon soldier's row.
Skipped when no Node is found (the page cases), as the recheck's."""
from __future__ import annotations

import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import test_modelblender as mb
import test_recheck_notes as rn
from ruse_studio import api as studio
from test_fix_notes import TURRET, UnitDoor, lost_of, plain
from test_recheck_notes import LANGS, PageCase

RIFLEMEN = "Descriptor_Unit_My_Riflemen"


def record_path(door: UnitDoor, kind=None) -> Path:
    return door.t.models / f"{RIFLEMEN}{'@' + kind if kind else ''}.json"


class DamagedWords(unittest.TestCase):
    """A Resize or a Move after a Bring back, the record's "blender_alpha_lost" in a shape this Studio never writes (a
    record edited by hand, or written by another program). Before the fix the report wasn't read on a Resize, so these
    records resized; with the fix, keep_said reads it."""

    SHAPES = {"a list": ["My turret"], "a word": "My turret", "a number in a list's place": {"none": 5},
              "a list of lists": [["none", "My turret"]]}

    def test_a_resize_and_a_move_say_a_damaged_record_in_words_or_go_on(self):
        out = []
        for name, shape in self.SHAPES.items():
            for step in ("resize", "place"):
                door = UnitDoor()
                try:
                    door.trip(rename={TURRET: "My turret"})
                    path = record_path(door)
                    data = json.loads(path.read_text(encoding="utf-8"))
                    data["report"]["blender_alpha_lost"] = shape
                    path.write_text(json.dumps(data), encoding="utf-8")
                    try:
                        if step == "resize":
                            door.api.model_resize(door.SQUAD, 1.5)
                        else:
                            door.api.model_place(door.SQUAD, [10, 0, 0])
                    except studio.StudioError:
                        pass   # (a refusal in words: what the modder can act on)
                    except Exception as exc:   # noqa: BLE001 - Python's own error, as the page would show it
                        out.append(f"{step}, {name}: {type(exc).__name__}: {exc}")
                finally:
                    door.close()
        self.assertEqual(out, [])


class OlderRecord(unittest.TestCase):
    """A model brought back from Blender by the Studio before this fix (07a688b5, the shine door: its record's report
    has "blender_alpha", each material's word in English, and the English notes, but no "blender_alpha_lost")."""

    def older(self) -> UnitDoor:
        door = UnitDoor()
        self.addCleanup(door.close)
        door.trip(rename={TURRET: "My turret"})
        path = record_path(door)
        data = json.loads(path.read_text(encoding="utf-8"))
        data["report"].pop("blender_alpha_lost")   # (as that Studio wrote it)
        path.write_text(json.dumps(data), encoding="utf-8")
        return door

    def test_what_an_older_record_says_reaches_the_page(self):
        """look()'s own_model, which the Model row draws from, carries nothing for alphaLostLines: the record says
        "My turret" has the plain 144 (in English), the page says nothing."""
        door = self.older()
        self.assertIn("plain 144", json.dumps(door.record()["report"]["blender_alpha"]))
        self.assertNotEqual(lost_of(door.look()["own_model"]), {})

    def test_an_older_record_s_note_survives_a_resize(self):
        """After a Resize the record's English note on "My turret" is gone, while the part still has the plain 144."""
        door = self.older()
        self.assertTrue(any("My turret" in n for n in door.record()["report"]["notes"]))
        door.api.model_resize(door.SQUAD, 1.5)
        self.assertEqual(set(mb.alphas_in(door.t.models / f"{RIFLEMEN}.glb")[TURRET]), {144})
        self.assertTrue(any("My turret" in n for n in door.record()["report"]["notes"]),
                        door.record()["report"]["notes"])


# page_in_node.mjs as it is, but the page's own pop-ups (app.js say) drawn as the window draws them, and each card's
# state read at the end: [its text, its classes, whether it waits to be closed (stayToast: no fading on the mouse)]
SAY_STUB = 'ctx.say = (text, kind) => { said.push([String(text ?? ""), kind || ""]); return null; };'
SAY_REAL = ('const realSay = ctx.say;\n'
            'ctx.say = (text, kind) => { said.push([String(text ?? ""), kind || ""]); return realSay(text, kind); };')
OUT_STUB = "said: said.slice(), calls,"
OUT_REAL = ('said: said.slice(), calls, cards: under(document.getElementById("status"), ".toast").map((c) => '
            '[c._text || "", c.className, c.onmouseleave === null]),')


class BothSaid(PageCase, unittest.TestCase):
    """The join of fix/resize and fix/notes on the unit page's Bring back: the model's record couldn't be read (resize's
    "not_kept" record: what else it held, the bone chosen under Its two halves and a Custom uniform, said as not kept)
    and a part came back with the plain shine (notes'). Both said in the Bring back's pop-up in every language, and the
    pop-up waits to be closed."""

    def setUp(self):
        text = rn.PAGE.read_text(encoding="utf-8")
        self.assertIn(SAY_STUB, text)
        self.assertIn(OUT_STUB, text)
        d = Path(tempfile.mkdtemp(dir=rn.TMP))
        self.addCleanup(shutil.rmtree, d, True)
        page = d / "page_cards_in_node.mjs"
        page.write_text(text.replace(SAY_STUB, SAY_REAL).replace(OUT_STUB, OUT_REAL), encoding="utf-8")
        old = rn.PAGE
        rn.PAGE = page
        self.addCleanup(setattr, rn, "PAGE", old)

    def case(self, name, kind=None, unreadable=True) -> dict:
        def make(lang):
            door = UnitDoor()
            try:
                door.trip()                                    # (the model in, its record written)
                if kind:
                    door.trip(kind=kind)
                if unreadable:
                    record_path(door, kind).write_text("{ cut short", encoding="utf-8")
                opened = door.api.model_blender(door.SQUAD, lang, kind)
                work = Path(opened["work"])
                mb.blender_sends(door.t.opened[-1], work / f"{work.name}.glb", {TURRET: "My turret"})
            except BaseException:
                door.close()
                raise
            return door.api, door.close
        return {"name": name, "page": "look", "unit": {"address": mb.SQUAD, "name": "My Riflemen"}, "make": make,
                "click": {"text": "model_blender_back", "index": 1 if kind else 0,
                          "title": "tip_model_kind_blender_back" if kind else "tip_model_blender_back_kinds"}}

    @staticmethod
    def piece(word: str) -> str:
        return max(re.split(r"\{\w+\}", word), key=len).strip()

    def check(self, got, name) -> list:
        out = []
        for lang in LANGS:
            res = got[lang][name]
            if res.get("error"):
                out.append(f"{lang}: the page stopped: {res['error'].splitlines()[0]}")
                continue
            w = studio.words(lang)
            record, shine = self.piece(w["model_kept_not_record"]), self.piece(w["model_alpha_none"])
            said = [t for t, _k in res.get("said") or []]
            if not any(record in t for t in said):
                out.append(f"{lang}: the pop-up doesn't say the record couldn't be read: {said}")
            if not any(shine in t and "My turret" in t for t in said):
                out.append(f"{lang}: the pop-up doesn't name 'My turret': {said}")
            staying = [c for c in res.get("cards") or [] if shine in c[0]]
            if not staying or not all(c[2] for c in staying):
                out.append(f"{lang}: the pop-up naming 'My turret' doesn't wait to be closed: {res.get('cards')}")
        return out

    def test_the_model_row_s_bring_back_says_both_and_waits(self):
        got = self.run_page([self.case("both")])
        self.assertEqual(self.check(got, "both"), [])

    def test_the_heavy_weapon_soldier_s_bring_back_says_both_and_waits(self):
        """His own Bring back the model under Its soldiers: his record unreadable (it can hold a Custom uniform his
        model took the place of), his turret renamed in Blender."""
        got = self.run_page([self.case("his", kind="bazooka")])
        self.assertEqual(self.check(got, "his"), [])


if __name__ == "__main__":
    unittest.main()
