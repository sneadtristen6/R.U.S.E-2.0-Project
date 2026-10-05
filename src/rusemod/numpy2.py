"""numpy, for the modules that do the plain code's sums on whole grids (tgu1np, paintnp, dxtnp): `from .numpy2 import
np`. Their answers were checked byte for byte against the plain code with numpy 2 (2.5.3, the one the apps carry).

numpy 1 chooses the kind of number a sum of small whole numbers gives in its own way and wasn't checked, so it is
refused here like a missing numpy (ImportError): the plain code then does the work, the same answers, slower."""
import numpy as np

if int(np.__version__.split(".")[0]) < 2:
    raise ImportError(f"numpy {np.__version__} is older than 2: the plain sums are used instead")
