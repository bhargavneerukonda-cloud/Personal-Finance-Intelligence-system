"""
Financial Health Score Model.

Composite 0–100 score based on 5 sub-dimensions:
  1. Savings Rate         (weight: 30%)
  2. Budget Adherence     (weight: 25%)
  3. Spending Stability   (weight: 20%)
  4. Emergency Fund       (weight: 15%)
  5. Debt-to-Income Ratio (weight: 10%)

Each sub-score is 0–100. Final score is weighted sum.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class HealthScoreInput:
    # Monthly income (0 if unknown)
    monthly_income: float = 0.0
    # Monthly total expenses
    monthly_expenses: float = 0.0
    # Liquid savings / cash balance
    liquid_savings: float = 0.0
    # Total monthly debt payments
    monthly_debt_payments: float = 0.0
    # Budget categories: dict of {category: (allocated, spent)}
    budget_performance: Optional[dict] = None
    # Last 6 months of monthly totals for stability
    monthly_spend_history: Optional[list] = None


@dataclass
class HealthScoreResult:
    overall_score: float
    savings_rate_score: float
    budget_adherence_score: float
    spending_stability_score: float
    emergency_fund_score: float
    debt_ratio_score: float
    grade: str
    summary: str
    recommendations: list


class FinancialHealthScorer:
    """
    Rule-based financial health scoring engine.
    Scores are grounded in widely-accepted personal finance benchmarks:
    - 50/30/20 rule (50% needs, 30% wants, 20% savings)
    - 3-6 month emergency fund
    - Debt-to-income ratio < 36%
    """

    WEIGHTS = {
        "savings_rate": 0.30,
        "budget_adherence": 0.25,
        "spending_stability": 0.20,
        "emergency_fund": 0.15,
        "debt_ratio": 0.10,
    }

    def compute(self, data: HealthScoreInput) -> HealthScoreResult:
        scores = {}

        # 1. Savings Rate Score
        scores["savings_rate"] = self._savings_rate_score(
            data.monthly_income, data.monthly_expenses
        )

        # 2. Budget Adherence Score
        scores["budget_adherence"] = self._budget_adherence_score(data.budget_performance)

        # 3. Spending Stability Score
        scores["spending_stability"] = self._spending_stability_score(data.monthly_spend_history)

        # 4. Emergency Fund Score
        scores["emergency_fund"] = self._emergency_fund_score(
            data.liquid_savings, data.monthly_expenses
        )

        # 5. Debt-to-Income Score
        scores["debt_ratio"] = self._debt_ratio_score(
            data.monthly_debt_payments, data.monthly_income
        )

        # Weighted overall
        overall = sum(scores[k] * self.WEIGHTS[k] for k in scores)
        overall = round(min(100.0, max(0.0, overall)), 1)

        grade = self._grade(overall)
        summary = self._summary(overall, scores)
        recommendations = self._recommendations(scores, data)

        return HealthScoreResult(
            overall_score=overall,
            savings_rate_score=round(scores["savings_rate"], 1),
            budget_adherence_score=round(scores["budget_adherence"], 1),
            spending_stability_score=round(scores["spending_stability"], 1),
            emergency_fund_score=round(scores["emergency_fund"], 1),
            debt_ratio_score=round(scores["debt_ratio"], 1),
            grade=grade,
            summary=summary,
            recommendations=recommendations,
        )

    def _savings_rate_score(self, income: float, expenses: float) -> float:
        if income <= 0:
            return 50.0  # Neutral when income unknown
        savings_rate = (income - expenses) / income
        # 20%+ savings = 100, 0% = 40, negative = 0
        if savings_rate >= 0.20:
            return min(100.0, 80.0 + (savings_rate - 0.20) * 100)
        elif savings_rate >= 0.10:
            return 60.0 + (savings_rate - 0.10) * 200
        elif savings_rate >= 0:
            return 40.0 + savings_rate * 200
        else:
            return max(0.0, 40.0 + savings_rate * 100)

    def _budget_adherence_score(self, budget_performance: Optional[dict]) -> float:
        if not budget_performance:
            return 50.0
        scores = []
        for category, (allocated, spent) in budget_performance.items():
            if allocated <= 0:
                continue
            utilization = spent / allocated
            if utilization <= 0.8:
                scores.append(100.0)
            elif utilization <= 1.0:
                scores.append(100.0 - (utilization - 0.8) * 250)
            else:
                scores.append(max(0.0, 50.0 - (utilization - 1.0) * 100))
        return float(np.mean(scores)) if scores else 50.0

    def _spending_stability_score(self, monthly_history: Optional[list]) -> float:
        if not monthly_history or len(monthly_history) < 3:
            return 50.0
        arr = np.array(monthly_history, dtype=float)
        mean = np.mean(arr)
        if mean <= 0:
            return 50.0
        cv = np.std(arr) / mean  # Coefficient of variation
        # CV < 0.1 = very stable = 100; CV > 0.5 = very unstable = 20
        if cv <= 0.10:
            return 100.0
        elif cv <= 0.30:
            return 100.0 - (cv - 0.10) * 400
        else:
            return max(20.0, 20.0 + (0.50 - cv) * 160)

    def _emergency_fund_score(self, liquid_savings: float, monthly_expenses: float) -> float:
        if monthly_expenses <= 0:
            return 50.0
        months_covered = liquid_savings / monthly_expenses
        # 6+ months = 100, 3 months = 70, 1 month = 40, 0 = 0
        if months_covered >= 6:
            return 100.0
        elif months_covered >= 3:
            return 70.0 + (months_covered - 3) * 10
        elif months_covered >= 1:
            return 40.0 + (months_covered - 1) * 15
        else:
            return max(0.0, months_covered * 40)

    def _debt_ratio_score(self, monthly_debt: float, monthly_income: float) -> float:
        if monthly_income <= 0:
            return 50.0
        dti = monthly_debt / monthly_income
        # DTI < 15% = 100, 15–36% = good, 36–50% = risky, >50% = danger
        if dti <= 0.15:
            return 100.0
        elif dti <= 0.36:
            return 100.0 - (dti - 0.15) / 0.21 * 30
        elif dti <= 0.50:
            return 70.0 - (dti - 0.36) / 0.14 * 40
        else:
            return max(0.0, 30.0 - (dti - 0.50) * 60)

    def _grade(self, score: float) -> str:
        if score >= 85:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 55:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"

    def _summary(self, overall: float, scores: dict) -> str:
        weakest = min(scores, key=scores.get)
        labels = {
            "savings_rate": "savings rate",
            "budget_adherence": "budget adherence",
            "spending_stability": "spending consistency",
            "emergency_fund": "emergency fund",
            "debt_ratio": "debt-to-income ratio",
        }
        if overall >= 80:
            return f"Excellent financial health! Focus on maintaining your {labels[weakest]}."
        elif overall >= 60:
            return f"Good financial health with room to improve your {labels[weakest]}."
        elif overall >= 40:
            return f"Fair financial health. Your {labels[weakest]} needs the most attention."
        else:
            return f"Your finances need attention. Start by improving your {labels[weakest]}."

    def _recommendations(self, scores: dict, data: HealthScoreInput) -> list:
        recs = []
        if scores["savings_rate"] < 60:
            recs.append("Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings.")
        if scores["emergency_fund"] < 70:
            months = round(data.liquid_savings / data.monthly_expenses, 1) if data.monthly_expenses > 0 else 0
            recs.append(f"Build your emergency fund from {months} to 3–6 months of expenses.")
        if scores["budget_adherence"] < 70:
            recs.append("Review your budget categories — you're exceeding limits in some areas.")
        if scores["spending_stability"] < 60:
            recs.append("Your spending varies significantly month-to-month. Try setting fixed weekly limits.")
        if scores["debt_ratio"] < 70:
            recs.append("Your debt payments are high. Consider paying down high-interest debt first.")
        if not recs:
            recs.append("Keep up the great work! Consider investing your surplus savings.")
        return recs
