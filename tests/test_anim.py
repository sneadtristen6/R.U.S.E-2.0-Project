"""rusemod.baf (the game's animation clips read, written, sampled and changed) and rusemod.anim (a mod's animations,
put in by the build into every pack that holds the clip)."""
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

B = "\\"
RUN = B.join(["genanim_15", "ww2", "res3d", "units", "common", "fusilier_courselod0.baf"])
FLEE = B.join(["genanim_15", "ww2", "res3d", "units", "common", "fusilier_deroutelod0.baf"])
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


if __name__ == "__main__":
    unittest.main()
