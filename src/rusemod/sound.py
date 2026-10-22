"""Sounds and music: the game's sound files played and made, the game's songs and where each one plays, and a mod's
own sounds put in by the build.

A mod replaces one of the game's sounds with a WAV at files/replace/<the sound's path in ZZ_Win.dat>.wav (the way a
texture is replaced by files/replace/<texture>.png): files/replace/gen_sound/ww2/sons/atp_music/battle1.ess.wav. The
build makes the game's kind of file from it, and the small description the game reads first, in every sound bank
that has one for that sound.

Reading follows RugnirViking's moddingSuite (its EssReader; GPL 3.0, its README says), widened to any number of
channels; the writer is ours. What `encode` makes, `decode` plays back sample for sample (tests/test_sound.py). Heard in the game
(the sound tests, 2026-10-07): the main menu song, the songs of battle lists 1 and 2 and the Sherman's move lines,
each replaced this way, and new songs under names of their own in lists 1 and 2; the rest (the third list,
missions' songs, jingles, other voices) not tried yet.
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
    """The description the game reads before a sound, for a sound of the kind music and most voices are (flag 1),
    and for the 6-channel map backgrounds (flag 0 with an empty loudness section, as every one of the game's own has).
    The other flag-0 sounds carry a loudness track whose making isn't known yet: refused."""
    h = header(b)
    ch = h["channels"]
    if h["flag"] == 0 and ch == 6:
        return struct.pack("<HBBBBHIIIIIIHBB", 0x0106, 0, ch, 0, 2 * ch, h["rate"], h["frames"], 44, len(b),
                           h["loop_start"], h["loop_end"], 0, 0, 10, 5)
    if h["flag"] != 1:
        raise SoundError("this kind of sound (one with a loudness track) can't be made yet")
    return struct.pack("<HBBBBHIIIII", 0x0106, 1, ch, 0, 2 * ch, h["rate"], h["frames"], 2 * ch, len(b),
                       h["loop_start"], h["loop_end"])


# --- the loudness track of the short effects (flag 0: guns, impacts, engines, the ruse cards...) ---
# The game uses a window's track only to rank which sounds keep a voice when too many play at once, never for how
# loud a sound plays: one byte of five, the further away the sound (the more its high notes are cut), the lower the
# byte it takes, so byte k is the window's level below (k + 1) x 8,820 Hz. How the game's own tracks were made isn't
# known exactly; measured on 30 of them, the bytes follow the level in a straight line (byte = TRACK_SLOPE[k] x the
# level below that cutoff), which this follows. Every one of the game's 230 tracks has ceil(frames / step) windows,
# the step 1024 at 11,025 a second, 2048 at 22,050, 4096 at 44,100 and 48,000.
TRACK_SLOPE = (0.00977, 0.01187, 0.01284, 0.01336, 0.01365)


def track_step(rate: int) -> int:
    """The track's window, in samples, for a sound at `rate` (as every one of the game's tracks has it)."""
    return 1024 if rate <= 16000 else 2048 if rate <= 32000 else 4096


def loudness_track(pcm, channels: int, rate: int, step: int | None = None) -> bytes:
    """Five rising bytes per window of `step` samples: the window's level below 8.8, 17.6, 26.5, 35.3 and 44.1 kHz
    (one-pole low-pass filters; a cutoff at or past half the rate is the whole sound)."""
    import math
    step = step or track_step(rate)
    frames = len(pcm) // channels
    mono = [sum(pcm[i * channels:(i + 1) * channels]) / channels for i in range(frames)]
    coefs = []
    for k in range(5):
        cut = (k + 1) * 8820
        coefs.append(None if cut >= rate / 2 else 1.0 - math.exp(-2 * math.pi * cut / rate))
    out = bytearray()
    state = [0.0] * 5
    for start in range(0, frames, step):
        sums = [0.0] * 5
        n = min(step, frames - start)
        for x in mono[start:start + n]:
            for k, a in enumerate(coefs):
                if a is None:
                    y = x
                else:
                    state[k] += a * (x - state[k])
                    y = state[k]
                sums[k] += y * y
        level = 0
        for k in range(5):
            v = int(round(TRACK_SLOPE[k] * math.sqrt(sums[k] / n)))
            level = max(level, min(255, v))   # rising, as every one of the game's is
            out.append(level)
    return bytes(out)


def description_like(game_desc: bytes, made: bytes) -> bytes:
    """The description of a sound made to stand in for one of the game's with a loudness track (flag 0): the game's
    own field 12, the new sound's format, length, loop and size, and a loudness track made from the new sound."""
    h = header(made)
    if len(game_desc) < 36 or game_desc[2] != 0:
        return description(made)
    ch = h["channels"]
    step = 0 if ch == 6 else track_step(h["rate"])
    if step:
        pcm, _ = decode(made)
        track = loudness_track(pcm, ch, h["rate"], step)
    else:
        track = b""   # the maps' 6-channel backgrounds: every one of the game's has an empty track
    field12 = struct.unpack_from("<I", game_desc, 12)[0]
    return struct.pack("<HBBBBHIIIIIIHBB", 0x0106, 0, ch, 0, 2 * ch, h["rate"], h["frames"], field12, len(made),
                       h["loop_start"], h["loop_end"], len(track) // 5, step, 10, 5) + track


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


# --- a mod's new songs: files/music/list<N>/<name>.wav, a new song in battle list N (heard in the game in lists 1 and
# 2: the new-song test, 2026-10-07) ---
NEW_MUSIC = "files/music"
LISTS = ("list1", "list2", "list3")  # the three lists battles play from, in the data's order
B = "\\"
MUSIC_DIR = B.join(["gen_sound", "ww2", "sons", "atp_music"]) + B   # where the game keeps its songs
MUSIC_FILES = B.join(["WW2", "Sons", "ATP_Music"]) + B              # how its data names them


def safe_name(name: str) -> str:
    """A new song's name as files and the data can hold it: letters, digits and _ only ("" when none are left)."""
    import re
    import unicodedata
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", plain).strip("_")[:40]


def new_song(mod_id: str, list_name: str, name: str) -> dict:
    """What the build makes of files/music/<list>/<name>.wav: the song's path in ZZ_Win.dat (`member`), the file name
    its data object gives (`file`), that object's name (`object`) and the list (`index`, 0 to 2)."""
    stem = f"{mod_id}_{safe_name(name)}"
    return {"member": (MUSIC_DIR + stem + ".ess").lower(), "file": MUSIC_FILES + stem + ".ogg",
            "object": "Music_" + safe_name(f"{mod_id}_{name}"), "index": LISTS.index(list_name)}


def mod_new_songs(folder: Path, mod_id: str) -> dict:
    """{song path in ZZ_Win.dat: (its WAV, new_song())} from a mod's files/music/list<N>/<name>.wav."""
    root = Path(folder) / NEW_MUSIC
    out: dict = {}
    for list_name in LISTS:
        for f in sorted((root / list_name).glob("*.wav")) if (root / list_name).is_dir() else []:
            if safe_name(f.stem):
                song = new_song(mod_id, list_name, f.stem)
                out[song["member"]] = (f, song)
    return out


def new_songs_rndf(songs: dict) -> str:
    """The data a mod's new songs need, as .rndf: each a new TSoundStream naming its file, added to its list."""
    lines = []
    for _member, (_wav, s) in sorted(songs.items()):
        lines.append(f"{s['object']} is TSoundStream ( FileName = path('{s['file']}') )")
        lines.append(f"patch {PLAYLISTS}:PlayLists[{s['index']}] ( Musics += [~/{s['object']}] )")
    return "\n".join(lines) + ("\n" if lines else "")


# --- a map's background sound (not tried in the game yet): maps/<map>/background_<1..3>.wav, its three layers, and
# maps/<map>/sound.toml, `background` = another of the game's background sounds for this map ---
AMBIENCE_DIR = B.join(["gen_sound", "ww2", "sons", "sfx_env"]) + B    # where the game keeps its map backgrounds
AMBIENCE_FILES = B.join(["WW2", "Sons", "SFX_ENV"]) + B               # how the maps' data names them
# a background holds three stereo layers (channels 1-2, 3-4, 5-6); the map's settings give the game three volumes for
# them (Hq, Air, Decor), but which layer each is, and when the game plays which, isn't known yet
LAYERS = (1, 2, 3)


def map_config_member(map_name: str) -> str:
    """The map's own settings file in the unit-data pack, which names its background sound."""
    return B.join(["genglad", "patchable", "map", map_name.lower(), "mapconstante.cpp.gladndfbin"])


def ambience_member(file_name: str) -> str:
    """The background's path in ZZ_Win.dat for the name the map's data gives it (some write DataDir:\\ in front)."""
    name = file_name.split(":", 1)[1].lstrip(B) if ":" in file_name else file_name
    return member_of(name)


def mod_ambience(folder: Path, mod_id: str) -> dict:
    """{map (as its folder under maps/ spells it): {"layers": {n: WAV}, "use": another background or None, "mod"}}
    from a mod's maps/<map>/background_<n>.wav and maps/<map>/sound.toml."""
    import tomllib
    out: dict = {}
    root = Path(folder) / "maps"
    for d in sorted(root.iterdir()) if root.is_dir() else []:
        if not d.is_dir():
            continue
        layers = {n: d / f"background_{n}.wav" for n in LAYERS if (d / f"background_{n}.wav").is_file()}
        use = None
        if (d / "sound.toml").is_file():
            try:
                use = tomllib.loads((d / "sound.toml").read_text(encoding="utf-8")).get("background")
            except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
                raise SoundError(f"maps/{d.name}/sound.toml: {exc}") from None
            if use is not None and not isinstance(use, str):
                raise SoundError(f"maps/{d.name}/sound.toml: background must be a background sound's name")
        if layers or use:
            out[d.name] = {"layers": layers, "use": use, "mod": mod_id}
    return out


def _background(raw: bytes):
    """(the settings file, the sound stream object it names as the background, that stream's FileName)."""
    from .ndf import Ndf, local_ref
    nd = Ndf(raw)
    for o in nd.objects:
        if nd.classes[o.cls] != "TSoundMapConfig":
            continue
        ref = next((v for pi, v in o.props if nd.prop_name(pi) == "AmbianceDecor_MultiPiste"), None)
        idx = local_ref(ref) if ref is not None else None
        if idx is None:
            continue
        name = next((v for pi, v in nd.objects[idx].props if nd.prop_name(pi) == "FileName"), None)
        if name is not None and name.tc in (0x07, 0x1C):
            return nd, idx, nd.strings[struct.unpack("<I", name.payload)[0]]
    return None, None, None


def background_of(raw: bytes) -> str | None:
    """The background sound a map's settings file names (its FileName), or None."""
    return _background(raw)[2]


def with_background(raw: bytes, file_name: str) -> bytes:
    """The map's settings file naming `file_name` as its background sound."""
    from .ndf import Value
    nd, idx, _old = _background(raw)
    if nd is None:
        raise SoundError("this map's settings name no background sound")
    at = nd.string_index(file_name)
    if at is None:
        at = nd.add_string(file_name)
    obj = nd.objects[idx]
    obj.props = [(pi, Value(v.tc, struct.pack("<I", at)) if nd.prop_name(pi) == "FileName" else v)
                 for pi, v in obj.props]
    return nd.to_member(compress=bool(struct.unpack_from("<I", raw, 12)[0] & 0x80))


def compose(base, base_channels: int, layers: dict) -> array:
    """A 6-channel background from the map's current one (`base`, interleaved; None when every layer is new) and new
    stereo layers ({n: 16-bit stereo PCM}): each layer in its own pair of channels, all as long as the longest, a
    shorter one repeated (the game loops the whole)."""
    frames = max([len(p) // 2 for p in layers.values()] + ([len(base) // base_channels] if base is not None else []))
    out = array("h", bytes(12 * frames))
    for n in LAYERS:
        if n in layers:
            src, ch, pair = layers[n], 2, (0, 1)
        elif base is not None:
            src, ch, pair = base, base_channels, (2 * (n - 1), 2 * (n - 1) + 1)
        else:
            continue
        length = len(src) // ch
        if length == 0:
            continue
        for c in (0, 1):
            col = src[pair[c]::ch]
            dst = 2 * (n - 1) + c
            for start in range(0, frames, length):
                part = col[:min(length, frames - start)]
                out[6 * start + dst:6 * (start + len(part)) + dst - 5:6] = part
    return out


def ambience_changes(read_config, zz, maps: dict, cache: Path | None = None, say=print, before: dict | None = None):
    """For the mods' map backgrounds ({map: mod_ambience entry}): ({settings file member: new bytes} for the unit-data
    pack, {bank: new bytes} and {new member: bytes} for ZZ_Win.dat). `read_config(member)`: a settings file's bytes
    as the build has it so far (None when the game has no such map). A new background is made from the layers given
    and the map's current one, cooked once (the build cache), and its description added to every bank that holds
    the game's backgrounds' (each map's own bank holds them all)."""
    from .edat import Edat
    earlier = {k.lower().replace("/", "\\"): v for k, v in (before or {}).items()}
    configs: dict = {}
    added: dict = {}
    descs: dict = {}
    for map_name, entry in sorted(maps.items()):
        member = map_config_member(map_name)
        raw = read_config(member)
        if raw is None:
            # not a game rule: the folder is named for a map this game (and the mods) haven't got
            raise SoundError(f"maps/{map_name}: no map {map_name} with a background sound in this game")
        current = background_of(raw)
        target = entry["use"] or current
        base_member = ambience_member(target or "")
        e = zz.entry(base_member) if target else None
        if e is None:
            # not a game rule: sound.toml names a background this game hasn't got
            raise SoundError(f"maps/{map_name}: no background sound {target} in this game")
        if entry["layers"]:
            base_raw = bytes(zz.read(e))
            wavs = {n: Path(w).read_bytes() for n, w in sorted(entry["layers"].items())}
            key = hashlib.sha256(base_raw + b"".join(bytes([n]) + hashlib.sha256(w).digest() for n, w in wavs.items())
                                 + bytes([0, CODEC_VERSION])).hexdigest()
            file = Path(cache) / "sound" / f"{key}.ess" if cache is not None else None
            if file is not None and file.is_file():
                made = file.read_bytes()
            else:
                layers = {}
                for n, w in wavs.items():
                    pcm, ch, rate = read_wav(w)
                    if (ch, rate) != (2, 48000):
                        raise SoundError(f"maps/{map_name}/background_{n}.wav: {ch} channel(s) at {rate} a second; a "
                                         f"background's layer is stereo at 48,000 a second (the Studio makes it so)")
                    layers[n] = pcm
                base = None
                if len(wavs) < len(LAYERS):  # the layers not given stay the map's current ones
                    base, h = decode(base_raw)
                    if (h["channels"], h["rate"]) != (6, 48000):
                        raise SoundError(f"{target}: not a background of three layers")
                made = encode(compose(base, 6, layers), 6, 48000, flag=0)
                if file is not None:
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.with_suffix(".part").write_bytes(made)
                    file.with_suffix(".part").replace(file)
            stem = f"{entry['mod']}_{safe_name(map_name)}"
            new_member = (AMBIENCE_DIR + stem + ".ess").lower()
            if zz.entry(new_member) is not None:
                # not a game rule: the name is taken (two mods, or a mod and the game)
                raise SoundError(f"maps/{map_name}: {new_member} is already in the game")
            added[new_member] = made
            descs[new_member[:-len(".ess")] + ".sformat"] = description(made)
            target = AMBIENCE_FILES + stem + ".wav"
            say(f"background sound: {map_name}, layer(s) {', '.join(str(n) for n in sorted(wavs))} of its own "
                f"({header(made)['frames'] / 48000:.1f} s)")
        else:
            say(f"background sound: {map_name} uses {target}")
        if target != current:
            configs[member] = with_background(raw, target)
    banks: dict = {}
    if descs:
        for e in zz.entries:
            p = e.path.lower()
            if not (p.startswith(BANKS) and p.endswith(".mpk")):
                continue
            raw = earlier.get(p) or bytes(zz.read(e))
            bank = Edat(raw)
            if any(x.path.lower().startswith(AMBIENCE_DIR) for x in bank.entries):
                banks[e.path] = bank.to_bytes(None, descs)
    return configs, banks, added


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


def new_song_changes(zz, songs: dict, cache: Path | None = None, say=print, before: dict | None = None):
    """({bank's path in ZZ_Win.dat: new bytes}, {new member: bytes}) for a mod's new songs (mod_new_songs): each song
    made from its WAV as a new file of ZZ_Win.dat, and its description added to every bank that holds the game's
    music's (where the game keeps its songs' descriptions). `before`: banks other steps changed ({path: bytes})."""
    from .edat import Edat
    earlier = {k.lower().replace("/", "\\"): v for k, v in (before or {}).items()}
    added: dict = {}
    descs: dict = {}
    for member, (wav, s) in sorted(songs.items()):
        if zz.entry(member) is not None:
            # not a game rule: the name is taken (two mods, or a mod and the game, with the same song file)
            raise SoundError(f"{NEW_MUSIC}/{LISTS[s['index']]}/{Path(wav).name}: {member} is already in the game")
        try:
            raw = Path(wav).read_bytes()
        except OSError as exc:
            raise SoundError(f"{wav}: {exc.strerror or exc}") from None
        made = _cooked(raw, 1, cache)
        added[member] = made
        descs[member[:-len(".ess")] + ".sformat"] = description(made)
        h = header(made)
        say(f"new song: {s['object']} in battle list {s['index'] + 1} from {Path(wav).name} "
            f"({h['frames'] / h['rate']:.1f} s, {h['channels']} channel(s), {h['rate']} a second)")
    banks: dict = {}
    if not descs:
        return banks, added
    for e in zz.entries:
        p = e.path.lower()
        if not (p.startswith(BANKS) and p.endswith(".mpk")):
            continue
        raw = earlier.get(p) or bytes(zz.read(e))
        bank = Edat(raw)
        if not any(x.path.lower().startswith(MUSIC_DIR) for x in bank.entries):
            continue
        banks[e.path] = bank.to_bytes(None, descs)
    return banks, added


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
        try:
            raw = Path(wav).read_bytes()
        except OSError as exc:
            raise SoundError(f"{wav}: {exc.strerror or exc}") from None
        # made the game's sound's own kind: flag 1 (music, voices) or flag 0 (effects, with a loudness track that
        # description_like makes from the new sound, bank by bank, below)
        out[e.path] = _cooked(raw, game["flag"], cache)
        made[member] = description(out[e.path]) if game["flag"] == 1 else None
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
                if desc is None:   # a flag-0 sound: its description made from the game's and the new sound
                    new = out[zz.entry(member).path]
                    desc = description_like(bytes(bank.read(d)), new)
                replace[d.path] = desc
        if replace:
            out[e.path] = bank.to_bytes(replace)
    return out


# --- how loud a mod plays each of the game's sounds ---
# The game can't play a sound louder than its own settings say: a sound's volume, the volume group it hangs from and
# the voice playing it each go from 0 to 1 at most, and the 45 shared settings most sounds take their volume from are
# in a pack the build doesn't write. So a sound's own volume here is its own sound made louder or quieter: every one of the game's settings for it
# (distance, its group, the game's own volume options) stays as it was.
VOLUMES = "files/sound/volume.toml"
MOST_VOLUME = 200       # not a game rule: the Studio's slider goes to twice the game's (louder is limited, below)
VOLUME_VERSION = 1      # part of the cache key, with CODEC_VERSION
_LIMIT_FROM = 24575     # 0.75 of full scale: louder than this is rounded off smoothly instead of cut (no crackle)
_LIMIT_TOP = 30934      # and never past -0.5 dBFS: the codec's own small error near the top would otherwise reach the
                        # rail (seen: 101 samples clipped at 150% of a cannon shot with the limit at full scale)


def volume_key(member: str) -> str:
    """How volume.toml names a sound: its path in ZZ_Win.dat with forward slashes, lower case."""
    return member.replace("\\", "/").lower()


def mod_volumes(folder: Path) -> dict:
    """{sound path in ZZ_Win.dat (backslashes, lower case): percent} from a mod's files/sound/volume.toml:

        [volume]
        "gen_sound/ww2/sons/sfx_ruse/sfx_tir/sfx_tir_obusap_leger_01.ess" = 150

    0 is silent, 100 the game's own (left out), up to MOST_VOLUME."""
    import tomllib
    f = Path(folder) / VOLUMES
    if not f.is_file():
        return {}
    try:
        table = tomllib.loads(f.read_text(encoding="utf-8")).get("volume", {})
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise SoundError(f"{VOLUMES}: {exc}") from None
    if not isinstance(table, dict):
        raise SoundError(f"{VOLUMES}: [volume] should be a table of sound = percent")
    out = {}
    for key, v in table.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= MOST_VOLUME:
            # not a game rule: the slider's range (louder than twice the game's would mostly be rounded off)
            raise SoundError(f"{VOLUMES}: {key} = {v!r}: a volume is a percent from 0 to {MOST_VOLUME}")
        key = key.strip().replace("/", "\\").lower()
        if not key.endswith(".ess"):
            raise SoundError(f"{VOLUMES}: {key}: name a sound by its path in ZZ_Win.dat, ending .ess")
        if round(v) != 100:
            out[key] = int(round(v))
    return out


def louder(pcm, percent: int) -> array:
    """16-bit PCM at `percent` of its volume. Quieter: each sample scaled. Louder: what passes 0.75 of full scale is
    rounded off smoothly towards -0.5 dBFS (a soft limiter), so nothing is cut flat."""
    import math
    g = percent / 100.0
    out = array("h", bytes(2 * len(pcm)))
    top = _LIMIT_TOP - _LIMIT_FROM
    for i, x in enumerate(pcm):
        y = x * g
        if g > 1.0 and abs(y) > _LIMIT_FROM:
            m = _LIMIT_FROM + top * math.tanh((abs(y) - _LIMIT_FROM) / top)
            y = m if y > 0 else -m
        out[i] = max(-32768, min(32767, int(round(y))))
    return out


def with_volume(raw: bytes, percent: int, cache: Path | None = None) -> bytes:
    """A game sound (the .ess bytes) made again at `percent` of its volume: the same kind, channels, rate, length and
    loop as the game's (its header's loop words are kept)."""
    key = hashlib.sha256(raw + struct.pack("<HBB", percent, CODEC_VERSION, VOLUME_VERSION)).hexdigest()
    file = Path(cache) / "sound" / "volume" / f"{key}.ess" if cache is not None else None
    if file is not None and file.is_file():
        return file.read_bytes()
    pcm, h = decode(raw)
    made = bytearray(encode(louder(pcm, percent), h["channels"], h["rate"], h["flag"]))
    made[12:20] = raw[12:20]   # the game's loop start and end (encode writes 0 .. the last sample)
    made = bytes(made)
    if file is not None:
        file.parent.mkdir(parents=True, exist_ok=True)
        tmp = file.with_suffix(".part")
        tmp.write_bytes(made)
        tmp.replace(file)
    return made


def volume_description(desc: bytes, made: bytes, percent: int) -> bytes:
    """A sound's description (as a bank holds it) for the sound made again by with_volume: its file size, and for a
    sound with a loudness track (flag 0), the track's bytes times the same amount (at most 255): they follow the
    sound's level in a straight line (see the loudness track, above), so scaling them is the closest known."""
    out = bytearray(desc)
    struct.pack_into("<I", out, 16, len(made))
    if len(desc) >= 36 and desc[2] == 0:
        count = struct.unpack_from("<I", desc, 28)[0]
        g = percent / 100.0
        for i in range(36, min(len(out), 36 + 5 * count)):
            out[i] = min(255, int(round(desc[i] * g)))
    return bytes(out)


def volume_changes(zz, volumes: dict, cache: Path | None = None, say=print, before: dict | None = None) -> dict:
    """{member path in ZZ_Win.dat: new bytes} for a mod's `volumes` ({sound path: percent}): each sound made again
    at its volume, from the mod's own sound when an earlier step replaced it (`before`, as for `changes`), and its
    description updated in every sound bank that has one."""
    from .edat import Edat
    earlier = {k.lower().replace("/", "\\"): v for k, v in (before or {}).items()}
    out: dict = {}
    made: dict = {}   # sound path -> (its new bytes, percent)
    for member, percent in sorted(volumes.items()):
        e = zz.entry(member)
        if e is None:
            # not a game rule: the mod names a sound this game build doesn't have (a typo, another game build)
            raise SoundError(f"{VOLUMES}: the game has no sound {volume_key(member)}")
        raw = earlier.get(e.path.lower()) or bytes(zz.read(e))
        out[e.path] = with_volume(raw, percent, cache)
        made[member] = (out[e.path], percent)
        say(f"sound volume: {volume_key(member)} at {percent}%")
    if not made:
        return out
    for e in zz.entries:
        p = e.path.lower()
        if not (p.startswith(BANKS) and p.endswith(".mpk")):
            continue
        raw = earlier.get(p) or bytes(zz.read(e))
        bank = Edat(raw)
        replace = {}
        for member, (new, percent) in made.items():
            d = bank.entry(member[:-len(".ess")] + ".sformat")
            if d is not None:
                replace[d.path] = volume_description(bytes(bank.read(d)), new, percent)
        if replace:
            out[e.path] = bank.to_bytes(replace)
    return out
