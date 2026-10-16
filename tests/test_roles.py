"""A plane's role and what a weapon can hit (ruse_studio.roles), on a made-up game: a Stuka (fighter-bomber, its dive
bomb on a forward mount), a B-25 (bomber, carpet bombs in a bomb bay), an ME109 (fighter, a cannon that hits planes)
and a Panzer IV (an AP and an HE shell on one turret). What the game ties together was seen in T50-T52 (2026-10-14):
a bomber drops only from a bomb bay, and what a weapon hits comes from its ammo's Arme."""
import struct
import tempfile
import tomllib
import unittest
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod import Edat
from rusemod.build import build_pack, load_mod, load_pack
from rusemod.dic import name_to_key
from rusemod.index import build_index
from rusemod.patch import Engine, Inline, Ref
from rusemod.play import Starter
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import Append, Link, ModEdits

ROOT = Path(__file__).resolve().parents[1]
E = "$/GFX/Everything/"
STUKA, B25, ME109, PANZER = (E + n for n in ("Descriptor_Avion_Junkers_87", "Descriptor_Avion_B25",
                                             "Descriptor_Avion_ME109_GR", "Descriptor_Unit_Panzer_IV_G"))
BOMB, CARPET, CANNON, AP, HE = (E + n for n in ("Ammo_Bombe_pique_Junker", "Ammo_Carpet_bombing_leger",
                                                "Ammo_Canon_air_moyen", "Ammo_Canon_AP_100", "Ammo_Canon_HE_105"))
DIVEBOMB, CARPETS, AIRGUN, APSHELL, HESHELL = (name_to_key(n) for n in ("DIVEBOMB", "CARPETS", "AIRGUN", "APSHELL",
                                                                       "HESHELL"))
AIR_FB, AIR_BL, AIR_F, AIR_REC, RECO_AR, TANK_M = (name_to_key(n) for n in ("AIR_FB", "AIR_BL", "AIR_F", "AIR_REC",
                                                                              "RECO_AR", "TANK_M"))
SCOUT, RECON_CAR = E + "Descriptor_Avion_Grasshopper", E + "Descriptor_Unit_M8_Greyhound"


def i32(v):
    return val(0x02, struct.pack("<i", v))


def u32(v):
    return val(0x03, struct.pack("<I", v))


def key(k):
    return val(0x1D, struct.pack("<Q", k))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def lst(*items):
    return val(0x11, struct.pack("<I", len(items)) + b"".join(items))


def flag(v):
    return val(0x00, struct.pack("<B", v))


def s(i):
    return val(0x07, struct.pack("<I", i))


# classes: 0 TAvionDescriptor, 1 TWeaponDescriptor, 2 TTurretAbsolueDescriptor, 3 TTurretBombardierDescriptor,
# 4 TMountedWeaponDescriptor, 5 TAmmunition, 6 TUniteAuSolDescriptor, 7 TTurretOneAxisDescriptor
P_ROLE, P_AI, P_FLAGS, P_HINT, P_WD, P_TURRETS, P_ABS_MOUNTS, P_BAY_MOUNTS, P_TAG, P_AMMO, P_ID, P_TYPE, P_ARME, \
    P_SHAPE, P_RANGE, P_WD_GROUND, P_ONE_MOUNTS, P_INDIRECT, P_NOPHYS, P_SIGHT, P_G_AI, P_G_CAT, P_G_SIGHT, P_G_FLAGS, \
    P_G_HINT = range(25)


def f32(v):
    return val(0x05, struct.pack("<f", v))


def ground(ai, cat, sight, flags, hint, wd=None):
    values = [(P_G_AI, i32(ai)), (P_G_CAT, i32(cat)), (P_G_SIGHT, f32(sight)),
              (P_G_FLAGS, lst(*(u32(f) for f in flags))), (P_G_HINT, key(hint))]
    return (6, values + ([(P_WD_GROUND, ref(wd, 1))] if wd is not None else []))


def plane(role, ai, flags, hint, wd):
    return (0, [(P_ROLE, i32(role)), (P_AI, i32(ai)), (P_FLAGS, lst(*(u32(f) for f in flags))), (P_HINT, key(hint)),
                (P_WD, ref(wd, 1))])


def ammo(n, kind, arme, shape=None, air=False):
    values = [(P_ID, u32(n)), (P_TYPE, key(kind)), (P_ARME, i32(arme)), (P_RANGE, val(0x05, struct.pack("<f", 9e4)))]
    if shape is not None:
        values.append((P_SHAPE, i32(shape)))
    if air:
        values += [(P_INDIRECT, flag(1)), (P_NOPHYS, flag(1))]
    return (5, values)


UNITS = make_ndf(
    objects=[plane(2, 1, [2, 101, 21], AIR_FB, 1),                                # 0 Stuka
             (1, [(P_TURRETS, lst(ref(2, 2)))]),                                 # 1 its weapons
             (2, [(P_ABS_MOUNTS, lst(ref(3, 4)))]),                              # 2 its bomb mount (forward)
             (4, [(P_TAG, s(0)), (P_AMMO, ref(9, 5))]),                          # 3 the dive bomb
             plane(3, 4, [2, 13, 21], AIR_BL, 5),                                 # 4 B-25
             (1, [(P_TURRETS, lst(ref(6, 3)))]),                                 # 5 its weapons
             (3, [(P_BAY_MOUNTS, lst(ref(7, 4)))]),                              # 6 its bomb bay
             (4, [(P_TAG, s(0)), (P_AMMO, ref(10, 5))]),                         # 7 carpet bombs
             plane(1, 1, [2, 100, 21], AIR_F, 11),                                # 8 ME109
             ammo(1, DIVEBOMB, 3, 4),                                            # 9 dive bomb
             ammo(2, CARPETS, 3, 4),                                             # 10 carpet bombs
             (1, [(P_TURRETS, lst(ref(12, 2)))]),                                # 11 ME109's weapons
             (2, [(P_ABS_MOUNTS, lst(ref(13, 4)))]),                             # 12 its cannon mount
             (4, [(P_TAG, s(0)), (P_AMMO, ref(14, 5))]),                         # 13 its cannon
             ammo(3, AIRGUN, 1, 3, air=True),                                    # 14 air cannon
             ground(1, 2, 104000, [10, 55, 21, 11], TANK_M, 16),                 # 15 Panzer IV
             (1, [(P_TURRETS, lst(ref(17, 7)))]),                                # 16 its weapons
             (7, [(P_ONE_MOUNTS, lst(ref(18, 4), ref(19, 4)))]),                 # 17 its turret
             (4, [(P_TAG, s(0)), (P_AMMO, ref(20, 5))]),                         # 18 AP
             (4, [(P_TAG, s(1)), (P_AMMO, ref(21, 5))]),                         # 19 HE
             ammo(4, APSHELL, 5),                                                # 20 AP shell
             ammo(5, HESHELL, 3, 1),                                             # 21 HE shell
             (0, [(P_ROLE, i32(5)), (P_AI, i32(3)), (P_FLAGS, lst(u32(2), u32(99), u32(70))), (P_HINT, key(AIR_REC)),
                  (P_SIGHT, f32(195000))]),                                      # 22 Grasshopper (a scout, unarmed)
             ground(3, 1, 234000, [10], RECO_AR)],                               # 23 Greyhound (recon)
    classes=["TAvionDescriptor", "TWeaponDescriptor", "TTurretAbsolueDescriptor", "TTurretBombardierDescriptor",
             "TMountedWeaponDescriptor", "TAmmunition", "TUniteAuSolDescriptor", "TTurretOneAxisDescriptor"],
    props=[("CategoryVolant", 0), ("CategorieIA", 0), ("InitialFlagSet", 0), ("TypeUnitHintToken", 0),
           ("WeaponDescriptor", 0), ("TurretDescriptorList", 1), ("MountedWeaponDescriptorList", 2),
           ("MountedWeaponDescriptorList", 3), ("EffectTag", 4), ("Ammunition", 4), ("AmmunitionId", 5),
           ("TypeName", 5), ("Arme", 5), ("ProjectileType", 5), ("PorteeMaximale", 5), ("WeaponDescriptor", 6),
           ("MountedWeaponDescriptorList", 7), ("TirIndirect", 5), ("FX_tir_sans_physic", 5), ("DetectionBase", 0),
           ("CategorieIA", 6), ("Category", 6), ("DetectionBase", 6), ("InitialFlagSet", 6), ("TypeUnitHintToken", 6)],
    strings=["weapon_effet_tag1", "weapon_effet_tag2"],
    exports={0: "GFX/Everything/Descriptor_Avion_Junkers_87", 4: "GFX/Everything/Descriptor_Avion_B25",
             8: "GFX/Everything/Descriptor_Avion_ME109_GR", 9: "GFX/Everything/Ammo_Bombe_pique_Junker",
             10: "GFX/Everything/Ammo_Carpet_bombing_leger", 14: "GFX/Everything/Ammo_Canon_air_moyen",
             15: "GFX/Everything/Descriptor_Unit_Panzer_IV_G", 20: "GFX/Everything/Ammo_Canon_AP_100",
             21: "GFX/Everything/Ammo_Canon_HE_105", 22: "GFX/Everything/Descriptor_Avion_Grasshopper",
             23: "GFX/Everything/Descriptor_Unit_M8_Greyhound"},
    topo=[0, 4, 8, 9, 10, 14, 15, 20, 21, 22, 23])


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("file", "everything.cpp.gladndfbin", UNITS)]))
    texts = [(DIVEBOMB, "Diving bomb"), (CARPETS, "Carpet bombing"), (AIRGUN, "Aircraft cannon"),
             (APSHELL, "AP shell"), (HESHELL, "HE shell")]
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", "us\\", [("file", "baseunite.dic", make_dic(texts))])])]))


class Roles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        (cls.game / "RUSE.exe").write_bytes(b"MZ")
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
        return Path(self.api.new_mod("Roles")["current"])

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
    def mounts(objs, unit, prop="WeaponDescriptor"):
        """[(each mount's class, [the ammo each of its weapons fires])] of a unit, as built."""
        def obj(v):
            return objs[v.target] if isinstance(v, Ref) else v.obj
        out = []
        for t in obj(objs[unit].props[prop]).props["TurretDescriptorList"].items:
            turret = obj(t)
            out.append((turret.cls, [obj(m).props["Ammunition"].target
                                     for m in turret.props["MountedWeaponDescriptorList"].items]))
        return out

    def test_roles_as_the_game_has_them(self):
        for unit, role, bombs in ((STUKA, "fighter_bomber", True), (B25, "bomber", True), (ME109, "fighter", False)):
            info = self.api.plane_role(unit)
            self.assertEqual((info["role"], info["game"], info["bombs"]), (role, role, bombs))
        self.assertEqual([r["id"] for r in info["roles"]], ["fighter", "fighter_bomber", "bomber", "scout"])
        self.assertEqual([r["id"] for r in info["roles"] if r["seen"]], ["bomber"])  # T50
        self.assertFalse(info["editable"])  # no mod yet
        with self.assertRaises(StudioError):
            self.api.plane_role(PANZER)

    def test_a_fighter_bomber_made_a_bomber_drops_from_a_bomb_bay(self):
        folder = self.mod()
        info = self.api.set_plane_role(STUKA, "bomber")
        self.assertEqual((info["role"], info["game"]), ("bomber", "fighter_bomber"))
        rndf = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"is clone {B25}:WeaponDescriptor.TurretDescriptorList[class=TTurretBombardierDescriptor]", rndf)  # the B-25's bay, copied
        objs = self.built(folder)
        stuka = objs[STUKA].props
        self.assertEqual((int(stuka["CategoryVolant"].value), int(stuka["CategorieIA"].value)), (3, 4))
        self.assertEqual([int(f.value) for f in stuka["InitialFlagSet"].items], [2, 13, 21])  # the bomber's flags
        self.assertEqual(stuka["TypeUnitHintToken"], objs[B25].props["TypeUnitHintToken"])  # a bomber's words
        self.assertEqual(self.mounts(objs, STUKA), [("TTurretBombardierDescriptor", [BOMB])])  # its own bomb, in a bay
        self.assertEqual(self.mounts(objs, B25), [("TTurretBombardierDescriptor", [CARPET])])  # the B-25 untouched
        # the game's role again: nothing of it is left in the mod
        info = self.api.set_plane_role(STUKA, None)
        self.assertEqual(info["role"], "fighter_bomber")
        edits = ModEdits(folder)
        self.assertEqual((edits.edits, edits.new_units), ({}, {}))

    def test_the_bombs_it_drops_are_the_mods_pick(self):
        folder = self.mod()
        weapon = self.api.weapons(STUKA)["weapons"][0]["address"]
        self.api.set_ammo(STUKA, weapon, CARPET)  # the player's report: carpet bombs on a fighter-bomber
        self.api.set_plane_role(STUKA, "bomber")
        objs = self.built(folder)
        self.assertEqual(self.mounts(objs, STUKA), [("TTurretBombardierDescriptor", [CARPET])])

    def test_the_bomb_bay_shows_on_its_page_and_its_bombs_change_there(self):
        folder = self.mod()
        self.api.set_plane_role(STUKA, "bomber")
        ws = self.api.weapons(STUKA)["weapons"]
        self.assertEqual(len(ws), 1)  # the bay's weapon in place of the Stuka's own, which is gone
        self.assertTrue(ws[0]["address"].startswith(E + "Role_"))
        self.assertEqual(ws[0]["ammo"]["address"], BOMB)
        self.api.set_ammo(STUKA, ws[0]["address"], CARPET)
        self.assertEqual(self.api.weapons(STUKA)["weapons"][0]["ammo"]["address"], CARPET)
        objs = self.built(folder)
        self.assertEqual(self.mounts(objs, STUKA), [("TTurretBombardierDescriptor", [CARPET])])

    def test_a_bomber_made_a_fighter_bomber_gets_a_forward_mount(self):
        folder = self.mod()
        self.api.set_plane_role(B25, "fighter_bomber")
        objs = self.built(folder)
        self.assertEqual(int(objs[B25].props["CategoryVolant"].value), 2)
        self.assertEqual([int(f.value) for f in objs[B25].props["InitialFlagSet"].items], [2, 101, 21])
        self.assertEqual(self.mounts(objs, B25), [("TTurretAbsolueDescriptor", [CARPET])])  # the Stuka's mount, copied

    def test_a_plane_with_no_bombs_cant_be_a_bomber_and_a_fighter_needs_no_mount(self):
        folder = self.mod()
        with self.assertRaises(StudioError) as cm:
            self.api.set_plane_role(ME109, "bomber")
        self.assertIn("no bombs", str(cm.exception))
        self.api.set_plane_role(STUKA, "fighter")  # a fighter drops bombs as it is (T51)
        objs = self.built(folder)
        self.assertEqual(int(objs[STUKA].props["CategoryVolant"].value), 1)
        self.assertEqual(self.mounts(objs, STUKA), [("TTurretAbsolueDescriptor", [BOMB])])
        with self.assertRaises(StudioError):
            self.api.set_plane_role(STUKA, "paratroop")

    def test_an_armed_scout_keeps_the_fighters_behaviour(self):
        # every game scout has 99 and 70 and no 21, and the scouts' sight (DetectionBase). The flags pick the plane's
        # behaviour, 100 first, then 99: a plane with 99 alone gets the scout's, which has no attack, and crashed the
        # game when sent to attack (T53-T56). An armed scout also gets 100, so it behaves as a fighter
        folder = self.mod()
        self.assertTrue(self.api.plane_role(STUKA)["armed"])
        self.api.set_plane_role(STUKA, "scout")
        objs = self.built(folder)
        props = objs[STUKA].props
        self.assertEqual([int(f.value) for f in props["InitialFlagSet"].items], [2, 100, 99, 70])
        self.assertEqual(float(props["DetectionBase"].value), 195000.0)  # the scouts' sight, which only scouts have
        self.assertEqual(int(props["CategoryVolant"].value), 5)
        self.api.set_plane_role(STUKA, "fighter_bomber")  # the scouts' sight goes with the role
        self.assertNotIn("DetectionBase", self.built(folder)[STUKA].props)
        self.api.set_plane_role(STUKA, None)
        self.assertEqual(ModEdits(folder).edits, {})  # its own flags back: nothing left to write

    def test_an_unarmed_scout_is_as_the_games(self):
        info = self.api.plane_role(SCOUT)
        self.assertEqual((info["role"], info["armed"]), ("scout", False))
        folder = self.mod()
        self.api.set_plane_role(SCOUT, "fighter")
        self.assertEqual([int(f.value) for f in self.built(folder)[SCOUT].props["InitialFlagSet"].items], [2, 100, 21])
        self.api.set_plane_role(SCOUT, "scout")  # its own role again: nothing left
        self.assertEqual(ModEdits(folder).edits, {})

    def test_a_tank_made_a_recon_unit(self):
        # T56: a Panzer IV with the recon cars' values worked as recon; the longer sight alone did not
        self.assertEqual(self.api.ground_role(PANZER)["role"], "game")
        greyhound = self.api.ground_role(RECON_CAR)
        self.assertEqual((greyhound["role"], greyhound["why"]), ("recon", "no_mod"))
        folder = self.mod()
        self.assertEqual(self.api.ground_role(RECON_CAR)["why"], "ground_role_recon_already")
        info = self.api.set_ground_role(PANZER, "recon")
        self.assertEqual((info["role"], info["game"]), ("recon", "game"))
        props = self.built(folder)[PANZER].props
        self.assertEqual((int(props["CategorieIA"].value), int(props["Category"].value)), (3, 1))
        self.assertEqual(float(props["DetectionBase"].value), 234000.0)
        self.assertEqual([int(f.value) for f in props["InitialFlagSet"].items], [10])  # no 55, 21, 11
        self.assertEqual(props["TypeUnitHintToken"], self.built(folder)[RECON_CAR].props["TypeUnitHintToken"])
        self.api.set_ground_role(PANZER, None)
        self.assertEqual(ModEdits(folder).edits, {})
        with self.assertRaises(StudioError):
            self.api.set_ground_role(STUKA, "recon")

    def test_a_copy_of_a_plane_made_a_bomber(self):
        folder = self.mod()
        made = self.api.new_unit(STUKA, "Heavy Stuka", 20)
        unit = made.get("address") or made
        self.assertEqual(self.api.set_plane_role(unit, "bomber")["role"], "bomber")
        objs = self.built(folder)
        self.assertEqual(self.mounts(objs, unit), [("TTurretBombardierDescriptor", [BOMB])])
        self.assertEqual(self.mounts(objs, STUKA), [("TTurretAbsolueDescriptor", [BOMB])])  # the game's Stuka as it was

    def test_a_tank_round_that_hits_planes_and_back(self):
        folder = self.mod()
        ws = self.api.weapons(PANZER)["weapons"]
        self.assertEqual([(w["hits"], w["game_hits"]) for w in ws], [("ground", "ground")] * 2)
        res = self.api.set_weapon_hits(PANZER, ws[0]["address"], "planes")
        copy = res["ammo"]
        self.assertTrue(copy.rsplit("/", 1)[-1].startswith("Ammo_Hits_"))
        self.assertEqual(self.api.weapons(PANZER)["weapons"][0]["hits"], "planes")
        objs = self.built(folder)
        marks = objs[copy].props
        self.assertEqual((int(marks["Arme"].value), int(marks["ProjectileType"].value), int(marks["TirIndirect"].value),
                          int(marks["FX_tir_sans_physic"].value)), (1, 3, 1, 1))  # the AA guns' marks (T52)
        self.assertEqual(self.mounts(objs, PANZER), [("TTurretOneAxisDescriptor", [copy, HE])])
        # back to the ground: its own AP shell again, and the copy goes
        self.api.set_weapon_hits(PANZER, ws[0]["address"], "ground")
        w = self.api.weapons(PANZER)["weapons"][0]
        self.assertEqual((w["hits"], w["ammo"]["address"]), ("ground", AP))
        self.assertNotIn(copy, ModEdits(folder).new_units)

    def test_both_adds_a_second_weapon_beside_it(self):
        folder = self.mod()
        he = self.api.weapons(PANZER)["weapons"][1]["address"]
        self.api.set_weapon_hits(PANZER, he, "both")
        ws = self.api.weapons(PANZER)["weapons"]
        self.assertEqual([w["hits"] for w in ws], ["ground", "both"])
        self.assertEqual(ws[1]["ammo"]["address"], HE)  # it keeps its own shell
        edits = ModEdits(folder)
        added = [e.value for e in edits.edits.values() if isinstance(e.value, Append)]
        self.assertEqual(len(added), 1)  # MountedWeaponDescriptorList += [...], read back as written
        objs = self.built(folder)
        (cls, fired), = self.mounts(objs, PANZER)
        self.assertEqual(fired[:2], [AP, HE])
        self.assertEqual(int(objs[fired[2]].props["Arme"].value), 1)  # the second: an anti-plane copy of the HE
        # ground again: the second weapon and its ammo go
        self.api.set_weapon_hits(PANZER, he, "ground")
        edits = ModEdits(folder)
        self.assertEqual((edits.edits, edits.new_units), ({}, {}))

    def test_a_planes_gun_made_to_hit_the_ground(self):
        folder = self.mod()
        gun = self.api.weapons(ME109)["weapons"][0]
        self.assertEqual(gun["hits"], "planes")
        copy = self.api.set_weapon_hits(ME109, gun["address"], "ground")["ammo"]
        objs = self.built(folder)
        props = objs[copy].props
        # as every plane's ground ammo has it (strafing guns, rockets, Rudel's cannon): T54, 2026-10-14, a fighter's
        # cannon left with its air-to-air marks flew the strafing pass and fired nothing
        self.assertEqual((int(props["Arme"].value), int(props["ProjectileType"].value), int(props["TirIndirect"].value)),
                         (3, 4, 1))
        self.assertEqual(float(props["PorteeMaximale"].value), 208000.0)  # the cannon's own 90,000 is too short

    def test_nothing_without_a_mod(self):
        with self.assertRaises(StudioError):
            self.api.set_plane_role(STUKA, "bomber")
        with self.assertRaises(StudioError):
            self.api.set_weapon_hits(PANZER, self.api.weapons(PANZER)["weapons"][0]["address"], "planes")
        self.mod()
        with self.assertRaises(StudioError):
            self.api.set_plane_role(STUKA, "zeppelin")
        with self.assertRaises(StudioError):
            self.api.set_weapon_hits(PANZER, self.api.weapons(PANZER)["weapons"][0]["address"], "space")


class OnThePage(unittest.TestCase):
    def test_the_controls_their_words_and_the_preview(self):
        ui = ROOT / "src" / "ruse_studio" / "ui"
        app, fake = (ui / "app.js").read_text(encoding="utf-8"), (ui / "fake-api.js").read_text(encoding="utf-8")
        for needle in ("function roleGroup", "api().plane_role(", "api().set_plane_role(", "function weaponHits",
                       "api().set_weapon_hits(", "function groundRoleGroup", "api().ground_role(",
                       "api().set_ground_role("):
            self.assertIn(needle, app)
        for needle in ("plane_role: async", "set_plane_role: async", "set_weapon_hits: async", "ground_role: async",
                       "set_ground_role: async"):
            self.assertIn(needle, fake)
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        langs = set(words["language"])
        keys = ("role_title", "role_help", "role_fighter", "role_fighter_bomber", "role_bomber", "role_scout",
                "role_paratroop", "role_paratroop_why", "role_not_tried", "role_bombs_moved", "tip_role_pick",
                "tip_role_undo", "hits", "hits_ground", "hits_planes", "hits_both", "tip_hits", "hits_not_tried",
                "role_scout_armed", "ground_role_help", "ground_role_game", "ground_role_recon", "tip_ground_role",
                "ground_role_recon_already")
        for k in keys:
            with self.subTest(word=k):
                self.assertEqual(set(words[k]), langs)
                self.assertIn(f"{k}:", fake)  # the preview shows it too
        self.assertTrue(all("{role}" in t for t in words["role_not_tried"].values()))


if __name__ == "__main__":
    unittest.main()
