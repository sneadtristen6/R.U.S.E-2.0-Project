"""The installer build's pieces that can be checked anywhere (installers/, packaging on Windows itself runs in
.github/workflows/apps.yml): the icons, the build commands, the installed apps' self-test and log file."""
import importlib.util
import io
import os
import re
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

import ruse_launcher
import ruse_studio
from rusemod import webui

ROOT = Path(__file__).parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(f"installers_{name}", ROOT / "installers" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


icons, build_app = load("icons"), load("build_app")


def png_pixels(data: bytes):
    """Decode our own PNGs (8-bit RGBA, no filters) back to rows of pixels."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack_from(">II", data, 16)
    idat = data.index(b"IDAT")
    size = struct.unpack_from(">I", data, idat - 4)[0]
    raw = zlib.decompress(data[idat + 4: idat + 4 + size])
    stride = 1 + 4 * width
    return [[tuple(raw[y * stride + 1 + 4 * x: y * stride + 5 + 4 * x]) for x in range(width)] for y in range(height)]


class Icons(unittest.TestCase):
    def test_pictures(self):
        for app in ("launcher", "studio"):
            rows = icons.draw(app, 32)
            pixels = png_pixels(icons.png(rows))
            self.assertEqual(pixels, [[tuple(p) for p in row] for row in rows])
            self.assertEqual(pixels[0][0][3], 0)  # the corner is outside the rounded tile
            self.assertEqual(pixels[16][16][:3], icons.GOLD)  # the Play triangle / the pencil crosses the middle
            self.assertEqual(pixels[0][16][:3], icons.EDGE)  # the gold edge along the top

    def test_ico_file(self):
        small = icons.bitmap(icons.draw("studio", 16))
        big = icons.png(icons.draw("studio", 24))
        data = icons.ico([(16, small), (256, big)])
        self.assertEqual(struct.unpack_from("<HHH", data), (0, 1, 2))
        entries = [struct.unpack_from("<BBBBHHII", data, 6 + 16 * i) for i in range(2)]
        self.assertEqual([(e[0], e[5]) for e in entries], [(16, 32), (0, 32)])  # 0 means 256
        self.assertEqual(data[entries[0][7]:entries[0][7] + entries[0][6]], small)
        self.assertEqual(data[entries[1][7]:entries[1][7] + 8], b"\x89PNG\r\n\x1a\n")
        header = struct.unpack_from("<IiiHH", small)
        self.assertEqual(header, (40, 16, 32, 1, 32))  # a bitmap and its mask: twice as high
        self.assertEqual(len(small), 40 + 16 * 16 * 4 + 16 * 4)


class WorkflowGuards(unittest.TestCase):
    def test_jobs_run_on_the_public_repo_by_its_number(self):
        # the shared private repo mirrors .github/ too, so every job checks which repo it's on: by the public repo's
        # number, which a rename keeps. A check by name ('sneadtristen6/Ruse-Mod-Platform') skipped every test, build
        # and release after the repo became R.U.S.E-2.0-Project, and nothing failed to say so (studio-v0.7.5).
        for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"github\.repository\s*==", path.name)
            jobs = len(re.findall(r"^\s+runs-on:", text, re.M))
            guards = len(re.findall(r"^\s+if: github\.repository_id == '1393317090'$", text, re.M))
            self.assertGreaterEqual(guards, jobs, path.name)


class BuildCommands(unittest.TestCase):
    def test_versions_come_from_the_apps(self):
        self.assertEqual(build_app.version("launcher"), ruse_launcher.__version__)
        self.assertEqual(build_app.version("studio"), ruse_studio.__version__)

    def test_nuitka(self):
        cmd = build_app.nuitka_command("studio", Path("studio.ico"), Path("out"))
        for option in ("--mode=standalone", "--windows-console-mode=disable", "--include-package-data=ruse_studio",
                       "--include-package-data=rusemod", "--output-filename=RUSE Studio.exe",
                       f"--file-version={ruse_studio.__version__}", "--windows-icon-from-ico=studio.ico"):
            self.assertIn(option, cmd)
        self.assertTrue(Path(cmd[-1]).is_file())  # installers/studio.py
        self.assertNotIn("ruse_launcher", " ".join(cmd))  # the other app never goes in

    def test_installer(self):
        with mock.patch.object(build_app, "iscc", lambda: "ISCC.exe"):
            cmd = build_app.installer_command("launcher", Path("prog"), Path("launcher.ico"), Path("dist"))
        defines = dict(arg[2:].split("=", 1) for arg in cmd if arg.startswith("/D"))
        self.assertEqual(defines["AppName"], "RUSE Launcher")
        self.assertEqual(defines["ExeName"], "RUSE Launcher.exe")
        self.assertEqual(defines["OutputName"], f"RUSE-Launcher-Setup-{ruse_launcher.__version__}")
        self.assertRegex(defines["AppId"], r"^[0-9A-F]{8}(-[0-9A-F]{4}){3}-[0-9A-F]{12}$")
        self.assertNotEqual(build_app.APPS["launcher"]["id"], build_app.APPS["studio"]["id"])
        script = (ROOT / "installers" / "installer.iss").read_text(encoding="utf-8")
        for name in defines:
            self.assertIn(f"{{#{name}}}", script)  # every value passed is used
        self.assertIn("AppId={{{#AppId}}", script)  # braces around the id, the first one escaped
        self.assertIn("PrivilegesRequired=lowest", script)  # no admin rights

    def test_only_on_windows(self):
        if sys.platform != "win32":
            with mock.patch("sys.stdout", io.StringIO()):
                self.assertEqual(build_app.main(["launcher"]), 2)


class InstalledApp(unittest.TestCase):
    def test_self_test(self):
        with tempfile.TemporaryDirectory() as d:
            report = Path(d, "report.txt")
            ui = ROOT / "src" / "ruse_launcher" / "ui"
            code = webui.self_test(str(report), ui, ["index.html", "app.js"], [("answers", lambda: "yes")],
                                   window=False)
            lines = report.read_text(encoding="utf-8").splitlines()
            self.assertEqual(code, 0, lines)
            self.assertEqual(lines[-1], "PASSED")
            self.assertIn("ok    answers: yes", lines)
            code = webui.self_test(str(report), ui, ["missing.html"], [("broken", lambda: 1 / 0)], window=False)
            text = report.read_text(encoding="utf-8")
            self.assertEqual(code, 1)
            self.assertIn("FAIL  file missing.html", text)
            self.assertIn("FAIL  broken: ZeroDivisionError", text)
            self.assertIn("FAILED: 2", text)

    def test_log_file(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": d}):
            logs = Path(d, "logs")
            logs.mkdir()
            (logs / "studio.log").write_text("x" * 1_000_001, encoding="utf-8")  # too big: starts over
            out, err = sys.stdout, sys.stderr
            try:
                log = webui.log_to_file("studio")
                print("hello from the installed Studio")
            finally:
                sys.stdout.close()
                sys.stdout, sys.stderr = out, err
            self.assertEqual(log.read_text(encoding="utf-8"), "hello from the installed Studio\n")
            self.assertEqual((logs / "studio.old.log").stat().st_size, 1_000_001)

    def test_entry_scripts_start_the_right_app(self):
        for app in ("launcher", "studio"):
            text = (ROOT / "installers" / f"{app}.py").read_text(encoding="utf-8")
            self.assertIn(f"from ruse_{app}.app import main", text)
            self.assertIn(f'log_to_file("{app}")', text)
            self.assertIsNone(re.search(r"ruse_(launcher|studio)", text.replace(f"ruse_{app}", "")))


if __name__ == "__main__":
    unittest.main()
