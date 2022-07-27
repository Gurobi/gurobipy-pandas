import unittest

import numpy as np
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
from pandas.testing import assert_index_equal, assert_series_equal

# import registers the accessors
import gurobipy_pandas  # noqa


class TestBase(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env(params={"LogToConsole": 0})
        self.model = gp.Model(env=self.env)

    def tearDown(self):
        self.model.close()
        self.env.close()


class TestDataFrameAddVars(TestBase):
    def setUp(self):
        super().setUp()
        self.df = pd.DataFrame(
            index=[0, 2, 3],
            data=[
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
                {"a": 5, "b": 6},
            ],
        )

    def test_no_args(self):
        """Adds a series of gp.Var as named column. This should be the
        simplest test we can have; the new column must have a name so
        we always use that + the index for variable naming."""
        result = self.df.grb.pd_add_vars(self.model, "x")
        self.model.update()
        assert_index_equal(result.index, self.df.index)
        self.assertEqual(list(result.columns), ["a", "b", "x"])
        self.assertEqual(list(self.df.columns), ["a", "b"])
        self.assertEqual(result["x"].dtype, object)
        for i, v in zip(result.index, result["x"]):
            self.assertIsInstance(v, gp.Var)
            self.assertEqual(v.VarName, f"x[{i}]")
            self.assertEqual(v.lb, 0.0)
            self.assertEqual(v.obj, 0.0)
            self.assertGreaterEqual(v.ub, GRB.INFINITY)
            self.assertEqual(v.VType, GRB.CONTINUOUS)

    def test_scalar_args(self):
        result = self.df.grb.pd_add_vars(
            self.model, "x", lb=-10, ub=10, obj=2, vtype=GRB.INTEGER
        )
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
            self.assertEqual(v.obj, 2.0)
            self.assertEqual(v.VType, GRB.INTEGER)

    def test_single_index_col(self):
        result = self.df.grb.pd_add_vars(self.model, name="y", index="a")
        self.model.update()
        self.assertEqual(list(result.columns), ["a", "b", "y"])
        for row in result.itertuples():
            self.assertEqual(row.y.VarName, f"y[{row.a}]")

    def test_multiple_index_cols(self):
        result = self.df.grb.pd_add_vars(self.model, name="z", index=["b", "a"])
        self.model.update()
        self.assertEqual(list(result.columns), ["a", "b", "z"])
        for row in result.itertuples():
            self.assertEqual(row.z.VarName, f"z[{row.b},{row.a}]")

    def test_set_bounds_by_column(self):
        result = self.df.grb.pd_add_vars(self.model, name="x", lb="a", ub="b")
        self.model.update()
        for row in result.itertuples():
            self.assertEqual(row.x.lb, row.a)
            self.assertEqual(row.x.ub, row.b)

    def test_set_objective_by_column(self):
        result = self.df.grb.pd_add_vars(self.model, name="x", obj="a")
        self.model.update()
        for row in result.itertuples():
            self.assertEqual(row.x.obj, row.a)

    def test_multiindex(self):
        df = self.df.assign(c=1).set_index(["b", "a"])
        result = df.grb.pd_add_vars(self.model, name="z")
        self.model.update()
        self.assertEqual(list(result.columns), ["c", "z"])
        for row in result.itertuples():
            ind = ",".join(map(str, row.Index))
            self.assertEqual(row.z.VarName, f"z[{ind}]")


class TestSeriesAttributes(TestBase):
    def test_var_get_X(self):
        """Map Var -> X in a series. Use the same name in the result."""
        series = pd.Series(index=list("abc"), data=[1, 2, 3]).astype(float)
        df = series.to_frame(name="value").grb.pd_add_vars(
            self.model, name="x", lb="value", ub="value"
        )
        self.model.optimize()
        solution = df["x"].grb.X
        assert_series_equal(solution, series, check_names=False)
        self.assertEqual(solution.name, "x")

    def test_var_get_bounds(self):
        df = pd.DataFrame(
            data=np.random.randint(0, 10, size=(100, 5)).astype(float),
            columns=list("abcde"),
        ).grb.pd_add_vars(self.model, name="x", lb="a", ub="b")
        self.model.update()
        assert_series_equal(df["x"].grb.lb, df["a"], check_names=False)
        assert_series_equal(df["x"].grb.ub, df["b"], check_names=False)

    def test_linexpr_getValue(self):
        series = pd.Series(index=list("abc"), data=[1, 2, 3]).astype(float)
        df = series.to_frame(name="value").grb.pd_add_vars(
            self.model, name="x", lb="value", ub="value"
        )
        self.model.optimize()
        solution = (df["x"] * 2.0).grb.getValue()
        assert_series_equal(solution, series * 2.0, check_names=False)

    def test_var_set_ub_scalar(self):
        x = pd.RangeIndex(0, 10).grb.pd_add_vars(self.model, name="x")
        x.grb.ub = 1
        self.model.update()
        for i in range(10):
            self.assertEqual(x.loc[i].ub, 1.0)

    def test_var_set_start_series(self):
        x = pd.RangeIndex(0, 10).grb.pd_add_vars(self.model, name="x")
        x.grb.Start = pd.Series(
            index=pd.RangeIndex(5, 10), data=[1, 2, 3, 0, 1]
        ).astype(float)
        self.model.update()
        expected = [GRB.UNDEFINED] * 5 + [1, 2, 3, 0, 1]
        for i, start in enumerate(expected):
            self.assertEqual(x.loc[i].Start, start)


class TestDataFrameAddConstrsByArgs(TestBase):
    def setUp(self):
        super().setUp()
        self.df = pd.DataFrame(
            data=[
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
                {"a": 5, "b": 6},
            ],
        )

    def test_scalar_rhs(self):
        df = self.df.grb.pd_add_vars(self.model, "x")
        result = df.grb.pd_add_constrs(self.model, "x", GRB.EQUAL, 1.0, name="constr")
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
        df = self.df.grb.pd_add_vars(self.model, "x")
        result = df.grb.pd_add_constrs(self.model, 1.0, GRB.EQUAL, "x", name="constr")
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
        df = self.df.grb.pd_add_vars(self.model, "x")
        result = df.grb.pd_add_constrs(
            self.model, "x", GRB.LESS_EQUAL, "b", name="constr"
        )
        self.model.update()
        for entry in result.itertuples():
            self.assertIsInstance(entry.constr, gp.Constr)
            self.assertEqual(entry.constr.sense, GRB.LESS_EQUAL)
            self.assertEqual(entry.constr.rhs, entry.b)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), entry.x)
            self.assertEqual(row.getCoeff(0), 1.0)

    def test_quadratic(self):
        df = self.df.grb.pd_add_vars(self.model, "x")
        df["x2"] = df["x"] * df["x"] + 1
        result = df.grb.pd_add_constrs(
            self.model, "x", GRB.LESS_EQUAL, "x2", name="constr"
        )
        self.model.update()
        for entry in result.itertuples():
            self.assertIsInstance(entry.constr, gp.QConstr)
            self.assertEqual(entry.constr.QCsense, GRB.LESS_EQUAL)
            self.assertEqual(entry.constr.QCrhs, 1.0)
            qcrow = self.model.getQCRow(entry.constr)
            self.assertEqual(qcrow.size(), 1)
            self.assertIs(qcrow.getVar1(0), entry.x)
            self.assertIs(qcrow.getVar2(0), entry.x)
            self.assertEqual(qcrow.getCoeff(0), -1.0)
            le = qcrow.getLinExpr()
            self.assertEqual(le.size(), 1)
            self.assertIs(le.getVar(0), entry.x)
            self.assertEqual(le.getCoeff(0), 1.0)


class TestDataFrameAddConstrsByExpression(TestBase):
    def setUp(self):
        super().setUp()
        self.df = pd.DataFrame(
            data=[
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
                {"a": 5, "b": 6},
            ],
        )

    def test_scalar_rhs(self):
        df = self.df.grb.pd_add_vars(self.model, "x")
        result = df.grb.pd_add_constrs(self.model, "x == 1", name="constr")
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
        df = self.df.grb.pd_add_vars(self.model, "x")
        result = df.grb.pd_add_constrs(self.model, "1 == x", name="constr")
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
        df = self.df.grb.pd_add_vars(self.model, "x")
        result = df.grb.pd_add_constrs(self.model, "x <= b", name="constr")
        self.model.update()
        for entry in result.itertuples():
            self.assertEqual(entry.constr.sense, GRB.LESS_EQUAL)
            self.assertEqual(entry.constr.rhs, entry.b)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), entry.x)
            self.assertEqual(row.getCoeff(0), 1.0)

    def test_expressions(self):
        df = self.df.grb.pd_add_vars(self.model, "x").grb.pd_add_vars(self.model, "y")
        result = df.grb.pd_add_constrs(self.model, "x + b <= 1 - 2*y", name="constr")
        self.model.update()
        self.assertEqual(df.shape, (3, 4))
        self.assertEqual(result.shape, (3, 5))
        for entry in result.itertuples():
            self.assertEqual(entry.constr.sense, GRB.LESS_EQUAL)
            self.assertEqual(entry.constr.rhs, 1 - entry.b)
            self.assertEqual(entry.constr.ConstrName, f"constr[{entry.Index}]")
            row = self.model.getRow(entry.constr)
            self.assertEqual(row.size(), 2)
            self.assertIs(row.getVar(0), entry.x)
            self.assertIs(row.getVar(1), entry.y)
            self.assertEqual(row.getCoeff(0), 1.0)
            self.assertEqual(row.getCoeff(1), 2.0)

    def test_quadratic(self):
        df = self.df.grb.pd_add_vars(self.model, "x")
        result = df.grb.pd_add_constrs(self.model, "x <= x**2 + 1", name="constr")
        self.model.update()
        for entry in result.itertuples():
            self.assertIsInstance(entry.constr, gp.QConstr)
            self.assertEqual(entry.constr.QCsense, GRB.LESS_EQUAL)
            self.assertEqual(entry.constr.QCrhs, 1.0)
            qcrow = self.model.getQCRow(entry.constr)
            self.assertEqual(qcrow.size(), 1)
            self.assertIs(qcrow.getVar1(0), entry.x)
            self.assertIs(qcrow.getVar2(0), entry.x)
            self.assertEqual(qcrow.getCoeff(0), -1.0)
            le = qcrow.getLinExpr()
            self.assertEqual(le.size(), 1)
            self.assertIs(le.getVar(0), entry.x)
            self.assertEqual(le.getCoeff(0), 1.0)


class TestIndexAddVars(TestBase):
    # TODO: Test string indexes (and string columns)

    def test_no_args(self):
        """Create a series of gp.Var with the given index."""
        index = pd.RangeIndex(0, 10, 2)
        x = index.grb.pd_add_vars(self.model)
        self.model.update()
        self.assertIsInstance(x, pd.Series)
        assert_index_equal(x.index, index)
        for i in range(5):
            self.assertIsInstance(x.loc[i * 2], gp.Var)
            self.assertEqual(x.loc[i * 2].VarName, f"C{i}")
            self.assertEqual(x.loc[i * 2].lb, 0.0)
            self.assertGreaterEqual(x.loc[i * 2].ub, GRB.INFINITY)
            self.assertEqual(x.loc[i * 2].VType, GRB.CONTINUOUS)

    def test_single_index_named(self):
        """Use the index for naming if a name is given."""
        index = pd.RangeIndex(0, 10, 2)
        x = index.grb.pd_add_vars(self.model, name="x")
        self.model.update()
        assert_index_equal(x.index, index)
        for i in range(0, 10, 2):
            self.assertEqual(x.loc[i].VarName, f"x[{i}]")
            self.assertEqual(x.loc[i].lb, 0.0)
            self.assertGreaterEqual(x.loc[i].ub, GRB.INFINITY)
            self.assertEqual(x.loc[i].VType, GRB.CONTINUOUS)

    def test_add_vars_scalar_attrs(self):
        index = pd.RangeIndex(0, 10)
        x = index.grb.pd_add_vars(self.model, lb=-10, ub=10, vtype=GRB.INTEGER)
        self.model.update()
        assert_index_equal(x.index, index)
        for i in range(0, 10):
            self.assertEqual(x.loc[i].VarName, f"C{i}")
            self.assertEqual(x.loc[i].lb, -10.0)
            self.assertGreaterEqual(x.loc[i].ub, 10.0)
            self.assertEqual(x.loc[i].VType, GRB.INTEGER)

    def test_add_vars_multiindex(self):
        index = pd.MultiIndex.from_tuples([(0, 1), (1, 0), (2, 2)])
        x = index.grb.pd_add_vars(self.model, name="y")
        self.model.update()
        assert_index_equal(x.index, index)
        self.assertEqual(x.loc[0, 1].VarName, "y[0,1]")
        self.assertEqual(x.loc[1, 0].VarName, "y[1,0]")
        self.assertEqual(x.loc[2, 2].VarName, "y[2,2]")
