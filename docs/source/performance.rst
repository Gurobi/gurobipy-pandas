Performance
===========

This section contains general advice for improving the performance of model building code in ``gurobipy-pandas``.

Prepare data first
------------------

You should always prepare your data well before initializing a model and creating variables and constraints. There are two key reasons for this:

1. Once all data is aligned on appropriate indices, it is simple to construct variables which are properly aligned to the data using the ``add_vars`` methods. With properly aligned variables and data, building set of constraints using the ``add_constrs`` methods is straightforward and does not require complex logic in code.
2. If data is appropriately filtered before the model is built, you can reduce the size of the model passed to Gurobi.

Take advantage of sparsity
--------------------------

Most mathematical optimization models have sparse index sets. Pandas indexes provide a flexible and powerful way to represent this sparsity, and to filter datasets down to only those records needed for modelling.  ``gurobipy-pandas`` users can leverage this to avoid the creation of redundant variables and constraints, reducing the size of their models.

This is best illustrated by example. In the :doc:`project allocation example <examples/projects>`, pandas' filtering mechanisms are used to compute the subset of allowed assignments *before* formulating the model. In the :doc:`workforce management example<examples/workforce>`, the input dataset is already sparse, which dictates the variables that need to be created. By setting up appropriate indices for the data, we only create those variables necessary to represent valid decisions in the model.

Avoid iterating over DataFrames
-------------------------------

Row-wise operations which mix data types in pandas can be slow. However, this is exactly the type of operation required to build constraints for optimization models (mixing data and modelling objects). ``gurobipy-pandas`` provides efficient implementations to build constraints from rows that avoid these performance pitfalls. However, you still need to be careful to use efficient operations when processing your data in the first place to keep your code performant.

So, in general, you should avoid iterating manually over rows in a dataframe in your own code. Patterns to avoid are:

- Using a for loop and indexing into a dataframe or series using ``.iloc``, ``.loc``, or ``[]``
- Using ``.iterrows()`` (see :doc:`advanced patterns<advanced>`: ``itertuples()`` is preferred)
- Using ``.apply()`` with a user-defined function which processes rows

In some cases, you will have to manually construct constraints per-row in a dataframe, for example for constraint types which ``gurobipy-pandas`` does not handle. For guidance on implementing such cases efficiently, see :doc:`advanced`.

Use ``.agg(gp.quicksum)`` over ``.sum()``
-----------------------------------------

For summations over series of ``gurobipy`` variables, pandas' built-in implementation of ``.sum()`` can be slow. You will find for large models it is worthwhile to replace ``.sum()`` calls with ``.agg(gp.quicksum)`` to improve performance. The ``quicksum`` function in gurobipy is designed to work efficiently with gurobipy objects. It gives the same result as built-in python ``sum`` functions, with lower overhead.

.. doctest:: [performance]

    >>> import pandas as pd
    >>> import gurobipy as gp
    >>> from gurobipy import GRB
    >>> import gurobipy_pandas as gppd
    >>> gppd.set_interactive()

    >>> m = gp.Model()
    >>> x = gppd.add_vars(m, pd.Index([0, 1, 2]), name='x')
    >>> x.sum()
    <gurobi.LinExpr: x[0] + x[1] + x[2]>
    >>> x.agg(gp.quicksum)
    <gurobi.LinExpr: x[0] + x[1] + x[2]>
