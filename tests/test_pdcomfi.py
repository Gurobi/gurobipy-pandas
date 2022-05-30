import unittest

import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
from pandas.testing import assert_index_equal, assert_series_equal

import pdcomfi  # import registers the accessors


class TestDataFrameAddVars(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)
        self.df = pd.DataFrame(
            index=[0, 2, 3],
            data=[
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
                {"a": 5, "b": 6},
            ],
        )

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_add_vars_no_args(self):
        """Adds a series of gp.Var as named column. This should be the
        simplest test we can have; the new column must have a name so
        we always use that + the index for variable naming."""
        result = self.df.grb.addVars(self.model, "x")
        self.model.update()
        assert_index_equal(result.index, self.df.index)
        self.assertEqual(list(result.columns), ["a", "b", "x"])
        self.assertEqual(list(self.df.columns), ["a", "b"])
        self.assertEqual(result["x"].dtype, object)
        for i, v in zip(result.index, result["x"]):
            self.assertIsInstance(v, gp.Var)
            self.assertEqual(v.VarName, f"x[{i}]")
            self.assertEqual(v.lb, 0.0)
            self.assertGreaterEqual(v.ub, GRB.INFINITY)
            self.assertEqual(v.VType, GRB.CONTINUOUS)

    def test_add_vars_scalar_args(self):
        result = self.df.grb.addVars(self.model, "x", lb=-10, ub=10, vtype=GRB.INTEGER)
        self.model.update()
        assert_index_equal(result.index, self.df.index)
        self.assertEqual(list(result.columns), ["a", "b", "x"])
        self.assertEqual(list(self.df.columns), ["a", "b"])
        self.assertEqual(result["x"].dtype, object)
        for i, v in zip(result.index, result["x"]):
            self.assertIsInstance(v, gp.Var)
            self.assertEqual(v.VarName, f"x[{i}]")
            self.assertEqual(v.lb, -10.0)
            self.assertEqual(v.ub, 10.0)
            self.assertEqual(v.VType, GRB.INTEGER)

    def test_add_vars_single_index_col(self):
        result = self.df.grb.addVars(self.model, name="y", index="a")
        self.model.update()
        self.assertEqual(list(result.columns), ["a", "b", "y"])
        for row in result.itertuples():
            self.assertEqual(row.y.VarName, f"y[{row.a}]")

    def test_add_vars_multiple_index_cols(self):
        result = self.df.grb.addVars(self.model, name="z", index=["b", "a"])
        self.model.update()
        self.assertEqual(list(result.columns), ["a", "b", "z"])
        for row in result.itertuples():
            self.assertEqual(row.z.VarName, f"z[{row.b},{row.a}]")

    def test_add_vars_set_bounds_by_column(self):
        result = self.df.grb.addVars(self.model, name="x", lb="a", ub="b")
        self.model.update()
        for row in result.itertuples():
            self.assertEqual(row.x.lb, row.a)
            self.assertEqual(row.x.ub, row.b)


class TestSeriesAccessors(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_var_X(self):
        """Map Var -> X in a series. Use the same name in the result."""
        series = pd.Series(index=list("abc"), data=[1, 2, 3]).astype(float)
        df = series.to_frame(name="value").grb.addVars(
            self.model, name="x", lb="value", ub="value"
        )
        self.model.optimize()
        solution = df["x"].grb.X
        assert_series_equal(solution, series, check_names=False)
        self.assertEqual(solution.name, "x")

    def test_var_bounds(self):
        df = pd.DataFrame(
            data=np.random.randint(0, 10, size=(100, 5)).astype(float),
            columns=list("abcde"),
        ).grb.addVars(self.model, name="x", lb="a", ub="b")
        self.model.update()
        assert_series_equal(df["x"].grb.lb, df["a"], check_names=False)
        assert_series_equal(df["x"].grb.ub, df["b"], check_names=False)

    def test_getValue(self):
        series = pd.Series(index=list("abc"), data=[1, 2, 3]).astype(float)
        df = series.to_frame(name="value").grb.addVars(
            self.model, name="x", lb="value", ub="value"
        )
        self.model.optimize()
        solution = (df["x"] * 2.0).grb.getValue()
        assert_series_equal(solution, series * 2.0, check_names=False)


class TestDataFrameAddLConstrs(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)
        self.df = pd.DataFrame(
            data=[
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
                {"a": 5, "b": 6},
            ],
        )

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_scalar_rhs(self):
        df = self.df.grb.addVars(self.model, "x")
        result = df.grb.addLConstrs(self.model, "x", GRB.EQUAL, 1.0, name="constr")
        self.model.update()
        for entry in result.itertuples():
            self.assertEqual(entry.constr.sense, GRB.EQUAL)
            self.assertEqual(entry.constr.rhs, 1.0)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), entry.x)
            self.assertEqual(row.getCoeff(0), 1.0)

    def test_scalar_lhs(self):
        df = self.df.grb.addVars(self.model, "x")
        result = df.grb.addLConstrs(self.model, 1.0, GRB.EQUAL, "x", name="constr")
        self.model.update()
        for entry in result.itertuples():
            self.assertEqual(entry.constr.sense, GRB.EQUAL)
            self.assertEqual(entry.constr.rhs, -1.0)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), entry.x)
            self.assertEqual(row.getCoeff(0), -1.0)

    def test_series_rhs(self):
        df = self.df.grb.addVars(self.model, "x")
        result = df.grb.addLConstrs(self.model, "x", GRB.LESS_EQUAL, "b", name="constr")
        self.model.update()
        for entry in result.itertuples():
            self.assertEqual(entry.constr.sense, GRB.LESS_EQUAL),
            self.assertEqual(entry.constr.rhs, entry.b)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), entry.x)
            self.assertEqual(row.getCoeff(0), 1.0)


class TestDataFrameAddConstrs(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)
        self.df = pd.DataFrame(
            data=[
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
                {"a": 5, "b": 6},
            ],
        )

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_scalar_rhs(self):
        df = self.df.grb.addVars(self.model, "x")
        result = df.grb.addConstrs(self.model, "x == 1", name="constr")
        self.model.update()
        for entry in result.itertuples():
            self.assertEqual(entry.constr.sense, GRB.EQUAL)
            self.assertEqual(entry.constr.rhs, 1.0)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), entry.x)
            self.assertEqual(row.getCoeff(0), 1.0)

    def test_scalar_lhs(self):
        df = self.df.grb.addVars(self.model, "x")
        result = df.grb.addConstrs(self.model, "1 == x", name="constr")
        self.model.update()
        for entry in result.itertuples():
            self.assertEqual(entry.constr.sense, GRB.EQUAL)
            self.assertEqual(entry.constr.rhs, -1.0)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), entry.x)
            self.assertEqual(row.getCoeff(0), -1.0)

    def test_series_rhs(self):
        df = self.df.grb.addVars(self.model, "x")
        result = df.grb.addConstrs(self.model, "x <= b", name="constr")
        self.model.update()
        for entry in result.itertuples():
            self.assertEqual(entry.constr.sense, GRB.LESS_EQUAL)
            self.assertEqual(entry.constr.rhs, entry.b)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), entry.x)
            self.assertEqual(row.getCoeff(0), 1.0)
