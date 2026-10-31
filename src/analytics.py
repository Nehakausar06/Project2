"""Reusable filtering, KPI, and insight calculations."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def apply_filters(
    orders: pd.DataFrame,
    *,
    year: int | None = None,
    months: Iterable[int] | None = None,
    categories: Iterable[str] | None = None,
    regions: Iterable[str] | None = None,
    products: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Apply dashboard filters without changing the source dataframe."""
    filtered = orders
    if year is not None:
        filtered = filtered.loc[filtered["year"] == year]
    for column, values in (
        ("month", months),
        ("category", categories),
        ("region", regions),
        ("product", products),
    ):
        if values is not None:
            selected = list(values)
            if not selected:
                return filtered.iloc[0:0].copy()
            filtered = filtered.loc[filtered[column].isin(selected)]
    return filtered.copy()


def calculate_kpis(orders: pd.DataFrame) -> dict[str, float | int]:
    """Calculate the business metrics displayed throughout the dashboard."""
    order_count = int(orders["order_id"].nunique())
    customer_count = int(orders.loc[orders["customer_id"] != "UNKNOWN", "customer_id"].nunique())
    sales = float(orders["sales"].sum())
    profit = float(orders["profit"].sum())
    quantity = int(orders["quantity"].sum())
    customer_orders = orders.loc[orders["customer_id"] != "UNKNOWN"].groupby("customer_id")["order_id"].nunique()

    return {
        "revenue": sales,
        "profit": profit,
        "orders": order_count,
        "units": quantity,
        "customers": customer_count,
        "profit_margin_pct": profit / sales * 100 if sales else 0.0,
        "average_order_value": sales / order_count if order_count else 0.0,
        "repeat_customer_rate_pct": (
            float((customer_orders > 1).sum()) / len(customer_orders) * 100
            if len(customer_orders)
            else 0.0
        ),
    }


def calculate_change(current: float, previous: float) -> float | None:
    """Return percent change, or None when a baseline cannot be compared."""
    if previous == 0:
        return None
    return (current - previous) / abs(previous) * 100


def build_business_insights(orders: pd.DataFrame) -> list[str]:
    """Summarize measurable patterns and plain-language recommendations."""
    if orders.empty:
        return ["No orders match the selected filters. Expand the filters to see insights."]

    insights: list[str] = []
    category_sales = orders.groupby("category", observed=True)["sales"].sum().sort_values(ascending=False)
    if not category_sales.empty and category_sales.sum() > 0:
        leader = category_sales.index[0]
        share = category_sales.iloc[0] / category_sales.sum() * 100
        insights.append(
            f"{leader} leads sales with {share:.1f}% of filtered revenue. "
            "Prioritize inventory availability and promotion planning for this category."
        )

    product_sales = orders.groupby("product", observed=True)["sales"].sum().sort_values(ascending=False)
    if not product_sales.empty:
        insights.append(
            f"{product_sales.index[0]} is the top product by revenue "
            f"({product_sales.iloc[0]:,.0f} in the selected period)."
        )

    region_sales = orders.groupby("region", observed=True)["sales"].sum().sort_values(ascending=False)
    if len(region_sales) > 1:
        insights.append(
            f"{region_sales.index[0]} is the strongest region by revenue; "
            f"{region_sales.index[-1]} is the lowest. Compare local demand and fulfillment costs "
            "before shifting regional budgets."
        )

    discount_summary = orders.groupby("discount_range", observed=True).agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
    )
    discount_summary = discount_summary.loc[discount_summary["sales"] > 0]
    if not discount_summary.empty:
        discount_summary["margin_pct"] = discount_summary["profit"] / discount_summary["sales"] * 100
        lowest_margin = discount_summary["margin_pct"].idxmin()
        insights.append(
            f"The {lowest_margin} discount band has the lowest profit margin "
            f"({discount_summary.loc[lowest_margin, 'margin_pct']:.1f}%). "
            "Review whether the extra sales justify discounts in this band."
        )

    customer_orders = orders.loc[orders["customer_id"] != "UNKNOWN"].groupby("customer_id")["order_id"].nunique()
    if len(customer_orders):
        repeat_rate = float((customer_orders > 1).sum()) / len(customer_orders) * 100
        insights.append(
            f"{repeat_rate:.1f}% of identified customers placed more than one order "
            "in this selection; consider retention campaigns for one-time buyers."
        )

    return insights
