"""Downloads on a PC whose Windows hasn't fetched GitHub's root certificate yet (rusemod.net): a player on Discord,
2026-10-10, could open the Launcher but no mod would download ("unable to get local issuer certificate")."""
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
        self.addCleanup(net._asked.clear)
        self.addCleanup(net._roots.clear)
        self.addCleanup(setattr, net, "_context", None)


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
                mock.patch.object(net, "_ask_windows", return_value=False):
            with self.assertRaises(urllib.error.URLError) as caught:
                net.urlopen("https://github.com/x", 10)
        self.assertEqual(caught.exception.reason.verify_code, 20)
        self.assertEqual(opened.call_count, 1)

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
        self.assertTrue(net.missing_root(cert_error(19, "self-signed certificate in certificate chain")))
        self.assertFalse(net.missing_root(cert_error(10, "certificate has expired")))
        self.assertFalse(net.missing_root(urllib.error.URLError("timed out")))

    def test_the_player_reads_what_to_look_at(self):
        why = mod_index.plain(cert_error(20))
        self.assertIn("doesn't trust the site's security certificate (unable to get local issuer certificate)", why)
        self.assertIn("antivirus", why)


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
