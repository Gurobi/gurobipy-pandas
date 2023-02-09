---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.4
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Network flow modelling examples

```{code-cell} ipython3
import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import gurobipy_pandas as gppd

gppd.set_interactive()
gp.setParam('OutputFlag', 0)
```

## Min-cost flow network for max-flow computation

The following example sets up a min-cost flow network for computing maximum flow through a network. In general, network data should be stored as a multi-indexed dataframe, where:

- A row in the dataframe corresponds to an edge.
- The (from, to) pair in the index of a given row represents the direction of the arc.
- Data columns store edge attributes. In most cases this will be capacity and cost.

A basic assumption here is that the network is sparsely connected, and all edges are represented in the dataframe. So, if a (from, to) edge pair is not represented in `arc_data`, then the network does not contain an edge between this pair.

```{code-cell} ipython3
arc_data = pd.DataFrame([
    # Main components of the network: limited-capacity arcs
    {"from": 0, "to": 1, "capacity": 16, "cost": 0},
    {"from": 0, "to": 2, "capacity": 13, "cost": 0},
    {"from": 1, "to": 2, "capacity": 10, "cost": 0},
    {"from": 2, "to": 1, "capacity": 4, "cost": 0},
    {"from": 1, "to": 3, "capacity": 12, "cost": 0},
    {"from": 3, "to": 2, "capacity": 9, "cost": 0},
    {"from": 2, "to": 4, "capacity": 14, "cost": 0},
    {"from": 4, "to": 3, "capacity": 7, "cost": 0},
    {"from": 3, "to": 5, "capacity": 20, "cost": 0},
    {"from": 4, "to": 5, "capacity": 4, "cost": 0},
    # Add an uncapacitated edge from sink to source
    {"from": 5, "to": 0, "capacity": np.inf, "cost": -1},
]).set_index(["from", "to"])

arc_data
```

Min-cost network flow takes a simple and repeatable form. First, use the `.gppd.add_vars` dataframe accessor to add a flow variable for each arc in the network.

```{code-cell} ipython3
model = gp.Model("max-flow")
model.ModelSense = GRB.MINIMIZE

arc_df = arc_data.gppd.add_vars(
    model, ub="capacity", obj="cost", name="flow"
)
arc_df
```

Using the `obj` attribute of the above method, and setting the model objective sense to minimization, sets up the linear objective function. In this case, the objective ultimately maximises the flow through the uncapacitated sink-source edge.

```{code-cell} ipython3
model.getObjective()
```

Flow constraints are simple to formulate using pandas `groupby` operations. Since the `arc_df` dataframe, containing arc attributes and flow variables, is indexed by from and to entries, we can group by each key to create linear expressions for inflow and outflow of each node in the network.

The inflow and outflow expressions are best grouped together in a single dataframe. This allows us to use the `.gppd.add_constrs` dataframe accessor to construct flow balance constraints.

```{code-cell} ipython3
constrs = (
    pd.DataFrame({
        "outflow": arc_df["flow"].groupby("from").sum(),
        "inflow": arc_df["flow"].groupby("to").sum(),
    })
    .gppd.add_constrs(model, "outflow == inflow", name="balance")
)
model.update()
constrs
```

Do some quick debugging checks to show the constraints were constructed as expected:

```{code-cell} ipython3
constrs['balance'].apply(model.getRow)
```

```{code-cell} ipython3
constrs['balance'].gppd.RHS
```

Solve the model, and extract the arc flows using the series accessors implemented in `gurobipy-pandas`:

```{code-cell} ipython3
model.optimize()
arc_df["flow"].gppd.X
```

It's also possible to use the constraints dataframe to compute total inflows and outflows from each node, based on the current solution, since it contains all the relevant linear expressions.

```{code-cell} ipython3
(
    constrs
    .assign(
        inflow_result=lambda df: df['inflow'].apply(gp.LinExpr).gppd.get_value(),
        outflow_result=lambda df: df['outflow'].apply(gp.LinExpr).gppd.get_value(),
    )
)
```

## Networks with demand nodes

Another model we might want to tackle is a network consisting of different node types:

- transshipment nodes with no demand or supply
- supply nodes with an external input
- demand nodes with an external output

The input dataframe structure for the network is the same here. Again, the model is structured such that if an edge is not in the network, it should not appear in this datase (and hence, cannot take any flows).

```{code-cell} ipython3
arc_data = pd.DataFrame([
    {"from": 0, "to": 1, "capacity": 16, "cost": 1},
    {"from": 0, "to": 2, "capacity": 13, "cost": 2},
    {"from": 1, "to": 2, "capacity": 10, "cost": 1},
    {"from": 2, "to": 1, "capacity": 4, "cost": 3},
    {"from": 1, "to": 3, "capacity": 12, "cost": 1},
    {"from": 3, "to": 2, "capacity": 9, "cost": 2},
    {"from": 2, "to": 4, "capacity": 14, "cost": 3},
    {"from": 4, "to": 3, "capacity": 7, "cost": 1},
    {"from": 3, "to": 5, "capacity": 20, "cost": 2},
    {"from": 4, "to": 5, "capacity": 4, "cost": 1},
]).set_index(["from", "to"])

arc_data
```

We need to also store the supply/demand requirements for each node. Here, we store this data in a dataframe, indexed by node, with a single demand column. A negative demand entry indicates a supply node, positive a demand. Transshipment nodes do not appear in this frame (implicitly supply, & demand are zero).

```{code-cell} ipython3
demand_data = pd.DataFrame([
    {"node": 0, "demand": -23},
    {"node": 5, "demand": 23}
]).set_index("node")
demand_data
```

Add flow variables using the same approach as before (one per arc in the dataframe):

```{code-cell} ipython3
model = gp.Model("supply-demand")
model.ModelSense = GRB.MINIMIZE

arc_df = arc_data.gppd.add_vars(model, name="flow", ub="capacity", obj="cost")
arc_df
```

```{code-cell} ipython3
model.getObjective()
```

Construction of flow balance is similar to the max-flow example, but we also need to include the supply/demand data.

One important note is that since various nodes are missing either inflow, outflow, or demand based on the network structure, there will be missing values in this dataframe. `gurobipy-pandas` explicitly disallows this, so we need to fill in the data.

Based on the way we structured the data initially: a missing entry in the demand column indicates a transhipment node (zero supply or demand). Similarly, if a node has no inflow edge, or no outflow edge, we can safely say it's total inflow or outflow, respectively, are zero. So applying `.fillna(0)` to this dataframe gives us the correct model.

```{code-cell} ipython3
pd.DataFrame({
    "inflow": arc_df["flow"].groupby("to").sum(),
    "outflow": arc_df["flow"].groupby("from").sum(),
    "demand": demand_data["demand"],
})
```

Applying `fillna`, then using method chaining to construct constraints, we get the following result:

```{code-cell} ipython3
balance_df = (
    pd.DataFrame({
        "inflow": arc_df["flow"].groupby("to").sum(),
        "outflow": arc_df["flow"].groupby("from").sum(),
        "demand": demand_data["demand"],
    })
    .fillna(0)   # zero fill (some nodes have no in, out, or demand)
    .gppd.add_constrs(model, "inflow - outflow == demand", name="balance")
)
balance_df
```

We can again inspect the constraints they were built to confirm:

```{code-cell} ipython3
balance_df['balance'].apply(model.getRow)
```

```{code-cell} ipython3
balance_df['balance'].gppd.RHS
```

Solve the model, and append the results as a column in the flows dataframe. We can easily inspect this to see that capacities are respected:

```{code-cell} ipython3
model.optimize()
arc_df.assign(result=lambda df: df['flow'].gppd.X)
```
