import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, Mail, ArrowRight, AlertCircle, KeyRound, Sparkles } from 'lucide-react';
import { BrandLogo } from '../../components/common/BrandLogo';
import { useAuth } from '../../context/AuthContext';

export const AdminLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('admin@sskcollections.com');
  const [password, setPassword] = useState('Admin@SSK2026!');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await login({ email, password });
      const role = res.user.role;
      if (!['Super Admin', 'Admin', 'Order Manager', 'Inventory Manager', 'Customer Support'].includes(role)) {
        setError('Access denied. This account does not possess seller or staff permissions.');
        return;
      }
      navigate('/admin/dashboard');
    } catch (err: any) {
      setError(err.message || 'Invalid administrative credentials');
    } finally {
      setIsSubmitting(false);
    }
  };

  const setDemoCredentials = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-ssk-navy-dark flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#C89A43_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-ssk-gold/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-ssk-blue-royal/20 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full bg-white rounded-3xl p-8 shadow-2xl border-2 border-ssk-gold/40 relative z-10 space-y-6">
        <div className="text-center space-y-2">
          <BrandLogo size="lg" className="justify-center mx-auto" />
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-bold mt-2">
            <Shield className="w-3.5 h-3.5 text-ssk-gold-dark" />
            <span>Meesho-Inspired Seller Panel</span>
          </div>
          <h2 className="text-xl font-serif font-bold text-ssk-navy">Staff & Seller Portal</h2>
          <p className="text-xs text-ssk-text-secondary">Manage products, orders, AWB logistics, returns, and inventory</p>
        </div>

        {error && (
          <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Quick Demo Access Buttons */}
        <div className="p-3 bg-ssk-surface rounded-2xl border border-ssk-border space-y-2">
          <span className="text-[10px] font-bold text-ssk-text-secondary uppercase tracking-wider block flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-ssk-gold" /> Quick Demo Role Switcher:
          </span>
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <button
              type="button"
              onClick={() => setDemoCredentials('admin@sskcollections.com', 'Admin@SSK2026!')}
              className="px-2.5 py-1.5 bg-white border border-ssk-border rounded-lg font-semibold text-ssk-navy hover:border-ssk-gold text-left truncate"
            >
              👑 Super Admin
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('orders@sskcollections.com', 'Staff@SSK2026!')}
              className="px-2.5 py-1.5 bg-white border border-ssk-border rounded-lg font-semibold text-ssk-navy hover:border-ssk-gold text-left truncate"
            >
              📦 Order Manager
            </button>
            <button
              type="button"
              onClick={() => setDemoCredentials('inventory@sskcollections.com', 'Staff@SSK2026!')}
              className="px-2.5 py-1.5 bg-white border border-ssk-border rounded-lg font-semibold text-ssk-navy hover:border-ssk-gold text-left truncate col-span-2"
            >
              🏷️ Inventory Manager
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Staff Email Address</label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
              />
              <Mail className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Secure Password</label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
              />
              <Lock className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
          >
            <KeyRound className="w-4 h-4 text-ssk-gold" />
            <span>{isSubmitting ? 'Authenticating...' : 'Enter Seller Dashboard'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-center pt-2 border-t border-ssk-border">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="text-xs text-ssk-navy hover:underline font-semibold"
          >
            &larr; Return to Customer Storefront
          </button>
        </div>
      </div>
    </div>
  );
};
