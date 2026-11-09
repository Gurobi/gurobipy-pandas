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
    # docstring doctests only live in public API methods
    tests.addTests(doctest.DocTestSuite(gurobipy_pandas.accessors, setUp=setup))
    tests.addTests(doctest.DocTestSuite(gurobipy_pandas.api, setUp=setup))
    # any rst might have some doctests, fetch them all
    here = pathlib.Path(__file__).parent
    docs = here.joinpath("../docs/source")
    for docfile in docs.rglob("*.rst"):
        # nonlinear.rst doctests show Gurobi 14 output
        if docfile.stem == "nonlinear" and GUROBIPY_MAJOR_VERSION < 14:
            continue
        tests.addTests(doctest.DocFileSuite(str(docfile.relative_to(here))))
    return tests
