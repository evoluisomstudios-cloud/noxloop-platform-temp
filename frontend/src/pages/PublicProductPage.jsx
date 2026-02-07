import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { 
  Zap, 
  CheckCircle, 
  ShieldCheck,
  Download,
  Loader2,
  Star,
  ArrowRight
} from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const PublicProductPage = () => {
  const { productId } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
  const [email, setEmail] = useState("");

  useEffect(() => {
    fetchProduct();
  }, [productId]);

  const fetchProduct = async () => {
    try {
      const response = await fetch(`${API}/public/product/${productId}`);
      if (response.ok) {
        setProduct(await response.json());
      }
    } catch (error) {
      console.error("Error fetching product:", error);
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async () => {
    if (!email) {
      toast.error("Introduz o teu email");
      return;
    }

    setPurchasing(true);
    
    try {
      const originUrl = window.location.origin;
      const response = await fetch(`${API}/checkout/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: productId,
          origin_url: originUrl,
          customer_email: email,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        window.location.href = data.url;
      } else {
        toast.error("Erro ao processar compra");
        setPurchasing(false);
      }
    } catch (error) {
      toast.error("Erro de conexão");
      setPurchasing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Produto não encontrado</h1>
          <p className="text-gray-400">Este produto não está disponível.</p>
        </div>
      </div>
    );
  }

  const landing = product.landing_page || {};

  return (
    <div className="min-h-screen bg-[#050505]" data-testid="public-product-page">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
        <div className="container-marketing flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center">
              <Zap className="w-4 h-4 text-black" />
            </div>
            <span className="font-bold">NOXLOOP</span>
          </div>
          <Button 
            onClick={() => document.getElementById("buy-section")?.scrollIntoView({ behavior: "smooth" })}
            className="bg-white text-black hover:bg-gray-200"
          >
            Comprar Agora
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-32 pb-16 relative">
        <div className="absolute inset-0 gradient-glow opacity-30" />
        <div className="container-marketing relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-6">
              <Star className="w-4 h-4 text-yellow-500" />
              <span className="text-sm text-gray-300">
                {product.product_type === "ebook" ? "eBook Digital" : 
                 product.product_type === "guide" ? "Guia Prático" :
                 product.product_type === "course" ? "Curso Online" : "Template"}
              </span>
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
              {landing.headline || product.title}
            </h1>

            <p className="text-xl text-gray-400 mb-8">
              {landing.subheadline || product.description}
            </p>

            <Button 
              size="lg"
              onClick={() => document.getElementById("buy-section")?.scrollIntoView({ behavior: "smooth" })}
              className="bg-white text-black hover:bg-gray-200 h-14 px-10 text-lg"
            >
              {landing.cta_text || "Comprar Agora"}
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* Benefits */}
      {landing.benefits && landing.benefits.length > 0 && (
        <section className="py-16">
          <div className="container-marketing">
            <h2 className="text-3xl font-bold text-center mb-12">O que vais aprender</h2>
            <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
              {landing.benefits.map((benefit, index) => (
                <div key={index} className="flex items-start gap-4 p-4 rounded-lg bg-white/5">
                  <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-lg">{benefit}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Features */}
      {landing.features && landing.features.length > 0 && (
        <section className="py-16 bg-[#0A0A0A]/50">
          <div className="container-marketing">
            <h2 className="text-3xl font-bold text-center mb-12">O que está incluído</h2>
            <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {landing.features.map((feature, index) => (
                <div key={index} className="card-marketing text-center">
                  <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                    <Download className="w-6 h-6" />
                  </div>
                  <p className="font-medium">{feature}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Testimonial */}
      {landing.testimonial && (
        <section className="py-16">
          <div className="container-marketing">
            <div className="max-w-2xl mx-auto text-center">
              <div className="flex justify-center gap-1 mb-6">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Star key={i} className="w-6 h-6 fill-yellow-500 text-yellow-500" />
                ))}
              </div>
              <blockquote className="text-2xl font-medium mb-6 italic">
                "{landing.testimonial.quote}"
              </blockquote>
              <div>
                <p className="font-semibold">{landing.testimonial.author}</p>
                <p className="text-gray-400">{landing.testimonial.role}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* FAQ */}
      {landing.faq && landing.faq.length > 0 && (
        <section className="py-16 bg-[#0A0A0A]/50">
          <div className="container-marketing">
            <h2 className="text-3xl font-bold text-center mb-12">Perguntas Frequentes</h2>
            <div className="max-w-2xl mx-auto space-y-4">
              {landing.faq.map((item, index) => (
                <div key={index} className="card-dashboard">
                  <h3 className="font-semibold mb-2">{item.question}</h3>
                  <p className="text-gray-400">{item.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Buy Section */}
      <section id="buy-section" className="py-20">
        <div className="container-marketing">
          <div className="max-w-xl mx-auto">
            <div className="card-marketing p-8 text-center">
              <h2 className="text-3xl font-bold mb-2">{product.title}</h2>
              <p className="text-gray-400 mb-6">{product.description}</p>
              
              <div className="text-5xl font-bold mb-6">
                €{product.price.toFixed(2)}
              </div>

              <div className="space-y-4 mb-6">
                <Input
                  type="email"
                  placeholder="O teu email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-12 bg-[#171717] border-[#262626] text-center"
                  data-testid="customer-email-input"
                />
                <Button
                  onClick={handlePurchase}
                  disabled={purchasing}
                  className="w-full h-14 bg-white text-black hover:bg-gray-200 text-lg"
                  data-testid="buy-btn"
                >
                  {purchasing ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      {landing.cta_text || "Comprar Agora"}
                      <ArrowRight className="w-5 h-5 ml-2" />
                    </>
                  )}
                </Button>
              </div>

              {/* Guarantee */}
              <div className="flex items-center justify-center gap-2 text-sm text-gray-400">
                <ShieldCheck className="w-5 h-5 text-green-500" />
                <span>{landing.guarantee || "Garantia de satisfação ou devolução"}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-white/10">
        <div className="container-marketing text-center text-gray-500 text-sm">
          © 2026 NOXLOOP. Todos os direitos reservados.
        </div>
      </footer>
    </div>
  );
};
