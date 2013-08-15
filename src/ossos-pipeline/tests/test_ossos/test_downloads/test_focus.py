__author__ = "David Rusk <drusk@uvic.ca>"

import unittest

from hamcrest import assert_that, close_to, has_length, equal_to
from ossos.downloads.cutouts.focus import SingletFocalPointCalculator, TripletFocalPointCalculator

from tests.base_tests import FileReadingTestCase
from ossos.astrom import AstromParser


def assert_tuples_almost_equal(actual, expected, delta=0.0000001):
    assert_that(actual[0], close_to(expected[0], delta))
    assert_that(actual[1], close_to(expected[1], delta))


class SingletFocalPointCalculatorTest(FileReadingTestCase):
    def setUp(self):
        astrom_data = AstromParser().parse(
            self.get_abs_path("data/1616681p22.measure3.cands.astrom"))
        self.source = astrom_data.get_sources()[0]
        self.reading0 = self.source.get_reading(0)
        self.reading1 = self.source.get_reading(1)
        self.reading2 = self.source.get_reading(2)

        self.undertest = SingletFocalPointCalculator(self.source)

    def test_get_focal_point_first_reading(self):
        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading0),
            (583.42, 408.46))

    def test_get_focal_point_second_reading(self):
        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading1),
            (586.18, 408.63))

    def test_get_focal_point_third_reading(self):
        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading2),
            (587.80, 407.98))


class TripletFocalPointCalculatorTest(FileReadingTestCase):
    def setUp(self):
        astrom_data = AstromParser().parse(
            self.get_abs_path("data/1616681p22.measure3.cands.astrom"))
        self.source = astrom_data.get_sources()[0]
        self.reading0 = self.source.get_reading(0)
        self.reading1 = self.source.get_reading(1)
        self.reading2 = self.source.get_reading(2)

        self.undertest = TripletFocalPointCalculator(self.source)

    def test_calculate_focal_points(self):
        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading0, 0),
            (560.06, 406.51))

        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading1, 0),
            (583.42, 408.46))

        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading2, 0),
            (608.48, 407.17))

        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading0, 1),
            (562.82, 406.68))

        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading1, 1),
            (586.18, 408.63))

        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading2, 1),
            (611.24, 407.34))

        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading0, 2),
            (564.44, 406.03))

        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading1, 2),
            (587.80, 407.98))

        assert_tuples_almost_equal(
            self.undertest.calculate_focal_point(self.reading2, 2),
            (612.86, 406.69))


if __name__ == '__main__':
    unittest.main()
