"""The installed RUSE Launcher starts here: Nuitka compiles this file into "RUSE Launcher.exe" (installers/build_app.py).
From the repo, run `py -3 -m ruse_launcher` instead."""
import time

STARTED = time.time()  # the start-up log's "python" (rusemod.startlog): this file's first line runs

import sys  # noqa: E402

from rusemod import startlog  # noqa: E402

startlog.begin("launcher", python=STARTED)

from ruse_launcher.app import main  # noqa: E402
from rusemod.webui import log_to_file  # noqa: E402

if __name__ == "__main__":
    try:
        log_to_file("launcher")  # no console: what it prints goes to <platform folder>\logs\launcher.log
    except OSError:
        pass
    sys.exit(main())
