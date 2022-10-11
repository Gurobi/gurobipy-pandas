"""
Internal methods for adding variables to a model using a pandas structure.
These are used to build the actual API methods.
"""

from typing import Union, NewType, Optional

import gurobipy as gp
from gurobipy import GRB
import pandas as pd


# Dummy type to enable type checking of series accessors
GRBSeriesVar = NewType("GRBSeriesVar", pd.Series)


def align_series(series: pd.Series, index: pd.Index) -> pd.Series:
    """
    Align :series with :index and return the result.

    Raise a KeyError on any mismatch between the index of :series and
    :index (reordering is ok).

    Raise a ValueError if there is any missing data once the series
    is aligned.
    """
    if not index.sort_values().equals(series.index.sort_values()):
        raise KeyError("... series not aligned with index")
    aligned = series.loc[index]
    if aligned.isnull().any():
        raise ValueError("... series has missing values")
    return aligned


def add_vars_from_index(
    model: gp.Model,
    index: pd.Index,
    *,
    lb: Union[float, pd.Series] = 0.0,
    ub: Union[float, pd.Series] = GRB.INFINITY,
    obj: Union[float, pd.Series] = 0.0,
    vtype: Union[str, pd.Series] = GRB.CONTINUOUS,
    name: Optional[Union[str, pd.Series]] = None,
) -> GRBSeriesVar:
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

    if isinstance(lb, pd.Series):
        lbseries = align_series(lb, index)
        lb = list(lbseries.values)

    if isinstance(ub, pd.Series):
        ubseries = align_series(ub, index)
        ub = list(ubseries.values)

    if isinstance(obj, pd.Series):
        objseries = align_series(obj, index)
        obj = list(objseries.values)

    if isinstance(vtype, pd.Series):
        vtypeseries = align_series(vtype, index)
        vtype = list(vtypeseries.values)

    if isinstance(name, pd.Series):
        nameseries = align_series(name, index)
        namearg = list(nameseries.values)
        seriesname = None
    else:
        namearg = name
        seriesname = name

    newvars = model.addVars(index, lb=lb, ub=ub, obj=obj, vtype=vtype, name=namearg)
    return pd.Series(index=index, data=list(newvars.values()), name=seriesname)


def add_vars_from_dataframe(
    model: gp.Model,
    data: pd.DataFrame,
    *,
    lb: Union[float, str] = 0.0,
    ub: Union[float, str] = GRB.INFINITY,
    obj: Union[float, str] = 0.0,
    vtype: str = GRB.CONTINUOUS,
    name: Optional[str] = None,
) -> GRBSeriesVar:
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
    return
