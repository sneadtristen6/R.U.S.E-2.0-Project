"""What a Bring back from Blender couldn't keep, said to the modder (the fix group "notes", round 2: fault L-F12 of the
silent-loss review of feat/anim-decoy-blender, tests/test_review_loss.py ThePage, and the recheck of round 1,
tests/test_recheck_notes.py): a material that came back with the plain 144 alpha (no shine or side colour of its own,
as no alpha picture went out to Blender under its name, or as its picture is gone from the Blender folder), one that
went out with one and didn't come back under its name, a picture swapped in Blender for one of another size, and on the
squad page an object Blender sent on no soldier.

TheAnswers: the Studio's own calls, as the page gets them through the window's bridge (JSON), carry it by name in every
place the page draws from: the Bring back's answer (its import's report "blender_alpha_lost" and "alpha_sizes", the
unit page's own_model and kinds rows, the squad page's reports and "left_out"), look() and squad_info afterwards (on the
first soldier who wears the model only), through a Resize and a Move (the same file fitted again: the record no longer
forgets it), and no more once a Bring back keeps everything. The Bring back with nothing lost carries none of it.

ThePage: the page's own code (ui/app.js and ui/squad.js, run in Node by tests/page_in_node.mjs as the recheck does it,
every call answered live by the Studio) drawn AFRESH, after the Bring back was done, from look() and squad_info alone:
what the recheck's tests leave out (they read the page right after its own click, which has the Bring back's answer).
In each of the 11 languages it names each thing lost, in that language, its blanks filled, on the model's own row (the
Model row, the heavy-weapon soldier's row under Its soldiers, the soldier's own line on the squad card), after a Resize
and a Move too; and the same page with nothing lost, or after a later Bring back that kept everything, warns of none.
Skipped when no Node is found, as the recheck's.

Tried on other code (scratch/animmodels/fix-notes/round2: make_trees.py, run_trees.py): on fddc462a 11 of these 13 fail
(the two with nothing lost pass, as they should), on round 1's uncommitted Studio edits 9 do (no page code; "renamed"
where a material made in Blender is no rename; a Resize forgets); and each mistake made on purpose in a copy of this fix
fails at least one: its words in English, a Resize or a Move that forgets, a model's loss said on every soldier who
wears it, a warning with nothing lost, said in the pop-up only, the record not told."""
from __future__ import annotations

import json
import re
import unittest
from contextlib import ExitStack
from pathlib import Path

import test_modelblender as mb   # (its ItsOwnShine and blender_sends as helpers, by the module's name)
import test_squadblender as sb   # (its BringItBack the same way)
from rusemod import gltf
from rusemod.dxt import png_bytes
from ruse_studio import api as studio
from test_recheck_notes import LANGS, PageCase, lines_of, text_of

HULL, TURRET = "test_tank_hull", "test_tank_turret"   # (the made-up game model's two materials, as they went out)
SAYING = ("model_alpha_none", "model_alpha_gone", "model_alpha_not_back", "model_alpha_size")   # (the page's words)


def plain(obj):
    """An answer as the page gets it (through the window's bridge: JSON)."""
    return json.loads(json.dumps(obj, default=str))


def lost_of(part) -> dict:
    """What a report or a row carries of what couldn't be kept (the page's alphaLostLines reads these two)."""
    return {k: part[k] for k in ("blender_alpha_lost", "alpha_sizes") if isinstance(part, dict) and k in part}


def swap_hull(work: Path) -> None:
    """In Blender, the hull's picture swapped for one of another size (4 x 4; its alpha that went out is 8 x 4)."""
    send = work / f"{work.name}.glb"
    doc, views = gltf.glb_views(send.read_bytes())
    for m in doc["materials"]:
        if m["name"] == HULL:
            img = doc["textures"][m["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]
            views[doc["images"][img]["bufferView"]] = png_bytes(bytes([90, 120, 30]) * 16, 4, 4)
    send.write_bytes(gltf.pack_glb(doc, views))


def hull_alpha_gone(work: Path) -> None:
    """The hull's alpha picture taken out of the Blender folder before the Bring back (as alpha.json names it)."""
    (work / json.loads((work / "alpha.json").read_text(encoding="utf-8"))["alpha"][HULL]).unlink()


class UnitDoor:
    """The unit page's Blender door on a new squad copying the US rifle squad, its riflemen and bazooka man drawing two
    models (test_recheck_notes.UnitPage's): test_modelblender.ItsOwnShine's made-up tank with pictures, the Studio's
    real export, Import model's real reading and fitting of pictures, Blender stood in (blender_sends), the Studio's own
    look()."""
    SQUAD = mb.SQUAD

    def __init__(self):
        t = self.t = mb.ItsOwnShine("test_a_tank_keeps_its_own_alpha_byte_for_byte")
        t.setUp()
        self.stack = ExitStack()
        self.stack.callback(t.tearDown)
        self.stack.enter_context(t.patched())
        api = self.api = t.api
        api._soldier_kinds = lambda address: {"fusilier": mb.RIFLEMAN, "bazooka": mb.BAZOOKA}
        api._look_models = lambda address: ([mb.BAZOOKA, mb.RIFLEMAN], [])
        api._soldier_figures = lambda address: [("GfxDescriptorFusilier", mb.RIFLEMAN),
                                                ("GfxDescriptorBazooka", mb.BAZOOKA)]
        api._soldiers = lambda address: True
        del api.look   # (the Studio's own look(): the page draws from it)

    def trip(self, kind=None, rename=None, before_back=None) -> dict:
        """Change it in Blender, Blender sends (`rename`: those materials renamed there), `before_back` done to the
        work folder, Bring back the model: its answer as the page gets it."""
        api = self.api
        opened = api.model_blender(self.SQUAD, "us", kind) if kind else api.model_blender(self.SQUAD)
        work = Path(opened["work"])
        mb.blender_sends(self.t.opened[-1], work / f"{work.name}.glb", rename)
        if before_back:
            before_back(work)
        return plain(api.model_blender_back(self.SQUAD, 1.0, kind) if kind else api.model_blender_back(self.SQUAD))

    def look(self) -> dict:
        return plain(self.api.look(self.SQUAD))

    def record(self, kind=None) -> dict:
        stem = "Descriptor_Unit_My_Riflemen" + (f"@{kind}" if kind else "")
        return json.loads((self.t.models / f"{stem}.json").read_text(encoding="utf-8"))

    def close(self):
        self.stack.close()


class SquadDoor:
    """The squad page's Blender door (test_squadblender.BringItBack's: the squad opened in Blender, Import model stood
    in), with the Studio's own look()."""

    def __init__(self, adding=False):
        t = self.t = sb.BringItBack("test_nothing_changed_at_all")
        t.setUp()
        self.stack = ExitStack()
        self.stack.callback(t.tearDown)
        del t.api.look
        self.stack.enter_context(t.patched())
        self.sid = "5"
        if adding:
            t.api.soldier_add(sb.SQUAD, "copy", "2")
            t.blender_opened()
            t.taking_in()
            self.sid = "new"
        soldier = next(s for s in t.manifest()["soldiers"] if s["id"] == self.sid)
        self.his, self.alpha = next(iter(soldier["alpha"].items()))   # (his material as it went, its alpha picture)

    def sends(self, figure: bytes, listed: dict | None = None, left_out=()) -> None:
        """Blender's Send: soldier `sid` sends `figure`, his line listing `listed` for alpha pictures (None: as it
        went), the others as they were opened."""
        t = self.t
        figures = {self.sid: figure} if self.sid == "new" else {**t.figures, self.sid: figure}
        t.blender_sends(figures, left_out=left_out)
        if listed is not None:
            sent = Path(t.manifest()["sent"])
            listing = json.loads(sent.read_text(encoding="utf-8"))
            listing["soldiers"][self.sid]["alpha"] = listed
            sent.write_text(json.dumps(listing), encoding="utf-8")

    def back(self) -> dict:
        with self.t.patched():
            return plain(self.t.api.squad_blender_back(sb.SQUAD, "us"))

    def info(self) -> dict:
        with self.t.patched():
            return plain(self.t.api.squad_info(sb.SQUAD, "us"))

    def close(self):
        self.stack.close()


class TheAnswers(unittest.TestCase):
    """What the page draws from carries what couldn't be kept, by name, as JSON (see the module's note)."""

    def unit(self) -> UnitDoor:
        door = UnitDoor()
        self.addCleanup(door.close)
        return door

    def squad(self, adding=False) -> SquadDoor:
        door = SquadDoor(adding)
        self.addCleanup(door.close)
        return door

    def test_a_renamed_material_is_carried_by_the_answer_its_look_and_its_record(self):
        door = self.unit()
        got = door.trip(rename={TURRET: "My turret"})
        want = {"blender_alpha_lost": {"none": ["My turret"], "not_back": [TURRET]}}
        self.assertEqual(lost_of(got["model"]), want)           # the Bring back's own report
        self.assertEqual(lost_of(got["own_model"]), want)       # look()'s part of its answer, the Model row's
        self.assertEqual(lost_of(door.look()["own_model"]), want)   # the page drawn again
        self.assertEqual(lost_of(door.record()["report"]), want)
        for rows in (got["kinds"], door.look()["kinds"]):        # (the riflemen's row is the same model's)
            self.assertEqual({r["kind"]: lost_of(r) for r in rows}, {"fusilier": want, "bazooka": {}})

    def test_a_picture_gone_and_a_picture_of_another_size_each_say_which(self):
        door = self.unit()
        self.assertEqual(lost_of(door.trip(before_back=hull_alpha_gone)["model"]),
                         {"blender_alpha_lost": {"gone": [HULL]}})
        door2 = self.unit()
        got = door2.trip(before_back=swap_hull)
        self.assertEqual(lost_of(got["model"]), {"alpha_sizes": [{"picture": HULL, "alpha": [8, 4], "colour": [4, 4]}]})
        self.assertEqual(lost_of(door2.look()["own_model"]), lost_of(got["model"]))

    def test_the_heavy_weapon_soldier_s_own_on_his_row_alone(self):
        door = self.unit()
        door.trip()                                              # the riflemen's model, nothing lost
        got = door.trip(kind="bazooka", rename={TURRET: "His turret"})
        want = {"blender_alpha_lost": {"none": ["His turret"], "not_back": [TURRET]}}
        self.assertEqual(lost_of(got["model"]), want)
        for rows in (got["kinds"], door.look()["kinds"]):        # his row says it, the riflemen's doesn't
            self.assertEqual({r["kind"]: lost_of(r) for r in rows}, {"fusilier": {}, "bazooka": want})
        self.assertEqual(lost_of(door.look()["own_model"]), {})

    def test_a_resize_and_a_move_keep_saying_it_and_a_bring_back_that_keeps_all_ends_it(self):
        """The same file fitted again has the same parts with the plain 144 (measured below): the record says so after
        a Resize, a Move and both again, its note once; a later Bring back with nothing lost says nothing."""
        door = self.unit()
        door.trip(rename={TURRET: "My turret"})
        door.trip(kind="bazooka", before_back=hull_alpha_gone)
        want = {"blender_alpha_lost": {"none": ["My turret"], "not_back": [TURRET]}}
        his = {"blender_alpha_lost": {"gone": [HULL]}}
        flat = mb.alphas_in(door.t.models / "Descriptor_Unit_My_Riflemen.glb")[TURRET]
        for step in (lambda: door.api.model_resize(door.SQUAD, 1.5), lambda: door.api.model_place(door.SQUAD, [10, 0, 0]),
                     lambda: door.api.model_resize(door.SQUAD, 0.8), lambda: door.api.model_place(door.SQUAD, [0, 0, 0])):
            got = plain(step())
            self.assertEqual(lost_of(got["model"]), want)
            look = door.look()
            self.assertEqual(lost_of(look["own_model"]), want)
            self.assertEqual({r["kind"]: lost_of(r) for r in look["kinds"]}, {"fusilier": want, "bazooka": his})
            for kind in (None, "bazooka"):   # (each record's note once, however many times it is fitted again)
                notes = door.record(kind)["report"]["notes"]
                self.assertEqual(sum("Back from Blender without an alpha picture" in n for n in notes), 1, notes)
            # (still so: the turret's alpha the plain 144, fitted again from the file brought back)
            self.assertEqual(mb.alphas_in(door.t.models / "Descriptor_Unit_My_Riflemen.glb")[TURRET], flat)
        self.assertEqual(set(flat), {144})
        door.trip(rename={"My turret": TURRET})                # brought back again, its turret's name as it went
        self.assertEqual(lost_of(door.look()["own_model"]), {})
        self.assertEqual(lost_of(door.record()["report"]), {})
        self.assertEqual(mb.alphas_in(door.t.models / "Descriptor_Unit_My_Riflemen.glb")[TURRET],
                         mb.GAME_ALPHA[TURRET])

    def test_nothing_lost_carries_nothing(self):
        door = self.unit()
        got = door.trip()
        self.assertEqual((lost_of(got["model"]), lost_of(got["own_model"])), ({}, {}))
        got = door.trip(kind="bazooka")
        self.assertEqual([lost_of(r) for r in got["kinds"]], [{}, {}])

    def test_the_squad_door_s_reports_and_his_line(self):
        """Soldier 5 sent back with his material replaced by one made in Blender ("Helmet paint"): his import's report
        says the new one has the plain 144 and his own didn't come back (the squad's Blender lists each material's
        alpha picture under its name at Send: his isn't listed), and so does his line of squad_info, his alone."""
        door = self.squad()
        door.sends(sb.glb_from(b"PNG-red", "Helmet paint"), listed={})
        got = door.back()
        want = {"blender_alpha_lost": {"none": ["Helmet paint"], "not_back": [door.his]}}
        self.assertEqual(got["changed"], ["5"])
        self.assertEqual(lost_of(got["reports"]["5"]), want)
        for info in (got, door.info()):
            self.assertEqual({s["id"]: lost_of(s) for s in info["soldiers"]},
                             {"1": {}, "2": {}, "3": {}, "4": {}, "5": want})

    def test_the_squad_door_s_picture_gone_its_join_and_objects_on_no_soldier(self):
        door = self.squad()
        Path(door.alpha).unlink()   # (his alpha picture, as the squad's opening wrote it, gone)
        door.sends(sb.glb_from(b"PNG-red", door.his), left_out=["My Cube"])
        got = door.back()
        self.assertEqual(lost_of(got["reports"]["5"]), {"blender_alpha_lost": {"gone": [door.his]}})
        self.assertEqual(got["left_out"], ["My Cube"])
        join = self.squad(adding=True)
        join.sends(sb.glb_from(b"PNG-new", "Helmet paint"))
        got = join.back()
        self.assertEqual(got["joined"], "5")
        self.assertEqual(lost_of(got["reports"]["5"]), {"blender_alpha_lost": {"none": ["Helmet paint"]}})
        self.assertEqual(lost_of(next(s for s in join.info()["soldiers"] if s["id"] == "5")),
                         {"blender_alpha_lost": {"none": ["Helmet paint"]}})

    def test_a_model_worn_by_several_soldiers_says_it_on_the_first_alone(self):
        """The riflemen's one model (from before each soldier had his own), worn by soldiers 1 to 4: what it couldn't
        keep is on soldier 1's line only, not four times."""
        door = self.squad()
        rifle = door.t.models / f"{sb.STEM}.glb"
        rifle.parent.mkdir(parents=True, exist_ok=True)
        rifle.write_bytes(b"glTF-riflemen")
        said = {"blender_alpha_lost": {"gone": ["Rifleman 1 1"]}}
        rifle.with_suffix(".json").write_text(json.dumps({"from": "x.glb", "report": {**said, "notes": []}}),
                                              encoding="utf-8")
        self.assertEqual({s["id"]: lost_of(s) for s in door.info()["soldiers"]},
                         {"1": said, "2": {}, "3": {}, "4": {}, "5": {}})

    def test_a_squad_bring_back_with_nothing_lost_carries_nothing(self):
        door = self.squad()
        door.sends(sb.glb_from(b"PNG-red", door.his))
        got = door.back()
        self.assertEqual((got["changed"], lost_of(got["reports"]["5"]), got["left_out"]), (["5"], {}, []))
        self.assertEqual([lost_of(s) for s in door.info()["soldiers"]], [{}] * 5)


class ThePage(PageCase, unittest.TestCase):
    """The page drawn afresh after the Bring back, in every language (see the module's note)."""
    BOTH = [HULL, TURRET]

    def unit_case(self, name, steps, click=("model_blender", 0)) -> dict:
        """A unit page (Look and moves, its Model and Its soldiers rows' More open): `steps(door)` done through the
        Studio before the page is drawn; then a button that changes nothing of it clicked (Change it in Blender:
        Blender opens, stood in), as page_in_node.mjs clicks one."""
        def make(lang):
            door = UnitDoor()
            try:
                steps(door)
            except BaseException:
                door.close()
                raise
            return door.api, door.close
        return {"name": name, "page": "look", "unit": {"address": mb.SQUAD, "name": "My Riflemen"}, "make": make,
                "click": {"text": click[0], "index": click[1]}}

    def squad_case(self, name, steps) -> dict:
        """The squad page (its card on squad_info, as showUnit draws it): `steps(door)` done before; then its one
        Blender button, Open in Blender, clicked (Blender opens, stood in: his line stays as squad_info has it)."""
        def make(lang):
            door = SquadDoor()
            try:
                steps(door)
            except BaseException:
                door.close()
                raise
            return door.t.api, door.close   # (the page's own calls too with the game's library stood in: SquadDoor's)
        return {"name": name, "page": "squad", "unit": {"address": sb.SQUAD, "name": "My Riflemen"}, "make": make,
                "click": {"text": "look_open"}}

    def lines_in(self, out: dict, cls: str) -> list:
        """The text of each element of class `cls` the page shows (none hidden, nor inside a hidden one)."""
        found = []

        def walk(node):
            if isinstance(node, str):
                return
            _tag, classes, hidden, kids = node
            if hidden:
                return
            if cls in classes.split():
                found.append(text_of(node))
            for k in kids:
                walk(k)
        if out.get("tree"):
            walk(out["tree"])
        return found

    @staticmethod
    def saying(text: str, lang: str) -> bool:
        """Whether `text` says something couldn't be kept: it has the longest fixed piece of one of the four sentences
        (SAYING) in `lang`."""
        words = studio.words(lang)
        return any(max(re.split(r"\{\w+\}", words[k]), key=len).strip() in text for k in SAYING)

    def losses_said(self, out: dict, lang: str, cls: str | None = None) -> list:
        """Every line and pop-up of a page (`cls`: of its elements of that class only) that says something couldn't be
        kept (saying)."""
        texts = self.lines_in(out, cls) if cls else [t for t, _w in lines_of(out, [])]
        return [t for t in texts if self.saying(t, lang)]

    def test_the_model_row_says_it_afresh_and_through_a_resize_and_a_move(self):
        renamed = lambda door: door.trip(rename={TURRET: "My turret"})   # noqa: E731
        moved = lambda door: (renamed(door), door.api.model_resize(door.SQUAD, 1.5),   # noqa: E731
                              door.api.model_place(door.SQUAD, [10, 0, 0]))
        got = self.run_page([self.unit_case("renamed", renamed), self.unit_case("moved", moved),
                             self.unit_case("clean", lambda door: door.trip())])
        for case in ("renamed", "moved"):
            self.assertEqual(self.problems(got, case, "clean", ["My turret", TURRET], also=self.BOTH), [])
        self.assertEqual(self.warned(got, "clean", self.BOTH), [])
        for lang in LANGS:   # (in the Model row's box, the riflemen's model's own: none under Its soldiers)
            for case in ("renamed", "moved"):
                own = [t for t in self.losses_said(got[lang][case], lang, "model-own") if "My turret" in t]
                self.assertTrue(own, (lang, case))
                self.assertEqual(self.losses_said(got[lang][case], lang, "model-kinds"), [], (lang, case))
            self.assertEqual(self.losses_said(got[lang]["clean"], lang), [], lang)

    def test_a_later_bring_back_that_keeps_everything_warns_of_nothing(self):
        def again(door):
            door.trip(rename={TURRET: "My turret"})
            door.api.model_resize(door.SQUAD, 1.5)
            door.trip(rename={"My turret": TURRET})   # (its old name again in Blender: its own comes back)
        got = self.run_page([self.unit_case("again", again)])
        for lang in LANGS:
            self.assertFalse(got[lang]["again"].get("error"), got[lang]["again"].get("error"))
            self.assertEqual(self.losses_said(got[lang]["again"], lang), [], lang)
            self.assertEqual([t for t, _w in lines_of(got[lang]["again"], []) if "My turret" in t], [], lang)

    def test_the_heavy_weapon_soldier_s_row_says_his_after_a_resize(self):
        def his(door):
            door.trip()
            door.trip(kind="bazooka", before_back=swap_hull)
            door.api.model_resize(door.SQUAD, 1.2)

        def clean(door):
            door.trip()
            door.trip(kind="bazooka")
            door.api.model_resize(door.SQUAD, 1.2)
        got = self.run_page([self.unit_case("his", his), self.unit_case("clean", clean)])
        self.assertEqual(self.problems(got, "his", "clean", [HULL], also=self.BOTH), [])
        self.assertEqual(self.warned(got, "clean", self.BOTH), [])
        for lang in LANGS:   # (on his row under Its soldiers: the riflemen's Model row says nothing of it)
            kinds = [t for t in self.losses_said(got[lang]["his"], lang, "model-kinds") if HULL in t]
            self.assertTrue(kinds, lang)
            self.assertEqual(self.losses_said(got[lang]["his"], lang, "model-own"), [], lang)
            self.assertEqual(self.losses_said(got[lang]["clean"], lang), [], lang)

    def test_the_squad_card_says_it_on_his_line_afresh(self):
        def made(door):
            door.sends(sb.glb_from(b"PNG-red", "Helmet paint"), listed={})
            door.back()

        def clean(door):
            door.sends(sb.glb_from(b"PNG-red", door.his))
            door.back()
        his = SquadDoor()
        name = his.his
        his.close()
        got = self.run_page([self.squad_case("made", made), self.squad_case("clean", clean)])
        self.assertEqual(self.problems(got, "made", "clean", ["Helmet paint", name]), [])
        self.assertEqual(self.warned(got, "clean", [name]), [])
        for lang in LANGS:   # (on soldier 5's line, the fifth, and on no other)
            lines = self.lines_in(got[lang]["made"], "squad-soldier")
            self.assertEqual(len(lines), 5, lang)
            self.assertEqual([i for i, t in enumerate(lines) if self.saying(t, lang)], [4], lang)
            self.assertIn("Helmet paint", lines[4], lang)
            self.assertEqual(self.losses_said(got[lang]["clean"], lang), [], lang)


if __name__ == "__main__":
    unittest.main()
