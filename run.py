import gurobipy as gp
import pandas as pd
import pdcomfi.extension

m = gp.Model()

x = pd.Series(m.addVars(10, name="x")).astype("gpobj")
m.update()

# ValueError: Can only compare identically-labeled Series objects
# Does Greg's code break this?
# Can't hack this ... there's an inherent difference between behaviour
# of comparison and arithmetic operations on a series. I think it's
# by design.
# We don't even enter the comparison ops of the extension array here.
print(x <= x[:5])

# Behaviour of the above is different to this:
# gurobipy.GurobiError: Constant is Nan
print(x - x[:5] <= 0)
# To make this work we need to implement the arithmetic operators
# ourselves, the defaults won't do.
# Is there an application for this? I guess it would be helpful
# as a way to implement a set intersection?
# Implementation: vectorise with a nan check?

# Application:
# x_i               \forall i \in I
# y_i               \forall j \in J
# x_i + y_i <= 1    \forall i \in I \intersection J
#
# (x + y <= 1)

# TL;DR - comparison operators are fundamentally meant to be logical
# operators in pandas.
