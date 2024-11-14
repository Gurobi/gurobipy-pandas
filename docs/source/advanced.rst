Adding Specialized Constraints
==============================

``gurobipy-pandas`` helper methods currently only cover building linear and
quadratic constraints. In some cases you may need to build other constraint
types, such as SOS or general constraints, using pandas series of variables or
expressions. This page provides recommended recipes for such operations.

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

    >>> m = gp.Model()
    >>> index = pd.RangeIndex(5)
    >>> x = gppd.add_vars(m, index, name="x")
    >>> y = gppd.add_vars(m, index, name="y")

There is no built-in ``gurobipy-pandas`` method for this. You should first align
align your variable series in a dataframe, then iterate over the rows in the
result, creating a constraint for each row. To iterate over rows efficiently,
use ``.itertuples()``, and call the ``addSOS`` function on the Gurobi model.

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
    ...     c = m.addSOS(GRB.SOS_TYPE1, [row.x, row.y])
    ...     cs.append(c)
    >>> sos = pd.Series(index=df.index, data=cs, name="sos")

The resulting ``sos`` series captures the newly added SOS constraint objects.
