import unittest

import pandas as pd

from src.analytics import apply_filters, calculate_change, calculate_kpis
from src.data import clean_orders, generate_raw_data


class DataCleaningTests(unittest.TestCase):
    def test_generated_data_is_reproducible_and_cleaning_is_idempotent(self):
        raw_first = generate_raw_data(rows=120, seed=7)
        raw_second = generate_raw_data(rows=120, seed=7)
        pd.testing.assert_frame_equal(raw_first, raw_second)

        cleaned = clean_orders(raw_first)
        pd.testing.assert_frame_equal(cleaned, clean_orders(cleaned))
        self.assertEqual(cleaned["order_id"].nunique(), len(cleaned))
        self.assertTrue((cleaned["quantity"] > 0).all())
        self.assertTrue(cleaned["discount_pct"].between(0, 0.8).all())
        self.assertTrue(cleaned["order_date"].notna().all())
        self.assertTrue((cleaned["sales"] >= 0).all())
        self.assertTrue((cleaned["profit"] == (cleaned["sales"] - cleaned["cost"]).round(2)).all())
        self.assertTrue(
            set(cleaned["category"]).issubset(
                {"Electronics", "Fashion", "Home & Kitchen", "Beauty", "Books", "Other"}
            )
        )

    def test_missing_required_column_is_reported(self):
        with self.assertRaisesRegex(ValueError, "missing required columns"):
            clean_orders(pd.DataFrame({"order_id": ["ORD1"]}))


class DashboardAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.orders = clean_orders(generate_raw_data(rows=240, seed=12))

    def test_filters_can_be_combined(self):
        filtered = apply_filters(
            self.orders,
            year=2024,
            months=(1, 2, 3),
            categories=("Electronics",),
            regions=("North",),
            products=("Laptop",),
        )
        self.assertTrue((filtered["year"] == 2024).all())
        self.assertTrue(filtered["month"].isin((1, 2, 3)).all())
        self.assertTrue((filtered["category"] == "Electronics").all())
        self.assertTrue((filtered["region"] == "North").all())
        self.assertTrue((filtered["product"] == "Laptop").all())

    def test_empty_filter_returns_no_rows(self):
        filtered = apply_filters(self.orders, categories=())
        self.assertTrue(filtered.empty)

    def test_kpis_use_distinct_orders_and_consistent_totals(self):
        kpis = calculate_kpis(self.orders)
        self.assertEqual(kpis["orders"], self.orders["order_id"].nunique())
        self.assertEqual(kpis["units"], self.orders["quantity"].sum())
        self.assertAlmostEqual(kpis["revenue"], self.orders["sales"].sum())
        self.assertAlmostEqual(kpis["profit_margin_pct"], kpis["profit"] / kpis["revenue"] * 100)

    def test_percent_change_handles_zero_baseline(self):
        self.assertIsNone(calculate_change(100, 0))
        self.assertAlmostEqual(calculate_change(120, 100), 20)


if __name__ == "__main__":
    unittest.main()
