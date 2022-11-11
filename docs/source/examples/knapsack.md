---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
kernelspec:
  display_name: gurobipy-pandas
  language: python
  name: gurobipy-pandas
---

# Knapsack Problem

+++

Implementing mathematical programming models in code requires transforming a dataset into a model. Pandas excels at storing and manipulating data, but it is not always clear how best to transform data to help interact with the modelling features of gurobipy in order to build a concrete model. This linking package aims to define a convenient API for doing so.

Consider a classical model such as the Multiple Knapsack Problem, which aims to assign items to one of several knapsacks, respecting their capacities, so that the total value of carried items is maximized. The model is defined as:

$$
\begin{alignat}{2}
\min \quad        & \sum_{i \in I} \sum_{k \in K} p_{i} x_{ik} \\
\mbox{s.t.} \quad & \sum_{i \in I} w_{i} x_{ik} \le W_{k} & \forall k \in K \\
                  & \sum_{k \in K} x_{ik} \le 1 & \forall i \in I \\\
                  & x_{ik} \in \lbrace 0, 1 \rbrace & \forall i \in I, k \in K. \\
\end{alignat}
$$

Defined this way, we can see that the model is defined based on its indices $i$ (items) and $k$ (knapsacks). The model data is defined using these indices: item weights $w_i$, item values $p_j$, and knapsack capacities $W_k$. This data must be associated with variables $x_{ij}$ (defined over the same indices) in order to build concrete instantiations of the constraints and objective in the model.

This model has a slight twist: not all items can go in all knapsacks. Knapsacks have a weight capacity, but also a dimension. This means we are considering a sparse model here, and best practice is to use pandas' filtering mechanisms to reduce the model size, rather than adding redundant variables.

+++

Imports you'll need for all `gurobipy_pandas` applications:

```{code-cell} ipython3
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import gurobipy_pandas as gppd

gppd.set_interactive()
```

Pandas conveniently stores data in relation to indexes, so we would naturally define the data for items in a single DataFrame (with columns for weights and profits).

```{code-cell} ipython3
items = pd.DataFrame(
    index=pd.Index([1, 2, 3, 4, 5], name="item"),
    data={
        "weight": [1.0, 1.5, 1.2, 0.9, 0.7],
        "value": [0.5, 1.2, 0.3, 0.7, 0.9],
        "size": [1, 1, 1, 2, 1],
    },
)
items
```

Data for knapsacks also goes in a dataframe:

```{code-cell} ipython3
knapsacks = pd.DataFrame(
    index=pd.Index([1, 2], name="knapsack"),
    data={
        "capacity": [2.0, 1.5],
        "size": [1, 2],
    }
)
knapsacks
```

We *could* create a variable in the model for every index pair. But this would be quite wasteful. We should instead exploit the natural sparsity of the problem by filtering on the *data* to find only the variables we need.

```{code-cell} ipython3
assignable_pairs = (
    pd.merge(
        items.reset_index(),
        knapsacks.reset_index(),
        how='cross',
        suffixes=["_item", "_knapsack"],
    )
    .query("size_item <= size_knapsack")
    .set_index(["item", "knapsack"])
    .drop(columns=["size_item", "size_knapsack"])
)
assignable_pairs
```

From the above dataframe, `gurobipy_pandas` provides an accessor to create a corresponding series of variables. We first create a gurobipy Model, then call `.gppd.add_vars` on our new dataframe to create a Gurobi variable for every entry in the index. The result is a Pandas dataframe containing Gurobi variables. Note the objective coefficients can be set directly on the variables as they are created, using the aligned item value data.

```{code-cell} ipython3
model = gp.Model()
model.ModelSense = GRB.MAXIMIZE
x = gppd.add_vars(model, assignable_pairs, vtype=GRB.BINARY, obj="value", name="x")
x
```

Check the constructed objective function:

```{code-cell} ipython3
model.getObjective()
```

Finally, we can build the capacity constraints by using the "knapsack" index to group variables along with their weights:

```{code-cell} ipython3
total_weight = (
    (items['weight'] * x)
    .groupby("knapsack").sum()
)
total_weight
```

and use the function `gppd.add_constrs` to create constraints by aligning these expressions with capacity data:

```{code-cell} ipython3
capconstr = gppd.add_constrs(
    model, total_weight, GRB.LESS_EQUAL, knapsacks["capacity"],
    name='capconstr',
)
capconstr
```

We also need constraints that each item only appears in one knapsack. This can be done using the same function:

```{code-cell} ipython3
gppd.add_constrs(
    model, x.groupby('item').sum(),
    GRB.LESS_EQUAL, 1.0, name="pack_once",
)
```

```{code-cell} ipython3
model.optimize()
```

Finally, we use the series accessor `.gppd.X` to retrieve solution values. Using Pandas functions we can transform the result into a more readable form. Below shows that items 1 and 5 are packed into knapsack 1, while only item 2 is packed into knapsack 2.

```{code-cell} ipython3
x.gppd.X
```

```{code-cell} ipython3
(
    x.gppd.X.to_frame()
    .query("x >= 0.9").reset_index()
    .groupby("knapsack").agg({"item": list})
)
```

We can also use the series accessor `.gppd.Slack` on constraint series to determine constraint slacks. For example, the following shows spare capacity in each knapsack based on the capacity constraint.

```{code-cell} ipython3
capconstr.gppd.Slack
```
