import { Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Receipt, Target, Lightbulb,
  MessageSquareText, BarChart3, LogOut, Sparkles,
} from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/utils/helpers";

const NAV_ITEMS = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/transactions", label: "Transactions", icon: Receipt },
  { path: "/budget", label: "Budget", icon: Target },
  { path: "/analytics", label: "Analytics", icon: BarChart3 },
  { path: "/insights", label: "Insights", icon: Lightbulb },
  { path: "/chat", label: "AI Assistant", icon: MessageSquareText },
];

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
        {/* Logo */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-gray-900">FinSight AI</h1>
              <p className="text-xs text-gray-500">Smart Finance</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
            <div
              key={path}
              onClick={() => navigate(path)}
              className={cn(
                location.pathname === path ? "sidebar-link-active" : "sidebar-link"
              )}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
              {path === "/chat" && (
                <span className="ml-auto badge bg-primary-100 text-primary-700 text-[10px]">AI</span>
              )}
            </div>
          ))}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-gray-100">
          <button
            onClick={handleLogout}
            className="sidebar-link w-full text-danger-600 hover:bg-danger-50 hover:text-danger-700"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
