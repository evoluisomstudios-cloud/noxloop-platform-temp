import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const HomePage = ({ user }) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                NOXLOOP
              </span>
            </div>
            <div className="flex items-center gap-4">
              {user ? (
                <Button onClick={() => navigate('/dashboard')} data-testid="dashboard-btn">
                  Dashboard
                </Button>
              ) : (
                <>
                  <Button variant="ghost" onClick={() => navigate('/auth')} data-testid="login-btn">
                    Entrar
                  </Button>
                  <Button onClick={() => navigate('/auth')} data-testid="signup-btn">
                    Criar conta
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight" data-testid="hero-headline">
              Cria páginas e ativos digitais<br />
              que geram <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">clientes e vendas</span> — com IA
            </h1>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto" data-testid="hero-subheadline">
              Compra soluções prontas ou cria do zero com IA usando créditos. Tudo num só lugar.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button size="lg" onClick={() => navigate('/auth')} className="text-lg px-8 py-6" data-testid="primary-cta">
              Criar conta
            </Button>
            <Button size="lg" variant="outline" onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })} className="text-lg px-8 py-6" data-testid="secondary-cta">
              Ver como funciona
            </Button>
          </div>
          <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
            <Badge variant="secondary" className="bg-green-100 text-green-700">+2,847 produtos criados este mês</Badge>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16" data-testid="features-section">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Tudo o que Precisas</h2>
          <p className="text-slate-600">Uma plataforma completa para criar e vender produtos digitais</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Geração com IA</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Cria eBooks, guias e cursos completos em minutos com tecnologia avançada</CardDescription>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Pagamentos Integrados</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Stripe configurado para receber pagamentos de forma automática</CardDescription>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Analytics em Tempo Real</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Acompanha vendas, conversões e métricas de performance</CardDescription>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Entrega Automática</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>Os clientes recebem acesso instantâneo após a compra</CardDescription>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="bg-slate-50 py-16" data-testid="how-it-works-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Como Funciona</h2>
            <p className="text-slate-600">De ideia a produto em 4 passos simples</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { num: '01', title: 'Define o Tópico', desc: 'Escolhe o tema e público-alvo do teu produto' },
              { num: '02', title: 'A IA Gera', desc: 'A tecnologia cria conteúdo profissional completo' },
              { num: '03', title: 'Personaliza', desc: 'Ajusta o preço e landing page de venda' },
              { num: '04', title: 'Vende', desc: 'Partilha o link e começa a faturar' }
            ].map((step) => (
              <div key={step.num} className="text-center space-y-4">
                <div className="text-5xl font-bold text-blue-600/20">{step.num}</div>
                <h3 className="text-xl font-semibold">{step.title}</h3>
                <p className="text-slate-600">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16" data-testid="pricing-section">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Preços Simples</h2>
          <p className="text-slate-600">Começa grátis e escala conforme cresces</p>
        </div>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {[
            {
              name: 'Starter',
              price: '€9.99',
              period: '/mês',
              features: ['50 gerações de produto', 'Landing pages ilimitadas', 'Pagamentos Stripe', 'Analytics básico'],
              popular: false
            },
            {
              name: 'Pro',
              price: '€29.99',
              period: '/mês',
              features: ['200 gerações de produto', 'Tudo do Starter', 'Prioridade na geração', 'Suporte prioritário'],
              popular: true
            },
            {
              name: 'Enterprise',
              price: '€99.99',
              period: '/mês',
              features: ['1000 gerações de produto', 'Tudo do Pro', 'API access', 'White-label'],
              popular: false
            }
          ].map((plan) => (
            <Card key={plan.name} className={plan.popular ? 'border-2 border-blue-600 relative' : ''}>
              {plan.popular && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600">Mais Popular</Badge>
              )}
              <CardHeader>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <div className="text-4xl font-bold">
                  {plan.price}
                  <span className="text-base font-normal text-slate-600">{plan.period}</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <ul className="space-y-2">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-center gap-2">
                      <span className="text-green-600">✓</span>
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button 
                  className="w-full" 
                  variant={plan.popular ? 'default' : 'outline'}
                  onClick={() => navigate('/auth')}
                  data-testid={`pricing-${plan.name.toLowerCase()}-btn`}
                >
                  Começar com {plan.name}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <h2 className="text-4xl font-bold">Pronto para Começar?</h2>
          <p className="text-xl text-blue-100">
            Junta-te a milhares de criadores que já estão a monetizar com produtos digitais gerados por IA.
          </p>
          <Button 
            size="lg" 
            className="bg-white text-blue-600 hover:bg-slate-100 text-lg px-8 py-6"
            onClick={() => navigate('/auth')}
            data-testid="final-cta"
          >
            Criar Conta Grátis
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-slate-600">
          <p>© 2025 NOXLOOP. Todos os direitos reservados.</p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
