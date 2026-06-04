"""Budget CRUD and progress tracking endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.budget import Budget, BudgetCategory

router = APIRouter(prefix="/budgets", tags=["Budgets"])


class BudgetCategoryCreate(BaseModel):
    category_name: str
    allocated_amount: Decimal
    alert_threshold_pct: float = 0.8


class BudgetCreate(BaseModel):
    name: str
    period_type: str = "monthly"
    period_start: date
    period_end: date
    total_limit: Decimal
    categories: List[BudgetCategoryCreate] = []


@router.get("")
async def list_budgets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget).where(Budget.user_id == current_user.id, Budget.is_active == True)
        .order_by(Budget.period_start.desc())
    )
    budgets = result.scalars().all()

    response = []
    for budget in budgets:
        cat_result = await db.execute(
            select(BudgetCategory).where(BudgetCategory.budget_id == budget.id)
        )
        categories = cat_result.scalars().all()
        response.append({
            "id": str(budget.id),
            "name": budget.name,
            "period_type": budget.period_type,
            "period_start": budget.period_start.isoformat(),
            "period_end": budget.period_end.isoformat(),
            "total_limit": float(budget.total_limit),
            "total_spent": sum(float(c.spent_amount) for c in categories),
            "utilization_pct": sum(float(c.spent_amount) for c in categories) / float(budget.total_limit) if budget.total_limit else 0,
            "categories": [
                {
                    "id": str(c.id),
                    "category_name": c.category_name,
                    "allocated_amount": float(c.allocated_amount),
                    "spent_amount": float(c.spent_amount),
                    "remaining": float(c.remaining),
                    "utilization_pct": c.utilization_pct,
                    "alert_threshold_pct": c.alert_threshold_pct,
                    "status": "over" if c.utilization_pct >= 1.0 else ("warning" if c.utilization_pct >= c.alert_threshold_pct else "ok"),
                }
                for c in categories
            ],
        })
    return response


@router.post("", status_code=201)
async def create_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    budget = Budget(
        user_id=current_user.id,
        name=payload.name,
        period_type=payload.period_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
        total_limit=payload.total_limit,
    )
    db.add(budget)
    await db.flush()

    for cat in payload.categories:
        db.add(BudgetCategory(
            budget_id=budget.id,
            category_name=cat.category_name,
            allocated_amount=cat.allocated_amount,
            alert_threshold_pct=cat.alert_threshold_pct,
        ))

    await db.flush()
    return {"id": str(budget.id), "message": "Budget created successfully"}


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    budget.is_active = False
    await db.flush()
