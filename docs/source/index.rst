Welcome to gurobipy-pandas's documentation!
===========================================

``gurobipy-pandas`` is a convenient (optional) wrapper to connect pandas with gurobipy. It enables users to more easily and efficiently build mathematical optimization models from data stored in DataFrames and Series, and to read solutions back directly as pandas objects.

``gurobipy-pandas`` is aimed at experienced pandas users who are familiar with methods to transform, group, and aggregate data stored in dataframes. It expects some familiarity with optimization modelling, but does not require deep experience with gurobipy.

Getting Started
---------------

``gurobipy-pandas`` provides simple to use functions and pandas accessors to help build optimization models and query solutions. Read the :doc:`usage` page first for an overview of the key methods. Second, explore the :doc:`examples` which provide complete model implementations formatted as Jupyter notebooks. The later sections cover advanced techniques, and advice on writing clean and performant model building code using this library.

Documentation
-------------

.. toctree::
   :maxdepth: 1
   :caption: Start

   installation
   usage
   examples

.. toctree::
   :maxdepth: 1
   :caption: Model Building

   performance
   naming
   advanced

.. toctree::
   :maxdepth: 1
   :caption: Reference

   api
   typing
   license
   contact
   acknowledgements
