"""The one Blender button of a unit's page (ruse_studio.oneblender; the owner, 2026-11-13: "you can either take the whole
unit or ... select which ones you want to bring into Blender ... I want to bring everything but the bones. So then you
just uncheck the bones"; "Why is there two different buttons doing the same thing that then break sometimes?"): which
Blender its ticks open and which bring-back it then calls, with the doors themselves standing in (their own tests are
test_modelblender, test_squadblender; the keepers' are test_modelblender BonesKept and PaintKept)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from ruse_studio.api import StudioError
from ruse_studio.oneblender import ONE, OneBlenderCalls

SRC = Path(__file__).resolve().parents[1] / "src" / "ruse_studio"

E = "$/GFX/Everything/"


class Stand(OneBlenderCalls):
    """A Studio with one mod, a unit in it, and every door recording its call."""

    def __init__(self, root: Path, squad=False, own_bones=False, game_unit=False):
        self.root, self.squad, self.own_bones_, self.game_unit = root, squad, own_bones, game_unit
        self.calls = []
        self.door = (False, None)   # the squad's own Blender: (something to bring back, its opening's session)
        self.model_sent = True      # the model's own Blender: something sent, or Blender open on it
        self.running = False        # the last Blender still open after its bring-back

    def _mod_dir(self):
        return self.root / "mod"

    def _squad_door(self, address):
        return self.door

    def _model_door(self, address, kind):
        return self.model_sent

    def _door_open(self, address, state):
        return self.running   # (its Blender still open after a bring-back)

    def _look_models(self, address):
        return (["unit_model"], [])

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
        self.door = (True, f"session {len(self.calls)}")   # (a new session in the squad's state, Blender open on it)
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
        s.blender_open(E + "Descriptor_Unit_My_Riflemen", {"model": True, "soldiers": ["1", "3"], "paint": False})
        s.blender_back(E + "Descriptor_Unit_My_Riflemen")
        self.assertEqual(s.calls, [("squad_blender", ["1", "3"]), ("squad_blender_back", False, True)])

    def test_a_squad_on_the_game_soldiers_bones_has_no_bones_tick(self):
        """Its soldiers come back onto the game soldier's bones whatever Blender did to them: walked with real Blender
        2026-11-13 (onewalk.py), a bone moved 5 cm, Its bones ticked and unticked, the mod's model the same byte for
        byte. So there's no Bones tick to untick, and an untick sent anyway keeps nothing."""
        s = Stand(self.root, squad=True)
        parts = s.blender_parts(E + "Descriptor_Unit_My_Riflemen")
        self.assertEqual([p["id"] for p in parts["parts"]], ["model", "paint"])
        s.blender_open(E + "Descriptor_Unit_My_Riflemen", {"model": True, "bones": False})
        s.blender_back(E + "Descriptor_Unit_My_Riflemen")
        self.assertEqual(s.calls[-1], ("squad_blender_back", False, False))
        # (on bones of its own, the Generic Horse: Bones is there, and unticked it keeps them)
        horse = Stand(self.root, squad=True, own_bones=True)
        self.assertEqual([p["id"] for p in horse.blender_parts(E + "Descriptor_Unit_Generic_Horse")["parts"]],
                         ["model", "bones", "paint"])

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

    def test_a_game_squad_cant_go_and_bring_back_before_open_is_refused(self):
        s = Stand(self.root, squad=True, game_unit=True)   # (its uniform is every squad's: copy it first)
        self.assertFalse(s.blender_parts(E + "Descriptor_Unit_Soldat_US_Leger")["can"])
        with self.assertRaises(StudioError):
            s.blender_open(E + "Descriptor_Unit_Soldat_US_Leger", {"model": True})
        t = Stand(self.root)
        with self.assertRaises(StudioError):
            t.blender_back(E + "Descriptor_Unit_Tank")
        self.assertEqual(s.calls + t.calls, [])

    def test_a_game_tank_goes_with_its_paint_alone(self):
        """A game unit that isn't a squad keeps what the Look box's Repaint in Blender gave it (seen in the game): its
        paint; the owner, 2026-11-13, "Tanks too" to the one button on its page."""
        s = Stand(self.root, game_unit=True)
        parts = s.blender_parts(E + "Descriptor_Unit_M4_Sherman")
        self.assertEqual((parts["route"], [p["id"] for p in parts["parts"]], parts["can"]), ("paint", ["paint"], True))
        s.blender_open(E + "Descriptor_Unit_M4_Sherman", {"model": True, "paint": True})   # (no model to tick: paint)
        s.blender_back(E + "Descriptor_Unit_M4_Sherman")
        self.assertEqual(s.calls, [("look_open",), ("look_bring_back",)])

    def test_a_new_tank_goes_whole_and_comes_back_whole(self):
        """A new unit of this mod that isn't a squad: its whole model to Blender (the owner, 2026-11-13: "Tanks too")."""
        s = Stand(self.root)
        parts = s.blender_parts(E + "Descriptor_Unit_My_Sherman")
        self.assertEqual([p["id"] for p in parts["parts"]], ["model", "paint"])
        s.blender_open(E + "Descriptor_Unit_My_Sherman", {"model": True, "paint": False})
        s.blender_back(E + "Descriptor_Unit_My_Sherman")
        self.assertEqual(s.calls, [("model_blender", None), ("model_blender_back", None, False, True)])

    def test_no_mod_says_so(self):
        s = Stand(self.root, game_unit=True)
        s._mod_dir = lambda: None
        parts = s.blender_parts(E + "Descriptor_Unit_M4_Sherman")
        self.assertFalse(parts["can"])
        with self.assertRaisesRegex(StudioError, "Pick or make a mod first"):
            s.blender_open(E + "Descriptor_Unit_M4_Sherman", {"paint": True})

    def test_still_open_after_a_bring_back_reads_bring_back(self):
        s = Stand(self.root)
        s.blender_open(E + "Descriptor_Unit_My_Sherman", {"model": True})
        s.blender_back(E + "Descriptor_Unit_My_Sherman")
        self.assertFalse(s.blender_parts(E + "Descriptor_Unit_My_Sherman")["open"])
        s.running = True   # (Blender still open on it: it can send again)
        self.assertTrue(s.blender_parts(E + "Descriptor_Unit_My_Sherman")["open"])

    def test_what_was_opened_is_remembered_beside_the_units_blender_files(self):
        s = Stand(self.root)
        s.blender_open(E + "Descriptor_Unit_Tank", {"model": True, "bones": False})
        one = self.root / "mod/blender/Descriptor_Unit_Tank" / ONE
        self.assertEqual(json.loads(one.read_text(encoding="utf-8"))["door"], "model")
        self.assertTrue(s.blender_parts(E + "Descriptor_Unit_Tank")["open"])
        s.blender_back(E + "Descriptor_Unit_Tank")
        self.assertFalse(s.blender_parts(E + "Descriptor_Unit_Tank")["open"])


class OtherOpeners(unittest.TestCase):
    """The squad's own Blender opened by something other than the one button: Add a soldier (his Blender, on the squad
    card's same Bring my changes back), or the Studio before the one button (its Blender open, or its sending waiting,
    when the modder updates). Before this, Bring my changes back refused it ("Open this unit in Blender first"), and
    after an earlier opening it brought back with that opening's ticks (found by the squad page's tests 2026-11-13)."""
    SQUAD = E + "Descriptor_Unit_My_Riflemen"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_add_a_soldiers_blender_comes_back_with_nothing_unticked(self):
        s = Stand(self.root, squad=True)
        s.door = (True, "his session")   # (Add a soldier's Blender, the one button never used on this squad)
        got = s.blender_back(self.SQUAD)
        self.assertEqual((s.calls, got["door"]), ([("squad_blender_back", False, False)], "squad"))

    def test_a_blender_opened_before_the_update_comes_back(self):
        s = Stand(self.root, squad=True, own_bones=True)   # (the Generic Horse: the old Studio opened its squad Blender)
        s.door = (True, "the old Studio's session")
        s.blender_back(E + "Descriptor_Unit_Generic_Horse")
        self.assertEqual(s.calls, [("squad_blender_back", False, False)])

    def test_add_a_soldier_after_the_one_button_comes_back_without_its_ticks(self):
        s = Stand(self.root, squad=True)
        s.blender_open(self.SQUAD, {"model": True, "soldiers": ["1"], "paint": False})
        s.blender_back(self.SQUAD)
        s.door = (True, "Add a soldier's session")   # (Blender closed; then Add a soldier opened it again)
        s.blender_back(self.SQUAD)
        self.assertEqual(s.calls, [("squad_blender", ["1"]), ("squad_blender_back", False, True),
                                   ("squad_blender_back", False, False)])

    def test_the_same_blender_brought_back_twice_keeps_its_ticks(self):
        s = Stand(self.root, squad=True)
        s.blender_open(self.SQUAD, {"model": True, "paint": False})
        s.blender_back(self.SQUAD)
        s.blender_back(self.SQUAD)   # (Blender still open: changed again, sent again)
        self.assertEqual(s.calls[1:], [("squad_blender_back", False, True), ("squad_blender_back", False, True)])

    def test_add_a_soldier_beside_the_one_buttons_model_blender_comes_back_first(self):
        s = Stand(self.root, squad=True, own_bones=True)
        s.blender_open(E + "Descriptor_Unit_Generic_Horse", {"model": True, "kind": "", "bones": False})
        s.door = (True, "Add a soldier's session")   # (the model's Blender closed, its sending not brought back yet)
        s.blender_back(E + "Descriptor_Unit_Generic_Horse")
        s.door = (False, "Add a soldier's session")   # (he joined; then the model's own sending)
        s.blender_back(E + "Descriptor_Unit_Generic_Horse")
        self.assertEqual(s.calls, [("model_blender", None), ("squad_blender_back", False, False),
                                   ("model_blender_back", None, True, False)])

    def test_nothing_waiting_anywhere_is_still_refused(self):
        s = Stand(self.root, squad=True)
        with self.assertRaises(StudioError):
            s.blender_back(self.SQUAD)
        self.assertEqual(s.calls, [])

    def test_the_models_blender_with_nothing_sent_names_this_button(self):
        """The model's own refusal names its own Bring back the model, a button the squad card hasn't got."""
        s = Stand(self.root, squad=True, own_bones=True)
        s.blender_open(E + "Descriptor_Unit_Generic_Horse", {"model": True, "kind": ""})
        s.model_sent = False   # (Blender closed without Send to the R.U.S.E. Studio)
        with self.assertRaisesRegex(StudioError, "then Bring my changes back here"):
            s.blender_back(E + "Descriptor_Unit_Generic_Horse")
        self.assertEqual(s.calls, [("model_blender", None)])


class TheUnitPage(unittest.TestCase):
    """The one Blender button on the page of a unit that isn't a squad (the owner, 2026-11-13: "Tanks too"): app.js
    oneBlenderBox in the Model row's More, in the place of the paint's own box; its words in 11 languages naming the
    buttons as the page does; the field manual's Edit Units and Change a Squad naming them as the page does."""

    def setUp(self):
        from test_lookmoves import function_text, read
        self.app, self.fake = read("app.js"), read("fake-api.js")
        self.look = function_text(self.app, "lookMovesBox")
        self.box = function_text(self.app, "oneBlenderBox")
        self.words = tomllib.loads((SRC / "words.toml").read_text(encoding="utf-8"))

    def test_a_unit_that_isnt_a_squad_has_the_one_button_in_its_model_row(self):
        self.assertIn("if (!squad) more.push(oneBlenderBox(address, info, drawLook, changed));", self.look)
        self.assertIn("else if (paintable) more.push(repaintBox(address, info, drawLook, changed));", self.look)
        for call in ("api().blender_parts(address, state.lang)", "api().blender_open(address, t, state.lang)",
                     "api().blender_back(address, state.lang)"):
            self.assertIn(call, self.box)
        self.assertIn("textContent: open ? w.squad_blender_back : w.look_open, title: open ? w.tip_one_back : "
                      "w.tip_one_open", self.box)
        opening = self.box[self.box.index("const openBlender"):self.box.index("const bringBack")]
        self.assertLess(opening.index("ticks.ticks()"), opening.index("show();"))   # (read before drawn again)
        self.assertNotIn("look_back", self.box)   # (one Bring my changes back, not the paint's own Bring back)

    def test_its_words_in_eleven_languages_name_the_buttons_as_the_page_does(self):
        from test_lookmoves import LANGS
        for key, labels in (("one_how_unit", ("blender_model_send", "squad_blender_back")),
                            ("one_how_paint", ("squad_blender_back",))):
            self.assertEqual(set(self.words[key]), set(LANGS), key)
            for lang in LANGS:
                for label in labels:
                    with self.subTest(key=key, lang=lang, label=label):
                        self.assertIn(self.words[label][lang], self.words[key][lang])
            for lang in ("us", "fr", "sc"):   # (word for word on the stand-in page)
                self.assertIn(f'"{key}": {json.dumps(self.words[key][lang], ensure_ascii=False)}', self.fake)

    def test_the_field_manual_names_them_as_the_page_does(self):
        from test_lookmoves import LANGS
        wiki = SRC.parents[1] / "docs" / "wiki"
        edit = {"us": "Edit-Units", "fr": "fr/Modifier-les-unités", "ger": "ger/Einheiten-bearbeiten",
                "ita": "ita/Modificare-le-unità", "spa": "spa/Editar-unidades", "pol": "pol/Edycja-jednostek",
                "ru": "ru/Редактирование-юнитов", "cz": "cz/Úprava-jednotek", "jpn": "jpn/ユニットの編集",
                "sc": "sc/编辑单位", "fa": "fa/ویرایش-یگان‌ها"}
        squad = {"us": "Change-a-Squad", "fr": "fr/Changer-une-escouade", "ger": "ger/Einen-Trupp-ändern",
                 "ita": "ita/Cambiare-una-squadra", "spa": "spa/Cambiar-un-pelotón", "pol": "pol/Zmiana-oddziału",
                 "ru": "ru/Изменение-отряда", "cz": "cz/Změna-družstva", "jpn": "jpn/分隊の変更", "sc": "sc/修改小队",
                 "fa": "fa/تغییر-جوخه"}
        self.assertEqual(set(edit), set(LANGS))
        for lang in LANGS:
            text = (wiki / f"{edit[lang]}.md").read_text(encoding="utf-8")
            for key in ("model_blender", "look_open", "squad_blender_back", "one_parts"):
                with self.subTest(page=edit[lang], key=key):
                    self.assertIn(f"**{self.words[key][lang]}", text)
            text = (wiki / f"{squad[lang]}.md").read_text(encoding="utf-8")
            with self.subTest(page=squad[lang]):   # (a squad of the mod has no Repaint in Blender box any more)
                self.assertNotIn(f"**{self.words['unit_look'][lang]}**", text)
                self.assertIn(f"**{self.words['one_part_paint'][lang]}**", text)


if __name__ == "__main__":
    unittest.main()
