// ── Auth ────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  currency_code: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ── Transactions ─────────────────────────────────────────────────────────────
export interface Transaction {
  id: string;
  account_id: string;
  amount: number;
  merchant_name: string | null;
  description: string;
  transaction_date: string;
  effective_category: string;
  category_predicted: string | null;
  category_user_override: string | null;
  confidence_score: number | null;
  is_recurring: boolean;
  tags: string | null;
  ml_prediction: MLPrediction | null;
  anomaly_flag: AnomalyFlag | null;
  created_at: string;
}

export interface MLPrediction {
  category: string;
  confidence: number;
  shap_values: Record<string, number> | null;
  model_version: string;
}

export interface AnomalyFlag {
  anomaly_type: string;
  anomaly_score: number;
  is_confirmed_fraud: boolean;
  is_dismissed: boolean;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SpendingSummary {
  category: string;
  total_amount: number;
  transaction_count: number;
  percentage_of_total: number;
  avg_transaction: number;
}

// ── Budget ───────────────────────────────────────────────────────────────────
export interface BudgetCategory {
  id: string;
  category_name: string;
  allocated_amount: number;
  spent_amount: number;
  remaining: number;
  utilization_pct: number;
  alert_threshold_pct: number;
  status: "ok" | "warning" | "over";
}

export interface Budget {
  id: string;
  name: string;
  period_type: string;
  period_start: string;
  period_end: string;
  total_limit: number;
  total_spent: number;
  utilization_pct: number;
  categories: BudgetCategory[];
}

// ── Insights ─────────────────────────────────────────────────────────────────
export interface Insight {
  insight_type: "saving_opportunity" | "budget_alert" | "pattern" | "forecast";
  title: string;
  message: string;
  severity: "info" | "warning" | "alert";
  action_items: string[];
  data?: Record<string, unknown>;
}

// ── Health Score ──────────────────────────────────────────────────────────────
export interface HealthScore {
  overall_score: number;
  savings_rate_score: number;
  budget_adherence_score: number;
  spending_stability_score: number;
  emergency_fund_score: number;
  debt_ratio_score: number;
  score_date: string;
}

// ── Forecast ─────────────────────────────────────────────────────────────────
export interface ForecastDay {
  date: string;
  predicted_amount: number;
  lower?: number;
  upper?: number;
}

export interface Forecast {
  horizon_days: number;
  predicted_total: number;
  daily_average: number;
  confidence_interval_low?: number;
  confidence_interval_high?: number;
  method: string;
  daily_breakdown: ForecastDay[];
}

// ── Chat ──────────────────────────────────────────────────────────────────────
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

// ── Accounts ──────────────────────────────────────────────────────────────────
export interface Account {
  id: string;
  institution_name: string;
  account_name: string;
  account_type: string;
  balance: number;
  currency: string;
  is_active: boolean;
  synced_at: string | null;
}
