"""The installed RUSE Studio starts here: Nuitka compiles this file into "RUSE Studio.exe" (installers/build_app.py).
From the repo, run `py -3 -m ruse_studio` instead."""
import time

STARTED = time.time()  # the start-up log's "python" (rusemod.startlog): this file's first line runs

import sys  # noqa: E402

from rusemod import startlog  # noqa: E402

startlog.begin("studio", python=STARTED)

from ruse_studio.app import main  # noqa: E402
from rusemod.webui import log_to_file  # noqa: E402

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # a worker program the build starts (rusemod.mend) runs its job, not the Studio
    try:
        log_to_file("studio")  # no console: what it prints goes to <platform folder>\logs\studio.log
    except OSError:
        pass
    sys.exit(main())
