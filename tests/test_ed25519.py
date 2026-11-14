"""rusemod.ed25519 against RFC 8032's test vectors (section 7.1), and what a bad signature does."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import unittest

from rusemod import ed25519

VECTORS = [  # (secret key, public key, message, signature), RFC 8032 section 7.1, tests 1 to 3
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
     "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025", "af82",
     "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
]


class Rfc8032(unittest.TestCase):
    def test_the_rfcs_vectors(self):
        for secret, public, message, signature in VECTORS:
            sk, pk, msg, sig = (bytes.fromhex(x) for x in (secret, public, message, signature))
            self.assertEqual(ed25519.public_key(sk), pk)
            self.assertEqual(ed25519.sign(sk, msg), sig)
            self.assertTrue(ed25519.verify(pk, msg, sig))

    def test_anything_else_fails(self):
        sk, pk, _msg, sig = (bytes.fromhex(x) for x in VECTORS[1])
        self.assertFalse(ed25519.verify(pk, b"\x73", sig))                       # another message
        self.assertFalse(ed25519.verify(pk, b"\x72", sig[:-1] + bytes([sig[-1] ^ 1])))  # a flipped bit
        self.assertFalse(ed25519.verify(bytes.fromhex(VECTORS[0][1]), b"\x72", sig))   # another key
        self.assertFalse(ed25519.verify(pk[:31], b"\x72", sig))                   # bad sizes never raise
        self.assertFalse(ed25519.verify(pk, b"\x72", sig + b"\0"))


if __name__ == "__main__":
    unittest.main()
