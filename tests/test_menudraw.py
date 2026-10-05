"""The 3D map picture a blank map's menus show (rusemod.menudraw): the slab the game's own are drawn as, the white
dots the build puts where players start (wherever the starting points are then), and the big pictures' frame."""
import unittest

from rusemod import menudraw
from rusemod.menudraw import (BACK_W, BACK_Y, FRONT_W, FRONT_Y, HEIGHT, MIDDLE, SOIL, WIDTH, dots, dotted, framed,
                              places, slab, to_picture)

WHITE = (255, 255, 255)


def at(rgba, x, y, w=WIDTH):
    o = (int(y) * w + int(x)) * 4
    return tuple(rgba[o:o + 4])


class TheSlab(unittest.TestCase):
    def test_shaped_as_the_games_own(self):
        """The map's top a trapezoid from its back edge (BACK_W wide at BACK_Y) to its front (FRONT_W at FRONT_Y),
        its soil below that, everything round it see-through (D-Day's own: 349 and 580 pixels, rows 10 and 170)."""
        for kind in menudraw.KINDS:
            px = slab(kind)
            self.assertEqual(len(px), WIDTH * HEIGHT * 4)
            for x, y in ((2, 2), (WIDTH - 3, 2), (2, HEIGHT - 3), (WIDTH - 3, HEIGHT - 3),
                         (MIDDLE - BACK_W / 2 - 6, BACK_Y + 3), (MIDDLE, FRONT_Y + SOIL + 3)):
                self.assertEqual(at(px, x, y)[3], 0, (kind, x, y))
            for x, y in ((MIDDLE, BACK_Y + 3), (MIDDLE - BACK_W / 2 + 4, BACK_Y + 3), (MIDDLE, 90),
                         (MIDDLE - FRONT_W / 2 + 4, FRONT_Y - 2), (MIDDLE, FRONT_Y + SOIL / 2)):
                self.assertEqual(at(px, x, y)[3], 255, (kind, x, y))

    def test_the_sea_or_the_land(self):
        sea, land = at(slab("ocean"), MIDDLE, 90), at(slab("land"), MIDDLE, 90)
        self.assertGreater(sea[2], sea[0])     # blue over red
        self.assertGreater(land[1], land[2])   # green over blue

    def test_no_dots_of_its_own(self):
        for kind in menudraw.KINDS:
            px = slab(kind)
            self.assertFalse(any(px[i:i + 3] == bytes(WHITE) for i in range(0, len(px), 4)), kind)

    def test_the_same_bytes_every_time(self):
        self.assertEqual(slab("land", [(0.3, 0.6)]), slab("land", [(0.3, 0.6)]))

    def test_no_such_kind(self):
        with self.assertRaises(ValueError):
            slab("lava")


class TheDots(unittest.TestCase):
    def test_north_is_the_back_edge_and_west_the_left(self):
        self.assertEqual(to_picture(0.5, 0.0), (MIDDLE, BACK_Y))
        self.assertEqual(to_picture(0.5, 1.0), (MIDDLE, FRONT_Y))
        self.assertEqual(to_picture(0.0, 1.0), (MIDDLE - FRONT_W / 2, FRONT_Y))
        self.assertLess(to_picture(0.0, 0.5)[0], to_picture(1.0, 0.5)[0])
        self.assertLess(to_picture(0.5, 0.5)[1], (BACK_Y + FRONT_Y) / 2)   # the far half looks smaller

    def test_a_dot_where_a_start_is(self):
        base = slab("land")
        x, y = to_picture(0.25, 0.5)
        self.assertNotEqual(at(base, x, y)[:3], WHITE)
        self.assertEqual(at(dotted(base, [(0.25, 0.5)]), x, y), WHITE + (255,))

    def test_moving_a_start_moves_its_dot(self):
        """(the owner, 2026-10-05: the dots go "where that's actually the spawn point of those players")"""
        base = slab("ocean")
        before, after = dotted(base, [(0.25, 0.5)]), dotted(base, [(0.75, 0.3)])
        old, new = to_picture(0.25, 0.5), to_picture(0.75, 0.3)
        self.assertEqual(at(before, *old)[:3], WHITE)
        self.assertNotEqual(at(after, *old)[:3], WHITE)
        self.assertEqual(at(after, *new)[:3], WHITE)

    def test_one_dot_for_starts_in_one_place(self):
        """A map's starting points for several team setups often share a place (D-Day: 10 points, 6 places)."""
        self.assertEqual(len(dots([(0.5, 0.5), (0.505, 0.5), (0.9, 0.9)])), 2)

    def test_none_off_the_map(self):
        self.assertEqual(dots([(-0.1, 0.5), (0.5, 1.2)]), [])

    def test_map_points_as_fractions_of_its_ground(self):
        self.assertEqual(places((0.0, 0.0, 400.0, 200.0), [(100.0, 50.0, 7.0)]), [(0.25, 0.25)])

    def test_only_on_a_3d_map_picture(self):
        with self.assertRaises(ValueError):
            dotted(bytes(16), [(0.5, 0.5)])


class TheFrame(unittest.TestCase):
    def test_the_games_grey_edge_and_its_shade(self):
        w, h = 64, 36
        px = framed(bytes((200, 200, 200, 255)) * (w * h), w, h)
        self.assertEqual(at(px, 0, 0, w), menudraw.FRAME + (255,))
        self.assertEqual(at(px, 2, h // 2, w), menudraw.FRAME + (255,))
        inside = at(px, 3, h // 2, w)
        self.assertLess(inside[0], 200)                                  # shaded just inside the edge
        self.assertEqual(at(px, w // 2, h // 2, w), (200, 200, 200, 255))  # the middle as it was


if __name__ == "__main__":
    unittest.main()
