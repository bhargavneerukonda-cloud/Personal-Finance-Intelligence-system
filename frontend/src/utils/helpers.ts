/**
 * Shared utility functions.
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Tailwind class merging utility
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Currency formatting
export function formatCurrency(
  amount: number,
  currency: string = "USD",
  locale: string = "en-US"
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

// Percentage formatting
export function formatPercent(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

// Date formatting
export function formatDate(dateStr: string, options?: Intl.DateTimeFormatOptions): string {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    ...options,
  });
}

export function formatDateShort(dateStr: string): string {
  return formatDate(dateStr, { month: "short", day: "numeric" });
}

export function formatRelativeDate(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return formatDate(dateStr);
}

// Category color mapping
export const CATEGORY_COLORS: Record<string, string> = {
  "Food & Dining": "#f59e0b",
  "Shopping": "#8b5cf6",
  "Transportation": "#3b82f6",
  "Entertainment": "#ec4899",
  "Healthcare": "#10b981",
  "Utilities": "#6b7280",
  "Housing": "#ef4444",
  "Groceries": "#22c55e",
  "Uncategorized": "#94a3b8",
};

export function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category] || "#94a3b8";
}

// Health score grade styling
export function getHealthScoreStyle(score: number): {
  color: string;
  bg: string;
  label: string;
  grade: string;
} {
  if (score >= 85) return { color: "text-success-600", bg: "bg-success-50", label: "Excellent", grade: "A" };
  if (score >= 70) return { color: "text-primary-600", bg: "bg-primary-50", label: "Good", grade: "B" };
  if (score >= 55) return { color: "text-warning-600", bg: "bg-warning-50", label: "Fair", grade: "C" };
  if (score >= 40) return { color: "text-orange-600", bg: "bg-orange-50", label: "Poor", grade: "D" };
  return { color: "text-danger-600", bg: "bg-danger-50", label: "Critical", grade: "F" };
}

// Severity badge styling
export function getSeverityStyle(severity: "info" | "warning" | "alert"): string {
  switch (severity) {
    case "alert": return "badge-danger";
    case "warning": return "badge-warning";
    case "info": return "badge-info";
  }
}

// Truncate text
export function truncate(text: string, maxLength: number = 40): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + "...";
}

// Generate unique ID for chat messages
export function generateId(): string {
  return Math.random().toString(36).slice(2, 11);
}
