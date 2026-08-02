import pandas as pd
import numpy as np

def load_data(file_input):
    """
    Loads sales data from a CSV or Excel file (either local path string or file-like buffer).
    """
    if isinstance(file_input, str):
        file_name = file_input
    elif hasattr(file_input, 'name'):
        file_name = file_input.name
    else:
        raise ValueError("Invalid file input type. Must be a file path string or UploadedFile.")
        
    if file_name.endswith('.csv'):
        try:
            df = pd.read_csv(file_input)
        except (UnicodeDecodeError, Exception) as e:
            # If standard utf-8 fails, try common fallbacks
            if hasattr(file_input, 'seek'):
                file_input.seek(0)
            try:
                df = pd.read_csv(file_input, encoding='latin1')
            except Exception:
                if hasattr(file_input, 'seek'):
                    file_input.seek(0)
                try:
                    df = pd.read_csv(file_input, encoding='cp1252')
                except Exception:
                    # Reraise the original UnicodeDecodeError if everything fails
                    raise e
    elif file_name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file_input)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
    return df


def calculate_profit(df):
    """
    Calculates profit and profit margin dynamically based on product categories.
    """
    df = df.copy()
    MARGINS = {
        'Electronics': 0.2134,
        'Accessories': 0.25,
        'Wearables': 0.32,
        'Home Appliances': 0.18,
        'Others': 0.15
    }
    
    category_col = None
    for col in df.columns:
        if col.lower().replace(' ', '_') == 'product_category':
            category_col = col
            break
            
    if category_col:
        df['Profit_Margin'] = df[category_col].map(MARGINS).fillna(0.22)
    else:
        df['Profit_Margin'] = 0.2134
        
    df['Total_Profit'] = df['Sales_Revenue'] * df['Profit_Margin']
    return df


def clean_data(df):
    """
    Cleans the input sales dataset.
    """
    # Create a copy to avoid SettingWithCopyWarning
    df = df.copy()
    
    # Rename columns to standard casing if needed
    col_mapping = {col.lower().replace(' ', '_'): col for col in df.columns}
    
    # Check for required columns and standardize names
    required_cols = ['date', 'product_category', 'product', 'region', 'units_sold', 'price_per_unit', 'discount', 'sales_revenue']
    
    standardized_cols = {}
    for req in required_cols:
        matched = False
        for low_col, orig_col in col_mapping.items():
            if req == low_col:
                standardized_cols[orig_col] = req.title() if req != 'sales_revenue' else 'Sales_Revenue'
                matched = True
                break
        if not matched:
            # If a column doesn't exist, we will try to handle it or create default
            if req == 'discount':
                df['Discount'] = 0.0
            elif req == 'sales_revenue' and 'units_sold' in col_mapping and 'price_per_unit' in col_mapping:
                # We can calculate it later
                pass
            else:
                raise ValueError(f"Missing required column: {req.title()}")
                
    df = df.rename(columns=standardized_cols)
    
    # Map back column names based on expected names
    expected_cols = {
        'Date': 'Date',
        'Product_Category': 'Product_Category',
        'Product': 'Product',
        'Region': 'Region',
        'Units_Sold': 'Units_Sold',
        'Price_Per_Unit': 'Price_Per_Unit',
        'Discount': 'Discount',
        'Sales_Revenue': 'Sales_Revenue'
    }
    
    # Check if we have Sales_Revenue, otherwise calculate it
    if 'Sales_Revenue' not in df.columns and 'Units_Sold' in df.columns and 'Price_Per_Unit' in df.columns:
        disc = df['Discount'] if 'Discount' in df.columns else 0.0
        df['Sales_Revenue'] = df['Units_Sold'] * df['Price_Per_Unit'] * (1.0 - disc)
        
    # Convert date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True, errors='coerce').dt.tz_localize(None)
    else:
        raise ValueError("Missing 'Date' column.")
        
    # Standardize numeric columns
    numeric_cols = ['Units_Sold', 'Price_Per_Unit', 'Discount', 'Sales_Revenue']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # Drop rows with missing dates or invalid records
    df = df.dropna(subset=['Date'])
    
    # Calculate profit metrics
    df = calculate_profit(df)
    
    return df

def engineer_features(df):
    """
    Engineers date/time features from the 'Date' column.
    """
    df = df.copy()
    
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = df['Date'].dt.quarter
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    df['IsWeekend'] = df['DayOfWeek'].isin([5, 6]).astype(int)
    df['MonthName'] = df['Date'].dt.strftime('%b')
    df['DayOfYear'] = df['Date'].dt.dayofyear
    
    return df

def aggregate_data(df, frequency='ME'):
    """
    Aggregates transactions to a specified frequency (e.g., 'D' for daily, 'W' for weekly, 'ME' for monthly).
    Returns aggregated dataframe grouped by Date.
    """
    # Group by date aggregated to frequency
    df_agg = df.groupby(pd.Grouper(key='Date', freq=frequency)).agg({
        'Sales_Revenue': 'sum',
        'Units_Sold': 'sum',
        'Discount': 'mean'
    }).reset_index()
    
    return df_agg

def suggest_mappings(df):
    """
    Attempts to identify which columns contain the date and sales values.
    Returns: (date_column, sales_column)
    """
    date_col = None
    sales_col = None
    
    # Lowercase names for comparison
    cols = list(df.columns)
    cols_low = [c.lower() for c in cols]
    
    # 1. Try to find a date column
    # Check by datetime datatype first
    for i, col in enumerate(cols):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_col = col
            break
            
    # Check by column name keywords if datatype check didn't work
    if date_col is None:
        date_keywords = ['date', 'time', 'timestamp', 'ds', 'period', 'year', 'day', 'month']
        for kw in date_keywords:
            for i, col_low in enumerate(cols_low):
                if kw in col_low:
                    date_col = cols[i]
                    break
            if date_col is not None:
                break
                
    # Fallback to the first column if still not found
    if date_col is None and len(cols) > 0:
        date_col = cols[0]
        
    # 2. Try to find a sales column
    # Check by keywords
    sales_keywords = ['revenue', 'sales', 'sales_revenue', 'amount', 'total', 'turnover', 'sales_amount', 'y']
    for kw in sales_keywords:
        for i, col_low in enumerate(cols_low):
            if kw == col_low:  # Exact match first
                sales_col = cols[i]
                break
        if sales_col is not None:
            break
            
    if sales_col is None:
        for kw in sales_keywords:
            for i, col_low in enumerate(cols_low):
                if kw in col_low:  # Partial match
                    sales_col = cols[i]
                    break
            if sales_col is not None:
                break
                
    # Check by numerical datatype as fallback
    if sales_col is None:
        for col in cols:
            if col != date_col and pd.api.types.is_numeric_dtype(df[col]):
                sales_col = col
                break
                
    # Fallback to the second column or the date column if nothing else
    if sales_col is None and len(cols) > 1:
        sales_col = cols[1] if cols[1] != date_col else cols[0]
    elif sales_col is None and len(cols) > 0:
        sales_col = cols[0]
        
    return date_col, sales_col

def map_and_clean_data(df, date_col, sales_col):
    """
    Standardizes column names for any dataset using the user's selected date and sales columns.
    Enforces types and handles missing values.
    """
    df = df.copy()
    
    # Safety checks
    if date_col not in df.columns or sales_col not in df.columns:
        raise ValueError("Selected columns do not exist in the dataset.")
        
    # Rename mapped columns
    rename_dict = {date_col: 'Date', sales_col: 'Sales_Revenue'}
    df = df.rename(columns=rename_dict)
    
    # Parse Date
    df['Date'] = pd.to_datetime(df['Date'], utc=True, errors='coerce').dt.tz_localize(None)
    df = df.dropna(subset=['Date'])
    
    # Parse Sales
    df['Sales_Revenue'] = pd.to_numeric(df['Sales_Revenue'], errors='coerce').fillna(0.0)
    
    # Standardize/Fill other optional columns
    cols_low = [c.lower() for c in df.columns]
    
    # Units Sold
    units_col = None
    for i, col_low in enumerate(cols_low):
        if 'units' in col_low or 'qty' in col_low or 'quantity' in col_low:
            units_col = df.columns[i]
            break
    if units_col and units_col not in ['Date', 'Sales_Revenue']:
        df['Units_Sold'] = pd.to_numeric(df[units_col], errors='coerce').fillna(1)
    else:
        df['Units_Sold'] = 1  # Default to 1 if not present
        
    # Discount
    discount_col = None
    for i, col_low in enumerate(cols_low):
        if 'discount' in col_low:
            discount_col = df.columns[i]
            break
    if discount_col and discount_col not in ['Date', 'Sales_Revenue', 'Units_Sold']:
        df['Discount'] = pd.to_numeric(df[discount_col], errors='coerce').fillna(0.0)
        # Normalize if expressed as percentage (e.g. > 1.0)
        if df['Discount'].max() > 1.0:
            df['Discount'] = df['Discount'] / 100.0
    else:
        df['Discount'] = 0.0
        
    # Price Per Unit
    price_col = None
    for i, col_low in enumerate(cols_low):
        if 'price' in col_low or 'rate' in col_low:
            price_col = df.columns[i]
            break
    if price_col and price_col not in ['Date', 'Sales_Revenue', 'Units_Sold', 'Discount']:
        df['Price_Per_Unit'] = pd.to_numeric(df[price_col], errors='coerce').fillna(df['Sales_Revenue'])
    else:
        df['Price_Per_Unit'] = df['Sales_Revenue']

    # Region
    region_col = None
    for i, col_low in enumerate(cols_low):
        if col_low in ['region', 'country', 'territory', 'zone', 'market', 'state']:
            region_col = df.columns[i]
            break
    if not region_col:
        for i, col_low in enumerate(cols_low):
            if 'region' in col_low or 'country' in col_low or 'territory' in col_low:
                region_col = df.columns[i]
                break
    if region_col and region_col not in ['Date', 'Sales_Revenue', 'Units_Sold', 'Discount', 'Price_Per_Unit']:
        df['Region'] = df[region_col].astype(str).fillna('Global')
    else:
        df['Region'] = 'Global'

    # Product_Category
    cat_col = None
    for i, col_low in enumerate(cols_low):
        if col_low in ['product_category', 'category', 'class', 'department', 'dept']:
            cat_col = df.columns[i]
            break
    if not cat_col:
        for i, col_low in enumerate(cols_low):
            if 'category' in col_low or 'dept' in col_low or 'class' in col_low:
                cat_col = df.columns[i]
                break
    if cat_col and cat_col not in ['Date', 'Sales_Revenue', 'Units_Sold', 'Discount', 'Price_Per_Unit', 'Region']:
        df['Product_Category'] = df[cat_col].astype(str).fillna('General')
    else:
        df['Product_Category'] = 'General'

    # Product
    prod_col = None
    for i, col_low in enumerate(cols_low):
        if col_low in ['product', 'item', 'sku', 'product_name']:
            prod_col = df.columns[i]
            break
    if not prod_col:
        for i, col_low in enumerate(cols_low):
            if 'product' in col_low or 'item' in col_low or 'name' in col_low:
                prod_col = df.columns[i]
                break
    if prod_col and prod_col not in ['Date', 'Sales_Revenue', 'Units_Sold', 'Discount', 'Price_Per_Unit', 'Region', 'Product_Category']:
        df['Product'] = df[prod_col].astype(str).fillna('Standard Product')
    else:
        df['Product'] = 'Standard Product'
        
    # Calculate profit metrics
    df = calculate_profit(df)
    
    return df

