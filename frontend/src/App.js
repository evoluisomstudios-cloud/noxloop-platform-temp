import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Toaster } from "./components/ui/sonner";

// Pages
import { LandingPage } from "./pages/LandingPage";
import { AuthPage } from "./pages/AuthPage";
import { AuthCallbackPage } from "./pages/AuthCallbackPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProductsPage } from "./pages/ProductsPage";
import { CreateProductPage } from "./pages/CreateProductPage";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { PublicProductPage } from "./pages/PublicProductPage";
import { PurchaseSuccessPage } from "./pages/PurchaseSuccessPage";
import { AdminPage } from "./pages/AdminPage";
import { CampaignBuilderPage } from "./pages/CampaignBuilderPage";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

// Auth Hook
export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await fetch(`${API}/auth/me`, { credentials: "include" });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        setUser(null);
      }
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (userData) => {
    // Set initial user data, then refresh to get full data including credits
    setUser(userData);
    // Small delay to ensure cookie is set, then refresh
    setTimeout(() => checkAuth(), 100);
  };
  
  const logout = async () => {
    try {
      await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
    } catch (error) {
      console.error("Logout error:", error);
    }
    setUser(null);
  };

  const refreshUser = async () => await checkAuth();

  return { user, loading, login, logout, refreshUser };
};

// Protected Route with optional admin check
const ProtectedRoute = ({ children, user, loading, requireAdmin = false }) => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate("/auth", { replace: true, state: { from: location } });
    } else if (!loading && user && requireAdmin && !user.is_admin) {
      // Non-admin trying to access admin route
      navigate("/dashboard", { replace: true });
    }
  }, [user, loading, navigate, location, requireAdmin]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4" />
          <p className="text-gray-400">A carregar...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;
  if (requireAdmin && !user.is_admin) return null;
  return children;
};

// App Router
const AppRouter = ({ user, loading, login, logout, refreshUser }) => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth" element={user ? <Navigate to="/dashboard" replace /> : <AuthPage onLogin={login} />} />
      <Route path="/auth/callback" element={<AuthCallbackPage onLogin={login} />} />
      <Route path="/p/:productId" element={<PublicProductPage />} />
      <Route path="/purchase/success" element={<PurchaseSuccessPage />} />

      {/* Protected Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute user={user} loading={loading}>
          <DashboardPage user={user} onLogout={logout} />
        </ProtectedRoute>
      } />
      <Route path="/products" element={
        <ProtectedRoute user={user} loading={loading}>
          <ProductsPage user={user} onLogout={logout} />
        </ProtectedRoute>
      } />
      <Route path="/products/new" element={
        <ProtectedRoute user={user} loading={loading}>
          <CreateProductPage user={user} onLogout={logout} refreshUser={refreshUser} />
        </ProtectedRoute>
      } />
      <Route path="/products/:productId" element={
        <ProtectedRoute user={user} loading={loading}>
          <ProductDetailPage user={user} onLogout={logout} />
        </ProtectedRoute>
      } />
      <Route path="/campaigns" element={
        <ProtectedRoute user={user} loading={loading}>
          <CampaignBuilderPage user={user} onLogout={logout} />
        </ProtectedRoute>
      } />
      <Route path="/campaigns/:workspaceId" element={
        <ProtectedRoute user={user} loading={loading}>
          <CampaignBuilderPage user={user} onLogout={logout} />
        </ProtectedRoute>
      } />
      <Route path="/analytics" element={
        <ProtectedRoute user={user} loading={loading}>
          <AnalyticsPage user={user} onLogout={logout} />
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute user={user} loading={loading}>
          <SettingsPage user={user} onLogout={logout} refreshUser={refreshUser} />
        </ProtectedRoute>
      } />
      
      {/* Admin Route - Only for is_admin=true users */}
      <Route path="/admin" element={
        <ProtectedRoute user={user} loading={loading} requireAdmin={true}>
          <AdminPage user={user} onLogout={logout} />
        </ProtectedRoute>
      } />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function App() {
  const { user, loading, login, logout, refreshUser } = useAuth();

  return (
    <BrowserRouter>
      <AppRouter user={user} loading={loading} login={login} logout={logout} refreshUser={refreshUser} />
      <Toaster position="top-right" richColors />
    </BrowserRouter>
  );
}

export default App;
