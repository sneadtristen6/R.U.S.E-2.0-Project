"""Pages in a long build list (the owner, 2026-10-31, with all 366 era units in: "you can't go down the list all the
way. So we need to introduce some way for the menu to be able to scroll down the whole inventory"; fault FL-51).

A tab of the build bar lists its buildings, then its units, one row each (a unit's upgrades in the row beside it), and
the game draws every row top to bottom: the rows past the bottom of the screen can't be reached. With pages, a tab
with more rows than PAGE_ROWS shows that many at a time with one more button below them that turns to the next page,
the last page back to the first; a tab whose rows fit is left as the game makes it.

Every reader of a tab's buttons in the game's scripts (the list the game draws, the buttons' states, a click's route)
takes them from the menu's liste_boutons, so the page is made there: its rows numbered from the top, the others left
out. The template runs after the game's own headup/menu module (pyscript.append_module), compiled with the game's
Python 2.5.1 (menupages_compiled). Any error inside it leaves the list as the game made it: an error out of the
game's scripts stops the game.
"""
from __future__ import annotations

import base64
import hashlib

from . import pyscript

PAGE_ROWS = 10   # rows on a page; with the page button, 11: his 1920 x 1080 screen showed 12 whole rows (bigpacks8)

SOURCES = {
    "menu": '''\
# pages in a long build list (the RUSE Studio's build): a tab with more rows than _r2_rows shows that many at a time
# and below them a button that turns to the next page (the last back to the first); a tab whose rows fit is left as
# the game makes it. Any error leaves the list as the game made it.
_r2_rows = 10


class R2PageButton(headup.bouton.BoutonDev):
    def OnEventButton1(self, mouse_state):
        try:
            headup.bouton.BoutonDev.OnEventButton1(self, mouse_state)
        except:
            pass
        try:
            menu = self._menu
            menu._r2_page = getattr(menu, '_r2_page', 0) + 1
            self.hud.update_menu_content()
        except:
            pass


_r2_game_update_sub_buttons = Menu.update_sub_buttons
_r2_game_liste_boutons = Menu.liste_boutons
_r2_game_kill = Menu.kill


def _r2_row(bouton):
    return getattr(bouton, '_r2_row', bouton.index)


def _r2_update_sub_buttons(self, *args, **kwargs):
    result = _r2_game_update_sub_buttons(self, *args, **kwargs)
    try:
        for bouton in _r2_game_liste_boutons(self):
            bouton._r2_row = bouton.index
    except:
        pass
    return result


def _r2_page_of(self, buttons):
    rows = []
    for bouton in buttons:
        row = _r2_row(bouton)
        if row not in rows:
            rows.append(row)
    if len(rows) <= _r2_rows + 1:
        for bouton in buttons:
            bouton.index = _r2_row(bouton)
        return buttons
    rows.sort()
    pages = (len(rows) + _r2_rows - 1) // _r2_rows
    page = getattr(self, '_r2_page', 0) % pages
    shown = rows[page * _r2_rows:(page + 1) * _r2_rows]
    out = []
    for bouton in buttons:
        row = _r2_row(bouton)
        if row in shown:
            bouton.index = shown.index(row)
            out.append(bouton)
    pager = getattr(self, '_r2_pager', None)
    if pager is None:
        pager = R2PageButton(self.hud, self, u'%d/%d' % (page + 1, pages), len(shown))
        self._r2_pager = pager
    pager.index = len(shown)
    pager._caption = u'%d/%d' % (page + 1, pages)
    out.append(pager)
    return out


def _r2_liste_boutons(self, *args, **kwargs):
    buttons = _r2_game_liste_boutons(self, *args, **kwargs)
    try:
        return _r2_page_of(self, buttons)
    except:
        return buttons


def _r2_kill(self, *args, **kwargs):
    try:
        pager = getattr(self, '_r2_pager', None)
        self._r2_pager = None
        if pager is not None:
            pager.kill()
    except:
        pass
    return _r2_game_kill(self, *args, **kwargs)


Menu.update_sub_buttons = _r2_update_sub_buttons
Menu.liste_boutons = _r2_liste_boutons
Menu.kill = _r2_kill
''',
}
# where each template goes: (the script pack in ZZ_Win.dat, the game's module in it)
SCRIPTS = {
    "menu": ("genpython\\eugen.ipk", "genpython\\1000\\codeia\\python\\eugen\\headup\\menu.xyz"),
}


class MenuPagesError(ValueError):
    pass


def source_sha(name: str) -> str:
    return hashlib.sha256(SOURCES[name].encode("utf-8")).hexdigest()


def template(name: str) -> pyscript.Code:
    """A template, compiled: refused when the compiled one isn't of the source above (menupages_compiled)."""
    from .menupages_compiled import COMPILED
    entry = COMPILED.get(name)
    if entry is None or entry["source_sha256"] != source_sha(name):
        raise MenuPagesError(f"the compiled {name} template isn't the one of its source: compile it again")
    code = pyscript.load(base64.b64decode(entry["marshal"]))
    if not isinstance(code, pyscript.Code):
        raise MenuPagesError(f"the compiled {name} template isn't a module")
    return code


def missing(zz_win) -> str:
    """What of the game's menu script ZZ_Win.dat lacks ("" when it's all there)."""
    from .edat import Edat
    for pack_path, member_path in SCRIPTS.values():
        entry = zz_win.entry(pack_path)
        if entry is None:
            return f"ZZ_Win.dat has no {pack_path}"
        if Edat(bytes(zz_win.read(entry))).entry(member_path) is None:
            return f"{pack_path} has no {member_path}"
    return ""


def script_changes(zz_win, packs: dict | None = None) -> dict:
    """{script pack's path in ZZ_Win.dat: (the pack, as an Edat; {module path: the new .xyz})}: the game's menu module
    with the pages template run after it. `packs`: script packs other steps already changed, {path: (pack, {module
    path: .xyz})}; a module there is changed from that version."""
    from .edat import Edat
    out: dict = {}
    for name, (pack_path, member_path) in SCRIPTS.items():
        entry = zz_win.entry(pack_path)
        if entry is None:
            raise MenuPagesError(f"ZZ_Win.dat has no {pack_path}")
        pack, changed = (packs or {}).get(entry.path) or out.get(entry.path) or (Edat(bytes(zz_win.read(entry))), {})
        member = pack.entry(member_path)
        if member is None:
            raise MenuPagesError(f"{pack_path} has no {member_path}")
        raw = changed.get(member.path) or bytes(pack.read(member))
        xyz = pyscript.read_xyz(raw)
        joined = pyscript.append_module(xyz.payload, template(name))
        out[entry.path] = (pack, {**changed, member.path: pyscript.write_xyz(pyscript.Xyz(xyz.source_md5, joined))})
    return out
