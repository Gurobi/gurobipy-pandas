---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
---

# The Stigler Diet Problem

```{code-cell}
import pandas as pd
import gurobipy as gp
import gurobipy_pandas as gppd
from gurobipy import GRB

gppd.set_interactive()
```

```{code-cell}
foods = pd.read_excel("data/diet.xlsx", sheet_name="Foods")
foods.head()
```

```{code-cell}
categories = pd.read_excel("data/diet.xlsx", sheet_name="Categories")
categories.head()
```

```{code-cell}
nutrition = pd.melt(
    pd.read_excel("data/diet.xlsx", sheet_name="Nutrition"),
    id_vars=["food"],
    var_name="nutrient",
)
nutrition.head()
```

```{code-cell}
env = gp.Env()
model = gp.Model(env=env)
```

```{code-cell}
buy = gppd.add_vars(model, foods.set_index("food"), name="buy")
buy.head()
```

```{code-cell}
amounts = (
    nutrition.join(buy, on="food")
    .set_index(["food", "nutrient"])
    .pipe(lambda df: df["value"] * df["buy"])
    .groupby("nutrient").sum()
)

limits = categories.set_index("category")

gppd.add_constrs(
    model,
    amounts,
    GRB.GREATER_EQUAL,
    limits["minimum"],
)

gppd.add_constrs(
    model,
    amounts,
    GRB.LESS_EQUAL,
    limits["maximum"],
)
```

```{code-cell}
model.setObjective((buy * foods.set_index("food")["cost"]).sum())
```

```{code-cell}
model.optimize()
```

```{code-cell}
buy.gppd.X.pipe(lambda s: s[s >0])
```
