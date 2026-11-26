"""The game crashes we know, told to the player (the owner's item 25), from a list that is ours and stays private.

The owner, 2026-11-13 (item 25): "It should tell them the unit that it was making when it crashed." and "For 25, they
should also be told why that unit made the game crash." Until 0.9.8.22 the apps carried the table of those crashes in
their own code. On 2026-11-24 he took Robbie's point about it: "Okay, fine. We can move it to the private repo." So the
list is ours and private, and the plan he approved that day is kept: the Bug Watch server hands the list to the apps
(refresh), each app keeps a copy on the PC (`<home>/bugwatch/known-crashes.json`), the game's crash report is checked
against it on the PC (reason, unit_number: rusemod.bugwatch.read_dump), and nothing more is sent. With no list on the PC
(offline, the first start) the crash notice leaves out the unit and the reason and says the Launcher couldn't check the
crash (rusemod.bugwatch.GameWatch).

Signed (the owner, 2026-11-25: "Okay, yes for 15 sign."): the list is signed with a key of its own that stays on the
owner's PC, and the apps carry its public half (KEY). A list is taken only when its signature holds (checked), so
someone who took over our server or its account can't change what the apps trust. Until the owner has made that key,
KEY is None and a list is taken on HTTPS alone (the server's certificate, checked as for every download: rusemod.net).

When it is fetched: only with Bug Watch on and version 5 of the agreement accepted (rusemod.bugwatch.allows_v5), when
a game starts (GameWatch), at most once a day (FRESH); and once more at a crash of the game itself when no list is on
the PC. The download is one GET of one address (ROUTE) with the apps' User-Agent and nothing else: no report code, no
username, nothing from the player's files. Unticking Bug Watch deletes the list with the rest of Bug Watch's folder
(rusemod.bugwatch.turn_off).

The list is data and is never run: strict JSON in one shape (parse), every number a whole number from 0 to below 2**32,
every range in order, each part within its limit; anything else and the whole list is refused. This file holds no
number of the game: they are all in the list.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import ssl
import struct
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import ed25519, net

REASONS = ("made", "turret", "setup", "part", "mesh")   # the reasons the apps have words for (words.toml crash_why_<key>)
ROUTE = "/v1/known-crashes"                             # on the Bug Watch server (rusemod.bugwatch.SERVER)
LIST_FILE = "known-crashes.json"                        # in <home>/bugwatch: {"list", "sig", "checked"}
LAST_FILE = "known-crashes-last.json"                   # in <home>/bugwatch: {"at", "result"} of the last refresh
TEMP_GLOB = "known-crashes.*.tmp.json"                  # a refresh's file before it replaces LIST_FILE (ends in .json, so
#                                                         turn_off deletes one left behind too)
PREFIX = b"RUSE2-CRASHES-1:"                            # what is signed: PREFIX + the list's text (UTF-8)
KEY: bytes | None = None                                # the list key's public half (32 bytes); None: HTTPS alone
MOST_BYTES = 64 * 1024                                  # the most a served list (and the list's own text) may weigh
FRESH = 24 * 3600                                       # seconds a checked list is used before it's asked for again
TIMEOUT = 15                                            # seconds for the download
WAIT_AT_CRASH = 30                                      # seconds GameWatch waits for a download still running at a crash
BUSY_TRIES = 3                                          # tries at putting the new file in place (Windows refuses it while
#                                                         the other app has it open), 0.2 s apart
MOST_BUILDS, MOST_PLACES, MOST_GROUPS, MOST_RANGES, MOST_KINDS = 16, 256, 8, 64, 64
TOP = 2 ** 32                                           # every number of the list is below this
KEYS = frozenset({"v", "n", "builds", "places", "creating", "kinds", "number_at"})   # a list's parts, all of them
PLACE_KEYS = frozenset({"at", "why", "chain", "stack"})
RESULT_RE = re.compile(r"(?:off|fresh|same|new|failed:[a-z0-9-]{1,24})")


@dataclass(frozen=True, eq=False)
class Known:
    """A list of the crashes we know, checked (parse): its number (`n`, higher for a newer list), its text as served,
    the builds of the game's program it is for (each as a crash report's module list gives it: size, checksum, time
    stamp), its places ({offset: (reason, chain groups, stack groups)}; a group is a tuple of (low, high) ranges, and a
    place counts only when the crash's chain, or the rest of the stack, has a place in one range of every group), the
    unit-creation step's range, the unit descriptions' kinds and where a description holds its number."""
    n: int
    text: str
    builds: frozenset
    places: dict
    creating: tuple
    kinds: frozenset
    number_at: int


# --- reading a list: data only, one shape, within limits ---------------------------------------------------------
def _no_twins(pairs) -> dict:
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("a key given twice")
        out[k] = v
    return out


def _refused(_text):
    raise ValueError("not a whole number")


def _strict(text: str):
    """JSON with no key given twice, no NaN or Infinity and no number with a point or an exponent."""
    return json.loads(text, object_pairs_hook=_no_twins, parse_constant=_refused, parse_float=_refused)


def _number(x) -> int:
    if type(x) is not int or not 0 <= x < TOP:   # (a bool is no number here)
        raise ValueError("not a number of the list")
    return x


def _span(x) -> tuple:
    if not isinstance(x, list) or len(x) != 2:
        raise ValueError("not a range")
    lo, hi = _number(x[0]), _number(x[1])
    if not lo < hi:
        raise ValueError("a range out of order")
    return lo, hi


def _groups(x) -> tuple:
    if not isinstance(x, list) or len(x) > MOST_GROUPS:
        raise ValueError("not a list of groups")
    out = []
    for group in x:
        if not isinstance(group, list) or not 1 <= len(group) <= MOST_RANGES:
            raise ValueError("not a group of ranges")
        out.append(tuple(_span(r) for r in group))
    return tuple(out)


def parse(text) -> Known | None:
    """The list in `text` (the served list's own text), checked, or None for anything else: not strict JSON or a
    key twice, another version than 1, a number that isn't a whole number from 0 to below 2**32 (a bool included), a
    range whose low end isn't below its high end, a part missing or one too many, a place twice, a part over its
    limit, or more than MOST_BYTES. A place whose reason the apps have no words for (not in REASONS) is left out and
    the rest kept. Never raises (deeply nested text too)."""
    try:
        return _parse(text)
    except Exception:  # noqa: BLE001 - RecursionError for deeply nested text included: anything else is no list
        return None


def _parse(text) -> Known | None:
    if isinstance(text, (bytes, bytearray)):
        text = bytes(text).decode("utf-8")
    if not isinstance(text, str) or len(text.encode("utf-8")) > MOST_BYTES:
        return None
    data = _strict(text)
    if not isinstance(data, dict) or set(data) != KEYS or type(data["v"]) is not int or data["v"] != 1:
        return None
    n = _number(data["n"])
    if n < 1:
        return None
    builds = data["builds"]
    if not isinstance(builds, list) or len(builds) > MOST_BUILDS:
        return None
    seen_builds = set()
    for b in builds:
        if not isinstance(b, list) or len(b) != 3:
            return None
        seen_builds.add(tuple(_number(x) for x in b))
    places = data["places"]
    if not isinstance(places, list) or len(places) > MOST_PLACES:
        return None
    kept: dict[int, tuple] = {}
    seen_places = set()
    for p in places:
        if not isinstance(p, dict) or set(p) != PLACE_KEYS or not isinstance(p["why"], str):
            return None
        at = _number(p["at"])
        if at in seen_places:
            return None
        seen_places.add(at)
        entry = (p["why"], _groups(p["chain"]), _groups(p["stack"]))
        if p["why"] in REASONS:
            kept[at] = entry
    creating = _span(data["creating"])
    kinds = data["kinds"]
    if not isinstance(kinds, list) or len(kinds) > MOST_KINDS:
        return None
    return Known(n=n, text=text, builds=frozenset(seen_builds), places=kept, creating=creating,
                 kinds=frozenset(_number(k) for k in kinds), number_at=_number(data["number_at"]))


def _checked(blob, key=None) -> tuple[Known | None, str, str]:
    """(the list, "ok", its signature) from a served or kept blob ({"list": text, "sig": hex}, and "checked" in the
    kept one), else (None, why, ""): "shape" or "signature"."""
    try:
        if isinstance(blob, (bytes, bytearray)):
            blob = bytes(blob).decode("utf-8")
        if not isinstance(blob, str) or len(blob.encode("utf-8")) > MOST_BYTES:
            return None, "shape", ""
        body = _strict(blob)
        if not isinstance(body, dict) or not isinstance(body.get("list"), str) or \
                set(body) - {"list", "sig", "checked"}:
            return None, "shape", ""
        text, sig = body["list"], body.get("sig", "")
        public = key if key is not None else KEY   # (read now: a test's patch of KEY counts)
        if public is not None:
            if not isinstance(sig, str) or not re.fullmatch(r"[0-9a-f]{128}", sig) or \
                    not ed25519.verify(public, PREFIX + text.encode("utf-8"), bytes.fromhex(sig)):
                return None, "signature", ""
        known = parse(text)
        if known is None:
            return None, "shape", ""
        return known, "ok", sig if isinstance(sig, str) else ""
    except Exception:  # noqa: BLE001 - anything that isn't a list in its one shape
        return None, "shape", ""


def checked(blob, key=None) -> Known | None:
    """The list in a served or kept blob when its signature holds under `key` (KEY when None, read when called; with
    no key at all, HTTPS alone: the signature isn't asked for) and the list parses; None otherwise. Never raises."""
    return _checked(blob, key)[0]


def load(home) -> Known | None:
    """The list kept on this PC, its signature and its shape checked again at every read, or None. A file the other
    app is putting in place this moment (Windows: PermissionError) is read again once, 0.2 s later. Never raises."""
    path = Path(home) / _folder() / LIST_FILE
    for attempt in range(2):
        try:
            return checked(path.read_bytes())
        except PermissionError:
            if attempt == 0:
                time.sleep(0.2)
        except Exception:  # noqa: BLE001 - no file, or one that can't be read: no list
            return None
    return None


def _folder() -> str:
    from .bugwatch import FOLDER
    return FOLDER


def _kept(home: Path) -> tuple[Known | None, float | None]:
    """(the kept list, when it was last checked against the server: the kept "checked", never the file's own time)."""
    known = load(home)
    if known is None:
        return None, None
    try:
        when = json.loads((home / _folder() / LIST_FILE).read_text(encoding="utf-8")).get("checked")
    except Exception:  # noqa: BLE001
        return known, None
    return known, float(when) if type(when) in (int, float) else None


def state(home) -> dict:
    """For the troubleshooter: {"n": the kept list's number or None, "checked": when it was last checked (seconds,
    UTC) or None, "last": the last refresh's result or None}. Never a number of the list itself. Never raises."""
    home = Path(home)
    out = {"n": None, "checked": None, "last": None}
    try:
        known, when = _kept(home)
        if known is not None:
            out["n"], out["checked"] = known.n, int(when) if when is not None else None
        last = json.loads((home / _folder() / LAST_FILE).read_text(encoding="utf-8")).get("result")
        if isinstance(last, str) and RESULT_RE.fullmatch(last):
            out["last"] = last
    except Exception:  # noqa: BLE001 - nothing more to say
        pass
    return out


def findings(home) -> list[dict]:
    """The troubleshooter's line for the list, when the apps fetch it (Bug Watch on and version 5 of the agreement
    accepted: rusemod.bugwatch.allows_v5; rusemod.doctor's finding shape; its words are doc_crashlist_on and
    doc_crashlist_missing in both apps): the kept list's number and when it was checked, or that none is on this PC and
    the last try's result. Never a number of the list. [] otherwise. Never raises."""
    try:
        from .bugwatch import allows_v5
        if not allows_v5(home):
            return []
        now = state(home)
        if now["n"] is not None:
            when = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(now["checked"])) if now["checked"] else "?"
            return [{"key": "crash_list", "level": "info", "say": "doc_crashlist_on",
                     "data": {"n": now["n"], "checked": when}, "fix": None}]
        return [{"key": "crash_list", "level": "info", "say": "doc_crashlist_missing",
                 "data": {"last": now["last"] or "none yet"}, "fix": None}]
    except Exception:  # noqa: BLE001 - the troubleshooter must never stop on it
        return []


# --- fetching it from the Bug Watch server ------------------------------------------------------------------------
def refresh(home, opener=None, clock=time.time) -> str:
    """Fetch the list when it is due, keep it on this PC, and say how it went; never raises, and nothing it downloads
    is ever run. "off": Bug Watch off or version 5 of the agreement not accepted (no request); "fresh": the kept list
    was checked less than FRESH ago (no request; its kept "checked" time, never the file's own); "same" or "new": the
    server's list checked and kept, with the time it was checked; "failed:<kind>", the kept file left as it was:
    offline, certificate, http-<code>, none (nothing published: 404), size, shape, signature, older (a lower number than
    the kept list), busy (the file couldn't be put in place), error. `opener`: net.urlopen when None (its certificate
    fallbacks, as every download of the apps). Each result but "off" is written down (LAST_FILE) for the
    troubleshooter; a player who unticks Bug Watch meanwhile leaves no list and nothing else behind ("off")."""
    try:
        return _refresh(Path(home), opener or net.urlopen, clock)
    except Exception:  # noqa: BLE001 - a refresh must never stop a game's watch
        return "failed:error"


def _refresh(home: Path, opener, clock) -> str:
    from .bugwatch import SERVER, allows_v5
    if not allows_v5(home):
        return "off"
    folder = home / _folder()
    kept, when = _kept(home)
    now = clock()
    if kept is not None and when is not None and 0 <= now - when < FRESH:
        return "fresh"
    result, known, sig = _fetch(opener, SERVER + ROUTE)
    if known is not None and kept is not None and known.n < kept.n:
        result = "failed:older"
    elif known is not None:
        result = "same" if kept is not None and kept.text == known.text else "new"
        if not _put(folder, LIST_FILE, {"list": known.text, "sig": sig, "checked": int(now)}):
            result = "failed:busy"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / LAST_FILE).write_text(json.dumps({"at": int(now), "result": result}), encoding="utf-8")
    except OSError:
        pass
    if not allows_v5(home):   # unticked meanwhile (in this app or the other): nothing of it stays
        for p in [folder / LIST_FILE, folder / LAST_FILE] + (sorted(folder.glob(TEMP_GLOB)) if folder.is_dir() else []):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass
        return "off"
    return result


def _fetch(opener, url: str) -> tuple[str, Known | None, str]:
    """("ok", the list, its signature) from the server, else (the failure, None, "")."""
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "RUSE-Bug-Watch"})
    try:
        with opener(req, timeout=TIMEOUT) as r:
            raw = r.read(MOST_BYTES + 1)
    except urllib.error.HTTPError as exc:
        return ("failed:none" if exc.code == 404 else f"failed:http-{int(exc.code)}"), None, ""
    except Exception as exc:  # noqa: BLE001 - no internet, a timeout, a certificate: the kept list stays
        certificate = isinstance(exc, ssl.SSLError) or isinstance(getattr(exc, "reason", None), ssl.SSLError)
        return ("failed:certificate" if certificate else "failed:offline"), None, ""
    if len(raw) > MOST_BYTES:
        return "failed:size", None, ""
    known, why, sig = _checked(raw)
    return ("ok", known, sig) if known is not None else (f"failed:{why}", None, "")


def _put(folder: Path, name: str, body: dict) -> bool:
    """`body` into folder/name through a file of its own and a replace, tried BUSY_TRIES times; whether it went in."""
    folder.mkdir(parents=True, exist_ok=True)
    temp = folder / f"known-crashes.{os.getpid()}.{secrets.token_hex(3)}.tmp.json"
    temp.write_text(json.dumps(body), encoding="utf-8")
    for attempt in range(BUSY_TRIES):
        try:
            os.replace(temp, folder / name)
            return True
        except PermissionError:
            if attempt + 1 < BUSY_TRIES:
                time.sleep(0.2)
    try:
        temp.unlink(missing_ok=True)
    except OSError:
        pass
    return False


# --- a crash checked against it (rusemod.bugwatch.read_dump) --------------------------------------------------------
def knows_build(known: Known | None, build) -> bool:
    """Whether the list is for this build of the game's program (size, checksum, time stamp, as a crash report's
    module list gives them)."""
    return known is not None and tuple(build or ()) in known.builds


def _holds(places, groups) -> bool:
    return all(any(lo <= at < hi for at in places for lo, hi in group) for group in groups)


def reason(known: Known | None, build, offset: int, chain=(), stack=None) -> str | None:
    """The key of the plain reason for a crash of the game's program at `offset` (from the program's start): one of
    REASONS when `build` is one the list is for, the place is one it knows, `chain` (the nearest places the crashed
    thread's stack returns to, nearest first, as a report sends them) holds what that place needs, and `stack` (every
    place it returns to in the part of it looked through; the chain when not given) what it needs there; None
    otherwise, and with no list."""
    if not knows_build(known, build):
        return None
    entry = known.places.get(offset)
    if entry is None:
        return None
    why, chain_needs, stack_needs = entry
    if not _holds(chain, chain_needs) or not _holds(chain if stack is None else stack, stack_needs):
        return None
    return why


def unit_number(known: Known | None, build, base: int, words, read, after_call) -> int | None:
    """The number (DescriptorId) of the unit the game was creating when it crashed, or None (and with no list).

    `words`: the crashed thread's stack, 8 bytes at a time from where it stopped up (nearest first); `base`: where
    the program was loaded; `read(address, size)`: the bytes the crash report kept there, None when it kept none;
    `after_call(offset)`: whether the place at that offset comes right after a call. Read only for the list's builds,
    and only when the stack returns into the unit-creation step: the unit descriptions that the words above that
    return point at (its caller keeps the one it is creating), up to the next return into the step. They must all hold
    one number: two different ones, or none, and no unit is said."""
    if not knows_build(known, build) or after_call is None:
        return None
    lo, hi = base + known.creating[0], base + known.creating[1]
    returns = [i for i, w in enumerate(words) if lo <= w < hi and after_call(w - base)]
    if not returns:
        return None
    end = returns[1] if len(returns) > 1 else len(words)
    found = set()
    for w in words[returns[0] + 1:end]:
        head = read(w, 8)
        if head is None or len(head) != 8 or struct.unpack("<Q", head)[0] - base not in known.kinds:
            continue
        raw = read(w + known.number_at, 4)
        number = struct.unpack("<I", raw)[0] if raw is not None and len(raw) == 4 else 0
        if number:
            found.add(number)
    return found.pop() if len(found) == 1 else None


def key_ready(key=None) -> str | None:
    """None when a release build may go out with this list key (KEY when None, read when called): 32 bytes, a point on
    the curve; else why not. While KEY is None the apps take a list on HTTPS alone, which a release build must not do
    (the owner, 2026-11-25: "Okay, yes for 15 sign.")."""
    public = KEY if key is None else key
    if public is None:
        return "the list key is not in the apps yet (KEY is None: a list would be taken on HTTPS alone)"
    if not isinstance(public, bytes) or len(public) != 32 or ed25519._decompress(public) is None:
        return "KEY is not an Ed25519 public key"
    return None


def main(argv: list[str]) -> int:
    """The release build's check that the list key is in the apps: run this module with --check-key."""
    if argv != ["--check-key"]:
        print("usage: python -m rusemod.knowncrashes --check-key")
        return 2
    why = key_ready()
    print(f"known-crashes key: {why}" if why else "known-crashes key: ready")
    return 1 if why else 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
