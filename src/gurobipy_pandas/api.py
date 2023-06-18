"""
Top-level API functions
"""

from typing import Callable, Mapping, Optional, Union, overload

import gurobipy as gp
import pandas as pd
from gurobipy import GRB

from gurobipy_pandas.constraints import add_constrs_from_series
from gurobipy_pandas.util import gppd_global_options
from gurobipy_pandas.variables import add_vars_from_dataframe, add_vars_from_index


def set_interactive(flag: bool = True):
    """Enables or disables interactive mode. In interactive mode, model
    updates are run immediately after any invocation of add_vars or
    add_constrs functions or accessors. This is useful when building models
    in interactive code environments like Jupyter notebooks, since variable
    and constraint names and attributes can be immediately queried after
    they are created. Interactive mode is disabled by default, since frequent
    update calls can be expensive.

    >>> import gurobipy as gp
    >>> import pandas as pd
    >>> import gurobipy_pandas as gppd
    >>> model = gp.Model()
    >>> index = pd.RangeIndex(5)
    >>> gppd.add_vars(model, index, name="x")
    0    <gurobi.Var *Awaiting Model Update*>
    1    <gurobi.Var *Awaiting Model Update*>
    2    <gurobi.Var *Awaiting Model Update*>
    3    <gurobi.Var *Awaiting Model Update*>
    4    <gurobi.Var *Awaiting Model Update*>
    Name: x, dtype: object
    >>> gppd.set_interactive()
    >>> gppd.add_vars(model, index, name="y")
    0    <gurobi.Var y[0]>
    1    <gurobi.Var y[1]>
    2    <gurobi.Var y[2]>
    3    <gurobi.Var y[3]>
    4    <gurobi.Var y[4]>
    Name: y, dtype: object
    >>> gppd.set_interactive(False)
    >>> gppd.add_vars(model, index, name="z")
    0    <gurobi.Var *Awaiting Model Update*>
    1    <gurobi.Var *Awaiting Model Update*>
    2    <gurobi.Var *Awaiting Model Update*>
    3    <gurobi.Var *Awaiting Model Update*>
    4    <gurobi.Var *Awaiting Model Update*>
    Name: z, dtype: object

    Note that interactive mode only applies to gurobipy_pandas calls. If
    you call methods of gurobipy.Model directly, updates will not be run
    automatically.

    :param flag: Pass True to enable interactive mode, False to disable.
        Defaults to True.
    :type flag: bool, optional
    """
    gppd_global_options["eager_updates"] = flag


# Index/Series variant (attribute arguments must be values or series)
@overload
def add_vars(
    model: gp.Model,
    pandas_obj: Union[pd.Index, pd.Series],
    *,
    name: Optional[Union[str, pd.Series]] = None,
    lb: Union[float, pd.Series] = 0.0,
    ub: Union[float, pd.Series] = GRB.INFINITY,
    obj: Union[float, pd.Series] = 0.0,
    vtype: Union[str, pd.Series] = GRB.CONTINUOUS,
    index_formatter: Union[str, Callable, Mapping[str, Callable]] = "default",
) -> pd.Series:
    ...  # pragma: no cover


# DataFrame variant (attribute arguments must be values or column names)
@overload
def add_vars(
    model: gp.Model,
    pandas_obj: pd.DataFrame,
    *,
    name: Optional[str] = None,
    lb: Union[float, str] = 0.0,
    ub: Union[float, str] = GRB.INFINITY,
    obj: Union[float, str] = 0.0,
    vtype: str = GRB.CONTINUOUS,
    index_formatter: Union[str, Callable, Mapping[str, Callable]] = "default",
) -> pd.Series:
    ...  # pragma: no cover


def add_vars(
    model,
    pandas_obj,
    *,
    name=None,
    lb=0.0,
    ub=GRB.INFINITY,
    obj=0.0,
    vtype=GRB.CONTINUOUS,
    index_formatter="default",
):
    """Add a variable to the given model for each entry in the given pandas
    Index, Series, or DataFrame.

    :param model: A Gurobi model to which new variables will be added
    :type model: :class:`gurobipy.Model`
    :param pandas_obj: A pandas Index, Series, or DataFrame
    :param name: If provided, used as base name for new Gurobi variables
        and the name of the returned series
    :type name: str, optional
    :param lb: Lower bound for created variables. Can be a single numeric
        value. If :pandas_obj is an Index or Series, can be a Series aligned
        with :pandas_obj. If :pandas_obj is a dataframe, can be a string
        referring to a column of :pandas_obj. Defaults to 0.0
    :type lb: float, str, or pd.Series, optional
    :return: A Series of vars with the the index of :pandas_obj
    :rtype: :class:`pd.Series`
    """
    if isinstance(pandas_obj, pd.Index):
        # Use the given index as the base object. All attribute arguments must
        # be single values, or series aligned with the index.
        return add_vars_from_index(
            model,
            pandas_obj,
            name=name,
            lb=lb,
            ub=ub,
            obj=obj,
            vtype=vtype,
            index_formatter=index_formatter,
        )
    elif isinstance(pandas_obj, pd.Series):
        # Use the index of the given series as the base object. All attribute
        # arguments must be single values, or series on the same index as the
        # given series.
        return add_vars_from_index(
            model,
            pandas_obj.index,
            name=name,
            lb=lb,
            ub=ub,
            obj=obj,
            vtype=vtype,
            index_formatter=index_formatter,
        )
    elif isinstance(pandas_obj, pd.DataFrame):
        # Use the given dataframe as the base object. All attribute arguments
        # must be single values, or names of columns in the given dataframe.
        return add_vars_from_dataframe(
            model,
            pandas_obj,
            name=name,
            lb=lb,
            ub=ub,
            obj=obj,
            vtype=vtype,
            index_formatter=index_formatter,
        )
    else:
        raise ValueError("`pandas_obj` must be an index, series, or dataframe")


def add_constrs(
    model: gp.Model,
    lhs: Union[pd.Series, float],
    sense: str,
    rhs: Union[pd.Series, float],
    *,
    name: Optional[str] = None,
    index_formatter: Union[str, Callable, Mapping[str, Callable]] = "default",
) -> pd.Series:
    """Add a constraint to the model for each row in lhs & rhs.

    :param model: A Gurobi model to which new constraints will be added
    :type model: :class:`gurobipy.Model`
    :param lhs: A series or numeric value
    :type lhs: pd.Series
    :param sense: Constraint sense
    :type sense: str
    :param rhs: A series or numeric value
    :type rhs: pd.Series
    :param name: Used as the returned series name, as well as the base
        name for added Gurobi constraints. Constraint name suffixes
        come from the lhs/rhs index.
    :type name: str
    :return: A Series of Constr objects
    :rtype: :class:`pd.Series`
    """
    return add_constrs_from_series(
        model, lhs, sense, rhs, name=name, index_formatter=index_formatter
    )
