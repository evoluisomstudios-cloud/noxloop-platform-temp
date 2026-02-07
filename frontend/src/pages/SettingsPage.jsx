import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { DashboardLayout } from "../components/DashboardLayout";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { 
  User,
  CreditCard,
  Sparkles,
  CheckCircle,
  Loader2,
  LogOut
} from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const SettingsPage = ({ user, onLogout, refreshUser }) => {
  const [searchParams] = useSearchParams();
  const [plans, setPlans] = useState({});
  const [subscribing, setSubscribing] = useState(null);
  const [checkingPayment, setCheckingPayment] = useState(false);

  useEffect(() => {
    fetchPlans();
    
    // Check if returning from subscription payment
    const sessionId = searchParams.get("session_id");
    if (sessionId && searchParams.get("subscription") === "success") {
      checkSubscriptionStatus(sessionId);
    }
  }, [searchParams]);

  const fetchPlans = async () => {
    try {
      const response = await fetch(`${API}/billing/plans`, {
        credentials: "include",
      });
      if (response.ok) {
        setPlans(await response.json());
      }
    } catch (error) {
      console.error("Error fetching plans:", error);
    }
  };

  const checkSubscriptionStatus = async (sessionId) => {
    setCheckingPayment(true);
    let attempts = 0;
    const maxAttempts = 5;

    const pollStatus = async () => {
      try {
        const response = await fetch(`${API}/billing/status/${sessionId}`, {
          credentials: "include",
        });
        
        if (response.ok) {
          const data = await response.json();
          
          if (data.payment_status === "paid") {
            await refreshUser();
            toast.success("Subscrição ativada com sucesso!");
            setCheckingPayment(false);
            // Clear URL params
            window.history.replaceState({}, "", "/settings");
            return;
          }
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(pollStatus, 2000);
        } else {
          setCheckingPayment(false);
          toast.error("Não foi possível confirmar o pagamento. Contacta o suporte.");
        }
      } catch (error) {
        setCheckingPayment(false);
        toast.error("Erro ao verificar pagamento");
      }
    };

    pollStatus();
  };

  const handleSubscribe = async (planId) => {
    setSubscribing(planId);
    
    try {
      const originUrl = window.location.origin;
      const response = await fetch(`${API}/billing/subscribe?plan_id=${planId}&origin_url=${encodeURIComponent(originUrl)}`, {
        method: "POST",
        credentials: "include",
      });
      
      if (response.ok) {
        const data = await response.json();
        window.location.href = data.url;
      } else {
        toast.error("Erro ao processar subscrição");
        setSubscribing(null);
      }
    } catch (error) {
      toast.error("Erro de conexão");
      setSubscribing(null);
    }
  };

  const plansList = [
    {
      id: "starter",
      name: "Starter",
      price: plans.starter?.price || 9.99,
      credits: plans.starter?.credits || 50,
      features: [
        "50 gerações de produto",
        "Landing pages ilimitadas",
        "Pagamentos Stripe",
        "Analytics básico",
      ],
    },
    {
      id: "pro",
      name: "Pro",
      price: plans.pro?.price || 29.99,
      credits: plans.pro?.credits || 200,
      popular: true,
      features: [
        "200 gerações de produto",
        "Tudo do Starter",
        "Prioridade na geração",
        "Suporte prioritário",
      ],
    },
    {
      id: "enterprise",
      name: "Enterprise",
      price: plans.enterprise?.price || 99.99,
      credits: plans.enterprise?.credits || 1000,
      features: [
        "1000 gerações de produto",
        "Tudo do Pro",
        "API access",
        "White-label",
      ],
    },
  ];

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-8" data-testid="settings-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold mb-1">Definições</h1>
          <p className="text-gray-400">
            Gere a tua conta e subscrição
          </p>
        </div>

        {/* Payment Status Check */}
        {checkingPayment && (
          <div className="card-dashboard bg-indigo-500/10 border-indigo-500/20">
            <div className="flex items-center gap-4">
              <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
              <div>
                <p className="font-medium">A verificar pagamento...</p>
                <p className="text-sm text-gray-400">Aguarda um momento</p>
              </div>
            </div>
          </div>
        )}

        {/* Profile Section */}
        <div className="card-dashboard">
          <div className="flex items-center gap-3 mb-6">
            <User className="w-5 h-5 text-gray-400" />
            <h2 className="text-xl font-semibold">Perfil</h2>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <Label className="text-gray-400 mb-2 block">Nome</Label>
              <Input
                value={user?.name || ""}
                readOnly
                className="bg-[#171717] border-[#262626]"
              />
            </div>
            <div>
              <Label className="text-gray-400 mb-2 block">Email</Label>
              <Input
                value={user?.email || ""}
                readOnly
                className="bg-[#171717] border-[#262626]"
              />
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-[#262626]">
            <Button
              variant="outline"
              onClick={onLogout}
              className="border-red-500/30 text-red-400 hover:bg-red-500/10"
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Terminar Sessão
            </Button>
          </div>
        </div>

        {/* Credits Section */}
        <div className="card-dashboard">
          <div className="flex items-center gap-3 mb-6">
            <Sparkles className="w-5 h-5 text-gray-400" />
            <h2 className="text-xl font-semibold">Créditos</h2>
          </div>
          
          <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
            <div>
              <p className="text-3xl font-bold">{user?.credits || 0}</p>
              <p className="text-gray-400">créditos disponíveis</p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              user?.plan === "pro" 
                ? "bg-indigo-500/20 text-indigo-400"
                : user?.plan === "enterprise"
                ? "bg-purple-500/20 text-purple-400"
                : "bg-gray-500/20 text-gray-400"
            }`}>
              Plano {user?.plan?.charAt(0).toUpperCase() + user?.plan?.slice(1) || "Free"}
            </div>
          </div>
        </div>

        {/* Subscription Plans */}
        <div className="card-dashboard">
          <div className="flex items-center gap-3 mb-6">
            <CreditCard className="w-5 h-5 text-gray-400" />
            <h2 className="text-xl font-semibold">Planos de Subscrição</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {plansList.map((plan) => (
              <div
                key={plan.id}
                className={`relative p-6 rounded-xl border ${
                  plan.popular
                    ? "bg-white/5 border-white/20"
                    : "bg-[#0A0A0A] border-[#262626]"
                } ${user?.plan === plan.id ? "ring-2 ring-green-500" : ""}`}
                data-testid={`plan-${plan.id}`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-white text-black text-xs font-medium rounded-full">
                    Popular
                  </div>
                )}
                
                {user?.plan === plan.id && (
                  <div className="absolute -top-3 right-4 px-3 py-1 bg-green-500 text-white text-xs font-medium rounded-full flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" />
                    Atual
                  </div>
                )}

                <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold">€{plan.price}</span>
                  <span className="text-gray-400">/mês</span>
                </div>

                <ul className="space-y-2 mb-6">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-gray-300">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>

                <Button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={subscribing === plan.id || user?.plan === plan.id}
                  className={`w-full ${
                    user?.plan === plan.id
                      ? "bg-green-500/20 text-green-400 hover:bg-green-500/20 cursor-default"
                      : plan.popular
                      ? "bg-white text-black hover:bg-gray-200"
                      : "bg-white/10 hover:bg-white/20"
                  }`}
                >
                  {subscribing === plan.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : user?.plan === plan.id ? (
                    "Plano Atual"
                  ) : (
                    `Subscrever ${plan.name}`
                  )}
                </Button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};
