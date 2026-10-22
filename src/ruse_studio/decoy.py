"""RUSE Decoy's calls (StudioApi's DecoyCalls; rusemod.soundlist, rusemod.sound): every sound the game has, by kind,
each heard, made louder or quieter (0 to 200% of the game's) and replaced; a mission's dialogue by mission and
language with its words. A sound's volume is saved in the current mod's files/sound/volume.toml and the build makes
that sound again at it (rusemod.sound.volume_changes); a replaced sound is files/replace/<its path>.wav, as the Music
tab saves songs (the same editor). Not tried in the game yet."""
from __future__ import annotations

import hashlib
import json
import re
import threading
import tomllib

from rusemod import sound, soundlist
from rusemod.edat import Edat
from rusemod.terrain import map_list

PAGE = 100          # rows the page asks for at a time
TEXT_LANGS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")  # the Studio's ten, as the texts name them


class DecoyError(Exception):
    pass


def _toml_key(member: str) -> str:
    return '"' + sound.volume_key(member).replace("\\", "\\\\").replace('"', '\\"') + '"'


class DecoyCalls:
    _decoy_lock = threading.Lock()

    # --- every game sound, worked out once per game build ---
    def _decoy_rows(self) -> list:
        """rusemod.soundlist.catalogue of the game's ZZ_Win.dat, kept per game build (in memory and in the cache)."""
        _game, zz, key = self._music_game()
        with self._decoy_lock:
            kept = getattr(self, "_decoy_kept", None)
            if kept is not None and kept[0] == key:
                return kept[1]
            file = self.cache_dir / "decoy" / f"catalogue-{key}-v2.json"
            rows = None
            if file.is_file():
                try:
                    rows = json.loads(file.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    rows = None
            if rows is None:
                heads = {}
                with Edat.open(str(zz)) as arc:
                    for e in arc.entries:
                        p = e.path.lower()
                        if p.endswith(".ess"):
                            heads[p] = sound.header(bytes(arc.raw[arc.data_offset + e.offset:arc.data_offset + e.offset + 20]))
                ix = self._open()
                try:
                    rows = soundlist.catalogue(ix.db, heads)
                    keys = [r["key"] for r in rows if r["key"]]
                    words = {lang: soundlist.subtitles(ix.db, keys, lang) for lang in TEXT_LANGS}
                finally:
                    ix.close()
                counts: dict = {}
                for r in rows:
                    if r["group"]:
                        counts[r["group"]] = counts.get(r["group"], 0) + 1
                for r in rows:
                    r["shared"] = counts.get(r["group"], 1) - 1 if r["group"] else 0
                    if r["key"]:
                        r["words"] = {lang: words[lang].get(r["key"]) for lang in TEXT_LANGS if words[lang].get(r["key"])}
                file.parent.mkdir(parents=True, exist_ok=True)
                tmp = file.with_suffix(".part")
                tmp.write_text(json.dumps(rows), encoding="utf-8")
                tmp.replace(file)
            self._decoy_kept = (key, rows)
            self._decoy_by = {r["member"]: r for r in rows}
            return rows

    def _decoy_row(self, member: str) -> dict | None:
        self._decoy_rows()
        return self._decoy_by.get(str(member).lower())

    def _decoy_volumes(self) -> dict:
        """The current mod's volumes, {member: percent} (files/sound/volume.toml), {} without a mod or a file."""
        mod = self._mod_dir()
        if mod is None:
            return {}
        try:
            return sound.mod_volumes(mod)
        except sound.SoundError as exc:
            raise DecoyError(str(exc)) from None

    def _decoy_mission_names(self, lang: str) -> dict:
        """{mission folder, lower case: its names in the game's menus in `lang`} (a campaign map has one a chapter)."""
        try:
            game = self._game()
            out = {}
            for m in map_list(game):
                t = m["titles"].get(lang) or m["titles"].get("us") or []
                if t:
                    out[m["pack"].lower()] = " / ".join(t[:2]) + (" …" if len(t) > 2 else "")
            return out
        except (OSError, ValueError, KeyError, TypeError):
            return {}

    # --- what the page calls ---
    def decoy_volumes(self) -> dict:
        """The current mod's volumes, {sound path: percent} (files/sound/volume.toml), for the songs' rows."""
        return self._decoy_volumes()

    def decoy(self, lang: str = "base") -> dict:
        """RUSE Decoy's first look: each kind with how many sounds it has and how many the mod changed, the missions
        whose dialogue there is (by their menu names), the languages the dialogue is in, and whether a mod is open."""
        rows = self._decoy_rows()
        vols = self._decoy_volumes()
        replaced = self._decoy_replaced()
        kinds: dict = {}
        for r in rows:
            k = kinds.setdefault(r["kind"], {"id": r["kind"], "count": 0, "changed": 0})
            k["count"] += 1
            if r["member"] in vols or r["member"] in replaced:
                k["changed"] += 1
        names = self._decoy_mission_names("us" if lang == "base" else lang)
        missions: dict = {}
        langs: set = set()
        for r in rows:
            if r["kind"] == "dialogue":
                missions[r["mission"]] = missions.get(r["mission"], 0) + 1
                langs.add(r["lang"])
        return {"kinds": [kinds[k] for k in soundlist.KINDS if k in kinds],
                "missions": [{"id": m, "name": names.get(m, m.replace("_", " ")), "count": n}
                             for m, n in sorted(missions.items())],
                "langs": sorted(langs), "mod": self._mod_dir() is not None}

    def decoy_list(self, kind: str, words: str = "", mission: str | None = None, in_lang: str | None = None,
                   lang: str = "base", start: int = 0, count: int = PAGE) -> dict:
        """One kind's sounds, `count` from `start`, that match `words` (in the name, the path or a dialogue line's
        words), a mission's (`mission`) and a language's (`in_lang`, for dialogue and the HQ's lines). Each with its
        length, format, the mod's volume for it (100 = the game's), whether the mod replaced it, the game's volume
        for its group (and how many other sounds share that group), and a dialogue line's words in `lang`."""
        if kind not in soundlist.KINDS:
            # not a game rule: the page named a kind there isn't
            raise DecoyError(f"{kind} isn't one of the kinds of sound")
        text_lang = "us" if lang == "base" else lang
        rows = self._decoy_rows()
        vols = self._decoy_volumes()
        want = [w for w in re.split(r"\s+", (words or "").lower()) if w]
        picked = []
        for r in rows:
            if r["kind"] != kind or (mission and r["mission"] != mission) or (in_lang and r["lang"] != in_lang):
                continue
            said = (r.get("words") or {}).get(text_lang) or (r.get("words") or {}).get("us") or ""
            if want:
                hay = f"{r['name']} {r['member']} {said}".lower()
                if not all(w in hay for w in want):
                    continue
            picked.append((r, said))
        replaced = self._decoy_replaced()
        out = [self._decoy_out(r, said, vols, replaced) for r, said in picked[start:start + max(1, min(count, 500))]]
        return {"rows": out, "total": len(picked), "start": start}

    @staticmethod
    def _decoy_out(r: dict, said: str, vols: dict, replaced: set) -> dict:
        """One sound as the page shows it."""
        return {"member": r["member"], "kind": r["kind"], "name": r["name"], "seconds": r["seconds"],
                "channels": r["channels"], "rate": r["rate"], "volume": vols.get(r["member"], 100),
                "mine": r["member"] in replaced, "group_volume": round(r["group_volume"] * 100),
                "grouped": bool(r["group"]), "shared": r.get("shared", 0), "said": said,
                "lang": r["lang"], "mission": r["mission"]}

    # --- a unit's own sounds (its page's "Sounds and animation" opens RUSE Decoy on them) ---
    MOTOR_ROLES = (("Run_Snd", "engine_run"), ("IdleAndStop_Snd", "engine_idle"), ("Dive_Snd", "engine_dive"))

    def _decoy_unit_sounds(self, address: str) -> tuple[str, list]:
        """(the unit's game address, [(sound path, role, moment)]) for a unit: its engine's sounds (its
        SoundMotorDescriptor's Run_Snd, IdleAndStop_Snd and a plane's Dive_Snd, each a sound whose TheSoundStream
        names the file) and its voice lines (its nation's and kind's, as its page shows them). A modder's new unit
        has its source's. Which of the game's guns and hits a unit sets off isn't read yet (its effects)."""
        try:
            edits = self._edits()
        except Exception:  # a mod file that can't be read: the game's own unit is still shown
            edits = None
        real, _new = self._resolve(edits, address)
        real = real.split(":", 1)[0]
        out = []
        ix = self._open()
        try:
            try:
                oid = ix._object(real)
            except KeyError:   # not in the game's data (yet): its voice lines are still found, below
                oid = None
            db = ix.db
            for path, role in (self.MOTOR_ROLES if oid is not None else ()):
                for (fname,) in db.execute("""SELECT f.text FROM ref m
                                              JOIN ref s ON s.src = m.dst AND s.path = ?
                                              JOIN ref t ON t.src = s.dst AND t.path = 'TheSoundStream'
                                              JOIN value f ON f.object = t.dst AND f.path = 'FileName'
                                              WHERE m.src = ? AND m.path = 'SoundMotorDescriptor'""", (path, oid)):
                    if fname:
                        out.append((sound.member_of(fname), role, None))
        finally:
            ix.close()
        try:
            v = self.unit_voices(address)
            for m in v.get("moments", []):
                for line in m["lines"]:
                    out.append((line["member"], "voice", m["id"]))
        except Exception:  # noqa: BLE001 (no voices for this unit: its engine is still shown)
            pass
        seen, unique = set(), []
        for item in out:
            if item[0] not in seen:
                seen.add(item[0])
                unique.append(item)
        return real, unique

    def decoy_unit(self, address: str) -> dict:
        """What a unit's page says about its sounds and animations: how many voice lines, engine sounds and clips."""
        _real, items = self._decoy_unit_sounds(address)
        try:
            clips = self.decoy_unit_anims(address)["total"]
        except Exception:  # noqa: BLE001 (no animations read: its sounds are still shown)
            clips = 0
        return {"count": len(items), "voices": sum(1 for _m, role, _x in items if role == "voice"),
                "engine": sum(1 for _m, role, _x in items if role.startswith("engine")), "clips": clips}

    def decoy_unit_list(self, address: str, lang: str = "base") -> dict:
        """A unit's own sounds as RUSE Decoy lists them: its engine first, then its voice lines by moment."""
        _real, items = self._decoy_unit_sounds(address)
        vols = self._decoy_volumes()
        replaced = self._decoy_replaced()
        rows = []
        for member, role, moment in items:
            r = self._decoy_row(member)
            if r is None:  # not a game rule: the data names a sound this game build hasn't got
                continue
            row = self._decoy_out(r, "", vols, replaced)
            row.update(role=role, moment=moment)
            rows.append(row)
        return {"rows": rows, "total": len(rows), "start": 0}

    # --- animations: every clip the game has (rusemod.animlist), shown on a model in 3D (rusemod.animglb) and changed
    # in the mod's files/anim/clips.toml (rusemod.anim) ---
    def _decoy_clips(self) -> list:
        """rusemod.animlist.catalogue of the game's clips, kept per game build (in memory and in the cache)."""
        from rusemod import animlist, baf
        _game, zz, key = self._music_game()
        with self._decoy_lock:
            kept = getattr(self, "_decoy_clips_kept", None)
            if kept is not None and kept[0] == key:
                return kept[1]
            file = self.cache_dir / "decoy" / f"clips-{key}-v1.json"
            rows = None
            if file.is_file():
                try:
                    rows = json.loads(file.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    rows = None
            if rows is None:
                found: dict = {}
                with Edat.open(str(zz)) as arc:
                    for e in arc.entries:
                        p = e.path.lower()
                        if p.endswith(".baf"):
                            found.setdefault(p, {"packs": [], "raw": bytes(arc.read(e))})["packs"].append("ZZ_Win.dat")
                        elif p.startswith("genanim_15\\pack\\") and p.endswith(".apk"):
                            pk = Edat(bytes(arc.read(e)))
                            for x in pk.entries:
                                q = x.path.lower()
                                if q.endswith(".baf"):
                                    got = found.setdefault(q, {"packs": [], "raw": None})
                                    got["packs"].append(p)
                                    if got["raw"] is None:
                                        got["raw"] = bytes(pk.read(x))
                clips = {}
                for m, v in found.items():
                    try:
                        c = baf.parse(v["raw"])
                    except baf.ClipError:  # not a game rule: a clip this reader doesn't know (none in 190852)
                        continue
                    names = baf.skeleton(c.skeleton)["names"]
                    clips[m] = {"packs": v["packs"], "seconds": round(c.duration, 3), "frames": c.frames,
                                "bones": c.bones, "skeleton": "|".join(n.lower() for n in names)}
                ix = self._open()
                try:
                    rows = animlist.catalogue(ix.db, clips)
                finally:
                    ix.close()
                for r in rows:
                    r["skeleton"] = clips[r["member"]]["skeleton"]
                file.parent.mkdir(parents=True, exist_ok=True)
                tmp = file.with_suffix(".part")
                tmp.write_text(json.dumps(rows), encoding="utf-8")
                tmp.replace(file)
            self._decoy_clips_kept = (key, rows)
            self._decoy_clip_by = {r["member"]: r for r in rows}
            return rows

    def _decoy_clip_row(self, member: str) -> dict | None:
        self._decoy_clips()
        return self._decoy_clip_by.get(str(member).lower().replace("/", "\\"))

    def _decoy_clip_edits(self) -> dict:
        from rusemod import anim
        mod = self._mod_dir()
        if mod is None:
            return {}
        try:
            return anim.mod_clips(mod)
        except anim.AnimError as exc:
            raise DecoyError(str(exc)) from None

    def _decoy_clip_out(self, r: dict, edits: dict, unit_names: dict | None = None) -> dict:
        e = edits.get(r["member"], {})
        return {"member": r["member"], "kind": r["kind"], "name": r["name"], "seconds": r["seconds"],
                "frames": r["frames"], "bones": r["bones"], "names": r["names"], "units": len(r["units"]),
                "speed": e.get("speed", 100.0), "from": e.get("from"), "mine": bool(e.get("file")),
                "tweaks": {b: {"size": v["size"], "turn": list(v["turn"]) if v["turn"] else None}
                           for b, v in e.get("bones", {}).items()},
                "changed": bool(e)}

    def decoy_anims(self) -> dict:
        """The animations' first look: each kind with how many clips it has and how many the mod changed."""
        from rusemod import animlist
        rows = self._decoy_clips()
        edits = self._decoy_clip_edits()
        kinds: dict = {}
        for r in rows:
            k = kinds.setdefault(r["kind"], {"id": r["kind"], "count": 0, "changed": 0})
            k["count"] += 1
            k["changed"] += r["member"] in edits
        return {"kinds": [kinds[k] for k in animlist.KINDS if k in kinds], "mod": self._mod_dir() is not None}

    def decoy_anim_list(self, kind: str, words: str = "", start: int = 0, count: int = PAGE) -> dict:
        """One kind's clips, `count` from `start`, that match `words` (in the name, the path or the names the game's
        models give the clip: "idle1", "t_course"...), each with what the mod changes in it."""
        from rusemod import animlist
        if kind not in animlist.KINDS:
            # not a game rule: the page named a kind there isn't
            raise DecoyError(f"{kind} isn't one of the kinds of animation")
        want = [w for w in re.split(r"\s+", (words or "").lower()) if w]
        edits = self._decoy_clip_edits()
        picked = [r for r in self._decoy_clips() if r["kind"] == kind and
                  all(w in f"{r['name']} {r['member']} {' '.join(r['names'])}".lower() for w in want)]
        return {"rows": [self._decoy_clip_out(r, edits) for r in picked[start:start + max(1, min(count, 500))]],
                "total": len(picked), "start": start}

    def decoy_anim_info(self, member: str) -> dict:
        """What a clip's page needs: its bones (to make one bigger or turn it) and the clips that can stand in for it
        (the same bones: rusemod.baf.same_skeleton), each with the names the game's models give it."""
        r = self._decoy_clip_row(member)
        if r is None:  # not a game rule: no such animation in the game's packs
            raise DecoyError(f"{member} isn't one of the game's animations")
        from rusemod import mocap
        same = [{"member": x["member"], "name": x["name"], "names": x["names"]} for x in self._decoy_clips()
                if x["skeleton"] == r["skeleton"] and x["member"] != r["member"]]
        raw = self._decoy_game_clips()(r["member"])
        return {"bones": r["skeleton"].split("|"), "same": same, "units": r["units"][:40],
                "loops": mocap.loops(raw) if raw else False, "mocap": "bip01" in r["skeleton"].split("|")}

    def _decoy_preview_model(self, r: dict) -> str | None:
        """A model that can play clip `r`: one of the models of the units that play it whose skeleton has its bones."""
        from rusemod import animglb, models
        want = set(r["skeleton"].split("|"))
        tried = set()
        lib = None
        try:
            for unit in r["units"][:6]:
                for name in self._look_models(unit)[0]:
                    if name in tried:
                        continue
                    tried.add(name)
                    if lib is None:
                        lib = models.Library(self._game())
                    sk = animglb.model_skeleton(lib, name)
                    if sk and want <= {n.lower() for n in sk["names"]}:
                        return name
        finally:
            if lib is not None:
                lib.close()
        return None

    def decoy_anim_preview(self, member: str) -> dict:
        """The clip on a model that plays it, as the current mod makes it (its speed, its stand-in, its bones), as a
        .glb at a cache address of the window's own: {"url", "model", "seconds", "matched", "bones"}; {"url": None}
        when no unit's model plays it (the HQ's figures, scenery: the page says so)."""
        from rusemod import anim
        r = self._decoy_clip_row(member)
        if r is None:  # not a game rule: no such animation in the game's packs
            raise DecoyError(f"{member} isn't one of the game's animations")
        model = self._decoy_preview_model(r)
        if model is None:
            return {"url": None}
        edit = self._decoy_clip_edits().get(r["member"], {})
        game_clip = self._decoy_game_clips()
        try:
            raw = anim.made(game_clip(r["member"]), edit, game_clip) if edit else game_clip(r["member"])
        except anim.AnimError as exc:
            raise DecoyError(str(exc)) from None
        return self._decoy_glb(model, raw)

    def _decoy_game_clips(self):
        """A function giving the game's own clip by its path (loose in ZZ_Win.dat or in a genanim_15 pack), or None."""
        _game, zz, _key = self._music_game()

        def game_clip(m):
            with Edat.open(str(zz)) as arc:
                e = arc.entry(m)
                if e is not None:
                    return bytes(arc.read(e))
                row = self._decoy_clip_row(m)
                for p in row["packs"] if row else []:
                    if p != "ZZ_Win.dat":
                        pk = Edat(bytes(arc.read(arc.entry(p))))
                        x = pk.entry(m)
                        if x is not None:
                            return bytes(pk.read(x))
            return None
        return game_clip

    def _decoy_glb(self, model: str, raw: bytes) -> dict:
        """Clip `raw` on `model` as a .glb at a cache address of the window's own: {"url", "model", "seconds"}."""
        from rusemod import animglb, baf, models
        _game, _zz, key = self._music_game()
        name = hashlib.sha1(raw + model.encode()).hexdigest()[:24] + ".glb"
        out = self.cache_dir / "decoy" / "anim" / key / name
        if not out.is_file():
            lib = models.Library(self._game())
            try:
                data, _got = animglb.glb(lib, model, baf.parse(raw), side=512)
            except animglb.AnimGlbError as exc:
                raise DecoyError(str(exc)) from None
            finally:
                lib.close()
            out.parent.mkdir(parents=True, exist_ok=True)
            part = out.with_suffix(".part")
            part.write_bytes(data)
            part.replace(out)
        return {"url": f"cache/decoy/anim/{key}/{name}", "model": model.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", ""),
                "seconds": baf.parse(raw).duration}

    # --- motion capture (rusemod.mocap): a .bvh made into one of the game's clips, watched, then kept in the mod as
    # files/replace/<clip>.baf with its credit beside it (<clip>.toml) ---
    def decoy_mocap_open(self, name: str, text: str) -> dict:
        """Read a .bvh the page picked: {"id", "name", "seconds", "fps", "parts", "missing", "credit"} (missing: the
        body parts its joints don't show; it can be used only when that's empty)."""
        from rusemod import mocap
        try:
            bvh = mocap.read_bvh(text)
        except (mocap.MocapError, ValueError, IndexError) as exc:
            raise DecoyError(f"{name}: {exc}") from None
        mid = hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:16]
        return self._decoy_mocap_keep(mid, str(name), bvh)

    def _decoy_mocap_keep(self, mid: str, name: str, bvh) -> dict:
        from rusemod import mocap
        with self._decoy_lock:
            kept = getattr(self, "_decoy_mocap", {})
            kept[mid] = (name, bvh)
            while len(kept) > 4:   # the last few files only: each holds every frame
                kept.pop(next(iter(kept)))
            self._decoy_mocap = kept
        return {"id": mid, "name": name, "seconds": round(bvh.seconds, 3), "fps": round(1 / bvh.frame_time, 2),
                "parts": len(mocap.parts_of(bvh)), "missing": mocap.missing(bvh), "credit": mocap.credit_of(bvh)}

    # --- the motion library (rusemod.motionlib): the free sets' moves by kind, fetched when picked ---
    def _decoy_motions(self) -> dict:
        from rusemod import motionlib
        with self._decoy_lock:
            cat = getattr(self, "_decoy_motion_cat", None)
            if cat is None:
                cat = self._decoy_motion_cat = motionlib.catalogue()
            return cat

    def decoy_motions(self, kind: str = "", words: str = "", set_: str = "", start: int = 0, count: int = 60) -> dict:
        """The motion library: each kind with how many moves it has, each set with how many are kept here, and the
        moves of `kind` and set `set_` ("" any) matching `words`, `count` from `start`, each with whether it's kept."""
        from rusemod import motionlib
        cat = self._decoy_motions()
        if kind and kind not in motionlib.KINDS:
            # not a game rule: the page named a kind there isn't
            raise DecoyError(f"{kind} isn't one of the kinds of move")
        counts: dict = {}
        for m in cat["moves"]:
            counts[m["kind"]] = counts.get(m["kind"], 0) + 1
        picked = motionlib.find(cat, kind, words, set_)
        rows = [{"id": m["id"], "set": m["set"], "name": m["name"], "group": m["group"], "kind": m["kind"],
                 "way": m.get("way"), "seconds": m["seconds"], "size": m.get("zip_size") or m["size"],
                 "alone": bool(m.get("url")), "have": motionlib.have(self._home, m)}
                for m in picked[max(0, start):max(0, start) + max(1, min(count, 200))]]
        return {"kinds": [{"id": k, "count": counts.get(k, 0)} for k in motionlib.KINDS if counts.get(k)],
                "sets": self.decoy_motion_sets(), "rows": rows, "total": len(picked), "start": start}

    def decoy_motion_sets(self) -> dict:
        """Each set of the library: its name, licence and site, whether it comes whole (and how big), how many of its
        moves are kept here, and how far a whole set's fetch has got ("job": state fetching / done / failed)."""
        from rusemod import motionlib
        cat = self._decoy_motions()
        sets = {}
        for s, info in cat["sets"].items():
            state = getattr(self, "_decoy_set_job", {}).get(s, {})
            sets[s] = {"name": info["name"], "licence": info["licence"], "site": info["site"],
                       "whole": bool(info.get("zip")), "size": info.get("zip_size"),
                       **motionlib.set_state(self._home, cat, s), "job": {k: v for k, v in state.items() if k != "thread"}}
        return sets

    def decoy_motion_open(self, move_id: str) -> dict:
        """A library move opened as decoy_mocap_open opens a file (fetched first when it isn't kept here), with the
        stretch its set marks ("from", "length") and its set's credit. {"fetch_set": set} when the move comes with its
        whole set, which isn't here yet."""
        from rusemod import mocap, motionlib
        cat = self._decoy_motions()
        move = next((m for m in cat["moves"] if m["id"] == move_id), None)
        if move is None:
            raise DecoyError(f"{move_id} isn't in the motion library")
        try:
            path = motionlib.fetch(self._home, move)
        except motionlib.MotionLibError as exc:
            if str(exc) == "set":
                return {"fetch_set": move["set"]}
            raise DecoyError(str(exc)) from None
        try:
            bvh = mocap.read_bvh(path.read_text(encoding="utf-8", errors="replace"))
        except (mocap.MocapError, ValueError, IndexError) as exc:
            raise DecoyError(f"{move['name']}: {exc}") from None
        got = self._decoy_mocap_keep("lib:" + move["id"], f"{move['name']} ({move['id']})", bvh)
        start = float(move.get("from") or 0.0)
        end = move.get("to") or bvh.seconds
        got.update({"credit": cat["sets"][move["set"]]["credit"], "from": round(start, 2),
                    "length": round(max(0.2, min(end, bvh.seconds) - start), 2), "move": move["id"]})
        return got

    def decoy_motion_set_fetch(self, set_: str) -> dict:
        """Start fetching a whole set (100STYLE, 1.4 GB) in the background; decoy_motions' "sets" says how far."""
        from rusemod import motionlib
        cat = self._decoy_motions()
        if set_ not in cat["sets"] or not cat["sets"][set_].get("zip"):
            raise DecoyError(f"{set_} isn't a set that comes whole")
        with self._decoy_lock:
            jobs = getattr(self, "_decoy_set_job", {})
            self._decoy_set_job = jobs
            if jobs.get(set_, {}).get("state") == "fetching":
                return {k: v for k, v in jobs[set_].items() if k != "thread"}
            job = jobs[set_] = {"state": "fetching", "done": 0, "total": cat["sets"][set_]["zip_size"], "message": ""}

        def run():
            try:
                motionlib.fetch_set(self._home, cat, set_,
                                    progress=lambda done, total: job.update(done=done, total=total))
                job["state"] = "done"
            except (motionlib.MotionLibError, OSError) as exc:
                job.update(state="failed", message=str(exc))
        started = dict(job)   # as it starts (the page asks decoy_motion_sets how far it has got)
        job["thread"] = threading.Thread(target=run, name=f"motion set {set_}", daemon=True)
        job["thread"].start()
        return started

    def _decoy_mocap_clip(self, member: str, mid: str, start, length, in_place, loop) -> tuple:
        from rusemod import baf, mocap
        r = self._decoy_clip_row(member)
        if r is None:  # not a game rule: no such animation in the game's packs
            raise DecoyError(f"{member} isn't one of the game's animations")
        got = getattr(self, "_decoy_mocap", {}).get(mid)
        if got is None:
            raise DecoyError("Pick the motion capture file again: it's no longer open.")
        for v in (start, length):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
                raise DecoyError("from and how long are seconds")
        base = self._decoy_game_clips()(r["member"])
        try:
            clip, info = mocap.retarget(got[1], baf.parse(base), float(start), float(start) + max(0.1, float(length)),
                                        in_place=bool(in_place), loop=None if loop is None else bool(loop))
        except (mocap.MocapError, baf.ClipError) as exc:
            raise DecoyError(str(exc)) from None
        return r, got[0], baf.build(clip), info

    def decoy_mocap_preview(self, member: str, mid: str, start=0.0, length=2.0, in_place=True, loop=None) -> dict:
        """The motion capture's stretch from `start` for `length` seconds made into clip `member`, on a model that plays
        it, not saved: decoy_anim_preview's answer with "frames", "loop" and "scale"."""
        r, _name, raw, info = self._decoy_mocap_clip(member, mid, start, length, in_place, loop)
        model = self._decoy_preview_model(r)
        if model is None:
            return {"url": None, **info}
        return {**self._decoy_glb(model, raw), **info}

    def decoy_mocap_use(self, member: str, mid: str, start=0.0, length=2.0, in_place=True, loop=None,
                        credit: str = "") -> dict:
        """Keep the clip decoy_mocap_preview showed in the mod: files/replace/<clip>.baf, and beside it <clip>.toml
        (the file it came from, the stretch, the credit). The clip's speed and bone changes still apply on top."""
        from rusemod import anim
        r, name, raw, info = self._decoy_mocap_clip(member, mid, start, length, in_place, loop)
        mod = self._mod_dir()
        if mod is None:
            raise DecoyError("Pick or make a mod first: animations are changed in a mod.")
        own = mod / anim.REPLACE / anim.clip_key(r["member"])
        q = lambda s: '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'  # noqa: E731
        side = "\n".join(["# Where this clip came from (RUSE Decoy's motion capture): carry the credit wherever the mod goes.",
                          f"source = {q(name)}", f"start = {float(start):g}", f"length = {float(length):g}",
                          f"in_place = {'true' if in_place else 'false'}", f"loop = {'true' if info['loop'] else 'false'}",
                          f"credit = {q(credit)}", ""])
        with self._saving:
            own.parent.mkdir(parents=True, exist_ok=True)
            tmp = own.with_suffix(".part")
            tmp.write_bytes(raw)
            tmp.replace(own)
            own.with_suffix(".toml").write_text(side, encoding="utf-8")
        return {**self._decoy_clip_out(r, self._decoy_clip_edits()), **info}

    def decoy_anim_set(self, member: str, speed=None, use=None, bone: str | None = None, size=None, turn=None) -> dict:
        """Change a clip in the current mod (files/anim/clips.toml): its `speed` (percent), `use` another clip of the
        same bones in its place ("" takes that out), or a `bone`'s `size` and `turn` (["x"|"y"|"z", degrees]; size 1
        and no turn take the bone out). What's not given is kept."""
        from rusemod import anim
        r = self._decoy_clip_row(member)
        if r is None:  # not a game rule: no such animation in the game's packs
            raise DecoyError(f"{member} isn't one of the game's animations")
        mod = self._mod_dir()
        if mod is None:
            raise DecoyError("Pick or make a mod first: animations are changed in a mod.")
        f = mod / anim.CLIPS
        with self._saving:
            table = {}
            if f.is_file():
                try:
                    table = tomllib.loads(f.read_text(encoding="utf-8")).get("clip", {})
                except tomllib.TOMLDecodeError as exc:
                    raise DecoyError(f"{anim.CLIPS}: {exc}") from None
            key = anim.clip_key(r["member"])
            entry = dict(table.get(key, {}))
            if speed is not None:
                if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not 1 <= speed <= 1000:
                    raise DecoyError("a speed is a percent from 1 to 1000")
                entry["speed"] = float(speed)
                if float(speed) == 100.0:
                    entry.pop("speed")
            if use is not None:
                if use:
                    other = self._decoy_clip_row(use)
                    if other is None or other["skeleton"] != r["skeleton"]:
                        raise DecoyError("only a clip of the same bones can stand in")
                    entry["from"] = anim.clip_key(other["member"])
                else:
                    entry.pop("from", None)
            if bone is not None:
                if bone.lower() not in r["skeleton"].split("|"):
                    raise DecoyError(f"this animation has no bone {bone}")
                bones = dict(entry.get("bone", {}))
                b = dict(bones.get(bone, {}))
                if size is not None:
                    b["size"] = float(size)
                if turn is not None:
                    b["turn"] = list(turn) if turn else None
                b = {k: v for k, v in b.items() if v is not None and not (k == "size" and v == 1.0)
                     and not (k == "turn" and (not v or v[1] == 0))}
                if b:
                    bones[bone] = b
                else:
                    bones.pop(bone, None)
                entry["bone"] = bones
                if not bones:
                    entry.pop("bone")
            if entry:
                table[key] = entry
            else:
                table.pop(key, None)
            text = self._decoy_clips_toml(table)
            if text is None:
                if f.is_file():
                    f.unlink()
            else:
                f.parent.mkdir(parents=True, exist_ok=True)
                tmp = f.with_suffix(".part")
                tmp.write_text(text, encoding="utf-8")
                anim.mod_clips(mod)  # (raises on anything the build wouldn't take)
                tmp.replace(f)
        try:
            anim.mod_clips(mod)
        except anim.AnimError as exc:
            raise DecoyError(str(exc)) from None
        return self._decoy_clip_out(r, self._decoy_clip_edits())

    @staticmethod
    def _decoy_clips_toml(table: dict) -> str | None:
        if not table:
            return None
        q = lambda s: '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'  # noqa: E731
        lines = ["# A mod's animations: each of the game's clips by its path in the game's packs. RUSE Decoy writes it;",
                 "# the build makes each clip again and puts it in every pack that holds it.", ""]
        for key in sorted(table):
            e = table[key]
            lines.append(f"[clip.{q(key)}]")
            if "speed" in e:
                lines.append(f"speed = {e['speed']:g}")
            if e.get("from"):
                lines.append(f"from = {q(e['from'])}")
            for bone, b in sorted((e.get("bone") or {}).items()):
                lines.append(f"[clip.{q(key)}.bone.{q(bone)}]")
                if "size" in b:
                    lines.append(f"size = {b['size']:g}")
                if b.get("turn"):
                    lines.append(f"turn = [{q(b['turn'][0])}, {float(b['turn'][1]):g}]")
            lines.append("")
        return "\n".join(lines)

    def decoy_anim_reset(self, member: str) -> dict:
        """Take every change the mod makes to a clip out (its line in clips.toml; a whole clip of its own too)."""
        from rusemod import anim
        r = self._decoy_clip_row(member)
        if r is None:  # not a game rule: no such animation in the game's packs
            raise DecoyError(f"{member} isn't one of the game's animations")
        mod = self._mod_dir()
        if mod is None:
            return {"member": r["member"]}
        f = mod / anim.CLIPS
        with self._saving:
            if f.is_file():
                table = tomllib.loads(f.read_text(encoding="utf-8")).get("clip", {})
                table.pop(anim.clip_key(r["member"]), None)
                text = self._decoy_clips_toml(table)
                if text is None:
                    f.unlink()
                else:
                    f.write_text(text, encoding="utf-8")
            own = mod / anim.REPLACE / anim.clip_key(r["member"])
            for f in (own, own.with_suffix(".toml")):   # a motion capture's clip and its credit
                if f.is_file():
                    f.unlink()
        return {"member": r["member"]}

    def decoy_unit_anims(self, address: str) -> dict:
        """A unit's own clips (its models' animations, a gun's crew's too), by the name its model gives each."""
        from rusemod import animlist
        try:
            edits = self._edits()
        except Exception:  # a mod file that can't be read: the game's own unit is still shown
            edits = None
        real, _new = self._resolve(edits, address)
        ix = self._open()
        try:
            items = animlist.unit_clips(ix.db, real.split(":", 1)[0])
        finally:
            ix.close()
        cedits = self._decoy_clip_edits()
        rows, seen = [], set()
        for member, name in items:
            r = self._decoy_clip_row(member)
            if r is None or member in seen:
                continue
            seen.add(member)
            row = self._decoy_clip_out(r, cedits)
            row["role"] = name
            rows.append(row)
        return {"rows": rows, "total": len(rows), "start": 0}

    def decoy_unit_volume(self, address: str, percent) -> dict:
        """Every one of a unit's own sounds at `percent` at once."""
        _real, items = self._decoy_unit_sounds(address)
        members = [m for m, _role, _x in items if self._decoy_row(m) is not None]
        if not members:
            raise DecoyError("this unit has no sounds of its own here")
        saved = self._decoy_save_volumes({m: percent for m in members})
        return {"count": len(members), "volume": int(round(percent)), "saved": saved}

    def _decoy_replaced(self) -> set:
        """The game sounds the current mod replaced (files/replace/<path>.ess.wav)."""
        mod = self._mod_dir()
        return set(sound.mod_sounds(mod)) if mod is not None else set()

    def decoy_volume(self, member: str, percent) -> dict:
        """The current mod plays the game's sound `member` at `percent` (0 to 200; 100 takes it out): saved in
        files/sound/volume.toml, every other sound's kept."""
        row = self._decoy_row(member)
        if row is None:
            # not a game rule: the page named a sound the game hasn't got
            raise DecoyError(f"{member} isn't one of the game's sounds")
        saved = self._decoy_save_volumes({row["member"]: percent})
        return {"member": row["member"], "volume": int(round(percent)), "saved": saved}

    def _decoy_save_volumes(self, change: dict) -> str:
        """Set {member: percent} in the current mod's files/sound/volume.toml at once (100 takes a sound out)."""
        for percent in change.values():
            if isinstance(percent, bool) or not isinstance(percent, (int, float)) or not 0 <= percent <= sound.MOST_VOLUME:
                # not a game rule: the slider's range
                raise DecoyError(f"a volume is a percent from 0 to {sound.MOST_VOLUME}")
        mod = self._mod_dir()
        if mod is None:
            raise DecoyError("Pick or make a mod first: a sound's volume is saved in a mod.")
        f = mod / sound.VOLUMES
        with self._saving:
            vols = sound.mod_volumes(mod) if f.is_file() else {}
            for member, percent in change.items():
                pct = int(round(percent))
                if pct == 100:
                    vols.pop(member, None)
                else:
                    vols[member] = pct
            if not vols:
                if f.is_file():
                    f.unlink()
            else:
                lines = ["# How loud this mod plays the game's sounds: percent of the game's own (100 = as the game,",
                         "# 0 = silent, up to 200). RUSE Decoy writes it; the build makes each sound again at its volume.",
                         "[volume]"]
                lines += [f"{_toml_key(m)} = {v}" for m, v in sorted(vols.items())]
                f.parent.mkdir(parents=True, exist_ok=True)
                tmp = f.with_suffix(".part")
                tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
                tomllib.loads(tmp.read_text(encoding="utf-8"))   # read back before it replaces the old one
                tmp.replace(f)
        return str(f)

    def decoy_volume_all(self, kind: str, percent, mission: str | None = None, in_lang: str | None = None) -> dict:
        """Every sound of a kind (a mission's, a language's) at `percent`: a whole kind louder or quieter at once."""
        rows = [r for r in self._decoy_rows() if r["kind"] == kind and (not mission or r["mission"] == mission)
                and (not in_lang or r["lang"] == in_lang)]
        if not rows:
            raise DecoyError(f"no sounds of the kind {kind} here")
        saved = self._decoy_save_volumes({r["member"]: percent for r in rows})
        return {"count": len(rows), "volume": int(round(percent)), "saved": saved}
