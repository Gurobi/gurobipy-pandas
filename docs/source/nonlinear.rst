Adding Nonlinear Constraints
============================

.. note::

   To add nonlinear constraints, you must have at least ``gurobipy`` version
   12.0.0 installed.

This example builds the constraint set :math:`y_i = \log(x_i)`, for each
:math:`i` in the index.

.. doctest:: [nonlinear]

    >>> import pandas as pd
    >>> import gurobipy as gp
    >>> from gurobipy import GRB
    >>> from gurobipy import nlfunc
    >>> import gurobipy_pandas as gppd
    >>> gppd.set_interactive()

    >>> model = gp.Model()
    >>> index = pd.RangeIndex(5)
    >>> x = gppd.add_vars(model, index, name="x")
    >>> y = gppd.add_vars(model, index, name="y")

The ``nlfunc`` module of gurobipy is used to create nonlinear expressions. You
can use ``apply`` to construct a series representing the logarithm of each
variable in the series:

.. doctest:: [nonlinear]

   >>> x.apply(nlfunc.log)
   0    log(x[0])
   1    log(x[1])
   2    log(x[2])
   3    log(x[3])
   4    log(x[4])
   Name: x, dtype: object

Similarly, you can use operator overloading to construct other nonlinear
expressions:

.. doctest:: [nonlinear]

   >>> x / y
   0    x[0] / y[0]
   1    x[1] / y[1]
   2    x[2] / y[2]
   3    x[3] / y[3]
   4    x[4] / y[4]
   dtype: object

The resulting expressions can be added as constraints using ``add_constrs``.
Note that you can only provide nonlinear constraints in the form :math:`y =
f(x)`. Therefore the ``lhs`` argument must be a series of ``Var`` objects, while
the ``sense`` argument must be ``GRB.EQUAL``.

.. doctest:: [nonlinear]

   >>> gppd.add_constrs(model, y, GRB.EQUAL, x.apply(nlfunc.log), name="log_x")
   0    <gurobi.GenConstr 0>
   1    <gurobi.GenConstr 1>
   2    <gurobi.GenConstr 2>
   3    <gurobi.GenConstr 3>
   4    <gurobi.GenConstr 4>
   Name: log_x, dtype: object
