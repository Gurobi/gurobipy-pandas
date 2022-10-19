import pandas as pd
from pandas.testing import assert_index_equal
import gurobipy as gp
from gurobipy import GRB

from gurobipy_pandas.variables import add_vars_from_index
from gurobipy_pandas.constraints import (
    add_constrs_from_dataframe,
    add_constrs_from_series,
)

from .utils import GurobiTestCase


class TestAddConstrsFromDataFrame(GurobiTestCase):
    def test_scalar_rhs(self):
        x = add_vars_from_index(self.model, pd.RangeIndex(5, 10), name="x")
        df = x.to_frame()

        constrs = add_constrs_from_dataframe(self.model, df, "x", GRB.LESS_EQUAL, 1.0)

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 5)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertIsNone(constrs.name)
        assert_index_equal(constrs.index, df.index)

        # Check data in the model
        for i, (index, constr) in enumerate(constrs.items()):
            self.assertEqual(constr.ConstrName, f"R{i}")
            self.assertEqual(constr.RHS, 1.0)
            self.assertEqual(constr.Sense, GRB.LESS_EQUAL)
            self.assert_linexpr_equal(self.model.getRow(constr), 1.0 * x[index])

    def test_scalar_rhs_quad(self):
        x = add_vars_from_index(self.model, pd.RangeIndex(5, 10), name="x")
        df = (x * x).to_frame(name="xsq")

        qconstrs = add_constrs_from_dataframe(
            self.model, df, "xsq", GRB.LESS_EQUAL, 1.0
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumQConstrs, 5)

        # Returned series has the right structure
        self.assertIsInstance(qconstrs, pd.Series)
        self.assertIsNone(qconstrs.name)
        assert_index_equal(qconstrs.index, df.index)

        # Check data in the model
        for i, (index, qconstr) in enumerate(qconstrs.items()):
            self.assertEqual(qconstr.QCName, "")
            self.assertEqual(qconstr.QCRHS, 1.0)
            self.assertEqual(qconstr.QCSense, GRB.LESS_EQUAL)
            self.assert_quadexpr_equal(
                self.model.getQCRow(qconstr), 1.0 * x[index] * x[index]
            )

    def test_scalar_lhs(self):
        x = add_vars_from_index(self.model, pd.RangeIndex(5, 10), name="x")
        df = x.to_frame()

        constrs = add_constrs_from_dataframe(self.model, df, 1.0, GRB.LESS_EQUAL, "x")

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 5)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertIsNone(constrs.name)
        assert_index_equal(constrs.index, df.index)

        # Check data in the model
        for i, (index, constr) in enumerate(constrs.items()):
            self.assertEqual(constr.ConstrName, f"R{i}")
            self.assertEqual(constr.RHS, -1.0)
            self.assertEqual(constr.Sense, GRB.LESS_EQUAL)
            self.assert_linexpr_equal(self.model.getRow(constr), -1.0 * x[index])

    def test_scalar_lhs_quad(self):
        x = add_vars_from_index(self.model, pd.RangeIndex(5, 10), name="x")
        df = (x * x).to_frame(name="xsq")

        qconstrs = add_constrs_from_dataframe(
            self.model, df, 2.0, GRB.LESS_EQUAL, "xsq"
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumQConstrs, 5)

        # Returned series has the right structure
        self.assertIsInstance(qconstrs, pd.Series)
        self.assertIsNone(qconstrs.name)
        assert_index_equal(qconstrs.index, df.index)

        # Check data in the model
        for i, (index, qconstr) in enumerate(qconstrs.items()):
            self.assertEqual(qconstr.QCName, "")
            self.assertEqual(qconstr.QCRHS, -2.0)
            self.assertEqual(qconstr.QCSense, GRB.LESS_EQUAL)
            self.assert_quadexpr_equal(
                self.model.getQCRow(qconstr), -1.0 * x[index] * x[index]
            )

    def test_bothcolumns(self):
        x = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        y = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        df = pd.DataFrame({"x": x, "y": y})

        constrs = add_constrs_from_dataframe(self.model, df, "x", GRB.EQUAL, "y")

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 4)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertIsNone(constrs.name)
        assert_index_equal(constrs.index, df.index)

        # Check data and names in the model
        for i, (index, constr) in enumerate(constrs.items()):
            self.assertEqual(constr.ConstrName, f"R{i}")
            self.assertEqual(constr.RHS, 0.0)
            self.assertEqual(constr.Sense, GRB.EQUAL)
            self.assert_linexpr_equal(self.model.getRow(constr), x[index] - y[index])

    def test_names(self):
        x = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        y = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        df = pd.DataFrame({"x": x, "y": y})

        constrs = add_constrs_from_dataframe(
            self.model, df, "x", GRB.EQUAL, "y", name="constr"
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 4)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertEqual(constrs.name, "constr")
        assert_index_equal(constrs.index, df.index)

        # Check names in the model
        for index, constr in constrs.items():
            self.assertEqual(constr.ConstrName, f"constr[{index}]")

    def test_names_multiindex(self):
        df = add_vars_from_index(
            self.model,
            pd.MultiIndex.from_tuples([(1, "a"), (2, "b"), (3, "c")]),
            name="x",
        ).to_frame()

        constrs = add_constrs_from_dataframe(
            self.model, df, "x", GRB.EQUAL, 1.0, name="BND"
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 3)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertEqual(constrs.name, "BND")
        assert_index_equal(constrs.index, df.index)

        # Check names in the model
        for (i1, i2), constr in constrs.items():
            self.assertEqual(constr.ConstrName, f"BND[{i1},{i2}]")

    def test_expression_1(self):
        # Linear series <= constant series

        x = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        y = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        a = pd.Series(index=pd.RangeIndex(5, 9), data=[1, 2, 3, 4])
        data = pd.DataFrame({"x": x, "y": y, "a": a})

        constrs = add_constrs_from_dataframe(
            self.model, data, "x + y <= a", name="linear1"
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 4)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertEqual(constrs.name, "linear1")
        assert_index_equal(constrs.index, data.index)

        # Check data in model
        for index, constr in constrs.items():
            self.assertEqual(constr.ConstrName, f"linear1[{index}]")
            self.assertEqual(constr.Sense, GRB.LESS_EQUAL)
            self.assertEqual(constr.RHS, a[index])
            self.assert_linexpr_equal(self.model.getRow(constr), x[index] + y[index])

    def test_expression_2(self):
        # Linear series == constant value

        x = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        y = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        a = pd.Series(index=pd.RangeIndex(5, 9), data=[1, 2, 3, 4])
        data = pd.DataFrame({"x": x, "y": y, "a": a})

        constrs = add_constrs_from_dataframe(
            self.model, data, "x + y == 1", name="linear2"
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 4)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertEqual(constrs.name, "linear2")
        assert_index_equal(constrs.index, data.index)

        # Check data in model
        for index, constr in constrs.items():
            self.assertEqual(constr.ConstrName, f"linear2[{index}]")
            self.assertEqual(constr.Sense, GRB.EQUAL)
            self.assertEqual(constr.RHS, 1.0)
            self.assert_linexpr_equal(self.model.getRow(constr), x[index] + y[index])

    def test_expression_3(self):
        # constant value >= linear series

        x = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        y = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        a = pd.Series(index=pd.RangeIndex(5, 9), data=[1, 2, 3, 4])
        data = pd.DataFrame({"x": x, "y": y, "a": a})

        constrs = add_constrs_from_dataframe(self.model, data, "2 >= x + a")

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 4)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertIsNone(constrs.name)
        assert_index_equal(constrs.index, data.index)

        # Check data in model
        for i, (index, constr) in enumerate(constrs.items()):
            self.assertEqual(constr.ConstrName, f"C[{i}]")
            self.assertEqual(constr.Sense, GRB.GREATER_EQUAL)
            self.assertEqual(constr.RHS, a[index] - 2.0)
            self.assert_linexpr_equal(self.model.getRow(constr), -1.0 * x[index])

    def test_expression_3(self):
        # quadratic series >= linear series

        x = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        y = add_vars_from_index(self.model, pd.RangeIndex(5, 9), name="x")
        a = pd.Series(index=pd.RangeIndex(5, 9), data=[1, 2, 3, 4])
        data = pd.DataFrame({"x": x, "y": y, "a": a})

        qconstrs = add_constrs_from_dataframe(
            self.model, data, "x * y >= y * a + 5.0", name="quad"
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumQConstrs, 4)

        # Returned series has the right structure
        self.assertIsInstance(qconstrs, pd.Series)
        self.assertEqual(qconstrs.name, "quad")
        assert_index_equal(qconstrs.index, data.index)

        # Check data in model
        for index, qconstr in qconstrs.items():
            self.assertEqual(qconstr.QCName, f"quad[{index}]")
            self.assertEqual(qconstr.QCSense, GRB.GREATER_EQUAL)
            self.assertEqual(qconstr.QCRHS, 5.0)
            ref = x[index] * y[index] - y[index] * a[index]
            self.assert_quadexpr_equal(self.model.getQCRow(qconstr), ref)


class TestAddConstrsFromSeries(GurobiTestCase):
    def test_bothseries(self):
        # linear series <= linear series

        index = pd.RangeIndex(5)
        x = add_vars_from_index(self.model, index, name="x")
        y = add_vars_from_index(self.model, index, name="y")

        constrs = add_constrs_from_series(
            self.model, x + 1, GRB.LESS_EQUAL, y * 2, name="linear"
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 5)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertEqual(constrs.name, "linear")
        assert_index_equal(constrs.index, index)

        # Check data in model
        for ind, constr in constrs.items():
            self.assertEqual(constr.ConstrName, f"linear[{ind}]")
            self.assertEqual(constr.Sense, GRB.LESS_EQUAL)
            self.assertEqual(constr.RHS, -1.0)
            self.assert_linexpr_equal(self.model.getRow(constr), x[ind] - 2 * y[ind])

    def test_lhs_scalar(self):
        # scalar == linear series

        index = pd.RangeIndex(5)
        x = add_vars_from_index(self.model, index, name="x")

        constrs = add_constrs_from_series(self.model, x + 1, GRB.EQUAL, 2)

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 5)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertIsNone(constrs.name)
        assert_index_equal(constrs.index, index)

        # Check data in model
        for i, (ind, constr) in enumerate(constrs.items()):
            self.assertEqual(constr.ConstrName, f"R{i}")
            self.assertEqual(constr.Sense, GRB.EQUAL)
            self.assertEqual(constr.RHS, 1.0)
            self.assert_linexpr_equal(self.model.getRow(constr), gp.LinExpr(x[ind]))

    def test_rhs_scalar(self):
        # scalar >= linear series

        index = pd.RangeIndex(5)
        x = add_vars_from_index(self.model, index, name="x")

        constrs = add_constrs_from_series(self.model, 1, GRB.GREATER_EQUAL, 2 * x)

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumConstrs, 5)

        # Returned series has the right structure
        self.assertIsInstance(constrs, pd.Series)
        self.assertIsNone(constrs.name)
        assert_index_equal(constrs.index, index)

        # Check data in model
        for i, (ind, constr) in enumerate(constrs.items()):
            self.assertEqual(constr.ConstrName, f"R{i}")
            self.assertEqual(constr.Sense, GRB.GREATER_EQUAL)
            self.assertEqual(constr.RHS, -1.0)
            self.assert_linexpr_equal(self.model.getRow(constr), -2.0 * x[ind])

    def test_quad_series(self):
        # quad == linear

        index = pd.MultiIndex.from_tuples([("a", 1), ("b", 2), ("c", 3)])
        x = add_vars_from_index(self.model, index, name="x")
        y = add_vars_from_index(self.model, index, name="y")
        z = add_vars_from_index(self.model, index, name="z")

        qconstrs = add_constrs_from_series(
            self.model, x * y, GRB.EQUAL, 3 * z + 1, name="Q"
        )

        # Constraints added to model
        self.model.update()
        self.assertEqual(self.model.NumQConstrs, 3)

        # Returned series has the right structure
        self.assertIsInstance(qconstrs, pd.Series)
        self.assertEqual(qconstrs.name, "Q")
        assert_index_equal(qconstrs.index, index)

        # Check data in model
        for (ind1, ind2), qconstr in qconstrs.items():
            self.assertEqual(qconstr.QCName, f"Q[{ind1},{ind2}]")
            self.assertEqual(qconstr.QCSense, GRB.EQUAL)
            self.assertEqual(qconstr.QCRHS, 1)
            ref = x[ind1, ind2] * y[ind1, ind2] - z[ind1, ind2] * 3
            self.assert_quadexpr_equal(self.model.getQCRow(qconstr), ref)

    def test_misaligned_series(self):

        x = add_vars_from_index(self.model, pd.RangeIndex(5))
        y = add_vars_from_index(self.model, pd.RangeIndex(1, 4))

        with self.assertRaises(KeyError):
            add_constrs_from_series(self.model, x, GRB.EQUAL, y)

        with self.assertRaises(KeyError):
            add_constrs_from_series(self.model, y, GRB.EQUAL, x)

    def test_missingvalues(self):

        y = add_vars_from_index(self.model, pd.RangeIndex(1, 4))
        a = pd.Series(index=y.index, data=[1, None, 2], dtype=float)

        with self.assertRaises(ValueError):
            add_constrs_from_series(self.model, y, GRB.EQUAL, a)

        with self.assertRaises(ValueError):
            add_constrs_from_series(self.model, a, GRB.EQUAL, y)
