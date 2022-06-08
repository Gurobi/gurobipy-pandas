"""
Pandas automatic test suite for extensions. Needs some fixing.

Uses pytest fixtures, so cannot be run using unittest alone.
"""

from unittest import mock

import gurobipy as gp
import numpy as np
import pytest

from pandas.tests.extension import base

from pdcomfi.extension import GurobipyArray, GurobipyDtype


@pytest.fixture
def dtype():
    """A fixture providing the ExtensionDtype to validate."""
    return GurobipyDtype


@pytest.fixture
def data():
    """Length-100 array for this type.
    TODO: not quiet sufficient, Var & LinExpr would need to be handled
    differently with copy arguments.
    """
    with gp.Env() as env, gp.Model(env=env) as m:
        x = m.addVars(100)
        m.update()
        yield GurobipyArray(np.array(x.values()))


class TestGurobipyDtype(base.BaseDtypeTests):
    # These tests are **very** broken. construct_from_string makes the
    # wrong distinction between the dtype class and the type of the dtype
    # class. Tests fail on geopandas.
    pass


class TestGurobipyArrayConstructors(base.BaseConstructorsTests):
    # Many tests rely on assert_series_equal which uses equality operators
    # We need to customise this to use _is_ when dealing with vars
    #
    # This will also be true for assert_dataframe_equal and
    # assert_extension_array_equal
    #
    # Possibly a deeply embedded issue ... comparison operators are too
    # fundamental in pandas, perhaps we should not be hacking around them.
    pass
