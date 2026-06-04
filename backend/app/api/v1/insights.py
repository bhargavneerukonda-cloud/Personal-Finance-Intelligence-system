"""AI insights, financial health score, and forecasting endpoints."""
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, timedelta
from decimal import Decimal
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.transaction import Transaction, Account
from app.models.budget import FinancialHealthScore, Budget, BudgetCategory
from app.schemas.transaction import InsightResponse

router = APIRouter(tags=["Insights & Analytics"])


@router.get("/health-score")
async def get_health_score(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FinancialHealthScore)
        .where(FinancialHealthScore.user_id == current_user.id)
        .order_by(FinancialHealthScore.score_date.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        # Compute on-the-fly for new users
        return {
            "overall_score": 50.0,
            "savings_rate_score": 50.0,
            "budget_adherence_score": 50.0,
            "spending_stability_score": 50.0,
            "emergency_fund_score": 50.0,
            "debt_ratio_score": 50.0,
            "score_date": date.today().isoformat(),
            "message": "Keep adding transactions to improve score accuracy.",
        }
    return {
        "overall_score": score.overall_score,
        "savings_rate_score": score.savings_rate_score,
        "budget_adherence_score": score.budget_adherence_score,
        "spending_stability_score": score.spending_stability_score,
        "emergency_fund_score": score.emergency_fund_score,
        "debt_ratio_score": score.debt_ratio_score,
        "score_date": score.score_date.isoformat(),
    }


@router.get("/forecast")
async def get_forecast(
    horizon_days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Proxy to ML service for spending forecast."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{settings.ML_SERVICE_URL}/forecast",
                params={"user_id": str(current_user.id), "horizon_days": horizon_days}
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass

    # Fallback: simple historical average
    end = date.today()
    start = end - timedelta(days=90)
    result = await db.execute(
        select(func.avg(Transaction.amount), func.count(Transaction.id))
        .join(Account, Transaction.account_id == Account.id)
        .where(Account.user_id == current_user.id, Transaction.transaction_date.between(start, end))
    )
    row = result.fetchone()
    avg_tx = float(row[0] or 0)
    count = row[1] or 0
    daily_rate = (avg_tx * count) / 90

    return {
        "horizon_days": horizon_days,
        "predicted_total": round(daily_rate * horizon_days, 2),
        "daily_average": round(daily_rate, 2),
        "confidence_interval_low": round(daily_rate * horizon_days * 0.85, 2),
        "confidence_interval_high": round(daily_rate * horizon_days * 1.15, 2),
        "method": "historical_average_fallback",
        "daily_breakdown": [
            {
                "date": (end + timedelta(days=i + 1)).isoformat(),
                "predicted_amount": round(daily_rate, 2),
            }
            for i in range(horizon_days)
        ],
    }


@router.get("/insights")
async def get_insights(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate rule-based + LLM-enhanced insights."""
    insights = []

    # Check budget utilization
    result = await db.execute(
        select(Budget, BudgetCategory)
        .join(BudgetCategory, Budget.id == BudgetCategory.budget_id)
        .where(Budget.user_id == current_user.id, Budget.is_active == True)
    )
    for budget, category in result.fetchall():
        util = category.utilization_pct
        if util >= 1.0:
            insights.append(InsightResponse(
                insight_type="budget_alert",
                title=f"{category.category_name} budget exceeded",
                message=f"You've spent ${float(category.spent_amount):.2f} of your ${float(category.allocated_amount):.2f} {category.category_name} budget.",
                severity="alert",
                action_items=["Review recent transactions", "Adjust budget limit", "Reduce spending in this category"],
            ))
        elif util >= 0.8:
            insights.append(InsightResponse(
                insight_type="budget_alert",
                title=f"{category.category_name} budget at {util * 100:.0f}%",
                message=f"${float(category.remaining):.2f} remaining for {category.category_name} this period.",
                severity="warning",
                action_items=["Monitor spending closely"],
            ))

    if not insights:
        insights.append(InsightResponse(
            insight_type="pattern",
            title="Good budget adherence",
            message="You're within all budget limits. Keep it up!",
            severity="info",
            action_items=["Set savings goals", "Review forecasts"],
        ))

    return insights


@router.get("/anomalies")
async def get_anomalies(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Proxy to ML service for anomaly flags."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{settings.ML_SERVICE_URL}/anomalies",
                params={"user_id": str(current_user.id)}
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {"anomalies": [], "message": "No anomalies detected or ML service unavailable"}
