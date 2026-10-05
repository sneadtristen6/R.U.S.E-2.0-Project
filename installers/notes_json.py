"""Every language's release notes of one app, in one file published beside its installer (rusemod.update NOTES_ASSET:
the apps show what's new in their own language, English for a language that has none).

    python installers/notes_json.py studio dist          -> dist/RUSE-Studio-notes.json
    python installers/notes_json.py studio --check       -> every language's file checked, nothing written

The English notes are .github/release-notes/<app>.md; a language's are <app>.<code>.md beside them, with the Studio's
language codes (fr, ger, ita, spa, pol, ru, cz, jpn, sc), written as the English ones are: a version's notes start
`**0.9.7:**` (no space before the colon: the apps look for exactly that), its changes in a two-column table. A
language's file may have fewer versions than the English (the apps fall back to English for the rest), never one
the English hasn't got. Also prints a line of links to each language's notes, for the release page.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / ".github" / "release-notes"
APPS = {"launcher": "Launcher", "studio": "Studio"}
# the apps' languages (src/ruse_studio/words.toml), and each one's own name for the release page's links
LANGS = {"fr": "Français", "ger": "Deutsch", "ita": "Italiano", "spa": "Español", "pol": "Polski", "ru": "Русский",
         "cz": "Čeština", "jpn": "日本語", "sc": "简体中文"}
VERSION = re.compile(r"^\*\*(\d+\.\d+\.\d+):\*\*", re.M)
SPACED = re.compile(r"^\*\*\d+\.\d+\.\d+\s+:\*\*", re.M)  # French typing's space before the colon: not seen


class NotesError(ValueError):
    pass


def versions(text: str) -> list[str]:
    return VERSION.findall(text)


def book(app: str, root: Path | None = None) -> dict[str, str]:
    """{language code: its notes} for `app`, English as "us"; refuses a language's file the apps would misread."""
    root = root or NOTES
    english = (root / f"{app}.md").read_text(encoding="utf-8-sig")
    out = {"us": english}
    known = set(versions(english))
    for path in sorted(root.glob(f"{app}.*.md")):
        code = path.name[len(app) + 1:-3]
        if code not in LANGS:
            raise NotesError(f"{path.name}: {code} isn't one of the apps' languages ({', '.join(LANGS)})")
        text = path.read_text(encoding="utf-8-sig")
        if SPACED.search(text):
            raise NotesError(f"{path.name}: a version heading has a space before its colon (write **0.9.7:**)")
        mine = versions(text)
        if not mine:
            raise NotesError(f"{path.name}: no version's notes (each starts **0.9.7:**)")
        extra = sorted(set(mine) - known, key=lambda v: tuple(int(p) for p in v.split(".")))
        if extra:
            raise NotesError(f"{path.name}: {', '.join(extra)} isn't in the English notes")
        out[code] = text
    return out


def links(app: str, tag: str, notes: dict, repo: str = "sneadtristen6/R.U.S.E-2.0-Project") -> str:
    """The release page's line of links to each language's notes (as published at `tag`)."""
    parts = [f"[{LANGS[c]}](https://github.com/{repo}/blob/{tag}/.github/release-notes/{app}.{c}.md)"
             for c in LANGS if c in notes]
    return " · ".join(parts)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] not in APPS:
        print(__doc__)
        return 2
    app, where = argv[0], argv[1]
    try:
        notes = book(app)
    except (NotesError, OSError) as exc:
        print(f"release notes: {exc}", file=sys.stderr)
        return 1
    if where == "--check":
        print(f"{app}: English and {len(notes) - 1} other language(s): {', '.join(c for c in notes if c != 'us') or 'none'}")
        return 0
    out = Path(where) / f"RUSE-{APPS[app]}-notes.json"
    out.write_text(json.dumps(notes, ensure_ascii=False), encoding="utf-8")
    tag = argv[2] if len(argv) > 2 else ""
    if tag:
        print(links(app, tag, notes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
