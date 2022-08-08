import re
from typing import Union, Optional, List

import pandas as pd

import gurobipy as gp
from gurobipy import GRB


@pd.api.extensions.register_dataframe_accessor("grb")
class GRBDataFrameAccessor:
    """Accessor class for methods invoked as :code:`pd.DataFrame(...).grb.*`.
    The accessor does not expect particular types in the dataframe. This
    class should not be instantiated directly; it should be used via Pandas'
    accessor API

    :param pandas_obj: A pandas dataframe
    :type pandas_obj: :class:`pd.DataFrame`
    """

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
        """Add a variable to the given model for each row in the dataframe
        referenced by this accessor.

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
        :type vtype: str, optional
        :param index: If provided, use the name column(s) for variable name
            suffixes. If :code:`None`, use the index
        :type index: str or list, optional
        :return: A new DataFrame with new Vars appended as a column
        :rtype: :class:`pd.DataFrame`
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
        referenced by this accessor.

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
        :return: A new DataFrame with new Constrs appended as a column
        :rtype: :class:`pd.DataFrame`

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
    """Accessor class for methods invoked as :code:`pd.Series(...).grb.*`. The
    accessor expects a series containing gurobipy objects, and can return new
    series by evaluating a target value across all objects in the series. This
    class should not be instantiated directly; it should be used via Pandas'
    accessor API

    :param pandas_obj: A pandas series
    :type pandas_obj: :class:`pd.Series`
    """

    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def __getattr__(self, attr):
        """Retrieve the given Gurobi attribute for every object in the
        Series held by this accessor

        :return: A series with the evaluated attributes
        :rtype: :class:`pd.Series`

        For example, after solving a model, solution values can be read
        using the :code:`X` attribute.

        Build and solve a little model:

        >>> m = gp.Model()
        >>> df = pd.DataFrame({"key": [1, 2, 2, 2], "obj": [4, 3, 2, 1]})
        >>> df = df.grb.pd_add_vars(m, name="x", vtype=gp.GRB.BINARY, obj="obj")
        >>> grouped = df.groupby('key')[['x']].sum().grb.pd_add_constrs(m, "x == 1", name="constr")
        >>> m.optimize()  # doctest: +ELLIPSIS
        Gurobi Optimizer version...
        Best objective 5.000000000000e+00, best bound 5.000000000000e+00, gap 0.0000%
        >>> df['x'].grb.X
        0    1.0
        1    0.0
        2    0.0
        3    1.0
        Name: x, dtype: float64
        """
        return pd.Series(
            index=self._obj.index,
            data=[v.getAttr(attr) for v in self._obj],
            name=self._obj.name,
        )

    def __setattr__(self, attr, value):
        """Implements Python built-in :code:`__setattr__` to change the
        given Gurobi attribute for every object in the Series held by this
        accessor

        :return: A new series with the evaluated attributes
        :rtype: :class:`pd.Series`

        For example, after creating a series of variables, their upper
        bounds can be set and retrieved.

        >>> m = gp.Model()
        >>> x = pd.RangeIndex(3).grb.pd_add_vars(m)
        >>> m.update()
        >>> x
        0    <gurobi.Var C0>
        1    <gurobi.Var C1>
        2    <gurobi.Var C2>
        dtype: object
        >>> upper_bounds = pd.Series(data=[3, 2], index=[1, 2])
        >>> upper_bounds
        1    3
        2    2
        dtype: int64
        >>> x.grb.UB = upper_bounds

        After setting upper bounds (by aligning the variable series :code:`x`
        with the data series :code:`upper_bounds`), attributes can be read
        back from the Gurobi objects.

        >>> m.update()
        >>> x.grb.UB
        0    inf
        1    3.0
        2    2.0
        dtype: float64
        """
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
        """Return a new series, on the same index, containing the result of
        :code:`obj.getValue()` for each gurobipy object in the series held
        by this accessor. Note that this assumes that the wrapped objects are
        gurobipy expressions (:class:`LinExpr` or :class:`QuadExpr`)

        :return: A series with the evaluated expression values
        :rtype: :class:`pd.Series`
        """
        return pd.Series(
            index=self._obj.index,
            data=[le.getValue() for le in self._obj],
        )

    def pd_add_constrs(
        self,
        model: gp.Model,
        sense: str,
        rhs: Optional[Union[str, float]] = None,
        name: Optional[str] = None,
    ):
        """Add a constraint to the model for each entry in the series
        referenced by this accessor.

        :param model: A Gurobi model to which new constraints will be added
        :type model: :class:`gurobipy.Model`
        :param sense: Constraint sense.
        :type sense: str
        :param rhs: Constraint right hand side. Can be a scalar value or
            another Series with a corresponding index.
        :type rhs: :class:`pd.Series` or float
        :param name: Used as the returned Series name, as well as the base
            name for added Gurobi constraints. Constraint name suffixes
            come from the dataframe index.
        :type name: str
        :return: A Series of constraints attached to the given Model.
        :rtype: :class:`pd.Series`

        This syntax is useful for simple groupby operations (for example,
        building logical OR relationships):

        >>> m = gp.Model()
        >>> df = pd.DataFrame({"key": [1, 2, 2, 2]})
        >>> df = df.grb.pd_add_vars(m, name="x", vtype=gp.GRB.BINARY)
        >>> constrs = (
        ...     df.groupby('key')['x'].sum()
        ...     .grb.pd_add_constrs(m, GRB.EQUAL, 1, name='c')
        ... )
        >>> m.update()
        >>> constrs.grb.RHS
        key
        1    1.0
        2    1.0
        Name: c, dtype: float64
        >>> constrs.grb.Sense
        key
        1    =
        2    =
        Name: c, dtype: object
        >>> constrs.apply(m.getRow)
        key
        1                  <gurobi.LinExpr: x[0]>
        2    <gurobi.LinExpr: x[1] + x[2] + x[3]>
        Name: c, dtype: object

        """
        df = self._obj.to_frame(name="lhs")
        df["rhs"] = rhs
        # Use the dataframe machinery.
        df = df.grb.pd_add_constrs(model, "lhs", sense, "rhs", name=name)
        return df[name]


@pd.api.extensions.register_index_accessor("grb")
class GRBIndexAccessor:
    """Accessor class for methods invoked as :code:`pd.Index(...).grb.*`. The
    accessor expects normal pandas types in the index, and can return new
    series of gurobipy objects aligned to that index. This class should not be
    instantiated directly; it should be used via Pandas' accessor API

    :param pandas_obj: A pandas index
    :type pandas_obj: :class:`pd.Index`
    """

    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def pd_add_vars(
        self,
        model: gp.Model,
        lb: float = 0.0,
        ub: float = GRB.INFINITY,
        vtype: str = GRB.CONTINUOUS,
        name: Optional[str] = None,
    ):
        """Add a variable to the given model for each entry in the index
        referenced by this accessor.

        :param model: A Gurobi model to which new variables will be added
        :type model: :class:`gurobipy.Model`
        :param lb: Lower bound for created variables, defaults to 0.0
        :type lb: float, optional
        :param ub: Upper bound for created variables, defaults to
            :code:`GRB.INFINITY`
        :type ub: float, optional
        :param obj: Objective function coefficient for created variables,
            defaults to 0.0
        :type obj: float, optional
        :param vtype: Gurobi variable type for created variables, defaults
            to :code:`GRB.CONTINUOUS`
        :type vtype: str, optional
        :param name: If provided, used as base name for new Gurobi variables
        :type name: str, optional
        :return: A Series of vars with the index referenced by the accessor
        :rtype: :class:`pd.Series`
        """
        if name is None:
            indices = len(self._obj)
        else:
            indices = self._obj
        x = model.addVars(indices, lb=lb, ub=ub, vtype=vtype, name=name)
        return pd.Series(index=self._obj, data=x.values(), name=name)
