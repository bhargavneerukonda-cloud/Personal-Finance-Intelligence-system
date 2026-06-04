"""
Training script for the expense categorization model.
Run: python -m ml.src.training.train_categorizer

Tracks experiments with MLflow.
"""
import os
import sys
import argparse
import pandas as pd
import mlflow
import mlflow.sklearn
from pathlib import Path
from sklearn.metrics import f1_score, accuracy_score, classification_report

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ml.src.models.categorizer import TransactionCategorizer

DATA_PATH = "ml/data/processed/transactions.csv"
MODEL_OUTPUT_PATH = "ml/models/categorizer.pkl"
EXPERIMENT_NAME = "finsight-categorizer"


def train(data_path: str = DATA_PATH, model_output: str = MODEL_OUTPUT_PATH):
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df):,} transactions, {df['category'].nunique()} categories")
    print(f"Category distribution:\n{df['category'].value_counts()}\n")

    # MLflow experiment tracking
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="xgboost_tfidf_ensemble"):
        mlflow.log_param("data_path", data_path)
        mlflow.log_param("n_samples", len(df))
        mlflow.log_param("n_categories", df["category"].nunique())

        model_params = {
            "n_estimators": 500,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 3,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "random_state": 42,
            "n_jobs": -1,
        }
        mlflow.log_params(model_params)

        print("Training TransactionCategorizer...")
        model = TransactionCategorizer(model_params=model_params)
        model.fit(df, target_col="category")
        model.version = mlflow.active_run().info.run_id[:8]

        # Evaluate on full dataset (train already split internally)
        categories, confidences = model.predict(df)
        acc = accuracy_score(df["category"], categories)
        f1_weighted = f1_score(df["category"], categories, average="weighted")
        f1_macro = f1_score(df["category"], categories, average="macro")

        mlflow.log_metric("train_accuracy", acc)
        mlflow.log_metric("train_f1_weighted", f1_weighted)
        mlflow.log_metric("train_f1_macro", f1_macro)
        mlflow.log_metric("avg_confidence", sum(confidences) / len(confidences))

        print(f"\n=== Training Metrics ===")
        print(f"Accuracy:    {acc:.4f}")
        print(f"F1 Weighted: {f1_weighted:.4f}")
        print(f"F1 Macro:    {f1_macro:.4f}")
        print(f"\n{classification_report(df['category'], categories)}")

        # Log feature importance
        importance_df = model.get_feature_importance(top_n=20)
        importance_df.to_csv("/tmp/feature_importance.csv", index=False)
        mlflow.log_artifact("/tmp/feature_importance.csv")

        # Save model
        os.makedirs(os.path.dirname(model_output), exist_ok=True)
        model.save(model_output)
        mlflow.log_artifact(model_output)

        run_id = mlflow.active_run().info.run_id
        print(f"\nModel saved to: {model_output}")
        print(f"MLflow run ID: {run_id}")

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train expense categorization model")
    parser.add_argument("--data-path", type=str, default=DATA_PATH)
    parser.add_argument("--model-output", type=str, default=MODEL_OUTPUT_PATH)
    args = parser.parse_args()

    # Generate synthetic data if not exists
    if not os.path.exists(args.data_path):
        print(f"Data not found at {args.data_path}. Generating synthetic data...")
        os.makedirs(os.path.dirname(args.data_path), exist_ok=True)
        os.system(f"python ml/data/generate_data.py --n-users 200 --transactions-per-user 500 --output {args.data_path}")

    train(args.data_path, args.model_output)
