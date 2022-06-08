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

    @classmethod
    def construct_array_type(cls):
        return GurobipyArray


class GurobipyArray(ExtensionArray):
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
    def _from_sequence(cls, scalars, dtype=None):
        assert dtype is None or isinstance(dtype, GurobipyDtype)
        return cls(np.array(scalars))

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
        return np.ones(self.shape).astype(bool)
