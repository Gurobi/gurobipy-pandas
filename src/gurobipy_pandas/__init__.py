__version__ = "1.1.1"

# Import public API functions
# Import accessors module to register accessors.
import gurobipy_pandas.accessors  # noqa: F401
from gurobipy_pandas.api import add_constrs as add_constrs  # noqa: F401
from gurobipy_pandas.api import add_vars as add_vars # noqa: F401
from gurobipy_pandas.api import set_interactive as set_interactive  # noqa: F401
