---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.1
---

# Portfolio selection

Given a sum of money to invest, one must decide how to spend it amongst a portfolio of financial securities.  Our approach is due to Markowitz (1959) and looks to minimize the risk associated with the investment while realizing a target expected return.  By varying the target, one can compute an 'efficient frontier', which defines the optimal portfolio for a given expected return.

Adapted from the Gurobi examples. This does not illustrate the accessor API since all constraints are single expressions.

Point to think about though: when we do construct a single expression by applying pandas operations to series, the user has to fall back onto gurobipy methods.

```{code-cell}
import gurobipy as gp
from gurobipy import GRB
from math import sqrt
import gurobipy_pandas as gppd
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
```

Import (normalized) historical return data using pandas

```{code-cell}
data = pd.read_csv('data/portfolio.csv', index_col=0)
```

Create a new model and add a variable for each stock. The columns in our dataframe correspond to stocks, so the columns can be used directly (as a pandas index) to construct the necessary variable.

```{code-cell}
model = gp.Model('Portfolio')
stocks = gppd.add_vars(model, data.columns, name="Stock")
model.update()
stocks
```

Objective is to minimize risk (squared).  This is modeled using the covariance matrix, which measures the historical correlation between stocks.

```{code-cell}
sigma = data.cov()
portfolio_risk = sigma.dot(stocks).dot(stocks)
model.setObjective(portfolio_risk, GRB.MINIMIZE)
```

Fix budget with a constraint. For summation over series, we get back just a single expression, so this constraint is added directly to the model (not through the accessors).

```{code-cell}
model.addConstr(stocks.sum() == 1, name='budget');
```

Optimize model to find the minimum risk portfolio.

```{code-cell}
model.optimize()
```

Display the minimum risk portfolio.

```{code-cell}
stocks.gppd.X.round(3)
```

Key metrics

```{code-cell}
minrisk_volatility = sqrt(portfolio_risk.getValue())
print('\nVolatility      = %g' % minrisk_volatility)

stock_return = data.mean()
portfolio_return = stock_return.dot(stocks)
minrisk_return = portfolio_return.getValue()
print('Expected Return = %g' % minrisk_return)
```

Solve for the efficient frontier by varying the target return (sampling).

One useful point here could be the ability to specify scenarios by mapping onto constraints

```{code-cell}
scenarios = pd.DataFrame(dict(target_return=np.linspace(stock_return.min(), stock_return.max())))
target_return = model.addConstr(portfolio_return == minrisk_return, 'target_return')

model.update()

model.NumScenarios = len(scenarios)
for row in scenarios.itertuples():
    model.Params.ScenarioNumber = row.Index
    target_return.ScenNRHS = row.target_return

model.Params.OutputFlag = 0
model.optimize()

results = []
for row in scenarios.itertuples():
    model.Params.ScenarioNumber = row.Index
    results.append(model.ScenNObjVal)

scenarios = scenarios.assign(ObjVal=pd.Series(results, index=scenarios.index))

scenarios['volatility'] = scenarios['ObjVal'].apply(sqrt)
scenarios.head()
```

```{code-cell}
# Plot volatility versus expected return for individual stocks
stock_volatility = data.std()
ax = plt.gca()
ax.scatter(x=stock_volatility, y=stock_return,
           color='Blue', label='Individual Stocks')
for i, stock in enumerate(stocks.index):
    ax.annotate(stock, (stock_volatility[i], stock_return[i]))

# Plot volatility versus expected return for minimum risk portfolio
ax.scatter(x=minrisk_volatility, y=minrisk_return, color='DarkGreen')
ax.annotate('Minimum\nRisk\nPortfolio', (minrisk_volatility, minrisk_return),
            horizontalalignment='right')

# Plot efficient frontier
scenarios.plot.line(x='volatility', y='target_return', ax=ax, color='DarkGreen')

# Format and display the final plot
ax.axis([0.005, 0.06, -0.02, 0.025])
ax.set_xlabel('Volatility (standard deviation)')
ax.set_ylabel('Expected Return')
ax.legend()
ax.grid()
```
