Using Type Hints
================

The ``gurobipy-pandas`` API is partially typed. There is currently no
mechanism in Python's type system to allow for type checking of the
DataFrame or Series accessor methods. So, it is only possible to get
type checking in your IDE, or static type checking with tools like
``mypy`` if you use the global functions ``gppd.add_vars`` and
``gppd.add_constrs`` when building your model.

To enable type checking, you will also need to install
:pypi:`pandas-stubs` in your Python environment.
