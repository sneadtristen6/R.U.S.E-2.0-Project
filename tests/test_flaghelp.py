"""The flag guide and its checks (rusemod.flaginfo; the owner, 2026-10-15: "each flag should tell you exactly what each
flag is", "warn people if it's a known crash and ... not allow them to start the game if it's going to crash"): every
flag explained, the Studio's judge of one unit's flags, and the build's new crash: a plane with weapons given the
recon flag 99 without the fighter flag 100 (T53-T56). Made-up units, no game files needed."""
import unittest

from rusemod import flaginfo
from rusemod.patch import Engine, Game, Inline, Obj, Op, Ref, Text, num, nums
from rusemod.resolve import ModInfo
from rusemod.unitflags import armed, crashes

PLANE, TANK, TRUCK, SQUAD = "TAvionDescriptor", "TUniteAuSolDescriptor", "TTruckDescriptor", "TInfanterieDescriptor"


class Guide(unittest.TestCase):
    def test_every_flag_explained(self):
        g = flaginfo.guide()
        self.assertEqual(sorted(g), list(range(105)))
        for n, e in g.items():
            with self.subTest(flag=n):
                self.assertIn(e["group"], flaginfo.GROUPS)
                self.assertIn(e["sure"], flaginfo.SURE)
                self.assertTrue(e["what"] and e["does"] and e["use"])
                self.assertIn(e["danger"], ("", "crash", "breaks"))
                self.assertEqual(bool(e["danger"]), bool(e["danger_why"]))

    def test_every_language_explains_every_flag(self):
        import tomllib
        from pathlib import Path
        from rusemod import schema
        root = Path(flaginfo.__file__).parent
        english = flaginfo.guide("us")
        for lang in schema.LANGS:
            if lang == "us":
                continue
            with self.subTest(lang=lang):
                own = tomllib.loads((root / f"flaginfo_{lang}.toml").read_text(encoding="utf-8"))
                self.assertEqual(sorted(int(n) for n in own), list(range(105)))
                for n, e in english.items():
                    mine = own[str(n)]
                    for key in ("what", "does", "use"):
                        self.assertTrue(mine.get(key), (lang, n, key))
                    self.assertEqual(bool(mine.get("danger_why")), bool(e["danger_why"]), (lang, n))
                g = flaginfo.guide(lang)
                self.assertEqual(g[62]["danger"], "crash")         # the kind and danger stay the English file's
                self.assertNotEqual(g[62]["what"], english[62]["what"])
        self.assertEqual(flaginfo.guide("xx")[11]["what"], english[11]["what"])  # no file: English

    def test_the_known_crashes_are_marked(self):
        g = flaginfo.guide()
        self.assertEqual(sorted(n for n, e in g.items() if e["danger"] == "crash"), [59, 62, 63, 99])
        for n in (62, 63):
            self.assertEqual(g[n]["sure"], "tried")

    def test_the_game_s_running_state_is_its_own_group(self):
        g = flaginfo.guide()
        for n in (26, 27, 54, 65, 90, 91, 104):
            self.assertEqual(g[n]["group"], "state", n)
        for n in (9, 12, 15, 16, 32, 39, 45, 74):
            self.assertEqual((g[n]["group"], g[n]["sure"]), ("unused", "unused"), n)


def levels(found):
    return sorted((p["level"], p["flag"]) for p in found)


class Judge(unittest.TestCase):
    def test_truck_flags_crash_off_a_truck(self):
        self.assertEqual(levels(flaginfo.judge(TANK, [10, 62, 63])), [("error", 62), ("error", 63)])
        self.assertEqual(flaginfo.judge(TRUCK, [44, 62, 63]), [])
        self.assertEqual(flaginfo.judge(TANK, [62], had=[62]), [])  # the game's own data: not the mod's doing

    def test_an_armed_recon_plane_without_100(self):
        self.assertEqual(levels(flaginfo.judge(PLANE, [2, 99], armed=True)), [("error", 99)])
        self.assertEqual(flaginfo.judge(PLANE, [2, 99, 100], armed=True), [])  # an armed scout: it can attack
        self.assertEqual(flaginfo.judge(PLANE, [2, 99], armed=False), [])      # a scout without guns
        self.assertEqual(flaginfo.judge(PLANE, [2, 70, 99], had=[2, 70, 99], armed=True), [])  # the Potez, as shipped

    def test_59_and_the_unit_it_drops(self):
        self.assertEqual(levels(flaginfo.judge(TANK, [59])), [("error", 59)])
        self.assertEqual(levels(flaginfo.judge(PLANE, [2, 59], drops=False)), [("error", 59)])
        self.assertEqual(flaginfo.judge(PLANE, [2, 59], drops=True), [])

    def test_what_is_expected_to_break_a_unit_is_a_warning(self):
        self.assertEqual(levels(flaginfo.judge(TANK, [2, 4, 42, 49, 76])),
                         [("warning", 2), ("warning", 4), ("warning", 42), ("warning", 49), ("warning", 76)])
        self.assertEqual(levels(flaginfo.judge(TANK, [10], had=[10, 22, 43])), [("warning", 22), ("warning", 43)])
        self.assertEqual(flaginfo.judge(SQUAD, [42], had=[42]), [])
        self.assertEqual(levels(flaginfo.judge(PLANE, [99])), [("warning", 2)])  # a plane without 2
        self.assertEqual(levels(flaginfo.judge(TANK, [10, 130])), [("warning", 130)])


def weapon():
    return Obj("TMountedWeaponDescriptor", {"Ammunition": Ref("$/Ammo")})


def game():
    """A fighter-bomber with a gun written in it, a recon plane as the game ships them (99 and a linked gun), and a
    tank."""
    def unit(cls, flags, **props):
        return Obj(cls, {"ClassNameForDebug": Text("string", "x"), "InitialFlagSet": nums(flags, "uint32"), **props})
    return Game(objects={
        "$/Stuka": unit(PLANE, [2, 10, 101], Turrets=Inline(Obj("TTurret", {"Weapon": Inline(weapon())}))),
        "$/Potez": unit(PLANE, [2, 10, 70, 99], Turrets=Inline(Obj("TTurret", {"Weapon": Ref("$/Gun")}))),
        "$/Gun": weapon(),
        "$/Ammo": Obj("TAmmunition", {"Puissance": num(10)}),
        "$/Stuart": unit(TANK, [10, 11, 21, 22, 55]),
    })


def run(*ops):
    for op in ops:
        op.mod, op.file, op.line = "m", "m.rndf", op.line or 1
    return Engine(game()).run([(ModInfo("m"), list(ops))])


class ScoutCrash(unittest.TestCase):
    """99 without 100 on a plane with weapons crashes R.U.S.E. when the plane is sent to attack: the build stops."""

    def test_armed(self):
        g = game()
        self.assertTrue(armed(g.objects["$/Stuka"]))
        self.assertTrue(armed(g.objects["$/Potez"], g.objects))
        self.assertFalse(armed(g.objects["$/Stuart"], g.objects))

    def test_99_on_a_fighter_bomber_stops_the_build(self):
        r = run(Op("append", "$/Stuka", "InitialFlagSet", [num(99)], line=4))
        self.assertEqual(len(r.errors), 1)
        self.assertIn("m (m.rndf:4): $/Stuka: flag 99 (avion_reco, recon plane) on a plane with weapons and without "
                      "flag 100", r.errors[0].message)

    def test_with_100_it_s_an_armed_scout(self):
        self.assertEqual(run(Op("append", "$/Stuka", "InitialFlagSet", [num(99), num(100)])).errors, [])

    def test_the_game_s_own_armed_recon_planes_and_their_copies(self):
        self.assertEqual(run(Op("append", "$/Potez", "InitialFlagSet", [num(71)]),
                             Op("clone", "$/Potez2", source="$/Potez")).errors, [])

    def test_a_new_plane_given_99(self):
        r = run(Op("clone", "$/Recon_Stuka", source="$/Stuka",
                   body=[Op("append", path="InitialFlagSet", value=[num(99)], line=2)], line=2))
        self.assertEqual(len(r.errors), 1)
        self.assertIn("$/Recon_Stuka: flag 99", r.errors[0].message)

    def test_crashes_says_why(self):
        g = game()
        why = crashes(Obj(PLANE, {"InitialFlagSet": nums([2, 99], "uint32"), "W": Inline(weapon())}))
        self.assertEqual(len(why), 1)
        self.assertIn("add 100 too", why[0])
        self.assertEqual(crashes(g.objects["$/Potez"], {99}, g.objects), [])


class StudioCheck(unittest.TestCase):
    """StudioApi.flag_check: the unit's kind, weapons, the unit it drops and the game's own flags from the index."""

    def api(self, cls, flags, weapons=0):
        import tempfile
        from pathlib import Path
        from ruse_studio.api import StudioApi
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        api = StudioApi(game_dir=Path(tmp.name) / "R.U.S.E", home=Path(tmp.name) / "home")
        unit = "$/GFX/Everything/Descriptor_Unit_X"
        parts = [f"{unit}:W{i}" for i in range(weapons)]

        class Ix:
            def show(self, a):
                if a == unit:
                    return {"class": cls, "values": [(f"InitialFlagSet[{i}]", n, None) for i, n in enumerate(flags)]}
                return {"class": "TMountedWeaponDescriptor", "values": []}

            def clone_plan(self, a):
                return {"copied": parts, "shared": []}

            def uses(self, a):
                return []

            def close(self):
                pass
        api._open = lambda: Ix()
        api._edits = lambda: None
        return api, unit

    def test_the_unit_s_own_flags_and_a_set_to_try(self):
        api, unit = self.api(PLANE, [2, 10, 101], weapons=2)
        self.assertEqual(api.flag_check(unit), {"problems": [], "blocked": False, "adding": api.flag_check(unit)["adding"]})
        res = api.flag_check(unit, [2, 10, 101, 99])
        self.assertTrue(res["blocked"])
        self.assertEqual([(p["level"], p["flag"]) for p in res["problems"]], [("error", 99)])
        adding = api.flag_check(unit)["adding"]
        self.assertEqual((adding[99], adding[62], adding[63]), ("error", "error", "error"))
        self.assertNotIn(100, adding)  # a fighter: nothing wrong with it

    def test_a_truck(self):
        api, unit = self.api(TRUCK, [10, 44, 62])
        self.assertNotIn(63, api.flag_check(unit)["adding"])


class Page(unittest.TestCase):
    def test_the_words_and_the_page(self):
        import tomllib
        from pathlib import Path
        root = Path(__file__).resolve().parents[1] / "src" / "ruse_studio"
        words = tomllib.loads((root / "words.toml").read_text(encoding="utf-8"))
        keys = ["flags_about", "flag_guide", "tip_flag_guide", "flag_guide_title", "flag_guide_lead",
                "flag_guide_search", "flag_guide_none", "flag_how", "flag_sure", "flag_danger_crash",
                "flag_danger_breaks", "flag_this_unit", "flag_crash_head", "flag_warn_head", "flag_take_off",
                "flag_add_this", "flag_put_back", "flag_blocked", "flag_crashes_here", "flag_breaks_here",
                "weapons_how_title", *[f"weapons_how_{i}" for i in range(1, 6)]]
        keys += [f"flag_sure_{s}" for s in flaginfo.SURE]
        keys += [f"flag_group_{g}" for g in flaginfo.GROUPS] + [f"flag_group_{g}_help" for g in flaginfo.GROUPS]
        for key in keys:
            self.assertEqual(len(words[key]), 10, key)
        app = (root / "ui" / "app.js").read_text(encoding="utf-8")
        for needle in ("api().flag_check(", "openFlagGuide(", "renderFlagGuide()", "flagTip(", "weapons-how"):
            self.assertIn(needle, app)
        html = (root / "ui" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="flag-guide"', html)
        fake = (root / "ui" / "fake-api.js").read_text(encoding="utf-8")
        self.assertIn("flag_check: async", fake)


if __name__ == "__main__":
    unittest.main()
