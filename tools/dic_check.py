r"""Check the text files (.dic) against docs/FORMATS.md §4 and src/rusemod/dic.py (READ-ONLY).

For every .dic (magic TRA) in every pack, reports:
  - which version bytes occur (FORMATS says TRA\0; RUSE-Mod-Manager's notes say the shipped files are TRA\x01)
  - whether every text lies inside the file after the table (offsets count from the start of the file)
  - how many entries share a text, and whether texts end with a UTF-16 null
  - whether keys are sorted
  - how many keys decode to names with the 6-bit scheme (Wargame's, via moddingSuite), with examples
  - how many files there are per language folder
  - the writer: adding one entry (in memory) keeps every original text readable and unchanged
Nothing is written.

  set PYTHONPATH=<repo>\src  &&  py -3 tools\dic_check.py [game_dir]
"""
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from rusemod import Edat  # noqa: E402
from rusemod.dic import Dic, name_to_key  # noqa: E402

PROBE_KEY = name_to_key("ZZPROBE9")  # a key no shipped file should use

DEFAULT_GAME = r"D:\Steam\steamapps\common\R.U.S.E"
LANG = re.compile(r"\\translations\\([^\\]+)\\|\\(dev)\\", re.I)


def walk_dic(arc, where):
    for e in arc.entries:
        data = bytes(arc.read(e))
        if data[:4] == b"edat":
            yield from walk_dic(Edat(data), f"{where}!{e.path}")
        elif data[:3] == b"TRA":
            yield f"{where}!{e.path}", data


def main():
    game = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GAME
    packs = sorted(glob.glob(os.path.join(game, "Data", "PC", "*", "*.dat")))
    if not packs:
        print(f"no archives found under {game}")
        return 2
    t = collections.Counter()
    versions, langs = collections.Counter(), collections.Counter()
    failures, undecoded, names = [], [], []
    for path in packs:
        with Edat.open(path) as arc:
            for where, raw in walk_dic(arc, os.path.basename(path)):
                t["files"] += 1
                try:
                    dic = Dic(raw)
                except ValueError as exc:
                    failures.append(f"{where}: {exc}")
                    continue
                versions[dic.version] += 1
                m = LANG.search(where)
                langs[(m.group(1) or m.group(2)).lower() if m else "(other)"] += 1
                table_end = 8 + 16 * len(dic.entries)
                offsets = collections.Counter(e.offset for e in dic.entries)
                keys = [e.key for e in dic.entries]
                t["entries"] += len(dic.entries)
                t["files with keys sorted"] += keys == sorted(keys)
                t["files with every text after the table"] += all(e.offset >= table_end for e in dic.entries)
                t["entries sharing a text"] += sum(c for c in offsets.values() if c > 1)
                if PROBE_KEY not in {e.key for e in dic.entries}:
                    probe = Dic(raw)
                    probe.add(PROBE_KEY, "probe")
                    again = Dic(probe.to_bytes())
                    t["files where adding an entry keeps every old text"] += (
                        all(again.text(e.key) == e.text for e in dic.entries) and again.text(PROBE_KEY) == "probe")
                for e in dic.entries:
                    end = e.offset + 2 * e.length
                    t["texts followed by a UTF-16 null"] += raw[end:end + 2] == b"\0\0"
                    if e.name:
                        t["keys that decode to names"] += 1
                        if len(names) < 25:
                            names.append(f"{e.name} = {e.text[:40]!r}")
                    elif len(undecoded) < 10:
                        undecoded.append(f"{e.key:#018x} = {e.text[:40]!r}  ({where})")
    print(f".dic files: {t['files']}  entries: {t['entries']}  unreadable: {len(failures)}")
    for f in failures[:10]:
        print("  ! " + f)
    print(f"version bytes: {dict(versions)}")
    print(f"files with keys sorted: {t['files with keys sorted']} of {t['files']}")
    print(f"files with every text after the table (offsets from file start): "
          f"{t['files with every text after the table']} of {t['files']}")
    print(f"entries sharing a text with another entry: {t['entries sharing a text']}")
    print(f"texts followed by a UTF-16 null: {t['texts followed by a UTF-16 null']} of {t['entries']}")
    print(f"keys that decode to names: {t['keys that decode to names']} of {t['entries']}")
    print("examples:\n  " + "\n  ".join(names))
    if undecoded:
        print("keys that don't decode (examples):\n  " + "\n  ".join(undecoded))
    print(f"files per language folder: {dict(langs)}")
    print(f"writer check, files where adding an entry keeps every old text: "
          f"{t['files where adding an entry keeps every old text']} of {t['files']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
