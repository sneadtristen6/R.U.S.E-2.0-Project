"""Refuse a public commit message that mentions the game's program or what's inside it (the owner's rule: never in
public). GitHub shows each folder's last commit message on the repository's front page, so a message is public text
like any file (an old one, about taking such details out, stood next to a folder there).

    py -3 tools/check_commit_msg.py <message file>     # the commit-msg hook (.git/hooks/commit-msg) runs it

Our own apps are "programs" or "installers" in messages, never "exe"."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_public import PROGRAM, WORDING  # noqa: E402

EXE = re.compile(r"\bexe\b|\.exe\b", re.I)


def problems(message: str) -> list[str]:
    text = "\n".join(line for line in message.splitlines() if not line.startswith("#"))
    return [f"the message says {m.group(0)!r}: public commit messages never mention the game's program or what's in it"
            for rx in (EXE, PROGRAM, WORDING) for m in [rx.search(text)] if m]


def main(argv: list[str]) -> int:
    found = problems(Path(argv[0]).read_text(encoding="utf-8", errors="replace")) if argv else []
    for f in found:
        print(f"commit refused: {f}", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
