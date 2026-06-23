//AdminLoginPage

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import { API_BASE_URL } from "@/App";

const AdminLoginPage = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/admin/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Admin girişi başarısız oldu.");
      }

      localStorage.setItem("admin_token", data.access_token);
      navigate("/admin");
    } catch (err: any) {
      setError(err.message || "Bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center bg-cover bg-center relative"
      style={{
        backgroundImage:
          'url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop")',
        backgroundColor: "#1a1a1a"
      }}
    >
      <div className="absolute inset-0 bg-black/70 z-0"></div>

      <div className="relative z-10 w-full max-w-md p-8 bg-white/10 backdrop-blur-md border border-white/10 rounded-3xl shadow-2xl">
        <div className="flex justify-center items-center gap-2 mb-10">
          <div className="text-3xl font-bold text-white tracking-wide flex items-center gap-2">
            Admin Panel
            <ShieldCheck className="text-green-400" size={28} />
          </div>
        </div>

        <form onSubmit={handleAdminLogin} className="space-y-8">
          <div className="relative group">
            <input
              type="email"
              placeholder="Admin Mail"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-transparent border-b border-gray-500 text-white placeholder-gray-400 focus:outline-none focus:border-white transition-colors py-2 pr-10"
            />
          </div>

          <div className="relative group">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-transparent border-b border-gray-500 text-white placeholder-gray-400 focus:outline-none focus:border-white transition-colors py-2 pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-0 top-2 text-gray-400 hover:text-white transition cursor-pointer"
            >
              {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>

          {error && (
            <div className="text-red-400 text-sm text-center bg-red-500/10 p-2 rounded">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gray-200 hover:bg-white text-black font-semibold rounded-full py-3 transition-all duration-300 transform hover:scale-[1.02] active:scale-95 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? "Login..." : "Login as Admin"}
          </button>

          <div className="flex justify-center pt-2">
            <button
              type="button"
              onClick={() => navigate("/")}
              className="text-gray-400 text-sm hover:text-white transition"
            >
              Kullanıcı girişine dön
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AdminLoginPage;