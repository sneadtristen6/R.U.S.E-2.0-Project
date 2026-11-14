"""Scenarios: two players' Studio mods in one Launcher mod set (the owner, 2026-11-13 overnight: "Usual and unusual
situations. Player can find themselves in when making new mods in our apps"). Each mod made in the Studio as a
player makes it and exported (Export… puts it in the Launcher's library: the two apps share the platform folder), then
a mod set made on the Launcher's screen (new_set), checked as the set screen checks it before Play (set_check), and
played (play: the mods built into the PC's modded copy of the made-up game; nothing starts). Two mods changing the same
value of the same unit; two mods each making a new unit of the same name; one mod hiding a unit another's copy is
researched from; two mods filling one group past six.

Each test marked expectedFailure shows a finding (its number in the comment above it; the agent's report lists them);
it passes once the finding is mended.

Checked our_tools.json: none of its tools is for this; this file reads no program: the made-up game's stand-in
RUSE.exe (tests/test_studio.py's way) is only where Play's stand-in starts it."""
import time
import unittest

from rusemod import Edat, Ndf
from rusemod.play import SHARED
from ruse_launcher.api import LauncherApi
from test_scenarios_units_base import M1, M2, H1, Player

GAME_EXE = "RUSE.exe"


def wait(api, job: str, seconds: float = 120) -> dict:
    end = time.time() + seconds
    while api.job(job)["state"] == "running" and time.time() < end:
        time.sleep(0.05)
    return api.job(job)


class TwoModsInOneSet(Player):
    def launcher(self) -> LauncherApi:
        return LauncherApi(game_dir=self.game, home=self.home, instances=self.home / "copies",
                           open_url=lambda url: None, start_game=self.started.append, steam_running=lambda: True,
                           wait=lambda s: None)

    def exported(self, name: str, make) -> str:
        """A mod `name` made with `make()` (the Studio's calls), exported: its id in the Launcher's library."""
        self.mod(name)
        make()
        j = wait(self.api, self.call("export_mod", "1.0.0", "A player", "")["job"])
        self.assertEqual(j["state"], "done", j)
        return j["result"]["library"]

    def built_copy(self) -> Ndf:
        pack = Edat((self.home / "copies" / SHARED / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        return Ndf(pack.read(pack.find("everything.cpp.gladndfbin")))

    def play(self, launcher, mods) -> tuple[dict, dict]:
        set_id = launcher.new_set("Both", mods)["set"]
        return launcher.set_check(set_id), wait(launcher, launcher.play(set_id)["job"])

    def test_two_mods_changing_the_same_value(self):
        a = self.exported("Tougher", lambda: self.call("edit", M1, "SeuilMort", 20, "", ""))
        b = self.exported("Toughest", lambda: self.call("edit", M1, "SeuilMort", 30, "", ""))
        check, j = self.play(self.launcher(), [a, b])
        self.assertEqual(j["state"], "done", j)
        self.assertEqual(self.value(self.built_copy(), M1, "SeuilMort").scalar(), 30)    # the later mod's
        print("\ntwo mods, one value: set_check", check, "| lines:", [ln for ln in j["lines"] if "SeuilMort" in ln])

    # U-13: the set screen says nothing when two Studio mods change the same value (set_check reads .rmod mods only,
    # rusemod.rmod.clashes): the later one's wins, and the player isn't told the earlier's change is gone
    @unittest.expectedFailure
    def test_the_set_screen_says_when_two_mods_change_the_same_value(self):
        a = self.exported("Tougher", lambda: self.call("edit", M1, "SeuilMort", 20, "", ""))
        b = self.exported("Toughest", lambda: self.call("edit", M1, "SeuilMort", 30, "", ""))
        launcher = self.launcher()
        check = launcher.set_check(launcher.new_set("Both", [a, b])["set"])
        self.assertTrue(check["soft"], check)

    def test_two_mods_each_making_a_unit_of_the_same_name(self):
        """Two players each made a "Super Tank" from the same tank: the same address in both mods."""
        a = self.exported("Alpha", lambda: self.call("new_unit", M1, "Super Tank", 40, -1, -1, False, None))
        b = self.exported("Bravo", lambda: self.call("new_unit", H1, "Super Tank", 60, -1, -1, False, None))
        launcher = self.launcher()
        check, j = self.play(launcher, [a, b])
        print("\ntwo mods, one unit name: set_check", check, "| state", j["state"], "|", j.get("message"),
              "|", [ln for ln in j["lines"] if "error" in ln.lower()][:6])
        if j["state"] == "failed":                       # refused: in words a player can act on
            self.assertTrue(j["message"])
        self.assertEqual(self.started, [] if j["state"] == "failed" else [self.home / "copies" / SHARED / GAME_EXE])

    # U-14: two mods that each make a new unit of the same name (two players' "Super Tank") can't be played together,
    # and the set screen doesn't say so before Play (set_check finds no clash between Studio mods)
    @unittest.expectedFailure
    def test_the_set_screen_says_two_mods_make_a_unit_of_the_same_name(self):
        a = self.exported("Alpha", lambda: self.call("new_unit", M1, "Super Tank", 40, -1, -1, False, None))
        b = self.exported("Bravo", lambda: self.call("new_unit", H1, "Super Tank", 60, -1, -1, False, None))
        launcher = self.launcher()
        check, j = self.play(launcher, [a, b])
        self.assertTrue(j["state"] == "done" or check["hard"], (check, j.get("message")))

    def hidden_parent(self, hider_first: bool) -> tuple[dict, dict, str]:
        """Mod A takes M1 out of the menus (the board's take-out: its upgrade M2 made buyable from the start); mod B
        has a copy of M2 (an upgrade of M1). Played together, A loaded first or B."""
        a = self.exported("No M1", lambda: self.call("board_take_out", 0, M1, None, "us"))
        made = {}
        b = self.exported("M2 again", lambda: made.update(
            self.call("new_unit", M2, "M2 Again", 40, -1, -1, False, None)))
        check, j = self.play(self.launcher(), [a, b] if hider_first else [b, a])
        return check, j, made["address"]

    def test_one_mod_hides_the_unit_anothers_copy_is_researched_from(self):
        """A first: B's copy is made from M2 as A left it, buyable from the start: played. B first: the copy is shown
        and researched from M1, which A hides: Play is refused before the game starts, the build's words say why and
        what to do, nothing is written (the set screen said nothing before Play: set_check reads .rmod mods only)."""
        check, j, copy = self.hidden_parent(True)
        self.assertEqual(j["state"], "done", j)
        self.assertIsNone(self.value(self.built_copy(), copy, "UpgradeRequire"))
        started = len(self.started)
        check, j, copy = self.hidden_parent(False)
        self.assertEqual((check["hard"], j["state"]), ([], "failed"))
        self.assertTrue(any("the game stops when that build menu opens" in e for e in j["errors"]), j["errors"])
        self.assertEqual(len(self.started), started)                         # nothing started

    def test_two_mods_filling_one_group_past_six(self):
        """Each mod puts three copies in M1's line (M1, M2 and three: five, within six); together it holds eight:
        the owner's pick (2026-10-31): built with a warning."""
        def three(tag):
            def make():
                for k in range(3):
                    self.call("new_unit", M1, f"{tag} {k}", 40, -1, -1, False, None)
            return make
        a = self.exported("Group A", three("A"))
        b = self.exported("Group B", three("B"))
        check, j = self.play(self.launcher(), [a, b])
        self.assertEqual(j["state"], "done", j)
        warned = [ln for ln in j["lines"] if "warning" in ln.lower()]
        print("\ngroup past six across mods:", warned[:4])
        self.assertTrue(any("6" in ln for ln in warned), j["lines"])


if __name__ == "__main__":
    unittest.main()
