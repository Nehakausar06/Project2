# E-commerce Business Analytics Dashboard

A Python implementation of the CodSoft Week 3 internship brief. It generates an original, reproducible e-commerce dataset, demonstrates data cleaning and exploratory analysis, and provides an interactive dashboard for revenue, profit, products, customers, categories, regions, and discounts.

The brief illustrates a Power BI dashboard. This project recreates its interactive analysis in a Python/Streamlit dashboard; it does not produce a Power BI `.pbix` file. [`powerbi_measures.dax`](./powerbi_measures.dax) contains equivalent starter measures for a Power BI handoff.

## Run on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`). Use the sidebar to select a year, months, categories, regions, or products. The filtered records can be downloaded as a CSV. To run the tests:

```powershell
py -m unittest discover -s tests -v
```

## Project contents

| Path | Purpose |
|---|---|
| `app.py` | Interactive dashboard and visualizations |
| `src/data.py` | Reproducible sample-data generation, cleaning, and loading |
| `src/analytics.py` | Reusable filters, KPI calculations, and business insights |
| `data/ecommerce_orders_raw.csv` | Synthetic source data with intentional quality issues |
| `data/ecommerce_orders.csv` | Clean dataset used by the dashboard |
| `scripts/generate_data.py` | Regenerates both sample CSV files |
| `tests/test_analytics.py` | Data-cleaning, filters, and KPI tests |
| `powerbi_measures.dax` | Starter measures for a Power BI handoff |

Regenerate the deterministic sample files with:

```powershell
py scripts\generate_data.py
```

## Dashboard pages

- **Overview:** revenue/profit/order/customer KPIs, year-over-year comparisons, monthly sales, category mix, best-selling products, region, payment mode, order status, and profit-versus-revenue.
- **Products:** top products by sales and profit, units sold, order counts, and margins.
- **Categories:** category revenue, profit, units, orders, and margin comparison.
- **Customers:** top customers, spending, order frequency, and customer segments.
- **Regions & discounts:** regional performance and revenue/profit across discount bands.
- **Data quality:** source-versus-clean checks, examples of raw issues, and clean data export.
- **Business insights:** filter-aware findings and practical recommendations.

## Data dictionary

One row represents one order. The sample contains 3,600 generated orders spanning 2023–2025; two duplicate rows are added to the raw source to demonstrate deduplication.

| Column | Meaning |
|---|---|
| `order_id` | Unique order identifier |
| `order_date`, `year`, `month`, `month_name`, `quarter` | Purchase date and calendar breakdown |
| `customer_id` | Synthetic customer identifier |
| `product`, `category` | Item and merchandise category |
| `quantity` | Units purchased; cleaned to a positive integer |
| `unit_price` | Price per unit in Indian rupees before discount |
| `discount_pct`, `discount_range` | Discount fraction and analysis band |
| `sales` | `unit_price × quantity × (1 − discount_pct)` |
| `cost` | Total cost of goods sold |
| `profit` | `sales − cost` |
| `profit_margin_pct` | `profit ÷ sales × 100` |
| `region` | Synthetic Indian sales region |
| `payment_mode` | COD, online, card, or wallet |
| `order_status` | Delivered, returned, cancelled, or pending |

`profit_margin_pct` is stored in percentage points (for example, `18.5` means 18.5%). Revenue and profit use the generated order-line sales consistently across statuses; status is shown separately for context.

## Cleaning and analysis workflow

1. Generate deterministic synthetic order records.
2. Detect and remove duplicate order IDs.
3. Parse dates, coerce numeric fields, and drop rows without a valid date, ID, or positive price.
4. Standardize IDs and category names; fill noncritical missing values.
5. Correct nonpositive quantities and cap invalid discount percentages.
6. Recalculate sales, profit, margin, and calendar/discount analysis fields.
7. Explore KPI and category/product/customer/region/discount patterns through dashboard filters.

## KPI definitions

- **Total revenue:** sum of `sales`.
- **Total profit:** sum of `profit`.
- **Total orders:** distinct order IDs.
- **Units sold:** sum of `quantity`.
- **Total customers:** distinct identified customers.
- **Profit margin:** total profit ÷ total revenue × 100.
- **Average order value:** total revenue ÷ distinct orders.
- **Repeat-customer rate:** identified customers with more than one order ÷ identified customers × 100.

## Notes

- All records and customer identifiers are synthetic; no customer or company data is included.
- Monetary amounts are INR. The dashboard renders large amounts in lakhs/crores.
- The app is designed to work offline after its Python dependencies are installed.
