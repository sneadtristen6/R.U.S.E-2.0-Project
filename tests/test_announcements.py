"""Every update gets its own announcement and its own public refresh. The owner, 2026-10-09: "There should be a new rule
or guard going forward that each update gets its own like announcement and like fresh up."

The apps' versions in the source are the update being made: the Discussions post (docs/community, posted by
tools/post_discussions.py) and the README's "latest" line have to name them before it goes out."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import post_discussions  # noqa: E402

COMMUNITY = ROOT / "docs" / "community"


def version(app: str) -> str:
    text = (ROOT / "src" / app / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'^__version__ = "([^"]+)"', text, re.M).group(1)


STUDIO, LAUNCHER = version("ruse_studio"), version("ruse_launcher")


def announcements() -> dict[str, tuple[dict, str]]:
    """Every release post that isn't skipped: {file name: (front matter, body)}."""
    posts = {p.name: post_discussions.read_post(p) for p in COMMUNITY.glob("release-*.md")}
    return {name: post for name, post in posts.items() if not post[0].get("skip")}


class OwnAnnouncement(unittest.TestCase):
    def current(self) -> tuple[str, dict, str]:
        found = [(name, meta, body) for name, (meta, body) in announcements().items()
                 if f"RUSE Studio {STUDIO}**" in body and f"RUSE Launcher {LAUNCHER}**" in body]
        self.assertEqual(len(found), 1, f"Studio {STUDIO} / Launcher {LAUNCHER} need their own announcement in "
                                        f"docs/community (release-{STUDIO}.md, naming both versions); found {found}")
        return found[0]

    def test_this_update_has_its_own_post(self):
        name, meta, _ = self.current()
        self.assertEqual(meta["category"], "Announcements")
        self.assertTrue(STUDIO in meta["title"] or LAUNCHER in meta["title"], (name, meta["title"]))

    def test_its_pictures_are_in_the_repo(self):
        _, _, body = self.current()
        pictures = re.findall(r"R\.U\.S\.E-2\.0-Project/main/(docs/images/[^)\s]+)", body)
        self.assertTrue(pictures, "the announcement shows this update's pictures")
        for picture in pictures:
            self.assertTrue((ROOT / picture).is_file(), picture)

    def test_only_this_update_waits_to_be_posted(self):
        """A post not yet sent is this update's or skipped (with why): an old one is never posted by accident."""
        posted = json.loads((COMMUNITY / "posted.json").read_text(encoding="utf-8"))
        name, _, _ = self.current()
        waiting = {p.name for p, _, _ in post_discussions.to_post([])} - set(posted)
        self.assertLessEqual(waiting, {name})

    def test_a_skipped_post_cant_be_sent(self):
        with self.assertRaisesRegex(ValueError, "release-0.9.8.md is skipped"):
            post_discussions.to_post(["release-0.9.8.md"])
        with self.assertRaisesRegex(ValueError, "no post file called nope.md"):
            post_discussions.to_post(["nope.md"])
        self.assertEqual([p.name for p, _, _ in post_discussions.to_post(["release-0.9.7.md"])], ["release-0.9.7.md"])


class Refreshed(unittest.TestCase):
    def test_the_readme_names_this_update(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"(latest: {LAUNCHER})", readme)
        self.assertIn(f"(latest: {STUDIO})", readme)

    def test_the_release_notes_start_with_this_update(self):
        for app, now in (("studio", STUDIO), ("launcher", LAUNCHER)):
            notes = (ROOT / ".github" / "release-notes" / f"{app}.md").read_text(encoding="utf-8")
            first = re.search(r"\*\*(\d+(?:\.\d+)+):\*\*", notes)
            self.assertEqual(first and first.group(1), now, f"{app}.md starts with another version's notes")


if __name__ == "__main__":
    unittest.main()
