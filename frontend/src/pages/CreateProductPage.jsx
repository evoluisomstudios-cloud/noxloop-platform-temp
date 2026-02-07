import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { DashboardLayout } from "../components/DashboardLayout";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { 
  ArrowRight, 
  ArrowLeft,
  Sparkles,
  BookOpen,
  FileText,
  GraduationCap,
  LayoutTemplate,
  Loader2,
  CheckCircle
} from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const CreateProductPage = ({ user, onLogout, refreshUser }) => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    product_type: "",
    topic: "",
    target_audience: "",
    tone: "professional",
    language: "pt",
  });

  const productTypes = [
    {
      id: "ebook",
      name: "eBook",
      icon: BookOpen,
      description: "Livro digital completo com capítulos",
    },
    {
      id: "guide",
      name: "Guia Prático",
      icon: FileText,
      description: "Guia passo-a-passo com instruções",
    },
    {
      id: "course",
      name: "Curso Online",
      icon: GraduationCap,
      description: "Estrutura de curso com módulos",
    },
    {
      id: "template",
      name: "Template",
      icon: LayoutTemplate,
      description: "Modelo pronto a usar",
    },
  ];

  const tones = [
    { id: "professional", name: "Profissional" },
    { id: "casual", name: "Casual" },
    { id: "academic", name: "Académico" },
    { id: "friendly", name: "Amigável" },
  ];

  const languages = [
    { id: "pt", name: "Português" },
    { id: "en", name: "English" },
    { id: "es", name: "Español" },
  ];

  const handleSubmit = async () => {
    if (user?.credits <= 0) {
      toast.error("Sem créditos suficientes. Faz upgrade do plano.");
      return;
    }

    setLoading(true);
    
    try {
      const response = await fetch(`${API}/products/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const product = await response.json();
        toast.success("Produto gerado com sucesso!");
        await refreshUser();
        navigate(`/products/${product.product_id}`);
      } else {
        const error = await response.json();
        toast.error(error.detail || "Erro ao gerar produto");
      }
    } catch (error) {
      toast.error("Erro de conexão. Tenta novamente.");
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1:
        return formData.product_type !== "";
      case 2:
        return formData.topic.trim() !== "" && formData.target_audience.trim() !== "";
      case 3:
        return formData.title.trim() !== "" && formData.description.trim() !== "";
      default:
        return false;
    }
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-2">Que tipo de produto queres criar?</h2>
              <p className="text-gray-400">Escolhe o formato do teu produto digital</p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              {productTypes.map((type) => (
                <button
                  key={type.id}
                  onClick={() => setFormData({ ...formData, product_type: type.id })}
                  className={`p-6 rounded-xl border text-left transition-all ${
                    formData.product_type === type.id
                      ? "bg-white/10 border-white/30"
                      : "bg-[#0A0A0A] border-[#262626] hover:border-white/20"
                  }`}
                  data-testid={`product-type-${type.id}`}
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                      formData.product_type === type.id ? "bg-white/20" : "bg-white/10"
                    }`}>
                      <type.icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{type.name}</h3>
                      <p className="text-sm text-gray-400">{type.description}</p>
                    </div>
                    {formData.product_type === type.id && (
                      <CheckCircle className="w-5 h-5 text-green-400 ml-auto" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-2">Define o conteúdo</h2>
              <p className="text-gray-400">Sobre o que vai ser o teu produto?</p>
            </div>

            <div className="space-y-4 max-w-xl mx-auto">
              <div>
                <Label className="text-gray-400 mb-2 block">Tópico / Tema Principal</Label>
                <Input
                  placeholder="Ex: Marketing Digital para Pequenos Negócios"
                  value={formData.topic}
                  onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                  className="h-12 bg-[#171717] border-[#262626]"
                  data-testid="topic-input"
                />
              </div>

              <div>
                <Label className="text-gray-400 mb-2 block">Público-Alvo</Label>
                <Input
                  placeholder="Ex: Empreendedores iniciantes"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                  className="h-12 bg-[#171717] border-[#262626]"
                  data-testid="audience-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-400 mb-2 block">Tom</Label>
                  <div className="flex flex-wrap gap-2">
                    {tones.map((tone) => (
                      <button
                        key={tone.id}
                        onClick={() => setFormData({ ...formData, tone: tone.id })}
                        className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                          formData.tone === tone.id
                            ? "bg-white text-black"
                            : "bg-[#171717] border border-[#262626] hover:border-white/20"
                        }`}
                        data-testid={`tone-${tone.id}`}
                      >
                        {tone.name}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-gray-400 mb-2 block">Idioma</Label>
                  <div className="flex flex-wrap gap-2">
                    {languages.map((lang) => (
                      <button
                        key={lang.id}
                        onClick={() => setFormData({ ...formData, language: lang.id })}
                        className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                          formData.language === lang.id
                            ? "bg-white text-black"
                            : "bg-[#171717] border border-[#262626] hover:border-white/20"
                        }`}
                        data-testid={`language-${lang.id}`}
                      >
                        {lang.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-2">Detalhes finais</h2>
              <p className="text-gray-400">Define o título e descrição do produto</p>
            </div>

            <div className="space-y-4 max-w-xl mx-auto">
              <div>
                <Label className="text-gray-400 mb-2 block">Título do Produto</Label>
                <Input
                  placeholder="Ex: Guia Completo de Marketing Digital"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="h-12 bg-[#171717] border-[#262626]"
                  data-testid="title-input"
                />
              </div>

              <div>
                <Label className="text-gray-400 mb-2 block">Descrição</Label>
                <Textarea
                  placeholder="Descreve brevemente o que o cliente vai aprender..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="min-h-[120px] bg-[#171717] border-[#262626]"
                  data-testid="description-input"
                />
              </div>

              {/* Summary */}
              <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                <h4 className="font-medium mb-3">Resumo do Produto</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tipo:</span>
                    <span>{productTypes.find(t => t.id === formData.product_type)?.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tópico:</span>
                    <span className="truncate ml-4">{formData.topic}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Público:</span>
                    <span className="truncate ml-4">{formData.target_audience}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tom:</span>
                    <span>{tones.find(t => t.id === formData.tone)?.name}</span>
                  </div>
                </div>
              </div>

              {/* Credits Info */}
              <div className="flex items-center justify-between p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                <div className="flex items-center gap-3">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  <span>Esta geração vai usar 1 crédito</span>
                </div>
                <span className="text-gray-400">
                  {user?.credits || 0} disponíveis
                </span>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="max-w-3xl mx-auto py-8" data-testid="create-product-page">
        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-2 mb-12">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`h-1 rounded-full transition-all duration-300 ${
                s <= step ? "bg-white w-12" : "bg-[#262626] w-8"
              }`}
            />
          ))}
        </div>

        {/* Step Content */}
        {renderStep()}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-12">
          <Button
            variant="ghost"
            onClick={() => setStep(step - 1)}
            disabled={step === 1}
            className={step === 1 ? "invisible" : ""}
            data-testid="prev-step-btn"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Anterior
          </Button>

          {step < 3 ? (
            <Button
              onClick={() => setStep(step + 1)}
              disabled={!canProceed()}
              className="bg-white text-black hover:bg-gray-200"
              data-testid="next-step-btn"
            >
              Seguinte
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={!canProceed() || loading}
              className="bg-white text-black hover:bg-gray-200 min-w-[160px]"
              data-testid="generate-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  A Gerar...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Gerar com IA
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};
