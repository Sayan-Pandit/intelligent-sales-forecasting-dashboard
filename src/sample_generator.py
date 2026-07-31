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
            "Laptop": 999.99,
            "Smartphone": 699.99,
            "Headphones": 149.99,
            "Smartwatch": 249.99
        },
        "Furniture": {
            "Office Chair": 199.99,
            "Desk": 299.99,
            "Dining Table": 499.99,
            "Sofa": 799.99
        },
        "Clothing": {
            "Jeans": 59.99,
            "T-shirt": 24.99,
            "Hoodie": 49.99,
            "Sneakers": 89.99
        },
        "Groceries": {
            "Coffee Beans": 14.99,
            "Organic Milk": 4.99,
            "Olive Oil": 19.99,
            "Chocolate": 5.99
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
    # We will generate between 50 and 150 transactions per day
    np.random.seed(42)
    
    records = []
    
    # Base multiplier for regions to introduce regional differences
    region_multipliers = {
        "East": 1.2,
        "West": 1.1,
        "North": 0.9,
        "South": 0.8
    }
    
    # Base multiplier for product categories to make some more popular
    category_multipliers = {
        "Electronics": 1.0,
        "Groceries": 1.5, # Groceries sold more frequently
        "Clothing": 1.2,
        "Furniture": 0.6  # Furniture sold less frequently
    }
    
    for date in dates:
        # Determine number of transactions for this day
        # Weekend effect: more transactions on Fri, Sat, Sun
        day_of_week = date.dayofweek
        is_weekend = day_of_week in [4, 5, 6] # Friday, Saturday, Sunday
        
        # Monthly seasonality (November/December spike, January slump)
        month = date.month
        month_multiplier = 1.0
        if month in [11, 12]:
            month_multiplier = 1.4  # Holiday shopping
        elif month == 1:
            month_multiplier = 0.8  # Post-holiday dip
        elif month in [8, 9]:
            month_multiplier = 1.1  # Back to school
            
        # Yearly growth trend (sales grow by ~10% each year)
        year_multiplier = 1.0 + (date.year - 2023) * 0.12
        
        # Calculate daily transaction count
        base_tx = np.random.randint(40, 90)
        if is_weekend:
            base_tx = int(base_tx * 1.3)
        
        n_tx = int(base_tx * month_multiplier * year_multiplier)
        
        # Randomly select products and regions for this day's transactions
        for _ in range(n_tx):
            prod_idx = np.random.choice(n_products)
            prod = product_list[prod_idx]
            cat = category_list[prod_idx]
            price = price_list[prod_idx]
            
            region = np.random.choice(regions)
            
            # Base quantity sold
            if cat == "Groceries":
                base_qty = np.random.randint(1, 6)
            elif cat == "Clothing":
                base_qty = np.random.randint(1, 4)
            elif cat == "Electronics":
                base_qty = np.random.randint(1, 3)
            else: # Furniture
                base_qty = 1
                
            # Apply multipliers
            m_mult = region_multipliers[region] * category_multipliers[cat]
            qty = max(1, int(round(base_qty * m_mult * (1.2 if is_weekend else 1.0))))
            
            # Apply discounts
            # High price items are more likely to have discounts
            discount_prob = 0.15 if cat in ["Groceries", "Clothing"] else 0.25
            if np.random.random() < discount_prob:
                discount = np.random.choice([0.05, 0.10, 0.15, 0.20, 0.25])
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
