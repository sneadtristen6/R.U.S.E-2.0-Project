r"""Verify the unit-pack writer (rusemod.unitpacks) against the game's own packs (READ-ONLY on the game).

  A. every mesh and skeleton pack (.spk) and texture stand-in pack (.ppk) in ZZ_Win.dat writes back byte for byte,
     and every draw call names its own mesh (first field) and ends 0xCDCD, in the game's packs and in every changed one;
  B. every animation pack (.apk) and every archive's dictionary (Data\PC\<rev>\*.dat) is rebuilt byte for byte by the
     same trie writer (the animation packs whole, by archive_with);
  C. every unit's models are given to every other nation's skirmish packs and to the common ones (one set of packs
     per nation, all units at once): nothing refused; in every changed mesh pack every model it had reads the same
     (positions, normals, UVs, triangles, material) and every new one as in the pack it came from; skeletons,
     stand-ins and animations the same way.
--quick does C for the Ju 87 and the Tiger into the US's packs only. Nothing is written anywhere.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\verify_unitpacks.py [game_dir] [--quick]
"""
import glob
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from pathlib import Path  # noqa: E402

from rusemod import unitcheck, unitpacks  # noqa: E402
from rusemod.build import find_pack, load_pack  # noqa: E402
from rusemod.edat import Edat  # noqa: E402
from rusemod.spk import Spk  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"
QUICK = ("$/GFX/Everything/Descriptor_Avion_Junkers_87", "$/GFX/Everything/Descriptor_Unit_Panzer_VI_Tigre")


def draw_rule(pack) -> list[str]:
    """The game's own rule for draw calls: the first field is the call's own mesh number, the last 0xCDCD."""
    bad = []
    for m, (first, count) in enumerate(pack.meshes):
        for d in range(first, first + count):
            if pack.draws[d][0] != m or pack.draws[d][5] != 0xCDCD:
                bad.append(f"draw {d} of mesh {m}: {pack.draws[d][0]}, {pack.draws[d][5]:#x}")
    return bad


def round_trips(zz: Edat, game: str) -> list[str]:
    bad, n = [], {"spk": 0, "ppk": 0, "apk": 0, "dat": 0}
    for e in zz.entries:
        p = e.path.lower()
        if not p.endswith((".spk", ".ppk", ".apk")):
            continue
        raw = bytes(zz.read(e))
        try:
            if raw[:8] == unitpacks.MESH_MAGIC:
                pack = unitpacks.MeshPack.read(raw)
                out, kind = pack.to_bytes(), "spk"
                bad += [f"{e.path}: {w}" for w in draw_rule(pack)[:3]]
            elif raw[:8] == unitpacks.PROXY_MAGIC:
                out, kind = unitpacks.ProxyPack.read(raw).to_bytes(), "ppk"
            elif raw[:4] == b"edat" and p.endswith(".apk"):
                out, kind = unitpacks.archive_with(raw, {}), "apk"
            else:
                continue
        except (unitpacks.PackError, ValueError) as exc:
            bad.append(f"{e.path}: {exc}")
            continue
        n[kind] += 1
        if out != raw:
            bad.append(f"{e.path}: written back differently")
    for path in sorted(glob.glob(os.path.join(game, "Data", "PC", "*", "*.dat"))):
        with Edat.open(path) as arc:
            d = bytes(arc._dict)
            names = unitpacks.read_names(d, 10, len(d), 9)
            out = (unitpacks.NAMES_HEAD + unitpacks.write_names(names)) if names else d
            n["dat"] += 1
            if out != d:
                bad.append(f"{os.path.basename(path)}: dictionary rebuilt differently")
    print(f"A/B. written back: {n['spk']} .spk, {n['ppk']} .ppk, {n['apk']} .apk, {n['dat']} archive dictionaries; "
          f"{len(bad)} not the same")
    return bad


def _parts(spk: Spk, name: str):
    mats = spk.materials()
    return [(p.positions, p.normals, p.uvs, p.indices, p.atlas, mats[p.material]) for p in spk.model(name)]


def check_changed(zz: Edat, out: dict, where: dict) -> list[str]:
    """`where`: {name copied in: the pack path it came from} by kind."""
    bad = []
    for path, new in out.items():
        old = bytes(zz.read(zz.entry(path)))
        short = path.rsplit("\\", 1)[-1]
        if path.endswith(".spk"):
            a, b = unitpacks.MeshPack.read(old), unitpacks.MeshPack.read(new)
            if b.to_bytes() != new:
                bad.append(f"{short}: doesn't read back")
            bad += [f"{short}: {w}" for w in draw_rule(b)[:3]]
            if a.meshes:
                sa, sb = Spk(old), Spk(new)
                bad += [f"{short}: {n} changed" for n in sa.items if _parts(sa, n) != _parts(sb, n)]
                for n in set(sb.items) - set(sa.items):
                    src = Spk(bytes(zz.read(zz.entry(where["mesh"][n]))))
                    if _parts(src, n) != _parts(sb, n) or src.items[n].box != sb.items[n].box:
                        bad.append(f"{short}: the copy of {n} reads differently")
            else:
                for n in a.items:
                    if a.skeletons[a.items[n][2]] != b.skeletons[b.items[n][2]]:
                        bad.append(f"{short}: the skeleton of {n} changed")
                for n in set(b.items) - set(a.items):
                    src = unitpacks.MeshPack.read(bytes(zz.read(zz.entry(where["skeleton"][n]))))
                    if src.skeletons[src.items[n][2]] != b.skeletons[b.items[n][2]]:
                        bad.append(f"{short}: the copy of {n}'s skeleton differs")
        elif path.endswith(".ppk"):
            a, b = unitpacks.ProxyPack.read(old), unitpacks.ProxyPack.read(new)
            da = dict(zip(a.names(), a.proxies))
            db = dict(zip(b.names(), b.proxies))
            bad += [f"{short}: {n} changed" for n in da if (da[n].key, da[n].data) != (db[n].key, db[n].data)]
            names = b.names()
            if [n for n in names if n in da] != a.names():
                bad.append(f"{short}: the names it had moved")
            for i, n in enumerate(names):  # a new name between its neighbours (two shipped packs aren't all sorted)
                if n not in da and not (i == 0 or unitpacks.sort_key(names[i - 1]) < unitpacks.sort_key(n)) \
                        or n not in da and i + 1 < len(names) and unitpacks.sort_key(names[i + 1]) < unitpacks.sort_key(n):
                    bad.append(f"{short}: {n} out of name order")
        else:
            a, b = Edat(old), Edat(new)
            bad += [f"{short}: {e.path} changed" for e in a.entries if bytes(b.read(b.entry(e.path))) != bytes(a.read(e))]
    return bad


def give_all(zz: Edat, game: Path, quick: bool) -> list[str]:
    g = load_pack(Edat.open(str(find_pack(game, "ZZ_GladPatchableWin.dat")))).base
    units = QUICK if quick else sorted(n for n, o in g.objects.items() if unitcheck.is_unit(o))
    targets = ["us"] if quick else list(unitpacks.TAGS) + [unitpacks.COMMON]
    bad = []
    for target in targets:
        t = time.time()
        packs = unitpacks.Packs(zz)
        where: dict = {"mesh": {}, "skeleton": {}}
        given_units = 0
        for u in units:
            o = g.objects[u]
            home = unitcheck.nation_of(o)
            if not 0 <= home < len(unitpacks.TAGS) or unitpacks.TAGS[home] == target:
                continue
            models = sorted(unitcheck.model_files(o, g))
            for kind in where:
                for m in models:
                    src = packs._source(kind, m, [unitpacks.TAGS[home]])
                    if src:
                        where[kind].setdefault(m, src)
            given, why = packs.give(models, target, [unitpacks.TAGS[home]])
            bad += [f"{target}: {u}: {w}" for w in why]
            given_units += bool(given)
        out = packs.output()
        problems = check_changed(zz, out, where)
        bad += problems
        print(f"C. {target}: {given_units} units' models copied into {len(out)} packs, {len(problems)} problems "
              f"({time.time() - t:.0f}s)")
    return bad


def main(argv):
    game = next((a for a in argv if not a.startswith("--")), DEFAULT_GAME)
    quick = "--quick" in argv
    zz = Edat.open(str(find_pack(Path(game), "ZZ_Win.dat")))
    bad = ([] if quick else round_trips(zz, game)) + give_all(zz, Path(game), quick)
    for line in bad[:30]:
        print("  FAIL", line)
    print(f"\n{'OK' if not bad else 'FAILED'}: {len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
