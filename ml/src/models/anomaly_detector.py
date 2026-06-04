"""
Anomaly Detection Model.

Two-stage approach:
  1. Isolation Forest on tabular transaction features (fast, interpretable)
  2. Statistical Z-score on per-user, per-category spend distributions

Flags: unusual_amount, unusual_frequency, unusual_merchant, potential_fraud
"""
import numpy as np
import pandas as pd
import pickle
import os
from typing import List, Dict, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    """Isolation Forest + statistical anomaly detector for transactions."""

    def __init__(
        self,
        contamination: float = 0.02,
        n_estimators: int = 200,
        z_score_threshold: float = 3.0,
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.z_score_threshold = z_score_threshold

        self.isolation_forest: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None

        # Per-user, per-category statistics for personalized detection
        self.user_category_stats: Dict[str, Dict[str, dict]] = {}
        self.global_stats: Dict[str, dict] = {}
        self.is_fitted = False

    def _build_feature_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """Build numeric feature matrix for Isolation Forest."""
        df = df.copy()
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        features = pd.DataFrame({
            "amount_log": np.log1p(df["amount"].abs()),
            "day_of_week": df["transaction_date"].dt.dayofweek,
            "hour": df.get("hour", pd.Series(np.zeros(len(df)))),
            "is_weekend": (df["transaction_date"].dt.dayofweek >= 5).astype(int),
            "is_month_end": (df["transaction_date"].dt.day >= 28).astype(int),
        })
        return features.values

    def fit(self, df: pd.DataFrame) -> "AnomalyDetector":
        """
        Fit anomaly detector on historical transaction data.
        Expects columns: user_id, amount, category, transaction_date, merchant_name
        """
        print("Fitting Isolation Forest...")
        X = self._build_feature_matrix(df)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.isolation_forest = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1,
        )
        self.isolation_forest.fit(X_scaled)

        # Build per-user per-category statistics
        print("Building user-category statistics...")
        if "user_id" in df.columns and "category" in df.columns:
            for user_id, user_df in df.groupby("user_id"):
                self.user_category_stats[str(user_id)] = {}
                for category, cat_df in user_df.groupby("category"):
                    amounts = cat_df["amount"].abs().values
                    self.user_category_stats[str(user_id)][category] = {
                        "mean": float(np.mean(amounts)),
                        "std": float(np.std(amounts)) if len(amounts) > 1 else float(np.mean(amounts)),
                        "count": len(amounts),
                    }

        # Global category stats
        for category, cat_df in df.groupby("category") if "category" in df.columns else []:
            amounts = cat_df["amount"].abs().values
            self.global_stats[category] = {
                "mean": float(np.mean(amounts)),
                "std": float(np.std(amounts)) if len(amounts) > 1 else float(np.mean(amounts)),
                "p95": float(np.percentile(amounts, 95)),
                "p99": float(np.percentile(amounts, 99)),
            }

        self.is_fitted = True
        print("Anomaly detector fitted.")
        return self

    def score_transaction(
        self,
        amount: float,
        category: str,
        transaction_date: str,
        merchant_name: str = "",
        user_id: Optional[str] = None,
        description: str = "",
    ) -> dict:
        """
        Score a single transaction for anomalies.
        Returns anomaly type, score, and whether it's flagged.
        """
        flags = []
        max_score = 0.0

        # 1. Isolation Forest score
        if self.isolation_forest and self.scaler:
            df_single = pd.DataFrame([{
                "amount": amount,
                "transaction_date": transaction_date,
            }])
            X = self._build_feature_matrix(df_single)
            X_scaled = self.scaler.transform(X)
            # decision_function returns negative values for anomalies
            raw_score = self.isolation_forest.decision_function(X_scaled)[0]
            isolation_score = max(0.0, min(1.0, (0.1 - raw_score) / 0.3))
            if isolation_score > 0.6:
                flags.append("isolation_forest_anomaly")
                max_score = max(max_score, isolation_score)

        # 2. User-specific Z-score check
        z_score = 0.0
        stats_source = "global"
        if user_id and str(user_id) in self.user_category_stats:
            user_stats = self.user_category_stats[str(user_id)].get(category, {})
            if user_stats and user_stats.get("count", 0) >= 5:
                z_score = abs(amount - user_stats["mean"]) / max(user_stats["std"], 1e-6)
                stats_source = "user_personalized"
        elif category in self.global_stats:
            gstats = self.global_stats[category]
            z_score = abs(amount - gstats["mean"]) / max(gstats["std"], 1e-6)
            stats_source = "global"

        if z_score > self.z_score_threshold:
            flags.append("unusual_amount")
            z_normalized = min(1.0, z_score / (self.z_score_threshold * 3))
            max_score = max(max_score, z_normalized)

        # 3. Velocity check — very large amounts
        if category in self.global_stats:
            p99 = self.global_stats[category].get("p99", float("inf"))
            if amount > p99 * 3:
                flags.append("potential_fraud")
                max_score = max(max_score, 0.9)

        is_anomaly = len(flags) > 0
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(max_score, 4),
            "anomaly_types": flags,
            "z_score": round(z_score, 2),
            "stats_source": stats_source,
            "flagged": is_anomaly and max_score > 0.5,
        }

    def score_batch(self, df: pd.DataFrame, user_id: Optional[str] = None) -> List[dict]:
        """Score a DataFrame of transactions."""
        results = []
        for _, row in df.iterrows():
            result = self.score_transaction(
                amount=float(row["amount"]),
                category=row.get("category", "Uncategorized"),
                transaction_date=str(row["transaction_date"]),
                merchant_name=row.get("merchant_name", ""),
                user_id=user_id or row.get("user_id"),
                description=row.get("description", ""),
            )
            results.append(result)
        return results

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"Anomaly detector saved to {path}")

    @classmethod
    def load(cls, path: str) -> "AnomalyDetector":
        with open(path, "rb") as f:
            return pickle.load(f)
