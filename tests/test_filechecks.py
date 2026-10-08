"""The build's checks for fonts, videos, Flash menus and shaders (rusemod.filechecks; the owner, 2026-10-08: "just write
a check for those four kinds"), on small made-up files. (Every one of the game's own 4 fonts, 5 Flash menus, its
shader file and 96 videos passes them: checked read-only against the game, 2026-10-08.)"""
import struct
import unittest
import zlib

from fixtures import make_ndf, val
from rusemod import filechecks, gamefiles
from rusemod.filechecks import CheckError


# --- a font ---
def table_font(tables: dict, version=b"\x00\x01\x00\x00") -> bytes:
    out, body = bytearray(version + struct.pack(">HHHH", len(tables), 0, 0, 0)), b""
    start = 12 + 16 * len(tables)
    for tag, data in tables.items():
        out += struct.pack(">4sIII", tag.encode("latin-1"), 0, start + len(body), len(data))
        body += data + b"\0" * (-len(data) % 4)
    return bytes(out + body)


def font_tables(**change) -> dict:
    head = bytearray(54)
    struct.pack_into(">I", head, 12, 0x5F0F3CF5)
    struct.pack_into(">H", head, 18, 1000)
    hhea = bytearray(36)
    struct.pack_into(">H", hhea, 34, 1)
    cmap = struct.pack(">HHHHI", 0, 1, 3, 1, 12) + struct.pack(">HHH", 4, 24, 0) + bytes(18)
    tables = {"cmap": cmap, "glyf": b"", "head": bytes(head), "hhea": bytes(hhea), "hmtx": bytes(4),
              "loca": struct.pack(">HH", 0, 0), "maxp": struct.pack(">IH", 0x5000, 1), "name": bytes(6),
              "post": bytes(32)}
    tables.update(change)
    return {k: v for k, v in tables.items() if v is not None}


class Fonts(unittest.TestCase):
    def test_a_font_and_a_collection(self):
        font = table_font(font_tables())
        self.assertEqual(filechecks.check_font(font), 1)
        one = table_font(font_tables())
        ttc = bytearray(b"ttcf" + struct.pack(">HHI", 1, 0, 1) + struct.pack(">I", 16))
        # a collection's tables are counted from its start: move the font's table offsets past the header
        moved = bytearray(one)
        for i in range(struct.unpack_from(">H", one, 4)[0]):
            off = struct.unpack_from(">I", one, 12 + 16 * i + 8)[0]
            struct.pack_into(">I", moved, 12 + 16 * i + 8, off + 16)
        self.assertEqual(filechecks.check_font(bytes(ttc + moved)), 1)
        self.assertEqual(gamefiles.check_kind("gen/fonts/new.ttf", font), "font")

    def test_bad_fonts_are_refused(self):
        bad_head = bytearray(font_tables()["head"])
        struct.pack_into(">I", bad_head, 12, 0)
        cases = {
            "not a TrueType": b"NOPE" + bytes(60),
            "without its post": table_font(font_tables(post=None)),
            "glyph outlines": table_font(font_tables(glyf=None)),
            "'head' table isn't one": table_font(font_tables(head=bytes(bad_head))),
            "go backwards": table_font(font_tables(loca=struct.pack(">HH", 4, 0))),
            "metrics don't agree": table_font(font_tables(hmtx=b"")),
            "kind fonts don't have": table_font(font_tables(cmap=struct.pack(">HHHHI", 0, 1, 3, 1, 12) +
                                                            struct.pack(">HHH", 99, 6, 0))),
            "past the file's end": table_font(font_tables())[:-40],
            "font collection says": b"ttcf" + struct.pack(">HHI", 1, 0, 9999),
        }
        for why, data in cases.items():
            with self.subTest(why=why), self.assertRaisesRegex(CheckError, why):
                filechecks.check_font(data)


# --- a video ---
def el(ident: int, body: bytes) -> bytes:
    size = len(body)
    return ident.to_bytes((ident.bit_length() + 7) // 8, "big") + bytes([0x80 | size]) + body if size < 127 else \
        ident.to_bytes((ident.bit_length() + 7) // 8, "big") + (0x10000000 | size).to_bytes(4, "big") + body


def webm(doc=b"webm", video=b"V_VP9", sounds=(b"A_VORBIS",), extra=b"") -> bytes:
    tracks = el(0xAE, el(0x83, b"\x01") + el(0x86, video))
    for s in sounds:
        tracks += el(0xAE, el(0x83, b"\x02") + el(0x86, s))
    segment = el(0x1654AE6B, tracks) + el(0x1F43B675, el(0xE7, b"\x00") + el(0xA3, b"\x81\x00\x00\x80frame")) + extra
    return el(0x1A45DFA3, el(0x4282, doc)) + el(0x18538067, segment)


class Videos(unittest.TestCase):
    def test_a_webm_the_game_plays(self):
        self.assertEqual(filechecks.check_video(webm()), {"video": 1, "sound": 1})
        self.assertEqual(filechecks.check_video(webm(sounds=(b"A_VORBIS",) * 8)), {"video": 1, "sound": 8})

    def test_others_are_refused(self):
        unknown = bytearray(webm())
        at = unknown.find(b"\x18\x53\x80\x67") + 4
        cases = {"another kind of Matroska": webm(doc=b"matroska"), "VP9 videos only": webm(video=b"V_VP8"),
                 "only in Vorbis": webm(sounds=(b"A_OPUS",)), "attachments": webm(extra=el(0x1941A469, b"x")),
                 "not a WebM": b"RIFF" + bytes(20), "runs past": webm()[:-3]}
        unknown[at] = 0xFF  # a size of all ones: "unknown"
        cases["unknown size"] = bytes(unknown[:at + 1] + unknown[at + 1:])
        for why, data in cases.items():
            with self.subTest(why=why), self.assertRaisesRegex(CheckError, why):
                filechecks.check_video(data)

    def test_not_taken_yet(self):
        # checked, but waiting for the safe way to hand the game a mod's video (the owner's call)
        with self.assertRaisesRegex(gamefiles.GameFileError, "isn't set up yet"):
            gamefiles.check_kind("ww2/videos/new.webm", webm())


# --- a Flash menu ---
def tag(code: int, payload: bytes) -> bytes:
    if len(payload) < 0x3F:
        return struct.pack("<H", code << 6 | len(payload)) + payload
    return struct.pack("<HI", code << 6 | 0x3F, len(payload)) + payload


def external_image(name: bytes) -> bytes:
    return struct.pack("<HHHH", 3, 13, 84, 84) + b"\0" + bytes([len(name)]) + name


def flash(code=b"\x96\x02\x00\x08\x00\x00", inner=b"\x07\x00", shape=b"\x01\x00shape", text=b"\x02\x00words",
          image=b"menu_I3.tga", compress=False, more=b"") -> bytes:
    sprite = struct.pack("<HH", 5, 1) + tag(59, struct.pack("<H", 5) + inner) + tag(1, b"") + tag(0, b"")
    tags = (tag(9, b"\x00\x00\x00") + tag(2, shape) + tag(37, text) + tag(1001, external_image(image)) +
            tag(12, code) + tag(39, sprite) + more + tag(1, b"") + tag(0, b""))
    body = b"\x00" + struct.pack("<HH", 30 << 8, 1) + tags  # an empty frame size, 30 frames a second, 1 frame
    if compress:
        return b"CFX\x09" + struct.pack("<I", 8 + len(body)) + zlib.compress(body)
    return b"GFX\x09" + struct.pack("<I", 8 + len(body)) + body


class FlashMenus(unittest.TestCase):
    def test_layout_shapes_and_words_change_the_code_stays(self):
        game = flash()
        self.assertEqual(filechecks.check_flash(game, game), 11)  # 8 tags, and the sprite's own 3
        self.assertGreater(filechecks.check_flash(flash(shape=b"\x01\x00a new shape", text=b"\x02\x00new words",
                                                        image=b"menu_I9.tga", compress=True), game), 0)
        self.assertEqual(gamefiles.check_kind("gen/menu.gfx", flash(text=b"\x02\x00other"), game), "Flash menu")

    def test_code_changes_are_refused(self):
        game = flash()
        cases = {"DoAction": flash(code=b"\x96\x02\x00\x08\x01\x00"),
                 "DoInitAction": flash(inner=b"\x07\x01"),
                 "ImportAssets2": flash(more=tag(71, b"other.swf\0\x01\x00")),
                 "tag 37": flash(text=b"\x02\x00<img src='x.swf'>"),
                 "tag 26": flash(more=tag(26, b"\x80\x01\x00clip actions"))}
        for what, data in cases.items():
            with self.subTest(what=what), self.assertRaisesRegex(CheckError, f"isn't the game's .*{what}"):
                filechecks.check_flash(data, game)
        with self.assertRaisesRegex(CheckError, "isn't the game's"):  # a new menu: no code at all
            filechecks.check_flash(game, None)

    def test_bad_menus_are_refused(self):
        game = flash()
        cut = bytearray(game)
        struct.pack_into("<I", cut, 4, len(game) + 5)
        past = bytearray(game[:-2] + struct.pack("<H", 1 << 6 | 9))  # the last tag says 9 bytes, none follow
        struct.pack_into("<I", past, 4, len(past))
        cases = {"not a Flash menu": b"PK\x03\x04" + bytes(20), "length isn't": bytes(cut), "runs past": bytes(past),
                 "names a file elsewhere": flash(image=b"../x.tga")}
        for why, data in cases.items():
            with self.subTest(why=why), self.assertRaisesRegex(CheckError, why):
                filechecks.check_flash(data, game)


# --- the shader file ---
PS = struct.pack("<7I", 0xFFFF0300, 0x0002FFFE, 0x42415443, 0, 0x02000001, 0x800F0800, 0x80E40000) + \
    struct.pack("<I", 0x0000FFFF)  # ps_3_0: a comment, "mov oC0, r0", the end mark
VS = struct.pack("<4I", 0xFFFE0300, 0x02000001, 0x800F0000, 0x90E40000) + struct.pack("<I", 0x0000FFFF)


def packed(code: bytes) -> bytes:
    z = zlib.compress(code)
    return struct.pack("<IBI", 4 + len(z), 1, len(code)) + z


def shader_file(*codes: bytes) -> bytes:
    objects = [(0, [])] + [(1, [(0, val(0x1E, packed(c)))]) for c in codes]
    return make_ndf(objects=objects, classes=filechecks.SHADER_CLASSES, props=[("ObjectCode", 1)])


class Shaders(unittest.TestCase):
    def test_the_game_s_shaders_pass_changed_ones_wait_for_approval(self):
        game = shader_file(PS, VS)
        self.assertEqual(filechecks.check_shader_code(PS), "ps_3_0")
        self.assertEqual(filechecks.check_shader_code(VS), "vs_3_0")
        self.assertEqual(filechecks.check_shaders(game, game), 2)
        self.assertEqual(filechecks.check_shaders(shader_file(VS, PS), game), 2)  # the same shaders, moved
        changed = PS.replace(struct.pack("<I", 0x80E40000), struct.pack("<I", 0x80E40001))
        with self.assertRaisesRegex(CheckError, "1 shader in it changed: .* until RUSE 2.0 approves it"):
            filechecks.check_shaders(shader_file(changed, VS), game)
        import hashlib
        self.assertEqual(filechecks.check_shaders(shader_file(changed, VS), game,
                                                  approved={hashlib.sha256(changed).hexdigest()}), 2)
        with self.assertRaisesRegex(gamefiles.GameFileError, "approves it"):
            gamefiles.check_kind("genhlsl/x/shadercachev02.shc", shader_file(changed, VS), game)

    def test_bad_shaders_are_refused(self):
        cases = {"another kind": struct.pack("<2I", 0xFFFF0200, 0x0000FFFF),
                 "no shader has": PS[:16] + struct.pack("<I", 0x00000063) + PS[20:],
                 "words past its end": PS + struct.pack("<I", 0),
                 "no end mark": PS[:-4],
                 "cut short": PS[:-4][:4] + b"\x01"}
        for why, code in cases.items():
            with self.subTest(why=why), self.assertRaisesRegex(CheckError, why):
                filechecks.check_shader_code(code)
        broken = bytearray(packed(PS))
        broken[-3] ^= 0xFF
        with self.assertRaisesRegex(CheckError, "doesn't unpack|isn't the size"):
            filechecks.shader_programs(make_ndf(objects=[(0, []), (1, [(0, val(0x1E, bytes(broken)))])],
                                                classes=filechecks.SHADER_CLASSES, props=[("ObjectCode", 1)]))
        with self.assertRaisesRegex(CheckError, "holds other things"):
            filechecks.shader_programs(make_ndf(objects=[(0, [])], classes=["TUnit"], props=[]))


if __name__ == "__main__":
    unittest.main()
