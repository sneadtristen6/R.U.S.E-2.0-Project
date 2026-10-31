"""The game's packs: read and write (lossless). The writer keeps a pack's own list of its files as it is and only lays
the files out again, so an unchanged rebuild gives the same bytes back.

Size (the owner, 2026-10-30: a player's build with many era units' own models stopped at 4 GiB). A pack's header
gives its data length in 8 bytes (at 0x25), but its list gives each member's place in 4 bytes, so a pack laid out the
game's way holds members starting up to 4 GiB into the file (PackTooBig past that). A WIDE pack is for a modded copy
with the "big-packs" game patch (rusemod.gamepatch): its places count in 16-byte steps and have bit 31 set
(WIDE_MARK), its members start on 16-byte steps, and it can hold 32 GiB. With that patch every pack of 2 GiB or more in
the copy has to be a wide one (the game's own ZZ_Win.dat, 2.24 GiB, has 4,725 members past 2 GiB whose plain places
have bit 31 set): build.build_and_write sees to that. This reader takes both kinds: a pack whose every place has bit
31 set is wide (a pack the game ships starts its first member at 0)."""
from __future__ import annotations

import mmap
import struct
from dataclasses import dataclass
from typing import BinaryIO, Iterator

MAGIC = b"edat"
DICT_OFFSET = 0x40D  # constant across every shipped pack
PLAIN_MOST = 0xFFFFFFFF  # the furthest byte of the file a plain pack's member may start at
WIDE_MARK = 0x80000000   # a wide pack's place: 16-byte steps, with this bit set
WIDE_STEP = 16
WIDE_MOST = 0x7FFFFFFF * WIDE_STEP  # the furthest a wide pack's member may start (32 GiB)
MEMBER_MOST = 0xFFFFFFFF  # a member's size, 4 bytes in the list either way


class PackTooBig(ValueError):
    """A pack that can't be laid out: its members come to `size` bytes, past what the layout can hold."""

    def __init__(self, size: int, wide: bool, member: str = ""):
        self.size, self.wide, self.member = size, wide, member
        if member:
            text = f"{member} alone is {size / (1 << 30):.2f} GiB, past the 4 GiB one file in a pack can be"
        else:
            text = (f"the pack's files come to {size / (1 << 30):.2f} GiB, past the "
                    f"{'32 GiB' if wide else '4 GiB'} a pack can hold")
        super().__init__(text)


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
        self.dict_offset, self.dict_len, self.data_offset = struct.unpack_from("<III", raw, 0x19)
        self.data_len = struct.unpack_from("<Q", raw, 0x25)[0]  # 8 bytes, as the game reads it
        self._dict = raw[self.dict_offset:self.dict_offset + self.dict_len]
        self.entries: list[Entry] = []
        self._walk(0, "")
        # a wide pack (ours, past 4 GiB): every position in 16-byte steps with bit 31 set; the game's own start at 0
        self.wide = bool(self.entries) and all(e.offset & WIDE_MARK for e in self.entries)
        if self.wide:
            for e in self.entries:
                e.offset = (e.offset & ~WIDE_MARK) * WIDE_STEP

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
                    add: dict[str, bytes] | None = None, wide: bool = False) -> Iterator[bytes]:
        """Stream the rebuilt archive. `replace` maps a member's path (or a path suffix) -> new member bytes; `add`
        maps the path of a member the archive doesn't have -> its bytes. `wide`: laid out as a wide pack (see the
        module's notes), only for a copy with the "big-packs" game patch.

        Members keep their original storage order (by offset). Unchanged members are copied verbatim, so
        with no replacements the output is byte-identical to the original file. Only one member is held in
        memory at a time, so this works for multi-GB packs. Added members follow LittleGroove's RUSE Mod Manager:
        each goes in front of the dictionary as a top-level entry named by its full path (so the original trie
        stays as it is), and its data after all the others. The layout is checked before anything is yielded:
        PackTooBig when the pack can't hold its members (the first chunk, the header, is never given then).
        """
        replace, add = replace or {}, add or {}
        targets = {}
        for key, blob in replace.items():
            e = self.entry(key) or self.find(key)
            targets[e.dict_pos] = blob
        order = sorted(self.entries, key=lambda e: e.offset)
        names = []
        for path in add:
            if self.entry(path) is not None:
                raise ValueError(f"can't add {path}: the archive already has it")
            name = path.replace("/", "\\").encode("latin-1") + b"\0"
            names.append((name, (17 + len(name)) % 2))  # entries start on even bytes
        front_len = sum(17 + len(name) + pad for name, pad in names)
        data_offset = self.dict_offset + front_len + len(self._dict) if add else self.data_offset

        # Lay out first (sizes only) so the header/dictionary can be written before the data.
        sizes = [(len(targets[e.dict_pos]) if e.dict_pos in targets else e.size, e.path) for e in order]
        sizes += [(len(blob), path) for path, blob in add.items()]
        starts, pads, pos = [], [], 0
        for size, path in sizes:
            if size > MEMBER_MOST:
                raise PackTooBig(size, wide, path)
            pad = -pos % WIDE_STEP if wide else 0
            pos += pad
            starts.append(pos)
            pads.append(pad)
            pos += size
        last = starts[-1] if starts else 0
        if (last > WIDE_MOST) if wide else (data_offset + last > PLAIN_MOST):
            raise PackTooBig(pos, wide)

        def place(at: int) -> int:
            return (at // WIDE_STEP) | WIDE_MARK if wide else at

        new_dict = bytearray(self._dict)
        for e, (size, _p), at in zip(order, sizes, starts):
            struct.pack_into("<II", new_dict, e.dict_pos, place(at), size)
        if not add:
            head = bytearray(self.raw[:self.data_offset])
            head[self.dict_offset:self.dict_offset + self.dict_len] = new_dict
        else:
            front = bytearray()
            for (name, pad), (size, _p), at in zip(names, sizes[len(order):], starts[len(order):]):
                front += struct.pack("<IIIIB", 0, 17 + len(name) + pad, place(at), size, 0) + name + b"\0" * pad
            new_dict = front + new_dict
            head = bytearray(self.raw[:self.dict_offset]) + new_dict
            struct.pack_into("<II", head, 0x1D, len(new_dict), len(head))  # dict_len, data_offset
        struct.pack_into("<Q", head, 0x25, pos)  # data_len: 8 bytes (a pack the game ships has the high 4 at 0)
        yield bytes(head)
        blobs = [targets[e.dict_pos] if e.dict_pos in targets else None for e in order] + list(add.values())
        for k, pad in enumerate(pads):
            if pad:
                yield b"\0" * pad
            blob = blobs[k]
            yield self.read(order[k]) if blob is None else blob

    def to_bytes(self, replace: dict[str, bytes] | None = None, add: dict[str, bytes] | None = None,
                 wide: bool = False) -> bytes:
        """Rebuild the whole archive in memory (fine for small packs; use `write_to` for big ones)."""
        return b"".join(self.iter_chunks(replace, add, wide))

    def write_to(self, out: BinaryIO, replace: dict[str, bytes] | None = None,
                 add: dict[str, bytes] | None = None, wide: bool = False) -> int:
        """Stream the rebuilt archive to an open binary file. Returns bytes written."""
        n = 0
        for chunk in self.iter_chunks(replace, add, wide):
            out.write(chunk)
            n += len(chunk)
        return n

    def laid_out(self, replace: dict[str, bytes] | None = None, add: dict[str, bytes] | None = None,
                 wide: bool = False) -> int:
        """The rebuilt archive's size in bytes, without reading or writing its members (PackTooBig as iter_chunks)."""
        head = next(iter(self.iter_chunks(replace, add, wide)))
        return len(head) + struct.unpack_from("<Q", head, 0x25)[0]
