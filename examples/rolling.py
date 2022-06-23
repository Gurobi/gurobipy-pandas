import pathlib
from telnetlib import IP

import pandas as pd
import gurobipy as gp

import pdcomfi.accessors

m = gp.Model()


here = pathlib.Path(__file__).parent
data = (
    pd.read_csv(here / "data/availability.csv")
    # Some munging required to assign some dates to the 'Tue9' strings.
    # In a real application, presumably there are already proper dates
    # stored in the pandas dataframe.
    .assign(
        ShiftDate=lambda df: df["Shift"]
        .str.replace("[A-Za-z]+([0-9]+)", lambda m: m.group(1), regex=True)
        .astype(int)
        .mul(pd.Timedelta(days=1))
        .add(pd.Timestamp("2022-06-30"))
    ).grb.addVars(m, name="assign", index=["Workers", "Shift"])
    # For demo purposes (show count of vars in rolling windows).
    .assign(value=1)
)
shifts = pd.date_range(
    start=data["ShiftDate"].min(), end=data["ShiftDate"].max(), freq="1D"
)
m.update()
print(data)

# Demo rolling window computation. Using the 'value' column,
# this counts the number of days in a given rolling window
# that a worker is available.
# Maybe this is cleaner without apply + lambda, especially if
# different workers have different shift requirements.
for worker, df in data.groupby("Workers"):
    rolling = (
        df.set_index("ShiftDate")["value"].reindex(shifts).fillna(0).rolling("7D").sum()
    )
    print("Worker")
    print(rolling)

# Try to do the same with the Var series, pandas rejects aggregation
# of non-numeric types. Not sure if this is a permanent limitation,
# an extension array may be able to resolve it.
# for worker, df in data.groupby("Workers"):
#     print("Worker")
#     print(df.set_index("ShiftDate")["assign"].reindex(shifts).fillna(0).rolling("7D").sum())
