import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = ({ user, onLogout, setUser }) => {
  const [products, setProducts] = useState([]);
  const [generations, setGenerations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [aiPrompt, setAiPrompt] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');

  useEffect(() => {
    loadProducts();
    loadGenerations();
  }, []);

  const loadProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
    } catch (err) {
      console.error('Error loading products:', err);
    }
  };

  const loadGenerations = async () => {
    try {
      const response = await axios.get(`${API}/ai/generations`);
      setGenerations(response.data);
    } catch (err) {
      console.error('Error loading generations:', err);
    }
  };

  const refreshUserData = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (err) {
      console.error('Error refreshing user:', err);
    }
  };

  const handleAIGeneration = async () => {
    if (!aiPrompt.trim()) {
      setError('Por favor, insere uma descrição do que queres criar');
      return;
    }

    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await axios.post(`${API}/ai/generate`, {
        prompt: aiPrompt,
        template: selectedTemplate
      });
      setSuccess(`Conteúdo gerado com sucesso! Créditos usados: ${response.data.credits_used}`);
      setAiPrompt('');
      setSelectedTemplate('');
      await refreshUserData();
      await loadGenerations();
    } catch (err) {
      if (err.response?.status === 402) {
        setError('Créditos insuficientes. Por favor, adquire mais créditos.');
      } else {
        setError(err.response?.data?.detail || 'Erro ao gerar conteúdo');
      }
    } finally {
      setLoading(false);
    }
  };

  const templates = [
    { id: 'landing', name: 'Página de captação', prompt: 'Landing page profissional para captar leads com formulário' },
    { id: 'ebook', name: 'eBook + página de vendas', prompt: 'eBook completo com landing page de vendas otimizada' },
    { id: 'funnel', name: 'Mini-funil', prompt: 'Funil completo com landing page + obrigado + emails' }
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                NOXLOOP
              </span>
              <span className="text-slate-600">Olá, {user.name}</span>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="secondary" className="text-lg px-4 py-2" data-testid="credits-display">
                <span className="font-semibold">{user.credits}</span> créditos
              </Badge>
              <Button variant="outline" onClick={onLogout} data-testid="logout-btn">
                Sair
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="products" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 max-w-md">
            <TabsTrigger value="products" data-testid="products-tab">Produtos</TabsTrigger>
            <TabsTrigger value="ai-create" data-testid="ai-create-tab">Criar com IA</TabsTrigger>
          </TabsList>

          {/* Products Tab */}
          <TabsContent value="products" className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold mb-2">Produtos Prontos</h2>
              <p className="text-slate-600">Soluções profissionais prontas a usar</p>
            </div>

            {products.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-slate-500">
                  A carregar produtos...
                </CardContent>
              </Card>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map((product) => (
                  <Card key={product.id} className="flex flex-col" data-testid={`product-${product.id}`}>
                    <CardHeader>
                      <CardTitle>{product.name}</CardTitle>
                      <CardDescription>{product.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1 flex flex-col justify-between">
                      <div className="space-y-4 mb-4">
                        <div>
                          <h4 className="font-semibold mb-2">Inclui:</h4>
                          <ul className="space-y-1">
                            {product.deliverables.map((item, idx) => (
                              <li key={idx} className="text-sm text-slate-600 flex items-start gap-2">
                                <span className="text-green-600 mt-0.5">✓</span>
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="text-3xl font-bold">€{product.price.toFixed(2)}</div>
                        <Button className="w-full" data-testid={`buy-product-${product.id}`}>
                          Comprar Agora
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* AI Create Tab */}
          <TabsContent value="ai-create" className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold mb-2">Criar com IA</h2>
              <p className="text-slate-600">Usa créditos para gerar conteúdo personalizado</p>
            </div>

            <Card data-testid="ai-generation-card">
              <CardHeader>
                <CardTitle>Geração Personalizada</CardTitle>
                <CardDescription>
                  Descreve o que queres criar ou escolhe um template. Custo: 5 créditos por geração
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Templates */}
                <div>
                  <h4 className="font-semibold mb-3">Templates Rápidos:</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {templates.map((template) => (
                      <Button
                        key={template.id}
                        variant={selectedTemplate === template.id ? 'default' : 'outline'}
                        onClick={() => {
                          setSelectedTemplate(template.id);
                          setAiPrompt(template.prompt);
                        }}
                        className="h-auto py-4"
                        data-testid={`template-${template.id}`}
                      >
                        {template.name}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Custom Prompt */}
                <div>
                  <h4 className="font-semibold mb-2">Ou descreve o que queres:</h4>
                  <Textarea
                    placeholder="Ex: Cria um eBook sobre marketing digital para pequenas empresas com 10 capítulos..."
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    rows={4}
                    data-testid="ai-prompt-input"
                  />
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {success && (
                  <Alert className="bg-green-50 text-green-900 border-green-200">
                    <AlertDescription>{success}</AlertDescription>
                  </Alert>
                )}

                <div className="flex items-center justify-between pt-4">
                  <div className="text-sm text-slate-600">
                    Créditos disponíveis: <span className="font-semibold">{user.credits}</span>
                  </div>
                  <Button 
                    onClick={handleAIGeneration}
                    disabled={loading || user.credits < 5}
                    size="lg"
                    data-testid="generate-btn"
                  >
                    {loading ? 'A gerar...' : user.credits < 5 ? 'Créditos insuficientes' : 'Gerar (5 créditos)'}
                  </Button>
                </div>

                {user.credits < 5 && (
                  <Alert>
                    <AlertDescription>
                      Não tens créditos suficientes. <a href="#" className="font-semibold underline">Adquire mais créditos</a>
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Previous Generations */}
            {generations.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-xl font-semibold">Gerações Anteriores</h3>
                <div className="space-y-3">
                  {generations.slice(0, 5).map((gen) => (
                    <Card key={gen.id} data-testid={`generation-${gen.id}`}>
                      <CardContent className="py-4">
                        <div className="flex justify-between items-start mb-2">
                          <Badge variant="secondary">ID: {gen.id.slice(0, 8)}</Badge>
                          <span className="text-sm text-slate-500">
                            {new Date(gen.created_at).toLocaleDateString('pt-PT')}
                          </span>
                        </div>
                        <p className="text-sm text-slate-700 whitespace-pre-wrap">{gen.content}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Dashboard;
