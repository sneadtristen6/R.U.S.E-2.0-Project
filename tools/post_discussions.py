"""Post the project's own Discussions posts from docs/community/*.md, the way docs/wiki is the wiki's source.

Each file starts with a front matter block (title, category), then the post's Markdown. The first run creates the
post in that category; later runs update it in place (the numbers are kept in docs/community/posted.json). It uses
the GitHub CLI, signed in by the owner (`gh auth login`); it never sees or stores a token.

    python tools/post_discussions.py            # what it would do
    python tools/post_discussions.py --post     # do it

Categories and pins can't be set through GitHub's API: make and pin them on the website.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = ("sneadtristen6", "Ruse-Mod-Platform")
FOLDER = Path(__file__).resolve().parents[1] / "docs" / "community"
POSTED = FOLDER / "posted.json"


def gh() -> str:
    found = shutil.which("gh") or next((str(p) for p in (Path("C:/Program Files/GitHub CLI/gh.exe"),) if p.is_file()), None)
    if not found:
        sys.exit("The GitHub CLI isn't installed: winget install --id GitHub.cli, then gh auth login")
    return found


def graphql(query: str, **values: str) -> dict:
    args = [gh(), "api", "graphql", "-f", f"query={query}"]
    for key, value in values.items():
        args += ["-f", f"{key}={value}"]
    done = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if done.returncode:
        sys.exit(f"GitHub said: {done.stderr.strip() or done.stdout.strip()}")
    return json.loads(done.stdout)["data"]


def read_post(path: Path) -> tuple[dict, str]:
    """(front matter, body) of one post file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: starts without its --- front matter (title, category)")
    head, _, body = text[4:].partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    if not meta.get("title") or not meta.get("category"):
        raise ValueError(f"{path.name}: the front matter needs a title and a category")
    return meta, body.strip() + "\n"


def main(post: bool) -> None:
    posted = json.loads(POSTED.read_text(encoding="utf-8")) if POSTED.is_file() else {}
    repo = graphql("query($owner: String!, $name: String!) { repository(owner: $owner, name: $name) { id "
                   "discussionCategories(first: 50) { nodes { id name } } } }", owner=REPO[0], name=REPO[1])["repository"]
    categories = {c["name"]: c["id"] for c in repo["discussionCategories"]["nodes"]}
    posts = sorted(((path, *read_post(path)) for path in FOLDER.glob("*.md")),
                   key=lambda p: (int(p[1].get("order", 99)), p[0].name))  # "order: 1" in the front matter goes first
    for path, meta, body in posts:
        known = posted.get(path.name)
        if known:
            print(f"update #{known['number']}: {meta['title']}")
            if post:
                graphql("mutation($id: ID!, $title: String!, $body: String!) { updateDiscussion(input: "
                        "{discussionId: $id, title: $title, body: $body}) { discussion { number } } }",
                        id=known["id"], title=meta["title"], body=body)
            continue
        if meta["category"] not in categories:
            sys.exit(f"{path.name}: there's no category {meta['category']!r} (there are: {', '.join(categories)})")
        print(f"create in {meta['category']}: {meta['title']}")
        if post:
            made = graphql("mutation($repo: ID!, $cat: ID!, $title: String!, $body: String!) { createDiscussion(input: "
                           "{repositoryId: $repo, categoryId: $cat, title: $title, body: $body}) "
                           "{ discussion { id number url } } }",
                           repo=repo["id"], cat=categories[meta["category"]], title=meta["title"], body=body)
            d = made["createDiscussion"]["discussion"]
            posted[path.name] = {"id": d["id"], "number": d["number"]}
            POSTED.write_text(json.dumps(posted, indent=2) + "\n", encoding="utf-8")
            print(f"  {d['url']}")
    if not post:
        print("(nothing sent: run with --post to do it)")


if __name__ == "__main__":
    main("--post" in sys.argv[1:])
