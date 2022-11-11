import doctest
import pathlib

import gurobipy as gp

import gurobipy_pandas.accessors

GUROBIPY_MAJOR_VERSION, *_ = gp.gurobi.version()


def setup(arg):
    """Ensure the default environment is started. Any license messages will
    be printed here so that they don't mess up the doctests. Also set some
    pandas display options for consistency."""
    with arg.globs["gp"].Model():
        pass
    arg.globs["pd"].set_option("display.width", 120)
    arg.globs["pd"].set_option("display.max_columns", 10)


# Load doctests as unittest, see https://docs.python.org/3/library/doctest.html#unittest-api
def load_tests(loader, tests, ignore):
    if GUROBIPY_MAJOR_VERSION < 10:
        # LinExpr and QuadExpr __str__ methods changed in v10, which affects how
        # they are displayed in a Series. So doctests fail on v9 and earlier.
        return tests
    # docstring doctests only live in public API methods
    tests.addTests(doctest.DocTestSuite(gurobipy_pandas.accessors, setUp=setup))
    tests.addTests(doctest.DocTestSuite(gurobipy_pandas.api, setUp=setup))
    # any rst might have some doctests, fetch them all
    here = pathlib.Path(__file__).parent
    docs = here.joinpath("../docs/source")
    for docfile in docs.rglob("*.rst"):
        tests.addTests(doctest.DocFileSuite(str(docfile.relative_to(here))))
    return tests
