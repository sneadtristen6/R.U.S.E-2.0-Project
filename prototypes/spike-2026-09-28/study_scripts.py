"""Read-only study of Eugen's own Python (the .xyz code objects) for tool-design ideas.

Builds a table of contents of the game's scripting layer: module tree, the functions/classes it defines,
and the identifiers it references most (its API vocabulary). Nothing is written or committed.
"""
import collections, sys
import ndf, xyz
from m25 import parse_xyz, M25

IPKS = ["eugen.ipk", "eugensolo.ipk", "eugentest.ipk", "eugenpatchable.ipk"]


def walk_code(m, co, mods, names, defs):
    """Recurse a code-object dict, collecting referenced names and nested def/class names."""
    for n in co.get("names", ()):        # identifiers referenced (globals, attrs, imports)
        if isinstance(n, str):
            names[n] += 1
    for c in co.get("consts", ()):        # nested functions/classes are code dicts inside consts
        if isinstance(c, dict) and c.get("code"):
            if isinstance(c.get("name"), str) and c["name"] not in ("<lambda>", "<genexpr>"):
                defs.append(c["name"])
            walk_code(m, c, mods, names, defs)


def module_key(fn):
    fn = fn.replace("\\", "/")
    i = fn.find("/python/")
    return fn[i + 8:] if i >= 0 else fn


def main():
    names = collections.Counter()
    per_pkg = collections.Counter()
    modules = []
    interesting = {"leveldesign": [], "game": [], "interface": [], "tools": []}
    for ipk in IPKS:
        try:
            arc = xyz.load_ipk(ipk)
        except KeyError:
            continue
        for e in arc.entries:
            raw = arc.read(e)
            if raw[:4] != b"XYZ0":
                continue
            _, _, payload = parse_xyz(raw)
            co = M25(payload).obj()
            key = module_key(co.get("filename", e.path))
            modules.append(key)
            per_pkg[key.split("/")[1] if key.startswith("eugen") and "/" in key else key.split("/")[0]] += 1
            defs = []
            walk_code(None, co, modules, names, defs)
            top = key.split("/")[2] if key.count("/") >= 2 else ""
            for k in interesting:
                if ("/" + k + "/") in ("/" + key) or key.split("/")[-2:-1] == [k]:
                    interesting[k].extend(defs[:8])
        arc.close()
    print(f"modules parsed: {len(modules)}")
    print("\nsub-packages (module counts):")
    for k, v in per_pkg.most_common():
        print(f"  {v:>3}  {k}")
    print("\ntop 50 referenced identifiers (engine scripting vocabulary):")
    for n, c in names.most_common(50):
        print(f"  {c:>4}  {n}")
    print("\nsample module paths:")
    for mkey in sorted(set(modules))[:40]:
        print("  " + mkey)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
