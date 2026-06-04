"""Transaction CRUD and ML-prediction endpoints."""
import uuid
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date
from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.transaction import Transaction, Account
from app.schemas.transaction import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    TransactionListResponse, SpendingSummary
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


async def _user_account_ids(user: User, db: AsyncSession) -> list:
    result = await db.execute(
        select(Account.id).where(Account.user_id == user.id, Account.is_active == True)
    )
    return [r[0] for r in result.fetchall()]


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    account_ids = await _user_account_ids(current_user, db)
    if not account_ids:
        return TransactionListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)

    filters = [Transaction.account_id.in_(account_ids)]
    if category:
        filters.append(
            (Transaction.category_user_override == category) |
            (Transaction.category_predicted == category)
        )
    if start_date:
        filters.append(Transaction.transaction_date >= start_date)
    if end_date:
        filters.append(Transaction.transaction_date <= end_date)
    if account_id:
        filters.append(Transaction.account_id == account_id)
    if search:
        filters.append(
            Transaction.merchant_name.ilike(f"%{search}%") |
            Transaction.description.ilike(f"%{search}%")
        )

    count_result = await db.execute(
        select(func.count(Transaction.id)).where(and_(*filters))
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Transaction)
        .where(and_(*filters))
        .order_by(Transaction.transaction_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    transactions = result.scalars().all()

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify account belongs to user
    result = await db.execute(
        select(Account).where(Account.id == payload.account_id, Account.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    transaction = Transaction(**payload.model_dump())
    db.add(transaction)
    await db.flush()

    # Trigger async ML categorization
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.ML_SERVICE_URL}/predict/category",
                json={"transaction_id": str(transaction.id),
                      "amount": float(transaction.amount),
                      "description": transaction.description,
                      "merchant_name": transaction.merchant_name}
            )
    except Exception:
        pass  # Non-blocking — categorization can happen async

    await db.refresh(transaction)
    return TransactionResponse.model_validate(transaction)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    account_ids = await _user_account_ids(current_user, db)
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.account_id.in_(account_ids)
        )
    )
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(transaction, field, value)

    await db.flush()
    await db.refresh(transaction)
    return TransactionResponse.model_validate(transaction)


@router.get("/summary/by-category")
async def spending_by_category(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    account_ids = await _user_account_ids(current_user, db)
    filters = [Transaction.account_id.in_(account_ids), Transaction.amount > 0]
    if start_date:
        filters.append(Transaction.transaction_date >= start_date)
    if end_date:
        filters.append(Transaction.transaction_date <= end_date)

    result = await db.execute(
        select(
            func.coalesce(Transaction.category_user_override, Transaction.category_predicted, "Uncategorized").label("category"),
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count"),
            func.avg(Transaction.amount).label("avg"),
        )
        .where(and_(*filters))
        .group_by("category")
        .order_by(func.sum(Transaction.amount).desc())
    )
    rows = result.fetchall()
    grand_total = sum(r.total for r in rows) or 1

    return [
        SpendingSummary(
            category=r.category,
            total_amount=r.total,
            transaction_count=r.count,
            percentage_of_total=round(float(r.total / grand_total) * 100, 2),
            avg_transaction=r.avg,
        )
        for r in rows
    ]
