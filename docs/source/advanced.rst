Adding Specialized Constraints
==============================

``gurobipy-pandas`` helper methods currently only cover building linear and
quadratic constraints. In some cases you may need to build other constraint
types, such as SOS or general constraints, using pandas series of variables or
expressions. This page provides recommended recipes for such operations.

Indicator Constraints
---------------------

This example builds a set of indicator constraints, such that the linear
constraint :math:`x_i + y_i \le 1.0` is enforced if the corresponding binary
variable :math:`z_i` is equal to 1.

.. doctest:: [indicator]

    >>> import pandas as pd
    >>> import gurobipy as gp
    >>> from gurobipy import GRB
    >>> import gurobipy_pandas as gppd
    >>> gppd.set_interactive()

    >>> model = gp.Model()
    >>> index = pd.RangeIndex(5)
    >>> x = gppd.add_vars(model, index, name="x")
    >>> y = gppd.add_vars(model, index, name="y")
    >>> z = gppd.add_vars(model, index, vtype=GRB.BINARY, name="z")

There is no built-in ``gurobipy-pandas`` method to add this constraint type. To
add indicator constraints, align your variables in a dataframe, then iterate
over the rows, creating a constraint for each row. To iterate over rows
efficiently, use ``.itertuples()``, and call the ``addGenConstrIndicator``
function of the Gurobi model.

.. doctest:: [indicator]

   >>> df = pd.DataFrame({"z": z, "expression": x + y})
   >>> df
                      z   expression
   0  <gurobi.Var z[0]>  x[0] + y[0]
   1  <gurobi.Var z[1]>  x[1] + y[1]
   2  <gurobi.Var z[2]>  x[2] + y[2]
   3  <gurobi.Var z[3]>  x[3] + y[3]
   4  <gurobi.Var z[4]>  x[4] + y[4]
   >>> constrs = []
   >>> for row in df.itertuples(index=False):
   ...     constr = model.addGenConstrIndicator(
   ...         row.z, 1.0, row.expression, GRB.LESS_EQUAL, 1.0
   ...     )
   ...     constrs.append(constr)
   >>> indicators = pd.Series(index=df.index, data=constrs, name="ind")

The resulting ``indicators`` series stores the indicator constraint objects.

SOS Constraints
---------------

This example builds the constraint set :math:`\text{SOS1}(x_i, y_i)` for each
:math:`i` in the index.

.. doctest:: [advanced]

    >>> import pandas as pd
    >>> import gurobipy as gp
    >>> from gurobipy import GRB
    >>> import gurobipy_pandas as gppd
    >>> gppd.set_interactive()

    >>> model = gp.Model()
    >>> index = pd.RangeIndex(5)
    >>> x = gppd.add_vars(model, index, name="x")
    >>> y = gppd.add_vars(model, index, name="y")

There is no built-in ``gurobipy-pandas`` method to add this constraint type. To
add SOS constraints, align your variables in a dataframe, then iterate over the
rows, creating a constraint for each row. To iterate over rows efficiently, use
``.itertuples()``, and call the ``addSOS`` function of the Gurobi model.

.. doctest:: [advanced]

    >>> df = pd.DataFrame({"x": x, "y": y})
    >>> df
                       x                  y
    0  <gurobi.Var x[0]>  <gurobi.Var y[0]>
    1  <gurobi.Var x[1]>  <gurobi.Var y[1]>
    2  <gurobi.Var x[2]>  <gurobi.Var y[2]>
    3  <gurobi.Var x[3]>  <gurobi.Var y[3]>
    4  <gurobi.Var x[4]>  <gurobi.Var y[4]>
    >>> cs = []
    >>> for row in df.itertuples(index=False):
    ...     c = model.addSOS(GRB.SOS_TYPE1, [row.x, row.y])
    ...     cs.append(c)
    >>> sos = pd.Series(index=df.index, data=cs, name="sos")

The resulting ``sos`` series captures the newly added SOS constraint objects.
