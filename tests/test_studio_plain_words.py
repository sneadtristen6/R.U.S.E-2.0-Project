"""The Studio's refusals that were English in every language, or in Python's words, said in the player's language (the
plain-words job, 2026-11-14; the owner: "There shouldn't be anywhere where it's like relying too heavily on them to
understand things."). Each case goes through the page's own way in (rusemod.webui.page_api), with a control that still
works or is said as before.

- A refusal made as `a if b else c` (errors.toml lists a refusal from the code: one written so gave it no words, and
  its map side stayed English): Show folder, Export… and the mod check's fixes with a map project open and no map.
- The era units list with no connection (the units scenarios' U-12: "The era units list couldn't be had: the era
  units list couldn't be loaded ([WinError 10061] No connection could be made because the target machine actively
  refused it)", English in every language): the Era units screen's notice and its download's refusal."""
import os
import socket
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rusemod.webui import page_api
from ruse_studio import era_units
from ruse_studio.api import StudioApi, StudioError

OFFLINE_US = ("this PC couldn't reach the server: there's no internet connection, or something on the way (a firewall, "
              "an antivirus, the server itself) turned the connection down")


def closed_port() -> int:
    """A port of this PC nothing listens on (a connection to it is refused at once)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


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


class TheEraListOffline(Base):
    def setUp(self):
        super().setUp()
        patch = mock.patch.dict(os.environ, {era_units.URL_ENV: f"http://127.0.0.1:{closed_port()}/"})
        patch.start()
        self.addCleanup(patch.stop)

    def test_its_notice_is_a_whole_sentence_in_the_studio_s_language(self):
        self.api.set_pref("lang", "fr")
        view = self.page.era_sections(False)
        self.assertEqual((view["sections"], view["whole"]), ([], True))
        self.assertEqual(view["message"], "La liste des unités d'époque n'a pas pu être obtenue : la liste des unités "
                                          "d'époque n'a pas pu être chargée (ce PC n'a pas pu joindre le serveur : il "
                                          "n'y a pas de connexion à Internet, ou quelque chose en chemin (un pare-feu, "
                                          "un antivirus, le serveur lui-même) a refusé la connexion)")
        self.assertNotIn("WinError", view["message"])

    def test_its_download_is_refused_in_the_studio_s_language(self):
        said = self.refused("ger", "era_download", "WWII")
        self.assertEqual(said, "Die Liste der Epochen-Einheiten war nicht zu bekommen: die Liste der "
                               "Epochen-Einheiten konnte nicht geladen werden (dieser PC hat den Server nicht erreicht: "
                               "Es gibt keine Internetverbindung, oder etwas auf dem Weg (eine Firewall, ein "
                               "Virenscanner, der Server selbst) hat die Verbindung abgelehnt)")

    def test_control_in_english(self):
        self.api.set_pref("lang", "us")
        view = self.page.era_sections(False)
        self.assertEqual(view["message"], f"The era units list couldn't be had: the era units list couldn't be loaded "
                                          f"({OFFLINE_US})")
        self.assertEqual(self.refused("us", "era_download", "WWII"), view["message"])


if __name__ == "__main__":
    unittest.main()
