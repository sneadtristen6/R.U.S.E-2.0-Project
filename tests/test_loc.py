"""Text mods (MOD_FORMAT §6): csv rows, handing out game keys, and writing them into the .dic files."""
import unittest

from test_dic import make_dic
from rusemod import loc
from rusemod.dic import GLYPH_KEY, Dic, name_to_key

SHERMAN = name_to_key("SHERMAN")  # a made-up key standing in for a game text


def game_files(langs=loc.LANGS + ("dev",), dictionary="baseunite"):
    return {loc.member(dictionary, lang): make_dic([(SHERMAN, f"M4 Sherman ({lang})"), (GLYPH_KEY, " M4Shrman()")])
            for lang in langs}


def reader(files):
    return lambda path: files.get(path)


CSV = """key,game_key,us,fr,de
r2.marines,,US Marines,Marines US,
r2.rangers,,Rangers,,Ranger
r2.named,R2NAMED,Named,,
"""


class ReadingCsv(unittest.TestCase):
    def test_columns_languages_and_fallback(self):
        rows = loc.read_csv(CSV, "baseunite", mod="m", file="text/baseunite.csv")
        self.assertEqual([r.key for r in rows], ["r2.marines", "r2.rangers", "r2.named"])
        self.assertEqual(rows[0].texts, {"us": "US Marines", "fr": "Marines US"})
        self.assertEqual(rows[1].texts, {"us": "Rangers", "ger": "Ranger"})  # `de` is the game's `ger`
        self.assertEqual((rows[2].game_key, rows[2].line, rows[2].dictionary), ("R2NAMED", 4, "baseunite"))

    def test_mistakes_say_where(self):
        cases = [("us\nx\n", "must name the columns"),
                 ("key,us,klingon\nx,y,z\n", "unknown column 'klingon'"),
                 ("key,us\nx,one\nx,two\n", ":3: the key 'x' is already on line 2"),
                 ("key,fr\nx,bonjour\n", "no `us` (English) text"),
                 ("key,game_key,us\nx,TOO_LONG_NAME,y\n", "not a valid text-key name"),
                 ("key,us,en\nx,a,b\n", "two columns for the language us")]
        for text, fragment in cases:
            with self.assertRaises(loc.TextError) as ctx:
                loc.read_csv(text, "baseunite", file="t.csv")
            self.assertIn(fragment, str(ctx.exception))


class HandingOutKeys(unittest.TestCase):
    def rows(self, text=CSV, mod="m"):
        return loc.read_csv(text, "baseunite", mod=mod, file="text/baseunite.csv")

    def test_prefix_and_sorted_numbers(self):
        p = loc.plan([("m", "R2", self.rows())], {"baseunite": {SHERMAN}})
        self.assertEqual(p.keys, {"r2.marines": "R2000001", "r2.named": "R2NAMED", "r2.rangers": "R2000002"})
        self.assertEqual(sorted(p.changes["baseunite"]),
                         sorted(name_to_key(n) for n in ("R2000001", "R2000002", "R2NAMED")))

    def test_the_same_rows_always_get_the_same_keys(self):
        shuffled = "key,us\nr2.b,B\nr2.a,A\n"
        p = loc.plan([("m", "X", self.rows(shuffled))], {})
        self.assertEqual(p.keys, {"r2.a": "X0000001", "r2.b": "X0000002"})  # sorted by key, not by line

    def test_clashes_are_errors_that_name_both(self):
        with self.assertRaisesRegex(loc.TextError, "set text_prefix"):
            loc.plan([("m", "", self.rows())], {})
        with self.assertRaisesRegex(loc.TextError, "SHERMAN is already a text in the game's baseunite.dic"):
            loc.plan([("m", "R2", self.rows("key,game_key,us\nx,SHERMAN,y\n"))], {"baseunite": {SHERMAN}})
        a = self.rows("key,game_key,us\na.x,SAMEKEY,A\n", mod="a")
        b = self.rows("key,game_key,us\nb.x,SAMEKEY,B\n", mod="b")
        with self.assertRaisesRegex(loc.TextError, r"b \(text/baseunite.csv:2\): the game key SAMEKEY is already "
                                                   r"used by a \(text/baseunite.csv:2\)"):
            loc.plan([("a", "", a), ("b", "", b)], {})
        with self.assertRaisesRegex(loc.TextError, "the text key 'x' is already defined by a"):
            loc.plan([("a", "A", self.rows("key,us\nx,1\n", "a")), ("b", "B", self.rows("key,us\nx,2\n", "b"))], {})

    def test_changing_a_game_text(self):
        rows = self.rows("key,us\ngame:SHERMAN,Sherman M4A1\n")
        p = loc.plan([("m", "", rows)], {"baseunite": {SHERMAN}})
        self.assertIn(SHERMAN, p.changes["baseunite"])
        with self.assertRaisesRegex(loc.TextError, "game:NOPE isn't a text in the game's baseunite.dic"):
            loc.plan([("m", "", self.rows("key,us\ngame:NOPE,x\n"))], {"baseunite": {SHERMAN}})
        twice = [("a", "", self.rows("key,us\ngame:SHERMAN,A\n", "a")), ("b", "", self.rows("key,us\ngame:SHERMAN,B\n", "b"))]
        p = loc.plan(twice, {"baseunite": {SHERMAN}})
        self.assertEqual(len(p.warnings), 1)
        self.assertEqual(p.changes["baseunite"][SHERMAN][1], {"us": "B"})  # the later mod wins


class WritingDicFiles(unittest.TestCase):
    def test_every_language_gets_its_text_or_english(self):
        files = game_files()
        p = loc.plan([("m", "R2", loc.read_csv(CSV, "baseunite", "m"))], {"baseunite": {SHERMAN}})
        changed, notes = loc.apply(p, reader(files))
        self.assertEqual(len(changed), len(loc.LANGS) + 1)  # ten languages and dev
        self.assertEqual(notes, [])
        marines = name_to_key("R2000001")
        texts = {path.split("\\")[-2]: Dic(data).text(marines) for path, data in changed.items()}
        self.assertEqual(texts["us"], "US Marines")
        self.assertEqual(texts["fr"], "Marines US")
        self.assertEqual(texts["ger"], "US Marines")  # no German text: English
        self.assertEqual(texts["dev"], "US Marines")
        us = Dic(changed[loc.member("baseunite", "us")])
        self.assertEqual(us.text(SHERMAN), "M4 Sherman (us)")  # the game's own texts are untouched
        self.assertTrue(set("US Marines") <= set(us.glyphs))  # new characters were added to the character list

    def test_missing_folders_are_a_note_and_a_missing_dictionary_an_error(self):
        files = game_files(langs=("us", "fr"))
        p = loc.plan([("m", "R2", loc.read_csv(CSV, "baseunite", "m"))], {"baseunite": set()})
        changed, notes = loc.apply(p, reader(files))
        self.assertEqual(len(changed), 2)
        self.assertIn("isn't in the ger, ita", notes[0])
        p = loc.plan([("m", "R2", loc.read_csv(CSV, "nosuch", "m"))], {})
        with self.assertRaisesRegex(loc.TextError, "no dictionary called nosuch.dic"):
            loc.apply(p, reader(files))


if __name__ == "__main__":
    unittest.main()
