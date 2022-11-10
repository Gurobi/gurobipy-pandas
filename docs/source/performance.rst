.. - Advice for building models efficiently / performance concerns
..    - Query, prepare and clean your data as a first step, *before creating a model*
..    - Align all data on an appropriate index (this should match your mathematical model)
..    - Operations along rows which mix data types in pandas can be slow. However it's necessary to build constraints (mix data and modelling objects). gppd provides efficient implementations here to avoid performance bottlenecks. *You still need to be careful to use efficient operations when processing your data in the first place*
..    - You should not try to use a pandas structure iteratively like a list or dict
..    - In the current implementation, .agg(gp.quicksum) is faster than .sum(), though the result is the same

Performance
===========
