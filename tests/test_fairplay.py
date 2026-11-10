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


def python25() -> Path | None:
    """The game's own Python (2.5.1), to run our game scripts where the game can't be started: the folder
    RUSE_PYTHON251 names (as the installers' build takes it), else the engine's own slot; None when neither is there."""
    for folder in (os.environ.get("RUSE_PYTHON251"),
                   Path(fairplay.__file__).parent.parent / "ruse_mod_engine" / "python251"):
        if folder and (Path(folder) / "python.exe").is_file():
            return Path(folder) / "python.exe"
    return None


class SameBuild(SwitchedOn):
    """A copy built with cheats or test tools plays multiplayer and co-op with players who have the same build, and
    leaves any other match (GitHub issue 24; the owner, 2026-11-10): the build code in its lock, the numbers it
    announces, and whole matches played by the lock itself under the game's Python."""
    FP = hashlib.sha256(b"x").digest()
    MODS = [("depot", "1.0.0"), ("tanks", "1.2.0")]

    def test_the_build_code(self):
        code = fairplay.build_code("24687178", self.FP, self.MODS)
        self.assertRegex(code, r"^[0-9a-f]{13}$")
        self.assertEqual(code, fairplay.build_code(24687178, self.FP, list(self.MODS)))  # the same build: the same
        others = [fairplay.build_code("24687179", self.FP, self.MODS),                     # another game build
                  fairplay.build_code("24687178", hashlib.sha256(b"y").digest(), self.MODS),  # other gameplay files
                  fairplay.build_code("24687178", self.FP, self.MODS[:1]),                 # a mod fewer
                  fairplay.build_code("24687178", self.FP, [("depot", "1.0.1"), ("tanks", "1.2.0")]),  # a version
                  fairplay.build_code("24687178", self.FP, self.MODS[::-1]),               # another order
                  fairplay.build_code("24687178", None, self.MODS)]                        # no gameplay change
        self.assertEqual(len({code, *others}), 7)
        self.assertNotIn(fairplay.NO_BUILD_CODE, {code, *others})
        with mock.patch.object(fairplay.hashlib, "sha256") as sha:  # a hash starting with thirteen zeros is still
            sha.return_value.hexdigest.return_value = "0" * 64      # a code: "all zeros" stays the lock's "none"
            self.assertEqual(fairplay.build_code("1", self.FP, []), "1" + "0" * 12)

    def test_the_code_goes_into_the_lock(self):
        code = fairplay.build_code("24687178", self.FP, self.MODS)
        plain, made = pyscript.load(fairplay.game_script(fairplay.LOCK)), pyscript.load(fairplay.lock_script(code))
        self.assertEqual(fairplay.lock_code_of(fairplay.game_script(fairplay.LOCK)), fairplay.NO_BUILD_CODE)
        self.assertEqual(fairplay.lock_code_of(fairplay.lock_script(code)), code)
        differ = [k for k, (a, b) in enumerate(zip(plain.consts, made.consts)) if a != b]
        self.assertEqual([(plain.consts[k], made.consts[k]) for k in differ],
                         [(fairplay.NO_BUILD_CODE.encode(), code.encode())])  # that one value, nothing else
        for part in ("argcount", "nlocals", "stacksize", "flags", "code", "names", "varnames", "freevars",
                     "cellvars", "filename", "name", "firstlineno", "lnotab"):
            self.assertEqual(getattr(plain, part), getattr(made, part), part)
        self.assertEqual(fairplay.lock_code_of(fairplay.lock_script()), fairplay.NO_BUILD_CODE)
        self.assertIsNone(fairplay.lock_code_of(fairplay.game_script(fairplay.WATCH)))
        for bad in ("", "xyz", code.upper(), code + "0", code[:-1]):
            with self.assertRaisesRegex(fairplay.FairPlayError, "build code"):
                fairplay.lock_script(bad)
        # and it still goes after a game module's own code, like the script without a code
        mod = module(bytes([LOAD_NAME, 0, 0, POP_TOP, LOAD_CONST, 0, 0, RETURN_VALUE]), names=(b"front",))
        joined = pyscript.load(pyscript.append_script(mod, fairplay.lock_script(code)))
        self.assertIn(code.encode(), joined.consts)
        self.assertIn(b"_fairplay_lock_code", joined.names)

    def test_the_numbers_a_lock_announces(self):
        first, second = fairplay.lock_numbers("473dc7fef1d1a")
        self.assertEqual((first, second), (0x40000000 | 1 << 24 | 0x473dc7, 0x40000000 | 1 << 28 | 0xfef1d1a))
        for code in ("fffffffffffff", "0000000000001", fairplay.build_code("1", self.FP, self.MODS)):
            for number in fairplay.lock_numbers(code):
                # above every production number the game makes itself (it counts from 1), below the game's signed
                # limit (its own lookup of a number reads 32 bits, signed)
                self.assertTrue(fairplay.LOCK_FIRST <= number < 2 ** 31, (code, number))
        self.assertNotEqual(fairplay.lock_numbers("fffffffffffff")[0] >> 28 & 3,
                            fairplay.lock_numbers("fffffffffffff")[1] >> 28 & 3)  # which half each one is
        for bad in (fairplay.NO_BUILD_CODE, "xyz", ""):
            with self.assertRaises(fairplay.FairPlayError):
                fairplay.lock_numbers(bad)

    def test_the_source_says_the_same_numbers(self):
        """The lock's source and rusemod.fairplay agree on the announcement's start, version and the code's name."""
        src = (fairplay.SCRIPTS / "fairplay_lock.py25").read_text(encoding="utf-8")
        self.assertIn(f"_fairplay_lock_first = 0x{fairplay.LOCK_FIRST:08X}", src)
        self.assertIn(f"_fairplay_lock_version = {fairplay.LOCK_VERSION} ", src)
        self.assertIn(f"_fairplay_lock_code = '{fairplay.NO_BUILD_CODE}'", src)
        top = pyscript.load(fairplay.game_script(fairplay.LOCK))
        self.assertEqual(top.consts.count(fairplay.NO_BUILD_CODE.encode()), 1)  # the one the build replaces

    @unittest.skipUnless(python25(), "no Python 2.5.1 on this PC (set RUSE_PYTHON251 to its folder)")
    def test_matches_played_under_the_games_python(self):
        """tests/gamescripts_sim.py25: whole matches between stand-in PCs, run by the game's own Python version with
        the scripts exactly as a build puts them in a copy. Every match goes as expected: same build = plays on;
        anyone missing or different = the cheat copy leaves; a game without our scripts is never touched."""
        import subprocess
        a = fairplay.build_code("24687178", self.FP, self.MODS)
        b = fairplay.build_code("24687178", self.FP, self.MODS + [("money", "0.3.0")])
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for name, data in (("lock_a", fairplay.lock_script(a)), ("lock_a2", fairplay.lock_script(a)),
                               ("lock_b", fairplay.lock_script(b)), ("lock_none", fairplay.lock_script()),
                               ("watch", fairplay.game_script(fairplay.WATCH)),
                               ("record", fairplay.game_script(fairplay.GUARD))):
                (out / f"{name}.bin").write_bytes(data)
            (out / "numbers.txt").write_text("".join(f"{name} {x} {y}\n" for name, (x, y) in
                                                     (("a", fairplay.lock_numbers(a)),
                                                      ("b", fairplay.lock_numbers(b)))), encoding="ascii")
            released = Path(__file__).with_name("data") / "fairplay_lock_before_same_build.bin"
            if released.is_file():  # the lock as released up to 0.4.8.18, before the same-build check: it meets
                # the new one (a player who hasn't updated yet)
                (out / "lock_old.bin").write_bytes(released.read_bytes()[16:])
            if (GAME / "Data").is_dir():  # with the game on this PC: its own Battles launcher with a copy's scripts
                from rusemod import Edat, loc  # after it, the very module a build writes into a copy
                from rusemod.build import find_pack
                fair = fairplay.FairPlay([fairplay.ModCheck("t", "Test tool", cheat=True)], scripts=True)
                with Edat.open(str(find_pack(GAME, loc.PACK))) as zz:
                    for name, code in (("joined_a", a), ("joined_a2", a), ("joined_b", b)):
                        _path, raw = fairplay.add_to_launcher(zz, fair.patches(code))
                        pack = Edat(raw)
                        member = next(e for e in pack.entries if e.path.lower().endswith(fairplay.MULTIPLAYER))
                        (out / f"{name}.bin").write_bytes(pyscript.read_xyz(bytes(pack.read(member))).payload)
            run = subprocess.run([str(python25()), str(Path(__file__).with_name("gamescripts_sim.py25")), str(out)],
                                 capture_output=True, text=True, timeout=300)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertRegex(run.stdout, r"(\d+) of \1 matches as expected")
        self.assertNotIn("FAILED", run.stdout)
        self.assertGreaterEqual(run.stdout.count("\nok "), 16)


class Mods(SwitchedOn):
    """Which mods make a cheat copy (`offline` in the code)."""

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
        code = fairplay.build_code("24687178", hashlib.sha256(b"x").digest(), [("listed", "1.2.0")])
        self.assertEqual(fair.patches(code), [fairplay.lock_script(code), fairplay.game_script(fairplay.WATCH),
                                              fairplay.game_script(fairplay.GUARD)])
        self.assertEqual(fairplay.lock_code_of(fair.patches(code)[0]), code)  # the copy's build code is in its lock
        self.assertEqual(fairplay.lock_code_of(fair.patches()[0]), fairplay.NO_BUILD_CODE)  # none given: none in it
        fair.dev = True  # a valid dev key: the one way past the lock
        self.assertEqual(fair.patches(code), [fairplay.game_script(fairplay.WATCH), fairplay.game_script(fairplay.GUARD)])

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

    def record(self, fair=None, lock_code=None):
        return fairplay.write_record(self.copy, "24687178", self.fp, [("tanks", "1.2.0")], fair or fairplay.FairPlay(),
                                     ["Data/PC/1/Units.dat"], lock_code)

    def test_a_multiplayer_copy_has_its_code(self):
        rec = self.record()
        self.assertEqual(rec["code"], encode_join_code(24687178, self.fp, [("tanks", "1.2.0")]))
        self.assertEqual((rec["why"], rec["lock"]), (None, None))
        view = fairplay.copy_view(self.copy, self.game, full=True)
        self.assertEqual((view["code"], view["problems"], view["fingerprint"]), (rec["code"], [], rec["fingerprint"]))

    def test_a_cheat_copy_has_its_code_too(self):
        """A copy built with cheats or test tools plays with players who have the same build (GitHub issue 24), so
        it has its join code for them to compare, and its record says which build code its lock carries."""
        lock = fairplay.build_code("24687178", self.fp, [("tanks", "1.2.0")])
        rec = self.record(fairplay.FairPlay([fairplay.ModCheck("dev", "Dev", cheat=True)]), lock)
        self.assertEqual((rec["code"], rec["why"], rec["offline"], rec["lock"]),
                         (encode_join_code(24687178, self.fp, [("tanks", "1.2.0")]), "offline",
                          ["Dev is a cheat or a test tool"], lock))
        view = fairplay.copy_view(self.copy, self.game, full=True)
        self.assertEqual((view["code"], view["why"], view["offline"]), (rec["code"], "offline", rec["offline"]))
        # two players with that set compare their codes as any others do
        self.assertTrue(fairplay.compare(view["code"], rec["code"])["same"])
        # a copy whose mods change nothing in how the game plays has no code, cheat copy or not
        none = fairplay.write_record(self.copy, "24687178", None, [("tanks", "1.2.0")],
                                     fairplay.FairPlay([fairplay.ModCheck("dev", "Dev", cheat=True)]), [])
        self.assertEqual((none["code"], none["why"]), (None, "offline"))
        plain = fairplay.write_record(self.copy, "24687178", None, [("tanks", "1.2.0")], fairplay.FairPlay(), [])
        self.assertEqual((plain["code"], plain["why"]), (None, "no gameplay change"))

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
