// src/pages/LoginPage.tsx
import { useNavigate } from "react-router-dom";
import { HelpCircle, ExternalLink, ShieldCheck } from "lucide-react";

const SUCCESS_FACTORS_URL =
  "https://performancemanager4.successfactors.com/login#/companyEntry";

const LoginPage = () => {
  const navigate = useNavigate();

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center bg-cover bg-center relative"
      style={{
        backgroundImage:
          'url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop")',
        backgroundColor: "#1a1a1a",
      }}
    >
      <div className="absolute inset-0 bg-black/60 z-0"></div>

      <button
        type="button"
        className="absolute bottom-6 right-6 text-gray-400 hover:text-white transition z-20"
        title="Yardım"
      >
        <HelpCircle size={32} />
      </button>

      <div className="relative z-10 w-full max-w-md p-8 bg-white/10 backdrop-blur-md border border-white/10 rounded-3xl shadow-2xl">
        <div className="flex justify-center items-center gap-2 mb-8">
          <div className="text-3xl font-bold text-white tracking-wide flex items-center gap-2">
            Sirobot
            <span className="w-6 h-6 rounded-full bg-gradient-to-tr from-blue-400 to-green-400 inline-block"></span>
            <span className="font-light text-gray-300">siro</span>
          </div>
        </div>

        <div className="flex justify-center mb-6">
          <div className="h-16 w-16 rounded-2xl bg-emerald-400/15 border border-emerald-300/30 flex items-center justify-center">
            <ShieldCheck className="h-9 w-9 text-emerald-300" />
          </div>
        </div>

        <div className="text-center space-y-4">
          <h1 className="text-2xl font-semibold text-white">
            SuccessFactors üzerinden giriş yapın
          </h1>

          <p className="text-sm leading-6 text-gray-300">
            Siro HR Assistant uygulamasına doğrudan bu sayfadan giriş yapılamaz.
            Lütfen önce SuccessFactors hesabınıza giriş yapın ve chatbot
            bağlantısını SuccessFactors içerisinden açın.
          </p>

          <a
            href={SUCCESS_FACTORS_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-gray-200 py-3 font-semibold text-black transition-all duration-300 hover:bg-white hover:scale-[1.02] active:scale-95"
          >
            SuccessFactors'a Git
            <ExternalLink size={18} />
          </a>

          <button
            type="button"
            onClick={() => navigate("/admin-login")}
            className="text-gray-400 text-sm hover:text-white transition pt-3"
          >
            Admin misiniz?
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;