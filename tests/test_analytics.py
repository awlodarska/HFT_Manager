"""Financial rules and resilient handling of empty or incomplete records."""

from datetime import date
import unittest

import pandas as pd

from studio.analytics import (
    daily_revenue, expense_categories, filter_period, period_start, sold_products, summarize,
)


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.orders = pd.DataFrame([
            {"created_at": "2026-10-01T10:00:00", "status": "Zrealizowane", "net_amount": 100, "product": "Polo", "quantity": 3},
            {"created_at": "2026-10-03T10:00:00", "status": "Zrealizowane", "net_amount": 50, "product": "Polo", "quantity": 2},
            {"created_at": "2026-10-03T12:00:00", "status": "Nowe", "net_amount": 999, "product": "Bluza", "quantity": 20},
            {"created_at": "2026-10-02T10:00:00", "status": "Anulowane", "net_amount": 999, "product": "Bluza", "quantity": 20},
        ])
        self.expenses = pd.DataFrame([{"created_at": "2026-10-01", "category": "Nici", "gross_amount": 40}])

    def test_only_completed_orders_are_revenue_and_sales(self):
        self.assertEqual(summarize(self.orders, self.expenses), {
            "revenue": 150.0, "expenses": 40.0, "profit": 110.0, "in_progress": 1, "completed": 2,
        })
        self.assertEqual(sold_products(self.orders).to_dict("records"), [{"product": "Polo", "quantity": 5}])

    def test_daily_revenue_fills_non_selling_days(self):
        result = daily_revenue(self.orders)
        self.assertEqual(result["revenue"].tolist(), [100, 0, 50])
        self.assertEqual(result["date"].iloc[-1], pd.Timestamp("2026-10-03"))

    def test_period_boundaries_and_inclusive_filter(self):
        today = date(2026, 11, 15)
        self.assertEqual(period_start("Ten miesiąc", today), pd.Timestamp("2026-11-01"))
        self.assertEqual(period_start("Ten kwartał", today), pd.Timestamp("2026-10-01"))
        self.assertEqual(period_start("Ten rok", today), pd.Timestamp("2026-01-01"))
        self.assertIsNone(period_start("Cały okres", today))
        self.assertEqual(len(filter_period(self.orders, pd.Timestamp("2026-10-03"))), 2)
        self.assertEqual(len(self.orders), 4)
        with self.assertRaises(ValueError):
            period_start("Nieznany")

    def test_empty_frames_and_nan_never_produce_nan_totals(self):
        self.assertEqual(summarize(pd.DataFrame(), pd.DataFrame())["profit"], 0)
        self.assertTrue(sold_products(pd.DataFrame()).empty)
        self.assertTrue(daily_revenue(pd.DataFrame()).empty)
        self.assertTrue(expense_categories(pd.DataFrame()).empty)
        self.assertTrue(filter_period(pd.DataFrame(), None).empty)
        bad_orders = pd.DataFrame([{"status": "Zrealizowane", "net_amount": float("nan"), "quantity": None}])
        bad_expenses = pd.DataFrame([{"category": None, "gross_amount": float("inf")}])
        self.assertEqual(summarize(bad_orders, bad_expenses)["profit"], 0)
        self.assertTrue(daily_revenue(bad_orders).empty)
        self.assertEqual(expense_categories(bad_expenses).iloc[0].to_dict(), {"category": "Inne", "amount": 0})

    def test_invalid_dates_ignored_and_timezone_mixture_supported(self):
        frame = pd.DataFrame({"created_at": ["bad", None, "2026-10-03T12:00:00+02:00", "2026-10-03"]})
        self.assertEqual(len(filter_period(frame, pd.Timestamp("2026-10-03"))), 2)


if __name__ == "__main__":
    unittest.main()
