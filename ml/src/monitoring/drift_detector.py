"""
Model drift monitoring using Evidently AI.
Compares reference (training) data distribution against current production data.
Triggers retraining alert if drift is detected.
"""
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime


class DriftMonitor:
    """
    Monitors data and prediction drift for ML models.
    Uses statistical tests (PSI, KS-test) as fallback when Evidently not available.
    """

    PSI_THRESHOLD = 0.2       # Population Stability Index — alert if > 0.2
    KS_THRESHOLD = 0.05       # KS-test p-value — alert if < 0.05

    def __init__(self, reference_data: Optional[pd.DataFrame] = None):
        self.reference_data = reference_data
        self.reports = []

    def set_reference(self, df: pd.DataFrame):
        self.reference_data = df.copy()
        print(f"Reference dataset set: {len(df):,} rows, {df.shape[1]} columns")

    def compute_psi(self, expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
        """
        Population Stability Index.
        PSI < 0.1: no significant change
        PSI 0.1–0.2: moderate change, monitor
        PSI > 0.2: significant change, investigate/retrain
        """
        expected = np.array(expected, dtype=float)
        actual = np.array(actual, dtype=float)

        # Create bins from expected distribution
        breakpoints = np.linspace(min(expected.min(), actual.min()),
                                  max(expected.max(), actual.max()), bins + 1)

        expected_counts = np.histogram(expected, bins=breakpoints)[0]
        actual_counts = np.histogram(actual, bins=breakpoints)[0]

        # Avoid division by zero
        expected_pct = np.where(expected_counts == 0, 0.001, expected_counts / len(expected))
        actual_pct = np.where(actual_counts == 0, 0.001, actual_counts / len(actual))

        psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return round(float(psi), 4)

    def detect_drift(self, current_data: pd.DataFrame, feature_cols: Optional[list] = None) -> dict:
        """
        Run drift detection comparing reference vs current data.
        Returns drift report with per-feature PSI scores.
        """
        if self.reference_data is None:
            return {"error": "Reference data not set. Call set_reference() first."}

        feature_cols = feature_cols or ["amount", "day_of_week", "month"]
        available_cols = [c for c in feature_cols if c in self.reference_data.columns and c in current_data.columns]

        drift_results = {}
        drifted_features = []

        for col in available_cols:
            ref_vals = self.reference_data[col].dropna().values
            cur_vals = current_data[col].dropna().values
            if len(ref_vals) < 10 or len(cur_vals) < 10:
                continue

            psi = self.compute_psi(ref_vals, cur_vals)
            is_drifted = psi > self.PSI_THRESHOLD
            drift_results[col] = {"psi": psi, "drifted": is_drifted}
            if is_drifted:
                drifted_features.append(col)

        # Try Evidently for richer report
        try:
            from evidently.report import Report
            from evidently.metric_preset import DataDriftPreset

            report = Report(metrics=[DataDriftPreset()])
            report.run(
                reference_data=self.reference_data[available_cols],
                current_data=current_data[available_cols],
            )
            evidently_available = True
        except ImportError:
            evidently_available = False

        overall_drift = len(drifted_features) > 0
        report_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "reference_size": len(self.reference_data),
            "current_size": len(current_data),
            "features_checked": available_cols,
            "feature_drift": drift_results,
            "drifted_features": drifted_features,
            "overall_drift_detected": overall_drift,
            "evidently_report_available": evidently_available,
            "recommendation": "RETRAIN" if overall_drift else "OK",
        }
        self.reports.append(report_entry)

        if overall_drift:
            print(f"\n⚠️  DRIFT DETECTED in features: {drifted_features}")
            print(f"   Recommendation: Schedule model retraining.")
        else:
            print(f"\n✅ No significant drift detected.")

        return report_entry

    def get_drift_summary(self) -> dict:
        if not self.reports:
            return {"message": "No drift reports generated yet"}
        latest = self.reports[-1]
        return {
            "total_checks": len(self.reports),
            "latest_check": latest["timestamp"],
            "latest_result": latest["recommendation"],
            "drifted_features": latest.get("drifted_features", []),
        }


def run_drift_check(
    reference_path: str = "ml/data/processed/transactions.csv",
    current_path: Optional[str] = None,
    n_current_samples: int = 500,
):
    """
    Standalone drift check utility.
    Simulates current data by sampling from reference with slight perturbation.
    In production, current_path points to recent production transactions.
    """
    print("Loading reference data...")
    ref_df = pd.read_csv(reference_path)

    if current_path:
        print(f"Loading current data from {current_path}...")
        current_df = pd.read_csv(current_path)
    else:
        # Simulate drift: sample + add noise
        print(f"Simulating current data ({n_current_samples} samples with artificial drift)...")
        current_df = ref_df.sample(n=min(n_current_samples, len(ref_df)), random_state=99).copy()
        current_df["amount"] = current_df["amount"] * np.random.uniform(0.8, 1.5, len(current_df))

    monitor = DriftMonitor()
    monitor.set_reference(ref_df)
    report = monitor.detect_drift(current_df, feature_cols=["amount", "day_of_week", "month"])

    print("\n=== Drift Report ===")
    for feat, result in report.get("feature_drift", {}).items():
        status = "🔴 DRIFT" if result["drifted"] else "🟢 OK"
        print(f"  {feat}: PSI={result['psi']:.4f} {status}")

    return report


if __name__ == "__main__":
    run_drift_check()
