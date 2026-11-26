"""The owner's signature on a release (rusemod.releasesig; the legal fixes' Part 7, his decision 26 A of 2026-11-25): a
statement signed with one of his release keys names an update's exact files, and the apps take nothing else as his.
The keys here are the RFC 8032 test vectors' published secrets, never a real key: the release build refuses them."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import tempfile
import tomllib
import unittest
from pathlib import Path

from rusemod import ed25519, releasesig, update

SECRET1 = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")   # RFC 8032 TEST 1
SECRET2 = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")   # RFC 8032 TEST 2
KEYS = {"release-1": ed25519.public_key(SECRET1), "release-2": ed25519.public_key(SECRET2)}
PAYLOAD = {"app": "studio", "version": "0.9.9.0", "tag": "studio-v0.9.9.0", "file": "RUSE-Studio-Setup-0.9.9.0.exe",
           "size": 123456789, "sha256": "ab" * 32, "notes_file": "RUSE-Studio-notes.json", "notes_size": 45678,
           "notes_sha256": "cd" * 32, "required": "0.9.8.17", "commit": "0123456789abcdef0123456789abcdef01234567"}
# the statement above signed with TEST 1's secret: the form the signing tool must make, byte for byte (its own copy of
# the signing code is checked against this same line)
GOLDEN = ("eyJhbGciOiJFZDI1NTE5IiwiYXBwIjoic3R1ZGlvIiwiY29tbWl0IjoiMDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWYwMTIzNDU2"
          "NyIsImZpbGUiOiJSVVNFLVN0dWRpby1TZXR1cC0wLjkuOS4wLmV4ZSIsImtleSI6InJlbGVhc2UtMSIsImtpbmQiOiJydXNlMi1yZWxlYXNl"
          "Iiwibm90ZXNfZmlsZSI6IlJVU0UtU3R1ZGlvLW5vdGVzLmpzb24iLCJub3Rlc19zaGEyNTYiOiJjZGNkY2RjZGNkY2RjZGNkY2RjZGNkY2Rj"
          "ZGNkY2RjZGNkY2RjZGNkY2RjZGNkY2RjZGNkY2RjZGNkY2RjZGNkIiwibm90ZXNfc2l6ZSI6NDU2NzgsInJlcXVpcmVkIjoiMC45LjguMTci"
          "LCJzaGEyNTYiOiJhYmFiYWJhYmFiYWJhYmFiYWJhYmFiYWJhYmFiYWJhYmFiYWJhYmFiYWJhYmFiYWJhYmFiYWJhYmFiYWJhYmFiIiwic2l6"
          "ZSI6MTIzNDU2Nzg5LCJ0YWciOiJzdHVkaW8tdjAuOS45LjAiLCJ2IjoxLCJ2ZXJzaW9uIjoiMC45LjkuMCJ9" "."
          "7JbyUKd8jdAk24KHmdqSJtdZf-qBQGO-itSW_GrTvtXkqi_dlU2wG9jCpUw5kfQI4kD03_6DZ03zAA-_jNs5Bg")


def fits(payload, **found):
    where = {"app": "studio", "version": "0.9.9.0", "tag": "studio-v0.9.9.0", "file": "RUSE-Studio-Setup-0.9.9.0.exe"}
    where.update(found)
    return releasesig.fits(payload, keys=KEYS, **where)


class Statement(unittest.TestCase):
    def test_the_golden_line(self):
        self.assertEqual(releasesig.make(PAYLOAD, SECRET1, "release-1"), GOLDEN)
        payload, why = releasesig.read(GOLDEN, keys=KEYS)
        self.assertEqual(why, "ok")
        self.assertIsNone(fits(payload))
        self.assertEqual({k: v for k, v in payload.items() if k not in ("alg", "kind", "v", "key")}, PAYLOAD)

    def test_a_changed_byte_or_another_key_is_no_signature(self):
        msg, sig = GOLDEN.split(".")
        body = json.loads(releasesig._unb64(msg))
        body["sha256"] = "ac" + "ab" * 31       # another installer, the signature kept
        moved = releasesig._b64(releasesig.canonical(body)) + "." + sig
        flipped = msg + "." + ("A" if sig[0] != "A" else "B") + sig[1:]
        for text, why in ((moved, "doesn't hold"), (flipped, "doesn't hold"),
                          (releasesig.make(PAYLOAD, SECRET1, "release-9"), "key this app doesn't have")):
            with self.subTest(why=why):
                self.assertEqual(releasesig.read(text, keys=KEYS)[0], None)
                self.assertIn(why, releasesig.read(text, keys=KEYS)[1])
        self.assertIsNone(releasesig.read(GOLDEN, keys={})[0])           # no keys yet: nothing is his
        self.assertIsNone(releasesig.read(GOLDEN, keys={"release-1": KEYS["release-2"]})[0])
        self.assertEqual(releasesig.read(releasesig.make(PAYLOAD, SECRET2, "release-2"), keys=KEYS)[1], "ok")  # CONTROL

    def test_a_malformed_file_never_raises_and_is_no_signature(self):
        msg, sig = GOLDEN.split(".")
        spaced = releasesig._b64(json.dumps(json.loads(releasesig._unb64(msg))).encode()) + "." + sig
        doubled = releasesig._b64(releasesig._unb64(msg)[:-1] + b',"v":1}') + "." + sig   # a key twice
        other = releasesig.make(dict(PAYLOAD, size=1), SECRET2, "release-2")
        for text in (b"\x00\xff" * 50, b"x" * (releasesig.MOST + 1), "not a token", "a.b.c", msg + ".", spaced,
                     doubled, GOLDEN + "\n" + other, "", "\n\n", (GOLDEN + "\n") * (releasesig.MOST_LINES + 1),
                     None, 12, "é" + GOLDEN):
            with self.subTest(text=repr(text)[:40]):
                self.assertIsNone(releasesig.read(text, keys=KEYS)[0])
        both = GOLDEN + "\n" + releasesig.make(PAYLOAD, SECRET2, "release-2") + "\n"   # a change of keys: both sign
        self.assertEqual(releasesig.read(both.encode("ascii"), keys=KEYS)[1], "ok")

    def test_a_later_format_line_is_left_alone(self):
        later = releasesig._b64(releasesig.canonical(dict(PAYLOAD, v=2, alg="Ed25519", kind=releasesig.KIND))) + ".AA"
        self.assertEqual(releasesig.read(later + "\n" + GOLDEN, keys=KEYS)[1], "ok")
        self.assertIsNone(releasesig.read(later, keys=KEYS)[0])

    def test_it_fits_only_the_release_it_names(self):
        payload = releasesig.read(GOLDEN, keys=KEYS)[0]
        self.assertIsNone(fits(payload))  # CONTROL
        for found in ({"app": "launcher"}, {"version": "0.9.9.1"}, {"tag": "studio-v0.9.9.1"},
                      {"file": "RUSE-Studio-Setup-0.9.9.1.exe"}):
            with self.subTest(found=found):
                self.assertIsNotNone(fits(payload, **found))
        for change in ({"size": True}, {"size": 0}, {"size": 2 ** 31 + 1}, {"notes_size": "45678"}, {"v": True},
                       {"required": "0.9.9.1"}, {"required": "x"}, {"sha256": "AB" * 32}, {"commit": "0123456"},
                       {"notes_file": "RUSE-Launcher-notes.json"}, {"kind": "ruse2-cheat-list"}, {"extra": 1},
                       {"key": "release-9"}):
            with self.subTest(change=change):
                self.assertIsNotNone(fits(dict(payload, **change)))
        missing = dict(payload)
        missing.pop("commit")
        self.assertIsNotNone(fits(missing))
        self.assertIsNone(fits(dict(payload, required="")))
        self.assertIsNone(fits(dict(payload, required="0.9.9.0")))   # required at its own version


class Required(unittest.TestCase):
    NOTES = ("**0.9.9.1:** newest\n\n- a change\n\n**0.9.9.0:** required\n<!-- required update -->\n\n- why\n\n"
             "**0.9.8.17:** older\n<!-- Required Update -->\n")

    def test_the_threshold_from_the_notes(self):
        self.assertEqual(releasesig.required_in_notes(self.NOTES, "0.9.9.1"), "0.9.9.0")
        self.assertEqual(releasesig.required_in_notes(self.NOTES, "0.9.9.0"), "0.9.9.0")
        self.assertEqual(releasesig.required_in_notes(self.NOTES, "0.9.8.20"), "0.9.8.17")
        self.assertEqual(releasesig.required_in_notes("**0.9.9.1:** plain\n", "0.9.9.1"), "")

    def test_who_installs_it_by_itself(self):
        payload = dict(PAYLOAD, required="0.9.8.17")
        self.assertTrue(releasesig.required_for(payload, "0.9.8.16"))
        self.assertFalse(releasesig.required_for(payload, "0.9.8.17"))  # already at the threshold
        self.assertFalse(releasesig.required_for(payload, "0.9.8.22"))
        self.assertFalse(releasesig.required_for(dict(PAYLOAD, required=""), "0.1.0"))


class Keys(unittest.TestCase):
    def file(self, text):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = Path(d.name) / "release_keys.toml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_a_release_build_needs_two_real_keys(self):
        good = {"release-1": bytes(range(32)), "release-2": bytes(range(1, 33))}
        good = {k: ed25519.public_key(v) for k, v in good.items()}   # two points nobody published the secrets of
        self.assertIsNone(releasesig.keys_ready(good))  # CONTROL
        for keys, why in (({}, "aren't in"), ({"release-1": good["release-1"]}, "aren't in"),
                          ({"release-1": good["release-1"], "release-2": good["release-1"]}, "the same"),
                          (dict(good, **{"release-2": KEYS["release-2"]}), "published test key"),
                          (dict(good, **{"release-2": b"\xff" * 31 + b"\x7f"}), "isn't an Ed25519 public key"),  # y >= p
                          (dict(good, **{"release-2": bytes(16)}), "isn't an Ed25519 public key")):
            with self.subTest(why=why):
                self.assertIn(why, releasesig.keys_ready(keys) or "")

    def test_the_keys_file(self):
        hex1, hex2 = (ed25519.public_key(bytes([n]) * 32).hex() for n in (7, 9))
        path = self.file(f'[keys]\nrelease-1 = "{hex1}"\nrelease-2 = "{hex2}"\n')
        self.assertEqual(sorted(releasesig.load_keys(path)), ["release-1", "release-2"])
        self.assertIsNone(releasesig.keys_ready(path=path))
        wrong = self.file(f'[keys]\nrelease-1 = "{hex1.upper()}"\nrelease-2 = "{hex2}"\n')
        self.assertIn("release-1", releasesig.keys_ready(path=wrong))
        self.assertEqual(sorted(releasesig.load_keys(wrong)), ["release-2"])

    def test_the_shipped_file_holds_public_halves_only(self):
        data = tomllib.loads(releasesig.KEYS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(sorted(data), ["keys"])
        for name, value in data["keys"].items():
            with self.subTest(name=name):
                self.assertTrue(value == "" or releasesig._HEX64.fullmatch(value), value)
        self.assertFalse(set(releasesig.RELEASE_KEYS.values()) & releasesig.TEST_PUBLICS)
        self.assertEqual(releasesig.TEST_PUBLICS, {KEYS["release-1"], KEYS["release-2"]})

    def test_the_apps_and_the_statement_read_versions_alike(self):
        self.assertIs(update.TAG_VERSION, releasesig.TAG_VERSION)
        self.assertEqual(releasesig.SUFFIX, ".sig")


if __name__ == "__main__":
    unittest.main()
