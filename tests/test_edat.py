"""EDAT archive reading and writing on small made-up archives (no game files needed)."""
import os
import struct
import tempfile
import unittest

from fixtures import make_edat, make_empty_edat
from rusemod import Edat

TREE = [
    ("dir", "genglad\\", [
        ("dir", "patchable\\", [
            ("file", "everything.cpp.gladndfbin", b"UNIT DATA " * 10),
            ("file", "mapinfo.cpp.gladndfbin", b"MAPS"),
        ]),
        ("file", "readme.txt", b"hello"),
    ]),
    ("file", "top.bin", b"\x00\x01\x02"),
]
PATHS = {
    "genglad\\patchable\\everything.cpp.gladndfbin": b"UNIT DATA " * 10,
    "genglad\\patchable\\mapinfo.cpp.gladndfbin": b"MAPS",
    "genglad\\readme.txt": b"hello",
    "top.bin": b"\x00\x01\x02",
}


class Reading(unittest.TestCase):
    def setUp(self):
        self.raw = make_edat(TREE)
        self.arc = Edat(self.raw)

    def test_lists_every_file_with_its_full_path(self):
        self.assertEqual({e.path for e in self.arc.entries}, set(PATHS))

    def test_reads_every_file(self):
        for e in self.arc.entries:
            self.assertEqual(self.arc.read(e), PATHS[e.path])

    def test_find_matches_a_path_ending_case_insensitively(self):
        self.assertEqual(self.arc.find("MAPINFO.CPP.GLADNDFBIN").path, "genglad\\patchable\\mapinfo.cpp.gladndfbin")
        with self.assertRaises(KeyError):
            self.arc.find("nothing.here")

    def test_rejects_other_files(self):
        with self.assertRaises(ValueError):
            Edat(b"EUG0" + b"\0" * 100)

    def test_empty_archive_has_no_files(self):
        self.assertEqual(Edat(make_empty_edat()).entries, [])


class Writing(unittest.TestCase):
    def setUp(self):
        self.raw = make_edat(TREE)
        self.arc = Edat(self.raw)

    def test_unchanged_rebuild_is_byte_identical(self):
        self.assertEqual(self.arc.to_bytes(), self.raw)

    def test_streamed_rebuild_equals_in_memory_rebuild(self):
        self.assertEqual(b"".join(self.arc.iter_chunks()), self.arc.to_bytes())

    def test_replacing_a_file_with_a_longer_one_keeps_the_others(self):
        new = b"CHANGED " * 50
        rebuilt = Edat(self.arc.to_bytes({"patchable\\mapinfo.cpp.gladndfbin": new}))
        got = {e.path: rebuilt.read(e) for e in rebuilt.entries}
        self.assertEqual(got, {**PATHS, "genglad\\patchable\\mapinfo.cpp.gladndfbin": new})
        self.assertEqual(rebuilt.data_len, sum(len(v) for v in got.values()))

    def test_replacing_with_a_shorter_file_works_too(self):
        rebuilt = Edat(self.arc.to_bytes({"everything.cpp.gladndfbin": b"x"}))
        self.assertEqual(rebuilt.read(rebuilt.find("everything.cpp.gladndfbin")), b"x")
        self.assertEqual(rebuilt.read(rebuilt.find("top.bin")), PATHS["top.bin"])

    def test_the_path_dictionary_is_kept_except_offsets_and_sizes(self):
        rebuilt = Edat(self.arc.to_bytes({"readme.txt": b"a longer readme"}))
        self.assertEqual(len(rebuilt._dict), len(self.arc._dict))
        self.assertEqual([e.path for e in rebuilt.entries], [e.path for e in self.arc.entries])

    def test_nested_archive_round_trips(self):
        inner = make_edat([("file", "eugen\\base\\camp.xyz", b"XYZ0 code")])
        outer = Edat(make_edat([("dir", "genpython\\", [("file", "eugen.ipk", inner)])]))
        nested = Edat(outer.read(outer.find("eugen.ipk")))
        self.assertEqual(nested.to_bytes(), inner)
        self.assertEqual(nested.entries[0].path, "eugen\\base\\camp.xyz")


class OpenFromDisk(unittest.TestCase):
    def test_open_reads_through_a_memory_map_and_closes(self):
        raw = make_edat(TREE)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.dat")
            with open(path, "wb") as f:
                f.write(raw)
            with Edat.open(path) as arc:
                self.assertEqual(arc.read(arc.find("top.bin")), PATHS["top.bin"])
                with open(os.path.join(d, "out.dat"), "wb") as out:
                    written = arc.write_to(out)
            self.assertEqual(written, len(raw))
            with open(os.path.join(d, "out.dat"), "rb") as f:
                self.assertEqual(f.read(), raw)


class HeaderLayout(unittest.TestCase):
    def test_fixture_matches_the_documented_header(self):
        raw = make_edat(TREE)
        self.assertEqual(raw[:4], b"edat")
        self.assertEqual(struct.unpack_from("<I", raw, 4)[0], 1)
        self.assertEqual(struct.unpack_from("<I", raw, 0x19)[0], 0x40D)


if __name__ == "__main__":
    unittest.main()
