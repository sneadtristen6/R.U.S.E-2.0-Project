"""Era units in the Units tab (ruse_studio.era_units) on the Studio tests' made-up game: the library read from
RUSE_ERA_UNITS, an era's units listed and filtered like the Units list, every one out of the mod until added, an era
unit's page with the game units it can start from (the suggestion first), adding one from the suggestion or from
another unit with its own name and price, its credit in the mod's CREDITS-era-units.md, the same name in two eras,
taking it out again. And the download: an era from the release's list, each file checked, updated when a newer one is
out, refused when a file isn't right."""
import hashlib
import json
import os
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_studio import M4, WithMod
from ruse_studio import era_units
from ruse_studio.api import StudioError

PANZER = "$/GFX/Everything/Descriptor_Unit_Panzer_IV_G"


def entry(era, nation, name, card, copies, extra="", air=False):
    return {"key": f"{era}|{nation}|{name}", "era": era, "nation": nation, "name": name, "in_place_of": "",
            "card": card, "building": "Armor base", "copies": copies, "copies_name": "", "game_nation": 0,
            "factory": 10, "aircraft": air, "model": None, "fits": True, "picture": None,
            "credit": {"title": f"{name} model", "author": "maker", "licence": "CC-BY 4.0",
                       "url": f"https://example.org/{name.replace(' ', '_')}", "extra": extra}}


UNITS = [entry("WWI", "USA", "Mark VIII Liberty", "Heavy Tank", M4),
         entry("Cold War", "USA", "Patton", "Medium Tank", M4, extra="Scan of Jo's 1:35 model"),
         entry("Modern", "USA", "Patton", "Medium Tank", M4),
         entry("Modern", "China", "Type 99", "Main Battle Tank", PANZER),
         entry("Modern", "USA", "F-35", "Advanced Fighter", M4, air=True)]


class EraUnits(WithMod):
    def setUp(self):
        super().setUp()
        self.lib = Path(tempfile.mkdtemp(dir=self.tmp.name))
        (self.lib / "era_units.json").write_text(json.dumps({"version": 1, "note": "", "units": UNITS}),
                                                 encoding="utf-8")
        patcher = mock.patch.dict(os.environ, {era_units.LIBRARY_ENV: str(self.lib)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_listed_by_era_and_filtered_like_the_units_list(self):
        self.assertEqual(era_units.library_dir(), self.lib)
        modern = self.api.era_units_list("Modern")
        self.assertTrue(modern["library"])
        self.assertEqual([u["name"] for u in modern["units"]], ["Patton", "Type 99", "F-35"])
        self.assertEqual([u["added"] for u in modern["units"]], [None, None, None])     # nothing added by itself
        self.assertEqual(modern["types"], ["Advanced Fighter", "Main Battle Tank", "Medium Tank"])
        self.assertEqual([u["name"] for u in self.api.era_units_list("Modern", kind="air")["units"]], ["F-35"])
        self.assertEqual([u["name"] for u in self.api.era_units_list("Modern", nation=7)["units"]], ["Type 99"])
        self.assertEqual([u["code"] for u in modern["units"]], [0, 7, 0])                  # China: chip 7
        self.assertEqual([u["name"] for u in self.api.era_units_list("Modern", search="pat")["units"]], ["Patton"])
        self.assertEqual([u["name"] for u in self.api.era_units_list("Modern", group="type:Main Battle Tank")["units"]],
                         ["Type 99"])

    def test_page_offers_any_unit_of_its_kind_to_start_from(self):
        page = self.api.era_unit_page("WWI|USA|Mark VIII Liberty")
        self.assertEqual((page["name"], page["added"], page["has_model"], page["picture"]),
                         ("Mark VIII Liberty", None, False, None))
        self.assertEqual(page["start"][0]["address"], M4)                                  # the suggestion first
        self.assertTrue(page["start"][0]["suggested"])
        self.assertIn(PANZER, [s["address"] for s in page["start"]])                       # any ground unit
        self.assertEqual(self.api.era_start_price(PANZER)["price"], 45.0)
        with self.assertRaises(StudioError):
            self.api.era_unit_page("Nope|USA|Nothing")

    def test_added_from_the_suggestion_and_taken_out(self):
        with self.assertRaises(StudioError):
            self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)                       # no mod yet
        folder = Path(self.api.new_mod("Eras")["current"])
        made = self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)
        self.assertEqual((made["name"], made["model"], made["model_note"]), ("Mark VIII Liberty", None, "no_model"))
        listed = {u["address"]: u for u in self.api.units()["units"]}
        self.assertEqual((listed[made["address"]]["new"], listed[made["address"]]["source"]), (True, M4))
        self.assertEqual(json.loads((folder / "era_units.json").read_text(encoding="utf-8")),
                         {"WWI|USA|Mark VIII Liberty": made["address"]})
        credits = (folder / "CREDITS-era-units.md").read_text(encoding="utf-8")
        self.assertIn('- Mark VIII Liberty (WWI, USA): "Mark VIII Liberty model" by maker, CC-BY 4.0, '
                      'https://example.org/Mark_VIII_Liberty.', credits)
        self.assertEqual(self.api.era_units_list("WWI")["units"][0]["added"], made["address"])
        self.assertEqual(self.api.era_unit_page("WWI|USA|Mark VIII Liberty")["added"], made["address"])
        with self.assertRaises(StudioError):
            self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 0, 10)                       # already in
        self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")
        self.assertNotIn(made["address"], {u["address"] for u in self.api.units()["units"]})
        self.assertFalse((folder / "CREDITS-era-units.md").exists())
        with self.assertRaises(StudioError):
            self.api.era_unit_remove("WWI|USA|Mark VIII Liberty")                           # not in any more

    def test_started_from_another_unit_with_its_own_name_and_price(self):
        folder = Path(self.api.new_mod("Own values")["current"])
        made = self.api.era_unit_add("WWI|USA|Mark VIII Liberty", 1, 10, source=PANZER, name="Liberty", price=99)
        self.assertEqual(made["name"], "Liberty")
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"is clone {PANZER}", rndf)                                           # the Panzer's values
        self.assertIn("ProductionPrice = [99, 99]", rndf)

    def test_same_name_in_two_eras_and_the_extra_credit(self):
        folder = Path(self.api.new_mod("Two Pattons")["current"])
        first = self.api.era_unit_add("Cold War|USA|Patton", 0, 10)
        second = self.api.era_unit_add("Modern|USA|Patton", 0, 10)
        self.assertEqual((first["name"], second["name"]), ("Patton", "Patton (Modern)"))
        credits = (folder / "CREDITS-era-units.md").read_text(encoding="utf-8")
        self.assertIn('"Patton model" by maker, CC-BY 4.0, https://example.org/Patton. Scan of Jo\'s 1:35 model.',
                      credits)

    def test_no_library(self):
        with mock.patch.object(era_units, "library_dir", return_value=None):
            self.assertEqual(self.api.era_units_list("WWI"),
                             {"library": False, "installed": False, "types": [], "units": []})


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class EraDownload(WithMod):
    """An era downloaded from the release's list (a folder standing in for GitHub): every file checked, unpacked into
    the platform folder's era_units, listed; a newer version updates it; a file that isn't right installs nothing."""

    def setUp(self):
        super().setUp()
        self.release = Path(tempfile.mkdtemp(dir=self.tmp.name))
        patcher = mock.patch.dict(os.environ, {era_units.URL_ENV: self.release.as_posix() + "/"})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(era_units.LIBRARY_ENV, None)
        self.root = self.home / era_units.DOWNLOADED

    def publish(self, files: dict, units: list, era="WWI", name="era-units-WWI-1.zip", size=None, digest=None):
        """The release: one .zip of `files` (path -> bytes) and the list naming it with `units`."""
        with zipfile.ZipFile(self.release / name, "w") as z:
            for path, data in files.items():
                z.writestr(path, data)
        data = (self.release / name).read_bytes()
        version = sha(json.dumps([sorted(files), units]).encode())
        part = {"file": name, "size": size or len(data), "sha256": digest or sha(data)}
        (self.release / era_units.LIST).write_text(json.dumps(
            {"format": 1, "sections": [{"era": era, "version": version, "parts": [part], "units": units}]}),
            encoding="utf-8")
        self.api._era_kept = None   # the list asked for again

    def run_job(self, era="WWI"):
        job = self.api.era_download(era)["job"]
        end = time.time() + 20
        while (got := self.api.job(job))["state"] == "running" and time.time() < end:
            time.sleep(0.05)
        return got

    def unit(self, name, picture):
        u = entry("WWI", "USA", name, "Heavy Tank", M4)
        return dict(u, model=f"WWI/USA/{name}.glb", picture=picture)

    def test_downloaded_listed_and_updated(self):
        self.publish({"WWI/USA/Liberty.glb": b"glb one", "pictures/a.jpg": b"jpg a"}, [self.unit("Liberty", "pictures/a.jpg")])
        self.assertEqual(self.api.era_units_list("WWI")["installed"], False)
        self.assertEqual(self.api.era_sections()["sections"][0] | {"size": 0},
                         {"era": "WWI", "units": 1, "size": 0, "state": "new"})
        self.assertEqual(self.api.era_sections(downloaded_only=True), {"sections": [], "message": ""})
        got = self.run_job()
        self.assertEqual((got["state"], got["lines"][-1]), ("done", "unpack"), got)
        self.assertEqual(era_units.library_dir(self.home), self.root)
        listed = self.api.era_units_list("WWI")
        self.assertEqual((listed["installed"], [u["name"] for u in listed["units"]]), (True, ["Liberty"]))
        page = self.api.era_unit_page("WWI|USA|Liberty")
        self.assertTrue(page["has_model"])
        self.assertEqual((self.root / "WWI/USA/Liberty.glb").read_bytes(), b"glb one")
        self.assertFalse((self.root / ".download").exists() and any((self.root / ".download").iterdir()))
        self.assertEqual(self.api.era_sections()["sections"][0]["state"], "current")
        # a newer version: another unit, the old picture gone
        self.publish({"WWI/USA/Whippet.glb": b"glb two", "pictures/b.jpg": b"jpg b"}, [self.unit("Whippet", "pictures/b.jpg")])
        self.assertEqual(self.api.era_sections(downloaded_only=True)["sections"][0]["state"], "update")
        self.assertEqual(self.run_job()["state"], "done")
        self.assertEqual([u["name"] for u in self.api.era_units_list("WWI")["units"]], ["Whippet"])
        self.assertFalse((self.root / "pictures/a.jpg").exists())
        self.assertFalse((self.root / "WWI/USA/Liberty.glb").exists())

    def test_an_era_in_the_librarys_folder_name(self):
        u = dict(entry("Cold War", "USA", "Patton", "Medium Tank", M4), model="Cold_War/USA/Patton.glb")
        self.publish({"Cold_War/USA/Patton.glb": b"glb"}, [u], era="Cold War", name="era-units-Cold_War-1.zip")
        self.assertEqual(self.run_job("Cold War")["state"], "done")
        self.assertEqual([x["name"] for x in self.api.era_units_list("Cold War")["units"]], ["Patton"])
        self.assertTrue(self.api.era_unit_page("Cold War|USA|Patton")["has_model"])

    def test_a_file_outside_the_era_installs_nothing(self):
        for bad in ("../evil.glb", "WWII/USA/x.glb", "WWI/USA/run.exe", "WWI/a/b/c.glb"):
            self.publish({"WWI/USA/Liberty.glb": b"glb", bad: b"x"}, [self.unit("Liberty", None)])
            got = self.run_job()
            self.assertEqual(got["state"], "failed", bad)
            self.assertIn("nothing was installed", got["message"])
            self.assertFalse((self.root / era_units.INDEX).exists())
            self.assertFalse(Path(self.root, "WWI").exists())

    def test_a_file_not_as_the_list_promises_is_refused(self):
        self.publish({"WWI/USA/Liberty.glb": b"glb"}, [self.unit("Liberty", None)], digest="0" * 64)
        got = self.run_job()
        self.assertEqual(got["state"], "failed")
        self.assertIn("isn't the file the era units list promises", got["message"])
        self.assertFalse((self.root / era_units.INDEX).exists())
        self.publish({"WWI/USA/Other.glb": b"glb"}, [self.unit("Liberty", None)])   # the list names what isn't there
        self.assertIn("don't hold", self.run_job()["message"])

    def test_the_list_checked(self):
        good = {"era": "WWI", "version": "a" * 64, "units": [{"key": "k", "era": "WWI", "model": "WWI/USA/x.glb"}],
                "parts": [{"file": "era-units-WWI-1.zip", "size": 10, "sha256": "b" * 64}]}
        bad = [dict(good, era="Space"), dict(good, version="x"), dict(good, units=[]),
               dict(good, parts=[{"file": "../era-units-x.zip", "size": 10, "sha256": "b" * 64}]),
               dict(good, parts=[{"file": "era-units-WWI-1.zip", "size": 2_000_000_001, "sha256": "b" * 64}]),
               dict(good, units=[{"key": "k", "era": "WWI", "model": "C:/x.glb"}])]
        for b in bad:
            self.assertEqual(era_units.parse_list(json.dumps({"format": 1, "sections": [b]}).encode()), [], b)
        self.assertEqual(len(era_units.parse_list(json.dumps({"format": 1, "sections": [good, good]}).encode())), 1)
        with self.assertRaises(era_units.EraDownloadError):
            era_units.parse_list(b'{"format": 2, "sections": []}')
        self.assertTrue(era_units.safe_member("Cold War/USA/M1 Abrams.glb"))
        self.assertTrue(era_units.safe_member("Cold_War/China/An_12_Chinese.glb"))   # as the library names it
        for name in ("pictures/../x.jpg", "WWI\\USA\\x.glb", "pictures/a/b.jpg", "WWI/USA/x.py", "/WWI/USA/x.glb"):
            self.assertFalse(era_units.safe_member(name), name)

    def test_no_list(self):
        (self.release / era_units.LIST).unlink(missing_ok=True)
        res = self.api.era_sections()
        self.assertEqual(res["sections"], [])
        self.assertIn("couldn't be loaded", res["message"])
        with self.assertRaises(StudioError):
            self.api.era_download("WWI")


if __name__ == "__main__":
    unittest.main()
