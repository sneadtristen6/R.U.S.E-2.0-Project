"""Read-only PE header analysis (stdlib only). Usage: py -3 pe_info.py <exe>"""
import collections, math, struct, sys

DIRS = ["EXPORT", "IMPORT", "RESOURCE", "EXCEPTION", "SECURITY", "BASERELOC", "DEBUG", "ARCH",
        "GLOBALPTR", "TLS", "LOAD_CONFIG", "BOUND_IMPORT", "IAT", "DELAY_IMPORT", "CLR", "RESERVED"]
DLLCH = {0x20: "HIGH_ENTROPY_VA", 0x40: "DYNAMIC_BASE(ASLR)", 0x80: "FORCE_INTEGRITY", 0x100: "NX_COMPAT(DEP)",
         0x200: "NO_ISOLATION", 0x400: "NO_SEH", 0x800: "NO_BIND", 0x1000: "APPCONTAINER", 0x2000: "WDM_DRIVER",
         0x4000: "GUARD_CF", 0x8000: "TERMINAL_SERVER_AWARE"}
PROXY = {"version.dll", "winmm.dll", "dinput8.dll", "dinput.dll", "dxgi.dll", "d3d9.dll", "d3d10.dll", "d3d11.dll",
         "d3d12.dll", "dsound.dll", "xinput1_3.dll", "xinput1_4.dll", "xinput9_1_0.dll", "winhttp.dll", "wininet.dll",
         "d3dx9_42.dll", "d3dx9_43.dll", "opengl32.dll", "dbghelp.dll", "iphlpapi.dll", "msacm32.dll", "avrt.dll",
         "ddraw.dll", "binkw64.dll", "binkw32.dll", "steam_api64.dll", "steam_api.dll", "x3daudio1_7.dll",
         "xaudio2_7.dll", "d3dcompiler_43.dll", "d3dx10_43.dll", "d3dx11_43.dll", "wsock32.dll", "mswsock.dll"}


def entropy(b):
    if not b:
        return 0.0
    c = collections.Counter(b)
    n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def main(path):
    with open(path, "rb") as f:  # read-only
        d = f.read()
    e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
    assert d[e_lfanew:e_lfanew + 4] == b"PE\0\0"
    mach, nsec, ts, _, _, sz_opt, chars = struct.unpack_from("<HHIIIHH", d, e_lfanew + 4)
    opt = e_lfanew + 24
    magic = struct.unpack_from("<H", d, opt)[0]
    pe64 = magic == 0x20B
    print(f"file={len(d):,} B machine=0x{mach:x} ({'x64' if mach == 0x8664 else 'x86' if mach == 0x14c else '?'}) "
          f"PE32{'+' if pe64 else ''} nsec={nsec} timestamp={ts} ({__import__('datetime').datetime.utcfromtimestamp(ts)}) chars=0x{chars:x}")
    linker = d[opt + 2], d[opt + 3]
    entry = struct.unpack_from("<I", d, opt + 16)[0]
    if pe64:
        imagebase = struct.unpack_from("<Q", d, opt + 24)[0]
        dllch = struct.unpack_from("<H", d, opt + 70)[0]
        subsys = struct.unpack_from("<H", d, opt + 68)[0]
        ndirs = struct.unpack_from("<I", d, opt + 108)[0]
        dir_off = opt + 112
    else:
        imagebase = struct.unpack_from("<I", d, opt + 28)[0]
        dllch = struct.unpack_from("<H", d, opt + 70)[0]
        subsys = struct.unpack_from("<H", d, opt + 68)[0]
        ndirs = struct.unpack_from("<I", d, opt + 92)[0]
        dir_off = opt + 96
    osver = struct.unpack_from("<HH", d, opt + 40)
    print(f"linker={linker[0]}.{linker[1]} osver={osver} subsystem={subsys} imagebase=0x{imagebase:x} entry_rva=0x{entry:x}")
    print(f"DllCharacteristics=0x{dllch:x}: " + ", ".join(v for k, v in DLLCH.items() if dllch & k))
    dirs = [struct.unpack_from("<II", d, dir_off + 8 * i) for i in range(ndirs)]
    print("data dirs:", ", ".join(f"{DIRS[i]}@0x{r:x}+0x{s:x}" for i, (r, s) in enumerate(dirs) if r or s))
    sec_off = opt + sz_opt
    secs = []
    for i in range(nsec):
        name, vsz, va, rsz, rptr = struct.unpack_from("<8sIIII", d, sec_off + 40 * i)
        sch = struct.unpack_from("<I", d, sec_off + 40 * i + 36)[0]
        name = name.rstrip(b"\0").decode("latin-1")
        secs.append((name, vsz, va, rsz, rptr, sch))
        ent = entropy(d[rptr:rptr + rsz])
        flags = ("R" if sch & 0x40000000 else "-") + ("W" if sch & 0x80000000 else "-") + ("X" if sch & 0x20000000 else "-")
        mark = " <- entry" if va <= entry < va + max(vsz, rsz) else ""
        print(f"  sec {name:<8} va=0x{va:08x} vsz=0x{vsz:08x} raw=0x{rptr:08x}+0x{rsz:08x} {flags} H={ent:.2f}{mark}")
    overlay = max(r + s for _, _, _, s, r, _ in secs)
    print(f"end of last section raw=0x{overlay:x}; overlay bytes={len(d) - overlay:,}")

    def rva2off(rva):
        for name, vsz, va, rsz, rptr, _ in secs:
            if va <= rva < va + max(vsz, rsz):
                return rva - va + rptr
        return None

    def cstr(off):
        return d[off:d.index(b"\0", off)].decode("latin-1")

    ptr = 8 if pe64 else 4
    ordflag = 1 << 63 if pe64 else 1 << 31
    fmt = "<Q" if pe64 else "<I"

    def thunks(rva):
        out = []
        o = rva2off(rva)
        while True:
            v = struct.unpack_from(fmt, d, o)[0]
            if v == 0:
                return out
            if v & ordflag:
                out.append(f"#{v & 0xffff}")
            else:
                out.append(cstr(rva2off(v & 0x7fffffff) + 2))
            o += ptr

    imports = {}
    irva, isz = dirs[1]
    o = rva2off(irva)
    while True:
        oft, _, _, name_rva, ft = struct.unpack_from("<IIIII", d, o)
        if name_rva == 0:
            break
        imports[cstr(rva2off(name_rva))] = thunks(oft or ft)
        o += 20
    print(f"IMPORTS ({len(imports)} DLLs, {sum(map(len, imports.values()))} functions):")
    for dll, fns in imports.items():
        flag = "  [PROXY CANDIDATE]" if dll.lower() in PROXY else ""
        print(f"  {dll:<24} {len(fns):>4} fns{flag}")
    # delay imports
    drva, dsz = dirs[13] if len(dirs) > 13 else (0, 0)
    if drva:
        o = rva2off(drva)
        print("DELAY IMPORTS:")
        while True:
            attrs, name_rva, hmod, iat, int_rva = struct.unpack_from("<IIIII", d, o)
            if name_rva == 0:
                break
            print(f"  {cstr(rva2off(name_rva))}: {len(thunks(int_rva))} fns")
            o += 32
    # TLS
    trva, tsz = dirs[9]
    if trva:
        o = rva2off(trva)
        if pe64:
            s, e, idx, cbs = struct.unpack_from("<QQQQ", d, o)
        else:
            s, e, idx, cbs = struct.unpack_from("<IIII", d, o)
        cb = []
        if cbs:
            co = rva2off(cbs - imagebase)
            while True:
                v = struct.unpack_from(fmt, d, co)[0]
                if v == 0:
                    break
                cb.append(hex(v)); co += ptr
        print(f"TLS: raw data 0x{s:x}-0x{e:x}, callbacks array VA=0x{cbs:x}: {cb or 'none'}")
    else:
        print("TLS: no TLS directory")
    # debug directory (PDB path)
    dbrva, dbsz = dirs[6]
    if dbrva:
        o = rva2off(dbrva)
        for i in range(dbsz // 28):
            _, dts, _, _, typ, sz, rva_, praw = struct.unpack_from("<IIHHIIII", d, o + 28 * i)
            info = ""
            if typ == 2 and d[praw:praw + 4] == b"RSDS":
                info = cstr(praw + 24)
            print(f"DEBUG type={typ} size={sz} {info}")
    # security dir (authenticode) -> file offset, not RVA
    srva, ssz = dirs[4]
    print(f"Authenticode signature: {'present, %d B at 0x%x' % (ssz, srva) if srva else 'none'}")
    # load config (CFG / security cookie)
    lrva, lsz = dirs[10]
    if lrva:
        o = rva2off(lrva)
        print(f"LOAD_CONFIG size field={struct.unpack_from('<I', d, o)[0]}")
    # interesting imported functions
    wanted = ("LoadLibrary", "GetProcAddress", "Direct3DCreate9", "D3D10", "D3D11", "CreateDXGIFactory", "DirectInput8Create",
              "XInputGetState", "SteamAPI", "IsDebuggerPresent", "CheckRemoteDebuggerPresent", "VirtualProtect", "CreateFileW",
              "CreateFileA", "PyEval", "Py_Initialize", "timeGetTime", "GetFileVersionInfo")
    hits = [f"{dll}!{fn}" for dll, fns in imports.items() for fn in fns if any(w in fn for w in wanted)]
    print("notable imports:", ", ".join(hits))
    # packer / DRM strings
    for s in (b"SteamStub", b".bind", b"UPX", b"Themida", b"VMProtect", b".securom", b"SecuROM", b"tages", b"Tages",
              b"StarForce", b"steam_api", b"SolidShield", b"GFWL", b"xlive", b"python25", b"Python", b"PyRun", b"Py_Initialize",
              b"lua_", b"Boost", b"Havok", b"Scaleform", b"GFx", b"bink", b"fmod", b"FMOD", b"libcurl", b"zlib", b"DirectX"):
        c = d.count(s)
        if c:
            print(f"  str {s.decode():<14} x{c} first@0x{d.find(s):x}")


if __name__ == "__main__":
    main(sys.argv[1])
