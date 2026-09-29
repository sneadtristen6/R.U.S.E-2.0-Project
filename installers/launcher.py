"""The installed RUSE Launcher starts here: Nuitka compiles this file into "RUSE Launcher.exe" (installers/build_app.py).
From the repo, run `py -3 -m ruse_launcher` instead."""
import sys

from ruse_launcher.app import main
from rusemod.webui import log_to_file

if __name__ == "__main__":
    try:
        log_to_file("launcher")  # no console: what it prints goes to <platform folder>\logs\launcher.log
    except OSError:
        pass
    sys.exit(main())
