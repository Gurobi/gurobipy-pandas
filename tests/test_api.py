"""
Tests for the public API. These are intentionally simple, more careful
tests of data types, errors, etc, are done on the lower-level functions.
"""

import math
import unittest

import gurobipy as gp
import pandas as pd
from gurobipy import GRB
from pandas.testing import assert_index_equal, assert_series_equal

import gurobipy_pandas as gppd
from tests.utils import GurobiModelTestCase

GUROBIPY_MAJOR_VERSION, *_ = gp.gurobi.version()


class TestAddVars(GurobiModelTestCase):
    def test_from_dataframe(self):
        data = pd.DataFrame(
            {
                "source": [1, 2, 1, 0],
                "sink": [0, 1, 3, 2],
                "capacity": [0.3, 1.2, 0.7, 0.9],
                "cost": [1.3, 1.7, 1.4, 1.1],
            }
        ).set_index(["source", "sink"])

        flow = gppd.add_vars(self.model, data, name="flow", obj="cost", ub="capacity")

        # Necessary variables registered on the model
        self.model.update()
        self.assertEqual(self.model.NumVars, 4)

        # Correctly structured series
        self.assertIsInstance(flow, pd.Series)
        self.assertEqual(flow.name, "flow")
        assert_index_equal(flow.index, data.index)

        # Names/types are correct and match the index (checking individual objects)
        for (source, sink), flowvar in flow.items():
            self.assertEqual(flowvar.VarName, f"flow[{source},{sink}]")
            self.assertEqual(flowvar.VType, GRB.CONTINUOUS)

        # Attributes are correct, using the series accessors to validate
        self.assertTrue((flow.gppd.LB == 0).all())
        assert_series_equal(flow.gppd.UB, data["capacity"], check_names=False)
        assert_series_equal(flow.gppd.Obj, data["cost"], check_names=False)

    def test_from_series(self):
        series = pd.Series(index=pd.RangeIndex(5), data=[1, 2, 3, 4, 5])

        x = gppd.add_vars(self.model, series, name="x", vtype="B")

        # Necessary variables registered on the model
        self.model.update()
        self.assertEqual(self.model.NumVars, 5)

        # Correctly structured series
        self.assertIsInstance(x, pd.Series)
        self.assertEqual(x.name, "x")
        assert_index_equal(x.index, series.index)

        # Names/types are correct and match the index (checking individual objects)
        for index, variable in x.items():
            self.assertEqual(variable.VarName, f"x[{index}]")
            self.assertEqual(variable.VType, GRB.BINARY)

        # Attributes are correct, using the series accessors to validate
        self.assertTrue((x.gppd.LB == 0.0).all())
        self.assertTrue((x.gppd.UB == 1.0).all())
        self.assertTrue((x.gppd.Obj == 0.0).all())

    def test_from_index(self):
        index = pd.RangeIndex(5)
        objseries = pd.Series(index=index, data=[1, 2, 3, 4, 5], dtype=float)

        x = gppd.add_vars(self.model, index, name="x", obj=objseries)

        # Necessary variables registered on the model
        self.model.update()
        self.assertEqual(self.model.NumVars, 5)

        # Correctly structured series
        self.assertIsInstance(x, pd.Series)
        self.assertEqual(x.name, "x")
        assert_index_equal(x.index, index)

        # Names/types are correct and match the index (checking individual objects)
        for ind, variable in x.items():
            self.assertEqual(variable.VarName, f"x[{ind}]")
            self.assertEqual(variable.VType, GRB.CONTINUOUS)

        # Attributes are correct, using the series accessors to validate
        self.assertTrue((x.gppd.LB == 0.0).all())
        self.assertTrue((x.gppd.UB >= 1e100).all())
        assert_series_equal(x.gppd.Obj, objseries, check_names=False)

    def test_names_1(self):
        # Default name sanitization
        index = pd.Index(["a  b", "c^d", "e+f"])
        expect_names = ["x[a_b]", "x[c_d]", "x[e_f]"]

        with self.subTest(obj="index"):
            x = gppd.add_vars(self.model, index, name="x")
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)

        with self.subTest(obj="series"):
            x = gppd.add_vars(
                self.model, pd.Series(index=index, data=[1, 2, 3]), name="x"
            )
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)

        with self.subTest(obj="dataframe"):
            x = gppd.add_vars(
                self.model, pd.DataFrame(index=index, data={"a": [1, 2, 3]}), name="x"
            )
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)

    def test_names_2(self):
        # Disable name sanitization
        index = pd.Index(["a  b", "c^d", "e+f"])
        expect_names = ["x[a  b]", "x[c^d]", "x[e+f]"]

        with self.subTest(obj="index"):
            x = gppd.add_vars(self.model, index, name="x", index_formatter="disable")
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)

        with self.subTest(obj="series"):
            x = gppd.add_vars(
                self.model,
                pd.Series(index=index, data=[1, 2, 3]),
                name="x",
                index_formatter="disable",
            )
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)

        with self.subTest(obj="dataframe"):
            x = gppd.add_vars(
                self.model,
                pd.DataFrame(index=index, data={"a": [1, 2, 3]}),
                name="x",
                index_formatter="disable",
            )
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)

    def test_names_3(self):
        # User provided formatter
        index = pd.Index(["a  b", "c^d", "e+f"])
        simple_mapping = {"a  b": 1, "c^d": 4, "e+f": 9}
        formatter = lambda index: index.map(simple_mapping)
        expect_names = ["x[1]", "x[4]", "x[9]"]

        with self.subTest(obj="index"):
            x = gppd.add_vars(self.model, index, name="x", index_formatter=formatter)
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)

        with self.subTest(obj="series"):
            x = gppd.add_vars(
                self.model,
                pd.Series(index=index, data=[1, 2, 3]),
                name="x",
                index_formatter=formatter,
            )
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)

        with self.subTest(obj="dataframe"):
            x = gppd.add_vars(
                self.model,
                pd.DataFrame(index=index, data={"a": [1, 2, 3]}),
                name="x",
                index_formatter=formatter,
            )
            self.model.update()
            for ind, name in zip(index, expect_names):
                self.assertEqual(x[ind].VarName, name)


class TestAddConstrs(GurobiModelTestCase):
    def test_from_series(self):
        index = pd.RangeIndex(10)

        x = gppd.add_vars(self.model, index, name="x")
        y = gppd.add_vars(self.model, index, name="y")
        k = pd.Series(index=index, data=range(10, 20))

        constrs = gppd.add_constrs(
            self.model, 2 * x + y, GRB.LESS_EQUAL, k, name="cons"
        )

        # Correct model metadata
        self.model.update()
        self.assertEqual(self.model.NumVars, 20)
        self.assertEqual(self.model.NumConstrs, 10)

        # Check return values
        self.assertIsInstance(constrs, pd.Series)
        self.assertEqual(constrs.name, "cons")
        assert_index_equal(constrs.index, index)

        # Constraint data per object
        for ind, constr in constrs.items():
            self.assertEqual(constr.ConstrName, f"cons[{ind}]")
            self.assert_linexpr_equal(self.model.getRow(constr), 2 * x[ind] + y[ind])

        # Check data using accessors
        self.assertTrue((constrs.gppd.Sense == GRB.LESS_EQUAL).all())
        assert_series_equal(constrs.gppd.RHS, k.astype(float), check_names=False)

    def test_index_formatter(self):
        index = pd.Index(["a  b", "c*d", "e:f"])

        x = gppd.add_vars(self.model, index)
        y = gppd.add_vars(self.model, index)

        with self.subTest(index_formatter="default"):
            constrs = gppd.add_constrs(self.model, x, GRB.LESS_EQUAL, y, name="c")
            self.model.update()
            names = list(constrs.gppd.ConstrName)
            self.assertEqual(names, ["c[a_b]", "c[c_d]", "c[e_f]"])

        with self.subTest(index_formatter="disable"):
            constrs = gppd.add_constrs(
                self.model, x, GRB.LESS_EQUAL, y, name="c", index_formatter="disable"
            )
            self.model.update()
            names = list(constrs.gppd.ConstrName)
            self.assertEqual(names, ["c[a  b]", "c[c*d]", "c[e:f]"])

        with self.subTest(index_formatter="callable"):
            index_map = lambda ind: ind.map({"a  b": 2, "c*d": 4, "e:f": 8})
            constrs = gppd.add_constrs(
                self.model, x, GRB.LESS_EQUAL, y, name="c", index_formatter=index_map
            )
            self.model.update()
            names = list(constrs.gppd.ConstrName)
            self.assertEqual(names, ["c[2]", "c[4]", "c[8]"])

    def test_sense_series(self):
        index = pd.Index(["a", "e", "g"])

        x = gppd.add_vars(self.model, index, name="x")
        y = gppd.add_vars(self.model, index, name="y")
        sense = pd.Series(index=index, data=["<=", ">", "="])

        constrs = gppd.add_constrs(self.model, 2 * x + 1, sense, y)
        self.model.update()

        for ind, sense in zip(
            ["a", "e", "g"], [GRB.LESS_EQUAL, GRB.GREATER_EQUAL, GRB.EQUAL]
        ):
            constr = constrs.loc[ind]
            self.assert_linexpr_equal(
                self.model.getRow(constr), 2 * x.loc[ind] - y.loc[ind]
            )
            self.assertEqual(constr.Sense, sense)
            self.assertEqual(constr.RHS, -1.0)


@unittest.skipIf(
    GUROBIPY_MAJOR_VERSION < 12,
    "Nonlinear constraints are only supported for Gurobi 12 and later",
)
class TestNonlinear(GurobiModelTestCase):
    def assert_approx_equal(self, value, expected, tolerance=1e-6):
        difference = abs(value - expected)
        self.assertLessEqual(difference, tolerance)

    def test_log(self):
        # max sum y_i
        # s.t. y_i = log(x_i)
        #      1.0 <= x <= 2.0
        from gurobipy import nlfunc

        index = pd.RangeIndex(3)
        x = gppd.add_vars(self.model, index, lb=1.0, ub=2.0, name="x")
        y = gppd.add_vars(self.model, index, obj=1.0, name="y")
        self.model.ModelSense = GRB.MAXIMIZE

        gppd.add_constrs(self.model, y, GRB.EQUAL, x.apply(nlfunc.log), name="log_x")

        self.model.optimize()
        self.assert_approx_equal(self.model.ObjVal, 3 * math.log(2.0))

    def test_inequality(self):
        # max  sum x_i
        # s.t. log2(x_i^2 + 1) <= 2.0
        #      0.0 <= x <= 1.0
        #
        # Formulated as
        #
        # max  sum x_i
        # s.t. log2(x_i^2 + 1) == z_i
        #      0.0 <= x <= 1.0
        #      -GRB.INFINITY <= z_i <= 2
        from gurobipy import nlfunc

        index = pd.RangeIndex(3)
        x = gppd.add_vars(self.model, index, name="x")
        z = gppd.add_vars(self.model, index, lb=-GRB.INFINITY, ub=2.0, name="z")
        self.model.setObjective(x.sum(), sense=GRB.MAXIMIZE)

        gppd.add_constrs(self.model, z, GRB.EQUAL, (x**2 + 1).apply(nlfunc.log))

        self.model.optimize()
        self.model.write("model.lp")
        self.model.write("model.sol")

        x_sol = x.gppd.X
        z_sol = z.gppd.X
        for i in range(3):
            self.assert_approx_equal(x_sol[i], math.sqrt(math.exp(2.0) - 1))
            self.assert_approx_equal(z_sol[i], 2.0)

    def test_wrong_usage(self):
        index = pd.RangeIndex(3)
        x = gppd.add_vars(self.model, index, name="x")
        y = gppd.add_vars(self.model, index, name="y")

        with self.assertRaisesRegex(
            gp.GurobiError, "Objective must be linear or quadratic"
        ):
            self.model.setObjective((x / y).sum())

        with self.assertRaisesRegex(
            ValueError, "Nonlinear constraints must be in the form"
        ):
            gppd.add_constrs(self.model, y, GRB.LESS_EQUAL, x**4)

        with self.assertRaisesRegex(
            ValueError, "Nonlinear constraints must be in the form"
        ):
            gppd.add_constrs(self.model, y + x**4, GRB.EQUAL, 1)

        with self.assertRaisesRegex(
            ValueError, "Nonlinear constraints must be in the form"
        ):
            gppd.add_constrs(self.model, y**4, GRB.EQUAL, x)

        with self.assertRaisesRegex(
            ValueError, "Nonlinear constraints must be in the form"
        ):
            x.to_frame().gppd.add_constrs(self.model, "x**3 == 1", name="bad")

    def test_eval(self):
        index = pd.RangeIndex(3)
        df = (
            gppd.add_vars(self.model, index, name="x")
            .to_frame()
            .gppd.add_vars(self.model, name="y")
            .gppd.add_constrs(self.model, "y == x**3", name="nlconstr")
        )

        self.model.update()
        for row in df.itertuples(index=False):
            self.assert_nlconstr_equal(
                row.nlconstr,
                row.y,
                [
                    (GRB.OPCODE_POW, -1.0, -1),
                    (GRB.OPCODE_VARIABLE, row.x, 0),
                    (GRB.OPCODE_CONSTANT, 3.0, 0),
                ],
            )

    def test_frame(self):
        from gurobipy import nlfunc

        index = pd.RangeIndex(3)
        df = (
            gppd.add_vars(self.model, index, name="x")
            .to_frame()
            .gppd.add_vars(self.model, name="y")
            .assign(exp_x=lambda df: df["x"].apply(nlfunc.exp))
            .gppd.add_constrs(self.model, "y", GRB.EQUAL, "exp_x", name="nlconstr")
        )

        self.model.update()
        for row in df.itertuples(index=False):
            self.assert_nlconstr_equal(
                row.nlconstr,
                row.y,
                [
                    (GRB.OPCODE_EXP, -1.0, -1),
                    (GRB.OPCODE_VARIABLE, row.x, 0),
                ],
            )


class TestDataValidation(GurobiModelTestCase):
    # Test that we throw some more informative errors, instead of obscure
    # ones from the underlying gurobipy library

    def test_bad_sense_1(self):
        index = pd.Index(["a", "e", "g"])

        x = gppd.add_vars(self.model, index, name="x")
        y = gppd.add_vars(self.model, index, name="y")

        with self.assertRaisesRegex(
            ValueError, "'less' is not a valid constraint sense"
        ):
            gppd.add_constrs(self.model, x, "less", y)

    def test_bad_sense_2(self):
        index = pd.Index(["a", "e", "g"])

        x = gppd.add_vars(self.model, index, name="x")
        y = gppd.add_vars(self.model, index, name="y")
        sense = pd.Series(index=index, data=["<=", "a", "="])

        with self.assertRaisesRegex(ValueError, "'a' is not a valid constraint sense"):
            gppd.add_constrs(self.model, x, sense, y)

    def test_bad_sense_3(self):
        index = pd.Index(["a", "e", "g"])

        x = gppd.add_vars(self.model, index, name="x")
        y = gppd.add_vars(self.model, index, name="y")

        with self.assertRaisesRegex(
            ValueError, "'3.5' is not a valid constraint sense"
        ):
            gppd.add_constrs(self.model, x, 3.5, y)


class TestNonInteractiveMode(GurobiModelTestCase):
    # Check that no updates are run by default.
    # Test all add_vars / add_constrs entry points.

    def test_add_vars_function_index(self):
        gppd.add_vars(self.model, pd.RangeIndex(5))
        self.assertEqual(self.model.NumVars, 0)
        self.model.update()
        self.assertEqual(self.model.NumVars, 5)

    def test_add_vars_function_series(self):
        gppd.add_vars(self.model, pd.Series(list(range(10))))
        self.assertEqual(self.model.NumVars, 0)
        self.model.update()
        self.assertEqual(self.model.NumVars, 10)

    def test_add_vars_function_dataframe(self):
        gppd.add_vars(
            self.model, pd.DataFrame(index=[1, 2], columns=["a", "b"], data=1)
        )
        self.assertEqual(self.model.NumVars, 0)
        self.model.update()
        self.assertEqual(self.model.NumVars, 2)

    def test_add_constrs_function(self):
        x = gppd.add_vars(self.model, pd.RangeIndex(5))
        y = gppd.add_vars(self.model, pd.RangeIndex(5))
        gppd.add_constrs(self.model, x, GRB.EQUAL, y)
        self.assertEqual(self.model.NumConstrs, 0)
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 5)

    def test_add_vars_accessor(self):
        df = pd.DataFrame(index=[1, 2], columns=["a", "b"], data=1)
        df.gppd.add_vars(self.model, name="x")
        self.assertEqual(self.model.NumVars, 0)
        self.model.update()
        self.assertEqual(self.model.NumVars, 2)

    def test_add_constrs_accessor_args(self):
        df = pd.DataFrame(index=[1, 2, 3, 4], columns=["a"], data=1).gppd.add_vars(
            self.model, name="x"
        )
        df.gppd.add_constrs(self.model, "x", GRB.EQUAL, 1.0, name="c")
        self.assertEqual(self.model.NumConstrs, 0)
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 4)

    def test_add_constrs_accessor_expression(self):
        df = pd.DataFrame(index=[1, 2, 3], columns=["a"], data=1).gppd.add_vars(
            self.model, name="x"
        )
        df.gppd.add_constrs(self.model, "x <= 1", name="c")
        self.assertEqual(self.model.NumConstrs, 0)
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 3)


class TestInteractiveMode(GurobiModelTestCase):
    # Check that auto-updates are done when interactive mode is enabled.
    # Test all add_vars / add_constrs entry points; changes should immediately
    # be visible in the model.

    def setUp(self):
        super().setUp()
        gppd.set_interactive()

    def tearDown(self):
        gppd.set_interactive(False)
        super().tearDown()

    def test_add_vars_function_index(self):
        gppd.add_vars(self.model, pd.RangeIndex(5))
        self.assertEqual(self.model.NumVars, 5)

    def test_add_vars_function_series(self):
        gppd.add_vars(self.model, pd.Series(list(range(10))))
        self.assertEqual(self.model.NumVars, 10)

    def test_add_vars_function_dataframe(self):
        gppd.add_vars(
            self.model, pd.DataFrame(index=[1, 2], columns=["a", "b"], data=1)
        )
        self.assertEqual(self.model.NumVars, 2)

    def test_add_constrs_function(self):
        x = gppd.add_vars(self.model, pd.RangeIndex(5))
        y = gppd.add_vars(self.model, pd.RangeIndex(5))
        gppd.add_constrs(self.model, x, GRB.EQUAL, y)
        self.assertEqual(self.model.NumConstrs, 5)

    def test_add_vars_accessor(self):
        df = pd.DataFrame(index=[1, 2], columns=["a", "b"], data=1)
        df.gppd.add_vars(self.model, name="x")
        self.assertEqual(self.model.NumVars, 2)

    def test_add_constrs_accessor_args(self):
        df = pd.DataFrame(index=[1, 2, 3, 4], columns=["a"], data=1).gppd.add_vars(
            self.model, name="x"
        )
        df.gppd.add_constrs(self.model, "x", GRB.EQUAL, 1.0, name="c")
        self.assertEqual(self.model.NumConstrs, 4)

    def test_add_constrs_accessor_expression(self):
        df = pd.DataFrame(index=[1, 2, 3], columns=["a"], data=1).gppd.add_vars(
            self.model, name="x"
        )
        df.gppd.add_constrs(self.model, "x <= 1", name="c")
        self.assertEqual(self.model.NumConstrs, 3)
