"""SQLAlchemy Budget and FinancialHealthScore models."""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Date, Numeric, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), default="monthly")  # weekly, monthly, yearly
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    total_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="budgets")
    categories = relationship("BudgetCategory", back_populates="budget", cascade="all, delete-orphan")


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("budgets.id"), nullable=False)
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    alert_threshold_pct: Mapped[float] = mapped_column(Float, default=0.8)  # alert at 80%

    budget = relationship("Budget", back_populates="categories")

    @property
    def remaining(self) -> Decimal:
        return self.allocated_amount - self.spent_amount

    @property
    def utilization_pct(self) -> float:
        if self.allocated_amount == 0:
            return 0.0
        return float(self.spent_amount / self.allocated_amount)


class FinancialHealthScore(Base):
    __tablename__ = "financial_health_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    savings_rate_score: Mapped[float] = mapped_column(Float, nullable=False)
    budget_adherence_score: Mapped[float] = mapped_column(Float, nullable=False)
    spending_stability_score: Mapped[float] = mapped_column(Float, nullable=False)
    emergency_fund_score: Mapped[float] = mapped_column(Float, default=50.0)
    debt_ratio_score: Mapped[float] = mapped_column(Float, default=50.0)
    score_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_scores")
