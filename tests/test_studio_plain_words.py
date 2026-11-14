"""The Studio's refusals that were English in every language, or in Python's words, said in the player's language (the
plain-words job, 2026-11-14; the owner: "There shouldn't be anywhere where it's like relying too heavily on them to
understand things."). Each case goes through the page's own way in (rusemod.webui.page_api), with a control that still
works or is said as before.

- A refusal made as `a if b else c` (errors.toml lists a refusal from the code: one written so gave it no words, and
  its map side stayed English): Show folder, Export… and the mod check's fixes with a map project open and no map."""
import tempfile
import unittest
from pathlib import Path

from rusemod.webui import page_api
from ruse_studio.api import StudioApi, StudioError


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.api = StudioApi(game_dir=self.tmp / "nowhere", home=self.tmp / "home", index_path=self.tmp / "x.sqlite")
        self.page = page_api(self.api)

    def tearDown(self):
        self._tmp.cleanup()

    def refused(self, lang: str, call, *args) -> str:
        self.api.set_pref("lang", lang)
        with self.assertRaises(StudioError) as caught:
            getattr(self.page, call)(*args)
        return str(caught.exception)


class EitherOr(Base):
    def test_no_map_picked_in_the_studio_s_language(self):
        for call, args in (("mod_info", ("map",)), ("show_folder", ("map",)), ("open_mod_in_folder", ("map",))):
            with self.subTest(call=call):
                self.assertEqual(self.refused("fr", call, *args), "Choisissez ou créez d'abord une carte.")
                self.assertEqual(self.refused("jpn", call, *args), "先にマップを選ぶか作ってください。")

    def test_control_no_mod_picked_as_before(self):
        self.assertEqual(self.refused("fr", "mod_info", "mod"), "Choisissez ou créez d'abord un mod.")
        self.assertEqual(self.refused("us", "mod_info", "map"), "Pick or make a map first.")


if __name__ == "__main__":
    unittest.main()
