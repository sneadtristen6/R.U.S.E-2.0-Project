"""What the game needs of a unit beyond its data's types (rusemod.unitcheck, rusemod.unitflags.problems): the build's
errors and warnings for ids, nations, price and menu lists, flags and salvos. Made-up units, no game files needed."""
import struct
import tempfile
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from rusemod import Edat
from rusemod.build import BuildResult, build_pack, load_mod, needs_zz_win, skirmish_models, unit_models
from rusemod.patch import Engine, Game, Inline, ListV, Obj, Op, Ref, Text, num, nums
from rusemod.resolve import ModInfo
from rusemod import unitcheck

TANK, PLANE, C47, PARA, TRUCK, ROCKETS = "$/Tank", "$/Plane", "$/C47", "$/Para", "$/Truck", "$/Rockets"
LAUNCHER = "$/Turret_Rockets"  # a named turret: a mod can put it on another weapon
NEW = "$/New"


def unit(cls, did, flags, nation=1, **extra):
    return Obj(cls, {"DescriptorId": num(did, "uint32"), "Nationalite": num(nation), "Factory": num(8),
                     "InitialFlagSet": nums(flags, "uint32"), "ProductionPrice": nums([10] * 5),
                     "ShowInMenu": nums([1] * 5, "bool"), "ClassNameForDebug": Text("string", f"Unit_{did}"), **extra})


def mounted(salvo):
    return Inline(Obj("TMountedWeaponDescriptor", {"SalveNumber": num(salvo)}))


def weapon(turrets, salves=None):
    props = {"TurretDescriptorList": ListV(turrets)}
    if salves is not None:
        props["Salves"] = nums(salves)
    return Inline(Obj("TWeaponDescriptor", props))


def game():
    """As the game has them: a tank whose gun fires no salvos (no Salves), an aircraft (flag 2), a C-47 dropping
    paratroopers (2 and 59, with the unit it drops), a truck (62), and a rocket launcher whose weapon has salvos and
    whose turret, a named object, fires salvo 1."""
    turret = Inline(Obj("TTurretDescriptor", {"MountedWeaponDescriptorList": ListV([mounted(-1)])}))
    return Game(objects={
        TANK: unit("TUniteAuSolDescriptor", 1000, [10, 24, 43, 55], WeaponDescriptor=weapon([turret])),
        PLANE: unit("TAvionDescriptor", 1200, [2, 10, 24]),
        C47: unit("TAvionDescriptor", 1201, [2, 10, 24, 59], UniteTransportee=Ref(PARA)),
        PARA: unit("TInfanterieDescriptor", 1300, [10, 24, 42, 48]),
        TRUCK: Obj("TTruckDescriptor", {"DescriptorId": num(10, "uint32"), "Nationalite": num(1),
                                        "InitialFlagSet": nums([10, 24, 44, 62], "uint32")}),
        ROCKETS: unit("TUniteAuSolDescriptor", 1400, [10, 24, 43],
                      WeaponDescriptor=weapon([Ref(LAUNCHER)], salves=[2, 6, -1, -1, -1])),
        LAUNCHER: Obj("TTurretDescriptor", {"MountedWeaponDescriptorList": ListV([mounted(1)])}),
    })


def run(*ops, base=None):
    for op in ops:
        op.mod, op.file, op.line = "m", "m.rndf", op.line or 1
    return Engine(base or game()).run([(ModInfo("m"), list(ops))])


def clone(*body, source=TANK):
    return Op("clone", NEW, source=source, body=[Op("set", path=p, value=v) for p, v in body])


def said(result, level="error"):
    return [f.message for f in result.findings if f.level == level]


class TheGameAsShipped(unittest.TestCase):
    def test_nothing_to_say(self):
        r = run()
        self.assertEqual([f for f in r.findings if f.level != "note"], [])
        for name in (TANK, PLANE, C47, PARA, TRUCK, ROCKETS):  # a copy of each is fine too
            with self.subTest(copy_of=name):
                self.assertEqual([f.level for f in run(clone(source=name)).findings if f.level != "note"], [])

    def test_what_it_already_had_isn_t_the_mods_doing(self):
        base = game()
        base.objects[TANK].props["Nationalite"] = num(9)
        base.objects[TANK].props["ProductionPrice"] = nums([10])
        base.objects[PLANE].props["DescriptorId"] = num(1000, "uint32")
        r = run(Op("set", TANK, "SeuilMort", num(5)), Op("set", PLANE, "SeuilMort", num(5)), base=base)
        self.assertEqual(said(r) + said(r, "warning"), [])


class Ids(unittest.TestCase):
    """The game keeps one unit per DescriptorId, across every kind of unit."""

    def test_another_unit_s_id_even_of_another_kind(self):
        r = run(clone(("DescriptorId", num(1200, "uint32"))))
        self.assertEqual(said(r), [f"m (m.rndf:1): {NEW}: DescriptorId 1200 is also {PLANE}'s: the game keeps one "
                                   f"unit per id, so it skips this one, and orders for it build {PLANE}; give it a "
                                   f"number no other unit has (a copy gets one by itself when it doesn't set "
                                   f"DescriptorId)"])

    def test_zero(self):
        r = run(clone(("DescriptorId", num(0, "uint32"))))
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{NEW}: DescriptorId 0 isn't an id", said(r)[0])

    def test_a_game_unit_patched_to_another_s_id_is_named_not_the_other(self):
        r = run(Op("set", TANK, "DescriptorId", num(1200, "uint32"), line=4))
        self.assertEqual([m.split(" is also ")[0] for m in said(r)], [f"m (m.rndf:4): {TANK}: DescriptorId 1200"])

    def test_a_unit_made_from_scratch_needs_one(self):
        r = run(Op("create", NEW, cls="TUniteAuSolDescriptor"))
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{NEW}: it has no DescriptorId", said(r)[0])
        r = run(Op("create", NEW, cls="TUniteAuSolDescriptor", body=[Op("set", path="DescriptorId", value=num(7))]))
        self.assertEqual(said(r), [])
        r = run(Op("create", "$/Thing", cls="TSomethingElse"))  # not a unit
        self.assertEqual(said(r), [])

    def test_taking_it_away(self):
        r = run(Op("delprop", TANK, "DescriptorId"))
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{TANK}: it has no DescriptorId", said(r)[0])

    def test_copies_get_their_own(self):
        r = run(clone(), Op("clone", "$/New2", source=PLANE))
        self.assertEqual(said(r) + said(r, "warning"), [])
        self.assertEqual(int(r.game.objects["$/New2"].props["DescriptorId"].value), 1402)


class Nations(unittest.TestCase):
    def test_0_to_6(self):
        for n in (7, -1, 100):
            with self.subTest(nation=n):
                r = run(clone(("Nationalite", num(n))))
                self.assertEqual(len(said(r)), 1)
                self.assertTrue(said(r)[0].startswith(f"m (m.rndf:1): {NEW}: Nationalite {n} isn't a nation: it must "
                                                      f"be 0 to 6 (0 US, 1 Germany, 2 UK, 3 France, 4 Italy, 5 USSR, "
                                                      f"6 Japan)"), said(r)[0])
        for n in (0, 6):
            self.assertEqual(said(run(clone(("Nationalite", num(n)))), "error"), [])
        r = run(Op("add", TANK, "Nationalite", 7))
        self.assertIn(f"{TANK}: Nationalite 8 isn't a nation", said(r)[0])


class ResearchParents(unittest.TestCase):
    """A unit researched from (UpgradeRequire) another nation's unit: the match's loading screen never ends
    (2026-10-09, era test 4); one researched from a missing unit is refused with it."""
    KV1, IS2, PERSHING = "$/KV1", "$/IS2", "$/Pershing"

    def base(self):
        g = game()
        g.objects[self.KV1] = unit("TUniteAuSolDescriptor", 1500, [10, 24, 43, 55], nation=5)
        g.objects[self.IS2] = unit("TUniteAuSolDescriptor", 1501, [10, 24, 43, 55], nation=5,
                                   UpgradeRequire=Ref(self.KV1), IsUpgrade=num(1, "bool"))
        g.objects[self.PERSHING] = unit("TUniteAuSolDescriptor", 1502, [10, 24, 43, 55], nation=0)
        return g

    def test_a_copy_in_another_army_keeping_its_parent(self):
        r = run(clone(("Nationalite", num(0)), source=self.IS2), base=self.base())
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{NEW}: it's researched from {self.KV1} (UpgradeRequire), which is USSR's unit, but this unit "
                      f"is in US's army", said(r)[0])
        self.assertIn("the loading screen never ends", said(r)[0])
        self.assertIn("Research it from one of US's own units, or make it a unit of its own", said(r)[0])

    def test_fine_in_its_own_army_or_on_its_own(self):
        self.assertEqual(said(run(clone(source=self.IS2), base=self.base())), [])
        on_its_own = clone(("Nationalite", num(0)), source=self.IS2)
        on_its_own.body += [Op("delprop", path="UpgradeRequire"), Op("delprop", path="IsUpgrade")]
        self.assertEqual(said(run(on_its_own, base=self.base())), [])
        moved = clone(("Nationalite", num(0)), ("UpgradeRequire", Ref(self.PERSHING)), source=self.IS2)
        self.assertEqual(said(run(moved, base=self.base())), [])

    def test_a_missing_parent_and_a_parent_moved_away(self):
        r = run(clone(("UpgradeRequire", Ref("$/Nothing")), source=self.IS2), base=self.base())
        self.assertIn(f"{NEW} still refers to $/Nothing", said(r))     # the build's own word on a missing object
        self.assertEqual(len([m for m in said(r) if "which isn't in the game. Research it from" in m]), 1)
        r = run(Op("set", self.KV1, "Nationalite", num(2)), base=self.base())   # the parent given to the UK
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{self.IS2}: it's researched from {self.KV1} (UpgradeRequire), which is UK's unit", said(r)[0])


class Lists(unittest.TestCase):
    """ProductionPrice and ShowInMenu have one item per battle date: 5."""

    def test_fewer_or_more_than_5(self):
        cases = {"ProductionPrice": nums([10]), "ShowInMenu": nums([1], "bool")}
        for prop, value in cases.items():
            with self.subTest(prop=prop):
                r = run(clone((prop, value)))
                self.assertEqual(len(said(r)), 1)
                self.assertTrue(said(r)[0].startswith(f"m (m.rndf:1): {NEW}: {prop} has 1 item(s); it needs 5, one "
                                                      f"per battle date ("), said(r)[0])
        r = run(Op("append", TANK, "ProductionPrice", [num(99)]))
        self.assertIn(f"{TANK}: ProductionPrice has 6 item(s)", said(r)[0])
        r = run(Op("set", TANK, "ProductionPrice", num(30)))  # a number where the list was
        self.assertIn(f"{TANK}: ProductionPrice isn't a list", said(r)[0])

    def test_5_items_pass(self):
        r = run(Op("set", TANK, "ProductionPrice", nums([30] * 5)), Op("mul", TANK, "ProductionPrice", "0.5"),
                Op("set", TANK, "ShowInMenu", nums([0, 0, 1, 1, 1])), Op("set", TANK, "ProductionPrice[2]", num(1)))
        self.assertEqual(said(r), [])

    def test_names_the_operation_that_changed_the_list(self):
        r = run(Op("set", TANK, "SeuilMort", num(1), line=2), Op("set", TANK, "ShowInMenu", nums([1, 1]), line=3),
                Op("set", TANK, "SeuilMort", num(2), line=4))
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:3): {TANK}: ShowInMenu has 2 item(s)"), said(r))


class Flags(unittest.TestCase):
    def test_59_on_anything_but_an_aircraft_crashes(self):
        r = run(Op("append", TANK, "InitialFlagSet", [num(59)]))
        self.assertEqual(len(said(r)), 1)
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:1): {TANK}: flag 59 (transport_parachutiste) on a unit that "
                                              f"isn't an aircraft crashes R.U.S.E."), said(r))

    def test_59_on_an_aircraft_that_drops_nobody_crashes(self):
        r = run(clone(("UniteTransportee", Ref(None)), source=C47))
        self.assertEqual(len(said(r)), 1)
        self.assertIn(f"{NEW}: flag 59 (transport_parachutiste) on an aircraft with no UniteTransportee", said(r)[0])
        r = run(Op("append", PLANE, "InitialFlagSet", [num(59)], line=2))
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:2): {PLANE}: flag 59"), said(r))
        r = run(Op("set", C47, "UniteTransportee", Ref(None), line=5))
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:5): {C47}: flag 59"), said(r))
        r = run(Op("set", C47, "InitialFlagSet", nums([2, 10, 24]), line=6), Op("delprop", C47, "UniteTransportee"))
        self.assertEqual(said(r), [])  # no 59, nothing dropped: fine

    def test_2_belongs_to_aircraft(self):
        r = run(clone(("InitialFlagSet", nums([2, 10, 24, 43], "uint32"))))
        self.assertEqual(said(r), [])
        self.assertEqual(said(r, "warning"), [f"m (m.rndf:1): {NEW}: flag 2 (avion) on a unit that isn't an aircraft "
                                              f"makes the game move and order it like an aircraft; take it off"])
        r = run(Op("remove", PLANE, "InitialFlagSet", [num(2)]))
        self.assertEqual(said(r), [])
        self.assertIn(f"{PLANE}: an aircraft without flag 2 (avion)", said(r, "warning")[0])

    def test_a_truck_without_62(self):
        r = run(Op("remove", TRUCK, "InitialFlagSet", [num(62)]))
        self.assertEqual(said(r), [])
        self.assertIn(f"{TRUCK}: a truck without flag 62 (truck)", said(r, "warning")[0])

    def test_only_0_to_104(self):
        r = run(Op("append", TANK, "InitialFlagSet", [num(105)]))
        self.assertEqual(said(r), [])
        self.assertEqual(said(r, "warning"), [f"m (m.rndf:1): {TANK}: flag 105 is outside 0 to 104, so the game "
                                              f"ignores it; take it off"])
        r = run(Op("append", TANK, "InitialFlagSet", [num(104)]))
        self.assertEqual(said(r) + said(r, "warning"), [])

    def test_override_makes_a_warning_a_note(self):
        op = Op("append", TANK, "InitialFlagSet", [num(105)])
        op.override = True
        self.assertEqual(said(run(op), "warning"), [])


class Salvos(unittest.TestCase):
    """A mounted weapon's SalveNumber (other than -1) is 0 to 4, and its weapon has that salvo (Salves[n] above 0)."""

    def test_a_salvo_turret_on_a_weapon_without_salvos(self):
        r = run(Op("append", TANK, "WeaponDescriptor.TurretDescriptorList", [Ref(LAUNCHER)], line=3))
        self.assertEqual(said(r), [f"m (m.rndf:3): {TANK}:WeaponDescriptor: TurretDescriptorList[1]."
                                   f"MountedWeaponDescriptorList[0] has SalveNumber 1, but the weapon has no Salves: "
                                   f"salvo 1 isn't defined; the game stops at load with a \"Quit game ?\" box. Give the "
                                   f"weapon a Salves list with salvo 1 above 0, or set SalveNumber to -1"])

    def test_the_salvo_taken_away(self):
        r = run(Op("set", ROCKETS, "WeaponDescriptor.Salves[1]", num(0), line=2))
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:2): {ROCKETS}:WeaponDescriptor: TurretDescriptorList[0]."
                                              f"MountedWeaponDescriptorList[0] has SalveNumber 1, but Salves[1] is 0"),
                        said(r))
        r = run(Op("set", ROCKETS, "WeaponDescriptor.Salves", nums([2])))
        self.assertIn("but Salves has no item 1", said(r)[0])
        r = run(Op("delprop", ROCKETS, "WeaponDescriptor.Salves"))
        self.assertIn("but the weapon has no Salves", said(r)[0])

    def test_a_salvo_number_out_of_range(self):
        r = run(Op("set", ROCKETS, "WeaponDescriptor.TurretDescriptorList[0].MountedWeaponDescriptorList[0]."
                                   "SalveNumber", num(5), line=7))
        self.assertEqual(len(said(r)), 1)
        self.assertTrue(said(r)[0].startswith(f"m (m.rndf:7): {ROCKETS}:WeaponDescriptor: TurretDescriptorList[0]."
                                              f"MountedWeaponDescriptorList[0] has SalveNumber 5, which isn't -1 or 0 "
                                              f"to 4"), said(r))

    def test_what_works(self):
        r = run(Op("set", ROCKETS, "WeaponDescriptor.Salves[1]", num(3)),
                Op("set", ROCKETS, "WeaponDescriptor.TurretDescriptorList[0].MountedWeaponDescriptorList[0]."
                                   "SalveNumber", num(0)),
                Op("append", TANK, "WeaponDescriptor.TurretDescriptorList",
                   [Inline(Obj("TTurretDescriptor", {"MountedWeaponDescriptorList": ListV([mounted(-1)])}))]),
                clone(source=ROCKETS))
        self.assertEqual(said(r), [])


# --- the build stops ---
def flag_list(values):
    return val(0x11, struct.pack("<I", len(values)) + b"".join(val(0x03, struct.pack("<I", v)) for v in values))


UNITS = make_ndf(objects=[(0, [(0, flag_list([10, 55]))])], classes=["TUniteAuSolDescriptor"],
                 props=[("InitialFlagSet", 0)], exports={0: "Stuart"}, compress=True)
PACK = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", UNITS)])])


class TheBuild(unittest.TestCase):
    def build(self, text):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d, "flags.rndf")
            mod.write_text(text, encoding="utf-8")
            return build_pack(Edat(PACK), [load_mod(mod)])

    def test_an_error_writes_nothing_a_warning_builds(self):
        result = self.build("patch $/Stuart ( InitialFlagSet += [uint32(59)] )\n")
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.changed, {})
        result = self.build("patch $/Stuart ( InitialFlagSet += [uint32(2)] )\n")
        self.assertEqual(result.errors, [])
        self.assertTrue(result.changed)


# --- models: a nation's unit models load only in matches where a player has that nation ---
def name_table(folder, models) -> bytes:
    """A mesh pack's name table: u32 10, 6 bytes, then one folder holding the models."""
    files = b""
    for k, name in enumerate(models):
        node = struct.pack("<II6fIHH", 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0xCDCD) + name.encode() + b"\0"
        node += bytes(len(node) % 2)
        if k < len(models) - 1:
            node = struct.pack("<II", 0, len(node)) + node[8:]
        files += node
    f = folder.encode() + b"\0"
    head = 8 + len(f) + (8 + len(f)) % 2
    return struct.pack("<I", 10) + bytes(6) + struct.pack("<II", head, 0) + f + bytes(head - 8 - len(f)) + files


def mesh_pack(models) -> bytes:
    """A mesh pack that only names its models (one empty mesh): enough for its name table to be read."""
    names = name_table("ww2\\res3d\\units\\", models)
    body = names + bytes(-len(names) % 4)
    fo = 0xC4 + len(body)
    body += struct.pack("<I", 256)
    mo = 0xC4 + len(body)
    body += struct.pack("<HH", 0, 0)
    head = bytearray(0xC4)
    head[0:8] = b"MESHPCPC"
    struct.pack_into("<I", head, 8, 4)
    for i, sec in enumerate([(0xC4, len(names), len(models)), (fo, 4, 0), (mo, 0, 0), (mo, 0, 0), (mo, 0, 0),
                             (mo, 4, 1), (mo, 0, 0), (mo, 0, 0)]):
        struct.pack_into("<III", head, 0x34 + 12 * i, *sec)
    struct.pack_into("<III", head, 0x9C, mo, 0, 0)
    return bytes(head) + body


SHERMAN_MODEL = "us\\tank\\us_shermanlod0.ase2ndfbin"
PANZER_MODEL = "ger\\tank\\ger_panzerivlod0.ase2ndfbin"
JEEP_MODEL = "common\\jeeplod0.ase2ndfbin"
LONG_TOM_MODEL = "us\\canon\\us_long_tomlod0.ase2ndfbin"
BOAT_MODEL = "us\\boat\\us_lcvplod0.ase2ndfbin"
PACKS = {"us": [SHERMAN_MODEL, LONG_TOM_MODEL], "ger": [PANZER_MODEL], "common": [JEEP_MODEL],
         "witboat_us": [BOAT_MODEL]}


def zz_win(packs=PACKS):
    files = [("file", f"meshskirmish{'' if tag.startswith('witboat') else '_'}{tag}.spk", mesh_pack(models))
             for tag, models in packs.items()] or [("file", "other.txt", b"x")]
    return Edat(make_edat([("dir", "gen_5\\pack\\gfxdescriptor\\", files)]))


def army():
    """Units whose model's mesh is an unnamed object, as in the game: a US Sherman, a German Panzer IV, a US jeep
    (its model in the common pack), a French atomic cannon on the US Long Tom's model (as the game's own are) and a US
    landing craft (its model in the US boats' pack)."""
    objects = {}

    def unit(name, did, nation, model):
        mesh = f"everything#{did}"
        objects[mesh] = Obj("TResourceMultiMaterialMesh", {"FileName": Text("path", "WW2\\Res3D\\Units\\" + model)})
        gfx = Inline(Obj("TGfxDescriptorModeleWithAnimation", {"MeshDescriptor": Ref(mesh)}))
        props = {"DescriptorId": num(did, "uint32"), "GfxDescriptor": gfx}
        if nation:
            props["Nationalite"] = num(nation)
        objects[name] = Obj("TUniteAuSolDescriptor", props)
    unit("$/Sherman", 1, 0, SHERMAN_MODEL.upper())
    unit("$/Panzer", 2, 1, PANZER_MODEL)
    unit("$/Jeep", 3, 0, JEEP_MODEL)
    unit("$/Canon_atomique_FR", 4, 3, LONG_TOM_MODEL)
    unit("$/LCVP", 5, 0, BOAT_MODEL)
    return Game(objects=objects)


PACK_KINDS = ("Proxy", "Mesh", "Animation")
NATION_TAGS = ("US", "GER", "UK", "FR", "ITA", "URSS", "JAP")


def loader(kind, nations=NATION_TAGS, force=None, missions=None):
    """A cluster map's loader of one kind of per-nation skirmish pack, as in the game (SkirmishPacks in Nationalite
    order); `missions`: what it loads outside a skirmish (NotSkirmishPacks), as pack names after "Pack<kind>"."""
    props = {"SkirmishPacks": ListV([Ref(f"$/IA/Cluster/Pack{kind}Skirmish_{n}") for n in nations]),
             "SkirmishCommon": Ref(f"$/IA/Cluster/Pack{kind}Skirmish_Common")}
    if force is not None:
        props["ForceLoadBitFieldIfSkirmish"] = num(force, "uint32")
    if missions is not None:
        props["NotSkirmishPacks"] = ListV([Ref(f"$/IA/Cluster/Pack{kind}{n}") for n in missions])
    return Inline(Obj("TClusterLoadSelectifResource", props))


def mission(*packs):
    """A campaign chapter's cluster map: its proxy and mesh loaders load `packs` outside a skirmish (as Holland's,
    one pack per nation it plays), its animation loader the one pack of every nation's (as every shipped one)."""
    return cluster_map(*(loader(k, missions=packs) for k in ("Proxy", "Mesh")),
                       loader("Animation", missions=("_All_ButCommon",)))


def listed(game, top):
    """Each loader of a cluster map: the packs it loads outside a skirmish, by name."""
    return [[x.target.rsplit("/", 1)[-1] for x in v.obj.props["NotSkirmishPacks"].items]
            for v in game.objects[top].props["SubClusterList"].items if v.obj.cls == "TClusterLoadSelectifResource"]


HOLLAND = ("Skirmish_Common", "Skirmish_US", "Skirmish_GER", "Skirmish_UK")


def cluster_map(*parts):
    """A scenario's cluster map: its sub-clusters, the per-nation pack loaders among them (all three by default)."""
    parts = parts or tuple(loader(k) for k in PACK_KINDS)
    return Obj("TClusterInitialisationWithSubClusters",
               {"SubClusterList": ListV([Inline(Obj("TClusterInitialisationExecute", {}))] + list(parts))})


def forced(game, top="$/Cluster"):
    """Each loader of a cluster map: its ForceLoadBitFieldIfSkirmish (None when not set)."""
    return [v.obj.props.get("ForceLoadBitFieldIfSkirmish") for v in game.objects[top].props["SubClusterList"].items
            if v.obj.cls == "TClusterLoadSelectifResource"]


class ForceLoadOn:
    """Tests of the force-load (build.FORCE_LOAD, as built)."""

    def setUp(self):
        import rusemod.build as b
        self.addCleanup(setattr, b, "FORCE_LOAD", b.FORCE_LOAD)
        b.FORCE_LOAD = True


class ForceLoadOff(unittest.TestCase):
    """With FORCE_LOAD off (the old way, kept), a unit for another nation, and a spawned one, get their models copied
    into the packs their matches load (rusemod.unitpacks; tests/test_unitpacks.py has the packs themselves), and
    nothing in the cluster maps changes."""

    def setUp(self):
        import rusemod.build as b
        self.addCleanup(setattr, b, "FORCE_LOAD", b.FORCE_LOAD)
        b.FORCE_LOAD = False

    def test_a_unit_for_another_nation_gets_its_models_copied(self):
        result = BuildResult()
        base = army()
        base.objects.update(LoadedEverywhere.MAPS)
        r = run(clone(("Nationalite", num(1)), source="$/Sherman"), base=base)
        unit_models(base, r, zz_win(), result)
        self.assertEqual(result.errors, [])
        self.assertEqual([f.message for f in result.findings], [
            f"m (m.rndf:1): {NEW} is in Germany's army (Nationalite 1), but its model ww2\\res3d\\units\\"
            f"{SHERMAN_MODEL} is in the mesh pack of US's units only: its models go into Germany's skirmish packs too "
            f"(1 mesh copied in from US's packs), so it loads with Germany's own units"])
        self.assertEqual(sorted(result.model_changed), ["gen_5\\pack\\gfxdescriptor\\meshskirmish_ger.spk"])
        from rusemod.spk import Spk
        self.assertIn(f"ww2\\res3d\\units\\{SHERMAN_MODEL}",
                      Spk(result.model_changed["gen_5\\pack\\gfxdescriptor\\meshskirmish_ger.spk"]).items)
        self.assertEqual(forced(r.game), [None] * 3)  # nothing forced

    def test_a_spawned_unit_s_models_go_into_the_common_packs(self):
        s = SpawnedUnits.check(self, "Unit_Panzer", maps=LoadedEverywhere.MAPS)
        self.assertEqual(s.errors, [])
        self.assertEqual([f.message for f in s.findings], [
            "spawner: the spawned Panzer use Germany's unit models, which a skirmish loads only when a player has "
            "Germany: they go into the skirmish packs every match loads too (1 mesh copied in from Germany's packs)"])
        self.assertEqual(sorted(s.model_changed), ["gen_5\\pack\\gfxdescriptor\\meshskirmish_common.spk"])
        self.assertEqual(forced(s.game), [None] * 3)

    def test_what_can_t_be_copied_is_refused(self):
        # no German mesh pack to copy the Sherman into
        result = BuildResult()
        base = army()
        r = run(clone(("Nationalite", num(1)), source="$/Sherman"), base=base)
        unit_models(base, r, zz_win({k: v for k, v in PACKS.items() if k != "ger"}), result)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("it can't be copied into Germany's skirmish packs: ZZ_Win.dat has no meshskirmish_ger.spk",
                      result.errors[0].message)
        self.assertEqual(result.model_changed, {})


class Models(ForceLoadOn, unittest.TestCase):
    def check(self, *ops, packs=PACKS, maps=None):
        """The models check on `army()` with the cluster maps `maps` ({name: Obj}, none by default): the findings,
        and the game as the build would write it."""
        base = army()
        base.objects.update(maps or {})
        result = BuildResult()
        r = run(*ops, base=base)
        unit_models(base, r, zz_win(packs) if packs is not None else None, result)
        result.game = r.game
        return result

    def test_a_unit_given_to_a_nation_whose_matches_don_t_load_its_model(self):
        # no cluster maps to load US units' models in every match: refused
        r = self.check(clone(("Nationalite", num(1)), source="$/Sherman"))
        self.assertEqual([f.message for f in r.errors], [
            f"m (m.rndf:1): {NEW} is in Germany's army (Nationalite 1), but its model ww2\\res3d\\units\\"
            f"{SHERMAN_MODEL} is in the mesh pack of US's units only, and the unit data has no cluster maps that "
            f"could load US's models in every match: the game loads a nation's unit models only in matches where a "
            f"player has that nation, so in other matches this unit has no model, or crashes the game. Copy one of "
            f"Germany's units instead, or leave it in US's army"])

    def test_a_game_unit_moved(self):
        r = self.check(Op("set", "$/Panzer", "Nationalite", num(0), line=4))
        self.assertEqual(len(r.errors), 1)
        self.assertTrue(r.errors[0].message.startswith("m (m.rndf:4): $/Panzer is in US's army (Nationalite 0)"))
        r = self.check(Op("delprop", "$/Panzer", "Nationalite"))  # not written = 0, the US
        self.assertIn("$/Panzer is in US's army", r.errors[0].message)

    def test_a_unit_given_another_nation_s_model(self):
        r = self.check(Op("set", "$/Sherman", "GfxDescriptor.MeshDescriptor", Ref("everything#2")))
        self.assertIn(f"$/Sherman is in US's army (Nationalite 0), but its model ww2\\res3d\\units\\{PANZER_MODEL}",
                      r.errors[0].message)

    def test_what_loads(self):
        r = self.check(clone(source="$/Sherman"), Op("clone", "$/Jeep_GER", source="$/Jeep",
                                                    body=[Op("set", path="Nationalite", value=num(1))]),
                       Op("clone", "$/Canon_2", source="$/Canon_atomique_FR"), Op("clone", "$/LCVP_2", source="$/LCVP"),
                       Op("set", "$/Panzer", "Nationalite", num(1)))
        self.assertEqual(r.findings, [])
        # the jeep's model is in the common pack, the landing craft's in the US boats' one: loaded for the US
        g, packs = army(), skirmish_models(zz_win())
        for name in ("$/Jeep", "$/LCVP"):
            self.assertEqual(unitcheck.missing_models(g.objects[name], g, packs), {}, name)
        g.objects["$/LCVP"].props["Nationalite"] = num(2)
        self.assertEqual(unitcheck.missing_models(g.objects["$/LCVP"], g, packs),
                         {f"ww2\\res3d\\units\\{BOAT_MODEL}": ["US"]})

    def test_the_game_s_own_odd_ones_only_where_the_game_has_them(self):
        # the French atomic cannon has the Long Tom's model, loaded with the US units: the game's own, so fine in
        # France; in Germany it's new
        r = self.check(Op("clone", "$/Canon_GER", source="$/Canon_atomique_FR",
                          body=[Op("set", path="Nationalite", value=num(1))]))
        self.assertIn("$/Canon_GER is in Germany's army", r.errors[0].message)

    def test_without_the_packs(self):
        r = self.check(clone(("Nationalite", num(1)), source="$/Sherman"), packs={})
        self.assertEqual([(f.level, f.message.split(",")[0]) for f in r.findings],
                         [("note", "ZZ_Win.dat has no skirmish mesh packs")])
        r = self.check(clone(("Nationalite", num(1)), source="$/Sherman"), packs=None)
        self.assertEqual(r.findings, [])
        r = self.check(Op("set", "$/Sherman", "SeuilMort", num(1)), packs={})  # nothing moved: nothing to say
        self.assertEqual(r.findings, [])

    def test_moving_a_unit_needs_zz_win(self):
        mod = ModInfo("m")
        self.assertTrue(needs_zz_win([(mod, [Op("set", "$/Panzer", "Nationalite", num(0))])]))
        self.assertTrue(needs_zz_win([(mod, [Op("set", "$/Panzer", "GfxDescriptor.MeshDescriptor", Ref(None))])]))
        self.assertTrue(needs_zz_win([(mod, [Op("set", path="Nationalite", value=num(1), every="TUniteAuSolDescriptor")])]))
        self.assertFalse(needs_zz_win([(mod, [Op("set", "$/Panzer", "SeuilMort", num(1))])]))


class LoadedEverywhere(ForceLoadOn, unittest.TestCase):
    """A unit whose models only another nation's matches load: that nation's packs load in every skirmish (the bit of
    its Nationalite in every cluster map loader's ForceLoadBitFieldIfSkirmish), and the old refusal is a note."""
    MAPS = {"$/Cluster": cluster_map(), "$/Cluster_2": cluster_map()}
    check = Models.check

    def test_the_us_sherman_for_germany(self):
        r = self.check(clone(("Nationalite", num(1)), source="$/Sherman"), maps=self.MAPS)
        self.assertEqual(r.errors, [])
        self.assertEqual([f.message for f in r.findings], [
            "US's unit models and animations now load in every skirmish, beside those of the nations playing, for the "
            "units of other nations that use them (6 loaders in 2 cluster maps; matches take a little more memory "
            "and loading time)",
            f"m (m.rndf:1): {NEW} is in Germany's army (Nationalite 1), but its model ww2\\res3d\\units\\"
            f"{SHERMAN_MODEL} is in the mesh pack of US's units: US's unit models now load in every skirmish, so it "
            f"shows in matches where no player has US too"])
        self.assertEqual([f.level for f in r.findings], ["note", "note"])
        for top in self.MAPS:  # US is Nationalite 0: bit 0, in the proxies', meshes' and animations' loaders
            self.assertEqual(forced(r.game, top), [num(1, "uint32")] * 3)

    def test_the_bit_is_the_nation_s(self):
        r = self.check(Op("set", "$/Panzer", "Nationalite", num(6)), maps=self.MAPS)  # German models for Japan
        self.assertEqual(forced(r.game), [num(2, "uint32")] * 3)
        self.assertIn("Germany's unit models now load in every skirmish", r.findings[1].message)
        r = self.check(clone(("Nationalite", num(4)), source="$/Sherman"), Op("set", "$/Panzer", "Nationalite", num(0)),
                       maps=self.MAPS)
        self.assertEqual(forced(r.game), [num(3, "uint32")] * 3)  # US and Germany
        self.assertEqual([f.level for f in r.findings], ["note"] * 4)

    def test_bits_already_set_are_kept(self):
        maps = {"$/Cluster": cluster_map(loader("Proxy", force=1 << 5), loader("Mesh", force=1), loader("Animation"))}
        r = self.check(clone(("Nationalite", num(2)), source="$/Sherman"), maps=maps)
        self.assertEqual(forced(r.game), [num(1 << 5 | 1, "uint32"), num(1, "uint32"), num(1, "uint32")])
        self.assertIn("(3 loaders in 1 cluster maps", r.findings[0].message)

    def test_only_what_needs_it(self):
        # a copy that stays in its nation, the game's own odd ones, and a unit moved without its model: no bit
        r = self.check(clone(source="$/Sherman"), Op("clone", "$/Canon_2", source="$/Canon_atomique_FR"),
                       Op("set", "$/Jeep", "Nationalite", num(5)), maps=self.MAPS)
        self.assertEqual(r.findings, [])
        self.assertEqual(forced(r.game), [None] * 3)
        self.assertEqual(forced(r.game, "$/Cluster_2"), [None] * 3)

    def test_one_nation_per_model(self):
        # a model in two nations' packs: the copy's own source nation's is loaded, or one already loaded for another
        packs = dict(PACKS, uk=[SHERMAN_MODEL])
        r = self.check(clone(("Nationalite", num(1)), source="$/Sherman"), packs=packs, maps=self.MAPS)
        self.assertEqual(forced(r.game), [num(1, "uint32")] * 3)
        self.assertIn("is in the mesh pack of US and UK's units: US's unit models now load", r.findings[1].message)
        r = self.check(Op("set", "$/Sherman", "Nationalite", num(1)), packs=dict(PACKS, uk=[SHERMAN_MODEL, PANZER_MODEL]),
                       maps=self.MAPS)
        self.assertEqual(forced(r.game), [num(1, "uint32")] * 3)  # (a game unit moved: the first nation)
        r = self.check(Op("set", "$/Sherman", "Nationalite", num(1)), Op("set", "$/Panzer", "Nationalite", num(0)),
                       packs=dict(PACKS, uk=[SHERMAN_MODEL, PANZER_MODEL]), maps=self.MAPS)
        self.assertEqual(forced(r.game), [num(3, "uint32")] * 3)  # Germany for the Panzer, then US for the Sherman

    def test_a_loader_without_the_nation_s_pack(self):
        # a loader whose SkirmishPacks stops before the nation is left alone; with none that has it, refused
        maps = {"$/Cluster": cluster_map(loader("Mesh", nations=("US", "GER")), loader("Animation"))}
        r = self.check(Op("set", "$/Sherman", "Nationalite", num(6)), Op("set", "$/Panzer", "Nationalite", num(6)),
                       maps=maps)
        self.assertEqual(forced(r.game), [num(3, "uint32"), num(3, "uint32")])
        short = {"$/Cluster": cluster_map(loader("Mesh", nations=("US",)))}
        r = self.check(Op("set", "$/Panzer", "Nationalite", num(0)), maps=short)
        self.assertEqual(len(r.errors), 1)
        self.assertIn("the unit data has no cluster maps that could load Germany's models", r.errors[0].message)
        r = self.check(Op("set", "$/Sherman", "Nationalite", num(1)), maps=short)  # US's pack is there: fine
        self.assertEqual([f.level for f in r.findings], ["note", "note"])

    def test_skeletons_and_card_pictures_load_with_every_nation(self):
        def skel(tag, n):
            return Obj("TClusterLoadResource", {"Packs": ListV([Inline(Obj("TResourceDescriptorMeshPack", {
                "PackName": Text("path", f"Pack\\GFXDescriptor\\Skeleton_{tag}.spk"),
                "UsefulnessMask": num(0x1ff0000 | 1 << n, "uint32")}, origin=("cluster", 10 + n)))])})

        def menu(tag):
            return Obj("TClusterLoadResource", {"Packs": ListV([Ref(f"$/Menu{tag}Pack")])})
        objects = {}
        for n, tag in enumerate(unitcheck.LOADER_TAGS):
            objects[unitcheck.SKELETONS.format(tag)] = skel(tag, n)
            for c in unitcheck.CARDS:
                objects[c.format(tag)] = menu(tag)
        g = Game(objects=dict(objects, **self.MAPS))
        self.assertEqual(unitcheck.load_with_every_nation(g, {1, 6}), {1: (6, 12), 6: (6, 12)})
        us = g.objects[unitcheck.SKELETONS.format("US")].props["Packs"].items
        self.assertEqual([x.obj.props["PackName"].value.rsplit("\\", 1)[-1] for x in us],
                         ["Skeleton_US.spk", "Skeleton_GER.spk", "Skeleton_JAP.spk"])
        self.assertIsNone(us[1].obj.origin)  # a copy, written as a new part
        self.assertEqual(us[1].obj.props["UsefulnessMask"], num(0x1ff0002, "uint32"))  # masks left as they are
        self.assertEqual([x.target for x in g.objects[unitcheck.CARDS[1].format("UK")].props["Packs"].items],
                         ["$/MenuUKPack", "$/MenuGERPack", "$/MenuJAPPack"])
        self.assertEqual(len(g.objects[unitcheck.SKELETONS.format("GER")].props["Packs"].items), 2)  # + Japan's
        # twice: nothing more
        self.assertEqual(unitcheck.load_with_every_nation(g, {1}), {1: (0, 0)})
        self.assertEqual(unitcheck.load_with_every_nation(Game(objects={}), [1, 9]), {1: (0, 0), 9: (0, 0)})

    def test_the_build_adds_them(self):
        base = army()
        base.objects.update(self.MAPS)
        for n, tag in enumerate(unitcheck.LOADER_TAGS):
            base.objects[unitcheck.SKELETONS.format(tag)] = Obj("TClusterLoadResource", {"Packs": ListV([Inline(Obj(
                "TResourceDescriptorMeshPack", {}, origin=("cluster", n)))])})
        result = BuildResult()
        r = run(clone(("Nationalite", num(1)), source="$/Sherman"), base=base)
        unit_models(base, r, zz_win(), result)
        self.assertEqual(result.errors, [])
        self.assertIn("US's unit skeletons and card pictures load in every nation's matches too (6 skeleton pack(s) "
                      "and 0 card picture pack(s) added to the other nations' loaders)",
                      [f.message for f in result.findings])

    def test_the_loaders(self):
        g = Game(objects={"$/Cluster": cluster_map(), "$/Other": Obj("TClusterLoadSelectifResource", {}),
                          "$/Tank": unit("TUniteAuSolDescriptor", 1, [10])})
        self.assertEqual([(top, path) for top, path, _ in unitcheck.loaders(g)],
                         [("$/Cluster", f"SubClusterList[{i}]") for i in (1, 2, 3)])  # (no SkirmishPacks: not one)
        self.assertEqual(unitcheck.load_everywhere(g, {1, 3}), {1: (3, 1), 3: (3, 1)})
        self.assertEqual(forced(g), [num(10, "uint32")] * 3)
        self.assertEqual(unitcheck.load_everywhere(Game(objects={}), [0]), {0: (0, 0)})

    def test_campaigns_and_operations_list_the_nation_too(self):
        # outside a skirmish a loader loads its own list and nothing else: Holland's has no French pack, so French
        # units spawned there had no model (a player's build, 2026-10-03: the game crashed loading the mission)
        g = Game(objects={"$/Holland": mission(*HOLLAND),
                          "$/Italy": mission("Skirmish_Common", "SkirmishWithBoat_US", "Skirmish_GER", "Skirmish_FR"),
                          "$/Alpha": mission("_All"), "$/Blitz": cluster_map()})
        self.assertEqual(unitcheck.load_in_missions(g, {3, 0}), {0: (0, 0), 3: (2, 1)})
        self.assertEqual(listed(g, "$/Holland"), [
            [f"PackProxySkirmish_{n}" for n in ("Common", "US", "GER", "UK", "FR")],
            [f"PackMeshSkirmish_{n}" for n in ("Common", "US", "GER", "UK", "FR")],
            ["PackAnimation_All_ButCommon"]])  # (one pack of every nation's: nothing to add)
        # the US's pack with boats holds all of the plain one: Italy has the US already, and France
        self.assertEqual(listed(g, "$/Italy")[1], ["PackMeshSkirmish_Common", "PackMeshSkirmishWithBoat_US",
                                                   "PackMeshSkirmish_GER", "PackMeshSkirmish_FR"])
        self.assertEqual(listed(g, "$/Alpha"), [["PackProxy_All"], ["PackMesh_All"], ["PackAnimation_All_ButCommon"]])
        self.assertEqual(forced(g, "$/Holland"), [None] * 3)  # (the skirmish bit stays as it was)
        # twice: nothing more
        self.assertEqual(unitcheck.load_in_missions(g, {3}), {3: (0, 0)})
        self.assertEqual(len(listed(g, "$/Holland")[1]), 5)


# --- the build writes the loaders' bits into the cluster map files ---
def ref(index, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))


NO_PACK = val(0x09, struct.pack("<III", 0xBBBBBBBB, 0xFFFFFFFF, 0xFFFFFFFF))


def path_text(index):
    return val(0x1C, struct.pack("<I", index))


def packs_list(n=7):
    return val(0x11, struct.pack("<I", n) + NO_PACK * n)


# a German tank whose model's mesh is an unnamed object
ARMY = make_ndf(objects=[(0, [(0, val(0x03, struct.pack("<I", 2))), (1, val(0x02, struct.pack("<i", 1))),
                              (2, ref(1, 1))]),
                         (1, [(3, ref(2, 2))]),
                         (2, [(4, path_text(0))])],
                classes=["TUniteAuSolDescriptor", "TGfxDescriptorModeleWithAnimation", "TResourceMultiMaterialMesh"],
                props=[("DescriptorId", 0), ("Nationalite", 0), ("GfxDescriptor", 0), ("MeshDescriptor", 1),
                       ("FileName", 2)],
                strings=["WW2\\Res3D\\Units\\" + PANZER_MODEL], exports={0: "Panzer"}, compress=True)
# a cluster map whose three loaders set no ForceLoadBitFieldIfSkirmish (as every shipped one)
CLUSTER = make_ndf(objects=[(0, [(0, val(0x11, struct.pack("<I", 3) + ref(1, 1) + ref(2, 1) + ref(3, 1)))]),
                            (1, [(1, packs_list()), (2, NO_PACK)]),
                            (1, [(1, packs_list()), (2, NO_PACK)]),
                            (1, [(1, packs_list()), (2, NO_PACK), (3, val(0x00, b"\x01"))])],
                   classes=["TClusterInitialisationWithSubClusters", "TClusterLoadSelectifResource"],
                   props=[("SubClusterList", 0), ("SkirmishPacks", 1), ("SkirmishCommon", 1),
                          ("DoNotLoadRessource", 1)])
CLUSTER_MAP = "genglad\\patchable\\scenario\\alpha\\scenario\\clustermap.cpp.gladndfbin"
UNIT_PACK = make_edat([("dir", "genglad\\patchable\\", [
    ("dir", "gfx\\", [("file", "everything.cpp.gladndfbin", ARMY)]),
    ("dir", "scenario\\alpha\\scenario\\", [("file", "clustermap.cpp.gladndfbin", CLUSTER)])])])


class TheBuildLoadsThem(ForceLoadOn, unittest.TestCase):
    def build(self, text, pack=UNIT_PACK):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d, "moved.rndf")
            mod.write_text(text, encoding="utf-8")
            return build_pack(Edat(pack), [load_mod(mod)], text_arc=zz_win())

    def test_a_german_tank_for_the_us(self):
        result = self.build("export Panzer_US is clone $/Panzer ( Nationalite = 0 )\n")
        self.assertEqual(result.errors, [])
        self.assertIn("Germany's unit models and animations now load in every skirmish", "\n".join(
            f.message for f in result.findings))
        self.assertIn(CLUSTER_MAP, result.changed)
        from rusemod.model import load
        g, _ = load({CLUSTER_MAP: result.changed[CLUSTER_MAP]})
        self.assertEqual([part.props.get("ForceLoadBitFieldIfSkirmish") for _t, _p, part in unitcheck.loaders(g)],
                         [num(2, "uint32")] * 3)
        # the rest of each loader as it was
        self.assertEqual([sorted(part.props) for _t, _p, part in unitcheck.loaders(g)],
                         [["ForceLoadBitFieldIfSkirmish", "SkirmishCommon", "SkirmishPacks"]] * 2
                         + [["DoNotLoadRessource", "ForceLoadBitFieldIfSkirmish", "SkirmishCommon", "SkirmishPacks"]])

    def test_nothing_moved_leaves_the_cluster_maps(self):
        result = self.build("export Panzer_2 is clone $/Panzer ( DescriptorId = 3 )\n")
        self.assertEqual(result.errors, [])
        self.assertNotIn(CLUSTER_MAP, result.changed)

    def test_without_cluster_maps_it_s_refused(self):
        alone = make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ARMY)])])
        result = self.build("patch $/Panzer ( Nationalite = 0 )\n", pack=alone)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("no cluster maps", result.errors[0].message)
        self.assertEqual(result.changed, {})


class SpawnedUnits(ForceLoadOn, unittest.TestCase):
    """A unit a mod's scenario spawns: the nation whose pack has its models loads in every skirmish, or the spawn is
    refused (Japanese units spawned on D-Day with no Japanese player crashed the game as the match started)."""

    def check(self, *whats, maps=None):
        from rusemod.build import spawn_models
        from rusemod.scenario import Spawn
        base = army()
        for name in ("$/Panzer", "$/Jeep", "$/Sherman"):
            base.objects[name].props["ClassNameForDebug"] = Text("string", "Unit_" + name[2:])
        base.objects.update(maps or {})
        mod = ModInfo("spawner")
        mod.scenario = {"Alpha": [Spawn("s.scenario", w, 1.0, 2.0) for w in whats]}
        result = BuildResult(order=["spawner"])
        r = run(base=base)
        spawn_models(r, zz_win(), [(mod, [])], result.order, result)
        result.game = r.game
        return result

    def test_a_spawned_german_tank_loads_germany_s_models(self):
        r = self.check("Unit_Panzer", "Unit_Panzer", maps=LoadedEverywhere.MAPS)
        self.assertEqual(r.errors, [])
        self.assertEqual([f.message for f in r.findings], [
            "spawner: the spawned Panzer use Germany's unit models, which a skirmish loads only when a player has "
            "Germany: they now load in every skirmish (6 loaders in 2 cluster maps)"])
        self.assertEqual(forced(r.game), [num(2, "uint32")] * 3)

    def test_a_spawned_unit_loads_in_campaign_chapters_too(self):
        r = self.check("Unit_Panzer", maps=dict(LoadedEverywhere.MAPS, **{"$/Holland": mission(
            "Skirmish_Common", "Skirmish_US", "Skirmish_UK")}))
        self.assertEqual(r.errors, [])
        self.assertIn("Germany's unit models load in campaign chapters and Operations too, which load only the nations "
                      "they play (2 loaders in 1 cluster maps)", [f.message for f in r.findings])
        self.assertEqual(listed(r.game, "$/Holland")[1],
                         [f"PackMeshSkirmish_{n}" for n in ("Common", "US", "UK", "GER")])

    def test_common_models_and_unknown_classes_need_nothing(self):
        r = self.check("Unit_Jeep", "Unit_Nobody", maps=LoadedEverywhere.MAPS)
        self.assertEqual(r.findings, [])
        self.assertEqual(forced(r.game), [None] * 3)

    def test_without_cluster_maps_the_spawn_is_refused(self):
        r = self.check("Unit_Sherman")
        self.assertEqual(len(r.errors), 1)
        self.assertIn("the spawned Sherman use US's unit models", r.errors[0].message)
        self.assertIn("would crash as the match starts", r.errors[0].message)


class Rules(unittest.TestCase):
    def test_the_kinds_of_unit(self):
        self.assertTrue(unitcheck.is_unit(Obj("TBatimentDescriptor")))
        self.assertFalse(unitcheck.is_unit(Obj("TAcknowUnitDescriptor")))  # has a Nationalite, isn't a unit
        base = game()
        base.objects["$/Ack"] = Obj("TAcknowUnitDescriptor", {"Nationalite": num(1)})
        self.assertEqual(said(run(Op("set", "$/Ack", "Nationalite", num(9)), base=base)), [])  # not a unit: not asked


if __name__ == "__main__":
    unittest.main()
