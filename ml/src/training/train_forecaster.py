"""
Training script for the spending forecaster model.
Run: python -m ml.src.training.train_forecaster
"""
import os
import sys
import argparse
import pandas as pd
import mlflow
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ml.src.models.forecaster import SpendingForecaster

DATA_PATH = "ml/data/processed/transactions.csv"
MODEL_OUTPUT_PATH = "ml/models/forecaster.pkl"
EXPERIMENT_NAME = "finsight-forecaster"


def train(data_path: str = DATA_PATH, model_output: str = MODEL_OUTPUT_PATH):
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])

    # Keep only expense transactions (positive amount)
    df = df[df["amount"] > 0].copy()
    categories = list(df["category"].unique())
    print(f"Training forecaster on {len(df):,} transactions, {len(categories)} categories")

    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="prophet_hybrid_forecaster"):
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("n_categories", len(categories))
        mlflow.log_param("date_range_days", (df["transaction_date"].max() - df["transaction_date"].min()).days)

        model_params = {
            "seasonality_mode": "multiplicative",
            "changepoint_prior_scale": 0.05,
        }
        mlflow.log_params(model_params)

        print("Fitting SpendingForecaster...")
        model = SpendingForecaster(**model_params)
        model.fit(df, categories=["__total__"] + categories)

        # Quick validation: predict 30 days and check reasonableness
        forecast = model.predict(category="__total__", horizon_days=30)
        mlflow.log_metric("forecast_30d_total", forecast["predicted_total"])
        mlflow.log_metric("forecast_daily_avg", forecast["daily_average"])
        mlflow.log_metric("n_models_fitted", len(model.models))

        print(f"\n=== Forecast Validation ===")
        print(f"30-day predicted total: ${forecast['predicted_total']:,.2f}")
        print(f"Daily average:          ${forecast['daily_average']:,.2f}")
        print(f"Method:                 {forecast['method']}")
        print(f"Models fitted:          {len(model.models)}/{len(categories) + 1}")

        os.makedirs(os.path.dirname(model_output), exist_ok=True)
        model.save(model_output)
        mlflow.log_artifact(model_output)

        print(f"\nForecaster saved to: {model_output}")

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train spending forecaster")
    parser.add_argument("--data-path", type=str, default=DATA_PATH)
    parser.add_argument("--model-output", type=str, default=MODEL_OUTPUT_PATH)
    args = parser.parse_args()

    if not os.path.exists(args.data_path):
        print("Data not found. Run train_categorizer.py first to generate data.")
        sys.exit(1)

    train(args.data_path, args.model_output)
