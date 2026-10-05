"""Answers worked out once, for everyone who loads the mod after (docs/MOD_FORMAT.md: `solved.bin`).

A big map mod asks the build some long questions whose answers are our own numbers, not the game's files: where the
movement circles of a drained sea go, which ground comes back round new water. The modder's build works them out
(minutes, on a map changed all over); kept in the mod, a player's build takes them from there. The owner
(2026-10-04): the long build is fine for the modder, the players "just download the map directly and then load it up",
and "we shouldn't be shipping game file changes".

So nothing kept here is a game file or a piece of one. An answer is named by a fingerprint of everything it was
worked out from (`name`: the question's own numbers, among them the game's as the build has them, which the
fingerprint doesn't give back) and holds plain numbers and text only. A build asks with the same inputs or it gets
no answer and works it out: an answer can't be laid on another map, another version of the game or another set of
mods. What a build takes from here it still checks as its own (the callers' `check`).

In a file the answers are locked with a key made from the game's own file for that map (`pack` / `unpack`: the
map's movement file as shipped): without the game the file is noise, the key is in no code of ours, and a file
changed by someone without the game is refused. The owner: "I don't want to give away Eugene's stuff, so I want to
protect their code with an encryption." It doesn't hide the numbers from someone who has the game: his copy must
read them. Made from hashlib alone: BLAKE2b as the stream (a counter under a key) and as the seal over the locked
bytes.

RUSE Guard (rusemod.guard, the fair play side; the owner, 2026-10-04: "at the very least, have it informed, because
that is part of our anti-cheat") knows this file as one of the mod's files: a signed mod manifest lists it with its
hash like every other file of the mod folder, so a changed file of answers fails the manifest. And answers can't
tilt a match quietly: a build weighs every answer it takes; answers that pass and still differ give another movement
file, so another fingerprint and another join code than everyone else's."""
from __future__ import annotations

import hashlib
import hmac
import io
import pickle
import re
import struct
import zlib
from pathlib import Path

MAGIC = b"RUSE-SOLVED-1\n"
FILE = "solved.bin"       # in a mod: maps/<map pack>/solved.bin
LIMIT = 50_000_000        # the most a file of answers may weigh (the owner's most extreme map: 115 KB)
_MAP = re.compile(r"^[A-Za-z0-9_]+$")
_ACTIVE: list = []  # the answers in use (the innermost `using`)


class SolvedError(ValueError):
    """A file of answers that can't be read: not one, cut short, changed, or locked with another game file."""


def name(kind: str, *parts) -> bytes:
    """An answer's name: a fingerprint of the kind of question and everything it is asked with (`parts`: numbers,
    text, bytes, lists and tuples of them; a float's repr gives it back to the last bit)."""
    h = hashlib.blake2b(digest_size=20, person=b"ruse-solved")
    h.update(kind.encode("utf-8") + b"\0")
    for part in parts:
        raw = part if isinstance(part, (bytes, bytearray)) else repr(part).encode("utf-8", "surrogatepass")
        h.update(struct.pack("<Q", len(raw)))
        h.update(raw)
    return h.digest()


class Solved:
    """Answers by name. `given`: the ones a mod came with; `used`: the given ones a build took; `found`: the ones this
    build worked out; `taken` counts the given ones used."""

    def __init__(self, given: dict | None = None):
        self.given = dict(given or {})
        self.used: dict = {}
        self.found: dict = {}
        self.taken = 0

    def every(self) -> dict:
        return {**self.given, **self.found}

    def needed(self) -> dict:
        """What this build asked for: the answers an export carries (a given answer nothing asked for is left out)."""
        return {**self.used, **self.found}


class using:
    """`with solved.using(store):` the answers `answer` takes from and adds to, inside."""

    def __init__(self, store: Solved | None):
        self.store = store

    def __enter__(self):
        _ACTIVE.append(self.store)
        return self.store

    def __exit__(self, *exc):
        _ACTIVE.pop()


def answer(key: bytes, work, check=None):
    """The answer named `key`: the one in use when there is one and `check(answer)` takes it (the caller's own test:
    an answer from a file is never trusted as it is), else `work()`'s, which is kept for the export."""
    store = _ACTIVE[-1] if _ACTIVE else None
    if store is not None:
        got = store.given.get(key)
        if got is None:
            got = store.found.get(key)
        elif check is not None:
            try:
                if not check(got):
                    got = None
            except Exception:  # noqa: BLE001 - an answer its own check chokes on is no answer
                got = None
            if got is not None:
                store.taken += 1
                store.used[key] = got
        else:
            store.taken += 1
            store.used[key] = got
        if got is not None:
            return got
    got = work()
    if store is not None:
        store.found[key] = got
    return got


def drop(key: bytes) -> None:
    """Forget the answer named `key` (one that passed its check and still didn't hold: worked out afresh next)."""
    store = _ACTIVE[-1] if _ACTIVE else None
    if store is not None:
        store.given.pop(key, None)
        store.used.pop(key, None)
        store.found.pop(key, None)


def digest(answers: dict) -> str:
    """A fingerprint of a set of answers (for the name of something worked out with them)."""
    h = hashlib.blake2b(digest_size=20, person=b"ruse-solved-set")
    for key in sorted(answers):
        h.update(key)
        h.update(repr(answers[key]).encode("utf-8", "surrogatepass"))
    return h.hexdigest()


def read_mod(folder) -> dict:
    """{map pack name: the bytes of maps/<map pack>/solved.bin} of a mod folder (locked as they are: a build opens
    them with the game's own file). A file too big to be one is left out."""
    maps = Path(folder) / "maps"
    out = {}
    for f in sorted(maps.glob(f"*/{FILE}")) if maps.is_dir() else []:
        if _MAP.match(f.parent.name) and f.is_file() and f.stat().st_size <= LIMIT:
            out[f.parent.name] = f.read_bytes()
    return out


def write_mod(folder, files: dict) -> list:
    """Write {map pack name: a file's bytes} into a mod folder as maps/<map pack>/solved.bin (the modder's export);
    the files written."""
    out = []
    for name, data in sorted(files.items()):
        if not _MAP.match(name):
            continue
        target = Path(folder) / "maps" / name / FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        out.append(target)
    return out


class _Plain(pickle.Unpickler):
    """Reads back plain values only (numbers, text, bytes, lists, tuples, dicts): nothing a file names is looked up."""

    def find_class(self, module, name):
        raise pickle.UnpicklingError(f"answers hold plain values, not {module}.{name}")


def _keys(game_file: bytes, nonce: bytes) -> tuple[bytes, bytes]:
    seed = hashlib.blake2b(game_file, digest_size=32, person=b"ruse-solved-key").digest()
    return (hashlib.blake2b(seed + nonce, digest_size=32, person=b"ruse-solved-enc").digest(),
            hashlib.blake2b(seed + nonce, digest_size=32, person=b"ruse-solved-mac").digest())


def _stream(key: bytes, data: bytes) -> bytes:
    """`data` under the key's stream (the same call locks and unlocks): BLAKE2b of a counter, 64 bytes a block."""
    blocks = (len(data) + 63) // 64
    pad = b"".join(hashlib.blake2b(struct.pack("<Q", i), key=key, digest_size=64).digest() for i in range(blocks))
    return (int.from_bytes(data, "little") ^ int.from_bytes(pad[:len(data)], "little")).to_bytes(len(data), "little")


def pack(answers: dict, game_file: bytes, about: str = "") -> bytes:
    """A file's bytes for `answers` ({name: plain value}), locked with `game_file` (the game's own file the answers
    go with, as shipped: its bytes make the key). `about`: a line anyone can read (the map's name)."""
    for key in answers:
        if not isinstance(key, bytes):
            raise SolvedError("an answer's name is its fingerprint")
    try:
        plain = zlib.compress(pickle.dumps(dict(sorted(answers.items())), protocol=4), 6)
        _Plain(io.BytesIO(zlib.decompress(plain))).load()  # (what can't be read back plainly is refused now)
    except Exception as exc:  # noqa: BLE001 - anything but plain values can't be an answer
        raise SolvedError(f"an answer holds something that isn't a plain value ({type(exc).__name__})") from None
    # the lock's own number comes from what is locked and the game file (no clock, no dice): the same answers give
    # the same file every time, so an export of an unchanged mod is the same package, and other answers another lock
    nonce = hashlib.blake2b(plain, key=hashlib.blake2b(bytes(game_file), digest_size=32).digest(), digest_size=16,
                            person=b"ruse-solved-non").digest()
    k_enc, k_mac = _keys(bytes(game_file), nonce)
    told = about.encode("utf-8")
    head = MAGIC + struct.pack("<H", len(told)) + told + nonce
    locked = _stream(k_enc, plain)
    seal = hashlib.blake2b(head + locked, key=k_mac, digest_size=32).digest()
    return head + struct.pack("<Q", len(locked)) + locked + seal


def about(data: bytes) -> str:
    """The readable line of a file of answers (no key needed)."""
    if not data.startswith(MAGIC) or len(data) < len(MAGIC) + 2:
        raise SolvedError("not a file of answers")
    n = struct.unpack_from("<H", data, len(MAGIC))[0]
    return bytes(data[len(MAGIC) + 2:len(MAGIC) + 2 + n]).decode("utf-8", "replace")


def unpack(data: bytes, game_file: bytes) -> dict:
    """The answers in a file, unlocked with the game's own file. SolvedError when it isn't such a file, was changed,
    or was locked with another file (another version of the game)."""
    data = bytes(data)
    if not data.startswith(MAGIC):
        raise SolvedError("not a file of answers")
    try:
        at = len(MAGIC)
        n = struct.unpack_from("<H", data, at)[0]
        at += 2 + n
        nonce = data[at:at + 16]
        at += 16
        size = struct.unpack_from("<Q", data, at)[0]
        at += 8
        locked, seal = data[at:at + size], data[at + size:at + size + 32]
        if len(nonce) != 16 or len(locked) != size or len(seal) != 32 or len(data) != at + size + 32:
            raise SolvedError("the file of answers is cut short")
    except struct.error:
        raise SolvedError("the file of answers is cut short") from None
    k_enc, k_mac = _keys(bytes(game_file), nonce)
    want = hashlib.blake2b(data[:len(MAGIC) + 2 + n + 16] + locked, key=k_mac, digest_size=32).digest()
    if not hmac.compare_digest(want, seal):
        raise SolvedError("the answers don't open with this game file: they were made with another version of the "
                          "game, or the file was changed")
    try:
        got = _Plain(io.BytesIO(zlib.decompress(_stream(k_enc, locked)))).load()
    except Exception as exc:  # noqa: BLE001 - whatever is wrong inside, it is no file of answers
        raise SolvedError(f"the answers can't be read ({type(exc).__name__})") from None
    if not isinstance(got, dict) or not all(isinstance(k, bytes) for k in got):
        raise SolvedError("the answers aren't a set of named answers")
    return got
