"""Map Paint's online textures (the Texture panel's Online (free) source; GroundTextureCalls.online_textures and
online_texture): free ground pictures from three places, each downloaded only when the modder clicks it, one picture
at a time, then kept in the mod like a picture of the modder's own (files/ground/<name>.png, its real size and credit
in the sidecar beside it: rusemod.groundtex.read_credit). The owner, 2026-10-09: "Make it more efficient to add ...
the more, the merrier".

- Poly Haven (CC0): its textures' list (api.polyhaven.com/assets), the "aerial" ones first (photos from above, 8 to
  90 m across: the size an RTS map is seen at), then "terrain"; a texture's colour picture (its "Diffuse" map, 1k JPG,
  from dl.polyhaven.org). Their sizes are given in millimetres.
- ambientCG (CC0): its materials found by words (ambientcg.com/api/v2/full_json), a material's 1K-JPG zip, of which
  only its *_Color.jpg is read (in memory: nothing of the zip is written). Their sizes are given in centimetres (0: not
  known).
- US aerial photos (public domain: the USGS National Map's NAIP imagery, flown for the USDA, about 0.6 m a pixel): a
  square of ground N metres across at a latitude and longitude in the 48 states, from the imagery service's
  exportImage. A built-in list of places (PLACES) or one typed in.

The lists are kept in the Studio's cache for a day (KEPT), so they open fast. Nothing goes over the network when this
module is imported. Not tried yet: a real download from any of the three (each is the modder's own click)."""
from __future__ import annotations

import base64
import http.client
import io
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from rusemod import groundtex as gt
from rusemod.mod_index import plain

SOURCES = ("polyhaven", "ambientcg", "usgs")
TIMEOUT = 20               # seconds for an answer to start coming
KEPT = 24 * 3600           # seconds a list is kept before it's asked for again
LIST_FORMAT = 1            # the kept lists' own format: a new one asks again
LIST_MOST = 16_000_000     # bytes: a list is well under a few MB
PICTURE_MOST = 24_000_000  # bytes in one picture (a 1k JPG is under 1 MB)
ZIP_MOST = 80_000_000      # bytes in an ambientCG 1K-JPG zip (its other maps come with it: about 10 MB)
HEADERS = {"User-Agent": "RUSE-Mod-Platform (RUSE Studio Map Paint)"}

POLYHAVEN_LIST = "https://api.polyhaven.com/assets?t=textures&c={category}"
POLYHAVEN_FILES = "https://api.polyhaven.com/files/{id}"
POLYHAVEN_CATEGORIES = ("aerial", "terrain")  # in this order: the aerial ones are at an RTS map's scale
POLYHAVEN_PAGE = "https://polyhaven.com/a/{id}"
POLYHAVEN_HOSTS = ("dl.polyhaven.org",)       # where its pictures are served from
POLYHAVEN_COLOUR = ("diffuse", "color", "col", "albedo")  # its colour map's name, the first found

AMBIENTCG_LIST = ("https://ambientcg.com/api/v2/full_json?type=Material&q={q}&limit={limit}&sort=Popular"
                  "&include=downloadData,previewData")
AMBIENTCG_ZIP = "https://ambientcg.com/get?file={id}_1K-JPG.zip"
AMBIENTCG_PAGE = "https://ambientcg.com/a/{id}"
AMBIENTCG_LIMIT = 100      # materials found at a time
AMBIENTCG_WORDS = "ground"  # what's found while nothing is typed
AMBIENTCG_THUMBS = ("128-JPG-242424", "128-PNG", "64-PNG", "256-JPG-242424")  # its small pictures, the first there

NAIP = "https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer"
NAIP_METRES = (160, 320, 640, 1280)  # a photo's side to choose from (metres)
NAIP_DEFAULT = 320                   # a map square, as the From a map source takes (groundtex.MAP_SIDE)
NAIP_PIXEL = 0.6                     # metres a pixel the imagery is flown at
NAIP_MOST = 1024                     # pixels across a photo at most
NAIP_LEAST = 64
# the imagery covers the 48 states (its extent, read from the service's own page 2026-10-09)
US_LAT = (24.4, 49.5)
US_LON = (-125.0, -66.9)
EARTH = 6378137.0                    # metres: Web Mercator's sphere (the service's own spatial reference, 3857)

_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


class OnlineError(gt.TextureError):
    """A list or a picture that couldn't be had, said for the modder."""


# The places the US aerial photos offer by name: (key, English name, latitude, longitude, kind). Picked by eye from
# memory of US landscapes, NOT checked against the photos: one may land a little off what its name says. The imagery
# is flown in the growing season, so snow is only where it stays all summer. Each key's words: tex_place_<key>.
PLACES = [
    ("wheat_kansas", "Wheat fields (Kansas)", 38.35, -98.60, "fields"),
    ("corn_iowa", "Cornfields (Iowa)", 42.05, -93.80, "fields"),
    ("pivots_kansas", "Round irrigated fields (Kansas)", 37.90, -100.95, "fields"),
    ("farms_pennsylvania", "Small farms (Pennsylvania)", 40.03, -76.10, "fields"),
    ("wheat_hills_washington", "Rolling wheat hills (Washington)", 46.90, -117.30, "fields"),
    ("cotton_mississippi", "Cotton fields (Mississippi)", 33.45, -90.65, "fields"),
    ("rice_california", "Rice paddies (California)", 39.30, -121.90, "fields"),
    ("orchards_california", "Orchards (California)", 37.55, -120.80, "fields"),
    ("vineyards_california", "Vineyards (California)", 38.43, -122.40, "fields"),
    ("prairie_kansas", "Tall grass prairie (Kansas)", 38.45, -96.55, "fields"),
    ("forest_pennsylvania", "Leafy forest (Pennsylvania)", 41.55, -78.85, "woods"),
    ("woods_wisconsin", "Woods and fields (Wisconsin)", 43.20, -90.55, "woods"),
    ("pines_arizona", "Pine forest (Arizona)", 35.05, -111.65, "woods"),
    ("oaks_california", "Oak grassland (California)", 37.40, -121.65, "woods"),
    ("swamp_louisiana", "Cypress swamp (Louisiana)", 30.25, -91.70, "woods"),
    ("desert_california", "Desert scrub (California)", 34.95, -116.60, "dry"),
    ("dunes_california", "Sand dunes (California)", 32.95, -115.10, "dry"),
    ("white_dunes_new_mexico", "White sand dunes (New Mexico)", 32.80, -106.25, "dry"),
    ("red_rock_arizona", "Red rock (Arizona)", 36.98, -110.10, "dry"),
    ("badlands_south_dakota", "Badlands (South Dakota)", 43.85, -102.25, "dry"),
    ("salt_flats_utah", "Salt flats (Utah)", 40.75, -113.85, "dry"),
    ("lava_idaho", "Lava fields (Idaho)", 43.42, -113.55, "dry"),
    ("marsh_florida", "Marsh (Florida)", 25.75, -80.75, "wet"),
    ("sandbars_nebraska", "River sand bars (Nebraska)", 40.68, -98.90, "wet"),
    ("beach_north_carolina", "Beach (North Carolina)", 35.25, -75.53, "wet"),
    ("rocky_coast_maine", "Rocky coast (Maine)", 44.33, -68.18, "wet"),
    ("glacier_washington", "Glacier snow (Washington)", 46.85, -121.75, "mountains"),
    ("tundra_colorado", "Mountain tundra (Colorado)", 40.40, -105.75, "mountains"),
    ("mine_utah", "Open pit mine (Utah)", 40.52, -112.15, "mountains"),
    ("town_kansas", "Small town streets (Kansas)", 38.574, -97.674, "towns"),
    ("old_town_georgia", "Old town squares (Georgia)", 32.077, -81.093, "towns"),
    ("rail_yard_nebraska", "Rail yard (Nebraska)", 41.13, -100.85, "towns"),
]


# --- over the network --------------------------------------------------------------------------------------------
def get(url: str, most: int, what: str) -> bytes:
    """`url`'s answer (HTTPS only), up to `most` bytes; OnlineError in plain words when it can't be had."""
    if not url.startswith("https://"):
        raise OnlineError(f"{what} isn't on a secure address, so it wasn't asked for")
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # noqa: S310 (https only, fixed hosts)
            data = r.read(most + 1)
    except (OSError, ValueError, http.client.HTTPException) as exc:
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
        raise OnlineError(f"{what} couldn't be loaded ({plain(exc, TIMEOUT)})") from None
    if len(data) > most:
        raise OnlineError(f"{what} is far bigger than one ever is, so it wasn't taken")
    return data


def _json(data: bytes, what: str):
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise OnlineError(f"{what} can't be read: the site answered something else") from None


def _host(url) -> str:
    try:
        return urllib.parse.urlsplit(str(url)).hostname or ""
    except ValueError:
        return ""


def _kept(file: Path):
    """A kept list's items while it's under a day old, else None."""
    try:
        if time.time() - file.stat().st_mtime > KEPT:
            return None
        doc = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc.get("items") if isinstance(doc, dict) and doc.get("format") == LIST_FORMAT else None


def _keep(file: Path, items: list) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    part = file.with_name(file.name + ".part")
    part.write_text(json.dumps({"format": LIST_FORMAT, "items": items}), encoding="utf-8")
    part.replace(file)


def _number(v) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None


def _strings(v) -> list[str]:
    return [t for t in v if isinstance(t, str)] if isinstance(v, list) else []


# --- Poly Haven --------------------------------------------------------------------------------------------------
def parse_polyhaven(doc, category: str) -> list[dict]:
    """A Poly Haven list's textures: {"id", "name", "metres" (its smaller side: the picture's middle square), "thumb",
    "tags", "author", "group" (the category it was listed in)}, by name."""
    out = []
    for key, a in (doc.items() if isinstance(doc, dict) else []):
        if not isinstance(a, dict) or not _ID.match(str(key)):
            continue
        dims = a.get("dimensions")
        sides = [_number(d) for d in dims] if isinstance(dims, list) and len(dims) == 2 else []
        metres = min(sides) / 1000.0 if sides and all(s and s > 0 for s in sides) else None  # (millimetres)
        authors = a.get("authors") if isinstance(a.get("authors"), dict) else {}
        thumb = a.get("thumbnail_url") if isinstance(a.get("thumbnail_url"), str) else ""
        words = _strings(a.get("tags")) + _strings(a.get("categories"))
        out.append({"id": key, "name": str(a.get("name") or key), "metres": metres,
                    "thumb": thumb if thumb.startswith("https://") else "", "tags": words,
                    "author": ", ".join(str(n) for n in authors) or "Poly Haven", "group": category})
    out.sort(key=lambda t: t["name"].lower())
    return out


def polyhaven_list(cache: Path) -> list[dict]:
    """Poly Haven's ground textures: the aerial ones, then the terrain ones not among them (kept a day)."""
    file = cache / "polyhaven.json"
    items = _kept(file)
    if items is not None:
        return items
    items, seen = [], set()
    for c in POLYHAVEN_CATEGORIES:
        doc = _json(get(POLYHAVEN_LIST.format(category=c), LIST_MOST, "Poly Haven's list"), "Poly Haven's list")
        for t in parse_polyhaven(doc, c):
            if t["id"] not in seen:
                seen.add(t["id"])
                items.append(t)
    _keep(file, items)
    return items


def polyhaven_colour_url(doc) -> str:
    """The 1k JPG of a Poly Haven texture's colour map, from its files list (api.polyhaven.com/files/<id>)."""
    maps = {str(k).lower(): v for k, v in doc.items()} if isinstance(doc, dict) else {}
    for name in POLYHAVEN_COLOUR:
        try:
            url = maps[name]["1k"]["jpg"]["url"]
        except (KeyError, TypeError):
            continue
        if isinstance(url, str) and url.startswith("https://") and _host(url) in POLYHAVEN_HOSTS:
            return url
    raise OnlineError("that Poly Haven texture has no colour picture at 1k to take")


# --- ambientCG ---------------------------------------------------------------------------------------------------
def _words_slug(words: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", words.lower()).strip("_")[:60] or "_"


def parse_ambientcg(doc) -> list[dict]:
    """An ambientCG list's materials that have a 1K-JPG download: {"id", "name", "metres" (its smaller side, None when
    not known), "thumb", "tags", "author", "page", "zip", "size"}."""
    out = []
    for a in (doc.get("foundAssets") or []) if isinstance(doc, dict) else []:
        if not isinstance(a, dict) or not _ID.match(str(a.get("assetId", ""))):
            continue
        key = a["assetId"]
        zip_link, size = AMBIENTCG_ZIP.format(id=key), None
        for folder in (a.get("downloadFolders") or {}).values() if isinstance(a.get("downloadFolders"), dict) else []:
            kinds = folder.get("downloadFiletypeCategories") if isinstance(folder, dict) else None
            for d in ((kinds or {}).get("zip") or {}).get("downloads") or []:
                if isinstance(d, dict) and d.get("attribute") == "1K-JPG":
                    size = _number(d.get("size"))
                    link = d.get("downloadLink")
                    if isinstance(link, str) and link.startswith("https://ambientcg.com/get?file="):
                        zip_link = link
        if size is None:
            continue  # (no 1K-JPG of it to take)
        sides = [_number(a.get("dimensionX")), _number(a.get("dimensionY"))]
        metres = min(sides) / 100.0 if all(s and s > 0 for s in sides) else None  # (centimetres; 0: not known)
        previews = a.get("previewImage") if isinstance(a.get("previewImage"), dict) else {}
        thumb = next((previews[k] for k in AMBIENTCG_THUMBS if isinstance(previews.get(k), str)), "")
        page = a.get("shortLink") if isinstance(a.get("shortLink"), str) else AMBIENTCG_PAGE.format(id=key)
        out.append({"id": key, "name": str(a.get("displayName") or key), "metres": metres,
                    "thumb": thumb if thumb.startswith("https://") else "",
                    "tags": _strings(a.get("tags")), "author": "ambientCG",
                    "page": page if page.startswith("https://") else AMBIENTCG_PAGE.format(id=key),
                    "zip": zip_link, "size": size})
    return out


def ambientcg_list(cache: Path, words: str = "") -> list[dict]:
    """ambientCG's materials found by `words` (AMBIENTCG_WORDS when none), the most popular first (kept a day)."""
    words = " ".join(str(words or "").split())[:80] or AMBIENTCG_WORDS
    file = cache / f"ambientcg-{_words_slug(words)}.json"
    items = _kept(file)
    if items is not None:
        return items
    url = AMBIENTCG_LIST.format(q=urllib.parse.quote(words), limit=AMBIENTCG_LIMIT)
    items = parse_ambientcg(_json(get(url, LIST_MOST, "ambientCG's list"), "ambientCG's list"))
    _keep(file, items)
    return items


def ambientcg_colour(data: bytes) -> bytes:
    """The colour picture (*_Color.jpg) out of an ambientCG zip, read in memory."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            found = [i for i in z.infolist() if re.search(r"(?i)_colou?r\.jpe?g$", i.filename)]
            if not found:
                raise OnlineError("that ambientCG download has no colour picture in it")
            pick = min(found, key=lambda i: len(i.filename))
            if pick.file_size > PICTURE_MOST:
                raise OnlineError("that ambientCG colour picture is far bigger than a 1K one ever is")
            return z.read(pick)
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        if isinstance(exc, OnlineError):
            raise
        raise OnlineError("that ambientCG download can't be opened: the site answered something else") from None


# --- US aerial photos --------------------------------------------------------------------------------------------
def naip_pixels(metres: float) -> int:
    """Pixels across a photo `metres` across: the power of two nearest NAIP_PIXEL a pixel, NAIP_LEAST..NAIP_MOST."""
    n = 2 ** round(math.log2(max(metres, 1.0) / NAIP_PIXEL))
    return int(min(NAIP_MOST, max(NAIP_LEAST, n)))


def naip_url(lat: float, lon: float, metres: float) -> str:
    """The imagery service's exportImage address for a square `metres` across centred at (lat, lon): in Web Mercator
    (its own spatial reference), where a metre on the ground is 1 / cos(latitude) of its units, as a JPG."""
    x = EARTH * math.radians(lon)
    y = EARTH * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    half = metres / 2 / math.cos(math.radians(lat))
    n = naip_pixels(metres)
    query = {"bbox": f"{x - half:.2f},{y - half:.2f},{x + half:.2f},{y + half:.2f}", "bboxSR": "3857",
             "imageSR": "3857", "size": f"{n},{n}", "format": "jpg", "f": "image"}
    return f"{NAIP}/exportImage?" + urllib.parse.urlencode(query)


def parse_where(text) -> tuple[float, float]:
    """A typed or pasted "latitude, longitude" (38.2, -98.4) in the 48 states; OnlineError in plain words else."""
    found = re.findall(r"[-+]?\d+(?:\.\d+)?", str(text or ""))
    if len(found) != 2:
        raise OnlineError("type a latitude and a longitude, like 38.2, -98.4")
    lat, lon = float(found[0]), float(found[1])
    if not (US_LAT[0] <= lat <= US_LAT[1] and US_LON[0] <= lon <= US_LON[1]):
        raise OnlineError(f"{lat:g}, {lon:g} isn't in the 48 US states, the only ground these photos cover")
    return lat, lon


def naip_photo(lat: float, lon: float, metres: float) -> bytes:
    data = get(naip_url(lat, lon, metres), PICTURE_MOST, "The aerial photo")
    if not data.startswith(b"\xff\xd8\xff"):
        said = ""
        try:
            said = str(json.loads(data.decode("utf-8")).get("error", {}).get("message") or "")
        except (UnicodeDecodeError, ValueError, AttributeError):
            pass
        raise OnlineError("the photo service didn't send a photo" + (f" ({said})" if said else ""))
    return data


# --- one picture -------------------------------------------------------------------------------------------------
def _data_url(data: bytes) -> str:
    kind = "jpeg" if data.startswith(b"\xff\xd8\xff") else "png" if data.startswith(b"\x89PNG") else None
    if kind is None:
        raise OnlineError("the site didn't send a picture")
    return f"data:image/{kind};base64," + base64.b64encode(data).decode("ascii")


def _listed(cache: Path, pattern: str, item: str) -> dict | None:
    """An item from any list kept (however old): the one the modder clicked was shown from one."""
    for file in sorted(cache.glob(pattern)):
        try:
            doc = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for t in doc.get("items") or [] if isinstance(doc, dict) else []:
            if isinstance(t, dict) and t.get("id") == item:
                return t
    return None


def picture(cache: Path, source: str, item: str = "", metres: float = 0, where: str = "") -> dict:
    """Download ONE picture: {"name" (for its file in files/ground), "picture": a JPG or PNG data URL, "metres" (the
    ground it covers across, None when not known), "credit": {"source", "author", "licence", "url"}}."""
    if source == "polyhaven":
        t = _listed(cache, "polyhaven.json", item) or next(
            (x for x in polyhaven_list(cache) if x["id"] == item), None)
        if t is None:
            raise OnlineError(f"Poly Haven has no texture {item!r} in its list")
        files = _json(get(POLYHAVEN_FILES.format(id=urllib.parse.quote(item)), LIST_MOST, "Poly Haven's files"),
                      "Poly Haven's files")
        data = get(polyhaven_colour_url(files), PICTURE_MOST, "The Poly Haven picture")
        credit = {"source": "Poly Haven", "author": t.get("author") or "Poly Haven", "licence": "CC0",
                  "url": POLYHAVEN_PAGE.format(id=item)}
        return {"name": t["name"], "picture": _data_url(data), "metres": t.get("metres"), "credit": credit}
    if source == "ambientcg":
        t = _listed(cache, "ambientcg-*.json", item)
        if t is None:
            raise OnlineError(f"ambientCG's material {item!r} isn't in a list found here: find it again")
        if _host(t.get("zip")) != "ambientcg.com":
            raise OnlineError("that ambientCG download isn't on ambientcg.com, so it wasn't asked for")
        most = min(ZIP_MOST, int(t["size"] * 1.25) + 65536) if t.get("size") else ZIP_MOST
        data = ambientcg_colour(get(t["zip"], most, "The ambientCG download"))
        credit = {"source": "ambientCG", "author": "ambientCG", "licence": "CC0",
                  "url": t.get("page") or AMBIENTCG_PAGE.format(id=item)}
        return {"name": t["name"], "picture": _data_url(data), "metres": t.get("metres"), "credit": credit}
    if source == "usgs":
        side = float(metres or NAIP_DEFAULT)
        if side not in NAIP_METRES:
            raise OnlineError(f"a photo is {', '.join(str(m) for m in NAIP_METRES)} m across")
        place = next((p for p in PLACES if p[0] == item), None) if item else None
        if place is not None:
            lat, lon, name = place[2], place[3], re.sub(r"[()]", "", place[1])
        elif item:
            raise OnlineError(f"there's no place {item!r} in the list")
        else:
            lat, lon = parse_where(where)
            name = f"US photo {lat:.4f} {lon:.4f}"
        data = naip_photo(lat, lon, side)
        credit = {"source": f"USGS National Map, NAIP imagery ({lat:.4f}, {lon:.4f})",
                  "author": "USDA Farm Production and Conservation, through the USGS", "licence": "Public domain",
                  "url": NAIP}
        return {"name": f"{name} {side:g}m", "picture": _data_url(data), "metres": side, "credit": credit}
    raise OnlineError(f"{source!r} isn't one of the online sources")


def listing(cache: Path, source: str, words: str = "") -> dict:
    """What the page lists for a source: {"source", "licence", "items"} (usgs: the places, with "metres": the sizes
    to choose from and "default")."""
    if source == "polyhaven":
        return {"source": source, "licence": "CC0", "items": polyhaven_list(cache)}
    if source == "ambientcg":
        return {"source": source, "licence": "CC0", "items": ambientcg_list(cache, words),
                "words": " ".join(str(words or "").split()) or AMBIENTCG_WORDS}
    if source == "usgs":
        return {"source": source, "licence": "Public domain", "metres": list(NAIP_METRES), "default": NAIP_DEFAULT,
                "items": [{"id": k, "name": n, "lat": la, "lon": lo, "group": g} for k, n, la, lo, g in PLACES]}
    raise OnlineError(f"{source!r} isn't one of the online sources")
