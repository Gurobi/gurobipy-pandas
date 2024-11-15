__version__ = "1.2.0"

__all__ = ["add_constrs", "add_vars", "set_interactive"]

# Import accessors module to register accessors with pandas
import gurobipy_pandas.accessors  # noqa: F401

# Import public API functions
from gurobipy_pandas.api import add_constrs, add_vars, set_interactive
