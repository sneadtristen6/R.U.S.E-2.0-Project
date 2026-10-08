"""The game's seven nations, as the Studio's Nations tab gives one a new name and flag (one of them replaced by
another nation, China in Italy's place say: data only, the game keeps seven).

What a nation's name and flag are in the game's files:
- its name in the lobby's nation list: the `flash_txt` text NATION_<n> (Japan's is NATION_7: NATION_6 is the lobby's
  Random);
- its army's name where an Operation asks which army to take: NAT_NAME_<n> (Japan has none);
- its flag: one small round picture (28 x 28, its shape in its alpha) that every flag list of the game points at (the
  loading screen's, the players' labels', the replays'): its FileName in `MultiplayerDataBag.NationalityIcons[n]`.
  A mod changes it as any picture (MOD_FORMAT §7, files/replace: rusemod.unitlook).
The lobby's own nation button draws its flags in its menu file (a frame each), not from this picture: it stays the
game's. Seen in the game (2026-10-08, Italy made China): the new name in the lobby's list, the new flag beside the
player's name in a match."""
from __future__ import annotations

NATIONS = ("usa", "germany", "uk", "france", "italy", "ussr", "japan")  # Nationalite 0..6 (rusemod.unitcheck)
FLAG_LIST = ("$/GFX/Everything/MultiplayerDataBag", "NationalityIcons")  # every flag list holds these same pictures
TEXT_TABLE = "flash_txt"


class NationError(ValueError):
    pass


def check(n) -> int:
    """`n` as a nation's number (0 to 6)."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        raise NationError(f"{n!r} isn't a nation's number") from None
    if not 0 <= n < len(NATIONS):
        # not a game rule: the seven nations the game has
        raise NationError(f"there's no nation {n}: the game has {len(NATIONS)}, 0 to {len(NATIONS) - 1}")
    return n


def lobby_key(n) -> str:
    """The text the lobby's nation list shows for nation `n` (NATION_6 is Random, so Japan's is NATION_7)."""
    n = check(n)
    return f"NATION_{n if n < 6 else 7}"


def army_key(n) -> str | None:
    """The text naming nation `n`'s army where an Operation asks which army to take; None for Japan (it has none)."""
    n = check(n)
    return f"NAT_NAME_{n}" if n < 6 else None


def flag_file(ix, n) -> str | None:
    """Nation `n`'s flag picture as the game's data names it (its FileName, DataDir:...png), read from the index
    `ix` (rusemod.index.Index); None when the index has no such list."""
    n = check(n)
    holder, prop = FLAG_LIST
    row = ix.db.execute("""SELECT v.text FROM object o JOIN ref r ON r.src = o.id AND r.path = ?
                           JOIN value v ON v.object = r.dst AND v.path = 'FileName'
                           WHERE o.address = ?""", (f"{prop}[{n}]", holder)).fetchone()
    return row[0] if row and row[0] else None


def flag_member(ix, n) -> str | None:
    """Nation `n`'s flag picture as a texture path in ZZ_Win.dat (Italy's: gen/ww2/res2d/interface/flags/flag_ita.tgv,
    with backslashes), or None."""
    from .unitlook import card_member
    name = flag_file(ix, n)
    return card_member(name) if name else None
