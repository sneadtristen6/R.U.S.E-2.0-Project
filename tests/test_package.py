"""A mod as one file (MOD_FORMAT §2, rusemod.package): pack, check, unpack, and a manifest kept up to date."""
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_build import write_mod
from rusemod import package
from rusemod.package import PackageError, check, files_of, info_of, pack, set_values, unpack, update_manifest

HALF = {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"}
MANIFEST = '''# my mod
[mod]
id          = "econ-half"
name        = "Half price"
version     = "1.0.0"
description = "Half."

[load]
after = []
'''


class Manifest(unittest.TestCase):
    def test_values_are_set_in_place_and_the_rest_stays(self):
        text = set_values(MANIFEST, "mod", {"version": "1.1.0", "authors": ["Tristen"], "description": 'Say "hi"'})
        self.assertIn('version     = "1.1.0"\n', text)          # the line keeps its place and its alignment
        self.assertIn('description = "Say \\"hi\\""\n', text)
        self.assertIn('\nauthors = ["Tristen"]\n\n[load]', text)  # a new key goes at the end of its table
        self.assertTrue(text.startswith("# my mod\n[mod]\nid          = \"econ-half\"\n"))
        data = tomllib.loads(text)
        self.assertEqual((data["mod"]["version"], data["mod"]["authors"], data["load"]["after"]), ("1.1.0", ["Tristen"], []))
        text = set_values(text, "game", {"builds": ["24687178"], "fingerprint": "K7Q2-M9XD"})
        self.assertTrue(text.endswith('[load]\nafter = []\n\n[game]\nbuilds = ["24687178"]\nfingerprint = "K7Q2-M9XD"\n'))
        text = set_values(text, "game", {"fingerprint": None, "data_revision": "190852"})
        self.assertNotIn("fingerprint", text)
        self.assertEqual(tomllib.loads(text)["game"], {"builds": ["24687178"], "data_revision": "190852"})
        self.assertEqual(set_values(MANIFEST, "game", {}), MANIFEST)

    def test_update_manifest_writes_the_file_and_gives_the_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = write_mod(tmp, "econ-half", HALF, extra='name = "Half price"\n')
            info = update_manifest(folder, mod={"authors": ["A"], "description": "Half."}, game={"builds": ["1"]})
            self.assertEqual((info["name"], info["author"], info["description"], info["builds"]), ("Half price", "A", "Half.", ["1"]))
            self.assertEqual(info_of(folder)["version"], "1.0.0")
            with self.assertRaisesRegex(PackageError, "isn't a mod"):
                info_of(Path(tmp, "nowhere"))


class Packing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mod = write_mod(self.root, "econ-half", HALF, extra='name = "Half price"\ndescription = "Half."\n')

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text="x"):
        path = self.mod / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_pack_check_unpack_round_trip(self):
        self.write("text/units.csv", "key,us\nk1,Text\n")
        self.write("README.md", "# Half")
        self.write("files/replace/gen/x.tgv.png", "png")
        self.write("cache/big.bin", "not packed")
        self.write(".hidden", "not packed")
        self.assertEqual([f.relative_to(self.mod).as_posix() for f in files_of(self.mod)],
                         ["mod.toml", "README.md", "src/eco.rndf", "text/units.csv", "files/replace/gen/x.tgv.png"])
        out = pack(self.mod, self.root / "out", build_id="24687178", data_revision="190852", fingerprint="K7Q2-M9XD")
        self.assertEqual(out, self.root / "out" / "econ-half-1.0.0.rusemod")
        folder_info = info_of(self.mod)  # the folder's own manifest got the build mark too
        self.assertEqual((folder_info["builds"], folder_info["data_revision"], folder_info["fingerprint"]),
                         (["24687178"], "190852", "K7Q2-M9XD"))
        info = check(out)
        self.assertEqual((info["id"], info["name"], info["version"], info["description"], info["fingerprint"], info["root"]),
                         ("econ-half", "Half price", "1.0.0", "Half.", "K7Q2-M9XD", ""))
        self.assertEqual(info["files"], ["mod.toml", "README.md", "src/eco.rndf", "text/units.csv", "files/replace/gen/x.tgv.png"])
        into = self.root / "library" / "econ-half"
        self.assertEqual(unpack(out, into)["id"], "econ-half")
        for rel in info["files"]:
            self.assertEqual((into / rel).read_bytes(), (self.mod / rel).read_bytes(), rel)
        self.assertFalse((into / "cache").exists())
        with self.assertRaisesRegex(PackageError, "isn't empty"):
            unpack(out, into)
        explicit = pack(self.mod, self.root / "elsewhere" / "half.rusemod")  # a file name of the modder's choosing
        self.assertEqual(explicit, self.root / "elsewhere" / "half.rusemod")
        self.assertEqual(check(explicit)["version"], "1.0.0")

    def test_what_cant_be_packed(self):
        with self.assertRaisesRegex(PackageError, "has no mod.toml"):
            pack(self.root / "nothing", self.root)
        self.write("src/helper.py", "print(1)")
        with self.assertRaisesRegex(PackageError, "scripts or programs \\(src/helper.py\\)"):
            pack(self.mod, self.root)
        (self.mod / "src" / "helper.py").unlink()
        self.write("src/broken.rndf", "patch $/B ( ProductionPrice *= )")
        with self.assertRaisesRegex(PackageError, "Fix the mod before packing it"):
            pack(self.mod, self.root)
        (self.mod / "src" / "broken.rndf").unlink()
        update_manifest(self.mod, mod={"version": "one"})
        with self.assertRaisesRegex(PackageError, "should look like 1.0.0"):
            pack(self.mod, self.root)
        update_manifest(self.mod, mod={"version": "1.0.0", "id": "Bad Id"})
        with self.assertRaisesRegex(PackageError, "isn't allowed"):
            pack(self.mod, self.root)

    def zipped(self, name, files):
        path = self.root / name
        with zipfile.ZipFile(path, "w") as z:
            for rel, text in files.items():
                z.writestr(rel, text)
        return path

    def test_what_cant_be_unpacked(self):
        (self.root / "text.rusemod").write_text("not a zip")
        with self.assertRaisesRegex(PackageError, "isn't a mod file"):
            check(self.root / "text.rusemod")
        with self.assertRaisesRegex(PackageError, "doesn't exist"):
            check(self.root / "gone.rusemod")
        with self.assertRaisesRegex(PackageError, "no mod.toml"):
            check(self.zipped("nomanifest.rusemod", {"src/a.rndf": "patch $/B ( ProductionPrice *= 0.5 )"}))
        manifest = '[mod]\nid = "m"\nversion = "1.0.0"\n'
        with self.assertRaisesRegex(PackageError, "outside its folder"):
            check(self.zipped("escape.rusemod", {"mod.toml": manifest, "../evil.txt": "x"}))
        with self.assertRaisesRegex(PackageError, "scripts or programs \\(run.bat\\)"):
            check(self.zipped("script.rusemod", {"mod.toml": manifest, "run.bat": "x"}))
        with self.assertRaisesRegex(PackageError, "can't be read"):
            check(self.zipped("badtoml.rusemod", {"mod.toml": "[mod\nid = 1"}))
        broken = self.zipped("broken.rusemod", {"m/mod.toml": manifest, "m/src/a.rndf": "patch $/B ( X *= )"})
        with self.assertRaisesRegex(PackageError, "has a mistake in one of its files"):
            check(broken)
        self.assertEqual(check(broken, read=False)["root"], "m/")  # the shape is fine, only the content isn't
        with mock.patch.object(package, "SIZE_LIMIT", 10):
            with self.assertRaisesRegex(PackageError, "far more than a mod"):
                check(self.zipped("big.rusemod", {"mod.toml": manifest, "src/a.rndf": "x" * 100}))
        into = self.root / "lib" / "m"
        with self.assertRaises(PackageError):
            unpack(broken.with_name("escape.rusemod"), into)
        self.assertFalse(into.exists())  # nothing half-written


if __name__ == "__main__":
    unittest.main()
