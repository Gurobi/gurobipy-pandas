Top Level Function Style
========================

Imports you'll need for this style:

.. doctest:: [toplevel]

    >>> import pandas as pd
    >>> import gurobipy as gp
    >>> from gurobipy import GRB
    >>> from gurobipy_pandas import pd_add_constrs, pd_add_vars

Create series variables based on pandas object:

.. doctest:: [toplevel]

    >>> model = gp.Model()
    >>> index = pd.RangeIndex(5)
    >>> x = pd_add_vars(model, index, name="x")
    >>> y = pd_add_vars(model, index, name="y")
    >>> model.update()
    >>> x
    0    <gurobi.Var x[0]>
    1    <gurobi.Var x[1]>
    2    <gurobi.Var x[2]>
    3    <gurobi.Var x[3]>
    4    <gurobi.Var x[4]>
    Name: x, dtype: object
    >>> y
    0    <gurobi.Var y[0]>
    1    <gurobi.Var y[1]>
    2    <gurobi.Var y[2]>
    3    <gurobi.Var y[3]>
    4    <gurobi.Var y[4]>
    Name: y, dtype: object

Create constraints from aligned series:

.. doctest:: [toplevel]

    >>> constrs = pd_add_constrs(model, x + y, GRB.EQUAL, 1.0, name="constr")
    >>> model.update()
    >>> constrs
    0    <gurobi.Constr constr[0]>
    1    <gurobi.Constr constr[1]>
    2    <gurobi.Constr constr[2]>
    3    <gurobi.Constr constr[3]>
    4    <gurobi.Constr constr[4]>
    Name: constr, dtype: object
