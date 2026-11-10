"""Fair play in multiplayer (PLAN.md §14, MOD_FORMAT.md §12): our apps are never the cheat tool for a match against
other people, and players who don't cheat can show it.

- A modded copy is a CHEAT COPY (`offline` in the code and the record, its first name) when one of its mods is a
  cheat or a test tool: tagged "cheat" (the mod list's tag, kept next to a mod installed from it in TAGS_FILE, or the
  mod's own `[mod] tags`), or a .rmod whose game scripts call one of the game's cheat orders (CHEAT_CALLS: money,
  units or kills out of nowhere, the developer menu). The build adds our lock to such a copy
  (gamescripts/fairplay_lock.py25) with the copy's build code in it (`build_code`, `lock_script`). In a multiplayer
  or co-op match the lock announces that code to every player's game and looks at what the others announced: every
  human player has the same code = the match goes on (GitHub issue 24, the owner 2026-11-10: players who all have
  the same game play together, cheats or not); anyone missing or different = it says so on screen and gives the
  match up a few seconds in, as it did for every such match before. The leaving passed in the game (the 10-30/31
  multiplayer tests); the same-build match is NOT TESTED in the game yet (docs/TESTS.md F5).
- Every copy gets a join code (rusemod.lock): the game build, the mods and their versions, the fingerprint.
  Two players with the same code have the same game; a different code says what differs (`compare`). A cheat copy
  has one too, so the players of a same-build match can compare before they start.
- The build leaves a record in the copy (RECORD): the code, the mods, and the size, time and SHA-256 of every file
  it wrote. `check_copy` finds a copy changed since (a pack swapped or edited, a file added to the game's data); the
  Launcher then shows no code.
- The watcher (gamescripts/fairplay_watch.py25) is in every modded copy: it says on screen when a match sees a
  cheat order, a unit made by a spawn order or a side's money jumping by 400 or more at once. It changes nothing in
  the match. NOT TESTED in the game yet (docs/TESTS.md F3).

The honest limit: all of this runs on the player's own PC. It keeps our tools from being how anyone cheats, and gives
honest players a way to show their game is the same; it can't stop someone who edits their game by hand.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import pyscript
from .lock import CodeError, decode_join_code, encode_join_code, fingerprint_text
from .mod_index import CHEAT_TAG

TAGS_FILE = "tags.toml"     # next to a mod installed from the mod list: the list's tags for it
RECORD = "fairplay.json"    # in a modded copy: what the build made (write_record)
SCRIPTS = Path(__file__).with_name("gamescripts")
LOCK, WATCH = "fairplay_lock", "fairplay_watch"
BUILD_CODE_DIGITS = 13                    # a cheat copy's build code: this many hex digits (52 bits), in its lock
NO_BUILD_CODE = "0" * BUILD_CODE_DIGITS   # a lock with no build code: it matches no copy, so it leaves every match
_CODE_NAME = b"_fairplay_lock_code"       # the name the lock's source sets its build code to (fairplay_lock.py25)
LOCK_FIRST, LOCK_VERSION = 0x40000000, 1  # the lock's announcement: its numbers' start and its version (lock_numbers)
GUARD = "guard_hash"  # RUSE Guard's in-game record (DomesticNukes' §3.2/§3.4; multiplayer only; rusemod.guard)
# FAIR PLAY IS SWITCHED ON for the release (the owner, 2026-10-31: "this is going out", after the 10-30/31
# multiplayer tests with a real opponent). Written on 2026-10-04 and held off until then (docs/BIG_PATCH.md).
# Off, the build checks no mods, adds no scripts and leaves no record; the Launcher shows no join code, no badges,
# no trust tick, and Play doesn't wait for one. Tests that need it off patch this line.
ON = True
# Our game scripts go into every build: the lock passed in the game (the 10-30/31 multiplayer tests: it surrendered
# a cheat copy and stopped it on the end-of-match screen), and the watcher and the record let no error out at any
# of the game's nine calls (checked with failing game objects at each). Off, no scripts go in; a test copy passes
# `FairPlay(scripts=...)` itself.
IN_BUILDS = True
MAP_SCRIPTS = "IA_Common.dat"         # the pack with the maps' own match scripts: ours go there (1.5 MB)
SCRIPT_ROOT = "genpython\\1000\\test\\"  # where a scenario's DataDir:\Test\... script folder is in that pack
MULTIPLAYER = "\\effetmapmultiplayer.xyz"  # the game's own multiplayer match script (ZZ_Win.dat, eugenpatchable.ipk)
SCENARIOS = "genglad\\patchable\\scenario\\"  # the scenario clusters (ZZ_GladPatchableWin.dat) naming the folders
GAMEPLAY_DIRS = ("data", "maps")      # the copy's folders the game's packs are in
# a scenario's script folder, as its cluster names it: DataDir:\Test\map\<map>\Scripting<...>
_FOLDER = re.compile(r"(?i)datadir:\\test\\(map\\[a-z0-9_]+\\scripting[a-z0-9_]*)")

# The game's cheat orders, as a mod's game scripts name them, and what each does. Orders run on every player's PC,
# so a script sending them changes everyone's match; the game's own scripts only send AddMaterial from the developer
# menu and never send SpawnUnit. (Playing a ruse card, Send_ChooseBluffCard, isn't here: every player uses it.)
CHEAT_CALLS = {
    b"Send_AddMaterial": "adds money",
    b"TNetworkActionAddMaterial": "adds money",
    b"Send_SpawnUnit": "makes units out of nowhere",
    b"TNetworkActionSpawnUnit": "makes units out of nowhere",
    b"TNetworkActionKill": "kills units",
    b"toggle_show_dev_buttons": "opens the game's developer menu",
    b"BoutonTransvaseRessource": "uses the developer menu's money buttons",
}


class FairPlayError(Exception):
    """A problem the player can act on; the message says what to do next."""


# --- what a mod is ---
def read_tags(folder) -> list[str]:
    """A mod folder's tags: its own `[mod] tags` and the mod list's (TAGS_FILE), in lowercase."""
    folder, tags = Path(folder), []
    for file, key in ((folder / "mod.toml", "mod"), (folder / TAGS_FILE, None)):
        try:
            data = tomllib.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        found = (data.get(key, {}) if key else data).get("tags", [])
        tags += [found] if isinstance(found, str) else [t for t in found if isinstance(t, str)]
    return sorted({t.strip().lower() for t in tags if t.strip()})


def save_tags(folder, tags) -> None:
    """Keep the mod list's tags next to a mod installed from it (read_tags reads them back)."""
    words = sorted({str(t).strip().lower() for t in tags or [] if str(t).strip()})
    if words:
        Path(folder, TAGS_FILE).write_text("# the mod list's tags for this mod (rusemod.fairplay)\ntags = ["
                                           + ", ".join(json.dumps(t) for t in words) + "]\n", encoding="utf-8")


def cheat_calls(path: str, data: bytes) -> set[str]:
    """What the game's cheat orders named in one script file do (a compiled .xyz, or an .ipk of them)."""
    low = path.lower()
    if low.endswith(".ipk"):
        from .edat import Edat
        pack = Edat(bytes(data))
        return set().union(*[cheat_calls(e.path, bytes(pack.read(e))) for e in pack.entries
                             if e.path.lower().endswith(".xyz")])
    if not low.endswith(".xyz"):
        return set()
    try:
        payload = pyscript.read_xyz(bytes(data)).payload
    except pyscript.ScriptError:
        payload = bytes(data)  # not the game's own form: look at the bytes as they are
    return {what for name, what in CHEAT_CALLS.items() if name in payload}


@dataclass
class ModCheck:
    id: str
    name: str
    version: str = "0.0.0"
    cheat: bool = False                          # tagged "cheat"
    scripts: list = field(default_factory=list)  # the game scripts a .rmod replaces or adds
    calls: list = field(default_factory=list)    # what the cheat orders its scripts name do

    @property
    def offline_reason(self) -> str | None:
        if self.cheat:
            return f"{self.name} is a cheat or a test tool"
        if self.calls:
            return f"{self.name}'s scripts " + " and ".join(self.calls)
        return None

    def view(self) -> dict:
        return {"id": self.id, "name": self.name, "version": self.version, "cheat": self.cheat,
                "scripts": list(self.scripts), "calls": list(self.calls), "offline": self.offline_reason}


def check_mod(folder) -> ModCheck:
    """What one mod folder of the library (or any mod folder with mod.toml) is, for fair play."""
    folder = Path(folder)
    try:
        manifest = tomllib.loads((folder / "mod.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        manifest = {}
    m = manifest.get("mod", {})
    out = ModCheck(str(m.get("id") or folder.name), str(m.get("name") or m.get("id") or folder.name),
                   str(m.get("version", "0.0.0")), CHEAT_TAG in read_tags(folder))
    rmod_file = str(manifest.get("rmod", {}).get("file", "") or "")
    if rmod_file:
        _read_rmod(folder / rmod_file, out)
    return out


def _read_rmod(path, out: ModCheck) -> None:
    """A .rmod's game scripts and the cheat orders they name, into `out`."""
    from . import rmod
    try:
        mod = rmod.check(path)
    except Exception:  # noqa: BLE001 - the build names the mod's own problem; here it just has no scripts to read
        return
    if out.version == "0.0.0":
        out.version = rmod.version_of(mod)
    out.scripts = rmod.scripts_of(mod)
    calls: set = set()
    for group in mod.file_patches:
        for fp in group.files:
            calls |= cheat_calls(fp.path, fp.data or b"")
    out.calls = sorted(calls)


def check_infos(infos) -> FairPlay:
    """For a build given only the mods as read (`ruse build`, rusemod.resolve.ModInfo): the .rmod mods' scripts are
    read; the mod list's tags aren't known there."""
    out = []
    for m in infos:
        c = ModCheck(m.id, m.id, m.version)
        if m.rmod is not None:
            _read_rmod(m.rmod, c)
        out.append(c)
    return FairPlay(out)


@dataclass
class FairPlay:
    """What a mod set's copy is for: offline (and why), or multiplayer. The watcher goes in every copy."""
    mods: list = field(default_factory=list)  # ModCheck, in load order
    watch: bool = True
    scripts: bool | None = None  # our game scripts in the copy: None = IN_BUILDS (off until tested in the game)
    dev: bool = False             # a valid RUSE Guard dev key on this PC: the one way past the offline lock

    @property
    def offline(self) -> list[str]:
        return [m.offline_reason for m in self.mods if m.offline_reason]

    @property
    def script_mods(self) -> list[str]:
        return [m.name for m in self.mods if m.scripts]

    def patches(self, code: str = NO_BUILD_CODE) -> list[bytes]:
        """Our game scripts this copy gets, compiled: a cheat copy's lock with the copy's build `code` in it
        (build_code; left out, the lock has none and leaves every match), the watcher, the record."""
        if not ON or not (IN_BUILDS if self.scripts is None else self.scripts):
            return []
        lock = bool(self.offline) and not self.dev
        return ([lock_script(code)] if lock else []) + [game_script(name) for name in (WATCH, GUARD) if self.watch]


def check(folders, watch: bool = True, home=None) -> FairPlay:
    """The mod set's fair play check; with `home` (the platform folder), its RUSE Guard dev key is looked at too."""
    dev = False
    if home is not None:
        from .guard import dev_key
        dev = dev_key(home).valid
    return FairPlay([check_mod(f) for f in folders], watch, dev=dev)


# --- our game scripts ---
def game_script(name: str) -> bytes:
    """A compiled game script of ours (tools/compile_gamescript.py25): the module's code, marshalled."""
    return (SCRIPTS / f"{name}.bin").read_bytes()[16:]


def build_code(build_id, fp: bytes | None, mods) -> str:
    """A cheat copy's build code, for its lock: BUILD_CODE_DIGITS hex digits (52 bits) that are the same in two
    copies exactly when what a join code names is the same (rusemod.lock: the game build, the mods with their
    versions in the set's order, the gameplay fingerprint `fp`), short enough for the lock's two orders. Never all
    zeros: that is the lock's "no code" (NO_BUILD_CODE)."""
    h = hashlib.sha256(b"RUSE Guard build code 1\n" + str(build_id or 0).encode("utf-8") + b"\n" + (fp or b""))
    for mod_id, version in mods:
        h.update(f"\n{mod_id}\t{version}".encode("utf-8"))
    code = h.hexdigest()[:BUILD_CODE_DIGITS]
    return code if code != NO_BUILD_CODE else "1" + code[1:]


def lock_script(code: str = NO_BUILD_CODE) -> bytes:
    """The lock of a cheat copy, compiled, with the copy's build code in it: the constant its top level sets
    `_fairplay_lock_code` to. Two copies whose locks carry the same code play multiplayer and co-op together; a lock
    with NO_BUILD_CODE matches no other copy."""
    if not re.fullmatch(r"[0-9a-f]{%d}" % BUILD_CODE_DIGITS, code):
        # not a game rule: what the lock's two orders carry
        raise FairPlayError(f"{code!r} isn't a build code ({BUILD_CODE_DIGITS} hex digits), so the copy's lock can't "
                            f"be made.")
    try:
        return pyscript.dump(pyscript.with_value(pyscript.load(game_script(LOCK)), _CODE_NAME, code.encode("ascii")))
    except pyscript.ScriptError as exc:
        raise FairPlayError(f"The copy's lock can't take its build code: {exc}") from None


def lock_numbers(code: str) -> tuple[int, int]:
    """The two production numbers a lock with build `code` announces in a match (fairplay_lock.py25 `numbers`, the
    same sum): each is LOCK_FIRST plus which half it is in bits 28-29 (0, 1); the first half carries the
    announcement's version (LOCK_VERSION, bits 24-27) and the code's first 24 bits, the second its last 28. The
    game counts a side's own productions from 1, and reads a number as signed 32 bits: these stay in between."""
    if not re.fullmatch(r"[0-9a-f]{%d}" % BUILD_CODE_DIGITS, code) or code == NO_BUILD_CODE:
        raise FairPlayError(f"{code!r} isn't a build code a lock announces.")
    return LOCK_FIRST | LOCK_VERSION << 24 | int(code[:6], 16), LOCK_FIRST | 1 << 28 | int(code[6:], 16)


def lock_code_of(script: bytes) -> str | None:
    """The build code in a compiled lock (lock_script), or None when the script sets none; for checks and tests."""
    try:
        top = pyscript.load(script)
        ins = pyscript.instructions(top.code)
        for k in range(1, len(ins)):
            if ins[k][1] == pyscript.STORE_NAME and top.names[ins[k][2]] == _CODE_NAME \
                    and ins[k - 1][1] == pyscript.LOAD_CONST:
                value = top.consts[ins[k - 1][2]]
                return value.decode("ascii") if isinstance(value, bytes) else None
    except (pyscript.ScriptError, IndexError, UnicodeDecodeError, AttributeError):
        pass
    return None


def script_is_current(name: str) -> bool:
    """Whether the .bin was compiled from the .py25 as it is now (its first 16 bytes are the source's MD5)."""
    src = (SCRIPTS / f"{name}.py25").read_bytes().replace(b"\r\n", b"\n")
    return (SCRIPTS / f"{name}.bin").read_bytes()[:16] == hashlib.md5(src).digest()


def _appended(raw: bytes, patches: list[bytes]) -> bytes:
    """A game script (.xyz) with our compiled `patches` after its own code."""
    xyz = pyscript.read_xyz(raw)
    payload = xyz.payload
    for patch in patches:
        payload = pyscript.append_script(payload, patch)
    return pyscript.write_xyz(pyscript.Xyz(xyz.source_md5, payload))


def script_folders(clusters) -> list[str]:
    """The map script folders the game's scenarios name, as IA_Common.dat member folders
    (`genpython\\1000\\test\\map\\<map>\\<folder>`), from the scenario clusters' data (`clusters`: their bytes, as
    the build has them). Each scenario adds its folder to the game's script search when its map loads, ahead of the
    game's own scripts; its match script (effetmap for a mission, effetmapmultiplayer for a skirmish or multiplayer
    match) is looked for there first."""
    from .ndf import Ndf
    found = set()
    for raw in clusters:
        strings = Ndf(raw).strings if raw[:4] == b"EUG0" else raw.decode("latin-1").split("\0")
        for s in strings:
            m = _FOLDER.fullmatch(s)
            if m:
                found.add(SCRIPT_ROOT + m.group(1).lower())
    return sorted(found)


def multiplayer_script(zz, changed: dict | None = None) -> bytes:
    """The game's own multiplayer match script (.xyz) from ZZ_Win.dat as the build has it: `zz` (with the .rmod
    mods' changes) and `changed` (the script packs the build changed already, {member: bytes})."""
    from .edat import Edat
    entry = zz.entry(pyscript.SCRIPT_PACK)
    if entry is None:
        raise FairPlayError(f"ZZ_Win.dat has no {pyscript.SCRIPT_PACK}, so the copy can't get its fair play scripts.")
    pack = Edat((changed or {}).get(entry.path) or bytes(zz.read(entry)))
    member = next((e for e in pack.entries if e.path.lower().endswith(MULTIPLAYER)), None)
    if member is None:
        raise FairPlayError(f"{pyscript.SCRIPT_PACK} has no effetmapmultiplayer.xyz, so the copy can't get its fair "
                            f"play scripts.")
    return bytes(pack.read(member))


def add_to_launcher(zz, patches: list[bytes], changed: dict | None = None) -> tuple[str, bytes]:
    """(the script pack's path in ZZ_Win.dat, the pack with our compiled `patches` after the code of the game's own
    Battles launcher, effetmapmultiplayer.xyz in it). That launcher is what the game loads for every Battles match,
    skirmish or multiplayer: a map folder's copy of it in IA_Common.dat is never loaded for Battles (add_to_maps alone
    ran nothing in the owner's matches with Nuke on 2026-10-30; the camera keys found the same on 2026-10-14), and the
    lock ran from here in those matches. `zz`: ZZ_Win.dat as the build has it (with the .rmod mods' changes);
    `changed`: the script packs the build changed already ({member path in ZZ_Win.dat: bytes}), patched on top of."""
    from .edat import Edat
    entry = zz.entry(pyscript.SCRIPT_PACK)
    if entry is None:
        raise FairPlayError(f"ZZ_Win.dat has no {pyscript.SCRIPT_PACK}, so the copy can't get its fair play scripts.")
    pack = Edat((changed or {}).get(entry.path) or bytes(zz.read(entry)))
    member = next((e for e in pack.entries if e.path.lower().endswith(MULTIPLAYER)), None)
    if member is None:
        raise FairPlayError(f"{pyscript.SCRIPT_PACK} has no effetmapmultiplayer.xyz, so the copy can't get its fair "
                            f"play scripts.")
    return entry.path, pack.to_bytes({member.path: _appended(bytes(pack.read(member)), patches)})


def add_to_maps(ia, folders, multiplayer: bytes, patches: list[bytes]) -> int:
    """Put our compiled `patches` in every map script folder of `ia` (IA_Common.dat as the build has it, a
    rusemod.rmod.Layered: it takes replace and add): after the code of each folder's own match scripts, and as a
    folder's multiplayer match script where it has none of its own (the game's, `multiplayer`, followed by ours).
    The scripts switch on once per session, so a match loading two of them gets them once. Returns how many folders
    got them."""
    done = 0
    for folder in folders:
        for name, fallback in (("effetmapmultiplayer.xyz", multiplayer), ("effetmap.xyz", None)):
            member = folder + "\\" + name
            raw = ia.get(member)
            if raw is not None:
                ia.replace(member, _appended(raw, patches))
            elif fallback is not None:
                ia.add(member, _appended(fallback, patches))
        done += 1
    return done


# --- the copy's record and its join code ---
def _stat(path: Path, full: bool) -> dict:
    st = path.stat()
    out = {"size": st.st_size, "time": st.st_mtime_ns}
    if full:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1 << 22), b""):
                h.update(block)
        out["sha256"] = h.hexdigest()
    return out


def write_record(instance, build_id, fp: bytes | None, mods, fair: FairPlay, written,
                 lock_code: str | None = None) -> dict:
    """Leave the build's record in the copy: the join code (None when the mods change nothing in how the game plays,
    or their versions don't fit a code), why it's a cheat copy (`offline`; `why` is then "offline", and the copy has
    its join code all the same: its players compare codes before a same-build match), the build code in its lock
    (`lock_code`, None when it has no lock), its script mods, the watcher, and every file the build wrote
    (`written`: paths relative to the copy) with its size, time and SHA-256."""
    instance = Path(instance)
    code, why = None, "offline" if fair.offline else None
    if fp is None:
        why = why or "no gameplay change"
    else:
        try:
            code = encode_join_code(int(build_id or 0), fp, [(str(i), str(v)) for i, v in mods])
        except (ValueError, UnicodeEncodeError) as exc:
            why = why or f"no join code: {exc}"
    record = {"version": 1, "build": str(build_id), "code": code, "why": why,
              "fingerprint": fingerprint_text(fp) if fp else None, "mods": [[str(i), str(v)] for i, v in mods],
              "offline": fair.offline, "lock": lock_code, "scripts": fair.script_mods, "watch": fair.watch,
              "files": {str(rel).replace("\\", "/"): _stat(instance / rel, True) for rel in written}}
    (instance / RECORD).write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def read_record(instance) -> dict | None:
    try:
        return json.loads(Path(instance, RECORD).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _gameplay_files(root: Path):
    """The copy's files that make the game what it is: everything under Data and Maps, and the programs at the top."""
    for top in root.iterdir() if root.is_dir() else []:
        if top.is_dir() and top.name.lower() in GAMEPLAY_DIRS:
            for p in top.rglob("*"):
                if p.is_file():
                    yield p.relative_to(root).as_posix()
        elif top.is_file() and top.suffix.lower() in (".exe", ".dll"):
            yield top.name


def _same_as_game(copy: Path, game: Path) -> bool:
    try:
        if os.path.samefile(copy, game):
            return True
        a, b = copy.stat(), game.stat()
        return a.st_size == b.st_size and a.st_mtime_ns == b.st_mtime_ns
    except OSError:
        return False


def check_copy(instance, game, full: bool = False) -> list[str]:
    """What changed in a modded copy since the build made it: the files the build wrote (their size and time; with
    `full`, their SHA-256), and every other file of the game's data and maps (still the game's own: the same file, or
    the same size and time), and files the game doesn't have. [] = unchanged. `full` reads every written file
    (ZZ_Win.dat is 2.4 GB), so it takes a few seconds."""
    instance, game = Path(instance), Path(game)
    record = read_record(instance)
    if record is None:
        return ["the copy has no record of its build (it was made by an older app, or the record was removed)"]
    files = record.get("files", {})
    out = []
    for rel, was in sorted(files.items()):
        p = instance / rel
        if not p.is_file():
            out.append(f"{rel} is gone")
            continue
        now = _stat(p, full)
        if now["size"] != was.get("size") or (full and now["sha256"] != was.get("sha256")) or \
                (not full and now["time"] != was.get("time")):
            out.append(f"{rel} changed after the build")
    written = {r.lower() for r in files}
    for rel in sorted(_gameplay_files(instance)):  # the disk's own order differs by system (NTFS by name, Linux not)
        if rel.lower() in written:
            continue
        theirs = game / rel
        if not theirs.is_file():
            out.append(f"{rel} isn't one of the game's files")
        elif not _same_as_game(instance / rel, theirs):
            out.append(f"{rel} isn't the game's own file any more")
    return out


def copy_view(instance, game, full: bool = False) -> dict:
    """What the Launcher shows about the modded copy: its join code (None when it has none, `why` says why), the
    fingerprint, the mods, why it's offline, its script mods, the watcher, and what changed since the build."""
    record = read_record(instance)
    if record is None:
        return {"built": False, "code": None, "why": "not built", "fingerprint": None, "mods": [], "offline": [],
                "scripts": [], "watch": False, "problems": []}
    problems = check_copy(instance, game, full)
    code = record.get("code") if not problems else None
    why = record.get("why") or ("changed" if problems else None)
    return {"built": True, "code": code, "why": why, "fingerprint": record.get("fingerprint"),
            "mods": record.get("mods", []), "offline": record.get("offline", []),
            "scripts": record.get("scripts", []), "watch": bool(record.get("watch")), "problems": problems}


def compare(mine: str | None, theirs: str) -> dict:
    """Two join codes side by side: {"same": bool, "differences": [sentences]}. `mine` None: this PC has no code."""
    other = decode_join_code(theirs)  # CodeError says what's wrong with the pasted text
    if not mine:
        raise CodeError("Your modded copy has no join code yet: press Play once, then compare.")
    me = decode_join_code(mine)
    if me.build_id == other.build_id and me.fingerprint == other.fingerprint:
        return {"same": True, "differences": []}
    out = []
    if me.build_id != other.build_id:
        out.append(f"Different game versions: yours is build {me.build_id}, theirs is build {other.build_id}. "
                   f"The one behind updates the game in Steam.")
    mine_v, theirs_v = dict(me.mods), dict(other.mods)
    for mod_id, v in other.mods:
        if mod_id not in mine_v:
            out.append(f"They have {mod_id} {v}; you don't.")
        elif mine_v[mod_id] != v:
            out.append(f"{mod_id}: you have {mine_v[mod_id]}, they have {v}.")
    out += [f"You have {mod_id} {v}; they don't." for mod_id, v in me.mods if mod_id not in theirs_v]
    if not out:
        out.append("Same mods and versions, but the games still differ (a mod was changed without a new version, "
                   "or the mods load in another order). Use the same mod files in the same order.")
    return {"same": False, "differences": out}
