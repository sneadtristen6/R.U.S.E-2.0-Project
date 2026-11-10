"""The Launcher's mod set editor says its refusals where the player is looking, and Create waits for a mod.

Players' reports (Bug Watch, 2026-11-02 to 11-08): 14 of 36 "New mod set" tries were refused, across six players. The
editor let Create (and Enter in the name box) go with no mod ticked; the Launcher refused; and the editor wrote the
refusal on the set's own page, which it hides while it is open. So nothing seemed to happen, and the player pressed
again. These read the screen's own code (ui/app.js): the editor's part of it, between `function renderEditor` and the
next function.
"""
import re
import unittest
from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "src" / "ruse_launcher" / "ui"


def editor() -> str:
    source = (UI / "app.js").read_text(encoding="utf-8")
    start = source.index("function renderEditor()")
    return source[start:source.index("\nfunction ", start + 10)]


class SetEditor(unittest.TestCase):
    def test_the_editor_hides_the_page_where_problems_are_otherwise_said(self):
        """Why the editor needs a place of its own: #play-message is inside #set-view, and the editor hides that."""
        page = (UI / "index.html").read_text(encoding="utf-8")
        view = page[page.index('<div id="set-view">'):page.index('<form id="editor"')]
        self.assertIn('id="play-message"', view)
        self.assertIn('$("set-view").classList.add("hidden")', editor())

    def test_a_refusal_is_said_inside_the_editor(self):
        code = editor()
        caught = code[code.index("catch (err)"):]
        self.assertIn("ed.problem = (err && err.message) || String(err);", caught)
        self.assertNotIn("problem(err)", code)       # (that writes on the hidden page)
        self.assertNotIn("setMessage((err", code)
        said = re.search(r'const said = el\("p", \{ className: "message bad" \+ \(ed\.problem \? "" : " hidden"\)', code)
        self.assertIsNotNone(said)
        self.assertIn('said.setAttribute("role", "alert")', code)
        # it is on the form, right after the buttons
        self.assertRegex(code, r'el\("div", \{ className: "actions" \}, save, cancel\),\s*said,')

    def test_the_refusal_goes_when_the_set_is_changed(self):
        code = editor()
        self.assertGreaterEqual(code.count('ed.problem = "";'), 4)   # the name, a tick, a move, the suggested order

    def test_create_waits_for_a_ticked_mod_and_says_why(self):
        """Create looks switched off until a mod is ticked and says why on it; pressed anyway (or Enter in the name
        box), the editor says why under the buttons and nothing is sent (FL-97: a press that did nothing)."""
        code = editor()
        self.assertIn('save.setAttribute("aria-disabled", String(noMods));', code)
        self.assertNotIn("save.disabled = ed.mods.length === 0", code)    # (a disabled button takes no press to say why)
        self.assertIn("if (noMods) save.title = state.library.length ? w.set_none_yet : w.library_empty_for_set;", code)
        sending = code[code.index("form.onsubmit"):]
        stop = sending.index("if (!ed.mods.length) {")
        self.assertLess(stop, sending.index("api().new_set("))
        said = sending[stop:sending.index("return;", stop)]
        self.assertIn("ed.problem = state.library.length ? w.set_none_yet : w.library_empty_for_set;", said)
        self.assertIn("renderEditor();", said)
        self.assertIn('button[aria-disabled="true"]', (UI / "style.css").read_text(encoding="utf-8"))

    def test_a_library_mod_that_has_gone_is_not_called_a_folder(self):
        code = editor()
        self.assertIn("w.set_mod_gone", code)
        self.assertIn("w.from_folder", code)
        self.assertIn(".pick-list .meta.bad", (UI / "style.css").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
