"""Localisation tables (.dic, magic 'TRA'): reading, and the text-key codec. See docs/FORMATS.md §4.

Layout: b"TRA" + u8 version, u32 count, then count x (u64 key, u32 byte offset, u32 length in UTF-16 characters)
sorted by key, then the UTF-16LE texts. Offsets count from the start of the file, and several entries can share one
text. (Offsets and sharing as reported by RUSE-Mod-Manager's notes; `tools/dic_check.py` verifies them on the game.)

Keys are not hashes: like Wargame's (moddingSuite `Utils.CreateLocalisationHash`, MIT), a key packs a name of up to
8 characters, 6 bits each (0-9, A-Z, _, a-z). R.U.S.E.'s multiplayer map-name keys decode to M_D_01 .. M_D_30.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"  # codes 1..63; 0 is never used


def key_to_name(key: int) -> str | None:
    """The name a text key was made from, or None if the key isn't a packed name."""
    out = []
    while key:
        code = key & 63
        if code == 0:
            return None
        out.append(_CHARS[code - 1])
        key >>= 6
    return "".join(reversed(out)) or None


def name_to_key(name: str) -> int:
    """Pack a name (1-8 characters of 0-9, A-Z, _, a-z) into a text key, the way the game's keys are made."""
    if not 1 <= len(name) <= 8 or any(c not in _CHARS for c in name):
        raise ValueError(f"not a valid text-key name: {name!r} (1-8 characters of 0-9 A-Z _ a-z)")
    key = 0
    for c in name:
        key = (key << 6) | (_CHARS.index(c) + 1)
    return key


@dataclass
class DicEntry:
    key: int      # the 64-bit key NDF values of type 0x1D refer to
    offset: int   # byte offset of the text from the start of the file
    length: int   # length in UTF-16 characters
    text: str

    @property
    def name(self) -> str | None:
        return key_to_name(self.key)


class Dic:
    """A read-only view of one .dic file."""

    def __init__(self, raw: bytes):
        if raw[:3] != b"TRA":
            raise ValueError(f"not a .dic (TRA) file: {raw[:4]!r}")
        self.raw = raw
        self.version = raw[3]
        count = struct.unpack_from("<I", raw, 4)[0]
        if 8 + 16 * count > len(raw):
            raise ValueError(f".dic claims {count} entries but is only {len(raw)} bytes")
        self.entries: list[DicEntry] = []
        for i in range(count):
            key, off, n = struct.unpack_from("<QII", raw, 8 + 16 * i)
            if off + 2 * n > len(raw):
                raise ValueError(f"entry {i}: text at {off} (+{2 * n} bytes) runs past the end of the file")
            self.entries.append(DicEntry(key, off, n, raw[off:off + 2 * n].decode("utf-16-le", "replace")))
        self._by_key = {e.key: e for e in self.entries}

    def text(self, key: int) -> str | None:
        e = self._by_key.get(key)
        return e.text if e else None
