"""Shared pieces of the web-style windows of both apps (the launcher and the Studio, PLAN.md ADR 2): serving a window's
screens on this PC only, background jobs the screens follow, opening the window, and what the installed apps need
(a log file, a check that the web engine is there, a self-test for the build; installers/README.md)."""
from __future__ import annotations

import functools
import http.server
import os
import sys
import threading
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from . import startlog
from .home import default_home

WEBVIEW2_DOWNLOAD = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"  # Microsoft's WebView2 Runtime installer


def serve(folder: Path, extra: dict[str, Path] | None = None) -> tuple[http.server.ThreadingHTTPServer, str]:
    """Serve `folder` on a free port of 127.0.0.1 (this PC only). Returns the server and its address.
    `extra` maps a first path part to another folder, e.g. {"cache": <platform folder>/cache} serves
    `cache/ground/x.png` from there (made pictures too big to hand over through the window's bridge)."""
    extra = {k: Path(v).resolve() for k, v in (extra or {}).items()}

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def translate_path(self, path):
            head, _, rest = path.lstrip("/").partition("/")
            if head in extra:
                root = extra[head]
                target = (root / urllib.parse.unquote(rest.split("?", 1)[0].split("#", 1)[0])).resolve()
                if target == root or root in target.parents:
                    return str(target)
                return ""  # outside the folder: never served (opening "" fails, so the answer is "not found")
            return super().translate_path(path)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(folder)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


class Job:
    """A long task a screen follows: its lines so far, and how it ended."""

    def __init__(self):
        self.id = uuid.uuid4().hex[:8]
        self.state, self.lines, self.message = "running", [], ""
        self.errors: list[str] = []  # a failed build's errors, one per mistake in the mods (play.Starter.modded)
        self.order: list[str] = []   # that build's load order (mod ids)

    def say(self, line: str) -> None:
        self.lines.append(line)

    def view(self, since: int = 0) -> dict:
        out = {"id": self.id, "state": self.state, "message": self.message, "lines": self.lines[since:],
               "count": len(self.lines)}
        return out | {"errors": self.errors} if self.errors else out

    def start(self, work, done: str, plain=(OSError,)) -> dict:
        """Run `work(say)` in the background. The job ends "done" with the message `done`, or "failed" with the
        error: as it is for the `plain` kinds (their messages are written for people), with its type for anything
        else (for a bug report)."""
        def run():
            try:
                work(self.say)
                self.state, self.message = "done", done
            except plain as exc:
                # the errors first: a screen that sees "failed" sees them too
                self.errors, self.order = list(getattr(exc, "errors", [])), list(getattr(exc, "order", []))
                self.state, self.message = "failed", str(exc)
            except Exception as exc:
                self.state, self.message = "failed", f"Something went wrong: {type(exc).__name__}: {exc}"

        threading.Thread(target=run, daemon=True).start()
        return {"job": self.id}


def job_view(jobs: dict, job_id: str, since: int = 0) -> dict:
    """What a screen sees of one of its jobs (`since` skips the lines it already has)."""
    job = jobs.get(job_id)
    return job.view(since) if job else {"id": job_id, "state": "failed", "message": "unknown job", "lines": [],
                                        "count": 0}


def open_window(title: str, folder: Path, page: str, api, width=1180, height=760,
                extra: dict[str, Path] | None = None, setup=None) -> int:
    """Open a window showing `folder/page`, with `api` callable from its JavaScript. Needs pywebview. What the screens
    keep (the Studio's language, say) is stored in the platform folder, so it's still there next time. `setup(window)`
    runs before the window opens, for hooks like on_file_drop. The app's start-up log (rusemod.startlog), when it has
    one, notes each step up to the page's first calls."""
    log = startlog.current()
    try:
        import webview
    except ImportError:
        print("This window needs pywebview. Install it once with:  py -3 -m pip install pywebview")
        return 2
    startlog.mark("pywebview")
    if not web_engine_ok(title):
        return 3
    startlog.mark("engine")
    server, base = serve(folder, extra)
    if log is not None:
        startlog.timed(api, log)  # the page's first calls, each with how long it took
    window = webview.create_window(title, f"{base}/{page}", js_api=api, width=width, height=height,
                                   min_size=(900, 600), background_color="#0a1628")  # the apps' navy, before the page draws
    api._window = window
    if setup is not None:
        setup(window)
    if log is not None:
        for event, step in (("shown", "shown"), ("before_load", "page"), ("loaded", "loaded")):
            try:
                handlers = getattr(window.events, event, None)  # pywebview's window events (6.x has all three)
                if handlers is not None:
                    handlers += _step(log, step)
            except Exception:  # noqa: BLE001  (another pywebview: that step isn't logged, the window opens anyway)
                pass
        log.mark("window")
    try:
        webview.start(private_mode=False, storage_path=str(default_home() / "webview"))
    finally:
        startlog.mark("closed")
        server.shutdown()
        server.server_close()
    return 0


def _step(log, step: str):
    """A window event's handler that marks `step` in the start-up log (no parameters: pywebview then passes none)."""
    return lambda: log.mark(step)


def pick_folder(window) -> str | None:
    """A "choose a folder" dialog in `window`; the folder, or None if the player cancels."""
    import webview
    kind = webview.FileDialog.FOLDER if hasattr(webview, "FileDialog") else webview.FOLDER_DIALOG
    chosen = window.create_file_dialog(kind)
    return chosen[0] if chosen else None


def pick_file(window, file_types=()) -> str | None:
    """A "choose a file" dialog in `window`; the file, or None if the player cancels. `file_types` are pywebview's
    filters, like ("Mods (*.zip;*.toml)",)."""
    import webview
    kind = webview.FileDialog.OPEN if hasattr(webview, "FileDialog") else webview.OPEN_DIALOG
    chosen = window.create_file_dialog(kind, file_types=tuple(file_types))
    return chosen[0] if chosen else None


def pick_save(window, filename: str, file_types=()) -> str | None:
    """A "save as" dialog in `window` suggesting `filename`; the path chosen, or None if the person cancels."""
    import webview
    kind = webview.FileDialog.SAVE if hasattr(webview, "FileDialog") else webview.SAVE_DIALOG
    chosen = window.create_file_dialog(kind, save_filename=filename, file_types=tuple(file_types))
    if isinstance(chosen, (list, tuple)):
        chosen = chosen[0] if chosen else None
    return str(chosen) if chosen else None


def on_file_drop(window, handler) -> None:
    """Call `handler(paths)` with the full paths of files or folders dropped anywhere on the window's page. A page's
    own JavaScript never sees a dropped file's path; pywebview's Windows side does, and hands it to a drop handler
    registered from Python (`pywebviewFullPath`). The page still has to allow the drop (`dragover` with
    preventDefault) and is told what happened by `handler` itself (`window.evaluate_js`)."""
    def attach():
        def dropped(event):
            files = (event.get("dataTransfer") or {}).get("files") or []
            paths = [f["pywebviewFullPath"] for f in files if isinstance(f, dict) and f.get("pywebviewFullPath")]
            if paths:
                handler(paths)
        window.dom.document.events.drop += dropped

    window.events.loaded += attach


def web_engine_ok(title: str) -> bool:
    """On Windows the screens need Microsoft's WebView2 (built into Windows 11, on most Windows 10 PCs). Without it
    the window would fall back to Internet Explorer and show nothing useful, so say so and offer the download."""
    if sys.platform != "win32":
        return True
    try:
        from webview.platforms import winforms
        if winforms.renderer == "edgechromium":
            return True
    except Exception as exc:  # the window library itself is broken: let pywebview report it when it starts
        print(f"Couldn't check the web engine: {type(exc).__name__}: {exc}")
        return True
    import ctypes
    answer = ctypes.windll.user32.MessageBoxW(
        None, "This app needs Microsoft Edge WebView2 Runtime, which this PC doesn't have yet. It's free and small, "
              "from Microsoft.\n\nOpen the download now?", title, 0x04 | 0x30)  # Yes/No, warning icon
    if answer == 6:  # Yes
        os.startfile(WEBVIEW2_DOWNLOAD)
    return False


def webview2_loader() -> str:
    """Where WebView2Loader.dll comes from, the way Windows looks for it when the window opens: next to the program,
    then the search path (pywebview adds its own folder). Raises if it isn't there or doesn't load."""
    import ctypes
    folders = [Path(sys.argv[0]).resolve().parent] + [Path(p) for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    for folder in folders:
        dll = folder / "WebView2Loader.dll"
        if dll.is_file():
            ctypes.WinDLL(str(dll))
            return f"WebView2Loader.dll loads from {dll}"
    raise FileNotFoundError("WebView2Loader.dll isn't next to the program or on the search path")


def log_to_file(app: str) -> Path:
    """The installed apps have no console: send what they print to `<platform folder>/logs/<app>.log` instead, for
    bug reports. The log starts over when it passes 1 MB."""
    folder = default_home() / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    log = folder / f"{app}.log"
    if log.is_file() and log.stat().st_size > 1_000_000:
        log.replace(log.with_suffix(".old.log"))
    stream = open(log, "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = stream
    return log


def self_test(report: str, folder: Path, files: list[str], calls: list[tuple[str, object]], window=True) -> int:
    """Check an installed app is complete, without opening a window (the build runs this on every app it makes):
    its screens and data files are there and served, its back end answers, and on Windows the window library and
    its .NET and WebView2 parts load. Writes one line per check to `report`; returns 0 when all pass."""
    lines, failed = [], 0

    def check(name: str, fn) -> None:
        nonlocal failed
        try:
            detail = fn()
            lines.append(f"ok    {name}" + (f": {detail}" if detail not in (None, "") else ""))
        except Exception as exc:
            failed += 1
            lines.append(f"FAIL  {name}: {type(exc).__name__}: {exc}")

    for f in files:
        check(f"file {f}", lambda f=f: f"{(folder / f).stat().st_size} bytes")

    def served():
        server, base = serve(folder)
        try:
            with urllib.request.urlopen(f"{base}/index.html", timeout=10) as r:
                return f"{len(r.read())} bytes"
        finally:
            server.shutdown()
            server.server_close()

    check("screens served on this PC", served)
    for name, fn in calls:
        check(name, fn)

    def window_library():
        import webview
        try:
            from webview._version import __version__ as version
        except ImportError:
            version = "?"
        if sys.platform != "win32":
            return f"{webview.__name__} {version}; not Windows, nothing more to check"
        from webview.platforms import edgechromium, winforms  # the .NET and WebView2 parts
        return (f"{webview.__name__} {version}, {edgechromium.__name__} loads, {webview2_loader()}; "
                f"web engine on this PC: {winforms.renderer}")

    if window:
        check("window library", window_library)
    lines.append(f"{'PASSED' if not failed else f'FAILED: {failed}'}")
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if failed else 0
