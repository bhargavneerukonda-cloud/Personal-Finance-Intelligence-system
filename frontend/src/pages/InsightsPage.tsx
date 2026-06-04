import { useQuery } from "@tanstack/react-query";
import { Lightbulb, AlertTriangle, Info, TrendingUp, CheckCircle2 } from "lucide-react";
import { insightsApi } from "@/services/api";
import { Insight } from "@/types";

function InsightCard({ insight }: { insight: Insight }) {
  const iconMap = {
    alert: <AlertTriangle className="w-5 h-5 text-danger-500" />,
    warning: <AlertTriangle className="w-5 h-5 text-warning-500" />,
    info: <Info className="w-5 h-5 text-primary-500" />,
  };
  const bgMap = {
    alert: "border-danger-200 bg-danger-50",
    warning: "border-warning-200 bg-warning-50",
    info: "border-primary-100 bg-primary-50",
  };
  return (
    <div className={`rounded-xl border p-5 ${bgMap[insight.severity]}`}>
      <div className="flex items-start gap-3">
        <div className="mt-0.5">{iconMap[insight.severity]}</div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{insight.title}</h3>
          <p className="text-sm text-gray-600 mt-1">{insight.message}</p>
          {insight.action_items.length > 0 && (
            <ul className="mt-3 space-y-1">
              {insight.action_items.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle2 className="w-3.5 h-3.5 text-success-500 mt-0.5 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          )}
        </div>
        <span className={`badge shrink-0 ${
          insight.severity === "alert" ? "badge-danger" :
          insight.severity === "warning" ? "badge-warning" : "badge-info"
        }`}>
          {insight.severity}
        </span>
      </div>
    </div>
  );
}

export default function InsightsPage() {
  const { data: insights, isLoading } = useQuery<Insight[]>({
    queryKey: ["insights"],
    queryFn: () => insightsApi.getInsights().then((r) => r.data),
  });

  const { data: anomalies } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () => insightsApi.getAnomalies().then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Lightbulb className="w-6 h-6 text-warning-500" /> Insights
        </h1>
        <p className="text-gray-500 mt-1">AI-generated financial insights and recommendations</p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card h-28 animate-pulse bg-gray-100" />
          ))}
        </div>
      ) : (
        <div className="space-y-4">
          {insights?.map((insight, i) => (
            <InsightCard key={i} insight={insight} />
          ))}
        </div>
      )}

      {/* Anomaly section */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-danger-500" /> Anomaly Detection
        </h2>
        {anomalies?.anomalies?.length === 0 || !anomalies?.anomalies ? (
          <div className="flex items-center gap-3 text-success-600 bg-success-50 rounded-lg p-4">
            <CheckCircle2 className="w-5 h-5" />
            <div>
              <p className="font-medium">No anomalies detected</p>
              <p className="text-sm text-gray-500 mt-0.5">Your recent transactions look normal</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {anomalies.anomalies.map((a: Record<string, unknown>, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 border border-danger-200 rounded-lg bg-danger-50">
                <AlertTriangle className="w-4 h-4 text-danger-500 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-gray-800">{String(a.anomaly_type)}</p>
                  <p className="text-gray-500">Score: {Number(a.anomaly_score).toFixed(3)}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
