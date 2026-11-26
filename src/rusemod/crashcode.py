"""A crash code for players without Bug Watch: twelve letters and digits the Launcher shows after a game it started
crashed, for the player to tell us.

The owner, 2026-11-14: "they should be given some sort of code that they can tell me that still tells us why it
crashed, but maybe not be as specific if they don't select bug watch, because they're obviously choosing not to enable
that feature. So they shouldn't get the full benefits of it." So the code is made on the PC from where the game
stopped, and from nothing else: the kind of stop (the crash report's own code, as one of KINDS), the module it stopped
in (the game's own program, or a short mark made from that module's name), the build of the game's program (a short
mark made from its size, checksum and time stamp), and the place in that module. Those are read from the game's own
crash report on the PC (rusemod.bugwatch.read_dump), as Bug Watch reads them. Never in it: the chain, the unit, the
mods, the map, anything of the player's. The Launcher sends the code nowhere: the player tells it to us if they want
to, and we read it (read) and look the place up in our own list of the crashes we know, which stays with us. A crash we
don't know yet still gets a code, and the code still says where it stopped once we know that place.

This file holds no number of the game: what it packs comes from the crash report on the player's PC.

    2 bits   the code's version (1)        4 bits  the kind of stop (KINDS; 0: another one)
    8 bits   the module (0: the game's program; 255: none; else module_mark)
    6 bits   the build of the game's program (0: not in the report; else build_mark)
    32 bits  the place, from the start of its module
    8 bits   a check (a CRC-8, POLY): a code with any one letter typed wrong is always refused, as are most others

Sixty bits, written as twelve Crockford letters and digits in three groups: 8K2M-4TQ7-X0PA.

Checked our_tools.json: none of its tools makes a short code for a player to tell us; this file reads no program and no
crash report itself, it packs the few fields rusemod.bugwatch.read_dump read.
"""
from __future__ import annotations

import hashlib
import re

from .lock import _B32, _B32_READ

VERSION = 1
POLY = 0x107   # x^8 + x^2 + x + 1: one letter is 5 bits, and a CRC of degree 8 catches every error that short
# The kinds of stop, by the code a crash report gives (Windows' own codes, and the game's own script-error stop, 0x29a)
KINDS = (0xC0000005, 0x29A, 0xE06D7363, 0xC0000409, 0xC00000FD, 0xC0000374, 0x80000003, 0xC000001D, 0xC0000094,
         0xC0000096, 0xC0000006, 0xC0000017, 0xC000008E, 0xC0000008, 0x40000015)
GAME = "ruse.exe"   # the game's program, by its file name (a crash report's module list)
NO_MODULE = 255     # the place is in no module the report lists
LENGTH = 12


def module_mark(name: str) -> int:
    """The mark of a module other than the game's program: 1 to 254, from its file name (any case)."""
    return 1 + hashlib.sha256(str(name).lower().encode("utf-8")).digest()[0] % 254


def build_mark(build) -> int:
    """The mark of a build of the game's program: 1 to 63, from its size, checksum and time stamp; 0 for none."""
    if not build or len(build) != 3:
        return 0
    text = ":".join(str(int(x)) for x in build).encode("ascii")
    return 1 + int.from_bytes(hashlib.sha256(text).digest()[:2], "big") % 63


def _remainder(value: int) -> int:
    """`value` as a polynomial over two digits, divided by POLY: what is left (below 256)."""
    for bit in range(value.bit_length() - 1, 7, -1):
        if value >> bit & 1:
            value ^= POLY << (bit - 8)
    return value


def make(found: dict) -> str | None:
    """The crash code of a crash report as read_dump reads it ("code", "module", "offset", and "build": the size,
    checksum and time stamp of the game's program when the report lists it), or None when it can't be read."""
    try:
        code, offset = int(str(found["code"]), 16), int(str(found["offset"]), 16)
        module = str(found.get("module") or "?")
    except (KeyError, TypeError, ValueError):
        return None
    kind = KINDS.index(code) + 1 if code in KINDS else 0
    if module.lower() == GAME:
        mark = 0
    elif module in ("?", "_"):   # (read_dump writes a place in no module as "?" made safe: "_")
        mark = NO_MODULE
    else:
        mark = module_mark(module)
    payload = (VERSION << 50) | (kind << 46) | (mark << 38) | (build_mark(found.get("build")) << 32) | \
        (offset & 0xFFFFFFFF)
    value = payload << 8
    value |= _remainder(value)   # (the whole code then divides by POLY)
    chars = "".join(_B32[(value >> (5 * (LENGTH - 1 - i))) & 31] for i in range(LENGTH))
    return "-".join(chars[i:i + 4] for i in range(0, LENGTH, 4))


def read(text: str) -> dict | None:
    """What a crash code says, or None when it isn't one (a letter too many or too few, one that doesn't belong, a
    check that doesn't fit): {"version", "kind": the crash report's code or None for another one, "module": "game",
    "none" or its mark, "build": the mark of the game's program's build (0: not in the report), "offset"}. Spaces,
    dashes and the letter case don't count; I and L read as 1, O as 0."""
    chars = [c for c in str(text or "").upper() if not re.match(r"[\s_-]", c)]
    if len(chars) != LENGTH or any(c not in _B32_READ for c in chars):
        return None
    value = 0
    for c in chars:
        value = value << 5 | _B32_READ[c]
    payload = value >> 8
    if _remainder(value) != 0 or payload >> 50 != VERSION:
        return None
    kind, mark = (payload >> 46) & 0xF, (payload >> 38) & 0xFF
    return {"version": VERSION, "kind": KINDS[kind - 1] if kind else None,
            "module": "game" if mark == 0 else "none" if mark == NO_MODULE else mark,
            "build": (payload >> 32) & 0x3F, "offset": payload & 0xFFFFFFFF}
