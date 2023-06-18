import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB
from pandas.testing import assert_index_equal, assert_series_equal

import gurobipy_pandas as gppd

from .utils import GurobiModelTestCase


class TestDataFrameAddVars(GurobiModelTestCase):
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
        # Adds a series of gp.Var as named column. This should be the
        # simplest test we can have; the new column must have a name so
        # we always use that + the index for variable naming.
        result = self.df.gppd.add_vars(self.model, name="x")
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
        result = self.df.gppd.add_vars(
            self.model, lb=-10, ub=10, obj=2, vtype=GRB.INTEGER, name="x"
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

    def test_set_bounds_by_column(self):
        result = self.df.gppd.add_vars(self.model, name="x", lb="a", ub="b")
        self.model.update()
        for row in result.itertuples():
            self.assertEqual(row.x.lb, row.a)
            self.assertEqual(row.x.ub, row.b)

    def test_set_objective_by_column(self):
        result = self.df.gppd.add_vars(self.model, name="x", obj="a")
        self.model.update()
        for row in result.itertuples():
            self.assertEqual(row.x.obj, row.a)

    def test_multiindex(self):
        df = self.df.assign(c=1).set_index(["b", "a"])
        result = df.gppd.add_vars(self.model, name="z")
        self.model.update()
        self.assertEqual(list(result.columns), ["c", "z"])
        for row in result.itertuples():
            ind = ",".join(map(str, row.Index))
            self.assertEqual(row.z.VarName, f"z[{ind}]")

    def test_index_formatter(self):
        # Test that the index_formatter argument is passed through and applied.
        # The different variants of the argument are tested lower down, no need
        # to repeat all of that here.
        df = self.df.assign(str1=["a  b", "c*d", "e:f"]).set_index("str1")

        with self.subTest(index_formatter="default"):
            result = df.gppd.add_vars(self.model, name="x")
            self.model.update()
            names = list(result["x"].gppd.VarName)
            self.assertEqual(names, ["x[a_b]", "x[c_d]", "x[e_f]"])

        with self.subTest(index_formatter="disable"):
            result = df.gppd.add_vars(self.model, name="x", index_formatter="disable")
            self.model.update()
            names = list(result["x"].gppd.VarName)
            self.assertEqual(names, ["x[a  b]", "x[c*d]", "x[e:f]"])


class TestSeriesAttributes(GurobiModelTestCase):
    def test_var_get_X(self):
        # Map Var -> X in a series. Use the same name in the result.
        series = pd.Series(index=list("abc"), data=[1, 2, 3]).astype(float)
        df = series.to_frame(name="value").gppd.add_vars(
            self.model, name="x", lb="value", ub="value"
        )
        self.model.optimize()
        solution = df["x"].gppd.X
        assert_series_equal(solution, series, check_names=False)
        self.assertEqual(solution.name, "x")

    def test_var_get_bounds(self):
        df = pd.DataFrame(
            data=np.random.randint(0, 10, size=(100, 5)).astype(float),
            columns=list("abcde"),
        ).gppd.add_vars(self.model, name="x", lb="a", ub="b")
        self.model.update()
        assert_series_equal(df["x"].gppd.lb, df["a"], check_names=False)
        assert_series_equal(df["x"].gppd.ub, df["b"], check_names=False)

    def test_linexpr_get_value(self):
        series = pd.Series(index=list("abc"), data=[1, 2, 3]).astype(float)
        df = series.to_frame(name="value").gppd.add_vars(
            self.model, name="x", lb="value", ub="value"
        )
        self.model.optimize()
        solution = (df["x"] * 2.0).gppd.get_value()
        assert_series_equal(solution, series * 2.0, check_names=False)

    def test_var_set_ub_scalar(self):
        index = pd.RangeIndex(0, 10)
        x = gppd.add_vars(self.model, index, name="x")
        x.gppd.ub = 1
        self.model.update()
        for i in index:
            self.assertEqual(x.loc[i].ub, 1.0)

    def test_var_set_start_series(self):
        x = gppd.add_vars(self.model, pd.RangeIndex(0, 10), name="x")
        mip_start = pd.Series(index=pd.RangeIndex(5, 10), data=[1, 2, 3, 0, 1]).astype(
            float
        )
        # Require exact alignment to set attribute, so we need to
        # index into the variable series first.
        x.loc[mip_start.index].gppd.Start = mip_start
        self.model.update()
        expected = [GRB.UNDEFINED] * 5 + [1, 2, 3, 0, 1]
        for i, start in enumerate(expected):
            self.assertEqual(x.loc[i].Start, start)

    def test_setattr_series_mismatch(self):
        x = gppd.add_vars(self.model, pd.RangeIndex(5))
        self.model.update()

        # Missing entries for some values in the index
        ub = pd.Series(index=pd.RangeIndex(1, 4), data=[1, 2, 3])
        with self.assertRaises(KeyError):
            x.gppd.UB = ub

        # Too many values (require exact alignment)
        lb = pd.Series(index=pd.RangeIndex(6), data=list(range(6)))
        with self.assertRaisesRegex(KeyError, "'LB' series not aligned with index"):
            x.gppd.LB = lb

    def test_setattr_series_missing_values(self):
        index = pd.RangeIndex(5)
        x = gppd.add_vars(self.model, index)
        self.model.update()

        # Missing data (series must be complete if on the same index)
        obj = pd.Series(index=index, data=[1, 2, None, 4, None])
        with self.assertRaisesRegex(ValueError, "'Obj' series has missing values"):
            x.gppd.Obj = obj

    def test_var_set_obj_index_mismatch(self):
        # Old example that we want to error our
        items = pd.Index([1, 2, 3, 4, 5], name="item")
        knapsacks = pd.Index([1, 2], name="knapsack")
        item_data = pd.DataFrame(
            index=items,
            data={
                "weight": [1.0, 1.5, 1.2, 0.9, 0.7],
                "value": [0.5, 1.2, 0.3, 0.7, 0.9],
            },
        )

        x = gppd.add_vars(self.model, pd.MultiIndex.from_product([items, knapsacks]))
        self.model.update()

        with self.assertRaises(KeyError):
            # Attempts to align a multi-index with a single index. The accessor
            # should complain of the mismatch.
            x.gppd.Obj = item_data["value"]

    def test_setattr_dataframe(self):
        # Must be a scalar or series, not a dataframe
        index = pd.RangeIndex(5)
        x = gppd.add_vars(self.model, index)
        self.model.update()

        with self.assertRaises(TypeError):
            x.gppd.Start = pd.DataFrame(index=index, data={"start": [1, 2, 3, 4, 5]})


class TestSeriesGetAttrSetAttr(GurobiModelTestCase):
    def test_var_getattr_X(self):
        # Map Var -> X in a series. Use the same name in the result.
        series = pd.Series(index=list("abc"), data=[1, 2, 3]).astype(float)
        df = series.to_frame(name="value").gppd.add_vars(
            self.model, name="x", lb="value", ub="value"
        )
        self.model.optimize()
        solution = df["x"].gppd.get_attr("X")
        assert_series_equal(solution, series, check_names=False)
        self.assertEqual(solution.name, "x")

    def test_var_setattr_bounds(self):
        index = pd.RangeIndex(5, 10)
        x = gppd.add_vars(self.model, index, name="x")
        lb = 1.0
        ub = pd.Series(index=index, data=[2.0, 3.0, 4.0, 5.0, 6.0])
        result = x.gppd.set_attr("LB", lb).gppd.set_attr("UB", ub)
        self.model.update()
        for i in range(5):
            self.assertEqual(result.loc[i + 5].lb, 1.0)
            self.assertEqual(result.loc[i + 5].ub, i + 2)

    def test_setattr_series_mismatch(self):
        x = gppd.add_vars(self.model, pd.RangeIndex(5))
        self.model.update()

        # Missing entries for some values in the index
        ub = pd.Series(index=pd.RangeIndex(1, 4), data=[1, 2, 3])
        with self.assertRaises(KeyError):
            x.gppd.set_attr("UB", ub)

        # Too many values (require exact alignment)
        lb = pd.Series(index=pd.RangeIndex(6), data=list(range(6)))
        with self.assertRaises(KeyError):
            x.gppd.set_attr("LB", lb)

    def test_setattr_series_missing_values(self):
        index = pd.RangeIndex(5)
        x = gppd.add_vars(self.model, index)
        self.model.update()

        # Missing data (series must be complete if on the same index)
        obj = pd.Series(index=index, data=[1, 2, None, 4, None])
        with self.assertRaisesRegex(ValueError, "'Obj' series has missing values"):
            x.gppd.set_attr("Obj", obj)

    def test_var_set_obj_index_mismatch(self):
        # Old example that we want to error our
        items = pd.Index([1, 2, 3, 4, 5], name="item")
        knapsacks = pd.Index([1, 2], name="knapsack")
        item_data = pd.DataFrame(
            index=items,
            data={
                "weight": [1.0, 1.5, 1.2, 0.9, 0.7],
                "value": [0.5, 1.2, 0.3, 0.7, 0.9],
            },
        )

        x = gppd.add_vars(self.model, pd.MultiIndex.from_product([items, knapsacks]))
        self.model.update()

        with self.assertRaisesRegex(KeyError, "'Obj' series not aligned with index"):
            # Attempts to align a multi-index with a single index. The accessor
            # should complain of the mismatch.
            x.gppd.set_attr("Obj", item_data["value"])

    def test_setattr_dataframe(self):
        # Must be a scalar or series, not a dataframe
        index = pd.RangeIndex(5)
        x = gppd.add_vars(self.model, index)
        self.model.update()

        with self.assertRaises(TypeError):
            x.gppd.set_attr(
                "Start", pd.DataFrame(index=index, data={"start": [1, 2, 3, 4, 5]})
            )


class TestDataFrameAddConstrsByArgs(GurobiModelTestCase):
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
        df = self.df.gppd.add_vars(self.model, name="x")
        result = df.gppd.add_constrs(self.model, "x", GRB.EQUAL, 1.0, name="constr")
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
        df = self.df.gppd.add_vars(self.model, name="x")
        result = df.gppd.add_constrs(self.model, 1.0, GRB.EQUAL, "x", name="constr")
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
        df = self.df.gppd.add_vars(self.model, name="x")
        result = df.gppd.add_constrs(
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
        df = self.df.gppd.add_vars(self.model, name="x")
        df["x2"] = df["x"] * df["x"] + 1
        result = df.gppd.add_constrs(
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

    def test_index_formatter(self):
        index = pd.Index(["a  b", "c*d", "e:f"])

        df = pd.DataFrame(index=index).gppd.add_vars(self.model, name="x")

        with self.subTest(index_formatter="default"):
            result = df.gppd.add_constrs(self.model, "x", GRB.EQUAL, 1, name="c")
            self.model.update()
            names = list(result["c"].gppd.ConstrName)
            self.assertEqual(names, ["c[a_b]", "c[c_d]", "c[e_f]"])

        with self.subTest(index_formatter="disable"):
            result = df.gppd.add_constrs(
                self.model, "x", GRB.EQUAL, 1, name="c", index_formatter="disable"
            )
            self.model.update()
            names = list(result["c"].gppd.ConstrName)
            self.assertEqual(names, ["c[a  b]", "c[c*d]", "c[e:f]"])

        with self.subTest(index_formatter="callable"):
            index_map = lambda ind: ind.map({"a  b": 2, "c*d": 4, "e:f": 8})
            result = df.gppd.add_constrs(
                self.model, "x", GRB.EQUAL, 1, name="c", index_formatter=index_map
            )
            self.model.update()
            names = list(result["c"].gppd.ConstrName)
            self.assertEqual(names, ["c[2]", "c[4]", "c[8]"])

    def test_nonpython_columnnames(self):
        # Create a column with a name not admissible as a python variable name,
        # check we can still reference it without issues (itertuples is used
        # as a fast iterator for constraint generation, so such edge cases
        # can fail if looking up by attribute names).
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}).gppd.add_vars(
            self.model, name="ab cd"
        )

        result = df.gppd.add_constrs(self.model, "ab cd", GRB.EQUAL, 2, name="c")

        self.model.update()
        for ind in df.index:
            constr = result.loc[ind, "c"]
            self.assertIsInstance(constr, gp.Constr)
            self.assertEqual(constr.Sense, GRB.EQUAL)
            self.assertEqual(constr.RHS, 2.0)
            row = self.model.getRow(constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), df.loc[ind, "ab cd"])
            self.assertEqual(row.getCoeff(0), 1.0)


class TestDataFrameAddConstrsByExpression(GurobiModelTestCase):
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
        df = self.df.gppd.add_vars(self.model, name="x")
        result = df.gppd.add_constrs(self.model, "x == 1", name="constr")
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
        df = self.df.gppd.add_vars(self.model, name="x")
        result = df.gppd.add_constrs(self.model, "1 == x", name="constr")
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
        df = self.df.gppd.add_vars(self.model, name="x")
        result = df.gppd.add_constrs(self.model, "x <= b", name="constr")
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
        df = self.df.gppd.add_vars(self.model, name="x").gppd.add_vars(
            self.model, name="y"
        )
        result = df.gppd.add_constrs(self.model, "x + b <= 1 - 2*y", name="constr")
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
        df = self.df.gppd.add_vars(self.model, name="x")
        result = df.gppd.add_constrs(self.model, "x <= x**2 + 1", name="constr")
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

    def test_multiindex_names(self):
        df = pd.DataFrame(
            index=pd.MultiIndex.from_product([pd.RangeIndex(2), pd.RangeIndex(2)])
        ).gppd.add_vars(self.model, name="x")
        df = df.gppd.add_constrs(self.model, "x <= 2", name="c1")
        self.model.update()

        names = df["c1"].gppd.get_attr("ConstrName")
        expected = pd.Series(
            index=pd.MultiIndex.from_product([[0, 1], [0, 1]]),
            data=["c1[0,0]", "c1[0,1]", "c1[1,0]", "c1[1,1]"],
            name="c1",
        )

        assert_series_equal(names, expected)

    def test_index_formatter(self):
        index = pd.Index(["a  b", "c*d", "e:f"])

        df = pd.DataFrame(index=index).gppd.add_vars(self.model, name="x")

        with self.subTest(index_formatter="default"):
            result = df.gppd.add_constrs(self.model, "x <= 1", name="c")
            self.model.update()
            names = list(result["c"].gppd.ConstrName)
            self.assertEqual(names, ["c[a_b]", "c[c_d]", "c[e_f]"])

        with self.subTest(index_formatter="disable"):
            result = df.gppd.add_constrs(
                self.model, "x <= 1", name="c", index_formatter="disable"
            )
            self.model.update()
            names = list(result["c"].gppd.ConstrName)
            self.assertEqual(names, ["c[a  b]", "c[c*d]", "c[e:f]"])

        with self.subTest(index_formatter="callable"):
            index_map = lambda ind: ind.map({"a  b": 2, "c*d": 4, "e:f": 8})
            result = df.gppd.add_constrs(
                self.model, "x <= 1", name="c", index_formatter=index_map
            )
            self.model.update()
            names = list(result["c"].gppd.ConstrName)
            self.assertEqual(names, ["c[2]", "c[4]", "c[8]"])

    def test_nonpython_columnnames(self):
        # Create a column with a name not admissible as a python variable name,
        # check we can still use it with pd.DataFrame.eval backtick style.

        df = pd.DataFrame({"a:b": [1, 2, 3], "b@d": [4, 5, 6]}).gppd.add_vars(
            self.model, name="ab cd"
        )

        # For the record: pandas eval can handle this (only for numeric types)
        result = df.eval("`a:b` + `b@d`")
        assert_series_equal(result, pd.Series([5, 7, 9]))

        result = df.gppd.add_constrs(self.model, "`ab cd` >= `a:b` + `b@d`", name="c")

        # For reference, same result via direct columns
        # result = (
        #     df.assign(tmp=lambda data: data.eval("`a:b` + `b@d`"))
        #     .gppd.add_constrs(self.model, "ab cd", GRB.GREATER_EQUAL, "tmp", name="c")
        # )

        self.model.update()
        for ind, rhs in zip(df.index, [5.0, 7.0, 9.0]):
            constr = result.loc[ind, "c"]
            self.assertIsInstance(constr, gp.Constr)
            self.assertEqual(constr.Sense, GRB.GREATER_EQUAL)
            self.assertEqual(constr.RHS, rhs)
            row = self.model.getRow(constr)
            self.assertEqual(row.size(), 1)
            self.assertIs(row.getVar(0), df.loc[ind, "ab cd"])
            self.assertEqual(row.getCoeff(0), 1.0)


class TestSeriesCaseError(GurobiModelTestCase):
    def test_get_attr(self):
        x = gppd.add_vars(self.model, pd.RangeIndex(5))
        self.model.update()
        msg = ".*no attribute 'getAttr'. Did you mean: 'get_attr'"
        with self.assertRaisesRegex(AttributeError, msg):
            x.gppd.getAttr("UB")

    def test_set_attr(self):
        x = gppd.add_vars(self.model, pd.RangeIndex(5))
        self.model.update()
        msg = ".*no attribute 'setAttr'. Did you mean: 'set_attr'"
        with self.assertRaisesRegex(AttributeError, msg):
            x.gppd.setAttr("Obj", [1, 2, 3, 4, 5])

    def test_get_value(self):
        x = gppd.add_vars(self.model, pd.RangeIndex(5))
        expr = x + 2
        self.model.optimize()
        msg = ".*no attribute 'getValue'. Did you mean: 'get_value'"
        with self.assertRaisesRegex(AttributeError, msg):
            expr.gppd.getValue()
