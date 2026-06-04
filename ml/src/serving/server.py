"""
ML Model Serving Server.
Runs as a separate FastAPI service on port 8001.
Loads trained models and exposes inference endpoints.
"""
import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from contextlib import asynccontextmanager

# Model paths
MODEL_DIR = Path("models")
CATEGORIZER_PATH = MODEL_DIR / "categorizer.pkl"
FORECASTER_PATH = MODEL_DIR / "forecaster.pkl"
ANOMALY_PATH = MODEL_DIR / "anomaly_detector.pkl"

# Global model registry
models = {}


def load_models():
    """Load all trained models into memory."""
    try:
        from ml.src.models.categorizer import TransactionCategorizer
        if CATEGORIZER_PATH.exists():
            models["categorizer"] = TransactionCategorizer.load(str(CATEGORIZER_PATH))
            print(f"✓ Categorizer loaded from {CATEGORIZER_PATH}")
        else:
            print(f"⚠ Categorizer model not found at {CATEGORIZER_PATH}. Run train_categorizer.py first.")
    except Exception as e:
        print(f"⚠ Failed to load categorizer: {e}")

    try:
        from ml.src.models.forecaster import SpendingForecaster
        if FORECASTER_PATH.exists():
            models["forecaster"] = SpendingForecaster.load(str(FORECASTER_PATH))
            print(f"✓ Forecaster loaded from {FORECASTER_PATH}")
        else:
            print(f"⚠ Forecaster not found at {FORECASTER_PATH}. Run train_forecaster.py first.")
    except Exception as e:
        print(f"⚠ Failed to load forecaster: {e}")

    try:
        from ml.src.models.anomaly_detector import AnomalyDetector
        if ANOMALY_PATH.exists():
            models["anomaly"] = AnomalyDetector.load(str(ANOMALY_PATH))
            print(f"✓ Anomaly detector loaded from {ANOMALY_PATH}")
        else:
            print(f"⚠ Anomaly detector not found at {ANOMALY_PATH}. Run train_anomaly.py first.")
    except Exception as e:
        print(f"⚠ Failed to load anomaly detector: {e}")

    from ml.src.models.health_scorer import FinancialHealthScorer
    models["health_scorer"] = FinancialHealthScorer()
    print("✓ Health scorer initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_models()
    yield


app = FastAPI(
    title="FinSight ML Service",
    version="1.0.0",
    description="ML inference endpoints for FinSight AI",
    lifespan=lifespan,
)


# ── Request / Response schemas ──────────────────────────────────────────────

class CategoryRequest(BaseModel):
    transaction_id: Optional[str] = None
    amount: float
    description: str
    merchant_name: Optional[str] = ""
    transaction_date: Optional[str] = "2024-01-01"


class CategoryResponse(BaseModel):
    transaction_id: Optional[str]
    category: str
    confidence: float
    model_version: str


class ForecastRequest(BaseModel):
    user_id: str
    category: Optional[str] = "__total__"
    horizon_days: int = 30


class AnomalyRequest(BaseModel):
    transaction_id: Optional[str] = None
    amount: float
    category: str
    transaction_date: str
    merchant_name: Optional[str] = ""
    user_id: Optional[str] = None
    description: Optional[str] = ""


class HealthScoreRequest(BaseModel):
    monthly_income: float = 0.0
    monthly_expenses: float = 0.0
    liquid_savings: float = 0.0
    monthly_debt_payments: float = 0.0
    budget_performance: Optional[dict] = None
    monthly_spend_history: Optional[list] = None


class BatchCategoryRequest(BaseModel):
    transactions: list


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "models_loaded": list(models.keys()),
    }


@app.post("/predict/category", response_model=CategoryResponse)
async def predict_category(req: CategoryRequest):
    if "categorizer" not in models:
        raise HTTPException(status_code=503, detail="Categorizer model not loaded. Run training first.")
    categorizer = models["categorizer"]
    result = categorizer.predict_single(
        amount=req.amount,
        description=req.description,
        merchant_name=req.merchant_name or "",
        transaction_date=req.transaction_date or "2024-01-01",
    )
    return CategoryResponse(
        transaction_id=req.transaction_id,
        category=result["category"],
        confidence=result["confidence"],
        model_version=result.get("model_version", "v1"),
    )


@app.post("/predict/category/batch")
async def predict_category_batch(req: BatchCategoryRequest):
    if "categorizer" not in models:
        raise HTTPException(status_code=503, detail="Categorizer model not loaded.")
    df = pd.DataFrame(req.transactions)
    required = ["amount", "description"]
    for col in required:
        if col not in df.columns:
            raise HTTPException(status_code=422, detail=f"Missing required column: {col}")
    if "merchant_name" not in df.columns:
        df["merchant_name"] = ""
    if "transaction_date" not in df.columns:
        df["transaction_date"] = "2024-01-01"

    categories, confidences = models["categorizer"].predict(df)
    return {
        "predictions": [
            {"category": c, "confidence": round(conf, 4)}
            for c, conf in zip(categories, confidences)
        ]
    }


@app.get("/forecast")
async def get_forecast(user_id: str, category: str = "__total__", horizon_days: int = 30):
    if "forecaster" not in models:
        raise HTTPException(status_code=503, detail="Forecaster model not loaded.")
    forecaster = models["forecaster"]
    result = forecaster.predict(category=category, horizon_days=horizon_days)
    result["user_id"] = user_id
    return result


@app.post("/predict/anomaly")
async def predict_anomaly(req: AnomalyRequest):
    if "anomaly" not in models:
        raise HTTPException(status_code=503, detail="Anomaly detector not loaded.")
    result = models["anomaly"].score_transaction(
        amount=req.amount,
        category=req.category,
        transaction_date=req.transaction_date,
        merchant_name=req.merchant_name or "",
        user_id=req.user_id,
        description=req.description or "",
    )
    result["transaction_id"] = req.transaction_id
    return result


@app.post("/health-score")
async def compute_health_score(req: HealthScoreRequest):
    scorer = models.get("health_scorer")
    if not scorer:
        raise HTTPException(status_code=503, detail="Health scorer not available.")
    from ml.src.models.health_scorer import HealthScoreInput
    data = HealthScoreInput(
        monthly_income=req.monthly_income,
        monthly_expenses=req.monthly_expenses,
        liquid_savings=req.liquid_savings,
        monthly_debt_payments=req.monthly_debt_payments,
        budget_performance=req.budget_performance,
        monthly_spend_history=req.monthly_spend_history,
    )
    result = scorer.compute(data)
    return {
        "overall_score": result.overall_score,
        "grade": result.grade,
        "summary": result.summary,
        "recommendations": result.recommendations,
        "sub_scores": {
            "savings_rate": result.savings_rate_score,
            "budget_adherence": result.budget_adherence_score,
            "spending_stability": result.spending_stability_score,
            "emergency_fund": result.emergency_fund_score,
            "debt_ratio": result.debt_ratio_score,
        },
    }


@app.get("/anomalies")
async def get_user_anomalies(user_id: str):
    """Return recent anomaly flags for a user (placeholder — integrates with DB in production)."""
    return {"user_id": user_id, "anomalies": [], "message": "Connect to DB for live anomaly history"}
