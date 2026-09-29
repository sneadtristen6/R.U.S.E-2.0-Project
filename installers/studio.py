"""The installed RUSE Studio starts here: Nuitka compiles this file into "RUSE Studio.exe" (installers/build_app.py).
From the repo, run `py -3 -m ruse_studio` instead."""
import sys

from ruse_studio.app import main
from rusemod.webui import log_to_file

if __name__ == "__main__":
    try:
        log_to_file("studio")  # no console: what it prints goes to <platform folder>\logs\studio.log
    except OSError:
        pass
    sys.exit(main())
