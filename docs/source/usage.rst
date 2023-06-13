Usage
=====

This page gives a brief run through of methods used to build optimization models in ``gurobipy-pandas`` and extract solutions. ``gurobipy-pandas`` provides several free functions for model building, and implements pandas' `accessors <https://pandas.pydata.org/docs/ecosystem.html#accessors>`_ to facilitate building models and querying results from dataframes and series respectively.

Standard Imports
----------------

Most ``gurobipy-pandas`` applications will start with the following imports.

.. doctest:: [usage]

   >>> import pandas as pd
   >>> import gurobipy as gp
   >>> from gurobipy import GRB
   >>> import gurobipy_pandas as gppd

Interactive Mode
----------------

When working in an interactive environment (such as the IPython shell or a Jupyter notebook) it can be helpful to use interactive mode. This makes it easier to inspect changes to an optimization model as you are building it. There is a performance hit for doing this, so while most examples in this documentation use interactive mode, you should in general remove it for production applications where speed is a concern. The following command enables interactive mode:

.. doctest:: [usage]

   >>> gppd.set_interactive()

Creating a Model
----------------

.. doctest:: [usage]

   >>> model = gp.Model()

Creating Variables
------------------

In ``gurobipy-pandas``, variables are always created aligned with an index. To create a Series of variables, use ``gppd.add_vars``. Note that you can pass the ``name`` argument to automatically construct names based on the index of the input DataFrame, and set other attributes such as upper bounds by referencing columns in the input DataFrame.

.. doctest:: [usage]

   >>> data = pd.DataFrame(
   ...     {
   ...         "i": [0, 0, 1, 2, 2],
   ...         "j": [1, 2, 0, 0, 1],
   ...         "u": [0.3, 1.2, 0.7, 0.9, 1.2],
   ...         "c": [1.3, 1.7, 1.4, 1.1, 0.9],
   ...     }
   ... ).set_index(["i", "j"])
   >>> data  # doctest: +NORMALIZE_WHITESPACE
          u    c
   i j
   0 1  0.3  1.3
     2  1.2  1.7
   1 0  0.7  1.4
   2 0  0.9  1.1
     1  1.2  0.9
   >>> x = gppd.add_vars(model, data, name="x", ub="u")
   >>> x
   i  j
   0  1    <gurobi.Var x[0,1]>
      2    <gurobi.Var x[0,2]>
   1  0    <gurobi.Var x[1,0]>
   2  0    <gurobi.Var x[2,0]>
      1    <gurobi.Var x[2,1]>
   Name: x, dtype: object

You can also use the DataFrame ``gppd`` accessor to create variables. The distinction between the two methods is that the accessor returns a new DataFrame with variables appended as new columns, allowing method chaining.

.. doctest:: [usage]

   >>> variables = (
   ...     data.gppd.add_vars(model, name="y")
   ...     .gppd.add_vars(model, name="z")
   ... )
   >>> variables  # doctest: +NORMALIZE_WHITESPACE
          u    c                    y                    z
   i j
   0 1  0.3  1.3  <gurobi.Var y[0,1]>  <gurobi.Var z[0,1]>
     2  1.2  1.7  <gurobi.Var y[0,2]>  <gurobi.Var z[0,2]>
   1 0  0.7  1.4  <gurobi.Var y[1,0]>  <gurobi.Var z[1,0]>
   2 0  0.9  1.1  <gurobi.Var y[2,0]>  <gurobi.Var z[2,0]>
     1  1.2  0.9  <gurobi.Var y[2,1]>  <gurobi.Var z[2,1]>

Arithmetic Expressions
----------------------

Building linear and quadratic expressions from variables is handled using standard pandas methods. For example, you can use arithmetic operations to create relationships across rows:

.. doctest:: [usage]

   >>> variables["y"] + variables["z"]
   i  j
   0  1    y[0,1] + z[0,1]
      2    y[0,2] + z[0,2]
   1  0    y[1,0] + z[1,0]
   2  0    y[2,0] + z[2,0]
      1    y[2,1] + z[2,1]
   dtype: object

And you can use groupby and aggregate to build summations across different levels of an index:

.. doctest:: [usage]

   >>> x.groupby("i").sum()
   i
   0        x[0,1] + x[0,2]
   1    <gurobi.Var x[1,0]>
   2        x[2,0] + x[2,1]
   Name: x, dtype: object
   >>> x.groupby("j").sum()
   j
   0        x[1,0] + x[2,0]
   1        x[0,1] + x[2,1]
   2    <gurobi.Var x[0,2]>
   Name: x, dtype: object

Note that the builtin ``.sum`` in pandas can be slow when working with a huge number of ``gurobipy`` modelling objects. In such applications, you should use ``.agg(gp.quicksum)`` instead. See :doc:`the performance section<performance>` of the documentation for further details.

Adding Constraints
------------------

Constraints are added row-wise. Similarly to adding variables, you have the option of using a free function or a dataframe accessor. The free function accepts series aligned on the same index to construct constraints, returning new constraints as a series. The following expresses the constraint :math:`x \le y` for each entry in the index:

.. doctest:: [usage]

   >>> gppd.add_constrs(  # doctest: +NORMALIZE_WHITESPACE
   ...     model,
   ...     variables.groupby("j")["y"].sum(),
   ...     GRB.LESS_EQUAL,
   ...     variables.groupby("i")["y"].sum(),
   ...     name="c1",
   ... )
   0    <gurobi.Constr c1[0]>
   1    <gurobi.Constr c1[1]>
   2    <gurobi.Constr c1[2]>
   Name: c1, dtype: object

While the dataframe accessor takes column name references to build constraints:

.. doctest:: [usage]

   >>> variables.gppd.add_constrs(  # doctest: +NORMALIZE_WHITESPACE
   ...     model, "y", GRB.LESS_EQUAL, "z", name="c1"
   ... )
          u    c                    y                    z                       c1
   i j
   0 1  0.3  1.3  <gurobi.Var y[0,1]>  <gurobi.Var z[0,1]>  <gurobi.Constr c1[0,1]>
     2  1.2  1.7  <gurobi.Var y[0,2]>  <gurobi.Var z[0,2]>  <gurobi.Constr c1[0,2]>
   1 0  0.7  1.4  <gurobi.Var y[1,0]>  <gurobi.Var z[1,0]>  <gurobi.Constr c1[1,0]>
   2 0  0.9  1.1  <gurobi.Var y[2,0]>  <gurobi.Var z[2,0]>  <gurobi.Constr c1[2,0]>
     1  1.2  0.9  <gurobi.Var y[2,1]>  <gurobi.Var z[2,1]>  <gurobi.Constr c1[2,1]>

You can also use a string syntax similar to pandas' eval method to build the same constraint concisely:

.. doctest:: [usage]

   >>> variables.gppd.add_constrs(  # doctest: +NORMALIZE_WHITESPACE
   ...     model, "y + z <= 1", name="c1"
   ... )
          u    c                    y                    z                       c1
   i j
   0 1  0.3  1.3  <gurobi.Var y[0,1]>  <gurobi.Var z[0,1]>  <gurobi.Constr c1[0,1]>
     2  1.2  1.7  <gurobi.Var y[0,2]>  <gurobi.Var z[0,2]>  <gurobi.Constr c1[0,2]>
   1 0  0.7  1.4  <gurobi.Var y[1,0]>  <gurobi.Var z[1,0]>  <gurobi.Constr c1[1,0]>
   2 0  0.9  1.1  <gurobi.Var y[2,0]>  <gurobi.Var z[2,0]>  <gurobi.Constr c1[2,0]>
     1  1.2  0.9  <gurobi.Var y[2,1]>  <gurobi.Var z[2,1]>  <gurobi.Constr c1[2,1]>

Note that you *must* correctly align all data, and fill values when necessary, when adding constraints. Missing data is not allowed and will throw an error. This is by design, as misaligned data and variables likely indicates a bug in model building logic.

``gurobipy`` methods
--------------------

In some cases, you will need to call ``gurobipy`` methods directly, using expressions produced from pandas series or dataframes. A common example is setting an objective, since this is not done per-row but from a single expression.

.. doctest:: [usage]

   >>> (x * data["c"]).sum()
   <gurobi.LinExpr: 1.3 x[0,1] + 1.7 x[0,2] + 1.4 x[1,0] + 1.1 x[2,0] + 0.9 x[2,1]>
   >>> model.setObjective((x * data["c"]).sum(), sense=GRB.MAXIMIZE)

Solving the model
-----------------

.. doctest:: [usage]

   >>> model.optimize()  # doctest: +ELLIPSIS
   Gurobi Optimizer version...
   ...
   Optimal objective  5.480000000e+00

Extracting solutions
--------------------

Variable values in the optimal solution can be extracted using the series accessor.

.. doctest:: [usage]

   >>> x.gppd.X
   i  j
   0  1    0.3
      2    1.2
   1  0    0.7
   2  0    0.9
      1    1.2
   Name: x, dtype: float64
