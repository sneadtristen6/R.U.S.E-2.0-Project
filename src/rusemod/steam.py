"""Find the R.U.S.E. install through Steam, on Windows, Linux and Steam Deck.

Steam's install folder (Windows registry `SteamPath`, or the usual Linux folders) -> `libraryfolders.vdf` (looked for
in both `steamapps/` and `config/`) -> the library holding `appmanifest_21970.acf` -> `steamapps/common/<installdir>`.
The manifest also gives the Steam build id and the beta branch, if any (e.g. `compat`).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

APP_ID = "21970"
_TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|([{}])|(//[^\n]*)|([^\s{}"]+)')
_ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", '"': '"'}


def parse_vdf(text: str) -> dict:
    """Parse Valve's text KeyValues format (libraryfolders.vdf, appmanifest_*.acf). Keys are lowercased."""
    stack: list[dict] = [{}]
    key = None
    for quoted, brace, comment, bare in _TOKEN.findall(text):
        if comment:
            continue
        if brace == "{":
            if key is None:
                raise ValueError("'{' without a key")
            child: dict = {}
            stack[-1][key.lower()] = child
            stack.append(child)
            key = None
        elif brace == "}":
            if len(stack) == 1:
                raise ValueError("unbalanced '}'")
            stack.pop()
            key = None
        else:
            token = re.sub(r"\\(.)", lambda m: _ESCAPES.get(m.group(1), m.group(1)), quoted) if quoted or not bare else bare
            if key is None:
                key = token
            else:
                stack[-1][key.lower()] = token
                key = None
    return stack[0]


def steam_roots() -> list[Path]:
    """Places Steam may be installed, most likely first."""
    found: list[Path] = []
    if sys.platform == "win32":
        import winreg
        for hive, sub, name in [(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
                                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
                                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath")]:
            try:
                with winreg.OpenKey(hive, sub) as k:
                    found.append(Path(winreg.QueryValueEx(k, name)[0]))
            except OSError:
                pass
        found.append(Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam")
    else:
        home = Path.home()
        found += [home / ".steam" / "steam", home / ".local" / "share" / "Steam",
                  home / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam"]
    unique: list[Path] = []
    for p in found:
        if p.is_dir() and p.resolve() not in [u.resolve() for u in unique]:
            unique.append(p)
    return unique


def libraries(steam_root: Path) -> list[Path]:
    """Every Steam library folder listed by this Steam install (the install itself included)."""
    libs = [steam_root]
    for rel in ("steamapps/libraryfolders.vdf", "config/libraryfolders.vdf"):
        vdf = steam_root / rel
        if not vdf.is_file():
            continue
        data = parse_vdf(vdf.read_text(encoding="utf-8", errors="replace")).get("libraryfolders", {})
        for k, v in data.items():
            if not k.isdigit():
                continue
            path = v.get("path") if isinstance(v, dict) else v  # new format: {"path": ...}; old format: the path
            if path and Path(path) not in libs:
                libs.append(Path(path))
    return libs


def find_game(roots: list[Path] | None = None) -> dict | None:
    """Locate R.U.S.E. Returns a dict with game_dir, build_id, branch, data_revisions, library, or None."""
    for root in (steam_roots() if roots is None else roots):
        for lib in libraries(root):
            acf = lib / "steamapps" / f"appmanifest_{APP_ID}.acf"
            if not acf.is_file():
                continue
            state = parse_vdf(acf.read_text(encoding="utf-8", errors="replace")).get("appstate", {})
            game_dir = lib / "steamapps" / "common" / state.get("installdir", "R.U.S.E")
            if not game_dir.is_dir():
                continue
            branch = (state.get("userconfig", {}).get("betakey")
                      or state.get("mountedconfig", {}).get("betakey") or "public")
            return {"game_dir": game_dir, "build_id": state.get("buildid", "?"), "branch": branch,
                    "data_revisions": data_revisions(game_dir), "library": lib}
    return None


def build_of(game_dir: Path) -> str | None:
    """The Steam build id of the game in `game_dir`, from the manifest two folders up (steamapps/)."""
    acf = Path(game_dir).resolve().parent.parent / f"appmanifest_{APP_ID}.acf"
    if not acf.is_file():
        return None
    return parse_vdf(acf.read_text(encoding="utf-8", errors="replace")).get("appstate", {}).get("buildid")


def data_revisions(game_dir: Path) -> list[str]:
    pc = Path(game_dir) / "Data" / "PC"
    return sorted(p.name for p in pc.iterdir() if p.is_dir() and p.name.isdigit()) if pc.is_dir() else []
