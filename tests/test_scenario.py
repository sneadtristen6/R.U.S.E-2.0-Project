"""A map's scenario file (rusemod.scenario): its zones and design items, on a made-up file laid out like the game's
(the real ones are checked by tools, on all 102 the game ships)."""
import struct
import unittest

from fixtures import make_ndf, val
from rusemod.scenario import AREA, MAGIC, Scenario, ScenarioError


def u32(*vs) -> bytes:
    return struct.pack(f"<{len(vs)}I", *vs)


def f32s(*vs) -> bytes:
    return struct.pack(f"<{len(vs)}f", *vs)


def zone(number: int, name: str, square: float) -> bytes:
    """A square zone of side `square` cut into 2 triangles, its 4 corners its border."""
    raw = name.encode()
    body = AREA + u32(2, number, len(raw)) + raw + bytes(-len(raw) % 4)
    body += AREA + f32s(square / 2, square / 2, 100.0)
    body += AREA + u32(1) + u32(0, 2, 0, 4)
    body += AREA + u32(0, 2, 0, 4)
    body += AREA + u32(0, 4)
    corners = [(0, 0), (square, 0), (square, square), (0, square)]
    body += AREA + u32(4, 2) + b"".join(f32s(x, y, 100.0, 0.0, 0.0) for x, y in corners)
    body += AREA + u32(0, 1, 2, 0, 2, 3)
    body += AREA + u32(4, 0, 1, 2, 3) + AREA + b"END0"
    return body


def design_items() -> bytes:
    """One starting point (alliance 2, turned 1.5 radians) and one spawn with a unit class, as TGameDesignItems."""
    def s(i):
        return val(0x07, struct.pack("<I", i))

    def ref(i, cls):
        return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))

    def vec(x, y, z):
        return val(0x0B, struct.pack("<3f", x, y, z))

    return make_ndf(
        objects=[(0, [(0, vec(1000.0, 2000.0, 50.0)), (1, val(0x05, struct.pack("<f", 1.5))), (2, ref(2, 1))]),
                 (0, [(0, vec(3000.0, 4000.0, 60.0)), (2, ref(3, 2))]),
                 (1, [(3, val(0x02, struct.pack("<i", 2))), (4, s(0))]),
                 (2, [(5, s(1))])],
        classes=["TGameDesignItem", "TGameDesignAddOn_StartingPoint", "TGameDesignAddOn_Spawn"],
        props=[("Position", 0), ("Rotation", 0), ("AddOn", 0), ("AllianceNum", 1), ("Name", 1),
               ("PythonClassName", 2)],
        strings=["HQ_Allies", "front.parametres.Classes.Unit_M4_Sherman"])


def scenario(zones=(("zone_a", 1000.0), ("zone_b", 500.0)), items=True) -> bytes:
    data = u32(len(zones)) + b"".join(zone(k, n, sq) for k, (n, sq) in enumerate(zones))
    out = MAGIC + bytes(16) + bytes(2) + u32(4, 1) + u32(len(data)) + data
    if items:
        nd = design_items()
        out += u32(len(nd)) + nd
    return out


class Reading(unittest.TestCase):
    def test_zones(self):
        s = Scenario.read(scenario())
        self.assertEqual(s.version, 4)
        self.assertEqual([(z.number, z.name) for z in s.zones], [(0, "zone_a"), (1, "zone_b")])
        a = s.zones[0]
        self.assertEqual((a.anchor, len(a.vertices), a.triangles), ((500.0, 500.0, 100.0), 4, [(0, 1, 2), (0, 2, 3)]))
        self.assertEqual(a.outline_points(), [(0.0, 0.0), (1000.0, 0.0), (1000.0, 1000.0), (0.0, 1000.0)])
        self.assertEqual(a.outline, [0, 1, 2, 3])

    def test_design_items(self):
        start, spawn = Scenario.read(scenario()).items
        self.assertEqual((start.kind, start.position, start.rotation), ("StartingPoint", (1000.0, 2000.0, 50.0), 1.5))
        self.assertEqual(start.values, {"AllianceNum": 2, "Name": "HQ_Allies"})
        self.assertEqual((spawn.kind, spawn.rotation, spawn.values["PythonClassName"]),
                         ("Spawn", 0.0, "front.parametres.Classes.Unit_M4_Sherman"))

    def test_a_file_without_items_and_broken_files(self):
        self.assertEqual(Scenario.read(scenario(items=False)).items, [])
        with self.assertRaises(ScenarioError):
            Scenario.read(b"NOTASCENARIO" + bytes(40))
        broken = bytearray(scenario())
        broken[broken.find(b"END0")] = ord("X")
        with self.assertRaises(ScenarioError):
            Scenario.read(bytes(broken))


if __name__ == "__main__":
    unittest.main()
