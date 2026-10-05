"""Answers a mod brings with it (rusemod.solved): named by what they were worked out from, locked with the game's own
file, never trusted as they are; and the movement step taking them (rusemod.nav), on made-up graphs."""
import unittest
from unittest import mock

from rusemod import nav, solved
from test_nav import made, row


class Names(unittest.TestCase):
    def test_a_name_is_the_question_to_the_last_bit(self):
        a = solved.name("open", [(1.0, 2.0, 320.0)], 1280.0, b"raw")
        self.assertEqual(a, solved.name("open", [(1.0, 2.0, 320.0)], 1280.0, b"raw"))
        self.assertEqual(len(a), 20)
        others = [solved.name("fill", [(1.0, 2.0, 320.0)], 1280.0, b"raw"),          # another question
                  solved.name("open", [(1.0, 2.0, 320.0)], 1280.0, b"rae"),          # another byte
                  solved.name("open", [(1.0, 2.0, 320.00000000000006)], 1280.0, b"raw"),  # the last bit of a number
                  solved.name("open", [(1.0, 2.0)], 320.0, 1280.0, b"raw"),          # the same values grouped otherwise
                  solved.name("open", [(1.0, 2.0, 320.0)], 1280.0)]
        self.assertEqual(len({a, *others}), 6)
        self.assertNotEqual(solved.name("x", 0.1 + 0.2), solved.name("x", 0.3))


class Taking(unittest.TestCase):
    def test_worked_out_once_then_taken_and_never_trusted_as_it_is(self):
        key, calls = solved.name("q", 1), []

        def work():
            calls.append(1)
            return [(640.0, 0.0, 1280.0)]
        self.assertEqual(solved.answer(key, work), [(640.0, 0.0, 1280.0)])  # no answers in use: worked out
        self.assertEqual(len(calls), 1)
        mine = solved.Solved()
        with solved.using(mine):
            self.assertEqual(solved.answer(key, work), [(640.0, 0.0, 1280.0)])
            self.assertEqual(solved.answer(key, work), [(640.0, 0.0, 1280.0)])  # this build's own: not worked out twice
        self.assertEqual((len(calls), mine.found, mine.taken), (2, {key: [(640.0, 0.0, 1280.0)]}, 0))
        brought = solved.Solved({key: [(1280.0, 0.0, 640.0)]})
        with solved.using(brought):
            self.assertEqual(solved.answer(key, work, lambda a: True), [(1280.0, 0.0, 640.0)])  # taken: its check passes
            self.assertEqual((len(calls), brought.taken), (2, 1))
            self.assertEqual(solved.answer(key, work, lambda a: False), [(640.0, 0.0, 1280.0)])  # refused: worked out
            self.assertEqual(solved.answer(key, work, lambda a: 1 / 0), [(640.0, 0.0, 1280.0)])  # a check that chokes
            self.assertEqual(brought.taken, 1)
            solved.drop(key)
            self.assertEqual(brought.every(), {})
        self.assertEqual(solved.answer(key, work), [(640.0, 0.0, 1280.0)])  # outside `using` again
        self.assertEqual(len(calls), 5)


class Locked(unittest.TestCase):
    GAME = bytes(range(256)) * 40  # the game's own file for the map, as shipped
    ANSWERS = {solved.name("open", 1): [[(640.0, 1280.0, 1280.0), (0.1 + 0.2, -0.0, 5e-324)], 3, False],
               solved.name("fill", 2): [(640.0, 0.0, 320.0, 7)], solved.name("text", 3): "DISTINCTIVE-WORDS-INSIDE"}

    def test_read_back_only_with_the_same_game_file(self):
        data = solved.pack(self.ANSWERS, self.GAME, "M04_Cotentin")
        self.assertEqual(solved.unpack(data, self.GAME), self.ANSWERS)  # every value to the last bit, tuples as tuples
        self.assertEqual(solved.about(data), "M04_Cotentin")            # the one line anyone can read
        self.assertNotIn(b"DISTINCTIVE", data)                          # nothing of the answers shows
        self.assertEqual(data, solved.pack(dict(reversed(self.ANSWERS.items())), self.GAME, "M04_Cotentin"))  # the same
        other = solved.pack({**self.ANSWERS, solved.name("text", 3): "other words"}, self.GAME, "M04_Cotentin")
        self.assertNotEqual(data[:len(data) // 2], other[:len(other) // 2])  # other answers: another lock all through
        other = bytearray(self.GAME)
        other[1234] ^= 1
        for wrong in (bytes(other), self.GAME[:-1], b""):  # another version of the game's file: one bit, one byte
            with self.assertRaises(solved.SolvedError):
                solved.unpack(data, wrong)

    def test_a_changed_or_cut_file_is_refused(self):
        data = solved.pack(self.ANSWERS, self.GAME, "a map")
        for at in (0, len(solved.MAGIC) + 1, len(solved.MAGIC) + 4, len(data) // 2, len(data) - 40, len(data) - 1):
            spoiled = bytearray(data)
            spoiled[at] ^= 0x10
            with self.assertRaises(solved.SolvedError, msg=at):
                solved.unpack(bytes(spoiled), self.GAME)
        for cut in (data[:-1], data[:len(data) // 2], data[:20], data + b"x", b"", b"not a file of answers at all"):
            with self.assertRaises(solved.SolvedError):
                solved.unpack(cut, self.GAME)
        with self.assertRaises(solved.SolvedError):
            solved.about(b"nothing")

    def test_only_plain_values_go_in(self):
        for value in (solved.Solved(), unittest.TestCase, lambda: 1, [(1.0, 2.0), {"a": solved.SolvedError("x")}]):
            with self.assertRaises(solved.SolvedError, msg=value):
                solved.pack({solved.name("x", 1): value}, self.GAME)
        with self.assertRaises(solved.SolvedError):
            solved.pack({"a name that isn't a fingerprint": 1}, self.GAME)


def field():
    """A field (one circle) on a map 65,536 across: ground to open lies east of it."""
    return made([(6000.0, 30000.0, 9000.0)], [])


ZONES = [(30000.0, 30000.0, 16000.0), (50000.0, 30000.0, 8000.0), (30000.0, 52000.0, 4000.0)]


class Movement(unittest.TestCase):
    """nav takes the answers of its two long questions (where opened ground's circles go, which circles fill the
    ground back round a block) from the ones in use, weighs them, and works them out when they don't hold."""

    def opened(self, store=None, zones=ZONES):
        g = field()
        with solved.using(store):
            counts = g.open_ground(zones)
        return g.to_bytes(), counts

    def test_opened_ground_from_the_answers_is_the_same_graph(self):
        plain = self.opened()
        first = solved.Solved()
        self.assertEqual(self.opened(first), plain)
        self.assertTrue(first.found)

        def never(*_a, **_k):
            raise AssertionError("worked out though the answer was there")
        again = solved.Solved(dict(first.found))
        with mock.patch.object(nav, "_grow", never):
            self.assertEqual(self.opened(again), plain)
        self.assertGreater(again.taken, 0)
        self.assertEqual(again.found, {})
        self.assertNotEqual(self.opened(solved.Solved(dict(first.found)), ZONES[:2]), plain)  # other zones: other names

    def test_an_answer_that_could_not_be_ours_is_worked_out_instead(self):
        plain = self.opened()
        first = solved.Solved()
        self.opened(first)
        key = next(k for k, v in first.found.items() if v[0])
        circles, left_out, _full = first.found[key]
        x, y, r = circles[0]
        spoiled = {
            "off the grid": [[(x + 1.0, y, r)] + circles[1:], left_out, False],
            "a radius that isn't whole steps": [[(x, y, r - 100.0)] + circles[1:], left_out, False],
            "too small": [[(x, y, 320.0)] + circles[1:], left_out, False],
            "outside every zone": [circles + [(60160.0, 60160.0, 1280.0)], left_out, False],
            "bigger than its zone": [[(x, y, r + 3200.0)] + circles[1:], left_out, False],
            "on ground units have already": [circles + [(6400.0, 30080.0, 1280.0)], left_out, False],
            "inside the circle before it": [circles[:1] + [(x + 640.0, y, 1280.0)] + circles[1:], left_out, False],
            "off the map": [circles + [(-640.0, 30080.0, 1280.0)], left_out, False],
            "said to be too many": [circles, left_out, True],
            "not circles": [[("a", "b", "c")], left_out, False],
            "a list of lists": [[list(c) for c in circles], left_out, False],
            "not an answer": "circles",
        }
        for what, bad in spoiled.items():
            store = solved.Solved({**first.found, key: bad})
            self.assertEqual(self.opened(store), plain, what)  # worked out here instead: the same graph
            self.assertIn(key, store.found, what)
        # one that passes every weighing but can't be reached from the ground: dropped, and worked out
        island = [(30080.0, 51840.0, 1280.0)]  # in the small zone alone, touching nothing
        store = solved.Solved({**first.found, key: [island, 0, False]})
        self.assertEqual(self.opened(store), plain)
        self.assertNotEqual(store.every().get(key), [island, 0, False])

    def test_the_ground_filled_back_round_a_block_from_the_answers(self):
        def blocked(store=None):
            g = row()
            with solved.using(store):
                counts = g.block([(7000.0, 2000.0, 400.0)])
            return g.to_bytes(), counts
        plain = blocked()
        first = solved.Solved()
        self.assertEqual(blocked(first), plain)
        key = next(k for k, v in first.found.items() if v)
        self.assertGreater(plain[1]["added"], 0)

        def never(*_a, **_k):
            raise AssertionError("worked out though the answer was there")
        again = solved.Solved(dict(first.found))
        with mock.patch.object(nav, "_fill", never):
            self.assertEqual(blocked(again), plain)
        self.assertEqual(again.taken, 1)
        x, y, r, source = first.found[key][0]
        for what, bad in {"in the block": [(7040.0, 1920.0, 1280.0, source)],
                          "past its source": [(x, y, r + 3200.0, source)],
                          "a source that isn't there": [(x, y, r, 99)],
                          "off the grid": [(x + 3.0, y, r, source)],
                          "on ground left": first.found[key] + [(1920.0, 1920.0, 1280.0, 0)],
                          "twice": [first.found[key][0], first.found[key][0]]}.items():
            self.assertEqual(blocked(solved.Solved({key: bad})), plain, what)


class InBuilds(unittest.TestCase):
    """The modder's export carries what the build worked out for the mod's maps (maps/<map>/solved.bin, locked with
    the game's own movement file); a build of the mod takes it from there and gives the same game files."""

    def game(self, root, size=16000.0):
        from fixtures import make_edat
        from test_build import PACK
        from test_open_ground import win_of
        game = root / "steamapps" / "common" / "R.U.S.E"
        rev = game / "Data" / "PC" / "190852"
        rev.mkdir(parents=True)
        (game / "RUSE.exe").write_bytes(b"MZ")
        (rev / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        (rev / "DataMap_Win.dat").write_bytes(make_edat(
            [("dir", "datasmap/blitz/".replace("/", "\\"), [("file", "mapinfo.win", win_of(row(), size=size))])]))
        (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
        return game

    def test_an_export_carries_the_answers_and_a_build_takes_them(self):
        import tempfile
        import zipfile
        from pathlib import Path
        from test_build import write_mod
        from rusemod import package
        from rusemod.build import build_and_write, load_mod
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = self.game(root)
            folder = write_mod(root / "mods", "paths", {})
            (folder / "maps" / "Blitz").mkdir(parents=True)
            (folder / "maps" / "Blitz" / "terrain.toml").write_text(
                '[[stroke]]\nbrush = "open_vehicles"\nx = 12500.0\ny = 2000.0\nradius = 2560.0\n', encoding="utf-8")
            built = root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat"
            lines: list = []
            first = build_and_write(game, [load_mod(folder)], instance=root / "copy", say=lines.append)
            self.assertEqual(first.errors, [], lines)
            self.assertEqual(sorted(first.solved), ["Blitz"])           # what its movement step worked out, locked
            self.assertFalse(any("came with the mod" in line for line in lines))
            self.assertEqual(solved.about(first.solved["Blitz"]), "Blitz")
            want = built.read_bytes()
            self.assertEqual(load_mod(folder)[0].solved, {})            # a build writes nothing into the mod
            out = package.pack(folder, root / "out", solved=first.solved)  # the export does
            file = folder / "maps" / "Blitz" / solved.FILE
            self.assertEqual(file.read_bytes(), first.solved["Blitz"])
            with zipfile.ZipFile(out) as z:
                self.assertIn("maps/Blitz/solved.bin", z.namelist())    # and the package carries it
            self.assertEqual(load_mod(folder)[0].solved, {"Blitz": first.solved["Blitz"]})

            def never(*_a, **_k):
                raise AssertionError("worked out though the answer came with the mod")
            lines = []
            with mock.patch.object(nav, "_grow", never):
                again = build_and_write(game, [load_mod(folder)], instance=root / "copy2", say=lines.append)
            self.assertEqual(again.errors, [], lines)
            self.assertTrue(any("worked-out answers came with the mod" in line for line in lines), lines)
            self.assertEqual((root / "copy2" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes(), want)
            self.assertEqual(again.solved, first.solved)                # the next export carries the same file
            self.assertEqual([f for f in again.findings if "weren't used" in f.message], [])

    def test_answers_that_do_not_open_are_left_out_with_a_note(self):
        import tempfile
        from pathlib import Path
        from test_build import write_mod
        from rusemod.build import build_and_write, load_mod
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = self.game(root)
            folder = write_mod(root / "mods", "paths", {})
            (folder / "maps" / "Blitz").mkdir(parents=True)
            (folder / "maps" / "Blitz" / "terrain.toml").write_text(
                '[[stroke]]\nbrush = "open_vehicles"\nx = 12500.0\ny = 2000.0\nradius = 2560.0\n', encoding="utf-8")
            first = build_and_write(game, [load_mod(folder)], instance=root / "copy", say=lambda _line: None)
            want = (root / "copy" / "Data" / "PC" / "190852" / "DataMap_Win.dat").read_bytes()
            good = first.solved["Blitz"]
            spoiled = bytearray(good)
            spoiled[len(spoiled) // 2] ^= 1
            for what, data in (("made with another game file", solved.pack({solved.name("x", 1): [1.0]}, b"other")),
                               ("changed", bytes(spoiled)), ("not a file of answers", b"hello")):
                (folder / "maps" / "Blitz" / solved.FILE).write_bytes(data)
                again = build_and_write(game, [load_mod(folder)], instance=root / what.replace(" ", "-"),
                                        say=lambda _line: None)
                self.assertEqual(again.errors, [], what)
                notes = [f.message for f in again.findings if f.level == "note" and "weren't used" in f.message]
                self.assertEqual(len(notes), 1, what)
                self.assertIn("paths", notes[0])
                self.assertIn("takes longer", notes[0])
                self.assertEqual((root / what.replace(" ", "-") / "Data" / "PC" / "190852"
                                  / "DataMap_Win.dat").read_bytes(), want, what)  # worked out here: the same files
                self.assertEqual(again.solved, first.solved, what)       # and the next export mends the file

    def test_the_keep_and_the_answers_go_together(self):
        """build._kept_movement: answers given make another name in the keep (what was made with them is theirs), and
        the answers a map's movement asked for come back from the keep too (a warm build can still export)."""
        import tempfile
        from rusemod import build
        from rusemod.cover import member
        from test_open_ground import win_of
        read = {member("Blitz"): win_of(row())}.get
        blocks = [nav.Block(12500.0, 2000.0, 2560.0, open=True)]
        real, made = nav.apply_blocks, []

        def counted(*args, **kwargs):
            made.append(1)
            return real(*args, **kwargs)
        with tempfile.TemporaryDirectory() as cache, mock.patch.object(nav, "apply_blocks", counted):
            first: dict = {}
            want = build._kept_movement(read, "Blitz", blocks, [], cache, None, first)
            self.assertTrue(first)
            warm: dict = {}
            self.assertEqual(build._kept_movement(read, "Blitz", blocks, [], cache, None, warm), want)
            self.assertEqual((len(made), warm), (1, first))             # from the keep, its answers with it
            given: dict = {}
            self.assertEqual(build._kept_movement(read, "Blitz", blocks, [], cache, dict(first), given), want)
            self.assertEqual((len(made), given), (2, first))            # with answers given: its own entry, the same
            stale = {solved.name("open", "an older version of the mod"): [[], 0, False]}
            carried: dict = {}
            self.assertEqual(build._kept_movement(read, "Blitz", blocks, [], cache, {**first, **stale}, carried), want)
            self.assertEqual(carried, first)                            # an answer nothing asked for isn't carried on


if __name__ == "__main__":
    unittest.main()
