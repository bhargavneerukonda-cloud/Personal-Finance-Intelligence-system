"""
Training script for the anomaly detection model.
Run: python -m ml.src.training.train_anomaly
"""
import os
import sys
import argparse
import pandas as pd
import mlflow
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ml.src.models.anomaly_detector import AnomalyDetector

DATA_PATH = "ml/data/processed/transactions.csv"
MODEL_OUTPUT_PATH = "ml/models/anomaly_detector.pkl"
EXPERIMENT_NAME = "finsight-anomaly"


def train(data_path: str = DATA_PATH, model_output: str = MODEL_OUTPUT_PATH):
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df):,} transactions")
    print(f"Anomaly rate: {df['is_anomaly'].mean():.2%}")

    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="isolation_forest_zscore"):
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("anomaly_rate", round(df["is_anomaly"].mean(), 4))

        model_params = {
            "contamination": 0.02,
            "n_estimators": 200,
            "z_score_threshold": 3.0,
        }
        mlflow.log_params(model_params)

        print("Fitting AnomalyDetector...")
        model = AnomalyDetector(**model_params)
        model.fit(df)

        # Evaluate using ground truth labels from synthetic data
        print("Evaluating on full dataset...")
        results = model.score_batch(df)

        y_true = df["is_anomaly"].astype(int).values
        y_pred = [1 if r["flagged"] else 0 for r in results]
        y_scores = [r["anomaly_score"] for r in results]

        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        try:
            auc = roc_auc_score(y_true, y_scores)
        except Exception:
            auc = 0.0

        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("auc_roc", auc)
        mlflow.log_metric("flagged_count", sum(y_pred))

        print(f"\n=== Anomaly Detection Metrics ===")
        print(f"Precision:  {precision:.4f}")
        print(f"Recall:     {recall:.4f}")
        print(f"F1 Score:   {f1:.4f}")
        print(f"AUC-ROC:    {auc:.4f}")
        print(f"Flagged:    {sum(y_pred):,} / {len(y_pred):,}")

        os.makedirs(os.path.dirname(model_output), exist_ok=True)
        model.save(model_output)
        mlflow.log_artifact(model_output)

        print(f"\nAnomaly detector saved to: {model_output}")

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, default=DATA_PATH)
    parser.add_argument("--model-output", type=str, default=MODEL_OUTPUT_PATH)
    args = parser.parse_args()

    if not os.path.exists(args.data_path):
        print("Data not found. Run generate_data.py first.")
        sys.exit(1)

    train(args.data_path, args.model_output)
