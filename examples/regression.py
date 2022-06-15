"""
sklearn style implementation of L1 regression with Lasso regularization

Uses only the accessor implementation
"""

import gurobipy as gp
from gurobipy import GRB

from sklearn import datasets
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

import pdcomfi.accessors


class GurobiL1Regression:
    def __init__(self, alpha):
        self.alpha = alpha

    def fit(self, X_train, y_train):

        # Create model
        model = gp.Model()

        # Create unbounded variables for each column coefficient, and bound
        # magnitudes using additional variables. Keep intercept separate (no
        # regularization weight).
        intercept = model.addVar(lb=-GRB.INFINITY, name="intercept")
        coeffs = (
            X_train.columns.grb.addVars(model, name="coeff", lb=-GRB.INFINITY)
            .to_frame()
            .grb.addVars(model, name="abscoeff", lb=0.0)
            .grb.addConstrs(model, "coeff <= abscoeff", name="poscoeff")
            .grb.addConstrs(model, "coeff >= -abscoeff", name="negcoeff")
        )

        # Create linear relationship
        relation = (X_train * coeffs["coeff"]).sum(axis="columns").to_frame(
            name="MX"
        ) + intercept

        # Add deviation vars and build constraints
        fit = (
            relation.grb.addVars(model, name="U")
            .grb.addVars(model, name="V")
            .join(y_train)
            .grb.addConstrs(model, "target == MX + U - V", name="fit")
        )
        abs_error = fit["U"] + fit["V"]
        mean_abs_error = abs_error.sum() / fit.shape[0]
        regularization = coeffs["abscoeff"].sum()

        # Minimize L1 norm
        model.setObjective(
            mean_abs_error + self.alpha * regularization, sense=GRB.MINIMIZE
        )

        # Optimize
        model.optimize()

        self.intercept_ = intercept.X
        self.coefs_ = coeffs["coeff"].grb.X

    def predict(self, X_test):
        return (X_test * self.coefs_).sum(axis="columns") + self.intercept_


def fit_check(regr):

    # Load the diabetes dataset
    diabetes_X, diabetes_y = datasets.load_diabetes(return_X_y=True, as_frame=True)

    # Split data for fit assessment
    X_train, X_test, y_train, y_test = train_test_split(diabetes_X, diabetes_y)

    # Create and fit parameterised model
    regr.fit(X_train, y_train)
    y_pred = regr.predict(X_test)

    # Assess error
    print()
    print(f"=== {regr.__class__.__name__} ===")
    print("Mean squared error: %.2f" % mean_squared_error(y_test, y_pred))
    print("Mean absolute error: %.2f" % mean_absolute_error(y_test, y_pred))
    print("Coefficient of determination: %.2f" % r2_score(y_test, y_pred))
    print()


if __name__ == "__main__":
    fit_check(GurobiL1Regression(alpha=0.001))
    fit_check(LinearRegression())
