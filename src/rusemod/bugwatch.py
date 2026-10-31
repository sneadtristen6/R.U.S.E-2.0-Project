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
minutes played, and crashes: the apps' own (an error nobody caught: its kind and the lines in our own files only)
and the game's (its crash code, module and offset, read from the game's crash report on this PC, and for the game's
script-error stop the Traceback text). Never sent: a path, a file, anything typed, the crash report file itself, the
player's in-game name, any Steam ID. Days wait in `<platform folder>/bugwatch/outbox/` until a send gets through;
none waits more than 30 days.

Checked our_tools.json: none of its tools reads a crash report; this module reads only the exception record and the
module list of the game's crash report, on the player's PC, which a public app may do, and sends the crash code, the
module's name and the offset, nothing more (the plan, §2)."""
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
            self._changed()

    def job(self, name: str, ok: bool, seconds: float, error=None, build_errors: int = 0) -> None:
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
            self._changed()

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


def read_dump(path) -> dict | None:
    """From a crash report file, read on this PC only: {"code", "module", "offset"} and, for the game's script-error stop
    (0x29a), "traceback" (the game Python's text, paths cut). None if it can't be read. The dump never leaves the
    PC (the plan, §2)."""
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    if data[:4] != b"MDMP":
        return None
    try:
        count, rva = struct.unpack_from("<II", data, 8)
        streams = {}
        for i in range(count):
            kind, size, at = struct.unpack_from("<III", data, rva + 12 * i)
            streams[kind] = (at, size)
        if 6 not in streams:  # ExceptionStream
            return None
        at, _size = streams[6]
        code, _flags, _rec, address = struct.unpack_from("<IIQQ", data, at + 8)
        module, offset = "?", address
        if 4 in streams:  # ModuleListStream
            mat, _ = streams[4]
            (n,) = struct.unpack_from("<I", data, mat)
            for i in range(n):
                base, size, _sum, _stamp, name_rva = struct.unpack_from("<QIIII", data, mat + 4 + 108 * i)
                if base <= address < base + size:
                    (length,) = struct.unpack_from("<I", data, name_rva)
                    name = data[name_rva + 4:name_rva + 4 + length].decode("utf-16-le", "replace")
                    module, offset = re.split(r"[\\/]", name)[-1], address - base
                    break
    except struct.error:
        return None
    module = re.sub(r"[^A-Za-z0-9_.+ -]", "_", module)[:64] or "?"
    out = {"code": f"0x{code:x}", "module": module, "offset": f"0x{offset:x}"}
    if code == 0x29A:
        at = data.find(b"Traceback (most recent call last)")
        if at >= 0:
            end = data.find(b"\x00", at)
            text = data[at:end if end > at else at + TRACEBACK_CHARS].decode("latin-1", "replace")
            out["traceback"] = no_paths(text)[:TRACEBACK_CHARS]
    return out


class GameWatch(threading.Thread):
    """Beside the game the apps started (rusemod.play.Starter): when it closes, the minutes it ran with its mods, and
    any crash report it left since it started."""

    def __init__(self, watch: Watch, process, listed: list[str], own: int, sleep=time.sleep, clock=time.time,
                 local: str | None = None):
        super().__init__(daemon=True, name="bug-watch-game")
        self.watch, self.process, self.listed, self.own = watch, process, listed, own
        self.sleep, self.clock, self.local, self.started = sleep, clock, local, clock()

    def run(self) -> None:
        while self.process.poll() is None:
            self.sleep(5)
        self.watch.played((self.clock() - self.started) / 60.0, self.listed, self.own)
        for dump in crash_dumps_since(self.started, self.local):
            found = read_dump(dump)
            if found:
                self.watch.game_crash(found, self.listed, self.own)


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
        _current.call(name, time.perf_counter() - started, error)


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
