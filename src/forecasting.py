import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from xgboost import XGBRegressor

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:
    PROPHET_AVAILABLE = False

class FallbackProphet:
    """
    A robust, zero-dependency fallback for Prophet that uses a Linear Regression model
    with a linear trend and monthly dummy variables. Fits quickly and provides 
    yhat, yhat_lower, and yhat_upper.
    """
    def __init__(self):
        from sklearn.linear_model import LinearRegression
        self.model = LinearRegression()
        self.std_dev = 0.0
        
    def fit(self, df):
        # df has columns 'ds' and 'y'
        df = df.copy()
        df['ds'] = pd.to_datetime(df['ds'])
        
        # Features: time index (trend) and month dummies
        df['time_idx'] = (df['ds'] - df['ds'].min()).dt.days
        df['month'] = df['ds'].dt.month
        
        # Monthly dummy variables (11 columns to avoid dummy variable trap)
        month_dummies = pd.get_dummies(df['month'], prefix='month', drop_first=True)
        # Ensure all months from 2 to 12 are represented
        for m in range(2, 13):
            col = f'month_{m}'
            if col not in month_dummies.columns:
                month_dummies[col] = 0
                
        # Align columns alphabetically
        month_dummies = month_dummies[[f'month_{m}' for m in range(2, 13)]]
        
        X = pd.concat([df[['time_idx']], month_dummies], axis=1).astype(float)
        y = df['y']
        
        self.model.fit(X, y)
        
        # Calculate residuals std dev for prediction intervals
        preds = self.model.predict(X)
        residuals = y - preds
        self.std_dev = np.std(residuals) if len(residuals) > 1 else 1.0
        self.min_ds = df['ds'].min()
        return self
        
    def predict(self, future_df):
        future_df = future_df.copy()
        future_df['ds'] = pd.to_datetime(future_df['ds'])
        
        future_df['time_idx'] = (future_df['ds'] - self.min_ds).dt.days
        future_df['month'] = future_df['ds'].dt.month
        
        month_dummies = pd.get_dummies(future_df['month'], prefix='month', drop_first=True)
        for m in range(2, 13):
            col = f'month_{m}'
            if col not in month_dummies.columns:
                month_dummies[col] = 0
                
        month_dummies = month_dummies[[f'month_{m}' for m in range(2, 13)]]
        
        X = pd.concat([future_df[['time_idx']], month_dummies], axis=1).astype(float)
        
        preds = self.model.predict(X)
        
        future_df['yhat'] = preds
        # 95% Confidence Interval
        future_df['yhat_lower'] = preds - 1.96 * self.std_dev
        future_df['yhat_upper'] = preds + 1.96 * self.std_dev
        
        return future_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def train_prophet_model(df_agg, horizon_months=6):
    """
    Fits a Prophet model (or FallbackProphet if prophet is not installed) 
    and predicts 'horizon_months' into the future.
    Input df_agg must have columns: 'Date' and 'Sales_Revenue'
    """
    # Prepare data for Prophet: requires 'ds' (date) and 'y' (target)
    df_prophet = df_agg[['Date', 'Sales_Revenue']].rename(columns={'Date': 'ds', 'Sales_Revenue': 'y'})
    df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])
    
    if PROPHET_AVAILABLE:
        try:
            m = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                interval_width=0.95
            )
            m.fit(df_prophet)
            
            # Create future dates (monthly frequency 'ME')
            future = m.make_future_dataframe(periods=horizon_months, freq='ME')
            forecast = m.predict(future)
            
            return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']], "Prophet"
        except Exception as e:
            print(f"Prophet execution failed: {e}. Falling back to Regression-based forecasting.")
            
    # Fallback path
    m = FallbackProphet()
    m.fit(df_prophet)
    
    # Create future dates
    last_date = df_prophet['ds'].max()
    future_dates = pd.date_range(start=last_date + pd.offsets.MonthBegin(1), periods=horizon_months, freq='ME')
    future = pd.DataFrame({'ds': pd.concat([df_prophet['ds'], pd.Series(future_dates)])})
    
    forecast = m.predict(future)
    return forecast, "Regression-Trend Seasonal (Prophet Fallback)"

def build_regression_features(df_agg, lags=[1, 2, 3, 12]):
    """
    Helper to build lag and rolling window features for regression models.
    df_agg must have 'Date' and 'Sales_Revenue' columns, sorted by Date.
    """
    df = df_agg.copy().sort_values('Date').reset_index(drop=True)
    df['Month'] = df['Date'].dt.month
    df['Year'] = df['Date'].dt.year
    
    # Create lag features
    for lag in lags:
        df[f'Sales_Lag_{lag}'] = df['Sales_Revenue'].shift(lag)
        
    # Create rolling features (e.g. 3-month mean)
    df['Sales_Rolling_Mean_3'] = df['Sales_Revenue'].shift(1).rolling(window=3).mean()
    df['Sales_Rolling_Std_3'] = df['Sales_Revenue'].shift(1).rolling(window=3).std()
    
    return df

def train_regression_model(df_agg, horizon_months=6, model_type='rf'):
    """
    Trains a Random Forest or XGBoost model on aggregated sales data.
    Performs recursive forecasting to predict future values.
    Returns:
      - forecast_df: columns [ds, yhat, yhat_lower, yhat_upper]
      - metrics: dict containing MAE, RMSE, R2
      - model_name: str
    """
    df_feats = build_regression_features(df_agg)
    
    # Drop rows with NaNs from lags (we lose up to 12 rows)
    df_clean = df_feats.dropna().copy()
    
    if len(df_clean) < 6:
        raise ValueError("Not enough historical data to train regression models. Please aggregate daily or use Prophet.")
        
    # Features & Target
    feature_cols = [col for col in df_clean.columns if 'Lag' in col or 'Rolling' in col] + ['Month', 'Year']
    X = df_clean[feature_cols]
    y = df_clean['Sales_Revenue']
    
    # Train-test split (hold out last 6 months for evaluation if we have enough data)
    test_size = min(6, int(len(df_clean) * 0.2))
    if test_size < 1:
        test_size = 1
        
    X_train, X_test = X.iloc[:-test_size], X.iloc[-test_size:]
    y_train, y_test = y.iloc[:-test_size], y.iloc[-test_size:]
    
    # Model selection
    if model_type == 'rf':
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model_name = "Random Forest Regressor"
    elif model_type == 'mlp':
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        model = Pipeline([
            ('scaler', StandardScaler()),
            ('mlp', MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42, early_stopping=True))
        ])
        model_name = "MLP Neural Network"
    else:
        model = XGBRegressor(n_estimators=100, learning_rate=0.05, random_state=42)
        model_name = "XGBoost Regressor"

        
    model.fit(X_train, y_train)
    
    # Evaluate model
    test_preds = model.predict(X_test)
    metrics = {
        'MAE': mean_absolute_error(y_test, test_preds),
        'RMSE': np.sqrt(mean_squared_error(y_test, test_preds)),
        'R2': r2_score(y_test, test_preds)
    }
    
    # Retrain on full dataset before future forecasting
    model.fit(X, y)
    
    # Residual standard deviation for prediction interval estimation
    train_preds = model.predict(X)
    residuals = y - train_preds
    residual_std = np.std(residuals) if len(residuals) > 1 else 1.0
    
    # Recursive Forecasting for Future Horizon
    # Start with the full historical dataframe
    history = df_agg.copy().sort_values('Date').reset_index(drop=True)
    last_date = history['Date'].max()
    
    future_records = []
    
    for i in range(horizon_months):
        next_date = last_date + pd.offsets.MonthEnd(1) * (i + 1)
        
        # Build features for this future step
        # Create a temp df with the new date
        temp_row = pd.DataFrame({'Date': [next_date], 'Sales_Revenue': [np.nan]})
        temp_history = pd.concat([history, temp_row], ignore_index=True)
        
        # Build lag features on the temp_history
        temp_feats = build_regression_features(temp_history)
        
        # Extract features for the very last row (the target future step)
        row_feats = temp_feats.iloc[-1][feature_cols].to_frame().T
        
        # Predict sales revenue for this month
        pred_val = float(model.predict(row_feats)[0])
        pred_val = max(0.0, pred_val) # Sales cannot be negative
        
        # Store in historical log so it is used in subsequent lag feature calculations
        history = pd.concat([history, pd.DataFrame({'Date': [next_date], 'Sales_Revenue': [pred_val]})], ignore_index=True)
        
        # Prediction bands
        yhat_lower = max(0.0, pred_val - 1.96 * residual_std)
        yhat_upper = pred_val + 1.96 * residual_std
        
        future_records.append({
            'ds': next_date,
            'yhat': pred_val,
            'yhat_lower': yhat_lower,
            'yhat_upper': yhat_upper
        })
        
    forecast_df = pd.DataFrame(future_records)
    
    # Append historical actuals (for visual consistency, we return history as well)
    historical_forecast = pd.DataFrame({
        'ds': df_agg['Date'],
        'yhat': df_agg['Sales_Revenue'],
        'yhat_lower': df_agg['Sales_Revenue'],
        'yhat_upper': df_agg['Sales_Revenue']
    })
    
    full_forecast = pd.concat([historical_forecast, forecast_df], ignore_index=True)
    
    return full_forecast, metrics, model_name
