"""Bug Watch: what the Studio and the Launcher do and where they fail, and the game's crashes with the mods that were
on, counted on the PC and sent once a day to our developers' server (the plan: the RUSE Guard repository's
docs/BUG_WATCH.md; what the server takes: its cloudflare/bug-watch/PAYLOADS.md).

Opt-in (the owner, 2026-10-22): nothing is counted, kept or sent unless the player ticked Bug Watch (settings.json
"bugwatch": {"on": true}) and so has an install ID and a username ("player": {"id": 32 random characters, "name":
"Nick#4821"}). `RUSE_NO_BUGWATCH=1` turns it off on a PC whatever the settings say. And `ON` below is the code's own
switch, beside RUSE Guard's fairplay.ON: off until the owner says.

What is counted, per UTC day and app version: every call a window makes (webui._passed_on: its name, how many,
how many failed, the error's kind, the time in five steps), every long job (webui.Job), screens, problems shown,
troubleshooter checks that failed, updates, the mods in use (mod-list mods by id@version, any other as a count),
the game's Steam build,
minutes played, and crashes: the apps' own (an error nobody caught: its kind and the lines in our own files only)
and the game's (its crash code, module and offset, read from the game's crash report on this PC; for the game's
script-error stop the Traceback text; for a bad memory access, what the game tried to do and where (read 0x20); and
the chain: up to 16 places in RUSE.exe the crashed thread's stack returns to, nearest first, so a report says which
part of the game was running, not only where it stopped). Never sent: a path, a file, anything typed, the crash
report file itself, the player's in-game name, any Steam ID. Days wait in `<platform folder>/bugwatch/outbox/` until a
send gets through; none waits more than 30 days.

WHICH failure it was (2026-11-10; players' reports said "BuildError at job:play" and nothing more, and three faults
could not be told from a hundred others): every failed call and job is also counted, under "messages", by the error's
own key when it has one (the Launcher's mod set refusals) and otherwise by where in our own code it came from, as
"play:rusemod.play:327": a module's name and a line number, which the app's version turns back into the very line
(reason_key, site_of). A build that lists mistakes in the mods counts each by where the build found it,
"mistake:rusemod.build:1208" (rusemod.patch.Finding.site). Never the words of either: they hold what the player
typed, folders, and the names in the player's own mods. The agreement's words for this: "what went wrong and where
(in our own code only)".

WHICH check, by a key that never changes (2026-11-10, FL-98 and FL-99: a modder's two Test in game tries and two
players' Plays failed with "BuildError" and a count of mistakes, and a line moves with every edit): a refusal and each
listed mistake are counted by the check that made it (rusemod.checkkeys: a rule's id such as "nation-models", else
the module and function, "build.load_mod"), a mistake made from a caught error also by that error's ("cause:..."); a
failed Play or Test in game by how far it got ("play:stage:before" | build | listed | start) and its set, mods from
our list by id and version and the player's own as counts of folder and .rmod mods ("play:set:L1-F0-R1"); a game
that closed within a minute with no crash report, "game:closed-under-1-min" (Watch._failed, GameWatch).

Checked our_tools.json: crash_site.py reads a whole crash report for our own research and is private; this module
reads only the exception record, the module list and the crashed thread's stack of the game's crash report, on the
player's PC, as any crash reporter does, and sends the crash code, the module's name and the offset, the access and
the chain, nothing more (the plan, §2). For the chain it reads the copy's RUSE.exe section table and the few bytes
before each stack word that points into it: a word right after a call is where that call returns to (2026-11-02, the
owner's "Yes, add it": a player's crash report named only where the game stopped)."""
from __future__ import annotations

import json
import os
import platform
import re
import secrets
import string
import struct
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ON = True   # switched on for the release (the owner, 2026-10-31); each player's own opt-in decides (enabled())
SERVER = "https://ruse-bug-watch.sneadtristen6.workers.dev"
FOLDER = "bugwatch"
OUTBOX = "outbox"
KEEP_DAYS = 30                    # the server refuses a day older than this; the outbox drops it too
SEND_EVERY = 24 * 3600            # a day's counts go once a day, on start
STEPS = (1.0, 10.0, 60.0, 300.0)  # time in five steps: under 1 s, 10 s, 1 min, 5 min, longer
OUR_PACKAGES = ("rusemod", "ruse_studio", "ruse_launcher")
GAME_DUMPS = ("Temp/CrashRpt_*/*.dmp", "*Dumps/RUSE.exe*.dmp")  # the game's crash reporter's folder, then Windows' own
# the server's own limits (PAYLOADS.md / worker.js LIMITS)
MOST = {"calls": 150, "jobs": 30, "screens": 30, "messages": 60, "checks": 60, "mods": 60}
ERROR_KINDS_EACH, ERROR_KINDS_ALL, MAX_COUNT, MAX_MINUTES = 8, 100, 1_000_000, 1440
DAY_BYTES, CRASH_BYTES, TRACEBACK_CHARS, FRAMES = 64 * 1024, 32 * 1024, 12_000, 30
CHAIN_MOST = 16           # places in RUSE.exe a game crash report names from the crashed thread's stack, nearest first
STACK_LOOK = 64 * 1024    # bytes of that stack looked through, from where the crash happened up
ACCESS = {0: "read", 1: "write", 8: "execute"}   # a bad memory access's first detail: what the game tried to do
NAME_RE = re.compile(r"[A-Za-z0-9_.:-]{1,64}")
KIND_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]{0,63}")
MOD_RE = re.compile(r"[A-Za-z0-9_.+-]{1,64}@[0-9A-Za-z.+-]{1,20}")
FILE_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]{0,119}")
FUNC_RE = re.compile(r"[A-Za-z0-9_.<>$-]{1,80}")
ID_CHARS = string.ascii_letters + string.digits + "_-"
# what the server refuses as a path, anywhere in a send (worker.js PATH_PATTERNS)
LOOKS_LIKE_PATH = re.compile(r"(?:^|[^A-Za-z0-9])[A-Za-z]:[\\/]|[\\/]Users[\\/]|/home/", re.IGNORECASE)
ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s\"'<>|*?]*")


# --- the player's yes -------------------------------------------------------------------------------------------
def _settings(home) -> dict:
    from .home import settings
    return settings(Path(home))


def enabled(home) -> bool:
    """Whether Bug Watch counts and sends on this PC: the code's switch, no RUSE_NO_BUGWATCH, the player's tick and an
    install ID."""
    if not ON or os.environ.get("RUSE_NO_BUGWATCH", "").strip() not in ("", "0"):
        return False
    values = _settings(home)
    return bool((values.get("bugwatch") or {}).get("on")) and _good_id((values.get("player") or {}).get("id"))


def _good_id(value) -> bool:
    return isinstance(value, str) and len(value) == 32 and all(c in ID_CHARS for c in value)


def username_of(typed: str, number: int | None = None) -> str:
    """The name the player typed, made safe and unique without a server: control characters, backtick, \\ / and #
    out, then "#" and four digits (`Nick#4821`); 40 characters at most in all."""
    name = re.sub(r"[\x00-\x1f\x7f`\\/#]", "", str(typed or "")).strip()[:34] or "player"
    return f"{name}#{number if number is not None else secrets.randbelow(9000) + 1000:04d}"


def _ensure_player(values: dict, username: str) -> dict:
    """Make or keep the shared player {id, name} in `values`: a 32-character install ID made once, and the username
    (made unique with a #number) when one is given. Shared by Bug Watch and RUSE Guard's program check, so a player
    who ticks either on the agreement screen gets one username and one ID."""
    player = dict(values.get("player") or {})
    if not _good_id(player.get("id")):
        player["id"] = "".join(secrets.choice(ID_CHARS) for _ in range(32))
    if username:
        player["name"] = username if re.fullmatch(r"[^\x00-\x1f\x7f`\\/#]{1,34}#\d{4}", username) else \
            username_of(username)
    values["player"] = player
    return player


def set_username(home, username: str) -> dict:
    """First start (plan §3a): the player picked a username by ticking the program check, Bug Watch, or both. The
    shared install ID and username go in settings.json WITHOUT turning Bug Watch on -- the guard-only case (program
    check on, Bug Watch off) needs the username too. Bug Watch's own switch is left exactly as it was."""
    from .home import save_settings
    values = _settings(home)
    player = _ensure_player(values, username)
    save_settings(Path(home), values)
    return {"name": player.get("name", ""), "code": player["id"][:8]}


def turn_on(home, username: str) -> dict:
    """The player ticked Bug Watch: an install ID (made once) and the username, both kept in settings.json."""
    from .home import save_settings
    values = _settings(home)
    player = _ensure_player(values, username)
    values["bugwatch"] = {**(values.get("bugwatch") or {}), "on": True}
    save_settings(Path(home), values)
    return {"on": True, "name": player.get("name", ""), "code": player["id"][:8]}


def turn_off(home) -> dict:
    """The player unticked it: nothing is counted or sent, the outbox and the kept counts go, and the ID goes too
    unless RUSE Guard's program check still uses it (the plan, §3: "Turn both off and the ID is deleted")."""
    from .home import save_settings
    values = _settings(home)
    values["bugwatch"] = {**(values.get("bugwatch") or {}), "on": False}
    if not (values.get("guard") or {}).get("terms"):   # RUSE Guard (terms accepted) keeps the shared username for its records
        values.pop("player", None)
    save_settings(Path(home), values)
    folder = Path(home) / FOLDER
    for p in sorted(folder.rglob("*.json"), reverse=True) if folder.is_dir() else []:
        try:
            p.unlink()
        except OSError:
            pass
    return {"on": False}


def status(home) -> dict:
    """What Settings shows: whether this build has Bug Watch, on or off, the username and the report code (the ID's
    first 8 characters)."""
    values = _settings(home)
    player = values.get("player") or {}
    return {"available": ON, "on": enabled(home), "name": player.get("name", ""),
            "code": player["id"][:8] if _good_id(player.get("id")) else ""}


# --- making what's sent safe ------------------------------------------------------------------------------------
def no_paths(text: str) -> str:
    """`text` with no path left in it: the player's own folders written as Windows names them for anyone
    (community.private_paths_out), then any other full path cut down to its file name."""
    from .community import private_paths_out
    out = private_paths_out(str(text or ""))
    out = ABSOLUTE.sub(lambda m: re.split(r"[\\/]", m.group(0).rstrip("\\/"))[-1] or "", out)
    return LOOKS_LIKE_PATH.sub(" ", out)


def _name(value) -> str | None:
    text = re.sub(r"[^A-Za-z0-9_.:-]", "_", str(value or ""))[:64]
    return text if NAME_RE.fullmatch(text) else None


def _kind(exc_or_name) -> str:
    name = exc_or_name if isinstance(exc_or_name, str) else type(exc_or_name).__name__
    return name if KIND_RE.fullmatch(name or "") else "Error"


def site_of(error) -> str:
    """Where in our own code an error came from, as "rusemod.play:327": the last line of our own packages on its way
    (the line that raised it, or our line that called what raised it). "" when none of its lines is ours. Our code
    only: a module's name and a line number, no path and nothing of the player's."""
    tb, site = getattr(error, "__traceback__", None), ""
    while tb is not None:
        module = tb.tb_frame.f_globals.get("__name__", "")
        passing_on = module == "rusemod.webui" and tb.tb_frame.f_code.co_name in ("call", "run")
        # (webui's own two lines that pass every call and job on say nothing about which one failed)
        if isinstance(module, str) and module.split(".")[0] in OUR_PACKAGES and not passing_on:
            site = f"{module}:{tb.tb_lineno}"
        tb = tb.tb_next
    return site


def reason_key(name: str, error) -> str | None:
    """What a failed call or job is counted by under "messages", so a report says WHICH refusal or failure it was and
    not only its kind: the error's own key when it carries one (the Launcher's LauncherError(key=...)), else the
    call's name and the check that refused, by a key that never changes ("play:build.load_mod", "play:nation-models":
    rusemod.checkkeys), else where the error came from, "play:rusemod.play:327" (the app's version, sent with the
    day, says which code that line is in). Never the error's words: they can hold what the player typed, or a
    folder."""
    key = getattr(error, "words_key", None)
    if isinstance(key, str) and key:
        return _name(key)
    check = _check_of(error)
    if check:
        return _name(f"{str(name)[:max(1, 63 - len(check))]}:{check}")
    site = site_of(error)
    if not site:
        return None
    site = site[-60:]
    return _name(f"{str(name)[:max(1, 63 - len(site))]}:{site}")


def _check_of(error) -> str:
    """The key of the check that raised `error` (rusemod.checkkeys.error_check), "" when the file doesn't know it."""
    try:
        from .checkkeys import error_check
        return error_check(error)
    except Exception:  # noqa: BLE001 - counting must never stop the app
        return ""


# --- how far a failed Play or Test in game got, and with which mods (2026-11-10: FL-98, FL-99) ---------------------
STAGES = ("before", "build", "listed", "start")  # refused before any build / the build raised / it listed mistakes in
#                                                  the mods / the game didn't start (rusemod.play.Starter.modded)


def set_of(folders) -> tuple[list[str], int, int]:
    """(the mod-list mods among these mod folders as id@version, how many others are folder mods, how many others are
    .rmod files): mods_of, with the player's own mods counted by their kind, never named."""
    listed, own = mods_of(folders)
    rmods = 0
    if own:
        from .rmod import rmod_of
        for folder in folders:
            folder = Path(folder)
            if not (folder / "tags.toml").is_file() and rmod_of(folder) is not None:
                rmods += 1
    return listed, max(0, own - rmods), rmods


def failed_at(error, stage: str, folders) -> None:
    """Mark an error leaving a Play or a Test in game (rusemod.play.Starter.modded) with how far it got and the set's
    mods (set_of), for Watch.job. Never raises."""
    try:
        if getattr(error, "stage", None) is None:
            error.stage = stage if stage in STAGES else None
        if getattr(error, "mod_set", None) is None:
            error.mod_set = set_of(list(folders or []))
    except Exception:  # noqa: BLE001 - an error that takes no attributes, or a mod folder that can't be read
        pass


def _step(seconds: float) -> int:
    return next((i for i, edge in enumerate(STEPS) if seconds < edge), len(STEPS))


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# --- the counts -------------------------------------------------------------------------------------------------
def _blank_day(version: str) -> dict:
    return {"version": version, "calls": {}, "jobs": {}, "screens": {}, "messages": {}, "checks": {},
            "updates": {"offered": 0, "installed": 0, "failed": 0}, "mods": {}, "own_mods": 0,
            "played": {"total": 0, "mods": {}}, "app_crashes": 0}


class Watch:
    """One app's Bug Watch while it runs: the counts of each UTC day, kept in `<home>/bugwatch/days-<app>.json` (so a
    restart adds to them), and the outbox of what waits to be sent."""

    def __init__(self, home, app: str, version: str, opener=None, clock=time.time):
        self.home, self.app, self.version = Path(home), app, version
        self.folder = self.home / FOLDER
        self.outbox = self.folder / OUTBOX
        self.file = self.folder / f"days-{app}.json"
        self.lock = threading.RLock()
        self.opener = opener or urllib.request.urlopen
        self.clock = clock
        self.days: dict[str, dict] = {}
        self._dirty = 0
        try:
            self.days = json.loads(self.file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.days = {}

    # recording (each does nothing when the player hasn't said yes)
    def _day(self) -> dict | None:
        if not enabled(self.home):
            return None
        day = _today()
        if day not in self.days:
            self.days[day] = _blank_day(self.version)
        return self.days[day]

    def _changed(self) -> None:
        self._dirty += 1
        if self._dirty >= 20:
            self.save()

    def call(self, name: str, seconds: float, error=None) -> None:
        key = _name(name)
        with self.lock:
            day = self._day()
            if day is None or key is None:
                return
            c = day["calls"].setdefault(key, {"n": 0, "failed": 0, "errors": {}, "time": [0, 0, 0, 0, 0]})
            c["n"] += 1
            c["time"][_step(seconds)] += 1
            if error is not None:
                c["failed"] += 1
                kind = _kind(error)
                c["errors"][kind] = c["errors"].get(kind, 0) + 1
                self._reason(day, key, error)
            self._changed()

    def job(self, name: str, ok: bool, seconds: float, error=None, build_errors: int = 0, mistakes=()) -> None:
        """`mistakes`: for a build that listed mistakes in the mods, where the build found each one
        (rusemod.patch.Finding.site), counted under "messages" as "mistake:rusemod.build:1208" when the error
        doesn't say which check each was (its `error_keys`: _failed)."""
        key = _name(name) or "job"
        with self.lock:
            day = self._day()
            if day is None:
                return
            j = day["jobs"].setdefault(key, {"done": 0, "failed": 0, "errors": {}, "build_errors": 0,
                                             "time": [0, 0, 0, 0, 0], "running": 0})
            j["done" if ok else "failed"] += 1
            j["time"][_step(seconds)] += 1
            j["build_errors"] += max(0, int(build_errors or 0))
            if not ok and error is not None:
                kind = _kind(error)
                j["errors"][kind] = j["errors"].get(kind, 0) + 1
                self._reason(day, key, error)
                if not self._failed(day, key, error):
                    for site in list(mistakes or [])[:MOST["messages"]]:
                        where = _name(f"mistake:{str(site)[-55:]}") if site else None
                        if where:
                            day["messages"][where] = day["messages"].get(where, 0) + 1
            self._changed()

    def _failed(self, day: dict, job: str, error) -> bool:
        """What a failed Play or Test in game tells beyond its kind, under "messages" (2026-11-10: FL-98, FL-99), each a
        key of our own, never the words:
        - "play:stage:before" | build | listed | start: how far it got (rusemod.play.Starter.modded);
        - "play:set:L2-F1-R0": the set's mods, L from our mod list, F the player's own folder mods, R the player's own
          .rmod files (counted, never named), and "play:lib:cheat-mod-v2:2.0.0" for each from the list (id:version);
        - "mistake:<check>" for each listed mistake (rusemod.checkkeys: a rule's id, or the module and function that
          found it), "cause:<check or module.function>" for the caught error one said again, and for the refusal's
          own cause.
        Returns whether the error said its mistakes' checks (then the sites aren't counted again)."""
        def add(text: str) -> None:
            k = _name(text)
            if k and len(text) <= 64 and (k in day["messages"] or len(day["messages"]) < 4 * MOST["messages"]):
                day["messages"][k] = day["messages"].get(k, 0) + 1

        try:
            stage = getattr(error, "stage", None)
            if stage in STAGES:
                add(f"{job}:stage:{stage}")
            found = getattr(error, "mod_set", None)
            if isinstance(found, tuple) and len(found) == 3:
                listed, folders, rmods = found
                add(f"{job}:set:L{len(listed)}-F{int(folders)}-R{int(rmods)}")
                for mod in listed[:MOST["mods"]]:
                    if MOD_RE.fullmatch(str(mod)):
                        add(f"{job}:lib:{str(mod).replace('@', ':')}")
            from .checkkeys import cause_of, where_of
            context = error.__cause__ or error.__context__
            cause = cause_of(context, where_of(error)) if context is not None else ""
            if cause:
                add(f"cause:{cause}")
            keys = getattr(error, "error_keys", None)
            if not isinstance(keys, list):
                return False
            for check, cause in keys[:MOST["messages"]]:
                if check:
                    add(f"mistake:{str(check)[-55:]}")
                if cause:
                    add(f"cause:{str(cause)[-57:]}")
            return True
        except Exception:  # noqa: BLE001 - counting must never stop the app
            return False

    def _reason(self, day: dict, name: str, error) -> None:
        """Which refusal or failure it was (reason_key), counted with the problems shown."""
        key = reason_key(name, error)
        if key:
            day["messages"][key] = day["messages"].get(key, 0) + 1

    def game_build(self, build) -> None:
        """The game's Steam build as the app found it when it started a game: named in the day's report."""
        text = str(build or "")
        with self.lock:
            day = self._day()
            if day is not None and re.fullmatch(r"[0-9A-Za-z._+-]{1,24}", text) and day.get("game_build") != text:
                day["game_build"] = text
                self._changed()

    def checks(self, findings) -> None:
        """The troubleshooter's findings that say something is wrong ("warn" or "fail"), each counted by its key."""
        for found in findings or []:
            if isinstance(found, dict) and found.get("level") in ("warn", "fail") and found.get("key"):
                self.count("checks", str(found["key"]))

    def count(self, group: str, key: str) -> None:
        """One of: "screens" (a screen opened), "messages" (a problem shown: its words key), "checks" (a
        troubleshooter check that failed), "updates" ("offered" / "installed" / "failed")."""
        name = _name(key)
        with self.lock:
            day = self._day()
            if day is None or name is None:
                return
            if group == "screens":
                s = day["screens"].setdefault(name, {"opened": 0, "used": 0})
                s["opened"] += 1
            elif group == "updates":
                if name in day["updates"]:
                    day["updates"][name] += 1
            elif group in ("messages", "checks"):
                day[group][name] = day[group].get(name, 0) + 1
            self._changed()

    def played(self, minutes: float, listed: list[str], own: int) -> None:
        """A game that ran `minutes` with these mods: `listed` the mod-list mods as id@version, `own` any others."""
        mins = max(0, int(round(minutes)))
        with self.lock:
            day = self._day()
            if day is None:
                return
            day["played"]["total"] = min(MAX_MINUTES, day["played"]["total"] + mins)
            for mod in listed:
                if MOD_RE.fullmatch(mod):
                    day["mods"][mod] = 1
                    day["played"]["mods"][mod] = min(MAX_MINUTES, day["played"]["mods"].get(mod, 0) + mins)
            day["own_mods"] = max(day["own_mods"], max(0, int(own)))
            self.save()

    def save(self) -> None:
        with self.lock:
            self._dirty = 0
            if not self.days:
                return
            try:
                self.folder.mkdir(parents=True, exist_ok=True)
                self.file.write_text(json.dumps(self.days), encoding="utf-8")
            except OSError:
                pass

    # what goes out
    def payload(self, day: str, counts: dict) -> dict:
        """One day's send, cut to the server's limits (the most-used kept)."""
        values = _settings(self.home)
        player = values.get("player") or {}
        out = {"v": 1, "id": player.get("id", ""), "app": self.app, "version": counts.get("version") or self.version,
               "day": day, "setup": self.setup()}
        if counts.get("game_build"):
            out["setup"]["game_build"] = counts["game_build"]
        if player.get("name"):
            out["user"] = player["name"]
        budget = [ERROR_KINDS_ALL]

        def errors(kinds: dict) -> dict:
            kept = dict(sorted(kinds.items(), key=lambda kv: -kv[1])[:max(0, min(ERROR_KINDS_EACH, budget[0]))])
            budget[0] -= len(kept)
            return {k: min(MAX_COUNT, v) for k, v in kept.items()}

        def top(group: dict, most: int, weight) -> list:
            return sorted(group.items(), key=lambda kv: -weight(kv[1]))[:most]

        calls = {}
        for name, c in top(counts.get("calls", {}), MOST["calls"], lambda c: c["n"]):
            item = {"n": min(MAX_COUNT, c["n"]), "failed": min(c["n"], c["failed"]), "time": c["time"]}
            kinds = errors(c["errors"]) if c["errors"] else {}
            if kinds:
                item["errors"] = kinds
            calls[name] = item
        jobs = {}
        for name, j in top(counts.get("jobs", {}), MOST["jobs"], lambda j: j["done"] + j["failed"]):
            item = {k: min(MAX_COUNT, j[k]) for k in ("done", "failed", "build_errors", "running")}
            item["time"] = j["time"]
            kinds = errors(j["errors"]) if j["errors"] else {}
            if kinds:
                item["errors"] = kinds
            jobs[name] = item
        if calls:
            out["calls"] = calls
        if jobs:
            out["jobs"] = jobs
        screens = dict(top(counts.get("screens", {}), MOST["screens"], lambda s: s["opened"]))
        if screens:
            out["screens"] = screens
        for group in ("messages", "checks"):
            kept = dict(top(counts.get(group, {}), MOST[group], lambda n: n))
            if kept:
                out[group] = {k: min(MAX_COUNT, v) for k, v in kept.items()}
        if any(counts.get("updates", {}).values()):
            out["updates"] = counts["updates"]
        mods = sorted(counts.get("mods", {}))[:MOST["mods"]]
        if mods or counts.get("own_mods"):
            out["mods"] = {"list": mods, "own": counts.get("own_mods", 0)}
        played = counts.get("played") or {}
        if played.get("total"):
            out["played"] = {"total": played["total"],
                             "mods": {m: v for m, v in played.get("mods", {}).items() if m in mods}}
        if counts.get("app_crashes"):
            out["app_crashes"] = min(MAX_COUNT, counts["app_crashes"])
        while len(json.dumps(out, separators=(",", ":")).encode()) > DAY_BYTES and out.get("calls"):
            out["calls"].popitem()  # the least-used call goes first (they're in order of use)
        return out

    def setup(self) -> dict:
        values = _settings(self.home)
        out = {}
        release = platform.release() if sys.platform == "win32" else ""
        if release in ("10", "11"):
            out["windows"] = release
        lang = ((values.get("prefs") or {}).get(self.app) or {}).get("lang") or values.get("lang")
        if isinstance(lang, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,12}", lang):
            out["language"] = lang
        try:
            from . import fairplay
            out["guard"] = bool(fairplay.ON)
        except ImportError:
            pass
        return out

    def roll(self) -> int:
        """Every finished day (before today, UTC) into the outbox as its send; days older than KEEP_DAYS are dropped.
        Returns how many went."""
        today = _today()
        oldest = (datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)).strftime("%Y-%m-%d")
        moved = 0
        with self.lock:
            for day in sorted(self.days):
                if day >= today:
                    continue
                counts = self.days.pop(day)
                if day >= oldest and enabled(self.home):
                    self._write_out(f"day-{self.app}-{day}.json", self.payload(day, counts))
                    moved += 1
            if self.days:
                self.save()
            else:
                self.file.unlink(missing_ok=True)
        return moved

    def _write_out(self, name: str, body: dict) -> None:
        self.outbox.mkdir(parents=True, exist_ok=True)
        (self.outbox / name).write_text(json.dumps(body), encoding="utf-8")

    def send_waiting(self, force: bool = False) -> dict:
        """Send what waits in the outbox: the crashes at once, the days once a day (or `force`). A send that gets
        through or that the server refuses for good goes; one it can't take now (switched off, busy, no internet)
        waits, up to KEEP_DAYS. Never raises: a failed send just waits for the next."""
        out = {"sent": 0, "waiting": 0, "dropped": 0}
        if not enabled(self.home) or not self.outbox.is_dir():
            return out
        last = float((_settings(self.home).get("bugwatch") or {}).get("last_send") or 0)
        days_due = force or self.clock() - last >= SEND_EVERY
        sent_a_day = False
        for p in sorted(self.outbox.glob("*.json")):
            is_day = p.name.startswith("day-")
            if is_day and not days_due:
                out["waiting"] += 1
                continue
            try:
                if self.clock() - p.stat().st_mtime > KEEP_DAYS * 86400:
                    p.unlink(missing_ok=True)
                    out["dropped"] += 1
                    continue
                body = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                p.unlink(missing_ok=True)
                out["dropped"] += 1
                continue
            answer = self._post("/v1/day" if is_day else "/v1/crash", body)
            if answer in (200, 400, 413, 429):  # through, or refused for good (it would never get through)
                p.unlink(missing_ok=True)
                out["sent" if answer == 200 else "dropped"] += 1
                sent_a_day |= is_day and answer == 200
            else:
                out["waiting"] += 1
        if sent_a_day:
            from .home import save_settings
            values = _settings(self.home)
            values["bugwatch"] = {**(values.get("bugwatch") or {}), "last_send": int(self.clock())}
            save_settings(self.home, values)
        return out

    def _post(self, path: str, body: dict) -> int:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        req = urllib.request.Request(SERVER + path, data=data, method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": "RUSE-Bug-Watch"})
        try:
            with self.opener(req, timeout=15) as r:
                return int(getattr(r, "status", 200))
        except urllib.error.HTTPError as exc:
            return int(exc.code)
        except Exception:  # no internet, a timeout, anything: it waits for the next time
            return 0

    # crashes
    def crash(self, body: dict, send=True) -> Path:
        """One crash report into the outbox, and sent now in the background."""
        values = _settings(self.home)
        player = values.get("player") or {}
        body = {"v": 1, "id": player.get("id", ""), "app": self.app, "version": self.version, **body}
        if player.get("name"):
            body["user"] = player["name"]
        if len(json.dumps(body).encode()) > CRASH_BYTES:
            body.pop("traceback", None)
        name = f"crash-{self.app}-{int(self.clock() * 1000)}-{secrets.token_hex(3)}.json"
        self._write_out(name, body)
        if send:
            threading.Thread(target=self.send_waiting, daemon=True).start()
        return self.outbox / name

    def app_crash(self, exc_type, exc, tb) -> None:
        if not enabled(self.home):
            return
        with self.lock:
            day = self._day()
            if day is not None:
                day["app_crashes"] += 1
                self.save()
        self.crash({"kind": "app", "error": _kind(exc_type.__name__), "frames": our_frames(tb)})

    def game_crash(self, found: dict, listed: list[str], own: int, send=True) -> Path | None:
        if not enabled(self.home):
            return None
        body = {"kind": "game", "code": found["code"], "module": found["module"], "offset": found["offset"],
                "mods": [m for m in listed if MOD_RE.fullmatch(m)][:MOST["mods"]], "own_mods": max(0, int(own))}
        if found.get("access"):
            body["access"] = found["access"]
        if found.get("chain"):
            body["chain"] = found["chain"][:CHAIN_MOST]
        if found.get("traceback"):
            body["traceback"] = found["traceback"]
        return self.crash(body, send)


def our_frames(tb) -> list:
    """[file, line, function] for the frames in our own packages, oldest first, as the server takes them: the file
    from the package folder on (`rusemod/build.py`), nothing above it."""
    out = []
    for frame in traceback.extract_tb(tb):
        parts = re.split(r"[\\/]", frame.filename)
        at = next((i for i in range(len(parts) - 1, -1, -1) if parts[i] in OUR_PACKAGES), None)
        if at is None:
            continue
        name = "/".join(parts[at:])
        func = frame.name if FUNC_RE.fullmatch(frame.name or "") else "?"
        if FILE_RE.fullmatch(name) and ".." not in name:
            out.append([name, int(frame.lineno or 0), func])
    return out[-FRAMES:]


# --- the game's crashes ---------------------------------------------------------------------------------------
def crash_dumps_since(since: float, local: str | None = None) -> list[Path]:
    """The game's crash report files written after `since` on this PC (GAME_DUMPS under %LOCALAPPDATA%)."""
    local = local or os.environ.get("LOCALAPPDATA")
    if not local:
        return []
    found = []
    for pattern in GAME_DUMPS:
        for p in Path(local).glob(pattern):
            try:
                if p.stat().st_mtime >= since:
                    found.append(p)
            except OSError:
                continue
    return sorted(found, key=lambda p: p.stat().st_mtime)


def _returns_to(exe):
    """For the copy's RUSE.exe at `exe`: a test of whether a place in it (its offset from the start of the loaded
    program) comes right after a call, so a stack word pointing there is where that call returns to, a caller, rather
    than any other pointer into the program. None when the file can't be read as a 64-bit Windows program."""
    try:
        raw = Path(exe).read_bytes()
        (pe,) = struct.unpack_from("<I", raw, 0x3C)
        if raw[pe:pe + 4] != b"PE\0\0":
            return None
        (sections,), (optional,) = struct.unpack_from("<H", raw, pe + 6), struct.unpack_from("<H", raw, pe + 20)
        code = []
        at = pe + 24 + optional
        for _ in range(sections):
            _name, vsize, va, rsize, rawptr = struct.unpack_from("<8sIIII", raw, at)
            (flags,) = struct.unpack_from("<I", raw, at + 36)
            if flags & 0x20000000:  # (a section the program runs)
                code.append((va, max(vsize, rsize), rawptr, rsize))
            at += 40
    except (OSError, struct.error):
        return None

    def after_call(place: int) -> bool:
        for va, span, rawptr, rsize in code:
            if not va <= place < va + span:
                continue
            o = place - va + rawptr
            if o - 7 < rawptr or o > rawptr + rsize:
                return False
            b = raw
            return (b[o - 5] == 0xE8                                                # call to a fixed place
                    or b[o - 6:o - 4] == b"\xff\x15"                                # call [a fixed place]
                    or (b[o - 2] == 0xFF and b[o - 1] & 0xF8 == 0xD0)                # call a register
                    or (b[o - 2] == 0xFF and b[o - 1] & 0xF8 == 0x10 and b[o - 1] & 7 not in (4, 5))  # call [reg]
                    or (b[o - 3] == 0xFF and b[o - 2] == 0x14)                       # call [reg+reg]
                    or (b[o - 3] == 0xFF and b[o - 2] & 0xF8 == 0x50 and b[o - 2] & 7 != 4)  # call [reg+small]
                    or (b[o - 4] == 0xFF and b[o - 3] == 0x54)                       # call [reg+reg+small]
                    or (b[o - 6] == 0xFF and b[o - 5] & 0xF8 == 0x90 and b[o - 5] & 7 != 4)  # call [reg+large]
                    or (b[o - 7] == 0xFF and b[o - 6] == 0x94))                      # call [reg+reg+large]
        return False
    return after_call


def _memory_at(data: bytes, streams: dict, address: int) -> tuple[int, int, int] | None:
    """(start, size, where in the file) of the memory the crash report kept around `address`, from its memory lists
    (the game's own crash reporter keeps the threads' stacks there, not beside each thread), or None."""
    if 5 in streams:  # MemoryListStream: (start, size, where) each
        at, _ = streams[5]
        (n,) = struct.unpack_from("<I", data, at)
        for i in range(n):
            start, size, where = struct.unpack_from("<QII", data, at + 4 + 16 * i)
            if start <= address < start + size and where + size <= len(data):
                return start, size, where
    if 9 in streams:  # Memory64ListStream: (start, size) each, their bytes one after another from one place
        at, _ = streams[9]
        n, where = struct.unpack_from("<QQ", data, at)
        for i in range(n):
            start, size = struct.unpack_from("<QQ", data, at + 16 + 16 * i)
            if start <= address < start + size and where + size <= len(data):
                return start, size, where
            where += size
    return None


def read_dump(path, exe=None) -> dict | None:
    """From a crash report file, read on this PC only: {"code", "module", "offset"}; for a bad memory access
    (0xc0000005) "access", what the game tried to do and where ("read 0x20"); with the copy's RUSE.exe (`exe`) given,
    "chain": the places in RUSE.exe the crashed thread's stack returns to, nearest first (up to CHAIN_MOST, each one
    right after a call); and for the game's script-error stop (0x29a), "traceback" (the game Python's text, paths cut).
    None if it can't be read. The dump never leaves the PC (the plan, §2)."""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    if data[:4] != b"MDMP":
        return None
    access, chain = None, []
    try:
        count, rva = struct.unpack_from("<II", data, 8)
        streams = {}
        for i in range(count):
            kind, size, at = struct.unpack_from("<III", data, rva + 12 * i)
            streams[kind] = (at, size)
        if 6 not in streams:  # ExceptionStream
            return None
        at, exc_size = streams[6]
        (thread,) = struct.unpack_from("<I", data, at)
        code, _flags, _rec, address, params = struct.unpack_from("<IIQQI", data, at + 8)
        if code == 0xC0000005 and params >= 2:
            what, where = struct.unpack_from("<QQ", data, at + 40)
            access = f"{ACCESS.get(what, '?')} 0x{where:x}"
        modules = []
        if 4 in streams:  # ModuleListStream
            mat, _ = streams[4]
            (n,) = struct.unpack_from("<I", data, mat)
            for i in range(n):
                base, size, _sum, _stamp, name_rva = struct.unpack_from("<QIIII", data, mat + 4 + 108 * i)
                (length,) = struct.unpack_from("<I", data, name_rva)
                name = data[name_rva + 4:name_rva + 4 + length].decode("utf-16-le", "replace")
                modules.append((base, size, re.split(r"[\\/]", name)[-1]))
        module, offset = next(((name, address - base) for base, size, name in modules
                               if base <= address < base + size), ("?", address))
        game = next(((base, size) for base, size, name in modules if name.lower() == "ruse.exe"), None)
        after_call = _returns_to(exe) if exe is not None and game is not None else None
        if after_call is not None and 3 in streams and exc_size >= 168:  # ThreadListStream; the thread's registers
            _ctx_size, ctx_at = struct.unpack_from("<II", data, at + 160)
            (rsp,) = struct.unpack_from("<Q", data, ctx_at + 0x98)  # (where the crashed thread's stack was)
            tat, _ = streams[3]
            (n,) = struct.unpack_from("<I", data, tat)
            for i in range(n):
                t = tat + 4 + 48 * i
                if struct.unpack_from("<I", data, t)[0] != thread:
                    continue
                start, ssize, srva = struct.unpack_from("<QII", data, t + 24)
                if not srva or srva + ssize > len(data):  # (the stack kept in a memory list instead)
                    start, ssize, srva = _memory_at(data, streams, rsp) or (0, 0, 0)
                stack = data[srva:srva + ssize] if srva else b""
                first = rsp - start if start <= rsp < start + ssize else 0
                first -= first % 8
                base, size = game
                for o in range(first, min(len(stack), first + STACK_LOOK) - 7, 8):
                    (word,) = struct.unpack_from("<Q", stack, o)
                    place = f"RUSE.exe+0x{word - base:x}"
                    if base <= word < base + size and place not in chain and after_call(word - base):
                        chain.append(place)
                        if len(chain) >= CHAIN_MOST:
                            break
                break
    except struct.error:
        return None
    module = re.sub(r"[^A-Za-z0-9_.+ -]", "_", module)[:64] or "?"
    out = {"code": f"0x{code:x}", "module": module, "offset": f"0x{offset:x}"}
    if access:
        out["access"] = access
    if chain:
        out["chain"] = chain
    if code == 0x29A:
        text = script_error_text(data)
        if text:
            out["traceback"] = no_paths(text)[:TRACEBACK_CHARS]
    return out


TRACEBACK_MARK = b"Traceback (most recent call last)"
TRACEBACK_COPIES = 64   # copies of the text looked at in one crash report


def _one_error_text(raw: bytes) -> tuple[bool, str]:
    """(whole?, text) for one copy of the game's script error text: its lines up to and with the error's own line
    (the first line after the header that isn't indented: "KeyError: ..."), and nothing after it (whatever bytes
    followed it in memory). Not whole when the copy ends before that line."""
    lines = raw.decode("latin-1", "replace").replace("\r\n", "\n").split("\n")
    kept = [lines[0].rstrip()]
    for line in lines[1:]:
        clean = "".join(ch for ch in line if ch == "\t" or " " <= ch <= "~" or "\xa0" <= ch).rstrip()
        if line.startswith(" "):
            kept.append(clean)
            continue
        if re.match(r"[A-Za-z_][A-Za-z0-9_.]*(?::|$)", clean):  # the error's own line: its kind, then what it says
            kept.append(clean)
            return True, "\n".join(kept)
        break
    return False, "\n".join(kept)


def script_error_text(data: bytes) -> str:
    """The game's script error text in a crash report file (its code 0x29a stop). The file can hold the text more
    than once, and the first copy can be cut short before the error's own line (two players' reports of 2026-11-06
    ended in the middle of a file name): the copy that reaches the error's line wins, else the longest one."""
    best, best_whole = "", False
    at, seen = data.find(TRACEBACK_MARK), 0
    while at >= 0 and seen < TRACEBACK_COPIES:
        end = data.find(b"\x00", at)
        whole, text = _one_error_text(data[at:end if at < end <= at + TRACEBACK_CHARS else at + TRACEBACK_CHARS])
        if (whole, len(text)) > (best_whole, len(best)):
            best, best_whole = text, whole
        seen += 1
        at = data.find(TRACEBACK_MARK, at + len(TRACEBACK_MARK))
    return best


QUICK_CLOSE = 60.0  # seconds: a game started from a modded copy that closed sooner, leaving no crash report, is counted


class GameWatch(threading.Thread):
    """Beside the game the apps started (rusemod.play.Starter): when it closes, the minutes it ran with its mods, and
    any crash report it left since it started."""

    def __init__(self, watch: Watch, process, listed: list[str], own: int, sleep=time.sleep, clock=time.time,
                 local: str | None = None, exe=None):
        super().__init__(daemon=True, name="bug-watch-game")
        self.watch, self.process, self.listed, self.own = watch, process, listed, own
        self.sleep, self.clock, self.local, self.started = sleep, clock, local, clock()
        self.exe = exe  # the copy's RUSE.exe, for a crash's chain (read_dump)

    def run(self) -> None:
        while self.process.poll() is None:
            self.sleep(5)
        ran = self.clock() - self.started
        self.watch.played(ran / 60.0, self.listed, self.own)
        crashed = False
        for dump in crash_dumps_since(self.started, self.local):
            found = read_dump(dump, self.exe)
            if found:
                crashed = True
                self.watch.game_crash(found, self.listed, self.own)
        if ran < QUICK_CLOSE and not crashed:  # the game didn't get going, or was quit at once (2026-11-10)
            self.watch.count("messages", "game:closed-under-1-min")


def mods_of(folders) -> tuple[list[str], int]:
    """(the mod-list mods among these mod folders as id@version, how many others): a mod installed from the mod list
    has the list's tags beside it (fairplay.TAGS_FILE); any other is someone's own and is never named."""
    import tomllib
    listed, own = [], 0
    for folder in folders:
        folder = Path(folder)
        try:
            mod = tomllib.loads((folder / "mod.toml").read_text(encoding="utf-8")).get("mod", {})
        except (OSError, ValueError):
            mod = {}
        name = f"{mod.get('id', '')}@{mod.get('version', '')}"
        if (folder / "tags.toml").is_file() and MOD_RE.fullmatch(name):
            listed.append(name)
        else:
            own += 1
    return listed, own


# --- one Watch per app, and the hooks ---------------------------------------------------------------------------
_current: Watch | None = None
_calls = threading.local()  # the window call running on this thread (a job started in it takes its name)


def start(home, app: str, version: str) -> Watch:
    """At the app's start: its Watch, the finished days into the outbox, what waits sent in the background, and
    the error hooks that count crashes. Safe to call when Bug Watch is off (nothing is counted then)."""
    global _current
    _current = Watch(home, app, version)
    _hook_errors(_current)
    if enabled(home):
        _current.roll()
        threading.Thread(target=_current.send_waiting, daemon=True).start()
    import atexit
    atexit.register(_current.save)
    return _current


def current() -> Watch | None:
    return _current


def call_started(name: str) -> float:
    _calls.name = name
    return time.perf_counter()


def call_ended(name: str, started: float, error=None) -> None:
    _calls.name = None
    if _current is not None and not name.startswith("bugwatch_"):  # (its own calls aren't what it counts)
        # (a failed call is also counted by which refusal or failure it was: Watch.call, reason_key)
        _current.call(name, time.perf_counter() - started, error)


def count(group: str, key: str) -> None:
    """Count one of Watch.count's groups in this app's Watch, when there is one (nothing when Bug Watch is off)."""
    if _current is not None:
        _current.count(group, key)


def checks(findings) -> None:
    """Count the troubleshooter's findings that say something is wrong (Watch.checks), when there is a Watch."""
    if _current is not None:
        _current.checks(findings)


class Refused(Exception):
    """A job an app refused before it started: its kind as Bug Watch counts it, and its key (never words)."""

    def __init__(self, key: str):
        super().__init__(key)
        self.words_key = key


def refused(name: str, key: str) -> None:
    """A job an app refused before starting it (the Launcher's Play: one already starting, a restore running, no
    such set, a set with a mistake, an author not trusted yet), counted as a failed job of kind "Refused" and by its
    key under "messages". Until 2026-11-10 these Plays never reached Bug Watch at all (the job never started)."""
    if _current is not None:
        _current.job(name, False, 0.0, Refused(key))


class BugWatchCalls:
    """The window API's Bug Watch calls, for both apps (a mixin beside community.CommunityCalls: it uses the API's
    `_home` and rusemod.update.UpdateCalls' UPDATE_APP and UPDATE_VERSION)."""

    def _bugwatch(self) -> Watch:
        home = Path(self._home)
        if _current is None or _current.home != home:
            return start(home, getattr(self, "UPDATE_APP", "app"), getattr(self, "UPDATE_VERSION", "0"))
        return _current

    def bugwatch_status(self) -> dict:
        """{"available": whether this version has Bug Watch, "on", "name": the username, "code": the report code}."""
        return status(self._home)

    def bugwatch_on(self, username: str) -> dict:
        """The player ticked Bug Watch with this username (made unique with a #number)."""
        if not ON:
            raise ValueError("Bug Watch isn't in this version of the app yet.")
        out = turn_on(self._home, username)
        self._bugwatch()
        return out

    def set_username(self, username: str) -> dict:
        """First start (plan 3a): the player picked a username by ticking the program check or Bug Watch. The shared
        username and install ID are saved without turning Bug Watch on (RUSE Guard's program check uses them too)."""
        return set_username(self._home, username)

    def bugwatch_off(self) -> dict:
        """The player unticked it: nothing more is counted or sent, and what was kept is deleted."""
        return turn_off(self._home)

    def bugwatch_next_send(self) -> dict:
        """What would be sent, word for word (Settings' "Show what's sent"): today's counts as they'd go, and the
        sends already waiting."""
        watch = self._bugwatch()
        day = _today()
        with watch.lock:
            counts = json.loads(json.dumps(watch.days.get(day) or _blank_day(watch.version)))
        waiting = sorted(p.name for p in watch.outbox.glob("*.json")) if watch.outbox.is_dir() else []
        return {"today": watch.payload(day, counts), "waiting": waiting}

    def bugwatch_seen(self, group: str, key: str) -> dict:
        """The page tells Bug Watch a screen opened ("screens", its name) or a problem shown ("messages", its words
        key)."""
        if group not in ("screens", "messages"):
            raise ValueError("Bug Watch counts screens and messages from the page, nothing else.")
        if _current is not None:
            _current.count(group, key)
        return {"ok": True}


def running_call() -> str | None:
    return getattr(_calls, "name", None)


def _hook_errors(watch: Watch) -> None:
    before, before_thread = sys.excepthook, threading.excepthook

    def on_error(exc_type, exc, tb):
        try:
            watch.app_crash(exc_type, exc, tb)
        except Exception:
            pass
        before(exc_type, exc, tb)

    def on_thread_error(args):
        try:
            if args.exc_type is not SystemExit:
                watch.app_crash(args.exc_type, args.exc_value, args.exc_traceback)
        except Exception:
            pass
        before_thread(args)

    sys.excepthook, threading.excepthook = on_error, on_thread_error
