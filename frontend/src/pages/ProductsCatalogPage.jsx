import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ProductsCatalogPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchProducts();
  }, [filter]);

  const fetchProducts = async () => {
    try {
      const url = filter === 'all' 
        ? `${API}/public/products`
        : `${API}/public/products?product_type=${filter}`;
      
      const response = await fetch(url);
      const data = await response.json();
      setProducts(data.products || []);
    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setLoading(false);
    }
  };

  const productTypes = [
    { value: 'all', label: 'Todos' },
    { value: 'ebook', label: 'eBooks' },
    { value: 'course', label: 'Cursos' },
    { value: 'guide', label: 'Guias' },
    { value: 'template', label: 'Templates' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center">
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                NOXLOOP
              </span>
            </Link>
            <div className="flex items-center gap-4">
              <Link to="/auth">
                <Button variant="ghost">Entrar</Button>
              </Link>
              <Link to="/auth">
                <Button>Criar conta</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4">
            Produtos Digitais <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Prontos a Usar</span>
          </h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Soluções profissionais criadas com IA para acelerar o teu negócio
          </p>
        </div>

        {/* Filters */}
        <div className="flex justify-center gap-2 mb-8 flex-wrap">
          {productTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => setFilter(type.value)}
              className={`px-4 py-2 rounded-full transition-all ${
                filter === type.value
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-white text-slate-700 hover:bg-slate-100 border'
              }`}
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Products Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="spinner mx-auto mb-4" />
              <p className="text-slate-600">A carregar produtos...</p>
            </div>
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-xl text-slate-600">Nenhum produto encontrado</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <Card key={product.product_id} className="flex flex-col hover:shadow-xl transition-all">
                <CardHeader>
                  <div className="flex justify-between items-start mb-2">
                    <Badge variant="secondary">{product.product_type}</Badge>
                    {product.views > 0 && (
                      <span className="text-sm text-slate-500">{product.views} visualizações</span>
                    )}
                  </div>
                  <CardTitle className="text-xl">{product.title}</CardTitle>
                  <CardDescription>{product.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col justify-between">
                  <div className="mb-4">
                    {product.downloads > 0 && (
                      <p className="text-sm text-green-600 font-medium">
                        ✓ {product.downloads} pessoas já compraram
                      </p>
                    )}
                  </div>
                  <div className="space-y-3">
                    <div className="text-3xl font-bold text-blue-600">
                      €{product.price.toFixed(2)}
                    </div>
                    <Link to={`/p/${product.slug}`} className="block">
                      <Button className="w-full" size="lg">
                        Ver Detalhes
                      </Button>
                    </Link>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="border-t bg-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-slate-600">
            <p className="mb-2">© 2025 NOXLOOP. Todos os direitos reservados.</p>
            <div className="flex justify-center gap-6 mt-4">
              <Link to="/" className="hover:text-blue-600">Início</Link>
              <Link to="/produtos" className="hover:text-blue-600">Produtos</Link>
              <Link to="/auth" className="hover:text-blue-600">Criar Conta</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ProductsCatalogPage;
