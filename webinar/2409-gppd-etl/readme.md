# Databricks Staff Rostering ETL Workflow

This directory contains an example Databricks optimization workflow as presented
in the Gurobi webinar "Running Optimization Models in an ETL Pipeline". The
webinar slides can be found
[here](https://gurobi.github.io/gurobipy-pandas/gppd-etl).

Note that this demo was built with easy setup in mind. Many aspects are
simplified compared to a practical configuration.

## Setup steps

1. Set up an Azure Databricks workspace and configure Databricks CLI

2. Clone this repo into your databricks workspace:

```
databricks repos create \
    https://github.com/Gurobi/gurobipy-pandas.git \
    --path /Shared/gurobipy-pandas
```

3. Create the job using the `workflow.json` file in this directory:

```
databricks jobs create --json @workflow.json
```

## Running the job

Execute the job using the UI in the "Workflows" tab in your databricks
workspace. Alternatively, you can launch the job using:

```
databricks jobs run-now
```

## Using Gurobi Instant Cloud

By default, the optimization task will run locally in databricks using a free
size-limited Gurobi license. If secrets are configured, the optimization will be
run remotely using Gurobi Instant Cloud. Use the following commands to provide
your cloud API key details as databricks secrets (each command separately
prompts you to enter a secret):

```
databricks secrets create-scope grbcloud
databricks secrets put-secret grbcloud cloudaccessid
databricks secrets put-secret grbcloud cloudsecretkey
databricks secrets put-secret grbcloud licenseid
databricks secrets put-secret grbcloud csappname
databricks secrets put-secret grbcloud cloudpool
```
