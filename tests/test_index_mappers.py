import datetime
from email.policy import default
import unittest

import pandas as pd

from gurobipy_pandas.index_mappers import default_mapper, map_index_entries


class TestNoMapper(unittest.TestCase):
    # Without a mapper, everything should pass through unchanged.

    def test_int(self):
        # Integer dtypes -> iterable of ints
        index = pd.RangeIndex(10)
        mapped = map_index_entries(index)
        self.assertEqual(list(mapped), list(range(10)))

    def test_object(self):
        # Object dtypes -> iterable of objects
        index = pd.Index(
            ["a", 1, "b", datetime.date(2021, 3, 5), datetime.time(12, 30, 43)]
        )
        mapped = map_index_entries(index)
        self.assertEqual(
            list(mapped),
            ["a", 1, "b", datetime.date(2021, 3, 5), datetime.time(12, 30, 43)],
        )

    def test_timestamp(self):
        # Datetimes just get the equivalent objects back
        index = pd.date_range(start=pd.Timestamp(2021, 1, 1), freq="D", periods=3)
        mapped = map_index_entries(index)
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
        mapped = map_index_entries(index)
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
    # Default mapper should map to strings where necessary (for non-int data types)
    # and tidy up by removing disallowed characters.
    # https://www.gurobi.com/documentation/9.5/refman/lp_format.html
    # a name should not contain any of the characters +, -, *, ^, or :
    # default mapper replaces all these characters, and whitespace with underscores

    def test_int(self):
        # Integer dtypes -> iterable of ints
        # There's no point converting in this case, no risk of illegal characters.
        index = pd.RangeIndex(10)
        mapped = map_index_entries(index, mapper=default_mapper)
        self.assertEqual(list(mapped), list(range(10)))

    def test_object(self):
        # Object dtype -> iterable of strings
        index = pd.Index(
            ["a", 1, "a*b+c^d", datetime.date(2021, 3, 5), datetime.time(12, 30, 43)]
        )
        mapped = map_index_entries(index, mapper=default_mapper)
        self.assertEqual(list(mapped), ["a", "1", "a_b_c_d", "2021_03_05", "12_30_43"])

    def test_whitespace(self):
        # All continuous whitespace replace with a single underscore
        index = pd.Index(["a  b", "c\td"])
        mapped = map_index_entries(index, mapper=default_mapper)
        self.assertEqual(list(mapped), ["a_b", "c_d"])

    def test_timestamp(self):
        # For datetimes, use an iso-ish format that avoids special characters
        index = pd.date_range(
            start=pd.Timestamp(2021, 1, 18, 12, 32, 41),
            freq="D",
            periods=3,
            tz=datetime.timezone.utc,
        )
        mapped = map_index_entries(index, mapper=default_mapper)
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
        mapped = map_index_entries(index, mapper=default_mapper)
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
        mapped = map_index_entries(index, mapper=default_mapper)
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
