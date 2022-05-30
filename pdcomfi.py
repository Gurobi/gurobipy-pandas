import pandas as pd

from gurobipy import GRB


@pd.api.extensions.register_dataframe_accessor("grb")
class GRBDataFrameAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def addVars(self, model, name, lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS):
        """Name is a required argument as the new column needs a name.
        This makes a signature slightly different to model.addVars"""
        x = model.addVars(self._obj.index, name=name, lb=lb, ub=ub, vtype=vtype)
        xs = pd.Series(data=x, index=self._obj.index, name=name)
        return self._obj.join(xs)
