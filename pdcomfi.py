import pandas as pd

from gurobipy import GRB


@pd.api.extensions.register_dataframe_accessor("grb")
class GRBDataFrameAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def addVars(self, model, name, index=None, lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS):
        """Name is a required argument as the new column needs a name.
        This makes a signature slightly different to model.addVars"""
        if index is None:
            indices = self._obj.index
        elif isinstance(index, str):
            indices = self._obj[index]
        else:
            indices = self._obj[index].itertuples(index=False)
        x = model.addVars(indices, name=name, lb=lb, ub=ub, vtype=vtype)
        xs = pd.Series(data=x.values(), index=self._obj.index, name=name)
        return self._obj.join(xs)
