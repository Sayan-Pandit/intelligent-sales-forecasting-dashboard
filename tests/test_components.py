import unittest
import os
import pandas as pd
import numpy as np

from src.sample_generator import generate_sample_data
from src.preprocessing import load_data, clean_data, engineer_features, aggregate_data
from src.forecasting import FallbackProphet, train_regression_model

class TestDashboardComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate a small sample dataset for testing (e.g. 3 months)
        cls.test_csv = "data/test_sales_data.csv"
        generate_sample_data(cls.test_csv, start_date="2024-01-01", end_date="2024-03-31")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_csv):
            os.remove(cls.test_csv)

    def test_01_data_generation(self):
        """Test if the sample dataset is generated and has correct columns"""
        self.assertTrue(os.path.exists(self.test_csv))
        df = pd.read_csv(self.test_csv)
        self.assertGreater(len(df), 0)
        expected_cols = ['Date', 'Product_Category', 'Product', 'Region', 'Units_Sold', 'Price_Per_Unit', 'Discount', 'Sales_Revenue']
        for col in expected_cols:
            self.assertIn(col, df.columns)

    def test_02_preprocessing(self):
        """Test data loading, cleaning, and feature engineering"""
        df = load_data(self.test_csv)
        df_cleaned = clean_data(df)
        df_engineered = engineer_features(df_cleaned)
        
        # Check added features
        self.assertIn('Year', df_engineered.columns)
        self.assertIn('Month', df_engineered.columns)
        self.assertIn('DayOfWeek', df_engineered.columns)
        self.assertIn('IsWeekend', df_engineered.columns)
        
        # Test aggregation
        df_agg = aggregate_data(df_engineered, frequency='W')
        self.assertGreater(len(df_agg), 0)
        self.assertIn('Sales_Revenue', df_agg.columns)

    def test_03_fallback_prophet(self):
        """Test if FallbackProphet runs and predicts correctly"""
        df = load_data(self.test_csv)
        df_cleaned = clean_data(df)
        df_monthly = aggregate_data(df_cleaned, frequency='W') # aggregate weekly for shorter test data
        
        df_prophet = df_monthly[['Date', 'Sales_Revenue']].rename(columns={'Date': 'ds', 'Sales_Revenue': 'y'})
        
        model = FallbackProphet()
        model.fit(df_prophet)
        
        # Predict on future
        future_dates = pd.date_range(start=df_prophet['ds'].max() + pd.offsets.Day(7), periods=4, freq='W')
        future = pd.DataFrame({'ds': pd.concat([df_prophet['ds'], pd.Series(future_dates)])})
        
        forecast = model.predict(future)
        self.assertIn('yhat', forecast.columns)
        self.assertIn('yhat_lower', forecast.columns)
        self.assertIn('yhat_upper', forecast.columns)
        self.assertEqual(len(forecast), len(future))

if __name__ == '__main__':
    unittest.main()
