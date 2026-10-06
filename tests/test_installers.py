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

    def test_the_owners_artwork_is_the_icon(self):
        """installers/art: each app's .ico (every size Windows asks for, PNG pictures, square) and its 256 px PNG,
        which make() hands to the build."""
        for app in ("launcher", "studio"):
            data, preview = icons.make(app)
            self.assertEqual(data, (icons.ART / f"{app}.ico").read_bytes())
            self.assertEqual(preview[:8], b"\x89PNG\r\n\x1a\n")
            reserved, kind, count = struct.unpack_from("<HHH", data)
            self.assertEqual((reserved, kind), (0, 1))
            sizes = []
            for i in range(count):
                w, h, _c, _r, _planes, _bits, length, at = struct.unpack_from("<BBBBHHII", data, 6 + 16 * i)
                self.assertEqual(w, h)
                self.assertEqual(data[at:at + 8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", data[at + 16:at + 24]), (w or 256, h or 256))
                sizes.append(w or 256)
            self.assertEqual(sorted(sizes), [16, 24, 32, 48, 64, 128, 256])
        ui = Path(ruse_launcher.__file__).parent / "ui"
        self.assertIn('src="logo.png"', (ui / "index.html").read_text(encoding="utf-8"))
        self.assertEqual((ui / "logo.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        studio_ui = Path(ruse_studio.__file__).parent / "ui"
        self.assertIn('src="logo.png"', (studio_ui / "index.html").read_text(encoding="utf-8"))

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

    def test_the_tests_run_with_the_numpy_the_apps_carry_and_without(self):
        # installers/requirements.txt pins the numpy the apps are built with (the map sums on whole grids); tests.yml
        # installs that same one for its Python 3.12 runs (numpy 2.5 needs 3.12) and keeps its 3.11 runs without
        # numpy: the plain sums, which every whole-grid module is checked against, must go on working alone
        pin = re.search(r"^numpy==(\S+)", (ROOT / "installers" / "requirements.txt").read_text(encoding="utf-8"), re.M)
        self.assertIsNotNone(pin)
        text = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
        self.assertIn(f'"numpy=={pin.group(1)}"', text)
        self.assertIn('python: ["3.11", "3.12"]', text)
        self.assertIn("if: matrix.python == '3.12'", text)

    def test_the_tests_install_every_library_the_apps_carry_at_its_pin(self):
        # what the apps carry is pinned in installers/requirements.txt from numpy on (above it: the build's tools and
        # the window library); the Python 3.12 test runs install each at that same version, so the tests check what
        # the apps ship (the Studio's script viewer, 2026-10-06: its libraries and the three they need)
        req = (ROOT / "installers" / "requirements.txt").read_text(encoding="utf-8")
        pins = re.findall(r"^([A-Za-z0-9_.-]+==\S+)$", req[req.index("\nnumpy=="):], re.M)
        self.assertGreater(len(pins), 1)
        text = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
        for pin in pins:
            with self.subTest(pin=pin):
                self.assertIn(f'"{pin}"', text)

    def test_the_release_page_is_made_in_utf8(self):
        # the page's links name each language in its own script; GitHub's Windows runner prints in a Western code
        # page, and the first release with notes in ten languages stopped on a UnicodeEncodeError in notes_json's
        # print (launcher-v0.4.8, 2026-10-06). Before that print: Python's output and PowerShell's reading of it UTF-8,
        # and the English notes read as UTF-8 too
        text = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        publish = text[text.index("name: Publish the release"):]
        before = publish[:publish.index("python installers/notes_json.py")]
        self.assertIn('$env:PYTHONIOENCODING = "utf-8"', before)
        self.assertIn("[Console]::OutputEncoding = [System.Text.Encoding]::UTF8", before)
        self.assertIn("Get-Content -Raw -Encoding utf8", before)


class ReleaseNotesLinks(unittest.TestCase):
    def test_the_links_print_on_a_western_console(self):
        # what the runner did: a stdout in cp1252. notes_json makes its own output UTF-8 whatever the console is
        notes_json = load("notes_json")
        raw = io.BytesIO()
        out = io.TextIOWrapper(raw, encoding="cp1252", write_through=True)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(sys, "stdout", out):
            code = notes_json.main(["launcher", tmp, "launcher-v0.4.8"])
            sys.stdout.flush()
        self.assertEqual(code, 0)
        expected = notes_json.links("launcher", "launcher-v0.4.8", notes_json.book("launcher"))
        self.assertEqual(raw.getvalue().decode("utf-8").strip(), expected)
        self.assertFalse(expected.isascii(), "the links should hold a language's own name (the case that broke)")


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

    def test_the_studio_takes_its_script_libraries_whole(self):
        # the libraries the Studio shows the game's scripts with load parts of themselves by name, which Nuitka
        # can't follow from the code: the Studio's build takes each whole (its self-test shows a script); the
        # Launcher doesn't carry them
        include = build_app.APPS["studio"]["include"]
        self.assertTrue(include)
        studio = build_app.nuitka_command("studio", Path("studio.ico"), Path("out"))
        launcher = build_app.nuitka_command("launcher", Path("launcher.ico"), Path("out"))
        for package in include:
            with self.subTest(package=package):
                self.assertIn(f"--include-package={package}", studio)
                self.assertNotIn(f"--include-package={package}", launcher)

    def test_the_licence_files_go_beside_the_program(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_app.licence_files(Path(tmp))
            for name in build_app.LICENCE_FILES:
                with self.subTest(name=name):
                    self.assertEqual(Path(tmp, name).read_bytes(), (ROOT / name).read_bytes())

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

    def test_an_installed_app_without_numpy_fails_its_self_test(self):
        from rusemod import groundpaint, tgu1, update
        said = groundpaint.whole_grids()  # from the repo it only says which way the work goes
        if groundpaint.whole_arrays() is None or tgu1.whole_arrays() is None:
            self.assertIn("the plain sums do the work", said)
        else:
            self.assertRegex(said, r"^numpy 2\.")
        with mock.patch.object(groundpaint, "whole_arrays", lambda: None):
            self.assertIn("the plain sums do the work", groundpaint.whole_grids())
            with mock.patch.object(update, "installed_app", lambda: True), self.assertRaises(RuntimeError):
                groundpaint.whole_grids()  # an installed app: its self-test fails, so the build does
        for app in ("launcher", "studio"):  # both apps build maps, both ask
            text = (ROOT / "src" / f"ruse_{app}" / "app.py").read_text(encoding="utf-8")
            self.assertIn('("the map sums on whole grids (a big map is painted by them)", _grids),', text)

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
