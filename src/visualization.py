import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Set standard design system color palette
COLORS = {
    'primary': '#636EFA',      # Deep Electric Blue
    'secondary': '#EF553B',    # Soft Coral Red
    'accent': '#00CC96',       # Fresh Green
    'contrast': '#AB63FA',     # Purple
    'background': '#1E1E2E',   # Dark Slate
    'text': '#E0E0E6',         # Off-white
    'grid': '#3A3A4A',         # Subtle Grid Line
    'card_bg': '#2B2B3D'       # Card Slate
}

def apply_layout_theme(fig):
    """
    Applies a premium, modern dark-mode style to the Plotly figure.
    """
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORS['text'], family="Outfit, Inter, sans-serif"),
        title_font=dict(size=18, color='#FFFFFF', family="Outfit, Inter, sans-serif"),
        xaxis=dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['grid'],
            tickfont=dict(color=COLORS['text']),
            title_font=dict(color=COLORS['text'])
        ),
        yaxis=dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['grid'],
            tickfont=dict(color=COLORS['text']),
            title_font=dict(color=COLORS['text'])
        ),
        legend=dict(
            font=dict(color=COLORS['text']),
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)'
        ),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig

def plot_sales_trend(df):
    """
    Plots historical sales revenue trend.
    """
    # Group by Date
    monthly_sales = df.groupby(pd.Grouper(key='Date', freq='ME')).agg({'Sales_Revenue': 'sum'}).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_sales['Date'],
        y=monthly_sales['Sales_Revenue'],
        mode='lines+markers',
        name='Sales Revenue',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=6, color=COLORS['accent']),
        hovertemplate='<b>Date</b>: %{x|%B %Y}<br><b>Sales</b>: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Monthly Sales Revenue Trend",
        xaxis_title="Date",
        yaxis_title="Sales Revenue ($)"
    )
    
    return apply_layout_theme(fig)

def plot_product_analysis(df, category=None):
    """
    Plots product sales revenue breakdown.
    If category is provided, drills down to specific products in that category.
    """
    if category:
        filtered_df = df[df['Product_Category'] == category]
        group_col = 'Product'
        title = f"Sales Revenue by Product in {category}"
    else:
        filtered_df = df
        group_col = 'Product_Category'
        title = "Sales Revenue by Product Category"
        
    prod_sales = filtered_df.groupby(group_col).agg({
        'Sales_Revenue': 'sum',
        'Units_Sold': 'sum'
    }).reset_index().sort_values('Sales_Revenue', ascending=True)
    
    fig = go.Figure()
    
    # Horizontal Bar Chart
    fig.add_trace(go.Bar(
        y=prod_sales[group_col],
        x=prod_sales['Sales_Revenue'],
        orientation='h',
        marker=dict(
            color=COLORS['primary'],
            line=dict(color='#FFFFFF', width=0.5)
        ),
        hovertemplate='<b>' + group_col + '</b>: %{y}<br><b>Revenue</b>: $%{x:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Sales Revenue ($)",
        yaxis_title=group_col
    )
    
    return apply_layout_theme(fig)

def plot_regional_analysis(df):
    """
    Plots a donut chart for regional sales share.
    """
    region_sales = df.groupby('Region').agg({'Sales_Revenue': 'sum'}).reset_index()
    
    fig = px.pie(
        region_sales,
        values='Sales_Revenue',
        names='Region',
        hole=0.4,
        color_discrete_sequence=[COLORS['primary'], COLORS['secondary'], COLORS['accent'], COLORS['contrast']]
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>Region</b>: %{label}<br><b>Revenue</b>: $%{value:,.2f}<br><b>Share</b>: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        title="Sales Contribution by Region",
        legend_title="Region"
    )
    
    return apply_layout_theme(fig)

def plot_price_vs_volume(df):
    """
    Plots a scatter plot of Price vs. Units Sold, sized by Revenue.
    """
    # Sample a subset to keep performance smooth if data is massive
    sampled_df = df.sample(min(2000, len(df)), random_state=42) if len(df) > 2000 else df
    
    fig = px.scatter(
        sampled_df,
        x="Price_Per_Unit",
        y="Units_Sold",
        color="Product_Category",
        size="Sales_Revenue",
        hover_data=["Product", "Region", "Discount"],
        color_discrete_sequence=[COLORS['primary'], COLORS['secondary'], COLORS['accent'], COLORS['contrast']],
        title="Price Elasticity (Price vs. Quantity Sold)"
    )
    
    fig.update_layout(
        xaxis_title="Price Per Unit ($)",
        yaxis_title="Units Sold"
    )
    
    return apply_layout_theme(fig)

def plot_forecast(historical_df, forecast_df, model_name):
    """
    Plots historical sales trend along with future predictions and prediction intervals.
    """
    # Ensure Date column is sorted
    historical_df = historical_df.groupby(pd.Grouper(key='Date', freq='ME')).agg({'Sales_Revenue': 'sum'}).reset_index()
    
    # Historical and predicted date ranges
    # Separating future predictions (where 'ds' > last historical date)
    last_hist_date = historical_df['Date'].max()
    
    # Align dates
    forecast_df = forecast_df.copy()
    forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])
    
    # Split forecast into historical fit and future forecast
    future_forecast = forecast_df[forecast_df['ds'] > last_hist_date].sort_values('ds')
    
    fig = go.Figure()
    
    # 1. Historical Actual Sales
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Sales_Revenue'],
        mode='lines+markers',
        name='Historical Sales',
        line=dict(color=COLORS['text'], width=2),
        marker=dict(size=4)
    ))
    
    if len(future_forecast) > 0:
        # We also want to connect the historical line with the forecast line
        last_hist_row = pd.DataFrame({
            'ds': [last_hist_date],
            'yhat': [historical_df.loc[historical_df['Date'] == last_hist_date, 'Sales_Revenue'].values[0]],
            'yhat_lower': [historical_df.loc[historical_df['Date'] == last_hist_date, 'Sales_Revenue'].values[0]],
            'yhat_upper': [historical_df.loc[historical_df['Date'] == last_hist_date, 'Sales_Revenue'].values[0]]
        })
        future_forecast_conn = pd.concat([last_hist_row, future_forecast], ignore_index=True)
        
        # 2. Prediction Interval Band
        fig.add_trace(go.Scatter(
            x=pd.concat([future_forecast_conn['ds'], future_forecast_conn['ds'].iloc[::-1]]),
            y=pd.concat([future_forecast_conn['yhat_upper'], future_forecast_conn['yhat_lower'].iloc[::-1]]),
            fill='toself',
            fillcolor='rgba(99, 110, 250, 0.15)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=True,
            name='95% Confidence Band'
        ))
        
        # 3. Future Forecast
        fig.add_trace(go.Scatter(
            x=future_forecast_conn['ds'],
            y=future_forecast_conn['yhat'],
            mode='lines+markers',
            name=f'{model_name} Forecast',
            line=dict(color=COLORS['primary'], width=3, dash='dash'),
            marker=dict(size=6, color=COLORS['accent'])
        ))
        
    fig.update_layout(
        title=f"Sales Forecast using {model_name}",
        xaxis_title="Date",
        yaxis_title="Sales Revenue ($)"
    )
    
    return apply_layout_theme(fig)
