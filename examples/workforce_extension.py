"""
Workforce model using extension API features (comparison overloads)
to create variables and constraints. The accessor API is still needed
for attribute access in order to query the solution.
"""

import pathlib

import pandas as pd
import gurobipy_pandas.accessors
from gurobipy_pandas.extension import Model


# Load data (multiple frames for different model components).
here = pathlib.Path(__file__).parent
availability = pd.read_csv(here / "data/availability.csv")
shift_req = pd.read_csv(here / "data/shiftReq.csv", index_col=[0])
pay = pd.read_csv(here / "data/workerpay.csv", index_col=[0])

m = Model()

# Variable series created from an index.
assign = m.addSeriesVars(
    availability.set_index(["Shift", "Workers"]).index, name="assign", ub=1.0
)

# Construct expressions by grouping & aggregating variables, then compare
# with data. It's a bit inconvenient to have variables as a series since
# the grouping keys are now in the index.
lhs = assign.reset_index().groupby("Shift")["assign"].sum()
# Indexes must be perfectly aligned for pandas to allow comparison operators
# in pandas, so we have to fix ordering either using .loc or .align.
shift_cover = m.addSeriesConstrs(
    lhs == shift_req["Req"].loc[lhs.index], name="shift_cover"
)

# Single expressions can be constructed using element-wise operations and
# aggregations; then the usual model functions will work.
m.setObjective(
    (assign.reset_index().groupby("Workers")["assign"].sum() * pay["Pay"]).sum()
)

# Optimize model.
m.optimize()

# Variables dataframe. Printing needs another thing implemented.
# print(assign)

# Constraints are a series, can check attributes using accessors.
print(shift_cover.grb.Slack)

# Employees assigned to each shift + shifts (use accessor API).
df = assign.reset_index()
print(df[df["assign"].grb.X > 0.9].groupby("Shift")["Workers"].agg(list))

# Shift assignments table. Here it is convenient that assign
# is already a series.
print((assign.grb.X.unstack() > 0.9).replace({True: "Y", False: "-"}))
