"""Shared pieces of the web-style windows (the launcher and the Studio, PLAN.md ADR 2): serving a window's screens on
this PC only, and background jobs the screens follow."""
from __future__ import annotations

import functools
import http.server
import threading
import uuid
from pathlib import Path


def serve(folder: Path) -> tuple[http.server.ThreadingHTTPServer, str]:
    """Serve `folder` on a free port of 127.0.0.1 (this PC only). Returns the server and its address."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(folder)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


class Job:
    """A long task a screen follows: its lines so far, and how it ended."""

    def __init__(self):
        self.id = uuid.uuid4().hex[:8]
        self.state, self.lines, self.message = "running", [], ""

    def say(self, line: str) -> None:
        self.lines.append(line)

    def view(self, since: int = 0) -> dict:
        return {"id": self.id, "state": self.state, "message": self.message, "lines": self.lines[since:],
                "count": len(self.lines)}


def open_window(title: str, folder: Path, page: str, api, width=1180, height=760) -> int:
    """Open a window showing `folder/page`, with `api` callable from its JavaScript. Needs pywebview."""
    try:
        import webview
    except ImportError:
        print("This window needs pywebview. Install it once with:  py -3 -m pip install pywebview")
        return 2
    server, base = serve(folder)
    window = webview.create_window(title, f"{base}/{page}", js_api=api, width=width, height=height,
                                   min_size=(900, 600), background_color="#15181b")
    api._window = window
    try:
        webview.start()
    finally:
        server.shutdown()
        server.server_close()
    return 0
