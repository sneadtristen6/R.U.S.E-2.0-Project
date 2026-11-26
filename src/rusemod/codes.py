"""The failure codes Bug Watch sends (the owner's ask of 2026-11-24, "our studio and launcher should be giving us proper
code so that the bug watch is super effective", and his answers of 2026-11-26, B6 B to B11 B): one code for each
distinct failure a player can meet, kept in codes.toml beside this file, the one list of them.

A code is <AREA>-<NN>: PLAY (a Play or a Test in game, the copy built, the game started), SET (the Launcher's mod sets),
LIST (the mod list), UPD (the apps' update check), SIGN (sign-in through Steam), CRASH (the game's end, after a Play or
a Test in game), TST (the Studio's Test in game), PAGE (a page's own script); PASS (why a sign-in pass doesn't check
out) and OWN (why a game folder isn't confirmed as an owned copy) only ever say why, inside another code. BLD-<NNN> is
a check a build makes. The app that sends a code puts its letter in front (wire): L for the Launcher, S for the Studio. A
code of our shared code (rusemod) has one number in both apps: L-PLAY-08 from a Play, S-PLAY-08 from a Test in game; a
BLD code goes as it is.

codes.toml says, for each code, where it is (`place`: the module and the function, never a line), the key Bug Watch got
for it before (`old`; for a build check's code, `check`: the rusemod.checkkeys key it stands for, which a build failure
is still counted by beside it), the release it came in (`since`) and, for a code given by hand, what it is (`what`). A
code given in the code itself is written there as a string (coded(error, "SET-08"), failure("LIST-01")); a code for a
whole window call (`calls`), any of its failures that no other code says. A number is never given twice: a code whose
place is gone stays in the file, marked `gone`. tests/test_codes.py keeps the file and the code in step; write() gives
each new build check its BLD code.

The code travels on the error (coded: attributes only, so what the player reads and what the code does stay as they
were); a failure that is no error (a sign-in answer, a mod list that couldn't be had, a game that ended badly) is
counted where it happens (rusemod.bugwatch.failure). Only codes and numbers leave the PC, and only under the agreement
version that describes them (rusemod.bugwatch.CODES_AGREEMENT)."""
from __future__ import annotations

import ast
import json
import re
import tomllib
from functools import lru_cache
from pathlib import Path

FILE = Path(__file__).with_name("codes.toml")
ROOT = Path(__file__).parents[1]  # the folder holding rusemod, ruse_studio and ruse_launcher
AREAS = ("PLAY", "SET", "LIST", "UPD", "SIGN", "PASS", "OWN", "CRASH", "TST", "PAGE", "BLD")
CODE = re.compile(r"(?:PLAY|SET|LIST|UPD|SIGN|PASS|OWN|CRASH|TST|PAGE)-\d{2}|BLD-\d{3}")
SINCE = "0.9.8.23/0.4.8.23"  # the release a new code comes in (Studio/Launcher): the one after 0.9.8.22/0.4.8.22
LETTER = {"launcher": "L", "studio": "S"}  # the app that sends a code puts its letter in front (wire)
PACKAGES = ("rusemod", "ruse_studio", "ruse_launcher")  # where codes are given (the engine is LittleGroove's own)
APIS = {"launcher": "ruse_launcher/api.py", "studio": "ruse_studio/api.py"}  # where a code for a window call lives
FIELDS = ("place", "old", "check", "calls", "what", "since", "gone")


# --- on an error, and at run time -------------------------------------------------------------------------------
def coded(error, code: str, **detail):
    """`error` carrying a failure's code for Bug Watch, and its numbers (`detail`: n a count, win a Windows error
    number, http a web server's answer, exit the game's exit number, why another code), returned so it can be raised:
    `raise coded(BuildError(...), "BLD-412") from None`. Attributes only: what the player reads and what the code
    does stay as they were. A code the error carried already (from deeper down) becomes the `why` of the new one."""
    if not code:
        return error
    try:
        old = getattr(error, "bw_code", "")
        kept = dict(getattr(error, "bw_detail", None) or {})
        if old and old != code:
            kept.setdefault("why", old)
        kept.update({k: v for k, v in detail.items() if v is not None and v != ""})
        error.bw_code, error.bw_detail = code, kept
    except (AttributeError, TypeError):  # an error that takes no attributes: no code, never a failure of its own
        pass
    return error


def code_of(error) -> str:
    """A failure's code: the one its error carries (coded), else the code of the build check that refused
    (rusemod.checkkeys: its key's BLD code), else "". An error of Python's own (a KeyError, an OSError) is no check's
    refusal: its words get a check's code only from a text with words of its own, never from one that is only blanks
    ("{0}", which any words fit)."""
    code = getattr(error, "bw_code", "") if error is not None else ""
    if isinstance(code, str) and code:
        return code
    if error is None:
        return ""
    try:
        from .checkkeys import MIN_OWN, check_of, where_of
        least = MIN_OWN if type(error).__module__ == "builtins" else 0
        return bld_of(check_of(str(error), where_of(error), least=least))
    except Exception:  # noqa: BLE001 - a code is never worth stopping the app for
        return ""


def finding_code(finding) -> str:
    """A build's listed mistake by its code: the one of the error it was made from (rusemod.patch.Finding.code), else
    its check's BLD code (rusemod.checkkeys.finding_key), else ""."""
    code = getattr(finding, "code", "")
    if isinstance(code, str) and code:
        return code
    try:
        from .checkkeys import finding_key
        return bld_of(finding_key(finding)[0])
    except Exception:  # noqa: BLE001 - a code is never worth stopping the app for
        return ""


def bld_of(check: str) -> str:
    """The BLD code of a build check's key (rusemod.checkkeys), else ""."""
    return _entries()["check"].get(check, "") if check else ""


def for_call(app: str, name: str) -> str:
    """The code codes.toml gives a whole window call of `app` (`calls`): for its failures no other code says."""
    return _entries()["call"].get((app, name), "")


def wire(code: str, app: str) -> str:
    """A code as `app` sends it: its letter in front (L-PLAY-08, S-PLAY-08), a BLD code as it is; "" for no code."""
    if not isinstance(code, str) or not CODE.fullmatch(code):
        return ""
    letter = LETTER.get(app)
    return code if code.startswith("BLD-") or not letter else f"{letter}-{code}"


def read(path: Path = FILE) -> dict:
    try:
        return tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def app_of(place: str) -> str:
    """The app a place is in ("launcher.api.play": "launcher"), "" for our shared code."""
    head = str(place or "").split(".")[0]
    return head if head in LETTER else ""


@lru_cache(maxsize=2)
def _table(path: str, stamp: float) -> dict:
    out: dict = {"check": {}, "call": {}}
    for code, e in read(Path(path)).items():
        if not isinstance(e, dict) or e.get("gone") or not CODE.fullmatch(code):
            continue
        if e.get("check"):
            out["check"].setdefault(str(e["check"]), code)
        for name in e.get("calls") or []:
            out["call"][(app_of(e.get("place", "")), str(name))] = code
    return out


def _entries() -> dict:
    try:
        return _table(str(FILE), FILE.stat().st_mtime)
    except OSError:
        return {"check": {}, "call": {}}


# --- the file and the code in step (the test and write(); the apps only read the file) ---------------------------
def short(module: str) -> str:
    """A module's name as a place says it: "build" for rusemod.build, "launcher.api", "studio.api"."""
    for long, brief in (("rusemod.", ""), ("ruse_studio.", "studio."), ("ruse_launcher.", "launcher."),
                        ("ruse_mod_engine.", "engine.")):
        if module.startswith(long):
            return brief + module[len(long):]
    return module


def _module_of(path: Path, root: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


class _Finder(ast.NodeVisitor):
    def __init__(self, module: str):
        self.module, self.defs, self.found = module, [], []

    def visit_FunctionDef(self, node):
        self.defs.append(node.name)
        self.generic_visit(node)
        self.defs.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Constant(self, node):
        if isinstance(node.value, str) and CODE.fullmatch(node.value):
            where = ".".join(self.defs[-2:]) if self.defs else "<module>"
            self.found.append((node.value, f"{short(self.module)}.{where}", node.lineno))


def found_in_code(root: Path = ROOT) -> dict[str, list[tuple[str, int]]]:
    """{code: [(its place, line)...]} for every code written in our code: a string that is a code, by the module and
    the function it is in ("launcher.api._check_mods"; a module's "<module>" outside any function)."""
    out: dict[str, list] = {}
    for package in PACKAGES:
        for p in sorted((Path(root) / package).rglob("*.py")):
            if "__pycache__" in p.parts or "python251" in p.parts:
                continue
            finder = _Finder(_module_of(p, Path(root)))
            finder.visit(ast.parse(p.read_text(encoding="utf-8")))
            for code, place, line in finder.found:
                out.setdefault(code, []).append((place, line))
    return out


def _build_checks() -> dict[str, str]:
    """{check: its place} of every build check in checkkeys.toml (the apps' own steps before a build have codes of
    their own: PLAY, TST)."""
    from .checkkeys import read as checks
    out = {}
    for e in checks().values():
        where = str(e.get("where", ""))
        if e.get("check") and not where.startswith(("ruse_studio.", "ruse_launcher.")):
            module, _, func = where.partition(":")
            out.setdefault(str(e["check"]), f"{short(module)}.{func}")
    return out


def _methods(root: Path, app: str) -> set[str]:
    tree = ast.parse((Path(root) / APIS[app]).read_text(encoding="utf-8"))
    return {n.name for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body
            if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")}


def stale(path: Path = FILE, root: Path = ROOT) -> list[str]:
    """What the test checks, said plainly: a code in the code that the file hasn't, or names in another place, or
    writes twice; a code in the file the code doesn't give (and not marked gone); a build check with no BLD code, or a
    BLD code whose check is gone; an entry missing what every entry says; a window call that isn't there."""
    have, found, out = read(path), found_in_code(root), []
    for code, places in found.items():
        e = have.get(code)
        if e is None:
            out.append(f"not in codes.toml: {code} ({places[0][0]} line {places[0][1]})")
            continue
        if e.get("gone"):
            out.append(f"{code} is marked gone, but the code still gives it ({places[0][0]})")
        if len(places) > 1:
            out.append(f"{code} is written in more than one place: " + ", ".join(f"{p} line {n}" for p, n in places))
        out += [f"{code} is in {p} (line {n}), codes.toml says {e.get('place')}" for p, n in places
                if p != e.get("place")]
    checks = _build_checks()
    given: dict[str, str] = {}
    for code, e in have.items():
        if not CODE.fullmatch(code) or not isinstance(e, dict):
            out.append(f"not a code: {code}")
            continue
        for field in ("place", "since"):
            if not isinstance(e.get(field), str) or not e.get(field):
                out.append(f"{code} has no {field}")
        if e.get("gone"):
            continue
        if e.get("check"):
            check = str(e["check"])
            if not code.startswith("BLD-"):
                out.append(f"{code} stands for a build check, so it is a BLD code")
            if check not in checks:
                out.append(f"{code}: the check {check} isn't in checkkeys.toml any more: run rusemod.codes.write()")
            elif given.setdefault(check, code) != code:
                out.append(f"{check} has two codes: {given[check]} and {code}")
            elif e.get("place") != checks[check]:
                out.append(f"{code}: its check is made in {checks[check]}, codes.toml says {e.get('place')}: run "
                           f"write()")
            continue
        if not e.get("what"):
            out.append(f"{code} says no `what`")
        if e.get("calls"):
            app = app_of(e.get("place", ""))
            methods = _methods(root, app) if app else set()
            out += [f"{code}: {app or '?'} has no window call {name}" for name in e["calls"] if name not in methods]
        elif code not in found:
            out.append(f"{code} is in codes.toml but the code gives it nowhere: mark it gone")
    out += [f"no BLD code for the build check {check}: run rusemod.codes.write()" for check in checks
            if check not in given]
    return out


HEAD = """# The failure codes Bug Watch sends (rusemod/codes.py says what a code is and how it travels). One entry for
# each code, never two for one number, never a number given again: a code whose place is gone stays, marked `gone`.
# `place`: the module and the function it is given in (a module of rusemod by its own name; launcher. and studio. for
#   the apps'), never a line. `old`: the key Bug Watch got for that failure before (a "<call>:<module>:<line>" place
#   moved with every release). `check`: for a BLD code, the build check (rusemod.checkkeys key) it stands for; the
#   build failure is still counted by that key too, and its words are in checkkeys.toml. `calls`: window calls whose
#   failures no other code says get this one. `what`: what the failure is, in our words (never sent). `since`: the
#   release it came in, Studio/Launcher.
# Codes given in the code (as a string: coded(error, "SET-08"), failure("LIST-01")) are written here by hand; a new
# build check gets its BLD code from rusemod.codes.write(). tests/test_codes.py fails when the two differ.
"""


def _key(code: str) -> tuple:
    area, _, number = code.partition("-")
    return (AREAS.index(area) if area in AREAS else len(AREAS), int(number) if number.isdigit() else 0)


def write(path: Path = FILE) -> dict:
    """Give each build check of checkkeys.toml with no BLD code the next number nobody had, and mark gone (keeping its
    number) a BLD code whose check isn't there any more. Every other entry stays as it is. Returns {"new", "gone"}."""
    have = read(path)
    checks = _build_checks()
    given = {str(e["check"]) for e in have.values() if isinstance(e, dict) and e.get("check") and not e.get("gone")}
    numbers = [int(c[4:]) for c in have if c.startswith("BLD-") and c[4:].isdigit()]
    top, new, gone = max(numbers, default=0), 0, 0
    for check, place in checks.items():
        if check not in given:
            top += 1
            have[f"BLD-{top:03d}"] = {"place": place, "check": check, "since": SINCE}
            new += 1
    for e in have.values():
        if not isinstance(e, dict) or not e.get("check") or e.get("gone"):
            continue
        if str(e["check"]) in checks:
            e["place"] = checks[str(e["check"])]  # (a check's function renamed: its code follows it)
        else:
            e["gone"] = SINCE
            gone += 1
    lines = [HEAD]
    for code in sorted(have, key=_key):
        e = have[code]
        lines.append(f"[{code}]")
        lines += [f"{field} = {json.dumps(e[field], ensure_ascii=False)}" for field in FIELDS if field in e]
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8", newline="\n")  # (the same file on every system)
    _table.cache_clear()
    return {"new": new, "gone": gone}
