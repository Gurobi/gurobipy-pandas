import unittest

import pandas as pd
from pandas.testing import assert_index_equal
import gurobipy as gp
from gurobipy import GRB

from gurobipy_pandas.add_vars import add_vars_from_index


class TestAddVarsFromIndex(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_rangeindex_noargs(self):
        # Variables are created for each entry in index, with default names
        # from Gurobi
        index = pd.RangeIndex(5, 10)

        varseries = add_vars_from_index(self.model, index)

        self.model.update()
        self.assertEqual(self.model.NumVars, 5)

        self.assertIsInstance(varseries, pd.Series)
        self.assertIsNone(varseries.name)
        assert_index_equal(varseries.index, index)

        for i, ind in enumerate(index):
            v = varseries[ind]
            self.assertEqual(v.LB, 0.0)
            self.assertGreater(v.UB, 1e100)
            self.assertEqual(v.Obj, 0.0)
            self.assertEqual(v.VType, GRB.CONTINUOUS)
            self.assertEqual(v.VarName, f"C{i}")

    def test_rangeindex_generatednames(self):
        # Variables are created for each entry in index, with prefixed
        # names incorporating the index values
        index = pd.RangeIndex(5, 10)

        varseries = add_vars_from_index(self.model, index, name="x")

        self.model.update()
        self.assertEqual(self.model.NumVars, 5)

        self.assertIsInstance(varseries, pd.Series)
        self.assertEqual(varseries.name, "x")
        assert_index_equal(varseries.index, index)

        for ind in index:
            v = varseries[ind]
            self.assertEqual(v.LB, 0.0)
            self.assertGreater(v.UB, 1e100)
            self.assertEqual(v.Obj, 0.0)
            self.assertEqual(v.VType, GRB.CONTINUOUS)
            self.assertEqual(v.VarName, f"x[{ind}]")

    def test_multiindex_noargs(self):
        # Variables are created for each entry in index, with default names
        # from Gurobi
        tuples = [(1, "red"), (1, "blue"), (2, "red"), (2, "blue")]
        index = pd.MultiIndex.from_tuples(tuples, names=("number", "color"))

        varseries = add_vars_from_index(self.model, index)

        self.model.update()
        self.assertEqual(self.model.NumVars, 4)

        self.assertIsInstance(varseries, pd.Series)
        self.assertIsNone(varseries.name)
        assert_index_equal(varseries.index, index)

        for i, ind in enumerate(index):
            v = varseries[ind]
            self.assertEqual(v.LB, 0.0)
            self.assertGreater(v.UB, 1e100)
            self.assertEqual(v.Obj, 0.0)
            self.assertEqual(v.VType, GRB.CONTINUOUS)
            self.assertEqual(v.VarName, f"C{i}")

    def test_multiindex_generatednames(self):
        # Variables are created for each entry in index, with prefixed
        # names incorporating the index values
        tuples = [(1, "red"), (1, "blue"), (2, "red"), (2, "blue")]
        index = pd.MultiIndex.from_tuples(tuples, names=("number", "color"))

        varseries = add_vars_from_index(self.model, index, name="ball")

        self.model.update()
        self.assertEqual(self.model.NumVars, 4)

        self.assertIsInstance(varseries, pd.Series)
        self.assertEqual(varseries.name, "ball")
        assert_index_equal(varseries.index, index)

        for number, color in index:
            v = varseries[number, color]
            self.assertEqual(v.LB, 0.0)
            self.assertGreater(v.UB, 1e100)
            self.assertEqual(v.Obj, 0.0)
            self.assertEqual(v.VType, GRB.CONTINUOUS)
            self.assertEqual(v.VarName, f"ball[{number},{color}]")

    def test_name_series(self):
        # Variables are created for each entry in index, with explicit names
        index = pd.RangeIndex(4, 8)
        names = pd.Series(index=index, data=["a", "b", "c", "d"])

        varseries = add_vars_from_index(self.model, index, name=names)

        self.model.update()
        self.assertEqual(self.model.NumVars, 4)

        self.assertIsInstance(varseries, pd.Series)
        self.assertIsNone(varseries.name)
        assert_index_equal(varseries.index, index)

        for ind, name in zip([4, 5, 6, 7], ["a", "b", "c", "d"]):
            v = varseries[ind]
            self.assertEqual(v.VarName, name)

    def test_name_series_reordered(self):
        # Variables are created for each entry in index, with explicit names
        index = pd.RangeIndex(4, 8)
        names = pd.Series(index=[7, 6, 5, 4], data=["a", "b", "c", "d"])

        varseries = add_vars_from_index(self.model, index, name=names)

        self.model.update()
        self.assertEqual(self.model.NumVars, 4)

        self.assertIsInstance(varseries, pd.Series)
        self.assertIsNone(varseries.name)
        assert_index_equal(varseries.index, index)

        for ind, name in zip([4, 5, 6, 7], ["d", "c", "b", "a"]):
            v = varseries[ind]
            self.assertEqual(v.VarName, name)

    def test_name_series_mismatch(self):

        index = pd.RangeIndex(5)

        # Missing entries for some values in the index
        names = pd.Series(index=pd.RangeIndex(1, 4), data=list("abc"))
        with self.assertRaises(KeyError):
            add_vars_from_index(self.model, index, name=names)

        # Too many values (require exact alignment)
        names = pd.Series(index=pd.RangeIndex(6), data=list("abcdef"))
        with self.assertRaises(KeyError):
            add_vars_from_index(self.model, index, name=names)

    def test_name_series_missing_values(self):

        index = pd.RangeIndex(5)

        # Missing data (series must be complete if on the same index)
        names = pd.Series(index=index, data=["a", "b", None, None, "e"])
        with self.assertRaises(ValueError):
            add_vars_from_index(self.model, index, name=names)

    def test_lb_value(self):
        index = pd.RangeIndex(5)

        # All variables assigned the same lower bound
        varseries = add_vars_from_index(self.model, index, lb=-1.0)
        self.model.update()
        for _, v in varseries.items():
            self.assertEqual(v.LB, -1.0)

    def test_lb_series(self):
        index = pd.RangeIndex(5)

        # Bounds assigned from an aligned series
        lbseries = pd.Series(index=index, data=[1, 2, 3, 4, 5])
        varseries = add_vars_from_index(self.model, index, lb=lbseries)
        self.model.update()
        for ind in index:
            self.assertEqual(varseries[ind].LB, lbseries[ind])

    def test_lb_series_mismatch(self):
        index = pd.RangeIndex(5)

        # Missing entries for some values in the index
        with self.assertRaises(KeyError):
            lbseries = pd.Series(index=pd.RangeIndex(1, 4), data=[1, 2, 3])
            add_vars_from_index(self.model, index, lb=lbseries)

        # Too many values (require exact alignment)
        with self.assertRaises(KeyError):
            lbseries = pd.Series(index=pd.RangeIndex(6), data=[1, 2, 3, 4, 5, 6])
            add_vars_from_index(self.model, index, lb=lbseries)

    def test_lb_series_missing_values(self):
        index = pd.RangeIndex(5)

        # Missing values
        with self.assertRaises(ValueError):
            lbseries = pd.Series(index=index, data=[0, None, 1, 2, None])
            add_vars_from_index(self.model, index, lb=lbseries)

    def test_ub_value(self):
        index = pd.RangeIndex(5)

        # All variables assigned the same lower bound
        varseries = add_vars_from_index(self.model, index, ub=10.0)
        self.model.update()
        for _, v in varseries.items():
            self.assertEqual(v.UB, 10.0)

    def test_ub_series(self):
        index = pd.RangeIndex(5)

        # Bounds assigned from an aligned series
        ubseries = pd.Series(index=[4, 3, 2, 1, 0], data=[1, 2, 3, 4, 5])
        varseries = add_vars_from_index(self.model, index, ub=ubseries)
        self.model.update()
        for ind in index:
            self.assertEqual(varseries[ind].UB, ubseries[ind])

    def test_ub_series_mismatch(self):
        index = pd.RangeIndex(5)

        # Missing entries for some values in the index
        with self.assertRaises(KeyError):
            ubseries = pd.Series(index=pd.RangeIndex(1, 4), data=[1, 2, 3])
            add_vars_from_index(self.model, index, ub=ubseries)

        # Too many values (require exact alignment)
        with self.assertRaises(KeyError):
            ubseries = pd.Series(index=pd.RangeIndex(6), data=[1, 2, 3, 4, 5, 6])
            add_vars_from_index(self.model, index, ub=ubseries)

    def test_ub_series_missing_values(self):
        index = pd.RangeIndex(5)

        # Missing values
        with self.assertRaises(ValueError):
            ubseries = pd.Series(index=index, data=[0, None, 1, 2, None])
            add_vars_from_index(self.model, index, ub=ubseries)

    def test_obj_value(self):
        index = pd.RangeIndex(5)

        # All variables assigned the same lower bound
        varseries = add_vars_from_index(self.model, index, obj=10.0)
        self.model.update()
        for _, v in varseries.items():
            self.assertEqual(v.Obj, 10.0)

    def test_obj_series(self):
        index = pd.RangeIndex(5)

        # Bounds assigned from an aligned series
        objseries = pd.Series(index=[1, 2, 0, 4, 3], data=[5, 4, 3, 2, 1])
        varseries = add_vars_from_index(self.model, index, obj=objseries)
        self.model.update()
        for ind in index:
            self.assertEqual(varseries[ind].Obj, objseries[ind])

    def test_obj_series_mismatch(self):
        index = pd.RangeIndex(5)

        # Missing entries for some values in the index
        with self.assertRaises(KeyError):
            objseries = pd.Series(index=pd.RangeIndex(1, 4), data=[1, 2, 3])
            add_vars_from_index(self.model, index, obj=objseries)

        # Too many values (require exact alignment)
        with self.assertRaises(KeyError):
            objseries = pd.Series(index=pd.RangeIndex(6), data=[1, 2, 3, 4, 5, 6])
            add_vars_from_index(self.model, index, obj=objseries)

    def test_obj_series_missing_values(self):
        index = pd.RangeIndex(5)

        # Missing values
        with self.assertRaises(ValueError):
            objseries = pd.Series(index=index, data=[0, None, 1, 2, None])
            add_vars_from_index(self.model, index, obj=objseries)

    def test_vtype_value(self):
        index = pd.RangeIndex(5)

        # All variables assigned the same lower bound
        varseries = add_vars_from_index(self.model, index, vtype=GRB.BINARY)
        self.model.update()
        for _, v in varseries.items():
            self.assertEqual(v.VType, GRB.BINARY)

    def test_vtype_series(self):
        index = pd.RangeIndex(5)

        # Bounds assigned from an aligned series
        vtypeseries = pd.Series(index=[3, 4, 2, 0, 1], data=["B", "I", "C", "S", "N"])
        varseries = add_vars_from_index(self.model, index, vtype=vtypeseries)
        self.model.update()
        for ind in index:
            self.assertEqual(varseries[ind].VType, vtypeseries[ind])

    def test_vtype_series_mismatch(self):
        index = pd.RangeIndex(5)

        # Missing entries for some values in the index
        with self.assertRaises(KeyError):
            vtypeseries = pd.Series(index=pd.RangeIndex(1, 4), data=["B", "I", "C"])
            add_vars_from_index(self.model, index, vtype=vtypeseries)

        # Too many values (require exact alignment)
        with self.assertRaises(KeyError):
            vtypeseries = pd.Series(index=pd.RangeIndex(8), data=["B"] * 8)
            add_vars_from_index(self.model, index, vtype=vtypeseries)

    def test_vtype_series_missing_values(self):
        index = pd.RangeIndex(5)

        # Missing values
        with self.assertRaises(ValueError):
            vtypeseries = pd.Series(index=index, data=["C", None, "I", "B", None])
            add_vars_from_index(self.model, index, vtype=vtypeseries)
