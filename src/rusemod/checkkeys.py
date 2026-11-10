"""Which check refused a Play or a Test in game, or listed a mistake in the mods, by a key that never changes (Bug
Watch, 2026-11-10: a modder's two Test in game tries and two players' Plays failed, and the reports said only
"BuildError at job:test_in_game" and how many mistakes the build listed; a module and a line,
"mistake:rusemod.build:1208", moves with every edit above it and says where, not which check).

checkkeys.toml holds every refusal a build can end on and every mistake it can list, each as its English template
(its values as {0}, {1}...) under the function that makes it, with its key (`check`):
- the rule's id when the code flags it "# rule: <id>" (rusemod.rules; the same window tests/test_rules.py reads:
  its line or the one before), e.g. "nation-models";
- otherwise the module and the function, "build.load_mod", with "-2", "-3"... for each further text that function
  says. Once in the file a key stays: it keeps it while its words stay, and a text whose words changed keeps its
  function's old key when it is the only one there that changed (write()).
Which texts: in the modules a build runs (the import closure of rusemod.play, rusemod.build and rusemod.rmod), every
BuildError, every listed mistake (Finding("error", ...), _find("error", ...), ("error", ...)) and every other raise
flagged "# rule:" or "# not a game rule:"; the errors LittleGroove's .rmod engine records (result.error(...)); and the
apps' own steps before a build (the Studio's test_in_game and check_mod, the Launcher's play).

At run time a text is matched against the templates of the function that made it (an error: the last frame of our
code, or the engine's, in its traceback; a finding: the code that made it, rusemod.patch.Finding.where), the most
particular first, the way rusemod.wordedtext matches a text to say it in the player's language. A mistake a build
makes from a caught error also gets that error's own place (`cause`). Only keys leave the PC, never the words: they
hold what the player typed, folders, and the names in the player's own mods (the agreement, version 3: "what went
wrong and where (in our own code only)"). tests/test_checkkeys.py keeps the file in step with the code.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import tomllib
from functools import lru_cache
from pathlib import Path

from . import wordedtext

FILE = Path(__file__).with_name("checkkeys.toml")
ROOT = Path(__file__).parents[1]  # the folder holding rusemod, ruse_studio, ruse_launcher and ruse_mod_engine
STARTS = ("rusemod.play", "rusemod.build", "rusemod.rmod")
# the apps' own steps before a build: their refusals end a Test in game or a Play too
APPS = {"ruse_studio.api": ("test_in_game", "test_in_game.work", "check_mod"), "ruse_launcher.api": ("play", "_play")}
OURS = ("rusemod", "ruse_studio", "ruse_launcher")
ENGINE = "ruse_mod_engine"
SHORT = (("rusemod.", ""), ("ruse_studio.", "studio."), ("ruse_launcher.", "launcher."), (ENGINE + ".", "engine."))
TAG = re.compile(r"#\s*(?:rule:\s*([a-z0-9-]+)|not a game rule\b)")  # tests/test_rules.py's
KEY = re.compile(r"[A-Za-z0-9_.-]{1,48}")  # a check: what Bug Watch's server takes in a key, with room for "play:"
MIN_OWN = wordedtext.MIN_TEXT  # a template with fewer words of its own isn't matched outside its own function
COMPREHENSIONS = ("<listcomp>", "<genexpr>", "<dictcomp>", "<setcomp>")


def short(module: str) -> str:
    """A module's name as a key says it: "build" for rusemod.build, "studio.api", "engine.applier"."""
    for long, brief in SHORT:
        if module.startswith(long):
            return brief + module[len(long):]
    return module


# --- the file, made from the code (the test and write(); the apps only read it) ---------------------------------
def _files(root: Path) -> dict[str, Path]:
    out = {}
    for p in root.rglob("*.py"):
        if "python251" in p.parts or "__pycache__" in p.parts:
            continue
        parts = list(p.relative_to(root).with_suffix("").parts)
        out[".".join(parts[:-1] if parts[-1] == "__init__" else parts)] = p
    return out


def _imports(module: str, files: dict) -> set[str]:
    path = files[module]
    pkg = module if path.name == "__init__.py" else module.rpartition(".")[0]
    out = set()
    for n in ast.walk(_parse(path)):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            base = n.module or ""
            if n.level:
                up = pkg.split(".")
                base = ".".join(up[:len(up) - (n.level - 1)] + ([base] if base else []))
            out |= {base} | {f"{base}.{a.name}" for a in n.names}
    return {m for m in out if m in files}


def build_modules(root: Path = ROOT) -> list[str]:
    """The modules a build runs: the import closure of STARTS (ours and the engine's)."""
    files = _files(root)
    seen, todo = set(), list(STARTS)
    while todo:
        m = todo.pop()
        if m not in seen and m in files:
            seen.add(m)
            todo += sorted(_imports(m, files) - seen)
    return sorted(seen)


LEVELS = {"error", "warning", "note"}
LOGS = {"log", "logger", "logging", "_log", "LOG"}  # the engine's own log lines aren't errors it records


def _parse(path: Path) -> ast.Module:
    import warnings
    with warnings.catch_warnings():  # (an old escape in a string of someone's code: not ours to say here)
        warnings.simplefilter("ignore", SyntaxWarning)
        return ast.parse(path.read_text(encoding="utf-8"))


def _returns(trees) -> dict[str, str]:
    """{function name: the template it returns} for functions of these modules that return one text and nothing else
    (rmod.refusal), when no other function has the name: a refusal made by such a call gets that text."""
    out, seen = {}, {}
    for tree in trees:
        for f in ast.walk(tree):
            if not isinstance(f, ast.FunctionDef):
                continue
            seen[f.name] = seen.get(f.name, 0) + 1
            rets = [n for n in ast.walk(f) if isinstance(n, ast.Return) and n.value is not None]
            t = wordedtext.template_of(rets[0].value, loose=True) if len(rets) == 1 else None
            if t is not None and _own(t) >= MIN_OWN:
                out[f.name] = t
    return {name: t for name, t in out.items() if seen[name] == 1}


_RETURNS: dict[str, str] = {}


def _template(node) -> str:
    """A text's English template (wordedtext.template_of, loose); a call of a function that returns one text, that
    text (_returns); "{0}" for a text made otherwise (a variable, str(exc))."""
    t = wordedtext.template_of(node, loose=True) if node is not None else None
    if t is None and isinstance(node, ast.Call):
        t = _RETURNS.get(getattr(node.func, "id", None) or getattr(node.func, "attr", None) or "")
    return t if t is not None else "{0}"


def _own(template: str) -> int:
    return len(wordedtext._literal(template).strip())


class _Finder(ast.NodeVisitor):
    def __init__(self, module: str, lines: list[str], engine: bool, only: tuple | None):
        self.module, self.lines, self.engine, self.only = module, lines, engine, only
        self.defs: list[str] = []
        self.found: list[dict] = []

    def visit_FunctionDef(self, node):
        self.defs.append(node.name)
        self.generic_visit(node)
        self.defs.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _in_scope(self) -> bool:
        return self.only is None or bool(self.defs and (self.defs[-1] in self.only
                                                        or ".".join(self.defs[-2:]) in self.only))

    def _add(self, node, kind: str, text_node) -> None:
        if not self._in_scope():
            return
        span = "\n".join(self.lines[max(0, node.lineno - 2):node.end_lineno])
        rule = next((r for r in TAG.findall(span) if r), "")
        func = self.defs[-1] if self.defs else "<module>"
        qual = ".".join(self.defs[-2:]) if self.defs else "module"
        self.found.append({"where": f"{self.module}:{func}", "base": f"{short(self.module)}.{qual}", "kind": kind,
                           "us": _template(text_node), "rule": rule, "line": node.lineno,
                           "tagged": bool(TAG.search(span))})

    def visit_Raise(self, node):
        exc = node.exc
        if isinstance(exc, ast.Call):
            name = getattr(exc.func, "id", None) or getattr(exc.func, "attr", None)
            span = "\n".join(self.lines[max(0, node.lineno - 2):node.end_lineno])
            if name != "BuildError" and (self.only is not None or TAG.search(span)):  # (BuildError: visit_Call)
                self._add(node, "raise", exc.args[0] if exc.args else None)
        self.generic_visit(node)

    def visit_Call(self, node):
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if self.engine:
            if name == "error" and isinstance(node.func, ast.Attribute) and node.args \
                    and getattr(node.func.value, "id", None) not in LOGS:
                self._add(node, "engine", node.args[0])
        elif name == "BuildError":
            self._add(node, "raise", node.args[0] if node.args else None)
        elif name in ("Finding", "_find") and node.args and isinstance(node.args[0], ast.Constant) \
                and node.args[0].value == "error":
            self._add(node, "mistake", node.args[1] if len(node.args) > 1 else None)
        self.generic_visit(node)

    def visit_Tuple(self, node):
        if not self.engine and len(node.elts) > 1 and isinstance(node.elts[0], ast.Constant) \
                and node.elts[0].value == "error" \
                and not all(isinstance(e, ast.Constant) and e.value in LEVELS for e in node.elts):  # (the levels)
            # ("error", text) or ("error", property, why): the part with the most words of its own
            best = max(node.elts[1:], key=lambda e: _own(_template(e)))
            self._add(node, "tuple", best)
        self.generic_visit(node)


def found_in_code(root: Path = ROOT) -> list[dict]:
    """Every refusal and listed mistake in the code (see the module's notes), once per function and template, in the
    order met: {"where", "base", "kind", "us", "rule", "line", "tagged"}."""
    files = _files(root)
    out, seen = [], set()
    targets = [(m, None) for m in build_modules(root)] + [(m, only) for m, only in APPS.items() if m in files]
    trees = {m: _parse(files[m]) for m, _only in targets}
    _RETURNS.clear()
    _RETURNS.update(_returns(t for m, t in trees.items() if not m.startswith(ENGINE)))
    for module, only in targets:
        text = files[module].read_text(encoding="utf-8")
        finder = _Finder(module, text.splitlines(), module.startswith(ENGINE), only)
        finder.visit(trees[module])
        for f in sorted(finder.found, key=lambda f: f["line"]):
            k = (f["where"], f["us"])
            if k not in seen:
                seen.add(k)
                out.append(f)
            elif f["rule"]:  # a later copy of the same text flagged with its rule: the rule's
                first = next(o for o in out if (o["where"], o["us"]) == k)
                first["rule"] = first["rule"] or f["rule"]
    return out


def entry_name(where: str, template: str) -> str:
    """An entry's name in the file: from its function and its English template, so it stays while both do."""
    return "c" + hashlib.sha1(f"{where}\n{template}".encode("utf-8")).hexdigest()[:10]


def read(path: Path = FILE) -> dict:
    try:
        return tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def plan(found: list[dict], old: dict) -> dict:
    """{entry name: entry} for what the code says now, every key kept from `old` (see the module's notes)."""
    taken = {e.get("check") for e in old.values()}
    names = [entry_name(f["where"], f["us"]) for f in found]
    out = {}
    for f, name in zip(found, names):
        check = f["rule"] or (old.get(name) or {}).get("check", "")
        out[name] = {"check": check, "where": f["where"], "kind": f["kind"], "us": f["us"], "base": f["base"]}
    new = set(names)
    for where in dict.fromkeys(f["where"] for f in found):
        waiting = [n for n in out if out[n]["where"] == where and not out[n]["check"]]
        gone = [n for n, e in old.items() if e.get("where") == where and n not in new
                and not re.fullmatch(r"[a-z0-9-]+", e.get("check", "") or "x.")]   # (a rule's id isn't carried)
        if len(waiting) == 1 and len(gone) == 1:  # one text reworded in that function: it keeps its key
            out[waiting[0]]["check"] = old[gone[0]]["check"]
    for name, e in out.items():
        if not e["check"]:
            base = e["base"][:44].rstrip(".")
            n, check = 1, base
            while check in taken:
                n += 1
                check = f"{base}-{n}"
            e["check"] = check
        taken.add(e["check"])
    return out


HEAD = """# Which check refused a Play or a Test in game, or listed a mistake in the mods (rusemod/checkkeys.py): Bug Watch
# counts each by its `check`, never by its words. Made from the code by rusemod.checkkeys.write(); a key once here
# stays (a rule's id, else the module and function that say the text). tests/test_checkkeys.py fails when the code
# says a refusal or a mistake this file doesn't have, or the file has one the code no longer says: run write() then.
# `kind`: raise (an error that ends the job), mistake (a build's listed mistake), tuple (a check's ("error", ...) the
# build lists), engine (an error the .rmod engine records).
"""


def write(path: Path = FILE, root: Path = ROOT) -> dict:
    """Make the file from the code, keeping every key it already gives. Returns {"entries", "new", "gone"}."""
    old = read(path)
    entries = plan(found_in_code(root), old)
    lines = [HEAD]
    for name, e in entries.items():
        lines.append(f"[{name}]")
        for field in ("check", "where", "kind", "us"):
            lines.append(f"{field} = {json.dumps(e[field], ensure_ascii=False)}")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")
    _table.cache_clear()
    return {"entries": len(entries), "new": len(set(entries) - set(old)), "gone": len(set(old) - set(entries))}


def stale(path: Path = FILE, root: Path = ROOT) -> list[str]:
    """What the test checks, said plainly: a text of the code with no entry, an entry the code no longer says, a rule's
    id that isn't the code's, and a key Bug Watch's server wouldn't take."""
    have = read(path)
    found = found_in_code(root)
    out = []
    for f in found:
        e = have.get(entry_name(f["where"], f["us"]))
        if e is None:
            out.append(f"no entry: {f['where']} line {f['line']}: {f['us'][:80]}")
        elif f["rule"] and e.get("check") != f["rule"]:
            out.append(f"rule {f['rule']} but the file says {e.get('check')}: {f['where']} line {f['line']}")
    names = {entry_name(f["where"], f["us"]) for f in found}
    out += [f"left over: {e.get('where')}: {e.get('us', '')[:80]}" for n, e in have.items() if n not in names]
    out += [f"not a key: {e.get('check')}" for e in have.values() if not KEY.fullmatch(str(e.get("check", "")))]
    return out


# --- at run time ----------------------------------------------------------------------------------------------
def _pattern(template: str, prefix: bool = False) -> re.Pattern:
    p = wordedtext._pattern(template)
    return re.compile(r"(?:.*?: )?" + p.pattern, re.S) if prefix else p


@lru_cache(maxsize=2)
def _table(path: str, stamp: float) -> dict:
    """{"where": {where: [(pattern, check, own)]}, "tuple": [...], "engine": [...]}, each the most particular first."""
    out: dict = {"where": {}, "tuple": [], "engine": []}
    for e in read(Path(path)).values():
        if not isinstance(e, dict) or not isinstance(e.get("us"), str) or not KEY.fullmatch(str(e.get("check", ""))):
            continue
        own = _own(e["us"])
        item = (_pattern(e["us"]), e["check"], own)
        out["where"].setdefault(e.get("where", ""), []).append(item)
        if e.get("kind") == "tuple" and own >= MIN_OWN:
            out["tuple"].append((_pattern(e["us"], prefix=True), e["check"], own))
        if e.get("kind") == "engine" and own >= MIN_OWN:
            out["engine"].append(item)
    for items in [*out["where"].values(), out["tuple"], out["engine"]]:
        items.sort(key=lambda i: -i[2])
    return out


def _entries() -> dict:
    try:
        return _table(str(FILE), FILE.stat().st_mtime)
    except OSError:
        return {"where": {}, "tuple": [], "engine": []}


def _first(items, text: str, least: int = 0) -> str:
    return next((check for pattern, check, own in items if own >= least and pattern.fullmatch(text)), "")


def check_of(text, where: str, tuples: bool = False) -> str:
    """The key of a text made in the function `where` ("rusemod.build:load_mod"), else "". `tuples`: a listed mistake,
    which may also be a check's ("error", ...) text the build put its own words before."""
    if not isinstance(text, str) or not where:
        return ""
    t = _entries()
    own = t["where"].get(where, [])
    if not tuples:
        return _first(own, text)
    return _first(own, text, MIN_OWN) or _first(t["tuple"], text) or _first(own, text)


def engine_check(text) -> str:
    """The key of an error the .rmod engine recorded (its ApplyResult.errors), else ""."""
    return _first(_entries()["engine"], text) if isinstance(text, str) else ""


def where_of(error) -> str:
    """Where an error was raised, as "rusemod.build:load_mod": the last frame of our code or the engine's in its
    traceback; "" when none is."""
    tb, where = getattr(error, "__traceback__", None), ""
    while tb is not None:
        frame = tb.tb_frame
        module = frame.f_globals.get("__name__", "")
        if isinstance(module, str) and module.split(".")[0] in OURS + (ENGINE,) \
                and not (module == "rusemod.webui" and frame.f_code.co_name in ("call", "run")):
            where = f"{module}:{frame.f_code.co_name}"
        tb = tb.tb_next
    return where


def error_check(error) -> str:
    """The key of a raised error (where_of and its words), else ""."""
    return check_of(str(error), where_of(error)) if error is not None else ""


def cause_of(error, besides: str = "") -> str:
    """For an error caught and said again (a listed mistake made in an `except`, or an error raised from another):
    the caught one's key, else its place as "module.function" ("missionbuild.read_spawns"); "" when it has no place
    of ours or the engine's, or its place is `besides` (the same function said it again: nothing more to tell)."""
    where = where_of(error) if error is not None else ""
    if not where or where == besides:
        return ""
    module, _, func = where.partition(":")
    return check_of(str(error), where) or f"{short(module)}.{func}"[:48]


def finding_where(frame) -> str:
    """For rusemod.patch.Finding: the function that made a finding, past the helpers that only pass it on (_find,
    comprehensions)."""
    while frame is not None and (frame.f_code.co_name == "_find" or frame.f_code.co_name in COMPREHENSIONS):
        frame = frame.f_back
    if frame is None:
        return ""
    return f"{frame.f_globals.get('__name__', '?')}:{frame.f_code.co_name}"


def finding_key(finding) -> tuple[str, str]:
    """(key, cause) of one of a build's listed mistakes: its own key (Finding.check when the code gave one, else the
    file's for its words where it was made), else its place (Finding.site); and the caught error's (Finding.cause)."""
    key = getattr(finding, "check", "") or check_of(getattr(finding, "message", None),
                                                     getattr(finding, "where", ""), tuples=True)
    return key or getattr(finding, "site", ""), getattr(finding, "cause", "")
