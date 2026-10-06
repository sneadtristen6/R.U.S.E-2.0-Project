"""The game index (docs/PLAN.md L2): one SQLite file per game build that knows every pack, file, NDF object, reference
and text, so tools can ask "where is this used", "which units have X above Y" or "what would a clone copy" in well under
a second instead of opening packs.

Built read-only from the install (`build_index`), queried through `Index`. Tables:

  meta       build key, data revision, format version, build time
  pack       every archive, nested ones included: name, location, size, SHA-256, layer (core, map, nested), parent
  file       every file: location (pack!path[!path]), game path, size, SHA-1, type (from its first bytes), map name
  ndf        every NDF file: object/class/property/string counts, whether it has a TOPO table, SHA-1 uncompressed
  object     every NDF object: file, index, class, export path, stable address, stable?, shared?, and whether it's
             in a debug-info copy (`*_debuginfo` files repeat their main file's names; lookups prefer the main file)
  owner      (unnamed object, named object that reaches it); more than one owner = shared
  ref        from object + property path to: an object, an import path, a file path, or a text key
  import     every IMPR entry and the object it resolves to in another file (when found)
  prop_seen  class + property + type: how often, min and max for numbers, an example (feeds the schema DB); a list's
             items are listed as `Prop[]`
  value      the numbers and texts of every object's properties (top level; list items up to 16), for filters
  text       every .dic entry: file, language, dictionary, key, key name, text

Stable addresses (L2): a named object's export path (`$/GFX/Everything/Descriptor_Unit_X`); an unnamed object through
its nearest named owner (`$/GFX/Everything/Descriptor_Unit_X:Weapons[0].Ammunition`), found breadth first from the
named objects in export-path order, so the shortest path wins and ties go to the owner whose path sorts first. A list
position becomes a class selector (`Turrets[class=TTurretDescriptor]`) when that class appears once among the list's
objects: it survives lists being reordered, and the patch engine understands it. Objects no named object reaches get
`<game path>#<index>` (marked unstable). These addresses work as `.rndf` patch targets.
"""
from __future__ import annotations

import hashlib
import html
import os
import re
import sqlite3
import struct
import time
from collections import defaultdict, deque
from pathlib import Path

from .build import SHADOW
from .dic import GLYPH_KEY, Dic, key_to_name
from .edat import Edat
from .ndf import SCALAR, Ndf, decode, sub_values
from .steam import build_of, data_revisions

FORMAT = "4"  # 3: whole flag lists (WHOLE_LISTS); 4: the keys of top-level maps
TYPES = {0x00: "bool", 0x01: "int8", 0x02: "int32", 0x03: "uint32", 0x05: "float32", 0x06: "float64", 0x07: "string",
         0x08: "wide string", 0x09: "reference", 0x0B: "vec3f", 0x0C: "float4", 0x0D: "color32", 0x11: "list",
         0x12: "map", 0x13: "int64", 0x14: "blob", 0x18: "int16", 0x19: "uint16", 0x1A: "guid", 0x1C: "path",
         0x1D: "text key", 0x1E: "zip blob", 0x1F: "int2", 0x21: "float2", 0x22: "pair"}
_LANG = re.compile(r"\\translations\\([^\\]+)\\|\\(dev)\\", re.I)
_MAP = re.compile(r"^DataMap(.+?)(?:_v\d+)?\.dat$", re.I)
_FILEISH = re.compile(r"[\\/].*\.[A-Za-z0-9]{2,5}$|^[A-Za-z]+:")
LIST_VALUES = 16  # list items stored in `value` per property
WHOLE_LISTS = {"InitialFlagSet": 256}  # lists stored whole (up to this many items): a unit's flags, up to 17 in the game

SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE pack(id INTEGER PRIMARY KEY, name TEXT, location TEXT UNIQUE, size INTEGER, sha256 TEXT, layer TEXT,
                  parent INTEGER);
CREATE TABLE file(id INTEGER PRIMARY KEY, pack INTEGER, location TEXT UNIQUE, game_path TEXT, display TEXT,
                  size INTEGER, sha1 TEXT, type TEXT, map TEXT);
CREATE TABLE ndf(file INTEGER PRIMARY KEY, objects INTEGER, classes INTEGER, props INTEGER, strings INTEGER,
                 has_topo INTEGER, sha1 TEXT);
CREATE TABLE object(id INTEGER PRIMARY KEY, file INTEGER, idx INTEGER, class TEXT, export TEXT, address TEXT,
                    stable INTEGER, shared INTEGER, shadow INTEGER);
CREATE TABLE owner(object INTEGER, owner INTEGER);
CREATE TABLE ref(src INTEGER, path TEXT, kind TEXT, dst INTEGER, target TEXT);
CREATE TABLE import(file INTEGER, idx INTEGER, path TEXT, object INTEGER);
CREATE TABLE prop_seen(class TEXT, prop TEXT, type TEXT, count INTEGER, min REAL, max REAL, example TEXT,
                       PRIMARY KEY(class, prop, type));
CREATE TABLE value(object INTEGER, path TEXT, num REAL, text TEXT);
CREATE TABLE text(file INTEGER, lang TEXT, dictionary TEXT, key TEXT, name TEXT, text TEXT);
"""
INDEXES = """
CREATE INDEX file_game_path ON file(game_path);
CREATE INDEX object_file ON object(file, idx);
CREATE INDEX object_export ON object(export);
CREATE INDEX object_address ON object(address);
CREATE INDEX object_class ON object(class);
CREATE INDEX owner_object ON owner(object);
CREATE INDEX ref_src ON ref(src);
CREATE INDEX ref_dst ON ref(dst);
CREATE INDEX ref_target ON ref(kind, target);
CREATE INDEX import_file_path ON import(file, path);
CREATE INDEX value_path ON value(path, num);
CREATE INDEX value_object ON value(object);
CREATE INDEX text_name ON text(name);
"""


def build_key(game: Path) -> str:
    return f"{build_of(game) or 'unknown'}-{(data_revisions(game) or ['0'])[-1]}"


def default_path(game: Path) -> Path:
    from .home import default_home
    return default_home() / "index" / f"{build_key(game)}.sqlite"


def game_packs(game: Path) -> list[tuple[Path, str]]:
    """(pack, layer) for the core packs (every data revision) and the map packs."""
    out = []
    for rev in data_revisions(game):
        out += [(p, "core") for p in sorted((game / "Data" / "PC" / rev).glob("*.dat"))]
    out += [(p, "map") for p in sorted((game / "Maps" / "PC").glob("*.dat"))] if (game / "Maps" / "PC").is_dir() else []
    return out


def walk(v, path: str):
    """(path, value) for `v` and everything inside it: list items `[i]`, map entries `[i].k` / `[i].v`, pairs `.0` / `.1`."""
    yield path, v
    if v.tc == 0x11:
        for i, x in enumerate(sub_values(v)):
            yield from walk(x, f"{path}[{i}]")
    elif v.tc == 0x12:
        items = sub_values(v)
        for i in range(0, len(items), 2):
            yield from walk(items[i], f"{path}[{i // 2}].k")
            yield from walk(items[i + 1], f"{path}[{i // 2}].v")
    elif v.tc == 0x22:
        a, b = sub_values(v)
        yield from walk(a, f"{path}.0")
        yield from walk(b, f"{path}.1")


def _type_of(data: bytes, name: str) -> str:
    if data[:4] == b"edat":
        return "pack"
    if data[:4] == b"EUG0" and data[8:12] == b"CNDF":
        return "ndf"
    if data[:3] == b"TRA":
        return "dic"
    ext = os.path.splitext(name)[1].lower().lstrip(".")
    return ext or "?"


class _Builder:
    def __init__(self, db: sqlite3.Connection, say):
        self.db, self.say = db, say
        self.counts = defaultdict(int)
        self.prop_seen: dict[tuple, list] = {}

    # --- packs and files ---
    def pack(self, arc: Edat, name: str, location: str, layer: str, parent, size: int, sha256: str, map_name,
             mount: str) -> None:
        cur = self.db.execute("INSERT INTO pack(name, location, size, sha256, layer, parent) VALUES (?,?,?,?,?,?)",
                              (name, location, size, sha256, layer, parent))
        pack_id = cur.lastrowid
        self.counts[f"{layer} packs"] += 1
        for e in arc.entries:
            data = bytes(arc.read(e))
            loc = f"{location}!{e.path}"
            game_path = e.path.replace("\\", "/").lower()
            if mount:
                game_path = f"{mount}/{game_path}"
            kind = _type_of(data, e.path)
            cur = self.db.execute(
                "INSERT INTO file(pack, location, game_path, display, size, sha1, type, map) VALUES (?,?,?,?,?,?,?,?)",
                (pack_id, loc, game_path, e.path, len(data), hashlib.sha1(data).hexdigest(), kind, map_name))
            file_id = cur.lastrowid
            self.counts["files"] += 1
            if kind == "pack":
                try:
                    inner = Edat(data)
                except ValueError as exc:
                    self.say(f"  note: {loc} looks like a pack but isn't readable ({exc})")
                    continue
                self.pack(inner, e.path.rsplit("\\", 1)[-1], loc, "nested", pack_id, len(data),
                          hashlib.sha256(data).hexdigest(), map_name, mount="")
            elif kind == "ndf":
                self.ndf(file_id, game_path, data)
            elif kind == "dic":
                self.dic(file_id, loc, data)

    # --- NDF ---
    def ndf(self, file_id: int, game_path: str, raw: bytes) -> None:
        ndf = Ndf(raw)
        n = len(ndf.objects)
        self.db.execute("INSERT INTO ndf VALUES (?,?,?,?,?,?,?)",
                        (file_id, n, len(ndf.classes), len(ndf.props), len(ndf.strings), int(bool(ndf.topo)),
                         hashlib.sha1(decode(raw)).hexdigest()))
        self.counts["NDF files"] += 1
        self.counts["objects"] += n
        # every value of every object, with its path; local references per object for the address walk
        values: list[list[tuple[str, object]]] = []
        children: list[list[tuple[str, int]]] = []
        mixed: set[tuple[int, str]] = set()  # (object, list path) of lists that also hold imports
        for i, o in enumerate(ndf.objects):
            vals, kids = [], []
            for pi, v in o.props:
                for path, x in walk(v, ndf.prop_name(pi)):
                    vals.append((path, x))
                    if x.tc == 0x09:
                        sub, idx = struct.unpack_from("<II", x.payload)
                        if sub == 0xBBBBBBBB and idx != 0xFFFFFFFF and idx < n:
                            kids.append((path, idx))
                        elif sub == 0xAAAAAAAA and path.endswith("]"):
                            mixed.add((i, path[:path.rfind("[")]))
            values.append(vals)
            children.append(kids)
        address, stable, owners = self._addresses(ndf, game_path, children, mixed)
        shadow = int(bool(SHADOW.search(game_path)))
        first = self.db.execute("SELECT COALESCE(MAX(id), 0) FROM object").fetchone()[0] + 1
        rows = []
        for i, o in enumerate(ndf.objects):
            cls = ndf.classes[o.cls]
            rows.append((first + i, file_id, i, cls, ndf.exports.get(i), address[i], stable[i],
                         int(len(owners.get(i, ())) > 1), shadow))
        self.db.executemany("INSERT INTO object VALUES (?,?,?,?,?,?,?,?,?)", rows)
        self.db.executemany("INSERT INTO owner VALUES (?,?)",
                            [(first + i, first + j) for i, js in owners.items() for j in sorted(js)])
        self.db.executemany("INSERT INTO import VALUES (?,?,?,NULL)",
                            [(file_id, k, p) for k, p in sorted(ndf.imports.items())])
        refs, vals_out = [], []
        for i, o in enumerate(ndf.objects):
            cls, oid = ndf.classes[o.cls], first + i
            for pi, v in o.props:
                self._seen(cls, ndf.prop_name(pi), v, ndf)
                if v.tc == 0x11:  # a list's items too, as `Prop[]` (the Studio needs to know whole numbers)
                    for x in sub_values(v):
                        self._seen(cls, ndf.prop_name(pi) + "[]", x, ndf)
            for path, x in values[i]:
                tc = x.tc
                if tc == 0x09:
                    sub, idx = struct.unpack_from("<II", x.payload)
                    if sub == 0xBBBBBBBB and idx != 0xFFFFFFFF and idx < n:
                        refs.append((oid, path, "object", first + idx, None))
                    elif sub == 0xAAAAAAAA:
                        refs.append((oid, path, "import", None, ndf.imports.get(idx, f"<import #{idx}>")))
                elif tc in (0x07, 0x1C):
                    s = ndf.strings[struct.unpack("<I", x.payload)[0]]
                    if tc == 0x1C or _FILEISH.search(s):
                        refs.append((oid, path, "file", None, s.replace("\\", "/").lower()))
                    if self._stored(path):
                        vals_out.append((oid, path, None, s))
                elif tc == 0x1D:
                    key = struct.unpack("<Q", x.payload)[0]
                    name = key_to_name(key) or f"0x{key:016X}"
                    refs.append((oid, path, "text", None, name))
                    if self._stored(path):
                        vals_out.append((oid, path, None, name))
                elif tc in SCALAR and self._stored(path):
                    vals_out.append((oid, path, float(struct.unpack(SCALAR[tc], x.payload)[0]), None))
        self.db.executemany("INSERT INTO ref VALUES (?,?,?,?,?)", refs)
        self.db.executemany("INSERT INTO value VALUES (?,?,?,?)", vals_out)
        self.counts["references"] += len(refs)

    @staticmethod
    def _stored(path: str) -> bool:
        """Top-level numbers, the first items of top-level lists of numbers (Price[0] … Price[15]; all of a
        WHOLE_LISTS list), and the keys of top-level maps (SousElements[39].k = weapon_effet_tag1: which part of a
        model a weapon fires from; BinderEffets[0].k = tir: which effect is its shot)."""
        if "[" not in path:
            return "." not in path
        if re.fullmatch(r"[^.\[\]]+\[\d+\]\.k", path):
            return True
        m = re.fullmatch(r"([^.\[\]]+)\[(\d+)\]", path)
        return bool(m) and int(m.group(2)) < WHOLE_LISTS.get(m.group(1), LIST_VALUES)

    def _addresses(self, ndf: Ndf, game_path: str, children, mixed):
        n = len(ndf.objects)
        address: list[str | None] = [None] * n
        stable = [1] * n
        roots = sorted(ndf.exports.items(), key=lambda kv: kv[1])
        # class selectors: a list item whose class appears once among that list's objects
        selector = {}
        for i, kids in enumerate(children):
            by_list = defaultdict(list)
            for path, j in kids:
                m = re.fullmatch(r"(.*)\[(\d+)\]", path)
                if m:
                    by_list[m.group(1)].append((path, j))
            for base, items in by_list.items():
                if (i, base) in mixed:  # the patch engine counts imported items too; stay with positions
                    continue
                classes = [ndf.classes[ndf.objects[j].cls] for _p, j in items]
                for (path, j), cls in zip(items, classes):
                    if classes.count(cls) == 1:
                        selector[(i, path)] = f"{base}[class={cls}]"
        queue = deque()
        for i, path in roots:
            address[i] = path
            queue.append(i)
        while queue:
            i = queue.popleft()
            for path, j in children[i]:
                if address[j] is not None:
                    continue
                step = selector.get((i, path), path)
                address[j] = f"{address[i]}:{step}" if i in ndf.exports else f"{address[i]}.{step}"
                queue.append(j)
        for i in range(n):
            if address[i] is None:
                address[i], stable[i] = f"{game_path}#{i}", 0
                self.counts["last-resort addresses"] += 1
        # every named object that reaches each unnamed one (through unnamed objects only)
        owners: dict[int, set] = defaultdict(set)
        for r, _path in roots:
            seen, stack = set(), [r]
            while stack:
                i = stack.pop()
                for _p, j in children[i]:
                    if j in ndf.exports or j in seen:
                        continue
                    seen.add(j)
                    owners[j].add(r)
                    stack.append(j)
        self.counts["shared objects"] += sum(1 for js in owners.values() if len(js) > 1)
        return address, stable, owners

    def _seen(self, cls: str, prop: str, v, ndf: Ndf) -> None:
        key = (cls, prop, TYPES.get(v.tc, f"0x{v.tc:02X}"))
        entry = self.prop_seen.get(key)
        num = example = None
        if v.tc in SCALAR:
            num = float(struct.unpack(SCALAR[v.tc], v.payload)[0])
        if entry is None:
            if num is not None:
                example = repr(num)
            elif v.tc in (0x07, 0x1C):
                example = ndf.strings[struct.unpack("<I", v.payload)[0]][:80]
            elif v.tc == 0x11:
                example = f"{struct.unpack_from('<I', v.payload)[0]} items"
            self.prop_seen[key] = [1, num, num, example]
            return
        entry[0] += 1
        if num is not None:
            entry[1] = num if entry[1] is None else min(entry[1], num)
            entry[2] = num if entry[2] is None else max(entry[2], num)

    # --- texts ---
    def dic(self, file_id: int, location: str, raw: bytes) -> None:
        try:
            dic = Dic(raw)
        except ValueError:
            return
        m = _LANG.search(location)
        lang = (m.group(1) or m.group(2)).lower() if m else ""
        dictionary = os.path.splitext(location.rsplit("\\", 1)[-1])[0].lower()
        rows = [(file_id, lang, dictionary, f"{e.key:016X}", e.name, e.text)
                for e in dic.entries if e.key != GLYPH_KEY]
        self.db.executemany("INSERT INTO text VALUES (?,?,?,?,?,?)", rows)
        self.counts["texts"] += len(rows)

    def finish(self) -> None:
        self.db.executemany("INSERT INTO prop_seen VALUES (?,?,?,?,?,?,?)",
                            [(c, p, t, e[0], e[1], e[2], e[3]) for (c, p, t), e in sorted(self.prop_seen.items())])
        self.db.executescript(INDEXES)
        # imports resolve to the named object with that export path (a file that isn't a debug-info copy first)
        self.db.execute("""
            UPDATE import SET object = (
              SELECT o.id FROM object o WHERE o.export = import.path ORDER BY o.shadow, o.id LIMIT 1)""")
        self.db.execute("""
            UPDATE ref SET dst = (
              SELECT i.object FROM import i JOIN object s ON s.file = i.file
              WHERE s.id = ref.src AND i.path = ref.target LIMIT 1)
            WHERE kind = 'import'""")
        total, found = self.db.execute("SELECT COUNT(*), COUNT(object) FROM import").fetchone()
        self.counts["imports"], self.counts["imports resolved"] = total, found


def build_index(game: Path, out: Path | None = None, say=print) -> Path:
    """Build the index of the game at `game` into `out` (default: the platform folder, one file per build).
    Read-only for the game. Returns the index file."""
    game = Path(game)
    out = Path(out) if out else default_path(game)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".partial")
    if tmp.exists():
        tmp.unlink()
    packs = game_packs(game)
    if not packs:
        raise FileNotFoundError(f"no packs found under {game}")
    start = time.time()
    db = sqlite3.connect(tmp)
    try:
        db.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;" + SCHEMA)
        b = _Builder(db, say)
        for path, layer in packs:
            say(f"  {path.name}")
            sha = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(1 << 22), b""):
                    sha.update(chunk)
            m = _MAP.match(path.name) if layer == "map" else None
            with Edat.open(str(path)) as arc:
                b.pack(arc, path.name, path.name, layer, None, path.stat().st_size, sha.hexdigest(),
                       m.group(1) if m else None, mount="datasmap" if layer == "map" else "")
        b.finish()
        meta = {"format": FORMAT, "build": build_of(game) or "unknown", "data_revision": ",".join(data_revisions(game)),
                "game": str(game), "built": time.strftime("%Y-%m-%d %H:%M:%S"), "seconds": f"{time.time() - start:.0f}"}
        meta.update({f"count: {k}": str(v) for k, v in b.counts.items()})
        db.executemany("INSERT INTO meta VALUES (?,?)", sorted(meta.items()))
        db.commit()
    finally:
        db.close()
    _replace_when_free(tmp, out)
    return out


def _replace_when_free(tmp: Path, out: Path, tries: int = 50, wait: float = 0.1) -> None:
    """os.replace(tmp, out), waiting up to tries * wait seconds while something reads the old index: Windows won't
    replace a file another reader has open (the Studio's Maps tab can read an old index while the new one builds)."""
    for n in range(tries):
        try:
            os.replace(tmp, out)
            return
        except PermissionError:
            if n == tries - 1:
                raise
            time.sleep(wait)


class Index:
    """Questions for a built index. Addresses are the stable addresses described above."""

    def __init__(self, path):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"no index at {self.path}; build it first (ruse index build)")
        self.db = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)  # read-only; safe on Windows paths

    def close(self) -> None:
        self.db.close()

    def meta(self) -> dict:
        return dict(self.db.execute("SELECT key, value FROM meta"))

    def _object(self, address: str):
        row = self.db.execute("SELECT id FROM object WHERE address = ? OR export = ? ORDER BY shadow, id LIMIT 1",
                              (address, address)).fetchone()
        if row is None:
            raise KeyError(f"no object at {address!r}")
        return row[0]

    def find(self, words: str, limit: int = 50) -> list[tuple[str, str]]:
        """(address, class) of objects whose address or class contains `words`, named objects first."""
        like = f"%{words}%"
        return self.db.execute("""SELECT address, class FROM object WHERE (address LIKE ? OR class LIKE ?) AND shadow = 0
                                  ORDER BY stable DESC, export IS NULL, address LIMIT ?""", (like, like, limit)).fetchall()

    def of_class(self, cls: str) -> list[dict]:
        """Every object of `cls` as show() gives it, each with the game file it's in: for objects that share one name
        in several files (rusemod.economy's two copies), where an address reaches only the first."""
        rows = self.db.execute("""SELECT o.id FROM object o JOIN file f ON f.id = o.file
                                  WHERE o.class = ? AND o.shadow = 0 ORDER BY f.location, o.idx""", (cls,)).fetchall()
        return [self._shown(oid) for (oid,) in rows]

    def show(self, address: str) -> dict:
        """One object: where it lives, its class, its numbers and texts, who owns it."""
        return self._shown(self._object(address))

    def _shown(self, oid: int) -> dict:
        o = self.db.execute("""SELECT o.address, o.class, o.export, o.stable, o.shared, o.idx, f.location
                               FROM object o JOIN file f ON f.id = o.file WHERE o.id = ?""", (oid,)).fetchone()
        values = self.db.execute("SELECT path, num, text FROM value WHERE object = ? ORDER BY rowid", (oid,)).fetchall()
        owners = [r[0] for r in self.db.execute("""SELECT o.address FROM owner w JOIN object o ON o.id = w.owner
                                                   WHERE w.object = ? ORDER BY o.address""", (oid,))]
        return {"address": o[0], "class": o[1], "export": o[2], "stable": bool(o[3]), "shared": bool(o[4]),
                "index": o[5], "file": o[6], "values": values, "owners": owners}

    def used_by(self, address: str) -> list[tuple[str, str]]:
        """(address, property path) of every object that refers to this one, in its own file or through imports."""
        oid = self._object(address)
        return self.db.execute("""SELECT s.address, r.path FROM ref r JOIN object s ON s.id = r.src
                                  WHERE r.dst = ? AND s.shadow = 0 ORDER BY s.address, r.path""", (oid,)).fetchall()

    def uses(self, address: str) -> list[tuple[str, str, str]]:
        """(property path, kind, what) of everything this object refers to: objects, imports, files and texts."""
        oid = self._object(address)
        rows = self.db.execute("""SELECT r.path, r.kind, COALESCE(d.address, r.target) FROM ref r
                                  LEFT JOIN object d ON d.id = r.dst WHERE r.src = ? ORDER BY r.rowid""", (oid,))
        return rows.fetchall()

    def where_file(self, fragment: str, limit: int = 100) -> list[tuple[str, str, str]]:
        """(object address, property path, file path) of data that mentions a file path containing `fragment`."""
        return self.db.execute("""SELECT s.address, r.path, r.target FROM ref r JOIN object s ON s.id = r.src
                                  WHERE r.kind = 'file' AND r.target LIKE ? AND s.shadow = 0
                                  ORDER BY r.target, s.address LIMIT ?""",
                               (f"%{fragment.replace(chr(92), '/').lower()}%", limit)).fetchall()

    def filter(self, cls: str, path: str, op: str, number: float, limit: int = 200) -> list[tuple[str, float]]:
        """(address, value) of objects of `cls` whose number at `path` compares with `op` (< <= = >= > !=)."""
        if op not in ("<", "<=", "=", ">=", ">", "!="):
            raise ValueError(f"unknown comparison {op!r}")
        return self.db.execute(f"""SELECT o.address, v.num FROM value v JOIN object o ON o.id = v.object
                                   WHERE o.class = ? AND v.path = ? AND v.num {op} ? AND o.shadow = 0
                                   ORDER BY v.num DESC, o.address LIMIT ?""", (cls, path, number, limit)).fetchall()

    def texts(self, words: str, lang: str = "us", limit: int = 50) -> list[tuple[str, str, str]]:
        """(key name, dictionary, text) of texts containing `words` in one language."""
        return self.db.execute("""SELECT COALESCE(name, key), dictionary, text FROM text
                                  WHERE lang = ? AND text LIKE ? ORDER BY dictionary, name LIMIT ?""",
                               (lang, f"%{words}%", limit)).fetchall()

    def text_used_by(self, name: str) -> list[tuple[str, str]]:
        """(address, property path) of the data that shows the text with this key name."""
        return self.db.execute("""SELECT s.address, r.path FROM ref r JOIN object s ON s.id = r.src
                                  WHERE r.kind = 'text' AND r.target = ? AND s.shadow = 0
                                  ORDER BY s.address""", (name,)).fetchall()

    def unused_texts(self, lang: str = "us", dictionary: str | None = None, limit: int = 100):
        """(key name, dictionary, text) of texts no NDF data refers to. Scripts and the program may still use some."""
        return self.db.execute("""SELECT COALESCE(t.name, t.key), t.dictionary, t.text FROM text t
                                  WHERE t.lang = ? AND (? IS NULL OR t.dictionary = ?) AND NOT EXISTS
                                    (SELECT 1 FROM ref r WHERE r.kind = 'text' AND r.target = COALESCE(t.name, '0x' || t.key))
                                  ORDER BY t.dictionary, t.name LIMIT ?""",
                               (lang, dictionary, dictionary, limit)).fetchall()

    def units(self, classes) -> list[dict]:
        """Named objects of `classes` (units, buildings…) with their nation, factory, menu slot, name key, type key
        (TypeUnitHintToken: the game's own "Light Tank", "Heavy Bomber", "Armored Recon"... on the unit's card) and
        description key (the card's line, "May field armored units and armored recon."; else its long text)."""
        marks = ",".join("?" * len(classes))
        rows = self.db.execute(f"""
            SELECT o.address, o.class,
              (SELECT num FROM value WHERE object = o.id AND path = 'Nationalite'),
              (SELECT num FROM value WHERE object = o.id AND path = 'Factory'),
              (SELECT num FROM value WHERE object = o.id AND path = 'PositionInMenu'),
              (SELECT text FROM value WHERE object = o.id AND path = 'NameInMenuToken'),
              (SELECT text FROM value WHERE object = o.id AND path = 'TypeUnitHintToken'),
              COALESCE((SELECT text FROM value WHERE object = o.id AND path = 'DescriptionUnitHintToken'),
                       (SELECT text FROM value WHERE object = o.id AND path = 'LongDescriptionUnitHintToken'))
            FROM object o WHERE o.class IN ({marks}) AND o.shadow = 0 AND o.export IS NOT NULL
            ORDER BY o.address""", list(classes)).fetchall()
        return [{"address": a, "class": c, "nation": int(n or 0), "factory": None if f is None else int(f),
                 "slot": None if s is None else int(s), "key": k, "type_key": t, "desc_key": d}
                for a, c, n, f, s, k, t, d in rows]

    def flag_sets(self, prop: str = "InitialFlagSet") -> list[dict]:
        """Every number the named objects' `prop` lists hold (a unit's flags): [{flag, count, examples}], by number;
        `count` named objects have it, `examples` are the first three of them."""
        per: dict[int, set] = defaultdict(set)
        for num, address in self.db.execute("""SELECT v.num, o.address FROM value v JOIN object o ON o.id = v.object
                                               WHERE substr(v.path, 1, ?) = ? AND o.shadow = 0
                                               AND o.export IS NOT NULL""", (len(prop) + 1, prop + "[")):
            if num is not None:
                per[int(num)].add(address)
        return [{"flag": f, "count": len(a), "examples": sorted(a)[:3]} for f, a in sorted(per.items())]

    def ammunition(self) -> list[dict]:
        """Every named ammunition (TAmmunition): its address, id, name and kind keys (texts), and the named units whose
        weapons fire it, by address."""
        rows = self.db.execute("""SELECT o.id, o.address,
              (SELECT num FROM value WHERE object = o.id AND path = 'AmmunitionId'),
              (SELECT text FROM value WHERE object = o.id AND path = 'Name'),
              (SELECT text FROM value WHERE object = o.id AND path = 'TypeName')
            FROM object o WHERE o.class = 'TAmmunition' AND o.shadow = 0 AND o.export IS NOT NULL
            ORDER BY o.address""").fetchall()
        users: dict[int, set] = defaultdict(set)
        for dst, owner in self.db.execute("""SELECT r.dst, n.address FROM ref r JOIN object d ON d.id = r.dst
                                             JOIN owner w ON w.object = r.src JOIN object n ON n.id = w.owner
                                             WHERE d.class = 'TAmmunition' AND n.shadow = 0"""):
            users[dst].add(owner)
        return [{"address": a, "id": None if i is None else int(i), "name_key": k, "type_key": t,
                 "users": sorted(users[oid])} for oid, a, i, k, t in rows]

    def prop_types(self, cls: str) -> dict:
        """Property -> the value type objects of `cls` use for it ("int32", "float32", "list"…), the most common one."""
        return dict(self.db.execute("SELECT prop, type FROM prop_seen WHERE class = ? ORDER BY count, type", (cls,)))

    def names(self, keys, lang: str) -> dict:
        """Key name -> its text in one language, preferring the unit-name dictionary (baseunite). The game's texts keep
        some characters as HTML entities ("ARTILLERY &amp; ANTI-AIR BASE"): they come back as the characters."""
        keys = [k for k in set(keys) if k]
        out = {}
        for start in range(0, len(keys), 500):
            chunk = keys[start:start + 500]
            marks = ",".join("?" * len(chunk))
            for name, text in self.db.execute(f"""SELECT name, text FROM text WHERE lang = ? AND name IN ({marks})
                                                  ORDER BY dictionary = 'baseunite'""", [lang] + chunk):
                out[name] = html.unescape(text) if text and "&" in text else text
        return out

    def _step(self, src: int, path: str) -> str:
        """How an address writes the step `path` out of object `src`: a list item becomes a class selector when its
        class is the only one of its kind in that list (and the list holds no imports), like the index's addresses."""
        m = re.fullmatch(r"(.*)\[(\d+)\]", path)
        if not m:
            return path
        base = m.group(1)
        items = [(p, kind, dst) for p, kind, dst in self.db.execute(
            "SELECT path, kind, dst FROM ref WHERE src = ? AND path LIKE ?", (src, base + "[%"))
            if re.fullmatch(re.escape(base) + r"\[\d+\]", p)]
        if any(kind != "object" for _p, kind, _d in items):
            return path
        classes = {p: self.db.execute("SELECT class FROM object WHERE id = ?", (d,)).fetchone()[0] for p, _k, d in items}
        return f"{base}[class={classes[path]}]" if list(classes.values()).count(classes[path]) == 1 else path

    def path_to(self, root: str, part: str) -> str | None:
        """The shortest path from the named object `root` to `part`, one of its unnamed parts (through unnamed objects
        only), as an address writes it after `root:`. None if `root` doesn't reach it. A part several units share has
        one address (through its first owner); this gives the way in through any of the others."""
        start, goal = self._object(root), self._object(part)
        seen, queue = {start}, deque([(start, "")])
        while queue:
            oid, path = queue.popleft()
            for p, dst in self.db.execute("SELECT path, dst FROM ref WHERE src = ? AND kind = 'object' ORDER BY rowid",
                                          (oid,)).fetchall():
                if dst in seen or self.db.execute("SELECT export FROM object WHERE id = ?", (dst,)).fetchone()[0]:
                    continue
                step = self._step(oid, p)
                full = f"{path}.{step}" if path else step
                if dst == goal:
                    return full
                seen.add(dst)
                queue.append((dst, full))
        return None

    def clone_plan(self, address: str) -> dict:
        """What cloning this object would do (MOD_FORMAT §10.5): its owned parts are copied, parts other named
        objects reach too are shared, named objects and imports stay references."""
        root = self._object(address)
        copied, shared, named, seen, stack = [], [], [], {root}, [root]
        while stack:
            oid = stack.pop()
            for dst, kind, target in self.db.execute("SELECT dst, kind, target FROM ref WHERE src = ? ORDER BY rowid",
                                                     (oid,)).fetchall():
                if kind == "import":
                    named.append(target)
                    continue
                if kind != "object" or dst in seen:
                    continue
                seen.add(dst)
                a, export, is_shared = self.db.execute("SELECT address, export, shared FROM object WHERE id = ?",
                                                       (dst,)).fetchone()
                if export:
                    named.append(a)
                elif is_shared:
                    shared.append(a)
                else:
                    copied.append(a)
                    stack.append(dst)
        return {"copied": copied, "shared": shared, "references": sorted(set(named))}

    def report(self) -> dict:
        """The M1 checks: counts, repeated game paths, shared objects, last-resort addresses, imports resolved."""
        meta = self.meta()
        repeated = self.db.execute("""SELECT game_path, COUNT(*) FROM file GROUP BY game_path HAVING COUNT(*) > 1
                                      ORDER BY COUNT(*) DESC, game_path LIMIT 20""").fetchall()
        return {"counts": {k[len("count: "):]: v for k, v in meta.items() if k.startswith("count: ")},
                "repeated paths": repeated, "seconds": meta.get("seconds"), "build": meta.get("build")}
