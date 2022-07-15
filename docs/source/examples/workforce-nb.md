---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.0
kernelspec:
  display_name: gurobipy-pandas
  language: python
  name: gurobipy-pandas
---

# Workforce Scheduling

Assigning shifts to maximize worker happiness!!

Basic code done, need to document the mathematical model in mathjax alongside (index corresponds directly to sets, column corresponds directly to data defined over that set).

```{code-cell} ipython3
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import gurobipy_pandas

pd.options.display.max_rows = 8
```

Read in the data. Preference data contains 3 columns: shift date, worker, and preference value. If a worker is not available for a given shift, then that work-shift combination does not appear in the table.

```{code-cell} ipython3
preferences = pd.read_feather("data/preferences.feather")
preferences
```

Shift requirements data indicates the number of required workers for each shift.

```{code-cell} ipython3
shift_requirements = (
    pd.read_feather("data/shift_requirements.feather")
    .set_index("Shift")
)
shift_requirements
```

Our goal is to fill all available shifts with the required number of workers, while maximising the total preference values of assignments. To do this, we'll create a binary variable for each worker (1 = shift assigned) and use preferences as the objective.

Semantics: worker and shift are index sets in the model, we should put these in the index of the dataframe.

Note: binary vars can be relaxed without issue in this model, but we should keep them binary so that the modelling is clear to newbies.

Note: in the gurobipy-pandas API, we only use Model() and Env() calls from gurobipy

```{code-cell} ipython3
m = gp.Model()
df = (
    preferences
    .set_index(["Worker", "Shift"])
    .grb.pdAddVars(m, name="assign", vtype=GRB.BINARY, obj="Preference")
)
m.update()
df
```

By grouping variables across one of our indices, we can efficiently construct the shift requirement constraints. This involves a few transform steps.

Todo: explain each column, constraint w.r.t mathematical model

Fixme: .update() calls just to show naming are annoying to have to include... need to think about how to include (to show naming effect) while indicating to users that they should not update() during formulation in general. Perhaps we could include that as an `interactive` flag in gurobipy_pandas?

Also would be useful to format dates cleanly. Must remove spacing, maybe remove time if date is the only distinction.

```{code-cell} ipython3
shift_cover = (
    df.groupby('Shift')[['assign']].sum()
    .join(shift_requirements)
    .grb.pdAddConstrs(m, "assign == Required", name="shift_cover")
)
m.update()
shift_cover
```

```{code-cell} ipython3
m.optimize()
```

```{code-cell} ipython3
solution = df['assign'].grb.X
solution
```

```{code-cell} ipython3
assigned_shifts = solution.reset_index().query("assign == 1")
assigned_shifts
```

```{code-cell} ipython3
pd.options.display.max_rows = 15
solution.unstack(0).fillna("-").replace({0.0: "-", 1.0: "Y"})
```
