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
    """One .dic file: read it, change or add texts, write it back.

    Writing keeps every original text byte where it was (only shifted past the grown table) and appends new or
    changed texts at the end, each followed by a UTF-16 null. An unchanged file writes back byte-identical.
    """

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
        self._table_end = 8 + 16 * count
        self._new: dict[int, str] = {}  # key -> text added or changed since reading

    def text(self, key: int) -> str | None:
        if key in self._new:
            return self._new[key]
        e = self._by_key.get(key)
        return e.text if e else None

    def set_text(self, key: int, text: str) -> None:
        """Change an existing entry's text."""
        if key not in self._by_key and key not in self._new:
            raise KeyError(f"no entry with key {key:#x}; use add()")
        self._new[key] = text

    def add(self, key: int, text: str) -> None:
        """Add a new entry. Keys must be unique."""
        if key in self._by_key or key in self._new:
            raise KeyError(f"key {key:#x} ({key_to_name(key)}) is already used; use set_text()")
        self._new[key] = text

    def to_bytes(self) -> bytes:
        if not self._new:
            return self.raw
        keys = sorted(set(self._by_key) | set(self._new))
        table_end = 8 + 16 * len(keys)
        shift = table_end - self._table_end
        blob = bytearray(self.raw[self._table_end:])  # the original texts, untouched
        table = bytearray()
        for key in keys:
            if key in self._new:
                text = self._new[key]
                off = table_end + len(blob)
                blob += text.encode("utf-16-le") + b"\0\0"
                table += struct.pack("<QII", key, off, len(text.encode("utf-16-le")) // 2)
            else:
                e = self._by_key[key]
                if e.offset < self._table_end:
                    raise ValueError(f"key {key:#x}: text inside the table; can't move it safely")
                table += struct.pack("<QII", key, e.offset + shift, e.length)
        return self.raw[:4] + struct.pack("<I", len(keys)) + bytes(table) + bytes(blob)
