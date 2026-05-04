import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="SKIMS Market Analytics",
    layout="wide",
)

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def _make_connection():
    return snowflake.connector.connect(
        account=st.secrets["SNOWFLAKE_ACCOUNT"],
        user=st.secrets["SNOWFLAKE_USER"],
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        database=st.secrets["SNOWFLAKE_DATABASE"],
        warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
        role=st.secrets["SNOWFLAKE_ROLE"],
    )


@st.cache_resource
def get_connection():
    return _make_connection()


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a SQL query and return the results as a DataFrame.

    Handles stale Snowflake connections (e.g. after the server-side idle
    timeout of ~4 hours) by clearing the cached connection and retrying
    once before propagating the error.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        df = cur.fetch_pandas_all()
        cur.close()
        return df
    except Exception:
        # Connection may have been closed server-side; evict and retry once.
        get_connection.clear()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        df = cur.fetch_pandas_all()
        cur.close()
        return df


@st.cache_data(ttl=3600)
def load_categories() -> pd.DataFrame:
    return run_query(
        "SELECT CATEGORY_CODE, CATEGORY_NAME FROM MARTS.DIM_CATEGORY ORDER BY CATEGORY_NAME"
    )


@st.cache_data(ttl=3600)
def load_sales(category_codes: tuple, year_min: int, year_max: int) -> pd.DataFrame:
    # Build a parameterized IN clause using %s placeholders to avoid SQL injection.
    placeholders = ", ".join(["%s"] * len(category_codes))
    sql = f"""
        SELECT
            f.PERIOD,
            d.YEAR,
            d.MONTH,
            d.QUARTER,
            d.SEASON,
            c.CATEGORY_NAME,
            f.SALES_MILLIONS,
            f.MONTH_OVER_MONTH_PCT,
            f.YEAR_OVER_YEAR_PCT
        FROM MARTS.FACT_RETAIL_SALES f
        JOIN MARTS.DIM_DATE     d ON f.PERIOD        = d.PERIOD
        JOIN MARTS.DIM_CATEGORY c ON f.CATEGORY_CODE = c.CATEGORY_CODE
        WHERE f.CATEGORY_CODE IN ({placeholders})
          AND d.YEAR BETWEEN %s AND %s
          AND f.SEASONALLY_ADJ = 'no'
          AND f.DATA_TYPE_CODE = 'SM'
        ORDER BY f.PERIOD, c.CATEGORY_NAME
    """
    return run_query(sql, params=(*category_codes, year_min, year_max))


# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("Filters")
st.sidebar.caption("Planning Analyst · SKIMS Market")

categories_df = load_categories()
cat_options = categories_df["CATEGORY_NAME"].tolist()
cat_map = dict(zip(categories_df["CATEGORY_NAME"], categories_df["CATEGORY_CODE"]))

default_cats = [c for c in ["Clothing Stores", "Clothing and Clothing Accessories Stores"] if c in cat_options]
selected_names = st.sidebar.multiselect("Categories", options=cat_options, default=default_cats or cat_options[:2])

year_range = st.sidebar.slider("Year range", min_value=2019, max_value=2025, value=(2019, 2024))

# ── Guard: require at least one category ─────────────────────────────────────
if not selected_names:
    st.warning("Select at least one category from the sidebar to view the dashboard.")
    st.stop()

selected_codes = tuple(cat_map[n] for n in selected_names)

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_sales(selected_codes, year_range[0], year_range[1])

if df.empty:
    st.warning("No data for the selected filters. Try adjusting categories or year range.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Retail Sales Analytics — Shapewear & Intimates Market")
st.caption("Source: US Census Bureau Monthly Retail Trade Survey · Transformed via dbt")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Overview", "🗓 Seasonal Patterns", "📦 Inventory Implications"])

# ── Tab 1: Overview (Descriptive) ─────────────────────────────────────────────
with tab1:
    st.subheader("What happened? Monthly retail sales trends")

    yearly = df.copy()
    yearly["MONTH_NAME"] = yearly["MONTH"].map(MONTH_NAMES)
    yearly_agg = (
        yearly.groupby(["YEAR", "MONTH", "MONTH_NAME"])["SALES_MILLIONS"]
        .mean()
        .reset_index()
        .sort_values(["YEAR", "MONTH"])
    )
    fig = px.line(
        yearly_agg,
        x="MONTH_NAME",
        y="SALES_MILLIONS",
        color="YEAR",
        title="Monthly Retail Sales by Year ($M)",
        labels={"MONTH_NAME": "Month", "SALES_MILLIONS": "Sales ($M)", "YEAR": "Year"},
        category_orders={"MONTH_NAME": list(MONTH_NAMES.values())},
        color_discrete_sequence=px.colors.qualitative.Plotly,
    )
    fig.update_layout(legend_title_text="Year", hovermode="x unified")
    fig.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: Seasonal Patterns (Diagnostic) ─────────────────────────────────────
with tab2:
    st.subheader("Why did it happen? Average sales by calendar month")

    seasonal = (
        df.groupby("MONTH")["SALES_MILLIONS"]
        .mean()
        .reset_index()
    )
    seasonal["MONTH_NAME"] = seasonal["MONTH"].map(MONTH_NAMES)
    seasonal = seasonal.sort_values("MONTH")

    fig2 = px.bar(
        seasonal,
        x="MONTH_NAME",
        y="SALES_MILLIONS",
        title="Average Monthly Sales by Calendar Month (across selected years)",
        labels={"MONTH_NAME": "Month", "SALES_MILLIONS": "Avg Sales ($M)"},
        color="SALES_MILLIONS",
        color_continuous_scale="Blues",
    )
    dec_sales = seasonal.loc[seasonal["MONTH"] == 12, "SALES_MILLIONS"].values
    jan_sales = seasonal.loc[seasonal["MONTH"] == 1,  "SALES_MILLIONS"].values

    fig2.update_layout(
        coloraxis_showscale=False,
        xaxis={"categoryorder": "array", "categoryarray": list(MONTH_NAMES.values())},
    )
    fig2.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig2, use_container_width=True)

    if len(dec_sales) and len(jan_sales):
        drop_pct = (jan_sales[0] - dec_sales[0]) / dec_sales[0]

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("December avg sales", f"${dec_sales[0]:,.0f}M")
        col_b.metric("January avg sales",  f"${jan_sales[0]:,.0f}M")
        col_c.metric("Dec → Jan drop",     f"{drop_pct:.0%}")

        drop_df = pd.DataFrame({
            "Month": ["December", "January"],
            "Avg Sales ($M)": [dec_sales[0], jan_sales[0]],
            "Color": ["#3b82f6", "#ef4444"],
        })
        fig_drop = px.bar(
            drop_df,
            x="Month",
            y="Avg Sales ($M)",
            color="Month",
            color_discrete_map={"December": "#3b82f6", "January": "#ef4444"},
            title="December → January Demand Drop",
            labels={"Avg Sales ($M)": "Avg Sales ($M)"},
        )
        fig_drop.update_layout(showlegend=False)
        fig_drop.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_drop, use_container_width=True)

    st.caption(
        "The steepest single-month demand drop in the calendar. "
        "Inventory not cleared before January faces the worst sell-through environment of the year."
    )

ACTION_COLORS = {
    "Markdown Window":  "#ef4444",
    "Normal":           "#94a3b8",
    "Build Inventory":  "#22c55e",
    "Peak Season":      "#f97316",
}

def month_action(month: int) -> str:
    if month in (1, 2):
        return "Markdown Window"
    if month in (8, 9, 10):
        return "Build Inventory"
    if month in (11, 12):
        return "Peak Season"
    return "Normal"

# ── Tab 3: Inventory Implications (Diagnostic) ────────────────────────────────
with tab3:
    st.subheader("What does this mean? Inventory action calendar")

    monthly_avg = df.groupby("MONTH")["SALES_MILLIONS"].mean()
    q4_avg = df[df["MONTH"].isin([10, 11, 12])]["SALES_MILLIONS"].mean()
    full_avg = df["SALES_MILLIONS"].mean()
    q4_uplift = (q4_avg - full_avg) / full_avg if full_avg > 0 else 0
    peak_month = int(monthly_avg.idxmax())
    trough_month = int(monthly_avg.idxmin())

    c1, c2, c3 = st.columns(3)
    c1.metric("Q4 vs Annual Average", f"{q4_uplift:+.1%}")
    c2.metric("Peak Demand Month", MONTH_NAMES.get(peak_month, "—"))
    c3.metric("Trough Month", MONTH_NAMES.get(trough_month, "—"))

    action_df = (
        monthly_avg
        .reset_index()
        .rename(columns={"MONTH": "month_num", "SALES_MILLIONS": "avg_sales"})
    )
    action_df["MONTH_NAME"] = action_df["month_num"].map(MONTH_NAMES)
    action_df["Action"] = action_df["month_num"].map(month_action)
    action_df = action_df.sort_values("month_num")

    fig3 = px.bar(
        action_df,
        x="MONTH_NAME",
        y="avg_sales",
        color="Action",
        color_discrete_map=ACTION_COLORS,
        title="Inventory Action Calendar — Average Monthly Sales",
        labels={"MONTH_NAME": "Month", "avg_sales": "Avg Sales ($M)"},
        category_orders={
            "MONTH_NAME": list(MONTH_NAMES.values()),
            "Action": ["Markdown Window", "Normal", "Build Inventory", "Peak Season"],
        },
    )
    fig3.add_hline(
        y=full_avg,
        line_dash="dash",
        line_color="gray",
        annotation_text="Annual avg",
        annotation_position="top right",
    )
    fig3.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig3, use_container_width=True)

    st.info(
        "🟢 **Build Inventory (Aug–Oct):** Place purchase orders now — 6–8 week lead times mean "
        "holiday stock must be committed before demand peaks.  \n"
        "🟠 **Peak Season (Nov–Dec):** Highest demand. Inventory should already be in place.  \n"
        "🔴 **Markdown Window (Jan–Feb):** Demand drops sharply. Clear excess stock at discounts."
    )
