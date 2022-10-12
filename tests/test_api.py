"""
Tests for the public API. These are intentionally simple, more careful
tests of data types, errors, etc, are done on the lower-level functions.
"""

import unittest

import pandas as pd
from pandas.testing import assert_index_equal, assert_series_equal
import gurobipy as gp
from gurobipy import GRB
from gurobipy_pandas import pd_add_vars


class TestPDAddVars(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_from_dataframe(self):

        data = pd.DataFrame(
            {
                "source": [1, 2, 1, 0],
                "sink": [0, 1, 3, 2],
                "capacity": [0.3, 1.2, 0.7, 0.9],
                "cost": [1.3, 1.7, 1.4, 1.1],
            }
        ).set_index(["source", "sink"])

        flow = pd_add_vars(self.model, data, name="flow", obj="cost", ub="capacity")

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
        self.assertTrue((flow.grb.LB == 0).all())
        assert_series_equal(flow.grb.UB, data["capacity"], check_names=False)
        assert_series_equal(flow.grb.Obj, data["cost"], check_names=False)

    def test_from_series(self):

        series = pd.Series(index=pd.RangeIndex(5), data=[1, 2, 3, 4, 5])

        x = pd_add_vars(self.model, series, name="x", vtype="B")

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
        self.assertTrue((x.grb.LB == 0.0).all())
        self.assertTrue((x.grb.UB == 1.0).all())
        self.assertTrue((x.grb.Obj == 0.0).all())

    def test_from_index(self):

        index = pd.RangeIndex(5)
        objseries = pd.Series(index=index, data=[1, 2, 3, 4, 5], dtype=float)

        x = pd_add_vars(self.model, index, name="x", obj=objseries)

        # Necessary variables registered on the model
        self.model.update()
        self.assertEqual(self.model.NumVars, 5)

        # Correctly structured series
        self.assertIsInstance(x, pd.Series)
        self.assertEqual(x.name, "x")
        assert_index_equal(x.index, index)

        # Names/types are correct and match the index (checking individual objects)
        for index, variable in x.items():
            self.assertEqual(variable.VarName, f"x[{index}]")
            self.assertEqual(variable.VType, GRB.CONTINUOUS)

        # Attributes are correct, using the series accessors to validate
        self.assertTrue((x.grb.LB == 0.0).all())
        self.assertTrue((x.grb.UB >= 1e100).all())
        assert_series_equal(x.grb.Obj, objseries, check_names=False)
