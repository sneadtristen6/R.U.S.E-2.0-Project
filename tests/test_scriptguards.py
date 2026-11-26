"""Guards on four places where the game's own scripts stop the game with mods on (rusemod.scriptguards): each
compiled guard is of its source; it is joined after the game's module, on top of what the build did to the same script
pack; a guard that carries on after the game's own function is joined only to that function, so a mod's own script is
left as the mod has it, with a note; a game without the script packs gets nothing; and nothing here stops a build.
What each guard does with the game's own function is checked where the game's scripts are (the project's template
compiler runs every case under the game's Python before it writes scriptguards_compiled.py)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import os
import unittest
from pathlib import Path

from rusemod import pyscript
from rusemod import scriptguards as sg
from rusemod.edat import Edat
from test_ownbuildings import game_module

GAME = Path(os.environ.get("RUSE_GAME", "D:/Steam/steamapps/common/R.U.S.E"))
NEEDS = {"menu": (b"Menu",), "strategic_ia": (b"DescriptorIAAll",), "units": (b"ActionMuteUnit", b"leveldesign"),
         "condition": (b"ConditionDetectUnitDansZoneDetection", b"_killable")}


def xyz(names) -> bytes:
    return pyscript.write_xyz(pyscript.Xyz(b"\0" * 16, game_module(names)))


def made_up_zz(menu=NEEDS["menu"], ia=NEEDS["strategic_ia"], units=NEEDS["units"],
               condition=NEEDS["condition"]) -> Edat:
    """ZZ_Win.dat with the four modules the guards go after, as made-up modules that set the names they need (and
    none of the game's own functions). `condition`: the names, or the module's own bytes (marshal)."""
    from fixtures import make_edat
    eugen = make_edat([("dir", "genpython\\1000\\codeia\\python\\eugen\\headup\\", [("file", "menu.xyz", xyz(menu))])])
    cond = condition if isinstance(condition, bytes) else game_module(condition)
    solo = make_edat([("dir", "genpython\\1000\\codeia\\python\\eugensolo\\leveldesignsolo\\", [
        ("file", "strategic_ia.xyz", xyz(ia)), ("file", "units.xyz", xyz(units)),
        ("file", "condition.xyz", pyscript.write_xyz(pyscript.Xyz(b"\0" * 16, cond)))])])
    return Edat(make_edat([("dir", "genpython\\", [("file", "eugen.ipk", eugen), ("file", "eugensolo.ipk", solo)])]))


def module_with_get_unit_list(body: bytes) -> bytes:
    """A made-up condition module whose class ConditionDetectUnitDansZoneDetection has a get_unit_list doing `body`
    (a mod's own), setting the names the zone guard reads."""
    func = pyscript.Code(2, 2, 1, 67, body, (None,), (), (b"self", b"world"), (), (), b"condition.py",
                         b"get_unit_list", 322, b"")
    cls = pyscript.Code(0, 0, 1, 66, b"", (func,), (), (), (), (), b"condition.py",
                        b"ConditionDetectUnitDansZoneDetection", 305, b"")
    code = b"d\x00\x00Z\x00\x00d\x00\x00Z\x01\x00d\x01\x00S"   # the class and _killable set (to constants), then None
    mod = pyscript.Code(0, 0, 1, 64, code, (cls, None), (b"ConditionDetectUnitDansZoneDetection", b"_killable"), (),
                        (), (), b"condition.py", b"<module>", 1, b"")
    return pyscript.dump(mod)


def module_in(zz: Edat, changed: dict, name: str) -> pyscript.Code:
    pack_path, member_path = sg.SCRIPTS[name]
    entry = zz.entry(pack_path)
    pack = Edat(changed.get(entry.path) or bytes(zz.read(entry)))
    return pyscript.load(pyscript.read_xyz(bytes(pack.read(pack.entry(member_path)))).payload)


class Guards(unittest.TestCase):
    def test_compiled_of_their_sources(self):
        from rusemod.scriptguards_compiled import COMPILED, GAME_FUNCTIONS
        self.assertEqual(sorted(sg.SOURCES), sorted(sg.SCRIPTS))
        self.assertEqual(sorted(sg.SOURCES), sorted(sg.FUNCTIONS))
        self.assertEqual(sorted(sg.SOURCES), sorted(sg.WHAT))
        self.assertEqual(sorted(sg.SOURCES), sorted(COMPILED))
        for name in sg.SOURCES:
            code = sg.template(name)
            self.assertIsInstance(code, pyscript.Code)
            self.assertIn(sg.KEPT[name], pyscript.stored_names(code))
            self.assertIn(sg.KEPT[name].decode(), sg.SOURCES[name])
        self.assertEqual(sorted(GAME_FUNCTIONS), sorted(n for n, f in sg.FUNCTIONS.items() if f is not None))

    def test_each_guard_counts_when_it_steps_in(self):
        """(2026-11-13) A guard that steps in adds 1 to the count the game's own text says before a later script-error
        stop ("Previously ignored errors: N"), so a crash report says how often guards kept the game going; only in
        its stepping-in branch (the cases, each guard against the game's own function under the game's Python, are
        run by the template compiler: count_after in its checker)."""
        self.assertIn("sys.ignore_count = getattr(sys, 'ignore_count', 0) + 1", sg.COUNT)
        for name, source in sg.SOURCES.items():
            self.assertIn(sg.COUNT, source, name)
            self.assertEqual(source.count("_r2g_count()"), 2, name)   # its definition, and one call
        menu, ia, units = sg.SOURCES["menu"], sg.SOURCES["strategic_ia"], sg.SOURCES["units"]
        self.assertIn("            raise\n    _r2g_count()\n    for techno_fille", menu)
        self.assertIn("    if no_ia:\n        _r2g_count()\n        return None", ia)
        self.assertIn("        except RuntimeError:\n            gone = 1\n    if gone:\n        _r2g_count()", units)
        self.assertIn("            raise\n    _r2g_count()\n    return _killable.KillableList()",
                      sg.SOURCES["condition"])

    def test_a_changed_source_is_refused_until_compiled_again(self):
        old = sg.SOURCES["menu"]
        sg.SOURCES["menu"] = old + "\n# changed\n"
        try:
            with self.assertRaisesRegex(sg.GuardError, "compile it again"):
                sg.template("menu")
        finally:
            sg.SOURCES["menu"] = old

    def test_each_guard_reads_only_what_the_games_module_or_the_guard_sets(self):
        for name in sg.SOURCES:
            joined = pyscript.load(pyscript.append_module(game_module(NEEDS[name]), sg.template(name)))
            before = pyscript.load(game_module(NEEDS[name]))
            self.assertEqual(joined.code[:len(before.code) - 4], before.code[:-4], name)
            self.assertEqual(joined.names[:len(before.names)], before.names, name)
            with self.assertRaises(pyscript.ScriptError):
                pyscript.append_module(game_module((b"SomethingElse",)), sg.template(name))

    def test_a_game_without_the_script_packs_gets_nothing_and_no_note(self):
        from fixtures import make_edat
        empty = Edat(make_edat([("dir", "genpython\\", [("file", "other.ipk", make_edat([]))])]))
        self.assertEqual(sg.script_changes(empty, {}), ({}, [], []))
        self.assertEqual(sg.script_changes(None, {}), ({}, [], []))

    def test_a_mods_own_function_is_left_as_the_mod_has_it(self):
        """The made-up modules hold none of the game's own functions: the three guards that carry on after the game's
        function are left out with a note; the one that only decides whether to call it is joined."""
        zz = made_up_zz()
        changed, added, notes = sg.script_changes(zz, {})
        self.assertEqual(added, ["strategic_ia"])
        self.assertEqual(len(notes), 3)
        self.assertTrue(all("isn't the game's" in n and "left as the mod has it" in n for n in notes), notes)
        self.assertIn(sg.KEPT["strategic_ia"], pyscript.stored_names(module_in(zz, changed, "strategic_ia")))
        self.assertNotIn(sg.KEPT["units"], pyscript.stored_names(module_in(zz, changed, "units")))
        self.assertNotIn(sg.KEPT["menu"], pyscript.stored_names(module_in(zz, changed, "menu")))
        self.assertNotIn(sg.KEPT["condition"], pyscript.stored_names(module_in(zz, changed, "condition")))

    def test_a_module_without_the_name_gives_a_note_not_an_error(self):
        zz = made_up_zz(ia=(b"NotTheClass",))
        changed, added, notes = sg.script_changes(zz, {})
        self.assertEqual((changed, added), ({}, []))
        self.assertEqual(len(notes), 4)
        self.assertTrue(any("DescriptorIAAll" in n for n in notes), notes)

    def test_the_zone_guard_goes_on_the_game_s_own_zone_check_only(self):
        """(2026-11-26, FL-101's zone check on a zone with no zone info) The fourth guard goes on the mission scripts'
        condition module, on ConditionDetectUnitDansZoneDetection.get_unit_list, and only when that function is the
        game's own (its mark as the template compiler recorded it from the game's module): a mod's own get_unit_list
        is left as the mod has it, with a note naming it, and the rest of the pack's changes still go in."""
        from rusemod.scriptguards_compiled import GAME_FUNCTIONS
        self.assertEqual(sg.SCRIPTS["condition"], ("genpython\\eugensolo.ipk", "genpython\\1000\\codeia\\python\\"
                                                   "eugensolo\\leveldesignsolo\\condition.xyz"))
        self.assertEqual(sg.FUNCTIONS["condition"], (b"ConditionDetectUnitDansZoneDetection", b"get_unit_list"))
        self.assertEqual(GAME_FUNCTIONS["condition"],
                         "805c770e44e491078fe379597603e6f1fa1d4f80b460b8d959d4cf6d7acc9a05")
        self.assertEqual(sg.KEPT["condition"], b"_r2g_game_zone_units")
        own = module_with_get_unit_list(b"g\x00\x00S")   # a mod's own: return []
        self.assertIsNotNone(sg.function_sha(pyscript.load(own), *sg.FUNCTIONS["condition"]))
        zz = made_up_zz(condition=own)
        changed, added, notes = sg.script_changes(zz, {})
        self.assertEqual(added, ["strategic_ia"])   # the same pack's other guard still goes in
        said = [n for n in notes if n.startswith(sg.WHAT["condition"])]
        self.assertEqual(len(said), 1, notes)
        self.assertIn("this set's own ConditionDetectUnitDansZoneDetection.get_unit_list isn't the game's", said[0])
        self.assertIn("left as the mod has it", said[0])
        pack_path, member_path = sg.SCRIPTS["condition"]
        pack = Edat(changed[zz.entry(pack_path).path])   # (the pack is changed: the other guard went in)
        self.assertEqual(pyscript.read_xyz(bytes(pack.read(pack.entry(member_path)))).payload, own)   # the mod's
        self.assertIn(sg.KEPT["strategic_ia"], pyscript.stored_names(module_in(zz, changed, "strategic_ia")))

    def test_the_zone_guard_steps_in_only_where_the_zone_has_no_info(self):
        """(2026-11-26) The game's own get_unit_list runs first and unchanged; only an AttributeError is caught, and
        only when the zone's info is None and the error is the one of reading its radius (the players' text, word for
        word); then the count goes up by one and the check gets the game's own empty list, as for a zone with no units
        (the game's scan only goes through it). Any other error goes on as it was. What it does against the game's own
        compiled function under the game's Python is run by the template compiler (its checker's condition cases)."""
        source = sg.SOURCES["condition"]
        self.assertIn("_r2g_game_zone_units = ConditionDetectUnitDansZoneDetection.get_unit_list\n", source)
        self.assertIn("    try:\n        return _r2g_game_zone_units(self, world)\n"
                      "    except AttributeError, error:\n        if not _r2g_no_zone_info(self, error):\n"
                      "            raise\n", source)
        self.assertIn("self.Detecteur.zone_info is None and error.args == "
                      "(\"'NoneType' object has no attribute 'radius'\",)", source)
        self.assertEqual(source.count("except AttributeError"), 1)
        self.assertEqual(source.count("except:"), 2)   # the count's and the zone check's own: they never stop anything
        self.assertTrue(source.endswith("\nConditionDetectUnitDansZoneDetection.get_unit_list = _r2g_zone_units\n"))
        # it reads nothing but the game's class, the game's own list maker and built-ins
        template = sg.template("condition")
        read = pyscript._read_names(template) - pyscript.stored_names(template) - pyscript.BUILTINS
        self.assertEqual(read, {b"ConditionDetectUnitDansZoneDetection", b"_killable"})
        self.assertIn(b"AttributeError", pyscript._read_names(template))
        with self.assertRaisesRegex(pyscript.ScriptError, "_killable"):
            pyscript.append_module(game_module((b"ConditionDetectUnitDansZoneDetection",)), template)

    def test_on_top_of_what_the_build_did_to_the_pack_and_once_only(self):
        zz = made_up_zz()
        entry = zz.entry(sg.SCRIPTS["strategic_ia"][0])
        pack = Edat(bytes(zz.read(entry)))
        member = pack.entry(sg.SCRIPTS["units"][1])
        earlier = pack.to_bytes({member.path: xyz(NEEDS["units"] + (b"_a_step_before",))})
        changed, added, _notes = sg.script_changes(zz, {entry.path: earlier})
        self.assertEqual(added, ["strategic_ia"])
        self.assertIn(b"_a_step_before", pyscript.stored_names(module_in(zz, changed, "units")))   # kept
        again, added_again, _ = sg.script_changes(zz, changed)                                      # read again
        self.assertEqual((again, added_again), ({}, []))

    def test_the_function_s_mark_is_of_what_it_does_not_where_it_is(self):
        def module(file: bytes, line: int, body: bytes) -> pyscript.Code:
            func = pyscript.Code(1, 1, 1, 67, body, (None,), (), (b"self",), (), (), file, b"add_bouton_techno", line,
                                 b"")
            cls = pyscript.Code(0, 0, 1, 66, b"", (func,), (), (), (), (), file, b"Menu", line, b"")
            return pyscript.Code(0, 0, 1, 64, b"", (cls, None), (b"Menu",), (), (), (), file, b"<module>", 1, b"")
        a = sg.function_sha(module(b"a.py", 10, b"d\x00\x00S"), b"Menu", b"add_bouton_techno")
        self.assertEqual(a, sg.function_sha(module(b"elsewhere.py", 99, b"d\x00\x00S"), b"Menu", b"add_bouton_techno"))
        self.assertNotEqual(a, sg.function_sha(module(b"a.py", 10, b"d\x00\x00\x01S"), b"Menu", b"add_bouton_techno"))
        self.assertIsNone(sg.function_sha(module(b"a.py", 10, b"d\x00\x00S"), b"Menu", b"another"))
        self.assertIsNone(sg.function_sha(module(b"a.py", 10, b"d\x00\x00S"), b"Other", b"add_bouton_techno"))

    @unittest.skipUnless((GAME / "Data").is_dir(), "the game isn't on this PC")
    def test_all_four_join_the_game_s_own_modules(self):
        from rusemod.build import find_pack
        with Edat.open(str(find_pack(GAME, "ZZ_Win.dat"))) as zz:
            changed, added, notes = sg.script_changes(zz, {})
            self.assertEqual((sorted(added), notes), (sorted(sg.SOURCES), []))
            self.assertEqual(sorted(added), ["condition", "menu", "strategic_ia", "units"])
            self.assertEqual(len(changed), 2)   # the two script packs
            for name in sg.SOURCES:
                pack_path, member_path = sg.SCRIPTS[name]
                entry = zz.entry(pack_path)
                game_pack = Edat(bytes(zz.read(entry)))
                before = pyscript.load(pyscript.read_xyz(bytes(game_pack.read(game_pack.entry(member_path)))).payload)
                after = module_in(zz, changed, name)
                self.assertEqual(after.code[:len(before.code) - 4], before.code[:-4], name)   # the game's code first
                self.assertEqual(after.names[:len(before.names)], before.names, name)
                self.assertIn(sg.KEPT[name], pyscript.stored_names(after))
                # every other module of the pack is the game's own, byte for byte
                new_pack = Edat(changed[entry.path])
                mine = {m.lower() for n, (p, m) in sg.SCRIPTS.items() if p == pack_path}
                for e in game_pack.entries:
                    if e.path.lower() not in mine:
                        self.assertEqual(bytes(new_pack.read(new_pack.entry(e.path))), bytes(game_pack.read(e)), e.path)
            self.assertEqual(sg.script_changes(zz, changed), ({}, [], []))


if __name__ == "__main__":
    unittest.main()
