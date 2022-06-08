import unittest

import gurobipy as gp
import numpy as np
import pandas as pd

from pdcomfi.extension import GurobipyArray, GurobipyDtype


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
