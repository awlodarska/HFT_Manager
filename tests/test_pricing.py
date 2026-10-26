import math
import unittest

from studio.pricing import estimate_price


class PricingTests(unittest.TestCase):
    def test_time_includes_setup_and_color_changes(self):
        result = estimate_price(12_000, 600, 4, 20, 40)
        self.assertEqual(result.production_minutes, 27)
        self.assertEqual(result.labor_cost, 40.5)
        self.assertEqual(result.total_cost, 62)
        self.assertAlmostEqual(result.suggested_price, 103.3333333333)
        self.assertAlmostEqual(result.profit / result.suggested_price, 0.4)

    def test_zero_margin_charges_cost_without_profit(self):
        result = estimate_price(0, 700, 0, 0, 0)
        self.assertEqual(result.suggested_price, result.total_cost)
        self.assertEqual(result.profit, 0)
        self.assertEqual(result.production_minutes, 5)

    def test_custom_overheads_are_applied(self):
        result = estimate_price(6000, 1000, 2, 12, 50, hourly_rate=120, setup_minutes=2, color_change_seconds=60, material_cost=3)
        self.assertEqual(result.production_minutes, 10)
        self.assertEqual(result.total_cost, 35)
        self.assertEqual(result.suggested_price, 70)

    def test_invalid_domains_are_rejected(self):
        base = dict(stitches=10_000, speed=600, color_changes=3, garment_cost=20, margin_percent=40)
        invalid = (("speed", 0), ("speed", math.nan), ("speed", math.inf), ("stitches", -1), ("stitches", 1.5), ("color_changes", -1), ("color_changes", True), ("garment_cost", -0.01), ("garment_cost", math.nan), ("margin_percent", 100), ("margin_percent", -1), ("hourly_rate", -1), ("material_cost", math.inf), ("setup_minutes", -1))
        for key, value in invalid:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                estimate_price(**(base | {key: value}))


if __name__ == "__main__":
    unittest.main()
