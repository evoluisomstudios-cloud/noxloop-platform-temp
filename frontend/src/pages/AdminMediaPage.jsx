import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Trash2, Upload, Image as ImageIcon, Video, FileText } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AdminMediaPage = ({ user }) => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadAssets();
  }, [filter]);

  const loadAssets = async () => {
    try {
      const url = filter === 'all' 
        ? `${API}/admin/media`
        : `${API}/admin/media?type=${filter}`;
      
      const response = await fetch(url, { credentials: 'include' });
      
      if (response.ok) {
        const data = await response.json();
        setAssets(data.assets || []);
      }
    } catch (error) {
      toast.error('Erro ao carregar assets');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate size (50MB)
    if (file.size > 50 * 1024 * 1024) {
      toast.error('Ficheiro demasiado grande. Máximo: 50MB');
      return;
    }

    // Validate type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'video/mp4', 'video/webm', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Tipo de ficheiro não suportado. Usa: imagem, vídeo ou PDF');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API}/admin/media/upload`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });

      if (response.ok) {
        const asset = await response.json();
        toast.success('Upload concluído!');
        setAssets([asset, ...assets]);
        e.target.value = ''; // Reset input
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erro ao fazer upload');
      }
    } catch (error) {
      toast.error('Erro de conexão');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (assetId) => {
    if (!window.confirm('Apagar este asset permanentemente?')) return;

    try {
      const response = await fetch(`${API}/admin/media/${assetId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        toast.success('Asset apagado');
        setAssets(assets.filter((a) => a.asset_id !== assetId));
      } else {
        toast.error('Erro ao apagar asset');
      }
    } catch (error) {
      toast.error('Erro de conexão');
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'image': return <ImageIcon className="w-5 h-5" />;
      case 'video': return <Video className="w-5 h-5" />;
      case 'document': return <FileText className="w-5 h-5" />;
      default: return null;
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-6" data-testid="admin-media-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Media Assets</h1>
        <p className="text-gray-400">Gestão de imagens, vídeos e documentos</p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Novo Asset</CardTitle>
          <CardDescription>
            Tipos suportados: JPG, PNG, GIF, WebP, MP4, WebM, PDF | Máximo: 50MB
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <input
              type="file"
              accept="image/*,video/*,application/pdf"
              onChange={handleUpload}
              disabled={uploading}
              className="hidden"
              id="file-upload"
              data-testid="file-input"
            />
            <label htmlFor="file-upload">
              <Button asChild disabled={uploading} data-testid="upload-btn">
                <span className="cursor-pointer">
                  <Upload className="w-4 h-4 mr-2" />
                  {uploading ? 'A fazer upload...' : 'Escolher Ficheiro'}
                </span>
              </Button>
            </label>
            {uploading && <div className="spinner" />}
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'image', 'video', 'document'].map((type) => (
          <Button
            key={type}
            variant={filter === type ? 'default' : 'outline'}
            onClick={() => setFilter(type)}
            size="sm"
            data-testid={`filter-${type}`}
          >
            {type === 'all' ? 'Todos' : type.charAt(0).toUpperCase() + type.slice(1)}
          </Button>
        ))}
      </div>

      {/* Assets Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="spinner" />
        </div>
      ) : assets.length === 0 ? (
        <Alert>
          <AlertDescription>Nenhum asset encontrado. Faz upload do primeiro!</AlertDescription>
        </Alert>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {assets.map((asset) => (
            <Card key={asset.asset_id} className="group relative" data-testid={`asset-${asset.asset_id}`}>
              <CardContent className="p-4">
                {/* Preview */}
                <div className="aspect-square bg-slate-100 rounded mb-3 flex items-center justify-center overflow-hidden">
                  {asset.type === 'image' ? (
                    <img
                      src={`${API}/media/${asset.asset_id}`}
                      alt={asset.original_filename}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-slate-400">
                      {getTypeIcon(asset.type)}
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <Badge variant="secondary" className="text-xs">
                      {asset.type}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(asset.asset_id)}
                      className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      data-testid={`delete-${asset.asset_id}`}
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                  
                  <p className="text-sm font-medium truncate" title={asset.original_filename}>
                    {asset.original_filename}
                  </p>
                  
                  <p className="text-xs text-gray-500">
                    {formatSize(asset.size)}
                  </p>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => {
                      navigator.clipboard.writeText(asset.asset_id);
                      toast.success('ID copiado!');
                    }}
                  >
                    Copiar ID
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Stats */}
      {assets.length > 0 && (
        <div className="text-sm text-gray-500 text-center">
          {assets.length} asset{assets.length !== 1 ? 's' : ''} • 
          Total: {formatSize(assets.reduce((sum, a) => sum + a.size, 0))}
        </div>
      )}
    </div>
  );
};

export default AdminMediaPage;
