"""Microsoft's WebView2, which the apps' own window draws its screens with (rusemod.webui): whether this PC has it, and
Microsoft's small installer for it ("Evergreen Bootstrapper"), which comes with the installed apps: installers/
build_app.py puts it in the installed app's webview2 folder, checked to be signed by Microsoft. It fetches WebView2 from
Microsoft, so it needs the internet.

It goes in only when the player says yes (the owner, 2026-11-24: "make this like a box in the settings or something
they can always get if they need, instead of forcing it into the build ... make a pop up, be like, hey, you don't have
this. Do you want this? ... in all of the first time download ones, it'll be something where you can choose, and it'll
be automatically selected ... if we detect it's Linux or something, obviously that's null"): the installers' ticked
box on a first install (installers/installer.iss), the box when an app starts without it (webui.open_window), and
the apps' Settings (WebView2Calls). Under Wine (Linux, the Steam Deck through Proton) none of it is offered: WebView2
doesn't start there (issue #21), and the apps open in the web browser instead (rusemod.browsermode)."""
from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path

from . import browsermode

SETUP_NAME = "MicrosoftEdgeWebview2Setup.exe"
FOLDER = "webview2"  # beside the program: <program folder>/webview2/MicrosoftEdgeWebview2Setup.exe
# Where Windows keeps the installed WebView2's version ("pv"): the keys Microsoft's distribution page lists, which
# installers/installer.iss and pywebview read too; per machine, then per user
CLIENT = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
KEYS = (("HKEY_LOCAL_MACHINE", "SOFTWARE\\WOW6432Node\\" + CLIENT), ("HKEY_LOCAL_MACHINE", "SOFTWARE\\" + CLIENT),
        ("HKEY_CURRENT_USER", "Software\\" + CLIENT))
# Seconds the version is looked for again after Microsoft's installer closes, in case it writes it a moment later.
# Not measured: a margin.
SETTLE = 30


def version(read=None) -> str:
    """The installed WebView2's version, "" when this PC has none (Microsoft: a missing key, an empty value or
    0.0.0.0 all mean none)."""
    read = read or _read_registry
    for root, key in KEYS:
        value = read(root, key)
        if value and value != "0.0.0.0":
            return value
    return ""


def _read_registry(root: str, key: str) -> str:
    if sys.platform != "win32":
        return ""
    import winreg
    try:
        with winreg.OpenKey(getattr(winreg, root), key) as handle:
            value, _kind = winreg.QueryValueEx(handle, "pv")
    except OSError:
        return ""
    return value if isinstance(value, str) else ""


def program_folder() -> Path:
    """The installed program's folder, where webui.webview2_loader looks first too."""
    return Path(sys.argv[0]).resolve().parent


def setup_file(folder: Path | None = None) -> Path | None:
    """Microsoft's installer that came with the app, or None (run from the repo: it comes only with a built app)."""
    path = Path(folder or program_folder()) / FOLDER / SETUP_NAME
    return path if path.is_file() else None


def offered(folder: Path | None = None) -> bool:
    """Whether the apps offer WebView2 here: on Windows only, never under Wine, and only with Microsoft's installer
    at hand."""
    return sys.platform == "win32" and not browsermode.under_wine() and setup_file(folder) is not None


def install(setup: Path, run=subprocess.run, read=None, wait=time.sleep, settle: int = SETTLE) -> str:
    """Run Microsoft's installer the way a player runs it from Microsoft's download page (no switches: its own window
    shows how far it is) and wait for it to end. Returns the version installed then, "" when there's still none."""
    run([str(setup)], check=False)
    found = version(read)
    for _ in range(settle):
        if found:
            break
        wait(1)
        found = version(read)
    return found


def start_again(argv: list[str] | None = None, popen=subprocess.Popen) -> None:
    """Start this program again, apart from this one: only a new start sees a WebView2 installed since (pywebview
    decides which engine to use once, when it's imported: webview/platforms/winforms.py, is_chromium)."""
    argv = list(sys.argv if argv is None else argv)
    program = Path(argv[0]).resolve()
    if program.suffix.lower() != ".exe" and program.with_name(program.name + ".exe").is_file():
        program = program.with_name(program.name + ".exe")
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    popen([str(program), *argv[1:]], close_fds=True, creationflags=flags)


class WebView2Calls:
    """Settings' WebView2 card, for both apps (a mixin for the window API). Tests replace `_webview2_folder` (where
    the program is), `_webview2_run` (Microsoft's installer), `_webview2_read` (the registry) and `_webview2_wait`."""

    _webview2_folder: Path | None = None
    _webview2_run = staticmethod(subprocess.run)
    _webview2_read = None
    _webview2_wait = staticmethod(time.sleep)
    _webview2_state: dict | None = None

    def webview2_status(self) -> dict:
        """{"offered": the card shows (Windows, not Wine, Microsoft's installer at hand), "version": the installed
        one ("" when none), "installing": Microsoft's installer is running, "tried": an install from Settings ended
        in this run, "failed": it ended with no WebView2}."""
        state = self._webview2_state or {}
        return {"offered": offered(self._webview2_folder), "version": version(self._webview2_read),
                "installing": bool(state.get("installing")), "tried": bool(state.get("tried")),
                "failed": bool(state.get("failed"))}

    def webview2_install(self) -> dict:
        """Settings' Install WebView2: start Microsoft's installer in the background (its own window shows how far it
        is) and return webview2_status(); the page asks again until "installing" ends. Nothing starts where it isn't
        offered, or while it's already running."""
        setup = setup_file(self._webview2_folder) if offered(self._webview2_folder) else None
        if setup is None or (self._webview2_state or {}).get("installing"):
            return self.webview2_status()
        state = {"installing": True, "tried": False, "failed": False}
        self._webview2_state = state

        def work():
            try:
                found = install(setup, run=self._webview2_run, read=self._webview2_read, wait=self._webview2_wait)
            except OSError as exc:  # Windows couldn't start it: the card says it didn't install, the log says why
                print(f"Microsoft's WebView2 installer didn't start: {type(exc).__name__}: {exc}")
                found = ""
            state.update(installing=False, tried=True, failed=not found)
        threading.Thread(target=work, name="WebView2 install", daemon=True).start()
        return self.webview2_status()
