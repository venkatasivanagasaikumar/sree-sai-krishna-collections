import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';
import { BrandLogo } from '../../components/common/BrandLogo';
import { useAuth } from '../../context/AuthContext';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/account';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-3xl p-8 border border-ssk-border shadow-xl space-y-6">
        <div className="text-center space-y-2">
          <BrandLogo size="lg" className="justify-center mx-auto" />
          <h2 className="text-xl font-serif font-bold text-ssk-navy pt-2">Welcome Back</h2>
          <p className="text-xs text-ssk-text-secondary">Sign in to access your orders, saved addresses & bag</p>
        </div>

        {error && (
          <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Email Address</label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="priya.sharma@example.com"
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
              />
              <Mail className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-ssk-text">Password</label>
            </div>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
              />
              <Lock className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
          >
            <span>{isSubmitting ? 'Signing in...' : 'Sign In'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-center space-y-3 pt-2 border-t border-ssk-border">
          <p className="text-xs text-ssk-text-secondary">
            Don't have an account?{' '}
            <Link to="/register" className="font-bold text-ssk-navy hover:underline">
              Create an Account
            </Link>
          </p>

          <Link
            to="/admin/login"
            className="block text-[11px] text-ssk-gold-dark font-medium hover:underline pt-1"
          >
            Are you a seller / administrator? Sign in here &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
};
