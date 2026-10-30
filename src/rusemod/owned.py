"""Owned copies only: the apps start a modded game only from a copy of R.U.S.E. its player owns.

R.U.S.E. itself starts only for a Steam account that owns it, unless Steam's own file in the game folder is swapped
for a fake one. So the check here looks at the game folder the way Steam left it:

- Steam's record of the install: `appmanifest_21970.acf` in the `steamapps` folder two levels up, naming this folder.
- Steam's own file, `steam_api64.dll`: signed by Valve, and the signature fits the file (the signed digest of the file
  is the file's digest now). Read from the file itself, the same on Windows, under Proton/Wine and on Linux.
- No files a fake Steam leaves beside the game (FAKE_STEAM_FILES).

A copy that fails can still be confirmed: owners of a copy from before R.U.S.E. was on Steam, or anyone the check gets
wrong, open a ticket (Discord or GitHub) with their folder code, and the project sends back an unlock code. The folder
code comes from this PC and the game's RUSE.exe, so an unlock code works on that one PC only. Unlock codes are
Ed25519 signatures made with a key only the project holds; the apps carry its public half (UNLOCK_PUBLIC_KEY) and keep
the codes they were given in settings.json ("unlocks").

The code is open, so anyone can take a check out of it: this stops a pirated copy from being modded and played with
the apps as they are released, not someone who rebuilds them.

Checked our_tools.json: its tools study the game's code; none hashes a file or reads a file's signature, which is all
this module does.
"""
from __future__ import annotations

import hashlib
import struct
import sys
import tomllib
import uuid
from pathlib import Path
from urllib.parse import urlencode

from .home import save_settings, settings
from .lock import _B32, _B32_READ
from .steam import APP_ID, parse_vdf

STEAM_FILE = "steam_api64.dll"
VALVE = ("valve corp.", "valve corporation")  # the signer's organisation or name, as Valve's certificates write it
# files and folders a fake Steam leaves in the game folder (names as they are, compared without case)
FAKE_STEAM_FILES = ("steam_settings", "steam_emu.ini", "SmartSteamEmu.ini", "SmartSteamEmu", "steam_api64_o.dll",
                    "steam_api_o.dll", "cream_api.ini", "ColdClientLoader.ini", "steamclient_loader.exe",
                    "steam_interfaces.txt", "CODEX.ini", "CODEX64.ini", "ALI213.ini", "3DMGAME.ini")
UNLOCK_PUBLIC_KEY = bytes.fromhex("67ff7ef1bd30a9f2caba02c941dbb95ea58b2128c488468744f37ed87c976c5a")
UNLOCK_PREFIX = b"RUSE2-UNLOCK-1:"
FOLDER_PREFIX = b"RUSE2-FOLDER-1|"
DISCORD = "https://discord.gg/h54t5baNsC"
TICKET = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/issues/new"
STEAM_VERIFY = f"steam://validate/{APP_ID}"
_WORDS = Path(__file__).with_name("ownedtext.toml")


# --- Ed25519 signatures (RFC 8032): checked here; made by the project with sign() and its private key ---

_P = 2 ** 255 - 19
_Q = 2 ** 252 + 27742317777372353535851937790883648493
_D = -121665 * pow(121666, _P - 2, _P) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)


def _h(data: bytes) -> int:
    return int.from_bytes(hashlib.sha512(data).digest(), "little") % _Q


def _add(a, b):
    p1, p2 = (a[1] - a[0]) * (b[1] - b[0]) % _P, (a[1] + a[0]) * (b[1] + b[0]) % _P
    c, d = 2 * a[3] * b[3] * _D % _P, 2 * a[2] * b[2] % _P
    e, f, g, h = p2 - p1, d - c, d + c, p2 + p1
    return e * f % _P, g * h % _P, f * g % _P, e * h % _P


def _mul(s: int, pt):
    out = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            out = _add(out, pt)
        pt = _add(pt, pt)
        s >>= 1
    return out


def _same(a, b) -> bool:
    return (a[0] * b[2] - b[0] * a[2]) % _P == 0 and (a[1] * b[2] - b[1] * a[2]) % _P == 0


def _x_of(y: int, sign: int):
    if y >= _P:
        return None
    x2 = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P) % _P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P:
        x = x * _SQRT_M1 % _P
    if (x * x - x2) % _P:
        return None
    return _P - x if (x & 1) != sign else x


_GY = 4 * pow(5, _P - 2, _P) % _P
_GX = _x_of(_GY, 0)
_G = (_GX, _GY, 1, _GX * _GY % _P)


def _pack(pt) -> bytes:
    zi = pow(pt[2], _P - 2, _P)
    x, y = pt[0] * zi % _P, pt[1] * zi % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _unpack(data: bytes):
    if len(data) != 32:
        return None
    y = int.from_bytes(data, "little")
    sign, y = y >> 255, y & ((1 << 255) - 1)
    x = _x_of(y, sign)
    return None if x is None else (x, y, 1, x * y % _P)


def _expand(secret: bytes) -> tuple[int, bytes]:
    h = hashlib.sha512(secret).digest()
    return int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254), h[32:]


def public_key(secret: bytes) -> bytes:
    return _pack(_mul(_expand(secret)[0], _G))


def sign(secret: bytes, message: bytes) -> bytes:
    a, prefix = _expand(secret)
    pub = _pack(_mul(a, _G))
    r = _h(prefix + message)
    big_r = _pack(_mul(r, _G))
    return big_r + ((r + _h(big_r + pub + message) * a) % _Q).to_bytes(32, "little")


def verify(public: bytes, message: bytes, signature: bytes) -> bool:
    if len(signature) != 64:
        return False
    a, r = _unpack(public), _unpack(signature[:32])
    s = int.from_bytes(signature[32:], "little")
    if a is None or r is None or s >= _Q:
        return False
    return _same(_mul(s, _G), _add(r, _mul(_h(signature[:32] + public + message), a)))


# --- codes: Crockford base32 (rusemod.lock's letters), read back without dashes, spaces or case ---

def b32(data: bytes) -> str:
    bits = len(data) * 8
    width = -(-bits // 5)
    n = int.from_bytes(data, "big") << (width * 5 - bits)
    return "".join(_B32[(n >> (5 * (width - 1 - i))) & 31] for i in range(width))


def unb32(text: str, size: int) -> bytes | None:
    chars = [c for c in str(text).upper() if c not in " -_\n\r\t"]
    if any(c not in _B32_READ for c in chars) or len(chars) != -(-size * 8 // 5):
        return None
    n = 0
    for c in chars:
        n = n << 5 | _B32_READ[c]
    return (n >> (len(chars) * 5 - size * 8)).to_bytes(size, "big")


def _clean(code: str) -> str:
    return "".join(c for c in str(code).upper() if c not in " -_\n\r\t")


def grouped(code: str, size: int = 4) -> str:
    code = _clean(code)
    return "-".join(code[i:i + size] for i in range(0, len(code), size))


# --- this PC and this game folder ---

def machine_id() -> str:
    """This PC's own id: Windows' MachineGuid (a Wine or Proton prefix has its own), Linux's machine-id."""
    if sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                return str(winreg.QueryValueEx(k, "MachineGuid")[0])
        except OSError:
            pass
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            text = Path(path).read_text(encoding="ascii").strip()
            if text:
                return text
        except OSError:
            pass
    return f"{uuid.getnode():012x}"


def _file_sha256(path: Path) -> bytes:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.digest()


def folder_code(game: Path, machine: str | None = None) -> str:
    """The code a player sends in a ticket: this PC and the game's RUSE.exe, 16 characters."""
    exe = Path(game) / "RUSE.exe"
    digest = _file_sha256(exe) if exe.is_file() else b""
    seed = FOLDER_PREFIX + (machine or machine_id()).encode("utf-8") + b"|" + digest
    return b32(hashlib.sha256(seed).digest()[:10])


def unlock_code(secret: bytes, code: str) -> str:
    """The project's answer to a ticket, made with its private key."""
    return grouped(b32(sign(secret, UNLOCK_PREFIX + _clean(code).encode("ascii"))), 5)


def unlock_fits(unlock: str, code: str, public: bytes | None = None) -> bool:
    signature = unb32(unlock, 64)
    return signature is not None and verify(public or UNLOCK_PUBLIC_KEY, UNLOCK_PREFIX + _clean(code).encode("ascii"),
                                            signature)


# --- Steam's own file: its Authenticode signature, read from the file ---

def _tlv(data: bytes, at: int) -> tuple[int, int, int]:
    """The DER element at `at`: (its tag, where its content starts, where it ends)."""
    tag, size, at = data[at], data[at + 1], at + 2
    if size & 0x80:
        n = size & 0x7F
        size, at = int.from_bytes(data[at:at + n], "big"), at + n
    if at + size > len(data):
        raise ValueError("cut short")
    return tag, at, at + size


def _kids(data: bytes, start: int, end: int) -> list[tuple[int, int, int]]:
    out = []
    while start < end:
        out.append(_tlv(data, start))
        start = out[-1][2]
    return out


def _oid(raw: bytes) -> str:
    parts, n = [raw[0] // 40, raw[0] % 40], 0
    for byte in raw[1:]:
        n = n << 7 | (byte & 0x7F)
        if not byte & 0x80:
            parts.append(n)
            n = 0
    return ".".join(map(str, parts))


_DIGESTS = {"1.3.14.3.2.26": "sha1", "2.16.840.1.101.3.4.2.1": "sha256", "2.16.840.1.101.3.4.2.2": "sha384",
            "2.16.840.1.101.3.4.2.3": "sha512"}
_NAME_PARTS = {"2.5.4.3", "2.5.4.10"}  # a certificate's common name and organisation


def _names(der: bytes, start: int, end: int) -> list[str]:
    """The common name and organisation in a certificate's Name."""
    out = []
    for _set, a, b in _kids(der, start, end):
        for _seq, c, d in _kids(der, a, b):
            kids = _kids(der, c, d)
            if len(kids) == 2 and _oid(der[kids[0][1]:kids[0][2]]) in _NAME_PARTS:
                out.append(der[kids[1][1]:kids[1][2]].decode("utf-8", "replace").strip().lower())
    return out


def _signature(pe: bytes) -> tuple[bytes, int, int, int, int] | None:
    """(the PKCS#7 blob, where the checksum is, where the certificate entry is, the table's start and size)."""
    if pe[:2] != b"MZ":
        return None
    head = struct.unpack_from("<I", pe, 0x3C)[0]
    if pe[head:head + 4] != b"PE\0\0":
        return None
    opt = head + 24
    magic = struct.unpack_from("<H", pe, opt)[0]
    entry = opt + (112 if magic == 0x20B else 96) + 4 * 8  # the fifth data directory: the certificates
    start, size = struct.unpack_from("<II", pe, entry)
    if not start or not size or start + size > len(pe):
        return None
    length, _revision, kind = struct.unpack_from("<IHH", pe, start)
    if kind != 2:  # WIN_CERT_TYPE_PKCS_SIGNED_DATA
        return None
    return pe[start + 8:start + length], opt + 64, entry, start, size


def signed_by(path: Path) -> str | None:
    """Who signed this Windows file (its signer's common name and organisation), when the signature fits the file as
    it is: the digest it signed is the file's digest now. None for an unsigned file or one changed after signing."""
    try:
        pe = Path(path).read_bytes()
        found = _signature(pe)
        if found is None:
            return None
        blob, checksum, entry, start, size = found
        _tag, a, b = _tlv(blob, 0)
        top = _kids(blob, a, b)
        if _oid(blob[top[0][1]:top[0][2]]) != "1.2.840.113549.1.7.2":  # signedData
            return None
        _seq, da, db = _tlv(blob, top[1][1])
        parts = _kids(blob, da, db)
        # the signed content: SpcIndirectDataContent { the file's kind, DigestInfo { algorithm, digest } }
        content = _kids(blob, parts[2][1], parts[2][2])[1]
        indirect = _tlv(blob, content[1])
        digest_info = _kids(blob, indirect[1], indirect[2])[1]
        algorithm, digest = _kids(blob, digest_info[1], digest_info[2])
        algo_oid = _kids(blob, algorithm[1], algorithm[2])[0]
        name = _DIGESTS.get(_oid(blob[algo_oid[1]:algo_oid[2]]))
        if name is None:
            return None
        h = hashlib.new(name)
        for piece in (pe[:checksum], pe[checksum + 4:entry], pe[entry + 8:start], pe[start + size:]):
            h.update(piece)
        if h.digest() != blob[digest[1]:digest[2]]:
            return None
        # the signer's certificate: the one whose serial number the (first) SignerInfo names
        certs = next((p for p in parts if p[0] == 0xA0), None)
        signer = _kids(blob, parts[-1][1], parts[-1][2])[0]
        issuer_serial = _kids(blob, signer[1], signer[2])[1]
        serial = _kids(blob, issuer_serial[1], issuer_serial[2])[1]
        want = blob[serial[1]:serial[2]]
        for _cert, ea, eb in (_kids(blob, certs[1], certs[2]) if certs else []):
            tbs = _kids(blob, ea, eb)[0]
            fields = _kids(blob, tbs[1], tbs[2])
            if fields[0][0] == 0xA0:  # the version
                fields = fields[1:]
            if blob[fields[0][1]:fields[0][2]] == want:  # serial, algorithm, issuer, validity, subject
                return ", ".join(_names(blob, fields[4][1], fields[4][2])) or None
        return None
    except (OSError, IndexError, ValueError, struct.error):
        return None


# --- the check ---

def steam_record(game: Path) -> bool:
    """Steam's own record of this install: steamapps/appmanifest_21970.acf naming this folder."""
    try:
        here = Path(game).resolve()
        acf = here.parent.parent / f"appmanifest_{APP_ID}.acf"
        if here.parent.name.lower() != "common" or not acf.is_file():
            return False
        state = parse_vdf(acf.read_text(encoding="utf-8", errors="replace")).get("appstate", {})
        return str(state.get("installdir", "")).lower() == here.name.lower()
    except (OSError, ValueError):
        return False


def fake_steam_files(game: Path) -> list[str]:
    try:
        here = {p.name.lower(): p.name for p in Path(game).iterdir()}
    except OSError:
        return []
    return [here[n.lower()] for n in FAKE_STEAM_FILES if n.lower() in here]


def check(game: Path, unlocks=(), machine: str | None = None, public: bytes | None = None) -> dict:
    """{"ok", "unlocked", "reasons": ["no_steam_record" | "steam_file" | "fake_steam"], "fake": [names], "code"}.
    `code` (the folder code, in fours) is worked out only when something failed: it reads all of RUSE.exe."""
    game = Path(game)
    reasons, fake = [], fake_steam_files(game)
    if not steam_record(game):
        reasons.append("no_steam_record")
    signer = signed_by(game / STEAM_FILE)
    if signer is None or not any(v in signer for v in VALVE):
        reasons.append("steam_file")
    if fake:
        reasons.append("fake_steam")
    if not reasons:
        return {"ok": True, "unlocked": False, "reasons": [], "fake": [], "code": ""}
    code = folder_code(game, machine)
    unlocked = any(unlock_fits(u, code, public) for u in unlocks)
    return {"ok": unlocked, "unlocked": unlocked, "reasons": reasons, "fake": fake, "code": grouped(code)}


def words(lang: str) -> dict:
    """The box's words in `lang` (rusemod/ownedtext.toml), English where a word isn't translated."""
    with open(_WORDS, "rb") as f:
        table = tomllib.load(f)
    return {key: values.get(lang) or values["us"] for key, values in table.items()}


def ticket_url(code: str, app: str, version: str) -> str:
    """A new unlock ticket on GitHub, the folder code and the app filled in (.github/ISSUE_TEMPLATE/unlock.yml)."""
    fields = {"template": "unlock.yml", "title": f"[Unlock] {code}", "code": code, "app": f"{app} {version}"}
    return f"{TICKET}?{urlencode(fields)}"


class OwnedCalls:
    """The window API's calls for owned copies, for both apps (a mixin beside rusemod.community.CommunityCalls; it
    uses _home, _game, _starter, prefs and _community_open). The check is on once the app's window turns it on
    (use_owned_check, in each app's app.py), so tests that build copies of a made-up game don't meet it."""

    _owned_on = False

    def use_owned_check(self) -> None:
        self._owned_on = True
        self._starter.owned = self._owned_refusal

    def _owned_game(self) -> Path | None:
        game = self._game()
        game = game[0] if isinstance(game, tuple) else game
        return Path(game) if game is not None else None

    def _owned_lang(self) -> str:
        return (self.prefs() or {}).get("lang") or "us"

    def _owned_view(self, game: Path | None) -> dict:
        if not self._owned_on or game is None or not (game / "RUSE.exe").is_file():
            return {"ok": True, "unlocked": False, "reasons": [], "fake": [], "code": ""}
        return check(game, settings(self._home).get("unlocks", []))

    def _owned_refusal(self, game: Path) -> str | None:
        """For rusemod.play.Starter: the message when a modded game mustn't start from `game`, else None."""
        return None if self._owned_view(Path(game))["ok"] else words(self._owned_lang())["refused"]

    def owned_check(self) -> dict:
        """The check for the game folder in use, with the box's words in the player's language."""
        return self._owned_view(self._owned_game()) | {"words": words(self._owned_lang()), "discord": DISCORD}

    def owned_unlock(self, unlock: str) -> dict:
        """Keep an unlock code that fits this PC and game folder, then check again; {"ok": False, "bad_code": True}
        for one that doesn't fit."""
        game = self._owned_game()
        if game is None or not unlock_fits(unlock, folder_code(game)):
            return self.owned_check() | {"ok": False, "bad_code": True}
        values = settings(self._home)
        values["unlocks"] = list(dict.fromkeys([*values.get("unlocks", []), grouped(unlock, 5)]))
        save_settings(self._home, values)
        return self.owned_check()

    def owned_open(self, what: str) -> dict:
        """Open the Discord ("discord"), a GitHub ticket with the folder code ("ticket") or Steam's check of the
        game's files ("steam")."""
        if what == "discord":
            return self._community_open(DISCORD)
        if what == "steam":
            return self._community_open(STEAM_VERIFY)
        if what == "ticket":
            game = self._owned_game()
            code = grouped(folder_code(game)) if game is not None else ""
            return self._community_open(ticket_url(code, self.UPDATE_APP, self.UPDATE_VERSION))
        raise ValueError(f"There's nothing called {what!r} to open")
