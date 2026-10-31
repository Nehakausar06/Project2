# E-commerce Business Analytics — Project Report

## Objective

Build an end-to-end Python analytics solution that turns e-commerce order records into clean, filterable business insights. The solution follows the CodSoft Week 3 brief: data cleaning, exploratory data analysis, KPI calculations, customer/product/category/region/discount analysis, and an interactive dashboard.

## Dataset

The project creates its own deterministic synthetic dataset (seed `42`) with 3,600 order rows, customer IDs, product/category, quantity, unit price, discount, cost, sales, profit, order status, payment mode, and region. Orders span 2023–2025 so the dashboard can compare a selected year with the preceding year. The raw CSV includes a small number of deliberate data-quality issues; the clean CSV is the dashboard source.

## Method

The cleaning pipeline standardizes category/ID text, parses dates, converts numeric fields, removes duplicate order IDs, fixes invalid quantities, caps discounts, fills noncritical missing values, and drops records that lack a usable order ID, date, or price. It recalculates sales, profit, margin, calendar attributes, and discount bands. Unit tests cover reproducible data generation, cleaning, filters, KPI arithmetic, and zero-baseline comparisons.

## Analysis and deliverables

The Streamlit dashboard presents revenue, profit, orders, units, customers, margin, AOV, and repeat-customer rate. Interactive year/month/category/region filters update the overview and dedicated product, category, customer, regional/discount, and business-insights pages. Users can export filtered data or the complete clean dataset.

Findings are generated from the currently selected data in the dashboard rather than hard-coded to a particular filter selection. They identify the leading revenue category/product and region, compare regional performance, surface the lowest-margin discount band, and summarize repeat-customer activity. Recommendations are displayed alongside each finding.

### Full-sample snapshot

The generated clean sample contains 3,598 unique orders, ₹3.06 Cr revenue, ₹87.61 L profit, a 28.6% profit margin, 5,654 units, and 947 identified customers. The repeat-customer rate is 69.2%. Electronics accounts for 70.7% of sales; Laptop is the top product by sales at about ₹1.44 Cr. South is the highest-revenue region (₹82.1 L), while Central is the lowest (₹42.9 L). The 15–20% discount band has the lowest observed margin (16.6%). These are results from synthetic data, not real commercial performance.

## Interpretation and limitations

The dataset is simulated for training, so its patterns are illustrative and should not be treated as real market evidence. Sales/profit use the generated order-line values consistently across statuses; order status is analyzed separately. A Python dashboard is supplied in place of a Power BI `.pbix` because the requested implementation language is Python; starter DAX measures are included for optional Power BI recreation.
