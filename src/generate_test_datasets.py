import os
import pandas as pd
import numpy as np

def generate_noise_dataset(output_path="data/overfitting_noise_test.csv", start_date="2023-01-01", end_date="2026-06-30"):
    """
    Generates a dataset with 90% random noise and almost no trend/seasonality.
    Overfitted models will try to fit the noise, showing a massive gap 
    between training performance and testing performance.
    """
    print(f"Generating noise dataset: {output_path}")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    np.random.seed(101)
    
    records = []
    base_sales = 5000.0
    
    for date in dates:
        # High noise (standard deviation is 50% of the base sales)
        noise = np.random.normal(0, 2500.0)
        sales = max(100.0, base_sales + noise)
        
        # Simple categorical variables
        category = np.random.choice(["Electronics", "Accessories", "Wearables", "Home Appliances", "Others"])
        product = f"Product_{np.random.randint(1, 5)}"
        region = np.random.choice(["North", "East", "South", "West"])
        qty = np.random.randint(1, 10)
        price = round(sales / qty, 2)
        
        records.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Product_Category": category,
            "Product": product,
            "Region": region,
            "Units_Sold": qty,
            "Price_Per_Unit": price,
            "Discount": 0.0,
            "Sales_Revenue": round(sales, 2)
        })
        
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} records.")

def generate_structural_break_dataset(output_path="data/structural_break_test.csv", start_date="2023-01-01", end_date="2026-06-30"):
    """
    Generates a dataset where the trend abruptly changes in the middle of 2025.
    Helps check if models overfit to past trends and fail to adapt to structural breaks.
    """
    print(f"Generating structural break dataset: {output_path}")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    np.random.seed(202)
    
    records = []
    break_date = pd.to_datetime("2025-06-01")
    
    for date in dates:
        # Seasonality
        month_season = 1.0 + 0.15 * np.sin(2 * np.pi * date.month / 12)
        
        # Trend
        if date < break_date:
            # Positive trend up to mid-2025
            trend = 3000.0 + (date - pd.to_datetime(start_date)).days * 2.0
        else:
            # Abrupt drop and flat/negative trend afterwards
            trend = 2200.0 - (date - break_date).days * 0.5
            
        noise = np.random.normal(0, 300.0)
        sales = max(50.0, (trend * month_season) + noise)
        
        category = np.random.choice(["Electronics", "Accessories", "Wearables", "Home Appliances", "Others"])
        product = f"Product_{np.random.randint(1, 5)}"
        region = np.random.choice(["North", "East", "South", "West"])
        qty = np.random.randint(1, 5)
        price = round(sales / qty, 2)
        
        records.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Product_Category": category,
            "Product": product,
            "Region": region,
            "Units_Sold": qty,
            "Price_Per_Unit": price,
            "Discount": 0.0,
            "Sales_Revenue": round(sales, 2)
        })
        
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} records.")

def generate_clean_seasonality_dataset(output_path="data/seasonal_clean_test.csv", start_date="2023-01-01", end_date="2026-06-30"):
    """
    Generates a dataset with very clean seasonality and low noise.
    Expected: Models should have extremely high train and test accuracy (no overfitting).
    """
    print(f"Generating clean seasonal dataset: {output_path}")
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    np.random.seed(303)
    
    records = []
    
    for date in dates:
        # Perfect sinus trend + yearly trend
        trend = 4000.0 + (date - pd.to_datetime(start_date)).days * 0.8
        seasonality = 1.0 + 0.3 * np.sin(2 * np.pi * date.dayofyear / 365)
        
        # Very low noise
        noise = np.random.normal(0, 50.0)
        sales = max(100.0, (trend * seasonality) + noise)
        
        category = np.random.choice(["Electronics", "Accessories", "Wearables", "Home Appliances", "Others"])
        product = f"Product_{np.random.randint(1, 5)}"
        region = np.random.choice(["North", "East", "South", "West"])
        qty = np.random.randint(1, 5)
        price = round(sales / qty, 2)
        
        records.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Product_Category": category,
            "Product": product,
            "Region": region,
            "Units_Sold": qty,
            "Price_Per_Unit": price,
            "Discount": 0.0,
            "Sales_Revenue": round(sales, 2)
        })
        
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} records.")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    generate_noise_dataset()
    generate_structural_break_dataset()
    generate_clean_seasonality_dataset()
