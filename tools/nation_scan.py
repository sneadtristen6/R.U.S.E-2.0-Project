r"""Count everything in the game data that is built around the 7 nations (READ-ONLY). See docs/RESEARCH.md §6.

For a real 8th nation (China, RUSE 2.0, PLAN.md decision 19), every place the data keeps one entry per nation needs an
8th entry, and every kind of object tagged with a nation needs Chinese versions. This counts both, across every data
file in every pack (the debug-info copies are skipped, as builds skip them):
  A. objects with a Nationalite, by class and nation (0 = US, which isn't written)
  B. lists with exactly 7 items, by class and property. A * marks names about nations, flags or countries: those are
     most likely one entry per nation. The rest may hold 7 things by coincidence and need a look.
  C. nation bit fields (properties named BitFieldNationalite...): the values in use, one bit per nation
Nothing is written.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\nation_scan.py [game_dir]
"""
import collections
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat, Ndf  # noqa: E402
from rusemod.build import SHADOW  # noqa: E402
from rusemod.model import game_path  # noqa: E402
from rusemod.ndf import iter_values  # noqa: E402

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"
NATIONS = {0: "US", 1: "GER", 2: "UK", 3: "FR", 4: "ITA", 5: "USSR", 6: "JAP"}  # FORMATS.md §3
INTS = {0x00, 0x01, 0x02, 0x03, 0x13, 0x18, 0x19}
NATION_WORDS = re.compile(r"nation|flag|drapeau|pays|country", re.IGNORECASE)


def walk_ndf(arc, where):
    for e in arc.entries:
        data = bytes(arc.read(e))
        if data[:4] == b"edat":
            yield from walk_ndf(Edat(data), f"{where}!{e.path}")
        elif data[:4] == b"EUG0" and data[8:12] == b"CNDF":
            yield f"{where}!{e.path}", e.path, data


def count(n):
    return f"{n:,}"


class Scan:
    def __init__(self):
        self.files = self.shadows = 0
        self.nations = collections.defaultdict(collections.Counter)  # class -> Counter(nation or None)
        self.sevens = collections.defaultdict(lambda: [0, set()])     # (class, property) -> [objects, files]
        self.bits = collections.defaultdict(collections.Counter)      # (class, property) -> Counter(value)

    def add(self, where, ndf):
        self.files += 1
        for o in ndf.objects:
            cls, nation = ndf.classes[o.cls], None
            for pi, v in o.props:
                name = ndf.prop_name(pi)
                if name == "Nationalite" and v.tc in INTS:
                    nation = v.scalar()
                elif name.startswith("BitFieldNationalite") and v.tc in INTS:
                    self.bits[(cls, name)][v.scalar()] += 1
                for x in iter_values(v):
                    if x.tc == 0x11 and struct.unpack_from("<I", x.payload)[0] == 7:
                        key = (cls, name if x is v else f"{name} (inside)")
                        self.sevens[key][0] += 1
                        self.sevens[key][1].add(where)
            self.nations[cls][nation] += 1

    def report(self):
        print(f"NDF files: {count(self.files)} (skipped {self.shadows} debug-info copies)")
        print("A. Objects with a nation, by class (0 = US, not written):")
        tagged = {c: n for c, n in self.nations.items() if any(k is not None for k in n)}
        for cls, n in sorted(tagged.items(), key=lambda kv: -sum(kv[1].values())):
            per = collections.Counter()
            for k, v in n.items():  # not written = 0, the US
                per[k if k is not None else 0] += v
            cells = ", ".join(f"{NATIONS.get(k, k)} {count(v)}" for k, v in sorted(per.items()))
            print(f"  {cls} ({count(sum(n.values()))}): {cells}")
        print("B. Lists with exactly 7 items (* = named after nations, flags or countries):")
        starred = 0
        for (cls, name), (objs, files) in sorted(self.sevens.items(), key=lambda kv: (-kv[1][0], kv[0])):
            star = "*" if NATION_WORDS.search(name) else " "
            starred += star == "*"
            print(f"  {star} {cls}.{name}: {count(objs)} object(s) in {count(len(files))} file(s)")
        print("C. Nation bit fields (values in use):")
        for (cls, name), values in sorted(self.bits.items()):
            cells = ", ".join(f"0x{v:X} ×{n}" for v, n in sorted(values.items()))
            print(f"  {cls}.{name}: {cells}")
        star_objs = sum(o for (c, n), (o, f) in self.sevens.items() if NATION_WORDS.search(n))
        star_files = len(set().union(*[f for (c, n), (o, f) in self.sevens.items() if NATION_WORDS.search(n)] or [set()]))
        print(f"Summary: an 8th entry in {starred} named per-nation structure(s) ({count(star_objs)} objects, "
              f"{count(star_files)} files), plus any unstarred 7-item lists that turn out to be per nation; "
              f"Chinese versions of {len(tagged)} kind(s) of nation-tagged objects; {len(self.bits)} bit field(s).")


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GAME
    packs = sorted(glob.glob(os.path.join(game, "Data", "PC", "*", "*.dat"))) + \
        sorted(glob.glob(os.path.join(game, "Maps", "PC", "*.dat")))
    if not packs:
        print(f"no archives found under {game}")
        return 2
    scan = Scan()
    for path in packs:
        with Edat.open(path) as arc:
            for where, member, raw in walk_ndf(arc, os.path.basename(path)):
                if SHADOW.search(game_path(member)):
                    scan.shadows += 1
                    continue
                scan.add(where, Ndf(raw))
    scan.report()
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
