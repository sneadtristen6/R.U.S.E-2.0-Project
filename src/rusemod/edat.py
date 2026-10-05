"""The game's packs: read and write (lossless). The writer keeps a pack's own list of its files as it is and only lays
the files out again, so an unchanged rebuild gives the same bytes back."""
from __future__ import annotations

import mmap
import struct
from dataclasses import dataclass
from typing import BinaryIO, Iterator

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
    """An EDAT archive over `raw`: bytes (small/nested archives) or a read-only mmap (files; see `open`)."""

    def __init__(self, raw: bytes | mmap.mmap):
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
        """Memory-map the file read-only: members are read on demand, so multi-GB packs cost no RAM up front."""
        f = open(path, "rb")
        try:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        except Exception:
            f.close()
            raise
        arc = cls(mm)
        arc._file = f
        return arc

    def close(self) -> None:
        if isinstance(self.raw, mmap.mmap):
            self.raw.close()
        f = getattr(self, "_file", None)
        if f is not None:
            f.close()

    def __enter__(self) -> "Edat":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _cstr(self, pos: int) -> tuple[str, int]:
        end = self._dict.index(b"\0", pos)
        return self._dict[pos:end].decode("latin-1"), end + 1

    def _walk(self, pos: int, prefix: str) -> None:
        d = self._dict
        while True:
            if pos + 8 > len(d):  # empty directory (e.g. an archive with no files): nothing below it
                return
            head_len, next_sib = struct.unpack_from("<II", d, pos)
            if head_len == 0:  # file
                offset, size, flag = struct.unpack_from("<IIB", d, pos + 8)
                frag, _ = self._cstr(pos + 17)
                self.entries.append(Entry(prefix + frag, offset, size, flag, pos + 8))
            else:  # directory
                frag, frag_end = self._cstr(pos + 8)
                # A header shorter than its own name means "no children" (empty archives use head_len = 1).
                if head_len >= frag_end - pos:
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

    def entry(self, path: str) -> Entry | None:
        """The member at exactly `path` (either slash, any case), or None."""
        key = path.replace("/", "\\").lower()
        if not hasattr(self, "_by_path"):
            self._by_path = {e.path.lower(): e for e in self.entries}
        return self._by_path.get(key)

    def iter_chunks(self, replace: dict[str, bytes] | None = None,
                    add: dict[str, bytes] | None = None) -> Iterator[bytes]:
        """Stream the rebuilt archive. `replace` maps a member's path (or a path suffix) -> new member bytes; `add`
        maps the path of a member the archive doesn't have -> its bytes.

        Members keep their original storage order (by offset). Unchanged members are copied verbatim, so
        with no replacements the output is byte-identical to the original file. Only one member is held in
        memory at a time, so this works for multi-GB packs. Added members follow LittleGroove's RUSE Mod Manager:
        each goes in front of the dictionary as a top-level entry named by its full path (so the original trie
        stays as it is), and its data after all the others.
        """
        replace, add = replace or {}, add or {}
        targets = {}
        for key, blob in replace.items():
            e = self.entry(key) or self.find(key)
            targets[e.dict_pos] = blob
        order = sorted(self.entries, key=lambda e: e.offset)

        # Lay out first (sizes only) so the header/dictionary can be written before the data.
        new_dict = bytearray(self._dict)
        pos = 0
        for e in order:
            size = len(targets[e.dict_pos]) if e.dict_pos in targets else e.size
            struct.pack_into("<II", new_dict, e.dict_pos, pos, size)
            pos += size

        if not add:
            head = bytearray(self.raw[:self.data_offset])
            head[self.dict_offset:self.dict_offset + self.dict_len] = new_dict
        else:
            front = bytearray()
            for path, blob in add.items():
                if self.entry(path) is not None:
                    raise ValueError(f"can't add {path}: the archive already has it")
                name = path.replace("/", "\\").encode("latin-1") + b"\0"
                size = 17 + len(name)
                pad = size % 2  # entries start on even bytes
                front += struct.pack("<IIIIB", 0, size + pad, pos, len(blob), 0) + name + b"\0" * pad
                pos += len(blob)
            new_dict = front + new_dict
            head = bytearray(self.raw[:self.dict_offset]) + new_dict
            struct.pack_into("<II", head, 0x1D, len(new_dict), len(head))  # dict_len, data_offset
        struct.pack_into("<I", head, 0x25, pos)  # data_len
        yield bytes(head)
        for e in order:
            yield targets[e.dict_pos] if e.dict_pos in targets else self.read(e)
        yield from add.values()

    def to_bytes(self, replace: dict[str, bytes] | None = None, add: dict[str, bytes] | None = None) -> bytes:
        """Rebuild the whole archive in memory (fine for small packs; use `write_to` for big ones)."""
        return b"".join(self.iter_chunks(replace, add))

    def write_to(self, out: BinaryIO, replace: dict[str, bytes] | None = None,
                 add: dict[str, bytes] | None = None) -> int:
        """Stream the rebuilt archive to an open binary file. Returns bytes written."""
        n = 0
        for chunk in self.iter_chunks(replace, add):
            out.write(chunk)
            n += len(chunk)
        return n
