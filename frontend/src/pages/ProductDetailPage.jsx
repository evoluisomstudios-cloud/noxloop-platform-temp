import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { DashboardLayout } from "../components/DashboardLayout";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { 
  ArrowLeft,
  Save,
  ExternalLink,
  Copy,
  Eye,
  FileText,
  Sparkles,
  Loader2,
  CheckCircle,
  Image as ImageIcon,
  X
} from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const ProductDetailPage = ({ user, onLogout }) => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generatingLanding, setGeneratingLanding] = useState(false);
  const [editedProduct, setEditedProduct] = useState(null);
  const [mediaAssets, setMediaAssets] = useState([]);
  const [loadingMedia, setLoadingMedia] = useState(false);

  useEffect(() => {
    fetchProduct();
    if (user?.is_admin) {
      fetchMediaAssets();
    }
  }, [productId, user]);

  const fetchProduct = async () => {
    try {
      const response = await fetch(`${API}/products/${productId}`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setProduct(data);
        setEditedProduct(data);
      } else {
        toast.error("Produto não encontrado");
        navigate("/products");
      }
    } catch (error) {
      console.error("Error fetching product:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMediaAssets = async () => {
    setLoadingMedia(true);
    try {
      const response = await fetch(`${API}/admin/media?type=image`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setMediaAssets(data.assets || []);
      }
    } catch (error) {
      console.error("Error fetching media:", error);
    } finally {
      setLoadingMedia(false);
    }
  };

  const toggleMediaAsset = (assetId) => {
    const current = editedProduct.media_asset_ids || [];
    const updated = current.includes(assetId)
      ? current.filter(id => id !== assetId)
      : [...current, assetId];
    setEditedProduct({ ...editedProduct, media_asset_ids: updated });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API}/products/${productId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          title: editedProduct.title,
          description: editedProduct.description,
          price: parseFloat(editedProduct.price) || 0,
          is_published: editedProduct.is_published,
          media_asset_ids: editedProduct.media_asset_ids || [],
        }),
      });

      if (response.ok) {
        const updated = await response.json();
        setProduct(updated);
        setEditedProduct(updated);
        toast.success("Produto guardado com sucesso");
      } else {
        toast.error("Erro ao guardar produto");
      }
    } catch (error) {
      toast.error("Erro de conexão");
    } finally {
      setSaving(false);
    }
  };

  const generateLandingPage = async () => {
    setGeneratingLanding(true);
    try {
      const response = await fetch(`${API}/products/${productId}/landing-page`, {
        method: "POST",
        credentials: "include",
      });

      if (response.ok) {
        const landingData = await response.json();
        setProduct({ ...product, landing_page: landingData });
        setEditedProduct({ ...editedProduct, landing_page: landingData });
        toast.success("Landing page gerada com sucesso!");
      } else {
        toast.error("Erro ao gerar landing page");
      }
    } catch (error) {
      toast.error("Erro de conexão");
    } finally {
      setGeneratingLanding(false);
    }
  };

  const copyProductLink = () => {
    const url = `${window.location.origin}/p/${productId}`;
    navigator.clipboard.writeText(url);
    toast.success("Link copiado!");
  };

  if (loading) {
    return (
      <DashboardLayout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-[60vh]">
          <div className="spinner" />
        </div>
      </DashboardLayout>
    );
  }

  if (!product) {
    return null;
  }

  const productLink = `${window.location.origin}/p/${productId}`;

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-6" data-testid="product-detail-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate("/products")}
              className="p-2"
              data-testid="back-btn"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">{product.title}</h1>
              <div className="flex items-center gap-3 mt-1">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  product.is_published
                    ? "bg-green-500/20 text-green-400"
                    : "bg-gray-500/20 text-gray-400"
                }`}>
                  {product.is_published ? "Publicado" : "Rascunho"}
                </span>
                <span className="text-sm text-gray-400">
                  {product.downloads} vendas · €{product.revenue.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {product.is_published && (
              <>
                <Button
                  variant="outline"
                  onClick={copyProductLink}
                  className="border-[#262626]"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copiar Link
                </Button>
                <a href={productLink} target="_blank" rel="noopener noreferrer">
                  <Button variant="outline" className="border-[#262626]">
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Ver Página
                  </Button>
                </a>
              </>
            )}
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-white text-black hover:bg-gray-200"
              data-testid="save-btn"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Save className="w-4 h-4 mr-2" />
              )}
              Guardar
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="details" className="space-y-6">
          <TabsList className="bg-[#0A0A0A] border border-[#262626]">
            <TabsTrigger value="details" data-testid="tab-details">Detalhes</TabsTrigger>
            <TabsTrigger value="content" data-testid="tab-content">Conteúdo</TabsTrigger>
            {user?.is_admin && <TabsTrigger value="media" data-testid="tab-media">Media</TabsTrigger>}
            <TabsTrigger value="landing" data-testid="tab-landing">Landing Page</TabsTrigger>
          </TabsList>

          {/* Details Tab */}
          <TabsContent value="details" className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="card-dashboard space-y-4">
                <h3 className="font-semibold">Informações Básicas</h3>
                
                <div>
                  <Label className="text-gray-400 mb-2 block">Título</Label>
                  <Input
                    value={editedProduct.title}
                    onChange={(e) => setEditedProduct({ ...editedProduct, title: e.target.value })}
                    className="bg-[#171717] border-[#262626]"
                    data-testid="edit-title"
                  />
                </div>

                <div>
                  <Label className="text-gray-400 mb-2 block">Descrição</Label>
                  <Textarea
                    value={editedProduct.description}
                    onChange={(e) => setEditedProduct({ ...editedProduct, description: e.target.value })}
                    className="min-h-[100px] bg-[#171717] border-[#262626]"
                    data-testid="edit-description"
                  />
                </div>

                <div>
                  <Label className="text-gray-400 mb-2 block">Preço (€)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    min="0"
                    value={editedProduct.price}
                    onChange={(e) => setEditedProduct({ ...editedProduct, price: e.target.value })}
                    className="bg-[#171717] border-[#262626]"
                    data-testid="edit-price"
                  />
                </div>
              </div>

              <div className="card-dashboard space-y-4">
                <h3 className="font-semibold">Publicação</h3>
                
                <div className="flex items-center justify-between p-4 rounded-lg bg-white/5">
                  <div>
                    <p className="font-medium">Publicar Produto</p>
                    <p className="text-sm text-gray-400">
                      Torna o produto disponível para compra
                    </p>
                  </div>
                  <Switch
                    checked={editedProduct.is_published}
                    onCheckedChange={(checked) => 
                      setEditedProduct({ ...editedProduct, is_published: checked })
                    }
                    data-testid="publish-switch"
                  />
                </div>

                {editedProduct.is_published && (
                  <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-4 h-4 text-green-400" />
                      <span className="text-green-400 font-medium">Produto Publicado</span>
                    </div>
                    <p className="text-sm text-gray-400 mb-3">
                      O teu produto está disponível em:
                    </p>
                    <div className="flex items-center gap-2">
                      <Input
                        value={productLink}
                        readOnly
                        className="text-sm bg-[#171717] border-[#262626]"
                      />
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={copyProductLink}
                        className="border-[#262626]"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                )}

                {!editedProduct.is_published && editedProduct.price <= 0 && (
                  <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
                    <p className="text-sm text-yellow-400">
                      Define um preço antes de publicar o produto.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Content Tab */}
          <TabsContent value="content">
            <div className="card-dashboard">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Conteúdo Gerado
                </h3>
                <span className="text-sm text-gray-400">
                  Tipo: {product.product_type}
                </span>
              </div>
              <div className="markdown-content p-6 rounded-lg bg-[#171717] border border-[#262626] max-h-[600px] overflow-y-auto">
                <pre className="whitespace-pre-wrap font-sans text-gray-300">
                  {product.content}
                </pre>
              </div>
            </div>
          </TabsContent>

          {/* Media Tab - Admin Only */}
          {user?.is_admin && (
            <TabsContent value="media" className="space-y-6">
              <div className="card-dashboard">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <ImageIcon className="w-5 h-5" />
                  Imagens do Produto
                </h3>
                <p className="text-sm text-gray-400 mb-4">
                  Seleciona as imagens que aparecem na página pública. A primeira será a imagem principal.
                </p>

                {/* Selected Images Preview */}
                {(editedProduct.media_asset_ids?.length > 0) && (
                  <div className="mb-6">
                    <p className="text-sm text-gray-400 mb-2">Selecionadas ({editedProduct.media_asset_ids.length}):</p>
                    <div className="flex flex-wrap gap-2">
                      {editedProduct.media_asset_ids.map((assetId, idx) => {
                        const asset = mediaAssets.find(a => a.asset_id === assetId);
                        return (
                          <div key={assetId} className="relative group">
                            <img
                              src={`${API}/media/${assetId}`}
                              alt={asset?.original_filename || "Media"}
                              className="w-20 h-20 object-cover rounded border border-[#262626]"
                            />
                            {idx === 0 && (
                              <span className="absolute top-0 left-0 bg-green-500 text-black text-xs px-1 rounded-br">
                                Principal
                              </span>
                            )}
                            <button
                              onClick={() => toggleMediaAsset(assetId)}
                              className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <X className="w-3 h-3 text-white" />
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Available Media Grid */}
                {loadingMedia ? (
                  <div className="flex justify-center py-8">
                    <div className="spinner" />
                  </div>
                ) : mediaAssets.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">
                    Nenhuma imagem disponível. Faz upload em Admin → Media.
                  </p>
                ) : (
                  <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
                    {mediaAssets.map((asset) => {
                      const isSelected = editedProduct.media_asset_ids?.includes(asset.asset_id);
                      return (
                        <div
                          key={asset.asset_id}
                          onClick={() => toggleMediaAsset(asset.asset_id)}
                          className={`cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
                            isSelected
                              ? "border-blue-500 ring-2 ring-blue-500/30"
                              : "border-[#262626] hover:border-gray-500"
                          }`}
                          data-testid={`media-select-${asset.asset_id}`}
                        >
                          <img
                            src={`${API}/media/${asset.asset_id}`}
                            alt={asset.original_filename}
                            className="w-full aspect-square object-cover"
                          />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </TabsContent>
          )}

          {/* Landing Page Tab */}
          <TabsContent value="landing" className="space-y-6">
            {!product.landing_page ? (
              <div className="card-dashboard text-center py-12">
                <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
                  <Eye className="w-8 h-8 text-gray-500" />
                </div>
                <h3 className="text-lg font-medium mb-2">Sem Landing Page</h3>
                <p className="text-gray-400 mb-6">
                  Gera uma landing page de alta conversão com IA
                </p>
                <Button
                  onClick={generateLandingPage}
                  disabled={generatingLanding}
                  className="bg-white text-black hover:bg-gray-200"
                  data-testid="generate-landing-btn"
                >
                  {generatingLanding ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      A Gerar...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Gerar Landing Page
                    </>
                  )}
                </Button>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Preview da Landing Page</h3>
                  <Button
                    onClick={generateLandingPage}
                    disabled={generatingLanding}
                    variant="outline"
                    className="border-[#262626]"
                  >
                    {generatingLanding ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Sparkles className="w-4 h-4 mr-2" />
                    )}
                    Regenerar
                  </Button>
                </div>

                <div className="card-dashboard space-y-6">
                  <div>
                    <Label className="text-gray-400 text-sm">Headline</Label>
                    <p className="text-2xl font-bold mt-1">{product.landing_page.headline}</p>
                  </div>
                  
                  <div>
                    <Label className="text-gray-400 text-sm">Subheadline</Label>
                    <p className="text-gray-300 mt-1">{product.landing_page.subheadline}</p>
                  </div>

                  <div>
                    <Label className="text-gray-400 text-sm">Benefícios</Label>
                    <ul className="mt-2 space-y-2">
                      {product.landing_page.benefits?.map((benefit, i) => (
                        <li key={i} className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-green-400" />
                          <span>{benefit}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <Label className="text-gray-400 text-sm">CTA</Label>
                    <Button className="mt-2 bg-white text-black hover:bg-gray-200">
                      {product.landing_page.cta_text || "Comprar Agora"}
                    </Button>
                  </div>

                  <div>
                    <Label className="text-gray-400 text-sm">Garantia</Label>
                    <p className="text-gray-300 mt-1">{product.landing_page.guarantee}</p>
                  </div>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};
