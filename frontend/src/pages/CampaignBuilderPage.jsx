import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { DashboardLayout } from "../components/DashboardLayout";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { 
  ArrowRight, 
  ArrowLeft,
  Sparkles,
  Target,
  Megaphone,
  Mail,
  CheckSquare,
  Image,
  Loader2,
  Download,
  Copy
} from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const CampaignBuilderPage = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const { workspaceId } = useParams();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [campaign, setCampaign] = useState(null);
  const [formData, setFormData] = useState({
    niche: "",
    product: "",
    offer: "",
    price: "",
    objective: "vendas",
    tone: "professional",
    channel: "instagram",
    language: "pt",
    use_rag: true,
  });

  const objectives = [
    { id: "vendas", name: "Vendas", desc: "Conversões directas" },
    { id: "leads", name: "Leads", desc: "Captação de contactos" },
  ];

  const tones = [
    { id: "professional", name: "Profissional" },
    { id: "casual", name: "Casual" },
    { id: "urgente", name: "Urgente" },
    { id: "inspiracional", name: "Inspiracional" },
  ];

  const channels = [
    { id: "instagram", name: "Instagram" },
    { id: "facebook", name: "Facebook" },
    { id: "google", name: "Google Ads" },
    { id: "email", name: "Email Marketing" },
    { id: "linkedin", name: "LinkedIn" },
  ];

  const handleGenerate = async () => {
    setLoading(true);
    
    try {
      const wsId = workspaceId || user?.workspaces?.[0]?.workspace_id;
      if (!wsId) {
        toast.error("Nenhum workspace encontrado");
        return;
      }

      const response = await fetch(`${API}/workspaces/${wsId}/campaigns/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const data = await response.json();
        setCampaign(data);
        setStep(3);
        toast.success("Campanha gerada com sucesso!");
      } else {
        const error = await response.json();
        toast.error(error.detail || "Erro ao gerar campanha");
      }
    } catch (error) {
      toast.error("Erro de conexão");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!campaign) return;
    
    try {
      const wsId = workspaceId || user?.workspaces?.[0]?.workspace_id;
      const response = await fetch(`${API}/workspaces/${wsId}/campaigns/${campaign.campaign_id}/export`, {
        credentials: "include",
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `campaign_${campaign.campaign_id}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("Export descarregado!");
      } else {
        toast.error("Erro no export");
      }
    } catch (error) {
      toast.error("Erro de conexão");
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado!");
  };

  const canProceed = () => {
    if (step === 1) {
      return formData.niche && formData.product && formData.offer && formData.price;
    }
    return true;
  };

  const renderStep = () => {
    if (step === 1) {
      return (
        <div className="space-y-6 animate-fade-in">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold mb-2">Configuração da Campanha</h2>
            <p className="text-gray-400">Define os detalhes do teu produto e oferta</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            <div>
              <Label className="text-gray-400 mb-2 block">Nicho / Mercado</Label>
              <Input
                placeholder="Ex: Fitness, Finanças, Tecnologia..."
                value={formData.niche}
                onChange={(e) => setFormData({ ...formData, niche: e.target.value })}
                className="h-12 bg-[#171717] border-[#262626]"
              />
            </div>
            <div>
              <Label className="text-gray-400 mb-2 block">Produto / Serviço</Label>
              <Input
                placeholder="Ex: Curso de Trading, eBook..."
                value={formData.product}
                onChange={(e) => setFormData({ ...formData, product: e.target.value })}
                className="h-12 bg-[#171717] border-[#262626]"
              />
            </div>
            <div>
              <Label className="text-gray-400 mb-2 block">Oferta</Label>
              <Input
                placeholder="Ex: 50% desconto, Bónus exclusivo..."
                value={formData.offer}
                onChange={(e) => setFormData({ ...formData, offer: e.target.value })}
                className="h-12 bg-[#171717] border-[#262626]"
              />
            </div>
            <div>
              <Label className="text-gray-400 mb-2 block">Preço</Label>
              <Input
                placeholder="Ex: €97, €47/mês..."
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                className="h-12 bg-[#171717] border-[#262626]"
              />
            </div>
          </div>
        </div>
      );
    }

    if (step === 2) {
      return (
        <div className="space-y-6 animate-fade-in">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold mb-2">Estratégia</h2>
            <p className="text-gray-400">Define o canal e tom da campanha</p>
          </div>

          <div className="max-w-2xl mx-auto space-y-6">
            <div>
              <Label className="text-gray-400 mb-3 block">Objetivo</Label>
              <div className="grid grid-cols-2 gap-4">
                {objectives.map((obj) => (
                  <button
                    key={obj.id}
                    onClick={() => setFormData({ ...formData, objective: obj.id })}
                    className={`p-4 rounded-lg border text-left transition-all ${
                      formData.objective === obj.id
                        ? "bg-white/10 border-white/30"
                        : "bg-[#0A0A0A] border-[#262626] hover:border-white/20"
                    }`}
                  >
                    <p className="font-semibold">{obj.name}</p>
                    <p className="text-sm text-gray-400">{obj.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-gray-400 mb-3 block">Canal Principal</Label>
              <div className="flex flex-wrap gap-2">
                {channels.map((ch) => (
                  <button
                    key={ch.id}
                    onClick={() => setFormData({ ...formData, channel: ch.id })}
                    className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                      formData.channel === ch.id
                        ? "bg-white text-black"
                        : "bg-[#171717] border border-[#262626] hover:border-white/20"
                    }`}
                  >
                    {ch.name}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <Label className="text-gray-400 mb-3 block">Tom de Comunicação</Label>
              <div className="flex flex-wrap gap-2">
                {tones.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setFormData({ ...formData, tone: t.id })}
                    className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                      formData.tone === t.id
                        ? "bg-white text-black"
                        : "bg-[#171717] border border-[#262626] hover:border-white/20"
                    }`}
                  >
                    {t.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (step === 3 && campaign) {
      const { assets } = campaign;
      
      return (
        <div className="space-y-6 animate-fade-in">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold">Campanha Gerada!</h2>
              <p className="text-gray-400">Revê e exporta os assets</p>
            </div>
            <Button onClick={handleExport} className="bg-white text-black hover:bg-gray-200">
              <Download className="w-4 h-4 mr-2" />
              Export ZIP
            </Button>
          </div>

          {/* Landing Copy */}
          <div className="card-dashboard">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold flex items-center gap-2">
                <Target className="w-5 h-5" />
                Landing Page Copy
              </h3>
              <Button variant="ghost" size="icon" onClick={() => copyToClipboard(JSON.stringify(assets.landing_copy, null, 2))}>
                <Copy className="w-4 h-4" />
              </Button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="p-3 rounded bg-white/5">
                <p className="text-gray-400 text-xs mb-1">Headline</p>
                <p className="text-lg font-bold">{assets.landing_copy?.headline}</p>
              </div>
              <div className="p-3 rounded bg-white/5">
                <p className="text-gray-400 text-xs mb-1">Subheadline</p>
                <p>{assets.landing_copy?.subheadline}</p>
              </div>
              <div className="p-3 rounded bg-white/5">
                <p className="text-gray-400 text-xs mb-1">Benefícios</p>
                <ul className="list-disc list-inside">
                  {assets.landing_copy?.bullets?.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
              </div>
            </div>
          </div>

          {/* Ad Variations */}
          <div className="card-dashboard">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Megaphone className="w-5 h-5" />
              Variações de Anúncios ({assets.ad_variations?.length || 0})
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              {assets.ad_variations?.slice(0, 4).map((ad, i) => (
                <div key={i} className="p-4 rounded-lg bg-white/5">
                  <p className="text-xs text-gray-400 mb-2">Variação {i + 1} - {ad.style}</p>
                  <p className="font-medium mb-2">{ad.hook}</p>
                  <p className="text-sm text-gray-300">{ad.body}</p>
                  <p className="text-sm text-blue-400 mt-2">{ad.cta}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Creative Ideas */}
          <div className="card-dashboard">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Image className="w-5 h-5" />
              Ideias de Criativos ({assets.creative_ideas?.length || 0})
            </h3>
            <div className="space-y-3">
              {assets.creative_ideas?.map((idea, i) => (
                <div key={i} className="p-3 rounded-lg bg-white/5">
                  <p className="font-medium">{idea.concept}</p>
                  <p className="text-sm text-gray-400 mt-1">{idea.visual_description}</p>
                  <p className="text-xs text-gray-500 mt-1">Formato: {idea.format}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Email Sequence */}
          <div className="card-dashboard">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <Mail className="w-5 h-5" />
              Sequência de Emails ({assets.email_sequence?.length || 0})
            </h3>
            <div className="space-y-3">
              {assets.email_sequence?.map((email, i) => (
                <div key={i} className="p-4 rounded-lg bg-white/5">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-xs">Dia {email.day}</span>
                    <span className="text-sm text-gray-400">{email.purpose}</span>
                  </div>
                  <p className="font-medium">{email.subject_line}</p>
                  <p className="text-sm text-gray-400 mt-2 line-clamp-3">{email.body?.substring(0, 200)}...</p>
                </div>
              ))}
            </div>
          </div>

          {/* Checklist */}
          <div className="card-dashboard">
            <h3 className="font-semibold flex items-center gap-2 mb-4">
              <CheckSquare className="w-5 h-5" />
              Checklist de Publicação
            </h3>
            <div className="space-y-2">
              {assets.checklist?.map((item, i) => (
                <div key={i} className="flex items-start gap-3 p-2">
                  <input type="checkbox" className="mt-1" />
                  <div>
                    <p className="font-medium">{item.task}</p>
                    <p className="text-xs text-gray-400">{item.details}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="max-w-4xl mx-auto py-8" data-testid="campaign-builder-page">
        {/* Progress */}
        {step < 3 && (
          <div className="flex items-center justify-center gap-2 mb-12">
            {[1, 2].map((s) => (
              <div
                key={s}
                className={`h-1 rounded-full transition-all duration-300 ${
                  s <= step ? "bg-white w-12" : "bg-[#262626] w-8"
                }`}
              />
            ))}
          </div>
        )}

        {renderStep()}

        {/* Navigation */}
        {step < 3 && (
          <div className="flex items-center justify-between mt-12">
            <Button
              variant="ghost"
              onClick={() => setStep(step - 1)}
              disabled={step === 1}
              className={step === 1 ? "invisible" : ""}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Anterior
            </Button>

            {step < 2 ? (
              <Button
                onClick={() => setStep(step + 1)}
                disabled={!canProceed()}
                className="bg-white text-black hover:bg-gray-200"
              >
                Seguinte
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button
                onClick={handleGenerate}
                disabled={loading}
                className="bg-white text-black hover:bg-gray-200 min-w-[180px]"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    A Gerar...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Gerar Campanha
                  </>
                )}
              </Button>
            )}
          </div>
        )}

        {/* New Campaign Button */}
        {step === 3 && (
          <div className="flex justify-center mt-8">
            <Button
              onClick={() => {
                setStep(1);
                setCampaign(null);
              }}
              variant="outline"
              className="border-[#262626]"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Nova Campanha
            </Button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
