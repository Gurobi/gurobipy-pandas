"""
Internal methods for adding variables to a model using a pandas structure.
These are used to build the actual API methods.
"""

from typing import Optional, Union

import gurobipy as gp
import pandas as pd
from gurobipy import GRB

from gurobipy_pandas.util import align_series, create_names, gppd_global_options


def prepare_series(series: pd.Series, index: pd.Index, err_label: str):
    """
    Align :series with :index and return the values as a list.

    Raise a KeyError on any mismatch between the index of :series and
    :index (reordering is ok).

    Raise a ValueError if there is any missing data once the series
    is aligned.
    """
    aligned = align_series(series, index, err_label="...")
    return list(aligned.values)


def add_vars_from_index(
    model: gp.Model,
    index: pd.Index,
    *,
    lb: Union[float, pd.Series] = 0.0,
    ub: Union[float, pd.Series] = GRB.INFINITY,
    obj: Union[float, pd.Series] = 0.0,
    vtype: Union[str, pd.Series] = GRB.CONTINUOUS,
    name: Optional[Union[str, pd.Series]] = None,
    index_formatter="default",
) -> pd.Series:
    """Add one variable to :model for every entry in :index. Added
    variables are returned as a series with index :index.

    If :lb is numeric, all variables have lower bound :lb. If it is
    a Series, lower bounds are taken from this series. The series must
    align exactly with :index and have no missing values.

    If :ub is numeric, all variables have upper bound :ub. If it is
    a Series, upper bounds are taken from this series. The series must
    align exactly with :index and have no missing values.

    If :obj is numeric, all variables have objective coeff :obj. If it is
    a Series, objective coeffs are taken from this series. The series must
    align exactly with :index and have no missing values.

    If :vtype is a string, it must be one of Gurobi's type values. If it
    is a Series, variable types are taken from this series. The series must
    align exactly with :index and have no missing values.

    If :name is None, variables are given default names by the optimizer.
    If it is a string, :name is used as a prefix with the full names
    constructed based on :index. If it is a series, names are taken from
    this series. The series must align exactly with :index and have no
    missing values.

    model and index are positional, others are keyword-only
    """

    if index.has_duplicates:
        raise ValueError("Index contains duplicate entries, cannot create variables")

    if isinstance(lb, pd.Series):
        lb = prepare_series(lb, index, "lb")
    else:
        lb = float(lb)

    if isinstance(ub, pd.Series):
        ub = prepare_series(ub, index, "ub")
    else:
        ub = float(ub)

    if isinstance(obj, pd.Series):
        obj = prepare_series(obj, index, "obj")
    else:
        obj = float(obj)

    if isinstance(vtype, pd.Series):
        vtype = prepare_series(vtype, index, "vtype")
    elif not isinstance(vtype, str):
        raise TypeError("'vtype' must be a string or series")

    if isinstance(name, pd.Series):
        namearg = prepare_series(name, index, "name")
        seriesname = None
    elif isinstance(name, str):
        namearg = create_names(name, index, index_formatter)
        seriesname = name
    elif name is None:
        namearg = None
        seriesname = None
    else:
        raise TypeError("'name' must be a string, series, or None")

    newvars = model.addMVar(
        len(index), lb=lb, ub=ub, obj=obj, vtype=vtype, name=namearg
    )
    if gppd_global_options["eager_updates"]:
        model.update()
    return pd.Series(index=index, data=newvars.tolist(), name=seriesname)


def add_vars_from_dataframe(
    model: gp.Model,
    data: pd.DataFrame,
    *,
    lb: Union[float, str] = 0.0,
    ub: Union[float, str] = GRB.INFINITY,
    obj: Union[float, str] = 0.0,
    vtype: str = GRB.CONTINUOUS,
    name: Optional[str] = None,
    index_formatter="default",
) -> pd.Series:
    """Add one variable to :model for every row in :data. Added
    variables are returned as a series on the same index as :data.

    If :lb is numeric, all variables have lower bound :lb. If it is
    a string, lower bounds taken from column :lb of data.

    If :ub is numeric, all variables have upper bound :ub. If it is
    a string, upper bounds taken from column :ub of :data.

    If :obj is numeric, all variables have objective coeff :obj. If it is
    a string, objective coeffs taken from column :obj of :data.

    :vtype must be one of Gurobi's type values. It cannot reference a
    column in :data, as these type values are strings and this creates
    ambiguity. So all returned variables have the same type.

    :name can be a string or None. If None, variables are given default
    names by the optimizer. If it is a string, :name is used as a prefix
    with the full names constructed based on the index of :data.

    model and data are positional, others are keyword-only
    """

    if data.index.has_duplicates:
        raise ValueError("Index contains duplicate entries, cannot create variables")

    if isinstance(lb, str):
        lb = prepare_series(data[lb], data.index, "lb")
    else:
        lb = float(lb)

    if isinstance(ub, str):
        ub = prepare_series(data[ub], data.index, "ub")
    else:
        ub = float(ub)

    if isinstance(obj, str):
        obj = prepare_series(data[obj], data.index, "obj")
    else:
        obj = float(obj)

    if not isinstance(vtype, str):
        raise TypeError("'vtype' must be a string")

    if not (name is None or isinstance(name, str)):
        raise TypeError("'name' must be a string or None")

    if name:
        namearg = create_names(name, data.index, index_formatter)
    else:
        namearg = None

    newvars = model.addMVar(
        len(data.index), lb=lb, ub=ub, obj=obj, vtype=vtype, name=namearg
    )
    if gppd_global_options["eager_updates"]:
        model.update()
    return pd.Series(index=data.index, data=newvars.tolist(), name=name)
