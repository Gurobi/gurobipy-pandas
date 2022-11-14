---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
---

# Network flow modelling examples

```{code-cell}
import numpy as np
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import gurobipy_pandas as gppd
```

## Min-cost flow network for max-flow computation

```{code-cell}
arc_data = pd.DataFrame([
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
    {"from": 5, "to": 0, "capacity": np.inf, "cost": -1},
]).set_index(["from", "to"])

arc_data
```

```{code-cell}
model = gp.Model("max-flow")
model.ModelSense = GRB.MINIMIZE

arc_df = arc_data.gppd.add_vars(
    model, ub="capacity", obj="cost", name="flow"
)
model.update()
arc_df
```

```{code-cell}
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

```{code-cell}
model.optimize()
```

```{code-cell}
arc_df["flow"].gppd.X
```

```{code-cell}
(
    constrs
    .assign(
        inflow_result=lambda df: df['inflow'].apply(gp.LinExpr).gppd.get_value(),
        outflow_result=lambda df: df['outflow'].apply(gp.LinExpr).gppd.get_value(),
    )
)
```

## Transshipment / sources / sinks

```{code-cell}
arc_data = pd.DataFrame([
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
]).set_index(["from", "to"])

arc_data
```

```{code-cell}
demand_data = pd.DataFrame([
    {"node": 0, "demand": -23},
    {"node": 5, "demand": 23}
]).set_index("node")
demand_data
```

```{code-cell}
model = gp.Model("supply-demand")
model.ModelSense = GRB.MINIMIZE

arc_df = arc_data.gppd.add_vars(model, name="flow", ub="capacity", obj="cost")
model.update()
arc_df
```

```{code-cell}
balance_df = (
    pd.DataFrame({
        "inflow": arc_df["flow"].groupby("to").sum(),
        "outflow": arc_df["flow"].groupby("from").sum(),
        "demand": demand_data["demand"],
    })
    .fillna(0)   # zero fill (some nodes have no in, out, or demand)
    .gppd.add_constrs(model, "inflow - outflow == demand", name="balance")
)
model.update()

# Code is readable, and you still get the full method-chained
# dataframe to help check you formulated things correctly.
balance_df
```

```{code-cell}
# With the dataframe, but without the accessors?

# tmp_df = (       # Already yuck, throwaway object
#     pd.DataFrame({
#         "inflow": arc_df["flow"].groupby("to").sum(),
#         "outflow": arc_df["flow"].groupby("from").sum(),
#         "demand": demand_data["demand"],
#     })
#     .fillna(0)   # zero fill (some nodes have no in, out, or demand)
# )

# gppd.add_constrs(model, tmp_df, "inflow - outflow == demand")

# gppd.add_constrs(
#     model,
#     tmp_df["inflow"] - tmp_df["outflow"],
#     GRB.EQUAL,
#     tmp_df["demand"],
# )
```

```{code-cell}
# The alternative feels artificial, I don't really need
# the node set anywhere. And to build it automatically
# I need to do lots of unions...
# The accessors feel cleaner here, I don't have to separately
# track a node set and keep that in sync with other data.

# from itertools import chain

# # Maybe it's good to force the user to do this?
# nodes = set(chain(
#     arc_df.index.get_level_values("from").unique(),
#     arc_df.index.get_level_values("to").unique(),
#     demand_data.index.unique(),
# ))

# # But then we'll just wind up doing reindex in three places
# # instead of fill in one.
# inflow = arc_df["flow"].groupby("to").sum().reindex(nodes).fillna(0)
# outflow = arc_df["flow"].groupby("from").sum().reindex(nodes).fillna(0)
# demand = demand_data["demand"].reindex(nodes).fillna(0)

# # This was a long way round to get here.
# gppd.pd_add_constrs(
#     model,
#     inflow - outflow,
#     GRB.EQUAL,
#     demand,
# )
```

```{code-cell}
model.optimize()
```

```{code-cell}
# Check flows against bounds
arc_df.assign(result=lambda df: df['flow'].gppd.X)
```

```{code-cell}
# balance_df has the constraint expression components alongside
# the dataframe, so we can sense check results or gather other stats

# TODO: clearly with sparse indices we are going to get a lot of
# mixed types (gurobi types and constants). The get_value accessor
# should handle this gracefully.

(
    balance_df
    .assign(
        inflow_result=lambda df: df['inflow'].apply(gp.LinExpr).gppd.get_value(),
        outflow_result=lambda df: df['outflow'].apply(gp.LinExpr).gppd.get_value(),
    )
)
```
