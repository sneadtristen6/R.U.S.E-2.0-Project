"""NDF string edits on a small made-up file (no game files needed).

  set PYTHONPATH=<repo>\\src  &&  py -3 -m unittest discover -s tests
"""
import struct
import unittest

from rusemod import Ndf

SECTIONS = ["OBJE", "TOPO", "CHNK", "CLAS", "PROP", "STRG", "TRAN", "IMPR", "EXPR"]


def strs(items):
    return b"".join(struct.pack("<I", len(s)) + s.encode("latin-1") for s in items)


def make_ndf(strings, other_string_user=False):
    """One TClusterMountMapDataPack-like object whose DataPack (type 0x07) points at STRG #0."""
    obje = struct.pack("<I", 0) + struct.pack("<II", 0, 0x07) + struct.pack("<I", 0)
    if other_string_user:
        obje += struct.pack("<II", 1, 0x07) + struct.pack("<I", 0)
    obje += struct.pack("<I", 0xABABABAB)
    body = {
        "OBJE": obje,
        "TOPO": b"",
        "CHNK": struct.pack("<II", 0, 1),
        "CLAS": strs(["TClusterMountMapDataPack"]),
        "PROP": b"".join(struct.pack("<I", len(n)) + n.encode() + struct.pack("<I", 0) for n in ["DataPack", "Other"]),
        "STRG": strs(strings),
        "TRAN": strs(["Mount"]),
        "IMPR": b"",
        "EXPR": struct.pack("<IiI", 0, 0, 0),  # one name ("Mount") for object 0
    }
    blob, toc = b"", []
    for name in SECTIONS:
        toc.append((name, 0x28 + len(blob), len(body[name])))
        blob += body[name]
    footer = b"TOC0" + struct.pack("<I", len(toc)) + b"".join(
        n.encode() + struct.pack("<IQQ", 0, off, size) for n, off, size in toc)
    footer_off = 0x28 + len(blob)
    header = b"EUG0" + struct.pack("<I", 0) + b"CNDF" + struct.pack("<IQQQ", 0, footer_off, 0x28, footer_off + len(footer))
    return header + blob + footer


class StringEdits(unittest.TestCase):
    def test_unchanged_round_trip_is_identical(self):
        raw = make_ndf(["MapDat:\\DataMapTwoIslands_v09.dat"])
        self.assertEqual(Ndf(raw).to_logical(), raw)

    def test_same_length_rename_changes_only_those_bytes(self):
        old, new = "MapDat:\\DataMapTwoIslands_v09.dat", "MapDat:\\DataMapTwoIslandz_v09.dat"
        raw = make_ndf([old])
        ndf = Ndf(raw)
        ndf.set_string(0, new)
        out = ndf.to_logical()
        self.assertEqual(len(out), len(raw))
        self.assertEqual(sum(a != b for a, b in zip(out, raw)), 1)  # 's' -> 'z'
        self.assertEqual(Ndf(out).strings, [new])

    def test_longer_string_relays_sections(self):
        raw = make_ndf(["MapDat:\\A_v09.dat", "keep me"])
        ndf = Ndf(raw)
        ndf.set_string(0, "MapDat:\\A_much_longer_name_v09.dat")
        again = Ndf(ndf.to_logical())
        self.assertEqual(again.strings, ["MapDat:\\A_much_longer_name_v09.dat", "keep me"])
        self.assertEqual(again.exports, {0: "Mount"})
        self.assertEqual(len(again.objects), 1)

    def test_non_latin1_is_refused(self):
        ndf = Ndf(make_ndf(["x"]))
        with self.assertRaises(UnicodeEncodeError):
            ndf.set_string(0, "日本")


if __name__ == "__main__":
    unittest.main()
