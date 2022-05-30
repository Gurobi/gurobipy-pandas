import unittest

import gurobipy as gp
from gurobipy import GRB
import pandas as pd
from pandas.testing import assert_index_equal

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
