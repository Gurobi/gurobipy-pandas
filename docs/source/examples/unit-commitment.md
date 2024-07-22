---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
---

# Unit Commitment

```{code-cell}
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import gurobipy_pandas as gppd

import matplotlib.pyplot as plt
import seaborn as sns

sns.set_palette(sns.color_palette("deep"))
gppd.set_interactive()
```

```{code-cell}
########
# Data schema
#
# Each generator has properties which remain fixed over all time periods
#
# - num_available: number of available generating units
# - min_output: minimum generation in MWh for each active generator
# - max_output: maximum generation in MWh for each active generator
# - cost_per_hour: $ cost per hour per active generator
# - marginal cost: cost in $/MWh for generation above min_output
# - startup_cost: fixed cost incurred for starting a generator in an interval
# - state0: number of generators active before the first period
#
# Each time period has the following data
#
# - expected_demand: predicted MWh demand, which the solution will meet exactly
# - minimum_capacity: value in MWh above the predicted demand; the total online
#                     generation capacity must exceed this value
#
########

generator_data = pd.read_csv("data/generators.csv", index_col=0)
time_period_data = pd.read_csv("data/time_periods.csv", parse_dates=["time_period"], index_col=0)
```

```{code-cell}
generator_data
```

```{code-cell}
time_period_data
```

```{code-cell}
# Set up variables based on the data schema
#
# For each generator type, we have three classes of variables:
#
# - The total output of all generators in the class in the given time
#   period (continuous)
# - The number of active generators of the class in the given time period
#   (integer, upper bounded by number of available generators)
# - The number of active generators of the class which start up in the
#   given time period (integer)
#
# One variable is required for every generator class and time period

env = gp.Env()
model = gp.Model(env=env)

# Method chain our way to creating these variable sets.
# We need to create a dense index: generators x time periods.

index_formatter = {"time_period": lambda index: index.strftime("%H%M")}
generators = (
    pd.DataFrame(
        index=pd.MultiIndex.from_product([generator_data.index, time_period_data.index])
    )
    .join(generator_data)
    .gppd.add_vars(model, name="output", index_formatter=index_formatter)
    .gppd.add_vars(
        model,
        vtype=GRB.INTEGER,
        ub="num_available",
        name="num_active",
        index_formatter=index_formatter,
    )
    .gppd.add_vars(
        model, vtype=GRB.INTEGER, name="num_startup", index_formatter=index_formatter
    )
)
```

```{code-cell}
# Just show a subset of the time-expanded dataframe
(
    generators[["output", "num_active", "num_startup", "cost_per_hour", "startup_cost", "min_output", "max_output"]]
    .assign(
        output=lambda df: df["output"].gppd.VarName,
        num_active=lambda df: df["num_active"].gppd.VarName,
        num_startup=lambda df: df["num_startup"].gppd.VarName,
    )
)
```

```{code-cell}
# Constrain that predicted demand is exactly satisfied
demand_constraint = gppd.add_constrs(
    model,
    generators.groupby("time_period")["output"].sum(),
    GRB.EQUAL,
    time_period_data["expected_demand"],
)
```

```{code-cell}
df = (
    generators
    .gppd.add_constrs(
        model,
        "output >= min_output * num_active",
        name="lower_limit",
        index_formatter=index_formatter
    )
    .gppd.add_constrs(
        model,
        "output <= max_output * num_active",
        name="constr_max_output",
        index_formatter=index_formatter
    )
)

(
    df[["output", "num_active", "min_output", "max_output", "lower_limit"]]
    .assign(
        output=lambda df: df["output"].gppd.VarName,
        num_active=lambda df: df["num_active"].gppd.VarName,
        lower_limit=lambda df: df["lower_limit"].gppd.ConstrName,
    )
)
```

```{code-cell}
# Alternative: Constrain that generators are producing between their minimum and maximum
# min_output_constraint = gppd.add_constrs(
#     model,
#     generators["output"],
#     GRB.GREATER_EQUAL,
#     generators["min_output"] * generators["num_active"],
#     name="min_output",
# )
# max_output_constraint = gppd.add_constrs(
#     model,
#     generators["output"],
#     GRB.LESS_EQUAL,
#     generators["max_output"] * generators["num_active"],
#     name="max_output",
# )
```

```{code-cell}
# Constrain that the active generators during each time
# period are capable of meeting the reserve demand.
active_capacity = (
    (generators["max_output"] * generators["num_active"])
    .groupby("time_period").sum()
)
active_capacity_constraint = gppd.add_constrs(
    model,
    active_capacity,
    GRB.GREATER_EQUAL,
    time_period_data["minimum_active_capacity"],
)
```

```{code-cell}
active_capacity.to_frame()
```

```{code-cell}
(
    generators[["num_active", "num_startup"]]
    .assign(
        num_active=lambda df: df["num_active"].gppd.VarName,
        num_startup=lambda df: df["num_startup"].gppd.VarName,
    )
)
```

```{code-cell}
# Constrain the relationship between active generators and startups.

def startup_constraints(group):
    group = group.sort_index()
    return gppd.add_constrs(
        model,
        group["num_startup"].iloc[1:],
        GRB.GREATER_EQUAL,
        (group["num_active"] - group["num_active"].shift(1)).dropna(),
        name="startup",
    ).to_frame()

startup = generators.groupby("generator_class").apply(startup_constraints).droplevel(0)

time_period_1 = generators.sort_index().groupby("generator_class").first()
initial_startup = gppd.add_constrs(
    model,
    time_period_1["num_startup"],
    GRB.GREATER_EQUAL,
    time_period_1["num_active"] - generator_data["state0"],
    name="initial_startup",
)
```

```{code-cell}
c = startup.iloc[2].item()
print(model.getRow(c), c.sense + '=', c.rhs)
```

```{code-cell}
# Minimize total cost objective
model.setObjective(
    (
        # Fixed hourly costs for started generators
        generators["cost_per_hour"] * generators["num_active"]
        # Marginal hourly cost of additional generation above the minimum
        + generators["marginal_cost"]
        * (generators["output"] - generators["num_active"] * generators["min_output"])
        # Startup costs for newly active generators in each time period
        + generators["startup_cost"] * generators["num_startup"]
    ).sum(),
    sense=GRB.MINIMIZE
)
```

```{code-cell}
# Do the magic
model.write("unit-commitment.lp")
model.optimize()
```

```{code-cell}
pd.DataFrame(
    dict(
        num_active=generators["num_active"].gppd.X,
        num_startup=generators["num_startup"].gppd.X,
    )
)
```

```{code-cell}
plt.figure(figsize=(8, 4))
pd.DataFrame(
    {
        "Demand": time_period_data["expected_demand"],
        "Min. Active Capacity": time_period_data["minimum_active_capacity"],
        "Active Capacity": active_capacity.gppd.get_value(),
        "Excess": (-active_capacity_constraint.gppd.Slack),
    }
).plot.line(ax=plt.gca());
```

```{code-cell}
#model.close()
#env.close()
```
