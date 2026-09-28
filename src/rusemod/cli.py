"""`ruse`: the command-line tool.

  ruse detect                          find R.U.S.E. through Steam and show its version
  ruse ls <pack> [filter]              list the files in a pack
  ruse names <pack> [filter]           list the named objects in a pack's data files
  ruse dump <pack> <file> [filter]     show one data file as text
  ruse extract <pack> <filter> [--out DIR]   copy files out of a pack (default folder: extracted/)
  ruse build <mod>... [--pack P] [--out FILE|DIR] [--instance DIR]   build mods into packs or a modded copy

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

from .build import BuildError, build_and_write, find_pack, load_mod
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


def cmd_build(args) -> int:
    try:
        mods = [load_mod(m) for m in args.mods]
    except (BuildError, RndfError, OSError) as exc:
        raise UserError(str(exc)) from None
    pack = str(_find_pack(args.pack, args))
    game = _game_dir(args)
    try:
        result = build_and_write(game, mods, pack=pack, out=Path(args.out) if args.out else None,
                                 instance=Path(args.instance) if args.instance else None, show_all=args.all)
    except BuildError as exc:
        raise UserError(str(exc)) from None
    return 2 if result.errors else 0


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
    p = sub.add_parser("build", help="build mods into a rebuilt pack or a modded copy of the game")
    p.add_argument("mods", nargs="+", help="mod folders (with mod.toml) or single .rndf files")
    p.add_argument("--pack", default="ZZ_GladPatchableWin.dat", help="the pack the mods change (default: the unit data)")
    p.add_argument("--out", help="write the rebuilt pack to this .dat file, or every rebuilt pack into this folder")
    p.add_argument("--instance", help="build a modded copy of the game in this folder (never the Steam install)")
    p.add_argument("--all", action="store_true", help="show every note, without collapsing similar ones")
    p.set_defaults(fn=cmd_build)
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
