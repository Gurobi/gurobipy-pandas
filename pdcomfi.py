import pandas as pd

from gurobipy import GRB


@pd.api.extensions.register_dataframe_accessor("grb")
class GRBDataFrameAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def addVars(
        self, model, name, index=None, lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS
    ):
        """Name is a required argument as the new column needs a name.
        This makes a signature slightly different to model.addVars.

        Bounds can be set by passing a column name. Variable types can only
        be set constant (vtype='C' could cause ambiguity between a column
        name or GRB.CONTINUOUS).
        """
        if index is None:
            indices = self._obj.index
        elif isinstance(index, str):
            indices = self._obj[index]
        else:
            indices = self._obj[index].itertuples(index=False)
        if lb in self._obj.columns:
            lb = self._obj[lb]
        if ub in self._obj.columns:
            ub = self._obj[ub]
        x = model.addVars(indices, name=name, lb=lb, ub=ub, vtype=vtype)
        xs = pd.Series(data=x.values(), index=self._obj.index, name=name)
        return self._obj.join(xs)

    def addLConstrs(self, model, lhs, sense, rhs, name):
        """lhs must be a column name, rhs can be a scalar or column"""
        c = [
            model.addLConstr(
                lhs=getattr(row, lhs),
                sense=sense,
                rhs=getattr(row, rhs) if rhs in self._obj.columns else rhs,
                name=f"{name}[{row.Index}]",
            )
            for row in self._obj.itertuples()
        ]
        cs = pd.Series(c, index=self._obj.index, name=name)
        return self._obj.join(cs)


@pd.api.extensions.register_series_accessor("grb")
class GRBSeriesAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def __getattr__(self, attr):
        """Use Gurobi getAttr (not builtin) to access Var.X, Var.lb,
        Constr.Slack , etc attribute values series-wise."""
        return pd.Series(
            index=self._obj.index,
            data=[v.getAttr(attr) for v in self._obj],
            name=self._obj.name,
        )
