"""`ruse`: the command-line tool.

  ruse detect                          find R.U.S.E. through Steam and show its version
  ruse ls <pack> [filter]              list the files in a pack
  ruse names <pack> [filter]           list the named objects in a pack's data files
  ruse dump <pack> <file> [filter]     show one data file as text
  ruse extract <pack> <filter> [--out DIR]   copy files out of a pack (default folder: extracted/)
  ruse export-model <name>... [--out DIR]    game models as .glb files for Blender (default: extracted/models)
  ruse import-model <file> --like <model> --unit <name> [--mod DIR]   a .3ds/.glb as a new unit's own model
  ruse build <mod>... [--pack P] [--out FILE|DIR] [--instance DIR]   build mods into packs or a modded copy
  ruse index build                     index the whole game (once per game build; about a minute)
  ruse index find|show|where|filter|texts|clone|report ...   ask the index (see `ruse index -h`)

A pack can be a path, or just its name (`ZZ_GladPatchableWin.dat`), found in the game folder. Packs inside packs are
reached with `!`: `ZZ_Win.dat!eugen.ipk`. Nothing here ever writes into the game folder.

Run it as `py -3 -m rusemod <command>` (with PYTHONPATH=src), or as `ruse <command>` after `pip install -e .`.
"""
from __future__ import annotations

import argparse
import contextlib
import os
import sys
from pathlib import Path

from .build import BuildError, build_and_write, build_cache, find_pack, load_mod
from .build import report_lines  # noqa: F401  (kept here for callers of rusemod.cli.report_lines)
from .edat import Edat
from .ndf import Ndf
from .rndf import RndfError
from .steam import find_game
from .text import NdfText


class UserError(Exception):
    """A problem the user can fix; printed without a traceback."""


def _game_dir(args) -> Path:
    if args.game:
        return Path(args.game)
    if os.environ.get("RUSE_GAME"):
        return Path(os.environ["RUSE_GAME"])
    found = find_game()
    if not found:
        # not a game rule: the game or one of its files isn't found
        raise UserError("Couldn't find R.U.S.E. through Steam. Pass the game folder with --game.")
    return found["game_dir"]


def _find_pack(name: str, args) -> Path:
    p = Path(name)
    if p.is_file():
        return p
    game = _game_dir(args)
    found = find_pack(game, name)
    if found is None:
        raise UserError(f"No pack called {name!r} in {game}.")
    return found


@contextlib.contextmanager
def open_pack(spec: str, args):
    parts = spec.split("!")
    with Edat.open(str(_find_pack(parts[0], args))) as arc:
        for inner in parts[1:]:
            arc = Edat(bytes(arc.read(_member(arc, inner, parts[0]))))
        yield arc


def _member(arc: Edat, suffix: str, where: str):
    try:
        return arc.find(suffix)
    except KeyError:
        raise UserError(f"No file ending in {suffix!r} in {where}. Try: ruse ls {where} <part of the name>") from None


def cmd_detect(args) -> int:
    found = find_game()
    if not found:
        print("R.U.S.E. not found through Steam. Is it installed? You can also pass --game <folder>.")
        return 1
    print(f"game folder:    {found['game_dir']}")
    print(f"Steam build id: {found['build_id']}")
    print(f"branch:         {found['branch']}")
    print(f"data revision:  {', '.join(found['data_revisions']) or '(none found)'}")
    return 0


def cmd_ls(args) -> int:
    with open_pack(args.pack, args) as arc:
        want = (args.filter or "").lower()
        rows = [e for e in arc.entries if want in e.path.lower()]
        for e in sorted(rows, key=lambda e: e.path.lower()):
            print(f"{e.size:>12,}  {e.path}")
        print(f"{len(rows)} file(s)")
    return 0


def _is_ndf(data) -> bool:
    return data[:4] == b"EUG0" and data[8:12] == b"CNDF"


def cmd_names(args) -> int:
    want = (args.filter or "").lower()
    n = 0
    with open_pack(args.pack, args) as arc:
        for e in arc.entries:
            start = arc.data_offset + e.offset
            if not _is_ndf(arc.raw[start:start + 12]):  # peek first: big packs hold thousands of other files
                continue
            ndf = Ndf(bytes(arc.read(e)))
            for oi, path in sorted(ndf.exports.items(), key=lambda kv: kv[1].lower()):
                if want in path.lower():
                    print(f"{path}    {ndf.classes[ndf.objects[oi].cls]}    ({e.path})")
                    n += 1
    print(f"{n} named object(s)")
    return 0


def cmd_dump(args) -> int:
    with open_pack(args.pack, args) as arc:
        e = _member(arc, args.file, args.pack)
        data = bytes(arc.read(e))
        if not _is_ndf(data):
            raise UserError(f"{e.path} isn't an NDF data file.")
        ndf = Ndf(data)
    print(f"// {args.pack}!{e.path}")
    print(f"// {len(ndf.objects):,} objects, {len(ndf.classes)} classes, {len(ndf.exports):,} named")
    print()
    for line in NdfText(ndf).lines(args.filter):
        print(line)
    return 0


def cmd_extract(args) -> int:
    out = Path(args.out).resolve()
    pack = _find_pack(args.pack.split("!")[0], args).resolve()
    protected = [a for a in pack.parents if (a / "RUSE.exe").is_file()]
    with contextlib.suppress(UserError):
        protected.append(_game_dir(args).resolve())
    for game in protected:
        if out == game or game in out.parents:
            # not a game rule: we never write into the game folder
            raise UserError(f"Refusing to write into the game folder ({game}). Pick another --out folder.")
    want = args.filter.lower()
    n = 0
    with open_pack(args.pack, args) as arc:
        for e in arc.entries:
            if want not in e.path.lower():
                continue
            dst = out.joinpath(*e.path.split("\\"))
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(bytes(arc.read(e)))
            n += 1
    print(f"extracted {n} file(s) to {out}")
    return 0


def cmd_export_model(args) -> int:
    from . import gltf
    from .models import Library
    out = Path(args.out).resolve()
    game = _game_dir(args).resolve()
    if out == game or game in out.parents:
        # not a game rule: we never write into the game folder
        raise UserError(f"Refusing to write into the game folder ({game}). Pick another --out folder.")
    lib = Library(game)
    try:
        names = []
        for want in args.names:
            w = want.lower().replace("/", "\\")
            found = sorted(n for n in lib.where if w in n and n.endswith("lod0.ase2ndfbin")
                           and "_lodmedium" not in n and (args.all or "_dest" not in n))
            if not found:
                print(f"no model matches {want!r}")
            names += [n for n in found if n not in names]
        if not names:
            return 1
        written = gltf.export(lib, names, out, side=args.size)
        for s in written:
            bones = f", {len(s['bones'])} bones" if "bones" in s else ""
            print(f"{s['file']}: {s['draw_calls']} part(s), {s['vertices']:,} vertices, {s['triangles']:,} triangles"
                  f"{bones}; pictures: {', '.join(s['pictures'])}")
    finally:
        lib.close()
    if args.open:
        from .blender import DOWNLOAD, find_blender, open_models
        blender = find_blender(args.blender)
        if blender is None:
            # not a game rule: Blender isn't found on this PC
            raise UserError(f"Couldn't find Blender (free: {DOWNLOAD}). Pass its blender.exe with --blender, "
                            f"or set RUSE_BLENDER.")
        open_models(blender, [s["file"] for s in written])
        print(f"opening in Blender: {blender}")
    return 0


def cmd_import_model(args) -> int:
    from .models import Library
    from .modelin import ModelError
    from .unitmodel import MODELS, import_model
    game = _game_dir(args).resolve()
    lib = Library(game)
    try:
        want = args.like.lower().replace("/", "\\")
        found = sorted(n for n in lib.where if want in n and n.endswith("lod0.ase2ndfbin") and "_dest" not in n
                       and "_lodmedium" not in n)
    finally:
        lib.close()
    exact = [n for n in found if n.rsplit("\\", 1)[-1] == want or n == want]
    if len(exact) == 1:
        found = exact
    if len(found) != 1:
        print(f"{len(found)} models match {args.like!r}" + (": " + ", ".join(found[:12]) if found else "")
              + "; name one (export-model lists them too)")
        return 1
    out = Path(args.out) if args.out else Path(args.mod) / MODELS / f"{args.unit}.glb"
    if game == out.resolve() or game in out.resolve().parents:
        # not a game rule: we never write into the game folder
        raise UserError(f"Refusing to write into the game folder ({game}).")
    try:
        r = import_model(game, found[0], Path(args.file), out, size=args.size, side=args.side, pictures=args.pictures)
    except (ModelError, OSError, ValueError) as exc:
        raise UserError(str(exc)) from None
    print(f"{out}: {r['vertices']:,} points, {r['triangles']:,} triangles in {r['draws']} part(s), fitted to "
          f"{r['like']} (facing {'+' if r['facing'][1] > 0 else '-'}{r['facing'][0]}, scale {r['scale']:.3f})")
    for name, role in r["parts"].items():
        print(f"  {name}: {role}")
    print("  pictures: " + ", ".join(f"{n} {w}x{h}" for n, w, h in r["pictures"]))
    print(f"  normals: {r.get('normals', '?')}; alpha (side colour / shine): "
          + ", ".join(f"{n} {a}" for n, a in (r.get("alpha") or {}).items()))
    for note in r.get("notes") or ():
        print(f"  NOTE: {note}")
    if r.get("missing"):
        print("  NOT FOUND (a flat colour instead; point --pictures at their folder): " + ", ".join(r["missing"]))
    return 0


def cmd_build(args) -> int:
    try:
        mods = [load_mod(m) for m in args.mods]
    except (BuildError, RndfError, OSError) as exc:
        raise UserError(str(exc)) from None
    pack = str(_find_pack(args.pack, args))
    game = _game_dir(args)
    from .instance import InstanceError
    try:
        result = build_and_write(game, mods, pack=pack, out=Path(args.out) if args.out else None,
                                 instance=Path(args.instance) if args.instance else None, show_all=args.all,
                                 cache=build_cache())
    except (BuildError, InstanceError) as exc:  # (a game still running from the copy is said plainly, not dumped)
        raise UserError(str(exc)) from None
    return 2 if result.errors else 0


_OPS = {"gt": ">", "ge": ">=", "lt": "<", "le": "<=", "eq": "=", "ne": "!="}


def _number(x) -> str:
    return str(int(x)) if x == int(x) else repr(x)


def cmd_index(args) -> int:
    from .index import Index, build_index, default_path
    path = Path(args.index) if args.index else None
    if args.action == "build":
        game = _game_dir(args)
        print(f"indexing {game} (read-only)")
        built = build_index(game, path, say=print)
        ix = Index(built)
        report = ix.report()
        ix.close()
        print(f"index: {built}  ({report['seconds']} s)")
        for key, value in sorted(report["counts"].items()):
            print(f"  {key}: {value}")
        for game_path, n in report["repeated paths"]:
            print(f"  in {n} packs: {game_path}")
        return 0
    try:
        ix = Index(path or default_path(_game_dir(args)))
    except FileNotFoundError as exc:
        raise UserError(str(exc)) from None
    try:
        if args.action == "find":
            for address, cls in ix.find(args.words, limit=args.limit):
                print(f"{address}  ({cls})")
        elif args.action == "show":
            try:
                o = ix.show(args.address)
            except KeyError as exc:
                raise UserError(str(exc.args[0])) from None
            print(f"{o['address']}  ({o['class']})")
            print(f"file: {o['file']}  object #{o['index']}")
            if not o["stable"]:
                print("address: last resort (no named object reaches it)")
            if o["owners"]:
                print(("shared by: " if o["shared"] else "owner: ") + ", ".join(o["owners"]))
            for vpath, num, text in o["values"]:
                print(f"  {vpath} = {_number(num) if num is not None else text}")
            for address, rpath in ix.used_by(o["address"]):
                print(f"used by: {address}  ({rpath})")
            for rpath, kind, what in ix.uses(o["address"]):
                print(f"uses: {rpath} -> {what}  ({kind})")
        elif args.action == "where":
            for address, rpath, target in ix.where_file(args.fragment, limit=args.limit):
                print(f"{address}  {rpath} -> {target}")
        elif args.action == "filter":
            op = _OPS.get(args.op, args.op)
            try:
                rows = ix.filter(args.cls, args.path, op, float(args.number), limit=args.limit)
            except ValueError as exc:
                raise UserError(f"{exc} (use < <= = >= > != or gt ge eq le lt ne)") from None
            for address, num in rows:
                print(f"{address}  {_number(num)}")
        elif args.action == "texts":
            for name, dictionary, text in ix.texts(args.words, lang=args.lang, limit=args.limit):
                print(f"{name}  ({dictionary})  {text}")
        elif args.action == "clone":
            try:
                plan = ix.clone_plan(args.address)
            except KeyError as exc:
                raise UserError(str(exc.args[0])) from None
            print("copied (the clone gets its own): " + (", ".join(plan["copied"]) or "nothing"))
            print("shared (stays shared): " + (", ".join(plan["shared"]) or "nothing"))
            print("references (keep pointing at the originals): " + (", ".join(plan["references"]) or "nothing"))
        elif args.action == "report":
            report = ix.report()
            print(f"build {report['build']}, indexed in {report['seconds']} s")
            for key, value in sorted(report["counts"].items()):
                print(f"  {key}: {value}")
            for game_path, n in report["repeated paths"]:
                print(f"  in {n} packs: {game_path}")
    finally:
        ix.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ruse", description="Tools for R.U.S.E. game data. Nothing here modifies the game.")
    ap.add_argument("--game", help="the R.U.S.E. folder (default: found through Steam, or $RUSE_GAME)")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("detect", help="find R.U.S.E. through Steam").set_defaults(fn=cmd_detect)
    p = sub.add_parser("ls", help="list the files in a pack")
    p.add_argument("pack")
    p.add_argument("filter", nargs="?")
    p.set_defaults(fn=cmd_ls)
    p = sub.add_parser("names", help="list named objects in a pack's data files")
    p.add_argument("pack")
    p.add_argument("filter", nargs="?")
    p.set_defaults(fn=cmd_names)
    p = sub.add_parser("dump", help="show one data file as text")
    p.add_argument("pack")
    p.add_argument("file", help="the end of the file's path inside the pack, e.g. everything.cpp.gladndfbin")
    p.add_argument("filter", nargs="?", help="only objects whose name or class contains this")
    p.set_defaults(fn=cmd_dump)
    p = sub.add_parser("extract", help="copy files out of a pack")
    p.add_argument("pack")
    p.add_argument("filter", help="part of the file path, e.g. gfx\\\\everything")
    p.add_argument("--out", default="extracted", help="where to put them (default: extracted/, ignored by git)")
    p.set_defaults(fn=cmd_extract)
    p = sub.add_parser("export-model", help="write game models as .glb files for Blender (with their pictures)")
    p.add_argument("names", nargs="+", help="part of a model's path, e.g. us_m4_sherman or ger_panzergrenadier")
    p.add_argument("--out", default="extracted/models", help="where to put them (default: extracted/models, "
                   "ignored by git: the models are the game's)")
    p.add_argument("--size", type=int, default=2048, help="largest texture side to export (default 2048)")
    p.add_argument("--all", action="store_true", help="also the destroyed versions (_dest)")
    p.add_argument("--open", action="store_true", help="then open them in Blender, textured")
    p.add_argument("--blender", help="Blender's blender.exe (default: $RUSE_BLENDER, the PATH or Program Files)")
    p.set_defaults(fn=cmd_export_model)
    p = sub.add_parser("import-model", help="fit a .3ds or .glb model to a unit, as a new unit's own model in a mod")
    p.add_argument("file", help="the model: .3ds (its .tga or .png pictures beside it) or .glb (pictures inside)")
    p.add_argument("--like", required=True, help="the model of the unit the new one copies (part of its path, e.g. "
                   "coc_shermanm4_tir)")
    p.add_argument("--unit", required=True, help="the new unit's name, e.g. Descriptor_Unit_R2_M1_Abrams")
    p.add_argument("--mod", default=".", help="the mod folder: it goes to files/models/<unit>.glb there")
    p.add_argument("--out", help="write the .glb here instead")
    p.add_argument("--size", type=float, default=1.0, help="its length over the copied unit's (default 1: as long)")
    p.add_argument("--side", type=int, default=1024, help="largest picture side (default 1024, as the game's)")
    p.add_argument("--pictures", help="where a .3ds's pictures are (default: beside it, then one folder up)")
    p.set_defaults(fn=cmd_import_model)
    p = sub.add_parser("build", help="build mods into a rebuilt pack or a modded copy of the game")
    p.add_argument("mods", nargs="+", help="mod folders (with mod.toml), .rmod files, or single .rndf files")
    p.add_argument("--pack", default="ZZ_GladPatchableWin.dat", help="the pack the mods change (default: the unit data)")
    p.add_argument("--out", help="write the rebuilt pack to this .dat file, or every rebuilt pack into this folder")
    p.add_argument("--instance", help="build a modded copy of the game in this folder (never the Steam install)")
    p.add_argument("--all", action="store_true", help="show every note, without collapsing similar ones")
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser("index", help="the game index: find anything in the game data, and where it's used")
    p.add_argument("--index", help="the index file (default: the one for this game build, in the platform folder)")
    p.set_defaults(fn=cmd_index)
    isub = p.add_subparsers(dest="action", required=True)
    isub.add_parser("build", help="index the whole game (read-only; about a minute)")
    q = isub.add_parser("find", help="objects whose address or class contains these words")
    q.add_argument("words")
    q = isub.add_parser("show", help="one object: its values, owners, what uses it and what it uses")
    q.add_argument("address", help="e.g. $/GFX/Everything/Descriptor_Unit_M4_Sherman")
    q = isub.add_parser("where", help="the data that mentions a file path")
    q.add_argument("fragment", help="part of the path, e.g. sherman.tgv")
    q = isub.add_parser("filter", help="objects of a class whose number compares, e.g. TUniteAuSolDescriptor "
                                        "ProductionPrice[0] gt 30")
    q.add_argument("cls")
    q.add_argument("path")
    q.add_argument("op", help="gt ge eq le lt ne (or > >= = <= < !=, quoted in a Windows prompt)")
    q.add_argument("number")
    q = isub.add_parser("texts", help="game texts containing these words")
    q.add_argument("words")
    q.add_argument("--lang", default="us", help="language folder (default: us)")
    q = isub.add_parser("clone", help="what cloning an object would copy, share and keep pointing at")
    q.add_argument("address")
    isub.add_parser("report", help="counts, repeated paths, shared objects, imports resolved")
    for name in ("find", "where", "filter", "texts"):
        isub.choices[name].add_argument("--limit", type=int, default=100, help="at most this many (default 100)")
    return ap


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except UserError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
