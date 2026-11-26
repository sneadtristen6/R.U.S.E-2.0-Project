"""The building that builds a unit, picked from the nation's real buildings and not typed as a number (the owner,
2026-11-26, "3 A": build it: the unit's page offers a list of that nation's own buildings in place of typing a name).
The All values tab (code names, value_edit) keeps taking a typed number: the plan's own default for its open question.
On test_scenarios_units_base's made-up game: the unit's Factory typed as 99, a build menu its nation hasn't got, was
saved and then built ("Factory: 99"); now it's refused in words in every language, and a real menu of the nation is
still saved and built."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import unittest
from pathlib import Path

from test_scenarios_units_base import M1, Player

UI = Path(__file__).resolve().parents[1] / "src" / "ruse_studio" / "ui"


class FactoryPick(Player):
    def own_menus(self, address):
        """(the unit's nation, its factory, the nation's other factories) as the page's menus list has them."""
        unit = next(u for u in self.call("units")["units"] if u["address"] == address)
        nation = next(n for n in self.call("menus", "us")["nations"] if n["name"] == unit["nation_name"]
                      or n["nation"] == unit.get("nation"))
        factories = [f["factory"] for f in nation["factories"]]
        return nation["nation"], unit["factory"], factories

    def test_a_factory_the_nation_has_no_menu_for_is_refused_and_nothing_saved(self):
        folder = self.mod("Factory refused")
        before = {p: p.read_bytes() for p in folder.rglob("*") if p.is_file()}
        said = self.refusal("edit", M1, "Factory", 99, "", "")
        self.assertEqual(self.english_left(said), [])
        self.assertEqual({p: p.read_bytes() for p in folder.rglob("*") if p.is_file()}, before)
        self.assertEqual(self.build(folder)[0], [])

    def test_a_real_building_of_the_nation_is_saved_and_built(self):
        folder = self.mod("Factory real")
        _nation, own, factories = self.own_menus(M1)
        other = next(f for f in factories if f != own)
        self.assertEqual(self.call("edit", M1, "Factory", other, "", "")["value"], other)
        errors, ndf, _texts = self.build(folder)
        self.assertEqual(errors, [])
        self.assertEqual(self.value(ndf, M1, "Factory").scalar(), other)

    def test_the_units_page_offers_the_nations_buildings_as_a_list(self):
        app = (UI / "app.js").read_text(encoding="utf-8")
        self.assertIn("function factoryBox(", app)
        row = app[app.index("function row(u, r, mode)"):]
        self.assertIn('r.prop === "Factory"', row[:row.index("\nfunction ")])
        box = app[app.index("function factoryBox("):]
        self.assertIn('el("select"', box[:box.index("\nfunction ")])
        self.assertIn("api().menus(", box[:box.index("\nfunction ")])


if __name__ == "__main__":
    unittest.main()
