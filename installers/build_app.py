"""Build one app into a Windows program with Nuitka, then its installer with Inno Setup (PLAN.md ADR 9; how and why:
installers/README.md). Runs on Windows: GitHub Actions does it on every push to main (.github/workflows/apps.yml).

  py -3 installers/build_app.py launcher|studio [--test-install]

Steps: draw the icon; compile the app into a folder under build/<app>/ ("RUSE Launcher.exe" and everything it
needs, Python included; the Studio also the game's own Python 2.5.1: python251(); both Microsoft's WebView2
installer, checked to be Microsoft's: webview2_setup()); run that program's self-test;
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

# Microsoft's WebView2 installer (its "Evergreen Bootstrapper", about 2 MB, which fetches WebView2 from Microsoft), carried
# by both apps in webview2/ beside the program and run only on the player's yes: the installer's ticked box, the box
# when an app starts without WebView2, Settings (rusemod.webview2; the owner, 2026-11-24). Microsoft's distribution
# page says to "package it with your WebView2 app". Fetched at each build from Microsoft's own link (the one
# rusemod.webui.WEBVIEW2_DOWNLOAD opens: it leads to MicrosoftEdgeWebview2Setup.exe on Microsoft's download server,
# checked 2026-11-24), or taken from the file RUSE_WEBVIEW2_SETUP names. Microsoft changes the file now and then, so
# its bytes aren't pinned: the build stops unless Windows says its signature is valid and Microsoft Corporation's.
WEBVIEW2_URL = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"
WEBVIEW2_PLACE = ("webview2", "MicrosoftEdgeWebview2Setup.exe")  # rusemod.webview2's FOLDER and SETUP_NAME
WEBVIEW2_SIGNER = "O=Microsoft Corporation"


def webview2_signature(path: Path) -> tuple[str, str]:
    """Windows' word on `path`'s signature: (its status, "Valid" when it holds; the signer's certificate subject)."""
    script = ("$s = Get-AuthenticodeSignature -LiteralPath $env:RUSE_SIGNED_FILE; "
              "[string]$s.Status; [string]$s.SignerCertificate.Subject")
    out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True,
                         text=True, timeout=120, env=dict(os.environ, RUSE_SIGNED_FILE=str(path)))
    lines = [line.strip() for line in out.stdout.splitlines()] + ["", ""]
    return lines[0], lines[1]


def _fetch(url: str, target: Path) -> None:
    import urllib.request
    with urllib.request.urlopen(url, timeout=120) as answer, open(target, "wb") as f:
        shutil.copyfileobj(answer, f)


def webview2_setup(app_dir: Path, source=None, fetch=_fetch, signature=webview2_signature) -> Path:
    """Put Microsoft's WebView2 installer in the built app's webview2 folder: the file `source` (else the one
    RUSE_WEBVIEW2_SETUP names), else fetched from Microsoft. SystemExit, with the file taken out again, unless its
    signature is valid and Microsoft Corporation's: an app never carries an installer that isn't Microsoft's."""
    target = app_dir.joinpath(*WEBVIEW2_PLACE)
    target.parent.mkdir(parents=True, exist_ok=True)
    given = source or os.environ.get("RUSE_WEBVIEW2_SETUP")
    if given:
        shutil.copy2(given, target)
    else:
        fetch(WEBVIEW2_URL, target)
    status, signer = signature(target) if target.is_file() else ("no file", "")
    if status != "Valid" or WEBVIEW2_SIGNER not in signer:
        target.unlink(missing_ok=True)
        raise SystemExit(f"Microsoft's WebView2 installer didn't pass the signature check (status: {status or 'none'}; "
                         f"signed by: {signer or 'nobody'}): the build stops rather than ship it")
    print(f"WebView2 installer: {target.stat().st_size:,} bytes, signed by {signer}", flush=True)
    return target


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
            "--include-package-data=certifi",  # its cacert.pem: Mozilla's root list (rusemod.net's third try)
            f"--windows-icon-from-ico={icon}", "--company-name=RUSE Mod Platform",
            f"--product-name={a['name']}", f"--file-version={v}", f"--product-version={v}",
            f"--file-description={a['description']}", "--copyright=GPL-3.0 (C) 2026 sneadtristen6 and the RUSE Mod Platform contributors", f"--report={out / 'report.xml'}",
            *(f"--include-package={p}" for p in a.get("include", ())),
            *(f"--include-data-files={src}={dest}" for src, dest in data_files(app)
              if src.suffix.lower() in SKIPPED_SUFFIXES),
            str(ROOT / "installers" / f"{app}.py")]


# Files the apps read that Nuitka's --include-package-data leaves out by their suffix alone (its
# default_ignored_suffixes in nuitka/freezer/IncludedDataFiles.py, Nuitka 4.2.2 as pinned: .bin, .exe, .dll ...):
# RUSE Guard's compiled game scripts, rusemod/gamescripts/*.bin, were missing from Launcher 0.4.8.10 and 0.4.8.11 and
# Studio 0.9.8.10 and 0.9.8.11, so every modded Play and Test in game stopped ("[Errno 2] No such file or directory:
# ...fairplay_watch.bin", the owner, 2026-11-01). Each such file goes in by name (--include-data-files keeps any
# suffix), and a build stops when any data file of the app's packages isn't in the built app (check_data_files).
SKIPPED_SUFFIXES = (".bin", ".exe", ".dll", ".so", ".pyd", ".pyx", ".pyi", ".pyw", ".dylib")
CODE_SUFFIXES = (".py", ".pyc", ".pyo")  # compiled into the program (the scripts Blender runs: blender_scripts)


def data_files(app: str) -> list[tuple[Path, str]]:
    """Every file of the app's packages that isn't Python code: (the source file, its path in the built app)."""
    out = []
    for package in (APPS[app]["package"], "rusemod", "ruse_mod_engine"):
        base = ROOT / "src" / package
        for path in sorted(base.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix.lower() not in CODE_SUFFIXES \
                    and path.name != "py.typed":
                out.append((path, f"{package}/{path.relative_to(base).as_posix()}"))
    return out


def check_data_files(app: str, app_dir: Path) -> None:
    """Stop the build when a data file of the app's packages isn't in the built app: a modded game can't be built
    without them, and the self-test doesn't build one."""
    missing = [dest for _src, dest in data_files(app) if not (app_dir / dest).is_file()]
    if missing:
        raise SystemExit(f"the built app lacks {len(missing)} file(s) it reads: " + ", ".join(missing[:20]))


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
    # the other app's id: the uninstaller looks for its install record, to leave the shared folder alone while it stays
    other = next(o["id"] for k, o in APPS.items() if k != app)
    return [iscc(), f"/DAppName={a['name']}", f"/DAppId={a['id']}", f"/DOtherAppId={other}", f"/DAppVersion={v}",
            f"/DExeName={exe_name(app)}",
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
    webview2_setup(program.parent)
    if APPS[app].get("python251"):
        python251(program.parent)
    check_data_files(app, program.parent)
    self_test(program, "built app")
    run(installer_command(app, program.parent, icon, dist))
    setup = dist / f"{APPS[app]['name'].replace(' ', '-')}-Setup-{version(app)}.exe"
    print(f"Made {setup} ({setup.stat().st_size // 1_000_000} MB)")
    if "--test-install" in args:
        test_install(app, setup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
