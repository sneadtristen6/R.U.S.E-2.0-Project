"""rusemod.pyscript: the game's compiled Python and its unit list, on a made-up unit list written byte by byte
(PLAN.md decision 23). The real game is checked by tools/verify_pyscript.py."""
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_build import write_mod
from rusemod import Edat, pyscript
from rusemod.build import BuildError, build_pack, load_mod
from rusemod.pyscript import (BODY_CODE, NewClass, ScriptError, Xyz, add_classes, check_added, dump, load,
                              read_xyz, unit_list, write_xyz)

LOAD_CONST, LOAD_NAME, LOAD_ATTR, BUILD_TUPLE, IMPORT_NAME = 100, 101, 105, 102, 107
MAKE_FUNCTION, CALL_FUNCTION, BUILD_CLASS, STORE_NAME, STORE_ATTR, RETURN_VALUE = 132, 131, 89, 90, 95, 83


def i32(v):
    return struct.pack("<i", v)


def s(x):
    return b"s" + i32(len(x)) + x


def t(x):  # an interned string: later R(n) points back at the n-th one
    return b"t" + i32(len(x)) + x


def R(n):
    return b"R" + i32(n)


def tup(*items):
    return b"(" + i32(len(items)) + b"".join(items)


def op(o, arg=None):
    return bytes([o]) if arg is None else bytes([o, arg & 255, arg >> 8])


def code(body, consts, names, filename, name, stacksize=2, flags=0x42):
    return (b"c" + struct.pack("<4i", 0, 0, stacksize, flags) + s(body) + consts + names + tup() + tup() + tup()
            + filename + name + i32(1) + s(b""))


# class Tank_A(front.unit.TankUnit), class Building_B(front.batiment.Batiment), each with its base_class line.
# Interned strings, in stream order: 0 Tank_A, 1-6 the body's names, 7 classes.py, 8 Building_B, 9 front, ...
BODY_A = code(BODY_CODE, tup(s(b"$/Tank_A")),
              tup(t(b"__name__"), t(b"__module__"), t(b"_ndf"), t(b"Database"), t(b"GetObject"), t(b"descriptor")),
              t(b"classes.py"), R(0))
BODY_B = code(BODY_CODE, tup(s(b"$/Building_B")), tup(R(1), R(2), R(3), R(4), R(5), R(6)), R(7), R(8))
MODULE_CODE = (op(LOAD_CONST, 0) + op(LOAD_CONST, 1) + op(IMPORT_NAME, 1) + op(STORE_NAME, 0)
               + op(LOAD_CONST, 0) + op(LOAD_CONST, 1) + op(IMPORT_NAME, 5) + op(STORE_NAME, 0)
               + op(LOAD_CONST, 2) + op(LOAD_NAME, 0) + op(LOAD_ATTR, 2) + op(LOAD_ATTR, 3) + op(BUILD_TUPLE, 1)
               + op(LOAD_CONST, 3) + op(MAKE_FUNCTION, 0) + op(CALL_FUNCTION, 0) + op(BUILD_CLASS) + op(STORE_NAME, 4)
               + op(LOAD_CONST, 4) + op(LOAD_NAME, 0) + op(LOAD_ATTR, 6) + op(LOAD_ATTR, 7) + op(BUILD_TUPLE, 1)
               + op(LOAD_CONST, 5) + op(MAKE_FUNCTION, 0) + op(CALL_FUNCTION, 0) + op(BUILD_CLASS) + op(STORE_NAME, 8)
               + op(LOAD_NAME, 4) + op(LOAD_NAME, 4) + op(LOAD_ATTR, 9) + op(STORE_ATTR, 10)
               + op(LOAD_NAME, 8) + op(LOAD_NAME, 8) + op(LOAD_ATTR, 9) + op(STORE_ATTR, 10)
               + op(LOAD_CONST, 1) + op(RETURN_VALUE))
# The module's own name is a reference to an interned string that comes *after* the constants ("front", 9), so a
# write that interned anything new among the constants would shift it and break it.
MODULE = code(MODULE_CODE, tup(b"i" + i32(-1), b"N", t(b"Tank_A"), BODY_A, t(b"Building_B"), BODY_B),
              tup(t(b"front"), t(b"front.unit"), t(b"unit"), t(b"TankUnit"), R(0), t(b"front.batiment"),
                  t(b"batiment"), t(b"Batiment"), R(8), R(6), t(b"base_class")),
              R(7), R(9), stacksize=8, flags=0x40)
NEW = NewClass("Tank_C", "$/Tank_C", "Tank_A")


def interned_count(data):
    r = pyscript._Reader(data)
    r.obj()
    return len(r.interned)


class Marshal(unittest.TestCase):
    def test_reads_the_made_up_module(self):
        m = load(MODULE)
        self.assertEqual((m.name, m.filename, m.consts[2], m.names[4]), (b"front", b"classes.py", b"Tank_A", b"Tank_A"))
        self.assertEqual(m.consts[5].names[5], b"descriptor")

    def test_other_kinds_of_values(self):
        self.assertEqual(load(b"l" + i32(-2) + struct.pack("<2H", 5, 1)), -(5 + (1 << 15)))
        self.assertEqual(load(b"g" + struct.pack("<d", 2.5)), 2.5)
        self.assertEqual(load(b"u" + i32(2) + "é".encode("utf-8")), "é")
        self.assertEqual(load(b"[" + i32(2) + b"T" + b"F"), [True, False])
        self.assertEqual(load(b"{" + s(b"k") + b"i" + i32(3) + b"0"), {b"k": 3})
        for v in (None, True, 7, b"x", (b"a", (1, None))):
            self.assertEqual(load(dump(v)), v)
        self.assertEqual(load(dump(load(MODULE))), load(MODULE))  # dump writes strings plain; the values are the same

    def test_bad_data(self):
        for bad in (b"s" + i32(9) + b"abc", b"R" + i32(0), b"?", b"i" + i32(1) + b"extra"):
            with self.assertRaises(ScriptError):
                load(bad)


class UnitList(unittest.TestCase):
    def test_finds_the_classes(self):
        ul = unit_list(MODULE)
        self.assertEqual(sorted(ul.classes), ["Building_B", "Tank_A"])
        a = ul.classes["Tank_A"]
        self.assertEqual((a.path, a.base, a.standard, a.registered), ("$/Tank_A", ("unit", "TankUnit"), True, True))
        self.assertEqual(ul.classes["Building_B"].base, ("batiment", "Batiment"))
        self.assertIs(ul.by_path["$/Building_B"], ul.classes["Building_B"])

    def test_adds_a_class_like_another(self):
        new = add_classes(MODULE, [NEW])
        ul = unit_list(new)
        c = ul.classes["Tank_C"]
        self.assertEqual((c.path, c.base, c.standard, c.registered), ("$/Tank_C", ("unit", "TankUnit"), True, True))
        self.assertEqual(len(ul.classes), 3)
        m = load(new)
        self.assertEqual((m.name, m.filename), (b"front", b"classes.py"))  # references after the constants intact
        self.assertEqual(interned_count(new), interned_count(MODULE))  # nothing new interned
        self.assertEqual(load(new).consts[:6], load(MODULE).consts)

    def test_several_at_once(self):
        new = add_classes(MODULE, [NEW, NewClass("Building_D", "$/Building_D", "Building_B")])
        ul = unit_list(new)
        self.assertEqual(ul.classes["Building_D"].base, ("batiment", "Batiment"))
        self.assertTrue(ul.classes["Building_D"].registered and ul.classes["Tank_C"].registered)

    def test_unsafe_or_wrong_values_are_refused(self):
        bad = [NewClass(n, "$/Tank_C", "Tank_A") for n in ("", "1Tank", "Tank C", "Tank;C", "a.b", "Tank_A", "front")]
        bad += [NewClass("Tank_C", p, "Tank_A") for p in ("Tank_C", "$/a b", "$/../x", "$/x/", "$/Tank_A")]
        bad += [NewClass("Tank_C", "$/Tank_C", "Nope")]
        for n in bad:
            with self.subTest(n=n), self.assertRaises(ScriptError):
                add_classes(MODULE, [n])
        with self.assertRaises(ScriptError):
            add_classes(MODULE, [NEW, NewClass("Tank_C", "$/Tank_E", "Tank_A")])  # the same name twice

    def test_check_refuses_anything_but_the_template(self):
        new = add_classes(MODULE, [NEW])
        check_added(MODULE, new, [NEW])
        (c0, c1), _, _ = pyscript._module_spans(new)
        body = load(new).code
        added_at = len(MODULE_CODE) - 4
        swapped = body[:added_at] + bytes([IMPORT_NAME]) + body[added_at + 1:]  # LOAD_CONST -> IMPORT_NAME
        tampered = [
            new[:c0] + dump(swapped) + new[c1:],
            new.replace(b"$/Tank_C", b"$/Tank_X"),            # the new class points somewhere else
            new.replace(b"$/Building_B", b"$/Building_Z"),    # an existing class changed
            MODULE,                                           # nothing added
        ]
        for data in tampered:
            with self.assertRaises(ScriptError):
                check_added(MODULE, data, [NEW])


class Container(unittest.TestCase):
    def test_round_trip(self):
        raw = write_xyz(Xyz(b"\x11" * 16, MODULE))
        self.assertEqual(raw[:12], b"XYZ0\x0a\x0d\xf2\xb3" + struct.pack(">I", len(MODULE)))
        self.assertEqual(read_xyz(raw), Xyz(b"\x11" * 16, MODULE))

    def test_bad_files(self):
        raw = write_xyz(Xyz(b"\0" * 16, MODULE))
        for bad in (b"XYZ1" + raw[4:], raw[:8] + struct.pack(">I", 5) + raw[12:]):
            with self.assertRaises(ScriptError):
                read_xyz(bad)


UNIT_NDF = make_ndf(objects=[(0, [(0, val(0x02, struct.pack("<i", n))), (1, val(0x07, struct.pack("<I", i)))])
                             for i, n in enumerate((7, 8))],  # Tank_A is in the unit list, Tank_Hidden isn't
                    classes=["TUniteAuSolDescriptor"], props=[("DescriptorId", 0), ("ClassNameForDebug", 0)],
                    strings=["Tank_A", "Tank_Hidden"], exports={0: "Tank_A", 1: "Tank_Hidden"}, topo=[0, 1])
UNIT_PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", UNIT_NDF)])])
SCRIPTS = make_edat([("dir", "genpython\\1000\\codeia\\python\\eugenpatchable\\parametres\\", [
    ("file", "__init__.xyz", b"untouched"), ("file", "classes.xyz", write_xyz(Xyz(b"\x22" * 16, MODULE)))])])
ZZ_WIN = make_edat([("dir", "genpython\\", [("file", "eugenpatchable.ipk", SCRIPTS)]), ("file", "other.bin", b"x")])


class InTheBuild(unittest.TestCase):
    def build(self, text, zz_win=ZZ_WIN):
        with tempfile.TemporaryDirectory() as d:
            mod = load_mod(write_mod(d, "units", {"u.rndf": text}))
            return build_pack(Edat(UNIT_PACK), [mod], text_arc=Edat(zz_win) if zz_win else None)

    def test_a_copy_gets_its_class(self):
        result = self.build("export Tank_C is clone $/Tank_A ( )")
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.new_classes), 1)
        pack = Edat(result.script_changed["genpython\\eugenpatchable.ipk"])
        ul = unit_list(read_xyz(bytes(pack.read(pack.find("classes.xyz")))).payload)
        c = ul.by_path["$/Tank_C"]
        self.assertEqual((c.name, c.base, c.registered), (result.new_classes[0], ("unit", "TankUnit"), True))
        self.assertEqual(bytes(pack.read(pack.find("__init__.xyz"))), b"untouched")
        self.assertTrue(any("gets its class" in f.message for f in result.findings))

    def test_what_the_list_cant_take(self):
        result = self.build("delete $/Tank_A")
        self.assertIn("Python unit list", result.errors[0].message)
        result = self.build("export Tank_E is clone $/Tank_Hidden ( )")
        self.assertEqual(result.errors, [])
        self.assertTrue(any(f.level == "warning" and "isn't a copy of a unit" in f.message for f in result.findings))
        self.assertEqual(result.script_changed, {})

    def test_without_the_list(self):
        for zz_win in (None, make_edat([("file", "other.bin", b"x")])):
            result = self.build("export Tank_C is clone $/Tank_A ( )", zz_win)
            self.assertEqual((result.errors, result.script_changed), ([], {}))
            self.assertTrue(any("got no class" in f.message for f in result.findings))


class ModsCantBringScripts(unittest.TestCase):
    def test_refused(self):
        for name in ("helper.py", "classes.xyz", "run.bat", "tool.exe", "scripts.ipk"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as d:
                folder = write_mod(d, "sneaky", {"u.rndf": "export X is clone $/Tank_A ( )"})
                (folder / "extras").mkdir()
                (folder / "extras" / name).write_bytes(b"x")
                with self.assertRaises(BuildError) as cm:
                    load_mod(folder)
                self.assertIn("decision 23", str(cm.exception))

    def test_ordinary_files_are_fine(self):
        with tempfile.TemporaryDirectory() as d:
            folder = write_mod(d, "fine", {"u.rndf": "export X is clone $/Tank_A ( )"})
            (folder / "icon.png").write_bytes(b"x")
            (folder / "README.md").write_text("hi", encoding="utf-8")
            load_mod(folder)


if __name__ == "__main__":
    unittest.main()
