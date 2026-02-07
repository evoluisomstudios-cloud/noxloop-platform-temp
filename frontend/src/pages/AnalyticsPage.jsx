import { useState, useEffect } from "react";
import { DashboardLayout } from "../components/DashboardLayout";
import { 
  TrendingUp, 
  DollarSign, 
  Package, 
  Eye,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar
} from "recharts";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

export const AnalyticsPage = ({ user, onLogout }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`${API}/analytics`, {
        credentials: "include",
      });
      if (response.ok) {
        setAnalytics(await response.json());
      }
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    {
      label: "Receita Total",
      value: analytics ? `€${analytics.total_revenue.toFixed(2)}` : "€0.00",
      icon: DollarSign,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
      change: "+12.5%",
      changePositive: true,
    },
    {
      label: "Total de Vendas",
      value: analytics?.total_sales || 0,
      icon: TrendingUp,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      change: "+8.2%",
      changePositive: true,
    },
    {
      label: "Produtos Ativos",
      value: analytics?.total_products || 0,
      icon: Package,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
      change: "+2",
      changePositive: true,
    },
    {
      label: "Visualizações",
      value: analytics?.total_views || 0,
      icon: Eye,
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
      change: "+24.1%",
      changePositive: true,
    },
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#171717] border border-[#262626] rounded-lg p-3 shadow-lg">
          <p className="text-sm text-gray-400 mb-1">{label}</p>
          <p className="text-lg font-semibold">{payload[0].value} vendas</p>
        </div>
      );
    }
    return null;
  };

  return (
    <DashboardLayout user={user} onLogout={onLogout}>
      <div className="space-y-8" data-testid="analytics-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold mb-1">Analytics</h1>
          <p className="text-gray-400">
            Acompanha o desempenho dos teus produtos
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="card-dashboard"
              data-testid={`analytics-stat-${index}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <div className={`flex items-center gap-1 text-sm ${
                  stat.changePositive ? "text-green-400" : "text-red-400"
                }`}>
                  {stat.changePositive ? (
                    <ArrowUpRight className="w-4 h-4" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4" />
                  )}
                  {stat.change}
                </div>
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

        {/* Charts */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Sales Chart */}
          <div className="card-dashboard">
            <h3 className="font-semibold mb-6">Vendas por Dia</h3>
            {loading ? (
              <div className="h-[300px] loading-shimmer rounded" />
            ) : analytics?.sales_by_day?.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.sales_by_day}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#52525B"
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getDate()}/${date.getMonth() + 1}`;
                      }}
                    />
                    <YAxis stroke="#52525B" />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar 
                      dataKey="sales" 
                      fill="#6366f1" 
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-400">
                Sem dados de vendas ainda
              </div>
            )}
          </div>

          {/* Revenue Chart */}
          <div className="card-dashboard">
            <h3 className="font-semibold mb-6">Evolução da Receita</h3>
            {loading ? (
              <div className="h-[300px] loading-shimmer rounded" />
            ) : analytics?.sales_by_day?.length > 0 ? (
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={analytics.sales_by_day}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#52525B"
                      tickFormatter={(value) => {
                        const date = new Date(value);
                        return `${date.getDate()}/${date.getMonth() + 1}`;
                      }}
                    />
                    <YAxis stroke="#52525B" />
                    <Tooltip content={<CustomTooltip />} />
                    <Line 
                      type="monotone" 
                      dataKey="sales" 
                      stroke="#22c55e" 
                      strokeWidth={2}
                      dot={{ fill: "#22c55e", strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-gray-400">
                Sem dados de receita ainda
              </div>
            )}
          </div>
        </div>

        {/* Recent Transactions */}
        <div className="card-dashboard">
          <h3 className="font-semibold mb-6">Vendas Recentes</h3>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 loading-shimmer rounded" />
              ))}
            </div>
          ) : analytics?.recent_sales?.length > 0 ? (
            <div className="space-y-3">
              {analytics.recent_sales.map((sale, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 rounded-lg bg-white/5"
                >
                  <div>
                    <p className="font-medium">Venda #{sale.transaction_id?.slice(-8)}</p>
                    <p className="text-sm text-gray-400">
                      {new Date(sale.created_at).toLocaleDateString("pt-PT")}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-400">
                      +€{sale.amount?.toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-400">{sale.currency?.toUpperCase()}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              Sem vendas recentes
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};
