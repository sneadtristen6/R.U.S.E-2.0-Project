"""Signed releases (the legal fixes' Part 7; the owner, 2026-11-25, question 26: "Yep, all three for 26"): an app
installs an update only when the owner's own signature names that update's exact files. Each release carries
`RUSE-<App>-Setup-<version>.exe.sig` beside its installer, made on his PC by his signing tool after GitHub's build:
one statement per line, `base64url(canonical JSON) "." base64url(Ed25519 signature)` (the token form RUSE Guard's
tokens use), each signed with one of his release keys. The public halves are in release_keys.toml; the private halves
never leave his PC and his USB stick.

A statement names the app, version, tag and installer, the installer's size and SHA-256, the notes file's name, size
and SHA-256 (What's new in every language), the required threshold (apps older than it install this release by
themselves) and the commit it was built from. There are no dates: a PC's clock never matters. What an app reads from
GitHub alone (its digest, the hash in the release text, the release text's required line and its notes) is not
trusted by an app with this check.

Only standard Python and rusemod.ed25519 (the apps only verify; the signing tool signs with its own copy). Nothing
here raises on bad input: read() and fits() say why.
"""
from __future__ import annotations

import base64
import json
import re
import sys
import tomllib
from pathlib import Path

from . import ed25519

KIND = "ruse2-release"      # a token signed for anything else (RUSE Guard's, an unlock code) can't pass as a release
FORMAT = 1                  # the statement's version ("v"); a line of a later format is left for a later app
SUFFIX = ".sig"             # the signature file: the installer's name and this
MOST = 16_384               # the most a signature file may hold (bytes)
MOST_LINES = 16
KEYS_FILE = Path(__file__).with_name("release_keys.toml")
APPS = {"launcher": "Launcher", "studio": "Studio"}
TAG_VERSION = r"\d+\.\d+\.\d+(?:\.\d+)?"  # a release's version: three numbers, or four (0.9.4.1, 0.9.8.1)
REQUIRED = re.compile(r"^\s*<!--\s*required update\s*-->\s*$", re.M | re.I)  # under a version's notes: it's required
FIELDS = frozenset({"alg", "kind", "v", "key", "app", "version", "tag", "file", "size", "sha256", "notes_file",
                    "notes_size", "notes_sha256", "required", "commit"})
LARGEST = 2 ** 31           # the biggest file size a statement may name
# The RFC 8032 test vectors' public keys (section 7.1, TEST 1 and TEST 2): the tests sign with those published secrets,
# so a key everyone can sign with is never one a release build may carry (keys_ready)
TEST_PUBLICS = frozenset({
    bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"),
    bytes.fromhex("3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"),
})
_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_PART = re.compile(r"[A-Za-z0-9_-]+")


def version_tuple(v: str) -> tuple:
    try:
        return tuple(int(p) for p in str(v).split("."))
    except ValueError:
        return (0,)


def load_keys(path: Path = KEYS_FILE) -> dict[str, bytes]:
    """The owner's release keys' public halves, {name: 32 bytes}, from release_keys.toml: those written as 64 hex
    characters (an empty one, or one written wrong, is left out here; keys_ready names it)."""
    try:
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    keys = data.get("keys") if isinstance(data.get("keys"), dict) else {}
    return {str(k): bytes.fromhex(v) for k, v in keys.items() if isinstance(v, str) and _HEX64.fullmatch(v)}


RELEASE_KEYS = load_keys()   # the tests patch this; no setting, argument or environment variable changes it


def canonical(payload: dict) -> bytes:
    """The bytes that are signed: JSON with sorted keys, no spaces, ASCII only."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    if not _PART.fullmatch(text) or len(text) % 4 == 1:
        raise ValueError("not base64url")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def make(payload: dict, secret: bytes, key: str) -> str:
    """One signed line for `payload` (the owner's signing tool has its own copy of this; the tests use this one)."""
    body = dict(payload, alg="Ed25519", kind=KIND, v=FORMAT, key=key)
    msg = canonical(body)
    return _b64(msg) + "." + _b64(ed25519.sign(secret, msg))


def _line(line: str, keys: dict) -> tuple[dict | None, str]:
    try:
        msg_b64, sig_b64 = line.split(".")
        msg, sig = _unb64(msg_b64), _unb64(sig_b64)
        payload = json.loads(msg.decode("ascii"))
    except (ValueError, UnicodeDecodeError):
        return None, "a line isn't a signed statement"
    if not isinstance(payload, dict) or canonical(payload) != msg:
        return None, "a statement isn't in its one exact form"
    if type(payload.get("v")) is not int or payload.get("v") != FORMAT:
        return None, "later"      # a format this app doesn't know: left alone, never an error
    if payload.get("alg") != "Ed25519" or payload.get("kind") != KIND:
        return None, "a statement isn't a release's"
    public = keys.get(payload.get("key")) if isinstance(payload.get("key"), str) else None
    if not public:
        return None, "a statement is signed with a key this app doesn't have"
    if not ed25519.verify(public, msg, sig):
        return None, "a statement's signature doesn't hold"
    return payload, "ok"


def read(text, keys: dict | None = None) -> tuple[dict | None, str]:
    """(the signed statement, "ok") from a signature file's text (str or bytes), else (None, why). A line in a later
    format is skipped; lines that verify must all say the same apart from the key that signed them (a change of keys is
    signed with both); if none verifies there is no signature."""
    keys = RELEASE_KEYS if keys is None else keys
    if isinstance(text, bytes):
        if len(text) > MOST:
            return None, "the signature file is too big"
        try:
            text = text.decode("ascii")
        except UnicodeDecodeError:
            return None, "the signature file isn't plain text"
    if not isinstance(text, str) or len(text) > MOST:
        return None, "no signature file"
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None, "the signature file is empty"
    if len(lines) > MOST_LINES:
        return None, "the signature file has too many lines"
    found, why = [], "no line is signed with a key this app has"
    for line in lines:
        payload, said = _line(line, keys)
        if payload is not None:
            found.append(payload)
        elif said != "later":
            why = said
    if not found:
        return None, why
    same = [{k: v for k, v in p.items() if k != "key"} for p in found]
    if any(s != same[0] for s in same[1:]):
        return None, "two signed lines say different things"
    return found[0], "ok"


def _size(value) -> bool:
    return type(value) is int and 1 <= value <= LARGEST


def fits(payload: dict, app: str, version: str, tag: str, file: str, keys: dict | None = None) -> str | None:
    """None when the signed statement is this release's (`app`, `version`, `tag`, `file` as the app found them on
    GitHub), else why not. Every field must be there, of its kind, and no other."""
    keys = RELEASE_KEYS if keys is None else keys
    if not isinstance(payload, dict) or set(payload) != FIELDS:
        return "the statement's fields aren't a release statement's"
    if payload["alg"] != "Ed25519" or payload["kind"] != KIND or type(payload["v"]) is not int or payload["v"] != FORMAT:
        return "the statement isn't a release statement"
    if payload["key"] not in keys:
        return "the statement names a key this app doesn't have"
    if app not in APPS or (payload["app"], payload["version"], payload["tag"], payload["file"]) != (app, version, tag, file):
        return "the statement is another release's"
    if not isinstance(version, str) or not re.fullmatch(TAG_VERSION, version) or tag != f"{app}-v{version}":
        return "the statement's version isn't a release's"
    if file != f"RUSE-{APPS[app]}-Setup-{version}.exe" or payload["notes_file"] != f"RUSE-{APPS[app]}-notes.json":
        return "the statement names other files"
    if not (_size(payload["size"]) and _size(payload["notes_size"])):
        return "the statement's sizes aren't whole numbers of bytes"
    if not all(isinstance(payload[k], str) and _HEX64.fullmatch(payload[k]) for k in ("sha256", "notes_sha256")):
        return "the statement's SHA-256 values aren't written as they must be"
    if not (isinstance(payload["commit"], str) and _HEX40.fullmatch(payload["commit"])):
        return "the statement's commit isn't written as it must be"
    req = payload["required"]
    if not isinstance(req, str) or (req and (not re.fullmatch(TAG_VERSION, req) or
                                            version_tuple(req) > version_tuple(version))):
        return "the statement's required version isn't one"
    return None


def required_for(payload: dict, current: str) -> bool:
    """Whether an app at `current` installs this release by itself: it's older than the signed threshold."""
    req = payload.get("required") if isinstance(payload, dict) else ""
    return bool(req) and isinstance(req, str) and version_tuple(current) < version_tuple(req)


def required_in_notes(notes: str, version: str) -> str:
    """The threshold for a release of `version`, from its English notes (.github/release-notes/<app>.md): the newest
    version up to it whose notes carry the line `<!-- required update -->`, or "" (what the signing tool signs; the
    same rule the apps used to read from the release text)."""
    parts = re.split(rf"^\*\*({TAG_VERSION}):\*\*", notes or "", flags=re.M)
    found = [v for v, text in zip(parts[1::2], parts[2::2])
             if version_tuple(v) <= version_tuple(version) and REQUIRED.search(text)]
    return max(found, key=version_tuple) if found else ""


def keys_ready(keys: dict | None = None, path: Path = KEYS_FILE) -> str | None:
    """None when a release build may go out with these keys: at least two (the daily one and the backup), each a
    point on the curve, all different, none of them a published test key, none written wrong in the file; else why
    not (the release build stops: an app without the owner's keys could never update itself)."""
    if keys is None:
        try:
            raw = tomllib.loads(Path(path).read_text(encoding="utf-8")).get("keys") or {}
        except (OSError, ValueError) as exc:
            return f"{Path(path).name} can't be read ({exc})"
        bad = [k for k, v in raw.items() if not (isinstance(v, str) and (v == "" or _HEX64.fullmatch(v)))]
        if bad:
            return f"{', '.join(sorted(bad))}: not written as 64 lowercase hex characters"
        keys = load_keys(path)
    if len(keys) < 2:
        return f"the owner's release keys aren't in {KEYS_FILE.name} yet ({len(keys)} of at least 2)"
    if len(set(keys.values())) != len(keys):
        return "two release keys are the same"
    for name, public in keys.items():
        if len(public) != 32 or ed25519._decompress(public) is None:
            return f"{name} isn't an Ed25519 public key"
        if public in TEST_PUBLICS:
            return f"{name} is a published test key, which anyone can sign with"
    return None


def main(argv: list[str]) -> int:
    """`python -m rusemod.releasesig --check-keys`: the release build's check that the owner's keys are in."""
    if argv != ["--check-keys"]:
        print("usage: python -m rusemod.releasesig --check-keys")
        return 2
    why = keys_ready()
    print(f"release keys: {why}" if why else f"release keys: {', '.join(sorted(RELEASE_KEYS))} ready")
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
