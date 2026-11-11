"""Which of a unit's own animations each of its actions plays: one rule, used by the Studio's page (the action table,
ruse_studio.actions) and by the build (rusemod.build.unit_own_clips), so what the page says is what the game plays.

A unit with a model on bones of its own brings the model's animations with it (Import model; files/anim/units.toml's
[unit.<name>.animation] table, rusemod.anim). The game asks a unit's figures for clips by action: each figure lists
its clips by an action's name (its ResourceAnimation): a soldier's come in pairs, t_<action> for the top half of the
body and b_<action> for the bottom half, played at once, each through its own mask (rusemod.unitmodel.halves); the
far-zoom figure adds <action>_replacement ones; a gun's crew and a vehicle's people have names of their own (idle1,
walkingfront, stand, move...). The ride is the unit's own on long moves (the build's ride unit, drawn as the model
playing one animation on a loop: the 2026-11-09 Horse Squad's way). The page shows one row an action (its t_, b_ and
far-zoom listings together), and the modder picks one of the model's animations for it or leaves it on Nearest.

THE RULE: a listing plays, in this order,
  1. the animation picked for its action (both halves);
  2. else the animation named for it: its own name (t_course, course, or the name of the game's clip it played,
     fusilier_course), else a name that says what the action does: words for the kind of action (stand or idle, walk,
     run or gallop, aim, fire or shoot, throw or grenade, reload, hit, die or death, flee...), with the words for its
     way (back or backwards, left, right, explosion or blast, bazooka or special) and its number (run 2) when it has
     them (KINDS, WAYS). Only an animation made for that half of the body counts: one whose name starts t_ (or top_)
     is the top half's, b_ (or bottom_) the bottom half's, after what all the model's names start with (hr_t_stand,
     hr_b_run: the 2026-11-09 Horse Squad's rider and horse), any other is the whole body's;
  3. else, the same way, what the next action on its line plays (ACTIONS' lines: a walk plays the run, a run the
     walk, then the stand; a fire the aim, then the stand; a death of another kind the plain death, then the
     stand...). The top half of an action done while aiming (walks aiming) plays an aim only when the model has one
     picked or named for it, else the moving; its bottom half does the moving, as the game's own soldiers do (their
     t_marche_vise plays the standing aim, b_marche_vise the walk);
  4. else the model's first animation (for that half).
The least a model needs is a stand, a walk and a run (NEEDED; the owner's settled answer, 2026-11-10): the page names
any of the three that has nothing picked or named for it."""
from __future__ import annotations

import os
import re

NEEDED = ("stand", "marche", "course")   # stand, walk, run: what the 2026-11-09 horse's own body had
RIDE = "ride"                            # the unit's own ride on long moves (rusemod.build: its looping animation)
HALVES = {"t_": "top", "b_": "bottom"}
SECTIONS = ("stand", "move", "fight", "special", "hit", "die", "para", "crew", "ride", "other")

# what an animation's name says it is: the first kind whose words it has, in this order (a "death shot" is a death)
KINDS = (
    ("fallen", "fallen corpse lying"),
    ("die", "die dies dying death deaths dead mort killed"),
    ("hit", "hit hits hurt hurts damage damaged pain flinch impact"),
    ("reload", "reload reloads reloading recharge"),
    ("throw", "throw throws throwing grenade grenades toss lob secondaire"),
    ("fire", "fire fires firing shoot shoots shooting shot tir attack attacks attacking"),
    ("raise", "raise raises raising draw"),
    ("lower", "lower lowers lowering holster"),
    ("aim", "aim aims aiming vise ready"),
    ("flee", "flee flees fleeing rout routs routing panic deroute retreat"),
    ("ride", "ride rides riding"),
    ("run", "run runs running gallop gallops galloping sprint sprints sprinting trot trots trotting canter cantering "
            "course jog jogging charge"),
    ("walk", "walk walks walking marche step steps stroll move moves moving"),
    ("crouch", "crouch crouches crouching crouched kneel kneels kneeling accroupi"),
    ("look", "look looks looking"),
    ("jump", "jump jumps jumping deploy"),
    ("fall", "fall falls falling chute"),
    ("fly", "fly flies flying float floats floating glide gliding vol parachute"),
    ("land", "land lands landing"),
    ("stand", "stand stands standing idle idles idling still rest resting wait waits waiting breathe breathing stay"),
)
MOVING = ("walk", "run", "crouch")   # kinds that also say the way of an aim (an "aim walk" is aiming while walking)
WAYS = (
    ("back", "back backs backward backwards behind reverse arriere dos"),
    ("left", "left gauche"),
    ("right", "right droite"),
    ("blast", "explosion explosions explode blast bomb"),
    ("special", "special bazooka rocket launcher panzerschreck piat"),
    ("hard", "violent violente hard"),
)
_KIND_OF = {w: k for k, words in KINDS for w in words.split()}
_WAY_OF = {w: k for k, words in WAYS for w in words.split()}
_ORDER = {k: i for i, (k, _w) in enumerate(KINDS)}

# every action the game's figures list: (its section on the page, the names that say it ("kind way way|kind..."),
# its number (a second or third way of doing it), its line (the next nearest actions; "!x": x only when the model has
# an animation picked or named for x), the top half's line when the halves differ)
ACTIONS = {
    # standing still
    "stand": ("stand", "stand", 0, ""),
    "accroupi": ("stand", "crouch", 0, "stand"),
    "look_around": ("stand", "look", 0, "stand"),
    # moving
    "marche": ("move", "walk", 0, "course stand"),
    "marche_arriere": ("move", "walk back", 0, "marche"),
    "course": ("move", "run", 0, "marche stand"),
    "course2": ("move", "run", 2, "course"),
    "course3": ("move", "run", 3, "course"),
    "course_droite": ("move", "run right", 0, "course"),
    "course_gauche": ("move", "run left", 0, "course"),
    "course_arriere": ("move", "run back", 0, "!marche_arriere course"),
    "deroute": ("move", "flee", 0, "course"),
    "deroute2": ("move", "flee", 2, "deroute"),
    "deroute3": ("move", "flee", 3, "deroute"),
    # aiming and firing
    "stand_vise": ("fight", "aim", 0, "stand"),
    "accroupi_vise": ("fight", "aim crouch", 0, "accroupi", "!stand_vise accroupi"),
    "marche_vise": ("fight", "aim walk", 0, "marche", "!stand_vise marche"),
    "marche_arriere_vise": ("fight", "aim walk back", 0, "marche_arriere", "!stand_vise marche_arriere"),
    "course_vise": ("fight", "aim run", 0, "course", "!stand_vise course"),
    "course_droite_vise": ("fight", "aim run right", 0, "course_droite", "!stand_vise course_droite"),
    "course_gauche_vise": ("fight", "aim run left", 0, "course_gauche", "!stand_vise course_gauche"),
    "course_arriere_vise": ("fight", "aim run back", 0, "course_arriere", "!stand_vise course_arriere"),
    "tir": ("fight", "fire", 0, "stand_vise"),
    "tir_secondaire": ("fight", "throw", 0, "tir"),
    "tir_secondaire2": ("fight", "throw", 2, "tir_secondaire"),
    "tir_secondaire3": ("fight", "throw", 3, "tir_secondaire"),
    "recharge": ("fight", "reload", 0, "stand"),
    # the heavy weapon (a bazooka man's)
    "stand_vise_special": ("special", "aim special", 0, "stand_vise"),
    "course_vise_special": ("special", "aim run special", 0, "course", "!stand_vise_special !stand_vise course"),
    "course_droite_vise_special": ("special", "aim run right special", 0, "course_droite",
                                   "!stand_vise_special !stand_vise course_droite"),
    "course_gauche_vise_special": ("special", "aim run left special", 0, "course_gauche",
                                   "!stand_vise_special !stand_vise course_gauche"),
    "course_arriere_vise_special": ("special", "aim run back special", 0, "course_arriere",
                                    "!stand_vise_special !stand_vise course_arriere"),
    "tir_special": ("special", "fire special", 0, "tir"),
    "transition_to_special": ("special", "raise special|raise", 0, "stand_vise_special"),
    "transition_from_special": ("special", "lower special|lower", 0, "stand_vise_special"),
    # getting hit
    "hit": ("hit", "hit", 0, "stand"),
    "hit_dos": ("hit", "hit back", 0, "hit"),
    "hit_explosion": ("hit", "hit blast", 0, "hit"),
    # dying
    "mort_balle": ("die", "die", 0, "stand"),
    "mort_balle_violente": ("die", "die hard", 0, "mort_balle"),
    "mort_balle_dos": ("die", "die back", 0, "mort_balle"),
    "mort_explosion": ("die", "die blast", 0, "mort_balle"),
    "mort_explosion_dos": ("die", "die blast back", 0, "mort_explosion"),
    "mort": ("die", "fallen", 0, "mort_balle"),
    # parachuting
    "deploy": ("para", "jump", 0, "chute"),
    "chute": ("para", "fall", 0, "stand"),
    "vol": ("para", "fly", 0, "chute"),
    "land": ("para", "land", 0, "stand"),
    # a gun's crew, a vehicle's people
    "move": ("crew", "walk", 0, "marche"),
    "fire": ("crew", "fire", 0, "tir"),
    "idle1": ("crew", "stand", 0, "stand"),
    "idle2": ("crew", "stand", 2, "idle1"),
    "walkingfront": ("crew", "walk", 0, "marche"),
    "walkingback": ("crew", "walk back", 0, "marche_arriere"),
    "gotogun": ("crew", "", 0, "stand"),
    "gotowalk": ("crew", "", 0, "stand"),
    "morphin": ("crew", "", 0, "stand"),
    "morphout": ("crew", "", 0, "stand"),
    "reload": ("crew", "reload", 0, "recharge"),
    # its own ride on long moves
    RIDE: ("ride", "ride", 0, "course"),
}
_REPLACEMENT = re.compile(r"_replacement(?:_\d+)?$")


def parse_key(key: str) -> tuple[str | None, str]:
    """A listing's action name as (the half it plays: "top", "bottom" or None for the whole figure, the action the
    page names): "t_course_vise" -> ("top", "course_vise"), "t_tir_replacement" -> ("top", "tir"), "idle1" ->
    (None, "idle1")."""
    k = str(key).strip().lower()
    half = HALVES.get(k[:2])
    if half:
        k = k[2:]
    return half, _REPLACEMENT.sub("", k)


def _norm(name: str) -> str:
    """A name as names are compared: lower case, words joined by _, no lod0 at the end."""
    n = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
    return re.sub(r"_?lod0$", "", n)


def tokens(name: str) -> list[str]:
    """An animation's name in words: "Horse_Run2" -> horse, run, 2; "RiderFireLeft" -> rider, fire, left."""
    s = re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", str(name))
    return [t for t in re.split(r"[^a-z0-9]+", s.lower()) if t]


def says(name: str) -> tuple[str | None, frozenset, int]:
    """What an animation's name says it is: (its kind or None, its ways, its number: 0 for the first or only one)."""
    words = tokens(name)
    kinds = sorted({_KIND_OF[w] for w in words if w in _KIND_OF}, key=_ORDER.get)
    kind = kinds[0] if kinds else None
    ways = {_WAY_OF[w] for w in words if w in _WAY_OF} | {k for k in kinds[1:] if k in MOVING}
    numbers = [int(w) for w in words if w.isdigit()]
    n = numbers[0] if numbers else 0
    return kind, frozenset(ways), 0 if n == 1 else n


def _signatures(base: str) -> list[tuple[str, frozenset]]:
    spec = ACTIONS.get(base)
    if spec is None or not spec[1]:
        return []
    out = []
    for sig in spec[1].split("|"):
        words = sig.split()
        out.append((words[0], frozenset(words[1:])))
    return out


def _line(base: str, half: str | None) -> list[tuple[str, bool]]:
    """(action, only when picked or named) of an action's line for that half."""
    spec = ACTIONS.get(base)
    if spec is None:
        return [("stand", False)] if base != "stand" else []
    text = spec[4] if half == "top" and len(spec) > 4 else spec[3]
    return [(w.lstrip("!"), w.startswith("!")) for w in text.split()]


HALF_MARKS = (("t_", "top"), ("top_", "top"), ("upper_", "top"), ("b_", "bottom"), ("bottom_", "bottom"),
              ("lower_", "bottom"))


def marked(names: list) -> dict:
    """{name: (its core, the half it's made for or None)} for a model's animation names: what all of them start with
    dropped (hr_ of hr_t_stand, hr_b_run, hr_ride), then a half's mark at the start (t_ or top_ for the top half, b_
    or bottom_ for the bottom one: the game's own way, t_stand and b_stand). A name made for one half plays on that
    half only (the owner's 2026-11-09 Horse Squad: the rider's clips on top, the horse's below)."""
    norms = {n: _norm(n) for n in names}
    prefix = os.path.commonprefix(list(norms.values())) if len(norms) > 1 else ""
    prefix = prefix[:prefix.rfind("_") + 1]
    out = {}
    for n, x in norms.items():
        core, half = x[len(prefix):] or x, None
        for mark, h in HALF_MARKS:
            if core.startswith(mark) and len(core) > len(mark):
                core, half = core[len(mark):], h
                break
        out[n] = (core, half)
    return out


def named(base: str, names: list, key: str | None = None, clip: str | None = None, half: str | None = None,
          marks: dict | None = None) -> str | None:
    """The model's animation named for the action `base` (rule 2), or None, of those made for the listing's `half`
    (or for the whole body): one called by the listing's name (`key`: t_course), the action's (course), or the game's
    clip it played (`clip`: fusilier_course, or course), else the first whose name says the action's kind, ways and
    number."""
    marks = marks if marks is not None else marked(names)
    fit = [n for n in names if marks[n][1] in (None, half)]
    if half is None:   # (a whole figure, its ride: one made for a half after those for the whole body)
        fit += [n for n in names if marks[n][1] is not None]
    wanted = {_norm(x) for x in (key, base, f"fusilier_{base}", clip) if x}
    if clip:
        wanted.add(re.sub(r"^fusilier_", "", _norm(clip)))
    for n in fit:
        if _norm(n) in wanted or marks[n][0] in wanted:
            return n
    sigs = _signatures(base)
    if not sigs:
        return None
    number = ACTIONS[base][2]
    said = {n: says(n) for n in fit}
    for kind, ways in sigs:
        for n in fit:
            k, w, num = said[n]
            if k == kind and w == ways and num == number:
                return n
    return None


def choose(key: str, names: list, picks: dict | None = None, clip: str | None = None) -> tuple[str | None, str]:
    """The animation the listing `key` plays (THE RULE), of the model's `names` (in the model's order), `picks`
    {action: animation} the modder's, `clip` the game's clip the listing played (its file name). Returns (the
    animation, how: "picked", "named" or "nearest"); (None, "none") for a model with no animations."""
    names = list(names)
    if not names:
        return None, "none"
    picks = {a: n for a, n in (picks or {}).items() if n in names}
    half, base = parse_key(key)
    if base in picks:
        return picks[base], "picked"
    marks = marked(names)
    got = named(base, names, str(key).lower() if key else None, _stem(clip), half, marks)
    if got is not None:
        return got, "named"
    seen: set = set()

    def walk(action: str, strict: bool) -> str | None:
        if (action, strict) in seen:
            return None
        seen.add((action, strict))
        if action in picks:
            return picks[action]
        found = named(action, names, half=half, marks=marks)
        if found is not None or strict:
            return found
        for nxt, only in _line(action, half):
            found = walk(nxt, only)
            if found is not None:
                return found
        return None

    for nxt, only in _line(base, half):
        got = walk(nxt, only)
        if got is not None:
            return got, "nearest"
    return next((n for n in names if marks[n][1] in (None, half)), names[0]), "nearest"   # (rule 4)


def _stem(clip: str | None) -> str | None:
    """The game's clip a listing played, as a name to match: "WW2\\...\\Fusilier_courselod0.Ase2NdfBin" ->
    fusilier_course."""
    if not clip:
        return None
    return _norm(str(clip).replace("/", "\\").rsplit("\\", 1)[-1].rsplit(".", 1)[0])


def section(base: str) -> str:
    spec = ACTIONS.get(base)
    return spec[0] if spec else "other"


def table(listings: list, names: list, picks: dict | None = None) -> list[dict]:
    """The page's rows for a unit's `listings` [(figure path, action name, the game's clip it plays or None)]: one an
    action, in ACTIONS' order (actions the game lists that aren't there after, by name), each {"action", "section",
    "picked": the animation picked or None, "plays": {"top"/"bottom"/"all": animation}, "how": "picked", "named" or
    "nearest" (the best of its halves': a horse's own walk below its rider's nearest on top is a walk of its own),
    "keys": how many listings it covers}."""
    picks = {a: n for a, n in (picks or {}).items() if n in names}
    first: dict = {}   # action -> {half: (key, clip)}: the first figure's listing of each half
    count: dict = {}
    for _path, key, clip in listings:
        half, base = parse_key(key)
        count[base] = count.get(base, 0) + 1
        first.setdefault(base, {}).setdefault(half or "all", (key, clip))
    order = {a: i for i, a in enumerate(ACTIONS)}
    rows = []
    for base in sorted(first, key=lambda a: (order.get(a, len(order)), a)):
        plays, hows = {}, {}
        for half, (key, clip) in sorted(first[base].items(), key=lambda kv: ("top", "all", "bottom").index(kv[0])):
            plays[half], hows[half] = choose(key, names, picks, clip)
        how = next(h for h in ("picked", "named", "nearest", "none") if h in hows.values())
        rows.append({"action": base, "section": section(base), "picked": picks.get(base), "plays": plays,
                     "how": how, "keys": count[base]})
    return rows


def missing(rows: list[dict]) -> list[str]:
    """Of NEEDED, the actions the rows have that nothing is picked or named for (each plays the nearest)."""
    have = {r["action"]: r for r in rows}
    return [a for a in NEEDED if a in have and have[a]["how"] == "nearest"]


def ride(names: list, picks: dict | None = None) -> tuple[str | None, str]:
    """The animation the unit's own ride plays on a loop, and how (choose)."""
    return choose(RIDE, names, picks)
