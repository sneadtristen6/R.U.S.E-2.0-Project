"""What a build's kept result is named by beside what it's made from: its kind's format number, bumped by hand when
that kind of result comes out different for the same inputs. Before (until 2026-10-17) each kept result was also
named by a fingerprint of every one of the platform's Python files (rusemod.model.code_version), so any Studio update,
even one that changed only a word on a button, threw every kept model, map ground, painting, movement and tile away,
and a player's first build after an update was a cold one again (the heaviest map mod: 412 s instead of 41 s;
studio-tools-design §12, "a format number per kind of kept result").

tests/test_keptformat.py guards the numbers: it makes each kind on small made-up inputs and compares a fingerprint of
what it made with the one recorded for that kind's number. When code changes what a kind makes, that test fails: bump
the kind's number below and record the new fingerprint there. A change that makes the same bytes keeps the number, and
every result kept with it stays good."""
from __future__ import annotations

# kind -> its format number: what makes it, and so what a change to bump it for touches
FORMATS = {
    "model": 1,      # the game's unit data as loaded (rusemod.model.load: its objects, names and files)
    "map": 2,        # a reshaped map's ground (rusemod.terrain.edit_map / groundgen, and the riverbed mend)
    #                  (2: the height trees' normals in the game's own layout, the ground-lighting fix of 2026-10-21,
    #                  commit 4b0f1c8c: the kept grounds made before it carried the old, wrongly lit words)
    "paint": 1,      # a map's painted pictures (rusemod.groundpaint.paint_ground: both tile sets, the close-up map)
    "movement": 1,   # a map's movement graphs after its blocks and opens (rusemod.nav.apply_blocks)
    "tile": 1,       # one painted ground tile (rusemod.groundpaint.paint_strokes), kept apart, any map
}


def stamp(kind: str) -> bytes:
    """The words a kept result of `kind` is named with, beside its inputs (KeyError for a kind there isn't)."""
    return f"rusemod kept {kind} v{FORMATS[kind]}".encode()
