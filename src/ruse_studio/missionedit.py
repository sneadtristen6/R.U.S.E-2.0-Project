"""The Scenario side's mission calls (StudioApi's MissionCalls; rusemod.mission): a new Operation's or campaign
chapter's own mission, kept in the map project's maps/<map>/mission.toml (the owner's design, 2026-10-09: "the actual
unit commands, spawning the units, choosing the sides, the camera angles", events When -> Do, all on the same map
screen). The page holds the mission as the file's own table and sends it back whole; every check is the build's own
(mission.problems), so what the Studio says is what Test in game will say."""
from __future__ import annotations

import struct
import tomllib
import zlib

from rusemod import mission as M
from rusemod import missionbuild as MB
from rusemod import presets
from rusemod.build import find_pack
from rusemod.edat import Edat


class MissionCalls:
    """Mixed into StudioApi: uses its _new_maps, _copy_kind, _map_dir, _game, _open, map_scenarios and _saving."""

    def _mission_file(self, name: str):
        folder = self._map_dir()
        return folder / "maps" / name / "mission.toml" if folder is not None else None

    def _mission_source(self, spec) -> tuple:
        """(the copied mission's Base, its scenario file, the copied map's camera path names), read once a map."""
        cache = self.__dict__.setdefault("_mission_bases", {})
        key = (spec.copy_of.lower(), (spec.entry or "").lower())
        if key in cache:
            return cache[key]
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise M.MissionError("R.U.S.E. wasn't found, so the mission being copied can't be read.")
        file = presets.copy_scenario(game, spec.copy_of, spec.entry)
        ia_path, glad_path = find_pack(game, "IA_Common.dat"), find_pack(game, "ZZ_GladPatchableWin.dat")
        if ia_path is None or glad_path is None:
            # not a game rule: the game or one of its files isn't found
            raise M.MissionError("IA_Common.dat or ZZ_GladPatchableWin.dat isn't in the game folder.")
        try:
            with Edat.open(str(glad_path)) as g:
                folder = MB.entry_folder(lambda member: bytes(g.read(g.entry(member))) if g.entry(member) else None,
                                         spec.copy_of, spec.entry)
            with Edat.open(str(ia_path)) as ia:
                src_member, _new = MB.script_members(ia, spec.copy_of, folder, "x")
                base = M.base_of(bytes(ia.read(ia.find(src_member))))
        except (MB.MissionBuildError, M.MissionError, KeyError, ValueError, struct.error, zlib.error) as exc:
            raise M.MissionError(f"{spec.entry or spec.copy_of}: the mission being copied can't be read ({exc})") from None
        paths = []
        data = find_pack(game, "DataMap_Win.dat")
        if data is not None:
            stem = file.rsplit(".", 1)[0]
            want = f"test\\map\\{spec.copy_of}\\campath\\campaths_{stem}.ndfbin".lower()
            with Edat.open(str(data)) as d:
                e = next((x for x in d.entries if x.path.lower() == want), None)
                if e is not None:
                    try:
                        paths = MB.camera_paths(bytes(d.read(e)))
                    except (ValueError, KeyError, struct.error):
                        paths = []
        cache[key] = (base, file, paths)
        return cache[key]

    def mission(self, pack: str) -> dict:
        """The map's own mission, for the Scenario side's Mission, Goals & events and Camera moves trays:
        {"allowed": whether the map can have one, "why": the reason it can't (a word key), "kind": operation or
        campaign, "exists": whether mission.toml is there, "mission": the file's table (an empty mission when there's
        none), "sides": the copied mission's sides (number, player, nation, team), "points" / "zones": the named
        points and zones a mission can name, "cameras": the copied map's camera paths, "groups": the groups the
        mission fills, "problems": [[level, message]], "units": {class: its unit address}}."""
        copy = self._new_maps().get(str(pack).lower())
        if copy is None:
            return {"allowed": False, "why": "mission_why_copy"}
        name, spec = copy
        kind = self._copy_kind(spec)
        if kind not in ("operation", "campaign"):
            return {"allowed": False, "why": "mission_why_battles", "kind": kind}
        base, file, map_cams = self._mission_source(spec)
        path = self._mission_file(name)
        exists = bool(path and path.is_file())
        problems: list = []
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8")) if exists else {}
            m = M.parse(data, f"maps/{name}/mission.toml")
        except (tomllib.TOMLDecodeError, UnicodeDecodeError, M.MissionError) as exc:
            m = M.Mission()
            problems.append(["error", str(exc)])
        if not m.sides:  # a new mission: every side of the copied mission, as it is
            m.sides = [M.Side(c[1]) for c in base.camps]
        view = self.map_scenarios(pack)
        s = next((x for x in view.get("scenarios", []) if x.get("file", "").lower() == file.lower()), None)
        points, zones, rects = set(), set(), set()
        for it in (s or {}).get("items", []):
            n = it.get("name")
            if not n or it.get("gone"):
                continue
            if it.get("kind") in ("CircularZone", "RectangleZone"):
                zones.add(n)
                if it["kind"] == "RectangleZone":
                    rects.add(n)
            elif it.get("kind") == "Name":
                points.add(n)
        from rusemod.scenario import placed_groups
        try:
            _moves, spawns = self._read_scenario_edits(pack)
        except Exception:  # noqa: BLE001  (a broken scenario.toml is the map check's to say)
            spawns = []
        placed = placed_groups(spawns, file)
        ctx = M.Context(name, kind, points, zones, rects, set(map_cams), placed)
        problems += [[level, msg] for level, msg in M.problems(m, base, ctx)]
        groups = sorted({a.group for e in m.events for a in e.actions if a.group} | {g.group for g in m.goals if g.group}
                        | {a.target for e in m.events for a in e.actions if a.target} | set(placed))
        sides = []
        back = {v: k for k, v in M.NATIONS.items()}
        for var, number, _func, values, player in base.camps:
            nat = values.get("Nationalite")
            nation = back.get(nat.path.rsplit(".", 1)[-1]) if isinstance(nat, M.Attr) else None
            sides.append({"number": number, "player": player, "nation": nation,
                          "team": values.get("Alliance") if isinstance(values.get("Alliance"), int) else None})
        return {"allowed": True, "kind": kind, "name": name, "file": file, "exists": exists,
                "mission": tomllib.loads(M.to_toml(m)), "sides": sides, "points": sorted(points), "zones": sorted(zones),
                "cameras": map_cams, "groups": groups, "problems": problems,
                "units": {c: (getattr(self, "_by_class", None) or {}).get(c, {}).get("unit") for c in
                          {a.unit for e in m.events for a in e.actions if a.unit}}}

    def mission_save(self, pack: str, data: dict) -> dict:
        """Save the map's mission (the file's table, as mission() gives it); refuses what the file can't hold, with
        what to change. Returns mission(pack)."""
        copy = self._new_maps().get(str(pack).lower())
        if copy is None or self._map_dir() is None:
            raise M.MissionError("A mission belongs to a new Operation or campaign chapter of the map project: make one "
                             "with Duplicate map first.")
        name, spec = copy
        if self._copy_kind(spec) not in ("operation", "campaign"):
            raise M.MissionError("A BATTLES map can't have a mission of its own yet: copy an Operation or a campaign "
                             "chapter.")
        try:
            m = M.parse(data if isinstance(data, dict) else {}, f"maps/{name}/mission.toml")
        except M.MissionError as exc:
            raise M.MissionError(str(exc)) from None
        text = M.to_toml(m, f"The mission of {name}, a new {self._copy_kind(spec)}: sides, rules, goals, events and "
                            f"camera moves (MOD_FORMAT §8, mission.toml), saved by RUSE Studio.")
        with self._saving:
            path = self._mission_file(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return self.mission(pack)

    def mission_delete(self, pack: str) -> dict:
        """Take the map's own mission out (the copy plays the mission it copies again). Returns mission(pack)."""
        copy = self._new_maps().get(str(pack).lower())
        if copy is not None and self._map_dir() is not None:
            with self._saving:
                path = self._mission_file(copy[0])
                if path.is_file():
                    path.unlink()
        return self.mission(pack)

    def mission_unit(self, address: str) -> dict:
        """A unit picked in a spawn action's list: {"class": its class name (what the mission names), "unit"}."""
        ix = self._open()
        try:
            try:
                o = ix.show(address)
            except KeyError:
                raise M.MissionError(f"There's no unit at {address}.") from None
            cls = next((t for p, _n, t in o["values"] if p == "ClassNameForDebug" and t), None)
        finally:
            ix.close()
        if not cls:
            # not a game rule: what our script writer supports (it names a unit by its class)
            raise M.MissionError("That unit has no class name for the game's scripts, so a mission can't make it.")
        return {"class": cls, "unit": address}
