import doctest

import gurobipy_pandas.accessors


def setup(arg):
    """Ensure the default environment is started. Any license messages will
    be printed here so that they don't mess up the doctests."""
    with arg.globs["gp"].Model():
        pass


# Load doctests as unittest, see https://docs.python.org/3/library/doctest.html#unittest-api
def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(gurobipy_pandas.accessors, setUp=setup))
    tests.addTests(doctest.DocFileSuite("../docs/source/walkthrough.rst"))
    return tests
