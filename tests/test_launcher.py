"""The launcher app's back end (ruse_launcher.api) on a made-up game folder; nothing starts for real."""
import json
import os
import re
import sys
import tempfile
import time
import unittest
import urllib.request
import zipfile
from pathlib import Path
from unittest import mock

from test_build import PACK, price, write_mod
from ruse_launcher import app
from ruse_launcher.api import MOD_FILES, LauncherApi, LauncherError, _words, language_code, words
from rusemod import package, schema
from rusemod.play import STEAM_OPEN, STEAM_PLAY, keep_order
from rusemod.resolve import ModInfo
from rusemod.webui import serve
import hashlib


def wait_for(api, job_id, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        j = api.job(job_id)
        if j["state"] != "running":
            return j
        time.sleep(0.02)
    raise AssertionError("the job didn't finish")


class Base(unittest.TestCase):
    """A launcher on a made-up game folder, with a fresh platform folder per test; nothing starts for real."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.game = root / "steamapps" / "common" / "R.U.S.E"
        (self.game / "Data" / "PC" / "190852").mkdir(parents=True)
        (self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        (root / "steamapps" / "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
        self.home, self.instances = root / "home", root / "copies"
        self.urls, self.started = [], []
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop("RUSE_GAME", None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def api(self, **kw):
        args = dict(game_dir=self.game, home=self.home, instances=self.instances, open_url=self.urls.append,
                    start_game=self.started.append, steam_running=lambda: True, wait=lambda s: None)
        args.update(kw)
        return LauncherApi(**args)

    def mod_set(self, name, mods, body=""):
        (self.home / "sets").mkdir(parents=True, exist_ok=True)
        lines = ", ".join(f'"{Path(m).as_posix()}"' for m in mods)
        (self.home / "sets" / f"{name}.toml").write_text(f'name = "{name.title()}"\nmods = [{lines}]\n{body}',
                                                         encoding="utf-8")


class Launcher(Base):
    def test_status(self):
        s = self.api().status()
        self.assertTrue(s["found"])
        self.assertEqual(s["build"], "24687178")
        self.assertIn("(build 24687178)", s["message"])
        s = self.api(game_dir=None, find=lambda: None).status()
        self.assertEqual((s["found"], s["message"]), (False, "We couldn't find R.U.S.E. Is it installed through Steam?"))

    def test_choosing_the_game_folder(self):
        wrong = Path(self.tmp.name)
        api = self.api(game_dir=None, find=lambda: None, pick_folder=lambda: str(wrong))
        self.assertIn("doesn't have RUSE.exe", api.choose_game_folder()["message"])
        api._pick_folder = lambda: str(self.game)
        self.assertTrue(api.choose_game_folder()["found"])
        self.assertTrue(self.api(game_dir=None, find=lambda: None).status()["found"])  # remembered

    def test_mod_sets(self):
        mod = write_mod(self.tmp.name, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.mod_set("half", [mod], 'description = "Every building costs half."\n')
        self.mod_set("empty", [])
        (self.home / "sets" / "Bad Name.toml").write_text("mods = []", encoding="utf-8")
        sets = self.api().mod_sets()
        self.assertEqual([s["id"] for s in sets], ["vanilla", "bad name", "empty", "half"])
        half = sets[-1]
        self.assertEqual((half["name"], half["description"], half["mod_names"]),
                         ("Half", "Every building costs half.", ["econ-half"]))
        self.assertIn("lowercase", sets[1]["error"])
        self.assertEqual(sets[2]["error"], "it lists no mods")

    def test_play_vanilla_goes_through_steam(self):
        api = self.api()
        j = wait_for(api, api.play("vanilla")["job"])
        self.assertEqual((j["state"], self.urls), ("done", [STEAM_PLAY]))

    def test_play_a_mod_set_builds_the_copy_and_starts_it(self):
        mod = write_mod(self.tmp.name, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.mod_set("half", [mod])
        api = self.api()
        j = wait_for(api, api.play("half")["job"])
        self.assertEqual(j["state"], "done", j)
        copy = self.instances / "half"
        self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
        self.assertEqual(self.started, [copy / "RUSE.exe"])
        self.assertTrue(any("modded copy ready" in line for line in j["lines"]))
        later = api.job(j["id"], since=j["count"])
        self.assertEqual(later["lines"], [])  # `since` skips the lines already shown

    def test_steam_is_started_first_when_it_isnt_running(self):
        mod = write_mod(self.tmp.name, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.mod_set("half", [mod])
        answers = iter([False, False, True])
        api = self.api(steam_running=lambda: next(answers))
        j = wait_for(api, api.play("half")["job"])
        self.assertEqual(j["state"], "done", j)
        self.assertEqual(self.urls, [STEAM_OPEN])
        self.assertIn("Starting Steam…", j["lines"])

    def test_problems_end_the_job_with_a_plain_message(self):
        bad = write_mod(self.tmp.name, "bad", {"x.rndf": "patch $/Nope ( P = 1 )"})
        self.mod_set("bad", [bad])
        self.mod_set("empty", [])
        api = self.api()
        j = wait_for(api, api.play("bad")["job"])
        self.assertEqual(j["state"], "failed")
        self.assertIn("have errors", j["message"])
        self.assertEqual(self.started, [])
        self.assertIn("has a mistake", api.job(api.play("empty")["job"])["message"])
        self.assertIn("no mod set called", api.job(api.play("nope")["job"])["message"])


HALF = {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"}
TEN = {"ten.rndf": "patch $/B ( ProductionPrice = [10, 10, 10, 10, 10] )"}


def make_zip(path: Path, files: dict, prefix: str = "") -> Path:
    """A .zip of a mod: `files` maps paths inside the mod to text, written under `prefix` ("mymod/" or "")."""
    with zipfile.ZipFile(path, "w") as z:
        for rel, text in files.items():
            z.writestr(prefix + rel, text)
    return path


class Library(Base):
    """The mod library: mods added from a folder, a .zip or a .rusemod file, checked first, listed, removed."""

    def mod(self, mod_id, files=HALF, extra=""):
        return write_mod(Path(self.tmp.name, "downloads"), mod_id, files, extra=extra)

    def test_a_mod_folder_is_checked_copied_and_listed(self):
        api = self.api()
        self.assertEqual(api.library(), [])
        folder = self.mod("econ-half", extra='name = "Half price"\nauthors = ["A", "B"]\ndescription = "Half.\"\n'
                                             '[game]\nbuilds = ["24687178"]\n')
        res = api.add_mod(str(folder))
        self.assertEqual((res["replaced"], res["mod"]["id"], res["mod"]["name"]), (False, "econ-half", "Half price"))
        mod = res["library"][0]
        self.assertEqual((mod["version"], mod["author"], mod["description"], mod["builds"], mod["used_in"]),
                         ("1.0.0", "A, B", "Half.", ["24687178"], 0))
        self.assertEqual(mod["path"], str(self.home / "library" / "econ-half"))
        self.assertTrue((self.home / "library" / "econ-half" / "src" / "eco.rndf").is_file())
        self.assertEqual([s["id"] for s in res["sets"]], ["vanilla"])  # every change returns the fresh lists
        again = api.add_mod(str(folder / "mod.toml"))  # the file inside the folder does the same
        self.assertEqual((again["replaced"], len(again["library"])), (True, 1))
        newer = self.mod("econ-half", extra='name = "Half price"\n').with_name("econ-half")
        (newer / "mod.toml").write_text('[mod]\nid = "econ-half"\nversion = "1.1.0"\nname = "Half price"\n', encoding="utf-8")
        res = api.add_mod(str(newer))
        self.assertEqual((res["replaced"], res["mod"]["version"], res["library"][0]["version"]), (True, "1.1.0", "1.1.0"))
        self.assertEqual([p.name for p in (self.home / "library").iterdir()], ["econ-half"])  # no leftovers

    def test_a_zip_is_unpacked_from_its_top_or_from_one_folder(self):
        api = self.api()
        files = {"mod.toml": '[mod]\nid = "zipped"\nversion = "2.0.0"\nname = "Zipped"\n',
                 "src/eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )", "README.md": "hello"}
        res = api.add_mod(str(make_zip(Path(self.tmp.name, "a.zip"), files, "Zipped Mod/")))
        self.assertEqual((res["mod"]["id"], res["mod"]["version"]), ("zipped", "2.0.0"))
        self.assertEqual((self.home / "library" / "zipped" / "README.md").read_text(encoding="utf-8"), "hello")
        res = api.add_mod(str(make_zip(Path(self.tmp.name, "b.zip"), files)))  # mod.toml at the top
        self.assertEqual((res["replaced"], len(res["library"])), (True, 1))

    def test_mods_that_cant_go_in(self):
        api = self.api()
        bad_rndf = self.mod("broken", {"x.rndf": "patch $/B ( ProductionPrice = \n"})
        script = self.mod("scripted", HALF)
        (script / "src" / "hack.py").write_text("print(1)", encoding="utf-8")
        no_toml = Path(self.tmp.name, "plain")
        no_toml.mkdir()
        bad_id = self.mod("bad-id", HALF).with_name("bad-id")
        (bad_id / "mod.toml").write_text('[mod]\nid = "Bad Id"\n', encoding="utf-8")
        no_toml_zip = make_zip(Path(self.tmp.name, "nomod.zip"), {"readme.txt": "x"})
        exe_zip = make_zip(Path(self.tmp.name, "exe.zip"), {"mod.toml": '[mod]\nid = "x"\n', "tool.exe": "MZ"})
        slip = Path(self.tmp.name, "slip.zip")
        with zipfile.ZipFile(slip, "w") as z:
            z.writestr("mod.toml", '[mod]\nid = "slip"\n')
            z.writestr("../evil.txt", "x")
        for path, why in [(bad_rndf, "mistake"), (script, "scripts or programs"), (no_toml, "no mod.toml"),
                          (bad_id, "lowercase"), (no_toml_zip, "no mod.toml"), (exe_zip, "scripts or programs"),
                          (slip, "safely"), (Path(self.tmp.name, "nope"), "doesn't exist"),
                          (Path(self.tmp.name, "nomod.zip").with_suffix(".txt"), "isn't a mod")]:
            if path.suffix == ".txt":
                path.write_text("x", encoding="utf-8")
            with self.subTest(path=path.name), self.assertRaises(LauncherError) as cm:
                api.add_mod(str(path))
            self.assertIn(why, str(cm.exception))
        self.assertEqual(api.library(), [])
        self.assertEqual([p.name for p in (self.home / "library").iterdir()], [])  # nothing half-added

    def test_a_mod_file_from_the_studio_is_installed_and_plays(self):
        folder = self.mod("econ-half", extra='name = "Half price"\nauthors = ["Tristen"]\n')
        file = package.pack(folder, Path(self.tmp.name), build_id="24687178", fingerprint="K7Q2-M9XD")
        self.assertEqual(file.name, "econ-half-1.0.0.rusemod")
        api = self.api(pick_file=lambda: str(file))
        mod = api.add_mod_file()["library"][0]
        self.assertEqual((mod["id"], mod["version"], mod["author"], mod["builds"], mod["fingerprint"]),
                         ("econ-half", "1.0.0", "Tristen", ["24687178"], "K7Q2-M9XD"))
        self.assertTrue((self.home / "library" / "econ-half" / "src" / "eco.rndf").is_file())
        api.new_set("Half", ["econ-half"])
        j = wait_for(api, api.play("half")["job"])
        self.assertEqual(j["state"], "done", j)
        copy = self.instances / "half"
        self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
        broken = Path(self.tmp.name, "broken.rusemod")
        with zipfile.ZipFile(broken, "w") as z:
            z.writestr("mod.toml", '[mod]\nid = "broken"\nversion = "1.0.0"\n')
            z.writestr("src/x.rndf", "patch $/B ( ProductionPrice = \n")
        with self.assertRaises(LauncherError) as cm:
            api.add_mod(str(broken))
        self.assertIn("mistake", str(cm.exception))
        self.assertEqual(len(api.library()), 1)
        self.assertEqual(MOD_FILES[0], "Mods (*.rusemod;*.rmod;*.zip;*.toml)")

    def test_removing_a_mod(self):
        api = self.api()
        api.add_mod(str(self.mod("econ-half")))
        api.new_set("Half", ["econ-half"])
        self.assertEqual(api.library()[0]["used_in"], 1)
        res = api.remove_mod("econ-half")
        self.assertEqual((res["mod"]["id"], res["library"]), ("econ-half", []))
        self.assertFalse((self.home / "library" / "econ-half").exists())
        half = res["sets"][1]
        self.assertIn("isn't in the library", half["error"])
        self.assertEqual(half["mod_names"], ["econ-half"])
        with self.assertRaises(LauncherError):
            api.remove_mod("econ-half")
        with self.assertRaises(LauncherError):
            api.remove_mod("../home")

    def test_the_file_dialog_and_dropped_files(self):
        folder = self.mod("econ-half")
        api = self.api(pick_file=lambda: None)
        self.assertEqual((api.add_mod_file()["mod"], api.library()), (None, []))  # cancelled
        api = self.api(pick_file=lambda: str(folder / "mod.toml"))
        self.assertEqual(api.add_mod_file()["mod"]["id"], "econ-half")
        self.assertEqual(self.api().add_mod_file()["mod"], None)  # no window: nothing to ask with

        told = []
        window = mock.Mock(evaluate_js=told.append)
        app.dropped(api, window, [str(folder), str(Path(self.tmp.name, "nope.zip"))])
        events = [json.loads(re.search(r"detail: (.*)\}\)\)$", js).group(1)) for js in told]
        self.assertEqual((events[0]["ok"], events[0]["mod"]["id"], events[0]["replaced"]), (True, "econ-half", True))
        self.assertEqual(events[1]["ok"], False)
        self.assertIn("doesn't exist", events[1]["message"])


class SetsOnScreen(Base):
    """Mod sets made in the window: new, edit, rename, duplicate, delete; the order is kept and counts when playing."""

    def setUp(self):
        super().setUp()
        self.lib = self.api()
        for mod_id, files in (("aaa-half", HALF), ("bbb-ten", TEN)):
            self.lib.add_mod(str(write_mod(Path(self.tmp.name, "dl"), mod_id, files, extra=f'name = "{mod_id.title()}"\n')))

    def test_new_edit_rename_duplicate_delete(self):
        api = self.api()
        res = api.new_set("My Set!", ["bbb-ten", "aaa-half"])
        self.assertEqual(res["set"], "my-set")
        self.assertEqual((self.home / "sets" / "my-set.toml").read_text(encoding="utf-8"),
                         'name = "My Set!"\ndescription = ""\nmods = ["bbb-ten", "aaa-half"]\n')
        mine = res["sets"][1]
        self.assertEqual((mine["name"], mine["mods"], mine["mod_names"], mine["error"], mine["editable"]),
                         ("My Set!", ["bbb-ten", "aaa-half"], ["Bbb-Ten", "Aaa-Half"], None, True))
        self.assertEqual([m["used_in"] for m in res["library"]], [1, 1])
        self.assertEqual(res["sets"][0]["editable"], False)  # Vanilla

        res = api.save_set("my-set", "My Set!", ["aaa-half", "bbb-ten"])  # the order changed
        self.assertEqual(res["sets"][1]["mods"], ["aaa-half", "bbb-ten"])
        res = api.save_set("my-set", "Renamed")  # a rename keeps the mods and the id
        self.assertEqual((res["set"], res["sets"][1]["name"], res["sets"][1]["mods"]), ("my-set", "Renamed", ["aaa-half", "bbb-ten"]))

        res = api.duplicate_set("my-set", "Renamed (copy)")
        self.assertEqual(res["set"], "renamed-copy")
        self.assertEqual([(s["id"], s["mods"]) for s in res["sets"]],
                         [("vanilla", []), ("my-set", ["aaa-half", "bbb-ten"]), ("renamed-copy", ["aaa-half", "bbb-ten"])])
        res = api.delete_set("my-set")
        self.assertEqual((res["set"], [s["id"] for s in res["sets"]]), ("vanilla", ["vanilla", "renamed-copy"]))
        self.assertFalse((self.home / "sets" / "my-set.toml").exists())
        self.assertEqual([s["id"] for s in api.new_set("Test", ["aaa-half"])["sets"]], ["vanilla", "renamed-copy", "test"])
        self.assertEqual(api.new_set("Test", ["aaa-half"])["set"], "test-2")  # names can repeat, ids can't
        self.assertEqual(api.new_set("Vanilla", ["aaa-half"])["set"], "vanilla-2")

    def test_what_cant_be_done(self):
        api = self.api()
        for name, mods in [("", ["aaa-half"]), ("x", []), ("x", ["nope"]), ("x", ["aaa-half", "aaa-half"]), ("x", "aaa-half"),
                           ("x", [""])]:
            with self.subTest(name=name, mods=mods), self.assertRaises(LauncherError):
                api.new_set(name, mods)
        for call in (lambda: api.save_set("vanilla", "x"), lambda: api.delete_set("vanilla"),
                     lambda: api.duplicate_set("vanilla", "x"), lambda: api.save_set("nope", "x"),
                     lambda: api.delete_set("nope")):
            with self.assertRaises(LauncherError):
                call()
        with self.assertRaises(LauncherError) as cm:
            api.new_set("x", ["nope"])
        self.assertIn("Add a mod file", str(cm.exception))  # says what to do next
        self.assertEqual(api.mod_sets()[1:], [])

    def test_play_builds_a_set_made_on_screen_in_its_order(self):
        api = self.api()
        api.new_set("Ten then half", ["bbb-ten", "aaa-half"])
        j = wait_for(api, api.play("ten-then-half")["job"])
        self.assertEqual(j["state"], "done", j)
        copy = self.instances / "ten-then-half"
        self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [5] * 5)
        self.assertIn("load order: bbb-ten -> aaa-half", j["lines"])  # the set's order, not the ids' order
        api.new_set("Half then ten", ["aaa-half", "bbb-ten"])
        j = wait_for(api, api.play("half-then-ten")["job"])
        self.assertEqual(j["state"], "done", j)
        copy = self.instances / "half-then-ten"
        self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [10] * 5)
        self.assertEqual(len(self.started), 2)

    def test_hand_written_sets_still_work_and_can_be_edited(self):
        folder = write_mod(Path(self.tmp.name, "elsewhere"), "econ-half", HALF)
        self.mod_set("old", [folder, "bbb-ten"])  # a folder by path, and a library mod by id
        api = self.api()
        old = api.mod_sets()[-1]
        self.assertEqual((old["mod_names"], old["error"]), (["econ-half", "Bbb-Ten"], None))
        res = api.save_set("old", "Old", ["bbb-ten", str(folder)])
        self.assertEqual(res["sets"][-1]["mod_names"], ["Bbb-Ten", "econ-half"])
        j = wait_for(api, api.play("old")["job"])
        self.assertEqual(j["state"], "done", j)

    def test_the_order_rule(self):
        a, b, c = ModInfo("a"), ModInfo("b"), ModInfo("c", before=["b"])
        keep_order([(c, []), (b, []), (a, [])])
        self.assertEqual((a.after, b.after, c.after), (["b"], [], []))  # c and b already say how they relate


class Browse(Base):
    """Browse mods: the mod index on a local web server, installs checked against it, the copy kept for offline."""

    def setUp(self):
        super().setUp()
        self.www = Path(self.tmp.name, "www")
        self.www.mkdir()
        folder = write_mod(Path(self.tmp.name, "src"), "econ-half", HALF, extra='name = "Half price"\nauthors = ["Tristen"]\n')
        self.file = package.pack(folder, self.www, build_id="24687178", fingerprint="K7Q2-M9XD")
        self.server, self.base = serve(self.www)
        self.write_index("1.0.0")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        super().tearDown()

    def write_index(self, version, extra=""):
        data = self.file.read_bytes()
        (self.www / "index.toml").write_text(
            'format = 1\n\n[[mod]]\nid = "econ-half"\nname = "Half price"\nversion = "%s"\nauthor = "Tristen"\n'
            'description = "Every building costs half."\nhomepage = "https://example.com/half"\n'
            'download = "%s/%s"\nsize = %d\nsha256 = "%s"\ngame_build = "24687178"\nfingerprint = "K7Q2-M9XD"\n'
            'tags = ["economy"]\n%s' % (version, self.base, self.file.name, len(data), hashlib.sha256(data).hexdigest(), extra),
            encoding="utf-8")

    def browser(self, **kw):
        return self.api(index_url=f"{self.base}/index.toml", **kw)

    def test_the_list_its_states_and_search(self):
        api = self.browser()
        res = api.browse()
        self.assertEqual((res["source"], res["message"], res["problems"]), ("online", "", []))
        mod = res["mods"][0]
        self.assertEqual((mod["id"], mod["name"], mod["version"], mod["author"], mod["state"], mod["game_build"], mod["tags"]),
                         ("econ-half", "Half price", "1.0.0", "Tristen", "new", "24687178", ["economy"]))
        self.assertEqual(mod["size_text"], f"{max(1, round(len(self.file.read_bytes()) / 1000))} KB")
        self.assertEqual(api.browse("nothing like it")["mods"], [])
        self.assertEqual(len(api.browse("economy")["mods"]), 1)  # tags count
        api.add_mod(str(self.file))
        self.assertEqual(api.browse()["mods"][0]["state"], "installed")
        self.write_index("1.1.0")
        self.assertEqual(api.browse()["mods"][0]["version"], "1.0.0")  # the list is fetched once per run…
        fresh = api.browse(fresh=True)["mods"][0]
        self.assertEqual((fresh["version"], fresh["state"], fresh["installed_version"]), ("1.1.0", "update", "1.0.0"))
        with self.assertRaisesRegex(LauncherError, "Only https"):
            api.open_link("http://example.com")
        api.open_link("https://example.com/half")
        self.assertEqual(self.urls, ["https://example.com/half"])

    def test_install_from_the_list_then_play(self):
        api = self.browser()
        j = wait_for(api, api.install_from_index("econ-half")["job"])
        self.assertEqual((j["state"], j["message"]), ("done", "Half price is in the library."), j)
        self.assertIn("The file matches the mod list (size and checksum).", j["lines"])
        mod = api.library()[0]
        self.assertEqual((mod["id"], mod["version"], mod["builds"], mod["fingerprint"]), ("econ-half", "1.0.0", ["24687178"], "K7Q2-M9XD"))
        self.assertEqual(api.browse()["mods"][0]["state"], "installed")
        self.assertEqual(list((self.home / "downloads").iterdir()), [])  # nothing kept
        api.new_set("Half", ["econ-half"])
        j = wait_for(api, api.play("half")["job"])
        self.assertEqual(j["state"], "done", j)
        self.assertEqual(price((self.instances / "half" / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
        with self.assertRaisesRegex(LauncherError, "no mod called"):
            api.install_from_index("nope")

    def test_a_wrong_or_missing_file_is_refused(self):
        wrong = ('\n[[mod]]\nid = "wrong"\nname = "Wrong"\nversion = "1.0.0"\ndownload = "%s/%s"\nsize = 5\nsha256 = "%s"\n'
                 '\n[[mod]]\nid = "gone"\nname = "Gone"\nversion = "1.0.0"\ndownload = "%s/missing.rusemod"\nsize = 5\nsha256 = "%s"\n'
                 % (self.base, self.file.name, "0" * 64, self.base, "1" * 64))
        self.write_index("1.0.0", extra=wrong)
        api = self.browser()
        j = wait_for(api, api.install_from_index("wrong")["job"])
        self.assertEqual(j["state"], "failed")
        self.assertIn("isn't the one the mod list promises", j["message"])
        j = wait_for(api, api.install_from_index("gone")["job"])
        self.assertIn("couldn't be downloaded", j["message"])
        self.assertEqual(api.library(), [])

    def test_offline_shows_the_copy_from_before(self):
        self.assertEqual(self.browser().browse()["source"], "online")
        self.server.shutdown()
        self.server.server_close()
        res = self.browser().browse()  # a new launcher run: no list in memory, no network
        self.assertEqual((res["source"], len(res["mods"])), ("cache", 1))
        self.assertIn("This is the copy from", res["message"])
        res = self.browser(home=Path(self.tmp.name, "other-home")).browse()
        self.assertEqual((res["source"], res["mods"]), ("none", []))
        self.assertIn("couldn't be loaded", res["message"])


class Words(unittest.TestCase):
    """The launcher's words in all ten languages, every one the screen uses, and the language it starts in."""

    def test_complete_and_used(self):
        for key, entry in _words().items():
            self.assertEqual([lang for lang in schema.LANGS if not entry.get(lang)], [], key)
        app_js = (Path(__file__).parents[1] / "src" / "ruse_launcher" / "ui" / "app.js").read_text(encoding="utf-8")
        used = set(re.findall(r"\b(?:w|state\.words)\.([a-z_]+)", app_js))
        self.assertGreater(len(used), 40)
        self.assertEqual(sorted(used - set(_words())), [])
        self.assertEqual((words("fr")["play"], words("xx")["play"]), ("Jouer", "Play"))

    def test_starts_in_the_pcs_language(self):
        for tag, code in [("fr-FR", "fr"), ("de_DE", "ger"), ("zh_CN", "sc"), ("en_US", "us"), ("cs_CZ.UTF-8", "cz"),
                          ("", "us"), ("xx", "us"), ("Japanese_Japan", "us")]:
            self.assertEqual(language_code(tag), code, tag)
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(LauncherApi(home=d, ui_language=lambda: "pl_PL").default_language(), "pol")
            self.assertEqual(LauncherApi(home=d, ui_language=mock.Mock(side_effect=OSError)).default_language(), "us")
            self.assertEqual([lang["code"] for lang in LauncherApi(home=d).languages()], list(schema.LANGS))


class Window(unittest.TestCase):
    def test_the_screens_are_served_on_this_pc_only(self):
        server, base = serve(app.UI)
        try:
            self.assertTrue(base.startswith("http://127.0.0.1:"))
            with urllib.request.urlopen(f"{base}/index.html") as r:
                self.assertIn(b"RUSE", r.read())
        finally:
            server.shutdown()
            server.server_close()

    def test_without_pywebview_it_says_how_to_install_it(self):
        with mock.patch.dict(sys.modules, {"webview": None}):
            with mock.patch("builtins.print") as out:
                self.assertEqual(app.main([]), 2)
        self.assertIn("pip install pywebview", out.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
