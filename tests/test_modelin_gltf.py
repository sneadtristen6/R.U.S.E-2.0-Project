"""glTF .gltf models with their files beside them (rusemod.modelin.read_gltf): the buffers and pictures read from the
files the .gltf names, as a .glb holds them; a see-through material's alphaMode kept, and its mask picture found
beside its colour picture as Poly Haven's plants come (<name>_alpha_<size>.png for <name>_diff_<size>.jpg); never a
file outside the model's folder."""
import json
import struct
import tempfile
import unittest
from pathlib import Path

from rusemod.dxt import png_bytes
from rusemod.modelin import ModelError, read_model

TMP = None   # the system's temp folder (TEMP)


def write_model(folder: Path, *, mask: bool = True, uri: str = "leaf.bin") -> Path:
    """One triangle (glTF's y up) with UVs, its colour picture leaf_diff_2k.png, alphaMode MASK, and (with `mask`)
    leaf_alpha_2k.png beside it."""
    pos = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 2, 0)          # the third corner 2 up (glTF y)
    uv = struct.pack("<6f", 0, 0, 1, 0, 0, 1)
    idx = struct.pack("<3H", 0, 1, 2) + b"\0\0"
    (folder / "leaf.bin").write_bytes(pos + uv + idx)
    (folder / "leaf_diff_2k.png").write_bytes(png_bytes(bytes([10, 120, 20] * 16), 4, 4))
    if mask:
        (folder / "leaf_alpha_2k.png").write_bytes(png_bytes(bytes([255, 255, 255] * 16), 4, 4))
    doc = {"asset": {"version": "2.0"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
           "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 0}]}],
           "materials": [{"name": "leaf", "alphaMode": "MASK", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
           "textures": [{"source": 0}], "images": [{"uri": "leaf_diff_2k.png"}],
           "buffers": [{"uri": uri, "byteLength": len(pos + uv + idx)}],
           "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36},
                           {"buffer": 0, "byteOffset": 36, "byteLength": 24},
                           {"buffer": 0, "byteOffset": 60, "byteLength": 6}],
           "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"},
                         {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC2"},
                         {"bufferView": 2, "componentType": 5123, "count": 3, "type": "SCALAR"}]}
    path = folder / "leaf_2k.gltf"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


class Gltf(unittest.TestCase):
    def test_read_with_its_files_beside_it(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            m = read_model(write_model(Path(d)))
            self.assertEqual(m.counts(), (3, 1))
            self.assertEqual([tuple(round(c, 6) for c in p) for p in m.meshes[0].positions],
                             [(0, 0, 0), (1, 0, 0), (0, 0, 2)])   # z up
            mat = m.materials[0]
            self.assertEqual(mat.data, (Path(d) / "leaf_diff_2k.png").read_bytes())
            self.assertEqual(mat.cutout, "MASK")
            self.assertEqual(mat.mask, (Path(d) / "leaf_alpha_2k.png").read_bytes())

    def test_no_mask_file_no_mask(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            mat = read_model(write_model(Path(d), mask=False)).materials[0]
            self.assertEqual((mat.cutout, mat.mask), ("MASK", b""))

    def test_never_a_file_outside_its_folder(self):
        with tempfile.TemporaryDirectory(dir=TMP) as d:
            inner = Path(d) / "model"
            inner.mkdir()
            path = write_model(inner, uri="../leaf.bin")
            (inner / "leaf.bin").replace(Path(d) / "leaf.bin")
            with self.assertRaises(ModelError):
                read_model(path)


if __name__ == "__main__":
    unittest.main()
