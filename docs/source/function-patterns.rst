Function Patterns
=================

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
