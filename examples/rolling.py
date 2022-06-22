import pandas as pd
import gurobipy as gp


m = gp.Model()

data = (
    pd.read_csv("examples/data/availability.csv")
    .assign(
        ShiftTime=lambda df: df["Shift"]
        .str.replace("[A-Za-z]+([0-9]+)", lambda m: m.group(1), regex=True)
        .astype(int)
        .mul(pd.Timedelta(days=1))
        .add(pd.Timestamp("2022-06-30"))
    )
    .assign(assign=lambda df: list(m.addVars(df.index).values()))
    .assign(value=1)
)

m.update()

print(data)

print(
    data.groupby("Workers").apply(
        lambda g: g.set_index("ShiftTime").rolling("7D")["value"].sum()
    )
)

print(
    data.groupby("Workers").apply(
        lambda g: g.set_index("ShiftTime")[["assign"]]
        .rolling("7D", method="table")
        .apply(lambda g: g["assign"].sum(), engine="cython")
    )
)
