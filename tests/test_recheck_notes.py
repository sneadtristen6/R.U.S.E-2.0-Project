"""Recheck of the fix group "notes" (2026-11-12): fault L-F12 of the silent-loss review of feat/anim-decoy-blender at
07a688b5 (tests/test_review_loss.py ThePage). What a Bring back from Blender couldn't keep must be shown to the modder
ON THE PAGE, in his language, naming it: a material that came back with the plain 144 alpha (no shine or side colour
of its own: renamed or new in Blender, its alpha picture gone from the Blender folder, its picture swapped there for one
of another size), and an object Blender sent on no soldier (not brought back).

The page's own code runs (ui/app.js and ui/squad.js of the code under test, as they are) in Node (page_in_node.mjs
beside this file), and every call it makes is answered live by the Studio's own StudioApi, with the stand-ins for the
game and Blender of tests/test_modelblender.py (ItsOwnShine) and tests/test_squadblender.py (Squad): for each of the
Studio's 11 languages, a mod made, Change it in Blender opened and Blender's sending written as Blender writes it, the
page drawn, its Bring back clicked (the Model row's Bring back the model, a squad's heavy-weapon soldier's own under Its
soldiers: the layout a squad's page has when its squad card can't be read; the squad card's Bring my changes back, its
Add a soldier's too), the page left to finish (it reads look() and squad_info() again, as it does), then every line it
shows and every pop-up it says read. Each case is tried beside the same Bring back with nothing lost (the control).
For each thing that wasn't kept:
- at least one shown line names it that the page doesn't show the same way when nothing was lost (its words alike:
  names and numbers taken out);
- every such line is in the page's language (not the English page's line) with its blanks filled;
and the Bring back with nothing lost warns of none of its materials.

Each test FAILS on fddc462a by design, for the fault: nothing on the page names it, in any language (the import's
report and the model's record name a material in English only; the squad page's Bring my changes back drops
rusemod.gltf.with_alpha's word on each material, and shows neither its answer's "left_out" nor its "message"). Skipped
when no Node is found: RUSE_NODE names node.exe, else node on the PATH, else the project's tools folder's."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path

import test_modelblender as mb   # (its ItsOwnShine as a helper, by the module's name: its tests don't run here)
import test_squadblender as sb   # (its BringItBack as a helper, the same way)
from rusemod import gltf
from rusemod.dxt import png_bytes
from ruse_studio import api as studio

LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
PAGE = Path(__file__).resolve().with_name("page_in_node.mjs")
UI = Path(studio.__file__).resolve().parent / "ui"
TMP = os.environ.get("RUSE_TEST_TMP") or None
WAIT = 600   # seconds the whole page run may take


def node() -> str | None:
    """node.exe: RUSE_NODE, else on the PATH, else the project's own (D:/RUSE-2.0/tools/node-v*), else None."""
    named = os.environ.get("RUSE_NODE")
    if named and Path(named).is_file():
        return named
    found = shutil.which("node")
    if found:
        return found
    tools = Path("D:/RUSE-2.0/tools")
    own = sorted(tools.glob("node-v*/node.exe")) if tools.is_dir() else []
    return str(own[-1]) if own else None


NODE = node()


def plain(obj):
    """An answer as the page gets it (through the window's bridge: JSON)."""
    return json.loads(json.dumps(obj, default=str))


def text_of(node) -> str:
    _tag, _cls, _hidden, kids = node
    return "".join(k if isinstance(k, str) else text_of(k) for k in kids)


def bare(text: str, names) -> str:
    """A line's own words: the names, numbers, signs and one-letter bits taken out, in lower case."""
    for n in sorted(names, key=len, reverse=True):
        text = text.replace(n, " ")
    text = re.sub(r"[\d\W_]+", " ", text.lower())
    return " ".join(t for t in text.split() if len(t) > 1)


def lines_of(res: dict, names) -> list:
    """Every line the page shows in one case and language (page_in_node.mjs's "out"), and every pop-up it said:
    [(its text, its classes and its parents')]. A piece of text's line is the element it's in, or the nearest above
    it with words of its own beyond `names` and numbers; hidden elements (and what's in them) aren't shown."""
    out = []

    def walk(node, up):
        _tag, _cls, hidden, kids = node
        if hidden:
            return
        here = up + [node]
        for k in kids:
            if isinstance(k, str):
                if k.strip():
                    i = len(here) - 1
                    while i > 0 and not bare(text_of(here[i]), names):
                        i -= 1
                    out.append((text_of(here[i]), " ".join(n[1] for n in here[:i + 1])))
            else:
                walk(k, here)
    for tree in (res.get("tree"), res.get("status"), res.get("body")):
        if tree:
            walk(tree, [])
    return out + [(text, f"(pop-up {kind})") for text, kind in res.get("said") or []]


class PageCase:
    """What the page shows, in every language, for cases whose calls the Studio answers live (run_page)."""

    def run_page(self, cases: list) -> dict:
        """Each case {"name", "page", "unit", "click", "make": make(lang) -> (the StudioApi answering the page,
        what puts the case away)} run on the page in every language: {lang: {name: page_in_node.mjs's "out"}}."""
        if NODE is None:
            self.skipTest("no Node found (RUSE_NODE, the PATH, the project's tools folder)")
        makers = {c["name"]: c["make"] for c in cases}
        scenario = {"langs": list(LANGS), "words": {lang: studio.words(lang) for lang in LANGS},
                    "cases": [{k: v for k, v in c.items() if k != "make"} for c in cases]}
        got: dict = {lang: {} for lang in LANGS}
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            given = Path(d) / "scenario.json"
            given.write_text(json.dumps(scenario, ensure_ascii=False), encoding="utf-8")
            with subprocess.Popen([NODE, str(PAGE), str(UI), str(given)], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8") as run:
                errors: list = []
                drain = threading.Thread(target=lambda: errors.extend(run.stderr), daemon=True)
                drain.start()
                watch = threading.Timer(WAIT, run.kill)
                watch.start()
                api, away = None, None
                try:   # (a case that can't be made, or anything else here, stops the page's run too)
                    for line in run.stdout:
                        m = json.loads(line)
                        reply: dict = {"id": m["id"]}
                        if "begin" in m:
                            api, away = makers[m["begin"]](m["lang"])
                        elif "call" in m:
                            try:
                                if m["call"].startswith("_") or not callable(getattr(api, m["call"], None)):
                                    raise AttributeError(f"the Studio has no call {m['call']}")
                                reply["value"] = plain(getattr(api, m["call"])(*m["args"]))
                            except Exception as exc:   # (as the window's bridge: the page gets the error's message)
                                reply["error"] = str(exc) or type(exc).__name__
                        elif "end" in m:
                            got[m["lang"]][m["end"]] = m["out"]
                            away()
                            api, away = None, None
                        run.stdin.write(json.dumps(reply) + "\n")
                        run.stdin.flush()
                        if m.get("done"):
                            break
                except BaseException:
                    run.kill()
                    raise
                finally:
                    watch.cancel()
                    if away:
                        away()
                    run.wait(timeout=60)
                    drain.join(timeout=10)
            self.assertEqual(run.returncode, 0, f"the page didn't run in Node: {''.join(errors)[-3000:]}")
        return got

    def problems(self, got: dict, case: str, clean: str, names: list, also=()) -> list:
        """What's wrong, in each language, with case `case`'s page for the things `names` that weren't kept (each a
        name, or a tuple of the names it may be called by: a renamed material's new name, or its picture's, which kept
        the old one), beside case `clean`'s (the same Bring back with nothing lost): `also`, the other names in the two
        cases, taken out of a line with them to judge its words. A line naming one that the clean page shows the same
        way (its words alike) is one of the page's usual lines, not a word on the loss."""
        out = []
        wants = [(n,) if isinstance(n, str) else tuple(n) for n in names]
        every = [n for w in wants for n in w] + list(also)
        for lang in LANGS:
            res, ok = got[lang][case], got[lang][clean]
            stopped = [r["error"].splitlines()[0] for r in (res, ok) if r.get("error")]
            if stopped:
                out += [f"{lang}: the page stopped: {s}" for s in stopped]
                continue
            usual = {bare(t, every) for t, _w in lines_of(ok, every)}
            for want in wants:
                name = " or ".join(repr(n) for n in want)
                naming = [(t, w) for t, w in lines_of(res, every) if any(n in t for n in want)]
                mine = [(t, w) for t, w in naming if bare(t, every) not in usual]
                if not mine:
                    out.append(f"{lang}: nothing on the page names {name}" + (
                        f" but what it shows when nothing was lost too: {[t for t, _w in naming]}" if naming else ""))
                    continue
                english = {bare(t, every) for t, _w in lines_of(got["us"][case], every) if any(n in t for n in want)}
                for text, where in mine:
                    if re.search(r"\{\w+\}", text):
                        out.append(f"{lang}: a blank left unfilled in {text!r}")
                    if lang != "us" and bare(text, every) in english:
                        out.append(f"{lang}: in English: {text!r} ({where})")
        return out

    def warned(self, got: dict, clean: str, names: list) -> list:
        """Each line or pop-up of case `clean` (nothing lost) that warns of one of its materials `names` (shown as a
        warning or a problem)."""
        out = []
        for lang in LANGS:
            res = got[lang][clean]
            if res.get("error"):
                out.append(f"{lang}: the page stopped: {res['error'].splitlines()[0]}")
                continue
            out += [f"{lang}: {t!r} ({w})" for t, w in lines_of(res, names)
                    if any(n in t for n in names) and re.search(r"\b(warn|error)\b", w)]
        return out


class UnitPage(PageCase, unittest.TestCase):
    """The unit page's Look and moves section (app.js lookMovesBox, the layout a squad's page has when its squad card
    can't be read): its Model row's Bring back the model, and the heavy-weapon soldier's own under Its soldiers, on a
    new squad copying the US rifle squad whose riflemen and bazooka man draw two models."""
    SQUAD = mb.SQUAD
    BOTH = ["test_tank_hull", "test_tank_turret"]   # (the made-up game model's two materials, as they went out)

    def case(self, name, kind=None, rename=None, before_back=None) -> dict:
        """A Bring back on the page: in each language a mod of its own, Change it in Blender opened (`kind`: a
        soldier's own), Blender's sending written (`rename`: those materials renamed there), `before_back` done to
        the work folder; the page's click then answered live."""
        def make(lang):
            t = mb.ItsOwnShine("test_a_tank_keeps_its_own_alpha_byte_for_byte")
            t.setUp()
            stack = ExitStack()
            stack.callback(t.tearDown)
            stack.enter_context(t.patched())
            api = t.api
            api._soldier_kinds = lambda address: {"fusilier": mb.RIFLEMAN, "bazooka": mb.BAZOOKA}
            api._look_models = lambda address: ([mb.BAZOOKA, mb.RIFLEMAN], [])
            api._soldier_figures = lambda address: [("GfxDescriptorFusilier", mb.RIFLEMAN),
                                                    ("GfxDescriptorBazooka", mb.BAZOOKA)]
            api._soldiers = lambda address: True
            del api.look   # (the Studio's own look(), not ItsOwnShine's stand-in: the page draws from it)
            opened = api.model_blender(self.SQUAD, lang, kind)
            work = Path(opened["work"])
            mb.blender_sends(t.opened[-1], work / f"{work.name}.glb", rename)
            if before_back:
                before_back(work)
            return api, stack.close
        # (the Model row's button comes first on the page, the Its soldiers row's after it; by its tooltip when it's
        # that)
        return {"name": name, "page": "look", "unit": {"address": self.SQUAD, "name": "My Riflemen"}, "make": make,
                "click": {"text": "model_blender_back", "index": 1 if kind else 0,
                          "title": "tip_model_kind_blender_back" if kind else "tip_model_blender_back_kinds"}}

    def test_a_material_renamed_in_blender_is_named_on_the_page(self):
        """The riflemen's model (the Model row's Bring back the model), its turret's material renamed in Blender:
        "My turret" has the plain 144 (no alpha picture went out under that name). Fails on fddc462a: nothing on the
        page names it, in any language (the answer's report has it, in English). (As built, a material renamed in
        Blender gets the plain 144; whether it keeps its own instead is the shine agent's question 2, waiting on the
        owner: his "keep its own" would leave nothing lost here, and this case would change with it.)"""
        got = self.run_page([self.case("renamed", rename={"test_tank_turret": "My turret"}), self.case("clean")])
        self.assertEqual(self.problems(got, "renamed", "clean", [("My turret", "test_tank_turret")], also=self.BOTH),
                         [])
        self.assertEqual(self.warned(got, "clean", self.BOTH), [])

    def test_a_kind_s_own_bring_back_names_its_renamed_material_on_the_page(self):
        """The bazooka man's own Bring back the model (under Its soldiers), his turret's material renamed in Blender:
        "His turret" has the plain 144. Fails on fddc462a: nothing on the page names it. (The owner's question 2, as
        the test above.)"""
        got = self.run_page([self.case("kind", kind="bazooka", rename={"test_tank_turret": "His turret"}),
                             self.case("kind clean", kind="bazooka")])
        self.assertEqual(self.problems(got, "kind", "kind clean", [("His turret", "test_tank_turret")], also=self.BOTH),
                         [])
        self.assertEqual(self.warned(got, "kind clean", self.BOTH), [])

    def test_an_alpha_picture_gone_from_the_blender_folder_is_named_on_the_page(self):
        """The hull's alpha picture taken out of the Blender folder before the Bring back: test_tank_hull has the
        plain 144. Fails on fddc462a: nothing on the page names it."""
        def take_out(work):   # (the hull's alpha picture, as alpha.json names it)
            (work / json.loads((work / "alpha.json").read_text(encoding="utf-8"))["alpha"]["test_tank_hull"]).unlink()
        got = self.run_page([self.case("gone", before_back=take_out), self.case("clean")])
        self.assertEqual(self.problems(got, "gone", "clean", ["test_tank_hull"], also=self.BOTH), [])
        self.assertEqual(self.warned(got, "clean", self.BOTH), [])

    def test_a_picture_swapped_in_blender_for_one_of_another_size_is_named_on_the_page(self):
        """The hull's picture swapped in Blender for one of another size (4 x 4; the alpha that went out with it is
        8 x 4): Import model gives it the plain 144 (rusemod.modelin.fit_pictures) and says so in its report's notes
        only, in English, while the answer's blender_alpha says "its own, put back". Fails on fddc462a: nothing on the
        page names it."""
        def swap(work):
            send = work / f"{work.name}.glb"
            doc, views = gltf.glb_views(send.read_bytes())
            for m in doc["materials"]:
                if m["name"] == "test_tank_hull":
                    img = doc["textures"][m["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]
                    views[doc["images"][img]["bufferView"]] = png_bytes(bytes([90, 120, 30]) * 16, 4, 4)
            send.write_bytes(gltf.pack_glb(doc, views))
        got = self.run_page([self.case("size", before_back=swap), self.case("clean")])
        self.assertEqual(self.problems(got, "size", "clean", ["test_tank_hull"], also=self.BOTH), [])
        self.assertEqual(self.warned(got, "clean", self.BOTH), [])


class SquadPage(PageCase, unittest.TestCase):
    """The squad page (squad.js SquadView.section, on the squad's squad_info as the page draws it): its Bring my
    changes back clicked (Blender closed, its sending waiting), More options opened after."""

    @staticmethod
    def opened(adding=False) -> tuple:
        """(the squad opened in Blender in a mod of its own: BringItBack's, with the Studio's own look(); `adding`:
        then Add a soldier's Blender, a copy of soldier 2; what puts it away, the soldier sent back's material as his
        start file named it: his alpha picture went out under it)."""
        t = sb.BringItBack("test_nothing_changed_at_all")
        stack = ExitStack()
        t.setUp()   # (the squad opened in Blender, Blender's opening written, Import model stood in)
        stack.callback(t.tearDown)
        del t.api.look   # (the Studio's own look(): the page's More options draws from it)
        stack.enter_context(t.patched())
        sid = "5"
        if adding:
            t.api.soldier_add(sb.SQUAD, "copy", "2")
            t.blender_opened()
            t.taking_in()
            sid = "new"
        return t, stack, next(iter(next(s for s in t.manifest()["soldiers"] if s["id"] == sid)["alpha"]))

    def material(self, adding=False) -> str:
        t, stack, his = self.opened(adding)
        stack.close()
        return his

    def case(self, name, send, adding=False) -> dict:
        """A Bring my changes back on the page: in each language the squad opened in Blender (opened), Blender's
        sending written by `send(t, his material)`; the page's click then answered live."""
        def make(lang):
            t, stack, his = self.opened(adding)
            send(t, his)
            return t.api, stack.close
        return {"name": name, "page": "squad", "unit": {"address": sb.SQUAD, "name": "My Riflemen"}, "make": make,
                "click": {"text": "squad_blender_back"}}

    def test_a_material_made_in_blender_is_named_on_the_page(self):
        """Soldier 5 sent back with a material made in Blender ("Helmet paint": no alpha picture goes with it), so
        rusemod.gltf.with_alpha gives it the plain 144 and says so, and squadblender drops that word ([0]). Fails on
        fddc462a: the card says "Changed: Soldier 5: Bazooka man ..." and nothing on the page names it."""
        made = self.case("squad", lambda t, his: t.blender_sends({**t.figures, "5": sb.glb_from(b"PNG-red",
                                                                                                "Helmet paint")}))
        clean = self.case("squad clean", lambda t, his: t.blender_sends({**t.figures, "5": sb.glb_from(b"PNG-red", his)}))
        his = self.material()
        got = self.run_page([made, clean])
        self.assertEqual(self.problems(got, "squad", "squad clean", ["Helmet paint"], also=[his]), [])
        self.assertEqual(self.warned(got, "squad clean", [his]), [])

    def test_a_soldier_added_from_blender_with_a_material_made_there_is_named_on_the_page(self):
        """Add a soldier (a copy of soldier 2), his material in Blender replaced by one made there ("Helmet paint"):
        he joins the squad (squadblender._join) with the plain 144 on it, the word on it dropped there too. Fails on
        fddc462a: the card says "One soldier more ..." and nothing on the page names it."""
        made = self.case("join", lambda t, his: t.blender_sends({"new": sb.glb_from(b"PNG-new", "Helmet paint")}),
                         adding=True)
        clean = self.case("join clean", lambda t, his: t.blender_sends({"new": sb.glb_from(b"PNG-new", his)}),
                          adding=True)
        his = self.material(adding=True)
        got = self.run_page([made, clean])
        self.assertEqual(self.problems(got, "join", "join clean", ["Helmet paint"], also=[his]), [])
        self.assertEqual(self.warned(got, "join clean", [his]), [])

    def test_an_alpha_picture_gone_from_the_squad_s_blender_folder_is_named_on_the_page(self):
        """Soldier 5 sent back with his own material, but its alpha picture (in the squad's Blender folder, as the
        squad's opening wrote it) taken out before the Bring back: rusemod.gltf.with_alpha gives it the plain 144 and
        says so, and squadblender drops that word. Fails on fddc462a: nothing on the page names his material."""
        def send(gone):
            def go(t, his):
                t.blender_sends({**t.figures, "5": sb.glb_from(b"PNG-red", his)})
                if gone:
                    Path(next(s for s in t.manifest()["soldiers"] if s["id"] == "5")["alpha"][his]).unlink()
            return go
        his = self.material()
        got = self.run_page([self.case("gone", send(True)), self.case("gone clean", send(False))])
        self.assertEqual(self.problems(got, "gone", "gone clean", [his]), [])
        self.assertEqual(self.warned(got, "gone clean", [his]), [])

    def test_objects_blender_sent_on_no_soldier_are_named_on_the_page(self):
        """An object Blender sent on no soldier ("My Cube": on no soldier's bones or collection) isn't brought back:
        squad_blender_back's answer names it ("left_out", and its "message" in the page's language), and Blender said
        so at Send. Fails on fddc462a: the page shows neither, so nothing on it names the object."""
        def send(left):
            return lambda t, his: t.blender_sends({**t.figures, "5": sb.glb_from(b"PNG-red", his)}, left_out=left)
        his = self.material()
        got = self.run_page([self.case("left out", send(["My Cube"])), self.case("none left out", send([]))])
        self.assertEqual(self.problems(got, "left out", "none left out", ["My Cube"], also=[his]), [])


if __name__ == "__main__":
    unittest.main()
