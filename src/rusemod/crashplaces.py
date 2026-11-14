"""The game crashes we know the cause of: the place in the game's program where each one stops, the plain reason the
apps give the player for it, and how the unit the game was making is found in the game's crash report. Bug Watch
reads the report on the player's PC (rusemod.bugwatch.read_dump) and the Launcher tells the player (the owner's item
25); nothing here is sent anywhere.

THE ONE FILE OF THE PUBLIC APPS THAT HOLDS DETAILS OF THE GAME'S PROGRAM. tools/check_public.py refuses them in every
other file and lets this one hold them (its PROGRAM_TABLE), on the owner's word of 2026-11-13. Asked "The unit the
game was making when it crashed: (a) put game program details in the public app, which your rules forbid; (b) keep
them on our private server and have the app fetch them; (c) take the unit out of the wording", he answered: "It
should tell them the unit that it was making when it crashed. So while yes, I don't want people knowing how the exact
exe code works, if their unit was crashing the game, they should be told that." and "For 25, they should also be told
why that unit made the game crash. For 25, I don't care. You can put it in the app." So only what telling the player
needs is here: no other detail of the program goes into the public apps.

Where the numbers come from: our study of the owner's fault FL-100 (2026-11-10, kept private) and the item-25 check of
2026-11-13, both made on the developers' PC from our map of the program and the crash reports held there:
- the build: the size, checksum and time stamp a crash report's module list gives the game's program: Steam build
  24670294's in 55 of the 58 crash report files held (2 name no program; 1, a research copy's with the big-packs
  game patch, is one page longer, as that patch makes it), in its program file and in eight test copies' own;
- each place: the function it is in, read in the program, and the crash reports that stopped there (below);
- the unit: in all 4 held reports made while a unit was being created (a Tiger made for the US, two Stuka copies,
  a horse squad of the owner's own), the creating step's caller kept that unit's description on the stack, every
  copy of it holding the one number; in the 4 others at known places none was kept, and no unit is said for them;
- the reasons: the same places in the players' reports of the 2026-11-10 pull of our server (5 of its 17 game
  crash reports; the other 12 stopped outside the game's own program).
"""
from __future__ import annotations

import struct

# The game's program this table is for, as a crash report's module list gives it: its size once loaded, its checksum
# and its time stamp. The program file of Steam build 24670294, and a modded copy's own with the more-buildings or
# own-squads game patches (rusemod.gamepatch: they change bytes in place and keep all three). The big-packs patch adds
# a section of its own at the end, so its copies' program is one page longer; none of the three patches' edits touches
# a place, a function or a class table below (checked 2026-11-13 on the three patch files the apps take, by their
# SHA-256). Any other build gives no reason and no unit: its places may hold other code.
BUILD = (0x1C4C000, 0x1B067D7, 0x6A7AF8D7)
BUILDS = frozenset({BUILD, (BUILD[0] + 0x1000,) + BUILD[1:]})   # Steam's, and with the big-packs game patch

# Functions a crash's chain is checked against (start, end: offsets from the program's start)
PART_BY_NAME = (0x9BF570, 0x9BF5EE)            # a model's part found by its name
TWO_AXIS = ((0x7C93E0, 0x7C947D),              # TTurretTwoAxis: its virtual function 44 (as our map numbers them),
            (0x7C92E0, 0x7C9373))              # which looks itself up, and the step that finds its parts on its model
CREATING = (0x5EAF60, 0x5EB2EF)                # TUniteComponentCreateContext's constructor: a unit being created

# The known crash places, from the program's start: (the reason's key, what the chain must hold as well: for each
# group, a place in one of its ranges). The reasons are words the apps say (words.toml crash_why_<key>).
PLACES: dict[int, tuple[str, tuple]] = {
    # the parts list of a model being made (called once, by the model instance's constructor) was empty: not one
    # part of the model could be made. Seen: a Tiger made for the US in a match with no German player (its nation's
    # models weren't loaded), two soldier figures whose skeletons weren't loaded, a horse squad's own model whose
    # skeleton wasn't loaded in a skirmish; a player's report (11-04) with the same 16 places as the Tiger's
    0x9BED79: ("made", ()),
    # a search in a sorted name list (used by many things): only with a two-axis turret looking itself up in its
    # model in the chain, which got a slot of the model's made parts that was never filled. A player's report (11-06)
    0x7F945A: ("turret", ((PART_BY_NAME,), TWO_AXIS)),
    # TTurretOneAxis's virtual function 14: a one-axis turret used a part of its model that was never made. Seen:
    # a Stuka copy made for the US, twice (its skeletons weren't loaded)
    0x7C78CC: ("turret", ()),
    # TGfxInstanceModele's virtual function 34, a model's first setup: its skeleton read for its bone count, and
    # there was none. Seen: the GMC construction truck (an old pack writer of ours had rewritten the US skeletons);
    # two reports of one player (11-06, a far-zoom token's model)
    0x9DACCE: ("setup", ()),
    # the part lookup itself: a two-axis turret's name is no part of its model at all. Read in the program only,
    # never seen in a crash report
    0x9BF58C: ("part", ()),
    # TMobileMesh's virtual function 20: a model's size box read, and it had no mesh. Seen once on the developers'
    # PC (10-04) and in a player's report
    0x1875CA: ("mesh", ()),
}
REASONS = ("made", "turret", "setup", "part", "mesh")

# The seven kinds of unit description the game makes units from, by where each kind's table of functions is (the
# first 8 bytes of every such description): TUniteDescriptor, TUniteAuSolDescriptor, TInfanterieDescriptor,
# TAvionDescriptor, TTruckDescriptor, TBatimentDescriptor, TUniteDescriptorBarycentre
UNIT_CLASSES = frozenset({0x11A8DC8, 0x11A5B28, 0x11833D8, 0x1172E38, 0x11A46E8, 0x1176E08, 0x11A5BA8})
UNIT_NUMBER = 0x18   # where a unit description holds its DescriptorId (32 bits), the number the game knows it by


def _same_build(build) -> bool:
    return tuple(build or ()) in BUILDS


def reason(build, offset: int, chain=()) -> str | None:
    """The key of the plain reason for a crash of the game's program at `offset` (from the program's start), with
    `chain`, the offsets the crashed thread's stack returns to, nearest first: one of REASONS when `build` (the
    program's size, checksum and time stamp in the crash report) is one of this table's (BUILDS) and the place is one
    we know (and its chain holds what that place needs); None otherwise."""
    if not _same_build(build):
        return None
    entry = PLACES.get(offset)
    if entry is None:
        return None
    key, needs = entry
    for group in needs:
        if not any(lo <= at < hi for at in chain for lo, hi in group):
            return None
    return key


def unit_number(build, base: int, words, read, after_call) -> int | None:
    """The number (DescriptorId) of the unit the game was creating when it crashed, or None.

    `words`: the crashed thread's stack, 8 bytes at a time from where it stopped up (nearest first); `base`: where
    the program was loaded; `read(address, size)`: the bytes the crash report kept there, None when it kept none;
    `after_call(offset)`: whether a place in the program comes right after a call (a stack word pointing there is
    where that call returns to). Read only for this table's builds (BUILDS), and only when the stack returns into the
    unit-creation step: the unit descriptions that the words above that return point at (its caller keeps the one it
    is creating), up to the next return into the step. They must all hold one number: two different ones, or none,
    and no unit is said."""
    if not _same_build(build) or after_call is None:
        return None
    lo, hi = base + CREATING[0], base + CREATING[1]
    returns = [i for i, w in enumerate(words) if lo <= w < hi and after_call(w - base)]
    if not returns:
        return None
    end = returns[1] if len(returns) > 1 else len(words)
    found = set()
    for w in words[returns[0] + 1:end]:
        head = read(w, 8)
        if head is None or len(head) != 8 or struct.unpack("<Q", head)[0] - base not in UNIT_CLASSES:
            continue
        raw = read(w + UNIT_NUMBER, 4)
        number = struct.unpack("<I", raw)[0] if raw is not None and len(raw) == 4 else 0
        if number:
            found.add(number)
    return found.pop() if len(found) == 1 else None
