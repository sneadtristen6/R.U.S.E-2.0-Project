"""A scripted scenario's camps (a campaign chapter, an Operation, a challenge): who owns the units a spawn names by
its `Camp` number, read from the scenario's mission script in IA_Common.dat
(`genpython\\<build>\\test\\map\\<map>\\scripting<suffix>\\effetmap.xyz`, compiled Python 2.5, rusemod.pyscript).

The script makes each camp with `leveldesign.camps.VariableCamp(Alliance=..., CampNumber=..., Nationalite=...,
NiveauIA=..., ...)` stored under a name, and lists them in the launch descriptor's `CampList = [...]`, often in the
reverse of the order they're made (M03_Italie's first chapter: IR_763 down to IR_758). A spawn's `Camp` is the camp's
place in that list, unless the camp sets its own `CampNumber` (not -1); a number with no camp behind it never spawns.
That rule is LittleGroove's (ruse_mod_engine/camp_resolver.py, from the game's own launch code); this reads the same
two things straight from the compiled script, with nothing else to install. `NiveauIA` says who plays a camp: `Player`
is a human player, the others are the computer's.

Only straight-line code is followed (names, attributes, constants, lists, calls, stores), which is all a camp or the
camp list is made of; anything else just drops what was being followed.
"""
from __future__ import annotations

import zlib
from dataclasses import dataclass

from .pyscript import (CALL_FUNCTION, LOAD_ATTR, LOAD_CONST, LOAD_NAME, MAGIC, STORE_NAME, BUILD_TUPLE, Code, ScriptError,
                       instructions, load)

BUILD_LIST, STORE_GLOBAL, LOAD_GLOBAL, LOAD_FAST, STORE_FAST = 103, 97, 116, 124, 125  # Python 2.5's numbers
SCRIPT = "genpython\\{build}\\test\\map\\{map}\\scripting{suffix}\\effetmap.xyz"
# A camp's Nationalite (the game's French names) -> the nation number units carry (Nationalite on a descriptor)
NATIONS = {"EU": 0, "Allemagne": 1, "RU": 2, "France": 3, "Italie": 4, "URSS": 5, "Japon": 6}


@dataclass
class Camp:
    key: int                 # what a spawn's Camp holds for this camp
    var: str                 # the script's name for it (IR_758)
    player: bool             # NiveauIA.Player: a human player plays it
    ai: str | None           # its NiveauIA ("Player", "Scripted", ...)
    nation: str | None       # its Nationalite ("EU", "Allemagne", "RU", "France", "Italie", "URSS", "Japon")
    alliance: int | None     # its Alliance (the team)


def script_path(entries, map_dir: str, scenario_file: str) -> str | None:
    """The member of IA_Common.dat holding `scenario_file`'s mission script (leveldesign_chapter1.scenario ->
    ...\\scripting_chapter1\\effetmap.xyz), found case-blind among `entries` (its paths); None when it has none (the
    BATTLES maps' scenarios aren't scripted)."""
    stem = scenario_file.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    stem = stem[:-len(".scenario")] if stem.lower().endswith(".scenario") else stem
    suffix = stem[len("leveldesign"):] if stem.lower().startswith("leveldesign") else ""
    paths = {p.lower(): p for p in entries}
    builds = sorted({p.split("\\")[1] for p in paths if p.startswith("genpython\\") and p.count("\\") > 1
                     and p.split("\\")[1].isdigit()})
    for build in builds:
        want = SCRIPT.format(build=build, map=map_dir, suffix=suffix).lower()
        if want in paths:
            return paths[want]
    return None


def module_code(raw: bytes) -> Code:
    """The module code object of an .xyz mission script (its stored size isn't checked: some scripts ship it stale)."""
    if raw[:4] != MAGIC:
        raise ScriptError(f"not an .xyz script (starts {raw[:8].hex(' ')})")
    code = load(zlib.decompressobj().decompress(raw[28:]))
    if not isinstance(code, Code):
        raise ScriptError("the script isn't a compiled module")
    return code


def _text(v) -> str:
    return v.decode("latin-1") if isinstance(v, bytes) else str(v)


def _follow(code: Code, made: dict, lists: list) -> None:
    """Record every VariableCamp(...) stored under a name into `made` {name: keywords}, and every CampList=[...] given
    to a call into `lists`, in `code` and the code objects inside it."""
    stack: list = []
    for _at, op, arg in instructions(code.code):
        if op == LOAD_CONST:
            stack.append(("const", code.consts[arg]))
        elif op in (LOAD_NAME, LOAD_GLOBAL):
            stack.append(("name", _text(code.names[arg])))
        elif op == LOAD_FAST:
            stack.append(("name", _text(code.varnames[arg])))
        elif op == LOAD_ATTR and stack and stack[-1][0] in ("name", "attr"):
            stack.append(("attr", f"{stack.pop()[1]}.{_text(code.names[arg])}"))
        elif op in (BUILD_LIST, BUILD_TUPLE) and len(stack) >= arg:
            items = stack[len(stack) - arg:] if arg else []
            del stack[len(stack) - arg:]
            stack.append(("list", items))
        elif op == CALL_FUNCTION and len(stack) >= 1 + (arg & 0xFF) + 2 * (arg >> 8):
            n_pos, n_kw = arg & 0xFF, arg >> 8
            kw_items = stack[len(stack) - 2 * n_kw:] if n_kw else []
            del stack[len(stack) - 2 * n_kw:]
            del stack[len(stack) - n_pos:]
            callee = stack.pop()
            kwargs = {}
            for k, v in zip(kw_items[0::2], kw_items[1::2]):
                if k[0] == "const":
                    kwargs[_text(k[1])] = v
            if "CampList" in kwargs and kwargs["CampList"][0] == "list":
                lists.append([v[1] for v in kwargs["CampList"][1] if v[0] == "name"])
            stack.append(("call", callee[1] if callee[0] in ("name", "attr") else None, kwargs))
        elif op in (STORE_NAME, STORE_GLOBAL, STORE_FAST) and stack:
            v = stack.pop()
            names = code.varnames if op == STORE_FAST else code.names
            if v[0] == "call" and v[1] and v[1].endswith("VariableCamp"):
                made[_text(names[arg])] = v[2]
        else:
            stack.clear()  # something not followed: start again at the next statement
    for c in code.consts:
        if isinstance(c, Code):
            _follow(c, made, lists)


def _last(v) -> str | None:
    """An enum's member from `_enum_for_game_play.NiveauIA.Player`: "Player"; a constant as text."""
    if v is None:
        return None
    if v[0] == "attr":
        return v[1].rsplit(".", 1)[-1]
    if v[0] == "const" and v[1] is not None:
        return _text(v[1])
    return None


def _int(v) -> int | None:
    return v[1] if v and v[0] == "const" and isinstance(v[1], int) and not isinstance(v[1], bool) else None


def camps(raw: bytes) -> list[Camp]:
    """The camps of a mission script (.xyz bytes), in its CampList's order, each with the key a spawn's Camp uses.
    Empty when the script has no CampList."""
    made, lists = {}, []
    _follow(module_code(raw), made, lists)
    if not lists:
        return []
    out = []
    for i, var in enumerate(lists[0]):
        kw = made.get(var, {})
        number = _int(kw.get("CampNumber"))
        ai = _last(kw.get("NiveauIA"))
        out.append(Camp(number if number is not None and number != -1 else i, var, ai == "Player", ai,
                        _last(kw.get("Nationalite")), _int(kw.get("Alliance"))))
    return out


def scenario_camps(ia, map_dir: str, scenario_file: str) -> list[Camp]:
    """The camps of a scenario's mission script in IA_Common.dat (`ia`, an Edat), or [] when it has none."""
    member = script_path([e.path for e in ia.entries], map_dir, scenario_file)
    if member is None:
        return []
    return camps(bytes(ia.read(ia.find(member))))
