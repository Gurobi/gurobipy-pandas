---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
---

# Project-Team Allocation

Consider the following decision problem: a number of teams are available to work on a collection of new projects in your organisation. Due to resourcing constraints, each team has a finite capacity, so not all projects will be completed. Furthermore, the teams are heterogeneous: not all teams are capable of completing all projects. Your task is to allocate projects to teams so that the total value of completed projects is maximised.

The mathematical model is defined based on two indices: the projects $i \in I$ and the teams $j \in J$. The model data is also defined on these indices: each project has a resource requirement $w_i$ and a value $p_i$. Each team has a capacity $c_j$. We will define binary variables $x_{ij}$ over possible assignment pairs $(i,j)$ in order to build the constraints and objective in the model.

The mathematical model is formulated as

$$
\begin{alignat}{2}
\max \quad        & \sum_{i \in I} \sum_{j \in J} p_{i} x_{ij} \\
\mbox{s.t.} \quad & \sum_{i \in I} w_{i} x_{ij} \le c_{j} & \forall j \in J \\
                  & \sum_{j \in J} x_{ij} \le 1 & \forall i \in I \\\
                  & x_{ij} \in \lbrace 0, 1 \rbrace & \forall i \in I, j \in J \\
\end{alignat}
$$

and is more commonly known as the Multiple Knapsack Problem (MKP).

This model has a slight twist: since the teams are heterogeneous, not all teams can complete all projects. We will deal with this requirement *before* constructing the model, by filtering the input data. In this way we leverage the inherent *sparsity* of the model variables to avoid adding redundant variables and reduce the overall model size.

+++

For all `gurobipy_pandas` applications, we start with the standard imports:

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

We will first read in the data for both projects and teams. To match our mathematical model, which is indexed based on projects $i$ and teams $j$, we will set the indexes of our pandas dataframes in the same way.

```{code-cell}
projects = pd.read_csv("data/projects.csv", index_col="project")
projects.head()
```

```{code-cell}
teams = pd.read_csv("data/teams.csv", index_col="team")
teams.head()
```

We first do some quick quality and size checks on the data. Clearly, it will not be possible to complete all projects with the available resource.

```{code-cell}
print(f"There are {len(projects)} projects and {len(teams)} teams.")
print(f"Total project resource required: {projects.resource.sum():.1f}")
print(f"Total team resource available: {teams.capacity.sum():.1f}")
```

We also check the heterogeneous nature of the projects and teams. This model follows a simple rule: team $j$ can complete project $i$ if $\text{skill}_j \ge \text{difficulty}_i$. So, we can see that the available teams (and therefore capacity) for projects with difficulty 3 is far less than the available capacity for projects with difficulty 1.

```{code-cell}
projects.difficulty.value_counts()
```

```{code-cell}
teams.skill.value_counts()
```

When formulating the model, we could create a variable for *every* index pair $(i, j)$, and later disallow the invalid assignments using constraints. But this would introduce redundant variables, creating a model which is larger than needed. We should instead exploit the natural sparsity of the problem by filtering on the data to find only the variables we need, *before we start to create variables*.

```{code-cell}
# Pandas does not have a conditional join, but we can use a
# cross join + query to create the list of allowed pairs.
# For larger datasets, this data filtering might be better
# done before loading into python/pandas (e.g. in SQL, which
# will handle this more efficiently).

allowed_pairs = (
    pd.merge(
        projects.reset_index(),
        teams.reset_index(),
        how='cross',
    )
    .query("difficulty <= skill")
    .set_index(["project", "team"])
)

print(
    f"Model will have {len(allowed_pairs)} variables"
    f" (out of a possible {len(projects) * len(teams)})"
)

allowed_pairs
```

The new dataframe we have constructed has a sparse index, which represents the small set of allowed pairs (roughly half the set of total possible pairs). This approach reduces the model size, and correspondingly the time taken to formulate it.

+++

## Model Formulation

From the `allowed_pairs` dataframe, `gurobipy_pandas` provides a free function to create a corresponding series of variables on our new index. We first create a gurobipy Model, then call `gppd.add_vars` to create a Gurobi variable for every entry in the index. Since the `value` column exists in this dataframe, we can reference this column directly to use it as the linear objective coefficient for each variable.

```{code-cell}
model = gp.Model()
model.ModelSense = GRB.MAXIMIZE
x = gppd.add_vars(model, allowed_pairs, vtype=GRB.BINARY, obj="value", name="x")
x
```

To add the necessary constraints to the model, we use pandas native groupby and aggregate operations to group our binary assignment variables along with their resource requirements. The result is a Series of expressions capturing the total resource requirement allocated to a team based on the selected assignments:

```{code-cell}
total_resource = (
    (projects["resource"] * x)
    .groupby("team").sum()
)
total_resource
```

We then use the free function `gppd.add_constrs` to create constraints by aligning these expressions with capacity data:

```{code-cell}
capacity_constraints = gppd.add_constrs(
    model, total_resource, GRB.LESS_EQUAL, teams["capacity"],
    name='capacity',
)
capacity_constraints.head()
```

We also need to constrain that each project is allocated to at most one team. This is done using the same function:

```{code-cell}
allocate_once = gppd.add_constrs(
    model, x.groupby('project').sum(),
    GRB.LESS_EQUAL, 1.0, name="allocate_once",
)
allocate_once.head()
```

## Extracting Solutions

With the model formulated, we solve it using the Gurobi Optimizer:

```{code-cell}
model.optimize()
```

To extract the solution, we use the series accessor `.gppd.X` to retrieve solution values for all variables in the series `x`:

```{code-cell}
x.gppd.X
```

Notice that the result is returned on the same index as `x` so we can directly apply pandas tranformations, so we can immediately use pandas methods to transform the result into a more readable form. We could also directly write the result to another file or result API. In this example, we will perform a simple aggregation to show the list of projects allocated to each team:

```{code-cell}
(
    x.gppd.X.to_frame()
    .query("x >= 0.9").reset_index()
    .groupby("team").agg({"project": list})
)
```

To aid in follow-up analysis, we can also use the series accessor `.gppd.Slack` on any constraint series to determine the slack in inequality constraints. For example, the following shows the spare capacity of each team in the current assignment:

```{code-cell}
capacity_constraints.gppd.Slack
```
