"""Bug Watch: what the Studio and the Launcher do and where they fail, and the game's crashes with the mods that were
on, counted on the PC and sent once a day to our developers' server (the plan: the RUSE Guard repository's
docs/BUG_WATCH.md; what the server takes: its cloudflare/bug-watch/PAYLOADS.md).

Opt-in (the owner, 2026-10-22): nothing is counted, kept or sent unless the player ticked Bug Watch (settings.json
"bugwatch": {"on": true}) and so has an install ID and a username ("player": {"id": 32 random characters, "name":
"Nick#4821"}). `RUSE_NO_BUGWATCH=1` turns it off on a PC whatever the settings say. And `ON` below is the code's own
switch, beside RUSE Guard's fairplay.ON: off until the owner says.

WHAT THE AGREEMENT SAYS, KEPT (2026-11-24): the player's untick deletes what the PC kept and nothing comes back, in
either app of this version, not even after a later tick (turn_off; Watch._now_on reads the setting at every count, save
and send). Known limits while the other app is still 0.9.8.22 or older (the two update one at a time): that app writes
its own counts back at its end, as 0.9.8.22 did, and its untick leaves no mark for the counts this app made since its
last save (Watch._now_on); both end once both apps are this version. The game's error text goes out with the player's
own folders named for anyone and any other full path cut to its file name, spaces, Python's doubled \\ and network
paths too (no_paths), then through RUSE Guard's own cleaning: a SteamID64 and any number of 9 digits or more (no_ids;
a Steam ID written another way, as STEAM_0:1:... or [U:1:...], is not looked for). Only the game's own crash reports
are read (game_report). Settings' "Save username" saves the name only, never ticking Bug Watch (the pages call
set_username, as the first start does).

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
could not be told from a hundred others): every failed call and job is also counted, under "messages", by its name
and the error's own key when it has one, as "new_set:set_no_mods" (the Launcher's mod set refusals), and otherwise by
its name and where in our own code it came from, as "play:rusemod.play:327": a module's name and a line number, which
the app's version turns back into the very line (reason_key, site_of). A refusal the page makes itself, before any
call, is counted by the page under "messages" as "page:new_set:set_no_mods" (BugWatchCalls.bugwatch_seen). A build that lists mistakes in the mods counts each by where the build found it,
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

VERSION 4 OF THE AGREEMENT (rusemod.guard.TERMS_VERSION 4, 2026-11-13; the owner's "sure" to its items): only for a
player who accepted it (allows_v4), a send also says which version was accepted ("agreement"); a game crash report the
map the game's script-error text names (the game's own map by its name, any other only as "own": map_of), what the
player's own mods hold (own_holds: for each kind of thing, OWN_KINDS, how many of them hold it) and the unit the game
was making at one of the crashes we know (one of the game's own units by its number, {"game": <its number>}; a unit a
mod added only as {"added": true}: unit_sent, unit_named; version 4's "The apps send the unit only when they can read
it from the game's crash report"); a day the same kinds, the most of any game that day; a failed Play or Test in game
its own mods by format and the kinds they hold. Under version 3 a failed Play's own mods are one number
("play:set:L1-O2"), as version 3's words say.

THE DAY'S LIST OF FAILURES (the owner's answers of 2026-11-26, B6 B to B11 B; rusemod.codes): only under the agreement
version that describes it (CODES_AGREEMENT; below it a day goes exactly as before), a day's send also lists the
failures the player met, at most 20, each by its code (L-SET-08, S-TST-02, BLD-123) with how far a Play or a Test in
game got, its set's shape, and numbers only: a count, the Windows error number, the web server's answer number, the
game's exit number, and another code saying why (failure_entry). The keys under "messages" go on beside it. What sent
nothing before is in it too: sign-in answers that aren't errors, the mod list or the update check failing, a crash
report that can't be read, a game that ended badly (its exit number), a page's own script error (its screen's name and
the error's short name, Watch.page_error), and a game the app was closed under (its note, notes_left). A refusal of
what the player entered (the Studio's EntryError, B10 A) sends nothing at all.

THE CRASHES WE KNOW, TOLD TO THE PLAYER (the owner's item 25, 2026-11-13: "It should tell them the unit that it was
making when it crashed." and "For 25, they should also be told why that unit made the game crash."): a game crash at
a place our list of known crashes knows gets its plain reason (read_dump's "reason"), and under version 4 the unit the
game was making (read_dump's "unit"), named from the crashed copy's own data as its card says (unit_named). Neither
the reason nor the name is ever sent. The list is ours and private since 2026-11-24 (the owner: "Okay, fine. We can
move it to the private repo."): the Bug Watch server hands it to the apps, signed, and each app keeps a copy on the PC
and checks a crash against it there (rusemod.knowncrashes: fetched when a game starts, only under version 5 of the
agreement); with no list on the PC the notice says the Launcher couldn't check the crash ("list": False), and each
such case is counted ("crash_no_list", "crashlist:<why the download failed>", "crashlist:build-missing"). GameWatch
keeps the notice for the game it watched, before anything of Bug Watch's own is written (a record that can't be written
never costs the player it), and drops one never taken when the next game starts; the window's bugwatch_crash hands it
to the page once: the Launcher says it after a Play, or when its page opens again.

THE CRASH CODE (the owner, 2026-11-14, for players without Bug Watch: "they should be given some sort of code that they
can tell me that still tells us why it crashed, but maybe not be as specific if they don't select bug watch"; and
2026-11-26, for every player: "... send this report to me on either GitHub or Discord. ... And then be like, copy
code."): after a game the Launcher started crashed (version 5 of the agreement accepted: crash_code_given), the
Launcher shows a short code made from where the game stopped (rusemod.crashcode), Bug Watch on or off, for the player
to send us with a screenshot. With Bug Watch off, CodeWatch reads the game's own crash report on the PC as read_dump
does; with it on, GameWatch puts the same code in its notice. Nothing more is counted, kept or sent for it: the code
goes in no report, and without Bug Watch the apps don't contact our server for it.

Checked our_tools.json: crash_site.py reads a whole crash report for our own research and is private; this module
reads only the exception record, the module list and the crashed thread's stack of the game's crash report (and, at
a crash we know, the memory the report kept round that stack's words, for the unit), on the player's PC, as any crash
reporter does, and sends the crash code, the module's name and the offset, the access and the chain, and under
version 4 the unit as above, nothing more (the plan, §2). For the chain it reads the copy's RUSE.exe section table and
the few bytes before each stack word that points into it: a word right after a call is where that call returns to
(2026-11-02, the owner's "Yes, add it": a player's crash report named only where the game stopped)."""
from __future__ import annotations

import bisect
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
# a full Windows path (no_paths): its drive, its folders, spaces and all (each one up to its next slash, any number of
# them: Python prints a path's \ as \\), then its last part up to a space or a quote
ABSOLUTE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]+(?:[^\\/\r\n\"'<>|*?:]+[\\/]+)*[^\s\\/\"'<>|*?:]*")
# a network path (\\server\share\..., as Windows writes it, or Python's \\\\server\\share), where a path starts: a
# server's name, then at least one more part, as above
NETWORK = re.compile(r"(?<![^\s\"'(\[=,;])\\{2,}[A-Za-z0-9._$-]+[\\/]+(?:[^\\/\r\n\"'<>|*?:]+[\\/]+)*"
                     r"[^\s\\/\"'<>|*?:]*")


# --- the player's yes -------------------------------------------------------------------------------------------
def _settings(home) -> dict:
    from .home import settings
    return settings(Path(home))


def enabled(home) -> bool:
    """Whether Bug Watch counts and sends on this PC: the code's switch, no RUSE_NO_BUGWATCH, the player's tick and an
    install ID."""
    return not _switched_off() and _ticked_in(_settings(home))


def _switched_off() -> bool:
    """The code's own switch (ON) off, or RUSE_NO_BUGWATCH on this PC: off, whatever the settings say."""
    return not ON or os.environ.get("RUSE_NO_BUGWATCH", "").strip() not in ("", "0")


def _ticked_in(values: dict) -> bool:
    """The player's own tick and an install ID, in settings.json's values as read (enabled, Watch._now_on)."""
    return bool((values.get("bugwatch") or {}).get("on")) and _good_id((values.get("player") or {}).get("id"))


def _untick_mark(values: dict) -> str:
    """The mark the player's last untick left in settings.json ("bugwatch": {"untick_mark"}, a new one at each untick:
    turn_off; "" before any). Counts an app made under another mark were made before that untick, so they are never
    kept or sent, in whichever app they were made (Watch._now_on)."""
    mark = (values.get("bugwatch") or {}).get("untick_mark")
    return mark if isinstance(mark, str) else ""


def _settings_now(home, tries: int = 3) -> dict | None:
    """settings.json as it is now ({} when there is none yet), or None when it is there but can't be read: the other
    app may be writing it this very moment (rusemod.home.save_settings), and a file half written is no untick
    (Watch._now_on, start)."""
    p = Path(home) / "settings.json"
    for attempt in range(tries):
        try:
            values = json.loads(p.read_text(encoding="utf-8"))
            return values if isinstance(values, dict) else None
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            if attempt + 1 < tries:
                time.sleep(0.02)
    return None


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
    unless RUSE Guard's program check still uses it (the plan, §3: "Turn both off and the ID is deleted").

    What was kept is deleted and never comes back (the agreement: "Untick it any time in Settings: nothing more is
    counted or sent, and what was kept is deleted"): this app's counts in memory go at once, and the new untick mark
    (_untick_mark) tells every app's Watch of this version, the other app's too (both apps can run at once, and this
    untick can't reach that app's memory), that what it counted before is never written or sent, even after the player
    ticks it again. The other app still on 0.9.8.22 or older reads no mark: Watch._now_on's known limits."""
    from .home import save_settings
    values = _settings(home)
    values["bugwatch"] = {**(values.get("bugwatch") or {}), "on": False, "untick_mark": secrets.token_hex(8)}
    if not (values.get("guard") or {}).get("terms"):   # RUSE Guard (terms accepted) keeps the shared username for its records
        values.pop("player", None)
    save_settings(Path(home), values)
    watch = _current
    if watch is not None and watch.home == Path(home):
        with watch.lock:
            watch._now_on()   # (the new mark: this app's counts in memory go)
    _delete_kept(home)
    return {"on": False}


def _delete_kept(home) -> None:
    """Every count and send Bug Watch keeps on this PC deleted: the days' counts and the outbox (its folder's files)."""
    folder = Path(home) / FOLDER
    for p in sorted(folder.rglob("*.json"), reverse=True) if folder.is_dir() else []:
        try:
            p.unlink()
        except OSError:
            pass


def status(home) -> dict:
    """What Settings shows: whether this build has Bug Watch, on or off, the username and the report code (the ID's
    first 8 characters)."""
    values = _settings(home)
    player = values.get("player") or {}
    return {"available": ON, "on": enabled(home), "name": player.get("name", ""),
            "code": player["id"][:8] if _good_id(player.get("id")) else ""}


# --- what version 4 of the agreement added (the owner, 2026-11-13: "sure", to "What version 4 of the agreement adds:
# the unit at a model crash, the game mode, and what a player's own mod holds"; the map of a script error with it).
# The game mode was taken out of version 4's words afterwards (item 26, left to us: nothing can read the mode from the
# game's crash report), so nothing here reads or sends it -------------------------------------------------------
AGREEMENT_V4 = 4  # the agreement's version (rusemod.guard.TERMS_VERSION) from which the fields below may go
# What a player's own mods hold, by kind: for each kind, how many of the player's own mods hold it (never a name, a
# word, a path or a file; own_holds). "folder" and "rmod": how many are of each format.
OWN_KINDS = ("folder", "rmod", "data", "new_objects", "texts", "maps", "missions", "scripts", "models", "pictures",
             "sounds", "game_files", "assets")
# the map the game's script-error text names ("Current Map: DataDir:\DATASMAP\<map pack>", the game's own words)
CURRENT_MAP = re.compile(rb"Current Map: DataDir:[\\/]+DATASMAP[\\/]+([A-Za-z0-9_]{1,64})")
OWN_MAP = "own"  # a map the game's install hasn't got (a mod made it): said only as this, never by its name


def agreement(home) -> int:
    """The version of the agreement the player accepted (settings.json guard.terms, rusemod.guardcalls), 0 for none."""
    terms = (_settings(home).get("guard") or {}).get("terms", 0)
    return terms if isinstance(terms, int) and not isinstance(terms, bool) and terms > 0 else 0


def allows_v4(home) -> bool:
    """Whether what version 4 of the agreement added may be counted and sent: Bug Watch on (enabled) and version 4 or
    later accepted. A player who ticked Bug Watch under version 3 sends only what version 3 lists until the apps have
    shown version 4 and the player accepted it (the agreement screen, at the next start)."""
    return enabled(home) and agreement(home) >= AGREEMENT_V4


AGREEMENT_V5 = 5  # the agreement's version from which the apps fetch our list of known crashes (rusemod.knowncrashes)
#                   and the Launcher shows its player a crash code (crash_code_given)


def allows_v5(home) -> bool:
    """Whether our list of known crashes may be fetched from the Bug Watch server: Bug Watch on (enabled) and version 5
    or later of the agreement accepted, the version whose words say so (rusemod.knowncrashes.refresh)."""
    return enabled(home) and agreement(home) >= AGREEMENT_V5


# --- the day's list of failures, each by its code (the owner's B6 B and B7 B, 2026-11-26: "each failure goes in a short
# list in the day's send", with "the code, where in our code, counts, plus three numbers that name no player: the
# Windows error number, the web server's answer number, the game's exit number"; rusemod.codes) ---------------------
# The agreement version from which the list and its numbers are counted and sent: the legal session's version 5 notice
# is to describe them (which version does: not said yet, so it is this one constant). Below it nothing new is counted
# or sent: the day goes as before.
CODES_AGREEMENT = 5
FAILURES_MOST = 20      # entries in a day's list (the server's LIMITS.failures); a failure the list holds already: once
MISTAKES_MOST = 8       # entries one build's listed mistakes may take of them, beside the build's own
DETAIL_MOST = {"n": MAX_COUNT, "win": 4294967295, "http": 599, "exit": 4294967295}  # the server's highest each
SHAPE_RE = re.compile(r"L[0-9]{1,3}-(?:F[0-9]{1,3}-R[0-9]{1,3}|O[0-9]{1,3})")


def _entry(error) -> bool:
    """Whether an error is a refusal of what the player entered (`bw_entry`: the Studio's EntryError), which Bug Watch
    sends nothing for (the owner's B10 A)."""
    return error is not None and getattr(error, "bw_entry", False) is True


def allows_codes(home) -> bool:
    """Whether the day's list of failures and its numbers may be counted and sent: Bug Watch on and the agreement
    version that describes them (CODES_AGREEMENT) or a later one accepted."""
    return enabled(home) and agreement(home) >= CODES_AGREEMENT


def detail_of(error) -> dict:
    """The numbers a failure's error says, none naming a player: those it carries (rusemod.codes.coded), the web
    server's answer number of an HTTP refusal (http), and the Windows error number of a file or network error (win:
    os_number, also for a network error urllib wrapped)."""
    out = dict(getattr(error, "bw_detail", None) or {}) if error is not None else {}
    if "http" not in out and isinstance(error, urllib.error.HTTPError):
        out["http"] = error.code
    elif "win" not in out and (number := os_number(error)) is not None:
        out["win"] = number
    return out


def os_number(error) -> int | None:
    """The Windows error number of a file or network error, None when it has none: the number Windows gave
    (winerror), else the one Python gave (errno; a name not found gives getaddrinfo's own, 11001); for a network error
    urllib wrapped (URLError: "couldn't reach the server"), its reason's. Never an SSL library's own number
    (ssl.SSLError: OpenSSL's, not Windows'), nor for a web server's answer (HTTPError: that is its http). A timeout of
    our own (TimeoutError "timed out") has none."""
    import ssl
    inner = getattr(error, "reason", None) if isinstance(error, urllib.error.URLError) else None
    for e in (inner, error):
        if isinstance(e, OSError) and not isinstance(e, (ssl.SSLError, urllib.error.URLError)):
            number = getattr(e, "winerror", None) or e.errno
            if isinstance(number, int) and not isinstance(number, bool):
                return number
    return None


def _shape(found, v4: bool) -> str | None:
    """A failed Play's or Test in game's mod set as Watch._failed writes it (L2-F1-R0; before version 4 L2-O1)."""
    if not (isinstance(found, tuple) and len(found) == 3):
        return None
    listed, folders, rmods = found
    shape = (f"L{len(listed)}-F{int(folders)}-R{int(rmods)}" if v4 else
             f"L{len(listed)}-O{int(folders) + int(rmods)}")
    return shape if SHAPE_RE.fullmatch(shape) else None


def failure_entry(app: str, code: str, stage=None, shape=None, detail=None) -> dict | None:
    """One entry of the day's list as the server takes it (PAYLOADS.md "failures"): the code as `app` sends it
    (rusemod.codes.wire), how far a Play or Test in game got, the set's shape, and only numbers and codes in its
    detail. None for no code."""
    from .codes import wire
    wired = wire(code, app)
    if not wired:
        return None
    out: dict = {"code": wired}
    if stage in STAGES:
        out["stage"] = stage
    if isinstance(shape, str) and SHAPE_RE.fullmatch(shape):
        out["set"] = shape
    kept = {}
    for key, value in (detail or {}).items():
        if key in DETAIL_MOST and isinstance(value, int) and not isinstance(value, bool):
            kept[key] = value % 2 ** 32 if key in ("win", "exit") else value  # (a negative exit: as Windows says it)
            if not 0 <= kept[key] <= DETAIL_MOST[key]:
                kept.pop(key)
        elif key == "why" and wire(value, app):
            kept["why"] = wire(value, app)
    if kept:
        out["detail"] = kept
    return out


def game_maps(game) -> dict[str, str]:
    """The game's own map packs, from its install: {name in lower case: the pack's own name}, from
    Maps/PC/DataMap<name>_v09.dat. A map a mod makes is only in the modded copy, never in the install, so it isn't
    here."""
    try:
        return {p.name[7:-8].lower(): p.name[7:-8] for p in (Path(game) / "Maps" / "PC").glob("DataMap*_v09.dat")
                if len(p.name) > 15}
    except (OSError, TypeError):
        return {}


def map_of(data: bytes, maps: dict[str, str]) -> str | None:
    """The map a crash report's script-error text names: the game's own map by its pack's name, any other as OWN_MAP
    (its name is a mod's), None when the report names none."""
    found = CURRENT_MAP.search(data)
    if found is None:
        return None
    return maps.get(found.group(1).decode("ascii").lower(), OWN_MAP)


def _folder_holds(folder: Path) -> set[str]:
    """What kinds of thing one mod folder in our format holds (OWN_KINDS), from where its files are (MOD_FORMAT.md)."""
    found = set()

    def has(pattern: str) -> bool:
        return next(folder.glob(pattern), None) is not None

    rndf = sorted(folder.glob("src/**/*.rndf"))
    if rndf:
        found.add("data")
        from .rndf import parse
        for f in rndf:
            try:
                if any(op.kind in ("create", "clone") for op in parse(f.read_text(encoding="utf-8"), file=f.name,
                                                                         mod="mod")):
                    found.add("new_objects")
                    break
            except Exception:  # noqa: BLE001 - a file the build itself would refuse: its kind is still "data"
                continue
    if has("text/*.csv"):
        found.add("texts")
    maps = [p for p in folder.glob("maps/*/*") if p.is_file()]
    if any(p.name.lower() not in ("mission.toml",) for p in maps):
        found.add("maps")
    if any(p.name.lower() == "mission.toml" for p in maps) or has("menus.toml"):
        found.add("missions")
    if has("scripts/**/*.py") or has("scripts/**/*.xyz"):
        found.add("scripts")
    if has("files/models/**/*") or has("files/anim/**/*") or has("files/replace/**/*"):
        found.add("models")
    if has("files/cards/**/*") or has("files/textures/**/*") or has("files/ground/**/*"):
        found.add("pictures")
    if has("files/sound/**/*") or has("files/music/**/*") or has("maps/*/*.wav"):
        found.add("sounds")
    if has("files/game/**/*"):
        found.add("game_files")
    if has("files/assets/**/*") or has("files/buildings/**/*"):
        found.add("assets")
    return found


def _rmod_holds(path) -> set[str]:
    """What kinds of thing one .rmod mod holds (OWN_KINDS), from what it changes (rusemod.rmod.edits_of)."""
    from .rmod import edits_of, file_kind
    edits = edits_of(path)
    if edits is None:
        return set()
    found = set()
    for key in edits.values:
        found.add("maps" if str(key[1]).lower().endswith((".scenario", ".win")) else "data")
    if edits.creates:
        found.add("new_objects")
    if edits.texts:
        found.add("texts")
    kinds = {"script": "scripts", "script archive": "scripts", "picture": "pictures", "sound": "sounds",
             "sound archive": "sounds", "map file": "maps", "text file": "texts", "video": "game_files",
             "game data": "game_files"}
    for _digest, path_in in list(edits.files.values()) + [v[:2] for v in edits.inside.values()]:
        found.add(kinds.get(file_kind(path_in), "game_files"))
    return found


def own_holds(folders) -> dict[str, int]:
    """What the player's own mods among these mod folders hold (mods_of: any not from our mod list), by kind
    (OWN_KINDS): how many of them hold each kind, the kinds none holds left out. Never a name, a word, a path or a
    file. Never raises: a mod that can't be read counts by its format only."""
    from .rmod import rmod_of
    out: dict[str, int] = {}
    for folder in folders or []:
        folder = Path(folder)
        try:
            if mods_of([folder])[1] == 0:
                continue  # one from our mod list: named already, by id and version
            rmod = rmod_of(folder) is not None
            kinds = {"rmod" if rmod else "folder"}   # its format: an .rmod (or one converted for the Studio), or ours
            if rmod:
                kinds |= _rmod_holds(folder)
            if folder.is_dir() and (folder / "mod.toml").is_file():
                kinds |= _folder_holds(folder)       # our format's own parts (an .rmod converted for the Studio too)
        except Exception:  # noqa: BLE001 - counting must never stop the app
            continue
        for kind in kinds & set(OWN_KINDS):
            out[kind] = out.get(kind, 0) + 1
    return {k: out[k] for k in OWN_KINDS if out.get(k)}


# --- making what's sent safe ------------------------------------------------------------------------------------
def no_paths(text: str) -> str:
    """`text` with no path left in it: the player's own folders written as Windows names them for anyone
    (community.private_paths_out), then any other full path cut down to its file name: one on a drive (ABSOLUTE) or a
    network path (NETWORK), its folders' spaces and Python's doubled \\ too (2026-11-24: until then a folder's space
    or a network path let the rest of the path through)."""
    from .community import private_paths_out
    out = private_paths_out(str(text or ""))
    out = NETWORK.sub(_last_part, ABSOLUTE.sub(_last_part, out))
    return LOOKS_LIKE_PATH.sub(" ", out)


def _last_part(found) -> str:
    """What no_paths leaves of a full path it found: its last part, the file's name."""
    return re.split(r"[\\/]", found.group(0).rstrip("\\/"))[-1] or ""


GAME_DATA = re.compile(r"(datadir:)", re.IGNORECASE)   # the game's own name for its data, in its error text


def no_ids(text: str) -> str:
    """`text` through RUSE Guard's own cleaning (guard.no_ids, the one RUSE Guard's line goes through): a SteamID64,
    any number of 9 digits or more, and a drive's path left, for the game's error text a crash report sends (read_dump,
    after no_paths). A Steam ID written another way (STEAM_0:1:..., [U:1:...]) or a shorter number is not looked for.
    The game's own name for its data, "DataDir:" as in 'File "DataDir:\\x\\menu.py", line 40', is no drive and is left
    as it is: that cleaning would take its "r:\\" for one and cut out the game's own script names, which no_paths
    keeps."""
    from .guard import no_ids as cleaned
    parts = GAME_DATA.split(str(text or ""))   # (the game's own "DataDir:" at every odd place)
    return "".join(part if i % 2 else cleaned(part.encode("utf-8", "replace")).decode("utf-8", "replace")
                   for i, part in enumerate(parts))


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
    not only its kind: the call's name and the error's own key when it carries one (the Launcher's
    LauncherError(key=...)), "new_set:set_no_mods", else the call's name and the check that refused, by a key that
    never changes ("play:build.load_mod", "play:nation-models": rusemod.checkkeys), else the call's name and where the
    error came from, "play:rusemod.play:327" (the app's version, sent with the day, says which code that line is in).
    Never the error's words: they can hold what the player typed, or a folder.

    The call's name is in front of a key too (FL-97, 2026-11-10): one key comes from several calls (set_gone from
    save_set, delete_set, duplicate_set...; set_no_mods from new_set, save_set, import_set, best_order), and a day
    with refusals of two calls could not say which was which; the server's rule 8 finds a call's refusals by that
    name in front."""
    key = getattr(error, "words_key", None)
    if isinstance(key, str) and key:
        key = key[-40:]
        return _name(f"{str(name)[:max(1, 63 - len(key))]}:{key}")
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
    mods (set_of), for Watch.job; under version 4 of the agreement also what the player's own mods hold (own_holds).
    Never raises."""
    try:
        if getattr(error, "stage", None) is None:
            error.stage = stage if stage in STAGES else None
        if getattr(error, "mod_set", None) is None:
            error.mod_set = set_of(list(folders or []))
        watch = current()
        if getattr(error, "own_holds", None) is None and error.mod_set[1] + error.mod_set[2] \
                and watch is not None and allows_v4(watch.home):
            error.own_holds = own_holds(list(folders or []))
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
    restart adds to them), and the outbox of what waits to be sent. Whether Bug Watch is on is read at each count,
    save and send (_now_on), never remembered: the player can untick it in the other app."""

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
        self._kept = False   # this Watch's days file there, as it last knew it: read at its start or written since
        values = _settings_now(self.home)
        # the untick mark these counts are made under (_now_on; None: not known, the settings can't be read now, and
        # then nothing kept is taken in)
        self.mark = _untick_mark(values) if values is not None else None
        try:
            if values is not None:
                self.days = json.loads(self.file.read_text(encoding="utf-8"))
                self._kept = True
        except (OSError, ValueError):
            self.days = {}

    def _now_on(self) -> bool | None:
        """Whether Bug Watch is on now, settings.json read now (None: it can't be read this moment, the other app
        writing it; then nothing is counted, written or dropped). Counts this app made before the player's last untick,
        here or in the other app (a new untick mark), go first; with Bug Watch off, all of them: what an untick
        deleted never comes back by a save or a send, not even after the player ticks it again. Under the lock.

        An untick in the other app while that app is still 0.9.8.22 or older (the Studio and the Launcher update one at
        a time) leaves no new mark, but deletes the kept files as every untick does: so this Watch's days file, there
        before (read at its start or written since) and gone now, is that untick too, and the counts made before it
        go, even when the player ticked it again there while this app counted nothing (2026-11-24). Known limits:
        counts this app made since its last save, before such an untick, have no file to tell by; and that older app
        still writes its own counts back at its end, as 0.9.8.22 did. Both end once both apps are this version."""
        values = _settings_now(self.home)
        if values is None:
            return None
        mark = _untick_mark(values)
        gone = self._kept and not self.file.exists()   # (deleted by an untick: turn_off, in either app, any version)
        if mark != self.mark or gone:
            self.days, self.mark, self._dirty, self._kept = {}, mark, 0, False
        if _switched_off() or not _ticked_in(values):
            self.days, self._dirty = {}, 0
            return False
        return True

    # recording (each does nothing when the player hasn't said yes)
    def _day(self) -> dict | None:
        if self._now_on() is not True:
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
        """A window call: its try, and when it failed, the error's kind, which refusal or failure it was (reason_key)
        and its code in the day's list (_coded). A refusal of what the player entered (an error marked `bw_entry`: the
        Studio's EntryError, the owner's B10 A, "send nothing for them") counts nothing at all, not even the try."""
        key = _name(name)
        if _entry(error):
            return
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
                self._coded(day, error, call=key)
            self._changed()

    def job(self, name: str, ok: bool, seconds: float, error=None, build_errors: int = 0, mistakes=()) -> None:
        """`mistakes`: for a build that listed mistakes in the mods, where the build found each one
        (rusemod.patch.Finding.site), counted under "messages" as "mistake:rusemod.build:1208" when the error
        doesn't say which check each was (its `error_keys`: _failed). A job ended by a refusal of what the player
        entered (`bw_entry`, B10 A) counts nothing at all."""
        key = _name(name) or "job"
        if not ok and _entry(error):
            return
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
                self._coded(day, error)
            self._changed()

    def _coded(self, day: dict, error, call: str | None = None) -> None:
        """A failed call's or job's entry in the day's list (B6 B): its code (rusemod.codes.code_of; a window call's
        own code in codes.toml for one no other code says, `call`), how far a Play or Test in game got and its set,
        and its numbers (detail_of); a build's listed mistakes each by its code beside it (the error's
        `error_codes`). Only under CODES_AGREEMENT; never stops the app."""
        try:
            if not allows_codes(self.home):
                return
            from .codes import code_of, for_call
            code = code_of(error) or (for_call(self.app, call) if call else "")
            if not code:
                return
            stage, shape = getattr(error, "stage", None), _shape(getattr(error, "mod_set", None),
                                                                  allows_v4(self.home))
            self._add_failure(day, failure_entry(self.app, code, stage, shape, detail_of(error)))
            mistakes = [c for c in dict.fromkeys(getattr(error, "error_codes", None) or []) if c]
            for mistake in mistakes[:MISTAKES_MOST]:
                self._add_failure(day, failure_entry(self.app, mistake, stage, shape))
        except Exception:  # noqa: BLE001 - counting must never stop the app
            pass

    def _add_failure(self, day: dict, entry: dict | None) -> None:
        kept = day.setdefault("failures", [])
        if entry is not None and entry not in kept and len(kept) < FAILURES_MOST:
            kept.append(entry)

    def failure(self, code: str, error=None, shape=None, **detail) -> None:
        """A failure that is no window call's or job's error (a sign-in answer, a mod list that couldn't be had, a
        game that ended badly), by its code in the day's list, with its numbers (`detail`, and those `error` says:
        detail_of) and the set's shape. Only under CODES_AGREEMENT."""
        with self.lock:
            day = self._day()
            if day is None or not allows_codes(self.home):
                return
            numbers = detail_of(error) | {k: v for k, v in detail.items() if v is not None}
            self._add_failure(day, failure_entry(self.app, code, None, shape, numbers))
            self._changed()

    def page_error(self, screen: str, name: str) -> None:
        """A page's own script failed (the owner's B11 B: "the Studio page's own script errors send the screen's name
        and a short error name"): "page_error:<screen>:<name>" with the problems shown, and PAGE-01 in the day's list.
        Never the error's words, its file or its line. Only under CODES_AGREEMENT."""
        screen = re.sub(r"[^a-z0-9_-]", "", str(screen or "").lower())[:20] or "start"
        name = re.sub(r"[^A-Za-z0-9_]", "", str(name or ""))[:32] or "Error"
        with self.lock:
            day = self._day()
            if day is None or not allows_codes(self.home):
                return
            key = f"page_error:{screen}:{name}"
            day["messages"][key] = day["messages"].get(key, 0) + 1
            self._add_failure(day, failure_entry(self.app, "PAGE-01"))
            self._changed()

    def _failed(self, day: dict, job: str, error) -> bool:
        """What a failed Play or Test in game tells beyond its kind, under "messages" (2026-11-10: FL-98, FL-99), each a
        key of our own, never the words:
        - "play:stage:before" | build | listed | start: how far it got (rusemod.play.Starter.modded);
        - "play:set:L2-O1": the set's mods, L from our mod list, O the player's own (counted, never named), and
          "play:lib:cheat-mod-v2:2.0.0" for each from the list (id:version); under version 4 of the agreement (its "by
          kind and count") the own ones by format, "play:set:L2-F1-R0" (F folder mods, R .rmod files), and
          "play:own:<kind>" for each kind of thing they hold (OWN_KINDS: how many of them hold it, own_holds);
        - "mistake:<check>" for each listed mistake (rusemod.checkkeys: a rule's id, or the module and function that
          found it), "cause:<check or module.function>" for the caught error one said again, and for the refusal's
          own cause.
        Returns whether the error said its mistakes' checks (then the sites aren't counted again)."""
        def add(text: str, n: int = 1) -> None:
            k = _name(text)
            if k and len(text) <= 64 and (k in day["messages"] or len(day["messages"]) < 4 * MOST["messages"]):
                day["messages"][k] = day["messages"].get(k, 0) + max(1, int(n))

        try:
            stage = getattr(error, "stage", None)
            if stage in STAGES:
                add(f"{job}:stage:{stage}")
            found = getattr(error, "mod_set", None)
            if isinstance(found, tuple) and len(found) == 3:
                listed, folders, rmods = found
                if allows_v4(self.home):
                    add(f"{job}:set:L{len(listed)}-F{int(folders)}-R{int(rmods)}")
                    holds = getattr(error, "own_holds", None)
                    for kind, n in (holds.items() if isinstance(holds, dict) else ()):
                        if kind in OWN_KINDS and kind not in ("folder", "rmod") and isinstance(n, int) and n > 0:
                            add(f"{job}:own:{kind}", n)
                else:  # version 3 lists "how many ... (counted, never named)": one number (the owner's question)
                    add(f"{job}:set:L{len(listed)}-O{int(folders) + int(rmods)}")
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
        """One of: "screens" (a screen opened), "screen_used" (a screen did what it is for: a mod set made in the
        editor), "messages" (a problem shown: its words key), "checks" (a troubleshooter check that failed),
        "updates" ("offered" / "installed" / "failed")."""
        name = _name(key)
        with self.lock:
            day = self._day()
            if day is None or name is None:
                return
            if group in ("screens", "screen_used"):
                # (the server's rule 7 says "opened but never used" of a screen with no use counted: a screen that
                # is counted opened is counted used too)
                s = day["screens"].setdefault(name, {"opened": 0, "used": 0})
                s["opened" if group == "screens" else "used"] += 1
            elif group == "updates":
                if name in day["updates"]:
                    day["updates"][name] += 1
            elif group in ("messages", "checks"):
                day[group][name] = day[group].get(name, 0) + 1
            self._changed()

    def played(self, minutes: float, listed: list[str], own: int, holds: dict | None = None) -> None:
        """A game that ran `minutes` with these mods: `listed` the mod-list mods as id@version, `own` any others;
        `holds`: what those others hold (own_holds), kept only under version 4 of the agreement, each kind the most
        of any game that day."""
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
            if holds and own and allows_v4(self.home):
                kept = day.setdefault("own_holds", {})
                for kind, n in holds.items():
                    if kind in OWN_KINDS and isinstance(n, int) and n > 0:
                        kept[kind] = min(MOST["mods"], max(kept.get(kind, 0), n))
            self.save()

    def save(self) -> None:
        """The days' counts into the days file, only while Bug Watch is on, read at the save itself: the save at the
        app's end (start's atexit), an update's quit and a move's never write back what an untick deleted, here or in
        the other app; and an untick there while the file is written deletes it again."""
        with self.lock:
            self._dirty = 0
            if self._now_on() is not True or not self.days:
                return
            mark = self.mark
            try:
                self.folder.mkdir(parents=True, exist_ok=True)
                self.file.write_text(json.dumps(self.days), encoding="utf-8")
                self._kept = True
                if self._now_on() is False or self.mark != mark:
                    self.file.unlink(missing_ok=True)
                    self._kept = False
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
        v4 = allows_v4(self.home)
        if v4:  # what version 4 of the agreement added: the version accepted, what the player's own mods hold
            out["agreement"] = agreement(self.home)
            holds = {k: v for k, v in (counts.get("own_holds") or {}).items() if k in OWN_KINDS and v}
            if holds and counts.get("own_mods"):
                out["mods"]["holds"] = holds
        played = counts.get("played") or {}
        if played.get("total"):
            out["played"] = {"total": played["total"],
                             "mods": {m: v for m, v in played.get("mods", {}).items() if m in mods}}
        if counts.get("app_crashes"):
            out["app_crashes"] = min(MAX_COUNT, counts["app_crashes"])
        failures = [f for f in counts.get("failures") or [] if isinstance(f, dict) and f.get("code")]
        if failures and allows_codes(self.home):  # (B6 B: only under the agreement version that describes them)
            out["failures"] = failures[:FAILURES_MOST]
        while len(json.dumps(out, separators=(",", ":")).encode()) > DAY_BYTES and out.get("calls"):
            out["calls"].popitem()  # the least-used call goes first (they're in order of use)
        return out

    def language(self) -> str:
        """The app's language as its window keeps it (settings.json "prefs"), "us" when it keeps none: the language a
        crash's unit is named in (GameWatch)."""
        values = _settings(self.home)
        lang = ((values.get("prefs") or {}).get(self.app) or {}).get("lang") or values.get("lang")
        return lang if isinstance(lang, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,12}", lang) else "us"

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
            self._now_on()   # (counts made before the player's last untick go first: never sent)
            for day in sorted(self.days):
                if day >= today:
                    continue
                counts = self.days.pop(day, None)
                if counts is not None and day >= oldest and enabled(self.home):
                    moved += self._write_out(f"day-{self.app}-{day}.json", self.payload(day, counts))
            if self.days:
                self.save()
            else:
                self.file.unlink(missing_ok=True)
                self._kept = False   # (its own unlink: no untick)
        return moved

    def _write_out(self, name: str, body: dict) -> bool:
        """One send into the outbox, only while Bug Watch is on, read at the write as save reads it (one an untick
        meets while it is written goes at once). Whether it went in."""
        with self.lock:
            if self._now_on() is not True:
                return False
            mark = self.mark
            self.outbox.mkdir(parents=True, exist_ok=True)
            path = self.outbox / name
            path.write_text(json.dumps(body), encoding="utf-8")
            if self._now_on() is False or self.mark != mark:
                path.unlink(missing_ok=True)
                return False
            return True

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

    def game_crash(self, found: dict, listed: list[str], own: int, send=True, holds: dict | None = None) -> Path | None:
        """A game crash report (read_dump's `found`) with the mods that were on. Under version 4 of the agreement also
        the version accepted, the map the game's script-error text names (the game's own by its name, any other only
        as OWN_MAP), what the player's own mods hold (`holds`, own_holds) and the unit the game was making, when it
        was read and named (unit_sent: the game's own by its number, a mod's only as added). Never the crash's plain
        reason or the unit's name: those are only for the player (GameWatch's notice)."""
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
        if isinstance(found.get("ignored"), int) and found["ignored"] > 0:
            body["ignored"] = min(MAX_COUNT, found["ignored"])  # (the game's own text: version 3 lists it)
        if allows_v4(self.home):
            body["agreement"] = agreement(self.home)
            if isinstance(found.get("map"), str) and re.fullmatch(r"[A-Za-z0-9_]{1,64}", found["map"]):
                body["map"] = found["map"]
            kept = {k: v for k, v in (holds or {}).items() if k in OWN_KINDS and isinstance(v, int) and v > 0}
            if kept and own:
                body["own"] = kept
            unit = unit_sent(found)
            if unit is not None:
                body["unit"] = unit
        return self.crash(body, send)


UNIT_MOST = 1_000_000  # the server's most for a unit's number (worker.js MAX_UNIT): past it the whole report is refused


def unit_sent(found: dict) -> dict | None:
    """What a game crash report sends of the unit the game was making (version 4 of the agreement: "one of the game's
    own units by its number; a unit a mod added only as "a mod's unit""): {"game": its number} for one of the game's
    own, {"added": True} for one a mod added (never its number or its name), None when the unit wasn't read from the
    crash report, or wasn't found in the copy's data (unit_named: then whether a mod added it isn't known)."""
    number, added = found.get("unit"), found.get("unit_added")
    if not isinstance(number, int) or isinstance(number, bool) or not isinstance(added, bool):
        return None
    if added:
        return {"added": True}
    return {"game": number} if 1 <= number <= UNIT_MOST else None


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
                when = p.stat().st_mtime
            except OSError:
                continue
            if when >= since:
                found.append((when, str(p), p))
    # (in the order they were written, by the time read once: a report gone meanwhile must not stop the watch before
    # the player is told: GameWatch)
    return [p for _when, _name, p in sorted(found)]


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


def _kept_memory(data: bytes, streams: dict):
    """A reader of the memory a crash report kept: read(address, size) gives those bytes when one kept piece holds
    them all, else None. The game's own crash reporter keeps hundreds of pieces (round every word on the threads'
    stacks, from 256 bytes before it to 768 after): sorted once, each read is found by halving."""
    pieces = []
    if 5 in streams:  # MemoryListStream: (start, size, where) each
        at, _ = streams[5]
        (n,) = struct.unpack_from("<I", data, at)
        for i in range(n):
            start, size, where = struct.unpack_from("<QII", data, at + 4 + 16 * i)
            if where + size <= len(data):
                pieces.append((start, size, where))
    if 9 in streams:  # Memory64ListStream: (start, size) each, their bytes one after another from one place
        at, _ = streams[9]
        n, where = struct.unpack_from("<QQ", data, at)
        for i in range(n):
            start, size = struct.unpack_from("<QQ", data, at + 16 + 16 * i)
            if where + size <= len(data):
                pieces.append((start, size, where))
            where += size
    pieces.sort()
    starts = [p[0] for p in pieces]

    def read(address: int, size: int) -> bytes | None:
        i = bisect.bisect_right(starts, address) - 1
        if i < 0:
            return None
        start, length, where = pieces[i]
        if address + size > start + length:
            return None
        return data[where + address - start:where + address - start + size]
    return read


GAME_PROGRAM = "ruse.exe"   # the game's program, by its file name: every modded copy runs one (rusemod.play)
NAME_BYTES = 0x10000        # the most of a module's name read (a Windows path is at most 32,767 characters)


def game_report(path) -> bool:
    """Whether a crash report file is the game's own: its module list names the game's program (GAME_PROGRAM, as
    read_dump finds the game in a report). The game's crash reporter is used by other programs too, and their reports
    can lie in the same folder; the agreement says "When the game writes its own crash report, the apps read that
    report on your PC". So of any file only its header, its list of parts and its module list's names are read to tell,
    nothing else of it, and another program's crash report is never read (2026-11-24). Never raises.

    Checked our_tools.json: none of its tools tells whose a crash report is from its module list alone, before
    anything else of it is read."""
    try:
        with open(path, "rb") as f:
            def read(at: int, size: int) -> bytes:
                f.seek(at)
                return f.read(size)
            head = read(0, 32)
            if head[:4] != b"MDMP":
                return False
            count, rva = struct.unpack_from("<II", head, 8)
            for i in range(count):
                entry = read(rva + 12 * i, 12)
                if len(entry) < 12:
                    return False
                kind, _size, at = struct.unpack("<III", entry)
                if kind != 4:  # ModuleListStream
                    continue
                (n,) = struct.unpack("<I", read(at, 4))
                for j in range(n):
                    (name_rva,) = struct.unpack_from("<I", read(at + 4 + 108 * j, 24), 20)
                    (length,) = struct.unpack("<I", read(name_rva, 4))
                    name = read(name_rva + 4, min(length, NAME_BYTES)).decode("utf-16-le", "replace")
                    if re.split(r"[\\/]", name)[-1].lower() == GAME_PROGRAM:
                        return True
            return False
    except (OSError, ValueError, struct.error):
        return False


def _unread(why: list | None, code: str, error=None) -> None:
    """Why read_dump read no crash report from a file, for Bug Watch's list (GameWatch): its code, and the Windows
    error number of a file that couldn't be read."""
    if why is not None:
        why.append((code, detail_of(error) if error is not None else {}))


def _from_copy(program: str | None, copy) -> bool:
    """Whether a crash report's RUSE.exe (its module's path as the report keeps it) ran from the modded copy at `copy`:
    its last parts are the copy's folder, its parent's, and RUSE.exe (a report keeps the path in a form of its own, so
    only its end is compared)."""
    if not program:
        return False
    have = [p.lower() for p in re.split(r"[\\/]", program) if p]
    want = [p.lower() for p in (Path(copy).parent.name, Path(copy).name, "RUSE.exe") if p]
    return have[-len(want):] == want


def read_dump(path, exe=None, install=None, unit=False, known=None, why: list | None = None,
              copy=None) -> dict | None:
    """From a crash report file, read on this PC only: {"code", "module", "offset"}; for a bad memory access
    (0xc0000005) "access", what the game tried to do and where ("read 0x20"); with the copy's RUSE.exe (`exe`) given,
    "chain": the places in RUSE.exe the crashed thread's stack returns to, nearest first (up to CHAIN_MOST, each one
    right after a call); and for the game's script-error stop (0x29a), "traceback" (the game Python's text, paths cut),
    "ignored" (the number on the game's "Previously ignored errors: N" line before it, when there is one: each of our
    script guards adds 1 when it steps in, rusemod.scriptguards) and, with the game's install (`install`) given, "map":
    the map its text names, the game's own by its name, a mod's as OWN_MAP (map_of; sent only under version 4 of the
    agreement: Watch.game_crash). "build": the size, checksum and time stamp of the game's program when the report
    lists it (for the crash code, rusemod.crashcode, and to tell a build our list isn't for; never sent). At one of the
    crashes we know (`known`: our list, rusemod.knowncrashes; none without it: for the game build the list is for, its
    chain and the rest of the looked-at stack holding what that place needs: a place that needs them gets none without
    `exe`), "reason": its plain reason's key; and with `unit` (asked only under version 4 of the agreement: GameWatch)
    and `exe`, "unit": the number of the unit the game was making, when the report kept it
    (knowncrashes.unit_number). Neither goes out as it is (Watch.game_crash, unit_sent). None if it can't be read, and
    for another program's crash report, which is never read further (game_report). For a file that can't be read or
    isn't a crash report, and for one of the game's own that can't be read, `why` (a list, when given) gets why, by
    its code: CRASH-14 the file couldn't be read, CRASH-04 it isn't a crash report, CRASH-12 it holds no exception
    record, CRASH-13 it is cut short. With `copy` (a modded copy's folder), None too for a report whose RUSE.exe
    didn't run from that copy (_from_copy: another game's). The dump never leaves the PC (the plan, §2)."""
    unreadable, not_one = "CRASH-14", "CRASH-04"   # (each code written once: the header's look and the read below)
    try:  # (only its first bytes, as game_report reads the header: whether it is a crash report at all)
        with open(path, "rb") as f:
            head = f.read(4)
    except OSError as exc:
        _unread(why, unreadable, exc)
        return None
    if head != b"MDMP":
        _unread(why, not_one)
        return None
    if not game_report(path):
        return None   # another program's crash report: never read further, never counted
    try:
        data = Path(path).read_bytes()
    except OSError as exc:   # (gone or held since its header was read)
        _unread(why, unreadable, exc)
        return None
    if data[:4] != b"MDMP":   # (changed since its header was read)
        _unread(why, not_one)
        return None
    access, chain, at_offsets, words, builds, reason, number = None, [], [], [], {}, None, None
    list_error = False   # a check against our list that raised (counted by GameWatch; never sent)
    returns = []  # every place in RUSE.exe the looked-at stack returns to, nearest first (a crash we know: knowncrashes)
    try:
        count, rva = struct.unpack_from("<II", data, 8)
        streams = {}
        for i in range(count):
            kind, size, at = struct.unpack_from("<III", data, rva + 12 * i)
            streams[kind] = (at, size)
        if 6 not in streams:  # ExceptionStream
            _unread(why, "CRASH-12")
            return None
        at, exc_size = streams[6]
        (thread,) = struct.unpack_from("<I", data, at)
        code, _flags, _rec, address, params = struct.unpack_from("<IIQQI", data, at + 8)
        if code == 0xC0000005 and params >= 2:
            what, where = struct.unpack_from("<QQ", data, at + 40)
            access = f"{ACCESS.get(what, '?')} 0x{where:x}"
        modules, program = [], None
        if 4 in streams:  # ModuleListStream
            mat, _ = streams[4]
            (n,) = struct.unpack_from("<I", data, mat)
            for i in range(n):
                base, size, checksum, stamp, name_rva = struct.unpack_from("<QIIII", data, mat + 4 + 108 * i)
                (length,) = struct.unpack_from("<I", data, name_rva)
                name = data[name_rva + 4:name_rva + 4 + length].decode("utf-16-le", "replace")
                modules.append((base, size, re.split(r"[\\/]", name)[-1]))
                builds[(base, size)] = (size, checksum, stamp)  # which build of it (knowncrashes.Known.builds)
                if modules[-1][2].lower() == "ruse.exe":
                    program = name  # (its path: only compared with the copy's, never kept)
        if copy is not None and not _from_copy(program, copy):
            return None  # another game's report (one started outside the apps, or from the game's own folder)
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
                look = stack[first:first + STACK_LOOK]
                words = [w for (w,) in struct.iter_unpack("<Q", look[:len(look) // 8 * 8])]
                for word in words:
                    if not base <= word < base + size or not after_call(word - base):
                        continue
                    returns.append(word - base)
                    place = f"RUSE.exe+0x{word - base:x}"
                    if len(chain) < CHAIN_MOST and place not in chain:   # (what a report sends: the nearest 16)
                        chain.append(place)
                        at_offsets.append(word - base)
                break
        if game is not None and game[0] <= address < game[0] + game[1] and known is not None:  # one we know?
            from . import knowncrashes
            try:  # (a list or a check that fails costs the notice only, never the crash's report)
                reason = knowncrashes.reason(known, builds.get(game), address - game[0], at_offsets, returns)
            except Exception:  # noqa: BLE001 - said below ("list_error"), never silent
                reason, list_error = None, True
            if reason is not None and unit and after_call is not None and words:
                try:  # (a memory list that can't be read costs the unit only, never the crash's report)
                    number = knowncrashes.unit_number(known, builds.get(game), game[0], words,
                                                      _kept_memory(data, streams), after_call)
                except (struct.error, ValueError, IndexError):
                    number = None   # (a report cut short: as before the list moved)
                except Exception:  # noqa: BLE001 - said below ("list_error"), never silent
                    number, list_error = None, True
    except struct.error:
        _unread(why, "CRASH-13")
        return None
    module = re.sub(r"[^A-Za-z0-9_.+ -]", "_", module)[:64] or "?"
    out = {"code": f"0x{code:x}", "module": module, "offset": f"0x{offset:x}"}
    if game is not None and builds.get(game):
        out["build"] = list(builds[game])   # (only for the crash code and the list's builds: never sent)
    if list_error:
        out["list_error"] = True            # (GameWatch counts it: never sent)
    if access:
        out["access"] = access
    if chain:
        out["chain"] = chain
    if reason is not None:
        out["reason"] = reason   # (only for the player: never sent)
    if number is not None:
        out["unit"] = number     # (sent only as unit_sent says, under version 4)
    if code == 0x29A:
        text = script_error_text(data)
        if text:   # paths cut down to their file names, then RUSE Guard's own cleaning (no_ids)
            out["traceback"] = no_ids(no_paths(text))[:TRACEBACK_CHARS]
        ignored = IGNORED.search(data)
        if ignored is not None:
            out["ignored"] = min(MAX_COUNT, int(ignored.group(1)))
        if install is not None:
            found_map = map_of(data, game_maps(install))
            if found_map:
                out["map"] = found_map
    return out


IGNORED = re.compile(rb"Previously ignored errors: (\d{1,9})")  # the game's own line, before its script-error text


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
NOTES = "games"     # <home>/bugwatch/games/: a note for each game an app watches, while it runs (notes_left, B11 B)
NOTE_EVERY = 60.0   # seconds between the times a note says the game was last seen running


class _GameWatched(threading.Thread):
    """A watch beside a game an app started (GameWatch, CodeWatch): while it runs, the window keeps asking
    (crash_notice's "watching"), and a notice of an earlier game the window never took goes when it starts."""

    def start(self) -> None:
        global _notice
        with _notice_lock:  # (the window waits for a notice while a game is watched: crash_notice)
            _watching.add(self)
            _notice = None  # an earlier game's notice the window never took: never said while this game runs
        try:
            super().start()
        except RuntimeError:
            with _notice_lock:
                _watching.discard(self)
            raise

    def run(self) -> None:
        try:
            self._watch()
        finally:
            with _notice_lock:
                _watching.discard(self)

    def _watch(self) -> None:
        raise NotImplementedError


class GameWatch(_GameWatched):
    """Beside the game the apps started (rusemod.play.Starter): when it closes, the minutes it ran with its mods, and
    any crash report it left since it started; at one of the crashes we know, the notice for the player (crash_notice:
    the plain reason, and under version 4 the unit the game was making, named as its card says). The notice is kept
    first, before Bug Watch's own records, and each record that can't be written (a full disk, a folder held) costs
    only itself; a notice of an earlier game the window never took goes when this game starts.

    Our list of known crashes (rusemod.knowncrashes): under version 5 of the agreement it is fetched while the game
    loads (`refreshing`, a thread of its own; a failure counted as "crashlist:<why>"), and read once the game has
    closed. At a crash of the game itself with no list on the PC, the watch waits for that fetch (up to
    knowncrashes.WAIT_AT_CRASH seconds), fetches once more when it failed or never ran, and reads the report again; with
    still no list, the notice says the Launcher couldn't check the crash ("list": False, counted as "crash_no_list").
    A list without this game's build is counted once a game ("crashlist:build-missing"). Each crash report is read on
    its own: one that can't be read costs only itself, never the game's other records.

    The crash code (crash_code_given: the Launcher's player under version 5; the owner, 2026-11-26): the notice of a
    crash we know, or of one that couldn't be checked, carries the code CodeWatch would give for the same report; any
    other crash is told by its code alone, unless this game's notice already says more (a second report of the same
    crash, as Windows' own beside the game's). The code is for the player only: it goes in no record.

    Under CODES_AGREEMENT also, in the day's list of failures (B6 B, B7 B): a crash report that couldn't be read
    (read_dump's code), a game that closed within a minute with none (CRASH-01), and one that ended after that with an
    exit number other than 0 and none (CRASH-05), each with the game's exit number; and while the game runs, its note
    on the PC (_write_note), so a game the app was closed under still counts at the app's next start (notes_left: the
    owner's B11 B)."""

    def __init__(self, watch: Watch, process, listed: list[str], own: int, sleep=time.sleep, clock=time.time,
                 local: str | None = None, exe=None, folders=None, game=None):
        super().__init__(daemon=True, name="bug-watch-game")
        self.folders = list(folders or [])  # the mods' folders: what the player's own hold (own_holds, version 4)
        self.game = game  # the game's install: which maps are the game's own (read_dump's map), and which units
        self.watch, self.process, self.listed, self.own = watch, process, listed, own
        self.sleep, self.clock, self.local, self.started = sleep, clock, local, clock()
        self.exe = exe  # the copy's program file, for a crash's chain and unit (read_dump); its folder is the copy
        self.refreshing: threading.Thread | None = None   # the fetch of our list of known crashes, while the game runs
        self.fetched: list[str] = []                       # what each fetch said (knowncrashes.refresh)
        self.tried_at_crash = False                        # the one more fetch at a crash, done (once a game)
        self.note: Path | None = None  # the game's note while it is watched (_write_note)

    def start(self) -> None:
        self._close_notes()  # (an earlier game an app was closed under has ended: no game runs twice from the copy)
        self._write_note()  # (first: a game whose watch can't start is still counted at the next start)
        super().start()

    def _close_notes(self) -> None:
        """A game starting from the modded copy (either app's): the note of every earlier game still waiting (an app
        was closed under it) gets this start as its end at the latest (`until`), since a copy runs one game at a time
        (rusemod.instance.refuse_if_running): its crash report is looked for before it only (notes_left)."""
        folder = self.watch.folder / NOTES
        for p in folder.glob("*.json") if folder.is_dir() else []:
            try:
                note = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(note, dict) and not note.get("done") and not note.get("until"):
                    p.write_text(json.dumps({**note, "until": self.started}), encoding="utf-8")
            except (OSError, ValueError, TypeError):
                continue

    def _write_note(self, seen: float | None = None) -> None:
        """The game's note on the PC (B11 B), under CODES_AGREEMENT only: when it started, when it was last seen
        running, its mods (mod-list ones by id@version, the others as a count), and where the copy's program and the
        game's install are, for its crash report (read_dump). Never sent. One that can't be written costs only
        itself."""
        try:
            if self.note is None and (seen is not None or not allows_codes(self.watch.home)):
                return
            path = self.watch.folder / NOTES / f"{self.watch.app}-{int(self.started * 1000)}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"started": self.started, "seen": self.started if seen is None else seen,
                                        "listed": list(self.listed), "own": int(self.own),
                                        "exe": str(self.exe or ""), "game": str(self.game or "")}), encoding="utf-8")
            self.note = path
        except (OSError, TypeError, ValueError):
            pass

    def _note_done(self) -> None:
        """The game closed while watched: its note goes (marked done when it can't be deleted, so it never counts
        twice)."""
        if self.note is None:
            return
        try:
            self.note.unlink(missing_ok=True)
        except OSError:
            try:
                self.note.write_text(json.dumps({"done": True}), encoding="utf-8")
            except OSError:
                pass
        self.note = None

    def _fetch(self) -> None:
        """One fetch of our list of known crashes (rusemod.knowncrashes.refresh), a failure counted by its kind."""
        from . import knowncrashes
        said = knowncrashes.refresh(self.watch.home)
        self.fetched.append(said)
        if said.startswith("failed:"):
            _record(self.watch.count, "messages", "crashlist:" + said[len("failed:"):])

    def _watch(self) -> None:
        from . import knowncrashes
        if allows_v5(self.watch.home):   # while the game loads: the list is usually on the PC before any crash
            self.refreshing = threading.Thread(target=self._fetch, daemon=True, name="bug-watch-crash-list")
            self.refreshing.start()
        seen = self.clock() if self.note is not None else 0.0
        while True:
            ended = self.process.poll()  # (its exit number, once it has ended)
            if ended is not None:
                break
            self.sleep(5)
            if self.note is not None and self.clock() - seen >= NOTE_EVERY:
                seen = self.clock()
                self._write_note(seen)
        self._note_done()
        ran = self.clock() - self.started
        v4 = allows_v4(self.watch.home)
        coded = crash_code_given(self.watch)   # under version 5, in either app: the crash code too
        known = knowncrashes.load(self.watch.home)
        crashes, unread, build_said, told_more = [], [], False, False   # (unread: why a report couldn't be read)
        for dump in crash_dumps_since(self.started, self.local):
            try:  # (a report that can't be read costs only itself)
                found = read_dump(dump, self.exe, install=self.game, unit=v4, known=known, why=unread)  # unit: v4
                if not found:
                    continue
                ours = str(found.get("module", "")).lower() == "ruse.exe"   # a crash of the game itself
                if ours and known is None:
                    known = self._list_at_crash()
                    if known is not None:
                        found = read_dump(dump, self.exe, install=self.game, unit=v4, known=known) or found
                if ours and known is not None and not build_said and \
                        not knowncrashes.knows_build(known, found.get("build")):
                    build_said = True   # (a new game build: the list must be brought up to it)
                    _record(self.watch.count, "messages", "crashlist:build-missing")
                if found.get("list_error"):   # (a check against the list raised: our own fault, counted)
                    _record(self.watch.count, "messages", "crashlist:check-error")
                if isinstance(found.get("unit"), int) and self.exe is not None:
                    named = unit_named(found["unit"], Path(self.exe).parent, self.game, self.watch.language())
                    if named is not None:
                        found["unit_name"], found["unit_added"] = named["name"], named["added"]
                # (the code as CodeWatch makes it, kept apart from `found`: no record carries it)
                code = _crash_code(found) if coded else None
                if found.get("reason"):
                    _tell(found, code)  # the player first: before any of Bug Watch's own records, which can fail
                    told_more = True
                elif ours and known is None:
                    _tell_no_list(code)
                    told_more = True
                    _record(self.watch.count, "messages", "crash_no_list")
                elif code and not told_more:
                    _tell_code(code)
                crashes.append(found)
            except Exception:  # noqa: BLE001 - one report that can't be read: the next one, and the game's records
                continue
        holds = own_holds(self.folders) if self.own and self.folders and v4 else None
        _record(self.watch.played, ran / 60.0, self.listed, self.own, holds)
        for found in crashes:
            _record(self.watch.game_crash, found, self.listed, self.own, holds=holds)
        if ran < QUICK_CLOSE and not crashes:  # the game didn't get going, or was quit at once (2026-11-10)
            _record(self.watch.count, "messages", "game:closed-under-1-min")
        if crashes or not allows_codes(self.watch.home):
            return
        shape = self._shape()
        for code, numbers in unread:
            _record(self.watch.failure, code, shape=shape, **numbers, exit=ended)
        if ran < QUICK_CLOSE:
            _record(self.watch.failure, "CRASH-01", shape=shape, exit=ended)
        elif ended and not unread:  # (0: the game ended as it should; its own exit number at a normal quit: not known)
            _record(self.watch.failure, "CRASH-05", shape=shape, exit=ended)

    def _shape(self) -> str | None:
        try:
            return _shape(set_of(self.folders), allows_v4(self.watch.home)) if self.folders else None
        except Exception:  # noqa: BLE001 - a mod folder that can't be read: no shape
            return None

    def _list_at_crash(self):
        """At a crash of the game itself with no list read: the fetch still running waited for (up to
        knowncrashes.WAIT_AT_CRASH seconds), one more fetch when it failed or none ran, then the list on the PC (or
        None). Only under version 5 of the agreement."""
        from . import knowncrashes
        if not allows_v5(self.watch.home):
            return None
        if self.refreshing is not None:
            self.refreshing.join(knowncrashes.WAIT_AT_CRASH)
        running = self.refreshing is not None and self.refreshing.is_alive()
        if not self.tried_at_crash and not running and (not self.fetched or self.fetched[-1].startswith("failed:")):
            self.tried_at_crash = True
            self._fetch()
        return knowncrashes.load(self.watch.home)


def notes_left(watch: Watch, local: str | None = None) -> int:
    """At an app's start: each game it watched that was still running when the app was last closed, by its note (the
    owner's B11 B: "a game still running when the Studio is closed is recorded through a small note file on the
    player's PC, read at the next start (its minutes, and a crash if the game left one)"): the minutes it was seen
    running (up to its crash report's time when it left one) and that crash report, counted now. Only a report its
    game can have left counts: written before the next game started from the copy (the note's `until`,
    GameWatch._close_notes), by a RUSE.exe that ran from the copy (read_dump's `copy`). A game still running from its
    copy waits for a later start; a note older than KEEP_DAYS goes. Under CODES_AGREEMENT only: otherwise a note goes
    unread. Returns how many games were counted."""
    folder, counted = watch.folder / NOTES, 0
    for p in sorted(folder.glob(f"{watch.app}-*.json")) if folder.is_dir() else []:
        try:
            note = json.loads(p.read_text(encoding="utf-8"))
            started, seen = float(note["started"]), float(note.get("seen", note["started"]))
            until = float(note["until"]) if note.get("until") else None
            own = max(0, int(note.get("own") or 0))
            exe, game = str(note.get("exe") or "") or None, str(note.get("game") or "") or None
            listed = [m for m in note.get("listed") or [] if isinstance(m, str)]
        except (OSError, ValueError, TypeError, KeyError, AttributeError):  # (a note made wrong: it goes)
            note, started = None, 0.0
        old = watch.clock() - started > KEEP_DAYS * 86400
        if note is None or note.get("done") or old or not allows_codes(watch.home):
            _forget(p)
            continue
        if until is None and exe and _runs_from(Path(exe).parent):
            continue  # the game still runs: a later start counts it
        crashes = []
        for dump in crash_dumps_since(started, local):
            try:
                when = dump.stat().st_mtime
            except OSError:
                continue
            if until is not None and when >= until:
                continue  # (the next game's)
            found = read_dump(dump, exe, install=game, unit=False, copy=Path(exe).parent if exe else None)
            if found:
                crashes.append(found)
                seen = max(seen, when)  # (it ran until it crashed)
        if until is not None:
            seen = min(seen, until)
        _record(watch.played, max(0.0, seen - started) / 60.0, listed, own)
        for found in crashes:
            _record(watch.game_crash, found, listed, own, send=False)
        _forget(p)
        counted += 1
    return counted


def _runs_from(copy: Path) -> bool:
    """Whether the game (or anything) still runs from the modded copy at `copy` (rusemod.instance.game_running)."""
    try:
        from .instance import game_running
        return bool(game_running(str(copy)))
    except Exception:  # noqa: BLE001 - not known: counted now, as one that ended
        return False


def _forget(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _seen_at_exit() -> None:
    """The app closing: each game it still watches is noted as seen running now (the note's last time: notes_left)."""
    for game in list(_watching):
        try:
            if getattr(game, "note", None) is not None:   # (a CodeWatch keeps no note)
                game._write_note(game.clock())
        except Exception:  # noqa: BLE001 - the app is closing: nothing may stop it
            pass


class CodeWatch(_GameWatched):
    """Beside a game an app started for a player without Bug Watch (crash_code_watched): when it closes, the
    crash code of the newest crash report the game left since it started (rusemod.crashcode: made from where the game
    stopped, read from the game's own crash report on the PC as read_dump reads it), kept for the window as GameWatch
    keeps its notice ({"code": ...}). A cheat copy's stop (RUSE Guard's marked lines in the report) is no crash to tell
    us and gets none. Nothing is counted, kept on the disk or sent, and nothing contacts our server."""

    def __init__(self, process, sleep=time.sleep, clock=time.time, local: str | None = None):
        super().__init__(daemon=True, name="crash-code-watch")
        self.process, self.sleep, self.clock, self.local, self.started = process, sleep, clock, local, clock()

    def _watch(self) -> None:
        from . import crashcode
        while self.process.poll() is None:
            self.sleep(5)
        for dump in crash_dumps_since(self.started, self.local):
            try:  # (a report that can't be read costs only itself)
                found = read_dump(dump)
                if not found:
                    continue
                from .guard import read_stop
                if read_stop(dump) is not None:
                    continue
                code = crashcode.make(found)
                if code:
                    _tell_code(code)
            except Exception:  # noqa: BLE001
                continue


def crash_code_given(watch: "Watch | None") -> bool:
    """Whether a crash of a game the app started gets a crash code for its player (rusemod.crashcode): the
    Launcher's after a Play and the Studio's after a Test in game (the owner, 2026-11-26: every player; his "13,
    yes": the Studio's too), Bug Watch on or off, once version 5 of the agreement is accepted, the version whose
    words say so. With Bug Watch off CodeWatch gives it; with it on, GameWatch's notice carries it."""
    return watch is not None and watch.app in ("launcher", "studio") and agreement(watch.home) >= AGREEMENT_V5


def crash_code_watched(watch: "Watch | None") -> bool:
    """Whether a game the app starts gets a CodeWatch: a crash code given (crash_code_given) and Bug Watch off (with it
    on, GameWatch gives the same code beside what it tells more)."""
    return crash_code_given(watch) and not enabled(watch.home)


def _crash_code(found: dict) -> str | None:
    """GameWatch's crash code for a report as read_dump read it (rusemod.crashcode.make, as CodeWatch makes it); None
    when it can't be made, which costs only the code, never the notice or the crash's report."""
    from . import crashcode
    try:
        return crashcode.make(found)
    except Exception:  # noqa: BLE001 - the notice is told without a code
        return None


def _record(write, *args, **kwargs) -> None:
    """One of Bug Watch's own records of a watched game; one that can't be written (a full disk, a folder another
    program holds) costs only itself, never the next one or the player's notice (GameWatch)."""
    try:
        write(*args, **kwargs)
    except OSError:
        pass


# --- the crashes we know, told to the player (the owner's item 25) ------------------------------------------------
_notice_lock = threading.Lock()
_watching: set = set()        # the GameWatch threads still watching a game an app started
_notice: dict | None = None   # the newest crash we know, for the player, until the window has taken it


def _tell(found: dict, code: str | None = None) -> None:
    """Keep the notice of a crash we know (read_dump's "reason", and GameWatch's name for the unit) for the window,
    with its crash code when one is given (crash_code_given)."""
    global _notice
    name = found.get("unit_name")
    notice = {"why": found["reason"], "unit": name if isinstance(name, str) and name else None,
              "added": found.get("unit_added") is True, "list": True}
    if code:
        notice["code"] = code
    with _notice_lock:
        _notice = notice


def _tell_no_list(code: str | None = None) -> None:
    """Keep the notice of a crash of the game itself that couldn't be checked: no list of known crashes on the PC;
    with its crash code when one is given (crash_code_given)."""
    global _notice
    notice = {"why": None, "unit": None, "added": False, "list": False}
    if code:
        notice["code"] = code
    with _notice_lock:
        _notice = notice


def _tell_code(code: str) -> None:
    """Keep the notice of a crash told by its crash code alone: a player without Bug Watch's (CodeWatch), or, with Bug
    Watch on, a crash GameWatch tells nothing more of."""
    global _notice
    with _notice_lock:
        _notice = {"code": code}


def crash_notice() -> dict:
    """For the window (BugWatchCalls.bugwatch_crash): {"watching": whether a game an app started is still being
    watched, so the page asks again; "notice": the newest crash since the window last took one, else None}. A notice
    is one of: a crash we know, {"why": the plain reason's key (rusemod.knowncrashes.REASONS; words.toml
    crash_why_<key>), "unit": the unit the game was making, by its name as its card says, or None, "added": whether a
    mod added it, "list": True}; a crash of the game itself with no list of known crashes on the PC, {"why": None,
    "unit": None, "added": False, "list": False}; each of the two with "code", its crash code, when one is given
    (crash_code_given: the Launcher's player under version 5); a crash told by its code alone, {"code": its crash
    code} (CodeWatch, or GameWatch at a crash it tells nothing more of). A notice is handed over once."""
    global _notice
    with _notice_lock:
        notice, _notice = _notice, None
        return {"watching": bool(_watching), "notice": notice}


def unit_named(number: int, copy, game, lang: str = "us") -> dict | None:
    """The unit numbered `number` (its DescriptorId) in the modded copy whose folder is `copy`, from the copy's own
    data: {"name": its name as its card says (the copy's texts in `lang` when the game has that language, else in
    English; else its name in the data, which for a mod's unit is the name that mod gave it), "added": whether a mod
    added it (False when the game's install, `game`, has a unit of that number and that name; None when the install
    can't be read)}. None when the copy's data can't be read, or holds no unit of that number, or more than one. Read
    after the game closed (the unit data loads in about 2 seconds). Never raises: the app must never stop on it."""
    try:
        return _unit_named(int(number), Path(copy), game, lang)
    except Exception:  # noqa: BLE001 - a copy rebuilt or moved meanwhile, a file that can't be read: no name
        return None


UNIT_DATA = "ZZ_GladPatchableWin.dat"   # the pack the game's units are in (rusemod.build.DEFAULT_PACK)
CARD_NAMES = "baseunite"                # the dictionary of the units' names on their cards (build._english_names)
NAME_MOST = 80                          # characters of a unit's name the notice says


def _units_in(pack) -> dict[int, list]:
    """{DescriptorId: [(name, unit)...]} of every unit in a unit-data pack, loaded the way a build loads it."""
    from .build import load_pack
    from .edat import Edat
    from .patch import Num
    from . import unitcheck
    # read whole first (a few MB) and the file let go at once: the copy's own file is never held while its units are
    # read (2 seconds or more), so a build of that copy just after the game closed can set it aside as usual
    model = load_pack(Edat(Path(pack).read_bytes()), None)
    out: dict[int, list] = {}
    for name, obj in model.base.objects.items():
        v = obj.props.get(unitcheck.ID) if unitcheck.is_unit(obj) else None
        if isinstance(v, Num):
            out.setdefault(int(v.value), []).append((name, obj))
    return out


def _unit_named(number: int, copy: Path, game, lang: str) -> dict | None:
    from .build import find_pack
    pack = find_pack(copy, UNIT_DATA)
    if pack is None or not pack.is_file():
        return None
    units = _units_in(pack).get(number) or []
    if len(units) != 1:
        return None
    name, obj = units[0]
    added = None
    own = find_pack(Path(game), UNIT_DATA) if game is not None else None
    if own is not None and own.is_file():
        try:
            same = os.path.samefile(pack, own)  # the copy's unit data linked from the game's: no mod changed it
        except OSError:
            same = False
        theirs = [n for n, _o in (_units_in(own).get(number) or [])] if not same else [name]
        added = theirs != [name]
    return {"name": _card_name(copy, obj, lang) or _data_name(name), "added": added}


def _card_name(copy: Path, obj, lang: str) -> str | None:
    """A unit's name as its card says it in the copy: its NameInMenuToken's text in the copy's unit names, in `lang`
    when the game has that language, else in English."""
    import html
    from .build import find_pack
    from .dic import Dic, name_to_key
    from .edat import Edat
    from .patch import Text
    from . import loc, schema
    v = obj.props.get("NameInMenuToken")
    if not isinstance(v, Text) or v.kind != "key":
        return None
    key = int(v.value, 16) if v.value.lower().startswith("0x") else name_to_key(v.value)
    texts = find_pack(copy, loc.PACK)
    if texts is None or not texts.is_file():
        return None
    with Edat.open(str(texts)) as arc:
        entries = {e.path.lower(): e for e in arc.entries}
        for language in dict.fromkeys((schema.game_lang(lang), "us")):
            e = entries.get(loc.member(CARD_NAMES, language).lower())
            text = Dic(bytes(arc.read(e))).text(key) if e is not None else None
            said = " ".join(html.unescape(text or "").split())
            if said:
                return said[:NAME_MOST]
    return None


def _data_name(name: str) -> str:
    """A unit's name in the data, as a name to read: Descriptor_Unit_Horse_Squad -> Horse Squad."""
    short = re.sub(r"^(?:Descriptor_)?(?:Unit_)?", "", str(name).replace("\\", "/").rsplit("/", 1)[-1])
    return " ".join(short.replace("_", " ").split())[:NAME_MOST] or str(name)[:NAME_MOST]


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
    the error hooks that count crashes. Safe to call when Bug Watch is off (nothing is counted then). With the player's
    own tick off, anything still in Bug Watch's folder goes first: until 2026-11-24 an app's save at its end wrote the
    day's counts back after an untick, and they would have gone out after a later tick."""
    global _current, _exit_hooked
    values = _settings_now(home)
    if values is not None and not _ticked_in(values):
        _delete_kept(home)
    _current = Watch(home, app, version)
    _hook_errors(_current)
    if enabled(home):
        _current.roll()
        threading.Thread(target=_left_then_send, args=(_current,), daemon=True).start()
    import atexit
    atexit.register(_current.save)
    if not _exit_hooked:
        _exit_hooked = True
        atexit.register(_seen_at_exit)  # (a game still watched as the app closes: its note says when, notes_left)
    return _current


_exit_hooked = False


def _left_then_send(watch: Watch) -> None:
    """In the background at an app's start: the games it was closed under counted (notes_left), then what waits sent."""
    try:
        notes_left(watch)
    except Exception:  # noqa: BLE001 - counting must never stop the app
        pass
    watch.send_waiting()


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


def failure(code: str, error=None, **detail) -> None:
    """Count a failure that is no window call's error in this app's Watch (Watch.failure), when there is one."""
    if _current is not None:
        try:
            _current.failure(code, error, **detail)
        except Exception:  # noqa: BLE001 - counting must never stop the app
            pass


def failed(error) -> None:
    """Count a caught error that the window call doesn't fail on (an update check that couldn't ask GitHub) by its
    code (rusemod.codes.coded) and its numbers, when it has a code."""
    from .codes import code_of
    code = code_of(error)
    if code:
        failure(code, error)


class Refused(Exception):
    """A job an app refused before it started: its kind as Bug Watch counts it, and its key (never words)."""

    def __init__(self, key: str):
        super().__init__(key)
        self.words_key = key


def refused(name: str, key: str, code: str = "", **detail) -> None:
    """A job an app refused before starting it (the Launcher's Play: one already starting, a restore running, no
    such set, a set with a mistake, an author not trusted yet), counted as a failed job of kind "Refused" and by its
    key under "messages", and by its `code` with its numbers in the day's list (rusemod.codes). Until 2026-11-10 these
    Plays never reached Bug Watch at all (the job never started)."""
    if _current is not None:
        from .codes import coded
        _current.job(name, False, 0.0, coded(Refused(key), code, **detail))


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
            watch._now_on()   # (counts made before the player's last untick, here or in the other app: never shown)
            counts = json.loads(json.dumps(watch.days.get(day) or _blank_day(watch.version)))
        waiting = sorted(p.name for p in watch.outbox.glob("*.json")) if watch.outbox.is_dir() else []
        return {"today": watch.payload(day, counts), "waiting": waiting}

    def bugwatch_crash(self) -> dict:
        """After a game this app started: {"watching": whether it's still watched (the page asks again while it is),
        "notice": the crash it stopped at, once, or None} (crash_notice: a crash we know, with the plain reason's key,
        the unit the game was making by its name as its card says, whether a mod added it; one that couldn't be
        checked; and, for the Launcher's player under version 5, Bug Watch on or off, its crash code). With Bug Watch
        on, GameWatch watches the game; with it off, the Launcher's CodeWatch (rusemod.play.Starter). Bug Watch's own
        call, so not counted as one of the window's."""
        return crash_notice()

    def bugwatch_page_error(self, screen: str, name: str) -> dict:
        """The page's own script failed (the Studio's window.onerror, the owner's B11 B): the screen's name and the
        error's short name (TypeError), nothing else (Watch.page_error)."""
        if _current is not None:
            _current.page_error(screen, name)
        return {"ok": True}

    def bugwatch_seen(self, group: str, key: str) -> dict:
        """The page tells Bug Watch a screen opened ("screens", its name), that screen used ("screen_used": the Launcher's
        mod set editor made a set) or a problem shown ("messages", a key that never changes: a refusal the page makes
        itself, which never reaches a call, as "page:new_set:set_no_mods")."""
        if group not in ("screens", "screen_used", "messages"):
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
