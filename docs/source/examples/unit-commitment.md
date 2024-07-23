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

This examples covers Unit Commitment, a classical operations research problem that arises in the operation of electrical networks. In this problem, multiple power generation units with different characteristics are dispatched to meet expected electricity demand. A unit can be on or off, with a startup cost associated with transitioning from off to on, and power output that must lie in a specified range while the unit is on. The model is specified over discrete time periods, and decides which units to turn on, and when, in order to satisfy demand for each time period. The model also captures a reserve requirement, where the selected power plants must be capable of increasing their output, while still respecting their maximum output, in order to cope with the situation where actual demand exceeds predicted demand.

This model is based on example 15 from the fifth edition of Model Building in Mathematical Programming, by H. Paul Williams on pages 270-271 and 325-326, and is adapted from an existing Gurobi notebook [here](https://github.com/Gurobi/modeling-examples/tree/master/electrical_power_generation) which uses Python data structures to build the model.

```{code-cell}
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import gurobipy_pandas as gppd

gppd.set_interactive()
```

```{code-cell}
:nbsphinx: hidden

# Hidden cell to avoid licensing messages
# when docs are generated.
with gp.Model():
    pass
```

## Data Schema

Each generator has properties which remain fixed over all time periods:

- `num_available`: number of available generating units
- `min_output`: minimum generation in MWh for each active generator
- `max_output`: maximum generation in MWh for each active generator
- `cost_per_hour`: cost per hour per active generator
- `marginal cost`: cost per MWh for generation above min_output
- `startup_cost`: fixed cost incurred for starting a generator in an interval
- `state0`: number of generators active before the first period

Input data for the generators is stored in a DataFrame with the generator class name as the index.

```{code-cell}
# Load and check the generator data
generator_data = pd.read_csv(
    "data/generators.csv",
    index_col="generator_class",
)
generator_data
```

Each time period has the following data:

- `expected_demand`: predicted MWh demand, which the solution will meet exactly
- `minimum_capacity`: value in MWh above the predicted demand; the total online generation capacity must exceed this value

Input data for the time periods is stored in a DataFrame with the time periods as the index.

```{code-cell}
# Load and check the time period data
time_period_data = pd.read_csv(
    "data/time_periods.csv",
    parse_dates=["time_period"],
    index_col="time_period",
)
time_period_data
```

## Create the model

```{code-cell}
model = gp.Model()
```

## Add Time-Expanded Variables

The model has three variable types capturing the state of each generator class:

- `output`: The total output of all generators in the class in the given time period (continuous)
- `num_active`: The number of active generators of the class in the given time period (integer, upper bounded by number of available generators)
- `num_startup`: The number of active generators of the class which start up in the given time period (integer)

One variable of each type is needed for every generator class and time period. To create this 'time-expanded' formulation we need to take the product of the two indexes in our input data. This is done using pandas' [MultiIndex.from_product](https://pandas.pydata.org/docs/reference/api/pandas.MultiIndex.from_product.html) method.

Using this time-expanded index, we'll then use the DataFrame accessors from gurobipy-pandas to create our variables.

```{code-cell}
# Simplifies variable names
short_time = {"time_period": lambda index: index.strftime("%H%M")}

# Construct time-expanded index and add variables
generators = (
    # Create a new dataframe for the time-expanded index
    pd.DataFrame(
        index=pd.MultiIndex.from_product([generator_data.index, time_period_data.index])
    )
    .join(generator_data)
    # Create continuous variables (one per row) for generator output
    .gppd.add_vars(model, name="output", index_formatter=short_time)
    # Create integer variables for the number of active generators
    .gppd.add_vars(
        model,
        vtype=GRB.INTEGER,
        ub="num_available",  # Use num_available from the input data as a bound
        name="num_active",
        index_formatter=short_time,
    )
    # Create non-negative integer variables capturing generator startups
    .gppd.add_vars(
        model, vtype=GRB.INTEGER, name="num_startup", index_formatter=short_time
    )
)
```

The resulting `generators` DataFrame will be used to create constraints. Note that it contains both data columns and Gurobi variables as columns. This allows us to use standard pandas operations to build constraint expressions.

```{code-cell}
generators
```

## Demand Constraints

There are two types of demand constraints:

1. The total output of all generators in each time period must match the expected demand
2. The active generators in each time period must be able to meet the reserve demand

```{code-cell}
# Constrain that predicted demand is exactly satisfied
demand_constraint = gppd.add_constrs(
    model,
    generators.groupby("time_period")["output"].sum(),
    GRB.EQUAL,
    time_period_data["expected_demand"],
    index_formatter=short_time,
)
```

```{code-cell}
# Constrain that the active generators during each time
# period are capable of meeting the reserve demand.
active_capacity = (
    (generators["max_output"] * generators["num_active"])
    .groupby("time_period").sum()
).rename("active_capacity")
active_capacity_constraint = gppd.add_constrs(
    model,
    active_capacity,
    GRB.GREATER_EQUAL,
    time_period_data["minimum_active_capacity"],
    index_formatter=short_time,
)
```

Note that we keep total online capacity as a series of expressions. This way we can directly use it in analysis of the results.

```{code-cell}
active_capacity.to_frame()
```

## Output Constraints

Each generator class is constrained within it's operating limits.

```{code-cell}
df = (
    generators
    .gppd.add_constrs(
        model,
        "output >= min_output * num_active",
        name="lower_limit",
        index_formatter=short_time,
    )
    .gppd.add_constrs(
        model,
        "output <= max_output * num_active",
        name="constr_max_output",
        index_formatter=short_time,
    )
)
```

## Startup Constraints

The startup variables will be used to capture the cost associated with starting a generator during a time period. For this we need a rolling-window constraint such that startups capture the difference between the number of generators online in adjacent time periods.

```{code-cell}
# Constrain the relationship between active generators and startups.

def startup_constraints(group):
    group = group.sort_index()
    return gppd.add_constrs(
        model,
        group["num_startup"].iloc[1:],
        GRB.GREATER_EQUAL,
        group["num_active"].diff().dropna(),
        name="startup",
        index_formatter=short_time,
    )

startup = generators.groupby("generator_class").apply(startup_constraints).droplevel(0)
```

This groupby + diff operation creates constraints of this form (these can be inspected by writing the model to an LP file using `model.write("unit-commitment.lp")`):

```
startup[thermal1,0900]: num_active[thermal1,0800]
   - num_active[thermal1,0900] + num_startup[thermal1,0900] >= 0
```

i.e. the number of generators started at 9am, is at least as large as difference between the number of active generators at 9am and the number of active generators at 8am. `num_startup` is a non-negative integer, and it has a cost penalty associated with it in the objective function, so we can be sure it will capture the number of startups correctly.

```{code-cell}
# Separately capture the startups at time period 0.

time_period_1 = generators.sort_index().groupby("generator_class").first()
initial_startup = gppd.add_constrs(
    model,
    time_period_1["num_startup"],
    GRB.GREATER_EQUAL,
    time_period_1["num_active"] - generator_data["state0"],
    name="initial_startup",
    index_formatter=short_time,
)
```

## Objective Function

The total cost objective is now easy to compute:

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

## Solve the model

```{code-cell}
model.optimize()
```

## Extract results

Results are extracted using Series accessors. Note that after extracting the results, we can `close()` the model and proceed to analyse results using only pandas operations.

```{code-cell}
# Extract all variable values
solution = pd.DataFrame(
    dict(
        output=generators["output"].gppd.X,
        num_active=generators["num_active"].gppd.X,
        num_startup=generators["num_startup"].gppd.X,
    )
)

# Extract some additional results for comparison
results = pd.DataFrame(
    {
        "Demand": time_period_data["expected_demand"],
        "Min. Active Capacity": time_period_data["minimum_active_capacity"],
        "Active Capacity": active_capacity.gppd.get_value(),
        "Excess": (-active_capacity_constraint.gppd.Slack),
    }
)

# After extracting all results, close the model.
model.close()
```

## Analysis

Briefly; show the solution meeting the reserve demand and the excess capacity online.

```{code-cell}
%matplotlib inline
%config InlineBackend.figure_formats = ['svg']

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_palette(sns.color_palette("deep"))

plt.figure(figsize=(8, 4))
results.plot.line(ax=plt.gca())
plt.xlabel("Time")
plt.ylabel("MWh")
plt.ylim([0, 50000])
plt.legend(loc=2);
```
