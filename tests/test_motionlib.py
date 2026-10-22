"""rusemod.motionlib (RUSE Decoy's motion library: the free sets' moves listed, each fetched when picked and kept only
when it's the listed file) and its Studio calls (ruse_studio.decoy: decoy_motions / decoy_motion_open /
decoy_motion_set_fetch)."""
import hashlib
import io
import tempfile
import threading
import unittest
import urllib.error
import zipfile
from pathlib import Path

from rusemod import motionlib
from ruse_studio.decoy import DecoyCalls, DecoyError
from test_mocap import bvh_text

WALK = bvh_text([{}] * 121).encode()
STAND = bvh_text([{}] * 61).encode()


def packed(name: str, data: bytes) -> bytes:
    """A move as the CMU set keeps it online: a zip of its one file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(name, data)
    return buf.getvalue()


WALK_ZIP = packed("02_01.bvh", WALK)


def listed(data: bytes, **more) -> dict:
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest(), **more}


def catalogue(zip_bytes: bytes = b"") -> dict:
    return {"sets": {"cmu": {"name": "CMU", "credit": "CMU credit", "licence": "free", "site": "http://cmu"},
                     "100style": {"name": "100STYLE", "credit": "100STYLE credit", "licence": "CC BY 4.0",
                                  "site": "https://zenodo", "zip": "https://zenodo/100STYLE.zip",
                                  "zip_size": len(zip_bytes), "zip_md5": hashlib.md5(zip_bytes).hexdigest()}},
            "moves": [listed(WALK, id="cmu/02_01", set="cmu", name="walk", group="various", kind="walk",
                             seconds=1.0, path="cmu/Sequence-001-009/02/Data/02_01.bvh",
                             url="https://raw/02_01.zip", zip_size=len(WALK_ZIP),
                             zip_sha256=hashlib.sha256(WALK_ZIP).hexdigest(), **{"from": 0.0, "to": None}),
                      listed(STAND, id="100style/Waving_ID", set="100style", name="Waving", group="waving hello",
                             way="ID", kind="stand", seconds=0.5, path="100STYLE/Waving/Waving_ID.bvh", url=None,
                             **{"from": 0.1, "to": 0.4})]}


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def opener(data: bytes):
    asked = []

    def open_(req):
        asked.append(req.full_url)
        return Answer(data)
    open_.asked = asked
    return open_


class Listed(unittest.TestCase):
    def test_the_list_that_ships(self):
        cat = motionlib.catalogue()
        self.assertEqual(len(cat["moves"]), 3205)
        self.assertEqual(sum(m["set"] == "cmu" for m in cat["moves"]), 2505)
        self.assertEqual(sum(m["set"] == "100style" for m in cat["moves"]), 700)
        for m in cat["moves"]:
            self.assertIn(m["kind"], motionlib.KINDS)
            self.assertRegex(m["sha256"], r"^[0-9a-f]{64}$")
            self.assertGreater(m["size"], 0)
            if m["set"] == "cmu":   # kept online as a small zip of its one file
                self.assertTrue(m["url"].startswith("https://raw.githubusercontent.com/Shriinivas/cmubvh/main/"))
                self.assertTrue(m["url"].endswith(m["path"].rsplit("/", 1)[-1][:-4] + ".zip"))
                self.assertRegex(m["zip_sha256"], r"^[0-9a-f]{64}$")
                self.assertLess(m["zip_size"], m["size"])
            else:
                self.assertIsNone(m["url"])
                self.assertIn(m["way"], motionlib.WAYS)
        self.assertEqual(len({m["id"] for m in cat["moves"]}), 3205)
        self.assertIn("NSF EIA-0196217", cat["sets"]["cmu"]["credit"])
        self.assertIn("CC BY 4.0", cat["sets"]["100style"]["credit"])

    def test_found_by_kind_and_words(self):
        cat = catalogue()
        self.assertEqual([m["id"] for m in motionlib.find(cat, "walk")], ["cmu/02_01"])
        self.assertEqual([m["id"] for m in motionlib.find(cat, words="waving hello")], ["100style/Waving_ID"])
        self.assertEqual(motionlib.find(cat, words="tank"), [])
        self.assertEqual(len(motionlib.find(cat, set_="100style")), 1)


class Fetched(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.home = Path(self.d.name)

    def test_a_move_fetched_once_and_kept(self):
        cat = catalogue()
        walk = cat["moves"][0]
        self.assertFalse(motionlib.have(self.home, walk))
        got = opener(WALK_ZIP)
        p = motionlib.fetch(self.home, walk, got)
        self.assertEqual(p.read_bytes(), WALK)                     # its one file, out of the zip
        self.assertEqual(got.asked, ["https://raw/02_01.zip"])
        self.assertTrue(motionlib.have(self.home, walk))
        motionlib.fetch(self.home, walk, got)
        self.assertEqual(len(got.asked), 1)                    # kept: not fetched again
        self.assertEqual(motionlib.set_state(self.home, cat, "cmu"), {"have": 1, "total": 1})

    def test_anything_else_refused(self):
        walk = catalogue()["moves"][0]
        for wrong in (WALK_ZIP[:-5], packed("02_01.bvh", WALK.replace(b"Hips", b"Hipz")), WALK):
            with self.subTest(n=len(wrong)), self.assertRaises(motionlib.MotionLibError):
                motionlib.fetch(self.home, walk, opener(wrong))
        self.assertFalse(motionlib.where(self.home, walk).parent.exists() and
                         any(motionlib.where(self.home, walk).parent.iterdir()))

        def down(req):
            raise urllib.error.URLError("no network")
        with self.assertRaises(motionlib.MotionLibError) as e:
            motionlib.fetch(self.home, walk, down)
        self.assertIn("couldn't be reached", str(e.exception))
        with self.assertRaises(motionlib.MotionLibError) as e:   # a set that comes whole: the page offers it
            motionlib.fetch(self.home, catalogue()["moves"][1], opener(STAND))
        self.assertEqual(str(e.exception), "set")

    def zipped(self, extra=()):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("100STYLE/Waving/Waving_ID.bvh", STAND)
            z.writestr("__MACOSX/100STYLE/Waving/._Waving_ID.bvh", b"junk")
            for name, data in extra:
                z.writestr(name, data)
        return buf.getvalue()

    def test_a_whole_set_fetched_its_moves_kept(self):
        big = self.zipped(extra=[("100STYLE/Other/Other_ID.bvh", b"not listed")])
        cat = catalogue(big)
        seen = []
        state = motionlib.fetch_set(self.home, cat, "100style", progress=lambda d, t: seen.append((d, t)),
                                    opener=opener(big))
        self.assertEqual(state, {"have": 1, "total": 1})
        self.assertEqual(seen[-1], (len(big), len(big)))
        self.assertEqual(motionlib.where(self.home, cat["moves"][1]).read_bytes(), STAND)
        self.assertEqual(sorted(p.name for p in motionlib.folder(self.home).rglob("*") if p.is_file()),
                         ["Waving_ID.bvh"])                     # the big file deleted; nothing unlisted kept
        cut = catalogue(big)
        with self.assertRaises(motionlib.MotionLibError):         # cut off: refused, nothing left behind
            motionlib.fetch_set(Path(self.d.name) / "other", cut, "100style", opener=opener(big[:-10]))
        self.assertFalse((Path(self.d.name) / "other" / motionlib.FOLDER / "100style.zip.part").exists())


class Calls(DecoyCalls):
    def __init__(self, home):
        self._home = Path(home)
        self._saving = threading.RLock()


class DecoyLibrary(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        self.calls = Calls(self.d.name)

    def test_listed_by_kind(self):
        got = self.calls.decoy_motions("walk")
        kinds = {k["id"]: k["count"] for k in got["kinds"]}
        self.assertEqual(sum(kinds.values()), 3205)
        self.assertTrue(all(r["kind"] == "walk" for r in got["rows"]))
        self.assertEqual(got["total"], kinds["walk"])
        self.assertEqual((got["sets"]["cmu"]["have"], got["sets"]["100style"]["whole"]), (0, True))
        with self.assertRaises(DecoyError):
            self.calls.decoy_motions("tanks")

    def test_a_move_opened_with_its_stretch_and_credit(self):
        cat = catalogue()
        self.calls._decoy_motion_cat = cat
        stand = cat["moves"][1]
        self.assertEqual(self.calls.decoy_motion_open(stand["id"]), {"fetch_set": "100style"})
        p = motionlib.where(Path(self.d.name), stand)
        p.parent.mkdir(parents=True)
        p.write_bytes(STAND)                                     # as fetch_set keeps it
        got = self.calls.decoy_motion_open(stand["id"])
        self.assertEqual((got["from"], got["length"], got["credit"], got["missing"]), (0.1, 0.3, "100STYLE credit", []))
        self.assertIn(got["id"], self.calls._decoy_mocap)        # open for decoy_mocap_preview / _use
        with self.assertRaises(DecoyError):
            self.calls.decoy_motion_open("cmu/nope")

    def test_a_whole_set_in_the_background(self):
        cat = catalogue(b"x")
        self.calls._decoy_motion_cat = cat
        started = threading.Event()

        def fake(home, cat_, set_, progress, opener=None):
            progress(1, 1)
            started.set()
            raise motionlib.MotionLibError("no network")
        orig = motionlib.fetch_set
        motionlib.fetch_set = fake
        try:
            job = self.calls.decoy_motion_set_fetch("100style")
            self.assertEqual(job["state"], "fetching")
            started.wait(5)
            self.calls._decoy_set_job["100style"]["thread"].join(5)
        finally:
            motionlib.fetch_set = orig
        sets = self.calls.decoy_motion_sets()
        self.assertEqual((sets["100style"]["job"]["state"], sets["100style"]["job"]["message"]), ("failed", "no network"))
        with self.assertRaises(DecoyError):
            self.calls.decoy_motion_set_fetch("cmu")


if __name__ == "__main__":
    unittest.main()
