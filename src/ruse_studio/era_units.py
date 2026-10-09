"""Era units in the Units tab (StudioApi's EraUnitCalls): RUSE 2.0's base models for four eras (WWI, WWII+, Cold War,
Modern), each another maker's free model (CC0 or CC BY), credited, already fitted and given its nation's markings
(owner 2026-10-08: "add what we have to the studio ... these were all of the what CCO, CC BY ones that we could
include in our game. There's plenty more out there").

They're listed in the Units tab beside the game's own units (owner 2026-10-08: "Why is it not with the rest of the
units? ... the existing ones are in the ... vanilla section. And then there's a World War One, World War Two plus, Cold
War, Modern"): the era filter picks Vanilla (the game's units) or an era. Every era unit is OFF until a modder adds it
(owner 2026-10-08: "I don't want all of these just to automatically be units"). Adding one makes it a new unit of the
current mod: it starts from the values of a game unit the modder picks (owner 2026-10-08: "what if they don't want to
make it the same as a Sherman?": the library only suggests one), with the name, price and build menu given, gets its
model (Import model's step) and its credit in the mod's credits file; then it's a new unit like any other, every value
changed on its page. Taking it out deletes that unit again.

Its size (owner 2026-10-09: "the units we add should be scaled proportionally with how big the units are ... in real
life"): the importer makes a model as long as the start unit's hull times a size (1: as long). The size suggested is
the one that gives it its real width (an aircraft: its wingspan), when the library gives that ("real": {"width_m",
"span_m"} per unit) and the game units in a metre ("units_per_metre": {"ground", "air"} at the library's top); else 1,
as before. The modder can change it.

Researched from (owner 2026-10-09: "If it's advanced, I want it to be hidden behind the research ... The person should
be able to choose what tank it replaces ... it has to be super customizable"): the add form offers the units of the
build menu picked (the Upgrade box's choices, the mod's new units too, so era units chain: a T-80, then a T-90
researched from it) or none (buyable from the start), with a research price and time. Suggested: the start unit when
it's in that menu, else the unit the era unit stands in for ("in_place_of") when it's there, else for Cold War and
Modern units the dearest unit of the menu, else none. After adding, the unit page's Upgrade box changes it.

The library: a folder holding era_units.json, the fitted models, their pictures and their cards (each unit's model
drawn at the game's card size: added, it's the new unit's own card) (RUSE_ERA_UNITS, else the eras the
Studio downloaded, else an era_units folder beside the Studio's program, else beside its source). The mod keeps which
era units it has in era_units.json and the credits in CREDITS-era-units.md, both in the mod's folder.

The download (owner 2026-10-08: "have the studio just download each of the sections we already made ... build enough
files to where they're under the 2 gigabytes and have the studio auto-update with them"): each era is a section of
RUSE 2.0's GitHub release `era-units`, in .zip files under 2 GB each. The release's era-units.json lists every section:
its version, its files (size and SHA-256) and its units. An era downloads when the modder picks it and presses
Download; every file is checked against the list before it's used, and only models and pictures inside the era's own
folders (or pictures/) are taken from it. A downloaded era updates itself when the list holds a newer version of it,
so eras still being finished arrive as they're put up, without a new Studio."""
from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from rusemod.mod_index import plain
from rusemod.webui import Job

LIBRARY_ENV = "RUSE_ERA_UNITS"
INDEX = "era_units.json"          # in the library: the units; in a mod: {era unit key: its new unit's address}
CREDITS = "CREDITS-era-units.md"  # in a mod: the makers of the era units it has, as their licences ask
ERAS = ("WWI", "WWII", "Cold War", "Modern")
# the Units tab's nation chips: the game's seven nations by number, China (no game nation of its own) as 7
NATION_CODE = {"USA": 0, "Germany": 1, "UK": 2, "France": 3, "Italy": 4, "USSR": 5, "Russia": 5, "Japan": 6, "China": 7}
CLASS_OF = {"ground": "TUniteAuSolDescriptor", "air": "TAvionDescriptor"}
FACING = (0, 1)                   # a library model's way: already in the game's axes, its front +x (era_unit_add)
REAL_OF = {"ground": "width_m", "air": "span_m"}    # a unit's real size the library gives: its width, a plane's span
SCALE = "units_per_metre"         # at the library's top: {"ground": k, "air": k}, the game's units in a metre
RESEARCH_ERAS = ("Cold War", "Modern")              # put behind research when nothing closer suggests a parent
SUGGESTED = "suggested"           # era_unit_add's research_from: the one the add form suggests


SECTIONS_URL = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/download/era-units/"
URL_ENV = "RUSE_ERA_UNITS_URL"    # another place for the list and its files, ending in "/" (a test's, a local copy)
LIST = "era-units.json"           # the release's list of sections
DOWNLOADED = "era_units"          # in the platform folder: the downloaded eras, laid out as a library
PART_MOST = 1_990_000_000         # bytes in one file: GitHub takes files under 2 GB
LIST_MOST = 20_000_000            # bytes: the list is a few hundred KB
TIMEOUT = 15                      # seconds for the list and for a file to start coming
LIST_KEPT = 600                   # seconds the list is kept before it's asked for again
KINDS = (".glb", ".png", ".jpg")  # what a section's files hold: models and pictures, nothing else
FILES = ("model", "picture", "card_picture")    # a unit's files in the library (card_picture: its card, 360 x 184)
_HEADERS = {"User-Agent": "RUSE-Mod-Platform"}
_LOCK = threading.Lock()


class EraDownloadError(Exception):
    """A problem with the era units list or a download, said for the modder."""


def library_dir(home: Path | None = None) -> Path | None:
    """Where the era units library is: RUSE_ERA_UNITS, else the eras downloaded into `home` (the platform folder),
    else era_units beside the program, else beside the source."""
    places = [os.environ.get(LIBRARY_ENV)] if os.environ.get(LIBRARY_ENV) else []
    places += [Path(home) / DOWNLOADED] if home else []
    places += [Path(sys.executable).resolve().parent / "era_units", Path(sys.argv[0]).resolve().parent / "era_units",
               Path(__file__).resolve().parents[2] / "era_units"]
    for p in places:
        if p and (Path(p) / INDEX).is_file():
            return Path(p)
    return None


def slug(era: str) -> str:
    return era.replace(" ", "_")


def folders(era: str) -> tuple[str, ...]:
    """An era's own folders in the library: its name, or as the library writes it (Cold_War)."""
    return (era, slug(era))


def safe_member(name) -> bool:
    """A path a section may hold: <era>/<nation>/<file> or pictures/<file>, a model or a picture, nothing outside."""
    if not isinstance(name, str):
        return False
    parts = name.split("/")
    return ((len(parts) == 3 and any(parts[0] in folders(e) for e in ERAS))
            or (len(parts) == 2 and parts[0] == "pictures")) and all(
        p and p not in (".", "..") and p == p.strip() and not any(c in p for c in ':\\*?"<>|') for p in parts) and (
        Path(name).suffix.lower() in KINDS)


def _is_sha(text) -> bool:
    return isinstance(text, str) and len(text) == 64 and all(c in "0123456789abcdef" for c in text)


def parse_list(data: bytes) -> list[dict]:
    """The sections of an era-units.json, each checked: one that isn't right is left out, so one mistake never hides
    the rest. A list of a newer format is refused (the Studio is too old for it). The list's "units_per_metre" (the
    game's units in a metre, for the units' real sizes) goes with each section, into the library it's put in."""
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise EraDownloadError(f"the era units list can't be read ({exc})") from None
    if not isinstance(doc, dict) or doc.get("format") != 1:
        raise EraDownloadError("the era units list is made for a newer Studio: update the Studio")
    scale = scale_of(doc)
    out = []
    for s in doc.get("sections") if isinstance(doc.get("sections"), list) else []:
        try:
            era, parts, units = s["era"], s["parts"], s["units"]
            ok = (era in ERAS and _is_sha(s["version"]) and isinstance(parts, list) and parts
                  and isinstance(units, list) and units and era not in {o["era"] for o in out})
            ok = ok and all(isinstance(p["file"], str) and p["file"].startswith("era-units-")
                            and p["file"].endswith(".zip") and p["file"] == Path(p["file"]).name
                            and isinstance(p["size"], int) and 0 < p["size"] <= PART_MOST and _is_sha(p["sha256"])
                            for p in parts)
            ok = ok and all(isinstance(u, dict) and u.get("era") == era and isinstance(u.get("key"), str)
                            and all(u.get(f) is None or safe_member(u[f]) for f in FILES)
                            for u in units)
        except (KeyError, TypeError):
            ok = False
        if ok:
            out.append(dict(s, **{SCALE: scale}) if scale else s)
    return out


def _open(url: str):
    """A file of the list's place: over HTTPS, or from a folder (RUSE_ERA_UNITS_URL set to one)."""
    if url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
        return urllib.request.urlopen(urllib.request.Request(url, headers=_HEADERS), timeout=TIMEOUT)
    return open(url, "rb")


def base_url() -> str:
    return os.environ.get(URL_ENV) or SECTIONS_URL


def fetch_list(base: str | None = None, opener=_open) -> list[dict]:
    """The release's sections; none while no list is out (the owner, 2026-10-08: the eras are there, "just saying
    there's no units yet": their models come in a later update)."""
    try:
        with opener((base or base_url()) + LIST) as r:
            data = r.read(LIST_MOST + 1)
    except (OSError, ValueError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
            if exc.code == 404:
                return []   # no list published yet: no units yet
        if isinstance(exc, FileNotFoundError):
            return []
        raise EraDownloadError(f"the era units list couldn't be loaded ({plain(exc, TIMEOUT)})") from None
    if len(data) > LIST_MOST:
        raise EraDownloadError("the era units list is far bigger than one ever is, so it wasn't read")
    return parse_list(data)


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def download_part(base: str, part: dict, into: Path, progress=lambda n: None, opener=_open) -> Path:
    """One of a section's files, into the folder `into`, checked against the size and SHA-256 the list gives.
    Anything else is deleted and refused. A file already there and right (a download stopped after it) is kept."""
    into.mkdir(parents=True, exist_ok=True)
    target = into / part["file"]
    if target.is_file() and target.stat().st_size == part["size"] and _sha_file(target) == part["sha256"]:
        progress(part["size"])
        return target
    tmp = target.with_name(target.name + ".part")
    digest, got = hashlib.sha256(), 0
    try:
        with opener(base + part["file"]) as r, tmp.open("wb") as f:
            while chunk := r.read(1 << 20):
                got += len(chunk)
                if got > part["size"]:
                    break  # bigger than promised: no point reading on
                digest.update(chunk)
                f.write(chunk)
                progress(len(chunk))
    except (OSError, ValueError) as exc:
        tmp.unlink(missing_ok=True)
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
        raise EraDownloadError(f"{part['file']} couldn't be downloaded ({plain(exc, TIMEOUT)})") from None
    if got != part["size"] or digest.hexdigest() != part["sha256"]:
        tmp.unlink(missing_ok=True)
        raise EraDownloadError(f"{part['file']} isn't the file the era units list promises (its size or checksum "
                               f"differs), so it wasn't used. Try again: the list may have changed while it came.")
    tmp.replace(target)
    return target


def read_section(root: Path, era: str) -> dict | None:
    """The section of `era` downloaded into `root`: {"era", "version", "units"}, or None."""
    try:
        got = json.loads((root / "sections" / f"{slug(era)}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return got if isinstance(got, dict) and got.get("era") == era else None


def write_index(root: Path, scale: dict | None = None) -> None:
    """The library's era_units.json: the units of every section downloaded, era by era, and the game's units in a
    metre (`scale`: the list's, as the section just put in brought it; else the index's own, kept)."""
    units = [u for era in ERAS for u in (read_section(root, era) or {}).get("units", [])]
    if not scale:
        try:
            scale = scale_of(json.loads((root / INDEX).read_text(encoding="utf-8")))
        except (OSError, ValueError):
            scale = None
    doc = {"version": 1, "note": "", **({SCALE: scale} if scale else {}), "units": units}
    (root / INDEX).write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")


def install_section(root: Path, section: dict, zips: list[Path]) -> None:
    """Put a section's checked files into the library at `root`: each .zip unpacked into a folder of its own first
    (only models and pictures in the era's own folders or pictures/: anything else stops it, nothing installed), every
    model and picture its units name there, then the era's old files out and the new ones in, and the index made
    again."""
    era = section["era"]
    stage = root / ".staging" / slug(era)
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    names = set()
    for z in zips:
        with zipfile.ZipFile(z) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                if not safe_member(info.filename) or info.filename.split("/")[0] not in (*folders(era), "pictures"):
                    shutil.rmtree(stage, ignore_errors=True)
                    raise EraDownloadError(f"{z.name} holds {info.filename!r}, which an era's file never does, so "
                                           f"nothing was installed.")
                out = stage / info.filename
                out.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, out.open("wb") as dst:
                    shutil.copyfileobj(src, dst, 1 << 20)
                names.add(info.filename)
    missing = sorted({u[f] for u in section["units"] for f in FILES if u.get(f)} - names)
    if missing:
        shutil.rmtree(stage, ignore_errors=True)
        raise EraDownloadError(f"the {era} files don't hold {len(missing)} of what the list names ({missing[0]}...), "
                               f"so nothing was installed.")
    others = {u.get("picture") for e in ERAS if e != era for u in (read_section(root, e) or {}).get("units", [])}
    for u in (read_section(root, era) or {}).get("units", []):
        if u.get("picture") and u["picture"] not in others and safe_member(u["picture"]):
            (root / u["picture"]).unlink(missing_ok=True)   # the era's old pictures (one another era shows stays)
    for folder in folders(era):
        shutil.rmtree(root / folder, ignore_errors=True)
    for name in sorted(names):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        os.replace(stage / name, root / name)
    shutil.rmtree(root / ".staging", ignore_errors=True)
    (root / "sections").mkdir(parents=True, exist_ok=True)
    (root / "sections" / f"{slug(era)}.json").write_text(
        json.dumps({"era": era, "version": section["version"], "units": section["units"]}, ensure_ascii=False),
        encoding="utf-8")
    write_index(root, scale_of(section))


def credits_text(units: list[dict]) -> str:
    """The mod's credits file for the era units it has (CC BY asks for the maker, the work, its licence and a note of
    changes)."""
    lines = ["# Era unit models", "",
             "These units use free 3D models by their makers, under the licence named. Changes: fitted to the game "
             "(turned, scaled) and the unit's nation's markings added (older markings covered).", ""]
    for u in sorted(units, key=lambda x: (x["era"], x["nation"], x["name"])):
        c = u["credit"]
        extra = f" {c['extra']}." if c.get("extra") else ""
        lines.append(f"- {u['name']} ({u['era']}, {u['nation']}): \"{c['title']}\" by {c['author']}, {c['licence']}, "
                     f"{c['url']}.{extra}")
    return "\n".join(lines) + "\n"


def kind_of(u: dict) -> str:
    return "air" if u.get("aircraft") else "ground"


def positive(x) -> float | None:
    """A number the library gives, when it's a finite one above 0; else None (not known)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0:
        return None
    return float(x)


def scale_of(doc) -> dict | None:
    """The game's units in a metre a library (or the release's list) gives at its top, {"ground", "air"}: the kinds
    given as numbers above 0; None when it gives neither."""
    given = doc.get(SCALE) if isinstance(doc, dict) else None
    out = {k: positive(given.get(k)) for k in REAL_OF} if isinstance(given, dict) else {}
    return {k: v for k, v in out.items() if v is not None} or None


def real_size(entry: dict, lib: dict) -> tuple[float | None, float | None]:
    """(an era unit's real width in metres, an aircraft's wingspan; the game's units in a metre for its kind), each
    None when the library doesn't give it."""
    kind = kind_of(entry)
    real = entry.get("real") if isinstance(entry.get("real"), dict) else {}
    return positive(real.get(REAL_OF[kind])), (scale_of(lib) or {}).get(kind)


def size_for(real_m: float, per_metre: float, model_length: float, model_width: float, like_length: float) -> float:
    """The import size that makes a model `real_m` metres wide in the game. Fitted at size s, its hull is
    like_length x s long (rusemod.modelin.prepare), so model_width / model_length x like_length x s wide; that's to be
    real_m x per_metre game units."""
    return real_m * per_metre * model_length / (model_width * like_length)


def first_number(value) -> float | None:
    """A price as a unit has it: a number, or a list's first (its first battle date's); None when it's neither."""
    if isinstance(value, list):
        value = next((v for v in value if v is not None), None)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


class EraUnitCalls:
    """Mixed into StudioApi: uses its _open, _mod_dir, _edits, _saving, _all_units, _names, _resolve, _menu_units,
    _game, _look_models, cache_dir, new_unit, set_upgrade, set_research, model_import, model_import_remove and
    delete_unit."""

    def _era_library(self) -> tuple[Path | None, dict]:
        folder = library_dir(self._home)
        if folder is None:
            return None, {"units": [], "note": ""}
        return folder, json.loads((folder / INDEX).read_text(encoding="utf-8"))

    def _era_list(self, fresh: bool = False) -> tuple[list[dict], str]:
        """The release's sections and why they couldn't be had ("" when they could), asked for once in LIST_KEPT
        seconds (a failure once a minute)."""
        now = time.monotonic()
        kept = getattr(self, "_era_kept", None)
        if fresh or kept is None or now - kept[0] > (LIST_KEPT if not kept[2] else 60):
            try:
                kept = (now, fetch_list(), "")
            except EraDownloadError as exc:
                kept = (now, [], str(exc))
            self._era_kept = kept
        return kept[1], kept[2]

    def era_sections(self, downloaded_only: bool = False) -> dict:
        """Each era's download: {"sections": [{era, units (how many), size (bytes to download), state: "new" (not on
        this PC), "update" (a newer one is out: the screen starts it by itself) or "current"}], "message": "" or why
        the list couldn't be had}. With `downloaded_only` and no era downloaded yet, the list isn't asked for."""
        root = self._home / DOWNLOADED
        if downloaded_only and not any(read_section(root, era) for era in ERAS):
            return {"sections": [], "message": ""}
        sections, why = self._era_list()
        out = []
        for s in sections:
            have = read_section(root, s["era"])
            state = "new" if have is None else "current" if have.get("version") == s["version"] else "update"
            out.append({"era": s["era"], "units": len(s["units"]), "size": sum(p["size"] for p in s["parts"]),
                        "state": state})
        return {"sections": out, "message": why}

    def era_download(self, era: str) -> dict:
        """Download one era's units into the library (its files from the list, each checked, then unpacked): a job the
        screen follows. Its lines are "<bytes so far>/<bytes in all>" and then "unpack". An era already coming isn't
        started twice."""
        from .api import StudioError
        sections, why = self._era_list()
        section = next((s for s in sections if s["era"] == era), None)
        if section is None:
            # not a game rule: the list doesn't offer this era (yet)
            raise StudioError(f"No {era} units are out yet." if not why
                              else f"The era units list couldn't be had: {why}")
        with _LOCK:
            jobs = self.__dict__.setdefault("_era_jobs", {})
            running = jobs.get(era)
            if running and running in self._jobs and self._jobs[running].state == "running":
                return {"job": running}
            job = Job()
            self._jobs[job.id] = job
            jobs[era] = job.id
        root, base = self._home / DOWNLOADED, base_url()
        total = sum(p["size"] for p in section["parts"])

        def work(say):
            into = root / ".download"
            into.mkdir(parents=True, exist_ok=True)
            free = shutil.disk_usage(into).free
            if free < 2 * total + 200_000_000:
                # not a game rule: the PC's disk is too full for the download and its unpacking
                raise EraDownloadError(f"There isn't room on the disk for the {era} units: about "
                                       f"{(2 * total + 200_000_000) / 1e9:.1f} GB needed, {free / 1e9:.1f} GB free.")
            done, shown = 0, -1

            def tick(n):
                nonlocal done, shown
                done += n
                if done * 100 // total != shown:
                    shown = done * 100 // total
                    say(f"{done}/{total}")

            zips = [download_part(base, p, into, tick) for p in section["parts"]]
            say("unpack")
            install_section(root, section, zips)
            for z in zips:
                z.unlink(missing_ok=True)

        return job.start(work, f"The {era} units are ready.", plain=(OSError, EraDownloadError, zipfile.BadZipFile))

    def _era_record(self) -> dict:
        """{era unit key: its unit's address} for the current mod, keeping only units the mod still has."""
        mod = self._mod_dir()
        if mod is None or not (mod / INDEX).is_file():
            return {}
        try:
            record = json.loads((mod / INDEX).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        edits = self._edits()
        have = set(edits.new_units) if edits is not None else set()
        return {k: a for k, a in record.items() if a in have}

    def _era_save(self, record: dict, lib: dict) -> None:
        mod = self._mod_dir()
        (mod / INDEX).write_text(json.dumps(record, indent=1, ensure_ascii=False), encoding="utf-8")
        mine = [u for u in lib["units"] if u["key"] in record]
        credits = mod / CREDITS
        if mine:
            credits.write_text(credits_text(mine), encoding="utf-8")
        else:
            credits.unlink(missing_ok=True)

    def era_units_list(self, era: str, kind: str = "all", nation: int = -1, search: str = "",
                       group: str = "all") -> dict:
        """One era's units for the Units list: {"library": found or not, "units": [{key, name, nation, code (the
        nation chip), card, kind, added}], "types": the card types there, sorted}, filtered as the Units list is:
        by kind (ground or air), nation chip, words in the name and card type ("type:<card>")."""
        folder, lib = self._era_library()
        record = self._era_record() if self._mod_dir() is not None else {}
        words = (search or "").casefold().split()
        rows = [u for u in lib["units"] if u["era"] == era]
        rows = [u for u in rows if kind in ("all", kind_of(u)) and nation in (-1, NATION_CODE.get(u["nation"], -1))]
        types = sorted({u["card"] for u in rows})
        if group.startswith("type:"):
            rows = [u for u in rows if u["card"] == group[5:]]
        rows = [u for u in rows if all(w in u["name"].casefold() for w in words)]
        return {"library": folder is not None, "types": types,
                "installed": any(u["era"] == era for u in lib["units"]),
                "units": [{"key": u["key"], "name": u["name"], "nation": u["nation"],
                           "code": NATION_CODE.get(u["nation"], -1), "card": u["card"], "kind": kind_of(u),
                           "added": record.get(u["key"])} for u in rows]}

    def _era_price(self, source: str) -> float:
        from .api import _props
        ix = self._open()
        try:
            prices = _props(ix.show(source)).get("ProductionPrice")
        finally:
            ix.close()
        nums = [n for n in (prices or {}).get("numbers", []) if n is not None]
        return float(nums[0]) if nums else 0.0

    def era_start_price(self, source: str) -> dict:
        """A game unit's price (its first battle date's), for the era unit's price box when the start unit changes."""
        return {"price": self._era_price(source)}

    def _era_entry(self, key: str) -> tuple[Path, dict, dict]:
        """(the library's folder, the library, the era unit `key`'s entry); StudioError when it isn't there."""
        from .api import StudioError
        folder, lib = self._era_library()
        entry = next((u for u in lib["units"] if u["key"] == key), None)
        if folder is None or entry is None:
            raise StudioError(f"{key}: not in the era units library")
        return folder, lib, entry

    def _era_model_size(self, path: Path, aircraft: bool) -> tuple[float, float] | None:
        """A library model's hull (length, width) as the importer measures it (rusemod.modelin.hull_extent, the way it
        faces pinned as era_unit_add pins it), kept while the file is the same; None when it can't be read."""
        from rusemod.modelin import hull_extent, read_model
        try:
            st = path.stat()
        except OSError:
            return None
        key = (str(path), st.st_size, st.st_mtime_ns, bool(aircraft))
        kept = self.__dict__.setdefault("_era_measured", {})
        if key not in kept:
            try:
                kept[key] = hull_extent(read_model(path), {"facing": list(FACING), "aircraft": bool(aircraft)})
            except (ValueError, OSError, KeyError, IndexError, TypeError, struct.error):
                kept[key] = None      # (rusemod.modelin's ModelError is a ValueError)
        return kept[key]

    def _era_like(self, source: str) -> dict | None:
        """The start unit's model as the importer fits to it (rusemod.unitmodel.find_source's "like": its hull's
        "length" and "width" in game units...), kept while ZZ_Win.dat is the same (in the cache folder too, eras/
        likes.json: working it out reads the game's model packs, a few seconds); None when it has no model the importer
        can fit to, or the game's files aren't found."""
        from rusemod.build import find_pack
        from rusemod.edat import Edat
        from rusemod.unitmodel import UnitModelError, find_source
        game = self._game()
        zz_path = find_pack(game, "ZZ_Win.dat") if game is not None else None
        if zz_path is None:
            return None
        st = zz_path.stat()
        key = f"{zz_path}|{st.st_size}|{st.st_mtime_ns}|{source}"
        kept = self.__dict__.setdefault("_era_likes", {})
        if key in kept:
            return kept[key]
        saved = self.cache_dir / "eras" / "likes.json"
        try:
            on_disk = json.loads(saved.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            on_disk = {}
        on_disk = on_disk if isinstance(on_disk, dict) else {}
        if key in on_disk and (on_disk[key] is None or isinstance(on_disk[key], dict)):
            kept[key] = on_disk[key]
            return kept[key]
        like = None
        try:
            found = [m for m in self._look_models(source)[0] if "_dest" not in m.lower()]  # as model_import
            if found:
                zz = Edat.open(str(zz_path))
                try:
                    for model in found:   # as model_import: the first it can fit to (a jeep's driver can come first)
                        try:
                            src = find_source(zz, model)
                        except UnitModelError:
                            continue
                        like = {k: src.like[k] for k in ("length", "width")}
                        break
                finally:
                    zz.close()
        except (ValueError, OSError, KeyError, IndexError, TypeError, struct.error):
            like = None               # (UnitModelError is a ValueError)
        kept[key] = like
        try:
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_text(json.dumps({k: v for k, v in on_disk.items() if k.startswith(f"{zz_path}|{st.st_size}|"
                                                                                       f"{st.st_mtime_ns}|")}
                                        | {key: like}), encoding="utf-8")
        except OSError:
            pass                      # kept for this run only
        return like

    def _era_size(self, folder: Path, lib: dict, entry: dict, source: str | None) -> dict:
        """The import size suggested for an era unit started from `source`: {"size": its real width's (an aircraft:
        its wingspan's) when that can be worked out, else 1 (as long as the start unit, as before); "real": whether it
        is; "clamped": the size its real width needs when that's outside model_import's sizes (the size is then the
        nearest end), else None; "real_m": its real width (span) in metres or None; "what": "width" or "span"; "why":
        "" or why it's 1: "no_model", "no_real" (the library gives no real size), "no_scale" (nor the game's units in
        a metre), "model_unread" (its model couldn't be measured), "start_unread" (nor the start unit's)}."""
        from .api import MODEL_SIZES
        real_m, per_metre = real_size(entry, lib)
        info = {"size": 1.0, "real": False, "clamped": None, "real_m": real_m,
                "what": "span" if kind_of(entry) == "air" else "width", "why": ""}
        model = folder / entry["model"] if entry.get("model") else None
        if model is None or not model.is_file():
            return dict(info, why="no_model")
        if real_m is None:
            return dict(info, why="no_real")
        if per_metre is None:
            return dict(info, why="no_scale")
        measured = self._era_model_size(model, bool(entry.get("aircraft")))
        if measured is None or positive(measured[0]) is None or positive(measured[1]) is None:
            return dict(info, why="model_unread")
        length = positive((self._era_like(source) or {}).get("length")) if source else None
        if length is None:
            return dict(info, why="start_unread")
        s = size_for(real_m, per_metre, measured[0], measured[1], length)
        lo, hi = MODEL_SIZES
        return dict(info, size=min(hi, max(lo, s)), real=True, clamped=None if lo <= s <= hi else s)

    def _era_research(self, entry: dict, source: str | None, nation, factory, lang: str) -> dict:
        """The units the era unit may be researched from in build menu (`nation`, `factory`): upgrade()'s choices for a
        new unit there (the same nation's units in that menu, the mod's new ones too, so era units chain), each
        {address, name} by its game name, and the one suggested: the start unit when it's there ("why": "start"),
        else the unit the era unit stands in for ("in_place_of", by its English name), else for Cold War and Modern
        units the dearest there (its price at the first battle date: "dearest"), else none. "offered": False when
        units of its kind have no research in the game's files (no UpgradeRequire), and nothing is offered."""
        from rusemod import schema
        from .api import UPGRADE, _props, _tail
        from .edits import REMOVED, EditsFileError
        empty = {"offered": False, "choices": [], "suggested": None, "why": ""}
        try:
            menu = (int(nation), int(factory))
        except (TypeError, ValueError):
            return empty
        try:
            edits = self._edits()
        except EditsFileError:
            edits = None
        new_units = edits.new_units if edits else {}
        told = lang if lang in schema.LANGS else "us"     # game names, never code names
        ix = self._open()
        try:
            if UPGRADE not in ix.prop_types(CLASS_OF[kind_of(entry)]):
                return empty
            units = {u["address"]: u for u in self._all_units(ix)}
            choices = self._menu_units(edits, units, menu)
            names = self._names(ix, choices, told, new_units)
            english = names if told == "us" else self._names(ix, choices, "us", new_units)
            def shown_at(a, props):     # the battle dates the build menu shows unit `a` at (None: not said)
                shows = edits.get(a, "ShowInMenu") if edits else None
                shows = (props.get("ShowInMenu") or {}).get("numbers") if shows is None else shows
                return [bool(x) for x in shows] if isinstance(shows, list) and shows else None
            # the new unit is shown at its start unit's dates; a parent missing from the menu at one of them isn't
            # suggested (2026-10-09: the dearest were the game's atomic units, shown at the last date only, and
            # DEMO, film and empty units, never shown): there it could never be researched. It stays a choice.
            mine_at = shown_at(source, _props(ix.show(self._resolve(edits, source)[0]))) if source else None
            prices, never_shown = {}, set()
            for a in choices:
                props = _props(ix.show(self._resolve(edits, a)[0]))
                mine = edits.get(a, "ProductionPrice") if edits else None
                if mine is None:
                    prices[a] = first_number((props.get("ProductionPrice") or {}).get("numbers"))
                else:
                    prices[a] = None if mine is REMOVED else first_number(mine)
                at = shown_at(a, props)
                if at is not None and (not any(at) or (mine_at is not None and any(
                        need and not (at[i] if i < len(at) else False) for i, need in enumerate(mine_at)))):
                    never_shown.add(a)
        finally:
            ix.close()
        shown = list(names.values())
        twice = {n for n in shown if shown.count(n) > 1}  # two called the same: told apart as the Upgrade box does

        def named(a):
            n = names.get(a, _tail(a))
            return {"address": a, "name": f"{n} ({_tail(a)})" if n in twice and n != _tail(a) else n}
        listed = sorted((named(a) for a in choices), key=lambda c: c["name"].lower())
        suggested, why = None, ""
        stands_for = str(entry.get("in_place_of") or "").strip().casefold()
        if source in choices:
            suggested, why = source, "start"
        elif stands_for:
            hit = next((c["address"] for c in listed if english.get(c["address"], "").strip().casefold() == stands_for),
                       None)
            suggested, why = (hit, "in_place_of") if hit else (None, "")
        if suggested is None and entry.get("era") in RESEARCH_ERAS:
            priced = [(prices[c["address"]], c["address"]) for c in listed
                      if prices.get(c["address"]) is not None and c["address"] not in never_shown]
            if priced:
                top = max(p for p, _a in priced)
                suggested, why = next(a for p, a in priced if p == top), "dearest"
        return {"offered": True, "choices": listed, "suggested": suggested, "why": why}

    def _era_options(self, folder: Path, lib: dict, entry: dict, source: str | None, nation, factory,
                     lang: str) -> dict:
        size = self._era_size(folder, lib, entry, source)
        return {"price": self._era_price(source) if source else 0.0, "size": size.pop("size"), "size_info": size,
                "research": self._era_research(entry, source, nation, factory, lang)}

    def era_unit_start(self, key: str, source: str, nation: int, factory: int, lang: str = "base") -> dict:
        """What the add form shows for start unit `source` and build menu (`nation`, `factory`), asked again when one
        of them changes: {"price": the start unit's, "size": the import size suggested (its real size, else 1),
        "size_info": how it was had (_era_size), "research": the units it may be researched from there and the one
        suggested (_era_research)}."""
        from .api import StudioError
        folder, lib, entry = self._era_entry(key)
        ix = self._open()
        try:
            ix.show(source)
        except KeyError:
            # not a game rule: the game or one of its files isn't found
            raise StudioError(f"{source} isn't in this game build") from None
        finally:
            ix.close()
        return self._era_options(folder, lib, entry, source, nation, factory, lang)

    def era_unit_page(self, key: str, lang: str = "base") -> dict:
        """One era unit for its page: its library entry, "added" (its unit's address in this mod, or None), "has_model",
        "picture" (a cache URL of its model's picture, or None), "start": the game units it can start from (its kind's
        units with a build menu: the suggested one first, then its card type's, then the rest by name), each {address,
        name (its game name), nation, suggested, same_type}, and for the suggested start unit in the library's build
        menu (era_unit_start): "price", "size", "size_info" and "research"."""
        from rusemod import schema
        folder, lib, entry = self._era_entry(key)
        record = self._era_record() if self._mod_dir() is not None else {}
        picture = None
        if entry.get("picture") and (folder / entry["picture"]).is_file():
            copy = self.cache_dir / "eras" / Path(entry["picture"]).name
            if not copy.is_file():
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(folder / entry["picture"], copy)
            picture = f"cache/eras/{copy.name}"
        ix = self._open()
        try:
            cls = CLASS_OF[kind_of(entry)]
            units = [u for u in self._all_units(ix) if u["class"] == cls and u["factory"] is not None]
            # game names (English in the code names' mode), never code names
            names = self._names(ix, [u["address"] for u in units], lang if lang in schema.LANGS else "us")
            types = ix.names([u["type_key"] for u in units if u["type_key"]], "us")
        finally:
            ix.close()
        start = []
        for u in units:
            same = types.get(u["type_key"]) == entry["card"]
            start.append({"address": u["address"], "name": names.get(u["address"], u["address"].rsplit("/", 1)[-1]),
                          "nation": u["nation"], "suggested": u["address"] == entry.get("copies"), "same_type": same})
        start.sort(key=lambda s: (not s["suggested"], not s["same_type"], s["name"].casefold()))
        options = self._era_options(folder, lib, entry, entry.get("copies"), entry.get("game_nation"),
                                    entry.get("factory"), lang)
        return dict(entry, added=record.get(key), picture=picture, start=start,
                    has_model=bool(entry.get("model") and (folder / entry["model"]).is_file()), **options)

    def era_unit_add(self, key: str, nation: int, factory: int, source: str | None = None, name: str | None = None,
                     price=None, size=None, research_from=SUGGESTED, research_price=None, research_time=None) -> dict:
        """Add an era unit to the current mod: a new unit starting from `source`'s values (default: the library's
        suggestion), called `name` (default: the era unit's), costing `price` (default: the source's), in nation
        `nation`'s build menu `factory`, with its model at `size` (times the start unit's length; default: the size
        suggested, its real size when known: _era_size), its card and its credit; researched from `research_from` (one
        of the menu's units era_unit_start offers; None: buyable from the start; default: the one suggested) for
        `research_price` and `research_time` (default: the Studio's 50 and 50 s), as the Upgrade box links it. Returns
        {"address", "name", "model": the model's report or None, "model_note": "" or why it shows the start unit's
        model, "card": whether it got its own card, "size": the size its model was fitted at (None: no model),
        "research_from": the unit it's researched from or None}."""
        from .api import MODEL_SIZES, RESEARCH, StudioError
        folder, lib, entry = self._era_entry(key)
        if self._mod_dir() is None or self._edits() is None:
            raise StudioError("Pick or make a mod first: an era unit is added to a mod.")
        source = source or entry.get("copies")
        if not source:
            raise StudioError(f"{entry['name']}: pick a unit to start from")
        record = self._era_record()
        if key in record:
            raise StudioError(f"{entry['name']} is already in this mod")
        # everything asked for is checked before the unit is made, so a refusal leaves nothing half made
        has_model = bool(entry.get("model") and (folder / entry["model"]).is_file())
        if size is None or size == "":
            size = self._era_size(folder, lib, entry, source)["size"] if has_model else 1.0
        if isinstance(size, bool) or not isinstance(size, (int, float)) or not MODEL_SIZES[0] <= size <= MODEL_SIZES[1]:
            # not a game rule: the sizes the model importer takes (model_import)
            raise StudioError("Give a size from 0.2 to 5 (1 is as long as the unit it starts from).")
        research = self._era_research(entry, source, nation, factory, "us")
        if research_from == SUGGESTED:
            research_from = research["suggested"]
        if research_from is not None and research_from not in {c["address"] for c in research["choices"]}:
            # not a game rule: what the Upgrade box offers (the same nation's units in the same build menu)
            raise StudioError(f"{entry['name']} can't be researched from {research_from} in that build menu")
        costs = {}
        for prop, value in (("UpgradePrice", research_price), ("UpgradeTime", research_time)):
            value = RESEARCH[prop] if value is None or value == "" else value
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                # not a game rule: a research price or time is a number, nothing below 0
                raise StudioError(f"{prop}: a number from 0 up")
            costs[prop] = value
        cost = self._era_price(source) if price is None or price == "" else price
        wanted = (name or "").strip() or entry["name"]
        try:
            made = self.new_unit(source, wanted, cost, int(nation), int(factory))
        except StudioError as exc:
            if name or "already a unit" not in str(exc):
                raise
            wanted = f"{entry['name']} ({entry['era']})"   # the same name in two eras (a Leopard 1 in both, say)
            made = self.new_unit(source, wanted, cost, int(nation), int(factory))
        record[key] = made["address"]
        with self._saving:
            self._era_save(record, lib)
        if research["offered"]:
            # linked as the Upgrade box links it (set_upgrade: the link, the upgrade flag, a research price and time);
            # None also takes away a link the start unit had, so it's buyable from the start
            self.set_upgrade(made["address"], research_from)
            if research_from is not None:
                for prop, value in costs.items():
                    self.set_research(made["address"], prop, value)
        model, note = None, ""
        if has_model:
            try:
                # the library's model is already in the game's axes, its front +x (and pinned by hand where the
                # importer's rules couldn't tell): kept so, not worked out again
                model = self.model_import(made["address"], str(folder / entry["model"]), float(size),
                                          bool(entry.get("aircraft")), facing=list(FACING))["model"]
            except StudioError as exc:
                note = "no_fit" if not entry.get("fits") else str(exc)
        else:
            note = "no_model"
        card = self._era_card(made["address"], folder, entry)
        return {"address": made["address"], "name": made["name"], "model": model, "model_note": note, "card": card,
                "size": float(size) if has_model else None,
                "research_from": research_from if research["offered"] else None}

    def _era_card(self, address: str, folder: Path, entry: dict) -> bool:
        """Give the new unit its era card (the library's "card_picture": its fitted model drawn at the game's card
        size; "card" is its kind of card, Tank or Fighter): the build menu and the selection show it instead of the
        card of the unit it started from (2026-10-08 test: an F-4 showed the Bf 109's). False when the library has
        none, or it isn't the card's size."""
        from rusemod.png import read_png
        name = entry.get("card_picture")
        target = self._own_card_file(address)
        if not safe_member(name) or target is None or not (folder / name).is_file():
            return False
        data = (folder / name).read_bytes()
        try:
            w, h, _px = read_png(data)
        except ValueError:
            return False
        card = self._card_view(address)
        if card is not None and (w, h) != (card["width"], card["height"]):
            return False
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return True

    def era_unit_remove(self, key: str, researched=None) -> dict:
        """Take an era unit out of the mod: its unit, every change made to it, its model, its card and its credit. The
        units researched from it are dealt with first, as the modder chose (delete_unit; `researched` "anyway" after
        the warning). Returns {"removed": its address, "relinked", "left"}, or {"removed": None, "ask": the units
        researched from it} when the modder is to be warned first (nothing changed)."""
        from .api import StudioError
        _folder, lib = self._era_library()
        record = self._era_record()
        address = record.get(key)
        if address is None:
            raise StudioError(f"{key}: not in this mod")
        research = self._research_gone(address, researched)   # before anything goes: a refusal leaves it whole
        if "ask" in research:
            return {"removed": None, "ask": research["ask"]}
        record.pop(key)
        try:
            self.model_import_remove(address)
        except StudioError:
            pass
        mine = self._own_card_file(address)       # its era card goes with it
        if mine is not None:
            mine.unlink(missing_ok=True)
        self.delete_unit(address, "anyway")       # the units researched from it are dealt with above
        with self._saving:
            self._era_save(record, lib)
        return {"removed": address, **research}
