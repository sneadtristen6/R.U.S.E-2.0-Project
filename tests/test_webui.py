"""What a window's page may call (rusemod.webui.page_api): only the API's own public methods, walked and looked up the
way pywebview does it (6.2.1's util.inject_pywebview get_functions and js_bridge_call's lookup, copied below), so a
Path, a dict or a private attribute of the API never reaches the page."""
import inspect
import unittest
from pathlib import Path

from rusemod.webui import page_api


def exposed(obj, base="", out=None, seen=None, depth=6):
    """pywebview's walk: every public attribute; a function is handed over with its arguments (self dropped), anything
    else with a __module__ is walked into; whatever fails on one attribute is skipped (pywebview logs it and goes on).
    `depth` stops it where pywebview has no stop: each Path's .parent is a new object, so on Linux the walk never ends
    on its own (pywebview stops there when Python runs out of depth)."""
    seen = [] if seen is None else seen
    out = {} if out is None else out
    if id(obj) in seen or depth < 0:
        return out
    seen.append(id(obj))
    for name in dir(obj):
        if name.startswith("_"):
            continue
        full = f"{base}.{name}" if base else name
        try:
            attr = getattr(obj, name)
            if inspect.ismethod(attr) or inspect.isfunction(attr):
                out[full] = list(inspect.getfullargspec(attr).args)[1:]
            elif inspect.isclass(attr) or (not callable(attr) and hasattr(attr, "__module__")):
                exposed(attr, full, out, seen, depth - 1)
        except Exception:  # noqa: BLE001 - pywebview logs and goes on
            continue
    return out


def looked_up(obj, dotted):
    """pywebview's lookup on a call: each part with getattr, underscores and all."""
    for part in dotted.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    return obj


class Api:
    KINDS = {"mod": "mods"}
    VERSION = "1.2.3"

    def __init__(self):
        self._home = Path("D:/somewhere")
        self.calls = []

    @property
    def cache_dir(self) -> Path:
        return self._home / "cache"

    def status(self) -> dict:
        """The status."""
        return {"ready": True}

    def units(self, lang: str = "base", kind: str = "all", nation: int = -1) -> list:
        self.calls.append((lang, kind, nation))
        return [lang, kind, nation]

    def _private(self):
        return "secret"


class PageApi(unittest.TestCase):
    def test_the_page_gets_the_api_methods_and_nothing_reached_through_data(self):
        api = Api()
        before = exposed(api)
        self.assertIn("cache_dir.rename", before)      # what pywebview handed over before: a Path's methods, and
        self.assertIn("cache_dir.parent.parent.rmdir", before)  # its parents' (the walk goes on through .parent)
        self.assertEqual(exposed(page_api(api)), {"status": [], "units": ["lang", "kind", "nation"]})

    def test_calls_pass_on_with_the_same_arguments(self):
        api = Api()
        page = page_api(api)
        self.assertEqual(page.units("fr", nation=3), ["fr", "all", 3])
        self.assertEqual(api.calls, [("fr", "all", 3)])
        self.assertEqual(page.status(), {"ready": True})
        self.assertEqual(page.status.__doc__, "The status.")

    def test_nothing_else_can_be_called_by_name(self):
        api = Api()
        for name in ("cache_dir.rename", "_home.rename", "_private", "KINDS.clear"):  # all reachable before
            self.assertIsNotNone(looked_up(api, name), name)
        page = page_api(api)
        for name in ("cache_dir.rename", "cache_dir", "_home.rename", "_home", "_private", "KINDS.clear", "VERSION",
                     "calls.append"):
            self.assertIsNone(looked_up(page, name), name)
        self.assertNotIsInstance(looked_up(page, "status.__self__"), Api)  # the real API stays inside the method


if __name__ == "__main__":
    unittest.main()
