"""
Internal methods for adding constraints to a model using a pandas structure.
These are used to build the actual API methods.
"""

import re
from typing import Optional, Union

import pandas as pd
import gurobipy as gp
from gurobipy import GRB


CONSTRAINT_SENSES = frozenset([GRB.LESS_EQUAL, GRB.EQUAL, GRB.GREATER_EQUAL])


def _format_index(index):
    if isinstance(index, tuple):
        return ",".join(map(str, index))
    return str(index)


def add_constrs_from_dataframe(
    model: gp.Model,
    data: pd.DataFrame,
    lhs: Union[str, float],
    sense: Optional[str] = None,
    rhs: Optional[Union[str, float]] = None,
    *,
    name: Optional[str] = None,
) -> pd.Series:
    """
    Create a constraint for each row in the dataframe. Returns a series
    on the same index as :data.

    Can be called in 3-arg (model, data, expression) form, or 5-arg
    (model, data, lhs, sense, rhs) form.

    For 3-arg, :lhs must be a string expression including a comparison
    operator, which is evaluated over the dataframe columns to produce
    constraints.

    For 5-arg, :lhs and :rhs must refer to columns or be scalar values.
    Constraints are build as if the comparison operator were applied
    element-wise over between data[lhs] and data[rhs].
    """

    if sense is None:
        # called with 3 positional arguments
        # lhs must be an evaluable (?) expression on the dataframe columns
        data, sense = _create_expressions_dataframe(data, lhs)
        return _add_constrs_from_dataframe_args(model, data, "lhs", sense, "rhs", name)

    else:
        # called with 5 positional arguments
        # lhs & rhs must be column references or numeric values
        assert rhs is not None
        return _add_constrs_from_dataframe_args(model, data, lhs, sense, rhs, name)


def add_constrs_from_series(
    model: gp.Model,
    lhs: Union[pd.Series, float],
    sense: str,
    rhs: Union[pd.Series, float],
    *,
    name: Optional[str] = None,
) -> pd.Series:

    if isinstance(lhs, pd.Series) and isinstance(rhs, pd.Series):
        if not lhs.index.sort_values().equals(rhs.index.sort_values()):
            raise KeyError("series must be aligned")

    if isinstance(lhs, pd.Series) and lhs.isnull().any():
        raise ValueError("lhs series has missing values")

    if isinstance(rhs, pd.Series) and rhs.isnull().any():
        raise ValueError("rhs series has missing values")

    data = pd.DataFrame(
        {
            "lhs": lhs,
            "rhs": rhs,
        }
    )

    return add_constrs_from_dataframe(model, data, "lhs", sense, "rhs", name=name)


def _create_expressions_dataframe(df, expr):
    """Parse an expression (like DataFrame.query) to create left- and
    right-hand sides for buildind constraints. A new dataframe is
    always returned with two columns ('lhs' and 'rhs'). The sense is
    also extracted and returned.

    Note that DataFrame.eval() cannot be used to evaluate the two sides
    of the expression. For a dtype='object' series, both engines available
    in pandas seems to only allow operators implemented on 'object' (which
    is essentially none. So we have to roll our own here.

    TODO add query-like abilty to pull variables from the enclosing
    scope (uses leading @).

    TODO handle backtick syntax for columns containing spaces
    """
    lhs, rhs = re.split("[<>=]+", expr)
    # Just get the first character of sense, to match the gurobipy enums
    sense = expr.replace(lhs, "").replace(rhs, "")[0]
    scope = df
    lhsseries = eval(lhs, None, scope)
    rhsseries = eval(rhs, None, scope)
    data = pd.DataFrame(
        index=df.index,
        data={
            "lhs": lhsseries,
            "rhs": rhsseries,
        },
    )
    assert sense in CONSTRAINT_SENSES
    return data, sense


def _add_constr(model, lhs, sense, rhs, name):
    """Add a single constraint to the model, calling the appropriate
    function depending on the expression type."""
    if name is None:
        name = ""
    if isinstance(lhs, gp.QuadExpr) or isinstance(rhs, gp.QuadExpr):
        return model.addQConstr(lhs, sense, rhs, name=name)
    return model.addLConstr(lhs, sense, rhs, name=name)


def _add_constrs_from_dataframe_args(
    model: gp.Model,
    data: pd.DataFrame,
    lhs: Union[str, float],
    sense: str,
    rhs: Union[str, float],
    name: Optional[str],
) -> pd.Series:
    """Add one constraint per in :data, where :lhs and :rhs are column
    references or single values. Return constraints as an aligned series.
    """

    if isinstance(lhs, str):
        assert lhs in data.columns
    else:
        lhs = float(lhs)

    if isinstance(rhs, str):
        assert rhs in data.columns
    else:
        rhs = float(rhs)

    constrs = [
        _add_constr(
            model,
            getattr(row, lhs) if isinstance(lhs, str) else lhs,
            sense,
            getattr(row, rhs) if isinstance(rhs, str) else rhs,
            name=f"{name}[{_format_index(row.Index)}]" if name else None,
        )
        for row in data.itertuples()
    ]
    return pd.Series(index=data.index, data=constrs, name=name)
