import re
from typing import Union, Optional, List

import pandas as pd

import gurobipy as gp
from gurobipy import GRB


@pd.api.extensions.register_dataframe_accessor("grb")
class GRBDataFrameAccessor:
    def __init__(self, pandas_obj: pd.DataFrame):
        self._obj = pandas_obj

    def pd_add_vars(
        self,
        model: gp.Model,
        name: str,
        lb: Union[float, str] = 0.0,
        ub: Union[float, str] = GRB.INFINITY,
        obj: Union[float, str] = 0.0,
        vtype: str = GRB.CONTINUOUS,
        index: Optional[Union[str, List[str]]] = None,
    ):
        """Add a variable to the model for each row in the dataframe
        referenced by this accessor. Return a new DataFrame with the
        corresponding Vars appended as a new column

        :param model: A Gurobi model to which new variables will be added
        :type model: :class:`gurobipy.Model`
        :param name: Used as the appended column name, as well as the base
            name for added Gurobi variables
        :type name: str
        :param lb: Lower bound for created variables. May be a single value
            or the name of a column in the dataframe, defaults to 0.0
        :type lb: float or str, optional
        :param ub: Upper bound for created variables. May be a single value
            or the name of a column in the dataframe, defaults to
            :code:`GRB.INFINITY`
        :type ub: float or str, optional
        :param obj: Objective function coefficient for created variables.
            May be a single value, or the name of a column in the dataframe,
            defaults to 0.0
        :type obj: float or str, optional
        :param vtype: Gurobi variable type for created variables, defaults
            to :code:`GRB.CONTINUOUS`
        :param index: If provided, use the name column(s) for variable name
            suffixes. If :code:`None`, use the index
        :type index: str or list, optional
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
        # FIXME resolve ambiguities in column referencing vs. values ... maybe
        # lb/ub/obj must be only float or string. If string, then must match a
        # column, if float, then it's a fixed value (pandas columns can have
        # any hashable name). Test to be added to clear this up.
        x = model.addVars(indices, name=name, lb=lb, ub=ub, obj=obj, vtype=vtype)
        xs = pd.Series(data=x.values(), index=self._obj.index, name=name)
        return self._obj.join(xs)

    def pd_add_constrs(
        self,
        model: gp.Model,
        lhs: str,
        sense: Optional[str] = None,
        rhs: Optional[Union[str, float]] = None,
        name: Optional[str] = None,
    ):
        """Add a constraint to the model for each row in the dataframe
        referenced by this accessor. A new dataframe is returned, with
        constraint objects appended as an additional column.

        :param model: A Gurobi model to which new constraints will be added
        :type model: :class:`gurobipy.Model`
        :param lhs: A string representation of the entire constraint
            expression, or the name of a column
        :type lhs: str
        :param sense: Constraint sense. Required if lhs is not a complete
            expression including a comparator
        :type sense: str, optional
        :param rhs: Constraint right hand side. Can be a column name or
            float value. Required if lhs is not a complete expression
            including a comparator
        :type rhs: str or float, optional
        :param name: Used as the appended column name, as well as the base
            name for added Gurobi constraints. Constraint name suffixes
            come from the dataframe index.
        :type name: str

        Using some simple example data and variables to demo:

        >>> m = gp.Model()
        >>> df = (
        ...     pd.DataFrame({"c": [1, 2, 3]})
        ...     .grb.pd_add_vars(m, name="x")
        ...     .grb.pd_add_vars(m, name="y")
        ... )
        >>> m.update()
        >>> df
           c                  x                  y
        0  1  <gurobi.Var x[0]>  <gurobi.Var y[0]>
        1  2  <gurobi.Var x[1]>  <gurobi.Var y[1]>
        2  3  <gurobi.Var x[2]>  <gurobi.Var y[2]>

        Constraints can be added using a :code:`pd.DataFrame.eval`-like
        syntax. In this case, a constraint is added to the model for each
        row in the dataframe, specifying e.g. :math:`x_0 + y_0 \le 1` in the
        first row.

        >>> df2 = df.grb.pd_add_constrs(m, "x + y <= c", name="constr")
        >>> m.update()
        >>> df2
           c                  x                  y                     constr
        0  1  <gurobi.Var x[0]>  <gurobi.Var y[0]>  <gurobi.Constr constr[0]>
        1  2  <gurobi.Var x[1]>  <gurobi.Var y[1]>  <gurobi.Constr constr[1]>
        2  3  <gurobi.Var x[2]>  <gurobi.Var y[2]>  <gurobi.Constr constr[2]>

        Alternatively, you can use explicit column references in place of
        a string expression. This case specifies that :math:`x_i \le y_i`
        must hold for every row in the dataframe.

        >>> df3 = df.grb.pd_add_constrs(m, "x", GRB.LESS_EQUAL, "y", name="xy")
        >>> m.update()
        >>> df3
           c                  x                  y                     xy
        0  1  <gurobi.Var x[0]>  <gurobi.Var y[0]>  <gurobi.Constr xy[0]>
        1  2  <gurobi.Var x[1]>  <gurobi.Var y[1]>  <gurobi.Constr xy[1]>
        2  3  <gurobi.Var x[2]>  <gurobi.Var y[2]>  <gurobi.Constr xy[2]>

        Scalar values can also be used in place of a column reference for
        either the left or right-hand sides. The following case specifies
        that :math:`x_i + y_i \le 1` must hold for every row.

        >>> df4 = df.assign(expr=df["x"] + df["y"])
        >>> df4
           c                  x                  y                           expr
        0  1  <gurobi.Var x[0]>  <gurobi.Var y[0]>  <gurobi.LinExpr: x[0] + y[0]>
        1  2  <gurobi.Var x[1]>  <gurobi.Var y[1]>  <gurobi.LinExpr: x[1] + y[1]>
        2  3  <gurobi.Var x[2]>  <gurobi.Var y[2]>  <gurobi.LinExpr: x[2] + y[2]>
        >>> df4 = df4.grb.pd_add_constrs(m, "expr", GRB.LESS_EQUAL, 1, name="c4")
        >>> m.update()
        >>> df4[["expr", "c4"]]
                                    expr                     c4
        0  <gurobi.LinExpr: x[0] + y[0]>  <gurobi.Constr c4[0]>
        1  <gurobi.LinExpr: x[1] + y[1]>  <gurobi.Constr c4[1]>
        2  <gurobi.LinExpr: x[2] + y[2]>  <gurobi.Constr c4[2]>
        """
        if sense is None:
            return self._add_constrs_by_expression(model, lhs, name=name)
        else:
            return self._add_constrs_by_args(model, lhs, sense, rhs, name=name)

    def _add_constrs_by_args(self, model, lhs, sense, rhs, name):
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

    def _add_constrs_by_expression(self, model, expr, *, name):
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
            .grb._add_constrs_by_args(model, "lhs", sense, "rhs", name)
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

    def get_value(self):
        return pd.Series(
            index=self._obj.index,
            data=[le.getValue() for le in self._obj],
        )


@pd.api.extensions.register_index_accessor("grb")
class GRBIndexAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def pd_add_vars(
        self, model, lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name=None
    ):
        """Given an index, return a series of Vars with that index."""
        if name is None:
            indices = len(self._obj)
        else:
            indices = self._obj
        x = model.addVars(indices, lb=lb, ub=ub, vtype=vtype, name=name)
        return pd.Series(index=self._obj, data=x.values(), name=name)
