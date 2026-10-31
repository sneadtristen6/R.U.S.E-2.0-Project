"""Fair play (rusemod.fairplay): which copies are offline, our game scripts after the game's match rules, the copy's
record and its self-check, join codes compared, and the Launcher's calls for them."""
import base64
import hashlib
import json
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rusemod import fairplay, pyscript
from rusemod.lock import CodeError, encode_join_code
from rusemod.pyscript import Code, ScriptError, dump, instructions

GAME = Path(os.environ.get("RUSE_GAME", "D:/Steam/steamapps/common/R.U.S.E"))
LOAD_CONST, RETURN_VALUE, LOAD_NAME, POP_TOP, JUMP_ABSOLUTE = 100, 83, 101, 1, 113


def module(code: bytes, consts=(None,), names=()) -> bytes:
    """A made-up module, marshalled the way the game's are."""
    return dump(Code(0, 0, 2, 64, code, consts, names, (), (), (), b"datadir:\\x.py", b"<module>", 1, b""))


def xyz(names) -> bytes:
    """A made-up game script (.xyz) naming `names`."""
    code = b"".join(bytes([LOAD_NAME, i, 0, POP_TOP]) for i in range(len(names))) + bytes([LOAD_CONST, 0, 0, RETURN_VALUE])
    return pyscript.write_xyz(pyscript.Xyz(b"\0" * 16, module(code, names=tuple(names))))


class SwitchedOn(unittest.TestCase):
    """Fair play is written and switched off (fairplay.ON); these tests run it switched on."""

    def setUp(self):
        on = mock.patch.object(fairplay, "ON", True)
        on.start()
        self.addCleanup(on.stop)


class Released(unittest.TestCase):
    """Switched on for the release (the owner, 2026-10-31): the checks, the join code, and the game scripts in every
    build."""

    def test_on_by_default(self):
        self.assertTrue(fairplay.ON)
        self.assertTrue(fairplay.IN_BUILDS)


class Off(unittest.TestCase):
    """Switched off (as it was held from 2026-10-04 to the release): no scripts in builds, nothing in the Launcher,
    Play doesn't ask. These tests switch it off themselves."""

    def setUp(self):
        off = mock.patch.object(fairplay, "ON", False)
        off.start()
        self.addCleanup(off.stop)

    def test_off_builds_nothing(self):
        self.assertEqual(fairplay.FairPlay([fairplay.ModCheck("t", "Test tool", cheat=True)], scripts=True).patches(), [])

    def test_the_launcher_shows_none_of_it(self):
        from ruse_launcher.api import LauncherApi
        with tempfile.TemporaryDirectory() as d:
            api = LauncherApi(game_dir=Path(d), home=Path(d) / "home", instances=Path(d) / "inst", find=lambda: None)
            self.assertEqual(api.fair_play_on(), {"on": False})
            self.assertEqual(api._fair_view({"id": "x", "path": d}, {}),
                             {"scripts": False, "trusted": False, "cheat": False, "offline": None})


class Scripts(SwitchedOn):
    """Our game scripts are compiled from their sources as they are, go after a module's own code unchanged, and
    go in every map's own script folder."""

    def test_compiled_from_the_sources_as_they_are(self):
        for name in (fairplay.LOCK, fairplay.WATCH, fairplay.GUARD):
            self.assertTrue(fairplay.script_is_current(name), f"run tools/compile_gamescript.py25 on {name}.py25")
            code = pyscript.load(fairplay.game_script(name))
            self.assertIsInstance(code, Code)
            self.assertEqual(code.flags & 0x2000, 0x2000)  # true division, like every game script

    def test_appended_after_the_modules_own_code(self):
        mod = module(bytes([LOAD_NAME, 0, 0, POP_TOP, JUMP_ABSOLUTE, 0, 0, LOAD_CONST, 0, 0, RETURN_VALUE]),
                     names=(b"front",))
        for name in (fairplay.LOCK, fairplay.WATCH):
            patch = fairplay.game_script(name)
            new = pyscript.append_script(mod, patch)
            a, p, b = pyscript.load(mod), pyscript.load(patch), pyscript.load(new)
            self.assertEqual(b.code[:7], a.code[:7])  # the module's own code, then the script's
            self.assertEqual(b.consts, a.consts + p.consts)
            self.assertEqual(b.names, a.names + p.names)
            self.assertEqual(len(b.code), 7 + len(p.code))
            for (_at, op, arg), (_at2, op2, arg2) in zip(instructions(b.code[7:]), instructions(p.code)):
                self.assertEqual(op, op2)
                if op == LOAD_CONST:
                    self.assertEqual(arg, arg2 + len(a.consts))
                elif op in pyscript._HAS_NAME:
                    self.assertEqual(arg, arg2 + len(a.names))
                elif op in pyscript._HAS_JUMP_TO:
                    self.assertEqual(arg, arg2 + 7)
                else:
                    self.assertEqual(arg, arg2)
        both = pyscript.append_script(pyscript.append_script(mod, fairplay.game_script(fairplay.LOCK)),
                                      fairplay.game_script(fairplay.WATCH))
        self.assertEqual(pyscript.load(both).names[:1], (b"front",))

    def test_refused(self):
        patch = fairplay.game_script(fairplay.LOCK)
        with self.assertRaisesRegex(ScriptError, "return None"):
            pyscript.append_script(module(bytes([LOAD_NAME, 0, 0, RETURN_VALUE]), names=(b"x",)), patch)
        with self.assertRaisesRegex(ScriptError, "jumps to its own end"):
            pyscript.append_script(module(bytes([JUMP_ABSOLUTE, 3, 0, LOAD_CONST, 0, 0, RETURN_VALUE])), patch)
        with self.assertRaisesRegex(ScriptError, "exec"):
            pyscript.append_script(module(bytes([LOAD_CONST, 0, 0, RETURN_VALUE])),
                                   module(bytes([LOAD_CONST, 0, 0, 85, LOAD_CONST, 0, 0, RETURN_VALUE])))

    def test_the_maps_script_folders(self):
        bs = "\\"
        cluster = bs.join(["DataDir:", "Test", "map", "Chess", "scripting"]).encode() + b"\0" + \
            bs.join(["DataDir:", "Test", "map", "Chess", "Dialog"]).encode() + b"\0" + \
            bs.join(["DataDir:", "Test", "map", "Edge", "Scripting_challenge"]).encode() + b"\0" + \
            bs.join(["DataDir:", "Test", "map", "Chess", "scripting", "deeper"]).encode()
        self.assertEqual(fairplay.script_folders([cluster, cluster]), [
            bs.join(["genpython", "1000", "test", "map", "chess", "scripting"]),
            bs.join(["genpython", "1000", "test", "map", "edge", "scripting_challenge"])])

    def test_added_to_every_folder(self):
        class Pack(dict):  # IA_Common.dat as the build has it (rusemod.rmod.Layered): get, replace, add
            def get(self, path):
                return dict.get(self, path)

            def replace(self, path, data):
                assert path in self
                self[path] = data

            def add(self, path, data):
                assert path not in self
                self[path] = data
        own = xyz([b"Descriptor"])
        ia = Pack({"m\\a\\effetmap.xyz": own, "m\\b\\effetmapmultiplayer.xyz": own})
        multiplayer = xyz([b"launch"])
        patches = [fairplay.game_script(fairplay.WATCH)]
        self.assertEqual(fairplay.add_to_maps(ia, ["m\\a", "m\\b", "m\\c"], multiplayer, patches), 3)
        self.assertEqual(sorted(ia), ["m\\a\\effetmap.xyz", "m\\a\\effetmapmultiplayer.xyz", "m\\b\\effetmapmultiplayer.xyz",
                                      "m\\c\\effetmapmultiplayer.xyz"])  # no effetmap made where there was none
        for member, base in (("m\\a\\effetmap.xyz", own), ("m\\a\\effetmapmultiplayer.xyz", multiplayer),
                             ("m\\b\\effetmapmultiplayer.xyz", own), ("m\\c\\effetmapmultiplayer.xyz", multiplayer)):
            game, ours = pyscript.load(pyscript.read_xyz(base).payload), pyscript.load(pyscript.read_xyz(ia[member]).payload)
            self.assertEqual(ours.names[:len(game.names)], game.names, member)  # the folder's own script, then ours
            self.assertIn(b"_fairplay_watch", ours.names, member)

    @unittest.skipUnless((GAME / "Data").is_dir(), "the game isn't on this PC")
    def test_on_the_games_own_files(self):
        """Every scenario's script folder gets the scripts in IA_Common.dat; the 2.4 GB ZZ_Win.dat is only read."""
        from rusemod import Edat, loc
        from rusemod.build import DEFAULT_PACK, find_pack
        from rusemod.rmod import Layered
        with Edat.open(str(find_pack(GAME, DEFAULT_PACK))) as glad, Edat.open(str(find_pack(GAME, loc.PACK))) as zz, \
                Edat.open(str(find_pack(GAME, fairplay.MAP_SCRIPTS))) as base:
            clusters = [bytes(glad.read(e)) for e in glad.entries
                        if e.path.lower().startswith(fairplay.SCENARIOS) and "cluster" in e.path.lower()]
            folders = fairplay.script_folders(clusters)
            self.assertEqual(len(folders), 68)  # 74 of the 85 scenarios name one (the flat test maps don't)
            ia = Layered(base, "IA_Common.dat")
            patches = fairplay.FairPlay([fairplay.ModCheck("t", "Test tool", cheat=True)], scripts=True).patches()
            self.assertEqual(len(patches), 3)  # the lock, the watcher, RUSE Guard's in-game record
            self.assertEqual(fairplay.add_to_maps(ia, folders, fairplay.multiplayer_script(zz), patches), len(folders))
            shipped = {e.path.lower() for e in base.entries}
            self.assertEqual(len(ia.added), len(folders) - len([f for f in folders if
                                                                 f + fairplay.MULTIPLAYER in shipped]))
            for path, data in list(ia.changed.items()) + list(ia.added.items()):
                code = pyscript.load(pyscript.read_xyz(data).payload)
                self.assertIn(b"_fairplay_lock", code.names, path)
                self.assertIn(b"_fairplay_watch", code.names, path)
                self.assertIn(b"_guard_hash", code.names, path)
            new = ia.to_bytes()
            self.assertLess(len(new), 4_000_000)  # the small pack, rewritten: a few MB, not 2.4 GB
            self.assertEqual(len(Edat(new).entries), len(base.entries) + len(ia.added))

    @unittest.skipUnless((GAME / "Data").is_dir(), "the game isn't on this PC")
    def test_after_the_battles_launcher(self):
        """The scripts go after the game's own Battles launcher in ZZ_Win.dat's script pack, the one copy the game
        loads for Battles (the map folders' never ran in a match, 2026-10-30); every other member stays byte for
        byte, and a pack the build changed already keeps its changes."""
        from rusemod import Edat, loc
        from rusemod.build import find_pack
        patches = fairplay.FairPlay([fairplay.ModCheck("t", "Test tool", cheat=True)], scripts=True).patches()
        with Edat.open(str(find_pack(GAME, loc.PACK))) as zz:
            shipped_raw = bytes(zz.read(zz.entry(pyscript.SCRIPT_PACK)))
            path, raw = fairplay.add_to_launcher(zz, patches)
            self.assertEqual(path.lower(), pyscript.SCRIPT_PACK.lower())
            shipped, new = Edat(shipped_raw), Edat(raw)
            self.assertEqual([e.path for e in new.entries], [e.path for e in shipped.entries])
            launcher = [e for e in new.entries if e.path.lower().endswith(fairplay.MULTIPLAYER)]
            self.assertEqual(len(launcher), 1)
            for e in new.entries:
                if e is launcher[0]:
                    code = pyscript.load(pyscript.read_xyz(bytes(new.read(e))).payload)
                    for name in (b"_fairplay_lock", b"_fairplay_watch", b"_guard_hash"):
                        self.assertIn(name, code.names)
                else:
                    self.assertEqual(bytes(new.read(e)), bytes(shipped.read(shipped.entry(e.path))), e.path)
            # on top of a script pack the build changed already: that change stays, the launcher gets the scripts
            other = next(e for e in shipped.entries if not e.path.lower().endswith(fairplay.MULTIPLAYER)
                         and e.path.lower().endswith(".xyz"))
            mark = pyscript.write_xyz(pyscript.Xyz(b"\0" * 16, pyscript.read_xyz(bytes(shipped.read(other))).payload))
            changed_pack = shipped.to_bytes({other.path: mark})
            _p, raw2 = fairplay.add_to_launcher(zz, patches, {path: changed_pack})
            again = Edat(raw2)
            self.assertEqual(bytes(again.read(again.entry(other.path))), mark)
            code2 = pyscript.load(pyscript.read_xyz(bytes(again.read(
                next(e for e in again.entries if e.path.lower().endswith(fairplay.MULTIPLAYER))))).payload)
            self.assertIn(b"_guard_hash", code2.names)


class Mods(SwitchedOn):
    """Which mods make a copy offline."""

    def setUp(self):
        super().setUp()
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)

    def folder(self, name, toml="", rmod=None) -> Path:
        f = self.dir / name
        f.mkdir()
        lines = ["[mod]", f'id = "{name}"', f'name = "{name.title()}"', 'version = "1.2.0"', toml]
        if rmod is not None:
            (f / "m.rmod").write_text(json.dumps(rmod), encoding="utf-8")
            lines += ["[rmod]", 'file = "m.rmod"']
        (f / "mod.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return f

    @staticmethod
    def rmod(names) -> dict:
        data = base64.b64encode(xyz(names)).decode()
        return {"$schema": "ruse-mod/v1", "id": "s", "name": "S", "version": "1.2.0", "file_patches": [
            {"dat": "Data/PC/1/ZZ_Win.dat", "files": [{"container": "genpython/eugenpatchable.ipk",
                                                       "path": "genpython/1000/codeia/python/x/y.xyz", "data": data}]}]}

    def test_a_plain_mod_is_for_multiplayer(self):
        c = fairplay.check_mod(self.folder("maps"))
        self.assertEqual((c.cheat, c.scripts, c.calls, c.offline_reason), (False, [], [], None))
        fair = fairplay.check([self.dir / "maps"])
        self.assertEqual(fair.patches(), [fairplay.game_script(fairplay.WATCH), fairplay.game_script(fairplay.GUARD)])  # in every build (fairplay.IN_BUILDS)
        fair.scripts = False
        self.assertEqual(fair.patches(), [])  # a copy built with them off gets none

    def test_tagged_cheat_by_itself_or_by_the_list(self):
        self.assertTrue(fairplay.check_mod(self.folder("own", 'tags = ["Cheat"]')).cheat)
        listed = self.folder("listed")
        fairplay.save_tags(listed, ["cheat", "cheats"])
        self.assertEqual(fairplay.read_tags(listed), ["cheat", "cheats"])
        fair = fairplay.check([listed])
        self.assertEqual(fair.offline, ["Listed is a cheat or a test tool"])
        fair.scripts = True
        self.assertEqual(fair.patches(), [fairplay.game_script(fairplay.LOCK), fairplay.game_script(fairplay.WATCH), fairplay.game_script(fairplay.GUARD)])
        fair.dev = True  # a valid dev key: the one way past the offline lock
        self.assertEqual(fair.patches(), [fairplay.game_script(fairplay.WATCH), fairplay.game_script(fairplay.GUARD)])

    def test_scripts_that_send_cheat_orders(self):
        cheat = fairplay.check_mod(self.folder("dev", rmod=self.rmod([b"base", b"Send_AddMaterial", b"Hud",
                                                                       b"toggle_show_dev_buttons"])))
        self.assertEqual(cheat.scripts, ["genpython/eugenpatchable.ipk/genpython/1000/codeia/python/x/y.xyz"])
        self.assertEqual(cheat.calls, ["adds money", "opens the game's developer menu"])
        self.assertEqual(cheat.offline_reason, "Dev's scripts adds money and opens the game's developer menu")
        ui = fairplay.check_mod(self.folder("formations", rmod=self.rmod([b"front", b"Send_ChooseBluffCard"])))
        self.assertEqual((bool(ui.scripts), ui.calls, ui.offline_reason), (True, [], None))  # scripts, but no cheat
        fair = fairplay.check([self.dir / "formations"])
        self.assertEqual(fair.script_mods, ["Formations"])
        fair.scripts = True
        self.assertEqual(fair.patches(), [fairplay.game_script(fairplay.WATCH), fairplay.game_script(fairplay.GUARD)])


class Copy(unittest.TestCase):
    """The build's record in the copy, the join code in it, and the copy checked against it."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.game, self.copy = self.dir / "game", self.dir / "copy"
        for root in (self.game, self.copy):
            (root / "Data" / "PC" / "1").mkdir(parents=True)
            (root / "Maps").mkdir()
        (self.game / "Data" / "PC" / "1" / "Units.dat").write_bytes(b"units")
        (self.game / "Data" / "PC" / "1" / "Big.dat").write_bytes(b"big" * 100)
        (self.game / "RUSE.exe").write_bytes(b"MZ")
        shutil.copy2(self.game / "Data" / "PC" / "1" / "Big.dat", self.copy / "Data" / "PC" / "1" / "Big.dat")
        shutil.copy2(self.game / "RUSE.exe", self.copy / "RUSE.exe")
        (self.copy / "Data" / "PC" / "1" / "Units.dat").write_bytes(b"modded units")
        self.fp = hashlib.sha256(b"x").digest()

    def record(self, fair=None):
        return fairplay.write_record(self.copy, "24687178", self.fp, [("tanks", "1.2.0")], fair or fairplay.FairPlay(),
                                     ["Data/PC/1/Units.dat"])

    def test_a_multiplayer_copy_has_its_code(self):
        rec = self.record()
        self.assertEqual(rec["code"], encode_join_code(24687178, self.fp, [("tanks", "1.2.0")]))
        view = fairplay.copy_view(self.copy, self.game, full=True)
        self.assertEqual((view["code"], view["problems"], view["fingerprint"]), (rec["code"], [], rec["fingerprint"]))

    def test_an_offline_copy_has_none(self):
        rec = self.record(fairplay.FairPlay([fairplay.ModCheck("dev", "Dev", cheat=True)]))
        self.assertEqual((rec["code"], rec["why"], rec["offline"]), (None, "offline", ["Dev is a cheat or a test tool"]))

    def test_changes_after_the_build(self):
        self.record()
        units = self.copy / "Data" / "PC" / "1" / "Units.dat"
        stat = units.stat()
        units.write_bytes(b"cheaty units")  # the same size, the same time: only the full check sees it
        os.utime(units, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual(fairplay.check_copy(self.copy, self.game), [])
        self.assertEqual(fairplay.check_copy(self.copy, self.game, full=True), ["Data/PC/1/Units.dat changed after the build"])
        (self.copy / "Data" / "PC" / "1" / "Big.dat").write_bytes(b"BIG" * 100)  # a game file swapped
        (self.copy / "Data" / "PC" / "1" / "ZZ_Cheat.dat").write_bytes(b"more")  # a pack the game would load
        (self.copy / "RUSE.exe").write_bytes(b"MZ patched")
        found = fairplay.check_copy(self.copy, self.game)
        self.assertEqual(found, ["Data/PC/1/Big.dat isn't the game's own file any more",
                                 "Data/PC/1/ZZ_Cheat.dat isn't one of the game's files",
                                 "RUSE.exe isn't the game's own file any more"])
        view = fairplay.copy_view(self.copy, self.game)
        self.assertEqual((view["code"], len(view["problems"])), (None, 3))

    def test_no_record(self):
        self.assertEqual(fairplay.copy_view(self.copy, self.game)["built"], False)
        self.assertIn("no record", fairplay.check_copy(self.copy, self.game)[0])


class Compare(unittest.TestCase):
    fp = hashlib.sha256(b"x").digest()

    def test_same_and_different(self):
        mine = encode_join_code(1, self.fp, [("a", "1.0.0"), ("b", "2.0.0")])
        self.assertEqual(fairplay.compare(mine, mine), {"same": True, "differences": []})
        theirs = encode_join_code(2, hashlib.sha256(b"y").digest(), [("a", "1.1.0"), ("c", "1.0.0")])
        self.assertEqual(fairplay.compare(mine, theirs)["differences"], [
            "Different game versions: yours is build 1, theirs is build 2. The one behind updates the game in Steam.",
            "a: you have 1.0.0, they have 1.1.0.", "They have c 1.0.0; you don't.", "You have b 2.0.0; they don't."])
        same_mods = encode_join_code(1, hashlib.sha256(b"z").digest(), [("a", "1.0.0"), ("b", "2.0.0")])
        self.assertIn("still differ", fairplay.compare(mine, same_mods)["differences"][0])
        with self.assertRaisesRegex(CodeError, "press Play once"):
            fairplay.compare(None, mine)
        with self.assertRaises(CodeError):
            fairplay.compare(mine, "hello")


class Launcher(SwitchedOn):
    """The Launcher's fair play calls: the copy's view, compare, the trust tick before Play."""

    def setUp(self):
        super().setUp()
        from ruse_launcher.api import LauncherApi
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        (self.dir / "game").mkdir()
        self.api = LauncherApi(game_dir=self.dir / "game", home=self.dir / "home", instances=self.dir / "inst",
                               find=lambda: None)

    def test_calls(self):
        from ruse_launcher.api import LauncherError
        self.assertEqual(self.api.fair_play()["built"], False)
        with self.assertRaisesRegex(LauncherError, "press Play once"):
            self.api.compare_code(encode_join_code(1, b"\0" * 32, []))

    def test_play_waits_for_the_trust_tick(self):
        mods = self.dir / "mods"
        mods.mkdir()
        folder = mods / "ui"
        folder.mkdir()
        (folder / "m.rmod").write_text(json.dumps(Mods.rmod([b"front"])), encoding="utf-8")
        (folder / "mod.toml").write_text('[mod]\nid = "ui"\nname = "UI"\nversion = "1.0.0"\n[rmod]\nfile = "m.rmod"\n',
                                         encoding="utf-8")
        chosen = {"mods": ["ui"], "folders": [str(folder)]}
        self.assertEqual(self.api._untrusted(chosen), ["UI"])
        self.api._save_fair("trusted", {"ui": "1.0.0"})
        self.assertEqual(self.api._untrusted(chosen), [])
        self.api._save_fair("trusted", {"ui": "0.9.0"})  # an older version was ticked: asked again
        self.assertEqual(self.api._untrusted(chosen), ["UI"])
        view = self.api._fair_view({"id": "ui", "path": str(folder)}, {"ui": "1.0.0"})
        self.assertEqual(view, {"scripts": True, "trusted": True, "cheat": False, "offline": None})


if __name__ == "__main__":
    unittest.main()
