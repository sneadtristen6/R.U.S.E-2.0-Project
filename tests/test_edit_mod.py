"""Edit an installed mod (the Studio's StudioApi.installed_mods / edit_installed; the owner, 2026-10-10): the Launcher's
mods open in the Studio with everything in them. Yours opens its project; anyone else's becomes a copy of your own
under a name of its own, never the original's, which Export and the Launcher refuse too (rusemod.package.edit_problem).
A mod made the older way (an .rmod) can't be opened yet."""
import tempfile
import tomllib
import unittest
from pathlib import Path

from rusemod import package
from rusemod.library import Library, LibraryError
from ruse_studio.api import StudioApi, StudioError

ROOT = Path(__file__).resolve().parents[1]
LANGS = {"us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"}
KEYS = ("edit_installed", "edit_title", "edit_lead", "edit_none", "edit_has_units", "edit_has_maps", "edit_by",
        "edit_older", "edit_open", "tip_edit_open", "tip_edit_copy", "edit_yours", "edit_copy_lead", "edit_someone",
        "edit_copy_name", "edit_copy_go", "only_mod", "tip_only_mod")


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def manifest(folder: Path, mod_id: str, name: str, version: str = "1.0.0", authors=("nickgit",), extra: str = ""):
    names = ", ".join(f'"{a}"' for a in authors)
    write(folder / "mod.toml", f'[mod]\nid = "{mod_id}"\nname = "{name}"\nversion = "{version}"\nauthors = [{names}]\n'
                               f'description = "Twenty-two new units."\n{extra}')


class EditInstalled(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name, "home")
        lib = self.home / "library"
        # someone else's Studio mod: unit changes, a painted picture
        self.field = lib / "r-u-s-e-field-manual-v1"
        manifest(self.field, "r-u-s-e-field-manual-v1", "R.U.S.E. Field Manual")
        write(self.field / "src" / "studio.rndf", "# the Studio's changes\n")
        (self.field / "files" / "replace").mkdir(parents=True)
        (self.field / "files" / "replace" / "a.png").write_bytes(b"\x89PNG fake")
        write(self.field / "cache" / "junk.bin", "never copied")
        # someone else's map-only mod
        self.mapmod = lib / "winter-maps"
        manifest(self.mapmod, "winter-maps", "Winter Maps", authors=("Cascade",))
        write(self.mapmod / "maps" / "Winter" / "map.toml", 'copy_of = "Dday"\n')
        # one made the older way
        self.old = lib / "airfield-capacity"
        manifest(self.old, "airfield-capacity", "Airfield Capacity", extra='\n[rmod]\nfile = "Airfield.rmod"\n')
        (self.old / "Airfield.rmod").write_bytes(b"RMOD")
        # one of yours: exported from this Studio's project
        self.project = self.home / "mods" / "abrams"
        manifest(self.project, "abrams", "Abrams", authors=("Tristen",))
        write(self.project / "src" / "studio.rndf", "# mine\n")
        manifest(lib / "abrams", "abrams", "Abrams", authors=("Tristen",))
        write(lib / "abrams" / "src" / "studio.rndf", "# mine, exported\n")
        self.api = StudioApi(index_path=Path(self.tmp.name, "none.sqlite"), find=lambda: None, home=self.home)

    def test_the_list_says_what_each_mod_is(self):
        rows = {m["id"]: m for m in self.api.installed_mods()["mods"]}
        self.assertEqual(set(rows), {"r-u-s-e-field-manual-v1", "winter-maps", "airfield-capacity", "abrams"})
        field = rows["r-u-s-e-field-manual-v1"]
        self.assertEqual((field["name"], field["author"], field["yours"], field["older"], field["units"], field["maps"]),
                         ("R.U.S.E. Field Manual", "nickgit", "", False, True, False))
        self.assertEqual((rows["winter-maps"]["units"], rows["winter-maps"]["maps"]), (False, True))
        self.assertTrue(rows["airfield-capacity"]["older"])
        self.assertEqual(rows["abrams"]["yours"], str(self.project))

    def test_someone_else_s_mod_needs_a_name_of_its_own(self):
        for bad in ("", "   ", "R.U.S.E. Field Manual", "r.u.s.e.  field   MANUAL", "Winter Maps"):
            with self.subTest(name=bad):
                with self.assertRaises(StudioError):
                    self.api.edit_installed("r-u-s-e-field-manual-v1", bad)
        self.assertFalse((self.home / "mods" / "r-u-s-e-field-manual-v1").exists())
        self.assertEqual([p.name for p in (self.home / "mods").iterdir()], ["abrams"])  # nothing half made

    def test_the_copy_holds_everything_and_says_where_it_came_from(self):
        before = (self.field / "mod.toml").read_bytes()
        res = self.api.edit_installed("r-u-s-e-field-manual-v1", "Field Manual Roundels")
        copy = Path(res["path"])
        self.assertEqual(copy, self.home / "mods" / "field-manual-roundels")
        self.assertTrue(res["copied"])
        self.assertEqual((res["units"], res["maps"]), (True, False))
        data = tomllib.loads((copy / "mod.toml").read_text(encoding="utf-8"))
        self.assertEqual((data["mod"]["id"], data["mod"]["name"]), ("field-manual-roundels", "Field Manual Roundels"))
        self.assertEqual(data["edited_from"], {"id": "r-u-s-e-field-manual-v1", "name": "R.U.S.E. Field Manual",
                                               "version": "1.0.0", "authors": ["nickgit"]})
        self.assertEqual((copy / "src" / "studio.rndf").read_text(encoding="utf-8"), "# the Studio's changes\n")
        self.assertEqual((copy / "files" / "replace" / "a.png").read_bytes(), b"\x89PNG fake")
        self.assertFalse((copy / "cache").exists())  # only what the mod's package holds
        self.assertEqual((self.field / "mod.toml").read_bytes(), before)  # the Launcher's copy is untouched
        self.assertEqual(res["mod"]["current"], str(copy))  # it's the Units tab's mod now
        self.assertEqual(package.edit_problem(copy), "")
        # the original is still someone else's: the copy has an id of its own, in the Launcher once it's exported
        rows = {m["id"]: m for m in self.api.installed_mods()["mods"]}
        self.assertEqual(rows["r-u-s-e-field-manual-v1"]["yours"], "")
        self.assertNotIn("field-manual-roundels", rows)

    def test_a_maps_only_mod_opens_in_the_maps_tab(self):
        res = self.api.edit_installed("winter-maps", "Winter Maps Snowier")
        copy = Path(res["path"])
        self.assertEqual(copy.parent, self.home / "maps")
        self.assertEqual(res["map"]["current"], str(copy))
        self.assertIsNone(res["mod"]["current"])
        self.assertTrue((copy / "maps" / "Winter" / "map.toml").is_file())

    def test_yours_opens_its_project(self):
        res = self.api.edit_installed("abrams")
        self.assertFalse(res["copied"])
        self.assertEqual(res["path"], str(self.project))
        self.assertEqual(res["mod"]["current"], str(self.project))
        self.assertEqual(sorted(p.name for p in (self.home / "mods").iterdir()), ["abrams"])

    def test_the_older_way_can_t_be_opened_yet(self):
        with self.assertRaisesRegex(StudioError, "older way"):
            self.api.edit_installed("airfield-capacity", "Airfield Mine")
        with self.assertRaisesRegex(StudioError, "isn't installed"):
            self.api.edit_installed("gone", "Gone")

    def test_export_refuses_an_edit_put_back_to_the_original_s_name(self):
        copy = Path(self.api.edit_installed("r-u-s-e-field-manual-v1", "Field Manual Roundels")["path"])
        package.update_manifest(copy, mod={"name": "R.U.S.E. Field Manual"})
        with self.assertRaisesRegex(StudioError, "can't carry that mod's name or id"):
            self.api.export_mod("1.0.1")
        package.update_manifest(copy, mod={"name": "Field Manual Roundels", "id": "r-u-s-e-field-manual-v1"})
        with self.assertRaisesRegex(StudioError, "can't carry that mod's name or id"):
            self.api.export_mod("1.0.1")

    def test_the_launcher_refuses_an_edit_under_the_original_s_name(self):
        edit = Path(self.tmp.name, "an-edit")
        manifest(edit, "field-manual-mine", "R.U.S.E. Field Manual",
                 extra='\n[edited_from]\nid = "r-u-s-e-field-manual-v1"\nname = "R.U.S.E. Field Manual"\n')
        with self.assertRaisesRegex(LibraryError, "can't carry that mod's name or id"):
            Library(self.home / "library").add(edit)
        package.update_manifest(edit, mod={"name": "Field Manual Mine"})
        info, replaced = Library(self.home / "library").add(edit)
        self.assertEqual((info["id"], replaced), ("field-manual-mine", False))

    def test_names_compare_without_case_or_spaces(self):
        self.assertEqual(package.name_key("  R.U.S.E.   Field manual "), package.name_key("r.u.s.e. FIELD MANUAL"))
        self.assertNotEqual(package.name_key("Field Manual"), package.name_key("Field Manual 2"))


class Page(unittest.TestCase):
    def test_the_words_are_in_every_language(self):
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        for key in KEYS:
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), LANGS)

    def test_the_menu_and_its_dialog_are_on_the_page(self):
        ui = ROOT / "src" / "ruse_studio" / "ui"
        html, app = (ui / "index.html").read_text(encoding="utf-8"), (ui / "app.js").read_text(encoding="utf-8")
        fake = (ui / "fake-api.js").read_text(encoding="utf-8")
        for needle in ('id="edit-mods"', 'id="edit-mods-list"', 'id="edit-mods-close"'):
            self.assertIn(needle, html)
        for needle in ("function openEditMods", "api().installed_mods(", "api().edit_installed(", "w.edit_installed",
                       "state.onlyMod"):
            self.assertIn(needle, app)
        for needle in ("installed_mods: async", "edit_installed: async"):
            self.assertIn(needle, fake)


if __name__ == "__main__":
    unittest.main()
