import unittest

from pdcomfi.extension import GurobipyArray, GurobipyDtype


class TestGurobipyDtype(unittest.TestCase):
    def test_properties(self):
        assert GurobipyDtype.name == "gpobj"
        assert GurobipyDtype.construct_array_type() == GurobipyArray
