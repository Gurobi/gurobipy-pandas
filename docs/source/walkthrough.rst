Walkthrough
===========

Implementing mathematical programming models in code requires transforming a dataset into a model. Pandas excels at storing and manipulating data, but it is not always clear how best to transform data to help interact with the modelling features of gurobipy in order to build a concrete model. This linking package aims to define a convenient API for doing so.

Consider a classical model such as the Multiple Knapsack Problem, which aims to assign items to one of several knapsacks, respecting their capacities, so that the total value of carried items is maximized. The model is defined as:

.. math::

    \begin{alignat}{2}
    \min \quad        & \sum_{i \in I} \sum_{k \in K} p_{i} x_{ik} \\
    \mbox{s.t.} \quad & \sum_{i \in I} w_{i} x_{ik} \le W_{k} & \forall k \in K \\
                      & \sum_{k \in K} x_{ik} \le 1 & \forall i \in I \\\
                      & x_{ik} \in \lbrace 0, 1 \rbrace & \forall i \in I, k \in K. \\
    \end{alignat}

Defined this way, we can see that the model is defined based on its indices :math:`i` (items) and :math:`k` (knapsacks). The model data is defined using these indices: item weights :math:`w_i`, item values :math:`p_j`, and knapsack capacities :math:`W_k`. This data must be associated with variables :math:`x_{ij}` (defined over the same indices) in order to build concrete instantiations of the constraints and objective in the model.

Imports you'll need for all :code:`gurobipy_pandas` applications:

.. doctest:: [knapsack]

    >>> import pandas as pd
    >>> import gurobipy as gp
    >>> from gurobipy import GRB
    >>> import gurobipy_pandas as gppd

Pandas conveniently stores data in relation to indexes, so we would naturally define the data for items in a single DataFrame (with columns for weights and profits).

.. doctest:: [knapsack]

    >>> items = pd.Index([1, 2, 3, 4, 5], name="item")
    >>> item_data = pd.DataFrame(index=items, data={
    ...     "weight": [1.0, 1.5, 1.2, 0.9, 0.7],
    ...     "value": [0.5, 1.2, 0.3, 0.7, 0.9],
    ... })
    >>> item_data  # doctest: +NORMALIZE_WHITESPACE
          weight  value
    item
    1        1.0    0.5
    2        1.5    1.2
    3        1.2    0.3
    4        0.9    0.7
    5        0.7    0.9

Data for knapsacks fits more naturally in a Series, since there is only one data point per knapsack.

.. doctest:: [knapsack]

    >>> knapsacks = pd.Index([1, 2], name="knapsack")
    >>> knapsack_capacity = pd.Series(
    ...     index=knapsacks, data=[2.0, 1.5], name="capacity",
    ... )
    >>> knapsack_capacity
    knapsack
    1    2.0
    2    1.5
    Name: capacity, dtype: float64

The model contains a variable for every index pair. Pandas provides a convenient construction to express all the indices for :math:`x_{ij}` as a multi-index. We can then join the item data onto this index (this helps us later to align data with variables).

.. doctest:: [knapsack]

    >>> df_pairs = pd.DataFrame(
    ...    index=pd.MultiIndex.from_product([items, knapsacks])
    ... ).join(item_data)
    >>> df_pairs    # doctest: +NORMALIZE_WHITESPACE
                   weight  value
    item knapsack
    1    1            1.0    0.5
         2            1.0    0.5
    2    1            1.5    1.2
         2            1.5    1.2
    3    1            1.2    0.3
         2            1.2    0.3
    4    1            0.9    0.7
         2            0.9    0.7
    5    1            0.7    0.9
         2            0.7    0.9

From the above dataframe, :code:`gurobipy_pandas` provides an accessor to create a corresponding series of variables. We first create a gurobipy Model, then call :code:`.gppd.add_vars` on our new dataframe to create a Gurobi variable for every entry in the index. The result is a Pandas dataframe containing Gurobi variables. Note the objective coefficients can be set directly on the variables as they are created, using the aligned item value data.

.. doctest:: [knapsack]

    >>> m = gp.Model()
    >>> df_assign = df_pairs.gppd.add_vars(
    ...    m, name='x', vtype=GRB.BINARY, obj="value"
    ... )
    >>> m.ModelSense = GRB.MAXIMIZE
    >>> m.update()
    >>> df_assign    # doctest: +NORMALIZE_WHITESPACE
                   weight  value                    x
    item knapsack
    1    1            1.0    0.5  <gurobi.Var x[1,1]>
         2            1.0    0.5  <gurobi.Var x[1,2]>
    2    1            1.5    1.2  <gurobi.Var x[2,1]>
         2            1.5    1.2  <gurobi.Var x[2,2]>
    3    1            1.2    0.3  <gurobi.Var x[3,1]>
         2            1.2    0.3  <gurobi.Var x[3,2]>
    4    1            0.9    0.7  <gurobi.Var x[4,1]>
         2            0.9    0.7  <gurobi.Var x[4,2]>
    5    1            0.7    0.9  <gurobi.Var x[5,1]>
         2            0.7    0.9  <gurobi.Var x[5,2]>

Check the constructed objective function:

.. doctest:: [knapsack]

    >>> m.getObjective()
    <gurobi.LinExpr: 0.5 x[1,1] + 0.5 x[1,2] + 1.2 x[2,1] + 1.2 x[2,2] + 0.3 x[3,1] + 0.3 x[3,2] + 0.7 x[4,1] + 0.7 x[4,2] + 0.9 x[5,1] + 0.9 x[5,2]>

Finally, we can build the capacity constraints by using the "knapsack" index to group variables along with their weights:

.. doctest:: [knapsack]

    >>> total_weight = (
    ...     (df_assign["weight"] * df_assign["x"])
    ...     .groupby("knapsack").sum()
    ... )
    >>> total_weight  # doctest: +ELLIPSIS
    knapsack
    1    x[1,1] + 1.5 x[2,1] + 1.2 x[3,1] + ...
    2    x[1,2] + 1.5 x[2,2] + 1.2 x[3,2] + ...
    dtype: object

and using the function :code:`gppd.add_constrs` to create constraints by aligning these expressions with capacity data:

.. doctest:: [knapsack]

    >>> c1 = gppd.add_constrs(
    ...     m, total_weight, GRB.LESS_EQUAL, knapsack_capacity,
    ...     name='capconstr'
    ... )
    >>> m.update()
    >>> c1
    knapsack
    1    <gurobi.Constr capconstr[1]>
    2    <gurobi.Constr capconstr[2]>
    Name: capconstr, dtype: object

We also need constraints that each item only appears in one knapsack. This can be done using the same function:

.. doctest:: [knapsack]

    >>> c2 = gppd.add_constrs(
    ...     m, df_assign['x'].groupby('item').sum(),
    ...     GRB.LESS_EQUAL, 1.0, name="c",
    ... )
    >>> m.update()
    >>> c2  # doctest: +NORMALIZE_WHITESPACE
    item
    1    <gurobi.Constr c[1]>
    2    <gurobi.Constr c[2]>
    3    <gurobi.Constr c[3]>
    4    <gurobi.Constr c[4]>
    5    <gurobi.Constr c[5]>
    Name: c, dtype: object

Solving the model ...

.. doctest:: [knapsack]

    >>> m.optimize()  # doctest: +ELLIPSIS
    Gurobi Optimizer ...
    Best objective 2.800000000000e+00, best bound 2.800000000000e+00, gap 0.0000%

Finally, we use the series accessor :code:`.gppd.X` to retrieve solution values. Using Pandas functions we can transform the result into a more readable form. Below shows that items 4 and 5 are packed into knapsack 1, while only item 2 is packed into knapsack 2.

.. doctest:: [knapsack]

    >>> df_assign['x'].gppd.X.unstack().abs()  # doctest: +NORMALIZE_WHITESPACE
    knapsack    1    2
    item
    1         0.0  0.0
    2         0.0  1.0
    3         0.0  0.0
    4         1.0  0.0
    5         1.0  0.0

We can also use the series access :code:`.gppd.Slack` on constraint series to determine constraint slacks. For example, the following shows spare capacity in each knapsack based on the capacity constraint.

.. doctest:: [knapsack]

    >>> c1.gppd.Slack
    knapsack
    1    0.4
    2    0.0
    Name: capconstr, dtype: float64
