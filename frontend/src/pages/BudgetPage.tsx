// BudgetPage.tsx
import { useQuery } from "@tanstack/react-query";
import { Target, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";
import { budgetsApi } from "@/services/api";
import { Budget } from "@/types";
import { formatCurrency, formatPercent } from "@/utils/helpers";

export function BudgetPage() {
  const { data: budgets, isLoading } = useQuery<Budget[]>({
    queryKey: ["budgets"],
    queryFn: () => budgetsApi.list().then((r) => r.data),
  });

  if (isLoading) return <div className="animate-pulse space-y-4">{Array.from({length:3}).map((_,i)=><div key={i} className="card h-32 bg-gray-100"/>)}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Budget Planner</h1>
          <p className="text-gray-500 mt-1">Track your spending against budget limits</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Target className="w-4 h-4" /> New Budget
        </button>
      </div>

      {!budgets || budgets.length === 0 ? (
        <div className="card text-center py-16">
          <Target className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-gray-600 font-medium">No budgets yet</h3>
          <p className="text-gray-400 text-sm mt-1">Create your first budget to start tracking spending</p>
        </div>
      ) : (
        budgets.map((budget) => (
          <div key={budget.id} className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-gray-900">{budget.name}</h3>
                <p className="text-sm text-gray-500">{budget.period_start} → {budget.period_end}</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">{formatCurrency(budget.total_spent)}</div>
                <div className="text-xs text-gray-400">of {formatCurrency(budget.total_limit)}</div>
              </div>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 mb-6">
              <div
                className={`h-2 rounded-full transition-all ${budget.utilization_pct >= 1 ? "bg-danger-500" : budget.utilization_pct >= 0.8 ? "bg-warning-500" : "bg-success-500"}`}
                style={{ width: `${Math.min(100, budget.utilization_pct * 100)}%` }}
              />
            </div>
            <div className="space-y-3">
              {budget.categories.map((cat) => (
                <div key={cat.id} className="flex items-center gap-3">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-700">{cat.category_name}</span>
                      <div className="flex items-center gap-2">
                        {cat.status === "over" && <AlertTriangle className="w-3.5 h-3.5 text-danger-500" />}
                        {cat.status === "ok" && <CheckCircle className="w-3.5 h-3.5 text-success-500" />}
                        <span className="text-xs text-gray-500">{formatCurrency(cat.spent_amount)} / {formatCurrency(cat.allocated_amount)}</span>
                      </div>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${cat.status === "over" ? "bg-danger-500" : cat.status === "warning" ? "bg-warning-500" : "bg-primary-400"}`}
                        style={{ width: `${Math.min(100, cat.utilization_pct * 100)}%` }}
                      />
                    </div>
                  </div>
                  <span className={`text-xs font-medium w-12 text-right ${cat.status === "over" ? "text-danger-600" : "text-gray-500"}`}>
                    {formatPercent(cat.utilization_pct * 100, 0)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default BudgetPage;
