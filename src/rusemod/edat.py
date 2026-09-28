"""EDAT v1 archive: read and write (lossless).

The container is a header, a trie of path fragments (the "dictionary"), then the raw file data.
See docs/FORMATS.md. The writer keeps the trie bytes intact and only re-lays the data section and
patches each file entry's (offset, size) fields, so an unchanged rebuild is byte-identical to the original.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

MAGIC = b"edat"
DICT_OFFSET = 0x40D  # constant across every shipped pack


@dataclass
class Entry:
    path: str          # full path, backslash-separated
    offset: int        # relative to data_offset
    size: int
    flag: int
    dict_pos: int      # byte position in the dictionary of this entry's u32 offset field (size at +4, flag at +8)


class Edat:
    def __init__(self, raw: bytes):
        if raw[:4] != MAGIC:
            raise ValueError(f"not an EDAT archive: {raw[:4]!r}")
        self.version = struct.unpack_from("<I", raw, 4)[0]
        if self.version != 1:
            raise ValueError(f"unsupported EDAT version {self.version}")
        self.raw = raw
        self.checksum = raw[8:24]
        self.dict_offset, self.dict_len, self.data_offset, self.data_len = struct.unpack_from("<IIII", raw, 0x19)
        self._dict = raw[self.dict_offset:self.dict_offset + self.dict_len]
        self.entries: list[Entry] = []
        self._walk(0, "")

    @classmethod
    def open(cls, path: str) -> "Edat":
        with open(path, "rb") as f:
            return cls(f.read())

    def _cstr(self, pos: int) -> tuple[str, int]:
        end = self._dict.index(b"\0", pos)
        return self._dict[pos:end].decode("latin-1"), end + 1

    def _walk(self, pos: int, prefix: str) -> None:
        d = self._dict
        while True:
            head_len, next_sib = struct.unpack_from("<II", d, pos)
            if head_len == 0:  # file
                offset, size, flag = struct.unpack_from("<IIB", d, pos + 8)
                frag, _ = self._cstr(pos + 17)
                self.entries.append(Entry(prefix + frag, offset, size, flag, pos + 8))
            else:  # directory
                frag, _ = self._cstr(pos + 8)
                self._walk(pos + head_len, prefix + frag)
            if next_sib == 0:
                return
            pos += next_sib

    def find(self, suffix: str) -> Entry:
        suffix = suffix.lower()
        for e in self.entries:
            if e.path.lower().endswith(suffix):
                return e
        raise KeyError(suffix)

    def read(self, entry: Entry) -> bytes:
        start = self.data_offset + entry.offset
        return self.raw[start:start + entry.size]

    def to_bytes(self, replace: dict[str, bytes] | None = None) -> bytes:
        """Rebuild the archive. `replace` maps a path suffix -> new member bytes.

        Members keep their original storage order (by offset). Unchanged members are copied verbatim, so
        with no replacements the result is byte-identical to the original file.
        """
        replace = replace or {}
        targets = {}
        for suffix in replace:
            targets[self.find(suffix).dict_pos] = replace[suffix]

        new_dict = bytearray(self._dict)
        data = bytearray()
        for e in sorted(self.entries, key=lambda e: e.offset):
            blob = targets.get(e.dict_pos)
            if blob is None:
                blob = self.read(e)
            new_off = len(data)
            data += blob
            struct.pack_into("<II", new_dict, e.dict_pos, new_off, len(blob))

        out = bytearray(self.raw[:self.data_offset])
        out[self.dict_offset:self.dict_offset + self.dict_len] = new_dict
        struct.pack_into("<I", out, 0x25, len(data))  # data_len
        out += data
        return bytes(out)
