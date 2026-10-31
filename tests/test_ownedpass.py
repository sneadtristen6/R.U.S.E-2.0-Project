"""Owned copies, layer 2 (rusemod.ownedpass): "Sign in through Steam". The offline pass check (against a real
worker-made token), the server client, the kept pass, and the window API both apps share.

Checked our_tools.json: its tools study the game's code; these tests only make and check Ed25519 tokens and talk to a
faked server.
"""
import base64
import json
import tempfile
import unittest
from pathlib import Path

from rusemod import owned, ownedpass

ROOT = Path(__file__).resolve().parents[1]
SECRET = bytes(range(32))            # a made-up signing key for the tests; the project's own never leaves its PC
PUBLIC = owned.public_key(SECRET)

# A real token from the ruse-owned worker's own tests (test/owned.test.mjs), signed with a fixed TEST key (seed
# 00..1f). Kept here so this test proves our reader agrees with the server's signer, byte for byte, with no other
# repository. payload: exp 1795981858, iat 1793389858 (a 30-day pass).
WORKER_PUBLIC = bytes.fromhex("03a107bff3ce10be1d70dd18e74bc09967e4d6309ba50d5f1ddc8664125531b8")
WORKER_TOKEN = ("eyJhbGciOiJFZDI1NTE5IiwiYXBwIjoyMTk3MCwiZXhwIjoxNzk1OTgxODU4LCJpYXQiOjE3OTMzODk4NTgsImtpbmQiOiJvd25l"
                "ZCIsInN1YiI6IjAzZWU4NWNiODlkNDU5ZGM2OTc3NWQ5MmIyYTdmMzgyIiwidiI6MSwidmlhIjoic3RlYW0ifQ.eyyphjLdpNR3"
                "YLbLGlCHIPIvXZXldqGJkqhs4PjpDVGwoW2Q9p1PZ6PIm_0rgvxJ1YkDQ8GrZhNbqIp_RDFuCA")
WORKER_IAT, WORKER_EXP = 1793389858, 1795981858


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def make_raw(secret: bytes, msg_text: str) -> str:
    msg = msg_text.encode("utf-8")
    return _b64(msg) + "." + _b64(owned.sign(secret, msg))


def good_payload(now: int = 1_700_000_000) -> dict:
    return {"alg": "Ed25519", "app": ownedpass.APP_ID, "exp": now + 86400, "iat": now,
            "kind": "owned", "sub": "a" * 32, "v": 1, "via": "steam"}


def make_pass(secret: bytes, payload: dict) -> str:
    return make_raw(secret, ownedpass._canonical(payload))


class ReadPass(unittest.TestCase):
    def test_accepts_a_real_worker_token(self):
        payload, why = ownedpass.read_pass(WORKER_TOKEN, WORKER_PUBLIC, now=WORKER_IAT + 10)
        self.assertEqual(why, "ok")
        self.assertEqual(payload["kind"], "owned")
        self.assertEqual(payload["app"], 21970)
        self.assertEqual(payload["via"], "steam")
        self.assertEqual(payload["exp"], WORKER_EXP)

    def test_a_worker_token_past_its_expiry_is_refused(self):
        self.assertEqual(ownedpass.read_pass(WORKER_TOKEN, WORKER_PUBLIC, now=WORKER_EXP)[1], "expired")

    def test_a_worker_token_checked_with_another_key_is_refused(self):
        # the project's real key isn't the test key, so the real reader rejects this test token: the signature is the guard
        self.assertEqual(ownedpass.read_pass(WORKER_TOKEN, ownedpass.PUBLIC_KEY, now=WORKER_IAT + 10)[1], "bad signature")

    def test_a_pass_we_sign_ourselves_checks_out(self):
        payload, why = ownedpass.read_pass(make_pass(SECRET, good_payload()), PUBLIC, now=1_700_000_001)
        self.assertEqual(why, "ok")
        self.assertEqual(payload["sub"], "a" * 32)

    def test_a_tampered_payload_fails_the_signature(self):
        good = good_payload()
        sig = make_pass(SECRET, good).split(".")[1]
        forged = _b64(ownedpass._canonical({**good, "sub": "b" * 32}).encode()) + "." + sig
        self.assertEqual(ownedpass.read_pass(forged, PUBLIC, now=good["iat"])[1], "bad signature")

    def test_another_key_fails_the_signature(self):
        token = make_pass(bytes([7] * 32), good_payload())
        self.assertEqual(ownedpass.read_pass(token, PUBLIC, now=1_700_000_001)[1], "bad signature")

    def test_an_expired_pass_is_refused(self):
        token = make_pass(SECRET, good_payload(now=1_700_000_000))
        self.assertEqual(ownedpass.read_pass(token, PUBLIC, now=1_700_000_000 + 86400)[1], "expired")

    def test_a_pass_for_something_else_is_refused(self):
        for over in ({"kind": "dev"}, {"app": 123}, {"v": 2}):
            token = make_pass(SECRET, {**good_payload(), **over})
            self.assertEqual(ownedpass.read_pass(token, PUBLIC, now=1_700_000_001)[1], "not an owned-copy pass")

    def test_a_non_canonical_payload_is_refused(self):
        # the same fields, signed, but not in the server's canonical order: refused before the signature is trusted
        unsorted = {"via": "steam", "alg": "Ed25519", "app": ownedpass.APP_ID, "exp": 1_700_086_400,
                    "iat": 1_700_000_000, "kind": "owned", "sub": "a" * 32, "v": 1}
        raw = make_raw(SECRET, json.dumps(unsorted, separators=(",", ":")))
        self.assertEqual(ownedpass.read_pass(raw, PUBLIC, now=1_700_000_001)[1], "non-canonical payload")

    def test_malformed_tokens(self):
        for bad in ("not-a-pass", "a.b.c", "!!!.@@@", "", f"{_b64(b'{}')}.!!!"):
            self.assertIsNone(ownedpass.read_pass(bad, PUBLIC, now=1_700_000_001)[0])

    def test_the_apps_carry_a_real_public_key(self):
        self.assertEqual(len(ownedpass.PUBLIC_KEY), 32)
        self.assertNotEqual(ownedpass.PUBLIC_KEY, bytes(32))
        self.assertIsNotNone(owned._unpack(ownedpass.PUBLIC_KEY))  # a point on the curve


class Client(unittest.TestCase):
    def _patch_call(self, fn):
        real = ownedpass._call
        ownedpass._call = fn
        self.addCleanup(setattr, ownedpass, "_call", real)

    def test_start_hands_back_the_code_and_link(self):
        self._patch_call(lambda url, data=None, timeout=30: (200, {
            "code": "C" * 43, "login_url": "https://ruse-owned.example/v1/steam/login?code=" + "C" * 43,
            "poll_every": 3, "expires_in": 600}))
        info = ownedpass.start("https://ruse-owned.example")
        self.assertEqual(info["code"], "C" * 43)
        self.assertIn("/v1/steam/login", info["login_url"])
        self.assertEqual((info["poll_every"], info["expires_in"]), (3, 600))

    def test_start_raises_the_servers_reason_when_off(self):
        self._patch_call(lambda *a, **k: (503, {"ok": False, "live": False, "reason": "Sign in through Steam isn't switched on yet"}))
        with self.assertRaises(ownedpass.OwnedPassError) as caught:
            ownedpass.start("https://ruse-owned.example")
        self.assertIn("switched on", str(caught.exception))

    def test_start_raises_a_plain_message_when_unreachable(self):
        def boom(*a, **k):
            raise OSError("no route")
        self._patch_call(boom)
        with self.assertRaises(ownedpass.OwnedPassError) as caught:
            ownedpass.start("https://ruse-owned.example")
        self.assertIn("reach", str(caught.exception).lower())

    def test_poll_passes_the_servers_answer_through(self):
        self._patch_call(lambda *a, **k: (200, {"status": "owned", "pass": "a.b"}))
        self.assertEqual(ownedpass.poll("https://x", "C" * 43)["status"], "owned")
        self._patch_call(lambda *a, **k: (200, {"status": "pending"}))
        self.assertEqual(ownedpass.poll("https://x", "C" * 43), {"status": "pending"})

    def test_poll_reads_an_unreachable_server_as_steam_error(self):
        def boom(*a, **k):
            raise OSError("down")
        self._patch_call(boom)
        self.assertEqual(ownedpass.poll("https://x", "C" * 43), {"status": "steam-error"})

    def test_fetch_public_reads_the_served_key(self):
        self._patch_call(lambda *a, **k: (200, {"alg": "Ed25519", "public": PUBLIC.hex()}))
        self.assertEqual(ownedpass.fetch_public("https://x"), PUBLIC)
        self._patch_call(lambda *a, **k: (200, {"set_up": False}))
        self.assertIsNone(ownedpass.fetch_public("https://x"))


class KeptPass(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.home, True)

    def test_store_read_and_clear(self):
        self.assertEqual(ownedpass.stored_pass(self.home), "")
        ownedpass.store_pass(self.home, "a.token")
        self.assertEqual(ownedpass.stored_pass(self.home), "a.token")
        ownedpass.clear_pass(self.home)
        self.assertEqual(ownedpass.stored_pass(self.home), "")

    def test_status_with_no_pass(self):
        st = ownedpass.pass_status(self.home)
        self.assertEqual((st["signed_in"], st["owned"], st["reason"]), (False, False, "none"))

    def test_status_with_a_valid_pass(self):
        ownedpass.store_pass(self.home, make_pass(SECRET, good_payload(now=1_700_000_000)))
        st = ownedpass.pass_status(self.home, public=PUBLIC, now=1_700_000_010)
        self.assertTrue(st["signed_in"] and st["owned"])
        self.assertEqual(st["until"], 1_700_086_400)

    def test_status_with_an_expired_pass(self):
        ownedpass.store_pass(self.home, make_pass(SECRET, good_payload(now=1_700_000_000)))
        st = ownedpass.pass_status(self.home, public=PUBLIC, now=1_700_200_000)
        self.assertFalse(st["owned"])
        self.assertEqual(st["reason"], "expired")


class FakeApi(ownedpass.OwnedPassCalls):
    def __init__(self, home, lang="us"):
        self._home = Path(home)
        self._lang = lang
        self.opened = []

    def prefs(self):
        return {"lang": self._lang}

    def _community_open(self, url):
        self.opened.append(url)
        return {"opened": url}


class Mixin(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.addCleanup(__import__("shutil").rmtree, self.home, True)
        self.api = FakeApi(self.home)
        # the tests sign with our made-up key, so point the reader at its public half for the duration
        real_key, real_on = ownedpass.PUBLIC_KEY, ownedpass.ON
        ownedpass.PUBLIC_KEY = PUBLIC
        self.addCleanup(setattr, ownedpass, "PUBLIC_KEY", real_key)
        self.addCleanup(setattr, ownedpass, "ON", real_on)

    def _on(self):
        ownedpass.ON = True

    def test_held_off_nothing_is_gated_and_status_says_so(self):
        ownedpass.ON = False
        self.assertTrue(self.api.owned_pass_ok())
        st = self.api.owned_pass_status()
        self.assertFalse(st["on"])
        self.assertFalse(st["signed_in"])
        self.assertEqual(self.api.owned_sign_in_start(), {"on": False})

    def test_gate_when_on(self):
        self._on()
        self.assertFalse(self.api.owned_pass_ok())  # on, no pass yet
        ownedpass.store_pass(self.home, make_pass(SECRET, good_payload(now=1_700_000_000)))
        self.assertFalse(self.api.owned_pass_ok())  # still false: old pass, now is real time
        ownedpass.store_pass(self.home, make_pass(SECRET, good_payload(now=int(__import__("time").time()))))
        self.assertTrue(self.api.owned_pass_ok())

    def test_sign_in_opens_the_browser_and_returns_the_code(self):
        self._on()
        real = ownedpass.start
        ownedpass.start = lambda server, timeout=30: {"code": "Z" * 43,
                                                      "login_url": "https://ruse-owned.example/v1/steam/login?code=" + "Z" * 43,
                                                      "poll_every": 3, "expires_in": 600}
        self.addCleanup(setattr, ownedpass, "start", real)
        out = self.api.owned_sign_in_start()
        self.assertTrue(out["on"])
        self.assertEqual(out["code"], "Z" * 43)
        self.assertEqual(len(self.api.opened), 1)
        self.assertIn("/v1/steam/login", self.api.opened[0])

    def test_poll_owned_keeps_the_pass(self):
        self._on()
        token = make_pass(SECRET, good_payload(now=int(__import__("time").time())))
        real = ownedpass.poll
        ownedpass.poll = lambda server, code, timeout=30: {"status": "owned", "pass": token}
        self.addCleanup(setattr, ownedpass, "poll", real)
        out = self.api.owned_sign_in_poll("Z" * 43)
        self.assertEqual(out["status"], "owned")
        self.assertTrue(out["owned"])
        self.assertEqual(ownedpass.stored_pass(self.home), token)

    def test_poll_refuses_a_pass_that_doesnt_check_out(self):
        self._on()
        real = ownedpass.poll
        ownedpass.poll = lambda server, code, timeout=30: {"status": "owned", "pass": "garbage.token"}
        self.addCleanup(setattr, ownedpass, "poll", real)
        out = self.api.owned_sign_in_poll("Z" * 43)
        self.assertEqual(out["status"], "bad-pass")
        self.assertEqual(ownedpass.stored_pass(self.home), "")  # nothing kept

    def test_sign_out_forgets_the_pass(self):
        self._on()
        ownedpass.store_pass(self.home, make_pass(SECRET, good_payload(now=int(__import__("time").time()))))
        out = self.api.owned_sign_out()
        self.assertFalse(out["signed_in"])
        self.assertEqual(ownedpass.stored_pass(self.home), "")


class BothApps(unittest.TestCase):
    def test_on_for_the_release(self):
        self.assertTrue(ownedpass.ON)  # switched on with RUSE Guard for the release (the owner, 2026-10-31)

    def test_the_screen_has_every_word_in_all_eleven_languages(self):
        import tomllib
        from rusemod import schema
        table = tomllib.loads(ownedpass._WORDS.read_text(encoding="utf-8"))
        for key, values in table.items():
            self.assertEqual([lang for lang in schema.APP_LANGS if not values.get(lang)], [], key)
        self.assertNotEqual(ownedpass.words("fr")["title"], ownedpass.words("us")["title"])  # translated
        self.assertIn("{date}", ownedpass.words("fa")["until"])   # the placeholder survives every translation
        self.assertEqual(ownedpass.words("xx")["title"], ownedpass.words("us")["title"])  # unknown: English

    def test_both_apps_include_the_calls_and_ship_the_screen(self):
        for app in ("ruse_launcher", "ruse_studio"):
            api_src = (ROOT / "src" / app / "api.py").read_text(encoding="utf-8")
            self.assertIn("OwnedPassCalls", api_src, app)
            app_src = (ROOT / "src" / app / "app.py").read_text(encoding="utf-8")
            self.assertIn('"ownedsignin.js"', app_src, app)
            self.assertIn('<script src="ownedsignin.js"></script>',
                          (ROOT / "src" / app / "ui" / "index.html").read_text(encoding="utf-8"), app)
        self.assertEqual((ROOT / "src/ruse_launcher/ui/ownedsignin.js").read_bytes(),
                         (ROOT / "src/ruse_studio/ui/ownedsignin.js").read_bytes())  # one screen, the same in both


if __name__ == "__main__":
    unittest.main()
