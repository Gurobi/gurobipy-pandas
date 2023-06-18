"""
Tests for the public API. These are intentionally simple, more careful
tests of data types, errors, etc, are done on the lower-level functions.
"""

import pandas as pd
from gurobipy import GRB
from pandas.testing import assert_index_equal, assert_series_equal

import gurobipy_pandas as gppd
from tests.utils import GurobiModelTestCase


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
