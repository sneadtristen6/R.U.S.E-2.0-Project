"""Object names in the game's data files: the names a file gives its own objects and the ones it uses from other
files (`$/GFX/Everything/Descriptor_Unit_X`), read and written. New names go in name order where a file's names are
already in name order, otherwise at the end."""
from __future__ import annotations

import struct
from dataclasses import dataclass, field


@dataclass
class NameNode:
    tran: int
    leaf: int = -1
    children: list = field(default_factory=list)


def parse(section: bytes) -> NameNode | None:
    if not section:
        return None

    def node(off: int) -> NameNode:
        tr, leaf, cnt = struct.unpack_from("<IiI", section, off)
        base = off + 12
        kids = [node(base + struct.unpack_from("<I", section, base + 4 * k)[0]) for k in range(cnt)]
        return NameNode(tr, leaf, kids)

    return node(0)


def to_bytes(root: NameNode | None) -> bytes:
    if root is None:
        return b""
    out = bytearray()

    def write(n: NameNode) -> int:
        pos = len(out)
        out.extend(struct.pack("<IiI", n.tran, n.leaf, len(n.children)) + b"\0" * (4 * len(n.children)))
        for k, child in enumerate(n.children):
            child_pos = write(child)
            struct.pack_into("<I", out, pos + 12 + 4 * k, child_pos - (pos + 12))
        return pos

    write(root)
    return bytes(out)


def paths(root: NameNode | None, trans: list[str]) -> dict[int, str]:
    """leaf -> path."""
    out: dict[int, str] = {}

    def walk(n: NameNode, prefix: str) -> None:
        path = trans[n.tran] if not prefix else f"{prefix}/{trans[n.tran]}"
        if n.leaf >= 0:
            out[n.leaf] = path
        for c in n.children:
            walk(c, path)

    if root is not None:
        walk(root, "")
    return out


def add(root: NameNode | None, path: str, leaf: int, trans: list[str], tran_index) -> NameNode:
    """Add `path` with `leaf`; `tran_index(fragment)` returns (adding if needed) a TRAN index. Returns the root."""
    parts = path.split("/")
    if root is None:
        root = NameNode(tran_index(parts[0]))
    elif trans[root.tran] != parts[0]:
        raise ValueError(f"{path!r} doesn't start with this tree's root {trans[root.tran]!r}")
    node = root
    for part in parts[1:]:
        found = next((c for c in node.children if trans[c.tran] == part), None)
        if found is None:
            found = NameNode(tran_index(part))
            names = [trans[c.tran].lower() for c in node.children]
            if names == sorted(names):
                pos = sum(1 for n in names if n < part.lower())
            else:
                pos = len(node.children)
            node.children.insert(pos, found)
        node = found
    if node.leaf >= 0:
        raise ValueError(f"{path!r} is already named here")
    node.leaf = leaf
    return root


def remove(root: NameNode | None, leaf: int) -> bool:
    """Take `leaf`'s name away (pruning nodes left empty). Returns whether it was found."""
    if root is None:
        return False

    def walk(n: NameNode) -> bool:
        for k, c in enumerate(n.children):
            if c.leaf == leaf:
                c.leaf = -1
                if not c.children:
                    del n.children[k]
                return True
            if walk(c):
                if c.leaf < 0 and not c.children:
                    del n.children[k]
                return True
        return False

    if root.leaf == leaf:
        root.leaf = -1
        return True
    return walk(root)
