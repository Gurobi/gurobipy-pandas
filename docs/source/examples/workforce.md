---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
---

# Workforce Scheduling

This example implements a simple workforce scheduling model: assigning workers to shifts in order to maximize a total preference score.

```{code-cell}
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import gurobipy_pandas as gppd

pd.options.display.max_rows = 8
gppd.set_interactive()
```

```{code-cell}
:nbsphinx: hidden

# Hidden cell to avoid licensing messages
# when docs are generated.
with gp.Model():
    pass
```

First read in preference data. The preference data contains 3 columns: a shift date, worker name, and a preference value. If a worker is not available for a given shift, then that work-shift combination does not appear in the data (i.e. only preferenced shifts are valid).

```{code-cell}
preferences = pd.read_csv(
    "data/preferences.csv",
    parse_dates=["Shift"],
    index_col=['Worker', 'Shift']
)
preferences
```

Unstacking the data, we can see that the dataset is sparse: not all worker-shift combinations are possible. When constructing the model, we should take care that decision variables are only created for the valid combinations.

```{code-cell}
preferences.unstack(0).head()
```

Next load the shift requirements data, which indicates the number of required workers for each shift.

```{code-cell}
shift_requirements = pd.read_csv(
    "data/shift_requirements.csv",
    parse_dates=["Shift"],
    index_col="Shift"
)
shift_requirements
```

## Model Formulation

Our goal is to fill all available shifts with the required number of workers, while maximising the sum of preference values over all assignments. To do this, will create a binary variable for each valid worker-shift pairing (1 = shift assigned) and use preference values as linear coefficients in the objective.

There are three pandas indices involved in creating this model: workers, shifts, and preference pairings. While variables are added for the preference pairings, we will see that the worker and shift indexes emerge when aggregating.

```{code-cell}
m = gp.Model()
df = (
    preferences
    .gppd.add_vars(
        m, name="assign", vtype=GRB.BINARY, obj="Preference",
        index_formatter={"Shift": lambda index: index.strftime('%a%d')},
    )
)
df
```

By grouping variables across the shift indices, we can efficiently construct the shift requirement constraints.

```{code-cell}
shift_cover = gppd.add_constrs(
    m,
    df['assign'].groupby('Shift').sum(),
    GRB.EQUAL,
    shift_requirements["Required"],
    name="shift_cover",
    index_formatter={"Shift": lambda index: index.strftime('%a%d')},
)
shift_cover
```

## Extracting Solutions

With the model formulated, we solve it using the Gurobi Optimizer:

```{code-cell}
m.optimize()
```

Extract the solution using the series accessor `.gppd.X`:

```{code-cell}
solution = df['assign'].gppd.X
solution
```

Since the result is returned as a pandas series, we can easily filter down to the selected assignments:

```{code-cell}
assigned_shifts = solution.reset_index().query("assign == 1")
assigned_shifts
```

Additionally, we can unstack the result and transform it to produce a roster table:

```{code-cell}
shift_table = solution.unstack(0).fillna("-").replace({0.0: "-", 1.0: "Y"})
pd.options.display.max_rows = 15
shift_table
```

```{code-cell}
:nbsphinx: hidden

# Tests
assert isinstance(solution, pd.Series)
assert isinstance(assigned_shifts, pd.DataFrame)
assert isinstance(shift_table, pd.DataFrame)
assigned = len(assigned_shifts)
free = shift_table.shape[0] * shift_table.shape[1] - assigned
assert shift_table.stack().value_counts().to_dict() == {'Y': assigned, '-': free}
assert m.ObjVal == 96.0
```
