"""Map Paint's textures in the Studio (StudioApi's GroundTextureCalls; rusemod.groundtex): what the Texture brush can
paint with besides a spot of the same map. The owner, 2026-10-09: "On a blank map, there is no spot to copy from, so
how are you supposed to make textures? We need to add all of the game textures into this, and then make it very easy
to be able to add cool textures to your map."

- The game's ground textures: every one its maps are dressed with up close (grass, fields, earth, sand, rock, snow,
  wet ground, roads, town ground, battle damage, markings), read from the player's own game; their small pictures
  are made once per game build and kept in the cache.
- A square of any map's ground: the map's overview to click on, and the square's picture.
- The mod's own pictures (files/ground/<name>.png): the page turns any picture the browser can show into a PNG of
  its middle square and sends it here.
- Online (free) textures (groundtex_online): Poly Haven's and ambientCG's (CC0) and US aerial photos (public domain),
  listed from their sites (kept a day) and downloaded one at a time, only the one the modder clicks; the page makes
  it a PNG of its middle square and keeps it as one of the mod's own pictures, with its real size and credit beside it
  (files/ground/<name>.toml).
Each texture's picture for the page to paint with is the one the build lays (groundtex.Swatch: made seamless), at
up to PREVIEW pixels across."""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import math
import re
from contextlib import nullcontext

from rusemod import groundtex as gt
from rusemod.build import find_pack
from rusemod.dxt import png_bytes
from rusemod.edat import Edat
from rusemod.terrain import pack_file
from rusemod.webui import Job

from . import groundtex_online as online

PREVIEW = 128        # pixels across the picture the page paints its preview with
THUMB = 64           # pixels across a texture's small picture in the list
CATALOGUE_FORMAT = 1  # the kept list's own format: a new one makes it again
PICTURE_MOST = 4096  # pixels across a picture of the mod's own, at most (it is cut to its middle square, 1,024 at most)
CREDIT_MOST = 300    # characters kept of each of a picture's credit's words (source, author, licence, url)


def _png_url(n: int, rgba: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png_bytes(rgba, n, n, 4)).decode("ascii")


def _small(n: int, rgba: bytes, side: int) -> tuple[int, bytes]:
    """A square picture halved until it is `side` across or less."""
    while n > side:
        rgba = gt.halve(n, rgba)
        n //= 2
    return n, rgba


def _file_name(name: str) -> str:
    """A picture's name for files/ground: letters, digits, spaces, dots, dashes and _ kept, the rest made _,
    ending .png."""
    stem = re.sub(r"\.(png|jpe?g|webp|gif|bmp)$", "", str(name or "").strip(), flags=re.I)
    stem = re.sub(r"[^A-Za-z0-9_ .-]", "_", stem).strip(" .") or "picture"
    if not re.match(r"[A-Za-z0-9_]", stem):
        stem = "_" + stem
    return stem[:76] + ".png"


def _metres(metres) -> float | None:
    """A picture's real size across (metres), checked: None when not given, TextureError when it isn't one."""
    if metres in (None, "", 0):
        return None
    if isinstance(metres, bool) or not isinstance(metres, (int, float)) or not math.isfinite(metres) or not (
            0 < metres <= gt.METRES_MOST):
        raise gt.TextureError(f"A picture covers 0 to {gt.METRES_MOST:,.0f} m across, not {metres!r}.")
    return float(metres)


class GroundTextureCalls:
    """Mixed into StudioApi: uses its _game, _map_dir, cache_dir, _saving, _jobs, _grounds_lock and _ground_jobs."""

    def _texture_packs(self):
        """(ZZ_Win.dat, ZZ_GladPatchableWin.dat) paths in the game, or TextureError."""
        game = self._game()
        if game is None:
            # not a game rule: the game or one of its files isn't found
            raise gt.TextureError("We couldn't find R.U.S.E., so its ground textures can't be read.")
        zz, glad = find_pack(game, "ZZ_Win.dat"), find_pack(game, "ZZ_GladPatchableWin.dat")
        if zz is None:
            # not a game rule: the game or one of its files isn't found
            raise gt.TextureError("ZZ_Win.dat isn't in the game folder, so its ground textures can't be read.")
        return zz, glad

    def _catalogue_dir(self):
        zz, _glad = self._texture_packs()
        st = zz.stat()
        return self.cache_dir / "groundtex" / f"{st.st_size}-{int(st.st_mtime)}-v{CATALOGUE_FORMAT}"

    def ground_textures(self) -> dict:
        """The game's ground textures to paint with: {"base": "cache/groundtex/<build>/", "textures": [{"ref",
        "theatres", "group", "words", "period" (map units a repeat in the game), "see_through", "thumb"}], "groups":
        groundtex.GROUP_ORDER} once their small pictures are made (once per game build, under a minute), else
        {"job": id}; ask again when the job is done."""
        folder = self._catalogue_dir()
        index = folder / "index.json"
        base = f"cache/groundtex/{folder.name}/"
        if index.is_file():
            return {"base": base, "groups": gt.GROUP_ORDER, **json.loads(index.read_text(encoding="utf-8"))}
        name = f"groundtex:{folder.name}"
        with self._grounds_lock:
            running = self._ground_jobs.get(name)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            self._jobs[job.id] = job
            self._ground_jobs[name] = job.id
        zz_path, glad_path = self._texture_packs()

        def work(say):
            with Edat.open(str(zz_path)) as zz:
                glad = Edat.open(str(glad_path)) if glad_path else None
                try:
                    cat = gt.catalogue(zz, glad)
                finally:
                    if glad is not None:
                        glad.close()
                folder.mkdir(parents=True, exist_ok=True)
                rows = []
                for k, t in enumerate(cat, 1):
                    thumb = re.sub(r"[^a-z0-9]+", "_", t.ref.lower()) + ".png"
                    try:
                        w, h, px = gt.tgv_rgba(bytes(zz.read(zz.entry(gt.game_member(t.ref)))), THUMB)
                    except (gt.TextureError, ValueError):
                        continue  # (a picture that can't be read isn't listed)
                    n, sq = _small(*gt.square(w, h, px), THUMB)
                    (folder / thumb).write_bytes(png_bytes(sq, n, n, 4))
                    rows.append({"ref": t.ref, "theatres": t.theatres, "group": t.group, "words": t.words,
                                 "period": t.period, "see_through": t.see_through, "thumb": thumb})
                    if k % 20 == 0 or k == len(cat):
                        say(f"{k}/{len(cat)}")
            part = index.with_name("index.json.part")
            part.write_text(json.dumps({"textures": rows}), encoding="utf-8")
            part.replace(index)

        return job.start(work, "The game's ground textures are ready.")

    def _own_picture(self, name: str):
        folder = self._map_dir()
        if folder is None:
            raise gt.TextureError("Pick or make a mod first: its pictures are kept in it.")
        if not gt.file_name_ok(name):
            raise gt.TextureError(f"{name!r} isn't a picture's name in {gt.GROUND.as_posix()}")
        return folder / gt.GROUND / name

    def ground_texture(self, ref: str) -> dict:
        """One texture as the build lays it, for the page to paint its preview with: {"ref", "period" (map units a
        repeat at its own size), "n", "png": its picture made seamless, up to PREVIEW across, as a data URL}. A map's
        square is kept in the cache (it takes a few seconds)."""
        gt.check_ref(ref)
        kind = ref.split(":", 1)[0]
        if kind == "file":
            path = self._own_picture(ref[5:])
            lib = gt.Library(files={ref: path})
            made = lib.swatch(ref, PREVIEW)
        elif kind == "game":
            zz_path, glad_path = self._texture_packs()
            index = self._catalogue_dir() / "index.json"
            periods = None
            if index.is_file():  # each one's own size, from the list made once (reading the game's data takes longer)
                rows = json.loads(index.read_text(encoding="utf-8"))["textures"]
                periods = {gt.game_member(t["ref"]).lower(): t["period"] for t in rows}
            with Edat.open(str(zz_path)) as zz:
                glad = Edat.open(str(glad_path)) if glad_path and periods is None else None
                try:
                    made = gt.Library(zz, glad, periods=periods).swatch(ref, PREVIEW)
                finally:
                    if glad is not None:
                        glad.close()
        elif kind == "swatch":
            made = self._palette_swatch(ref)
        else:
            made = self._map_square(ref)
        n, px = _small(*made.mips[0], PREVIEW)
        out = {"ref": ref, "period": made.period, "n": n, "png": _png_url(n, px), "mirrored": made.mirrored}
        if made.grain:   # a palette swatch's grain, laid by itself over the colour (groundtex.Swatch.grain_sampler)
            gn, g = next(((k, g) for k, g in made.grain if k <= PREVIEW), made.grain[-1])
            out.update(grain=_png_url(gn, bytes(v for b in g for v in (b, b, b, 255))), grain_n=gn,
                       grain_period=made.grain_period, grain_unit=gt.GRAIN_UNIT)
        return out

    def repaint_preview(self, pack: str) -> dict:
        """What the build paints for the current mod's repaint strokes on a map (rusemod.repaint, Map Paint plan step
        8), for the page to show: the map's ground with the mod's ground brushes applied as the build applies them
        (terrain_edit.edit_map; a new map whose ground is drawn as our own, map.toml ground = "generated", drawn the
        same way: rusemod.groundgen), then the rules, what moved measured from the flat start on a map that starts
        flat (repaint.start_level): {"strokes": [the texture strokes, the terrain file's keys], "said": what was laid
        in words} once worked out (seconds to a minute; kept in the cache by the strokes and the map), else
        {"job": id}; ask again when the job is done. {"strokes": []} without a repaint stroke."""
        from dataclasses import asdict
        from rusemod.brush import PAINT_KINDS
        from rusemod.groundgen import GroundGenError, generate
        from rusemod.repaint import RepaintError, expand, start_level
        from rusemod.terrain_edit import edit_map
        with self._saving:
            strokes = self._read_strokes(self._terrain_file(pack))
        repaints = [s for s in strokes if s.kind.kind == "repaint"]
        if not repaints:
            return {"strokes": [], "said": ""}
        ground = [s for s in strokes if s.kind.kind not in PAINT_KINDS + ("repaint", "cover", "block", "open")]
        game = self._game()
        source = self._game_pack(pack)
        path = find_pack(game, pack_file(source)) if game is not None else None
        if path is None:  # not a game rule: the map's file isn't in the game folder
            raise gt.TextureError(f"The map {source} isn't in this game.")
        st = path.stat()
        spec = self._new_maps().get(pack.lower())
        drawn = spec is not None and spec[1].ground == "generated"
        said = json.dumps([asdict(s) for s in strokes if s.kind.kind not in PAINT_KINDS], sort_keys=True, default=str)
        key = hashlib.sha1(f"{source}|{st.st_size}|{int(st.st_mtime)}|{drawn}|{said}".encode()).hexdigest()[:24]
        kept = self.cache_dir / "repaint" / f"{key}.json"
        if kept.is_file():
            return json.loads(kept.read_text(encoding="utf-8"))
        name = f"repaint:{key}"
        with self._grounds_lock:
            running = self._ground_jobs.get(name)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            self._jobs[job.id] = job
            self._ground_jobs[name] = job.id

        def work(say):
            say("the ground brushes")
            with Edat.open(str(path)) as arc:
                def read(member):
                    try:
                        return bytes(arc.read(arc.find(member)))
                    except KeyError:
                        return None
                old = read("output\\highdef.tms")
                changed = None
                if drawn:
                    try:
                        changed, _notes = generate(read, ground, source, None)
                    except GroundGenError:   # (the build draws it the usual way too)
                        changed = None
                if changed is None:
                    changed, _notes = edit_map(read, ground, source)
            new = next((v for k, v in changed.items() if k.lower().endswith("highdef.tms")), old)
            say("the rules")
            try:
                laid, words = expand(repaints, old, new, [s for s in ground if s.kind.kind == "water"],
                                     start_level(ground, old))
            except RepaintError as exc:
                raise gt.TextureError(str(exc)) from None
            keys = ("brush", "x", "y", "radius", "shape", "edge", "texture", "mask")
            by_shape = {"line": ("x2", "y2"), "square": ("dx", "dy", "length")}   # (the terrain file's own keys)
            out = {"strokes": [{k: getattr(s, k) for k in keys + by_shape.get(s.shape, ())} for s in laid],
                   "said": words}
            kept.parent.mkdir(parents=True, exist_ok=True)
            kept.write_text(json.dumps(out), encoding="utf-8")

        return job.start(work, "What moved is worked out.")

    def brush_masks(self) -> dict:
        """The brushes that are pictures (rusemod.brushmask), for the page to preview strokes with the build's own
        values: {"size": values across, "turns": a round dab's turnings [[ax, ay]], "edge": the masks that set how far
        a stroke reaches, "rag_in": the reach where such a mask is 0, "masks": {name: its values as base64}} in
        brushmask.MASKS's order."""
        from rusemod import brushmask
        return {"size": brushmask.SIZE, "turns": [list(t) for t in brushmask.TURNS],
                "edge": list(brushmask.EDGE_MASKS), "rag_in": brushmask.RAG_IN,
                "masks": {n: base64.b64encode(brushmask.make(n)).decode("ascii") for n in brushmask.MASKS}}

    def _palette_kept(self, ref: str, pal: dict):
        """(the swatch's row, its map's pack, its pixels across, where its picture is kept): the build's pixels across
        or PREVIEW if fewer; TextureError for a swatch the palette hasn't or a map the game hasn't."""
        got = pal.get(ref)
        if got is None:  # not a game rule: the palette's own list
            raise gt.TextureError(f"The palette has no {ref[7:]}.")
        game = self._game()
        path = find_pack(game, pack_file(got.map)) if game is not None else None
        if path is None:  # not a game rule: the map's file isn't in the game folder
            raise gt.TextureError(f"The map {got.map} isn't in this game.")
        n = min(PREVIEW, gt.need(got.side))
        st = path.stat()
        said = (f"{ref}|{got.x}|{got.y}|{got.side}|{got.facing}|{n}|{st.st_size}|{int(st.st_mtime)}|{got.detail}|"
                f"{got.detail_side}")
        key = hashlib.sha1(said.encode()).hexdigest()[:20]
        return got, path, n, self.cache_dir / "groundtex" / "palette" / f"{key}.png"

    def _palette_swatch(self, ref: str, pal: dict | None = None) -> gt.Swatch:
        """A palette swatch as the build makes it (its map's square read turned to its rows, with the game's own
        grain where it names it: groundtex.swatch_pixels), at the build's pixels across or PREVIEW if fewer; its
        picture kept in the cache (reading the map takes seconds)."""
        got, path, n, kept = self._palette_kept(ref, pal if pal is not None else gt.palette())
        grained = kept.with_name(kept.stem + "-grain.png")   # (its grain beside it: one byte a pixel, kept as grey)
        if kept.is_file():
            _w, _h, px = gt.picture_rgba(kept.read_bytes())
            grain = None
            if grained.is_file():
                gn, _h, gpx = gt.picture_rgba(grained.read_bytes())
                grain = (gn, gpx[0::4], got.side / gt.detail_repeats(got.side, got.detail_side))
            return gt.Swatch.make(ref, n, px, got.side, mirrored=True, grain=grain)
        game = self._game()
        zz_path = find_pack(game, "ZZ_Win.dat") if game is not None and got.detail else None
        with Edat.open(str(path)) as arc, (Edat.open(str(zz_path)) if zz_path else nullcontext()) as zz:
            def read(member):
                try:
                    return bytes(arc.read(arc.find(member)))
                except KeyError:
                    return None
            n, px, grain = gt.swatch_pixels(got, read, n, zz, self.cache_dir / "groundtex" / "tiles")
        kept.parent.mkdir(parents=True, exist_ok=True)
        if grain is not None:
            gn, gpx, _rep = grain
            grained.write_bytes(png_bytes(bytes(v for b in gpx for v in (b, b, b, 255)), gn, gn, 4))
        kept.write_bytes(png_bytes(px, n, n, 4))
        return gt.Swatch.make(ref, n, px, got.side, mirrored=True, grain=grain)

    def ground_palette(self) -> dict:
        """The named palette (groundtex.palette: materials measured on the game's own maps) to paint with:
        {"swatches": [{"ref", "theme", "name", "label" (English: the page says its own words), "map" (whose ground),
        "kind" (rows: a field's, laid turned with Turn; plain), "period" (map units a repeat), "thumb": a small picture
        as a data URL}]} once their pictures are made (a few seconds the first time; kept), else {"job": id}; ask again
        when the job is done."""
        pal = gt.palette()
        rows = []

        def row(p, made):
            n, px = _small(*made.mips[0], THUMB)
            return {"ref": p.ref, "theme": p.theme, "name": p.name, "label": p.label, "map": p.map, "kind": p.kind,
                    "period": p.side, "thumb": _png_url(n, px)}
        try:
            for p in pal.values():
                if not self._palette_kept(p.ref, pal)[3].is_file():
                    break
                rows.append(row(p, self._palette_swatch(p.ref, pal)))
            else:
                return {"swatches": rows}
        except gt.TextureError as exc:
            return {"swatches": [], "error": str(exc)}
        name = "groundtex:palette"
        with self._grounds_lock:
            running = self._ground_jobs.get(name)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            self._jobs[job.id] = job
            self._ground_jobs[name] = job.id

        def work(say):
            for k, p in enumerate(pal.values(), 1):
                self._palette_swatch(p.ref, pal)
                say(f"{k}/{len(pal)}")

        return job.start(work, "The palette's pictures are ready.")

    def _map_square(self, ref: str) -> gt.Swatch:
        _, pack, _x, _y = ref.split(":")
        game = self._game()
        path = find_pack(game, pack_file(pack)) if game is not None else None
        if path is None:  # not a game rule: the map's file isn't in the game folder
            raise gt.TextureError(f"The map {pack} isn't in this game.")
        st = path.stat()
        key = hashlib.sha1(f"{ref}|{st.st_size}|{int(st.st_mtime)}".encode()).hexdigest()[:20]
        kept = self.cache_dir / "groundtex" / "squares" / f"{key}.png"
        if kept.is_file():
            w, h, px = gt.picture_rgba(kept.read_bytes())
            return gt.Swatch.make(ref, w, px, gt.MAP_SIDE)
        with Edat.open(str(path)) as arc:
            def read(member):
                try:
                    return bytes(arc.read(arc.find(member)))
                except KeyError:
                    return None
            # (PREVIEW points across, not the build's 512: a page's preview, in a second instead of several)
            n, px = gt.map_square(read, float(_x), float(_y), self.cache_dir / "groundtex" / "tiles", PREVIEW)
        kept.parent.mkdir(parents=True, exist_ok=True)
        kept.write_bytes(png_bytes(px, n, n, 4))
        return gt.Swatch.make(ref, n, px, gt.MAP_SIDE)

    def map_overview(self, pack: str) -> dict:
        """A map's small overview picture to pick a square of its ground on: {"pack", "picture": a data URL,
        "bounds": [x0, y0, x1, y1] it covers (map units; row 0 at y0)}."""
        from rusemod.terrain import PICTURE
        from rusemod.groundpaint import map_bounds
        game = self._game()
        path = find_pack(game, pack_file(pack)) if game is not None and re.fullmatch(r"[A-Za-z0-9_]+", pack) else None
        if path is None:  # not a game rule: the map's file isn't in the game folder
            raise gt.TextureError(f"The map {pack} isn't in this game.")
        with Edat.open(str(path)) as arc:
            mesh = bytes(arc.read(arc.find("output\\highdef.tms")))
            try:
                png = bytes(arc.read(arc.find(PICTURE)))
            except KeyError:
                raise gt.TextureError(f"The map {pack} has no overview picture.") from None
        x0, y0, x1, y1 = map_bounds(mesh)
        return {"pack": pack, "picture": "data:image/png;base64," + base64.b64encode(png).decode("ascii"),
                "bounds": [x0, y0, x1, y1]}

    def map_texture(self, pack: str, x: float, y: float) -> dict:
        """A square of a map's ground, centred at (x, y), to paint with: ground_texture's answer for its ref."""
        ref = f"map:{pack}:{round(float(x))}:{round(float(y))}"
        return self.ground_texture(ref)

    def ground_pictures(self) -> dict:
        """The current mod's own pictures to paint with (files/ground/*.png): {"pictures": [{"ref": "file:<name>",
        "name", "thumb": a small copy as a data URL, "period": map units a repeat at its own size, and from its sidecar
        (files/ground/<name>.toml) when it has one: "metres" it covers across and "credit": {"source", "author",
        "licence", "url"}}], "folder": where they are, or None without a mod}."""
        folder = self._map_dir()
        if folder is None:
            return {"pictures": [], "folder": None}
        where = folder / gt.GROUND
        out = []
        for f in sorted(where.glob("*.png"), key=lambda p: p.name.lower()) if where.is_dir() else []:
            if not gt.file_name_ok(f.name):
                continue
            try:
                n, px = _small(*gt.square(*gt.picture_rgba(f.read_bytes())), THUMB)
            except (ValueError, OSError):
                continue  # (the mod check says what's wrong with it)
            said = gt.read_credit(f)
            row = {"ref": f"file:{f.name}", "name": f.stem, "thumb": _png_url(n, px), "period": gt.file_period(f)}
            if "metres" in said:
                row["metres"] = said["metres"]
            credit = {k: said[k] for k in gt.CREDIT_KEYS if k in said}
            if credit:
                row["credit"] = credit
            out.append(row)
        return {"pictures": out, "folder": str(where)}

    def add_ground_picture(self, name: str, picture: str, metres: float | None = None,
                           credit: dict | None = None) -> dict:
        """Keep a picture in the current mod to paint with: `picture` a PNG as a data URL (the page makes one of any
        picture), saved as files/ground/<name>.png (a name already there gets _2, _3...). With `metres` (the ground
        the picture covers across, its real size) or `credit` ({"source", "author", "licence", "url"}: where it comes
        from, an online texture's) they're kept beside it, files/ground/<name>.toml, and the picture is laid at its
        real size. Returns ground_pictures() with "ref" the new one's."""
        folder = self._map_dir()
        if folder is None:
            raise gt.TextureError("Pick or make a mod first: its pictures are kept in it.")
        try:
            data = base64.b64decode(str(picture).split(",", 1)[-1], validate=True)
            w, h, _px = gt.picture_rgba(data)
        except (ValueError, TypeError, binascii.Error) as exc:
            raise gt.TextureError(f"That picture can't be read ({exc}).") from None
        if not (w and h) or max(w, h) > PICTURE_MOST:
            raise gt.TextureError(f"That picture is {w} x {h}: up to {PICTURE_MOST} pixels across, please.")
        side = _metres(metres)
        said = {k: str(credit[k])[:CREDIT_MOST] for k in gt.CREDIT_KEYS
                if isinstance(credit, dict) and isinstance(credit.get(k), str) and credit[k].strip()}
        where = folder / gt.GROUND
        base = _file_name(name)
        file, k = where / base, 2
        while file.exists() or gt.credit_path(file).exists():  # (a sidecar left behind isn't another picture's)
            file, k = where / f"{base[:-4]}_{k}.png", k + 1
        with self._saving:
            where.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
            if side or said:
                gt.credit_path(file).write_text(gt.credit_toml(side, said), encoding="utf-8")
        return {**self.ground_pictures(), "ref": f"file:{file.name}"}

    def online_textures(self, source: str, words: str = "") -> dict:
        """Free ground pictures to download, from `source`: "polyhaven" (Poly Haven's aerial textures, then its
        terrain ones; CC0), "ambientcg" (ambientCG's materials found by `words`; CC0) or "usgs" (US aerial photos'
        places; public domain). {"source", "licence", "items": [{"id", "name", "metres" (real metres across, None when
        not known), "thumb" (the site's own small picture), "tags", "author"}]} (usgs: [{"id", "name", "lat", "lon",
        "group"}], with "metres": the photo sizes to choose from, and "default"). The lists are kept a day in the
        cache; nothing else is downloaded here."""
        return online.listing(self.cache_dir / "groundtex" / "online", str(source), str(words or ""))

    def online_texture(self, source: str, item: str = "", metres: float = 0, where: str = "") -> dict:
        """Download ONE free picture, the one the modder clicked: `item` an id from online_textures (usgs: a place's,
        or none and `where` a typed "latitude, longitude"; `metres` the photo's side). {"name", "picture": a JPG or
        PNG data URL, "metres", "credit": {"source", "author", "licence", "url"}}: the page makes it a PNG of its
        middle square and keeps it with add_ground_picture."""
        try:
            side = float(metres or 0)
        except (TypeError, ValueError):
            raise gt.TextureError("A photo's size is a number of metres.") from None
        return online.picture(self.cache_dir / "groundtex" / "online", str(source), str(item or ""), side,
                              str(where or ""))
