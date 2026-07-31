import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Import local modules
from src.sample_generator import generate_sample_data
from src.preprocessing import load_data, clean_data, engineer_features, aggregate_data
from src.forecasting import train_prophet_model, train_regression_model
from src.visualization import (
    plot_sales_trend, 
    plot_product_analysis, 
    plot_regional_analysis, 
    plot_price_vs_volume, 
    plot_forecast
)

# Page Configuration
st.set_page_config(
    page_title="Intelligent Sales Forecasting Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI CSS styling
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Outfit', sans-serif !important;
    }
    
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
        padding-top: 40px !important;
    }
    
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span {
        color: #E0E0E6 !important;
        font-weight: 500 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Multi-select styling */
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
    
    /* Dropdowns and select inputs styling */
    div[data-baseweb="select"] > div {
        background-color: #1E1E2E !important;
        border-color: #2B2B3D !important;
        color: #E0E0E6 !important;
        border-radius: 8px !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Glassmorphic KPI cards */
    .metric-card {
        background: rgba(30, 30, 46, 0.45);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: left;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        margin-bottom: 16px;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 110, 250, 0.6);
        box-shadow: 0 12px 40px 0 rgba(99, 110, 250, 0.25);
    }
    
    .metric-title {
        color: #8C8C9A;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1.8px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .metric-value {
        background: linear-gradient(90deg, #FFFFFF 0%, #D0D0E0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 6px;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .metric-delta {
        font-size: 14px;
        font-weight: 600;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .metric-delta.positive {
        color: #00CC96;
    }
    
    .metric-delta.negative {
        color: #EF553B;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(30, 30, 46, 0.4);
        padding: 8px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #8C8C9A;
        font-weight: 600;
        font-size: 15px;
        border: none;
        padding: 0px 24px;
        transition: all 0.3s ease;
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #FFFFFF;
        background-color: rgba(255, 255, 255, 0.03);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #636EFA 0%, #AB63FA 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 15px rgba(99, 110, 250, 0.3) !important;
    }
    
    /* Premium form styling */
    div[data-testid="stForm"] {
        background: rgba(30, 30, 46, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
    }
    
    /* Buttons styling */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #636EFA 0%, #AB63FA 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        box-shadow: 0 4px 15px rgba(99, 110, 250, 0.4) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 110, 250, 0.6) !important;
        color: white !important;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Pre-generate sample data so application works out of the box
SAMPLE_DATA_PATH = "data/sample_sales_data.csv"
generate_sample_data(SAMPLE_DATA_PATH)

# Header Title with Gradient Neon Line
header_html = """
<div style="margin-bottom: 32px; padding-top: 10px;">
    <h1 style="background: linear-gradient(90deg, #636EFA 0%, #AB63FA 50%, #00CC96 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 42px; font-weight: 800; margin-bottom: 4px; font-family: 'Outfit', sans-serif; display: inline-block;">📈 Intelligent Sales Forecasting Dashboard</h1>
    <p style="color: #8C8C9A; font-size: 16px; font-family: 'Outfit', sans-serif; margin-top: 6px;">Predict future sales using historical business data and visualize trends for management.</p>
    <div style="height: 2px; background: linear-gradient(90deg, rgba(99,110,250,0.8) 0%, rgba(171,99,250,0.5) 50%, rgba(255,255,255,0) 100%); margin-top: 16px; margin-bottom: 16px;"></div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# Sidebar - Configuration and Data Input
st.sidebar.markdown("## 📊 Configuration")

# Option to use sample data or upload file
data_source = st.sidebar.radio(
    "Data Source Selection",
    ["Use Sample Sales Dataset", "Upload Custom Sales CSV/Excel"]
)

uploaded_file = None
if data_source == "Upload Custom Sales CSV/Excel":
    uploaded_file = st.sidebar.file_uploader(
        "Upload sales records file",
        type=["csv", "xlsx", "xls"],
        help="Upload sales logs containing at least Date, Product Category, Product, Region, Units Sold, Price Per Unit, and Revenue."
    )

# Load data based on selection
@st.cache_data
def get_dataset(source_type, file_upload):
    if source_type == "Use Sample Sales Dataset" or file_upload is None:
        try:
            df = load_data(SAMPLE_DATA_PATH)
            return df, True
        except Exception as e:
            st.error(f"Error loading sample dataset: {e}")
            return None, False
    else:
        try:
            # Pass the uploaded file object itself to load_data
            df = load_data(file_upload)
            return df, False
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}. Please check file structure.")
            return None, False


df_raw, is_sample = get_dataset(data_source, uploaded_file)

if df_raw is not None:
    try:
        # Preprocessing & cleaning
        df_cleaned = clean_data(df_raw)
        df_engineered = engineer_features(df_cleaned)
        
        # Sidebar Filter Controls
        st.sidebar.markdown("## 🔍 Filtering Options")
        
        # Date range filter
        min_date = df_engineered['Date'].min().to_pydatetime()
        max_date = df_engineered['Date'].max().to_pydatetime()
        
        selected_dates = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Region and Product Category filters
        all_regions = sorted(df_engineered['Region'].unique().tolist())
        selected_regions = st.sidebar.multiselect(
            "Select Regions",
            options=all_regions,
            default=all_regions
        )
        
        all_categories = sorted(df_engineered['Product_Category'].unique().tolist())
        selected_categories = st.sidebar.multiselect(
            "Select Product Categories",
            options=all_categories,
            default=all_categories
        )
        
        # Apply filters
        # Handle date range selection correctly
        start_date = pd.to_datetime(selected_dates[0]) if len(selected_dates) >= 1 else pd.to_datetime(min_date)
        end_date = pd.to_datetime(selected_dates[1]) if len(selected_dates) >= 2 else pd.to_datetime(max_date)
        
        df_filtered = df_engineered[
            (df_engineered['Date'] >= start_date) & 
            (df_engineered['Date'] <= end_date) & 
            (df_engineered['Region'].isin(selected_regions)) & 
            (df_engineered['Product_Category'].isin(selected_categories))
        ]
        
        if df_filtered.empty:
            st.warning("No data matches the selected filters. Please adjust your criteria.")
        else:
            # Layout Setup: 4 Tabs
            tabs = st.tabs([
                "📊 Executive Summary", 
                "🔍 Deep-Dive Insights", 
                "🔮 Future Prediction", 
                "📋 Data Explorer"
            ])
            
            # --- TAB 1: Executive Summary ---
            with tabs[0]:
                st.subheader("Key Performance Indicators (KPIs)")
                
                # Metrics calculations
                total_revenue = df_filtered['Sales_Revenue'].sum()
                total_units = df_filtered['Units_Sold'].sum()
                avg_discount = df_filtered['Discount'].mean() * 100
                avg_order_value = total_revenue / len(df_filtered) if len(df_filtered) > 0 else 0
                
                # Compare to previous period if date range supports it
                # For simplicity, calculate base YoY metrics using year column
                if len(df_filtered['Year'].unique()) > 1:
                    latest_year = df_filtered['Year'].max()
                    prev_year = latest_year - 1
                    latest_sales = df_filtered[df_filtered['Year'] == latest_year]['Sales_Revenue'].sum()
                    prev_sales = df_filtered[df_filtered['Year'] == prev_year]['Sales_Revenue'].sum()
                    yoy_growth = ((latest_sales - prev_sales) / prev_sales * 100) if prev_sales > 0 else 0.0
                    yoy_growth_str = f"{yoy_growth:+.1f}% YoY"
                    growth_class = "positive" if yoy_growth >= 0 else "negative"
                else:
                    yoy_growth_str = "N/A (Multi-year data required)"
                    growth_class = "positive"
                
                # Custom CSS KPI Cards grid
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Total Revenue</div>
                        <div class="metric-value">${total_revenue:,.2f}</div>
                        <div class="metric-delta {growth_class}">{yoy_growth_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Units Sold</div>
                        <div class="metric-value">{total_units:,}</div>
                        <div class="metric-delta positive">Across all stores</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Avg Order Value (AOV)</div>
                        <div class="metric-value">${avg_order_value:,.2f}</div>
                        <div class="metric-delta positive">Average order size</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-title">Avg Discount Rate</div>
                        <div class="metric-value">{avg_discount:.1f}%</div>
                        <div class="metric-delta negative">Impact on margin</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Main historical trend line chart
                fig_trend = plot_sales_trend(df_filtered)
                st.plotly_chart(fig_trend, use_container_width=True, key="executive_trend_chart")
                
                col_left, col_right = st.columns(2)
                with col_left:
                    # Regional sales donut
                    fig_region = plot_regional_analysis(df_filtered)
                    st.plotly_chart(fig_region, use_container_width=True, key="executive_regional_chart")
                with col_right:
                    # Product category bar chart
                    fig_product = plot_product_analysis(df_filtered)
                    st.plotly_chart(fig_product, use_container_width=True, key="executive_product_chart")
            
            # --- TAB 2: Deep-Dive Insights ---
            with tabs[1]:
                st.subheader("Interactive Sales Analysis")
                st.markdown("Drill down into product elasticities and category breakdowns.")
                
                col_ctrl1, col_ctrl2 = st.columns(2)
                with col_ctrl1:
                    category_drilldown = st.selectbox(
                        "Drilldown Category Details",
                        options=[None] + all_categories,
                        format_func=lambda x: "All Categories" if x is None else x
                    )
                with col_ctrl2:
                    st.write("") # placeholder for alignment
                    
                col_dleft, col_dright = st.columns(2)
                with col_dleft:
                    # Category or product specific bar chart
                    fig_prod_drill = plot_product_analysis(df_filtered, category=category_drilldown)
                    st.plotly_chart(fig_prod_drill, use_container_width=True, key="drilldown_product_chart")
                with col_dright:
                    # Elasticity scatter plot
                    fig_elasticity = plot_price_vs_volume(df_filtered)
                    st.plotly_chart(fig_elasticity, use_container_width=True, key="drilldown_elasticity_chart")
                    
                # Extra statistics table
                st.subheader("Performance Summary by Category")
                summary_df = df_filtered.groupby('Product_Category').agg({
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
                
            # --- TAB 3: Future Prediction ---
            with tabs[2]:
                st.subheader("🔮 Machine Learning Sales Forecasting")
                st.markdown("Select a Machine Learning model and configure the forecast horizon to generate predictions.")
                
                # Model selection form container
                with st.form("forecasting_form"):
                    col_f1, col_f2 = st.columns(2)
                    with col_f1:
                        model_choice = st.selectbox(
                            "Select Forecasting Model",
                            options=["Prophet / Time Series", "Random Forest Regressor", "XGBoost Regressor"],
                            help="Choose Prophet for classical trend/seasonality modeling, or regression-based models for lag-based supervised forecasting."
                        )
                    with col_f2:
                        horizon = st.slider(
                            "Forecast Horizon (Months)",
                            min_value=1,
                            max_value=12,
                            value=6,
                            help="Number of future months to predict."
                        )
                        
                    submit_forecast = st.form_submit_button("Run Predictions")
                    
                if submit_forecast:
                    with st.spinner("Preparing data and training forecasting models..."):
                        # Aggregate the filtered data to monthly level
                        # Requires Date and Sales_Revenue columns
                        df_monthly = aggregate_data(df_filtered, frequency='ME')
                        
                        if len(df_monthly) < 15:
                            st.error("Insufficient historical months in selected date range to train ML models. Please expand your Date Range in the sidebar (minimum 15 months).")
                        else:
                            try:
                                if model_choice == "Prophet / Time Series":
                                    forecast_df, name = train_prophet_model(df_monthly, horizon_months=horizon)
                                    metrics = None
                                else:
                                    model_code = 'rf' if model_choice == "Random Forest Regressor" else 'xgb'
                                    forecast_df, metrics, name = train_regression_model(df_monthly, horizon_months=horizon, model_type=model_code)
                                    
                                # Display metrics if available
                                if metrics:
                                    st.success(f"Successfully trained {name}!")
                                    col_m1, col_m2, col_m3 = st.columns(3)
                                    with col_m1:
                                        st.metric("Mean Absolute Error (MAE)", f"${metrics['MAE']:,.2f}")
                                    with col_f2: # using existing columns layout or small delta
                                        pass
                                    with col_m2:
                                        st.metric("Root Mean Squared Error (RMSE)", f"${metrics['RMSE']:,.2f}")
                                    with col_m3:
                                        st.metric("R² Score (Variance Explained)", f"{metrics['R2']:.4f}")
                                else:
                                    st.success(f"Successfully fit {name}!")
                                    
                                # Plot prediction
                                fig_forecast = plot_forecast(df_monthly, forecast_df, name)
                                st.plotly_chart(fig_forecast, use_container_width=True, key="forecasting_prediction_chart")
                                
                                # Show future predictions in a table
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
                                
                                # Download as CSV option
                                csv_data = future_only.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label="📥 Download Forecast CSV",
                                    data=csv_data,
                                    file_name=f"sales_forecast_{name.lower().replace(' ', '_')}.csv",
                                    mime="text/csv"
                                )
                            except Exception as ex:
                                st.error(f"Error running model training/forecasting: {ex}")
                                import traceback
                                st.code(traceback.format_exc())
            
            # --- TAB 4: Data Explorer ---
            with tabs[3]:
                st.subheader("📋 Dataset Explorer")
                st.markdown("Filter, explore, and download the preprocessed data records.")
                
                # Download full preprocessed dataset as CSV
                full_csv = df_filtered.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Cleaned Dataset as CSV",
                    data=full_csv,
                    file_name="cleaned_sales_dataset.csv",
                    mime="text/csv"
                )
                
                # Show dataset details
                st.write(f"Showing {len(df_filtered):,} records after filtering:")
                st.dataframe(df_filtered.head(1000), use_container_width=True)
                if len(df_filtered) > 1000:
                    st.info("Showing first 1,000 rows. Download full CSV to view the entire dataset.")
                    
    except Exception as e:
        st.error(f"Data processing error: {e}")
        import traceback
        st.code(traceback.format_exc())
else:
    st.info("Please choose a data source in the sidebar to load the sales records.")
