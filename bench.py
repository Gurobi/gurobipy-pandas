from contextlib import contextmanager
import time

import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import gurobipy_pandas as gppd

from gurobipy_pandas.util import gppd_global_options


@contextmanager
def extension_enabled():
    gppd_global_options["use_extension"] = True
    try:
        yield
    finally:
        gppd_global_options["use_extension"] = False


def perftest(model, n):
    index = pd.RangeIndex(n)
    result = pd.DataFrame(
        dict(
            x=gppd.add_vars(model, index, name="x"),
            y=gppd.add_vars(model, index, name="y"),
            z=gppd.add_vars(model, index, name="z"),
        )
    ).gppd.add_constrs(model, "x + y <= z", name="c")
    model.update()
    assert model.NumVars == n * 3
    assert model.NumConstrs == n
    assert result.shape == (n, 4)
    return result


def display(model, result):
    print(
        result.assign(
            lhs=lambda df: df["c"].apply(model.getRow),
            sense=lambda df: df["c"].gppd.Sense,
            rhs=lambda df: df["c"].gppd.RHS,
        )
    )


with gp.Env() as env:

    print("===== Without Extension =====")
    with gp.Model(env=env) as model:
        result = perftest(model, 5)
        display(model, result)

    print("===== With Extension =====")
    with extension_enabled(), gp.Model(env=env) as model:
        result = perftest(model, 5)
        display(model, result)

    n = 100000
    print(f"===== Create {n} linear constraints =====")

    with gp.Model(env=env) as model:
        tic = time.perf_counter()
        result = perftest(model, n)
        toc = time.perf_counter()
        print(f"Without Extension: {toc - tic:.2f}")

    with extension_enabled(), gp.Model(env=env) as model:
        tic = time.perf_counter()
        result = perftest(model, n)
        toc = time.perf_counter()
        print(f"With Extension:    {toc - tic:.2f}")
