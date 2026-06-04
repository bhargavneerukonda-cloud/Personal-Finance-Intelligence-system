import { useQuery } from "@tanstack/react-query";
import {
  AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { TrendingUp, TrendingDown, Shield, Target, AlertTriangle, Wallet } from "lucide-react";
import { transactionsApi, insightsApi } from "@/services/api";
import { formatCurrency, formatPercent, getCategoryColor, getHealthScoreStyle, formatDateShort } from "@/utils/helpers";
import { SpendingSummary, Forecast } from "@/types";

function StatCard({
  title, value, subtitle, icon: Icon, trend, color = "primary",
}: {
  title: string; value: string; subtitle?: string;
  icon: React.ElementType; trend?: number; color?: string;
}) {
  const colorMap: Record<string, string> = {
    primary: "bg-primary-50 text-primary-600",
    success: "bg-success-50 text-success-600",
    warning: "bg-warning-50 text-warning-600",
    danger: "bg-danger-50 text-danger-600",
  };
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-gray-400">{subtitle}</p>}
        </div>
        <div className={`p-2.5 rounded-lg ${colorMap[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {trend !== undefined && (
        <div className="mt-3 flex items-center gap-1">
          {trend >= 0
            ? <TrendingUp className="w-3 h-3 text-danger-500" />
            : <TrendingDown className="w-3 h-3 text-success-500" />}
          <span className={`text-xs font-medium ${trend >= 0 ? "text-danger-500" : "text-success-500"}`}>
            {Math.abs(trend).toFixed(1)}% vs last month
          </span>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  const { data: categoryData } = useQuery<SpendingSummary[]>({
    queryKey: ["spending-by-category"],
    queryFn: () => transactionsApi.summaryByCategory().then((r) => r.data),
  });

  const { data: healthScore } = useQuery({
    queryKey: ["health-score"],
    queryFn: () => insightsApi.getHealthScore().then((r) => r.data),
  });

  const { data: forecast } = useQuery<Forecast>({
    queryKey: ["forecast-30d"],
    queryFn: () => insightsApi.getForecast(30).then((r) => r.data),
  });

  const { data: insights } = useQuery({
    queryKey: ["insights"],
    queryFn: () => insightsApi.getInsights().then((r) => r.data),
  });

  const totalSpend = categoryData?.reduce((sum, c) => sum + c.total_amount, 0) || 0;
  const scoreStyle = getHealthScoreStyle(healthScore?.overall_score || 50);

  // Build area chart data from forecast
  const forecastChartData = forecast?.daily_breakdown?.slice(0, 14).map((d) => ({
    date: formatDateShort(d.date),
    predicted: d.predicted_amount,
    upper: d.upper,
    lower: d.lower,
  })) || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Your financial overview</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        <StatCard
          title="Total Spending"
          value={formatCurrency(totalSpend)}
          subtitle="This month"
          icon={Wallet}
          trend={4.2}
          color="primary"
        />
        <StatCard
          title="Health Score"
          value={`${healthScore?.overall_score || "--"}/100`}
          subtitle={scoreStyle.label}
          icon={Shield}
          color="success"
        />
        <StatCard
          title="30-Day Forecast"
          value={formatCurrency(forecast?.predicted_total || 0)}
          subtitle={`~${formatCurrency(forecast?.daily_average || 0)}/day`}
          icon={TrendingUp}
          color="warning"
        />
        <StatCard
          title="Budget Alerts"
          value={String(insights?.filter((i: { severity: string }) => i.severity === "alert").length || 0)}
          subtitle="Categories over limit"
          icon={AlertTriangle}
          color="danger"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Spending by category (Pie) */}
        <div className="card">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Spending by Category</h2>
          {categoryData && categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={categoryData.slice(0, 8)}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="total_amount"
                  nameKey="category"
                >
                  {categoryData.slice(0, 8).map((entry) => (
                    <Cell key={entry.category} fill={getCategoryColor(entry.category)} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), "Amount"]}
                />
                <Legend
                  iconType="circle"
                  iconSize={8}
                  formatter={(value) => <span className="text-xs text-gray-600">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
              Add transactions to see spending breakdown
            </div>
          )}
        </div>

        {/* 14-day forecast (Area) */}
        <div className="card">
          <h2 className="text-base font-semibold text-gray-900 mb-4">14-Day Spending Forecast</h2>
          {forecastChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={forecastChartData}>
                <defs>
                  <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                <Tooltip formatter={(v: number) => [`$${v.toFixed(2)}`, "Predicted"]} />
                <Area
                  type="monotone"
                  dataKey="predicted"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  fill="url(#forecastGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
              Forecast loading...
            </div>
          )}
        </div>
      </div>

      {/* Health score breakdown */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-base font-semibold text-gray-900">Financial Health Score</h2>
          <div className={`text-2xl font-bold ${scoreStyle.color}`}>
            {healthScore?.overall_score || "--"}
            <span className="text-sm font-normal text-gray-400">/100</span>
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: "Savings Rate", key: "savings_rate_score" },
            { label: "Budget Adherence", key: "budget_adherence_score" },
            { label: "Stability", key: "spending_stability_score" },
            { label: "Emergency Fund", key: "emergency_fund_score" },
            { label: "Debt Ratio", key: "debt_ratio_score" },
          ].map(({ label, key }) => {
            const score = healthScore?.[key as keyof typeof healthScore] as number | undefined;
            const style = getHealthScoreStyle(score || 50);
            return (
              <div key={key} className="text-center">
                <div className={`text-lg font-bold ${style.color}`}>{score?.toFixed(0) || "--"}</div>
                <div className="w-full bg-gray-100 rounded-full h-1.5 mt-1 mb-1">
                  <div
                    className="h-1.5 rounded-full bg-primary-500 transition-all"
                    style={{ width: `${score || 0}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500">{label}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent insights */}
      {insights && insights.length > 0 && (
        <div className="card">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Recent Insights</h2>
          <div className="space-y-3">
            {insights.slice(0, 3).map((insight: { insight_type: string; severity: string; title: string; message: string }, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50">
                <Target className="w-4 h-4 text-primary-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-800">{insight.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{insight.message}</p>
                </div>
                <span className={`ml-auto badge ${
                  insight.severity === "alert" ? "badge-danger" :
                  insight.severity === "warning" ? "badge-warning" : "badge-info"
                }`}>
                  {insight.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
