"""Unit flags: what labels.toml says about each one (the Studio's flag picker shows it), and the build's guard against
the two that crash the game on anything but a truck (rusemod.unitflags). Made-up units, no game files needed."""
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat, schema
from rusemod.build import build_pack, load_mod
from rusemod.patch import Engine, Game, Obj, Op, Text, num, nums
from rusemod.resolve import ModInfo
from rusemod.unitflags import crashes, is_truck

# Every flag the game's own units carry in InitialFlagSet, with the game's own name for it.
GAME_NAMES = {
    0: "aerodrome", 1: "artillerie", 2: "avion", 4: "batiment", 5: "batiment_de_production", 6: "batiment_defense",
    7: "batiment_depot", 8: "batiment_hq", 10: "blessable", 11: "blocage_foret", 13: "bombardier",
    14: "can_capture_village", 18: "canon", 19: "capturable", 20: "cible_artillerie", 21: "combattant",
    22: "controlable", 23: "dalle_batiment_depot", 24: "detectable", 25: "detectable_volant", 30: "fake_batiment",
    31: "fake_truck", 33: "ghost", 34: "ghost_batiment", 38: "ghost_used_for_production", 40: "has_weapon",
    41: "highlightable", 42: "infanterie", 43: "ld_detectable", 44: "logistique", 46: "non_selectionnable_en_groupe",
    47: "obstacle_flocking", 48: "parachutiste", 49: "parachutiste_en_vol", 50: "pickable", 53: "selectionnable",
    55: "tank", 57: "target", 58: "toujours_visible", 59: "transport_parachutiste", 60: "tourelle_de_batiment",
    62: "truck", 63: "truck_construction", 64: "truck_devise", 67: "vehicule_volant", 70: "vision_centre_patrouille",
    71: "vision_circulaire", 72: "vision_no_obstacle", 76: "bateau", 77: "cannot_attack_en_reflexe",
    92: "cannot_hide_in_forest", 93: "batiment_administratif", 99: "avion_reco", 100: "avion_chasseur",
    101: "avion_chasseur_bomber", 102: "aerodrome_fake"}
# The other numbers of 0-104, with the game's name (DomesticNukes' table; 81-89 are all already_*): state the game sets
# on units while it runs, never in its data. In InitialFlagSet they do nothing (90 and 91 were tried), and labels.toml
# says so; 15 and 16 have no name and no use.
RUNTIME_NAMES = {
    3: "avion_can_attack_without_engaged", 9: "batiment_super_weapon", 12: "bluff_card", 17: "cannot_be_shoot_reflex",
    26: "en_combat", 27: "en_foret", 28: "factory", 29: "fake", 32: "flag_batiments_camoufles_for_truck",
    35: "ghost_batiment_depot", 36: "ghost_order", 37: "ghost_placed", 39: "group", 45: "munition_super_weapon",
    51: "plane_returning_to_base", 52: "avion_oqp", 54: "sous_tir_artillerie", 56: "got_all_its_ammo",
    61: "avion_dans_engagement", 65: "uberstress", 66: "use_morphe", 68: "vehicule_volant_au_sol", 69: "is_attacked",
    73: "vue", 74: "shadow_avion", 75: "cadavre_infanterie", 78: "avion_sans_munitions_restantes", 79: "selectionnee",
    80: "cannot_be_targeted", **{n: "already_*" for n in range(81, 90)}, 90: "is_en_silence_radio", 91: "is_camoufle",
    94: "cadavre_vehicle", 95: "cadavre_avion", 96: "holding_fire_for_ambush", 97: "cannot_be_captured",
    98: "already_cannot_be_captured", 103: "can_drop_para", 104: "has_scanner"}
UNUSED = (15, 16)
# In each language, "does nothing", and the whole "in a unit's flags it does nothing" the runtime ones end with.
NOTHING = {"us": ("does nothing", "in a unit's flags it does nothing"),
           "fr": ("sans effet", "dans les drapeaux d'une unité, sans effet"),
           "ger": ("wirkungslos", "in den Flags einer Einheit wirkungslos"),
           "ita": ("non fa nulla", "nei flag di un'unità non fa nulla"),
           "spa": ("no hace nada", "en los indicadores de una unidad no hace nada"),
           "pol": ("nic nie daje", "we flagach jednostki nic nie daje"),
           "ru": ("ничего не даёт", "во флагах юнита ничего не даёт"),
           "cz": ("nic nedělá", "v příznacích jednotky nic nedělá"),
           "jpn": ("効果なし", "部隊のフラグに入れても効果なし"), "sc": ("无效", "放在单位的标志位里无效")}
# In each language, the word that warns and a word of "crashes", in the texts of 62 and 63.
CRASH_WORDS = {"us": ("WARNING", "crash"), "fr": ("ATTENTION", "planter"), "ger": ("ACHTUNG", "stürzt"),
               "ita": ("ATTENZIONE", "crash"), "spa": ("ATENCIÓN", "cuelga"), "pol": ("UWAGA", "wysypuje"),
               "ru": ("ВНИМАНИЕ", "вылетает"), "cz": ("POZOR", "spadne"), "jpn": ("警告", "クラッシュ"),
               "sc": ("警告", "崩溃")}
WHY_62 = ("flag 62 (truck) on a unit that isn't a truck crashes R.U.S.E. at match start; take it off (only trucks, "
          "TTruckDescriptor units, can carry it)")


class Labels(unittest.TestCase):
    def test_every_number_of_0_to_104(self):
        self.assertEqual(sorted([*GAME_NAMES, *RUNTIME_NAMES, *UNUSED]), list(range(105)))
        self.assertEqual(len(GAME_NAMES), 56)  # the ones the game's units carry
        self.assertEqual(sorted(int(n) for n in schema._data()["flags"]), list(range(105)))
        self.assertEqual(schema.flag_numbers(), list(range(105)))

    def test_ten_languages_each_ending_with_the_game_s_name(self):
        for n, name in {**GAME_NAMES, **RUNTIME_NAMES}.items():
            entry = schema._data()["flags"][str(n)]
            self.assertEqual(sorted(entry), sorted(schema.LANGS), n)
            for lang in schema.LANGS:
                with self.subTest(flag=n, lang=lang):
                    text = entry[lang]
                    self.assertTrue(text.endswith(f" ({name})"), text)
                    self.assertTrue(text[:-len(name) - 3].strip(), text)  # it says something before the name

    def test_the_ones_no_unit_carries_say_they_do_nothing_in_every_language(self):
        self.assertEqual(sorted(NOTHING), sorted(schema.LANGS))
        for lang, (word, whole) in NOTHING.items():
            for n in range(105):
                with self.subTest(flag=n, lang=lang):
                    text = schema.flag(n, lang)
                    if n in RUNTIME_NAMES:
                        self.assertIn(whole, text)
                    elif n in UNUSED:
                        self.assertIn(word, text)
                        self.assertNotIn("(", text)  # no name
                    else:
                        self.assertNotIn(whole, text)  # the game's units carry it: it does something
        for n in (90, 91):  # tried in the game
            self.assertIn(", tested (", schema.flag(n))

    def test_62_and_63_warn_of_the_crash_in_every_language(self):
        self.assertEqual(sorted(CRASH_WORDS), sorted(schema.LANGS))
        for n in (62, 63):
            for lang, words in CRASH_WORDS.items():
                with self.subTest(flag=n, lang=lang):
                    for word in words:
                        self.assertIn(word, schema.flag(n, lang))

    def test_schema_flag_gives_the_text(self):
        self.assertEqual(schema.flag(62), schema.flag(62, "us"))  # the game's names chosen: the English text
        self.assertTrue(schema.flag(62).startswith("Truck; WARNING: crashes the game at match start"))
        self.assertTrue(schema.flag(63, "fr").startswith("Camion de construction ; ATTENTION"))
        self.assertTrue(schema.flag("1").endswith("(artillerie)"))
        self.assertTrue(schema.flag(72).startswith("Sees through obstacles"))
        self.assertTrue(schema.flag(91).startswith("Camouflaged, by the ruse card: the game sets it while playing"))
        self.assertEqual(schema.flag(15, "ger"), "Unbenutzt: das Spiel gibt ihm keinen Namen; wirkungslos")
        self.assertIsNone(schema.flag(105))  # no such flag: the picker shows the number


def game():
    """Two trucks as the game has them (TTruckDescriptor, with 44 and 62; the construction truck with 63 too) and a
    tank."""
    def unit(cls, debug, flags):
        return Obj(cls, {"ClassNameForDebug": Text("string", debug), "InitialFlagSet": nums(flags, "uint32")})
    return Game(objects={
        "$/Truck": unit("TTruckDescriptor", "Truck_GMC_factory", [10, 22, 44, 58, 62, 64]),
        "$/Builder": unit("TTruckDescriptor", "Truck_GMC_construction", [10, 22, 44, 58, 62, 63]),
        "$/Stuart": unit("TUniteAuSolDescriptor", "Unit_M3_Stuart", [10, 11, 21, 22, 55]),
    })


def run(*mods, base=None):
    """mods: (mod id, [Op]) in load order; each operation is on line 1 of <mod id>.rndf, or the line it says."""
    packed = []
    for mid, ops in mods:
        for op in ops:
            op.mod, op.file, op.line = mid, f"{mid}.rndf", op.line or 1
        packed.append((ModInfo(mid), ops))
    return Engine(base or game()).run(packed)


def errors(result):
    return [f.message for f in result.errors]


class TruckFlags(unittest.TestCase):
    """62 and 63 crash R.U.S.E. at match start on anything but a truck: the build stops with an error."""

    def test_62_on_a_tank_is_an_error_naming_the_unit_and_why(self):
        r = run(("trucks", [Op("append", "$/Stuart", "InitialFlagSet", [num(62)], line=3)]))
        self.assertEqual(errors(r), [f"trucks (trucks.rndf:3): $/Stuart: {WHY_62}"])

    def test_63_too_and_each_flag_gets_its_own_error(self):
        r = run(("trucks", [Op("append", "$/Stuart", "InitialFlagSet", [num(63), num(62)])]))
        self.assertEqual(len(r.errors), 2)
        self.assertIn("flag 62 (truck) on a unit that isn't a truck", errors(r)[0])
        self.assertIn("flag 63 (construction truck) on a unit that isn't a truck crashes R.U.S.E. at match start",
                      errors(r)[1])

    def test_every_way_of_writing_a_flag_list(self):
        for op in (Op("set", "$/Stuart", "InitialFlagSet", nums([10, 62], "uint32")),  # the Studio's way
                   Op("set", "$/Stuart", "InitialFlagSet[0]", num(62)),
                   Op("insert", "$/Stuart", "InitialFlagSet", num(62), anchor=num(10)),
                   Op("append", path="InitialFlagSet", value=[num(62)], every="TUniteAuSolDescriptor")):
            with self.subTest(op=op.kind):
                self.assertEqual(errors(run(("trucks", [op]))), [f"trucks (trucks.rndf:1): $/Stuart: {WHY_62}"])

    def test_nothing_on_a_truck(self):
        r = run(("trucks", [Op("append", "$/Truck", "InitialFlagSet", [num(63)]),
                            Op("append", "$/Builder", "InitialFlagSet", [num(1), num(62)]),
                            Op("clone", "$/Truck2", source="$/Truck")]))
        self.assertEqual(errors(r), [])

    def test_nothing_for_other_flags(self):
        r = run(("woods", [Op("remove", "$/Stuart", "InitialFlagSet", [num(11), num(21), num(55)]),
                           Op("append", "$/Stuart", "InitialFlagSet", [num(1), num(44), num(64), num(71), num(77)]),
                           Op("remove", "$/Truck", "InitialFlagSet", [num(62)])]))
        self.assertEqual(errors(r), [])

    def test_44_doesn_t_make_a_tank_a_truck(self):
        r = run(("trucks", [Op("append", "$/Stuart", "InitialFlagSet", [num(44), num(64), num(62)])]))
        self.assertEqual(errors(r), [f"trucks (trucks.rndf:1): $/Stuart: {WHY_62}"])

    def test_a_truck_without_44_is_still_a_truck(self):
        # 44 (logistique) on a tank does nothing; nothing says a truck without it crashes
        r = run(("trucks", [Op("remove", "$/Truck", "InitialFlagSet", [num(44)], line=7),
                            Op("set", "$/Builder", "InitialFlagSet", nums([62, 63], "uint32"))]))
        self.assertEqual(errors(r), [])

    def test_a_new_unit(self):
        r = run(("trucks", [Op("clone", "$/Stuart2", source="$/Stuart",
                                  body=[Op("append", path="InitialFlagSet", value=[num(62)], line=2)], line=2)]))
        self.assertEqual(errors(r), [f"trucks (trucks.rndf:2): $/Stuart2: {WHY_62}"])
        r = run(("a", [Op("append", "$/Stuart", "InitialFlagSet", [num(62)])]),
                ("b", [Op("clone", "$/Copy", source="$/Stuart")]))  # a copy of a unit a mod gave 62
        self.assertEqual(errors(r), [f"b (b.rndf:1): $/Copy: {WHY_62}", f"a (a.rndf:1): $/Stuart: {WHY_62}"])

    def test_names_the_mod_that_added_the_flag(self):
        r = run(("a", [Op("append", "$/Stuart", "InitialFlagSet", [num(62)])]),
                ("b", [Op("append", "$/Stuart", "InitialFlagSet", [num(71)])]))
        self.assertEqual(errors(r), [f"a (a.rndf:1): $/Stuart: {WHY_62}"])

    def test_names_the_mod_that_added_the_flag_whichever_way_each_wrote_it(self):
        # one item (InitialFlagSet[0]) and the whole list are two paths to the same flags: the mod that put 62 there
        # is named, not the one that came after it with another flag (the review of 2026-10-01 found b named here)
        by_item = Op("set", "$/Stuart", "InitialFlagSet[0]", num(62))
        whole = Op("append", "$/Stuart", "InitialFlagSet", [num(71)])
        self.assertEqual(errors(run(("a", [by_item]), ("b", [whole]))), [f"a (a.rndf:1): $/Stuart: {WHY_62}"])
        by_item = Op("set", "$/Stuart", "InitialFlagSet[0]", num(62))
        whole = Op("append", "$/Stuart", "InitialFlagSet", [num(71)])
        self.assertEqual(errors(run(("b", [whole]), ("a", [by_item]))), [f"a (a.rndf:1): $/Stuart: {WHY_62}"])
        # `add` makes 62 out of another flag (10 + 52)
        r = run(("a", [Op("add", "$/Stuart", "InitialFlagSet[0]", "52")]),
                ("b", [Op("append", "$/Stuart", "InitialFlagSet", [num(71)])]))
        self.assertEqual(errors(r), [f"a (a.rndf:1): $/Stuart: {WHY_62}"])

    def test_the_game_s_own_units_aren_t_checked(self):
        base = game()
        base.objects["$/Stuart"].props["InitialFlagSet"] = nums([10, 62], "uint32")
        self.assertEqual(errors(run(("m", [Op("append", "$/Truck", "InitialFlagSet", [num(1)])]), base=base)), [])

    def test_nor_the_flags_a_unit_already_had(self):
        # a unit that carried 62 before the mods (none does in the game; the .rmod mods a build applies first could):
        # changing its other flags isn't adding 62, but adding 63 is
        base = game()
        base.objects["$/Stuart"].props["InitialFlagSet"] = nums([10, 11, 62], "uint32")
        self.assertEqual(errors(run(("m", [Op("remove", "$/Stuart", "InitialFlagSet", [num(11)])]), base=base)), [])
        r = run(("m", [Op("append", "$/Stuart", "InitialFlagSet", [num(63)])]), base=base)
        self.assertEqual([why.split(" on ")[0] for why in errors(r)], ["m (m.rndf:1): $/Stuart: flag 63 (construction truck)"])
        # a copy is a new unit: all of its flags count
        r = run(("m", [Op("clone", "$/Copy", source="$/Stuart")]), base=base)
        self.assertEqual(errors(r), [f"m (m.rndf:1): $/Copy: {WHY_62}"])

    def test_what_a_truck_is(self):
        truck = Obj("TTruckDescriptor", {"InitialFlagSet": nums([44, 62], "uint32")})
        self.assertEqual((is_truck(truck), crashes(truck)), (True, []))
        tank = Obj("TUniteAuSolDescriptor", {"InitialFlagSet": nums([44, 62, 63], "uint32")})
        self.assertFalse(is_truck(tank))
        self.assertEqual([why.split(" on ")[0] for why in crashes(tank)],
                         ["flag 62 (truck)", "flag 63 (construction truck)"])
        self.assertEqual([why.split(" on ")[0] for why in crashes(tank, had={62})], ["flag 63 (construction truck)"])
        self.assertEqual(crashes(Obj("TBatimentDescriptor", {})), [])  # no flags at all
        self.assertTrue(is_truck(Obj("TTruckDescriptor", {"InitialFlagSet": nums([62], "uint32")})))  # without 44


def flag_list(values):
    return val(0x11, struct.pack("<I", len(values)) + b"".join(val(0x03, struct.pack("<I", v)) for v in values))


UNITS = make_ndf(objects=[(0, [(0, flag_list([10, 55]))]), (1, [(1, flag_list([44, 62]))])],
                 classes=["TUniteAuSolDescriptor", "TTruckDescriptor"],
                 props=[("InitialFlagSet", 0), ("InitialFlagSet", 1)], exports={0: "Stuart", 1: "Truck"}, compress=True)
PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", UNITS)])])


class TheBuild(unittest.TestCase):
    def build(self, text):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d, "trucks.rndf")
            mod.write_text(text, encoding="utf-8")
            return build_pack(Edat(PACK), [load_mod(mod)])

    def test_stops_and_says_why(self):
        result = self.build("patch $/Stuart ( InitialFlagSet += [uint32(62)] )\n")
        self.assertEqual([f.message for f in result.errors], [f"trucks (trucks.rndf:1): $/Stuart: {WHY_62}"])
        self.assertEqual(result.changed, {})  # nothing to write

    def test_a_truck_builds(self):
        result = self.build("patch $/Truck ( InitialFlagSet += [uint32(63)] )\n")
        self.assertEqual(result.errors, [])
        self.assertTrue(result.changed)


if __name__ == "__main__":
    unittest.main()
