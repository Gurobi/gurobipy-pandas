Adding Nonlinear Constraints
============================

Gurobi 12 supports adding nonlinear constraints, using the ``NLExpr`` object to
capture nonlinear expressions. ``gurobipy-pandas`` supports adding a ``Series``
of nonlinear constraints to a model via ``add_constrs``. Note that ``gurobipy``
only supports nonlinear constraints of the form :math:`y = f(x)`, and
``gurobipy-pandas`` applies the same restriction.

.. note::

   To add nonlinear constraints, you must have at least ``gurobipy`` version
   12.0.0 installed.

Nonlinear Equality Constraints
------------------------------

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

Nonlinear Inequality Constraints
--------------------------------

As noted above, nonlinear constraints can only be provided in the form :math:`y=
f(x)`. To formulate inequality constraints, you must introduce bounded
intermediate variables. The following example formulates the set of constraints
:math:`\log(x_i^2 + 1) \le 2` by introducing intermediate variables :math:`z_i`
with no lower bound and an upper bound of :math:`2.0`.

.. doctest:: [nonlinear]

   >>> z = gppd.add_vars(model, index, lb=-GRB.INFINITY, ub=2.0, name="z")
   >>> constrs = gppd.add_constrs(model, z, GRB.EQUAL, (x**2 + 1).apply(nlfunc.log))

To see the effect of this constraint, you can set a maximization objective
:math:`\sum_{i=0}^{4} x_i` and solve the resulting model. You will find that the
original variables :math:`x_i` are maximized to :math:`\sqrt{e^2 - 1}` in
the optimal solution. The intermediate variables :math:`z_i` are at their upper
bounds, indicating that the constraint is satisfied with equality.

.. doctest:: [nonlinear]

   >>> model.setObjective(x.sum(), sense=GRB.MAXIMIZE)
   >>> model.optimize()  # doctest: +ELLIPSIS
   Gurobi Optimizer ...
   Optimal solution found ...
   >>> x.gppd.X.round(3)
   0    2.528
   1    2.528
   2    2.528
   3    2.528
   4    2.528
   Name: x, dtype: float64
   >>> z.gppd.X.round(3)
   0    2.0
   1    2.0
   2    2.0
   3    2.0
   4    2.0
   Name: z, dtype: float64
