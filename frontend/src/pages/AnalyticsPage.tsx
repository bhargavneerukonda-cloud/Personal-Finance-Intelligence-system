import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Legend,
} from "recharts";
import { transactionsApi, insightsApi } from "@/services/api";
import { SpendingSummary, Forecast } from "@/types";
import { formatCurrency, formatPercent, getCategoryColor } from "@/utils/helpers";

const HORIZONS = [
  { label: "30 days", value: 30 },
  { label: "60 days", value: 60 },
  { label: "90 days", value: 90 },
];

export default function AnalyticsPage() {
  const [horizon, setHorizon] = useState(30);

  const { data: categoryData } = useQuery<SpendingSummary[]>({
    queryKey: ["spending-by-category"],
    queryFn: () => transactionsApi.summaryByCategory().then((r) => r.data),
  });

  const { data: forecast } = useQuery<Forecast>({
    queryKey: ["forecast", horizon],
    queryFn: () => insightsApi.getForecast(horizon).then((r) => r.data),
  });

  // Prepare bar chart data (top 7 categories)
  const barData = categoryData?.slice(0, 7).map((c) => ({
    category: c.category.replace(" & ", " &\n"),
    amount: Number(c.total_amount.toFixed(2)),
    fill: getCategoryColor(c.category),
  })) || [];

  // Prepare forecast line data (sample every 3 days for readability)
  const forecastData = forecast?.daily_breakdown
    ?.filter((_, i) => i % 3 === 0)
    .map((d) => ({
      date: d.date.slice(5), // MM-DD
      predicted: d.predicted_amount,
      upper: d.upper || d.predicted_amount * 1.1,
      lower: d.lower || d.predicted_amount * 0.9,
    })) || [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-500 mt-1">Deep-dive into your spending patterns and forecasts</p>
      </div>

      {/* Spending by category bar chart */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-900 mb-6">Spending by Category</h2>
        {barData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="category"
                tick={{ fontSize: 11 }}
                interval={0}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `$${v >= 1000 ? (v / 1000).toFixed(1) + "k" : v}`}
              />
              <Tooltip
                formatter={(v: number) => [formatCurrency(v), "Spent"]}
                cursor={{ fill: "#f8fafc" }}
              />
              <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                {barData.map((entry, i) => (
                  <rect key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
            Add transactions to see category breakdown
          </div>
        )}
      </div>

      {/* Category table */}
      {categoryData && categoryData.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <div className="p-5 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">Category Breakdown</h2>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50">
                <th className="text-left py-3 px-5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Category</th>
                <th className="text-right py-3 px-5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Total</th>
                <th className="text-right py-3 px-5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Transactions</th>
                <th className="text-right py-3 px-5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Avg</th>
                <th className="text-right py-3 px-5 text-xs font-semibold text-gray-500 uppercase tracking-wider">% of Total</th>
                <th className="py-3 px-5 text-xs font-semibold text-gray-500 uppercase tracking-wider">Share</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {categoryData.map((row) => (
                <tr key={row.category} className="hover:bg-gray-50 transition-colors">
                  <td className="py-3 px-5">
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: getCategoryColor(row.category) }}
                      />
                      <span className="font-medium text-gray-800">{row.category}</span>
                    </div>
                  </td>
                  <td className="py-3 px-5 text-right font-semibold text-gray-900">
                    {formatCurrency(row.total_amount)}
                  </td>
                  <td className="py-3 px-5 text-right text-gray-500">{row.transaction_count}</td>
                  <td className="py-3 px-5 text-right text-gray-500">
                    {formatCurrency(row.avg_transaction)}
                  </td>
                  <td className="py-3 px-5 text-right text-gray-500">
                    {formatPercent(row.percentage_of_total)}
                  </td>
                  <td className="py-3 px-5">
                    <div className="w-full bg-gray-100 rounded-full h-1.5 min-w-16">
                      <div
                        className="h-1.5 rounded-full"
                        style={{
                          width: `${row.percentage_of_total}%`,
                          backgroundColor: getCategoryColor(row.category),
                        }}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Forecast chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Spending Forecast</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Predicted: <span className="font-medium text-gray-900">{formatCurrency(forecast?.predicted_total || 0)}</span>
              {" "}· Daily avg: <span className="font-medium text-gray-900">{formatCurrency(forecast?.daily_average || 0)}</span>
              {" "}· Method: <span className="text-primary-600">{forecast?.method || "—"}</span>
            </p>
          </div>
          <div className="flex gap-2">
            {HORIZONS.map((h) => (
              <button
                key={h.value}
                onClick={() => setHorizon(h.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  horizon === h.value
                    ? "bg-primary-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {h.label}
              </button>
            ))}
          </div>
        </div>
        {forecastData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
              <Tooltip
                formatter={(v: number, name: string) => [
                  formatCurrency(v),
                  name === "predicted" ? "Predicted" : name === "upper" ? "Upper bound" : "Lower bound",
                ]}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="upper"
                stroke="#e2e8f0"
                strokeWidth={1}
                strokeDasharray="4 4"
                dot={false}
                name="upper"
              />
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#0ea5e9"
                strokeWidth={2.5}
                dot={false}
                name="predicted"
              />
              <Line
                type="monotone"
                dataKey="lower"
                stroke="#e2e8f0"
                strokeWidth={1}
                strokeDasharray="4 4"
                dot={false}
                name="lower"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
            Forecast data loading...
          </div>
        )}
      </div>
    </div>
  );
}
