"""The All values tab (rusemod.values, the Studio's value_* calls; LittleGroove's raw value editor brought over): every
value of any object of the unit data, shown from the game's file, changed in the mod, and built, on a made-up game.
Also the mod file's spelling of any value (rusemod.rndf.literal) and what typed input becomes (rusemod.values.typed)."""
import re
import struct
import tempfile
import tomllib
import unittest
import uuid
from decimal import Decimal
from pathlib import Path

from fixtures import make_edat, make_ndf, val
from test_dic import make_dic
from rusemod import Edat, Ndf, values
from rusemod.build import build_pack, load_mod
from rusemod.dic import name_to_key
from rusemod.index import build_index
from rusemod.patch import Inline, ListV, MapV, Num, Obj, PairV, Raw, Ref, Text
from rusemod.play import Starter
from rusemod.rndf import literal, parse_value
from ruse_studio.api import StudioApi, StudioError
from ruse_studio.edits import Link, Literal, ModEdits

ROOT = Path(__file__).resolve().parents[1]
LANGS = {"us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"}
GUID = uuid.UUID("8a1f9c0e-35b2-4c55-9e7d-0d3e5f6a7b8c")


def num(kind, v):
    return Num(kind, Decimal(str(v)))


class Spelling(unittest.TestCase):
    """rusemod.rndf.literal: any value a mod file can hold, written so the reader gets the same value back."""

    def test_every_kind_reads_back_the_same(self):
        for v in (num("int32", -5), num("int8", 7), num("int16", -300), num("uint16", 60000), num("uint32", 4000000000),
                  num("int64", -2**40), num("bool", 1), num("bool", 0), Num("float32", Decimal(30)),
                  Num("float32", Decimal(struct.unpack("<f", struct.pack("<f", 0.1))[0])), num("float64", 0.25),
                  Text("string", "Unit_M4_Sherman"), Text("string", "it's"), Text("path", "GameData:/a b.png"),
                  Text("wstr", "Größe"), Text("key", "N_UNI_137"), Text("key", "0x00000000000ABCDE"),
                  Ref("$/GFX/Everything/Ammo_X"), Ref("$/GFX/Everything/Unit_A:Weapons[class=TTurret].Ammo"),
                  Ref("@TAmmunition[AmmunitionId=1120]"), Ref(None),
                  ListV([num("int32", 1), num("int32", 2)]), ListV([]), ListV([Ref("$/GFX/Everything/A"), Ref(None)]),
                  MapV([(Text("string", "day"), num("int32", 1)), (Text("string", "night"), num("int32", 0))]),
                  PairV(num("int32", 1), Num("float32", Decimal("2.5"))),
                  Raw(0x0B, struct.pack("<fff", 0, -0.7, 0.7)), Raw(0x0C, struct.pack("<ffff", 1, 2, 3, 4)),
                  Raw(0x21, struct.pack("<ff", 0.5, 1)), Raw(0x1F, struct.pack("<ii", 3, -4)),
                  Raw(0x0D, bytes([255, 230, 200, 128])), Raw(0x1A, GUID.bytes_le)):
            with self.subTest(v=v):
                text = literal(v)
                back = parse_value(text)
                if isinstance(v, Num) and v.kind == "float32":  # the shortest text that gives the same float32
                    self.assertEqual(back.kind, "float32")
                    self.assertEqual(struct.pack("<f", float(back.value)), struct.pack("<f", float(v.value)))
                elif isinstance(v, Num):
                    self.assertEqual((back.kind, float(back.value)), (v.kind, float(v.value)))
                else:  # vectors' floats come back as the float32s they were: the same bytes
                    self.assertEqual(back, v)

    def test_the_way_numbers_are_written(self):
        self.assertEqual(literal(Num("float32", Decimal(struct.unpack("<f", struct.pack("<f", 0.1))[0]))), "0.1")
        self.assertEqual(literal(Num("float32", Decimal(30))), "30.0")  # a bare 30 would read as a whole number
        self.assertEqual(literal(num("uint32", 7)), "uint32(7)")
        self.assertEqual(literal(num("float64", 2)), "f64(2.0)")
        self.assertEqual(literal(Text("key", "1ABC")), f"key(0x{name_to_key('1ABC'):016X})")  # not a name the reader takes
        self.assertEqual(literal(Raw(0x0D, bytes([1, 2, 3, 4]))), "RGBA[1, 2, 3, 4]")

    def test_what_a_mod_file_can_t_write(self):
        for v in (Inline(Obj("TPart")), Raw(0x14, b"\x02\0\0\0ab"), Num("float32", Decimal("NaN")),
                  Text("string", "both ' and \""), Text("string", "two\nlines"), Num("bool", Decimal(2)),
                  Ref("genglad/patchable/gfx/everything.cpp.gladndfbin#45058"), ListV([Inline(Obj("TPart"))])):
            with self.subTest(v=v), self.assertRaises(ValueError):
                literal(v)

    def test_the_studio_keeps_any_value_it_wrote(self):
        with tempfile.TemporaryDirectory() as tmp:
            edits = ModEdits(tmp)
            edits.set("$/GFX/Everything/A", "Pos", Literal("Float3[0.0, -0.7, 0.7]"))
            edits.set("$/GFX/Everything/A", "Name", Literal("'Unit_A2'"))
            edits.set("$/GFX/Everything/A", "Up", Literal("nil"))
            edits.set("$/GFX/Everything/A", "Price", [20, 25])
            again = ModEdits(tmp)
            self.assertEqual(again.of("$/GFX/Everything/A"), {"Pos": "Float3[0.0, -0.7, 0.7]", "Name": "'Unit_A2'",
                                                             "Up": "nil", "Price": [20, 25]})
            self.assertIsInstance(again.get("$/GFX/Everything/A", "Pos"), Literal)


class Typed(unittest.TestCase):
    """rusemod.values.typed: what the modder types, as the mod file's value, checked against the game's."""

    def typed(self, old, text, named=lambda a: a.startswith("$/GFX/Everything/"), game_to=None):
        return values.typed(old, text, "Prop", named, game_to)

    def test_numbers(self):
        self.assertEqual(self.typed(num("int32", 5), "7.5"), (8, False))  # half away from zero, as the build rounds
        self.assertEqual(self.typed(num("int32", 5), 5), (5, True))
        self.assertEqual(self.typed(Num("float32", Decimal(struct.unpack("<f", struct.pack("<f", 0.1))[0])), "0,1"),
                         (0.1, True))  # a decimal comma; the float32 the game has
        self.assertEqual(self.typed(num("bool", 1), False), (0, False))
        self.assertEqual(self.typed(num("bool", 0), "yes"), (1, False))
        for old, text in ((num("int8", 1), 300), (num("uint32", 1), -1), (num("int32", 1), "lots"), (num("bool", 1), 2)):
            with self.subTest(old=old, text=text), self.assertRaises(values.TypedError):
                self.typed(old, text)

    def test_texts_and_keys(self):
        self.assertEqual(self.typed(Text("string", "A"), "B's"), ('"B\'s"', False))  # the other quotes
        self.assertEqual(self.typed(Text("path", "a.png"), "b.png"), ("path('b.png')", False))
        self.assertEqual(self.typed(Text("wstr", "x"), "x"), ('wstr(\'x\')', True))
        self.assertEqual(self.typed(Text("key", "N_A"), " N_B "), ("key(N_B)", False))
        for text in ("way too long a key", "N-A", ""):
            with self.subTest(text=text), self.assertRaises(values.TypedError):
                self.typed(Text("key", "N_A"), text)
        with self.assertRaises(values.TypedError):
            self.typed(Text("string", "A"), "line\nbreak")

    def test_vectors_ids_and_lists(self):
        pos = Raw(0x0B, struct.pack("<fff", 0, -0.7, 0.7))
        self.assertEqual(self.typed(pos, "0, -0.7, 0.7"), ("Float3[0.0, -0.7, 0.7]", True))
        self.assertEqual(self.typed(pos, [1, 2, 3]), ("Float3[1.0, 2.0, 3.0]", False))
        self.assertEqual(self.typed(Raw(0x0D, bytes(4)), "255 128 0 255"), ("RGBA[255, 128, 0, 255]", False))
        for old, text in ((pos, "1, 2"), (Raw(0x0D, bytes(4)), "256, 0, 0, 0"), (Raw(0x1A, GUID.bytes_le), "nope")):
            with self.subTest(old=old, text=text), self.assertRaises(values.TypedError):
                self.typed(old, text)
        self.assertEqual(self.typed(Raw(0x1A, GUID.bytes_le), "{" + str(GUID).upper() + "}"), (f"GUID:{{{GUID}}}", True))
        prices = ListV([num("int32", 20), num("int32", 20)])
        self.assertEqual(self.typed(prices, "20, 25.4, 30"), ([20, 25, 30], False))  # longer, whole numbers
        self.assertEqual(self.typed(prices, [20, 20]), ([20, 20], True))
        self.assertEqual(self.typed(prices, ""), ("[]", False))
        self.assertEqual(self.typed(ListV([num("bool", 1), num("bool", 0)]), [0, 0]), ([0, 0], False))

    def test_links(self):
        self.assertEqual(self.typed(Ref("$/GFX/Everything/A"), "$/GFX/Everything/B"), ("$/GFX/Everything/B", False))
        self.assertIsInstance(self.typed(Ref(None), "$/GFX/Everything/B")[0], values.Linked)
        self.assertEqual(self.typed(Ref("$/GFX/Everything/A"), ""), ("nil", False))
        self.assertEqual(self.typed(Ref(None), "nil"), ("nil", True))
        # the game's link to a shared part, given back as the game index names it: the same link
        self.assertEqual(self.typed(Ref("x.ndfbin#12"), "$/GFX/Everything/A:Armor", game_to="$/GFX/Everything/A:Armor"),
                         ("$/GFX/Everything/A:Armor", True))
        with self.assertRaises(values.TypedError):
            self.typed(Ref(None), "$/Somewhere/Else")

    def test_lists_maps_and_pairs_as_written(self):
        tags = MapV([(Text("path", "a.png"), Num("float32", Decimal(1)))])
        new, same = self.typed(tags, "MAP [('b.png', 2), ('c.png', 3)]")
        self.assertEqual((new, same), ("MAP [(path('b.png'), 2.0), (path('c.png'), 3.0)]", False))  # the game's types
        self.assertIsInstance(new, values.Spelled)
        refs = ListV([Ref("$/GFX/Everything/A")])
        self.assertEqual(self.typed(refs, "[$/GFX/Everything/A, nil]"), ("[$/GFX/Everything/A, nil]", False))
        for old, text in ((tags, "[1, 2]"), (refs, "[$/Nowhere/X]"), (tags, "MAP [(1, 2"),
                          (ListV([Inline(Obj("TPart"))]), "[]")):
            with self.subTest(text=text), self.assertRaises(values.TypedError):
                self.typed(old, text)


# --- a made-up game: the unit data with every kind of value, another pack, and texts ---
CLASSES = ["TUnit", "TPart", "TOther"]
PROPS = [("Health", 0), ("DescriptorId", 0), ("Price", 0), ("Stick", 0), ("DebugName", 0), ("Model", 0), ("Wide", 0),
         ("NameInMenuToken", 0), ("Weapon", 0), ("ArmorDescriptor", 0), ("Upgrade", 0), ("Pos", 0), ("Col", 0),
         ("Tags", 0), ("Guid", 0), ("Blob", 0), ("Pair", 0), ("Size", 0), ("Big", 0), ("Other", 0), ("Speed", 1),
         ("Armour", 1), ("Value", 2), ("Part", 2)]
P = {name: i for i, (name, _c) in enumerate(PROPS)}
E = "$/GFX/Everything/"


def f32(v):
    return val(0x05, struct.pack("<f", v))


def i32(v):
    return val(0x02, struct.pack("<i", v))


def ref(i, cls):
    return val(0x09, struct.pack("<III", 0xBBBBBBBB, i, cls))


def everything() -> bytes:
    unit_a = [(P["Health"], f32(400)), (P["DescriptorId"], val(0x03, struct.pack("<I", 1143))),
              (P["Price"], val(0x11, struct.pack("<I", 2) + i32(20) + i32(20))), (P["Stick"], val(0x00, b"\x01")),
              (P["DebugName"], val(0x07, struct.pack("<I", 0))), (P["Model"], val(0x1C, struct.pack("<I", 1))),
              (P["Wide"], val(0x08, struct.pack("<I", 6) + "Abc".encode("utf-16-le"))),
              (P["NameInMenuToken"], val(0x1D, struct.pack("<Q", name_to_key("N_A")))), (P["Weapon"], ref(1, 1)),
              (P["ArmorDescriptor"], ref(2, 1)), (P["Upgrade"], ref(3, 0)),
              (P["Pos"], val(0x0B, struct.pack("<fff", 0, -0.7, 0.7))), (P["Col"], val(0x0D, bytes([255, 230, 200, 255]))),
              (P["Tags"], val(0x12, struct.pack("<I", 1) + val(0x07, struct.pack("<I", 2)) + i32(1))),
              (P["Guid"], val(0x1A, GUID.bytes_le)), (P["Blob"], val(0x14, struct.pack("<I", 2) + b"ab")),
              (P["Pair"], val(0x22, i32(1) + f32(2.5))), (P["Size"], val(0x1F, struct.pack("<ii", 3, 4))),
              (P["Big"], val(0x01, struct.pack("<b", 5))), (P["Other"], val(0x09, struct.pack("<II", 0xAAAAAAAA, 0)))]
    objects = [(0, unit_a),                                                                  # 0 Unit_A
               (1, [(P["Speed"], f32(10))]),                                                 # 1 its own part
               (1, [(P["Armour"], f32(5))]),                                                 # 2 shared by A and B
               (0, [(P["Health"], f32(300)), (P["ArmorDescriptor"], ref(2, 1)),              # 3 Unit_B
                    (P["NameInMenuToken"], val(0x1D, struct.pack("<Q", name_to_key("N_B"))))]),
               (2, [(P["Value"], i32(9))])]                                                  # 4 nothing leads to it
    return make_ndf(objects=objects, classes=CLASSES, props=PROPS, strings=["Unit_A", "GameData:/a.png", "day"],
                    exports={0: "GFX/Everything/Unit_A", 3: "GFX/Everything/Unit_B"},
                    imports=["GFX/Everything/Other_C"], topo=[0, 3])


def other(name: str) -> bytes:
    """A file with one named object and a part of it."""
    return make_ndf(objects=[(2, [(P["Value"], i32(7)), (P["Part"], ref(1, 1))]), (1, [(P["Speed"], f32(1))])],
                    classes=CLASSES, props=PROPS, exports={0: f"GFX/Everything/{name}"}, topo=[0])


GFX = "genglad\\patchable\\gfx\\"


def write_game(root: Path):
    rev = root / "Data" / "PC" / "190852"
    rev.mkdir(parents=True)
    (rev / "ZZ_GladPatchableWin.dat").write_bytes(make_edat([("dir", GFX, [
        ("file", "everything.cpp.gladndfbin", everything()),
        ("file", "everything_debuginfo.cpp.gladndfbin", everything()),
        ("file", "other.cpp.gladndfbin", other("Other_C"))])]))
    (rev / "ZZ_GladNotPatchableWin.dat").write_bytes(make_edat([("dir", "genglad\\notpatchable\\", [
        ("file", "outside.cpp.gladndfbin", other("Outside"))])]))
    (rev / "ZZ_Win.dat").write_bytes(make_edat([("dir", "genlocalisation\\ww2\\localisation\\translations\\", [
        ("dir", f"{lang}\\", [("file", "baseunite.dic", make_dic([(name_to_key(k), t) for k, t in texts.items()]))])
        for lang, texts in {"us": {"N_A": "ALPHA", "N_B": "BRAVO"}, "fr": {"N_A": "ALPHA FR"}}.items()])]))


class Words(unittest.TestCase):
    def test_every_word_in_every_language(self):
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        app = (ROOT / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        used = (set(re.findall(r"\bw\.((?:tip_)?values_\w+)", app)) | set(re.findall(r'"((?:tip_)?values_\w+)"', app))
                | {"values_tab", "tip_tab_values"})
        self.assertGreater(len(used), 60)
        for key in sorted(used):
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), LANGS)

    def test_the_item_details_words(self):
        """The Maps tab's box of the picked item's values (maps.js renderItemDetails): every word in every language."""
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        maps = (ROOT / "src" / "ruse_studio" / "ui" / "maps.js").read_text(encoding="utf-8")
        used = set(re.findall(r"\bw\.((?:tip_)?scen_item_\w+)", maps))
        self.assertGreater(len(used), 15)
        for key in sorted(used):
            with self.subTest(key=key):
                self.assertEqual(set(words[key]), LANGS)
        html = (ROOT / "src" / "ruse_studio" / "ui" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="scen-details"', html)
        self.assertIn("scenario_change: async", (ROOT / "src" / "ruse_studio" / "ui" / "fake-api.js").read_text(
            encoding="utf-8"))

    def test_the_tab_is_on_the_page(self):
        html = (ROOT / "src" / "ruse_studio" / "ui" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        fake = (ROOT / "src" / "ruse_studio" / "ui" / "fake-api.js").read_text(encoding="utf-8")
        for needle in ('id="tab-values"', 'id="values-view"', 'id="values-file"', 'id="values-find"',
                       'id="values-prop"', 'id="values-value"', 'id="values-list"', 'id="values-detail"'):
            self.assertIn(needle, html)
        for needle in ("function renderValues", "api().values_files(", "api().values_find(", "api().value_object(",
                       "api().value_edit(", "api().value_reset(", "api().value_links(", 'showView("values")',
                       '"tab-values": "tip_tab_values"'):
            self.assertIn(needle, app)
        for needle in ("values_files: async", "values_find: async", "value_object: async", "value_edit: async",
                       "value_reset: async", "value_links: async"):
            self.assertIn(needle, fake)


class Tab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.game = Path(cls.tmp.name, "game")
        write_game(cls.game)
        (cls.game / "RUSE.exe").write_bytes(b"MZ")
        cls.index = build_index(cls.game, Path(cls.tmp.name, "index.sqlite"), say=lambda line: None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(dir=self.tmp.name))
        starter = Starter(open_url=lambda url: None, start_game=lambda exe: None, steam_running=lambda: True,
                          wait=lambda s: None)
        self.api = StudioApi(index_path=self.index, game_dir=self.game, home=self.home, starter=starter,
                             instances=self.home / "copies")

    def rows(self, page):
        return {r["prop"]: r for r in page["rows"]}

    def test_the_files_and_looking_things_up(self):
        files = self.api.values_files()
        self.assertEqual(files["pack"], "ZZ_GladPatchableWin.dat")
        self.assertEqual(files["files"], [{"path": "genglad/patchable/gfx/everything.cpp.gladndfbin", "objects": 5},
                                          {"path": "genglad/patchable/gfx/other.cpp.gladndfbin", "objects": 2}])
        found = self.api.values_find(words="unit", lang="us")
        self.assertEqual([(o["address"], o["name"]) for o in found["objects"]],
                         [(E + "Unit_A", "ALPHA"), (E + "Unit_B", "BRAVO"), (E + "Unit_A:ArmorDescriptor", None),
                          (E + "Unit_A:Weapon", None)])  # named first; nothing from the debug-info copy
        self.assertEqual(found["total"], 4)
        self.assertEqual(self.api.values_find(words="unit", lang="base")["objects"][0]["name"], None)  # code names
        self.assertEqual([o["address"] for o in self.api.values_find(file="genglad/patchable/gfx/other.cpp.gladndfbin")[
            "objects"]], [E + "Other_C", E + "Other_C:Part"])
        by_value = self.api.values_find(prop="Health", value="300")
        self.assertEqual([(o["address"], o["match"]) for o in by_value["objects"]], [(E + "Unit_B", "Health = 300.0")])
        by_link = self.api.values_find(prop="Upgrade", value="Unit_B")
        self.assertEqual([o["address"] for o in by_link["objects"]], [E + "Unit_A"])
        self.assertEqual(self.api.values_find(words="Outside")["total"], 0)  # another pack: not the unit data

    def test_an_object_shows_every_value_it_has(self):
        page = self.api.value_object(E + "Unit_A", "us")
        self.assertEqual((page["class"], page["name"], page["file"], page["index"], page["named"], page["editable"],
                          page["why_not"], page["users"]),
                         ("TUnit", "ALPHA", "genglad/patchable/gfx/everything.cpp.gladndfbin", 0, True, False, "no_mod", 0))
        rows = self.rows(page)
        self.assertEqual(list(rows), [p for p, _c in PROPS[:20]])  # in the file's order
        self.assertEqual({p: (r["kind"], r["type"], r["value"]) for p, r in rows.items()}, {
            "Health": ("number", "float32", 400), "DescriptorId": ("number", "uint32", 1143),
            "Price": ("numbers", "int32", [20, 20]), "Stick": ("bool", "bool", 1),
            "DebugName": ("text", "string", "Unit_A"), "Model": ("text", "path", "GameData:/a.png"),
            "Wide": ("text", "wstr", "Abc"), "NameInMenuToken": ("key", "key", "N_A"),
            "Weapon": ("part", "TPart", None), "ArmorDescriptor": ("link", "reference", E + "Unit_A:ArmorDescriptor"),
            "Upgrade": ("link", "reference", E + "Unit_B"), "Pos": ("vector", "Float3", [0, -0.7, 0.7]),
            "Col": ("vector", "RGBA", [255, 230, 200, 255]), "Tags": ("map", "map", None),
            "Guid": ("guid", "guid", str(GUID)), "Blob": ("fixed", "0x14", "6 bytes"), "Pair": ("pair", "pair", None),
            "Size": ("vector", "Int2", [3, 4]), "Big": ("number", "int8", 5), "Other": ("link", "reference", E + "Other_C")})
        self.assertEqual(rows["Weapon"]["to"], E + "Unit_A:Weapon")
        self.assertEqual(rows["NameInMenuToken"]["words"], "ALPHA")
        self.assertEqual(rows["Tags"]["text"], "MAP [('day', 1)]")
        self.assertEqual(rows["Pair"]["text"], "(1, 2.5)")
        self.assertTrue(rows["DescriptorId"]["locked"])
        self.assertFalse(any(r["can"] for r in rows.values()))  # no mod yet
        self.assertEqual(self.api.value_object(E + "Unit_A", "fr")["name"], "ALPHA FR")
        self.assertEqual(self.rows(self.api.value_object(E + "Unit_A", "fr"))["Health"]["label"], "Health")

        part = self.api.value_object(E + "Unit_A:ArmorDescriptor", "us")
        self.assertEqual((part["shared"], part["owners"], part["owner"], part["users"]),
                         (True, 2, {"address": E + "Unit_A", "name": "ALPHA"}, 2))
        self.assertEqual([u["address"] for u in part["used_by"]], [E + "Unit_A", E + "Unit_B"])
        lost = self.api.values_find(words="TOther", file="genglad/patchable/gfx/everything.cpp.gladndfbin")["objects"]
        self.assertEqual(len(lost), 1)
        self.assertEqual(self.api.value_object(lost[0]["address"])["why_not"], "not_stable")
        self.assertEqual(self.api.value_object(E + "Outside")["why_not"], "outside")  # shown, not changed
        with self.assertRaises(StudioError):
            self.api.value_object(E + "Nowhere")

    def test_changes_are_saved_built_and_taken_back(self):
        with self.assertRaises(StudioError):
            self.api.value_edit(E + "Unit_A", "Health", 500)  # no mod to save it in yet
        self.api.new_mod("Raw")
        folder = self.home / "mods" / "raw"
        page = self.api.value_object(E + "Unit_A", "us")
        self.assertTrue(page["editable"])
        self.assertEqual({p for p, r in self.rows(page).items() if not r["can"]}, {"DescriptorId", "Weapon", "Blob"})
        edits = [("Health", 500), ("Price", "20, 25, 30"), ("Stick", False), ("DebugName", "Unit_A2"),
                 ("Model", "GameData:/b.png"), ("Wide", "Größe"), ("NameInMenuToken", "N_B"), ("Upgrade", E + "Other_C"),
                 ("Pos", [1, 2, 3]), ("Col", "1, 2, 3, 4"), ("Tags", "MAP [('night', 2)]"), ("Pair", "(3, 4.5)"),
                 ("Size", "5, 6"), ("Big", -3), ("Guid", "00000000-0000-0000-0000-000000000001"),
                 ("ArmorDescriptor", "")]
        for prop, value in edits:
            res = self.api.value_edit(E + "Unit_A", prop, value, "us")
            self.assertIsNotNone(self.rows(res["page"])[prop]["edited"], prop)
        with self.assertRaises(StudioError):
            self.api.value_edit(E + "Unit_A", "DescriptorId", 5)  # ids stay unique
        with self.assertRaises(StudioError):
            self.api.value_edit(E + "Unit_A", "Upgrade", E + "Nowhere")
        with self.assertRaises(StudioError):
            self.api.value_edit(E + "Unit_A", "Pos", "1, 2")
        self.api.value_edit(E + "Unit_A:ArmorDescriptor", "Armour", 6)  # a part both units share: changed for both
        rows = self.rows(self.api.value_object(E + "Unit_A", "us"))
        self.assertEqual(rows["NameInMenuToken"]["edited"], {"value": "N_B", "text": "key(N_B)", "words": "BRAVO"})
        self.assertEqual(rows["Pos"]["edited"]["value"], [1, 2, 3])
        self.assertEqual(rows["ArmorDescriptor"]["edited"], {"value": None, "text": "nil"})
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        self.assertIn(f"\npatch shared {E}Unit_A:ArmorDescriptor\n(\n    Armour = 6\n)\n", text)
        for line in ("ArmorDescriptor = nil", "Big = -3", "Col = RGBA[1, 2, 3, 4]", "DebugName = 'Unit_A2'",
                     "Guid = GUID:{00000000-0000-0000-0000-000000000001}", "Health = 500", "Model = path('GameData:/b.png')",
                     "NameInMenuToken = key(N_B)", "Pair = (3, 4.5)", "Pos = Float3[1.0, 2.0, 3.0]", "Price = [20, 25, 30]",
                     "Size = Int2[5, 6]", "Stick = 0", "Tags = MAP [('night', 2)]", f"Upgrade = {E}Other_C",
                     "Wide = wstr('Größe')"):
            self.assertIn(f"    {line}\n", text)

        arc = Edat((self.game / "Data" / "PC" / "190852" / "ZZ_GladPatchableWin.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)])
        self.assertEqual(result.errors, [])
        new = Edat(arc.to_bytes(result.changed))
        nd = Ndf(new.read(new.find("everything.cpp.gladndfbin")))
        got = {nd.prop_name(pi): v for pi, v in nd.objects[0].props}
        self.assertEqual(struct.unpack("<f", got["Health"].payload)[0], 500)
        self.assertEqual(got["Price"].payload, struct.pack("<I", 3) + i32(20) + i32(25) + i32(30))
        self.assertEqual(got["Stick"].payload, b"\0")
        self.assertEqual(nd.strings[struct.unpack("<I", got["DebugName"].payload)[0]], "Unit_A2")
        self.assertEqual((got["Model"].tc, nd.strings[struct.unpack("<I", got["Model"].payload)[0]]),
                         (0x1C, "GameData:/b.png"))
        self.assertEqual(got["Wide"].payload[4:].decode("utf-16-le"), "Größe")
        self.assertEqual(got["NameInMenuToken"].payload, struct.pack("<Q", name_to_key("N_B")))
        self.assertEqual(got["Pos"].payload, struct.pack("<fff", 1, 2, 3))
        self.assertEqual(got["Col"].payload, bytes([1, 2, 3, 4]))
        self.assertEqual(got["Size"].payload, struct.pack("<ii", 5, 6))
        self.assertEqual(got["Big"].payload, struct.pack("<b", -3))
        self.assertEqual(got["Guid"].payload, uuid.UUID(int=1).bytes_le)
        self.assertEqual(got["Pair"].payload, i32(3) + f32(4.5))
        self.assertEqual(got["ArmorDescriptor"].payload, struct.pack("<III", 0xBBBBBBBB, 0xFFFFFFFF, 0xFFFFFFFF))
        sub, idx = struct.unpack_from("<II", got["Upgrade"].payload)
        self.assertEqual((sub, nd.imports[idx]), (0xAAAAAAAA, E + "Other_C"))  # a named object of another file
        self.assertEqual(got["Blob"].payload, struct.pack("<I", 2) + b"ab")  # untouched values keep their bytes
        armour = {nd.prop_name(pi): v for pi, v in nd.objects[2].props}["Armour"]
        self.assertEqual(struct.unpack("<f", armour.payload)[0], 6)

        # the game's own value again takes the change out; so does "Game's value"
        self.assertIsNone(self.rows(self.api.value_edit(E + "Unit_A", "Health", "400", "us")["page"])["Health"]["edited"])
        self.assertIsNone(self.rows(self.api.value_reset(E + "Unit_A", "Pos", "us")["page"])["Pos"]["edited"])
        self.assertIsNone(self.rows(self.api.value_edit(E + "Unit_A", "Price", [20, 20])["page"])["Price"]["edited"])
        text = (folder / "src" / "studio.rndf").read_text(encoding="utf-8")
        for gone in ("Health =", "Pos =", "Price ="):
            self.assertNotIn(gone, text)

    def test_links_offered_and_allowed(self):
        self.api.new_mod("Links")
        offered = self.api.value_links(E + "Unit_A", "Upgrade", "", "us")
        self.assertEqual((offered["class"], [o["address"] for o in offered["objects"]]),
                         ("TUnit", [E + "Unit_A", E + "Unit_B"]))
        self.assertEqual(offered["objects"][1]["name"], "BRAVO")
        armour = self.api.value_links(E + "Unit_B", "ArmorDescriptor", "", "us")  # a part: parts of its file too
        self.assertEqual([o["address"] for o in armour["objects"]], [E + "Unit_A:ArmorDescriptor", E + "Unit_A:Weapon"])
        self.api.value_edit(E + "Unit_B", "ArmorDescriptor", E + "Unit_A:Weapon")  # a part of the same file: fine
        page = self.api.value_edit(E + "Unit_B", "ArmorDescriptor", E + "Unit_A:ArmorDescriptor")["page"]
        self.assertIsNone(self.rows(page)["ArmorDescriptor"]["edited"])  # the game's own link again
        with self.assertRaises(StudioError):  # a part of another file can't be linked to (the build couldn't)
            self.api.value_edit(E + "Unit_A", "Upgrade", E + "Other_C:Part")
        self.api.value_edit(E + "Unit_A", "Upgrade", E + "Other_C")  # its named object can

    def test_the_words_a_key_shows(self):
        """LittleGroove's "Save text": the words of one of the game's texts changed in the mod, every language written
        so a language left alone keeps the game's words, and built into the game's text table."""
        with self.assertRaises(StudioError):
            self.api.value_words_set("N_A", {"us": "ANT"})  # no mod to save it in yet
        self.api.new_mod("Words")
        folder = self.home / "mods" / "words"
        now = self.api.value_words("N_A")
        self.assertEqual(now["table"], "baseunite")
        self.assertEqual({w["lang"]: (w["game"], w["mine"]) for w in now["words"] if w["game"]},
                         {"us": ("ALPHA", None), "fr": ("ALPHA FR", None)})
        res = self.api.value_words_set("N_A", {"fr": "FOURMI"})
        self.assertEqual({w["lang"]: w["mine"] for w in res["words"] if w["mine"]}, {"us": "ALPHA", "fr": "FOURMI"})
        csv_file = folder / "text" / "studio-words.baseunite.csv"
        self.assertEqual(csv_file.read_text(encoding="utf-8").splitlines(),
                         ["key,us,fr,ger,ita,spa,pol,ru,cz,jpn,sc", "game:N_A,ALPHA,FOURMI,,,,,,,,"])
        rows = self.rows(self.api.value_object(E + "Unit_A", "fr"))
        self.assertEqual((rows["NameInMenuToken"]["words"], rows["NameInMenuToken"]["words_mine"]), ("ALPHA FR", "FOURMI"))
        self.assertIsNone(self.rows(self.api.value_object(E + "Unit_A", "us"))["NameInMenuToken"]["words_mine"])
        with self.assertRaises(StudioError):  # a key the game has no text for
            self.api.value_words_set("NOPE", {"us": "x"})
        with self.assertRaises(StudioError):
            self.api.value_words_set("N_A", {"us": "two\nlines"})

        rev = self.game / "Data" / "PC" / "190852"
        arc, text_arc = Edat((rev / "ZZ_GladPatchableWin.dat").read_bytes()), Edat((rev / "ZZ_Win.dat").read_bytes())
        result = build_pack(arc, [load_mod(folder)], text_arc=text_arc)
        self.assertEqual(result.errors, [])
        from rusemod.dic import Dic
        changed = {k.lower(): v for k, v in result.text_changed.items()}
        fr = Dic(changed["genlocalisation\\ww2\\localisation\\translations\\fr\\baseunite.dic"])
        self.assertEqual(fr.text(name_to_key("N_A")), "FOURMI")
        self.assertNotIn("genlocalisation\\ww2\\localisation\\translations\\us\\baseunite.dic", changed)  # unchanged

        back = self.api.value_words_set("N_A", {"fr": "ALPHA FR"})  # the game's words again: the row goes
        self.assertEqual([w for w in back["words"] if w["mine"]], [])
        self.assertFalse(csv_file.exists())

    def test_the_units_tab_shows_a_change_made_here(self):
        self.api.new_mod("Both")
        self.api.value_edit(E + "Unit_A", "Price", "")  # an emptied list: the mod's own text
        unit = self.api.unit(E + "Unit_A", "us")
        row = next(r for g in unit["groups"] for r in g["rows"] if r["prop"] == "Price")
        self.assertEqual((row["values"], row["editable"], row["edited"]), (["[]"], False, None))
        self.assertTrue(unit["in_game"])


if __name__ == "__main__":
    unittest.main()
