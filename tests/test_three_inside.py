"""The Studio's 3D library inside the Studio (the owner, 2026-11-25, question 28: "Yes, you can download the 3D views
drawing library"): three.js 0.170.0's five files ship in src/ruse_studio/ui/three, exactly the bytes recorded in
THIRD_PARTY_NOTICES.md, so a 3D view loads nothing from the internet, and the words no longer blame the internet."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import hashlib
import mimetypes
import re
import tomllib
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "src" / "ruse_studio" / "ui"
FILES = {"three.module.min.js": 691_648, "addons/controls/OrbitControls.js": 32_134,
         "addons/loaders/GLTFLoader.js": 110_273, "addons/utils/BufferGeometryUtils.js": 31_768, "LICENSE": 1_081}


def recorded() -> dict:
    """{file in ui/three: (bytes, SHA-256, address)} from THIRD_PARTY_NOTICES.md's three.js table."""
    text = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    section = text[text.index("## In the Studio, for its 3D views: three.js"):]
    rows = re.findall(r"^\| [^|]+ \| ui/three/(\S+) \| ([\d,]+) \| ([0-9a-f]{64}) \| (https://\S+) \|$", section, re.M)
    return {name: (int(size.replace(",", "")), sha, url) for name, size, sha, url in rows}


class ShippedInside(unittest.TestCase):
    def test_the_five_files_are_the_recorded_bytes(self):
        rows = recorded()
        self.assertEqual(sorted(rows), sorted(FILES))
        for name, size in FILES.items():
            with self.subTest(name=name):
                data = (UI / "three" / name).read_bytes()
                self.assertEqual((len(data), rows[name][0]), (size, size))
                self.assertEqual(hashlib.sha256(data).hexdigest(), rows[name][1])
                self.assertTrue(rows[name][2].startswith("https://cdn.jsdelivr.net/npm/three@0.170.0/"))
        self.assertIn("src/ruse_studio/ui/three/** -text -diff", (ROOT / ".gitattributes").read_text(encoding="utf-8"))

    def test_nothing_of_it_comes_from_the_internet(self):
        for page in sorted(UI.glob("*.html")) + sorted(UI.glob("*.js")):
            if page.name == "fake-api.js":
                continue
            text = page.read_text(encoding="utf-8")
            with self.subTest(page=page.name):
                self.assertNotRegex(text, r"https?://[^\s\"']*three")
                self.assertNotIn("jsdelivr", text.lower())
        for page in ("index.html", "spike3d.html"):
            text = (UI / page).read_text(encoding="utf-8")
            self.assertIn('"three": "./three/three.module.min.js"', text)
        self.assertIn('"three/addons/": "./three/addons/"', (UI / "index.html").read_text(encoding="utf-8"))
        imported = set()
        for page in UI.glob("*.js"):
            imported |= set(re.findall(r'import\("three/addons/([^"]+)"\)', page.read_text(encoding="utf-8")))
        self.assertGreaterEqual(len(imported), 2)
        for path in imported:
            with self.subTest(path=path):
                self.assertTrue((UI / "three" / "addons" / path).is_file())
        loader = (UI / "three" / "addons" / "loaders" / "GLTFLoader.js").read_text(encoding="utf-8")
        for dep in re.findall(r"from '(\.\.?/[^']+)'", loader):
            self.assertTrue((UI / "three" / "addons" / "loaders" / dep).resolve().is_file(), dep)
        self.assertNotIn("jsdelivr", (ROOT / "SECURITY.md").read_text(encoding="utf-8").lower())

    def test_the_studio_s_self_test_and_its_build_carry_them(self):
        app = (ROOT / "src" / "ruse_studio" / "app.py").read_text(encoding="utf-8")
        for name in FILES:
            self.assertIn(f'"three/{name}"', app)

    def test_modules_are_served_as_javascript_whatever_windows_says(self):
        """A PC whose registry calls .js text/plain would stop every module (maps.js and three.js): the page server
        names the type itself."""
        from rusemod import webui
        for ext in (".js", ".mjs"):
            mimetypes.add_type("text/plain", ext)       # what such a PC's registry tells Python
        server, base = webui.serve(UI)
        try:
            for path in ("maps.js", "three/three.module.min.js", "three/addons/controls/OrbitControls.js"):
                with self.subTest(path=path), urllib.request.urlopen(f"{base}/{path}", timeout=10) as r:
                    self.assertEqual(r.headers.get_content_type(), "text/javascript")
        finally:
            server.shutdown()
            server.server_close()
            for ext in (".js", ".mjs"):
                mimetypes.add_type("text/javascript", ext)


class TheWords(unittest.TestCase):
    INTERNET = re.compile(r"internet|интернет|インターネット|联网|اینترنت", re.I)

    def test_the_two_messages_no_longer_blame_the_internet(self):
        words = tomllib.loads((ROOT / "src" / "ruse_studio" / "words.toml").read_text(encoding="utf-8"))
        for key in ("no_viewer", "decoy_anim_no_3d"):
            for lang, text in words[key].items():
                with self.subTest(key=key, lang=lang):
                    self.assertNotRegex(text, self.INTERNET)
        fake = (UI / "fake-api.js").read_text(encoding="utf-8")
        for line in fake.splitlines():
            if "no_viewer:" in line or "decoy_anim_no_3d:" in line:
                self.assertNotRegex(line.split("no_viewer:")[-1].split("decoy_anim_no_3d:")[-1][:200], self.INTERNET)


if __name__ == "__main__":
    unittest.main()
