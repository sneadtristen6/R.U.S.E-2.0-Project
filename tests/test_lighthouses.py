"""A lighthouse's light goes with it (rusemod.lighthouses): on made-up game files laid out like D-Day's, the effect set
a map's scenario starts, its lighthouse lights (one placed as Swamps' and Blitz's are, one as D-Day's), and the
map-list entry and MapIA of the new-map tests' Blitz."""
import math
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_newmap import glad_files, reader, ref, s
from test_scenery import block, compact, make_scenery, moved, road
from rusemod.lighthouses import GFX, NEAR, gone, lighthouses, lights, scenario_effects, take_out
from rusemod.ndf import Ndf, local_ref, sub_values

BS = chr(92)
MAPIA = BS.join(["genglad", "patchable", "scenario", "supercrossroads4", "scenario", "mapia.cpp.gladndfbin"])
LIGHT_A, LIGHT_B = (1000.0, 2000.0, 300.0), (5000.0, 6000.0, 300.0)
SET = "$/GFX/Everything/FX_Atmospheric_Test"


def listed(*objects) -> bytes:
    return val(0x11, struct.pack("<I", len(objects)) + b"".join(objects))


def effects() -> bytes:
    """The game's effects: the lighthouse light template, and a set that starts rain and two lighthouse lights, the
    first at a place of its own (Swamps', Blitz's), the second at a place less the mouse's (D-Day's)."""
    classes = ["TSimultaneousActionForActionCallTemplate", "TSimultaneousAction", "TActionCall", "TPinnableValue",
               "TConstantFloat3", "TIntrinsicCall_2Param"]
    props = [("LocalVariables", 1), ("_ShortDatabaseName", 1), ("Actions", 1), ("_ShortDatabaseName", 2),
             ("Action", 2), ("InitialValue", 3), ("Value", 4), ("Param0", 5)]
    return make_ndf(
        objects=[(0, []),                                                                       # 0 GEN_Fx_Phare
                 (1, [(0, listed()), (1, s(0)), (2, listed(ref(2, 2), ref(3, 1), ref(7, 1)))]),  # 1 the set
                 (2, [(3, s(1))]),                                                              # 2 its rain
                 (1, [(0, listed(ref(4, 3))), (1, s(2)), (2, listed(ref(5, 2)))]),              # 3 light A
                 (3, [(5, ref(6, 4))]),
                 (2, [(4, ref(0, 0))]),
                 (4, [(6, val(0x0B, struct.pack("<3f", *LIGHT_A)))]),
                 (1, [(0, listed(ref(8, 3))), (1, s(3)), (2, listed(ref(9, 2)))]),              # 7 light B
                 (3, [(5, ref(10, 5))]),
                 (2, [(4, ref(0, 0))]),
                 (5, [(7, ref(11, 4))]),
                 (4, [(6, val(0x0B, struct.pack("<3f", *LIGHT_B)))])],
        classes=classes, props=props,
        strings=["FX_Atmospheric_Test", "Rain", "FX_phare_1", "FX_phare_2"],
        exports={0: "GFX/Everything/GEN_Fx_Phare", 1: "GFX/Everything/FX_Atmospheric_Test"}, topo=[1, 0])


def mapia(name="$/gfx/everything/FX_Atmospheric_Test") -> bytes:
    return make_ndf(objects=[(0, [(0, s(0))])], classes=["TFXLauncher"], props=[("FXName", 0)], strings=[name])


def files(**more) -> dict:
    return {**glad_files(), GFX: effects(), MAPIA: mapia(), **more}


def actions(nd: Ndf, path: str) -> list[int]:
    o = nd.objects[nd._by_export[path]]
    v = next(v for pi, v in o.props if nd.prop_name(pi) == "Actions")
    return [local_ref(x) for x in sub_values(v)]


class Lights(unittest.TestCase):
    def test_a_sets_lighthouse_lights_and_where_they_shine(self):
        nd = Ndf(effects())
        self.assertEqual(lights(nd, 1), [(3, LIGHT_A), (7, LIGHT_B)])

    def test_the_maps_scenarios_that_start_a_set(self):
        found = scenario_effects(reader(files()), "SuperCrossRoads4")
        self.assertEqual([(m, k) for m, _ia, k in found], [(MAPIA, 0)])
        self.assertEqual(scenario_effects(reader(files()), "M01_Leipzig"), [])   # its MapIA isn't there


class TakeOut(unittest.TestCase):
    def test_an_erased_lighthouse_takes_its_light_out_of_a_copy_its_map_starts(self):
        """Blank Ocean, 2026-10-05: D-Day's lighthouses erased, their lights stayed, turning over the sea."""
        changes, notes = take_out(reader(files()), "SuperCrossRoads4", [(LIGHT_A[0] + 150.0, LIGHT_A[1] - 80.0)])
        self.assertEqual(set(changes), {GFX, MAPIA})
        nd, ia = Ndf(changes[GFX]), Ndf(changes[MAPIA])
        copy = SET + "_SuperCrossRoads4"
        self.assertEqual(actions(nd, copy), [2, 7])           # the rain and the other light stay
        self.assertEqual(actions(nd, SET), [2, 3, 7])         # the game's own set keeps all its lights
        self.assertIn(nd._by_export[copy], nd.topo)           # a top object, like the set
        short = next(v for pi, v in nd.objects[nd._by_export[copy]].props if nd.prop_name(pi) == "_ShortDatabaseName")
        self.assertEqual(nd.strings[struct.unpack("<I", short.payload)[0]], "FX_Atmospheric_Test_SuperCrossRoads4")
        named = ia.strings[struct.unpack("<I", ia.objects[0].props[0][1].payload)[0]]
        self.assertEqual(named, "$/gfx/everything/FX_Atmospheric_Test_SuperCrossRoads4")
        self.assertEqual(len(notes), 1)
        self.assertIn("1 erased lighthouse", notes[0])

    def test_both_lights_out_and_the_set_read_back_whole(self):
        changes, _notes = take_out(reader(files()), "SuperCrossRoads4", [LIGHT_A[:2], LIGHT_B[:2]])
        nd = Ndf(changes[GFX])
        self.assertEqual(actions(nd, SET + "_SuperCrossRoads4"), [2])
        self.assertEqual(lights(nd, nd._by_export[SET]), [(3, LIGHT_A), (7, LIGHT_B)])
        self.assertEqual(len(nd.objects), len(Ndf(effects()).objects) + 1)   # one object more: the copy

    def test_a_lighthouse_far_from_every_light_changes_nothing(self):
        far = (LIGHT_A[0] + NEAR + 1.0, LIGHT_A[1])
        self.assertEqual(take_out(reader(files()), "SuperCrossRoads4", [far]), ({}, []))
        self.assertEqual(take_out(reader(files()), "SuperCrossRoads4", []), ({}, []))

    def test_a_map_whose_scenario_starts_no_set_with_lights_changes_nothing(self):
        plain = files(**{MAPIA: mapia("$/gfx/everything/FX_Atmospheric_Generic")})
        self.assertEqual(take_out(reader(plain), "SuperCrossRoads4", [LIGHT_A[:2]]), ({}, []))
        self.assertEqual(take_out(reader({k: v for k, v in files().items() if k != GFX}), "SuperCrossRoads4",
                                  [LIGHT_A[:2]]), ({}, []))


def village(first="TypeWarrior/Phare") -> bytes:
    """test_scenery's village with its town hall (placed once, at 1,000, 2,000: light A's place) named `first`."""
    wood = block([struct.pack("<I", 0x80000000 | 1 << 4 | 1), moved(0x80000000 | 1 << 4, 100.0, 0.0),
                  road((10.0, 20.0), (5.0, 0.0), (40.0, 20.0), (-5.0, 0.0))])
    root_len = len(block([compact(0, 1000.0, 2000.0), moved(0, 0, 0), moved(0, 0, 0)]))
    root = block([compact(0, 1000.0, 2000.0, math.pi / 2), moved(root_len, 5000.0, 0.0),
                  moved(root_len, 5000.0, 9000.0)])
    return make_scenery([root, wood], [first, "TypeWarrior/Chene_02"])


def edat_of(files: dict) -> bytes:
    """An EDAT pack holding {member path: bytes}."""
    tree: dict = {}
    for path, data in files.items():
        *dirs, name = path.split(BS)
        node = tree
        for d in dirs:
            node = node.setdefault(d + BS, {})
        node[name] = data

    def nodes(t):
        return [("dir", k, nodes(v)) if isinstance(v, dict) else ("file", k, v) for k, v in sorted(t.items())]
    return make_edat(nodes(tree))


class Lighthouses(unittest.TestCase):
    def test_where_the_maps_lighthouses_stand_and_which_went(self):
        self.assertEqual(lighthouses(village()), [(1000.0, 2000.0)])
        self.assertEqual(lighthouses(village("TypeWarrior/fx_prod_gyrophare")), [])   # a factory's beacon isn't one
        self.assertEqual(gone([(0.0, 0.0), (10.0, 10.0)], [(10.0, 10.5)]), [(0.0, 0.0)])


class Building(unittest.TestCase):
    def test_a_mod_that_erases_a_lighthouse_takes_its_light_out(self):
        """The whole way: a mod's erase area over Blitz's lighthouse; the build says so, writes the effects' copy
        without light A and points the map's scenario at it."""
        from rusemod.build import build_and_write, load_mod
        from rusemod.edat import Edat
        from test_scenery import unit_pack_raw
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "R.U.S.E"
            data = game / "Data" / "PC" / "190852"
            data.mkdir(parents=True)
            (game / "Maps" / "PC").mkdir(parents=True)
            units = Edat(unit_pack_raw())
            glad = {**{e.path: bytes(units.read(e)) for e in units.entries}, **files()}
            (data / "ZZ_GladPatchableWin.dat").write_bytes(edat_of(glad))
            (game / "Maps" / "PC" / "DataMapSuperCrossRoads4_v09.dat").write_bytes(
                make_edat([("dir", "output\\", [("file", "save.boobspc", village())])]))
            mod = root / "mod"
            (mod / "maps" / "SuperCrossRoads4").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "dark"\nversion = "1.0.0"\n', encoding="utf-8")
            (mod / "maps" / "SuperCrossRoads4" / "scenery.toml").write_text(
                '[[erase]]\nx = 1000\ny = 2000\nradius = 10\ntypes = ["TypeWarrior/Phare"]\n', encoding="utf-8")
            lines = []
            result = build_and_write(game, [load_mod(mod)], out=root / "out", say=lines.append)
            self.assertEqual(result.errors, [], lines)
            self.assertIn("lighthouses: SuperCrossRoads4, from dark", lines)
            out = Edat((root / "out" / "ZZ_GladPatchableWin.dat").read_bytes())
            nd = Ndf(bytes(out.read(out.find(GFX))))
            self.assertEqual(actions(nd, SET + "_SuperCrossRoads4"), [2, 7])
            ia = Ndf(bytes(out.read(out.find(MAPIA))))
            self.assertIn("$/gfx/everything/FX_Atmospheric_Test_SuperCrossRoads4", ia.strings)
            maps = Edat((root / "out" / "DataMapSuperCrossRoads4_v09.dat").read_bytes())
            self.assertEqual(lighthouses(bytes(maps.read(maps.find("save.boobspc")))), [])   # the lighthouse went


if __name__ == "__main__":
    unittest.main()
