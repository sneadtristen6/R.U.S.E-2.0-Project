"""rusemod — core library for reading and writing R.U.S.E. (Eugen IRISZOOM) data files.

Read-only against the game install; all edits target rebuilt copies, never the Steam files.
"""
from .dic import Dic
from .edat import Edat, Entry
from .ndf import Ndf, Obj, Value, decode

__version__ = "0.0.1"
__all__ = ["Dic", "Edat", "Entry", "Ndf", "Obj", "Value", "decode"]
