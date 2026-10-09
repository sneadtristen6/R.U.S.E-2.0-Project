"""The apps' pages in the player's web browser (rusemod.browsermode, issue #21): served under a random key with the
bridge script, calls answered as the window answers them, files dropped and handed on, other sites refused; and
webui.open_window going to the browser where the window can't show the pages."""
from __future__ import annotations

import json
import logging
import socket
import sys
import tempfile
import tomllib
import types
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rusemod import browsermode, webui  # noqa: E402

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # this PC only, never a proxy


class Api:
    def add(self, a, b):
        return a + b

    def boom(self):
        raise ValueError("it broke")

    def _secret(self):
        return "private"


def get(url: str, data: bytes | None = None, kind: str | None = None) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, data=data, headers={"Content-Type": kind} if kind else {})
    try:
        with OPENER.open(req, timeout=10) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("Content-Type", "")


def raw(port: int, text: str) -> str:
    """A request written by hand (another Host, another Origin, a path a browser would tidy away)."""
    with socket.create_connection(("127.0.0.1", port), timeout=10) as s:
        s.sendall(text.encode())
        out = b""
        while chunk := s.recv(65536):
            out += chunk
    return out.decode("utf-8", "replace")


class Served(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ui = self.tmp / "ui"
        (self.ui / "sub").mkdir(parents=True)
        (self.ui / "index.html").write_text("<!doctype html><html><head><title>x</title></head><body>"
                                            "<script src=\"app.js\"></script></body></html>", encoding="utf-8")
        (self.ui / "app.js").write_text("console.log(1);", encoding="utf-8")
        (self.ui / "sub" / "x.png").write_bytes(b"\x89PNG")
        (self.tmp / "secret.txt").write_text("not for pages", encoding="utf-8")
        self.cache = self.tmp / "cache"
        self.cache.mkdir()
        (self.cache / "a.glb").write_bytes(b"glTF")
        self.window = browsermode.BrowserWindow()
        self.server, self.base, self.key = browsermode.serve(self.ui, {"cache": self.cache}, Api(), self.window,
                                                             "Closed!")
        self.port = self.server.server_address[1]
        self.at = f"{self.base}/{self.key}/"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_the_page_comes_with_the_bridge_first_in_its_head(self):
        for url in (self.at + "index.html", self.at):
            code, body, kind = get(url)
            self.assertEqual(code, 200)
            self.assertTrue(kind.startswith("text/html"))
            self.assertIn(b'<head><script src="__ruse_bridge.js"></script><title>', body)

    def test_files_and_the_extra_folder_with_types_a_browser_runs(self):
        self.assertEqual(get(self.at + "app.js")[2], "text/javascript; charset=utf-8")
        self.assertEqual(get(self.at + "sub/x.png")[:2], (200, b"\x89PNG"))
        self.assertEqual(get(self.at + "cache/a.glb"), (200, b"glTF", "model/gltf-binary"))

    def test_nothing_without_this_starts_key_or_outside_the_folders(self):
        self.assertEqual(get(f"{self.base}/index.html")[0], 404)
        self.assertEqual(get(f"{self.base}/{'0' * 32}/index.html")[0], 404)
        for path in ("../secret.txt", "..%2fsecret.txt", "cache/../../secret.txt", "sub/"):
            answer = raw(self.port, f"GET /{self.key}/{path} HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n"
                                    "Connection: close\r\n\r\n")
            self.assertTrue(answer.startswith("HTTP/1.0 404"), (path, answer[:40]))
            self.assertNotIn("not for pages", answer)

    def test_the_bridge_lists_the_public_calls_only(self):
        code, body, kind = get(self.at + "__ruse_bridge.js")
        self.assertEqual((code, kind), (200, "text/javascript; charset=utf-8"))
        js = body.decode()
        self.assertIn('const names = ["add", "boom"];', js)
        self.assertNotIn("_secret", js)
        self.assertIn('const closedText = "Closed!";', js)
        self.assertIn("if (!false || !e.dataTransfer) return;", js)  # no drop handler: drops aren't sent
        self.window.drop_handler = lambda paths: None
        self.assertIn("if (!true || !e.dataTransfer) return;", get(self.at + "__ruse_bridge.js")[1].decode())

    def test_calls_answer_as_the_window_does(self):
        def call(name, args, kind="application/json"):
            code, body, _ = get(self.at + "__api/" + name, json.dumps(args).encode(), kind)
            return code, json.loads(body) if body.startswith(b"{") else body

        self.assertEqual(call("add", [2, 3]), (200, {"value": 5}))
        self.assertEqual(call("add", ["é", "!"]), (200, {"value": "é!"}))
        code, out = call("boom", [])
        self.assertEqual((code, out["error"]["name"], out["error"]["message"]), (200, "ValueError", "it broke"))
        self.assertIn("Traceback", out["error"]["stack"])
        self.assertEqual(call("_secret", [])[0], 404)
        self.assertEqual(call("__class__", [])[0], 404)
        self.assertEqual(call("add", [2, 3], kind="text/plain")[0], 404)  # a form of another site could send that

    def test_other_sites_are_refused(self):
        body = "[2, 3]"
        for headers in (f"Host: evil.example:{self.port}\r\n",
                        f"Host: 127.0.0.1:{self.port}\r\nOrigin: http://evil.example\r\n"):
            answer = raw(self.port, f"POST /{self.key}/__api/add HTTP/1.1\r\n{headers}Content-Type: application/json"
                                    f"\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n{body}")
            self.assertTrue(answer.startswith("HTTP/1.0 404"), answer[:40])
        same = raw(self.port, f"POST /{self.key}/__api/add HTTP/1.1\r\nHost: localhost:{self.port}\r\nOrigin: "
                              f"http://localhost:{self.port}\r\nContent-Type: application/json\r\nContent-Length: "
                              f"{len(body)}\r\nConnection: close\r\n\r\n{body}")
        self.assertIn('{"value": 5}', same)

    def test_a_dropped_file_reaches_the_handler_as_a_path_then_goes(self):
        seen = []

        def handler(paths):
            path = Path(paths[0])
            seen.append((path.name, path.read_bytes(), path))
            self.window.evaluate_js("window.done = 1")

        self.assertEqual(get(self.at + "__drop?name=a.rusemod", b"x", "application/octet-stream")[0], 404)  # no handler
        self.window.drop_handler = handler
        data = bytes(range(256)) * 5000
        code, body, _ = get(self.at + "__drop?name=..%2F..%2Fmy%20mod%3F.rusemod", data, "application/octet-stream")
        self.assertEqual((code, json.loads(body)), (200, {"scripts": ["window.done = 1"]}))
        name, got, path = seen[0]
        self.assertEqual((name, got), ("my mod_.rusemod", data))
        self.assertFalse(path.exists())
        self.assertFalse(path.parent.exists())
        self.assertEqual(self.window.take_scripts(), [])
        # a mod.toml alone would be an empty mod put in place of the library's copy: the page says use the folder's way
        code, body, _ = get(self.at + "__drop?name=MOD.toml", b"[mod]\nid = 'x'\n", "application/octet-stream")
        self.assertEqual((code, json.loads(body)),
                         (200, {"scripts": ['window.dispatchEvent(new CustomEvent("folder-dropped"))']}))
        self.assertEqual(len(seen), 1)


class Pieces(unittest.TestCase):
    def test_safe_names(self):
        self.assertEqual(browsermode.safe_name("C:\\x\\..\\a.zip"), "a.zip")
        self.assertEqual(browsermode.safe_name('a<b>:"c|?*.rmod'), "a_b___c___.rmod")
        self.assertEqual(browsermode.safe_name(" .. "), "dropped")

    def test_filters_from_pywebviews_file_types(self):
        self.assertEqual(browsermode.filters(("Mods (*.rusemod;*.zip)", "All files (*.*)")),
                         [("Mods (*.rusemod;*.zip)", "*.rusemod;*.zip"), ("All files (*.*)", "*.*")])
        self.assertEqual(browsermode.filters(()), [("*.*", "*.*")])

    def test_the_bridge_goes_in_without_a_head_too(self):
        self.assertEqual(browsermode.with_bridge(b"<p>x</p>"), b'<script src="__ruse_bridge.js"></script><p>x</p>')
        self.assertEqual(browsermode.with_bridge(b"<HEAD lang=x><header>"),
                         b'<HEAD lang=x><script src="__ruse_bridge.js"></script><header>')

    def test_the_language_the_player_picked_first(self):
        api = types.SimpleNamespace(prefs=lambda: {"lang": "fr"}, language_choice=lambda: {"suggested": "ger"})
        self.assertEqual(browsermode.page_language(api), "fr")
        api.prefs = lambda: {}
        self.assertEqual(browsermode.page_language(api), "ger")
        self.assertEqual(browsermode.page_language(object()), "us")

    def test_the_build_self_test_check(self):
        self.assertIn("with its bridge, a call answered", browsermode.check(ROOT / "src" / "ruse_launcher" / "ui"))


class Words(unittest.TestCase):
    def words(self, app):
        return tomllib.loads((ROOT / "src" / app / "words.toml").read_text(encoding="utf-8"))

    def test_both_apps_say_it_in_all_ten_languages(self):
        langs = {"us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"}
        for app in ("ruse_studio", "ruse_launcher"):
            words = self.words(app)
            for key in browsermode.ENGLISH:
                self.assertEqual(set(words[key]), langs, (app, key))
                self.assertEqual(words[key]["us"], browsermode.ENGLISH[key], (app, key))
                for lang, text in words[key].items():
                    self.assertIn("{app}", text, (app, key, lang))
                    if key == "browser_open":
                        self.assertIn("{address}", text, (app, key, lang))
        self.assertEqual(set(self.words("ruse_launcher")["drop_folder_browser"]), langs)

    def test_texts_fill_in_the_app(self):
        from ruse_launcher.api import words
        said = browsermode.texts(words, "fr", "RUSE Launcher")
        self.assertTrue(said["browser_closed"].startswith("RUSE Launcher est fermé"))
        self.assertEqual(browsermode.texts(None, "fr", "X")["browser_closed"], "X is closed. Start it again to carry on.")


class FakeEvent:
    def __iadd__(self, handler):
        return self


def fake_webview(start):
    module = types.ModuleType("webview")

    def create_window(title, url, js_api=None, **kwargs):
        module.window = types.SimpleNamespace(api=js_api, url=url, destroyed=False, events=types.SimpleNamespace(
            shown=FakeEvent(), before_load=FakeEvent(), loaded=FakeEvent()))
        module.window.destroy = lambda: setattr(module.window, "destroyed", True)
        return module.window

    module.create_window, module.start = create_window, start
    return module


class TheWindowOrTheBrowser(unittest.TestCase):
    """webui.open_window: the window where it can show the pages, the browser where it can't."""

    def open(self, webview=None, engine="ok", wine=False, browser=False, choice="quit"):
        went = []

        def in_browser(title, folder, page, page_side, window, extra, words):
            went.append((page_side, window, words))
            return 0

        api = types.SimpleNamespace(prefs=lambda: {"lang": "ger"})
        modules = {"webview": webview} if webview is not None else {"webview": None}
        with mock.patch.dict(sys.modules, modules), \
                mock.patch.object(webui, "web_engine", return_value=engine), \
                mock.patch.object(webui, "no_engine_choice", return_value=choice), \
                mock.patch.object(browsermode, "under_wine", return_value=wine), \
                mock.patch.object(browsermode, "open_in_browser", side_effect=in_browser):
            code = webui.open_window("RUSE Launcher", ROOT / "src" / "ruse_launcher" / "ui", "index.html", api,
                                     words=lambda lang: {"browser_closed": f"{{app}} closed ({lang})"},
                                     browser=browser)
        return code, went, api

    def test_the_window_when_it_works(self):
        code, went, api = self.open(fake_webview(lambda **kw: None))
        self.assertEqual((code, went), (0, []))
        self.assertNotIsInstance(api._window, browsermode.BrowserWindow)

    def test_the_browser_when_asked_or_under_wine(self):
        for kwargs in ({"browser": True, "webview": fake_webview(lambda **kw: None)},
                       {"wine": True, "webview": fake_webview(lambda **kw: None)},
                       {"wine": True}):  # under Wine pywebview isn't even needed
            code, went, api = self.open(**kwargs)
            self.assertEqual((code, len(went)), (0, 1), kwargs)
            self.assertIsInstance(api._window, browsermode.BrowserWindow)
            self.assertEqual(went[0][2]["browser_closed"], "RUSE Launcher closed (ger)")

    def test_without_pywebview_it_still_says_how_to_install_it(self):
        with mock.patch("builtins.print") as out:
            code, went, _ = self.open()  # sys.modules["webview"] = None: the import fails
        self.assertEqual((code, went), (2, []))
        self.assertIn("pip install pywebview", out.call_args[0][0])

    def test_a_broken_window_library_or_one_that_fails_to_start(self):
        code, went, _ = self.open(fake_webview(lambda **kw: None), engine="the window library doesn't load: X")
        self.assertEqual((code, len(went)), (0, 1))

        def raises(**kwargs):
            raise RuntimeError("BadImageFormatException")
        code, went, _ = self.open(fake_webview(raises))
        self.assertEqual((code, len(went)), (0, 1))

    def test_webview2_failing_to_start_closes_the_window_for_the_browser(self):
        module = fake_webview(None)

        def start(**kwargs):  # what pywebview 6.2.1 logs when WebView2 doesn't start (issue #21's log)
            logging.getLogger("pywebview").error("WebView2 initialization failed with exception:\n WebView2Loader.dll")
            for _ in range(200):
                if module.window.destroyed:
                    return
                import time
                time.sleep(0.01)
        module.start = start
        code, went, _ = self.open(module)
        self.assertTrue(module.window.destroyed)
        self.assertEqual((code, len(went)), (0, 1))
        self.assertFalse(any(isinstance(h, webui.EngineWatch) for h in logging.getLogger("pywebview").handlers))

    def test_no_webview2_the_players_pick(self):
        self.assertEqual(self.open(fake_webview(lambda **kw: None), engine="missing", choice="quit")[:2], (3, []))
        self.assertEqual(self.open(fake_webview(lambda **kw: None), engine="missing", choice="download")[:2], (3, []))
        code, went, _ = self.open(fake_webview(lambda **kw: None), engine="missing", choice="browser")
        self.assertEqual((code, len(went)), (0, 1))


class DialogsAndDrops(unittest.TestCase):
    def test_the_apis_dialogs_and_drops_go_the_browsers_way(self):
        window = browsermode.BrowserWindow()
        with mock.patch.object(browsermode, "folder_dialog", return_value="D:/f"), \
                mock.patch.object(browsermode, "file_dialog", side_effect=lambda types=(), filename="", save=False:
                                  f"{'save' if save else 'open'}:{filename}:{','.join(types)}"):
            self.assertEqual(webui.pick_folder(window), "D:/f")
            self.assertEqual(webui.pick_file(window, ("Mods (*.zip)",)), "open::Mods (*.zip)")
            self.assertEqual(webui.pick_save(window, "a.rusemod", ("M (*.rusemod)",)), "save:a.rusemod:M (*.rusemod)")
        handler = object()
        webui.on_file_drop(window, handler)
        self.assertIs(window.drop_handler, handler)


if __name__ == "__main__":
    unittest.main()
