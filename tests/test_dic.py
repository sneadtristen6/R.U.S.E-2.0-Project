"""Text files (.dic) and the text-key codec, on made-up data (no game files needed)."""
import struct
import unittest

from rusemod.dic import Dic, key_to_name, name_to_key

# A real R.U.S.E. key, from RUSE-Mod-Manager's notes: the first multiplayer map's name.
MP01_KEY = struct.unpack("<Q", bytes.fromhex("42503ae505000000"))[0]


def make_dic(items, version=0):
    """items: [(key, text)]; texts stored after the table, in order, with absolute offsets."""
    items = sorted(items)
    head = b"TRA" + bytes([version]) + struct.pack("<I", len(items))
    pos = len(head) + 16 * len(items)
    table, blob = b"", b""
    for key, text in items:
        data = text.encode("utf-16-le")
        table += struct.pack("<QII", key, pos + len(blob), len(text))
        blob += data
    return head + table + blob


class KeyCodec(unittest.TestCase):
    def test_a_real_game_key_decodes_to_a_name(self):
        self.assertEqual(key_to_name(MP01_KEY), "M_D_01")

    def test_names_round_trip(self):
        for name in ["M_D_01", "R2U00001", "a", "Z9_z"]:
            self.assertEqual(key_to_name(name_to_key(name)), name)
        self.assertEqual(name_to_key("M_D_01"), MP01_KEY)

    def test_invalid_names_are_refused(self):
        for bad in ["", "TOO_LONG_1", "has space", "é"]:
            with self.assertRaises(ValueError):
                name_to_key(bad)

    def test_a_key_that_isnt_a_packed_name_gives_none(self):
        self.assertIsNone(key_to_name(0b000001_000000_000001))  # a zero code in the middle


class Reading(unittest.TestCase):
    def test_reads_every_entry(self):
        dic = Dic(make_dic([(MP01_KEY, "Blitz"), (name_to_key("R2U00001"), "US Marines")]))
        self.assertEqual(dic.text(MP01_KEY), "Blitz")
        self.assertEqual([e.name for e in dic.entries], ["M_D_01", "R2U00001"])  # sorted by key

    def test_version_byte_is_kept(self):
        self.assertEqual(Dic(make_dic([(1, "x")], version=1)).version, 1)

    def test_shared_text_is_allowed(self):
        raw = bytearray(make_dic([(1, "same"), (2, "same")]))
        struct.pack_into("<I", raw, 8 + 16 + 8, struct.unpack_from("<I", raw, 8 + 8)[0])  # point entry 2 at entry 1's text
        dic = Dic(bytes(raw))
        self.assertEqual(dic.text(2), "same")

    def test_rejects_broken_files(self):
        with self.assertRaises(ValueError):
            Dic(b"EUG0" + b"\0" * 20)
        with self.assertRaises(ValueError):
            Dic(b"TRA\0" + struct.pack("<I", 1000))


if __name__ == "__main__":
    unittest.main()
