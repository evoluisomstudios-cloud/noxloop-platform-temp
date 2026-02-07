import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { 
  Users, 
  Package, 
  Zap, 
  Settings,
  TrendingUp,
  Database,
  Server,
  Activity,
  Plus,
  Trash2,
  Edit,
  CheckCircle,
  XCircle,
  ArrowLeft
} from "lucide-react";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const AdminPage = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.is_admin) {
      navigate("/dashboard");
      return;
    }
    fetchData();
  }, [user, navigate]);

  const fetchData = async () => {
    try {
      const [statsRes, usersRes, templatesRes] = await Promise.all([
        fetch(`${API}/admin/stats`, { credentials: "include" }),
        fetch(`${API}/admin/users`, { credentials: "include" }),
        fetch(`${API}/admin/templates`, { credentials: "include" }),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (usersRes.ok) {
        const data = await usersRes.json();
        setUsers(data.users || []);
      }
      if (templatesRes.ok) setTemplates(await templatesRes.json());
    } catch (error) {
      console.error("Error fetching admin data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!user?.is_admin) return null;

  const StatCard = ({ icon: Icon, label, value, color }) => (
    <div className="card-dashboard">
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-2xl font-bold">{loading ? "..." : value}</p>
          <p className="text-sm text-gray-400">{label}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050505] p-6" data-testid="admin-page">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate("/dashboard")} className="p-2">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Admin Backoffice</h1>
            <p className="text-gray-400">Gestão da plataforma DigiForge</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-sm ${
            stats?.llm_provider === "mock" ? "bg-yellow-500/20 text-yellow-400" :
            stats?.llm_provider === "openai" ? "bg-green-500/20 text-green-400" :
            "bg-blue-500/20 text-blue-400"
          }`}>
            LLM: {stats?.llm_provider || "..."}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
        <StatCard icon={Users} label="Utilizadores" value={stats?.total_users} color="bg-blue-500" />
        <StatCard icon={Package} label="Workspaces" value={stats?.total_workspaces} color="bg-purple-500" />
        <StatCard icon={Zap} label="Produtos" value={stats?.total_products} color="bg-green-500" />
        <StatCard icon={TrendingUp} label="Campanhas" value={stats?.total_campaigns} color="bg-orange-500" />
        <StatCard icon={Activity} label="Gerações Hoje" value={stats?.usage_today} color="bg-pink-500" />
        <StatCard icon={Activity} label="Gerações Mês" value={stats?.usage_month} color="bg-indigo-500" />
      </div>

      {/* System Status */}
      <div className="card-dashboard mb-8">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" />
          Estado do Sistema
        </h2>
        <div className="grid md:grid-cols-4 gap-4">
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
            {stats?.llm_provider !== "mock" ? (
              <CheckCircle className="w-5 h-5 text-green-400" />
            ) : (
              <XCircle className="w-5 h-5 text-yellow-400" />
            )}
            <div>
              <p className="font-medium">LLM Provider</p>
              <p className="text-sm text-gray-400">{stats?.llm_provider || "Loading..."}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
            {stats?.rag_enabled ? (
              <CheckCircle className="w-5 h-5 text-green-400" />
            ) : (
              <XCircle className="w-5 h-5 text-gray-400" />
            )}
            <div>
              <p className="font-medium">RAG</p>
              <p className="text-sm text-gray-400">{stats?.rag_enabled ? "Enabled" : "Disabled"}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
            {stats?.stripe_enabled ? (
              <CheckCircle className="w-5 h-5 text-green-400" />
            ) : (
              <XCircle className="w-5 h-5 text-gray-400" />
            )}
            <div>
              <p className="font-medium">Stripe</p>
              <p className="text-sm text-gray-400">{stats?.stripe_enabled ? "Enabled" : "Disabled"}</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
            <Database className="w-5 h-5 text-green-400" />
            <div>
              <p className="font-medium">Database</p>
              <p className="text-sm text-gray-400">Connected</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="users" className="space-y-6">
        <TabsList className="bg-[#0A0A0A] border border-[#262626]">
          <TabsTrigger value="users">Utilizadores</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="plans">Planos</TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users">
          <div className="card-dashboard">
            <h3 className="font-semibold mb-4">Utilizadores Registados</h3>
            {loading ? (
              <div className="h-40 loading-shimmer rounded" />
            ) : users.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Nenhum utilizador registado</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[#262626]">
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Nome</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Email</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Admin</th>
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Data</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.user_id} className="border-b border-[#262626]/50">
                        <td className="py-3 px-4">{u.name}</td>
                        <td className="py-3 px-4 text-gray-400">{u.email}</td>
                        <td className="py-3 px-4">
                          {u.is_admin ? (
                            <span className="px-2 py-1 rounded bg-purple-500/20 text-purple-400 text-xs">Admin</span>
                          ) : (
                            <span className="px-2 py-1 rounded bg-gray-500/20 text-gray-400 text-xs">User</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-gray-400 text-sm">
                          {u.created_at ? new Date(u.created_at).toLocaleDateString("pt-PT") : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates">
          <div className="card-dashboard">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Templates de Prompt</h3>
              <Button 
                className="bg-white text-black hover:bg-gray-200"
                onClick={() => toast.info("Template editor coming soon")}
              >
                <Plus className="w-4 h-4 mr-2" />
                Novo Template
              </Button>
            </div>
            {templates.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Nenhum template criado</p>
            ) : (
              <div className="space-y-3">
                {templates.map((t) => (
                  <div key={t.template_id} className="p-4 rounded-lg bg-white/5 flex items-center justify-between">
                    <div>
                      <p className="font-medium">{t.name}</p>
                      <p className="text-sm text-gray-400">{t.description}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs">{t.category}</span>
                      <Button variant="ghost" size="icon"><Edit className="w-4 h-4" /></Button>
                      <Button variant="ghost" size="icon" className="text-red-400"><Trash2 className="w-4 h-4" /></Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </TabsContent>

        {/* Plans Tab */}
        <TabsContent value="plans">
          <div className="card-dashboard">
            <h3 className="font-semibold mb-4">Configuração de Planos</h3>
            <div className="grid md:grid-cols-4 gap-4">
              {["free", "starter", "pro", "enterprise"].map((plan) => (
                <div key={plan} className="p-4 rounded-lg bg-white/5 border border-[#262626]">
                  <h4 className="font-bold capitalize mb-2">{plan}</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Preço:</span>
                      <span>€{plan === "free" ? "0" : plan === "starter" ? "9.99" : plan === "pro" ? "29.99" : "99.99"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Créditos:</span>
                      <span>{plan === "free" ? "10" : plan === "starter" ? "50" : plan === "pro" ? "200" : "1000"}</span>
                    </div>
                  </div>
                  <Button variant="outline" className="w-full mt-4 border-[#262626]" onClick={() => toast.info("Plan editor coming soon")}>
                    <Settings className="w-4 h-4 mr-2" />
                    Editar
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
