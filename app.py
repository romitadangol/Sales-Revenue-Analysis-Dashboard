
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Sales & Revenue Dashboard",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# DASHBOARD STYLING
# --------------------------------------------------

st.markdown("""
<style>
    /* Main application background */
    .stApp {
        background-color: #F7F9FC;
    }

    /* Main content spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Main title */
    h1 {
        color: #17365D;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Section headings */
    h2, h3 {
        color: #234B70;
        font-weight: 600;
    }

    /* KPI cards */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E3EAF2;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(20, 50, 80, 0.04);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748B;
        font-size: 14px;
    }

    div[data-testid="stMetricValue"] {
        color: #17365D;
        font-weight: 700;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #EEF3F8;
    }

    /* Dividers */
    hr {
        border-color: #DCE5EF;
    }

    /* Captions */
    .stCaption {
        color: #64748B;
    }
</style>
""", unsafe_allow_html=True)

st.info(
    "Dataset: Tableau Sample Superstore | "
    "Analysis period: January 2023 – November 16, 2026"
)

st.title("Sales & Revenue Analysis Dashboard")
st.caption("An interactive analysis of sales, profitability, customers, and products.")


# --------------------------------------------------
# 2. LOAD DATA
# --------------------------------------------------

DATA_PATH = Path(__file__).parent / "data" / "processed_sales_data.csv"

@st.cache_data
def load_data(path):
    data = pd.read_csv(path)
    data["Order Date"] = pd.to_datetime(data["Order Date"])
    data["Ship Date"] = pd.to_datetime(data["Ship Date"])
    return data


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(
        "Dataset not found. Please check that "
        "processed_sales_data.csv is inside the data folder."
    )
    st.stop()


# --------------------------------------------------
# 3. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Dashboard Filters")

min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()

selected_dates = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

selected_regions = st.sidebar.multiselect(
    "Region",
    options=sorted(df["Region"].dropna().unique()),
    default=sorted(df["Region"].dropna().unique())
)

selected_categories = st.sidebar.multiselect(
    "Category",
    options=sorted(df["Category"].dropna().unique()),
    default=sorted(df["Category"].dropna().unique())
)

selected_segments = st.sidebar.multiselect(
    "Customer segment",
    options=sorted(df["Segment"].dropna().unique()),
    default=sorted(df["Segment"].dropna().unique())
)


# --------------------------------------------------
# 4. FILTER DATA
# --------------------------------------------------

if len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = selected_dates[0]
    end_date = selected_dates[0]

filtered_df = df[
    (df["Order Date"].dt.date >= start_date)
    & (df["Order Date"].dt.date <= end_date)
    & (df["Region"].isin(selected_regions))
    & (df["Category"].isin(selected_categories))
    & (df["Segment"].isin(selected_segments))
].copy()

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()


# --------------------------------------------------
# 5. CALCULATE KPIs
# --------------------------------------------------

total_revenue = filtered_df["Sales"].sum()
total_profit = filtered_df["Profit"].sum()
total_orders = filtered_df["Order ID"].nunique()
total_customers = filtered_df["Customer ID"].nunique()
total_quantity = filtered_df["Quantity"].sum()
profit_margin = (
    total_profit / total_revenue * 100
    if total_revenue != 0 else 0
)
average_order_value = (
    total_revenue / total_orders
    if total_orders != 0 else 0
)


# --------------------------------------------------
# 6. KPI CARDS
# --------------------------------------------------

st.subheader("Executive Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Profit", f"${total_profit:,.2f}")
col3.metric("Total Orders", f"{total_orders:,}")
col4.metric("Profit Margin", f"{profit_margin:.2f}%")

col5, col6, col7 = st.columns(3)

col5.metric("Total Customers", f"{total_customers:,}")
col6.metric("Units Sold", f"{total_quantity:,.0f}")
col7.metric("Average Order Value", f"${average_order_value:,.2f}")


# --------------------------------------------------
# 7. MONTHLY SALES TREND
# --------------------------------------------------

st.divider()
st.subheader("Monthly Sales & Profit Trend")

monthly_data = (
    filtered_df
    .assign(Month=filtered_df["Order Date"].dt.to_period("M").dt.to_timestamp())
    .groupby("Month", as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum")
    )
)

monthly_long = monthly_data.melt(
    id_vars="Month",
    value_vars=["Revenue", "Profit"],
    var_name="Metric",
    value_name="Amount"
)

fig_monthly = px.line(
    monthly_long,
    x="Month",
    y="Amount",
    color="Metric",
    markers=True,
    title="Monthly Revenue and Profit",
    labels={"Amount": "Amount ($)", "Month": "Month"}
)

fig_monthly.update_layout(
    hovermode="x unified",
    legend_title_text=""
)

st.plotly_chart(fig_monthly, use_container_width=True)


# --------------------------------------------------
# 8. CATEGORY PERFORMANCE
# --------------------------------------------------

st.divider()
st.subheader("Category Performance")

category_data = (
    filtered_df
    .groupby("Category", as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Units_Sold=("Quantity", "sum")
    )
)

category_data["Profit Margin"] = (
    category_data["Profit"] / category_data["Revenue"] * 100
)

col1, col2 = st.columns(2)

with col1:
    fig_revenue = px.bar(
        category_data.sort_values("Revenue", ascending=False),
        x="Category",
        y="Revenue",
        title="Revenue by Category",
        text_auto=".2s",
        labels={"Revenue": "Revenue ($)"}
    )
    st.plotly_chart(fig_revenue, use_container_width=True)

with col2:
    fig_profit = px.bar(
        category_data.sort_values("Profit", ascending=False),
        x="Category",
        y="Profit",
        title="Profit by Category",
        text_auto=".2s",
        labels={"Profit": "Profit ($)"}
    )
    st.plotly_chart(fig_profit, use_container_width=True)

st.dataframe(
    category_data.style.format({
        "Revenue": "${:,.2f}",
        "Profit": "${:,.2f}",
        "Units_Sold": "{:,.0f}",
        "Profit Margin": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 9. PRODUCT PERFORMANCE
# --------------------------------------------------

st.divider()
st.subheader("Product Performance")

# Aggregate performance at product level
product_data = (
    filtered_df
    .groupby(["Product ID", "Product Name"], as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Units_Sold=("Quantity", "sum"),
        Orders=("Order ID", "nunique")
    )
)

product_data["Profit Margin"] = (
    product_data["Profit"] / product_data["Revenue"] * 100
)

# Top 10 products by revenue and profit
top_revenue = product_data.nlargest(10, "Revenue")
top_profit = product_data.nlargest(10, "Profit")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Top 10 Products by Revenue**")

    fig_top_revenue = px.bar(
        top_revenue.sort_values("Revenue"),
        x="Revenue",
        y="Product Name",
        orientation="h",
        title="Highest Revenue Products",
        labels={"Revenue": "Revenue ($)", "Product Name": ""},
        hover_data=["Profit", "Units_Sold", "Orders"]
    )

    fig_top_revenue.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_top_revenue, use_container_width=True)

with col2:
    st.markdown("**Top 10 Products by Profit**")

    fig_top_profit = px.bar(
        top_profit.sort_values("Profit"),
        x="Profit",
        y="Product Name",
        orientation="h",
        title="Most Profitable Products",
        labels={"Profit": "Profit ($)", "Product Name": ""},
        hover_data=["Revenue", "Units_Sold", "Orders"]
    )

    fig_top_profit.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_top_profit, use_container_width=True)


# Loss-making products
st.markdown("**Products with the Highest Total Losses**")

loss_products = (
    product_data[product_data["Profit"] < 0]
    .sort_values("Profit")
    .head(10)
)

if not loss_products.empty:
    fig_loss = px.bar(
        loss_products.sort_values("Profit", ascending=False),
        x="Profit",
        y="Product Name",
        orientation="h",
        title="10 Products with Lowest Total Profit",
        labels={"Profit": "Profit / Loss ($)", "Product Name": ""},
        hover_data=["Revenue", "Units_Sold", "Orders"]
    )

    st.plotly_chart(fig_loss, use_container_width=True)
else:
    st.info("No loss-making products found for the selected filters.")


# Subcategory performance
st.markdown("**Subcategory Performance**")

subcategory_data = (
    filtered_df
    .groupby(["Category", "Sub-Category"], as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Units_Sold=("Quantity", "sum"),
        Orders=("Order ID", "nunique")
    )
)

subcategory_data["Profit Margin"] = (
    subcategory_data["Profit"] / subcategory_data["Revenue"] * 100
)

fig_subcategory = px.bar(
    subcategory_data.sort_values("Profit"),
    x="Profit",
    y="Sub-Category",
    color="Category",
    orientation="h",
    title="Profit by Product Subcategory",
    labels={"Profit": "Profit / Loss ($)"}
)

st.plotly_chart(fig_subcategory, use_container_width=True)

st.dataframe(
    subcategory_data.sort_values("Profit", ascending=False).style.format({
        "Revenue": "${:,.2f}",
        "Profit": "${:,.2f}",
        "Units_Sold": "{:,.0f}",
        "Orders": "{:,.0f}",
        "Profit Margin": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# 10. REGIONAL PERFORMANCE
# --------------------------------------------------

st.divider()
st.subheader("Regional Performance")

# Aggregate regional data
region_data = (
    filtered_df
    .groupby("Region", as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique"),
        Customers=("Customer ID", "nunique"),
        Units_Sold=("Quantity", "sum")
    )
)

region_data["Profit Margin"] = (
    region_data["Profit"] / region_data["Revenue"] * 100
)

col1, col2 = st.columns(2)

with col1:
    fig_region_revenue = px.bar(
        region_data.sort_values("Revenue", ascending=False),
        x="Region",
        y="Revenue",
        title="Revenue by Region",
        text_auto=".2s",
        labels={"Revenue": "Revenue ($)"}
    )
    st.plotly_chart(fig_region_revenue, use_container_width=True)

with col2:
    fig_region_profit = px.bar(
        region_data.sort_values("Profit", ascending=False),
        x="Region",
        y="Profit",
        title="Profit by Region",
        text_auto=".2s",
        labels={"Profit": "Profit ($)"}
    )
    st.plotly_chart(fig_region_profit, use_container_width=True)

st.markdown("**Regional Performance Summary**")

st.dataframe(
    region_data.sort_values("Revenue", ascending=False).style.format({
        "Revenue": "${:,.2f}",
        "Profit": "${:,.2f}",
        "Orders": "{:,.0f}",
        "Customers": "{:,.0f}",
        "Units_Sold": "{:,.0f}",
        "Profit Margin": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)


# State-level analysis
st.markdown("**State-Level Performance**")

state_data = (
    filtered_df
    .groupby("State/Province", as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique"),
        Customers=("Customer ID", "nunique")
    )
)

state_data["Profit Margin"] = (
    state_data["Profit"] / state_data["Revenue"] * 100
)

state_data = state_data.sort_values("Revenue", ascending=False)

fig_state = px.bar(
    state_data.head(15).sort_values("Revenue"),
    x="Revenue",
    y="State/Province",
    orientation="h",
    title="Top 15 States by Revenue",
    labels={"Revenue": "Revenue ($)", "State/Province": ""},
    hover_data=["Profit", "Profit Margin", "Orders"]
)

st.plotly_chart(fig_state, use_container_width=True)

# Highlight loss-making states
loss_states = (
    state_data[state_data["Profit"] < 0]
    .sort_values("Profit")
)

st.markdown("**States with Negative Total Profit**")

if not loss_states.empty:
    st.dataframe(
        loss_states[[
            "State/Province",
            "Revenue",
            "Profit",
            "Profit Margin",
            "Orders"
        ]].style.format({
            "Revenue": "${:,.2f}",
            "Profit": "${:,.2f}",
            "Profit Margin": "{:.2f}%",
            "Orders": "{:,.0f}"
        }),
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("No loss-making states in the selected filters.")


# --------------------------------------------------
# 11. CUSTOMER & DISCOUNT ANALYSIS
# --------------------------------------------------

st.divider()
st.subheader("Customer & Discount Analysis")

# Customer-level aggregation
customer_data = (
    filtered_df
    .groupby(["Customer ID", "Customer Name"], as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Orders=("Order ID", "nunique"),
        Units_Sold=("Quantity", "sum")
    )
)

customer_data["Average Order Value"] = (
    customer_data["Revenue"] / customer_data["Orders"]
)

# Customer KPIs
total_customer_count = customer_data["Customer ID"].nunique()
repeat_customers = (customer_data["Orders"] > 1).sum()
one_time_customers = (customer_data["Orders"] == 1).sum()

repeat_rate = (
    repeat_customers / total_customer_count * 100
    if total_customer_count else 0
)

col1, col2, col3 = st.columns(3)

col1.metric("Unique Customers", f"{total_customer_count:,}")
col2.metric("Repeat Customers", f"{repeat_customers:,}")
col3.metric("Repeat Customer Rate", f"{repeat_rate:.2f}%")

# Top customers
st.markdown("**Top 10 Customers by Revenue**")

top_customers = customer_data.nlargest(10, "Revenue")

fig_customers = px.bar(
    top_customers.sort_values("Revenue"),
    x="Revenue",
    y="Customer ID",
    orientation="h",
    title="Top Customers by Revenue",
    labels={"Revenue": "Revenue ($)", "Customer ID": "Customer ID"},
    hover_data=["Profit", "Orders", "Average Order Value"]
)

st.plotly_chart(fig_customers, use_container_width=True)

st.dataframe(
    top_customers[[
        "Customer Name",
        "Revenue",
        "Profit",
        "Orders",
        "Units_Sold",
        "Average Order Value"
    ]].style.format({
        "Revenue": "${:,.2f}",
        "Profit": "${:,.2f}",
        "Orders": "{:,.0f}",
        "Units_Sold": "{:,.0f}",
        "Average Order Value": "${:,.2f}"
    }),
    use_container_width=True,
    hide_index=True
)

# Repeat vs one-time customers
customer_type_data = pd.DataFrame({
    "Customer Type": ["Repeat Customers", "One-Time Customers"],
    "Count": [repeat_customers, one_time_customers]
})

fig_customer_type = px.pie(
    customer_type_data,
    names="Customer Type",
    values="Count",
    hole=0.55,
    title="Customer Distribution"
)

st.plotly_chart(fig_customer_type, use_container_width=True)


# --------------------------------------------------
# DISCOUNT ANALYSIS
# --------------------------------------------------

st.divider()
st.subheader("Discount Analysis")

discount_data = (
    filtered_df
    .groupby("Discount", as_index=False)
    .agg(
        Revenue=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Line_Items=("Order ID", "size"),
        Orders=("Order ID", "nunique")
    )
)

discount_data["Profit Margin"] = (
    discount_data["Profit"] / discount_data["Revenue"] * 100
)

col1, col2 = st.columns(2)

with col1:
    fig_discount_revenue = px.bar(
        discount_data,
        x="Discount",
        y="Revenue",
        title="Revenue by Discount Level",
        labels={
            "Discount": "Discount Rate",
            "Revenue": "Revenue ($)"
        }
    )
    st.plotly_chart(fig_discount_revenue, use_container_width=True)

with col2:
    fig_discount_profit = px.bar(
        discount_data,
        x="Discount",
        y="Profit",
        title="Profit by Discount Level",
        labels={
            "Discount": "Discount Rate",
            "Profit": "Profit ($)"
        }
    )
    st.plotly_chart(fig_discount_profit, use_container_width=True)

st.markdown("**Discount Performance Summary**")

st.dataframe(
    discount_data.style.format({
        "Discount": "{:.0%}",
        "Revenue": "${:,.2f}",
        "Profit": "${:,.2f}",
        "Line_Items": "{:,.0f}",
        "Orders": "{:,.0f}",
        "Profit Margin": "{:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# LOSS-MAKING TRANSACTIONS
# --------------------------------------------------

st.markdown("**Loss-Making Transactions (Line Items)**")

loss_transactions = filtered_df[filtered_df["Profit"] < 0].copy()

col1, col2, col3 = st.columns(3)

col1.metric("Loss-Making Line Items", f"{len(loss_transactions):,}")
col2.metric(
    "Total Loss",
    f"${loss_transactions['Profit'].sum():,.2f}"
)
col3.metric(
    "Share of Line Items",
    f"{len(loss_transactions) / len(filtered_df) * 100:.2f}%"
)

st.caption(
    "A loss-making line item is an individual product entry with negative profit. "
    "An order can contain both profitable and loss-making line items."
)

with st.expander("View loss-making line items"):
    st.dataframe(
        loss_transactions[[
            "Order ID",
            "Customer ID",
            "Product Name",
            "Category",
            "Sub-Category",
            "Discount",
            "Sales",
            "Profit"
        ]].sort_values("Profit"),
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 9. DATA SUMMARY
# --------------------------------------------------

st.divider()

with st.expander("View filtered data summary"):
    st.write(f"**Records displayed:** {len(filtered_df):,}")
    st.write(
        f"**Date range:** {start_date.strftime('%d %b %Y')} "
        f"to {end_date.strftime('%d %b %Y')}"
    )
    st.dataframe(filtered_df, use_container_width=True)

st.caption("Sales & Revenue Analysis Dashboard | Built with Python, Pandas, Plotly and Streamlit")
