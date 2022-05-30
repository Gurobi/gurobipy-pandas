import pathlib

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import pdcomfi


# Load data (multiple frames for different model components).
here = pathlib.Path(__file__).parent
availability = pd.read_csv(here / "data/availability.csv")
shift_req = pd.read_csv(here / "data/shiftReq.csv", index_col=[0])
pay = pd.read_csv(here / "data/workerpay.csv", index_col=[0])

m = gp.Model()

# Variables added as a column.
df = availability.grb.addVars(m, name="assign", index=["Shift", "Workers"], ub=1.0)

# Construct expressions by grouping & aggregating variables, joining with
# data. Add constraints element-wise from the result using dataframe accessor.
shift_cover = (
    df.groupby("Shift")[["assign"]]
    .sum()
    .join(shift_req)
    .grb.addLConstrs(m, "assign", GRB.EQUAL, "Req", name="shift_cover")
)

# Single expressions can be constructed using element-wise operations and
# aggregations; then the usual model functions will work.
m.setObjective((df.groupby("Workers")["assign"].sum() * pay["Pay"]).sum())

# Optimize model.
m.optimize()

# Variables joined onto availability dataframe.
print(df)

# Constraints joined recorded as a joined column
print(shift_cover)

# Employees assigned to each shift + shifts
print(df[df["assign"].grb.X > 0.9].groupby("Shift")["Workers"].agg(list))

# Shift assignments table.
print(
    (df.set_index(['Shift', 'Workers'])['assign'].grb.X.unstack() > 0.9)
    .replace({True: "Y", False: "-"})
)
