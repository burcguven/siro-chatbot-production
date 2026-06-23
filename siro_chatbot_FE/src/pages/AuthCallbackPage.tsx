import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

const AuthCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const accessToken = searchParams.get("access_token");

    if (!accessToken) {
      navigate("/", { replace: true });
      return;
    }

    localStorage.setItem("siro_token", accessToken);
    navigate("/chat", { replace: true });
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b0f19] text-white">
      <p>Giriş tamamlanıyor...</p>
    </div>
  );
};

export default AuthCallbackPage;