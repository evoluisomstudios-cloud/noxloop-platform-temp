import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { 
  Zap, 
  ArrowRight, 
  Sparkles, 
  CreditCard, 
  BarChart3, 
  Download,
  CheckCircle,
  Star,
  Play
} from "lucide-react";

export const LandingPage = () => {
  const features = [
    {
      icon: Sparkles,
      title: "Geração com IA",
      description: "Cria eBooks, guias e cursos completos em minutos com GPT-5.2",
    },
    {
      icon: CreditCard,
      title: "Pagamentos Integrados",
      description: "Stripe configurado para receber pagamentos de forma automática",
    },
    {
      icon: BarChart3,
      title: "Analytics em Tempo Real",
      description: "Acompanha vendas, conversões e métricas de performance",
    },
    {
      icon: Download,
      title: "Entrega Automática",
      description: "Os clientes recebem acesso instantâneo após a compra",
    },
  ];

  const steps = [
    { number: "01", title: "Define o Tópico", description: "Escolhe o tema e público-alvo do teu produto" },
    { number: "02", title: "A IA Gera", description: "O GPT-5.2 cria conteúdo profissional completo" },
    { number: "03", title: "Personaliza", description: "Ajusta o preço e landing page de venda" },
    { number: "04", title: "Vende", description: "Partilha o link e começa a faturar" },
  ];

  const plans = [
    {
      name: "Starter",
      price: "9.99",
      credits: 50,
      features: ["50 gerações de produto", "Landing pages ilimitadas", "Pagamentos Stripe", "Analytics básico"],
    },
    {
      name: "Pro",
      price: "29.99",
      credits: 200,
      popular: true,
      features: ["200 gerações de produto", "Tudo do Starter", "Prioridade na geração", "Suporte prioritário"],
    },
    {
      name: "Enterprise",
      price: "99.99",
      credits: 1000,
      features: ["1000 gerações de produto", "Tudo do Pro", "API access", "White-label"],
    },
  ];

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
        <div className="container-marketing flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3" data-testid="logo-link">
            <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center">
              <Zap className="w-5 h-5 text-black" />
            </div>
            <span className="text-lg font-bold tracking-tight">DigiForge</span>
          </Link>
          
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-gray-400 hover:text-white transition-colors">Funcionalidades</a>
            <a href="#how-it-works" className="text-gray-400 hover:text-white transition-colors">Como Funciona</a>
            <a href="#pricing" className="text-gray-400 hover:text-white transition-colors">Preços</a>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/auth">
              <Button variant="ghost" className="text-gray-400 hover:text-white" data-testid="login-nav-btn">
                Entrar
              </Button>
            </Link>
            <Link to="/auth">
              <Button className="bg-white text-black hover:bg-gray-200" data-testid="signup-nav-btn">
                Começar Grátis
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-24 overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 gradient-glow opacity-50" />
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url("https://images.unsplash.com/photo-1737505599162-d9932323a889?crop=entropy&cs=srgb&fm=jpg&q=85")`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        
        <div className="container-marketing relative z-10">
          <div className="max-w-4xl">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8 animate-fade-in">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span className="text-sm text-gray-300">Powered by GPT-5.2</span>
            </div>

            {/* Headline */}
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6 animate-fade-in stagger-1">
              Cria Produtos Digitais
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-gray-300 to-gray-500">
                com Inteligência Artificial
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl md:text-2xl text-gray-400 mb-10 max-w-2xl animate-fade-in stagger-2">
              Gera eBooks, guias e cursos completos em minutos. 
              Cria landing pages de venda e começa a faturar hoje.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 animate-fade-in stagger-3">
              <Link to="/auth">
                <Button size="lg" className="bg-white text-black hover:bg-gray-200 h-14 px-8 text-lg" data-testid="hero-cta-btn">
                  Começar Grátis
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="h-14 px-8 text-lg border-white/20 hover:bg-white/5">
                <Play className="w-5 h-5 mr-2" />
                Ver Demo
              </Button>
            </div>

            {/* Social Proof */}
            <div className="flex items-center gap-6 mt-12 animate-fade-in stagger-4">
              <div className="flex -space-x-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 border-2 border-[#050505]"
                    style={{ animationDelay: `${i * 0.1}s` }}
                  />
                ))}
              </div>
              <div>
                <div className="flex items-center gap-1 mb-1">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Star key={i} className="w-4 h-4 fill-yellow-500 text-yellow-500" />
                  ))}
                </div>
                <p className="text-sm text-gray-400">
                  <span className="text-white font-medium">+2,847</span> produtos criados este mês
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="section-spacing">
        <div className="container-marketing">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Tudo o que Precisas</h2>
            <p className="text-xl text-gray-400">Uma plataforma completa para criar e vender produtos digitais</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className="card-marketing animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
                data-testid={`feature-card-${index}`}
              >
                <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-400">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="section-spacing bg-[#0A0A0A]/50">
        <div className="container-marketing">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Como Funciona</h2>
            <p className="text-xl text-gray-400">De ideia a produto em 4 passos simples</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="relative animate-fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-8 left-full w-full h-px bg-gradient-to-r from-white/20 to-transparent" />
                )}
                <div className="text-6xl font-bold text-white/10 mb-4">{step.number}</div>
                <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                <p className="text-gray-400">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="section-spacing">
        <div className="container-marketing">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Preços Simples</h2>
            <p className="text-xl text-gray-400">Começa grátis e escala conforme cresces</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {plans.map((plan, index) => (
              <div
                key={index}
                className={`relative p-8 rounded-xl border ${
                  plan.popular
                    ? "bg-white/5 border-white/20"
                    : "bg-[#0A0A0A] border-white/10"
                } animate-fade-in`}
                style={{ animationDelay: `${index * 0.1}s` }}
                data-testid={`pricing-card-${plan.name.toLowerCase()}`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-white text-black text-sm font-medium rounded-full">
                    Mais Popular
                  </div>
                )}
                <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold">€{plan.price}</span>
                  <span className="text-gray-400">/mês</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-3 text-gray-300">
                      <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link to="/auth">
                  <Button
                    className={`w-full h-12 ${
                      plan.popular
                        ? "bg-white text-black hover:bg-gray-200"
                        : "bg-white/10 hover:bg-white/20"
                    }`}
                  >
                    Começar com {plan.name}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section-spacing">
        <div className="container-marketing">
          <div className="relative p-12 md:p-16 rounded-2xl bg-gradient-to-br from-white/5 to-transparent border border-white/10 overflow-hidden">
            <div className="absolute inset-0 gradient-glow opacity-30" />
            <div className="relative z-10 text-center">
              <h2 className="text-4xl md:text-5xl font-bold mb-4">
                Pronto para Começar?
              </h2>
              <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
                Junta-te a milhares de criadores que já estão a monetizar com produtos digitais gerados por IA.
              </p>
              <Link to="/auth">
                <Button size="lg" className="bg-white text-black hover:bg-gray-200 h-14 px-10 text-lg" data-testid="final-cta-btn">
                  Criar Conta Grátis
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/10">
        <div className="container-marketing">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center">
                <Zap className="w-4 h-4 text-black" />
              </div>
              <span className="font-bold">DigiForge</span>
            </div>
            <p className="text-gray-500 text-sm">
              © 2026 DigiForge. Todos os direitos reservados.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
