import os
import sys
sys.path.append(os.getcwd())
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor

from src.preprocessing import load_data, map_and_clean_data, engineer_features, aggregate_data, suggest_mappings
from src.forecasting import build_regression_features, FallbackProphet

def evaluate_on_dataset(file_path):
    print(f"\nEvaluating models on: {file_path}")
    
    # 1. Load and process
    df_raw = load_data(file_path)
    d_col, s_col = suggest_mappings(df_raw)
    df_mapped = map_and_clean_data(df_raw, d_col, s_col)
    df_engineered = engineer_features(df_mapped)
    df_monthly = aggregate_data(df_engineered, frequency='ME')
    
    if len(df_monthly) < 15:
        print(f"Warning: Dataset has only {len(df_monthly)} months, which is small.")
        
    # 2. Build features for baseline models (Linear Regression)
    df_feats = build_regression_features(df_monthly)
    df_clean = df_feats.dropna().copy()
    
    feature_cols_lr = [col for col in df_clean.columns if 'Lag' in col or 'Rolling' in col] + ['Month', 'Year']
    X_lr = df_clean[feature_cols_lr]
    y_lr = df_clean['Sales_Revenue']
    
    test_size_lr = min(6, int(len(df_clean) * 0.2))
    if test_size_lr < 1:
        test_size_lr = 1
        
    X_train_lr, X_test_lr = X_lr.iloc[:-test_size_lr], X_lr.iloc[-test_size_lr:]
    y_train_lr, y_test_lr = y_lr.iloc[:-test_size_lr], y_lr.iloc[-test_size_lr:]
    
    # Detrending setup for ML models (RF, XGB, MLP)
    min_date = df_monthly['Date'].min()
    df_monthly_copy = df_monthly.copy().sort_values('Date').reset_index(drop=True)
    df_monthly_copy['Time_Idx'] = (df_monthly_copy['Date'] - min_date).dt.days
    
    test_size_trend = min(6, int(len(df_monthly_copy) * 0.2))
    if test_size_trend < 1:
        test_size_trend = 1
    df_train_raw = df_monthly_copy.iloc[:-test_size_trend]
    
    trend_model = LinearRegression()
    trend_model.fit(df_train_raw[['Time_Idx']].values, df_train_raw['Sales_Revenue'].values)
    
    df_monthly_detrended = df_monthly_copy.copy()
    df_monthly_detrended['Sales_Revenue'] = df_monthly_copy['Sales_Revenue'] - trend_model.predict(df_monthly_copy[['Time_Idx']].values)
    
    # Build regression features on detrended series
    df_feats_det = build_regression_features(df_monthly_detrended)
    df_clean_det = df_feats_det.dropna().copy()
    
    feature_cols_det = [col for col in df_clean_det.columns if 'Lag' in col or 'Rolling' in col] + ['Month']
    X_det = df_clean_det[feature_cols_det]
    y_det = df_clean_det['Sales_Revenue']
    
    test_size_ml = min(6, int(len(df_clean_det) * 0.2))
    if test_size_ml < 1:
        test_size_ml = 1
        
    X_train_det, X_test_det = X_det.iloc[:-test_size_ml], X_det.iloc[-test_size_ml:]
    y_train_det, y_test_det = y_det.iloc[:-test_size_ml], y_det.iloc[-test_size_ml:]
    
    # Define models
    lr_model = LinearRegression()
    
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42
    )
    
    xgb_model = XGBRegressor(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=4,
        reg_alpha=0.1,
        reg_lambda=1.0,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    
    use_early_stopping = len(X_train_det) >= 20
    mlp_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('mlp', MLPRegressor(
            hidden_layer_sizes=(32, 16),
            max_iter=3000,
            random_state=42,
            early_stopping=use_early_stopping,
            n_iter_no_change=10,
            learning_rate_init=0.01
        ))
    ])
    mlp_model = TransformedTargetRegressor(
        regressor=mlp_pipeline,
        transformer=StandardScaler()
    )
    
    results = []
    
    # 1. Evaluate Linear Regression
    lr_model.fit(X_train_lr, y_train_lr)
    train_preds_lr = lr_model.predict(X_train_lr)
    test_preds_lr = lr_model.predict(X_test_lr)
    
    train_r2_lr = r2_score(y_train_lr, train_preds_lr)
    test_r2_lr = r2_score(y_test_lr, test_preds_lr)
    train_mae_lr = mean_absolute_error(y_train_lr, train_preds_lr)
    test_mae_lr = mean_absolute_error(y_test_lr, test_preds_lr)
    
    results.append({
        "Model": "Linear Regression",
        "Train R2": round(train_r2_lr, 4),
        "Test R2": round(test_r2_lr, 4),
        "Train MAE": round(train_mae_lr, 2),
        "Test MAE": round(test_mae_lr, 2),
        "Overfit Gap (Train - Test R2)": round(train_r2_lr - test_r2_lr, 4)
    })
    
    # Helper to evaluate detrended models
    y_train_actual = df_monthly_copy.iloc[df_clean_det.index[:-test_size_ml]]['Sales_Revenue'].values
    y_test_actual = df_monthly_copy.iloc[df_clean_det.index[-test_size_ml:]]['Sales_Revenue'].values
    train_time_idx = df_monthly_copy.iloc[df_clean_det.index[:-test_size_ml]][['Time_Idx']].values
    test_time_idx = df_monthly_copy.iloc[df_clean_det.index[-test_size_ml:]][['Time_Idx']].values
    
    def evaluate_detrended_model(name, model):
        model.fit(X_train_det, y_train_det)
        
        # Predict on train
        tr_preds_det = model.predict(X_train_det)
        tr_preds = tr_preds_det + trend_model.predict(train_time_idx)
        
        # Predict on test
        ts_preds_det = model.predict(X_test_det)
        ts_preds = ts_preds_det + trend_model.predict(test_time_idx)
        
        train_r2 = r2_score(y_train_actual, tr_preds)
        test_r2 = r2_score(y_test_actual, ts_preds)
        train_mae = mean_absolute_error(y_train_actual, tr_preds)
        test_mae = mean_absolute_error(y_test_actual, ts_preds)
        
        results.append({
            "Model": name,
            "Train R2": round(train_r2, 4),
            "Test R2": round(test_r2, 4),
            "Train MAE": round(train_mae, 2),
            "Test MAE": round(test_mae, 2),
            "Overfit Gap (Train - Test R2)": round(train_r2 - test_r2, 4)
        })
        
    evaluate_detrended_model("Random Forest (Detrended & Regularized)", rf_model)
    evaluate_detrended_model("XGBoost (Detrended & Regularized)", xgb_model)
    evaluate_detrended_model("MLP Neural Network (Detrended & Regularized)", mlp_model)
    
    # 2. Evaluate FallbackProphet separately
    try:
        df_prophet = df_monthly[['Date', 'Sales_Revenue']].rename(columns={'Date': 'ds', 'Sales_Revenue': 'y'})
        df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])
        
        # Split prophet train/test
        p_train = df_prophet.iloc[:-test_size_trend]
        p_test = df_prophet.iloc[-test_size_trend:]
        
        prophet_model = FallbackProphet()
        prophet_model.fit(p_train)
        
        # Predict on train and test
        train_pred_df = prophet_model.predict(p_train)
        test_pred_df = prophet_model.predict(p_test)
        
        train_r2 = r2_score(p_train['y'], train_pred_df['yhat'])
        test_r2 = r2_score(p_test['y'], test_pred_df['yhat'])
        train_mae = mean_absolute_error(p_train['y'], train_pred_df['yhat'])
        test_mae = mean_absolute_error(p_test['y'], test_pred_df['yhat'])
        
        results.append({
            "Model": "Prophet (Linear Trend Fallback)",
            "Train R2": round(train_r2, 4),
            "Test R2": round(test_r2, 4),
            "Train MAE": round(train_mae, 2),
            "Test MAE": round(test_mae, 2),
            "Overfit Gap (Train - Test R2)": round(train_r2 - test_r2, 4)
        })
    except Exception as e:
        print(f"Prophet evaluation failed: {e}")
        
    return pd.DataFrame(results)

if __name__ == "__main__":
    datasets = {
        "Clean Seasonality (High Signal)": "data/seasonal_clean_test.csv",
        "Overfitting/Noise Test (High Noise)": "data/overfitting_noise_test.csv",
        "Structural Break (Trend Change)": "data/structural_break_test.csv"
    }
    
    for label, path in datasets.items():
        print(f"\n==================================================")
        print(f" DATASET: {label}")
        print(f"==================================================")
        df_res = evaluate_on_dataset(path)
        print(df_res.to_string(index=False))
