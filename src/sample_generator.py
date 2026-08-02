import os
import pandas as pd
import numpy as np

def generate_sample_data(output_path="data/sample_sales_data.csv", start_date="2023-01-01", end_date="2026-06-30"):
    """
    Generates a realistic daily sales dataset and saves it to output_path.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check if file already exists
    if os.path.exists(output_path):
        print(f"Sample data already exists at: {output_path}")
        return output_path
        
    print("Generating realistic sales dataset...")
    
    # Date range
    dates = pd.date_range(start=start_date, end=end_date)
    
    # Products catalog with categories and prices
    catalog = {
        "Electronics": {
            "Laptop Pro": 1299.99,
            "Smartphone X": 899.99,
            "Tablet Air": 599.99
        },
        "Accessories": {
            "Wireless Earbuds": 199.99,
            "Leather Case": 49.99,
            "USB-C Hub": 79.99
        },
        "Wearables": {
            "Smart Watch": 299.99,
            "Fitness Tracker": 99.99
        },
        "Home Appliances": {
            "Coffee Maker": 149.99,
            "Smart Bulb": 29.99
        },
        "Others": {
            "Office Chair": 249.99,
            "Water Bottle": 34.99
        }
    }
    
    regions = ["North", "East", "South", "West"]
    
    # Flatten the catalog for easier sampling
    product_list = []
    category_list = []
    price_list = []
    for cat, items in catalog.items():
        for prod, price in items.items():
            product_list.append(prod)
            category_list.append(cat)
            price_list.append(price)
            
    n_products = len(product_list)
    
    # To generate realistic sales, we'll sample daily transactions
    np.random.seed(42)
    
    records = []
    
    # Base multiplier for regions to introduce regional differences
    region_multipliers = {
        "East": 1.15,
        "West": 1.25, # West is highest growth / highest sales
        "North": 0.95,
        "South": 0.85
    }
    
    # Base multiplier for product categories to make some more popular (matching Electronics dominance)
    category_multipliers = {
        "Electronics": 1.6,
        "Accessories": 0.8,
        "Wearables": 0.6,
        "Home Appliances": 0.4,
        "Others": 0.3
    }
    
    for date in dates:
        # Determine number of transactions for this day
        # Weekend effect
        day_of_week = date.dayofweek
        is_weekend = day_of_week in [4, 5, 6] # Friday, Saturday, Sunday
        
        # Monthly seasonality (November/December spike, January slump)
        month = date.month
        month_multiplier = 1.0
        if month in [11, 12]:
            month_multiplier = 1.35  # Holiday shopping
        elif month == 1:
            month_multiplier = 0.8  # Post-holiday dip
        elif month in [8, 9]:
            month_multiplier = 1.1  # Back to school
            
        # Yearly growth trend (sales grow by ~12% each year)
        year_multiplier = 1.0 + (date.year - 2023) * 0.12
        
        # Adjust base transaction count to achieve ~$2.73M in 2023
        # Average price is higher, so let's generate around 25-45 transactions per day
        base_tx = np.random.randint(22, 38)
        if is_weekend:
            base_tx = int(base_tx * 1.25)
        
        n_tx = int(base_tx * month_multiplier * year_multiplier)
        
        # Randomly select products and regions for this day's transactions
        for _ in range(n_tx):
            prod_idx = np.random.choice(n_products)
            prod = product_list[prod_idx]
            cat = category_list[prod_idx]
            price = price_list[prod_idx]
            
            region = np.random.choice(regions)
            
            # Base quantity sold
            if cat in ["Accessories", "Others"]:
                base_qty = np.random.randint(1, 4)
            elif cat == "Electronics":
                # Electronics are expensive, so mostly 1, occasionally 2
                base_qty = np.random.choice([1, 2], p=[0.85, 0.15])
            else:
                base_qty = np.random.randint(1, 3)
                
            # Apply multipliers
            m_mult = region_multipliers[region] * category_multipliers[cat]
            qty = max(1, int(round(base_qty * m_mult * (1.15 if is_weekend else 1.0))))
            
            # Apply discounts
            discount_prob = 0.20
            if np.random.random() < discount_prob:
                discount = np.random.choice([0.05, 0.10, 0.15, 0.20])
            else:
                discount = 0.0
                
            revenue = qty * price * (1.0 - discount)
            
            records.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Product_Category": cat,
                "Product": prod,
                "Region": region,
                "Units_Sold": qty,
                "Price_Per_Unit": price,
                "Discount": discount,
                "Sales_Revenue": round(revenue, 2)
            })
            
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} transactions in {output_path}")
    return output_path

if __name__ == "__main__":
    generate_sample_data()
