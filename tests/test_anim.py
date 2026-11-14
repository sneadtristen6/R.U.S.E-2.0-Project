"""rusemod.baf (the game's animation clips read, written, sampled and changed) and rusemod.anim (a mod's animations,
put in by the build into every pack that holds the clip; one unit's own animations, files of their own that only that
unit's listings name)."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import contextlib
import io
import math
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rusemod import anim, baf
from rusemod.edat import Edat

B = "\\"
RUN = B.join(["genanim_15", "ww2", "res3d", "units", "common", "fusilier_courselod0.baf"])
FLEE = B.join(["genanim_15", "ww2", "res3d", "units", "common", "fusilier_deroutelod0.baf"])
STAND = B.join(["genanim_15", "ww2", "res3d", "units", "common", "fusilier_standlod0.baf"])
HORSE = B.join(["genanim_15", "ww2", "res3d", "decors", "animaux", "horse_runlod0.baf"])


def skeleton_part(names, parents):
    """A skeleton part laid out as the game's: header, name lengths, 3 x bones matrices, parents, indices, names."""
    nb = len(names)
    head = 36 + 2 * nb
    m_off = head + (-head % 4)
    p_off = m_off + 144 * nb
    i_off = p_off + 4 * nb
    n_off = i_off + 4 * nb
    ident = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    out = bytearray(struct.pack("<II7I", 1, nb, m_off, p_off, i_off, n_off, 144 * nb, 4 * nb, 4 * nb))
    out += struct.pack(f"<{nb}H", *(len(n) for n in names))
    out += bytes(m_off - len(out))
    for _ in range(3 * nb):
        out += struct.pack("<12f", *ident)
    out += struct.pack(f"<{nb}i", *parents) + struct.pack(f"<{nb}I", *range(nb))
    raw = "".join(names).encode("latin-1")
    return bytes(out + raw + bytes(-len(raw) % 4))


def clip(names=("bip01 pelvis", "bip01 head"), frames=31, seconds=1.0, lift=1.0):
    ident = baf.pack_quat(0.0, 0.0, 0.0, 1.0)
    turned = baf.pack_quat(*baf.axis_angle("z", 40.0))
    tracks = []
    for u in range(len(names)):
        T = [(0, 0.0, 0.0, 10.0 * u), (baf.time_of(0.5), 0.0, lift, 10.0 * u), (baf.LAST_TIME, 0.0, 0.0, 10.0 * u)]
        tracks.append(baf.Track(T, [(0, 1.0, 1.0, 1.0)], [(0,) + ident, (baf.LAST_TIME,) + turned]))
    return baf.Clip(seconds, frames, tracks, skeleton_part(list(names), [-1] + [0] * (len(names) - 1)))


class Clips(unittest.TestCase):
    def test_written_and_read_back(self):
        c = clip()
        raw = baf.build(c)
        self.assertEqual(baf.build(baf.parse(raw)), raw)            # byte for byte
        s = baf.skeleton(baf.parse(raw).skeleton)
        self.assertEqual((s["bones"], s["names"], s["parents"]), (2, ["bip01 pelvis", "bip01 head"], [-1, 0]))
        self.assertEqual(baf.track_of(c, "BIP01 HEAD"), 1)

    def test_turns_packed_as_the_game_has_them(self):
        self.assertEqual(struct.pack("<4H", *baf.pack_quat(0.0, 0.0, 0.0, 1.0)),
                         bytes.fromhex("0080000420000000"))                # the game's no-turn, as its files hold it
        for q in ((0.1, -0.2, 0.3, 0.927), (0.0, 0.0, 0.0, -1.0), baf.axis_angle("y", 130)):
            back = baf.unpack_quat(baf.pack_quat(*q))
            n = math.sqrt(sum(v * v for v in q))
            for a, b in zip(back, (v / n for v in q)):
                self.assertAlmostEqual(a, b, places=5)

    def test_the_rules_kept(self):
        c = clip()
        c.tracks[0].T[-1] = (baf.LAST_TIME - 5, 0.0, 0.0, 0.0)      # more than two keys must end at the clip's end
        with self.assertRaises(baf.ClipError):
            baf.build(c)
        with self.assertRaises(baf.ClipError):
            baf.build(baf.Clip(1.0, 2, [], b""))                       # no bones
        with self.assertRaises(baf.ClipError):
            baf.parse(b"\x0e" + bytes(40))                              # another version

    def test_sampled_as_the_game_does(self):
        c = clip()
        move, turn, size = baf.sample(c.tracks[1], 0.5)
        self.assertEqual((move, size), ((0.0, 1.0, 10.0), (1.0, 1.0, 1.0)))
        half = baf.axis_angle("z", 20.0)                                  # two turn keys: straight across the clip
        for a, b in zip(turn, half):
            self.assertAlmostEqual(a, b, places=4)

    def test_changes(self):
        c = clip()
        self.assertAlmostEqual(baf.with_speed(c, 200).duration, 0.5)
        self.assertAlmostEqual(baf.with_speed(c, 50).duration, 2.0)
        big = baf.with_bone(c, "bip01 head", size=2.5)
        self.assertEqual(big.tracks[1].S, [(0, 2.5, 2.5, 2.5)])
        self.assertEqual(big.tracks[0].S, c.tracks[0].S)                 # the other bones as they were
        turned = baf.with_bone(c, "bip01 head", turn=("x", 90))
        q = baf.unpack_quat(turned.tracks[1].R[0][1:5])
        for a, b in zip(q, baf.axis_angle("x", 90)):
            self.assertAlmostEqual(a, b, places=5)
        self.assertTrue(baf.same_skeleton(c, clip(lift=3.0)))
        self.assertFalse(baf.same_skeleton(c, clip(names=("bip01 pelvis", "horse head"))))


class ModFiles(unittest.TestCase):
    def test_read(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / anim.CLIPS
            f.parent.mkdir(parents=True)
            f.write_text(f'[clip."{anim.clip_key(RUN)}"]\nspeed = 150\nfrom = "{anim.clip_key(FLEE)}"\n'
                         f'[clip."{anim.clip_key(RUN)}".bone."bip01 head"]\nsize = 2.5\nturn = ["z", 30]\n',
                         encoding="utf-8")
            rep = Path(d) / anim.REPLACE / anim.clip_key(HORSE)
            rep.parent.mkdir(parents=True)
            rep.write_bytes(baf.build(clip()))
            got = anim.mod_clips(Path(d))
            self.assertEqual(got[RUN], {"speed": 150.0, "from": FLEE, "file": None,
                                        "bones": {"bip01 head": {"size": 2.5, "turn": ("z", 30.0)}}})
            self.assertEqual(got[HORSE]["file"], rep)

    def test_refused(self):
        for text in ('[clip."a.baf"]\nspeed = 0\n', '[clip."a.txt"]\nspeed = 50\n',
                     '[clip."a.baf".bone.x]\nsize = 50\n', '[clip."a.baf".bone.x]\nturn = ["w", 3]\n', 'clip = 3\n'):
            with tempfile.TemporaryDirectory() as d, self.subTest(text=text):
                f = Path(d) / anim.CLIPS
                f.parent.mkdir(parents=True)
                f.write_text(text, encoding="utf-8")
                with self.assertRaises(anim.AnimError):
                    anim.mod_clips(Path(d))


class InTheBuild(unittest.TestCase):
    def game(self, d):
        """A made-up game: the run in two genanim_15 packs, the flee in one, the horse loose in ZZ_Win.dat."""
        from fixtures import make_edat
        from test_build import PACK
        run, flee, horse = baf.build(clip()), baf.build(clip(lift=4.0)), baf.build(clip(names=("horse root",)))
        common = make_edat([("dir", "genanim_15\\ww2\\res3d\\units\\common\\", [
            ("file", "fusilier_courselod0.baf", run), ("file", "fusilier_deroutelod0.baf", flee)])])
        us = make_edat([("dir", "genanim_15\\ww2\\res3d\\units\\common\\", [("file", "fusilier_courselod0.baf", run)])])
        zz = make_edat([("dir", "genanim_15\\", [
            ("dir", "pack\\", [("file", "gfxdescriptor_common.apk", common), ("file", "gfxdescriptor_us.apk", us)]),
            ("dir", "ww2\\res3d\\decors\\animaux\\", [("file", "horse_runlod0.baf", horse)])])])
        game = Path(d, "R.U.S.E")
        data = game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        (data / "ZZ_GladPatchableWin.dat").write_bytes(PACK)
        (data / "ZZ_Win.dat").write_bytes(zz)
        return game, zz, run, flee, horse

    def build(self, d, game, mod):
        from rusemod.cli import main
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(["--game", str(game), "build", str(mod), "--instance", str(Path(d, "copy"))])
        return code, out.getvalue()

    def test_ruse_build_puts_the_clips_in_every_pack(self):
        from rusemod.edat import Edat
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, zz, run, flee, horse = self.game(d)
            mod = Path(d, "moves")
            (mod / "files" / "anim").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "moves"\nversion = "1.0.0"\n', encoding="utf-8")
            (mod / anim.CLIPS).write_text(
                f'[clip."{anim.clip_key(RUN)}"]\nspeed = 200\nfrom = "{anim.clip_key(FLEE)}"\n'
                f'[clip."{anim.clip_key(RUN)}".bone."bip01 head"]\nsize = 2.5\n'
                f'[clip."{anim.clip_key(HORSE)}"]\nspeed = 50\n', encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            self.assertIn("animations: 2", said)
            copy = Edat(Path(d, "copy", "Data", "PC", "190852", "ZZ_Win.dat").read_bytes())
            want = baf.build(baf.with_speed(baf.with_bone(baf.parse(flee), "bip01 head", 2.5), 200))
            for name in ("gfxdescriptor_common.apk", "gfxdescriptor_us.apk"):     # in both packs that hold it
                pk = Edat(bytes(copy.read(copy.find(name))))
                self.assertEqual(bytes(pk.read(pk.find("fusilier_courselod0.baf"))), want)
            pk = Edat(bytes(copy.read(copy.find("gfxdescriptor_common.apk"))))
            self.assertEqual(bytes(pk.read(pk.find("fusilier_deroutelod0.baf"))), flee)   # the source untouched
            got = baf.parse(bytes(copy.read(copy.find("horse_runlod0.baf"))))              # loose: in its place
            self.assertAlmostEqual(got.duration, 2.0)
            self.assertEqual((game / "Data" / "PC" / "190852" / "ZZ_Win.dat").read_bytes(), zz)

    def test_a_clip_of_other_bones_refused(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game, *_ = self.game(d)
            mod = Path(d, "moves")
            (mod / "files" / "anim").mkdir(parents=True)
            (mod / "mod.toml").write_text('[mod]\nid = "moves"\nversion = "1.0.0"\n', encoding="utf-8")
            (mod / anim.CLIPS).write_text(f'[clip."{anim.clip_key(RUN)}"]\nfrom = "{anim.clip_key(HORSE)}"\n',
                                          encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertNotEqual(code, 0)
            self.assertIn("only a clip of the same bones can stand in", said)


# --- one unit's own animations (files/anim/units.toml, files/anim/own/<unit>/) ---
E = "$/GFX/Everything/"
FILE_OF = {STAND: "WW2\\Res3D\\Units\\Common\\Fusilier_standlod0.Ase2NdfBin",
           RUN: "WW2\\Res3D\\Units\\Common\\Fusilier_courselod0.Ase2NdfBin"}
UNIT_DATA = "genglad\\patchable\\gfx\\everything.cpp.gladndfbin"


def squads_pack() -> bytes:
    """Made-up unit data as the game's infantry has it: Descriptor_Unit_Squad (a rifleman and a bazooka man) and
    Descriptor_Unit_Other (a rifleman), each figure its own part listing its clips by action (ResourceAnimation:
    t_stand, b_stand, t_course), the listings themselves objects every figure shares, as the game's 80-user ones."""
    from fixtures import make_edat, make_ndf, val

    def text(i):
        return val(0x07, struct.pack("<I", i))

    def ref(index, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, index, cls))

    def listing(*pairs):
        return val(0x12, struct.pack("<I", len(pairs)) + b"".join(text(k) + ref(o, 2) for k, o in pairs))
    strings = ["t_stand", "b_stand", "t_course", FILE_OF[STAND], FILE_OF[RUN],
               "WW2\\Res3D\\Units\\US\\Infanterie\\US_Soldier_modellod0.Ase2NdfBin"]
    ndf = make_ndf(objects=[
        (0, [(0, val(0x03, struct.pack("<I", 2))), (8, val(0x02, struct.pack("<i", 1))), (1, ref(1, 1)),
             (2, ref(2, 1))]),
        (1, [(4, ref(3, 3)), (3, listing((0, 4), (1, 4), (2, 5)))]),
        (1, [(4, ref(3, 3)), (3, listing((0, 4), (2, 5)))]),
        (3, [(7, val(0x1C, struct.pack("<I", 5)))]),
        (2, [(5, val(0x1C, struct.pack("<I", 3))), (6, val(0x00, b"\x01"))]),
        (2, [(5, val(0x1C, struct.pack("<I", 4)))]),
        (0, [(0, val(0x03, struct.pack("<I", 4))), (8, val(0x02, struct.pack("<i", 1))), (1, ref(7, 1))]),
        (1, [(4, ref(3, 3)), (3, listing((0, 4), (2, 5)))])],
        classes=["TInfanterieDescriptor", "TGfxDescriptorBiped", "TGfxDescriptorAnimation",
                 "TResourceMultiMaterialMesh"],
        props=[("DescriptorId", 0), ("GfxDescriptorFusilier", 0), ("GfxDescriptorBazooka", 0),
               ("ResourceAnimation", 1), ("MeshDescriptor", 1), ("FileName", 2), ("PlayInLoop", 2), ("FileName", 3),
               ("Nationalite", 0)],
        strings=strings, exports={0: "GFX/Everything/Descriptor_Unit_Squad", 6: "GFX/Everything/Descriptor_Unit_Other"},
        compress=True)
    return make_edat([("dir", "genglad\\patchable\\gfx\\", [("file", "everything.cpp.gladndfbin", ndf)])])


class OneUnitsOwn(unittest.TestCase):
    """A clip changed for one unit only: a file of its own in ZZ_Win.dat, and only that unit's listings naming it."""

    def game(self, d):
        """The made-up game: squads_pack's units; the stand in two genanim_15 packs, the run and the flee in one, the
        horse loose in ZZ_Win.dat."""
        from fixtures import make_edat
        self.stand, self.run, self.flee = baf.build(clip()), baf.build(clip(lift=2.0)), baf.build(clip(lift=4.0))
        self.horse = baf.build(clip(names=("horse root",)))
        common = make_edat([("dir", "genanim_15\\ww2\\res3d\\units\\common\\", [
            ("file", "fusilier_courselod0.baf", self.run), ("file", "fusilier_deroutelod0.baf", self.flee),
            ("file", "fusilier_standlod0.baf", self.stand)])])
        us = make_edat([("dir", "genanim_15\\ww2\\res3d\\units\\common\\", [
            ("file", "fusilier_standlod0.baf", self.stand)])])
        zz = make_edat([("dir", "genanim_15\\", [
            ("dir", "pack\\", [("file", "gfxdescriptor_common.apk", common), ("file", "gfxdescriptor_us.apk", us)]),
            ("dir", "ww2\\res3d\\decors\\animaux\\", [("file", "horse_runlod0.baf", self.horse)])])])
        game = Path(d, "R.U.S.E")
        data = game / "Data" / "PC" / "190852"
        data.mkdir(parents=True)
        self.units = squads_pack()
        (data / "ZZ_GladPatchableWin.dat").write_bytes(self.units)
        (data / "ZZ_Win.dat").write_bytes(zz)
        self.zz = zz
        return game

    def mod(self, d, name="moves", units=None, rndf=None, clips=None, files=None):
        mod = Path(d, name)
        (mod / "src").mkdir(parents=True)
        (mod / "mod.toml").write_text(f'[mod]\nid = "{name}"\nversion = "1.0.0"\n', encoding="utf-8")
        if rndf:
            (mod / "src" / "units.rndf").write_text(rndf, encoding="utf-8")
        if units is not None:
            (mod / anim.UNITS).parent.mkdir(parents=True, exist_ok=True)
            (mod / anim.UNITS).write_text(units, encoding="utf-8")
        if clips is not None:
            (mod / anim.CLIPS).parent.mkdir(parents=True, exist_ok=True)
            (mod / anim.CLIPS).write_text(clips, encoding="utf-8")
        for rel, data in (files or {}).items():
            (mod / rel).parent.mkdir(parents=True, exist_ok=True)
            (mod / rel).write_bytes(data)
        return mod

    def build(self, d, game, *mods):
        from rusemod.cli import main
        out = io.StringIO()
        args = ["--game", str(game), "build", *[str(m) for m in mods], "--instance", str(Path(d, "copy"))]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = main(args)
        return code, out.getvalue()

    def copy(self, d):
        """(the copy's ZZ_Win.dat, the copy's unit data as the build reads it: {name: object})."""
        from rusemod.build import load_pack
        data = Path(d, "copy", "Data", "PC", "190852")
        return Edat((data / "ZZ_Win.dat").read_bytes()), load_pack(Edat((data / "ZZ_GladPatchableWin.dat")
                                                                        .read_bytes())).base.objects

    @staticmethod
    def listings(objects, unit, figure="GfxDescriptorFusilier"):
        """{action: the FileName its listing names} of a figure of a unit in the built data."""
        from rusemod.patch import Inline
        fig = objects[E + unit].props[figure]
        fig = fig.obj if isinstance(fig, Inline) else objects[fig.target]
        out = {}
        for k, v in fig.props["ResourceAnimation"].pairs:
            a = v.obj if isinstance(v, Inline) else objects[v.target]
            out[k.value] = a.props["FileName"].value
        return out

    def game_clips_kept(self, copy):
        """Every file of the game's ZZ_Win.dat (its clips loose and in their packs) in the copy's, byte for byte."""
        game = Edat(self.zz)
        for e in game.entries:
            got = copy.entry(e.path)
            self.assertIsNotNone(got, e.path)
            self.assertEqual(bytes(copy.read(got)), bytes(game.read(e)), e.path)

    def test_no_unit_s_own_builds_as_before(self):
        # a mod with a new unit and a change for every unit, no units.toml: no file of a unit's own, every listing the
        # game's; and an empty units.toml builds byte for byte the same
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            rndf = f"export Descriptor_Unit_Horse_Squad is clone {E}Descriptor_Unit_Squad ( )\n"
            clips = f'[clip."{anim.clip_key(RUN)}"]\nspeed = 200\n'
            mod = self.mod(d, rndf=rndf, clips=clips)
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            self.assertNotIn("units' own animations", said)
            data = Path(d, "copy", "Data", "PC", "190852")
            first = {n: (data / n).read_bytes() for n in ("ZZ_Win.dat", "ZZ_GladPatchableWin.dat")}
            zz, objects = self.copy(d)
            self.assertEqual(sorted(e.path for e in zz.entries), sorted(e.path for e in Edat(self.zz).entries))
            for unit in ("Descriptor_Unit_Horse_Squad", "Descriptor_Unit_Squad", "Descriptor_Unit_Other"):
                self.assertEqual(self.listings(objects, unit)["t_stand"], FILE_OF[STAND])
            (mod / anim.UNITS).write_text("# nothing yet\n", encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            self.assertEqual({n: (data / n).read_bytes() for n in first}, first)

    def test_only_this_unit(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            rndf = f"export Descriptor_Unit_Horse_Squad is clone {E}Descriptor_Unit_Squad ( )\n"
            units = (f'[unit.Descriptor_Unit_Horse_Squad.clip."{anim.clip_key(STAND)}"]\nspeed = 200\n'
                     f'[unit.Descriptor_Unit_Horse_Squad.clip."{anim.clip_key(STAND)}".bone."bip01 head"]\nsize = 2\n')
            mod = self.mod(d, rndf=rndf, units=units)
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            own = anim.own_member("own_horse_squad_fusilier_standlod0")
            self.assertEqual(own, "genanim_15\\ww2\\res3d\\units\\common\\own_horse_squad_fusilier_standlod0.baf")
            self.assertIn("Descriptor_Unit_Horse_Squad plays 1 clip(s) of its own", said)
            zz, objects = self.copy(d)
            had = {e.path.lower() for e in Edat(self.zz).entries}
            self.assertEqual([e.path.lower() for e in zz.entries if e.path.lower() not in had], [own])  # one new file
            want = baf.build(baf.with_speed(baf.with_bone(baf.parse(self.stand), "bip01 head", 2.0), 200))
            self.assertEqual(bytes(zz.read(zz.entry(own))), want)
            self.game_clips_kept(zz)                                                 # the game's clips, all of them
            mine = anim.own_data_name("own_horse_squad_fusilier_standlod0")
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Horse_Squad"),
                             {"t_stand": mine, "b_stand": mine, "t_course": FILE_OF[RUN]})
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Horse_Squad", "GfxDescriptorBazooka"),
                             {"t_stand": mine, "t_course": FILE_OF[RUN]})
            for unit in ("Descriptor_Unit_Squad", "Descriptor_Unit_Other"):        # the others: the game's
                self.assertEqual(self.listings(objects, unit)["t_stand"], FILE_OF[STAND])
            from rusemod.build import load_pack
            before = load_pack(Edat(self.units)).base.objects
            for name in (E + "Descriptor_Unit_Squad", E + "Descriptor_Unit_Other"):
                self.assertEqual(objects[name], before[name])                       # every value as the game's
            shared = [n for n, o in before.items() if o.cls == "TGfxDescriptorAnimation"]
            self.assertEqual([objects[n] for n in shared], [before[n] for n in shared])

    def test_two_units_changing_one_clip_get_a_file_each(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            rndf = (f"export Descriptor_Unit_Horse_Squad is clone {E}Descriptor_Unit_Squad ( )\n"
                    f"export Descriptor_Unit_Camel_Squad is clone {E}Descriptor_Unit_Squad ( )\n")
            units = "".join(f'[unit.Descriptor_Unit_{u}_Squad.clip."{anim.clip_key(STAND)}"]\nspeed = {s}\n'
                            for u, s in (("Horse", 200), ("Camel", 50)))
            code, said = self.build(d, game, self.mod(d, rndf=rndf, units=units))
            self.assertEqual(code, 0, said)
            zz, objects = self.copy(d)
            for u, s in (("horse", 200), ("camel", 50)):
                stem = f"own_{u}_squad_fusilier_standlod0"
                self.assertAlmostEqual(baf.parse(bytes(zz.read(zz.entry(anim.own_member(stem))))).duration, 100 / s)
                self.assertEqual(self.listings(objects, f"Descriptor_Unit_{u.title()}_Squad")["t_stand"],
                                 anim.own_data_name(stem))
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Squad")["t_stand"], FILE_OF[STAND])

    def test_one_of_the_game_s_units_and_a_copy_of_it(self):
        # "Only this unit" on the game's own squad: its copy (made before, sharing its listings) keeps the game's
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            rndf = f"export Descriptor_Unit_Horse_Squad is clone {E}Descriptor_Unit_Squad ( )\n"
            units = f'[unit.Descriptor_Unit_Squad.clip."{anim.clip_key(STAND)}"]\nfrom = "{anim.clip_key(FLEE)}"\n'
            code, said = self.build(d, game, self.mod(d, rndf=rndf, units=units))
            self.assertEqual(code, 0, said)
            zz, objects = self.copy(d)
            stem = "own_squad_fusilier_standlod0"
            self.assertEqual(bytes(zz.read(zz.entry(anim.own_member(stem)))), self.flee)
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Squad", "GfxDescriptorBazooka")["t_stand"],
                             anim.own_data_name(stem))
            for unit in ("Descriptor_Unit_Horse_Squad", "Descriptor_Unit_Other"):
                self.assertEqual(self.listings(objects, unit)["t_stand"], FILE_OF[STAND])
            self.game_clips_kept(zz)

    def test_an_action_s_own_clip_from_elsewhere(self):
        # add_unit_clip (Import model's way in): one figure's action, and every figure's
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            rndf = f"export Descriptor_Unit_Horse_Squad is clone {E}Descriptor_Unit_Squad ( )\n"
            mod = self.mod(d, rndf=rndf)
            mine = baf.build(clip(names=("bip01 pelvis", "bip01 head", "bip01 tail"), lift=5.0))
            other = baf.build(clip(names=("bip01 pelvis", "bip01 head", "bip01 tail"), lift=7.0))
            f = anim.add_unit_clip(mod, "Descriptor_Unit_Horse_Squad", "t_stand", mine, name="rider stand")
            self.assertEqual(f, mod / anim.OWN / "Descriptor_Unit_Horse_Squad" / "rider_stand.baf")
            anim.add_unit_clip(mod, "Descriptor_Unit_Horse_Squad", "t_stand", other, name="rider_bazooka_stand",
                               figure="GfxDescriptorBazooka")
            anim.add_unit_clip(mod, "Descriptor_Unit_Horse_Squad", "b_stand", mine, name="rider stand")  # (one file)
            got = anim.mod_unit_clips(mod)["Descriptor_Unit_Horse_Squad"]["actions"]
            self.assertEqual(sorted(got, key=str), [("b_stand", None), ("t_stand", "GfxDescriptorBazooka"),
                                                    ("t_stand", None)])
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            zz, objects = self.copy(d)
            rider, bazooka = "own_horse_squad_rider_standlod0", "own_horse_squad_rider_bazooka_standlod0"
            self.assertEqual(bytes(zz.read(zz.entry(anim.own_member(rider)))), mine)
            self.assertEqual(bytes(zz.read(zz.entry(anim.own_member(bazooka)))), other)
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Horse_Squad"),
                             {"t_stand": anim.own_data_name(rider), "b_stand": anim.own_data_name(rider),
                              "t_course": FILE_OF[RUN]})
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Horse_Squad", "GfxDescriptorBazooka"),
                             {"t_stand": anim.own_data_name(bazooka), "t_course": FILE_OF[RUN]})
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Squad")["t_stand"], FILE_OF[STAND])
            # taken out again: the file goes once nothing names it
            self.assertTrue(anim.remove_unit_clip(mod, "Descriptor_Unit_Horse_Squad", "t_stand"))
            self.assertTrue((mod / anim.OWN / "Descriptor_Unit_Horse_Squad" / "rider_stand.baf").is_file())  # b_stand
            self.assertTrue(anim.remove_unit_clip(mod, "Descriptor_Unit_Horse_Squad", "b_stand"))
            self.assertFalse((mod / anim.OWN / "Descriptor_Unit_Horse_Squad" / "rider_stand.baf").exists())
            self.assertFalse(anim.remove_unit_clip(mod, "Descriptor_Unit_Horse_Squad", "b_stand"))

    def test_a_mod_taken_out_leaves_nothing(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            rndf = f"export Descriptor_Unit_Horse_Squad is clone {E}Descriptor_Unit_Squad ( )\n"
            units = f'[unit.Descriptor_Unit_Squad.clip."{anim.clip_key(STAND)}"]\nspeed = 50\n'
            code, said = self.build(d, game, self.mod(d, units=units))
            self.assertEqual(code, 0, said)
            other = self.mod(d, name="other", rndf=rndf)
            code, said = self.build(d, game, other)                                   # the next Play, without it
            self.assertEqual(code, 0, said)
            zz, objects = self.copy(d)
            self.assertFalse([e.path for e in zz.entries if "own_" in e.path.lower()])
            self.game_clips_kept(zz)
            self.assertEqual(self.listings(objects, "Descriptor_Unit_Squad")["t_stand"], FILE_OF[STAND])

    def test_what_the_build_says(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"RUSE_PLATFORM_HOME": str(Path(d, "home"))}):
            game = self.game(d)
            mine = baf.build(clip())
            units = (f'[unit.Descriptor_Unit_Squad.clip."{anim.clip_key(HORSE)}"]\nspeed = 50\n'   # it doesn't play it
                     '[unit.Descriptor_Unit_Squad.action]\nt_wave = "wave.baf"\n'                  # no such action
                     '[unit.Descriptor_Unit_Squad.figure."GfxDescriptorPilot".action]\nt_stand = "wave.baf"\n')
            mod = self.mod(d, units=units, files={f"{anim.OWN}/Descriptor_Unit_Squad/wave.baf": mine})
            code, said = self.build(d, game, mod)
            self.assertEqual(code, 0, said)
            self.assertIn(f"Descriptor_Unit_Squad plays no {anim.clip_key(HORSE)}", said)
            self.assertIn("Descriptor_Unit_Squad lists no action t_wave, so nothing plays", said)
            self.assertIn("lists no action t_stand (it has no figure GfxDescriptorPilot)", said)
            self.assertIn("The mods change nothing in these packs.", said)   # nothing names them: no file of its own
            self.assertFalse(Path(d, "copy").exists())
            # a unit nothing makes
            (mod / anim.UNITS).write_text(f'[unit.Descriptor_Unit_Nobody.clip."{anim.clip_key(STAND)}"]\n'
                                          'speed = 50\n', encoding="utf-8")
            code, said = self.build(d, game, mod)
            self.assertNotEqual(code, 0)
            self.assertIn("no mod in the set makes a unit Descriptor_Unit_Nobody, and the game has none", said)

    def test_names(self):
        from rusemod.animlist import member_of
        self.assertEqual(anim.own_stem("Descriptor_Unit_Horse_Squad", STAND), "own_horse_squad_fusilier_standlod0")
        self.assertEqual(anim.own_stem("Descriptor_Para_X", "Rider stand.baf"), "own_para_x_rider_standlod0")
        # the name a listing gives it is the file the build adds, as for the game's own clips
        self.assertEqual(member_of(anim.own_data_name("own_xlod0")), anim.own_member("own_xlod0"))
        self.assertEqual(member_of(FILE_OF[STAND]), STAND)

    def test_the_file_refused(self):
        for text in ('[unit."Bad Name".clip."a.baf"]\nspeed = 50\n', '[unit.X.clip."a.txt"]\nspeed = 50\n',
                     '[unit.X.clip."a.baf"]\nspeed = 0\n', '[unit.X.action]\nt_stand = "missing.baf"\n',
                     '[unit.X.action]\nt_stand = "../escape.baf"\n', '[unit.X.thing]\na = 1\n', 'other = 3\n',
                     '[unit.X.figure."F"]\nt_stand = "a.baf"\n'):
            with tempfile.TemporaryDirectory() as d, self.subTest(text=text):
                f = Path(d) / anim.UNITS
                f.parent.mkdir(parents=True)
                f.write_text(text, encoding="utf-8")
                with self.assertRaises(anim.AnimError):
                    anim.mod_unit_clips(Path(d))
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(anim.AnimError):          # not a clip
                anim.add_unit_clip(Path(d), "Descriptor_Unit_X", "t_stand", b"not a clip")
            with self.assertRaises(anim.AnimError):
                anim.add_unit_clip(Path(d), "Not a unit!", "t_stand", baf.build(clip()))
            self.assertFalse((Path(d) / anim.UNITS).exists())

    def test_a_unit_taken_out_of_the_mod(self):
        with tempfile.TemporaryDirectory() as d:
            mod = Path(d)
            anim.add_unit_clip(mod, "Descriptor_Unit_A", "t_stand", baf.build(clip()))
            anim.add_unit_clip(mod, "Descriptor_Unit_B", "t_stand", baf.build(clip()))
            anim.remove_unit(mod, "Descriptor_Unit_A")
            self.assertEqual(sorted(anim.mod_unit_clips(mod)), ["Descriptor_Unit_B"])
            self.assertFalse((mod / anim.OWN / "Descriptor_Unit_A").exists())
            anim.remove_unit(mod, "Descriptor_Unit_B")
            self.assertFalse((mod / anim.UNITS).exists())


if __name__ == "__main__":
    unittest.main()
