import gurobipy as gp
import pandas as pd
from gurobipy import GRB
from pandas.testing import assert_index_equal

from gurobipy_pandas.variables import add_vars_from_dataframe, add_vars_from_index

from .utils import GurobiModelTestCase

GUROBIPY_MAJOR_VERSION, *_ = gp.gurobi.version()


class TestAddVarsFromIndex(GurobiModelTestCase):
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

    def test_attribute_wrongtypes(self):
        # If series are not passed for attributes, they must be scalar
        index = pd.RangeIndex(5)

        with self.subTest(attr="lb"):
            with self.assertRaises(TypeError):
                add_vars_from_index(self.model, index, lb=[1, 2, 3, 4, 5])

        with self.subTest(attr="ub"):
            with self.assertRaises(TypeError):
                add_vars_from_index(self.model, index, ub=[1, 2, 3, 4, 5])

        with self.subTest(attr="obj"):
            with self.assertRaises(TypeError):
                add_vars_from_index(self.model, index, obj=[1, 2, 3, 4, 5])

        with self.subTest(attr="vtype"):
            with self.assertRaises(TypeError):
                add_vars_from_index(self.model, index, vtype=["B", "I", "C", "N", "S"])

        with self.subTest(attr="name"):
            with self.assertRaises(TypeError):
                add_vars_from_index(self.model, index, name=1.5)

    def test_default_index_formatter(self):
        # Cleanup of illegal characters in names should happen by default
        datetimeindex = pd.date_range(
            start=pd.Timestamp(2022, 4, 3), freq="D", periods=3
        )
        stringindex = pd.Index(["a  b", "c", "d"])
        index = pd.MultiIndex.from_arrays([datetimeindex, stringindex])

        x = add_vars_from_index(self.model, index, name="x")
        self.model.update()

        string_map = {"a  b": "a_b", "c": "c", "d": "d"}
        for dtvalue, strvalue in index:
            expected = f"x[2022_04_{dtvalue.day:02d}T00_00_00,{string_map[strvalue]}]"
            self.assertEqual(x[dtvalue, strvalue].VarName, expected)

    def test_custom_index_formatter(self):
        # Customize or switch off auto-formatting by index level
        datetimeindex = pd.date_range(
            start=pd.Timestamp(2022, 4, 3), freq="D", periods=3, name="date"
        )
        stringindex = pd.Index(["a  b", "c", "d"], name="surname")
        index = pd.MultiIndex.from_arrays([datetimeindex, stringindex])

        formatter = {
            "date": lambda index: pd.Series(index).dt.strftime("%Y%m%d"),
            "surname": None,
        }
        x = add_vars_from_index(self.model, index, name="x", index_formatter=formatter)
        self.model.update()

        for dtvalue, strvalue in index:
            expected = f"x[202204{dtvalue.day:02d},{strvalue}]"
            self.assertEqual(x[dtvalue, strvalue].VarName, expected)

    def test_index_duplicates(self):
        index = pd.Index([0, 1, 1, 2])
        self.assertTrue(index.has_duplicates)

        with self.assertRaisesRegex(ValueError, "Index contains duplicate entries"):
            add_vars_from_index(self.model, index)

    def test_naming_duplicates(self):
        index = pd.RangeIndex(5)
        self.assertFalse(index.has_duplicates)

        # User provided index formatter which creates duplicates. This should
        # go through ok (although they'll get a warning and reversion to default
        # if they try to write to a file).
        x = add_vars_from_index(
            self.model,
            index,
            name="x",
            index_formatter=lambda ind: ["label"] * len(ind),
        )

        self.model.update()
        self.assertEqual(self.model.NumVars, 5)
        if GUROBIPY_MAJOR_VERSION >= 10:
            self.assertEqual(list(x.gppd.VarName), ["x[label]"] * 5)
        else:
            self.assertEqual(list(x.gppd.VarName), [f"x[label][{i}]" for i in range(5)])


class TestAddVarsFromDataFrame(GurobiModelTestCase):
    def setUp(self):
        super().setUp()
        self.data = pd.DataFrame(
            {
                "str1": ["a", "b", "c", "d"],
                "int1": [1, 2, 3, 4],
                "float1": [2.2, 3.1, -1.0, 2.4],
                "float2": [1.1, 2.1, 4.3, 1.5],
            }
        )

    def test_noargs(self):
        # Variables are created for each entry in index, with default names
        # from Gurobi

        varseries = add_vars_from_dataframe(self.model, self.data)

        self.model.update()
        self.assertEqual(self.model.NumVars, 4)

        self.assertIsInstance(varseries, pd.Series)
        self.assertIsNone(varseries.name)
        assert_index_equal(varseries.index, self.data.index)

        for i, ind in enumerate(self.data.index):
            v = varseries[ind]
            self.assertEqual(v.LB, 0.0)
            self.assertGreater(v.UB, 1e100)
            self.assertEqual(v.Obj, 0.0)
            self.assertEqual(v.VType, GRB.CONTINUOUS)
            self.assertEqual(v.VarName, f"C{i}")

    def test_generatednames(self):
        # Variables are created for each entry in index, with prefixed
        # names incorporating the index values

        df = self.data.set_index("int1")

        varseries = add_vars_from_dataframe(self.model, df, name="y")

        self.model.update()
        self.assertEqual(self.model.NumVars, 4)

        self.assertIsInstance(varseries, pd.Series)
        self.assertEqual(varseries.name, "y")
        assert_index_equal(varseries.index, df.index)

        for ind in df.index:
            v = varseries[ind]
            self.assertEqual(v.LB, 0.0)
            self.assertGreater(v.UB, 1e100)
            self.assertEqual(v.Obj, 0.0)
            self.assertEqual(v.VType, GRB.CONTINUOUS)
            self.assertEqual(v.VarName, f"y[{ind}]")

    def test_generatednames_multiindex(self):
        # Variables are created for each entry in index, with prefixed
        # names incorporating the index values

        df = self.data.set_index(["int1", "str1"])

        varseries = add_vars_from_dataframe(self.model, df, name="z")

        self.model.update()
        self.assertEqual(self.model.NumVars, 4)

        self.assertIsInstance(varseries, pd.Series)
        self.assertEqual(varseries.name, "z")
        assert_index_equal(varseries.index, df.index)

        for some_int, some_str in df.index:
            v = varseries[some_int, some_str]
            self.assertEqual(v.LB, 0.0)
            self.assertGreater(v.UB, 1e100)
            self.assertEqual(v.Obj, 0.0)
            self.assertEqual(v.VType, GRB.CONTINUOUS)
            self.assertEqual(v.VarName, f"z[{some_int},{some_str}]")

    def test_lb_value(self):
        # lb numeric value assigned to all variables

        varseries = add_vars_from_dataframe(self.model, self.data, lb=-100)

        self.model.update()
        for _, v in varseries.items():
            self.assertEqual(v.LB, -100.0)

    def test_lb_column(self):
        # lb string value interpreted as a column to reference

        varseries = add_vars_from_dataframe(self.model, self.data, lb="float1")

        self.model.update()
        for ind, v in varseries.items():
            self.assertEqual(v.LB, self.data.loc[ind, "float1"])

    def test_ub_value(self):
        # ub numeric value assigned to all variables

        varseries = add_vars_from_dataframe(self.model, self.data, ub=5)

        self.model.update()
        for _, v in varseries.items():
            self.assertEqual(v.UB, 5.0)

    def test_ub_column(self):
        # ub string value interpreted as a column to reference

        varseries = add_vars_from_dataframe(self.model, self.data, ub="float2")

        self.model.update()
        for ind, v in varseries.items():
            self.assertEqual(v.UB, self.data.loc[ind, "float2"])

    def test_obj_value(self):
        # obj numeric value assigned to all variables

        varseries = add_vars_from_dataframe(self.model, self.data, obj=1.0)

        self.model.update()
        for _, v in varseries.items():
            self.assertEqual(v.Obj, 1.0)

    def test_obj_column(self):
        # obj string value interpreted as a column to reference

        varseries = add_vars_from_dataframe(self.model, self.data, obj="float1")

        self.model.update()
        for ind, v in varseries.items():
            self.assertEqual(v.Obj, self.data.loc[ind, "float1"])

    def test_vtype_value(self):
        # vtype can only be a string value, giving all variables the
        # same type

        varseries = add_vars_from_dataframe(self.model, self.data, vtype=GRB.BINARY)

        self.model.update()
        for _, v in varseries.items():
            self.assertEqual(v.VType, GRB.BINARY)

    def test_attribute_series(self):
        # passing attributes as a series should fail (even if aligned)

        with self.subTest(attr="lb"):
            with self.assertRaises(TypeError):
                add_vars_from_dataframe(self.model, self.data, lb=self.data["float1"])

        with self.subTest(attr="ub"):
            with self.assertRaises(TypeError):
                add_vars_from_dataframe(self.model, self.data, ub=self.data["float1"])

        with self.subTest(attr="obj"):
            with self.assertRaises(TypeError):
                add_vars_from_dataframe(self.model, self.data, obj=self.data["float1"])

        with self.subTest(attr="name"):
            with self.assertRaises(TypeError):
                add_vars_from_dataframe(self.model, self.data, name=self.data["str1"])

        with self.subTest(attr="vtype"):
            typeseries = pd.Series(index=self.data.index, data=["I", "B", "C", "S"])
            with self.assertRaises(TypeError):
                add_vars_from_dataframe(self.model, self.data, vtype=typeseries)

    def test_default_index_formatter(self):
        # Cleanup of illegal characters in names should happen by default
        datetimeindex = pd.date_range(
            start=pd.Timestamp(2022, 4, 3), freq="D", periods=3
        )
        stringindex = pd.Index(["a  b", "c", "d"])
        df = pd.DataFrame(
            index=pd.MultiIndex.from_arrays([datetimeindex, stringindex]),
            data={"a": [1, 2, 3], "b": [4, 5, 6]},
        )

        x = add_vars_from_dataframe(self.model, df, name="x", lb="a", ub="b")
        self.model.update()

        string_map = {"a  b": "a_b", "c": "c", "d": "d"}
        for dtvalue, strvalue in df.index:
            expected = f"x[2022_04_{dtvalue.day:02d}T00_00_00,{string_map[strvalue]}]"
            self.assertEqual(x[dtvalue, strvalue].VarName, expected)

    def test_custom_index_formatter(self):
        # Override cleanup for name index levels. Defaults still apply to
        # non-named levels.
        datetimeindex = pd.date_range(
            start=pd.Timestamp(2022, 4, 3), freq="D", periods=3, name="date"
        )
        stringindex = pd.Index(["a  b", "c", "d"], name="surname")
        df = pd.DataFrame(
            index=pd.MultiIndex.from_arrays([datetimeindex, stringindex]),
            data={"a": [1, 2, 3], "b": [4, 5, 6]},
        )

        formatter = {"date": lambda index: pd.Series(index).dt.strftime("%y%m%d")}
        x = add_vars_from_dataframe(
            self.model, df, name="x", lb="a", ub="b", index_formatter=formatter
        )
        self.model.update()

        string_map = {"a  b": "a_b", "c": "c", "d": "d"}
        for dtvalue, strvalue in df.index:
            expected = f"x[2204{dtvalue.day:02d},{string_map[strvalue]}]"
            self.assertEqual(x[dtvalue, strvalue].VarName, expected)

    def test_index_duplicates(self):
        data = pd.DataFrame(index=pd.Index([0, 1, 1, 2]), data={"a": list(range(4))})
        self.assertTrue(data.index.has_duplicates)

        with self.assertRaisesRegex(ValueError, "Index contains duplicate entries"):
            add_vars_from_dataframe(self.model, data)

    def test_naming_duplicates(self):
        data = pd.DataFrame(index=pd.RangeIndex(5), data={"a": list(range(5))})
        self.assertFalse(data.index.has_duplicates)

        # User provided index formatter which creates duplicates. This should
        # go through ok (although they'll get a warning and reversion to default
        # if they try to write to a file).
        x = add_vars_from_dataframe(
            self.model,
            data,
            name="x",
            index_formatter=lambda ind: ["label"] * len(ind),
        )

        self.model.update()
        self.assertEqual(self.model.NumVars, 5)
        if GUROBIPY_MAJOR_VERSION >= 10:
            self.assertEqual(list(x.gppd.VarName), ["x[label]"] * 5)
        else:
            self.assertEqual(list(x.gppd.VarName), [f"x[label][{i}]" for i in range(5)])
