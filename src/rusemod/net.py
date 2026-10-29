"""Opening web addresses, for both apps: urllib's urlopen, a second try with the root certificates Windows trusts, and
a third with Mozilla's root list.

Python checks a site's certificate against the root certificates Windows has on disk. Windows keeps only some of its
roots there and fetches the others the first time one of its own programs needs one; Python can't ask for that. On a
PC that never needed GitHub's root, every mod download failed with "certificate verify failed: unable to get local
issuer certificate" (a player on Discord, 2026-10-10). So when Python finds no root for a site, Windows itself is asked
to check the site's certificate (that fetches the missing root, as a browser would), and the request is tried once more
with the roots Windows trusted.

On a PC whose Windows can't fetch the root either (its root updates turned off or blocked), the mod downloads still
failed: "unable to get issuer certificate" (a player on Reddit, 2026-10-29; GitHub's download site's chain ends at ISRG
Root X1, and that PC's Windows had the certificate under it but not that root). Then the request is tried once more
with Mozilla's root list too: the roots Firefox trusts (the certifi package the apps carry), as a browser that brings
its own list does. Python still checks everything else (the site's name, the dates, the chain), so only a root Windows
or Mozilla trusts is ever trusted.
"""
from __future__ import annotations

import socket
import ssl
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request

# Where the apps' downloads go (the mod list, the mods' and the apps' releases): a download from one is redirected to
# another, so a missing root is looked for on all of them at once.
GITHUB_HOSTS = ("github.com", "api.github.com", "raw.githubusercontent.com", "objects.githubusercontent.com",
                "release-assets.githubusercontent.com")
NO_ROOT = {2, 19, 20}  # OpenSSL's "unable to get issuer certificate", "self-signed certificate in certificate chain",
#                        "unable to get local issuer certificate": no root Python knows
ASK_TIMEOUT = 10  # seconds for each site's certificate, and for Windows to check it

_lock = threading.Lock()
_asked: set[str] = set()     # the sites Windows was asked about in this run
_roots: list[bytes] = []     # the roots Windows trusted for them (DER), added to Python's
_mozilla: str | None = None  # Mozilla's root list (PEM) once it was added in this run ("": the apps haven't got it)
_context: ssl.SSLContext | None = None


def urlopen(req, timeout: float):
    """urllib.request.urlopen(req, timeout), and when Python found no root for the site's certificate, once more after
    Windows has checked it (windows_roots), and once more with Mozilla's root list when that didn't do it either
    (_add_mozilla). Raises what urlopen raises."""
    used = _context
    try:
        return _open(req, timeout, used)
    except urllib.error.URLError as exc:
        if not missing_root(exc):
            raise
        failed = exc
    host = _host(req)
    for widen in (_ask_windows, _add_mozilla):
        # (another download may have widened the roots meanwhile: then they're tried too)
        if not (widen(host) or _context is not used):
            continue
        used = _context
        try:
            return _open(req, timeout, used)
        except urllib.error.URLError as exc:
            if not missing_root(exc):
                raise
            failed = exc
    raise failed


def _open(req, timeout: float, context: ssl.SSLContext | None):
    if context is None:
        return urllib.request.urlopen(req, timeout=timeout)
    return urllib.request.urlopen(req, timeout=timeout, context=context)


def missing_root(exc: BaseException) -> bool:
    """Whether a failed request failed because Python knows no root for the site's certificate."""
    reason = getattr(exc, "reason", exc)
    return isinstance(reason, ssl.SSLCertVerificationError) and reason.verify_code in NO_ROOT


def _host(req) -> str:
    url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
    return (urllib.parse.urlsplit(url).hostname or "").lower()


def _ask_windows(host: str, chain=None, check=None) -> bool:
    """Ask Windows about `host` (and GitHub's other download sites, with a GitHub address) once per run; True when it
    trusted a root Python didn't have, so a second try can work. `chain` and `check` are for tests."""
    global _context
    chain, check = chain or server_chain, check or windows_roots
    hosts = [host] + [h for h in GITHUB_HOSTS if h != host] if host in GITHUB_HOSTS else [host]
    with _lock:
        new = []
        for h in hosts:
            if not h or h in _asked:
                continue
            _asked.add(h)
            try:
                certs = chain(h)
                new += [root for root in check(certs) if root not in _roots + new]
            except (OSError, ValueError):
                continue  # that site can't be reached or checked now: the others still can
        if not new:
            return False
        _roots.extend(new)
        _context = _widened()
        return True


def mozilla_roots() -> str:
    """Mozilla's root list (PEM): the roots Firefox trusts, from the certifi package the apps carry (its cacert.pem,
    made from Mozilla's certdata.txt; MPL-2.0). ImportError or OSError when this copy hasn't got it."""
    import certifi
    return certifi.contents()


def _add_mozilla(host: str = "", roots: str | None = None) -> bool:
    """Add Mozilla's root list to Python's roots, once per run; True when it did, so another try can work. `roots` is
    for tests. A run without certifi (from source, without the apps' libraries) goes on without it."""
    global _context, _mozilla
    with _lock:
        if _mozilla is not None:
            return False
        try:
            _mozilla = mozilla_roots() if roots is None else roots
        except (ImportError, OSError):
            _mozilla = ""
            return False
        _context = _widened()
        return True


def _widened() -> ssl.SSLContext:
    """Python's usual roots (Windows' on disk), with the roots Windows trusted when asked and Mozilla's list once added.
    Call it holding _lock."""
    context = ssl.create_default_context()
    if _roots:
        context.load_verify_locations(cadata=b"".join(_roots))
    if _mozilla:
        context.load_verify_locations(cadata=_mozilla)
    return context


def mozilla_check() -> str:
    """The apps' self-test: Mozilla's root list is in this copy and Python reads it."""
    roots = mozilla_roots()
    context = ssl.create_default_context(cadata=roots)
    return f"{roots.count('-----BEGIN CERTIFICATE-----')} roots, {len(context.get_ca_certs())} read"


def server_chain(host: str, port: int = 443, timeout: float = ASK_TIMEOUT) -> list[bytes]:
    """The certificates `host` sends (DER, its own first), read without checking them: only Windows' check of them
    is used, never the certificates themselves."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=timeout) as raw, \
            context.wrap_socket(raw, server_hostname=host) as tls:
        chain = getattr(tls._sslobj, "get_unverified_chain", None)  # Python 3.10 on (3.13's public one gives bytes)
        certs = [c.public_bytes(ssl._ssl.ENCODING_DER) for c in (chain() or [])] if chain else []
        return certs or [tls.getpeercert(binary_form=True)]


def windows_roots(certs: list[bytes]) -> list[bytes]:
    """The root (DER) Windows trusts for this chain (the site's certificate first, then the ones it sent with it), or
    [] when Windows doesn't trust it either. Windows fetches a root it doesn't have on disk while it checks, as it does
    for a browser. Not on Windows: []."""
    if sys.platform != "win32" or not certs:
        return []
    import ctypes
    from ctypes import wintypes

    class CertContext(ctypes.Structure):
        _fields_ = [("dwCertEncodingType", wintypes.DWORD), ("pbCertEncoded", ctypes.POINTER(ctypes.c_ubyte)),
                    ("cbCertEncoded", wintypes.DWORD)]

    class ChainElement(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("pCertContext", ctypes.POINTER(CertContext))]

    class SimpleChain(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("dwErrorStatus", wintypes.DWORD), ("dwInfoStatus", wintypes.DWORD),
                    ("cElement", wintypes.DWORD), ("rgpElement", ctypes.POINTER(ctypes.POINTER(ChainElement)))]

    class ChainContext(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("dwErrorStatus", wintypes.DWORD), ("dwInfoStatus", wintypes.DWORD),
                    ("cChain", wintypes.DWORD), ("rgpChain", ctypes.POINTER(ctypes.POINTER(SimpleChain)))]

    class EnhKeyUsage(ctypes.Structure):
        _fields_ = [("cUsageIdentifier", wintypes.DWORD), ("rgpszUsageIdentifier", ctypes.c_void_p)]

    class UsageMatch(ctypes.Structure):
        _fields_ = [("dwType", wintypes.DWORD), ("Usage", EnhKeyUsage)]

    class ChainPara(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("RequestedUsage", UsageMatch)]

    encoding = 0x1 | 0x10000  # X509_ASN_ENCODING | PKCS_7_ASN_ENCODING
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)  # its own handle: the argtypes set here stay here
    crypt32.CertCreateCertificateContext.restype = ctypes.POINTER(CertContext)
    crypt32.CertCreateCertificateContext.argtypes = [wintypes.DWORD, ctypes.c_char_p, wintypes.DWORD]
    crypt32.CertFreeCertificateContext.argtypes = [ctypes.POINTER(CertContext)]
    crypt32.CertOpenStore.restype = ctypes.c_void_p
    crypt32.CertOpenStore.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
    crypt32.CertAddEncodedCertificateToStore.argtypes = [ctypes.c_void_p, wintypes.DWORD, ctypes.c_char_p,
                                                         wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    crypt32.CertCloseStore.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    crypt32.CertGetCertificateChain.argtypes = [ctypes.c_void_p, ctypes.POINTER(CertContext), ctypes.c_void_p,
                                                ctypes.c_void_p, ctypes.POINTER(ChainPara), wintypes.DWORD,
                                                ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(ChainContext))]
    crypt32.CertFreeCertificateChain.argtypes = [ctypes.POINTER(ChainContext)]

    leaf = crypt32.CertCreateCertificateContext(encoding, certs[0], len(certs[0]))
    if not leaf:
        raise ValueError("Windows can't read the site's certificate")
    store = crypt32.CertOpenStore(ctypes.c_void_p(2), 0, None, 0, None)  # CERT_STORE_PROV_MEMORY: the ones it sent
    chain = ctypes.POINTER(ChainContext)()
    try:
        for cert in certs[1:]:
            if store:
                crypt32.CertAddEncodedCertificateToStore(store, encoding, cert, len(cert), 4, None)  # ADD_ALWAYS
        para = ChainPara(ctypes.sizeof(ChainPara))
        if not crypt32.CertGetCertificateChain(None, leaf, None, store, ctypes.byref(para), 0, None,
                                               ctypes.byref(chain)):
            raise ValueError(f"Windows couldn't check the site's certificate (error {ctypes.get_last_error()})")
        if chain.contents.dwErrorStatus or not chain.contents.cChain:
            return []  # Windows doesn't trust it either (or it's out of date): nothing is added
        simple = chain.contents.rgpChain[0].contents
        root = simple.rgpElement[simple.cElement - 1].contents.pCertContext.contents
        return [ctypes.string_at(root.pbCertEncoded, root.cbCertEncoded)]
    finally:
        if chain:
            crypt32.CertFreeCertificateChain(chain)
        if store:
            crypt32.CertCloseStore(store, 0)
        crypt32.CertFreeCertificateContext(leaf)
