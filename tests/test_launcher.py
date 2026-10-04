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
from ruse_launcher import __version__, app
from rusemod.play import SHARED
from ruse_launcher.api import MOD_FILES, LauncherApi, LauncherError, _words, language_code, words
from rusemod import doctor, package, schema
from rusemod.backup import BackupError
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
        copy = self.instances / SHARED
        self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
        self.assertEqual(self.started, [copy / "RUSE.exe"])
        self.assertTrue(any("modded copy ready" in line for line in j["lines"]))
        later = api.job(j["id"], since=j["count"])
        self.assertEqual(later["lines"], [])  # `since` skips the lines already shown
        from rusemod.webui import Job
        busy = Job()  # a start still going: another waits for it (two raced for the same copy)
        api._jobs[busy.id] = busy
        api._play_job = busy.id
        self.assertIn("already being started", api.job(api.play("half")["job"])["message"])
        busy.state = "done"
        self.assertEqual(wait_for(api, api.play("half")["job"])["state"], "done")

    def test_a_second_play_with_nothing_changed_builds_nothing(self):
        # a player, 2026-10-04: "Waiting 30 minutes every time just to add or remove a unit"
        mod = write_mod(self.tmp.name, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})
        self.mod_set("half", [mod])
        api = self.api()
        api.set_pref("lang", "fr")
        self.assertEqual(wait_for(api, api.play("half")["job"])["state"], "done")
        j = wait_for(api, api.play("half")["job"])
        self.assertEqual(j["state"], "done", j)
        self.assertEqual(j["lines"][0], words("fr")["play_unchanged"])  # said in the player's language
        self.assertFalse(any("modded copy ready" in line for line in j["lines"]))
        self.assertEqual(self.started, [self.instances / SHARED / "RUSE.exe"] * 2)

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

    def test_a_mod_with_a_misnamed_map_folder_is_added_and_the_problem_said(self):
        api = self.api()
        files = {"mod.toml": '[mod]\nid = "blitz-hill"\nversion = "1.0.0"\nname = "Blitz hill"\n',
                 "maps/Blitz/terrain.toml": '[[stroke]]\nbrush = "hill"\nx = 1.0\ny = 2.0\nradius = 3.0\nheight = 4.0\n'}
        maps = [{"pack": "SuperCrossRoads4", "titles": {"us": ["Blitz"]}}]
        with mock.patch("rusemod.modcheck.map_list", return_value=maps):
            res = api.add_mod(str(make_zip(Path(self.tmp.name, "c.zip"), files)))
        self.assertEqual(res["mod"]["id"], "blitz-hill")  # it goes in: the author has the fix
        self.assertEqual([(p["file"], p["rename_to"]) for p in res["problems"]], [("maps/Blitz", "SuperCrossRoads4")])
        good = api.add_mod(str(make_zip(Path(self.tmp.name, "d.zip"), {"mod.toml": files["mod.toml"]})))
        self.assertEqual(good["problems"], [])

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
        copy = self.instances / SHARED
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

    def test_share_and_import_a_load_order(self):
        api = self.api()
        api.new_set("Mine", ["bbb-ten", "aaa-half"])
        text = api.share_set("mine")["text"]
        self.assertIn("Set: Mine\n", text)
        self.assertIn("1. Bbb-Ten | v1.0.0\n2. Aaa-Half | v1.0.0\n=== End Load Order ===", text)
        check = api.import_check("from a friend:\n" + text.replace("Aaa-Half", "Missing Mod"))
        self.assertEqual(([f["id"] for f in check["found"]], check["missing"], check["set_name"]),
                         (["bbb-ten"], [{"name": "Missing Mod", "version": "1.0.0"}], "Mine"))
        res = api.import_set(text, "From Bob")
        self.assertEqual((res["set"], res["sets"][-1]["mods"]), ("from-bob", ["bbb-ten", "aaa-half"]))
        with self.assertRaisesRegex(LauncherError, "no load order"):
            api.import_check("hello")
        with self.assertRaisesRegex(LauncherError, "None of these mods"):
            api.import_set("=== R.U.S.E. Load Order ===\n1. Nope\n=== End Load Order ===")
        with self.assertRaisesRegex(LauncherError, "Vanilla has no mods"):
            api.share_set("vanilla")

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
        copy = self.instances / SHARED
        self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [5] * 5)
        self.assertIn("load order: bbb-ten -> aaa-half", j["lines"])  # the set's order, not the ids' order
        api.new_set("Half then ten", ["aaa-half", "bbb-ten"])
        j = wait_for(api, api.play("half-then-ten")["job"])
        self.assertEqual(j["state"], "done", j)
        copy = self.instances / SHARED
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


class Clashing(Base):
    """.rmod mods that don't go together (rusemod.rmod.clashes): the set screen asks set_check / check_mods and
    shows them before Play; Play refuses the set with the reason."""

    def test_set_check_and_play_refuse_clashing_mods(self):
        from test_rmod import rmod_json, set_values
        dl = Path(self.tmp.name, "dl")
        dl.mkdir()
        api = self.api()
        for name, files, patches in (
                ("Alpha", {"genpython/map/effetmap.xyz": b"XYZ0 A"}, [set_values("Unit_Battleship", VitesseLineaire=9.5)]),
                ("Beta", {"genpython/map/effetmap.xyz": b"XYZ0 B"}, []),
                ("Gamma", {}, [set_values("Unit_Battleship", VitesseLineaire=0)])):
            path = dl / f"{name}.rmod"
            path.write_text(rmod_json(files, mod_id=name.lower(), name=name, patches=patches), encoding="utf-8")
            api.add_mod(str(path))
        api.new_set("Clashing", ["alpha", "gamma", "beta"])
        check = api.set_check("clashing")
        self.assertEqual([(c["kind"], c["hard"], c["a"], c["b"], c["mods"]) for c in check["hard"]],
                         [("file", True, "Alpha", "Beta", ["Alpha", "Beta"])])
        self.assertEqual([(c["kind"], c["a"], c["b"], c["count"], c["what"]) for c in check["soft"]],
                         [("value", "Gamma", "Alpha", 1, "Unit_Battleship.VitesseLineaire")])
        self.assertEqual(api.check_mods(["alpha", "gamma"])["hard"], [])   # while a set is edited: ids, no set yet
        self.assertEqual(api.check_mods(["alpha", "nope"]), {"hard": [], "soft": [], "best": None})
        self.assertEqual(api.set_check("vanilla"), {"hard": [], "soft": [], "best": None})
        j = wait_for(api, api.play("clashing")["job"])
        self.assertEqual(j["state"], "failed")
        self.assertIn("These mods can't be played together (1 clash):", j["message"])
        self.assertIn("Alpha and Beta each replace the same script, effetmap.xyz", j["message"])
        self.assertEqual(self.started, [])
        self.assertFalse((self.instances / SHARED).exists())


    def test_best_order_puts_the_smaller_mod_after_the_bigger_one(self):
        from test_rmod import rmod_json, set_values
        dl = Path(self.tmp.name, "dl")
        dl.mkdir()
        api = self.api()
        for name, patches in (("Static", [set_values("Unit_Battleship", VitesseLineaire=0)]),
                              ("Navy", [set_values("Unit_Battleship", VitesseLineaire=9.5, Blindage=3),
                                        set_values("Unit_Destroyer", VitesseLineaire=12)])):
            path = dl / f"{name}.rmod"
            path.write_text(rmod_json({}, mod_id=name.lower(), name=name, patches=patches), encoding="utf-8")
            api.add_mod(str(path))
        api.new_set("Ships", ["static", "navy"])
        check = api.set_check("ships")
        self.assertEqual((check["best"], check["helped"]), (["navy", "static"], ["Static"]))
        lists = api.best_order("ships")
        chosen = next(s for s in lists["sets"] if s["id"] == "ships")
        self.assertEqual(chosen["mods"], ["navy", "static"])
        self.assertIsNone(api.set_check("ships")["best"])  # already the best order: no button

class ListServer(Base):
    """The mod index on a local web server, listing one mod (econ-half)."""

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


class Browse(ListServer):
    """Supported mods: the mod index on a local web server, installs checked against it, the copy kept for offline."""

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
        self.assertEqual(price((self.instances / SHARED / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
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


class SupportedMods(ListServer):
    """The Supported mods tab and the first run's "Choose your mods": several mods ticked and installed in one go,
    the cheats and test tools (tag "cheat") in their own group and downloaded only when ticked."""

    def setUp(self):
        super().setUp()
        self.files = {"econ-half": self.file}
        for mod_id, name in (("cheap-units", "Cheap units"), ("big-airfields", "Big airfields")):
            folder = write_mod(Path(self.tmp.name, "src"), mod_id, HALF, extra=f'name = "{name}"\n')
            self.files[mod_id] = package.pack(folder, self.www)
        self.write_list()

    def entry(self, mod_id, name, tags, sha=None):
        data = self.files[mod_id].read_bytes()
        return ('\n[[mod]]\nid = "%s"\nname = "%s"\nversion = "1.0.0"\ndownload = "%s/%s"\nsize = %d\nsha256 = "%s"\n'
                'tags = %s\n' % (mod_id, name, self.base, self.files[mod_id].name, len(data),
                                 sha or hashlib.sha256(data).hexdigest(), json.dumps(tags)))

    def write_list(self, broken=""):
        """econ-half (from Browse), then a cheat listed before an ordinary mod: the list puts the cheat last."""
        self.write_index("1.0.0", extra=self.entry("cheap-units", "Cheap units", ["Cheat", "testing"], sha=broken or None)
                         + self.entry("big-airfields", "Big airfields", ["air"]))

    def downloaded(self):
        """The packages the launcher fetched from the server so far."""
        return [line for line in self.server.log if line.endswith(".rusemod")]

    def serve_logged(self):
        log = []
        handler = self.server.RequestHandlerClass.func  # this server's own handler class (webui.serve)
        handler.log_request = lambda this, code="-", size="-": log.append(this.path)  # every file asked for
        self.server.log = log

    def test_the_list_says_which_are_cheats_and_where_it_lives(self):
        res = self.browser().browse()
        self.assertEqual([(m["id"], m["cheat"]) for m in res["mods"]],
                         [("econ-half", False), ("big-airfields", False), ("cheap-units", True)])
        self.assertEqual(res["page"], "https://github.com/sneadtristen6/Ruse-Mods")

    def test_several_ticked_mods_install_in_one_go_and_a_cheat_only_when_ticked(self):
        self.serve_logged()
        api = self.browser()
        j = wait_for(api, api.install_mods(["econ-half", "big-airfields"])["job"])
        self.assertEqual((j["state"], j["message"]), ("done", "The 2 mods are in the library."), j)
        self.assertIn("(2/2) Big airfields", j["lines"])
        self.assertEqual(sorted(m["id"] for m in api.library()), ["big-airfields", "econ-half"])
        self.assertEqual(self.downloaded(), ["/" + self.files["econ-half"].name, "/" + self.files["big-airfields"].name])
        states = {m["id"]: m["state"] for m in api.browse()["mods"]}
        self.assertEqual(states, {"econ-half": "installed", "big-airfields": "installed", "cheap-units": "new"})
        j = wait_for(api, api.install_mods(["cheap-units"])["job"])  # ticked: now it comes
        self.assertEqual((j["state"], j["message"]), ("done", "Cheap units is in the library."), j)
        self.assertIn("/" + self.files["cheap-units"].name, self.downloaded())
        with self.assertRaisesRegex(LauncherError, "no mod called 'nope'"):
            api.install_mods(["econ-half", "nope"])
        for nothing in ([], "econ-half", [3]):
            with self.assertRaisesRegex(LauncherError, "Tick the mods to install"):
                api.install_mods(nothing)

    def test_one_that_fails_doesnt_stop_the_others(self):
        self.write_list(broken="0" * 64)  # the cheat's file no longer matches the list
        api = self.browser()
        j = wait_for(api, api.install_mods(["cheap-units", "big-airfields"])["job"])
        self.assertEqual(j["state"], "failed", j)
        self.assertTrue(j["message"].startswith("1 of 2 mods were installed. Not installed: Cheap units (The file for "
                                                "Cheap units isn't the one the mod list promises"), j["message"])
        self.assertEqual([m["id"] for m in api.library()], ["big-airfields"])

    def test_one_install_at_a_time(self):
        api = self.browser()
        api.browse()
        with mock.patch.object(api, "_install_one", side_effect=lambda entry, say: time.sleep(0.5)):
            first = api.install_mods(["econ-half"])["job"]
            with self.assertRaisesRegex(LauncherError, "Mods are being installed"):
                api.install_from_index("big-airfields")
            self.assertEqual(wait_for(api, first)["state"], "done")
        self.assertEqual(wait_for(api, api.install_from_index("big-airfields")["job"])["state"], "done")

    def test_the_first_run_until_the_player_chooses_or_skips(self):
        api = self.browser()
        self.assertEqual(api.first_run(), {"show": True})  # no library yet
        self.assertEqual(api.first_run_done(), {"show": False})
        self.assertEqual(api.first_run(), {"show": False})
        self.assertEqual(self.browser().first_run(), {"show": False})  # kept in settings.json for the next start
        again = self.browser(home=Path(self.tmp.name, "home-2"))
        wait_for(again, again.install_mods(["econ-half"])["job"])
        self.assertEqual(again.first_run(), {"show": False})  # a library already: nothing to choose at the start

    def test_the_first_run_offline_shows_the_saved_copy_or_nothing(self):
        self.assertEqual(len(self.browser().browse()["mods"]), 3)  # a copy kept from an earlier start
        self.server.shutdown()
        self.server.server_close()
        res = self.browser().browse()
        self.assertEqual((res["source"], [m["cheat"] for m in res["mods"]]), ("cache", [False, False, True]))
        none = self.browser(home=Path(self.tmp.name, "fresh")).browse()  # no copy at all: only Skip
        self.assertEqual((none["source"], none["mods"]), ("none", []))


class Troubleshooter(Base):
    """The troubleshooter (rusemod.doctor) as the window asks for it: the launcher's own game, folder for modded
    copies and Steam check, and the two fixes it can run."""

    def test_findings_and_the_report(self):
        with mock.patch("rusemod.winfiles.processes", return_value=[]):
            res = self.api().troubleshoot()
            got = {f["key"]: f for f in res["findings"]}
            self.assertEqual((got["game"]["level"], got["game"]["data"]), ("ok", {"path": str(self.game)}))
            self.assertEqual((got["steam"]["level"], got["running"]["level"], got["leftovers"]["level"]), ("ok", "ok", "ok"))
            self.assertEqual(got["write"]["data"], {"path": str(self.instances)})  # where this launcher puts its copies
            self.assertTrue(res["report"].startswith(f"RUSE Launcher {__version__}, Windows "), res["report"])
            self.assertIn("[ok] game: doc_game_ok (path=", res["report"])
            steam_off = self.api(steam_running=lambda: False).troubleshoot()["findings"]
            self.assertEqual([f["level"] for f in steam_off if f["key"] == "steam"], ["info"])
            none = self.api(game_dir=None, find=lambda: None).troubleshoot()["findings"]
        self.assertEqual([(f["key"], f["fix"]) for f in none], [("game", "choose_game"), ("steam", None), ("running", None)])

    def test_its_fixes(self):
        api = self.api()
        for action in ("format the drive", "choose_game"):  # Choose folder… is the window's own
            with self.subTest(action=action), self.assertRaisesRegex(LauncherError, "no fix called"):
                api.troubleshoot_fix(action)
        (self.instances / "half.old" / "Data").mkdir(parents=True)
        (self.instances / "half.old" / "Data" / "A.dat").write_bytes(b"pack")
        game_in_copy = str(self.instances / SHARED / "RUSE.exe")
        with mock.patch("rusemod.winfiles.processes", return_value=[(7, game_in_copy)]):
            got = {f["key"]: f for f in api.troubleshoot()["findings"]}
            self.assertEqual((got["running"]["fix"], got["leftovers"]["fix"]), ("close_game", "clear_leftovers"))
            with mock.patch("rusemod.winfiles.close", return_value=True) as close:
                self.assertEqual(api.troubleshoot_fix("close_game"), {"done": 1, "left": []})
            close.assert_called_once_with(7)
        self.assertEqual(api.troubleshoot_fix("clear_leftovers"), {"done": 1, "left": []})
        self.assertFalse((self.instances / "half.old").exists())
        # a copy per mod set, as the apps made them before: a leftover; the one both apps use now isn't
        for name in ("old-set", SHARED):
            (self.instances / name).mkdir(parents=True, exist_ok=True)
            (self.instances / name / "RUSE.exe").write_bytes(b"MZ")
            (self.instances / name / "steam_appid.txt").write_text("21970")
        got = {f["key"]: f for f in api.troubleshoot()["findings"]}
        self.assertEqual(got["leftovers"]["data"]["names"], "old-set")
        self.assertEqual(api.troubleshoot_fix("clear_leftovers"), {"done": 1, "left": []})
        self.assertEqual(sorted(p.name for p in self.instances.iterdir() if not p.name.startswith(".")), [SHARED])
        from rusemod.webui import Job
        busy = Job()  # a Play still building its copy: the copy would look like a leftover
        api._jobs[busy.id] = busy
        api._play_job = busy.id
        with self.assertRaisesRegex(LauncherError, "being started"):
            api.troubleshoot_fix("clear_leftovers")
        with self.assertRaisesRegex(LauncherError, "Choose its folder"):
            self.api(game_dir=None, find=lambda: None).troubleshoot_fix("clear_leftovers")


class CleanBackup(Base):
    """The clean game backup in Settings, as the window asks for it (what it does is rusemod.backup's:
    tests/test_backup.py)."""

    def api(self, **kw):
        return super().api(**({"backups": Path(self.tmp.name) / "backups"} | kw))

    def test_make_check_and_restore(self):
        api = self.api()
        s = api.backup_status()
        self.assertEqual((s["found"], s["build"], s["backups"], s["current"], s["busy"], s["enough"]),
                         (True, "24687178", [], None, "", True))
        self.assertEqual((s["folder"], s["drive"]), (str(Path(self.tmp.name) / "backups"), self.game.drive or "/"))
        self.assertGreater(s["free_gb"], 0)
        j = wait_for(api, api.backup_make()["job"])
        self.assertEqual((j["state"], j["result"]["build"], j["result"]["files"], j["lines"][-1]),
                         ("done", "24687178", 2, "100%"), j)
        current = api.backup_status()["current"]
        self.assertEqual((current["build"], current["files"], current["matches"], len(current["date"])),
                         ("24687178", 2, True, 16))
        j = wait_for(api, api.backup_make()["job"])  # one there already: made again only when asked
        self.assertEqual(j["state"], "failed")
        self.assertIn("already a backup of this build", j["message"])
        self.assertNotIn("result", j)
        self.assertEqual(wait_for(api, api.backup_make(True)["job"])["state"], "done")
        pack = self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat"
        pack.write_bytes(b"changed by another mod manager")
        (self.game / "extra.txt").write_text("not the game's", encoding="utf-8")
        found = wait_for(api, api.backup_check()["job"])["result"]
        self.assertEqual((found["changed"], found["missing"], found["added"]),
                         (["Data/PC/190852/ZZ_GladPatchableWin.dat"], [], ["extra.txt"]))
        with mock.patch("rusemod.winfiles.processes", return_value=[(4312, str(self.game / "RUSE.exe"))]):
            j = wait_for(api, api.backup_restore()["job"])
        self.assertEqual(j["state"], "failed")
        self.assertIn("RUSE.exe (process 4312). Close the game", j["message"])
        with mock.patch("rusemod.winfiles.processes", return_value=[]):
            j = wait_for(api, api.backup_restore()["job"])
        self.assertEqual((j["state"], j["result"]["restored"], j["result"]["set_aside"], j["result"]["left"]),
                         ("done", 1, 1, []), j)
        self.assertEqual(pack.read_bytes(), PACK)
        self.assertTrue(Path(j["result"]["set_aside_to"], "extra.txt").is_file())
        clean = wait_for(api, api.backup_check(True)["job"])["result"]
        self.assertEqual((clean["changed"], clean["missing"], clean["added"], clean["hashed"]), ([], [], [], 2))
        self.assertEqual(api.steam_verify(), {"opened": "steam://validate/21970"})
        self.assertEqual(self.urls, ["steam://validate/21970"])

    def test_what_is_refused(self):
        from rusemod.webui import Job
        api = self.api()
        for call in (api.backup_check, api.backup_restore):
            with self.subTest(call=call.__name__), self.assertRaisesRegex(BackupError, "no backup of the game yet"):
                call()
        playing = Job()  # a Play building its copy from the game's files: a restore waits for it
        api._jobs[playing.id] = playing
        api._play_job = playing.id
        with self.assertRaisesRegex(BackupError, "being started"):
            api.backup_restore()
        playing.state = "done"
        restoring = Job()  # and a Play waits for a restore
        restoring.kind = "restore"
        api._jobs[restoring.id] = restoring
        api._backup_job = restoring.id
        self.assertEqual(api.job(api.play("vanilla")["job"])["message"],
                         "The game's files are being restored: wait for it to finish.")
        self.assertEqual(self.urls, [])
        self.assertEqual(api.backup_status()["busy"], "restore")
        with self.assertRaisesRegex(BackupError, "busy"):  # one backup job at a time
            api.backup_make()
        restoring.state = "done"
        none = self.api(game_dir=None, find=lambda: None)
        self.assertEqual(none.backup_status(), {"found": False, "backups": [], "current": None, "busy": ""})
        with self.assertRaisesRegex(BackupError, "couldn't find R.U.S.E."):
            none.backup_make()

    def test_the_studio_at_work_on_the_game_is_waited_for(self):
        from rusemod import backup
        api, folder = self.api(), Path(self.tmp.name) / "backups"
        self.assertEqual(wait_for(api, api.backup_make()["job"])["state"], "done")
        with backup._busy(folder, "restore"):  # the Studio restoring the game's files: a Play waits
            j = wait_for(api, api.play("vanilla")["job"])
        self.assertEqual((j["state"], j["message"]), ("failed", "The game's files are being restored: wait for it to "
                                                                "finish."))
        self.assertEqual(self.urls, [])
        with backup.reading(folder):  # the Studio building a Test in game: a restore waits
            with mock.patch("rusemod.winfiles.processes", return_value=[]):
                j = wait_for(api, api.backup_restore()["job"])
        self.assertEqual(j["state"], "failed")
        self.assertIn("A modded copy of the game is being built", j["message"])
        with backup._busy(folder, "make"):  # the Studio making a backup: one at a time
            j = wait_for(api, api.backup_make(True)["job"])
        self.assertIn("the other app (the Launcher or the Studio) is making a backup", j["message"])
        self.assertEqual(wait_for(api, api.play("vanilla")["job"])["state"], "done")  # nothing held any more
        self.assertEqual([p.name for p in folder.iterdir()], ["24687178"])  # and nothing left behind


class Words(unittest.TestCase):
    """The launcher's words in all ten languages, every one the screen uses, and the language it starts in."""

    def test_every_word_of_the_troubleshooter(self):
        """rusemod.doctor names each finding's sentence and fix; the window shows them with these words."""
        source = Path(doctor.__file__).read_text(encoding="utf-8")
        said = set(re.findall(r'"(doc_[a-z_]+)"', source))
        fixes = set(re.findall(r'_finding\("\w+", "\w+", "doc_\w+", "(\w+)"', source))
        self.assertGreater(len(said), 15)
        self.assertEqual(fixes, {"choose_game", "close_game", "clear_leftovers"})
        self.assertEqual(sorted((said | {f"doc_fix_{fix}" for fix in fixes}) - set(_words())), [])

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
        no_steam = lambda: None  # noqa: E731
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(LauncherApi(home=d, ui_language=lambda: "pl_PL", find=no_steam).default_language(), "pol")
            self.assertEqual(LauncherApi(home=d, ui_language=mock.Mock(side_effect=OSError),
                                         find=no_steam).default_language(), "us")
            self.assertEqual([lang["code"] for lang in LauncherApi(home=d).languages()], list(schema.LANGS))

    def test_starts_in_the_games_language_in_steam(self):
        # the game set to French in Steam beats an English PC; a language the game doesn't have falls to the PC's
        with tempfile.TemporaryDirectory() as d:
            french = LauncherApi(home=d, ui_language=lambda: "en_US", find=lambda: {"language": "french"})
            self.assertEqual(french.default_language(), "fr")
            self.assertEqual(french.language_choice(), {"suggested": "fr", "from": "steam", "chosen": False})
            odd = LauncherApi(home=d, ui_language=lambda: "de_DE", find=lambda: {"language": "koreana"})
            self.assertEqual(odd.language_choice(), {"suggested": "ger", "from": "pc", "chosen": False})
            broken = LauncherApi(home=d, ui_language=lambda: "xx", find=mock.Mock(side_effect=OSError))
            self.assertEqual(broken.language_choice(), {"suggested": "us", "from": "default", "chosen": False})
            french.set_pref("lang_chosen", True)
            self.assertTrue(french.language_choice()["chosen"])


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
        from rusemod import startlog
        startlog.stop()
        self.addCleanup(startlog.stop)
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": d}):
            with mock.patch.dict(sys.modules, {"webview": None}):
                with mock.patch("builtins.print") as out:
                    self.assertEqual(app.main([]), 2)
            # the start-up log (rusemod.startlog) shows how far it got: the window library was the next step
            line = startlog.recent("launcher", Path(d))[-1]
        self.assertIn("pip install pywebview", out.call_args[0][0])
        self.assertIn(f" launcher {__version__}: python ", line)
        self.assertEqual([p.rpartition(" ")[0] for p in line.split(": ", 1)[1].split(", ")], ["python", "imports", "api"])


if __name__ == "__main__":
    unittest.main()
