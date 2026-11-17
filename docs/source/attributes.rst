Modifying Gurobi Attributes
===========================

Gurobi modeling objects expose type-specific attributes. Some are read-only,
while others control model data, such as variable bounds and constraint
right-hand sides. The `Gurobi attribute reference
<https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes.html>`_
lists the available attributes and whether each one can be modified.

A Series containing Gurobi objects exposes the same attributes through its
``gppd`` accessor. Assign a scalar to set the same value on every object, or
assign a pandas Series to set values by index.

The examples below use a small binary model.

.. doctest:: [attributes]

   >>> import pandas as pd
   >>> import gurobipy as gp
   >>> from gurobipy import GRB
   >>> import gurobipy_pandas as gppd
   >>> model = gp.Model()
   >>> items = pd.Index(["a", "b", "c"], name="item")
   >>> x = gppd.add_vars(model, items, vtype=GRB.BINARY, name="x")
   >>> limits = gppd.add_constrs(
   ...     model, x, GRB.LESS_EQUAL, 1, name="limit"
   ... )
   >>> model.update()

Changing variable bounds
------------------------

Set lower and upper bounds with the ``LB`` and ``UB`` attributes. Here the
lower bounds vary by item, while the scalar upper bound is applied to every
variable.

.. doctest:: [attributes]

   >>> x.gppd.LB = pd.Series([0, 1, 0], index=items)
   >>> x.gppd.UB = 1
   >>> model.update()
   >>> x.gppd.LB
   item
   a    0.0
   b    1.0
   c    0.0
   Name: x, dtype: float64
   >>> x.gppd.UB
   item
   a    1.0
   b    1.0
   c    1.0
   Name: x, dtype: float64

Changing constraint right-hand sides
------------------------------------

The same syntax works for constraint attributes. Assign to ``RHS`` to change
the right-hand side of each linear constraint.

.. doctest:: [attributes]

   >>> limits.gppd.RHS = pd.Series([1, 0, 1], index=items)
   >>> model.update()
   >>> limits.gppd.RHS
   item
   a    1.0
   b    0.0
   c    1.0
   Name: limit, dtype: float64

Setting a MIP start
-------------------

For a mixed-integer model, assign candidate solution values to the ``Start``
attribute. Gurobi will try to use these values when optimization begins.

.. doctest:: [attributes]

   >>> x.gppd.Start = pd.Series([1, 0, 1], index=items)
   >>> model.update()
   >>> x.gppd.Start
   item
   a    1.0
   b    0.0
   c    1.0
   Name: x, dtype: float64

Attribute updates are lazy, like updates made directly through ``gurobipy``.
Call :meth:`~gurobipy.Model.update` before reading the changed values if the
model has not otherwise been updated.

When assigning a Series, its index must match the target Gurobi-object Series
exactly. To set an attribute on only some objects, select those objects first:

.. doctest:: [attributes]

   >>> partial_start = pd.Series([0, 1], index=["a", "c"])
   >>> x.loc[partial_start.index].gppd.Start = partial_start

The explicit :meth:`~gurobipy_pandas.GRBSeriesAccessor.set_attr` and
:meth:`~gurobipy_pandas.GRBSeriesAccessor.get_attr` methods provide equivalent
functionality when the attribute name is stored in a string.
