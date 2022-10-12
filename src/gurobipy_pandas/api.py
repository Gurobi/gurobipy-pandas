"""
Top-level API functions
"""

from typing import overload, Union, Optional

import gurobipy as gp
from gurobipy import GRB
import pandas as pd

from gurobipy_pandas.add_vars import (
    add_vars_from_index,
    add_vars_from_dataframe,
)


# Index/Series variant (attribute arguments must be values or series)
@overload
def pd_add_vars(
    model: gp.Model,
    pandas_obj: Union[pd.Index, pd.Series],
    *,
    name: Optional[Union[str, pd.Series]] = None,
    lb: Union[float, pd.Series] = 0.0,
    ub: Union[float, pd.Series] = GRB.INFINITY,
    obj: Union[float, pd.Series] = 0.0,
    vtype: Union[str, pd.Series] = GRB.CONTINUOUS,
) -> pd.Series:
    ...


# DataFrame variant (attribute arguments must be values or column names)
@overload
def pd_add_vars(
    model: gp.Model,
    pandas_obj: pd.DataFrame,
    *,
    name: Optional[str] = None,
    lb: Union[float, str] = 0.0,
    ub: Union[float, str] = GRB.INFINITY,
    obj: Union[float, str] = 0.0,
    vtype: str = GRB.CONTINUOUS,
) -> pd.Series:
    ...


def pd_add_vars(
    model,
    pandas_obj,
    *,
    name=None,
    lb=0.0,
    ub=GRB.INFINITY,
    obj=0.0,
    vtype=GRB.CONTINUOUS,
):

    if isinstance(pandas_obj, pd.Index):
        # Use the given index as the base object. All attribute arguments must
        # be single values, or series aligned with the index.
        return add_vars_from_index(
            model, pandas_obj, name=name, lb=lb, ub=ub, obj=obj, vtype=vtype
        )
    elif isinstance(pandas_obj, pd.Series):
        # Use the index of the given series as the base object. All attribute
        # arguments must be single values, or series on the same index as the
        # given series.
        return add_vars_from_index(
            model, pandas_obj.index, name=name, lb=lb, ub=ub, obj=obj, vtype=vtype
        )
    elif isinstance(pandas_obj, pd.DataFrame):
        # Use the given dataframe as the base object. All attribute arguments
        # must be single values, or names of columns in the given dataframe.
        return add_vars_from_dataframe(
            model, pandas_obj, name=name, lb=lb, ub=ub, obj=obj, vtype=vtype
        )
    else:
        raise ValueError("`pandas_obj` must be an index, series, or dataframe")
