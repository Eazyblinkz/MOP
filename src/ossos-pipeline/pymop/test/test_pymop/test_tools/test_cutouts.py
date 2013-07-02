__author__ = "David Rusk <drusk@uvic.ca>"

import unittest

from hamcrest import assert_that, equal_to

from pymop.tools.cutouts import CutoutCalculator


class CutoutCalculatorTest(unittest.TestCase):
    def setUp(self):
        self.imgsize = (2000, 2000)

    def test_calc_cutout_internal(self):
        self.calculator = CutoutCalculator(100, 200)

        (x0, x1, y0, y1), _ = self.calculator.calc_cutout((500, 600), self.imgsize)
        assert_that(x0, equal_to(400))
        assert_that(x1, equal_to(600))
        assert_that(y0, equal_to(550))
        assert_that(y1, equal_to(650))

    def test_calc_cutout_internal_str(self):
        self.calculator = CutoutCalculator(100, 200)

        (x0, x1, y0, y1), _ = self.calculator.calc_cutout((500, 600), self.imgsize)
        assert_that(x0, equal_to(400))
        assert_that(x1, equal_to(600))
        assert_that(y0, equal_to(550))
        assert_that(y1, equal_to(650))

    def test_calc_cutout_internal_str_float(self):
        self.calculator = CutoutCalculator(100, 200)

        (x0, x1, y0, y1), _ = self.calculator.calc_cutout((500.00, 600.00), self.imgsize)
        assert_that(x0, equal_to(400))
        assert_that(x1, equal_to(600))
        assert_that(y0, equal_to(550))
        assert_that(y1, equal_to(650))

    def test_build_cutout_str(self):
        self.calculator = CutoutCalculator(100, 200)

        cutout_str, _ = self.calculator.build_cutout_str(15, (500, 600), self.imgsize)
        assert_that(cutout_str, equal_to("[15][400:600,550:650]"))

    def test_calc_cutout_internal_converter(self):
        self.calculator = CutoutCalculator(100, 200)

        _, converter = self.calculator.calc_cutout((500, 600), self.imgsize)
        assert_that(converter.convert((400, 550)), equal_to((0, 0)))
        assert_that(converter.convert((600, 550)), equal_to((200, 0)))
        assert_that(converter.convert((400, 650)), equal_to((0, 100)))
        assert_that(converter.convert((600, 650)), equal_to((200, 100)))
        assert_that(converter.convert((500, 600)), equal_to((100, 50)))

    def test_build_cutout_str_converter(self):
        self.calculator = CutoutCalculator(100, 200)

        _, converter = self.calculator.build_cutout_str(15, (500, 600), self.imgsize)
        assert_that(converter.convert((400, 550)), equal_to((0, 0)))
        assert_that(converter.convert((600, 550)), equal_to((200, 0)))
        assert_that(converter.convert((400, 650)), equal_to((0, 100)))
        assert_that(converter.convert((600, 650)), equal_to((200, 100)))
        assert_that(converter.convert((500, 600)), equal_to((100, 50)))

    def test_calc_cutout_boundary_x(self):
        self.calculator = CutoutCalculator(200, 200)

        (x0, x1, y0, y1), _ = self.calculator.calc_cutout((50, 400), self.imgsize)
        assert_that(x0, equal_to(1))
        assert_that(x1, equal_to(201))
        assert_that(y0, equal_to(300))
        assert_that(y1, equal_to(500))

    def test_calc_cutout_boundary_y(self):
        self.calculator = CutoutCalculator(200, 200)

        (x0, x1, y0, y1), _ = self.calculator.calc_cutout((400, 50), self.imgsize)
        assert_that(x0, equal_to(300))
        assert_that(x1, equal_to(500))
        assert_that(y0, equal_to(1))
        assert_that(y1, equal_to(201))

    def test_calc_cutout_boundary_x_converter(self):
        self.calculator = CutoutCalculator(200, 200)

        _, converter = self.calculator.build_cutout_str(15, (50, 400), self.imgsize)
        assert_that(converter.convert((51, 400)), equal_to((50, 100)))
        assert_that(converter.convert((1, 300)), equal_to((0, 0)))

    def test_calc_cutout_boundary_x_converter(self):
        self.calculator = CutoutCalculator(200, 200)

        _, converter = self.calculator.build_cutout_str(15, (400, 50), self.imgsize)
        assert_that(converter.convert((400, 51)), equal_to((100, 50)))
        assert_that(converter.convert((300, 1)), equal_to((0, 0)))

    def test_calc_cutout_boundary_xmax(self):
        self.imgsize = (200, 200)
        self.calculator = CutoutCalculator(100, 100)

        (x0, x1, y0, y1), _ = self.calculator.calc_cutout((175, 100), self.imgsize)
        assert_that(x0, equal_to(100))
        assert_that(x1, equal_to(200))
        assert_that(y0, equal_to(50))
        assert_that(y1, equal_to(150))

    def test_calc_cutout_boundary_ymax(self):
        self.imgsize = (200, 200)
        self.calculator = CutoutCalculator(100, 100)

        (x0, x1, y0, y1), _ = self.calculator.calc_cutout((100, 175), self.imgsize)
        assert_that(x0, equal_to(50))
        assert_that(x1, equal_to(150))
        assert_that(y0, equal_to(100))
        assert_that(y1, equal_to(200))

    def test_calc_cutout_boundary_xmax_converter(self):
        self.imgsize = (200, 200)
        self.calculator = CutoutCalculator(100, 100)

        _, converter = self.calculator.calc_cutout((175, 100), self.imgsize)
        assert_that(converter.convert((175, 100)), equal_to((75, 50)))
        assert_that(converter.convert((100, 50)), equal_to((0, 0)))
        assert_that(converter.convert((200, 150)), equal_to((100, 100)))

    def test_calc_cutout_boundary_ymax_converter(self):
        self.imgsize = (200, 200)
        self.calculator = CutoutCalculator(100, 100)

        _, converter = self.calculator.calc_cutout((100, 175), self.imgsize)
        assert_that(converter.convert((100, 175)), equal_to((50, 75)))
        assert_that(converter.convert((50, 100)), equal_to((0, 0)))
        assert_that(converter.convert((150, 200)), equal_to((100, 100)))

    def test_calc_cutout_inverted(self):
        self.calculator = CutoutCalculator(20, 20)

        (x0, x1, y0, y1), _ = self.calculator.calc_cutout((20, 20), (200, 200),
                                                          inverted=True)
        assert_that(x0, equal_to(190))
        assert_that(x1, equal_to(170))
        assert_that(y0, equal_to(190))
        assert_that(y1, equal_to(170))

    def test_calc_cutout_inverted_converter(self):
        self.calculator = CutoutCalculator(20, 20)

        _, converter = self.calculator.calc_cutout((20, 20), (200, 200),
                                                   inverted=True)
        assert_that(converter.convert((10, 10)), equal_to((0, 0)))
        assert_that(converter.convert((30, 10)), equal_to((20, 0)))
        assert_that(converter.convert((10, 30)), equal_to((0, 20)))
        assert_that(converter.convert((30, 30)), equal_to((20, 20)))
        assert_that(converter.convert((20, 20)), equal_to((10, 10)))

    def test_build_cutout_str_inverted(self):
        self.calculator = CutoutCalculator(20, 20)

        cutout_str, _ = self.calculator.build_cutout_str("10", (20, 20), (200, 200),
                                                         inverted=True)
        assert_that(cutout_str, equal_to("[10][190:170,190:170]"))


if __name__ == '__main__':
    unittest.main()