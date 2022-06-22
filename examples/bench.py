import time

import pandas as pd
import numpy as np
import gurobipy as gp


def bench(n, m):

    print(f"Bench {n = }  {m = }")

    model = gp.Model()

    tic = time.perf_counter()
    data = {}
    for i in range(m):
        data[f"c{i}"] = np.random.random(n)
    df = pd.DataFrame(data)
    print(f"Create m column df:    {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    x = np.array(model.addVars(n, name='x').values())
    assert pd.api.types.is_object_dtype(x)
    print(f"Create x vars:         {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    y = np.array(model.addVars(n, name='y').values())
    assert pd.api.types.is_object_dtype(y)
    print(f"Create y vars:         {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    sx = pd.Series(x)
    print(f"Create x series:       {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    sy = pd.Series(y)
    print(f"Create y series:       {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    df2 = df.assign(x=x)
    print(f"Create frame + x:      {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    df3 = df.assign(x=x).assign(y=y)
    print(f"Create frame + x + y:  {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    df4 = df.copy()
    df['x'] = x
    df['y'] = y
    print(f"Create frame + x + y:  {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    expr = df3['c0'] * df3['x']
    print(f"Element-wise c0 * x    {time.perf_counter() - tic:6.3f}")

    tic = time.perf_counter()
    expr = sx + sy
    print(f"Element-wise x + y:    {time.perf_counter() - tic:6.3f}")

bench(n=1_000_000, m=3)
print()
bench(n=1_000_000, m=20)
