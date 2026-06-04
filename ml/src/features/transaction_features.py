"""
Feature engineering pipeline for transaction data.
Produces tabular + text features for ML models.
"""
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer


AMOUNT_BINS = [0, 5, 20, 50, 100, 250, 500, 1000, float("inf")]
AMOUNT_BIN_LABELS = ["micro", "tiny", "small", "medium", "large", "xlarge", "xxlarge", "extreme"]

CATEGORY_LIST = [
    "Food & Dining", "Shopping", "Transportation", "Entertainment",
    "Healthcare", "Utilities", "Housing", "Groceries", "Uncategorized",
]


def engineer_features(df: pd.DataFrame, fit: bool = True, artifacts: Optional[dict] = None) -> Tuple[pd.DataFrame, dict]:
    """
    Full feature engineering pipeline.

    Args:
        df: Raw transaction DataFrame
        fit: If True, fit encoders/scalers (training). If False, use provided artifacts.
        artifacts: Dict of fitted encoders/scalers (for inference)

    Returns:
        (feature_df, artifacts)
    """
    artifacts = artifacts or {}
    df = df.copy()

    # --- Date features ---
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["day_of_week"] = df["transaction_date"].dt.dayofweek
    df["day_of_month"] = df["transaction_date"].dt.day
    df["month"] = df["transaction_date"].dt.month
    df["quarter"] = df["transaction_date"].dt.quarter
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_month_start"] = (df["day_of_month"] <= 3).astype(int)
    df["is_month_end"] = (df["day_of_month"] >= 28).astype(int)

    # --- Amount features ---
    df["amount_abs"] = df["amount"].abs()
    df["amount_log"] = np.log1p(df["amount_abs"])
    df["amount_bin"] = pd.cut(df["amount_abs"], bins=AMOUNT_BINS, labels=AMOUNT_BIN_LABELS)

    # --- Text features: merchant name ---
    df["merchant_clean"] = (
        df["merchant_name"]
        .fillna("")
        .str.lower()
        .str.replace(r"[^a-z0-9 ]", " ", regex=True)
        .str.replace(r"\b(inc|llc|ltd|corp|co)\b", "", regex=True)
        .str.strip()
    )
    df["description_clean"] = (
        df["description"]
        .fillna("")
        .str.lower()
        .str.replace(r"[^a-z0-9 ]", " ", regex=True)
        .str.strip()
    )
    df["text_combined"] = df["merchant_clean"] + " " + df["description_clean"]

    # TF-IDF on combined text
    if fit:
        tfidf = TfidfVectorizer(max_features=200, ngram_range=(1, 2), min_df=2)
        tfidf_matrix = tfidf.fit_transform(df["text_combined"])
        artifacts["tfidf"] = tfidf
    else:
        tfidf = artifacts["tfidf"]
        tfidf_matrix = tfidf.transform(df["text_combined"])

    tfidf_df = pd.DataFrame(
        tfidf_matrix.toarray(),
        columns=[f"tfidf_{i}" for i in range(tfidf_matrix.shape[1])],
        index=df.index,
    )

    # --- Amount bin encoding ---
    if fit:
        bin_encoder = LabelEncoder()
        df["amount_bin_enc"] = bin_encoder.fit_transform(df["amount_bin"].astype(str))
        artifacts["bin_encoder"] = bin_encoder
    else:
        df["amount_bin_enc"] = artifacts["bin_encoder"].transform(df["amount_bin"].astype(str))

    # --- Numerical feature scaling ---
    num_cols = ["amount_abs", "amount_log", "day_of_week", "day_of_month", "month", "quarter"]
    if fit:
        scaler = StandardScaler()
        df[num_cols] = scaler.fit_transform(df[num_cols])
        artifacts["scaler"] = scaler
    else:
        df[num_cols] = artifacts["scaler"].transform(df[num_cols])

    # --- Assemble feature matrix ---
    base_cols = num_cols + [
        "amount_bin_enc", "is_weekend", "is_month_start", "is_month_end",
    ]
    feature_df = pd.concat([df[base_cols].reset_index(drop=True), tfidf_df.reset_index(drop=True)], axis=1)

    return feature_df, artifacts


def compute_user_aggregates(df: pd.DataFrame, user_id_col: str = "user_id") -> pd.DataFrame:
    """
    Compute user-level aggregate features for personalization.
    """
    user_stats = df.groupby(user_id_col).agg(
        avg_tx_amount=("amount", "mean"),
        std_tx_amount=("amount", "std"),
        total_transactions=("amount", "count"),
        total_spend=("amount", "sum"),
        max_single_tx=("amount", "max"),
    ).reset_index()
    user_stats["std_tx_amount"] = user_stats["std_tx_amount"].fillna(0)
    return user_stats


def add_rolling_features(df: pd.DataFrame, user_id_col: str = "user_id") -> pd.DataFrame:
    """
    Add rolling 7-day and 30-day spend features per user.
    Requires transaction_date column.
    """
    df = df.sort_values([user_id_col, "transaction_date"]).copy()
    df.set_index("transaction_date", inplace=True)

    def rolling_sum(group, window):
        return group["amount"].rolling(window, min_periods=1).sum()

    df["rolling_7d_spend"] = (
        df.groupby(user_id_col, group_keys=False)
        .apply(lambda g: rolling_sum(g, "7D"))
    )
    df["rolling_30d_spend"] = (
        df.groupby(user_id_col, group_keys=False)
        .apply(lambda g: rolling_sum(g, "30D"))
    )
    df.reset_index(inplace=True)
    return df
