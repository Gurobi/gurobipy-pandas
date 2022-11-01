.. New Docs Outline
.. ----------------

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



.. Points to cover:

.. - Goals/intention: create gurobipy variables and constraints simply/cleanly/efficiently from pandas data structures
.. - Target audience: familiar with pandas, comfortable transforming data in pandas, some familiarity with Gurobi/gurobipy
.. - The API (brief example illustrating all of this?)
..    - Add variables as series
..       - global functions, get back series
..       - dataframe accessor, append columns and method chain
..    - Use pandas arithmetic operations
..    - Build constraints by row
..       - global functions, get back series
..       - dataframe accessor, append columns and method chain
..    - gurobipy
..       - some parts of the gurobipy API need to be used in most models
..       - Env, Model, setObjective, sometimes addConstr or addVar for non-indexed variables/constraints
..    - Attribute access / series-wise queries
..       - series accessor
..       - See attributes pages on gurobi site
.. - Model Sparsity
..    - Indexes in pandas are flexible and powerful
..    - Most mathematical optimization models have sparse index sets
..    - Leverage sparse indexes to avoid creating unnecessary variables
..    - Pandas' aggregation operations efficiently transform between the index sets in your model
.. - Variable and constraint names
..    - See naming.rst
.. - Advice for building models efficiently / performance concerns
..    - Query, prepare and clean your data as a first step, *before creating a model*
..    - Align all data on an appropriate index (this should match your mathematical model)
..    - Operations along rows which mix data types in pandas can be slow. However it's necessary to build constraints (mix data and modelling objects). gppd provides efficient implementations here to avoid performance bottlenecks. *You still need to be careful to use efficient operations when processing your data in the first place*
..    - You should not try to use a pandas structure iteratively like a list or dict
.. - Advanced patterns
..    - At present, gppd only implements arithmetic constraints
..    - If you need SOS or general constraints, here is the general pattern to follow
.. - Modelling examples
.. - Licensing info
.. - Gurobi environments
