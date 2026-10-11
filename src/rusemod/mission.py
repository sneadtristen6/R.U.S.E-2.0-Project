"""A new Operation's or campaign chapter's own mission (maps/<map>/mission.toml, MOD_FORMAT §8): its sides, its rules,
its goals, its events (When -> Do) and its camera moves, as data. The build makes the mission script from it
(rusemod.missionscript: the game's own blocks, written the way Python 2.5 compiles them, no compiler and no script
from the mod), with its texts in the game's ten languages, its camera moves in the map's camera file, and the
mission in a menu pack of its own (the game keeps a mission's saved results by pack and place).

Every block is written the way the game's own missions write it, and each kind was tried in the game in our test
missions (T22 2026-10-03: a hint, units made, an artillery strike, goals, victory; T30 2026-10-04: an attack order,
a bombing run, named units in a group, a group-destroyed goal; T41 2026-10-09: a move along spots, holding a zone, a
paratroop drop, main and bonus goals, a campaign chapter's victory). Not tried yet, and said so where the Studio
offers them: a camera move of the mod's own (T41's never played: the camera file's TOPO table didn't list it, fixed
here), the goals panel opened after the goals start (T41's Escape lock: an Operation's goals panel holds Escape
until it's closed), a side handed to the computer (DescriptorIAAll, Prolution's Fortress Europa uses it), repeating
events, a goal done after a time, the money given during a mission.

The sides are the copied mission's own, in its order, with the camp numbers its scenario's starting points and spawns
use: a mission file changes a side's nation, difficulty, money and whether the computer plays it, never how many
there are (the game wants as many human sides as players).
"""
from __future__ import annotations

import math
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .missionscript import Attr, Call, Long, Ref, call

LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")  # the game's ten (its translations folders)
E = "_enum_for_game_play"
# a side's nation: the Studio's names -> the game's (Nationalite)
NATIONS = {"US": "EU", "Germany": "Allemagne", "UK": "RU", "France": "France", "Italy": "Italie", "USSR": "URSS",
           "Japan": "Japon"}
DIFFICULTIES = {"easy": "Facile", "normal": "Normal", "hard": "Difficile"}  # (TDifficultes, as the missions use)
PLAYS = ("player", "script", "ai")   # a human; the computer, doing only what the events say; the computer, all of it
TIME_UP = ("defeat", "victory", "nothing")
WIN = ("main_goals", "events")
WHEN = ("start", "time", "zone", "destroyed", "goal")
GOAL_DONE = ("zone", "destroyed", "time", "event")
ACTIONS = ("message", "spawn", "move", "attack", "hold", "artillery", "bombing", "paradrop", "camera", "money", "goal",
           "complete", "victory", "defeat", "wait", "ai")
MOST = {"goals": 40, "events": 200, "actions": 60, "cameras": 30, "points": 60, "count": 50}
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
_TEXT_MOST = 2000


class MissionError(ValueError):
    pass


@dataclass
class Words:
    """A text in English and, where given, the other languages (a language left out shows the English)."""
    us: str
    more: dict = field(default_factory=dict)

    def get(self, lang: str) -> str:
        return self.more.get(lang) or self.us


@dataclass
class Side:
    number: int                    # the camp number its scenario uses (the copied mission's: not changed here)
    nation: str | None = None      # NATIONS key; None: the copied mission's
    difficulty: str | None = None  # DIFFICULTIES key; None: the copied mission's
    plays: str | None = None       # "script" or "ai" for a computer side; None: as the copied mission
    money: int | None = None       # its money at the start; None: as the game gives


@dataclass
class Action:
    do: str
    text: Words | None = None   # message
    unit: str = ""              # spawn: a class name (Unit_M4_Sherman)
    count: int = 1              # spawn
    side: int | None = None     # spawn, money, ai: a side's number
    at: str = ""                # spawn, artillery, bombing, paradrop: a named point
    group: str = ""             # spawn (into), move, attack, hold, artillery, bombing, paradrop
    to: list = field(default_factory=list)  # move: named points, in turn
    target: str = ""            # attack: a group
    zone: str = ""              # hold
    camera: str = ""            # camera: a [[camera]] name, or a path of the copied map's
    seconds: float = 0.0        # camera (how long), wait
    amount: int = 0             # money
    goal: str = ""              # goal (show it), complete (set it done)


@dataclass
class Event:
    id: str
    when: str
    at: float = 0.0          # time: seconds after the start
    zone: str = ""           # zone
    side: int | None = None  # zone: whose units (None: the player's)
    count: int = 1           # zone: how many
    group: str = ""          # destroyed
    goal: str = ""           # goal
    wait: float = 0.0        # seconds between being set off and the first action
    repeat: float = 0.0      # time: again every this many seconds (0: once)
    actions: list = field(default_factory=list)


@dataclass
class Goal:
    id: str
    text: Words
    main: bool = True
    done: str = "zone"       # GOAL_DONE
    zone: str = ""           # done = zone: a unit of the player's (not a building or truck) in it
    group: str = ""          # done = destroyed: all of it destroyed
    seconds: float = 0.0     # done = time: this long after it starts
    marker: str = ""         # a named point its label sits on (else on its group, else no marker)
    start: str = "start"     # "start": shown at the start; "event": shown by an event's goal action


@dataclass
class Camera:
    name: str
    points: list             # [(x, y, z)], map units (z: height above the sea, as the game's)
    look: tuple              # (x, y, z): the spot it looks at the whole way
    seconds: float = 15.0


@dataclass
class Mission:
    time_limit: float = 0.0  # minutes; 0: no clock
    time_up: str = "defeat"
    win: str = "main_goals"
    opening: str = ""        # a camera move played at the start (a [[camera]], or a path of the copied map's)
    sides: list = field(default_factory=list)
    goals: list = field(default_factory=list)
    events: list = field(default_factory=list)
    cameras: list = field(default_factory=list)


# --- reading mission.toml ---

def _words(v, at: str) -> Words:
    if isinstance(v, str):
        v = {"us": v}
    if not isinstance(v, dict) or not isinstance(v.get("us"), str) or not v["us"].strip():
        raise MissionError(f"{at}: text needs its English words (text = \"...\", or a table with us = \"...\")")
    extra = sorted(set(v) - set(LANGS))
    if extra:
        # not a game rule: our list of the game's 10 text languages
        raise MissionError(f"{at}: {extra[0]!r} isn't one of the game's languages ({', '.join(LANGS)})")
    for lang, t in v.items():
        if not isinstance(t, str) or len(t) > _TEXT_MOST:
            raise MissionError(f"{at}: the {lang} words must be text of up to {_TEXT_MOST} characters")
    return Words(v["us"].strip(), {k: t.strip() for k, t in v.items() if k != "us" and t.strip()})


def _num(m: dict, k: str, at: str, default=0.0, least=0.0, most=1e9) -> float:
    v = m.get(k, default)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not least <= v <= most:
        raise MissionError(f"{at}: {k} must be a number from {least:g} to {most:g}")
    return float(v)


def _int(m: dict, k: str, at: str, default=None, least=0, most=2 ** 31 - 1):
    if k not in m:
        return default
    v = m[k]
    if isinstance(v, bool) or not isinstance(v, int) or not least <= v <= most:
        raise MissionError(f"{at}: {k} must be a whole number from {least} to {most}")
    return v


def _name(m: dict, k: str, at: str, required=False) -> str:
    v = m.get(k, "")
    if not isinstance(v, str) or (v and not _ID.match(v)) or (required and not v):
        raise MissionError(f"{at}: {k} must be a name of letters, digits and _ (starting with a letter, up to 40)"
                           + (" and is needed" if required else ""))
    return v


def _spot(m: dict, k: str, at: str, required=False) -> str:
    """A named point or zone of the map (its scenario's own, or one a mod adds in places.toml)."""
    v = m.get(k, "")
    if not isinstance(v, str) or len(v) > 100 or (v and not all(c.isalnum() or c in "_-. " for c in v)) \
            or (required and not v):
        raise MissionError(f"{at}: {k} must name a point or zone of the map" + (" (it's needed)" if required else ""))
    return v


def _keys(m: dict, allowed: set, at: str) -> None:
    extra = sorted(set(m) - allowed)
    if extra:
        raise MissionError(f"{at}: unknown key {extra[0]!r}")


def _action(m, at: str) -> Action:
    if not isinstance(m, dict):
        raise MissionError(f"{at} isn't a table")
    do = m.get("do")
    if do not in ACTIONS:
        raise MissionError(f"{at}: do must be one of {', '.join(ACTIONS)}")
    a = Action(do)
    need = {"message": {"text"}, "spawn": {"unit", "at"}, "move": {"group", "to"}, "attack": {"group", "target"},
            "hold": {"group", "zone"}, "artillery": {"group", "at"}, "bombing": {"group", "at"},
            "paradrop": {"group", "at"}, "camera": {"camera"}, "money": {"side", "amount"}, "goal": {"goal"},
            "complete": {"goal"}, "victory": set(), "defeat": set(), "wait": {"seconds"}, "ai": {"side"}}[do]
    allowed = need | {"do"} | ({"count", "side", "group"} if do == "spawn" else set()) \
        | ({"seconds"} if do == "camera" else set())
    _keys(m, allowed, at)
    missing = sorted(need - set(m))
    if missing:
        raise MissionError(f"{at}: {do} needs {missing[0]}")
    if "text" in m:
        a.text = _words(m["text"], at)
    if "unit" in m:
        u = m["unit"]
        if not isinstance(u, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,99}", u):
            raise MissionError(f"{at}: unit must be a unit's class name, like Unit_M4_Sherman")
        a.unit = u
    a.count = _int(m, "count", at, 1, 1, MOST["count"])
    a.side = _int(m, "side", at, None, 0, 16)
    a.at = _spot(m, "at", at)
    a.group = _name(m, "group", at)
    if "to" in m:
        to = m["to"]
        if not isinstance(to, list) or not to or len(to) > MOST["points"]:
            raise MissionError(f"{at}: to must be a list of named points (1 to {MOST['points']})")
        a.to = [_spot({"to": t}, "to", at, True) for t in to]
    a.target = _name(m, "target", at)
    a.zone = _spot(m, "zone", at)
    if "camera" in m:
        c = m["camera"]
        if not isinstance(c, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,60}", c):
            raise MissionError(f"{at}: camera must name a camera move")
        a.camera = c
    a.seconds = _num(m, "seconds", at, 15.0 if do == "camera" else 0.0, 0.0, 3600.0)
    a.amount = _int(m, "amount", at, 0, 0, 10 ** 9)
    a.goal = _name(m, "goal", at)
    return a


def parse(data: dict, where: str = "mission.toml") -> Mission:
    """A mission file's contents (tomllib's dict) as a Mission; raises MissionError with what to change."""
    _keys(data, {"mission", "side", "goal", "event", "camera"}, where)
    head = data.get("mission", {})
    if not isinstance(head, dict):
        raise MissionError(f"{where}: [mission] is a table")
    _keys(head, {"time_limit", "time_up", "win", "opening"}, f"{where}: [mission]")
    m = Mission(time_limit=_num(head, "time_limit", f"{where}: [mission]", 0.0, 0.0, 600.0))
    m.time_up = head.get("time_up", "defeat")
    if m.time_up not in TIME_UP:
        raise MissionError(f"{where}: [mission] time_up must be one of {', '.join(TIME_UP)}")
    m.win = head.get("win", "main_goals")
    if m.win not in WIN:
        raise MissionError(f"{where}: [mission] win must be one of {', '.join(WIN)}")
    op = head.get("opening", "")
    if not isinstance(op, str) or (op and not re.fullmatch(r"[A-Za-z0-9_]{1,60}", op)):
        raise MissionError(f"{where}: [mission] opening must name a camera move, or be left out")
    m.opening = op
    seen_sides = set()
    for n, s in enumerate(data.get("side", []), start=1):
        at = f"{where}: side {n}"
        if not isinstance(s, dict):
            raise MissionError(f"{at} isn't a table")
        _keys(s, {"number", "nation", "difficulty", "plays", "money"}, at)
        number = _int(s, "number", at, None, 0, 16)
        if number is None or number in seen_sides:
            raise MissionError(f"{at}: number (its camp number, 0 up) is needed, once a side")
        seen_sides.add(number)
        side = Side(number, money=_int(s, "money", at, None, 0, 10 ** 9))
        for k, table in (("nation", NATIONS), ("difficulty", DIFFICULTIES)):
            if k in s:
                if s[k] not in table:
                    raise MissionError(f"{at}: {k} must be one of {', '.join(table)}")
                setattr(side, k, s[k])
        if "plays" in s:
            if s["plays"] not in PLAYS:
                raise MissionError(f"{at}: plays must be one of {', '.join(PLAYS)}")
            side.plays = s["plays"]
        m.sides.append(side)
    ids: set = set()

    def unique(i: str, at: str) -> str:
        if i in ids:
            raise MissionError(f"{at}: id {i!r} is used twice (goals and events each need their own)")
        ids.add(i)
        return i
    goals = data.get("goal", [])
    if not isinstance(goals, list) or len(goals) > MOST["goals"]:
        raise MissionError(f"{where}: up to {MOST['goals']} [[goal]] tables")
    for n, g in enumerate(goals, start=1):
        at = f"{where}: goal {n}"
        if not isinstance(g, dict):
            raise MissionError(f"{at} isn't a table")
        _keys(g, {"id", "text", "main", "done", "zone", "group", "seconds", "marker", "start"}, at)
        goal = Goal(unique(_name(g, "id", at, True), at), _words(g.get("text"), at))
        if "main" in g:
            if not isinstance(g["main"], bool):
                raise MissionError(f"{at}: main is true (a main goal) or false (a bonus goal)")
            goal.main = g["main"]
        goal.done = g.get("done", "zone")
        if goal.done not in GOAL_DONE:
            raise MissionError(f"{at}: done must be one of {', '.join(GOAL_DONE)}")
        goal.zone = _spot(g, "zone", at, goal.done == "zone")
        goal.group = _name(g, "group", at, goal.done == "destroyed")
        goal.seconds = _num(g, "seconds", at, 0.0, 0.0, 36000.0)
        if goal.done == "time" and goal.seconds <= 0:
            raise MissionError(f"{at}: done = \"time\" needs seconds (how long after it starts)")
        goal.marker = _spot(g, "marker", at)
        goal.start = g.get("start", "start")
        if goal.start not in ("start", "event"):
            raise MissionError(f"{at}: start is \"start\" (shown at the start) or \"event\" (shown by an event)")
        m.goals.append(goal)
    events = data.get("event", [])
    if not isinstance(events, list) or len(events) > MOST["events"]:
        raise MissionError(f"{where}: up to {MOST['events']} [[event]] tables")
    for n, e in enumerate(events, start=1):
        at = f"{where}: event {n}"
        if not isinstance(e, dict):
            raise MissionError(f"{at} isn't a table")
        _keys(e, {"id", "when", "at", "zone", "side", "count", "group", "goal", "wait", "repeat", "do"}, at)
        ev = Event(unique(_name(e, "id", at, True), at), e.get("when", ""))
        if ev.when not in WHEN:
            raise MissionError(f"{at}: when must be one of {', '.join(WHEN)}")
        ev.at = _num(e, "at", at, 0.0, 0.0, 36000.0)
        ev.zone = _spot(e, "zone", at, ev.when == "zone")
        ev.side = _int(e, "side", at, None, 0, 16)
        ev.count = _int(e, "count", at, 1, 1, 500)
        ev.group = _name(e, "group", at, ev.when == "destroyed")
        ev.goal = _name(e, "goal", at, ev.when == "goal")
        ev.wait = _num(e, "wait", at, 0.0, 0.0, 36000.0)
        ev.repeat = _num(e, "repeat", at, 0.0, 0.0, 36000.0)
        if ev.repeat and ev.when != "time":
            raise MissionError(f"{at}: repeat is for when = \"time\" only")
        if ev.repeat and ev.repeat < 5:
            raise MissionError(f"{at}: repeat is at least 5 seconds")
        acts = e.get("do", [])
        if not isinstance(acts, list) or len(acts) > MOST["actions"]:
            raise MissionError(f"{at}: do is a list of up to {MOST['actions']} actions")
        ev.actions = [_action(a, f"{at}: action {k}") for k, a in enumerate(acts, start=1)]
        m.events.append(ev)
    cams = data.get("camera", [])
    if not isinstance(cams, list) or len(cams) > MOST["cameras"]:
        raise MissionError(f"{where}: up to {MOST['cameras']} [[camera]] tables")
    names: set = set()
    for n, c in enumerate(cams, start=1):
        at = f"{where}: camera {n}"
        if not isinstance(c, dict):
            raise MissionError(f"{at} isn't a table")
        _keys(c, {"name", "points", "look", "seconds"}, at)
        name = c.get("name", "")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,59}", name) or name in names:
            raise MissionError(f"{at}: name must be its own name of letters, digits and _")
        names.add(name)
        pts = c.get("points", [])
        if not isinstance(pts, list) or not 2 <= len(pts) <= MOST["points"]:
            raise MissionError(f"{at}: points is a list of 2 to {MOST['points']} [x, y, z] points")
        points = [_point(p, f"{at}: points") for p in pts]
        m.cameras.append(Camera(name, points, _point(c.get("look"), f"{at}: look"),
                                _num(c, "seconds", at, 15.0, 1.0, 600.0)))
    return m


def _point(p, at: str) -> tuple:
    if not isinstance(p, list) or len(p) != 3 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                                                     or not math.isfinite(v) for v in p):
        raise MissionError(f"{at}: a point is [x, y, z] in map units")
    return tuple(float(v) for v in p)


def read_mod(folder: Path) -> dict:
    """{map folder name: (Mission, the file's path in the mod)} for every maps/<map>/mission.toml of a mod."""
    out = {}
    maps = Path(folder) / "maps"
    for f in sorted(maps.glob("*/mission.toml"), key=lambda p: p.parent.name.lower()) if maps.is_dir() else []:
        rel = f.relative_to(folder).as_posix()
        try:
            data = tomllib.loads(f.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
            raise MissionError(f"{rel}: {exc}") from None
        out[f.parent.name] = (parse(data, rel), rel)
    return out


# --- writing mission.toml (the Studio) ---

def _q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t") + '"'


def _wt(w: Words) -> str:
    if not w.more:
        return _q(w.us)
    return "{ " + ", ".join(f"{k} = {_q(v)}" for k, v in [("us", w.us)] + sorted(w.more.items())) + " }"


def _n(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def _action_toml(a: Action) -> str:
    parts = [f'do = "{a.do}"']
    if a.text is not None:
        parts.append(f"text = {_wt(a.text)}")
    if a.unit:
        parts.append(f'unit = "{a.unit}"')
    if a.do == "spawn" and a.count != 1:
        parts.append(f"count = {a.count}")
    if a.side is not None:
        parts.append(f"side = {a.side}")
    for k in ("at", "group", "target", "zone", "camera", "goal"):
        if getattr(a, k):
            parts.append(f"{k} = {_q(getattr(a, k))}")
    if a.to:
        parts.append("to = [" + ", ".join(_q(t) for t in a.to) + "]")
    if a.do in ("wait", "camera"):
        parts.append(f"seconds = {_n(a.seconds)}")
    if a.do == "money":
        parts.append(f"amount = {a.amount}")
    return "{ " + ", ".join(parts) + " }"


def to_toml(m: Mission, header: str = "") -> str:
    lines = [f"# {ln}" for ln in header.splitlines()] + ([""] if header else [])
    lines += ["[mission]", f"time_limit = {_n(m.time_limit)}", f'time_up = "{m.time_up}"', f'win = "{m.win}"']
    if m.opening:
        lines.append(f'opening = "{m.opening}"')
    for s in m.sides:
        lines += ["", "[[side]]", f"number = {s.number}"]
        for k in ("nation", "difficulty", "plays"):
            if getattr(s, k):
                lines.append(f'{k} = "{getattr(s, k)}"')
        if s.money is not None:
            lines.append(f"money = {s.money}")
    for g in m.goals:
        lines += ["", "[[goal]]", f'id = "{g.id}"', f"text = {_wt(g.text)}", f"main = {'true' if g.main else 'false'}",
                  f'done = "{g.done}"']
        for k in ("zone", "group", "marker"):
            if getattr(g, k):
                lines.append(f"{k} = {_q(getattr(g, k))}")
        if g.done == "time":
            lines.append(f"seconds = {_n(g.seconds)}")
        if g.start != "start":
            lines.append(f'start = "{g.start}"')
    for e in m.events:
        lines += ["", "[[event]]", f'id = "{e.id}"', f'when = "{e.when}"']
        if e.when == "time":
            lines.append(f"at = {_n(e.at)}")
        if e.zone:
            lines.append(f"zone = {_q(e.zone)}")
        if e.side is not None:
            lines.append(f"side = {e.side}")
        if e.when == "zone" and e.count != 1:
            lines.append(f"count = {e.count}")
        for k in ("group", "goal"):
            if getattr(e, k):
                lines.append(f"{k} = {_q(getattr(e, k))}")
        if e.wait:
            lines.append(f"wait = {_n(e.wait)}")
        if e.repeat:
            lines.append(f"repeat = {_n(e.repeat)}")
        lines.append("do = [")
        lines += [f"  {_action_toml(a)}," for a in e.actions]
        lines.append("]")
    for c in m.cameras:
        lines += ["", "[[camera]]", f'name = "{c.name}"', f"seconds = {_n(c.seconds)}",
                  "points = [" + ", ".join("[" + ", ".join(_n(v) for v in p) + "]" for p in c.points) + "]",
                  "look = [" + ", ".join(_n(v) for v in c.look) + "]"]
    return "\n".join(lines) + "\n"


# --- the copied mission: its sides and rules, read from its script (rusemod.missions) ---

@dataclass
class Base:
    camps: list          # [(var, number, func, kwargs {name: script value}, the player's?)] in CampList order
    support: list        # [(var, Call)]: what the camps name (their LocalizedCampName)
    rules: Call | None   # its GameRules call
    chapter_pos: bool    # it has a MapChapterPos (a campaign chapter)


def _value(v, calls: dict, support: dict, depth=0):
    """A value as rusemod.missions follows it -> a missionscript value; names it uses go into `support`."""
    if depth > 6:
        raise MissionError("the copied mission's sides nest too deep to copy")
    kind = v[0]
    if kind == "const":
        x = v[1]
        if isinstance(x, bytes):
            return x.decode("latin-1")
        if isinstance(x, int) and not isinstance(x, bool) and not -2 ** 31 <= x < 2 ** 31:
            return Long(x)
        return x
    if kind == "attr":
        return Attr(v[1])
    if kind == "list":
        return [_value(x, calls, support, depth + 1) for x in v[1]]
    if kind == "name":
        name = v[1]
        if name in ("True", "False", "None"):
            return {"True": True, "False": False, "None": None}[name]
        if name not in calls:
            raise MissionError(f"the copied mission's sides use {name}, which isn't a block")
        if name not in support:
            func, kw, args = calls[name]
            support[name] = None  # (no loops)
            support[name] = Call(func, tuple(_value(a, calls, support, depth + 1) for a in args),
                                 sorted((k, _value(x, calls, support, depth + 1)) for k, x in kw.items()))
        return Ref("B_" + name)
    if kind == "call":
        return Call(v[1], tuple(_value(a, calls, support, depth + 1) for a in v[3]),
                    sorted((k, _value(x, calls, support, depth + 1)) for k, x in v[2].items()))
    raise MissionError("the copied mission's sides hold something that can't be copied")


def _rename(v):
    """A support call's own names -> their B_ names (support refs are already B_)."""
    return v


def base_of(raw: bytes) -> Base:
    """The copied mission's sides and rules, from its .xyz script."""
    from .missions import _follow, module_code
    made, lists, calls, launch = {}, [], {}, []
    _follow(module_code(raw), made, lists, calls, launch)
    if not launch or not lists:
        raise MissionError("the copied mission has no launch with a list of sides")
    kw = launch[0]
    support: dict = {}
    camps = []
    for i, var in enumerate(lists[0]):
        if var not in calls:
            raise MissionError(f"the copied mission's side {var} isn't made where it can be read")
        func, ckw, _args = calls[var]
        if not (func or "").endswith("VariableCamp"):
            raise MissionError(f"the copied mission's side {var} isn't a VariableCamp")
        values = {k: _value(x, calls, support) for k, x in ckw.items()}
        number = values.get("CampNumber", -1)
        number = number if isinstance(number, int) and not isinstance(number, bool) and number != -1 else i
        ai = values.get("NiveauIA")
        camps.append((var, number, func, values, isinstance(ai, Attr) and ai.path.endswith(".Player")))
    rules = None
    r = kw.get("GameRules")
    if r is not None and r[0] == "name" and r[1] in calls:
        func, rkw, args = calls[r[1]]
        if (func or "").rsplit(".", 1)[-1] in ("GameRulesChallenge", "GameRulesSkirmish") and not args:
            try:
                rules = Call(func, (), sorted((k, _value(x, calls, {})) for k, x in rkw.items()))
            except MissionError:
                rules = None
    pos = kw.get("MapChapterPos")
    return Base(camps, [(k, c) for k, c in support.items() if c is not None], rules,
                pos is not None and not (pos[0] == "const" and pos[1] is None))


# --- the script ---

IMPORTS = ["_enum_for_game_play", "defines.colors", "leveldesign.camera", "leveldesign.camps", "leveldesign.condition",
           "leveldesign.descriptor", "leveldesign.descriptorspecial", "leveldesign.launcheffetmap",
           "leveldesign.operator", "leveldesign.variable", "leveldesignsolo.camps", "leveldesignsolo.condition",
           "leveldesignsolo.contrainte_unit", "leveldesignsolo.descriptor", "leveldesignsolo.fx",
           "leveldesignsolo.helper", "leveldesignsolo.missions", "leveldesignsolo.objectif",
           "leveldesignsolo.production", "leveldesignsolo.strategic_ia", "leveldesignsolo.units", "parametres.Classes"]
CATEGORY = ("IsAttacked IsAvion IsAvionAuSol IsAvionEnVol IsAvionSansMunitionsRestantes IsBatiment IsBatimentFake "
            "IsCamoufle IsEnCombat IsEnForet IsEnSilenceRadio IsEnZoneCombat IsInfanterie IsSelectionnee "
            "IsSousTirArtillerie IsTank IsTruck IsTruckConstruction IsTruckDevise IsUberStress IsUnitFake IsVue").split()


@dataclass
class Context:
    """What the build knows around a mission: the map's name (texts' keys), its kind ("operation" or "campaign"),
    its named points and zones, the camera paths of its camera file, the units placed in each group (names of
    their design items), and the unit classes the game can make."""
    map_name: str
    kind: str
    points: set = field(default_factory=set)
    zones: set = field(default_factory=set)
    rect_zones: set = field(default_factory=set)
    map_paths: set = field(default_factory=set)
    placed: dict = field(default_factory=dict)     # group -> [design item names]
    classes: set | None = None                     # registered unit classes (None: not known, not checked)
    unit_problem: object = None                    # class name -> why the create step can't make it, or None


_KEY_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"


def text_key_name(map_name: str, what: str) -> str:
    """A text's key name (the game packs up to 10 characters into a key, rusemod.dic): "MZ" and 8 characters from a
    hash of the map's name and the text's role, so the same text keeps its key build after build and two maps' never
    meet. (The game's own keys are words like M_D_01 or N_UNI_137.)"""
    import hashlib
    n = int.from_bytes(hashlib.sha1(f"{map_name.lower()}|{what}".encode("utf-8")).digest()[:8], "big")
    out = []
    for _ in range(8):
        out.append(_KEY_CHARS[n % len(_KEY_CHARS)])
        n //= len(_KEY_CHARS)
    return "MZ" + "".join(out)


def problems(m: Mission, base: Base, ctx: Context) -> list:
    """[(level, message)]: "error" stops the build; "warning" says what isn't tried or may not work."""
    out = []
    numbers = {c[1] for c in base.camps}
    player = {c[1] for c in base.camps if c[4]}
    for s in m.sides:
        if s.number not in numbers:
            out.append(("error", f"side {s.number} isn't one of the copied mission's sides ({', '.join(map(str, sorted(numbers)))})"))
        elif s.number in player and s.plays not in (None, "player"):
            # rule: mission-human-sides
            out.append(("error", f"side {s.number} is played by a person in the copied mission: it stays the player's"))
        elif s.number not in player and s.plays == "player":
            # rule: mission-human-sides
            out.append(("error", f"side {s.number} is the computer's in the copied mission: a mission can't add a "
                                 f"human side (the game wants as many as there are players)"))
    goals = {g.id: g for g in m.goals}
    groups = set(ctx.placed) | {a.group for e in m.events for a in e.actions if a.do == "spawn" and a.group}
    cams = {c.name for c in m.cameras} | set(ctx.map_paths)

    def point(name, at):
        if name and name not in ctx.points:
            out.append(("error", f"{at}: {name!r} isn't a named point of the map (add it with Add a name or zone)"))

    def zone(name, at):
        if name and name not in ctx.zones:
            out.append(("error", f"{at}: {name!r} isn't a zone of the map (add a round or square zone)"))
        elif name in ctx.rect_zones:
            out.append(("warning", f"{at}: {name!r} is a square zone; only round zones were tried in a mission yet"))

    def group(name, at):
        if name and name not in groups:
            out.append(("error", f"{at}: no units are ever put in group {name!r} (spawn some into it, or give "
                                 f"placed units that group)"))

    def side(n, at):
        if n is not None and n not in numbers:
            out.append(("error", f"{at}: side {n} isn't one of the mission's sides"))
    if m.opening and m.opening not in cams:
        out.append(("error", f"the opening camera move {m.opening!r} isn't one of the mission's or the map's"))
    if m.opening and m.opening in {c.name for c in m.cameras}:
        out.append(("warning", "a camera move of the mission's own hasn't been tried in the game yet"))
    for g in m.goals:
        at = f"goal {g.id}"
        zone(g.zone, at)
        group(g.group, at)
        point(g.marker, at)
    if m.win == "main_goals" and not any(g.main for g in m.goals):
        out.append(("warning", "no main goal, so the mission is won only by an event's victory"))
    if ctx.kind == "operation" and not any(g.start == "start" for g in m.goals):
        out.append(("warning", "no goal shows at the start: the goals panel the game opens there will be empty"))
    for e in m.events:
        at = f"event {e.id}"
        zone(e.zone, at)
        side(e.side, at)
        group(e.group, at)
        if e.goal and e.goal not in goals:
            out.append(("error", f"{at}: there's no goal {e.goal!r}"))
        if e.repeat:
            out.append(("warning", f"{at}: a repeating event hasn't been tried in the game yet"))
        for k, a in enumerate(e.actions, start=1):
            aat = f"{at}, action {k} ({a.do})"
            side(a.side, aat)
            point(a.at, aat)
            for t in a.to:
                point(t, aat)
            zone(a.zone, aat)
            if a.do != "spawn":
                group(a.group, aat)
            group(a.target, aat)
            if a.do in ("goal", "complete") and a.goal not in goals:
                out.append(("error", f"{aat}: there's no goal {a.goal!r}"))
            if a.do == "goal" and a.goal in goals and goals[a.goal].start != "event":
                out.append(("error", f"{aat}: goal {a.goal!r} already shows at the start (set it to show by an event)"))
            if a.do == "complete" and a.goal in goals and goals[a.goal].done != "event":
                out.append(("error", f"{aat}: goal {a.goal!r} is done by its own rule, not by an event"))
            if a.do == "camera" and a.camera not in cams:
                out.append(("error", f"{aat}: there's no camera move {a.camera!r}"))
            if a.do == "camera" and a.camera in {c.name for c in m.cameras}:
                out.append(("warning", f"{aat}: a camera move of the mission's own hasn't been tried in the game yet"))
            if a.do == "spawn":
                if a.side is None:
                    out.append(("error", f"{aat}: say whose units they are (side)"))
                if ctx.classes is not None and a.unit not in ctx.classes:
                    # rule: mission-unit-class
                    out.append(("error", f"{aat}: {a.unit} isn't a unit class the game knows"))
                why = ctx.unit_problem(a.unit) if callable(ctx.unit_problem) else None
                if why:
                    out.append(("error", f"{aat}: {why}"))
            if a.do in ("ai", "money") and a.do == "ai":
                out.append(("warning", f"{aat}: handing a side to the computer hasn't been tried in our missions yet"))
    for g in m.goals:
        if g.start == "event" and not any(a.do == "goal" and a.goal == g.id for e in m.events for a in e.actions):
            out.append(("warning", f"goal {g.id} shows by an event, but no event shows it"))
        if g.done == "event" and not any(a.do == "complete" and a.goal == g.id for e in m.events for a in e.actions):
            out.append(("warning", f"goal {g.id} is done by an event, but no event completes it"))
        if g.done == "time":
            out.append(("warning", f"goal {g.id}: a goal done after a time hasn't been tried in the game yet"))
    return out


class _Script:
    """The statements being written, each name made once, in an order where nothing is used before it's made."""

    def __init__(self):
        self.defs: list = []
        self.names: set = set()
        self.post: list = []   # PostInit: every reactive block (sides, goals, conditions, variables, groups)
        self.tags: list = []

    def add(self, name: str, v: Call, post=False, tag=False) -> Ref:
        if name not in self.names:
            self.defs.append((name, v))
            self.names.add(name)
            if post:
                self.post.append(Ref(name))
            if tag:
                self.tags.append(Ref(name))
        return Ref(name)


def _clean(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", s)


def _seq(*parts, repeat=False) -> Call:
    return call("leveldesign.descriptor.DescriptorSequential", Repeat=repeat, SubActions=list(parts))


def _sim(*parts) -> Call:
    return call("leveldesign.descriptor.DescriptorSimultaneous", SubActions=list(parts))


def _wait(s: float) -> Call:
    return call("leveldesign.descriptor.DescriptorWaitDuree", Duree=int(s) if float(s).is_integer() else float(s))


def script(m: Mission, base: Base, ctx: Context, keys) -> tuple:
    """(imports, statements, launch name) for the mission; `keys(name) -> int` gives a text's key. The caller has
    checked `problems` for errors."""
    from .dic import name_to_key  # noqa: F401  (keys come from the caller, which uses it)
    sc = _Script()
    victory = (call("leveldesignsolo.objectif.DescriptorDeclencheVictoire", Chapter=1, DeclencheCredits=False,
                    IdMapSoloForLadder=-1) if ctx.kind == "campaign"
               else call("leveldesignsolo.objectif.DescriptorDeclencheVictoireChallenge"))
    defeat = call("leveldesignsolo.objectif.DescriptorDeclencheDefaite")

    def point(name: str) -> Ref:
        return sc.add(f"T_{_clean(name)}", call("leveldesignsolo.helper.TagPosition", name), tag=True)

    def zone(name: str) -> Ref:
        return sc.add(f"Z_{_clean(name)}", call("leveldesignsolo.helper.TagZoneDetection", name), tag=True)
    # the sides: the copied mission's, with the file's changes
    for var, c in base.support:
        sc.add("B_" + var, c)
    by_number = {s.number: s for s in m.sides}
    camps: dict = {}
    for var, number, func, values, is_player in base.camps:
        v = dict(values)
        s = by_number.get(number)
        if s is not None:
            if s.nation:
                v["Nationalite"] = Attr(f"{E}.Nationalite.{NATIONS[s.nation]}")
            if s.difficulty:
                v["Difficulte"] = Attr(f"{E}.TDifficultes.{DIFFICULTIES[s.difficulty]}")
            if s.plays in ("script", "ai") and not is_player:
                v["NiveauIA"] = Attr(f"{E}.NiveauIA.Scripted")
        camps[number] = sc.add(f"SIDE_{number}", Call(func, (), sorted(v.items())), post=True)
    player = next((camps[c[1]] for c in base.camps if c[4]), next(iter(camps.values())))
    rules_kw = dict(base.rules.kwargs) if base.rules is not None else {}
    rules_func = base.rules.func if base.rules is not None else (
        "leveldesign.launcheffetmap.GameRulesSkirmish" if ctx.kind == "campaign"
        else "leveldesign.launcheffetmap.GameRulesChallenge")
    if not rules_kw:  # the copied mission's rules couldn't be read: Anzio's, or COLDITZ CASTLE's (T41)
        rules_kw = dict(_default_rules(ctx.kind))
    if m.time_limit > 0:
        rules_kw["GameTime"] = int(m.time_limit * 60) + 15
        rules_kw["GameTimeMode"] = Attr(f"{E}.TGameTimerMode.Countdown")
    elif "GameTimeMode" in rules_kw:
        rules_kw["GameTime"] = 0
        rules_kw["GameTimeMode"] = Attr(f"{E}.TGameTimerMode.Clock")
    rules = sc.add("RULES", Call(rules_func, (), sorted(rules_kw.items())))
    # the groups: placed units first (their design items' names), then those spawns fill
    groups: dict = {}

    def group(name: str) -> Ref:
        if name not in groups:
            units = [sc.add(f"U_{_clean(n)}", call("leveldesignsolo.helper.TagUnit", n), tag=True)
                     for n in ctx.placed.get(name, [])]
            groups[name] = sc.add(f"G_{_clean(name)}", call("leveldesignsolo.units.VariableUnitGroup", UnitList=units),
                                  post=True)
        return groups[name]

    def flag(name: str) -> tuple:
        """A 0/1 variable and its "it's 1" condition."""
        v = sc.add(f"V_{name}", call("leveldesign.variable.VariableInteger", Value=0), post=True)
        op = sc.add(f"OP_{name}", call("leveldesign.operator.OperatorIntegerStrictlyMore", Value=0, Variable=None))
        c = sc.add(f"C_{name}", call("leveldesign.condition.ConditionVariableInteger", Operator=op, Variable=v),
                   post=True)
        return v, c

    def set_flag(v: Ref) -> Call:
        return call("leveldesign.descriptor.DescriptorSetVariableInteger", Value=1, Variable=v)

    def count_is(g: Ref, gname: str, op_cls: str, value: int, tag: str) -> Ref:
        op = sc.add(f"OP_{tag}", call(f"leveldesign.operator.{op_cls}", Value=value, Variable=None))
        return sc.add(f"C_{tag}", call("leveldesignsolo.condition.ConditionUnitGroup", Operator=op, Variable=g),
                      post=True)

    def in_zone(z: Ref, side: Ref, count: int, tag: str) -> Ref:
        team = sc.add(f"K_TEAM_{tag}", call("leveldesignsolo.contrainte_unit.ContrainteOnUnitTeam", Camp=side,
                                            OperatorType=0))
        kind = sc.add("K_NOT_BUILDINGS", Call("leveldesignsolo.contrainte_unit.ContrainteOnUnitCategory", (),
                                              [(f, f in {"IsBatiment", "IsTruck", "IsTruckConstruction",
                                                         "IsTruckDevise"}) for f in CATEGORY]
                                              + [("MatchType", 2), ("UnitGroup", None)]))
        both = sc.add(f"K_BOTH_{tag}", call("leveldesignsolo.contrainte_unit.ContrainteOnUnitAllContrainte",
                                            ContrainteList=[team, kind]))
        op = sc.add(f"OP_N_{tag}", call("leveldesign.operator.OperatorIntegerMoreOrEqual", Value=count, Variable=None))
        return sc.add(f"C_{tag}", call("leveldesignsolo.condition.ConditionDetectUnitDansZoneDetection",
                                       ComparaisonNbUnits=op, Contrainte=both, Detecteur=z, OrbitIgnore=False),
                      post=True)

    def wait_for(c: Ref) -> Call:
        return call("leveldesign.descriptor.DescriptorWaitCondition", Condition=c)

    def destroyed(gname: str, tag: str) -> list:
        """Wait until group `gname` has had units, then has none."""
        g = group(gname)
        some = count_is(g, gname, "OperatorIntegerMoreOrEqual", 1, f"SOME_{tag}")
        none = count_is(g, gname, "OperatorIntegerEqual", 0, f"NONE_{tag}")
        return [wait_for(some), wait_for(none)]
    # the goals: each a flag its own rule sets, a label and the game's goal block; done, it says so (V_R_<id>) and,
    # a main goal, counts towards the win
    main_count = sum(1 for g in m.goals if g.main)
    v_main = sc.add("V_MAIN", call("leveldesign.variable.VariableInteger", Value=0), post=True) if main_count else None
    goal_units: dict = {}
    goal_blocks: dict = {}
    reported: dict = {}
    for i, g in enumerate(m.goals):
        tag = f"G{i}_{_clean(g.id)}"
        v_done, c_done = flag(f"DONE_{tag}")
        v_rep, c_rep = flag(f"R_{tag}")
        reported[g.id] = (v_rep, c_rep, v_done)
        key = Long(keys(text_key_name(ctx.map_name, f"G_{g.id}")))
        label = sc.add(f"L_{tag}", call(
            "leveldesignsolo.fx.DescriptorDrawLabel", DoesAllFusionnedObjectivesNeedSucces=True, FoldedText=key,
            Group=group(g.group) if g.group and not g.marker else None, HeriteVisibiliteFromUnitGroup=True,
            IdForFusion=0, IsObjectif=True, ListTimers=[], ListTimersForFoldedText=[], ListVariables=[],
            ListVariablesForFoldedText=[], Position=point(g.marker) if g.marker else None,
            Style=0 if g.main else 1, Text=key, VisibleByCamp=None))
        done = [set_flag(v_rep)]
        if g.main and v_main is not None:
            done.append(call("leveldesign.descriptor.DescriptorIncrementeVariableInteger", Value=1, Variable=v_main))
        block = sc.add(f"GOAL_{tag}", call(
            "leveldesignsolo.objectif.DescriptorGereObjectifAvecLabel", ActionsEchec=None,
            ActionsReussi=sc.add(f"DONE_ACTS_{tag}", _seq(*done)), BonusScoreMission=500 if g.main else 250,
            Condition=c_done, ConditionEchec=None, ConditionFin=None, IdForAchievement=0, ImmediateSubActions=False,
            Label=label, LabelsScondaires=[], ShowFailAnimation=False, ShowNewObjectif=True,
            ShowOnMap=bool(g.marker or g.group), TrackingId=_clean(f"{ctx.map_name}_{g.id}")[:60],
            UnitGroupPosition=None), post=True)
        goal_blocks[g.id] = block
        if g.done == "zone":
            watch = [wait_for(in_zone(zone(g.zone), player, 1, f"IN_{tag}")), set_flag(v_done)]
        elif g.done == "destroyed":
            watch = destroyed(g.group, tag) + [set_flag(v_done)]
        elif g.done == "time":
            watch = [_wait(g.seconds), set_flag(v_done)]
        else:  # an event completes it
            watch = None
        goal_units[g.id] = sc.add(f"RUN_{tag}", _sim(block, sc.add(f"WATCH_{tag}", _seq(*watch))) if watch
                                  else _sim(block))
    # the camera moves (the build writes their paths into the map's camera file)

    def camera(name: str, seconds: float) -> Call:
        return call("leveldesign.camera.DescriptorStartCameraPath", AccelerationActivated=True, Action=None,
                    BlackStrips=True, BlackStripsFadeWhenBegin=True, BlackStripsFadeWhenEnd=True,
                    CameraPathName=name, DecelerationActivated=True, StartFromCurrentCameraPosition=False,
                    StopAllUnitOfCampDuJoueur=True, SynchronizeEvents=True,
                    TimeInSecond=int(seconds) if float(seconds).is_integer() else float(seconds))
    cam_seconds = {c.name: c.seconds for c in m.cameras}
    spawned = [0]

    def action(a: Action, tag: str, k: int):
        side = camps.get(a.side) if a.side is not None else player
        if a.do == "message":
            return call("leveldesignsolo.descriptor.DescriptorAfficheHint",
                        Info=Long(keys(text_key_name(ctx.map_name, f"E_{tag}_{k}"))), Pause=False, Time=10)
        if a.do == "spawn":
            spawned[0] += 1
            g = group(a.group) if a.group else sc.add(f"G_SPAWN_{spawned[0]}", call(
                "leveldesignsolo.units.VariableUnitGroup", UnitList=[]), post=True)
            return call("leveldesignsolo.production.DescriptorCreateUnit", Camp=side, Group=g, IsFake=False,
                        IsFakeSelectionnable=False, NbUnit=a.count, Position=point(a.at),
                        TypeUnit=Attr(f"parametres.Classes.{a.unit}"))
        if a.do == "move":  # as Eugen's: the group walks the points in turn, arrows on the map, and then goes on
            return call("leveldesignsolo.missions.DescriptorMove", AfficheFleches=True, Blocking=True,
                        ComportementPolicy=Attr(f"{E}.ComportementAutoPolicy.Declenchement_Immediat"), Force=False,
                        ForceNoRoad=False, ForceRoad=False, Group=group(a.group), GroupSameSpeed=False, Loop=False,
                        MinStressCombat=66, OrderCancelable=False, Positions=[point(t) for t in a.to],
                        WaitForOthers=True)
        if a.do == "attack":
            return call("leveldesignsolo.missions.DescriptorAttack", AttackEnPrioriteUniteNotUbserstress=True,
                        AvionsEnContinu=False, Blocking=False,
                        ComportementPolicy=Attr(f"{E}.ComportementAutoPolicy.Declenchement_Immediat"),
                        DipatchUnitAttaquanteSurLesCibles=True, Group=group(a.group), IgnoreInvisibleUnits=True,
                        MinStressCombat=66, OrderCancelable=False, Targets=group(a.target))
        if a.do == "hold":
            return call("leveldesignsolo.missions.DescriptorDefendZone", AvionsEnContinu=False, Blocking=False,
                        Detecteur=zone(a.zone), ForceIgnoreInvisibleUnits=True, Group=group(a.group),
                        IgnoreBatiments=False, IgnoreInvisibleUnits=True, MinStressCombat=66,
                        MoveWhenNoEnnemies=False, OrderCancelable=False, StopIfNoEnnemies=False)
        if a.do == "artillery":
            return call("leveldesignsolo.missions.DescriptorFrappeArtillerie", Blocking=False, Group=group(a.group),
                        OrderCancelable=False, Position=point(a.at), ToutesLesArtilleries=True)
        if a.do == "bombing":
            return call("leveldesignsolo.missions.DescriptorBombardement", AvionsEnContinu=False, Blocking=False,
                        Group=group(a.group), OrderCancelable=False, Position=point(a.at), TousLesBombardiers=True)
        if a.do == "paradrop":
            return call("leveldesignsolo.missions.DescriptorParachutage", Blocking=True, Group=group(a.group),
                        OrderCancelable=False, Position=point(a.at))
        if a.do == "camera":
            return camera(a.camera, a.seconds or cam_seconds.get(a.camera, 15.0))
        if a.do == "money":
            return call("leveldesignsolo.camps.DescriptorSetRessourceCamp", Camp=side, Quantite=a.amount)
        if a.do == "complete":
            return set_flag(reported[a.goal][2])
        if a.do == "victory":
            return victory
        if a.do == "defeat":
            return defeat
        if a.do == "wait":
            return _wait(a.seconds)
        if a.do == "ai":
            return call("leveldesignsolo.strategic_ia.DescriptorIAAll", Camp=side)
        raise MissionError(f"unknown action {a.do}")

    def run(actions: list, tag: str, k0: int = 1) -> list:
        """The actions in turn; a goal shown runs beside the rest (a goal block lasts until it's done)."""
        out = []
        for k, a in enumerate(actions, start=k0):
            if a.do == "goal":
                rest = run(actions[k - k0 + 1:], tag, k + 1)
                out.append(_sim(goal_units[a.goal], *([_seq(*rest)] if rest else [])))
                return out
            out.append(action(a, tag, k))
        return out
    flows = []
    for i, e in enumerate(m.events):
        tag = f"E{i}_{_clean(e.id)}"
        acts = run(e.actions, _clean(e.id))
        if e.wait:
            acts = [_wait(e.wait)] + acts
        if not acts:
            continue
        if e.when == "start":
            body = acts
        elif e.when == "time":
            body = [_wait(e.at)] + ([sc.add(f"LOOP_{tag}", _seq(*acts, _wait(e.repeat), repeat=True))]
                                   if e.repeat else acts)
        elif e.when == "zone":
            side = camps.get(e.side) if e.side is not None else player
            body = [wait_for(in_zone(zone(e.zone), side, e.count, f"IN_{tag}"))] + acts
        elif e.when == "destroyed":
            body = destroyed(e.group, tag) + acts
        else:  # goal
            body = [wait_for(reported[e.goal][1])] + acts
        flows.append(sc.add(f"EVENT_{tag}", _seq(*body)))
    # the win and the clock
    if m.win == "main_goals" and main_count:
        op = sc.add("OP_ALL_MAIN", call("leveldesign.operator.OperatorIntegerMoreOrEqual", Value=main_count,
                                        Variable=None))
        c_all = sc.add("C_ALL_MAIN", call("leveldesign.condition.ConditionVariableInteger", Operator=op,
                                          Variable=v_main), post=True)
        flows.append(sc.add("WIN", _seq(wait_for(c_all), _wait(5), victory)))
    if m.time_limit > 0 and m.time_up != "nothing":
        flows.append(sc.add("TIME_UP", _seq(_wait(m.time_limit * 60), victory if m.time_up == "victory" else defeat)))
    # the goals shown at the start, and the goals panel a second after them (an Operation's panel holds Escape until
    # it's closed, and lists only the goals already going: T41, from the game's code)
    first = [goal_units[g.id] for g in m.goals if g.start == "start"]
    panel = sc.add("PANEL", call("leveldesignsolo.objectif.DescriptorObjectifsPanel",
                                 ObjectifsList=[goal_blocks[g.id] for g in m.goals if g.start == "start"]))
    after = sc.add("PANEL_AFTER", call("leveldesign.descriptor.DescriptorPlayEffetAfterWait", Action=panel, Duree=1))
    # the start, as the shipped Operations: money, the loading's end (with the opening camera move beside it),
    # sound, the HUD, the computer sides that play the whole map, then the ready flag the rest waits on
    v_ready, c_ready = flag("READY")
    start = []
    for s in m.sides:
        if s.money is not None and s.number in camps:
            start.append(call("leveldesignsolo.camps.DescriptorSetRessourceCamp", Camp=camps[s.number],
                              Quantite=s.money))
    loading = call("leveldesign.descriptor.DescriptorLoadingDone")
    start.append(_sim(camera(m.opening, cam_seconds.get(m.opening, 18)), loading) if m.opening else loading)
    start.append(call("leveldesign.descriptorspecial.DescriptorInitSoundAndMusic", Acknow2Ds=True, Acknow3Ds=True,
                      Ambience=True, MusicAuto=True))
    start.append(call("leveldesign.camps.DescriptorHudElementsVisibility", AlertMessages=True, BluffMenu=True,
                      BuildMenu=True, Devises=True, EtiquettesJoueurs=True, FastStrike=False, Highlight=True,
                      PadInfos=True, RuseZones=True, Score=True, ScoreAdverse=True, Selection=True,
                      SituationAwareness=True, TimeRemaining=True, UnitHints=True))
    for s in m.sides:
        if s.plays == "ai" and s.number in camps:
            start.append(call("leveldesignsolo.strategic_ia.DescriptorIAAll", Camp=camps[s.number]))
    start.append(call("leveldesign.descriptor.DescriptorIncrementeVariableInteger", Value=1, Variable=v_ready))
    begin = sc.add("START", _seq(*start))
    main = sc.add("MAIN", _seq(wait_for(c_ready), _sim(*first, after, *flows)))
    root = sc.add("ROOT", _sim(begin, main))
    chpos = sc.add("CHPOS", call("leveldesign.variable.VariableInteger", Value=0), post=True) \
        if base.chapter_pos or ctx.kind == "campaign" else None
    sc.add("ER_MISSION", call("leveldesign.launcheffetmap.DescriptorLaunchEffetMap",
                              CampList=[camps[c[1]] for c in base.camps], CampaignInfo=None, EffetMap=root,
                              GameRules=rules, MapChapterPos=chpos, UnitToSpawnList=[], PostInit=list(sc.post),
                              TagList=list(sc.tags)))
    return IMPORTS, sc.defs, "ER_MISSION"


def _default_rules(kind: str) -> list:
    """The rules when the copied mission's can't be read: Anzio's (an Operation) or COLDITZ CASTLE's (a chapter)."""
    if kind == "campaign":
        return [("AltitudeCamera", 1), ("AzimutCamera", 0), ("ConstructionNecessiteHQ", True), ("DefaiteArmy", False),
                ("DisableBazooka", False), ("DisableCapture", False), ("DisableUnableToHide", False),
                ("DureeCamera", 0), ("Fow", 1), ("GameTime", 0), ("GameTimeMode", Attr(f"{E}.TGameTimerMode.Clock")),
                ("GameType", 0), ("IsMapMulti", False), ("IsTestStandard", False), ("MaxScore", 1000000),
                ("MaxScoreVictory", False), ("MinScore", 0), ("MinScoreDefeat", False), ("ModeFixedRandomSeed", True),
                ("PopCapLimit", Attr(f"{E}.TPopCapConfig.PopCapSolo")), ("ScoreIgnoreCapture", False),
                ("SiteCamera", 0), ("TeleportCameraHQ", False), ("UseScore", True)]
    return [("AlliancesSharingMoney", []), ("AltitudeCamera", 1), ("AzimutCamera", 0),
            ("ConstructionNecessiteHQ", True), ("DisableBazooka", False), ("DisableCapture", False),
            ("DureeCamera", 0), ("Fow", 1), ("GameTime", 3600), ("GameTimeMode", Attr(f"{E}.TGameTimerMode.Countdown")),
            ("IsMapMulti", False), ("MaxScore", 1000), ("MinScore", -1000), ("ModeFixedRandomSeed", True),
            ("PopCapLimit", Attr(f"{E}.TPopCapConfig.PopCapSolo")), ("ScoreIgnoreCapture", False), ("SiteCamera", 0),
            ("TeleportCameraHQ", False), ("UseScore", True)]


def texts(m: Mission, map_name: str) -> dict:
    """{text key name: Words}: every goal's and message's words."""
    out = {}
    for g in m.goals:
        out[text_key_name(map_name, f"G_{g.id}")] = g.text
    for e in m.events:
        tag = _clean(e.id)
        k = 1
        for a in e.actions:
            if a.do == "message" and a.text is not None:
                out[text_key_name(map_name, f"E_{tag}_{k}")] = a.text
            k += 1
    return out


def camera_keys(c: Camera) -> list:
    """[(point, unit direction towards its look spot)] for a camera move's path."""
    out = []
    for p in c.points:
        d = tuple(c.look[i] - p[i] for i in range(3))
        n = math.sqrt(sum(v * v for v in d)) or 1.0
        out.append((p, tuple(v / n for v in d)))
    return out
