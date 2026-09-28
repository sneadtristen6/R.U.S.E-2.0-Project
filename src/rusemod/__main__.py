"""`py -3 -m rusemod <command>`: the `ruse` command-line tool (see cli.py)."""
import sys

from .cli import main

sys.exit(main())
