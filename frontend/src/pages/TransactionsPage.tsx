import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, Filter, RefreshCw, AlertCircle, Repeat } from "lucide-react";
import { transactionsApi } from "@/services/api";
import { Transaction, TransactionListResponse } from "@/types";
import { formatCurrency, formatRelativeDate, getCategoryColor, cn } from "@/utils/helpers";

const CATEGORIES = [
  "All", "Food & Dining", "Shopping", "Transportation", "Entertainment",
  "Healthcare", "Utilities", "Housing", "Groceries", "Uncategorized",
];

function CategoryBadge({ category }: { category: string }) {
  const color = getCategoryColor(category);
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
      style={{ backgroundColor: `${color}18`, color }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
      {category}
    </span>
  );
}

function ConfidencePill({ score }: { score: number | null }) {
  if (!score) return null;
  const pct = Math.round(score * 100);
  const color = pct >= 90 ? "text-success-600 bg-success-50" : pct >= 70 ? "text-warning-600 bg-warning-50" : "text-danger-600 bg-danger-50";
  return <span className={`badge ${color}`}>{pct}%</span>;
}

export default function TransactionsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");

  const { data, isLoading } = useQuery<TransactionListResponse>({
    queryKey: ["transactions", page, search, category],
    queryFn: () =>
      transactionsApi.list({
        page,
        page_size: 20,
        search: search || undefined,
        category: category !== "All" ? category : undefined,
      }).then((r) => r.data),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      transactionsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["transactions"] }),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
        <p className="text-gray-500 mt-1">
          {data?.total ? `${data.total.toLocaleString()} transactions` : "Loading..."}
        </p>
      </div>

      {/* Filters */}
      <div className="card py-4">
        <div className="flex flex-col md:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search merchant or description..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="input pl-9"
            />
          </div>

          {/* Category filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              className="input pl-9 pr-8 appearance-none cursor-pointer min-w-48"
            >
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>

          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ["transactions"] })}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Date</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Merchant</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Category</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Confidence</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Flags</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {isLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <td key={j} className="py-3 px-4">
                        <div className="h-4 bg-gray-100 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-16 text-center text-gray-400">
                    No transactions found. Add your first transaction or connect a bank account.
                  </td>
                </tr>
              ) : (
                data?.items.map((tx: Transaction) => (
                  <tr key={tx.id} className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-gray-500 text-xs whitespace-nowrap">
                      {formatRelativeDate(tx.transaction_date)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-gray-800">
                        {tx.merchant_name || "Unknown"}
                      </div>
                      <div className="text-xs text-gray-400 truncate max-w-xs">
                        {tx.description}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <CategoryBadge category={tx.effective_category} />
                      {tx.category_user_override && (
                        <span className="ml-1 text-[10px] text-gray-400">edited</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <ConfidencePill score={tx.confidence_score} />
                    </td>
                    <td className={cn(
                      "py-3 px-4 text-right font-semibold tabular-nums",
                      tx.amount > 0 ? "text-danger-600" : "text-success-600"
                    )}>
                      {tx.amount > 0 ? "-" : "+"}{formatCurrency(Math.abs(tx.amount))}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1">
                        {tx.is_recurring && (
                          <Repeat className="w-3.5 h-3.5 text-primary-400" title="Recurring" />
                        )}
                        {tx.anomaly_flag && !tx.anomaly_flag.is_dismissed && (
                          <AlertCircle className="w-3.5 h-3.5 text-danger-400" title="Anomaly flagged" />
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
            <span className="text-xs text-gray-500">
              Page {data.page} of {data.total_pages} · {data.total} total
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-secondary text-xs py-1 px-3"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
                className="btn-secondary text-xs py-1 px-3"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
