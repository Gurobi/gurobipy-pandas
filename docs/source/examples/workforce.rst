Workforce Scheduling
====================

.. ipython:: python

    import pandas as pd
    import gurobipy as gp
    from gurobipy import GRB
    import gurobipy_pandas


Read in the data. Preference data contains 3 columns: shift date, worker, and preference value. If a worker is not available for a given shift, then that work-shift combination does not appear in the table.

.. ipython:: python

    preferences = pd.read_feather("source/examples/data/preferences.feather")
    preferences

Shift requirements data indicates the number of required workers for each shift.

.. ipython:: python

    shift_requirements = (
        pd.read_feather("source/examples/data/shift_requirements.feather")
        .set_index("Shift")
    )
    shift_requirements

Our goal is to fill all available shifts with the required number of workers, while maximising the total preference values of assignments. To do this, we'll create a binary variable for each worker (1 = shift assigned) and use preferences as the objective.

Semantics: worker and shift are index sets in the model, we should put these in the index of the dataframe.

Note: binary vars can be relaxed without issue in this model, but we should keep them binary so that the modelling is clear to newbies.

Note: in the gurobipy-pandas API, we only use Model() and Env() calls from gurobipy

.. ipython:: python

    m = gp.Model()
    df = (
        preferences
        .set_index(["Worker", "Shift"])
        .grb.pdAddVars(m, name="assign", vtype=GRB.BINARY, obj="Preference")
    )
    m.update()
    df

By grouping variables across one of our indices, we can efficiently construct the shift requirement constraints. This involves a few transform steps.

Todo: explain each column, constraint w.r.t mathematical model

Fixme: .update() calls just to show naming are annoying to have to include... need to think about how to include (to show naming effect) while indicating to users that they should not update() during formulation in general.

.. ipython:: python

    shift_cover = (
        df.groupby('Shift')[['assign']].sum()
        .join(shift_requirements)
        .grb.pdAddConstrs(m, "assign == Required", name="shift_cover")
    )
    m.update()
    shift_cover

Optimize

.. ipython:: python

    m.optimize()

Get solution using series accessors.

Todo: it might be good to have a series accessor which recognised binary variable types and returned a boolean series for the result. Then the modelling looks a bit more natural for decision problems.

.. ipython:: python

    solution = df['assign'].grb.X
    solution

Use the 0/1 solution values to filter down tot he 52 selected shift assignments.

.. ipython:: python

    assigned_shifts = solution.reset_index().query("assign == 1")
    assigned_shifts
