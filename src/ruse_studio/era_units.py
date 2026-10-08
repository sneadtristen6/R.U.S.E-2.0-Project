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

The library: a folder holding era_units.json, the fitted models and their pictures (RUSE_ERA_UNITS, else the eras the
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
import os
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


SECTIONS_URL = "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/download/era-units/"
URL_ENV = "RUSE_ERA_UNITS_URL"    # another place for the list and its files, ending in "/" (a test's, a local copy)
LIST = "era-units.json"           # the release's list of sections
DOWNLOADED = "era_units"          # in the platform folder: the downloaded eras, laid out as a library
PART_MOST = 1_990_000_000         # bytes in one file: GitHub takes files under 2 GB
LIST_MOST = 20_000_000            # bytes: the list is a few hundred KB
TIMEOUT = 15                      # seconds for the list and for a file to start coming
LIST_KEPT = 600                   # seconds the list is kept before it's asked for again
KINDS = (".glb", ".png", ".jpg")  # what a section's files hold: models and pictures, nothing else
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


def safe_member(name) -> bool:
    """A path a section may hold: <era>/<nation>/<file> or pictures/<file>, a model or a picture, nothing outside."""
    if not isinstance(name, str):
        return False
    parts = name.split("/")
    return ((len(parts) == 3 and parts[0] in ERAS) or (len(parts) == 2 and parts[0] == "pictures")) and all(
        p and p not in (".", "..") and p == p.strip() and not any(c in p for c in ':\\*?"<>|') for p in parts) and (
        Path(name).suffix.lower() in KINDS)


def _is_sha(text) -> bool:
    return isinstance(text, str) and len(text) == 64 and all(c in "0123456789abcdef" for c in text)


def parse_list(data: bytes) -> list[dict]:
    """The sections of an era-units.json, each checked: one that isn't right is left out, so one mistake never hides
    the rest. A list of a newer format is refused (the Studio is too old for it)."""
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise EraDownloadError(f"the era units list can't be read ({exc})") from None
    if not isinstance(doc, dict) or doc.get("format") != 1:
        raise EraDownloadError("the era units list is made for a newer Studio: update the Studio")
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
                            and all(u.get(f) is None or safe_member(u[f]) for f in ("model", "picture"))
                            for u in units)
        except (KeyError, TypeError):
            ok = False
        if ok:
            out.append(s)
    return out


def _open(url: str):
    """A file of the list's place: over HTTPS, or from a folder (RUSE_ERA_UNITS_URL set to one)."""
    if url.startswith(("https://", "http://127.0.0.1", "http://localhost")):
        return urllib.request.urlopen(urllib.request.Request(url, headers=_HEADERS), timeout=TIMEOUT)
    return open(url, "rb")


def base_url() -> str:
    return os.environ.get(URL_ENV) or SECTIONS_URL


def fetch_list(base: str | None = None, opener=_open) -> list[dict]:
    try:
        with opener((base or base_url()) + LIST) as r:
            data = r.read(LIST_MOST + 1)
    except (OSError, ValueError) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
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


def write_index(root: Path) -> None:
    """The library's era_units.json: the units of every section downloaded, era by era."""
    units = [u for era in ERAS for u in (read_section(root, era) or {}).get("units", [])]
    (root / INDEX).write_text(json.dumps({"version": 1, "note": "", "units": units}, indent=1, ensure_ascii=False),
                              encoding="utf-8")


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
                if not safe_member(info.filename) or info.filename.split("/")[0] not in (era, "pictures"):
                    shutil.rmtree(stage, ignore_errors=True)
                    raise EraDownloadError(f"{z.name} holds {info.filename!r}, which an era's file never does, so "
                                           f"nothing was installed.")
                out = stage / info.filename
                out.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, out.open("wb") as dst:
                    shutil.copyfileobj(src, dst, 1 << 20)
                names.add(info.filename)
    missing = sorted({u[f] for u in section["units"] for f in ("model", "picture") if u.get(f)} - names)
    if missing:
        shutil.rmtree(stage, ignore_errors=True)
        raise EraDownloadError(f"the {era} files don't hold {len(missing)} of what the list names ({missing[0]}...), "
                               f"so nothing was installed.")
    others = {u.get("picture") for e in ERAS if e != era for u in (read_section(root, e) or {}).get("units", [])}
    for u in (read_section(root, era) or {}).get("units", []):
        if u.get("picture") and u["picture"] not in others and safe_member(u["picture"]):
            (root / u["picture"]).unlink(missing_ok=True)   # the era's old pictures (one another era shows stays)
    shutil.rmtree(root / era, ignore_errors=True)
    for name in sorted(names):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        os.replace(stage / name, root / name)
    shutil.rmtree(root / ".staging", ignore_errors=True)
    (root / "sections").mkdir(parents=True, exist_ok=True)
    (root / "sections" / f"{slug(era)}.json").write_text(
        json.dumps({"era": era, "version": section["version"], "units": section["units"]}, ensure_ascii=False),
        encoding="utf-8")
    write_index(root)


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


class EraUnitCalls:
    """Mixed into StudioApi: uses its _open, _mod_dir, _edits, _saving, _all_units, _names, cache_dir, new_unit,
    model_import, model_import_remove and delete_unit."""

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
            raise StudioError(f"No {era} units are out yet." if not why else f"The era units list couldn't be had: {why}")
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

    def era_unit_page(self, key: str, lang: str = "base") -> dict:
        """One era unit for its page: its library entry, "added" (its unit's address in this mod, or None), "has_model",
        "picture" (a cache URL of its model's picture, or None), "price" (the suggested start unit's), and "start":
        the game units it can start from (its kind's units with a build menu: the suggested one first, then its card
        type's, then the rest by name), each {address, name, nation, suggested, same_type}."""
        from .api import StudioError
        folder, lib = self._era_library()
        entry = next((u for u in lib["units"] if u["key"] == key), None)
        if folder is None or entry is None:
            raise StudioError(f"{key}: not in the era units library")
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
            names = self._names(ix, [u["address"] for u in units], lang)
            types = ix.names([u["type_key"] for u in units if u["type_key"]], "us")
        finally:
            ix.close()
        start = []
        for u in units:
            same = types.get(u["type_key"]) == entry["card"]
            start.append({"address": u["address"], "name": names.get(u["address"], u["address"].rsplit("/", 1)[-1]),
                          "nation": u["nation"], "suggested": u["address"] == entry.get("copies"), "same_type": same})
        start.sort(key=lambda s: (not s["suggested"], not s["same_type"], s["name"].casefold()))
        price = self._era_price(entry["copies"]) if entry.get("copies") else 0.0
        return dict(entry, added=record.get(key), price=price, picture=picture, start=start,
                    has_model=bool(entry.get("model") and (folder / entry["model"]).is_file()))

    def era_unit_add(self, key: str, nation: int, factory: int, source: str | None = None, name: str | None = None,
                     price=None) -> dict:
        """Add an era unit to the current mod: a new unit starting from `source`'s values (default: the library's
        suggestion), called `name` (default: the era unit's), costing `price` (default: the source's), in nation
        `nation`'s build menu `factory`, with its model and its credit. Returns {"address", "name", "model": the
        model's report or None, "model_note": "" or why it shows the start unit's model}."""
        from .api import StudioError
        folder, lib = self._era_library()
        entry = next((u for u in lib["units"] if u["key"] == key), None)
        if folder is None or entry is None:
            raise StudioError(f"{key}: not in the era units library")
        if self._mod_dir() is None or self._edits() is None:
            raise StudioError("Pick or make a mod first: an era unit is added to a mod.")
        source = source or entry.get("copies")
        if not source:
            raise StudioError(f"{entry['name']}: pick a unit to start from")
        record = self._era_record()
        if key in record:
            raise StudioError(f"{entry['name']} is already in this mod")
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
        model, note = None, ""
        if entry.get("model") and (folder / entry["model"]).is_file():
            try:
                model = self.model_import(made["address"], str(folder / entry["model"]), 1.0,
                                          bool(entry.get("aircraft")))["model"]
            except StudioError as exc:
                note = "no_fit" if not entry.get("fits") else str(exc)
        else:
            note = "no_model"
        return {"address": made["address"], "name": made["name"], "model": model, "model_note": note}

    def era_unit_remove(self, key: str) -> dict:
        """Take an era unit out of the mod: its unit, every change made to it, its model and its credit."""
        from .api import StudioError
        _folder, lib = self._era_library()
        record = self._era_record()
        address = record.pop(key, None)
        if address is None:
            raise StudioError(f"{key}: not in this mod")
        try:
            self.model_import_remove(address)
        except StudioError:
            pass
        self.delete_unit(address)
        with self._saving:
            self._era_save(record, lib)
        return {"removed": address}
