import unittest
import os
import pandas as pd
import numpy as np

from src.sample_generator import generate_sample_data
from src.preprocessing import load_data, clean_data, engineer_features, aggregate_data, suggest_mappings, map_and_clean_data
from src.forecasting import FallbackProphet, train_regression_model

class TestDashboardComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate a small sample dataset for testing (e.g. 6 months)
        cls.test_csv = "data/test_sales_data.csv"
        generate_sample_data(cls.test_csv, start_date="2024-01-01", end_date="2024-06-30")

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

    def test_04_dynamic_mapping(self):
        """Test if suggest_mappings correctly identifies columns in a renamed dataset"""
        df = pd.read_csv(self.test_csv)
        # Rename columns to simulate an arbitrary user dataset
        df_renamed = df.rename(columns={
            'Date': 'transaction_time',
            'Sales_Revenue': 'net_revenue_usd'
        })
        
        date_col, sales_col = suggest_mappings(df_renamed)
        self.assertEqual(date_col, 'transaction_time')
        self.assertEqual(sales_col, 'net_revenue_usd')
        
        df_cleaned = map_and_clean_data(df_renamed, date_col, sales_col)
        self.assertIn('Date', df_cleaned.columns)
        self.assertIn('Sales_Revenue', df_cleaned.columns)

    def test_05_mlp_forecasting(self):
        """Test if the MLP Neural Network trains and generates recursive forecasts"""
        df = load_data(self.test_csv)
        df_cleaned = clean_data(df)
        df_weekly = aggregate_data(df_cleaned, frequency='W')
        
        # We need enough historical data points, so let's expand df_weekly if needed
        # In setupClass we generate 3 months, which gives ~13 weeks. 
        # train_regression_model requires len(clean) >= 6.
        # Let's verify it trains and outputs forecasts.
        forecast_df, metrics, name = train_regression_model(df_weekly, horizon_months=4, model_type='mlp')
        
        self.assertEqual(name, "MLP Neural Network")
        self.assertIn('MAE', metrics)
        self.assertIn('RMSE', metrics)
        self.assertIn('R2', metrics)
        
        self.assertIn('yhat', forecast_df.columns)
        self.assertIn('yhat_lower', forecast_df.columns)
        self.assertIn('yhat_upper', forecast_df.columns)
        
        # Total forecast length should be historical length + future horizon (4 weeks)
        self.assertEqual(len(forecast_df), len(df_weekly) + 4)

    def test_06_xgboost_forecasting(self):
        """Test if the XGBoost Regressor trains and generates recursive forecasts"""
        df = load_data(self.test_csv)
        df_cleaned = clean_data(df)
        df_weekly = aggregate_data(df_cleaned, frequency='W')
        
        forecast_df, metrics, name = train_regression_model(df_weekly, horizon_months=4, model_type='xgb')
        
        self.assertEqual(name, "XGBoost Regressor")
        self.assertIn('MAE', metrics)
        self.assertIn('RMSE', metrics)
        self.assertIn('R2', metrics)
        
        self.assertIn('yhat', forecast_df.columns)
        self.assertIn('yhat_lower', forecast_df.columns)
        self.assertIn('yhat_upper', forecast_df.columns)
        
        self.assertEqual(len(forecast_df), len(df_weekly) + 4)

    def test_07_gemini_insights_fallback(self):
        """Test that generate_gemini_insights_helper returns None when no API key is set."""
        import os
        from src.gemini_insights import generate_gemini_insights_helper
        import pandas as pd

        # Remove key if present to ensure clean state
        original_key = os.environ.pop("GEMINI_API_KEY", None)

        try:
            df = pd.DataFrame({
                'Sales_Revenue': [100000.0, 200000.0],
                'Region': ['East', 'West'],
                'Product_Category': ['Electronics', 'Clothing'],
                'Units_Sold': [150, 200],
                'Total_Profit': [20000.0, 40000.0]
            })

            # Without API key, must return None (triggering rule-based fallback)
            result = generate_gemini_insights_helper(df)
            self.assertIsNone(result, "Expected None when GEMINI_API_KEY is not set")
        finally:
            # Restore original key if it was set
            if original_key:
                os.environ["GEMINI_API_KEY"] = original_key

    def test_08_report_generation(self):
        """Test report generation fallback produces valid HTML containing expected segments."""
        from src.reports_generator import generate_report_content
        import pandas as pd

        df = pd.DataFrame({
            'Sales_Revenue': [500000.0, 300000.0],
            'Region': ['East', 'West'],
            'Product_Category': ['Electronics', 'Furniture'],
            'Product': ['Laptop Pro', 'Ergo Chair'],
            'Units_Sold': [100, 150],
            'Total_Profit': [100000.0, 60000.0]
        })

        # Test executive summary generation
        html = generate_report_content(df, report_type="executive")
        self.assertIsInstance(html, str)
        self.assertIn("Executive Summary", html)
        self.assertIn("Regional Distribution Analysis", html)
        self.assertIn("Product Performance &amp; Breakdown", html)
        self.assertIn("Strategic Recommendations", html)

if __name__ == '__main__':
    unittest.main()
