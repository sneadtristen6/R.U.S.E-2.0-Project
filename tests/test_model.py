"""The bridge between game data files and the rules engine: load, run mods, write back (made-up data)."""
import hashlib
import os
import pickle
import struct
import tempfile
import unittest
import zlib
from decimal import Decimal
from pathlib import Path
from unittest import mock

from fixtures import make_ndf, val
from rusemod import Ndf, model
from rusemod.dic import name_to_key
from rusemod.model import ModelError, load, save
from rusemod.patch import Engine, Inline, ListV, MapV, Obj, Op, PairV, Ref, Text, _walk_obj, num
from rusemod.resolve import ModInfo
from rusemod.rndf import parse

UNITS = "genglad/patchable/gfx/everything.cpp.gladndfbin"
OTHER = "genglad/patchable/other.cpp.gladndfbin"


def i32(v):
    return val(0x02, struct.pack("<i", v))


def f32(v):
    return val(0x05, struct.pack("<f", v))


def ints(values):
    return val(0x11, struct.pack("<I", len(values)) + b"".join(i32(v) for v in values))


def local(i):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, 0))


def imported(k):
    return val(0x09, struct.pack("<II", 0xAAAAAAAA, k))


CLASSES = ["TUniteAuSolDescriptor", "TWeapon", "TAmmunition"]
PROPS = [("ProductionPrice", 0), ("Speed", 0), ("Weapon", 0), ("Ammo", 1), ("Puissance", 2), ("Flag", 0),
         ("Name", 0), ("Show", 0), ("Title", 0)]
# #0 Unit A: price, speed, own weapon #1 (inline), odd bool, key, an import; #1 weapon -> shared ammo #2
# #2 ammo (used by #1 and #4: shared); #3 Unit B; #4 weapon of B (inline) -> #2
OBJECTS = [
    (0, [(0, ints([100] * 5)), (1, f32(1.5)), (2, local(1)), (5, val(0x00, b"\x4e")),
         (6, val(0x1D, struct.pack("<Q", name_to_key("M_D_01")))), (7, imported(0))]),
    (1, [(3, local(2))]),
    (2, [(4, i32(40))]),
    (0, [(0, ints([50] * 5)), (2, local(4)), (8, val(0x07, struct.pack("<I", 0)))]),
    (1, [(3, local(2))]),
]
FILES = {
    UNITS: make_ndf(objects=OBJECTS, classes=CLASSES, props=PROPS, strings=["Old title"],
                    exports={0: "A", 3: "B"}, imports=["VersionOption/ShowOfficialMap"], topo=[0, 3], compress=True),
}
MENU = make_ndf(objects=[(0, [(0, val(0x11, struct.pack("<I", 1) + imported(0)))])], classes=["TMenu"],
                props=[("Units", 0)], exports={0: "Menu"}, imports=["A"], topo=[0])


def build(text, files=FILES, ops=None):
    base, loaded = load(files)
    result = Engine(base).run([(ModInfo("m"), ops if ops is not None else parse(text, file="m.rndf", mod="m"))])
    return base, loaded, result


def build_and_save(text, files=FILES, ops=None):
    base, loaded, result = build(text, files, ops)
    assert result.errors == [], [f.message for f in result.errors]
    notes = []
    return save(base, result.game, loaded, result.created, notes), notes


def reread(out, path=UNITS):
    return Ndf(out[path])


class Loading(unittest.TestCase):
    def test_model_shape(self):
        game, _ = load(FILES)
        a = game.objects["$/A"]
        self.assertEqual(a.cls, "TUniteAuSolDescriptor")
        self.assertIsInstance(a.props["Weapon"], Inline)                     # used only by A: part of A
        self.assertEqual(a.props["Weapon"].obj.props["Ammo"], Ref(f"{UNITS}#2"))  # used twice: shared
        self.assertEqual(a.props["Show"], Ref("$/VersionOption/ShowOfficialMap"))
        self.assertEqual(game.objects["$/VersionOption/ShowOfficialMap"].cls, "<external>")  # stand-in, not broken
        self.assertEqual(a.props["Name"].value, "M_D_01")

    def test_nothing_changes_without_mods(self):
        base, loaded, result = build("patch $/A ( Speed *= 1 )")
        self.assertEqual(save(base, result.game, loaded), {})

    def test_the_same_name_in_two_files_is_reported_and_kept_apart(self):
        other = make_ndf(objects=[(0, [])], classes=["T"], props=[], exports={0: "A"})
        game, _ = load({**FILES, OTHER: other})
        self.assertEqual(game.objects["$/A"].cls, "TUniteAuSolDescriptor")  # the first file's
        self.assertEqual(game.objects[f"{OTHER}#0"].cls, "T")
        self.assertIn("$/A is named in both", game.notes[0])

    def test_each_scenarios_own_copy_of_a_file_is_kept_apart_quietly(self):
        one = make_ndf(objects=[(0, [])], classes=["T"], props=[], exports={0: "C"})
        two = make_ndf(objects=[(0, [])], classes=["T"], props=[], exports={0: "C"})
        game, _ = load({"genglad/patchable/scenario/a/scenario/clustermap.cpp.gladndfbin": one,
                        "genglad/patchable/scenario/b/scenario_2v2/clustermap.cpp.gladndfbin": two})
        self.assertEqual(game.notes, [])
        self.assertIn("genglad/patchable/scenario/b/scenario_2v2/clustermap.cpp.gladndfbin#0", game.objects)
        game, _ = load({"genglad/patchable/map/a/mapterrain.cpp.gladndfbin": one,
                        "genglad/patchable/map/b/mapterrain.cpp.gladndfbin": two})
        self.assertEqual(game.notes, [])


class WritingBack(unittest.TestCase):
    def test_value_changes_land_and_everything_else_keeps_its_bytes(self):
        base, loaded, result = build("patch $/A ( ProductionPrice *= 0.5  Speed *= 1.1 )")
        self.assertEqual(result.errors, [])
        out = save(base, result.game, loaded)
        ndf, orig = reread(out), Ndf(FILES[UNITS])
        a = ndf.objects[0]
        self.assertEqual(a.get(0).int_list(), [50] * 5)
        self.assertEqual(a.get(1).payload, struct.pack("<f", 1.5 * 1.1))
        self.assertEqual(a.get(5).payload, b"\x4e")                       # the odd bool kept its raw byte
        for i in (1, 2, 3, 4):
            self.assertEqual([(p, v.encode()) for p, v in ndf.objects[i].props],
                             [(p, v.encode()) for p, v in orig.objects[i].props])
        self.assertTrue(struct.unpack_from("<I", out[UNITS], 12)[0] & 0x80)  # still compressed

    def test_inline_part_and_shared_object(self):
        base, loaded, result = build("patch shared $/A:Weapon.Ammo ( Puissance = 55 )")
        self.assertEqual(result.errors, [])
        ndf = reread(save(base, result.game, loaded))
        self.assertEqual(ndf.objects[2].get(4).scalar(), 55)              # the shared ammo object changed
        self.assertEqual([(p, v.encode()) for p, v in ndf.objects[1].props],
                         [(p, v.encode()) for p, v in Ndf(FILES[UNITS]).objects[1].props])

    def test_texts_and_keys(self):
        base, loaded, result = build("patch $/B ( Title = 'New title' )\npatch $/A ( Name = key(R2MARINE) )")
        ndf = reread(save(base, result.game, loaded))
        self.assertEqual(ndf.strings, ["Old title", "New title"])           # new string appended
        self.assertEqual(ndf.objects[3].get(8).payload, struct.pack("<I", 1))
        self.assertEqual(struct.unpack("<Q", ndf.objects[0].get(6).payload)[0], name_to_key("R2MARINE"))

    def test_references_to_existing_objects(self):
        base, loaded, result = build("patch $/A ( Show = $/B )\npatch $/B ( Title = nil )")
        ndf = reread(save(base, result.game, loaded))
        self.assertEqual(struct.unpack("<III", ndf.objects[0].get(7).payload), (0xBBBBBBBB, 3, 0))
        self.assertEqual(struct.unpack("<III", ndf.objects[3].get(8).payload), (0xBBBBBBBB, 0xFFFFFFFF, 0xFFFFFFFF))

    def test_a_replaced_part_stays_in_the_file_unused(self):
        out, _ = build_and_save("patch $/B ( Weapon = $/A )")  # B's own weapon part #4 is left unused
        ndf = reread(out)
        self.assertEqual(len(ndf.objects), 5)  # nothing removed: no index moves
        self.assertEqual(struct.unpack("<III", ndf.objects[3].get(2).payload), (0xBBBBBBBB, 0, 0))

    def test_refs_to_unnamed_objects_in_other_files_are_refused(self):
        other = make_ndf(objects=[(0, [(0, i32(1))])], classes=["T"], props=[("X", 0)], exports={0: "O"})
        base, loaded, result = build("", {**FILES, OTHER: other},
                                     ops=[Op("set", "$/O", "X", Ref(f"{UNITS}#2"), mod="m")])
        with self.assertRaisesRegex(ModelError, "unnamed object in another file"):
            save(base, result.game, loaded, result.created)

    def test_same_property_name_in_two_classes_keeps_each_objects_own_entry(self):
        # PROP has "Cost" twice: entry 0 for class TA, entry 1 for class TB. Changing B's other value must not move
        # its Cost to TA's entry, and setting Cost on an A that lacked it must use TA's entry.
        files = {UNITS: make_ndf(
            objects=[(0, [(0, i32(1))]), (1, [(1, i32(2)), (2, i32(3))]), (0, [])],
            classes=["TA", "TB"], props=[("Cost", 0), ("Cost", 1), ("Other", 1)], exports={0: "A", 1: "B", 2: "A2"})}
        base, loaded, result = build("patch $/B ( Other = 30 )\npatch $/A2 ( Cost = 7 )", files)
        self.assertEqual(result.errors, [])
        ndf = reread(save(base, result.game, loaded))
        self.assertEqual([(pi, v.scalar()) for pi, v in ndf.objects[1].props], [(1, 2), (2, 30)])
        self.assertEqual([(pi, v.scalar()) for pi, v in ndf.objects[2].props], [(0, 7)])

    def test_refs_to_unimported_objects_are_reported(self):
        base, loaded, result = build("patch $/A ( Show = $/Somewhere/Else )")
        self.assertTrue(result.errors)  # the engine already says it's dangling
        self.assertIn("still refers to $/Somewhere/Else", result.errors[0].message)



class NewObjects(unittest.TestCase):
    def test_clone_a_unit(self):
        out, _ = build_and_save("export C is clone $/A ( ProductionPrice = [1, 1, 1, 1, 1] )")
        ndf, orig = reread(out), Ndf(FILES[UNITS])
        self.assertEqual(len(ndf.objects), 7)                       # C at #5, its copied weapon part at #6
        self.assertEqual(struct.unpack("<II", ndf._sec("CHNK")), (0, 7))
        self.assertEqual(ndf.exports[5], "$/C")
        self.assertEqual(ndf.topo, [0, 3, 5])                       # named: in; the part's source #1 wasn't
        c, part = ndf.objects[5], ndf.objects[6]
        self.assertEqual(ndf.classes[c.cls], "TUniteAuSolDescriptor")
        self.assertEqual(c.get(0).int_list(), [1] * 5)
        self.assertEqual(c.get(1).payload, orig.objects[0].get(1).payload)          # Speed copied as is
        self.assertEqual(struct.unpack("<III", c.get(2).payload), (0xBBBBBBBB, 6, 1))  # its own weapon part
        self.assertEqual(c.get(5).payload, b"\x4e")
        self.assertEqual(c.get(7).payload, orig.objects[0].get(7).payload)          # the same import
        self.assertEqual(struct.unpack("<III", part.get(3).payload), (0xBBBBBBBB, 2, 2))  # shared ammo stays shared
        for i in range(5):                                          # everything that was there is untouched
            self.assertEqual([(p, v.encode()) for p, v in ndf.objects[i].props],
                             [(p, v.encode()) for p, v in orig.objects[i].props])

    def test_clone_of_a_clone_goes_to_the_same_file(self):
        out, _ = build_and_save("export C is clone $/A ( )\nexport D is clone ~/C ( ProductionPrice = [2, 2, 2, 2, 2] )")
        ndf = reread(out)
        self.assertEqual((ndf.exports[5], ndf.exports[7]), ("$/C", "$/D"))
        self.assertEqual(ndf.objects[7].get(0).int_list(), [2] * 5)

    def test_a_new_object_of_a_new_class(self):
        ops = [Op("create", "$/Z", cls="TRadar", body=[Op("set", path="Range", value=num(3000))], mod="m")]
        out, _ = build_and_save("", ops=ops)
        ndf = reread(out)
        z = ndf.objects[5]
        self.assertEqual((ndf.classes[z.cls], ndf.props[z.props[0][0]]), ("TRadar", ("Range", 3)))
        self.assertEqual(z.get(z.props[0][0]).scalar(), 3000)
        self.assertEqual(ndf.exports[5], "$/Z")

    def test_a_list_in_another_file_picks_up_the_new_unit(self):
        out, _ = build_and_save("export C is clone $/A ( )\npatch $/Menu ( Units += [~/C] )", {**FILES, OTHER: MENU})
        menu = Ndf(out[OTHER])
        self.assertEqual(menu.imports, {0: "$/A", 1: "$/C"})       # the new unit is imported by name
        items = menu.objects[0].get(0).payload
        self.assertEqual(struct.unpack_from("<I", items)[0], 2)
        self.assertEqual(struct.unpack_from("<III", items, 4 + 12), (0x09, 0xAAAAAAAA, 1))

    def test_delete_keeps_indices(self):
        out, notes = build_and_save("delete $/B")
        ndf = reread(out)
        self.assertEqual(len(ndf.objects), 5)
        self.assertNotIn(3, ndf.exports)
        self.assertEqual(ndf.topo, [0])
        self.assertIn("$/B is deleted", notes[0])

    def test_own_gives_a_unit_its_own_copy_of_a_shared_part(self):
        out, _ = build_and_save("patch own $/A:Weapon.Ammo ( Puissance = 1 )")
        ndf = reread(out)
        self.assertEqual(len(ndf.objects), 6)                       # the copy is new object #5
        self.assertEqual(struct.unpack("<III", ndf.objects[1].get(3).payload), (0xBBBBBBBB, 5, 2))
        self.assertEqual(ndf.objects[5].get(4).scalar(), 1)
        self.assertEqual(ndf.objects[2].get(4).scalar(), 40)       # B still uses the shared original

    def test_a_reference_to_a_part_makes_it_a_shared_object(self):
        # B takes A's own weapon (#1): the part keeps its place, A and B both point at it, nothing new is added
        out, _ = build_and_save("patch $/B ( Weapon = $/A:Weapon )")
        ndf = reread(out)
        self.assertEqual(len(ndf.objects), 5)
        self.assertEqual(struct.unpack("<III", ndf.objects[3].get(2).payload)[:2], (0xBBBBBBBB, 1))
        self.assertEqual(struct.unpack("<III", ndf.objects[0].get(2).payload)[:2], (0xBBBBBBBB, 1))
        base, _loaded, result = build("patch $/B ( Weapon = $/A:Weapon )  patch $/A:Weapon.Ammo ( Puissance = 1 )")
        self.assertIn("which 2 places use", result.errors[0].message)  # from then on it counts as shared


# mods for comparing a kept model with one loaded afresh: every kind of change save() writes
KEPT_MODS = [
    ("patch $/A ( ProductionPrice *= 0.5  Speed *= 1.1 )", None),
    ("patch shared $/A:Weapon.Ammo ( Puissance = 55 )", None),
    ("patch $/B ( Title = 'New title' )\npatch $/A ( Name = key(R2MARINE) )", None),
    ("export C is clone $/A ( ProductionPrice = [1, 1, 1, 1, 1] )", None),
    ("export C is clone $/A ( )\nexport D is clone ~/C ( ProductionPrice = [2, 2, 2, 2, 2] )", None),
    ("export C is clone $/A ( )\npatch $/Menu ( Units += [~/C] )", None),
    ("", [Op("create", "$/Z", cls="TRadar", body=[Op("set", path="Range", value=num(3000))], mod="m")]),
    ("delete $/B", None),
    ("patch own $/A:Weapon.Ammo ( Puissance = 1 )", None),
    ("patch $/B ( Weapon = $/A:Weapon )", None),
]
KEPT_FILES = {**FILES, OTHER: MENU}


def model_text(game, loaded) -> str:
    """Everything a loaded model is, as text: its objects with their origins, in order, its notes, each file's state."""
    return repr((list(game.objects.items()), game.notes, game.files,
                 [(p, nf.path, nf.raw, list(nf.names.items()), sorted(nf.inline), list(nf.index_of.items()),
                   nf.n_objects) for p, nf in loaded.items()]))


def saved(text, ops, files, cache):
    base, loaded = load(files, cache)
    result = Engine(base).run([(ModInfo("m"), ops if ops is not None else parse(text, file="m.rndf", mod="m"))])
    assert result.errors == [], [f.message for f in result.errors]
    notes = []
    return save(base, result.game, loaded, result.created, notes), notes, loaded


class KeptModel(unittest.TestCase):
    """With a cache folder the loaded model is kept, by a fingerprint of the files and the code, and read back."""

    def test_a_kept_model_is_the_model_loaded_afresh(self):
        fresh = model_text(*load(KEPT_FILES))
        with tempfile.TemporaryDirectory() as d:
            first = load(KEPT_FILES, d)
            kept = model.kept_path(KEPT_FILES, d)
            self.assertTrue(kept.is_file())
            with mock.patch.object(model, "_load", side_effect=AssertionError("loaded afresh")):
                second = load(KEPT_FILES, d)  # from the kept file
            self.assertEqual(model_text(*first), fresh)
            self.assertEqual(model_text(*second), fresh)
            self.assertIsNone(second[1][UNITS]._ndf)  # the files themselves aren't read until saving needs one

    def test_saving_from_a_kept_model_writes_the_same_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            load(KEPT_FILES, d)
            for text, ops in KEPT_MODS:
                with self.subTest(text or ops[0].kind):
                    out, notes, _ = saved(text, ops, KEPT_FILES, None)
                    kept_out, kept_notes, loaded = saved(text, ops, KEPT_FILES, d)
                    self.assertTrue(out)
                    self.assertEqual(kept_out, out)
                    self.assertEqual(kept_notes, notes)
                    # only what changes is read: a mod that leaves the menu file alone never opens it
                    self.assertEqual(loaded[OTHER]._ndf is None, OTHER not in out and "create" not in repr(ops))

    def test_a_changed_file_or_order_or_code_is_loaded_afresh(self):
        changed = {UNITS: make_ndf(objects=OBJECTS[:2] + [(2, [(4, i32(41))])] + OBJECTS[3:], classes=CLASSES,
                                   props=PROPS, strings=["Old title"], exports={0: "A", 3: "B"},
                                   imports=["VersionOption/ShowOfficialMap"], topo=[0, 3], compress=True),
                   OTHER: MENU}
        with tempfile.TemporaryDirectory() as d:
            load(KEPT_FILES, d)
            paths = {model.kept_path(KEPT_FILES, d), model.kept_path(changed, d),
                     model.kept_path({OTHER: MENU, UNITS: FILES[UNITS]}, d)}
            self.assertEqual(len(paths), 3)  # each file's bytes count, and their order
            game, loaded = load(changed, d)
            self.assertEqual(game.objects[f"{UNITS}#2"].props["Puissance"].value, 41)  # the new bytes, not the kept
            self.assertEqual(model_text(game, loaded), model_text(*load(changed)))
            with mock.patch.object(model, "code_version", return_value=model.code_version() + b"another"):
                other_code = model.kept_path(KEPT_FILES, d)
            self.assertNotIn(other_code, paths)  # other code: another name

    def test_a_damaged_kept_file_is_ignored_and_kept_again(self):
        game, loaded = load(KEPT_FILES)
        fresh = model_text(game, loaded)

        def kept_file(*inside, raw=None):
            body = zlib.compress(raw if raw is not None else pickle.dumps(inside, protocol=5))
            return hashlib.blake2b(body, digest_size=model.KEPT_DIGEST).digest() + body

        whole = kept_file(model.KEPT_FORMAT, game, {p: nf.state() for p, nf in loaded.items()})
        flipped = bytearray(whole)
        flipped[len(flipped) // 2] ^= 0x40
        damage = {"one byte changed": bytes(flipped), "cut short": whole[:len(whole) // 2], "empty": b"",
                  "not a model": kept_file(raw=b"hello"),
                  "another format": kept_file(model.KEPT_FORMAT + 1, game, {}),
                  "a file left out": kept_file(model.KEPT_FORMAT, game, {}),
                  "something else inside": kept_file(model.KEPT_FORMAT, os.getcwd, {})}  # never called
        with tempfile.TemporaryDirectory() as d:
            kept = model.kept_path(KEPT_FILES, d)
            for what, data in damage.items():
                with self.subTest(what):
                    kept.write_bytes(data)
                    self.assertIsNone(model._read_kept(kept, KEPT_FILES))
                    self.assertEqual(model_text(*load(KEPT_FILES, d)), fresh)  # loaded afresh
                    self.assertEqual(model_text(*model._read_kept(kept, KEPT_FILES)), fresh)  # and kept again, whole
            kept.write_bytes(whole)
            self.assertEqual(model_text(*model._read_kept(kept, KEPT_FILES)), fresh)  # an undamaged one reads

    def test_only_the_most_recently_used_are_kept(self):
        with tempfile.TemporaryDirectory() as d:
            old = [Path(d) / f"model-{i:040x}.bin" for i in range(model.KEPT_MOST + 3)]
            for k, f in enumerate(old):
                f.write_bytes(b"old")
                os.utime(f, (1_000_000 + k, 1_000_000 + k))
            other = Path(d) / "road-profile-0.json"  # the cache's other files are left alone
            other.write_text("{}")
            os.utime(other, (1, 1))
            load(KEPT_FILES, d)
            left = sorted(Path(d).glob("model-*.bin"))
            self.assertEqual(len(left), model.KEPT_MOST)
            self.assertIn(model.kept_path(KEPT_FILES, d), left)
            self.assertEqual(set(left) - {model.kept_path(KEPT_FILES, d)}, set(old[-(model.KEPT_MOST - 1):]))
            self.assertTrue(other.is_file())

    def test_the_collector_runs_again_after_a_pause_as_before(self):
        import gc
        self.assertTrue(gc.isenabled())
        with self.assertRaises(ValueError), model.collector_paused():
            with model.collector_paused():
                self.assertFalse(gc.isenabled())
            self.assertFalse(gc.isenabled())  # an inner pause leaves the outer one be
            raise ValueError
        self.assertTrue(gc.isenabled())
        gc.disable()
        try:
            with model.collector_paused():
                pass
            self.assertFalse(gc.isenabled())  # it was off: left off
        finally:
            gc.enable()

    def test_walked_is_walk_obj(self):
        inner = Obj("TPart", {"Deep": ListV([Ref("$/X"), Inline(Obj("TDeeper", {"N": num(1)}))])})
        obj = Obj("T", {"A": num(1), "L": ListV([num(2), ListV([num(3)]), Inline(inner)]),
                        "M": MapV([(Text("string", "k"), PairV(num(4), Inline(Obj("TValue", {"V": num(5)})))),
                                   (num(6), ListV([]))]),
                        "P": PairV(Ref(None), Inline(Obj("TPair", {}))), "Z": Text("key", "M_D_01")})
        want = list(_walk_obj(obj))
        got = model.walked(obj)
        self.assertEqual(len(got), len(want))
        self.assertTrue(all(a is b for a, b in zip(got, want)))
        self.assertEqual([id(p) for p in model.parts_inside(obj)], [id(v.obj) for v in want if isinstance(v, Inline)])
        self.assertEqual([p.cls for p in model.parts_inside(obj)], ["TPart", "TDeeper", "TValue", "TPair"])


if __name__ == "__main__":
    unittest.main()
