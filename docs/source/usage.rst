.. - The API (brief example illustrating all of this?)
..    - Add variables as series
..       - global functions, get back series
..       - dataframe accessor, append columns and method chain
..    - Use pandas arithmetic operations
..    - Build constraints by row
..       - global functions, get back series
..       - dataframe accessor, append columns and method chain
..    - gurobipy
..       - some parts of the gurobipy API need to be used in most models
..       - Env, Model, setObjective, sometimes addConstr or addVar for non-indexed variables/constraints
..    - Attribute access / series-wise queries
..       - series accessor
..       - See attributes pages on gurobi site

Usage
=====

:code:`gurobipy-pandas` implements pandas' `accessors <https://pandas.pydata.org/docs/ecosystem.html#accessors>`_ to extend the capabilities of series, and dataframes. For example, given a simple dataframe, one can create Gurobi variables mapped to a dataframe index:

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

To get to grips with the operation of :code:`gurobipy-pandas`, first see the xxxx which outlines key concepts and the design philosophy. Then, peruse our library of :doc:`examples` to see how complete models are built. The :doc:`api` documentation spells out the various accessor methods in more complete detail.


Function Patterns
-----------------

Imports you'll need for this pattern:

.. doctest:: [toplevel]

    >>> import pandas as pd
    >>> import gurobipy as gp
    >>> from gurobipy import GRB
    >>> import gurobipy_pandas as gppd

Some networky data to feed in:

.. doctest:: [toplevel]

    >>> data = pd.DataFrame(
    ...     {
    ...         "from": [1, 2, 1, 0, 3],
    ...         "to": [0, 1, 3, 2, 2],
    ...         "capacity": [0.3, 1.2, 0.7, 0.9, 1.2],
    ...         "cost": [1.3, 1.7, 1.4, 1.1, 0.9],
    ...     }
    ... ).set_index(["from", "to"])

Create a series of variables based on a pandas dataframe (dataframe may be used to set attributes):

.. doctest:: [toplevel]

    >>> model = gp.Model("networkflow")
    >>> flow = gppd.add_vars(
    ... model,
    ... data,
    ... ub="capacity",
    ... obj="cost",
    ... name="flow",
    ... )
    >>> model.update()
    >>> flow
    from  to
    1     0     <gurobi.Var flow[1,0]>
    2     1     <gurobi.Var flow[2,1]>
    1     3     <gurobi.Var flow[1,3]>
    0     2     <gurobi.Var flow[0,2]>
    3     2     <gurobi.Var flow[3,2]>
    Name: flow, dtype: object
    >>> flow.gppd.UB
    from  to
    1     0     0.3
    2     1     1.2
    1     3     0.7
    0     2     0.9
    3     2     1.2
    Name: flow, dtype: float64

Create constraints from aligned series:

.. doctest:: [toplevel]

    >>> constrs = gppd.add_constrs(
    ... model,
    ... flow.groupby("to").sum(),
    ... GRB.EQUAL,
    ... flow.groupby("from").sum(),
    ... )
    >>> model.update()
    >>> constrs
    0    <gurobi.Constr R0>
    1    <gurobi.Constr R1>
    2    <gurobi.Constr R2>
    3    <gurobi.Constr R3>
    dtype: object
    >>> constrs.apply(model.getRow)
    0                     flow[1,0] + -1.0 flow[0,2]
    1    -1.0 flow[1,0] + flow[2,1] + -1.0 flow[1,3]
    2         -1.0 flow[2,1] + flow[0,2] + flow[3,2]
    3                     flow[1,3] + -1.0 flow[3,2]
    dtype: object
    >>> constrs.gppd.Sense
    0    =
    1    =
    2    =
    3    =
    dtype: object
    >>> constrs.gppd.RHS
    0    0.0
    1    0.0
    2    0.0
    3    0.0
    dtype: float64
