Welcome to gurobipy-pandas's documentation!
===========================================

:code:`gurobipy-pandas` is a convenient (optional) wrapper to connect Pandas with Gurobipy. This enables users to more easily and cleanly build optimization models from data stored in Pandas structures.

:code:`gurobipy-pandas` is aimed at experienced Pandas users, familiar with methods to transform and group data in dataframes, with some familiarity with optimization concepts.

The library uses Pandas' accessor API to extend the capabilities of indices, series, and dataframes. For example, given a simple dataframe, one can create Gurobi variables mapped to a dataframe index:

.. doctest:: [simple]

   >>> df
      a  b
   0  1  3
   1  2  4
   >>> df.grb.pd_add_vars(model, name='x')
      a  b                  x
   0  1  3  <gurobi.Var x[0]>
   1  2  4  <gurobi.Var x[1]>

Once variables are added, standard pandas transformations can be used to manipulate them into building expressions:

.. doctest:: [simple]

   >>> df
      a                  y
   0  1  <gurobi.Var y[0]>
   1  2  <gurobi.Var y[1]>
   2  2  <gurobi.Var y[2]>
   3  1  <gurobi.Var y[3]>
   >>> df.groupby('a').sum()
                                 y
   a
   1  <gurobi.LinExpr: y[0] + y[3]>
   2  <gurobi.LinExpr: y[1] + y[2]>

Finally, :code:`gurobipy-pandas` allows constraints to be built from the result:

.. doctest:: [simple]

   >>> df.groupby("a").sum().grb.pd_add_constrs(m, "y", gp.GRB.LESS_EQUAL, 1, name='c')
                                 y                     c
   a
   1  <gurobi.LinExpr: y[0] + y[3]>  <gurobi.Constr c[1]>
   2  <gurobi.LinExpr: y[1] + y[2]>  <gurobi.Constr c[2]>

To get to grips with the operation of :code:`gurobipy-pandas`, first see the Walkthrough which outlines key concepts and the design philosophy. Then, peruse our library of examples to see how complete models are built.

Index
-----

.. toctree::

   walkthrough
   examples
   api
