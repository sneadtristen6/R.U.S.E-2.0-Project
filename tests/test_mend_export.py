"""The one check's findings 13 and 9 (the owner's numbered list of 2026-11-13), mended by fixer D.

13: a model record's .part file (the Studio writes a record beside itself, then puts it in place; one is left only when
the Studio is stopped in between) went into an exported mod as it was, the maker's folder in its "from". The class:
every file the Studio and the build leave beside one of their own while they write it (<name>.part, <stem>.part,
<name>.<program>.part, <name>.partial, <name>.tmp) stays out of the package (rusemod.package.is_work_file), so out of the
Launcher's copy of it and Publish's .zip (a byte copy of the package) too; Export names each it left out. A modder's own
file whose name only looks alike (part.json, tmp.csv, x.tmpl) goes out byte for byte.

9: with a platform folder of 140 characters or more the Horse Squad couldn't be added and the words said a picture
"isn't there" (the builder's scratch names took 120 characters; Windows stops at 260). Now the builder's scratch names are
short (rusemod.horsesquad.WORK_PREFIX, WORK_PARTS: 64 characters under the platform folder, the files it ends with named
as before), and before the long part the Add works out the longest path it is going to write, in the platform folder and
in the mod, and refuses in words saying which folder is too deep, by how many characters, and what to change
(ruse_studio.horse_squad._horse_room), unless this program may write longer paths (long_paths_on)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import os
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_build import write_mod
from test_horse_squad import GAME, GLBS, HEAVY, INDEX, RIFLE, finished, stand_in
from test_studio import WithMod
from rusemod import package
from ruse_studio import errortext, era_units, horse_squad
from ruse_studio.api import StudioApi, StudioError

FOLDER = "C:\\Users\\someone\\models"   # a maker's folder, as a record's "from" names it


def members(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}


def walk(folder: Path) -> list[str]:
    out = []
    for dirpath, dirs, files in os.walk(folder):
        out += [os.path.join(dirpath, n) for n in files + dirs]
    return out


# --- 13 ---
WORK_FILES = {   # each form a program of this Studio leaves while it writes (grep of src/: .part, .partial, .tmp)
    "files/models/Descriptor_Unit_Beast.json.part": json.dumps({"from": FOLDER + "\\beast.glb"}, indent=1),  # api
    "files/models/Descriptor_Unit_Cow.JSON.PART": json.dumps({"from": FOLDER + "\\cow.glb"}),   # (any case)
    "files/anim/units.part": "half of units.toml",                     # anim.py: with_suffix(".part")
    "files/anim/own/Descriptor_Unit_Beast/hr_ride.part": "half a clip",
    "maps/Blitz/kept.bin.1234.part": "half",                           # groundpaint: <name>.<program>.part
    "files/models/x.glb.1234-5678.part": "half",                       # model.py, mapkeep.py: <name>.<pid>-<thread>.part
    "text/index.json.partial": "half",                                 # edits.py, api.py: <name>.partial
    "src/units.rndf.tmp": "half",                                      # the engine's converter: <name>.tmp
}
LOOK_ALIKE = {   # a modder's own files whose names only look like those: they go out byte for byte
    "files/part.json": "{}", "files/my.parts.json": "{}", "text/tmp.csv": "key,us\n", "files/x.tmpl": "x",
    "files/models/partial.glb": "glb", "files/notes.part.md": "his notes", "files/temp/a.txt": "a",
}


class WorkFilesStayOut(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mod = write_mod(self.root, "cavalry", {"units.rndf": "patch $/B ( ProductionPrice *= 0.5 )"},
                             extra='name = "Cavalry"\n')
        for rel, text in {**WORK_FILES, **LOOK_ALIKE}.items():
            path = self.mod / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_what_the_studio_leaves_while_writing_never_goes_into_a_package_and_is_named(self):
        """FAILED before the mend: every work file went in (`files_of` packed all under files/, the cleaner only
        .json/.glb/texts), the record's .part with the maker's folder in it."""
        left_out = []
        out = package.pack(self.mod, self.root / "out", left_out=left_out)
        got = members(out)
        self.assertEqual([n for n in got if package.is_work_file(n)], [])
        for name, data in got.items():
            self.assertNotIn(b"someone", data, name)
        self.assertEqual(sorted(left_out), sorted(WORK_FILES))
        for rel in LOOK_ALIKE:
            self.assertEqual(got[rel], (self.mod / rel).read_bytes(), rel)
        for rel in WORK_FILES:
            self.assertTrue((self.mod / rel).is_file(), rel)   # (the mod folder itself: nothing taken from it)

    def test_files_of_names_what_it_left_out_and_a_mod_without_them_packs_as_before(self):
        """The control: with the work files gone, the package is what zipping files_of's list one by one gives, as
        before the mend (and `left_out` stays empty)."""
        for rel in WORK_FILES:
            (self.mod / rel).unlink()
        left_out = []
        out = package.pack(self.mod, self.root / "out", left_out=left_out)
        self.assertEqual(left_out, [])
        before = self.root / "before.zip"
        with zipfile.ZipFile(before, "w", zipfile.ZIP_DEFLATED) as z:
            for f in package.files_of(self.mod):
                z.write(f, f.relative_to(self.mod).as_posix())
        self.assertEqual(out.read_bytes(), before.read_bytes())
        self.assertEqual(sorted(members(out)), sorted(["mod.toml", "src/units.rndf", *LOOK_ALIKE]))


class TheStudiosExport(WithMod):
    def test_a_record_s_part_stays_out_of_the_export_and_the_launcher_s_copy_and_export_names_it(self):
        """Through the Studio's own Export: the .rusemod and the copy in his Launcher's library hold no .part, and
        Export's line names the file it left out, in his language too. The line needs api.export_mod to pass
        `left_out` to package.pack and say it (fixer D's report: a line in a file that isn't D's): FAILS until it
        does; the files themselves stay out without it."""
        folder = Path(self.api.new_mod("Shared")["current"])
        part = folder / "files" / "models" / "Descriptor_Unit_Beast.json.part"
        part.parent.mkdir(parents=True, exist_ok=True)
        part.write_text(json.dumps({"from": FOLDER + "\\beast.glb"}, indent=1), encoding="utf-8")
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        view = finished(self.api, self.api.export_mod("1.0.0", "a modder", "Cavalry.")["job"])
        self.assertEqual(view["state"], "done", view.get("message"))
        got = members(Path(view["result"]["path"]))
        self.assertEqual([n for n in got if n.endswith(".part")], [])
        library = self.home / "library" / package.info_of(folder)["id"]
        self.assertTrue(library.is_dir())
        self.assertEqual([p for p in walk(library) if p.lower().endswith(".part")], [])
        said = [ln for ln in view["lines"] if ln.startswith("Left out of the exported file:")]
        self.assertEqual(said, ["Left out of the exported file: files/models/Descriptor_Unit_Beast.json.part. These "
                                "are files the Studio left half written when it was stopped while writing them (their "
                                "names end in .part, .partial or .tmp); no build reads them."])
        self.api.set_pref("lang", "fr")
        self.assertEqual(len([ln for ln in self.api.job(view["id"])["lines"]
                              if ln.startswith("Laissés hors du fichier exporté")]), 1)


# --- 9 ---
def era_library(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": []}), encoding="utf-8")
    return folder


class TheAddsRoom(WithMod):
    """The Add's sum on the made-up game, the builder stood in for (its longest path said by the stand-in), Windows'
    long paths off as on the PCs this was tried on (long_paths_on: False)."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(era_library(
            Path(tempfile.mkdtemp(dir=self.tmp.name))))})
        patcher.start()
        self.addCleanup(patcher.stop)
        off = mock.patch.object(horse_squad, "long_paths_on", lambda: False)
        off.start()
        self.addCleanup(off.stop)
        files = Path(tempfile.mkdtemp(dir=self.tmp.name))
        self.rifle, self.heavy = files / "rifle.glb", files / "heavy.glb"
        self.rifle.write_bytes(b"glb rifle")
        self.heavy.write_bytes(b"glb heavy")
        self.folder = Path(self.api.new_mod("Room")["current"])

    def add(self, longest, name="Generic Horse"):
        """horse_squad_add with a stand-in builder whose longest path in `out` is `longest(out)`: (the job's view, or
        the StudioError it was refused with; the builder's calls)."""
        asked = []
        module = stand_in(self.rifle, self.heavy, asked=asked)
        module.longest_written = longest
        with mock.patch.dict(sys.modules, {horse_squad.BUILDER: module}), \
                mock.patch.object(StudioApi, "model_import", lambda api, address, file, **kw: None), \
                mock.patch.object(StudioApi, "_horse_check", lambda api, address: None):
            try:
                return finished(self.api, self.api.horse_squad_add(0, 10, name, 7, group="new")["job"]), asked
            except StudioError as exc:
                return exc, asked

    def tree(self):
        return {p: Path(p).read_bytes() for p in walk(self.folder) if Path(p).is_file()}

    def test_a_platform_folder_too_deep_is_refused_before_anything_is_made_saying_what_to_change(self):
        """FAILED before the mend: the add went on into the builder (which then stopped on a picture that "isn't
        there")."""
        before = self.tree()
        said, asked = self.add(lambda out: horse_squad.PATH_MOST + 3)
        self.assertIsInstance(said, StudioError)
        self.assertEqual(str(said), (
            f"The Generic Horse can't be added: the folder the Studio keeps its own files in ({self.home}) is too deep "
            f"for it. Adding it would write a file whose path is 3 character(s) longer than Windows takes "
            f"({horse_squad.PATH_MOST} at most). Move it to a folder with a shorter path, and set the Windows "
            f"environment variable RUSE_PLATFORM_HOME to that folder, then add it again."))
        self.assertEqual(asked, [])                                        # the builder never started
        self.assertFalse((self.home / horse_squad.FOLDER).exists())       # nothing made in the platform folder
        self.assertEqual(self.tree(), before)                              # nor in the mod
        self.assertNotIn(era_units.INDEX, [Path(p).name for p in walk(self.folder)])
        for lang in ("fr", "ger", "jpn", "fa"):
            worded = errortext.worded(str(said), lang)
            self.assertNotEqual(worded, str(said), lang)
            self.assertNotIn("too deep", worded, lang)
            self.assertIn(str(self.home), worded, lang)

    def test_a_path_windows_takes_exactly_is_added(self):
        """The legitimate edge: the builder's longest path PATH_MOST characters, the Horse Squad added."""
        view, asked = self.add(lambda out: horse_squad.PATH_MOST)
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(len(asked), 1)

    def test_a_mod_folder_too_deep_for_the_unit_s_animations_is_refused_and_a_name_one_shorter_is_added(self):
        """The mod's side: the unit's own animations go in <mod>/files/anim/own/<its address>/<clip>.part, so a name
        that makes that path 260 characters is refused naming the mod's folder, and one a letter shorter is added."""
        room = horse_squad.PATH_MOST - len(str(Path(self.folder, *horse_squad.OWN_CLIPS, "Descriptor_Unit_",
                                                    "x" * horse_squad.CLIP_LONGEST + ".part")))
        self.assertGreater(room, 20)
        before = self.tree()
        said, asked = self.add(lambda out: 10, name="H" * (room + 1))
        self.assertIsInstance(said, StudioError)
        self.assertEqual(str(said), (
            f"The Generic Horse can't be added: your mod's folder ({self.folder}) is too deep for it. Adding it would "
            f"write a file whose path is 1 character(s) longer than Windows takes ({horse_squad.PATH_MOST} at most). "
            f"Give it a shorter name in the form, or put the mod in a folder with a shorter path, then add it again."))
        self.assertEqual((asked, self.tree()), ([], before))
        self.assertNotIn("too deep", errortext.worded(str(said), "ru"))
        view, asked = self.add(lambda out: 10, name="H" * room)
        self.assertEqual(view["state"], "done", view.get("message"))
        self.assertEqual(view["result"]["address"].rsplit("/", 1)[-1], "Descriptor_Unit_" + "H" * room)

    def test_with_windows_long_paths_on_nothing_is_refused(self):
        with mock.patch.object(horse_squad, "long_paths_on", lambda: True):
            view, asked = self.add(lambda out: 10_000)
        self.assertEqual(view["state"], "done", view.get("message"))

    def test_a_builder_that_doesn_t_say_its_longest_path_is_not_refused_for_it(self):
        """A builder without longest_written (an older one): only the Add's own folder is counted."""
        view, _asked = self.add(None)
        self.assertEqual(view["state"], "done", view.get("message"))


class AFileTooLongAfterAll(unittest.TestCase):
    """A path the sum didn't see coming (a write Windows stopped for its length: Python's FileNotFoundError, as on
    2026-11-12) is said as a path too long, never as a file that "isn't there"; a file truly not there still is."""

    def test_a_path_past_windows_longest_is_said_as_too_long(self):
        import errno
        folder = Path("D:/" + "d" * 200) / horse_squad.FOLDER
        long = folder / ".m1234abcd" / "h1234abcd" / "b" / "us_soldier_bazooka_model_TSCOther_diffuseTexture01.png"
        with mock.patch.object(horse_squad, "long_paths_on", lambda: False):
            said = StudioApi._horse_file_error(FileNotFoundError(errno.ENOENT, "No such file", str(long)), folder)
            self.assertEqual(str(said), (
                f"The Generic Horse couldn't be added: {long} is {len(str(long)) - horse_squad.PATH_MOST} character(s) "
                f"longer than Windows takes in a path ({horse_squad.PATH_MOST} at most). Put the folder it is in "
                f"somewhere with a shorter path, then add it again."))
            self.assertIn("dépasse", errortext.worded(str(said), "fr"))
            short = Path("D:/m/horse_squad/horse-squad-rifle.glb")
            said = StudioApi._horse_file_error(FileNotFoundError(errno.ENOENT, "No such file", str(short)), folder)
            self.assertEqual(str(said), f"The Generic Horse couldn't be added: {short} isn't there.")
        with mock.patch.object(horse_squad, "long_paths_on", lambda: True):
            said = StudioApi._horse_file_error(FileNotFoundError(errno.ENOENT, "No such file", str(long)), folder)
            self.assertEqual(str(said), f"The Generic Horse couldn't be added: {long} isn't there.")


class TheBuildersNames(unittest.TestCase):
    def test_its_scratch_names_are_short_and_its_files_keep_their_names(self):
        from rusemod import horsesquad
        out = Path("C:/P/horse_squad") / (horse_squad.WORK + "x" * 8)
        self.assertEqual(horsesquad.longest_written(out),
                         len(str(out / ("h" + "x" * 8) / "b" / "us_soldier_bazooka_model.glb")))
        self.assertEqual(horsesquad.longest_written(out) - len("C:/P"), 64)   # (120 before: 140 + 120 > 259)
        self.assertEqual(horsesquad.FILES, {"rifle": "horse-squad-rifle.glb", "bazooka": "horse-squad-bazooka.glb"})

    @unittest.skipUnless(RIFLE.is_file() and HEAVY.is_file(), f"the passed copy's two files aren't in {GLBS}")
    def test_the_longest_animation_name_is_the_passed_copy_s(self):
        longest = 0
        for f in (RIFLE, HEAVY):
            data = f.read_bytes()
            doc = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
            longest = max([longest] + [len(a["name"]) for a in doc.get("animations", [])])
        self.assertEqual(longest, horse_squad.CLIP_LONGEST)

    @unittest.skipUnless(GAME is not None and GAME.is_dir(), "RUSE_GAME isn't set: the real builder needs the game")
    def test_the_real_builder_writes_nothing_longer_than_it_says(self):
        """The real builder, its scratch folder kept: every path it wrote is at most longest_written's, and one is that
        long (the sum is the builder's own, not a guess)."""
        from rusemod import horsesquad
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "o"
            with mock.patch.object(horsesquad.shutil, "rmtree", lambda *a, **k: None):
                horsesquad.horse_squad_glbs(GAME, out, index=INDEX if INDEX.is_file() else None, say=lambda _: None)
            lengths = [len(p) for p in walk(out)]
            self.assertEqual(max(lengths), horsesquad.longest_written(out))


@unittest.skipUnless(GAME is not None and GAME.is_dir() and RIFLE.is_file() and HEAVY.is_file(),
                     "RUSE_GAME isn't set, or the passed copy's two files aren't there")
class TheModsSide(unittest.TestCase):
    def test_nothing_the_add_writes_in_the_mod_is_longer_than_the_sum(self):
        """On the real game, the passed copy's two files handed over (the real import): every path the Add leaves in
        the mod is at most the sum's (<clip>.part) and the longest is its .baf, one shorter."""
        base = Path(tempfile.mkdtemp(prefix="R", dir=os.environ.get("RUSE_TEST_TMP")))
        try:
            home = base / "h"
            api = StudioApi(index_path=INDEX, game_dir=GAME, home=home, instances=home / "copies")
            mod = Path(api.new_mod("Room")["current"])
            with mock.patch.dict(sys.modules, {horse_squad.BUILDER: stand_in(RIFLE, HEAVY)}):
                view = finished(api, api.horse_squad_add(0, 8, "Generic Horse", 5, None, None, None, "new")["job"])
            self.assertEqual(view["state"], "done", view.get("message"))
            tail = view["result"]["address"].rsplit("/", 1)[-1]
            sum_ = len(str(Path(mod, *horse_squad.OWN_CLIPS, tail, "x" * horse_squad.CLIP_LONGEST + ".part")))
            self.assertEqual(max(len(p) for p in walk(mod)), sum_ - 1)
        finally:
            shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
