"""RUSE Decoy's copies of an animation (the owner, 2026-11-13: "a way to copy an animation so that way you can change an
animation and implement it into like certain models and soldiers"; his "sounds good go" to the way proposed, the same
day): rusemod.anim's files/anim/copies.toml written and read back, refused when the build couldn't take it; the build
playing a copy on the units, or only the soldiers of a unit, ticked for it and nowhere else, a unit's own rows still
winning and every tick that plays nothing said (test_anim's made-up game, the real build); a copied unit ticked where
its source is, a deleted unit unticked (the Studio's Delete too); the Studio's calls (ruse_studio.decoycopies) making,
changing, ticking, renaming and deleting a copy, where a copy starts (every unit's change, the unit's own copy, its own
animation from Blender, another copy), its refusals in words in eleven languages; and RUSE Decoy's page (decoy.js): a
tooltip on every new control, every word in eleven languages and on the stand-in page, every call the Studio's and the
stand-in page's. Nothing here was tried in the game."""
import os
import re
import sqlite3
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

import test_anim   # (the module, not its test classes: those run in test_anim once)
from rusemod import anim, baf
from rusemod.edat import Edat
from test_anim import E, FILE_OF, HORSE, RUN, STAND, clip
from test_decoy import SQUAD, UnitCalls

B = "\\"
UI = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"
LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")
BLANK = re.compile(r"\{(\w+)\}")


def copy_toml(cid: str, name: str, member: str, units: dict, extra: str = "") -> str:
    """One copy's table as RUSE Decoy writes it."""
    out = f'[copy.{cid}]\nname = "{name}"\nclip = "{anim.clip_key(member)}"\n{extra}'
    if units:
        out += f"[copy.{cid}.units]\n" + "".join(
            f"{u} = [{', '.join(chr(34) + f + chr(34) for f in figs)}]\n" for u, figs in units.items())
    return out


# --- the file -------------------------------------------------------------------------------------------------------
class TheFile(unittest.TestCase):
    def test_written_and_read_back(self):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d)
            (mod / anim.COPY_DIR).mkdir(parents=True)
            (mod / anim.COPY_DIR / "fast.baf").write_bytes(baf.build(clip()))
            far = "GfxDescriptorIcone.PawnDescriptor.DescriptorFigurine"
            anim.write_copies(mod, {"fast": {
                "name": 'Fast "run" à la française', "clip": anim.clip_key(STAND), "speed": 150.0,
                "from": anim.clip_key(RUN), "file": "fast.baf", "bone": {"bip01 head": {"size": 2.0, "turn": ["z", 30.0]}},
                "units": {"Descriptor_Unit_A": [], "Descriptor_Unit_B": ["GfxDescriptorBazooka", far]}}})
            got = anim.mod_copies(mod)["fast"]
            self.assertEqual((got["name"], got["clip"]), ('Fast "run" à la française', STAND))
            self.assertEqual((got["edit"]["speed"], got["edit"]["from"], got["edit"]["file"]),
                             (150.0, RUN, mod / anim.COPY_DIR / "fast.baf"))
            self.assertEqual(got["edit"]["bones"], {"bip01 head": {"size": 2.0, "turn": ("z", 30.0)}})
            self.assertEqual(got["units"], {"Descriptor_Unit_A": (), "Descriptor_Unit_B": ("GfxDescriptorBazooka", far)})
            self.assertEqual(anim.read_copies(mod)["fast"]["units"]["Descriptor_Unit_A"], [])
            anim.write_copies(mod, {})                                    # none left: no file
            self.assertFalse((mod / anim.COPIES).exists())
            self.assertEqual(anim.mod_copies(mod), {})

    def test_refused(self):
        good = copy_toml("x", "X", STAND, {})
        for text in ('[copy."Bad Id"]\nname = "X"\nclip = "a.baf"\n', '[copy.x]\nclip = "a.baf"\n',
                     '[copy.x]\nname = ""\nclip = "a.baf"\n', '[copy.x]\nname = "X\\u0001"\nclip = "a.baf"\n',
                     f'[copy.x]\nname = "{"x" * 81}"\nclip = "a.baf"\n', '[copy.x]\nname = "X"\nclip = "a.txt"\n',
                     good + "speed = 0\n", good + 'file = "../escape.baf"\n', good + 'file = "missing.baf"\n',
                     good + "colour = 1\n", good + '[copy.x.units]\n"Not a unit" = []\n',
                     good + '[copy.x.units]\nDescriptor_Unit_A = "GfxDescriptorBazooka"\n',
                     good + '[copy.x.units]\nDescriptor_Unit_A = ["F", "F"]\n', "other = 1\n"):
            with tempfile.TemporaryDirectory() as d, self.subTest(text=text):
                f = Path(d) / anim.COPIES
                f.parent.mkdir(parents=True)
                f.write_text(text, encoding="utf-8")
                with self.assertRaises(anim.AnimError):
                    anim.mod_copies(Path(d))
        with tempfile.TemporaryDirectory() as d:   # nothing the build wouldn't take is written: the old file stays
            anim.write_copies(Path(d), {"x": {"name": "X", "clip": anim.clip_key(STAND)}})
            before = (Path(d) / anim.COPIES).read_bytes()
            with self.assertRaises(anim.AnimError):
                anim.write_copies(Path(d), {"x": {"name": "X", "clip": anim.clip_key(STAND), "speed": 5000}})
            self.assertEqual((Path(d) / anim.COPIES).read_bytes(), before)

    def test_ids(self):
        self.assertEqual(anim.copy_id("Fast run!", set()), "fast_run")
        self.assertEqual(anim.copy_id("Fast run", {"fast_run", "fast_run_2"}), "fast_run_3")
        self.assertEqual(anim.copy_id("Быстрый бег", set()), "copy")
        self.assertEqual(anim.copy_id("x" * 60, set()), "x" * 32)


class UnitsAndTicks(unittest.TestCase):
    """A copied unit is ticked where its source is (the owner, 2026-11-10: "They should have the same animation"); a unit
    taken out of the mod is unticked everywhere (a tick for a unit no mod makes stops the build)."""

    def mod(self, d) -> Path:
        mod = Path(d)
        (mod / anim.COPIES).parent.mkdir(parents=True)
        (mod / anim.COPIES).write_text(copy_toml("x", "X", STAND, {"Descriptor_Unit_A": [],
                                                                   "Descriptor_Unit_B": ["GfxDescriptorBazooka"]}),
                                       encoding="utf-8")
        return mod

    def test_a_copied_unit_is_ticked_where_its_source_is(self):
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d)
            self.assertTrue(anim.copy_unit(mod, "Descriptor_Unit_B", "Descriptor_Unit_C"))
            self.assertEqual(anim.mod_copies(mod)["x"]["units"], {"Descriptor_Unit_A": (),
                                                                  "Descriptor_Unit_B": ("GfxDescriptorBazooka",),
                                                                  "Descriptor_Unit_C": ("GfxDescriptorBazooka",)})
            self.assertFalse((mod / anim.UNITS).exists())             # (no rows of its own to take along)
            self.assertFalse(anim.copy_unit(mod, "Descriptor_Unit_Z", "Descriptor_Unit_Y"))   # nothing to take
            # with rows of its own too: both go along
            anim.add_unit_clip(mod, "Descriptor_Unit_A", "t_stand", baf.build(clip()))
            self.assertTrue(anim.copy_unit(mod, "Descriptor_Unit_A", "Descriptor_Unit_D"))
            self.assertIn("Descriptor_Unit_D", anim.mod_unit_clips(mod))
            self.assertEqual(anim.mod_copies(mod)["x"]["units"]["Descriptor_Unit_D"], ())

    def test_a_unit_taken_out_is_unticked(self):
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d)
            anim.remove_unit(mod, "Descriptor_Unit_A")
            self.assertEqual(anim.mod_copies(mod)["x"]["units"], {"Descriptor_Unit_B": ("GfxDescriptorBazooka",)})
            self.assertEqual(anim.ticked_in(mod, "Descriptor_Unit_B"), ["x"])
            self.assertEqual(anim.untick_unit(mod, "Descriptor_Unit_B"), ["x"])
            self.assertEqual(anim.mod_copies(mod)["x"]["units"], {})   # the copy stays, ticked for no unit
            self.assertEqual(anim.untick_unit(mod, "Descriptor_Unit_B"), [])

    def test_the_studio_s_delete_unticks_all_or_nothing(self):
        from ruse_studio.edits import ModEdits, TakeOut
        with tempfile.TemporaryDirectory() as d:
            mod = self.mod(d)
            before = (mod / anim.COPIES).read_bytes()
            take = TakeOut(mod)
            gone = ModEdits(mod)._take_files("Descriptor_Unit_A", take)
            self.assertEqual(gone, [f"{anim.COPIES} [copy.x.units] Descriptor_Unit_A"])
            self.assertNotIn("Descriptor_Unit_A", anim.mod_copies(mod)["x"]["units"])
            take.put_back()                                             # a later step failing: all as it was
            self.assertEqual((mod / anim.COPIES).read_bytes(), before)

    def test_a_mistake_in_the_file_named_when_a_delete_stops(self):
        from ruse_studio.api import StudioApi, StudioError
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d)
            (mod / anim.COPIES).parent.mkdir(parents=True)
            (mod / anim.COPIES).write_text("[copy.x]\nname = 1\n", encoding="utf-8")
            try:
                anim.ticked_in(mod, "Descriptor_Unit_A")
                anim.mod_copies(mod)
            except anim.AnimError as exc:
                said = StudioApi._take_error(mock.Mock(), exc, mod)
            self.assertIsInstance(said, StudioError)
            self.assertIn(str(mod / anim.COPIES), str(said))           # the copies' file, never units.toml
            self.assertNotIn(anim.UNITS, str(said).replace(anim.COPIES, ""))


# --- the build (test_anim's made-up game: Descriptor_Unit_Squad, a rifleman and a bazooka man; Descriptor_Unit_Other) --
class CopiesInTheBuild(unittest.TestCase):
    game = test_anim.OneUnitsOwn.game
    mod = test_anim.OneUnitsOwn.mod
    build = test_anim.OneUnitsOwn.build
    copy = test_anim.OneUnitsOwn.copy
    listings = staticmethod(test_anim.OneUnitsOwn.listings)
    game_clips_kept = test_anim.OneUnitsOwn.game_clips_kept
    HORSE_SQUAD = f"export Descriptor_Unit_Horse_Squad is clone {E}Descriptor_Unit_Squad ( )\n"

    def new_files(self, zz) -> list:
        had = {e.path.lower() for e in Edat(self.zz).entries}
        return sorted(e.path.lower() for e in zz.entries if e.path.lower() not in had)

    def test_a_copy_plays_on_the_units_ticked_and_nowhere_else(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            text = copy_toml("fast_stand", "Fast stand", STAND, {"Descriptor_Unit_Horse_Squad": [],
                                                                  "Descriptor_Unit_Other": ["GfxDescriptorFusilier"]},
                             "speed = 200\n")
            code, said = self.build(d, game, self.mod(d, rndf=self.HORSE_SQUAD, files={anim.COPIES: text.encode()}))
            self.assertEqual(code, 0, said)
            stem = "own_copy_fast_stand_fusilier_standlod0"
            zz, objects = self.copy(d)
            self.assertEqual(self.new_files(zz), [anim.own_member(stem)])               # one clip, made once
            self.assertEqual(bytes(zz.read(zz.entry(anim.own_member(stem)))),
                             baf.build(baf.with_speed(baf.parse(self.stand), 200)))
            self.game_clips_kept(zz)
            mine = anim.own_data_name(stem)
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Horse_Squad"),
                             {"t_stand": mine, "b_stand": mine, "t_course": FILE_OF[RUN]})
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Horse_Squad", "GfxDescriptorBazooka"),
                             {"t_stand": mine, "t_course": FILE_OF[RUN]})
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Other"), {"t_stand": mine, "t_course": FILE_OF[RUN]})
            from rusemod.build import load_pack
            before = load_pack(Edat(self.units)).base.objects
            self.assertEqual(objects[E + "Descriptor_Unit_Squad"], before[E + "Descriptor_Unit_Squad"])  # untouched
            shared = [n for n, o in before.items() if o.cls == "TGfxDescriptorAnimation"]
            self.assertEqual([objects[n] for n in shared], [before[n] for n in shared])
            self.assertIn(f"the copy Fast stand (fast_stand) of {anim.clip_key(STAND)} plays on 4 listing(s)", said)
            self.assertIn("Descriptor_Unit_Horse_Squad (3), Descriptor_Unit_Other (1)", said)

    def test_only_the_soldier_ticked(self):
        # the game's own squad, its bazooka man alone: its riflemen and a copy of it made in the mod keep the game's
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            text = copy_toml("slow", "Slow", STAND, {"Descriptor_Unit_Squad": ["GfxDescriptorBazooka"]}, "speed = 50\n")
            code, said = self.build(d, game, self.mod(d, rndf=self.HORSE_SQUAD, files={anim.COPIES: text.encode()}))
            self.assertEqual(code, 0, said)
            zz, objects = self.copy(d)
            mine = anim.own_data_name("own_copy_slow_fusilier_standlod0")
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Squad", "GfxDescriptorBazooka")["t_stand"], mine)
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Squad"),
                             {"t_stand": FILE_OF[STAND], "b_stand": FILE_OF[STAND], "t_course": FILE_OF[RUN]})
            for unit in ("Descriptor_Unit_Horse_Squad", "Descriptor_Unit_Other"):
                for fig in ("GfxDescriptorFusilier", "GfxDescriptorBazooka")[:2 if unit != "Descriptor_Unit_Other" else 1]:
                    self.assertEqual(self.listings(objects, unit, fig)["t_stand"], FILE_OF[STAND], (unit, fig))
            self.assertIn("plays on 1 listing(s)", said)

    def test_two_copies_of_one_clip(self):
        # the whole squad on one copy, its bazooka man on another: the copy ticked for him wins for him
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            text = (copy_toml("all_of_it", "All of it", STAND, {"Descriptor_Unit_Squad": []}, "speed = 200\n")
                    + copy_toml("his", "His", STAND, {"Descriptor_Unit_Squad": ["GfxDescriptorBazooka"]}, "speed = 50\n"))
            code, said = self.build(d, game, self.mod(d, files={anim.COPIES: text.encode()}))
            self.assertEqual(code, 0, said)
            zz, objects = self.copy(d)
            whole, his = "own_copy_all_of_it_fusilier_standlod0", "own_copy_his_fusilier_standlod0"
            self.assertEqual(self.new_files(zz), sorted([anim.own_member(whole), anim.own_member(his)]))
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Squad")["t_stand"], anim.own_data_name(whole))
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Squad", "GfxDescriptorBazooka")["t_stand"],
                             anim.own_data_name(his))
            self.assertAlmostEqual(baf.parse(bytes(zz.read(zz.entry(anim.own_member(his))))).duration,
                                   baf.parse(self.stand).duration * 2)

    def test_the_unit_s_own_wins_and_is_said(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            units = f'[unit.Descriptor_Unit_Horse_Squad.clip."{anim.clip_key(STAND)}"]\nspeed = 300\n'
            text = copy_toml("fast", "Fast", STAND, {"Descriptor_Unit_Horse_Squad": []}, "speed = 200\n")
            code, said = self.build(d, game, self.mod(d, rndf=self.HORSE_SQUAD, units=units,
                                                      files={anim.COPIES: text.encode()}))
            self.assertEqual(code, 0, said)
            self.assertIn(f"Descriptor_Unit_Horse_Squad has its own copy of {anim.clip_key(STAND)} "
                          f"({anim.UNITS}), which it plays instead", said)
            self.assertIn("the copy Fast (fast): nothing plays it, so it isn't made", said)
            zz, objects = self.copy(d)
            self.assertEqual(self.new_files(zz), [anim.own_member("own_horse_squad_fusilier_standlod0")])
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Horse_Squad")["t_stand"],
                             anim.own_data_name("own_horse_squad_fusilier_standlod0"))

    def test_what_the_build_says(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            text = (copy_toml("pilot", "Pilot", STAND, {"Descriptor_Unit_Squad": ["GfxDescriptorPilot"]})
                    + copy_toml("horse", "Horse", HORSE, {"Descriptor_Unit_Squad": []})
                    + copy_toml("lonely", "Lonely", STAND, {}))
            mod = self.mod(d, files={anim.COPIES: text.encode()})
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            self.assertIn("the copy Pilot (pilot): Descriptor_Unit_Squad has no figure GfxDescriptorPilot", said)
            self.assertIn(f"the copy Horse (horse): Descriptor_Unit_Squad plays no {anim.clip_key(HORSE)}", said)
            self.assertIn("the copy Lonely (lonely) is ticked for no unit, so nothing plays it and it isn't made", said)
            self.assertIn("The mods change nothing in these packs.", said)   # nothing named them: no file of a copy
            self.assertFalse(Path(d, "copy").exists())
            # a unit nothing makes: the build stops, and says what to do
            (mod / anim.COPIES).write_text(copy_toml("x", "X", STAND, {"Descriptor_Unit_Nobody": []}), encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertNotEqual(code, 0)
            self.assertIn("it is ticked for a unit Descriptor_Unit_Nobody, which no mod in the set makes", said)
            self.assertIn("untick it under Who plays it in RUSE Decoy", said)

    def test_a_copy_with_a_clip_of_its_own(self):
        # (a motion capture's, or one from a unit's Blender change): its speed on top
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            own = baf.build(clip(lift=5.0))
            text = copy_toml("dance", "Dance", STAND, {"Descriptor_Unit_Other": []}, 'speed = 150\nfile = "dance.baf"\n')
            code, said = self.build(d, game, self.mod(d, files={anim.COPIES: text.encode(),
                                                                f"{anim.COPY_DIR}/dance.baf": own}))
            self.assertEqual(code, 0, said)
            zz, objects = self.copy(d)
            stem = "own_copy_dance_fusilier_standlod0"
            self.assertEqual(bytes(zz.read(zz.entry(anim.own_member(stem)))),
                             baf.build(baf.with_speed(baf.parse(own), 150)))
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Other")["t_stand"], anim.own_data_name(stem))

    def test_a_copy_ticked_for_no_unit_builds_as_before(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            mod = self.mod(d, rndf=self.HORSE_SQUAD)
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            data = Path(d, "copy", "Data", "PC", "190852")
            first = {n: (data / n).read_bytes() for n in ("ZZ_Win.dat", "ZZ_GladPatchableWin.dat")}
            (mod / anim.COPIES).parent.mkdir(parents=True, exist_ok=True)
            (mod / anim.COPIES).write_text(copy_toml("x", "X", STAND, {}, "speed = 200\n"), encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            self.assertEqual({n: (data / n).read_bytes() for n in first}, first)


# --- the Studio's calls (test_decoy's made-up game and index, with a second squad and a new unit) --------------------
OTHER = "$/GFX/Everything/Descriptor_Unit_Other"
TANK = "$/GFX/Everything/Descriptor_Unit_Tank"
HORSE_SQUAD = "$/GFX/Everything/Descriptor_Unit_Horse_Squad"
RUN_FILE = "WW2\\Res3D\\Units\\Common\\Fusilier_courselod0.Ase2NdfBin"


class CopyCalls(UnitCalls):
    """UnitCalls (test_decoy) with a fuller index: Descriptor_Unit_Squad's rifleman and bazooka man both play the run
    (t_course, one listing object they share), Descriptor_Unit_Other's rifleman too, a tank plays nothing; the mod has
    Descriptor_Unit_Horse_Squad, a copy of the squad. units() names them as the Units tab does."""

    def __init__(self, d):
        super().__init__(d)
        self.db.close()   # (UnitCalls' own index: this one takes its place)
        db = sqlite3.connect(":memory:")
        db.executescript(f"""
            CREATE TABLE object(id INTEGER PRIMARY KEY, class TEXT, shadow INTEGER, address TEXT, export TEXT);
            CREATE TABLE value(object INTEGER, path TEXT, num REAL, text TEXT);
            CREATE TABLE ref(src INTEGER, path TEXT, kind TEXT, dst INTEGER, target TEXT);
            INSERT INTO object VALUES (1, 'TInfanterieDescriptor', 0, '{SQUAD}', NULL),
                (2, 'TGfxDescriptorBiped', 0, '{SQUAD}:GfxDescriptorFusilier', NULL),
                (3, 'TGfxDescriptorAnimation', 0, '{SQUAD}:GfxDescriptorFusilier.ResourceAnimation[0].v', NULL),
                (4, 'TGfxDescriptorBiped', 0, '{SQUAD}:GfxDescriptorBazooka', NULL),
                (5, 'TInfanterieDescriptor', 0, '{OTHER}', NULL),
                (6, 'TGfxDescriptorBiped', 0, '{OTHER}:GfxDescriptorFusilier', NULL),
                (7, 'TUniteAuSolDescriptor', 0, '{TANK}', NULL);
            INSERT INTO ref VALUES (1, 'GfxDescriptorFusilier', 'object', 2, NULL),
                (2, 'ResourceAnimation[0].v', 'object', 3, NULL), (1, 'GfxDescriptorBazooka', 'object', 4, NULL),
                (4, 'ResourceAnimation[0].v', 'object', 3, NULL), (5, 'GfxDescriptorFusilier', 'object', 6, NULL),
                (6, 'ResourceAnimation[0].v', 'object', 3, NULL);
            INSERT INTO value VALUES (2, 'ResourceAnimation[0].k', NULL, 't_course'),
                (4, 'ResourceAnimation[0].k', NULL, 't_course'), (6, 'ResourceAnimation[0].k', NULL, 't_course'),
                (3, 'FileName', NULL, '{RUN_FILE}');
        """)
        self.db = db

    def _path(self):
        return "made-up index"

    def _resolve(self, edits, address):
        return (SQUAD, object()) if address == HORSE_SQUAD else (address, None)

    def _decoy_clip_row(self, member):
        r = super()._decoy_clip_row(member)
        return {**r, "units": [SQUAD, OTHER]} if r else None

    def units(self, lang="base"):
        return {"units": [{"address": HORSE_SQUAD, "name": "Horse Squad", "new": True, "nation_name": "USA",
                           "kind": "infantry"},
                          {"address": SQUAD, "name": "Rifle squad", "new": False, "nation_name": "USA",
                           "kind": "infantry"},
                          {"address": OTHER, "name": "Grenadiers", "new": False, "nation_name": "Germany",
                           "kind": "infantry"},
                          {"address": TANK, "name": "Sherman", "new": False, "nation_name": "USA", "kind": "ground"}]}


class TheStudio(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.calls = CopyCalls(self.d.name)
        self.addCleanup(self.calls.db.close)
        self.mod = Path(self.d.name)
        self.run = UnitCalls._RUN

    def test_made_changed_ticked_and_read_by_the_build(self):
        c = self.calls
        self.assertEqual(c.decoy_copies(), {"copies": [], "mod": True})
        got = c.decoy_copy_make(self.run, "  Fast run ")
        self.assertEqual((got["copy"], got["name"], got["started"], got["units"], got["member"]),
                         ("fast_run", "Fast run", "game", 0, self.run))
        got = c.decoy_anim_set(self.run, speed=150, copy="fast_run")
        self.assertEqual((got["speed"], got["changed"]), (150.0, True))
        for f in (anim.CLIPS, anim.UNITS):                                  # every unit's and a unit's own: untouched
            self.assertFalse((self.mod / f).exists(), f)
        who = c.decoy_copy_players("fast_run")
        self.assertEqual([(u["address"], u["new"], u["ticked"]) for u in who["units"]],
                         [(HORSE_SQUAD, True, None), (SQUAD, False, None), (OTHER, False, None)])   # yours first
        self.assertEqual([(f["path"], f["kind"]) for f in who["units"][0]["figures"]],
                         [("GfxDescriptorFusilier", "rifle"), ("GfxDescriptorBazooka", "heavy")])
        self.assertEqual(who["unreached"], [])
        self.assertEqual(c.decoy_copy_tick("fast_run", HORSE_SQUAD, [])["moved"], [])
        c.decoy_copy_tick("fast_run", SQUAD, ["GfxDescriptorBazooka"])
        c.decoy_copy_tick("fast_run", OTHER, ["GfxDescriptorFusilier"])     # all of its figures: [] (every one)
        built = anim.mod_copies(self.mod)["fast_run"]                       # what the build reads
        self.assertEqual((built["name"], built["clip"], built["edit"]["speed"]), ("Fast run", self.run, 150.0))
        self.assertEqual(built["units"], {"Descriptor_Unit_Horse_Squad": (), "Descriptor_Unit_Squad":
                                          ("GfxDescriptorBazooka",), "Descriptor_Unit_Other": ()})
        who = c.decoy_copy_players("fast_run")
        self.assertEqual([u["ticked"] for u in who["units"]], ["all", "some", "all"])
        self.assertEqual([f["ticked"] for f in who["units"][1]["figures"]], [False, True])
        row = c.decoy_unit_anims(HORSE_SQUAD)["rows"][0]                    # the unit's page: it plays your copy
        self.assertEqual([(x["copy"], x["figures"]) for x in row["copies"]], [("fast_run", [])])
        self.assertEqual(c.decoy_unit_anims(SQUAD)["rows"][0]["copies"][0]["figures"], ["GfxDescriptorBazooka"])
        c.decoy_anim_preview(self.run, copy="fast_run")                     # watched as the copy is: 150%
        game = baf.parse(c.clips[self.run]).duration
        self.assertAlmostEqual(baf.parse(c.shown[-1]).duration, game / 1.5, places=4)
        c.decoy_copy_tick("fast_run", SQUAD, None)                          # unticked
        self.assertNotIn("Descriptor_Unit_Squad", anim.mod_copies(self.mod)["fast_run"]["units"])

    def test_a_soldier_plays_one_copy_of_a_clip(self):
        c = self.calls
        c.decoy_copy_make(self.run, "Whole squad")
        c.decoy_copy_make(self.run, "His")
        c.decoy_copy_tick("whole_squad", SQUAD, [])
        self.assertEqual(c.decoy_copy_tick("his", SQUAD, ["GfxDescriptorBazooka"])["moved"], ["Whole squad"])
        copies = anim.mod_copies(self.mod)
        self.assertEqual(copies["whole_squad"]["units"]["Descriptor_Unit_Squad"], ("GfxDescriptorFusilier",))
        self.assertEqual(copies["his"]["units"]["Descriptor_Unit_Squad"], ("GfxDescriptorBazooka",))
        who = {u["address"]: u for u in c.decoy_copy_players("whole_squad")["units"]}
        self.assertEqual([(f["ticked"], f["other"]) for f in who[SQUAD]["figures"]], [(True, None), (False, "His")])
        self.assertEqual(c.decoy_copy_tick("his", SQUAD, [])["moved"], ["Whole squad"])   # the whole squad now
        self.assertNotIn("Descriptor_Unit_Squad", anim.mod_copies(self.mod)["whole_squad"]["units"])

    def test_where_a_copy_starts(self):
        c = self.calls
        c.decoy_anim_set(self.run, speed=200)                               # every unit's change (clips.toml)
        got = c.decoy_copy_make(self.run, "As everyone")
        self.assertEqual((got["speed"], got["started"]), (200.0, "all"))
        c.decoy_anim_set(self.run, speed=300, unit=SQUAD)                   # the squad's own copy (Only this unit)
        got = c.decoy_copy_make(self.run, "As the squad", unit=SQUAD)
        self.assertEqual((got["speed"], got["started"]), (300.0, "own"))
        mine = baf.build(clip(lift=6.0))                                    # its own animation from Blender
        anim.add_unit_clip(self.mod, "Descriptor_Unit_Other", "t_course", mine, name="blender_run")
        got = c.decoy_copy_make(self.run, "As Blender made it", unit=OTHER)
        self.assertEqual((got["started"], got["mine"], got["speed"]), ("blender", True, 100.0))
        self.assertEqual((self.mod / anim.COPY_DIR / "as_blender_made_it.baf").read_bytes(), mine)
        got = c.decoy_copy_make(self.run, "Again", copy="as_the_squad")    # a copy of a copy
        self.assertEqual((got["speed"], got["started"]), (300.0, "copy"))
        for f in (anim.CLIPS, anim.UNITS):
            self.assertTrue((self.mod / f).is_file(), f)                    # (what it started from stays)
        self.assertEqual(anim.mod_clips(self.mod)[self.run]["speed"], 200.0)

    def test_only_this_unit_starts_as_the_copy_it_plays(self):
        # (Only this unit "starts as the animation this unit plays now": the copy its whole self is ticked in)
        c = self.calls
        c.decoy_anim_set(self.run, speed=200)                               # every unit's: not what it plays
        c.decoy_copy_make(self.run, "Fast run")
        c.decoy_anim_set(self.run, speed=150, copy="fast_run")
        c.decoy_copy_tick("fast_run", SQUAD, [])
        got = c.decoy_anim_set(self.run, bone="bip01 head", size=2.0, unit=SQUAD)
        self.assertEqual(got["own"]["speed"], 150.0)
        c.decoy_copy_tick("fast_run", OTHER, ["GfxDescriptorFusilier"])      # (every figure of Other: [])
        c.decoy_copy_tick("fast_run", HORSE_SQUAD, ["GfxDescriptorBazooka"])  # one soldier only: every unit's
        got = c.decoy_anim_set(self.run, bone="bip01 head", size=2.0, unit=HORSE_SQUAD)
        self.assertEqual(got["own"]["speed"], 200.0)

    def test_motion_capture_into_a_copy_and_back(self):
        from test_mocap import bvh_text
        c = self.calls
        c.decoy_copy_make(self.run, "Dance")
        c.decoy_copy_tick("dance", OTHER, [])
        mid = c.decoy_mocap_open("walk.bvh", bvh_text([{}] * 241))["id"]
        used = c.decoy_mocap_use(self.run, mid, 0.5, 1.0, True, None, "Me, CC0", None, "dance")
        self.assertTrue(used["mine"])
        own = self.mod / anim.COPY_DIR / "dance.baf"
        self.assertTrue(own.is_file() and own.with_suffix(".toml").is_file())     # the clip and its credit
        self.assertEqual(anim.mod_copies(self.mod)["dance"]["edit"]["file"], own)  # the build takes it
        for f in (anim.REPLACE, anim.OWN, anim.CLIPS, anim.UNITS):
            self.assertFalse((self.mod / f).exists(), f)                    # nothing else written
        back = c.decoy_anim_reset(self.run, copy="dance")                   # Back to the game's animation
        self.assertEqual((back["mine"], back["speed"], back["units"]), (False, 100.0, 1))   # still ticked
        self.assertFalse(own.exists() or own.with_suffix(".toml").exists())

    def test_renamed_and_deleted(self):
        c = self.calls
        c.decoy_copy_make(self.run, "Dance")
        c.decoy_copy_tick("dance", OTHER, [])
        self.assertEqual(c.decoy_copy_rename("dance", "Waltz")["name"], "Waltz")
        self.assertEqual(sorted(anim.mod_copies(self.mod)), ["dance"])      # (its id stays: its ticks and file too)
        mid = c.decoy_mocap_open("walk.bvh", __import__("test_mocap").bvh_text([{}] * 241))["id"]
        c.decoy_mocap_use(self.run, mid, 0.5, 1.0, True, None, "Me, CC0", None, "dance")
        got = c.decoy_copy_delete("dance")
        self.assertEqual((got["name"], got["units"]), ("Waltz", 1))
        self.assertFalse((self.mod / anim.COPIES).exists())
        self.assertFalse((self.mod / anim.COPY_DIR).exists())               # its file, credit and folder
        self.assertEqual(c.decoy_copies()["copies"], [])

    def test_refused_in_words(self):
        from ruse_studio import errortext
        from ruse_studio.api import StudioError
        c = self.calls
        c.decoy_copy_make(self.run, "Fast run")
        for call, said in (
                (lambda: c.decoy_copy_make(self.run, "fast RUN"), "This mod has a copy called fast RUN already"),
                (lambda: c.decoy_copy_make(self.run, "   "), "A copy's name is 1 to 80 letters."),
                (lambda: c.decoy_copy_rename("fast_run", "x" * 81), "A copy's name is 1 to 80 letters."),
                (lambda: c.decoy_copy_tick("fast_run", TANK, []), "This unit doesn't play this animation"),
                (lambda: c.decoy_copy_tick("fast_run", SQUAD, ["GfxDescriptorPilot"]),
                 "This unit has no soldier or part GfxDescriptorPilot that plays this animation."),
                (lambda: c.decoy_copy_tick("fast_run", SQUAD, "GfxDescriptorBazooka"), "Tick a unit, or some of"),
                (lambda: c.decoy_anim_set(self.run, speed=150, copy="gone"), "This mod has no copy gone any more"),
                (lambda: c.decoy_copy_delete("../x"), "This mod has no copy ../x any more")):
            with self.subTest(said=said):
                with self.assertRaises(StudioError) as cm:
                    call()
                self.assertIn(said, str(cm.exception))
                self.assertNotEqual(errortext.worded(str(cm.exception), "fr"), str(cm.exception))   # (and in French)
        (self.mod / anim.COPIES).write_text("[copy.x]\nname = 1\n", encoding="utf-8")   # a file with a mistake
        with self.assertRaises(StudioError) as cm:
            c.decoy_copies()
        self.assertIn("Fix that file (or delete it) first: your copies of animations are kept there.", str(cm.exception))
        with mock.patch.object(c, "_mod_dir", return_value=None):          # no mod
            self.assertEqual(c.decoy_copies(), {"copies": [], "mod": False})
            with self.assertRaises(StudioError) as cm:
                c.decoy_copy_make(self.run, "Y")
            self.assertIn("Pick or make a mod first", str(cm.exception))


# --- the page (decoy.js) --------------------------------------------------------------------------------------------
def js_function(js: str, name: str) -> str:
    """One of decoy.js's functions (inside its one wrapping function), to the next one."""
    m = re.search(rf"^  (?:async )?function {name}\(", js, re.M)
    if m is None:
        raise AssertionError(f"no function {name}")
    nxt = re.search(r"^  (?:async function |function |const |window\.)", js[m.end():], re.M)
    return js[m.start(): m.end() + (nxt.start() if nxt else len(js) - m.end())]


def controls(js: str) -> list:
    """The option braces of every button, select and input the code makes."""
    out = []
    for m in re.finditer(r'el\("(?:button|input|select)", \{', js):
        depth, at = 0, m.end() - 1
        for at in range(m.end() - 1, len(js)):
            depth += {"{": 1, "}": -1}.get(js[at], 0)
            if depth == 0:
                break
        out.append(js[m.end():at])
    return out


NEW = ("copiesList", "copyRow", "copyBox", "copyForm", "whoBox", "whoDraw", "whoUnit", "whoTick", "scopeChoice",
       "kinds", "list", "animRow", "openAnim", "animControls", "saveAnim", "mocapUse", "wire")


class ThePage(unittest.TestCase):
    def setUp(self):
        self.js = (UI / "decoy.js").read_text(encoding="utf-8")
        self.new = "".join(js_function(self.js, n) for n in NEW)

    def test_a_tooltip_on_every_control(self):
        made = controls(self.new)
        self.assertGreaterEqual(len(made), 12)
        self.assertEqual([c for c in made if "title" not in c], [])

    def test_every_word_in_eleven_languages_and_on_the_stand_in_page(self):
        words = tomllib.loads((UI.parent / "words.toml").read_text(encoding="utf-8"))
        fake = (UI / "fake-api.js").read_text(encoding="utf-8")
        used = set(re.findall(r"\bw\.(\w+)", self.new)) | set(re.findall(r"W\(\)\.(\w+)", self.js))
        used |= set(re.findall(r'"(fit_fig_\w+)"', self.js))                # (a figure's name, by its kind)
        mine = sorted(k for k in used if re.search(r"decoy_(copy|copies)|anim_for_copy|mc_used_copy", k))
        self.assertGreaterEqual(len(mine), 40)
        for key in sorted(used):
            with self.subTest(key=key):
                self.assertIn(key, words)
                self.assertEqual(set(words[key]), set(LANGS))
                for lang in LANGS:
                    self.assertTrue(words[key][lang].strip(), lang)
                    self.assertEqual(sorted(BLANK.findall(words[key][lang])), sorted(BLANK.findall(words[key]["us"])),
                                     lang)
        for key in mine:
            self.assertRegex(fake, rf"\b{key}: \"", key)                    # (the stand-in page, index.html?fake)

    def test_every_call_is_the_studio_s_and_the_stand_in_page_s(self):
        from ruse_studio.api import StudioApi
        fake = (UI / "fake-api.js").read_text(encoding="utf-8")
        calls = set(re.findall(r"api\(\)\.(\w+)\(", self.js))
        self.assertTrue({"decoy_copies", "decoy_copy_make", "decoy_copy_rename", "decoy_copy_delete",
                         "decoy_copy_players", "decoy_copy_tick"} <= calls, calls)
        self.assertEqual(sorted(x for x in calls if not callable(getattr(StudioApi, x, None))), [])
        self.assertEqual(sorted(x for x in calls if not re.search(rf"\b{x}: async", fake)), [])

    def test_the_editor_s_calls_carry_the_copy(self):
        # (the editor's own: the list rows' Back to the game's is every unit's, as before)
        for fn, call in (("saveAnim", "decoy_anim_set("), ("showClip", "decoy_anim_preview("),
                         ("mocapUse", "decoy_mocap_use("), ("wire", "decoy_anim_reset("),
                         ("copyForm", "decoy_copy_make(")):
            text = js_function(self.js, fn)
            at = text.index("api()." + call)
            self.assertIn("D.copy", text[at:text.index(";", at)], fn)
        self.assertIn('id="da-copy"', (UI / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
