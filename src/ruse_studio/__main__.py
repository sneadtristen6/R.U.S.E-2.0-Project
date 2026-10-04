import time

STARTED = time.time()  # the start-up log's "python" (rusemod.startlog)

import sys  # noqa: E402

from rusemod import startlog  # noqa: E402

startlog.begin("studio", python=STARTED)

from .app import main  # noqa: E402

sys.exit(main())
