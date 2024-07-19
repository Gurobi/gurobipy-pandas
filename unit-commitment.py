import io
import textwrap

import gurobipy as gp
import matplotlib.pyplot as plt
import pandas as pd
from gurobipy import GRB

import gurobipy_pandas as gppd

gppd.set_interactive()

########
# Data schema
#
# Each generator has properties which remain fixed over all time periods
#
# - num_available: number of available generating units
# - min_output: minimum generation in MWh for each active generator
# - max_output: maximum generation in MWh for each active generator
# - cost_per_hour: $ cost per hour per active generator
# - marginal cost: cost in $/MWh for generation above min_output
# - startup_cost: fixed cost incurred for starting a generator in an interval
# - state0: number of generators active before the first period
#
# Each time period has the following data
#
# - expected_demand: predicted MWh demand, which the solution will meet exactly
# - minimum_capacity: value in MWh above the predicted demand; the total online
#                     generation capacity must exceed this value
#
########

generator_data = pd.read_csv(
    io.StringIO(
        textwrap.dedent(
            """
            generator_class,num_available,min_output,max_output,cost_per_hour,marginal_cost,startup_cost,state0
            thermal1,12,850.0,2000.0,1000.0,2.0,2000.0,0
            thermal2,10,1250.0,1750.0,2600.0,1.30,1000.0,0
            thermal3,5,1500.0,4000.0,3000.0,3.0,500.0,0
            """
        )
    ),
    index_col=0,
)

time_period_data = (
    pd.read_csv(
        io.StringIO(
            textwrap.dedent(
                """
                time_period,expected_demand,minimum_active_capacity
                0,15000.0,17250.0
                1,30000.0,34500.0
                2,25000.0,28750.0
                3,40000.0,46000.0
                4,27000.0,31050.0
                """
            )
        )
    )
    .assign(
        time_period=pd.date_range(
            pd.Timestamp("2024-07-19 06:00:00"), freq="h", periods=5
        )
    )
    .set_index("time_period")
)

# Set up variables based on the data schema
#
# For each generator type, we have three classes of variables:
#
# - The total output of all generators in the class in the given time
#   period (continuous)
# - The number of active generators of the class in the given time period
#   (integer, upper bounded by number of available generators)
# - The number of active generators of the class which start up in the
#   given time period (integer)
#
# One variable is required for every generator class and time period

env = gp.Env()
model = gp.Model(env=env)

# Method chain our way to creating these variable sets.
# We need to create a dense index: generators x time periods.

index_formatter = {"time_period": lambda index: index.strftime("%H%M")}
generators = (
    pd.DataFrame(
        index=pd.MultiIndex.from_product([generator_data.index, time_period_data.index])
    )
    .join(generator_data)
    .gppd.add_vars(model, name="output", index_formatter=index_formatter)
    .gppd.add_vars(
        model,
        vtype=GRB.INTEGER,
        ub="num_available",
        name="num_active",
        index_formatter=index_formatter,
    )
    .gppd.add_vars(
        model, vtype=GRB.INTEGER, name="num_startup", index_formatter=index_formatter
    )
)

# Constrain that predicted demand is exactly satisfied
demand_constraint = gppd.add_constrs(
    model,
    generators.groupby("time_period")["output"].sum(),
    GRB.EQUAL,
    time_period_data["expected_demand"],
)

# Constrain that generators are producing between their minimum and maximum
gppd.add_constrs(
    model,
    generators["output"],
    GRB.GREATER_EQUAL,
    generators["min_output"] * generators["num_active"],
)
gppd.add_constrs(
    model,
    generators["output"],
    GRB.LESS_EQUAL,
    generators["max_output"] * generators["num_active"],
)

# Constrain that the started generators during each time period are capable
# of meeting the reserve demand
active_capacity = (
    (generators["max_output"] * generators["num_active"]).groupby("time_period").sum()
)
max_capacity_constraint = gppd.add_constrs(
    model,
    active_capacity,
    GRB.GREATER_EQUAL,
    time_period_data["minimum_active_capacity"],
)

# Compute total generation cost over all time periods
generation_costs = (
    # Fixed hourly costs for started generators
    generators["cost_per_hour"] * generators["num_active"]
    # Marginal hourly cost of additional generation above the minimum
    + generators["marginal_cost"]
    * (generators["output"] - generators["num_active"] * generators["min_output"])
)

# Compute total startup costs over all time periods.

# 1. Constrain the relationship between active generators and startups.


def startup_constraints(group):
    group = group.sort_index()
    return gppd.add_constrs(
        model,
        group["num_startup"].iloc[1:],
        GRB.GREATER_EQUAL,
        (group["num_active"] - group["num_active"].shift(1)).dropna(),
        name="startup",
    ).to_frame()


startup = generators.groupby("generator_class").apply(startup_constraints).droplevel(0)

# 2. Startup costs compared to initial state

time_period_1 = generators.sort_index().groupby("generator_class").first()
initial_startup = gppd.add_constrs(
    model,
    time_period_1["num_startup"],
    GRB.GREATER_EQUAL,
    time_period_1["num_active"] - generator_data["state0"],
    name="initial_startup",
)

# 3. Compute total startup cost incurred

total_startup_costs = (generators["startup_cost"] * generators["num_startup"]).sum()

# Minimize total cost objective
model.setObjective(total_generation_costs + total_startup_costs, sense=GRB.MINIMIZE)

# Do the magic
model.write("unit-commitment.lp")
model.optimize()

# Present results
print(
    pd.DataFrame(
        dict(
            num_active=generators["num_active"].gppd.X,
            num_startup=generators["num_startup"].gppd.X,
        )
    ).to_markdown()
)

pd.DataFrame(
    {
        "Demand": time_period_data["expected_demand"],
        "Min. Active Capacity": time_period_data["minimum_active_capacity"],
        "Active Capacity": active_capacity.gppd.get_value(),
    }
).plot.line()

plt.show()

# Clean up

model.close()
env.close()
