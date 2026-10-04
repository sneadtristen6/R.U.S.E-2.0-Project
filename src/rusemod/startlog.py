"""How long each app takes to start, for a player's report (the owner, 2026-10-04: RUSE Studio 0.9.5 "took a long ...
time to load, over 360 seconds", while its own start-up calls each take under a second on the same PC). Each start is
one line of `<platform folder>/logs/<app>-start.log`: the date and version, then the seconds since the program
started at each step, in the order they happened:

  python     the app's first line of Python runs (before it: the program itself, its DLLs and Python starting)
  imports    the app's modules are loaded
  api        its back end is made
  app_list   Windows' list of installed apps is checked (rusemod.update.fix_app_list_version; the installed app only)
  pywebview  the window library is loaded
  engine     the web engine is checked (rusemod.webui.web_engine_ok: .NET and WebView2 load here)
  window     the window is asked for
  shown      the window is on the screen
  page       its page is loaded
  loaded     the page can call the back end
  <call>     the page's first call of each kind: when it was asked + how long it took ("+?": no answer yet)
  ready      the page has drawn its first screen (it says so: StartCalls.start_mark)
  <call> done / failed   a job started by one of those calls ended (the clean game backup, the game index)
  closed     the window was closed

  2026-10-04 14:02:11 studio 0.9.5: python 0.41, imports 1.32, api 1.33, (...) status 4.58+0.01, (...) ready 4.62

The file keeps the last KEEP starts, each line cut at LINE characters, so it stays under 10 KB. It's written again
WAIT seconds after each change, by a thread of its own (a write took 7 to 8 ms on the owner's PC, 2026-10-04: the
page's calls never wait for one), and once more when the window closes; so a start that never finished (the player
closed the app) still shows how far it got. Writing it never stops an app: a log that can't be written is skipped.
The troubleshooter's report carries the last REPORT starts (rusemod.doctor.report)."""
from __future__ import annotations

import inspect
import os
import sys
import threading
import time
from pathlib import Path

KEEP = 20              # starts kept in the file
LINE = 500             # characters a start's line may take: KEEP lines stay under 10 KB
CALLS = 24             # first calls recorded per start
AFTER_READY = 120      # seconds after "ready" in which a first call still counts as the start's
REPORT = 5             # starts the troubleshooter's report carries
WAIT = 0.25            # seconds the writer waits after a change, so the changes close together are one write
PAGE_MARKS = {"ready"}  # what the page may mark (StartCalls.start_mark)
QUIET = {"start_mark", "job"}  # calls never listed: the mark itself, and following a job (asked every 0.4 s)

_lock = threading.RLock()       # what happened: one change at a time
_file_lock = threading.RLock()  # the file: one write at a time, and no read of it mid-write
_log: StartLog | None = None  # the running app's log (one app per program)


def process_start() -> float | None:
    """When this program started, in time.time()'s seconds, as Windows recorded it; None elsewhere or when it can't
    be read."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)  # its own copy: the types set here stay here
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        k32.GetProcessTimes.restype = wintypes.BOOL
        times = [wintypes.FILETIME() for _ in range(4)]  # created, exited, kernel time, user time
        if not k32.GetProcessTimes(k32.GetCurrentProcess(), *[ctypes.byref(t) for t in times]):
            return None
        created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime  # 100 ns steps since 1601
        return created / 10_000_000 - 11_644_473_600
    except Exception:  # noqa: BLE001  (an odd Windows: the log starts at Python's first line instead)
        return None


def _num(seconds: float) -> str:
    """4.50 -> "4.5", 0.001 -> "0", 360.0 -> "360": two decimals at most."""
    return f"{max(seconds, 0.0):.2f}".rstrip("0").rstrip(".")


class StartLog:
    """One start of an app: its steps and its page's first calls, written to `path` as they happen (once live)."""

    def __init__(self, app: str, path: Path, started: float, version: str = ""):
        self.app, self.path, self.version, self.started = app, Path(path), version, started
        self.entries: list[list] = []  # [seconds since start, name, end (calls only, None while running), is call]
        self.calls: set[str] = set()   # the calls listed
        self.jobs: dict[str, str] = {}  # job id -> the call that started it, until it ends
        self.live = False              # written to the file (after the self-test check: a self-test isn't a start)
        self.ready_at: float | None = None
        self.closed = False
        self._changed = threading.Event()  # something to write: the writer thread (go) writes it WAIT seconds later

    # --- what happened ---
    def _now(self) -> float:
        return time.time() - self.started

    def mark(self, name: str, at: float | None = None) -> None:
        """A step, now (or at the time.time() `at`); a step already marked stays at its first time. "closed" is
        written at once: the program ends right after it."""
        with _lock:
            if any(not e[3] and e[1] == name for e in self.entries):
                return
            seconds = self._now() if at is None else at - self.started
            self.entries.append([seconds, name, None, False])
            if name == "ready":
                self.ready_at = seconds
            if name == "closed":
                self.closed = True
            self._write()
        if name == "closed":
            self.flush()

    def watching(self) -> bool:
        """Whether a call can still add to the log: a first call during the start, or the end of a job it started."""
        return not self.closed and (self.counting() or bool(self.jobs))

    def counting(self) -> bool:
        """Whether a first call still counts as part of the start."""
        return (not self.closed and len(self.calls) < CALLS
                and (self.ready_at is None or self._now() - self.ready_at <= AFTER_READY))

    def call_started(self, name: str) -> list | None:
        """The page asks for `name`: listed when it's the first of its kind during the start. Returns its entry."""
        with _lock:
            if name in QUIET or name in self.calls or not self.counting():
                return None
            self.calls.add(name)
            entry = [self._now(), name, None, True]
            self.entries.append(entry)
            self._write()
            return entry

    def call_ended(self, entry: list | None, name: str, out=None) -> None:
        """The call (`entry` when listed) answered `out`: a job it started is followed until it ends."""
        with _lock:
            changed = False
            if entry is not None:
                entry[2] = self._now()
                changed = True
            if isinstance(out, dict):
                if entry is not None and isinstance(out.get("job"), str):
                    self.jobs[out["job"]] = name
                ended = out.get("state") in ("done", "failed") and self.jobs.pop(str(out.get("id")), None)
                if ended:
                    self.entries.append([self._now(), f"{ended} {out['state']}", None, False])
                    changed = True
            if changed:
                self._write()

    # --- the file ---
    def header(self) -> str:
        return f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.started))} {self.app} {self.version}".rstrip()

    def line(self) -> str:
        """This start as one line, at most LINE characters: the latest calls give way first (" ..." says some did),
        then the rest is cut."""
        parts = [(e[3], f"{e[1]} {_num(e[0])}" + (("+" + ("?" if e[2] is None else _num(e[2] - e[0]))) if e[3] else ""))
                 for e in sorted(self.entries, key=lambda e: e[0])]
        head, cut = self.header() + ":", False

        def text() -> str:
            return head + " " + ", ".join(p for _c, p in parts) + (" ..." if cut else "")

        while len(text()) > LINE:
            calls = [i for i, (is_call, _p) in enumerate(parts) if is_call]
            if not calls:
                break
            del parts[calls[-1]]
            cut = True
        out = text()
        return out if len(out) <= LINE else out[:LINE - 3] + "..."

    def _write(self) -> None:
        """Something changed: the writer thread writes it soon."""
        if self.live:
            self._changed.set()

    def flush(self) -> None:
        """Write this start's line into the file now, in place of its line there, after the last KEEP - 1 others."""
        with _file_lock:  # the line is made under the file's lock: a later write never carries an older line
            with _lock:
                if not self.live:
                    return
                line, mine = self.line(), self.header() + ":"
            tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")
            try:
                try:
                    old = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
                except OSError:
                    old = []
                lines = [ln[:LINE] for ln in old if ln.strip() and not ln.startswith(mine)][-(KEEP - 1):] + [line]
                self.path.parent.mkdir(parents=True, exist_ok=True)
                tmp.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
                os.replace(tmp, self.path)
            except Exception:  # noqa: BLE001  (a log that can't be written never stops the app)
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass

    def _writing(self) -> None:
        """The writer thread: each change written WAIT seconds after it, with the ones that came meanwhile; it ends
        with the window ("closed" is written at once)."""
        while True:
            self._changed.wait()
            time.sleep(WAIT)
            self._changed.clear()
            if self.closed:
                return
            self.flush()

    def go(self) -> None:
        """From now on the start is written to the file (what happened so far at once)."""
        with _lock:
            if self.live:
                return
            self.live = True
        self.flush()
        threading.Thread(target=self._writing, name="start-up log", daemon=True).start()


def path_of(app: str, home: Path | None = None) -> Path:
    from .home import default_home
    return Path(home or default_home()) / "logs" / f"{app}-start.log"


def begin(app: str, version: str = "", python: float | None = None, home: Path | None = None) -> StartLog:
    """The start-up log of this program, made on the first call (`python`: the time.time() its first line ran, else
    now); later calls give the version. Nothing is written before go()."""
    global _log
    if _log is not None and _log.app != app:
        stop()  # before taking _lock: stop takes the file's lock first, as a write does
    with _lock:
        if _log is None:
            now = time.time()
            started = process_start()
            if started is None or not now - 86_400 < started <= now:
                started = python or now
            _log = StartLog(app, path_of(app, home), started)
            _log.mark("python", python or now)
        if version:
            _log.version = version
        return _log


def current() -> StartLog | None:
    return _log


def stop() -> None:
    """No start-up log for this program (a self-test isn't a player's start): nothing more is written, and its writer
    thread ends."""
    global _log
    with _file_lock, _lock:  # a write under way finishes first
        if _log is not None:
            _log.live, _log.closed = False, True
            _log._changed.set()
        _log = None


def mark(name: str) -> None:
    """A step of the running app's start, when there is a log."""
    log = _log
    if log is not None:
        log.mark(name)


def recent(app: str, home: Path | None = None, n: int = REPORT) -> list[str]:
    """The last `n` starts of `app` from its log, oldest first (none when there's no log or it can't be read)."""
    with _file_lock:
        try:
            lines = path_of(app, home).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
    return [ln[:LINE] for ln in lines if ln.strip()][-n:]


def timed(api, log: StartLog | None = None):
    """Have `log` (the running app's) note the window's calls to `api`: each public method is wrapped, on this object
    only, by one that tells the log when a call starts and ends. pywebview reads a method's parameter names to hand
    it to the page, so each wrapper carries its method's signature. Returns `api`."""
    log = log or _log
    if log is None:
        return api
    for name in dir(type(api)):
        if name.startswith("_"):
            continue
        try:
            raw = inspect.getattr_static(api, name, None)
            if inspect.isfunction(raw):  # plain methods: not properties, static or class methods
                setattr(api, name, _wrapped(log, name, getattr(api, name), raw))
        except Exception:  # noqa: BLE001  (the log never stops the app: that call just isn't timed)
            continue
    return api


def _wrapped(log: StartLog, name: str, method, raw):
    def call(*args, **kwargs):
        if not log.watching():
            return method(*args, **kwargs)
        entry = log.call_started(name)
        try:
            out = method(*args, **kwargs)
        except BaseException:
            log.call_ended(entry, name)
            raise
        log.call_ended(entry, name, out)
        return out

    call.__name__, call.__qualname__, call.__doc__ = name, name, raw.__doc__
    call.__signature__ = inspect.signature(raw)  # the class's function: `self` first, as pywebview expects
    return call


class StartCalls:
    """The window API's start-up call, for both apps (a mixin): the page says when it has drawn its first screen."""

    def start_mark(self, what: str = "ready") -> dict:
        if what in PAGE_MARKS:
            mark(what)
        return {}
