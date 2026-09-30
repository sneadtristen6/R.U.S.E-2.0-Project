"""The repository's own files: no Windows path mangled into control characters.

A path like "test\\map\\blitz" written with single backslashes in a normal (not raw) string turns \\b into a
backspace, \\t into a tab, \\f into a form feed, silently: the string is wrong and nothing warns (it happened three
times on 2026-09-30, and a test built a pack with a broken name). So:
  - Python: a non-raw string may use only the escapes \\n \\r \\t \\0 \\\\ \\' \\" \\x.. \\u.... \\N{...} and a line
    continuation; \\a \\b \\f \\v and unknown ones (\\m, \\s, ...) fail here, with the file and line. A backslash
    in a path goes in as "\\\\", or the path as "a/b".replace("/", "\\\\").
  - Every text file: no control characters other than tab, newline and carriage return, and no tab inside a
    Windows-looking path in Markdown (`D:\\RUSE-Instances<TAB>errain` was `\\terrain`).
"""
import io
import re
import tokenize
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_DIRS = ("src", "tests", "tools")
TEXT_SUFFIXES = {".py", ".md", ".toml", ".js", ".html", ".css", ".rndf", ".csv", ".yml", ".txt"}
SKIP_DIRS = {".git", ".claude", ".enola", "node_modules", "__pycache__", "build", "dist"}
VENDORED = {"ruse_mod_engine"}  # LittleGroove's engine, kept as he wrote it (PLAN decision 26)
GOOD = set("nrt0\\'\"xuN\n")
BAD_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def files(dirs, suffixes):
    for d in dirs:
        base = ROOT / d
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in suffixes and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS):
                yield p


def bad_escapes(source: str):
    """(line, the string's start) of every non-raw string literal with a mangling escape (f-strings too: from Python
    3.12 their text comes as FSTRING_MIDDLE pieces)."""
    fstring_raw = []  # for each f-string being read: whether it's raw
    fstart = getattr(tokenize, "FSTRING_START", None)
    fmiddle = getattr(tokenize, "FSTRING_MIDDLE", None)
    fend = getattr(tokenize, "FSTRING_END", None)
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if fstart is not None and tok.type == fstart:
            fstring_raw.append("r" in tok.string.lower())
            continue
        if fend is not None and tok.type == fend:
            if fstring_raw:
                fstring_raw.pop()
            continue
        if fmiddle is not None and tok.type == fmiddle:
            if fstring_raw and not fstring_raw[-1]:
                body = tok.string
            else:
                continue
        elif tok.type != tokenize.STRING:
            continue
        else:
            s = tok.string
            prefix = s[:len(s) - len(s.lstrip("rRbBuUfF"))].lower()
            if "r" in prefix:
                continue
            body = s[len(prefix):]
        s = tok.string
        i = 0
        while True:
            i = body.find("\\", i)
            if i < 0 or i + 1 >= len(body):
                break
            nxt = body[i + 1]
            if nxt not in GOOD:
                yield tok.start[0], s[:60]
                break
            i += 2


class Source(unittest.TestCase):
    def test_the_check_catches_the_mistakes_it_is_for(self):
        bs = chr(92)
        bad = [f'x = "test{bs}map{bs}blitz{bs}{bs}"', f'x = "a{bs}flat{bs}france"', f'x = "D:{bs}RUSE{bs}x"',
               f'x = f"test{bs}map{bs}{{name}}"', f'"""A doc: test{bs}map{bs}<map>."""']
        good = [f'x = r"test{bs}map{bs}blitz"', f'x = "test{bs}{bs}map{bs}{bs}blitz"', f'x = "line{bs}n{bs}ttab"',
                'x = "test/map/blitz/".replace("/", chr(92))', f'x = b"{bs}x00{bs}n"']
        with warnings.catch_warnings():  # the bad samples are bad on purpose
            warnings.simplefilter("ignore", SyntaxWarning)
            self.assertEqual([len(list(bad_escapes(s))) for s in bad], [1] * len(bad))
            self.assertEqual([len(list(bad_escapes(s))) for s in good], [0] * len(good))

    def test_no_mangling_escapes_in_python_strings(self):
        found = []
        for p in files(PY_DIRS, {".py"}):
            if set(p.relative_to(ROOT).parts) & VENDORED:
                continue
            try:
                src = p.read_text(encoding="utf-8")
                found += [f"{p.relative_to(ROOT)}:{line}: {text}" for line, text in bad_escapes(src)]
            except (tokenize.TokenError, SyntaxError, IndentationError) as exc:
                found.append(f"{p.relative_to(ROOT)}: can't be read ({exc})")
        self.assertEqual(found, [], "use \"\\\\\" for a backslash, a raw string, or \"a/b\".replace(\"/\", \"\\\\\")")

    def test_no_control_characters_in_text_files(self):
        found = []
        for p in files(("src", "tests", "tools", "docs", ".github"), TEXT_SUFFIXES):
            text = p.read_text(encoding="utf-8", errors="replace")
            for n, line in enumerate(text.splitlines(), start=1):
                if BAD_CONTROL.search(line):
                    found.append(f"{p.relative_to(ROOT)}:{n}: control character {BAD_CONTROL.search(line).group()!r}")
                if p.suffix.lower() == ".md" and re.search(r"[A-Za-z]:\\[^\s`]*\t", line):
                    found.append(f"{p.relative_to(ROOT)}:{n}: a tab inside a Windows path")
        for p in (ROOT / "README.md", ROOT / "PLAN.md"):
            if p.is_file() and BAD_CONTROL.search(p.read_text(encoding="utf-8", errors="replace")):
                found.append(f"{p.name}: control character")
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
