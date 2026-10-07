"""Sounds and music: the game's sound files played and made, the game's songs and where each one plays, and a mod's
own sounds put in by the build.

A mod replaces one of the game's sounds with a WAV at files/replace/<the sound's path in ZZ_Win.dat>.wav (the way a
texture is replaced by files/replace/<texture>.png): files/replace/gen_sound/ww2/sons/atp_music/battle1.ess.wav. The
build makes the game's kind of file from it, and the small description the game reads first, in every sound bank
that has one for that sound.

Reading follows RugnirViking's moddingSuite (GPL-2.0-or-later: its EssReader), widened to any number of channels;
the writer is ours. What `encode` makes, `decode` plays back sample for sample (tests/test_sound.py). Heard in the game
(the sound test, 2026-10-07): the main menu song, the songs of battle lists 1 and 2 and the Sherman's move lines,
each replaced this way; the rest (the third list, missions' songs, jingles, other voices) not tried yet.
"""
from __future__ import annotations

import hashlib
import io
import struct
import wave
from array import array
from pathlib import Path

REPLACE = "files/replace"
BANKS = "gen_sound\\pack\\"            # the sound banks in ZZ_Win.dat that hold each sound's description
FRAMES_PER_BLOCK = {1: 1024, 2: 512, 6: 170}  # the channel counts the game's own sounds have
TOP_BAND = 32779
CODEC_VERSION = 1                       # part of the cache key: a cooked sound is reused only by the same writer
_INT_LO, _INT_HI = -0x80000000, 0x7FFFFFFF


class SoundError(ValueError):
    pass


def _i16(v: int) -> int:
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def _i32(v: int) -> int:
    return ((v + 0x80000000) & 0xFFFFFFFF) - 0x80000000


def header(b: bytes) -> dict:
    """What a game sound says about itself: channels, rate, frames, its loop, and its kind (`flag`)."""
    if len(b) < 20 or b[0] != 1 or b[1] != 0:
        # not a game rule: the bytes aren't a sound file of the kind this reads
        raise SoundError("not one of the game's sounds")
    rate = struct.unpack_from(">H", b, 6)[0]
    frames, loop_start, loop_end = struct.unpack_from(">III", b, 8)
    return dict(codec=b[2], table=b[3], flag=b[4], channels=b[5], rate=rate, frames=frames, loop_start=loop_start,
                loop_end=loop_end)


def _block_ends(b: bytes) -> list[int]:
    n = 1
    while 20 + 4 * n <= len(b):
        if struct.unpack_from(">I", b, 16 + 4 * n)[0] == len(b) - 20 - 4 * n:
            return list(struct.unpack_from(f">{n}I", b, 20))
        n += 1
    raise SoundError("a sound with no parts")


class Stats:
    """What a checking decode saw (tests and checks): parts whose stored start doesn't follow on from the part
    before, codes read past a part's end, and so on."""

    def __init__(self):
        self.blocks = self.breaks = self.wraps = self.overruns = 0
        self.cut_short = 0  # samples missing at the very end (the file stops before its last codes)
        self.spare_bits: dict[int, int] = {}


class _OutOfBits(SoundError):
    pass


def _decode_channel(bits: str, pos: int, n: int, st: list[int], out, off: int, stride: int, stats):
    w2, w1, y1, y2, x1, x2, x3, c1, c2, c3 = st
    find = bits.find
    for i in range(n):
        j = find("1", pos)
        if j < 0:  # the file stops here: the rest of this part keeps the last sample
            for _ in range(n - i):
                out[off] = y1
                off += stride
            err = _OutOfBits("the sound ends early")
            err.missing = n - i
            err.state = [w2, w1, y1, y2, x1, x2, x3, c1, c2, c3]
            raise err
        r = j - pos
        pos = j + 1
        if r == 24:
            r = 24 + int(bits[pos:pos + 16], 2)
            pos += 16
        k = r >> 1
        if k == 0:
            lo, hi = 0, c1
            c1 -= 2 * ((c1 + 2046) >> 11)
        elif k == 1:
            lo, hi = c1, c1 + c2
            c1 += 6 * ((c1 + 2048) >> 11)
            c2 -= 2 * ((c2 + 1022) >> 10)
        elif k == 2:
            lo = c1 + c2
            hi = lo + c3
            c1 += 6 * ((c1 + 2048) >> 11)
            c2 += 6 * ((c2 + 1024) >> 10)
            c3 -= 2 * ((c3 + 510) >> 9)
        else:
            lo = c1 + c2 + (c3 + 1) * (k - 2)
            hi = lo + c3
            c1 += 6 * ((c1 + 2048) >> 11)
            c2 += 6 * ((c2 + 1024) >> 10)
            c3 += 6 * ((c3 + 512) >> 9)
        mid = (lo + hi) >> 1
        if mid <= c1:
            c1 -= 2 * ((c1 + 2046) >> 11)
        elif mid <= c2:
            c2 -= 2 * ((c2 + 1022) >> 10)
        elif mid <= c3:
            c3 -= 2 * ((c3 + 510) >> 9)
        if hi - lo > 64:
            e = lo + int(bits[pos:pos + 2], 2) * (((hi - lo) >> 2) + 1)
            pos += 2
        else:
            e = mid
        if r & 1:
            e = ~e
        p1 = 4 * x1 - 5 * x2 - 2 * x3
        a = p1 * w1 + 128
        if a < _INT_LO or a > _INT_HI:
            a = _i32(a)
            if stats is not None:
                stats.wraps += 1
        xn = (a >> 8) + e
        if p1 or e:
            w1 += 2 if (p1 ^ e) >= 0 else -2
        p2 = 2 * y1 - y2
        a = p2 * w2 + 128
        if a < _INT_LO or a > _INT_HI:
            a = _i32(a)
            if stats is not None:
                stats.wraps += 1
        y = (a >> 8) + xn
        if p2 or xn:
            w2 += 2 if (p2 ^ xn) >= 0 else -2
        if y > 32767:
            y = 32767
        elif y < -32768:
            y = -32768
        x3 = x2
        x2 = x1
        x1 = xn
        y2 = y1
        y1 = y
        out[off] = y
        off += stride
    return pos, [w2, w1, y1, y2, x1, x2, x3, c1, c2, c3]


def decode(b: bytes, stats: Stats | None = None) -> tuple[array, dict]:
    """A game sound as 16-bit PCM (an array('h'), channels interleaved) and its header()."""
    h = header(b)
    if h["codec"] != 2 or h["table"] != 2:
        # not a game rule: what this reader knows (every one of the game's own sounds is of this one kind)
        raise SoundError(f"a kind of sound file the game's own don't use ({h['codec']}, {h['table']})")
    ch, frames = h["channels"], h["frames"]
    fpb = FRAMES_PER_BLOCK.get(ch)
    if fpb is None:
        # not a game rule: this reader knows the channel counts the game's own sounds have (1, 2, 6)
        raise SoundError(f"{ch} channels: none of the game's sounds has that many")
    ends = _block_ends(b)
    if len(ends) != -(-frames // fpb):
        raise SoundError(f"{len(ends)} parts for {frames} frames")
    data = 20 + 4 * len(ends)
    out = array("h", bytes(2 * frames * ch))
    prev = None
    start = 0
    for bi, end in enumerate(ends):
        blk = b[data + start:data + end]
        n = min(fpb, frames - bi * fpb)
        states = [list(struct.unpack_from(">10h", blk, 20 * c)) for c in range(ch)]
        if stats is not None:
            stats.blocks += 1
            if prev is not None and [[_i16(v) for v in s] for s in prev] != states:
                stats.breaks += 1
        payload = blk[20 * ch:]
        after = b[data + end:data + end + 8]  # the game reads on past a part's end: its last code may end there
        after += bytes(8 - len(after))
        limit = 8 * len(payload)
        bits = format(int.from_bytes(payload + after, "big"), f"0{limit + 64}b")
        pos = 0
        prev = []
        for c in range(ch):
            try:
                pos, st = _decode_channel(bits, pos, n, states[c], out, bi * fpb * ch + c, ch, stats)
            except _OutOfBits as exc:
                # some of the game's own songs stop a few codes before their end (Battle 3: 4 samples); the game
                # reads on past the file there. Only the very last part may: anywhere else the file is damaged.
                if bi != len(ends) - 1:
                    raise SoundError(f"part {bi} of {len(ends)} ends early: the file is damaged") from None
                if stats is not None:
                    stats.cut_short += exc.missing
                pos, st = len(bits), exc.state
            prev.append(st)
        if pos > limit + 64:
            raise SoundError(f"part {bi} reads far past its end")
        if stats is not None:
            stats.overruns += pos > limit
            stats.spare_bits[limit - pos] = stats.spare_bits.get(limit - pos, 0) + 1
        start = end
    return out, h


def _encode_channel(samples, st: list[int], codes: list[str], recon=None):
    w2, w1, y1, y2, x1, x2, x3, c1, c2, c3 = st
    put = codes.append
    for t in samples:
        p1 = 4 * x1 - 5 * x2 - 2 * x3
        a = p1 * w1 + 128
        if a < _INT_LO or a > _INT_HI:
            a = _i32(a)
        P1 = a >> 8
        p2 = 2 * y1 - y2
        a = p2 * w2 + 128
        if a < _INT_LO or a > _INT_HI:
            a = _i32(a)
        P2 = a >> 8
        want = t - P1 - P2
        if want >= 0:
            m, sign = want, 0
        else:
            m, sign = ~want, 1
        if m < c1:
            k0 = 0
        elif m < c1 + c2:
            k0 = 1
        else:
            k0 = min(TOP_BAND, 2 + (m - c1 - c2) // (c3 + 1))
        best = None
        for k in (k0 - 1, k0, k0 + 1):  # the nearest of the three bands around it
            if k < 0 or k > TOP_BAND:
                continue
            if k == 0:
                lo, hi = 0, c1
            elif k == 1:
                lo, hi = c1, c1 + c2
            else:
                lo = c1 + c2 + (c3 + 1) * (k - 2)
                hi = lo + c3
            if hi - lo > 64:
                step = ((hi - lo) >> 2) + 1
                q = min(3, max(0, (m - lo + (step >> 1)) // step))
                v = lo + q * step
            else:
                q = -1
                v = (lo + hi) >> 1
            err = v - m if v >= m else m - v
            if best is None or err < best[0]:
                best = (err, k, q, v, lo, hi)
        _, k, q, v, lo, hi = best
        r = 2 * k + sign
        code = "0" * r + "1" if r < 24 else "0" * 24 + "1" + format(r - 24, "016b")
        put(code if q < 0 else code + "01"[q >> 1] + "01"[q & 1])
        if k == 0:
            c1 -= 2 * ((c1 + 2046) >> 11)
        elif k == 1:
            c1 += 6 * ((c1 + 2048) >> 11)
            c2 -= 2 * ((c2 + 1022) >> 10)
        elif k == 2:
            c1 += 6 * ((c1 + 2048) >> 11)
            c2 += 6 * ((c2 + 1024) >> 10)
            c3 -= 2 * ((c3 + 510) >> 9)
        else:
            c1 += 6 * ((c1 + 2048) >> 11)
            c2 += 6 * ((c2 + 1024) >> 10)
            c3 += 6 * ((c3 + 512) >> 9)
        mid = (lo + hi) >> 1
        if mid <= c1:
            c1 -= 2 * ((c1 + 2046) >> 11)
        elif mid <= c2:
            c2 -= 2 * ((c2 + 1022) >> 10)
        elif mid <= c3:
            c3 -= 2 * ((c3 + 510) >> 9)
        e = v if sign == 0 else ~v
        xn = P1 + e
        if p1 or e:
            w1 += 2 if (p1 ^ e) >= 0 else -2
        y = P2 + xn
        if p2 or xn:
            w2 += 2 if (p2 ^ xn) >= 0 else -2
        if y > 32767:
            y = 32767
        elif y < -32768:
            y = -32768
        x3 = x2
        x2 = x1
        x1 = xn
        y2 = y1
        y1 = y
        if recon is not None:
            recon.append(y)
    return [w2, w1, y1, y2, x1, x2, x3, c1, c2, c3]


def encode(pcm, channels: int, rate: int, flag: int = 1, recon=None) -> bytes:
    """A game sound from 16-bit PCM (any sequence of ints, channels interleaved). `recon` (a list or an array('h')),
    if given, gets what the game will play, interleaved."""
    fpb = FRAMES_PER_BLOCK.get(channels)
    if fpb is None:
        # (whether the game plays other channel counts isn't known)
        # not a game rule: this writer makes the channel counts the game's own sounds have
        raise SoundError(f"{channels} channels: the game's sounds have 1, 2 or 6")
    if not 1 <= rate <= 0xFFFF:
        raise SoundError(f"a rate of {rate} a second can't be written")
    frames = len(pcm) // channels
    if frames == 0:
        raise SoundError("an empty sound")
    states = [[0] * 10 for _ in range(channels)]
    body = bytearray()
    ends = []
    played = [array("h") for _ in range(channels)] if recon is not None else None
    for start in range(0, frames, fpb):
        n = min(fpb, frames - start)
        head = bytearray()
        codes: list[str] = []
        for c in range(channels):
            st = [_i16(v) for v in states[c]]  # what the game reads back: the encoder goes on from the same
            head += struct.pack(">10h", *st)
            part = pcm[start * channels + c:(start + n) * channels:channels]
            states[c] = _encode_channel(part, st, codes, played[c] if played is not None else None)
        bits = "".join(codes)
        bits += "0" * (-len(bits) % 8)
        body += head
        if bits:
            body += int(bits, 2).to_bytes(len(bits) // 8, "big")
        ends.append(len(body))
    if played is not None:
        both = array("h", bytes(2 * frames * channels))
        for c in range(channels):
            both[c::channels] = played[c]
        recon.extend(both)
    head = bytes([1, 0, 2, 2, flag, channels]) + struct.pack(">HIII", rate, frames, 0, frames)
    return head + struct.pack(f">{len(ends)}I", *ends) + bytes(body)


def description(b: bytes) -> bytes:
    """The description the game reads before a sound, for a sound of the kind music and most voices are (flag 1).
    The other kind also carries a loudness track whose making isn't known yet: refused."""
    h = header(b)
    if h["flag"] != 1:
        raise SoundError("this kind of sound (one with a loudness track) can't be made yet")
    ch = h["channels"]
    return struct.pack("<HBBBBHIIIII", 0x0106, 1, ch, 0, 2 * ch, h["rate"], h["frames"], 2 * ch, len(b),
                       h["loop_start"], h["loop_end"])


# --- WAV files ---
def read_wav(raw: bytes) -> tuple[array, int, int]:
    """(16-bit PCM, channels, rate) of a WAV file; 16-bit PCM WAVs only."""
    try:
        with wave.open(io.BytesIO(raw), "rb") as w:
            if w.getsampwidth() != 2:
                raise SoundError(f"a WAV of {8 * w.getsampwidth()}-bit samples: save it as 16-bit")
            pcm = array("h", w.readframes(w.getnframes()))
            return pcm, w.getnchannels(), w.getframerate()
    except (wave.Error, EOFError) as exc:
        raise SoundError(f"not a WAV file we can read ({exc})") from None


def write_wav(pcm, channels: int, rate: int) -> bytes:
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(array("h", pcm).tobytes())
    return out.getvalue()


# --- the game's songs ---
SONGS_AT = "$/Misc/Musics/"
MENU_MUSIC = "$/GFX/Everything/FlashSoundManager"
PLAYLISTS = "$/GFX/Everything/musicInGame"


def member_of(file_name: str) -> str:
    """The path in ZZ_Win.dat of the sound the game plays for a FileName in its data (WW2\\Sons\\X.ogg)."""
    stem = file_name.replace("/", "\\").rsplit(".", 1)[0]
    return ("gen_sound\\" + stem + ".ess").lower()


def song_name(address: str) -> str:
    """A song's name to show: its name in the data without RUSE_, in words ("RUSE_battle1_ref" -> "Battle 1 ref")."""
    name = address.rsplit("/", 1)[-1]
    if name.lower().startswith("ruse_"):
        name = name[5:]
    out = ""
    for i, ch in enumerate(name):
        prev = name[i - 1] if i else ""
        if ch == "_":
            out += " "
        elif (ch.isdigit() and prev.isalpha()) or (ch.isupper() and prev.islower()):
            out += " " + ch
        else:
            out += ch
    out = " ".join(out.split())
    return out[:1].upper() + out[1:].lower()


def songs(ix) -> list[dict]:
    """The game's songs from its index: [{address, name, file, member}] in the data's order."""
    out = []
    for o in ix.of_class("TSoundStream"):
        if not o["address"].startswith(SONGS_AT):
            continue
        file = next((t for p, _n, t in o["values"] if p == "FileName" and t), None)
        if file:
            out.append({"address": o["address"], "name": song_name(o["address"]), "file": file,
                        "member": member_of(file)})
    return out


# The menus' songs by their key in the data (MusicDescriptors = MAP [('outgame', ...), ('credits', ...)], read from
# the game's data 2026-10-07; the game index keeps the songs but not the keys)
MENU_KEYS = {"$/Misc/Musics/RUSE_outgame": "outgame", "$/Misc/Musics/RUSE_theme": "credits"}


def slots(ix) -> dict:
    """Where the game's data puts songs: {"menu": [song address, ...]} (the menus' songs; MENU_KEYS says which is
    which), {"playlists": [[song address, ...], ...]} (the three lists battles play from, in the data's order)."""
    try:
        menu = [what for path, _kind, what in ix.uses(MENU_MUSIC) if path.startswith("MusicDescriptors[")]
    except KeyError:
        menu = []
    lists = []
    try:
        parts = [what for path, kind, what in ix.uses(PLAYLISTS) if path.startswith("PlayLists[") and kind == "object"]
    except KeyError:
        parts = []
    for part in parts:
        lists.append([what for path, _kind, what in ix.uses(part) if path.startswith("Musics[")])
    return {"menu": menu, "playlists": lists}


def game_scripts(game: Path) -> dict:
    """{script path: compiled bytes} of the game's scripts that can name songs: the maps' (IA_Common.dat) and the
    game's own (the script packs in ZZ_Win.dat: the end-of-match screens and mission objectives play jingles)."""
    from .edat import Edat
    out: dict = {}
    data = sorted(Path(game, "Data", "PC").glob("*/IA_Common.dat")) + sorted(Path(game, "Data", "PC").glob("*/ZZ_Win.dat"))
    for pack in data:
        with Edat.open(str(pack)) as a:
            for e in a.entries:
                p = e.path.lower()
                if p.endswith(".xyz") and "\\map\\" in p:
                    out[e.path] = bytes(a.read(e))
                elif p.startswith("genpython\\") and p.endswith(".ipk"):
                    inner = Edat(bytes(a.read(e)))
                    for f in inner.entries:
                        if f.path.lower().endswith(".xyz"):
                            out[e.path + "!" + f.path] = bytes(inner.read(f))
    return out


def script_songs(raw_scripts) -> dict:
    """{song address (lower case): [script path, ...]} from scripts ({path: the compiled script's bytes}): the songs
    each one names (missions and the end-of-match screens play songs by name)."""
    import zlib
    found: dict = {}
    at = SONGS_AT.lower().encode()  # the game's own scripts write it $/MISC/Musics/
    for path, raw in raw_scripts.items():
        try:
            data = zlib.decompressobj().decompress(raw[28:]) if raw[:4] == b"XYZ0" else raw
        except zlib.error:
            continue
        low = data.lower()
        pos = low.find(at)
        while pos >= 0:
            n = struct.unpack_from("<I", data, pos - 4)[0] if pos >= 4 else 0
            if len(at) < n < 120:
                found.setdefault(low[pos:pos + n].decode("latin-1"), set()).add(path)
            pos = low.find(at, pos + 1)
    return {k: sorted(v) for k, v in found.items()}


# --- a mod's own sounds, put in by the build ---
def mod_sounds(folder: Path) -> dict:
    """{sound path in ZZ_Win.dat (backslashes, lower case): its WAV} from a mod's files/replace/**/<name>.ess.wav."""
    root = Path(folder) / REPLACE
    if not root.is_dir():
        return {}
    out = {}
    for f in sorted(root.rglob("*.wav")):
        rel = f.relative_to(root).as_posix().lower()
        if rel.endswith(".ess.wav"):
            out[rel[:-len(".wav")].replace("/", "\\")] = f
    return out


def _cooked(raw_wav: bytes, flag: int, cache: Path | None) -> bytes:
    """The game sound made from a WAV, kept in `cache` (by the WAV's contents) so it's made once."""
    key = hashlib.sha256(raw_wav + bytes([flag, CODEC_VERSION])).hexdigest()
    file = Path(cache) / "sound" / f"{key}.ess" if cache is not None else None
    if file is not None and file.is_file():
        return file.read_bytes()
    pcm, channels, rate = read_wav(raw_wav)
    made = encode(pcm, channels, rate, flag)
    if file is not None:
        file.parent.mkdir(parents=True, exist_ok=True)
        tmp = file.with_suffix(".part")
        tmp.write_bytes(made)
        tmp.replace(file)
    return made


def changes(zz, sounds: dict, cache: Path | None = None, say=print, before: dict | None = None) -> dict:
    """{member path in ZZ_Win.dat: new bytes} for a mod's `sounds` ({sound path: WAV file}): each sound made from its
    WAV, and its description replaced in every sound bank that has one. `before`: members other build steps already
    changed ({path: bytes}); a bank among them is changed from that version."""
    from .edat import Edat
    earlier = {k.lower().replace("/", "\\"): v for k, v in (before or {}).items()}
    out: dict = {}
    made: dict = {}  # sound path -> its description
    for member, wav in sorted(sounds.items()):
        e = zz.entry(member)
        if e is None:
            # not a game rule: the WAV is named for a sound this game doesn't have (a typo, another game build)
            raise SoundError(f"{REPLACE}/{member.replace(chr(92), '/')}.wav: the game has no sound {member}")
        game = header(bytes(zz.read(e)))
        if game["flag"] != 1:
            raise SoundError(f"{member}: this kind of sound (one with a loudness track) can't be replaced yet")
        try:
            raw = Path(wav).read_bytes()
        except OSError as exc:
            raise SoundError(f"{wav}: {exc.strerror or exc}") from None
        out[e.path] = _cooked(raw, 1, cache)
        made[member] = description(out[e.path])
        h = header(out[e.path])
        say(f"sound: {member} from {Path(wav).name} ({h['frames'] / h['rate']:.1f} s, {h['channels']} channel(s), "
            f"{h['rate']} a second)")
    if not made:
        return out
    for e in zz.entries:
        p = e.path.lower()
        if not (p.startswith(BANKS) and p.endswith(".mpk")):
            continue
        raw = earlier.get(p) or bytes(zz.read(e))
        bank = Edat(raw)
        replace = {}
        for member, desc in made.items():
            d = bank.entry(member[:-len(".ess")] + ".sformat")
            if d is not None:
                replace[d.path] = desc
        if replace:
            out[e.path] = bank.to_bytes(replace)
    return out
