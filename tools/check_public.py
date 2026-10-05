"""Keep the public repo public-safe (the owner's rule: sensitive files stay in the private shared repo). Fails when a
tracked file is something that belongs only there:

- the private folder, the research handover, the community mods (`private/`, `*handover*`, `mods/`);
- what describes the game's own files rather than the apps: lists of its files, notes on their layout, working notes,
  and tools that go through its data (`listings/`, `docs/FORMATS.md`, ..., every tool but the four named below);
- game files or data taken out of the game (packs, NDF, texts, textures, meshes, scenery, scripts; `.rmod` mods);
- details of the game's program: code addresses (`FUN_14xxxxxx`, `0x14xxxxxxx`) or disassembly-tool notes.

    py -3 tools/check_public.py            # the files git tracks here
    py -3 tools/check_public.py FILE ...   # just these (a pre-commit check)

GitHub runs it on every push and pull request (.github/workflows/tests.yml). The sync to the private repo only ever
goes one way (public -> private, .github/workflows/sync-private.yml), so nothing private comes back through it.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRS = ("private/", "mods/", "extracted/")
PRIVATE_NAMES = re.compile(r"handover", re.I)
# the owner, 2026-10-05: this repo holds the two apps and what players and modders need to use them. What describes
# the game's own files instead is kept in the private repo until the game's developers say otherwise: lists of its
# files, notes on how they are laid out, working notes, and the tools that go through its data. In tools/ only the
# four named here are public; a new tool is private until it is added to this list on purpose.
KEPT_PRIVATE = re.compile(r"^(?:listings/|prototypes/|ruse_edat\.py$|"
                          r"docs/(?:FORMATS|ENGINE_NOTES|RESEARCH[\w-]*|LITTLEGROOVE_STUDY|LESSONS|LOG|TASKS|PLAN|"
                          r"TESTS|ROADS|IWO_JIMA)\.md$|"
                          r"tools/(?!(?:check_public|check_commit_msg|post_discussions|rmod_to_mod)\.py$))", re.I)
GAME_FILES = {".dat", ".ndfbin", ".gladndfbin", ".dic", ".tgv", ".tgv_pc", ".spk", ".spkpc", ".ppk", ".ipk", ".xyz",
              ".boobspc", ".kdt", ".tms", ".tmst", ".tmst_pc", ".tmst_chunk_pc", ".scenario", ".ess", ".win", ".sdb",
              ".rmod", ".ase2ndfbin", ".exe", ".dll", ".pdb", ".idb", ".i64", ".gzf"}
PROGRAM = re.compile(r"\bFUN_[0-9A-Fa-f]{6,}\b|\b0x14[0-9A-Fa-f]{7}\b|\bsub_14[0-9A-Fa-f]{7}\b")
# words that say what the game's program does or holds (the owner: "NO do not mention exe in public"): public text
# says what the game does with its data, never what's inside RUSE.exe
WORDING = re.compile(r"RUSE\.exe'?s\b|RUSE\.exe (?:does|reads|checks|holds|keeps|decides|loads|has|uses|calls)\b|"
                     r"program-side|\b(?:in|inside) the (?:game's )?program\b|"
                     r"\bthe (?:game's )?program (?:does|reads|checks|holds|keeps|decides|loads|calls|caps)\b|"
                     r"exe internals|disassembl|\bRTTI\b|\bvtables?\b|"
                     # how anything was studied (the owner, 2026-10-02: nothing public may point at it): our text says
                     # "read the game's scripts", "the file's layout", "decoded", never these
                     r"decompil|reverse[- ]?engineer|uncompyle|\bxdis\b|ghidra|\bIDA\b|\bvfunc|"
                     # and the words and tools that lead to it
                     r"bytecode|opcode|hex-?rays|binary ninja|x64dbg|ollydbg|cheat engine|\bdebugger\b|minidump|"
                     r"crash ?dumps?\b|hex[- ]?editor|"
                     # the same in the other nine languages the apps and their pages speak (the owner, 2026-10-05:
                     # "translated every language on the GitHub"): a translation mustn't say what the English can't
                     r"d[ée]compil|dekompil|descompil|декомпил|逆コンパイル|反编译|"
                     r"r[ée]tro-?ing[ée]nierie|ing[ée]nierie inverse|ingegneria inversa|ingenier[ií]a inversa|"
                     r"in[żz]ynieri\w* wsteczn|обратн\w* (?:разработк|инжиниринг)|реверс-?инжиниринг|zp[ěe]tn\w* in[žz]en[ýy]r|"
                     r"リバースエンジニアリング|逆向工程|"
                     r"d[ée]sassembl|desensambl|deasembl|дизассембл|逆アセンブル|反汇编|"
                     r"d[ée]bogueur|depurador|debuger|отладчик|デバッガ|调试器|"
                     r"байт-?код|バイトコード|字节码|"
                     r"vidage (?:m[ée]moire|sur incident)|speicherabbild|absturzabbild|дамп\w*|クラッシュダンプ|崩溃转储|"
                     r"[ée]diteur hexad[ée]cimal|editor hexadecimal|шестнадцатеричн\w* редактор|16進エディタ|十六进制编辑器",
                     re.I)
# how public text frames what we do (the owner, 2026-10-04, on "read-only count of everything in the game data"): it
# says what changing strictly data can do, and that anything beyond data is outside the project; never that we go
# through the whole of the game's data
FRAMING = re.compile(r"everything (?:we know )?(?:in|about) the game(?:'s)? (?:data|files)\b|\bwhole-game\b|"
                     r"\b(?:index|scan|survey|count|dump|walk|verif)\w* (?:of )?the whole game\b|"
                     r"\bagainst the whole game\b|across every (?:NDF |data )?file in every pack|"
                     r"\bevery (?:archive|pack|NDF file|data file)(?: and (?:archive|pack|NDF file|data file))? in the "
                     r"game\b|"
                     r"\b(?:scan|survey|count|dump) of (?:everything|how the game|the game(?:'s)? (?:data|files))|"
                     # and nothing public says there is work beyond data somewhere else, or planned
                     r"runtime extender|\bprogram work\b|program can'?t be edited", re.I)
# where the words may appear on purpose: this check itself, and code that must refuse such files; the GPL's text
ALLOWED = {"tools/check_public.py", "tests/test_check_public.py", "tools/check_commit_msg.py"}
WORDING_ALLOWED = {"LICENSE"}
# LittleGroove's engine as he wrote and published it (PLAN decision 26): his words are his, left as they are
WORDING_ALLOWED_DIRS = ("src/ruse_mod_engine/",)
TEXT_LIMIT = 4_000_000


def problems(paths: list[str], read=lambda p: (ROOT / p).read_bytes()) -> list[str]:
    out = []
    for path in paths:
        p = path.replace("\\", "/")
        low = p.lower()
        if p in ALLOWED:
            continue
        if low.startswith(PRIVATE_DIRS) or any(f"/{d}" in f"/{low}" for d in PRIVATE_DIRS[:1]):
            out.append(f"{p}: private material belongs in the private shared repo")
            continue
        if PRIVATE_NAMES.search(PurePosixPath(low).name):
            out.append(f"{p}: the research handover stays in the private repo")
            continue
        if KEPT_PRIVATE.search(p):
            out.append(f"{p}: describes the game's own files (a list of them, notes on them, or a tool that goes "
                       f"through them); kept in the private repo")
            continue
        suffix = PurePosixPath(low).suffix
        if suffix in GAME_FILES and not low.startswith("tests/"):
            out.append(f"{p}: a game file (or one made from the game's), never stored here")
            continue
        try:
            data = read(p)
        except OSError:
            continue
        if len(data) > TEXT_LIMIT or b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", "replace")
        m = PROGRAM.search(text)
        if m:
            out.append(f"{p}: names a place in the game's program ({m.group(0)}); program details stay private")
            continue
        m = WORDING.search(text) if p not in WORDING_ALLOWED and not p.startswith(WORDING_ALLOWED_DIRS) else None
        if m:
            line = text.count("\n", 0, m.start()) + 1
            out.append(f"{p}:{line}: says what the game's program does or holds ({m.group(0)!r}); public text says "
                       f"what the game does with its data")
            continue
        m = FRAMING.search(text) if p not in WORDING_ALLOWED and not p.startswith(WORDING_ALLOWED_DIRS) else None
        if m:
            line = text.count("\n", 0, m.start()) + 1
            out.append(f"{p}:{line}: says we go through the whole of the game's data ({m.group(0)!r}); public text "
                       f"says what changing strictly data can do, and that anything beyond data is outside the project")
    return out


def main(argv: list[str]) -> int:
    paths = argv or subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True,
                                   check=True).stdout.splitlines()
    found = problems(paths)
    for line in found:
        print(line)
    print(f"{len(paths)} file(s) checked, {len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
