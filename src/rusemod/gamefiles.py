"""Whole game files changed or added by a mod (MOD_FORMAT §7: LittleGroove's Raw / Asset Editor's Import / Replace
and Add File, brought over the safe way the owner asked for, 2026-10-08):

- A mod never carries a copy of a game file: a changed file is kept as a delta against the game's own file
  (`files/game/<pack>/<path in the pack>.rdelta`: what to copy from the game's file and what's new), made for that one
  file (its SHA-256 is in the delta): when a game update changes the file, the build stops instead of guessing.
- A file the mod adds is its own, only inside the mod's own folder in the pack (`files/game/<pack>/mods/<mod id>/...`),
  so it can't stand in for one of the game's files.
- Every file a build would hand the game is checked first as a file of its kind (CHECKED): a texture opens as a
  texture, a text table as a text table, a font, a Flash menu, the shader file and a video read cleanly to their end
  (rusemod.filechecks). A Flash menu's code stays the game's own; shaders and videos aren't offered yet
  (NOT_YET). A kind that can't be checked, or is a script, or has a tool of its own (sounds: the Music tab), isn't
  taken.
- A file inside a pack inside the pack is reached through it: files/game/ZZ_Win.dat/gen/pack/x.ppk/gen/a.tgv.rdelta.
- Two mods changing one file: the one lower in the load order wins, as for every other change, and the build says
  which (the Launcher shows it before Play, with the way to have the other one's).
- Hard limits for now (the owner, 2026-10-08): FILE_MOST per file, MOD_MOST for all of a mod's game files.
The game folder is never written: the build hands the changes to the modded copy like every other change.
"""
from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from . import filechecks
from .edat import MAGIC as PACK_MAGIC, Edat

MOD_DIR = PurePosixPath("files", "game")
SUFFIX = ".rdelta"
MAGIC = b"RDELTA1\0"
FILE_MOST = 32 * 1024 * 1024   # bytes: the biggest file a mod may change or add (the game's biggest checked kind is a
#                                9 MB texture)
MOD_MOST = 256 * 1024 * 1024   # bytes: all of one mod's changed and added game files (their deltas and new files)
BLOCK = 64                     # bytes: the size of the runs a delta looks for in the game's file

# the kinds of file that are checked before the game gets them (ending -> what it is, for a sentence)
CHECKED = {".tgv": "texture", ".tgv_pc": "texture", ".png": "picture", ".dic": "text table",
           ".gladndfbin": "game data", ".ndfbin": "game data", ".truendfbin": "game data", ".scenario": "scenario",
           ".xml": "XML text", ".ttf": "font", ".otf": "font", ".ttc": "font", ".gfx": "Flash menu",
           ".shc": "shader file", ".webm": "video"}
# checked, but not offered yet (the owner, 2026-10-08: what would need RUSE 2.0's approval isn't included yet; the
# approvals themselves are kept on the feat/approvals branch)
NOT_YET = {".webm": "changing or adding a video isn't offered yet",
           ".shc": "changing the shaders isn't offered yet"}
ELSEWHERE = {".ess": "a sound: change it in the Studio's Music tab, which keeps what the game reads about it in step",
             ".wav": "a sound: change it in the Studio's Music tab"}
NESTED = (".ppk", ".apk", ".mpk", ".gpk", ".spk")  # packs inside a pack, reached through (never replaced whole)


class GameFileError(ValueError):
    """A changed or added game file the build can't take: the message says which and why."""


# --- deltas ---
def make_delta(base: bytes, new: bytes) -> bytes:
    """A delta turning `base` (the game's file) into `new`: the runs of `base` found in `new` (of BLOCK bytes or more)
    are copied, the rest is carried; packed with zlib. Only for `base` (its SHA-256 is in it)."""
    index: dict = {}
    for at in range(0, len(base) - BLOCK + 1, BLOCK):
        index.setdefault(base[at:at + BLOCK], at)
    ops, lit, i, n = [], bytearray(), 0, len(new)
    while i + BLOCK <= n:
        at = index.get(new[i:i + BLOCK])
        if at is None:
            lit.append(new[i])
            i += 1
            continue
        start, length = at, BLOCK  # grow the run forwards, then back into what was about to be carried
        while i + length < n and start + length < len(base) and new[i + length] == base[start + length]:
            length += 1
        while lit and start > 0 and lit[-1] == base[start - 1]:
            lit.pop()
            start, i, length = start - 1, i - 1, length + 1
        if lit:
            ops.append(b"A" + struct.pack("<I", len(lit)) + bytes(lit))
            lit = bytearray()
        ops.append(b"C" + struct.pack("<QI", start, length))
        i += length
    lit += new[i:]
    if lit:
        ops.append(b"A" + struct.pack("<I", len(lit)) + bytes(lit))
    body = zlib.compress(struct.pack("<I", len(ops)) + b"".join(ops), 9)
    return (MAGIC + hashlib.sha256(base).digest() + struct.pack("<Q", len(base)) + hashlib.sha256(new).digest()
            + struct.pack("<Q", len(new)) + body)


def delta_base(delta: bytes) -> str:
    """The SHA-256 (hex) of the game's file a delta was made from."""
    if delta[:8] != MAGIC or len(delta) < 88:
        raise GameFileError("not a delta of a game file")  # not a game rule: our own delta format
    return delta[8:40].hex()


def apply_delta(base: bytes, delta: bytes) -> bytes:
    """`base` changed by `delta`: GameFileError when the delta was made from another file (a game update) or doesn't
    give the file it was made to give."""
    if delta[:8] != MAGIC or len(delta) < 88:
        raise GameFileError("not a delta of a game file")  # not a game rule: our own delta format
    want_base, base_size = delta[8:40], struct.unpack_from("<Q", delta, 40)[0]
    want_new, new_size = delta[48:80], struct.unpack_from("<Q", delta, 80)[0]
    if len(base) != base_size or hashlib.sha256(base).digest() != want_base:
        # not a game rule: a delta fits only the file it was made from (the owner's safeguard 3, 2026-10-08)
        raise GameFileError("it was made from another version of this game file (the game was updated since?): make "
                            "the change again on this version")
    try:
        body = zlib.decompress(delta[88:])
    except zlib.error as exc:
        raise GameFileError(f"its delta is damaged ({exc})") from None
    out, p = bytearray(), 4
    try:
        for _ in range(struct.unpack_from("<I", body, 0)[0]):
            tag = body[p:p + 1]
            if tag == b"C":
                start, length = struct.unpack_from("<QI", body, p + 1)
                if start + length > len(base):
                    # not a game rule: our own delta format
                    raise GameFileError("its delta is damaged (it copies past the game file's end)")
                out += base[start:start + length]
                p += 13
            elif tag == b"A":
                length = struct.unpack_from("<I", body, p + 1)[0]
                out += body[p + 5:p + 5 + length]
                p += 5 + length
            else:
                raise GameFileError("its delta is damaged")
            if len(out) > new_size:
                raise GameFileError("its delta is damaged (it makes a bigger file than it says)")
    except struct.error:
        raise GameFileError("its delta is damaged") from None
    if len(out) != new_size or hashlib.sha256(out).digest() != want_new:
        raise GameFileError("its delta is damaged (it doesn't make the file it was made to)")
    return bytes(out)


# --- what a file must be ---
def taken(path: str) -> str:
    """What a file of this name is ("texture"...) when its kind is taken (CHECKED), else GameFileError saying why."""
    ext = PurePosixPath(path.replace("\\", "/")).suffix.lower()
    if ext in ELSEWHERE:
        raise GameFileError(f"{path} is {ELSEWHERE[ext]}")
    if ext in NOT_YET:
        # not a game rule: the owner, 2026-10-08 (what needs RUSE 2.0's approval isn't included yet)
        raise GameFileError(f"{path}: {NOT_YET[ext]}")
    kind = CHECKED.get(ext)
    if kind is None:
        from .build import NOT_IN_MODS
        why = ("holds code" if ext in NOT_IN_MODS | {".gpk", ".lua"} else "can't be checked by the build yet")
        # not a game rule: what the build can check before the game gets it (owner, 2026-10-08: "in a safe way")
        raise GameFileError(f"{path}: a {ext or 'nameless'} file {why}, so a mod can't change or add it")
    return kind


def check_kind(path: str, data: bytes, base: bytes | None = None) -> str:
    """Check `data` is a good file of the kind its name says (CHECKED): GameFileError saying why when it isn't, or when
    its kind isn't taken. `base` is the game's own file it changes (None for a file a mod adds): a Flash menu's code
    and the shaders must be its (rusemod.filechecks). Returns what it is ("texture"...)."""
    kind = taken(path)
    if len(data) > FILE_MOST:
        # not a game rule: the hard limit for now (the owner, 2026-10-08)
        raise GameFileError(f"{path} is {len(data) // 1_000_000} MB: a mod's game file can be {FILE_MOST // 1_000_000} "
                            f"MB at most for now")
    try:
        if kind == "texture":
            from .packfiles import texture_rgba
            texture_rgba(data, most=64)  # its smallest pictures, decoded
        elif kind == "picture":
            from .png import read_png
            read_png(data)
        elif kind == "text table":
            from .dic import Dic
            Dic(data)
        elif kind == "game data":
            from .ndf import Ndf
            Ndf(data)
        elif kind == "scenario":
            from .scenario import Scenario
            Scenario.read(data)
        elif kind == "XML text":
            import xml.etree.ElementTree as ET
            ET.fromstring(data)
        elif kind == "font":
            filechecks.check_font(data)
        elif kind == "Flash menu":
            filechecks.check_flash(data, base)
        elif kind == "shader file":
            filechecks.check_shaders(data, base)
        elif kind == "video":
            filechecks.check_video(data)
    except filechecks.CheckError as exc:
        # not a game rule: the file doesn't read as its kind, or changes code (the owner's safeguards, 2026-10-08)
        raise GameFileError(f"{path}: {exc}") from None
    except GameFileError:
        raise
    except Exception as exc:  # each reader says what's wrong its own way
        # not a game rule: the file doesn't open as its kind
        raise GameFileError(f"{path} isn't a good {kind} ({type(exc).__name__}: {exc})") from None
    return kind


# --- a mod's game files ---
@dataclass
class GameFile:
    rel: str        # its file in the mod (files/game/...)
    pack: str       # the game's pack it goes in (ZZ_Win.dat, DataMapAlpha_v09.dat...)
    path: str       # its path in the pack, with / (a nested pack's files through it: gen/pack/x.ppk/gen/a.tgv)
    data: bytes     # the delta (a changed file) or the file (an added one)
    added: bool     # added (under mods/<mod id>/), or a change of the game's file


def mod_path(pack: str, path: str, added: bool = False) -> PurePosixPath:
    """Where a mod keeps its change of `path` in game pack `pack` (or its new file there)."""
    clean = path.replace("\\", "/").strip("/")
    return MOD_DIR / pack / (clean if added else clean + SUFFIX)


def read_mod(folder: Path, mod_id: str) -> list[GameFile]:
    """A mod folder's game files (files/game/<pack>/...): changes (.rdelta) and files of its own (under
    mods/<mod id>/ in the pack). GameFileError for one anywhere else, of a kind not taken, or past the limits."""
    root = Path(folder) / MOD_DIR
    out, total = [], 0
    for f in sorted(root.rglob("*")) if root.is_dir() else []:
        if not f.is_file():
            continue
        parts = f.relative_to(root).as_posix().split("/")
        rel = (MOD_DIR / f.relative_to(root).as_posix()).as_posix()
        if len(parts) < 2 or not parts[0].lower().endswith(".dat") or any(p in ("", ".", "..") for p in parts):
            # not a game rule: where our mod format keeps game files
            raise GameFileError(f"{rel}: a game file goes in files/game/<the game's pack>/<its path in the pack>")
        data = f.read_bytes()
        total += len(data)
        if total > MOD_MOST:
            # not a game rule: the hard limit for now (the owner, 2026-10-08)
            raise GameFileError(f"this mod's game files come to more than {MOD_MOST // 1_000_000} MB, the most a mod "
                                f"can carry for now")
        inside = "/".join(parts[1:])
        if f.name.endswith(SUFFIX):
            inside = inside[:-len(SUFFIX)]
            taken(inside)
            delta_base(data)  # (a delta at all)
            out.append(GameFile(rel, parts[0], inside, data, False))
            continue
        own = ["mods", mod_id]
        if [p.lower() for p in parts[1:3]] != own or len(parts) < 4:
            # not a game rule: a mod's new files stay in its own folder in the pack, never standing in for the game's
            raise GameFileError(f"{rel}: a file a mod adds goes in its own folder in the pack, files/game/{parts[0]}/"
                                f"mods/{mod_id}/...; to change one of the game's files, change it in the Studio's "
                                f"Files tab")
        check_kind(inside, data)
        out.append(GameFile(rel, parts[0], inside, data, True))
    return out


def touched(folder: Path) -> dict:
    """The game files a mod folder changes or adds, without reading them: {(pack, path) in lower case: "pack: path"}."""
    root = Path(folder) / MOD_DIR
    out = {}
    for f in sorted(root.rglob("*")) if root.is_dir() else []:
        if f.is_file():
            parts = f.relative_to(root).as_posix().split("/")
            if len(parts) >= 2:
                inside = "/".join(parts[1:])
                inside = inside[:-len(SUFFIX)] if inside.endswith(SUFFIX) else inside
                out[(parts[0].lower(), inside.lower())] = f"{parts[0]}: {inside}"
    return out


def overlaps(mods: list) -> list[dict]:
    """The game files two or more of `mods` ([(name, folder)] in load order) change: [{file, a, b}], `b` the mod
    lowest in the order (its version is used), `a` each of the others (point 7 of the owner's 2026-10-08 list:
    shown before Play, with the way to use `a`'s: put it below `b`)."""
    by: dict = {}
    for name, folder in mods:
        for key, shown in touched(folder).items():
            by.setdefault(key, (shown, []))[1].append(name)
    out = []
    for shown, names in by.values():
        for a in dict.fromkeys(names[:-1]):
            if a != names[-1]:
                out.append({"file": shown, "a": a, "b": names[-1]})
    return out


# --- in a build ---
def _split(arc: Edat, path: str) -> tuple[list[str], str]:
    """(the packs inside `arc` the path goes through, the rest of it), each with \\."""
    parts, nested, at = path.replace("\\", "/").split("/"), [], 0
    for k in range(1, len(parts)):
        head = "\\".join(parts[at:k])
        if head.lower().endswith(NESTED):
            nested.append(head)
            at = k
    return nested, "\\".join(parts[at:])


def changes(open_pack, find_pack, mods: list, say=print) -> tuple[dict, list]:
    """The game files `mods` change or add ([(mod id, [GameFile])] in load order), put into the packs `open_pack(path)`
    gives (rmod.Layered: what they read is what later steps read, so value patches go on top of a changed file).
    Returns ({pack path: Layered}, [(level, message)]): a later mod's version of a file wins, with a warning naming
    both; a file the game hasn't got, a delta made from another version of it, or a result that isn't a good file of
    its kind is an error."""
    said, touched, by = [], {}, {}
    for mod_id, files in mods:
        for g in files:
            key = (g.pack.lower(), g.path.lower())
            if key in by and by[key] != mod_id:
                said.append(("warning", f"{by[key]} and {mod_id} both change {g.pack}: {g.path}; {mod_id}'s is used "
                                        f"(it's lower in the load order). To use {by[key]}'s, put {by[key]} below "
                                        f"{mod_id}"))
            by[key] = mod_id
    final = {}
    for mod_id, files in mods:
        for g in files:
            final[(g.pack.lower(), g.path.lower())] = (mod_id, g)  # the lowest mod's wins
    for (_pack, _path), (mod_id, g) in final.items():
        where = f"{mod_id}: {g.rel}"
        path = find_pack(g.pack)
        if path is None:
            # not a game rule: the game or one of its files isn't found
            said.append(("error", f"{where}: the game has no pack {g.pack}"))
            continue
        top = open_pack(path)
        touched[path] = top
        try:
            nested, inner = _split(top, g.path)
            chain = [top]
            for name in nested:  # the packs it goes through, as they are now (changes included)
                e = chain[-1].entry(name)
                raw = bytes(chain[-1].read(e)) if e is not None else None
                if raw is None or raw[:4] != PACK_MAGIC:
                    # not a game rule: the pack the mod's file goes through isn't in the game
                    raise GameFileError(f"the game has no pack {name} in {g.pack}")
                chain.append(Edat(raw))
            arc = chain[-1]
            e = arc.entry(inner)
            if g.added:
                if e is not None:
                    # not a game rule: an added file never stands in for one already there
                    raise GameFileError(f"the game already has {inner}")
                new, base = g.data, None
            else:
                if e is None:
                    # not a game rule: the file the mod changes isn't in the game
                    raise GameFileError(f"the game has no {inner} in {g.pack}")
                base = bytes(arc.read(e))
                new = apply_delta(base, g.data)
            check_kind(inner, new, base)
            # put it in, then each pack it went through back into the one before
            data, member, added = new, inner, g.added
            for parent, name in zip(reversed(chain[:-1]), reversed(nested)):
                inner_arc = chain[chain.index(parent) + 1]
                data = inner_arc.to_bytes(add={member: data}) if added else inner_arc.to_bytes(replace={member: data})
                member, added = name, False
            if added:
                top.add(member, data)
            else:
                top.replace(member, data)
        except GameFileError as exc:
            said.append(("error", f"{where}: {exc}"))
            continue
        say(f"game file: {g.pack}: {g.path} ({'added' if g.added else 'changed'}, from {mod_id})")
    return touched, said
