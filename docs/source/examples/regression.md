---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
---

# L1 Norm Regression

This example implements a regression model which minimizes mean absolute error as a fitting criteria. This metric cannot be handled by the typical Ordinary Least Squares (OLS) regression implementation, but is well suited to linear programming (and therefore, to Gurobi!).

L1 norm regressionaims to choose weights $w$ in order to minimize the following loss function:

$$
\min_w \lvert Xw - y \rvert
$$

To model the L1 regression loss function using linear programming, we need to introduce a number of auxiliary variables. Here $I$ is the set of data points and $J$ the set of fields. Response values $y_i$ are predicted from predictor values $x_{ij}$ by fitting coefficients $w_j$. To handle the absolute value, non-negative continuous variables $u_i$ and $v_i$ are introduced.

$$
\begin{alignat}{2}
\min \quad        & \sum_i u_i + v_i \\
\mbox{s.t.} \quad & \sum_j w_j x_{ij} + u_i - v_i = y_i \quad & \forall i \in I \\
                  & u_i, v_i \ge 0                     \quad & \forall i \in I \\
                  & w_j \,\, \text{free}               \quad & \forall j \in J \\
\end{alignat}
$$

+++

We start with the usual imports for `gurobipy-pandas` models. Additionally, we import some `sklearn` modules, both to load an example dataset and to help perform model validation.

```{code-cell}
import gurobipy as gp
from gurobipy import GRB
import gurobipy_pandas as gppd
import pandas as pd

from sklearn import datasets
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
```

```{code-cell}
:nbsphinx: hidden

# Hidden cell to avoid licensing messages
# when docs are generated.
with gp.Model():
    pass
```

We first load the diabetes regression dataset into pandas dataframes, then perform scaling and a train-test split. Additionally, we add a constant column to capture an intercept term.

```{code-cell}
diabetes_X, diabetes_y = datasets.load_diabetes(return_X_y=True, as_frame=True)
scaler = StandardScaler()
diabetes_X_scaled = pd.DataFrame(
    data=scaler.fit_transform(diabetes_X),
    columns=diabetes_X.columns,
    index=diabetes_X.index,
)
diabetes_X_scaled["const"] = 1.0
X_train, X_test, y_train, y_test = train_test_split(
    diabetes_X_scaled, diabetes_y, random_state=42
)
X_train
```

## Model Formulation

Create the Gurobi model:

```{code-cell}
model = gp.Model()
```

Then we create an unbounded variable for each column coefficient. Here we use the free function `gppd.add_vars` to create these variables. Note that what we want here is one variable per column, and in pandas, the column labels are also an index. So, we can pass this index directly to the `gurobipy-pandas` function to create a Series of variables aligned to this column index.

```{code-cell}
coeffs = gppd.add_vars(model, X_train.columns, name="coeff", lb=-GRB.INFINITY)
model.update()
coeffs
```

Given this column-oriented series and our training dataset, we can formulate the linear relationships representing the regression formula using native pandas operations:

```{code-cell}
relation = (X_train * coeffs).sum(axis="columns")
relation
```

To incorporate the absolute error component, we need to introduce the variables $u_i$ and $v_i$, and constrain them such that they measure the error for each data point. This can be done compactly using the `gppd` dataframe accessor and method chaining:

```{code-cell}
fit = (
    relation.to_frame(name="MX")
    .gppd.add_vars(model, name="u")
    .gppd.add_vars(model, name="v")
    .join(y_train)
    .gppd.add_constrs(model, "target == MX + u - v", name="fit")
)
model.update()
fit
```

Each step of the above code appends a new column to the returned dataframe:

1. Start with the column "MX", representing the $Xw$ term
2. Append a column of new variables $u_i$ (one for each data point)
3. Append a column of new variables $v_i$ (one for each data point)
4. Join the true target data from `y_train`
5. Add one constraint per row such that `u_i - v_i` measures the error between prediction and target

Now we are in a position to formulate the mean absolute error expression, and minimize it in the objective function:

```{code-cell}
abs_error = fit["u"] + fit["v"]
mean_abs_error = abs_error.sum() / fit.shape[0]
model.setObjective(mean_abs_error, sense=GRB.MINIMIZE)
```

## Extracting Solutions

With the model formulated, we solve it using the Gurobi Optimizer:

```{code-cell}
model.optimize()
```

Using the series accessor, we can extract the result coefficients as a series and display them on a plot:

```{code-cell}
coeffs.gppd.X.plot.bar()
```

We can also extract the distribution of errors from the `abs_error` series we constructed, and plot the results as a histogram:

```{code-cell}
# abs_error is a Series of linear expressions
abs_error.head()
```

```{code-cell}
# .gppd.get_value() evaluates these expressions at the current solution
abs_error.gppd.get_value().plot.hist();
```

```{code-cell}
:nbsphinx: hidden

assert model.ObjVal <= 44
assert isinstance(coeffs.gppd.X, pd.Series)
```
