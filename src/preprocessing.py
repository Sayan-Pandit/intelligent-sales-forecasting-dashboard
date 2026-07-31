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
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        raise ValueError("Missing 'Date' column.")
        
    # Standardize numeric columns
    numeric_cols = ['Units_Sold', 'Price_Per_Unit', 'Discount', 'Sales_Revenue']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # Drop rows with missing dates or invalid records
    df = df.dropna(subset=['Date'])
    
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
