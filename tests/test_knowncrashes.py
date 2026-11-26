"""Our list of the game crashes we know (rusemod.knowncrashes) and the crash code for players without Bug Watch
(rusemod.crashcode): the list read as data only, its signature, keeping it on the PC, fetching it (to a fake: no
network), the troubleshooter's line, and the code made and read back.

The list here is MadeUp: the same reasons and the same ties as the real list's places, every number made up (the
private list's own test checks that none is one of the real list's). Its signature is made with the published test
key of RFC 8032 (section 7.1, test 1), which nothing trusts: no key of ours is made or read here.

Checked our_tools.json: none of its tools makes or checks the list or the crash code; these tests read no program and
no real crash report.
"""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import ast
import json
import os
import socket
import ssl
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rusemod import bugwatch, crashcode, ed25519, home as homes, knowncrashes, net, owned  # noqa: E402

# RFC 8032, section 7.1, TEST 1: a published test key (its secret is in the RFC); no list the apps take is signed with it
TEST_SECRET = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
TEST_PUBLIC = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
# RFC 8032, section 7.1, TEST 2: the other published test key
TEST2_PUBLIC = bytes.fromhex("3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c")
# a key made for this test file alone: no one else holds its secret, so key_ready may pass it
OWN_SECRET = bytes(range(1, 33))
OWN_PUBLIC = ed25519.public_key(OWN_SECRET)


class MadeUp:
    """A made-up list of known crashes: one place for each of the real list's (the same reason, the same ties: what
    the chain and the rest of the stack must hold), every number made up."""
    BUILD = (0x2000000, 0x12345, 0x5678)
    BUILDS = (BUILD, (BUILD[0] + 0x1000,) + BUILD[1:])     # (a second build, one page longer)
    CREATING = (0x30000, 0x30400)                            # the unit-creation step
    PART = (0x41000, 0x41080)                                # a model's part found by its name
    TWO_AXIS = ((0x52000, 0x52080), (0x53000, 0x53080))      # a two-axis turret's two steps
    KINDS = (0x610000, 0x610100, 0x610200)                   # the unit descriptions' kinds
    NUMBER_AT = 0x20                                         # where a unit description holds its number
    PLACES = {                                               # {offset: (reason, chain groups, stack groups)}
        0x70010: ("made", (), ((CREATING,),)),
        0x71020: ("turret", ((PART,), TWO_AXIS), ()),
        0x72030: ("turret", (), ()),
        0x73040: ("setup", (), ()),
        0x41040: ("part", (TWO_AXIS,), ()),
        0x74050: ("mesh", (), ()),
    }

    @classmethod
    def data(cls, n: int = 7) -> dict:
        return {"v": 1, "n": n, "builds": [list(b) for b in cls.BUILDS],
                "places": [{"at": at, "why": why, "chain": [[list(r) for r in g] for g in chain],
                            "stack": [[list(r) for r in g] for g in stack]}
                           for at, (why, chain, stack) in sorted(cls.PLACES.items())],
                "creating": list(cls.CREATING), "kinds": list(cls.KINDS), "number_at": cls.NUMBER_AT}

    @classmethod
    def text(cls, n: int = 7, data: dict | None = None) -> str:
        return json.dumps(data if data is not None else cls.data(n), separators=(",", ":"))

    @classmethod
    def blob(cls, n: int = 7, text: str | None = None, secret: bytes = TEST_SECRET,
             prefix: bytes = knowncrashes.PREFIX) -> bytes:
        """The list as the server serves it, {"list", "sig"}, signed with `secret` under `prefix`."""
        text = cls.text(n) if text is None else text
        sig = ed25519.sign(secret, prefix + text.encode("utf-8")).hex()
        return json.dumps({"list": text, "sig": sig}).encode("utf-8")

    @classmethod
    def known(cls, n: int = 7):
        return knowncrashes.parse(cls.text(n))

    @classmethod
    def keep(cls, home, n: int = 7, checked: float | None = None) -> Path:
        """The list kept on this PC as a fetch leaves it (<home>/bugwatch/known-crashes.json)."""
        body = json.loads(cls.blob(n))
        body["checked"] = int(time.time() if checked is None else checked)
        path = Path(home) / bugwatch.FOLDER / knowncrashes.LIST_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body), encoding="utf-8")
        return path


class Answer:
    def __init__(self, body: bytes, status=200):
        self.body, self.status = body, status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, most=-1):
        return self.body if most < 0 else self.body[:most]


class ListServer:
    """A fake of the Bug Watch server's list address: answers every request with `body` (or raises `error`), and
    keeps each request it was sent."""

    def __init__(self, body: bytes | None = None, error: Exception | None = None, before=None):
        self.body, self.error, self.before, self.asked = body, error, before, []

    def __call__(self, req, timeout=None):
        self.asked.append(req)
        if self.before is not None:
            self.before()
        if self.error is not None:
            raise self.error
        return Answer(self.body)


class NoNetwork:
    """net.urlopen's stand-in for every test (a test that fetches gives its own fake): a request that reaches here is
    kept and refused as no internet would refuse it, and the test fails at its end (refresh never raises, so a raise
    alone would go unseen)."""

    def __init__(self):
        self.reached = []

    def __call__(self, req, timeout=None):
        self.reached.append(getattr(req, "full_url", str(req)))
        raise OSError("no network in tests")


def keep_off_the_network(test: unittest.TestCase) -> NoNetwork:
    """Patch net.urlopen with a NoNetwork for `test`, and the list key with the test key; the test fails at its end
    if anything reached for the network."""
    stand = NoNetwork()
    for target, name, value in ((net, "urlopen", stand), (knowncrashes, "KEY", TEST_PUBLIC)):
        patcher = mock.patch.object(target, name, value)
        patcher.start()
        test.addCleanup(patcher.stop)
    test.addCleanup(lambda: test.assertEqual(stand.reached, [], "a test reached for the network"))
    return stand


class ListTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TEMP"))
        self.home = Path(self.tmp.name)
        self._on = bugwatch.ON
        bugwatch.ON = True
        os.environ.pop("RUSE_NO_BUGWATCH", None)
        self.no_network = keep_off_the_network(self)   # (and the owner's key, once made, stands as the test key)

    def tearDown(self):
        bugwatch.ON = self._on
        self.tmp.cleanup()

    def accept(self, version):
        values = homes.settings(self.home)
        values["guard"] = {"terms": version}
        homes.save_settings(self.home, values)

    def kept_file(self) -> Path:
        return self.home / bugwatch.FOLDER / knowncrashes.LIST_FILE


class Parse(ListTest):
    def test_the_made_up_list_is_read(self):
        known = MadeUp.known()
        self.assertEqual(known.n, 7)
        self.assertEqual(known.builds, frozenset(MadeUp.BUILDS))
        self.assertEqual(known.places, MadeUp.PLACES)
        self.assertEqual((known.creating, known.kinds, known.number_at),
                         (MadeUp.CREATING, frozenset(MadeUp.KINDS), MadeUp.NUMBER_AT))
        self.assertEqual({why for why, _c, _s in known.places.values()}, set(knowncrashes.REASONS))

    def changed(self, change) -> str:
        data = MadeUp.data()
        change(data)
        return json.dumps(data)

    def test_anything_but_the_one_shape_is_refused(self):
        def place(i, **over):
            return lambda d: d["places"][i].update(over)

        def set_(key, value):
            return lambda d: d.__setitem__(key, value)
        refused = {
            "not json": "{not json",
            "a key twice": MadeUp.text()[:-1] + ',"n":8}',
            "NaN": MadeUp.text().replace('"number_at":32', '"number_at":NaN'),
            "a number with a point": MadeUp.text().replace('"number_at":32', '"number_at":32.0'),
            "version 2": self.changed(set_("v", 2)),
            "version true": self.changed(set_("v", True)),
            "n 0": self.changed(set_("n", 0)),
            "n true": self.changed(set_("n", True)),
            "n a string": self.changed(set_("n", "7")),
            "a build of two numbers": self.changed(lambda d: d["builds"].append([1, 2])),
            "a number below 0": self.changed(lambda d: d["kinds"].append(-1)),
            "a number of 2**32": self.changed(lambda d: d["kinds"].append(2 ** 32)),
            "a bool for a number": self.changed(lambda d: d["kinds"].append(True)),
            "a range out of order": self.changed(set_("creating", [0x30400, 0x30000])),
            "an empty range": self.changed(set_("creating", [5, 5])),
            "a group with no range": self.changed(place(0, stack=[[]])),
            "a part missing": self.changed(lambda d: d.pop("kinds")),
            "a part too many": self.changed(set_("run", "this")),
            "a place with a part too many": self.changed(place(0, code="x")),
            "a place twice": self.changed(lambda d: d["places"].append(dict(d["places"][0]))),
            "a reason that isn't words": self.changed(place(0, why=3)),
            "too many builds": self.changed(set_("builds", [[i, 1, 2] for i in range(17)])),
            "too many places": self.changed(set_("places", [{"at": i, "why": "mesh", "chain": [], "stack": []}
                                                            for i in range(257)])),
            "too many groups": self.changed(place(0, chain=[[[1, 2]]] * 9)),
            "too many ranges": self.changed(place(0, chain=[[[1, 2]] * 65])),
            "too many kinds": self.changed(set_("kinds", list(range(65)))),
            "over 64 KB": self.changed(place(0, why="x" * knowncrashes.MOST_BYTES)),   # (fine but for its size)
            "not an object": "[1, 2]",
        }
        for name, text in refused.items():
            self.assertIsNone(knowncrashes.parse(text), name)
        self.assertIsNotNone(knowncrashes.parse(MadeUp.text()))   # (the control)

    def test_deeply_nested_text_is_no_list_and_raises_nothing(self):
        self.assertIsNone(knowncrashes.parse("[" * 200_000))
        self.assertIsNone(knowncrashes.checked('{"list": "' + "[" * 200_000 + '"}'))

    def test_a_place_with_a_reason_the_apps_have_no_words_for_is_left_out(self):
        text = self.changed(lambda d: d["places"].append({"at": 0x75060, "why": "new-kind", "chain": [],
                                                           "stack": []}))
        known = knowncrashes.parse(text)
        self.assertNotIn(0x75060, known.places)
        self.assertEqual(known.places, MadeUp.PLACES)              # the rest kept

    def test_an_empty_list_is_a_list(self):
        """Taking the list away from the players: an empty list with a higher number (a 404 leaves each app's
        copy)."""
        known = knowncrashes.parse(json.dumps({"v": 1, "n": 9, "builds": [], "places": [], "creating": [1, 2],
                                               "kinds": [], "number_at": 0}))
        self.assertEqual((known.n, known.places, known.builds), (9, {}, frozenset()))

    def test_the_list_is_data_and_this_code_holds_no_number_of_the_game(self):
        """A cheap check of the one file (the private leak scan is the guard): no whole number of 65,536 or more is
        written in rusemod/knowncrashes.py (its limits are written as products)."""
        source = Path(knowncrashes.__file__).read_text(encoding="utf-8")
        big = [n.value for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant)
               and type(n.value) is int and n.value >= 0x10000]
        self.assertEqual(big, [])
        self.assertNotIn("eval(", source)
        self.assertNotIn("exec(", source)


class Signature(ListTest):
    def test_the_test_key_is_the_published_one(self):
        self.assertEqual(ed25519.public_key(TEST_SECRET), TEST_PUBLIC)

    def test_a_list_signed_with_the_key_passes(self):
        self.assertEqual(knowncrashes.checked(MadeUp.blob()).places, MadeUp.PLACES)
        with mock.patch.object(knowncrashes, "KEY", None):
            self.assertIsNotNone(knowncrashes.checked(MadeUp.blob(), key=TEST_PUBLIC))

    def test_the_key_is_read_when_a_list_is_checked(self):
        """checked's key=None reads KEY at the call (a default key=KEY would keep the value of when the code
        loaded, and a patch, or the owner's key put in later, would be ignored)."""
        other = ed25519.public_key(bytes(range(32)))
        with mock.patch.object(knowncrashes, "KEY", other):
            self.assertIsNone(knowncrashes.checked(MadeUp.blob()))
        self.assertIsNotNone(knowncrashes.checked(MadeUp.blob()))

    def test_a_list_that_isnt_ours_word_for_word_is_refused(self):
        good = json.loads(MadeUp.blob())
        changed = dict(good, list=good["list"].replace('"n":7', '"n":8'))
        refused = {
            "one changed byte": json.dumps(changed),
            "no signature": json.dumps({"list": good["list"]}),
            "a short signature": json.dumps(dict(good, sig=good["sig"][:-2])),
            "a signature in capitals": json.dumps(dict(good, sig=good["sig"].upper())),
            "signed under the unlock codes' prefix": MadeUp.blob(prefix=owned.UNLOCK_PREFIX),
            "signed with another key": MadeUp.blob(secret=bytes(range(32))),
            "a part too many": json.dumps(dict(good, run="this")),
            "not an object": "[]",
        }
        for name, blob in refused.items():
            self.assertIsNone(knowncrashes.checked(blob), name)
        known, why, _sig = knowncrashes._checked(json.dumps(changed))
        self.assertEqual((known, why), (None, "signature"))

    def test_what_is_signed_is_apart_from_the_unlock_codes(self):
        """The list's signatures can't stand for an unlock code's, nor the other way round: neither prefix starts
        the other (the unlock codes' key is another key as well: TheShippedKey)."""
        self.assertFalse(knowncrashes.PREFIX.startswith(owned.UNLOCK_PREFIX))
        self.assertFalse(owned.UNLOCK_PREFIX.startswith(knowncrashes.PREFIX))

    def test_until_the_owner_makes_the_key_a_list_is_taken_on_https_alone(self):
        """The released state until his key exists: KEY None, and a list with no signature is taken (the design's
        HTTPS-only path); once KEY is set, the same list is refused."""
        unsigned = json.dumps({"list": MadeUp.text()})
        with mock.patch.object(knowncrashes, "KEY", None):
            self.assertIsNotNone(knowncrashes.checked(unsigned))
        self.assertIsNone(knowncrashes.checked(unsigned))


class TheShippedKey(unittest.TestCase):
    def test_the_apps_key_is_none_or_a_public_key(self):
        """No patch here: the key the apps carry. None until the owner makes the list key (publish.py --new-key, on
        his PC), then its 32-byte public half."""
        key = knowncrashes.KEY
        self.assertTrue(key is None or (isinstance(key, bytes) and len(key) == 32), key)
        self.assertNotEqual(key, owned.UNLOCK_PUBLIC_KEY)          # a key of its own, never the unlock codes'


class Load(ListTest):
    def test_a_missing_broken_or_wrongly_signed_file_is_no_list(self):
        self.assertIsNone(knowncrashes.load(self.home))
        path = MadeUp.keep(self.home)
        self.assertEqual(knowncrashes.load(self.home).n, 7)
        path.write_text("{broken", encoding="utf-8")
        self.assertIsNone(knowncrashes.load(self.home))
        body = json.loads(MadeUp.blob(secret=bytes(range(32))))
        path.write_text(json.dumps(dict(body, checked=1)), encoding="utf-8")
        self.assertIsNone(knowncrashes.load(self.home))

    def test_a_file_the_other_app_is_putting_in_place_is_read_again(self):
        MadeUp.keep(self.home)
        real, calls = Path.read_bytes, []

        def read_bytes(path):
            calls.append(path.name)
            if len(calls) == 1:
                raise PermissionError(13, "held")
            return real(path)
        with mock.patch.object(Path, "read_bytes", read_bytes):
            self.assertEqual(knowncrashes.load(self.home).n, 7)
        self.assertEqual(len(calls), 2)

    def test_load_never_raises(self):
        MadeUp.keep(self.home)
        with mock.patch.object(Path, "read_bytes", side_effect=RuntimeError("anything")):
            self.assertIsNone(knowncrashes.load(self.home))
        with mock.patch.object(Path, "read_bytes", side_effect=PermissionError(13, "held")):
            self.assertIsNone(knowncrashes.load(self.home))   # (held both times: no list, no error)


class Refresh(ListTest):
    def setUp(self):
        super().setUp()
        bugwatch.turn_on(self.home, "Nick")
        self.accept(5)

    def last(self) -> str:
        return json.loads((self.home / bugwatch.FOLDER / knowncrashes.LAST_FILE).read_text())["result"]

    def test_only_with_bug_watch_on_and_version_5_accepted(self):
        server = ListServer(MadeUp.blob())
        self.accept(4)
        self.assertEqual(knowncrashes.refresh(self.home, server), "off")
        self.accept(5)
        os.environ["RUSE_NO_BUGWATCH"] = "1"
        try:
            self.assertEqual(knowncrashes.refresh(self.home, server), "off")
        finally:
            os.environ.pop("RUSE_NO_BUGWATCH")
        bugwatch.turn_off(self.home)
        self.assertEqual(knowncrashes.refresh(self.home, server), "off")
        self.assertEqual(server.asked, [])                        # never asked
        self.assertFalse(self.kept_file().exists())

    def test_one_get_of_one_address_with_nothing_about_the_player(self):
        server = ListServer(MadeUp.blob())
        self.assertEqual(knowncrashes.refresh(self.home, server, clock=lambda: 1000.0), "new")
        (req,) = server.asked
        self.assertEqual((req.get_method(), req.full_url), ("GET", bugwatch.SERVER + knowncrashes.ROUTE))
        self.assertTrue(req.full_url.startswith("https://"))
        self.assertNotIn("?", req.full_url)
        self.assertEqual(req.header_items(), [("User-agent", "RUSE-Bug-Watch")])
        self.assertIsNone(req.data)
        player = homes.settings(self.home)["player"]
        said = req.full_url + json.dumps(req.header_items())
        for secret in (player["id"], player["id"][:8], player["name"], "Nick"):
            self.assertNotIn(secret, said)
        kept = json.loads(self.kept_file().read_text())
        self.assertEqual((kept["checked"], knowncrashes.load(self.home).n), (1000, 7))
        self.assertEqual(self.last(), "new")

    def test_a_list_checked_less_than_a_day_ago_isnt_asked_for_again(self):
        server = ListServer(MadeUp.blob())
        knowncrashes.refresh(self.home, server, clock=lambda: 1000.0)
        self.assertEqual(knowncrashes.refresh(self.home, server, clock=lambda: 1000.0 + knowncrashes.FRESH - 1),
                         "fresh")
        self.assertEqual(len(server.asked), 1)
        self.assertEqual(knowncrashes.refresh(self.home, server, clock=lambda: 1000.0 + knowncrashes.FRESH),
                         "same")                                  # a day on: asked again, the same list
        self.assertEqual(json.loads(self.kept_file().read_text())["checked"], 1000 + knowncrashes.FRESH)
        self.assertEqual(knowncrashes.refresh(self.home, server, clock=lambda: 500.0), "same")   # a clock gone back
        self.assertEqual(len(server.asked), 3)

    def test_freshness_comes_from_the_check_never_from_the_files_time(self):
        """A kept file written just now but whose signature fails is no list: it's asked for again."""
        path = MadeUp.keep(self.home)
        body = json.loads(path.read_text())
        path.write_text(json.dumps(dict(body, sig="0" * 128)), encoding="utf-8")
        server = ListServer(MadeUp.blob())
        self.assertEqual(knowncrashes.refresh(self.home, server), "new")
        self.assertEqual(len(server.asked), 1)

    def test_each_failure_says_its_kind_and_leaves_the_kept_list(self):
        kept = MadeUp.keep(self.home, n=7, checked=1)            # (a day old and more: asked for again)
        before = kept.read_bytes()
        cases = {
            "failed:none": ListServer(error=urllib.error.HTTPError("u", 404, "no", {}, None)),
            "failed:http-503": ListServer(error=urllib.error.HTTPError("u", 503, "busy", {}, None)),
            "failed:offline": ListServer(error=socket.timeout("timed out")),
            "failed:certificate": ListServer(error=urllib.error.URLError(ssl.SSLCertVerificationError(1, "no"))),
            "failed:size": ListServer(b" " * (knowncrashes.MOST_BYTES + 1)),
            "failed:shape": ListServer(MadeUp.blob(text='{"v": 1}')),   # (signed: only its shape is wrong)
            "failed:signature": ListServer(MadeUp.blob(secret=bytes(range(32)))),
            "failed:older": ListServer(MadeUp.blob(n=6)),
        }
        for want, server in cases.items():
            self.assertEqual(knowncrashes.refresh(self.home, server), want)
            self.assertEqual(kept.read_bytes(), before, want)      # byte for byte
            self.assertEqual(self.last(), want)
        self.assertEqual(knowncrashes.refresh(self.home, ListServer(MadeUp.blob(n=8))), "new")   # (the control)
        self.assertEqual(knowncrashes.load(self.home).n, 8)

    def test_a_file_held_by_the_other_app_leaves_the_kept_list(self):
        kept = MadeUp.keep(self.home, n=7, checked=1)
        before = kept.read_bytes()
        with mock.patch.object(knowncrashes.os, "replace", side_effect=PermissionError(5, "held")) as replace, \
                mock.patch.object(knowncrashes.time, "sleep"):
            self.assertEqual(knowncrashes.refresh(self.home, ListServer(MadeUp.blob(n=8))), "failed:busy")
        self.assertEqual(replace.call_count, knowncrashes.BUSY_TRIES)
        self.assertEqual(kept.read_bytes(), before)
        self.assertEqual(list((self.home / bugwatch.FOLDER).glob(knowncrashes.TEMP_GLOB)), [])

    def test_an_untick_while_it_downloads_leaves_nothing_behind(self):
        """The player unticks Bug Watch (in this app or the other) while the list is on its way: no list, no
        result and no file of its own stays."""
        server = ListServer(MadeUp.blob(), before=lambda: bugwatch.turn_off(self.home))
        self.assertEqual(knowncrashes.refresh(self.home, server), "off")
        folder = self.home / bugwatch.FOLDER
        self.assertEqual(sorted(p.name for p in folder.iterdir()) if folder.is_dir() else [], [])

    def test_unticking_deletes_the_kept_list(self):
        knowncrashes.refresh(self.home, ListServer(MadeUp.blob()))
        self.assertTrue(self.kept_file().exists())
        bugwatch.turn_off(self.home)
        self.assertFalse(self.kept_file().exists())
        self.assertIsNone(knowncrashes.load(self.home))

    def test_the_download_goes_through_the_apps_own_opener(self):
        """net.urlopen, with its certificate fallbacks, as every other download of the apps."""
        server = ListServer(MadeUp.blob())
        with mock.patch.object(net, "urlopen", server):
            self.assertEqual(knowncrashes.refresh(self.home), "new")
        self.assertEqual(len(server.asked), 1)

    def test_refresh_never_raises(self):
        with mock.patch.object(knowncrashes, "_kept", side_effect=RuntimeError("anything")):
            self.assertEqual(knowncrashes.refresh(self.home, ListServer(MadeUp.blob())), "failed:error")


class Checking(ListTest):
    def test_a_place_is_told_only_with_its_ties_and_its_build(self):
        known = MadeUp.known()
        b = MadeUp.BUILD
        turret = MadeUp.TWO_AXIS[1][0] + 4
        self.assertEqual(knowncrashes.reason(known, b, 0x41040, [turret]), "part")
        self.assertIsNone(knowncrashes.reason(known, b, 0x41040, [0x40]))           # reached from elsewhere
        self.assertIsNone(knowncrashes.reason(known, b[:2] + (b[2] + 1,), 0x41040, [turret]))   # another build
        self.assertIsNone(knowncrashes.reason(None, b, 0x41040, [turret]))           # no list
        made = MadeUp.CREATING[0] + 8
        self.assertEqual(knowncrashes.reason(known, b, 0x70010, [0x40], [0x40, made]), "made")   # deeper than the chain
        self.assertIsNone(knowncrashes.reason(known, b, 0x70010, [0x40], [0x40]))
        self.assertEqual(knowncrashes.reason(known, MadeUp.BUILDS[1], 0x74050), "mesh")
        self.assertTrue(knowncrashes.knows_build(known, list(b)))
        self.assertFalse(knowncrashes.knows_build(known, None))

    def test_no_unit_without_a_list(self):
        self.assertIsNone(knowncrashes.unit_number(None, MadeUp.BUILD, 0, [1, 2], lambda a, s: None, lambda o: True))


class Findings(ListTest):
    def test_the_troubleshooters_line(self):
        self.assertEqual(knowncrashes.findings(self.home), [])   # Bug Watch off: no line
        bugwatch.turn_on(self.home, "Nick")
        self.accept(4)
        self.assertEqual(knowncrashes.findings(self.home), [])   # before version 5 nothing is fetched: nothing to say
        self.accept(5)
        (none,) = knowncrashes.findings(self.home)
        self.assertEqual((none["key"], none["level"], none["say"], none["data"]),
                         ("crash_list", "info", "doc_crashlist_missing", {"last": "none yet"}))
        knowncrashes.refresh(self.home, ListServer(error=socket.timeout("t")))
        self.assertEqual(knowncrashes.findings(self.home)[0]["data"], {"last": "failed:offline"})
        knowncrashes.refresh(self.home, ListServer(MadeUp.blob()), clock=lambda: 86400.0 * 3)
        (on,) = knowncrashes.findings(self.home)
        self.assertEqual((on["say"], on["data"]), ("doc_crashlist_on", {"n": 7, "checked": "1970-01-04 00:00 UTC"}))
        said = json.dumps(knowncrashes.findings(self.home))
        for number in [MadeUp.CREATING[0], *MadeUp.KINDS, *MadeUp.PLACES]:   # never a number of the list
            self.assertNotIn(str(number), said)

    def test_both_apps_have_its_words_in_every_language(self):
        import re
        import tomllib
        from rusemod import schema
        root = Path(__file__).resolve().parents[1] / "src"
        for app in ("ruse_launcher", "ruse_studio"):
            words = tomllib.loads((root / app / "words.toml").read_text(encoding="utf-8"))
            for key in ("doc_crashlist_on", "doc_crashlist_missing"):
                self.assertEqual(sorted(words[key]), sorted(schema.APP_LANGS), f"{app} {key}")
                blanks = {tuple(sorted(re.findall(r"\{(\w+)\}", t))) for t in words[key].values()}
                self.assertEqual(len(blanks), 1, f"{app} {key}")

    def test_the_troubleshooter_of_each_app_says_it(self):
        """Both apps' troubleshooters (no game folder needed for it): the line with Bug Watch on, in the report too
        (its key and data, English for every language), and none with it off."""
        from ruse_launcher.api import LauncherApi
        from ruse_studio.api import StudioApi
        home = self.home / "home"

        def apis():
            return (LauncherApi(home=home, find=lambda: None, steam_running=lambda: True),
                    StudioApi(index_path=self.home / "none.sqlite", home=home, find=lambda: None))
        for api in apis():                                         # Bug Watch off: no line
            self.assertNotIn("crash_list", [f["key"] for f in api.troubleshoot()["findings"]])
        bugwatch.turn_on(home, "Nick")
        values = homes.settings(home)
        values["guard"] = {"terms": 5}
        homes.save_settings(home, values)
        for api in apis():
            said = api.troubleshoot()
            self.assertIn("crash_list", [f["key"] for f in said["findings"]], type(api).__name__)
            self.assertIn("[info] crash_list: doc_crashlist_missing (last=none yet)", said["report"])


class TheCrashCode(unittest.TestCase):
    def found(self, **over) -> dict:
        return {"code": "0xc0000005", "module": "RUSE.exe", "offset": "0x70010", "build": list(MadeUp.BUILD),
                **over}

    def test_made_and_read_back(self):
        code = crashcode.make(self.found())
        self.assertRegex(code, r"^[0-9A-HJKMNP-TV-Z]{4}-[0-9A-HJKMNP-TV-Z]{4}-[0-9A-HJKMNP-TV-Z]{4}$")
        self.assertEqual(crashcode.read(code), {"version": 1, "kind": 0xC0000005, "module": "game",
                                                "build": crashcode.build_mark(MadeUp.BUILD), "offset": 0x70010})
        self.assertEqual(crashcode.read(code.lower().replace("-", " ")), crashcode.read(code))   # case, spacing
        self.assertNotEqual(crashcode.make(self.found(offset="0x70011")), code)

    def test_other_modules_kinds_and_builds(self):
        other = crashcode.read(crashcode.make(self.found(module="d3d9.dll", offset="0x1234", code="0x29a")))
        self.assertEqual((other["module"], other["kind"], other["offset"]),
                         (crashcode.module_mark("D3D9.DLL"), 0x29A, 0x1234))
        self.assertTrue(1 <= other["module"] <= 254)
        nowhere = crashcode.read(crashcode.make(self.found(module="?", offset="0x7ff612345678")))
        self.assertEqual((nowhere["module"], nowhere["offset"]), ("none", 0x12345678))
        self.assertEqual(crashcode.read(crashcode.make(self.found(module="_")))["module"], "none")  # read_dump's form
        odd = crashcode.read(crashcode.make(self.found(code="0xdeadbeef")))
        self.assertIsNone(odd["kind"])                              # another kind of stop: said as none of KINDS
        unlisted = crashcode.read(crashcode.make(self.found(build=None)))
        self.assertEqual(unlisted["build"], 0)
        self.assertNotEqual(crashcode.build_mark(MadeUp.BUILDS[1]), 0)
        self.assertIsNone(crashcode.make({"code": "x"}))

    def test_any_one_letter_typed_wrong_is_refused(self):
        alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
        for found in (self.found(), self.found(module="kernelbase.dll", offset="0x3a3b9", code="0x29a")):
            code = crashcode.make(found).replace("-", "")
            for i, c in enumerate(code):
                for other in alphabet:
                    if other != c:
                        self.assertIsNone(crashcode.read(code[:i] + other + code[i + 1:]), (code, i, other))
            self.assertIsNone(crashcode.read(code[:-1]))           # one letter short
            self.assertIsNone(crashcode.read(code + "0"))          # one too many
            self.assertIsNone(crashcode.read(code[:5] + "U" + code[6:]))   # one that doesn't belong

    def test_nothing_of_the_player_goes_in(self):
        """What the code is made from: the kind of stop, the module, the build and the place only. The same crash in
        two players' reports, with every other field theirs, gives the same code."""
        a = self.found(chain=["RUSE.exe+0x1"], traceback="Nick's file", unit=4059, map="IwoGround")
        b = self.found(chain=["RUSE.exe+0x2"], traceback="Ann's", unit=1, map="Edge")
        self.assertEqual(crashcode.make(a), crashcode.make(b))


class TheReleaseBuildNeedsTheListKey(unittest.TestCase):
    """The release build stops while the apps carry no key for the list (the owner, 2026-11-25: "yes for 15 sign")."""

    def test_no_key_fails_the_check(self):
        with mock.patch.object(knowncrashes, "KEY", None):
            self.assertIn("KEY is None", knowncrashes.key_ready())
            self.assertEqual(knowncrashes.main(["--check-key"]), 1)

    def test_a_real_key_passes_and_a_wrong_one_fails(self):
        with mock.patch.object(knowncrashes, "KEY", OWN_PUBLIC):
            self.assertIsNone(knowncrashes.key_ready())
            self.assertEqual(knowncrashes.main(["--check-key"]), 0)
        with mock.patch.object(knowncrashes, "KEY", b"\x01" * 5):
            self.assertIsNotNone(knowncrashes.key_ready())
        self.assertEqual(knowncrashes.main([]), 2)

    def test_a_published_test_key_fails_the_check(self):
        """A key anyone can sign with (the two RFC 8032 test public keys) is never one a release build may carry."""
        for public in (TEST_PUBLIC, TEST2_PUBLIC):
            with mock.patch.object(knowncrashes, "KEY", public):
                self.assertIn("published test key", knowncrashes.key_ready())
                self.assertEqual(knowncrashes.main(["--check-key"]), 1)
            self.assertIn("published test key", knowncrashes.key_ready(public))

    def test_the_own_test_key_is_not_a_published_one(self):
        self.assertNotIn(OWN_PUBLIC, (TEST_PUBLIC, TEST2_PUBLIC))
        self.assertIsNone(knowncrashes.key_ready(OWN_PUBLIC))

    def test_the_two_sets_of_test_keys_are_equal_once_joined(self):
        try:
            from rusemod import releasesig
        except ImportError:
            self.skipTest("rusemod.releasesig is not on this branch (it is on legal/signed-updates): checked once both are in one tree")
        self.assertEqual(set(knowncrashes.TEST_PUBLICS), set(releasesig.TEST_PUBLICS))

    def test_the_crash_code_text_names_no_private_tool(self):
        text = Path(crashcode.__file__).read_text(encoding="utf-8")
        for word in ("crash_fn", "private map", "dump_survey", "crash_site"):
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
