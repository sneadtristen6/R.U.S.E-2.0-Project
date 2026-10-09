"""The apps' pages in the player's own web browser, for a PC whose app window can't show them (issue #21).

The window (pywebview) draws the pages with Microsoft's WebView2, through .NET. Under Wine (Linux and the Steam Deck
through Steam's Proton) .NET is Wine Mono and WebView2 doesn't start, so the window stays an empty navy rectangle; a
Windows PC can lack WebView2, or have a copy that doesn't start. The pages need neither: they are served on this PC
already (webui.serve), and everything they ask the app goes through one object, `window.pywebview.api`. Here that
object comes from a small script the server adds to each page (`bridge_js`): each call a request to this program,
answered with the method's result or its error, as the window answers them. What else the window gave the apps:

- file dialogs: Windows' own here (comdlg32's, and the shell's folder picker), which Wine has too;
- a dropped file's path (the Launcher adds a mod dropped on it): a browser hands a page the file, never its path, so
  the script sends the file itself, saved in a folder of its own and handed on as a path, then deleted. A dropped
  folder can't be sent: the page is told ("folder-dropped") and says so;
- the program's life: a small box says the app is open in the web browser and gives the page's address (copied, for a
  browser that didn't open by itself); closing the box closes the app.

Only this PC can reach the server (127.0.0.1), and only through this start's random key: every address starts with
it, so another web page can't guess its way to the app. Requests that come from another site are refused as well:
the Host and Origin are checked, and a call needs a JSON or file body, which another site's page can't send here
without asking first (and it is never answered)."""
from __future__ import annotations

import http.server
import json
import re
import secrets
import shutil
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

BRIDGE_FILE = "__ruse_bridge.js"
API_PATH = "__api/"
DROP_PATH = "__drop"

# Content types by file ending: Windows' own list can call .js "text/plain", and a browser won't run a module (the
# Studio's maps.js) sent as that.
TYPES = {".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8",
         ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".json": "application/json", ".txt": "text/plain; charset=utf-8",
         ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".webp": "image/webp", ".gif": "image/gif", ".ico": "image/x-icon", ".glb": "model/gltf-binary",
         ".gltf": "model/gltf+json", ".bin": "application/octet-stream", ".wasm": "application/wasm",
         ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".wav": "audio/wav", ".ogg": "audio/ogg",
         ".mp3": "audio/mpeg", ".flac": "audio/flac"}

# The box's words when the app gives none (each app's words.toml has them in all ten languages: browser_open,
# browser_closed, browser_no_engine)
ENGLISH = {
    "browser_open": "{app} is open in your web browser, because its own window can't open on this PC.\n\n"
                    "If no page opened, paste this address into your browser (it's already copied):\n{address}\n\n"
                    "Keep this box open while you use {app}.\n"
                    "OK: open the page again.   Cancel: close {app}.",
    "browser_closed": "{app} is closed. Start it again to carry on.",
    "browser_no_engine": "{app}'s own window needs Microsoft Edge WebView2 Runtime, which this PC doesn't have yet. "
                         "It's free and small, from Microsoft.\n\n"
                         "Yes: open the download page (then start {app} again).\n"
                         "No: use {app} in your web browser now.\n"
                         "Cancel: close {app}.",
}


def under_wine() -> bool:
    """Whether this Windows program runs under Wine (on Linux or macOS; Steam's Proton is Wine): Wine's ntdll has
    functions of its own that Windows' doesn't."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        return hasattr(ctypes.WinDLL("ntdll"), "wine_get_version")
    except Exception:  # noqa: BLE001  (can't tell: take it for Windows; a window that fails still falls back)
        return False


class BrowserWindow:
    """What the apps use of pywebview's window, in the browser: `evaluate_js` (the scripts are run by the page after
    the request that asked for them: a dropped file's), the drop handler (webui.on_file_drop) and the file dialogs."""

    def __init__(self):
        self._lock = threading.Lock()
        self._scripts: list[str] = []
        self.drop_handler = None

    def evaluate_js(self, script: str) -> None:
        with self._lock:
            self._scripts.append(script)

    def take_scripts(self) -> list[str]:
        with self._lock:
            out, self._scripts = self._scripts, []
        return out

    def pick_folder(self) -> str | None:
        return folder_dialog()

    def pick_file(self, file_types=()) -> str | None:
        return file_dialog(file_types)

    def pick_save(self, filename: str, file_types=()) -> str | None:
        return file_dialog(file_types, filename=filename, save=True)


def texts(words, lang: str, app: str) -> dict:
    """The browser mode's words in `lang` from an app's `words(lang)` (English where it has none), with {app} filled."""
    try:
        have = words(lang) if words is not None else {}
    except Exception:  # noqa: BLE001  (words that can't be read: English)
        have = {}
    return {key: (have.get(key) or text).replace("{app}", app) for key, text in ENGLISH.items()}


def page_language(api) -> str:
    """The language the player picked in the app (kept in settings.json), else the one it suggests, else English."""
    for ask in (lambda: api.prefs().get("lang"), lambda: api.language_choice().get("suggested")):
        try:
            lang = ask()
        except Exception:  # noqa: BLE001  (an API without it, or its files unreadable: the next guess)
            continue
        if lang:
            return lang
    return "us"


def bridge_js(names: list[str], drop: bool, closed: str) -> str:
    """The script the server adds to each page: `window.pywebview.api` with `names`, ready when the page has loaded
    (as the window makes it: "pywebviewready"); a dropped file sent to the app when `drop`; and `closed` shown over
    the page when the app has been closed."""
    return BRIDGE.replace("%NAMES%", json.dumps(names)).replace("%DROP%", "true" if drop else "false") \
        .replace("%CLOSED%", json.dumps(closed))


BRIDGE = r"""// RUSE apps in a web browser (rusemod.browsermode): window.pywebview.api as the app's own window gives it, each
// call a request to the app on this PC. Made for this start of the app only.
"use strict";
(function () {
  const base = location.pathname.slice(0, location.pathname.indexOf("/", 1) + 1);  // "/<this start's key>/"
  const names = %NAMES%;
  const closedText = %CLOSED%;
  let closed = false;

  function showClosed() {
    if (closed || !document.body) return;
    closed = true;
    const box = document.createElement("div");
    box.textContent = closedText;
    box.style.cssText = "position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;" +
      "justify-content:center;padding:24px;background:rgba(10,22,40,.94);color:#fff;" +
      "font:600 18px/1.5 system-ui,sans-serif;text-align:center";
    document.body.appendChild(box);
  }

  async function call(name, args) {
    let res;
    try {
      res = await fetch(base + "__api/" + name, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(args) });
    } catch (err) {
      showClosed();
      throw new Error(closedText);
    }
    const out = await res.json();
    if (out.error) {
      const err = new Error(out.error.message);
      err.name = out.error.name;
      err.stack = out.error.stack;
      throw err;
    }
    return out.value;
  }

  const api = {};
  names.forEach((name) => { api[name] = function () { return call(name, Array.prototype.slice.call(arguments)); }; });
  window.addEventListener("load", () => {
    window.pywebview = { api: api, browser: true };
    window.dispatchEvent(new CustomEvent("pywebviewready"));
  });

  async function send(files) {
    for (const file of files) {
      let out;
      try {
        const res = await fetch(base + "__drop?name=" + encodeURIComponent(file.name), {
          method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: file });
        out = await res.json();
      } catch (err) {
        showClosed();
        return;
      }
      (out.scripts || []).forEach((script) => {
        try { (new Function(script))(); } catch (err) { console.error(err); }
      });
    }
  }

  // a file dropped anywhere: never opened by the browser in the app's place; sent to the app when it takes drops
  window.addEventListener("dragover", (e) => { e.preventDefault(); });
  window.addEventListener("drop", (e) => {
    e.preventDefault();
    if (!%DROP% || !e.dataTransfer) return;
    const files = [];
    let folder = false;
    Array.from(e.dataTransfer.items || []).forEach((item) => {
      if (item.kind !== "file") return;
      const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null;
      if (entry && entry.isDirectory) { folder = true; return; }
      const file = item.getAsFile();
      if (file) files.push(file);
    });
    // after the page's own drop handler (its "Adding the mod…" would cover the folder's message)
    if (folder) setTimeout(() => window.dispatchEvent(new CustomEvent("folder-dropped")), 0);
    send(files);
  });
})();
"""


def with_bridge(html: bytes) -> bytes:
    """A page with the bridge's script first in its head, before the page's own scripts."""
    tag = f'<script src="{BRIDGE_FILE}"></script>'.encode()
    m = re.search(rb"<head\b[^>]*>", html, re.I)
    return html[:m.end()] + tag + html[m.end():] if m else tag + html


def safe_name(name: str) -> str:
    """A dropped file's name as a file name of its own: no folders, nothing Windows refuses."""
    name = re.split(r"[\\/]", name or "")[-1]
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "dropped"


def serve(folder: Path, extra: dict[str, Path] | None, page_side, window: BrowserWindow, closed: str = "",
          port: int = 0) -> tuple[http.server.ThreadingHTTPServer, str, str]:
    """Serve `folder` (and `extra`, as webui.serve) on 127.0.0.1 under a new random key, with `page_side`'s public
    methods callable by the pages. Returns (the server, its address, the key): a page is at <address>/<key>/<page>."""
    folder = Path(folder).resolve()
    extra = {k: Path(v).resolve() for k, v in (extra or {}).items()}
    key = secrets.token_hex(16)
    names = sorted(n for n in dir(type(page_side)) if not n.startswith("_") and callable(getattr(page_side, n, None)))
    allowed: dict[str, set] = {"hosts": set(), "origins": set()}

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, code: int, body: bytes, kind: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, value, code: int = 200) -> None:
            self._send(code, json.dumps(value).encode(), "application/json")

        def _inside(self) -> str | None:
            """The address after this start's key, for a request from this PC's pages; None for anything else."""
            if self.headers.get("Host", "") not in allowed["hosts"]:
                return None
            origin = self.headers.get("Origin")
            if origin is not None and origin not in allowed["origins"]:
                return None
            path = urllib.parse.urlsplit(self.path).path
            prefix = f"/{key}/"
            return urllib.parse.unquote(path[len(prefix):]) if path.startswith(prefix) else None

        def _file(self, rest: str) -> Path | None:
            head, _, tail = rest.partition("/")
            root, rel = (extra[head], tail) if head in extra else (folder, rest)
            target = (root / rel).resolve()
            return target if (target == root or root in target.parents) and target.is_file() else None

        def do_GET(self):
            rest = self._inside()
            if rest is None:
                return self._send(404, b"not found", TYPES[".txt"])
            if rest == BRIDGE_FILE:
                js = bridge_js(names, window.drop_handler is not None, closed)
                return self._send(200, js.encode(), TYPES[".js"])
            if rest == "" or rest.endswith("/"):
                rest += "index.html"
            target = self._file(rest)
            if target is None:
                return self._send(404, b"not found", TYPES[".txt"])
            kind = TYPES.get(target.suffix.lower(), "application/octet-stream")
            if target.suffix.lower() in (".html", ".htm"):
                return self._send(200, with_bridge(target.read_bytes()), kind)
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(target.stat().st_size))
            self.end_headers()
            with open(target, "rb") as f:
                shutil.copyfileobj(f, self.wfile)

        def do_POST(self):
            rest = self._inside()
            kind = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
            length = int(self.headers.get("Content-Length") or 0)
            if rest is not None and rest.startswith(API_PATH) and kind == "application/json":
                return self._call(rest[len(API_PATH):], self.rfile.read(length) if length else b"[]")
            if rest == DROP_PATH and kind == "application/octet-stream" and window.drop_handler is not None:
                query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                return self._drop(safe_name((query.get("name") or [""])[0]), length)
            # refused: what was sent is read first (up to 1 MB), so Windows doesn't cut the answer off (WinError 10053
            # in the tests, 2026-10-09); a bigger body is left and the connection closed
            if 0 < length <= 1 << 20:
                self.rfile.read(length)
            else:
                self.close_connection = True
            self._send(404, b"not found", TYPES[".txt"])

        def _call(self, name: str, body: bytes) -> None:
            if name not in names:
                return self._json({"error": {"message": f"no call {name!r}", "name": "AttributeError", "stack": ""}},
                                  404)
            try:
                args = json.loads(body or b"[]")
                value = getattr(page_side, name)(*(args if isinstance(args, list) else [args]))
                out = json.dumps({"value": value}).encode()
            except Exception as exc:  # noqa: BLE001  (the page gets the error, as the window hands it over)
                stack = traceback.format_exc()
                print(stack, end="")  # the app's log, as the window logs it
                out = json.dumps({"error": {"message": str(exc), "name": type(exc).__name__, "stack": stack}}).encode()
            self._send(200, out, "application/json")

        def _drop(self, name: str, length: int) -> None:
            if name.lower() == "mod.toml":
                # a mod.toml stands for its folder (library.Library.add): sent alone, it would be a mod with nothing
                # in it, put in place of the library's whole copy. The page says what a dropped folder gets instead
                # (the 0.9.8.2 review)
                if length <= 1 << 20:
                    self.rfile.read(length)
                else:
                    self.close_connection = True
                window.evaluate_js('window.dispatchEvent(new CustomEvent("folder-dropped"))')
                return self._json({"scripts": window.take_scripts()})
            work = Path(tempfile.mkdtemp(prefix="ruse-drop-"))
            try:
                path = work / name
                left = length
                with open(path, "wb") as f:
                    while left > 0:
                        chunk = self.rfile.read(min(left, 1 << 20))
                        if not chunk:
                            break
                        f.write(chunk)
                        left -= len(chunk)
                if left == 0:
                    window.drop_handler([str(path)])
            except Exception:  # noqa: BLE001  (the handler tells the page itself; anything else goes to the log)
                print(traceback.format_exc(), end="")
            finally:
                shutil.rmtree(work, ignore_errors=True)
            self._json({"scripts": window.take_scripts()})

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    port = server.server_address[1]
    allowed["hosts"] = {f"127.0.0.1:{port}", f"localhost:{port}"}
    allowed["origins"] = {f"http://{host}" for host in allowed["hosts"]}
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{port}", key


def open_in_browser(title: str, folder: Path, page: str, page_side, window: BrowserWindow,
                    extra: dict[str, Path] | None, words: dict) -> int:
    """Serve the pages, open them in the player's web browser, and keep the app running until the player closes its
    box (`keep_open`). `words`: texts(...)."""
    server, base, key = serve(folder, extra, page_side, window, words["browser_closed"])
    try:
        keep_open(title, f"{base}/{key}/{page}", words)
    finally:
        server.shutdown()
        server.server_close()
    return 0


def keep_open(title: str, address: str, words: dict) -> None:
    """Open `address` in the web browser and show the box that keeps the app running: OK opens the page again,
    Cancel (or closing the box) closes the app. The address is on the clipboard too, for a browser that didn't open."""
    copy_text(address)
    show_page(address)
    if sys.platform != "win32":  # from source, outside Windows: no box; the console says where the page is
        print(f"{title} is at {address} (Ctrl+C closes it)")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            return
    text = words["browser_open"].replace("{address}", address)
    while message_box(text, title, 0x01 | 0x40 | 0x10000) == 1:  # OK/Cancel, information, to the front; OK = 1
        show_page(address)


def show_page(address: str) -> None:
    try:
        webbrowser.open(address)
    except Exception as exc:  # noqa: BLE001  (no browser to open: the box gives the address)
        print(f"Couldn't open the web browser: {type(exc).__name__}: {exc}")


# --- Windows' own pieces, through ctypes (each library loaded apart, so other code's argtypes are left alone) ---

def message_box(text: str, title: str, flags: int) -> int:
    import ctypes
    user32 = ctypes.WinDLL("user32")
    user32.MessageBoxW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    return user32.MessageBoxW(None, text, title, flags)


def copy_text(text: str) -> bool:
    """Put `text` on the clipboard; False when it couldn't (another program holding the clipboard, say)."""
    if sys.platform != "win32":
        return False
    import ctypes
    user32, kernel32 = ctypes.WinDLL("user32"), ctypes.WinDLL("kernel32")
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    data = text.encode("utf-16-le") + b"\0\0"
    for _ in range(10):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return False
    try:
        user32.EmptyClipboard()
        memory = kernel32.GlobalAlloc(0x0002, len(data))  # GMEM_MOVEABLE
        if not memory:
            return False
        pointer = kernel32.GlobalLock(memory)
        ctypes.memmove(pointer, data, len(data))
        kernel32.GlobalUnlock(memory)
        if not user32.SetClipboardData(13, memory):  # CF_UNICODETEXT; the clipboard owns the memory once it's set
            kernel32.GlobalFree(memory)
            return False
        return True
    finally:
        user32.CloseClipboard()


def filters(file_types) -> list[tuple[str, str]]:
    """pywebview's file types ("Mods (*.zip;*.toml)") as a dialog's filters: (what it says, its patterns)."""
    out = []
    for kind in file_types or ():
        m = re.search(r"\(([^()]*)\)\s*$", kind)
        out.append((kind, m.group(1).strip() if m else "*.*"))
    return out or [("*.*", "*.*")]


def _com_thread():
    """Ready this thread for a dialog (COM, single-threaded, as the shell's dialogs want). Returns the call that
    undoes it, or None when it had been made ready another way."""
    import ctypes
    ole32 = ctypes.WinDLL("ole32")
    ole32.OleInitialize.argtypes = [ctypes.c_void_p]
    result = ole32.OleInitialize(None) & 0xFFFFFFFF
    return ole32.OleUninitialize if result in (0, 1) else None  # S_OK, S_FALSE


def _to_front_soon(seconds: float = 3.0) -> None:
    """Bring this program's next dialog in front of the web browser: the player clicked in the browser, and Windows
    otherwise leaves a background program's dialog behind it (only blinking in the taskbar)."""
    import ctypes
    from ctypes import wintypes
    user32, kernel32 = ctypes.WinDLL("user32"), ctypes.WinDLL("kernel32")
    me = kernel32.GetCurrentProcessId()
    enum_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [enum_proc, wintypes.LPARAM]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]

    def dialogs() -> list:
        found = []

        def each(hwnd, _):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == me and user32.IsWindowVisible(hwnd):
                name = ctypes.create_unicode_buffer(64)
                user32.GetClassNameW(hwnd, name, 64)
                if name.value == "#32770":  # a dialog
                    found.append(hwnd)
            return True
        user32.EnumWindows(enum_proc(each), 0)
        return found

    seen = set(dialogs())  # the app's box, open the whole time: not the one to bring forward

    def watch():
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            for hwnd in dialogs():
                if hwnd in seen:
                    continue
                seen.add(hwnd)
                front = user32.GetForegroundWindow()
                theirs = user32.GetWindowThreadProcessId(front, None) if front else 0
                mine = kernel32.GetCurrentThreadId()
                if theirs and theirs != mine:
                    user32.AttachThreadInput(mine, theirs, True)
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                if theirs and theirs != mine:
                    user32.AttachThreadInput(mine, theirs, False)
                return
            time.sleep(0.05)

    threading.Thread(target=watch, daemon=True).start()


def file_dialog(file_types=(), filename: str = "", save: bool = False) -> str | None:
    """Windows' "open" or "save as" dialog (comdlg32, which Wine has too); the path chosen, or None."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [("lStructSize", wintypes.DWORD), ("hwndOwner", wintypes.HWND), ("hInstance", wintypes.HINSTANCE),
                    ("lpstrFilter", ctypes.c_void_p), ("lpstrCustomFilter", ctypes.c_void_p),
                    ("nMaxCustFilter", wintypes.DWORD), ("nFilterIndex", wintypes.DWORD),
                    ("lpstrFile", ctypes.c_void_p), ("nMaxFile", wintypes.DWORD),
                    ("lpstrFileTitle", ctypes.c_void_p), ("nMaxFileTitle", wintypes.DWORD),
                    ("lpstrInitialDir", ctypes.c_void_p), ("lpstrTitle", ctypes.c_void_p),
                    ("Flags", wintypes.DWORD), ("nFileOffset", wintypes.WORD), ("nFileExtension", wintypes.WORD),
                    ("lpstrDefExt", ctypes.c_void_p), ("lCustData", wintypes.LPARAM), ("lpfnHook", ctypes.c_void_p),
                    ("lpTemplateName", ctypes.c_void_p), ("pvReserved", ctypes.c_void_p),
                    ("dwReserved", wintypes.DWORD), ("FlagsEx", wintypes.DWORD)]

    kinds = filters(file_types)
    spec = "".join(f"{label}\0{patterns}\0" for label, patterns in kinds) + "\0"
    spec_buffer = ctypes.create_unicode_buffer(len(spec) + 1)
    spec_buffer[:len(spec)] = spec  # the pairs are kept apart by NULs, so not a plain string
    name = ctypes.create_unicode_buffer(filename or "", 32768)
    ext = Path(filename).suffix.lstrip(".") if filename else ""
    if not ext:
        first = kinds[0][1].split(";")[0].strip()
        ext = first[2:] if first.startswith("*.") and "*" not in first[2:] else ""
    ext_buffer = ctypes.create_unicode_buffer(ext)
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.lpstrFilter = ctypes.addressof(spec_buffer)
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.addressof(name)
    ofn.nMaxFile = len(name)
    ofn.lpstrDefExt = ctypes.addressof(ext_buffer) if ext else None
    # OFN_EXPLORER | OFN_NOCHANGEDIR | OFN_PATHMUSTEXIST, then OFN_OVERWRITEPROMPT (save) or OFN_FILEMUSTEXIST (open)
    ofn.Flags = 0x00080000 | 0x00000008 | 0x00000800 | (0x00000002 if save else 0x00001000)
    comdlg32 = ctypes.WinDLL("comdlg32")
    ask = comdlg32.GetSaveFileNameW if save else comdlg32.GetOpenFileNameW
    ask.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
    undo = _com_thread()
    try:
        _to_front_soon()
        chosen = ask(ctypes.byref(ofn))
    finally:
        if undo is not None:
            undo()
    return name.value if chosen and name.value else None


def folder_dialog() -> str | None:
    """The shell's "choose a folder" dialog (which Wine has too); the folder, or None."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    class BROWSEINFOW(ctypes.Structure):
        _fields_ = [("hwndOwner", wintypes.HWND), ("pidlRoot", ctypes.c_void_p), ("pszDisplayName", ctypes.c_void_p),
                    ("lpszTitle", ctypes.c_void_p), ("ulFlags", wintypes.UINT), ("lpfn", ctypes.c_void_p),
                    ("lParam", wintypes.LPARAM), ("iImage", ctypes.c_int)]

    shell32, ole32 = ctypes.WinDLL("shell32"), ctypes.WinDLL("ole32")
    shell32.SHBrowseForFolderW.argtypes = [ctypes.POINTER(BROWSEINFOW)]
    shell32.SHBrowseForFolderW.restype = ctypes.c_void_p
    shell32.SHGetPathFromIDListW.argtypes = [ctypes.c_void_p, wintypes.LPWSTR]
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    shown = ctypes.create_unicode_buffer(260)
    info = BROWSEINFOW()
    info.pszDisplayName = ctypes.addressof(shown)
    info.ulFlags = 0x0001 | 0x0040  # BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE (resizable, with "Make new folder")
    undo = _com_thread()
    try:
        _to_front_soon()
        chosen = shell32.SHBrowseForFolderW(ctypes.byref(info))
        if not chosen:
            return None
        path = ctypes.create_unicode_buffer(32768)
        ok = shell32.SHGetPathFromIDListW(chosen, path)
        ole32.CoTaskMemFree(chosen)
        return path.value if ok and path.value else None
    finally:
        if undo is not None:
            undo()


def check(folder: Path, page: str = "index.html") -> str:
    """The build's self-test: `folder`'s page served the browser's way, with its bridge script, and a call answered.
    Returns what was seen; raises if anything is wrong."""
    class Probe:
        def echo(self, *args):
            return list(args)

    server, base, key = serve(folder, None, Probe(), BrowserWindow())
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # this PC: never through a proxy
    try:
        with opener.open(f"{base}/{key}/{page}", timeout=10) as r:
            html = r.read()
        if f'<script src="{BRIDGE_FILE}"></script>'.encode() not in html:
            raise RuntimeError(f"{page} came without the bridge script")
        with opener.open(f"{base}/{key}/{BRIDGE_FILE}", timeout=10) as r:
            if b'"echo"' not in r.read():
                raise RuntimeError("the bridge script doesn't list the calls")
        call = urllib.request.Request(f"{base}/{key}/{API_PATH}echo", data=json.dumps(["é", 2]).encode(),
                                      headers={"Content-Type": "application/json"})
        with opener.open(call, timeout=10) as r:
            answer = json.loads(r.read())
        if answer != {"value": ["é", 2]}:
            raise RuntimeError(f"a call came back as {answer!r}")
        return f"{page} ({len(html)} bytes) with its bridge, a call answered"
    finally:
        server.shutdown()
        server.server_close()
