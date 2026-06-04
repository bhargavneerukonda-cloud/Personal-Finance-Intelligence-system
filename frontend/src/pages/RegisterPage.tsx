import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles, Loader2 } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, login, isLoading, error, clearError } = useAuthStore();
  const [form, setForm] = useState({ email: "", password: "", full_name: "", confirm: "" });
  const [validationError, setValidationError] = useState("");

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationError("");

    if (form.password !== form.confirm) {
      setValidationError("Passwords do not match");
      return;
    }
    if (form.password.length < 8) {
      setValidationError("Password must be at least 8 characters");
      return;
    }

    try {
      await register(form.email, form.password, form.full_name);
      await login(form.email, form.password);
      navigate("/dashboard");
    } catch {
      // error shown from store
    }
  };

  const displayError = validationError || error;

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
          <p className="text-gray-500 mt-1 text-sm">Start your AI-powered financial journey</p>
        </div>

        <div className="card shadow-xl border-gray-100">
          <form onSubmit={handleSubmit} className="space-y-5">
            {displayError && (
              <div className="bg-danger-50 border border-danger-200 text-danger-700 rounded-lg px-4 py-3 text-sm">
                {displayError}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Full Name</label>
              <input
                type="text"
                value={form.full_name}
                onChange={set("full_name")}
                className="input"
                placeholder="Jane Smith"
                required
                autoFocus
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={set("email")}
                className="input"
                placeholder="jane@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={set("password")}
                className="input"
                placeholder="Min. 8 characters"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Confirm Password</label>
              <input
                type="password"
                value={form.confirm}
                onChange={set("confirm")}
                className="input"
                placeholder="Repeat your password"
                required
              />
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary w-full flex items-center justify-center gap-2">
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Creating account...</>
              ) : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-5">
            Already have an account?{" "}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              Sign in
            </Link>
          </p>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          By creating an account you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}
