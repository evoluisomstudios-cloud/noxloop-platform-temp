import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { 
  Zap, 
  LayoutDashboard, 
  Package, 
  BarChart3, 
  Settings, 
  LogOut,
  Menu,
  X,
  Plus,
  Sparkles,
  Megaphone,
  Shield
} from "lucide-react";

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/products", label: "Produtos", icon: Package },
  { path: "/campaigns", label: "Campanhas", icon: Megaphone },
  { path: "/analytics", label: "Analytics", icon: BarChart3 },
  { path: "/settings", label: "Definições", icon: Settings },
];

const adminNavItem = { path: "/admin", label: "Admin", icon: Shield };

export const DashboardLayout = ({ children, user, onLogout }) => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Sidebar */}
      <aside 
        className={`sidebar ${sidebarOpen ? "open" : ""}`}
        data-testid="sidebar"
      >
        {/* Logo */}
        <div className="p-6 border-b border-[#262626]">
          <Link to="/dashboard" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center">
              <Zap className="w-5 h-5 text-black" />
            </div>
            <span className="text-lg font-bold tracking-tight">NOXLOOP</span>
          </Link>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
                data-testid={`nav-${item.label.toLowerCase()}`}
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
          
          {/* Admin Link - Only visible for admin users */}
          {user?.is_admin && (
            <Link
              to={adminNavItem.path}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors mt-4 border-t border-[#262626] pt-4 ${
                location.pathname === adminNavItem.path
                  ? "bg-purple-500/20 text-purple-400"
                  : "text-purple-400/70 hover:text-purple-400 hover:bg-purple-500/10"
              }`}
              data-testid="nav-admin"
            >
              <adminNavItem.icon className="w-5 h-5" />
              <span className="font-medium">{adminNavItem.label}</span>
            </Link>
          )}
        </nav>

        {/* Create Button */}
        <div className="p-4 border-t border-[#262626]">
          <Link to="/products/new" onClick={() => setSidebarOpen(false)}>
            <Button className="w-full bg-white text-black hover:bg-gray-200" data-testid="sidebar-create-btn">
              <Plus className="w-4 h-4 mr-2" />
              Criar Produto
            </Button>
          </Link>
        </div>

        {/* Credits */}
        <div className="p-4 border-t border-[#262626]">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-indigo-500/10">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <div>
              <p className="text-sm font-medium">{user?.credits ?? 0} créditos</p>
              <p className="text-xs text-gray-400 capitalize">Plano {user?.plan || "Free"}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="main-content">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 h-16 bg-[#050505]/80 backdrop-blur-xl border-b border-[#262626]">
          <div className="flex items-center justify-between h-full px-4 md:px-6">
            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              data-testid="mobile-menu-btn"
            >
              {sidebarOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </Button>

            {/* Page Title - Hidden on mobile */}
            <div className="hidden lg:block" />

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-3 h-auto p-2" data-testid="user-menu-btn">
                  <Avatar className="w-8 h-8">
                    <AvatarImage src={user?.picture} alt={user?.name} />
                    <AvatarFallback className="bg-white/10 text-sm">
                      {user?.name?.charAt(0)?.toUpperCase() || "U"}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden md:inline font-medium">{user?.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-[#171717] border-[#262626]">
                <div className="px-3 py-2">
                  <p className="font-medium">{user?.name}</p>
                  <p className="text-sm text-gray-400 truncate">{user?.email}</p>
                </div>
                <DropdownMenuSeparator className="bg-[#262626]" />
                <DropdownMenuItem asChild>
                  <Link to="/settings" className="flex items-center">
                    <Settings className="w-4 h-4 mr-2" />
                    Definições
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-[#262626]" />
                <DropdownMenuItem onClick={onLogout} className="text-red-400 focus:text-red-400">
                  <LogOut className="w-4 h-4 mr-2" />
                  Terminar Sessão
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
};
