"""RUSE Guard, the Launcher's side (DomesticNukes' design: his RUSE-Guard repository, docs/DESIGN.md). The match review
half (the detectors, the replay reader, the review server and screen) runs on his side; this is what the Launcher
does for it. Like the rest of fair play it is SWITCHED OFF (rusemod.fairplay.ON).

- **Signed tokens** in his format (`base64url(canonical JSON).base64url(signature)`), checked with Ed25519
  (rusemod.ed25519) against the public keys the owner ships in KEYS (empty until he makes them):
  - a **dev key** (`<home>/guard/devkey.txt`) is the one way past the offline lock: a developer's copy with test tools
    can join multiplayer, and its matches are filed as dev tests;
  - a **signed mod manifest** (`ruseguard.manifest` in a mod's folder) says the mod's files are exactly what the
    owner approved (DESIGN §3.7): a whole lobby running the same changed mod no longer passes.
- **After a multiplayer match** (only then: the in-game record writes nothing otherwise), the Launcher collects the
  record the game wrote (gamescripts/guard_hash.py25: the state-hash series §3.2, the script hotkeys §3.4), the
  match's replay, the copy's fingerprint and file list, the signed manifests and the process scan's findings (§3.5),
  signs the bundle with this install's own key and sends it to the RUSE Guard server, or keeps it in the outbox
  until a server is set.
- **The process scan** (§3.5, disclosed in the terms, the player can say no) looks only while a multiplayer match is
  live, only at running programs' names, against the server's list of known cheat tools. It reports names, never
  anything else, and it never decides anything: the server only uses it to raise a review that a real detector opened.
Nothing here judges or bans: the server opens reviews for people to look at.
"""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import ed25519, net

KEYS = Path(__file__).with_name("guard_keys.toml")   # the owner's public keys (hex), shipped with the apps
DEV_KEY = "guard/devkey.txt"                          # in the platform folder: a developer's dev key token
CLIENT_KEY = "guard/client.key"                       # this install's own signing key (made on first use)
OUTBOX = "guard/outbox"                               # bundles waiting for a server
REFUSED = "guard/refused"                             # bundles the server rejected for good (out of the send queue)
SIGNATURES = "guard/signatures.json"                  # the server's list of known cheat tools (last fetched)
SERVER = "https://ruse-guard.sneadtristen6.workers.dev"  # the project's server: the app window sets it as the default
#                                                       (GuardCalls.use_guard_server), so tests keep their bundles
MANIFEST = "ruseguard.manifest"                       # a signed mod manifest, in the mod's folder
MATCH_LOG = "ruse_guard_match.txt"                    # what the in-game record writes, in the copy's folder
TERMS_VERSION = 3                                     # the agreement's version; raised when its text changes, so the
#                                                       apps show it again (2: the final text of 2026-10-31; 3, 2026-11-02:
#                                                       a game crash report's chain and memory place listed)
BUNDLE_LIMIT = 20_000_000                             # the most a bundle may weigh (the replay is most of it)
SCAN_EVERY = 30                                       # seconds between process scans in a live multiplayer match


class GuardError(Exception):
    """A problem the player can act on; the message says what to do next."""


class GuardRefused(GuardError):
    """The server (or a local size check) rejected a bundle for good: its shape or size won't change on a retry, so
    the Launcher sets it aside (REFUSED) instead of keeping it in the outbox, where it would block the bundles queued
    behind it. `status` is the HTTP code (or "too-big")."""

    def __init__(self, status, reason: str = ""):
        super().__init__(f"the RUSE Guard server refused this bundle ({status})" + (f": {reason}" if reason else ""))
        self.status, self.reason = status, reason


# --- signed tokens (his format) ---
def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def canonical(payload: dict) -> bytes:
    """The bytes he signs: JSON with sorted keys and no spaces."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def keys() -> dict:
    """The owner's public keys: {"dev": bytes, "mods": bytes}, empty bytes until he has made them."""
    try:
        data = tomllib.loads(KEYS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return {k: bytes.fromhex(str(data.get(k, "") or "")) for k in ("dev", "mods")}


def read_token(token: str, public: bytes) -> tuple[dict | None, str]:
    """(payload, "ok") when `token` is signed by `public` (Ed25519), else (None, why). His HMAC form (HS256) needs
    the signer's secret, which an app must never hold, so it's refused here."""
    try:
        msg_b64, sig_b64 = token.strip().split(".", 1)
        msg, sig = _unb64(msg_b64), _unb64(sig_b64)
        payload = json.loads(msg.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None, "malformed token"
    if not isinstance(payload, dict) or canonical(payload) != msg:
        return None, "non-canonical payload"
    if payload.get("alg") != "Ed25519":
        return None, "not an Ed25519 token"
    if not public:
        return None, "no key to check it with yet"
    if not ed25519.verify(public, msg, sig):
        return None, "bad signature"
    return payload, "ok"


def make_token(payload: dict, secret: bytes) -> str:
    """Sign a token (the owner's tool, and the tests)."""
    payload = dict(payload, alg="Ed25519")
    msg = canonical(payload)
    return _b64(msg) + "." + _b64(ed25519.sign(secret, msg))


# --- dev keys (DESIGN §6) ---
@dataclass
class DevKey:
    valid: bool
    reason: str
    key_id: str = ""
    holder: str = ""
    scope: str = ""
    capabilities: list = field(default_factory=list)


def dev_key(home, public: bytes | None = None, now: int | None = None, revoked=()) -> DevKey:
    """The developer key in `home` (the platform folder), checked. None there: not valid, "none"."""
    try:
        token = Path(home, DEV_KEY).read_text(encoding="utf-8").strip()
    except OSError:
        return DevKey(False, "none")
    payload, why = read_token(token, keys()["dev"] if public is None else public)
    if payload is None:
        return DevKey(False, why)
    key_id = str(payload.get("key_id", ""))
    if key_id in set(revoked):
        return DevKey(False, "revoked", key_id)
    expires = int(payload.get("expires", 0) or 0)
    if expires and (int(time.time()) if now is None else now) > expires:
        return DevKey(False, "expired", key_id)
    return DevKey(True, "ok", key_id, str(payload.get("holder", "")), str(payload.get("scope", "all_dev_lobby")),
                  list(payload.get("capabilities", [])))


# --- signed mod manifests (DESIGN §3.7) ---
def mod_files(folder) -> dict:
    """{path in the mod folder (forward slashes): SHA-256} of every file a mod ships, its manifest left out."""
    folder = Path(folder)
    out = {}
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.name != MANIFEST:
            out[p.relative_to(folder).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


@dataclass
class ModVerdict:
    verified: bool
    reason: str
    mod_id: str = ""
    version: str = ""
    token: str = ""
    missing: list = field(default_factory=list)
    extra: list = field(default_factory=list)
    changed: list = field(default_factory=list)
    deployed: dict = field(default_factory=dict)  # {path: SHA-256} of the mod's files (his server checks them again)


def check_manifest(folder, public: bytes | None = None, revoked=()) -> ModVerdict:
    """Whether a mod folder is exactly what the owner signed: its manifest's signature, then every file's hash."""
    try:
        token = Path(folder, MANIFEST).read_text(encoding="utf-8").strip()
    except OSError:
        return ModVerdict(False, "not signed")
    payload, why = read_token(token, keys()["mods"] if public is None else public)
    if payload is None:
        return ModVerdict(False, why, token=token)
    mod_id, version = str(payload.get("mod_id", "")), str(payload.get("version", ""))
    if f"{mod_id}@{version}" in set(revoked) or mod_id in set(revoked):
        return ModVerdict(False, "revoked manifest", mod_id, version, token)
    signed, deployed = payload.get("files", {}), mod_files(folder)
    missing = sorted(p for p in signed if p not in deployed)
    extra = sorted(p for p in deployed if p not in signed)
    changed = sorted(p for p in signed if p in deployed and deployed[p] != signed[p])
    if missing or extra or changed:
        return ModVerdict(False, "the files don't match the signed manifest", mod_id, version, token, missing, extra,
                          changed, deployed)
    return ModVerdict(True, "ok", mod_id, version, token, deployed=deployed)


# --- the in-game record (gamescripts/guard_hash.py25) ---
@dataclass
class MatchLog:
    started: int
    multiplayer: bool
    coop: bool
    local: str
    hotkeys: list = field(default_factory=list)   # [(action, "module.function")]
    states: list = field(default_factory=list)    # [(game time, hash)]
    ended: float | None = None                    # game time at the end; None: the game closed mid-match


def read_match_log(text: str) -> list[MatchLog]:
    """Every match the in-game record wrote, in order."""
    out: list[MatchLog] = []
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        try:
            if parts[0] == "start":
                out.append(MatchLog(int(parts[1]), parts[3] == "1", parts[5] == "1", parts[7] if len(parts) > 7 else ""))
            elif not out:
                continue
            elif parts[0] == "hotkey":
                out[-1].hotkeys.append((parts[1], parts[2] if len(parts) > 2 else ""))
            elif parts[0] == "state":
                out[-1].states.append((float(parts[1]), parts[2]))
            elif parts[0] == "end":
                out[-1].ended = float(parts[1])
        except (IndexError, ValueError):
            continue
    return out


def live_multiplayer(copy) -> bool:
    """Whether the copy's game is in a multiplayer match right now (its record has a start and no end yet)."""
    try:
        matches = read_match_log(Path(copy, MATCH_LOG).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return False
    return bool(matches) and matches[-1].ended is None and (matches[-1].multiplayer or matches[-1].coop)


def find_replay(game, since: int, until: int | None = None) -> Path | None:
    """The newest replay (.ruserpl) the game saved for a match that started at `since` (Steam's userdata folders)."""
    steam = Path(game).resolve().parents[2]  # <Steam>/steamapps/common/<game>
    found = []
    for p in (steam / "userdata").glob("*/21970/*/*.ruserpl"):
        try:
            t = p.stat().st_mtime
        except OSError:
            continue
        if t >= since and (until is None or t <= until + 600):
            found.append((t, p))
    return max(found)[1] if found else None


def local_player(game) -> str:
    """This PC's player for the game: the Steam account (its number) whose R.U.S.E. profile changed last."""
    steam = Path(game).resolve().parents[2]
    found = []
    for p in (steam / "userdata").glob("*/21970/local/PROFILE.ruse2"):
        try:
            found.append((p.stat().st_mtime, p.parts[-4]))
        except OSError:
            continue
    return max(found)[1] if found else "unknown"


# --- the process scan (DESIGN §3.5) ---
def running_programs() -> list[str]:
    """The names of the programs running on this PC, lowercase (Windows' task list; nothing else is read)."""
    if sys.platform != "win32":
        return []
    out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    return sorted({row[0].lower() for row in csv.reader(io.StringIO(out.stdout)) if row})


def scan(signatures: list, programs: list[str] | None = None) -> list[dict]:
    """The known cheat tools among the running programs: [{"name", "what"}]. `signatures`: [{"name": "x.exe",
    "what": "..."}], the server's list."""
    running = set(running_programs() if programs is None else (p.lower() for p in programs))
    return [{"name": s["name"], "what": s.get("what", "")} for s in signatures
            if isinstance(s, dict) and str(s.get("name", "")).lower() in running]


# --- the bundle ---
def client_key(home) -> bytes:
    """This install's own signing key (32 random bytes, made on first use): it proves a bundle wasn't changed on
    its way and that the same install sent this player's earlier ones."""
    p = Path(home, CLIENT_KEY)
    try:
        key = p.read_bytes()
        if len(key) == 32:
            return key
    except OSError:
        pass
    p.parent.mkdir(parents=True, exist_ok=True)
    key = os.urandom(32)
    p.write_bytes(key)
    return key


def bundle(home, log: MatchLog, *, username: str, record: dict | None, replay: Path | None, manifests: list,
           dev: DevKey, findings: list, ended: int, stop: dict | None = None) -> dict:
    """One match's evidence, in his server's shapes (ruse_guard.review.MatchBundle + server.PlayerEvidence), plus
    the in-game hotkeys (§3.4) and the process scan's findings (§3.5), signed with this install's key. `username` is
    the name the player chose on the agreement screen (Nick#4821, rusemod.bugwatch set_username/turn_on): it, never
    the player's Steam ID, is who the record is filed under, so the review team can tell players apart and match a
    report to its player (the owner, 2026-10-30; no-steam-account-risk)."""
    record = record or {}
    verified = [m for m in manifests if m.verified]
    replay_b64 = ""
    if replay is not None and replay.stat().st_size < BUNDLE_LIMIT:
        replay_b64 = base64.b64encode(replay.read_bytes()).decode("ascii")
    key = client_key(home)
    public = ed25519.public_key(key).hex()
    # The server files every bundle under a handle and refuses an empty one (cloudflare/guard worker.js fieldsOf). A
    # player who accepted RUSE Guard but ticked neither opt-in was never asked for a username (sharedui/agreement.js),
    # so they're filed under this install's own anonymous id instead: the start of its public key, which every bundle
    # already carries in full as client_key. Never a Steam ID; no "#", so it can't look like a chosen username.
    handle = username or f"player-{public[:12]}"
    # each player's Launcher sends its own bundle; the server finds the others of the same match (by start time
    # and the shared state hashes) and gives the match its id. This install's own key (client_key) ties a player's
    # matches together without any Steam identifier.
    bundle_id = hashlib.sha256(f"{handle}|{log.started}".encode()).hexdigest()[:16]
    body = {
        "version": 1,
        "bundle_id": bundle_id,
        "match": {"match_id": "", "is_multiplayer": bool(log.multiplayer or log.coop), "players": [handle],
                  "map_name": "", "mode": "coop" if log.coop else "multiplayer", "result": "", "started": log.started,
                  "ended": ended, "replay_path": replay.name if replay else "", "dev_test": dev.valid,
                  "dev_key_id": dev.key_id if dev.valid else ""},
        "evidence": {"player": handle, "username": username, "team": log.local, "sync_code": record.get("fingerprint") or "",
                     "join_code": record.get("code") or "",
                     "files": {p: v.get("sha256", "") for p, v in record.get("files", {}).items()},
                     "state_series": [[t, h] for t, h in log.states],
                     "mod_token": verified[0].token if verified else "",
                     "mod_deployed": verified[0].deployed if verified else {},
                     "mods": [{"mod_id": m.mod_id, "version": m.version, "verified": m.verified, "reason": m.reason}
                              for m in manifests],
                     "dev_token": "" if not dev.valid else Path(home, DEV_KEY).read_text(encoding="utf-8").strip(),
                     "hotkeys": [[a, f] for a, f in log.hotkeys], "process_findings": findings,
                     "stop": stop or {},  # the offline lock's "a cheat copy was stopped" lines, read from the game's crash report
                     "ended_in_game": log.ended is not None},
        "replay": replay_b64,
    }
    body["client_key"] = public
    body["signature"] = ed25519.sign(key, canonical(body)).hex()
    return body


def check_bundle(body: dict) -> bool:
    """Whether a bundle's signature matches its own client key (the server's first check)."""
    try:
        sig = bytes.fromhex(body["signature"])
        rest = {k: v for k, v in body.items() if k != "signature"}
        return ed25519.verify(bytes.fromhex(body["client_key"]), canonical(rest), sig)
    except (KeyError, ValueError, TypeError):
        return False


def send(server: str, body: dict, timeout: float = 30) -> dict:
    """POST a bundle to the RUSE Guard server; its answer (JSON)."""
    if not server.startswith(("http://", "https://")):
        raise GuardError("The RUSE Guard server's address must start with http:// or https://.")
    data = json.dumps(body).encode("utf-8")
    if len(data) > BUNDLE_LIMIT * 2:
        # not a game rule: our own size limit for what's sent. It will never fit, so it's a refusal, not a retry.
        raise GuardRefused("too-big", "this match's evidence is too big to send")
    req = urllib.request.Request(server.rstrip("/") + "/api/bundle", data=data,
                                 headers={"Content-Type": "application/json", "User-Agent": "RUSE-Guard-client"})
    try:
        with net.urlopen(req, timeout) as r:  # noqa: S310 (an address the player set; net: the certificate fallbacks)
            return json.loads(r.read(1_000_000) or b"{}")
    except urllib.error.HTTPError as e:
        if 400 <= e.code < 500:
            # the server looked at the bundle and said no (bad shape, 413 too big): a retry won't change that
            raise GuardRefused(e.code, str(getattr(e, "reason", "") or "")) from e
        raise GuardError(f"the RUSE Guard server answered {e.code}") from e  # 5xx (incl. 503 full): try again later


def signatures(home, server: str = "", timeout: float = 15) -> list:
    """The server's list of known cheat tools, fetched when a server is set (kept for when it isn't reachable)."""
    cache = Path(home, SIGNATURES)
    if server:
        try:
            req = urllib.request.Request(server.rstrip("/") + "/api/signatures",
                                         headers={"User-Agent": "RUSE-Guard-client"})
            with net.urlopen(req, timeout) as r:  # noqa: S310
                found = json.loads(r.read(1_000_000))
            if isinstance(found, list):
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps(found), encoding="utf-8")
                return found
        except (OSError, ValueError):
            pass
    try:
        found = json.loads(cache.read_text(encoding="utf-8"))
        return found if isinstance(found, list) else []
    except (OSError, ValueError):
        return []


def set_aside(home, path: Path) -> None:
    """Move a refused bundle out of the outbox into REFUSED: kept for a look, out of the send queue so it can't block
    the bundles behind it."""
    refused = Path(home, REFUSED)
    refused.mkdir(parents=True, exist_ok=True)
    try:
        path.replace(refused / path.name)
    except OSError:
        try:
            path.unlink()
        except OSError:
            pass


def deliver(home, body: dict, server: str = "") -> str:
    """Send a bundle, or keep it in the outbox (no server, or not reachable). Then try the outbox's older ones. A
    bundle the server refuses for good (a 4xx answer, or one too big to send) is set aside (REFUSED) so it can't
    block the rest; one that only failed to reach a working server is kept, to try again later. For the log."""
    outbox = Path(home, OUTBOX)
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / f"{body['bundle_id']}.json").write_text(json.dumps(body), encoding="utf-8")
    if not server:
        return "kept: no RUSE Guard server is set"
    sent = aside = 0
    for p in sorted(outbox.glob("*.json")):
        try:
            send(server, json.loads(p.read_text(encoding="utf-8")))
            p.unlink()
            sent += 1
        except GuardRefused:
            set_aside(home, p)   # the server won't ever take it: move it out of the way and go on to the next
            aside += 1
        except (OSError, ValueError, GuardError):
            break                # can't reach the server, or it's full/down (5xx): keep this and the rest, try later
    waiting = len(list(outbox.glob("*.json")))
    return f"sent {sent}; {waiting} waiting" + (f"; {aside} set aside" if aside else "")


# --- the Launcher's settings for it ---
def settings_of(values: dict, default_server: str = "") -> dict:
    """The player's RUSE Guard settings. `default_server` is where bundles go when the player set no server: the app
    window passes SERVER; tests pass nothing, so their bundles stay in the outbox and never leave the PC."""
    g = values.get("guard") if isinstance(values.get("guard"), dict) else {}
    return {"terms": int(g.get("terms", 0) or 0), "scan": bool(g.get("scan", True)),
            "server": str(g.get("server", default_server))}


# --- after the game starts: watch, then collect ---
def collect(home, game, copy, *, username: str, scan_findings: list | None = None, manifests: list | None = None,
            server: str = "", now: int | None = None, say=print) -> list[str]:
    """After the game closed: every multiplayer match in the copy's record becomes a bundle, delivered or kept, filed
    under the player's chosen `username` (never their Steam ID). The record is cleared once read. Returns what
    happened, one line per match."""
    from .fairplay import read_record
    log_path = Path(copy, MATCH_LOG)
    try:
        matches = read_match_log(log_path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []
    now = int(time.time()) if now is None else now
    record, dev, said = read_record(copy), dev_key(home), []
    for log in matches:
        if not (log.multiplayer or log.coop):
            continue  # (the record never writes these; checked again: offline is never sent)
        replay = find_replay(game, log.started, now)
        body = bundle(home, log, username=username, record=record, replay=replay, manifests=manifests or [], dev=dev,
                      findings=scan_findings or [], ended=now)
        said.append(f"RUSE Guard: match {body['bundle_id']}: " + deliver(home, body, server))
    try:
        log_path.unlink()
    except OSError:
        pass
    for line in said:
        say(line)
    return said


# --- the offline lock's crash evidence (the owner's 2026-10-30 crash route): when the lock stops a cheat copy it
# crashes the game on purpose, and the game's crash reporter writes a dump. The Launcher reads only RUSE Guard's own
# marked lines from that dump here, strips any Steam ID, long id or path (defence in depth; the mark itself carries
# none, findings F-150), and sends them as a small bundle; the dump itself never leaves the PC (no-steam-account-risk).
GUARD_DUMPS = ("Temp/CrashRpt_*/*.dmp", "*Dumps/RUSE.exe*.dmp")  # the game's crash reporter's folder, then Windows' own
_STEAM_ID = re.compile(rb"7656\d{13}")             # a SteamID64
_LONG_ID = re.compile(rb"\d{9,}")                  # an account number or other long id
_WIN_PATH = re.compile(rb"[A-Za-z]:\\[^\s\"<>|]+")  # a Windows path (the dump's module list etc.)
_MARK = re.compile(rb"RUSEGUARD-[A-Z]+.{0,4000}?RUSEGUARD-END", re.DOTALL)


def _clean_stop(raw: bytes) -> str:
    """RUSE Guard's marked text with any Steam ID, long id or path taken out (defence in depth), printable only."""
    raw = _STEAM_ID.sub(b"<id>", raw)
    raw = _WIN_PATH.sub(b"<path>", raw)
    raw = _LONG_ID.sub(b"<n>", raw)
    return "".join(c if 32 <= ord(c) < 127 else " " for c in raw.decode("ascii", "replace")).strip()[:1000]


def read_stop(dump_path) -> dict | None:
    """From a crash report file on this PC, the offline lock's marked lines ("a cheat copy was stopped"), cleaned of any
    Steam ID, long id or path. None if the dump has no filled-in RUSE Guard mark. The dump never leaves the PC; only
    these cleaned lines do. The crash code is the game's script-error stop (0x29a, findings F-147/F-150).

    Only a FILLED-IN mark counts, not the static format template ("...multi %d coop %d local %s..."): that template
    sits in the script's memory for ANY crash of a guard copy (the real dump of 2026-10-31 held both), so taking it
    would send a useless line and make every crash look like a stop. A real stop has the values in (multi 1 coop 0
    local 0) and no "%" (findings F-150)."""
    try:
        data = Path(dump_path).read_bytes()
    except OSError:
        return None
    found = [m.group() for m in _MARK.finditer(data)]
    try:  # the game writes some of it as UTF-16: find the mark there too
        wide = re.findall(r"RUSEGUARD-[A-Z]+.{0,4000}?RUSEGUARD-END", data.decode("utf-16-le", "ignore"), re.DOTALL)
        found += [w.encode("ascii", "replace") for w in wide]
    except (UnicodeError, ValueError):
        pass
    filled = [m for m in found if b"%" not in m]   # drop the unformatted template; keep only a real, filled-in mark
    if not filled:
        return None
    return {"text": _clean_stop(max(filled, key=len)), "code": "0x29a"}


def stop_dumps_since(since: float, local: str | None = None) -> list[Path]:
    """The crash report files written after `since` on this PC (GUARD_DUMPS under %LOCALAPPDATA%)."""
    local = local or os.environ.get("LOCALAPPDATA")
    if not local:
        return []
    out = []
    for pattern in GUARD_DUMPS:
        for p in Path(local).glob(pattern):
            try:
                if p.stat().st_mtime >= since:
                    out.append(p)
            except OSError:
                continue
    return out


def collect_stops(home, since, *, username: str, server: str = "", now: int | None = None, say=print,
                  local: str | None = None) -> list[str]:
    """After the game closed: every new crash report that carries RUSE Guard's mark (a cheat copy the offline lock
    stopped) becomes a small signed bundle, its cleaned lines in evidence.stop, delivered or kept. Each dump is read
    at most once per run. Returns one line per report."""
    now = int(time.time()) if now is None else now
    dev, said, seen = dev_key(home), [], set()
    for dump in stop_dumps_since(since, local):
        stop = read_stop(dump)
        if stop is None or stop["text"] in seen:
            continue
        seen.add(stop["text"])
        try:
            started = int(Path(dump).stat().st_mtime)
        except OSError:
            started = now
        log = MatchLog(started=started, multiplayer=True, coop=False, local="")
        body = bundle(home, log, username=username, record={}, replay=None, manifests=[], dev=dev, findings=[],
                      ended=now, stop=stop)
        said.append(f"RUSE Guard: a cheat copy was stopped ({body['bundle_id']}): " + deliver(home, body, server))
    for line in said:
        say(line)
    return said


class MatchWatch(threading.Thread):
    """Runs beside the game the Launcher started: while a multiplayer match is live and the player allowed it, the
    process scan every SCAN_EVERY seconds; when the game closes, `collect` the match record, then `collect_stops` any
    crash the offline lock caused."""

    def __init__(self, process, home, game, copy, *, username: str, consent: dict, manifests: list, say=print,
                 sleep=time.sleep, local: str | None = None):
        super().__init__(daemon=True, name="ruse-guard-watch")
        self.process, self.home, self.game, self.copy = process, home, game, copy
        self.username, self.consent, self.manifests, self.say, self.sleep = username, consent, manifests, say, sleep
        self.local = local           # where the crash reports are written (%LOCALAPPDATA% when None)
        self.started = time.time()   # only crash reports written after this are this match's
        self.findings: list[dict] = []

    def run(self) -> None:
        # the program check is part of RUSE Guard (not an opt-in): it runs whenever the player has accepted the terms
        accepted = self.consent.get("terms", 0) >= TERMS_VERSION
        sigs = signatures(self.home, self.consent.get("server", "")) if accepted else []
        while self.process.poll() is None:
            if sigs and live_multiplayer(self.copy):
                for f in scan(sigs):
                    if f not in self.findings:
                        self.findings.append(f)
            self.sleep(SCAN_EVERY)
        if self.consent.get("terms", 0) >= TERMS_VERSION:
            server = self.consent.get("server", "")
            collect(self.home, self.game, self.copy, username=self.username, scan_findings=self.findings,
                    manifests=self.manifests, server=server, say=self.say)
            # the offline lock stops a cheat copy by crashing it: read that crash's marked lines and send them too
            collect_stops(self.home, self.started, username=self.username, server=server, say=self.say,
                          local=self.local)
