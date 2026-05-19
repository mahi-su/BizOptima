"""
BizOptima - ML Model Training Script
Trains a Random Forest Regressor for profit prediction.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib

ML_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(ML_DIR, "saved_model.pkl")
SCALER_PATH = os.path.join(ML_DIR, "scaler.pkl")
METRICS_PATH = os.path.join(ML_DIR, "model_metrics.json")


def generate_synthetic_dataset(n_samples=5000):
    """Generate a realistic synthetic business dataset."""
    np.random.seed(42)

    revenue = np.random.lognormal(mean=12, sigma=1.5, size=n_samples)
    revenue = np.clip(revenue, 10_000, 5_000_000)

    expense_ratio = np.random.uniform(0.30, 0.80, n_samples)
    expenses = revenue * expense_ratio

    marketing_ratio = np.random.uniform(0.03, 0.20, n_samples)
    marketing_spend = revenue * marketing_ratio

    base_employees = np.log10(revenue) * 2
    employee_count = np.random.normal(base_employees, 2, n_samples).astype(int)
    employee_count = np.clip(employee_count, 1, 500)

    op_ratio = np.random.uniform(0.10, 0.40, n_samples)
    operational_cost = revenue * op_ratio

    marketing_effect = marketing_spend * np.random.uniform(0.5, 3.0, n_samples)
    noise = np.random.normal(0, revenue * 0.02, n_samples)
    profit = revenue - expenses - operational_cost + (marketing_effect * 0.1) + noise

    df = pd.DataFrame({
        "revenue": np.round(revenue, 2),
        "expenses": np.round(expenses, 2),
        "marketing_spend": np.round(marketing_spend, 2),
        "employee_count": employee_count,
        "operational_cost": np.round(operational_cost, 2),
        "profit": np.round(profit, 2),
    })

    df.head(500).to_csv(os.path.join(ML_DIR, "sample_dataset.csv"), index=False)
    print(f"Generated {n_samples} samples and saved 500 rows to sample_dataset.csv")
    return df


def train_model():
    """Train and save the Random Forest model, scaler, and metrics."""
    print("\n" + "=" * 55)
    print("  BizOptima - ML Model Training")
    print("=" * 55)

    print("\nGenerating synthetic business dataset...")
    df = generate_synthetic_dataset(5000)
    print(f"Dataset shape: {df.shape}")
    print(f"Profit range: ${df['profit'].min():,.0f} to ${df['profit'].max():,.0f}")

    feature_cols = ["revenue", "expenses", "marketing_spend", "employee_count", "operational_cost"]
    X = df[feature_cols]
    y = df["profit"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\nTrain size: {len(X_train)} | Test size: {len(X_test)}")

    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("\nTraining Random Forest Regressor...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mse)

    print("\nModel Performance Metrics:")
    print(f"R2 Score: {r2:.4f}")
    print(f"MAE:      ${mae:,.2f}")
    print(f"RMSE:     ${rmse:,.2f}")

    importances = dict(zip(feature_cols, model.feature_importances_.tolist()))
    print("\nFeature Importances:")
    for feat, imp in sorted(importances.items(), key=lambda item: item[1], reverse=True):
      bar = "#" * int(imp * 50)
      print(f"{feat:<20} {bar} {imp:.4f}")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\nModel saved to: {MODEL_PATH}")
    print(f"Scaler saved to: {SCALER_PATH}")

    metrics = {
        "r2_score": round(r2, 4),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mse": round(mse, 2),
        "feature_importances": importances,
        "model_type": "RandomForestRegressor",
        "n_estimators": 200,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to: {METRICS_PATH}")
    print("\nModel training complete.")
    print("=" * 55)
    return model, scaler, metrics


def load_model():
    """Load trained model and scaler. Train them if missing."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        print("Model not found. Training new model...")
        train_model()
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler


def predict_profit(revenue, expenses, marketing_spend, employee_count, operational_cost):
    """Make a profit prediction using the trained model."""
    model, scaler = load_model()
    features = pd.DataFrame([{
        "revenue": revenue,
        "expenses": expenses,
        "marketing_spend": marketing_spend,
        "employee_count": employee_count,
        "operational_cost": operational_cost,
    }])
    features_scaled = scaler.transform(features)
    prediction = model.predict(features_scaled)[0]
    return float(prediction)


def get_model_metrics():
    """Load saved model metrics."""
    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


if __name__ == "__main__":
    train_model()
