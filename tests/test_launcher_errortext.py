"""The Launcher's refusals in the player's language (ruse_launcher.errortext; the export scenarios' FE-9, 2026-11-14:
every refusal of the Launcher was English, whatever its language; the owner, 2026-11-14: "There shouldn't be anywhere
where it's like relying too heavily on them to understand things."): every refusal the Launcher raises or passes on
has its words in errors.toml in all eleven languages with the same blanks, and a page call's refusal comes out in the
Launcher's language with its values filled in, a file Windows held in words (FE-14), why a download failed in plain
words inside it (never "[WinError 10061] No connection could be made..."). The controls: English stays English, a
text no entry makes stays as it came, and what isn't refused still works."""
import socket
import tempfile
import tomllib
import unittest
from pathlib import Path

from rusemod import wordedtext
from rusemod.webui import Job, page_api
from ruse_launcher import errortext
from ruse_launcher.api import LauncherApi, LauncherError


def closed_port() -> int:
    """A port of this PC nothing listens on (a connection to it is refused at once)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class EveryRefusalHasItsWords(unittest.TestCase):
    def test_every_refusal_in_the_code_is_in_eleven_languages(self):
        templates = errortext.templates()
        self.assertGreater(len(templates), 60)
        self.assertEqual(wordedtext.missing(errortext.FILE, templates), [],
                         "refusals with no entry in ruse_launcher/errors.toml: list them and add their words")

    def test_no_entry_is_left_over(self):
        entries = tomllib.loads(errortext.FILE.read_text(encoding="utf-8"))
        keys = {wordedtext.key_of(t) for t in errortext.templates()}
        self.assertEqual(sorted(set(entries) - keys), [])

    def test_a_reason_inside_a_frame_names_frames_that_exist(self):
        entries = tomllib.loads(errortext.FILE.read_text(encoding="utf-8"))
        templates = set(errortext.templates())
        for words in entries.values():
            for frame in ([words["within"]] if isinstance(words.get("within"), str) else words.get("within", [])):
                self.assertIn(frame, templates, words["us"])
                self.assertIn(frame, errortext.WITHIN, words["us"])


class Worded(unittest.TestCase):
    def test_a_refusal_in_another_language(self):
        self.assertEqual(errortext.worded("Give the mod set a name.", "fr"), "Donnez un nom à l'ensemble de mods.")
        self.assertEqual(errortext.worded("There's no mod set called 'Tanks' any more. Pick another one.", "ger"),
                         "Es gibt kein Mod-Set namens 'Tanks' mehr. Wählen Sie ein anderes.")

    def test_why_a_download_failed_inside_it(self):
        offline = ("this PC couldn't reach the server: there's no internet connection, or something on the way (a "
                   "firewall, an antivirus, the server itself) turned the connection down")
        self.assertEqual(errortext.worded(f"Tank Mod couldn't be downloaded ({offline}).", "ru"),
                         "Tank Mod не удалось скачать (этот ПК не смог связаться с сервером: нет подключения к "
                         "интернету, или что-то на пути (брандмауэр, антивирус, сам сервер) отклонило соединение).")
        self.assertEqual(errortext.worded("Tank Mod couldn't be downloaded (the server answered 404).", "sc"),
                         "无法下载 Tank Mod（服务器返回了 404）。")
        # a reason no entry makes stays as it came, its frame said
        self.assertEqual(errortext.worded("Tank Mod couldn't be downloaded (something new).", "cz"),
                         "Tank Mod se nepodařilo stáhnout (something new).")

    def test_english_and_unknown_texts_stay(self):
        text = "Give the mod set a name."
        self.assertEqual(errortext.worded(text, "us"), text)
        self.assertEqual(errortext.worded(text, "base"), text)
        self.assertEqual(errortext.worded("Something nobody wrote", "fr"), "Something nobody wrote")
        # a reason alone is never said: only inside its frames
        self.assertEqual(errortext.worded("the server answered 404", "fr"), "the server answered 404")


class ThePageGetsIt(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.api = LauncherApi(home=self.tmp / "home", game_dir=self.tmp / "nowhere",
                               index_url=f"http://127.0.0.1:{closed_port()}/index.toml")
        self.page = page_api(self.api)

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_mod_set_with_no_name_in_every_language(self):
        said = {}
        for lang in wordedtext.LANGS:
            self.api.set_pref("lang", lang)
            with self.assertRaises(LauncherError) as caught:
                self.page.new_set("", [])
            said[lang] = str(caught.exception)
        self.assertEqual(said["us"], "Give the mod set a name.")
        self.assertEqual(said["jpn"], "MODセットに名前を付けてください。")
        self.assertEqual(len(set(said.values())), len(said), said)   # each language its own words

    def test_its_key_for_bug_watch_stays(self):
        self.api.set_pref("lang", "pol")
        with self.assertRaises(LauncherError) as caught:
            self.page.new_set("", [])
        self.assertEqual(caught.exception.words_key, "set_no_name")
        self.assertEqual(str(caught.exception), "Nadaj zestawowi modów nazwę.")

    def test_the_mod_list_offline_says_why_in_plain_words(self):
        self.api.set_pref("lang", "ger")
        view = self.page.browse("", True)
        self.assertEqual((view["source"], view["whole"]), ("none", True))
        self.assertEqual(view["message"], "Die Mod-Liste konnte nicht geladen werden (dieser PC hat den Server nicht "
                                          "erreicht: Es gibt keine Internetverbindung, oder etwas auf dem Weg (eine "
                                          "Firewall, ein Virenscanner, der Server selbst) hat die Verbindung "
                                          "abgelehnt), und es gibt keine Kopie von früher.")
        self.assertNotIn("WinError", view["message"])

    def test_a_file_windows_held_is_named_in_words(self):
        self.api.set_pref("lang", "ita")
        held = PermissionError(13, "Access is denied", str(self.tmp / "library" / "tank"), None,
                               str(self.tmp / "library" / ".old-tank"))
        said = self.api.page_error(held)
        self.assertIsInstance(said, LauncherError)
        self.assertEqual(str(said), f"{self.tmp / 'library' / 'tank'} non si è potuto spostare in "
                                    f"{self.tmp / 'library' / '.old-tank'}, perché un altro programma ne tiene aperto "
                                    f"un file o Windows non lo ha permesso. Chiudi quel programma, poi riprova.")
        # an OSError naming no file, not a full disk (a connection's), passes on as it was
        self.assertIsNone(self.api.page_error(ConnectionResetError(104, "reset")))

    def test_a_failed_job_s_refusal(self):
        self.api.set_pref("lang", "spa")
        job = Job()
        job.state, job.message = "failed", "Mods are being installed: wait for it to finish."
        self.api._jobs[job.id] = job
        self.assertEqual(self.page.job(job.id)["message"], "Se están instalando mods: espera a que termine.")

    def test_control_what_isn_t_refused_still_works(self):
        self.api.set_pref("lang", "fr")
        self.assertEqual([s["id"] for s in self.page.mod_sets()], ["vanilla"])
        self.assertIsNone(self.api.page_error(ValueError("not ours")))            # only the Launcher's own
        self.assertIsNone(self.api.page_error(LauncherError("Nobody's words")))  # nothing to say differently


class ADamagedModFile(unittest.TestCase):
    """The export scenarios' FE-9: a mod file with one byte changed (a download gone wrong) stopped the Launcher's Add
    with zlib's or zipfile's own words ("Error -3 while decompressing data: invalid code lengths set", "Bad CRC-32 for
    file 'src/eco.rndf'"), no refusal of ours. Now it's said in words naming the file inside, in the player's language;
    the same file undamaged is added (the control)."""

    MOD = {"mod.toml": '[mod]\nid = "econ-half"\nversion = "1.0.0"\nname = "Half price"\n',
           "src/eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )\n" * 40}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.whole = self.tmp / "econ-half-1.0.0.rusemod"
        import zipfile
        with zipfile.ZipFile(self.whole, "w", zipfile.ZIP_DEFLATED) as z:
            for rel, text in self.MOD.items():
                z.writestr(rel, text)

    def tearDown(self):
        self._tmp.cleanup()

    def damaged(self, member: str) -> Path:
        import zipfile
        raw = bytearray(self.whole.read_bytes())
        with zipfile.ZipFile(self.whole) as z:
            info = z.getinfo(member)
        start = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
        raw[start + 3] ^= 0xFF
        out = self.tmp / ("damaged-" + member.replace("/", "-")) / self.whole.name
        out.parent.mkdir()
        out.write_bytes(bytes(raw))
        return out

    def test_a_damaged_byte_is_said_in_words_in_the_player_s_language(self):
        for member in ("mod.toml", "src/eco.rndf"):
            with self.subTest(member=member):
                api = LauncherApi(home=self.tmp / member.replace("/", "-") / "home", game_dir=self.tmp / "nowhere")
                api.set_pref("lang", "fr")
                with self.assertRaises(LauncherError) as caught:
                    page_api(api).add_mod(str(self.damaged(member)))
                self.assertEqual(str(caught.exception),
                                 f"econ-half-1.0.0.rusemod est abîmé : {member} qu'il contient ne se décompresse pas "
                                 f"en entier. Récupérez de nouveau le fichier (téléchargez-le de nouveau, ou demandez à "
                                 f"la personne qui l'a envoyé de le renvoyer).")
                self.assertEqual(api.library(), [])

    def test_control_the_file_undamaged_is_added(self):
        api = LauncherApi(home=self.tmp / "home", game_dir=self.tmp / "nowhere")
        api.set_pref("lang", "fr")
        res = page_api(api).add_mod(str(self.whole))
        self.assertEqual((res["mod"]["id"], res["replaced"]), ("econ-half", False))


if __name__ == "__main__":
    unittest.main()
