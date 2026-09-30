"""Sharing a load order as text (rusemod.loadorder): the block RUSE Mod Manager copies and reads, both ways."""
import re
import unittest

from rusemod.loadorder import Entry, Shared, match, parse, share_text

# as RUSE Mod Manager copies it
THEIRS = """Here's my order:
=== R.U.S.E. Load Order ===
1. Passable Forests | v1.0.0
2. [COMPAT] Old Mod
3. Name | with a bar | v2
=== End Load Order ===
have fun"""


def their_parser(text):
    """RUSE Mod Manager's own reading of the block (mod_manager._mgr_parse_load_order), for the round trip."""
    inside, out = False, []
    for line in text.splitlines():
        s = line.strip()
        if "Load Order" in s and "R.U.S.E." in s:
            inside = True
            continue
        if "End Load Order" in s:
            break
        m = re.match(r"^\d+\.\s+(.+)$", s) if inside and s else None
        if m:
            body = m.group(1).strip()
            name, ver = body.rsplit(" | v", 1) if " | v" in body else (body, "")
            compat = name.startswith("[COMPAT] ")
            out.append((name[9:] if compat else name.strip(), ver.strip(), compat))
    return out


class Text(unittest.TestCase):
    def test_their_block_reads(self):
        got = parse(THEIRS)
        self.assertEqual(got.mode, "public")
        self.assertEqual(got.entries, [Entry("Passable Forests", "1.0.0"), Entry("Old Mod", "", True),
                                       Entry("Name | with a bar", "2")])

    def test_ours_reads_back_and_in_their_app(self):
        mods = [{"name": "Passable  Forests", "version": "1.0.0"}, {"name": "Old Mod", "compat": True},
                {"name": "Cheat Mod", "version": "2.0.0"}]
        text = share_text(mods, "compat", "My set", "24670294")
        self.assertTrue(text.startswith("=== R.U.S.E. COMPAT Load Order ===\nSet: My set\nGame build: 24670294\n1. "))
        got = parse(text)
        self.assertEqual((got.mode, got.set_name, got.build), ("compat", "My set", "24670294"))
        self.assertEqual(got.entries, [Entry("Passable Forests", "1.0.0"), Entry("Old Mod", "", True),
                                       Entry("Cheat Mod", "2.0.0")])
        self.assertEqual(their_parser(text), [("Passable Forests", "1.0.0", False), ("Old Mod", "", True),
                                              ("Cheat Mod", "2.0.0", False)])

    def test_no_block_is_nothing(self):
        self.assertEqual(parse("just some chat"), Shared())
        self.assertEqual(parse(""), Shared())


class Matching(unittest.TestCase):
    LIBRARY = [{"id": "passable-forests", "name": "Passable Forests", "version": "1.0.0"},
               {"id": "cheat-mod", "name": "Cheat Mod", "version": "2.0.0"},
               {"id": "cheat-mod-old", "name": "Cheat Mod", "version": "1.0.0"}]

    def test_by_name_then_version(self):
        shared = Shared([Entry("passable  FORESTS", "1.0.0"), Entry("Cheat Mod", "1.0.0"), Entry("Nope", "3"),
                         Entry("Passable Forests"), Entry("cheat-mod", "9.9")])
        m = match(shared, self.LIBRARY)
        self.assertEqual([mod["id"] for _e, mod in m.found], ["passable-forests", "cheat-mod-old", "cheat-mod"])
        self.assertEqual(m.missing, [Entry("Nope", "3")])
        self.assertEqual([e.name for e in m.repeated], ["Passable Forests"])
        self.assertEqual([(e.version, mod["id"]) for e, mod in m.other_version], [("9.9", "cheat-mod")])


if __name__ == "__main__":
    unittest.main()
