"""The build lists' groups in the build (rusemod.build, rusemod.menulines; the owner, 2026-10-31: "We just need to limit
how many can be in a certain group. Because it's buggy.", a mod already over it built with a warning; 11-01: at most 10
groups a building): a mod's menu_groups.toml read with it (a bad one refused, naming the file), the mods' groups merged
in load order, a warning (never an error) for each group past 6 and each building past 10 groups, counted as the Studio
counts them, and the file carried wherever a mod folder is copied or packed. Made-up data, no game files."""
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

from fixtures import make_edat, make_ndf, val
from test_build import write_mod
from test_dic import make_dic
from rusemod import Edat, loc, menugroups, package
from rusemod.build import (BuildError, BuildResult, build_pack, load_mod, menu_group_limits, merged_groups,
                           needs_zz_win)
from rusemod.dic import name_to_key
from rusemod.library import Library, LibraryError
from rusemod.model import Obj
from rusemod.patch import Ref, Text, num, nums
from rusemod.resolve import ModInfo

G = "$/GFX/Everything/"
GERMANY, ARMOR, AIRFIELD = 1, 10, 9


def unit(name=None, factory=ARMOR, nation=GERMANY, upgrade=None, shows=None, slot=None, key=None,
         cls="TUniteAuSolDescriptor"):
    props = {"Factory": num(factory), "Nationalite": num(nation)}
    if name:
        props["ClassNameForDebug"] = Text("string", name)
    if key:
        props["NameInMenuToken"] = Text("key", key)
    if upgrade:
        props["IsUpgrade"] = num(1, "bool")
        props["UpgradeRequire"] = Ref(upgrade)
    if shows is not None:
        props["ShowInMenu"] = nums(shows)
    if slot is not None:
        props["PositionInMenu"] = num(slot)
    return Obj(cls, props)


def building(kind, nation=GERMANY, key=None):
    props = {"TypeBatiment": num(kind), "Nationalite": num(nation)}
    if key:
        props["NameInMenuToken"] = Text("key", key)
    return Obj("TBatimentDescriptor", props)


def copies(n, of=G + "Kub", **kw):
    """`n` new units, copies of `of` bought from the start: (objects, created)."""
    objects = {f"{G}N{k}": unit(f"Unit_N{k}", **kw) for k in range(1, n + 1)}
    return objects, {p: SimpleNamespace(kind="clone", source=of) for p in objects}


def said(objects, created=None, groups=None, zz=None, result=None):
    result = result or BuildResult()
    run = SimpleNamespace(game=SimpleNamespace(objects=objects), created=created or {})
    menu_group_limits(run, zz, groups or {}, result)
    if result.findings:
        assert {f.level for f in result.findings} == {"warning"}, result.findings
    return [f.message for f in result.findings]


GROUP = "the {} group in Germany's Armor Base holds {}: its build list may act up past 6"


class AGroupPastSix(unittest.TestCase):
    def test_seven_is_a_warning_and_six_is_not(self):
        new, created = copies(6)
        objects = {G + "Kub": unit("Unit_Kub"), **new}
        self.assertEqual(said(objects, created), [GROUP.format("Unit_Kub", 7)])
        objects.pop(G + "N6")
        created.pop(G + "N6")
        self.assertEqual(said(objects, created), [])

    def test_a_hidden_unit_is_not_counted(self):
        new, created = copies(6)
        objects = {G + "Kub": unit("Unit_Kub"), **new}
        objects[G + "N6"] = unit("Unit_N6", shows=[0, 0, 0, 0, 0])
        self.assertEqual(said(objects, created), [])
        objects[G + "N6"] = unit("Unit_N6", shows=[0, 0, 1, 0, 0])  # shown at one battle date: counted
        self.assertEqual(said(objects, created), [GROUP.format("Unit_Kub", 7)])

    def test_an_upgrade_is_one_place(self):
        """An upgrade's research card and its unit are one place: the Kub and five upgrades are six, not eleven."""
        objects = {G + "Kub": unit("Unit_Kub")}
        objects.update({f"{G}E{k}": unit(f"Unit_E{k}", upgrade=G + ("Kub" if k == 1 else f"E{k - 1}"))
                        for k in range(1, 6)})
        self.assertEqual(said(objects), [])
        objects[G + "E6"] = unit("Unit_E6", upgrade=G + "E5")
        self.assertEqual(said(objects), [GROUP.format("Unit_Kub", 7)])

    def test_each_nation_and_building_apart(self):
        new, created = copies(6)
        objects = {G + "Kub": unit("Unit_Kub"), **new}
        objects[G + "N1"] = unit("Unit_N1", nation=2)
        objects[G + "N2"] = unit("Unit_N2", factory=13)
        objects[G + "N3"] = unit("Unit_N3", factory=3)                # not a building that makes units
        objects[G + "Tab"] = unit(factory=ARMOR, cls="TMainMenuInfos")  # not a unit
        self.assertEqual(said(objects, created), [])

    def test_where_the_mods_groups_put_them(self):
        new, created = copies(6)
        objects = {G + "Kub": unit("Unit_Kub"), G + "Tiger": unit("Unit_Tiger"), **new}
        self.assertEqual(said(objects, created, {p: p for p in new}), [])  # each a group of its own
        self.assertEqual(said(objects, created, {p: G + "Tiger" for p in new}), [GROUP.format("Unit_Tiger", 7)])

    def test_named_as_the_studio_shows_the_group(self):
        """Copies of another nation's unit: the group's first unit isn't in that row, so the group stands under its
        first unit in the board's order (place number, then address), as the Studio shows it."""
        new, created = copies(7)
        new[G + "N5"] = unit("Unit_N5", slot=301)
        new[G + "N6"] = unit("Unit_N6", slot=305)
        objects = {G + "Kub": unit("Unit_Kub", nation=2), **new}
        self.assertEqual(said(objects, created), [GROUP.format("Unit_N5", 7)])


TEXTS = {"KUB": "PANZER IV", "ARMOR": "ARMOR BASE", "GUNS": "ARTILLERY &amp; ANTI-AIR BASE", "AIR": "AIRFIELD"}


def zz_win(texts=TEXTS):
    dic = make_dic([(name_to_key(k), v) for k, v in texts.items()])
    return Edat(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\us\\",
                            [("file", "baseunite.dic", dic)])]))


class NamedInEnglish(unittest.TestCase):
    def objects(self, factory=ARMOR):
        new, created = copies(6, factory=factory)
        return {G + "Kub": unit("Unit_Kub", key="KUB", factory=factory), **new,
                G + "Base": building(ARMOR, key="ARMOR"), G + "Guns": building(13, key="GUNS"),
                G + "BaseUS": building(ARMOR, nation=0)}, created

    def test_the_games_names(self):
        objects, created = self.objects()
        self.assertEqual(said(objects, created, zz=zz_win()),
                         ["the PANZER IV group in Germany's ARMOR BASE holds 7: its build list may act up past 6"])
        objects, created = self.objects(13)
        self.assertEqual(said(objects, created, zz=zz_win()),
                         ["the PANZER IV group in Germany's ARTILLERY & ANTI-AIR BASE holds 7: its build list may act "
                          "up past 6"])

    def test_the_mods_texts_as_the_build_wrote_them(self):
        objects, created = self.objects()
        zz = zz_win()
        result = BuildResult()
        member = zz.entry(loc.member("baseunite", "us")).path
        result.text_changed = {member: make_dic([(name_to_key(k), v) for k, v in
                                                 {**TEXTS, "KUB": "PANTHER"}.items()])}
        self.assertEqual(said(objects, created, zz=zz, result=result),
                         ["the PANTHER group in Germany's ARMOR BASE holds 7: its build list may act up past 6"])

    def test_without_the_texts(self):
        objects, created = self.objects()
        self.assertEqual(said(objects, created), [GROUP.format("Unit_Kub", 7)])
        objects, created = self.objects()
        self.assertEqual(said(objects, created, zz=zz_win({"AIR": "AIRFIELD"})), [GROUP.format("Unit_Kub", 7)])


class ABuildingPastTenGroups(unittest.TestCase):
    def test_eleven_groups_is_a_warning_and_ten_is_not(self):
        objects = {f"{G}A{k}": unit(f"Unit_A{k}", factory=AIRFIELD) for k in range(11)}
        self.assertEqual(said(objects),
                         ["Germany's Airfield has 11 groups: its build list may run off the screen past 10"])
        objects[G + "A10"] = unit("Unit_A10", factory=AIRFIELD, shows=[0] * 5)  # hidden: no group
        self.assertEqual(said(objects), [])
        objects[G + "A10"] = unit("Unit_A10", factory=AIRFIELD, upgrade=G + "A9")  # an upgrade: in A9's group
        self.assertEqual(said(objects), [])

    def test_named_in_english(self):
        objects = {f"{G}A{k}": unit(f"Unit_A{k}", factory=AIRFIELD) for k in range(11)}
        objects[G + "Field"] = building(AIRFIELD, key="AIR")
        self.assertEqual(said(objects, zz=zz_win()),
                         ["Germany's AIRFIELD has 11 groups: its build list may run off the screen past 10"])

    def test_both_limits_at_once(self):
        objects = {f"{G}A{k}": unit(f"Unit_A{k}", factory=AIRFIELD) for k in range(11)}
        objects.update({f"{G}E{k}": unit(f"Unit_E{k}", factory=AIRFIELD, upgrade=G + "A0") for k in range(6)})
        self.assertEqual(said(objects), [GROUP.format("Unit_A0", 7).replace("Armor Base", "Airfield"),
                                         "Germany's Airfield has 11 groups: its build list may run off the screen "
                                         "past 10"])


class ReadWithTheMod(unittest.TestCase):
    def test_load_mod_reads_the_file(self):
        with tempfile.TemporaryDirectory() as d:
            folder = write_mod(d, "groups", {"a.rndf": "patch $/B ( P = 1 )"})
            self.assertEqual(load_mod(folder)[0].menu_groups, {})
            menugroups.write(folder, {G + "N1": G + "Tiger", G + "N2": G + "N2"})
            self.assertEqual(load_mod(folder)[0].menu_groups, {G + "N1": G + "Tiger", G + "N2": G + "N2"})

    def test_a_bad_file_is_refused_naming_it(self):
        with tempfile.TemporaryDirectory() as d:
            folder = write_mod(d, "groups", {"a.rndf": "patch $/B ( P = 1 )"})
            (folder / menugroups.FILE).write_text("[groups]\na = 1\n", encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "menu_groups.toml"):
                load_mod(folder)
            (folder / menugroups.FILE).write_text("[groups\n", encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "menu_groups.toml"):
                load_mod(folder)

    def test_a_quick_mod_has_none(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "quick.rndf")
            path.write_text("patch $/B ( P = 1 )", encoding="utf-8")
            (Path(d) / menugroups.FILE).write_text("[groups\n", encoding="utf-8")  # (not the quick mod's)
            self.assertEqual(load_mod(path)[0].menu_groups, {})

    def test_merged_in_load_order(self):
        a = ModInfo("a", menu_groups={G + "N1": G + "Kub", G + "N2": G + "Kub"})
        b = ModInfo("b", menu_groups={G + "N1": G + "N1"})
        self.assertEqual(merged_groups([a, b]), {G + "N1": G + "N1", G + "N2": G + "Kub"})
        self.assertEqual(merged_groups([b, a]), {G + "N1": G + "Kub", G + "N2": G + "Kub"})
        self.assertEqual(merged_groups([ModInfo("c")]), {})

    def test_a_mod_with_groups_alone_needs_zz_win(self):
        """The groups go into the menu script there (menu_lines), even when a mod changes nothing else."""
        self.assertTrue(needs_zz_win([(ModInfo("a", menu_groups={G + "Kub": G + "Tiger"}), [])]))
        self.assertFalse(needs_zz_win([(ModInfo("a"), [])]))


def int32(v):
    return val(0x02, struct.pack("<i", v))


KUB_KEY = name_to_key("KUB")
# the made-up game: Germany's Kub and Tiger in the Armor Base
GAME_NDF = make_ndf(objects=[(0, [(0, int32(1)), (1, int32(ARMOR)), (2, int32(GERMANY)),
                                  (3, val(0x1D, struct.pack("<Q", KUB_KEY)))]),
                             (0, [(0, int32(2)), (1, int32(ARMOR)), (2, int32(GERMANY))])],
                    classes=["TUniteAuSolDescriptor"],
                    props=[("DescriptorId", 0), ("Factory", 0), ("Nationalite", 0), ("NameInMenuToken", 0)],
                    exports={0: "Kub", 1: "Tiger"}, topo=[0, 1])
GAME_PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", GAME_NDF)])])


class InABuild(unittest.TestCase):
    """Two mods: `a` makes six copies of the Kub and puts them all in the Tiger's group (seven with it); `b` puts the
    sixth in a group of its own. The later mod's entry wins."""

    def mods(self, d, b_first=False):
        rndf = "\n".join(f"export N{k} is clone $/Kub ( DescriptorId = {10 + k} )" for k in range(1, 7))
        a = write_mod(d, "a", {"units.rndf": rndf}, extra='[load]\nafter = ["b"]\n' if b_first else "")
        menugroups.write(a, {f"$/N{k}": "$/Tiger" for k in range(1, 7)})
        b = write_mod(d, "b", {"x.rndf": "patch $/Tiger ( DescriptorId = 2 )"},
                      extra="" if b_first else '[load]\nafter = ["a"]\n')
        menugroups.write(b, {"$/N6": "$/N6"})
        return load_mod(a), load_mod(b)

    def build(self, mods):
        result = build_pack(Edat(GAME_PACK), list(mods))
        self.assertEqual(result.errors, [])
        return [f.message for f in result.findings if f.level == "warning"]

    def test_one_mod_over_the_limit_is_built_with_a_warning(self):
        with tempfile.TemporaryDirectory() as d:
            a, _b = self.mods(d)
            result = build_pack(Edat(GAME_PACK), [a])
            self.assertEqual(result.errors, [])
            self.assertTrue(result.changed)
            self.assertIn(GROUP.format("Tiger", 7),  # (no class name or English text here: its address's last part)
                          [f.message for f in result.findings if f.level == "warning"])

    def test_the_later_mods_entry_wins(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual([w for w in self.build(self.mods(d)) if "group" in w], [])
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual([w for w in self.build(self.mods(d, b_first=True)) if "group" in w],
                             [GROUP.format("Tiger", 7)])


class CarriedWithTheMod(unittest.TestCase):
    """menu_groups.toml goes wherever a mod folder goes: into its package (Export mod…, and the Studio's copy of an
    installed mod, both through package.files_of), out of it again, and into the library from a folder or a file."""
    GROUPS = {G + "N1": G + "Tiger", G + "N2": G + "N2"}

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.mod = write_mod(self.root, "grouped", {"a.rndf": "patch $/B ( P = 1 )"})
        menugroups.write(self.mod, self.GROUPS)

    def tearDown(self):
        self.tmp.cleanup()

    def test_in_the_package_and_out_again(self):
        self.assertIn(self.mod / menugroups.FILE, package.files_of(self.mod))
        out = package.pack(self.mod, self.root / "out")
        with zipfile.ZipFile(out) as z:
            self.assertIn(menugroups.FILE, z.namelist())
        package.unpack(out, self.root / "unpacked")
        self.assertEqual(menugroups.read(self.root / "unpacked"), self.GROUPS)

    def test_into_the_library(self):
        library = Library(self.root / "library")
        info, _replaced = library.add(self.mod)
        self.assertEqual(menugroups.read(info["path"]), self.GROUPS)
        out = package.pack(self.mod, self.root / "out")
        library.remove("grouped")
        info, _replaced = library.add(out)
        self.assertEqual(menugroups.read(info["path"]), self.GROUPS)
        self.assertEqual(load_mod(info["path"])[0].menu_groups, self.GROUPS)

    def test_a_bad_file_never_gets_in(self):
        (self.mod / menugroups.FILE).write_text("[groups]\na = 1\n", encoding="utf-8")
        with self.assertRaisesRegex(LibraryError, "menu_groups.toml"):
            Library(self.root / "library").add(self.mod)
        with self.assertRaises(package.PackageError):
            package.pack(self.mod, self.root / "out")


if __name__ == "__main__":
    unittest.main()
