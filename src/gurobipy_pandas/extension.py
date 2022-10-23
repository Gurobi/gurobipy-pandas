import gurobipy as gp
import numpy as np

from pandas.api.extensions import (
    ExtensionDtype,
    ExtensionArray,
    register_extension_dtype,
)


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


class GurobipyArray(ExtensionArray):
    def __init__(self, mobj):
        assert mobj.ndim == 1
        self._mobj = mobj

    @property
    def dtype(self) -> ExtensionDtype:
        return GurobipyDtype()

    def __len__(self):
        # .shape and .size are handled by the parent class
        return self._mobj.shape[0]

    @classmethod
    def _from_sequence(cls, scalars, dtype=None, copy=False):
        assert dtype is None or isinstance(dtype, GurobipyDtype)
        if copy:
            scalars = [
                obj if isinstance(obj, gp.Var) else obj.copy() for obj in scalars
            ]
        return cls(gp.MVar.fromlist(scalars))

    def copy(self):
        return GurobipyArray(self._mobj.copy())

    def __getitem__(self, item):
        # Almost back in the 0-D mess for a second. But pandas has clear guidance
        # here in ExtensionDType:
        #
        # For scalar ``item``, return a scalar value suitable for the array's
        # type. This should be an instance of ``self.dtype.type``.
        # For slice ``key``, return an instance of ``ExtensionArray``, even
        # if the slice is length 0 or 1.
        # For a boolean mask, return an instance of ``ExtensionArray``, filtered
        # to the values where ``item`` is True.

        sub = self._mobj[item]
        if sub.size == 1:
            return sub.item()
        return GurobipyArray(sub)

    def __add__(self, other):
        if isinstance(other, GurobipyArray):
            other = other._mobj
        return GurobipyArray(self._mobj + other)

    def __sub__(self, other):
        if isinstance(other, GurobipyArray):
            other = other._mobj
        return GurobipyArray(self._mobj - other)

    def isna(self):
        # Assumption is we always have a dense array (_can_hold_na = False)
        # Not really sure what role nan's would play anyway; to investigate
        return np.zeros(self.shape).astype(bool)
