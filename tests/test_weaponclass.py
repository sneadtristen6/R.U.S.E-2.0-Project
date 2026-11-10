"""An ammunition's own weapon class (ruse_studio.weaponclass, "New weapon class" on the ammo page), on a made-up game: a table of damage
numbers every ammunition links to, stored out of order as the game's is, and two ammunitions that share it."""
import struct
import tempfile
import tomllib
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat
from rusemod.build import build_pack, load_mod, load_pack
from rusemod.gamepatch import EXE
from rusemod.index import build_index
from rusemod.patch import Engine
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import Link, ModEdits
from ruse_studio.weaponclass import LEVELS, PREFIX

ROOT = Path(__file__).resolve().parents[1]
E = "$/GFX/Everything/"
RIFLE, SHELL = E + "Ammo_Rifle", E + "Ammo_Shell"
P_ID, P_ARME, P_POWER, P_STRESS, P_VALUES = range(5)


def i32(v):
    return val(0x02, struct.pack("<i", v))


def u32(v):
    return val(0x03, struct.pack("<I", v))


def f32(v):
    return val(0x05, struct.pack("<f", v))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def row(*numbers):
    return val(0x11, struct.pack("<I", len(numbers)) + b"".join(f32(n) for n in numbers))


def table(*rows):
    return val(0x12, struct.pack("<I", len(rows)) + b"".join(i32(k) + row(*numbers) for k, numbers in rows))


ZERO = [0.0] * 11
RIFLES = [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0]
SHELLS = [1.0, 0.0, 0.0, 1.0, 1.0, 0.25, 0.125, 0.5, 0.5, 0.5, 2.0]
UNITS = make_ndf(
    objects=[(0, [(P_ID, u32(1)), (P_POWER, f32(10)), (P_STRESS, ref(2, 1))]),                     # 0 a rifle (class 0: absent)
             (0, [(P_ID, u32(2)), (P_ARME, i32(3)), (P_POWER, f32(90)), (P_STRESS, ref(2, 1))]),   # 1 a shell (class 3)
             (1, [(P_VALUES, table((3, SHELLS), (2, ZERO), (0, RIFLES), (1, ZERO)))])],           # 2 the table, out of order
    classes=["TAmmunition", "TFloatArmeArmureContainer"],
    props=[("AmmunitionId", 0), ("Arme", 0), ("Puissance", 0), ("StressManager", 0), ("Values", 1)],
    exports={0: "GFX/Everything/Ammo_Rifle", 1: "GFX/Everything/Ammo_Shell"},
    topo=[0, 1])


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "everything.cpp.gladndfbin", UNITS)]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("file", "placeholder.bin", b"x")]))


class WeaponClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        (cls.game / EXE).write_bytes(b"MZ")
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: True,
                          wait=lambda s: None)
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home, starter=starter,
                             instances=self.home / "copies")

    def mod(self):
        return Path(self.api.new_mod("Classes")["current"])

    def built(self, folder):
        """The game's objects after the mod, as the build's patch engine leaves them (no errors)."""
        rev = self.game / "Data" / "PC" / "190852"
        arc = Edat((rev / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)], text_arc=Edat((rev / "ZZ_Win.dat").read_bytes()))
        self.assertEqual(result.errors, [])
        run = Engine(load_pack(arc, self.home / "cache").base).run([load_mod(folder)])
        self.assertEqual([f.message for f in run.findings if f.level == "error"], [])
        return run.game.objects

    @staticmethod
    def row_of(obj, klass):
        """A table object's row for weapon class `klass`, as floats."""
        pair = next(v for k, v in obj.props["Values"].pairs if int(k.value) == klass)
        assert all(n.kind == "float32" for n in pair.items), [n.kind for n in pair.items]  # the game reads float32
        return [float(n.value) for n in pair.items]

    def test_a_page_shows_the_ammo_s_own_row_of_the_table(self):
        self.mod()
        info = self.api.weapon_class(RIFLE)            # class 0: Arme is absent from the rifle
        self.assertEqual([l["value"] for l in info["levels"]], RIFLES)
        self.assertEqual(len(info["levels"]), len(LEVELS))
        self.assertFalse(info["own"])
        self.assertEqual([l["value"] for l in self.api.weapon_class(SHELL)["levels"]], SHELLS)  # stored first, class 3

    def test_every_level_is_named_in_every_language(self):
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        langs = set(words["armour_trucks"])
        for word in {w for w, _n in LEVELS}:
            self.assertEqual(set(words[word]), langs, word)
        for key in ("title", "new", "edit", "help", "save", "back", "saved", "backed"):
            self.assertEqual(set(words["weapon_class_" + key]), langs, key)
        for key in ("new", "number", "save", "back"):
            self.assertEqual(set(words["tip_weapon_class_" + key]), langs, key)

    def test_only_this_ammo_gets_the_numbers_and_the_row_is_the_right_one(self):
        folder = self.mod()
        mine = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 10.0]
        info = self.api.weapon_class_set(RIFLE, mine)
        self.assertTrue(info["own"])
        self.assertEqual([l["value"] for l in info["levels"]], mine)
        self.assertEqual([l["game"] for l in info["levels"]], RIFLES)
        objects = self.built(folder)
        rifle, shell = objects[RIFLE], objects[SHELL]
        own = rifle.props["StressManager"].target
        shared = shell.props["StressManager"].target
        self.assertNotEqual(own, shared)
        self.assertEqual(self.row_of(objects[own], 0), mine)
        self.assertEqual(self.row_of(objects[own], 3), SHELLS)     # the other rows copied as they are
        self.assertEqual(self.row_of(objects[shared], 0), RIFLES)  # the game's table untouched

    def test_a_copy_of_an_ammo_can_have_a_class_of_its_own(self):
        folder = self.mod()
        copy = self.api.new_ammo(RIFLE, "Sabre")["address"]
        numbers = [0.0, 0.0, 0.0, 3.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0]
        self.api.weapon_class_set(copy, numbers)
        objects = self.built(folder)                                # the copy links to a table the file writes before it
        self.assertEqual(self.row_of(objects[objects[copy].props["StressManager"].target], 0), numbers)
        self.assertEqual(self.row_of(objects[objects[RIFLE].props["StressManager"].target], 0), RIFLES)

    def test_saving_again_replaces_the_numbers(self):
        folder = self.mod()
        self.api.weapon_class_set(RIFLE, [2.0] * 11)
        self.api.weapon_class_set(RIFLE, [0.5] * 11)
        objects = self.built(folder)
        self.assertEqual(self.row_of(objects[objects[RIFLE].props["StressManager"].target], 0), [0.5] * 11)
        self.assertEqual(sum(1 for t in ModEdits(folder).new_units if PREFIX in t), 1)

    def test_back_to_the_game_s_class_takes_the_table_out(self):
        folder = self.mod()
        self.api.weapon_class_set(RIFLE, [2.0] * 11)
        info = self.api.weapon_class_reset(RIFLE)
        self.assertFalse(info["own"])
        self.assertEqual([l["value"] for l in info["levels"]], RIFLES)
        edits = ModEdits(folder)
        self.assertEqual([t for t in edits.new_units if PREFIX in t], [])
        self.assertIsNone(edits.get(RIFLE, "StressManager"))

    def test_deleting_a_copy_takes_its_table_with_it(self):
        folder = self.mod()
        copy = self.api.new_ammo(RIFLE, "Sabre")["address"]
        self.api.weapon_class_set(copy, [2.0] * 11)
        self.api.delete_unit(copy)
        self.assertEqual([t for t in ModEdits(folder).new_units if PREFIX in t], [])

    def test_a_table_two_ammo_share_stays_until_the_last_one_goes(self):
        folder = self.mod()
        self.api.weapon_class_set(RIFLE, [2.0] * 11)
        table_at = next(t for t in ModEdits(folder).new_units if PREFIX in t)
        copy = self.api.new_ammo(SHELL, "Twin")["address"]
        edits = ModEdits(folder)
        edits.set(copy, "StressManager", Link(table_at))
        self.api.weapon_class_reset(RIFLE)
        self.assertIn(table_at, ModEdits(folder).new_units)

    def test_any_number_goes_and_anything_else_is_refused(self):
        self.mod()
        self.assertTrue(self.api.weapon_class_set(RIFLE, [-1.0, 1000000.0, 0.001, *[0.0] * 8])["own"])
        for bad in ([1.0] * 10, [1.0] * 12, ["1"] * 11, [float("nan")] * 11, [float("inf")] * 11, [True] * 11, None):
            with self.assertRaises(StudioError):
                self.api.weapon_class_set(RIFLE, bad)

    def test_it_needs_a_mod_and_an_ammunition(self):
        with self.assertRaises(StudioError):
            self.api.weapon_class_set(RIFLE, [1.0] * 11)
        self.mod()
        with self.assertRaises(StudioError):
            self.api.weapon_class(E + "Nothing_Here")


if __name__ == "__main__":
    unittest.main()
