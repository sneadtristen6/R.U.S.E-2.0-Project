"""FL-97: every way the Launcher's "New mod set", "Save mod set" and Rename can be refused or fail reaches Bug Watch
with a key that never changes or a place in our code, and with the call it came from in front, so a report says
WHICH refusal it was (players' reports 2026-11-02 to 11-08 said only "LauncherError at call:new_set", 14 of 36).

The Launcher's side: each refusal through the window's own way in (webui.page_api, as the page calls it), and a
failure to write the set file. The page's side (ui/app.js): the refusals it makes before any call (Create pressed with
no mod ticked, a blank name) and the editor opened and used, which it tells Bug Watch itself (api.bugwatch_seen).
No network, no game: a made-up Launcher home.
"""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import bugwatch, webui  # noqa: E402
from ruse_launcher.api import LauncherApi  # noqa: E402

UI = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher" / "ui"
MOD = '[mod]\nid = "{id}"\nname = "{id}"\nversion = "1.0.0"\n'


def app_js() -> str:
    return (UI / "app.js").read_text(encoding="utf-8")


def function(code: str, name: str) -> str:
    start = code.index(f"function {name}(")
    return code[start:code.index("\nfunction ", start + 10)]


class Counted(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TEMP"))
        self.home = Path(self.tmp.name) / "home"
        (self.home / "library" / "tanks").mkdir(parents=True)
        (self.home / "library" / "tanks" / "mod.toml").write_text(MOD.format(id="tanks"), encoding="utf-8")
        self._on = bugwatch.ON
        bugwatch.ON = True
        os.environ.pop("RUSE_NO_BUGWATCH", None)
        bugwatch.turn_on(self.home, "Nick")
        bugwatch._current = bugwatch.Watch(self.home, "launcher", "0.4.8.20", opener=mock.Mock())
        self.api = LauncherApi(home=self.home, game_dir=Path(self.tmp.name) / "nowhere", find=lambda: None)
        self.page = webui.page_api(self.api)

    def tearDown(self):
        bugwatch.ON = self._on
        bugwatch._current = None
        self.tmp.cleanup()

    def day(self) -> dict:
        return bugwatch._current.days[bugwatch._today()]

    def refused(self, call, *args) -> None:
        with self.assertRaises(Exception):
            getattr(self.page, call)(*args)

    def test_every_refusal_of_the_three_calls_says_which_and_from_which_call(self):
        typed = "Nick's secret set"
        self.refused("new_set", "  ", ["tanks"])
        self.refused("new_set", typed, [])
        self.refused("new_set", typed, "tanks")             # not a list
        self.refused("new_set", typed, ["tanks", " "])      # a blank entry
        self.refused("new_set", typed, ["tanks", "tanks"])
        self.refused("new_set", typed, ["not-in-the-library"])
        made = self.page.new_set("Tanks", ["tanks"])["set"]
        self.refused("save_set", made, typed, [])
        self.refused("save_set", made, typed, ["tanks", "tanks"])
        self.refused("save_set", made, typed, ["gone-from-the-library"])
        self.refused("save_set", "vanilla", typed, ["tanks"])
        self.refused("save_set", "deleted-meanwhile", typed, ["tanks"])
        self.refused("rename_set", "deleted-meanwhile", typed)
        self.refused("rename_set", "vanilla", typed)
        self.assertEqual(self.day()["messages"], {
            "new_set:set_no_name": 1, "new_set:set_no_mods": 3, "new_set:set_mod_twice": 1,
            "new_set:set_mod_missing": 1, "save_set:set_no_mods": 1, "save_set:set_mod_twice": 1,
            "save_set:set_mod_missing": 1, "save_set:set_vanilla": 1, "save_set:set_gone": 1,
            "rename_set:set_gone": 1, "rename_set:set_vanilla": 1})
        calls = self.day()["calls"]
        self.assertEqual((calls["new_set"]["n"], calls["new_set"]["failed"]), (7, 6))
        self.assertEqual((calls["save_set"]["n"], calls["save_set"]["failed"]), (5, 5))
        self.assertEqual((calls["rename_set"]["n"], calls["rename_set"]["failed"]), (2, 2))
        sent = str(bugwatch._current.payload(bugwatch._today(), self.day()))
        for private in ("secret", "not-in-the-library", "gone-from-the-library", "deleted-meanwhile"):
            self.assertNotIn(private, sent)

    def test_a_rename_is_its_own_call_and_keeps_the_mods(self):
        made = self.page.new_set("Tanks", ["tanks"])["set"]
        after = self.page.rename_set(made, "Armour")
        renamed = next(s for s in after["sets"] if s["id"] == made)
        self.assertEqual((renamed["name"], renamed["mods"]), ("Armour", ["tanks"]))
        self.assertNotIn("save_set", self.day()["calls"])   # (save_set inside it is not the page's call)
        self.assertEqual(self.day()["calls"]["rename_set"]["n"], 1)

    def test_a_set_file_that_can_t_be_written_says_the_place_in_our_code(self):
        (self.home / "sets").write_text("a file where the folder goes", encoding="utf-8")
        self.refused("new_set", "Tanks", ["tanks"])
        keys = [k for k in self.day()["messages"] if k.startswith("new_set:")]
        self.assertEqual(len(keys), 1)
        self.assertRegex(keys[0], r"^new_set:ruse_launcher\.api:\d+$")
        line = int(keys[0].rsplit(":", 1)[1])
        source = (UI.parent / "api.py").read_text(encoding="utf-8").splitlines()[line - 1]
        self.assertIn("mkdir", source)                       # _write_set: the folder for the sets
        self.assertNotIn("LauncherError", self.day()["calls"]["new_set"]["errors"])

    def test_the_page_counts_its_own_refusals_and_the_editor_opened_and_used(self):
        """What app.js sends through api.bugwatch_seen, as the Launcher counts and sends it."""
        for group, key in (("screens", "set_editor_new"), ("messages", "page:new_set:set_no_mods"),
                           ("messages", "page:new_set:set_no_mods"), ("messages", "page:new_set:set_no_name"),
                           ("screen_used", "set_editor_new"), ("screens", "set_editor_new"),
                           ("messages", "page:new_set:set_library_empty"), ("screens", "set_editor_edit"),
                           ("screen_used", "set_editor_edit"), ("messages", "page:rename_set:set_no_name")):
            self.assertEqual(self.page.bugwatch_seen(group, key), {"ok": True})
        self.assertEqual(self.day()["screens"], {"set_editor_new": {"opened": 2, "used": 1},
                                                 "set_editor_edit": {"opened": 1, "used": 1}})
        self.assertEqual(self.day()["messages"], {"page:new_set:set_no_mods": 2, "page:new_set:set_no_name": 1,
                                                  "page:new_set:set_library_empty": 1,
                                                  "page:rename_set:set_no_name": 1})
        self.assertNotIn("bugwatch_seen", self.day()["calls"])  # (its own calls aren't what it counts)
        sent = bugwatch._current.payload(bugwatch._today(), self.day())
        self.assertEqual(sent["screens"]["set_editor_new"], {"opened": 2, "used": 1})
        self.assertEqual(sent["messages"]["page:new_set:set_no_mods"], 2)
        with self.assertRaises(ValueError):
            self.page.bugwatch_seen("calls", "new_set")       # the page counts screens and messages only

    def test_every_key_the_page_sends_is_one_the_server_takes(self):
        code = app_js()
        keys = set(re.findall(r'seen\("(?:screens|screen_used)", (?:set \? )?"([^"]+)"', code))
        keys |= set(re.findall(r'"(set_editor_(?:new|edit))"', code))
        keys |= {f"page:{call}:{key}" for call in ("new_set", "save_set") for key in
                 ("set_no_name", "set_no_mods", "set_library_empty")} | {"page:rename_set:set_no_name"}
        self.assertTrue({"set_editor_new", "set_editor_edit"} <= keys)
        for key in keys:
            self.assertRegex(key, bugwatch.NAME_RE)
            self.assertLessEqual(len(key), 64)


class ThePage(unittest.TestCase):
    """The page's own refusals reach Bug Watch: read in ui/app.js."""

    def test_seen_tells_bug_watch_and_never_stops_the_page(self):
        code = function(app_js(), "seen")
        self.assertIn("api().bugwatch_seen(group, key)", code)
        self.assertIn(".catch(() => {})", code)

    def test_the_editor_is_counted_opened_and_used(self):
        code = app_js()
        self.assertIn('seen("screens", set ? "set_editor_edit" : "set_editor_new");', function(code, "openEditor"))
        editor = function(code, "renderEditor")
        sending = editor[editor.index("form.onsubmit"):]
        used = sending.index('seen("screen_used", ed.id ? "set_editor_edit" : "set_editor_new");')
        self.assertLess(sending.index("await api().new_set("), used)        # only once the Launcher said yes
        self.assertLess(used, sending.index("catch (err)"))

    def test_create_pressed_with_no_mod_ticked_is_said_and_counted_and_nothing_is_sent(self):
        editor = function(app_js(), "renderEditor")
        sending = editor[editor.index("form.onsubmit"):]
        stop = sending.index("if (!ed.mods.length) {")
        part = sending[stop:sending.index("return;", stop)]
        self.assertIn('seen("messages", `page:${call}:${state.library.length ? "set_no_mods" : "set_library_empty"}`);',
                      part)
        self.assertLess(stop, sending.index("api().save_set("))
        self.assertIn('const call = ed.id ? "save_set" : "new_set";', editor)

    def test_a_blank_name_stopped_by_the_window_is_counted(self):
        code = app_js()
        editor = function(code, "renderEditor")
        self.assertIn('name.addEventListener("invalid", () => seen("messages", `page:${call}:set_no_name`));', editor)
        sending = editor[editor.index("form.onsubmit"):]
        blank = sending[sending.index("if (!ed.name.trim()) {"):sending.index("if (!ed.mods.length) {")]
        self.assertIn("name.reportValidity();", blank)        # spaces only: the same bubble, so the same count
        rename = function(code, "renameSet")
        self.assertIn('box.addEventListener("invalid", () => seen("messages", "page:rename_set:set_no_name"));', rename)
        self.assertIn("required: true", rename)

    def test_a_rename_calls_rename_set(self):
        rename = function(app_js(), "renameSet")
        self.assertIn("api().rename_set(set.id, box.value.trim())", rename)
        self.assertNotIn("api().save_set", rename)
        self.assertIn("rename_set:", (UI / "fake-api.js").read_text(encoding="utf-8"))  # the preview's stand-in


if __name__ == "__main__":
    unittest.main()
