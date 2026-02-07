import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { DashboardLayout } from "../components/DashboardLayout";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { 
  Plus, 
  Search, 
  Package,
  ExternalLink,
  MoreVertical,
  Trash2,
  Edit
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const ProductsPage = ({ user, onLogout }) => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API}/products`, {
        credentials: "include",
      });
      if (response.ok) {
        setProducts(await response.json());
      }
    } catch (error) {
      console.error("Error fetching products:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (productId) => {
    if (!window.confirm("Tens a certeza que queres eliminar este produto?")) {
      return;
    }

    try {
      const response = await fetch(`${API}/products/${productId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (response.ok) {
        setProducts(products.filter((p) => p.product_id !== productId));
        toast.success("Produto eliminado com sucesso");
      } else {
        toast.error("Erro ao eliminar produto");
      }
    } catch (error) {
      toast.error("Erro de conexão");
    }
  };

  const filteredProducts = products.filter((product) => {
    const matchesSearch = product.title
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesFilter =
      filter === "all" ||
      (filter === "published" && product.is_published) ||
      (filter === "draft" && !product.is_published);
    return matchesSearch && matchesFilter;
  });

  const productTypes = {
    ebook: "eBook",
    guide: "Guia",
    course: "Curso",
    template: "Template",
  };

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-6" data-testid="products-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-1">Produtos</h1>
            <p className="text-gray-400">
              Gere e vende os teus produtos digitais
            </p>
          </div>
          <Link to="/products/new">
            <Button className="bg-white text-black hover:bg-gray-200" data-testid="create-product-btn">
              <Plus className="w-4 h-4 mr-2" />
              Criar Produto
            </Button>
          </Link>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <Input
              placeholder="Pesquisar produtos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-[#171717] border-[#262626]"
              data-testid="search-input"
            />
          </div>
          <div className="flex gap-2">
            {["all", "published", "draft"].map((f) => (
              <Button
                key={f}
                variant={filter === f ? "default" : "outline"}
                onClick={() => setFilter(f)}
                className={filter === f ? "bg-white text-black" : "border-[#262626]"}
                data-testid={`filter-${f}`}
              >
                {f === "all" ? "Todos" : f === "published" ? "Publicados" : "Rascunhos"}
              </Button>
            ))}
          </div>
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="card-dashboard">
                <div className="h-4 w-3/4 loading-shimmer rounded mb-3" />
                <div className="h-3 w-full loading-shimmer rounded mb-2" />
                <div className="h-3 w-2/3 loading-shimmer rounded" />
              </div>
            ))}
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="card-dashboard text-center py-16">
            <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
              <Package className="w-8 h-8 text-gray-500" />
            </div>
            <h3 className="text-lg font-medium mb-2">
              {searchQuery ? "Nenhum resultado" : "Nenhum produto ainda"}
            </h3>
            <p className="text-gray-400 mb-6">
              {searchQuery
                ? "Tenta uma pesquisa diferente"
                : "Cria o teu primeiro produto digital com IA"}
            </p>
            {!searchQuery && (
              <Link to="/products/new">
                <Button className="bg-white text-black hover:bg-gray-200">
                  <Plus className="w-4 h-4 mr-2" />
                  Criar Primeiro Produto
                </Button>
              </Link>
            )}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProducts.map((product) => (
              <div
                key={product.product_id}
                className="card-dashboard group relative"
                data-testid={`product-item-${product.product_id}`}
              >
                {/* Actions Menu */}
                <div className="absolute top-4 right-4">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="w-8 h-8 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-[#171717] border-[#262626]">
                      <DropdownMenuItem asChild>
                        <Link to={`/products/${product.product_id}`} className="flex items-center">
                          <Edit className="w-4 h-4 mr-2" />
                          Editar
                        </Link>
                      </DropdownMenuItem>
                      {product.is_published && (
                        <DropdownMenuItem asChild>
                          <a
                            href={`/p/${product.product_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center"
                          >
                            <ExternalLink className="w-4 h-4 mr-2" />
                            Ver Página
                          </a>
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem
                        onClick={() => handleDelete(product.product_id)}
                        className="text-red-400 focus:text-red-400"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Eliminar
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <Link to={`/products/${product.product_id}`}>
                  {/* Status & Type */}
                  <div className="flex items-start justify-between mb-3 pr-8">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        product.is_published
                          ? "bg-green-500/20 text-green-400"
                          : "bg-gray-500/20 text-gray-400"
                      }`}
                    >
                      {product.is_published ? "Publicado" : "Rascunho"}
                    </span>
                    <span className="text-sm text-gray-400">
                      {productTypes[product.product_type] || product.product_type}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <h3 className="font-semibold mb-2 group-hover:text-white transition-colors">
                    {product.title}
                  </h3>
                  <p className="text-sm text-gray-400 line-clamp-2 mb-4">
                    {product.description}
                  </p>

                  {/* Stats */}
                  <div className="flex items-center justify-between pt-4 border-t border-[#262626]">
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-gray-400">
                        {product.downloads} vendas
                      </span>
                      <span className="text-gray-400">
                        {product.views || 0} views
                      </span>
                    </div>
                    <div className="text-right">
                      {product.price > 0 ? (
                        <span className="font-semibold text-green-400">
                          €{product.price.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-gray-500 text-sm">Sem preço</span>
                      )}
                    </div>
                  </div>
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
