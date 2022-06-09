Pandas operator behaviour
=========================

>>> import pandas as pd

>>> import numpy as np

>>> s = pd.Series(np.arange(10))

>>> x = s[[1, 3, 5, 7]]

>>> y = s[[4, 5, 7, 8]]

>>> x + y
1     NaN
3     NaN
4     NaN
5    10.0
7    14.0
8     NaN
dtype: float64

>>> x + y >= 0  # NaN's eval to true
Out[20]: 
1    False
3    False
4    False
5     True
7     True
8    False
dtype: bool

>>> x <= y
Traceback (most recent call last)
    ...
ValueError: Can only compare identically-labeled Series objects

>>> x.le(y)
1    False
3    False
4    False
5     True
7     True
8    False
dtype: bool

>>> x.le(y, fill_value=0)
Out[28]: 
1    False
3    False
4     True
5     True
7     True
8     True
dtype: bool



>>> import gurobipy as gp

>>> m = gp.Model()

>>> x = pd.Series(m.addVars(5, name="x"))

>>> y = pd.Series(m.addVars(3, name="x"))

>>> m.update()

>>> x
0    <gurobi.Var x[0]>
1    <gurobi.Var x[1]>
2    <gurobi.Var x[2]>
3    <gurobi.Var x[3]>
4    <gurobi.Var x[4]>
dtype: object

>>> y
0    <gurobi.Var x[0]>
1    <gurobi.Var x[1]>
2    <gurobi.Var x[2]>
dtype: object

>>> x <= y
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: Can only compare identically-labeled Series objects

>>> x.loc[y.index] <= y
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
gurobipy.GurobiError: Constraint has no bool value (are you trying "lb <= expr <= ub"?)

This method avoids the identically-labeled series requirement imposed on the operators, but it still tries to cast to boolean.

>>> x.loc[y.index].le(y)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
gurobipy.GurobiError: Constraint has no bool value (are you trying "lb <= expr <= ub"?)


>>> x.le(y)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
gurobipy.GurobiError: Constraint has no bool value (are you trying "lb <= expr <= ub"?)

>>> x + y
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
gurobipy.GurobiError: Constant is Nan

>>> x.add(y)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
gurobipy.GurobiError: Constant is Nan

Can fill to fix this, but it only works on one side. And this is not what pandas expects, really 3 & 4 should be `nan`. Can be fixed by our own arithmetic operator implementations which filter out the nans in advance.

>>> x.add(y, fill_value=0)
0    <gurobi.LinExpr: x[0] + x[0]>
1    <gurobi.LinExpr: x[1] + x[1]>
2    <gurobi.LinExpr: x[2] + x[2]>
3           <gurobi.LinExpr: x[3]>
4           <gurobi.LinExpr: x[4]>
dtype: object
