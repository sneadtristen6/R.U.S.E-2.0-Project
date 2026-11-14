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
from test_studio import M4, WithMod

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


class CodeNames(WithMod):
    """The units scenarios' U-4 and U-5: a refusal naming a unit by its address ("There's already a unit called
    Descriptor_Unit_Tiger_II (from 'Tiger II')") or a value by its game name ("ProductionPrice: 10000000000 doesn't
    fit"), in every language. Now the unit by its name and the value by its label, in the Studio's language; the
    control: the game's names when the Studio shows the game's own names (its "base" setting, a modder's choice)."""

    def setUp(self):
        super().setUp()
        self.page = page_api(self.api)
        self.api.new_mod("Tanks")

    def refused(self, lang: str, call, *args, **kwargs) -> str:
        self.api.set_pref("lang", lang)
        with self.assertRaises(StudioError) as caught:
            getattr(self.page, call)(*args, **kwargs)
        return str(caught.exception)

    def test_a_name_taken_is_said_by_the_unit_s_name(self):
        self.page.new_unit(M4, "Tiger II", 10, group="new")
        self.assertEqual(self.refused("fr", "new_unit", M4, "Tiger II", 10, group="new"),
                         "Il y a déjà une unité nommée Tiger II. Choisissez un autre nom.")
        said = self.refused("ru", "new_unit", M4, "Tiger-II", 10, group="new")
        self.assertEqual(said, "Tiger-II слишком похоже на имя Tiger II — юнита, который уже есть в игре или в вашем "
                               "моде: у них были бы одни и те же файлы. Выберите другое имя.")
        self.assertNotIn("Descriptor_", said)

    def test_a_number_too_big_is_said_by_the_value_s_label(self):
        self.assertEqual(self.refused("fr", "new_unit", M4, "Big", 10_000_000_000, group="new"),
                         "Prix : 10000000000 ne convient pas (doit être entre -2147483648 et 2147483647)")
        self.assertEqual(self.refused("us", "new_unit", M4, "Big", 10_000_000_000, group="new"),
                         "Price: 10000000000 doesn't fit (it must be -2147483648 to 2147483647)")

    def test_control_the_game_s_own_names_when_the_studio_shows_them(self):
        self.assertEqual(self.refused("base", "new_unit", M4, "Big", 10_000_000_000, group="new"),
                         "ProductionPrice: 10000000000 doesn't fit (it must be -2147483648 to 2147483647)")
        self.assertIn("Panther", self.page.new_unit(M4, "Panther", 10, group="new")["address"])  # (made)


class TheStudiosOtherRefusals(Base):
    """The Studio's own refusals of Ground paint, the Nations tab, RUSE Decoy, the Music tab, flag types and the
    missions (their own kinds of error, not StudioError): English in every language until now, though in plain words.
    A few the page can meet without the game, each in another language; the control: English."""

    def test_ground_paint_s_and_the_nations_tab_s_refusals_in_the_studio_s_language(self):
        self.assertEqual(self.refused("ita", "online_texture", "usgs", "", "lots"),
                         "La dimensione di una foto è un numero di metri.")
        self.assertEqual(self.refused("cz", "add_ground_picture", "Mud", "data:image/png;base64,AAAA"),
                         "Nejprve vyberte nebo vytvořte mod: jeho obrázky se ukládají do něj.")
        self.assertEqual(self.refused("ru", "nation_words_set", 6, "army", {}),
                         "У армии Японии в игре нет названия, которое можно изменить.")
        self.assertEqual(self.refused("fa", "nation_words_set", 6, "motto", {}),
                         "چیزی به نام 'motto' برای تغییر نیست.")

    def test_control_in_english(self):
        self.api.set_pref("lang", "us")   # (passed on as it was raised: the words are the same)
        for call, args, words in (("online_texture", ("usgs", "", "lots"), "A photo's size is a number of metres."),
                                  ("nation_words_set", (6, "army", {}), "Japan's army has no name to change in the game.")):
            with self.subTest(call=call), self.assertRaises(Exception) as caught:
                getattr(self.page, call)(*args)
            self.assertEqual(str(caught.exception), words)


class TheChangesFileBrokenByHand(WithMod):
    """The units scenarios' U-11: the mod's src/studio.rndf broken by hand made the unit page's notice and every
    refusal English in every language (an EditsFileError, which the page never said again). Now its frame is said in
    the Studio's language: which file, and to fix or delete it; the mistake it names inside, the file reader's own
    words, stays as it came (the engine's checks of a mod's files: the owner's pick of 2026-10-16, for later)."""

    def setUp(self):
        super().setUp()
        self.page = page_api(self.api)
        folder = Path(self.api.new_mod("Tanks")["current"])
        self.rndf = folder / "src" / "studio.rndf"
        self.rndf.parent.mkdir(parents=True, exist_ok=True)
        self.rndf.write_text("patch $/GFX/Everything/Nothing ( oops\n", encoding="utf-8")

    def test_the_unit_page_and_a_refusal_say_it_in_the_studio_s_language(self):
        self.api.set_pref("lang", "fr")
        why = self.page.unit(M4)["why_not"]
        self.assertTrue(why.startswith(f"{self.rndf} contient une erreur ("), why)
        self.assertTrue(why.endswith("). Corrigez-le, ou supprimez-le pour recommencer."), why)
        with self.assertRaises(StudioError) as caught:
            self.page.edit(M4, "SeuilMort", 15)
        self.assertEqual(str(caught.exception), why)
        self.assertEqual(self.rndf.read_text(encoding="utf-8"), "patch $/GFX/Everything/Nothing ( oops\n")

    def test_control_in_english_as_before(self):
        self.api.set_pref("lang", "us")
        why = self.page.unit(M4)["why_not"]
        self.assertTrue(why.startswith(f"{self.rndf} has a mistake ("), why)
        self.assertTrue(why.endswith("). Fix it, or delete it to start over."), why)


if __name__ == "__main__":
    unittest.main()
