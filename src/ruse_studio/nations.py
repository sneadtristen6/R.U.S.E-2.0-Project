"""The Nations tab's calls (StudioApi's NationCalls; rusemod.nations): one of the game's seven nations given a new name
and flag in the current mod, China in Italy's place say (the owner, 2026-10-08: "build the replace-a-nation feature
for this patch"; other mods have done it, his word). Data only: the game keeps seven nations.

- Its name in the lobby's nation list, and its army's name where an Operation asks which army to take: game texts
  the mod changes (text/studio-words.flash_txt.csv, the same rows All values' "Change the words..." writes).
- Its flag: the small round picture every flag list of the game shows, changed as any picture (files/replace/<its
  path>.png, rusemod.unitlook): the page fits the chosen picture to its size and shines it like the game's; its
  round shape stays the game's.
- Its units and what they say are changed where they always are: the Units tab (New unit puts a unit in its build
  menus) and each unit's page (Voice).
Seen in the game (2026-10-08, Italy made China): the new name in the lobby's list, the new flag in a match."""
from __future__ import annotations

import base64
import binascii
import hashlib
import shutil

from rusemod import nations
from rusemod.build import find_pack
from rusemod.edat import Edat


class NationCalls:
    """Mixed into StudioApi: uses its _open, _game, _mod_dir, _all_units, cache_dir, value_words and value_words_set."""

    def _nation_flag(self, ix, n: int) -> dict | None:
        """Nation `n`'s flag: {"texture": its path in ZZ_Win.dat, "width", "height", "url": the picture now (the mod's
        or the game's, a copy in the cache), "own": whether the mod has its own}; None when it can't be read."""
        from rusemod.unitlook import REPLACE, is_picture, picture_rgba
        member = nations.flag_member(ix, n)
        game = self._game()
        if member is None or game is None:
            return None
        zz = find_pack(game, "ZZ_Win.dat")
        if zz is None:
            return None
        st = zz.stat()
        arc = Edat.open(str(zz))
        try:
            entry = arc.entry(member)
            original = bytes(arc.read(entry)) if entry is not None else None
        finally:
            arc.close()
        if original is None or not is_picture(original):
            return None
        w, h, rgba = picture_rgba(original)
        mod = self._mod_dir()
        own = mod / REPLACE / (member.replace("\\", "/") + ".png") if mod is not None else None
        if own is not None and own.is_file():
            fst = own.stat()
            name = hashlib.sha1(f"{own}|{fst.st_size}|{fst.st_mtime_ns}".encode()).hexdigest()[:16] + ".png"
            copy = self.cache_dir / "nations" / "mine" / name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(own, copy)
            return {"texture": member, "width": w, "height": h, "own": True, "url": f"cache/nations/mine/{name}",
                    "game_url": self._nation_game_flag(member, st, rgba, w, h)}
        url = self._nation_game_flag(member, st, rgba, w, h)
        return {"texture": member, "width": w, "height": h, "own": False, "url": url, "game_url": url}

    def _nation_game_flag(self, member: str, st, rgba: bytes, w: int, h: int) -> str:
        """The game's own flag picture as a PNG in the cache (made once per game build): its address for the page."""
        from rusemod.dxt import png_bytes
        name = hashlib.sha1(f"{member}|{st.st_size}|{int(st.st_mtime)}".encode()).hexdigest()[:16] + ".png"
        copy = self.cache_dir / "nations" / "game" / name
        if not copy.is_file():
            copy.parent.mkdir(parents=True, exist_ok=True)
            part = copy.with_name(copy.name + ".part")
            part.write_bytes(png_bytes(rgba, w, h, channels=4))
            part.replace(copy)
        return f"cache/nations/game/{name}"

    def nations_view(self) -> dict:
        """The Nations tab: {"mod": whether a mod is picked, "nations": [{"nation": its number, "code", "name": the
        lobby's words for it in every language ([{lang, game, mine}], value_words), "name_key", "army": its army's
        ([...] or None for Japan), "army_key", "flag": _nation_flag, "units": how many units and buildings it has}]}."""
        ix = self._open()
        try:
            flags = [self._nation_flag(ix, n) for n in range(len(nations.NATIONS))]
            counts = {}
            for u in self._all_units(ix):
                counts[u.get("nation")] = counts.get(u.get("nation"), 0) + 1
        finally:
            ix.close()
        out = []
        for n, code in enumerate(nations.NATIONS):
            name_key, army_key = nations.lobby_key(n), nations.army_key(n)
            out.append({"nation": n, "code": code, "name_key": name_key, "army_key": army_key,
                        "name": self.value_words(name_key)["words"],
                        "army": self.value_words(army_key)["words"] if army_key else None,
                        "flag": flags[n], "units": counts.get(n, 0)})
        return {"mod": self._mod_dir() is not None, "nations": out}

    def nation_words_set(self, nation: int, which: str, texts: dict) -> dict:
        """Give nation `nation` new words in the current mod: `which` "name" (the lobby's nation list) or "army" (its
        army, where an Operation asks which army to take); `texts` {language: words} (a language left empty keeps
        the game's). Returns nations_view()."""
        n = nations.check(nation)
        key = {"name": nations.lobby_key(n), "army": nations.army_key(n)}.get(which)
        if key is None:
            # not a game rule: the game's texts have no army name for Japan (no NAT_NAME_6), and nothing else is offered
            raise nations.NationError("Japan's army has no name to change in the game." if which == "army"
                                      else f"There's nothing called {which!r} to change.")
        if self._mod_dir() is None:
            raise nations.NationError("Pick or make a mod first: the new name is saved in it.")
        self.value_words_set(key, {str(k): str(v or "") for k, v in (texts or {}).items()})
        return self.nations_view()

    def nation_flag_set(self, nation: int, picture: str) -> dict:
        """Use `picture` (a PNG, as a data: address or base64, the flag's own size: the page fits and shines it) as
        nation `nation`'s flag in the current mod (files/replace/<the flag's path>.png; its round shape stays the
        game's). Returns nations_view()."""
        from rusemod.png import read_png
        from rusemod.unitlook import REPLACE
        n = nations.check(nation)
        mod = self._mod_dir()
        if mod is None:
            raise nations.NationError("Pick or make a mod first: the flag goes into it.")
        ix = self._open()
        try:
            flag = self._nation_flag(ix, n)
        finally:
            ix.close()
        if flag is None:
            # not a game rule: the Studio found no flag picture it can read for this nation
            raise nations.NationError("The Studio can't read this nation's flag in the game's files.")
        try:
            data = base64.b64decode(str(picture).split(",", 1)[-1], validate=True)
            w, h, _px = read_png(data)
        except (ValueError, TypeError, binascii.Error):
            raise nations.NationError("The flag picture couldn't be read (not a PNG).") from None
        if (w, h) != (flag["width"], flag["height"]):
            # not a game rule: a picture is written at the size of the one it replaces (rusemod.unitlook)
            raise nations.NationError(f"The flag picture is {w} x {h}; the game's flags are {flag['width']} x "
                                      f"{flag['height']}.")
        to = mod / REPLACE / (flag["texture"].replace("\\", "/") + ".png")
        with self._saving:
            to.parent.mkdir(parents=True, exist_ok=True)
            part = to.with_name(to.name + ".part")
            part.write_bytes(data)
            part.replace(to)
        return self.nations_view()

    def nation_reset(self, nation: int, what: str = "all") -> dict:
        """Give nation `nation` back what the game has: `what` "flag", "name", "army" or "all". Returns nations_view()."""
        from rusemod.unitlook import REPLACE
        n = nations.check(nation)
        mod = self._mod_dir()
        if mod is None:
            return self.nations_view()
        if what in ("flag", "all"):
            ix = self._open()
            try:
                member = nations.flag_member(ix, n)
            finally:
                ix.close()
            if member:
                with self._saving:
                    (mod / REPLACE / (member.replace("\\", "/") + ".png")).unlink(missing_ok=True)
        for which in ("name", "army"):
            key = nations.lobby_key(n) if which == "name" else nations.army_key(n)
            if key and what in (which, "all"):
                game = {w["lang"]: w["game"] or "" for w in self.value_words(key)["words"]}
                self.value_words_set(key, game)  # the game's words in every language: the row is taken out
        return self.nations_view()
