"""Delete always goes through (the owner's item 6, 2026-11-13). Asked: "When deleting a unit stops half way, the button
that clears what it left only shows in Test in game's error. Should it also show when you open the mod?" His answer,
whole: "Why would deleting a unit stop? You should just meet if someone clicks it should through so fix number six".

A file of the unit another program holds (a real Windows share lock: Python's open() shares reading and writing, never
deleting, as most programs do; one test holds it from another program, a second Python) no longer stops Delete: it's
tried again for a few seconds (edits.HOLD_WAIT), then the unit goes all the same (its copy, its lines in every list,
units.toml, the copies.toml ticks) and the file waits, named in the mod's holding record (rusemod.holding): the build
and Export leave it out, and the Studio takes it out by itself when the mod is opened and before Test in game and Export
build it. The page says so in one line (app.js waitingTold).

The review's cases (2026-11-13), fixed: a unit made again under its name takes the record's lines of the old one out
first (holding.forget), so its own files are never left out or taken out, even a clip copied from the same source with
the very size and time Delete left; a waiting file its program saved after the Delete never stops the build and is
never taken out; a list file held for a moment (units.toml) is tried again as long as the unit's own files are.

What must keep working, checked here too: a units.toml that can't be read still stops Delete before anything changes; a
list file held past the wait still stops it, everything put back and nothing named, in words on the page; a record
that can't be written puts everything back; a card of no unit that the record doesn't name still stops the build with
its words; a file written in the waiting file's place since (the unit made again under its name) is never left out or
taken out; a record changed by hand names nothing outside the mod's own files.

On e9a092c3's code (run with its src first on the path) every test here fails but the six controls, which pass on
both:
    test_a_units_toml_that_can_t_be_read_still_stops_it_before_anything_changes
    test_a_copies_toml_that_can_t_be_read_still_stops_it_before_anything_changes
    test_a_held_units_toml_still_stops_it_everything_put_back_and_nothing_named
    test_a_units_toml_held_past_the_wait_still_stops_it_in_words_everything_put_back
    test_a_card_of_no_unit_the_record_doesnt_name_still_stops_the_build
    test_a_plain_delete_leaves_nothing_behind
rusemod.holding is imported inside the tests, so this file runs there too."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from test_studio import M4, WithMod
from rusemod import Edat, anim, package
from rusemod.build import build_pack, load_mod
from ruse_studio import edits as edits_module
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import ModEdits, TakeOut

WINDOWS = os.name == "nt"
TMP = os.environ.get("RUSE_TEST_TMP") or None
SRC = Path(edits_module.__file__).resolve().parent
UNIT = "$/GFX/Everything/Descriptor_Unit_Lancer"
OTHER = "$/GFX/Everything/Descriptor_Unit_Keeper"
SOURCE = "$/GFX/Everything/Descriptor_Unit_M4_Sherman"
SUPER = "$/GFX/Everything/Descriptor_Unit_Super_Sherman"
CLIP = "genanim_15/ww2/res3d/units/common/fusilier_standlod0.baf"
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")


def tail(address: str) -> str:
    return address.rsplit("/", 1)[-1]


def quick(seconds: float = 0.3):
    """A held file tried again this long only (create=True: this file still runs on e9a092c3's code)."""
    return mock.patch.object(edits_module, "HOLD_WAIT", seconds, create=True)


def tree(folder: Path) -> dict:
    """Every file under `folder` but the holding record's folder: {its path in it: its bytes}."""
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in Path(folder).rglob("*")
            if p.is_file() and ".taking-out" not in p.relative_to(folder).parts}


def record(mod: Path) -> dict:
    f = mod / ".taking-out" / "waiting.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def unit_files(mod: Path, t: str) -> list:
    """The unit `t`'s own files in the mod, listed here on their own (not the code's list), as paths in the mod."""
    models = mod / "files" / "models"
    out = [mod / "files" / "cards" / f"{t}.png", mod / "files" / "buildings" / t, mod / anim.OWN / t]
    out += [models / f"{t}{s}" for s in (".glb", ".json", ".squad.toml", ".copy.toml")]
    out += list(models.glob(f"{t}@*")) if models.is_dir() else []
    return sorted(p.relative_to(mod).as_posix() for p in out if p.exists())


def unit_on_disk(mod: Path, t: str) -> None:
    """Every kind of file Delete takes for the unit `t` (each one the build reads as it reads it), and its own
    animations' folder with two clips."""
    models = mod / "files" / "models"
    models.mkdir(parents=True, exist_ok=True)
    (mod / "files" / "cards").mkdir(parents=True, exist_ok=True)
    (mod / "files" / "cards" / f"{t}.png").write_bytes(b"card of " + t.encode())
    for name in (f"{t}.glb", f"{t}.json", f"{t}@bazooka.glb", f"{t}@2.json"):
        (models / name).write_bytes(b"of " + name.encode())
    (models / f"{t}.squad.toml").write_text("count = 5\n", encoding="utf-8")
    (models / f"{t}.copy.toml").write_text('of = "x"\n', encoding="utf-8")
    look = mod / "files" / "buildings" / t
    look.mkdir(parents=True, exist_ok=True)
    (look / "building.toml").write_text('piece = "x"\nmodel = "look.glb"\n', encoding="utf-8")
    (look / "look.glb").write_bytes(b"look of " + t.encode())
    own = mod / anim.OWN / t
    own.mkdir(parents=True, exist_ok=True)
    (own / "stand.baf").write_bytes(b"clip of " + t.encode())
    (own / "walk.baf").write_bytes(b"another clip of " + t.encode())


def rows(mod: Path, tails) -> None:
    """units.toml with a row for each of `tails`, playing its own stand.baf."""
    lines = []
    for t in tails:
        lines += [f"[unit.{t}.action]", 't_stand = "stand.baf"', ""]
    (mod / anim.UNITS).parent.mkdir(parents=True, exist_ok=True)
    (mod / anim.UNITS).write_text("\n".join(lines), encoding="utf-8")


def ticks(mod: Path, tails) -> None:
    """copies.toml with one copy of a clip, ticked for each of `tails`."""
    (mod / anim.COPIES).parent.mkdir(parents=True, exist_ok=True)
    (mod / anim.COPIES).write_text(f'[copy.x]\nname = "X"\nclip = "{CLIP}"\n[copy.x.units]\n'
                                   + "".join(f"{t} = []\n" for t in tails), encoding="utf-8")


def bare_mod(root: Path) -> Path:
    """A mod folder with two new units, every file of each, their rows and their ticks."""
    mod = root / "mod"
    mod.mkdir()
    (mod / "mod.toml").write_text('[mod]\nid = "held"\nversion = "1.0.0"\n', encoding="utf-8")
    edits = ModEdits(mod)
    edits.add_unit(UNIT, SOURCE, "Lancer", {"ProductionPrice": 100})
    edits.add_unit(OTHER, SOURCE, "Keeper", {})
    for t in (tail(UNIT), tail(OTHER)):
        unit_on_disk(mod, t)
    rows(mod, [tail(UNIT), tail(OTHER)])
    ticks(mod, [tail(UNIT), tail(OTHER)])
    return mod


class Holder:
    """Another program holding a file open: a second Python, open() as most programs open a file (no sharing of
    deletion), until let_go."""

    def __init__(self, path: Path):
        code = "import sys; f = open(sys.argv[1], 'rb'); print('held', flush=True); sys.stdin.read(); f.close()"
        self.proc = subprocess.Popen([sys.executable, "-c", code, str(path)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True)
        if self.proc.stdout.readline().strip() != "held":
            raise RuntimeError("the holding program didn't start")

    def let_go(self):
        if self.proc.poll() is None:
            self.proc.stdin.close()
            self.proc.wait(30)
        self.proc.stdout.close()


@unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
class HeldOnAModFolder(unittest.TestCase):
    """edits.ModEdits.remove_unit (and TakeOut) on a bare mod folder."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=TMP)
        self.addCleanup(self.tmp.cleanup)
        self.mod = bare_mod(Path(self.tmp.name))
        self.tail, self.other = tail(UNIT), tail(OTHER)
        self.card = self.mod / "files" / "cards" / f"{self.tail}.png"
        self.before = tree(self.mod)

    def held(self, path: Path):
        f = open(path, "rb")
        self.addCleanup(f.close)
        return f

    def others_kept(self):
        """The other unit: in the mod, every file of it byte for byte, its row and its tick."""
        self.assertIn(OTHER, ModEdits(self.mod).new_units)
        self.assertIn(self.other, anim.read_units(self.mod))
        self.assertEqual(anim.ticked_in(self.mod, self.other), ["x"])
        now = tree(self.mod)
        for name, data in self.before.items():
            if self.other in name:
                self.assertEqual(now.get(name), data, name)

    def test_delete_goes_through_with_its_card_held_and_the_build_and_export_leave_the_card_out(self):
        f = self.held(self.card)
        with quick():
            ModEdits(self.mod).remove_unit(UNIT)
        # the unit went: its copy and name, its row, its tick, every other file of it
        self.assertNotIn(UNIT, ModEdits(self.mod).new_units)
        self.assertNotIn("Lancer", (self.mod / "text" / "studio.baseunite.csv").read_text(encoding="utf-8"))
        self.assertNotIn(self.tail, anim.read_units(self.mod))
        self.assertEqual(anim.ticked_in(self.mod, self.tail), [])
        self.assertEqual(unit_files(self.mod, self.tail), [f"files/cards/{self.tail}.png"])
        self.others_kept()
        # the card waits, named with its size and time as Delete left it
        st = self.card.stat()
        self.assertEqual(record(self.mod)["files"], [{"unit": self.tail, "path": f"files/cards/{self.tail}.png",
                                                      "size": st.st_size, "time": st.st_mtime_ns}])
        # the build and Export leave it out (still held), the other unit's card in
        info = load_mod(self.mod)[0]
        self.assertEqual(sorted(info.cards), [self.other])
        packed = [p.relative_to(self.mod).as_posix() for p in package.files_of(self.mod)]
        self.assertNotIn(f"files/cards/{self.tail}.png", packed)
        self.assertIn(f"files/cards/{self.other}.png", packed)
        self.assertFalse(any(".taking-out" in p for p in packed))
        from rusemod import holding
        self.assertEqual(holding.clear(self.mod), [])      # (still held: it stays named)
        self.assertTrue(self.card.is_file())
        f.close()
        self.assertEqual(holding.clear(self.mod), [f"files/cards/{self.tail}.png"])
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertFalse((self.mod / ".taking-out").exists())
        self.others_kept()

    def test_another_program_holding_its_model_and_a_clip(self):
        """Held by another program (a second Python): the model and the clip wait, the clips' folder gives up its
        other clip at once; both go once that program lets go."""
        model = self.mod / "files" / "models" / f"{self.tail}.glb"
        clip = self.mod / anim.OWN / self.tail / "stand.baf"
        holders = [Holder(model), Holder(clip)]
        try:
            with quick():
                ModEdits(self.mod).remove_unit(UNIT)
            self.assertEqual(sorted(e["path"] for e in record(self.mod)["files"]),
                             [f"{anim.OWN}/{self.tail}/stand.baf", f"files/models/{self.tail}.glb"])
            self.assertEqual(sorted(p.name for p in clip.parent.iterdir()), ["stand.baf"])   # (walk.baf went)
            self.assertNotIn(self.tail, load_mod(self.mod)[0].models)
        finally:
            for h in holders:
                h.let_go()
        from rusemod import holding
        holding.clear(self.mod)
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertFalse((self.mod / ".taking-out").exists())
        self.others_kept()

    def test_every_reader_of_the_build_leaves_its_waiting_file_out(self):
        """Held: its squad file, its own copy of the model, a soldier's look record and its building look (the readers
        that read inside a file, mod_squads, mod_copies, mod_game_looks, mod_looks): the build reads none of them and
        Export packs none, the other unit's all read and packed."""
        from rusemod.squads import GAME
        models = self.mod / "files" / "models"
        for t in (self.tail, self.other):   # (soldier 2 of each wears the game's look: a record mod_game_looks takes)
            (models / f"{t}@2.json").write_text(json.dumps({"for": "2", "look": GAME}), encoding="utf-8")
        held = [models / f"{self.tail}.squad.toml", models / f"{self.tail}.copy.toml", models / f"{self.tail}@2.json",
                self.mod / "files" / "buildings" / self.tail / "building.toml"]
        for path in held:
            self.held(path)
        with quick():
            ModEdits(self.mod).remove_unit(UNIT)
        self.assertEqual(sorted(e["path"] for e in record(self.mod)["files"]),
                         sorted(p.relative_to(self.mod).as_posix() for p in held))
        info = load_mod(self.mod)[0]
        self.assertEqual((sorted(info.squads), sorted(info.model_copies), sorted(info.looks), info.squad_game),
                         ([self.other], [self.other], [self.other], {self.other: [2]}))
        packed = {p.relative_to(self.mod).as_posix() for p in package.files_of(self.mod)}
        self.assertEqual(packed & {p.relative_to(self.mod).as_posix() for p in held}, set())
        self.assertIn(f"files/models/{self.other}.squad.toml", packed)
        self.assertIn(f"files/buildings/{self.other}/building.toml", packed)

    def test_a_copies_toml_that_can_t_be_read_still_stops_it_before_anything_changes(self):
        """(Can't be read: not TOML at all, as anim.read_copies reads it. A copies.toml that reads but holds a wrong
        value, name = 1, never stopped Delete, before or now: the take-out only takes the unit's ticks out of it.)"""
        self.held(self.card)
        (self.mod / anim.COPIES).write_text("[copy.\n", encoding="utf-8")
        before = tree(self.mod)
        with quick(), self.assertRaises(anim.AnimError):
            ModEdits(self.mod).remove_unit(UNIT)
        self.assertEqual(tree(self.mod), before)
        self.assertFalse((self.mod / ".taking-out").exists())

    def test_a_file_let_go_within_the_few_seconds_goes_with_the_rest(self):
        f = self.held(self.card)
        threading.Timer(0.3, f.close).start()
        started = time.monotonic()
        with quick(3.0):
            ModEdits(self.mod).remove_unit(UNIT)
        self.assertGreaterEqual(time.monotonic() - started, 0.25)    # (it waited for it)
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertEqual(record(self.mod), {})
        self.assertFalse((self.mod / ".taking-out").exists())

    def test_a_folder_that_is_a_program_s_current_folder(self):
        """Windows won't move or remove a folder a program is in (a command window's current folder), but lets every
        file in it go: the files go, the empty folder waits (nothing the modder needs told: it holds no file), and goes
        once that program is elsewhere."""
        own = self.mod / anim.OWN / self.tail
        here = os.getcwd()
        os.chdir(own)
        try:
            take = TakeOut(self.mod)
            with quick():
                ModEdits(self.mod).remove_unit(UNIT, take)
                told = take.settle()
            take.done()
            self.assertEqual(told, [])
            self.assertEqual(list(own.iterdir()), [])
            self.assertEqual(record(self.mod)["folders"], [{"unit": self.tail, "path": f"{anim.OWN}/{self.tail}"}])
        finally:
            os.chdir(here)
        from rusemod import holding
        self.assertEqual(holding.clear(self.mod), [f"{anim.OWN}/{self.tail}"])
        self.assertEqual(unit_files(self.mod, self.tail), [])
        self.assertFalse((self.mod / ".taking-out").exists())

    # --- what must keep working ---
    def test_a_file_written_in_its_place_since_is_never_taken_out_or_left_out(self):
        """The unit made again under its name once the program let go of its old card, a new card written there: the
        record's line is the old card's (its size and time), so the new one is read by the build, packed, and kept."""
        f = self.held(self.card)
        with quick():
            ModEdits(self.mod).remove_unit(UNIT)
        f.close()
        ModEdits(self.mod).add_unit(UNIT, SOURCE, "Lancer", {})
        self.card.write_bytes(b"the new Lancer's own card, longer than the old one")
        self.assertIn(self.tail, load_mod(self.mod)[0].cards)
        self.assertIn(self.card, package.files_of(self.mod))
        from rusemod import holding
        self.assertEqual(holding.clear(self.mod), [])
        self.assertEqual(self.card.read_bytes(), b"the new Lancer's own card, longer than the old one")
        self.assertEqual(record(self.mod), {})

    def test_a_file_its_program_saved_after_the_delete_stays_out_of_the_build_and_is_never_taken_out(self):
        """The review's case: the program that had the card open (an editor, reading and writing) saves it after the
        Delete. Its unit is gone all the same: the build and Export leave it out, and the clear never takes it out (a
        save made after the Delete is never removed); it stays named until the unit is made again."""
        f = open(self.card, "r+b")
        self.addCleanup(f.close)
        with quick():
            ModEdits(self.mod).remove_unit(UNIT)
        f.seek(0)
        f.write(b"its card, saved again by the editor after the Delete")
        f.close()
        self.assertNotIn(self.tail, load_mod(self.mod)[0].cards)
        self.assertNotIn(self.card, package.files_of(self.mod))
        from rusemod import holding
        self.assertEqual(holding.clear(self.mod), [])
        self.assertEqual(self.card.read_bytes()[:52], b"its card, saved again by the editor after the Delete")
        self.assertEqual([e["path"] for e in record(self.mod)["files"]], [f"files/cards/{self.tail}.png"])
        self.assertNotIn(self.tail, load_mod(self.mod)[0].cards)
        ModEdits(self.mod).add_unit(UNIT, SOURCE, "Lancer", {})   # (made again: the card is the new unit's)
        self.assertIn(self.tail, load_mod(self.mod)[0].cards)
        self.assertEqual(record(self.mod), {})

    def test_a_unit_made_again_while_its_old_card_is_still_held_takes_it_as_its_own(self):
        """Made again while the program still holds the old card: what can't be taken out yet is the new unit's, read by
        the build and packed (the page shows that card as its own too: api._own_card_file), never taken out later."""
        self.held(self.card)
        with quick():
            ModEdits(self.mod).remove_unit(UNIT)
        ModEdits(self.mod).add_unit(UNIT, SOURCE, "Lancer", {})
        self.assertEqual(record(self.mod), {})
        self.assertIn(self.tail, load_mod(self.mod)[0].cards)
        self.assertIn(self.card, package.files_of(self.mod))

    def test_a_groups_draft_never_touches_the_record(self):
        """groups.Draft adds units in memory only (a unit's group worked out before it's made): the record on disk stays."""
        from ruse_studio.groups import Draft
        self.held(self.card)
        with quick():
            ModEdits(self.mod).remove_unit(UNIT)
        before = record(self.mod)
        Draft(ModEdits(self.mod)).add_unit(UNIT, SOURCE, "Lancer", {})
        self.assertEqual(record(self.mod), before)

    def test_a_units_toml_that_can_t_be_read_still_stops_it_before_anything_changes(self):
        self.held(self.card)
        (self.mod / anim.UNITS).write_text("[unit.\n", encoding="utf-8")
        before = tree(self.mod)
        with quick(), self.assertRaises(anim.AnimError):
            ModEdits(self.mod).remove_unit(UNIT)
        self.assertEqual(tree(self.mod), before)
        self.assertFalse((self.mod / ".taking-out").exists())

    def test_a_held_units_toml_still_stops_it_everything_put_back_and_nothing_named(self):
        self.held(self.card)
        self.held(self.mod / anim.UNITS)
        with quick(), self.assertRaises(OSError):
            ModEdits(self.mod).remove_unit(UNIT)
        self.assertEqual(tree(self.mod), self.before)
        self.assertFalse((self.mod / ".taking-out").exists())

    def test_a_record_that_can_t_be_written_puts_everything_back(self):
        self.held(self.card)
        with quick(), mock.patch("rusemod.holding._write", side_effect=OSError(28, "No space left on device")), \
                self.assertRaises(OSError):
            ModEdits(self.mod).remove_unit(UNIT)
        self.assertEqual(tree(self.mod), self.before)
        self.assertIn(UNIT, ModEdits(self.mod).new_units)
        self.assertFalse((self.mod / ".taking-out").exists())


class TheRecord(unittest.TestCase):
    def test_a_record_changed_by_hand_names_nothing_outside_the_mod_s_own_files(self):
        from rusemod import holding
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            root = Path(d)
            mod = root / "mod"
            (mod / "files" / "cards").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "x"\n', encoding="utf-8")
            (root / "outside.txt").write_text("not the mod's", encoding="utf-8")
            (mod / "files" / "cards" / "Descriptor_Unit_A.png").write_bytes(b"a card")
            lines = []
            for rel in ("mod.toml", "../outside.txt", "files/../mod.toml", "files\\cards\\Descriptor_Unit_A.png",
                        str(root / "outside.txt"), "files/cards/Descriptor_Unit_A.png"):
                st = os.stat(mod / rel)
                lines.append({"unit": "A", "path": rel, "size": st.st_size, "time": st.st_mtime_ns})
            (mod / ".taking-out").mkdir()
            (mod / ".taking-out" / "waiting.json").write_text(json.dumps(
                {"files": lines, "folders": [{"path": ".."}, {"path": "files/.."}], "holds": ["..", "a/b", "c\\d"]}),
                encoding="utf-8")
            self.assertEqual([e["path"] for e in holding.read(mod)["files"]], ["files/cards/Descriptor_Unit_A.png"])
            self.assertEqual(holding.read(mod)["folders"], [])
            self.assertEqual(holding.read(mod)["holds"], [])
            self.assertEqual(holding.clear(mod), ["files/cards/Descriptor_Unit_A.png"])
            self.assertTrue((mod / "mod.toml").is_file())
            self.assertTrue((root / "outside.txt").is_file())

    def test_no_record_no_folder_and_nothing_left_out(self):
        from rusemod import holding
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            self.assertEqual(holding.clear(d), [])
            self.assertIsNone(holding.skip_of(d))
            self.assertFalse((Path(d) / ".taking-out").exists())


class OnTheStudio(WithMod):
    """The Studio's Delete, Test in game, Export and opening a mod, on the Studio tests' made-up game."""

    def setUp(self):
        super().setUp()
        tmp = Path(tempfile.mkdtemp(dir=TMP))
        self.addCleanup(shutil.rmtree, tmp, True)
        self.dest = tmp
        self.folder = Path(self.api.new_mod("Held")["current"])
        self.api.new_unit(M4, "Super Sherman", 50, group="new")
        self.tail = tail(SUPER)
        self.card = self.folder / "files" / "cards" / f"{self.tail}.png"
        self.card.parent.mkdir(parents=True, exist_ok=True)
        self.card.write_bytes(b"its own card")
        (self.folder / anim.OWN / self.tail).mkdir(parents=True)
        (self.folder / anim.OWN / self.tail / "stand.baf").write_bytes(b"its clip")
        rows(self.folder, [self.tail])   # (its own animation; no copies.toml: the made-up game has no clips to copy)

    def build_errors(self) -> list:
        """The mod built on the made-up game's packs (as test_studio's NewUnits builds): its errors' words."""
        rev = self.game / "Data" / "PC" / "190852"
        arc, texts = Edat((rev / "ZZ_GladPatchableWin.dat").read_bytes()), Edat((rev / "ZZ_Win.dat").read_bytes())
        return [e.message for e in build_pack(arc, [load_mod(self.folder)], text_arc=texts).errors]

    def wait(self, job: str) -> dict:
        end = time.time() + 60
        while self.api.job(job)["state"] == "running" and time.time() < end:
            time.sleep(0.05)
        return self.api.job(job)

    def delete_held(self) -> tuple:
        """Delete clicked with the unit's card open in another program: (the answer, the open file)."""
        f = open(self.card, "rb")
        self.addCleanup(f.close)
        with quick():
            got = self.api.delete_unit(SUPER)
        return got, f

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_delete_goes_through_says_it_and_test_in_game_clears_it_before_its_build(self):
        got, f = self.delete_held()
        self.assertEqual((got["deleted"], got["waiting"]), (SUPER, [f"files/cards/{self.tail}.png"]))
        self.assertNotIn(SUPER, [u["address"] for u in self.api.units()["units"] if u["new"]])
        self.assertNotIn(self.tail, anim.read_units(self.folder))
        self.assertFalse((self.folder / anim.OWN / self.tail).exists())
        self.assertEqual(self.build_errors(), [])            # (the card still held: the build leaves it out)
        f.close()
        # (a change of the mod's own: on the made-up game a mod that changes nothing makes no copy to start)
        self.api.edit(M4, "SeuilMort", 15)
        view = self.wait(self.api.test_in_game()["job"])
        self.assertEqual(view["state"], "done", view)
        self.assertFalse(self.card.exists())                 # (taken out before the build, by itself)
        self.assertFalse((self.folder / ".taking-out").exists())

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_export_with_the_card_still_held_leaves_it_out_and_opening_the_mod_clears_it(self):
        _got, f = self.delete_held()
        self.api._pick_save = lambda name: str(self.dest / name)
        view = self.wait(self.api.export_mod("1.0.0", "a modder", "Held.")["job"])   # (built on the made-up game)
        self.assertEqual(view["state"], "done", view)
        with zipfile.ZipFile(view["result"]["path"]) as z:
            names = z.namelist()
        self.assertFalse([n for n in names if self.tail in n or ".taking-out" in n], names)
        self.assertTrue(self.card.is_file())                 # (still held: it stays, named)
        f.close()
        self.api.choose_mod(str(self.folder))
        self.assertFalse(self.card.exists())
        self.assertFalse((self.folder / ".taking-out").exists())

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_export_clears_it_first_once_let_go(self):
        _got, f = self.delete_held()
        f.close()
        self.api._game = lambda: None                        # (packed without a build: what's packed is checked)
        view = self.wait(self.api.export_mod("1.0.0", "a modder", "Held.")["job"])
        self.assertEqual(view["state"], "done", view)
        self.assertFalse(self.card.exists())

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_the_studio_s_start_clears_it(self):
        """app.py, when the window opens: the mod and the map it opens with (here the same folder)."""
        _got, f = self.delete_held()
        f.close()
        self.assertEqual(self.api._clear_waiting(self.api._mod_dir(), self.api._map_dir()),
                         [f"files/cards/{self.tail}.png"])
        self.assertFalse(self.card.exists())
        app = (SRC / "app.py").read_text(encoding="utf-8")
        self.assertIn("api._clear_waiting(api._mod_dir(), api._map_dir())", app)
        self.assertLess(app.index("api.use_documents()"), app.index("api._clear_waiting("))   # (the folders moved)

    def test_a_card_of_no_unit_the_record_doesnt_name_still_stops_the_build(self):
        """A control: what the record doesn't name is read as before, and the build says what's wrong."""
        stray = self.folder / "files" / "cards" / "Descriptor_Unit_Nobody.png"
        stray.write_bytes(b"a card for nothing")
        errors = self.build_errors()
        self.assertTrue(any("files/cards/Descriptor_Unit_Nobody.png: no mod in the set makes a new unit "
                            "Descriptor_Unit_Nobody" in e for e in errors), errors)

    def test_a_plain_delete_leaves_nothing_behind(self):
        """A control: nothing held, nothing waits, nothing said, no holding folder."""
        got = self.api.delete_unit(SUPER)
        self.assertEqual((got["deleted"], got.get("waiting", [])), (SUPER, []))
        self.assertFalse(self.card.exists())
        self.assertFalse((self.folder / ".taking-out").exists())

    def made_from_the_sherman(self) -> Path:
        """setUp's unit gone (nothing held), the game's Sherman given a clip of the mod's own, and Super Sherman made
        from it: the copy takes the clip along with its very time (anim.copy_unit). Its clip."""
        self.api.delete_unit(SUPER)
        own = self.folder / anim.OWN / tail(M4)
        own.mkdir(parents=True)
        (own / "stand.baf").write_bytes(b"the mod's own stand for the game's Sherman")
        rows(self.folder, [tail(M4)])
        self.api.new_unit(M4, "Super Sherman", 50, group="new")
        clip = self.folder / anim.OWN / self.tail / "stand.baf"
        self.assertEqual(clip.stat().st_mtime_ns, (own / "stand.baf").stat().st_mtime_ns)
        return clip

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_made_again_from_the_same_source_its_clip_is_its_own(self):
        """The review's case: Delete with the copied clip held, the unit made again from the same source once the
        program let go. Its new clip has the very size and time the record named for the old one, and is its own all the
        same: packed, kept by the clear, and the mod builds (before: left out, then taken out, and the build stopped)."""
        clip = self.made_from_the_sherman()
        rel = clip.relative_to(self.folder).as_posix()
        f = open(clip, "rb")
        try:
            with quick():
                self.assertEqual(self.api.delete_unit(SUPER)["waiting"], [rel])
        finally:
            f.close()
        self.api.new_unit(M4, "Super Sherman", 50, group="new")
        self.assertIn(rel, [p.relative_to(self.folder).as_posix() for p in package.files_of(self.folder)])
        self.assertEqual(self.api._clear_waiting(self.folder), [])
        self.assertTrue(clip.is_file())
        self.assertFalse((self.folder / ".taking-out").exists())
        load_mod(self.folder)

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_made_again_with_its_old_clip_still_held_export_packs_the_clip(self):
        """As above, the program still holding the clip when the unit is made again and when Export runs (before: Export
        packed the unit's rows without its clip and refused its own file)."""
        clip = self.made_from_the_sherman()
        f = open(clip, "rb")
        self.addCleanup(f.close)
        with quick():
            self.api.delete_unit(SUPER)
        self.api.new_unit(M4, "Super Sherman", 50, group="new")
        self.api._pick_save = lambda name: str(self.dest / name)
        view = self.wait(self.api.export_mod("1.0.0", "a modder", "Held.")["job"])   # (built on the made-up game)
        self.assertEqual(view["state"], "done", view)
        with zipfile.ZipFile(view["result"]["path"]) as z:
            self.assertIn(clip.relative_to(self.folder).as_posix(), z.namelist())

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_a_card_its_program_saved_after_the_delete_never_stops_the_build(self):
        """The review's case: the editor that had the card open saves it after the Delete. No build stops on it (no
        button needed), Test in game clears around it, and it's never taken out."""
        f = open(self.card, "r+b")
        self.addCleanup(f.close)
        with quick():
            got = self.api.delete_unit(SUPER)
        f.seek(0)
        f.write(b"its own card, saved again by the editor after the Delete")
        f.close()
        self.assertEqual(got["waiting"], [f"files/cards/{self.tail}.png"])
        self.assertEqual(self.build_errors(), [])
        self.assertEqual(self.api._clear_waiting(self.folder), [])
        self.assertEqual(self.card.read_bytes(), b"its own card, saved again by the editor after the Delete")
        self.assertEqual(self.build_errors(), [])

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_a_units_toml_held_for_a_moment_is_tried_again(self):
        """The review's case: units.toml held half a second (a sync program, an antivirus). Delete waits for it as for
        the unit's own files, and goes through (before: stopped at once)."""
        f = open(self.folder / anim.UNITS, "rb")
        threading.Timer(0.5, f.close).start()
        started = time.monotonic()
        with quick(3.0):
            got = self.api.delete_unit(SUPER)
        self.assertGreaterEqual(time.monotonic() - started, 0.4)
        self.assertEqual((got["deleted"], got["waiting"]), (SUPER, []))
        self.assertNotIn(self.tail, anim.read_units(self.folder))
        self.assertFalse(self.card.exists())

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_a_leftovers_take_out_tries_a_units_toml_held_for_a_moment_again(self):
        """The same kind of fault in the other take-out: what a unit the mod no longer has left behind (Delete on it,
        Test in game's Take out what it left: api._take_leftovers) with units.toml held half a second goes through."""
        edits = ModEdits(self.folder)
        unit = edits.new_units.pop(SUPER)
        edits.save()                                         # (the unit gone from the mod, its rows and files left)
        self.assertIsNotNone(unit)
        self.assertIn(self.tail, anim.read_units(self.folder))
        f = open(self.folder / anim.UNITS, "rb")
        threading.Timer(0.5, f.close).start()
        with quick(3.0):
            got = self.api.delete_unit(SUPER)
        self.assertIsNone(got["deleted"])
        self.assertTrue(got["leftovers"])
        self.assertNotIn(self.tail, anim.read_units(self.folder))
        self.assertFalse(self.card.exists())

    @unittest.skipUnless(WINDOWS, "a file another program holds: Windows")
    def test_a_units_toml_held_past_the_wait_still_stops_it_in_words_everything_put_back(self):
        """A control: held past the wait, Delete stops as before, names the file in words, and the mod is as it was."""
        before = tree(self.folder)
        f = open(self.folder / anim.UNITS, "rb")
        self.addCleanup(f.close)
        with quick(), self.assertRaisesRegex(StudioError, "units.toml couldn't be read or written, because another "
                                                          "program has it open"):
            self.api.delete_unit(SUPER)
        self.assertEqual(tree(self.folder), before)
        self.assertIn(SUPER, ModEdits(self.folder).new_units)

    def test_the_board_s_take_outs_pass_it_on(self):
        said = {"deleted": "$/X", "waiting": ["files/cards/X.png"]}
        with mock.patch.object(StudioApi, "_board_read", return_value=(None, {"$/X": {"new": True}})), \
                mock.patch.object(StudioApi, "delete_unit", return_value=said), \
                mock.patch.object(StudioApi, "board", return_value={"rows": []}):
            self.assertEqual(self.api.board_take_out(0, "$/X")["waiting"], ["files/cards/X.png"])
        ix = mock.Mock()
        with mock.patch.object(StudioApi, "_board_need_mod", return_value=None), \
                mock.patch.object(StudioApi, "_open", return_value=ix), \
                mock.patch.object(StudioApi, "_board_building_list",
                                  return_value=[{"address": "$/X", "new": True, "kind": "none", "name": "X"}]), \
                mock.patch.object(StudioApi, "_board_info", return_value={}), \
                mock.patch.object(StudioApi, "delete_unit", return_value=said), \
                mock.patch.object(StudioApi, "board", return_value={"rows": []}):
            self.assertEqual(self.api.board_remove_building(0, "$/X")["waiting"], ["files/cards/X.png"])


class TheWords(unittest.TestCase):
    """The one line the page says, in 11 languages, naming the buttons as the page does."""

    @classmethod
    def setUpClass(cls):
        cls.words = tomllib.loads((SRC / "words.toml").read_text(encoding="utf-8"))
        cls.app = (SRC / "ui" / "app.js").read_text(encoding="utf-8")
        cls.board = (SRC / "ui" / "board.js").read_text(encoding="utf-8")

    def test_in_eleven_languages_with_their_blank_and_the_buttons_named_as_the_page_does(self):
        for key, blank in (("unit_deleted_waiting_one", "{file}"), ("unit_deleted_waiting_many", "{files}")):
            self.assertEqual(sorted(self.words[key]), sorted(LANGS), key)
            for lang in LANGS:
                with self.subTest(key=key, lang=lang):
                    text = self.words[key][lang]
                    self.assertEqual(re.findall(r"\{\w+\}", text), [blank])
                    self.assertIn(self.words["test_in_game"][lang], text)
                    self.assertIn(self.words["export_mod"][lang], text)

    def test_said_after_delete_take_it_out_and_the_board(self):
        told = self.app[self.app.index("function researchTold"):]
        told = told[:told.index("\n}\n")]
        self.assertIn("const waiting = waitingTold(res);", told)
        self.assertIn("if (waiting) lines.push(waiting);", told)
        self.assertIn("const waiting = waitingTold(res);", self.board)
        self.assertIn("if (waiting) more.push(waiting);", self.board)

    def test_the_page_s_own_code_picks_the_line(self):
        """waitingTold and fill as app.js has them, run in Node with the words as the page gets them."""
        tools = Path("D:/RUSE-2.0/tools")
        node = os.environ.get("RUSE_NODE") or shutil.which("node") or next(
            (str(p) for p in sorted(tools.glob("node-v*/node.exe"))[-1:]), None) if tools.is_dir() else None
        if not node:
            self.skipTest("no Node")

        def function(name: str) -> str:
            start = self.app.index(f"function {name}(")
            return self.app[start:self.app.index("\n}\n", start) + 2]
        words = {k: self.words[k]["fr"] for k in ("unit_deleted_waiting_one", "unit_deleted_waiting_many")}
        script = (function("fill") + function("waitingTold") + f"const state = {{ words: {json.dumps(words)} }};\n"
                  "console.log(JSON.stringify([waitingTold({ waiting: [] }), waitingTold({}),"
                  " waitingTold({ waiting: ['files/cards/A.png'] }), waitingTold({ waiting: ['a', 'b'] })]));\n")
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            f = Path(d) / "told.js"
            f.write_text(script, encoding="utf-8")
            out = subprocess.run([node, str(f)], capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        got = json.loads(out.stdout)
        self.assertEqual(got[:2], [None, None])
        self.assertEqual(got[2], words["unit_deleted_waiting_one"].replace("{file}", "files/cards/A.png"))
        self.assertEqual(got[3], words["unit_deleted_waiting_many"].replace("{files}", "a, b"))


if __name__ == "__main__":
    unittest.main()
