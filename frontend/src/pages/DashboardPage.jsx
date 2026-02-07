import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { DashboardLayout } from "../components/DashboardLayout";
import { Button } from "../components/ui/button";
import { 
  Plus, 
  TrendingUp, 
  DollarSign, 
  Package, 
  Eye,
  ArrowUpRight,
  Sparkles
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const DashboardPage = ({ user, onLogout }) => {
  const [analytics, setAnalytics] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsRes, productsRes] = await Promise.all([
          fetch(`${API}/analytics`, { credentials: "include" }),
          fetch(`${API}/products`, { credentials: "include" }),
        ]);

        if (analyticsRes.ok) {
          setAnalytics(await analyticsRes.json());
        }
        if (productsRes.ok) {
          setProducts(await productsRes.json());
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const stats = [
    {
      label: "Receita Total",
      value: analytics ? `€${analytics.total_revenue.toFixed(2)}` : "€0.00",
      icon: DollarSign,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
    },
    {
      label: "Vendas",
      value: analytics?.total_sales || 0,
      icon: TrendingUp,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "Produtos",
      value: analytics?.total_products || 0,
      icon: Package,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
    },
    {
      label: "Visualizações",
      value: analytics?.total_views || 0,
      icon: Eye,
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
    },
  ];

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-8" data-testid="dashboard-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-1">
              Olá, {user?.name?.split(" ")[0] || "Utilizador"}
            </h1>
            <p className="text-gray-400">
              Bem-vindo ao teu painel de controlo
            </p>
          </div>
          <Link to="/products/new">
            <Button className="bg-white text-black hover:bg-gray-200" data-testid="create-product-btn">
              <Plus className="w-4 h-4 mr-2" />
              Criar Produto
            </Button>
          </Link>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="card-dashboard"
              data-testid={`stat-card-${index}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <ArrowUpRight className="w-4 h-4 text-gray-500" />
              </div>
              <p className="text-2xl font-bold mb-1">
                {loading ? (
                  <span className="inline-block w-16 h-6 loading-shimmer rounded" />
                ) : (
                  stat.value
                )}
              </p>
              <p className="text-sm text-gray-400">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Credits Banner */}
        <div className="card-dashboard bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border-indigo-500/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/20 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <p className="font-medium">Créditos de Geração</p>
                <p className="text-sm text-gray-400">
                  {user?.credits || 0} créditos disponíveis
                </p>
              </div>
            </div>
            <Link to="/settings">
              <Button variant="outline" className="border-indigo-500/30 hover:bg-indigo-500/10">
                Obter Mais
              </Button>
            </Link>
          </div>
        </div>

        {/* Recent Products */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Produtos Recentes</h2>
            <Link to="/products" className="text-gray-400 hover:text-white text-sm">
              Ver todos
            </Link>
          </div>

          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="card-dashboard">
                  <div className="h-4 w-3/4 loading-shimmer rounded mb-3" />
                  <div className="h-3 w-full loading-shimmer rounded mb-2" />
                  <div className="h-3 w-2/3 loading-shimmer rounded" />
                </div>
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="card-dashboard text-center py-12">
              <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
                <Package className="w-8 h-8 text-gray-500" />
              </div>
              <h3 className="text-lg font-medium mb-2">Nenhum produto ainda</h3>
              <p className="text-gray-400 mb-6">
                Cria o teu primeiro produto digital com IA
              </p>
              <Link to="/products/new">
                <Button className="bg-white text-black hover:bg-gray-200">
                  <Plus className="w-4 h-4 mr-2" />
                  Criar Primeiro Produto
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {products.slice(0, 6).map((product) => (
                <Link
                  key={product.product_id}
                  to={`/products/${product.product_id}`}
                  className="card-dashboard hover:border-white/20 transition-colors group"
                  data-testid={`product-card-${product.product_id}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      product.is_published 
                        ? "bg-green-500/20 text-green-400" 
                        : "bg-gray-500/20 text-gray-400"
                    }`}>
                      {product.is_published ? "Publicado" : "Rascunho"}
                    </span>
                    <span className="text-sm text-gray-400">
                      {product.product_type}
                    </span>
                  </div>
                  <h3 className="font-semibold mb-2 group-hover:text-white transition-colors">
                    {product.title}
                  </h3>
                  <p className="text-sm text-gray-400 line-clamp-2 mb-4">
                    {product.description}
                  </p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">
                      {product.downloads} vendas
                    </span>
                    <span className="font-medium text-green-400">
                      €{product.revenue.toFixed(2)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-4">
          <Link to="/products/new" className="card-dashboard hover:border-white/20 transition-colors group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center group-hover:bg-white/20 transition-colors">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold group-hover:text-white transition-colors">
                  Gerar Novo Produto
                </h3>
                <p className="text-sm text-gray-400">
                  Usa IA para criar conteúdo em minutos
                </p>
              </div>
            </div>
          </Link>
          <Link to="/analytics" className="card-dashboard hover:border-white/20 transition-colors group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center group-hover:bg-white/20 transition-colors">
                <TrendingUp className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold group-hover:text-white transition-colors">
                  Ver Analytics
                </h3>
                <p className="text-sm text-gray-400">
                  Acompanha o desempenho das vendas
                </p>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </DashboardLayout>
  );
};
