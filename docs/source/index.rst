Welcome to gurobipy-pandas's documentation!
===========================================

**This package is in beta development and not supported. The API may change without warning.**

-----

.. - Goals/intention: create gurobipy variables and constraints simply/cleanly/efficiently from pandas data structures
.. - Target audience: familiar with pandas, comfortable transforming data in pandas, some familiarity with Gurobi/gurobipy

:code:`gurobipy-pandas` is a convenient (optional) wrapper to connect pandas with gurobipy. It enables users to more easily and cleanly build mathematical optimization models from data stored in pandas objects.

:code:`gurobipy-pandas` is aimed at experienced pandas users who are familiar with methods to transform, group, and aggregate data stored in dataframes. It expects some familiarity with optimization modelling, but does not require deep experience with gurobipy.

.. 1. Why this package?
..    - Pandas is great at manipulating column structured data. However when building optimization models, that data needs to interact with modelling objects / row-wise operations need to be performed. This is not pandas' core competency, and it's easy to create performance headaches.
..    - `gurobipy-pandas` provides a few simple functions/accessors/extensions to help build optimization models using pandas data structures (and query solutions, etc)
.. 2. How to read/use this doc?
..    - First read the pandas primer. Even if you're an experienced pandas user, have a read. Here we point out some key features and common pitfalls when ti comes to pandas and building optimization models in python.
..       - Primer will point out column-wise data storage and emphasise that with this package, we provide fast implementations and convenient syntax for the inevitable row-wise operations that you need to create interesting constraints.
..    - Read the API overview. `gurobipy-pandas`` consists of only two key methods, ...
..       - This page should also note that the 'glue' for arithmetic operations is provided by pandas itself, but again, you should work series-wise when doing this
..    - Read the examples
..       - Put mathematical models next to their implementation in code
..       - Emphasise data cleaning and where it should be done (before the model: this is model-data separation in python: do your cleaning steps first, then build the model in a quick pass with no intermingled data processing logic).
..    - Check antipatterns (list of bad performance code paths to watch out for)

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

   sparsity
   naming
   performance
   advanced

.. toctree::
   :maxdepth: 1
   :caption: Reference

   license
   contact
   api
