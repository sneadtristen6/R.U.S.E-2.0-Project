"""`py -3 -m rusemod <command>`: the `ruse` command-line tool (see cli.py)."""
import sys

from .cli import main

if __name__ == "__main__":  # not in a worker program the build starts (rusemod.mend), which runs this file again
    sys.exit(main())
