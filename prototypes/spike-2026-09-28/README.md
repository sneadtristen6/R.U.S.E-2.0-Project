# Spike code, 2026-09-28

Throwaway, read-only analysis scripts from the first investigation. They are **not** the platform's code:
M1 rewrites them properly, with tests. Keep them as a reference for how each finding was verified.

| File | Purpose |
|---|---|
| `ndf.py` | NDF container: header, zlib body, TOC0 tables (CLAS/PROP/STRG/TRAN) |
| `obje.py` | OBJE object parser with the verified type table; IMPR/EXPR name trees |
| `xyz.py` | opens `.ipk` script packs in memory |
| `m25.py` | `.xyz` reader + Python 2.5 marshal walker |
| `pe_info.py` | RUSE.exe PE header / imports / sections analysis |

Caveats:
- `ndf.py` hard-codes the game path and this session's working folder.
- The scripts import `ruse_edat.py` from the project root.
- Only `ndf.py` and `obje.py` have been reviewed.
