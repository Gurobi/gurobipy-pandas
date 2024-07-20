gurobipy-pandas documentation
=============================

``gurobipy-pandas`` is a convenient (optional) wrapper to connect
:pypi:`pandas` with :pypi:`gurobipy`. It enables users to more easily
and efficiently build mathematical optimization models from data stored
in DataFrames and Series, and to read solutions back directly as pandas
objects.

``gurobipy-pandas`` is aimed at experienced pandas users who are
familiar with methods to transform, group, and aggregate data stored in
dataframes. It expects some familiarity with optimization modelling, but
does not require deep experience with gurobipy.

Installation
------------

:code:`gurobipy-pandas` can be installed directly from PyPI::

   python -m pip install gurobipy-pandas

This will also install pandas and gurobipy as dependencies.

Please note that gurobipy is commercial software and requires a license.
The package ships with an evaluation license which is only for testing
and can only solve models of limited size. You will be able to run all
the examples given in this documentation using this evaluation license.

A Simple Example
----------------

Build a simple optimization model!

How to Use this Documentation
-----------------------------

``gurobipy-pandas`` provides simple to use functions and pandas
accessors to help build optimization models and query solutions. Read
the :doc:`usage` page first for an overview of the key methods. Second,
explore the :doc:`examples` which provide complete model implementations
formatted as Jupyter notebooks. The :doc:`howto` cover methods for
specific use-cases and provide advice on writing clean and performant
model building code using this library. The :doc:`api` provides complete
reference documentation for the library.

Contact Us
----------

For questions related to using gurobipy-pandas please use the
`Gurobi Community Forum <https://support.gurobi.com/hc/en-us/community/topics/10373864542609-GitHub-Projects>`_.

For reporting bugs, issues and feature requests, specific to ``gurobipy-pandas``, please
`open an issue <https://github.com/Gurobi/gurobipy-pandas/issues>`_.

If you encounter issues with Gurobi or ``gurobipy`` please contact
`Gurobi Support <https://support.gurobi.com/hc/en-us>`_.



.. toctree::
   :hidden:

   installation
   usage
   examples
   How To ... <howto>
   api
   license
   contact
   acknowledgements
