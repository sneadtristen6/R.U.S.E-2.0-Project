"""Read-only helpers for R.U.S.E. Python script containers: .ipk (nested EDAT) and .xyz (compressed code)."""
import io, struct, zlib
import ndf
from ruse_edat import EdatArchive, MAGIC


def edat_from_bytes(data, name="<mem>"):
    """Open an EDAT archive held in memory (e.g. an .ipk read out of ZZ_Win.dat)."""
    a = EdatArchive.__new__(EdatArchive)
    a.path, a._f = name, io.BytesIO(data)
    head = a._f.read(0x29)
    assert head[:4] == MAGIC, head[:4]
    a.version = struct.unpack_from("<I", head, 4)[0]
    a.checksum = head[8:24]
    a.dict_offset, a.dict_len, a.data_offset, a.data_len = struct.unpack_from("<IIII", head, 0x19)
    a._f.seek(a.dict_offset)
    a._dict = a._f.read(a.dict_len)
    a.entries = []
    a._walk(0, "")
    return a


def find_zlib(raw, lo=4, hi=0x40):
    for off in range(lo, min(hi, len(raw) - 2)):
        if raw[off] == 0x78 and ((raw[off] << 8) | raw[off + 1]) % 31 == 0:
            try:
                d = zlib.decompressobj()
                out = d.decompress(raw[off:])
                return off, out, d.eof, len(d.unused_data)
            except zlib.error:
                continue
    return None


def load_ipk(name):
    zz = ndf.pack("ZZ_Win")
    try:
        data = ndf.read_entry(zz, "genpython\\" + name)
    finally:
        zz.close()
    return edat_from_bytes(data, name)
