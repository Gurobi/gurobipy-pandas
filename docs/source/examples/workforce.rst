Workforce Scheduling
====================

Assigning shifts to maximize worker happiness!!

Basic code done, need to document the mathematical model in mathjax alongside (index corresponds directly to sets, column corresponds directly to data defined over that set).

.. testsetup:: workforce

    # Already in examples/data dir, to shorten file paths
    import os
    pwd = os.getcwd()
    os.chdir("source/examples")

    # Set pandas options
    import pandas as pd
    old_max_rows = pd.options.display.max_rows
    pd.options.display.max_rows = 10

.. testcleanup:: workforce

    os.chdir(pwd)
    pd.options.display.max_rows = old_max_rows

Standard imports ...

.. testcode:: workforce

    import pandas as pd
    import gurobipy as gp
    from gurobipy import GRB
    import gurobipy_pandas

Read in the data. Preference data contains 3 columns: shift date, worker, and preference value. If a worker is not available for a given shift, then that work-shift combination does not appear in the table.

.. testcode:: workforce

    preferences = pd.read_feather("data/preferences.feather")
    print(preferences)

.. testoutput:: workforce
    :options: +NORMALIZE_WHITESPACE

       Worker      Shift  Preference
    0     Amy 2022-07-02           1
    1     Amy 2022-07-03           3
    2     Amy 2022-07-05           2
    3     Amy 2022-07-07           2
    4     Amy 2022-07-09           1
    ..    ...        ...         ...
    67     Gu 2022-07-10           2
    68     Gu 2022-07-11           2
    69     Gu 2022-07-12           2
    70     Gu 2022-07-13           2
    71     Gu 2022-07-14           3

    [72 rows x 3 columns]

Shift requirements data indicates the number of required workers for each shift.

.. testcode:: workforce

    shift_requirements = (
        pd.read_feather("data/shift_requirements.feather")
        .set_index("Shift")
    )
    print(shift_requirements)

.. testoutput:: workforce
    :options: +NORMALIZE_WHITESPACE

                Required
    Shift
    2022-07-01         3
    2022-07-02         2
    2022-07-03         4
    2022-07-04         2
    2022-07-05         5
    ...              ...
    2022-07-10         3
    2022-07-11         4
    2022-07-12         5
    2022-07-13         7
    2022-07-14         5

    [14 rows x 1 columns]

Our goal is to fill all available shifts with the required number of workers, while maximising the total preference values of assignments. To do this, we'll create a binary variable for each worker (1 = shift assigned) and use preferences as the objective.

Semantics: worker and shift are index sets in the model, we should put these in the index of the dataframe.

Note: binary vars can be relaxed without issue in this model, but we should keep them binary so that the modelling is clear to newbies.

Note: in the gurobipy-pandas API, we only use Model() and Env() calls from gurobipy

.. testcode:: workforce

    m = gp.Model()
    df = (
        preferences
        .set_index(["Worker", "Shift"])
        .grb.pdAddVars(m, name="assign", vtype=GRB.BINARY, obj="Preference")
    )
    m.update()
    print(df)

.. testoutput:: workforce
    :options: +NORMALIZE_WHITESPACE

                       Preference                                        assign
    Worker Shift
    Amy    2022-07-02           1  <gurobi.Var assign[Amy,2022-07-02 00:00:00]>
           2022-07-03           3  <gurobi.Var assign[Amy,2022-07-03 00:00:00]>
           2022-07-05           2  <gurobi.Var assign[Amy,2022-07-05 00:00:00]>
           2022-07-07           2  <gurobi.Var assign[Amy,2022-07-07 00:00:00]>
           2022-07-09           1  <gurobi.Var assign[Amy,2022-07-09 00:00:00]>
    ...                       ...                                           ...
    Gu     2022-07-10           2   <gurobi.Var assign[Gu,2022-07-10 00:00:00]>
           2022-07-11           2   <gurobi.Var assign[Gu,2022-07-11 00:00:00]>
           2022-07-12           2   <gurobi.Var assign[Gu,2022-07-12 00:00:00]>
           2022-07-13           2   <gurobi.Var assign[Gu,2022-07-13 00:00:00]>
           2022-07-14           3   <gurobi.Var assign[Gu,2022-07-14 00:00:00]>

    [72 rows x 2 columns]

By grouping variables across one of our indices, we can efficiently construct the shift requirement constraints. This involves a few transform steps.

Todo: explain each column, constraint w.r.t mathematical model

Fixme: .update() calls just to show naming are annoying to have to include... need to think about how to include (to show naming effect) while indicating to users that they should not update() during formulation in general.

.. testcode:: workforce

    shift_cover = (
        df.groupby('Shift')[['assign']].sum()
        .join(shift_requirements)
        .grb.pdAddConstrs(m, "assign == Required", name="shift_cover")
    )
    m.update()
    print(shift_cover)

.. testoutput:: workforce
    :options: +NORMALIZE_WHITESPACE

                                                           assign  Required                                       shift_cover
    Shift
    2022-07-01  <gurobi.LinExpr: assign[Bob,2022-07-01 00:00:0...         3  <gurobi.Constr shift_cover[2022-07-01 00:00:00]>
    2022-07-02  <gurobi.LinExpr: assign[Amy,2022-07-02 00:00:0...         2  <gurobi.Constr shift_cover[2022-07-02 00:00:00]>
    2022-07-03  <gurobi.LinExpr: assign[Amy,2022-07-03 00:00:0...         4  <gurobi.Constr shift_cover[2022-07-03 00:00:00]>
    2022-07-04  <gurobi.LinExpr: assign[Cathy,2022-07-04 00:00...         2  <gurobi.Constr shift_cover[2022-07-04 00:00:00]>
    2022-07-05  <gurobi.LinExpr: assign[Amy,2022-07-05 00:00:0...         5  <gurobi.Constr shift_cover[2022-07-05 00:00:00]>
    ...                                                       ...       ...                                               ...
    2022-07-10  <gurobi.LinExpr: assign[Amy,2022-07-10 00:00:0...         3  <gurobi.Constr shift_cover[2022-07-10 00:00:00]>
    2022-07-11  <gurobi.LinExpr: assign[Amy,2022-07-11 00:00:0...         4  <gurobi.Constr shift_cover[2022-07-11 00:00:00]>
    2022-07-12  <gurobi.LinExpr: assign[Amy,2022-07-12 00:00:0...         5  <gurobi.Constr shift_cover[2022-07-12 00:00:00]>
    2022-07-13  <gurobi.LinExpr: assign[Amy,2022-07-13 00:00:0...         7  <gurobi.Constr shift_cover[2022-07-13 00:00:00]>
    2022-07-14  <gurobi.LinExpr: assign[Amy,2022-07-14 00:00:0...         5  <gurobi.Constr shift_cover[2022-07-14 00:00:00]>

    [14 rows x 3 columns]

Optimize

.. testcode:: workforce

    m.optimize()

.. testoutput:: workforce
    :options: +NORMALIZE_WHITESPACE

    Gurobi Optimizer version ...
    Optimal solution found (tolerance 1.00e-04)
    Best objective 9.600000000000e+01, best bound 9.600000000000e+01, gap 0.0000%

Get solution using series accessors.

Todo: it might be good to have a series accessor which recognised binary variable types and returned a boolean series for the result. Then the modelling looks a bit more natural for decision problems.

.. testcode:: workforce

    solution = df['assign'].grb.X
    print(solution)

.. testoutput:: workforce
    :options: +NORMALIZE_WHITESPACE

    Worker  Shift
    Amy     2022-07-02    1.0
            2022-07-03    0.0
            2022-07-05    1.0
            2022-07-07    1.0
            2022-07-09    1.0
                         ... 
    Gu      2022-07-10    1.0
            2022-07-11    1.0
            2022-07-12    1.0
            2022-07-13    1.0
            2022-07-14    0.0
    Name: assign, Length: 72, dtype: float64

Use the 0/1 solution values to filter down tot he 52 selected shift assignments.

.. testcode:: workforce

    assigned_shifts = solution.reset_index().query("assign == 1")
    print(assigned_shifts)

.. testoutput:: workforce
    :options: +NORMALIZE_WHITESPACE

       Worker      Shift  assign
    0     Amy 2022-07-02     1.0
    2     Amy 2022-07-05     1.0
    3     Amy 2022-07-07     1.0
    4     Amy 2022-07-09     1.0
    7     Amy 2022-07-12     1.0
    ..    ...        ...     ...
    64     Gu 2022-07-07     1.0
    67     Gu 2022-07-10     1.0
    68     Gu 2022-07-11     1.0
    69     Gu 2022-07-12     1.0
    70     Gu 2022-07-13     1.0
    
    [52 rows x 3 columns]
