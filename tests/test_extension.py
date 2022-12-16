import unittest

import gurobipy as gp
import numpy as np
import pandas as pd

from gurobipy_pandas.extension import GurobipyArray, GurobipyDtype

from .utils import GurobiTestCase


class TestGurobipyDtype(unittest.TestCase):
    def test_properties(self):
        assert GurobipyDtype.name == "gpobj"
        assert GurobipyDtype.construct_array_type() == GurobipyArray


class TestGurobipyArray(unittest.TestCase):
    """Many of these tests are redundant to the constructors test from pandas..."""

    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_construction(self):
        x = self.model.addVars(10)
        self.model.update()
        array = GurobipyArray(np.array(x.values()))
        self.assertIsInstance(array.dtype, GurobipyDtype)

    def test_size_methods(self):
        x = self.model.addVars(10)
        self.model.update()
        array = GurobipyArray(np.array(x.values()))
        self.assertEqual(len(array), 10)
        self.assertEqual(array.shape, (10,))
        self.assertEqual(array.size, 10)

    def test_from_sequence_of_vars(self):
        x = self.model.addVars(10)
        self.model.update()
        array = GurobipyArray._from_sequence(x.values())
        self.assertEqual(len(array), 10)

    def test_from_sequence_dtype(self):
        x = self.model.addVars(10)
        self.model.update()
        array = GurobipyArray._from_sequence(x.values(), dtype=GurobipyDtype())
        self.assertEqual(len(array), 10)

    def test_from_sequence_copy(self):
        # Copy has no impact on Var, but should deep copy LinExpr
        x = self.model.addVars(10)
        self.model.update()
        linexprs = [v * 1.0 for v in x.values()]
        array = GurobipyArray._from_sequence(linexprs, dtype=GurobipyDtype(), copy=True)
        self.assertEqual(len(array), 10)
        for i in range(10):
            self.assertIsNot(linexprs[i], array[i])
            self.assertEqual(array[i].size(), 1)
            self.assertEqual(array[i].getCoeff(0), 1.0)
            self.assertIs(array[i].getVar(0), x[i])

    def test_from_sequence_nocopy(self):
        x = self.model.addVars(10)
        self.model.update()
        linexprs = [v * 1.0 for v in x.values()]
        array = GurobipyArray._from_sequence(
            linexprs, dtype=GurobipyDtype(), copy=False
        )
        self.assertEqual(len(array), 10)
        for i in range(10):
            self.assertIs(linexprs[i], array[i])

    def test_get_item(self):
        x = self.model.addVars(10)
        self.model.update()
        array = GurobipyArray._from_sequence(x.values())
        # Single element
        self.assertIs(array[4], x[4])
        # Slice
        subarray = array[3:7]
        self.assertIsInstance(subarray, GurobipyArray)
        self.assertEqual(len(subarray), 4)
        self.assertIs(subarray[0], x[3])
        # Conditional
        cond = np.array([1, 0, 0, 1, 1, 1, 0, 1, 1, 0]).astype(bool)
        subarray = array[cond]
        self.assertIsInstance(subarray, GurobipyArray)
        self.assertEqual(len(subarray), 6)
        self.assertIs(subarray[3], x[5])

    def test_isna(self):
        # for now, expect a dense array?
        x = self.model.addVars(10)
        self.model.update()
        array = GurobipyArray._from_sequence(x.values())
        np.testing.assert_array_equal(array.isna(), np.array([False] * 10))

    def test_copy_vars(self):
        """This is really a no-op, copying only the internal array"""
        x = self.model.addVars(10)
        self.model.update()
        array = GurobipyArray._from_sequence(x.values(), dtype=GurobipyDtype())
        copied = array.copy()
        for i in range(10):
            self.assertIs(copied[i], array[i])

    def test_expressions_vars(self):
        """This is really a no-op, copying only the internal array"""
        x = self.model.addVars(10)
        self.model.update()
        array = GurobipyArray._from_sequence([2.0 * v for v in x.values()])
        copied = array.copy()
        for i in range(10):
            self.assertIsNot(copied[i], array[i])
            self.assertEqual(copied[i].size(), 1)
            self.assertEqual(copied[i].getCoeff(0), 2.0)
            self.assertIs(copied[i].getVar(0), x[i])

    def test_astype(self):
        """Casting from an object series using registered type"""
        x = self.model.addVars(10)
        self.model.update()
        series = pd.Series(x).astype("gpobj")
        self.assertIs(series.loc[5], x[5])


class TestArithmenticOps(GurobiTestCase):
    """Not so thorough; these ops are installed for free."""

    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_add_var_var(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        y = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        result = x + y
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assert_linexpr_equal(le, x[i] + y[i])

    def test_add_var_numeric(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        a = pd.Series(np.arange(10))
        result = x + a
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assert_linexpr_equal(le, x[i] + i)

    def test_add_var_scalarvar(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        result = x + x[0]
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assert_linexpr_equal(le, x[i] + x[0])

    def test_add_scalar_var(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        result = 2.0 + x
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assert_linexpr_equal(le, x[i] + 2.0)

    def test_add_scalarvar_var(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        result = x[0] + x
        # LinExpr raises GurobiError when it should return NotImplemented
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assert_linexpr_equal(le, x[0] + x[i])

    def test_add_numeric_var(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        a = pd.Series(np.arange(10))
        result = a + x
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assert_linexpr_equal(le, x[i] + i)

    def test_mul_numeric_var(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        a = pd.Series(np.arange(10))
        result = a * x
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assert_linexpr_equal(le, i * x[i])

    def test_mul_var_var(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        y = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        result = x * y
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            qe = result[i]
            self.assertIsInstance(qe, gp.QuadExpr)
            self.assert_quadexpr_equal(qe, x[i] * y[i])


class TestCommonOps(GurobiTestCase):
    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_sum(self):
        x = self.model.addVars(3)
        xs = pd.Series(x).astype("gpobj")
        result = xs.sum()
        self.assertIsInstance(result, gp.LinExpr)
        self.assert_linexpr_equal(result, x[0] + x[1] + x[2])

    def test_groupby(self):
        x = self.model.addVars(3)
        df = pd.DataFrame(
            {
                "group": [1, 2, 1],
                "x": pd.Series(x).astype("gpobj"),
            }
        )
        self.model.update()
        result = df.groupby("group")["x"].sum()

        le1 = result[1]
        self.assertIsInstance(le1, gp.LinExpr)
        self.assert_linexpr_equal(le1, x[0] + x[2])

        le2 = result[2]
        self.assertIsInstance(le1, gp.LinExpr)
        self.assert_linexpr_equal(le2, x[1] * 1.0)
