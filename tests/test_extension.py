import unittest

import gurobipy as gp
import numpy as np
import pandas as pd

from pdcomfi.extension import GurobipyArray, GurobipyDtype, Model


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
        np.testing.assert_array_equal(array.isna(), np.array([True] * 10))

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


class TestArithmenticOps(unittest.TestCase):
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
            self.assertEqual(le.size(), 2)
            self.assertIs(le.getVar(0), x[i])
            self.assertEqual(le.getCoeff(0), 1.0)
            self.assertIs(le.getVar(1), y[i])
            self.assertEqual(le.getCoeff(1), 1.0)

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
            self.assertEqual(le.size(), 1)
            self.assertEqual(le.getConstant(), float(i))
            self.assertIs(le.getVar(0), x[i])
            self.assertEqual(le.getCoeff(0), 1.0)

    def test_add_var_scalarvar(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        result = x + x[0]
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assertEqual(le.size(), 2)
            self.assertEqual(le.getConstant(), 0)
            self.assertIs(le.getVar(0), x[i])
            self.assertEqual(le.getCoeff(0), 1.0)
            self.assertIs(le.getVar(1), x[0])
            self.assertEqual(le.getCoeff(1), 1.0)

    def test_add_scalar_var(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        result = 2.0 + x
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            le = result[i]
            self.assertIsInstance(le, gp.LinExpr)
            self.assertEqual(le.size(), 1)
            self.assertEqual(le.getConstant(), 2.0)
            self.assertIs(le.getVar(0), x[i])
            self.assertEqual(le.getCoeff(0), 1.0)

    @unittest.expectedFailure
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
            self.assertEqual(le.size(), 2)
            self.assertEqual(le.getConstant(), 0)
            self.assertIs(le.getVar(0), x[0])
            self.assertEqual(le.getCoeff(0), 1.0)
            self.assertIs(le.getVar(1), x[i])
            self.assertEqual(le.getCoeff(1), 1.0)

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
            self.assertEqual(le.size(), 1)
            self.assertEqual(le.getConstant(), float(i))
            self.assertIs(le.getVar(0), x[i])
            self.assertEqual(le.getCoeff(0), 1.0)

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
            self.assertEqual(le.size(), 1)
            self.assertIs(le.getVar(0), x[i])
            self.assertEqual(le.getCoeff(0), float(i))
            self.assertEqual(le.getConstant(), 0.0)

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
            self.assertEqual(qe.size(), 1)
            self.assertIs(qe.getVar1(0), x[i])
            self.assertIs(qe.getVar2(0), y[i])
            self.assertEqual(qe.getCoeff(0), 1.0)


class TestComparisonOps(unittest.TestCase):
    def setUp(self):
        self.env = gp.Env()
        self.model = gp.Model(env=self.env)

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_var_eq_var(self):
        x = pd.Series(self.model.addVars(10)).astype("gpobj")
        y = pd.Series(self.model.addVars(10)).astype("gpobj")
        self.model.update()
        result = x == y
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            tc = result[i]
            self.assertIsInstance(tc, gp.TempConstr)

    def test_var_le_var(self):
        x = pd.Series(self.model.addVars(10, name="x")).astype("gpobj")
        y = pd.Series(self.model.addVars(10, name="y")).astype("gpobj")
        self.model.update()
        result = x <= y
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            tc = result[i]
            self.assertIsInstance(tc, gp.TempConstr)

    def test_var_le_numeric(self):
        x = pd.Series(self.model.addVars(10, name="x")).astype("gpobj")
        self.model.update()
        a = pd.Series(np.arange(10))
        result = x <= a
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            tc = result[i]
            self.assertIsInstance(tc, gp.TempConstr)

    def test_numeric_le_var(self):
        x = pd.Series(self.model.addVars(10, name="x")).astype("gpobj")
        self.model.update()
        a = pd.Series(np.arange(10))
        # TODO pandas seems to resolve the operation to the extension
        # array, should confirm if this is a consistent rule.
        result = a <= x
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            tc = result[i]
            self.assertIsInstance(tc, gp.TempConstr)

    def test_var_ge_scalar(self):
        x = pd.Series(self.model.addVars(10, name="x")).astype("gpobj")
        self.model.update()
        result = x >= 1
        self.assertIsInstance(result, pd.Series)
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            tc = result[i]
            self.assertIsInstance(tc, gp.TempConstr)

    @unittest.expectedFailure
    def test_series_ge_linexpr(self):
        x = pd.Series(self.model.addVars(10, name="x")).astype("gpobj")
        self.model.update()
        result = x >= x[0]
        self.assertIsInstance(result, pd.Series)
        # Object dtype, not quite sure why. Problematic since we then leave
        # our dtyped universe.
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            tc = result[i]
            self.assertIsInstance(tc, gp.TempConstr)

    @unittest.expectedFailure
    def test_linexpr_ge_series(self):
        x = pd.Series(self.model.addVars(10, name="x")).astype("gpobj")
        self.model.update()
        result = x[0] >= x
        self.assertIsInstance(result, pd.Series)
        # TempConstr with a series on the right!!!!
        # LinExpr/Var should return NotImplemented in this case.
        self.assertIsInstance(result.dtype, GurobipyDtype)
        for i in range(10):
            tc = result[i]
            self.assertIsInstance(tc, gp.TempConstr)


class TestModel(unittest.TestCase):
    """Tests using the model subclass which adds addSeriesVars/addSeriesConstrs
    capabilities."""

    def setUp(self):
        self.env = gp.Env()
        self.model = Model(env=self.env)  # use model subclass

    def tearDown(self):
        self.model.close()
        self.env.close()

    def test_add_series_vars(self):
        index = pd.Index(["a", "b", "c"])
        xs = self.model.addSeriesVars(index, name="x")
        self.model.update()
        self.assertIsInstance(xs, pd.Series)
        self.assertEqual(xs.name, "x")
        self.assertIsInstance(xs.dtype, GurobipyDtype)
        for i, name in enumerate(["x[a]", "x[b]", "x[c]"]):
            x = xs[i]
            self.assertIsInstance(x, gp.Var)
            self.assertEqual(x.VarName, name)

    def test_add_constrs(self):
        index = pd.Index(["a", "b", "c"])
        xs = self.model.addSeriesVars(index, name="x")
        ys = self.model.addSeriesVars(index, name="y")
        constrs = self.model.addSeriesConstrs(xs <= ys, name="c")
        self.model.update()
        self.assertIsInstance(constrs, pd.Series)
        self.assertEqual(constrs.name, "c")
        self.assertIsInstance(constrs.dtype, GurobipyDtype)
        for i, name in enumerate(["c[a]", "c[b]", "c[c]"]):
            constr = constrs[i]
            self.assertIsInstance(constr, gp.Constr)
            self.assertEqual(constr.ConstrName, name)
            self.assertEqual(constr.RHS, 0.0)
            self.assertEqual(constr.Sense, gp.GRB.LESS_EQUAL)
            row = self.model.getRow(constr)
            self.assertEqual(row.size(), 2)
            self.assertIs(row.getVar(0), xs[i])
            self.assertEqual(row.getCoeff(0), 1.0)
            self.assertIs(row.getVar(1), ys[i])
            self.assertEqual(row.getCoeff(1), -1.0)
