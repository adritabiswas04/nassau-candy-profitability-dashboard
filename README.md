# Product Line Profitability & Margin Performance Analysis for Nassau Candy Distributor

This project was prepared for the Unified Mentor requirement. It analyzes whether products that sell well are also profitable, compares division-level margin performance, identifies margin-risk products, and provides an interactive Streamlit dashboard.

## Project deliverables

- `app.py` - Streamlit dashboard with required modules and user controls
- `data/Nassau Candy Distributor.csv` - original dataset
- `data/cleaned_nassau_candy_distributor.csv` - cleaned dataset with KPI and factory fields
- `outputs/product_profitability.csv` - product-level KPI table
- `outputs/division_performance.csv` - division-level KPI table
- `outputs/factory_performance.csv` - factory-level KPI table
- `outputs/product_factory_mapping.csv` - product-factory correlation table from the brief
- `outputs/margin_risk_flags.csv` - products requiring margin review
- `outputs/pareto_revenue.csv` - 80% revenue concentration analysis
- `outputs/pareto_profit.csv` - 80% profit concentration analysis
- `docs/Research_Paper_Nassau_Candy_Profitability.docx` and `.pdf`
- `docs/Executive_Summary_Nassau_Candy_Profitability.docx` and `.pdf`
- `notebooks/Nassau_Candy_EDA.ipynb` - reproducible EDA notebook

## How to run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Dashboard modules included

1. Product Profitability Overview
   - Product-level margin leaderboard
   - Profit contribution charts
   - Product search

2. Division Performance Dashboard
   - Revenue vs profit comparison
   - Margin distribution by division

3. Cost vs Margin Diagnostics
   - Cost-sales scatter plots
   - Margin risk flags

4. Profit Concentration Analysis
   - Pareto charts
   - Dependency indicators

5. Factory View
   - Factory profitability and product-factory correlation based on the project brief

## User capabilities included

- Date range selector
- Division filter
- Margin threshold slider
- Product search
- Downloadable filtered data and risk flags

## Key results

- Total sales: $141,783.63
- Total gross profit: $93,442.80
- Overall gross margin: 65.91%
- Products generating more than 80% revenue: 5
- Products generating more than 80% profit: 5
- Highest gross-profit product: Wonka Bar -Scrumdiddlyumptious
- Highest margin-risk product: Kazookles

## Notes

The raw file labels `Fizzy Lifting Drinks` under Sugar, but the project brief maps it to the Other division and Sugar Shack factory. The cleaned dataset and dashboard use the project brief mapping so the submission aligns with the provided requirements.
