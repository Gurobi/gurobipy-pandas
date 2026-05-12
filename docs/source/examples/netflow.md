---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
---

# Multicommodity Flow

**Author**: Irv Lustig, Optimization Principal, Princeton Consultants

Solve a multi-commodity flow problem.  There are multiple products, which can be
produced in multiple locations, and have to be shipped over a network to other locations.
Each location may have supply and/or demand for any product.  The network may have
transhipment locations where freight is interchanged. For each arc in the network, there is
a limited capacity of the total products that can be carried.  Each arc also has a product-specific
cost for shipping one unit of the product on that arc.

This example is based on `netflow.py` that is supplied by Gurobi.

+++

#### Import necessary libraries

- `IPython.display` is used to improve the display of `pandas` `Series` by converting them to `DataFrame` for output
- `openpxyl` is required to read `xlsx` data files

```{code-cell}
---
slideshow:
  slide_type: slide
---
from IPython.display import display
import pandas as pd
import gurobipy as gp
import gurobipy_pandas as gppd
```

#### Get the file from a prompt

```{code-cell}
filename = "data/mcfdata.v1.xlsx"
```

#### Read Data using `pandas`

Read in the data from an Excel file. Converts the data into a dictionary of `pandas` `Series`, with the assumption that the last column is the data column.

```{code-cell}
---
slideshow:
  slide_type: slide
---
raw_data = pd.read_excel(filename, sheet_name=None)
data = {
    k: df.set_index(df.columns[:-1].to_list())[df.columns[-1]]
    for k, df in raw_data.items()
}
for k, v in data.items():
    print(k)
    display(v.to_frame())
```

## Data Model

### Sets

| Notation | Meaning |  Table Locations |
| ---- | --------------------------- |  ----------- |
| $\mathcal N$ | Set of network nodes | `cost`: Columns `From`, `To` <br>  `capacity`: Columns `From`, `To` <br> `supply`: Column `Node` <br> `demand`: Column `Node` |
| $\mathcal P$ | Set of products (commodities) | `cost`: Column `Product` <br> `supply`: Column `Product` <br> `demand`: Column `Product` |
|$\mathcal A$ | Set of arcs $(n_f,n_t)$, $n_f,n_t\in\mathcal A$ | `cost`: Columns `From`, `To` |
| $\mathcal P_a$ | Set of products $p\in\mathcal P$ that can be carried on arc $a\in\mathcal A$ | `cost`: Columns `Product`, `From`, `To` |
| $\mathcal A_p$ | Set of arcs $a\in\mathcal A$ that can carry product $p\in\mathcal P$ | `cost`: Columns `Product`, `From`, `To` |



### Numerical Input Values

The input data is converted to pandas `Series`, so the name of each `Series` is also the name of the value.

| Notation | Meaning |  Table Name/Value Column | Index Columns
| ---- | --------------------------- |  ------ | ---------- |
| $\kappa_a$ | Capacity of arc $a\in\mathcal A$ | `capacity` |  `From`, `To` |
| $\pi_{ap}$ | Cost of carrying product $p$ on arc $a\in\mathcal A$, $p\in\mathcal P_a$,  | `cost` | `Product`, `From`, `To` |
| $\sigma_{pn}$ | Supply of product $p\in\mathcal P$ at node $n\in\mathcal N$. Defaults to 0 | `supply` | `Node` |
| $\delta_{pn}$ | Demand of product $p\in\mathcal P$ at node $n\in\mathcal N$. Defaults to 0 | `demand` | `Node` |

+++

### Compute Sets

- The set $\mathcal P$ of products can appear in any of the tables `supply`, `demand` and `cost` .
- The set $\mathcal N$ of nodes can appear in  any of the tables `capacity`, `supply`, `demand` and `cost`

```{code-cell}
commodities = set(
    pd.concat(
        [
            data[dfname].index.to_frame()["Product"]
            for dfname in ["supply", "demand", "cost"]
        ]
    ).unique()
)
commodities
```

```{code-cell}
nodes = set(
    pd.concat(
        [
            data[dfname].index.to_frame()[fromto].rename("Node")
            for dfname in ["capacity", "cost"]
            for fromto in ["From", "To"]
        ]
        + [data[dfname].index.to_frame()["Node"] for dfname in ["supply", "demand"]]
    ).unique()
)

nodes
```

### Compute the Net Flow for each node

The net flow $\mu_{pn}$ for each product $p\in\mathcal P$ and node $n\in\mathcal N$ is the sum of the supply less the demand.  For transshipment nodes, this value is 0.  This is called `inflow` in the code.

```{code-cell}
inflow = pd.concat(
    [
        data["supply"].rename("net"),
        data["demand"].rename("net") * -1,
        pd.Series(
            0,
            index=pd.MultiIndex.from_product(
                [commodities, nodes], names=["Product", "Node"]
            ),
            name="net",
        ),
    ]
).groupby(["Product", "Node"]).sum()
inflow
```

## Create the Gurobi Model

```{code-cell}
m = gp.Model("netflow")
```

## Model

### Decision Variables

The model will have one set of decision variables:
- $X_{pa}$ for $p\in\mathcal P$, $a\in\mathcal A_p$ represents the amount shipped of product $p$ on arc $a$.  We will call this variable `flow` in the code.

The cost of shipment is $\pi_{ap}$.

This defines the objective function:
$$
\text{minimize}\quad\sum_{a\in\mathcal A}\sum_{p\in\mathcal P_a} \pi_{ap}X_{pa}
$$

```{code-cell}
flow = gppd.add_vars(m, data["cost"], obj=data["cost"], name="flow")
m.update()
flow
```

### Constraints

#### Flow on each arc is capacitated

$$
\sum_{p\in\mathcal P_a} X_{pa} \le \kappa_a\qquad\forall a\in\mathcal A
$$

```{code-cell}
capct = pd.concat(
    [flow.groupby(["From", "To"]).agg(gp.quicksum), data["capacity"]], axis=1
).gppd.add_constrs(m, "flow <= capacity", name="cap")
m.update()
capct
```

#### Conservation of Flow

For each node and each product, the flow out of the node, less the flow into the node is equal to the net flow.

$$
\sum_{(n, n_t)\in A_p} X_{p(n,n_t)} - \sum_{(n_f, n)} X_{p(n_f,n)} = \mu_{pn}\qquad\forall p\in\mathcal P, n\in\mathcal N
$$

```{code-cell}
flowct = pd.concat(
    [
        flow.rename_axis(index={"From": "Node"})
        .groupby(["Product", "Node"])
        .agg(gp.quicksum)
        .rename("flowout"),
        flow.rename_axis(index={"To": "Node"})
        .groupby(["Product", "Node"])
        .agg(gp.quicksum)
        .rename("flowin"),
        inflow,
    ],
    axis=1,
).fillna(0).gppd.add_constrs(m, "flowout - flowin == net", name="node")
m.update()
flowct
```

## Optimize!

```{code-cell}
m.optimize()
```

## Get the Solution

Only print out arcs with flow, using pandas

```{code-cell}
soln = flow.gppd.X
soln.to_frame().query("flow > 0").sort_index()
```
