import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Nassau Candy Profitability Dashboard",
    page_icon="🍫",
    layout="wide"
)

PRODUCT_FACTORY_MAP = {
    "Wonka Bar - Nutty Crunch Surprise": ("Chocolate", "Lot's O' Nuts", 32.881893, -111.768036),
    "Wonka Bar - Fudge Mallows": ("Chocolate", "Lot's O' Nuts", 32.881893, -111.768036),
    "Wonka Bar -Scrumdiddlyumptious": ("Chocolate", "Lot's O' Nuts", 32.881893, -111.768036),
    "Wonka Bar - Milk Chocolate": ("Chocolate", "Wicked Choccy's", 32.076176, -81.088371),
    "Wonka Bar - Triple Dazzle Caramel": ("Chocolate", "Wicked Choccy's", 32.076176, -81.088371),
    "Laffy Taffy": ("Sugar", "Sugar Shack", 48.11914, -96.18115),
    "SweeTARTS": ("Sugar", "Sugar Shack", 48.11914, -96.18115),
    "Nerds": ("Sugar", "Sugar Shack", 48.11914, -96.18115),
    "Fun Dip": ("Sugar", "Sugar Shack", 48.11914, -96.18115),
    "Fizzy Lifting Drinks": ("Other", "Sugar Shack", 48.11914, -96.18115),
    "Everlasting Gobstopper": ("Sugar", "Secret Factory", 41.446333, -90.565487),
    "Hair Toffee": ("Sugar", "The Other Factory", 35.1175, -89.971107),
    "Lickable Wallpaper": ("Other", "Secret Factory", 41.446333, -90.565487),
    "Wonka Gum": ("Other", "Secret Factory", 41.446333, -90.565487),
    "Kazookles": ("Other", "The Other Factory", 35.1175, -89.971107),
}

@st.cache_data
def load_data(uploaded_file=None):
    default_path = Path("Nassau Candy Distributor.csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv(default_path)

    df.columns = [c.strip() for c in df.columns]
    for col in ["Order Date", "Ship Date"]:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
    for col in ["Sales", "Units", "Gross Profit", "Cost"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["Ship Mode", "Country/Region", "City", "State/Province", "Division", "Region", "Product ID", "Product Name"]:
        df[col] = df[col].astype(str).str.strip()

    df["Original Division"] = df["Division"]
    df["Division"] = df["Product Name"].map(lambda x: PRODUCT_FACTORY_MAP.get(x, (np.nan, np.nan, np.nan, np.nan))[0]).fillna(df["Division"])
    df["Factory"] = df["Product Name"].map(lambda x: PRODUCT_FACTORY_MAP.get(x, (np.nan, np.nan, np.nan, np.nan))[1])
    df["Factory Latitude"] = df["Product Name"].map(lambda x: PRODUCT_FACTORY_MAP.get(x, (np.nan, np.nan, np.nan, np.nan))[2])
    df["Factory Longitude"] = df["Product Name"].map(lambda x: PRODUCT_FACTORY_MAP.get(x, (np.nan, np.nan, np.nan, np.nan))[3])

    before = len(df)
    df = df.dropna(subset=["Order Date", "Ship Date", "Sales", "Units", "Gross Profit", "Cost"])
    df = df[(df["Sales"] > 0) & (df["Units"] > 0) & (df["Cost"] >= 0)].copy()
    removed = before - len(df)

    df["Gross Margin (%)"] = df["Gross Profit"] / df["Sales"] * 100
    df["Profit per Unit"] = df["Gross Profit"] / df["Units"]
    df["Cost to Sales (%)"] = df["Cost"] / df["Sales"] * 100
    df["Ship Lead Time (Days)"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Order Month"] = df["Order Date"].dt.to_period("M").astype(str)
    return df, before, removed

def product_metrics(data):
    agg = data.groupby(["Product ID", "Product Name", "Division", "Factory"], dropna=False, as_index=False).agg(
        Sales=("Sales", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Cost=("Cost", "sum"),
        Orders=("Order ID", "nunique"),
    )
    agg["Gross Margin (%)"] = agg["Gross_Profit"] / agg["Sales"] * 100
    agg["Profit per Unit"] = agg["Gross_Profit"] / agg["Units"]
    agg["Revenue Contribution (%)"] = agg["Sales"] / agg["Sales"].sum() * 100
    agg["Profit Contribution (%)"] = agg["Gross_Profit"] / agg["Gross_Profit"].sum() * 100
    agg["Cost to Sales (%)"] = agg["Cost"] / agg["Sales"] * 100

    monthly = data.groupby(["Product Name", "Order Month"], as_index=False).agg(Sales=("Sales", "sum"), Gross_Profit=("Gross Profit", "sum"))
    monthly["Monthly Margin (%)"] = monthly["Gross_Profit"] / monthly["Sales"] * 100
    vol = monthly.groupby("Product Name")["Monthly Margin (%)"].std(ddof=0).reset_index().rename(columns={"Monthly Margin (%)": "Margin Volatility"})
    agg = agg.merge(vol, on="Product Name", how="left")
    return agg

def division_metrics(data):
    agg = data.groupby("Division", as_index=False).agg(
        Sales=("Sales", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Cost=("Cost", "sum"),
        Products=("Product Name", "nunique"),
        Orders=("Order ID", "nunique"),
    )
    agg["Gross Margin (%)"] = agg["Gross_Profit"] / agg["Sales"] * 100
    agg["Profit per Unit"] = agg["Gross_Profit"] / agg["Units"]
    agg["Revenue Share (%)"] = agg["Sales"] / agg["Sales"].sum() * 100
    agg["Profit Share (%)"] = agg["Gross_Profit"] / agg["Gross_Profit"].sum() * 100
    agg["Cost to Sales (%)"] = agg["Cost"] / agg["Sales"] * 100
    return agg

def add_risk_flags(product_df, portfolio_margin):
    risk = product_df.copy()
    median_sales = risk["Sales"].median()
    flags = []
    for _, row in risk.iterrows():
        current = []
        if row["Gross Margin (%)"] < 30:
            current.append("Critical low margin")
        elif row["Gross Margin (%)"] < 50:
            current.append("Low margin")
        elif row["Gross Margin (%)"] < portfolio_margin:
            current.append("Below portfolio margin")
        if row["Sales"] >= median_sales and row["Gross Margin (%)"] < portfolio_margin:
            current.append("High-sales / below-margin")
        if row["Profit Contribution (%)"] < 0.25:
            current.append("Low profit contribution")
        if row["Cost to Sales (%)"] > 50:
            current.append("Cost-heavy")
        flags.append("; ".join(current) if current else "Healthy")
    risk["Margin Risk Flag"] = flags
    risk["Recommended Action"] = np.select(
        [risk["Margin Risk Flag"].str.contains("Critical low margin"),
         risk["Margin Risk Flag"].str.contains("High-sales / below-margin"),
         risk["Margin Risk Flag"].str.contains("Low profit contribution"),
         risk["Margin Risk Flag"].eq("Healthy")],
        ["Immediate repricing or cost renegotiation",
         "Review pricing, promotion depth, and supplier cost",
         "Portfolio rationalization / demand validation",
         "Protect supply and maintain pricing discipline"],
        default="Monitor margin trend"
    )
    return risk

def pareto_table(product_df, metric):
    df = product_df.sort_values(metric, ascending=False).copy()
    total = df[metric].sum()
    df[f"{metric} Share (%)"] = df[metric] / total * 100
    df[f"Cumulative {metric} Share (%)"] = df[f"{metric} Share (%)"].cumsum()
    df["Rank"] = range(1, len(df) + 1)
    return df

def money(x):
    return f"${x:,.2f}"

def pct(x):
    return f"{x:,.2f}%"

st.title("Product Line Profitability & Margin Performance Analysis")
st.caption("Nassau Candy Distributor | Unified Mentor Project Dashboard")

uploaded_file = st.sidebar.file_uploader("Optional: upload updated Nassau Candy CSV", type=["csv"])
df, original_rows, removed_rows = load_data(uploaded_file)

st.sidebar.header("Filters")
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

all_divisions = sorted(df["Division"].dropna().unique())
selected_divisions = st.sidebar.multiselect("Division filter", all_divisions, default=all_divisions)
margin_threshold = st.sidebar.slider("Margin threshold slider (%)", min_value=0, max_value=100, value=50, step=1)
product_search = st.sidebar.text_input("Product search", value="")

filtered = df[(df["Order Date"].dt.date >= start_date) & (df["Order Date"].dt.date <= end_date)]
if selected_divisions:
    filtered = filtered[filtered["Division"].isin(selected_divisions)]
if product_search.strip():
    filtered = filtered[filtered["Product Name"].str.contains(product_search.strip(), case=False, na=False)]

if filtered.empty:
    st.warning("No data matches the selected filters. Adjust the date, division, or product search filters.")
    st.stop()

portfolio_margin = filtered["Gross Profit"].sum() / filtered["Sales"].sum() * 100
products = product_metrics(filtered)
divisions = division_metrics(filtered)
risk = add_risk_flags(products, portfolio_margin)
pareto_revenue = pareto_table(products, "Sales")
pareto_profit = pareto_table(products, "Gross_Profit")
factory = filtered.groupby(["Factory", "Factory Latitude", "Factory Longitude"], as_index=False).agg(
    Sales=("Sales", "sum"), Units=("Units", "sum"), Gross_Profit=("Gross Profit", "sum"), Cost=("Cost", "sum"), Products=("Product Name", "nunique"), Orders=("Order ID", "nunique")
)
factory["Gross Margin (%)"] = factory["Gross_Profit"] / factory["Sales"] * 100
factory["Profit Share (%)"] = factory["Gross_Profit"] / factory["Gross_Profit"].sum() * 100

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Total Sales", money(filtered["Sales"].sum()))
kpi2.metric("Gross Profit", money(filtered["Gross Profit"].sum()))
kpi3.metric("Gross Margin", pct(portfolio_margin))
kpi4.metric("Units Sold", f"{filtered['Units'].sum():,.0f}")
kpi5.metric("Products", f"{filtered['Product Name'].nunique():,.0f}")

with st.expander("Data validation summary", expanded=False):
    st.write(f"Original rows loaded: **{original_rows:,}**")
    st.write(f"Rows removed during validation: **{removed_rows:,}**")
    st.write(f"Rows available after current filters: **{len(filtered):,}**")
    st.write("Validation rules: parse dates, coerce numeric sales/cost/profit/unit fields, remove zero-sales or invalid-unit records, standardize product/division labels, and add factory mapping from the brief.")
    changed = df[df["Original Division"] != df["Division"]][["Product Name", "Original Division", "Division", "Factory"]].drop_duplicates()
    if not changed.empty:
        st.info("Division standardization applied from the project brief:")
        st.dataframe(changed, use_container_width=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Product Profitability Overview",
    "Division Performance Dashboard",
    "Cost vs Margin Diagnostics",
    "Profit Concentration Analysis",
    "Factory View"
])

with tab1:
    st.subheader("Product-level margin leaderboard")
    leaderboard = products.sort_values("Gross Margin (%)", ascending=False)
    st.dataframe(
        leaderboard[["Product Name", "Division", "Factory", "Sales", "Gross_Profit", "Gross Margin (%)", "Profit per Unit", "Revenue Contribution (%)", "Profit Contribution (%)"]],
        use_container_width=True,
        hide_index=True
    )
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(products.sort_values("Gross_Profit", ascending=False), x="Product Name", y="Gross_Profit", color="Division", title="Gross Profit by Product")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.pie(products, names="Product Name", values="Gross_Profit", title="Profit Contribution by Product")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Division revenue vs profit comparison")
    c1, c2 = st.columns(2)
    with c1:
        div_long = divisions.melt(id_vars="Division", value_vars=["Sales", "Gross_Profit"], var_name="Metric", value_name="Value")
        fig = px.bar(div_long, x="Division", y="Value", color="Metric", barmode="group", title="Revenue vs Profit by Division")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.box(filtered, x="Division", y="Gross Margin (%)", points="all", title="Margin Distribution by Division")
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(divisions, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Cost vs margin diagnostics")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.scatter(
            products,
            x="Cost",
            y="Sales",
            size="Units",
            color="Gross Margin (%)",
            hover_name="Product Name",
            title="Cost vs Sales Scatter Plot",
        )
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        threshold_df = risk[risk["Gross Margin (%)"] < margin_threshold].sort_values("Gross Margin (%)")
        fig = px.bar(threshold_df, x="Product Name", y="Gross Margin (%)", color="Margin Risk Flag", title=f"Products Below {margin_threshold}% Margin")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Margin risk flags")
    st.dataframe(risk.sort_values("Gross Margin (%)"), use_container_width=True, hide_index=True)
    st.download_button("Download margin risk flags", risk.to_csv(index=False), file_name="margin_risk_flags.csv", mime="text/csv")

with tab4:
    st.subheader("Pareto charts and dependency indicators")
    rev_80 = int((pareto_revenue["Cumulative Sales Share (%)"] < 80).sum() + 1)
    prof_80 = int((pareto_profit["Cumulative Gross_Profit Share (%)"] < 80).sum() + 1)
    a, b = st.columns(2)
    a.metric("Products for 80% revenue", rev_80)
    b.metric("Products for 80% profit", prof_80)
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_bar(x=pareto_revenue["Product Name"], y=pareto_revenue["Sales Share (%)"], name="Revenue Share")
        fig.add_scatter(x=pareto_revenue["Product Name"], y=pareto_revenue["Cumulative Sales Share (%)"], name="Cumulative", mode="lines+markers")
        fig.add_hline(y=80, line_dash="dash")
        fig.update_layout(title="Revenue Pareto", xaxis_tickangle=-45, yaxis_title="Share (%)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = go.Figure()
        fig.add_bar(x=pareto_profit["Product Name"], y=pareto_profit["Gross_Profit Share (%)"], name="Profit Share")
        fig.add_scatter(x=pareto_profit["Product Name"], y=pareto_profit["Cumulative Gross_Profit Share (%)"], name="Cumulative", mode="lines+markers")
        fig.add_hline(y=80, line_dash="dash")
        fig.update_layout(title="Profit Pareto", xaxis_tickangle=-45, yaxis_title="Share (%)")
        st.plotly_chart(fig, use_container_width=True)
    st.info("Dependency indicator: when a small number of products cross the 80% revenue/profit threshold, the distributor is exposed to product-specific supply, pricing, and demand risk.")
    st.dataframe(pareto_profit, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Factory profitability from product-factory correlation")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(factory.sort_values("Gross_Profit", ascending=False), x="Factory", y="Gross_Profit", title="Gross Profit by Factory")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        map_df = factory.dropna(subset=["Factory Latitude", "Factory Longitude"])
        if not map_df.empty:
            fig = px.scatter_mapbox(
                map_df,
                lat="Factory Latitude",
                lon="Factory Longitude",
                size="Gross_Profit",
                color="Gross Margin (%)",
                hover_name="Factory",
                hover_data=["Sales", "Gross_Profit", "Products"],
                zoom=2.7,
                height=420,
                title="Factory Coordinates and Profit Contribution"
            )
            fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig, use_container_width=True)
    st.dataframe(factory, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Filtered data download")
st.download_button("Download filtered cleaned data", filtered.to_csv(index=False), file_name="filtered_cleaned_nassau_candy.csv", mime="text/csv")
