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

    Parameters
    ----------
    flag : bool, optional
        Pass True to enable interactive mode, False to disable.
        Defaults to True.
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

    Parameters
    ----------
    model : Model
        A Gurobi model to which new variables will be added
    pandas_obj : Index, Series, or DataFrame
        A pandas Index, Series, or DataFrame
    name : str, optional
        If provided, used as base name for new Gurobi variables and the name of
        the returned series
    lb : float, str, or Series, optional
        Lower bound for created variables. Can be a single numeric value. If
        ``pandas_obj`` is an Index or Series, can be a Series aligned with
        ``pandas_obj``. If ``pandas_obj`` is a dataframe, can be a string
        referring to a column of ``pandas_obj``. Defaults to 0.0.
    ub : float, str, or Series, optional
        Upper bound for created variables. Can be a single numeric value. If
        ``pandas_obj`` is an Index or Series, can be a Series aligned with
        ``pandas_obj``. If ``pandas_obj`` is a dataframe, can be a string
        referring to a column of ``pandas_obj``. Defaults to 0.0.
    obj : float, str, or Series, optional
        Linear objective function coefficient for created variables. Can be a
        single numeric value. If ``pandas_obj`` is an Index or Series, can be a
        Series aligned with ``pandas_obj``. If ``pandas_obj`` is a dataframe,
        can be a string referring to a column of ``pandas_obj``. Defaults to
        0.0.
    vtype : str or Series, optional
        Types of created variables. Can be a single string specifying the type
        (e.g. ``GRB.BINARY``). If ``pandas_obj`` is an Index or Series, can be a
        Series aligned with ``pandas_obj`` containing variable type string
        values. Defaults to ``GRB.CONTINUOUS``.
    index_formatter :
        Can be used to provide custom conversion of index values to variable
        names. The default behaviour is usually sufficient.

    Returns
    -------
    Series
        A Series of vars with the the index of `pandas_obj`
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


# Two overloads are used here to specify that at least one of the left- and
# right-hand sides must be a series (the other can be a single expression).


@overload
def add_constrs(
    model: gp.Model,
    lhs: pd.Series,
    sense: Union[pd.Series, str],
    rhs: Union[pd.Series, gp.Var, gp.LinExpr, gp.QuadExpr, float],
    *,
    name: Optional[str] = None,
    index_formatter: Union[str, Callable, Mapping[str, Callable]] = "default",
) -> pd.Series:
    ...  # pragma: no cover


@overload
def add_constrs(
    model: gp.Model,
    lhs: Union[pd.Series, gp.Var, gp.LinExpr, gp.QuadExpr, float],
    sense: Union[pd.Series, str],
    rhs: pd.Series,
    *,
    name: Optional[str] = None,
    index_formatter: Union[str, Callable, Mapping[str, Callable]] = "default",
) -> pd.Series:
    ...  # pragma: no cover


def add_constrs(
    model,
    lhs,
    sense,
    rhs,
    *,
    name=None,
    index_formatter="default",
) -> pd.Series:
    """Add a constraint to the model for each row in lhs & rhs. At least one of
    `lhs` and `rhs` must be a Series, while the other side may be a constant or a
    single gurobipy expression. If both sides are Series, then their indexes
    must match.

    Parameters
    ----------
    model : Model
        A Gurobi model to which new constraints will be added
    lhs : Series
        A series of expressions forming the left hand side of constraints, a
        constant, or a single expression.
    sense : Series or str
        Constraint sense; can be a series if senses vary, or a single string
        if all constraints have the same sense
    rhs : Series or float
        A series of expressions forming the right hand side of constraints, a
        constant, or a single expression.
    name : str
        Used as the returned series name, as well as the base name for added
        Gurobi constraints. Constraint name suffixes come from the lhs/rhs
        index.
    index_formatter :
        Can be used to provide custom conversion of index values to variable
        names. The default behaviour is usually sufficient.

    Returns
    -------
    Series
           A Series of Constr objects
    """
    return add_constrs_from_series(
        model, lhs, sense, rhs, name=name, index_formatter=index_formatter
    )
