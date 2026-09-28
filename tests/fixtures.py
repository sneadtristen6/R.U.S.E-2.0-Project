"""Small made-up EDAT archives and NDF files for tests (no game files needed).

The layouts follow docs/FORMATS.md §1 (EDAT) and §2 (NDF).
"""
import struct
import zlib

NDF_SECTIONS = ["OBJE", "TOPO", "CHNK", "CLAS", "PROP", "STRG", "TRAN", "IMPR", "EXPR"]


# --- EDAT ---------------------------------------------------------------------------------------------------------
def _even(b: bytes) -> bytes:
    return b + b"\0" if len(b) % 2 else b


def make_edat(tree) -> bytes:
    """Build an EDAT v1 archive from a nested tree.

    `tree` is a list of nodes: ("file", fragment, data) or ("dir", fragment, [children]). Paths are the fragments
    joined in order, e.g. [("dir", "gfx\\", [("file", "a.bin", b"...")])] holds "gfx\\a.bin".
    Data is laid out contiguously in tree order, like the shipped packs.
    """
    blobs = []

    def entries(nodes) -> bytes:
        out = b""
        for i, node in enumerate(nodes):
            last = i == len(nodes) - 1
            kind, frag = node[0], node[1].encode("latin-1") + b"\0"
            if kind == "file":
                offset = sum(len(b) for b in blobs)
                blobs.append(node[2])
                body = _even(struct.pack("<IIIIB", 0, 0, offset, len(node[2]), 0) + frag)
            else:
                head = _even(struct.pack("<II", 0, 0) + frag)
                body = struct.pack("<I", len(head)) + head[4:] + entries(node[2])
            if not last:
                body = body[:4] + struct.pack("<I", len(body)) + body[8:]
            out += body
        return out

    dictionary = entries(tree)
    data = b"".join(blobs)
    return _edat_header(len(dictionary), len(data)) + dictionary + data


def make_empty_edat() -> bytes:
    """An archive with no files: a single root entry whose header length (1) is shorter than itself."""
    dictionary = _even(struct.pack("<II", 1, 0) + b"\0")
    return _edat_header(len(dictionary), 0) + dictionary


def _edat_header(dict_len: int, data_len: int) -> bytes:
    head = bytearray(0x40D)
    head[0:4] = b"edat"
    struct.pack_into("<I", head, 4, 1)
    struct.pack_into("<IIII", head, 0x19, 0x40D, dict_len, 0x40D + dict_len, data_len)
    return bytes(head)


# --- NDF ----------------------------------------------------------------------------------------------------------
def strs(items) -> bytes:
    return b"".join(struct.pack("<I", len(s.encode("latin-1"))) + s.encode("latin-1") for s in items)


def val(tc: int, payload: bytes) -> bytes:
    """One encoded NDF value: u32 type code + payload."""
    return struct.pack("<I", tc) + payload


def make_ndf(objects, classes, props, strings=(), trans=("$",), exports=None, imports=None,
             compress=False) -> bytes:
    """Build an NDF binary.

    objects: list of (class index, [(property index, encoded value)]), values made with `val`.
    props:   list of (property name, class index).
    exports: {object index: name}; imports: [name]. Both become one-level name trees under trans[0] ("$"),
             so export paths read "$/<name>". Names are added to TRAN automatically.
    """
    trans = list(trans)

    def name_tree(leaves) -> bytes:  # root node, then one child node per (tran index, leaf)
        if not leaves:
            return b""
        n = len(leaves)
        root = struct.pack("<IiI", 0, -1, n) + b"".join(struct.pack("<I", 4 * n + 12 * k) for k in range(n))
        return root + b"".join(struct.pack("<IiI", t, leaf, 0) for t, leaf in leaves)

    def tran_index(name) -> int:
        if name not in trans:
            trans.append(name)
        return trans.index(name)

    expr = name_tree([(tran_index(name), oi) for oi, name in sorted((exports or {}).items())])
    impr = name_tree([(tran_index(name), k) for k, name in enumerate(imports or [])])
    obje = b""
    for cls, prop_values in objects:
        obje += struct.pack("<I", cls)
        for pi, encoded in prop_values:
            obje += struct.pack("<I", pi) + encoded
        obje += struct.pack("<I", 0xABABABAB)
    body = {
        "OBJE": obje,
        "TOPO": b"",
        "CHNK": struct.pack("<II", 0, len(objects)),
        "CLAS": strs(classes),
        "PROP": b"".join(struct.pack("<I", len(n)) + n.encode("latin-1") + struct.pack("<I", c) for n, c in props),
        "STRG": strs(strings),
        "TRAN": strs(trans),
        "IMPR": impr,
        "EXPR": expr,
    }
    blob, toc = b"", []
    for name in NDF_SECTIONS:
        toc.append((name, 0x28 + len(blob), len(body[name])))
        blob += body[name]
    footer = b"TOC0" + struct.pack("<I", len(toc)) + b"".join(
        n.encode() + struct.pack("<IQQ", 0, off, size) for n, off, size in toc)
    footer_off = 0x28 + len(blob)
    flags = 0x80 if compress else 0
    header = b"EUG0" + struct.pack("<I", 0) + b"CNDF" + struct.pack("<IQQQ", flags, footer_off, 0x28,
                                                                    footer_off + len(footer))
    logical = header + blob + footer
    if not compress:
        return logical
    rest = logical[0x28:]
    return logical[:0x28] + struct.pack("<I", len(rest)) + zlib.compress(rest, 9)
