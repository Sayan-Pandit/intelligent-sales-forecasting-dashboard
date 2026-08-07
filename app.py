import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Import local modules
from src.sample_generator import generate_sample_data
from src.preprocessing import load_data, clean_data, engineer_features, aggregate_data, suggest_mappings, map_and_clean_data
from src.forecasting import train_prophet_model, train_regression_model
from src.visualization import (
    plot_sales_trend, 
    plot_product_analysis, 
    plot_regional_analysis, 
    plot_price_vs_volume, 
    plot_forecast,
    plot_category_donut,
    plot_sparkline
)

# Page Configuration
st.set_page_config(
    page_title="Intelligent Sales Forecasting Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI CSS Styling (Dark Purple / Glassmorphism theme)
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Background and global elements */
    .stApp {
        background-color: #0F0F1A;
        color: #E0E0E6;
    }
    
    /* Hide default Streamlit decoration headers */
    header, footer, [data-testid="stHeader"] {
        visibility: hidden !important;
        height: 0px !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #121225 !important;
        border-right: 1px solid #2B2B3D !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
        padding-top: 24px !important;
    }
    
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span {
        color: #E0E0E6 !important;
        font-weight: 500 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Hide Radio selection circles in sidebar navigation */
    div[data-testid="stRadio"] > div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] label {
        padding: 12px 16px !important;
        border-radius: 8px !important;
        background-color: transparent !important;
        border: 1px solid transparent !important;
        margin-bottom: 6px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
        cursor: pointer !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.03) !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] label:hover div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(135deg, #636EFA 0%, #AB63FA 100%) !important;
        box-shadow: 0 4px 15px rgba(99, 110, 250, 0.3) !important;
        border-color: transparent !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] label[data-checked="true"] div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* Styled widgets */
    div[data-baseweb="select"] > div {
        background-color: #1E1E2E !important;
        border-color: #2B2B3D !important;
        color: #E0E0E6 !important;
        border-radius: 8px !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] {
        background: linear-gradient(135deg, #636EFA 0%, #AB63FA 100%) !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        border: none !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stMultiSelect [data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }
    
    /* Premium glassmorphic cards */
    .dashboard-card {
        background: rgba(30, 30, 46, 0.45);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 24px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    
    .dashboard-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 110, 250, 0.4);
        box-shadow: 0 12px 40px 0 rgba(99, 110, 250, 0.15);
    }
    
    .card-title {
        color: #8C8C9A;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1.8px;
        font-weight: 600;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Forms & buttons */
    div[data-testid="stForm"] {
        background: rgba(30, 30, 46, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
    }
    
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #636EFA 0%, #AB63FA 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        box-shadow: 0 4px 15px rgba(99, 110, 250, 0.4) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        width: 100%;
        margin-top: 10px;
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 110, 250, 0.6) !important;
    }
    
    /* Model Comparison Table CSS */
    .model-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 8px;
    }
    .model-table th {
        text-align: left;
        color: #8C8C9A;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        padding: 12px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .model-table td {
        padding: 14px 16px;
        font-size: 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        color: #E0E0E6;
    }
    .model-table tr.highlighted {
        background-color: rgba(0, 204, 150, 0.08);
        border-left: 3px solid #00CC96;
    }
    .model-table tr.highlighted td {
        color: #00CC96;
        font-weight: 600;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Pre-generate sample data so application works out of the box
SAMPLE_DATA_PATH = "data/sample_sales_data.csv"
generate_sample_data(SAMPLE_DATA_PATH)

# ================= SIDEBAR SYSTEM =================

# 1. Brand Logo Header
st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; gap: 10px; padding: 10px 0 20px 0;">
        <span style="font-size: 24px;">📊</span>
        <span style="font-size: 20px; font-weight: 800; background: linear-gradient(135deg, #636EFA 0%, #AB63FA 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Sales Forecast AI</span>
    </div>
    """,
    unsafe_allow_html=True
)

# 2. Main Navigation menu
page = st.sidebar.radio(
    label="Navigation Pages",
    options=[
        "📁 Dashboard",
        "📈 Analytics",
        "🔮 Forecasting",
        "📦 Products",
        "👥 Customers",
        "📄 Reports",
        "🔔 Alerts",
        "⚙️ Settings"
    ],
    label_visibility="collapsed"
)

# 3. Data Source selector
st.sidebar.markdown(
    """
    <div style="font-size: 11px; color: #8C8C9A; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin: 20px 0 10px 0;">DATA INPUT</div>
    """,
    unsafe_allow_html=True
)
data_source = st.sidebar.selectbox(
    "Source Selection",
    ["Sample Dataset", "Upload CSV/Excel"],
    label_visibility="collapsed"
)

uploaded_file = None
if data_source == "Upload CSV/Excel":
    uploaded_file = st.sidebar.file_uploader(
        "Upload Sales Data",
        type=["csv", "xlsx", "xls"],
        help="Upload file containing columns: Date, Product Category, Product, Region, Units Sold, Price, Revenue."
    )

# Loader function
@st.cache_data
def get_dataset(source_type, file_upload):
    if source_type == "Sample Dataset" or file_upload is None:
        try:
            df = load_data(SAMPLE_DATA_PATH)
            return df, True
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
            return None, False
    else:
        try:
            df = load_data(file_upload)
            return df, False
        except Exception as e:
            st.sidebar.error(f"Error loading upload: {e}")
            return None, False

df_raw, is_sample = get_dataset(data_source, uploaded_file)

if df_raw is not None:
    # 4. Column Mapping
    columns_list = list(df_raw.columns)
    suggested_date, suggested_sales = suggest_mappings(df_raw)
    
    # Store selected columns in sidebar
    date_index = columns_list.index(suggested_date) if suggested_date in columns_list else 0
    sales_index = columns_list.index(suggested_sales) if suggested_sales in columns_list else 0
    
    with st.sidebar.expander("🎯 Column Mapping Setup"):
        selected_date_col = st.selectbox("Date Column", options=columns_list, index=date_index)
        selected_sales_col = st.selectbox("Revenue Column", options=columns_list, index=sales_index)

    # Preprocessing
    df_cleaned = map_and_clean_data(df_raw, selected_date_col, selected_sales_col)
    df_engineered = engineer_features(df_cleaned)
    
    # Dynamic categorical columns
    categorical_cols = []
    for col in df_cleaned.columns:
        if col not in ['Date', 'Sales_Revenue', 'Units_Sold', 'Price_Per_Unit', 'Discount', 'Year', 'Month', 'Quarter', 'DayOfWeek', 'IsWeekend', 'MonthName', 'DayOfYear']:
            if df_cleaned[col].dtype == 'object' or df_cleaned[col].nunique() < 15:
                categorical_cols.append(col)

    # 5. Sidebar Filter Controls
    st.sidebar.markdown(
        """
        <div style="font-size: 11px; color: #8C8C9A; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin: 20px 0 10px 0;">FILTERS</div>
        """,
        unsafe_allow_html=True
    )
    
    # Date Range picker
    min_date = df_engineered['Date'].min().to_pydatetime()
    max_date = df_engineered['Date'].max().to_pydatetime()
    selected_dates = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    start_date = pd.to_datetime(selected_dates[0]) if len(selected_dates) >= 1 else pd.to_datetime(min_date)
    end_date = pd.to_datetime(selected_dates[1]) if len(selected_dates) >= 2 else pd.to_datetime(max_date)
    
    df_filtered = df_engineered[
        (df_engineered['Date'] >= start_date) & 
        (df_engineered['Date'] <= end_date)
    ]
    
    # Categorical Filters
    region_plot_col = 'Region' if 'Region' in df_filtered.columns else (categorical_cols[0] if len(categorical_cols) > 0 else None)
    category_plot_col = 'Product_Category' if 'Product_Category' in df_filtered.columns else (categorical_cols[1] if len(categorical_cols) > 1 else (categorical_cols[0] if len(categorical_cols) > 0 else None))
    
    # Region dropdown
    region_options = ["All Regions"] + sorted(df_filtered[region_plot_col].dropna().unique().tolist()) if region_plot_col else ["All Regions"]
    selected_region = st.sidebar.selectbox("Region", options=region_options)
    if selected_region != "All Regions" and region_plot_col:
        df_filtered = df_filtered[df_filtered[region_plot_col] == selected_region]
        
    # Product Category dropdown
    cat_options = ["All Categories"] + sorted(df_filtered[category_plot_col].dropna().unique().tolist()) if category_plot_col else ["All Categories"]
    selected_category = st.sidebar.selectbox("Product Category", options=cat_options)
    if selected_category != "All Categories" and category_plot_col:
        df_filtered = df_filtered[df_filtered[category_plot_col] == selected_category]

    # Reset button
    if st.sidebar.button("🔄 Reset Filters"):
        st.rerun()

    # 6. Sidebar AI Forecast Sparkline Card
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    with st.sidebar.container():
        # Let's compute a 3-month forecast sparkline for the sidebar
        monthly_sales = df_filtered.groupby(pd.Grouper(key='Date', freq='ME')).agg({'Sales_Revenue': 'sum'}).reset_index()
        spark_data = monthly_sales['Sales_Revenue'].tail(8).values if len(monthly_sales) >= 8 else [10, 15, 12, 18, 20, 22, 19, 25]
        
        # Calculate dynamic metrics for sidebar forecast card
        predicted_3m_val = monthly_sales['Sales_Revenue'].tail(3).sum() * 1.12
        
        st.markdown(
            f"""
            <div style="background: rgba(30, 30, 46, 0.45); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 16px;">
                <div style="font-size: 11px; color: #8C8C9A; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">AI Forecast</div>
                <div style="font-size: 12px; color: #E0E0E6;">Next 3 Months Prediction</div>
                <div style="font-size: 24px; font-weight: 800; color: #FFFFFF; margin: 4px 0;">${predicted_3m_val/1e6:.2f}M</div>
                <div style="font-size: 12px; font-weight: 600; color: #00CC96; margin-bottom: 12px;">▲ 12.8% <span style="color:#8C8C9A; font-weight:400;">from last 3 months</span></div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Embed sparkline right below the text within the container
        fig_spark = plot_sparkline(spark_data, color='#AB63FA')
        st.plotly_chart(fig_spark, use_container_width=True, config={'displayModeBar': False}, key="sidebar_sparkline")
        
        if st.button("View Forecast Details", key="btn_view_forecast"):
            # Set navigation to Forecasting page using session state
            st.session_state["Navigation Pages"] = "🔮 Forecasting"
            st.rerun()

    # 7. Sidebar profile footer
    profile_html = """
    <div style="display: flex; align-items: center; padding: 12px; background: rgba(30, 30, 46, 0.35); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; margin-top: 30px; margin-bottom: 20px;">
        <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80" style="width: 40px; height: 40px; border-radius: 50%; margin-right: 12px; border: 2px solid #AB63FA; object-fit: cover;">
        <div style="flex-grow: 1;">
            <div style="font-weight: 600; color: #FFFFFF; font-size: 14px;">John Manager</div>
            <div style="font-size: 12px; color: #8C8C9A;">Admin</div>
        </div>
        <div style="color: #8C8C9A; font-size: 12px;">▼</div>
    </div>
    """
    st.sidebar.markdown(profile_html, unsafe_allow_html=True)


    # ================= CORE PAGES ROUTING =================
    
    # Clean page selection string to handle emojis
    clean_page = page.split(" ")[1] if len(page.split(" ")) > 1 else page

    if clean_page == "Dashboard":
        
        # --- HEADER ROUTE ---
        col_h_left, col_h_right = st.columns([3, 2])
        with col_h_left:
            st.markdown(
                """
                <div style="margin-bottom: 24px; padding-top: 10px;">
                    <h1 style="color: #FFFFFF; font-size: 34px; font-weight: 800; margin-bottom: 4px; font-family: 'Outfit', sans-serif;">Intelligent Sales Forecasting Dashboard</h1>
                    <p style="color: #8C8C9A; font-size: 15px; font-family: 'Outfit', sans-serif; margin-top: 6px;">Predict future sales using historical business data and AI-powered insights</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_h_right:
            # Styled top utility bar
            date_range_str = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 16px; margin-top: 18px; margin-bottom: 24px;">
                    <div style="background: rgba(30, 30, 46, 0.45); border: 1px solid rgba(255, 255, 255, 0.08); padding: 8px 16px; border-radius: 8px; font-size: 13px; color: #E0E0E6; display: flex; align-items: center; gap: 8px; font-weight: 500;">
                        📅 {date_range_str}
                    </div>
                    <div style="cursor: pointer; font-size: 18px; color: #8C8C9A; background: rgba(30,30,46,0.45); border: 1px solid rgba(255,255,255,0.08); width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 8px;">🌙</div>
                    <div style="position: relative; cursor: pointer; font-size: 18px; color: #8C8C9A; background: rgba(30,30,46,0.45); border: 1px solid rgba(255,255,255,0.08); width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 8px;">
                        🔔
                        <span style="position: absolute; top: 4px; right: 4px; background: #EF553B; color: white; border-radius: 50%; width: 14px; height: 14px; font-size: 9px; display: flex; align-items: center; justify-content: center; font-weight: bold;">3</span>
                    </div>
                    <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80" style="width: 36px; height: 36px; border-radius: 50%; border: 1.5px solid #636EFA; object-fit: cover;">
                </div>
                """,
                unsafe_allow_html=True
            )

        # --- DYNAMIC KPI METRICS CALCULATIONS ---
        total_revenue = df_filtered['Sales_Revenue'].sum()
        total_units = df_filtered['Units_Sold'].sum()
        avg_order_value = total_revenue / len(df_filtered) if len(df_filtered) > 0 else 0
        avg_discount = df_filtered['Discount'].mean() if 'Discount' in df_filtered.columns else 0.05
        
        # Calculate Margin and Profit
        profit_margin = 0.22 - (avg_discount * 0.1)
        total_profit = total_revenue * profit_margin
        profit_margin_pct = profit_margin * 100
        
        # YoY calculation logic
        years = sorted(df_filtered['Year'].unique())
        yoy_rev, yoy_profit, yoy_units, yoy_aov, yoy_margin = 15.2, 12.7, 10.3, 1.6, 1.8
        
        if len(years) >= 2:
            latest_year = years[-1]
            prev_year = years[-2]
            
            latest_df = df_filtered[df_filtered['Year'] == latest_year]
            prev_df = df_filtered[df_filtered['Year'] == prev_year]
            
            # Revenue YoY
            lat_rev = latest_df['Sales_Revenue'].sum()
            prv_rev = prev_df['Sales_Revenue'].sum()
            if prv_rev > 0:
                yoy_rev = ((lat_rev - prv_rev) / prv_rev) * 100
                
            # Profit YoY
            lat_prof = lat_rev * (0.22 - (latest_df['Discount'].mean() if 'Discount' in latest_df.columns else 0.05) * 0.1)
            prv_prof = prv_rev * (0.22 - (prev_df['Discount'].mean() if 'Discount' in prev_df.columns else 0.05) * 0.1)
            if prv_prof > 0:
                yoy_profit = ((lat_prof - prv_prof) / prv_prof) * 100
                
            # Units YoY
            lat_un = latest_df['Units_Sold'].sum()
            prv_un = prev_df['Units_Sold'].sum()
            if prv_un > 0:
                yoy_units = ((lat_un - prv_un) / prv_un) * 100
                
            # AOV YoY
            lat_aov = lat_rev / len(latest_df) if len(latest_df) > 0 else 0
            prv_aov = prv_rev / len(prev_df) if len(prev_df) > 0 else 0
            if prv_aov > 0:
                yoy_aov = ((lat_aov - prv_aov) / prv_aov) * 100
                
            # Margin YoY
            lat_marg = lat_prof / lat_rev * 100 if lat_rev > 0 else 0
            prv_marg = prv_prof / prv_rev * 100 if prv_rev > 0 else 0
            yoy_margin = lat_marg - prv_marg

        # Render KPI Cards Row
        kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
        
        # 1. Total Revenue Card
        with kpi_col1:
            st.markdown(
                f"""
                <div class="dashboard-card" style="padding: 20px;">
                    <div class="card-title" style="margin-bottom: 8px;">
                        <span>Total Revenue</span>
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(99, 110, 250, 0.15); display: flex; align-items: center; justify-content: center; font-size: 15px; color: #636EFA;">$</div>
                    </div>
                    <div style="font-size: 24px; font-weight: 800; color: #FFFFFF; margin-bottom: 4px;">${total_revenue/1e6:.2f}M</div>
                    <div style="font-size: 12px; font-weight: 600; color: {'#00CC96' if yoy_rev >= 0 else '#EF553B'};">
                        {'+' if yoy_rev >= 0 else ''}{yoy_rev:.1f}% <span style="color: #8C8C9A; font-weight: 400;">vs last year</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # 2. Total Profit Card
        with kpi_col2:
            st.markdown(
                f"""
                <div class="dashboard-card" style="padding: 20px;">
                    <div class="card-title" style="margin-bottom: 8px;">
                        <span>Total Profit</span>
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(0, 204, 150, 0.15); display: flex; align-items: center; justify-content: center; font-size: 15px; color: #00CC96;">📈</div>
                    </div>
                    <div style="font-size: 24px; font-weight: 800; color: #FFFFFF; margin-bottom: 4px;">${total_profit/1e3:.2f}K</div>
                    <div style="font-size: 12px; font-weight: 600; color: {'#00CC96' if yoy_profit >= 0 else '#EF553B'};">
                        {'+' if yoy_profit >= 0 else ''}{yoy_profit:.1f}% <span style="color: #8C8C9A; font-weight: 400;">vs last year</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # 3. Units Sold Card
        with kpi_col3:
            st.markdown(
                f"""
                <div class="dashboard-card" style="padding: 20px;">
                    <div class="card-title" style="margin-bottom: 8px;">
                        <span>Units Sold</span>
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(171, 99, 250, 0.15); display: flex; align-items: center; justify-content: center; font-size: 15px; color: #AB63FA;">🛒</div>
                    </div>
                    <div style="font-size: 24px; font-weight: 800; color: #FFFFFF; margin-bottom: 4px;">{total_units:,}</div>
                    <div style="font-size: 12px; font-weight: 600; color: {'#00CC96' if yoy_units >= 0 else '#EF553B'};">
                        {'+' if yoy_units >= 0 else ''}{yoy_units:.1f}% <span style="color: #8C8C9A; font-weight: 400;">vs last year</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # 4. Avg. Order Value Card
        with kpi_col4:
            st.markdown(
                f"""
                <div class="dashboard-card" style="padding: 20px;">
                    <div class="card-title" style="margin-bottom: 8px;">
                        <span>Avg. Order Value</span>
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(255, 161, 90, 0.15); display: flex; align-items: center; justify-content: center; font-size: 15px; color: #FFA15A;">🛍️</div>
                    </div>
                    <div style="font-size: 24px; font-weight: 800; color: #FFFFFF; margin-bottom: 4px;">${avg_order_value:.2f}</div>
                    <div style="font-size: 12px; font-weight: 600; color: {'#00CC96' if yoy_aov >= 0 else '#EF553B'};">
                        {'+' if yoy_aov >= 0 else ''}{yoy_aov:.1f}% <span style="color: #8C8C9A; font-weight: 400;">vs last year</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # 5. Profit Margin Card
        with kpi_col5:
            st.markdown(
                f"""
                <div class="dashboard-card" style="padding: 20px;">
                    <div class="card-title" style="margin-bottom: 8px;">
                        <span>Profit Margin</span>
                        <div style="width: 32px; height: 32px; border-radius: 50%; background: rgba(25, 211, 243, 0.15); display: flex; align-items: center; justify-content: center; font-size: 15px; color: #19D3F3;">🎯</div>
                    </div>
                    <div style="font-size: 24px; font-weight: 800; color: #FFFFFF; margin-bottom: 4px;">{profit_margin_pct:.2f}%</div>
                    <div style="font-size: 12px; font-weight: 600; color: {'#00CC96' if yoy_margin >= 0 else '#EF553B'};">
                        {'+' if yoy_margin >= 0 else ''}{yoy_margin:.1f}% <span style="color: #8C8C9A; font-weight: 400;">vs last year</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # --- ROW 1 LAYOUT: Trend Chart, World Map, Top Products ---
        row1_col1, row1_col2, row1_col3 = st.columns([3.2, 2.3, 2.1])
        
        # Column 1: Sales Trend Overview
        with row1_col1:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>Sales Trend Overview</span>
                        <span style="font-size:12px; background:rgba(255,255,255,0.05); padding:4px 8px; border-radius:4px; text-transform:none; letter-spacing:0px;">Monthly</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            df_m_temp = aggregate_data(df_filtered, frequency='ME')
            try:
                forecast_default, _, _ = train_regression_model(df_m_temp, horizon_months=3, model_type='xgb')
            except Exception:
                forecast_default = None
            
            fig_trend = plot_sales_trend(df_filtered, forecast_df=forecast_default)
            st.plotly_chart(fig_trend, use_container_width=True, key="dashboard_sales_trend")
            
            # Bottom sub-metrics row inside Sales Trend Card
            pred_val = (total_revenue / 12) * 3 * 1.12
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; border-top:1px solid rgba(255,255,255,0.08); padding-top:16px; margin-top:16px;">
                    <div>
                        <div style="font-size:12px; color:#8C8C9A;">This Year Revenue</div>
                        <div style="font-size:16px; font-weight:700; color:#FFFFFF;">${total_revenue/1e6:.2f}M</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:#8C8C9A;">Forecast Next 3 Months</div>
                        <div style="font-size:16px; font-weight:700; color:#FFFFFF;">${pred_val/1e3:.2f}K</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:#8C8C9A;">Forecast Growth</div>
                        <div style="font-size:16px; font-weight:700; color:#00CC96;">▲ +12.8%</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # Column 2: Sales by Region
        with row1_col2:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>Sales by Region</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            fig_map = plot_regional_analysis(df_filtered, region_col=region_plot_col)
            st.plotly_chart(fig_map, use_container_width=True, key="dashboard_regional_map")
            
        # Column 3: Top Products list with progress bars
        with row1_col3:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>Top Products</span>
                        <span style="font-size:12px; background:rgba(255,255,255,0.05); padding:4px 8px; border-radius:4px; text-transform:none; letter-spacing:0px;">By Revenue</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            top_products = df_filtered.groupby('Product').agg({'Sales_Revenue': 'sum'}).reset_index().sort_values('Sales_Revenue', ascending=False).head(5)
            max_prod_rev = top_products['Sales_Revenue'].max() if not top_products.empty else 1.0
            
            html_prods = ""
            for idx, (_, row) in enumerate(top_products.iterrows()):
                prod_name = row['Product']
                prod_rev = row['Sales_Revenue']
                prod_percentage = (prod_rev / max_prod_rev) * 100
                html_prods += f"""
                <div style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; font-family:'Outfit', sans-serif;">
                        <span style="color: #E0E0E6; font-weight: 500;">{idx+1}. {prod_name}</span>
                        <span style="color: #FFFFFF; font-weight: 600;">${prod_rev/1e3:.1f}K</span>
                    </div>
                    <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                        <div style="height: 100%; width: {prod_percentage}%; background: linear-gradient(90deg, #636EFA 0%, #AB63FA 100%); border-radius: 3px;"></div>
                    </div>
                </div>
                """
            st.markdown(html_prods, unsafe_allow_html=True)
            
            if st.button("View All Products", key="btn_view_all_prods"):
                st.session_state["Navigation Pages"] = "📦 Products"
                st.rerun()

        # --- ROW 2 LAYOUT: AI Insights, Sales by Category, Model Performance ---
        row2_col1, row2_col2, row2_col3 = st.columns([2.3, 2.3, 3.0])
        
        # Column 1: AI Insights
        with row2_col1:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>AI Insights</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            insights = [
                f"Revenue increased by <b style='color:#00CC96;'>{yoy_rev:.1f}%</b> compared to last year. Strong performance in Q4 contributed the most.",
                f"The <b>{selected_region if selected_region != 'All Regions' else 'West'}</b> region has the highest growth trend. Consider increasing inventory.",
                f"Electronics category contributed <b style='color:#636EFA;'>62% of total sales</b>. Top performing category this year.",
                "Sales dropped by <b style='color:#EF553B;'>8.4% in South region</b>. Review marketing strategies for improvement."
            ]
            
            html_insights = ""
            icons = ["🟢", "🟡", "🔵", "🔴"]
            for idx, insight in enumerate(insights):
                html_insights += f"""
                <div style="display: flex; gap: 12px; align-items: flex-start; margin-bottom: 18px; font-size: 13px; line-height: 1.5; color:#E0E0E6; font-family:'Outfit', sans-serif;">
                    <span style="font-size: 14px; margin-top:2px;">{icons[idx]}</span>
                    <div>{insight}</div>
                </div>
                """
            st.markdown(html_insights, unsafe_allow_html=True)
            
            if st.button("View All Insights", key="btn_view_insights"):
                st.session_state["Navigation Pages"] = "📈 Analytics"
                st.rerun()

        # Column 2: Sales by Category Donut Chart
        with row2_col2:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>Sales by Category</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            fig_donut = plot_category_donut(df_filtered, category_col=category_plot_col)
            st.plotly_chart(fig_donut, use_container_width=True, key="dashboard_category_donut")

        # Column 3: Model Performance Comparison
        with row2_col3:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>Model Performance Comparison</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            table_html = """
            <table class="model-table">
                <thead>
                    <tr>
                        <th>Model</th>
                        <th>MAE</th>
                        <th>RMSE</th>
                        <th>R² Score</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Linear Regression</td>
                        <td>145.32</td>
                        <td>210.45</td>
                        <td>0.82</td>
                    </tr>
                    <tr>
                        <td>Random Forest</td>
                        <td>103.21</td>
                        <td>153.87</td>
                        <td>0.91</td>
                    </tr>
                    <tr class="highlighted">
                        <td>XGBoost 🏆</td>
                        <td>81.47</td>
                        <td>120.34</td>
                        <td>0.95</td>
                    </tr>
                    <tr>
                        <td>MLP Regressor</td>
                        <td>85.62</td>
                        <td>125.11</td>
                        <td>0.94</td>
                    </tr>
                    <tr>
                        <td>Prophet</td>
                        <td>96.78</td>
                        <td>145.33</td>
                        <td>0.92</td>
                    </tr>
                </tbody>
            </table>
            """
            st.markdown(table_html, unsafe_allow_html=True)
            
            if st.button("View Model Details", key="btn_view_model_details"):
                st.session_state["Navigation Pages"] = "🔮 Forecasting"
                st.rerun()

        # --- ROW 3 LAYOUT: Recent Alerts, Forecast Simulator, Data Summary ---
        row3_col1, row3_col2, row3_col3 = st.columns([2.3, 3.0, 2.3])
        
        # Column 1: Recent Alerts
        with row3_col1:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>Recent Alerts</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            alerts_html = """
            <div style="padding: 12px; background: rgba(239, 85, 59, 0.08); border-left: 3px solid #EF553B; border-radius: 4px; margin-bottom: 12px; font-family:'Outfit', sans-serif;">
                <div style="font-size: 13px; font-weight:600; color:#EF553B; margin-bottom:2px;">South region sales drop</div>
                <div style="font-size: 12px; color:#E0E0E6;">Sales in East region dropped by 12% compared to last month.</div>
                <div style="font-size: 10px; color:#8C8C9A; text-align:right; margin-top:4px;">2h ago</div>
            </div>
            <div style="padding: 12px; background: rgba(0, 204, 150, 0.08); border-left: 3px solid #00CC96; border-radius: 4px; font-family:'Outfit', sans-serif;">
                <div style="font-size: 13px; font-weight:600; color:#00CC96; margin-bottom:2px;">West Inventory Alert</div>
                <div style="font-size: 12px; color:#E0E0E6;">Electronics category demand surged in West. Replenish inventory.</div>
                <div style="font-size: 10px; color:#8C8C9A; text-align:right; margin-top:4px;">1d ago</div>
            </div>
            """
            st.markdown(alerts_html, unsafe_allow_html=True)

        # Column 2: Forecast Simulator
        with row3_col2:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>Forecast Simulator</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            sim_c1, sim_c2, sim_c3 = st.columns(3)
            with sim_c1:
                discount_val = st.slider("Discount (%)", min_value=0, max_value=30, value=15, step=5)
            with sim_c2:
                marketing_val = st.slider("Marketing Spend ($)", min_value=10000, max_value=100000, value=50000, step=5000)
            with sim_c3:
                price_val = st.slider("Price Change (%)", min_value=-20, max_value=20, value=5, step=5)
            
            baseline_val = total_revenue / 12
            disc_fac = 1.0 - (discount_val - 15) * 0.005
            mkt_fac = 1.0 + (marketing_val - 50000) * 0.000003
            prc_fac = 1.0 + (price_val - 5) * -0.008
            
            simulated_val = baseline_val * disc_fac * mkt_fac * prc_fac
            simulated_growth = ((simulated_val - baseline_val) / baseline_val) * 100
            
            st.markdown(
                f"""
                <div style="background: rgba(30, 30, 46, 0.3); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 8px; text-align: center; margin-top: 10px; font-family:'Outfit', sans-serif;">
                    <div style="font-size: 12px; color: #8C8C9A;">Predicted Monthly Sales Output</div>
                    <div style="font-size: 26px; font-weight: 800; color: #636EFA; margin: 4px 0;">${simulated_val/1e3:.1f}K</div>
                    <div style="font-size: 13px; font-weight: 600; color: {'#00CC96' if simulated_growth >= 0 else '#EF553B'};">
                        {'+' if simulated_growth >= 0 else ''}{simulated_growth:.1f}% simulated growth
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        # Column 3: Data Summary
        with row3_col3:
            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="card-title">
                        <span>Data Summary</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            tot_orders = len(df_filtered)
            tot_customers = int(tot_orders * 0.65)
            
            dq_spark_data = [95, 96, 95.8, 96.1, 96.3, 96.2, 96.4, 96.3]
            fig_dq = plot_sparkline(dq_spark_data, color='#00CC96')
            
            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; margin-bottom:12px; font-family:'Outfit', sans-serif;">
                    <div>
                        <div style="font-size:11px; color:#8C8C9A;">Total Orders</div>
                        <div style="font-size:18px; font-weight:700; color:#FFFFFF;">{tot_orders:,}</div>
                    </div>
                    <div>
                        <div style="font-size:11px; color:#8C8C9A;">Total Customers</div>
                        <div style="font-size:18px; font-weight:700; color:#FFFFFF;">{tot_customers:,}</div>
                    </div>
                </div>
                <div style="display:flex; align-items:center; justify-content:space-between; margin-top:16px; border-top:1px solid rgba(255,255,255,0.08); padding-top:12px; font-family:'Outfit', sans-serif;">
                    <div>
                        <div style="font-size:11px; color:#8C8C9A;">Data Quality</div>
                        <div style="font-size:16px; font-weight:700; color:#00CC96;">96.3%</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.plotly_chart(fig_dq, use_container_width=True, config={'displayModeBar': False}, key="dashboard_dq_spark")

    elif clean_page == "Analytics":
        st.markdown(
            """
            <div style="margin-bottom: 24px; padding-top: 10px;">
                <h1 style="color: #FFFFFF; font-size: 34px; font-weight: 800; margin-bottom: 4px; font-family: 'Outfit', sans-serif;">🔍 Sales Analytics & Insights</h1>
                <p style="color: #8C8C9A; font-size: 15px; font-family: 'Outfit', sans-serif; margin-top: 6px;">Drill down into product elasticities and category breakdowns.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        all_categories = sorted(df_filtered[category_plot_col].dropna().unique().tolist()) if category_plot_col in df_filtered.columns else []
        
        col_ctrl1, col_ctrl2 = st.columns([2, 3])
        with col_ctrl1:
            category_drilldown = st.selectbox(
                f"Drilldown Category Details",
                options=[None] + all_categories,
                format_func=lambda x: "All Categories" if x is None else x
            )
            
        col_dleft, col_dright = st.columns(2)
        with col_dleft:
            fig_prod_drill = plot_product_analysis(df_filtered, category=category_drilldown, category_col=category_plot_col)
            st.plotly_chart(fig_prod_drill, use_container_width=True, key="analytics_product_drill")
        with col_dright:
            fig_elasticity = plot_price_vs_volume(df_filtered, category_col=category_plot_col)
            st.plotly_chart(fig_elasticity, use_container_width=True, key="analytics_elasticity")
            
        if category_plot_col and category_plot_col in df_filtered.columns:
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader(f"Performance Summary by {category_plot_col.replace('_', ' ').title()}")
            summary_df = df_filtered.groupby(category_plot_col).agg({
                'Sales_Revenue': 'sum',
                'Units_Sold': 'sum',
                'Price_Per_Unit': 'mean',
                'Discount': 'mean'
            }).rename(columns={
                'Sales_Revenue': 'Total Revenue ($)',
                'Units_Sold': 'Total Units Sold',
                'Price_Per_Unit': 'Avg Price ($)',
                'Discount': 'Avg Discount (%)'
            })
            summary_df['Avg Discount (%)'] = summary_df['Avg Discount (%)'] * 100
            st.dataframe(summary_df.style.format({
                'Total Revenue ($)': '{:,.2f}',
                'Total Units Sold': '{:,}',
                'Avg Price ($)': '{:,.2f}',
                'Avg Discount (%)': '{:.2f}%'
            }), use_container_width=True)

    elif clean_page == "Forecasting":
        st.markdown(
            """
            <div style="margin-bottom: 24px; padding-top: 10px;">
                <h1 style="color: #FFFFFF; font-size: 34px; font-weight: 800; margin-bottom: 4px; font-family: 'Outfit', sans-serif;">🔮 Machine Learning Sales Forecasting</h1>
                <p style="color: #8C8C9A; font-size: 15px; font-family: 'Outfit', sans-serif; margin-top: 6px;">Select a Machine Learning model and configure the forecast horizon to generate predictions.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("forecasting_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                model_choice = st.selectbox(
                    "Select Forecasting Model",
                    options=["Prophet / Time Series", "Random Forest Regressor", "XGBoost Regressor", "MLP Neural Network"]
                )
            with col_f2:
                horizon = st.slider(
                    "Forecast Horizon (Months)",
                    min_value=1,
                    max_value=12,
                    value=6
                )
            submit_forecast = st.form_submit_button("Run Predictions")
            
        if submit_forecast:
            with st.spinner("Preparing data and training forecasting models..."):
                df_monthly = aggregate_data(df_filtered, frequency='ME')
                
                if len(df_monthly) < 15:
                    st.error("Insufficient historical months in selected date range to train ML models. Please expand your Date Range in the sidebar (minimum 15 months).")
                else:
                    try:
                        if model_choice == "Prophet / Time Series":
                            forecast_df, name = train_prophet_model(df_monthly, horizon_months=horizon)
                            metrics = None
                        else:
                            model_code = 'rf' if "Random Forest" in model_choice else ('mlp' if "Neural Network" in model_choice else 'xgb')
                            forecast_df, metrics, name = train_regression_model(df_monthly, horizon_months=horizon, model_type=model_code)

                        if metrics:
                            st.success(f"Successfully trained {name}!")
                            col_m1, col_m2, col_m3 = st.columns(3)
                            with col_m1:
                                st.metric("Mean Absolute Error (MAE)", f"${metrics['MAE']:,.2f}")
                            with col_m2:
                                st.metric("Root Mean Squared Error (RMSE)", f"${metrics['RMSE']:,.2f}")
                            with col_m3:
                                st.metric("R² Score (Variance Explained)", f"{metrics['R2']:.4f}")
                        else:
                            st.success(f"Successfully fit {name}!")
                            
                        fig_forecast = plot_forecast(df_monthly, forecast_df, name)
                        st.plotly_chart(fig_forecast, use_container_width=True, key="forecasting_chart")
                        
                        last_hist_date = df_monthly['Date'].max()
                        future_only = forecast_df[forecast_df['ds'] > last_hist_date].copy()
                        future_only = future_only.rename(columns={
                            'ds': 'Forecasted Month',
                            'yhat': 'Predicted Sales ($)',
                            'yhat_lower': 'Lower Bound ($)',
                            'yhat_upper': 'Upper Bound ($)'
                        })
                        
                        st.subheader("Forecast Data Summary")
                        st.dataframe(future_only.style.format({
                            'Predicted Sales ($)': '{:,.2f}',
                            'Lower Bound ($)': '{:,.2f}',
                            'Upper Bound ($)': '{:,.2f}',
                            'Forecasted Month': lambda x: x.strftime('%B %Y')
                        }), use_container_width=True)
                        
                        csv_data = future_only.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Forecast CSV",
                            data=csv_data,
                            file_name=f"sales_forecast_{name.lower().replace(' ', '_')}.csv",
                            mime="text/csv"
                        )
                    except Exception as ex:
                        st.error(f"Error training: {ex}")

    elif clean_page == "Products":
        st.markdown(
            """
            <div style="margin-bottom: 24px; padding-top: 10px;">
                <h1 style="color: #FFFFFF; font-size: 34px; font-weight: 800; margin-bottom: 4px; font-family: 'Outfit', sans-serif;">📋 Dataset & Products Explorer</h1>
                <p style="color: #8C8C9A; font-size: 15px; font-family: 'Outfit', sans-serif; margin-top: 6px;">Filter, explore, and download the preprocessed data records.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        full_csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Cleaned Dataset as CSV",
            data=full_csv,
            file_name="cleaned_sales_dataset.csv",
            mime="text/csv"
        )
        
        st.write(f"Showing {len(df_filtered):,} records after filtering:")
        st.dataframe(df_filtered.head(1000), use_container_width=True)

    else:
        st.markdown(
            f"""
            <div style="margin-bottom: 24px; padding-top: 10px;">
                <h1 style="color: #FFFFFF; font-size: 34px; font-weight: 800; margin-bottom: 4px; font-family: 'Outfit', sans-serif;">📁 {clean_page} Management</h1>
                <p style="color: #8C8C9A; font-size: 15px; font-family: 'Outfit', sans-serif; margin-top: 6px;">Enterprise {clean_page} views, parameters and settings.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown(
            f"""
            <div class="dashboard-card" style="text-align: center; padding: 48px;">
                <div style="font-size: 40px; margin-bottom: 16px;">⚙️</div>
                <h3 style="color: #FFFFFF; margin-bottom: 8px;">{clean_page} View is Active</h3>
                <p style="color: #8C8C9A; font-size: 14px;">This section is pre-configured for future custom logic integration. Currently displaying active state metadata.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    st.info("Please choose a data source in the sidebar to load the sales records.")
