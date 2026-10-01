"""Build one app into a Windows program with Nuitka, then its installer with Inno Setup (PLAN.md ADR 9; how and why:
installers/README.md). Runs on Windows: GitHub Actions does it on every push to main (.github/workflows/apps.yml).

  py -3 installers/build_app.py launcher|studio [--test-install]

Steps: draw the icon; compile the app into a folder under build/<app>/ ("RUSE Launcher.exe" and everything it
needs, Python included); run that program's self-test; make dist/RUSE-Launcher-Setup-<version>.exe. With
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
               "id": "89731BD4-5E55-415F-970E-F6CBBB8CFD51"},
}  # the ids never change: they let a new installer replace the old version


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
    self_test(program, "built app")
    run(installer_command(app, program.parent, icon, dist))
    setup = dist / f"{APPS[app]['name'].replace(' ', '-')}-Setup-{version(app)}.exe"
    print(f"Made {setup} ({setup.stat().st_size // 1_000_000} MB)")
    if "--test-install" in args:
        test_install(app, setup)
    return 0


if __name__ == "__main__":
    sys.exit(main())
