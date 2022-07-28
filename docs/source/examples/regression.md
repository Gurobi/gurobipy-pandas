---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.0
---

# L1 Norm Regression

```{code-cell}
import gurobipy as gp
from gurobipy import GRB
import gurobipy_pandas
import pandas as pd

from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import add_dummy_feature
```

Load diabetes regression dataset and spit in the usual way. Add a column for the intercept.

```{code-cell}
diabetes_X, diabetes_y = datasets.load_diabetes(return_X_y=True, as_frame=True)
diabetes_X["intercept"] = 1.0
X_train, X_test, y_train, y_test = train_test_split(diabetes_X, diabetes_y, random_state=42)
X_train
```

Create model.

```{code-cell}
model = gp.Model()
```

Create unbounded variables for each column coefficient. Use the index accessor; in pandas the columns are also an index, so `.grb.pd_add_vars` associates a Gurobi variable with each column index entry.

```{code-cell}
intercept = model.addVar(lb=-GRB.INFINITY)

coeffs = X_train.columns.grb.pd_add_vars(model, name="coeff", lb=-GRB.INFINITY)
model.update()
coeffs
```

Formulate the linear relationships representing the regression formula.

```{code-cell}
relation = (X_train * coeffs).sum(axis="columns").to_frame(name="MX")
relation
```

Add non-negative deviation variables for each data point to measure total error. Construct linear constraint to represent the regression relationship.

```{code-cell}
fit = (
    relation.grb.pd_add_vars(model, name="U")
    .grb.pd_add_vars(model, name="V")
    .join(y_train)
    .grb.pd_add_constrs(model, "target == MX + U - V", name="fit")
)
model.update()
fit
```

Formulate L1 norm regression objective (minimize absolute error).

```{code-cell}
abs_error = fit["U"] + fit["V"]
mean_abs_error = abs_error.sum() / fit.shape[0]
model.setObjective(mean_abs_error, sense=GRB.MINIMIZE)
```

Solve!

```{code-cell}
model.optimize()
```

Check coefficients.

```{code-cell}
coeffs.grb.X
```

Plot distribution of errors.

```{code-cell}
abs_error.grb.get_value().plot.hist();
```

```{code-cell}
:nbsphinx: hidden

assert model.ObjVal <= 44
assert isinstance(coeffs.grb.X, pd.Series)
```
