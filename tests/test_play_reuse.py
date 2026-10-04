"""Play reusing the modded copy (rusemod.play.built_from, rusemod.instance.needs_build and build_instance's reuse), on a
made-up game folder: an unchanged Play starts the copy with no build; any change, or a copy that isn't as its build
left it, builds again; a build takes the old copy's unchanged files as they are, and its copy holds exactly the bytes a
fresh build's would. A player's report, 2026-10-04: "Waiting 30 minutes every time just to add or remove a unit"."""
import json
import os
import re
import stat
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

from test_build import PACK, price, write_mod
from rusemod import instance as inst
from rusemod.build import build_and_write, load_mod
from rusemod.instance import NOTES, RECORD, Note, build_instance, needs_build, read_record, set_aside_old
from rusemod.play import Starter, built_from, in_words

ROOT = Path(__file__).resolve().parents[1]
UNITS = os.path.join("Data", "PC", "190852", "ZZ_GladPatchableWin.dat")
COMMON = os.path.join("Data", "PC", "190852", "Data_Common.dat")
LANG = os.path.join("Data", "lang.ini")


def make_game(root) -> Path:
    game = Path(root, "steamapps", "common", "R.U.S.E")
    (game / "Data" / "PC" / "190852").mkdir(parents=True)
    (game / "RUSE.exe").write_bytes(b"MZ the game")
    (game / UNITS).write_bytes(PACK)
    (game / COMMON).write_bytes(b"the common pack")
    (game / LANG).write_bytes(b"lang=us")
    Path(root, "steamapps", "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
    return game


def files_of(folder) -> dict:
    """{path inside: bytes} of every file in a copy but its record (which says when and how, not what)."""
    out = {}
    for root, _dirs, names in os.walk(folder):
        for n in names:
            path = os.path.join(root, n)
            rel = os.path.relpath(path, folder)
            if rel != RECORD:
                with open(path, "rb") as f:
                    out[rel] = f.read()
    return out


def refuse_links_from(folder):
    """os.link refusing links out of `folder` (the game's files, as on another drive); links elsewhere still made."""
    real = os.link
    key = os.path.normcase(os.path.abspath(folder)) + os.sep

    def link(src, dst, *args, **kwargs):
        if os.path.normcase(os.path.abspath(src)).startswith(key):
            raise OSError(18, "Invalid cross-device link")
        return real(src, dst, *args, **kwargs)
    return mock.patch("os.link", link)


def no_links():
    """os.link refusing every link (a drive whose file system has none: FAT32, exFAT)."""
    def link(*_args, **_kwargs):
        raise OSError(1, "links aren't supported here")
    return mock.patch("os.link", link)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = make_game(self.root)
        self.copy = self.root / "RUSE-Instances" / "Modded game"
        self.started, self.lines = [], []
        self.starter = Starter(open_url=lambda url: None, start_game=self.started.append,
                               steam_running=lambda: True, wait=lambda s: None)

    def tearDown(self):
        self.tmp.cleanup()

    def play(self, *mods, words=None):
        """One Play; returns how many builds it ran."""
        self.lines.clear()
        with mock.patch("rusemod.play.build_and_write", wraps=build_and_write) as built:
            self.starter.modded(self.game, [str(m) for m in mods], self.copy, "test", self.lines.append, words=words)
        return built.call_count


class Unchanged(Base):
    def test_an_unchanged_set_starts_the_copy_with_no_build(self):
        mod = write_mod(self.root, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.assertEqual(self.play(mod), 1)
        first = files_of(self.copy)
        self.assertEqual(self.play(mod), 0)  # nothing changed: nothing built
        self.assertEqual(self.lines[0], NOTES["play_unchanged"])
        self.assertNotIn("Building", "\n".join(self.lines))
        self.assertEqual(self.started, [self.copy / "RUSE.exe"] * 2)  # and the game starts from the copy
        self.assertEqual(files_of(self.copy), first)
        self.assertEqual(price((self.copy / UNITS).read_bytes()), [53] * 5)

    def test_the_old_copy_comes_back_when_the_mods_are_back_as_they_were(self):
        mod = write_mod(self.root, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.play(mod)
        first = files_of(self.copy)
        good = (mod / "src" / "eco.rndf").read_text(encoding="utf-8")
        (mod / "src" / "eco.rndf").write_text("patch $/Nope ( P = 1 )", encoding="utf-8")  # a mistake: no new copy
        with self.assertRaisesRegex(Exception, "errors"):
            self.play(mod)
        self.assertFalse(self.copy.exists())  # the old copy was set aside first, as before
        self.assertTrue(Path(str(self.copy) + ".old").is_dir())
        (mod / "src" / "eco.rndf").write_text(good, encoding="utf-8")  # the mistake undone
        self.assertEqual(self.play(mod), 0)  # the old copy is back, with no build
        self.assertEqual(self.lines[0], NOTES["play_unchanged"])
        self.assertEqual(files_of(self.copy), first)
        self.assertFalse(Path(str(self.copy) + ".old").exists())
        self.assertEqual(self.started[-1], self.copy / "RUSE.exe")

    def test_the_record_says_what_and_how(self):
        mod = write_mod(self.root, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.play(mod)
        record = read_record(str(self.copy))
        self.assertEqual(record["built_from"], json.loads(json.dumps(built_from(self.game, [str(mod)]))))
        kinds = {rel: e["kind"] for rel, e in record["files"].items()}
        self.assertEqual(kinds, {"RUSE.exe": "copy", UNITS: "written", COMMON: "link", LANG: "copy",
                                 "steam_appid.txt": "written"})
        self.assertEqual(needs_build(str(self.game), str(self.copy), built_from(self.game, [str(mod)])), "")


class Changes(Base):
    def test_a_changed_mod_builds_again(self):
        mod = write_mod(self.root, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.play(mod)
        (mod / "src" / "eco.rndf").write_text("patch $/B ( ProductionPrice *= 2 )", encoding="utf-8")
        self.assertEqual(self.play(mod), 1)
        self.assertEqual(price((self.copy / UNITS).read_bytes()), [210] * 5)
        (mod / "src" / "more.rndf").write_text("patch $/B ( ProductionPrice += 1 )", encoding="utf-8")  # a file added
        self.assertEqual(self.play(mod), 1)
        self.assertEqual(price((self.copy / UNITS).read_bytes()), [211] * 5)
        other = write_mod(self.root, "hardcore", {"hard.rndf": "patch $/B ( ProductionPrice += 5 )"})
        self.assertEqual(self.play(mod, other), 1)  # another mod in the set
        self.assertEqual(self.play(other, mod), 1)  # the same mods in another order
        self.assertEqual(self.play(other, mod), 0)

    def test_a_game_update_builds_again(self):
        mod = write_mod(self.root, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.play(mod)
        (self.game / LANG).write_bytes(b"lang=fr")  # Steam updated a file
        self.assertEqual(self.play(mod), 1)
        self.assertEqual((self.copy / LANG).read_bytes(), b"lang=fr")  # the copy has the new one, not the old copy's
        self.assertEqual(self.play(mod), 0)
        Path(self.root, "steamapps", "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24700000" }')
        self.assertEqual(self.play(mod), 1)  # a new build of the game
        (self.game / "Data" / "PC" / "190852" / "New.dat").write_bytes(b"a pack the update added")
        self.assertEqual(self.play(mod), 1)
        self.assertTrue((self.copy / "Data" / "PC" / "190852" / "New.dat").is_file())

    def test_a_mod_edited_while_the_build_reads_it_builds_again_next_time(self):
        mod = write_mod(self.root, "econ", {"eco.rndf": "patch $/B ( ProductionPrice *= 4 )"})
        eco = mod / "src" / "eco.rndf"

        def saved_meanwhile(path):  # the player saves the mod just after Play looked at it
            eco.write_text("patch $/B ( ProductionPrice *= 3 )", encoding="utf-8")
            return load_mod(path)
        with mock.patch("rusemod.play.load_mod", saved_meanwhile):
            self.assertEqual(self.play(mod), 1)
        self.assertEqual(price((self.copy / UNITS).read_bytes()), [315] * 5)
        self.assertFalse((self.copy / RECORD).exists())  # what it was built from isn't certain
        eco.write_text("patch $/B ( ProductionPrice *= 4 )", encoding="utf-8")  # back as Play first saw it
        self.assertEqual(self.play(mod), 1)  # built again: not the copy made from "*= 3"
        self.assertEqual(price((self.copy / UNITS).read_bytes()), [420] * 5)
        self.assertEqual(self.play(mod), 0)

    def test_a_mod_written_while_the_build_reads_it_builds_again_next_time(self):
        mod = write_mod(self.root, "econ", {"eco.rndf": "patch $/B ( ProductionPrice *= 4 )"})
        eco = mod / "src" / "eco.rndf"

        def written_meanwhile(path):  # changed and put back while it was read: the same bytes, a new time
            st = os.stat(eco)
            eco.write_text(eco.read_text(encoding="utf-8"), encoding="utf-8")
            os.utime(eco, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))
            return load_mod(path)
        with mock.patch("rusemod.play.load_mod", written_meanwhile):
            self.assertEqual(self.play(mod), 1)
        self.assertFalse((self.copy / RECORD).exists())
        self.assertEqual(self.play(mod), 1)
        self.assertEqual(self.play(mod), 0)

    def test_another_version_of_the_app_builds_again(self):
        mod = write_mod(self.root, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.play(mod)
        with mock.patch.dict("rusemod.play.CODE", {"rusemod": "another version"}):
            self.assertEqual(self.play(mod), 1)


class BrokenCopies(Base):
    def setUp(self):
        super().setUp()
        self.mod = write_mod(self.root, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.play(self.mod)
        self.fresh = files_of(self.copy)

    def rebuilt(self):
        self.assertEqual(self.play(self.mod), 1)
        self.assertEqual(files_of(self.copy), self.fresh)
        self.assertEqual(self.play(self.mod), 0)

    def test_a_file_missing(self):
        (self.copy / LANG).unlink()
        self.rebuilt()

    def test_a_written_pack_changed(self):
        with open(self.copy / UNITS, "r+b") as f:
            f.truncate(100)
        self.rebuilt()

    def test_a_copied_file_changed(self):
        (self.copy / "RUSE.exe").write_bytes(b"MZ something else")
        self.rebuilt()

    def test_a_link_to_the_game_replaced(self):
        (self.copy / COMMON).unlink()
        (self.copy / COMMON).write_bytes(b"the common pack")  # the same bytes, but no longer the game's file
        self.assertEqual(self.play(self.mod), 1)
        self.assertTrue(os.path.samefile(self.copy / COMMON, self.game / COMMON))

    def test_a_file_the_build_didnt_put_there(self):
        (self.copy / "Data" / "PC" / "190852" / "Stray.dat").write_bytes(b"a pack left in the copy")
        self.rebuilt()  # gone: the game could load it with the rest

    def test_no_record_or_one_that_cant_be_read(self):
        for broken in (None, "{not json", json.dumps({"format": 99}), json.dumps([1, 2])):
            if broken is None:
                (self.copy / RECORD).unlink()
            else:
                (self.copy / RECORD).write_text(broken, encoding="utf-8")
            self.rebuilt()

    def test_a_copy_of_another_game_folder(self):
        record = json.loads((self.copy / RECORD).read_text(encoding="utf-8"))
        record["game"] = str(self.root / "elsewhere")
        (self.copy / RECORD).write_text(json.dumps(record), encoding="utf-8")
        self.rebuilt()


class Reuse(unittest.TestCase):
    """build_instance taking the old copy's unchanged files: what it holds is what a fresh build would hold."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.game = str(make_game(self.root))
        self.dst = str(self.root / "copies" / "inst")

    def tearDown(self):
        self.tmp.cleanup()

    def fresh(self, **kwargs) -> dict:
        where = str(self.root / "fresh" / str(len(os.listdir(self.root / "fresh")) if (self.root / "fresh").is_dir()
                                              else 0))
        build_instance(self.game, where, **kwargs)
        return files_of(where)

    def test_a_replaced_then_unreplaced_pack_goes_back_to_the_games_file(self):
        build_instance(self.game, self.dst, replace={UNITS: b"MODDED"})
        self.assertEqual(Path(self.dst, UNITS).read_bytes(), b"MODDED")
        counts = build_instance(self.game, self.dst)
        self.assertTrue(os.path.samefile(os.path.join(self.dst, UNITS), os.path.join(self.game, UNITS)))
        self.assertEqual(counts, {"linked": 2, "copied": 0, "written": 0, "kept": 2})
        self.assertEqual(Path(self.game, UNITS).read_bytes(), PACK)  # the game's pack as it was
        self.assertEqual(files_of(self.dst), self.fresh())

    def test_on_another_drive_the_old_copys_packs_are_kept(self):
        with refuse_links_from(self.game):
            first = build_instance(self.game, self.dst, replace={UNITS: b"MODDED"})
            self.assertEqual(first.copied_bytes, sum(len(b) for rel, b in files_of(self.game).items() if rel != UNITS))
            old_common = os.stat(os.path.join(self.dst, COMMON))
            counts = build_instance(self.game, self.dst, replace={UNITS: b"MODDED 2"})
            self.assertEqual(counts, {"linked": 0, "copied": 0, "written": 1, "kept": 3})
            self.assertEqual(counts.copied_bytes, 0)  # nothing copied again
            new_common = os.stat(os.path.join(self.dst, COMMON))
            self.assertEqual((new_common.st_ino, new_common.st_dev), (old_common.st_ino, old_common.st_dev))
            self.assertEqual(files_of(self.dst), self.fresh(replace={UNITS: b"MODDED 2"}))
            build_instance(self.game, self.dst)  # the replaced pack goes back: a copy of the game's
            self.assertEqual(Path(self.dst, UNITS).read_bytes(), PACK)
            self.assertFalse(os.path.samefile(os.path.join(self.dst, UNITS), os.path.join(self.game, UNITS)))
            self.assertEqual(files_of(self.dst), self.fresh())

    def test_a_drive_without_links_moves_the_files_out_of_the_old_copy_set_aside(self):
        with no_links():
            build_instance(self.game, self.dst, replace={UNITS: b"MODDED"})
            set_aside_old(self.game, self.dst)  # as Play does: renamed .old, not started by mistake
            self.assertFalse(os.path.exists(self.dst))
            self.assertTrue(os.path.isdir(self.dst + ".old"))
            counts = build_instance(self.game, self.dst)
            self.assertEqual(counts.copied_bytes, len(PACK))  # only the pack that was replaced, back from the game
            self.assertEqual(counts["kept"], 3)
            self.assertEqual(files_of(self.dst), self.fresh())
        self.assertFalse(os.path.exists(self.dst + ".old"))

    def test_a_stopped_build_leaves_the_old_copy_whole(self):
        with no_links():
            build_instance(self.game, self.dst, replace={UNITS: b"MODDED"})
            before = files_of(self.dst)
            set_aside_old(self.game, self.dst)

            def fail(_f):
                raise OSError("disk full")

            with self.assertRaises(OSError):
                build_instance(self.game, self.dst, replace={UNITS: fail})
            self.assertEqual(files_of(self.dst + ".old"), before)  # what moved out went back
            self.assertFalse(os.path.exists(self.dst + ".partial"))
            build_instance(self.game, self.dst, replace={UNITS: b"MODDED"})
            self.assertEqual(files_of(self.dst), before)

    def test_a_copy_in_place_stays_whole_until_the_new_one_is_in(self):
        build_instance(self.game, self.dst, replace={UNITS: b"FIRST"})
        with refuse_links_from(self.game):
            def fail(_f):
                raise OSError("disk full")

            with self.assertRaises(OSError):
                build_instance(self.game, self.dst, replace={UNITS: fail})
        self.assertEqual(Path(self.dst, UNITS).read_bytes(), b"FIRST")
        self.assertIsNotNone(read_record(self.dst))
        self.assertFalse(os.path.exists(self.dst + ".partial"))

    def test_an_unchanged_copy_of_a_changed_game_file_isnt_kept(self):
        build_instance(self.game, self.dst)
        Path(self.game, LANG).write_bytes(b"lang=ger")
        counts = build_instance(self.game, self.dst)
        self.assertEqual(counts["copied"], 1)
        self.assertEqual(Path(self.dst, LANG).read_bytes(), b"lang=ger")

    def test_a_read_only_game_keeps_nothing_read_only(self):
        for path in (UNITS, COMMON, LANG, "RUSE.exe"):
            os.chmod(os.path.join(self.game, path), stat.S_IREAD)
        try:
            build_instance(self.game, self.dst)
            counts = build_instance(self.game, self.dst, replace={UNITS: b"MODDED"})
            self.assertEqual(counts, {"linked": 0, "copied": 0, "written": 1, "kept": 3})
            for root, _dirs, names in os.walk(self.dst):
                for n in names:
                    self.assertTrue(os.stat(os.path.join(root, n)).st_mode & stat.S_IWRITE, n)
            self.assertFalse(os.stat(os.path.join(self.game, COMMON)).st_mode & stat.S_IWRITE)  # the game's mark stays
        finally:
            for path in (UNITS, COMMON, LANG, "RUSE.exe"):
                os.chmod(os.path.join(self.game, path), stat.S_IREAD | stat.S_IWRITE)

    def test_a_new_maps_pack_no_longer_added_goes(self):
        new = os.path.join("Maps", "PC", "DataMapNew_v09.dat")
        build_instance(self.game, self.dst, add={new: b"NEW MAP"})
        build_instance(self.game, self.dst)
        self.assertFalse(os.path.exists(os.path.join(self.dst, new)))
        self.assertEqual(files_of(self.dst), self.fresh())

    def test_the_record_is_written_last(self):
        written = []
        real = inst._write_record

        def record(folder, *args):
            written.append(sorted(files_of(folder)))
            real(folder, *args)
        with mock.patch("rusemod.instance._write_record", record):
            build_instance(self.game, self.dst, replace={UNITS: b"MODDED"})
        self.assertEqual(written, [sorted(files_of(self.dst))])  # everything else was there already


class Words(unittest.TestCase):
    """The build's lines for the player, in both apps' ten languages."""

    def test_both_apps_have_every_note_in_ten_languages(self):
        langs = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")
        for app in ("ruse_launcher", "ruse_studio"):
            words = tomllib.loads((ROOT / "src" / app / "words.toml").read_text(encoding="utf-8"))
            for name, english in NOTES.items():
                self.assertEqual(words[name]["us"], english, (app, name))
                blanks = set(re.findall(r"\{(\w+)\}", english))
                for lang in langs:
                    self.assertEqual(set(re.findall(r"\{(\w+)\}", words[name][lang])), blanks, (app, name, lang))

    def test_the_apps_say_them_in_the_players_language(self):
        lines = []
        say = in_words(lines.append, {"play_other_drive": "Autre disque : {gb} Go copiés, {drive}."})
        say(Note("play_other_drive", gb="2.3", drive="D:"))
        say("load order: econ-half")
        say(Note("play_unchanged"))  # a word the app hasn't got: the English
        self.assertEqual(lines, ["Autre disque : 2.3 Go copiés, D:.", "load order: econ-half", NOTES["play_unchanged"]])

    def test_another_drive_is_said_once_with_what_was_copied(self):
        with tempfile.TemporaryDirectory() as d:
            game = make_game(d)
            mod = write_mod(d, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
            from rusemod.build import load_mod
            lines = []
            with refuse_links_from(game), mock.patch("rusemod.instance._other_drive", lambda src, dst: True):
                build_and_write(game, [load_mod(mod)], instance=Path(d, "copy"), say=lines.append)
            notes = [line for line in lines if isinstance(line, Note)]
            self.assertEqual([n.word for n in notes], ["play_other_drive"])
            copied = len(b"MZ the game") + len(b"the common pack") + len(b"lang=us")
            self.assertEqual(notes[0].data["gb"], f"{copied / (1 << 30):.1f}")

    def test_a_drive_without_links_is_said_by_its_file_system(self):
        with tempfile.TemporaryDirectory() as d:
            game = make_game(d)
            mod = write_mod(d, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
            from rusemod.build import load_mod
            for fs, said in (("exFAT", ["doc_drive_other"]), ("NTFS", [])):  # NTFS shares files: something else
                lines = []
                with no_links(), mock.patch("rusemod.winfiles.volume", lambda path, fs=fs: {"fs": fs}):
                    build_and_write(game, [load_mod(mod)], instance=Path(d, fs), say=lines.append)
                notes = [line for line in lines if isinstance(line, Note)]
                self.assertEqual([n.word for n in notes], said, fs)
                if said:
                    self.assertEqual(notes[0].data, {"path": d, "fs": "exFAT"})


if __name__ == "__main__":
    unittest.main()
