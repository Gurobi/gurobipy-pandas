import re

import pandas as pd

from gurobipy import GRB


@pd.api.extensions.register_dataframe_accessor("grb")
class GRBDataFrameAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def pdAddVars(
        self,
        model,
        name,
        index=None,
        lb=0.0,
        ub=GRB.INFINITY,
        obj=0.0,
        vtype=GRB.CONTINUOUS,
    ):
        """
        Create a Var for each row in the dataframe, appending those Vars as a
        new column.

        Name is a required argument as the new column needs a name.
        This makes a signature slightly different to model.addVars.

        Bounds can be set by passing a column name. Variable types can only
        be set constant (vtype='C' could cause ambiguity between a column
        name or GRB.CONTINUOUS).

        Come to think of it ... lb = 1 could ambiguously reference column 1 ?
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
        if obj in self._obj.columns:
            obj = self._obj[obj]
        x = model.addVars(indices, name=name, lb=lb, ub=ub, obj=obj, vtype=vtype)
        xs = pd.Series(data=x.values(), index=self._obj.index, name=name)
        return self._obj.join(xs)

    def pdAddConstrs(self, model, lhs, sense=None, rhs=None, name=None):
        """
        Add constraints row-wise, specifying a relationship between two columns:

            df.grb.addConstrs(m, "col1", GBR.EQUAL, "col2")

        Equivalent to this .query- / .eval -like syntax:

            df.grb.addConstrs(m, "col1 == col2")

        Use a scalar in place of a column:

            df.grb.addConstrs(m, "col1", GRB.EQUAL, 0)

        Constraint objects are appended as an additional column in the
        returned dataframe.
        """
        if sense is None:
            return self._addConstrsByExpression(model, lhs, name=name)
        else:
            return self._addConstrsByArgs(model, lhs, sense, rhs, name=name)

    def _addConstrsByArgs(self, model, lhs, sense, rhs, name):
        """lhs, rhs can be scalars or columns"""
        c = [
            # Use QConstr here for generalisability
            model.addQConstr(
                lhs=getattr(row, lhs) if lhs in self._obj.columns else lhs,
                sense=sense,
                rhs=getattr(row, rhs) if rhs in self._obj.columns else rhs,
                name=f"{name}[{row.Index}]",
            )
            for row in self._obj.itertuples()
        ]
        cs = pd.Series(c, index=self._obj.index, name=name)
        return self._obj.join(cs)

    def _addConstrsByExpression(self, model, expr, *, name):
        """Parse an expression (like DataFrame.query) to build constraints
        from data.

        TODO add query-like abilty to pull variables from the enclosing
        scope (uses leading @).
        """
        # DataFrame.eval() is one option to help generalise the expression
        # parsing for this. But for a dtype='object' series it seems to only
        # ever use operators implemented on 'object' (which is essentially
        # none??) so isn't that helpful.
        lhs, rhs = re.split("[<>=]+", expr)
        sense = expr.replace(lhs, "").replace(rhs, "")
        return self._obj.join(
            pd.DataFrame(
                index=self._obj.index,
                data={
                    "lhs": eval(lhs, None, self._obj),
                    "rhs": eval(rhs, None, self._obj),
                },
            )
            .grb._addConstrsByArgs(model, "lhs", sense, "rhs", name)
            .drop(columns=["lhs", "rhs"])
        )


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

    def __setattr__(self, attr, value):
        if attr == "_obj":
            super().__setattr__(attr, value)
        elif isinstance(value, pd.Series):
            df = self._obj.to_frame(name="x").join(
                value.to_frame(name="v"), how="inner"
            )
            for entry in df.itertuples(index=False):
                entry.x.setAttr(attr, entry.v)
        else:
            for v in self._obj:
                v.setAttr(attr, value)

    def getValue(self):
        return pd.Series(
            index=self._obj.index,
            data=[le.getValue() for le in self._obj],
        )


@pd.api.extensions.register_index_accessor("grb")
class GRBIndexAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def pdAddVars(
        self, model, lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name=None
    ):
        """Given an index, return a series of Vars with that index."""
        if name is None:
            indices = len(self._obj)
        else:
            indices = self._obj
        x = model.addVars(indices, lb=lb, ub=ub, vtype=vtype, name=name)
        return pd.Series(index=self._obj, data=x.values(), name=name)
