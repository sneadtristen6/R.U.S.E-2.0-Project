"""The mod index (MOD_FORMAT §15, rusemod.mod_index) on a local web server: read, kept for offline, downloads checked."""
import hashlib
import tempfile
import time
import unittest
from pathlib import Path

from test_build import write_mod
from rusemod import package
from rusemod.mod_index import IndexResult, ModIndexError, download, fetch, parse, size_text, states
from rusemod.webui import serve

HALF = {"eco.rndf": "patch $/B ( ProductionPrice *= 0.5 )"}


def toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(toml_value(x) for x in v) + "]"
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def entry(**values) -> str:
    return "[[mod]]\n" + "".join(f"{k} = {toml_value(v)}\n" for k, v in values.items())


def index_for(base: str, file: Path, **more) -> str:
    """An index.toml listing `file` (served under `base`) with its real size and checksum, plus extra entries."""
    data = file.read_bytes()
    text = "format = 1\n\n" + entry(id="econ-half", name="Half price", version="1.0.0", author="Tristen",
                                    description="Every building costs half.", download=f"{base}/{file.name}",
                                    size=len(data), sha256=hashlib.sha256(data).hexdigest(), game_build="24687178",
                                    fingerprint="K7Q2-M9XD", tags=["gameplay", "economy"])
    for e in more.values():
        text += "\n" + e
    return text


class Served(unittest.TestCase):
    """A folder served on this PC: the index, a real package, and files that are wrong on purpose."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.www = self.root / "www"
        self.www.mkdir()
        self.cache = self.root / "cache"
        mod = write_mod(self.root, "econ-half", HALF, extra='name = "Half price"\n')
        self.file = package.pack(mod, self.www)
        (self.www / "wrong.rusemod").write_bytes(b"not the promised bytes")
        self.server, self.base = serve(self.www)
        wrong = entry(id="wrong-sum", name="Wrong checksum", version="2.0.0", download=f"{self.base}/wrong.rusemod",
                      size=22, sha256="0" * 64)
        gone = entry(id="gone", name="Gone", version="1.0.0", download=f"{self.base}/missing.rusemod", size=5, sha256="1" * 64)
        broken = entry(id="Bad Id", name="Bad", version="1.0.0", download="https://x/y", size=1, sha256="2" * 64)
        (self.www / "index.toml").write_text(index_for(self.base, self.file, wrong=wrong, gone=gone, broken=broken), encoding="utf-8")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def test_read_online_and_kept_for_offline(self):
        r = fetch(f"{self.base}/index.toml", self.cache, now=lambda: time.strptime("2026-09-29 20:30", "%Y-%m-%d %H:%M"))
        self.assertEqual((r.source, r.as_of, [m["id"] for m in r.mods]), ("online", "2026-09-29 20:30", ["econ-half", "wrong-sum", "gone"]))
        self.assertEqual(r.problems, ["entry 4 (Bad Id) skipped: the id isn't lowercase letters, digits and -"])
        half = r.mods[0]
        self.assertEqual((half["name"], half["author"], half["size"], half["game_build"], half["tags"]),
                         ("Half price", "Tristen", self.file.stat().st_size, "24687178", ["gameplay", "economy"]))
        self.assertTrue((self.cache / "index.toml").is_file())
        self.server.shutdown()  # offline from now on
        self.server.server_close()
        r = fetch(f"{self.base}/index.toml", self.cache, timeout=2)
        self.assertEqual((r.source, r.as_of, len(r.mods)), ("cache", "2026-09-29 20:30", 3))
        self.assertIn("This is the copy from 2026-09-29 20:30.", r.message)
        with self.assertRaisesRegex(ModIndexError, "no copy from before"):
            fetch(f"{self.base}/index.toml", self.root / "empty", timeout=2)

    def test_a_download_is_checked_against_the_list(self):
        mods, _ = parse((self.www / "index.toml").read_text(encoding="utf-8"))
        by_id = {m["id"]: m for m in mods}
        got = download(by_id["econ-half"], self.root / "downloads")
        self.assertEqual((got.name, got.read_bytes()), ("econ-half-1.0.0.rusemod", self.file.read_bytes()))
        with self.assertRaisesRegex(ModIndexError, "isn't the one the mod list promises"):
            download(by_id["wrong-sum"], self.root / "downloads")
        with self.assertRaisesRegex(ModIndexError, "couldn't be downloaded \\(the server answered 404\\)"):
            download(by_id["gone"], self.root / "downloads")
        self.assertEqual(sorted(p.name for p in (self.root / "downloads").iterdir()), ["econ-half-1.0.0.rusemod"])


class Reading(unittest.TestCase):
    def test_entries_are_checked_one_by_one(self):
        good = entry(id="a", name="A", version="1.0.0", download="https://x/a.rusemod", size=10, sha256="a" * 64)
        text = "format = 1\n" + good + entry(id="a", name="Twice", version="1.0.0", download="https://x/a.rusemod", size=1, sha256="a" * 64)
        text += entry(id="b", version="1.0.0", download="https://x/b", size=1, sha256="b" * 64)  # no name: allowed
        text += entry(id="c", name="C", version="one", download="https://x/c", size=1, sha256="c" * 64)
        text += entry(id="d", name="D", version="1.0", download="ftp://x/d", size=1, sha256="d" * 64)
        text += entry(id="e", name="E", version="1.0", download="https://x/e", size=-1, sha256="e" * 64)
        text += entry(id="f", name="F", version="1.0", download="https://x/f", size=1, sha256="short")
        text += "[[mod]]\nname = \"no id\"\n"
        mods, problems = parse(text)
        self.assertEqual([m["id"] for m in mods], ["a", "b"])
        self.assertEqual(mods[1]["name"], "b")
        self.assertEqual([p.split(": ", 1)[1] for p in problems], [
            "listed twice", "the version isn't like 1.0.0", "the download isn't an https:// link",
            "the size isn't a number of bytes", "the sha256 isn't 64 hex characters",
            "missing id, version, download, size, sha256"])
        with self.assertRaisesRegex(ModIndexError, "can't be read"):
            parse("format = [")
        with self.assertRaisesRegex(ModIndexError, "newer launcher"):
            parse("format = 2\n")

    def test_states_and_sizes(self):
        mods = [{"id": "a", "version": "1.2.0"}, {"id": "b", "version": "1.0.0"}, {"id": "c", "version": "2.0.0"}]
        states(mods, {"a": "1.1.0", "b": "1.0.0", "c": "3.0.0"})
        self.assertEqual([(m["state"], m["installed_version"]) for m in mods], [("update", "1.1.0"), ("installed", "1.0.0"), ("installed", "3.0.0")])
        self.assertEqual(states([{"id": "d", "version": "1.0.0"}], {})[0]["state"], "new")
        self.assertEqual([size_text(n) for n in (0, 999, 12_345, 3_400_000)], ["1 KB", "1 KB", "12 KB", "3.4 MB"])
        self.assertEqual(IndexResult([], "online", "now").problems, [])


if __name__ == "__main__":
    unittest.main()
