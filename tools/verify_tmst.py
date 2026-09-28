r"""Verify the terrain tile reader/writer (rusemod.tmst) against every map pack (READ-ONLY on the game).

For output\highdef.* and output\lowdef.* of every Maps\PC\DataMap*_v09.dat:
  A. layout: header fields, key separators, zero padding, every tile a one-mip DXT1 TGV with a TGU1 payload,
     overview tile size = next power of two of 64 px per cell.
  B. unchanged rebuild of index and store is byte-identical.
  C. edited rebuild (finest top-left tile and the overview swapped for ZIPO checkerboards, of other sizes)
     reads back: the new tiles are there, every other tile is byte-identical, size fields match.
  D. placement cross-check: the store keeps each cell's tiles together and walks the cells column by column.
With --packs SCRATCH_DIR, also:
  E. whole map pack streamed through Edat.write_to into SCRATCH_DIR is byte-identical (file deleted after).
  F. an edited pack (C's tiles) reopens: new tiles present, every other member byte-identical (deleted after).
With --make-test MAP OUT [checker|mirror], writes a test pack for the game (see make_test below).

Usage:  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_tmst.py [--packs DIR] [--only Name] [--make-test ...]
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat  # noqa: E402
from rusemod.tmst import (MAGENTA, TAGS, TILE, YELLOW, Tgv, Tmst, checker_tile, dxt1_checker,  # noqa: E402
                          rgb565, zipo_tile, zipo_unpack)

MAPS = r"D:\Steam\steamapps\common\R.U.S.E\Maps\PC"
LODS = ("highdef", "lowdef")


def pow2(n):
    return 1 << (n - 1).bit_length()


def check_layout(t):
    idx, ch = t.index, t.chunk
    problems = []
    if idx[0x40:0x4C] != TAGS or t.table_offset != 0x4C:
        problems.append("tags/table offset")
    if struct.unpack_from("<5I", idx, 0x2C) != (0, 0x44, 0, 0x48, 0):
        problems.append(f"header 0x2C..0x3F = {struct.unpack_from('<5I', idx, 0x2C)}")
    sep = struct.pack("<I", t.key)
    if ch[:4] != sep:
        problems.append("store does not start with the key")
    pos = 4
    for tile in sorted(t.tiles, key=lambda x: x.offset):
        if tile.offset != pos or ch[tile.offset + tile.size:tile.offset + tile.size + 4] != sep:
            problems.append(f"record {tile.index} not followed by the key")
            break
        pos = tile.offset + tile.size + 4
        tex = t.texture(tile)
        end = tex.mips[0][0] + tex.mips[0][1]
        if (tex.format, len(tex.mips), tex.mips[0][0], tex.codec, tex.flag) != ("DXT1", 1, 0x28, "TGU1", 1):
            problems.append(f"record {tile.index}: {tex.format} {tex.mips} {tex.codec}")
        if not 0 <= tile.size - end < 4 or t.chunk[tile.offset + end:tile.offset + tile.size].strip(b"\0"):
            problems.append(f"record {tile.index}: padding")
        px = 64 if t.lod == "highdef" else 128  # the overview is the same picture in both sets
        want = (TILE, TILE) if tile.level < t.depth else (pow2(px * t.grid_w), pow2(px * t.grid_h))
        if (tex.width, tex.height) != want or (tex.width2, tex.height2) != want:
            problems.append(f"record {tile.index}: {tex.width}x{tex.height}, expected {want}")
    if pos != len(ch):
        problems.append("store has trailing bytes")
    return problems


def storage_walk(t):
    """True when the store walks the cells column by column (x outer, y inner), overview last. Tiles of a cell
    are stored together except for stragglers: a tile may land at most one cell late (parallel baking)."""
    order = sorted(t.tiles, key=lambda x: x.offset)
    if order[-1].level != t.depth:
        return False
    first, top = [], -1
    for tile in order[:-1]:
        x0, y0, _, _ = t.area(tile)
        rank = int(x0) * t.grid_h + int(y0)
        if rank < top - 1:
            return False
        if rank > top:
            first.append(rank)
            top = rank
    return first == list(range(t.grid_w * t.grid_h))


def edit(t):
    small = checker_tile()
    over = t.tiles[0]
    ow, oh = t.texture(over).width, t.texture(over).height
    big = zipo_tile(dxt1_checker(ow, oh, 32, rgb565(255, 255, 255), rgb565(0, 0, 0)), ow, oh)
    return {t.tile(0, 0, 0).index: small, over.index: big}


def check_edit(t, replace):
    idx, ch = t.rebuild(replace)
    n = Tmst(idx, ch)
    ok = len(n.tiles) == len(t.tiles) and n.key == t.key
    for a, b in zip(t.tiles, n.tiles):
        got = n.read(b)
        if a.index in replace:
            want = replace[a.index]
            ok &= got[:len(want)] == want and not got[len(want):].strip(b"\0") and len(got) % 4 == 0
            ok &= zipo_unpack(Tgv(got).payload()) == zipo_unpack(Tgv(want).payload())
        else:
            ok &= got == t.read(a) and (a.level, a.x, a.y) == (b.level, b.x, b.y)
    saved = sum(t.tiles[i].size - len(n.read(n.tiles[i])) for i in replace)
    ok &= len(ch) == len(t.chunk) - saved
    return ok, len(ch)


def compare_files(a, b, block=1 << 24):
    """Byte-for-byte comparison, streamed."""
    if os.path.getsize(a) != os.path.getsize(b):
        return False
    with open(a, "rb") as fa, open(b, "rb") as fb:
        while True:
            x, y = fa.read(block), fb.read(block)
            if x != y:
                return False
            if not x:
                return True


def make_test(pack_path, out_path, variant="checker"):
    """checker: every tile of both sets becomes a ZIPO checkerboard, colours by level (highdef: L0 magenta/yellow,
    L1 cyan/red, L2 green/blue, overview white/black; lowdef: every level orange/purple).
    mirror: every tile takes the original (TGU1) bytes of its left-right mirror twin at the same level, so the
    ground texture no longer matches the relief; tests the writer alone with the game's own codec."""
    palette = {0: (MAGENTA, YELLOW), 1: (rgb565(0, 255, 255), rgb565(255, 0, 0)),
               2: (rgb565(0, 255, 0), rgb565(0, 0, 255)), 3: (rgb565(255, 255, 255), rgb565(0, 0, 0))}
    with Edat.open(pack_path) as arc:
        members = {}
        for lod in LODS:
            t = Tmst.from_edat(arc, lod)
            replace = {}
            for tile in t.tiles:
                if variant == "mirror":
                    if tile.level == t.depth:
                        continue
                    side = t.grid_w << (t.depth - 1 - tile.level)
                    replace[tile.index] = t.read(t.tile(tile.level, side - 1 - tile.x, tile.y))
                else:
                    tex = t.texture(tile)
                    a, b = palette[tile.level] if lod == "highdef" else (rgb565(255, 128, 0), rgb565(128, 0, 255))
                    replace[tile.index] = zipo_tile(dxt1_checker(tex.width, tex.height, 64, a, b),
                                                    tex.width, tex.height)
            members.update(t.members(replace))
        with open(out_path, "wb") as f:
            n = arc.write_to(f, members)
    print(f"wrote {out_path} ({n:,} B, {variant})")


def main(argv):
    packs_dir = only = None
    if "--make-test" in argv:
        i = argv.index("--make-test")
        name, out = argv[i + 1], argv[i + 2]
        variant = argv[i + 3] if len(argv) > i + 3 else "checker"
        make_test(os.path.join(MAPS, f"DataMap{name}_v09.dat"), out, variant)
        return 0
    if "--packs" in argv:
        packs_dir = argv[argv.index("--packs") + 1]
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    paths = sorted(glob.glob(os.path.join(MAPS, "DataMap*_v09.dat")))
    if only:
        paths = [p for p in paths if os.path.basename(p) == f"DataMap{only}_v09.dat"]
    fails, counts = 0, {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0}
    tiles = 0
    for path in paths:
        name = os.path.basename(path)[7:-8]
        line = [name[:24].ljust(24)]
        with Edat.open(path) as arc:
            edits = {}
            for lod in LODS:
                t = Tmst.from_edat(arc, lod)
                tiles += len(t.tiles)
                probs = check_layout(t)
                a = not probs
                b = t.build_index() == t.index and b"".join(t.iter_chunk()) == bytes(t.chunk)
                replace = edit(t)
                c, new_size = check_edit(t, replace)
                d = storage_walk(t)
                edits[lod] = (t, replace)
                for k, v in zip("ABCD", (a, b, c, d)):
                    counts[k] += v
                fails += (not a) + (not b) + (not c)
                line.append(f"{lod[:2]} {t.grid_w}x{t.grid_h}x{t.depth} n={len(t.tiles):4} key={t.key:08x} "
                            f"A{'+' if a else '-'} B{'+' if b else '-'} C{'+' if c else '-'} D{'+' if d else '-'}"
                            f" store {len(t.chunk):,}->{new_size:,}")
                if probs:
                    line.append(f"  layout problems: {probs[:3]}")
            if packs_dir:
                out = os.path.join(packs_dir, "rt.dat")
                with open(out, "wb") as f:
                    arc.write_to(f)
                e = compare_files(path, out)
                os.remove(out)
                members = {}
                for lod, (t, replace) in edits.items():
                    members.update(t.members(replace))
                with open(out, "wb") as f:
                    arc.write_to(f, members)
                with Edat.open(out) as new:
                    f_ok = [x.path for x in new.entries] == [x.path for x in arc.entries]
                    for x, y in zip(arc.entries, new.entries):
                        if x.path in members:
                            f_ok &= new.read(y) == members[x.path]
                        else:
                            f_ok &= new.read(y) == arc.read(x)
                    for lod, (t, replace) in edits.items():
                        t2 = Tmst.from_edat(new, lod)
                        f_ok &= all(t2.read(t2.tiles[i])[:len(r)] == r for i, r in replace.items())
                    f_ok &= new.checksum == arc.checksum
                os.remove(out)
                counts["E"] += e
                counts["F"] += f_ok
                fails += (not e) + (not f_ok)
                line.append(f"pack E{'+' if e else '-'} F{'+' if f_ok else '-'}")
        print(" ".join(line), flush=True)
    print(f"\n{len(paths)} packs, {tiles:,} tiles; passes per check: {counts}; failures: {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
