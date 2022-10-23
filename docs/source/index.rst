Welcome to gurobipy-pandas's documentation!
===========================================

**This package is in beta development and not supported. The API may change without warning.**

-----

:code:`gurobipy-pandas` is a convenient (optional) wrapper to connect pandas with gurobipy. It enables users to more easily and cleanly build optimization models from data stored in pandas objects.

:code:`gurobipy-pandas` is aimed at experienced pandas users who are familiar with methods to transform and group data stored in dataframes. It expects some familiarity with optimization concepts, but does not require deep experience with gurobipy.

:code:`gurobipy-pandas` implements pandas' `accessors <https://pandas.pydata.org/docs/ecosystem.html#accessors>`_ to extend the capabilities of indices, series, and dataframes. For example, given a simple dataframe, one can create Gurobi variables mapped to a dataframe index:

.. doctest:: [simple]

   >>> import pandas as pd
   >>> import gurobipy as gp
   >>> from gurobipy import GRB
   >>> import gurobipy_pandas as gppd
   >>> gppd.set_interactive()
   >>> df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
   >>> df
      a  b
   0  1  3
   1  2  4
   >>> model = gp.Model()
   >>> df.gppd.add_vars(model, name='x')
      a  b                  x
   0  1  3  <gurobi.Var x[0]>
   1  2  4  <gurobi.Var x[1]>

Once variables are added, standard pandas transformations can be used to build expressions:

.. doctest:: [simple]

   >>> df = (
   ... pd.DataFrame({"a": [1, 2, 2, 1]})
   ... .gppd.add_vars(model, name="y")
   ... )
   >>> df
      a                  y
   0  1  <gurobi.Var y[0]>
   1  2  <gurobi.Var y[1]>
   2  2  <gurobi.Var y[2]>
   3  1  <gurobi.Var y[3]>
   >>> df.groupby('a').sum()  # doctest: +NORMALIZE_WHITESPACE
                y
   a
   1  y[0] + y[3]
   2  y[1] + y[2]

Finally, the accessors allow constraints to be added to the model using the resulting expressions:

.. doctest:: [simple]

   >>> gppd.add_constrs(
   ...     model, df.groupby("a")["y"].sum(), GRB.LESS_EQUAL, 1,
   ...     name="c",
   ... )
   a
   1    <gurobi.Constr c[1]>
   2    <gurobi.Constr c[2]>
   Name: c, dtype: object

To get to grips with the operation of :code:`gurobipy-pandas`, first see the :doc:`walkthrough` which outlines key concepts and the design philosophy. Then, peruse our library of :doc:`examples` to see how complete models are built. The :doc:`api` documentation spells out the various accessor methods in more complete detail.

Rewrite/Reorganize
------------------

1. Why this package?
   - Pandas is great at manipulating column structured data. However when building optimization models, that data needs to interact with modelling objects / row-wise operations need to be performed. This is not pandas' core competency, and it's easy to create performance headaches.
   - `gurobipy-pandas` provides a few simple functions/accessors/extensions to help build optimization models using pandas data structures (and query solutions, etc)
2. How to read/use this doc?
   - First read the pandas primer. Even if you're an experienced pandas user, have a read. Here we point out some key features and common pitfalls when ti comes to pandas and building optimization models in python.
      - Primer will point out column-wise data storage and emphasise that with this package, we provide fast implementations and convenient syntax for the inevitable row-wise operations that you need to create interesting constraints.
   - Read the API overview. `gurobipy-pandas`` consists of only two key methods, ...
      - This page should also note that the 'glue' for arithmetic operations is provided by pandas itself, but again, you should work series-wise when doing this
   - Read the examples
      - Put mathematical models next to their implementation in code
      - Emphasise data cleaning and where it should be done (before the model: this is model-data separation in python: do your cleaning steps first, then build the model in a quick pass with no intermingled data processing logic).

Index
-----

.. toctree::

   installation
   walkthrough
   function-patterns
   examples
   api
   naming
