"""The Generic Horse's horse in a picture of our own (rusemod.horsepaint; the owner, 2026-11-13: "new picture of
horse"), switched on only after his look (rusemod.horsesquad.OWN_PICTURE).

Always: the noise is the same numbers every time and stays in its range; a model that isn't the horse is refused in
words. With RUSE_GAME naming a game folder: the made files' horse painted ours, the same bytes twice, its pixels none
of the game's (the horse's own part of the picture compared texel by texel), the riders' picture and every other part
of the file as it was; with the switch on, both files carry it; with it off, the files are as before."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from rusemod import horsepaint as hp

GAME = Path(os.environ["RUSE_GAME"]) if os.environ.get("RUSE_GAME") else None
INDEX = Path(os.environ["RUSE_GAME_INDEX"]) if os.environ.get("RUSE_GAME_INDEX") else None


class Noise(unittest.TestCase):
    def test_the_same_numbers_every_time_in_range(self):
        yy, xx = np.mgrid[0:64, 0:64].astype(np.float64)
        a, b = hp.noise(xx / 3.0, yy / 5.0, 7), hp.noise(xx / 3.0, yy / 5.0, 7)
        self.assertTrue(np.array_equal(a, b))
        self.assertGreaterEqual(a.min(), -1.0)
        self.assertLessEqual(a.max(), 1.0)
        self.assertGreater(a.std(), 0.1)                       # (it varies)
        self.assertFalse(np.array_equal(a, hp.noise(xx / 3.0, yy / 5.0, 8)))   # (each seed its own)

    def test_a_model_that_isnt_the_horse_is_refused_in_words(self):
        points = np.array([[0.0, 1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 2.0, 0.0]])
        with self.assertRaisesRegex(hp.PaintError, "the model's parts aren't the horse's"):
            hp.paint(points, np.array([[0.1, 0.1], [0.2, 0.1], [0.1, 0.2]]), np.array([[0, 1, 2]]), 32, 16)


def images(raw: bytes) -> dict:
    from rusemod.gltf import glb_views
    doc, views = glb_views(raw)
    out = {}
    for m in doc["materials"]:
        src = doc["textures"][m["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]
        out[m["name"]] = views[doc["images"][src]["bufferView"]]
    return out


def pixels(png: bytes):
    from rusemod.png import read_png
    w, h, data = read_png(png)
    channels = len(data) // (w * h)
    return np.frombuffer(bytes(data), np.uint8).reshape(h, w, channels)[..., :3]


@unittest.skipUnless(GAME is not None and GAME.is_dir(), "RUSE_GAME names no game folder")
class OnTheMadeFiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from rusemod import horsesquad
        cls.tmp = tempfile.TemporaryDirectory()
        cls.files = horsesquad.horse_squad_glbs(GAME, Path(cls.tmp.name) / "game", index=INDEX, say=lambda s: None)
        cls.raw = {k: v.read_bytes() for k, v in cls.files.items()}
        cls.ours = hp.with_own_picture(cls.raw["rifle"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_same_bytes_twice(self):
        self.assertEqual(hp.with_own_picture(self.raw["rifle"]), self.ours)

    def test_none_of_the_game_s_pixels_on_the_horse(self):
        """Every texel of the horse's own part of the picture (its UV triangles, both its sides) compared with the
        game's at the same place: under 1 % alike by chance, and no 4 x 4 block the same."""
        from rusemod.gltf import glb_views
        game = pixels(images(self.raw["rifle"])["TSCForceDXT1_diffuseTexture01"]).astype(int)
        ours = pixels(images(self.ours)[hp.HORSE_MATERIAL]).astype(int)
        self.assertEqual(game.shape, ours.shape)
        doc, views = glb_views(self.raw["rifle"])
        k = next(i for i, m in enumerate(doc["materials"]) if m["name"] == "TSCForceDXT1_diffuseTexture01")
        mask = np.zeros(game.shape[:2], bool)
        h, w = mask.shape
        for mesh in doc["meshes"]:
            for prim in mesh["primitives"]:
                if prim.get("material") != k:
                    continue
                uv = np.mod(hp._read(doc, views, prim["attributes"]["TEXCOORD_0"]).astype(float), 1.0)
                for tri in hp._read(doc, views, prim["indices"]).reshape(-1, 3):
                    q = uv[tri] * [w, h]
                    x0, y0 = np.floor(q.min(0)).astype(int)
                    x1, y1 = np.ceil(q.max(0)).astype(int)
                    mask[max(y0, 0):y1, max(x0, 0):x1] = True       # (its box: a little more than the horse, never less)
        same = (game == ours).all(-1) & mask
        self.assertGreater(mask.sum(), 10000)
        self.assertLess(same.sum() / mask.sum(), 0.01, f"{same.sum()} of {mask.sum()} texels the game's")
        blocks = same[: h // 4 * 4, : w // 4 * 4].reshape(h // 4, 4, w // 4, 4).all((1, 3))
        self.assertFalse(blocks.any())

    def test_the_riders_picture_and_the_rest_of_the_file_as_they_were(self):
        from rusemod.gltf import glb_views
        was, now = images(self.raw["rifle"]), images(self.ours)
        self.assertEqual(sorted(now), sorted([hp.HORSE_MATERIAL, "TSCOther_diffuseTexture01"]))
        self.assertEqual(now["TSCOther_diffuseTexture01"], was["TSCOther_diffuseTexture01"])
        a, va = glb_views(self.raw["rifle"])
        b, vb = glb_views(self.ours)
        for key in ("meshes", "nodes", "skins", "animations", "accessors", "scenes", "asset"):
            self.assertEqual(a[key], b[key], key)
        image_views = {img["bufferView"] for img in a["images"]}
        self.assertEqual([x for i, x in enumerate(va) if i not in image_views],
                         [x for i, x in enumerate(vb) if i not in image_views])
        horse = next(m for m in b["materials"] if m["name"] == hp.HORSE_MATERIAL)
        self.assertNotIn("rusemod_texture", horse.get("extras", {}))   # (no game picture named on ours)

    def test_with_the_switch_on_both_files_carry_it_and_off_they_are_as_before(self):
        from rusemod import horsesquad
        with tempfile.TemporaryDirectory() as d, mock.patch.object(horsesquad, "OWN_PICTURE", True):
            on = horsesquad.horse_squad_glbs(GAME, Path(d) / "on", index=INDEX, say=lambda s: None)
            got = {k: images(v.read_bytes()) for k, v in on.items()}
        self.assertEqual(got["rifle"][hp.HORSE_MATERIAL], images(self.ours)[hp.HORSE_MATERIAL])
        self.assertEqual(got["bazooka"][hp.HORSE_MATERIAL], got["rifle"][hp.HORSE_MATERIAL])
        self.assertFalse(horsesquad.OWN_PICTURE)                     # (off until the owner has seen it)
        self.assertIn("TSCForceDXT1_diffuseTexture01", images(self.raw["bazooka"]))


if __name__ == "__main__":
    unittest.main()
