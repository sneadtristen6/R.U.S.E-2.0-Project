"""A unit's role, and what each of its weapons can hit (StudioApi's RoleCalls), from a player's report: a fighter-bomber
given a bomber's carpet bombs flew to its target and dropped nothing (2026-10-14). The owner: "even though it doesn't
make much sense, it should still be a thing": any weapon on any unit, a tank shooting planes with its own rounds.

What the game ties together (seen in the game in tests T50-T52, 2026-10-14):

- A plane's role is its CategoryVolant: 1 fighter, 2 fighter-bomber, 3 bomber, 4 paratroop plane, 5 scout. Each role
  flies its own way. A bomber flies a level bomb run and only a bomb bay (TTurretBombardierDescriptor) drops on it; a
  fighter-bomber dives and fires its ordinary forward mounts. So a plane made a bomber gets its bombs moved into a copy
  of a bomber's bomb bay (T50: role alone, or bay alone, dropped nothing; both together worked). A fighter drops bombs
  as it is (T51). The role also has a flag (100, 101, 13, 99), the computer player's category (CategorieIA) and the
  build menu's words for it (TypeUnitHintToken and the two hints): they change with it.
- What a weapon can hit comes from its ammunition: the game's anti-plane ammo (AA guns, fighters' guns) is Arme 1 with
  ProjectileType 3, TirIndirect and no physics; a Panzer IV's AP shell copied with those shot planes down and did
  nothing to ground units (T51, T52). The game's AA guns carry two weapons, one for planes and one for the ground, and
  take the right one by themselves (seen in T52): "both" adds a second weapon the same way.
"""
from __future__ import annotations

import re
from collections import Counter

PLANE = "TAvionDescriptor"
BAY = "TTurretBombardierDescriptor"  # the bomb bay: the only mount a bomber's bomb run drops from
FORWARD = "TTurretAbsolueDescriptor"  # a fighter-bomber's fixed forward mounts (its guns, its bombs)
MOUNTED = "TMountedWeaponDescriptor"
ROLE = "CategoryVolant"
AI_ROLE = "CategorieIA"
FLAGS = "InitialFlagSet"
HINTS = ("TypeUnitHintToken", "DescriptionUnitHintToken", "EfficaceHintToken")
# role -> (CategoryVolant, its flags, CategorieIA), as every game plane of that role has them (the game's 63 planes,
# 2026-10-14): fighters 100, fighter-bombers 101, bombers 13, each with 21 (a fighting unit); scouts 99 and 70 (their
# sight centred on the point they circle) and never 21. A Stuka made a scout with 99 alone had no scout's sight and
# crashed the game when sent at the enemy (T53)
ROLES = {"fighter": (1, (100, 21), 1), "fighter_bomber": (2, (101, 21), 1), "bomber": (3, (13, 21), 4),
         "scout": (5, (99, 70), 3)}
PARATROOP = 4  # a paratroop plane's role: it carries paratroopers, which no other plane has, so it's not offered
ROLE_FLAGS = {flag for _c, flags, _ai in ROLES.values() for flag in flags}
ROLE_OF = {c: role for role, (c, _f, _ai) in ROLES.items()}
SEEN = {"bomber"}  # roles seen working in the game on a plane made into them (T50, 2026-10-14)
ROLE_MOUNT = "Role_"  # the start of the name of the mount a role change makes (a bomb bay, or a forward mount)

ARME, SHAPE, INDIRECT, NO_PHYSICS = "Arme", "ProjectileType", "TirIndirect", "FX_tir_sans_physic"
AIR = 1  # Arme: anti-plane damage (the AA guns' and fighters' ammo); it does nothing to ground units (T51)
GROUND_ARME = 3  # Arme of the AA guns' ground ammo (Ammo_DCA_..._SOL), given to a ground copy of anti-plane ammo
RANGE = "PorteeMaximale"
PLANE_GROUND_SHAPE, PLANE_GROUND_RANGE = 4, 208000.0  # every plane's ground ammo: dropped/strafing shots, its reach
HITS = ("ground", "planes", "both")
HITS_COPY = "Ammo_Hits_"  # the start of the name of an ammo copy set_weapon_hits makes
HITS_MOUNT = "Mount_Hits_"  # ... and of the second weapon it adds for "both"


def hits_stem(unit: str, n: int) -> str:
    """The part of the names of weapon `n`'s (0 first) Hits copies and second weapon: its unit and its number."""
    from .api import safe_name
    base = unit.partition(":")[0]
    return safe_name(f"{re.sub(r'^Descriptor_[A-Za-z]+_', '', base.rsplit('/', 1)[-1])} {n + 1}")


def hits_mount(unit: str, n: int) -> str:
    """The address of the second weapon "both" adds beside weapon `n` of `unit`."""
    base = unit.partition(":")[0]
    return f"{base.rsplit('/', 1)[0]}/{HITS_MOUNT}{hits_stem(unit, n)}"


def _turret_of(weapon: str) -> tuple[str, str]:
    """A weapon's address -> (its turret's address, the list it's in)."""
    head, _, last = weapon.rpartition(".")
    return head, last.partition("[")[0]


class RoleCalls:
    """Mixed into StudioApi: uses its _open, _edits, _resolve, _saving, _editable, _all_ammo, set_ammo and weapons."""

    # --- a plane's role ---
    def plane_role(self, address: str, lang: str = "base") -> dict:
        """A plane's Role box: {"role": its role now (a key of ROLES; "paratroop" for a paratroop plane), "game": the
        game's, "roles": [{"id", "seen"}] (seen: tried in the game on a plane changed into it), "editable", "why":
        why it can't be changed (a key of the Studio's words), "bombs": whether it has a weapon that fires bombs}."""
        from .api import StudioError
        edits = self._edits_or_none()
        real, new = self._resolve(edits, address)
        ix = self._open()
        try:
            o = ix.show(real)
            if o["class"] != PLANE:
                raise StudioError(f"{address} isn't a plane")
            game = self._number(o, ROLE)
            bombs = self._bomb_turret(ix, edits, address, real) is not None or self._bay_of(ix, real) is not None
        finally:
            ix.close()
        keyed = address if new else o["address"]
        mine = edits.get(keyed, ROLE) if edits else None
        now = int(mine) if isinstance(mine, (int, float)) else game
        name = lambda c: "paratroop" if c == PARATROOP else ROLE_OF.get(c, "unknown")  # noqa: E731
        why = "" if edits is not None else "no_mod"
        if game == PARATROOP:
            why = "role_paratroop"
        return {"role": name(now), "game": name(game), "roles": [{"id": r, "seen": r in SEEN} for r in ROLES],
                "editable": why == "" and self._editable(o)[0], "why": why, "bombs": bombs}

    def set_plane_role(self, address: str, role: str | None, lang: str = "base") -> dict:
        """Make a plane a fighter, a fighter-bomber, a bomber or a scout (None: the game's role again), in the current
        mod: its role, its role flag, the computer player's category and the build menu's words for the role, all
        together. A bomber gets its bombs in a bomb bay (a copy of a game bomber's); a game bomber made anything else
        gets them on a forward mount (a copy of a game fighter-bomber's). A plane with no bombs can't be a bomber.
        The changes the mod made to the weapons that move are dropped: the bombs they fired go with them."""
        from .api import StudioError
        from .edits import Link, Literal, ModEdits
        if role is not None and role not in ROLES:
            raise StudioError("Pick a role from the list.")
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        real, new = self._resolve(edits, address)
        ix = self._open()
        try:
            o = ix.show(real)
            if o["class"] != PLANE:
                raise StudioError(f"{address} isn't a plane")
            game = self._number(o, ROLE)
            if game == PARATROOP:
                raise StudioError("A paratroop plane carries paratroopers: its role stays.")
            keyed = address if new else o["address"]
            want = ROLES[role][0] if role else game
            game_flags = [int(n) for p, n, _t in o["values"] if p.startswith(FLAGS + "[")]
            mine = edits.get(keyed, FLAGS)
            flags = [int(x) for x in mine] if isinstance(mine, list) else game_flags
            hints = self._role_hints(ix)
            bay = self._bay_of(ix, real)
            plan = None
            if want != game:
                if role == "bomber" and bay is None:
                    turret = self._bomb_turret(ix, edits, address, real)
                    if turret is None:
                        raise StudioError("It has no bombs to drop: pick bombs for one of its weapons first (Weapons, "
                                          "below), then make it a bomber.")
                    plan = (turret[0], turret[2], self._game_bay(ix), turret[1])
                elif role != "bomber" and bay is not None:
                    turret = self._bomb_turret(ix, edits, address, real)  # the bombs it drops now, the mod's pick
                    ammo = turret[1] if turret is not None and turret[0] == bay[0] else bay[1]
                    plan = (bay[0], bay[2], self._game_forward(ix), ammo)
            parts = self._mount_parts(ix, plan[2]) if plan is not None else []
        finally:
            ix.close()
        tail = keyed.rsplit("/", 1)[-1]
        mount = f"{keyed.rsplit('/', 1)[0]}/{ROLE_MOUNT}{re.sub(r'^Descriptor_[A-Za-z]+_', '', tail)}_Bombs"
        weapons = keyed + ":WeaponDescriptor"
        with self._saving:
            edits = ModEdits(edits.folder)
            # what an earlier role change made goes first
            for k in [k for k in edits.edits if k[0] == keyed and k[1].startswith("WeaponDescriptor.TurretDescriptor")
                      and isinstance(edits.edits[k].value, Link) and str(edits.edits[k].value) == mount]:
                del edits.edits[k]
            if mount in edits.new_units:
                edits.new_units.pop(mount)
                for k in [k for k in edits.edits if k[0] == mount]:
                    del edits.edits[k]
            if want == game:
                for prop in (ROLE, AI_ROLE, *HINTS):
                    edits.edits.pop(edits.key(keyed, prop), None)
                back = [f for f in flags if f not in ROLE_FLAGS or f in game_flags]
                back += [f for f in game_flags if f in ROLE_FLAGS and f not in back]
                if sorted(back) == sorted(game_flags):  # the game's own set: its order doesn't matter
                    edits.edits.pop(edits.key(keyed, FLAGS), None)
                else:
                    edits.edits[edits.key(keyed, FLAGS)] = self._edit(keyed, FLAGS, back)
            else:
                c, role_flags, ai = ROLES[role]
                for prop, value in ((ROLE, c), (AI_ROLE, ai)):
                    edits.edits[edits.key(keyed, prop)] = self._edit(keyed, prop, value)
                for prop, token in hints.get(c, {}).items():
                    edits.edits[edits.key(keyed, prop)] = self._edit(keyed, prop, Literal(f"key({token})"))
                put = [f for f in flags if f not in ROLE_FLAGS] + list(role_flags)
                edits.edits[edits.key(keyed, FLAGS)] = self._edit(keyed, FLAGS, put)
                if plan is not None:
                    turret, turret_real, source, ammo = plan
                    # the old mount's own changes go: it's replaced (the index names a part by its place, [0], or by
                    # its class when it's the only one of it, [class=...]: both ways)
                    inside = (turret_real.partition(":")[2], f"WeaponDescriptor.{turret}")
                    for k in [k for k in edits.edits if k[0] == keyed and k[1].startswith(
                              tuple(f"{p}{c}" for p in inside for c in ".["))]:
                        del edits.edits[k]
                    edits.new_units[mount] = self._new_unit(mount, source)
                    for part in parts:  # its weapons fire the bombs, by the index's own names for them
                        k = edits.key(_inside(mount, part, source), "Ammunition")
                        edits.edits[k] = self._edit(k[0], k[1], Link(ammo))
                    edits.edits[edits.key(weapons, turret)] = self._edit(keyed, f"WeaponDescriptor.{turret}",
                                                                        Link(mount))
            edits.save()
        return {"saved": str(edits.file), **self.plane_role(address, lang)}

    # --- what a weapon can hit ---
    def set_weapon_hits(self, unit: str, weapon: str, hits: str) -> dict:
        """What one of a unit's weapons can hit: "ground", "planes" or "both", in the current mod. Its ammo is copied
        with the anti-plane marks put on or taken off (named HITS_COPY + the unit and the weapon's number), the way
        set_range copies one, with the mod's changes to it carried over; back to what its ammo hits, the weapon fires
        that again. "both" keeps its ammo and adds a second weapon beside it (a copy of this one) firing the other
        kind, the way the game's AA guns carry one for planes and one for the ground."""
        from .api import StudioError
        from .edits import Link, ModEdits, plain_name
        if hits not in HITS:
            raise StudioError("Pick ground, planes or both.")
        edits = self._edits()
        if edits is None:
            raise StudioError("Pick or make a mod first: changes are saved in a mod.")
        listed = self.weapons(unit)["weapons"]
        n, w = next(((i, x) for i, x in enumerate(listed) if x["address"] == weapon), (None, None))
        if w is None:
            raise StudioError(f"{weapon} isn't a weapon of {unit}")
        stem, mount = hits_stem(unit, n), hits_mount(unit, n)
        turret, listname = _turret_of(weapon)
        ammo = w["ammo"]["address"]
        real_weapon, _new = self._resolve(edits, weapon)
        ix = self._open()
        try:
            source, carry = self._ammo_source(edits, ammo)
            src_air = self._air(ix, source, {})
            now_air = self.hits_of(ix, edits, ammo) == "planes"
            plane = ix.show(self._resolve(edits, unit)[0].partition(":")[0])["class"] == PLANE
            game = {p: n for p, n, _t in ix.show(source)["values"] if n is not None}  # the source ammo's values
        finally:
            ix.close()
        marks = lambda air: self._marks(air, plane, game, carry)  # noqa: E731
        copies = {air: f"{source.rsplit('/', 1)[0]}/{HITS_COPY}{stem}_{'Air' if air else 'Ground'}"
                  for air in (True, False)}
        with self._saving:  # the second weapon an earlier "both" added goes first
            edits = ModEdits(edits.folder)
            if mount in edits.new_units:
                edits.new_units.pop(mount)
                for k in [k for k in edits.edits if k[0] == mount]:
                    del edits.edits[k]
            edits.edits.pop(edits.key(turret, listname), None)
            edits.save()
        want_air = hits == "planes" or (hits == "both" and now_air)
        if want_air != now_air:  # the weapon's own ammo changes kind
            if want_air == src_air and ammo in copies.values() and not carry:
                self.set_ammo(unit, weapon, source)  # a copy made here, back to its source's kind: the source again
                ammo = source
            else:
                ammo = self._hits_copy(edits, source, carry, marks(want_air), copies[want_air])
                self.set_ammo(unit, weapon, ammo)
        other = None
        if hits == "both":
            other = (source if (not want_air) == src_air and not carry else
                     self._hits_copy(edits, source, carry, marks(not want_air), copies[not want_air]))
            with self._saving:
                edits = ModEdits(edits.folder)
                edits.add_unit(mount, real_weapon, plain_name(mount), {"Ammunition": Link(other)}, named=False)
                edits.set(turret, listname, _append([Link(mount)]))
        with self._saving:  # this weapon's copies that nothing fires now go
            edits = ModEdits(edits.folder)
            for copy in copies.values():
                if copy in edits.new_units and copy not in (ammo, other):
                    edits.remove_unit(copy)
        return {"saved": str(edits.file), "hits": hits, "ammo": ammo}

    @staticmethod
    def _marks(air: bool, plane: bool, game: dict, carry: dict) -> dict:
        """The values that make a copy of an ammo (its game values `game`, the mod's `carry`) hit planes (`air`) or
        the ground, on a plane's weapon or another unit's. Anti-plane, as the AA guns' and fighters' guns: Arme 1,
        ProjectileType 3, indirect, no physics. The ground from a plane, as every plane's strafing guns, rockets and
        Rudel's cannon: ProjectileType 4, indirect, at least their 208,000 range, no direct-fire share (T54: a
        fighter's cannon left with its air-to-air marks flew the pass and fired nothing). The ground from anything
        else, as the AA guns' ground ammo (_SOL): Arme 3, none of the anti-plane marks."""
        from .edits import REMOVED
        if air:
            return {ARME: AIR, SHAPE: 3, INDIRECT: 1, NO_PHYSICS: 1}
        gone = lambda *props: {p: REMOVED for p in props if p in game}  # noqa: E731
        if plane:
            reach = max(float(game.get(RANGE, 0)), float(carry.get(RANGE, 0) or 0), PLANE_GROUND_RANGE)
            return {ARME: GROUND_ARME, SHAPE: PLANE_GROUND_SHAPE, INDIRECT: 1, RANGE: reach,
                    **gone("PourcentageTirDirect", "PourcentageTirDirectEnMouvement")}
        return {ARME: GROUND_ARME, **gone(SHAPE, INDIRECT, NO_PHYSICS)}

    def _hits_copy(self, edits, source: str, carry: dict, marks: dict, target: str) -> str:
        """A copy of `source` at `target` (with the mod's changes `carry`) with `marks` (_marks) on top. One made
        there earlier is made again."""
        from .edits import ModEdits, plain_name
        with self._saving:
            edits = ModEdits(edits.folder)
            if target in edits.new_units:
                edits.new_units.pop(target)
                for k in [k for k in edits.edits if k[0] == target]:
                    del edits.edits[k]
            edits.add_unit(target, source, plain_name(target), {**carry, **marks}, named=False)
        return target

    def _ammo_source(self, edits, ammo: str) -> tuple[str, dict]:
        """The game ammo a mod's copy was made from and the copy's own changes (the game's ammo: itself, and the mod's
        changes to it)."""
        unit = edits.new_units.get(ammo) if edits else None
        if unit is not None:
            carry = {k: v for k, v in edits.of(ammo).items() if k not in (ARME, SHAPE, INDIRECT, NO_PHYSICS)}
            return unit.source, carry
        return ammo, {}

    @staticmethod
    def _air(ix, ammo: str, carry: dict) -> bool:
        """Whether the ammo hits planes: the game's anti-plane damage type (Arme 1)."""
        if ARME in carry and isinstance(carry[ARME], (int, float)):
            return int(carry[ARME]) == AIR
        try:
            values = ix.show(ammo)["values"]
        except KeyError:
            return False
        return next((int(n) for p, n, _t in values if p == ARME and n is not None), 0) == AIR

    def hits_of(self, ix, edits, ammo: str) -> str:
        """What an ammo hits now: "planes" or "ground" (weapons() lists it per weapon)."""
        source, carry = self._ammo_source(edits, ammo)
        if edits is not None and ammo in edits.new_units:
            mine = edits.of(ammo)
            if ARME in mine and isinstance(mine[ARME], (int, float)):
                return "planes" if int(mine[ARME]) == AIR else "ground"
        return "planes" if self._air(ix, source, carry) else "ground"

    # --- helpers ---
    def _edits_or_none(self):
        from .edits import EditsFileError
        try:
            return self._edits()
        except EditsFileError:
            return None

    @staticmethod
    def _number(o: dict, prop: str) -> int:
        return next((int(n) for p, n, _t in o["values"] if p == prop and n is not None), 0)

    @staticmethod
    def _edit(target: str, path: str, value):
        from .edits import Edit
        return Edit(target, path, value)

    @staticmethod
    def _new_unit(target: str, source: str):
        from .edits import NewUnit, plain_name
        return NewUnit(target, source, plain_name(target), named=False)

    @staticmethod
    def _mount_parts(ix, turret: str) -> list[str]:
        """The index addresses of a mount's weapons, in their order."""
        return [w for p, k, w in ix.uses(turret) if k == "object" and p.startswith("MountedWeaponDescriptorList[")]

    def role_parts(self, ix, edits, base: str, real_base: str) -> tuple[list[str], list[tuple]]:
        """For weapons(): a unit's mounts a role change replaced, as (the index addresses under which the game's
        weapons are gone, [(sort key, the weapon's index address, its address in the mod)] of the mount put there)."""
        if edits is None:
            return [], []
        from .edits import Link
        turrets = self._turrets(ix, real_base)
        gone, extra = [], []
        for (target, path, how), e in edits.edits.items():
            m = re.fullmatch(r"WeaponDescriptor\.TurretDescriptorList\[(\d+)\]", path)
            if not (target == base and how == "" and m and isinstance(e.value, Link)):
                continue
            mount = str(e.value)
            unit = edits.new_units.get(mount)
            i = int(m.group(1))
            if unit is None or not mount.rsplit("/", 1)[-1].startswith(ROLE_MOUNT) or i >= len(turrets):
                continue
            replaced = turrets[i][1]
            gone.append(replaced + ".")
            for part in self._mount_parts(ix, unit.source):
                inside = part[len(unit.source):]
                extra.append((replaced + inside, part, _inside(mount, part, unit.source)))
        return gone, extra

    def role_mount_of(self, edits, unit: str, weapon: str) -> bool:
        """Whether `weapon` is a weapon of a mount a role change gave `unit` (set_ammo changes it there)."""
        mount = weapon.partition(":")[0]
        if edits is None or mount not in edits.new_units or not mount.rsplit("/", 1)[-1].startswith(ROLE_MOUNT):
            return False
        base = unit.partition(":")[0]
        return any(t == base and str(e.value) == mount for (t, _p, _h), e in edits.edits.items())

    def _turrets(self, ix, real: str) -> list[tuple[str, str, str]]:
        """A unit's mounts in the game: [(its path in the unit, its address, its class)], in their order."""
        weapons = next((w for p, k, w in ix.uses(real) if p == "WeaponDescriptor" and k == "object"), None)
        if weapons is None:
            return []
        out = []
        for path, kind, what in ix.uses(weapons):
            m = re.fullmatch(r"TurretDescriptorList\[(\d+)\]", path)
            if m and kind == "object":
                out.append((int(m.group(1)), f"TurretDescriptorList[{m.group(1)}]", what, ix.show(what)["class"]))
        return [(p, a, c) for _i, p, a, c in sorted(out)]

    def _bay_of(self, ix, real: str):
        """(the mount's path in the unit, the bombs it drops, its index address) of a plane's bomb bay in the game,
        or None."""
        for path, address, cls in self._turrets(ix, real):
            if cls == BAY:
                ammo = self._mount_ammo(ix, address)
                return (path, ammo[0], address) if ammo else None
        return None

    @staticmethod
    def _mount_ammo(ix, turret: str) -> list[str]:
        out = []
        for path, kind, what in ix.uses(turret):
            if kind == "object" and path.startswith("MountedWeaponDescriptorList["):
                out += [a for p, k, a in ix.uses(what) if p == "Ammunition" and k == "object"]
        return out

    def _bomb_turret(self, ix, edits, address: str, real: str):
        """(the mount's path, the bombs it fires now, with the mod's picks, its index address) of the first of a
        plane's mounts that fires bombs, or None."""
        from .api import AMMO_GROUP_OF
        rows = {a["address"]: a for a in self._all_ammo(ix)}
        english = ix.names([a["type_key"] for a in rows.values() if a["type_key"]], "us")
        base, real_base = address.partition(":")[0], real.partition(":")[0]
        for path, turret, _cls in self._turrets(ix, real):
            for mount in self._mount_parts(ix, turret):
                game = next((a for p, k, a in ix.uses(mount) if p == "Ammunition" and k == "object"), None)
                chosen = edits.get(base + mount[len(real_base):], "Ammunition") if edits else None
                now = str(chosen) if chosen else game
                source = edits.new_units[now].source if edits and now in edits.new_units else now
                row = rows.get(source)
                if row and AMMO_GROUP_OF.get(english.get(row["type_key"], "")) == "bombs":
                    return path, now, turret
        return None

    @staticmethod
    def _game_bay(ix) -> str:
        """A game bomber's bomb bay to copy (the B-25's when the game has it)."""
        from .api import StudioError
        bays = [o["address"] for o in ix.of_class(BAY)]
        if not bays:
            raise StudioError("This game build has no bomber with a bomb bay to copy.")
        return next((b for b in bays if "Descriptor_Avion_B25:" in b), bays[0])

    def _game_forward(self, ix) -> str:
        """A game fighter-bomber's forward mount that fires bombs, to copy (the Stuka's when the game has it)."""
        from .api import StudioError
        found = []
        for o in ix.of_class(PLANE):
            if self._number(o, ROLE) != ROLES["fighter_bomber"][0]:
                continue
            turret = self._bomb_turret(ix, None, o["address"], o["address"])
            if turret is not None:
                found.append(turret[2])
        if not found:
            raise StudioError("This game build has no fighter-bomber with bombs to copy a mount from.")
        return next((f for f in found if "Descriptor_Avion_Junkers_87:" in f), found[0])

    def _role_hints(self, ix) -> dict:
        """CategoryVolant -> {each of the build menu's words for the role (TypeUnitHintToken,
        DescriptionUnitHintToken, EfficaceHintToken): the one most of the game's planes of that role have}."""
        seen: dict[tuple, Counter] = {}
        for o in ix.of_class(PLANE):
            role = self._number(o, ROLE)
            for p, _n, t in o["values"]:
                if p in HINTS and t:
                    seen.setdefault((role, p), Counter())[t] += 1
        out: dict[int, dict] = {}
        for (role, prop), counts in seen.items():
            out.setdefault(role, {})[prop] = counts.most_common(1)[0][0]
        return out


def _inside(obj: str, part: str, source: str) -> str:
    """The address in `obj` (a copy of `source`, a part) of what is at `part` inside `source`: `source` is
    `$/X:A.B`, `part` `$/X:A.B.C[0]`, the result `obj:C[0]`."""
    return f"{obj}:{part[len(source):].lstrip('.')}"


def _append(items):
    from .edits import Append
    return Append(items)
