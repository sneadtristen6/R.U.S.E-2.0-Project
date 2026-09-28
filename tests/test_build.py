"""Building mods into a pack, and `ruse build`, on a made-up game (no game files needed)."""
import contextlib
import io
import os
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat, Ndf
from rusemod.build import BuildError, build_pack, load_mod
from rusemod.cli import main

UNITS = "genglad\\patchable\\gfx\\everything.cpp.gladndfbin"


def ints(values):
    return val(0x11, struct.pack("<I", len(values)) + b"".join(val(0x02, struct.pack("<i", v)) for v in values))


NDF = make_ndf(objects=[(0, [(0, ints([105] * 5))])], classes=["TBatimentDescriptor"], props=[("ProductionPrice", 0)],
               exports={0: "B"}, compress=True)
PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", NDF)]),
                  ("file", "readme.txt", b"untouched")])


def write_mod(root, mod_id, files, extra=""):
    folder = Path(root, mod_id)
    folder.mkdir(parents=True, exist_ok=True)
    for rel, text in files.items():
        (folder / "src" / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / "src" / rel).write_text(text, encoding="utf-8")
    (folder / "mod.toml").write_text(f'[mod]\nid = "{mod_id}"\nversion = "1.0.0"\n{extra}', encoding="utf-8")
    return folder


def price(pack_bytes):
    arc = Edat(pack_bytes)
    return Ndf(arc.read(arc.find("everything.cpp.gladndfbin"))).objects[0].get(0).int_list()


class LoadingMods(unittest.TestCase):
    def test_a_mod_folder(self):
        with tempfile.TemporaryDirectory() as d:
            folder = write_mod(d, "econ", {"b.rndf": "patch $/B ( ProductionPrice += 1 )",
                                           "a/x.rndf": "when mod better-ai ( patch $/B ( ProductionPrice *= 2 ) )"},
                               extra='[dependencies]\ncore = "^1.0"\n[load]\nafter = ["z"]\n')
            info, ops = load_mod(folder)
            self.assertEqual((info.id, info.version, info.depends, info.after), ("econ", "1.0.0", {"core": "^1.0"}, ["z"]))
            self.assertEqual([o.file for o in ops], ["src/a/x.rndf", "src/b.rndf"])  # files in path order
            self.assertEqual(info.when_mods, {"better-ai"})

    def test_a_single_rndf_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d, "My Tweak.rndf")
            f.write_text("patch $/B ( ProductionPrice += 1 )", encoding="utf-8")
            info, ops = load_mod(f)
            self.assertEqual((info.id, len(ops)), ("my-tweak", 1))

    def test_bad_mods_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(BuildError, "no mod.toml"):
                load_mod(d)
            folder = write_mod(d, "Bad_ID", {})
            with self.assertRaisesRegex(BuildError, "lowercase"):
                load_mod(folder)


class BuildingAPack(unittest.TestCase):
    def mods(self, d):
        return [load_mod(write_mod(d, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})),
                load_mod(write_mod(d, "hardcore", {"hard.rndf": "patch $/B ( ProductionPrice += 5 )"}))]

    def test_worked_example_in_a_real_pack(self):
        with tempfile.TemporaryDirectory() as d:
            arc = Edat(PACK)
            result = build_pack(arc, self.mods(d), build_id="24687178")
            self.assertEqual((result.order, result.errors), (["econ-half", "hardcore"], []))
            new = arc.to_bytes(result.changed)
            self.assertEqual(price(new), [58] * 5)
            self.assertEqual(Edat(new).read(Edat(new).find("readme.txt")), b"untouched")
            self.assertEqual(len(result.fingerprint), 32)

    def test_errors_mean_nothing_to_write(self):
        with tempfile.TemporaryDirectory() as d:
            bad = load_mod(write_mod(d, "bad", {"x.rndf": "patch $/Nope ( P = 1 )"}))
            result = build_pack(Edat(PACK), [bad])
            self.assertTrue(result.errors)
            self.assertEqual(result.changed, {})


class DebugInfoShadows(unittest.TestCase):
    def test_debuginfo_copies_are_left_as_shipped(self):
        pack = make_edat([("dir", "genglad\\patchable\\gfx\\", [
            ("file", "everything.cpp.gladndfbin", NDF),
            ("file", "everything_debuginfo.cpp.gladndfbin", NDF)])])  # repeats every name of the main file
        with tempfile.TemporaryDirectory() as d:
            mod = load_mod(write_mod(d, "half", {"p.rndf": "patch every TBatimentDescriptor ( ProductionPrice *= 0.5 )"}))
            result = build_pack(Edat(pack), [mod])
        self.assertEqual(result.errors, [])
        self.assertEqual(list(result.changed), ["genglad\\patchable\\gfx\\everything.cpp.gladndfbin"])
        self.assertEqual([f.message for f in result.findings],
                         ["left 1 debug-info copies as shipped (everything_debuginfo.cpp.gladndfbin)"])


class Report(unittest.TestCase):
    def test_similar_notes_collapse(self):
        from rusemod.cli import report_lines
        from rusemod.patch import Finding
        notes = [Finding("note", f"m (p.rndf:4): $/GFX/Everything/B{i} has no ProductionPrice; skipped") for i in range(10)]
        lines = report_lines([Finding("error", "boom")] + notes)
        self.assertEqual(lines[0], "  error    boom")
        self.assertEqual(len(lines), 5)
        self.assertIn("… and 7 more like this", lines[-1])
        self.assertEqual(len(report_lines(notes, show_all=True)), 10)


class BuildCommand(unittest.TestCase):
    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(list(argv))
        return code, out.getvalue()

    def test_build_to_a_file_and_to_a_modded_copy(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d, "steamapps", "common", "R.U.S.E")
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "RUSE.exe").write_bytes(b"MZ")
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            Path(d, "steamapps", "appmanifest_21970.acf").write_text('"AppState" { "buildid" "24687178" }')
            mod = write_mod(d, "econ-half", {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"})

            code, out = self.run_cli("--game", str(game), "build", str(mod), "--out", str(Path(d, "out.dat")))
            self.assertEqual(code, 0, out)
            self.assertIn("load order: econ-half", out)
            self.assertIn("fingerprint: ", out)
            self.assertEqual(price(Path(d, "out.dat").read_bytes()), [53] * 5)  # 105 x 0.5 = 52.5 -> 53

            copy = Path(d, "RUSE-Instances", "econ")
            code, out = self.run_cli("--game", str(game), "build", str(mod), "--instance", str(copy))
            self.assertEqual(code, 0, out)
            self.assertEqual(price((copy / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes()), [53] * 5)
            self.assertEqual((copy / "steam_appid.txt").read_text(), "21970")
            self.assertEqual(price(PACK), [105] * 5)  # the made-up "Steam install" pack is untouched
            self.assertEqual((game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes(), PACK)

    def test_build_refuses_when_mods_have_errors(self):
        with tempfile.TemporaryDirectory() as d:
            game = Path(d, "R.U.S.E")
            (game / "Data" / "PC" / "190852").mkdir(parents=True)
            (game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
            mod = write_mod(d, "bad", {"x.rndf": "patch $/Nope ( P = 1 )"})
            code, out = self.run_cli("--game", str(game), "build", str(mod), "--out", str(Path(d, "out.dat")))
            self.assertEqual(code, 2)
            self.assertIn("Nothing was written.", out)
            self.assertFalse(Path(d, "out.dat").exists())


class Examples(unittest.TestCase):
    def test_every_example_mod_loads(self):
        root = Path(__file__).resolve().parent.parent / "examples"
        folders = sorted(p for p in root.iterdir() if (p / "mod.toml").is_file())
        self.assertTrue(folders)
        for folder in folders:
            info, ops = load_mod(folder)
            self.assertEqual(info.id, folder.name)
            self.assertTrue(ops, folder.name)


if __name__ == "__main__":
    unittest.main()
