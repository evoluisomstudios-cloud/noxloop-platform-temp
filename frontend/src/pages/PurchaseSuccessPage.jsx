import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { 
  Zap, 
  CheckCircle, 
  Download,
  Loader2,
  AlertCircle
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const PurchaseSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("checking"); // checking, success, error
  const [delivery, setDelivery] = useState(null);
  const [paymentInfo, setPaymentInfo] = useState(null);

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    if (sessionId) {
      checkPaymentStatus(sessionId);
    } else {
      setStatus("error");
    }
  }, [searchParams]);

  const checkPaymentStatus = async (sessionId) => {
    let attempts = 0;
    const maxAttempts = 10;

    const poll = async () => {
      try {
        const response = await fetch(`${API}/checkout/status/${sessionId}`);
        
        if (response.ok) {
          const data = await response.json();
          setPaymentInfo(data);
          
          if (data.payment_status === "paid") {
            // Fetch delivery
            const deliveryResponse = await fetch(`${API}/delivery/${sessionId}`);
            if (deliveryResponse.ok) {
              setDelivery(await deliveryResponse.json());
            }
            setStatus("success");
            return;
          } else if (data.status === "expired") {
            setStatus("error");
            return;
          }
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          setStatus("error");
        }
      } catch (error) {
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000);
        } else {
          setStatus("error");
        }
      }
    };

    poll();
  };

  const handleDownload = () => {
    if (delivery?.content) {
      const blob = new Blob([delivery.content], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${delivery.title || "produto"}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-6" data-testid="purchase-success-page">
      <div className="max-w-lg w-full text-center">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center">
            <Zap className="w-5 h-5 text-black" />
          </div>
          <span className="text-xl font-bold">NOXLOOP</span>
        </div>

        {status === "checking" && (
          <div className="card-dashboard py-12">
            <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-indigo-500" />
            <h2 className="text-2xl font-bold mb-2">A verificar pagamento...</h2>
            <p className="text-gray-400">Aguarda um momento enquanto confirmamos a tua compra.</p>
          </div>
        )}

        {status === "success" && (
          <div className="card-dashboard py-12">
            <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h2 className="text-3xl font-bold mb-2">Compra Confirmada!</h2>
            <p className="text-gray-400 mb-8">
              Obrigado pela tua compra. O teu produto está pronto para download.
            </p>

            {delivery && (
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-white/5 text-left">
                  <h3 className="font-semibold mb-1">{delivery.title}</h3>
                  <p className="text-sm text-gray-400">
                    Tipo: {delivery.product_type}
                  </p>
                  <p className="text-sm text-gray-400">
                    Downloads restantes: {delivery.downloads_remaining}
                  </p>
                </div>

                <Button
                  onClick={handleDownload}
                  className="w-full h-12 bg-white text-black hover:bg-gray-200"
                  data-testid="download-btn"
                >
                  <Download className="w-5 h-5 mr-2" />
                  Download do Produto
                </Button>
              </div>
            )}

            <div className="mt-8 pt-6 border-t border-[#262626]">
              <p className="text-sm text-gray-400 mb-4">
                Tens questões? Contacta o vendedor.
              </p>
              <Link to="/">
                <Button variant="outline" className="border-[#262626]">
                  Voltar ao Início
                </Button>
              </Link>
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="card-dashboard py-12">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-6">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Erro no Pagamento</h2>
            <p className="text-gray-400 mb-6">
              Não foi possível confirmar o teu pagamento. Por favor tenta novamente ou contacta o suporte.
            </p>
            <Link to="/">
              <Button className="bg-white text-black hover:bg-gray-200">
                Voltar ao Início
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};
