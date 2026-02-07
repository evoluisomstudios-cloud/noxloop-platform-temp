import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const AuthCallbackPage = ({ onLogin }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processCallback = async () => {
      const code = searchParams.get("code");
      const error = searchParams.get("error");

      if (error) {
        toast.error("Erro na autenticação Google");
        navigate("/auth", { replace: true });
        return;
      }

      if (!code) {
        navigate("/auth", { replace: true });
        return;
      }

      try {
        const redirectUri = window.location.origin + "/auth/callback";
        
        const response = await fetch(`${API}/auth/google/callback`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            code: code,
            redirect_uri: redirectUri,
          }),
        });

        if (response.ok) {
          const userData = await response.json();
          onLogin(userData);
          toast.success("Bem-vindo!");
          navigate("/dashboard", { replace: true });
        } else {
          const data = await response.json();
          toast.error(data.detail || "Erro na autenticação");
          navigate("/auth", { replace: true });
        }
      } catch (error) {
        console.error("Auth callback error:", error);
        toast.error("Erro de conexão");
        navigate("/auth", { replace: true });
      }
    };

    processCallback();
  }, [searchParams, navigate, onLogin]);

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center">
      <div className="text-center">
        <div className="spinner mx-auto mb-4" />
        <p className="text-gray-400">A autenticar...</p>
      </div>
    </div>
  );
};
