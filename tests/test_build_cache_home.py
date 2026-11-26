"""The build cache follows the Studio's home (the owner's pick 40, 2026-11-14: "the build cache follows the Studio's
home"). Test in game, Export and Check this map keep what a build measures under <the Studio's home>/cache/build, not
under the platform's default home (rusemod.home.default_home) when the two differ.

On 6b265ec1 (build_cache() took no home) every test here but the control fails."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from test_studio import WithMod
from rusemod import build as build_module


def spy(real, seen: list):
    """The build, called as it is, its `cache` argument kept."""
    def call(*args, **kwargs):
        seen.append(kwargs.get("cache"))
        return real(*args, **kwargs)
    return call


class TheCache(unittest.TestCase):
    def test_a_home_given_is_where_the_cache_is(self):
        self.assertEqual(build_module.build_cache(Path("somewhere")), Path("somewhere") / "cache" / "build")

    def test_control_without_a_home_it_is_the_platform_s(self):
        other = Path(tempfile.gettempdir()) / "elsewhere"
        with mock.patch("rusemod.home.default_home", return_value=other):
            self.assertEqual(build_module.build_cache(), other / "cache" / "build")


class OnTheStudio(WithMod):
    """A Studio whose home (self.home) is not the platform's default home."""

    def setUp(self):
        super().setUp()
        self.elsewhere = Path(tempfile.mkdtemp(dir=self.tmp.name))
        patch = mock.patch("rusemod.home.default_home", return_value=self.elsewhere)
        patch.start()
        self.addCleanup(patch.stop)
        self.want = self.home / "cache" / "build"

    def wait(self, job: str) -> dict:
        end = time.time() + 60
        while self.api.job(job)["state"] == "running" and time.time() < end:
            time.sleep(0.02)
        return self.api.job(job)

    def check(self, seen: list):
        self.assertTrue(seen, "the build was never called")
        self.assertEqual(set(seen), {self.want})
        self.assertFalse((self.elsewhere / "cache").exists())

    def test_test_in_game_keeps_its_cache_in_the_studio_s_home(self):
        self.api.new_mod("Cache Test")
        seen = []
        with mock.patch("rusemod.play.build_and_write", spy(build_module.build_and_write, seen)):
            self.wait(self.api.test_in_game()["job"])
        self.check(seen)

    def test_export_keeps_its_cache_in_the_studio_s_home(self):
        self.api.new_mod("Cache Export")
        seen = []
        with mock.patch("ruse_studio.api.build_and_write", spy(build_module.build_and_write, seen)):
            self.wait(self.api.export_mod("1.0.0")["job"])
        self.check(seen)

    def test_check_this_map_keeps_its_cache_in_the_studio_s_home(self):
        self.api.new_mod("Cache Map", kind="map")
        seen = []
        with mock.patch("rusemod.build.build_and_write", spy(build_module.build_and_write, seen)):
            self.wait(self.api.map_check("SuperCrossRoads4")["job"])
        self.check(seen)


if __name__ == "__main__":
    unittest.main()
