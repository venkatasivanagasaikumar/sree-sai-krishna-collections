import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, ShoppingBag, Package, Layers, RotateCcw,
  Users, Tag, BarChart3, Settings, LogOut, ChevronRight,
  Menu, X, Bell, Shield, ExternalLink, FileSpreadsheet
} from 'lucide-react';
import { BrandLogo } from '../common/BrandLogo';
import { useAuth } from '../../context/AuthContext';

export const AdminLayout: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout, isAdmin } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Guard: if not staff, redirect
  if (!user || !isAdmin) {
    navigate('/admin/login');
    return null;
  }

  const navItems = [
    { label: 'Overview', path: '/admin/dashboard', icon: LayoutDashboard },
    { label: 'Orders & Fulfilment', path: '/admin/orders', icon: Package, badge: 'Active' },
    { label: 'Product Catalog', path: '/admin/products', icon: ShoppingBag },
    { label: 'Inventory & SKUs', path: '/admin/inventory', icon: Layers },
    { label: 'Returns & Refunds', path: '/admin/returns', icon: RotateCcw },
    { label: 'Customer Directory', path: '/admin/customers', icon: Users },
    { label: 'Coupons & Promos', path: '/admin/promotions', icon: Tag },
    { label: 'Google Sheets / Excel', path: '/admin/sheets-sync', icon: FileSpreadsheet, badge: 'Sync' },
    { label: 'Reports & Audit Logs', path: '/admin/reports', icon: BarChart3 },
    { label: 'Store Settings', path: '/admin/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-ssk-surface flex">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
        />
      )}

      {/* Persistent Navy Sidebar (Meesho inspired layout) */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-ssk-navy-dark text-white flex flex-col justify-between transition-transform duration-300 ease-in-out border-r border-ssk-gold/30 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div>
          {/* Sidebar Brand Header */}
          <div className="h-20 flex items-center justify-between px-6 border-b border-white/10 bg-ssk-navy">
            <BrandLogo size="sm" light />
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="lg:hidden p-1 text-gray-300 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Seller Tag */}
          <div className="px-6 py-3 bg-white/5 border-b border-white/10 flex items-center justify-between text-[11px]">
            <span className="text-ssk-gold-light font-bold flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5" />
              <span>Seller Supplier Panel</span>
            </span>
            <span className="px-2 py-0.5 rounded-full bg-ssk-success text-white text-[9px] font-bold">
              LIVE
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1 overflow-y-auto max-h-[calc(100vh-220px)]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsSidebarOpen(false)}
                  className={`flex items-center justify-between px-4 py-3 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-ssk-gold text-white shadow-md'
                      : 'text-gray-300 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && !isActive && (
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-white/10 text-ssk-gold-light">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Bottom User Area */}
        <div className="p-4 border-t border-white/10 bg-black/20 space-y-3">
          <Link
            to="/"
            target="_blank"
            className="flex items-center justify-center gap-1.5 w-full py-2 bg-white/10 hover:bg-white/15 text-white text-xs font-semibold rounded-xl transition-all"
          >
            <span>View Live Storefront</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-ssk-gold text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
                {user.full_name?.charAt(0).toUpperCase()}
              </div>
              <div className="truncate">
                <p className="text-xs font-bold text-white truncate">{user.full_name}</p>
                <p className="text-[10px] text-gray-300 truncate">{user.role}</p>
              </div>
            </div>

            <button
              onClick={logout}
              className="p-2 text-gray-400 hover:text-red-400 transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-20 bg-white border-b border-ssk-border px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30 shadow-sm">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl text-ssk-text hover:bg-ssk-blue-light"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="hidden sm:block">
              <h2 className="text-sm font-bold text-ssk-navy font-serif">Sree Sai Krishna Collections (SSK)</h2>
              <p className="text-[11px] text-ssk-text-secondary">Secunderabad Warehouse & Fulfilment Hub</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-ssk-success bg-green-50 px-3 py-1.5 rounded-full border border-green-200">
              <span className="w-2 h-2 rounded-full bg-ssk-success animate-pulse" />
              <span className="hidden sm:inline">Store Active & Taking Orders</span>
            </div>

            <button
              onClick={() => navigate('/admin/orders')}
              className="relative p-2 text-ssk-text hover:bg-ssk-blue-light rounded-xl transition-colors"
              title="Notifications"
            >
              <Bell className="w-5 h-5 text-ssk-navy" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-ssk-gold" />
            </button>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
