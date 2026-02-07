import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Download, Package } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AdminPromoPage = ({ user }) => {
  const [products, setProducts] = useState([]);
  const [assets, setAssets] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedAssets, setSelectedAssets] = useState([]);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load workspace products
      const userRes = await fetch(`${API}/auth/me`, { credentials: 'include' });
      const userData = await userRes.json();
      const workspaceId = userData.workspaces[0]?.workspace_id;

      if (workspaceId) {
        const productsRes = await fetch(`${API}/workspaces/${workspaceId}/products`, {
          credentials: 'include',
        });
        if (productsRes.ok) {
          const productsData = await productsRes.json();
          setProducts(productsData.filter(p => p.is_published));
        }
      }

      // Load media assets
      const assetsRes = await fetch(`${API}/admin/media`, { credentials: 'include' });
      if (assetsRes.ok) {
        const assetsData = await assetsRes.json();
        setAssets(assetsData.assets || []);
      }
    } catch (error) {
      toast.error('Erro ao carregar dados');
    }
  };

  const toggleAsset = (assetId) => {
    setSelectedAssets((prev) =>
      prev.includes(assetId)
        ? prev.filter((id) => id !== assetId)
        : [...prev, assetId]
    );
  };

  const generatePack = () => {
    if (!selectedProduct) {
      toast.error('Seleciona um produto');
      return;
    }

    setGenerating(true);

    try {
      // Generate promo pack JSON
      const pack = {
        pack_id: `pack_${Date.now()}`,
        product: {
          id: selectedProduct.product_id,
          title: selectedProduct.title,
          description: selectedProduct.description,
          price: selectedProduct.price,
          public_url: selectedProduct.public_url,
          buy_url: `${window.location.origin}${selectedProduct.public_url}`,
        },
        assets: selectedAssets.map((assetId) => {
          const asset = assets.find((a) => a.asset_id === assetId);
          return {
            id: asset.asset_id,
            filename: asset.original_filename,
            type: asset.type,
            download_url: `${API}/media/${asset.asset_id}`,
          };
        }),
        generated_at: new Date().toISOString(),
      };

      // Download as JSON
      const blob = new Blob([JSON.stringify(pack, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `promo-pack-${selectedProduct.product_id}.json`;
      link.click();
      URL.revokeObjectURL(url);

      toast.success('Promo Pack gerado!');
    } catch (error) {
      toast.error('Erro ao gerar pack');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-promo-page">
      <div>
        <h1 className="text-3xl font-bold mb-2">Promo Packs</h1>
        <p className="text-gray-400">Criar pacotes promocionais com produto + assets</p>
      </div>

      {/* Product Selection */}
      <Card>
        <CardHeader>
          <CardTitle>1. Selecionar Produto</CardTitle>
        </CardHeader>
        <CardContent>
          <Select onValueChange={(value) => setSelectedProduct(products.find(p => p.product_id === value))}>
            <SelectTrigger data-testid="product-select">
              <SelectValue placeholder="Escolher produto publicado..." />
            </SelectTrigger>
            <SelectContent>
              {products.map((product) => (
                <SelectItem key={product.product_id} value={product.product_id}>
                  {product.title} - €{product.price}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {selectedProduct && (
            <div className="mt-4 p-4 rounded-lg bg-white/5 border border-[#262626]">
              <h4 className="font-semibold mb-2">{selectedProduct.title}</h4>
              <p className="text-sm text-gray-400 mb-2">{selectedProduct.description}</p>
              <div className="flex gap-2">
                <Badge>{selectedProduct.product_type}</Badge>
                <Badge variant="outline">€{selectedProduct.price}</Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Assets Selection */}
      <Card>
        <CardHeader>
          <CardTitle>2. Selecionar Assets</CardTitle>
          <CardDescription>{selectedAssets.length} assets selecionados</CardDescription>
        </CardHeader>
        <CardContent>
          {assets.length === 0 ? (
            <Alert>
              <AlertDescription>
                Nenhum asset disponível. Faz upload primeiro em Media.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {assets.map((asset) => {
                const isSelected = selectedAssets.includes(asset.asset_id);
                return (
                  <div
                    key={asset.asset_id}
                    onClick={() => toggleAsset(asset.asset_id)}
                    className={`cursor-pointer p-3 rounded-lg border transition-all ${
                      isSelected
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-[#262626] hover:border-gray-600'
                    }`}
                    data-testid={`asset-checkbox-${asset.asset_id}`}
                  >
                    <div className="aspect-square bg-slate-800 rounded mb-2 flex items-center justify-center overflow-hidden">
                      {asset.type === 'image' ? (
                        <img
                          src={`${API}/media/${asset.asset_id}`}
                          alt={asset.original_filename}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="text-gray-500">
                          {asset.type === 'video' ? <Video className="w-8 h-8" /> : <FileText className="w-8 h-8" />}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Checkbox checked={isSelected} />
                      <p className="text-xs truncate flex-1">{asset.original_filename}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generate Pack */}
      <Card>
        <CardHeader>
          <CardTitle>3. Gerar Promo Pack</CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            onClick={generatePack}
            disabled={!selectedProduct || selectedAssets.length === 0 || generating}
            className="w-full"
            size="lg"
            data-testid="generate-pack-btn"
          >
            <Package className="w-4 h-4 mr-2" />
            {generating ? 'A gerar...' : 'Gerar Pack (JSON)'}
          </Button>
          
          {selectedProduct && selectedAssets.length > 0 && (
            <Alert className="mt-4">
              <AlertDescription>
                O pack vai incluir: <strong>{selectedProduct.title}</strong> + {selectedAssets.length} asset(s)
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminPromoPage;
