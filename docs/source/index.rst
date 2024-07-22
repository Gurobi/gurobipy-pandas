gurobipy-pandas documentation
=============================

``gurobipy-pandas`` is a convenient (optional) wrapper to connect
:pypi:`pandas` with :pypi:`gurobipy`. It enables users to more easily
and efficiently build mathematical optimization models from data stored
in DataFrames and Series, and to read solutions back directly as pandas
objects. The package provides simple to use functions and pandas
accessors to help build optimization models efficiently from data and
query solutions as pandas structures.

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

How to use this documentation
-----------------------------

- The :doc:`usage` page provides an overview of the key methods
  available for creating variables and constraints in an optimization
  model using pandas data as input.
- The :doc:`examples` provide complete model implementations as Jupyter
  notebooks.
- The :doc:`api` provides complete reference documentation for the
  library.
- The remaining sections (see the contents sidebar for a full listing)
  cover further details and techniques, and provide advice on writing
  clean and performant model building code using this library.

Contact us
----------

For questions related to using ``gurobipy-pandas`` please use the
`Gurobi Community Forum <https://support.gurobi.com/hc/en-us/community/topics/10373864542609-GitHub-Projects>`_.

For reporting bugs, issues and feature requests, specific to ``gurobipy-pandas``, please
`open an issue <https://github.com/Gurobi/gurobipy-pandas/issues>`_.

If you encounter issues with Gurobi or ``gurobipy`` please contact
`Gurobi Support <https://support.gurobi.com/hc/en-us>`_.


.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Getting Started

   installation
   usage
   examples

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Users Guide

   performance
   naming
   advanced
   typing

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Reference

   api
   license
   contact
   acknowledgements
