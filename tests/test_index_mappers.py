import datetime
import unittest

import pandas as pd

from gurobipy_pandas.index_mappers import create_mapper


class TestNoMapper(unittest.TestCase):
    # Passing None to create a mapper disables all default mapping.

    def setUp(self):
        self.mapper = create_mapper("disable")

    def test_int(self):
        # Integer dtypes -> iterable of ints
        index = pd.RangeIndex(10)
        mapped = self.mapper(index)
        self.assertEqual(list(mapped), list(range(10)))

    def test_object(self):
        # Object dtypes -> iterable of objects
        index = pd.Index(
            ["a", 1, "b", datetime.date(2021, 3, 5), datetime.time(12, 30, 43)]
        )
        mapped = self.mapper(index)
        self.assertEqual(
            list(mapped),
            ["a", 1, "b", datetime.date(2021, 3, 5), datetime.time(12, 30, 43)],
        )

    def test_timestamp(self):
        # Datetimes just get the equivalent objects back
        index = pd.date_range(start=pd.Timestamp(2021, 1, 1), freq="D", periods=3)
        mapped = self.mapper(index)
        self.assertEqual(
            list(mapped),
            [
                pd.Timestamp("2021-01-01 00:00:00"),
                pd.Timestamp("2021-01-02 00:00:00"),
                pd.Timestamp("2021-01-03 00:00:00"),
            ],
        )

    def test_multi_index(self):
        # Multi index -> iterable of tuples, values unchanged
        intindex = pd.RangeIndex(2)
        objindex = pd.Index(
            [1, "a", datetime.date(2021, 3, 5), datetime.time(12, 30, 43)]
        )
        index = pd.MultiIndex.from_product([intindex, objindex])
        mapped = self.mapper(index)
        self.assertEqual(
            list(mapped),
            [
                (0, 1),
                (0, "a"),
                (0, datetime.date(2021, 3, 5)),
                (0, datetime.time(12, 30, 43)),
                (1, 1),
                (1, "a"),
                (1, datetime.date(2021, 3, 5)),
                (1, datetime.time(12, 30, 43)),
            ],
        )


class TestDefaultMapper(unittest.TestCase):
    # Default mapping maps to strings where necessary (for non-int data types)
    # and tidies up by removing disallowed characters.
    # https://www.gurobi.com/documentation/9.5/refman/lp_format.html
    # a name should not contain any of the characters +, -, *, ^, or :
    # default mapper replaces all these characters, and whitespace with underscores

    def setUp(self):
        self.mapper = create_mapper("default")

    def test_int(self):
        # Integer dtypes -> iterable of ints
        # There's no point converting in this case, no risk of illegal characters.
        index = pd.RangeIndex(10)
        mapped = self.mapper(index)
        self.assertEqual(list(mapped), list(range(10)))

    def test_object(self):
        # Object dtype -> iterable of strings
        index = pd.Index(
            ["a", 1, "a*b+c^d", datetime.date(2021, 3, 5), datetime.time(12, 30, 43)]
        )
        mapped = self.mapper(index)
        self.assertEqual(list(mapped), ["a", "1", "a_b_c_d", "2021_03_05", "12_30_43"])

    def test_whitespace(self):
        # All continuous whitespace replace with a single underscore
        index = pd.Index(["a  b", "c\td"])
        mapped = self.mapper(index)
        self.assertEqual(list(mapped), ["a_b", "c_d"])

    def test_timestamp(self):
        # For datetimes, use an iso-ish format that avoids special characters
        index = pd.date_range(
            start=pd.Timestamp(2021, 1, 18, 12, 32, 41),
            freq="D",
            periods=3,
            tz=datetime.timezone.utc,
        )
        mapped = self.mapper(index)
        self.assertEqual(
            list(mapped),
            ["2021_01_18T12_32_41", "2021_01_19T12_32_41", "2021_01_20T12_32_41"],
        )

    def test_timestamp_zoned(self):
        # For datetimes, use an iso-ish format that avoids special characters.
        # Don't show timezone, it's always going to be ambiguous for UTC-something.
        index = pd.date_range(
            start=pd.Timestamp(2021, 1, 18, 12, 32, 41),
            freq="D",
            periods=3,
            tz=datetime.timezone.utc,
        )
        mapped = self.mapper(index)
        self.assertEqual(
            list(mapped),
            ["2021_01_18T12_32_41", "2021_01_19T12_32_41", "2021_01_20T12_32_41"],
        )

    def test_multi_index(self):
        # Multi index -> iterable of tuples, string mapping for objects dtypes
        intindex = pd.RangeIndex(2)
        objindex = pd.Index(
            [1, "a*b+c^d", datetime.date(2021, 3, 5), datetime.time(12, 30, 43)]
        )
        index = pd.MultiIndex.from_product([intindex, objindex])
        mapped = self.mapper(index)
        self.assertEqual(
            list(mapped),
            [
                (0, "1"),
                (0, "a_b_c_d"),
                (0, "2021_03_05"),
                (0, "12_30_43"),
                (1, "1"),
                (1, "a_b_c_d"),
                (1, "2021_03_05"),
                (1, "12_30_43"),
            ],
        )


class TestCustomMapperCallable(unittest.TestCase):
    # Creating the mapper from a callable applies the callable to all levels in
    # the input series.

    def setUp(self):
        self.mapper = create_mapper(lambda index: index.strftime("%y%m%d"))

    def test_dates(self):
        index = pd.date_range(start=pd.Timestamp(2022, 6, 5), freq="D", periods=5)
        mapped = self.mapper(index)
        expected = ["220605", "220606", "220607", "220608", "220609"]
        self.assertEqual(list(mapped), expected)

    def test_multi_dates(self):
        index1 = pd.date_range(start=pd.Timestamp(2022, 6, 5), freq="D", periods=2)
        index2 = pd.date_range(start=pd.Timestamp(2022, 8, 9), freq="D", periods=2)
        index = pd.MultiIndex.from_product([index1, index2])
        mapped = self.mapper(index)
        expected = [
            ("220605", "220809"),
            ("220605", "220810"),
            ("220606", "220809"),
            ("220606", "220810"),
        ]
        self.assertEqual(list(mapped), expected)


class TestCustomMapperDict(unittest.TestCase):
    # Creating the mapper from a dict applies specific formatters to indexes
    # by name. Any unnamed index levels will have default formatting applied.

    def setUp(self):
        self.dtindex = pd.date_range(
            start=pd.Timestamp(2022, 6, 5), freq="D", periods=5, name="date"
        )
        strindex1 = pd.Index(["a  b", "c+d", "e", "f", "g"], name="str1")
        strindex2 = pd.Index(["a  b", "c+d", "e", "f", "g"], name="str2")

        self.index = pd.MultiIndex.from_arrays([self.dtindex, strindex1, strindex2])

    def test_by_level_name(self):
        # Named formatter applied to given level, default formatter otherwise
        mapper = create_mapper({"date": lambda index: index.strftime("%y%m%d")})
        mapped = mapper(self.index)

        expected = [
            ("220605", "a_b", "a_b"),
            ("220606", "c_d", "c_d"),
            ("220607", "e", "e"),
            ("220608", "f", "f"),
            ("220609", "g", "g"),
        ]
        self.assertEqual(list(mapped), expected)

    def test_by_level_nomapper(self):
        # None as a value implies no formatting to the given level
        mapper = create_mapper(
            {"date": lambda index: index.strftime("%y%m%d"), "str1": None}
        )
        mapped = mapper(self.index)

        expected = [
            ("220605", "a  b", "a_b"),
            ("220606", "c+d", "c_d"),
            ("220607", "e", "e"),
            ("220608", "f", "f"),
            ("220609", "g", "g"),
        ]
        self.assertEqual(list(mapped), expected)

    def test_disable_remaining(self):
        # None: None disables default mapping for any unnamed levels
        mapper = create_mapper(
            {"date": lambda index: index.strftime("%y%m%d"), None: None}
        )
        mapped = mapper(self.index)

        expected = [
            ("220605", "a  b", "a  b"),
            ("220606", "c+d", "c+d"),
            ("220607", "e", "e"),
            ("220608", "f", "f"),
            ("220609", "g", "g"),
        ]
        self.assertEqual(list(mapped), expected)

    def test_singleindex_named(self):
        # name -> callable mapping should still work on a single index,
        # if the name matches
        mapper = create_mapper(
            {"date": lambda index: index.strftime("%y%m%d"), None: None}
        )
        mapped = mapper(self.dtindex)

        self.assertIsInstance(mapped, pd.Index)
        self.assertNotIsInstance(mapped, pd.MultiIndex)

        expected = ["220605", "220606", "220607", "220608", "220609"]
        self.assertEqual(list(mapped), expected)
