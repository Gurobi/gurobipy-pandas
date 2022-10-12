"""
Internal methods for adding constraints to a model using a pandas structure.
These are used to build the actual API methods.
"""

from typing import Optional, Union

import pandas as pd
import gurobipy as gp
from gurobipy import GRB


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

    if sense is None:
        # called with 3 positional arguments
        # lhs must be an eval-able expression
        raise NotImplementedError()

    else:
        # called with 5 positional arguments
        # lhs & rhs must be column references or numeric values
        assert rhs is not None
        return add_constrs_from_dataframe_args(model, data, lhs, sense, rhs, name)


def add_constrs_from_dataframe_expression(
    model: gp.Model,
    data: pd.DataFrame,
    expr: str,
    *,
    name=None,
) -> pd.Series:
    return


def add_constr(model, lhs, sense, rhs, name):
    if name is None:
        name = ""
    if isinstance(lhs, gp.QuadExpr) or isinstance(rhs, gp.QuadExpr):
        return model.addQConstr(lhs, sense, rhs, name=name)
    return model.addLConstr(lhs, sense, rhs, name=name)


def add_constrs_from_dataframe_args(
    model: gp.Model,
    data: pd.DataFrame,
    lhs: Union[str, float],
    sense: str,
    rhs: Union[str, float],
    name: Optional[str],
) -> pd.Series:

    if isinstance(lhs, str):
        assert lhs in data.columns
    else:
        lhs = float(lhs)

    if isinstance(rhs, str):
        assert rhs in data.columns
    else:
        rhs = float(rhs)

    constrs = [
        add_constr(
            model,
            getattr(row, lhs) if isinstance(lhs, str) else lhs,
            sense,
            getattr(row, rhs) if isinstance(rhs, str) else rhs,
            name=f"{name}[{_format_index(row.Index)}]" if name else None,
        )
        for row in data.itertuples()
    ]
    return pd.Series(index=data.index, data=constrs, name=name)
