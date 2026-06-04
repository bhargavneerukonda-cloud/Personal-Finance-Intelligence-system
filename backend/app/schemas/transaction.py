"""Pydantic schemas for transactions and accounts."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    amount: Decimal
    merchant_name: Optional[str] = None
    description: str
    transaction_date: date
    category_user_override: Optional[str] = None
    tags: Optional[str] = None


class TransactionUpdate(BaseModel):
    category_user_override: Optional[str] = None
    tags: Optional[str] = None
    merchant_name: Optional[str] = None


class MLPredictionResponse(BaseModel):
    category: str
    confidence: float
    shap_values: Optional[dict] = None
    model_version: str

    model_config = {"from_attributes": True}


class AnomalyFlagResponse(BaseModel):
    anomaly_type: str
    anomaly_score: float
    is_confirmed_fraud: bool
    is_dismissed: bool

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    amount: Decimal
    merchant_name: Optional[str]
    description: str
    transaction_date: date
    effective_category: str
    category_predicted: Optional[str]
    category_user_override: Optional[str]
    confidence_score: Optional[float]
    is_recurring: bool
    tags: Optional[str]
    ml_prediction: Optional[MLPredictionResponse]
    anomaly_flag: Optional[AnomalyFlagResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AccountCreate(BaseModel):
    institution_name: str
    account_name: str
    account_type: str
    currency: str = "USD"


class AccountResponse(BaseModel):
    id: uuid.UUID
    institution_name: str
    account_name: str
    account_type: str
    balance: Decimal
    currency: str
    is_active: bool
    synced_at: Optional[datetime]

    model_config = {"from_attributes": True}


class SpendingSummary(BaseModel):
    category: str
    total_amount: Decimal
    transaction_count: int
    percentage_of_total: float
    avg_transaction: Decimal


class InsightResponse(BaseModel):
    insight_type: str  # saving_opportunity, budget_alert, pattern, forecast
    title: str
    message: str
    severity: str  # info, warning, alert
    action_items: List[str]
    data: Optional[dict] = None
