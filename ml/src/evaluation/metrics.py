"""
Model evaluation metrics and reporting utilities.
Used during training, CI validation, and production monitoring.
"""
import numpy as np
import pandas as pd
from typing import List, Optional
from sklearn.metrics import (
    f1_score, accuracy_score, precision_score, recall_score,
    classification_report, confusion_matrix, roc_auc_score,
    mean_absolute_percentage_error, mean_squared_error,
)


# ── Classification Metrics (Categorizer, Anomaly) ────────────────────────────

def classification_metrics(y_true: List, y_pred: List, labels: Optional[List] = None) -> dict:
    """Compute full suite of classification metrics."""
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "f1_weighted": round(f1_score(y_true, y_pred, average="weighted", zero_division=0), 4),
        "f1_macro": round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4),
        "precision_weighted": round(precision_score(y_true, y_pred, average="weighted", zero_division=0), 4),
        "recall_weighted": round(recall_score(y_true, y_pred, average="weighted", zero_division=0), 4),
        "report": classification_report(y_true, y_pred, labels=labels, zero_division=0),
    }


def confusion_matrix_df(y_true: List, y_pred: List, labels: List[str]) -> pd.DataFrame:
    """Return confusion matrix as a labeled DataFrame."""
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return pd.DataFrame(cm, index=labels, columns=labels)


def binary_anomaly_metrics(y_true: List[int], y_pred: List[int], y_scores: List[float]) -> dict:
    """
    Metrics for binary anomaly detection.
    y_true: 0=normal, 1=anomaly
    y_scores: continuous anomaly scores (higher = more anomalous)
    """
    metrics = {
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "flagged_count": int(sum(y_pred)),
        "true_positives": int(sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)),
        "false_positives": int(sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)),
        "false_negatives": int(sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)),
    }
    try:
        metrics["auc_roc"] = round(roc_auc_score(y_true, y_scores), 4)
    except ValueError:
        metrics["auc_roc"] = None
    return metrics


# ── Regression Metrics (Forecaster) ──────────────────────────────────────────

def forecasting_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Metrics for time-series spending forecasts.
    Target: MAPE < 10%, RMSE within acceptable range.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    # Mask zeros to avoid division by zero in MAPE
    mask = y_true != 0
    mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100) if mask.any() else 0.0
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(np.mean(np.abs(y_true - y_pred)))
    bias = float(np.mean(y_pred - y_true))  # positive = over-predicting

    return {
        "mape": round(mape, 2),
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "bias": round(bias, 2),
        "r2": round(1 - np.var(y_true - y_pred) / (np.var(y_true) + 1e-10), 4),
    }


# ── Model Comparison ──────────────────────────────────────────────────────────

def is_better_model(
    new_metrics: dict,
    current_metrics: dict,
    primary_metric: str = "f1_weighted",
    min_improvement: float = 0.01,
) -> bool:
    """
    Determine if new model should replace current production model.
    Requires min_improvement % improvement on primary metric.
    """
    new_val = new_metrics.get(primary_metric, 0)
    cur_val = current_metrics.get(primary_metric, 0)
    improvement = new_val - cur_val
    result = improvement >= min_improvement
    print(f"Model comparison on {primary_metric}: {cur_val:.4f} → {new_val:.4f} "
          f"({'PROMOTE' if result else 'REJECT'}, improvement={improvement:.4f})")
    return result


def print_metrics_table(metrics: dict, title: str = "Model Metrics"):
    """Pretty-print a metrics dict."""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    for k, v in metrics.items():
        if k != "report":
            print(f"  {k:35s}: {v}")
    if "report" in metrics:
        print(f"\n{metrics['report']}")
    print("="*50)
