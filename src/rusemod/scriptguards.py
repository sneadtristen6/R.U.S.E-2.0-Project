"""Guards on three places where the game's own scripts stop the game, added to every modded copy.

An error that leaves one of the game's scripts stops the game on the spot (its code 0x29a). Players' crash reports
(Bug Watch, 2026-11-05 to 11-09) came from three places where the game uses something without checking it is there,
each reached through mods the game was never written for:

- `menu`: a build list's research cards. For a research that upgrades a unit, the game looks that unit's button up in
  the SAME list. A set of mods can leave the unit in another building's list (one mod moves the T-26 to the Barracks,
  another makes the T-34 its upgrade in the Armor Base: neither is wrong alone) or hidden in the game mode played. The
  game then stops the moment the building is placed.
- `strategic_ia`: a mission's step that starts the computer's AI for a side. A side a person plays has no AI object,
  and this one step, unlike the steps beside it, uses it unchecked.
- `units`: a mission's step that turns units into another kind of unit. It keeps the new units for a few seconds and
  then uses each without checking it still exists; one killed and cleared away in between stops the game.

Each guard runs after the game's own module (pyscript.append_module, as the build lists' rows do: rusemod.menulines)
and changes nothing unless the game would have stopped: the game's own function runs first and unchanged where that
can be done (`menu`: only its exact failure is caught, any other error is passed on as it was; `strategic_ia`: only a
side with no AI object is left alone), and `units` repeats the game's five lines with the two that fail made safe per
unit. `menu` and `units` carry on with what the game's function does after the place it failed, so each is joined
only to the function it was written for: the module's function is compared with the game's own (GAME_FUNCTIONS, a
SHA-256 of its code), and a mod's own version of it is left as the mod has it, with a note.

A guard that can't be joined (a pack or module missing, a mod's own script, a name not there) is left out with a
note: it never stops a build.

Read in the game's scripts and, for `menu`, run with the game's own compiled menu scripts under its own Python on the
players' unit data, which gives the players' error without the guard and the lists with it. Not tried in the game.

Each guard that steps in also adds 1 to the count the game's own text says before a later script-error stop
("Previously ignored errors: N", COUNT), so Bug Watch can tell how often guards kept a game going before it stopped
(2026-11-13, the owner's "yes gather all bug watch stuff for this patch"). Checked with the game's own functions under
its Python (the count goes up by one only where a guard steps in); whether the game's text says it: not tried in the
game yet (one game test).
"""
from __future__ import annotations

import base64
import hashlib

from . import pyscript

# Each guard, when it steps in, adds 1 to the count the game's own script-error text says before a later stop
# ("Previously ignored errors: N", the game's sys.ignore_count), so the crash report of a stop later in the same game
# says how often guards had stepped in before it (Bug Watch's "ignored": rusemod.bugwatch.read_dump). The game's Python
# can write nothing anywhere else (2026-11-10, round 2 on FL-101). Never stops anything: any trouble is passed over.
COUNT = '''


def _r2g_count():
    # one more on the count the game's script-error text says before a later stop ("Previously ignored errors: N")
    try:
        import sys
        sys.ignore_count = getattr(sys, 'ignore_count', 0) + 1
    except:
        pass
'''
SOURCES = {
    "menu": '''\
# RUSE 2.0's guard on a build list's research cards (rusemod.scriptguards). The game's own code runs first, unchanged.
# Only when it fails at its unchecked look-up of the button of the unit an upgrade's research upgrades (the card is
# made and in the list, it is an upgrade's, and that unit has no button in this list), the card stays, unlinked, like
# a research that upgrades nothing, and the cards of the researches after it are made as the game goes on to do. Any
# other error is passed on as it was.
_r2g_game_add_techno = Menu.add_bouton_techno''' + COUNT + '''


def _r2g_no_parent_button(self, techno):
    try:
        if self._dico_boutons.get(techno, None) is None or not techno.IsUpgrade():
            return 0
        if self._dico_boutons.get(techno.GetParente().GetDescriptor().base_class, None) is None:
            return 1
    except:
        pass
    return 0


def _r2g_add_techno(self, techno, hud_instance, technologie_manager):
    try:
        return _r2g_game_add_techno(self, techno, hud_instance, technologie_manager)
    except KeyError:
        if not _r2g_no_parent_button(self, techno):
            raise
    _r2g_count()
    for techno_fille in techno.GetListeFilles():
        self.add_bouton_techno(techno_fille, hud_instance, technologie_manager)
    return None


Menu.add_bouton_techno = _r2g_add_techno
''',
    "strategic_ia": '''\
# RUSE 2.0's guard on a mission's "start the computer's AI for this side" step (rusemod.scriptguards). A side a person
# plays has no AI object: there is nothing to start, and the game's step would stop the game using it. Any other side
# goes to the game's own code, unchanged.
_r2g_game_ia_all = DescriptorIAAll.execute''' + COUNT + '''


def _r2g_ia_all(self, *args, **kwargs):
    try:
        no_ia = self.Camp.get_camp().ia is None
    except:
        no_ia = 0
    if no_ia:
        _r2g_count()
        return None
    return _r2g_game_ia_all(self, *args, **kwargs)


DescriptorIAAll.execute = _r2g_ia_all
''',
    "units": '''\
# RUSE 2.0's guard on the end of a mission's "turn these units into another unit" step (rusemod.scriptguards). The
# game keeps the new units for a few seconds, then takes their highlight off, each without checking it still exists:
# one killed and cleared away in between would stop the game. The game's own five lines, with a unit that is gone
# passed over.
_r2g_game_mute_finished = ActionMuteUnit.virtual_on_finished''' + COUNT + '''


def _r2g_mute_finished(self):
    units = getattr(self, '_ActionMuteUnit__units', None)
    if units is None:
        return _r2g_game_mute_finished(self)
    gone = 0
    for unit in units:
        try:
            unit.apparence_manager.Remove_Highlight_Modifier(self._fade_out_parameters)
            unit.apparence_manager.Set_AppearDisappearState(False)
        except RuntimeError:
            gone = 1
    if gone:
        _r2g_count()
    super(ActionMuteUnit, self).virtual_on_finished()
    self.terminate_ifn()
    return None


ActionMuteUnit.virtual_on_finished = _r2g_mute_finished
''',
}
# where each guard goes: (the script pack in ZZ_Win.dat, the game's module in it)
SCRIPTS = {
    "menu": ("genpython\\eugen.ipk", "genpython\\1000\\codeia\\python\\eugen\\headup\\menu.xyz"),
    "strategic_ia": ("genpython\\eugensolo.ipk",
                     "genpython\\1000\\codeia\\python\\eugensolo\\leveldesignsolo\\strategic_ia.xyz"),
    "units": ("genpython\\eugensolo.ipk", "genpython\\1000\\codeia\\python\\eugensolo\\leveldesignsolo\\units.xyz"),
}
# the game's function each guard takes the place of: (its class, its name). A guard that carries on after the place
# the game's function failed is joined only when the module's function is the game's own (its code's SHA-256, in
# scriptguards_compiled.GAME_FUNCTIONS); None: the guard only decides whether to call the function, whatever it is.
FUNCTIONS = {
    "menu": (b"Menu", b"add_bouton_techno"),
    "strategic_ia": None,
    "units": (b"ActionMuteUnit", b"virtual_on_finished"),
}
# what each guard is for, in the build's own words (the build says which were added)
WHAT = {
    "menu": "a build list whose research has no unit to stand beside",
    "strategic_ia": "a mission starting the AI of a side a person plays",
    "units": "a mission's changed units, one of them gone",
}


class GuardError(ValueError):
    pass


def source_sha(name: str) -> str:
    return hashlib.sha256(SOURCES[name].encode("utf-8")).hexdigest()


def template(name: str) -> pyscript.Code:
    """A guard, compiled with the game's Python: refused when the compiled one isn't of the source above."""
    from .scriptguards_compiled import COMPILED
    entry = COMPILED.get(name)
    if entry is None or entry["source_sha256"] != source_sha(name):
        raise GuardError(f"the compiled {name} guard isn't the one of its source: compile it again")
    code = pyscript.load(base64.b64decode(entry["marshal"]))
    if not isinstance(code, pyscript.Code):
        raise GuardError(f"the compiled {name} guard isn't a module")
    return code


def _plain(value):
    """A compiled function's parts as something to hash: nested code by its own parts, the rest by its repr."""
    if isinstance(value, pyscript.Code):
        return ("code", bytes(value.code), tuple(_plain(c) for c in value.consts), tuple(value.names),
                tuple(value.varnames), value.argcount)
    if isinstance(value, tuple):
        return tuple(_plain(v) for v in value)
    return repr(value)


def function_sha(module: pyscript.Code, cls: bytes, name: bytes) -> str | None:
    """The SHA-256 of what method `name` of class `cls` does in a compiled module (its code, constants, names and
    arguments; not its file name or line numbers), or None when the module has no such method."""
    for body in module.consts:
        if isinstance(body, pyscript.Code) and body.name == cls:
            for func in body.consts:
                if isinstance(func, pyscript.Code) and func.name == name:
                    return hashlib.sha256(repr(_plain(func)).encode("utf-8")).hexdigest()
    return None


# the name each guard keeps the game's own function under: a module that sets it has the guard already
KEPT = {"menu": b"_r2g_game_add_techno", "strategic_ia": b"_r2g_game_ia_all", "units": b"_r2g_game_mute_finished"}


def script_changes(zz_win, changed: dict | None = None) -> tuple[dict, list[str], list[str]]:
    """({script pack's path in ZZ_Win.dat: the pack's new bytes}, the guards added, notes on those left out).
    `zz_win`: ZZ_Win.dat as the build has it (an Edat, with the mods' changes); `changed`: the script packs the build
    changed already, {member path in ZZ_Win.dat: bytes} (BuildResult.script_changed): a guard goes on top of those
    (the build lists' rows template, when it is there, stays before the guard). A game without the script pack or
    the module (a made-up game in tests) gets nothing and no note."""
    from .edat import Edat
    from .scriptguards_compiled import GAME_FUNCTIONS
    out: dict = {}
    added, notes = [], []
    for name, (pack_path, member_path) in SCRIPTS.items():
        entry = zz_win.entry(pack_path) if zz_win is not None else None
        if entry is None:
            continue
        data = out.get(entry.path) or (changed or {}).get(entry.path)
        pack = Edat(data if data is not None else bytes(zz_win.read(entry)))
        member = pack.entry(member_path)
        if member is None:
            continue
        try:
            xyz = pyscript.read_xyz(bytes(pack.read(member)))
            module = pyscript.load(xyz.payload)
            if KEPT[name] in pyscript.stored_names(module):
                continue  # the guard is in this module already
            wanted = FUNCTIONS[name]
            if wanted is not None and function_sha(module, *wanted) != GAME_FUNCTIONS[name]:
                notes.append(f"{WHAT[name]}: this set's own {wanted[0].decode()}.{wanted[1].decode()} isn't the "
                             f"game's (a mod brings its own script), so it is left as the mod has it")
                continue
            joined = pyscript.append_module(xyz.payload, template(name))
        except (pyscript.ScriptError, GuardError, KeyError, ValueError) as exc:
            notes.append(f"{WHAT[name]}: {exc}")
            continue
        out[entry.path] = pack.to_bytes({member.path: pyscript.write_xyz(pyscript.Xyz(xyz.source_md5, joined))})
        added.append(name)
    return out, added, notes
