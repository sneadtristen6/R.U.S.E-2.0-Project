"""Downloads on a PC whose Windows hasn't fetched GitHub's root certificate yet (rusemod.net): a player on Discord,
2026-10-10, could open the Launcher but no mod would download ("unable to get local issuer certificate"); a player on
Reddit, 2026-10-29, whose Windows couldn't fetch it either ("unable to get issuer certificate"): Mozilla's root list
is the third try."""
import contextlib
import ssl
import sys
import unittest
import urllib.error
import urllib.request
from unittest import mock

from rusemod import mod_index, net


def cert_error(code: int, message: str = "unable to get local issuer certificate") -> urllib.error.URLError:
    exc = ssl.SSLCertVerificationError(1, f"[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: {message}")
    exc.verify_code, exc.verify_message = code, message
    return urllib.error.URLError(exc)


def windows_store(name: str) -> list[bytes]:
    return [cert for cert, kind, _ in ssl.enum_certificates(name) if kind == "x509_asn"]


class Fresh(unittest.TestCase):
    def setUp(self):
        net._asked.clear()
        net._roots.clear()
        net._context = None
        net._mozilla = None
        self.addCleanup(net._asked.clear)
        self.addCleanup(net._roots.clear)
        self.addCleanup(setattr, net, "_context", None)
        self.addCleanup(setattr, net, "_mozilla", None)


class SecondTry(Fresh):
    def test_a_missing_root_is_tried_again_once_windows_trusted_one(self):
        def windows(host):
            net._context = ssl.create_default_context()  # what _ask_windows leaves when Windows trusted a root
            return True
        answers = [cert_error(20), "the mod"]
        with mock.patch("urllib.request.urlopen", side_effect=answers) as opened, \
                mock.patch.object(net, "_ask_windows", side_effect=windows) as asked:
            self.assertEqual(net.urlopen("https://github.com/x/y.rusemod", 10), "the mod")
        asked.assert_called_once_with("github.com")
        self.assertEqual(opened.call_count, 2)
        self.assertNotIn("context", opened.call_args_list[0].kwargs)  # the first try is urllib's own, as before
        self.assertIs(opened.call_args_list[1].kwargs["context"], net._context)

    def test_no_second_try_when_windows_doesnt_trust_it_either(self):
        with mock.patch("urllib.request.urlopen", side_effect=cert_error(20)) as opened, \
                mock.patch.object(net, "_ask_windows", return_value=False), \
                mock.patch.object(net, "_add_mozilla", return_value=False):
            with self.assertRaises(urllib.error.URLError) as caught:
                net.urlopen("https://github.com/x", 10)
        self.assertEqual(caught.exception.reason.verify_code, 20)
        self.assertEqual(opened.call_count, 1)

    def test_mozilla_s_list_when_windows_can_t_fetch_the_root(self):
        # the Reddit player's PC: Windows had the certificate under GitHub's root (ISRG Root X1) but not the root, and
        # couldn't fetch it: "unable to get issuer certificate"
        def mozilla(host):
            net._context = ssl.create_default_context()  # what _add_mozilla leaves
            return True
        answers = [cert_error(2, "unable to get issuer certificate"), "the mod"]
        with mock.patch("urllib.request.urlopen", side_effect=answers) as opened, \
                mock.patch.object(net, "_ask_windows", return_value=False) as windows, \
                mock.patch.object(net, "_add_mozilla", side_effect=mozilla) as added:
            self.assertEqual(net.urlopen("https://release-assets.githubusercontent.com/x.rusemod", 10), "the mod")
        windows.assert_called_once_with("release-assets.githubusercontent.com")  # Windows first
        added.assert_called_once_with("release-assets.githubusercontent.com")
        self.assertEqual(opened.call_count, 2)
        self.assertIs(opened.call_args_list[1].kwargs["context"], net._context)

    def test_mozilla_s_list_after_windows_roots_still_lacked_one(self):
        def widened(host):
            net._context = ssl.create_default_context()
            return True
        answers = [cert_error(20), cert_error(2, "unable to get issuer certificate"), "the mod"]
        with mock.patch("urllib.request.urlopen", side_effect=answers) as opened, \
                mock.patch.object(net, "_ask_windows", side_effect=widened), \
                mock.patch.object(net, "_add_mozilla", side_effect=widened) as added:
            self.assertEqual(net.urlopen("https://github.com/x", 10), "the mod")
        added.assert_called_once()
        self.assertEqual(opened.call_count, 3)

    def test_the_last_failure_is_what_the_player_reads(self):
        def widened(host):
            net._context = ssl.create_default_context()
            return True
        answers = [cert_error(20), cert_error(2, "unable to get issuer certificate"), cert_error(19, "self-signed")]
        with mock.patch("urllib.request.urlopen", side_effect=answers) as opened, \
                mock.patch.object(net, "_ask_windows", side_effect=widened), \
                mock.patch.object(net, "_add_mozilla", side_effect=widened):
            with self.assertRaises(urllib.error.URLError) as caught:
                net.urlopen("https://github.com/x", 10)
        self.assertEqual((caught.exception.reason.verify_code, opened.call_count), (19, 3))

    def test_another_failure_on_a_later_try_isnt_tried_again(self):
        def widened(host):
            net._context = ssl.create_default_context()
            return True
        answers = [cert_error(20), urllib.error.URLError("timed out")]
        with mock.patch("urllib.request.urlopen", side_effect=answers) as opened, \
                mock.patch.object(net, "_ask_windows", side_effect=widened), \
                mock.patch.object(net, "_add_mozilla") as added:
            with self.assertRaises(urllib.error.URLError) as caught:
                net.urlopen("https://github.com/x", 10)
        self.assertEqual(str(caught.exception.reason), "timed out")
        added.assert_not_called()
        self.assertEqual(opened.call_count, 2)

    def test_other_failures_are_not_tried_again(self):
        for exc in (cert_error(10, "certificate has expired"), urllib.error.URLError("timed out"),
                    urllib.error.HTTPError("https://github.com/x", 404, "Not Found", {}, None)):
            with self.subTest(exc=str(exc)), mock.patch("urllib.request.urlopen", side_effect=exc) as opened, \
                    mock.patch.object(net, "_ask_windows") as asked:
                with self.assertRaises(urllib.error.URLError):
                    net.urlopen("https://github.com/x", 10)
                asked.assert_not_called()
                self.assertEqual(opened.call_count, 1)

    def test_which_failures_lack_a_root(self):
        self.assertTrue(net.missing_root(cert_error(20)))
        self.assertTrue(net.missing_root(cert_error(2, "unable to get issuer certificate")))
        self.assertTrue(net.missing_root(cert_error(19, "self-signed certificate in certificate chain")))
        self.assertFalse(net.missing_root(cert_error(10, "certificate has expired")))
        self.assertFalse(net.missing_root(urllib.error.URLError("timed out")))

    def test_the_player_reads_what_to_look_at(self):
        why = mod_index.plain(cert_error(20))
        self.assertIn("doesn't trust the site's security certificate (unable to get local issuer certificate)", why)
        self.assertIn("antivirus", why)


class Tls(Fresh):
    def test_net_s_own_connections_ask_for_tls_1_2_or_newer(self):
        # GitHub's code check (2026-10-11): the certificate reader's context allowed TLS 1.0 and 1.1 by its words
        # (Python 3.12's own lowest is 1.2 already). Both contexts net makes for a connection say 1.2; the first try
        # is urllib's own, Python's lowest
        used = []

        def wrapping(context, raw, server_hostname=None):
            used.append(context)
            raise OSError("no answer")
        with mock.patch("socket.create_connection", return_value=contextlib.nullcontext()), \
                mock.patch.object(ssl.SSLContext, "wrap_socket", autospec=True, side_effect=wrapping):
            with self.assertRaises(OSError):
                net.server_chain("github.com")
        with net._lock:
            used.append(net._widened())
        self.assertEqual([c.minimum_version for c in used], [ssl.TLSVersion.TLSv1_2] * 2)


class EveryDownload(unittest.TestCase):
    def test_every_web_address_is_opened_through_net(self):
        # the Reddit player's fault (2026-10-29) wherever the apps download: the era units and Map Paint's online
        # textures opened their addresses with urllib's own urlopen, so neither Windows nor Mozilla's list was tried
        # there. Only net itself and the self-test's look at its own local server (webui) may call it
        import re
        from pathlib import Path
        src = Path(net.__file__).resolve().parents[1]
        direct = []
        for path in sorted(src.rglob("*.py")):
            if path.name in ("net.py", "webui.py") and path.parent.name == "rusemod":
                continue
            if "python251" in path.parts:
                continue  # Python 2.5.1's own library where a PC has unpacked it: Python 2 code, not the apps'
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"\burllib\.request\.urlopen\(|\bfrom urllib\.request import\b.*\burlopen\b", line):
                    direct.append(f"{path.relative_to(src)}:{n}")
        self.assertEqual(direct, [])


class MozillaList(Fresh):
    PEM = ssl.DER_cert_to_PEM_cert(windows_store("ROOT")[0]) if sys.platform == "win32" else None

    def test_added_once_per_run_beside_windows_roots(self):
        if self.PEM is None:
            self.skipTest("a root to stand in for Mozilla's list comes from Windows here")
        net._roots.append(windows_store("ROOT")[-1])  # one Windows trusted when asked: kept
        self.assertTrue(net._add_mozilla("github.com", roots=self.PEM))
        self.assertIsInstance(net._context, ssl.SSLContext)
        self.assertEqual(net._mozilla, self.PEM)
        self.assertFalse(net._add_mozilla("github.com", roots=self.PEM))  # once per run
        net._asked.discard("example.org")
        # a later root from Windows keeps Mozilla's list in the roots
        with mock.patch.object(net, "server_chain", return_value=[b"x"]), \
                mock.patch.object(net, "windows_roots", return_value=[windows_store("ROOT")[1]]):
            self.assertTrue(net._ask_windows("example.org"))
        self.assertEqual(net._mozilla, self.PEM)

    def test_without_certifi_it_goes_on_without_it(self):
        with mock.patch.object(net, "mozilla_roots", side_effect=ImportError("No module named 'certifi'")):
            self.assertFalse(net._add_mozilla("github.com"))
        self.assertIsNone(net._context)
        self.assertEqual(net._mozilla, "")  # not asked again in this run
        self.assertFalse(net._add_mozilla("github.com"))

    def test_the_apps_list_holds_github_s_roots(self):
        try:
            roots = net.mozilla_roots()
        except ImportError:
            self.skipTest("certifi isn't installed here (the apps carry it: installers/requirements.txt)")
        for name in ("ISRG Root X1", "USERTrust ECC Certification Authority"):  # GitHub's download sites, 2026-10-29
            self.assertIn(f'# Label: "{name}"', roots)
        self.assertRegex(net.mozilla_check(), r"^\d{3} roots, \d{3} read$")


@unittest.skipUnless(sys.platform == "win32", "Windows' own certificate check")
class AskWindows(Fresh):
    def test_github_s_download_sites_are_asked_once_each(self):
        root = windows_store("ROOT")[0]
        asked = []

        def chain(host):
            asked.append(host)
            if host == "objects.githubusercontent.com":
                raise OSError("no answer")  # one site down: the others still count
            return [host.encode()]
        self.assertTrue(net._ask_windows("raw.githubusercontent.com", chain=chain, check=lambda certs: [root]))
        self.assertEqual(asked[0], "raw.githubusercontent.com")
        self.assertEqual(sorted(asked), sorted(net.GITHUB_HOSTS))
        self.assertEqual(net._roots, [root])  # the same root for every site: kept once
        self.assertIsInstance(net._context, ssl.SSLContext)
        self.assertFalse(net._ask_windows("github.com", chain=chain, check=lambda certs: [root]))  # all asked already
        self.assertEqual(len(asked), len(net.GITHUB_HOSTS))

    def test_nothing_added_when_windows_trusts_nothing(self):
        self.assertFalse(net._ask_windows("example.org", chain=lambda host: [b"x"], check=lambda certs: []))
        self.assertIsNone(net._context)

    def test_windows_finds_an_intermediate_s_root(self):
        roots = set(windows_store("ROOT"))
        for cert in windows_store("CA"):
            found = net.windows_roots([cert])
            if found and found[0] != cert:
                self.assertIn(found[0], roots)
                ssl.create_default_context().load_verify_locations(cadata=found[0])  # Python reads what it gives
                return
        self.skipTest("no intermediate in this PC's store that Windows trusts")

    def test_a_trusted_root_is_its_own_root(self):
        for cert in windows_store("ROOT"):
            found = net.windows_roots([cert])
            if found:
                self.assertEqual(found, [cert])
                return
        self.fail("Windows trusts none of its own roots")

    def test_what_isnt_a_certificate_is_refused(self):
        with self.assertRaises(ValueError):
            net.windows_roots([b"not a certificate"])


if __name__ == "__main__":
    unittest.main()
