r"""Rebuild a RUSE-Mod-Manager mod (`.rmod`, a JSON file) as a mod of ours: mod.toml, src/<id>.rndf, text/*.csv and
a README that says what could not be rebuilt (docs/MOD_FORMAT.md §13). Our own reader of the format, written from
the files themselves; RUSE-Mod-Manager's code is not used.

What carries over, and how (MOD_FORMAT §4):
  match by a property (ClassNameForDebug, AmmunitionId, TrackingId, PackName)  ->  patch @TClass[Prop=value]
  match every object of a class ({})                                          ->  patch every TClass
  match by an anchor (a named object plus steps into it)                      ->  patch shared @[Prop='v']:steps
  create                                                                      ->  Name is TClass ( ... )
  delete_props                                                                ->  delete Prop
  references by anchor or by debug name; `$ref` to the mod's own objects      ->  @[...]:path, ~/Name
  loc_patches                                                                 ->  text/<dictionary>.csv
    (LocHash values are the game's 64-bit text keys written byte by byte; they decode to names such as N_UNI_15)
What does not: objects matched by their position in the file (`_index`, `inst`), whole files inside the mod
(`file_patches`: music, videos, compiled scripts, scenarios, icons) and terrain layers (`sdb_patches`). Those are
listed in the README, and the statements stay in the .rndf as comments, so a session with the game can finish them.
A few mods have recipes below (a flag that is added or removed, a copy instead of a from-scratch unit, a path for
an object the original matched by position); every recipe is an assumption to check in-game, and says so.

  py -3 tools\rmod_to_mod.py <file.rmod> [more .rmod files] [--out mods]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod.dic import key_to_name  # noqa: E402

LANG_FOLDERS = ("us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")
UNIT_PATH = "WeaponDescriptor.TurretDescriptorList[0].MountedWeaponDescriptorList[0]"  # a unit's first gun

# Per-mod recipes, by the original mod id. Each one is written down in the README as an assumption.
RECIPES = {
    # A flag list that the original rewrote whole becomes a list edit: it composes with other mods and doesn't
    # depend on the game build's own flags. (bit, from the mod's description: 71 = all-round vision, 72 = no
    # line-of-sight check, 1 = indirect fire, 77 = never fires by reflex, 11/21/55 = keep out of forests.)
    "all-around-awareness": {"flags": ("+", [71])},
    "no-fog-of-war": {"flags": ("+", [72])},
    "indirect-fire-for-everyone": {"flags": ("+", [1])},
    "here-ill-hold-your-hand": {"flags": ("+", [77])},
    "passable-forests": {"flags": ("-", [11, 21, 55])},
    "argonne-forrest-mod": {"flags": ("+", [11, 21, 55])},
    # The same values on every object of the class, matched by position in the original: `patch every`.
    "super-aggressive-ai": {"index_as_every": ["TIAProfil"]},
    # The seven atomic cannons' first gun, which the original matched by file position (an assumption).
    "nuclear-artillery-endgame": {"index_targets": {
        "45604": f"shared @[ClassNameForDebug='Unit_Long_Tom_nuke']:{UNIT_PATH}",
        "45610": f"shared @[ClassNameForDebug='Unit_Canon_atomique_UK']:{UNIT_PATH}",
        "45613": f"shared @[ClassNameForDebug='Unit_Canon_atomique_FR']:{UNIT_PATH}",
        "45616": f"shared @[ClassNameForDebug='Unit_Canon_atomique_GER']:{UNIT_PATH}",
        "45619": f"shared @[ClassNameForDebug='Unit_Canon_atomique_ITA']:{UNIT_PATH}",
        "45622": f"shared @[ClassNameForDebug='Unit_Canon_atomique_URSS']:{UNIT_PATH}",
        "45625": f"shared @[ClassNameForDebug='Unit_Canon_atomique_JAP']:{UNIT_PATH}"}},
    # A unit the original built from scratch, borrowing most parts from one unit: a copy of that unit instead.
    "armed-factories": {"create_as_clone": {"inst_afg_unit": "@[ClassNameForDebug='Unit_Tourelle_MG_GER']"}},
    "navy-mod": {"create_as_clone": {
        f"inst_unit_unit_{ship}_{nation}": f"@[ClassNameForDebug='Unit_{ship.title()}']"
        for ship in ("destroyer", "heavy_cruiser", "battleship") for nation in ("ger", "uk", "fr", "ita", "urss", "jap")},
        # the three ships' model descriptors: the original's new units point at these same objects by position
        "index_targets": {"60218": "shared @[ClassNameForDebug='Unit_Destroyer']:GfxDescriptor",
                          "60250": "shared @[ClassNameForDebug='Unit_Battleship']:GfxDescriptor",
                          "60273": "shared @[ClassNameForDebug='Unit_Heavy_Cruiser']:GfxDescriptor"}},
}
EVERY_BY_DEFAULT = ["TTunableConstante"]  # the constants table: one object per constants file, matched by position
# What a copy already has from its source, so a create-as-clone body leaves it alone (fresh identity, MOD_FORMAT §10.5).
CLONE_KEEPS = {"DescriptorId", "TrackingId", "ClassNameForDebug"}
PLURALS = {"object changed": "objects changed", "value set": "values set", "new object": "new objects", "text": "texts",
           "deleted property": "deleted properties", "not rebuilt": "not rebuilt"}


def grouped(notes: list) -> list[str]:
    """(sentence, item) pairs -> one line per sentence, its items listed after it (at most eight, then a count)."""
    by: dict[str, list] = OrderedDict()
    for sentence, item in notes:
        items = by.setdefault(sentence, [])
        if item not in items:
            items.append(item)
    out = []
    for sentence, items in by.items():
        items = [i for i in items if i]
        tail = ""
        if items:
            tail = ": " + ", ".join(items[:8]) + (f" and {len(items) - 8} more" if len(items) > 8 else "")
        out.append(f"- {sentence}{tail}")
    return out


def counted(counts: Counter, skip=()) -> str:
    return ", ".join(f"{n} {k if n == 1 else PLURALS.get(k, k)}" for k, n in counts.items() if k not in skip)


class Unsupported(Exception):
    pass


def quote(text: str) -> str:
    if "'" not in text:
        return f"'{text}'"
    if '"' not in text:
        return f'"{text}"'
    raise Unsupported(f"a text with both kinds of quotes ({text[:30]}…)")


def ffloat(v) -> str:
    r = repr(float(v))
    if "inf" in r or "nan" in r:
        raise Unsupported(f"the number {r}")
    return r if "." in r or "e" in r else r + ".0"


def toml_str(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "") + '"'


def our_name(local_id: str, create: dict) -> str:
    """Our export name for an object the original created: Descriptor_<debug name>, else from its local id."""
    debug = (create.get("set") or {}).get("ClassNameForDebug", {})
    if isinstance(debug, dict) and debug.get("value"):
        return f"Descriptor_{debug['value']}"
    base = re.sub(r"[^A-Za-z0-9_]+", "_", re.sub(r"^inst_", "", local_id)).strip("_") or "Object"
    return "_".join(p.capitalize() if p.islower() else p for p in base.split("_"))


def lang_of(dic_path: str) -> str | None:
    m = re.search(r"/translations/([^/]+)/[^/]+\.dic$", dic_path.replace("\\", "/"))
    if m:
        return m.group(1)
    return "dev" if re.search(r"/dev/[^/]+\.dic$", dic_path.replace("\\", "/")) else None


def loc_key(h: str) -> int:
    return int.from_bytes(bytes.fromhex(h), "little")


class Rebuild:
    def __init__(self, data: dict, source_name: str):
        self.d, self.source = data, source_name
        self.orig_id = str(data.get("id", "mod"))
        self.id = re.sub(r"[^a-z0-9-]+", "-", self.orig_id.lower()).strip("-") or "mod"
        self.recipe = RECIPES.get(self.orig_id, {})
        self.notes: list[tuple[str, str]] = []   # (what happened, to whom): grouped in the README
        self.assumptions: list[tuple[str, str]] = []
        self.counts = Counter()
        self.creates = self._creates()      # local_id -> change
        self.names = {lid: our_name(lid, c) for lid, c in self.creates.items()}
        self.dropped: set[str] = set()      # local ids of creates that can't be rebuilt
        self.shipped = {Path(f.get("path", "").replace("\\", "/")).stem.lower()
                        for fp in data.get("file_patches", []) for f in fp.get("files", [])}
        self.texts, self.added = self._texts()

    # --- texts ---
    def _texts(self):
        """text/<dictionary>.csv rows, and the added text keys (hash -> row key) that LocHash values refer to."""
        tables: dict[str, OrderedDict] = {}
        added = {}
        for lp in self.d.get("loc_patches", []):
            lang = lang_of(lp.get("dic", ""))
            dictionary = lp.get("dic", "").replace("\\", "/").rsplit("/", 1)[-1][:-4]
            if lang is None or not dictionary:
                self.notes.append(("texts for a dictionary outside the language folders", f"`{lp.get('dic')}`"))
                continue
            rows = tables.setdefault(dictionary, OrderedDict())
            for e in lp.get("entries", []):
                h = e["key"]
                k = loc_key(h)
                name = key_to_name(k)
                if e.get("add"):
                    row_key = f"{self.id}.{name or h}"
                    added[h] = row_key
                    row = rows.setdefault(h, {"key": row_key, "game_key": name or "", "texts": {}})
                else:
                    row = rows.setdefault(h, {"key": f"game:{name or '0x%016X' % k}", "game_key": "", "texts": {}})
                if lang != "dev":
                    row["texts"][lang] = e["value"]
                else:
                    row["texts"].setdefault("us", e["value"])
        return tables, added

    # --- values ---
    def local(self, lid: str) -> str:
        if lid not in self.names:
            raise Unsupported(f"a reference to `{lid}`, which the original never creates")
        if lid in self.dropped:
            raise Unsupported(f"a reference to {self.names[lid]}, which couldn't be rebuilt")
        return f"~/{self.names[lid]}"

    def steps(self, steps) -> str:
        parts = []
        for step in steps:
            prop, idx = step[0], step[1:] if len(step) > 1 else []
            for i in idx:
                if not re.fullmatch(r"\[\d+\]", str(i)):
                    raise Unsupported(f"a map entry reached by its position ({prop}{i})")
            parts.append(prop + "".join(idx))
        return ".".join(parts)

    def anchor(self, a: dict) -> str:
        prop, value = a["root"]
        want = quote(str(value)) if isinstance(value, str) else str(value)
        path = self.steps(a.get("steps", []))
        return f"@[{prop}={want}]" + (f":{path}" if path else "")

    def ref(self, r) -> str:
        if not isinstance(r, dict):
            raise Unsupported(f"a reference written as {r!r}")
        if "$ref" in r:
            return self.local(r["$ref"])
        if "local_id" in r:
            return self.local(r["local_id"])
        if "anchor" in r:
            return self.anchor(r["anchor"])
        if "stable_ref" in r:
            prop, value, cls = r["stable_ref"], str(r["key_val"]), r.get("class_name") or ""
            for lid, c in self.creates.items():
                v = (c.get("set") or {}).get(prop, {})
                if isinstance(v, dict) and str(v.get("value")) == value:
                    return self.local(lid)
            return f"@{cls}[{prop}={quote(value)}]"
        if "inst" in r:
            raise Unsupported(f"a reference by file position (object #{r['inst']}, {r.get('class_name', '?')})")
        raise Unsupported(f"a reference written as {json.dumps(r)[:60]}")

    def value(self, v) -> str:
        if isinstance(v, dict) and "$ref" in v and "type" not in v:
            return self.local(v["$ref"])
        if not isinstance(v, dict) or "type" not in v:
            raise Unsupported(f"a value written as {json.dumps(v)[:60]}")
        t, val = v["type"], v.get("value")
        if t == "Float32":
            return ffloat(val)
        if t == "Int32":
            return str(int(val))
        if t == "UInt32":
            return f"uint32({int(val)})"
        if t == "Int8":
            return f"int8({int(val)})"
        if t == "Bool":
            return "true" if val else "false"
        if t == "StringRef":
            return quote(str(val))
        if t == "PathRef":
            if Path(str(val).replace("\\", "/")).stem.lower() in self.shipped:
                raise Unsupported(f"needs a file the original ships ({Path(str(val).replace(chr(92), '/')).name})")
            return f"path({quote(str(val))})"
        if t == "TransRef":
            trans = val.get("trans", "") if isinstance(val, dict) else str(val)
            if not trans.startswith("$/"):
                raise Unsupported(f"a TransRef to {trans!r}")
            return trans
        if t == "LocHash":
            if val in self.added:
                return f"loc('{self.added[val]}')"
            k = loc_key(val)
            name = key_to_name(k)
            return f"key({name})" if name else f"key(0x{k:016X})"
        if t == "ObjRef":
            return self.ref(val)
        if t.startswith("List<") and t.endswith(">"):
            inner = t[5:-1]
            items = [self.ref(x) if inner == "ObjRef" else self.value({"type": inner, "value": x}) for x in val]
            return "[" + ", ".join(items) + "]"
        if t.startswith("Map<") and t.endswith(">"):
            kt, vt = t[4:-1].split(",", 1)
            pairs = [f"({self.value({'type': kt, 'value': k})}, {self.ref(x) if vt == 'ObjRef' else self.value({'type': vt, 'value': x})})"
                     for k, x in val]
            return "MAP [ " + ", ".join(pairs) + " ]"
        raise Unsupported(f"a {t} value")

    # --- statements ---
    def body(self, sets: dict, keeps=(), flags=None) -> tuple[list[str], list[str]]:
        """Lines for a block body, and the properties that couldn't be written."""
        lines, left = [], []
        for prop, v in sets.items():
            if prop in keeps:
                continue
            if flags and prop == "InitialFlagSet":
                sign, bits = flags
                lines.append(f"InitialFlagSet {sign}= [{', '.join(f'uint32({b})' for b in bits)}]")
                continue
            try:
                lines.append(f"{prop} = {self.value(v)}")
            except Unsupported as exc:
                left.append(f"{prop}: {exc}")
        return lines, left

    def block(self, head: str, lines: list[str]) -> str:
        if len(lines) <= 3 and sum(map(len, lines)) < 80:
            return f"{head} ( {'  '.join(lines)} )"
        return f"{head}\n(\n" + "".join(f"    {ln}\n" for ln in lines) + ")"

    def comment(self, text: str) -> str:
        return "".join(f"// {ln}\n" for ln in text.splitlines())

    def kept(self, c: dict, head: str, why: str) -> str:
        """An unresolved statement, kept as comments with the original's values, for a session with the game."""
        lines, left = self.body(c.get("set") or {})
        lines += [f"{ln}  (not rebuilt)" for ln in left]
        lines += [f"delete {prop}" for prop in c.get("props", [])]
        text = f"Not rebuilt ({why}):\n{head}\n(\n" + "".join(f"    {ln}\n" for ln in lines[:60])
        if len(lines) > 60:
            text += f"    … {len(lines) - 60} more\n"
        return self.comment(text + ")")

    def target(self, c: dict, ndf: str) -> str:
        m = c.get("match") or {}
        table = c.get("table", "?")
        if not m:
            return f"every {table}"
        if "_index" in m:
            given = (self.recipe.get("index_targets") or {}).get(str(m["_index"]))
            if given:
                self.assumptions.append(("objects the original matched by their position in the file are taken to be",
                                         f"#{m['_index']} ({table}) = `{given.split(' ', 1)[-1]}`"))
                return given
            raise Unsupported(f"{table} object #{m['_index']} of {ndf.rsplit('/', 1)[-1]}, matched by its position "
                              f"in the file")
        if "anchor" in m:
            return "shared " + self.anchor(m["anchor"])
        if len(m) != 1:
            raise Unsupported(f"a match on several properties ({', '.join(m)})")
        (prop, value), = m.items()
        want = quote(str(value)) if isinstance(value, str) and not re.fullmatch(r"-?\d+", value) else str(value)
        return f"@{table}[{prop}={want}]"

    def statements(self, patch: dict) -> list[str]:
        ndf, out = patch.get("ndf", "?"), []
        changes = list(patch.get("changes", []))
        # the same values on every object of a class, matched one by one by position: one `patch every`
        every_tables = set(self.recipe.get("index_as_every", [])) | set(EVERY_BY_DEFAULT)
        for table in sorted(every_tables):
            group = [c for c in changes if c.get("action") == "patch" and c.get("table") == table
                     and "_index" in (c.get("match") or {})]
            if group and len({json.dumps(c.get("set"), sort_keys=True) for c in group}) == 1:
                first = changes.index(group[0])
                changes = [c for c in changes if c not in group]
                merged = dict(group[0], match={})
                changes.insert(first, merged)
                if table in EVERY_BY_DEFAULT:
                    self.assumptions.append((f"the {table} the original changed by position is changed in every "
                                             f"{table} object instead (the game has one per constants file)", ""))
                else:
                    self.assumptions.append((f"the {len(group)} {table} objects the original changed one by one "
                                             f"(by position) get the same values with one `patch every {table}`", ""))
        flags = self.recipe.get("flags")
        if flags:
            self.assumptions.append((f"the original rewrote each unit's whole InitialFlagSet list; here the bits "
                                     f"{', '.join(map(str, flags[1]))} are {'added to' if flags[0] == '+' else 'removed from'} "
                                     f"the list the game has", ""))
        for c in changes:
            action = c.get("action")
            try:
                if action == "patch":
                    out.append(self.patch(c, ndf, flags))
                elif action == "delete_props":
                    out.append(self.block(f"patch {self.target(c, ndf)}", [f"delete {p}" for p in c.get("props", [])]))
                    self.counts["deleted property"] += len(c.get("props", []))
                elif action == "create":
                    out.append(self.create(c))
                else:
                    raise Unsupported(f"the action {action!r}")
            except Unsupported as exc:
                if action == "create":
                    head = f"{self.names.get(c.get('local_id'), 'New')} is {c.get('table', '?')}"
                    self.notes.append((f"new objects: {exc}", head.split(" ", 1)[0]))
                else:
                    head = f"patch {c.get('table', '?')} {json.dumps(c.get('match'))}"
                    self.notes.append((f"{action} of {c.get('table', '?')}: {exc}", ""))
                self.counts["not rebuilt"] += 1
                out.append(self.kept(c, head, str(exc)))
        return out

    def patch(self, c: dict, ndf: str, flags) -> str:
        head = f"patch {self.target(c, ndf)}"
        lines, left = self.body(c.get("set") or {}, flags=flags)
        for item in left:
            prop, why = item.split(": ", 1)
            self.notes.append((f"{prop}: {why}", head.split(" ", 1)[-1]))
            lines.append(f"// not rebuilt: {item}")
        if not any(not ln.startswith("//") for ln in lines):
            raise Unsupported("none of its values can be written")
        self.counts["object changed"] += 1
        self.counts["value set"] += sum(1 for ln in lines if not ln.startswith("//"))
        return self.block(head, lines)

    def create(self, c: dict) -> str:
        lid, name = c.get("local_id", "?"), self.names.get(c.get("local_id", "?"), "New")
        source = (self.recipe.get("create_as_clone") or {}).get(lid)
        if source:
            lines, left = self.body(c.get("set") or {}, keeps=CLONE_KEEPS)
            for item in left:
                prop, why = item.split(": ", 1)
                self.notes.append((f"kept from the copied unit: {prop} (the original set {why})", name))
            self.assumptions.append((f"copies of {source} with the original's values on top, instead of units built "
                                     f"from scratch (the original borrowed most parts from that unit)", name))
            self.counts["new object"] += 1
            return self.block(f"export {name} is clone {source}", lines)
        lines, left = self.body(c.get("set") or {})
        if left:
            self.dropped.add(lid)
            raise Unsupported("; ".join(left))
        self.counts["new object"] += 1
        return self.block(f"{'export ' if c.get('top_object') else ''}{name} is {c.get('table', '?')}", lines)

    def _creates(self) -> dict:
        out = OrderedDict()
        for p in self.d.get("patches", []):
            for c in p.get("changes", []):
                if c.get("action") == "create" and c.get("local_id"):
                    out[c["local_id"]] = c
        return out

    # --- files ---
    def rndf(self) -> str:
        head = (f"// {self.d.get('name', self.id)}: rebuilt from the RUSE-Mod-Manager mod {self.source} by "
                f"tools/rmod_to_mod.py.\n// Objects are found the way the original found them (docs/MOD_FORMAT.md §4)"
                f": by debug name, ammunition id or class.\n")
        parts = []
        # creates first, in the order the original has them; their names must exist before anything refers to them
        for p in self.d.get("patches", []):
            creates = [c for c in p.get("changes", []) if c.get("action") == "create"]
            others = [c for c in p.get("changes", []) if c.get("action") != "create"]
            if not creates and not others:
                continue
            parts.append(f"\n// --- {p.get('ndf', '?')} (in {p.get('dat', '?')})\n")
            settled = False
            while not settled:  # a create that refers to a dropped one is dropped too
                before = len(self.dropped)
                notes, assumptions, counts = list(self.notes), list(self.assumptions), Counter(self.counts)
                body = self.statements(dict(p, changes=creates + others))
                settled = len(self.dropped) == before
                if not settled:
                    self.notes, self.assumptions, self.counts = notes, assumptions, counts
            parts += [s + "\n" for s in body]
        return head + "".join(parts).replace("\n\n\n", "\n\n")

    def manifest(self) -> str:
        m = self.d
        lines = [f"# Rebuilt from the RUSE-Mod-Manager mod {self.source} by tools/rmod_to_mod.py; README.md says what "
                 f"is and isn't here.", "[mod]", f'id          = "{self.id}"',
                 f"name        = {toml_str(str(m.get('name') or self.id))}",
                 f"version     = {toml_str(str(m.get('version') or '1.0.0'))}"]
        if m.get("author"):
            lines.append(f"authors     = [{toml_str(str(m['author']))}]")
        if m.get("description"):
            lines.append(f"description = {toml_str(str(m['description']))}")
        if self.added:
            lines.append(f'text_prefix = "{re.sub("[^A-Za-z0-9]", "", self.id.upper())[:2] or "MD"}"')
        if m.get("game_version"):
            lines += ["", "[game]", f"builds = [{toml_str(str(m['game_version']))}]  # the build the original was made on"]
        lines += ["", "[origin]", 'format       = "ruse-mod/v1"', f"file         = {toml_str(self.source)}",
                  f"id           = {toml_str(self.orig_id)}"]
        if m.get("game_version"):
            lines.append(f"game_version = {toml_str(str(m['game_version']))}")
        return "\n".join(lines) + "\n"

    def csvs(self) -> dict[str, str]:
        out = {}
        for dictionary, rows in self.texts.items():
            langs = [lg for lg in LANG_FOLDERS if any(lg in r["texts"] for r in rows.values())]
            same = all(len({r["texts"][lg] for lg in langs if lg in r["texts"]}) <= 1 for r in rows.values())
            langs = ["us"] if same else langs
            with_key = any(r["game_key"] for r in rows.values())
            buf = io.StringIO()
            w = csv.writer(buf, lineterminator="\n")
            w.writerow(["key"] + (["game_key"] if with_key else []) + langs)
            for r in rows.values():
                us = r["texts"].get("us") or next(iter(r["texts"].values()))
                cells = [r["key"]] + ([r["game_key"]] if with_key else [])
                cells += [us if lg == "us" else r["texts"].get(lg, "") for lg in langs]
                w.writerow(cells)
            out[f"{dictionary}.csv"] = buf.getvalue()
            self.counts["text"] += len(rows)
        return out

    def readme(self) -> str:
        m = self.d
        files = [(f["path"], len(f.get("data", "")) * 3 // 4) for fp in m.get("file_patches", []) for f in fp.get("files", [])]
        sdb = m.get("sdb_patches", [])
        lines = [f"# {m.get('name', self.id)}", ""]
        if m.get("description"):
            lines += [str(m["description"]).strip(), ""]
        made = f", made on game build {m['game_version']}" if m.get("game_version") else ""
        lines += [f"Rebuilt from the RUSE-Mod-Manager mod `{self.source}` (version {m.get('version', '?')}{made}) with "
                  f"`tools/rmod_to_mod.py`, so it builds with our engine and can go into a mod set "
                  f"(docs/MOD_FORMAT.md §13). Numbers and names are the original's.", ""]
        lines += [f"**In this mod:** {counted(self.counts, skip=('not rebuilt',)) or 'nothing could be rebuilt'}.", ""]
        if self.assumptions:
            lines += ["## Assumptions to check in-game", ""] + grouped(self.assumptions) + [""]
        left = grouped(self.notes)
        if files:
            left.append(f"{len(files)} whole file(s) inside the original (mods of ours hold no game files or compiled "
                        f"scripts): " + ", ".join(f"`{p}` ({n // 1024} KB)" for p, n in files[:6])
                        + (", …" if len(files) > 6 else ""))
        if sdb:
            left.append(f"terrain layers for {len(sdb)} map(s) (`sdb_patches`): that part of the format waits for the "
                        f"terrain work (PLAN.md §7 MT)")
        if left:
            lines += ["## Not rebuilt", ""] + [n if n.startswith("- ") else f"- {n}" for n in left]
            if self.counts.get("not rebuilt"):
                lines += ["", "Statements that could not be rebuilt stay in the `.rndf` file as comments, with the "
                          "original's values, so a session with the game can finish them."]
            lines.append("")
        else:
            lines += ["Everything in the original is here.", ""]
        return "\n".join(lines)

    def write(self, out_root: Path) -> Path:
        folder = out_root / self.id
        (folder / "src").mkdir(parents=True, exist_ok=True)
        rndf = self.rndf()
        csvs = self.csvs()
        (folder / "src" / f"{self.id}.rndf").write_text(rndf, encoding="utf-8")
        if csvs:
            (folder / "text").mkdir(exist_ok=True)
            for name, text in csvs.items():
                (folder / "text" / name).write_text(text, encoding="utf-8")
        (folder / "mod.toml").write_text(self.manifest(), encoding="utf-8")
        (folder / "README.md").write_text(self.readme(), encoding="utf-8")
        return folder


def rebuild(path: Path, out_root: Path) -> Rebuild:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("$schema") not in (None, "ruse-mod/v1"):
        raise SystemExit(f"{path}: unknown schema {data.get('$schema')!r}")
    r = Rebuild(data, re.sub(r"^[0-9a-f]{8}-", "", path.name))
    r.write(out_root)
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", help=".rmod files")
    ap.add_argument("--out", default="mods", help="where the mod folders go (default: mods/)")
    args = ap.parse_args(argv)
    for f in args.files:
        r = rebuild(Path(f), Path(args.out))
        left = len(grouped(r.notes))
        print(f"{r.id}: {counted(r.counts)}" + (f"; {left} note(s)" if left else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
