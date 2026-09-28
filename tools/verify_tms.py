r"""Verify the terrain mesh (.tms) reader/writer against the real map packs (READ-ONLY on the game install).

  A. Every highdef.tms / lowdef.tms of every map pack parses and re-serializes byte-identically.
  B. (--full) Every cell is decoded and re-encoded with our own LZ encoder; the rebuilt file re-reads to the
     same vertices, normals, triangle lists and patch tables.
  C. Edit: raise a plateau at the map centre in both meshes of one pack; the rebuilt files re-read with exactly
     the intended heights, untouched cells stay byte-identical, patch bounds cover the new heights.
  D. (--out DIR) Writes the edited .tms files, the rebuilt map pack (same file name as the original) and
     grayscale height PNGs (before/after) into DIR, which must be outside the game folder.

Usage:
  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_tms.py [--maps DIR] [--pack TwoIslands] [--full] [--out DIR]
"""
import argparse
import glob
import os
import struct
import sys
import time
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat  # noqa: E402
from rusemod.tms import Q_MAX, Tms, plateau  # noqa: E402

MAPS = r"D:\Steam\steamapps\common\R.U.S.E\Maps\PC"
MEMBERS = ("output\\highdef.tms", "output\\lowdef.tms")


def ok(name, passed, detail=""):
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))
    return passed


def write_png(path, grid, lo=None, hi=None):
    """8-bit grayscale PNG of a height grid (None = black)."""
    vals = [v for row in grid for v in row if v is not None]
    lo = min(vals) if lo is None else lo
    hi = max(vals) if hi is None else hi
    span = (hi - lo) or 1.0
    raw = b"".join(b"\0" + bytes(0 if v is None else max(0, min(255, int(255 * (v - lo) / span))) for v in row)
                   for row in grid)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    head = struct.pack(">IIBBBBB", len(grid[0]), len(grid), 8, 0, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", head) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def full_reencode(raw):
    """Re-encode every cell; return (identical_decode, old_size, new_size)."""
    m = Tms(raw)
    before = [(c.positions(), c.normals()) for c in m.cells]
    for c in m.cells:
        c.set_vertices(c.positions(), c.normals())
    out = m.to_bytes()
    back = Tms(out)
    same = all((c.positions(), c.normals()) == b for c, b in zip(back.cells, before))
    orig = Tms(raw)
    same &= all(a.ib == b.ib and a.patches == b.patches and a.icount == b.icount for a, b in zip(orig.cells, back.cells))
    same &= back.skirt == orig.skirt and back.skirt_data == orig.skirt_data and back.bounds == orig.bounds
    return same, len(raw), len(out)


def edit(raw, frac_top=0.06, frac_base=0.10):
    """Plateau at the map centre, top at the file's highest height. Returns (edited bytes, report dict)."""
    m = Tms(raw)
    x0, y0, z0, x1, y1, z1 = m.bounds
    cx, cy, width = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0
    fn = plateau(cx, cy, width * frac_top, width * frac_base, z1)
    # expected quantized heights, computed from the untouched decode
    expect = []
    for c in m.cells:
        row = []
        for p in c.positions():
            nz = None if (p[0] in (0, Q_MAX) or p[1] in (0, Q_MAX)) else fn(m.to_world(0, p[0]), m.to_world(1, p[1]), m.to_world(2, p[2]))
            row.append(p[2] if nz is None else m.to_quant(2, nz))
        expect.append(row)
    orig_vb = [c.vb for c in m.cells]
    n = m.edit_heights(fn)
    out = m.to_bytes()
    back = Tms(out)
    exact = all([p[2] for p in c.positions()] == e for c, e in zip(back.cells, expect))
    xyw_same = all([(p[0], p[1], p[3]) for p in a.positions()] == [(p[0], p[1], p[3]) for p in b.positions()]
                   for a, b in zip(Tms(raw).cells, back.cells))
    changed_cells = [k for k, c in enumerate(back.cells) if c.vb != orig_vb[k]]
    covered = True
    for c in back.cells:
        pos = c.positions()
        for p in c.patch_list():
            if p.vcount:
                zs = [back.to_world(2, max(v[2], v[3])) for v in pos[p.vstart:p.vstart + p.vcount]]
                covered &= max(zs) <= p.zhi + 1e-3 * abs(p.zhi) + 1
    top_q = m.to_quant(2, z1)
    at_top = sum(1 for c in back.cells for p in c.positions() if p[2] == top_q)
    return out, dict(vertices=n, exact=exact, xyw_same=xyw_same, changed_cells=changed_cells, covered=covered,
                     at_top=at_top, centre=(cx, cy), top=z1, radii=(width * frac_top, width * frac_base))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", default=MAPS)
    ap.add_argument("--pack", default="TwoIslands")
    ap.add_argument("--full", action="store_true", help="also re-encode every cell of every file (slow)")
    ap.add_argument("--out", help="directory for the edited files and PNGs (outside the game folder)")
    ap.add_argument("--png-width", type=int, default=384)
    a = ap.parse_args()
    packs = sorted(glob.glob(os.path.join(a.maps, "DataMap*_v09.dat")))
    if not packs:
        print(f"no map packs in {a.maps}")
        return 2
    results = []

    print(f"A. byte-identical re-serialization ({len(packs)} packs)")
    ident = total = cells = 0
    t = time.time()
    for pk in packs:
        with Edat.open(pk) as arc:
            for name in MEMBERS:
                raw = arc.read(arc.find(name))
                m = Tms(raw)
                total += 1
                cells += len(m.cells)
                ident += m.to_bytes() == raw
    results.append(ok("files re-serialize byte-identically", ident == total,
                      f"{ident}/{total} files, {cells} cells, {time.time() - t:.1f}s"))

    if a.full:
        print("B. full decode + re-encode of every cell")
        same = total = 0
        osz = nsz = 0
        t = time.time()
        for pk in packs:
            with Edat.open(pk) as arc:
                for name in MEMBERS:
                    s, o, n = full_reencode(arc.read(arc.find(name)))
                    same += s
                    total += 1
                    osz += o
                    nsz += n
        results.append(ok("re-encoded files re-read identically", same == total,
                          f"{same}/{total} files; size {nsz / osz:.3f}x of original, {time.time() - t:.0f}s"))

    matches = [p for p in packs if os.path.basename(p).lower() == f"datamap{a.pack.lower()}_v09.dat"]
    if not matches:
        print(f"pack {a.pack} not found")
        return 2
    pk = matches[0]
    print(f"C. plateau edit on {os.path.basename(pk)}")
    with Edat.open(pk) as arc:
        originals = {name: arc.read(arc.find(name)) for name in MEMBERS}
    edited = {}
    for name, raw in originals.items():
        out, r = edit(raw)
        edited[name] = out
        tag = name.split("\\")[1]
        print(f"    {tag}: centre ({r['centre'][0]:.0f}, {r['centre'][1]:.0f}), radii {r['radii'][0]:.0f}/{r['radii'][1]:.0f}, "
              f"top z {r['top']:.1f}; {r['vertices']} vertices in cells {r['changed_cells']}; {r['at_top']} at the top")
        results.append(ok(f"{tag}: re-reads with exactly the intended heights", r["exact"]))
        results.append(ok(f"{tag}: x, y and water untouched", r["xyw_same"]))
        results.append(ok(f"{tag}: patch bounds cover the new heights", r["covered"]))
        results.append(ok(f"{tag}: only cells under the plateau changed",
                          0 < len(r["changed_cells"]) < len(Tms(raw).cells)))

    if a.out:
        out_dir = os.path.abspath(a.out)
        game = os.path.dirname(os.path.dirname(os.path.abspath(a.maps)))   # ...\R.U.S.E
        try:
            inside = os.path.commonpath([out_dir, game]) == game
        except ValueError:  # different drives
            inside = False
        if inside or "steamapps" in out_dir.lower():
            print("refusing to write inside the game folder")
            return 2
        os.makedirs(out_dir, exist_ok=True)
        print(f"D. writing to {out_dir}")
        for name, blob in edited.items():
            with open(os.path.join(out_dir, name.split("\\")[1]), "wb") as f:
                f.write(blob)
        pack_out = os.path.join(out_dir, os.path.basename(pk))
        with Edat.open(pk) as arc, open(pack_out, "wb") as f:
            arc.write_to(f, {name: blob for name, blob in edited.items()})
        with Edat.open(pack_out) as new, Edat.open(pk) as old:
            members_ok = all(new.read(new.find(e.path)) == (edited[e.path] if e.path in edited else old.read(e))
                             for e in old.entries)
        results.append(ok("rebuilt map pack reads back (edited members new, all others identical)", members_ok))
        for label, blob in (("before", originals[MEMBERS[0]]), ("after", edited[MEMBERS[0]])):
            m = Tms(blob)
            write_png(os.path.join(out_dir, f"heights_{label}.png"), m.height_grid(a.png_width), m.bounds[2], m.bounds[5])
        with Edat.open(pk) as arc:
            with open(os.path.join(out_dir, "terrain.png"), "wb") as f:
                f.write(arc.read(arc.find("output\\terrain.png")))
        print("    heights_before.png, heights_after.png, terrain.png written")

    print(f"{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
