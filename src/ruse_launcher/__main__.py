import time

STARTED = time.time()  # the start-up log's "python" (rusemod.startlog)

import sys  # noqa: E402

from rusemod import startlog  # noqa: E402

startlog.begin("launcher", python=STARTED)

from .app import main  # noqa: E402

if __name__ == "__main__":  # not in a worker program the build starts (rusemod.mend), which runs this file again
    sys.exit(main())
