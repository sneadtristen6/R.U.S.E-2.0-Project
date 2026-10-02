"""Fingerprints and join codes (docs/MOD_FORMAT.md §10.8 and §12).

- The fingerprint is the same on two PCs exactly when their gameplay content is the same: SHA-256 over the Steam build
  id and every gameplay file the mod set changes, adds or deletes (NDF hashed uncompressed). Shown as `K7Q2-M9XD`.
- A join code names the game build, the mods and their exact versions, and the fingerprint:
  `RUSE1:` + Crockford base32, with a CRC-32 that catches typos and cut-off pastes. No server needed.
"""
from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass

from .ndf import decode

_B32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford: no I, L, O, U
_B32_READ = {c: i for i, c in enumerate(_B32)} | {"I": 1, "L": 1, "O": 0}
PREFIX = "RUSE1:"

_NDF_EXT = (".ndfbin", ".gladndfbin", ".truendfbin")
_GAMEPLAY_EXT = _NDF_EXT + (".scenario", ".win", ".kdt", ".boobspc", ".sdb", ".xyz", ".ipk")
_COSMETIC_EXT = (".tgv", ".tgv_pc", ".spk", ".spkpc", ".apk", ".baf", ".ess", ".webm", ".ttf", ".ttc", ".gpk", ".dic",
                 ".ppk", ".mpk")


class CodeError(ValueError):
    """A join code that can't be read; the message is meant for players."""


# --- gameplay or cosmetic (MOD_FORMAT §10.8) ---
def game_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def is_gameplay(path: str) -> bool:
    """Cautious on purpose: map packs and anything unknown count as gameplay."""
    p = game_path(path)
    if p.startswith("maps/") or p.endswith(_GAMEPLAY_EXT):
        return True
    return not p.endswith(_COSMETIC_EXT)


def canonical(path: str, data: bytes) -> bytes:
    """NDF files are compared uncompressed, with the header's "compressed" flag cleared, so compression can't change
    the fingerprint."""
    if game_path(path).endswith(_NDF_EXT) and data[:4] == b"EUG0":
        logical = bytearray(decode(data))
        struct.pack_into("<I", logical, 12, struct.unpack_from("<I", logical, 12)[0] & ~0x80)
        return bytes(logical)
    return data


# --- fingerprint (MOD_FORMAT §12) ---
def fingerprint(build_id: str, changed: dict[str, bytes | None]) -> bytes:
    """`changed`: game path -> the file's new bytes, or None if the mod set deletes it. Only gameplay files count;
    leave out files whose content ends up identical to the game's own."""
    h = hashlib.sha256()
    h.update(b"RUSEFP1\n" + str(build_id).encode() + b"\n")
    for path in sorted(game_path(p) for p in changed):
        if not is_gameplay(path):
            continue
        data = next(v for k, v in changed.items() if game_path(k) == path)
        digest = b"deleted" if data is None else hashlib.sha256(canonical(path, data)).hexdigest().encode()
        h.update(path.encode("utf-8") + b"\n" + digest + b"\n")
    return h.digest()


def fingerprint_text(fp: bytes) -> str:
    """The 8 characters people compare: `K7Q2-M9XD`."""
    s = _b32encode(fp[:5])
    return f"{s[:4]}-{s[4:8]}"


# --- join codes (MOD_FORMAT §12) ---
@dataclass
class JoinCode:
    build_id: int
    fingerprint: bytes              # the first 10 bytes
    mods: list                      # [(id, "major.minor.patch")]

    def matches(self, fp: bytes) -> bool:
        return fp[:10] == self.fingerprint


def encode_join_code(build_id, fp: bytes, mods) -> str:
    body = bytearray([1]) + struct.pack(">I", int(build_id)) + fp[:10]
    if len(mods) > 255:
        raise ValueError("a join code holds at most 255 mods")
    body.append(len(mods))
    for mod_id, version in mods:
        raw = mod_id.encode("ascii")
        parts = [int(x) for x in version.split(".")] + [0, 0]
        if len(raw) > 255 or not all(0 <= x <= 255 for x in parts[:3]):
            raise ValueError(f"{mod_id} {version} doesn't fit in a join code")
        body += bytes([len(raw)]) + raw + bytes(parts[:3])
    body += struct.pack(">I", zlib.crc32(body))
    return PREFIX + _b32encode(bytes(body))


def decode_join_code(code: str) -> JoinCode:
    text = "".join(code.split()).upper()
    if not (text[:4] == "RUSE" and text[4:5] in ("1", "L", "I") and text[5:6] == ":"):
        # not a game rule: a text the player pasted
        raise CodeError("That isn't a R.U.S.E. join code (they start with RUSE1:).")
    body = text[len(PREFIX):].replace("-", "")
    if any(c not in _B32_READ for c in body):
        raise CodeError("This join code has characters that don't belong in it. Copy it again.")
    data = _b32decode(body)
    if len(data) < 20 or zlib.crc32(data[:-4]) != struct.unpack(">I", data[-4:])[0]:
        raise CodeError("This join code is damaged or cut off. Ask your friend to send it again.")
    if data[0] != 1:
        raise CodeError("This join code is from a newer launcher. Update the launcher and try again.")
    build_id = struct.unpack(">I", data[1:5])[0]
    fp, count, pos, mods = data[5:15], data[15], 16, []
    for _ in range(count):
        n = data[pos]
        mod_id = data[pos + 1:pos + 1 + n].decode("ascii")
        major, minor, patch = data[pos + 1 + n:pos + 4 + n]
        mods.append((mod_id, f"{major}.{minor}.{patch}"))
        pos += 4 + n
    return JoinCode(build_id, fp, mods)


def _b32encode(data: bytes) -> str:
    n, bits = int.from_bytes(data, "big"), len(data) * 8
    pad = -bits % 5
    n <<= pad
    return "".join(_B32[(n >> s) & 31] for s in range(bits + pad - 5, -1, -5))


def _b32decode(text: str) -> bytes:
    n = 0
    for c in text:
        if c not in _B32_READ:
            raise ValueError(c)
        n = (n << 5) | _B32_READ[c]
    bits = len(text) * 5
    size, pad = bits // 8, bits % 8  # leftover bits of a cut-off code are dropped; the CRC then catches it
    return (n >> pad).to_bytes(size, "big")
