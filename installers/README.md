# Installers for the two apps

RUSE Launcher (players) and RUSE Studio (modders) each become a normal Windows program with its own installer
(PLAN.md decision 22, ADR 9). Nobody needs Python or Git to use them.

## Getting them

**Players: the Releases page.** Each version is published as a GitHub Release (`.github/workflows/release.yml`):
push a tag `launcher-v<version>` or `studio-v<version>` (it must equal the app's `__version__`), and GitHub builds,
test-installs and attaches `RUSE-Launcher-Setup-<version>.exe` itself, not zipped, with its SHA-256 in the notes.
Releases need no GitHub login and don't expire, and every player downloads the same file from the same address.

**Testers: the latest build.** GitHub also builds both apps on every push to `main` that changes them
(`.github/workflows/apps.yml`). Open the repo's **Actions** tab → the latest **apps** run → **Artifacts**:
`launcher-installer` and `studio-installer`. Each download is a zip holding `RUSE-Launcher-Setup-<version>.exe` or
`RUSE-Studio-Setup-<version>.exe`. These need a GitHub login and expire after 90 days, so they're for testing only.

### Browser warnings (Chrome called the first test build "dangerous", 2026-09-28)

Browsers judge a download by its address and by how many people have downloaded that exact file before. A test
build is the worst case: a new, unsigned file every time, in a zip, from a generic cloud-storage address. That first
build was checked (its SHA-256 matched GitHub's record, and Windows Defender found nothing). What we do about it:

1. **Releases, not test builds** (done): one stable file per version at a GitHub address, so its reputation grows as
   people download it. Don't publish a new version without a reason; each new file starts from zero.
2. **Updates from inside the launcher** (planned, Velopack): after the first install, updates never pass through a
   browser, so the warning can only ever appear once, at the first download.
3. **Report false alarms** for each release (needs the owner's go, since it sends the file to Google and Microsoft):
   Google Safe Browsing's error report and Microsoft's file submission (Defender and SmartScreen) usually clear a
   false alarm within days.
4. **Later, with no browser download at all:** `winget install` (Windows' package manager) and the Microsoft Store.
   Code signing is the paid way to carry a reputation from one version to the next; it isn't needed yet. Run it: no admin rights
needed; it installs for your Windows user, adds a Start menu entry (and a desktop icon if you tick it), and has an
uninstaller in Windows' "Installed apps". Uninstalling keeps your mods and settings (`%LOCALAPPDATA%\RUSE Mod Platform`).

- **Windows may warn "Windows protected your PC"** the first time: the installers aren't signed yet (signing costs
  money and waits for the first public release, PLAN.md ADR 9). Click "More info", then "Run anyway".
- **WebView2:** the apps' screens need Microsoft Edge WebView2 Runtime. Windows 11 has it, and so do most Windows 10
  PCs. If yours doesn't, the installer and the app both say so and offer Microsoft's download.
- What the installed apps print goes to `%LOCALAPPDATA%\RUSE Mod Platform\logs\` (for bug reports).

## How they're made

`installers/build_app.py launcher|studio` (Windows only) does it all:

1. `icons.py` draws the app's icon (standard library only; no image files in the repo).
2. **Nuitka** compiles the app (`launcher.py` / `studio.py` start it) into a folder with `RUSE Launcher.exe` and
   everything it needs, Python included. It's a folder, not one file: that starts faster and antivirus programs
   trust it more.
3. The built program checks itself: `"RUSE Launcher.exe" --self-test report.txt` (its screens and data files, its
   back end, and the window library with its .NET and WebView2 parts), without opening a window.
4. **Inno Setup** wraps the folder into the installer (`installer.iss`, one script for both apps).
5. With `--test-install` (the GitHub build uses it): the installer runs silently into a scratch folder, the installed
   program checks itself too, and it's uninstalled.

The tool versions are pinned in `requirements.txt`, so every build is the same. To build on your own PC: Python 3.12,
`py -3 -m pip install -r installers/requirements.txt`, Inno Setup 6, Visual Studio's C++ build tools (Nuitka offers to
download a compiler otherwise), then `py -3 installers/build_app.py launcher`.

Each app's version is `__version__` in its package (`src/ruse_launcher/__init__.py`, `src/ruse_studio/__init__.py`).
The installer ids in `build_app.py` never change: they let a new installer replace an older version in place.
