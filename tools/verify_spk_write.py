r"""Verify the mesh-pack writer (rusemod.spk_edit) against every pack the game ships (READ-ONLY on the game).

  A. every pack in ZZ_Win.dat (gen_5\pack\*.spk: mesh, skeleton and map packs) and every map pack's static meshes
     (Maps\PC\DataMap*.dat: output\staticmeshes*.spkpc) rebuilds byte for byte, its header hash included;
  B. copying: every model of one pack copied into another (default: the German skirmish pack into the US one, the
     captured-Tiger case) reads back with rusemod.spk exactly like the original: positions, normals, UVs,
     triangles, material names and textures.

Usage:  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_spk_write.py [game_dir] [--from meshskirmish_ger] [--to meshskirmish_us]
DomesticNukes and his Claude, 2026-10-02.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod.build import find_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.spk import Spk  # noqa: E402
from rusemod.spk_edit import Pack, header_hash  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"


def packs(game: Path):
    arc = Edat.open(str(find_pack(game, "ZZ_Win.dat")))
    for e in arc.entries:
        p = e.path.lower()
        if p.startswith("gen_5\\pack\\") and p.endswith(".spk"):
            raw = bytes(arc.read(e))
            if raw[:8] == b"MESHPCPC":
                yield e.path, raw
    for dat in sorted((game / "Maps" / "PC").glob("DataMap*.dat")):
        with Edat.open(str(dat)) as m:
            for e in m.entries:
                if e.path.lower().endswith(".spkpc"):
                    yield f"{dat.name}:{e.path}", bytes(m.read(e))


def same_model(a: Spk, b: Spk, name: str) -> list[str]:
    pa, pb = a.model(name), b.model(name)
    if len(pa) != len(pb):
        return [f"{name}: {len(pa)} draw calls, copy has {len(pb)}"]
    out = []
    ma, mb = a.materials(), b.materials()
    for i, (x, y) in enumerate(zip(pa, pb)):
        for f in ("positions", "normals", "uvs", "indices", "atlas"):
            if getattr(x, f) != getattr(y, f):
                out.append(f"{name} draw {i}: {f} differ")
        if ma[x.material] != mb[y.material]:
            out.append(f"{name} draw {i}: material {ma[x.material]['name']} became {mb[y.material]['name']}")
    return out


def main(argv):
    game = Path(next((a for a in argv if not a.startswith("--")), DEFAULT_GAME))
    src_name = argv[argv.index("--from") + 1] if "--from" in argv else "meshskirmish_ger"
    dst_name = argv[argv.index("--to") + 1] if "--to" in argv else "meshskirmish_us"
    start = time.time()
    n = {"packs": 0, "identical": 0}
    by_name = {}
    for path, raw in packs(game):
        n["packs"] += 1
        pack = Pack.from_bytes(raw)
        new = pack.to_bytes()
        ok = new == raw and raw[0x10:0x20] == header_hash(raw)
        n["identical"] += ok
        if not ok:
            at = next((i for i in range(min(len(new), len(raw))) if new[i] != raw[i]), min(len(new), len(raw)))
            print(f"FAIL {path}: {len(raw)} bytes, rebuilt {len(new)}, first difference at {at:#x}")
        key = path.lower().rsplit("\\", 1)[-1].removesuffix(".spk")
        by_name[key] = raw
    print(f"A. {n['identical']} of {n['packs']} packs rebuilt byte for byte")

    src_raw, dst_raw = by_name[src_name], by_name[dst_name]
    src, dst = Pack.from_bytes(src_raw), Pack.from_bytes(dst_raw)
    names = [m.name.decode("latin-1") for m in src.models if m.skeleton == 0xCDCD
             and not any(d.name.lower() == m.name.lower() for d in dst.models)]
    for name in names:
        dst.copy_model(src, name)
    out = dst.to_bytes()
    a, b, before = Spk(src_raw), Spk(out), Spk(dst_raw)
    problems = []
    for name in names:
        problems += same_model(a, b, name)
    for name in before.items:  # the pack's own models are untouched
        problems += same_model(before, b, name)
    print(f"B. {len(names)} models copied from {src_name} into {dst_name} ({len(dst_raw)} -> {len(out)} bytes): "
          f"{'all read back the same' if not problems else f'{len(problems)} problems'}")
    for p in problems[:10]:
        print("      ", p)
    print(f"in {time.time() - start:.0f}s")
    return 0 if n["identical"] == n["packs"] and not problems else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
