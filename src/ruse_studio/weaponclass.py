"""A weapon class of an ammunition's own (StudioApi's WeaponClassCalls), the "New weapon class" button on the ammo page
(the owner's go, 2026-11-09; a modder asked for a weapon class of his own).

What an ammunition does to each kind of target is one row of eleven numbers in the game's damage table, one number per
armour level: its power is multiplied by the number, and a 0 means it can't attack that target at all. Every ammunition
links to the same table and the table has no room for more rows, so a new weapon class is a copy of the whole table that
only this ammunition links to, with this ammunition's row changed. Nothing else's damage moves. Seen in the game in test
T62: a rifle round with a table of its own fired at tanks.

The numbers are not limited (the owner's rule, every combination possible): anything but a number is refused."""
from __future__ import annotations

import math
import re

STRESS, ARME, VALUES = "StressManager", "Arme", "Values"
AMMO = "TAmmunition"
# the start of a table copy's name. It sorts before "Ammo_": the mod file writes copies in name order, and a copied
# ammunition links to its table
PREFIX = "A_Weapon_Class_"
# the armour levels in the table's order, each as the Armour box names it: (a key of the Studio's words, its number)
LEVELS = (("armour_building", 0), ("armour_aircraft", 0), ("armour_para", 0), ("armour_infantry", 0), ("armour_light", 0),
          ("armour_tank", 1), ("armour_tank", 2), ("armour_tank", 3), ("armour_tank", 4), ("armour_tank", 5),
          ("armour_trucks", 0))


def _spelled(numbers) -> str:
    """The numbers as a list of the table's float32, as a mod file spells them."""
    def one(n):
        text = f"{float(n):.6f}".rstrip("0")
        return text + "0" if text.endswith(".") else text
    return "[" + ", ".join(one(n) for n in numbers) + "]"


def _is_number(n) -> bool:
    return isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)


class WeaponClassCalls:
    def _class_facts(self, edits, address: str) -> dict:
        """What a weapon class of the ammunition at `address` starts from: `keyed` (the address its changes are saved
        under), `o` (the game's object), `table` (the game's damage table it links to), `position` (its row's place in
        the table: the map is stored out of order), `game` (that row's numbers) and `own` (its own table's address)."""
        from .api import StudioError
        from .edits import Link, REMOVED
        real, new = self._resolve(edits, address)
        ix = self._open()
        try:
            try:
                o = ix.show(real)
            except KeyError:
                # not a game rule: the page asked for something this game build's index doesn't have
                raise StudioError(f"There's nothing at {address} in this game build.") from None
            if o["class"] != AMMO:
                raise StudioError(f"{address} isn't an ammunition")
            table = next((what for p, kind, what in ix.uses(real) if p == STRESS and kind == "object"), None)
            if table is None:
                raise StudioError(f"{address} has no damage table in this game build.")
            shown = ix.show(table)
        finally:
            ix.close()
        keyed = address if new else o["address"]
        arme = edits.get(keyed, ARME) if edits is not None else None
        if arme is REMOVED:
            arme = 0
        elif not _is_number(arme):
            arme = next((n for p, n, _t in o["values"] if p == ARME and n is not None), 0)
        nd, _changeable = self._value_file(shown["file"])
        pairs = nd.obj(shown["index"]).props[VALUES].pairs
        found = next(((i, row) for i, (key, row) in enumerate(pairs) if int(key.value) == int(arme)), None)
        if found is None:
            raise StudioError(f"{address} has a weapon class the game's damage table has no row for ({int(arme)}).")
        mine = edits.get(keyed, STRESS) if edits is not None else None
        own = str(mine) if isinstance(mine, Link) and str(mine).rsplit("/", 1)[-1].startswith(PREFIX) else None
        return {"keyed": keyed, "o": o, "table": table, "position": found[0],
                "game": [float(n.value) for n in found[1].items], "own": own}

    def weapon_class(self, address: str) -> dict:
        """The ammo page's weapon class: {"levels": [{"word", "n", "value", "game"}] (one per armour level, "word" a key
        of the Studio's words filled with "n"; its number and the game's), "own": it has a table of its own, "editable"}."""
        from .edits import EditsFileError
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        facts = self._class_facts(edits, address)
        values = facts["game"]
        if facts["own"]:
            row = edits.get(facts["own"], f"{VALUES}[{facts['position']}].v")
            if row is not None:
                values = [float(x) for x in str(row).strip("[] ").split(",")]
        show = lambda n: float(f"{n:.6g}")  # noqa: E731  (a float32 as a modder wrote it: 0.025, not 0.02500000037)
        return {"levels": [{"word": word, "n": n, "value": show(v), "game": show(g)}
                           for (word, n), v, g in zip(LEVELS, values, facts["game"])],
                "own": facts["own"] is not None,
                "editable": bool(edits is not None and self._editable(facts["o"])[0])}

    def weapon_class_set(self, address: str, numbers) -> dict:
        """Give the ammunition at `address` a weapon class of its own in the current mod: its own copy of the game's
        damage table, its row `numbers` (one for each armour level). Asked again, the numbers are replaced."""
        from .api import StudioError
        from .edits import Link, Literal, ModEdits, plain_name
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        if not isinstance(numbers, list) or len(numbers) != len(LEVELS) or not all(_is_number(n) for n in numbers):
            raise StudioError(f"A weapon class is one number for each of the {len(LEVELS)} kinds of target.")
        facts = self._class_facts(edits, address)
        ok, why = self._editable(facts["o"])
        if not ok:
            raise StudioError(f"{address} can't be edited here ({why})")
        keyed = facts["keyed"]
        namespace, tail = keyed.rsplit("/", 1)
        target = facts["own"] or f"{namespace}/{PREFIX}{re.sub(r'^Ammo_', '', tail)}"
        row = {f"{VALUES}[{facts['position']}].v": Literal(_spelled(numbers))}
        with self._saving:
            edits = ModEdits(edits.folder)  # read again: another change may have been saved meanwhile
            if target in edits.new_units:
                edits.new_units.pop(target)
                for key in [k for k in edits.edits if k[0] == target]:
                    del edits.edits[key]
            edits.add_unit(target, facts["table"], plain_name(target), row, named=False)
            edits.set(keyed, STRESS, Link(target))
        return {"saved": str(edits.file), **self.weapon_class(address)}

    def weapon_class_reset(self, address: str) -> dict:
        """Take the ammunition at `address` back to the game's weapon class: its own table goes."""
        from .api import StudioError
        from .edits import ModEdits
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        facts = self._class_facts(edits, address)
        if facts["own"]:
            with self._saving:
                edits = ModEdits(edits.folder)
                edits.reset(facts["keyed"], STRESS)
                self._drop_class_table(edits, facts["own"])
        return {"saved": str(edits.file), **self.weapon_class(address)}

    @staticmethod
    def class_table_of(edits, address: str) -> str | None:
        """The table of its own the ammunition at `address` links to in `edits`, or None."""
        from .edits import Link
        mine = edits.get(address, STRESS)
        return str(mine) if isinstance(mine, Link) and str(mine).rsplit("/", 1)[-1].startswith(PREFIX) else None

    @staticmethod
    def _drop_class_table(edits, table: str) -> None:
        """Take a table of its own out of the mod, unless a copy of the ammunition still links to it."""
        from .edits import Link
        if not any(isinstance(e.value, Link) and str(e.value) == table for e in edits.edits.values()):
            edits.remove_unit(table)
