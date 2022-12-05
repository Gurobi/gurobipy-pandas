import operator

import gurobipy as gp
from gurobipy import GRB
import numpy as np
import pandas as pd

from pandas.api.types import is_numeric_dtype, is_scalar
from pandas.api.extensions import (
    ExtensionDtype,
    ExtensionArray,
    ExtensionScalarOpsMixin,
    register_extension_dtype,
)
from pandas.core.algorithms import take


@register_extension_dtype
class GurobipyDtype(ExtensionDtype):
    """Creating just one type to handle series of any gurobipy objects. The
    expectation should be that the type of a series is consistent. Maybe we'll
    want to separate TempConstr/Constr from Var/LinExpr/QuadExpr at some stage.
    """

    name = "gpobj"
    type = object  # only superclass we have for all gurobipy objects
    kind = "O"
    _is_numeric = False  # this might disallow groupby?
    _is_boolean = False  # don't want this used for indexing
    _can_hold_na = False  # expect dense?
    na_value = None

    @classmethod
    def construct_array_type(cls):
        return GurobipyArray


class GurobipyArray(ExtensionArray, ExtensionScalarOpsMixin):
    """Could probably leverage some pandas internals such as
    NDBackedExtensionArray, but for now going with what's explicitly documented.
    """

    def __init__(self, array):
        """Just hold a 1-D numpy array of gurobipy objects.
        TODO check for bad inputs."""
        self._array = array

    @property
    def dtype(self) -> ExtensionDtype:
        return GurobipyDtype()

    def __len__(self):
        # .shape and .size are handled by the parent class
        return len(self._array)

    @classmethod
    def _from_sequence(cls, scalars, dtype=None, copy=False):
        assert dtype is None or isinstance(dtype, GurobipyDtype)
        if copy:
            scalars = [
                obj if isinstance(obj, gp.Var) else obj.copy() for obj in scalars
            ]
        return cls(np.array(scalars))

    def copy(self):
        # TODO inefficient (but just getting the interface correct for now)
        return GurobipyArray._from_sequence(self._array, dtype=self.dtype, copy=True)

    def __getitem__(self, item):
        """
        Almost back in the 0-D mess for a second. But pandas has clear guidance
        here in ExtensionDType:

        For scalar ``item``, return a scalar value suitable for the array's
        type. This should be an instance of ``self.dtype.type``.
        For slice ``key``, return an instance of ``ExtensionArray``, even
        if the slice is length 0 or 1.
        For a boolean mask, return an instance of ``ExtensionArray``, filtered
        to the values where ``item`` is True.
        """
        sub = self._array[item]
        if isinstance(sub, np.ndarray):
            return GurobipyArray(sub)
        return sub  # python object

    def isna(self):
        # Assumption is we always have a dense array (_can_hold_na = False)
        # Not really sure what role nan's would play anyway; to investigate
        return np.zeros(self.shape).astype(bool)

    def take(self, indices, allow_fill=False, fill_value=None):
        # Verbatim from
        # https://github.com/pandas-dev/pandas/blob/main/pandas/core/arrays/base.py
        data = self.astype(object)
        if allow_fill and fill_value is None:
            fill_value = self.dtype.na_value

        result = take(data, indices, fill_value=fill_value, allow_fill=allow_fill)

        return self._from_sequence(result, dtype=self.dtype)

    def _reduce(self, name, *, skipna=True, **kwargs):
        # Call down: this will always return a scalar?
        if name == "sum":
            assert self._array.ndim == 1
            return gp.quicksum(self._array)
        meth = getattr(self._array, name)
        return meth()


GurobipyArray._add_arithmetic_ops()
