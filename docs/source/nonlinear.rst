Adding Nonlinear Constraints
============================

Gurobi 12 introduced nonlinear constraints, using the ``NLExpr`` object to
capture nonlinear expressions. ``gurobipy-pandas`` supports adding a ``Series``
of nonlinear constraints to a model via ``add_constrs``.

.. note::

   To add nonlinear constraints, you must have at least ``gurobipy`` version
   12.0.0 installed. With ``gurobipy`` 14 or later, nonlinear constraints may
   be written in general form, with a nonlinear expression on either side and
   any constraint sense, and are added with ``Model.addNLConstr``. With
   ``gurobipy`` 12 and 13, only constraints of the form :math:`y = f(\bar{x})`
   are supported; see `Restrictions in Gurobi 12 and 13`_ below.

Nonlinear Equality Constraints
------------------------------

This example builds the constraint set :math:`y_i = \log(\frac{1}{x_i})`, for
each :math:`i` in the index.

.. doctest:: [nonlinear]

    >>> import pandas as pd
    >>> import gurobipy as gp
    >>> from gurobipy import GRB
    >>> from gurobipy import nlfunc
    >>> import gurobipy_pandas as gppd
    >>> gppd.set_interactive()

    >>> model = gp.Model()
    >>> index = pd.RangeIndex(5)
    >>> x = gppd.add_vars(model, index, lb=1.0, name="x")
    >>> y = gppd.add_vars(model, index, lb=-GRB.INFINITY, name="y")

You can create nonlinear expressions using standard Python operators. A
nonlinear expression is any expression which is not a polynomial of degree at
most 2. For example, dividing a constant by a series of ``Var`` objects produces
a series of nonlinear expressions.

.. doctest:: [nonlinear]

   >>> 1 / x
   0    1.0 / x[0]
   1    1.0 / x[1]
   2    1.0 / x[2]
   3    1.0 / x[3]
   4    1.0 / x[4]
   Name: x, dtype: object

The ``nlfunc`` module of gurobipy is used to create nonlinear expressions
involving mathematical functions. You can use ``apply`` to construct a series
representing the logarithm of the above result.

.. doctest:: [nonlinear]

   >>> (1 / x).apply(nlfunc.log)
   0    log(1.0 / x[0])
   1    log(1.0 / x[1])
   2    log(1.0 / x[2])
   3    log(1.0 / x[3])
   4    log(1.0 / x[4])
   Name: x, dtype: object

This series of expressions can be added as constraints using ``add_constrs``.
The nonlinear expression may appear on either side of the constraint, and the
sense may be ``GRB.EQUAL``, ``GRB.LESS_EQUAL`` or ``GRB.GREATER_EQUAL``.

.. doctest:: [nonlinear]

   >>> gppd.add_constrs(model, y, GRB.EQUAL, (1 / x).apply(nlfunc.log), name="log_x")
   0    <gurobi.NLConstr log_x[0]>
   1    <gurobi.NLConstr log_x[1]>
   2    <gurobi.NLConstr log_x[2]>
   3    <gurobi.NLConstr log_x[3]>
   4    <gurobi.NLConstr log_x[4]>
   Name: log_x, dtype: object

Nonlinear Inequality Constraints
--------------------------------

Nonlinear inequality constraints are added in the same way. The following
example formulates the set of constraints :math:`\log(x_i^2 + 1) \le 2`
directly.

.. doctest:: [nonlinear]

   >>> constrs = gppd.add_constrs(model, (x**2 + 1).apply(nlfunc.log), GRB.LESS_EQUAL, 2.0)

To see the effect of this constraint, you can set a maximization objective
:math:`\sum_{i=0}^{4} x_i` and solve the resulting model. You will find that the
original variables :math:`x_i` are maximized to :math:`\sqrt{e^2 - 1}` in
the optimal solution.

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

Restrictions in Gurobi 12 and 13
--------------------------------

Before Gurobi 14, ``gurobipy`` only supports nonlinear constraints of the form
:math:`y = f(\bar{x})`, added with ``Model.addGenConstrNL``, and
``gurobipy-pandas`` applies the same restriction when one of these versions is
installed. The ``lhs`` argument must be a series of ``Var`` objects, the
``sense`` argument must be ``GRB.EQUAL``, and the ``rhs`` a series of nonlinear
expressions. Anything else raises a ``ValueError``. The constraints returned
are ``GenConstr`` objects.

To formulate inequality constraints, introduce bounded intermediate variables.
For example, :math:`\log(x_i^2 + 1) \le 2` can be written as :math:`z_i =
\log(x_i^2 + 1)` where :math:`z_i` has no lower bound and an upper bound of
:math:`2.0`.

.. code-block:: python

   z = gppd.add_vars(model, index, lb=-GRB.INFINITY, ub=2.0, name="z")
   constrs = gppd.add_constrs(model, z, GRB.EQUAL, (x**2 + 1).apply(nlfunc.log))
