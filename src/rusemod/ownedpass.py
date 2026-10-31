"""Owned copies, layer 2: "Sign in through Steam".

Layer 1 (rusemod.owned) checks that the game folder is a copy the player owns, from the files Steam left behind.
Layer 2 adds a second, stronger proof for what the project runs online -- RUSE Guard and the optional content
downloads -- by asking Steam itself. The player signs in through Steam in their own browser; the project's server
(ruse-owned) asks Steam whether that account owns R.U.S.E. (app 21970) and hands back a short-lived pass signed with
the project's key. The pass carries no Steam ID, only a salted hash of it, so nothing kept here names the player.

The Launcher holds no secret and runs no local web server: it asks the server for a code, opens the login link in the
browser, and polls until the sign-in is done. That works the same on Windows, under Proton on the Steam Deck and on
Linux. A pass the player already has is checked here, offline, against the project's public key (PUBLIC_KEY) with
owned-copies' own Ed25519 (rusemod.owned.verify) -- the same signature the server makes -- so no network is needed to
trust a kept pass.

Held with RUSE Guard: ON is False until a release turns it on (the server is likewise off until its OWNED_LIVE switch
is set on Cloudflare). While ON is False, owned_pass_ok() is True for everyone, so nothing is gated and the sign-in
screen shows none of it.

Checked our_tools.json: its tools study the game's code; none signs in to Steam or checks a token, which is all this
module does, reusing rusemod.owned's own Ed25519 and rusemod.steam's APP_ID.
"""
from __future__ import annotations

import base64
import binascii
import json
import re
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .home import save_settings, settings
from .owned import verify
from .steam import APP_ID as _STEAM_APP_ID

APP_ID = int(_STEAM_APP_ID)   # 21970, the integer a pass carries (rusemod.steam keeps it as text for folder names)
SERVER = "https://ruse-owned.sneadtristen6.workers.dev"
# The project's pass public key (D:/RUSE-2.0/keys/cloudflare/pass.public.hex). Public: a pass is only ever CHECKED
# here, never signed; the private half lives only on the server as the secret PASS_KEY.
PUBLIC_KEY = bytes.fromhex("58edcfd55395d8e0378384da2bfefda977bf0745eee3a909d97aeadba5b00425")

ON = False              # the app side's switch, held off with RUSE Guard until a release turns it on
TIMEOUT = 30            # seconds for a server call
PASS_SETTING = "owned_pass"       # settings.json: the signed pass the player holds
SERVER_SETTING = "owned_server"   # settings.json: a server address other than SERVER (tests, a move)
PASS_KIND = "owned"
PASS_V = 1
_B64URL = re.compile(r"^[A-Za-z0-9_-]*$")
_WORDS = Path(__file__).with_name("ownedsignintext.toml")


class OwnedPassError(Exception):
    """A sign-in couldn't start or finish; the message is for the player (plain words, no detail to leak)."""


# --- the pass: the project's token format (ruse-owned worker.js signPass; the same as RUSE Guard's make_token) ---

def _canonical(payload: dict) -> str:
    """The exact text the server signs: JSON with sorted keys, no spaces, non-ASCII escaped (the worker's
    canonical()). A pass holds only ASCII, so this reproduces its signed bytes exactly."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _unb64url(text: str) -> bytes | None:
    if not isinstance(text, str) or not _B64URL.match(text) or len(text) % 4 == 1:
        return None
    try:
        return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    except (ValueError, binascii.Error):
        return None


def read_pass(token: str, public: bytes | None = None, now: int | None = None) -> tuple[dict | None, str]:
    """Check a signed pass. (payload, "ok") when it is a valid, unexpired owned-copy pass the project's key signed;
    (None, reason) otherwise. No network: the public key is enough. Mirrors the server's own /v1/pass/check."""
    public = PUBLIC_KEY if public is None else public
    now = int(time.time()) if now is None else int(now)
    if not isinstance(token, str):
        return None, "malformed pass"
    parts = token.strip().split(".")
    if len(parts) != 2:
        return None, "malformed pass"
    msg, sig = _unb64url(parts[0]), _unb64url(parts[1])
    if msg is None or sig is None:
        return None, "malformed pass"
    try:
        msg_text = msg.decode("utf-8")
        payload = json.loads(msg_text)
    except (UnicodeDecodeError, ValueError):
        return None, "malformed pass"
    if not isinstance(payload, dict):
        return None, "non-canonical payload"
    try:
        if _canonical(payload) != msg_text:
            return None, "non-canonical payload"
    except (TypeError, ValueError):
        return None, "non-canonical payload"
    if payload.get("alg") != "Ed25519":
        return None, "not an Ed25519 pass"
    if len(sig) != 64 or not verify(public, msg, sig):
        return None, "bad signature"
    if payload.get("kind") != PASS_KIND or payload.get("app") != APP_ID or payload.get("v") != PASS_V:
        return None, "not an owned-copy pass"
    exp = payload.get("exp")
    if not isinstance(exp, int) or isinstance(exp, bool) or exp <= now:
        return None, "expired"
    return payload, "ok"


# --- talking to the server (no secret held; the player's browser does the Steam sign-in) ---

def _call(url: str, data: bytes | None = None, timeout: float = TIMEOUT) -> tuple[int, dict]:
    """A GET (data None) or POST to the server; (status, the JSON body). The server answers JSON even when it refuses
    (off: 503; busy: 503), so an HTTPError's body is read too."""
    headers = {"User-Agent": "RUSE-Owned-client", "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _body(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, _body(exc.read())


def _body(raw: bytes) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def start(server: str = SERVER, timeout: float = TIMEOUT) -> dict:
    """Ask the server to begin a sign-in: {"code", "login_url", "poll_every", "expires_in"}. Raises OwnedPassError
    with a plain message when the server is off, busy, or unreachable."""
    if not str(server).startswith(("http://", "https://")):
        raise OwnedPassError("The sign-in server address isn't set up.")
    try:
        status, body = _call(server.rstrip("/") + "/v1/steam/start", data=b"", timeout=timeout)
    except (urllib.error.URLError, OSError, ValueError):
        raise OwnedPassError("We couldn't reach the sign-in server. Check your connection and try again.") from None
    if status == 200 and body.get("code") and body.get("login_url"):
        return {"code": str(body["code"]), "login_url": str(body["login_url"]),
                "poll_every": _pos(body.get("poll_every"), 3), "expires_in": _pos(body.get("expires_in"), 600)}
    raise OwnedPassError(str(body.get("reason") or "The sign-in server didn't answer. Try again in a few minutes."))


def poll(server: str, code: str, timeout: float = TIMEOUT) -> dict:
    """Ask the server whether the sign-in is done. Its JSON: {"status": "pending"|"owned"|"not-owned"|"private"|
    "steam-error"|"expired", "pass"?, "message"?}. A call that can't be made reads as steam-error, so the screen keeps
    polling or stops cleanly rather than throwing."""
    try:
        _status, body = _call(server.rstrip("/") + "/v1/steam/poll?code=" + urllib.parse.quote(str(code or ""), safe=""),
                              timeout=timeout)
    except (urllib.error.URLError, OSError, ValueError):
        return {"status": "steam-error"}
    return body if body.get("status") else {"status": "steam-error"}


def fetch_public(server: str = SERVER, timeout: float = TIMEOUT) -> bytes | None:
    """The server's current pass public key, for a check or to compare with PUBLIC_KEY; None if it isn't set up."""
    try:
        _status, body = _call(server.rstrip("/") + "/v1/pass/key", timeout=timeout)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    hexed = body.get("public")
    try:
        return bytes.fromhex(hexed) if isinstance(hexed, str) else None
    except ValueError:
        return None


def _pos(value, default: int) -> int:
    try:
        n = int(value)
        return n if n > 0 else default
    except (TypeError, ValueError):
        return default


# --- the pass the player holds (settings.json) ---

def store_pass(home, token: str) -> None:
    values = settings(home)
    values[PASS_SETTING] = str(token)
    save_settings(home, values)


def stored_pass(home) -> str:
    return str(settings(home).get(PASS_SETTING, "") or "")


def clear_pass(home) -> None:
    values = settings(home)
    if PASS_SETTING in values:
        values.pop(PASS_SETTING)
        save_settings(home, values)


def pass_status(home, public: bytes | None = None, now: int | None = None) -> dict:
    """{"signed_in", "owned", "until" (the pass's expiry, 0 when none/bad), "reason"}. A kept pass that no longer
    checks out (expired, or signed by a key we don't carry) reads as not signed in, with the reason."""
    token = stored_pass(home)
    if not token:
        return {"signed_in": False, "owned": False, "until": 0, "reason": "none"}
    payload, why = read_pass(token, public, now)
    if payload is None:
        return {"signed_in": False, "owned": False, "until": 0, "reason": why}
    return {"signed_in": True, "owned": True, "until": int(payload["exp"]), "reason": "ok"}


def words(lang: str = "us") -> dict:
    """The sign-in screen's words in `lang` (rusemod/ownedsignintext.toml), English where one isn't translated."""
    with open(_WORDS, "rb") as f:
        table = tomllib.load(f)
    return {key: values.get(lang) or values["us"] for key, values in table.items()}


class OwnedPassCalls:
    """The window API's calls for owned copies, layer 2, for both apps (a mixin beside rusemod.owned.OwnedCalls). It
    uses self._home (settings), self.prefs() (the language) and self._community_open (to open the login link). While
    ON is False it is held: the status says so and nothing is gated."""

    def _owned_server(self) -> str:
        return settings(self._home).get(SERVER_SETTING) or SERVER

    def _signin_lang(self) -> str:
        return (self.prefs() or {}).get("lang") or "us"

    def owned_pass_status(self) -> dict:
        """Whether the player is signed in through Steam and owns R.U.S.E., until when, with the screen's words and
        whether layer 2 is switched on at all."""
        return pass_status(self._home) | {"on": ON, "words": words(self._signin_lang()), "app_id": APP_ID}

    def owned_pass_ok(self) -> bool:
        """The gate the project's online features check: True when layer 2 is off (held), or the player holds a valid
        owned-copy pass. False only means "sign in through Steam first"."""
        return (not ON) or pass_status(self._home)["owned"]

    def owned_sign_in_start(self) -> dict:
        """Begin "Sign in through Steam": open Steam's login in the player's browser and return the code to poll with
        (owned_sign_in_poll). {"on": False} when layer 2 is off."""
        if not ON:
            return {"on": False}
        info = start(self._owned_server())
        self._community_open(info["login_url"])
        return {"on": True, **info}

    def owned_sign_in_poll(self, code: str) -> dict:
        """Ask the server whether the sign-in is done. On "owned", check the pass here and keep it, then return the
        fresh status; a pass that doesn't check out is refused ("bad-pass") and not kept."""
        if not ON:
            return {"status": "off"}
        result = poll(self._owned_server(), str(code or ""))
        if result.get("status") == "owned" and result.get("pass"):
            payload, why = read_pass(result["pass"])
            if payload is None:
                return {"status": "bad-pass", "reason": why} | self.owned_pass_status()
            store_pass(self._home, result["pass"])
            return {"status": "owned"} | self.owned_pass_status()
        return result

    def owned_sign_out(self) -> dict:
        """Forget the kept pass (the player signs in again next time it's needed)."""
        clear_pass(self._home)
        return self.owned_pass_status()
