"""Build one app into a Windows program with Nuitka, then its installer with Inno Setup (PLAN.md ADR 9; how and why:
installers/README.md). Runs on Windows: GitHub Actions does it on every push to main (.github/workflows/apps.yml).

  py -3 installers/build_app.py launcher|studio [--test-install]

Steps: draw the icon; compile the app into a folder under build/<app>/ ("RUSE Launcher.exe" and everything it
needs, Python included; the Studio also the game's own Python 2.5.1: python251()); run that program's self-test;
make dist/RUSE-Launcher-Setup-<version>.exe. With
--test-install it also installs the result into a scratch folder, runs the installed app's self-test and uninstalls.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPS = {
    "launcher": {"name": "RUSE Launcher", "package": "ruse_launcher", "description": "Play R.U.S.E. with mods",
                 "id": "96F731B1-F85A-48E8-A810-49128DF99706"},
    "studio": {"name": "RUSE Studio", "package": "ruse_studio", "description": "Make mods for R.U.S.E.",
               "id": "89731BD4-5E55-415F-970E-F6CBBB8CFD51",
               # the two libraries LittleGroove's engine shows the game's scripts with (the AI tab, rusemod.mapscripts):
               # they load parts of themselves by name, which Nuitka can't follow from the code
               "include": ("uncompyle6", "xdis"),
               # the game's own Python, which saves a changed mission script in the game's form (rusemod.mapscripts)
               "python251": True},
}  # the ids never change: they let a new installer replace the old version

# The game's own Python 2.5.1 (the owner, 2026-10-08: "Yes, Python and installers"): only what a mission script's
# compile needs, beside the engine's code where it looks (ruse_mod_engine/python251/python.exe). From python.org's
# python-2.5.1.msi (MD5 a1d1a9c07bc4c78bd8fa05dd3efec87f, 10,970,624 bytes, as python.org lists it), unpacked
# (msiexec /a): the folder RUSE_PYTHON251 names, else the engine's own slot on a modder's PC. Every one of the game's
# 82 scripts compiles to the same bytes with these files as with the whole interpreter (checked 2026-10-08), 4 MB
# instead of 19. Its licence (the PSF's, LICENSE.txt) goes with it.
PY251_FILES = ("python.exe", "python25.dll", "msvcr71.dll", "LICENSE.txt")
PY251_LIB = ("os", "ntpath", "stat", "UserDict", "copy_reg", "types", "warnings", "linecache", "codecs")  # (Lib/<it>.py,
# what python.exe -E -S -v loads for the compile, a coding line included) and the whole encodings package
PY251_SLOT = ROOT / "src" / "ruse_mod_engine" / "python251"


def python251(app_dir: Path, source: Path | None = None) -> Path:
    """Put the game's Python 2.5.1 beside the built app's engine code (ruse_mod_engine/python251): its interpreter,
    the few library files a compile needs, its licence, and the engine's compile worker (a .py Nuitka would compile
    in). SystemExit when the interpreter isn't found: a Studio without it can't save a mission script."""
    source = Path(source or os.environ.get("RUSE_PYTHON251") or PY251_SLOT)
    missing = [n for n in PY251_FILES if not (source / n).is_file()]
    missing += [f"Lib/{n}.py" for n in PY251_LIB if not (source / "Lib" / f"{n}.py").is_file()]
    if missing or not (source / "Lib" / "encodings" / "__init__.py").is_file():
        raise SystemExit(f"the game's Python 2.5.1 isn't in {source} ({', '.join(missing) or 'Lib/encodings'}): unpack "
                         f"python.org's python-2.5.1.msi there (msiexec /a), or set RUSE_PYTHON251 to that folder")
    target = app_dir / "ruse_mod_engine" / "python251"
    (target / "Lib").mkdir(parents=True, exist_ok=True)
    for name in PY251_FILES:
        shutil.copy2(source / name, target / name)
    for name in PY251_LIB:
        shutil.copy2(source / "Lib" / f"{name}.py", target / "Lib" / f"{name}.py")
    shutil.copytree(source / "Lib" / "encodings", target / "Lib" / "encodings", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("*.pyc", "*.pyo"))
    shutil.copy2(PY251_SLOT / "compile_worker.py", target / "compile_worker.py")
    return target
# Beside the built program: the apps' licence (GPL-3.0) and the libraries they carry, with theirs
LICENCE_FILES = ("LICENSE", "THIRD_PARTY_NOTICES.md")


def version(app: str) -> str:
    text = (ROOT / "src" / APPS[app]["package"] / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'__version__ = "([^"]+)"', text).group(1)


def exe_name(app: str) -> str:
    return f"{APPS[app]['name']}.exe"


def nuitka_command(app: str, icon: Path, out: Path) -> list[str]:
    a, v = APPS[app], version(app)
    return [sys.executable, "-m", "nuitka", "--mode=standalone", "--windows-console-mode=disable",
            "--assume-yes-for-downloads", f"--output-dir={out}", "--output-folder-name=app",
            f"--output-filename={exe_name(app)}", f"--include-package-data={a['package']}",
            "--include-package-data=rusemod", "--include-package-data=ruse_mod_engine",
            f"--windows-icon-from-ico={icon}", "--company-name=RUSE Mod Platform",
            f"--product-name={a['name']}", f"--file-version={v}", f"--product-version={v}",
            f"--file-description={a['description']}", "--copyright=GPL-3.0 (C) 2026 sneadtristen6 and the RUSE Mod Platform contributors", f"--report={out / 'report.xml'}",
            *(f"--include-package={p}" for p in a.get("include", ())),
            str(ROOT / "installers" / f"{app}.py")]


def iscc() -> str:
    found = shutil.which("iscc") or shutil.which("ISCC")
    if found:
        return found
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if base and Path(base, "Inno Setup 6", "ISCC.exe").is_file():
            return str(Path(base, "Inno Setup 6", "ISCC.exe"))
    raise SystemExit("Inno Setup 6 isn't installed (https://jrsoftware.org/isdl.php, or: choco install innosetup)")


def installer_command(app: str, program: Path, icon: Path, dist: Path) -> list[str]:
    a, v = APPS[app], version(app)
    return [iscc(), f"/DAppName={a['name']}", f"/DAppId={a['id']}", f"/DAppVersion={v}", f"/DExeName={exe_name(app)}",
            f"/DAppDescription={a['description']}", f"/DSourceDir={program}", f"/DIconFile={icon}",
            f"/DOutputDir={dist}", f"/DOutputName={a['name'].replace(' ', '-')}-Setup-{v}",
            str(ROOT / "installers" / "installer.iss")]


# Run by Blender from files of their own (rusemod.blender: blender --python <file>), so they go beside the compiled
# code as they are: Nuitka compiles every .py into the program, and the built app had none to give Blender
# (Studio 0.9.7's install folder: rusemod\labels.toml only, 2026-10-05).
BLENDER_SCRIPTS = ("blender_open.py", "blender_menu.py")


def blender_scripts(app_dir: Path) -> None:
    """Copy the scripts Blender runs into the built app's rusemod folder, where rusemod.blender looks for them (beside
    its own module, as rusemod.schema finds labels.toml)."""
    target = app_dir / "rusemod"
    target.mkdir(parents=True, exist_ok=True)
    for name in BLENDER_SCRIPTS:
        shutil.copy2(ROOT / "src" / "rusemod" / name, target / name)


def licence_files(app_dir: Path) -> None:
    """Copy the licence files beside the built program, so every install carries them (the GPL asks it of a program
    given out, and of the GPL libraries in it)."""
    for name in LICENCE_FILES:
        shutil.copy2(ROOT / name, app_dir / name)


def run(cmd: list[str]) -> None:
    print("> " + " ".join(f'"{c}"' if " " in c else c for c in cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "src")))


def self_test(program: Path, label: str) -> None:
    """Run a built or installed app's self-test (it opens no window) and show its report."""
    report = Path(tempfile.mkdtemp()) / "self-test.txt"
    code = subprocess.run([str(program), "--self-test", str(report)], timeout=300).returncode
    print(f"--- self-test of the {label} ---\n" + (report.read_text(encoding="utf-8") if report.is_file()
                                                   else "(no report written)\n"), flush=True)
    if code != 0:
        raise SystemExit(f"the self-test of the {label} failed (exit code {code})")


def test_install(app: str, setup: Path) -> None:
    """Install silently into a scratch folder (as the player, no admin), check the installed app, uninstall."""
    target = Path(tempfile.mkdtemp()) / APPS[app]["name"]
    run([str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CURRENTUSER", f"/DIR={target}",
         "/TASKS=", "/LOG=" + str(target.parent / "install.log")])
    self_test(target / exe_name(app), "installed app")
    run([str(target / "unins000.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"])


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # the self-test reports hold Chinese and Russian words
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] not in APPS or sys.platform != "win32":
        print(__doc__)
        return 2
    app = args[0]
    build, dist = ROOT / "build" / app, ROOT / "dist"
    shutil.rmtree(build, ignore_errors=True)
    dist.mkdir(parents=True, exist_ok=True)
    run([sys.executable, str(ROOT / "installers" / "icons.py"), str(ROOT / "build" / "icons")])
    icon = ROOT / "build" / "icons" / f"{app}.ico"
    run(nuitka_command(app, icon, build))
    program = next(build.rglob(exe_name(app)))
    blender_scripts(program.parent)
    licence_files(program.parent)
    if APPS[app].get("python251"):
        python251(program.parent)
    self_test(program, "built app")
    run(installer_command(app, program.parent, icon, dist))
    setup = dist / f"{APPS[app]['name'].replace(' ', '-')}-Setup-{version(app)}.exe"
    print(f"Made {setup} ({setup.stat().st_size // 1_000_000} MB)")
    if "--test-install" in args:
        test_install(app, setup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
