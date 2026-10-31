"""Interactive Python dashboard for the synthetic e-commerce analytics project."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import apply_filters, build_business_insights, calculate_change, calculate_kpis
from src.data import CLEAN_DATA_PATH, DATA_DIR, RAW_DATA_PATH, clean_orders, load_orders, load_raw_orders


st.set_page_config(
    page_title="E-commerce Business Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTE = ("#5841d8", "#2979d8", "#1a9b70", "#f29b38", "#ed5577", "#8b69db")
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
CHART_CONFIG = {"displayModeBar": False, "responsive": True}


@st.cache_data(show_spinner=False)
def get_clean_orders() -> pd.DataFrame:
    if CLEAN_DATA_PATH.exists():
        return load_orders(CLEAN_DATA_PATH)
    if RAW_DATA_PATH.exists():
        return clean_orders(load_raw_orders(RAW_DATA_PATH))
    return load_orders()


def format_inr(value: float | int) -> str:
    value = float(value)
    if abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:,.2f} Cr"
    if abs(value) >= 100_000:
        return f"₹{value / 100_000:,.2f} L"
    return f"₹{value:,.0f}"


def style_figure(figure: go.Figure, height: int = 330) -> go.Figure:
    figure.update_layout(
        template="plotly_white",
        height=height,
        margin={"l": 8, "r": 8, "t": 24, "b": 8},
        font={"family": "Inter, Segoe UI, sans-serif", "color": "#24304b"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        colorway=list(PALETTE),
        hoverlabel={"bgcolor": "white"},
    )
    return figure


def show_empty(message: str = "No orders match the selected filters.") -> None:
    st.info(message)


def render_filters(orders: pd.DataFrame) -> tuple[dict[str, object], pd.DataFrame]:
    st.sidebar.markdown("## Dashboard filters")
    years = sorted(orders["year"].dropna().astype(int).unique().tolist(), reverse=True)
    year_choice = st.sidebar.selectbox("Year", ["All years", *years], index=0)
    year = None if year_choice == "All years" else int(year_choice)

    month_options = list(range(1, 13))
    months = st.sidebar.multiselect(
        "Month",
        options=month_options,
        default=month_options,
        format_func=lambda month: MONTHS[month - 1],
    )
    categories = sorted(orders["category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect("Category", categories, default=categories)
    regions = sorted(orders["region"].dropna().unique().tolist())
    selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
    products = sorted(orders["product"].dropna().unique().tolist())
    selected_products = st.sidebar.multiselect("Product", products, default=products)

    filtered = apply_filters(
        orders,
        year=year,
        months=months,
        categories=selected_categories,
        regions=selected_regions,
        products=selected_products,
    )
    selections = {
        "year": year,
        "months": months,
        "categories": selected_categories,
        "regions": selected_regions,
        "products": selected_products,
    }

    st.sidebar.divider()
    st.sidebar.caption(f"{len(filtered):,} of {len(orders):,} orders selected")
    st.sidebar.caption("Data: reproducible synthetic sample • INR")
    st.sidebar.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="ecommerce_orders_filtered.csv",
        mime="text/csv",
        width="stretch",
    )
    return selections, filtered


def render_kpis(
    filtered: pd.DataFrame,
    orders: pd.DataFrame,
    selections: dict[str, object],
) -> None:
    kpis = calculate_kpis(filtered)
    year = selections["year"]
    previous_kpis = None
    if isinstance(year, int):
        previous = apply_filters(
            orders,
            year=year - 1,
            months=selections["months"],
            categories=selections["categories"],
            regions=selections["regions"],
            products=selections["products"],
        )
        if not previous.empty:
            previous_kpis = calculate_kpis(previous)

    cards = (
        ("Total revenue", "revenue", format_inr),
        ("Total profit", "profit", format_inr),
        ("Total orders", "orders", lambda value: f"{value:,.0f}"),
        ("Units sold", "units", lambda value: f"{value:,.0f}"),
        ("Customers", "customers", lambda value: f"{value:,.0f}"),
        ("Profit margin", "profit_margin_pct", lambda value: f"{value:.1f}%"),
    )
    for column, (label, key, formatter) in zip(st.columns(len(cards)), cards):
        delta = None
        if previous_kpis is not None:
            change = calculate_change(float(kpis[key]), float(previous_kpis[key]))
            delta = f"{change:+.1f}% vs PY" if change is not None else "No prior-year baseline"
        column.metric(label, formatter(kpis[key]), delta=delta, delta_color="normal")
    st.caption(
        f"Average order value: **{format_inr(kpis['average_order_value'])}**"
        f"  ·  Repeat-customer rate: **{kpis['repeat_customer_rate_pct']:.1f}%**"
    )


def render_overview(filtered: pd.DataFrame, selections: dict[str, object]) -> None:
    if filtered.empty:
        show_empty()
        return

    monthly = (
        filtered.groupby("month", as_index=False)
        .agg(sales=("sales", "sum"), profit=("profit", "sum"))
        .sort_values("month")
    )
    monthly["month_name"] = monthly["month"].map(lambda month: MONTHS[month - 1])
    category_sales = (
        filtered.groupby("category", as_index=False, observed=True)["sales"]
        .sum()
        .sort_values("sales", ascending=False)
    )
    product_sales = (
        filtered.groupby("product", as_index=False, observed=True)["sales"]
        .sum()
        .nlargest(8, "sales")
        .sort_values("sales")
    )

    left, middle, right = st.columns((1.35, 1, 1))
    with left:
        st.subheader("Sales over time")
        figure = px.line(
            monthly,
            x="month_name",
            y="sales",
            markers=True,
            labels={"month_name": "Month", "sales": "Revenue (₹)"},
        )
        figure.update_traces(line={"color": PALETTE[0], "width": 3})
        st.plotly_chart(style_figure(figure), width="stretch", config=CHART_CONFIG)
    with middle:
        st.subheader("Revenue by category")
        figure = px.pie(category_sales, names="category", values="sales", hole=0.58)
        figure.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(style_figure(figure), width="stretch", config=CHART_CONFIG)
    with right:
        st.subheader("Top products by revenue")
        figure = px.bar(
            product_sales,
            x="sales",
            y="product",
            orientation="h",
            labels={"sales": "Revenue (₹)", "product": ""},
        )
        figure.update_traces(marker_color=PALETTE[0])
        st.plotly_chart(style_figure(figure), width="stretch", config=CHART_CONFIG)

    left, middle, right = st.columns((1, 1, 1.2))
    region_sales = filtered.groupby("region", as_index=False, observed=True)["sales"].sum().sort_values("sales")
    payment_orders = (
        filtered.groupby("payment_mode", as_index=False, observed=True)
        .agg(orders=("order_id", "nunique"))
        .sort_values("orders", ascending=False)
    )
    with left:
        st.subheader("Revenue by region")
        figure = px.bar(
            region_sales,
            x="sales",
            y="region",
            orientation="h",
            labels={"sales": "Revenue (₹)", "region": ""},
        )
        figure.update_traces(marker_color=PALETTE[1])
        st.plotly_chart(style_figure(figure, 290), width="stretch", config=CHART_CONFIG)
    with middle:
        st.subheader("Orders by payment mode")
        figure = px.pie(payment_orders, names="payment_mode", values="orders", hole=0.56)
        figure.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(style_figure(figure, 290), width="stretch", config=CHART_CONFIG)
    with right:
        st.subheader("Profit vs revenue")
        figure = px.scatter(
            filtered,
            x="sales",
            y="profit",
            color="category",
            hover_data=["product", "region"],
            labels={"sales": "Revenue (₹)", "profit": "Profit (₹)"},
            opacity=0.65,
        )
        st.plotly_chart(style_figure(figure, 290), width="stretch", config=CHART_CONFIG)

    status_counts = (
        filtered.groupby("order_status", as_index=False, observed=True)
        .agg(orders=("order_id", "nunique"))
        .sort_values("orders", ascending=False)
    )
    status_column, insight_column = st.columns((1, 2))
    with status_column:
        st.subheader("Orders by status")
        figure = px.pie(status_counts, names="order_status", values="orders", hole=0.55)
        figure.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(style_figure(figure, 285), width="stretch", config=CHART_CONFIG)
    with insight_column:
        st.subheader("Quick business insights")
        for insight in build_business_insights(filtered)[:4]:
            st.markdown(f"- {insight}")
        if isinstance(selections["year"], int):
            st.caption(f"Year-over-year comparison uses the same filters for {selections['year'] - 1}.")


def render_products(filtered: pd.DataFrame) -> None:
    st.subheader("Product performance")
    if filtered.empty:
        show_empty()
        return
    products = (
        filtered.groupby("product", as_index=False, observed=True)
        .agg(
            revenue=("sales", "sum"),
            profit=("profit", "sum"),
            units=("quantity", "sum"),
            orders=("order_id", "nunique"),
        )
    )
    products["profit_margin_pct"] = (
        products["profit"].div(products["revenue"].where(products["revenue"] != 0)).fillna(0) * 100
    )
    revenue_top, profit_top = st.columns(2)
    with revenue_top:
        st.markdown("#### Top 10 products by revenue")
        figure = px.bar(
            products.nlargest(10, "revenue").sort_values("revenue"),
            x="revenue",
            y="product",
            orientation="h",
            labels={"revenue": "Revenue (₹)", "product": ""},
        )
        figure.update_traces(marker_color=PALETTE[0])
        st.plotly_chart(style_figure(figure, 420), width="stretch", config=CHART_CONFIG)
    with profit_top:
        st.markdown("#### Top 10 products by profit")
        figure = px.bar(
            products.nlargest(10, "profit").sort_values("profit"),
            x="profit",
            y="product",
            orientation="h",
            labels={"profit": "Profit (₹)", "product": ""},
        )
        figure.update_traces(marker_color=PALETTE[2])
        st.plotly_chart(style_figure(figure, 420), width="stretch", config=CHART_CONFIG)

    st.markdown("#### Product scorecard")
    st.dataframe(
        products.sort_values("revenue", ascending=False).style.format({
            "revenue": "₹{:,.0f}",
            "profit": "₹{:,.0f}",
            "profit_margin_pct": "{:.1f}%",
            "units": "{:,.0f}",
            "orders": "{:,.0f}",
        }),
        width="stretch",
        hide_index=True,
    )


def render_categories(filtered: pd.DataFrame) -> None:
    st.subheader("Category analysis")
    if filtered.empty:
        show_empty()
        return
    categories = (
        filtered.groupby("category", as_index=False, observed=True)
        .agg(
            revenue=("sales", "sum"),
            profit=("profit", "sum"),
            units=("quantity", "sum"),
            orders=("order_id", "nunique"),
        )
    )
    categories["profit_margin_pct"] = (
        categories["profit"].div(categories["revenue"].where(categories["revenue"] != 0)).fillna(0) * 100
    )
    left, right = st.columns(2)
    with left:
        st.markdown("#### Revenue and profit by category")
        figure = px.bar(
            categories.melt(
                id_vars="category",
                value_vars=("revenue", "profit"),
                var_name="measure",
                value_name="amount",
            ),
            x="category",
            y="amount",
            color="measure",
            barmode="group",
            labels={"category": "", "amount": "Amount (₹)", "measure": ""},
        )
        st.plotly_chart(style_figure(figure, 370), width="stretch", config=CHART_CONFIG)
    with right:
        st.markdown("#### Profit margin by category")
        figure = px.bar(
            categories.sort_values("profit_margin_pct"),
            x="profit_margin_pct",
            y="category",
            orientation="h",
            labels={"profit_margin_pct": "Profit margin (%)", "category": ""},
            text="profit_margin_pct",
        )
        figure.update_traces(marker_color=PALETTE[2], texttemplate="%{text:.1f}%")
        st.plotly_chart(style_figure(figure, 370), width="stretch", config=CHART_CONFIG)
    st.dataframe(
        categories.sort_values("revenue", ascending=False).style.format({
            "revenue": "₹{:,.0f}",
            "profit": "₹{:,.0f}",
            "profit_margin_pct": "{:.1f}%",
            "units": "{:,.0f}",
            "orders": "{:,.0f}",
        }),
        width="stretch",
        hide_index=True,
    )


def render_customers(filtered: pd.DataFrame) -> None:
    st.subheader("Customer analysis")
    if filtered.empty:
        show_empty()
        return
    identified = filtered.loc[filtered["customer_id"] != "UNKNOWN"]
    if identified.empty:
        show_empty("Customer IDs are unavailable for the selected orders.")
        return

    customers = (
        identified.groupby("customer_id", as_index=False, observed=True)
        .agg(
            revenue=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            units=("quantity", "sum"),
        )
    )
    customers["average_order_value"] = customers["revenue"] / customers["orders"]
    repeat_rate = float((customers["orders"] > 1).mean() * 100) if not customers.empty else 0
    top = customers.nlargest(10, "revenue").sort_values("revenue")

    left, right = st.columns((1.15, 1))
    with left:
        st.metric("Repeat customer rate", f"{repeat_rate:.1f}%")
        st.markdown("#### Top 10 customers by revenue")
        figure = px.bar(
            top,
            x="revenue",
            y="customer_id",
            orientation="h",
            labels={"revenue": "Revenue (₹)", "customer_id": ""},
        )
        figure.update_traces(marker_color=PALETTE[4])
        st.plotly_chart(style_figure(figure, 420), width="stretch", config=CHART_CONFIG)
    with right:
        st.markdown("#### Orders by customer segment")
        customers["segment"] = "Occasional (1 order)"
        customers.loc[customers["orders"].between(2, 4), "segment"] = "Regular (2-4 orders)"
        customers.loc[customers["orders"] >= 5, "segment"] = "High frequency (5+)"
        segments = customers.groupby("segment", as_index=False).agg(customers=("customer_id", "nunique"))
        figure = px.pie(segments, names="segment", values="customers", hole=0.55)
        figure.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(style_figure(figure, 360), width="stretch", config=CHART_CONFIG)
        st.markdown("#### Customer scorecard")
        st.dataframe(
            customers.nlargest(10, "revenue").sort_values("revenue", ascending=False).style.format({
                "revenue": "₹{:,.0f}",
                "profit": "₹{:,.0f}",
                "average_order_value": "₹{:,.0f}",
                "orders": "{:,.0f}",
                "units": "{:,.0f}",
            }),
            width="stretch",
            hide_index=True,
        )


def render_regions_discounts(filtered: pd.DataFrame) -> None:
    st.subheader("Regional sales and discount effectiveness")
    if filtered.empty:
        show_empty()
        return
    regions = (
        filtered.groupby("region", as_index=False, observed=True)
        .agg(
            revenue=("sales", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
        )
        .sort_values("revenue", ascending=False)
    )
    discount = (
        filtered.groupby("discount_range", as_index=False, observed=True)
        .agg(revenue=("sales", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
    )
    discount["profit_margin_pct"] = (
        discount["profit"].div(discount["revenue"].where(discount["revenue"] != 0)).fillna(0) * 100
    )
    regional, discounts = st.columns(2)
    with regional:
        st.markdown("#### Regional performance")
        figure = px.bar(
            regions.sort_values("revenue"),
            x="revenue",
            y="region",
            orientation="h",
            color="profit",
            color_continuous_scale="Purples",
            labels={"revenue": "Revenue (₹)", "region": "", "profit": "Profit (₹)"},
        )
        st.plotly_chart(style_figure(figure, 380), width="stretch", config=CHART_CONFIG)
        st.dataframe(
            regions.style.format({
                "revenue": "₹{:,.0f}",
                "profit": "₹{:,.0f}",
                "orders": "{:,.0f}",
                "customers": "{:,.0f}",
            }),
            width="stretch",
            hide_index=True,
        )
    with discounts:
        st.markdown("#### Revenue, profit and discount band")
        figure = go.Figure()
        figure.add_bar(
            x=discount["discount_range"],
            y=discount["revenue"],
            name="Revenue",
            marker_color=PALETTE[1],
        )
        figure.add_scatter(
            x=discount["discount_range"],
            y=discount["profit"],
            name="Profit",
            mode="lines+markers",
            line={"color": PALETTE[2], "width": 3},
            yaxis="y2",
        )
        figure.update_layout(
            yaxis={"title": "Revenue (₹)"},
            yaxis2={"title": "Profit (₹)", "overlaying": "y", "side": "right"},
            barmode="group",
        )
        st.plotly_chart(style_figure(figure, 380), width="stretch", config=CHART_CONFIG)
        st.markdown("#### Profit margin by discount band")
        figure = px.bar(
            discount,
            x="discount_range",
            y="profit_margin_pct",
            labels={"discount_range": "Discount band", "profit_margin_pct": "Profit margin (%)"},
            text="profit_margin_pct",
        )
        figure.update_traces(marker_color=PALETTE[2], texttemplate="%{text:.1f}%")
        st.plotly_chart(style_figure(figure, 270), width="stretch", config=CHART_CONFIG)


def render_data_quality(orders: pd.DataFrame) -> None:
    st.subheader("Data quality and cleaning")
    raw = load_raw_orders(RAW_DATA_PATH)
    raw_duplicates = int(raw["order_id"].duplicated().sum())
    raw_missing = int(raw.isna().sum().sum())
    cleaned = clean_orders(raw)
    summary = pd.DataFrame(
        [
            {"Check": "Source rows", "Before": f"{len(raw):,}", "After": f"{len(cleaned):,}"},
            {"Check": "Duplicate order IDs", "Before": f"{raw_duplicates:,}", "After": f"{cleaned['order_id'].duplicated().sum():,}"},
            {"Check": "Missing cells", "Before": f"{raw_missing:,}", "After": f"{int(cleaned.isna().sum().sum()):,}"},
            {"Check": "Invalid order dates", "Before": f"{pd.to_datetime(raw['order_date'], errors='coerce', format='mixed').isna().sum():,}", "After": "0"},
            {"Check": "Negative / zero quantities", "Before": f"{(pd.to_numeric(raw['quantity'], errors='coerce') <= 0).sum():,}", "After": f"{(cleaned['quantity'] <= 0).sum():,}"},
        ]
    )
    st.dataframe(summary, width="stretch", hide_index=True)
    st.markdown(
        "The sample intentionally includes duplicate orders, missing values, inconsistent category "
        "capitalization, invalid dates, an invalid quantity, and an out-of-range discount."
    )
    with st.expander("Preview original (uncleaned) source rows"):
        st.dataframe(raw.head(25), width="stretch", hide_index=True)
    with st.expander("Preview cleaned analysis dataset"):
        st.dataframe(cleaned.head(25), width="stretch", hide_index=True)
        st.download_button(
            "Download complete clean dataset",
            data=cleaned.to_csv(index=False).encode("utf-8"),
            file_name="ecommerce_orders.csv",
            mime="text/csv",
        )
    st.caption(f"Source file: {Path(RAW_DATA_PATH).name}  ·  Clean file: {Path(CLEAN_DATA_PATH).name}")


def render_business_insights(filtered: pd.DataFrame) -> None:
    st.subheader("Business insights and recommendations")
    if filtered.empty:
        show_empty()
        return
    kpis = calculate_kpis(filtered)
    revenue, margin, repeat = st.columns(3)
    revenue.metric("Selected revenue", format_inr(kpis["revenue"]))
    margin.metric("Profit margin", f"{kpis['profit_margin_pct']:.1f}%")
    repeat.metric("Repeat-customer rate", f"{kpis['repeat_customer_rate_pct']:.1f}%")
    for insight in build_business_insights(filtered):
        st.markdown(f"- {insight}")
    st.markdown("#### Discount bands")
    discount = (
        filtered.groupby("discount_range", as_index=False, observed=True)
        .agg(revenue=("sales", "sum"), profit=("profit", "sum"), orders=("order_id", "nunique"))
    )
    discount["profit_margin_pct"] = (
        discount["profit"].div(discount["revenue"].where(discount["revenue"] != 0)).fillna(0) * 100
    )
    st.dataframe(
        discount.style.format({
            "revenue": "₹{:,.0f}",
            "profit": "₹{:,.0f}",
            "profit_margin_pct": "{:.1f}%",
            "orders": "{:,.0f}",
        }),
        width="stretch",
        hide_index=True,
    )


def main() -> None:
    orders = get_clean_orders()
    st.sidebar.title("🛒 E-commerce analytics")
    page = st.sidebar.radio(
        "Explore",
        (
            "Overview",
            "Products",
            "Categories",
            "Customers",
            "Regions & discounts",
            "Data quality",
            "Business insights",
        ),
    )
    selections, filtered = render_filters(orders)

    st.markdown(
        "<div class='hero'><span class='eyebrow'>CODSOFT · DATA ANALYTICS PROJECT</span>"
        "<h1>E-commerce Business Analytics</h1>"
        "<p>Explore sales, profitability, products, customers, and regional performance.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <style>
        .hero { padding: 1.25rem 1.5rem; border-radius: 16px; margin-bottom: 1.1rem;
                background: linear-gradient(115deg, #f0edff 0%, #fff 62%, #fff2f5 100%);
                border: 1px solid #e6e1f8; }
        .hero h1 { margin: .25rem 0; color: #20204c; font-size: 2rem; }
        .hero p { color: #596078; margin: .25rem 0 0; }
        .eyebrow { color: #5841d8; font-size: .75rem; font-weight: 700; letter-spacing: .12em; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if page != "Data quality":
        render_kpis(filtered, orders, selections)
        st.divider()

    if page == "Overview":
        render_overview(filtered, selections)
    elif page == "Products":
        render_products(filtered)
    elif page == "Categories":
        render_categories(filtered)
    elif page == "Customers":
        render_customers(filtered)
    elif page == "Regions & discounts":
        render_regions_discounts(filtered)
    elif page == "Data quality":
        render_data_quality(orders)
    else:
        render_business_insights(filtered)

    st.divider()
    st.caption(
        "Built with Python, pandas, Plotly, and Streamlit. Dataset is synthetic and for learning purposes."
    )


if __name__ == "__main__":
    main()
