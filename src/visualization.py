import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Set standard design system color palette
COLORS = {
    'primary': '#636EFA',      # Deep Electric Blue
    'secondary': '#AB63FA',    # Electric Purple
    'accent': '#00CC96',       # Neon Green
    'contrast': '#AB63FA',     # Purple
    'warning': '#EF553B',      # Coral Red
    'background': '#0F0F1A',   # Deep Navy Black
    'card_bg': 'rgba(30, 30, 46, 0.45)', # Glassmorphic card
    'text': '#E0E0E6',         # Off-white
    'text_muted': '#8C8C9A',   # Muted grey
    'grid': '#2B2B3D'          # Grid lines
}

def apply_layout_theme(fig):
    """
    Applies a premium, modern dark-mode style to the Plotly figure.
    """
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=COLORS['text'], family="Outfit, Inter, sans-serif"),
        title_font=dict(size=16, color='#FFFFFF', family="Outfit, Inter, sans-serif"),
        xaxis=dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['grid'],
            zeroline=False,
            gridwidth=0.5,
            tickfont=dict(color=COLORS['text_muted']),
            title_font=dict(color=COLORS['text_muted'])
        ),
        yaxis=dict(
            gridcolor=COLORS['grid'],
            linecolor=COLORS['grid'],
            zeroline=False,
            gridwidth=0.5,
            tickfont=dict(color=COLORS['text_muted']),
            title_font=dict(color=COLORS['text_muted'])
        ),
        legend=dict(
            font=dict(color=COLORS['text']),
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)'
        ),
        hovermode="x unified",
        margin=dict(l=30, r=30, t=40, b=30)
    )
    return fig

def plot_sparkline(series, color='#AB63FA'):
    """
    Plots a tiny, clean sparkline with no axes or margins.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(series))),
        y=list(series),
        mode='lines',
        line=dict(color=color, width=2.5),
        fill='tozeroy',
        fillcolor='rgba(171, 99, 250, 0.12)' if color == '#AB63FA' else 'rgba(99, 110, 250, 0.12)',
        hoverinfo='skip'
    ))
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=40
    )
    return fig

def plot_sales_trend(df, forecast_df=None):
    """
    Plots actual sales and overlays forecasted sales if available.
    """
    monthly_sales = df.groupby(pd.Grouper(key='Date', freq='ME')).agg({'Sales_Revenue': 'sum'}).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_sales['Date'],
        y=monthly_sales['Sales_Revenue'],
        mode='lines+markers',
        name='Actual Sales',
        line=dict(color=COLORS['primary'], width=3),
        marker=dict(size=6, color=COLORS['primary']),
        hovertemplate='<b>Date</b>: %{x|%B %Y}<br><b>Actual Sales</b>: $%{y:,.2f}<extra></extra>'
    ))
    
    if forecast_df is not None:
        # Align dates and filter only future predictions
        last_hist_date = monthly_sales['Date'].max()
        forecast_df = forecast_df.copy()
        forecast_df['ds'] = pd.to_datetime(forecast_df['ds'])
        future_fc = forecast_df[forecast_df['ds'] > last_hist_date].sort_values('ds')
        
        if len(future_fc) > 0:
            last_actual_val = monthly_sales.loc[monthly_sales['Date'] == last_hist_date, 'Sales_Revenue'].values[0]
            last_actual_row = pd.DataFrame({
                'ds': [last_hist_date],
                'yhat': [last_actual_val]
            })
            future_fc_conn = pd.concat([last_actual_row, future_fc], ignore_index=True)
            
            fig.add_trace(go.Scatter(
                x=future_fc_conn['ds'],
                y=future_fc_conn['yhat'],
                mode='lines+markers',
                name='Forecasted Sales',
                line=dict(color=COLORS['secondary'], width=3, dash='dash'),
                marker=dict(size=6, color=COLORS['secondary']),
                hovertemplate='<b>Date</b>: %{x|%B %Y}<br><b>Forecasted</b>: $%{y:,.2f}<extra></extra>'
            ))
            
    fig.update_layout(
        title="Sales Trend Overview",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return apply_layout_theme(fig)

def plot_product_analysis(df, category=None, category_col='Product_Category', product_col='Product'):
    """
    Plots product sales revenue breakdown.
    If category is provided, drills down to specific products in that category.
    """
    if category_col not in df.columns:
        other_cols = [c for c in df.columns if c not in ['Date', 'Sales_Revenue', 'Units_Sold', 'Price_Per_Unit', 'Discount', 'Year', 'Month', 'Quarter', 'DayOfWeek', 'IsWeekend', 'MonthName', 'DayOfYear']]
        category_col = other_cols[0] if len(other_cols) > 0 else None
        
    if category_col is None:
        fig = go.Figure()
        fig.update_layout(title="No categorical breakdown available")
        return apply_layout_theme(fig)
        
    if category and category_col in df.columns:
        if product_col not in df.columns:
            product_col = category_col
        filtered_df = df[df[category_col] == category]
        group_col = product_col
        title = f"Revenue by {product_col} in {category}"
    else:
        filtered_df = df
        group_col = category_col
        title = f"Revenue by {category_col.replace('_', ' ')}"
        
    prod_sales = filtered_df.groupby(group_col).agg({
        'Sales_Revenue': 'sum',
        'Units_Sold': 'sum'
    }).reset_index().sort_values('Sales_Revenue', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=prod_sales[group_col],
        x=prod_sales['Sales_Revenue'],
        orientation='h',
        marker=dict(
            color=COLORS['primary'],
            line=dict(color='rgba(255,255,255,0.1)', width=0.5)
        ),
        hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Revenue ($)",
        yaxis_title=None
    )
    
    return apply_layout_theme(fig)

def plot_regional_analysis(df, region_col='Region'):
    """
    Plots regional sales on a styled dark world map using choropleth projection.
    """
    if region_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="No regional data available")
        return apply_layout_theme(fig)
        
    region_sales = df.groupby(region_col).agg({'Sales_Revenue': 'sum'}).reset_index()
    
    # Map regions to ISO-3 codes
    iso_map = {
        'North': ['USA', 'CAN'],
        'East': ['GBR', 'DEU', 'FRA', 'ITA', 'ESP'],
        'South': ['BRA', 'ARG', 'COL', 'PER'],
        'West': ['AUS', 'JPN', 'IND', 'CHN']
    }
    
    rows = []
    for _, row in region_sales.iterrows():
        reg = row[region_col]
        sales = row['Sales_Revenue']
        countries = iso_map.get(reg, ['USA'])
        sales_per_country = sales / len(countries)
        for country in countries:
            rows.append({
                'Country': country,
                'Sales': sales_per_country,
                'Region': reg
            })
            
    map_df = pd.DataFrame(rows)
    
    fig = px.choropleth(
        map_df,
        locations="Country",
        color="Sales",
        hover_name="Region",
        color_continuous_scale=[
            [0.0, '#121225'],
            [0.5, '#636EFA'],
            [1.0, '#AB63FA']
        ],
        labels={'Sales': 'Revenue'}
    )
    
    fig.update_layout(
        title="Sales by Region",
        coloraxis_colorbar=dict(tickfont=dict(color=COLORS['text_muted'])),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor=COLORS['grid'],
            projection_type='equirectangular',
            backgroundcolor='rgba(0,0,0,0)',
            landcolor='#16162B',
            lakecolor='#0F0F1A',
            showland=True,
            showlakes=True,
            subunitcolor=COLORS['grid']
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        height=320
    )
    
    return apply_layout_theme(fig)

def plot_category_donut(df, category_col='Product_Category'):
    """
    Plots a styled donut chart for category sales breakdown with total sales in the center.
    """
    if category_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="No category data available")
        return apply_layout_theme(fig)
        
    cat_sales = df.groupby(category_col).agg({'Sales_Revenue': 'sum'}).reset_index()
    total_rev = cat_sales['Sales_Revenue'].sum()
    
    fig = px.pie(
        cat_sales,
        values='Sales_Revenue',
        names=category_col,
        hole=0.6,
        color_discrete_sequence=[COLORS['primary'], COLORS['secondary'], COLORS['accent'], '#FFA15A', '#19D3F3']
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent',
        hovertemplate='<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Share: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        title="Sales by Category",
        annotations=[dict(
            text=f"<span style='font-size:11px;color:#8C8C9A;'>Total</span><br><b style='font-size:16px;color:#FFFFFF;'>${total_rev/1e6:.2f}M</b>",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(family="Outfit, Inter, sans-serif")
        )],
        legend=dict(
            orientation="v",
            yanchor="middle", y=0.5,
            xanchor="left", x=1.05,
            font=dict(size=11, color=COLORS['text_muted'])
        ),
        margin=dict(l=10, r=90, t=40, b=10),
        height=320
    )
    
    return apply_layout_theme(fig)

def plot_price_vs_volume(df, category_col='Product_Category'):
    """
    Plots a scatter plot of Price vs. Units Sold, sized by Revenue.
    """
    if category_col not in df.columns:
        other_cols = [c for c in df.columns if c not in ['Date', 'Sales_Revenue', 'Units_Sold', 'Price_Per_Unit', 'Discount', 'Year', 'Month', 'Quarter', 'DayOfWeek', 'IsWeekend', 'MonthName', 'DayOfYear']]
        category_col = other_cols[0] if len(other_cols) > 0 else None
        
    # Sample a subset to keep performance smooth if data is massive
    sampled_df = df.sample(min(2000, len(df)), random_state=42) if len(df) > 2000 else df
    
    hover_cols = [c for c in ['Product', 'Region', 'Discount'] if c in df.columns]
    
    fig = px.scatter(
        sampled_df,
        x="Price_Per_Unit",
        y="Units_Sold",
        color=category_col if category_col else None,
        size="Sales_Revenue",
        hover_data=hover_cols,
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
