"""Scenarios: a player making new units in the RUSE Studio (the owner, 2026-11-13 overnight: "Usual and unusual
situations. Player can find themselves in when making new mods in our apps"). New unit… on the page of a unit of each
kind the game has (a tank, an infantry squad, a plane, artillery, an anti-tank gun, a building); names in every script
the apps' languages use and the odd ones; a price of 0, negative, decimal, huge or not a number; another nation's build
menu, a nation with none; a group of 6 and a seventh, a building's tenth group and an eleventh; a copy of an upgrade, in
its own menu and in another nation's; a copy of a copy; the same name twice. Each call is made as the page makes it
(newUnitForm in ui/app.js: new_unit(address, name trimmed, Number(price), nation or -1, factory or -1, false, group or
null)). After each: what the page says, in every language; the mod's files; the mod built on the made-up game.

Each test marked expectedFailure shows a finding (its number in the comment above it; the agent's report lists them);
it passes once the finding is mended."""
import unittest
from pathlib import Path

from rusemod import menugroups
from test_scenarios_units_base import (A1, ARMOR_GER, ARMOR_US, CODE_NAME, E, G1, G2, GAME_LANGS, GS, H1, L1, LANGS,
                                       M1, M2, P1, P2, PYTHON_WORDS, S1, T1, U, Player, Refused)

KINDS = (("tank", M1, "ground"), ("squad", S1, "infantry"), ("plane", P1, "air"), ("artillery", A1, "ground"),
         ("anti-tank gun", T1, "ground"), ("building", ARMOR_US, "buildings"))
UNIT_NAMES = {"us": "Super Sherman", "fr": "Char léger à l'été", "ger": "Königstiger Ü", "ita": "Carro più veloce",
              "spa": "Tanque ñandú", "pol": "Czołg źdźbło", "ru": "Тигр Т-34", "cz": "Tank čeřich",
              "jpn": "九七式中戦車", "sc": "虎式坦克", "fa": "تانک سنگین"}


class NewUnitOfEveryKind(Player):
    """New unit… on the page of each kind of unit and on a building's."""

    def new(self, source, name, price=55, nation=-1, factory=-1, group=None, lang="us"):
        return self.call("new_unit", source, name.strip(), price, nation, factory, False, group, lang=lang)

    def test_a_copy_of_each_kind_is_listed_opened_and_built(self):
        folder = self.mod("Every kind")
        made = {}
        for label, source, kind in KINDS:
            with self.subTest(kind=label):
                res = self.new(source, f"New {label}")
                made[label] = res["address"]
                prefix = E + ("Descriptor_Building_" if kind == "buildings" else "Descriptor_Unit_")
                self.assertTrue(res["address"].startswith(prefix), res["address"])
                listed = {u["address"]: u for u in self.call("units", "us")["units"]}
                u = listed[res["address"]]
                self.assertEqual((u["name"], u["kind"], u["nation"], u["new"], u["source"]),
                                 (f"New {label}", kind, 0, True, source))
                page = self.call("unit", res["address"], "fr")
                self.assertEqual((page["name"], page["new"]["source"]), (f"New {label}", source))
                self.assertFalse(page["can_copy"])                              # a copy of a copy isn't offered
        errors, ndf, texts = self.build(folder)
        self.assertEqual(errors, [])
        for label, address in made.items():
            with self.subTest(built=label):
                self.assertEqual(self.value(ndf, address, "ProductionPrice").int_list(), [55] * 5)
                self.assertEqual(self.built_names(ndf, texts, address), {lang: f"New {label}" for lang in GAME_LANGS})

    def test_a_name_in_every_script_is_the_name_in_game_in_every_language(self):
        folder = self.mod("Names")
        made = {}
        sources = [M1, L1, H1, T1, A1, S1, P1]   # (a line holds 6: the copies spread over seven)
        for k, (lang, name) in enumerate(UNIT_NAMES.items()):
            made[lang] = self.new(sources[k % len(sources)], name)["address"]
        # Latin names with their accents folded (ł has no plain form: left out); a name with no Latin letter gets a
        # number; a Russian name keeps only its digits
        self.assertEqual((made["us"], made["fr"], made["ger"], made["pol"]),
                         (U + "Super_Sherman", U + "Char_leger_a_l_ete", U + "Konigstiger_U", U + "Czog_zdzbo"))
        self.assertEqual(made["ru"], U + "34")
        self.assertEqual([made[k] for k in ("jpn", "sc", "fa")], [U + "New_1", U + "New_2", U + "New_3"])
        listed = {u["address"]: u["name"] for u in self.call("units", "jpn")["units"]}
        for lang, name in UNIT_NAMES.items():
            self.assertEqual(listed[made[lang]], name)
            found = [u["address"] for u in self.call("units", lang, "all", -1, name)["units"]]
            self.assertIn(made[lang], found, f"searching {name!r}")
        errors, ndf, texts = self.build(folder)
        self.assertEqual(errors, [])
        for lang, name in UNIT_NAMES.items():
            with self.subTest(lang=lang):
                self.assertEqual(self.built_names(ndf, texts, made[lang]), {g: name for g in GAME_LANGS})

    def test_odd_names(self):
        """The names on copies of the USA's Armor Base (a building: no group to fill) and of a tank."""
        folder = self.mod("Odd names")
        odd = ["X" * 60, "戦" * 60, 'Tiger\'s "Ace" <1944>, 50% & more', "!!!", "CON", "NUL", "AUX", "COM1", "Tiger.",
               "Panther 🙂", "𠮷野家の戦車", "a,b;c\td", "=1+1", "Tiger\\Bear/Wolf"]
        made = {}
        for name in odd:
            with self.subTest(name=name):
                made[name] = self.new(ARMOR_US, name)["address"]
        b = E + "Descriptor_Building_"
        self.assertEqual((made["!!!"], made["Tiger."], made["CON"], made["Panther 🙂"], made["Tiger\\Bear/Wolf"]),
                         (b + "New_2", b + "Tiger", b + "CON", b + "Panther", b + "Tiger_Bear_Wolf"))
        tank = self.new(M1, "Sherman 🙂 𠮷")["address"]
        made["Sherman 🙂 𠮷"] = tank
        errors, ndf, texts = self.build(folder)
        self.assertEqual(errors, [])
        for name, address in made.items():
            with self.subTest(built=name):
                self.assertEqual(self.built_names(ndf, texts, address), {g: name for g in GAME_LANGS})

    def test_no_name(self):
        self.mod("No name")
        for name in ("", "   "):
            said = self.refusal("new_unit", M1, name.strip(), 40, -1, -1, False, None)
            self.assertEqual(said["us"], "Give the new unit a name.")
            self.assertEqual(self.english_left(said), [])

    def test_the_same_name_twice_and_a_game_units_name(self):
        """The same name again (or one written differently that makes the same address, Tiger-II after Tiger II, or
        the end of a game unit's address, M1) is refused, nothing made; a name with no Latin letter twice is two
        units of that name (two addresses)."""
        folder = self.mod("Twice")
        first = self.new(H1, "Tiger II")["address"]
        before = self.files(folder)
        for name in ("Tiger II", "Tiger-II", "Tiger  II!", "M1"):
            with self.subTest(name=name):
                said = self.refusal("new_unit", H1, name, 40, -1, -1, False, None)
                self.assertEqual(self.english_left(said), [])
        self.assertEqual(self.files(folder), before)
        self.assertEqual(self.new(H1, "虎")["address"], U + "New_1")
        self.assertEqual(self.new(H1, "虎")["address"], U + "New_2")
        self.assertEqual(self.build(folder)[0], [])
        self.assertEqual(first, U + "Tiger_II")

    def test_a_name_differing_only_in_capitals_is_refused_as_taken(self):
        """tiger ii after Tiger II, m1 beside the game's M1: refused as the same name is (U-8's mend); the board's copy
        of another nation's unit takes the next free address instead, as for the same name."""
        folder = self.mod("Case")
        self.new(H1, "Tiger II")
        for source, name in ((H1, "tiger ii"), (L1, "m1")):
            with self.subTest(name=name):
                self.assertEqual(self.english_left(self.refusal("new_unit", source, name, 40, -1, -1, False, None)), [])
        self.new(H1, "g one")
        self.assertEqual(self.call("board_put", 0, 10, G1, "", None, "new", "us")["made"], U + "G_One_2")
        self.assertEqual(self.build(folder)[0], [])

    # U-8 (mended by the PROPOSED FIX commit after these tests: before it, two units whose addresses differ only in
    # capitals, Tiger II and tiger ii, m1 and the game's M1, were both made and shared every file of their own on
    # Windows, whose file names don't tell capitals apart, and deleting tiger ii took Tiger II's card and model). The
    # test holds for either mend: tiger ii refused, or Delete taking only its own files.
    def test_deleting_tiger_ii_leaves_tiger_IIs_own_files(self):
        folder = self.mod("Case files")
        big = self.new(H1, "Tiger II")["address"]
        tail = big.rsplit("/", 1)[-1]
        card = folder / "files" / "cards" / f"{tail}.png"
        model = folder / "files" / "models" / f"{tail}.glb"
        for f, data in ((card, b"Tiger II's own card"), (model, b"Tiger II's own model")):
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        try:
            small = self.new(H1, "tiger ii")["address"]
        except Refused as r:   # refused: then in words, in every language
            small = None
            self.assertEqual(self.english_left(self.refusal("new_unit", H1, "tiger ii", 40, -1, -1, False, None)), [],
                             r.text)
        if small:
            self.call("delete_unit", small, None)
        self.assertEqual([f.is_file() for f in (card, model)], [True, True], "deleting tiger ii took Tiger II's files")
        self.assertEqual([card.read_bytes(), model.read_bytes()], [b"Tiger II's own card", b"Tiger II's own model"])

    # U-4: the refusal of a name already taken names the game's code name and quotes the name the Python way:
    # "There's already a unit called Descriptor_Unit_Tiger_II (from 'Tiger II'). Pick another name."
    @unittest.expectedFailure
    def test_the_same_name_twice_is_refused_in_plain_words(self):
        self.mod("Twice plainly")
        self.new(H1, "Tiger II")
        for lang, text in self.refusal("new_unit", H1, "Tiger II", 40, -1, -1, False, None).items():
            with self.subTest(lang=lang):
                self.assert_plain(text)
                self.assertNotIn("'Tiger II'", text)

    def test_prices(self):
        """The New unit form takes a whole number from 0 (its box: min 0, step 1; the browser stops a negative or a
        decimal one before it's sent); the Studio itself takes any number that fits the game's value, rounded."""
        folder = self.mod("Prices")
        for price, built in ((0, 0), (40.5, 41), (40.4, 40), (-10, -10), (2147483647, 2147483647)):
            with self.subTest(price=price):
                res = self.new(T1, f"Price {price}", price)
                errors, ndf, _ = self.build(folder)
                self.assertEqual(errors, [])
                self.assertEqual(self.value(ndf, res["address"], "ProductionPrice").int_list(), [built] * 5)
        for price in (2147483648, 1e10, 1e20):   # (the box takes these: Number("1e10"))
            with self.subTest(price=price):
                said = self.refusal("new_unit", T1, f"Too much {price}", price, -1, -1, False, None)
                self.assertEqual(self.english_left(said), [])
        for price in ("40", True, None, [40]):   # (never from the page: it sends Number(box), and only a finite one)
            with self.subTest(price=price):
                said = self.refusal("new_unit", T1, "Not a number", price, -1, -1, False, None)
                self.assertEqual(said["us"], "Price: one number, used for every battle date.")

    # U-5: a price too big for the game is refused with the value's code name and the int32 range:
    # "ProductionPrice: 10000000000 doesn't fit (it must be -2147483648 to 2147483647)"
    @unittest.expectedFailure
    def test_a_price_too_big_is_refused_in_plain_words(self):
        self.mod("Too big")
        for lang, text in self.refusal("new_unit", T1, "Too much", 1e10, -1, -1, False, None).items():
            with self.subTest(lang=lang):
                self.assertNotIn("ProductionPrice", text)
                self.assertNotIn("-2147483648", text)


class AnotherNationsMenu(Player):
    """New unit…'s "another nation's build menu": the nation and building picked (the form's selects)."""

    def new(self, source, name, nation=-1, factory=-1, group=None):
        return self.call("new_unit", source, name, 40, nation, factory, False, group)

    def test_a_tank_and_a_squad_in_germanys_menus(self):
        folder = self.mod("Lend-Lease")
        menus = {m["nation"]: [f["factory"] for f in m["factories"]] for m in self.call("menus", "us")["nations"]}
        self.assertEqual((menus[0], menus[1], menus[5]), ([8, 9, 10, 11, 13], [8, 10], []))
        tank = self.new(M1, "Lend Tank", 1, 10)["address"]
        squad = self.new(S1, "Lend Squad", 1, 8)["address"]
        listed = {u["address"]: u for u in self.call("units", "us", "all", 1)["units"]}
        self.assertEqual((listed[tank]["nation"], listed[squad]["nation"]), (1, 1))
        board = self.call("board", 1, "us")
        row = next(r for r in board["rows"] if r["factory"] == 10)
        self.assertIn(tank, next(g for g in row["groups"] if g["root"] == G1)["units"])   # G1's line: a medium tank
        errors, ndf, _ = self.build(folder)
        self.assertEqual(errors, [])
        self.assertEqual((self.value(ndf, tank, "Nationalite").scalar(), self.value(ndf, tank, "Factory").scalar()),
                         (1, 10))

    def test_a_nation_with_no_build_menu(self):
        """The form lists every nation; one with no build menus has an empty building list, and Create sends
        factory Number("") = 0."""
        self.mod("Nowhere")
        said = self.refusal("new_unit", M1, "Nowhere Tank", 40, 5, 0, False, None)
        self.assertEqual(self.english_left(said), [])
        for text in said.values():
            self.assertIsNone(PYTHON_WORDS.search(text), text)

    # U-6: that refusal names the nation and the building by their numbers: "No build menu for nation 5 and factory 0:
    # pick one of the menus the game has" (the page's select says "USSR")
    @unittest.expectedFailure
    def test_a_nation_with_no_build_menu_is_refused_naming_the_nation(self):
        self.mod("Nowhere named")
        said = self.refusal("new_unit", M1, "Nowhere Tank", 40, 5, 0, False, None)
        self.assertIn("USSR", said["us"])

    def test_a_squad_in_an_armor_base(self):
        """The form offers every building of the nation picked, the Armor Base for a squad too: the Studio makes it, in a
        group of its own there (no line of its kind). What the game does with a squad from an Armor Base isn't known."""
        folder = self.mod("Odd menu")
        squad = self.new(S1, "Tank Riders", 0, 10)["address"]
        row = next(r for r in self.call("board", 0, "us")["rows"] if r["factory"] == 10)
        self.assertEqual(next(g for g in row["groups"] if squad in g["units"])["units"], [squad])
        self.assertEqual(self.build(folder)[0], [])

    def test_a_building_copied_into_another_nations_menu(self):
        """A building's page has the same New unit… form, "another nation's build menu" too: a copy of the USA's
        Armor Base for Germany's armor menu."""
        folder = self.mod("Building elsewhere")
        res = self.new(ARMOR_US, "German Armor Base", 1, 10)
        errors, _ndf, _ = self.build(folder)
        self.assertEqual(errors, [], (folder / "src" / "studio.rndf").read_text(encoding="utf-8"))
        self.assertTrue(res["address"].startswith(E + "Descriptor_Building_"))

    def test_a_plane_in_a_nation_without_an_airfield(self):
        """Germany has no airfield in this game: the form doesn't offer one (menus); sent anyway, it's refused."""
        self.mod("No airfield")
        said = self.refusal("new_unit", P1, "Luftwaffe", 40, 1, 9, False, None)
        self.assertEqual(self.english_left(said), [])


class GroupsOfSix(Player):
    """A build list's group holds at most 6 (the owner, 2026-10-31: a 7th "Refuse it"); a building at most 10 groups."""

    def fill_m1(self):
        """M1's line (M1, M2) filled to 6 with copies of M1 (medium tanks go in it)."""
        folder = self.mod("Six")
        made = [self.call("new_unit", M1, f"Medium {k}", 40, -1, -1, False, None)["address"] for k in range(1, 5)]
        g = next(g for g in self.groups() if g["root"] == M1)
        self.assertEqual((g["count"], g["full"]), (6, True))
        return folder, made

    def groups(self, nation=0, factory=10):
        return next(r for r in self.call("board", nation, "us")["rows"] if r["factory"] == factory)["groups"]

    def test_a_seventh_is_refused_in_words_and_nothing_is_written(self):
        folder, _made = self.fill_m1()
        before = self.files(folder)
        said = self.refusal("new_unit", M1, "Medium 5", 40, -1, -1, False, None)
        self.assertRegex(said["us"], r"^There's no room in M One's group in Armor Base: it would have 7 units, and a "
                                     r"group holds at most 6\.")
        self.assertEqual(self.english_left(said), [])
        for text in said.values():
            self.assert_plain(text)
        self.assertEqual(self.files(folder), before)
        # a copy of the upgrade M2 stays an upgrade of M1: in M1's group, refused too
        self.assertEqual(self.english_left(self.refusal("new_unit", M2, "M2 again", 40, -1, -1, False, None)), [])
        self.assertEqual(self.files(folder), before)

    def test_the_seventh_in_a_group_of_its_own_or_after_one_is_deleted(self):
        folder, made = self.fill_m1()
        own = self.call("new_unit", M1, "Medium own", 40, -1, -1, False, "new")["address"]
        self.assertEqual(menugroups.read(folder)[own], own)
        self.call("delete_unit", made[0], None)
        again = self.call("new_unit", M1, "Medium 5", 40, -1, -1, False, None)["address"]
        self.assertIn(again, next(g for g in self.groups() if g["root"] == M1)["units"])
        self.assertEqual(self.build(folder)[0], [])

    def test_an_eleventh_group_in_a_building_is_refused(self):
        folder = self.mod("Ten groups")
        have = len(self.groups())
        for k in range(have, menugroups.MOST_GROUPS):
            self.call("new_unit", L1, f"Own group {k}", 40, -1, -1, False, "new")
        self.assertEqual(len(self.groups()), menugroups.MOST_GROUPS)
        said = self.refusal("new_unit", L1, "One more group", 40, -1, -1, False, "new")
        self.assertRegex(said["us"], r"^There's no room for another group in Armor Base")
        self.assertEqual(self.english_left(said), [])
        self.assertEqual(self.build(folder)[0], [])


class CopiesOfUpgrades(Player):
    """A copy of a unit researched from another: in its own menu it stays an upgrade; in a menu its research parent
    isn't in, it becomes buildable from the start (a unit researched from another nation's never lets a match load)."""

    def test_a_copy_of_an_upgrade_in_its_own_menu_stays_one(self):
        folder = self.mod("Upgrade copies")
        tank = self.call("new_unit", M2, "M2 Copy", 40, -1, -1, False, None)
        plane = self.call("new_unit", P2, "P2 Copy", 40, -1, -1, False, None)
        self.assertEqual((tank["research_parent_dropped"], plane["research_parent_dropped"]), (None, None))
        self.assertEqual(self.call("upgrade", tank["address"], "us")["parent"]["address"], M1)
        errors, ndf, _ = self.build(folder)
        self.assertEqual(errors, [])
        self.assertIsNotNone(self.value(ndf, tank["address"], "UpgradeRequire"))
        self.assertIsNotNone(self.value(ndf, plane["address"], "UpgradeRequire"))

    def test_a_copy_of_another_nations_upgrade_becomes_buildable_from_the_start(self):
        folder = self.mod("Upgrade elsewhere")
        res = self.call("new_unit", G2, "G2 for the USA", 40, 0, 10, False, None)
        self.assertEqual(res["research_parent_dropped"], G1)
        up = self.call("upgrade", res["address"], "us")
        self.assertIsNone(up["parent"])
        row = next(r for r in self.call("board", 0, "us")["rows"] if r["factory"] == 10)
        self.assertIn(res["address"], next(g for g in row["groups"] if g["root"] == H1)["units"])   # a heavy tank
        moved = self.call("new_unit", M2, "M2 at the AT base", 40, 0, 11, False, None)
        self.assertEqual(moved["research_parent_dropped"], M1)
        errors, ndf, _ = self.build(folder)
        self.assertEqual(errors, [])
        self.assertIsNone(self.value(ndf, res["address"], "UpgradeRequire"))
        self.assertIsNone(self.value(ndf, res["address"], "IsUpgrade"))

    # U-7: the page says nothing when a copy stops being an upgrade (new_unit's research_parent_dropped is never read
    # by newUnitForm): the player made a copy of G2, an upgrade of G1, and gets a unit bought from the start
    @unittest.expectedFailure
    def test_the_page_says_when_a_copy_stops_being_an_upgrade(self):
        page = (Path(__file__).parents[1] / "src" / "ruse_studio" / "ui" / "app.js").read_text(encoding="utf-8")
        start = page.index("function newUnitForm(")
        form = page[start:page.index("\nfunction ", start + 10)]
        self.assertIn("research_parent_dropped", form)


class CopyOfACopy(Player):
    def test_a_copy_of_a_copy_is_refused_and_not_offered(self):
        folder = self.mod("Copy of a copy")
        first = self.call("new_unit", M1, "First Copy", 40, -1, -1, False, None)["address"]
        self.assertFalse(self.call("unit", first, "us")["can_copy"])     # the page offers no New unit… on it
        before = self.files(folder)
        said = self.refusal("new_unit", first, "Second Copy", 40, -1, -1, False, None)
        self.assertEqual(self.english_left(said), [])
        self.assertEqual(self.files(folder), before)

    def test_the_board_moves_another_nations_copy_instead_of_copying_it(self):
        """A new unit of the mod put on another nation's board is moved there (board_put), never copied."""
        folder = self.mod("Board copies")
        mine = self.call("new_unit", M1, "Board Copy", 40, -1, -1, False, None)["address"]
        res = self.call("board_put", 1, 10, mine, "", None, None, "us")
        self.assertEqual(res["made"], mine)
        self.assertTrue(res["note"]["moved_nation"])
        self.assertEqual(self.build(folder)[0], [])

    def test_another_nations_unit_copied_twice_from_the_board(self):
        """The board's copy of another nation's unit, twice: the second gets _2, both named as the game names it."""
        folder = self.mod("Board twice")
        one = self.call("board_put", 0, 10, G1, "", None, None, "us")["made"]
        two = self.call("board_put", 0, 10, G1, "", None, None, "us")["made"]
        self.assertEqual((one, two), (U + "G_One", U + "G_One_2"))
        errors, ndf, texts = self.build(folder)
        self.assertEqual(errors, [])
        self.assertEqual(self.built_names(ndf, texts, one)["us"], self.built_names(ndf, texts, two)["us"])


if __name__ == "__main__":
    unittest.main()
