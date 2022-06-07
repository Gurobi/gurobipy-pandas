"""
Pandas automatic test suite for extensions. Needs some fixing.

Uses pytest fixtures, so cannot be run using unittest alone.
"""

import pytest

from pandas.tests.extension import base

from pdcomfi.extension import GurobipyDtype


@pytest.fixture
def dtype():
    return GurobipyDtype


class TestGurobiPyType(base.BaseDtypeTests):
    # These tests are **very** broken. construct_from_string makes the
    # wrong distinction between the dtype class and the type of the dtype
    # class. Tests fail on geopandas.
    pass
