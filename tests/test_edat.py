"""EDAT archive reading and writing on small made-up archives (no game files needed)."""
import os
import struct
import tempfile
import unittest

from fixtures import make_edat, make_empty_edat
from rusemod import Edat
from rusemod.edat import WIDE_MARK, WIDE_STEP, PackTooBig

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

    def test_added_files_go_in_front_of_the_dictionary_and_after_the_data(self):
        new = {"genglad\\patchable\\new.cpp.gladndfbin": b"NEW NDF", "extra/odd.txt": b"odd name, even data!"}
        rebuilt = Edat(self.arc.to_bytes({"top.bin": b"changed"}, add=new))
        got = {e.path: rebuilt.read(e) for e in rebuilt.entries}
        self.assertEqual(got, {**PATHS, "top.bin": b"changed", "genglad\\patchable\\new.cpp.gladndfbin": b"NEW NDF",
                               "extra\\odd.txt": b"odd name, even data!"})
        self.assertEqual(rebuilt._dict[-len(self.arc._dict):][:8], self.arc._dict[:8])  # the original trie follows
        self.assertEqual(rebuilt.data_offset, rebuilt.dict_offset + rebuilt.dict_len)
        self.assertEqual(rebuilt.data_len, sum(len(v) for v in got.values()))
        with self.assertRaises(ValueError):
            self.arc.to_bytes(add={"GENGLAD/readme.txt": b"already there"})

    def test_added_files_read_back_with_littlegrooves_reader_too(self):
        from ruse_mod_engine.edata import EdataFile
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "x.dat")
            with open(path, "wb") as f:
                self.arc.write_to(f, {"readme.txt": b"hi"}, add={"a\\b.bin": b"12345"})
            theirs = EdataFile.open(path)
            self.assertEqual(theirs.get("a/b.bin"), b"12345")
            self.assertEqual(theirs.get("genglad/readme.txt"), b"hi")
            self.assertEqual(theirs.get("genglad/patchable/everything.cpp.gladndfbin"), PATHS[
                "genglad\\patchable\\everything.cpp.gladndfbin"])

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


class Says(bytes):
    """A member that only says how long it is: the layout reads lengths, never the bytes, before it gives the
    header, so a pack's size can be tried without making it."""

    def __new__(cls, n):
        out = super().__new__(cls, b"")
        out.n = n
        return out

    def __len__(self):
        return self.n


class BigPacks(unittest.TestCase):
    """Past 4 GiB (the owner, 2026-10-30: a player's ZZ_Win.dat with many era units' own models): the data length in
    8 bytes, a plain pack refused past where its 4-byte places reach, and the wide layout for the big-packs patch."""

    def setUp(self):
        self.arc = Edat(make_edat(TREE))

    def test_the_data_length_in_8_bytes(self):
        raw = self.arc.to_bytes()
        self.assertEqual(struct.unpack_from("<Q", raw, 0x25)[0], self.arc.data_len)
        self.assertEqual(raw, make_edat(TREE))  # and every pack written as before stays byte for byte

    def test_a_plain_pack_past_4_gib_is_refused_before_anything_is_written(self):
        five = Says(5_000_000_000)
        with self.assertRaises(PackTooBig) as cm:  # one member past 4 GiB: its own size can't be said
            next(self.arc.iter_chunks({"top.bin": five}))
        self.assertIn("top.bin", str(cm.exception))
        three = Says(3_000_000_000)
        # 2 x 3 GB: the second starts before 4 GiB, which a plain pack's places reach; its 6 GB length is 8 bytes
        head = next(self.arc.iter_chunks({"top.bin": three}, {"new\\one.bin": three}))
        self.assertGreater(struct.unpack_from("<Q", head, 0x25)[0], 6_000_000_000)
        more = {"new\\one.bin": three, "new\\two.bin": three}  # 3 x 3 GB: the third starts past 4 GiB
        with self.assertRaises(PackTooBig) as cm:
            next(self.arc.iter_chunks({"top.bin": three}, more))
        self.assertFalse(cm.exception.wide)
        self.assertIn("4 GiB", str(cm.exception))
        # laid out wide it fits
        self.assertGreater(self.arc.laid_out({"top.bin": three}, more, wide=True), 9_000_000_000)

    def test_a_wide_pack_reads_back_with_every_member(self):
        added = {"new\\made.bin": b"N" * 37}
        raw = self.arc.to_bytes({"genglad\\readme.txt": b"longer hello"}, added, wide=True)
        back = Edat(raw)
        self.assertTrue(back.wide)
        want = {**PATHS, "genglad\\readme.txt": b"longer hello", **added}
        self.assertEqual({e.path: bytes(back.read(e)) for e in back.entries}, want)
        self.assertTrue(all(e.offset % WIDE_STEP == 0 for e in back.entries))  # 16-byte steps
        places = [struct.unpack_from("<I", back._dict, e.dict_pos)[0] for e in back.entries]
        self.assertTrue(all(p & WIDE_MARK for p in places))
        self.assertEqual(len(raw), back.data_offset + back.data_len)  # what the game checks the file's size against
        self.assertFalse(Edat(self.arc.to_bytes()).wide)
        self.assertEqual(Edat(raw).to_bytes(wide=True), raw)  # a wide pack rebuilt wide: the same bytes


if __name__ == "__main__":
    unittest.main()
