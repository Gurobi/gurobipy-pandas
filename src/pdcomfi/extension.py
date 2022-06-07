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

    pass
